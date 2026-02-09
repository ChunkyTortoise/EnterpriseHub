"""Data models for the response post-processing pipeline."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ProcessingAction(str, Enum):
    """Actions the pipeline can take on a response."""

    PASS = "pass"
    MODIFY = "modify"
    BLOCK = "block"
    SHORT_CIRCUIT = "short_circuit"


class ComplianceFlagSeverity(str, Enum):
    """Severity levels for compliance flags."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ComplianceFlag:
    """A compliance issue detected during processing."""

    stage: str
    category: str
    severity: ComplianceFlagSeverity
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingContext:
    """Context passed through all pipeline stages.

    Stages can read and write to this context to share state.
    """

    contact_id: str = ""
    bot_mode: str = "general"  # "lead", "buyer", "seller", "general"
    channel: str = "sms"  # "sms", "email", "chat", "whatsapp"
    user_message: str = ""
    detected_language: str = "en"
    is_opt_out: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessedResponse:
    """Result after all pipeline stages have run."""

    message: str
    original_message: str
    action: ProcessingAction = ProcessingAction.PASS
    compliance_flags: List[ComplianceFlag] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    context: Optional[ProcessingContext] = None
    stage_log: List[str] = field(default_factory=list)
