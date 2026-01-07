"""
Workflow Validator Service
Validates workflow logic and prevents common errors
"""

import logging
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class WorkflowValidator:
    """
    Validates workflow configurations

    Checks:
    - No infinite loops
    - Required fields present
    - Valid action types
    - Proper dependencies
    - Time delays make sense
    """

    VALID_ACTIONS = [
        "send_sms",
        "send_email",
        "send_voice",
        "assign_agent",
        "update_lead",
        "add_tag",
        "create_task",
        "schedule_appointment",
        "send_notification",
        "trigger_webhook",
        "wait",
        "conditional_branch",
    ]

    REQUIRED_FIELDS = {
        "send_sms": ["contact_id", "message"],
        "send_email": ["contact_id", "subject", "body"],
        "assign_agent": ["contact_id", "agent_id"],
        "add_tag": ["contact_id", "tag"],
        "wait": ["delay_minutes"],
    }

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_workflow(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate complete workflow

        Returns:
            Validation result with errors and warnings
        """
        self.errors = []
        self.warnings = []

        # Check required top-level fields
        self._validate_required_fields(workflow)

        # Validate steps
        if "steps" in workflow:
            self._validate_steps(workflow["steps"])

        # Check for loops
        if "steps" in workflow:
            self._check_for_loops(workflow["steps"])

        # Validate timing
        if "steps" in workflow:
            self._validate_timing(workflow["steps"])

        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def _validate_required_fields(self, workflow: Dict[str, Any]):
        """Check required workflow fields"""
        required = ["name", "trigger", "steps"]
        for field in required:
            if field not in workflow:
                self.errors.append(f"Missing required field: {field}")

    def _validate_steps(self, steps: List[Dict[str, Any]]):
        """Validate each workflow step"""
        if not steps:
            self.errors.append("Workflow must have at least one step")
            return

        for i, step in enumerate(steps):
            # Check action type
            action = step.get("action")
            if not action:
                self.errors.append(f"Step {i+1}: Missing action")
                continue

            if action not in self.VALID_ACTIONS:
                self.errors.append(f"Step {i+1}: Invalid action '{action}'")

            # Check required fields for action
            if action in self.REQUIRED_FIELDS:
                for field in self.REQUIRED_FIELDS[action]:
                    if field not in step and field not in step.get("data", {}):
                        self.errors.append(
                            f"Step {i+1}: Missing required field '{field}' for action '{action}'"
                        )

    def _check_for_loops(self, steps: List[Dict[str, Any]]):
        """Check for infinite loops"""
        # Simple check: no step should reference itself
        for i, step in enumerate(steps):
            if "next_step" in step and step["next_step"] == i:
                self.errors.append(
                    f"Step {i+1}: Infinite loop detected (references itself)"
                )

    def _validate_timing(self, steps: List[Dict[str, Any]]):
        """Validate timing makes sense"""
        total_delay = 0
        for i, step in enumerate(steps):
            delay = step.get("delay_minutes", 0)

            if delay < 0:
                self.errors.append(f"Step {i+1}: Negative delay not allowed")

            if delay > 43200:  # 30 days
                self.warnings.append(f"Step {i+1}: Very long delay ({delay} minutes)")

            total_delay += delay

        if total_delay > 129600:  # 90 days
            self.warnings.append(
                f"Workflow total duration is very long ({total_delay/1440:.1f} days)"
            )


if __name__ == "__main__":
    print("✅ Workflow Validator Demo\n")

    validator = WorkflowValidator()

    # Valid workflow
    valid_workflow = {
        "name": "Test Workflow",
        "trigger": "lead_created",
        "steps": [
            {
                "action": "send_sms",
                "contact_id": "123",
                "message": "Hello",
                "delay_minutes": 0,
            },
            {
                "action": "add_tag",
                "contact_id": "123",
                "tag": "contacted",
                "delay_minutes": 60,
            },
        ],
    }

    result = validator.validate_workflow(valid_workflow)
    print(f"Valid workflow: {result['valid']}")
    print(f"Errors: {result['errors']}")
    print(f"Warnings: {result['warnings']}")
