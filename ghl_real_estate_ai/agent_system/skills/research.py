"""
Research and Market Intelligence Skills.
Exposes Perplexity and NotebookLM-style capabilities to agents.
"""

from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.services.notebook_researcher import get_notebook_researcher
from ghl_real_estate_ai.services.perplexity_researcher import get_perplexity_researcher

from .base import skill

# Initialize singletons
_perplexity = get_perplexity_researcher()
_notebook = get_notebook_researcher()


@skill(name="web_research", tags=["research", "perplexity", "web"])
async def web_research(query: str, depth: str = "comprehensive") -> str:
    """
    Performs deep real-time web research on any topic using Perplexity AI.
    Use this when you need up-to-date facts, market trends, or specific data not in the training set.

    Args:
        query: The specific research question or topic.
        depth: 'basic' or 'comprehensive' research.
    """
    context = f"Search depth: {depth}. Focus on real estate implications if relevant."
    return await _perplexity.research_topic(query, context)


@skill(name="market_trends_lookup", tags=["research", "market", "real_estate"])
async def market_trends_lookup(location: str) -> str:
    """
    Get real-time real estate market trends for a specific city or neighborhood.

    Args:
        location: The city or neighborhood to research (e.g., 'Rancho Cucamonga, CA').
    """
    return await _perplexity.get_market_trends(location)


@skill(name="create_research_notebook", tags=["research", "notebook", "grounding"])
def create_research_notebook(name: str, description: Optional[str] = None) -> str:
    """
    Creates a new research notebook for grounded document analysis.
    Returns a notebook_id.
    """
    return _notebook.create_notebook(name, description)


@skill(name="add_to_notebook", tags=["research", "notebook", "document"])
def add_to_notebook(notebook_id: str, title: str, content: str) -> str:
    """
    Adds a document or text source to a research notebook.
    """
    try:
        _notebook.add_source(notebook_id, title, content)
        return f"Successfully added '{title}' to notebook."
    except Exception as e:
        return f"Error: {str(e)}"


@skill(name="query_notebook", tags=["research", "notebook", "grounding"])
async def query_notebook(notebook_id: str, query: str) -> str:
    """
    Perform grounded research across all documents in a specific notebook.
    Like NotebookLM, this only uses the provided sources to answer.
    """
    return await _notebook.query_notebook(notebook_id, query)


@skill(name="generate_notebook_summary", tags=["research", "notebook", "synthesis"])
async def generate_notebook_summary(notebook_id: str) -> str:
    """
    Generates a high-level briefing/summary of all materials in the notebook.
    """
    return await _notebook.generate_briefing_doc(notebook_id)
