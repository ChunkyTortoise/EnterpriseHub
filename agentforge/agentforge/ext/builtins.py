"""Built-in plugins that ship with AgentForge.

This module provides standard plugins for logging and metrics collection
that are automatically available when AgentForge is installed.

Available Plugins:
    - LoggingPlugin: Logs agent and tool execution events.
    - MetricsPlugin: Collects metrics on agent and tool executions.
"""

from typing import Any

from agentforge.ext.base import AgentForgeContext, AgentForgePlugin, PluginMetadata


class LoggingPlugin(AgentForgePlugin):
    """Built-in plugin for logging agent and tool execution events.

    This plugin registers hooks for agent.execute and tool.execute events
    and logs them to stdout. Useful for debugging and monitoring.

    Example:
        ```python
        from agentforge.ext import PluginManager

        manager = PluginManager()
        manager.load_all()  # LoggingPlugin is auto-discovered

        # Hooks are now registered for logging
        for hook in manager.context.get_hooks("agent.execute"):
            hook({"type": "agent", "name": "my_agent"})
        ```
    """

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="logging",
            version="1.0.0",
            description="Built-in logging plugin for agent and tool execution events",
            author="AgentForge Team",
            license="MIT",
            provides=["hooks:log"],
        )

    def on_load(self, context: AgentForgeContext) -> None:
        """Register logging hooks for agent and tool execution.

        Args:
            context: Plugin context for registration.
        """
        def log_handler(event_data: dict[str, Any]) -> None:
            """Handle logging for execution events.

            Args:
                event_data: Event data dictionary containing execution info.
            """
            event_type = event_data.get("type", "unknown")
            name = event_data.get("name", "unnamed")
            status = event_data.get("status", "unknown")
            duration = event_data.get("duration", "N/A")
            print(f"[LOG] {event_type}.{name} - status={status} duration={duration}")

        context.register_hook("agent.execute", log_handler)
        context.register_hook("tool.execute", log_handler)


class MetricsPlugin(AgentForgePlugin):
    """Built-in plugin for metrics collection.

    This plugin collects metrics on agent and tool executions, tracking
    counts by event type. Useful for monitoring and analytics.

    Example:
        ```python
        from agentforge.ext import PluginManager

        manager = PluginManager()
        manager.load_all()  # MetricsPlugin is auto-discovered

        # Get the plugin to access metrics
        metrics_plugin = manager.get_plugin("metrics")
        print(metrics_plugin.get_metrics())
        ```
    """

    def __init__(self) -> None:
        """Initialize the metrics plugin with empty metrics storage."""
        self._metrics: dict[str, int] = {}

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="metrics",
            version="1.0.0",
            description="Built-in metrics collection plugin for execution tracking",
            author="AgentForge Team",
            license="MIT",
            provides=["hooks:metrics"],
        )

    def on_load(self, context: AgentForgeContext) -> None:
        """Register metrics collection hooks.

        Args:
            context: Plugin context for registration.
        """
        def metrics_handler(event_data: dict[str, Any]) -> None:
            """Handle metrics collection for execution events.

            Args:
                event_data: Event data dictionary containing execution info.
            """
            event_type = event_data.get("type", "unknown")
            self._metrics[event_type] = self._metrics.get(event_type, 0) + 1

        context.register_hook("agent.execute", metrics_handler)
        context.register_hook("tool.execute", metrics_handler)

    def on_unload(self) -> None:
        """Clear metrics when plugin is unloaded."""
        self._metrics.clear()

    def get_metrics(self) -> dict[str, int]:
        """Get current metrics.

        Returns:
            Dictionary of event types to execution counts.
        """
        return self._metrics.copy()

    def reset_metrics(self) -> None:
        """Reset all metrics to zero."""
        self._metrics.clear()


class TimingPlugin(AgentForgePlugin):
    """Built-in plugin for timing execution events.

    This plugin tracks execution duration for agents and tools,
    providing statistics like min, max, and average times.

    Example:
        ```python
        from agentforge.ext import PluginManager

        manager = PluginManager()
        manager.load_all()

        timing_plugin = manager.get_plugin("timing")
        print(timing_plugin.get_stats())
        ```
    """

    def __init__(self) -> None:
        """Initialize the timing plugin with empty timing storage."""
        self._timings: dict[str, list[float]] = {}

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="timing",
            version="1.0.0",
            description="Built-in timing plugin for execution duration tracking",
            author="AgentForge Team",
            license="MIT",
            provides=["hooks:timing"],
        )

    def on_load(self, context: AgentForgeContext) -> None:
        """Register timing hooks.

        Args:
            context: Plugin context for registration.
        """
        def timing_handler(event_data: dict[str, Any]) -> None:
            """Handle timing for execution events.

            Args:
                event_data: Event data dictionary containing duration info.
            """
            event_type = event_data.get("type", "unknown")
            duration = event_data.get("duration", 0.0)
            if isinstance(duration, (int, float)):
                if event_type not in self._timings:
                    self._timings[event_type] = []
                self._timings[event_type].append(duration)

        context.register_hook("agent.execute", timing_handler)
        context.register_hook("tool.execute", timing_handler)

    def on_unload(self) -> None:
        """Clear timings when plugin is unloaded."""
        self._timings.clear()

    def get_stats(self) -> dict[str, dict[str, float]]:
        """Get timing statistics for all event types.

        Returns:
            Dictionary with min, max, avg, and count for each event type.
        """
        stats: dict[str, dict[str, float]] = {}
        for event_type, times in self._timings.items():
            if times:
                stats[event_type] = {
                    "min": min(times),
                    "max": max(times),
                    "avg": sum(times) / len(times),
                    "count": len(times),
                }
        return stats

    def reset_stats(self) -> None:
        """Reset all timing statistics."""
        self._timings.clear()
