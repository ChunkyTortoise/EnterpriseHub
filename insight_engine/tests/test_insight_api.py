"""Tests for the Insight Engine REST API."""
import pytest
from fastapi.testclient import TestClient
from insight_engine.api.app import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_render_metric_default():
    resp = client.post("/render/metric", json={
        "value": "$2.4M",
        "label": "Revenue",
        "variant": "default",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "$2.4M" in data["html"]
    assert "Revenue" in data["html"]
    assert data["component_type"] == "metric"


def test_render_metric_with_trend():
    resp = client.post("/render/metric", json={
        "value": "15",
        "label": "Hot Leads",
        "variant": "success",
        "trend": "up",
        "comparison_value": "+3 vs last week",
    })
    assert resp.status_code == 200
    assert "+3 vs last week" in resp.json()["html"]


def test_render_metric_invalid_variant():
    resp = client.post("/render/metric", json={
        "value": "5",
        "label": "Test",
        "variant": "invalid_variant",
    })
    assert resp.status_code == 422  # Pydantic validation error


def test_render_card_default():
    resp = client.post("/render/card", json={
        "title": "Hot Leads",
        "content": "15 leads need attention",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "Hot Leads" in data["html"]
    assert data["component_type"] == "card"


def test_render_card_with_glow():
    resp = client.post("/render/card", json={
        "title": "Alert",
        "content": "System warning",
        "variant": "alert",
        "glow_color": "#EF4444",
    })
    assert resp.status_code == 200
    assert "#EF4444" in resp.json()["html"]


def test_get_theme():
    resp = client.get("/theme")
    assert resp.status_code == 200
    # Should return CSS text
    assert "--bg-primary" in resp.text or "bg-primary" in resp.text or "0d1117" in resp.text


def test_dashboard_generation():
    resp = client.post("/dashboard", json={
        "title": "Test Dashboard",
        "metrics": [
            {"value": "$1M", "label": "Revenue", "variant": "success"},
            {"value": "42", "label": "Leads", "variant": "default"},
        ],
        "cards": [
            {"title": "Status", "content": "All systems operational", "variant": "success"},
        ],
    })
    assert resp.status_code == 200
    html = resp.text
    assert "Test Dashboard" in html
    assert "$1M" in html
    assert "Revenue" in html
    assert "All systems operational" in html


def test_dashboard_empty():
    resp = client.post("/dashboard", json={
        "title": "Empty Dashboard",
        "metrics": [],
        "cards": [],
    })
    assert resp.status_code == 200
    assert "Empty Dashboard" in resp.text


def test_dashboard_stream_response_type():
    resp = client.post("/dashboard/stream", json={
        "title": "Streaming Test",
        "metrics": [{"value": "42", "label": "Test", "variant": "default"}],
        "cards": [],
    })
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")


def test_dashboard_stream_contains_events():
    resp = client.post("/dashboard/stream", json={
        "title": "Stream Dashboard",
        "metrics": [{"value": "$1M", "label": "Revenue", "variant": "success"}],
        "cards": [{"title": "Status", "content": "OK", "variant": "default"}],
    })
    content = resp.text
    assert "start" in content
    assert "complete" in content
    assert "$1M" in content
