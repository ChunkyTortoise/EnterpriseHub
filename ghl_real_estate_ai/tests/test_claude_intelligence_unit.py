"""
Unit Tests for Claude Lead Intelligence - Infrastructure Independent

Simple unit tests that validate the core Claude intelligence logic
without requiring Redis, databases, or external API connections.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List


@pytest.mark.asyncio
async def test_claude_semantic_analyzer_factory():
    """Test that we can create a semantic analyzer with mock API key."""

    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        from ghl_real_estate_ai.services.claude_semantic_analyzer import create_claude_analyzer

        analyzer = create_claude_analyzer(api_key="test-key")
        assert analyzer is not None
        assert analyzer.api_key == "test-key"
        assert analyzer.model == "claude-3-5-sonnet-20241022"

        # Clean up
        await analyzer.close()


@pytest.mark.asyncio
async def test_semantic_analysis_response_parsing():
    """Test response parsing logic."""

    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        from ghl_real_estate_ai.services.claude_semantic_analyzer import create_claude_analyzer

        analyzer = create_claude_analyzer(api_key="test-key")

        # Test valid JSON response
        test_response = '{"intent": "researching", "confidence": 0.85, "urgency": "medium"}'
        parsed = analyzer._parse_claude_response(test_response)

        assert parsed["intent"] == "researching"
        assert parsed["confidence"] == 0.85
        assert parsed["urgency"] == "medium"

        # Test response with text and JSON
        test_response_with_text = 'Here is the analysis: {"intent": "ready_to_buy", "confidence": 0.95}'
        parsed_with_text = analyzer._parse_claude_response(test_response_with_text)

        assert parsed_with_text["intent"] == "ready_to_buy"
        assert parsed_with_text["confidence"] == 0.95

        # Test malformed response
        malformed_response = "This is not JSON"
        parsed_malformed = analyzer._parse_claude_response(malformed_response)

        assert "raw_response" in parsed_malformed
        assert parsed_malformed["raw_response"] == malformed_response

        # Clean up
        await analyzer.close()


@pytest.mark.asyncio
async def test_lead_intent_analysis_mock():
    """Test lead intent analysis with mocked Claude API."""

    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        from ghl_real_estate_ai.services.claude_semantic_analyzer import create_claude_analyzer

        analyzer = create_claude_analyzer(api_key="test-key")

        # Mock the Claude API call
        mock_response = json.dumps({
            "primary_intent": "actively_looking",
            "confidence": 0.85,
            "urgency_level": "high",
            "timeline": "1-3 months",
            "reasoning": "Multiple property inquiries indicate active search",
            "supporting_evidence": ["viewed 3 properties", "asked about financing"],
            "behavioral_signals": ["frequent responses", "detailed questions"],
            "qualification_readiness": 85
        })

        with patch.object(analyzer, '_call_claude_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_response

            test_messages = [
                {"role": "prospect", "content": "I'm looking for a 3 bedroom house under 500k"},
                {"role": "agent", "content": "What's your timeline?"},
                {"role": "prospect", "content": "We need to move by March"}
            ]

            result = await analyzer.analyze_lead_intent(test_messages)

            assert result["primary_intent"] == "actively_looking"
            assert result["confidence"] == 0.85
            assert result["urgency_level"] == "high"
            assert result["qualification_readiness"] == 85

            # Verify API was called
            mock_api.assert_called_once()
            call_args = mock_api.call_args[0][0]
            assert "analyze this conversation" in call_args.lower()

        # Clean up
        await analyzer.close()


@pytest.mark.asyncio
async def test_qualification_data_validation():
    """Test qualification data validation logic."""

    # Test complete lead data
    complete_lead = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-1234",
        "budget": 400000,
        "property_type": "single_family",
        "location": "Austin, TX",
        "timeline": "3 months"
    }

    # Test incomplete lead data
    incomplete_lead = {
        "name": "Jane Smith",
        "email": "jane@example.com"
        # Missing phone, budget, etc.
    }

    # Test data completeness calculation
    def calculate_data_completeness(lead_data: Dict[str, Any]) -> float:
        """Simple completeness calculation for testing."""
        required_fields = ["name", "email", "phone", "budget", "property_type", "location", "timeline"]
        present_fields = sum(1 for field in required_fields if field in lead_data and lead_data[field])
        return present_fields / len(required_fields)

    complete_score = calculate_data_completeness(complete_lead)
    incomplete_score = calculate_data_completeness(incomplete_lead)

    assert complete_score == 1.0  # 7/7 fields
    assert incomplete_score == 2/7  # 2/7 fields (name, email)


@pytest.mark.asyncio
async def test_lead_scoring_logic():
    """Test lead scoring calculation logic."""

    def calculate_lead_score(lead_data: Dict[str, Any], semantic_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Simple scoring logic for testing."""

        # Base score from data completeness
        required_fields = ["name", "email", "phone", "budget", "timeline"]
        data_score = sum(20 for field in required_fields if field in lead_data and lead_data[field])

        # Semantic score from analysis
        semantic_score = int(semantic_analysis.get("qualification_readiness", 50))

        # Combined score (weighted average)
        final_score = int((data_score * 0.4) + (semantic_score * 0.6))

        return {
            "overall_score": final_score,
            "data_completeness_score": data_score,
            "semantic_intelligence_score": semantic_score,
            "priority": "critical" if final_score >= 85 else "high" if final_score >= 70 else "medium"
        }

    # Test high-quality lead
    high_quality_lead = {
        "name": "Sarah Johnson",
        "email": "sarah@example.com",
        "phone": "555-9876",
        "budget": 600000,
        "timeline": "immediate"
    }

    high_semantic = {
        "qualification_readiness": 90,
        "primary_intent": "ready_to_buy"
    }

    high_score = calculate_lead_score(high_quality_lead, high_semantic)

    assert high_score["overall_score"] >= 85
    assert high_score["priority"] == "critical"

    # Test lower quality lead
    low_quality_lead = {
        "name": "Bob Smith",
        "email": "bob@example.com"
    }

    low_semantic = {
        "qualification_readiness": 40,
        "primary_intent": "just_browsing"
    }

    low_score = calculate_lead_score(low_quality_lead, low_semantic)

    assert low_score["overall_score"] < 70
    assert low_score["priority"] in ["medium", "low"]


def test_lead_data_parsing():
    """Test parsing of lead data from various sources."""

    def parse_email_lead_notification(email_text: str) -> Dict[str, Any]:
        """Simple email parsing for testing."""
        import re

        lead_data = {}

        # Extract name
        name_match = re.search(r'Name:\s*([^\n]+)', email_text)
        if name_match:
            lead_data['name'] = name_match.group(1).strip()

        # Extract email
        email_match = re.search(r'Email:\s*([^\n]+)', email_text)
        if email_match:
            lead_data['email'] = email_match.group(1).strip()

        # Extract phone
        phone_match = re.search(r'Phone:\s*([^\n]+)', email_text)
        if phone_match:
            lead_data['phone'] = phone_match.group(1).strip()

        # Extract property address
        property_match = re.search(r'Property:\s*([^\n]+)', email_text)
        if property_match:
            lead_data['property_address'] = property_match.group(1).strip()

        return lead_data

    # Test email parsing
    sample_email = """
    New Lead Alert!

    Name: Jennifer Wilson
    Email: jennifer.wilson@email.com
    Phone: (555) 123-4567
    Property: 123 Main St, Austin TX 78701
    Source: ReSimpli Leads
    """

    parsed_data = parse_email_lead_notification(sample_email)

    assert parsed_data['name'] == "Jennifer Wilson"
    assert parsed_data['email'] == "jennifer.wilson@email.com"
    assert parsed_data['phone'] == "(555) 123-4567"
    assert parsed_data['property_address'] == "123 Main St, Austin TX 78701"


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in Claude services."""

    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        from ghl_real_estate_ai.services.claude_semantic_analyzer import create_claude_analyzer

        analyzer = create_claude_analyzer(api_key="test-key")

        # Mock API failure
        with patch.object(analyzer, '_call_claude_api', new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = Exception("API connection failed")

            test_messages = [{"role": "prospect", "content": "Hi there"}]

            # Should handle error gracefully
            result = await analyzer.analyze_lead_intent(test_messages)

            assert result["primary_intent"] == "unknown"
            assert result["confidence"] == 0.1
            assert result["urgency_level"] == "unknown"
            assert "Analysis failed" in result["reasoning"]

        # Clean up
        await analyzer.close()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])