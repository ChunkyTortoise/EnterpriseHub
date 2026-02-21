"""Tests for AgentForge tools module.

This module tests:
- @tool decorator with various function signatures
- Schema generation for basic types
- Schema generation for Optional and List types
- Async and sync function execution
- OpenAI and Anthropic tool format conversion
- ToolRegistry operations
- Input validation
"""

import asyncio
from typing import Any, Literal

import pytest
from pydantic import BaseModel

from agentforge.tools import (
    FunctionTool,
    ToolConfig,
    ToolExecutionError,
    ToolMeta,
    ToolNotFoundError,
    ToolRegistry,
    clear_global_registry,
    create_pydantic_model_from_function,
    generate_tool_schema,
    get_global_registry,
    get_tool,
    merge_schemas,
    python_type_to_json_schema,
    register_tool,
    tool,
    unregister_tool,
    validate_tool_input,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def clean_global_registry():
    """Clear the global registry before and after each test."""
    clear_global_registry()
    yield
    clear_global_registry()


# =============================================================================
# Test @tool Decorator
# =============================================================================


class TestToolDecorator:
    """Tests for the @tool decorator."""

    def test_basic_decorator(self):
        """Test basic @tool decorator usage."""

        @tool
        def greet(name: str) -> str:
            """Greet someone."""
            return f"Hello, {name}!"

        assert isinstance(greet, FunctionTool)
        assert greet.name == "greet"
        assert greet.description == "Greet someone."

    def test_decorator_with_custom_name(self):
        """Test @tool decorator with custom name."""

        @tool(name="custom_name")
        def func() -> str:
            """A function."""
            return "result"

        assert func.name == "custom_name"

    def test_decorator_with_custom_description(self):
        """Test @tool decorator with custom description."""

        @tool(description="Custom description")
        def func() -> str:
            """Original docstring."""
            return "result"

        assert func.description == "Custom description"

    def test_decorator_with_both_custom(self):
        """Test @tool decorator with both custom name and description."""

        @tool(name="my_tool", description="My tool description")
        def func(x: int) -> int:
            """Original."""
            return x * 2

        assert func.name == "my_tool"
        assert func.description == "My tool description"

    def test_decorator_no_docstring(self):
        """Test @tool decorator with function without docstring."""

        @tool
        def no_doc(x: int) -> int:
            return x

        assert no_doc.description == ""

    def test_multiline_docstring(self):
        """Test that only first line of docstring is used."""

        @tool
        def multiline() -> str:
            """First line.

            Second line.
            Third line.
            """
            return "result"

        assert multiline.description == "First line."


# =============================================================================
# Test Schema Generation - Basic Types
# =============================================================================


class TestBasicTypeSchema:
    """Tests for basic type schema generation."""

    def test_string_type(self):
        """Test string type schema."""

        @tool
        def func(text: str) -> str:
            """Function with string."""
            return text

        schema = func.get_parameters_schema()
        assert schema["properties"]["text"]["type"] == "string"
        assert "text" in schema["required"]

    def test_integer_type(self):
        """Test integer type schema."""

        @tool
        def func(count: int) -> int:
            """Function with integer."""
            return count

        schema = func.get_parameters_schema()
        assert schema["properties"]["count"]["type"] == "integer"

    def test_float_type(self):
        """Test float type schema."""

        @tool
        def func(value: float) -> float:
            """Function with float."""
            return value

        schema = func.get_parameters_schema()
        assert schema["properties"]["value"]["type"] == "number"

    def test_boolean_type(self):
        """Test boolean type schema."""

        @tool
        def func(flag: bool) -> bool:
            """Function with boolean."""
            return flag

        schema = func.get_parameters_schema()
        assert schema["properties"]["flag"]["type"] == "boolean"

    def test_list_type(self):
        """Test list type schema."""

        @tool
        def func(items: list) -> list:
            """Function with list."""
            return items

        schema = func.get_parameters_schema()
        assert schema["properties"]["items"]["type"] == "array"

    def test_dict_type(self):
        """Test dict type schema."""

        @tool
        def func(data: dict) -> dict:
            """Function with dict."""
            return data

        schema = func.get_parameters_schema()
        assert schema["properties"]["data"]["type"] == "object"

    def test_default_values(self):
        """Test that default values are in schema."""

        @tool
        def func(name: str, count: int = 10) -> str:
            """Function with defaults."""
            return name * count

        schema = func.get_parameters_schema()
        assert "name" in schema["required"]
        assert "count" not in schema["required"]
        assert schema["properties"]["count"]["default"] == 10


# =============================================================================
# Test Schema Generation - Complex Types
# =============================================================================


class TestComplexTypeSchema:
    """Tests for complex type schema generation."""

    def test_optional_type(self):
        """Test Optional type schema."""

        @tool
        def func(name: str | None = None) -> str:
            """Function with Optional."""
            return name or "default"

        schema = func.get_parameters_schema()
        # Optional[str] should have string type (may be in anyOf for Optional)
        prop = schema["properties"]["name"]
        # Could be direct type or anyOf structure
        assert "type" in prop or "anyOf" in prop
        if "type" in prop:
            assert prop["type"] == "string"

    def test_list_of_int(self):
        """Test List[int] type schema."""

        @tool
        def func(numbers: list[int]) -> int:
            """Sum numbers."""
            return sum(numbers)

        schema = func.get_parameters_schema()
        assert schema["properties"]["numbers"]["type"] == "array"
        assert schema["properties"]["numbers"]["items"]["type"] == "integer"

    def test_dict_with_types(self):
        """Test Dict[str, int] type schema."""

        @tool
        def func(data: dict[str, int]) -> int:
            """Sum dict values."""
            return sum(data.values())

        schema = func.get_parameters_schema()
        assert schema["properties"]["data"]["type"] == "object"

    def test_pydantic_model_param(self):
        """Test Pydantic model as parameter."""

        class UserInput(BaseModel):
            name: str
            age: int

        @tool
        def func(user: UserInput) -> str:
            """Process user."""
            return f"{user.name} is {user.age}"

        schema = func.get_parameters_schema()
        # Pydantic models may use $ref or have direct properties
        user_prop = schema["properties"]["user"]
        # Check if it's a $ref or has properties directly
        assert "$ref" in user_prop or "properties" in user_prop

    def test_literal_type(self):
        """Test Literal type schema."""

        @tool
        def func(color: Literal["red", "green", "blue"]) -> str:
            """Pick a color."""
            return f"You chose {color}"

        schema = func.get_parameters_schema()
        # Literal should create an enum
        assert "enum" in schema["properties"]["color"] or "anyOf" in schema["properties"]["color"]


# =============================================================================
# Test python_type_to_json_schema Function
# =============================================================================


class TestPythonTypeToJsonSchema:
    """Tests for the python_type_to_json_schema utility function."""

    def test_basic_types(self):
        """Test basic type conversion."""
        assert python_type_to_json_schema(str) == {"type": "string"}
        assert python_type_to_json_schema(int) == {"type": "integer"}
        assert python_type_to_json_schema(float) == {"type": "number"}
        assert python_type_to_json_schema(bool) == {"type": "boolean"}
        assert python_type_to_json_schema(list) == {"type": "array", "items": {}}
        assert python_type_to_json_schema(dict) == {"type": "object"}

    def test_optional_str(self):
        """Test Optional[str] conversion."""
        schema = python_type_to_json_schema(str | None)
        assert schema == {"type": "string"}

    def test_optional_int(self):
        """Test Optional[int] conversion."""
        schema = python_type_to_json_schema(int | None)
        assert schema == {"type": "integer"}

    def test_list_of_strings(self):
        """Test List[str] conversion."""
        schema = python_type_to_json_schema(list[str])
        assert schema == {"type": "array", "items": {"type": "string"}}

    def test_list_of_ints(self):
        """Test List[int] conversion."""
        schema = python_type_to_json_schema(list[int])
        assert schema == {"type": "array", "items": {"type": "integer"}}

    def test_nested_list(self):
        """Test nested List conversion."""
        schema = python_type_to_json_schema(list[list[str]])
        assert schema["type"] == "array"
        assert schema["items"]["type"] == "array"
        assert schema["items"]["items"]["type"] == "string"

    def test_dict_with_value_type(self):
        """Test Dict[str, int] conversion."""
        schema = python_type_to_json_schema(dict[str, int])
        assert schema["type"] == "object"
        assert schema["additionalProperties"]["type"] == "integer"

    def test_literal_string(self):
        """Test Literal string conversion."""
        schema = python_type_to_json_schema(Literal["a", "b", "c"])
        assert schema["type"] == "string"
        assert set(schema["enum"]) == {"a", "b", "c"}

    def test_literal_int(self):
        """Test Literal int conversion."""
        schema = python_type_to_json_schema(Literal[1, 2, 3])
        assert schema["type"] == "integer"
        assert set(schema["enum"]) == {1, 2, 3}

    def test_pydantic_model(self):
        """Test Pydantic model conversion."""

        class Model(BaseModel):
            name: str
            count: int

        schema = python_type_to_json_schema(Model)
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert "count" in schema["properties"]


# =============================================================================
# Test Function Execution
# =============================================================================


class TestFunctionExecution:
    """Tests for tool function execution."""

    @pytest.mark.asyncio
    async def test_sync_function_execution(self):
        """Test executing a sync function."""

        @tool
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        result = await add.execute(a=2, b=3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_async_function_execution(self):
        """Test executing an async function."""

        @tool
        async def async_add(a: int, b: int) -> int:
            """Async add two numbers."""
            await asyncio.sleep(0)
            return a + b

        result = await async_add.execute(a=2, b=3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_execution_with_defaults(self):
        """Test execution with default values."""

        @tool
        def greet(name: str, greeting: str = "Hello") -> str:
            """Greet someone."""
            return f"{greeting}, {name}!"

        result = await greet.execute(name="World")
        assert result == "Hello, World!"

        result = await greet.execute(name="World", greeting="Hi")
        assert result == "Hi, World!"

    @pytest.mark.asyncio
    async def test_execution_error_handling(self):
        """Test that execution errors are wrapped."""

        @tool
        def failing_tool(x: int) -> int:
            """A tool that fails."""
            raise ValueError("Intentional error")

        with pytest.raises(ToolExecutionError) as exc_info:
            await failing_tool.execute(x=1)

        assert exc_info.value.tool_name == "failing_tool"
        assert "Intentional error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_input_validation(self):
        """Test that inputs are validated."""

        @tool
        def process(count: int) -> int:
            """Process a count."""
            return count * 2

        # Valid input
        result = await process.execute(count=5)
        assert result == 10

        # String that can be coerced to int
        result = await process.execute(count="5")
        assert result == 10


# =============================================================================
# Test Tool Format Conversion
# =============================================================================


class TestToolFormatConversion:
    """Tests for OpenAI and Anthropic tool format conversion."""

    def test_openai_format(self):
        """Test OpenAI tool format conversion."""

        @tool
        def search(query: str, limit: int = 10) -> str:
            """Search for information."""
            return f"Results for: {query}"

        openai_tool = search.to_openai_tool()

        assert openai_tool["type"] == "function"
        assert openai_tool["function"]["name"] == "search"
        assert openai_tool["function"]["description"] == "Search for information."
        assert "parameters" in openai_tool["function"]
        assert openai_tool["function"]["parameters"]["type"] == "object"

    def test_anthropic_format(self):
        """Test Anthropic tool format conversion."""

        @tool
        def search(query: str, limit: int = 10) -> str:
            """Search for information."""
            return f"Results for: {query}"

        anthropic_tool = search.to_anthropic_tool()

        assert anthropic_tool["name"] == "search"
        assert anthropic_tool["description"] == "Search for information."
        assert "input_schema" in anthropic_tool
        assert anthropic_tool["input_schema"]["type"] == "object"

    def test_format_with_complex_types(self):
        """Test format conversion with complex types."""

        @tool
        def process(
            items: list[str],
            options: dict[str, Any] | None = None,
        ) -> str:
            """Process items with options."""
            return f"Processed {len(items)} items"

        openai_tool = process.to_openai_tool()
        anthropic_tool = process.to_anthropic_tool()

        # Both should have proper schema
        assert "items" in openai_tool["function"]["parameters"]["properties"]
        assert "options" in openai_tool["function"]["parameters"]["properties"]
        assert "items" in anthropic_tool["input_schema"]["properties"]
        assert "options" in anthropic_tool["input_schema"]["properties"]


# =============================================================================
# Test ToolRegistry
# =============================================================================


class TestToolRegistry:
    """Tests for ToolRegistry operations."""

    def test_register_tool(self):
        """Test registering a tool."""

        @tool
        def my_tool(x: int) -> int:
            """My tool."""
            return x

        registry = ToolRegistry()
        registry.register(my_tool)

        assert "my_tool" in registry
        assert registry.get("my_tool") is my_tool

    def test_register_duplicate_raises(self):
        """Test that registering duplicate raises error."""

        @tool
        def my_tool(x: int) -> int:
            """My tool."""
            return x

        registry = ToolRegistry()
        registry.register(my_tool)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(my_tool)

    def test_unregister_tool(self):
        """Test unregistering a tool."""

        @tool
        def my_tool(x: int) -> int:
            """My tool."""
            return x

        registry = ToolRegistry()
        registry.register(my_tool)
        registry.unregister("my_tool")

        assert "my_tool" not in registry

    def test_unregister_nonexistent_raises(self):
        """Test that unregistering nonexistent raises error."""
        registry = ToolRegistry()

        with pytest.raises(ToolNotFoundError):
            registry.unregister("nonexistent")

    def test_get_nonexistent(self):
        """Test getting nonexistent tool returns None."""
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_get_required_nonexistent_raises(self):
        """Test get_required raises for nonexistent tool."""
        registry = ToolRegistry()

        with pytest.raises(ToolNotFoundError):
            registry.get_required("nonexistent")

    def test_list_tools(self):
        """Test listing tools."""

        @tool
        def tool_a() -> str:
            """Tool A."""
            return "a"

        @tool
        def tool_b() -> str:
            """Tool B."""
            return "b"

        registry = ToolRegistry()
        registry.register(tool_a)
        registry.register(tool_b)

        tools = registry.list_tools()
        assert set(tools) == {"tool_a", "tool_b"}

    def test_to_openai_tools(self):
        """Test exporting to OpenAI format."""

        @tool
        def tool_a(x: int) -> int:
            """Tool A."""
            return x

        @tool
        def tool_b(y: str) -> str:
            """Tool B."""
            return y

        registry = ToolRegistry()
        registry.register(tool_a)
        registry.register(tool_b)

        openai_tools = registry.to_openai_tools()

        assert len(openai_tools) == 2
        names = {t["function"]["name"] for t in openai_tools}
        assert names == {"tool_a", "tool_b"}

    def test_to_anthropic_tools(self):
        """Test exporting to Anthropic format."""

        @tool
        def tool_a(x: int) -> int:
            """Tool A."""
            return x

        @tool
        def tool_b(y: str) -> str:
            """Tool B."""
            return y

        registry = ToolRegistry()
        registry.register(tool_a)
        registry.register(tool_b)

        anthropic_tools = registry.to_anthropic_tools()

        assert len(anthropic_tools) == 2
        names = {t["name"] for t in anthropic_tools}
        assert names == {"tool_a", "tool_b"}

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test executing a tool through registry."""

        @tool
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        registry = ToolRegistry()
        registry.register(add)

        result = await registry.execute("add", a=2, b=3)
        assert result == 5

    @pytest.mark.asyncio
    async def test_execute_nonexistent_raises(self):
        """Test executing nonexistent tool raises error."""
        registry = ToolRegistry()

        with pytest.raises(ToolNotFoundError):
            await registry.execute("nonexistent", x=1)

    def test_len_and_iter(self):
        """Test __len__ and __iter__ methods."""

        @tool
        def tool_a() -> str:
            """Tool A."""
            return "a"

        @tool
        def tool_b() -> str:
            """Tool B."""
            return "b"

        registry = ToolRegistry()
        registry.register(tool_a)
        registry.register(tool_b)

        assert len(registry) == 2
        assert set(registry) == {"tool_a", "tool_b"}

    def test_clear(self):
        """Test clearing the registry."""

        @tool
        def my_tool() -> str:
            """My tool."""
            return "result"

        registry = ToolRegistry()
        registry.register(my_tool)
        registry.clear()

        assert len(registry) == 0


# =============================================================================
# Test Global Registry Functions
# =============================================================================


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def test_register_tool_global(self):
        """Test registering tool in global registry."""

        @tool
        def global_tool(x: int) -> int:
            """Global tool."""
            return x

        register_tool(global_tool)

        assert get_tool("global_tool") is global_tool

    def test_unregister_tool_global(self):
        """Test unregistering tool from global registry."""

        @tool
        def temp_tool(x: int) -> int:
            """Temp tool."""
            return x

        register_tool(temp_tool)
        unregister_tool("temp_tool")

        assert get_tool("temp_tool") is None

    def test_get_global_registry(self):
        """Test getting global registry."""
        registry = get_global_registry()
        assert isinstance(registry, ToolRegistry)

        # Should return same instance
        registry2 = get_global_registry()
        assert registry is registry2


# =============================================================================
# Test Utility Functions
# =============================================================================


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_generate_tool_schema(self):
        """Test generate_tool_schema function."""

        def my_func(name: str, count: int = 5) -> str:
            """My function."""
            return name * count

        schema = generate_tool_schema(my_func)

        assert schema["type"] == "function"
        assert schema["function"]["name"] == "my_func"
        assert schema["function"]["description"] == "My function."
        assert "name" in schema["function"]["parameters"]["required"]
        assert "count" not in schema["function"]["parameters"]["required"]

    def test_generate_tool_schema_custom(self):
        """Test generate_tool_schema with custom name/description."""

        def my_func(x: int) -> int:
            """Original."""
            return x

        schema = generate_tool_schema(
            my_func,
            name="custom_name",
            description="Custom description",
        )

        assert schema["function"]["name"] == "custom_name"
        assert schema["function"]["description"] == "Custom description"

    def test_create_pydantic_model_from_function(self):
        """Test creating Pydantic model from function."""

        def my_func(name: str, count: int = 5) -> str:
            """My function."""
            return name * count

        model_class = create_pydantic_model_from_function(my_func)

        # Valid input
        instance = model_class(name="test")
        assert instance.name == "test"
        assert instance.count == 5

        # With count override
        instance = model_class(name="test", count=10)
        assert instance.count == 10

    def test_merge_schemas(self):
        """Test merging schemas."""
        base = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "count": {"type": "integer"},
            },
        }
        override = {
            "properties": {
                "count": {"minimum": 0},
            },
        }

        merged = merge_schemas(base, override)

        assert merged["properties"]["name"]["type"] == "string"
        assert merged["properties"]["count"]["minimum"] == 0
        assert merged["properties"]["count"]["type"] == "integer"

    def test_validate_tool_input(self):
        """Test validate_tool_input function."""

        @tool
        def process(name: str, count: int = 10) -> str:
            """Process something."""
            return name * count

        # Valid input
        validated = validate_tool_input(process, {"name": "test"})
        assert validated["name"] == "test"
        assert validated["count"] == 10

        # With override
        validated = validate_tool_input(process, {"name": "test", "count": 5})
        assert validated["count"] == 5


# =============================================================================
# Test ToolMeta
# =============================================================================


class TestToolMeta:
    """Tests for ToolMeta model."""

    def test_tool_meta_creation(self):
        """Test creating ToolMeta."""

        def my_func(x: int) -> int:
            """My function."""
            return x * 2

        @tool
        def my_tool(x: int) -> int:
            """My tool."""
            return x * 2

        meta = ToolMeta(
            name="test",
            description="Test tool",
            parameters_schema={"type": "object", "properties": {}},
            callable=my_func,
        )

        assert meta.name == "test"
        assert meta.description == "Test tool"
        assert meta.callable is my_func


# =============================================================================
# Test ToolConfig
# =============================================================================


class TestToolConfig:
    """Tests for ToolConfig model."""

    def test_tool_config_defaults(self):
        """Test ToolConfig default values."""
        config = ToolConfig(name="test")

        assert config.name == "test"
        assert config.description == ""
        assert config.timeout == 30.0
        assert config.max_retries == 0
        assert config.requires_auth is False

    def test_tool_config_custom(self):
        """Test ToolConfig with custom values."""
        config = ToolConfig(
            name="test",
            description="Test tool",
            timeout=60.0,
            max_retries=3,
            requires_auth=True,
        )

        assert config.description == "Test tool"
        assert config.timeout == 60.0
        assert config.max_retries == 3
        assert config.requires_auth is True


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for the tools module."""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow from decorator to execution."""

        # Create tools
        @tool(description="Add two numbers")
        def add(a: int, b: int) -> int:
            """Add two numbers together."""
            return a + b

        @tool(description="Multiply two numbers")
        async def multiply(a: int, b: int) -> int:
            """Multiply two numbers together."""
            return a * b

        # Register in registry
        registry = ToolRegistry()
        registry.register(add)
        registry.register(multiply)

        # Export for LLM
        openai_tools = registry.to_openai_tools()
        assert len(openai_tools) == 2

        # Execute tools
        add_result = await registry.execute("add", a=5, b=3)
        assert add_result == 8

        multiply_result = await registry.execute("multiply", a=5, b=3)
        assert multiply_result == 15

    @pytest.mark.asyncio
    async def test_complex_tool_workflow(self):
        """Test workflow with complex types."""

        class SearchParams(BaseModel):
            query: str
            limit: int = 10
            filters: dict[str, Any] | None = None

        @tool
        async def search(query: str, limit: int = 10) -> list[str]:
            """Search for items."""
            return [f"Result {i} for {query}" for i in range(limit)]

        # Check schema
        schema = search.get_parameters_schema()
        assert "query" in schema["properties"]
        assert "limit" in schema["properties"]

        # Execute - pass as dict since that's what LLMs will provide
        result = await search.execute(query="test", limit=3)
        assert len(result) == 3
        assert "test" in result[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
