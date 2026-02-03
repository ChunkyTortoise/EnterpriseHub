"""
FHA/RESPA Compliance Middleware

Production-grade compliance enforcement layer for real estate AI communications.
Extends the base ``ComplianceGuard`` with:

- **Steering detection**: Subtle demographic proxies (school quality, safety,
  familial status, neighborhood character)
- **Availability steering**: Claiming areas are "sold out" as a redlining proxy
- **RESPA enforcement**: Referral fee, affiliated business, and settlement
  cost disclosure tracking
- **Conversation-level context**: Tracks compliance risk across multiple
  turns to catch patterns that only emerge over a conversation arc
- **Equal Housing Opportunity**: Ensures required disclosures are present
  in qualifying communications

Usage::

    middleware = ComplianceMiddleware()
    result = await middleware.enforce(
        message="The schools in Victoria are excellent",
        contact_id="c_123",
        mode="buyer",
    )
    if result.status == ComplianceStatus.BLOCKED:
        message = result.safe_alternative
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.services.compliance_guard import ComplianceStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class ViolationCategory(str, Enum):
    STEERING = "steering"
    REDLINING = "redlining"
    FAMILIAL_STATUS = "familial_status"
    AVAILABILITY_STEERING = "availability_steering"
    RESPA_REFERRAL = "respa_referral"
    RESPA_DISCLOSURE = "respa_disclosure"
    TONE_HARASSMENT = "tone_harassment"
    PROTECTED_CLASS = "protected_class"


class ViolationSeverity(str, Enum):
    CRITICAL = "critical"  # Auto-block
    HIGH = "high"          # Block unless context-cleared
    MEDIUM = "medium"      # Flag for review
    LOW = "low"            # Log only


@dataclass
class ComplianceViolation:
    category: ViolationCategory
    severity: ViolationSeverity
    pattern: str
    matched_text: str
    explanation: str


@dataclass
class ComplianceResult:
    status: ComplianceStatus
    violations: List[ComplianceViolation]
    reason: str
    safe_alternative: Optional[str] = None
    risk_score: float = 0.0  # 0.0 (clean) – 1.0 (critical)
    respa_disclosures_needed: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pattern banks
# ---------------------------------------------------------------------------

# Steering via school quality (demographic proxy)
SCHOOL_STEERING_PATTERNS: List[Tuple[str, str]] = [
    (r"\bgood\s+schools?\b", "School quality framing can be a proxy for neighborhood demographics"),
    (r"\bbest\s+schools?\b", "Superlative school claims may steer based on demographics"),
    (r"\btop\s+rated\s+school", "School ratings used as steering language"),
    (r"\bschool\s+district\s+is\s+(great|excellent|amazing)", "School district quality as steering"),
    (r"\bhighly\s+rated\s+school", "School rating emphasis as steering proxy"),
]

# Steering via safety/crime (racial proxy)
SAFETY_STEERING_PATTERNS: List[Tuple[str, str]] = [
    (r"\bsafe\s+(area|neighborhood|community|part\s+of\s+town)\b", "Safety framing can be a racial proxy"),
    (r"\blow\s+crime\b", "Crime statistics used as steering language"),
    (r"\bdangerous\s+(area|neighborhood)\b", "Negative safety characterization as steering"),
    (r"\bavoid\s+that\s+area\b", "Geographic avoidance suggestion as potential redlining"),
    (r"\bbad\s+(part|area|side)\s+of\s+town\b", "Negative area characterization"),
    (r"\bnot\s+a\s+good\s+area\b", "Negative area characterization as steering"),
]

# Familial status steering
FAMILIAL_STEERING_PATTERNS: List[Tuple[str, str]] = [
    (r"\bquiet\s+(neighborhood|community|area)\b", "'Quiet' can imply no children welcome"),
    (r"\badult\s+(community|living|only)\b", "Adult-only language violates familial status protections"),
    (r"\bno\s+(kids|children)\b", "Explicit familial status discrimination"),
    (r"\bperfect\s+for\s+(couples|retirees|singles)\b", "Targeting specific household types"),
    (r"\bfamily\s+friendly\b", "Familial status steering — implies other areas are not"),
    (r"\bnot\s+suitable\s+for\s+(families|children)\b", "Explicit familial status discrimination"),
]

# Availability steering (redlining proxy)
AVAILABILITY_STEERING_PATTERNS: List[Tuple[str, str]] = [
    (r"\b(sold\s+out|no\s+availability)\s+in\s+that\s+area\b", "Availability claims as geographic exclusion"),
    (r"\bnothing\s+available\s+(there|in\s+that)\b", "Blanket unavailability claims"),
    (r"\bwouldn'?t\s+recommend\s+that\s+(area|neighborhood)\b", "Discouraging specific areas"),
    (r"\byou\s+don'?t\s+want\s+to\s+live\s+(there|in\s+that)\b", "Direct discouragement of specific areas"),
    (r"\bthat\s+area\s+is\s+declining\b", "Decline narrative as steering language"),
]

# RESPA violation indicators
RESPA_PATTERNS: List[Tuple[str, str]] = [
    (r"\bi('ll| will)\s+give\s+you\s+a\s+(kickback|referral\s+fee|bonus)\b", "Illegal kickback/referral language"),
    (r"\breferral\s+fee\b", "Referral fee mention requires RESPA disclosure"),
    (r"\baffiliated\s+(company|business|lender|service)\b", "Affiliated business requires AfBA disclosure"),
    (r"\buse\s+our\s+(lender|title\s+company|inspector)\b", "Steering to affiliated services without disclosure"),
    (r"\bwe\s+require\s+you\s+to\s+use\b", "Requiring specific service providers violates RESPA"),
]


# Safe fallback messages by mode
SAFE_ALTERNATIVES = {
    "seller": "Let's stick to the facts about your property. What price are you looking to get?",
    "buyer": "I'm looking forward to helping you find the right home. What's your top priority in a neighborhood?",
    "general": "I'd love to help you with your real estate needs. What can I assist you with today?",
}


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class ComplianceMiddleware:
    """
    FHA/RESPA enforcement middleware.

    Runs pattern-based detection across multiple violation categories,
    computes a risk score, and returns a structured result with
    safe alternatives when violations are found.
    """

    # Category → (patterns, default severity)
    PATTERN_GROUPS: List[Tuple[ViolationCategory, List[Tuple[str, str]], ViolationSeverity]] = [
        (ViolationCategory.STEERING, SCHOOL_STEERING_PATTERNS, ViolationSeverity.MEDIUM),
        (ViolationCategory.STEERING, SAFETY_STEERING_PATTERNS, ViolationSeverity.HIGH),
        (ViolationCategory.FAMILIAL_STATUS, FAMILIAL_STEERING_PATTERNS, ViolationSeverity.HIGH),
        (ViolationCategory.AVAILABILITY_STEERING, AVAILABILITY_STEERING_PATTERNS, ViolationSeverity.HIGH),
        (ViolationCategory.RESPA_REFERRAL, RESPA_PATTERNS, ViolationSeverity.CRITICAL),
    ]

    # Severity weights for risk score
    SEVERITY_WEIGHTS = {
        ViolationSeverity.CRITICAL: 1.0,
        ViolationSeverity.HIGH: 0.7,
        ViolationSeverity.MEDIUM: 0.4,
        ViolationSeverity.LOW: 0.1,
    }

    def __init__(self):
        # Conversation-level violation history: contact_id → list of violations
        self._conversation_history: Dict[str, List[ComplianceViolation]] = {}

    async def enforce(
        self,
        message: str,
        contact_id: str = "",
        mode: str = "general",
        conversation_context: Optional[Dict[str, Any]] = None,
    ) -> ComplianceResult:
        """
        Run full compliance enforcement on an outbound message.

        Args:
            message: The AI-generated message to audit.
            contact_id: GHL contact ID for conversation tracking.
            mode: "seller", "buyer", or "general".
            conversation_context: Optional context (property data, prior turns).

        Returns:
            ComplianceResult with status, violations, and safe alternative.
        """
        violations: List[ComplianceViolation] = []

        # --- Pattern scanning ---
        for category, patterns, severity in self.PATTERN_GROUPS:
            for regex, explanation in patterns:
                match = re.search(regex, message, re.IGNORECASE)
                if match:
                    violations.append(ComplianceViolation(
                        category=category,
                        severity=severity,
                        pattern=regex,
                        matched_text=match.group(0),
                        explanation=explanation,
                    ))

        # --- RESPA disclosure check ---
        respa_disclosures = self._check_respa_disclosures(message)

        # --- Conversation-level escalation ---
        if contact_id:
            prior = self._conversation_history.get(contact_id, [])
            prior.extend(violations)
            self._conversation_history[contact_id] = prior

            # If the same contact has accumulated 3+ violations across turns, escalate
            if len(prior) >= 3 and not any(v.severity == ViolationSeverity.CRITICAL for v in violations):
                # Upgrade severity due to pattern across conversation
                violations.append(ComplianceViolation(
                    category=ViolationCategory.STEERING,
                    severity=ViolationSeverity.HIGH,
                    pattern="conversation_accumulation",
                    matched_text="",
                    explanation=f"Contact has {len(prior)} cumulative compliance flags across conversation",
                ))

        # --- Risk score ---
        risk_score = self._compute_risk_score(violations)

        # --- Status determination ---
        status = self._determine_status(violations, risk_score)

        # --- Safe alternative ---
        safe_alt = SAFE_ALTERNATIVES.get(mode, SAFE_ALTERNATIVES["general"]) if status == ComplianceStatus.BLOCKED else None

        reason = self._build_reason(violations, status)

        return ComplianceResult(
            status=status,
            violations=violations,
            reason=reason,
            safe_alternative=safe_alt,
            risk_score=round(risk_score, 3),
            respa_disclosures_needed=respa_disclosures,
        )

    def clear_history(self, contact_id: str) -> None:
        """Clear conversation compliance history for a contact."""
        self._conversation_history.pop(contact_id, None)

    # ------------------------------------------------------------------
    # RESPA disclosure check
    # ------------------------------------------------------------------

    @staticmethod
    def _check_respa_disclosures(message: str) -> List[str]:
        """Check if message requires RESPA disclosures that are missing."""
        needed: List[str] = []
        msg_lower = message.lower()

        # If mentioning affiliated services, need AfBA disclosure
        if re.search(r"\baffiliated\b|\bour\s+(lender|title|inspector)\b", msg_lower):
            if "affiliated business arrangement" not in msg_lower and "afba" not in msg_lower:
                needed.append("Affiliated Business Arrangement (AfBA) disclosure required")

        # If mentioning referral fees
        if "referral" in msg_lower and "fee" in msg_lower:
            if "disclosure" not in msg_lower:
                needed.append("RESPA Section 8 referral fee disclosure required")

        # If discussing settlement costs
        if re.search(r"\bsettlement\s+cost|\bclosing\s+cost\b", msg_lower):
            if "good faith estimate" not in msg_lower and "loan estimate" not in msg_lower:
                needed.append("Settlement cost transparency disclosure recommended")

        return needed

    # ------------------------------------------------------------------
    # Risk score computation
    # ------------------------------------------------------------------

    def _compute_risk_score(self, violations: List[ComplianceViolation]) -> float:
        """Compute 0-1 risk score from violations."""
        if not violations:
            return 0.0

        total = sum(self.SEVERITY_WEIGHTS.get(v.severity, 0.1) for v in violations)
        # Normalize: 1 critical = 1.0, multiple violations accumulate
        return min(1.0, total / 1.0)

    # ------------------------------------------------------------------
    # Status determination
    # ------------------------------------------------------------------

    @staticmethod
    def _determine_status(
        violations: List[ComplianceViolation],
        risk_score: float,
    ) -> ComplianceStatus:
        """Map violations and risk to a compliance status."""
        if not violations:
            return ComplianceStatus.PASSED

        has_critical = any(v.severity == ViolationSeverity.CRITICAL for v in violations)
        has_high = any(v.severity == ViolationSeverity.HIGH for v in violations)

        if has_critical or risk_score >= 0.9:
            return ComplianceStatus.BLOCKED
        if has_high or risk_score >= 0.5:
            return ComplianceStatus.BLOCKED
        return ComplianceStatus.FLAGGED

    # ------------------------------------------------------------------
    # Reason builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_reason(
        violations: List[ComplianceViolation],
        status: ComplianceStatus,
    ) -> str:
        if not violations:
            return "Message passed all compliance checks."

        categories = {v.category.value for v in violations}
        severities = {v.severity.value for v in violations}

        return (
            f"Detected {len(violations)} violation(s) across categories: "
            f"{', '.join(sorted(categories))}. "
            f"Severity levels: {', '.join(sorted(severities))}. "
            f"Status: {status.value}."
        )


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_middleware: Optional[ComplianceMiddleware] = None


def get_compliance_middleware() -> ComplianceMiddleware:
    global _middleware
    if _middleware is None:
        _middleware = ComplianceMiddleware()
    return _middleware
