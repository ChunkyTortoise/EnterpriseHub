"""Hardening tests for WebSocket JWT authentication helpers."""

import importlib
from typing import Any, Callable, Dict
from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture(
    params=[
        (
            "ghl_real_estate_ai.api.routes.analytics",
            "_authenticate_websocket",
            ("analytics_read", "analytics_websocket"),
            "analytics_dev",
            "analytics_user",
        ),
        (
            "ghl_real_estate_ai.api.routes.ai_concierge",
            "_authenticate_websocket_connection",
            ("concierge_read", "concierge_websocket"),
            "concierge_dev",
            "concierge_user",
        ),
    ],
    ids=["analytics", "ai_concierge"],
)
def auth_target(request: pytest.FixtureRequest) -> Dict[str, Any]:
    module_path, function_name, required_permissions, dev_role, default_role = request.param
    module = importlib.import_module(module_path)
    return {
        "module_path": module_path,
        "module": module,
        "function": getattr(module, function_name),
        "required_permissions": required_permissions,
        "dev_role": dev_role,
        "default_role": default_role,
    }


def _set_env(monkeypatch: pytest.MonkeyPatch, module: Any, *, environment: str, allow_insecure: str) -> None:
    monkeypatch.setenv("ALLOW_INSECURE_WEBSOCKET_AUTH", allow_insecure)
    monkeypatch.setattr(module.settings, "environment", environment, raising=False)


async def test_empty_and_blank_tokens_rejected(auth_target: Dict[str, Any]) -> None:
    authenticate: Callable[..., Any] = auth_target["function"]

    assert await authenticate(None) is None
    assert await authenticate("") is None
    assert await authenticate("   ") is None


async def test_dev_bypass_allowed_only_with_non_prod_flag_and_prefix(
    auth_target: Dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    module = auth_target["module"]
    authenticate: Callable[..., Any] = auth_target["function"]
    dev_role = auth_target["dev_role"]
    required_permissions = auth_target["required_permissions"]

    _set_env(monkeypatch, module, environment="development", allow_insecure="true")

    with patch.object(module.JWTAuth, "verify_token", side_effect=AssertionError("JWT verify should not run in bypass")):
        result = await authenticate("dev_ws_trusted_user")

    assert result == {
        "user_id": "trusted_user",
        "role": dev_role,
        "permissions": list(required_permissions),
    }


async def test_dev_bypass_requires_prefix(
    auth_target: Dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    module = auth_target["module"]
    authenticate: Callable[..., Any] = auth_target["function"]
    default_role = auth_target["default_role"]
    required_permissions = auth_target["required_permissions"]

    _set_env(monkeypatch, module, environment="development", allow_insecure="true")

    with patch.object(module.JWTAuth, "verify_token", return_value={"sub": "jwt_user", "permissions": []}) as verify_mock:
        result = await authenticate("non_prefixed_token")

    verify_mock.assert_called_once_with("non_prefixed_token")
    assert result is not None
    assert result["user_id"] == "jwt_user"
    assert result["role"] == default_role
    for permission in required_permissions:
        assert permission in result["permissions"]


async def test_production_blocks_dev_bypass(
    auth_target: Dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    module = auth_target["module"]
    authenticate: Callable[..., Any] = auth_target["function"]
    default_role = auth_target["default_role"]
    required_permissions = auth_target["required_permissions"]

    _set_env(monkeypatch, module, environment="production", allow_insecure="true")

    with patch.object(module.JWTAuth, "verify_token", return_value={"sub": "prod_user", "permissions": []}) as verify_mock:
        result = await authenticate("dev_ws_prod_user")

    verify_mock.assert_called_once_with("dev_ws_prod_user")
    assert result is not None
    assert result["user_id"] == "prod_user"
    assert result["role"] == default_role
    for permission in required_permissions:
        assert permission in result["permissions"]


async def test_missing_sub_claim_is_rejected(auth_target: Dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    module = auth_target["module"]
    authenticate: Callable[..., Any] = auth_target["function"]

    _set_env(monkeypatch, module, environment="development", allow_insecure="false")

    with patch.object(module.JWTAuth, "verify_token", return_value={"permissions": ["custom_permission"]}):
        assert await authenticate("jwt_token_without_sub") is None


async def test_permissions_normalized_and_required_permissions_enforced(
    auth_target: Dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    module = auth_target["module"]
    authenticate: Callable[..., Any] = auth_target["function"]
    required_permissions = auth_target["required_permissions"]

    _set_env(monkeypatch, module, environment="development", allow_insecure="false")

    payload = {
        "sub": "user_abc",
        "permissions": "custom_permission",
        "role": "custom_role",
    }

    with patch.object(module.JWTAuth, "verify_token", return_value=payload):
        result = await authenticate("jwt_valid_token")

    assert result is not None
    assert result["user_id"] == "user_abc"
    assert result["role"] == "custom_role"
    assert result["permissions"][0] == "custom_permission"
    for permission in required_permissions:
        assert permission in result["permissions"]


async def test_jwt_verify_exception_returns_none(auth_target: Dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    module = auth_target["module"]
    authenticate: Callable[..., Any] = auth_target["function"]

    _set_env(monkeypatch, module, environment="development", allow_insecure="false")

    with patch.object(module.JWTAuth, "verify_token", side_effect=RuntimeError("invalid jwt")):
        assert await authenticate("broken_token") is None
