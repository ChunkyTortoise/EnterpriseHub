"""Shared datetime parsing utilities."""

from datetime import datetime, timezone


def parse_iso8601(timestamp_str: str) -> datetime:
    """Parse ISO8601 timestamp, handling 'Z' suffix for UTC."""
    if timestamp_str.endswith("Z"):
        timestamp_str = timestamp_str[:-1] + "+00:00"
    return datetime.fromisoformat(timestamp_str)
