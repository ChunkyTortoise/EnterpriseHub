"""Function-to-tool schema generation for AgentForge.

This module provides utilities for converting Python functions to
OpenAI-compatible tool schemas using Pydantic for validation.

Features:
- Automatic schema generation from type hints
- Support for Optional, List, Dict, Union, and Literal types
- Nested Pydantic model support
- Input validation against schemas
"""

import inspect
from collections.abc import Callable
from typing import (
    Any,
    Literal,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from pydantic import BaseModel, ValidationError, create_model

from agentforge.tools.base import BaseTool


def python_type_to_json_schema(python_type: type) -> dict[str, Any]:
    """Convert a Python type annotation to JSON Schema.

    Handles basic types, Optional, List, Dict, Union, Literal, and Pydantic models.

    Args:
        python_type: The Python type to convert.

    Returns:
        JSON Schema dictionary.

    Example:
        ```python
        schema = python_type_to_json_schema(Optional[str])
        # Returns: {"type": "string"}

        schema = python_type_to_json_schema(List[int])
        # Returns: {"type": "array", "items": {"type": "integer"}}
        ```
    """
    # Handle basic types
    if python_type is str:
        return {"type": "string"}
    elif python_type is int:
        return {"type": "integer"}
    elif python_type is float:
        return {"type": "number"}
    elif python_type is bool:
        return {"type": "boolean"}
    elif python_type is list:
        return {"type": "array", "items": {}}
    elif python_type is dict:
        return {"type": "object"}

    # Get origin and args for generic types
    origin = get_origin(python_type)
    args = get_args(python_type)

    # Handle Optional[T] (which is Union[T, None])
    if origin is Union:
        # Check if it's Optional (Union with None)
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1 and type(None) in args:
            # It's Optional[T]
            return python_type_to_json_schema(non_none_args[0])
        else:
            # It's a true Union - use anyOf
            return {"anyOf": [python_type_to_json_schema(arg) for arg in non_none_args]}

    # Handle list[T]
    if origin is list:
        if args:
            return {
                "type": "array",
                "items": python_type_to_json_schema(args[0]),
            }
        return {"type": "array", "items": {}}

    # Handle dict[K, V]
    if origin is dict:
        if args and len(args) >= 2:
            return {
                "type": "object",
                "additionalProperties": python_type_to_json_schema(args[1]),
            }
        return {"type": "object"}

    # Handle Literal types
    if origin is Literal:
        # Infer type from the literal values
        if args:
            first_arg = args[0]
            if isinstance(first_arg, str):
                return {"type": "string", "enum": list(args)}
            elif isinstance(first_arg, int):
                return {"type": "integer", "enum": list(args)}
            elif isinstance(first_arg, float):
                return {"type": "number", "enum": list(args)}
            elif isinstance(first_arg, bool):
                return {"type": "boolean", "enum": list(args)}
        return {"type": "string", "enum": list(args) if args else []}

    # Handle Pydantic models
    if isinstance(python_type, type) and issubclass(python_type, BaseModel):
        return python_type.model_json_schema()

    # Default to string for unknown types
    return {"type": "string"}


def generate_tool_schema(
    func: Callable,
    name: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Generate an OpenAI-compatible tool schema from a function.

    Analyzes the function signature and type hints to create a
    JSON Schema that can be used with LLM tool calling.

    Args:
        func: The function to generate a schema for.
        name: Optional tool name (defaults to function name).
        description: Optional description (defaults to docstring).

    Returns:
        OpenAI-compatible tool schema dictionary.

    Example:
        ```python
        def search(query: str, limit: int = 10) -> str:
            '''Search for information.'''
            pass

        schema = generate_tool_schema(search)
        # Returns:
        # {
        #     "type": "function",
        #     "function": {
        #         "name": "search",
        #         "description": "Search for information.",
        #         "parameters": {
        #             "type": "object",
        #             "properties": {
        #                 "query": {"type": "string"},
        #                 "limit": {"type": "integer", "default": 10}
        #             },
        #             "required": ["query"]
        #         }
        #     }
        # }
        ```
    """
    tool_name = name or func.__name__
    tool_description = description or func.__doc__ or ""

    sig = inspect.signature(func)
    hints = get_type_hints(func)

    # Build parameter schema
    properties = {}
    required = []

    for param_name, param in sig.parameters.items():
        param_type = hints.get(param_name, str)
        has_default = param.default is not inspect.Parameter.empty

        prop = python_type_to_json_schema(param_type)

        if has_default:
            prop["default"] = param.default
        else:
            required.append(param_name)

        properties[param_name] = prop

    return {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": tool_description.strip(),
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def create_pydantic_model_from_function(
    func: Callable,
    model_name: str | None = None,
) -> type[BaseModel]:
    """Create a Pydantic model from a function's parameters.

    Useful for validating tool call arguments before invoking
    the actual function.

    Args:
        func: The function to create a model from.
        model_name: Optional name for the model.

    Returns:
        A Pydantic model class.

    Example:
        ```python
        def greet(name: str, count: int = 1) -> str:
            return f"Hello {name}!"

        Model = create_pydantic_model_from_function(greet)
        validated = Model(name="World")  # count defaults to 1
        ```
    """
    sig = inspect.signature(func)
    hints = get_type_hints(func)

    model_name = model_name or f"{func.__name__}_args"

    fields = {}
    for param_name, param in sig.parameters.items():
        param_type = hints.get(param_name, str)

        if param.default is inspect.Parameter.empty:
            fields[param_name] = (param_type, ...)
        else:
            fields[param_name] = (param_type, param.default)

    return create_model(model_name, **fields)


def validate_tool_input(tool: BaseTool, input_data: dict[str, Any]) -> dict[str, Any]:
    """Validate input data against a tool's schema.

    Uses the tool's parameter schema to validate the input data,
    applying defaults and type coercion where appropriate.

    Args:
        tool: The tool to validate against.
        input_data: The input data to validate.

    Returns:
        Validated and coerced input data.

    Raises:
        ValidationError: If the input data doesn't match the schema.

    Example:
        ```python
        @tool
        def calculate(a: int, b: int = 10) -> int:
            '''Calculate sum.'''
            return a + b

        validated = validate_tool_input(calculate, {"a": "5"})
        # Returns: {"a": 5, "b": 10}  # coerced and defaults applied
        ```
    """
    schema = tool.get_parameters_schema()

    # Create a Pydantic model from the schema
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    fields = {}
    for prop_name, prop_schema in properties.items():
        # Convert JSON Schema back to Python type
        prop_type = _json_schema_to_python_type(prop_schema)

        if prop_name in required:
            fields[prop_name] = (prop_type, ...)
        elif "default" in prop_schema:
            fields[prop_name] = (prop_type, prop_schema["default"])
        else:
            fields[prop_name] = (prop_type | None, None)

    # Create and use the validation model
    model_name = f"{tool.name}_validation_model"
    validation_model = create_model(model_name, **fields)

    try:
        validated = validation_model(**input_data)
        return validated.model_dump(exclude_none=True)
    except ValidationError as e:
        raise ValueError(f"Invalid input for tool '{tool.name}': {e}") from e


def _json_schema_to_python_type(schema: dict[str, Any]) -> type:
    """Convert a JSON Schema to a Python type.

    Args:
        schema: JSON Schema dictionary.

    Returns:
        Corresponding Python type.
    """
    schema_type = schema.get("type", "string")

    if schema_type == "string":
        if "enum" in schema:
            # Return Literal type for enums
            return Literal[tuple(schema["enum"])]
        return str
    elif schema_type == "integer":
        if "enum" in schema:
            return Literal[tuple(schema["enum"])]
        return int
    elif schema_type == "number":
        if "enum" in schema:
            return Literal[tuple(schema["enum"])]
        return float
    elif schema_type == "boolean":
        return bool
    elif schema_type == "array":
        items_schema = schema.get("items", {})
        item_type = _json_schema_to_python_type(items_schema)
        return list[item_type]
    elif schema_type == "object":
        return dict[str, Any]
    elif "anyOf" in schema:
        # Handle union types
        types = [_json_schema_to_python_type(s) for s in schema["anyOf"]]
        union_type = types[0]
        for type_option in types[1:]:
            union_type = union_type | type_option
        return union_type
    else:
        return Any


def merge_schemas(
    base_schema: dict[str, Any],
    override_schema: dict[str, Any],
) -> dict[str, Any]:
    """Merge two JSON schemas with override taking precedence.

    Useful for customizing generated schemas with additional
    constraints or descriptions.

    Args:
        base_schema: The base schema to merge into.
        override_schema: Schema with override values.

    Returns:
        Merged schema dictionary.
    """
    result = base_schema.copy()

    for key, value in override_schema.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_schemas(result[key], value)
        else:
            result[key] = value

    return result


__all__ = [
    "python_type_to_json_schema",
    "generate_tool_schema",
    "create_pydantic_model_from_function",
    "validate_tool_input",
    "merge_schemas",
]
