"""
Workflow Version Control System
Track changes, rollback, and A/B testing
"""

import copy
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WorkflowVersionControl:
    """
    Version control for workflows

    Features:
    - Save workflow versions
    - Rollback to previous versions
    - Compare versions
    - A/B test variants
    - Change tracking
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.versions = {}  # In production, this would be database

    def save_version(
        self,
        workflow_id: str,
        workflow_data: Dict[str, Any],
        message: str = "Updated workflow",
    ) -> str:
        """
        Save new version of workflow

        Args:
            workflow_id: Workflow ID
            workflow_data: Complete workflow configuration
            message: Version commit message

        Returns:
            Version ID
        """
        if workflow_id not in self.versions:
            self.versions[workflow_id] = []

        version_number = len(self.versions[workflow_id]) + 1
        version_id = f"{workflow_id}_v{version_number}"

        version = {
            "version_id": version_id,
            "version_number": version_number,
            "workflow_id": workflow_id,
            "data": copy.deepcopy(workflow_data),
            "message": message,
            "created_at": datetime.now().isoformat(),
            "created_by": "system",  # In production, track user
        }

        self.versions[workflow_id].append(version)
        logger.info(f"Saved version {version_number} of workflow {workflow_id}")

        return version_id

    def get_version(self, workflow_id: str, version_number: int) -> Optional[Dict[str, Any]]:
        """Get specific version"""
        if workflow_id not in self.versions:
            return None

        versions = self.versions[workflow_id]
        if version_number < 1 or version_number > len(versions):
            return None

        return versions[version_number - 1]

    def get_latest_version(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get latest version"""
        if workflow_id not in self.versions or not self.versions[workflow_id]:
            return None

        return self.versions[workflow_id][-1]

    def list_versions(self, workflow_id: str) -> List[Dict[str, Any]]:
        """List all versions"""
        if workflow_id not in self.versions:
            return []

        return [
            {
                "version_number": v["version_number"],
                "message": v["message"],
                "created_at": v["created_at"],
                "created_by": v["created_by"],
            }
            for v in self.versions[workflow_id]
        ]

    def rollback(self, workflow_id: str, version_number: int) -> Optional[Dict[str, Any]]:
        """
        Rollback to previous version

        Creates new version with old data
        """
        old_version = self.get_version(workflow_id, version_number)
        if not old_version:
            logger.error(f"Version {version_number} not found for workflow {workflow_id}")
            return None

        # Create new version with old data
        new_version_id = self.save_version(workflow_id, old_version["data"], f"Rolled back to version {version_number}")

        logger.info(f"Rolled back workflow {workflow_id} to version {version_number}")
        return self.get_latest_version(workflow_id)

    def compare_versions(self, workflow_id: str, version1: int, version2: int) -> Dict[str, Any]:
        """Compare two versions"""
        v1 = self.get_version(workflow_id, version1)
        v2 = self.get_version(workflow_id, version2)

        if not v1 or not v2:
            return {"error": "Version not found"}

        differences = {"version1": version1, "version2": version2, "changes": []}

        # Simple comparison (in production, do deep diff)
        if v1["data"] != v2["data"]:
            differences["changes"].append("Workflow data changed")

        return differences

    def create_ab_variant(self, workflow_id: str, variant_name: str, changes: Dict[str, Any]) -> str:
        """
        Create A/B test variant

        Args:
            workflow_id: Base workflow ID
            variant_name: Name for variant (e.g., "variant_a")
            changes: Changes to make to base workflow

        Returns:
            Variant workflow ID
        """
        base_workflow = self.get_latest_version(workflow_id)
        if not base_workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Create variant data
        variant_data = copy.deepcopy(base_workflow["data"])
        variant_data.update(changes)
        variant_data["is_variant"] = True
        variant_data["base_workflow"] = workflow_id
        variant_data["variant_name"] = variant_name

        # Save as new workflow
        variant_id = f"{workflow_id}_{variant_name}"
        self.save_version(variant_id, variant_data, f"A/B variant: {variant_name}")

        logger.info(f"Created A/B variant {variant_id}")
        return variant_id


if __name__ == "__main__":
    print("📚 Workflow Version Control Demo\n")

    vc = WorkflowVersionControl("tenant_123")

    # Save version 1
    workflow = {"name": "Test", "steps": [{"action": "send_sms"}]}
    v1_id = vc.save_version("wf_001", workflow, "Initial version")
    print(f"✅ Saved v1: {v1_id}")

    # Save version 2
    workflow["steps"].append({"action": "send_email"})
    v2_id = vc.save_version("wf_001", workflow, "Added email step")
    print(f"✅ Saved v2: {v2_id}")

    # List versions
    versions = vc.list_versions("wf_001")
    print(f"\n📋 Versions: {len(versions)}")
    for v in versions:
        print(f"   v{v['version_number']}: {v['message']}")

    # Rollback
    vc.rollback("wf_001", 1)
    print(f"\n↩️  Rolled back to v1")

    # Create A/B variant
    variant_id = vc.create_ab_variant("wf_001", "variant_a", {"steps": [{"action": "wait"}]})
    print(f"🧪 Created A/B variant: {variant_id}")
