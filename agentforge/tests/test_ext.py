"""Tests for the AgentForge plugin system.

This module tests:
- PluginMetadata validation
- AgentForgeContext registration
- PluginManager discovery, load, and unload
- Built-in plugins (LoggingPlugin, MetricsPlugin, TimingPlugin)
"""

import pytest

from agentforge.ext import (
    AgentForgeContext,
    AgentForgePlugin,
    LoggingPlugin,
    MetricsPlugin,
    PluginLoadError,
    PluginManager,
    PluginMetadata,
    TimingPlugin,
)


class TestPluginMetadata:
    """Tests for PluginMetadata model."""

    def test_metadata_creation_minimal(self) -> None:
        """Test creating metadata with minimal fields."""
        metadata = PluginMetadata(name="test_plugin")
        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == ""
        assert metadata.author == ""
        assert metadata.license == "MIT"
        assert metadata.dependencies == []
        assert metadata.provides == []

    def test_metadata_creation_full(self) -> None:
        """Test creating metadata with all fields."""
        metadata = PluginMetadata(
            name="my_plugin",
            version="2.0.0",
            description="A test plugin",
            author="Test Author",
            license="Apache-2.0",
            dependencies=["pydantic", "httpx"],
            provides=["tools:search", "agents:researcher"],
        )
        assert metadata.name == "my_plugin"
        assert metadata.version == "2.0.0"
        assert metadata.description == "A test plugin"
        assert metadata.author == "Test Author"
        assert metadata.license == "Apache-2.0"
        assert metadata.dependencies == ["pydantic", "httpx"]
        assert metadata.provides == ["tools:search", "agents:researcher"]

    def test_metadata_model_dump(self) -> None:
        """Test serializing metadata to dict."""
        metadata = PluginMetadata(
            name="test",
            version="1.5.0",
            description="Test",
        )
        data = metadata.model_dump()
        assert data["name"] == "test"
        assert data["version"] == "1.5.0"
        assert data["description"] == "Test"


class TestAgentForgeContext:
    """Tests for AgentForgeContext."""

    def test_context_initialization(self) -> None:
        """Test context initializes with empty registries."""
        context = AgentForgeContext()
        assert context.list_tools() == []
        assert context.list_agents() == []
        assert context.list_providers() == []
        assert context.list_hooks() == []

    def test_register_tool(self) -> None:
        """Test registering a tool."""
        context = AgentForgeContext()

        def tool(x):
            return x * 2

        context.register_tool("double", tool)
        assert context.get_tool("double") == tool
        assert "double" in context.list_tools()

    def test_register_agent(self) -> None:
        """Test registering an agent."""
        context = AgentForgeContext()
        agent = {"name": "test_agent"}
        context.register_agent("test", agent)
        assert context.get_agent("test") == agent
        assert "test" in context.list_agents()

    def test_register_provider(self) -> None:
        """Test registering a provider."""
        context = AgentForgeContext()
        provider = {"type": "llm", "model": "gpt-4"}
        context.register_provider("openai", provider)
        assert context.get_provider("openai") == provider
        assert "openai" in context.list_providers()

    def test_register_hook(self) -> None:
        """Test registering hooks."""
        context = AgentForgeContext()

        def handler1(e):
            return None

        def handler2(e):
            return None

        context.register_hook("agent.execute", handler1)
        context.register_hook("agent.execute", handler2)
        context.register_hook("tool.execute", handler1)

        hooks = context.get_hooks("agent.execute")
        assert len(hooks) == 2
        assert handler1 in hooks
        assert handler2 in hooks
        assert len(context.get_hooks("tool.execute")) == 1
        assert context.get_hooks("nonexistent") == []

    def test_get_nonexistent(self) -> None:
        """Test getting nonexistent items returns None."""
        context = AgentForgeContext()
        assert context.get_tool("nonexistent") is None
        assert context.get_agent("nonexistent") is None
        assert context.get_provider("nonexistent") is None

    def test_clear(self) -> None:
        """Test clearing all registrations."""
        context = AgentForgeContext()
        context.register_tool("tool1", lambda: None)
        context.register_agent("agent1", {})
        context.register_provider("provider1", {})
        context.register_hook("event", lambda: None)

        context.clear()

        assert context.list_tools() == []
        assert context.list_agents() == []
        assert context.list_providers() == []
        assert context.list_hooks() == []


class MockPlugin(AgentForgePlugin):
    """Mock plugin for testing."""

    def __init__(self, name: str = "mock", should_fail: bool = False) -> None:
        self._name = name
        self._should_fail = should_fail
        self.on_load_called = False
        self.on_unload_called = False
        self.config_received: dict | None = None

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=self._name,
            version="1.0.0",
            description="Mock plugin for testing",
        )

    def on_load(self, context: AgentForgeContext) -> None:
        if self._should_fail:
            raise RuntimeError("Intentional failure")
        self.on_load_called = True
        context.register_tool(f"{self._name}_tool", lambda: "tool_result")

    def on_unload(self) -> None:
        self.on_unload_called = True

    def on_config_change(self, config: dict) -> None:
        self.config_received = config


class FailingPlugin(AgentForgePlugin):
    """Plugin that fails during load."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(name="failing")

    def on_load(self, context: AgentForgeContext) -> None:
        raise RuntimeError("Intentional failure")


class TestPluginManager:
    """Tests for PluginManager."""

    def test_manager_initialization(self) -> None:
        """Test manager initializes correctly."""
        manager = PluginManager()
        assert manager.context is not None
        assert manager.list_plugins() == []
        assert not manager.is_loaded()

    def test_manager_with_custom_context(self) -> None:
        """Test manager with custom context."""
        context = AgentForgeContext()
        manager = PluginManager(context)
        assert manager.context is context

    def test_load_plugin(self) -> None:
        """Test loading a plugin."""
        manager = PluginManager()
        plugin = manager.load(MockPlugin)

        assert plugin.on_load_called
        assert "mock" in manager.list_plugins()
        assert manager.get_plugin("mock") is plugin
        assert manager.context.get_tool("mock_tool") is not None

    def test_load_plugin_with_config(self) -> None:
        """Test loading a plugin with configuration."""
        manager = PluginManager()
        config = {"setting": "value"}
        plugin = manager.load(MockPlugin, config=config)

        assert plugin.config_received == config

    def test_load_plugin_failure(self) -> None:
        """Test loading a plugin that fails."""
        manager = PluginManager()
        with pytest.raises(PluginLoadError) as exc_info:
            manager.load(FailingPlugin)

        assert "Failed to load plugin" in str(exc_info.value)
        assert exc_info.value.plugin_name == "FailingPlugin"

    def test_unload_plugin(self) -> None:
        """Test unloading a plugin."""
        manager = PluginManager()
        plugin = manager.load(MockPlugin)

        result = manager.unload("mock")

        assert result is True
        assert "mock" not in manager.list_plugins()
        assert plugin.on_unload_called

    def test_unload_nonexistent_plugin(self) -> None:
        """Test unloading a plugin that doesn't exist."""
        manager = PluginManager()
        result = manager.unload("nonexistent")
        assert result is False

    def test_unload_all(self) -> None:
        """Test unloading all plugins."""
        manager = PluginManager()
        manager.load(MockPlugin)
        manager.load(lambda: MockPlugin("plugin2"))

        manager.unload_all()

        assert manager.list_plugins() == []
        assert not manager.is_loaded()

    def test_load_all_idempotent(self) -> None:
        """Test that load_all is idempotent."""
        manager = PluginManager()

        # First load
        plugins1 = manager.load_all()

        # Second load should return same plugins without re-loading
        plugins2 = manager.load_all()

        assert plugins1 is plugins2

    def test_contains(self) -> None:
        """Test __contains__ method."""
        manager = PluginManager()
        manager.load(MockPlugin)

        assert "mock" in manager
        assert "nonexistent" not in manager

    def test_len(self) -> None:
        """Test __len__ method."""
        manager = PluginManager()
        assert len(manager) == 0

        manager.load(MockPlugin)
        assert len(manager) == 1

    def test_get_plugin_metadata(self) -> None:
        """Test getting plugin metadata."""
        manager = PluginManager()
        manager.load(MockPlugin)

        metadata = manager.get_plugin_metadata("mock")

        assert metadata is not None
        assert metadata["name"] == "mock"
        assert metadata["version"] == "1.0.0"

    def test_get_plugin_metadata_nonexistent(self) -> None:
        """Test getting metadata for nonexistent plugin."""
        manager = PluginManager()
        metadata = manager.get_plugin_metadata("nonexistent")
        assert metadata is None


class TestLoggingPlugin:
    """Tests for LoggingPlugin."""

    def test_logging_plugin_metadata(self) -> None:
        """Test LoggingPlugin metadata."""
        plugin = LoggingPlugin()
        metadata = plugin.metadata

        assert metadata.name == "logging"
        assert metadata.version == "1.0.0"
        assert "hooks:log" in metadata.provides

    def test_logging_plugin_registers_hooks(self, capsys: pytest.CaptureFixture) -> None:
        """Test LoggingPlugin registers hooks."""
        context = AgentForgeContext()
        plugin = LoggingPlugin()
        plugin.on_load(context)

        hooks = context.get_hooks("agent.execute")
        assert len(hooks) == 1

        # Test the hook logs correctly
        hooks[0]({"type": "agent", "name": "test", "status": "success", "duration": 0.5})
        captured = capsys.readouterr()
        assert "[LOG]" in captured.out
        assert "agent.test" in captured.out

    def test_logging_plugin_tool_hooks(self) -> None:
        """Test LoggingPlugin registers tool hooks."""
        context = AgentForgeContext()
        plugin = LoggingPlugin()
        plugin.on_load(context)

        hooks = context.get_hooks("tool.execute")
        assert len(hooks) == 1


class TestMetricsPlugin:
    """Tests for MetricsPlugin."""

    def test_metrics_plugin_metadata(self) -> None:
        """Test MetricsPlugin metadata."""
        plugin = MetricsPlugin()
        metadata = plugin.metadata

        assert metadata.name == "metrics"
        assert metadata.version == "1.0.0"
        assert "hooks:metrics" in metadata.provides

    def test_metrics_plugin_collects_metrics(self) -> None:
        """Test MetricsPlugin collects metrics."""
        plugin = MetricsPlugin()
        context = AgentForgeContext()
        plugin.on_load(context)

        # Get the registered hook
        hooks = context.get_hooks("agent.execute")
        assert len(hooks) == 1

        # Simulate events
        hooks[0]({"type": "agent"})
        hooks[0]({"type": "agent"})
        hooks[0]({"type": "tool"})

        metrics = plugin.get_metrics()
        assert metrics["agent"] == 2
        assert metrics["tool"] == 1

    def test_metrics_plugin_reset(self) -> None:
        """Test MetricsPlugin reset."""
        plugin = MetricsPlugin()
        context = AgentForgeContext()
        plugin.on_load(context)

        hooks = context.get_hooks("agent.execute")
        hooks[0]({"type": "agent"})

        plugin.reset_metrics()

        assert plugin.get_metrics() == {}

    def test_metrics_plugin_on_unload(self) -> None:
        """Test MetricsPlugin clears metrics on unload."""
        plugin = MetricsPlugin()
        context = AgentForgeContext()
        plugin.on_load(context)

        hooks = context.get_hooks("agent.execute")
        hooks[0]({"type": "agent"})

        plugin.on_unload()

        assert plugin.get_metrics() == {}


class TestTimingPlugin:
    """Tests for TimingPlugin."""

    def test_timing_plugin_metadata(self) -> None:
        """Test TimingPlugin metadata."""
        plugin = TimingPlugin()
        metadata = plugin.metadata

        assert metadata.name == "timing"
        assert metadata.version == "1.0.0"
        assert "hooks:timing" in metadata.provides

    def test_timing_plugin_collects_timings(self) -> None:
        """Test TimingPlugin collects timing data."""
        plugin = TimingPlugin()
        context = AgentForgeContext()
        plugin.on_load(context)

        # Get the registered hook
        hooks = context.get_hooks("agent.execute")
        assert len(hooks) == 1

        # Simulate events with durations
        hooks[0]({"type": "agent", "duration": 0.5})
        hooks[0]({"type": "agent", "duration": 1.0})
        hooks[0]({"type": "tool", "duration": 0.3})

        stats = plugin.get_stats()
        assert "agent" in stats
        assert stats["agent"]["min"] == 0.5
        assert stats["agent"]["max"] == 1.0
        assert stats["agent"]["avg"] == 0.75
        assert stats["agent"]["count"] == 2
        assert "tool" in stats

    def test_timing_plugin_reset(self) -> None:
        """Test TimingPlugin reset."""
        plugin = TimingPlugin()
        context = AgentForgeContext()
        plugin.on_load(context)

        hooks = context.get_hooks("agent.execute")
        hooks[0]({"type": "agent", "duration": 0.5})

        plugin.reset_stats()

        assert plugin.get_stats() == {}

    def test_timing_plugin_on_unload(self) -> None:
        """Test TimingPlugin clears timings on unload."""
        plugin = TimingPlugin()
        context = AgentForgeContext()
        plugin.on_load(context)

        hooks = context.get_hooks("agent.execute")
        hooks[0]({"type": "agent", "duration": 0.5})

        plugin.on_unload()

        assert plugin.get_stats() == {}

    def test_timing_plugin_ignores_non_numeric_duration(self) -> None:
        """Test TimingPlugin ignores non-numeric durations."""
        plugin = TimingPlugin()
        context = AgentForgeContext()
        plugin.on_load(context)

        hooks = context.get_hooks("agent.execute")
        # String duration should be ignored
        hooks[0]({"type": "agent", "duration": "not a number"})

        stats = plugin.get_stats()
        # String duration is ignored, so no stats recorded
        assert stats == {}

        # But valid numeric durations work
        hooks[0]({"type": "agent", "duration": 1.5})
        stats = plugin.get_stats()
        assert "agent" in stats
        assert stats["agent"]["count"] == 1
        assert stats["agent"]["avg"] == 1.5


class TestPluginIntegration:
    """Integration tests for the plugin system."""

    def test_multiple_plugins_same_context(self) -> None:
        """Test multiple plugins sharing the same context."""
        context = AgentForgeContext()

        # Load multiple plugins
        logging_plugin = LoggingPlugin()
        metrics_plugin = MetricsPlugin()

        logging_plugin.on_load(context)
        metrics_plugin.on_load(context)

        # Both should have registered hooks
        agent_hooks = context.get_hooks("agent.execute")
        assert len(agent_hooks) == 2  # One from each plugin

        tool_hooks = context.get_hooks("tool.execute")
        assert len(tool_hooks) == 2  # One from each plugin

    def test_plugin_with_tool_registration(self) -> None:
        """Test plugin that registers tools."""
        context = AgentForgeContext()
        plugin = MockPlugin()
        plugin.on_load(context)

        # Tool should be registered
        tool = context.get_tool("mock_tool")
        assert tool is not None
        assert tool() == "tool_result"

    def test_full_plugin_lifecycle(self) -> None:
        """Test full plugin lifecycle with manager."""
        manager = PluginManager()

        # Load
        manager.load(MockPlugin)
        assert "mock" in manager
        assert len(manager) == 1

        # Access via context
        assert manager.context.get_tool("mock_tool") is not None

        # Unload
        manager.unload("mock")
        assert "mock" not in manager
        assert len(manager) == 0
