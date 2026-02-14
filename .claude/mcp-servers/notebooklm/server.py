#!/usr/bin/env python3
"""
NotebookLM MCP Server
Provides Claude Code integration with Google NotebookLM for research and knowledge base management.

Based on notebooklm-py unofficial API.
"""
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

try:
    from notebooklm import NotebookLM
except ImportError:
    print("ERROR: notebooklm-py package not installed. Run: pip install notebooklm-py", file=sys.stderr)
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotebookLMMCPServer:
    """MCP Server for NotebookLM integration."""

    def __init__(self):
        self.notebook_lm = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize NotebookLM client with credentials."""
        # NotebookLM uses Google OAuth - credentials should be set up via gcloud or service account
        try:
            self.notebook_lm = NotebookLM()
            logger.info("NotebookLM client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize NotebookLM client: {e}")
            raise

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Return list of available MCP tools."""
        return [
            {
                "name": "notebooklm_create_notebook",
                "description": "Create a new NotebookLM notebook for organizing research",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the notebook"
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional description"
                        }
                    },
                    "required": ["title"]
                }
            },
            {
                "name": "notebooklm_add_source",
                "description": "Add a source (URL, document, or text) to a notebook",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "notebook_id": {
                            "type": "string",
                            "description": "Notebook ID"
                        },
                        "source_type": {
                            "type": "string",
                            "enum": ["url", "text", "document"],
                            "description": "Type of source to add"
                        },
                        "content": {
                            "type": "string",
                            "description": "URL, text content, or document path"
                        },
                        "title": {
                            "type": "string",
                            "description": "Optional title for the source"
                        }
                    },
                    "required": ["notebook_id", "source_type", "content"]
                }
            },
            {
                "name": "notebooklm_query",
                "description": "Query a notebook to find information and insights",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "notebook_id": {
                            "type": "string",
                            "description": "Notebook ID to query"
                        },
                        "query": {
                            "type": "string",
                            "description": "Question or search query"
                        },
                        "include_citations": {
                            "type": "boolean",
                            "description": "Include source citations in response",
                            "default": True
                        }
                    },
                    "required": ["notebook_id", "query"]
                }
            },
            {
                "name": "notebooklm_list_notebooks",
                "description": "List all available notebooks",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of notebooks to return",
                            "default": 50
                        }
                    }
                }
            },
            {
                "name": "notebooklm_generate_study_guide",
                "description": "Generate a study guide from notebook sources",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "notebook_id": {
                            "type": "string",
                            "description": "Notebook ID"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["markdown", "quiz", "flashcards", "outline"],
                            "description": "Study guide format",
                            "default": "markdown"
                        }
                    },
                    "required": ["notebook_id"]
                }
            },
            {
                "name": "notebooklm_generate_audio_overview",
                "description": "Generate an AI podcast/audio overview of notebook content",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "notebook_id": {
                            "type": "string",
                            "description": "Notebook ID"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Approximate duration in minutes",
                            "default": 10
                        }
                    },
                    "required": ["notebook_id"]
                }
            }
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call and return the result."""
        try:
            if name == "notebooklm_create_notebook":
                return await self._create_notebook(arguments)
            elif name == "notebooklm_add_source":
                return await self._add_source(arguments)
            elif name == "notebooklm_query":
                return await self._query_notebook(arguments)
            elif name == "notebooklm_list_notebooks":
                return await self._list_notebooks(arguments)
            elif name == "notebooklm_generate_study_guide":
                return await self._generate_study_guide(arguments)
            elif name == "notebooklm_generate_audio_overview":
                return await self._generate_audio_overview(arguments)
            else:
                return {"error": f"Unknown tool: {name}"}
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return {"error": str(e)}

    async def _create_notebook(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new notebook."""
        notebook = await asyncio.to_thread(
            self.notebook_lm.create_notebook,
            title=args["title"],
            description=args.get("description")
        )
        return {
            "success": True,
            "notebook_id": notebook.id,
            "title": notebook.title,
            "message": f"Created notebook: {notebook.title}"
        }

    async def _add_source(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add a source to a notebook."""
        source = await asyncio.to_thread(
            self.notebook_lm.add_source,
            notebook_id=args["notebook_id"],
            source_type=args["source_type"],
            content=args["content"],
            title=args.get("title")
        )
        return {
            "success": True,
            "source_id": source.id,
            "message": f"Added {args['source_type']} source to notebook"
        }

    async def _query_notebook(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Query a notebook."""
        result = await asyncio.to_thread(
            self.notebook_lm.query,
            notebook_id=args["notebook_id"],
            query=args["query"],
            include_citations=args.get("include_citations", True)
        )
        return {
            "success": True,
            "answer": result.answer,
            "citations": result.citations if args.get("include_citations") else [],
            "query": args["query"]
        }

    async def _list_notebooks(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all notebooks."""
        notebooks = await asyncio.to_thread(
            self.notebook_lm.list_notebooks,
            limit=args.get("limit", 50)
        )
        return {
            "success": True,
            "notebooks": [
                {
                    "id": nb.id,
                    "title": nb.title,
                    "description": nb.description,
                    "source_count": nb.source_count,
                    "created_at": str(nb.created_at)
                }
                for nb in notebooks
            ]
        }

    async def _generate_study_guide(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a study guide."""
        guide = await asyncio.to_thread(
            self.notebook_lm.generate_study_guide,
            notebook_id=args["notebook_id"],
            format=args.get("format", "markdown")
        )
        return {
            "success": True,
            "content": guide.content,
            "format": args.get("format", "markdown")
        }

    async def _generate_audio_overview(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an audio overview (podcast)."""
        audio = await asyncio.to_thread(
            self.notebook_lm.generate_audio_overview,
            notebook_id=args["notebook_id"],
            duration_minutes=args.get("duration_minutes", 10)
        )
        return {
            "success": True,
            "audio_url": audio.url,
            "duration_minutes": audio.duration,
            "message": "Audio overview generated successfully"
        }

    async def run(self):
        """Run the MCP server using stdio transport."""
        logger.info("Starting NotebookLM MCP Server...")

        while True:
            try:
                # Read JSON-RPC request from stdin
                line = await asyncio.to_thread(sys.stdin.readline)
                if not line:
                    break

                request = json.loads(line)
                method = request.get("method")
                params = request.get("params", {})
                request_id = request.get("id")

                # Handle MCP protocol methods
                if method == "tools/list":
                    tools = await self.list_tools()
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"tools": tools}
                    }
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = await self.call_tool(tool_name, arguments)
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {"code": -32601, "message": f"Method not found: {method}"}
                    }

                # Write response to stdout
                print(json.dumps(response), flush=True)

            except Exception as e:
                logger.error(f"Error processing request: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id if 'request_id' in locals() else None,
                    "error": {"code": -32603, "message": str(e)}
                }
                print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    server = NotebookLMMCPServer()
    asyncio.run(server.run())
