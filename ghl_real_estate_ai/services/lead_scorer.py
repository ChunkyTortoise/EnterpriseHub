"""
Lead scoring service for real estate AI.

Calculates lead quality scores based on NUMBER OF QUALIFYING QUESTIONS ANSWERED.
This is Jorge's requirement: count questions, not points.

Scoring Methodology (Question Count):
- Budget confirmed: +1 question
- Location specified: +1 question
- Timeline confirmed: +1 question
- Property requirements (beds/baths/must-haves): +1 question
- Financing status: +1 question
- Motivation (why buying/selling now): +1 question
- Home condition (sellers only): +1 question

Lead Classifications (Jorge's Criteria):
- Hot Lead: 3+ questions answered (immediate action required)
- Warm Lead: 2 questions answered (follow up within 24 hours)
- Cold Lead: 0-1 questions answered (nurture campaign)
"""

import hashlib
import json
from typing import Any, Dict, List

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.services.cache_service import get_cache_service


class _SyncAsyncValue:
    """Value wrapper that can be used directly or awaited."""

    def __init__(self, value: Any):
        self._value = value

    def unwrap(self) -> Any:
        return self._value

    async def _as_async(self) -> Any:
        return self._value

    def __await__(self):
        return self._as_async().__await__()

    def __repr__(self) -> str:
        return repr(self._value)

    def __str__(self) -> str:
        return str(self._value)

    def __bool__(self) -> bool:
        return bool(self._value)

    def __int__(self) -> int:
        return int(self._value)

    def __float__(self) -> float:
        return float(self._value)

    def __index__(self) -> int:
        return int(self._value)

    def __len__(self):
        return len(self._value)

    def __iter__(self):
        return iter(self._value)

    def __getitem__(self, key):
        return self._value[key]

    def __hash__(self) -> int:
        try:
            return hash(self._value)
        except TypeError:
            return id(self)

    def __getattr__(self, name: str):
        return getattr(self._value, name)

    @staticmethod
    def _coerce(other: Any) -> Any:
        return other._value if isinstance(other, _SyncAsyncValue) else other

    def __eq__(self, other: Any) -> bool:
        return self._value == self._coerce(other)

    def __lt__(self, other: Any) -> bool:
        return self._value < self._coerce(other)

    def __le__(self, other: Any) -> bool:
        return self._value <= self._coerce(other)

    def __gt__(self, other: Any) -> bool:
        return self._value > self._coerce(other)

    def __ge__(self, other: Any) -> bool:
        return self._value >= self._coerce(other)

    def __add__(self, other: Any):
        return self._value + self._coerce(other)

    def __radd__(self, other: Any):
        return self._coerce(other) + self._value

    def __sub__(self, other: Any):
        return self._value - self._coerce(other)

    def __rsub__(self, other: Any):
        return self._coerce(other) - self._value

    def __mul__(self, other: Any):
        return self._value * self._coerce(other)

    def __rmul__(self, other: Any):
        return self._coerce(other) * self._value

    def __truediv__(self, other: Any):
        return self._value / self._coerce(other)

    def __rtruediv__(self, other: Any):
        return self._coerce(other) / self._value


class LeadScorer:
    """Calculate lead quality scores based on conversation analysis."""

    def __init__(self):
        """Initialize lead scorer with thresholds from config."""
        self.hot_threshold = settings.hot_lead_threshold
        self.warm_threshold = settings.warm_lead_threshold
        self.cache = get_cache_service()

    def _generate_cache_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """Generate a stable cache key from dictionary data."""
        # Sort keys to ensure stability
        data_str = json.dumps(data, sort_keys=True, default=str)
        data_hash = hashlib.md5(data_str.encode()).hexdigest()
        return f"lead_scorer:{prefix}:{data_hash}"

    def calculate(self, context: Dict[str, Any]):
        """
        Calculate lead score based on NUMBER OF QUESTIONS ANSWERED.

        Jorge's Requirement: Count questions answered, not points.
        """
        if context is None:
            return _SyncAsyncValue(0)

        # Check if this is seller mode (Jorge's bot)
        if (
            context.get("seller_preferences")
            or context.get("seller_temperature")
            or "seller" in context.get("conversation_type", "").lower()
        ):
            seller_result = self.calculate_seller_score(context.get("seller_preferences", {}))
            return _SyncAsyncValue(seller_result["questions_answered"])

        # Continue with existing buyer scoring logic...
        questions_answered = 0
        prefs = context.get("extracted_preferences", {})

        # Question 1: Budget/Price Range
        if prefs.get("budget"):
            questions_answered += 1

        # Question 2: Location Preference
        if self._is_meaningful_location(prefs.get("location")):
            questions_answered += 1

        # Question 3: Timeline
        if self._is_meaningful_timeline(prefs.get("timeline")):
            questions_answered += 1

        # Question 4: Property Requirements (beds/baths)
        if prefs.get("bedrooms") or prefs.get("bathrooms"):
            questions_answered += 1

        # Question 5: Financing Status
        if prefs.get("financing"):
            questions_answered += 1

        # Question 6: Motivation (why buying/selling now)
        if prefs.get("motivation"):
            questions_answered += 1

        # Question 7: Must-haves (buyers) or home condition (sellers)
        if prefs.get("must_haves") or prefs.get("home_condition"):
            questions_answered += 1

        return _SyncAsyncValue(questions_answered)

    def get_percentage_score(self, question_count: int) -> int:
        """
        Convert Jorge's question count (0-7) to percentage score (0-100).

        This mapping ensures Jorge's 70+ threshold triggers at 5+ questions answered.

        Mapping:
        - 7 questions = 100% (all qualifying info collected)
        - 6 questions = 85% (nearly complete)
        - 5 questions = 75% (above Jorge's 70% threshold - triggers handoff)
        - 4 questions = 65% (strong engagement)
        - 3 questions = 50% (Hot lead threshold)
        - 2 questions = 30% (Warm lead threshold)
        - 1 question = 15% (minimal engagement)
        - 0 questions = 5% (no engagement)

        Args:
            question_count: Number of questions answered (0-7)

        Returns:
            Percentage score (0-100)
        """
        score_mapping = {
            7: 100,  # All questions answered
            6: 85,  # 6 questions
            5: 75,  # 5 questions (above Jorge's 70 threshold)
            4: 65,  # 4 questions
            3: 50,  # 3 questions (Hot lead)
            2: 30,  # 2 questions (Warm lead)
            1: 15,  # 1 question (Cold lead)
            0: 5,  # No questions answered
        }
        return score_mapping.get(question_count, 0)

    def _is_urgent_timeline(self, timeline: str) -> bool:
        """
        Determine if timeline indicates urgency.

        Args:
            timeline: User's timeline preference (e.g., "ASAP", "next month")

        Returns:
            True if timeline is urgent (< 3 months)
        """
        if not timeline:
            return False

        timeline_lower = timeline.lower()

        # Urgent keywords
        urgent_keywords = [
            "asap",
            "immediately",
            "urgent",
            "this month",
            "next month",
            "this week",
            "next week",
            "soon",
            "right away",
        ]

        return any(keyword in timeline_lower for keyword in urgent_keywords)

    def _is_meaningful_timeline(self, timeline: Any) -> bool:
        """Treat vague discovery-only timelines as unanswered."""
        if not timeline:
            return False
        if not isinstance(timeline, str):
            return True

        timeline_lower = timeline.strip().lower()
        vague_patterns = ["just looking", "no rush", "exploring", "not sure", "someday", "sometime"]
        return not any(pattern in timeline_lower for pattern in vague_patterns)

    def _is_meaningful_location(self, location: Any) -> bool:
        """Treat generic non-committal locations as unanswered."""
        if not location:
            return False
        if not isinstance(location, str):
            return True

        location_lower = location.strip().lower()
        vague_patterns = ["anywhere cheap", "anywhere", "exploring options", "no preference", "wherever"]
        return not any(pattern in location_lower for pattern in vague_patterns)

    def classify(self, score: int) -> str:
        """
        Classify lead based on number of questions answered.

        Jorge's Rules:
        - Hot: 3+ questions answered
        - Warm: 2 questions answered
        - Cold: 0-1 questions answered

        Args:
            score: Number of questions answered (0-7)

        Returns:
            Lead classification: "hot", "warm", or "cold"
        """
        if score >= self.hot_threshold:  # 3+
            return "hot"
        elif score >= self.warm_threshold:  # 2
            return "warm"
        else:  # 0-1
            return "cold"

    def get_recommended_actions(self, score: int) -> List[str]:
        """
        Get recommended actions based on lead score.

        Args:
            score: Lead score (0-100)

        Returns:
            List of recommended actions for the agent
        """
        classification = self.classify(score)

        if classification == "hot":
            return [
                "Tag as 'Hot Lead'",
                "Notify agent via SMS immediately",
                "Schedule showing within 24-48 hours",
                "Prioritize in CRM dashboard",
                "Send pre-approval checklist if not completed",
            ]
        elif classification == "warm":
            return [
                "Tag as 'Warm Lead'",
                "Follow up within 24 hours",
                "Send market update email",
                "Add to weekly follow-up sequence",
            ]
        else:
            return [
                "Tag as 'Cold Lead'",
                "Add to nurture campaign",
                "Send educational content",
                "Follow up in 7 days",
            ]

    def calculate_with_reasoning(self, context: Dict[str, Any]):
        """
        Calculate score with detailed reasoning breakdown.

        Returns question count (0-7) instead of points (0-100).

        Args:
            context: Conversation context

        Returns:
            Dict containing score, classification, reasoning, and recommended actions
        """
        if context is None:
            return _SyncAsyncValue({
                "score": 0,
                "questions_answered": 0,
                "classification": "cold",
                "reasoning": "No qualifying questions answered yet",
                "recommended_actions": self.get_recommended_actions(0),
            })

        score = int(self.calculate(context))
        classification = self.classify(score)
        actions = self.get_recommended_actions(score)

        # Build reasoning breakdown - show which questions were answered
        prefs = context.get("extracted_preferences", {})
        questions_answered = []

        if prefs.get("budget"):
            questions_answered.append(
                f"Budget: ${prefs.get('budget'):,}"
                if isinstance(prefs.get("budget"), (int, float))
                else f"Budget: {prefs.get('budget')}"
            )
        if self._is_meaningful_location(prefs.get("location")):
            questions_answered.append(f"Location: {prefs.get('location')}")
        if self._is_meaningful_timeline(prefs.get("timeline")):
            questions_answered.append(f"Timeline: {prefs.get('timeline')}")
        if prefs.get("bedrooms") or prefs.get("bathrooms"):
            prop_details = []
            if prefs.get("bedrooms"):
                prop_details.append(f"{prefs.get('bedrooms')} bed")
            if prefs.get("bathrooms"):
                prop_details.append(f"{prefs.get('bathrooms')} bath")
            # Ensure all items in prop_details are strings
            safe_prop_details = [str(p) for p in prop_details]
            questions_answered.append(f"Property: {', '.join(safe_prop_details)}")
        if prefs.get("must_haves"):
            must_haves = prefs.get("must_haves")
            if isinstance(must_haves, list):
                must_haves_text = ", ".join(str(m) for m in must_haves)
            else:
                must_haves_text = str(must_haves)
            questions_answered.append(f"Must-haves: {must_haves_text}")
        if prefs.get("financing"):
            questions_answered.append(f"Financing: {prefs.get('financing')}")
        if prefs.get("motivation"):
            questions_answered.append(f"Motivation: {prefs.get('motivation')}")
        if prefs.get("home_condition"):
            questions_answered.append(f"Home Condition: {prefs.get('home_condition')}")

        reasoning = (
            " | ".join([str(q) for q in questions_answered])
            if questions_answered
            else "No qualifying questions answered yet"
        )

        return _SyncAsyncValue({
            "score": score,
            "questions_answered": score,  # Make it explicit this is question count
            "classification": classification,
            "reasoning": reasoning,
            "recommended_actions": actions,
        })

    # ==============================================================================
    # JORGE'S SELLER SCORING (4 QUESTIONS)
    # ==============================================================================

    def calculate_seller_score(self, seller_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate seller lead score based on Jorge's 4 questions.

        Jorge's Seller Questions:
        1. Motivation & Relocation destination
        2. Timeline acceptance (30-45 days)
        3. Property condition
        4. Price expectation

        Args:
            seller_data: Dict containing seller qualification data

        Returns:
            Dict with score (0-4), temperature classification, and details
        """
        score = 0
        details = {}

        # Question 1: Motivation (25% weight)
        if seller_data.get("motivation") and seller_data.get("relocation_destination"):
            score += 1
            details["motivation_score"] = 1
        elif seller_data.get("motivation"):
            score += 0.5  # Partial answer
            details["motivation_score"] = 0.5

        # Question 2: Timeline (35% weight - most important for Jorge)
        timeline_score = 0
        if seller_data.get("timeline_acceptable") is True:
            timeline_score = 1
        elif seller_data.get("timeline_acceptable") is False:
            timeline_score = 0.5  # Still answered, but not ideal
        elif seller_data.get("timeline_urgency"):
            timeline_score = 0.3  # Some timeline info but no 30-45 day answer

        score += timeline_score
        details["timeline_score"] = timeline_score

        # Question 3: Property Condition (20% weight)
        if seller_data.get("property_condition"):
            score += 1
            details["condition_score"] = 1

        # Question 4: Price Expectation (20% weight)
        if seller_data.get("price_expectation"):
            score += 1
            details["price_score"] = 1

        # Calculate temperature based on Jorge's rules
        temperature = self._classify_seller_temperature(
            score=score,
            seller_data=seller_data,
            response_quality=seller_data.get("response_quality", 0.5),
            responsiveness=seller_data.get("responsiveness", 0.5),
        )

        # Convert to percentage for consistency with existing system
        percentage_score = int((score / 4) * 100)

        return {
            "raw_score": score,
            "percentage_score": percentage_score,
            "temperature": temperature,
            "details": details,
            "questions_answered": int(score),  # Count of questions essentially answered
            "max_questions": 4,
            "classification": temperature,  # For consistency with existing interface
            "reasoning": self._build_seller_reasoning(seller_data, details),
            "recommended_actions": self._get_seller_actions(temperature, seller_data),
        }

    def _classify_seller_temperature(
        self, score: float, seller_data: Dict[str, Any], response_quality: float, responsiveness: float
    ) -> str:
        """Jorge's seller temperature classification logic"""

        # Hot seller criteria (Jorge's exact requirements)
        if (
            score >= 3.5  # Nearly all questions answered (allow for partial scores)
            and seller_data.get("timeline_acceptable") is True  # 30-45 days acceptable
            and response_quality >= 0.7  # High quality responses
            and responsiveness >= 0.7
        ):  # Responsive to messages
            return "hot"

        # Warm seller criteria
        elif (
            score >= 2.5  # Most questions answered
            and response_quality >= 0.5
        ):  # Decent responses
            return "warm"

        # Cold seller (default)
        else:
            return "cold"

    def _build_seller_reasoning(self, seller_data: Dict[str, Any], details: Dict[str, Any]) -> str:
        """Build reasoning text for seller scoring"""
        reasoning_parts = []

        if seller_data.get("motivation"):
            reason = f"Motivation: {seller_data['motivation']}"
            if seller_data.get("relocation_destination"):
                reason += f" (to {seller_data['relocation_destination']})"
            reasoning_parts.append(reason)

        if seller_data.get("timeline_acceptable") is not None:
            timeline_text = "30-45 days acceptable" if seller_data["timeline_acceptable"] else "Timeline too fast"
            if seller_data.get("timeline_urgency"):
                timeline_text += f" ({seller_data['timeline_urgency']})"
            reasoning_parts.append(f"Timeline: {timeline_text}")

        if seller_data.get("property_condition"):
            reasoning_parts.append(f"Condition: {seller_data['property_condition']}")

        if seller_data.get("price_expectation"):
            price = seller_data["price_expectation"]
            price_text = f"${price:,}" if isinstance(price, (int, float)) else str(price)
            reasoning_parts.append(f"Price: {price_text}")

        return " | ".join(reasoning_parts) if reasoning_parts else "No seller data collected yet"

    def _get_seller_actions(self, temperature: str, seller_data: Dict[str, Any]) -> List[str]:
        """Get recommended actions for seller based on temperature"""

        if temperature == "hot":
            return [
                f"Tag as 'Hot-Seller'",
                "Remove 'Needs Qualifying' tag",
                "Trigger agent notification workflow immediately",
                "Schedule valuation appointment within 24 hours",
                "Priority follow-up if no response",
                "Add 'Seller-Qualified' tag",
            ]
        elif temperature == "warm":
            return [
                f"Tag as 'Warm-Seller'",
                "Send market analysis and recent sales",
                "Follow up within 48 hours",
                "Continue qualification process",
                "Provide educational content about selling process",
            ]
        else:  # cold
            return [
                f"Tag as 'Cold-Seller'",
                "Add to seller nurture sequence",
                "Send quarterly market updates",
                "Follow up in 2-3 days with additional questions",
                "Provide home valuation resources",
            ]

    def calculate_seller_with_reasoning(self, seller_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate seller score with detailed reasoning - Jorge's 4-question version.

        Args:
            seller_data: Seller qualification data

        Returns:
            Complete seller scoring analysis
        """
        return self.calculate_seller_score(seller_data)
