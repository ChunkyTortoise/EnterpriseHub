"""
Session Manager for Cross-Session Conversation Tracking

Handles persistent session storage, tenant isolation, and user session management
across browser restarts and multiple devices.
"""

import asyncio
import logging
import uuid
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Session data structure"""
    session_id: str
    user_id: str
    tenant_id: str
    user_type: str  # lead, buyer, seller, agent

    # Session metadata
    created_at: datetime
    last_active: datetime
    device_info: Dict[str, str]
    ip_address: Optional[str] = None

    # Conversation state
    conversation_id: Optional[str] = None
    message_count: int = 0
    current_stage: str = "initial_contact"

    # User context
    user_profile: Dict[str, Any] = None
    preferences: Dict[str, Any] = None
    behavioral_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.user_profile is None:
            self.user_profile = {}
        if self.preferences is None:
            self.preferences = {}
        if self.behavioral_data is None:
            self.behavioral_data = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_active'] = self.last_active.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_active'] = datetime.fromisoformat(data['last_active'])
        return cls(**data)


class SessionManager:
    """
    Cross-session conversation tracking with tenant isolation.

    Features:
    - Persistent session storage across browser restarts
    - Tenant-specific data isolation
    - User session deduplication and merging
    - Automatic session cleanup and expiry
    - Multi-device session tracking
    """

    def __init__(
        self,
        storage_path: str = "./session_data",
        session_timeout_hours: int = 24 * 7,  # 7 days
        cleanup_interval_hours: int = 24  # Daily cleanup
    ):
        """Initialize session manager"""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

        self.session_timeout_hours = session_timeout_hours
        self.cleanup_interval_hours = cleanup_interval_hours

        # In-memory session cache
        self.active_sessions: Dict[str, SessionData] = {}
        self.user_session_map: Dict[str, List[str]] = {}  # user_key -> session_ids

        # Tenant isolation
        self.tenant_storage: Dict[str, Path] = {}

        self.last_cleanup = datetime.now()

        logger.info(f"SessionManager initialized with storage at {self.storage_path}")

    def _get_tenant_path(self, tenant_id: str) -> Path:
        """Get storage path for tenant"""
        if tenant_id not in self.tenant_storage:
            tenant_path = self.storage_path / f"tenant_{tenant_id}"
            tenant_path.mkdir(exist_ok=True)
            self.tenant_storage[tenant_id] = tenant_path

        return self.tenant_storage[tenant_id]

    def _generate_user_key(self, user_id: str, tenant_id: str) -> str:
        """Generate unique user key for tenant isolation"""
        return f"{tenant_id}:{user_id}"

    def _hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for privacy"""
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    async def create_session(
        self,
        user_id: str,
        tenant_id: str,
        user_type: str,
        device_info: Optional[Dict[str, str]] = None,
        ip_address: Optional[str] = None
    ) -> SessionData:
        """Create new session for user"""

        # Check for existing sessions
        existing_session = await self.get_user_session(user_id, tenant_id)

        if existing_session and self._is_session_valid(existing_session):
            # Update existing session
            existing_session.last_active = datetime.now()
            if device_info:
                existing_session.device_info.update(device_info)

            await self._save_session(existing_session)
            return existing_session

        # Create new session
        session_id = str(uuid.uuid4())
        session_data = SessionData(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            user_type=user_type,
            created_at=datetime.now(),
            last_active=datetime.now(),
            device_info=device_info or {},
            ip_address=self._hash_sensitive_data(ip_address) if ip_address else None
        )

        # Store in cache
        self.active_sessions[session_id] = session_data

        # Update user session mapping
        user_key = self._generate_user_key(user_id, tenant_id)
        if user_key not in self.user_session_map:
            self.user_session_map[user_key] = []

        self.user_session_map[user_key].append(session_id)

        # Persist to storage
        await self._save_session(session_data)

        logger.info(f"Created session {session_id} for user {user_id} in tenant {tenant_id}")
        return session_data

    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID"""

        # Check cache first
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            if self._is_session_valid(session):
                return session
            else:
                # Clean up expired session
                del self.active_sessions[session_id]

        # Load from storage
        session = await self._load_session(session_id)

        if session and self._is_session_valid(session):
            self.active_sessions[session_id] = session
            return session

        return None

    async def get_user_session(
        self,
        user_id: str,
        tenant_id: str
    ) -> Optional[SessionData]:
        """Get most recent valid session for user"""

        user_key = self._generate_user_key(user_id, tenant_id)

        if user_key not in self.user_session_map:
            # Try to load from storage
            await self._load_user_sessions(user_id, tenant_id)

        if user_key in self.user_session_map:
            # Get most recent session
            for session_id in reversed(self.user_session_map[user_key]):
                session = await self.get_session(session_id)
                if session:
                    return session

        return None

    async def update_session_activity(
        self,
        session_id: str,
        activity_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update session activity and metadata"""

        session = await self.get_session(session_id)
        if not session:
            return False

        session.last_active = datetime.now()

        if activity_data:
            # Update message count
            if 'message_count' in activity_data:
                session.message_count = activity_data['message_count']

            # Update current stage
            if 'current_stage' in activity_data:
                session.current_stage = activity_data['current_stage']

            # Update user profile
            if 'user_profile' in activity_data:
                session.user_profile.update(activity_data['user_profile'])

            # Update preferences
            if 'preferences' in activity_data:
                session.preferences.update(activity_data['preferences'])

            # Update behavioral data
            if 'behavioral_data' in activity_data:
                session.behavioral_data.update(activity_data['behavioral_data'])

        await self._save_session(session)
        return True

    async def merge_user_sessions(
        self,
        user_id: str,
        tenant_id: str
    ) -> Optional[SessionData]:
        """Merge multiple sessions for the same user"""

        user_key = self._generate_user_key(user_id, tenant_id)

        if user_key not in self.user_session_map:
            await self._load_user_sessions(user_id, tenant_id)

        if user_key not in self.user_session_map or len(self.user_session_map[user_key]) <= 1:
            return await self.get_user_session(user_id, tenant_id)

        # Get all valid sessions for user
        valid_sessions = []
        for session_id in self.user_session_map[user_key]:
            session = await self.get_session(session_id)
            if session:
                valid_sessions.append(session)

        if not valid_sessions:
            return None

        if len(valid_sessions) == 1:
            return valid_sessions[0]

        # Merge sessions - keep most recent, merge data
        primary_session = max(valid_sessions, key=lambda s: s.last_active)

        for session in valid_sessions:
            if session.session_id != primary_session.session_id:
                # Merge user profile
                for key, value in session.user_profile.items():
                    if key not in primary_session.user_profile:
                        primary_session.user_profile[key] = value

                # Merge preferences
                for key, value in session.preferences.items():
                    if key not in primary_session.preferences:
                        primary_session.preferences[key] = value

                # Merge behavioral data
                for key, value in session.behavioral_data.items():
                    if key not in primary_session.behavioral_data or session.last_active > primary_session.last_active:
                        primary_session.behavioral_data[key] = value

                # Update message count
                primary_session.message_count += session.message_count

                # Remove merged session
                await self._delete_session(session.session_id)

        # Update session mapping
        self.user_session_map[user_key] = [primary_session.session_id]

        await self._save_session(primary_session)

        logger.info(f"Merged {len(valid_sessions)} sessions for user {user_id}")
        return primary_session

    async def get_tenant_sessions(
        self,
        tenant_id: str,
        active_only: bool = True
    ) -> List[SessionData]:
        """Get all sessions for a tenant"""

        tenant_path = self._get_tenant_path(tenant_id)
        sessions = []

        # Load from storage
        for session_file in tenant_path.glob("session_*.json"):
            try:
                session = await self._load_session_from_file(session_file)
                if session:
                    if not active_only or self._is_session_valid(session):
                        sessions.append(session)
            except Exception as e:
                logger.warning(f"Failed to load session from {session_file}: {e}")

        return sorted(sessions, key=lambda s: s.last_active, reverse=True)

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""

        if (datetime.now() - self.last_cleanup).total_seconds() < self.cleanup_interval_hours * 3600:
            return 0  # Too soon for cleanup

        self.last_cleanup = datetime.now()
        cleaned_count = 0

        # Clean up in-memory cache
        expired_session_ids = []
        for session_id, session in self.active_sessions.items():
            if not self._is_session_valid(session):
                expired_session_ids.append(session_id)

        for session_id in expired_session_ids:
            del self.active_sessions[session_id]
            cleaned_count += 1

        # Clean up storage files
        for tenant_id in self.tenant_storage:
            tenant_path = self._get_tenant_path(tenant_id)

            for session_file in tenant_path.glob("session_*.json"):
                try:
                    session = await self._load_session_from_file(session_file)
                    if session and not self._is_session_valid(session):
                        session_file.unlink()
                        cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Error cleaning session file {session_file}: {e}")

        # Clean up user session mapping
        for user_key in list(self.user_session_map.keys()):
            valid_sessions = []
            for session_id in self.user_session_map[user_key]:
                if session_id in self.active_sessions or await self._session_file_exists(session_id):
                    valid_sessions.append(session_id)

            if valid_sessions:
                self.user_session_map[user_key] = valid_sessions
            else:
                del self.user_session_map[user_key]

        logger.info(f"Cleaned up {cleaned_count} expired sessions")
        return cleaned_count

    def _is_session_valid(self, session: SessionData) -> bool:
        """Check if session is still valid"""
        expiry_time = session.last_active + timedelta(hours=self.session_timeout_hours)
        return datetime.now() < expiry_time

    async def _save_session(self, session: SessionData):
        """Save session to persistent storage"""
        tenant_path = self._get_tenant_path(session.tenant_id)
        session_file = tenant_path / f"session_{session.session_id}.json"

        try:
            with open(session_file, 'w') as f:
                json.dump(session.to_dict(), f, default=str)
        except Exception as e:
            logger.error(f"Failed to save session {session.session_id}: {e}")

    async def _load_session(self, session_id: str) -> Optional[SessionData]:
        """Load session from storage"""
        # Search across all tenants (this could be optimized with a session index)
        for tenant_id in self.tenant_storage:
            tenant_path = self._get_tenant_path(tenant_id)
            session_file = tenant_path / f"session_{session_id}.json"

            if session_file.exists():
                return await self._load_session_from_file(session_file)

        return None

    async def _load_session_from_file(self, session_file: Path) -> Optional[SessionData]:
        """Load session from file"""
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
                return SessionData.from_dict(data)
        except Exception as e:
            logger.warning(f"Failed to load session from {session_file}: {e}")
            return None

    async def _load_user_sessions(self, user_id: str, tenant_id: str):
        """Load all sessions for user from storage"""
        tenant_path = self._get_tenant_path(tenant_id)
        user_key = self._generate_user_key(user_id, tenant_id)
        session_ids = []

        for session_file in tenant_path.glob("session_*.json"):
            session = await self._load_session_from_file(session_file)
            if session and session.user_id == user_id:
                session_ids.append(session.session_id)

        if session_ids:
            self.user_session_map[user_key] = session_ids

    async def _delete_session(self, session_id: str):
        """Delete session from storage and cache"""
        # Remove from cache
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        # Remove from storage
        for tenant_id in self.tenant_storage:
            tenant_path = self._get_tenant_path(tenant_id)
            session_file = tenant_path / f"session_{session_id}.json"

            if session_file.exists():
                session_file.unlink()
                break

    async def _session_file_exists(self, session_id: str) -> bool:
        """Check if session file exists in storage"""
        for tenant_id in self.tenant_storage:
            tenant_path = self._get_tenant_path(tenant_id)
            session_file = tenant_path / f"session_{session_id}.json"

            if session_file.exists():
                return True

        return False

    def get_session_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get session statistics for tenant"""
        tenant_sessions = [s for s in self.active_sessions.values() if s.tenant_id == tenant_id]

        if not tenant_sessions:
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "user_types": {},
                "average_message_count": 0,
                "session_stages": {}
            }

        # Calculate statistics
        user_types = {}
        session_stages = {}
        total_messages = 0

        for session in tenant_sessions:
            user_types[session.user_type] = user_types.get(session.user_type, 0) + 1
            session_stages[session.current_stage] = session_stages.get(session.current_stage, 0) + 1
            total_messages += session.message_count

        return {
            "total_sessions": len(tenant_sessions),
            "active_sessions": len([s for s in tenant_sessions if self._is_session_valid(s)]),
            "user_types": user_types,
            "average_message_count": total_messages / len(tenant_sessions) if tenant_sessions else 0,
            "session_stages": session_stages,
            "last_cleanup": self.last_cleanup.isoformat(),
            "storage_path": str(self.storage_path)
        }