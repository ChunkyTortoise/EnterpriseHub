"""
Response generation and objection handling module for buyer bot.
"""

import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService
from ghl_real_estate_ai.services.sentiment_analysis_service import SentimentAnalysisService

logger = get_logger(__name__)


class ResponseGenerator:
    """Handles response generation and objection handling."""

    def __init__(
        self,
        claude: Optional[ClaudeAssistant] = None,
        sentiment_service: Optional[SentimentAnalysisService] = None,
        ab_testing: Optional[ABTestingService] = None,
    ):
        self.claude = claude or ClaudeAssistant()
        self.sentiment_service = sentiment_service
        self.ab_testing = ab_testing

    @staticmethod
    def _extract_text_from_response(response: Any) -> str:
        """Normalize buyer response payloads from different Claude client shapes."""
        if response is None:
            return ""
        if isinstance(response, str):
            return response
        if isinstance(response, dict):
            content = response.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, dict):
                nested = content.get("text") or content.get("content")
                if isinstance(nested, str):
                    return nested
            for key in ("analysis", "response", "text", "message"):
                value = response.get(key)
                if isinstance(value, str):
                    return value
            return ""
        content_attr = getattr(response, "content", None)
        if isinstance(content_attr, str):
            return content_attr
        return str(response)

    async def handle_objections(self, state: BuyerBotState) -> Dict:
        """Handle detected buyer objections with appropriate strategies."""
        objection_type = state.get("detected_objection_type")
        if not objection_type:
            return {}

        objection_strategies = {
            "budget_shock": {
                "approach": "Show affordable alternatives and financing options",
                "talking_points": [
                    "There are great neighborhoods with homes in your range",
                    "Let's explore areas that give you the best value",
                ],
            },
            "analysis_paralysis": {
                "approach": "Narrow focus and create urgency with market data",
                "talking_points": [
                    "Based on what you've told me, I'd focus on these top 3 options",
                    "Properties in this range are moving quickly right now",
                ],
            },
            "spouse_decision": {
                "approach": "Include partner and schedule joint viewing",
                "talking_points": [
                    "I'd love to include them in the conversation",
                    "Would a weekend showing work for both of you?",
                ],
            },
            "timing": {
                "approach": "Provide market education and soft follow-up",
                "talking_points": [
                    "I understand timing is important. Let me share what the market looks like",
                    "I can keep you updated on new listings that match your criteria",
                ],
            },
            "just_looking": {
                "approach": "Validate their pace, redirect with value and curiosity",
                "talking_points": [
                    "Totally get it! A lot of buyers start by exploring. What area are you most curious about?",
                    "No rush at all. Want me to send you some listings in a specific area so you can get a feel for the market?",
                    "That's a great way to start. What caught your eye so far?",
                ],
            },
        }

        strategy = objection_strategies.get(
            objection_type,
            {
                "approach": "Address concern with empathy and helpful information",
                "talking_points": ["I understand your concern. Let's work through this together."],
            },
        )

        # Enrich budget_shock with affordability data if available
        if objection_type == "budget_shock" and state.get("affordability_analysis"):
            analysis = state["affordability_analysis"]
            strategy["talking_points"].append(
                f"With 20% down, your estimated monthly payment would be "
                f"${analysis.get('total_monthly_payment', 0):,.0f}"
            )

        # Track objection in history
        objection_record = {
            "type": objection_type,
            "strategy": strategy["approach"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        objection_history = state.get("objection_history") or []
        objection_history.append(objection_record)

        return {
            "objection_history": objection_history,
            "current_qualification_step": "objection_handling",
        }

    async def generate_buyer_response(self, state: BuyerBotState, tone_variant: Optional[str] = None) -> Dict:
        """
        Generate strategic buyer response based on qualification and property matches.
        Enhanced with Phase 3.3 intelligence context for consultative recommendations.
        """
        try:
            profile = state.get("intent_profile")
            matches = state.get("matched_properties", [])
            intelligence_context = state.get("intelligence_context")
            buyer_id = state.get("buyer_id", "unknown")

            # UPS: Progressive skills integration (feature-flagged)
            skill_context = self._load_buyer_skill_context(state)

            # Use A/B test variant from state (assigned in process_buyer_conversation)
            if not tone_variant:
                tone_variant = state.get("tone_variant", "empathetic")

            # Phase 1.5: Analyze sentiment of the user message
            sentiment_context = ""
            if self.sentiment_service:
                try:
                    last_user_msg = next(
                        (
                            msg.get("content", "")
                            for msg in reversed(state.get("conversation_history", []))
                            if msg.get("role") == "user"
                        ),
                        "",
                    )
                    if last_user_msg:
                        sentiment_result = await self.sentiment_service.analyze_sentiment(last_user_msg)
                        tone_adjustment = self.sentiment_service.get_response_tone_adjustment(
                            sentiment_result.sentiment
                        )

                        sentiment_context = f"""
            SENTIMENT ANALYSIS (Phase 1.5):
            - Detected Sentiment: {sentiment_result.sentiment.value.upper()} (Confidence: {sentiment_result.confidence:.2f})
            - Suggested Tone: {tone_adjustment.get("tone", "professional")}
            - Pacing: {tone_adjustment.get("pace", "normal")}
            """
                        # Check for escalation
                        if sentiment_result.escalation_required.value != "none":
                            logger.warning(
                                f"Sentiment escalation triggered for buyer {buyer_id}: "
                                f"{sentiment_result.escalation_required.value}"
                            )
                except Exception as e:
                    logger.warning(f"Sentiment analysis failed in buyer response generation: {e}")

            # Base prompt for buyer consultation
            buyer_temp = getattr(profile, "buyer_temperature", "cold") if profile else "cold"
            response_prompt = f"""
            As Jorge's Buyer Bot, generate a helpful and supportive response for this buyer.

            MARKET CONTEXT:
            - Jorge specializes exclusively in Rancho Cucamonga, CA (Inland Empire, San Bernardino County)
            - Typical single-family home range: $550K–$1.2M; luxury above $1.2M
            - Key neighborhoods/areas: Etiwanda, Alta Loma, Day Creek, Victoria Groves, Heritage, Caryn, Windrows, Old Alta Loma
            - Market dynamics: strong demand, fast-moving inventory, commuter-friendly (SR-210/I-15 access, 55-65 min to downtown LA), highly ranked schools (CVUSD)
            - When relevant, reference specific neighborhoods, school names, or local landmarks to demonstrate market expertise
            - Common seller motivations: upsizing, relocating out of state, estate sales, investor exits, divorce

            BUYER CONTEXT:
            - Common buyer profiles: first-time buyers (often FHA/VA), move-up buyers from LA/OC looking for more space, investors, and remote workers seeking Inland Empire value
            - Price sensitivity: FHA loan limits ~$730K; jumbo threshold ~$766K
            - Key buyer concerns: commute time, school district (CVUSD highly valued), HOA fees, new vs resale
            - Always establish WHERE they want to live and WHY before discussing finances
            - One question per message. Never ask two questions in the same response.

            Buyer Temperature: {buyer_temp}
            Financial Readiness: {state.get("financial_readiness_score", 25)}/100
            Properties Matched: {len(matches)}
            Current Step: {state.get("current_qualification_step", "unknown")}

            Conversation Context: {state.get("conversation_history", [])[-2:]}
            {sentiment_context}

            Response should be:
            - Warm, helpful and genuinely caring
            - Educational and patient (never pushy)
            - Focused on understanding their needs first
            - Property-focused if qualified with matches
            - Market education if qualified but no matches
            - Professional, friendly and relationship-focused (Jorge's style)

            Tone style: {tone_variant}

            Keep under 290 characters for SMS compliance (pipeline enforces 320 max).
            No hyphens. No robotic phrasing. Short sentences.
            Do not open with 'Hey' and do not identify yourself as an AI — that is handled separately.
            """

            # UPS: Inject progressive skill guidance into prompt
            if skill_context:
                response_prompt += f"\n\nPROGRESSIVE SKILL GUIDANCE:\n{skill_context}"

            # Enhance prompt with intelligence context if available (Phase 3.3)
            if intelligence_context:
                response_prompt = self._enhance_buyer_prompt_with_intelligence(
                    response_prompt, intelligence_context, state
                )

            raw_response = await self.claude.generate_response(response_prompt)
            response = self._extract_text_from_response(raw_response)

            import random

            fallback = random.choice(
                [
                    "What are you looking for in your next home? I want to make sure we're on the same page.",
                    "What matters most to you in your next home? Area, size, style?",
                    "What's the most important thing on your wish list for your next place?",
                ]
            )
            content = response or fallback

            # Strip markdown headers if Claude returned structured analysis instead of SMS text
            # (occurs when intelligence context confuses the output format)
            if content and (content.startswith("#") or "\n##" in content[:120]):
                lines = [
                    ln.strip()
                    for ln in content.split("\n")
                    if ln.strip()
                    and not ln.startswith("#")
                    and not ln.startswith("**")
                    and not ln.startswith("- ")
                    and len(ln.strip()) > 15
                ]
                content = lines[0] if lines else fallback

            content = content.replace("-", " ")  # Jorge spec: no hyphens in SMS
            return {
                "response_content": content,
                "response_tone": "friendly_consultative",
                "next_action": "send_response",
            }

        except Exception as e:
            logger.error(f"Error generating buyer response for {state.get('buyer_id')}: {str(e)}")
            import random

            return {
                "response_content": random.choice(
                    [
                        "What area are you looking in? I can check what's available right now.",
                        "What matters most to you in your next home? Let's start there.",
                        "To find you the best matches, what price range works for your situation?",
                    ]
                ),
                "response_tone": "friendly_supportive",
                "next_action": "send_response",
            }

    def _enhance_buyer_prompt_with_intelligence(
        self, base_prompt: str, intelligence_context: Any, state: BuyerBotState
    ) -> str:
        """
        Enhance Claude prompt with buyer intelligence context for consultative responses.
        """
        try:
            enhanced_prompt = base_prompt

            # Add property intelligence if available
            if hasattr(intelligence_context, "property_intelligence"):
                property_intel = intelligence_context.property_intelligence
                if property_intel.match_count > 0:
                    enhanced_prompt += f"\n\nPROPERTY INTELLIGENCE:"
                    enhanced_prompt += f"\n- Found {property_intel.match_count} properties matching buyer preferences"
                    enhanced_prompt += f"\n- Best match score: {property_intel.best_match_score:.1f}%"
                    if property_intel.behavioral_reasoning:
                        enhanced_prompt += f"\n- Match reasoning: {property_intel.behavioral_reasoning}"

            # Add conversation intelligence insights for buyer consultation
            if hasattr(intelligence_context, "conversation_intelligence"):
                conversation_intel = intelligence_context.conversation_intelligence
                if conversation_intel.objections_detected:
                    enhanced_prompt += f"\n\nBUYER CONCERNS DETECTED:"
                    for objection in conversation_intel.objections_detected[:2]:  # Top 2 concerns
                        concern_type = objection.get("type", "unknown")
                        confidence = objection.get("confidence", 0.0)
                        context = objection.get("context", "")
                        enhanced_prompt += f"\n- {concern_type.upper()} concern detected ({confidence:.0%}): {context}"

                        # Add consultative suggestions for buyer concerns
                        suggestions = objection.get("suggested_responses", [])
                        if suggestions:
                            enhanced_prompt += f"\n  Consultative approach: {suggestions[0]}"

            # Add preference intelligence insights for personalization
            if hasattr(intelligence_context, "preference_intelligence"):
                preference_intel = intelligence_context.preference_intelligence
                if preference_intel.profile_completeness > 0.3:
                    enhanced_prompt += f"\n\nBUYER PREFERENCE INTELLIGENCE:"
                    enhanced_prompt += (
                        f"\n- Preference profile completeness: {preference_intel.profile_completeness:.0%}"
                    )

                    # Add learned preferences for better consultation
                    if hasattr(preference_intel, "learned_preferences") and preference_intel.learned_preferences:
                        preferences = preference_intel.learned_preferences
                        enhanced_prompt += f"\n- Key preferences: {', '.join(preferences.keys())}"

            # Add market intelligence for buyer education
            enhanced_prompt += f"\n\nMARKET GUIDANCE:"
            enhanced_prompt += f"\n- Use this intelligence to provide specific, helpful property guidance"
            enhanced_prompt += f"\n- Maintain warm, friendly tone - educate and guide with care"
            enhanced_prompt += f"\n- If concerns detected, address them with understanding and helpful alternatives"

            return enhanced_prompt

        except Exception as e:
            logger.warning(f"Buyer prompt enhancement failed: {e}")
            return base_prompt

    def _load_buyer_skill_context(self, state: BuyerBotState) -> str:
        """
        Load progressive skill content based on buyer's current qualification step.

        Returns skill file content as a string to inject into the prompt,
        or empty string if the feature is disabled or no skill applies.
        """
        enabled = os.getenv("ENABLE_BUYER_PROGRESSIVE_SKILLS", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        if not enabled:
            return ""

        buying_motivation = state.get("buying_motivation_score") or state.get("financial_readiness_score", 0) or 0

        # High-intent leads skip progressive skills (full model handles them)
        if buying_motivation >= 90:
            return ""

        # Determine which skill file to load based on current step
        current_step = state.get("current_qualification_step", "")
        frs = state.get("financial_readiness_score", 0) or 0

        objection_history = state.get("objection_history") or []
        detected_objection = state.get("detected_objection_type")

        if detected_objection or objection_history:
            skill_file = "objection_handling.md"
        elif current_step == "preferences" or frs >= 30:
            skill_file = "property_matching.md"
        else:
            skill_file = "initial_discovery.md"

        # Resolve skill file path relative to this module
        skills_dir = Path(__file__).parent / "skills"
        skill_path = skills_dir / skill_file

        try:
            content = skill_path.read_text()
            logger.info(f"Buyer progressive skill loaded: {skill_file}")
            return content
        except FileNotFoundError:
            logger.warning(f"Buyer skill file not found: {skill_path}")
            return ""
