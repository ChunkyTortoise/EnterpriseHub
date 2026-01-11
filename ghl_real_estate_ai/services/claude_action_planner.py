"""
Claude Action Planner Service (Phase 3 Enhancement)

Provides intelligent action planning and recommendations using Claude's reasoning capabilities.
Analyzes conversation context, lead qualification progress, and behavioral signals to suggest
optimal next steps, follow-up strategies, and automated actions.

Features:
- Context-aware action recommendations
- Personalized follow-up strategy generation
- Dynamic workflow suggestion based on lead lifecycle stage
- Intelligent timing optimization for agent actions
- Multi-channel communication planning
- Risk assessment and intervention strategies
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum

from ghl_real_estate_ai.services.claude_semantic_analyzer import ClaudeSemanticAnalyzer

logger = logging.getLogger(__name__)


class ActionPriority(Enum):
    """Action priority levels for agent recommendations."""
    CRITICAL = "critical"    # Immediate action required (< 1 hour)
    HIGH = "high"           # Action needed today
    MEDIUM = "medium"       # Action needed this week
    LOW = "low"            # Action can be scheduled flexibly


class ActionCategory(Enum):
    """Categories of recommended actions."""
    IMMEDIATE_RESPONSE = "immediate_response"    # Send message/call now
    FOLLOW_UP = "follow_up"                     # Scheduled follow-up
    QUALIFICATION = "qualification"              # Continue qualification process
    NURTURING = "nurturing"                     # Long-term relationship building
    SCHEDULING = "scheduling"                    # Book appointments/meetings
    CONTENT_DELIVERY = "content_delivery"       # Send listings, documents, etc.
    ESCALATION = "escalation"                   # Hand off or get help
    WORKFLOW_TRIGGER = "workflow_trigger"       # Trigger automated workflow


class ActionChannel(Enum):
    """Communication channels for action execution."""
    SMS = "sms"
    EMAIL = "email"
    PHONE_CALL = "phone_call"
    PROPERTY_PORTAL = "property_portal"
    IN_PERSON = "in_person"
    VIDEO_CALL = "video_call"
    WORKFLOW_AUTOMATION = "workflow_automation"


class ClaudeActionPlanner:
    """
    Intelligent action planning service using Claude AI reasoning.

    Analyzes lead context, conversation history, and qualification progress
    to recommend optimal next steps and strategies for real estate agents.
    """

    # Action templates organized by scenario
    ACTION_TEMPLATES = {
        "first_contact": {
            "priority": ActionPriority.HIGH,
            "category": ActionCategory.IMMEDIATE_RESPONSE,
            "channel": ActionChannel.SMS,
            "timing_hours": 0.5,  # 30 minutes
            "template": "Welcome and initial engagement"
        },
        "high_intent_detected": {
            "priority": ActionPriority.CRITICAL,
            "category": ActionCategory.IMMEDIATE_RESPONSE,
            "channel": ActionChannel.PHONE_CALL,
            "timing_hours": 1.0,
            "template": "Strike while iron is hot - call immediately"
        },
        "qualification_stalled": {
            "priority": ActionPriority.MEDIUM,
            "category": ActionCategory.QUALIFICATION,
            "channel": ActionChannel.SMS,
            "timing_hours": 24.0,
            "template": "Re-engage with different approach"
        },
        "ready_for_showing": {
            "priority": ActionPriority.HIGH,
            "category": ActionCategory.SCHEDULING,
            "channel": ActionChannel.PHONE_CALL,
            "timing_hours": 2.0,
            "template": "Schedule property viewing"
        }
    }

    # Follow-up sequences based on lead behavior
    FOLLOW_UP_SEQUENCES = {
        "new_lead_nurture": [
            {"day": 1, "channel": "sms", "focus": "welcome_introduction"},
            {"day": 3, "channel": "email", "focus": "market_insights"},
            {"day": 7, "channel": "sms", "focus": "check_in_questions"},
            {"day": 14, "channel": "email", "focus": "success_stories"}
        ],
        "qualified_buyer": [
            {"day": 1, "channel": "phone_call", "focus": "schedule_showing"},
            {"day": 3, "channel": "sms", "focus": "listing_alerts_setup"},
            {"day": 7, "channel": "email", "focus": "market_update"},
            {"day": 14, "channel": "phone_call", "focus": "feedback_check"}
        ],
        "warm_prospect": [
            {"day": 2, "channel": "sms", "focus": "value_proposition"},
            {"day": 7, "channel": "email", "focus": "educational_content"},
            {"day": 14, "channel": "sms", "focus": "market_opportunity"},
            {"day": 30, "channel": "phone_call", "focus": "relationship_check"}
        ]
    }

    def __init__(self, location_id: str):
        """
        Initialize action planner for a specific GHL location.

        Args:
            location_id: GHL Location ID for multi-tenant support
        """
        self.location_id = location_id
        self.data_dir = Path(__file__).parent.parent / "data" / "action_planning" / location_id
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # File storage
        self.plans_file = self.data_dir / "action_plans.json"
        self.strategies_file = self.data_dir / "strategies.json"
        self.performance_file = self.data_dir / "performance_metrics.json"

        # Load existing data
        self.action_plans = self._load_action_plans()
        self.strategies = self._load_strategies()
        self.performance_metrics = self._load_performance_metrics()

        # Initialize Claude analyzer
        self.claude_analyzer = ClaudeSemanticAnalyzer()

        logger.info(f"ClaudeActionPlanner initialized for location {location_id}")

    def _load_action_plans(self) -> Dict:
        """Load existing action plans from file."""
        if self.plans_file.exists():
            try:
                with open(self.plans_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading action plans: {e}")
        return {}

    def _save_action_plans(self) -> None:
        """Save action plans to file."""
        try:
            with open(self.plans_file, 'w') as f:
                json.dump(self.action_plans, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving action plans: {e}")

    def _load_strategies(self) -> Dict:
        """Load follow-up strategies from file."""
        if self.strategies_file.exists():
            try:
                with open(self.strategies_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading strategies: {e}")
        return {}

    def _save_strategies(self) -> None:
        """Save strategies to file."""
        try:
            with open(self.strategies_file, 'w') as f:
                json.dump(self.strategies, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving strategies: {e}")

    def _load_performance_metrics(self) -> Dict:
        """Load performance metrics from file."""
        if self.performance_file.exists():
            try:
                with open(self.performance_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading performance metrics: {e}")
        return {"plans_created": 0, "actions_executed": 0, "success_rate": 0}

    def _save_performance_metrics(self) -> None:
        """Save performance metrics to file."""
        try:
            with open(self.performance_file, 'w') as f:
                json.dump(self.performance_metrics, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving performance metrics: {e}")

    async def create_action_plan(
        self,
        contact_id: str,
        context: Dict[str, Any],
        qualification_data: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict]] = None,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create comprehensive action plan using Claude intelligence.

        Args:
            contact_id: Unique contact identifier
            context: Lead context and current situation
            qualification_data: Qualification progress from orchestrator
            conversation_history: Recent conversation messages
            agent_id: Agent handling the lead

        Returns:
            Dictionary containing action plan with recommendations and timing
        """
        try:
            plan_id = f"plan_{contact_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            now = datetime.now().isoformat()

            # Analyze current situation with Claude
            situation_analysis = await self._analyze_situation(
                context, qualification_data, conversation_history
            )

            # Generate immediate action recommendations
            immediate_actions = await self._generate_immediate_actions(
                contact_id, situation_analysis
            )

            # Create follow-up strategy
            follow_up_strategy = await self._create_follow_up_strategy(
                contact_id, situation_analysis
            )

            # Assess risks and opportunities
            risk_assessment = await self._assess_risks_opportunities(
                situation_analysis, conversation_history
            )

            # Create comprehensive action plan
            action_plan = {
                "plan_id": plan_id,
                "contact_id": contact_id,
                "agent_id": agent_id,
                "location_id": self.location_id,
                "created_at": now,
                "updated_at": now,
                "status": "active",

                # Analysis results
                "situation_analysis": situation_analysis,
                "risk_assessment": risk_assessment,

                # Action recommendations
                "immediate_actions": immediate_actions,
                "follow_up_strategy": follow_up_strategy,

                # Execution tracking
                "execution_status": {
                    "actions_completed": 0,
                    "actions_pending": len(immediate_actions),
                    "next_action_due": self._calculate_next_action_time(immediate_actions)
                },

                # Performance metrics
                "metrics": {
                    "priority_score": situation_analysis.get("priority_score", 50),
                    "likelihood_to_convert": situation_analysis.get("conversion_likelihood", 50),
                    "urgency_level": situation_analysis.get("urgency_level", "medium"),
                    "engagement_quality": situation_analysis.get("engagement_quality", "medium")
                }
            }

            # Save action plan
            self.action_plans[plan_id] = action_plan
            self._save_action_plans()

            # Update metrics
            self.performance_metrics["plans_created"] += 1
            self._save_performance_metrics()

            logger.info(f"Created action plan {plan_id} for contact {contact_id}")

            return action_plan

        except Exception as e:
            logger.error(f"Error creating action plan: {e}")
            return {"error": str(e), "status": "failed"}

    async def _analyze_situation(
        self,
        context: Dict[str, Any],
        qualification_data: Optional[Dict[str, Any]],
        conversation_history: Optional[List[Dict]]
    ) -> Dict[str, Any]:
        """Analyze current lead situation using Claude intelligence."""
        try:
            # Build analysis context
            analysis_context = {
                "lead_context": context,
                "qualification_progress": qualification_data or {},
                "conversation_recent": conversation_history[-5:] if conversation_history else [],
                "analysis_timestamp": datetime.now().isoformat()
            }

            # Use Claude for semantic analysis
            conversation_messages = []
            if conversation_history:
                for msg in conversation_history[-10:]:
                    conversation_messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", msg.get("text", "")),
                        "timestamp": msg.get("timestamp", "")
                    })

            claude_analysis = {}
            if conversation_messages:
                try:
                    claude_analysis = await self.claude_analyzer.analyze_lead_intent(conversation_messages)
                except Exception as e:
                    logger.warning(f"Claude analysis failed: {e}")

            # Calculate priority score
            priority_score = self._calculate_priority_score(
                context, qualification_data, claude_analysis
            )

            # Determine urgency level
            urgency_level = self._determine_urgency_level(
                claude_analysis, qualification_data
            )

            # Assess engagement quality
            engagement_quality = self._assess_engagement_quality(
                conversation_history, claude_analysis
            )

            return {
                "priority_score": priority_score,
                "urgency_level": urgency_level,
                "engagement_quality": engagement_quality,
                "conversion_likelihood": claude_analysis.get("conversion_probability", 50),
                "key_insights": claude_analysis.get("key_insights", []),
                "behavioral_signals": claude_analysis.get("behavioral_signals", []),
                "qualification_gaps": self._identify_qualification_gaps(qualification_data),
                "recommended_approach": self._recommend_approach(
                    priority_score, urgency_level, engagement_quality
                )
            }

        except Exception as e:
            logger.error(f"Error analyzing situation: {e}")
            return {"error": str(e), "priority_score": 50}

    def _calculate_priority_score(
        self,
        context: Dict[str, Any],
        qualification_data: Optional[Dict[str, Any]],
        claude_analysis: Dict[str, Any]
    ) -> int:
        """Calculate priority score for action planning."""
        score = 50  # Base score

        # Qualification progress weight
        if qualification_data:
            completion = qualification_data.get("completion_percentage", 0)
            if completion >= 80:
                score += 25
            elif completion >= 50:
                score += 15
            elif completion >= 20:
                score += 10

        # Claude intent analysis weight
        intent_confidence = claude_analysis.get("confidence", 50)
        if intent_confidence > 80:
            score += 20
        elif intent_confidence > 60:
            score += 10

        # Urgency indicators
        urgency = claude_analysis.get("urgency_score", 50)
        if urgency > 75:
            score += 15
        elif urgency > 50:
            score += 5

        # Recent activity
        last_interaction = context.get("last_interaction_timestamp")
        if last_interaction:
            try:
                last_time = datetime.fromisoformat(last_interaction)
                hours_since = (datetime.now() - last_time).total_seconds() / 3600

                if hours_since < 2:
                    score += 10
                elif hours_since < 24:
                    score += 5
                elif hours_since > 72:
                    score -= 10
            except:
                pass

        return max(0, min(100, score))

    def _determine_urgency_level(
        self,
        claude_analysis: Dict[str, Any],
        qualification_data: Optional[Dict[str, Any]]
    ) -> str:
        """Determine urgency level for action recommendations."""
        urgency_score = claude_analysis.get("urgency_score", 50)

        # Check for explicit urgency indicators
        urgency_indicators = claude_analysis.get("urgency_indicators", [])
        high_urgency_keywords = ["asap", "urgent", "soon", "immediately", "deadline"]

        has_urgency_keywords = any(
            keyword in " ".join(urgency_indicators).lower()
            for keyword in high_urgency_keywords
        )

        # Check qualification progress urgency
        qualification_urgency = False
        if qualification_data:
            completion = qualification_data.get("completion_percentage", 0)
            if completion >= 80:  # Ready to close
                qualification_urgency = True

        if urgency_score > 80 or has_urgency_keywords or qualification_urgency:
            return "critical"
        elif urgency_score > 60:
            return "high"
        elif urgency_score > 40:
            return "medium"
        else:
            return "low"

    def _assess_engagement_quality(
        self,
        conversation_history: Optional[List[Dict]],
        claude_analysis: Dict[str, Any]
    ) -> str:
        """Assess quality of lead engagement."""
        if not conversation_history:
            return "unknown"

        # Recent message count
        recent_messages = len(conversation_history[-10:])

        # Message length analysis
        avg_length = 0
        if conversation_history:
            total_length = sum(len(msg.get("content", msg.get("text", ""))) for msg in conversation_history)
            avg_length = total_length / len(conversation_history)

        # Claude engagement signals
        engagement_score = claude_analysis.get("engagement_score", 50)

        # Quality assessment
        if engagement_score > 80 and recent_messages >= 5 and avg_length > 50:
            return "high"
        elif engagement_score > 60 and recent_messages >= 3:
            return "medium"
        elif engagement_score > 40 or recent_messages >= 1:
            return "low"
        else:
            return "minimal"

    def _identify_qualification_gaps(
        self,
        qualification_data: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Identify gaps in lead qualification."""
        if not qualification_data:
            return ["No qualification data available"]

        gaps = []
        qualification_areas = ["budget", "timeline", "location", "property_preferences"]

        for area in qualification_areas:
            area_data = qualification_data.get(area, {})
            if isinstance(area_data, dict):
                confidence = area_data.get("confidence", 0)
                if confidence < 70:
                    gaps.append(f"Incomplete {area} information")

        return gaps or ["Qualification appears complete"]

    def _recommend_approach(
        self,
        priority_score: int,
        urgency_level: str,
        engagement_quality: str
    ) -> str:
        """Recommend overall approach strategy."""
        if priority_score > 80 and urgency_level in ["critical", "high"]:
            return "immediate_aggressive_pursuit"
        elif priority_score > 60 and engagement_quality in ["high", "medium"]:
            return "active_nurturing"
        elif urgency_level in ["critical", "high"]:
            return "urgency_response"
        elif engagement_quality == "low":
            return "re_engagement_required"
        else:
            return "standard_follow_up"

    async def _generate_immediate_actions(
        self,
        contact_id: str,
        situation_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate immediate action recommendations."""
        actions = []
        priority_score = situation_analysis.get("priority_score", 50)
        urgency_level = situation_analysis.get("urgency_level", "medium")
        approach = situation_analysis.get("recommended_approach", "standard_follow_up")

        # Immediate response based on urgency and priority
        if urgency_level == "critical":
            actions.append({
                "action_id": f"immediate_{contact_id}_{len(actions)}",
                "category": ActionCategory.IMMEDIATE_RESPONSE.value,
                "priority": ActionPriority.CRITICAL.value,
                "channel": ActionChannel.PHONE_CALL.value,
                "action": "Make immediate phone call",
                "description": "High urgency detected - call within 1 hour",
                "due_time": (datetime.now() + timedelta(hours=1)).isoformat(),
                "estimated_duration_minutes": 15,
                "success_criteria": "Contact reached and next steps confirmed"
            })

        elif priority_score > 70:
            actions.append({
                "action_id": f"priority_{contact_id}_{len(actions)}",
                "category": ActionCategory.IMMEDIATE_RESPONSE.value,
                "priority": ActionPriority.HIGH.value,
                "channel": ActionChannel.SMS.value,
                "action": "Send personalized SMS",
                "description": "High-priority lead - send targeted message within 4 hours",
                "due_time": (datetime.now() + timedelta(hours=4)).isoformat(),
                "estimated_duration_minutes": 5,
                "success_criteria": "Message sent and response received"
            })

        # Follow-up actions based on qualification gaps
        qualification_gaps = situation_analysis.get("qualification_gaps", [])
        if "budget" in str(qualification_gaps).lower():
            actions.append({
                "action_id": f"budget_{contact_id}_{len(actions)}",
                "category": ActionCategory.QUALIFICATION.value,
                "priority": ActionPriority.HIGH.value,
                "channel": ActionChannel.SMS.value,
                "action": "Qualify budget range",
                "description": "Ask about budget and financing status",
                "due_time": (datetime.now() + timedelta(hours=8)).isoformat(),
                "estimated_duration_minutes": 10,
                "success_criteria": "Budget range and financing status obtained"
            })

        # Content delivery based on engagement
        engagement_quality = situation_analysis.get("engagement_quality", "medium")
        if engagement_quality in ["medium", "high"]:
            actions.append({
                "action_id": f"content_{contact_id}_{len(actions)}",
                "category": ActionCategory.CONTENT_DELIVERY.value,
                "priority": ActionPriority.MEDIUM.value,
                "channel": ActionChannel.EMAIL.value,
                "action": "Send market insights",
                "description": "Provide valuable market information to maintain engagement",
                "due_time": (datetime.now() + timedelta(days=1)).isoformat(),
                "estimated_duration_minutes": 20,
                "success_criteria": "Content delivered and engagement maintained"
            })

        return actions

    async def _create_follow_up_strategy(
        self,
        contact_id: str,
        situation_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive follow-up strategy."""
        priority_score = situation_analysis.get("priority_score", 50)
        approach = situation_analysis.get("recommended_approach", "standard_follow_up")

        # Select appropriate follow-up sequence
        if priority_score > 80:
            sequence_type = "qualified_buyer"
        elif priority_score > 60:
            sequence_type = "warm_prospect"
        else:
            sequence_type = "new_lead_nurture"

        base_sequence = self.FOLLOW_UP_SEQUENCES.get(sequence_type, [])

        # Customize sequence based on situation
        customized_sequence = []
        for step in base_sequence:
            customized_step = {
                **step,
                "due_date": (datetime.now() + timedelta(days=step["day"])).isoformat(),
                "priority": self._determine_step_priority(step, situation_analysis),
                "personalization_notes": self._generate_personalization_notes(step, situation_analysis)
            }
            customized_sequence.append(customized_step)

        return {
            "strategy_type": sequence_type,
            "total_steps": len(customized_sequence),
            "sequence": customized_sequence,
            "success_metrics": {
                "response_rate_target": 60,
                "engagement_score_target": 70,
                "conversion_probability_target": 30
            }
        }

    def _determine_step_priority(
        self,
        step: Dict[str, Any],
        situation_analysis: Dict[str, Any]
    ) -> str:
        """Determine priority for follow-up step."""
        urgency_level = situation_analysis.get("urgency_level", "medium")

        if step["focus"] in ["schedule_showing", "feedback_check"] and urgency_level == "critical":
            return ActionPriority.CRITICAL.value
        elif step["focus"] in ["welcome_introduction", "check_in_questions"]:
            return ActionPriority.HIGH.value
        else:
            return ActionPriority.MEDIUM.value

    def _generate_personalization_notes(
        self,
        step: Dict[str, Any],
        situation_analysis: Dict[str, Any]
    ) -> str:
        """Generate personalization notes for follow-up steps."""
        key_insights = situation_analysis.get("key_insights", [])
        behavioral_signals = situation_analysis.get("behavioral_signals", [])

        notes = []

        if step["focus"] == "welcome_introduction":
            notes.append("Reference their specific property interests from initial conversation")

        elif step["focus"] == "market_insights":
            notes.append("Focus on their preferred locations and price range")

        elif step["focus"] == "check_in_questions":
            if "urgency" in str(behavioral_signals).lower():
                notes.append("Ask about timeline urgency mentioned earlier")

        return "; ".join(notes) if notes else "Use standard template with personal touch"

    async def _assess_risks_opportunities(
        self,
        situation_analysis: Dict[str, Any],
        conversation_history: Optional[List[Dict]]
    ) -> Dict[str, Any]:
        """Assess risks and opportunities for this lead."""
        risks = []
        opportunities = []

        # Risk assessment
        engagement_quality = situation_analysis.get("engagement_quality", "medium")
        if engagement_quality == "low":
            risks.append({
                "type": "low_engagement",
                "severity": "medium",
                "description": "Lead showing minimal engagement",
                "mitigation": "Try different communication channel or content approach"
            })

        urgency_level = situation_analysis.get("urgency_level", "medium")
        if urgency_level == "critical":
            opportunities.append({
                "type": "time_sensitive_opportunity",
                "potential": "high",
                "description": "Lead showing urgency signals",
                "action": "Prioritize immediate response and fast-track qualification"
            })

        # Analyze conversation patterns for risks/opportunities
        if conversation_history:
            recent_messages = len(conversation_history[-5:])
            if recent_messages == 0:
                risks.append({
                    "type": "communication_gap",
                    "severity": "high",
                    "description": "No recent communication activity",
                    "mitigation": "Immediate re-engagement attempt with valuable content"
                })

        return {
            "risks": risks,
            "opportunities": opportunities,
            "overall_risk_level": self._calculate_overall_risk(risks),
            "overall_opportunity_level": self._calculate_overall_opportunity(opportunities)
        }

    def _calculate_overall_risk(self, risks: List[Dict]) -> str:
        """Calculate overall risk level."""
        if not risks:
            return "low"

        high_risks = sum(1 for risk in risks if risk.get("severity") == "high")
        if high_risks > 0:
            return "high"
        elif len(risks) > 2:
            return "medium"
        else:
            return "low"

    def _calculate_overall_opportunity(self, opportunities: List[Dict]) -> str:
        """Calculate overall opportunity level."""
        if not opportunities:
            return "low"

        high_potential = sum(1 for opp in opportunities if opp.get("potential") == "high")
        if high_potential > 0:
            return "high"
        elif len(opportunities) > 1:
            return "medium"
        else:
            return "low"

    def _calculate_next_action_time(self, immediate_actions: List[Dict]) -> Optional[str]:
        """Calculate when the next action is due."""
        if not immediate_actions:
            return None

        earliest_due = min(
            action.get("due_time", datetime.now().isoformat())
            for action in immediate_actions
        )

        return earliest_due

    def get_action_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get action plan by ID."""
        return self.action_plans.get(plan_id)

    def update_action_status(
        self,
        plan_id: str,
        action_id: str,
        status: str,
        result: Optional[str] = None
    ) -> bool:
        """Update status of a specific action in a plan."""
        try:
            if plan_id not in self.action_plans:
                return False

            plan = self.action_plans[plan_id]

            # Find and update action
            for action in plan["immediate_actions"]:
                if action.get("action_id") == action_id:
                    action["status"] = status
                    action["completed_at"] = datetime.now().isoformat()
                    if result:
                        action["result"] = result

                    # Update plan execution status
                    plan["execution_status"]["actions_completed"] += 1
                    plan["execution_status"]["actions_pending"] -= 1
                    plan["updated_at"] = datetime.now().isoformat()

                    self._save_action_plans()
                    return True

            return False

        except Exception as e:
            logger.error(f"Error updating action status: {e}")
            return False

    def get_actions_due(
        self,
        agent_id: Optional[str] = None,
        hours_ahead: int = 24
    ) -> List[Dict[str, Any]]:
        """Get actions due within specified timeframe."""
        due_actions = []
        cutoff_time = datetime.now() + timedelta(hours=hours_ahead)

        for plan in self.action_plans.values():
            # Filter by agent if specified
            if agent_id and plan.get("agent_id") != agent_id:
                continue

            # Check immediate actions
            for action in plan.get("immediate_actions", []):
                if action.get("status", "pending") == "pending":
                    due_time = datetime.fromisoformat(action.get("due_time", datetime.now().isoformat()))
                    if due_time <= cutoff_time:
                        due_actions.append({
                            **action,
                            "plan_id": plan["plan_id"],
                            "contact_id": plan["contact_id"]
                        })

        # Sort by priority and due time
        priority_order = {"critical": 1, "high": 2, "medium": 3, "low": 4}
        due_actions.sort(
            key=lambda x: (priority_order.get(x.get("priority", "medium"), 3), x.get("due_time"))
        )

        return due_actions

    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get action planning performance analytics."""
        total_plans = len(self.action_plans)
        active_plans = len([p for p in self.action_plans.values() if p.get("status") == "active"])

        # Calculate success metrics
        completed_actions = 0
        total_actions = 0

        for plan in self.action_plans.values():
            for action in plan.get("immediate_actions", []):
                total_actions += 1
                if action.get("status") == "completed":
                    completed_actions += 1

        success_rate = (completed_actions / total_actions * 100) if total_actions > 0 else 0

        return {
            "total_plans_created": total_plans,
            "active_plans": active_plans,
            "total_actions": total_actions,
            "completed_actions": completed_actions,
            "success_rate": round(success_rate, 1),
            "average_priority_score": self._calculate_average_priority_score(),
            "most_common_urgency_level": self._get_most_common_urgency_level(),
            "performance_metrics": self.performance_metrics
        }

    def _calculate_average_priority_score(self) -> float:
        """Calculate average priority score across all plans."""
        scores = [
            plan.get("metrics", {}).get("priority_score", 50)
            for plan in self.action_plans.values()
        ]
        return sum(scores) / len(scores) if scores else 50.0

    def _get_most_common_urgency_level(self) -> str:
        """Get most common urgency level."""
        urgency_counts = defaultdict(int)
        for plan in self.action_plans.values():
            urgency = plan.get("metrics", {}).get("urgency_level", "medium")
            urgency_counts[urgency] += 1

        return max(urgency_counts.items(), key=lambda x: x[1])[0] if urgency_counts else "medium"


if __name__ == "__main__":
    # Demo usage
    import asyncio

    async def demo():
        print("Claude Action Planner Demo\n")
        print("=" * 70)

        planner = ClaudeActionPlanner("demo_location")

        # Create sample context
        context = {
            "contact_id": "contact_789",
            "last_interaction_timestamp": datetime.now().isoformat(),
            "lead_source": "website",
            "tags": ["Interested", "First-Time-Buyer"]
        }

        qualification_data = {
            "completion_percentage": 65,
            "budget": {"confidence": 80, "mentioned": True},
            "timeline": {"confidence": 40, "mentioned": False},
            "location": {"confidence": 90, "mentioned": True}
        }

        conversation_history = [
            {"role": "user", "content": "Looking for a 3br house in Austin under 400k", "timestamp": datetime.now().isoformat()},
            {"role": "assistant", "content": "I can help you find great options! What's your ideal timeline?", "timestamp": datetime.now().isoformat()},
            {"role": "user", "content": "Pretty flexible, but would like to move by summer", "timestamp": datetime.now().isoformat()}
        ]

        # Create action plan
        print("Creating action plan...")
        plan = await planner.create_action_plan(
            contact_id="contact_789",
            context=context,
            qualification_data=qualification_data,
            conversation_history=conversation_history,
            agent_id="agent_123"
        )

        print(f"Plan ID: {plan['plan_id']}")
        print(f"Priority Score: {plan['metrics']['priority_score']}")
        print(f"Urgency Level: {plan['metrics']['urgency_level']}")
        print(f"Immediate Actions: {len(plan['immediate_actions'])}")
        print(f"Follow-up Steps: {plan['follow_up_strategy']['total_steps']}")

        # Get actions due
        due_actions = planner.get_actions_due(hours_ahead=24)
        print(f"\nActions due in next 24 hours: {len(due_actions)}")

        # Get analytics
        analytics = planner.get_performance_analytics()
        print(f"Success rate: {analytics['success_rate']}%")
        print("=" * 70)

    # Run demo
    asyncio.run(demo())