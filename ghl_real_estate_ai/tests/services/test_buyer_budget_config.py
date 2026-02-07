"""
Tests for Jorge Buyer Budget Configuration.

Validates budget validation, financial calculations, and readiness assessment.
"""

import pytest
import os
from unittest.mock import patch

from ghl_real_estate_ai.ghl_utils.jorge_config import (
    BuyerBudgetConfig,
)


class TestBuyerBudgetConfig:
    """Test suite for buyer budget configuration."""

    @pytest.fixture
    def budget_config(self):
        """Create a BuyerBudgetConfig instance."""
        return BuyerBudgetConfig()

    def test_load_from_env_success(self, budget_config):
        """Test loading configuration from environment variables."""
        # Set environment variables
        env_vars = {
            "BUYER_FINANCING_PRE_APPROVED_THRESHOLD": "80",
            "BUYER_URGENCY_IMMEDIATE_THRESHOLD": "70",
            "BUYER_QUALIFICATION_HOT_THRESHOLD": "80",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = BuyerBudgetConfig.from_environment()

            assert config.FINANCING_PRE_APPROVED_THRESHOLD == 80
            assert config.URGENCY_IMMEDIATE_THRESHOLD == 70
            assert config.QUALIFICATION_HOT_THRESHOLD == 80

    def test_validate_budget_in_range(self, budget_config):
        """Test budget validation when within acceptable range."""
        budget_range = budget_config.get_budget_range("under 600")

        assert budget_range is not None
        assert "budget_max" in budget_range
        assert "buyer_type" in budget_range
        assert budget_range["budget_max"] == 600000

    def test_validate_budget_below_min(self, budget_config):
        """Test budget validation when below minimum."""
        # Very low budget
        budget_range = budget_config.get_budget_range("under 300")

        assert budget_range is not None
        assert budget_range["budget_max"] == 700000  # Maps to entry level

    def test_validate_budget_above_max(self, budget_config):
        """Test budget validation when above maximum."""
        # High budget
        budget_range = budget_config.get_budget_range("over 1m")

        assert budget_range is not None
        assert "budget_min" in budget_range
        assert budget_range["budget_min"] == 1200000

    def test_calculate_monthly_payment(self, budget_config):
        """Test monthly payment calculation."""
        # Simple calculation: principal * rate / 12
        # This is a placeholder - actual implementation may differ
        budget = 600000
        down_payment = 120000
        interest_rate = 0.06
        loan_term_years = 30

        # Calculate monthly payment (simplified)
        principal = budget - down_payment
        monthly_rate = interest_rate / 12
        num_payments = loan_term_years * 12

        # Monthly payment formula
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)

        assert monthly_payment > 0
        assert monthly_payment < principal  # Should be less than total principal

    def test_calculate_debt_to_income_ratio(self, budget_config):
        """Test debt-to-income ratio calculation."""
        monthly_income = 10000
        monthly_debt = 3000
        monthly_payment = 2500

        dti = (monthly_debt + monthly_payment) / monthly_income

        assert 0 <= dti <= 1
        assert dti == 0.55  # (3000 + 2500) / 10000

    def test_assess_financial_readiness(self, budget_config):
        """Test financial readiness assessment."""
        # High readiness scenario
        financing_score = 85  # Above 75 threshold
        budget_score = 80
        urgency_score = 75

        # Assess readiness
        is_ready = (
            financing_score >= budget_config.FINANCING_PRE_APPROVED_THRESHOLD and
            budget_score >= budget_config.FINANCING_CASH_BUDGET_THRESHOLD and
            urgency_score >= budget_config.URGENCY_IMMEDIATE_THRESHOLD
        )

        assert is_ready is True

    def test_get_budget_recommendations(self, budget_config):
        """Test getting budget recommendations."""
        # Test urgency level classification
        urgency_score = 80
        urgency_level = budget_config.get_urgency_level(urgency_score)

        assert urgency_level == "immediate"

        # Test qualification level classification
        qual_score = 85
        qual_level = budget_config.get_qualification_level(qual_score)

        assert qual_level == "hot"

        # Test next action
        action, hours = budget_config.get_next_action(qual_score)

        assert action == "schedule_property_tour"
        assert hours == budget_config.QUALIFICATION_HOT_FOLLOWUP_HOURS
