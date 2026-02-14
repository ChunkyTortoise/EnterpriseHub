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
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
sys.path.append(root_dir)

try:
    from notebooklm import NotebookLMClient
except ImportError:
    NotebookLMClient = None
    print("ERROR: notebooklm-py package not installed. Run: pip install notebooklm-py", file=sys.stderr)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


class NotebookLMMCPServer:
    """MCP Server for NotebookLM integration."""

    def __init__(self):
        self.notebook_lm = None
        self.error_message = None
        # Note: client initialization will be done asynchronously in run or on first tool call

    async def _ensure_initialized(self):
        """Lazy initialization of NotebookLM client."""
        if self.notebook_lm is not None:
            return True

        if NotebookLMClient is None:
            self.error_message = "notebooklm-py package not installed"
            logger.error(self.error_message)
            return False

        try:
            # We use from_storage to avoid complex auth setup in stdio MCP
            self.notebook_lm = await NotebookLMClient.from_storage()
            logger.info("NotebookLM client initialized successfully")
            return True
        except Exception as e:
            self.error_message = f"Failed to initialize NotebookLM client: {str(e)}"
            logger.error(self.error_message)
            return False

    async def list_tools(self) -> List[Dict[str, Any]]:
        """Return list of available MCP tools."""
        if self.error_message:
            # If initialization failed, we still return the tools so Claude knows they exist,
            # but calls to them will fail with the initialization error.
            # Alternatively, we could return an empty list, but that would hide the tool.
            logger.warning(f"Returning tools list despite initialization error: {self.error_message}")

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
        if self.error_message:
            return {"error": f"NotebookLM service not initialized: {self.error_message}"}
        if not self.notebook_lm:
            return {"error": "NotebookLM client not available"}

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
        notebook = await self.notebook_lm.notebooks.create(
            title=args["title"]
        )
        return {
            "success": True,
            "notebook_id": notebook.id,
            "title": notebook.title,
            "message": f"Created notebook: {notebook.title}"
        }

    async def _add_source(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add a source to a notebook."""
        source_type = args["source_type"]
        notebook_id = args["notebook_id"]
        content = args["content"]
        
        if source_type == "url":
            source = await self.notebook_lm.sources.add_url(notebook_id, content)
        elif source_type == "text":
            source = await self.notebook_lm.sources.add_text(
                notebook_id, 
                text=content, 
                title=args.get("title", "Text Source")
            )
        else:
            return {"error": f"Unsupported source type: {source_type}"}
            
        return {
            "success": True,
            "source_id": source.id,
            "message": f"Added {source_type} source to notebook"
        }

    async def _query_notebook(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Query a notebook."""
        result = await self.notebook_lm.chat.ask(
            notebook_id=args["notebook_id"],
            query=args["query"]
        )
        return {
            "success": True,
            "answer": result.answer,
            "citations": [str(c) for c in result.references] if args.get("include_citations", True) else [],
            "query": args["query"]
        }

    async def _list_notebooks(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all notebooks."""
        notebooks = await self.notebook_lm.notebooks.list()
        limit = args.get("limit", 50)
        return {
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
        }

    async def _generate_study_guide(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a study guide."""
        try:
            # Note: artifact API structure might vary, this is based on current source
            guide = await self.notebook_lm.artifacts.get_guide(
                notebook_id=args["notebook_id"]
            )
            return {
                "success": True,
                "content": str(guide),
                "format": args.get("format", "markdown")
            }
        except Exception as e:
            return {"error": f"Failed to generate study guide: {str(e)}"}

    async def _generate_audio_overview(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate an audio overview (podcast)."""
        try:
            # Audio overview is handled in artifacts
            audio = await self.notebook_lm.artifacts.generate_audio_overview(
                notebook_id=args["notebook_id"]
            )
            return {
                "success": True,
                "message": "Audio overview generation started",
                "task_id": getattr(audio, 'task_id', 'unknown')
            }
        except Exception as e:
            return {"error": f"Failed to generate audio overview: {str(e)}"}

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

                # Ensure initialized on first protocol request
                if method in ["tools/list", "tools/call"]:
                    if not await self._ensure_initialized():
                        logger.error(f"Initialization failed: {self.error_message}")

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
