"""
CQRS (Command Query Responsibility Segregation) Service
Separates read and write operations for optimal performance and scalability
"""

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.services.event_streaming_service import (
    EventType,
    Priority,
    get_event_streaming_service,
)

logger = logging.getLogger(__name__)


@dataclass
class Command:
    """Base command for write operations"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Query:
    """Base query for read operations"""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    cache_ttl: int = 300  # 5 minutes default cache TTL


@dataclass
class CommandResult:
    """Result of command execution"""

    success: bool
    command_id: str
    data: Dict[str, Any]
    events: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class QueryResult:
    """Result of query execution"""

    success: bool
    query_id: str
    data: Dict[str, Any]
    source: str = "database"  # database, cache, computed
    latency_ms: float = 0
    error: Optional[str] = None


# Lead Intelligence Commands
@dataclass
class CreateLeadCommand(Command):
    lead_data: Dict[str, Any]
    source: str = "ghl_webhook"


@dataclass
class UpdateLeadCommand(Command):
    lead_id: str
    updates: Dict[str, Any]


@dataclass
class ScoreLeadCommand(Command):
    lead_id: str
    scoring_context: Dict[str, Any]
    force_refresh: bool = False


@dataclass
class MatchPropertiesCommand(Command):
    lead_id: str
    preferences: Dict[str, Any]
    max_matches: int = 10


# Lead Intelligence Queries
@dataclass
class GetLeadQuery(Query):
    lead_id: str
    include_history: bool = False


@dataclass
class GetLeadScoreQuery(Query):
    lead_id: str
    include_reasoning: bool = False


@dataclass
class GetPropertyMatchesQuery(Query):
    lead_id: str
    limit: int = 10
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GetLeadAnalyticsQuery(Query):
    date_range: Dict[str, str]
    filters: Dict[str, Any] = field(default_factory=dict)


class CommandHandler(ABC):
    """Abstract base class for command handlers"""

    @abstractmethod
    async def handle(self, command: Command) -> CommandResult:
        pass


class QueryHandler(ABC):
    """Abstract base class for query handlers"""

    @abstractmethod
    async def handle(self, query: Query) -> QueryResult:
        pass


class LeadCommandHandler(CommandHandler):
    """Handles lead-related write operations"""

    def __init__(self):
        from ghl_real_estate_ai.services.cache_service import get_cache_service
        from ghl_real_estate_ai.services.enhanced_lead_intelligence import get_enhanced_lead_intelligence

        self.lead_service = get_enhanced_lead_intelligence()
        self.cache = get_cache_service()

    async def handle(self, command: Command) -> CommandResult:
        """Route command to appropriate handler"""
        datetime.utcnow()

        try:
            if isinstance(command, CreateLeadCommand):
                result = await self._handle_create_lead(command)
            elif isinstance(command, UpdateLeadCommand):
                result = await self._handle_update_lead(command)
            elif isinstance(command, ScoreLeadCommand):
                result = await self._handle_score_lead(command)
            elif isinstance(command, MatchPropertiesCommand):
                result = await self._handle_match_properties(command)
            else:
                raise ValueError(f"Unknown command type: {type(command)}")

            # Publish events for successful operations
            event_service = await get_event_streaming_service()
            for event_data in result.events:
                await event_service.publish_event(
                    event_type=EventType(event_data["type"]),
                    data=event_data["data"],
                    priority=Priority(event_data.get("priority", Priority.MEDIUM.value)),
                    correlation_id=command.correlation_id,
                )

            return result

        except Exception as e:
            logger.error(f"Command handling failed: {e}")
            return CommandResult(success=False, command_id=command.id, data={}, error=str(e))

    async def _handle_create_lead(self, command: CreateLeadCommand) -> CommandResult:
        """Handle lead creation with automatic scoring"""
        lead_data = command.lead_data
        lead_id = lead_data.get("id", str(uuid.uuid4()))

        # Store lead data (simulate database write)
        await self.cache.set(f"lead:{lead_id}", lead_data, ttl=3600)

        # Generate events for downstream processing
        events = [
            {
                "type": EventType.LEAD_CREATED.value,
                "data": {"lead_id": lead_id, "lead_data": lead_data},
                "priority": Priority.HIGH.value,
            },
            {
                "type": EventType.LEAD_SCORED.value,
                "data": {"lead_id": lead_id, "trigger": "creation"},
                "priority": Priority.HIGH.value,
            },
        ]

        return CommandResult(
            success=True,
            command_id=command.id,
            data={"lead_id": lead_id, "created_at": datetime.utcnow().isoformat()},
            events=events,
        )

    async def _handle_update_lead(self, command: UpdateLeadCommand) -> CommandResult:
        """Handle lead updates with change tracking"""
        lead_id = command.lead_id
        updates = command.updates

        # Get existing lead data
        existing_data = await self.cache.get(f"lead:{lead_id}")
        if not existing_data:
            raise ValueError(f"Lead {lead_id} not found")

        # Apply updates
        updated_data = {**existing_data, **updates, "updated_at": datetime.utcnow().isoformat()}
        await self.cache.set(f"lead:{lead_id}", updated_data, ttl=3600)

        # Invalidate related caches
        await self.cache.delete(f"lead_score:{lead_id}")
        await self.cache.delete(f"property_matches:{lead_id}")

        events = [
            {
                "type": EventType.LEAD_UPDATED.value,
                "data": {"lead_id": lead_id, "updates": updates, "changed_fields": list(updates.keys())},
                "priority": Priority.MEDIUM.value,
            }
        ]

        return CommandResult(
            success=True,
            command_id=command.id,
            data={"lead_id": lead_id, "updated_fields": list(updates.keys())},
            events=events,
        )

    async def _handle_score_lead(self, command: ScoreLeadCommand) -> CommandResult:
        """Handle lead scoring with caching"""
        lead_id = command.lead_id

        # Use enhanced lead intelligence for scoring
        analysis_result = await self.lead_service.get_comprehensive_lead_analysis(
            lead_name=f"Lead_{lead_id}", lead_context=command.scoring_context, force_refresh=command.force_refresh
        )

        # Cache the score
        score_data = {
            "score": analysis_result.final_score,
            "classification": analysis_result.classification,
            "confidence": analysis_result.confidence_score,
            "scored_at": datetime.utcnow().isoformat(),
        }
        await self.cache.set(f"lead_score:{lead_id}", score_data, ttl=1800)

        events = [
            {
                "type": EventType.LEAD_SCORED.value,
                "data": {
                    "lead_id": lead_id,
                    "score": analysis_result.final_score,
                    "classification": analysis_result.classification,
                },
                "priority": Priority.HIGH.value if analysis_result.classification == "hot" else Priority.MEDIUM.value,
            }
        ]

        return CommandResult(success=True, command_id=command.id, data=score_data, events=events)

    async def _handle_match_properties(self, command: MatchPropertiesCommand) -> CommandResult:
        """Handle property matching with intelligent caching"""
        lead_id = command.lead_id
        preferences = command.preferences

        # Simulate property matching logic
        matches = []
        for i in range(min(command.max_matches, 5)):
            matches.append(
                {
                    "property_id": f"prop_{i + 1}",
                    "match_score": 95 - (i * 5),
                    "address": f"123{i} Example St, Rancho Cucamonga, CA",
                    "price": 450000 + (i * 25000),
                }
            )

        # Cache matches
        match_data = {"matches": matches, "generated_at": datetime.utcnow().isoformat(), "preferences": preferences}
        await self.cache.set(f"property_matches:{lead_id}", match_data, ttl=900)

        events = [
            {
                "type": EventType.PROPERTY_MATCHED.value,
                "data": {
                    "lead_id": lead_id,
                    "match_count": len(matches),
                    "top_match_score": matches[0]["match_score"] if matches else 0,
                },
                "priority": Priority.MEDIUM.value,
            }
        ]

        return CommandResult(
            success=True, command_id=command.id, data={"lead_id": lead_id, "matches_count": len(matches)}, events=events
        )


class LeadQueryHandler(QueryHandler):
    """Handles lead-related read operations with caching optimization"""

    def __init__(self):
        from ghl_real_estate_ai.services.cache_service import get_cache_service

        self.cache = get_cache_service()

    async def handle(self, query: Query) -> QueryResult:
        """Route query to appropriate handler with performance tracking"""
        start_time = datetime.utcnow()

        try:
            if isinstance(query, GetLeadQuery):
                result = await self._handle_get_lead(query)
            elif isinstance(query, GetLeadScoreQuery):
                result = await self._handle_get_lead_score(query)
            elif isinstance(query, GetPropertyMatchesQuery):
                result = await self._handle_get_property_matches(query)
            elif isinstance(query, GetLeadAnalyticsQuery):
                result = await self._handle_get_analytics(query)
            else:
                raise ValueError(f"Unknown query type: {type(query)}")

            # Calculate latency
            end_time = datetime.utcnow()
            result.latency_ms = (end_time - start_time).total_seconds() * 1000

            return result

        except Exception as e:
            logger.error(f"Query handling failed: {e}")
            end_time = datetime.utcnow()
            return QueryResult(
                success=False,
                query_id=query.id,
                data={},
                latency_ms=(end_time - start_time).total_seconds() * 1000,
                error=str(e),
            )

    async def _handle_get_lead(self, query: GetLeadQuery) -> QueryResult:
        """Get lead data with optional history"""
        lead_id = query.lead_id
        cache_key = f"lead:{lead_id}"

        # Try cache first
        lead_data = await self.cache.get(cache_key)
        source = "cache" if lead_data else "database"

        if not lead_data:
            # Simulate database read
            lead_data = {
                "id": lead_id,
                "name": f"Lead {lead_id}",
                "email": f"lead{lead_id}@example.com",
                "created_at": datetime.utcnow().isoformat(),
            }
            await self.cache.set(cache_key, lead_data, ttl=query.cache_ttl)

        if query.include_history:
            # Add interaction history
            lead_data["history"] = [
                {"type": "email_sent", "timestamp": datetime.utcnow().isoformat()},
                {"type": "property_viewed", "timestamp": datetime.utcnow().isoformat()},
            ]

        return QueryResult(success=True, query_id=query.id, data=lead_data, source=source)

    async def _handle_get_lead_score(self, query: GetLeadScoreQuery) -> QueryResult:
        """Get lead score with optional reasoning"""
        lead_id = query.lead_id
        cache_key = f"lead_score:{lead_id}"

        score_data = await self.cache.get(cache_key)
        source = "cache" if score_data else "computed"

        if not score_data:
            # Compute score if not cached
            score_data = {
                "score": 75.0,
                "classification": "warm",
                "confidence": 0.85,
                "scored_at": datetime.utcnow().isoformat(),
            }
            await self.cache.set(cache_key, score_data, ttl=1800)

        if query.include_reasoning:
            score_data["reasoning"] = "High engagement score with recent property views"

        return QueryResult(success=True, query_id=query.id, data=score_data, source=source)

    async def _handle_get_property_matches(self, query: GetPropertyMatchesQuery) -> QueryResult:
        """Get property matches with filtering"""
        lead_id = query.lead_id
        cache_key = f"property_matches:{lead_id}:{hash(str(query.filters))}"

        matches_data = await self.cache.get(cache_key)
        source = "cache" if matches_data else "computed"

        if not matches_data:
            # Compute matches with filters
            all_matches = [
                {"property_id": f"prop_{i}", "match_score": 90 - i, "price": 400000 + (i * 20000)} for i in range(20)
            ]

            # Apply filters
            filtered_matches = all_matches
            if "max_price" in query.filters:
                filtered_matches = [m for m in filtered_matches if m["price"] <= query.filters["max_price"]]

            matches_data = {
                "matches": filtered_matches[: query.limit],
                "total_matches": len(filtered_matches),
                "generated_at": datetime.utcnow().isoformat(),
            }
            await self.cache.set(cache_key, matches_data, ttl=900)

        return QueryResult(success=True, query_id=query.id, data=matches_data, source=source)

    async def _handle_get_analytics(self, query: GetLeadAnalyticsQuery) -> QueryResult:
        """Get analytics data with aggregation"""
        cache_key = f"analytics:{hash(str(query.date_range))}:{hash(str(query.filters))}"

        analytics_data = await self.cache.get(cache_key)
        source = "cache" if analytics_data else "computed"

        if not analytics_data:
            # Compute analytics
            analytics_data = {
                "total_leads": 1250,
                "hot_leads": 125,
                "warm_leads": 500,
                "cold_leads": 625,
                "conversion_rate": 0.12,
                "avg_score": 68.5,
                "generated_at": datetime.utcnow().isoformat(),
            }
            await self.cache.set(cache_key, analytics_data, ttl=600)

        return QueryResult(success=True, query_id=query.id, data=analytics_data, source=source)


class CQRSService:
    """
    Main CQRS service that routes commands and queries to appropriate handlers
    """

    def __init__(self):
        self.command_handler = LeadCommandHandler()
        self.query_handler = LeadQueryHandler()
        self.metrics = {
            "commands_processed": 0,
            "queries_processed": 0,
            "errors": 0,
            "avg_command_time_ms": 0,
            "avg_query_time_ms": 0,
        }

    async def execute_command(self, command: Command) -> CommandResult:
        """Execute write command"""
        start_time = datetime.utcnow()

        try:
            result = await self.command_handler.handle(command)

            # Update metrics
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000
            self._update_command_metrics(execution_time, result.success)

            return result

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            self.metrics["errors"] += 1
            return CommandResult(success=False, command_id=command.id, data={}, error=str(e))

    async def execute_query(self, query: Query) -> QueryResult:
        """Execute read query"""
        start_time = datetime.utcnow()

        try:
            result = await self.query_handler.handle(query)

            # Update metrics
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds() * 1000
            self._update_query_metrics(execution_time, result.success)

            return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            self.metrics["errors"] += 1
            return QueryResult(success=False, query_id=query.id, data={}, error=str(e))

    def _update_command_metrics(self, execution_time_ms: float, success: bool):
        """Update command execution metrics"""
        if success:
            count = self.metrics["commands_processed"]
            current_avg = self.metrics["avg_command_time_ms"]
            self.metrics["commands_processed"] += 1
            self.metrics["avg_command_time_ms"] = (current_avg * count + execution_time_ms) / (count + 1)

    def _update_query_metrics(self, execution_time_ms: float, success: bool):
        """Update query execution metrics"""
        if success:
            count = self.metrics["queries_processed"]
            current_avg = self.metrics["avg_query_time_ms"]
            self.metrics["queries_processed"] += 1
            self.metrics["avg_query_time_ms"] = (current_avg * count + execution_time_ms) / (count + 1)

    def get_metrics(self) -> Dict[str, Any]:
        """Get CQRS service metrics"""
        total_operations = self.metrics["commands_processed"] + self.metrics["queries_processed"]
        error_rate = self.metrics["errors"] / max(total_operations, 1)

        return {**self.metrics, "total_operations": total_operations, "error_rate": error_rate}


# Singleton instance
_cqrs_service = None


def get_cqrs_service() -> CQRSService:
    """Get singleton CQRS service instance"""
    global _cqrs_service
    if _cqrs_service is None:
        _cqrs_service = CQRSService()
    return _cqrs_service
