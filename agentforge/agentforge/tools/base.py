"""Base tool definitions for AgentForge.

This module provides the abstract base class for tools and the @tool
decorator for easy function-to-tool conversion with automatic Pydantic
schema generation.
"""

import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, get_type_hints

from pydantic import BaseModel, ConfigDict, Field, create_model


class ToolMeta(BaseModel):
    """Metadata for a tool.

    Contains all information needed to describe and execute a tool,
    including its schema for LLM function calling.

    Attributes:
        name: Tool name used in API calls.
        description: Human-readable description of what the tool does.
        parameters_schema: JSON Schema for the tool's parameters.
        callable: The actual function to execute.
    """

    name: str
    description: str
    parameters_schema: dict[str, Any]
    callable: Callable[..., Any]

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ToolConfig(BaseModel):
    """Configuration for a tool instance.

    Attributes:
        name: Tool name (used in API calls).
        description: Human-readable description of what the tool does.
        timeout: Maximum execution time in seconds.
        max_retries: Maximum number of retry attempts on failure.
        requires_auth: Whether the tool requires authentication.
    """

    name: str
    description: str = ""
    timeout: float = 30.0
    max_retries: int = 0
    requires_auth: bool = False


class ToolSchema(BaseModel):
    """JSON Schema for a tool's parameters.

    Attributes:
        type: Always "object" for tool parameters.
        properties: Schema for each parameter.
        required: List of required parameter names.
    """

    type: str = "object"
    properties: dict[str, Any] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)


class BaseTool(ABC):
    """Abstract base class for all tools.

    Tools are functions that agents can call to perform actions.
    Each tool must define its schema and implement the execute method.

    Attributes:
        config: Tool configuration.
        schema: JSON schema for the tool's parameters.

    Example:
        ```python
        class SearchTool(BaseTool):
            def __init__(self):
                super().__init__(
                    ToolConfig(
                        name="search",
                        description="Search for information",
                    )
                )

            async def execute(self, query: str) -> str:
                return f"Results for: {query}"
        ```
    """

    def __init__(self, config: ToolConfig) -> None:
        """Initialize the tool.

        Args:
            config: Tool configuration.
        """
        self.config = config
        self._schema: ToolSchema | None = None

    @property
    def name(self) -> str:
        """Get the tool name."""
        return self.config.name

    @property
    def description(self) -> str:
        """Get the tool description."""
        return self.config.description

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """Execute the tool with the given arguments.

        Args:
            **kwargs: Tool arguments as defined in the schema.

        Returns:
            Tool execution result.

        Raises:
            ToolExecutionError: If execution fails.
        """
        ...

    @abstractmethod
    def get_parameters_schema(self) -> dict[str, Any]:
        """Get the JSON Schema for the tool's parameters.

        Returns:
            JSON Schema dictionary for the parameters.
        """
        ...

    def get_schema(self) -> dict[str, Any]:
        """Get the OpenAI-compatible tool schema.

        Returns:
            Dictionary containing the tool definition.
        """
        if self._schema is None:
            self._schema = self._generate_schema()

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._schema.model_dump(exclude_none=True),
            },
        }

    def to_openai_tool(self) -> dict[str, Any]:
        """Convert to OpenAI tool format.

        Returns:
            OpenAI-compatible tool definition.
        """
        return self.get_schema()

    def to_anthropic_tool(self) -> dict[str, Any]:
        """Convert to Anthropic tool format.

        Returns:
            Anthropic-compatible tool definition.
        """
        if self._schema is None:
            self._schema = self._generate_schema()

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self._schema.model_dump(exclude_none=True),
        }

    def _generate_schema(self) -> ToolSchema:
        """Generate schema from the execute method signature.

        Override this method to provide a custom schema.
        """
        sig = inspect.signature(self.execute)
        hints = get_type_hints(self.execute)

        properties = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            param_type = hints.get(param_name, str)
            prop = self._type_to_schema(param_type)

            # Add description from docstring if available
            if self.execute.__doc__:
                # TODO: Parse docstring for parameter descriptions
                pass

            properties[param_name] = prop

            # Check if parameter is required (no default value)
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        return ToolSchema(properties=properties, required=required)

    @staticmethod
    def _type_to_schema(python_type: type) -> dict[str, Any]:
        """Convert a Python type to JSON Schema.

        Args:
            python_type: The Python type to convert.

        Returns:
            JSON Schema representation.
        """
        origin = getattr(python_type, "__origin__", None)

        if python_type is str:
            return {"type": "string"}
        elif python_type is int:
            return {"type": "integer"}
        elif python_type is float:
            return {"type": "number"}
        elif python_type is bool:
            return {"type": "boolean"}
        elif python_type is list or origin is list:
            return {"type": "array", "items": {}}
        elif python_type is dict or origin is dict:
            return {"type": "object"}
        elif hasattr(python_type, "__bases__") and issubclass(python_type, BaseModel):
            # Pydantic model
            return python_type.model_json_schema()
        else:
            return {"type": "string"}


class ToolExecutionError(Exception):
    """Exception raised when tool execution fails.

    Attributes:
        tool_name: Name of the tool that failed.
        message: Error description.
        cause: Underlying exception.
    """

    def __init__(
        self,
        tool_name: str,
        message: str,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(f"Tool '{tool_name}' failed: {message}")
        self.tool_name = tool_name
        self.cause = cause


class FunctionTool(BaseTool):
    """Tool created from a regular Python function.

    Wraps a function with the BaseTool interface, automatically
    generating schema from type hints using Pydantic.

    Attributes:
        _func: The wrapped function.
        _meta: Tool metadata including schema.
        _input_model: Pydantic model for input validation.
    """

    def __init__(
        self,
        func: Callable,
        name: str | None = None,
        description: str | None = None,
    ) -> None:
        """Initialize the function tool.

        Args:
            func: The function to wrap.
            name: Optional tool name (defaults to function name).
            description: Optional description (defaults to docstring).
        """
        self._func = func
        self._tool_name = name or func.__name__
        self._tool_description = description or self._extract_description()
        self._meta = self._build_meta()
        self._input_model = self._create_input_model()

        # Initialize with config
        config = ToolConfig(
            name=self._tool_name,
            description=self._tool_description,
        )
        super().__init__(config)

    def _extract_description(self) -> str:
        """Extract description from docstring.

        Returns:
            First line of docstring or empty string.
        """
        doc = self._func.__doc__ or ""
        return doc.strip().split("\n")[0]

    def _build_meta(self) -> ToolMeta:
        """Build tool metadata from function signature.

        Uses Pydantic's create_model to generate a schema from
        the function's type hints.

        Returns:
            ToolMeta instance with schema and callable.
        """
        hints = get_type_hints(self._func)
        sig = inspect.signature(self._func)

        fields = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            param_type = hints.get(param_name, Any)
            default = ... if param.default is inspect.Parameter.empty else param.default
            fields[param_name] = (param_type, default)

        # Create a Pydantic model for the input
        input_model = create_model(f"{self._tool_name}_input", **fields)

        return ToolMeta(
            name=self._tool_name,
            description=self._tool_description,
            parameters_schema=input_model.model_json_schema(),
            callable=self._func,
        )

    def _create_input_model(self) -> type[BaseModel]:
        """Create a Pydantic model for input validation.

        Returns:
            Pydantic model class for validating tool inputs.
        """
        hints = get_type_hints(self._func)
        sig = inspect.signature(self._func)

        fields = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            param_type = hints.get(param_name, Any)
            default = ... if param.default is inspect.Parameter.empty else param.default
            fields[param_name] = (param_type, default)

        return create_model(f"{self._tool_name}_validated_input", **fields)

    def get_parameters_schema(self) -> dict[str, Any]:
        """Get the JSON Schema for the tool's parameters.

        Returns:
            JSON Schema dictionary.
        """
        return self._meta.parameters_schema

    async def execute(self, **kwargs: Any) -> Any:
        """Execute the wrapped function with validation.

        Validates input against the Pydantic model before execution.
        Supports both sync and async functions.

        Args:
            **kwargs: Arguments to pass to the function.

        Returns:
            Function return value.

        Raises:
            ToolExecutionError: If execution fails.
        """
        try:
            # Validate input using Pydantic model
            validated = self._input_model(**kwargs)
            validated_kwargs = validated.model_dump()

            # Execute function (sync or async)
            if inspect.iscoroutinefunction(self._func):
                return await self._func(**validated_kwargs)
            else:
                return self._func(**validated_kwargs)

        except Exception as e:
            raise ToolExecutionError(
                tool_name=self.name,
                message=str(e),
                cause=e,
            ) from e

    def to_openai_tool(self) -> dict[str, Any]:
        """Convert to OpenAI tool format.

        Returns:
            OpenAI-compatible tool definition.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema(),
            },
        }

    def to_anthropic_tool(self) -> dict[str, Any]:
        """Convert to Anthropic tool format.

        Returns:
            Anthropic-compatible tool definition.
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.get_parameters_schema(),
        }


def tool(
    name: str | None = None,
    description: str | None = None,
) -> Callable[[Callable], FunctionTool]:
    """Decorator to convert a function into a tool.

    Creates a FunctionTool from a regular Python function,
    automatically generating the schema from type hints.

    Can be used with or without parentheses:
        @tool
        def my_func(): ...

        @tool()
        def my_func(): ...

        @tool(name="custom_name")
        def my_func(): ...

    Args:
        name: Optional tool name (defaults to function name).
        description: Optional description (defaults to docstring).

    Returns:
        Decorator function that returns a FunctionTool.

    Example:
        ```python
        @tool(description="Search for information")
        async def search(query: str, limit: int = 10) -> str:
            '''Search for information on the web.'''
            return f"Results for: {query}"
        ```
    """

    def decorator(func: Callable) -> FunctionTool:
        return FunctionTool(func, name=name, description=description)

    # Handle @tool without parentheses
    # When called as @tool (no parens), the first arg is the function itself
    if callable(name):
        # @tool was used without parentheses
        func = name
        name = None
        return FunctionTool(func, name=None, description=description)

    return decorator


__all__ = [
    "ToolMeta",
    "BaseTool",
    "ToolConfig",
    "ToolSchema",
    "ToolExecutionError",
    "FunctionTool",
    "tool",
]
