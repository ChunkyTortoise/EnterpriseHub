"""
Design Agent (V2)
Specialized in visual staging, UI components, and property presentation aesthetics.
Built with PydanticAI and optimized for Gemini 1.5 Pro.
"""

from typing import Any, Dict, List

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel

from ghl_real_estate_ai.services.property_visualizer import PropertyVisualizer


# 1. Define the Design Result Schema
class StagingConcept(BaseModel):
    room_name: str
    style: str  # e.g., "Modern Minimalist", "Industrial Loft"
    description: str
    image_prompt: str  # For Midjourney/DALL-E
    color_palette: List[str]  # Hex codes


class UIComponentSpec(BaseModel):
    component_name: str
    style_attributes: Dict[str, str]
    interaction_model: str


class DesignResult(BaseModel):
    theme_name: str
    staged_rooms: List[StagingConcept]
    ui_specs: List[UIComponentSpec]
    digital_twin_enabled: bool
    presentation_style: str  # e.g., "Dark Mode Tech", "Clean Luxury"


# 2. Define Dependencies
class DesignDeps:
    def __init__(self):
        self.visualizer = PropertyVisualizer()


# 3. Initialize Gemini Model
model = GeminiModel("gemini-2.0-flash")

# 4. Create the Design Agent
design_agent = Agent(
    model,
    deps_type=DesignDeps,
    output_type=DesignResult,
    system_prompt=(
        "You are an Elite Real Estate Design Architect. "
        "Your goal is to create stunning visual concepts and UI specifications for property listings. "
        "Think about high-end staging, immersive digital twins, and modern presentation aesthetics. "
        "Provide detailed image prompts for AI staging and precise UI component specs."
    ),
)


# 5. Define Tools
@design_agent.tool
def get_visual_assets(ctx: RunContext[DesignDeps], address: str) -> Dict[str, Any]:
    """Check if 3D assets or existing style metadata exists for this property."""
    return ctx.deps.visualizer.get_digital_twin_metadata(address)


@design_agent.tool
def suggest_color_palette(ctx: RunContext[DesignDeps], theme: str) -> List[str]:
    """Suggest a professional color palette based on a theme."""
    if theme.lower() == "luxury":
        return ["#1A1A1A", "#C5A059", "#FFFFFF", "#F5F5F5"]
    elif theme.lower() == "tech":
        return ["#0A0E14", "#00E5FF", "#B0BEC5", "#1C2331"]
    return ["#FFFFFF", "#333333", "#CCCCCC"]
