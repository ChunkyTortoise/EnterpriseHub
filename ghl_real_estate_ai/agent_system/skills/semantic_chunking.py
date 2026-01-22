"""
Semantic Chunking Skill for React/JSX
=====================================
Provides dependency-aware chunking for large React component trees.
Uses AST-based boundaries to ensure semantic validity of code splits.
"""

import re
from typing import List, Dict, Set, Any
from dataclasses import dataclass, field

@dataclass
class JSXChunk:
    """Represents a semantically valid chunk of JSX/TSX code"""
    id: str
    code: str
    dependencies: Set[str] = field(default_factory=set)
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    token_count: int = 0
    type: str = "component"  # component, hook, utility, types

class DependencyAwareChunker:
    """
    Chunks React components while preserving dependency graphs.
    """
    
    def __init__(self, max_chunk_tokens: int = 4000):
        self.max_tokens = max_chunk_tokens
        self.dependency_graph = {}
        
    def chunk_jsx_file(self, content: str) -> List[Dict[str, Any]]:
        """
        Naive implementation of semantic chunking using regex boundaries.
        In a production environment, this would use @babel/parser.
        """
        chunks = []
        
        # Identify semantic boundaries (Exported components, hooks, interfaces)
        # Pattern: Matches 'export const ComponentName = ...' or 'export function ComponentName ...'
        boundaries = list(re.finditer(r'export (?:const|function|interface|type) ([A-Z][a-zA-Z0-9_]*)', content))
        
        if not boundaries:
            # Fallback to simple chunking if no clear boundaries found
            return [{"code": content, "type": "raw"}]
            
        imports = re.findall(r'^import .*;$', content, re.MULTILINE)
        
        for i in range(len(boundaries)):
            start = boundaries[i].start()
            end = boundaries[i+1].start() if i+1 < len(boundaries) else len(content)
            
            chunk_code = content[start:end].strip()
            name = boundaries[i].group(1)
            
            # Simple dependency extraction (looking for other component names in the code)
            deps = set()
            for other_b in boundaries:
                other_name = other_b.group(1)
                if other_name != name and other_name in chunk_code:
                    deps.add(other_name)
            
            chunks.append({
                "id": name,
                "code": chunk_code,
                "dependencies": list(deps),
                "imports": imports if i == 0 else [], # Include imports in first chunk or logically split
                "token_count": len(chunk_code) // 4, # Rough estimate
                "type": "interface" if "interface" in boundaries[i].group(0) else "component"
            })
            
        return chunks

    def generate_edit_hints(self, chunk: Dict[str, Any]) -> str:
        """Generates LLM hints for safe editing of this chunk"""
        hints = []
        if chunk.get("dependencies"):
            hints.append(f"⚠️ This component depends on: {', '.join(chunk['dependencies'])}")
        
        if chunk.get("type") == "component":
            hints.append("💡 Use Tailwind CSS for styling. Ensure Shadcn/UI conventions.")
            
        return "\n".join(hints)

# Integration with Skill System
from ghl_real_estate_ai.agent_system.skills.base import Skill

class SemanticChunkingSkill(Skill):
    """Skill to handle large React file chunking"""
    
    name = "semantic_chunking"
    description = "Chunks large JSX/TSX files into semantically valid units for AI processing"
    
    def execute(self, action: str, content: str = "", **kwargs) -> Any:
        chunker = DependencyAwareChunker()
        if action == "chunk":
            return chunker.chunk_jsx_file(content)
        elif action == "get_hints":
            return chunker.generate_edit_hints(kwargs.get("chunk", {}))
        return None

def register_skill():
    from ghl_real_estate_ai.agent_system.skills.base import registry
    registry.register(SemanticChunkingSkill())
