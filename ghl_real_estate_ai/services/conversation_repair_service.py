"""
Wave 2B: Conversation Repair Engine

Detects and recovers from conversational failures in Jorge Bot interactions.
Implements pattern recognition for dead-ends, loops, misunderstandings, and topic drift.

Key Features:
- Dead-end detection: Short/negative responses, disengagement signals
- Loop detection: Repetitive question/answer patterns
- Misunderstanding detection: Confusion signals, clarification requests
- Topic drift detection: Off-topic conversation threads
- Recovery strategies: Context-aware repair prompts and redirects
- A/B testing integration: Track repair success rates

Design Principles:
- Low false positive rate (<5%)
- Fast detection (<50ms)
- Context-aware strategies
- Graceful degradation
"""

import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.bot_context_types import ConversationMessage

logger = get_logger(__name__)


class FailureType(str, Enum):
    """Types of conversational failures."""

    DEAD_END = "dead_end"
    LOOP = "loop"
    MISUNDERSTANDING = "misunderstanding"
    TOPIC_DRIFT = "topic_drift"
    NONE = "none"


@dataclass
class FailureDetection:
    """Result of failure detection analysis."""

    failure_type: FailureType
    confidence: float  # 0.0 to 1.0
    evidence: List[str] = field(default_factory=list)
    severity: float = 0.5  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RepairStrategy:
    """Strategy for repairing a conversation failure."""

    failure_type: FailureType
    approach: str
    prompt_addition: str
    talking_points: List[str] = field(default_factory=list)
    fallback_action: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConversationRepairService:
    """
    Conversation Repair Engine for Jorge Bot.

    Analyzes conversation history to detect failures and suggests
    context-aware recovery strategies.

    Usage:
        service = ConversationRepairService()
        failure = service.detect_failure(conversation_history)
        if failure.failure_type != FailureType.NONE:
            strategy = service.suggest_repair(failure, context)
    """

    # Detection thresholds
    DEAD_END_SHORT_RESPONSE_THRESHOLD = 5  # words
    DEAD_END_CONSECUTIVE_THRESHOLD = 2  # messages
    LOOP_PATTERN_THRESHOLD = 2  # repetitions
    LOOP_SIMILARITY_THRESHOLD = 0.7  # 70% similarity
    MISUNDERSTANDING_CONFIDENCE_THRESHOLD = 0.6
    TOPIC_DRIFT_THRESHOLD = 0.8

    # Real estate keywords for topic detection
    REAL_ESTATE_KEYWORDS = {
        "property",
        "house",
        "home",
        "sell",
        "buy",
        "listing",
        "price",
        "bedroom",
        "bathroom",
        "sqft",
        "agent",
        "market",
        "appraisal",
        "closing",
        "offer",
        "mortgage",
        "realtor",
        "neighborhood",
        "cma",
        "equity",
        "refinance",
        "inspection",
        "escrow",
        "title",
        "zestimate",
        "zillow",
        "redfin",
        "mls",
        "commission",
        "buyer",
        "seller",
        "rent",
        "lease",
        "investment",
        "flip",
        "cash",
        "financing",
    }

    # Confusion/misunderstanding signals
    CONFUSION_PATTERNS = [
        r"\b(what|huh|confused|don\'t understand|not sure|unclear)\b",
        r"\b(mean|saying|talking about)\?",
        r"^(what|huh|say that again)\??$",
        r"\b(explain|clarify|rephrase)\b",
    ]

    # Negative sentiment patterns
    NEGATIVE_PATTERNS = [
        r"\b(no|nope|nah|not interested|not now|maybe later)\b",
        r"\b(busy|later|another time|not ready)\b",
        r"\b(stop|leave me alone|don\'t contact)\b",
    ]

    def __init__(self):
        """Initialize the conversation repair service."""
        self.repair_history: Dict[str, List[Dict]] = {}  # contact_id -> repairs
        self.success_metrics: Dict[FailureType, Dict[str, int]] = {
            failure_type: {"attempts": 0, "successes": 0}
            for failure_type in FailureType
            if failure_type != FailureType.NONE
        }

    def detect_failure(
        self, conversation_history: List[ConversationMessage], context: Optional[Dict[str, Any]] = None
    ) -> FailureDetection:
        """
        Detect conversation failures from message history.

        Args:
            conversation_history: List of conversation messages
            context: Optional context (bot state, metadata)

        Returns:
            FailureDetection with type, confidence, and evidence
        """
        if not conversation_history:
            return FailureDetection(FailureType.NONE, 0.0)

        # Run all detection methods and pick highest confidence
        detections = [
            self._detect_dead_end(conversation_history, context),
            self._detect_loop(conversation_history, context),
            self._detect_misunderstanding(conversation_history, context),
            self._detect_topic_drift(conversation_history, context),
        ]

        # Return detection with highest confidence (if above threshold)
        best_detection = max(detections, key=lambda d: d.confidence)

        # Log detection for monitoring
        if best_detection.failure_type != FailureType.NONE:
            logger.info(
                f"Detected {best_detection.failure_type.value} failure (confidence: {best_detection.confidence:.2f})",
                extra={
                    "failure_type": best_detection.failure_type.value,
                    "confidence": best_detection.confidence,
                    "evidence_count": len(best_detection.evidence),
                },
            )

        return best_detection

    def suggest_repair(self, failure: FailureDetection, context: Optional[Dict[str, Any]] = None) -> RepairStrategy:
        """
        Suggest repair strategy for detected failure.

        Args:
            failure: Detected failure
            context: Optional context (bot state, qualification data)

        Returns:
            RepairStrategy with approach and talking points
        """
        if failure.failure_type == FailureType.NONE:
            return RepairStrategy(
                failure_type=FailureType.NONE,
                approach="continue_normal",
                prompt_addition="",
                talking_points=[],
            )

        # Select strategy based on failure type
        strategy_map = {
            FailureType.DEAD_END: self._repair_dead_end,
            FailureType.LOOP: self._repair_loop,
            FailureType.MISUNDERSTANDING: self._repair_misunderstanding,
            FailureType.TOPIC_DRIFT: self._repair_topic_drift,
        }

        repair_fn = strategy_map.get(failure.failure_type)
        if repair_fn:
            strategy = repair_fn(failure, context or {})
            logger.info(
                f"Generated repair strategy for {failure.failure_type.value}",
                extra={
                    "failure_type": failure.failure_type.value,
                    "approach": strategy.approach,
                },
            )
            return strategy

        # Fallback strategy
        return RepairStrategy(
            failure_type=failure.failure_type,
            approach="generic_recovery",
            prompt_addition="Let me try a different approach to help you better.",
            talking_points=["How can I make this easier for you?"],
        )

    def track_repair_attempt(
        self,
        contact_id: str,
        failure_type: FailureType,
        strategy: RepairStrategy,
    ) -> None:
        """Track repair attempt for analytics."""
        if contact_id not in self.repair_history:
            self.repair_history[contact_id] = []

        self.repair_history[contact_id].append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "failure_type": failure_type.value,
                "approach": strategy.approach,
                "success": None,  # Updated later via track_repair_outcome
            }
        )

        self.success_metrics[failure_type]["attempts"] += 1

    def track_repair_outcome(
        self,
        contact_id: str,
        success: bool,
    ) -> None:
        """Track outcome of most recent repair attempt."""
        if contact_id not in self.repair_history or not self.repair_history[contact_id]:
            return

        # Update most recent repair
        repair = self.repair_history[contact_id][-1]
        repair["success"] = success

        failure_type = FailureType(repair["failure_type"])
        if success:
            self.success_metrics[failure_type]["successes"] += 1

    def get_repair_stats(self, failure_type: Optional[FailureType] = None) -> Dict[str, Any]:
        """Get repair success statistics."""
        if failure_type:
            metrics = self.success_metrics[failure_type]
            success_rate = metrics["successes"] / metrics["attempts"] if metrics["attempts"] > 0 else 0.0
            return {
                "failure_type": failure_type.value,
                "attempts": metrics["attempts"],
                "successes": metrics["successes"],
                "success_rate": round(success_rate, 3),
            }

        # Overall stats
        total_attempts = sum(m["attempts"] for m in self.success_metrics.values())
        total_successes = sum(m["successes"] for m in self.success_metrics.values())
        overall_rate = total_successes / total_attempts if total_attempts > 0 else 0.0

        return {
            "overall": {
                "attempts": total_attempts,
                "successes": total_successes,
                "success_rate": round(overall_rate, 3),
            },
            "by_type": {ft.value: self.get_repair_stats(ft) for ft in FailureType if ft != FailureType.NONE},
        }

    # ── Detection Methods ──────────────────────────────────────────────

    def _detect_dead_end(self, history: List[ConversationMessage], context: Optional[Dict]) -> FailureDetection:
        """Detect dead-end conversations (disengagement)."""
        if len(history) < 2:
            return FailureDetection(FailureType.DEAD_END, 0.0)

        # Analyze recent user messages (last 3)
        user_messages = [msg for msg in history[-6:] if msg.get("role") == "user"][-3:]

        if not user_messages:
            return FailureDetection(FailureType.DEAD_END, 0.0)

        evidence = []
        confidence = 0.0

        # Check for short responses
        short_count = 0
        for msg in user_messages:
            content = msg.get("content", "")
            word_count = len(content.split())

            if word_count <= self.DEAD_END_SHORT_RESPONSE_THRESHOLD:
                short_count += 1
                evidence.append(f"Short response: '{content[:50]}'")

        if short_count >= self.DEAD_END_CONSECUTIVE_THRESHOLD:
            confidence += 0.4

        # Check for negative sentiment
        negative_count = 0
        for msg in user_messages:
            content = msg.get("content", "").lower()
            for pattern in self.NEGATIVE_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    negative_count += 1
                    evidence.append(f"Negative signal: '{content[:50]}'")
                    break

        if negative_count >= 1:
            confidence += 0.3 * min(negative_count, 2)

        # Check for declining engagement
        if len(user_messages) >= 3:
            word_counts = [len(msg.get("content", "").split()) for msg in user_messages]
            if word_counts[0] > word_counts[1] > word_counts[2]:
                evidence.append("Declining engagement pattern")
                confidence += 0.2

        return FailureDetection(
            failure_type=FailureType.DEAD_END if confidence >= 0.5 else FailureType.NONE,
            confidence=min(confidence, 1.0),
            evidence=evidence,
            severity=confidence,
        )

    def _detect_loop(self, history: List[ConversationMessage], context: Optional[Dict]) -> FailureDetection:
        """Detect repetitive conversation loops."""
        if len(history) < 4:
            return FailureDetection(FailureType.LOOP, 0.0)

        # Extract bot and user messages separately
        bot_messages = [msg.get("content", "") for msg in history[-8:] if msg.get("role") in ("assistant", "bot")]
        user_messages = [msg.get("content", "") for msg in history[-8:] if msg.get("role") == "user"]

        if len(bot_messages) < 2 or len(user_messages) < 2:
            return FailureDetection(FailureType.LOOP, 0.0)

        evidence = []
        confidence = 0.0

        # Check for repeated bot questions
        bot_similarity = self._calculate_message_similarity(bot_messages[-3:])
        if bot_similarity >= self.LOOP_SIMILARITY_THRESHOLD:
            evidence.append(f"Repeated bot pattern (similarity: {bot_similarity:.2f})")
            confidence += 0.5

        # Check for repeated user responses
        user_similarity = self._calculate_message_similarity(user_messages[-3:])
        if user_similarity >= self.LOOP_SIMILARITY_THRESHOLD:
            evidence.append(f"Repeated user pattern (similarity: {user_similarity:.2f})")
            confidence += 0.3

        # Check for question-answer loops
        loop_detected = self._detect_qa_loop(history[-8:])
        if loop_detected:
            evidence.append("Question-answer loop detected")
            confidence += 0.3

        return FailureDetection(
            failure_type=FailureType.LOOP if confidence >= 0.6 else FailureType.NONE,
            confidence=min(confidence, 1.0),
            evidence=evidence,
            severity=confidence,
        )

    def _detect_misunderstanding(self, history: List[ConversationMessage], context: Optional[Dict]) -> FailureDetection:
        """Detect user confusion or misunderstanding."""
        if len(history) < 2:
            return FailureDetection(FailureType.MISUNDERSTANDING, 0.0)

        # Analyze recent user messages
        user_messages = [msg for msg in history[-6:] if msg.get("role") == "user"][-3:]

        if not user_messages:
            return FailureDetection(FailureType.MISUNDERSTANDING, 0.0)

        evidence = []
        confidence = 0.0

        # Check for confusion signals
        for msg in user_messages:
            content = msg.get("content", "")
            for pattern in self.CONFUSION_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    evidence.append(f"Confusion signal: '{content[:50]}'")
                    confidence += 0.4
                    break

        # Check for question-heavy responses
        question_count = sum(1 for msg in user_messages if "?" in msg.get("content", ""))
        if question_count >= 2:
            evidence.append(f"Multiple questions ({question_count})")
            confidence += 0.2

        # Check for clarification requests
        clarification_words = ["explain", "mean", "clarify", "rephrase", "what"]
        for msg in user_messages:
            content = msg.get("content", "").lower()
            if any(word in content for word in clarification_words):
                evidence.append(f"Clarification request: '{content[:50]}'")
                confidence += 0.3
                break

        return FailureDetection(
            failure_type=FailureType.MISUNDERSTANDING
            if confidence >= self.MISUNDERSTANDING_CONFIDENCE_THRESHOLD
            else FailureType.NONE,
            confidence=min(confidence, 1.0),
            evidence=evidence,
            severity=confidence,
        )

    def _detect_topic_drift(self, history: List[ConversationMessage], context: Optional[Dict]) -> FailureDetection:
        """Detect conversation drifting away from real estate."""
        if len(history) < 3:
            return FailureDetection(FailureType.TOPIC_DRIFT, 0.0)

        # Analyze recent user messages
        user_messages = [msg for msg in history[-6:] if msg.get("role") == "user"][-3:]

        if not user_messages:
            return FailureDetection(FailureType.TOPIC_DRIFT, 0.0)

        evidence = []
        confidence = 0.0

        # Check real estate keyword density
        total_words = 0
        re_word_count = 0

        for msg in user_messages:
            content = msg.get("content", "").lower()
            words = set(re.findall(r"\b\w+\b", content))
            total_words += len(words)
            re_words = words & self.REAL_ESTATE_KEYWORDS
            re_word_count += len(re_words)

        if total_words > 10:  # Need minimum word count for valid density check
            re_density = re_word_count / total_words

            if re_density < 0.03:  # Less than 3% real estate keywords
                evidence.append(f"Low RE keyword density ({re_density:.2%})")
                confidence = 0.85
            elif re_density < 0.10:  # Less than 10%
                evidence.append(f"Moderate RE keyword density ({re_density:.2%})")
                confidence = 0.5
        else:
            # Too few words for reliable density check
            confidence = 0.0

        # Check for off-topic indicators
        off_topic_indicators = [
            "weather",
            "sports",
            "politics",
            "news",
            "recipe",
            "movie",
            "tv show",
            "game",
            "music",
            "restaurant",
        ]

        for msg in user_messages:
            content = msg.get("content", "").lower()
            for indicator in off_topic_indicators:
                if indicator in content:
                    evidence.append(f"Off-topic indicator: '{indicator}'")
                    confidence += 0.3
                    break

        return FailureDetection(
            failure_type=FailureType.TOPIC_DRIFT if confidence >= self.TOPIC_DRIFT_THRESHOLD else FailureType.NONE,
            confidence=min(confidence, 1.0),
            evidence=evidence,
            severity=confidence,
        )

    # ── Repair Strategy Methods ────────────────────────────────────────

    def _repair_dead_end(self, failure: FailureDetection, context: Dict[str, Any]) -> RepairStrategy:
        """Generate repair strategy for dead-end conversations."""
        # Extract context
        qualification_score = context.get("financial_readiness_score", 0)
        has_budget = context.get("budget_range") is not None

        # Tailor approach based on qualification level
        if qualification_score >= 60:
            # High-qualified lead - offer value
            approach = "value_proposition"
            prompt = (
                "I sense you might need a moment. Before you go, I'd love to share "
                "something that might help with your decision."
            )
            talking_points = [
                "I have some market data that could be valuable for your situation",
                "Would it help if I showed you what similar homes are selling for?",
                "Can I send you something helpful to review on your own time?",
            ]
        elif has_budget:
            # Mid-qualified - alternative angle
            approach = "alternative_angle"
            prompt = "I want to make sure I'm asking the right questions. Let me try a different approach."
            talking_points = [
                "What would make this conversation more helpful for you?",
                "Is there a specific concern I can address?",
                "Would you prefer to explore this at a different time?",
            ]
        else:
            # Low-qualified - soft exit with open door
            approach = "soft_exit_open_door"
            prompt = (
                "I appreciate your time today. I don't want to take up more "
                "of your day, but I'm here whenever you're ready."
            )
            talking_points = [
                "Feel free to reach out when you'd like to continue",
                "I can send you some helpful resources in the meantime",
                "Would you like me to check back in a few days?",
            ]

        return RepairStrategy(
            failure_type=FailureType.DEAD_END,
            approach=approach,
            prompt_addition=prompt,
            talking_points=talking_points,
            fallback_action="schedule_followup" if qualification_score >= 40 else "mark_nurture",
        )

    def _repair_loop(self, failure: FailureDetection, context: Dict[str, Any]) -> RepairStrategy:
        """Generate repair strategy for conversation loops."""
        approach = "break_pattern_pivot"
        prompt = (
            "I realize I might be asking the same things. Let me take a different approach that might be more helpful."
        )

        # Suggest pivoting based on context
        current_step = context.get("current_qualification_step", "unknown")

        if "budget" in current_step:
            talking_points = [
                "Instead of specific numbers, what monthly payment would feel comfortable?",
                "Let's talk about what you're hoping to accomplish with this purchase",
                "What matters most to you - location, size, or something else?",
            ]
        elif "property" in current_step:
            talking_points = [
                "Tell me about your ideal day in your new home",
                "What's your favorite thing about where you live now?",
                "If you could change one thing about your current situation, what would it be?",
            ]
        else:
            talking_points = [
                "Let's step back - what brought you to think about this now?",
                "What would success look like for you in this process?",
                "How can I make this easier and more helpful for you?",
            ]

        return RepairStrategy(
            failure_type=FailureType.LOOP,
            approach=approach,
            prompt_addition=prompt,
            talking_points=talking_points,
            fallback_action="escalate_to_human" if failure.severity > 0.8 else None,
        )

    def _repair_misunderstanding(self, failure: FailureDetection, context: Dict[str, Any]) -> RepairStrategy:
        """Generate repair strategy for misunderstandings."""
        approach = "clarify_and_simplify"
        prompt = "I apologize if I wasn't clear. Let me explain this better in simpler terms."

        # Provide examples and analogies
        talking_points = [
            "Think of it this way: [provide simple analogy]",
            "For example, [concrete example from their context]",
            "Let me break this down step by step",
            "Would it help if I showed you a quick example?",
        ]

        return RepairStrategy(
            failure_type=FailureType.MISUNDERSTANDING,
            approach=approach,
            prompt_addition=prompt,
            talking_points=talking_points,
            fallback_action="provide_visual_aid",
            metadata={"use_examples": True, "simplify_language": True},
        )

    def _repair_topic_drift(self, failure: FailureDetection, context: Dict[str, Any]) -> RepairStrategy:
        """Generate repair strategy for topic drift."""
        approach = "gentle_redirect"
        prompt = (
            "I appreciate you sharing that with me. Let me bring us back "
            "to your real estate goals so I can help you best."
        )

        # Acknowledge then redirect
        talking_points = [
            "That's interesting! Speaking of your property search...",
            "I hear you. Now, about finding the right home for you...",
            "Got it. Let's make sure we get you the information you need about...",
        ]

        return RepairStrategy(
            failure_type=FailureType.TOPIC_DRIFT,
            approach=approach,
            prompt_addition=prompt,
            talking_points=talking_points,
            fallback_action="refocus_on_qualification",
            metadata={"acknowledge_first": True},
        )

    # ── Helper Methods ─────────────────────────────────────────────────

    def _calculate_message_similarity(self, messages: List[str]) -> float:
        """Calculate similarity between messages using simple token overlap."""
        if len(messages) < 2:
            return 0.0

        # Tokenize messages
        tokenized = []
        for msg in messages:
            tokens = set(re.findall(r"\b\w+\b", msg.lower()))
            tokenized.append(tokens)

        # Calculate pairwise similarity
        similarities = []
        for i in range(len(tokenized) - 1):
            for j in range(i + 1, len(tokenized)):
                intersection = len(tokenized[i] & tokenized[j])
                union = len(tokenized[i] | tokenized[j])
                similarity = intersection / union if union > 0 else 0.0
                similarities.append(similarity)

        return sum(similarities) / len(similarities) if similarities else 0.0

    def _detect_qa_loop(self, messages: List[ConversationMessage]) -> bool:
        """Detect if same question-answer pattern is repeating."""
        if len(messages) < 4:
            return False

        # Extract Q-A pairs
        pairs = []
        for i in range(len(messages) - 1):
            if messages[i].get("role") in ("assistant", "bot") and messages[i + 1].get("role") == "user":
                q = messages[i].get("content", "")
                a = messages[i + 1].get("content", "")
                pairs.append((q, a))

        # Check for repeated pairs
        if len(pairs) < 2:
            return False

        # Hash pairs for efficient comparison
        hashed_pairs = [hashlib.md5(f"{q}:{a}".encode()).hexdigest()[:8] for q, a in pairs]

        # Check for duplicates
        counter = Counter(hashed_pairs)
        return any(count >= self.LOOP_PATTERN_THRESHOLD for count in counter.values())


# ── Singleton Factory ──────────────────────────────────────────────────

_service_instance: Optional[ConversationRepairService] = None


def get_conversation_repair_service() -> ConversationRepairService:
    """Get or create singleton conversation repair service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ConversationRepairService()
    return _service_instance
