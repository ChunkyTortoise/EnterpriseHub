"""
Base Skill and MCP Integration Layer.
Provides a standardized interface for agent capabilities (Skills).
"""
import inspect
from typing import Any, Callable, Dict, List, Optional, Type
from pydantic import BaseModel, Field, create_model
from fastmcp import FastMCP

class SkillMetadata(BaseModel):
    """Metadata for a skill/tool."""
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    requires_auth: bool = False

class Skill:
    """
    A Skill is a unit of capability that an agent can perform.
    Can be exposed via MCP or directly as a Gemini Tool.
    """
    
    def __init__(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        tags: List[str] = None
    ):
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or "No description provided."
        self.tags = tags or []
        
        # Introspect parameters for schema generation
        self.sig = inspect.signature(func)
        self.schema = self._generate_schema()
        
    def _generate_schema(self) -> Dict[str, Any]:
        """Generate a JSON schema from function signature."""
        fields = {}
        for name, param in self.sig.parameters.items():
            if name == 'self': continue
            
            default = ... if param.default == inspect.Parameter.empty else param.default
            annotation = param.annotation if param.annotation != inspect.Parameter.empty else Any
            fields[name] = (annotation, Field(default=default))
            
        # Create a dynamic Pydantic model for validation and schema
        model_name = f"{self.name.capitalize()}Params"
        dynamic_model = create_model(model_name, **fields)
        return dynamic_model.model_json_schema()

    def execute(self, **kwargs) -> Any:
        """Execute the skill with provided arguments."""
        # Validation could be added here using the dynamic model
        return self.func(**kwargs)

    def to_gemini_tool(self) -> Dict[str, Any]:
        """Convert to Gemini tool declaration format."""
        return {
            "function_declarations": [
                {
                    "name": self.name,
                    "description": self.description,
                    "parameters": self.schema
                }
            ]
        }

class SkillRegistry:
    """Central registry for all agent skills."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SkillRegistry, cls).__new__(cls)
            cls._instance.skills = {}
            cls._instance.mcp = FastMCP("EnterpriseHub")
        return cls._instance

    def register(self, name: Optional[str] = None, tags: List[str] = None):
        """Decorator to register a function as a skill."""
        def decorator(func: Callable):
            skill = Skill(func, name=name, tags=tags)
            self.skills[skill.name] = skill
            
            # Also register with FastMCP
            self.mcp.tool()(func)
            
            return func
        return decorator

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def find_relevant_skills(self, query: str, limit: int = 5) -> List[Skill]:
        """
        Simple keyword-based skill discovery. 
        Note: In a full implementation, this would use ChromaDB embeddings.
        """
        relevant = []
        query_words = set(query.lower().split())
        
        for skill in self.skills.values():
            skill_text = (skill.name + " " + skill.description + " " + " ".join(skill.tags)).lower()
            if any(word in skill_text for word in query_words):
                relevant.append(skill)
        
        # Fallback to all if few found, or return limited set
        return relevant[:limit] if relevant else list(self.skills.values())[:limit]

    def get_all_gemini_tools(self) -> List[Dict[str, Any]]:
        """Return all registered skills as Gemini tool declarations."""
        return [skill.to_gemini_tool()["function_declarations"][0] for skill in self.skills.values()]

# Global registry instance
registry = SkillRegistry()

def skill(name: Optional[str] = None, tags: List[str] = None):
    """Convenience decorator for registering skills."""
    return registry.register(name=name, tags=tags)
