"""Calendar MCP Server — Booking, scheduling, and availability management."""

from mcp_toolkit.servers.calendar.server import mcp as calendar_server
from mcp_toolkit.servers.calendar.availability import AvailabilityFinder

__all__ = ["calendar_server", "AvailabilityFinder"]
