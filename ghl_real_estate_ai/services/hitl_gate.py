"""
HITL Gate -- High-Value Human-in-the-Loop Protection.

Intercepts responses for high-composite-score leads or high-value properties,
routing them to human review via GHL Internal Notes instead of SMS.

Thresholds configurable via env:
  HITL_COMPOSITE_THRESHOLD (default: 90)
  HITL_PROPERTY_VALUE_THRESHOLD (default: 1200000)
"""

import os
from typing import Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class HITLGate:
    """Evaluates whether a bot response requires human approval."""

    def __init__(self):
        self.composite_threshold = float(os.getenv("HITL_COMPOSITE_THRESHOLD", "90"))
        self.property_value_threshold = float(os.getenv("HITL_PROPERTY_VALUE_THRESHOLD", "1200000"))

    def evaluate(self, response: Dict, property_value: Optional[float] = None) -> bool:
        """
        Return True if the response requires human approval.

        Triggers when:
        - composite_score > composite_threshold (default 90), OR
        - property_value > property_value_threshold (default $1.2M)
        """
        # Calculate composite score from response fields
        frs = response.get("frs_score", 0.0) or 0.0
        pcs = response.get("pcs_score", 0.0) or 0.0
        financial_readiness = response.get("financial_readiness", 0.0) or 0.0
        buying_motivation = response.get("buying_motivation_score", 0.0) or 0.0

        # Seller: frs + pcs; Buyer: financial_readiness + buying_motivation
        if frs > 0 or pcs > 0:
            composite_score = (frs + pcs) / 2
        elif financial_readiness > 0 or buying_motivation > 0:
            composite_score = (financial_readiness + buying_motivation) / 2
        else:
            composite_score = 0.0

        high_score = composite_score > self.composite_threshold
        high_value = (property_value or 0.0) > self.property_value_threshold

        if high_score or high_value:
            logger.info(
                f"HITL triggered: composite_score={composite_score:.1f} "
                f"(threshold={self.composite_threshold}), "
                f"property_value={property_value} "
                f"(threshold={self.property_value_threshold})"
            )

        return high_score or high_value
