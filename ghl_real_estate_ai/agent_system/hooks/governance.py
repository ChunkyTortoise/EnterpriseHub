import os
import threading
from datetime import datetime


class GovernanceAuditor:
    """
    Persists MarketplaceGovernor decisions and SecuritySentry violations.
    Ensures accountability and transparency for Jorge.
    """

    def __init__(self, manifest_path: str = "AUDIT_MANIFEST.md"):
        self.manifest_path = manifest_path
        self._lock = threading.Lock()
        self._ensure_manifest_exists()

    def _ensure_manifest_exists(self):
        if not os.path.exists(self.manifest_path):
            with self._lock:
                with open(self.manifest_path, "w") as f:
                    f.write("# 🛡️ GHL AI Governance Audit Manifest\n\n")
                    f.write("This file is an immutable record of all marketplace skill installations, ")
                    f.write("security guardrail violations, and autonomous governance decisions.\n\n")
                    f.write("---\n\n")

    def log_marketplace_decision(self, skill_name: str, decision: str, reason: str = ""):
        """Logs a decision from the MarketplaceGovernor."""
        timestamp = datetime.now().isoformat()
        status_emoji = "✅" if decision == "APPROVED" else "❌"

        entry = f"\n## {status_emoji} [{timestamp}] Marketplace Decision: {skill_name}\n"
        entry += f"- **Decision**: {decision}\n"
        if reason:
            entry += f"- **Reason**: {reason}\n"
        entry += "\n"

        self._write_to_manifest(entry)

    def log_security_violation(self, agent_name: str, violation_type: str, content: str):
        """Logs a security violation detected by SecuritySentry."""
        timestamp = datetime.now().isoformat()

        entry = f"\n## 🚨 [{timestamp}] SECURITY VIOLATION: {agent_name}\n"
        entry += f"- **Type**: {violation_type}\n"
        snippet = content[:200].replace("\n", " ")
        entry += f"- **Content Snippet**: {snippet}...\n"
        entry += "\n"

        self._write_to_manifest(entry)

    def log_conflict_resolution(self, agents: list, conflict_desc: str, resolution: str):
        """Logs an autonomous conflict resolution event."""
        timestamp = datetime.now().isoformat()

        entry = f"\n## ⚖️ [{timestamp}] Conflict Resolution\n"
        entry += f"- **Agents Involved**: {', '.join(agents)}\n"
        entry += f"- **Conflict**: {conflict_desc}\n"
        entry += f"- **Resolution**: {resolution}\n"
        entry += "\n"

        self._write_to_manifest(entry)

    def log_recovery_event(self, action: str, error: str, resolution: str):
        """Logs an autonomous recovery event from RecoveryOrchestrator."""
        timestamp = datetime.now().isoformat()

        entry = f"\n## 🩹 [{timestamp}] Recovery Event: {action}\n"
        entry += f"- **Failure**: {error}\n"
        entry += f"- **Proposed Recovery**: {resolution}\n"
        entry += "\n"

        self._write_to_manifest(entry)

    def log_roi_milestone(self, metrics: dict):
        """Logs an ROI milestone reached during operations."""
        timestamp = metrics.get("timestamp", datetime.now().isoformat())
        total_value = metrics.get("total_value_generated", 0.0)

        entry = f"\n## 💰 [{timestamp}] ROI Milestone Reached\n"
        entry += f"- **Total Value Generated**: ${total_value:,.2f}\n"
        entry += f"- **Time Saved**: {metrics.get('time_saved_hours', 0)} hours (${metrics.get('time_saved_value', 0):,.2f})\n"
        entry += f"- **Revenue Lift**: ${metrics.get('conversion_lift_value', 0):,.2f} ({metrics.get('matches_found', 0)} matches)\n"
        entry += "\n"

        self._write_to_manifest(entry)

    def _write_to_manifest(self, text: str):
        with self._lock:
            with open(self.manifest_path, "a") as f:
                f.write(text)


# Singleton instance
governance_auditor = GovernanceAuditor()
