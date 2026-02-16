"""Tests for /api/v1/alerts endpoints."""


class TestAlertsAPI:
    def test_create_alert_rule(self, client):
        payload = {
            "name": "High Latency",
            "metric_name": "latency",
            "condition": "gt",
            "threshold": 100.0,
            "cooldown_seconds": 300,
        }
        response = client.post("/api/v1/alerts", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "High Latency"
        assert data["metric_name"] == "latency"
        assert "id" in data

    def test_list_alert_rules(self, client):
        # Create a rule
        payload = {"name": "Test", "metric_name": "latency", "condition": "gt", "threshold": 50.0}
        create_resp = client.post("/api/v1/alerts", json=payload)
        rule_id = create_resp.json()["id"]

        response = client.get("/api/v1/alerts")
        assert response.status_code == 200
        rules = response.json()
        assert any(r["id"] == rule_id for r in rules)

        # Cleanup
        client.delete(f"/api/v1/alerts/{rule_id}")

    def test_get_alert_rule(self, client):
        # Create a rule
        payload = {"name": "Test", "metric_name": "cost", "condition": "gt", "threshold": 1.0}
        create_resp = client.post("/api/v1/alerts", json=payload)
        rule_id = create_resp.json()["id"]

        response = client.get(f"/api/v1/alerts/{rule_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == rule_id
        assert data["name"] == "Test"

        # Cleanup
        client.delete(f"/api/v1/alerts/{rule_id}")

    def test_get_nonexistent_alert_rule(self, client):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/v1/alerts/{fake_id}")
        assert response.status_code == 404

    def test_delete_alert_rule(self, client):
        # Create a rule
        payload = {"name": "Test", "metric_name": "latency", "condition": "gt", "threshold": 50.0}
        create_resp = client.post("/api/v1/alerts", json=payload)
        rule_id = create_resp.json()["id"]

        # Delete it
        response = client.delete(f"/api/v1/alerts/{rule_id}")
        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify deletion
        get_resp = client.get(f"/api/v1/alerts/{rule_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_alert_rule(self, client):
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(f"/api/v1/alerts/{fake_id}")
        assert response.status_code == 404
