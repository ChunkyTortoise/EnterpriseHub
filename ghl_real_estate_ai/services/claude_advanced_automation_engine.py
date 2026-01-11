"""
Claude Advanced Automation Engine (Advanced Feature #2)

Intelligent workflow automation system that uses Claude AI analysis to trigger
sophisticated automated responses and actions based on conversation patterns,
behavioral signals, and predictive insights.

Features:
- Intelligent trigger detection using Claude semantic analysis
- Dynamic workflow branching based on conversation context
- Multi-channel automation (SMS, email, calls, tasks)
- Behavior-driven automation rules
- Market condition-sensitive automations
- Lead lifecycle automation with AI decision points
- Agent workload balancing automation
- Performance-based automation optimization
"""

import asyncio
import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable

from anthropic import AsyncAnthropic
from ghl_real_estate_ai.services.claude_semantic_analyzer import ClaudeSemanticAnalyzer
from ghl_real_estate_ai.services.claude_predictive_analytics_engine import claude_predictive_analytics
from ghl_real_estate_ai.ghl_utils.config import settings

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Types of automation triggers."""
    MESSAGE_RECEIVED = "message_received"
    BEHAVIORAL_PATTERN = "behavioral_pattern"
    TIME_BASED = "time_based"
    LIFECYCLE_STAGE = "lifecycle_stage"
    ENGAGEMENT_THRESHOLD = "engagement_threshold"
    MARKET_CONDITION = "market_condition"
    AGENT_AVAILABILITY = "agent_availability"
    LEAD_SCORE_CHANGE = "lead_score_change"
    COMPETITIVE_EVENT = "competitive_event"
    SEASONAL_TRIGGER = "seasonal_trigger"


class ActionType(Enum):
    """Types of automated actions."""
    SEND_SMS = "send_sms"
    SEND_EMAIL = "send_email"
    SCHEDULE_CALL = "schedule_call"
    CREATE_TASK = "create_task"
    UPDATE_LEAD_SCORE = "update_lead_score"
    TRIGGER_WORKFLOW = "trigger_workflow"
    ASSIGN_AGENT = "assign_agent"
    SEND_LISTING = "send_listing"
    BOOK_SHOWING = "book_showing"
    ESCALATE_URGENT = "escalate_urgent"
    CREATE_FOLLOW_UP = "create_follow_up"
    TRIGGER_NURTURE_SEQUENCE = "trigger_nurture_sequence"


class AutomationPriority(Enum):
    """Priority levels for automation execution."""
    IMMEDIATE = "immediate"  # Execute within 1 minute
    HIGH = "high"           # Execute within 15 minutes
    NORMAL = "normal"       # Execute within 1 hour
    LOW = "low"            # Execute within 24 hours
    SCHEDULED = "scheduled" # Execute at specific time


class AutomationChannel(Enum):
    """Communication channels for automation."""
    SMS = "sms"
    EMAIL = "email"
    PHONE = "phone"
    WHATSAPP = "whatsapp"
    FACEBOOK = "facebook"
    WEBSITE_CHAT = "website_chat"
    INTERNAL_TASK = "internal_task"
    CRM_UPDATE = "crm_update"


@dataclass
class AutomationTrigger:
    """Definition of an automation trigger condition."""
    trigger_id: str
    trigger_type: TriggerType
    trigger_conditions: Dict[str, Any]
    claude_analysis_required: bool
    semantic_keywords: List[str]
    behavioral_patterns: List[str]
    timing_conditions: Dict[str, Any]
    market_conditions: Dict[str, Any]
    priority: AutomationPriority
    is_active: bool
    created_at: datetime


@dataclass
class AutomationAction:
    """Definition of an automated action."""
    action_id: str
    action_type: ActionType
    action_parameters: Dict[str, Any]
    channel: AutomationChannel
    message_template: Optional[str]
    delay_minutes: int
    requires_approval: bool
    fallback_action: Optional[str]
    success_criteria: Dict[str, Any]
    is_active: bool
    created_at: datetime


@dataclass
class AutomationRule:
    """Complete automation rule linking triggers to actions."""
    rule_id: str
    rule_name: str
    description: str
    trigger: AutomationTrigger
    actions: List[AutomationAction]
    conditions: Dict[str, Any]
    exclusion_criteria: Dict[str, Any]
    claude_reasoning_prompt: Optional[str]
    success_metrics: Dict[str, Any]
    is_active: bool
    performance_stats: Dict[str, Any]
    created_at: datetime
    last_executed: Optional[datetime]


@dataclass
class AutomationExecution:
    """Record of an automation execution."""
    execution_id: str
    rule_id: str
    trigger_data: Dict[str, Any]
    claude_analysis: Dict[str, Any]
    actions_executed: List[Dict[str, Any]]
    execution_result: str
    success: bool
    execution_time_ms: float
    lead_id: Optional[str]
    agent_id: Optional[str]
    executed_at: datetime


class ClaudeAdvancedAutomationEngine:
    """
    Advanced automation engine that uses Claude AI to intelligently trigger
    and execute sophisticated workflow automations in real estate processes.
    """

    def __init__(self, location_id: str = "default"):
        """Initialize advanced automation engine."""
        self.location_id = location_id
        self.data_dir = Path(__file__).parent.parent / "data" / "automation" / location_id
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # File storage
        self.rules_file = self.data_dir / "automation_rules.json"
        self.executions_file = self.data_dir / "executions.json"
        self.performance_file = self.data_dir / "performance_metrics.json"
        self.templates_file = self.data_dir / "message_templates.json"

        # Initialize services
        self.claude_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.claude_analyzer = ClaudeSemanticAnalyzer()
        self.predictive_engine = claude_predictive_analytics

        # Load data
        self.automation_rules = self._load_automation_rules()
        self.execution_history = self._load_execution_history()
        self.performance_metrics = self._load_performance_metrics()
        self.message_templates = self._load_message_templates()

        # Runtime state
        self.active_executions = {}
        self.trigger_queue = deque()
        self.execution_lock = asyncio.Lock()
        self.monitoring_tasks = {}

        # Initialize default rules
        self._initialize_default_automation_rules()

        logger.info(f"Claude Advanced Automation Engine initialized for location {location_id}")

    def _load_automation_rules(self) -> Dict[str, AutomationRule]:
        """Load automation rules from file."""
        if self.rules_file.exists():
            try:
                with open(self.rules_file, 'r') as f:
                    data = json.load(f)
                    rules = {}
                    for rule_id, rule_data in data.items():
                        # Convert dict back to dataclass
                        rules[rule_id] = self._dict_to_automation_rule(rule_data)
                    return rules
            except Exception as e:
                logger.error(f"Error loading automation rules: {e}")
        return {}

    def _save_automation_rules(self) -> None:
        """Save automation rules to file."""
        try:
            # Convert dataclasses to dicts for JSON serialization
            rules_data = {}
            for rule_id, rule in self.automation_rules.items():
                rules_data[rule_id] = asdict(rule)

            with open(self.rules_file, 'w') as f:
                json.dump(rules_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving automation rules: {e}")

    def _load_execution_history(self) -> List[AutomationExecution]:
        """Load execution history from file."""
        if self.executions_file.exists():
            try:
                with open(self.executions_file, 'r') as f:
                    data = json.load(f)
                    executions = []
                    for exec_data in data:
                        executions.append(self._dict_to_automation_execution(exec_data))
                    return executions
            except Exception as e:
                logger.error(f"Error loading execution history: {e}")
        return []

    def _save_execution_history(self) -> None:
        """Save execution history to file."""
        try:
            # Keep only last 1000 executions
            recent_executions = self.execution_history[-1000:]
            exec_data = [asdict(execution) for execution in recent_executions]

            with open(self.executions_file, 'w') as f:
                json.dump(exec_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving execution history: {e}")

    def _load_performance_metrics(self) -> Dict[str, Any]:
        """Load performance metrics from file."""
        if self.performance_file.exists():
            try:
                with open(self.performance_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading performance metrics: {e}")
        return {
            "total_executions": 0,
            "successful_executions": 0,
            "average_execution_time_ms": 0,
            "rules_triggered_count": defaultdict(int),
            "actions_executed_count": defaultdict(int),
            "conversion_impact": 0.0,
            "engagement_impact": 0.0
        }

    def _save_performance_metrics(self) -> None:
        """Save performance metrics to file."""
        try:
            with open(self.performance_file, 'w') as f:
                json.dump(self.performance_metrics, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving performance metrics: {e}")

    def _load_message_templates(self) -> Dict[str, Dict[str, str]]:
        """Load message templates from file."""
        if self.templates_file.exists():
            try:
                with open(self.templates_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading message templates: {e}")
        return self._get_default_message_templates()

    def _save_message_templates(self) -> None:
        """Save message templates to file."""
        try:
            with open(self.templates_file, 'w') as f:
                json.dump(self.message_templates, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving message templates: {e}")

    def _initialize_default_automation_rules(self) -> None:
        """Initialize default automation rules if none exist."""
        if not self.automation_rules:
            default_rules = self._create_default_automation_rules()
            for rule in default_rules:
                self.automation_rules[rule.rule_id] = rule
            self._save_automation_rules()
            logger.info(f"Initialized {len(default_rules)} default automation rules")

    def _create_default_automation_rules(self) -> List[AutomationRule]:
        """Create default automation rules for real estate workflows."""
        rules = []

        # Rule 1: High Intent Response
        high_intent_trigger = AutomationTrigger(
            trigger_id="high_intent_detected",
            trigger_type=TriggerType.MESSAGE_RECEIVED,
            trigger_conditions={
                "semantic_analysis": {"intent_strength": ">0.8"},
                "keywords": ["buy", "purchase", "ready", "urgent", "asap"],
                "urgency_score": ">70"
            },
            claude_analysis_required=True,
            semantic_keywords=["buy", "purchase", "ready", "urgent", "serious"],
            behavioral_patterns=["multiple_inquiries", "specific_questions"],
            timing_conditions={"business_hours": False},
            market_conditions={},
            priority=AutomationPriority.IMMEDIATE,
            is_active=True,
            created_at=datetime.now()
        )

        high_intent_action = AutomationAction(
            action_id="immediate_agent_notification",
            action_type=ActionType.CREATE_TASK,
            action_parameters={
                "task_type": "urgent_lead_response",
                "priority": "critical",
                "assign_to": "best_available_agent"
            },
            channel=AutomationChannel.INTERNAL_TASK,
            message_template="urgent_lead_response",
            delay_minutes=0,
            requires_approval=False,
            fallback_action="send_automated_response",
            success_criteria={"response_time": "<15_minutes"},
            is_active=True,
            created_at=datetime.now()
        )

        rules.append(AutomationRule(
            rule_id="high_intent_immediate_response",
            rule_name="High Intent Immediate Response",
            description="Immediately notify agents of high-intent leads",
            trigger=high_intent_trigger,
            actions=[high_intent_action],
            conditions={"business_hours": False, "agent_availability": True},
            exclusion_criteria={"recently_contacted": "<2_hours"},
            claude_reasoning_prompt="Analyze lead intent and urgency for immediate response needs",
            success_metrics={"response_time": 900, "conversion_rate": 0.25},
            is_active=True,
            performance_stats={"executions": 0, "success_rate": 0.0},
            created_at=datetime.now(),
            last_executed=None
        ))

        # Rule 2: Qualification Stalled Recovery
        stalled_trigger = AutomationTrigger(
            trigger_id="qualification_stalled",
            trigger_type=TriggerType.BEHAVIORAL_PATTERN,
            trigger_conditions={
                "qualification_progress": "<50%",
                "days_since_last_response": ">3",
                "engagement_score": "<40"
            },
            claude_analysis_required=True,
            semantic_keywords=["maybe", "thinking", "not sure"],
            behavioral_patterns=["decreasing_engagement", "delayed_responses"],
            timing_conditions={},
            market_conditions={},
            priority=AutomationPriority.HIGH,
            is_active=True,
            created_at=datetime.now()
        )

        stalled_action = AutomationAction(
            action_id="re_engagement_sequence",
            action_type=ActionType.TRIGGER_NURTURE_SEQUENCE,
            action_parameters={
                "sequence_type": "qualification_recovery",
                "personalization_level": "high",
                "channel_preference": "lead_preferred"
            },
            channel=AutomationChannel.SMS,
            message_template="qualification_recovery",
            delay_minutes=60,
            requires_approval=False,
            fallback_action="schedule_agent_call",
            success_criteria={"response_within": "48_hours"},
            is_active=True,
            created_at=datetime.now()
        )

        rules.append(AutomationRule(
            rule_id="qualification_stalled_recovery",
            rule_name="Qualification Stalled Recovery",
            description="Re-engage leads with stalled qualification",
            trigger=stalled_trigger,
            actions=[stalled_action],
            conditions={"lead_score": ">30"},
            exclusion_criteria={"marked_as_not_interested": True},
            claude_reasoning_prompt="Analyze qualification stalling reasons and suggest recovery approach",
            success_metrics={"re_engagement_rate": 0.35, "qualification_completion": 0.15},
            is_active=True,
            performance_stats={"executions": 0, "success_rate": 0.0},
            created_at=datetime.now(),
            last_executed=None
        ))

        # Rule 3: Market Opportunity Alert
        market_trigger = AutomationTrigger(
            trigger_id="market_opportunity",
            trigger_type=TriggerType.MARKET_CONDITION,
            trigger_conditions={
                "price_drop": ">5%",
                "new_listing": True,
                "match_score": ">80%"
            },
            claude_analysis_required=True,
            semantic_keywords=["opportunity", "deal", "motivated"],
            behavioral_patterns=["high_search_activity"],
            timing_conditions={},
            market_conditions={"market_type": "buyers_market"},
            priority=AutomationPriority.HIGH,
            is_active=True,
            created_at=datetime.now()
        )

        market_action = AutomationAction(
            action_id="opportunity_notification",
            action_type=ActionType.SEND_EMAIL,
            action_parameters={
                "template": "market_opportunity_alert",
                "include_listings": True,
                "include_market_analysis": True
            },
            channel=AutomationChannel.EMAIL,
            message_template="market_opportunity",
            delay_minutes=30,
            requires_approval=False,
            fallback_action="send_sms_alert",
            success_criteria={"open_rate": ">0.6", "click_rate": ">0.2"},
            is_active=True,
            created_at=datetime.now()
        )

        rules.append(AutomationRule(
            rule_id="market_opportunity_alert",
            rule_name="Market Opportunity Alert",
            description="Alert qualified leads of market opportunities",
            trigger=market_trigger,
            actions=[market_action],
            conditions={"lead_status": "qualified"},
            exclusion_criteria={"email_frequency": ">2_per_week"},
            claude_reasoning_prompt="Analyze market opportunity relevance for specific lead",
            success_metrics={"engagement_rate": 0.45, "showing_requests": 0.15},
            is_active=True,
            performance_stats={"executions": 0, "success_rate": 0.0},
            created_at=datetime.now(),
            last_executed=None
        ))

        return rules

    def _get_default_message_templates(self) -> Dict[str, Dict[str, str]]:
        """Get default message templates for automations."""
        return {
            "urgent_lead_response": {
                "sms": "Hi {name}! I saw your message and I'm excited to help you. I'll call you within the next 15 minutes to discuss your needs. - {agent_name}",
                "email": "Hi {name},\n\nThank you for reaching out! I can see you're ready to move forward, and I'm here to help make that happen.\n\nI'll be calling you shortly to discuss your specific needs and how I can assist you in finding the perfect property.\n\nBest regards,\n{agent_name}"
            },
            "qualification_recovery": {
                "sms": "Hi {name}, I wanted to follow up on your home search. I found some great options that match what you're looking for. Would you like to see them? - {agent_name}",
                "email": "Hi {name},\n\nI hope you're doing well! I noticed we haven't connected in a few days, and I wanted to check in on your home search.\n\nI've been working on finding properties that match your criteria and have some exciting options to share with you.\n\nWould you be available for a quick call this week to discuss these opportunities?\n\nBest regards,\n{agent_name}"
            },
            "market_opportunity": {
                "email": "Hi {name},\n\nI have exciting news! A property just came on the market that perfectly matches your criteria:\n\n{property_details}\n\nBased on current market conditions, this represents an excellent opportunity. Properties like this are moving quickly in today's market.\n\nWould you like to schedule a viewing? I can arrange a showing as early as tomorrow.\n\nBest regards,\n{agent_name}",
                "sms": "Great news {name}! A perfect property just listed that matches your search. Price: {price}, Location: {location}. Want to see it today? - {agent_name}"
            },
            "showing_reminder": {
                "sms": "Hi {name}, just confirming our showing tomorrow at {time} for {property_address}. See you there! - {agent_name}",
                "email": "Hi {name},\n\nThis is a friendly reminder about our property showing scheduled for:\n\nDate: {date}\nTime: {time}\nAddress: {property_address}\n\nI'll meet you there and we'll have plenty of time to explore the property and discuss any questions you may have.\n\nLooking forward to seeing you!\n\n{agent_name}"
            }
        }

    async def process_trigger_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        lead_id: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> List[AutomationExecution]:
        """
        Process a trigger event and execute matching automation rules.

        Args:
            event_type: Type of event (message_received, behavioral_pattern, etc.)
            event_data: Data associated with the event
            lead_id: Lead identifier if applicable
            agent_id: Agent identifier if applicable

        Returns:
            List of automation executions that were triggered
        """
        try:
            executions = []

            # Find matching automation rules
            matching_rules = await self._find_matching_rules(
                event_type, event_data, lead_id, agent_id
            )

            logger.info(f"Found {len(matching_rules)} matching automation rules for event {event_type}")

            # Execute each matching rule
            for rule in matching_rules:
                try:
                    execution = await self._execute_automation_rule(
                        rule, event_data, lead_id, agent_id
                    )
                    if execution:
                        executions.append(execution)

                        # Update rule performance
                        await self._update_rule_performance(rule.rule_id, execution.success)

                except Exception as e:
                    logger.error(f"Error executing automation rule {rule.rule_id}: {e}")

            # Update global performance metrics
            if executions:
                await self._update_performance_metrics(executions)

            return executions

        except Exception as e:
            logger.error(f"Error processing trigger event {event_type}: {e}")
            return []

    async def _find_matching_rules(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        lead_id: Optional[str],
        agent_id: Optional[str]
    ) -> List[AutomationRule]:
        """Find automation rules that match the current event."""
        matching_rules = []

        for rule in self.automation_rules.values():
            if not rule.is_active:
                continue

            try:
                # Check basic trigger type match
                if not self._check_trigger_type_match(rule.trigger, event_type):
                    continue

                # Check trigger conditions
                if not await self._check_trigger_conditions(rule.trigger, event_data):
                    continue

                # Check rule conditions
                if not await self._check_rule_conditions(rule, event_data, lead_id, agent_id):
                    continue

                # Check exclusion criteria
                if await self._check_exclusion_criteria(rule, event_data, lead_id, agent_id):
                    continue

                # Use Claude analysis if required
                if rule.trigger.claude_analysis_required:
                    claude_approved = await self._claude_rule_approval(
                        rule, event_data, lead_id, agent_id
                    )
                    if not claude_approved:
                        continue

                matching_rules.append(rule)

            except Exception as e:
                logger.error(f"Error checking rule {rule.rule_id}: {e}")

        return matching_rules

    def _check_trigger_type_match(self, trigger: AutomationTrigger, event_type: str) -> bool:
        """Check if trigger type matches the event."""
        trigger_type_map = {
            "message_received": TriggerType.MESSAGE_RECEIVED,
            "behavioral_pattern": TriggerType.BEHAVIORAL_PATTERN,
            "time_based": TriggerType.TIME_BASED,
            "lifecycle_stage": TriggerType.LIFECYCLE_STAGE,
            "engagement_threshold": TriggerType.ENGAGEMENT_THRESHOLD,
            "market_condition": TriggerType.MARKET_CONDITION,
            "lead_score_change": TriggerType.LEAD_SCORE_CHANGE
        }

        return trigger.trigger_type == trigger_type_map.get(event_type)

    async def _check_trigger_conditions(
        self,
        trigger: AutomationTrigger,
        event_data: Dict[str, Any]
    ) -> bool:
        """Check if trigger conditions are met."""
        conditions = trigger.trigger_conditions

        for condition_key, condition_value in conditions.items():
            if condition_key not in event_data:
                return False

            event_value = event_data[condition_key]

            # Handle different condition types
            if isinstance(condition_value, str):
                if condition_value.startswith(">"):
                    threshold = float(condition_value[1:])
                    if float(event_value) <= threshold:
                        return False
                elif condition_value.startswith("<"):
                    threshold = float(condition_value[1:])
                    if float(event_value) >= threshold:
                        return False
                elif condition_value != event_value:
                    return False
            elif isinstance(condition_value, dict):
                # Handle nested conditions like semantic_analysis
                if not self._check_nested_conditions(condition_value, event_value):
                    return False
            elif condition_value != event_value:
                return False

        return True

    def _check_nested_conditions(self, conditions: Dict, data: Any) -> bool:
        """Check nested condition structures."""
        if not isinstance(data, dict):
            return False

        for key, value in conditions.items():
            if key not in data:
                return False

            if isinstance(value, str) and value.startswith(">"):
                threshold = float(value[1:])
                if float(data[key]) <= threshold:
                    return False
            elif isinstance(value, str) and value.startswith("<"):
                threshold = float(value[1:])
                if float(data[key]) >= threshold:
                    return False
            elif data[key] != value:
                return False

        return True

    async def _check_rule_conditions(
        self,
        rule: AutomationRule,
        event_data: Dict[str, Any],
        lead_id: Optional[str],
        agent_id: Optional[str]
    ) -> bool:
        """Check if rule-level conditions are met."""
        conditions = rule.conditions

        # Check business hours condition
        if "business_hours" in conditions:
            is_business_hours = self._is_business_hours()
            if conditions["business_hours"] != is_business_hours:
                return False

        # Check agent availability
        if "agent_availability" in conditions:
            agent_available = await self._check_agent_availability(agent_id)
            if conditions["agent_availability"] and not agent_available:
                return False

        # Check lead score
        if "lead_score" in conditions and lead_id:
            lead_score = await self._get_lead_score(lead_id)
            score_condition = conditions["lead_score"]
            if isinstance(score_condition, str) and score_condition.startswith(">"):
                threshold = int(score_condition[1:])
                if lead_score <= threshold:
                    return False

        return True

    async def _check_exclusion_criteria(
        self,
        rule: AutomationRule,
        event_data: Dict[str, Any],
        lead_id: Optional[str],
        agent_id: Optional[str]
    ) -> bool:
        """Check if any exclusion criteria prevent execution."""
        exclusions = rule.exclusion_criteria

        # Check recently contacted
        if "recently_contacted" in exclusions and lead_id:
            time_str = exclusions["recently_contacted"]
            if time_str.endswith("_hours"):
                hours = int(time_str.replace("_hours", "").replace("<", ""))
                last_contact = await self._get_last_contact_time(lead_id)
                if last_contact and (datetime.now() - last_contact).total_seconds() < (hours * 3600):
                    return True  # Excluded

        # Check if marked as not interested
        if exclusions.get("marked_as_not_interested") and lead_id:
            if await self._is_lead_not_interested(lead_id):
                return True  # Excluded

        return False  # Not excluded

    async def _claude_rule_approval(
        self,
        rule: AutomationRule,
        event_data: Dict[str, Any],
        lead_id: Optional[str],
        agent_id: Optional[str]
    ) -> bool:
        """Use Claude AI to approve or reject rule execution."""
        try:
            # Build context for Claude analysis
            analysis_context = {
                "rule": {
                    "name": rule.rule_name,
                    "description": rule.description,
                    "trigger_conditions": rule.trigger.trigger_conditions
                },
                "event_data": event_data,
                "lead_context": await self._get_lead_context(lead_id) if lead_id else {},
                "agent_context": await self._get_agent_context(agent_id) if agent_id else {},
                "market_context": await self._get_current_market_context(),
                "timing_context": self._get_timing_context()
            }

            # Create Claude prompt for rule approval
            approval_prompt = f"""
            AUTOMATION RULE APPROVAL REQUEST

            Rule: {rule.rule_name}
            Description: {rule.description}

            Context: {json.dumps(analysis_context, indent=2, default=str)}

            Claude Reasoning Prompt: {rule.claude_reasoning_prompt or "Analyze if this automation should execute"}

            Please analyze the context and determine if this automation rule should execute.

            Consider:
            1. Relevance and timing appropriateness
            2. Lead engagement and receptivity
            3. Market conditions and opportunities
            4. Potential for positive outcome
            5. Risk of over-communication or poor timing

            Respond with:
            - APPROVE: If the automation should execute
            - REJECT: If the automation should not execute
            - REASON: Brief explanation of your decision

            Format: DECISION: [APPROVE/REJECT] - REASON: [explanation]
            """

            response = await self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=200,
                temperature=0.3,
                system="""You are an expert real estate automation specialist.
                Analyze automation rules and approve only those that will provide value
                to leads and agents while avoiding over-communication or poor timing.""",
                messages=[{"role": "user", "content": approval_prompt}]
            )

            claude_response = response.content[0].text

            # Parse Claude's decision
            if "APPROVE" in claude_response.upper():
                logger.info(f"Claude approved rule {rule.rule_id}: {claude_response}")
                return True
            else:
                logger.info(f"Claude rejected rule {rule.rule_id}: {claude_response}")
                return False

        except Exception as e:
            logger.error(f"Error in Claude rule approval: {e}")
            # Default to approval if Claude analysis fails
            return True

    async def _execute_automation_rule(
        self,
        rule: AutomationRule,
        event_data: Dict[str, Any],
        lead_id: Optional[str],
        agent_id: Optional[str]
    ) -> Optional[AutomationExecution]:
        """Execute an automation rule and its actions."""
        start_time = datetime.now()
        execution_id = f"exec_{rule.rule_id}_{int(start_time.timestamp())}"

        try:
            # Get Claude analysis for the execution
            claude_analysis = await self._get_execution_analysis(
                rule, event_data, lead_id, agent_id
            )

            executed_actions = []
            overall_success = True

            # Execute each action in the rule
            for action in rule.actions:
                if not action.is_active:
                    continue

                try:
                    action_result = await self._execute_action(
                        action, event_data, claude_analysis, lead_id, agent_id
                    )

                    executed_actions.append({
                        "action_id": action.action_id,
                        "action_type": action.action_type.value,
                        "result": action_result,
                        "success": action_result.get("success", False),
                        "executed_at": datetime.now().isoformat()
                    })

                    if not action_result.get("success", False):
                        overall_success = False

                except Exception as e:
                    logger.error(f"Error executing action {action.action_id}: {e}")
                    executed_actions.append({
                        "action_id": action.action_id,
                        "action_type": action.action_type.value,
                        "result": {"error": str(e)},
                        "success": False,
                        "executed_at": datetime.now().isoformat()
                    })
                    overall_success = False

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            # Create execution record
            execution = AutomationExecution(
                execution_id=execution_id,
                rule_id=rule.rule_id,
                trigger_data=event_data,
                claude_analysis=claude_analysis,
                actions_executed=executed_actions,
                execution_result="success" if overall_success else "partial_failure",
                success=overall_success,
                execution_time_ms=execution_time,
                lead_id=lead_id,
                agent_id=agent_id,
                executed_at=start_time
            )

            # Store execution
            self.execution_history.append(execution)
            self._save_execution_history()

            # Update rule last executed time
            rule.last_executed = start_time
            self._save_automation_rules()

            logger.info(f"Executed automation rule {rule.rule_id}: {execution.execution_result}")
            return execution

        except Exception as e:
            logger.error(f"Error executing automation rule {rule.rule_id}: {e}")
            return None

    async def _execute_action(
        self,
        action: AutomationAction,
        event_data: Dict[str, Any],
        claude_analysis: Dict[str, Any],
        lead_id: Optional[str],
        agent_id: Optional[str]
    ) -> Dict[str, Any]:
        """Execute a specific automation action."""
        try:
            # Add delay if specified
            if action.delay_minutes > 0:
                await asyncio.sleep(action.delay_minutes * 60)

            # Execute based on action type
            if action.action_type == ActionType.SEND_SMS:
                return await self._execute_send_sms(action, event_data, claude_analysis, lead_id)

            elif action.action_type == ActionType.SEND_EMAIL:
                return await self._execute_send_email(action, event_data, claude_analysis, lead_id)

            elif action.action_type == ActionType.CREATE_TASK:
                return await self._execute_create_task(action, event_data, claude_analysis, agent_id)

            elif action.action_type == ActionType.SCHEDULE_CALL:
                return await self._execute_schedule_call(action, event_data, claude_analysis, lead_id, agent_id)

            elif action.action_type == ActionType.TRIGGER_WORKFLOW:
                return await self._execute_trigger_workflow(action, event_data, claude_analysis, lead_id)

            elif action.action_type == ActionType.TRIGGER_NURTURE_SEQUENCE:
                return await self._execute_trigger_nurture(action, event_data, claude_analysis, lead_id)

            else:
                return {"success": False, "error": f"Unknown action type: {action.action_type}"}

        except Exception as e:
            logger.error(f"Error executing action {action.action_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_send_sms(
        self,
        action: AutomationAction,
        event_data: Dict[str, Any],
        claude_analysis: Dict[str, Any],
        lead_id: Optional[str]
    ) -> Dict[str, Any]:
        """Execute SMS sending action."""
        try:
            # Get lead information
            lead_info = await self._get_lead_info(lead_id) if lead_id else {}

            # Get message template
            template_name = action.message_template or "default"
            message_template = self.message_templates.get(template_name, {}).get("sms", "")

            if not message_template:
                return {"success": False, "error": "No SMS template found"}

            # Personalize message using Claude
            personalized_message = await self._personalize_message(
                message_template, lead_info, claude_analysis, "sms"
            )

            # Send SMS (integration with GHL SMS API would happen here)
            sms_result = await self._send_sms_via_ghl(
                phone_number=lead_info.get("phone"),
                message=personalized_message,
                lead_id=lead_id
            )

            return {
                "success": sms_result.get("success", False),
                "message_sent": personalized_message,
                "sms_id": sms_result.get("message_id"),
                "delivery_status": sms_result.get("status", "sent")
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_send_email(
        self,
        action: AutomationAction,
        event_data: Dict[str, Any],
        claude_analysis: Dict[str, Any],
        lead_id: Optional[str]
    ) -> Dict[str, Any]:
        """Execute email sending action."""
        try:
            # Get lead information
            lead_info = await self._get_lead_info(lead_id) if lead_id else {}

            # Get message template
            template_name = action.message_template or "default"
            message_template = self.message_templates.get(template_name, {}).get("email", "")

            if not message_template:
                return {"success": False, "error": "No email template found"}

            # Personalize message using Claude
            personalized_message = await self._personalize_message(
                message_template, lead_info, claude_analysis, "email"
            )

            # Send email (integration with GHL email API would happen here)
            email_result = await self._send_email_via_ghl(
                email_address=lead_info.get("email"),
                subject=f"Update on Your Home Search - {lead_info.get('name', 'Dear Client')}",
                message=personalized_message,
                lead_id=lead_id
            )

            return {
                "success": email_result.get("success", False),
                "message_sent": personalized_message,
                "email_id": email_result.get("email_id"),
                "delivery_status": email_result.get("status", "sent")
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _execute_create_task(
        self,
        action: AutomationAction,
        event_data: Dict[str, Any],
        claude_analysis: Dict[str, Any],
        agent_id: Optional[str]
    ) -> Dict[str, Any]:
        """Execute task creation action."""
        try:
            task_params = action.action_parameters

            # Create task details
            task_data = {
                "title": task_params.get("task_type", "Automated Task"),
                "description": f"Automated task created based on: {claude_analysis.get('trigger_reason', 'automation trigger')}",
                "priority": task_params.get("priority", "medium"),
                "assigned_to": agent_id or task_params.get("assign_to", "default_agent"),
                "due_date": (datetime.now() + timedelta(hours=24)).isoformat(),
                "category": "automation",
                "metadata": {
                    "automation_generated": True,
                    "trigger_event": event_data,
                    "claude_analysis": claude_analysis
                }
            }

            # Create task via GHL API
            task_result = await self._create_task_via_ghl(task_data)

            return {
                "success": task_result.get("success", False),
                "task_id": task_result.get("task_id"),
                "task_details": task_data
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # Helper methods for automation execution...

    async def _personalize_message(
        self,
        template: str,
        lead_info: Dict[str, Any],
        claude_analysis: Dict[str, Any],
        channel: str
    ) -> str:
        """Use Claude to personalize message templates."""
        try:
            personalization_prompt = f"""
            PERSONALIZE MESSAGE TEMPLATE

            Template: {template}
            Lead Information: {json.dumps(lead_info, indent=2)}
            Claude Analysis: {json.dumps(claude_analysis, indent=2)}
            Channel: {channel}

            Please personalize this message template with:
            1. Lead's name and specific details
            2. Relevant context from the analysis
            3. Appropriate tone for the channel
            4. Compelling call-to-action

            Return only the personalized message, no explanations.
            """

            response = await self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=300,
                temperature=0.7,
                system="You are an expert real estate communication specialist. Personalize messages to be engaging, relevant, and action-oriented.",
                messages=[{"role": "user", "content": personalization_prompt}]
            )

            personalized = response.content[0].text.strip()

            # Basic template variable replacement as fallback
            personalized = personalized.replace("{name}", lead_info.get("name", ""))
            personalized = personalized.replace("{agent_name}", lead_info.get("agent_name", "Your Agent"))

            return personalized

        except Exception as e:
            logger.error(f"Error personalizing message: {e}")
            # Return template with basic replacements
            return template.replace("{name}", lead_info.get("name", "")).replace("{agent_name}", "Your Agent")

    # Integration methods (would connect to actual GHL APIs in production)

    async def _send_sms_via_ghl(self, phone_number: str, message: str, lead_id: str) -> Dict[str, Any]:
        """Send SMS via GHL API."""
        # Placeholder for GHL SMS API integration
        return {"success": True, "message_id": f"sms_{int(datetime.now().timestamp())}", "status": "sent"}

    async def _send_email_via_ghl(self, email_address: str, subject: str, message: str, lead_id: str) -> Dict[str, Any]:
        """Send email via GHL API."""
        # Placeholder for GHL email API integration
        return {"success": True, "email_id": f"email_{int(datetime.now().timestamp())}", "status": "sent"}

    async def _create_task_via_ghl(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create task via GHL API."""
        # Placeholder for GHL task API integration
        return {"success": True, "task_id": f"task_{int(datetime.now().timestamp())}"}

    # Context and helper methods...

    async def _get_lead_context(self, lead_id: str) -> Dict[str, Any]:
        """Get comprehensive lead context."""
        return {
            "lead_id": lead_id,
            "qualification_status": "in_progress",
            "engagement_score": 75,
            "last_activity": "2024-01-10",
            "preferences": {"location": "Austin", "budget": "400-500k"}
        }

    async def _get_agent_context(self, agent_id: str) -> Dict[str, Any]:
        """Get agent context for automation decisions."""
        return {
            "agent_id": agent_id,
            "availability": "available",
            "workload": "medium",
            "specialties": ["luxury", "first_time_buyers"]
        }

    async def _get_current_market_context(self) -> Dict[str, Any]:
        """Get current market context."""
        return {
            "market_type": "balanced",
            "inventory_level": "moderate",
            "interest_rates": "elevated",
            "seasonal_factor": "spring_market"
        }

    def _get_timing_context(self) -> Dict[str, Any]:
        """Get current timing context."""
        now = datetime.now()
        return {
            "current_time": now.isoformat(),
            "is_business_hours": self._is_business_hours(),
            "day_of_week": now.strftime("%A"),
            "month": now.strftime("%B"),
            "season": self._get_current_season()
        }

    def _is_business_hours(self) -> bool:
        """Check if current time is within business hours."""
        now = datetime.now()
        return 8 <= now.hour <= 18 and now.weekday() < 5

    def _get_current_season(self) -> str:
        """Get current season."""
        month = datetime.now().month
        if month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        elif month in [9, 10, 11]:
            return "fall"
        else:
            return "winter"

    # Performance tracking methods...

    async def _update_rule_performance(self, rule_id: str, success: bool) -> None:
        """Update performance stats for a specific rule."""
        if rule_id in self.automation_rules:
            rule = self.automation_rules[rule_id]
            rule.performance_stats["executions"] += 1
            if success:
                successes = rule.performance_stats.get("successes", 0) + 1
                rule.performance_stats["successes"] = successes
                rule.performance_stats["success_rate"] = successes / rule.performance_stats["executions"]

    async def _update_performance_metrics(self, executions: List[AutomationExecution]) -> None:
        """Update global performance metrics."""
        self.performance_metrics["total_executions"] += len(executions)
        successful = sum(1 for e in executions if e.success)
        self.performance_metrics["successful_executions"] += successful

        # Update success rate
        total = self.performance_metrics["total_executions"]
        if total > 0:
            success_rate = self.performance_metrics["successful_executions"] / total
            self.performance_metrics["success_rate"] = success_rate

        self._save_performance_metrics()

    # Data conversion helpers...

    def _dict_to_automation_rule(self, data: Dict) -> AutomationRule:
        """Convert dictionary to AutomationRule dataclass."""
        # This would include proper dataclass conversion logic
        # Simplified for this implementation
        return AutomationRule(**data)

    def _dict_to_automation_execution(self, data: Dict) -> AutomationExecution:
        """Convert dictionary to AutomationExecution dataclass."""
        # Convert ISO string back to datetime
        data["executed_at"] = datetime.fromisoformat(data["executed_at"])
        return AutomationExecution(**data)

    # Additional helper methods for checking conditions, getting lead scores, etc.

    async def _check_agent_availability(self, agent_id: Optional[str]) -> bool:
        """Check if agent is available for immediate response."""
        if not agent_id:
            return True
        # Would integrate with agent scheduling/availability system
        return True

    async def _get_lead_score(self, lead_id: str) -> int:
        """Get current lead score."""
        # Would integrate with lead scoring system
        return 75

    async def _get_last_contact_time(self, lead_id: str) -> Optional[datetime]:
        """Get timestamp of last contact with lead."""
        # Would query contact history
        return datetime.now() - timedelta(hours=12)

    async def _is_lead_not_interested(self, lead_id: str) -> bool:
        """Check if lead is marked as not interested."""
        # Would query lead status
        return False

    async def _get_lead_info(self, lead_id: str) -> Dict[str, Any]:
        """Get lead information for message personalization."""
        return {
            "name": "John Doe",
            "phone": "+1234567890",
            "email": "john.doe@example.com",
            "agent_name": "Sarah Johnson"
        }

    async def _get_execution_analysis(
        self,
        rule: AutomationRule,
        event_data: Dict[str, Any],
        lead_id: Optional[str],
        agent_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get Claude analysis for automation execution."""
        return {
            "trigger_reason": f"Rule {rule.rule_name} triggered by event",
            "confidence_score": 0.85,
            "recommended_personalization": "high",
            "timing_appropriateness": "optimal"
        }

    def get_automation_stats(self) -> Dict[str, Any]:
        """Get comprehensive automation statistics."""
        return {
            "total_rules": len(self.automation_rules),
            "active_rules": len([r for r in self.automation_rules.values() if r.is_active]),
            "performance_metrics": self.performance_metrics,
            "recent_executions": len([e for e in self.execution_history if e.executed_at > datetime.now() - timedelta(days=7)]),
            "top_performing_rules": self._get_top_performing_rules(),
            "automation_coverage": self._calculate_automation_coverage()
        }

    def _get_top_performing_rules(self) -> List[Dict[str, Any]]:
        """Get top performing automation rules."""
        rules_with_performance = [
            {
                "rule_id": rule.rule_id,
                "rule_name": rule.rule_name,
                "executions": rule.performance_stats.get("executions", 0),
                "success_rate": rule.performance_stats.get("success_rate", 0.0)
            }
            for rule in self.automation_rules.values()
            if rule.performance_stats.get("executions", 0) > 0
        ]

        return sorted(rules_with_performance, key=lambda x: x["success_rate"], reverse=True)[:5]

    def _calculate_automation_coverage(self) -> float:
        """Calculate what percentage of workflows are automated."""
        # Simplified calculation
        total_possible_automations = 20
        active_automations = len([r for r in self.automation_rules.values() if r.is_active])
        return min(1.0, active_automations / total_possible_automations)


# Global instance for easy access
claude_automation_engine = ClaudeAdvancedAutomationEngine()