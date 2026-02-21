"""Cross-bot handoff during voice calls."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from voice_ai.pipeline.buyerbot_adapter import BuyerBotAdapter
from voice_ai.pipeline.leadbot_adapter import LeadBotAdapter
from voice_ai.pipeline.llm_processor import LLMProcessor
from voice_ai.pipeline.sellerbot_adapter import SellerBotAdapter

logger = logging.getLogger(__name__)

BOT_ADAPTERS = {
    "lead": LeadBotAdapter,
    "buyer": BuyerBotAdapter,
    "seller": SellerBotAdapter,
}

HANDOFF_CONFIDENCE_THRESHOLD = 0.7


@dataclass
class HandoffDecision:
    """Result of a handoff evaluation."""

    should_handoff: bool
    target_bot: str | None = None
    confidence: float = 0.0
    reason: str = ""


@dataclass
class HandoffManager:
    """Manages cross-bot handoffs during voice calls.

    Monitors conversation signals and triggers handoffs when a caller's intent
    clearly shifts (e.g., lead -> buyer). Includes circular prevention and
    rate limiting consistent with EnterpriseHub's handoff safeguards.
    """

    current_bot_type: str = "lead"
    llm: LLMProcessor | None = None
    _handoff_history: list[dict[str, Any]] = field(default_factory=list, repr=False)
    _last_handoff_time: float = 0.0
    _handoff_cooldown_seconds: float = 300.0  # 5 min cooldown

    def get_current_adapter(self) -> LeadBotAdapter | BuyerBotAdapter | SellerBotAdapter:
        """Return the adapter for the current bot type."""
        adapter_cls = BOT_ADAPTERS.get(self.current_bot_type, LeadBotAdapter)
        return adapter_cls()

    def evaluate_handoff(self, conversation_history: list[dict[str, str]]) -> HandoffDecision:
        """Evaluate whether a handoff should occur based on conversation signals."""
        if not conversation_history:
            return HandoffDecision(should_handoff=False)

        # Check cooldown
        now = time.monotonic()
        if now - self._last_handoff_time < self._handoff_cooldown_seconds:
            return HandoffDecision(should_handoff=False, reason="Cooldown active")

        # Check for circular handoff
        if self._handoff_history:
            last = self._handoff_history[-1]
            if last.get("from") == self.current_bot_type:
                return HandoffDecision(should_handoff=False, reason="Circular handoff prevented")

        # Use current adapter to extract signals
        adapter = self.get_current_adapter()
        if not hasattr(adapter, "extract_handoff_signals"):
            return HandoffDecision(should_handoff=False)

        signals = adapter.extract_handoff_signals(conversation_history)

        # Find the strongest signal that isn't the current bot
        best_target = None
        best_confidence = 0.0
        for target, confidence in signals.items():
            if target != self.current_bot_type and confidence > best_confidence:
                best_target = target
                best_confidence = confidence

        if best_target and best_confidence >= HANDOFF_CONFIDENCE_THRESHOLD:
            return HandoffDecision(
                should_handoff=True,
                target_bot=best_target,
                confidence=best_confidence,
                reason=f"Strong {best_target} intent detected",
            )

        return HandoffDecision(should_handoff=False)

    async def execute_handoff(
        self, target_bot: str, conversation_history: list[dict[str, str]]
    ) -> str:
        """Execute a handoff to the target bot.

        Returns the new bot's greeting message.
        """
        old_bot = self.current_bot_type
        self.current_bot_type = target_bot
        self._last_handoff_time = time.monotonic()
        self._handoff_history.append(
            {
                "from": old_bot,
                "to": target_bot,
                "time": self._last_handoff_time,
            }
        )

        new_adapter = self.get_current_adapter()

        # Update LLM system prompt for the new bot
        if self.llm:
            self.llm.set_system_prompt(new_adapter.get_system_prompt())

        logger.info("Handoff executed: %s -> %s", old_bot, target_bot)
        return new_adapter.get_greeting()
