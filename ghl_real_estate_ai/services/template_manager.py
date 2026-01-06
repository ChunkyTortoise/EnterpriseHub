"""
Template Manager Service
Export workflows as templates and manage template publishing

This service handles:
- Exporting existing workflows as templates
- Customizing template variables
- Template validation
- Publishing templates to marketplace
- Managing user-created templates
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class TemplateVariable:
    """Variable that can be customized when installing a template"""
    name: str
    type: str
    default: Any
    description: str = ""
    required: bool = True


@dataclass
class ValidationResult:
    """Result of template validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: Dict[str, Any]


class TemplateManagerService:
    """Service for creating and managing workflow templates"""
    
    def __init__(self, data_dir: str = "data/marketplace"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.user_templates_dir = self.data_dir / "user_templates"
        self.user_templates_dir.mkdir(exist_ok=True)
    
    def export_workflow_as_template(
        self,
        workflow: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export an existing workflow as a template
        
        Args:
            workflow: Workflow object to export
            metadata: Optional metadata (name, description, category, etc.)
        
        Returns:
            Template dictionary ready for customization
        """
        # Extract variables from workflow
        variables = self._extract_variables(workflow)
        
        # Build template
        template = {
            "id": f"tmpl_{uuid.uuid4().hex[:8]}",
            "name": metadata.get("name", workflow.get("name", "Untitled Template")),
            "description": metadata.get("description", workflow.get("description", "")),
            "category": metadata.get("category", "custom"),
            "author": metadata.get("author", "User"),
            "version": "1.0.0",
            "icon": metadata.get("icon", "📋"),
            "tags": metadata.get("tags", []),
            "rating": 0.0,
            "reviews_count": 0,
            "downloads_count": 0,
            "price": metadata.get("price", 0),
            "is_premium": metadata.get("is_premium", False),
            "is_featured": False,
            "trigger": workflow.get("trigger", {}).get("trigger_type", "manual"),
            "steps_count": len(workflow.get("actions", [])),
            "estimated_time": metadata.get("estimated_time", "5 minutes"),
            "difficulty": metadata.get("difficulty", "intermediate"),
            "variables": variables,
            "screenshots": metadata.get("screenshots", []),
            "documentation": metadata.get("documentation", ""),
            "workflow": workflow,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }
        
        return template
    
    def _extract_variables(self, workflow: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract customizable variables from workflow
        
        Looks for placeholders like {{variableName}} in workflow config
        """
        variables = []
        seen_vars = set()
        
        # Search through actions for variables
        for action in workflow.get("actions", []):
            config = action.get("config", {})
            
            # Search in all string values
            for key, value in config.items():
                if isinstance(value, str):
                    # Find {{variable}} patterns
                    import re
                    matches = re.findall(r'\{\{(\w+)\}\}', value)
                    for var_name in matches:
                        if var_name not in seen_vars:
                            seen_vars.add(var_name)
                            variables.append({
                                "name": var_name,
                                "type": "string",
                                "default": f"{{{{{var_name}}}}}",
                                "description": f"Value for {var_name}",
                                "required": True
                            })
        
        return variables
    
    def validate_template(self, template: Dict[str, Any]) -> ValidationResult:
        """
        Validate a template before publishing
        
        Args:
            template: Template to validate
        
        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []
        info = {}
        
        # Required fields
        required_fields = [
            "name", "description", "category", "trigger", 
            "workflow", "icon"
        ]
        
        for field in required_fields:
            if not template.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Name validation
        name = template.get("name", "")
        if len(name) < 3:
            errors.append("Template name must be at least 3 characters")
        if len(name) > 100:
            errors.append("Template name must be less than 100 characters")
        
        # Description validation
        description = template.get("description", "")
        if len(description) < 10:
            warnings.append("Description should be at least 10 characters for better discoverability")
        if len(description) > 500:
            warnings.append("Description is very long. Consider shortening it.")
        
        # Workflow validation
        workflow = template.get("workflow", {})
        if not workflow.get("actions"):
            errors.append("Template must have at least one action")
        
        # Check for at least one step
        steps_count = len(workflow.get("actions", []))
        info["steps_count"] = steps_count
        if steps_count == 0:
            errors.append("Template must have at least one step")
        elif steps_count > 20:
            warnings.append(f"Template has {steps_count} steps. Consider breaking into smaller workflows.")
        
        # Category validation
        valid_categories = [
            "lead_nurturing", "re_engagement", "appointments", 
            "transactions", "relationship", "education", "events", "luxury", "custom"
        ]
        if template.get("category") not in valid_categories:
            warnings.append(f"Unknown category: {template.get('category')}. Will be set to 'custom'")
        
        # Variables validation
        variables = template.get("variables", [])
        info["variables_count"] = len(variables)
        if len(variables) > 0:
            info["has_customization"] = True
        
        # Tags validation
        tags = template.get("tags", [])
        if len(tags) == 0:
            warnings.append("Adding tags improves template discoverability")
        elif len(tags) > 10:
            warnings.append("Too many tags. Recommend 3-5 relevant tags.")
        
        # Documentation
        if not template.get("documentation"):
            warnings.append("Adding documentation helps users understand the template")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            info=info
        )
    
    def publish_template(
        self,
        template: Dict[str, Any],
        visibility: str = "private"
    ) -> Dict[str, Any]:
        """
        Publish a template to marketplace or save privately
        
        Args:
            template: Template to publish
            visibility: "public" for marketplace, "private" for personal use
        
        Returns:
            Published template with ID
        """
        # Validate first
        validation = self.validate_template(template)
        if not validation.is_valid:
            raise ValueError(f"Template validation failed: {validation.errors}")
        
        # Ensure template has ID
        if not template.get("id"):
            template["id"] = f"tmpl_{uuid.uuid4().hex[:8]}"
        
        # Set timestamps
        template["created_at"] = datetime.utcnow().isoformat() + "Z"
        template["updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        # Save template
        if visibility == "public":
            # Add to main marketplace templates
            templates_file = self.data_dir / "templates.json"
            if templates_file.exists():
                with open(templates_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {"templates": []}
            
            data["templates"].append(template)
            
            with open(templates_file, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Save as user template
            template_file = self.user_templates_dir / f"{template['id']}.json"
            with open(template_file, 'w') as f:
                json.dump(template, f, indent=2)
        
        return template
    
    def unpublish_template(self, template_id: str) -> bool:
        """
        Remove a template from public marketplace
        
        Args:
            template_id: Template ID to unpublish
        
        Returns:
            True if successful
        """
        templates_file = self.data_dir / "templates.json"
        if not templates_file.exists():
            return False
        
        with open(templates_file, 'r') as f:
            data = json.load(f)
        
        templates = data.get("templates", [])
        original_count = len(templates)
        templates = [t for t in templates if t.get("id") != template_id]
        
        if len(templates) == original_count:
            return False  # Template not found
        
        data["templates"] = templates
        with open(templates_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return True
    
    def get_my_templates(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all templates created by a user
        
        Args:
            user_id: User ID (optional, returns all user templates if None)
        
        Returns:
            List of user templates
        """
        templates = []
        
        for template_file in self.user_templates_dir.glob("*.json"):
            with open(template_file, 'r') as f:
                template = json.load(f)
                
                # Filter by user if specified
                if user_id is None or template.get("author") == user_id:
                    templates.append(template)
        
        return templates
    
    def update_template(
        self,
        template_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update an existing template
        
        Args:
            template_id: Template ID
            updates: Fields to update
        
        Returns:
            Updated template or None if not found
        """
        # Check user templates first
        template_file = self.user_templates_dir / f"{template_id}.json"
        if template_file.exists():
            with open(template_file, 'r') as f:
                template = json.load(f)
            
            template.update(updates)
            template["updated_at"] = datetime.utcnow().isoformat() + "Z"
            
            with open(template_file, 'w') as f:
                json.dump(template, f, indent=2)
            
            return template
        
        return None
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a user template
        
        Args:
            template_id: Template ID
        
        Returns:
            True if deleted
        """
        template_file = self.user_templates_dir / f"{template_id}.json"
        if template_file.exists():
            template_file.unlink()
            return True
        return False
    
    def customize_template(
        self,
        template: Dict[str, Any],
        customizations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply customizations to a template
        
        Args:
            template: Template to customize
            customizations: Dictionary of variable name -> value
        
        Returns:
            Customized workflow ready for installation
        """
        import copy
        workflow = copy.deepcopy(template.get("workflow", {}))
        
        # Replace variables in workflow
        workflow_str = json.dumps(workflow)
        
        for var_name, var_value in customizations.items():
            placeholder = f"{{{{{var_name}}}}}"
            workflow_str = workflow_str.replace(placeholder, str(var_value))
        
        customized_workflow = json.loads(workflow_str)
        
        return customized_workflow


# Demo/Test function
def demo_template_manager():
    """Demonstrate template manager capabilities"""
    service = TemplateManagerService()
    
    print("📝 Template Manager Demo\n")
    
    # Create a sample workflow
    sample_workflow = {
        "workflow_id": "test_workflow",
        "name": "My Custom Welcome",
        "description": "Custom welcome sequence",
        "trigger": {
            "trigger_type": "lead_created",
            "conditions": {}
        },
        "actions": [
            {
                "action_id": "action_1",
                "action_type": "send_sms",
                "config": {
                    "message": "Hi {{firstName}}, I'm {{agentName}} from {{companyName}}!"
                },
                "conditions": [],
                "delay_seconds": 0
            }
        ]
    }
    
    # Export as template
    print("1️⃣  Exporting workflow as template...")
    template = service.export_workflow_as_template(
        sample_workflow,
        metadata={
            "name": "Custom Welcome Template",
            "description": "A personalized welcome message for new leads",
            "category": "lead_nurturing",
            "tags": ["welcome", "custom"],
            "icon": "👋"
        }
    )
    print(f"   ✅ Created template: {template['name']}")
    print(f"   📊 Variables found: {len(template['variables'])}")
    for var in template['variables']:
        print(f"      • {var['name']}: {var['description']}")
    
    # Validate template
    print("\n2️⃣  Validating template...")
    validation = service.validate_template(template)
    print(f"   Valid: {validation.is_valid}")
    if validation.errors:
        print(f"   ❌ Errors: {validation.errors}")
    if validation.warnings:
        print(f"   ⚠️  Warnings: {validation.warnings}")
    print(f"   ℹ️  Info: {validation.info}")
    
    # Publish privately
    print("\n3️⃣  Publishing template (private)...")
    published = service.publish_template(template, visibility="private")
    print(f"   ✅ Published: {published['id']}")
    
    # Get my templates
    print("\n4️⃣  My Templates:")
    my_templates = service.get_my_templates()
    print(f"   Found {len(my_templates)} template(s)")
    for t in my_templates:
        print(f"   • {t['name']} (ID: {t['id']})")
    
    # Customize template
    print("\n5️⃣  Customizing template...")
    customized = service.customize_template(template, {
        "firstName": "John",
        "agentName": "Sarah",
        "companyName": "Dream Homes Realty"
    })
    print(f"   ✅ Customized workflow ready")
    print(f"   Message: {customized['actions'][0]['config']['message']}")
    
    return service


if __name__ == "__main__":
    demo_template_manager()
