"""Prompt safety checker: injection detection and PII scanning."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class SafetyCheckResult:
    is_safe: bool
    issues: list[str]
    risk_score: float  # 0.0-1.0


INJECTION_PATTERNS = [
    (r"ignore\s+(all\s+)?previous\s+instructions", "Instruction override attempt"),
    (r"you\s+are\s+now\s+(?:a|an)\s+\w+", "Role reassignment attempt"),
    (r"system\s*:\s*", "System prompt injection"),
    (r"<\|im_start\|>|<\|im_end\|>", "Chat markup injection"),
    (r"```\s*system", "Code block system prompt injection"),
    (r"do\s+not\s+follow\s+(any\s+)?rules", "Rule override attempt"),
    (r"pretend\s+(you\s+are|to\s+be)", "Identity manipulation"),
    (r"forget\s+(all|everything|your)", "Memory wipe attempt"),
]

PII_PATTERNS = [
    (r"\b\d{3}-\d{2}-\d{4}\b", "SSN detected"),
    (r"\b\d{16}\b", "Credit card number detected"),
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "Email address detected"),
    (r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b", "Phone number detected"),
]


class PromptSafetyChecker:
    """Detects prompt injection attempts and PII in prompt content."""

    def __init__(self, check_pii: bool = True, check_injection: bool = True):
        self.check_pii = check_pii
        self.check_injection = check_injection

    def check(self, content: str) -> SafetyCheckResult:
        issues: list[str] = []
        risk = 0.0

        if self.check_injection:
            for pattern, description in INJECTION_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    issues.append(f"Injection: {description}")
                    risk += 0.3

        if self.check_pii:
            for pattern, description in PII_PATTERNS:
                if re.search(pattern, content):
                    issues.append(f"PII: {description}")
                    risk += 0.2

        risk = min(risk, 1.0)
        return SafetyCheckResult(
            is_safe=len(issues) == 0,
            issues=issues,
            risk_score=risk,
        )

    def check_output(self, output: str) -> SafetyCheckResult:
        """Check LLM output for PII leakage."""
        issues: list[str] = []
        risk = 0.0
        if self.check_pii:
            for pattern, description in PII_PATTERNS:
                if re.search(pattern, output):
                    issues.append(f"Output PII: {description}")
                    risk += 0.3
        risk = min(risk, 1.0)
        return SafetyCheckResult(is_safe=len(issues) == 0, issues=issues, risk_score=risk)
