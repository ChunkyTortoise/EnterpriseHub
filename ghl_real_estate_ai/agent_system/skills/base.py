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
        schema = dynamic_model.model_json_schema()
        return self._clean_schema(schema)

    def _clean_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Cleans JSON schema for Gemini API compatibility."""
        if not isinstance(schema, dict):
            return schema
            
        # Remove unsupported fields
        unsupported = ["anyOf", "allOf", "oneOf", "default", "$defs", "definitions", "title", "examples"]
        
        # Handle anyOf by taking the first non-null type if possible
        if "anyOf" in schema:
            options = schema["anyOf"]
            # Find first option that isn't null type
            best_option = options[0]
            for opt in options:
                if isinstance(opt, dict) and opt.get("type") != "null":
                    best_option = opt
                    break
            schema.update(best_option)
            
        # Convert type to uppercase for Gemini Proto compatibility
        if "type" in schema and isinstance(schema["type"], str):
            schema["type"] = schema["type"].upper()
            
        # Create a list of keys to delete to avoid modification while iterating
        to_delete = [field for field in unsupported if field in schema]
        for field in to_delete:
            del schema[field]
                
        # Recursively clean nested objects
        if "properties" in schema:
            for prop in schema["properties"].values():
                self._clean_schema(prop)
        
        if "items" in schema:
            self._clean_schema(schema["items"])
            
        # Ensure type is present for objects
        if "type" not in schema and "properties" in schema:
            schema["type"] = "OBJECT"
            
        return schema

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
            cls._instance._skill_collections = {} # Map location_id -> collection
            cls._instance._doc_collections = {} # Map location_id -> collection for docs
            cls._instance._doc_cache = {} # In-memory fallback
            cls._instance._init_chroma()
        return cls._instance

    def _init_chroma(self):
        """Initialize ChromaDB client."""
        try:
            import chromadb
            self._chroma_client = chromadb.Client()
        except (ImportError, Exception) as e:
            self._chroma_client = None
            print(f"⚠️ ChromaDB Semantic Search unavailable ({str(e)}). Using keyword fallback.")

    def _get_skill_collection(self, location_id: str = "global"):
        """Gets or creates a skill collection for a specific tenant."""
        if not self._chroma_client:
            return None
        
        if location_id not in self._skill_collections:
            collection_name = f"skills_{location_id}"
            self._skill_collections[location_id] = self._chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine", "location_id": location_id}
            )
        return self._skill_collections[location_id]

    def _get_doc_collection(self, location_id: str = "global"):
        """Gets or creates a documentation collection."""
        if not self._chroma_client:
            return None
        
        if location_id not in self._doc_collections:
            collection_name = f"component_docs_{location_id}"
            self._doc_collections[location_id] = self._chroma_client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine", "location_id": location_id}
            )
        return self._doc_collections[location_id]

    def register(self, name: Optional[str] = None, tags: List[str] = None, location_id: str = "global"):
        """Decorator to register a function as a skill."""
        def decorator(func: Callable):
            skill = Skill(func, name=name, tags=tags)
            self.skills[skill.name] = skill
            
            # Register with FastMCP
            self.mcp.tool()(func)
            
            # Register with Vector DB (Partitioned by location_id)
            collection = self._get_skill_collection(location_id)
            if collection:
                text = f"{skill.name}: {skill.description} {' '.join(skill.tags)}"
                collection.upsert(
                    documents=[text],
                    ids=[skill.name],
                    metadatas=[{"name": skill.name, "tags": ",".join(skill.tags), "location_id": location_id}]
                )
            
            return func
        return decorator

    def register_document(self, name: str, content: str, tags: List[str] = None, location_id: str = "global"):
        """Registers a documentation string with the vector DB."""
        collection = self._get_doc_collection(location_id)
        if collection:
            collection.upsert(
                documents=[content],
                ids=[name],
                metadatas=[{"name": name, "tags": ",".join(tags or []), "location_id": location_id}]
            )

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def find_relevant_skills(self, query: str, limit: int = 5, location_id: str = "global") -> List[Skill]:
        """
        Find relevant skills using Semantic Search (ChromaDB) with keyword fallback.
        Strictly isolated by location_id.
        """
        # 1. Try Semantic Search in the tenant-specific collection
        collection = self._get_skill_collection(location_id)
        if collection:
            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=min(limit, len(self.skills))
                )
                if results['ids'] and results['ids'][0]:
                    found_skills = [self.skills[name] for name in results['ids'][0] if name in self.skills]
                    if found_skills:
                        return found_skills
            except Exception as e:
                # Log error and fall back
                print(f"Vector search failed for location {location_id}: {e}")

        # 2. Fallback to Keyword Search
        relevant = []
        query_words = set(query.lower().split())
        
        for skill in self.skills.values():
            skill_text = (skill.name + " " + skill.description + " " + " ".join(skill.tags)).lower()
            if any(word in skill_text for word in query_words):
                relevant.append(skill)
        
        return relevant[:limit] if relevant else list(self.skills.values())[:limit]

    def find_relevant_docs(self, query: str, limit: int = 3, location_id: str = "global") -> List[Dict[str, Any]]:
        """Finds relevant component documentation using Semantic Search or keyword fallback."""
        collection = self._get_doc_collection(location_id)
        if collection:
            try:
                results = collection.query(query_texts=[query], n_results=limit)
                if results and results['ids'] and results['ids'][0]:
                    docs = []
                    for i, doc_id in enumerate(results['ids'][0]):
                        docs.append({
                            "id": doc_id,
                            "content": results['documents'][0][i],
                            "distance": results['distances'][0][i]
                        })
                    return docs
            except Exception as e:
                print(f"Doc search failed for location {location_id}: {e}")

        # Keyword fallback to in-memory cache
        relevant_docs = []
        query_words = set(query.lower().split())
        
        cache = self._doc_cache.get(location_id, {})
        for name, content in cache.items():
            if any(word in content.lower() for word in query_words):
                relevant_docs.append({
                    "id": name,
                    "content": content,
                    "distance": 1.0 # No real distance
                })
        return relevant_docs[:limit]

    def get_all_gemini_tools(self) -> List[Dict[str, Any]]:
        """Return all registered skills as Gemini tool declarations."""
        return [skill.to_gemini_tool()["function_declarations"][0] for skill in self.skills.values()]

# Global registry instance
registry = SkillRegistry()

@registry.register(name="discover_skills", tags=["system", "meta"])
def discover_skills(query: Optional[str] = None, location_id: str = "global") -> List[Dict[str, Any]]:
    """
    Lists all available skills or searches for relevant ones if a query is provided.
    Useful for agents to understand their own capabilities.
    """
    if query:
        skills = registry.find_relevant_skills(query, location_id=location_id)
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

def skill(name: Optional[str] = None, tags: List[str] = None, location_id: str = "global"):
    """Convenience decorator for registering skills."""
    return registry.register(name=name, tags=tags, location_id=location_id)
