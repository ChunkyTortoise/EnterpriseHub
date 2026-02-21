from __future__ import annotations

import json
import os

from fastapi.testclient import TestClient

from portal_api import app
from portal_api.dependencies import get_services

client = TestClient(app)


def _reset_state(api_key: str | None = None) -> None:
    effective_api_key = api_key or os.getenv("PORTAL_API_DEMO_KEY")
    headers = {"X-API-Key": effective_api_key} if effective_api_key else None
    response = client.post("/system/reset", headers=headers)
    assert response.status_code == 200


def _openapi_response_ref(paths: dict, route: str, method: str) -> str:
    return paths[route][method]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]


def _openapi_error_ref(paths: dict, route: str, method: str, status_code: str) -> str:
    return paths[route][method]["responses"][status_code]["content"]["application/json"]["schema"]["$ref"]


def _openapi_request_ref(paths: dict, route: str, method: str) -> str:
    return paths[route][method]["requestBody"]["content"]["application/json"]["schema"]["$ref"]


def _assert_request_id_header(response, expected: str | None = None) -> None:
    request_id = response.headers.get("X-Request-ID")
    assert request_id
    if expected:
        assert request_id == expected


def test_root_endpoint() -> None:
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "GHL Real Estate AI API is running"
    assert payload["reset"] == "/system/reset"
    assert payload["state"] == "/system/state"
    assert payload["state_details"] == "/system/state/details"


def test_openapi_contract_models_bound_for_critical_routes() -> None:
    openapi = app.openapi()
    paths = openapi["paths"]

    expected_response_refs = {
        ("/", "get"): "RootResponse",
        ("/health", "get"): "HealthResponse",
        ("/system/state", "get"): "StateResponse",
        ("/system/state/details", "get"): "DetailedStateResponse",
        ("/portal/swipe", "post"): "SwipeResponse",
        ("/vapi/tools/book-tour", "post"): "VapiToolResponse",
        ("/ghl/sync", "post"): "GHLSyncResponse",
    }

    for (route, method), schema_name in expected_response_refs.items():
        assert _openapi_response_ref(paths, route, method).endswith(f"/{schema_name}")

    assert _openapi_request_ref(paths, "/portal/swipe", "post").endswith("/Interaction")
    assert _openapi_request_ref(paths, "/vapi/tools/book-tour", "post").endswith("/VapiToolPayload")
    assert "requestBody" not in paths["/ghl/sync"]["post"]


def test_openapi_ghl_sync_500_contract_locked() -> None:
    openapi = app.openapi()
    responses = openapi["paths"]["/ghl/sync"]["post"]["responses"]

    assert "500" in responses
    assert responses["500"]["description"] == "GoHighLevel sync failed"
    assert _openapi_error_ref(openapi["paths"], "/ghl/sync", "post", "500").endswith("/ApiErrorResponse")


def test_openapi_401_contracts_locked_for_mutating_routes() -> None:
    openapi = app.openapi()
    paths = openapi["paths"]
    guarded_routes = [
        ("/portal/swipe", "post"),
        ("/vapi/tools/book-tour", "post"),
        ("/ghl/sync", "post"),
        ("/system/reset", "post"),
    ]

    for route, method in guarded_routes:
        responses = paths[route][method]["responses"]
        assert "401" in responses
        assert responses["401"]["description"] == "API key missing or invalid"
        assert _openapi_error_ref(paths, route, method, "401").endswith("/ApiErrorResponse")


def test_openapi_422_validation_contracts_locked_on_selected_routes() -> None:
    openapi = app.openapi()
    paths = openapi["paths"]

    selected_routes = [
        ("/portal/swipe", "post"),
        ("/system/state/details", "get"),
    ]

    for route, method in selected_routes:
        responses = paths[route][method]["responses"]
        assert "422" in responses
        assert responses["422"]["description"] == "Validation Error"
        assert _openapi_error_ref(paths, route, method, "422").endswith("/HTTPValidationError")


def test_openapi_interaction_schema_constraints_locked() -> None:
    interaction_schema = app.openapi()["components"]["schemas"]["Interaction"]
    action_schema = interaction_schema["properties"]["action"]

    assert set(interaction_schema["required"]) == {"contact_id", "property_id", "action"}
    assert set(action_schema["enum"]) == {"like", "pass"}
    assert len(action_schema["enum"]) == 2


def test_openapi_state_details_limit_parameter_bounds() -> None:
    details_get = app.openapi()["paths"]["/system/state/details"]["get"]
    limit_param = next(param for param in details_get["parameters"] if param.get("name") == "limit")
    limit_schema = limit_param["schema"]

    assert limit_param["in"] == "query"
    assert limit_schema["default"] == 5
    assert limit_schema["minimum"] == 0
    assert limit_schema["maximum"] == 100


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    _assert_request_id_header(response)
    assert response.json()["status"] == "ok"


def test_request_id_header_propagates_when_supplied() -> None:
    response = client.get("/health", headers={"X-Request-ID": "demo-request-123"})
    assert response.status_code == 200
    _assert_request_id_header(response, expected="demo-request-123")


def test_portal_deck_endpoint() -> None:
    _reset_state()
    response = client.get("/portal/deck", params={"contact_id": "lead_001"})
    assert response.status_code == 200
    payload = response.json()
    assert "deck" in payload
    assert isinstance(payload["deck"], list)
    assert len(payload["deck"]) >= 1


def test_swipe_then_reset_restores_state() -> None:
    _reset_state()
    baseline_deck = client.get("/portal/deck", params={"contact_id": "lead_001"}).json()["deck"]

    swipe_response = client.post(
        "/portal/swipe",
        json={
            "contact_id": "lead_001",
            "property_id": "prop_001",
            "action": "like",
            "location_id": "loc_123",
            "time_on_card": 12.7,
            "feedback": {"note": "interested"},
        },
    )
    assert swipe_response.status_code == 200
    swipe_payload = swipe_response.json()
    assert swipe_payload["status"] == "success"
    assert swipe_payload["high_intent"] is True

    reduced_deck = client.get("/portal/deck", params={"contact_id": "lead_001"}).json()["deck"]
    assert len(reduced_deck) <= len(baseline_deck)

    reset_response = client.post("/system/reset")
    assert reset_response.status_code == 200
    reset_payload = reset_response.json()
    assert reset_payload["status"] == "success"
    assert "inventory_interactions_cleared" in reset_payload["reset"]

    reset_deck = client.get("/portal/deck", params={"contact_id": "lead_001"}).json()["deck"]
    assert len(reset_deck) == len(baseline_deck)


def test_system_state_endpoint_tracks_counters() -> None:
    _reset_state()
    baseline = client.get("/system/state")
    assert baseline.status_code == 200
    baseline_state = baseline.json()["state"]
    assert baseline_state["inventory_leads"] >= 1
    assert baseline_state["inventory_properties"] >= 1
    assert baseline_state["inventory_interactions"] == 0
    assert baseline_state["ghl_actions"] == 0
    assert baseline_state["appointments"] == 0

    swipe_response = client.post(
        "/portal/swipe",
        json={
            "contact_id": "lead_001",
            "property_id": "prop_001",
            "action": "like",
            "location_id": "loc_123",
            "time_on_card": 12.7,
            "feedback": {"note": "interested"},
        },
    )
    assert swipe_response.status_code == 200

    booking_response = client.post(
        "/vapi/tools/book-tour",
        json={
            "toolCall": {
                "id": "tool-3",
                "function": {
                    "arguments": {
                        "contact_id": "lead_001",
                        "slot_time": "2026-02-15T10:00:00",
                        "property_address": "123 Palm Ave",
                    },
                },
            }
        },
    )
    assert booking_response.status_code == 200

    current = client.get("/system/state")
    assert current.status_code == 200
    current_state = current.json()["state"]
    assert current_state["inventory_interactions"] == 1
    assert current_state["ghl_actions"] == 3
    assert current_state["appointments"] == 1

    reset_response = client.post("/system/reset")
    assert reset_response.status_code == 200
    reset_payload = reset_response.json()
    assert reset_payload["reset"]["inventory_interactions_cleared"] == 1
    assert reset_payload["reset"]["ghl_actions_cleared"] == 3
    assert reset_payload["reset"]["appointments_cleared"] == 1

    after_reset = client.get("/system/state")
    assert after_reset.status_code == 200
    after_reset_state = after_reset.json()["state"]
    assert after_reset_state["inventory_interactions"] == 0
    assert after_reset_state["ghl_actions"] == 0
    assert after_reset_state["appointments"] == 0


def test_state_endpoint_aliases_match() -> None:
    _reset_state()
    system_state = client.get("/system/state")
    short_state = client.get("/state")
    admin_state = client.get("/admin/state")
    assert system_state.status_code == 200
    assert short_state.status_code == 200
    assert admin_state.status_code == 200
    assert system_state.json() == short_state.json() == admin_state.json()


def test_state_summary_matches_detailed_counts() -> None:
    _reset_state()
    swipe_response = client.post(
        "/portal/swipe",
        json={
            "contact_id": "lead_001",
            "property_id": "prop_001",
            "action": "like",
        },
    )
    assert swipe_response.status_code == 200

    booking_response = client.post(
        "/vapi/tools/book-tour",
        json={
            "toolCall": {
                "id": "tool-parity-1",
                "function": {
                    "arguments": {
                        "contact_id": "lead_001",
                        "slot_time": "2026-02-15T10:00:00",
                        "property_address": "123 Palm Ave",
                    },
                },
            }
        },
    )
    assert booking_response.status_code == 200

    state_response = client.get("/system/state")
    details_response = client.get("/system/state/details", params={"limit": 100})
    assert state_response.status_code == 200
    assert details_response.status_code == 200

    state = state_response.json()["state"]
    details = details_response.json()["details"]
    assert details["inventory"]["lead_count"] == state["inventory_leads"]
    assert details["inventory"]["property_count"] == state["inventory_properties"]
    assert details["inventory"]["interaction_count"] == state["inventory_interactions"]
    assert details["ghl"]["action_count"] == state["ghl_actions"]
    assert details["appointment"]["booking_count"] == state["appointments"]


def test_system_state_details_endpoint_tracks_recent_activity() -> None:
    _reset_state()
    baseline_response = client.get("/system/state/details")
    assert baseline_response.status_code == 200
    baseline_details = baseline_response.json()["details"]
    assert baseline_details["inventory"]["interaction_count"] == 0
    assert baseline_details["ghl"]["action_count"] == 0
    assert baseline_details["appointment"]["booking_count"] == 0
    assert baseline_details["inventory"]["recent_interactions"] == []
    assert baseline_details["ghl"]["recent_actions"] == []
    assert baseline_details["appointment"]["recent_bookings"] == []

    swipe_response = client.post(
        "/portal/swipe",
        json={
            "contact_id": "lead_001",
            "property_id": "prop_001",
            "action": "like",
        },
    )
    assert swipe_response.status_code == 200

    booking_response = client.post(
        "/vapi/tools/book-tour",
        json={
            "toolCall": {
                "id": "tool-4",
                "function": {
                    "arguments": {
                        "contact_id": "lead_001",
                        "slot_time": "2026-02-15T10:00:00",
                        "property_address": "123 Palm Ave",
                    },
                },
            }
        },
    )
    assert booking_response.status_code == 200

    details_response = client.get("/system/state/details", params={"limit": 2})
    assert details_response.status_code == 200
    details_payload = details_response.json()["details"]
    assert details_payload["inventory"]["interaction_count"] == 1
    assert details_payload["ghl"]["action_count"] == 3
    assert details_payload["appointment"]["booking_count"] == 1
    assert len(details_payload["inventory"]["recent_interactions"]) == 1
    assert len(details_payload["ghl"]["recent_actions"]) == 2
    assert len(details_payload["appointment"]["recent_bookings"]) == 1

    interaction = details_payload["inventory"]["recent_interactions"][0]
    assert interaction["lead_id"] == "lead_001"
    assert interaction["property_id"] == "prop_001"
    assert interaction["action"] == "like"
    assert "timestamp" in interaction

    booking = details_payload["appointment"]["recent_bookings"][0]
    assert booking["contact_id"] == "lead_001"
    assert booking["property_address"] == "123 Palm Ave"

    reset_response = client.post("/system/reset")
    assert reset_response.status_code == 200

    after_reset_details = client.get("/system/state/details")
    assert after_reset_details.status_code == 200
    after_reset_payload = after_reset_details.json()["details"]
    assert after_reset_payload["inventory"]["interaction_count"] == 0
    assert after_reset_payload["ghl"]["action_count"] == 0
    assert after_reset_payload["appointment"]["booking_count"] == 0
    assert after_reset_payload["inventory"]["recent_interactions"] == []
    assert after_reset_payload["ghl"]["recent_actions"] == []
    assert after_reset_payload["appointment"]["recent_bookings"] == []


def test_state_details_aliases_match() -> None:
    _reset_state()
    system_details = client.get("/system/state/details")
    short_details = client.get("/state/details")
    admin_details = client.get("/admin/state/details")
    assert system_details.status_code == 200
    assert short_details.status_code == 200
    assert admin_details.status_code == 200
    assert system_details.json() == short_details.json() == admin_details.json()


def test_state_details_limit_zero_keeps_counts_and_hides_recent_entries() -> None:
    _reset_state()
    swipe_response = client.post(
        "/portal/swipe",
        json={
            "contact_id": "lead_001",
            "property_id": "prop_001",
            "action": "like",
        },
    )
    assert swipe_response.status_code == 200

    details_response = client.get("/system/state/details", params={"limit": 0})
    assert details_response.status_code == 200
    details_payload = details_response.json()["details"]
    assert details_payload["inventory"]["interaction_count"] == 1
    assert details_payload["ghl"]["action_count"] == 3
    assert details_payload["inventory"]["recent_interactions"] == []
    assert details_payload["ghl"]["recent_actions"] == []
    assert details_payload["appointment"]["recent_bookings"] == []


def test_state_details_rejects_invalid_limit_values() -> None:
    _reset_state()
    above_max_limit = client.get("/system/state/details", params={"limit": 101})
    assert above_max_limit.status_code == 422
    assert any(error["loc"][-1] == "limit" for error in above_max_limit.json().get("detail", []))

    negative_limit = client.get("/system/state/details", params={"limit": -1})
    assert negative_limit.status_code == 422
    assert any(error["loc"][-1] == "limit" for error in negative_limit.json().get("detail", []))

    non_integer_limit = client.get("/system/state/details", params={"limit": "abc"})
    assert non_integer_limit.status_code == 422
    assert any(error["loc"][-1] == "limit" for error in non_integer_limit.json().get("detail", []))


def test_swipe_rejects_invalid_action() -> None:
    _reset_state()
    response = client.post(
        "/portal/swipe",
        json={
            "contact_id": "lead_001",
            "property_id": "prop_001",
            "action": "save",
        },
    )
    assert response.status_code == 422
    _assert_request_id_header(response)
    payload = response.json()
    assert any(error["loc"][-1] == "action" for error in payload.get("detail", []))


def test_swipe_pass_does_not_trigger_high_intent_or_ghl_actions() -> None:
    _reset_state()
    response = client.post(
        "/portal/swipe",
        json={
            "contact_id": "lead_001",
            "property_id": "prop_001",
            "action": "pass",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["high_intent"] is False
    assert payload["trigger_sms"] is False
    assert payload["adjustments"] == []

    state_response = client.get("/system/state")
    assert state_response.status_code == 200
    state = state_response.json()["state"]
    assert state["inventory_interactions"] == 1
    assert state["ghl_actions"] == 0
    assert state["appointments"] == 0


def test_vapi_tool_endpoints() -> None:
    _reset_state()
    availability = client.post(
        "/vapi/tools/check-availability",
        json={
            "toolCall": {
                "id": "tool-1",
                "function": {
                    "arguments": {"date": "2026-02-15"},
                },
            }
        },
    )
    assert availability.status_code == 200
    avail_payload = availability.json()
    assert isinstance(avail_payload.get("results"), list)
    assert avail_payload["results"][0]["toolCallId"] == "tool-1"

    booking = client.post(
        "/vapi/tools/book-tour",
        json={
            "toolCall": {
                "id": "tool-2",
                "function": {
                    "arguments": {
                        "contact_id": "lead_001",
                        "slot_time": "2026-02-15T10:00:00",
                        "property_address": "123 Palm Ave",
                    },
                },
            }
        },
    )
    assert booking.status_code == 200
    book_payload = booking.json()
    assert isinstance(book_payload.get("results"), list)
    assert book_payload["results"][0]["toolCallId"] == "tool-2"


def test_vapi_tool_endpoints_accept_stringified_arguments() -> None:
    _reset_state()
    availability = client.post(
        "/vapi/tools/check-availability",
        json={
            "toolCall": {
                "id": "tool-string-1",
                "function": {
                    "arguments": '{"date":"2026-02-15"}',
                },
            }
        },
    )
    assert availability.status_code == 200
    avail_payload = availability.json()
    assert avail_payload["results"][0]["toolCallId"] == "tool-string-1"
    avail_result = json.loads(avail_payload["results"][0]["result"])
    assert avail_result["status"] == "success"
    assert isinstance(avail_result["slots"], list)

    booking = client.post(
        "/vapi/tools/book-tour",
        json={
            "toolCall": {
                "id": "tool-string-2",
                "function": {
                    "arguments": (
                        '{"contact_id":"lead_001","slot_time":"2026-02-15T10:00:00","property_address":"123 Palm Ave"}'
                    ),
                },
            }
        },
    )
    assert booking.status_code == 200
    booking_payload = booking.json()
    assert booking_payload["results"][0]["toolCallId"] == "tool-string-2"
    booking_result = json.loads(booking_payload["results"][0]["result"])
    assert booking_result["status"] == "success"
    assert booking_result["booking"]["contact_id"] == "lead_001"


def test_vapi_tool_endpoints_handle_malformed_string_arguments() -> None:
    _reset_state()
    availability = client.post(
        "/vapi/tools/check-availability",
        json={
            "toolCall": {
                "id": "tool-malformed-1",
                "function": {
                    "arguments": "{not-valid-json",
                },
            }
        },
    )
    assert availability.status_code == 200
    avail_payload = availability.json()
    assert avail_payload["results"][0]["toolCallId"] == "tool-malformed-1"
    avail_result = json.loads(avail_payload["results"][0]["result"])
    assert avail_result["status"] == "success"
    assert isinstance(avail_result["slots"], list)

    booking = client.post(
        "/vapi/tools/book-tour",
        json={
            "toolCall": {
                "id": "tool-malformed-2",
                "function": {
                    "arguments": "{not-valid-json",
                },
            }
        },
    )
    assert booking.status_code == 200
    booking_payload = booking.json()
    assert booking_payload["results"][0]["toolCallId"] == "tool-malformed-2"
    booking_result = json.loads(booking_payload["results"][0]["result"])
    assert booking_result["status"] == "error"
    assert booking_result["message"] == "contact_id is required"


def test_vapi_book_tour_defaults_when_tool_call_missing() -> None:
    _reset_state()
    response = client.post("/vapi/tools/book-tour", json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["results"][0]["toolCallId"] is None
    result = json.loads(payload["results"][0]["result"])
    assert result["status"] == "error"
    assert result["message"] == "contact_id is required"


def test_ghl_endpoints_return_expected_shapes() -> None:
    _reset_state()
    sync_response = client.post("/ghl/sync")
    assert sync_response.status_code == 200
    sync_payload = sync_response.json()
    assert sync_payload["status"] == "success"
    assert isinstance(sync_payload["synced_count"], int)

    fields_response = client.get("/ghl/fields")
    assert fields_response.status_code == 200
    fields_payload = fields_response.json()
    assert "fields" in fields_payload or "message" in fields_payload


def test_ghl_sync_returns_500_on_service_exception(monkeypatch) -> None:
    _reset_state()
    services = get_services()

    def _raise_sync_error() -> int:
        raise RuntimeError("upstream provider timeout")

    monkeypatch.setattr(services.ghl, "sync_contacts_from_ghl", _raise_sync_error)

    response = client.post("/ghl/sync")
    assert response.status_code == 500
    _assert_request_id_header(response)
    payload = response.json()
    assert payload["error"]["code"] == "ghl_sync_failed"
    assert payload["error"]["message"] == "GoHighLevel sync failed"
    assert payload["error"]["request_id"] == response.headers["X-Request-ID"]
    assert "upstream provider timeout" not in json.dumps(payload)


def test_demo_api_key_guard_disabled_when_env_unset(monkeypatch) -> None:
    _reset_state()
    monkeypatch.delenv("PORTAL_API_DEMO_KEY", raising=False)

    response = client.post(
        "/portal/swipe",
        json={
            "contact_id": "lead_001",
            "property_id": "prop_001",
            "action": "like",
        },
    )
    assert response.status_code == 200
    _assert_request_id_header(response)


def test_demo_api_key_guard_enforced_when_env_set(monkeypatch) -> None:
    _reset_state()
    monkeypatch.setenv("PORTAL_API_DEMO_KEY", "demo-secret")

    unauthorized = client.post(
        "/portal/swipe",
        json={
            "contact_id": "lead_001",
            "property_id": "prop_001",
            "action": "like",
        },
    )
    assert unauthorized.status_code == 401
    _assert_request_id_header(unauthorized)
    unauthorized_payload = unauthorized.json()
    assert unauthorized_payload["error"]["code"] == "unauthorized"
    assert unauthorized_payload["error"]["message"] == "Invalid API key"
    assert unauthorized_payload["error"]["request_id"] == unauthorized.headers["X-Request-ID"]

    authorized = client.post(
        "/portal/swipe",
        headers={"X-API-Key": "demo-secret"},
        json={
            "contact_id": "lead_001",
            "property_id": "prop_001",
            "action": "like",
        },
    )
    assert authorized.status_code == 200
    _assert_request_id_header(authorized)


def test_demo_api_key_guard_protects_reset_and_allows_valid_key(monkeypatch) -> None:
    _reset_state()
    monkeypatch.setenv("PORTAL_API_DEMO_KEY", "demo-secret")

    unauthorized = client.post("/system/reset")
    assert unauthorized.status_code == 401
    assert unauthorized.json()["error"]["code"] == "unauthorized"

    authorized = client.post("/system/reset", headers={"X-API-Key": "demo-secret"})
    assert authorized.status_code == 200
    _assert_request_id_header(authorized)
