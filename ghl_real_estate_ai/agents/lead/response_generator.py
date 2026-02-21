"""
Response Generator for constructing lead bot messages.
"""

from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.agents.lead.constants import MILESTONE_MESSAGES
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class ResponseGenerator:
    """Generates and constructs lead bot responses"""

    @staticmethod
    def _apply_tone_variant(message: str, tone: str = "empathetic") -> str:
        """
        Apply tone variant transformations to a message.

        Args:
            message: Base message text
            tone: One of "formal", "casual", "empathetic"

        Returns:
            Message with tone-appropriate adjustments
        """
        if tone == "formal":
            # More professional, structured language
            message = message.replace("Hey", "Hello")
            message = message.replace("Hi ", "Hello ")  # Add space to avoid partial matches
            message = message.replace("hope you're doing well!", "I trust this finds you well.")
            message = message.replace("hope you're doing well", "I trust this finds you well")
            message = message.replace("Any questions", "Should you have any questions")
            message = message.replace("want me to", "I would be happy to")
            message = message.replace("Let me know", "Please let me know")
            message = message.replace("Happy to", "I would be happy to")

        elif tone == "casual":
            # Relaxed, conversational language
            message = message.replace("Hi ", "Hey ")  # Add space to avoid partial matches
            message = message.replace("Hello", "Hey")
            message = message.replace("I trust this finds you well", "Hope you're doing great")
            message = message.replace("Should you have any questions", "Got any questions")
            message = message.replace("Any questions", "Any questions")  # Keep casual
            message = message.replace("I would be happy to", "happy to")

        # "empathetic" is the default - no transformations needed

        return message

    @staticmethod
    def construct_intelligent_day3_message(
        lead_name: str,
        intelligence_context: Optional[Any] = None,
        personalized_insights: Optional[List[str]] = None,
        critical_scenario: Optional[Dict] = None,
        tone_variant: str = "empathetic",
    ) -> str:
        """
        Construct Day 3 message using intelligence insights.

        Args:
            lead_name: Lead's name
            intelligence_context: Optional intelligence context
            personalized_insights: Optional list of insights
            critical_scenario: Optional critical scenario dict
            tone_variant: Message tone ("formal", "casual", "empathetic")
        """
        # Base message logic
        if critical_scenario:
            base_msg = f"Hi {lead_name}, following up on your property search. I have some time-sensitive information that could be valuable."
        else:
            # Standard nurture message with intelligence enhancements
            if intelligence_context and personalized_insights:
                # Use intelligence insights to personalize the message
                insights_text = " ".join(personalized_insights).lower()
                if "property matches" in insights_text:
                    base_msg = f"Hi {lead_name}, I found some properties that match what you're looking for. Any questions about the market?"
                elif "objections" in insights_text:
                    base_msg = f"Hi {lead_name}, checking in about your property search. Happy to address any concerns you might have."
                elif "positive sentiment" in insights_text:
                    base_msg = f"Hi {lead_name}, hope you're doing well! Any updates on your property search?"
                else:
                    base_msg = (
                        f"Hi {lead_name}, checking in about your property search. Any questions about the market?"
                    )
            else:
                # Fallback to standard message
                base_msg = f"Hi {lead_name}, checking in about your property search. Any questions about the market?"

        return ResponseGenerator._apply_tone_variant(base_msg, tone_variant)

    @staticmethod
    def construct_adaptive_day14_message(
        lead_name: str,
        intelligence_context: Optional[Any] = None,
        preferred_channel: str = "Email",
        content_adaptation_applied: bool = False,
        tone_variant: str = "empathetic",
    ) -> str:
        """
        Construct adaptive Day 14 message using intelligence insights.

        Args:
            lead_name: Lead's name
            intelligence_context: Optional intelligence context
            preferred_channel: Preferred communication channel
            content_adaptation_applied: Whether content adaptation was applied
            tone_variant: Message tone ("formal", "casual", "empathetic")
        """
        if intelligence_context and content_adaptation_applied:
            property_matches = intelligence_context.property_intelligence.match_count
            objections = intelligence_context.conversation_intelligence.objections_detected
            sentiment = intelligence_context.conversation_intelligence.overall_sentiment

            if property_matches > 0 and sentiment >= 0:
                if preferred_channel == "Voice":
                    msg = f"Hey {lead_name}, found {property_matches} places matching what you described. Quick call to go over them?"
                else:
                    msg = f"Hey {lead_name}, found {property_matches} places matching what you described. Sending details—let me know your thoughts!"

            elif objections and sentiment < 0:
                if preferred_channel == "Voice":
                    msg = (
                        f"Hey {lead_name}, I hear you on the concerns. Easier to talk it through—open to a quick call?"
                    )
                else:
                    msg = f"Hey {lead_name}, totally understand the hesitation. Happy to answer questions—what's on your mind?"

            else:
                # Standard follow-up with intelligence hints
                msg = f"Hey {lead_name}, been watching the market for you. Anything new on your end?"
        else:
            # Fallback standard message
            msg = f"Hey {lead_name}, checking in on your search. Spotted some good inventory lately—interested?"

        return ResponseGenerator._apply_tone_variant(msg, tone_variant)

    @staticmethod
    def construct_intelligent_day30_message(
        lead_name: str,
        final_strategy: str,
        intelligence_score: float,
        handoff_reasoning: List[str],
        tone_variant: str = "empathetic",
    ) -> str:
        """
        Construct intelligent Day 30 message based on final strategy.

        Args:
            lead_name: Lead's name
            final_strategy: Final engagement strategy
            intelligence_score: Intelligence score
            handoff_reasoning: List of handoff reasoning points
            tone_variant: Message tone ("formal", "casual", "empathetic")
        """
        if final_strategy == "jorge_qualification":
            msg = f"Hey {lead_name}, been 30 days—sounds like you're getting serious. Want me to connect you with Jorge for a deeper market breakdown?"

        elif final_strategy == "jorge_consultation":
            msg = f"Hey {lead_name}, market's moving in your area. Jorge can give you the full picture—want me to set up a quick call?"

        elif final_strategy == "graceful_disengage":
            msg = f"Hey {lead_name}, just checking—still looking or should I pause the updates? No pressure either way."

        else:  # nurture
            msg = f"Hey {lead_name}, it's been a month. Anything change with your timeline? I'm here when you're ready."

        return ResponseGenerator._apply_tone_variant(msg, tone_variant)

    @staticmethod
    def construct_cma_response(address: str, zillow_variance_abs: float, pdf_url: str, digital_twin_url: str) -> str:
        """Construct CMA response message."""
        return (
            f"I ran the numbers for {address}. Zillow's estimate is off by ${zillow_variance_abs:,.0f}. "
            f"Here is the real market analysis based on actual comps from the last 45 days: \n\n"
            f"[View CMA Report]({pdf_url})\n\n"
            f"I've also prepared a 3D Digital Twin of your property: {digital_twin_url}"
        )

    @staticmethod
    def build_cma_email_html(property_address: str) -> str:
        """Return branded HTML email body referencing the attached CMA PDF."""
        return f"""
<html>
<body style="font-family: Arial, sans-serif; color: #2c3e50; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: #2d5a7a; color: white; padding: 20px; text-align: center;">
        <h1 style="margin: 0; font-size: 22px;">Your Personalized Market Analysis</h1>
    </div>
    <div style="padding: 20px;">
        <p>Hey,</p>
        <p>I went through the comps myself and put together a <strong>Comparative Market Analysis (CMA)</strong> for <strong>{property_address}</strong> so you can see exactly how the market stacks up right now.</p>
        <p>The full report is attached as a PDF. Here's what you'll find inside:</p>
        <ul>
            <li>Current estimated market value with confidence range</li>
            <li>Comparable sales analysis with adjustments</li>
            <li>Zillow Zestimate vs. our AI-powered valuation</li>
            <li>Local market narrative and trends</li>
        </ul>
        <p>Have questions about the numbers? Just reply to this email and I'll
        walk you through everything.</p>
        <p style="margin-top: 25px;">Talk soon,<br><strong>Jorge</strong><br>
        EnterpriseHub Real Estate Intelligence</p>
    </div>
    <div style="border-top: 1px solid #e0e0e0; padding-top: 12px; font-size: 11px; color: #999; text-align: center;">
        Powered by EnterpriseHub AI &bull; Rancho Cucamonga, CA
    </div>
</body>
</html>"""

    @staticmethod
    def get_milestone_message(milestone: str, lead_name: str) -> str:
        """Get appropriate message for the current escrow milestone."""
        template = MILESTONE_MESSAGES.get(
            milestone, "Congrats {lead_name} on being under contract! I'll keep you updated on each milestone."
        )
        return template.format(lead_name=lead_name)

    @staticmethod
    def construct_showing_message(address: str, inventory_days: Optional[int] = None) -> str:
        """Construct showing coordination message."""
        urgency_msg = ""
        if inventory_days is not None and inventory_days < 15:
            urgency_msg = f" This market is moving fast ({inventory_days} days avg), so we should see it soon."

        return f"Great choice! I'm coordinating with the listing agent for {address}.{urgency_msg} Does tomorrow afternoon work for a tour?"

    @staticmethod
    def construct_offer_strategy_message(address: str, price_appreciation: Optional[float] = None) -> str:
        """Construct offer strategy message."""
        if price_appreciation is not None and price_appreciation > 10:
            strategy = "Given the 10%+ appreciation in this area, we might need to be aggressive with the terms."
        else:
            strategy = "Market is stable here, so we have some room to negotiate on repairs."

        return f"I've prepared an offer strategy for {address}. {strategy} Ready to review the numbers?"
