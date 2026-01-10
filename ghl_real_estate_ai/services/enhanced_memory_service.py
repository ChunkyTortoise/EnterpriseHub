"""
Enhanced Memory Service for Multi-Tenant Continuous Memory System.

Extends existing MemoryService with PostgreSQL/Redis backend while maintaining
backward compatibility with the current file-based system.
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4
import time

from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.models.memory_models import (
    Tenant, Conversation, ConversationMessage, ConversationWithMemory,
    BehavioralPreference, PropertyInteraction, PreferenceType, InteractionType,
    ConversationStage, MessageRole, convert_legacy_context_to_conversation,
    convert_conversation_to_legacy_context
)
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class DatabasePool:
    """Database connection pool management."""

    def __init__(self):
        self.pool = None
        self.initialized = False

    async def initialize(self):
        """Initialize database connection pool."""
        if self.initialized:
            return

        try:
            import asyncpg
            self.pool = await asyncpg.create_pool(
                dsn=getattr(settings, 'database_url', None),
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            self.initialized = True
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            self.pool = None
            self.initialized = False

    async def get_connection(self):
        """Get database connection from pool."""
        if not self.initialized:
            await self.initialize()
        return self.pool

    async def execute(self, query: str, *args):
        """Execute a query."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Fetch multiple rows."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        """Fetch single row."""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)


class RedisClient:
    """Redis client for caching."""

    def __init__(self):
        self.client = None
        self.initialized = False

    async def initialize(self):
        """Initialize Redis connection."""
        if self.initialized:
            return

        try:
            import aioredis
            redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
            self.client = aioredis.from_url(
                redis_url,
                max_connections=getattr(settings, 'redis_max_connections', 20),
                decode_responses=True
            )
            await self.client.ping()
            self.initialized = True
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            self.client = None
            self.initialized = False

    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        if not self.client:
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        """Set value with expiration."""
        if not self.client:
            return False
        try:
            await self.client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Redis SETEX error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self.client:
            return False
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self.client:
            return False
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False


class EnhancedMemoryService(MemoryService):
    """
    Enhanced memory service with PostgreSQL backend and continuous memory.
    Extends existing MemoryService for backward compatibility.
    """

    def __init__(self, use_database: bool = None, use_redis: bool = None):
        """
        Initialize enhanced memory service.

        Args:
            use_database: Whether to use PostgreSQL backend. Auto-detected if None.
            use_redis: Whether to use Redis caching. Auto-detected if None.
        """
        super().__init__()

        # Auto-detect database availability
        if use_database is None:
            use_database = hasattr(settings, 'database_url') and settings.database_url is not None

        if use_redis is None:
            use_redis = hasattr(settings, 'redis_url') and settings.redis_url is not None

        self.use_database = use_database
        self.use_redis = use_redis

        # Initialize database and Redis clients
        self.db_pool = DatabasePool() if use_database else None
        self.redis_client = RedisClient() if use_redis else None

        # Performance metrics
        self.metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "db_queries": 0,
            "avg_response_time_ms": 0
        }

        logger.info(f"Enhanced memory service initialized - Database: {use_database}, Redis: {use_redis}")

    async def ensure_initialized(self):
        """Ensure database and Redis connections are initialized."""
        if self.db_pool and not self.db_pool.initialized:
            await self.db_pool.initialize()

        if self.redis_client and not self.redis_client.initialized:
            await self.redis_client.initialize()

    async def get_conversation_with_memory(
        self,
        tenant_id: str,
        contact_id: str,
        include_behavioral_context: bool = True,
        message_limit: int = 50
    ) -> ConversationWithMemory:
        """
        Retrieve conversation with full memory context including:
        - Message history with intelligent truncation
        - Behavioral preferences learned over time
        - Property interaction patterns
        - Smart resume context for conversation gaps
        """
        start_time = time.time()

        try:
            await self.ensure_initialized()

            if not self.use_database:
                # Fallback to existing file-based system during migration
                return await self._get_legacy_context_enhanced(tenant_id, contact_id)

            # Try Redis cache first (L1)
            cache_key = f"conv_memory:{tenant_id}:{contact_id}"
            if self.use_redis:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    self.metrics["cache_hits"] += 1
                    conversation_with_memory = ConversationWithMemory.from_cache(cached_data)

                    # Update memory context summary
                    await self._update_memory_context_summary(conversation_with_memory)

                    return conversation_with_memory

            self.metrics["cache_misses"] += 1

            # Load from PostgreSQL (L2)
            conversation_with_memory = await self._load_conversation_from_db(
                tenant_id, contact_id, include_behavioral_context, message_limit
            )

            # Cache for future requests (30min TTL for active conversations)
            if self.use_redis and conversation_with_memory:
                ttl = self._calculate_cache_ttl(conversation_with_memory.conversation.last_interaction_at)
                await self.redis_client.setex(cache_key, ttl, conversation_with_memory.to_cache())

            return conversation_with_memory

        except Exception as e:
            logger.error(f"Error retrieving conversation with memory: {e}")
            # Fallback to legacy system on error
            return await self._get_legacy_context_enhanced(tenant_id, contact_id)

        finally:
            # Update performance metrics
            response_time_ms = (time.time() - start_time) * 1000
            self._update_metrics(response_time_ms)

    async def _load_conversation_from_db(
        self,
        tenant_id: str,
        contact_id: str,
        include_behavioral_context: bool = True,
        message_limit: int = 50
    ) -> ConversationWithMemory:
        """Load conversation from PostgreSQL database."""

        self.metrics["db_queries"] += 1

        # Get tenant UUID
        tenant_uuid = await self._get_or_create_tenant_uuid(tenant_id)

        # Load base conversation
        conversation_row = await self.db_pool.fetchrow(
            """
            SELECT id, tenant_id, contact_id, conversation_stage, lead_score, last_interaction_at,
                   extracted_preferences, lead_intelligence, previous_sessions_summary,
                   behavioral_profile, session_count, total_messages, created_at, updated_at
            FROM conversations
            WHERE tenant_id = $1 AND contact_id = $2
            """,
            tenant_uuid, contact_id
        )

        if not conversation_row:
            # Create new conversation
            conversation = await self._create_new_conversation(tenant_uuid, contact_id)
        else:
            conversation = self._row_to_conversation(conversation_row)

        # Load message history
        message_rows = await self.db_pool.fetch(
            """
            SELECT id, conversation_id, role, content, timestamp, metadata,
                   claude_reasoning, response_time_ms, token_count, message_order
            FROM conversation_messages
            WHERE conversation_id = $1
            ORDER BY message_order DESC
            LIMIT $2
            """,
            conversation.id, message_limit
        )

        message_history = [self._row_to_message(row) for row in message_rows]

        # Create base ConversationWithMemory
        conversation_with_memory = ConversationWithMemory(
            conversation=conversation,
            message_history=message_history
        )

        # Load behavioral context if requested
        if include_behavioral_context:
            # Load behavioral preferences
            pref_rows = await self.db_pool.fetch(
                """
                SELECT id, conversation_id, preference_type, preference_value, confidence_score,
                       learned_from, source_interaction_id, timestamp, created_at, updated_at
                FROM behavioral_preferences
                WHERE conversation_id = $1
                ORDER BY timestamp DESC
                """,
                conversation.id
            )

            conversation_with_memory.behavioral_preferences = [
                self._row_to_behavioral_preference(row) for row in pref_rows
            ]

            # Load property interactions
            interaction_rows = await self.db_pool.fetch(
                """
                SELECT id, conversation_id, property_id, property_data, interaction_type,
                       feedback_category, feedback_text, time_on_property, claude_analysis,
                       behavioral_signals, timestamp, created_at
                FROM property_interactions
                WHERE conversation_id = $1
                ORDER BY timestamp DESC
                """,
                conversation.id
            )

            conversation_with_memory.property_interactions = [
                self._row_to_property_interaction(row) for row in interaction_rows
            ]

        # Update memory context summary
        await self._update_memory_context_summary(conversation_with_memory)

        return conversation_with_memory

    async def update_behavioral_preferences(
        self,
        conversation_id: UUID,
        interaction_data: Dict[str, Any],
        learning_source: str,
        claude_reasoning: Optional[str] = None
    ):
        """
        Update behavioral preferences based on interaction patterns:
        - Communication style (formal, casual, direct)
        - Decision-making patterns (analytical, emotional, quick)
        - Information processing preference (detailed, summary)
        - Response timing patterns
        """

        try:
            await self.ensure_initialized()

            if not self.use_database:
                logger.warning("Database not available for behavioral preference updates")
                return

            # Extract behavioral signals from interaction
            behavioral_signals = await self._extract_behavioral_signals(
                interaction_data, claude_reasoning
            )

            for signal_type, signal_data in behavioral_signals.items():
                await self._upsert_behavioral_preference(
                    conversation_id,
                    signal_type,
                    signal_data,
                    learning_source
                )

            # Invalidate cache for this conversation
            await self._invalidate_conversation_cache(conversation_id)

            logger.info(f"Updated behavioral preferences for conversation {conversation_id}")

        except Exception as e:
            logger.error(f"Error updating behavioral preferences: {e}")

    async def add_property_interaction(
        self,
        conversation_id: UUID,
        property_id: Optional[str],
        property_data: Dict[str, Any],
        interaction_type: str,
        feedback_category: Optional[str] = None,
        feedback_text: Optional[str] = None,
        time_on_property: float = 0.0,
        claude_analysis: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """Add property interaction to memory system."""

        try:
            await self.ensure_initialized()

            interaction_id = uuid4()
            interaction = PropertyInteraction(
                id=interaction_id,
                conversation_id=conversation_id,
                property_id=property_id,
                property_data=property_data,
                interaction_type=InteractionType(interaction_type),
                feedback_category=feedback_category,
                feedback_text=feedback_text,
                time_on_property=time_on_property,
                claude_analysis=claude_analysis or {}
            )

            if self.use_database:
                await self.db_pool.execute(
                    """
                    INSERT INTO property_interactions
                    (id, conversation_id, property_id, property_data, interaction_type,
                     feedback_category, feedback_text, time_on_property, claude_analysis,
                     behavioral_signals, timestamp, created_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                    interaction.id, interaction.conversation_id, interaction.property_id,
                    json.dumps(interaction.property_data), interaction.interaction_type.value,
                    interaction.feedback_category, interaction.feedback_text,
                    interaction.time_on_property, json.dumps(interaction.claude_analysis),
                    json.dumps(interaction.behavioral_signals), interaction.timestamp,
                    interaction.created_at
                )

            # Invalidate cache
            await self._invalidate_conversation_cache(conversation_id)

            logger.info(f"Added property interaction {interaction_id} for conversation {conversation_id}")
            return interaction_id

        except Exception as e:
            logger.error(f"Error adding property interaction: {e}")
            return uuid4()  # Return dummy ID on error

    async def save_enhanced_context(
        self,
        tenant_id: str,
        contact_id: str,
        conversation_with_memory: ConversationWithMemory
    ):
        """Save enhanced conversation context to database."""

        try:
            await self.ensure_initialized()

            if not self.use_database:
                # Fallback to legacy system
                legacy_context = convert_conversation_to_legacy_context(conversation_with_memory)
                await super().save_context(contact_id, legacy_context, tenant_id)
                return

            # Get tenant UUID
            tenant_uuid = await self._get_or_create_tenant_uuid(tenant_id)
            conversation = conversation_with_memory.conversation
            conversation.tenant_id = tenant_uuid

            # Save conversation
            await self.db_pool.execute(
                """
                INSERT INTO conversations
                (id, tenant_id, contact_id, conversation_stage, lead_score, last_interaction_at,
                 extracted_preferences, lead_intelligence, previous_sessions_summary,
                 behavioral_profile, session_count, total_messages, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (tenant_id, contact_id)
                DO UPDATE SET
                    conversation_stage = EXCLUDED.conversation_stage,
                    lead_score = EXCLUDED.lead_score,
                    last_interaction_at = EXCLUDED.last_interaction_at,
                    extracted_preferences = EXCLUDED.extracted_preferences,
                    lead_intelligence = EXCLUDED.lead_intelligence,
                    previous_sessions_summary = EXCLUDED.previous_sessions_summary,
                    behavioral_profile = EXCLUDED.behavioral_profile,
                    session_count = EXCLUDED.session_count,
                    total_messages = EXCLUDED.total_messages,
                    updated_at = EXCLUDED.updated_at
                """,
                conversation.id, conversation.tenant_id, conversation.contact_id,
                conversation.conversation_stage.value, conversation.lead_score,
                conversation.last_interaction_at, json.dumps(conversation.extracted_preferences),
                json.dumps(conversation.lead_intelligence), conversation.previous_sessions_summary,
                json.dumps(conversation.behavioral_profile), conversation.session_count,
                conversation.total_messages, conversation.created_at, conversation.updated_at
            )

            # Invalidate cache
            cache_key = f"conv_memory:{tenant_id}:{contact_id}"
            await self.redis_client.delete(cache_key)

            logger.info(f"Saved enhanced context for {tenant_id}:{contact_id}")

        except Exception as e:
            logger.error(f"Error saving enhanced context: {e}")

    # Legacy compatibility methods

    async def get_context(
        self, contact_id: str, location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Legacy-compatible get_context method.
        Provides backward compatibility with existing MemoryService API.
        """

        if location_id is None:
            # Use existing parent method for backward compatibility
            return await super().get_context(contact_id, location_id)

        try:
            # Get enhanced memory and convert to legacy format
            conversation_with_memory = await self.get_conversation_with_memory(
                location_id, contact_id
            )

            if conversation_with_memory:
                return convert_conversation_to_legacy_context(conversation_with_memory)
            else:
                return await super().get_context(contact_id, location_id)

        except Exception as e:
            logger.error(f"Error in legacy get_context: {e}")
            # Fallback to parent implementation
            return await super().get_context(contact_id, location_id)

    async def save_context(
        self,
        contact_id: str,
        context: Dict[str, Any],
        location_id: Optional[str] = None,
    ) -> None:
        """
        Legacy-compatible save_context method.
        Provides backward compatibility while also saving to enhanced system.
        """

        # Always save to legacy system for backward compatibility
        await super().save_context(contact_id, context, location_id)

        if location_id and self.use_database:
            try:
                # Also save to enhanced system
                tenant_uuid = await self._get_or_create_tenant_uuid(location_id)
                conversation_with_memory = convert_legacy_context_to_conversation(
                    context, tenant_uuid, contact_id
                )
                await self.save_enhanced_context(location_id, contact_id, conversation_with_memory)

            except Exception as e:
                logger.error(f"Error saving to enhanced system: {e}")

    # Helper methods

    async def _get_legacy_context_enhanced(
        self, tenant_id: str, contact_id: str
    ) -> ConversationWithMemory:
        """Get legacy context and convert to enhanced format."""

        legacy_context = await super().get_context(contact_id, tenant_id)
        tenant_uuid = uuid4()  # Temporary UUID for file-based system

        return convert_legacy_context_to_conversation(
            legacy_context, tenant_uuid, contact_id
        )

    async def _get_or_create_tenant_uuid(self, location_id: str) -> UUID:
        """Get or create tenant UUID from location_id."""

        if not self.use_database:
            return uuid4()  # Return random UUID for non-database mode

        # Check if tenant exists
        tenant_row = await self.db_pool.fetchrow(
            "SELECT id FROM tenants WHERE location_id = $1",
            location_id
        )

        if tenant_row:
            return tenant_row['id']

        # Create new tenant
        tenant_id = uuid4()
        await self.db_pool.execute(
            """
            INSERT INTO tenants (id, location_id, name, status, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (location_id) DO NOTHING
            """,
            tenant_id, location_id, f"Tenant {location_id}", "active",
            datetime.utcnow(), datetime.utcnow()
        )

        return tenant_id

    async def _create_new_conversation(self, tenant_id: UUID, contact_id: str) -> Conversation:
        """Create new conversation in database."""

        conversation = Conversation(
            id=uuid4(),
            tenant_id=tenant_id,
            contact_id=contact_id
        )

        if self.use_database:
            await self.db_pool.execute(
                """
                INSERT INTO conversations
                (id, tenant_id, contact_id, conversation_stage, lead_score, last_interaction_at,
                 extracted_preferences, lead_intelligence, previous_sessions_summary,
                 behavioral_profile, session_count, total_messages, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                """,
                conversation.id, conversation.tenant_id, conversation.contact_id,
                conversation.conversation_stage.value, conversation.lead_score,
                conversation.last_interaction_at, json.dumps(conversation.extracted_preferences),
                json.dumps(conversation.lead_intelligence), conversation.previous_sessions_summary,
                json.dumps(conversation.behavioral_profile), conversation.session_count,
                conversation.total_messages, conversation.created_at, conversation.updated_at
            )

        return conversation

    def _row_to_conversation(self, row) -> Conversation:
        """Convert database row to Conversation object."""
        return Conversation(
            id=row['id'],
            tenant_id=row['tenant_id'],
            contact_id=row['contact_id'],
            conversation_stage=ConversationStage(row['conversation_stage']),
            lead_score=row['lead_score'],
            last_interaction_at=row['last_interaction_at'],
            extracted_preferences=json.loads(row['extracted_preferences']) if row['extracted_preferences'] else {},
            lead_intelligence=json.loads(row['lead_intelligence']) if row['lead_intelligence'] else {},
            previous_sessions_summary=row['previous_sessions_summary'],
            behavioral_profile=json.loads(row['behavioral_profile']) if row['behavioral_profile'] else {},
            session_count=row['session_count'],
            total_messages=row['total_messages'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_message(self, row) -> ConversationMessage:
        """Convert database row to ConversationMessage object."""
        return ConversationMessage(
            id=row['id'],
            conversation_id=row['conversation_id'],
            role=MessageRole(row['role']),
            content=row['content'],
            timestamp=row['timestamp'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            claude_reasoning=row['claude_reasoning'],
            response_time_ms=row['response_time_ms'],
            token_count=row['token_count'],
            message_order=row['message_order']
        )

    def _row_to_behavioral_preference(self, row) -> BehavioralPreference:
        """Convert database row to BehavioralPreference object."""
        return BehavioralPreference(
            id=row['id'],
            conversation_id=row['conversation_id'],
            preference_type=PreferenceType(row['preference_type']),
            preference_value=json.loads(row['preference_value']),
            confidence_score=row['confidence_score'],
            learned_from=row['learned_from'],
            source_interaction_id=row['source_interaction_id'],
            timestamp=row['timestamp'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def _row_to_property_interaction(self, row) -> PropertyInteraction:
        """Convert database row to PropertyInteraction object."""
        return PropertyInteraction(
            id=row['id'],
            conversation_id=row['conversation_id'],
            property_id=row['property_id'],
            property_data=json.loads(row['property_data']),
            interaction_type=InteractionType(row['interaction_type']),
            feedback_category=row['feedback_category'],
            feedback_text=row['feedback_text'],
            time_on_property=row['time_on_property'],
            claude_analysis=json.loads(row['claude_analysis']) if row['claude_analysis'] else {},
            behavioral_signals=json.loads(row['behavioral_signals']) if row['behavioral_signals'] else {},
            timestamp=row['timestamp'],
            created_at=row['created_at']
        )

    def _calculate_cache_ttl(self, last_interaction: datetime) -> int:
        """Calculate cache TTL based on conversation activity."""
        hours_since = (datetime.utcnow() - last_interaction).total_seconds() / 3600

        if hours_since < 1:
            return 1800  # 30 minutes for very active
        elif hours_since < 24:
            return 3600  # 1 hour for recent
        else:
            return 7200  # 2 hours for older

    async def _extract_behavioral_signals(
        self, interaction_data: Dict[str, Any], claude_reasoning: Optional[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Extract behavioral signals from interaction data."""

        signals = {}

        # Analyze response timing
        if "response_time_ms" in interaction_data:
            response_time = interaction_data["response_time_ms"]
            if response_time < 1000:
                timing_style = "immediate"
            elif response_time < 5000:
                timing_style = "measured"
            else:
                timing_style = "delayed"

            signals[PreferenceType.RESPONSE_TIMING.value] = {
                "timing_style": timing_style,
                "response_time_ms": response_time
            }

        # Analyze message length and detail preference
        if "message_content" in interaction_data:
            content = interaction_data["message_content"]
            if len(content) > 100:
                detail_pref = "detailed"
            elif len(content) > 30:
                detail_pref = "summary"
            else:
                detail_pref = "concise"

            signals[PreferenceType.INFO_PROCESSING.value] = {
                "detail_preference": detail_pref,
                "message_length": len(content)
            }

        # TODO: Add more sophisticated behavioral signal extraction using Claude analysis

        return signals

    async def _upsert_behavioral_preference(
        self,
        conversation_id: UUID,
        preference_type: str,
        preference_value: Dict[str, Any],
        learning_source: str
    ):
        """Insert or update behavioral preference."""

        if not self.use_database:
            return

        preference_id = uuid4()
        confidence_score = 0.7  # Default confidence, could be calculated

        await self.db_pool.execute(
            """
            INSERT INTO behavioral_preferences
            (id, conversation_id, preference_type, preference_value, confidence_score,
             learned_from, timestamp, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (conversation_id, preference_type, timestamp)
            DO UPDATE SET
                preference_value = EXCLUDED.preference_value,
                confidence_score = (behavioral_preferences.confidence_score + EXCLUDED.confidence_score) / 2,
                updated_at = EXCLUDED.updated_at
            """,
            preference_id, conversation_id, preference_type,
            json.dumps(preference_value), confidence_score, learning_source,
            datetime.utcnow(), datetime.utcnow(), datetime.utcnow()
        )

    async def _update_memory_context_summary(self, conversation_with_memory: ConversationWithMemory):
        """Update memory context summary for intelligent conversation resume."""

        conversation = conversation_with_memory.conversation

        # Calculate session gap
        hours_since = (datetime.utcnow() - conversation.last_interaction_at).total_seconds() / 3600
        conversation_with_memory.hours_since_last_interaction = hours_since

        # Determine if returning lead (> 4 hours gap)
        conversation_with_memory.is_returning_lead = hours_since > 4

        if conversation_with_memory.is_returning_lead:
            # Generate intelligent summary for conversation resume
            recent_messages = conversation_with_memory.get_recent_messages(limit=5)
            behavioral_insights = conversation_with_memory.get_behavioral_insights()
            property_patterns = conversation_with_memory.get_property_interaction_patterns()

            summary_parts = []

            if recent_messages:
                last_topic = recent_messages[0].content[:100] + "..." if len(recent_messages[0].content) > 100 else recent_messages[0].content
                summary_parts.append(f"Last discussed: {last_topic}")

            if behavioral_insights:
                summary_parts.append(f"Communication style: {list(behavioral_insights.keys())}")

            if property_patterns:
                engagement = property_patterns.get("engagement_level", "unknown")
                summary_parts.append(f"Property engagement: {engagement}")

            conversation_with_memory.memory_context_summary = " | ".join(summary_parts)

    async def _invalidate_conversation_cache(self, conversation_id: UUID):
        """Invalidate Redis cache for conversation."""

        if not self.use_redis:
            return

        try:
            # Get conversation to find tenant and contact
            conversation_row = await self.db_pool.fetchrow(
                "SELECT tenant_id, contact_id FROM conversations WHERE id = $1",
                conversation_id
            )

            if conversation_row:
                tenant_row = await self.db_pool.fetchrow(
                    "SELECT location_id FROM tenants WHERE id = $1",
                    conversation_row['tenant_id']
                )

                if tenant_row:
                    cache_key = f"conv_memory:{tenant_row['location_id']}:{conversation_row['contact_id']}"
                    await self.redis_client.delete(cache_key)

        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")

    def _update_metrics(self, response_time_ms: float):
        """Update performance metrics."""

        # Simple moving average for response time
        current_avg = self.metrics["avg_response_time_ms"]
        self.metrics["avg_response_time_ms"] = (current_avg + response_time_ms) / 2

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring."""

        total_requests = self.metrics["cache_hits"] + self.metrics["cache_misses"]
        cache_hit_rate = self.metrics["cache_hits"] / total_requests if total_requests > 0 else 0

        return {
            "cache_hit_rate": cache_hit_rate,
            "cache_hits": self.metrics["cache_hits"],
            "cache_misses": self.metrics["cache_misses"],
            "db_queries": self.metrics["db_queries"],
            "avg_response_time_ms": self.metrics["avg_response_time_ms"],
            "database_enabled": self.use_database,
            "redis_enabled": self.use_redis
        }