"""
JSON Utilities for EnterpriseHub
================================

Utilities for handling JSON serialization of complex objects including enums,
dataclasses, and datetime objects.

Author: EnterpriseHub - January 2026
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any


class EnterpriseJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for EnterpriseHub objects."""

    def default(self, obj: Any) -> Any:
        """Convert objects to JSON-serializable format."""

        # Handle Enum objects
        if isinstance(obj, Enum):
            return obj.value

        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()

        # Handle objects with to_dict method
        if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
            return obj.to_dict()

        # Fallback to string representation
        return str(obj)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safely serialize an object to JSON with EnterpriseJSONEncoder."""
    return json.dumps(obj, cls=EnterpriseJSONEncoder, **kwargs)


def serialize_signals(signals: list) -> str:
    """Serialize a list of SentimentSignal objects to JSON."""
    # Convert signals to dictionaries first
    signal_dicts = []
    for signal in signals:
        if hasattr(signal, "to_dict"):
            signal_dicts.append(signal.to_dict())
        else:
            # Fallback for signals that don't have to_dict method
            signal_dict = {}
            for field, value in signal.__dict__.items():
                if isinstance(value, Enum):
                    signal_dict[field] = value.value
                elif isinstance(value, datetime):
                    signal_dict[field] = value.isoformat()
                else:
                    signal_dict[field] = value
            signal_dicts.append(signal_dict)

    return json.dumps(signal_dicts, indent=2)
