"""Service registry for the Streamlit demo app.

Handles service imports, fallback mocks, cache warming, and service initialization.
"""

import datetime
import json
import sys
from pathlib import Path

import streamlit as st

from ghl_real_estate_ai.streamlit_demo.config.page_config import ASYNC_UTILS_AVAILABLE, DEMO_MODE, run_async

# Base path for ghl_real_estate_ai package
_GHL_ROOT = Path(__file__).resolve().parent.parent.parent


class MockService:
    """Fallback mock service for demo purposes."""

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, name):
        def method(*args, **kwargs):
            return {}

        return method


# Add project root and ghl_real_estate_ai to sys.path
project_root = _GHL_ROOT.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

ghl_root = _GHL_ROOT
if str(ghl_root) not in sys.path:
    sys.path.insert(0, str(ghl_root))

demo_root = ghl_root / "streamlit_demo"
if str(demo_root) not in sys.path:
    sys.path.insert(0, str(demo_root))


# Import services - using proper absolute paths
try:
    import importlib

    import ghl_real_estate_ai.services.ai_predictive_lead_scoring
    import ghl_real_estate_ai.services.lead_scorer

    # Reloading for development/demo purposes
    importlib.reload(ghl_real_estate_ai.services.lead_scorer)
    importlib.reload(ghl_real_estate_ai.services.ai_predictive_lead_scoring)

    from ghl_real_estate_ai.services.ai_predictive_lead_scoring import PredictiveLeadScorer
    from ghl_real_estate_ai.services.lead_scorer import LeadScorer

    print(f"DEBUG: LeadScorer RELOADED from: {ghl_real_estate_ai.services.lead_scorer.__file__}")

    from ghl_real_estate_ai.services.agent_coaching import AgentCoachingService
    from ghl_real_estate_ai.services.ai_content_personalization import AIContentPersonalizationService
    from ghl_real_estate_ai.services.ai_smart_segmentation import AISmartSegmentationService
    from ghl_real_estate_ai.services.auto_followup_sequences import AutoFollowUpSequences
    from ghl_real_estate_ai.services.churn_integration_service import ChurnIntegrationService
    from ghl_real_estate_ai.services.claude_assistant_optimized import ClaudeAssistantOptimized
    from ghl_real_estate_ai.services.claude_executive_intelligence import get_executive_intelligence_service
    from ghl_real_estate_ai.services.commission_calculator import CommissionCalculator, CommissionType, DealStage
    from ghl_real_estate_ai.services.competitive_benchmarking import BenchmarkingEngine
    from ghl_real_estate_ai.services.deal_closer_ai import DealCloserAI
    from ghl_real_estate_ai.services.executive_dashboard import ExecutiveDashboardService
    from ghl_real_estate_ai.services.lead_swarm_service import get_lead_swarm_service
    from ghl_real_estate_ai.services.live_feed import LiveFeedService
    from ghl_real_estate_ai.services.meeting_prep_assistant import MeetingPrepAssistant, MeetingType
    from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
    from ghl_real_estate_ai.services.quality_assurance import QualityAssuranceEngine
    from ghl_real_estate_ai.services.reengagement_engine import ReengagementEngine, ReengagementTrigger
    from ghl_real_estate_ai.services.revenue_attribution import RevenueAttributionEngine
    from ghl_real_estate_ai.services.smart_document_generator import DocumentType, SmartDocumentGenerator
    from ghl_real_estate_ai.services.workflow_marketplace import WorkflowMarketplaceService

    # Initialize OPTIMIZED Claude Assistant (75% faster responses)
    if DEMO_MODE:
        claude = MockService()
    else:
        claude = ClaudeAssistantOptimized()

    # PERFORMANCE OPTIMIZATION: Initialize cache warming service
    if not DEMO_MODE:
        from ghl_real_estate_ai.services.performance_optimization_service import get_performance_service

        performance_service = get_performance_service()

    # Import Claude Platform Companion
    try:
        from ghl_real_estate_ai.services.claude_platform_companion import get_claude_platform_companion

        claude_companion = get_claude_platform_companion()
        CLAUDE_COMPANION_AVAILABLE = True
    except ImportError as e:
        print(f"Claude Platform Companion not available: {e}")
        CLAUDE_COMPANION_AVAILABLE = False
        claude_companion = None

    # Enhanced services imports
    try:
        from ghl_real_estate_ai.services.enhanced_lead_scorer import EnhancedLeadScorer

        ENHANCED_LEAD_SCORER_AVAILABLE = True
    except ImportError:
        print("Enhanced Lead Scorer not available")
        ENHANCED_LEAD_SCORER_AVAILABLE = False

    try:
        from ghl_real_estate_ai.services.enhanced_property_matcher import EnhancedPropertyMatcher

        ENHANCED_PROPERTY_MATCHER_AVAILABLE = True
    except ImportError:
        print("Enhanced Property Matcher not available")
        ENHANCED_PROPERTY_MATCHER_AVAILABLE = False

    try:
        from ghl_real_estate_ai.services.churn_prediction_engine import ChurnPredictionEngine

        CHURN_PREDICTION_ENGINE_AVAILABLE = True
    except ImportError:
        print("Churn Prediction Engine not available")
        CHURN_PREDICTION_ENGINE_AVAILABLE = False

    # Component Imports
    from ghl_real_estate_ai.streamlit_demo.components.agent_os import render_agent_os_tab
    from ghl_real_estate_ai.streamlit_demo.components.ai_training_feedback import render_rlhf_loop
    from ghl_real_estate_ai.streamlit_demo.components.automation_studio import AutomationStudioHub
    from ghl_real_estate_ai.streamlit_demo.components.billing_dashboard import show as render_billing_dashboard
    from ghl_real_estate_ai.streamlit_demo.components.buyer_journey import (
        render_buyer_analytics,
        render_buyer_dashboard,
        render_buyer_journey_hub,
    )
    from ghl_real_estate_ai.streamlit_demo.components.calculators import render_revenue_funnel, render_roi_calculator
    from ghl_real_estate_ai.streamlit_demo.components.churn_early_warning_dashboard import ChurnEarlyWarningDashboard
    from ghl_real_estate_ai.streamlit_demo.components.claude_cost_tracking_dashboard import (
        render_claude_cost_tracking_dashboard,
    )
    from ghl_real_estate_ai.streamlit_demo.components.claude_panel import render_claude_assistant
    from ghl_real_estate_ai.streamlit_demo.components.executive_hub import render_executive_hub
    from ghl_real_estate_ai.streamlit_demo.components.financing_calculator import render_financing_calculator
    from ghl_real_estate_ai.streamlit_demo.components.floating_claude import render_floating_claude
    from ghl_real_estate_ai.streamlit_demo.components.global_header import render_global_header
    from ghl_real_estate_ai.streamlit_demo.components.lead_intelligence_hub import render_lead_intelligence_hub
    from ghl_real_estate_ai.streamlit_demo.components.listing_architect import render_listing_architect
    from ghl_real_estate_ai.streamlit_demo.components.marketplace_management import render_marketplace_management
    from ghl_real_estate_ai.streamlit_demo.components.neighborhood_intelligence import render_neighborhood_explorer
    from ghl_real_estate_ai.streamlit_demo.components.neural_uplink import render_neural_uplink
    from ghl_real_estate_ai.streamlit_demo.components.ops_optimization import OpsOptimizationHub
    from ghl_real_estate_ai.streamlit_demo.components.proactive_intelligence_dashboard import (
        render_proactive_alerts_widget,
        render_proactive_intelligence_dashboard,
    )
    from ghl_real_estate_ai.streamlit_demo.components.project_copilot import render_project_copilot
    from ghl_real_estate_ai.streamlit_demo.components.property_swipe import render_property_swipe
    from ghl_real_estate_ai.streamlit_demo.components.property_valuation import render_property_valuation_engine
    from ghl_real_estate_ai.streamlit_demo.components.sales_copilot import SalesCopilotHub
    from ghl_real_estate_ai.streamlit_demo.components.security_governance import render_security_governance
    from ghl_real_estate_ai.streamlit_demo.components.seller_journey import (
        render_marketing_campaign_dashboard,
        render_seller_analytics,
        render_seller_communication_portal,
        render_seller_journey_hub,
        render_seller_prep_checklist,
        render_transaction_timeline,
    )
    from ghl_real_estate_ai.streamlit_demo.components.swarm_visualizer import render_swarm_visualizer
    from ghl_real_estate_ai.streamlit_demo.components.ui_elements import render_action_card, render_insight_card
    from ghl_real_estate_ai.streamlit_demo.components.voice_claude_interface import (
        add_voice_interface_css,
        render_voice_claude_interface,
        render_voice_settings,
    )
    from ghl_real_estate_ai.streamlit_demo.components.voice_intelligence import render_voice_intelligence
    from ghl_real_estate_ai.streamlit_demo.components.workflow_designer import render_workflow_designer
    from ghl_real_estate_ai.streamlit_demo.realtime_dashboard_integration import render_realtime_intelligence_dashboard

    SERVICES_LOADED = True
except ImportError as e:
    print(f"DEBUG IMPORT ERROR: {e}")
    st.error(f"Error importing services: {e}")
    st.error("Please ensure you're running from the correct directory")
    SERVICES_LOADED = False
    # Set defaults for enhanced service availability flags
    ENHANCED_LEAD_SCORER_AVAILABLE = False
    ENHANCED_PROPERTY_MATCHER_AVAILABLE = False
    CHURN_PREDICTION_ENGINE_AVAILABLE = False
    CLAUDE_COMPANION_AVAILABLE = False
    claude_companion = None

    # Define fallback mock classes for all required services
    LeadScorer = MockService
    AISmartSegmentationService = MockService
    PredictiveLeadScorer = MockService
    AIContentPersonalizationService = MockService
    DealCloserAI = MockService
    CommissionCalculator = MockService
    MeetingPrepAssistant = MockService
    ExecutiveDashboardService = MockService
    SmartDocumentGenerator = MockService
    QualityAssuranceEngine = MockService
    RevenueAttributionEngine = MockService
    BenchmarkingEngine = MockService
    AgentCoachingService = MockService
    AutoFollowUpSequences = MockService
    WorkflowMarketplaceService = MockService
    PropertyMatcher = MockService
    ReengagementEngine = MockService
    ChurnIntegrationService = MockService
    ClaudeAssistantOptimized = MockService
    claude = MockService()


def load_mock_data():
    """Load mock analytics data from JSON file."""
    data_path = _GHL_ROOT / "data" / "mock_analytics.json"
    if data_path.exists():
        with open(data_path) as f:
            return json.load(f)
    return {}


def get_runtime_transparency_status() -> dict:
    """Expose runtime mode details for buyer-facing transparency badges."""
    mock_data_path = _GHL_ROOT / "data" / "mock_analytics.json"
    uses_mock_services = DEMO_MODE or not SERVICES_LOADED

    return {
        "demo_mode": DEMO_MODE,
        "services_loaded": SERVICES_LOADED,
        "uses_mock_services": uses_mock_services,
        "mock_data_available": mock_data_path.exists(),
        "mock_data_path": str(mock_data_path),
        "generated_at": datetime.datetime.now().isoformat(),
    }


# ============================================================================
# PERFORMANCE OPTIMIZATION: Cache Warming & Service Initialization
# ============================================================================


@st.cache_data(ttl=1800)  # Cache for 30 minutes
def warm_critical_data():
    """Pre-load critical data to eliminate cold start delays."""
    import time

    start_time = time.time()

    warmed_data = {}

    try:
        # Warm mock data
        warmed_data["mock_analytics"] = load_mock_data()

        # Warm common lead data structures
        warmed_data["sample_leads"] = [
            {
                "name": "Sarah Chen",
                "email": "sarah.chen@email.com",
                "budget": 450000,
                "location": "Austin",
                "preferences": {"bedrooms": 3, "bathrooms": 2, "property_type": "Single Family"},
            },
            {
                "name": "David Kim",
                "email": "david.kim@email.com",
                "budget": 350000,
                "location": "Austin",
                "preferences": {"bedrooms": 2, "bathrooms": 2, "property_type": "Condo"},
            },
        ]

        # Warm property data
        warmed_data["sample_properties"] = [
            {
                "address": "123 Austin St",
                "price": 425000,
                "bedrooms": 3,
                "bathrooms": 2,
                "property_type": "Single Family",
                "neighborhood": "South Austin",
            }
        ]

        # Warm analytics time series data
        warmed_data["analytics_trends"] = {
            "revenue": [100000, 120000, 135000, 145000, 160000],
            "conversion_rates": [0.15, 0.18, 0.22, 0.25, 0.28],
            "lead_velocity": [25, 30, 35, 40, 45],
        }

        end_time = time.time()
        warmed_data["cache_warming_time"] = round((end_time - start_time) * 1000, 2)  # ms

        return warmed_data

    except Exception as e:
        st.warning(f"Cache warming encountered an issue: {e}")
        return {"error": str(e), "cache_warming_time": 0}


@st.cache_resource(ttl=3600)  # Cache for 1 hour
def initialize_claude_assistant_cache():
    """Initialize and warm Claude Assistant semantic cache."""
    try:
        from ghl_real_estate_ai.services.claude_assistant_optimized import ClaudeAssistantOptimized

        assistant = ClaudeAssistantOptimized(context_type="dashboard")

        # Warm cache with common queries
        common_queries = [
            "What is the lead score for this contact?",
            "Show me property recommendations",
            "Analyze this lead's conversion probability",
            "What is the market trend analysis?",
            "Generate follow-up email",
            "Calculate commission for this deal",
            "Show revenue forecasting",
            "What are the top performing agents?",
            "Display property matching results",
            "Analyze churn risk factors",
        ]

        # Asynchronously warm the cache
        try:
            if hasattr(assistant, "semantic_cache"):
                if ASYNC_UTILS_AVAILABLE:
                    # Use safe async handling
                    warmed = run_async(assistant.semantic_cache.warm_cache(common_queries))
                else:
                    # Fallback: skip cache warming for stability
                    warmed = 0
                return {"assistant": assistant, "warmed_queries": warmed}
            else:
                return {"assistant": assistant, "warmed_queries": 0}
        except Exception as cache_error:
            # Return assistant even if cache warming fails
            return {"assistant": assistant, "warmed_queries": 0, "cache_error": str(cache_error)}

    except Exception as e:
        st.warning(f"Claude Assistant cache initialization failed: {e}")
        return {"error": str(e), "warmed_queries": 0}


@st.cache_data(ttl=900)  # Cache for 15 minutes
def preload_dashboard_components():
    """Pre-load dashboard component data for instant rendering."""

    components_data = {}

    try:
        # Pre-generate common chart configurations
        components_data["chart_configs"] = {
            "revenue_trend": {"type": "line", "color": "#6366F1", "height": 300, "data_points": 30},
            "conversion_funnel": {"type": "funnel", "colors": ["#10B981", "#F59E0B", "#EF4444"], "height": 250},
            "lead_distribution": {"type": "pie", "colors": ["#8B5CF6", "#06B6D4", "#84CC16"], "height": 200},
        }

        # Pre-load dashboard metrics
        components_data["kpi_metrics"] = {
            "total_revenue": {"value": 2150000, "change": 0.12, "format": "currency"},
            "conversion_rate": {"value": 0.23, "change": 0.05, "format": "percent"},
            "active_leads": {"value": 847, "change": 0.08, "format": "number"},
            "avg_deal_size": {"value": 425000, "change": -0.02, "format": "currency"},
        }

        # WS-6: pre-load Jorge KPI panel definitions and snapshot for dashboard surfaces.
        try:
            from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector

            ws6_collector = BotMetricsCollector()
            components_data["jorge_ws6"] = {
                "definitions": ws6_collector.get_dashboard_definitions(),
                "snapshot": ws6_collector.get_dashboard_kpi_snapshot(),
            }
        except Exception as ws6_error:
            components_data["jorge_ws6"] = {"available": False, "error": str(ws6_error)}

        # Pre-load navigation state
        components_data["navigation"] = {
            "available_hubs": [
                "Executive Command Center",
                "Lead Intelligence Hub",
                "Property Matching Engine",
                "Revenue Analytics Hub",
                "Market Intelligence Center",
            ],
            "default_hub": "Executive Command Center",
        }

        return components_data

    except Exception as e:
        st.warning(f"Dashboard preloading failed: {e}")
        return {"error": str(e)}


@st.cache_data(ttl=1800, show_spinner="Warming demo cache for instant performance...")
def warm_demo_cache_comprehensive():
    """
    PERFORMANCE OPTIMIZATION: Pre-warm all critical caches for instant client demos.
    This eliminates cold start delays and ensures 200-400ms response times.

    Returns:
        Dict containing warmed cache status and timing metrics
    """
    import time

    start_time = time.time()

    warmed_status = {"timestamp": datetime.datetime.now().isoformat(), "components_warmed": [], "errors": []}

    try:
        # 1. Warm common analytics data
        try:
            analytics_data = warm_critical_data()
            warmed_status["components_warmed"].append("analytics_data")
            warmed_status["analytics_cache_time"] = analytics_data.get("cache_warming_time", 0)
        except Exception as e:
            warmed_status["errors"].append(f"analytics: {str(e)}")

        # 2. Warm Claude Assistant cache
        try:
            claude_cache = initialize_claude_assistant_cache()
            warmed_status["components_warmed"].append("claude_assistant")
            warmed_status["claude_queries_warmed"] = claude_cache.get("warmed_queries", 0)
        except Exception as e:
            warmed_status["errors"].append(f"claude_assistant: {str(e)}")

        # 3. Preload dashboard components
        try:
            preload_dashboard_components()
            warmed_status["components_warmed"].append("dashboard_components")
        except Exception as e:
            warmed_status["errors"].append(f"dashboard_components: {str(e)}")

        # Calculate total warming time
        end_time = time.time()
        warmed_status["total_warming_time_ms"] = round((end_time - start_time) * 1000, 2)
        warmed_status["success"] = len(warmed_status["errors"]) == 0

        return warmed_status

    except Exception as e:
        warmed_status["errors"].append(f"critical_error: {str(e)}")
        warmed_status["success"] = False
        return warmed_status


@st.cache_resource(ttl=3600, show_spinner=True)  # Cache services for 1 hour, show loading
def get_services(market="Austin"):
    listings_file = "property_listings.json" if market == "Austin" else "property_listings_rancho.json"
    listings_path = _GHL_ROOT / "data" / "knowledge_base" / listings_file

    # Safe import of orchestrator services with fallback
    if DEMO_MODE:
        claude_orchestrator = MockService()
        claude_automation = MockService()
    else:
        try:
            from ghl_real_estate_ai.services.claude_automation_engine import ClaudeAutomationEngine
            from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

            claude_orchestrator = get_claude_orchestrator()
            claude_automation = ClaudeAutomationEngine()
        except ImportError as e:
            print(f"Warning: Claude orchestrator services not available: {e}")
            claude_orchestrator = MockService()
            claude_automation = MockService()

    services_dict = {
        "lead_scorer": LeadScorer(),
        "segmentation": AISmartSegmentationService(),
        "predictive_scorer": PredictiveLeadScorer(),
        "personalization": AIContentPersonalizationService(),
        "deal_closer": DealCloserAI(),
        "commission_calc": CommissionCalculator(),
        "meeting_prep": MeetingPrepAssistant(),
        "executive": ExecutiveDashboardService(),
        "doc_gen": SmartDocumentGenerator(),
        "qa": QualityAssuranceEngine(),
        "revenue": RevenueAttributionEngine(),
        "benchmarking": BenchmarkingEngine(),
        "coaching": AgentCoachingService(),
        "sequences": AutoFollowUpSequences(),
        "marketplace": WorkflowMarketplaceService(),
        "property_matcher": PropertyMatcher(listings_path=str(listings_path)),
        "claude_orchestrator": claude_orchestrator,
        "claude_automation": claude_automation,
        "churn_service": ChurnIntegrationService(
            memory_service=None,  # Would be injected with actual services
            lifecycle_tracker=None,
            behavioral_engine=None,
            lead_scorer=None,
            reengagement_engine=ReengagementEngine(),
            ghl_service=None,
        ),
    }

    # Add enhanced services if available
    if ENHANCED_LEAD_SCORER_AVAILABLE:
        try:
            services_dict["enhanced_lead_scorer"] = EnhancedLeadScorer()
            st.success("Enhanced Lead Scorer initialized successfully")
        except Exception as e:
            st.error(f"Failed to initialize Enhanced Lead Scorer: {e}")
            services_dict["enhanced_lead_scorer"] = MockService()  # Fallback

    if ENHANCED_PROPERTY_MATCHER_AVAILABLE:
        try:
            services_dict["enhanced_property_matcher"] = EnhancedPropertyMatcher(listings_path=str(listings_path))
            st.success("Enhanced Property Matcher initialized successfully")
        except Exception as e:
            st.error(f"Failed to initialize Enhanced Property Matcher: {e}")
            services_dict["enhanced_property_matcher"] = MockService()  # Fallback

    if CHURN_PREDICTION_ENGINE_AVAILABLE:
        try:
            # Initialize required services for ChurnPredictionEngine
            memory_service = MockService()  # Mock service for demo
            lifecycle_tracker = MockService()  # Mock service for demo
            behavioral_engine = MockService()  # Mock service for demo

            services_dict["churn_prediction"] = ChurnPredictionEngine(
                memory_service=memory_service,
                lifecycle_tracker=lifecycle_tracker,
                behavioral_engine=behavioral_engine,
                lead_scorer=services_dict["lead_scorer"],  # Use the actual lead scorer
            )
            st.success("Churn Prediction Engine initialized successfully")
        except Exception as e:
            st.error(f"Failed to initialize Churn Prediction Engine: {e}")
            services_dict["churn_prediction"] = MockService()  # Fallback

    return services_dict
