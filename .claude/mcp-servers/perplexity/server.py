#!/usr/bin/env python3
"""
Perplexity MCP Server
Model Context Protocol server for Perplexity AI search and research.

Provides tools for:
- Real-time web search with citations
- Academic research queries
- Technical documentation lookup
- Current events and news research

Uses Perplexity Pro API for enhanced results.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    # Find .env file in project root
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not available, rely on environment

# Environment variable for API key
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

if not PERPLEXITY_API_KEY:
    print("WARNING: PERPLEXITY_API_KEY not found in environment", file=sys.stderr)


class PerplexityMCPServer:
    """MCP Server for Perplexity AI operations"""

    def __init__(self):
        self.api_key = PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def search(
        self,
        query: str,
        model: str = "sonar-pro",
        max_tokens: int = 4000,
        temperature: float = 0.2,
        return_citations: bool = True,
        return_images: bool = False,
        search_recency_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search using Perplexity AI with real-time web access.

        Args:
            query: Search query or question
            model: Perplexity model to use (default: sonar-pro for best results)
            max_tokens: Maximum response tokens
            temperature: Response creativity (0.0-1.0, lower = more factual)
            return_citations: Include source citations
            return_images: Include relevant images
            search_recency_filter: Filter by time ('day', 'week', 'month', 'year')

        Returns:
            Search results with answer and citations

        Example:
            search(
                query="What are the latest features in Python 3.13?",
                search_recency_filter="month"
            )
        """
        if not self.api_key:
            return {
                "error": "PERPLEXITY_API_KEY not configured",
                "status": "configuration_error"
            }

        endpoint = f"{self.base_url}/chat/completions"

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful research assistant. Provide accurate, well-cited information."
                },
                {
                    "role": "user",
                    "content": query
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "return_citations": return_citations,
            "return_images": return_images,
        }

        if search_recency_filter:
            payload["search_recency_filter"] = search_recency_filter

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()

                # Extract relevant information
                choice = result.get("choices", [{}])[0]
                message = choice.get("message", {})

                return {
                    "answer": message.get("content", ""),
                    "citations": result.get("citations", []),
                    "images": result.get("images", []),
                    "model": result.get("model"),
                    "usage": result.get("usage", {}),
                    "status": "success"
                }

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.json()
            except:
                error_detail = e.response.text
            error_msg = f"Perplexity API error: {str(e)}\nDetails: {error_detail}"
            return {"error": error_msg, "status": "failed"}
        except httpx.HTTPError as e:
            error_msg = f"Perplexity API error: {str(e)}"
            return {"error": error_msg, "status": "failed"}

    async def research_topic(
        self,
        topic: str,
        focus: Optional[str] = None,
        depth: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Conduct deep research on a topic with structured output.

        Args:
            topic: Main research topic
            focus: Specific aspect to focus on (optional)
            depth: Research depth ('quick', 'balanced', 'comprehensive')

        Returns:
            Structured research with key findings, citations, and summary

        Example:
            research_topic(
                topic="Real estate AI automation",
                focus="lead scoring and qualification",
                depth="comprehensive"
            )
        """
        # Adjust parameters based on depth
        depth_config = {
            "quick": {"max_tokens": 2000, "temperature": 0.1},
            "balanced": {"max_tokens": 3000, "temperature": 0.2},
            "comprehensive": {"max_tokens": 4000, "temperature": 0.2}
        }

        config = depth_config.get(depth, depth_config["balanced"])

        # Construct research query
        query = f"Provide a {depth} research overview of: {topic}"
        if focus:
            query += f"\n\nSpecifically focus on: {focus}"

        query += "\n\nInclude: key concepts, current trends, best practices, and relevant examples."

        result = await self.search(
            query=query,
            max_tokens=config["max_tokens"],
            temperature=config["temperature"],
            return_citations=True
        )

        return result

    async def get_latest_news(
        self,
        topic: str,
        timeframe: str = "day",
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Get latest news and updates on a topic.

        Args:
            topic: News topic
            timeframe: Time filter ('day', 'week', 'month')
            max_results: Number of news items to include

        Returns:
            Latest news with citations

        Example:
            get_latest_news(
                topic="Claude AI announcements",
                timeframe="week"
            )
        """
        query = f"What are the latest news and updates about {topic}? Provide {max_results} most recent and relevant items."

        return await self.search(
            query=query,
            search_recency_filter=timeframe,
            return_citations=True,
            max_tokens=2000
        )

    async def compare_approaches(
        self,
        topic: str,
        approaches: List[str]
    ) -> Dict[str, Any]:
        """
        Compare different approaches or technologies.

        Args:
            topic: Main topic or problem domain
            approaches: List of approaches/technologies to compare

        Returns:
            Comparative analysis with pros/cons and citations

        Example:
            compare_approaches(
                topic="Real-time caching strategies",
                approaches=["Redis", "Memcached", "In-memory caching"]
            )
        """
        approaches_str = ", ".join(approaches)
        query = f"""
        Compare and contrast these approaches for {topic}: {approaches_str}

        For each approach, provide:
        1. Key strengths and weaknesses
        2. Best use cases
        3. Performance characteristics
        4. Integration complexity

        Include practical examples and current industry usage.
        """

        return await self.search(
            query=query,
            max_tokens=4000,
            temperature=0.2,
            return_citations=True
        )


async def run_server():
    """Run the Perplexity MCP server"""
    server = Server("perplexity-search")
    perplexity = PerplexityMCPServer()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available Perplexity search tools"""
        return [
            Tool(
                name="perplexity_search",
                description="Search the web using Perplexity AI with real-time access and citations. Great for current information, technical docs, and research.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query or question"
                        },
                        "search_recency_filter": {
                            "type": "string",
                            "enum": ["day", "week", "month", "year"],
                            "description": "Filter results by time (optional)"
                        },
                        "model": {
                            "type": "string",
                            "description": "Perplexity model (default: sonar-pro)",
                            "default": "sonar-pro",
                            "enum": ["sonar-pro", "sonar", "sonar-reasoning"]
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="perplexity_research",
                description="Conduct deep research on a topic with structured output. Best for comprehensive analysis and understanding.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Main research topic"
                        },
                        "focus": {
                            "type": "string",
                            "description": "Specific aspect to focus on (optional)"
                        },
                        "depth": {
                            "type": "string",
                            "enum": ["quick", "balanced", "comprehensive"],
                            "description": "Research depth",
                            "default": "balanced"
                        }
                    },
                    "required": ["topic"]
                }
            ),
            Tool(
                name="perplexity_news",
                description="Get latest news and updates on a topic with time filtering. Best for current events and recent developments.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "News topic"
                        },
                        "timeframe": {
                            "type": "string",
                            "enum": ["day", "week", "month"],
                            "description": "Time filter",
                            "default": "week"
                        }
                    },
                    "required": ["topic"]
                }
            ),
            Tool(
                name="perplexity_compare",
                description="Compare different approaches, technologies, or solutions with pros/cons analysis.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Main topic or problem domain"
                        },
                        "approaches": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of approaches to compare"
                        }
                    },
                    "required": ["topic", "approaches"]
                }
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        """Handle tool calls"""

        if name == "perplexity_search":
            result = await perplexity.search(**arguments)
        elif name == "perplexity_research":
            result = await perplexity.research_topic(**arguments)
        elif name == "perplexity_news":
            result = await perplexity.get_latest_news(**arguments)
        elif name == "perplexity_compare":
            result = await perplexity.compare_approaches(**arguments)
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]

        # Format response
        if result.get("status") == "success":
            response_text = f"{result.get('answer', '')}\n\n"

            if result.get("citations"):
                response_text += "**Citations:**\n"
                for i, citation in enumerate(result["citations"], 1):
                    response_text += f"{i}. {citation}\n"

            return [TextContent(type="text", text=response_text)]
        else:
            return [TextContent(
                type="text",
                text=f"Error: {result.get('error', 'Unknown error')}"
            )]

    # Run the server
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(run_server())
