#!/usr/bin/env python3
"""
NotebookLM MCP Server
Provides Claude Code integration with Google NotebookLM for research and knowledge base management.

Based on notebooklm-py unofficial API, using official MCP SDK for protocol handling.
"""
import asyncio
import json
import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

# Add parent directory to path for imports
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if root_dir not in sys.path:
    sys.path.append(root_dir)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

mcp = FastMCP("notebooklm")


@asynccontextmanager
async def _get_client():
    """Context manager for NotebookLM client with deferred import."""
    try:
        from notebooklm import NotebookLMClient
    except ImportError as e:
        raise RuntimeError(f"notebooklm-py package not installed. Run: pip install notebooklm-py ({e})")

    try:
        client = await NotebookLMClient.from_storage()
        async with client as ctx_client:
            yield ctx_client
    except Exception as e:
        msg = f"Failed to initialize NotebookLM client: {e}"
        logger.error(msg)
        raise RuntimeError(msg)


@mcp.tool()
async def notebooklm_create_notebook(title: str, description: str = "") -> str:
    """Create a new NotebookLM notebook for organizing research."""
    async with _get_client() as client:
        notebook = await client.notebooks.create(title=title)
        return json.dumps({
            "success": True,
            "notebook_id": notebook.id,
            "title": notebook.title,
            "message": f"Created notebook: {notebook.title}"
        }, indent=2)


@mcp.tool()
async def notebooklm_add_source(notebook_id: str, source_type: str, content: str, title: str = "Source") -> str:
    """Add a source (url or text) to a notebook. source_type must be 'url' or 'text'."""
    async with _get_client() as client:
        if source_type == "url":
            source = await client.sources.add_url(notebook_id, content)
        elif source_type == "text":
            source = await client.sources.add_text(notebook_id, text=content, title=title)
        else:
            return json.dumps({"error": f"Unsupported source type: {source_type}. Use 'url' or 'text'."})

        return json.dumps({
            "success": True,
            "source_id": source.id,
            "message": f"Added {source_type} source to notebook"
        }, indent=2)


@mcp.tool()
async def notebooklm_query(notebook_id: str, query: str, include_citations: bool = True) -> str:
    """Query a notebook to find information and insights."""
    async with _get_client() as client:
        result = await client.chat.ask(notebook_id=notebook_id, query=query)
        return json.dumps({
            "success": True,
            "answer": result.answer,
            "citations": [str(c) for c in result.references] if include_citations else [],
            "query": query
        }, indent=2)


@mcp.tool()
async def notebooklm_list_notebooks(limit: int = 50) -> str:
    """List all available notebooks."""
    async with _get_client() as client:
        notebooks = await client.notebooks.list()
        return json.dumps({
            "success": True,
            "notebooks": [
                {
                    "id": nb.id,
                    "title": nb.title,
                    "description": getattr(nb, 'description', ''),
                    "source_count": getattr(nb, 'source_count', 0),
                    "created_at": str(getattr(nb, 'created_at', ''))
                }
                for nb in notebooks[:limit]
            ]
        }, indent=2)


@mcp.tool()
async def notebooklm_generate_study_guide(notebook_id: str, format: str = "markdown") -> str:
    """Generate a study guide from notebook sources. Format: markdown, quiz, flashcards, outline."""
    async with _get_client() as client:
        guide = await client.artifacts.get_guide(notebook_id=notebook_id)
        return json.dumps({
            "success": True,
            "content": str(guide),
            "format": format
        }, indent=2)


@mcp.tool()
async def notebooklm_generate_audio_overview(notebook_id: str, duration_minutes: int = 10) -> str:
    """Generate an AI podcast/audio overview of notebook content."""
    async with _get_client() as client:
        audio = await client.artifacts.generate_audio_overview(notebook_id=notebook_id)
        return json.dumps({
            "success": True,
            "message": "Audio overview generation started",
            "task_id": getattr(audio, 'task_id', 'unknown')
        }, indent=2)



if __name__ == "__main__":
    mcp.run(transport="stdio")
