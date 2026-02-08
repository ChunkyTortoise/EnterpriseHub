"""Tool registry for agentic RAG system.

This module provides a registry of tools that can be used by the agentic RAG system,
including vector search, web search, and calculator tools. Each tool follows a
standardized interface for consistent execution and result handling.
"""

from __future__ import annotations

import asyncio
import json
import math
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID, uuid4

import aiohttp
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.exceptions import RAGException


class ToolExecutionError(RAGException):
    """Exception raised when a tool execution fails."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize tool execution error.

        Args:
            message: Error message
            tool_name: Name of the tool that failed
            details: Additional error details
        """
        super().__init__(
            message=message,
            details=details,
            error_code=f"TOOL_ERROR_{tool_name.upper()}",
        )
        self.tool_name = tool_name


class ToolResult(BaseModel):
    """Standardized result from tool execution.

    Attributes:
        tool_name: Name of the executed tool
        success: Whether execution was successful
        data: Result data (type depends on tool)
        error: Error message if failed
        execution_time_ms: Time taken to execute
        metadata: Additional execution metadata
    """

    model_config = ConfigDict(extra="allow")

    tool_name: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time_ms: float = Field(default=0.0, ge=0.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("error")
    @classmethod
    def validate_error(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure error is set if success is False."""
        values = info.data
        if not values.get("success", True) and not v:
            return "Unknown error"
        return v


class ToolMetadata(BaseModel):
    """Metadata describing a tool's capabilities.

    Attributes:
        name: Tool name
        description: Human-readable description
        version: Tool version
        parameters: JSON schema for parameters
        required_credentials: List of required environment variables
        rate_limit_per_minute: Maximum calls per minute
        timeout_seconds: Default timeout
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    version: str = "1.0.0"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    required_credentials: List[str] = Field(default_factory=list)
    rate_limit_per_minute: int = Field(default=60, ge=1)
    timeout_seconds: float = Field(default=30.0, ge=1.0)


class BaseTool(ABC):
    """Abstract base class for all tools.

    All tools must inherit from this class and implement the required
    methods for consistent execution and result handling.

    Example:
        ```python
        class MyTool(BaseTool):
            @property
            def metadata(self) -> ToolMetadata:
                return ToolMetadata(
                    name="my_tool",
                    description="Does something useful"
                )

            async def execute(self, **kwargs) -> ToolResult:
                # Implementation
                return ToolResult(...)
        ```
    """

    def __init__(self) -> None:
        """Initialize the tool."""
        self._call_count = 0
        self._last_call_time: Optional[datetime] = None

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Return tool metadata."""
        pass

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult with execution results
        """
        pass

    def validate_input(self, **kwargs: Any) -> List[str]:
        """Validate input parameters.

        Args:
            **kwargs: Parameters to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required credentials
        for cred in self.metadata.required_credentials:
            if not os.environ.get(cred):
                errors.append(f"Missing required credential: {cred}")

        return errors

    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool parameters.

        Returns:
            JSON schema dictionary
        """
        return {
            "name": self.metadata.name,
            "description": self.metadata.description,
            "parameters": self.metadata.parameters,
        }

    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting.

        Raises:
            ToolExecutionError: If rate limit exceeded
        """
        if self._last_call_time:
            time_since_last = (datetime.now() - self._last_call_time).total_seconds()
            min_interval = 60.0 / self.metadata.rate_limit_per_minute

            if time_since_last < min_interval:
                wait_time = min_interval - time_since_last
                await asyncio.sleep(wait_time)

        self._call_count += 1
        self._last_call_time = datetime.now()


class VectorSearchTool(BaseTool):
    """Tool for searching the vector store.

    This tool integrates with the hybrid searcher to perform
    dense and sparse retrieval from the knowledge base.
    """

    def __init__(self, hybrid_searcher: Optional[Any] = None) -> None:
        """Initialize vector search tool.

        Args:
            hybrid_searcher: Optional hybrid searcher instance
        """
        super().__init__()
        self._hybrid_searcher = hybrid_searcher

    @property
    def metadata(self) -> ToolMetadata:
        """Return tool metadata."""
        return ToolMetadata(
            name="vector_search",
            description="Search the knowledge base using vector similarity",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query text"},
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 100,
                    },
                    "threshold": {
                        "type": "number",
                        "description": "Minimum similarity threshold",
                        "default": 0.0,
                        "minimum": 0.0,
                        "maximum": 1.0,
                    },
                    "filters": {"type": "object", "description": "Metadata filters"},
                    "use_hybrid": {"type": "boolean", "description": "Use hybrid search", "default": True},
                },
                "required": ["query"],
            },
            timeout_seconds=30.0,
        )

    async def execute(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
        use_hybrid: bool = True,
        **kwargs: Any,
    ) -> ToolResult:
        """Execute vector search.

        Args:
            query: Search query text
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            filters: Optional metadata filters
            use_hybrid: Whether to use hybrid search
            **kwargs: Additional parameters

        Returns:
            ToolResult with search results
        """
        import time

        start_time = time.time()

        try:
            await self._check_rate_limit()

            # If no hybrid searcher provided, return mock results
            if self._hybrid_searcher is None:
                # Mock implementation for testing
                results = self._mock_search(query, top_k)
            else:
                # Real implementation would use hybrid searcher
                results = await self._hybrid_searcher.search(
                    query=query,
                    top_k=top_k,
                    threshold=threshold,
                    filters=filters,
                )

            execution_time = (time.time() - start_time) * 1000

            return ToolResult(
                tool_name=self.metadata.name,
                success=True,
                data={
                    "results": results,
                    "total_found": len(results),
                    "query": query,
                },
                execution_time_ms=execution_time,
                metadata={
                    "top_k": top_k,
                    "threshold": threshold,
                    "use_hybrid": use_hybrid,
                },
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResult(
                tool_name=self.metadata.name,
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )

    def _mock_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Generate mock search results for testing.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            List of mock results
        """
        results = []
        for i in range(min(top_k, 5)):
            results.append(
                {
                    "id": str(uuid4()),
                    "content": f"Mock result {i + 1} for query: {query}",
                    "score": 0.9 - (i * 0.1),
                    "metadata": {"source": "mock"},
                }
            )
        return results


class WebSearchTool(BaseTool):
    """Tool for searching the web using Serper or Tavily APIs.

    Supports multiple search providers with automatic fallback.
    """

    SERPER_API_URL = "https://google.serper.dev/search"
    TAVILY_API_URL = "https://api.tavily.com/search"

    def __init__(
        self,
        serper_api_key: Optional[str] = None,
        tavily_api_key: Optional[str] = None,
    ) -> None:
        """Initialize web search tool.

        Args:
            serper_api_key: Serper API key (or from env)
            tavily_api_key: Tavily API key (or from env)
        """
        super().__init__()
        self._serper_key = serper_api_key or os.environ.get("SERPER_API_KEY")
        self._tavily_key = tavily_api_key or os.environ.get("TAVILY_API_KEY")
        self._session: Optional[aiohttp.ClientSession] = None

    @property
    def metadata(self) -> ToolMetadata:
        """Return tool metadata."""
        return ToolMetadata(
            name="web_search",
            description="Search the web for current information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 20,
                    },
                    "search_type": {"type": "string", "enum": ["search", "news"], "default": "search"},
                },
                "required": ["query"],
            },
            required_credentials=["SERPER_API_KEY"],
            rate_limit_per_minute=100,
            timeout_seconds=15.0,
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def execute(self, query: str, num_results: int = 5, search_type: str = "search", **kwargs: Any) -> ToolResult:
        """Execute web search.

        Args:
            query: Search query
            num_results: Number of results to return
            search_type: Type of search (search or news)
            **kwargs: Additional parameters

        Returns:
            ToolResult with search results
        """
        import time

        start_time = time.time()

        try:
            await self._check_rate_limit()

            # Try Serper first
            if self._serper_key:
                results = await self._search_serper(query, num_results, search_type)
            # Fallback to Tavily
            elif self._tavily_key:
                results = await self._search_tavily(query, num_results)
            else:
                # Return mock results if no API keys
                results = self._mock_web_search(query, num_results)

            execution_time = (time.time() - start_time) * 1000

            return ToolResult(
                tool_name=self.metadata.name,
                success=True,
                data={
                    "results": results,
                    "total_found": len(results),
                    "query": query,
                    "provider": "serper" if self._serper_key else "tavily" if self._tavily_key else "mock",
                },
                execution_time_ms=execution_time,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return ToolResult(
                tool_name=self.metadata.name,
                success=False,
                error=str(e),
                execution_time_ms=execution_time,
            )

    async def _search_serper(self, query: str, num_results: int, search_type: str) -> List[Dict[str, Any]]:
        """Search using Serper API.

        Args:
            query: Search query
            num_results: Number of results
            search_type: Type of search

        Returns:
            List of search results
        """
        session = await self._get_session()

        payload = {
            "q": query,
            "num": min(num_results, 20),
        }

        if search_type == "news":
            payload["type"] = "news"

        headers = {"X-API-KEY": self._serper_key, "Content-Type": "application/json"}

        async with session.post(
            self.SERPER_API_URL, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            if response.status != 200:
                raise ToolExecutionError(f"Serper API error: {response.status}", tool_name="web_search")

            data = await response.json()

            # Extract organic results
            results = []
            organic = data.get("organic", [])
            for item in organic[:num_results]:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "position": item.get("position", 0),
                    }
                )

            return results

    async def _search_tavily(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search using Tavily API.

        Args:
            query: Search query
            num_results: Number of results

        Returns:
            List of search results
        """
        session = await self._get_session()

        payload = {
            "api_key": self._tavily_key,
            "query": query,
            "search_depth": "basic",
            "include_answer": False,
            "max_results": min(num_results, 20),
        }

        async with session.post(self.TAVILY_API_URL, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status != 200:
                raise ToolExecutionError(f"Tavily API error: {response.status}", tool_name="web_search")

            data = await response.json()

            results = []
            for item in data.get("results", [])[:num_results]:
                results.append(
                    {
                        "title": item.get("title", ""),
                        "link": item.get("url", ""),
                        "snippet": item.get("content", ""),
                        "score": item.get("score", 0),
                    }
                )

            return results

    def _mock_web_search(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Generate mock web search results.

        Args:
            query: Search query
            num_results: Number of results

        Returns:
            List of mock results
        """
        results = []
        for i in range(min(num_results, 3)):
            results.append(
                {
                    "title": f"Mock Web Result {i + 1} for '{query}'",
                    "link": f"https://example.com/result{i + 1}",
                    "snippet": f"This is a mock search result snippet for the query: {query}",
                    "position": i + 1,
                }
            )
        return results

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()


class CalculatorTool(BaseTool):
    """Tool for safe mathematical calculations.

    Evaluates mathematical expressions in a safe sandbox environment.
    """

    # Allowed operations
    SAFE_FUNCTIONS: Dict[str, Any] = {
        "abs": abs,
        "round": round,
        "max": max,
        "min": min,
        "sum": sum,
        "len": len,
        "pow": pow,
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "exp": math.exp,
        "ceil": math.ceil,
        "floor": math.floor,
        "pi": math.pi,
        "e": math.e,
    }

    # Allowed operators
    SAFE_OPERATORS: Dict[str, Any] = {
        "+": lambda x, y: x + y,
        "-": lambda x, y: x - y,
        "*": lambda x, y: x * y,
        "/": lambda x, y: x / y if y != 0 else float("inf"),
        "//": lambda x, y: x // y if y != 0 else 0,
        "%": lambda x, y: x % y,
        "**": lambda x, y: x**y,
    }

    def __init__(self) -> None:
        """Initialize calculator tool."""
        super().__init__()

    @property
    def metadata(self) -> ToolMetadata:
        """Return tool metadata."""
        return ToolMetadata(
            name="calculator",
            description="Perform mathematical calculations safely",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Mathematical expression to evaluate"},
                    "variables": {"type": "object", "description": "Variables to use in expression", "default": {}},
                },
                "required": ["expression"],
            },
            timeout_seconds=5.0,
        )

    async def execute(self, expression: str, variables: Optional[Dict[str, Any]] = None, **kwargs: Any) -> ToolResult:
        """Execute calculation.

        Args:
            expression: Mathematical expression
            variables: Optional variables for expression
            **kwargs: Additional parameters

        Returns:
            ToolResult with calculation result
        """
        import time

        start_time = time.time()

        try:
            await self._check_rate_limit()

            # Clean and validate expression
            cleaned_expr = self._clean_expression(expression)

            # Validate safety
            validation_errors = self._validate_expression(cleaned_expr)
            if validation_errors:
                return ToolResult(
                    tool_name=self.metadata.name,
                    success=False,
                    error=f"Validation failed: {'; '.join(validation_errors)}",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

            # Prepare evaluation namespace
            namespace = dict(self.SAFE_FUNCTIONS)
            if variables:
                namespace.update(variables)

            # Evaluate expression
            result = eval(cleaned_expr, {"__builtins__": {}}, namespace)

            execution_time = (time.time() - start_time) * 1000

            return ToolResult(
                tool_name=self.metadata.name,
                success=True,
                data={
                    "result": result,
                    "expression": expression,
                    "variables": variables or {},
                },
                execution_time_ms=execution_time,
            )

        except ZeroDivisionError:
            return ToolResult(
                tool_name=self.metadata.name,
                success=False,
                error="Division by zero",
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.metadata.name,
                success=False,
                error=f"Calculation error: {str(e)}",
                execution_time_ms=(time.time() - start_time) * 1000,
            )

    def _clean_expression(self, expression: str) -> str:
        """Clean and normalize expression.

        Args:
            expression: Raw expression

        Returns:
            Cleaned expression
        """
        # Remove whitespace
        cleaned = expression.strip()

        # Replace common math words with operators
        replacements = {
            "plus": "+",
            "minus": "-",
            "times": "*",
            "multiplied by": "*",
            "divided by": "/",
            "over": "/",
            "to the power of": "**",
            "squared": "**2",
            "cubed": "**3",
        }

        for word, symbol in replacements.items():
            cleaned = cleaned.replace(word, symbol)

        return cleaned

    def _validate_expression(self, expression: str) -> List[str]:
        """Validate expression for safety.

        Args:
            expression: Expression to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Check for dangerous patterns
        dangerous_patterns = [
            r"__\w+",  # Dunder methods
            r"import\s+\w+",  # Import statements
            r"from\s+\w+\s+import",  # From imports
            r"exec\s*\(",  # Exec function
            r"eval\s*\(",  # Eval function
            r"compile\s*\(",  # Compile function
            r"open\s*\(",  # File operations
            r"file\s*\(",  # File constructor
            r"os\.",  # OS module
            r"sys\.",  # Sys module
            r"subprocess",  # Subprocess
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                errors.append(f"Forbidden pattern detected: {pattern}")

        return errors


class ToolRegistry:
    """Registry for managing and executing tools.

    Provides centralized tool management with registration,
    discovery, and execution capabilities.

    Example:
        ```python
        registry = ToolRegistry()

        # Register tools
        registry.register(VectorSearchTool())
        registry.register(WebSearchTool())

        # Execute tool
        result = await registry.execute(
            "vector_search",
            query="machine learning"
        )
        ```
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._tools: Dict[str, BaseTool] = {}
        self._execution_history: List[Dict[str, Any]] = []

    def register(self, tool: BaseTool) -> None:
        """Register a tool in the registry.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If tool with same name already registered
        """
        name = tool.metadata.name
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")

        self._tools[name] = tool

    def unregister(self, tool_name: str) -> bool:
        """Unregister a tool.

        Args:
            tool_name: Name of tool to remove

        Returns:
            True if tool was removed, False if not found
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            return True
        return False

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name.

        Args:
            tool_name: Name of tool

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all registered tools.

        Returns:
            List of tool schemas
        """
        return [tool.get_schema() for tool in self._tools.values()]

    async def execute(self, tool_name: str, **kwargs: Any) -> ToolResult:
        """Execute a tool by name.

        Args:
            tool_name: Name of tool to execute
            **kwargs: Parameters for tool execution

        Returns:
            ToolResult from execution

        Raises:
            ValueError: If tool not found
        """
        tool = self._tools.get(tool_name)
        if tool is None:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' not found in registry",
            )

        # Validate credentials
        validation_errors = tool.validate_input(**kwargs)
        if validation_errors:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Validation failed: {'; '.join(validation_errors)}",
            )

        # Execute tool
        result = await tool.execute(**kwargs)

        # Record execution
        self._execution_history.append(
            {
                "tool_name": tool_name,
                "parameters": kwargs,
                "result": result.model_dump(),
                "timestamp": datetime.now().isoformat(),
            }
        )

        return result

    async def execute_multiple(self, executions: List[Tuple[str, Dict[str, Any]]]) -> List[ToolResult]:
        """Execute multiple tools in parallel.

        Args:
            executions: List of (tool_name, parameters) tuples

        Returns:
            List of ToolResults in same order
        """
        tasks = [self.execute(tool_name, **params) for tool_name, params in executions]
        return await asyncio.gather(*tasks)

    def aggregate_results(self, results: List[ToolResult], strategy: str = "concatenate") -> Dict[str, Any]:
        """Aggregate multiple tool results.

        Args:
            results: List of tool results
            strategy: Aggregation strategy (concatenate, merge, rank)

        Returns:
            Aggregated result data
        """
        if strategy == "concatenate":
            return self._concatenate_results(results)
        elif strategy == "merge":
            return self._merge_results(results)
        elif strategy == "rank":
            return self._rank_results(results)
        else:
            raise ValueError(f"Unknown aggregation strategy: {strategy}")

    def _concatenate_results(self, results: List[ToolResult]) -> Dict[str, Any]:
        """Concatenate results from multiple tools.

        Args:
            results: List of results

        Returns:
            Concatenated data
        """
        all_items = []
        sources = []

        for result in results:
            if result.success and result.data:
                if isinstance(result.data, dict) and "results" in result.data:
                    all_items.extend(result.data["results"])
                else:
                    all_items.append(result.data)
                sources.append(result.tool_name)

        return {
            "items": all_items,
            "sources": sources,
            "total_items": len(all_items),
            "successful_tools": sum(1 for r in results if r.success),
        }

    def _merge_results(self, results: List[ToolResult]) -> Dict[str, Any]:
        """Merge results by key.

        Args:
            results: List of results

        Returns:
            Merged data
        """
        merged = {}

        for result in results:
            if result.success and isinstance(result.data, dict):
                for key, value in result.data.items():
                    if key not in merged:
                        merged[key] = []
                    if isinstance(value, list):
                        merged[key].extend(value)
                    else:
                        merged[key].append(value)

        return merged

    def _rank_results(self, results: List[ToolResult]) -> Dict[str, Any]:
        """Rank and deduplicate results.

        Args:
            results: List of results

        Returns:
            Ranked and deduplicated data
        """
        all_items = []

        for result in results:
            if result.success and result.data:
                if isinstance(result.data, dict) and "results" in result.data:
                    items = result.data["results"]
                    for item in items:
                        if isinstance(item, dict):
                            item["_source_tool"] = result.tool_name
                    all_items.extend(items)
                elif isinstance(result.data, dict) and "result" in result.data:
                    all_items.append(
                        {
                            "value": result.data["result"],
                            "_source_tool": result.tool_name,
                        }
                    )

        # Sort by score if available
        all_items.sort(key=lambda x: x.get("score", x.get("position", 0)), reverse=True)

        # Deduplicate by content similarity
        seen = set()
        unique_items = []
        for item in all_items:
            content = str(item.get("content", item.get("snippet", item.get("value", ""))))
            content_hash = hash(content[:100])  # Use first 100 chars
            if content_hash not in seen:
                seen.add(content_hash)
                unique_items.append(item)

        return {
            "items": unique_items,
            "total_before_dedup": len(all_items),
            "total_after_dedup": len(unique_items),
        }

    def get_execution_history(self, tool_name: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get execution history.

        Args:
            tool_name: Filter by tool name
            limit: Maximum number of records

        Returns:
            List of execution records
        """
        history = self._execution_history

        if tool_name:
            history = [h for h in history if h["tool_name"] == tool_name]

        return history[-limit:]

    def clear_history(self) -> None:
        """Clear execution history."""
        self._execution_history.clear()
