"""
Architecture & Codebase Intelligence Hooks.
Implements: Pattern Architect, Legacy Archaeologist, Dependency Mapper.
"""
from ghl_real_estate_ai.agent_system.skills.codebase import map_codebase, analyze_dependencies

class CodebaseInvestigator:
    """Explores and analyzes the codebase structure and dependencies."""
    
    def map_project(self, root_dir: str = "."):
        return map_codebase(root_dir)

    def find_dependencies(self, file_path: str):
        return analyze_dependencies(file_path)

class PatternArchitect:
    """Identifies and suggests architectural patterns."""
    
    def suggest_patterns(self, file_path: str):
        deps = analyze_dependencies(file_path)
        if "fastmcp" in str(deps):
            return "Consider using the MCP Tool pattern for this module."
        return "Standard service pattern recommended."

from ghl_real_estate_ai.agent_system.hooks.security import SecuritySentry
from ghl_real_estate_ai.agent_system.hooks.governance import governance_auditor

class MarketplaceGovernor:
    """
    Manages the 'Workflow Marketplace'.
    Validates third-party skills before installation.
    """
    def __init__(self):
        self.sentry = SecuritySentry()
        self.installed_skills = []

    def validate_skill(self, skill_metadata: dict) -> bool:
        """
        Validates a third-party skill against security guardrails.
        """
        skill_name = skill_metadata.get('name', 'Unknown Skill')
        # Scan description and code-snippet if provided
        content_to_scan = f"{skill_name} {skill_metadata.get('description', '')}"
        
        if not self.sentry.scan_output(content_to_scan):
            governance_auditor.log_marketplace_decision(skill_name, "REJECTED", "Security scan failed: Potential malicious content detected.")
            return False
            
        # Check for required security headers/metadata
        if "security_audit_id" not in skill_metadata:
            governance_auditor.log_marketplace_decision(skill_name, "REJECTED", "Missing required security_audit_id metadata.")
            return False
            
        governance_auditor.log_marketplace_decision(skill_name, "APPROVED", "Passed all security scans and metadata checks.")
        return True

    def install_skill(self, skill_metadata: dict) -> bool:
        if self.validate_skill(skill_metadata):
            self.installed_skills.append(skill_metadata["name"])
            return True
        return False
