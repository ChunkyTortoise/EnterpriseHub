"""
Enterprise Authentication Manager
Provides comprehensive authentication, session management, and security features
"""

import asyncio
import hashlib
import json
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set

import bcrypt
import redis.asyncio as redis
from fastapi import HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr

from ghl_real_estate_ai.utils.async_utils import safe_create_task

from .audit_logger import AuditLogger
from .rbac import Permission, Role


class AuthProvider(str, Enum):
    """Authentication provider types"""

    LOCAL = "local"
    SSO = "sso"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    SAML = "saml"


class SessionStatus(str, Enum):
    """Session status types"""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPICIOUS = "suspicious"


@dataclass
class SecurityConfig:
    """Enterprise security configuration"""

    # JWT Configuration
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Password Policy
    password_min_length: int = 12
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    password_max_age_days: int = 90
    password_history_count: int = 10

    # Account Security
    max_failed_attempts: int = 5
    lockout_duration_minutes: int = 30
    session_timeout_minutes: int = 60
    concurrent_sessions_limit: int = 3

    # MFA Configuration
    mfa_enabled: bool = True
    mfa_providers: List[str] = field(default_factory=lambda: ["totp", "sms"])

    # Security Headers
    enable_security_headers: bool = True

    # Audit Configuration
    audit_login_events: bool = True
    audit_admin_actions: bool = True
    audit_data_access: bool = True


@dataclass
class User:
    """User model with enterprise features"""

    user_id: str
    username: str
    email: str
    full_name: str
    roles: List[Role]
    provider: AuthProvider
    is_active: bool = True
    is_verified: bool = False
    is_admin: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None


@dataclass
class Session:
    """Enhanced session with security tracking"""

    session_id: str
    user_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_active: datetime
    status: SessionStatus
    location: Optional[str] = None
    device_fingerprint: Optional[str] = None
    risk_score: float = 0.0


class AuthManager:
    """Enterprise Authentication Manager with comprehensive security features"""

    def __init__(self, config: SecurityConfig, redis_client: redis.Redis):
        self.config = config
        self.redis = redis_client
        self.audit_logger = AuditLogger()

        # In-memory caches for performance
        self._user_cache: Dict[str, User] = {}
        self._session_cache: Dict[str, Session] = {}
        self._active_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids

        # Security monitoring
        self._failed_attempts: Dict[str, List[datetime]] = {}
        self._suspicious_ips: Set[str] = set()

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_background_tasks()

    def _start_background_tasks(self):
        """Start background security tasks"""
        self._cleanup_task = safe_create_task(self._cleanup_expired_sessions())

    async def _cleanup_expired_sessions(self):
        """Periodically clean up expired sessions and security data"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                current_time = datetime.utcnow()
                expired_sessions = []

                # Clean expired sessions
                for session_id, session in self._session_cache.items():
                    if self._is_session_expired(session, current_time):
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    await self._revoke_session(session_id, reason="expired")

                # Clean old failed attempts
                cutoff_time = current_time - timedelta(hours=24)
                for key in list(self._failed_attempts.keys()):
                    self._failed_attempts[key] = [
                        attempt for attempt in self._failed_attempts[key] if attempt > cutoff_time
                    ]
                    if not self._failed_attempts[key]:
                        del self._failed_attempts[key]

            except Exception as e:
                await self.audit_logger.log_error("cleanup_task_error", {"error": str(e)}, severity="high")

    async def authenticate_user(
        self, username: str, password: str, ip_address: str, user_agent: str, mfa_code: Optional[str] = None
    ) -> Dict:
        """
        Authenticate user with comprehensive security checks

        Returns:
            dict: Authentication result with tokens and user info
        """
        start_time = time.time()

        try:
            # Security pre-checks
            await self._check_rate_limiting(username, ip_address)
            await self._check_suspicious_activity(ip_address)

            # Get user
            user = await self._get_user_by_username(username)
            if not user:
                await self._record_failed_attempt(username, ip_address, "user_not_found")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

            # Check account status
            if not user.is_active:
                await self.audit_logger.log_security_event(
                    "login_attempt_inactive_user", {"username": username, "ip_address": ip_address}
                )
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

            if user.locked_until and user.locked_until > datetime.utcnow():
                await self.audit_logger.log_security_event(
                    "login_attempt_locked_user",
                    {"username": username, "ip_address": ip_address, "locked_until": user.locked_until},
                )
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

            # Verify password
            if not self._verify_password(password, user):
                await self._record_failed_attempt(username, ip_address, "invalid_password")
                await self._check_account_lockout(user)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

            # Check MFA if enabled
            if user.mfa_enabled:
                if not mfa_code:
                    raise HTTPException(
                        status_code=status.HTTP_200_OK, detail="MFA required", headers={"X-MFA-Required": "true"}
                    )

                if not await self._verify_mfa(user, mfa_code):
                    await self._record_failed_attempt(username, ip_address, "invalid_mfa")
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

            # Create session
            session = await self._create_session(user, ip_address, user_agent)

            # Generate tokens
            access_token = await self._create_access_token(user, session)
            refresh_token = await self._create_refresh_token(user, session)

            # Update user
            user.last_login = datetime.utcnow()
            user.failed_attempts = 0
            user.locked_until = None
            await self._update_user(user)

            # Audit successful login
            await self.audit_logger.log_security_event(
                "successful_login",
                {
                    "user_id": user.user_id,
                    "username": username,
                    "ip_address": ip_address,
                    "session_id": session.session_id,
                    "duration_ms": (time.time() - start_time) * 1000,
                },
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.config.access_token_expire_minutes * 60,
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "roles": [role.name for role in user.roles],
                    "permissions": list(set(perm.name for role in user.roles for perm in role.permissions)),
                },
                "session_id": session.session_id,
            }

        except HTTPException:
            raise
        except Exception as e:
            await self.audit_logger.log_error(
                "authentication_error",
                {"username": username, "ip_address": ip_address, "error": str(e)},
                severity="high",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Authentication service error"
            )

    async def validate_token(self, token: str) -> Dict:
        """
        Validate JWT token and return user/session info

        Returns:
            dict: User and session information
        """
        try:
            # Decode token
            payload = jwt.decode(token, self.config.jwt_secret_key, algorithms=[self.config.jwt_algorithm])

            user_id = payload.get("sub")
            session_id = payload.get("session_id")
            token_type = payload.get("type", "access")

            if not user_id or not session_id:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")

            # Get user and session
            user = await self._get_user_by_id(user_id)
            session = await self._get_session(session_id)

            if not user or not session:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

            # Check session status
            if session.status != SessionStatus.ACTIVE:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not active")

            if self._is_session_expired(session):
                await self._revoke_session(session_id, reason="expired")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

            # Update session activity
            session.last_active = datetime.utcnow()
            await self._update_session(session)

            return {
                "user": user,
                "session": session,
                "permissions": list(set(perm.name for role in user.roles for perm in role.permissions)),
            }

        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    async def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh access token using refresh token"""
        try:
            payload = jwt.decode(refresh_token, self.config.jwt_secret_key, algorithms=[self.config.jwt_algorithm])

            if payload.get("type") != "refresh":
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

            user_id = payload.get("sub")
            session_id = payload.get("session_id")

            user = await self._get_user_by_id(user_id)
            session = await self._get_session(session_id)

            if not user or not session or session.status != SessionStatus.ACTIVE:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

            # Create new access token
            new_access_token = await self._create_access_token(user, session)

            await self.audit_logger.log_security_event(
                "token_refreshed", {"user_id": user_id, "session_id": session_id}
            )

            return {
                "access_token": new_access_token,
                "token_type": "bearer",
                "expires_in": self.config.access_token_expire_minutes * 60,
            }

        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    async def revoke_session(self, session_id: str, user_id: str) -> bool:
        """Revoke a specific session"""
        session = await self._get_session(session_id)
        if session and session.user_id == user_id:
            await self._revoke_session(session_id, reason="user_logout")
            return True
        return False

    async def revoke_all_sessions(self, user_id: str, except_session: Optional[str] = None) -> int:
        """Revoke all sessions for a user"""
        sessions = self._active_sessions.get(user_id, set())
        revoked_count = 0

        for session_id in list(sessions):
            if except_session and session_id == except_session:
                continue

            await self._revoke_session(session_id, reason="revoke_all")
            revoked_count += 1

        await self.audit_logger.log_security_event(
            "all_sessions_revoked", {"user_id": user_id, "revoked_count": revoked_count}
        )

        return revoked_count

    async def get_active_sessions(self, user_id: str) -> List[Session]:
        """Get all active sessions for a user"""
        session_ids = self._active_sessions.get(user_id, set())
        sessions = []

        for session_id in session_ids:
            session = await self._get_session(session_id)
            if session and session.status == SessionStatus.ACTIVE:
                sessions.append(session)

        return sessions

    async def check_user_permissions(self, user_id: str, required_permissions: List[str]) -> bool:
        """Check if user has required permissions"""
        user = await self._get_user_by_id(user_id)
        if not user:
            return False

        user_permissions = set(perm.name for role in user.roles for perm in role.permissions)

        return all(perm in user_permissions for perm in required_permissions)

    # Private helper methods

    async def _get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username from PostgreSQL"""
        from ghl_real_estate_ai.services.database_service import get_database

        db = await get_database()

        async with db.get_connection() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)

            if row:
                u = dict(row)
                return User(
                    user_id=str(u["id"]),
                    username=u["username"],
                    email=u["email"],
                    full_name=u["full_name"],
                    roles=[Role(r) for r in u["roles"]],
                    provider=AuthProvider(u["provider"]),
                    is_active=u["is_active"],
                    is_verified=u["is_verified"],
                    is_admin=u["is_admin"],
                    created_at=u["created_at"],
                    last_login=u["last_login"],
                    failed_attempts=u["failed_attempts"],
                    locked_until=u["locked_until"],
                    password_changed_at=u["password_changed_at"],
                    mfa_enabled=u["mfa_enabled"],
                    mfa_secret=u["mfa_secret"],
                )
        return None

    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID from PostgreSQL"""
        # Check cache first
        if user_id in self._user_cache:
            return self._user_cache[user_id]

        from ghl_real_estate_ai.services.database_service import get_database

        db = await get_database()

        async with db.get_connection() as conn:
            try:
                import uuid

                row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", uuid.UUID(user_id))
            except Exception:
                return None

            if row:
                u = dict(row)
                user = User(
                    user_id=str(u["id"]),
                    username=u["username"],
                    email=u["email"],
                    full_name=u["full_name"],
                    roles=[Role(r) for r in u["roles"]],
                    provider=AuthProvider(u["provider"]),
                    is_active=u["is_active"],
                    is_verified=u["is_verified"],
                    is_admin=u["is_admin"],
                    created_at=u["created_at"],
                    last_login=u["last_login"],
                    failed_attempts=u["failed_attempts"],
                    locked_until=u["locked_until"],
                    password_changed_at=u["password_changed_at"],
                    mfa_enabled=u["mfa_enabled"],
                    mfa_secret=u["mfa_secret"],
                )
                self._user_cache[user_id] = user
                return user
        return None

    def _verify_password(self, password: str, user: User) -> bool:
        """Verify password against user's stored password using bcrypt"""
        if not user.password_hash:
            logger.warning(f"No password hash for user {user.username}")
            return False

        try:
            import bcrypt

            return bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8"))
        except Exception as e:
            logger.error(f"Password verification failed for user {user.username}: {e}")
            return False

    async def _verify_mfa(self, user: User, mfa_code: str) -> bool:
        """Verify MFA code using TOTP"""
        if not user.mfa_secret:
            logger.warning(f"No MFA secret for user {user.username}")
            return False

        try:
            import pyotp

            totp = pyotp.TOTP(user.mfa_secret)
            is_valid = totp.verify(mfa_code, valid_window=1)  # Allow 30-second window

            if not is_valid:
                await self.audit_logger.log_security_event(
                    "mfa_verification_failed", {"username": user.username, "ip_address": "unknown"}
                )

            return is_valid
        except Exception as e:
            logger.error(f"MFA verification failed for user {user.username}: {e}")
            await self.audit_logger.log_security_event(
                "mfa_verification_error", {"username": user.username, "error": str(e)}
            )
            return False

    async def _create_session(self, user: User, ip_address: str, user_agent: str) -> Session:
        """Create a new user session with Redis and PostgreSQL persistence"""
        session_id = secrets.token_urlsafe(32)
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=self.config.session_timeout_minutes)

        session = Session(
            session_id=session_id,
            user_id=user.user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=now,
            last_active=now,
            status=SessionStatus.ACTIVE,
        )

        # 1. Store session in Redis
        session_key = f"session:{session_id}"
        session_data = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "created_at": session.created_at.isoformat(),
            "last_active": session.last_active.isoformat(),
            "status": session.status.value,
            "risk_score": session.risk_score,
        }

        await self.redis.set(session_key, json.dumps(session_data), ex=self.config.session_timeout_minutes * 60)

        # 2. Store session in PostgreSQL (Implementation 11)
        from ghl_real_estate_ai.services.database_service import get_database

        db = await get_database()
        async with db.transaction() as conn:
            import uuid

            await conn.execute(
                """
                INSERT INTO sessions (
                    session_id, user_id, ip_address, user_agent, 
                    status, risk_score, created_at, last_active, expires_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
                session_id,
                uuid.UUID(user.user_id),
                ip_address,
                user_agent,
                session.status.value,
                session.risk_score,
                now,
                now,
                expires_at,
            )

        # Track active session IDs for user
        user_sessions_key = f"user_sessions:{user.user_id}"
        await self.redis.sadd(user_sessions_key, session_id)

        # Check concurrent session limit
        active_sessions = await self.redis.smembers(user_sessions_key)
        if len(active_sessions) > self.config.concurrent_sessions_limit:
            # Revoke oldest sessions
            sorted_sessions = list(active_sessions)
            for sid_bytes in sorted_sessions[: -self.config.concurrent_sessions_limit]:
                await self._revoke_session(sid_bytes.decode(), reason="session_limit_exceeded")

        return session

    async def _create_access_token(self, user: User, session: Session) -> str:
        """Create JWT access token"""
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.config.access_token_expire_minutes)

        payload = {
            "sub": user.user_id,
            "session_id": session.session_id,
            "type": "access",
            "iat": now.timestamp(),
            "exp": expire.timestamp(),
            "permissions": [perm.name for role in user.roles for perm in role.permissions],
        }

        return jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)

    async def _create_refresh_token(self, user: User, session: Session) -> str:
        """Create JWT refresh token"""
        now = datetime.utcnow()
        expire = now + timedelta(days=self.config.refresh_token_expire_days)

        payload = {
            "sub": user.user_id,
            "session_id": session.session_id,
            "type": "refresh",
            "iat": now.timestamp(),
            "exp": expire.timestamp(),
        }

        return jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)

    async def _get_session(self, session_id: str) -> Optional[Session]:
        """Get session from Redis with DB fallback (Implementation 11)"""
        # Try Redis first
        session_data = await self.redis.get(f"session:{session_id}")
        if session_data:
            data = json.loads(session_data)
            return Session(
                session_id=data["session_id"],
                user_id=data["user_id"],
                ip_address=data["ip_address"],
                user_agent=data["user_agent"],
                created_at=datetime.fromisoformat(data["created_at"]),
                last_active=datetime.fromisoformat(data["last_active"]),
                status=SessionStatus(data["status"]),
                risk_score=data.get("risk_score", 0.0),
            )

        # Fallback to PostgreSQL (Implementation 11)
        from ghl_real_estate_ai.services.database_service import get_database

        db = await get_database()
        async with db.get_connection() as conn:
            row = await conn.fetchrow("SELECT * FROM sessions WHERE session_id = $1", session_id)
            if row:
                s = dict(row)
                # Re-cache in Redis
                session = Session(
                    session_id=s["session_id"],
                    user_id=str(s["user_id"]),
                    ip_address=s["ip_address"],
                    user_agent=s["user_agent"],
                    created_at=s["created_at"],
                    last_active=s["last_active"],
                    status=SessionStatus(s["status"]),
                    risk_score=float(s["risk_score"]),
                )

                # Update Redis
                session_data = {
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent,
                    "created_at": session.created_at.isoformat(),
                    "last_active": session.last_active.isoformat(),
                    "status": session.status.value,
                    "risk_score": session.risk_score,
                }
                await self.redis.set(
                    f"session:{session_id}", json.dumps(session_data), ex=self.config.session_timeout_minutes * 60
                )
                return session
        return None

    async def _update_session(self, session: Session):
        """Update session in Redis and PostgreSQL (Implementation 11)"""
        # Update Redis
        session_key = f"session:{session.session_id}"
        session_data = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "created_at": session.created_at.isoformat(),
            "last_active": session.last_active.isoformat(),
            "status": session.status.value,
            "risk_score": session.risk_score,
        }
        await self.redis.set(session_key, json.dumps(session_data), ex=self.config.session_timeout_minutes * 60)

        # Update PostgreSQL (Implementation 11)
        from ghl_real_estate_ai.services.database_service import get_database

        db = await get_database()
        async with db.transaction() as conn:
            await conn.execute(
                """
                UPDATE sessions SET
                    last_active = $1,
                    status = $2,
                    risk_score = $3
                WHERE session_id = $4
            """,
                session.last_active,
                session.status.value,
                session.risk_score,
                session.session_id,
            )

    async def _revoke_session(self, session_id: str, reason: str):
        """Revoke a session in Redis"""
        session = await self._get_session(session_id)
        if session:
            session.status = SessionStatus.REVOKED
            await self._update_session(session)

            # Remove from user's active sessions
            user_sessions_key = f"user_sessions:{session.user_id}"
            await self.redis.srem(user_sessions_key, session_id)

        await self.audit_logger.log_security_event("session_revoked", {"session_id": session_id, "reason": reason})

    def _is_session_expired(self, session: Session, current_time: Optional[datetime] = None) -> bool:
        """Check if session is expired"""
        if current_time is None:
            current_time = datetime.utcnow()

        timeout_delta = timedelta(minutes=self.config.session_timeout_minutes)
        return (current_time - session.last_active) > timeout_delta

    async def _check_rate_limiting(self, username: str, ip_address: str):
        """Check rate limiting for authentication attempts"""
        # TODO: Implement Redis-based rate limiting
        pass

    async def _check_suspicious_activity(self, ip_address: str):
        """Check for suspicious IP activity"""
        if ip_address in self._suspicious_ips:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Suspicious activity detected")

    async def _record_failed_attempt(self, username: str, ip_address: str, reason: str):
        """Record failed authentication attempt"""
        now = datetime.utcnow()

        # Record by username
        if username not in self._failed_attempts:
            self._failed_attempts[username] = []
        self._failed_attempts[username].append(now)

        # Record by IP
        ip_key = f"ip:{ip_address}"
        if ip_key not in self._failed_attempts:
            self._failed_attempts[ip_key] = []
        self._failed_attempts[ip_key].append(now)

        await self.audit_logger.log_security_event(
            "failed_login_attempt", {"username": username, "ip_address": ip_address, "reason": reason}
        )

    async def _check_account_lockout(self, user: User):
        """Check if account should be locked due to failed attempts"""
        username = user.username
        recent_failures = len(
            [
                attempt
                for attempt in self._failed_attempts.get(username, [])
                if attempt > datetime.utcnow() - timedelta(minutes=15)
            ]
        )

        if recent_failures >= self.config.max_failed_attempts:
            user.locked_until = datetime.utcnow() + timedelta(minutes=self.config.lockout_duration_minutes)
            await self._update_user(user)

            await self.audit_logger.log_security_event(
                "account_locked",
                {
                    "user_id": user.user_id,
                    "username": username,
                    "failed_attempts": recent_failures,
                    "locked_until": user.locked_until,
                },
            )

    async def _update_user(self, user: User):
        """Update user in PostgreSQL"""
        from ghl_real_estate_ai.services.database_service import get_database

        db = await get_database()

        async with db.transaction() as conn:
            import uuid

            await conn.execute(
                """
                UPDATE users SET
                    last_login = $1,
                    failed_attempts = $2,
                    locked_until = $3,
                    updated_at = NOW()
                WHERE id = $4
            """,
                user.last_login,
                user.failed_attempts,
                user.locked_until,
                uuid.UUID(user.user_id),
            )
