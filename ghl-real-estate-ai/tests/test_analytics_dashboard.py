"""
Tests for Analytics Dashboard

Validates dashboard load performance, data processing, and visualization rendering.
"""
import pytest
import json
import time
from pathlib import Path
from datetime import datetime, timedelta

# Import dashboard functions (since we can't run streamlit directly in tests)
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "streamlit_demo"))

from analytics import (
    load_mock_data,
    filter_conversations_by_date,
    calculate_aggregate_metrics,
    create_lead_score_distribution_chart,
    create_classification_pie_chart,
    create_conversation_timeline,
    create_response_time_chart,
    create_intent_breakdown
)


class TestDataLoading:
    """Test data loading functionality."""

    def test_load_mock_data_exists(self):
        """Test that mock data file exists and loads correctly."""
        data = load_mock_data()

        assert "tenants" in data
        assert "conversations" in data
        assert "system_health" in data

        assert len(data["tenants"]) == 3
        assert len(data["conversations"]) >= 50

    def test_load_mock_data_performance(self):
        """Test that data loads in under 1 second."""
        start_time = time.time()
        data = load_mock_data()
        end_time = time.time()

        load_time = end_time - start_time
        assert load_time < 1.0, f"Data loading took {load_time:.2f}s, should be < 1s"

    def test_tenant_structure(self):
        """Test tenant data structure."""
        data = load_mock_data()
        tenants = data["tenants"]

        for tenant in tenants:
            assert "location_id" in tenant
            assert "name" in tenant
            assert "created_at" in tenant
            assert "tier" in tenant
            assert "region" in tenant

    def test_conversation_structure(self):
        """Test conversation data structure."""
        data = load_mock_data()
        conversations = data["conversations"]

        required_fields = [
            "conversation_id", "location_id", "contact_id", "contact_name",
            "start_time", "message_count", "lead_score", "classification",
            "intent", "response_time_avg_seconds", "sentiment", "conversion_probability"
        ]

        for conv in conversations:
            for field in required_fields:
                assert field in conv, f"Missing field: {field}"

    def test_system_health_structure(self):
        """Test system health data structure."""
        data = load_mock_data()
        health = data["system_health"]

        required_metrics = [
            "total_api_calls_24h", "avg_response_time_ms", "uptime_percentage",
            "error_rate_percentage", "sms_sent_24h", "sms_compliance_rate"
        ]

        for metric in required_metrics:
            assert metric in health, f"Missing metric: {metric}"


class TestDataFiltering:
    """Test data filtering and processing."""

    def test_filter_conversations_by_date(self):
        """Test date range filtering."""
        from datetime import timezone
        data = load_mock_data()
        conversations = data["conversations"]

        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=7)

        filtered = filter_conversations_by_date(conversations, start_date, end_date)

        for conv in filtered:
            conv_date = datetime.fromisoformat(conv["start_time"].replace("Z", "+00:00"))
            assert start_date <= conv_date <= end_date

    def test_filter_by_tenant(self):
        """Test filtering by tenant."""
        data = load_mock_data()
        conversations = data["conversations"]
        tenant_id = data["tenants"][0]["location_id"]

        tenant_convs = [c for c in conversations if c["location_id"] == tenant_id]

        assert len(tenant_convs) > 0
        for conv in tenant_convs:
            assert conv["location_id"] == tenant_id

    def test_filter_by_classification(self):
        """Test filtering by lead classification."""
        data = load_mock_data()
        conversations = data["conversations"]

        hot_leads = [c for c in conversations if c["classification"] == "hot"]
        warm_leads = [c for c in conversations if c["classification"] == "warm"]
        cold_leads = [c for c in conversations if c["classification"] == "cold"]

        assert len(hot_leads) > 0
        assert len(warm_leads) > 0
        assert len(cold_leads) > 0

        total = len(hot_leads) + len(warm_leads) + len(cold_leads)
        assert total == len(conversations)


class TestMetricsCalculation:
    """Test metrics calculation functions."""

    def test_calculate_aggregate_metrics(self):
        """Test aggregate metrics calculation."""
        data = load_mock_data()
        conversations = data["conversations"]

        metrics = calculate_aggregate_metrics(conversations)

        assert metrics["total_conversations"] == len(conversations)
        assert metrics["total_messages"] > 0
        assert 0 <= metrics["avg_lead_score"] <= 100
        assert metrics["hot_leads"] >= 0
        assert metrics["warm_leads"] >= 0
        assert metrics["cold_leads"] >= 0
        assert metrics["total_contacts"] > 0
        assert metrics["avg_response_time"] > 0
        assert 0 <= metrics["conversion_rate"] <= 1

    def test_metrics_empty_conversations(self):
        """Test metrics calculation with empty conversation list."""
        metrics = calculate_aggregate_metrics([])

        assert metrics["total_conversations"] == 0
        assert metrics["total_messages"] == 0
        assert metrics["avg_lead_score"] == 0
        assert metrics["hot_leads"] == 0

    def test_metrics_accuracy(self):
        """Test metrics calculation accuracy with known data."""
        test_conversations = [
            {
                "message_count": 10,
                "lead_score": 90,
                "classification": "hot",
                "contact_id": "c1",
                "response_time_avg_seconds": 10,
                "conversion_probability": 0.9
            },
            {
                "message_count": 5,
                "lead_score": 50,
                "classification": "warm",
                "contact_id": "c2",
                "response_time_avg_seconds": 20,
                "conversion_probability": 0.5
            }
        ]

        metrics = calculate_aggregate_metrics(test_conversations)

        assert metrics["total_conversations"] == 2
        assert metrics["total_messages"] == 15
        assert metrics["avg_lead_score"] == 70  # (90 + 50) / 2
        assert metrics["hot_leads"] == 1
        assert metrics["warm_leads"] == 1
        assert metrics["total_contacts"] == 2
        assert metrics["avg_response_time"] == 15  # (10 + 20) / 2
        assert metrics["conversion_rate"] == 0.7  # (0.9 + 0.5) / 2


class TestChartGeneration:
    """Test chart generation functions."""

    def test_lead_score_distribution_chart(self):
        """Test lead score distribution chart generation."""
        data = load_mock_data()
        conversations = data["conversations"]

        chart = create_lead_score_distribution_chart(conversations)

        assert chart is not None
        assert chart.data is not None
        assert len(chart.data) > 0

    def test_classification_pie_chart(self):
        """Test classification pie chart generation."""
        data = load_mock_data()
        conversations = data["conversations"]

        chart = create_classification_pie_chart(conversations)

        assert chart is not None
        assert chart.data is not None
        assert len(chart.data) > 0

    def test_conversation_timeline_chart(self):
        """Test conversation timeline chart generation."""
        data = load_mock_data()
        conversations = data["conversations"]

        chart = create_conversation_timeline(conversations)

        assert chart is not None
        assert chart.data is not None

    def test_response_time_chart(self):
        """Test response time chart generation."""
        data = load_mock_data()
        conversations = data["conversations"]

        chart = create_response_time_chart(conversations)

        assert chart is not None
        assert chart.data is not None
        assert len(chart.data) > 0

    def test_intent_breakdown_chart(self):
        """Test intent breakdown chart generation."""
        data = load_mock_data()
        conversations = data["conversations"]

        chart = create_intent_breakdown(conversations)

        assert chart is not None
        assert chart.data is not None
        assert len(chart.data) > 0

    def test_chart_generation_performance(self):
        """Test that all charts generate in under 2 seconds total."""
        data = load_mock_data()
        conversations = data["conversations"]

        start_time = time.time()

        create_lead_score_distribution_chart(conversations)
        create_classification_pie_chart(conversations)
        create_conversation_timeline(conversations)
        create_response_time_chart(conversations)
        create_intent_breakdown(conversations)

        end_time = time.time()
        total_time = end_time - start_time

        assert total_time < 2.0, f"Chart generation took {total_time:.2f}s, should be < 2s"


class TestDashboardPerformance:
    """Test overall dashboard performance."""

    def test_full_dashboard_load_time(self):
        """Test that full dashboard data processing is under 3 seconds."""
        start_time = time.time()

        # Simulate full dashboard load
        data = load_mock_data()
        conversations = data["conversations"]

        # Calculate all metrics
        calculate_aggregate_metrics(conversations)

        # Generate all charts
        create_lead_score_distribution_chart(conversations)
        create_classification_pie_chart(conversations)
        create_conversation_timeline(conversations)
        create_response_time_chart(conversations)
        create_intent_breakdown(conversations)

        # Process tenant data
        tenants = data["tenants"]
        for tenant in tenants:
            tenant_convs = [c for c in conversations if c["location_id"] == tenant["location_id"]]
            calculate_aggregate_metrics(tenant_convs)

        end_time = time.time()
        load_time = end_time - start_time

        assert load_time < 3.0, f"Full dashboard load took {load_time:.2f}s, should be < 3s"

    def test_data_consistency(self):
        """Test data consistency across multiple loads."""
        data1 = load_mock_data()
        data2 = load_mock_data()

        assert len(data1["tenants"]) == len(data2["tenants"])
        assert len(data1["conversations"]) == len(data2["conversations"])


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_date_range(self):
        """Test filtering with no matching dates."""
        from datetime import timezone
        data = load_mock_data()
        conversations = data["conversations"]

        future_start = datetime.now(timezone.utc) + timedelta(days=365)
        future_end = future_start + timedelta(days=7)

        filtered = filter_conversations_by_date(conversations, future_start, future_end)

        assert len(filtered) == 0

        # Should still calculate metrics without errors
        metrics = calculate_aggregate_metrics(filtered)
        assert metrics["total_conversations"] == 0

    def test_single_tenant_filtering(self):
        """Test analytics for a single tenant."""
        data = load_mock_data()
        tenant = data["tenants"][0]
        conversations = [c for c in data["conversations"] if c["location_id"] == tenant["location_id"]]

        assert len(conversations) > 0

        metrics = calculate_aggregate_metrics(conversations)
        assert metrics["total_conversations"] > 0

    def test_all_classifications_present(self):
        """Test that all three classifications are represented in mock data."""
        data = load_mock_data()
        conversations = data["conversations"]

        classifications = set(c["classification"] for c in conversations)

        assert "hot" in classifications
        assert "warm" in classifications
        assert "cold" in classifications


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
