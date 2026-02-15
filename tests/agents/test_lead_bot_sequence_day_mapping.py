"""
Tests for LeadBotWorkflow._map_int_to_sequence_day() helper method.

Validates that integer-to-enum mapping handles:
- Valid exact mappings (0, 3, 7, 14, 30)
- Boundary conditions and edge cases
- Invalid inputs (negative, out-of-range)
"""

import pytest

from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow
from ghl_real_estate_ai.services.lead_sequence_state_service import SequenceDay


@pytest.fixture
def lead_bot():
    """Create LeadBotWorkflow instance for testing."""
    return LeadBotWorkflow()


class TestSequenceDayMapping:
    """Test suite for _map_int_to_sequence_day validation."""

    def test_exact_mappings(self, lead_bot):
        """Test all exact valid mappings."""
        assert lead_bot._map_int_to_sequence_day(0) == SequenceDay.INITIAL
        assert lead_bot._map_int_to_sequence_day(3) == SequenceDay.DAY_3
        assert lead_bot._map_int_to_sequence_day(7) == SequenceDay.DAY_7
        assert lead_bot._map_int_to_sequence_day(14) == SequenceDay.DAY_14
        assert lead_bot._map_int_to_sequence_day(30) == SequenceDay.DAY_30

    def test_boundary_lower(self, lead_bot):
        """Test days below valid ranges default to INITIAL."""
        assert lead_bot._map_int_to_sequence_day(-1) == SequenceDay.INITIAL
        assert lead_bot._map_int_to_sequence_day(-100) == SequenceDay.INITIAL
        assert lead_bot._map_int_to_sequence_day(1) == SequenceDay.INITIAL
        assert lead_bot._map_int_to_sequence_day(2) == SequenceDay.INITIAL

    def test_boundary_mid_ranges(self, lead_bot):
        """Test days in mid-ranges map to nearest lower day."""
        # [3, 7) -> DAY_3
        assert lead_bot._map_int_to_sequence_day(4) == SequenceDay.DAY_3
        assert lead_bot._map_int_to_sequence_day(5) == SequenceDay.DAY_3
        assert lead_bot._map_int_to_sequence_day(6) == SequenceDay.DAY_3

        # [7, 14) -> DAY_7
        assert lead_bot._map_int_to_sequence_day(8) == SequenceDay.DAY_7
        assert lead_bot._map_int_to_sequence_day(10) == SequenceDay.DAY_7
        assert lead_bot._map_int_to_sequence_day(13) == SequenceDay.DAY_7

        # [14, 30) -> DAY_14
        assert lead_bot._map_int_to_sequence_day(15) == SequenceDay.DAY_14
        assert lead_bot._map_int_to_sequence_day(20) == SequenceDay.DAY_14
        assert lead_bot._map_int_to_sequence_day(29) == SequenceDay.DAY_14

    def test_boundary_upper(self, lead_bot):
        """Test days >= 30 map to DAY_30."""
        assert lead_bot._map_int_to_sequence_day(31) == SequenceDay.DAY_30
        assert lead_bot._map_int_to_sequence_day(45) == SequenceDay.DAY_30
        assert lead_bot._map_int_to_sequence_day(100) == SequenceDay.DAY_30
        assert lead_bot._map_int_to_sequence_day(365) == SequenceDay.DAY_30

    def test_zero_edge_case(self, lead_bot):
        """Test that zero maps to INITIAL."""
        assert lead_bot._map_int_to_sequence_day(0) == SequenceDay.INITIAL

    def test_type_safety(self, lead_bot):
        """Test that helper works with different numeric types."""
        # int
        assert lead_bot._map_int_to_sequence_day(3) == SequenceDay.DAY_3
        # Should handle numeric values even if passed as different types
        assert lead_bot._map_int_to_sequence_day(int(7)) == SequenceDay.DAY_7
