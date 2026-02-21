"""ASCII dashboard and monitoring for AgentForge.

This module provides a simple ASCII-based dashboard for monitoring
agent execution in real-time. Includes both standalone Dashboard
and MetricsCollector-integrated ASCIIDashboard.
"""

import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from agentforge.observe.metrics import MetricsCollector


class DashboardConfig(BaseModel):
    """Configuration for ASCII dashboard.

    Attributes:
        refresh_rate: How often to refresh the dashboard (seconds).
        show_tokens: Whether to show token usage.
        show_costs: Whether to show costs.
        show_latencies: Whether to show latency stats.
        show_agents: Whether to show per-agent breakdown.
        width: Width of the dashboard in characters.
    """

    refresh_rate: float = Field(default=1.0, ge=0.1, description="Refresh rate in seconds")
    show_tokens: bool = True
    show_costs: bool = True
    show_latencies: bool = True
    show_agents: bool = True
    width: int = Field(default=50, ge=30, description="Dashboard width in characters")


class Dashboard:
    """ASCII monitoring dashboard for agent execution.

    Provides real-time visualization of:
    - Active agents and their status
    - Recent executions
    - Token usage
    - Error rates
    - Performance metrics

    Example:
        ```python
        dashboard = Dashboard()

        # Update dashboard with execution
        dashboard.record_execution(
            agent_id="agent-1",
            status="completed",
            duration_ms=150.5,
            tokens=100,
        )

        # Render dashboard
        print(dashboard.render())
        ```
    """

    def __init__(
        self,
        title: str = "AgentForge Dashboard",
        max_history: int = 100,
    ) -> None:
        """Initialize the dashboard.

        Args:
            title: Dashboard title.
            max_history: Maximum number of historical records.
        """
        self.title = title
        self.max_history = max_history
        self._executions: list[dict[str, Any]] = []
        self._agent_status: dict[str, str] = {}
        self._start_time = time.time()

    def record_execution(
        self,
        agent_id: str,
        status: str,
        duration_ms: float | None = None,
        tokens: int | None = None,
        error: str | None = None,
    ) -> None:
        """Record an execution event.

        Args:
            agent_id: ID of the agent.
            status: Execution status.
            duration_ms: Execution duration in milliseconds.
            tokens: Total tokens used.
            error: Error message if failed.
        """
        self._executions.append(
            {
                "timestamp": time.time(),
                "agent_id": agent_id,
                "status": status,
                "duration_ms": duration_ms,
                "tokens": tokens,
                "error": error,
            }
        )

        # Trim history
        if len(self._executions) > self.max_history:
            self._executions = self._executions[-self.max_history :]

        # Update agent status
        self._agent_status[agent_id] = status

    def update_agent_status(
        self,
        agent_id: str,
        status: str,
    ) -> None:
        """Update an agent's status.

        Args:
            agent_id: ID of the agent.
            status: Current status.
        """
        self._agent_status[agent_id] = status

    def render(self) -> str:
        """Render the dashboard as ASCII.

        Returns:
            ASCII dashboard string.
        """
        lines = []

        # Header
        lines.append("═" * 60)
        lines.append(f"  {self.title}")
        lines.append(f"  Uptime: {self._format_uptime()}")
        lines.append("═" * 60)
        lines.append("")

        # Agent Status
        lines.append("┌─ AGENT STATUS " + "─" * 44 + "┐")
        if self._agent_status:
            for agent_id, status in self._agent_status.items():
                status_icon = self._get_status_icon(status)
                lines.append(f"│ {status_icon} {agent_id:<30} {status:<15} │")
        else:
            lines.append("│ No active agents" + " " * 42 + "│")
        lines.append("└" + "─" * 58 + "┘")
        lines.append("")

        # Statistics
        stats = self._calculate_stats()
        lines.append("┌─ STATISTICS " + "─" * 45 + "┐")
        lines.append(f"│ Total Executions: {stats['total']:<37} │")
        lines.append(f"│ Successful: {stats['success']:<41} │")
        lines.append(f"│ Failed: {stats['failed']:<45} │")
        lines.append(f"│ Avg Duration: {stats['avg_duration_ms']:<38} │")
        lines.append(f"│ Total Tokens: {stats['total_tokens']:<39} │")
        lines.append("└" + "─" * 58 + "┘")
        lines.append("")

        # Recent Executions
        lines.append("┌─ RECENT EXECUTIONS " + "─" * 38 + "┐")
        recent = self._executions[-5:] if self._executions else []
        if recent:
            for exec_record in reversed(recent):
                timestamp = datetime.fromtimestamp(exec_record["timestamp"]).strftime("%H:%M:%S")
                agent = exec_record["agent_id"][:15]
                status = exec_record["status"][:10]
                duration = f"{exec_record.get('duration_ms', 0):.1f}ms"
                lines.append(f"│ {timestamp} │ {agent:<15} │ {status:<10} │ {duration:>8} │")
        else:
            lines.append("│ No recent executions" + " " * 36 + "│")
        lines.append("└" + "─" * 58 + "┘")

        return "\n".join(lines)

    def render_compact(self) -> str:
        """Render a compact one-line status.

        Returns:
            Compact status string.
        """
        stats = self._calculate_stats()
        active = sum(1 for s in self._agent_status.values() if s == "running")

        return (
            f"[AgentForge] "
            f"Active: {active} │ "
            f"Execs: {stats['total']} │ "
            f"Success: {stats['success_rate']:.1f}% │ "
            f"Avg: {stats['avg_duration_ms']:.1f}ms"
        )

    def _calculate_stats(self) -> dict[str, Any]:
        """Calculate statistics from execution history."""
        total = len(self._executions)
        success = sum(1 for e in self._executions if e["status"] == "completed")
        failed = sum(1 for e in self._executions if e["status"] == "failed")

        durations = [e["duration_ms"] for e in self._executions if e.get("duration_ms") is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0

        tokens = sum(e.get("tokens", 0) for e in self._executions if e.get("tokens") is not None)

        return {
            "total": total,
            "success": success,
            "failed": failed,
            "success_rate": (success / total * 100) if total > 0 else 0,
            "avg_duration_ms": avg_duration,
            "total_tokens": tokens,
        }

    def _format_uptime(self) -> str:
        """Format uptime as human-readable string."""
        uptime = time.time() - self._start_time

        if uptime < 60:
            return f"{uptime:.0f}s"
        elif uptime < 3600:
            minutes = uptime / 60
            return f"{minutes:.0f}m"
        else:
            hours = uptime / 3600
            return f"{hours:.1f}h"

    @staticmethod
    def _get_status_icon(status: str) -> str:
        """Get an icon for a status."""
        icons = {
            "idle": "⚪",
            "running": "🔵",
            "completed": "🟢",
            "failed": "🔴",
        }
        return icons.get(status, "⚪")


class StructuredLogger:
    """Structured JSON logger for agent events.

    Outputs structured log entries suitable for ingestion by
    log aggregation systems.

    Example:
        ```python
        logger = StructuredLogger("agentforge")
        logger.info("agent_started", agent_id="agent-1", task="process")
        logger.error("agent_failed", agent_id="agent-1", error="timeout")
        ```
    """

    def __init__(
        self,
        name: str = "agentforge",
        level: str = "INFO",
    ) -> None:
        """Initialize the logger.

        Args:
            name: Logger name.
            level: Minimum log level.
        """
        self.name = name
        self.level = level
        self._levels = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}

    def _log(
        self,
        level: str,
        event: str,
        **kwargs: Any,
    ) -> None:
        """Output a structured log entry."""
        if self._levels.get(level, 0) < self._levels.get(self.level, 0):
            return

        import json

        entry = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": level,
            "logger": self.name,
            "event": event,
            **kwargs,
        }

        print(json.dumps(entry))

    def debug(self, event: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log("DEBUG", event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log("INFO", event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log("WARNING", event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log("ERROR", event, **kwargs)


class ASCIIDashboard:
    """ASCII-based monitoring dashboard integrated with MetricsCollector.

    Renders metrics as ASCII art for console display.
    Can be attached to a MetricsCollector for real-time updates.

    Example:
        ```python
        from agentforge.observe import MetricsCollector, ASCIIDashboard

        metrics = MetricsCollector()
        dashboard = ASCIIDashboard()
        dashboard.attach(metrics)

        # After some operations...
        dashboard.print()
        ```
    """

    def __init__(self, config: DashboardConfig | None = None):
        """Initialize the dashboard.

        Args:
            config: Dashboard configuration. Uses defaults if not provided.
        """
        self.config = config or DashboardConfig()
        self._metrics: MetricsCollector | None = None

    def attach(self, metrics: "MetricsCollector") -> None:
        """Attach to a metrics collector.

        Args:
            metrics: The MetricsCollector to display.
        """
        self._metrics = metrics

    def detach(self) -> None:
        """Detach from the current metrics collector."""
        self._metrics = None

    def render(self) -> str:
        """Render the dashboard as ASCII.

        Returns:
            ASCII string representation of the dashboard.
        """
        if not self._metrics:
            return "No metrics attached"

        summary = self._metrics.get_summary()
        lines = [
            "╔" + "═" * (self.config.width - 2) + "╗",
            "║" + "AgentForge Dashboard".center(self.config.width - 2) + "║",
            "╠" + "═" * (self.config.width - 2) + "╣",
        ]

        if self.config.show_tokens:
            tokens = summary.get("tokens", {})
            lines.extend(self._render_tokens_section(tokens))

        if self.config.show_costs:
            lines.extend(self._render_costs_section(summary))

        if self.config.show_latencies:
            latencies = summary.get("latencies", {})
            if latencies:
                lines.extend(self._render_latencies_section(latencies))

        if self.config.show_agents:
            agent_tokens = summary.get("agent_tokens", {})
            if agent_tokens:
                lines.extend(self._render_agents_section(agent_tokens))

        lines.append("╚" + "═" * (self.config.width - 2) + "╝")

        return "\n".join(lines)

    def _render_tokens_section(self, tokens: dict[str, int]) -> list[str]:
        """Render the token usage section."""
        lines = [
            "║ Token Usage" + " " * (self.config.width - 13) + "║",
            "║" + "─" * (self.config.width - 2) + "║",
        ]

        prompt = tokens.get("prompt_tokens", 0)
        completion = tokens.get("completion_tokens", 0)
        total = tokens.get("total_tokens", 0)

        lines.append(f"║   Prompt:     {prompt:>12,} tokens  ║")
        lines.append(f"║   Completion: {completion:>12,} tokens  ║")
        lines.append(f"║   Total:      {total:>12,} tokens  ║")
        lines.append("║" + " " * (self.config.width - 2) + "║")

        return lines

    def _render_costs_section(self, summary: dict[str, Any]) -> list[str]:
        """Render the costs section."""
        lines = [
            "║ Costs" + " " * (self.config.width - 7) + "║",
            "║" + "─" * (self.config.width - 2) + "║",
        ]

        total_cost = summary.get("cost_usd", 0)
        lines.append(f"║   Total: ${total_cost:>14.4f}       ║")

        cost_by_model = summary.get("cost_by_model", {})
        if cost_by_model:
            lines.append("║" + " " * (self.config.width - 2) + "║")
            lines.append("║   By Model:" + " " * (self.config.width - 13) + "║")
            for model, cost in sorted(cost_by_model.items()):
                model_display = model[:20] if len(model) > 20 else model
                lines.append(f"║     {model_display:<20} ${cost:>8.4f} ║")

        lines.append("║" + " " * (self.config.width - 2) + "║")

        return lines

    def _render_latencies_section(self, latencies: dict[str, dict]) -> list[str]:
        """Render the latencies section."""
        lines = [
            "║ Latencies" + " " * (self.config.width - 11) + "║",
            "║" + "─" * (self.config.width - 2) + "║",
        ]

        for op, stats in latencies.items():
            op_display = op[:15] if len(op) > 15 else op
            p50_ms = stats.get("p50", 0) * 1000
            p95_ms = stats.get("p95", 0) * 1000
            count = stats.get("count", 0)

            lines.append(f"║   {op_display:<15} (n={count:>4})       ║")
            lines.append(f"║     P50: {p50_ms:>8.1f}ms  P95: {p95_ms:>8.1f}ms ║")

        lines.append("║" + " " * (self.config.width - 2) + "║")

        return lines

    def _render_agents_section(self, agent_tokens: dict[str, dict]) -> list[str]:
        """Render the per-agent section."""
        lines = [
            "║ Per-Agent Tokens" + " " * (self.config.width - 18) + "║",
            "║" + "─" * (self.config.width - 2) + "║",
        ]

        for agent, tokens in sorted(agent_tokens.items()):
            agent_display = agent[:20] if len(agent) > 20 else agent
            total = tokens.get("total_tokens", 0)

            lines.append(f"║   {agent_display:<20}            ║")
            lines.append(f"║     Total: {total:>10,}              ║")

        lines.append("║" + " " * (self.config.width - 2) + "║")

        return lines

    def print(self) -> None:
        """Print the dashboard to console."""
        print(self.render())

    def __str__(self) -> str:
        """String representation of the dashboard."""
        return self.render()

    def __repr__(self) -> str:
        """Developer representation."""
        return f"ASCIIDashboard(config={self.config!r}, attached={self._metrics is not None})"


def create_dashboard(
    metrics: Optional["MetricsCollector"] = None,
    **config_kwargs: Any,
) -> ASCIIDashboard:
    """Create and optionally attach a dashboard.

    Args:
        metrics: Optional MetricsCollector to attach.
        **config_kwargs: Configuration options for DashboardConfig.

    Returns:
        Configured ASCIIDashboard instance.

    Example:
        ```python
        from agentforge.observe import create_dashboard, get_metrics

        metrics = get_metrics()
        dashboard = create_dashboard(metrics, width=60, show_costs=True)
        dashboard.print()
        ```
    """
    config = DashboardConfig(**config_kwargs) if config_kwargs else None
    dashboard = ASCIIDashboard(config)
    if metrics:
        dashboard.attach(metrics)
    return dashboard


__all__ = ["Dashboard", "DashboardConfig", "ASCIIDashboard", "StructuredLogger", "create_dashboard"]
