from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict

from fastapi import Header, Request

from modules.appointment_manager import AppointmentManager
from modules.ghl_sync import GHLSyncService
from modules.inventory_manager import InventoryManager
from modules.voice_trigger import trigger_outbound_call


@dataclass
class Services:
    inventory: InventoryManager
    ghl: GHLSyncService
    appointment: AppointmentManager
    trigger_outbound_call: Any


class DemoAuthError(Exception):
    """Raised when demo API key auth is enabled and a request is unauthorized."""

    pass


class AuthMisconfiguredError(Exception):
    """Raised when required auth mode is enabled without a configured API key."""

    pass


AUTH_MODE_OPTIONAL = "optional"
AUTH_MODE_REQUIRED = "required"


def _get_auth_mode() -> str:
    auth_mode = os.getenv("PORTAL_API_AUTH_MODE", AUTH_MODE_OPTIONAL).strip().lower()
    if auth_mode not in {AUTH_MODE_OPTIONAL, AUTH_MODE_REQUIRED}:
        return AUTH_MODE_OPTIONAL
    return auth_mode


@lru_cache(maxsize=1)
def get_services() -> Services:
    return Services(
        inventory=InventoryManager(),
        ghl=GHLSyncService(),
        appointment=AppointmentManager(),
        trigger_outbound_call=trigger_outbound_call,
    )


def reset_services() -> Dict[str, int]:
    services = get_services()
    summary = {
        "inventory_interactions_cleared": services.inventory.interaction_count,
        "ghl_actions_cleared": services.ghl.action_count,
        "appointments_cleared": services.appointment.booking_count,
    }
    services.inventory.reset()
    services.ghl.reset()
    services.appointment.reset()
    return summary


def get_service_state() -> Dict[str, int]:
    services = get_services()
    return {
        "inventory_leads": services.inventory.lead_count,
        "inventory_properties": services.inventory.property_count,
        "inventory_interactions": services.inventory.interaction_count,
        "ghl_actions": services.ghl.action_count,
        "appointments": services.appointment.booking_count,
    }


def get_detailed_service_state(recent_limit: int = 5) -> Dict[str, Any]:
    services = get_services()
    return {
        "inventory": services.inventory.get_state_snapshot(recent_limit=recent_limit),
        "ghl": services.ghl.get_state_snapshot(recent_limit=recent_limit),
        "appointment": services.appointment.get_state_snapshot(recent_limit=recent_limit),
    }


def get_idempotency_key(idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> str | None:
    return idempotency_key


def require_demo_api_key(request: Request, x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
    auth_mode = _get_auth_mode()
    expected_api_key = os.getenv("PORTAL_API_DEMO_KEY")
    if auth_mode == AUTH_MODE_REQUIRED:
        if not expected_api_key:
            raise AuthMisconfiguredError("Authentication is required but PORTAL_API_DEMO_KEY is not configured")
        if x_api_key == expected_api_key:
            return
        raise DemoAuthError("Invalid API key")
    if not expected_api_key:
        return
    if x_api_key == expected_api_key:
        return
    raise DemoAuthError("Invalid API key")
