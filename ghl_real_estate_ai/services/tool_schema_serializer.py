"""
Tool Schema Serializer - Robust schema extraction with progressive fallbacks

Addresses Priority 4 issue: Tool schema serialization edge cases
- Multi-strategy serialization (Pydantic V2 → Introspection → Minimal fallback)
- Comprehensive logging for debugging
- Metrics tracking for monitoring
- Preserves maximum schema information at each fallback level
"""

import asyncio
import inspect
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, get_type_hints, Union, get_origin, get_args

try:
    from ghl_real_estate_ai.ghl_utils.logger import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

logger = get_logger(__name__)


class SerializationMethod(Enum):
    """Serialization strategies in order of preference"""
    PYDANTIC_V2 = "pydantic_v2"
    FUNCTION_INTROSPECTION = "function_introspection"
    TYPE_HINT_ANALYSIS = "type_hint_analysis"
    MINIMAL_FALLBACK = "minimal_fallback"
    FAILED = "failed"


@dataclass
class SchemaSerializationResult:
    """Result of schema serialization attempt with diagnostic information"""
    success: bool
    method_used: SerializationMethod
    schema: Dict[str, Any]
    warnings: List[str] = field(default_factory=list)
    error: Optional[str] = None
    tool_name: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging and metrics"""
        return {
            "success": self.success,
            "method": self.method_used.value,
            "warnings": self.warnings,
            "error": self.error,
            "tool_name": self.tool_name,
            "timestamp": self.timestamp.isoformat(),
            "schema_keys": list(self.schema.keys()) if self.schema else []
        }


class ToolSchemaSerializer:
    """
    Multi-strategy tool schema serializer with progressive fallbacks.

    Serialization Strategies (in order):
    1. Pydantic V2 model_json_schema() - Standard approach
    2. Function Signature Introspection - Fallback for complex types
    3. Type Hint Analysis - Deep introspection of type hints
    4. Minimal Fallback - Preserve name/description only

    All strategies log results and track metrics for monitoring.
    """

    def __init__(self, analytics_service=None):
        """
        Initialize serializer with optional analytics tracking.

        Args:
            analytics_service: Optional AnalyticsService for metrics tracking
        """
        self.analytics = analytics_service
        self._serialization_stats = {
            "total_attempts": 0,
            "successes": 0,
            "failures": 0,
            "methods_used": {method.value: 0 for method in SerializationMethod}
        }

    async def serialize_tool_schema(
        self,
        mcp_tool: Any,
        tool_name: str,
        tenant_id: Optional[str] = None
    ) -> Tuple[Dict[str, Any], SchemaSerializationResult]:
        """
        Serialize MCP tool schema with progressive fallback strategies.

        Args:
            mcp_tool: FastMCP tool object
            tool_name: Name of the tool
            tenant_id: Optional tenant ID for analytics

        Returns:
            Tuple of (schema_dict, serialization_result)
        """
        self._serialization_stats["total_attempts"] += 1

        # Strategy 1: Pydantic V2 (preferred)
        result = await self._try_pydantic_v2(mcp_tool, tool_name)
        if result.success:
            await self._track_success(result, tenant_id)
            return result.schema, result

        # Strategy 2: Function Introspection
        result = await self._try_function_introspection(mcp_tool, tool_name)
        if result.success:
            await self._track_success(result, tenant_id)
            return result.schema, result

        # Strategy 3: Type Hint Analysis
        result = await self._try_type_hint_analysis(mcp_tool, tool_name)
        if result.success:
            await self._track_success(result, tenant_id)
            return result.schema, result

        # Strategy 4: Minimal Fallback (always succeeds)
        result = await self._minimal_fallback(mcp_tool, tool_name)
        await self._track_failure(result, tenant_id)
        return result.schema, result

    async def _try_pydantic_v2(self, mcp_tool: Any, tool_name: str) -> SchemaSerializationResult:
        """
        Strategy 1: Use Pydantic V2 model_json_schema() method.

        This is the standard approach and works for most tools.
        """
        try:
            schema = mcp_tool.model_json_schema()

            logger.info(
                f"Tool schema serialization successful (Pydantic V2): {tool_name}",
                extra={"tool": tool_name, "method": "pydantic_v2", "schema_keys": list(schema.keys())}
            )

            return SchemaSerializationResult(
                success=True,
                method_used=SerializationMethod.PYDANTIC_V2,
                schema=schema,
                tool_name=tool_name
            )

        except AttributeError as e:
            logger.debug(
                f"Pydantic V2 serialization failed (no model_json_schema method): {tool_name}",
                extra={"tool": tool_name, "error": str(e)}
            )
            return SchemaSerializationResult(
                success=False,
                method_used=SerializationMethod.PYDANTIC_V2,
                schema={},
                error=f"AttributeError: {str(e)}",
                tool_name=tool_name
            )

        except Exception as e:
            logger.warning(
                f"Pydantic V2 serialization failed (unexpected error): {tool_name}",
                extra={"tool": tool_name, "error": str(e), "error_type": type(e).__name__}
            )
            return SchemaSerializationResult(
                success=False,
                method_used=SerializationMethod.PYDANTIC_V2,
                schema={},
                error=f"{type(e).__name__}: {str(e)}",
                tool_name=tool_name
            )

    async def _try_function_introspection(self, mcp_tool: Any, tool_name: str) -> SchemaSerializationResult:
        """
        Strategy 2: Use function signature introspection to build schema.

        This works for tools defined as functions with standard Python types.
        """
        try:
            # Get the underlying function
            func = None
            if hasattr(mcp_tool, 'fn'):
                func = mcp_tool.fn
            elif hasattr(mcp_tool, '__call__'):
                func = mcp_tool.__call__
            elif callable(mcp_tool):
                func = mcp_tool

            if not func:
                return SchemaSerializationResult(
                    success=False,
                    method_used=SerializationMethod.FUNCTION_INTROSPECTION,
                    schema={},
                    error="No callable found on tool object",
                    tool_name=tool_name
                )

            # Introspect signature
            sig = inspect.signature(func)
            properties = {}
            required = []

            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'cls'):
                    continue

                # Build parameter schema
                param_schema = self._parameter_to_schema(param)
                properties[param_name] = param_schema

                # Track required parameters
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)

            schema = {
                "type": "object",
                "properties": properties,
                "required": required
            }

            logger.info(
                f"Tool schema serialization successful (Introspection): {tool_name}",
                extra={
                    "tool": tool_name,
                    "method": "function_introspection",
                    "param_count": len(properties)
                }
            )

            return SchemaSerializationResult(
                success=True,
                method_used=SerializationMethod.FUNCTION_INTROSPECTION,
                schema=schema,
                tool_name=tool_name,
                warnings=["Schema built via introspection, may lack detailed type information"]
            )

        except Exception as e:
            logger.warning(
                f"Function introspection serialization failed: {tool_name}",
                extra={"tool": tool_name, "error": str(e), "error_type": type(e).__name__}
            )
            return SchemaSerializationResult(
                success=False,
                method_used=SerializationMethod.FUNCTION_INTROSPECTION,
                schema={},
                error=f"{type(e).__name__}: {str(e)}",
                tool_name=tool_name
            )

    async def _try_type_hint_analysis(self, mcp_tool: Any, tool_name: str) -> SchemaSerializationResult:
        """
        Strategy 3: Deep analysis of type hints to build schema.

        This handles complex types like Union, Optional, List, Dict.
        """
        try:
            # Get the underlying function
            func = None
            if hasattr(mcp_tool, 'fn'):
                func = mcp_tool.fn
            elif hasattr(mcp_tool, '__call__'):
                func = mcp_tool.__call__
            elif callable(mcp_tool):
                func = mcp_tool

            if not func:
                return SchemaSerializationResult(
                    success=False,
                    method_used=SerializationMethod.TYPE_HINT_ANALYSIS,
                    schema={},
                    error="No callable found on tool object",
                    tool_name=tool_name
                )

            # Get type hints
            try:
                type_hints = get_type_hints(func)
            except Exception:
                type_hints = {}

            # Build schema from type hints
            sig = inspect.signature(func)
            properties = {}
            required = []

            for param_name, param in sig.parameters.items():
                if param_name in ('self', 'cls', 'return'):
                    continue

                # Get type hint
                param_type = type_hints.get(param_name)
                param_schema = self._type_to_schema(param_type, param)
                properties[param_name] = param_schema

                # Track required parameters
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)

            schema = {
                "type": "object",
                "properties": properties,
                "required": required
            }

            logger.info(
                f"Tool schema serialization successful (Type Hint Analysis): {tool_name}",
                extra={
                    "tool": tool_name,
                    "method": "type_hint_analysis",
                    "param_count": len(properties)
                }
            )

            return SchemaSerializationResult(
                success=True,
                method_used=SerializationMethod.TYPE_HINT_ANALYSIS,
                schema=schema,
                tool_name=tool_name,
                warnings=["Schema built via type hint analysis, complex types may be simplified"]
            )

        except Exception as e:
            logger.warning(
                f"Type hint analysis serialization failed: {tool_name}",
                extra={"tool": tool_name, "error": str(e), "error_type": type(e).__name__}
            )
            return SchemaSerializationResult(
                success=False,
                method_used=SerializationMethod.TYPE_HINT_ANALYSIS,
                schema={},
                error=f"{type(e).__name__}: {str(e)}",
                tool_name=tool_name
            )

    async def _minimal_fallback(self, mcp_tool: Any, tool_name: str) -> SchemaSerializationResult:
        """
        Strategy 4: Minimal fallback that preserves tool metadata.

        This always succeeds and provides at least the tool name/description.
        Better than empty schema as it preserves basic information.
        """
        try:
            # Try to extract description
            description = None
            if hasattr(mcp_tool, 'description'):
                description = mcp_tool.description
            elif hasattr(mcp_tool, '__doc__'):
                description = mcp_tool.__doc__

            # Build minimal schema with metadata
            schema = {
                "type": "object",
                "properties": {},
                "description": description or f"Tool: {tool_name} (schema unavailable)",
                "x-serialization-fallback": True,
                "x-tool-name": tool_name
            }

            logger.warning(
                f"Tool schema using minimal fallback: {tool_name} - Tool may not work correctly",
                extra={
                    "tool": tool_name,
                    "method": "minimal_fallback",
                    "warning": "All serialization strategies failed, using minimal schema"
                }
            )

            return SchemaSerializationResult(
                success=False,  # Mark as failure even though we return a schema
                method_used=SerializationMethod.MINIMAL_FALLBACK,
                schema=schema,
                tool_name=tool_name,
                warnings=[
                    "All serialization strategies failed",
                    "Using minimal fallback schema",
                    "Tool may not function correctly"
                ]
            )

        except Exception as e:
            # This should never happen, but handle it anyway
            logger.error(
                f"Minimal fallback failed (critical): {tool_name}",
                extra={"tool": tool_name, "error": str(e)}
            )
            return SchemaSerializationResult(
                success=False,
                method_used=SerializationMethod.FAILED,
                schema={"type": "object", "properties": {}},
                error=f"Critical failure: {str(e)}",
                tool_name=tool_name,
                warnings=["Critical: Even minimal fallback failed"]
            )

    def _parameter_to_schema(self, param: inspect.Parameter) -> Dict[str, Any]:
        """Convert function parameter to JSON schema property"""
        schema = {}

        # Try to infer type from annotation
        if param.annotation != inspect.Parameter.empty:
            schema = self._type_to_schema(param.annotation, param)
        else:
            schema = {"type": "string", "description": f"Parameter: {param.name}"}

        # Add default value if present
        if param.default != inspect.Parameter.empty:
            schema["default"] = param.default

        return schema

    def _type_to_schema(self, param_type: Any, param: Optional[inspect.Parameter] = None) -> Dict[str, Any]:
        """Convert Python type to JSON schema"""
        if param_type is None or param_type == inspect.Parameter.empty:
            return {"type": "string"}

        # Handle string type
        if param_type == str or param_type is str:
            return {"type": "string"}

        # Handle numeric types
        if param_type == int or param_type is int:
            return {"type": "integer"}

        if param_type == float or param_type is float:
            return {"type": "number"}

        # Handle boolean
        if param_type == bool or param_type is bool:
            return {"type": "boolean"}

        # Handle Dict
        origin = get_origin(param_type)
        if origin is dict or param_type is dict:
            return {"type": "object"}

        # Handle List
        if origin is list or param_type is list:
            args = get_args(param_type)
            if args:
                return {"type": "array", "items": self._type_to_schema(args[0], None)}
            return {"type": "array"}

        # Handle Optional/Union
        if origin is Union:
            args = get_args(param_type)
            # Filter out NoneType
            non_none_args = [arg for arg in args if arg is not type(None)]
            if len(non_none_args) == 1:
                return self._type_to_schema(non_none_args[0], None)
            # Multiple types - use anyOf
            return {"anyOf": [self._type_to_schema(arg, None) for arg in non_none_args]}

        # Fallback to string for unknown types
        return {"type": "string", "description": f"Type: {param_type}"}

    async def _track_success(self, result: SchemaSerializationResult, tenant_id: Optional[str]):
        """Track successful serialization in metrics"""
        self._serialization_stats["successes"] += 1
        self._serialization_stats["methods_used"][result.method_used.value] += 1

        if self.analytics and tenant_id:
            try:
                await self.analytics.track_event(
                    event_type="tool_schema_serialization_success",
                    location_id=tenant_id,
                    data={
                        "tool_name": result.tool_name,
                        "method": result.method_used.value,
                        "warnings": result.warnings
                    }
                )
            except Exception as e:
                logger.debug(f"Failed to track serialization success: {e}")

    async def _track_failure(self, result: SchemaSerializationResult, tenant_id: Optional[str]):
        """Track failed serialization in metrics"""
        self._serialization_stats["failures"] += 1
        self._serialization_stats["methods_used"][result.method_used.value] += 1

        if self.analytics and tenant_id:
            try:
                await self.analytics.track_event(
                    event_type="tool_schema_serialization_failure",
                    location_id=tenant_id,
                    data={
                        "tool_name": result.tool_name,
                        "method": result.method_used.value,
                        "error": result.error,
                        "warnings": result.warnings
                    }
                )
            except Exception as e:
                logger.debug(f"Failed to track serialization failure: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get serialization statistics for monitoring"""
        stats = self._serialization_stats.copy()
        if stats["total_attempts"] > 0:
            stats["success_rate"] = stats["successes"] / stats["total_attempts"]
        else:
            stats["success_rate"] = 0.0
        return stats