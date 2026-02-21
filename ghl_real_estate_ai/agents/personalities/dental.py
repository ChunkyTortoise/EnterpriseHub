"""
Dental Bot Personality — Second BotPersonality ABC Implementation

Demonstrates industry portability by implementing dental-specific
intent signals, qualification questions, and handoff triggers.

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


@BotPersonalityRegistry.register("dental", "lead")
class DentalLeadPersonality(BotPersonality):
    """Dental practice lead qualification personality."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(
            industry="dental",
            bot_type="lead",
            tone=kwargs.get("tone", "friendly"),
        )

    def get_qualification_questions(self) -> list[QualificationQuestion]:
        return [
            QualificationQuestion(
                text="What type of dental care are you looking for?",
                category="procedure",
                priority=3,
                follow_ups=[
                    "Is this for a specific concern or a routine visit?",
                    "When did you last see a dentist?",
                ],
            ),
            QualificationQuestion(
                text="Do you have dental insurance?",
                category="insurance",
                priority=2,
                follow_ups=[
                    "Which provider are you with?",
                    "Would you like to know about our payment plans?",
                ],
            ),
            QualificationQuestion(
                text="How soon would you like to schedule an appointment?",
                category="urgency",
                priority=1,
                follow_ups=[
                    "Are mornings or afternoons better for you?",
                ],
            ),
            QualificationQuestion(
                text="Do you have a budget range in mind for your treatment?",
                category="budget",
                priority=0,
                follow_ups=[
                    "We offer flexible financing options if that helps.",
                ],
            ),
        ]

    def get_intent_signals(self) -> dict[str, IntentMarkerSet]:
        return {
            "urgency": IntentMarkerSet(
                high=[
                    "emergency",
                    "severe pain",
                    "broken tooth",
                    "swelling",
                    "abscess",
                    "knocked out tooth",
                    "bleeding won't stop",
                ],
                medium=[
                    "pain",
                    "toothache",
                    "sensitive",
                    "bothering me",
                    "uncomfortable",
                    "need to be seen soon",
                ],
                low=[
                    "routine checkup",
                    "just a cleaning",
                    "been a while",
                    "overdue for a visit",
                ],
            ),
            "procedure_value": IntentMarkerSet(
                high=[
                    "implants",
                    "veneers",
                    "invisalign",
                    "full mouth restoration",
                    "cosmetic makeover",
                    "dental implant",
                ],
                medium=[
                    "crown",
                    "bridge",
                    "root canal",
                    "teeth whitening",
                    "filling",
                    "extraction",
                ],
                low=[
                    "cleaning",
                    "checkup",
                    "x-rays",
                    "exam",
                ],
            ),
            "insurance_status": IntentMarkerSet(
                high=[
                    "have insurance",
                    "covered by",
                    "my plan covers",
                    "dental benefits",
                ],
                medium=[
                    "checking coverage",
                    "need to verify",
                    "not sure about coverage",
                ],
                low=[
                    "no insurance",
                    "paying out of pocket",
                    "self-pay",
                    "no dental plan",
                ],
            ),
            "motivation": IntentMarkerSet(
                high=[
                    "wedding coming up",
                    "job interview",
                    "important event",
                    "can't eat",
                    "can't sleep from pain",
                ],
                medium=[
                    "want a nicer smile",
                    "self-conscious",
                    "considering",
                ],
                low=[
                    "just curious",
                    "looking into it",
                    "maybe someday",
                ],
            ),
        }

    def get_temperature_thresholds(self) -> TemperatureThresholds:
        return TemperatureThresholds(hot=70.0, warm=45.0, lukewarm=25.0)

    def get_handoff_triggers(self) -> list[HandoffTrigger]:
        return [
            HandoffTrigger(
                target_bot="cosmetic",
                confidence_threshold=0.7,
                trigger_phrases=[
                    "veneers",
                    "teeth whitening",
                    "cosmetic",
                    "smile makeover",
                    "invisalign",
                    "bonding",
                ],
                description="Route to cosmetic dental specialist",
            ),
            HandoffTrigger(
                target_bot="orthodontic",
                confidence_threshold=0.7,
                trigger_phrases=[
                    "braces",
                    "alignment",
                    "crooked teeth",
                    "orthodontist",
                    "retainer",
                    "bite issues",
                ],
                description="Route to orthodontic specialist",
            ),
            HandoffTrigger(
                target_bot="emergency",
                confidence_threshold=0.5,
                trigger_phrases=[
                    "emergency",
                    "severe pain",
                    "knocked out",
                    "broken tooth",
                    "swelling",
                    "abscess",
                ],
                description="Route to emergency triage (lower threshold)",
            ),
        ]

    def get_system_prompt(self, context: dict[str, Any] | None = None) -> str:
        ctx = context or {}
        patient_name = ctx.get("patient_name", "there")
        tone_mode = ctx.get("tone_mode", "friendly")
        return (
            f"You are a friendly dental practice assistant helping "
            f"{patient_name} with their dental care needs.\n"
            f"Your approach is: WARM, REASSURING, and KNOWLEDGEABLE.\n\n"
            f"CORE VALUES:\n"
            f"- Patient comfort and care come first\n"
            f"- Reduce dental anxiety through clear communication\n"
            f"- Provide honest treatment recommendations\n"
            f"- Make scheduling easy and convenient\n"
            f"- Build long-term patient relationships\n\n"
            f"Current tone: {tone_mode}\n"
            f"Keep responses concise and reassuring."
        )

    def get_scoring_weights(self) -> ScoringWeights:
        return ScoringWeights(
            weights={
                "urgency": 0.35,
                "procedure_value": 0.25,
                "insurance_status": 0.20,
                "motivation": 0.20,
            }
        )

    def get_tone_instructions(self) -> dict[str, str]:
        return {
            "friendly": "Be warm and approachable. Make the patient feel comfortable.",
            "reassuring": ("Address dental anxiety. Emphasize comfort and modern techniques."),
            "informative": "Explain procedures clearly without medical jargon.",
            "urgent": ("Be empathetic but direct about the need for prompt treatment."),
        }

    def get_journey_stages(self) -> list[str]:
        return [
            "initial_inquiry",
            "qualification",
            "treatment_planning",
            "scheduling",
            "pre_appointment",
            "post_treatment",
        ]

    def get_stall_responses(self) -> dict[str, list[str]]:
        return {
            "dental_anxiety": [
                "We completely understand dental anxiety! Our office "
                "uses comfort-focused techniques. Would you like to "
                "know more about our approach?",
                "Many of our happiest patients started out feeling nervous. We go at your pace -- no judgment.",
            ],
            "cost_concern": [
                "We offer flexible payment plans! Would you like to learn about our financing options?",
                "Let me check what your insurance would cover for this treatment.",
            ],
            "thinking": [
                "No rush at all! Would it help to come in for a free consultation first?",
                "Take your time. What questions can I answer to help you feel more comfortable?",
            ],
            "second_opinion": [
                "Getting a second opinion is totally reasonable! We're happy to provide a complimentary evaluation.",
            ],
        }
