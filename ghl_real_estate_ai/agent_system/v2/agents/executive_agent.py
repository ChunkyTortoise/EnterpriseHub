"""
Executive Agent (V2)
Specialized in narrative synthesis, investor presentations, and executive summaries.
Built with PydanticAI and optimized for Gemini 1.5 Pro.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel

from ghl_real_estate_ai.services.report_generator_service import report_generator_service

# 1. Define the Executive Result Schema
class SlideContent(BaseModel):
    title: str
    bullet_points: List[str]
    visual_reference: str # e.g., "DesignAgent.staged_rooms[0]"

class ExecutiveResult(BaseModel):
    executive_summary: str
    investor_narrative: str
    presentation_outline: List[SlideContent]
    investment_verdict: str
    suggested_next_steps: List[str]
    gamma_deck_prompt: str # For Gamma.app or similar presentation AI

# 2. Define Dependencies
class ExecutiveDeps:
    def __init__(self):
        self.reporter = report_generator_service

# 3. Initialize Gemini Model
model = GeminiModel('gemini-2.0-flash')

# 4. Create the Executive Agent
executive_agent = Agent(
    model,
    deps_type=ExecutiveDeps,
    output_type=ExecutiveResult,
    system_prompt=(
        "You are an Elite Real Estate Executive Strategist. "
        "Your goal is to synthesize research, analysis, and design into a powerful investor-ready narrative. "
        "Create compelling presentation outlines and executive summaries that drive decision-making. "
        "Your tone should be professional, authoritative, and persuasive."
    )
)

# 5. Define Tools
@executive_agent.tool
async def generate_investor_report_pdf(ctx: RunContext[ExecutiveDeps], data: Dict[str, Any]) -> str:
    """Trigger the generation of a professional PDF report for this property."""
    # In a real tool, we might return a URL or a confirmation
    await ctx.deps.reporter.generate_v2_investor_report(data)
    return "INVESTOR_REPORT_PDF_GENERATED_SUCCESSFULLY"

@executive_agent.tool
def draft_investor_email(ctx: RunContext[ExecutiveDeps], summary: str, verdict: str) -> str:
    """Draft a professional email to an investor summarizing the opportunity."""
    return f"Subject: Investment Opportunity: {verdict}\n\nDear Investor,\n\n{summary}\n\nBest regards,\nExecutive Agent"

@executive_agent.tool
def generate_summary_pdf_blueprint(ctx: RunContext[ExecutiveDeps], data: Dict[str, Any]) -> str:
    """Prepare a blueprint for the PDF report generator."""
    return "PDF Blueprint ready for ReportGeneratorService."
