
import sys
from pathlib import Path

project_root = Path.cwd()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("Checking imports...")
try:
    from ghl_real_estate_ai.services.lead_scorer import LeadScorer
    from ghl_real_estate_ai.services.ai_smart_segmentation import AISmartSegmentationService
    from ghl_real_estate_ai.services.ai_predictive_lead_scoring import PredictiveLeadScorer
    from ghl_real_estate_ai.services.ai_content_personalization import AIContentPersonalizationService
    from ghl_real_estate_ai.services.deal_closer_ai import DealCloserAI
    from ghl_real_estate_ai.services.commission_calculator import CommissionCalculator
    from ghl_real_estate_ai.services.meeting_prep_assistant import MeetingPrepAssistant
    from ghl_real_estate_ai.services.executive_dashboard import ExecutiveDashboardService
    from ghl_real_estate_ai.services.quality_assurance import QualityAssuranceEngine
    from ghl_real_estate_ai.services.revenue_attribution import RevenueAttributionEngine
    from ghl_real_estate_ai.services.competitive_benchmarking import BenchmarkingEngine
    from ghl_real_estate_ai.services.agent_coaching import AgentCoachingService
    from ghl_real_estate_ai.services.smart_document_generator import SmartDocumentGenerator
    from ghl_real_estate_ai.services.live_feed import LiveFeedService
    from ghl_real_estate_ai.services.workflow_marketplace import WorkflowMarketplaceService
    from ghl_real_estate_ai.services.auto_followup_sequences import AutoFollowUpSequences
    from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
    from ghl_real_estate_ai.services.reengagement_engine import ReengagementEngine
    from ghl_real_estate_ai.services.churn_integration_service import ChurnIntegrationService
    from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
    print("Core services imported successfully.")
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Other error: {e}")

try:
    from ghl_real_estate_ai.streamlit_demo.components.performance_dashboard import render_performance_dashboard
    print("Streamlit components imported successfully.")
except ImportError as e:
    print(f"Component import error: {e}")
