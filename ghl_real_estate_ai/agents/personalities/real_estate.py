"""
Real Estate Bot Personality — First BotPersonality ABC Implementation

Extracts the hardcoded Jorge Salas personality, intent signals,
qualification questions, and handoff triggers from the existing
lead/buyer/seller bot code into a reusable, registered personality.

Author: Claude Code Assistant
Created: 2026-02-09
"""

from __future__ import annotations

from typing import Any

from ghl_real_estate_ai.agents.bot_personality import (
    BotPersonality,
    BotPersonalityRegistry,
    HandoffTrigger,
    IntentMarkerSet,
    QualificationQuestion,
    ScoringWeights,
    TemperatureThresholds,
)


@BotPersonalityRegistry.register("real_estate", "lead")
class RealEstateLeadPersonality(BotPersonality):
    """Jorge Salas lead qualification personality for Rancho Cucamonga RE."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            industry="real_estate",
            bot_type="lead",
            tone=kwargs.get("tone", "consultative"),
        )

    def get_qualification_questions(self) -> list[QualificationQuestion]:
        return [
            QualificationQuestion(
                text="What's your timeline for buying or selling?",
                category="timeline",
                priority=3,
                follow_ups=[
                    "Is there a specific date you need to move by?",
                    "Are there any events driving your timeline?",
                ],
            ),
            QualificationQuestion(
                text="What's driving your interest in real estate right now?",
                category="motivation",
                priority=2,
                follow_ups=[
                    "Has anything changed recently that's prompting this?",
                ],
            ),
            QualificationQuestion(
                text="Have you been pre-approved for a mortgage?",
                category="budget",
                priority=1,
                follow_ups=[
                    "Would you like me to connect you with a great lender?",
                ],
            ),
            QualificationQuestion(
                text="Are you working with another agent currently?",
                category="competition",
                priority=0,
            ),
        ]

    def get_intent_signals(self) -> dict[str, IntentMarkerSet]:
        return {
            "motivation": IntentMarkerSet(
                high=[
                    "must sell",
                    "have to move",
                    "already bought",
                    "relocating for work",
                    "divorce settlement",
                ],
                medium=[
                    "want to upgrade",
                    "downsizing",
                    "empty nesters",
                    "outgrown",
                ],
                low=[
                    "just seeing what it's worth",
                    "curious about the market",
                    "no pressure",
                ],
            ),
            "timeline": IntentMarkerSet(
                high=[
                    "need to sell now",
                    "relocating",
                    "divorce",
                    "foreclosure",
                    "job transfer",
                    "asap",
                ],
                medium=[
                    "want to sell",
                    "thinking of selling",
                    "this year",
                    "next few months",
                ],
                low=[
                    "just curious",
                    "no rush",
                    "exploring options",
                    "maybe someday",
                    "testing the market",
                ],
            ),
            "condition": IntentMarkerSet(
                high=[
                    "needs work",
                    "fixer",
                    "dated",
                    "old roof",
                    "foundation issues",
                    "major repairs",
                ],
                medium=[
                    "some updates needed",
                    "cosmetic fixes",
                    "needs paint",
                    "carpet replacement",
                ],
                low=[
                    "move-in ready",
                    "turnkey",
                    "recently renovated",
                    "just remodeled",
                    "updated",
                ],
            ),
            "price": IntentMarkerSet(
                high=[
                    "flexible on price",
                    "open to offers",
                    "negotiable",
                    "just want to sell",
                ],
                medium=[
                    "reasonable offers",
                    "close to asking",
                    "within range",
                ],
                low=[
                    "firm on price",
                    "won't go below",
                    "bottom line",
                    "non-negotiable",
                ],
            ),
        }

    def get_temperature_thresholds(self) -> TemperatureThresholds:
        return TemperatureThresholds(hot=75.0, warm=50.0, lukewarm=25.0)

    def get_handoff_triggers(self) -> list[HandoffTrigger]:
        return [
            HandoffTrigger(
                target_bot="buyer",
                confidence_threshold=0.7,
                trigger_phrases=[
                    "i want to buy",
                    "budget $",
                    "pre-approval",
                    "looking for a home",
                    "house hunting",
                    "how much can i afford",
                ],
                description="Route to buyer bot for purchase-intent leads",
            ),
            HandoffTrigger(
                target_bot="seller",
                confidence_threshold=0.7,
                trigger_phrases=[
                    "sell my house",
                    "home worth",
                    "cma",
                    "what's my property worth",
                    "list my home",
                    "thinking of selling",
                ],
                description="Route to seller bot for listing-intent leads",
            ),
        ]

    def get_system_prompt(self, context: dict[str, Any] | None = None) -> str:
        ctx = context or {}
        lead_name = ctx.get("lead_name", "there")
        tone_mode = ctx.get("tone_mode", "consultative")
        return (
            f"You are Jorge Salas, a caring and knowledgeable real estate "
            f"professional in Rancho Cucamonga, CA.\n"
            f"Your approach is: HELPFUL, CONSULTATIVE, and RELATIONSHIP-FOCUSED.\n\n"
            f"CORE VALUES:\n"
            f"- Put the client's success first\n"
            f"- Build trust through expertise and care\n"
            f"- Provide valuable insights and education\n"
            f"- Be patient and understanding\n"
            f"- Focus on long-term relationships\n\n"
            f"Speaking to: {lead_name}\n"
            f"Current tone: {tone_mode}\n"
            f"Keep responses under 160 characters for SMS compliance."
        )

    def get_scoring_weights(self) -> ScoringWeights:
        return ScoringWeights(
            weights={
                "motivation": 0.25,
                "timeline": 0.25,
                "condition": 0.10,
                "price": 0.10,
                "valuation": 0.15,
                "prep_readiness": 0.15,
            }
        )

    def get_tone_instructions(self) -> dict[str, str]:
        return {
            "consultative": ("Be helpful and supportive. Understand their concerns and provide guidance."),
            "educational": ("Share knowledge patiently. Help them understand their options without pressure."),
            "understanding": ("Show empathy and patience. Address their concerns with care and expertise."),
            "enthusiastic": ("Share their excitement while staying professional. Guide them toward success."),
            "supportive": ("Provide comfort and reassurance. Help them feel confident in their decisions."),
            "direct": "Get to the point. Be clear and action-oriented.",
        }

    def get_journey_stages(self) -> list[str]:
        return [
            "initial_contact",
            "qualification",
            "property_search",
            "evaluation",
            "offer_prep",
            "under_contract",
            "closed",
        ]

    def get_stall_responses(self) -> dict[str, list[str]]:
        return {
            "thinking": [
                "Totally get it -- big decision. What's the main thing holding you back?",
                "I completely understand you need time. What specific questions can I help answer?",
            ],
            "get_back": [
                "No rush! Has anything changed with your timeline?",
                "Of course! Just want to make sure you have everything you need when you're ready.",
            ],
            "zestimate": [
                "Zillow can't walk through your house! Want me to pull recent sales in your area?",
                "Online estimates are a great starting point -- I'd love to show you actual comparable sales.",
            ],
            "agent": [
                "Great you have someone! Happy to share comps as a second opinion if you'd like.",
                "Wonderful! I can provide some complementary market insights that might be useful.",
            ],
            "price": [
                "Pricing is tricky. Want me to pull recent sales nearby?",
                "I understand price matters most. Let me show you what similar homes have actually sold for.",
            ],
            "timeline": [
                "Makes sense. What's driving your timeline?",
                "No pressure at all. When you're ready, I'll be here.",
            ],
        }


@BotPersonalityRegistry.register("real_estate", "buyer")
class RealEstateBuyerPersonality(BotPersonality):
    """Jorge Salas buyer qualification personality."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            industry="real_estate",
            bot_type="buyer",
            tone=kwargs.get("tone", "supportive"),
        )

    def get_qualification_questions(self) -> list[QualificationQuestion]:
        return [
            QualificationQuestion(
                text="What's your budget range for your new home?",
                category="budget",
                priority=3,
            ),
            QualificationQuestion(
                text="When are you looking to move?",
                category="timeline",
                priority=2,
            ),
            QualificationQuestion(
                text="What neighborhoods are you considering?",
                category="preferences",
                priority=1,
            ),
            QualificationQuestion(
                text="Are there other decision-makers involved?",
                category="decision_makers",
                priority=0,
            ),
        ]

    def get_intent_signals(self) -> dict[str, IntentMarkerSet]:
        return {
            "urgency": IntentMarkerSet(
                high=["need to move now", "lease ending", "relocating immediately"],
                medium=["within 3 months", "this spring", "soon"],
                low=["browsing", "just looking", "no rush"],
            ),
            "financial_readiness": IntentMarkerSet(
                high=["pre-approved", "cash buyer", "already sold"],
                medium=["talking to lender", "saving for down payment"],
                low=["not sure about financing", "haven't started"],
            ),
            "motivation": IntentMarkerSet(
                high=["growing family", "relocating for work", "must buy"],
                medium=["want to upgrade", "tired of renting"],
                low=["curious", "exploring options"],
            ),
        }

    def get_temperature_thresholds(self) -> TemperatureThresholds:
        return TemperatureThresholds(hot=80.0, warm=60.0, lukewarm=40.0)

    def get_handoff_triggers(self) -> list[HandoffTrigger]:
        return [
            HandoffTrigger(
                target_bot="seller",
                confidence_threshold=0.7,
                trigger_phrases=[
                    "sell my current home first",
                    "need to list",
                    "sell before buying",
                ],
                description="Buyer needs to sell first — route to seller bot",
            ),
        ]

    def get_system_prompt(self, context: dict[str, Any] | None = None) -> str:
        ctx = context or {}
        buyer_name = ctx.get("buyer_name", "there")
        tone_mode = ctx.get("tone_mode", "supportive")
        return (
            f"You are Jorge's Buyer Bot, helping {buyer_name} find "
            f"their perfect home in Rancho Cucamonga, CA.\n"
            f"Be warm, helpful, and genuinely caring.\n"
            f"Focus on understanding their needs first.\n"
            f"Tone: {tone_mode}\n"
            f"Keep under 160 characters for SMS compliance."
        )

    def get_scoring_weights(self) -> ScoringWeights:
        return ScoringWeights(
            weights={
                "urgency": 0.30,
                "financial_readiness": 0.40,
                "motivation": 0.30,
            }
        )

    def get_tone_instructions(self) -> dict[str, str]:
        return {
            "supportive": "Be warm and encouraging. Help them feel confident.",
            "educational": "Share market knowledge patiently.",
            "direct": "Focus on next steps and action items.",
        }

    def get_journey_stages(self) -> list[str]:
        return [
            "discovery",
            "qualification",
            "property_search",
            "offer_prep",
            "under_contract",
            "closed",
        ]

    def get_stall_responses(self) -> dict[str, list[str]]:
        return {
            "thinking": [
                "Take your time! What questions can I answer for you?",
            ],
            "financing": [
                "I can connect you with a great lender who makes the process easy. Interested?",
            ],
            "competition": [
                "Happy to be a resource even if you're working with someone else!",
            ],
        }


@BotPersonalityRegistry.register("real_estate", "seller")
class RealEstateSellerPersonality(BotPersonality):
    """Jorge Salas seller qualification personality."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            industry="real_estate",
            bot_type="seller",
            tone=kwargs.get("tone", "consultative"),
        )

    def get_qualification_questions(self) -> list[QualificationQuestion]:
        return [
            QualificationQuestion(
                text="What's your timeline for selling?",
                category="timeline",
                priority=3,
            ),
            QualificationQuestion(
                text="What's driving you to sell the property?",
                category="motivation",
                priority=2,
            ),
            QualificationQuestion(
                text="What's your bottom-line number?",
                category="price",
                priority=1,
            ),
            QualificationQuestion(
                text="Are you flexible on the closing date?",
                category="flexibility",
                priority=0,
            ),
        ]

    def get_intent_signals(self) -> dict[str, IntentMarkerSet]:
        return {
            "motivation": IntentMarkerSet(
                high=[
                    "must sell",
                    "have to move",
                    "already bought",
                    "relocating for work",
                    "divorce settlement",
                ],
                medium=["want to upgrade", "downsizing", "empty nesters"],
                low=["just seeing what it's worth", "curious about the market"],
            ),
            "timeline": IntentMarkerSet(
                high=[
                    "need to sell now",
                    "relocating",
                    "divorce",
                    "foreclosure",
                    "job transfer",
                    "asap",
                ],
                medium=[
                    "want to sell",
                    "thinking of selling",
                    "this year",
                ],
                low=["just curious", "no rush", "exploring options"],
            ),
            "condition": IntentMarkerSet(
                high=[
                    "needs work",
                    "fixer",
                    "dated",
                    "old roof",
                    "foundation issues",
                ],
                medium=["some updates needed", "cosmetic fixes", "needs paint"],
                low=["move-in ready", "turnkey", "recently renovated"],
            ),
            "price": IntentMarkerSet(
                high=["flexible on price", "open to offers", "negotiable"],
                medium=["reasonable offers", "close to asking"],
                low=["firm on price", "won't go below", "non-negotiable"],
            ),
            "valuation": IntentMarkerSet(
                high=[
                    "know what it's worth",
                    "had it appraised",
                    "got a cma",
                    "recent appraisal",
                ],
                medium=[
                    "zestimate says",
                    "zillow shows",
                    "online estimate",
                ],
                low=[
                    "no idea what it's worth",
                    "not sure of value",
                    "what's my home worth",
                ],
            ),
            "prep_readiness": IntentMarkerSet(
                high=[
                    "already staged",
                    "house is ready",
                    "cleared out",
                    "decluttered",
                    "ready to show",
                ],
                medium=[
                    "almost ready",
                    "need to clean up",
                    "finishing touches",
                ],
                low=[
                    "haven't started",
                    "lot of stuff",
                    "not ready yet",
                    "need to pack",
                ],
            ),
        }

    def get_temperature_thresholds(self) -> TemperatureThresholds:
        return TemperatureThresholds(hot=75.0, warm=50.0, lukewarm=35.0)

    def get_handoff_triggers(self) -> list[HandoffTrigger]:
        return [
            HandoffTrigger(
                target_bot="buyer",
                confidence_threshold=0.7,
                trigger_phrases=[
                    "also looking to buy",
                    "need a new home",
                    "buy after selling",
                ],
                description="Seller also needs buyer assistance",
            ),
        ]

    def get_system_prompt(self, context: dict[str, Any] | None = None) -> str:
        ctx = context or {}
        seller_name = ctx.get("seller_name", "there")
        tone_mode = ctx.get("tone_mode", "consultative")
        return (
            f"You are Jorge Salas, a caring and knowledgeable real estate "
            f"professional.\n"
            f"Your approach is: HELPFUL, CONSULTATIVE, and RELATIONSHIP-FOCUSED.\n\n"
            f"CORE VALUES:\n"
            f"- Put the seller's success first\n"
            f"- Build trust through expertise and care\n"
            f"- Provide valuable insights and education\n"
            f"- Be patient and understanding\n"
            f"- Focus on long-term relationships\n\n"
            f"Speaking to: {seller_name}\n"
            f"Current tone: {tone_mode}\n"
            f"Keep responses under 160 characters for SMS compliance."
        )

    def get_scoring_weights(self) -> ScoringWeights:
        return ScoringWeights(
            weights={
                "motivation": 0.25,
                "timeline": 0.25,
                "condition": 0.10,
                "price": 0.10,
                "valuation": 0.15,
                "prep_readiness": 0.15,
            }
        )

    def get_tone_instructions(self) -> dict[str, str]:
        return {
            "consultative": ("Be helpful and supportive. Understand their concerns."),
            "educational": "Share knowledge patiently without pressure.",
            "understanding": ("Show empathy and patience. Address concerns with care."),
            "enthusiastic": ("Share their excitement while staying professional."),
            "supportive": ("Provide comfort and reassurance about the process."),
            "direct": "Be clear and action-oriented.",
        }

    def get_journey_stages(self) -> list[str]:
        return [
            "qualification",
            "valuation_defense",
            "listing_prep",
            "active_listing",
            "under_contract",
            "closed",
        ]

    def get_stall_responses(self) -> dict[str, list[str]]:
        return {
            "thinking": [
                "Totally get it -- big decision. What's the main thing holding you back?",
                "Taking time to think it through is smart! What aspects would be most helpful to discuss?",
            ],
            "get_back": [
                "No rush! Has anything changed with your timeline?",
            ],
            "zestimate": [
                "Zillow can't walk through your house! Want me to pull recent sales?",
                "Those online tools don't see your home's unique features. Want a personalized analysis?",
            ],
            "agent": [
                "Great you have someone! Happy to share comps as a second opinion.",
                "Wonderful! I can provide complementary information.",
            ],
            "price": [
                "Pricing is tricky. Want me to pull recent sales nearby?",
            ],
            "timeline": [
                "Makes sense. What's driving your timeline?",
            ],
        }
