"""
Research Intelligence MCP Server
Exposes specialized research tools using Perplexity and NotebookLM-style capabilities.
"""

import json
from typing import List, Optional

from fastmcp import FastMCP

from ghl_real_estate_ai.services.notebook_researcher import get_notebook_researcher
from ghl_real_estate_ai.services.perplexity_researcher import get_perplexity_researcher

# Create the MCP server
mcp = FastMCP("ResearchIntelligence")

# Initialize the services
perplexity = get_perplexity_researcher()
notebook = get_notebook_researcher()


@mcp.tool()
async def web_research(query: str, depth: str = "comprehensive") -> str:
    """
    Performs deep real-time web research on any topic using Perplexity AI.
    """
    try:
        context = f"Search depth: {depth}."
        result = await perplexity.research_topic(query, context)
        return result
    except Exception as e:
        return f"Error during web research: {str(e)}"


@mcp.tool()
async def market_trends_lookup(location: str) -> str:
    """
    Get real-time real estate market trends for a specific city or neighborhood.
    """
    try:
        result = await perplexity.get_market_trends(location)
        return result
    except Exception as e:
        return f"Error looking up market trends for {location}: {str(e)}"


@mcp.tool()
async def create_research_notebook(name: str, description: Optional[str] = None) -> str:
    """
    Creates a new research notebook for grounded document analysis.
    Returns a notebook_id.
    """
    try:
        notebook_id = notebook.create_notebook(name, description)
        return notebook_id
    except Exception as e:
        return f"Error creating notebook: {str(e)}"


@mcp.tool()
async def add_to_notebook(notebook_id: str, title: str, content: str) -> str:
    """
    Adds a document or text source to a research notebook.
    """
    try:
        notebook.add_source(notebook_id, title, content)
        return f"Successfully added '{title}' to notebook {notebook_id}."
    except Exception as e:
        return f"Error adding source: {str(e)}"


@mcp.tool()
async def query_notebook(notebook_id: str, query: str) -> str:
    """
    Perform grounded research across all documents in a specific notebook.
    """
    try:
        result = await notebook.query_notebook(notebook_id, query)
        return result
    except Exception as e:
        return f"Error querying notebook {notebook_id}: {str(e)}"


@mcp.tool()
async def generate_notebook_summary(notebook_id: str) -> str:
    """
    Generates a high-level briefing/summary of all materials in the notebook.
    """
    try:
        result = await notebook.generate_briefing_doc(notebook_id)
        return result
    except Exception as e:
        return f"Error generating summary for notebook {notebook_id}: {str(e)}"


if __name__ == "__main__":
    mcp.run()
