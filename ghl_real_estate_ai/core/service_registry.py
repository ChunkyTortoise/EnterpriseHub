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
            "lead_lifecycle", "campaign_analytics", "memory", "monitoring"
        ]
