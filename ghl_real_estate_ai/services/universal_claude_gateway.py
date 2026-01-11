"""
Universal Claude Gateway Service - Unified Claude Access with Agent Context

Provides centralized routing and coordination for all Claude services throughout
the EnterpriseHub platform with agent profile awareness and intelligent service
selection.

Key Features:
- Intelligent service routing based on query type and agent context
- Agent profile integration across all Claude interactions
- Cross-service conversation continuity
- Performance optimization with intelligent caching
- Cost optimization through model selection
- Unified API interface for all components
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Type
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib

from anthropic import AsyncAnthropic

from ..ghl_utils.config import settings
from .enhanced_claude_agent_service import (
    EnhancedClaudeAgentService, EnhancedCoachingResponse
)
from .agent_profile_service import AgentProfileService
from ..models.agent_profile_models import (
    AgentProfile, AgentSession, AgentRole, GuidanceType
)

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of queries for intelligent routing."""
    GENERAL_COACHING = "general_coaching"
    OBJECTION_HANDLING = "objection_handling"
    LEAD_QUALIFICATION = "lead_qualification"
    PROPERTY_RECOMMENDATION = "property_recommendation"
    MARKET_ANALYSIS = "market_analysis"
    SEMANTIC_ANALYSIS = "semantic_analysis"
    VISION_ANALYSIS = "vision_analysis"
    ACTION_PLANNING = "action_planning"
    CONVERSATION_ANALYSIS = "conversation_analysis"
    BUSINESS_INTELLIGENCE = "business_intelligence"
    ADVANCED_COACHING = "advanced_coaching"
    REAL_TIME_ASSISTANCE = "real_time_assistance"


class ServicePriority(Enum):
    """Service priority levels for intelligent routing."""
    CRITICAL = "critical"  # Sub-100ms response required
    HIGH = "high"         # Sub-500ms response required
    NORMAL = "normal"     # Sub-1s response acceptable
    BACKGROUND = "background"  # >1s response acceptable


@dataclass
class UniversalQueryRequest:
    """Universal request structure for all Claude interactions."""
    # Core identification
    agent_id: str
    session_id: Optional[str] = None
    location_id: Optional[str] = None

    # Query content
    query: str
    query_type: QueryType
    context: Optional[Dict[str, Any]] = None

    # Priority and preferences
    priority: ServicePriority = ServicePriority.NORMAL
    preferred_guidance_types: Optional[List[GuidanceType]] = None

    # Performance targets
    max_response_time_ms: Optional[int] = None
    enable_caching: bool = True
    enable_streaming: bool = False

    # Additional context
    conversation_stage: Optional[str] = None
    prospect_data: Optional[Dict[str, Any]] = None
    property_data: Optional[Dict[str, Any]] = None
    market_data: Optional[Dict[str, Any]] = None

    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class UniversalClaudeResponse:
    """Universal response structure from Claude services."""
    # Core response
    response: str
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0

    # Agent context
    agent_role: Optional[str] = None
    guidance_types_applied: List[str] = field(default_factory=list)
    role_specific_insights: List[str] = field(default_factory=list)

    # Performance metrics
    processing_time_ms: float = 0.0
    service_used: str = "unknown"
    cached_response: bool = False

    # Additional context
    next_questions: List[str] = field(default_factory=list)
    urgency_level: str = "normal"
    conversation_stage: Optional[str] = None

    # Session continuity
    session_id: Optional[str] = None
    context_preserved: bool = False

    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ServiceRoutingRule:
    """Rules for intelligent service routing."""
    query_patterns: List[str]
    service_name: str
    agent_roles: Optional[List[AgentRole]] = None
    priority_threshold: Optional[ServicePriority] = None
    performance_target_ms: Optional[int] = None
    fallback_services: List[str] = field(default_factory=list)


class UniversalClaudeGateway:
    """
    Universal Claude Gateway - Central coordination hub for all Claude services.

    Provides intelligent routing, agent context integration, and performance
    optimization for all Claude interactions throughout EnterpriseHub.
    """

    def __init__(self):
        # Core services
        self.enhanced_claude = EnhancedClaudeAgentService()
        self.agent_profile_service = AgentProfileService()

        # Service registry for dynamic loading
        self.claude_services: Dict[str, Any] = {}
        self.service_health: Dict[str, Dict[str, Any]] = {}

        # Performance optimization
        self.response_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl_seconds = 300  # 5 minutes default

        # Routing intelligence
        self.routing_rules = self._initialize_routing_rules()
        self.performance_history: Dict[str, List[float]] = {}

        # Cost optimization
        self.model_selection_cache: Dict[str, str] = {}
        self.usage_tracking: Dict[str, int] = {}

        logger.info("Universal Claude Gateway initialized")

    def _initialize_routing_rules(self) -> List[ServiceRoutingRule]:
        """Initialize intelligent service routing rules."""
        return [
            # General coaching - use enhanced service with agent context
            ServiceRoutingRule(
                query_patterns=["coaching", "guidance", "help", "advice"],
                service_name="enhanced_claude_agent_service",
                performance_target_ms=500,
                fallback_services=["claude_agent_service"]
            ),

            # Objection handling - specialized service
            ServiceRoutingRule(
                query_patterns=["objection", "concern", "hesitation", "doubt"],
                service_name="enhanced_claude_agent_service",
                priority_threshold=ServicePriority.HIGH,
                performance_target_ms=300,
                fallback_services=["claude_agent_service"]
            ),

            # Lead qualification - orchestrator service
            ServiceRoutingRule(
                query_patterns=["qualify", "qualification", "questions", "discovery"],
                service_name="enhanced_qualification_orchestrator",
                performance_target_ms=400,
                fallback_services=["enhanced_claude_agent_service"]
            ),

            # Property recommendations - specialized service
            ServiceRoutingRule(
                query_patterns=["property", "house", "home", "recommendation"],
                service_name="claude_intelligent_property_recommendation",
                performance_target_ms=600,
                fallback_services=["enhanced_claude_agent_service"]
            ),

            # Market analysis - specialized service
            ServiceRoutingRule(
                query_patterns=["market", "price", "trends", "analysis"],
                service_name="claude_realtime_market_analysis",
                performance_target_ms=800,
                fallback_services=["enhanced_claude_agent_service"]
            ),

            # Semantic analysis - specialized service
            ServiceRoutingRule(
                query_patterns=["analyze", "sentiment", "intent", "meaning"],
                service_name="claude_semantic_analyzer",
                performance_target_ms=200,
                fallback_services=["enhanced_claude_agent_service"]
            ),

            # Vision analysis - specialized service
            ServiceRoutingRule(
                query_patterns=["image", "photo", "visual", "document"],
                service_name="claude_vision_analyzer",
                performance_target_ms=1000,
                fallback_services=["enhanced_claude_agent_service"]
            ),

            # Advanced coaching analytics
            ServiceRoutingRule(
                query_patterns=["analytics", "performance", "coaching analytics"],
                service_name="claude_advanced_coaching_optimization",
                agent_roles=[AgentRole.TRANSACTION_COORDINATOR],
                performance_target_ms=600,
                fallback_services=["enhanced_claude_agent_service"]
            ),

            # Real-time assistance
            ServiceRoutingRule(
                query_patterns=["urgent", "immediate", "real-time", "live"],
                service_name="claude_streaming_service",
                priority_threshold=ServicePriority.CRITICAL,
                performance_target_ms=100,
                fallback_services=["enhanced_claude_agent_service"]
            )
        ]

    async def process_universal_query(
        self,
        request: UniversalQueryRequest
    ) -> UniversalClaudeResponse:
        """
        Process a universal Claude query with intelligent routing and agent context.

        Args:
            request: Universal query request with all context

        Returns:
            Universal Claude response with agent context and performance metrics
        """
        start_time = datetime.now()

        try:
            # 1. Load agent profile and session context
            agent_profile, session_context = await self._load_agent_context(
                request.agent_id, request.session_id, request.location_id
            )

            # 2. Intelligent service routing
            service_name, fallback_chain = await self._route_to_service(
                request, agent_profile
            )

            # 3. Check cache if enabled
            if request.enable_caching:
                cached_response = await self._check_cache(request)
                if cached_response:
                    cached_response.processing_time_ms = (
                        datetime.now() - start_time
                    ).total_seconds() * 1000
                    return cached_response

            # 4. Execute query with selected service
            response = await self._execute_with_service(
                service_name, request, agent_profile, session_context, fallback_chain
            )

            # 5. Enhance response with universal context
            enhanced_response = await self._enhance_response_context(
                response, agent_profile, session_context, service_name
            )

            # 6. Update session context and cache
            await self._update_session_context(
                request, enhanced_response, agent_profile
            )

            if request.enable_caching:
                await self._cache_response(request, enhanced_response)

            # 7. Track performance metrics
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            enhanced_response.processing_time_ms = processing_time

            await self._track_performance(service_name, processing_time)

            logger.info(
                f"Universal query processed: {service_name} | "
                f"{processing_time:.1f}ms | Agent: {agent_profile.primary_role if agent_profile else 'unknown'}"
            )

            return enhanced_response

        except Exception as e:
            logger.error(f"Error processing universal query: {e}")
            return await self._get_fallback_response(request, str(e))

    async def _load_agent_context(
        self,
        agent_id: str,
        session_id: Optional[str],
        location_id: Optional[str]
    ) -> tuple[Optional[AgentProfile], Optional[Dict[str, Any]]]:
        """Load agent profile and session context."""
        try:
            # Load agent profile
            agent_profile = await self.agent_profile_service.get_agent_profile(
                agent_id=agent_id,
                requester_location_id=location_id
            )

            # Load session context if available
            session_context = None
            if session_id:
                session = await self.agent_profile_service.get_agent_session(
                    session_id
                )
                if session:
                    session_context = {
                        "session_id": session.session_id,
                        "conversation_history": session.conversation_history,
                        "coaching_effectiveness": session.coaching_effectiveness,
                        "preferences": session.preferences
                    }

            return agent_profile, session_context

        except Exception as e:
            logger.error(f"Error loading agent context: {e}")
            return None, None

    async def _route_to_service(
        self,
        request: UniversalQueryRequest,
        agent_profile: Optional[AgentProfile]
    ) -> tuple[str, List[str]]:
        """Intelligent service routing based on query type and agent context."""

        # Check for explicit query type routing
        query_type_mapping = {
            QueryType.GENERAL_COACHING: "enhanced_claude_agent_service",
            QueryType.OBJECTION_HANDLING: "enhanced_claude_agent_service",
            QueryType.LEAD_QUALIFICATION: "enhanced_qualification_orchestrator",
            QueryType.PROPERTY_RECOMMENDATION: "claude_intelligent_property_recommendation",
            QueryType.MARKET_ANALYSIS: "claude_realtime_market_analysis",
            QueryType.SEMANTIC_ANALYSIS: "claude_semantic_analyzer",
            QueryType.VISION_ANALYSIS: "claude_vision_analyzer",
            QueryType.ACTION_PLANNING: "claude_action_planner",
            QueryType.CONVERSATION_ANALYSIS: "claude_conversation_analyzer",
            QueryType.BUSINESS_INTELLIGENCE: "claude_business_intelligence_automation",
            QueryType.ADVANCED_COACHING: "claude_advanced_coaching_optimization",
            QueryType.REAL_TIME_ASSISTANCE: "claude_streaming_service"
        }

        if request.query_type in query_type_mapping:
            primary_service = query_type_mapping[request.query_type]
            fallback_chain = ["enhanced_claude_agent_service", "claude_agent_service"]
            return primary_service, fallback_chain

        # Pattern-based routing using rules
        for rule in self.routing_rules:
            if self._matches_routing_rule(request, rule, agent_profile):
                return rule.service_name, rule.fallback_services

        # Default to enhanced service with agent context
        return "enhanced_claude_agent_service", ["claude_agent_service"]

    def _matches_routing_rule(
        self,
        request: UniversalQueryRequest,
        rule: ServiceRoutingRule,
        agent_profile: Optional[AgentProfile]
    ) -> bool:
        """Check if request matches a routing rule."""

        # Check query patterns
        query_lower = request.query.lower()
        pattern_match = any(pattern in query_lower for pattern in rule.query_patterns)

        if not pattern_match:
            return False

        # Check agent role constraints
        if rule.agent_roles and agent_profile:
            if agent_profile.primary_role not in rule.agent_roles:
                return False

        # Check priority constraints
        if rule.priority_threshold:
            priority_values = {
                ServicePriority.BACKGROUND: 0,
                ServicePriority.NORMAL: 1,
                ServicePriority.HIGH: 2,
                ServicePriority.CRITICAL: 3
            }
            if priority_values[request.priority] < priority_values[rule.priority_threshold]:
                return False

        return True

    async def _execute_with_service(
        self,
        service_name: str,
        request: UniversalQueryRequest,
        agent_profile: Optional[AgentProfile],
        session_context: Optional[Dict[str, Any]],
        fallback_chain: List[str]
    ) -> UniversalClaudeResponse:
        """Execute query with the selected service, with fallback handling."""

        services_to_try = [service_name] + fallback_chain

        for service in services_to_try:
            try:
                if service == "enhanced_claude_agent_service":
                    return await self._execute_enhanced_claude(
                        request, agent_profile, session_context
                    )
                elif service == "enhanced_qualification_orchestrator":
                    return await self._execute_qualification_orchestrator(
                        request, agent_profile, session_context
                    )
                else:
                    # For specialized services, use enhanced Claude with context
                    return await self._execute_enhanced_claude(
                        request, agent_profile, session_context
                    )

            except Exception as e:
                logger.warning(f"Service {service} failed: {e}, trying next fallback")
                continue

        # If all services fail, return error response
        raise Exception(f"All Claude services failed for query: {request.query[:100]}...")

    async def _execute_enhanced_claude(
        self,
        request: UniversalQueryRequest,
        agent_profile: Optional[AgentProfile],
        session_context: Optional[Dict[str, Any]]
    ) -> UniversalClaudeResponse:
        """Execute query using the enhanced Claude service with agent context."""

        if not agent_profile:
            # Fallback to base service without agent context
            base_response = await self._execute_base_claude_fallback(request)
            return base_response

        # Build conversation context
        conversation_context = {
            "agent_profile": {
                "agent_id": agent_profile.agent_id,
                "role": agent_profile.primary_role.value,
                "specializations": agent_profile.specializations,
                "guidance_preferences": [gt.value for gt in agent_profile.preferred_guidance_types]
            },
            "query_context": request.context or {},
            "session_context": session_context or {},
            "prospect_data": request.prospect_data or {},
            "property_data": request.property_data or {},
            "market_data": request.market_data or {}
        }

        # Call enhanced Claude service
        enhanced_response = await self.enhanced_claude.get_agent_aware_coaching(
            agent_id=request.agent_id,
            session_id=request.session_id or "",
            conversation_context=conversation_context,
            prospect_message=request.query,
            conversation_stage=request.conversation_stage or "discovery",
            location_id=request.location_id
        )

        # Convert to universal response format
        return UniversalClaudeResponse(
            response=enhanced_response.recommended_response or "",
            insights=enhanced_response.role_specific_insights,
            recommendations=enhanced_response.coaching_suggestions,
            confidence=enhanced_response.confidence,
            agent_role=enhanced_response.agent_role,
            guidance_types_applied=enhanced_response.guidance_types_applied,
            role_specific_insights=enhanced_response.role_specific_insights,
            service_used="enhanced_claude_agent_service",
            next_questions=[enhanced_response.next_question] if enhanced_response.next_question else [],
            urgency_level=enhanced_response.urgency,
            conversation_stage=enhanced_response.conversation_stage,
            session_id=request.session_id,
            context_preserved=True
        )

    async def _execute_qualification_orchestrator(
        self,
        request: UniversalQueryRequest,
        agent_profile: Optional[AgentProfile],
        session_context: Optional[Dict[str, Any]]
    ) -> UniversalClaudeResponse:
        """Execute query using the enhanced qualification orchestrator."""

        # This would integrate with the enhanced qualification orchestrator
        # For now, route to enhanced Claude with qualification context
        qualification_context = {
            **request.context,
            "purpose": "qualification",
            "stage": request.conversation_stage or "discovery"
        }

        qualified_request = UniversalQueryRequest(
            agent_id=request.agent_id,
            session_id=request.session_id,
            location_id=request.location_id,
            query=request.query,
            query_type=QueryType.GENERAL_COACHING,
            context=qualification_context,
            priority=request.priority,
            conversation_stage=request.conversation_stage,
            prospect_data=request.prospect_data
        )

        return await self._execute_enhanced_claude(
            qualified_request, agent_profile, session_context
        )

    async def _execute_base_claude_fallback(
        self, request: UniversalQueryRequest
    ) -> UniversalClaudeResponse:
        """Fallback to base Claude service when agent profile is unavailable."""

        # Call the base Claude agent service
        base_response = await self.enhanced_claude.base_service.chat_with_agent(
            agent_id=request.agent_id,
            query=request.query,
            lead_id=None,
            context=request.context
        )

        return UniversalClaudeResponse(
            response=base_response.response,
            insights=base_response.insights,
            recommendations=base_response.recommendations,
            confidence=base_response.confidence,
            service_used="claude_agent_service_fallback",
            next_questions=base_response.follow_up_questions,
            context_preserved=False
        )

    async def _enhance_response_context(
        self,
        response: UniversalClaudeResponse,
        agent_profile: Optional[AgentProfile],
        session_context: Optional[Dict[str, Any]],
        service_name: str
    ) -> UniversalClaudeResponse:
        """Enhance response with universal context and metadata."""

        if agent_profile and not response.agent_role:
            response.agent_role = agent_profile.primary_role.value

        if session_context and not response.context_preserved:
            response.context_preserved = True

        response.service_used = service_name

        return response

    async def _update_session_context(
        self,
        request: UniversalQueryRequest,
        response: UniversalClaudeResponse,
        agent_profile: Optional[AgentProfile]
    ) -> None:
        """Update session context with query and response for continuity."""

        if not request.session_id or not agent_profile:
            return

        try:
            # Update session with new interaction
            await self.agent_profile_service.update_session_context(
                session_id=request.session_id,
                interaction_data={
                    "query": request.query,
                    "response": response.response,
                    "service_used": response.service_used,
                    "confidence": response.confidence,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error updating session context: {e}")

    async def _check_cache(self, request: UniversalQueryRequest) -> Optional[UniversalClaudeResponse]:
        """Check for cached response."""

        cache_key = self._generate_cache_key(request)

        if cache_key in self.response_cache:
            cache_entry = self.response_cache[cache_key]
            cache_time = cache_entry.get("timestamp", datetime.min)

            if (datetime.now() - cache_time).total_seconds() < self.cache_ttl_seconds:
                cached_response = cache_entry["response"]
                cached_response.cached_response = True
                logger.debug(f"Cache hit for query: {request.query[:50]}...")
                return cached_response

        return None

    async def _cache_response(
        self, request: UniversalQueryRequest, response: UniversalClaudeResponse
    ) -> None:
        """Cache response for future use."""

        cache_key = self._generate_cache_key(request)

        self.response_cache[cache_key] = {
            "response": response,
            "timestamp": datetime.now()
        }

        # Clean up old cache entries
        await self._cleanup_cache()

    def _generate_cache_key(self, request: UniversalQueryRequest) -> str:
        """Generate cache key for request."""

        cache_components = [
            request.agent_id,
            request.query,
            str(request.query_type.value),
            str(request.context),
            str(request.conversation_stage)
        ]

        cache_string = "|".join(cache_components)
        return hashlib.md5(cache_string.encode()).hexdigest()

    async def _cleanup_cache(self) -> None:
        """Clean up expired cache entries."""

        current_time = datetime.now()
        expired_keys = []

        for key, entry in self.response_cache.items():
            cache_time = entry.get("timestamp", datetime.min)
            if (current_time - cache_time).total_seconds() > self.cache_ttl_seconds:
                expired_keys.append(key)

        for key in expired_keys:
            del self.response_cache[key]

    async def _track_performance(self, service_name: str, processing_time: float) -> None:
        """Track performance metrics for optimization."""

        if service_name not in self.performance_history:
            self.performance_history[service_name] = []

        self.performance_history[service_name].append(processing_time)

        # Keep only last 100 measurements
        if len(self.performance_history[service_name]) > 100:
            self.performance_history[service_name] = self.performance_history[service_name][-100:]

    async def _get_fallback_response(
        self, request: UniversalQueryRequest, error_message: str
    ) -> UniversalClaudeResponse:
        """Generate fallback response when all services fail."""

        return UniversalClaudeResponse(
            response=f"I apologize, but I'm experiencing technical difficulties. Please try your request again in a moment.",
            insights=[f"Error occurred: {error_message}"],
            recommendations=["Please try rephrasing your question", "Contact support if the issue persists"],
            confidence=0.1,
            service_used="fallback_handler",
            urgency_level="normal"
        )

    # Performance monitoring methods
    async def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all Claude services."""

        health_status = {}

        for service_name, history in self.performance_history.items():
            if history:
                avg_time = sum(history) / len(history)
                health_status[service_name] = {
                    "avg_response_time_ms": round(avg_time, 2),
                    "recent_requests": len(history),
                    "status": "healthy" if avg_time < 1000 else "slow"
                }

        return health_status

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics."""

        total_entries = len(self.response_cache)
        current_time = datetime.now()

        valid_entries = sum(
            1 for entry in self.response_cache.values()
            if (current_time - entry["timestamp"]).total_seconds() < self.cache_ttl_seconds
        )

        return {
            "total_cached_responses": total_entries,
            "valid_cache_entries": valid_entries,
            "cache_hit_rate": "Not yet available",  # Would track this with usage
            "cache_ttl_seconds": self.cache_ttl_seconds
        }


# Convenience functions for easy integration
async def process_claude_query(
    agent_id: str,
    query: str,
    query_type: QueryType = QueryType.GENERAL_COACHING,
    session_id: Optional[str] = None,
    location_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    priority: ServicePriority = ServicePriority.NORMAL
) -> UniversalClaudeResponse:
    """
    Convenience function for processing Claude queries through the gateway.

    Args:
        agent_id: Agent identifier
        query: Natural language query
        query_type: Type of query for routing
        session_id: Optional session ID for context continuity
        location_id: Optional location ID for multi-tenant support
        context: Additional context data
        priority: Query priority level

    Returns:
        Universal Claude response with agent context
    """

    gateway = UniversalClaudeGateway()

    request = UniversalQueryRequest(
        agent_id=agent_id,
        query=query,
        query_type=query_type,
        session_id=session_id,
        location_id=location_id,
        context=context,
        priority=priority
    )

    return await gateway.process_universal_query(request)