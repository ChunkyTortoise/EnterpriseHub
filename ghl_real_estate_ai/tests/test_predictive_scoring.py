"""
Tests for Predictive Lead Scoring Service
"""

from datetime import datetime

import pytest

from ghl_real_estate_ai.services.predictive_scoring import BatchPredictor, PredictiveLeadScorer


class TestPredictiveLeadScorer:
    def test_predict_conversion_hot_lead(self):
        scorer = PredictiveLeadScorer()

        # Simulate a very hot lead
        contact_data = {
            "contact_id": "hot_123",
            "lead_score": 85,
            "previous_contacts": 1,
            "location_fit": 0.9,
            "messages": [
                {"text": "I am pre-approved for $500k cash.", "response_time_seconds": 30},
                {"text": "I need to move in the next 2 weeks to Rancho Cucamonga.", "response_time_seconds": 45},
                {"text": "Is the 3 bedroom house available?", "response_time_seconds": 60},
            ],
        }

        prediction = scorer.predict_conversion(contact_data)

        assert prediction["contact_id"] == "hot_123"
        assert prediction["conversion_probability"] > 70
        assert prediction["confidence"] == "high"
        assert any("Pre-approved" in r for r in prediction["reasoning"])
        assert any("HIGH PRIORITY" in r["title"] for r in prediction["recommendations"])

    def test_predict_conversion_cold_lead(self):
        scorer = PredictiveLeadScorer()

        # Simulate a cold lead
        contact_data = {
            "contact_id": "cold_456",
            "lead_score": 20,
            "messages": [{"text": "Just looking around.", "response_time_seconds": 600}],
        }

        prediction = scorer.predict_conversion(contact_data)

        assert prediction["conversion_probability"] < 40
        assert any("Nurture campaign" in r["title"] for r in prediction["recommendations"])


class TestBatchPredictor:
    def test_predict_batch(self):
        predictor = BatchPredictor()
        contacts = [
            {"contact_id": "c1", "lead_score": 20, "messages": []},
            {
                "contact_id": "c2",
                "lead_score": 90,
                "messages": [{"text": "approved cash", "response_time_seconds": 10}],
            },
        ]

        batch = predictor.predict_batch(contacts)
        assert len(batch) == 2
        # Should be sorted by probability
        assert batch[0]["contact_id"] == "c2"
        assert batch[1]["contact_id"] == "c1"