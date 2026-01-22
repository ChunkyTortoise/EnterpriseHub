"""
Component Registry Skill for AI UI Generation
==============================================
Uses RAG (Retrieval-Augmented Generation) to provide specific Shadcn/UI and 
Tremor component documentation to agents, reducing system prompt bloat.
"""

from typing import List, Dict, Any, Optional
import os

class ComponentRegistry:
    """
    Manages a local registry of UI components and their documentation.
    In a full implementation, this would use ChromaDB/FAISS.
    """
    
    def __init__(self):
        # Mock registry of components commonly used in the project
        self.registry = {
            "Button": {
                "library": "shadcn/ui",
                "doc": "Props: variant (default, destructive, outline, secondary, ghost, link), size (default, sm, lg, icon), asChild",
                "usage": "<Button variant='outline'>Click Me</Button>"
            },
            "Card": {
                "library": "shadcn/ui",
                "doc": "Components: Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter",
                "usage": "<Card><CardHeader><CardTitle>Total Revenue</CardTitle></CardHeader><CardContent>$45,231</CardContent></Card>"
            },
            "LineChart": {
                "library": "tremor",
                "doc": "Props: data, index, categories, colors, valueFormatter, yAxisWidth",
                "usage": "<LineChart data={chartdata} index='date' categories={['Revenue']} colors={['blue']} />"
            },
            "Metric": {
                "library": "tremor",
                "doc": "Simple KPI display component",
                "usage": "<Metric>$ 34,743</Metric>"
            }
        }

    def retrieve_relevant_components(self, task_description: str) -> List[Dict[str, Any]]:
        """
        Simple keyword-based retrieval for the prototype.
        """
        relevant = []
        task_lower = task_description.lower()
        
        for name, info in self.registry.items():
            if name.lower() in task_lower or info["library"] in task_lower:
                relevant.append({"name": name, **info})
        
        # Fallback: if no specific component mentioned, return common ones
        if not relevant:
            relevant = [
                {"name": "Card", **self.registry["Card"]},
                {"name": "Button", **self.registry["Button"]}
            ]
            
        return relevant

    def build_system_context(self, components: List[Dict[str, Any]]) -> str:
        """Constructs a focused documentation snippet for the LLM prompt"""
        context = "### Available UI Components (Reference Documentation):\n\n"
        for comp in components:
            context += f"Component: {comp['name']} ({comp['library']})\n"
            context += f"Docs: {comp['doc']}\n"
            context += f"Usage Example: {comp['usage']}\n\n"
        return context

# Integration with Skill System
from ghl_real_estate_ai.agent_system.skills.base import Skill

class ComponentRegistrySkill(Skill):
    """Skill to provide focused UI component documentation"""
    
    name = "component_registry"
    description = "Retrieves relevant Shadcn/UI and Tremor documentation for the current task"
    
    def execute(self, action: str, task: str = "", **kwargs) -> Any:
        registry = ComponentRegistry()
        if action == "retrieve":
            relevant = registry.retrieve_relevant_components(task)
            return {
                "components": relevant,
                "prompt_snippet": registry.build_system_context(relevant)
            }
        return None

def register_skill():
    from ghl_real_estate_ai.agent_system.skills.base import registry
    registry.register(ComponentRegistrySkill())
