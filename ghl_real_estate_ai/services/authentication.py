"""Backward-compatible authentication dependency exports."""

from typing import Any, Dict

from fastapi import Depends, HTTPException

from .auth_service import get_current_user as _get_current_user


async def get_current_user(current_user: Dict[str, Any] = Depends(_get_current_user)) -> Dict[str, Any]:
    """Compatibility wrapper for legacy imports."""
    return current_user


async def verify_admin_access(current_user: Dict[str, Any] = Depends(_get_current_user)) -> Dict[str, Any]:
    """Require admin-level access for protected routes."""
    role = str(current_user.get("role", "")).lower()
    if role not in {"admin", "super_admin"}:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


__all__ = ["get_current_user", "verify_admin_access"]
