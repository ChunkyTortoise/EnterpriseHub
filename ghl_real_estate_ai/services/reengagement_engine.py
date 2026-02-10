"""
Enhanced Re-engagement Engine for Silent Leads & Churn Recovery.

ENHANCED: Now includes comprehensive churn recovery campaigns with CLV modeling.

Features:
- Time-based trigger detection (24h, 48h, 72h) for silent leads
- ENHANCED: Churn recovery campaign templates for confirmed churned leads
- ENHANCED: Customer Lifetime Value (CLV) based campaign selection
- SMS-compliant message templates (Jorge's direct tone)
- Integration with GHL client for sending
- Memory service integration for tracking
- ENHANCED: ChurnEventTracker integration for recovery workflow
- Prevents duplicate re-engagement attempts

Usage:
    engine = ReengagementEngine()

    # Traditional silent lead re-engagement
    silent_leads = await engine.scan_for_silent_leads()
    for lead in silent_leads:
        await engine.send_reengagement_message(
            contact_id=lead["contact_id"],
            contact_name=lead["contact_name"],
            context=lead["context"]
        )

    # ENHANCED: Churn recovery campaigns
    recovery_leads = await engine.scan_for_recovery_eligible_leads()
    for lead in recovery_leads:
        await engine.send_recovery_campaign(
            contact_id=lead["contact_id"],
            churn_reason=lead["churn_reason"],
            clv_estimate=lead["clv_estimate"]
        )
"""

import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.api.schemas.ghl import MessageType
from ghl_real_estate_ai.core.llm_client import LLMClient
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.prompts.reengagement_templates import get_reengagement_message
from ghl_real_estate_ai.services.analytics_service import AnalyticsService

# ENHANCED: Import ChurnEventTracker for recovery workflow integration
from ghl_real_estate_ai.services.churn_prediction_engine import (
    ChurnEventTracker,
    ChurnReason,
)
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.memory_service import MemoryService

logger = get_logger(__name__)


class ReengagementTrigger(Enum):
    """Re-engagement trigger levels based on time elapsed."""

    HOURS_24 = "24h"
    HOURS_48 = "48h"
    HOURS_72 = "72h"


# ============================================================================
# ENHANCED: Recovery Campaign System for Churned Leads
# ============================================================================


class RecoveryCampaignType(Enum):
    """Recovery campaign types for churned leads based on churn reason and CLV."""

    WIN_BACK_AGGRESSIVE = "win_back_aggressive"  # High CLV, recoverable reasons
    WIN_BACK_NURTURE = "win_back_nurture"  # Medium CLV, timing/budget issues
    MARKET_COMEBACK = "market_comeback"  # Market condition related churn
    VALUE_PROPOSITION = "value_proposition"  # Competition/service related churn
    FINAL_ATTEMPT = "final_attempt"  # Last attempt before permanent churn


class CLVTier(Enum):
    """Customer Lifetime Value tiers for campaign prioritization."""

    HIGH_VALUE = "high_value"  # $50K+ potential commission value
    MEDIUM_VALUE = "medium_value"  # $20K-50K potential commission value
    LOW_VALUE = "low_value"  # <$20K potential commission value


@dataclass
class RecoveryCampaignTemplate:
    """Recovery campaign template with CLV-based messaging."""

    campaign_type: RecoveryCampaignType
    target_clv_tier: CLVTier
    target_reasons: List[ChurnReason]

    # Message templates by channel
    sms_template: str
    email_subject: str
    email_template: str

    # Campaign timing
    delay_hours: int  # Hours after churn event
    max_attempts: int

    # Success metrics
    expected_recovery_rate: float
    roi_threshold: float


@dataclass
class CLVEstimate:
    """Customer Lifetime Value estimate for recovery decision making."""

    lead_id: str
    estimated_transaction_value: float
    commission_rate: float = 0.03  # 3% typical real estate commission
    probability_multiplier: float = 1.0  # Probability of conversion

    @property
    def estimated_clv(self) -> float:
        """Calculate estimated CLV."""
        return self.estimated_transaction_value * self.commission_rate * self.probability_multiplier

    @property
    def clv_tier(self) -> CLVTier:
        """Determine CLV tier for campaign selection."""
        clv = self.estimated_clv
        if clv >= 50000:
            return CLVTier.HIGH_VALUE
        elif clv >= 20000:
            return CLVTier.MEDIUM_VALUE
        else:
            return CLVTier.LOW_VALUE


class ReengagementEngine:
    """
    Engine for detecting and re-engaging silent leads.

    Monitors conversation history and triggers automated re-engagement
    messages at 24h, 48h, and 72h intervals.
    """

    def __init__(
        self,
        ghl_client: Optional[GHLClient] = None,
        memory_service: Optional[MemoryService] = None,
        churn_event_tracker: Optional[ChurnEventTracker] = None,
    ):
        """
        Initialize enhanced re-engagement engine with recovery capabilities.

        Args:
            ghl_client: GHL API client (creates new if not provided)
            memory_service: Memory service for tracking conversations
            churn_event_tracker: ENHANCED: ChurnEventTracker for recovery workflow
        """
        self.ghl_client = ghl_client or GHLClient()
        self.memory_service = memory_service or MemoryService(storage_type="file")
        self.llm_client = LLMClient(provider="claude", model=settings.claude_model)
        self.analytics = AnalyticsService()

        # ENHANCED: Initialize ChurnEventTracker for recovery campaigns
        self.churn_tracker = churn_event_tracker or ChurnEventTracker(self.memory_service)

        # ENHANCED: Load recovery campaign templates
        self.recovery_templates = self._load_recovery_campaign_templates()

    async def detect_trigger(self, context: Dict[str, Any]) -> Optional[ReengagementTrigger]:
        """
        Detect if a lead needs re-engagement based on time elapsed.

        Args:
            context: Conversation context from memory service

        Returns:
            ReengagementTrigger if action needed, None otherwise

        Logic:
            - 24-48h: Send first re-engagement (24h)
            - 48-72h: Send second re-engagement (48h)
            - 72h+: Send final re-engagement (72h)
            - Already sent same trigger: Skip to prevent duplicates
        """
        # Get last interaction timestamp
        last_interaction_str = context.get("last_interaction_at")
        if not last_interaction_str:
            logger.warning(f"No last_interaction_at for contact {context.get('contact_id')}")
            return None

        try:
            last_interaction = datetime.fromisoformat(last_interaction_str)
        except (ValueError, TypeError) as e:
            logger.error(f"Invalid timestamp format: {last_interaction_str}, error: {e}")
            return None

        # Calculate hours since last interaction
        now = datetime.utcnow()
        hours_elapsed = (now - last_interaction).total_seconds() / 3600

        # Get last re-engagement trigger (if any) to prevent duplicates
        last_trigger = context.get("last_reengagement_trigger")

        # Determine trigger level
        if hours_elapsed >= 72:
            # 72h+ trigger (final attempt)
            if last_trigger == ReengagementTrigger.HOURS_72.value:
                logger.info(f"72h trigger already sent for {context.get('contact_id')}")
                return None
            return ReengagementTrigger.HOURS_72

        elif hours_elapsed >= 48:
            # 48-72h trigger
            if last_trigger in [
                ReengagementTrigger.HOURS_48.value,
                ReengagementTrigger.HOURS_72.value,
            ]:
                logger.info(f"48h trigger already sent for {context.get('contact_id')}")
                return None
            return ReengagementTrigger.HOURS_48

        elif hours_elapsed >= 24:
            # 24-48h trigger
            if last_trigger:
                # Already sent any re-engagement, skip 24h
                logger.info(f"24h trigger already sent for {context.get('contact_id')}")
                return None
            return ReengagementTrigger.HOURS_24

        else:
            # Less than 24h, no trigger
            return None

    async def agentic_reengagement(self, contact_name: str, context: Dict[str, Any]) -> str:
        """
        🆕 Phase 4: Sentiment-Aware Recovery
        Uses Claude to generate a personalized re-engagement message based on history.
        """
        history = context.get("conversation_history", [])
        preferences = context.get("extracted_preferences", {})

        prompt = f"""You are a senior Real Estate Concierge on Jorge's team. A lead has gone silent and you need to re-engage them.

LEAD NAME: {contact_name}
CONVERSATION HISTORY:
{json.dumps(history[-5:], indent=2)}

LEAD PREFERENCES:
{json.dumps(preferences, indent=2)}

YOUR GOAL:
1. Reference a specific detail from their preferences (e.g. their budget or a specific neighborhood).
2. Maintain a professional, direct, and non-pushy tone.
3. Provide a clear "Value Hook" (e.g. "I found a new match in Downtown" or "I wanted to see if your timeline shifted").
4. Keep it under 160 characters for SMS.

Example: "Hi {contact_name}, I just saw a new 3-bed in Austin that hits your $500k target. Still looking to move next month? - Jorge's team"
"""
        try:
            response = await self.llm_client.agenerate(
                prompt=prompt,
                system_prompt="You are an expert Real Estate Concierge. Be direct, helpful, and concise.",
                temperature=0.7,
                max_tokens=150,
            )

            # Record usage
            location_id = context.get("location_id", "unknown")
            await self.analytics.track_llm_usage(
                location_id=location_id,
                model=response.model,
                provider=response.provider.value,
                input_tokens=response.input_tokens or 0,
                output_tokens=response.output_tokens or 0,
                cached=False,
                contact_id=context.get("contact_id"),
            )

            return response.content.strip()
        except Exception as e:
            logger.error(f"Agentic re-engagement failed: {e}")
            # Fallback to standard template logic (will be handled by caller)
            return ""

    def get_message_for_trigger(
        self,
        trigger: ReengagementTrigger,
        contact_name: str,
        action: Optional[str] = None,
        is_buyer: Optional[bool] = None,
        is_seller: Optional[bool] = None,
    ) -> str:
        """
        Get re-engagement message for specific trigger.

        Args:
            trigger: Trigger level (24h, 48h, 72h)
            contact_name: Lead's first name
            action: Action verb (e.g., "buy", "sell")
            is_buyer: True if lead is buying
            is_seller: True if lead is selling

        Returns:
            SMS-compliant re-engagement message (<160 chars)
        """
        return get_reengagement_message(
            trigger_level=trigger.value,
            contact_name=contact_name,
            action=action,
            is_buyer=is_buyer,
            is_seller=is_seller,
        )

    def _determine_lead_goal(self, context: Dict[str, Any]) -> tuple[Optional[str], Optional[bool], Optional[bool]]:
        """
        Determine lead's goal (buy/sell) from context.

        Args:
            context: Conversation context

        Returns:
            Tuple of (action, is_buyer, is_seller)
        """
        preferences = context.get("extracted_preferences", {})
        goal = preferences.get("goal", "").lower()

        if "buy" in goal:
            return "buy", True, False
        elif "sell" in goal:
            return "sell", False, True
        else:
            # Try to infer from conversation history
            history = context.get("conversation_history", [])
            for msg in history:
                content = msg.get("content", "").lower()
                if any(word in content for word in ["buy", "buying", "purchase"]):
                    return "buy", True, False
                elif any(word in content for word in ["sell", "selling", "list"]):
                    return "sell", False, True

        # Default to general
        return None, None, None

    async def send_reengagement_message(
        self, contact_id: str, contact_name: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Send re-engagement message to a silent lead.

        Args:
            contact_id: GHL contact ID
            contact_name: Lead's first name
            context: Conversation context

        Returns:
            GHL API response if sent, None if no trigger detected
        """
        # Detect trigger
        trigger = await self.detect_trigger(context)
        if not trigger:
            logger.info(f"No re-engagement trigger for {contact_id}")
            return None

        # Determine lead goal
        action, is_buyer, is_seller = self._determine_lead_goal(context)

        # Try agentic message first (Phase 4)
        message = await self.agentic_reengagement(contact_name, context)

        # Fallback to template if agentic fails or returns empty
        if not message:
            message = self.get_message_for_trigger(
                trigger=trigger,
                contact_name=contact_name,
                action=action,
                is_buyer=is_buyer,
                is_seller=is_seller,
            )

        logger.info(
            f"Sending {trigger.value} re-engagement to {contact_id}: {message}",
            extra={"contact_id": contact_id, "trigger": trigger.value},
        )

        # Send via GHL
        try:
            result = await self.ghl_client.send_message(contact_id=contact_id, message=message, channel=MessageType.SMS)

            # Update context to track re-engagement
            context["last_reengagement_trigger"] = trigger.value
            context["last_reengagement_at"] = datetime.utcnow().isoformat()

            # Save updated context
            await self.memory_service.save_context(
                contact_id=contact_id,
                context=context,
                location_id=context.get("location_id"),
            )

            logger.info(
                f"Successfully sent {trigger.value} re-engagement to {contact_id}",
                extra={
                    "contact_id": contact_id,
                    "trigger": trigger.value,
                    "message_id": result.get("messageId"),
                },
            )

            return result

        except Exception as e:
            logger.error(
                f"Failed to send re-engagement to {contact_id}: {str(e)}",
                extra={"contact_id": contact_id, "error": str(e)},
            )
            return None

    async def scan_for_silent_leads(self, memory_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Scan memory service for silent leads that need re-engagement.

        Args:
            memory_dir: Directory to scan (defaults to data/memory)

        Returns:
            List of silent lead dicts with contact_id, context, and trigger
        """
        if memory_dir is None:
            memory_dir = Path("data/memory")

        if not memory_dir.exists():
            logger.warning(f"Memory directory does not exist: {memory_dir}")
            return []

        silent_leads = []

        # Scan all memory files
        for file_path in memory_dir.glob("**/*.json"):
            try:
                with open(file_path, "r") as f:
                    context = json.load(f)

                contact_id = context.get("contact_id")
                if not contact_id:
                    continue

                # Check if trigger detected
                trigger = await self.detect_trigger(context)
                if trigger:
                    # Extract contact name from context or conversation
                    contact_name = self._extract_contact_name(context)

                    silent_leads.append(
                        {
                            "contact_id": contact_id,
                            "contact_name": contact_name,
                            "context": context,
                            "trigger": trigger,
                            "hours_since_interaction": self._calculate_hours_since(context),
                        }
                    )

            except Exception as e:
                logger.error(f"Error scanning {file_path}: {str(e)}")
                continue

        logger.info(f"Scanned {memory_dir}, found {len(silent_leads)} silent leads")

        return silent_leads

    def _extract_contact_name(self, context: Dict[str, Any]) -> str:
        """Extract contact name from context or default to 'there'."""
        # Try extracted preferences first
        preferences = context.get("extracted_preferences", {})
        if "name" in preferences:
            return preferences["name"]

        # Try conversation history
        history = context.get("conversation_history", [])
        for msg in history:
            if msg.get("role") == "user":
                content = msg.get("content", "")
                # Simple name extraction: "my name is X"
                if "name is" in content.lower():
                    parts = content.lower().split("name is")
                    if len(parts) > 1:
                        name_candidate = parts[1].strip().split()[0]
                        return name_candidate.capitalize()

        # Default
        return "there"

    def _calculate_hours_since(self, context: Dict[str, Any]) -> float:
        """Calculate hours since last interaction."""
        last_interaction_str = context.get("last_interaction_at")
        if not last_interaction_str:
            return 0.0

        try:
            last_interaction = datetime.fromisoformat(last_interaction_str)
            now = datetime.utcnow()
            return (now - last_interaction).total_seconds() / 3600
        except (ValueError, TypeError):
            return 0.0

    async def process_all_silent_leads(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Process all silent leads and send re-engagement messages.

        Args:
            dry_run: If True, only detect but don't send messages

        Returns:
            Summary dict with counts and results
        """
        silent_leads = await self.scan_for_silent_leads()

        summary = {
            "total_scanned": len(silent_leads),
            "messages_sent": 0,
            "errors": 0,
            "dry_run": dry_run,
            "results": [],
        }

        for lead in silent_leads:
            contact_id = lead["contact_id"]
            contact_name = lead["contact_name"]
            context = lead["context"]
            trigger = lead["trigger"]

            if dry_run:
                logger.info(
                    f"[DRY RUN] Would send {trigger.value} to {contact_id} ({contact_name})",
                    extra={"contact_id": contact_id, "trigger": trigger.value},
                )
                summary["results"].append(
                    {
                        "contact_id": contact_id,
                        "trigger": trigger.value,
                        "status": "dry_run",
                    }
                )
            else:
                result = await self.send_reengagement_message(
                    contact_id=contact_id, contact_name=contact_name, context=context
                )

                if result:
                    summary["messages_sent"] += 1
                    summary["results"].append(
                        {
                            "contact_id": contact_id,
                            "trigger": trigger.value,
                            "status": "sent",
                            "message_id": result.get("messageId"),
                        }
                    )
                else:
                    summary["errors"] += 1
                    summary["results"].append(
                        {
                            "contact_id": contact_id,
                            "trigger": trigger.value,
                            "status": "error",
                        }
                    )

        logger.info(
            f"Re-engagement batch complete: {summary['messages_sent']} sent, {summary['errors']} errors",
            extra=summary,
        )

        return summary

    # ============================================================================
    # ENHANCED: Recovery Campaign Methods for Churned Leads
    # ============================================================================

    def _load_recovery_campaign_templates(self) -> List[RecoveryCampaignTemplate]:
        """Load recovery campaign templates based on churn reason and CLV."""
        return [
            # High-value aggressive win-back campaigns
            RecoveryCampaignTemplate(
                campaign_type=RecoveryCampaignType.WIN_BACK_AGGRESSIVE,
                target_clv_tier=CLVTier.HIGH_VALUE,
                target_reasons=[ChurnReason.TIMING, ChurnReason.BUDGET],
                sms_template="Hi {name}, Jorge here. I know the timing wasn't right before, but I just found an exclusive property that fits your {budget} budget perfectly. Worth a quick look? 📱 {phone}",
                email_subject="Exclusive {location} property just hit the market - Perfect for your budget",
                email_template="""Hi {name},

I've been keeping an eye on the market for you since we last spoke.

A stunning {bedrooms}-bedroom home just became available in {preferred_area} for ${price_formatted} - right in your target range.

Given what you mentioned about wanting to move when the timing was right, this might be exactly what you've been waiting for.

I can get you a private showing today before it hits the general market.

What do you think?

Best regards,
Jorge's Team""",
                delay_hours=48,  # 2 days after churn
                max_attempts=3,
                expected_recovery_rate=0.35,
                roi_threshold=5000.0,
            ),
            RecoveryCampaignTemplate(
                campaign_type=RecoveryCampaignType.WIN_BACK_NURTURE,
                target_clv_tier=CLVTier.MEDIUM_VALUE,
                target_reasons=[ChurnReason.BUDGET, ChurnReason.MARKET_CONDITIONS],
                sms_template="Hi {name}, market conditions have shifted in your favor! New programs available that could save you $15K+. Quick call? - Jorge",
                email_subject="Market update: New opportunities in {location}",
                email_template="""Hi {name},

You mentioned concerns about the market when we last spoke.

Good news: Things have shifted significantly in buyers' favor over the past month:

• Interest rates dropped 0.3%
• New first-time buyer programs launched
• {location} inventory increased 15%

These changes could save you thousands on the property you wanted.

Would you like me to run the new numbers for you?

No pressure - just thought you'd want to know.

Jorge's Team""",
                delay_hours=168,  # 1 week after churn
                max_attempts=2,
                expected_recovery_rate=0.25,
                roi_threshold=3000.0,
            ),
            RecoveryCampaignTemplate(
                campaign_type=RecoveryCampaignType.MARKET_COMEBACK,
                target_clv_tier=CLVTier.HIGH_VALUE,
                target_reasons=[ChurnReason.MARKET_CONDITIONS, ChurnReason.PROPERTY_MISMATCH],
                sms_template="{name}, that property you loved in {neighborhood}? Similar one just listed at $30K less. Interested? - Jorge",
                email_subject="The {neighborhood} opportunity you've been waiting for",
                email_template="""Hi {name},

Remember that {property_type} in {neighborhood} you were interested in before market conditions changed?

A virtually identical property just came on the market at ${price_formatted} - that's $30,000 less than what we were looking at before.

Same school district, same floor plan, even better lot.

If you're still interested in the area, this could be the perfect opportunity.

Let me know if you'd like the details.

Jorge's Team""",
                delay_hours=72,  # 3 days after churn
                max_attempts=2,
                expected_recovery_rate=0.40,
                roi_threshold=8000.0,
            ),
            RecoveryCampaignTemplate(
                campaign_type=RecoveryCampaignType.VALUE_PROPOSITION,
                target_clv_tier=CLVTier.HIGH_VALUE,
                target_reasons=[ChurnReason.COMPETITOR, ChurnReason.COMMUNICATION],
                sms_template="Hi {name}, I hear you went with another agent. No hard feelings! If anything changes, you know where to find me. Good luck! - Jorge",
                email_subject="Thank you and good luck with your home search",
                email_template="""Hi {name},

I heard you decided to work with another agent for your home search.

No hard feelings at all - finding the right agent fit is important, and I respect your decision.

If anything changes or you need a second opinion on anything real estate related, you know where to find me.

Wishing you the best with your home search!

Jorge's Team

P.S. - I'll keep an eye out for any exceptional properties in {preferred_area}, just in case.""",
                delay_hours=336,  # 2 weeks after churn
                max_attempts=1,
                expected_recovery_rate=0.15,
                roi_threshold=1000.0,
            ),
            RecoveryCampaignTemplate(
                campaign_type=RecoveryCampaignType.FINAL_ATTEMPT,
                target_clv_tier=CLVTier.MEDIUM_VALUE,
                target_reasons=[ChurnReason.UNRESPONSIVE, ChurnReason.OTHER],
                sms_template="Hi {name}, checking if you're still looking for a home in {location}? If not, I'll remove you from my updates. Just reply YES/NO. Thanks! - Jorge",
                email_subject="Final check: Still searching for a home?",
                email_template="""Hi {name},

I wanted to check one last time if you're still looking for a home in the {location} area.

If you are, I'd love to help find the right property for you.

If your plans have changed, just let me know and I'll remove you from my property updates.

Either way is totally fine - I just want to respect your time and inbox.

Thanks!
Jorge's Team""",
                delay_hours=720,  # 30 days after churn
                max_attempts=1,
                expected_recovery_rate=0.10,
                roi_threshold=500.0,
            ),
        ]

    async def calculate_clv_estimate(self, contact_id: str, context: Dict[str, Any]) -> CLVEstimate:
        """
        Calculate Customer Lifetime Value estimate for recovery campaign selection.

        Args:
            contact_id: Lead identifier
            context: Conversation context with preferences

        Returns:
            CLVEstimate with calculated CLV and tier
        """
        try:
            preferences = context.get("extracted_preferences", {})

            # Extract budget/price range from preferences
            budget_str = preferences.get("budget", "").lower()
            estimated_transaction_value = 500000  # Default

            # Parse budget range
            if "k" in budget_str or "$" in budget_str:
                import re

                numbers = re.findall(r"\d+", budget_str)
                if numbers:
                    # Take the higher number if range, single number if just one
                    budget_value = int(numbers[-1])
                    if "k" in budget_str:
                        budget_value *= 1000
                    estimated_transaction_value = budget_value

            # Adjust probability based on engagement level
            engagement_history = context.get("conversation_history", [])
            engagement_count = len(engagement_history)

            # More engagement = higher probability
            if engagement_count >= 10:
                probability_multiplier = 1.2
            elif engagement_count >= 5:
                probability_multiplier = 1.0
            else:
                probability_multiplier = 0.8

            return CLVEstimate(
                lead_id=contact_id,
                estimated_transaction_value=estimated_transaction_value,
                probability_multiplier=probability_multiplier,
            )

        except Exception as e:
            logger.error(f"Error calculating CLV for {contact_id}: {str(e)}")
            # Return conservative estimate
            return CLVEstimate(lead_id=contact_id, estimated_transaction_value=400000, probability_multiplier=0.8)

    def select_recovery_campaign(
        self, churn_reason: ChurnReason, clv_estimate: CLVEstimate
    ) -> Optional[RecoveryCampaignTemplate]:
        """
        Select appropriate recovery campaign template based on churn reason and CLV.

        Args:
            churn_reason: Reason for churn
            clv_estimate: CLV estimate for campaign selection

        Returns:
            Best matching recovery campaign template
        """
        # Filter templates by CLV tier and churn reason compatibility
        compatible_templates = []

        for template in self.recovery_templates:
            # Check if CLV tier matches or is compatible
            clv_compatible = template.target_clv_tier == clv_estimate.clv_tier or (
                template.target_clv_tier == CLVTier.HIGH_VALUE and clv_estimate.clv_tier == CLVTier.MEDIUM_VALUE
            )

            # Check if churn reason matches
            reason_compatible = churn_reason in template.target_reasons

            # Check if ROI threshold makes sense
            roi_compatible = clv_estimate.estimated_clv >= template.roi_threshold

            if clv_compatible and reason_compatible and roi_compatible:
                compatible_templates.append(template)

        if not compatible_templates:
            # Fallback to final attempt if no perfect match
            fallback_templates = [
                t for t in self.recovery_templates if t.campaign_type == RecoveryCampaignType.FINAL_ATTEMPT
            ]
            return fallback_templates[0] if fallback_templates else None

        # Select the template with highest expected recovery rate
        return max(compatible_templates, key=lambda t: t.expected_recovery_rate)

    async def scan_for_recovery_eligible_leads(self) -> List[Dict[str, Any]]:
        """
        Scan for leads eligible for recovery campaigns.

        Returns:
            List of recovery-eligible leads with churn data and CLV estimates
        """
        try:
            recovery_leads = []

            # Get all churn events from tracker
            for contact_id in self.churn_tracker._events_cache.keys():
                events = await self.churn_tracker.get_churn_events(contact_id)

                for event in events:
                    # Check eligibility for recovery
                    (
                        is_eligible,
                        eligibility_status,
                        attempts_remaining,
                    ) = await self.churn_tracker.check_recovery_eligibility(contact_id)

                    if is_eligible and attempts_remaining > 0:
                        # Get context for CLV calculation
                        try:
                            context = await self.memory_service.get_context(contact_id)
                        except Exception:
                            context = {}

                        # Calculate CLV estimate
                        clv_estimate = await self.calculate_clv_estimate(contact_id, context)

                        # Select appropriate campaign
                        campaign_template = self.select_recovery_campaign(
                            event.churn_reason or ChurnReason.OTHER, clv_estimate
                        )

                        if campaign_template:
                            recovery_leads.append(
                                {
                                    "contact_id": contact_id,
                                    "contact_name": self._extract_contact_name(context),
                                    "churn_event": event,
                                    "churn_reason": event.churn_reason,
                                    "clv_estimate": clv_estimate,
                                    "campaign_template": campaign_template,
                                    "attempts_remaining": attempts_remaining,
                                    "context": context,
                                }
                            )

            logger.info(f"Found {len(recovery_leads)} recovery-eligible leads")
            return recovery_leads

        except Exception as e:
            logger.error(f"Error scanning for recovery eligible leads: {str(e)}")
            return []

    async def send_recovery_campaign(
        self,
        contact_id: str,
        churn_reason: ChurnReason,
        clv_estimate: CLVEstimate,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Send recovery campaign to a churned lead.

        Args:
            contact_id: Lead identifier
            churn_reason: Reason for churn
            clv_estimate: CLV estimate
            context: Optional conversation context

        Returns:
            Send result or None if failed
        """
        try:
            if context is None:
                context = await self.memory_service.get_context(contact_id)

            # Select campaign template
            campaign_template = self.select_recovery_campaign(churn_reason, clv_estimate)
            if not campaign_template:
                logger.warning(f"No suitable recovery campaign template for {contact_id}")
                return None

            # Generate campaign ID
            campaign_id = f"recovery_{contact_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Record recovery attempt with churn tracker
            attempt_recorded = await self.churn_tracker.record_recovery_attempt(contact_id, campaign_id)
            if not attempt_recorded:
                logger.warning(f"Recovery attempt could not be recorded for {contact_id} - not eligible or exhausted")
                return None

            # Extract personalization data from context
            preferences = context.get("extracted_preferences", {})
            contact_name = self._extract_contact_name(context)

            # Personalize message
            message = self._personalize_recovery_message(campaign_template.sms_template, contact_name, preferences)

            # Send via GHL
            result = await self.ghl_client.send_message(contact_id=contact_id, message=message, channel=MessageType.SMS)

            # Update context
            context["last_recovery_campaign"] = {
                "campaign_id": campaign_id,
                "campaign_type": campaign_template.campaign_type.value,
                "sent_at": datetime.utcnow().isoformat(),
                "clv_tier": clv_estimate.clv_tier.value,
                "estimated_clv": clv_estimate.estimated_clv,
            }

            await self.memory_service.save_context(
                contact_id=contact_id,
                context=context,
                location_id=context.get("location_id"),
            )

            logger.info(
                f"Recovery campaign {campaign_template.campaign_type.value} sent to {contact_id}",
                extra={
                    "contact_id": contact_id,
                    "campaign_id": campaign_id,
                    "campaign_type": campaign_template.campaign_type.value,
                    "clv_tier": clv_estimate.clv_tier.value,
                    "estimated_clv": clv_estimate.estimated_clv,
                },
            )

            return result

        except Exception as e:
            logger.error(f"Failed to send recovery campaign to {contact_id}: {str(e)}")
            return None

    def _personalize_recovery_message(self, template: str, contact_name: str, preferences: Dict[str, Any]) -> str:
        """
        Personalize recovery message template with lead preferences.

        Args:
            template: Message template
            contact_name: Lead name
            preferences: Extracted preferences

        Returns:
            Personalized message
        """
        # Basic personalization mapping
        personalization = {
            "name": contact_name,
            "budget": preferences.get("budget", "your budget"),
            "location": preferences.get("location", "your area"),
            "preferred_area": preferences.get("preferred_area", "your preferred area"),
            "neighborhood": preferences.get("neighborhood", "your neighborhood"),
            "bedrooms": preferences.get("bedrooms", "3"),
            "property_type": preferences.get("property_type", "home"),
            "phone": settings.jorge_phone if hasattr(settings, "jorge_phone") else "(555) 123-4567",
            "price_formatted": "TBD",  # Would be filled with actual property price
        }

        # Replace placeholders
        try:
            return template.format(**personalization)
        except KeyError as e:
            logger.warning(f"Missing personalization key: {e}")
            # Return template with basic substitutions
            return template.replace("{name}", contact_name)

    async def process_all_recovery_campaigns(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Process all recovery-eligible leads and send campaigns.

        Args:
            dry_run: If True, only detect but don't send campaigns

        Returns:
            Summary dict with counts and results
        """
        recovery_leads = await self.scan_for_recovery_eligible_leads()

        summary = {
            "total_scanned": len(recovery_leads),
            "campaigns_sent": 0,
            "errors": 0,
            "dry_run": dry_run,
            "clv_breakdown": {"high": 0, "medium": 0, "low": 0},
            "campaign_types": {},
            "results": [],
        }

        for lead in recovery_leads:
            contact_id = lead["contact_id"]
            clv_estimate = lead["clv_estimate"]
            campaign_template = lead["campaign_template"]
            context = lead["context"]

            # Update CLV breakdown
            summary["clv_breakdown"][clv_estimate.clv_tier.value.replace("_value", "")] += 1

            # Update campaign type breakdown
            campaign_type = campaign_template.campaign_type.value
            summary["campaign_types"][campaign_type] = summary["campaign_types"].get(campaign_type, 0) + 1

            if dry_run:
                logger.info(
                    f"[DRY RUN] Would send {campaign_type} recovery to {contact_id} (CLV: ${clv_estimate.estimated_clv:,.0f})"
                )
                summary["results"].append(
                    {
                        "contact_id": contact_id,
                        "campaign_type": campaign_type,
                        "clv_tier": clv_estimate.clv_tier.value,
                        "estimated_clv": clv_estimate.estimated_clv,
                        "status": "dry_run",
                    }
                )
            else:
                result = await self.send_recovery_campaign(
                    contact_id=contact_id,
                    churn_reason=lead["churn_reason"] or ChurnReason.OTHER,
                    clv_estimate=clv_estimate,
                    context=context,
                )

                if result:
                    summary["campaigns_sent"] += 1
                    summary["results"].append(
                        {
                            "contact_id": contact_id,
                            "campaign_type": campaign_type,
                            "clv_tier": clv_estimate.clv_tier.value,
                            "estimated_clv": clv_estimate.estimated_clv,
                            "status": "sent",
                            "message_id": result.get("messageId"),
                        }
                    )
                else:
                    summary["errors"] += 1
                    summary["results"].append(
                        {
                            "contact_id": contact_id,
                            "campaign_type": campaign_type,
                            "clv_tier": clv_estimate.clv_tier.value,
                            "estimated_clv": clv_estimate.estimated_clv,
                            "status": "error",
                        }
                    )

        logger.info(
            f"Recovery campaign batch complete: {summary['campaigns_sent']} sent, {summary['errors']} errors",
            extra=summary,
        )

        return summary


# ==============================================================================
# CLI INTERFACE
# ==============================================================================


async def main():
    """CLI interface for testing re-engagement engine."""
    import sys

    engine = ReengagementEngine()

    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        print("Scanning for silent leads...")
        silent_leads = await engine.scan_for_silent_leads()
        print(f"\nFound {len(silent_leads)} silent leads:")

        for lead in silent_leads:
            print(f"\n  Contact ID: {lead['contact_id']}")
            print(f"  Name: {lead['contact_name']}")
            print(f"  Trigger: {lead['trigger'].value}")
            print(f"  Hours since interaction: {lead['hours_since_interaction']:.1f}h")

    elif len(sys.argv) > 1 and sys.argv[1] == "process":
        dry_run = "--dry-run" in sys.argv
        print(f"Processing silent leads (dry_run={dry_run})...")

        summary = await engine.process_all_silent_leads(dry_run=dry_run)

        print(f"\nSummary:")
        print(f"  Total scanned: {summary['total_scanned']}")
        print(f"  Messages sent: {summary['messages_sent']}")
        print(f"  Errors: {summary['errors']}")

    else:
        print("Usage:")
        print("  python services/reengagement_engine.py scan")
        print("  python services/reengagement_engine.py process [--dry-run]")


if __name__ == "__main__":
    asyncio.run(main())
