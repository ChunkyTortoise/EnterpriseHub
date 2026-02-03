"""
Compliance Guard Service - The "Safety Moat"
Automated Bias Detection and FHA/RESPA Compliance Enforcement.

Ensures that "Confrontational" AI remains 100% compliant with real estate laws.
"""
import re
from typing import Dict, Any, List, Tuple
from enum import Enum
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.core.llm_client import LLMClient, TaskComplexity

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
        r"\brace\b", r"\breligion\b", r"\bcolor\b", r"\bnational origin\b",
        r"\bsex\b", r"\bfamilial status\b", r"\bdisability\b", r"\bhandicap\b",
        r"\bchildren\b", r"\bkids\b", r"\bmarried\b", r"\bsingle\b",
        r"\bchurch\b", r"\bsynagogue\b", r"\bmosque\b", r"\bneighborhood quality\b",
        r"\bsafe area\b", r"\bbad area\b", r"\bthose people\b", r"\bimmigrant\b"
    ]

    # Max input length to prevent token abuse (10 KB — far exceeds any legitimate
    # SMS or chat message while blocking payload-stuffing attacks)
    MAX_INPUT_LENGTH = 10_000

    def __init__(self):
        self.llm_client = LLMClient(provider="claude", model="claude-sonnet-4-5-20250514")

    async def audit_message(self, message: str, contact_context: Dict[str, Any] = None) -> Tuple[ComplianceStatus, str, List[str]]:
        """
        Runs a multi-tier audit on an outbound message.
        Returns: (Status, Explanation, ViolationList)
        """
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

        # Tier 2: LLM Cognitive Audit (Reasoning)
        if not pattern_violations:
            return await self._run_llm_audit(message, contact_context)

        return ComplianceStatus.BLOCKED, "Pattern match detected protected class language.", pattern_violations

    def _check_patterns(self, message: str) -> List[str]:
        violations = []
        msg_lower = message.lower()
        for pattern in self.PROTECTED_KEYWORDS:
            if re.search(pattern, msg_lower):
                violations.append(f"Keyword match: {pattern}")
        return violations

    async def _run_llm_audit(self, message: str, context: Dict[str, Any] = None) -> Tuple[ComplianceStatus, str, List[str]]:
        """Uses LLM to detect subtle steering or bias."""
        prompt = f"""
        Audit the following Real Estate AI response for Fair Housing Act (FHA) compliance.
        
        RESPONSE: "{message}"
        
        CONTEXT: {context or "No specific lead context provided."}
        
        CRITERIA:
        1. STEERING: Is the AI encouraging/discouraging a lead based on neighborhood demographics?
        2. DISCRIMINATION: Is there any bias regarding race, religion, familial status, or disability?
        3. REDLINING: Is the AI refusing service based on geographic location in a discriminatory way?
        4. TONE: Is the "confrontational" tone crossing into harassment?
        
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
                        "violations": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["status", "reason", "violations"]
                }
            )
            
            import json
            # Extract JSON from response.content
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return ComplianceStatus(result["status"]), result["reason"], result["violations"]
            
            logger.warning("Compliance LLM Audit: failed to parse JSON from response, flagging for review.")
            return ComplianceStatus.FLAGGED, "LLM Audit response unparseable — flagged for human review.", ["llm_parse_failure"]

        except Exception as e:
            logger.error(f"Compliance LLM Audit failed: {e}")
            return ComplianceStatus.FLAGGED, f"LLM Audit error — flagged for human review: {type(e).__name__}", ["llm_audit_error"]

# Global instance
compliance_guard = ComplianceGuard()
