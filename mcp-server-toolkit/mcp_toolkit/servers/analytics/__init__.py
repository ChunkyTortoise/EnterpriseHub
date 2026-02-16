"""Analytics MCP Server — Query metrics, generate charts, anomaly detection."""

from mcp_toolkit.servers.analytics.server import mcp as analytics_server
from mcp_toolkit.servers.analytics.chart_generator import ChartGenerator

__all__ = ["analytics_server", "ChartGenerator"]
