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
