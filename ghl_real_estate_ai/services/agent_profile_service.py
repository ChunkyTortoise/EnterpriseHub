"""
Multi-Tenant Agent Profile Service

This service handles all agent profile operations with multi-tenant support,
building on the existing EnterpriseHub service patterns and infrastructure.

Features:
- Shared agent pool with location-based access control
- Session-based context management
- Redis caching with PostgreSQL persistence
- Integration with existing services
- Graceful fallbacks and error handling
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import uuid

# Database and caching
import asyncpg
import redis.asyncio as redis

# Models and base classes
from ..models.agent_profile_models import (
    AgentProfile, AgentSession, CoachingInteraction,
    CreateAgentProfileRequest, UpdateAgentProfileRequest, StartAgentSessionRequest,
    AgentRole, GuidanceType, ConversationStage,
    create_agent_id, create_session_id
)
from .base import BaseService
from ..core.exceptions import (
    ServiceError, ValidationError, NotFoundError, PermissionError
)

logger = logging.getLogger(__name__)


class AgentProfileService(BaseService):
    """
    Multi-tenant agent profile service with Redis caching and PostgreSQL persistence.
    Supports shared agent pool where agents can work across multiple locations.
    """

    def __init__(self, location_id: Optional[str] = None):
        """
        Initialize agent profile service.

        Args:
            location_id: Primary location context for multi-tenant operations
        """
        super().__init__()
        self.location_id = location_id or "default"

        # Redis client for caching
        self._redis_client = None

        # Database pool for persistence
        self._db_pool = None

        # Cache configuration
        self.cache_config = {
            "profile_ttl": 3600,  # 1 hour for agent profiles
            "session_ttl": 1800,  # 30 minutes for active sessions
            "location_agents_ttl": 1800,  # 30 minutes for location agent lists
            "coaching_context_ttl": 300,  # 5 minutes for coaching context
        }

        # Performance metrics
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "db_operations": 0,
            "errors": 0
        }

    async def _get_redis_client(self) -> redis.Redis:
        """Get Redis client with connection pooling"""
        if not self._redis_client:
            try:
                self._redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=True,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30
                )
                # Test connection
                await self._redis_client.ping()
                logger.info("Redis connection established for AgentProfileService")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Operating without cache.")
                self._redis_client = None
        return self._redis_client

    async def _get_db_pool(self) -> asyncpg.Pool:
        """Get PostgreSQL connection pool"""
        if not self._db_pool:
            try:
                self._db_pool = await asyncpg.create_pool(
                    host='localhost',
                    port=5432,
                    database='enterprisehub',
                    user='postgres',
                    password='postgres',  # Should use environment variables
                    min_size=5,
                    max_size=20,
                    command_timeout=60
                )
                logger.info("PostgreSQL connection pool created for AgentProfileService")
            except Exception as e:
                logger.error(f"Database connection failed: {e}")
                raise ServiceError(f"Database unavailable: {e}")
        return self._db_pool

    def _generate_cache_key(self, key_type: str, *args) -> str:
        """Generate Redis cache key with tenant isolation"""
        return f"agent_profile:{self.location_id}:{key_type}:{':'.join(map(str, args))}"

    async def _cache_get(self, key: str) -> Optional[Any]:
        """Get value from cache with metrics tracking"""
        try:
            redis_client = await self._get_redis_client()
            if redis_client:
                value = await redis_client.get(key)
                if value:
                    self.metrics["cache_hits"] += 1
                    return json.loads(value)
                else:
                    self.metrics["cache_misses"] += 1
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            self.metrics["errors"] += 1
        return None

    async def _cache_set(self, key: str, value: Any, ttl: int):
        """Set value in cache with TTL"""
        try:
            redis_client = await self._get_redis_client()
            if redis_client:
                json_value = json.dumps(value, default=str)
                await redis_client.setex(key, ttl, json_value)
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            self.metrics["errors"] += 1

    async def _cache_delete(self, key: str):
        """Delete value from cache"""
        try:
            redis_client = await self._get_redis_client()
            if redis_client:
                await redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete error: {e}")

    # ============================================================================
    # Agent Profile Management
    # ============================================================================

    async def create_agent_profile(
        self,
        profile_data: CreateAgentProfileRequest,
        creator_location_id: Optional[str] = None
    ) -> AgentProfile:
        """
        Create new agent profile with multi-tenant support.

        Args:
            profile_data: Profile creation data
            creator_location_id: Location ID of the creator (for access control)

        Returns:
            Created AgentProfile

        Raises:
            ValidationError: If profile data is invalid
            PermissionError: If creator lacks permission
            ServiceError: If creation fails
        """
        try:
            # Generate unique agent ID
            agent_id = create_agent_id(profile_data.agent_name, profile_data.email)

            # Validate location access
            creator_location = creator_location_id or self.location_id
            if not self._validate_location_access(creator_location, profile_data.primary_location_id):
                raise PermissionError(f"No permission to create agent for location {profile_data.primary_location_id}")

            # Build accessible locations list
            accessible_locations = profile_data.accessible_locations or [profile_data.primary_location_id]
            if profile_data.primary_location_id not in accessible_locations:
                accessible_locations.append(profile_data.primary_location_id)

            # Create profile object
            profile = AgentProfile(
                agent_id=agent_id,
                agent_name=profile_data.agent_name,
                email=profile_data.email,
                phone=profile_data.phone,
                primary_location_id=profile_data.primary_location_id,
                accessible_locations=accessible_locations,
                role_permissions=profile_data.role_permissions or {},
                primary_role=profile_data.primary_role,
                secondary_roles=profile_data.secondary_roles or [],
                years_experience=profile_data.years_experience or 0,
                specializations=profile_data.specializations or [],
                preferred_guidance_types=profile_data.preferred_guidance_types or [
                    GuidanceType.RESPONSE_SUGGESTIONS, GuidanceType.STRATEGY_COACHING
                ],
                coaching_style_preference=profile_data.coaching_style_preference or "balanced",
                communication_style=profile_data.communication_style or "professional",
                timezone=profile_data.timezone or "UTC",
                language_preference=profile_data.language_preference or "en-US"
            )

            # Insert into database
            db_pool = await self._get_db_pool()
            async with db_pool.acquire() as conn:
                # Set tenant context for RLS
                await conn.execute("SELECT set_config('app.current_location_id', $1, false)", creator_location)

                await conn.execute("""
                    INSERT INTO agent_profiles (
                        agent_id, agent_name, email, phone,
                        primary_location_id, accessible_locations, role_permissions,
                        primary_role, secondary_roles, years_experience, specializations,
                        preferred_guidance_types, coaching_style_preference, communication_style,
                        timezone, language_preference, created_at, updated_at
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                """,
                    profile.agent_id, profile.agent_name, profile.email, profile.phone,
                    profile.primary_location_id, json.dumps(profile.accessible_locations),
                    json.dumps(profile.role_permissions),
                    profile.primary_role.value, json.dumps([r.value for r in profile.secondary_roles]),
                    profile.years_experience, json.dumps(profile.specializations),
                    json.dumps([g.value for g in profile.preferred_guidance_types]),
                    profile.coaching_style_preference.value, profile.communication_style.value,
                    profile.timezone, profile.language_preference,
                    profile.created_at, profile.updated_at
                )

            self.metrics["db_operations"] += 1

            # Cache the new profile
            cache_key = self._generate_cache_key("profile", agent_id)
            await self._cache_set(cache_key, profile.to_dict(), self.cache_config["profile_ttl"])

            # Invalidate location agent list cache
            await self._invalidate_location_caches(accessible_locations)

            logger.info(f"Created agent profile: {agent_id} for locations: {accessible_locations}")
            return profile

        except asyncpg.UniqueViolationError:
            raise ValidationError(f"Agent with email {profile_data.email} already exists")
        except Exception as e:
            logger.error(f"Error creating agent profile: {e}")
            self.metrics["errors"] += 1
            if isinstance(e, (ValidationError, PermissionError)):
                raise
            raise ServiceError(f"Failed to create agent profile: {e}")

    async def get_agent_profile(
        self,
        agent_id: str,
        requester_location_id: Optional[str] = None
    ) -> Optional[AgentProfile]:
        """
        Get agent profile with caching and multi-tenant access control.

        Args:
            agent_id: Agent identifier
            requester_location_id: Location context for access control

        Returns:
            AgentProfile if found and accessible, None otherwise
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key("profile", agent_id)
            cached_data = await self._cache_get(cache_key)
            if cached_data:
                profile = AgentProfile.parse_obj(cached_data)
                # Validate access
                requester_location = requester_location_id or self.location_id
                if profile.has_access_to_location(requester_location):
                    return profile
                else:
                    return None  # No access to this profile

            # Query database
            db_pool = await self._get_db_pool()
            async with db_pool.acquire() as conn:
                # Set tenant context for RLS
                requester_location = requester_location_id or self.location_id
                await conn.execute("SELECT set_config('app.current_location_id', $1, false)", requester_location)

                row = await conn.fetchrow("""
                    SELECT * FROM agent_profiles WHERE agent_id = $1 AND is_active = true
                """, agent_id)

                if not row:
                    return None

                # Convert database row to profile
                profile = self._row_to_agent_profile(row)

                # Cache the profile
                await self._cache_set(cache_key, profile.to_dict(), self.cache_config["profile_ttl"])

                self.metrics["db_operations"] += 1
                return profile

        except Exception as e:
            logger.error(f"Error getting agent profile {agent_id}: {e}")
            self.metrics["errors"] += 1
            return None

    async def update_agent_profile(
        self,
        agent_id: str,
        update_data: UpdateAgentProfileRequest,
        updater_location_id: Optional[str] = None
    ) -> Optional[AgentProfile]:
        """
        Update agent profile with validation and caching.

        Args:
            agent_id: Agent identifier
            update_data: Update data
            updater_location_id: Location context for access control

        Returns:
            Updated AgentProfile if successful, None otherwise
        """
        try:
            # Get current profile for access validation
            current_profile = await self.get_agent_profile(agent_id, updater_location_id)
            if not current_profile:
                raise NotFoundError(f"Agent profile {agent_id} not found or no access")

            # Build update fields
            update_fields = {}
            update_params = []
            param_count = 1

            # Helper to add update field
            def add_field(field_name: str, value: Any):
                nonlocal param_count
                if value is not None:
                    update_fields[field_name] = f"${param_count}"
                    update_params.append(value)
                    param_count += 1

            # Process update fields
            add_field("agent_name", update_data.agent_name)
            add_field("phone", update_data.phone)

            if update_data.accessible_locations is not None:
                add_field("accessible_locations", json.dumps(update_data.accessible_locations))

            if update_data.role_permissions is not None:
                add_field("role_permissions", json.dumps(update_data.role_permissions))

            if update_data.secondary_roles is not None:
                add_field("secondary_roles", json.dumps([r.value for r in update_data.secondary_roles]))

            add_field("years_experience", update_data.years_experience)

            if update_data.specializations is not None:
                add_field("specializations", json.dumps(update_data.specializations))

            if update_data.preferred_guidance_types is not None:
                add_field("preferred_guidance_types",
                         json.dumps([g.value for g in update_data.preferred_guidance_types]))

            if update_data.coaching_style_preference is not None:
                add_field("coaching_style_preference", update_data.coaching_style_preference.value)

            if update_data.communication_style is not None:
                add_field("communication_style", update_data.communication_style.value)

            if update_data.skill_levels is not None:
                add_field("skill_levels", json.dumps(update_data.skill_levels))

            if update_data.notification_preferences is not None:
                add_field("notification_preferences", json.dumps(update_data.notification_preferences))

            add_field("timezone", update_data.timezone)
            add_field("language_preference", update_data.language_preference)
            add_field("is_active", update_data.is_active)

            if not update_fields:
                return current_profile  # No changes

            # Always update the timestamp
            update_fields["updated_at"] = f"${param_count}"
            update_params.append(datetime.utcnow())

            # Build and execute update query
            set_clause = ", ".join([f"{field} = {placeholder}" for field, placeholder in update_fields.items()])
            query = f"""
                UPDATE agent_profiles
                SET {set_clause}
                WHERE agent_id = ${param_count + 1} AND is_active = true
                RETURNING *
            """
            update_params.append(agent_id)

            db_pool = await self._get_db_pool()
            async with db_pool.acquire() as conn:
                # Set tenant context
                updater_location = updater_location_id or self.location_id
                await conn.execute("SELECT set_config('app.current_location_id', $1, false)", updater_location)

                row = await conn.fetchrow(query, *update_params)

                if not row:
                    return None

                # Convert to profile
                updated_profile = self._row_to_agent_profile(row)

                # Update cache
                cache_key = self._generate_cache_key("profile", agent_id)
                await self._cache_set(cache_key, updated_profile.to_dict(), self.cache_config["profile_ttl"])

                # Invalidate location caches if accessible locations changed
                if update_data.accessible_locations is not None:
                    await self._invalidate_location_caches(update_data.accessible_locations)

                self.metrics["db_operations"] += 1
                logger.info(f"Updated agent profile: {agent_id}")
                return updated_profile

        except Exception as e:
            logger.error(f"Error updating agent profile {agent_id}: {e}")
            self.metrics["errors"] += 1
            if isinstance(e, (NotFoundError, ValidationError)):
                raise
            raise ServiceError(f"Failed to update agent profile: {e}")

    async def get_agents_for_location(
        self,
        location_id: str,
        role_filter: Optional[AgentRole] = None,
        active_only: bool = True
    ) -> List[AgentProfile]:
        """
        Get all agents accessible to a location (Shared Agent Pool).

        Args:
            location_id: Location identifier
            role_filter: Optional role filter
            active_only: Only return active agents

        Returns:
            List of accessible agents
        """
        try:
            # Check cache
            cache_key = self._generate_cache_key("location_agents", location_id, role_filter or "all", active_only)
            cached_data = await self._cache_get(cache_key)
            if cached_data:
                return [AgentProfile.parse_obj(agent_data) for agent_data in cached_data]

            # Query database using the stored function
            db_pool = await self._get_db_pool()
            async with db_pool.acquire() as conn:
                # Set tenant context
                await conn.execute("SELECT set_config('app.current_location_id', $1, false)", location_id)

                role_value = role_filter.value if role_filter else None
                rows = await conn.fetch("""
                    SELECT * FROM get_agents_for_location($1, $2)
                """, location_id, role_value)

                # Convert rows to profiles
                profiles = []
                for row in rows:
                    if not active_only or row['is_active']:
                        # Fetch full profile data
                        full_row = await conn.fetchrow("""
                            SELECT * FROM agent_profiles WHERE agent_id = $1
                        """, row['agent_id'])
                        if full_row:
                            profile = self._row_to_agent_profile(full_row)
                            profiles.append(profile)

                # Cache results
                profiles_data = [profile.to_dict() for profile in profiles]
                await self._cache_set(cache_key, profiles_data, self.cache_config["location_agents_ttl"])

                self.metrics["db_operations"] += 1
                return profiles

        except Exception as e:
            logger.error(f"Error getting agents for location {location_id}: {e}")
            self.metrics["errors"] += 1
            return []

    # ============================================================================
    # Session Management
    # ============================================================================

    async def start_agent_session(
        self,
        agent_id: str,
        location_id: str,
        guidance_types: Optional[List[GuidanceType]] = None,
        session_data: Optional[StartAgentSessionRequest] = None
    ) -> AgentSession:
        """
        Start new agent session with profile context.

        Args:
            agent_id: Agent identifier
            location_id: Session location context
            guidance_types: Optional guidance type override
            session_data: Optional additional session data

        Returns:
            Created AgentSession

        Raises:
            NotFoundError: If agent not found or no access
            ServiceError: If session creation fails
        """
        try:
            # Validate agent has location access
            agent_profile = await self.get_agent_profile(agent_id, location_id)
            if not agent_profile:
                raise NotFoundError(f"Agent {agent_id} not found or no access to location {location_id}")

            # Generate session ID
            session_id = create_session_id(agent_id)

            # Use guidance types from request, profile, or defaults
            active_guidance_types = guidance_types or agent_profile.preferred_guidance_types or [
                GuidanceType.RESPONSE_SUGGESTIONS
            ]

            # Create session object
            session = AgentSession(
                session_id=session_id,
                agent_id=agent_id,
                location_id=location_id,
                active_guidance_types=active_guidance_types,
                conversation_stage=session_data.conversation_stage if session_data else ConversationStage.DISCOVERY,
                current_lead_id=session_data.current_lead_id if session_data else None,
                client_info=session_data.client_info if session_data else {},
                property_context=session_data.property_context if session_data else {},
                market_context=session_data.market_context if session_data else {},
                ghl_contact_id=session_data.ghl_contact_id if session_data else None,
                qualification_flow_id=session_data.qualification_flow_id if session_data else None
            )

            # Store in database
            db_pool = await self._get_db_pool()
            async with db_pool.acquire() as conn:
                # Set tenant context
                await conn.execute("SELECT set_config('app.current_location_id', $1, false)", location_id)

                await conn.execute("""
                    INSERT INTO agent_sessions (
                        session_id, agent_id, location_id, current_lead_id,
                        conversation_stage, workflow_context, active_guidance_types,
                        session_start_time, last_activity, client_info,
                        property_context, market_context, ghl_contact_id,
                        qualification_flow_id, is_active
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                """,
                    session.session_id, session.agent_id, session.location_id,
                    session.current_lead_id, session.conversation_stage.value,
                    json.dumps(session.workflow_context),
                    json.dumps([g.value for g in session.active_guidance_types]),
                    session.session_start_time, session.last_activity,
                    json.dumps(session.client_info), json.dumps(session.property_context),
                    json.dumps(session.market_context), session.ghl_contact_id,
                    session.qualification_flow_id, session.is_active
                )

            # Store in Redis cache
            cache_key = self._generate_cache_key("session", session_id)
            await self._cache_set(cache_key, session.to_dict(), self.cache_config["session_ttl"])

            # Update agent profile with current session
            await self._update_agent_current_session(agent_id, session_id)

            self.metrics["db_operations"] += 1
            logger.info(f"Started agent session: {session_id} for agent: {agent_id}")
            return session

        except Exception as e:
            logger.error(f"Error starting agent session: {e}")
            self.metrics["errors"] += 1
            if isinstance(e, NotFoundError):
                raise
            raise ServiceError(f"Failed to start agent session: {e}")

    async def get_agent_session(self, session_id: str) -> Optional[AgentSession]:
        """Get agent session with caching"""
        try:
            # Check cache first
            cache_key = self._generate_cache_key("session", session_id)
            cached_data = await self._cache_get(cache_key)
            if cached_data:
                return AgentSession.parse_obj(cached_data)

            # Query database
            db_pool = await self._get_db_pool()
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM agent_sessions WHERE session_id = $1
                """, session_id)

                if not row:
                    return None

                session = self._row_to_agent_session(row)

                # Cache the session
                await self._cache_set(cache_key, session.to_dict(), self.cache_config["session_ttl"])

                self.metrics["db_operations"] += 1
                return session

        except Exception as e:
            logger.error(f"Error getting agent session {session_id}: {e}")
            self.metrics["errors"] += 1
            return None

    async def end_agent_session(self, session_id: str) -> bool:
        """End agent session and calculate final metrics"""
        try:
            session = await self.get_agent_session(session_id)
            if not session or not session.is_active:
                return False

            # Calculate final duration
            session.end_session()

            # Update database
            db_pool = await self._get_db_pool()
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE agent_sessions
                    SET session_end_time = $1, is_active = false,
                        session_duration_seconds = $2, last_activity = $3
                    WHERE session_id = $4
                """, session.session_end_time, session.session_duration_seconds,
                    session.last_activity, session_id)

            # Remove from cache
            cache_key = self._generate_cache_key("session", session_id)
            await self._cache_delete(cache_key)

            # Clear current session from agent profile
            await self._update_agent_current_session(session.agent_id, None)

            self.metrics["db_operations"] += 1
            logger.info(f"Ended agent session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error ending agent session {session_id}: {e}")
            self.metrics["errors"] += 1
            return False

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _row_to_agent_profile(self, row) -> AgentProfile:
        """Convert database row to AgentProfile object"""
        return AgentProfile(
            agent_id=row['agent_id'],
            agent_name=row['agent_name'],
            email=row['email'],
            phone=row['phone'],
            primary_location_id=row['primary_location_id'],
            accessible_locations=row['accessible_locations'] or [],
            role_permissions=row['role_permissions'] or {},
            primary_role=AgentRole(row['primary_role']),
            secondary_roles=[AgentRole(r) for r in (row['secondary_roles'] or [])],
            years_experience=row['years_experience'],
            specializations=row['specializations'] or [],
            preferred_guidance_types=[GuidanceType(g) for g in (row['preferred_guidance_types'] or [])],
            coaching_style_preference=row['coaching_style_preference'],
            communication_style=row['communication_style'],
            current_session_id=row['current_session_id'],
            active_conversations=row['active_conversations'] or [],
            skill_levels=row['skill_levels'] or {},
            performance_metrics_summary=row['performance_metrics_summary'] or {},
            notification_preferences=row['notification_preferences'] or {},
            timezone=row['timezone'],
            language_preference=row['language_preference'],
            profile_version=row['profile_version'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            is_active=row['is_active'],
            last_login=row['last_login'],
            login_count=row['login_count']
        )

    def _row_to_agent_session(self, row) -> AgentSession:
        """Convert database row to AgentSession object"""
        return AgentSession(
            session_id=row['session_id'],
            agent_id=row['agent_id'],
            location_id=row['location_id'],
            current_lead_id=row['current_lead_id'],
            conversation_stage=ConversationStage(row['conversation_stage']),
            workflow_context=row['workflow_context'] or {},
            system_prompt_version=row['system_prompt_version'],
            conversation_history_summary=row['conversation_history_summary'],
            active_guidance_types=[GuidanceType(g) for g in (row['active_guidance_types'] or [])],
            session_start_time=row['session_start_time'],
            session_duration_seconds=row['session_duration_seconds'],
            messages_exchanged=row['messages_exchanged'],
            guidance_requests=row['guidance_requests'],
            coaching_effectiveness_score=row['coaching_effectiveness_score'],
            client_info=row['client_info'] or {},
            property_context=row['property_context'] or {},
            market_context=row['market_context'] or {},
            is_active=row['is_active'],
            last_activity=row['last_activity'],
            session_end_time=row['session_end_time'],
            ghl_contact_id=row['ghl_contact_id'],
            qualification_flow_id=row['qualification_flow_id'],
            opportunity_id=row['opportunity_id']
        )

    def _validate_location_access(self, requester_location: str, target_location: str) -> bool:
        """Validate if requester has access to target location"""
        # Super admin access
        if requester_location == "admin":
            return True
        # Same location access
        if requester_location == target_location:
            return True
        # TODO: Implement more sophisticated location hierarchy validation
        return False

    async def _update_agent_current_session(self, agent_id: str, session_id: Optional[str]):
        """Update agent's current session ID"""
        try:
            db_pool = await self._get_db_pool()
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE agent_profiles SET current_session_id = $1, updated_at = $2
                    WHERE agent_id = $3
                """, session_id, datetime.utcnow(), agent_id)

            # Invalidate profile cache
            cache_key = self._generate_cache_key("profile", agent_id)
            await self._cache_delete(cache_key)

        except Exception as e:
            logger.warning(f"Failed to update agent current session: {e}")

    async def _invalidate_location_caches(self, location_ids: List[str]):
        """Invalidate cached data for locations"""
        try:
            redis_client = await self._get_redis_client()
            if redis_client:
                # Build cache key patterns to delete
                patterns = []
                for location_id in location_ids:
                    patterns.append(f"agent_profile:{location_id}:location_agents:*")

                # Delete matching keys
                for pattern in patterns:
                    keys = await redis_client.keys(pattern)
                    if keys:
                        await redis_client.delete(*keys)

        except Exception as e:
            logger.warning(f"Failed to invalidate location caches: {e}")

    async def get_service_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics"""
        cache_hit_rate = 0.0
        if self.metrics["cache_hits"] + self.metrics["cache_misses"] > 0:
            cache_hit_rate = self.metrics["cache_hits"] / (
                self.metrics["cache_hits"] + self.metrics["cache_misses"]
            )

        return {
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": self.metrics["cache_hits"],
            "cache_misses": self.metrics["cache_misses"],
            "db_operations": self.metrics["db_operations"],
            "errors": self.metrics["errors"],
            "redis_connected": self._redis_client is not None,
            "db_connected": self._db_pool is not None
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on service dependencies"""
        health = {
            "service": "AgentProfileService",
            "status": "healthy",
            "checks": {}
        }

        # Check Redis
        try:
            redis_client = await self._get_redis_client()
            if redis_client:
                await redis_client.ping()
                health["checks"]["redis"] = "healthy"
            else:
                health["checks"]["redis"] = "unavailable"
        except Exception as e:
            health["checks"]["redis"] = f"error: {e}"
            health["status"] = "degraded"

        # Check PostgreSQL
        try:
            db_pool = await self._get_db_pool()
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health["checks"]["postgresql"] = "healthy"
        except Exception as e:
            health["checks"]["postgresql"] = f"error: {e}"
            health["status"] = "unhealthy"

        return health