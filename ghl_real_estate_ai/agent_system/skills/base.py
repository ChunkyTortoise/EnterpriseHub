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
            cls._instance._chroma_client = None
            cls._instance._collection = None
            cls._instance._init_vector_db()
        return cls._instance

    def _init_vector_db(self):
        """Initialize ChromaDB for semantic skill search."""
        try:
            import chromadb
            # Use a persistent path or ephemeral for now
            self._chroma_client = chromadb.Client()
            self._collection = self._chroma_client.get_or_create_collection(
                name="skill_registry",
                metadata={"hnsw:space": "cosine"}
            )
        except (ImportError, Exception) as e:
            # Chromadb might fail due to onnxruntime on some platforms
            # We will gracefully fall back to keyword search
            self._chroma_client = None
            self._collection = None
            print(f"⚠️ ChromaDB Semantic Search unavailable ({str(e)}). Using keyword fallback.")

    def register(self, name: Optional[str] = None, tags: List[str] = None):
        """Decorator to register a function as a skill."""
        def decorator(func: Callable):
            skill = Skill(func, name=name, tags=tags)
            self.skills[skill.name] = skill
            
            # Register with FastMCP
            self.mcp.tool()(func)
            
            # Register with Vector DB
            if self._collection:
                text = f"{skill.name}: {skill.description} {' '.join(skill.tags)}"
                self._collection.upsert(
                    documents=[text],
                    ids=[skill.name],
                    metadatas=[{"name": skill.name, "tags": ",".join(skill.tags)}]
                )
            
            return func
        return decorator

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def find_relevant_skills(self, query: str, limit: int = 5) -> List[Skill]:
        """
        Find relevant skills using Semantic Search (ChromaDB) with keyword fallback.
        """
        # 1. Try Semantic Search
        if self._collection:
            try:
                results = self._collection.query(
                    query_texts=[query],
                    n_results=min(limit, len(self.skills))
                )
                if results['ids'] and results['ids'][0]:
                    found_skills = [self.skills[name] for name in results['ids'][0] if name in self.skills]
                    if found_skills:
                        return found_skills
            except Exception as e:
                # Log error and fall back
                print(f"Vector search failed: {e}")

        # 2. Fallback to Keyword Search
        relevant = []
        query_words = set(query.lower().split())
        
        for skill in self.skills.values():
            skill_text = (skill.name + " " + skill.description + " " + " ".join(skill.tags)).lower()
            if any(word in skill_text for word in query_words):
                relevant.append(skill)
        
        return relevant[:limit] if relevant else list(self.skills.values())[:limit]

    def get_all_gemini_tools(self) -> List[Dict[str, Any]]:
        """Return all registered skills as Gemini tool declarations."""
        return [skill.to_gemini_tool()["function_declarations"][0] for skill in self.skills.values()]

# Global registry instance
registry = SkillRegistry()

@registry.register(name="discover_skills", tags=["system", "meta"])
def discover_skills(query: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Lists all available skills or searches for relevant ones if a query is provided.
    Useful for agents to understand their own capabilities.
    """
    if query:
        skills = registry.find_relevant_skills(query)
    else:
        skills = list(registry.skills.values())
        
    return [
        {
            "name": s.name,
            "description": s.description,
            "tags": s.tags
        }
        for s in skills
    ]

def skill(name: Optional[str] = None, tags: List[str] = None):
    """Convenience decorator for registering skills."""
    return registry.register(name=name, tags=tags)
