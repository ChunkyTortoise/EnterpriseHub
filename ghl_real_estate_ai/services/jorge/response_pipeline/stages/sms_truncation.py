"""SMS-safe truncation and carrier spam guard stage.

Truncates messages at sentence boundaries to stay within SMS character limits.
Preserves AI disclosure footer (SB 243) if present.
Post-truncation: sanitizes carrier spam triggers (excessive caps, spam words,
URL shorteners) to improve deliverability.
"""

import re
import logging

from ghl_real_estate_ai.services.jorge.response_pipeline.base import ResponseProcessorStage
from ghl_real_estate_ai.services.jorge.response_pipeline.models import (
    ProcessedResponse,
    ProcessingAction,
    ProcessingContext,
)

logger = logging.getLogger(__name__)

SMS_MAX_CHARS = 320
SENTENCE_SEPARATORS = (". ", "! ", "? ")
KNOWN_FOOTERS = (
    "\n[AI-assisted message]",
    "\n[Mensaje asistido por IA]",
)

# Carrier AI filter trigger words (case-insensitive all-caps versions get flagged)
SPAM_TRIGGER_WORDS = [
    "FREE", "WIN", "WINNER", "URGENT", "ACT NOW", "LIMITED TIME",
    "CONGRATULATIONS", "CLAIM", "GUARANTEED", "NO OBLIGATION",
]

# URL shortener domains that carriers flag
URL_SHORTENER_PATTERNS = re.compile(
    r"https?://(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|ow\.ly|is\.gd|buff\.ly)/",
    re.IGNORECASE,
)


def _sanitize_spam_triggers(text: str) -> tuple[str, list[str]]:
    """Lowercase carrier spam trigger words found in text.

    Returns:
        Tuple of (sanitized_text, list of warnings).
    """
    warnings: list[str] = []
    result = text
    for word in SPAM_TRIGGER_WORDS:
        # Match the all-caps version as a whole word
        pattern = re.compile(r"\b" + re.escape(word) + r"\b")
        if pattern.search(result):
            replacement = word.capitalize() if len(word) > 3 else word.lower()
            result = pattern.sub(replacement, result)
            warnings.append(f"spam_word_lowered:{word}")
    return result, warnings


def _fix_excessive_caps(text: str, threshold: float = 0.30) -> tuple[str, bool]:
    """Convert text to sentence case if >threshold fraction is uppercase.

    Only operates on real multi-word content (requires spaces).
    Ignores footers/brackets.

    Returns:
        Tuple of (fixed_text, was_fixed).
    """
    # Strip known footer patterns for analysis
    analysis_text = text
    for footer in KNOWN_FOOTERS:
        analysis_text = analysis_text.replace(footer, "")

    # Only check multi-word text (single-token strings aren't real caps abuse)
    if " " not in analysis_text.strip():
        return text, False

    alpha_chars = [c for c in analysis_text if c.isalpha()]
    if not alpha_chars:
        return text, False

    upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
    if upper_ratio > threshold:
        # Convert to sentence case: lowercase everything, then capitalize first char
        # of each sentence
        lowered = text.lower()
        # Capitalize after sentence-ending punctuation
        result = re.sub(
            r"(^|[.!?]\s+)([a-z])",
            lambda m: m.group(1) + m.group(2).upper(),
            lowered,
        )
        # Restore known proper nouns
        result = result.replace("jorge", "Jorge")
        return result, True
    return text, False


def _check_url_shorteners(text: str) -> list[str]:
    """Return warnings for URL shortener domains found in text."""
    matches = URL_SHORTENER_PATTERNS.findall(text)
    if matches:
        return [f"url_shortener_detected:{m}" for m in matches]
    return []


class SMSTruncationProcessor(ResponseProcessorStage):
    """Truncates messages exceeding SMS_MAX_CHARS at sentence boundaries.

    Preserves AI disclosure footers by stripping them before truncation
    and re-appending after, ensuring SB 243 compliance is never broken.

    Post-truncation, applies carrier spam guard:
    - Lowercases spam trigger words (FREE, URGENT, etc.)
    - Converts excessive caps (>30% uppercase) to sentence case
    - Warns on URL shorteners in logs
    """

    def __init__(self, max_chars: int = SMS_MAX_CHARS):
        self._max_chars = max_chars

    @property
    def name(self) -> str:
        return "sms_truncation"

    async def process(
        self,
        response: ProcessedResponse,
        context: ProcessingContext,
    ) -> ProcessedResponse:
        # Only process for SMS channel
        if context.channel != "sms":
            return response

        modified = False

        # --- Truncation ---
        if len(response.message) > self._max_chars:
            # Detect and preserve disclosure footer
            footer = ""
            content = response.message
            for known_footer in KNOWN_FOOTERS:
                if content.endswith(known_footer):
                    footer = known_footer
                    content = content[: -len(known_footer)]
                    break

            # Truncate content portion only, reserving space for footer
            content_limit = self._max_chars - len(footer)
            if len(content) > content_limit:
                truncated = content[:content_limit]
                for sep in SENTENCE_SEPARATORS:
                    idx = truncated.rfind(sep)
                    if idx > content_limit // 2:
                        truncated = truncated[: idx + 1]
                        break
                content = truncated.rstrip()

            response.message = content + footer
            modified = True

            logger.debug(
                "Truncated message for %s from %d to %d chars",
                context.contact_id,
                len(response.original_message),
                len(response.message),
            )

        # --- Carrier Spam Guard ---
        # 1. Sanitize spam trigger words
        response.message, spam_warnings = _sanitize_spam_triggers(response.message)
        if spam_warnings:
            modified = True
            for w in spam_warnings:
                logger.info("Carrier spam guard [%s]: %s", context.contact_id, w)

        # 2. Fix excessive caps
        response.message, caps_fixed = _fix_excessive_caps(response.message)
        if caps_fixed:
            modified = True
            logger.info(
                "Carrier spam guard [%s]: excessive_caps_converted",
                context.contact_id,
            )

        # 3. Warn on URL shorteners (log only, don't modify)
        url_warnings = _check_url_shorteners(response.message)
        for w in url_warnings:
            logger.warning("Carrier spam guard [%s]: %s", context.contact_id, w)

        if modified and response.action == ProcessingAction.PASS:
            response.action = ProcessingAction.MODIFY

        return response
