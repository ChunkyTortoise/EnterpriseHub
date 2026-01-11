"""
ServiceRegistry - Unified API Gateway for GHL Real Estate AI

This module provides a single entry point to all 61+ backend services,
implementing the "One Import Rule" for clean frontend integration.

Architecture:
- Lazy Loading: Services are instantiated only when first accessed
- Graceful Degradation: Falls back to mock data if API keys are missing
- Type Safety: Returns structured dictionaries ready for frontend rendering
- Error Resilience: Never crashes; logs errors and returns safe defaults

Usage:
    from ghl_real_estate_ai.core import ServiceRegistry
    
    registry = ServiceRegistry(location_id="loc_123", demo_mode=True)
    
    # High-level operations
    dashboard_data = registry.get_executive_dashboard_data()
    lead_analysis = registry.analyze_lead(lead_data)
    commission_report = registry.calculate_commissions(deals)
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

# Import service classes dynamically to handle missing/renamed classes gracefully
# This ensures the registry works even if some services are unavailable

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Unified service registry providing single-point access to all backend services.
    
    Implements lazy loading, graceful degradation, and demo mode support.
    """
    
    def __init__(
        self,
        location_id: Optional[str] = None,
        demo_mode: bool = False,
        api_key: Optional[str] = None
    ):
        """
        Initialize the service registry.
        
        Args:
            location_id: GHL location ID for API calls
            demo_mode: If True, use mock data instead of real API calls
            api_key: GHL API key (optional, falls back to environment variable)
        """
        self.location_id = location_id or os.getenv("GHL_LOCATION_ID", "demo_location")
        self.demo_mode = demo_mode or not api_key and not os.getenv("GHL_API_KEY")
        self.api_key = api_key or os.getenv("GHL_API_KEY")
        
        # Lazy-loaded service instances
        self._services: Dict[str, Any] = {}
        
        # Track initialization status
        self._initialized = False
        
        logger.info(
            f"ServiceRegistry initialized (location={self.location_id}, "
            f"demo_mode={self.demo_mode})"
        )
    
    # ========================================================================
    # Service Accessors (Lazy Loading)
    # ========================================================================
    
    def _get_service(self, service_name: str, module_name: str, class_name: str) -> Any:
        """
        Get or create a service instance with lazy loading and dynamic import.
        
        Args:
            service_name: Unique identifier for the service
            module_name: Module name (e.g., 'lead_scorer')
            class_name: Class name to import
            
        Returns:
            Service instance or None if unavailable
        """
        if service_name not in self._services:
            try:
                # Dynamic import
                module = __import__(
                    f"ghl_real_estate_ai.services.{module_name}",
                    fromlist=[class_name]
                )
                service_class = getattr(module, class_name)
                
                # Create service instance
                if service_name == "demo_mode":
                    self._services[service_name] = service_class()
                else:
                    # Try different initialization patterns
                    try:
                        self._services[service_name] = service_class(
                            location_id=self.location_id
                        )
                    except TypeError:
                        # Some services don't take location_id
                        try:
                            self._services[service_name] = service_class()
                        except:
                            self._services[service_name] = service_class(
                                ghl_location_id=self.location_id
                            )
                
                logger.debug(f"Initialized service: {service_name}")
            except Exception as e:
                logger.warning(f"Service {service_name} unavailable: {e}")
                # Return None for unavailable services
                return None
        
        return self._services[service_name]
    
    @property
    def lead_scorer(self):
        """Get or create LeadScorer instance."""
        return self._get_service("lead_scorer", "lead_scorer", "LeadScorer")
    
    @property
    def deal_closer_ai(self):
        """Get or create DealCloserAI instance."""
        return self._get_service("deal_closer_ai", "deal_closer_ai", "DealCloserAI")
    
    @property
    def commission_calculator(self):
        """Get or create CommissionCalculator instance."""
        return self._get_service("commission_calculator", "commission_calculator", "CommissionCalculator")
    
    @property
    def executive_dashboard(self):
        """Get or create ExecutiveDashboardService instance."""
        return self._get_service("executive_dashboard", "executive_dashboard", "ExecutiveDashboardService")
    
    @property
    def demo_mode_service(self):
        """Get or create DemoModeManager instance."""
        return self._get_service("demo_mode", "demo_mode", "DemoModeManager")
    
    @property
    def meeting_prep(self):
        """Get or create MeetingPrepAssistant instance."""
        return self._get_service("meeting_prep", "meeting_prep_assistant", "MeetingPrepAssistant")
    
    @property
    def predictive_scoring(self):
        """Get or create PredictiveLeadScorer instance."""
        return self._get_service("predictive_scoring", "predictive_scoring", "PredictiveLeadScorer")
    
    @property
    def revenue_attribution(self):
        """Get or create RevenueAttributionEngine instance."""
        return self._get_service("revenue_attribution", "revenue_attribution", "RevenueAttributionEngine")
    
    @property
    def competitive_benchmarking(self):
        """Get or create BenchmarkingEngine instance."""
        return self._get_service("competitive_benchmarking", "competitive_benchmarking", "BenchmarkingEngine")
    
    @property
    def smart_recommendations(self):
        """Get or create RecommendationEngine instance."""
        return self._get_service("smart_recommendations", "smart_recommendations", "RecommendationEngine")
    
    @property
    def analytics_engine(self):
        """Get or create AnalyticsEngine instance."""
        return self._get_service("analytics_engine", "analytics_engine", "AnalyticsEngine")
    
    @property
    def property_matcher(self):
        """Get or create PropertyMatcher instance."""
        return self._get_service("property_matcher", "property_matcher", "PropertyMatcher")
    
    @property
    def workflow_marketplace(self):
        """Get or create WorkflowMarketplaceService instance."""
        return self._get_service("workflow_marketplace", "workflow_marketplace", "WorkflowMarketplaceService")
    
    @property
    def memory(self):
        """Get or create MemoryService instance."""
        return self._get_service("memory", "memory_service", "MemoryService")
    
    @property
    def monitoring(self):
        """Get or create MonitoringService instance."""
        return self._get_service("monitoring", "monitoring", "MonitoringService")

    # ========================================================================
    # Claude AI Services (Phase 2 Enhancement)
    # ========================================================================

    @property
    def claude_agent(self):
        """Get or create ClaudeAgentService instance."""
        return self._get_service("claude_agent", "claude_agent_service", "ClaudeAgentService")

    @property
    def claude_semantic_analyzer(self):
        """Get or create ClaudeSemanticAnalyzer instance."""
        return self._get_service("claude_semantic_analyzer", "claude_semantic_analyzer", "ClaudeSemanticAnalyzer")

    @property
    def qualification_orchestrator(self):
        """Get or create QualificationOrchestrator instance."""
        return self._get_service("qualification_orchestrator", "qualification_orchestrator", "QualificationOrchestrator")

    @property
    def business_metrics(self):
        """Get or create BusinessMetricsService instance."""
        return self._get_service("business_metrics", "business_metrics_service", "BusinessMetricsService")

    @property
    def agent_profile_service(self):
        """Get or create AgentProfileService instance with graceful fallback."""
        return self._get_service("agent_profile_service", "agent_profile_service", "AgentProfileService")

    @property
    def enhanced_claude_agent(self):
        """Get or create EnhancedClaudeAgentService instance with graceful fallback."""
        return self._get_service("enhanced_claude_agent", "enhanced_claude_agent_service", "EnhancedClaudeAgentService")

    # ========================================================================
    # High-Level Convenience Methods (Frontend-Ready)
    # ========================================================================
    
    def get_executive_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive executive dashboard data.
        
        Returns:
            Dictionary containing:
            - revenue_metrics: Current revenue, trends, forecasts
            - lead_metrics: Lead counts, conversion rates, velocity
            - performance_metrics: Team performance, top performers
            - alert_summary: Critical alerts and recommendations
        """
        try:
            if self.demo_mode:
                return self.demo_mode_service.get_executive_dashboard()
            
            dashboard = self.executive_dashboard
            if not dashboard:
                return self._get_safe_dashboard_fallback()
            
            return dashboard.get_dashboard_data()
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return self._get_safe_dashboard_fallback()
    
    def analyze_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive lead analysis.
        
        Args:
            lead_data: Lead information (contact details, interactions, etc.)
            
        Returns:
            Dictionary containing:
            - score: Numeric lead score (0-100)
            - grade: Letter grade (A+, A, B+, etc.)
            - insights: List of behavioral insights
            - recommendations: Suggested next actions
            - property_matches: Top matching properties
        """
        try:
            if self.demo_mode:
                return self.demo_mode_service.analyze_lead(lead_data)
            
            scorer = self.lead_scorer
            if not scorer:
                return self._get_safe_lead_fallback()
            
            # Get lead score
            score_result = scorer.score_lead(lead_data)
            
            # Get property matches
            matcher = self.property_matcher
            matches = []
            if matcher:
                try:
                    matches = matcher.find_matches(lead_data.get("preferences", {}))
                except Exception as e:
                    logger.warning(f"Property matching failed: {e}")
            
            # Get recommendations
            recommender = self.smart_recommendations
            recommendations = []
            if recommender:
                try:
                    recommendations = recommender.get_recommendations(
                        lead_data.get("id"),
                        context={"score": score_result.get("score")}
                    )
                except Exception as e:
                    logger.warning(f"Recommendations failed: {e}")
            
            return {
                **score_result,
                "property_matches": matches[:5],  # Top 5
                "recommendations": recommendations[:3],  # Top 3
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing lead: {e}")
            return self._get_safe_lead_fallback()
    
    def calculate_commissions(
        self,
        deals: List[Dict[str, Any]],
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate commission breakdown and projections.
        
        Args:
            deals: List of closed/pending deals
            agent_id: Optional agent ID to filter by
            
        Returns:
            Dictionary containing:
            - total_commission: Total commission amount
            - breakdown: Commission by category
            - projections: Future commission estimates
            - charts: Data ready for visualization
        """
        try:
            if self.demo_mode:
                return self.demo_mode_service.calculate_commissions(deals)
            
            calculator = self.commission_calculator
            if not calculator:
                return self._get_safe_commission_fallback()
            
            return calculator.calculate_detailed_breakdown(deals, agent_id)
            
        except Exception as e:
            logger.error(f"Error calculating commissions: {e}")
            return self._get_safe_commission_fallback()
    
    def get_deal_closer_suggestions(
        self,
        lead_id: str,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get AI-powered deal closing suggestions.
        
        Args:
            lead_id: Lead identifier
            conversation_history: Recent conversation messages
            
        Returns:
            Dictionary containing:
            - suggested_response: AI-generated response
            - objection_handling: Tips for overcoming objections
            - closing_techniques: Recommended closing strategies
            - urgency_triggers: Time-sensitive opportunities
        """
        try:
            if self.demo_mode:
                return self.demo_mode_service.get_deal_closer_suggestions(
                    lead_id, conversation_history
                )
            
            deal_closer = self.deal_closer_ai
            if not deal_closer:
                return self._get_safe_deal_closer_fallback()
            
            return deal_closer.get_suggestions(lead_id, conversation_history)
            
        except Exception as e:
            logger.error(f"Error getting deal closer suggestions: {e}")
            return self._get_safe_deal_closer_fallback()
    
    def prepare_meeting(
        self,
        lead_id: str,
        meeting_type: str = "showing"
    ) -> Dict[str, Any]:
        """
        Generate meeting preparation materials.
        
        Args:
            lead_id: Lead identifier
            meeting_type: Type of meeting (showing, listing, closing, etc.)
            
        Returns:
            Dictionary containing:
            - brief: Executive summary
            - talking_points: Key discussion topics
            - documents: Required documents checklist
            - research: Property/market research
        """
        try:
            if self.demo_mode:
                return self.demo_mode_service.prepare_meeting(lead_id, meeting_type)
            
            prep_assistant = self.meeting_prep
            if not prep_assistant:
                return self._get_safe_meeting_prep_fallback()
            
            return prep_assistant.prepare(lead_id, meeting_type)
            
        except Exception as e:
            logger.error(f"Error preparing meeting: {e}")
            return self._get_safe_meeting_prep_fallback()
    
    def get_revenue_metrics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive revenue analytics.
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            
        Returns:
            Dictionary containing:
            - total_revenue: Total revenue in period
            - revenue_by_source: Attribution breakdown
            - trends: Historical trends
            - forecasts: Future projections
        """
        try:
            if self.demo_mode:
                return self.demo_mode_service.get_revenue_metrics()
            
            attribution = self.revenue_attribution
            if not attribution:
                return self._get_safe_revenue_fallback()
            
            return attribution.get_attribution_report(start_date, end_date)
            
        except Exception as e:
            logger.error(f"Error getting revenue metrics: {e}")
            return self._get_safe_revenue_fallback()
    
    def get_workflow_templates(
        self,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get available workflow templates from marketplace.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of workflow templates with metadata
        """
        try:
            if self.demo_mode:
                return self.demo_mode_service.get_workflow_templates(category)
            
            marketplace = self.workflow_marketplace
            if not marketplace:
                return []
            
            return marketplace.get_templates(category)
            
        except Exception as e:
            logger.error(f"Error getting workflow templates: {e}")
            return []
    
    def get_competitive_analysis(
        self,
        property_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get competitive market analysis.
        
        Args:
            property_id: Optional property to analyze
            
        Returns:
            Dictionary containing market positioning and competitive intelligence
        """
        try:
            if self.demo_mode:
                return self.demo_mode_service.get_competitive_analysis()
            
            benchmarking = self.competitive_benchmarking
            if not benchmarking:
                return self._get_safe_competitive_fallback()
            
            return benchmarking.analyze(property_id)
            
        except Exception as e:
            logger.error(f"Error getting competitive analysis: {e}")
            return self._get_safe_competitive_fallback()
    
    # ========================================================================
    # Safe Fallback Methods
    # ========================================================================
    
    def _get_safe_dashboard_fallback(self) -> Dict[str, Any]:
        """Return safe default dashboard data."""
        return {
            "revenue_metrics": {
                "total": 0,
                "trend": "stable",
                "forecast": 0
            },
            "lead_metrics": {
                "total": 0,
                "conversion_rate": 0,
                "velocity": 0
            },
            "performance_metrics": {
                "team_performance": [],
                "top_performers": []
            },
            "alert_summary": {
                "critical": 0,
                "warnings": 0,
                "info": 1,
                "messages": ["Dashboard in demo mode"]
            },
            "demo_mode": True
        }
    
    def _get_safe_lead_fallback(self) -> Dict[str, Any]:
        """Return safe default lead analysis."""
        return {
            "score": 50,
            "grade": "B",
            "insights": ["Lead analysis unavailable"],
            "recommendations": ["Configure API keys to enable analysis"],
            "property_matches": [],
            "demo_mode": True
        }
    
    def _get_safe_commission_fallback(self) -> Dict[str, Any]:
        """Return safe default commission data."""
        return {
            "total_commission": 0,
            "breakdown": {},
            "projections": [],
            "charts": {"labels": [], "values": []},
            "demo_mode": True
        }
    
    def _get_safe_deal_closer_fallback(self) -> Dict[str, Any]:
        """Return safe default deal closer suggestions."""
        return {
            "suggested_response": "Configure API keys to enable AI suggestions.",
            "objection_handling": [],
            "closing_techniques": [],
            "urgency_triggers": [],
            "demo_mode": True
        }
    
    def _get_safe_meeting_prep_fallback(self) -> Dict[str, Any]:
        """Return safe default meeting prep."""
        return {
            "brief": "Meeting preparation unavailable",
            "talking_points": [],
            "documents": [],
            "research": {},
            "demo_mode": True
        }
    
    def _get_safe_revenue_fallback(self) -> Dict[str, Any]:
        """Return safe default revenue metrics."""
        return {
            "total_revenue": 0,
            "revenue_by_source": {},
            "trends": [],
            "forecasts": [],
            "demo_mode": True
        }
    
    def _get_safe_competitive_fallback(self) -> Dict[str, Any]:
        """Return safe default competitive analysis."""
        return {
            "market_position": "unknown",
            "competitors": [],
            "insights": [],
            "demo_mode": True
        }

    # ========================================================================
    # Claude AI Convenience Methods (Phase 2 Enhancement)
    # ========================================================================

    async def get_real_time_coaching(
        self,
        agent_id: str,
        conversation_context: Dict[str, Any],
        prospect_message: str,
        conversation_stage: str = "discovery"
    ) -> Dict[str, Any]:
        """
        Get real-time coaching suggestions for agent during conversation.

        Args:
            agent_id: Agent identifier
            conversation_context: Current conversation context
            prospect_message: Latest prospect message
            conversation_stage: Current conversation stage

        Returns:
            Dictionary containing:
            - suggestions: List of coaching suggestions
            - objection_detected: Boolean indicating objection
            - recommended_response: Suggested response
            - next_questions: Recommended follow-up questions
        """
        try:
            if self.demo_mode:
                return self._get_safe_claude_coaching_fallback()

            claude_agent = self.claude_agent
            if not claude_agent:
                return self._get_safe_claude_coaching_fallback()

            return await claude_agent.get_real_time_coaching(
                agent_id=agent_id,
                conversation_context=conversation_context,
                prospect_message=prospect_message,
                conversation_stage=conversation_stage
            )

        except Exception as e:
            logger.error(f"Error getting real-time coaching: {e}")
            return self._get_safe_claude_coaching_fallback()

    async def analyze_lead_semantics(
        self,
        conversation_messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform semantic analysis of lead conversations.

        Args:
            conversation_messages: List of conversation messages

        Returns:
            Dictionary containing:
            - intent_analysis: Detected intentions and motivations
            - semantic_preferences: Extracted preferences
            - qualification_assessment: Qualification completeness
            - recommended_questions: Intelligent follow-up questions
        """
        try:
            if self.demo_mode:
                return self._get_safe_claude_semantics_fallback()

            semantic_analyzer = self.claude_semantic_analyzer
            if not semantic_analyzer:
                return self._get_safe_claude_semantics_fallback()

            # Perform comprehensive semantic analysis
            intent_analysis = await semantic_analyzer.analyze_lead_intent(conversation_messages)
            preferences = await semantic_analyzer.extract_semantic_preferences(
                [msg.get("content", "") for msg in conversation_messages]
            )

            # Build unified response
            return {
                "intent_analysis": intent_analysis,
                "semantic_preferences": preferences,
                "confidence": intent_analysis.get("confidence", 50),
                "extracted_data": intent_analysis.get("extracted_data", {}),
                "urgency_score": intent_analysis.get("urgency_score", 50),
                "analyzed_at": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing lead semantics: {e}")
            return self._get_safe_claude_semantics_fallback()

    async def start_intelligent_qualification(
        self,
        contact_id: str,
        contact_name: str,
        initial_message: str = "",
        source: str = "website",
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start intelligent qualification flow with adaptive questioning.

        Args:
            contact_id: Unique contact identifier
            contact_name: Contact's name
            initial_message: Initial message from contact
            source: Lead source
            agent_id: Agent handling the lead

        Returns:
            Dictionary containing:
            - flow_id: Qualification flow identifier
            - journey_id: Lifecycle journey identifier
            - next_questions: Recommended questions
            - initial_analysis: Analysis of initial message
        """
        try:
            if self.demo_mode:
                return self._get_safe_claude_qualification_fallback()

            orchestrator = self.qualification_orchestrator
            if not orchestrator:
                return self._get_safe_claude_qualification_fallback()

            return await orchestrator.start_qualification_flow(
                contact_id=contact_id,
                contact_name=contact_name,
                initial_message=initial_message,
                source=source,
                agent_id=agent_id
            )

        except Exception as e:
            logger.error(f"Error starting qualification flow: {e}")
            return self._get_safe_claude_qualification_fallback()

    async def process_qualification_response(
        self,
        flow_id: str,
        user_message: str,
        agent_response: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process response in qualification flow and get next recommendations.

        Args:
            flow_id: Qualification flow identifier
            user_message: User's response/message
            agent_response: Agent's response (if any)
            context: Additional context data

        Returns:
            Dictionary containing:
            - completion_percentage: Qualification completeness
            - next_questions: Recommended questions
            - semantic_analysis: Analysis of response
            - agent_recommendations: Suggested actions for agent
        """
        try:
            if self.demo_mode:
                return self._get_safe_claude_qualification_fallback()

            orchestrator = self.qualification_orchestrator
            if not orchestrator:
                return self._get_safe_claude_qualification_fallback()

            return await orchestrator.process_response(
                flow_id=flow_id,
                user_message=user_message,
                agent_response=agent_response,
                context=context
            )

        except Exception as e:
            logger.error(f"Error processing qualification response: {e}")
            return self._get_safe_claude_qualification_fallback()

    def get_qualification_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive qualification analytics and metrics.

        Returns:
            Dictionary containing:
            - flow_metrics: Qualification flow statistics
            - completion_rates: Completion rates by area
            - performance_insights: Performance analysis
        """
        try:
            if self.demo_mode:
                return self._get_safe_claude_analytics_fallback()

            orchestrator = self.qualification_orchestrator
            if not orchestrator:
                return self._get_safe_claude_analytics_fallback()

            return orchestrator.get_qualification_analytics()

        except Exception as e:
            logger.error(f"Error getting qualification analytics: {e}")
            return self._get_safe_claude_analytics_fallback()

    # ========================================================================
    # Claude AI Safe Fallback Methods
    # ========================================================================

    def _get_safe_claude_coaching_fallback(self) -> Dict[str, Any]:
        """Return safe default Claude coaching data."""
        return {
            "suggestions": ["Configure Claude API for real-time coaching"],
            "objection_detected": False,
            "recommended_response": "Continue the conversation to gather more information",
            "next_questions": [],
            "demo_mode": True
        }

    def _get_safe_claude_semantics_fallback(self) -> Dict[str, Any]:
        """Return safe default Claude semantics analysis."""
        return {
            "intent_analysis": {"intent": "unknown", "confidence": 50},
            "semantic_preferences": {},
            "confidence": 50,
            "extracted_data": {},
            "urgency_score": 50,
            "demo_mode": True
        }

    def _get_safe_claude_qualification_fallback(self) -> Dict[str, Any]:
        """Return safe default Claude qualification data."""
        return {
            "flow_id": "demo_flow",
            "completion_percentage": 0,
            "next_questions": [],
            "status": "demo",
            "demo_mode": True
        }

    def _get_safe_claude_analytics_fallback(self) -> Dict[str, Any]:
        """Return safe default Claude analytics."""
        return {
            "total_flows": 0,
            "active_flows": 0,
            "completion_rates": {},
            "demo_mode": True
        }

    # ========================================================================
    # Agent Profile System Convenience Methods
    # ========================================================================

    async def start_agent_session_with_fallback(
        self,
        agent_id: str,
        location_id: str,
        guidance_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Start agent session with comprehensive fallback.

        Args:
            agent_id: Agent identifier
            location_id: Location context for session
            guidance_types: Optional guidance type preferences

        Returns:
            Dictionary containing session information or fallback data
        """
        try:
            if self.demo_mode:
                return self._get_demo_agent_session(agent_id, location_id)

            agent_service = self.agent_profile_service
            if not agent_service:
                logger.warning("AgentProfileService unavailable, using fallback")
                return self._get_fallback_agent_session(agent_id, location_id)

            # Import guidance types
            from ghl_real_estate_ai.models.agent_profile_models import GuidanceType

            # Convert string guidance types to enums
            guidance_enums = []
            if guidance_types:
                guidance_enums = [GuidanceType(gt) for gt in guidance_types if gt in GuidanceType.__members__]

            session = await agent_service.start_agent_session(
                agent_id=agent_id,
                location_id=location_id,
                guidance_types=guidance_enums
            )

            return {
                "session_id": session.session_id,
                "agent_id": session.agent_id,
                "location_id": session.location_id,
                "active_guidance_types": [gt.value for gt in session.active_guidance_types],
                "conversation_stage": session.conversation_stage.value,
                "status": "active",
                "enhanced_features": True,
                "demo_mode": False
            }

        except Exception as e:
            logger.error(f"Error starting agent session: {e}")
            return self._get_fallback_agent_session(agent_id, location_id)

    async def get_location_agents(
        self,
        location_id: str,
        role_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get all agents accessible to a location (Shared Agent Pool).

        Args:
            location_id: Location identifier
            role_filter: Optional role filter (seller_agent, buyer_agent, transaction_coordinator)

        Returns:
            Dictionary containing agents and metadata
        """
        try:
            if self.demo_mode:
                return self._get_demo_location_agents(location_id, role_filter)

            agent_service = self.agent_profile_service
            if not agent_service:
                return self._get_fallback_location_agents(location_id)

            # Import AgentRole if needed
            role_enum = None
            if role_filter:
                from ghl_real_estate_ai.models.agent_profile_models import AgentRole
                try:
                    role_enum = AgentRole(role_filter)
                except ValueError:
                    logger.warning(f"Invalid role filter: {role_filter}")

            agents = await agent_service.get_agents_for_location(
                location_id=location_id,
                role_filter=role_enum,
                active_only=True
            )

            return {
                "status": "success",
                "location_id": location_id,
                "agents": [
                    {
                        "agent_id": agent.agent_id,
                        "agent_name": agent.agent_name,
                        "email": agent.email,
                        "primary_role": agent.primary_role.value,
                        "secondary_roles": [r.value for r in agent.secondary_roles],
                        "years_experience": agent.years_experience,
                        "specializations": agent.specializations,
                        "accessible_locations": agent.accessible_locations,
                        "preferred_guidance_types": [g.value for g in agent.preferred_guidance_types],
                        "communication_style": agent.communication_style.value,
                        "is_active": agent.is_active
                    }
                    for agent in agents
                ],
                "total_count": len(agents),
                "role_filter": role_filter,
                "enhanced_features": True,
                "demo_mode": False
            }

        except Exception as e:
            logger.error(f"Error getting location agents: {e}")
            return self._get_fallback_location_agents(location_id)

    async def get_agent_profile_summary(
        self,
        agent_id: str,
        requester_location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get agent profile summary with session information.

        Args:
            agent_id: Agent identifier
            requester_location_id: Location context for access control

        Returns:
            Dictionary containing agent profile summary
        """
        try:
            if self.demo_mode:
                return self._get_demo_agent_profile(agent_id)

            agent_service = self.agent_profile_service
            if not agent_service:
                return self._get_fallback_agent_profile(agent_id)

            profile = await agent_service.get_agent_profile(
                agent_id=agent_id,
                requester_location_id=requester_location_id or self.location_id
            )

            if not profile:
                return self._get_fallback_agent_profile(agent_id, not_found=True)

            return {
                "agent_id": profile.agent_id,
                "agent_name": profile.agent_name,
                "email": profile.email,
                "primary_role": profile.primary_role.value,
                "secondary_roles": [r.value for r in profile.secondary_roles],
                "years_experience": profile.years_experience,
                "specializations": profile.specializations,
                "accessible_locations": profile.accessible_locations,
                "preferred_guidance_types": [g.value for g in profile.preferred_guidance_types],
                "coaching_style_preference": profile.coaching_style_preference.value,
                "communication_style": profile.communication_style.value,
                "current_session_id": profile.current_session_id,
                "active_conversations": profile.active_conversations,
                "skill_levels": profile.skill_levels,
                "performance_metrics_summary": profile.performance_metrics_summary,
                "is_active": profile.is_active,
                "last_login": profile.last_login.isoformat() if profile.last_login else None,
                "created_at": profile.created_at.isoformat(),
                "enhanced_features": True,
                "demo_mode": False
            }

        except Exception as e:
            logger.error(f"Error getting agent profile: {e}")
            return self._get_fallback_agent_profile(agent_id)

    async def get_agent_session_status(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Get agent session status and metrics.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary containing session status and metrics
        """
        try:
            if self.demo_mode:
                return self._get_demo_session_status(session_id)

            agent_service = self.agent_profile_service
            if not agent_service:
                return self._get_fallback_session_status(session_id)

            session = await agent_service.get_agent_session(session_id)

            if not session:
                return self._get_fallback_session_status(session_id, not_found=True)

            return {
                "session_id": session.session_id,
                "agent_id": session.agent_id,
                "location_id": session.location_id,
                "current_lead_id": session.current_lead_id,
                "conversation_stage": session.conversation_stage.value,
                "active_guidance_types": [g.value for g in session.active_guidance_types],
                "session_start_time": session.session_start_time.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "duration_minutes": session.get_session_duration_minutes(),
                "messages_exchanged": session.messages_exchanged,
                "guidance_requests": session.guidance_requests,
                "coaching_effectiveness_score": session.coaching_effectiveness_score,
                "is_active": session.is_active,
                "enhanced_features": True,
                "demo_mode": False
            }

        except Exception as e:
            logger.error(f"Error getting session status: {e}")
            return self._get_fallback_session_status(session_id)

    # ========================================================================
    # Business Intelligence Convenience Methods
    # ========================================================================

    async def get_business_dashboard_metrics(
        self,
        location_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive business intelligence dashboard metrics.

        Args:
            location_id: GHL location identifier
            days: Number of days to analyze

        Returns:
            Dictionary with comprehensive business metrics
        """
        try:
            if self.demo_mode:
                return self._get_safe_business_metrics_fallback()

            business_metrics = self.business_metrics
            if not business_metrics:
                return self._get_safe_business_metrics_fallback()

            return await business_metrics.get_executive_dashboard_metrics(
                location_id, days
            )

        except Exception as e:
            logger.error(f"Error getting business dashboard metrics: {e}")
            return self._get_safe_business_metrics_fallback()

    async def track_lead_conversion(
        self,
        contact_id: str,
        location_id: str,
        stage: str,
        ai_score: Optional[int] = None,
        agent_id: Optional[str] = None,
        deal_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Track lead conversion stage progression.

        Args:
            contact_id: GHL contact identifier
            location_id: GHL location identifier
            stage: Conversion stage name
            ai_score: AI lead score
            agent_id: Agent handling the lead
            deal_value: Deal value for closed deals
            metadata: Additional tracking data

        Returns:
            True if tracking succeeded
        """
        try:
            if self.demo_mode:
                return True

            business_metrics = self.business_metrics
            if not business_metrics:
                return False

            # Import ConversionStage enum
            from ghl_real_estate_ai.services.business_metrics_service import ConversionStage
            from decimal import Decimal

            # Map stage string to enum
            stage_mapping = {
                "lead_created": ConversionStage.LEAD_CREATED,
                "ai_qualified": ConversionStage.AI_QUALIFIED,
                "human_contacted": ConversionStage.HUMAN_CONTACTED,
                "appointment_scheduled": ConversionStage.APPOINTMENT_SCHEDULED,
                "property_showing": ConversionStage.PROPERTY_SHOWING,
                "offer_submitted": ConversionStage.OFFER_SUBMITTED,
                "contract_signed": ConversionStage.CONTRACT_SIGNED,
                "deal_closed": ConversionStage.DEAL_CLOSED
            }

            conversion_stage = stage_mapping.get(stage.lower())
            if not conversion_stage:
                logger.warning(f"Unknown conversion stage: {stage}")
                return False

            await business_metrics.track_conversion_stage(
                contact_id=contact_id,
                location_id=location_id,
                stage=conversion_stage,
                ai_score=ai_score,
                agent_id=agent_id,
                deal_value=Decimal(str(deal_value)) if deal_value else None,
                metadata=metadata
            )

            return True

        except Exception as e:
            logger.error(f"Error tracking lead conversion: {e}")
            return False

    async def track_agent_performance(
        self,
        agent_id: str,
        location_id: str,
        activity: str,
        contact_id: Optional[str] = None,
        deal_value: Optional[float] = None,
        response_time_minutes: Optional[float] = None,
        ai_recommendation_used: bool = False
    ) -> bool:
        """
        Track agent performance and activity metrics.

        Args:
            agent_id: Agent identifier
            location_id: GHL location identifier
            activity: Activity type (contact, deal_closed, etc.)
            contact_id: Contact involved
            deal_value: Deal value for closed deals
            response_time_minutes: Response time in minutes
            ai_recommendation_used: Whether AI recommendation was used

        Returns:
            True if tracking succeeded
        """
        try:
            if self.demo_mode:
                return True

            business_metrics = self.business_metrics
            if not business_metrics:
                return False

            from decimal import Decimal

            await business_metrics.track_agent_activity(
                agent_id=agent_id,
                location_id=location_id,
                activity_type=activity,
                contact_id=contact_id,
                deal_value=Decimal(str(deal_value)) if deal_value else None,
                response_time_minutes=response_time_minutes,
                ai_recommendation_used=ai_recommendation_used
            )

            return True

        except Exception as e:
            logger.error(f"Error tracking agent performance: {e}")
            return False

    def _get_safe_business_metrics_fallback(self) -> Dict[str, Any]:
        """Return safe default business metrics."""
        return {
            "summary": {
                "total_revenue": 0.0,
                "revenue_per_lead": 0.0,
                "conversion_rate": 0.0,
                "webhook_success_rate": 100.0
            },
            "ghl_integration": {
                "total_webhooks": 0,
                "success_rate": 100.0,
                "avg_processing_time": 0.5,
                "meets_sla": True,
                "contact_enrichment_rate": 0.0,
                "ai_activation_rate": 0.0
            },
            "business_impact": {
                "total_revenue": 0.0,
                "revenue_per_lead": 0.0,
                "conversion_rate": 0.0,
                "avg_deal_size": 0.0,
                "time_to_conversion": 0.0,
                "ai_score_correlation": 0.0
            },
            "property_matching": {
                "total_recommendations": 0,
                "acceptance_rate": 0.0,
                "showing_rate": 0.0,
                "avg_recommendation_score": 0.0
            },
            "top_agents": [],
            "generated_at": datetime.now().isoformat(),
            "demo_mode": True
        }

    # ========================================================================
    # System Health & Diagnostics
    # ========================================================================
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get overall system health status.
        
        Returns:
            Dictionary containing:
            - status: overall, critical, warning, healthy
            - services_loaded: Count of initialized services
            - demo_mode: Whether in demo mode
            - last_check: Timestamp
        """
        loaded_services = len(self._services)
        
        return {
            "status": "demo" if self.demo_mode else "healthy",
            "services_loaded": loaded_services,
            "demo_mode": self.demo_mode,
            "location_id": self.location_id,
            "last_check": datetime.now().isoformat()
        }
    
    def list_available_services(self) -> List[str]:
        """
        List all available service names.
        
        Returns:
            List of service property names
        """
        return [
            "lead_scorer", "deal_closer_ai", "commission_calculator",
            "executive_dashboard", "meeting_prep", "predictive_scoring",
            "revenue_attribution", "competitive_benchmarking",
            "smart_recommendations", "analytics_engine", "property_matcher",
            "smart_segmentation", "content_personalization",
            "workflow_marketplace", "hot_lead_fastlane", "auto_followup",
            "document_generator", "agent_coaching", "win_loss_analysis",
            "cma_generator", "property_launcher", "voice_receptionist",
            "tour_scheduler", "client_portal", "neighborhood_insights",
            "social_media", "multichannel", "listing_writer",
            "smart_automation", "workflow_builder", "reengagement",
            "lead_lifecycle", "campaign_analytics", "memory", "monitoring",
            # Claude AI Services (Phase 2)
            "claude_agent", "claude_semantic_analyzer", "qualification_orchestrator",
            # Business Intelligence Services
            "business_metrics"
        ]
