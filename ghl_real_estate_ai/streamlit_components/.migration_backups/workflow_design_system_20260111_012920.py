"""
User-Friendly Workflow Design System for EnterpriseHub Real Estate AI
====================================================================

Comprehensive workflow design framework providing:
- Intuitive multi-step process flows
- Visual workflow builders
- Guided user journeys
- Error prevention and recovery
- Progress tracking and status indicators
- Context-aware help and tooltips
- Smart form validation
- Workflow automation setup

Designed to make complex operations accessible to users of all skill levels.
"""

# ============================================================================
# MIGRATION NOTES (Automated Migration - 2026-01-11)
# ============================================================================
# Changes Applied:
# # - Added base class: EnterpriseDashboardComponent
# - Added unified design system import check
# - Consider replacing inline styled divs with enterprise_card
# - Consider using enterprise_metric for consistent styling
#
# This component has been migrated to enterprise standards.
# See migration documentation for details.
# ============================================================================



import streamlit as st

# === ENTERPRISE BASE IMPORTS ===
from .enhanced_enterprise_base import (
    EnhancedEnterpriseComponent,
    EnterpriseDashboardComponent,
    EnterpriseDataComponent,
    ComponentMetrics,
    ComponentState
)
from .enterprise_theme_system import (
    EnterpriseThemeManager,
    ThemeVariant,
    ComponentType,
    inject_enterprise_theme,
    create_enterprise_card,
    create_enterprise_metric,
    create_enterprise_alert
)


# === UNIFIED DESIGN SYSTEM ===
try:
    from ..design_system import (
        enterprise_metric,
        enterprise_card,
        enterprise_badge,
        enterprise_progress_ring,
        enterprise_status_indicator,
        enterprise_kpi_grid,
        enterprise_section_header,
        apply_plotly_theme,
        ENTERPRISE_COLORS
    )
    UNIFIED_DESIGN_SYSTEM_AVAILABLE = True
except ImportError:
    UNIFIED_DESIGN_SYSTEM_AVAILABLE = False
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import time


class WorkflowStepType(Enum):
    """Types of workflow steps"""
    INPUT = "input"
    SELECTION = "selection"
    CONFIRMATION = "confirmation"
    PROCESSING = "processing"
    COMPLETION = "completion"
    BRANCHING = "branching"
    VALIDATION = "validation"


class WorkflowStatus(Enum):
    """Workflow execution status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class WorkflowStep:
    """Individual workflow step configuration"""
    id: str
    title: str
    description: str
    type: WorkflowStepType
    required: bool = True
    component: Optional[Callable] = None
    validation: Optional[Callable] = None
    next_step: Optional[str] = None
    error_step: Optional[str] = None
    help_text: Optional[str] = None
    estimated_time: Optional[int] = None  # in seconds
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class WorkflowDefinition:
    """Complete workflow definition"""
    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    start_step: str
    category: str
    difficulty: str  # "beginner", "intermediate", "advanced"
    estimated_duration: int  # in minutes
    required_permissions: List[str] = field(default_factory=list)


class WorkflowDesignSystem(EnterpriseDashboardComponent):
    """Advanced workflow design and execution system"""

    def __init__(self):
        """Initialize workflow design system"""
        self.workflows = self._initialize_predefined_workflows()
        self.current_workflow = None
        self.workflow_state = {}
        self.step_history = []

        # Initialize session state
        self._initialize_session_state()

        # Inject workflow CSS
        self._inject_workflow_css()

    def _initialize_session_state(self):
        """Initialize workflow session state"""
        if 'workflow_data' not in st.session_state:
            st.session_state.workflow_data = {}

        if 'current_step' not in st.session_state:
            st.session_state.current_step = None

        if 'workflow_progress' not in st.session_state:
            st.session_state.workflow_progress = {}

        if 'workflow_errors' not in st.session_state:
            st.session_state.workflow_errors = {}

    def _inject_workflow_css(self):
        """Inject workflow-specific CSS"""
        st.markdown("""
        <style>
        /* Workflow Design System Styles */
        .workflow-container {
            background: #f9fafb;
            min-height: 100vh;
            padding: 20px;
        }

        .workflow-header {
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            margin-bottom: 24px;
            border-left: 4px solid #3b82f6;
        }

        .workflow-title {
            font-size: 24px;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 8px;
        }

        .workflow-description {
            color: #6b7280;
            font-size: 16px;
            line-height: 1.5;
        }

        .workflow-meta {
            display: flex;
            gap: 16px;
            margin-top: 16px;
            flex-wrap: wrap;
        }

        .workflow-meta-item {
            display: flex;
            align-items: center;
            gap: 6px;
            background: #f3f4f6;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 14px;
            color: #374151;
        }

        /* Progress indicators */
        .progress-container {
            background: white;
            padding: 20px 24px;
            border-radius: 12px;
            margin-bottom: 24px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .progress-title {
            font-size: 16px;
            font-weight: 600;
            color: #1f2937;
        }

        .progress-percentage {
            color: #3b82f6;
            font-weight: 600;
            font-size: 14px;
        }

        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e5e7eb;
            border-radius: 4px;
            overflow: hidden;
            margin-bottom: 16px;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3b82f6, #1d4ed8);
            border-radius: 4px;
            transition: width 300ms ease;
        }

        .step-indicators {
            display: flex;
            gap: 12px;
            overflow-x: auto;
            padding-bottom: 4px;
        }

        .step-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
            white-space: nowrap;
            min-width: 120px;
        }

        .step-dot {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: 600;
            color: white;
            flex-shrink: 0;
        }

        .step-dot.completed {
            background: #10b981;
        }

        .step-dot.current {
            background: #3b82f6;
        }

        .step-dot.pending {
            background: #d1d5db;
            color: #6b7280;
        }

        .step-dot.error {
            background: #ef4444;
        }

        .step-label {
            font-size: 13px;
            color: #374151;
            font-weight: 500;
        }

        /* Step content container */
        .step-container {
            background: white;
            padding: 32px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            margin-bottom: 24px;
        }

        .step-header {
            margin-bottom: 24px;
            padding-bottom: 16px;
            border-bottom: 1px solid #e5e7eb;
        }

        .step-title {
            font-size: 20px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 8px;
        }

        .step-description {
            color: #6b7280;
            font-size: 16px;
            line-height: 1.5;
        }

        .step-help {
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
        }

        .step-help-title {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            color: #0369a1;
            margin-bottom: 8px;
        }

        .step-help-content {
            color: #0c4a6e;
            font-size: 14px;
            line-height: 1.5;
        }

        /* Form elements */
        .workflow-form {
            margin-bottom: 24px;
        }

        .form-group {
            margin-bottom: 24px;
        }

        .form-label {
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 8px;
            font-size: 14px;
        }

        .form-label.required::after {
            content: "*";
            color: #ef4444;
        }

        .form-description {
            color: #6b7280;
            font-size: 13px;
            margin-bottom: 12px;
            line-height: 1.4;
        }

        .form-error {
            color: #ef4444;
            font-size: 13px;
            margin-top: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .form-success {
            color: #10b981;
            font-size: 13px;
            margin-top: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* Navigation controls */
        .workflow-navigation {
            background: white;
            padding: 20px 24px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 16px;
        }

        .nav-button {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 150ms ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .nav-button:hover {
            background: #2563eb;
            transform: translateY(-1px);
        }

        .nav-button.secondary {
            background: #f3f4f6;
            color: #374151;
        }

        .nav-button.secondary:hover {
            background: #e5e7eb;
        }

        .nav-button:disabled {
            background: #d1d5db;
            color: #9ca3af;
            cursor: not-allowed;
            transform: none;
        }

        .nav-center {
            flex: 1;
            display: flex;
            justify-content: center;
            gap: 12px;
        }

        .save-draft-btn {
            background: transparent;
            border: 1px solid #d1d5db;
            color: #6b7280;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
        }

        /* Status indicators */
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }

        .status-badge.completed {
            background: #dcfce7;
            color: #166534;
        }

        .status-badge.in-progress {
            background: #dbeafe;
            color: #1e40af;
        }

        .status-badge.error {
            background: #fef2f2;
            color: #dc2626;
        }

        .status-badge.pending {
            background: #f3f4f6;
            color: #6b7280;
        }

        /* Smart validation */
        .validation-container {
            background: #fefce8;
            border: 1px solid #fde047;
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
        }

        .validation-title {
            font-weight: 600;
            color: #a16207;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .validation-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }

        .validation-item {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #a16207;
            font-size: 14px;
            margin-bottom: 4px;
        }

        .validation-item.valid {
            color: #166534;
        }

        /* Mobile responsive */
        @media (max-width: 768px) {
            .workflow-container {
                padding: 12px;
            }

            .workflow-header,
            .progress-container,
            .step-container,
            .workflow-navigation {
                padding: 16px;
            }

            .workflow-meta {
                flex-direction: column;
                gap: 8px;
            }

            .step-indicators {
                flex-direction: column;
                gap: 8px;
            }

            .workflow-navigation {
                flex-direction: column;
                gap: 12px;
            }

            .nav-center {
                order: 3;
                width: 100%;
            }

            .nav-button {
                width: 100%;
                justify-content: center;
            }
        }

        /* Workflow builder styles */
        .workflow-builder {
            display: grid;
            grid-template-columns: 250px 1fr;
            gap: 24px;
            height: 100vh;
        }

        .workflow-palette {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            overflow-y: auto;
        }

        .workflow-canvas {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
        }

        .step-block {
            background: #f8fafc;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 12px;
            cursor: grab;
            transition: all 150ms ease;
        }

        .step-block:hover {
            border-color: #3b82f6;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }

        .step-block.dragging {
            opacity: 0.5;
            cursor: grabbing;
        }
        </style>
        """, unsafe_allow_html=True)

    def _initialize_predefined_workflows(self) -> Dict[str, WorkflowDefinition]:
        """Initialize predefined workflows"""
        workflows = {}

        # Lead Qualification Workflow
        lead_qualification = WorkflowDefinition(
            id="lead_qualification",
            name="Lead Qualification Process",
            description="Complete lead qualification workflow with AI assistance",
            category="Lead Management",
            difficulty="beginner",
            estimated_duration=15,
            steps=[
                WorkflowStep(
                    id="contact_info",
                    title="Contact Information",
                    description="Gather essential contact details",
                    type=WorkflowStepType.INPUT,
                    help_text="Ensure all contact information is accurate for effective follow-up",
                    estimated_time=180
                ),
                WorkflowStep(
                    id="needs_assessment",
                    title="Needs Assessment",
                    description="Understand client property requirements",
                    type=WorkflowStepType.SELECTION,
                    help_text="Focus on must-have vs nice-to-have features",
                    estimated_time=300
                ),
                WorkflowStep(
                    id="budget_qualification",
                    title="Budget Qualification",
                    description="Determine financial capacity and timeline",
                    type=WorkflowStepType.INPUT,
                    help_text="Be tactful when discussing financial capacity",
                    estimated_time=240
                ),
                WorkflowStep(
                    id="ai_scoring",
                    title="AI Lead Scoring",
                    description="AI analyzes lead quality and recommendations",
                    type=WorkflowStepType.PROCESSING,
                    estimated_time=30
                ),
                WorkflowStep(
                    id="next_actions",
                    title="Next Actions",
                    description="Review AI recommendations and plan follow-up",
                    type=WorkflowStepType.CONFIRMATION,
                    estimated_time=120
                )
            ],
            start_step="contact_info"
        )

        # Property Matching Workflow
        property_matching = WorkflowDefinition(
            id="property_matching",
            name="AI Property Matching",
            description="Find perfect property matches using AI",
            category="Property Management",
            difficulty="intermediate",
            estimated_duration=20,
            steps=[
                WorkflowStep(
                    id="criteria_setup",
                    title="Search Criteria",
                    description="Define property search parameters",
                    type=WorkflowStepType.INPUT,
                    estimated_time=300
                ),
                WorkflowStep(
                    id="ai_search",
                    title="AI Property Search",
                    description="AI searches and scores matching properties",
                    type=WorkflowStepType.PROCESSING,
                    estimated_time=60
                ),
                WorkflowStep(
                    id="review_matches",
                    title="Review Matches",
                    description="Review AI-recommended properties",
                    type=WorkflowStepType.SELECTION,
                    estimated_time=600
                ),
                WorkflowStep(
                    id="client_presentation",
                    title="Client Presentation",
                    description="Prepare property presentation for client",
                    type=WorkflowStepType.CONFIRMATION,
                    estimated_time=240
                )
            ],
            start_step="criteria_setup"
        )

        # GHL Integration Setup
        ghl_integration = WorkflowDefinition(
            id="ghl_integration_setup",
            name="GoHighLevel Integration Setup",
            description="Configure AI integration with GoHighLevel CRM",
            category="System Configuration",
            difficulty="advanced",
            estimated_duration=45,
            required_permissions=["admin"],
            steps=[
                WorkflowStep(
                    id="api_configuration",
                    title="API Configuration",
                    description="Configure GoHighLevel API settings",
                    type=WorkflowStepType.INPUT,
                    help_text="Ensure API credentials have appropriate permissions",
                    estimated_time=600
                ),
                WorkflowStep(
                    id="webhook_setup",
                    title="Webhook Configuration",
                    description="Set up webhooks for real-time synchronization",
                    type=WorkflowStepType.INPUT,
                    estimated_time=480
                ),
                WorkflowStep(
                    id="field_mapping",
                    title="Field Mapping",
                    description="Map GHL fields to AI system fields",
                    type=WorkflowStepType.SELECTION,
                    estimated_time=900
                ),
                WorkflowStep(
                    id="test_connection",
                    title="Test Connection",
                    description="Verify integration is working correctly",
                    type=WorkflowStepType.PROCESSING,
                    estimated_time=120
                ),
                WorkflowStep(
                    id="automation_rules",
                    title="Automation Rules",
                    description="Configure AI automation rules",
                    type=WorkflowStepType.SELECTION,
                    estimated_time=600
                )
            ],
            start_step="api_configuration"
        )

        workflows[lead_qualification.id] = lead_qualification
        workflows[property_matching.id] = property_matching
        workflows[ghl_integration.id] = ghl_integration

        return workflows

    def render_workflow_selector(self) -> Optional[str]:
        """Render workflow selection interface"""
        st.markdown("""
        <div class="workflow-container">
            <div class="workflow-header">
                <div class="workflow-title">🔄 Workflow Center</div>
                <div class="workflow-description">
                    Choose a workflow to streamline your real estate AI operations
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Group workflows by category
        categories = {}
        for workflow in self.workflows.values():
            if workflow.category not in categories:
                categories[workflow.category] = []
            categories[workflow.category].append(workflow)

        selected_workflow = None

        for category, workflows in categories.items():
            st.markdown(f"### {category}")

            cols = st.columns(len(workflows))
            for i, workflow in enumerate(workflows):
                with cols[i]:
                    difficulty_colors = {
                        "beginner": "#10b981",
                        "intermediate": "#f59e0b",
                        "advanced": "#ef4444"
                    }

                    difficulty_color = difficulty_colors.get(workflow.difficulty, "#6b7280")

                    if st.button(
                        f"🚀 Start Workflow",
                        key=f"start_{workflow.id}",
                        use_container_width=True
                    ):
                        selected_workflow = workflow.id

                    st.markdown(f"""
                    <div style="
                        background: white;
                        padding: 20px;
                        border-radius: 12px;
                        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                        margin-bottom: 16px;
                        border-left: 4px solid {difficulty_color};
                    ">
                        <h4 style="margin: 0 0 8px 0; color: #1f2937;">{workflow.name}</h4>
                        <p style="color: #6b7280; font-size: 14px; margin: 0 0 16px 0;">
                            {workflow.description}
                        </p>
                        <div style="display: flex; gap: 12px; flex-wrap: wrap;">
                            <div style="
                                background: {difficulty_color};
                                color: white;
                                padding: 4px 8px;
                                border-radius: 12px;
                                font-size: 12px;
                                font-weight: 600;
                            ">
                                {workflow.difficulty.upper()}
                            </div>
                            <div style="
                                background: #f3f4f6;
                                color: #374151;
                                padding: 4px 8px;
                                border-radius: 12px;
                                font-size: 12px;
                                font-weight: 600;
                            ">
                                ⏱️ {workflow.estimated_duration}m
                            </div>
                            <div style="
                                background: #f3f4f6;
                                color: #374151;
                                padding: 4px 8px;
                                border-radius: 12px;
                                font-size: 12px;
                                font-weight: 600;
                            ">
                                📋 {len(workflow.steps)} steps
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        return selected_workflow

    def execute_workflow(self, workflow_id: str) -> None:
        """Execute a workflow with guided steps"""
        if workflow_id not in self.workflows:
            st.error(f"Workflow '{workflow_id}' not found")
            return

        workflow = self.workflows[workflow_id]
        self.current_workflow = workflow

        # Initialize workflow state
        if f"workflow_{workflow_id}" not in st.session_state:
            st.session_state[f"workflow_{workflow_id}"] = {
                "current_step": workflow.start_step,
                "completed_steps": [],
                "step_data": {},
                "status": WorkflowStatus.IN_PROGRESS,
                "start_time": datetime.now()
            }

        workflow_state = st.session_state[f"workflow_{workflow_id}"]

        # Render workflow header
        self._render_workflow_header(workflow)

        # Render progress indicator
        self._render_workflow_progress(workflow, workflow_state)

        # Find current step
        current_step = self._find_step(workflow, workflow_state["current_step"])
        if not current_step:
            st.error("Invalid workflow step")
            return

        # Render current step
        self._render_workflow_step(workflow, current_step, workflow_state)

        # Render navigation
        self._render_workflow_navigation(workflow, current_step, workflow_state)

    def _render_workflow_header(self, workflow: WorkflowDefinition) -> None:
        """Render workflow header"""
        st.markdown(f"""
        <div class="workflow-header">
            <div class="workflow-title">{workflow.name}</div>
            <div class="workflow-description">{workflow.description}</div>
            <div class="workflow-meta">
                <div class="workflow-meta-item">
                    📋 {len(workflow.steps)} Steps
                </div>
                <div class="workflow-meta-item">
                    ⏱️ ~{workflow.estimated_duration} minutes
                </div>
                <div class="workflow-meta-item">
                    🎯 {workflow.difficulty.title()}
                </div>
                <div class="workflow-meta-item">
                    📁 {workflow.category}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def _render_workflow_progress(self, workflow: WorkflowDefinition, state: Dict[str, Any]) -> None:
        """Render workflow progress indicator"""
        completed_count = len(state["completed_steps"])
        total_steps = len(workflow.steps)
        progress_percentage = int((completed_count / total_steps) * 100)

        st.markdown(f"""
        <div class="progress-container">
            <div class="progress-header">
                <div class="progress-title">Progress</div>
                <div class="progress-percentage">{progress_percentage}% Complete</div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {progress_percentage}%"></div>
            </div>
            <div class="step-indicators">
        """, unsafe_allow_html=True)

        for i, step in enumerate(workflow.steps):
            if step.id in state["completed_steps"]:
                dot_class = "completed"
                icon = "✓"
            elif step.id == state["current_step"]:
                dot_class = "current"
                icon = str(i + 1)
            else:
                dot_class = "pending"
                icon = str(i + 1)

            st.markdown(f"""
                <div class="step-indicator">
                    <div class="step-dot {dot_class}">{icon}</div>
                    <div class="step-label">{step.title}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("""
            </div>
        </div>
        """, unsafe_allow_html=True)

    def _render_workflow_step(self, workflow: WorkflowDefinition,
                            step: WorkflowStep, state: Dict[str, Any]) -> None:
        """Render current workflow step"""
        st.markdown(f"""
        <div class="step-container">
            <div class="step-header">
                <div class="step-title">{step.title}</div>
                <div class="step-description">{step.description}</div>
            </div>
        """, unsafe_allow_html=True)

        # Render help text if available
        if step.help_text:
            st.markdown(f"""
            <div class="step-help">
                <div class="step-help-title">
                    💡 Helpful Tip
                </div>
                <div class="step-help-content">
                    {step.help_text}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Render step content based on type
        if step.type == WorkflowStepType.INPUT:
            self._render_input_step(step, state)
        elif step.type == WorkflowStepType.SELECTION:
            self._render_selection_step(step, state)
        elif step.type == WorkflowStepType.CONFIRMATION:
            self._render_confirmation_step(step, state)
        elif step.type == WorkflowStepType.PROCESSING:
            self._render_processing_step(step, state)
        elif step.type == WorkflowStepType.COMPLETION:
            self._render_completion_step(step, state)

        st.markdown("</div>", unsafe_allow_html=True)

    def _render_input_step(self, step: WorkflowStep, state: Dict[str, Any]) -> None:
        """Render input step content"""
        st.markdown('<div class="workflow-form">', unsafe_allow_html=True)

        if step.id == "contact_info":
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("First Name *", key=f"{step.id}_first_name")
                st.text_input("Email *", key=f"{step.id}_email")
            with col2:
                st.text_input("Last Name *", key=f"{step.id}_last_name")
                st.text_input("Phone *", key=f"{step.id}_phone")

            st.text_area("Additional Notes", key=f"{step.id}_notes")

        elif step.id == "budget_qualification":
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox(
                    "Budget Range *",
                    ["Under $300K", "$300K - $500K", "$500K - $750K", "$750K - $1M", "Over $1M"],
                    key=f"{step.id}_budget"
                )
                st.selectbox(
                    "Timeline *",
                    ["ASAP", "1-3 months", "3-6 months", "6+ months", "Just browsing"],
                    key=f"{step.id}_timeline"
                )
            with col2:
                st.selectbox(
                    "Financing Status *",
                    ["Pre-approved", "Need pre-approval", "Cash buyer", "Exploring options"],
                    key=f"{step.id}_financing"
                )
                st.selectbox(
                    "Current Housing *",
                    ["First-time buyer", "Need to sell current", "Renting", "Other"],
                    key=f"{step.id}_current_housing"
                )

        elif step.id == "criteria_setup":
            col1, col2, col3 = st.columns(3)
            with col1:
                st.selectbox("Property Type", ["Single Family", "Condo", "Townhome", "Multi-family"], key=f"{step.id}_type")
                st.number_input("Min Bedrooms", min_value=1, max_value=10, value=2, key=f"{step.id}_min_beds")
            with col2:
                st.multiselect("Preferred Areas", ["Downtown", "Round Rock", "Pflugerville", "Cedar Park"], key=f"{step.id}_areas")
                st.number_input("Min Bathrooms", min_value=1, max_value=10, value=2, key=f"{step.id}_min_baths")
            with col3:
                st.slider("Max Commute (minutes)", 0, 60, 30, key=f"{step.id}_commute")
                st.multiselect("Must-have Features", ["Pool", "Garage", "Yard", "Updated Kitchen"], key=f"{step.id}_features")

        st.markdown('</div>', unsafe_allow_html=True)

    def _render_selection_step(self, step: WorkflowStep, state: Dict[str, Any]) -> None:
        """Render selection step content"""
        if step.id == "needs_assessment":
            st.markdown("### Property Requirements")

            col1, col2 = st.columns(2)
            with col1:
                st.multiselect(
                    "Property Types (select all that apply)",
                    ["Single Family Home", "Condominium", "Townhome", "Multi-family", "Land"],
                    key=f"{step.id}_property_types"
                )

                st.slider("Bedrooms", 1, 6, (2, 4), key=f"{step.id}_bedrooms")
                st.slider("Bathrooms", 1, 5, (2, 3), key=f"{step.id}_bathrooms")

            with col2:
                st.multiselect(
                    "Preferred Neighborhoods",
                    ["Downtown Austin", "Round Rock", "Pflugerville", "Cedar Park", "Leander"],
                    key=f"{step.id}_neighborhoods"
                )

                st.multiselect(
                    "Must-Have Features",
                    ["Swimming Pool", "2-car Garage", "Large Yard", "Updated Kitchen",
                     "Master Suite", "Home Office", "Walk-in Closets"],
                    key=f"{step.id}_must_have"
                )

        elif step.id == "review_matches":
            st.markdown("### AI-Recommended Properties")

            # Mock property matches
            properties = [
                {
                    "address": "123 Oak Street, Round Rock, TX",
                    "price": "$425,000",
                    "beds": 3,
                    "baths": 2.5,
                    "sqft": "1,850",
                    "score": 95,
                    "highlights": ["Pool", "Updated Kitchen", "Great Schools"]
                },
                {
                    "address": "456 Pine Avenue, Pflugerville, TX",
                    "price": "$380,000",
                    "beds": 4,
                    "baths": 3,
                    "sqft": "2,100",
                    "score": 88,
                    "highlights": ["Large Yard", "2-car Garage", "New HVAC"]
                }
            ]

            for i, prop in enumerate(properties):
                with st.expander(f"🏠 {prop['address']} - Match Score: {prop['score']}%", expanded=i==0):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Price", prop['price'])
                        st.metric("Bedrooms", prop['beds'])
                    with col2:
                        st.metric("Bathrooms", prop['baths'])
                        st.metric("Square Feet", prop['sqft'])
                    with col3:
                        st.markdown("**Highlights:**")
                        for highlight in prop['highlights']:
                            st.markdown(f"✓ {highlight}")

                    if st.checkbox(f"Include in presentation", key=f"{step.id}_include_{i}"):
                        st.success("Added to client presentation")

    def _render_confirmation_step(self, step: WorkflowStep, state: Dict[str, Any]) -> None:
        """Render confirmation step content"""
        if step.id == "next_actions":
            st.markdown("### AI Recommendations")

            # Mock AI recommendations
            recommendations = {
                "lead_score": 85,
                "priority": "High",
                "suggested_actions": [
                    "Schedule property viewing within 48 hours",
                    "Send pre-approval information",
                    "Follow up with similar properties"
                ],
                "timeline": "Contact within 2 hours for best results"
            }

            col1, col2 = st.columns(2)
            with col1:
                st.metric("AI Lead Score", f"{recommendations['lead_score']}/100")
                st.metric("Priority Level", recommendations['priority'])

            with col2:
                st.markdown("**Suggested Actions:**")
                for action in recommendations['suggested_actions']:
                    if st.checkbox(action, key=f"{step.id}_{action}"):
                        st.success("Action scheduled")

            st.info(f"⏰ **Timing:** {recommendations['timeline']}")

        elif step.id == "client_presentation":
            st.markdown("### Presentation Summary")
            st.markdown("Review the property presentation before sending to client:")

            # Mock presentation data
            st.markdown("""
            **Selected Properties:** 2 properties match your criteria
            **Total Presentation Value:** $805,000 combined
            **Next Steps:** Schedule viewings for this weekend
            """)

            if st.checkbox("Client presentation looks good"):
                st.success("Presentation approved - ready to send!")

    def _render_processing_step(self, step: WorkflowStep, state: Dict[str, Any]) -> None:
        """Render processing step content"""
        st.markdown("### 🤖 AI Processing")

        if step.id == "ai_scoring":
            with st.spinner("AI is analyzing lead quality..."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Simulate AI processing
                import time
                for i in range(100):
                    time.sleep(0.03)
                    progress_bar.progress(i + 1)
                    if i < 30:
                        status_text.text("Analyzing contact information...")
                    elif i < 60:
                        status_text.text("Evaluating budget and timeline...")
                    elif i < 90:
                        status_text.text("Calculating lead score...")
                    else:
                        status_text.text("Generating recommendations...")

            st.success("✅ AI analysis complete!")

        elif step.id == "ai_search":
            with st.spinner("AI is searching for matching properties..."):
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Simulate property search
                for i in range(100):
                    time.sleep(0.02)
                    progress_bar.progress(i + 1)
                    if i < 25:
                        status_text.text("Scanning MLS database...")
                    elif i < 50:
                        status_text.text("Applying search criteria...")
                    elif i < 75:
                        status_text.text("Scoring property matches...")
                    else:
                        status_text.text("Ranking results...")

            st.success("✅ Found 15 potential matches!")

    def _render_completion_step(self, step: WorkflowStep, state: Dict[str, Any]) -> None:
        """Render completion step content"""
        st.markdown("### 🎉 Workflow Complete!")
        st.success("Great job! Your workflow has been completed successfully.")

        # Show summary
        st.markdown("#### Summary")
        st.markdown("- All required steps completed")
        st.markdown("- Data saved to system")
        st.markdown("- Next actions scheduled")

        # Offer next steps
        st.markdown("#### What's Next?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Another Workflow", use_container_width=True):
                # Reset workflow state
                pass
        with col2:
            if st.button("View Results", use_container_width=True):
                # Show detailed results
                pass

    def _render_workflow_navigation(self, workflow: WorkflowDefinition,
                                  current_step: WorkflowStep,
                                  state: Dict[str, Any]) -> None:
        """Render workflow navigation controls"""
        st.markdown("""
        <div class="workflow-navigation">
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            if self._has_previous_step(workflow, current_step):
                if st.button("← Previous", key="nav_previous"):
                    self._go_to_previous_step(workflow, state)

        with col2:
            # Save draft button
            if st.button("💾 Save Draft", key="save_draft"):
                st.success("Progress saved!")

            # Show validation errors if any
            validation_errors = self._validate_current_step(current_step, state)
            if validation_errors:
                st.error("Please fix the following issues:")
                for error in validation_errors:
                    st.markdown(f"• {error}")

        with col3:
            can_proceed = len(self._validate_current_step(current_step, state)) == 0

            if self._has_next_step(workflow, current_step):
                if st.button("Next →", key="nav_next", disabled=not can_proceed):
                    if can_proceed:
                        self._go_to_next_step(workflow, current_step, state)
            else:
                if st.button("Complete ✓", key="nav_complete", disabled=not can_proceed):
                    if can_proceed:
                        self._complete_workflow(workflow, state)

        st.markdown("</div>", unsafe_allow_html=True)

    def _find_step(self, workflow: WorkflowDefinition, step_id: str) -> Optional[WorkflowStep]:
        """Find workflow step by ID"""
        for step in workflow.steps:
            if step.id == step_id:
                return step
        return None

    def _validate_current_step(self, step: WorkflowStep, state: Dict[str, Any]) -> List[str]:
        """Validate current step inputs"""
        errors = []

        if step.required:
            # Check for required fields based on step type
            if step.type == WorkflowStepType.INPUT:
                required_fields = self._get_required_fields(step)
                for field in required_fields:
                    field_key = f"{step.id}_{field}"
                    if field_key not in st.session_state or not st.session_state[field_key]:
                        errors.append(f"{field.replace('_', ' ').title()} is required")

        return errors

    def _get_required_fields(self, step: WorkflowStep) -> List[str]:
        """Get required fields for a step"""
        required_fields_map = {
            "contact_info": ["first_name", "last_name", "email", "phone"],
            "budget_qualification": ["budget", "timeline", "financing", "current_housing"],
            "criteria_setup": ["type", "min_beds", "areas"]
        }
        return required_fields_map.get(step.id, [])

    def _has_previous_step(self, workflow: WorkflowDefinition, current_step: WorkflowStep) -> bool:
        """Check if there's a previous step"""
        current_index = next(i for i, step in enumerate(workflow.steps) if step.id == current_step.id)
        return current_index > 0

    def _has_next_step(self, workflow: WorkflowDefinition, current_step: WorkflowStep) -> bool:
        """Check if there's a next step"""
        current_index = next(i for i, step in enumerate(workflow.steps) if step.id == current_step.id)
        return current_index < len(workflow.steps) - 1

    def _go_to_previous_step(self, workflow: WorkflowDefinition, state: Dict[str, Any]) -> None:
        """Navigate to previous step"""
        current_index = next(i for i, step in enumerate(workflow.steps) if step.id == state["current_step"])
        if current_index > 0:
            previous_step = workflow.steps[current_index - 1]
            state["current_step"] = previous_step.id
            st.experimental_rerun()

    def _go_to_next_step(self, workflow: WorkflowDefinition,
                        current_step: WorkflowStep, state: Dict[str, Any]) -> None:
        """Navigate to next step"""
        # Mark current step as completed
        if current_step.id not in state["completed_steps"]:
            state["completed_steps"].append(current_step.id)

        # Move to next step
        current_index = next(i for i, step in enumerate(workflow.steps) if step.id == current_step.id)
        if current_index < len(workflow.steps) - 1:
            next_step = workflow.steps[current_index + 1]
            state["current_step"] = next_step.id
            st.experimental_rerun()

    def _complete_workflow(self, workflow: WorkflowDefinition, state: Dict[str, Any]) -> None:
        """Complete workflow execution"""
        state["status"] = WorkflowStatus.COMPLETED
        state["end_time"] = datetime.now()

        # Mark final step as completed
        if state["current_step"] not in state["completed_steps"]:
            state["completed_steps"].append(state["current_step"])

        st.balloons()
        st.success(f"🎉 {workflow.name} completed successfully!")

    def render_workflow_builder(self) -> None:
        """Render visual workflow builder"""
        st.markdown("### 🛠️ Workflow Builder")
        st.markdown("Create custom workflows with drag-and-drop interface")

        # For now, show a simplified version
        st.info("🚧 Visual workflow builder coming soon! Currently supports predefined workflows.")

        # Show current workflows
        st.markdown("#### Available Workflows")
        for workflow in self.workflows.values():
            with st.expander(f"{workflow.name} - {len(workflow.steps)} steps"):
                st.markdown(f"**Description:** {workflow.description}")
                st.markdown(f"**Category:** {workflow.category}")
                st.markdown(f"**Difficulty:** {workflow.difficulty}")
                st.markdown(f"**Duration:** ~{workflow.estimated_duration} minutes")

                st.markdown("**Steps:**")
                for i, step in enumerate(workflow.steps):
                    st.markdown(f"{i+1}. {step.title} ({step.type.value})")


# Global workflow design system instance
workflow_system = WorkflowDesignSystem()

def get_workflow_system() -> WorkflowDesignSystem:
    """Get the global workflow design system instance"""
    return workflow_system