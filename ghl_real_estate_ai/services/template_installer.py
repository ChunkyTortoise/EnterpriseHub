"""
Template Installer Service
One-click installation of marketplace templates into workflows

This service handles:
- Installing templates as workflows
- Variable substitution
- Workflow activation
- Installation tracking
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class TemplateInstallerService:
    """Service for installing marketplace templates as workflows"""

    def __init__(self, workflows_dir: str = "data/workflows"):
        self.workflows_dir = Path(workflows_dir)
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.installations_file = Path("data/marketplace/installations.json")
        self.installations: List[Dict[str, Any]] = []
        self._load_installations()

    def _load_installations(self):
        """Load installation history"""
        if self.installations_file.exists():
            with open(self.installations_file, "r") as f:
                data = json.load(f)
                self.installations = data.get("installations", [])

    def _save_installations(self):
        """Save installation history"""
        self.installations_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.installations_file, "w") as f:
            json.dump({"installations": self.installations}, f, indent=2)

    def install_template(
        self,
        template: Dict[str, Any],
        tenant_id: str,
        customizations: Optional[Dict[str, Any]] = None,
        workflow_name: Optional[str] = None,
        enabled: bool = True,
    ) -> Dict[str, Any]:
        """
        Install a template as a workflow

        Args:
            template: Template to install
            tenant_id: Tenant/user ID
            customizations: Variable customizations
            workflow_name: Optional custom name for the workflow
            enabled: Whether to enable the workflow immediately

        Returns:
            Installed workflow object
        """
        customizations = customizations or {}

        # Get workflow from template
        workflow_template = template.get("workflow", {})

        # Apply customizations
        workflow = self._apply_customizations(workflow_template, customizations)

        # Generate new workflow ID
        workflow_id = str(uuid.uuid4())

        # Build workflow object
        installed_workflow = {
            "workflow_id": workflow_id,
            "name": workflow_name or template.get("name", "Untitled Workflow"),
            "description": template.get("description", ""),
            "trigger": workflow.get("trigger", {}),
            "actions": workflow.get("actions", []),
            "enabled": enabled,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "created_by": tenant_id,
            "template_id": template.get("id"),
            "template_version": template.get("version", "1.0.0"),
            "execution_count": 0,
            "success_count": 0,
        }

        # Save workflow
        workflow_file = self.workflows_dir / f"{workflow_id}.json"
        with open(workflow_file, "w") as f:
            json.dump(installed_workflow, f, indent=2)

        # Record installation
        installation_record = {
            "installation_id": str(uuid.uuid4()),
            "template_id": template.get("id"),
            "template_name": template.get("name"),
            "workflow_id": workflow_id,
            "tenant_id": tenant_id,
            "customizations": customizations,
            "installed_at": datetime.utcnow().isoformat(),
        }
        self.installations.append(installation_record)
        self._save_installations()

        return installed_workflow

    def _apply_customizations(
        self, workflow: Dict[str, Any], customizations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply variable customizations to workflow

        Args:
            workflow: Workflow template
            customizations: Variable name -> value mapping

        Returns:
            Customized workflow
        """
        import copy

        customized = copy.deepcopy(workflow)

        # Convert to JSON string for easy replacement
        workflow_str = json.dumps(customized)

        # Replace all variables
        for var_name, var_value in customizations.items():
            placeholder = f"{{{{{var_name}}}}}"
            workflow_str = workflow_str.replace(placeholder, str(var_value))

        # Also handle common default variables if not provided
        default_vars = {
            "agent": "Your Agent Name",
            "company": "Your Company",
            "phone": "Your Phone",
            "email": "Your Email",
        }

        for var_name, default_value in default_vars.items():
            if var_name not in customizations:
                placeholder = f"{{{{{var_name}}}}}"
                if placeholder in workflow_str:
                    workflow_str = workflow_str.replace(placeholder, default_value)

        return json.loads(workflow_str)

    def get_installation_history(
        self, tenant_id: Optional[str] = None, template_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get installation history

        Args:
            tenant_id: Filter by tenant
            template_id: Filter by template

        Returns:
            List of installation records
        """
        results = self.installations

        if tenant_id:
            results = [i for i in results if i.get("tenant_id") == tenant_id]

        if template_id:
            results = [i for i in results if i.get("template_id") == template_id]

        return results

    def get_installed_templates(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get all templates installed by a tenant

        Args:
            tenant_id: Tenant ID

        Returns:
            List of installed templates
        """
        installations = self.get_installation_history(tenant_id=tenant_id)

        # Get unique templates
        templates_map = {}
        for installation in installations:
            template_id = installation.get("template_id")
            if template_id and template_id not in templates_map:
                templates_map[template_id] = {
                    "template_id": template_id,
                    "template_name": installation.get("template_name"),
                    "workflow_id": installation.get("workflow_id"),
                    "installed_at": installation.get("installed_at"),
                    "installation_count": 1,
                }
            elif template_id:
                templates_map[template_id]["installation_count"] += 1

        return list(templates_map.values())

    def uninstall_workflow(self, workflow_id: str) -> bool:
        """
        Uninstall/delete a workflow

        Args:
            workflow_id: Workflow ID to delete

        Returns:
            True if successful
        """
        workflow_file = self.workflows_dir / f"{workflow_id}.json"
        if workflow_file.exists():
            workflow_file.unlink()
            return True
        return False

    def validate_customizations(
        self, template: Dict[str, Any], customizations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate customizations before installation

        Args:
            template: Template to validate against
            customizations: Proposed customizations

        Returns:
            Validation result with errors
        """
        errors = []
        warnings = []

        template_vars = {v["name"]: v for v in template.get("variables", [])}

        # Check required variables
        for var_name, var_def in template_vars.items():
            if var_def.get("required", True) and var_name not in customizations:
                errors.append(f"Required variable missing: {var_name}")

        # Check variable types
        for var_name, var_value in customizations.items():
            if var_name in template_vars:
                var_def = template_vars[var_name]
                expected_type = var_def.get("type", "string")

                # Basic type validation
                if expected_type == "string" and not isinstance(var_value, str):
                    warnings.append(f"{var_name} should be a string")
                elif expected_type == "number" and not isinstance(
                    var_value, (int, float)
                ):
                    warnings.append(f"{var_name} should be a number")
                elif expected_type == "boolean" and not isinstance(var_value, bool):
                    warnings.append(f"{var_name} should be a boolean")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def preview_installation(
        self, template: Dict[str, Any], customizations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Preview what the installed workflow will look like

        Args:
            template: Template to preview
            customizations: Variable customizations

        Returns:
            Preview of the customized workflow
        """
        customizations = customizations or {}

        workflow = template.get("workflow", {})
        customized = self._apply_customizations(workflow, customizations)

        return {
            "name": template.get("name"),
            "description": template.get("description"),
            "trigger": customized.get("trigger"),
            "steps_count": len(customized.get("actions", [])),
            "actions_preview": [
                {
                    "action_type": a.get("action_type"),
                    "config_preview": self._preview_config(a.get("config", {})),
                }
                for a in customized.get("actions", [])[:3]  # First 3 actions
            ],
        }

    def _preview_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create a preview of action config (truncate long values)"""
        preview = {}
        for key, value in config.items():
            if isinstance(value, str) and len(value) > 100:
                preview[key] = value[:100] + "..."
            else:
                preview[key] = value
        return preview

    def get_installation_stats(self) -> Dict[str, Any]:
        """Get statistics about installations"""
        total_installations = len(self.installations)

        # Count by template
        template_counts = {}
        for installation in self.installations:
            template_id = installation.get("template_id")
            template_counts[template_id] = template_counts.get(template_id, 0) + 1

        # Most installed templates
        most_installed = sorted(
            template_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        return {
            "total_installations": total_installations,
            "unique_templates": len(template_counts),
            "most_installed": [
                {"template_id": tid, "installations": count}
                for tid, count in most_installed
            ],
        }


# Demo/Test function
def demo_template_installer():
    """Demonstrate template installer capabilities"""
    service = TemplateInstallerService()

    print("⚙️  Template Installer Demo\n")

    # Create a sample template
    sample_template = {
        "id": "tmpl_demo",
        "name": "Demo Welcome Template",
        "description": "A demo template for testing",
        "category": "lead_nurturing",
        "version": "1.0.0",
        "variables": [
            {
                "name": "agentName",
                "type": "string",
                "default": "{{agent}}",
                "description": "Agent's name",
                "required": True,
            },
            {
                "name": "companyName",
                "type": "string",
                "default": "{{company}}",
                "description": "Company name",
                "required": True,
            },
        ],
        "workflow": {
            "trigger": {"trigger_type": "lead_created", "conditions": {}},
            "actions": [
                {
                    "action_id": "action_1",
                    "action_type": "send_sms",
                    "config": {
                        "message": "Hi! I'm {{agentName}} from {{companyName}}. Thanks for reaching out!"
                    },
                    "conditions": [],
                    "delay_seconds": 0,
                }
            ],
        },
    }

    # Validate customizations
    print("1️⃣  Validating customizations...")
    customizations = {"agentName": "Sarah Johnson", "companyName": "Dream Homes Realty"}

    validation = service.validate_customizations(sample_template, customizations)
    print(f"   Valid: {validation['is_valid']}")
    if validation["errors"]:
        print(f"   Errors: {validation['errors']}")

    # Preview installation
    print("\n2️⃣  Previewing installation...")
    preview = service.preview_installation(sample_template, customizations)
    print(f"   Name: {preview['name']}")
    print(f"   Steps: {preview['steps_count']}")
    print(f"   First action: {preview['actions_preview'][0]['action_type']}")
    print(
        f"   Message: {preview['actions_preview'][0]['config_preview'].get('message')}"
    )

    # Install template
    print("\n3️⃣  Installing template...")
    workflow = service.install_template(
        sample_template,
        tenant_id="demo_user",
        customizations=customizations,
        workflow_name="My Welcome Workflow",
    )
    print(f"   ✅ Installed: {workflow['name']}")
    print(f"   Workflow ID: {workflow['workflow_id']}")
    print(f"   Enabled: {workflow['enabled']}")

    # Get installation history
    print("\n4️⃣  Installation History:")
    history = service.get_installation_history(tenant_id="demo_user")
    print(f"   Total installations: {len(history)}")
    for install in history[-3:]:  # Last 3
        print(f"   • {install['template_name']} at {install['installed_at'][:19]}")

    # Get stats
    print("\n5️⃣  Installation Stats:")
    stats = service.get_installation_stats()
    print(f"   Total: {stats['total_installations']}")
    print(f"   Unique templates: {stats['unique_templates']}")

    return service


if __name__ == "__main__":
    demo_template_installer()
