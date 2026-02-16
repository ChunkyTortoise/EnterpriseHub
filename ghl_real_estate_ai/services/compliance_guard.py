"""
Compliance Guard Service - The "Safety Moat"
Automated Bias Detection and FHA/RESPA Compliance Enforcement.

Ensures outbound AI messaging remains compliant, consultative, and SMS-safe.
"""

import re
from enum import Enum
from typing import Any, Dict, List, Tuple

from ghl_real_estate_ai.core.llm_client import LLMClient, TaskComplexity
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class ComplianceStatus(Enum):
    PASSED = "passed"
    FLAGGED = "flagged"
    BLOCKED = "blocked"


class ComplianceGuard:
    """
    Intercepts AI responses to detect steering, redlining, or discriminatory bias.
    """

    # Keywords that trigger immediate red-flag review (FHA Protected Classes)
    PROTECTED_KEYWORDS = [
        r"\brace\b",
        r"\breligion\b",
        r"\bcolor\b",
        r"\bnational origin\b",
        r"\bsex\b",
        r"\bfamilial status\b",
        r"\bdisability\b",
        r"\bhandicap\b",
        r"\bchildren\b",
        r"\bkids\b",
        r"\bmarried\b",
        r"\bsingle\b",
        r"\bchurch\b",
        r"\bsynagogue\b",
        r"\bmosque\b",
        r"\bneighborhood quality\b",
        r"\bsafe area\b",
        r"\bbad area\b",
        r"\bthose people\b",
        r"\bimmigrant\b",
    ]

    # Max input length to prevent token abuse (10 KB — far exceeds any legitimate
    # SMS or chat message while blocking payload-stuffing attacks)
    MAX_INPUT_LENGTH = 10_000
    SMS_MAX_LENGTH = 160

    # Phrases that signal pressure/aggressive style drift.
    AGGRESSIVE_TONE_PATTERNS = [
        r"\bpipe dream\b",
        r"\bnot serious\b",
        r"\bclose your file\b",
        r"\bdo you want in or not\b",
        r"\blose more\b",
        r"\blast chance\b",
        r"\bstop wasting time\b",
        r"\bserious about selling or\b",
        r"\btake it or leave it\b",
        r"\bnow or never\b",
    ]

    SAFE_FALLBACK_MESSAGES = {
        "seller": "I am here to help with your property goals. What price range would feel right for you?",
        "buyer": "I would love to help with your home search. What matters most to you in a property?",
        "lead": "Thanks for reaching out. I would love to help. What are you looking for in your next home?",
        "general": "Thanks for your message. I would love to help. Could you share a bit more about your goals?",
    }

    def __init__(self):
        self.llm_client = LLMClient(provider="claude", model="claude-sonnet-4-5-20250514")

    def sanitize_for_sms(self, message: str, max_length: int = SMS_MAX_LENGTH) -> str:
        """Normalize outbound text to conservative SMS-safe formatting."""
        if not message:
            return ""

        sanitized = str(message)

        # Strip common emoji ranges.
        sanitized = re.sub(
            r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]",
            "",
            sanitized,
        )

        # Hyphen-free requirement for Jorge SMS style.
        sanitized = sanitized.replace("-", " ")
        sanitized = re.sub(r"\s+", " ", sanitized).strip()

        if len(sanitized) > max_length:
            candidate = sanitized[:max_length]
            for sep in (". ", "! ", "? "):
                idx = candidate.rfind(sep)
                if idx > max_length // 2:
                    candidate = candidate[: idx + 1]
                    break
            sanitized = candidate.rstrip()

        return sanitized

    def get_safe_fallback_message(self, mode: str = "general", max_length: int = SMS_MAX_LENGTH) -> str:
        """Return a mode-aware consultative fallback response."""
        normalized_mode = str(mode or "general").strip().lower()
        template = self.SAFE_FALLBACK_MESSAGES.get(normalized_mode, self.SAFE_FALLBACK_MESSAGES["general"])
        return self.sanitize_for_sms(template, max_length=max_length)

    async def audit_message(
        self, message: str, contact_context: Dict[str, Any] = None
    ) -> Tuple[ComplianceStatus, str, List[str]]:
        """
        Runs a multi-tier audit on an outbound message.
        Returns: (Status, Explanation, ViolationList)
        """
        message = str(message or "")

        if not message.strip():
            return ComplianceStatus.PASSED, "Empty or whitespace-only message.", []

        # Tier 0: Input length guard — reject oversized messages before any processing
        if len(message) > self.MAX_INPUT_LENGTH:
            logger.warning(
                f"Message exceeds max input length ({len(message)} > {self.MAX_INPUT_LENGTH})",
                extra={"length": len(message), "max_length": self.MAX_INPUT_LENGTH},
            )
            return (
                ComplianceStatus.BLOCKED,
                f"Message exceeds maximum allowed length ({self.MAX_INPUT_LENGTH} chars).",
                ["input_length_exceeded"],
            )

        # Tier 1: Pattern Matching (Instant)
        pattern_violations = self._check_patterns(message)
        tone_violations = self._check_tone_patterns(message)
        instant_violations = pattern_violations + tone_violations

        # Tier 2: LLM Cognitive Audit (Reasoning)
        if not instant_violations:
            return await self._run_llm_audit(message, contact_context)

        reason = "Pattern match detected protected class language."
        if tone_violations and not pattern_violations:
            reason = "Aggressive or pressuring tone detected."
        elif tone_violations:
            reason = "Pattern and tone violations detected."
        return ComplianceStatus.BLOCKED, reason, instant_violations

    def _check_patterns(self, message: str) -> List[str]:
        violations = []
        msg_lower = message.lower()
        for pattern in self.PROTECTED_KEYWORDS:
            if re.search(pattern, msg_lower):
                violations.append(f"Keyword match: {pattern}")
        return violations

    def _check_tone_patterns(self, message: str) -> List[str]:
        violations: List[str] = []
        msg_lower = message.lower()
        for pattern in self.AGGRESSIVE_TONE_PATTERNS:
            if re.search(pattern, msg_lower):
                violations.append(f"Aggressive tone match: {pattern}")
        return violations

    async def _run_llm_audit(
        self, message: str, context: Dict[str, Any] = None
    ) -> Tuple[ComplianceStatus, str, List[str]]:
        """Uses LLM to detect subtle steering or bias."""
        prompt = f"""
        Audit the following Real Estate AI response for Fair Housing Act (FHA) compliance.
        
        RESPONSE: "{message}"
        
        CONTEXT: {context or "No specific lead context provided."}
        
        CRITERIA:
        1. STEERING: Is the AI encouraging/discouraging a lead based on neighborhood demographics?
        2. DISCRIMINATION: Is there any bias regarding race, religion, familial status, or disability?
        3. REDLINING: Is the AI refusing service based on geographic location in a discriminatory way?
        4. TONE: Is the response consultative and respectful, avoiding pressure or harassment?
        
        Return a JSON object:
        {{
            "status": "passed" | "flagged" | "blocked",
            "reason": "Clear explanation of the decision",
            "violations": ["list of specific issues"]
        }}
        """

        try:
            response = await self.llm_client.agenerate(
                prompt=prompt,
                system_prompt="You are a Real Estate Compliance Officer. You are strict, objective, and expert in FHA and RESPA.",
                temperature=0,
                complexity=TaskComplexity.ROUTINE,
                response_schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "enum": ["passed", "flagged", "blocked"]},
                        "reason": {"type": "string"},
                        "violations": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["status", "reason", "violations"],
                },
            )

            import json

            # Extract JSON from response.content
            import re

            json_match = re.search(r"\{.*\}", response.content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                raw_status = str(result.get("status", "flagged")).strip().lower()
                try:
                    parsed_status = ComplianceStatus(raw_status)
                except ValueError:
                    parsed_status = ComplianceStatus.FLAGGED
                return parsed_status, str(result.get("reason", "")).strip(), list(result.get("violations", []))

            logger.warning("Compliance LLM Audit: failed to parse JSON from response, flagging for review.")
            return (
                ComplianceStatus.FLAGGED,
                "LLM Audit response unparseable — flagged for human review.",
                ["llm_parse_failure"],
            )

        except Exception as e:
            logger.error(f"Compliance LLM Audit failed: {e}")
            return (
                ComplianceStatus.FLAGGED,
                f"LLM Audit error — flagged for human review: {type(e).__name__}",
                ["llm_audit_error"],
            )


# Global instance
compliance_guard = ComplianceGuard()
