"""Tests for query expansion (HyDE and multi-query)."""

import pytest
from unittest.mock import AsyncMock

from rag_service.core.query_expander import QueryExpander, ExpandedQuery


@pytest.fixture
def mock_llm_client():
    """Mock LLM client."""
    llm = AsyncMock()
    return llm


@pytest.fixture
def expander_with_llm(mock_llm_client):
    """Query expander with LLM."""
    return QueryExpander(llm_client=mock_llm_client)


@pytest.fixture
def expander_without_llm():
    """Query expander without LLM (fallback mode)."""
    return QueryExpander(llm_client=None)


class TestQueryExpander:
    """Test query expansion techniques."""

    async def test_hyde_expansion_with_llm(self, expander_with_llm, mock_llm_client):
        """Test HyDE expansion using LLM."""
        # Arrange
        mock_llm_client.generate = AsyncMock(
            return_value="Real estate prices vary by location and market conditions."
        )

        # Act
        result = await expander_with_llm.expand(
            "What are real estate prices?", method="hyde"
        )

        # Assert
        assert isinstance(result, ExpandedQuery)
        assert result.method == "hyde"
        assert result.original == "What are real estate prices?"
        assert len(result.expansions) == 2  # Original + hypothetical
        assert "Real estate prices" in result.expansions[1]
        mock_llm_client.generate.assert_called_once()

    async def test_multi_query_expansion_with_llm(
        self, expander_with_llm, mock_llm_client
    ):
        """Test multi-query expansion using LLM."""
        # Arrange
        mock_llm_client.generate = AsyncMock(
            return_value="What is the cost of housing?\nHow much do homes cost?\nWhat are property prices?"
        )

        # Act
        result = await expander_with_llm.expand(
            "What are real estate prices?", method="multi_query"
        )

        # Assert
        assert result.method == "multi_query"
        assert len(result.expansions) >= 2  # Original + reformulations
        assert result.original in result.expansions
        # Should include reformulated queries
        assert any("cost" in q.lower() for q in result.expansions)

    async def test_hyde_fallback_without_llm(self, expander_without_llm):
        """Test HyDE expansion falls back to original query without LLM."""
        # Act
        result = await expander_without_llm.expand(
            "What are the prices?", method="hyde"
        )

        # Assert
        assert result.method == "hyde"
        assert result.expansions == ["What are the prices?"]
        assert len(result.expansions) == 1

    async def test_multi_query_fallback_without_llm(self, expander_without_llm):
        """Test multi-query expansion uses keyword fallback without LLM."""
        # Act
        result = await expander_without_llm.expand(
            "What are the real estate prices today?", method="multi_query"
        )

        # Assert
        assert result.method == "multi_query"
        assert len(result.expansions) >= 1
        assert result.original in result.expansions
        # May include shortened version
        if len(result.original.split()) > 3:
            assert len(result.expansions) == 2  # Original + shortened

    async def test_no_expansion_method(self, expander_with_llm):
        """Test that 'none' method returns original query only."""
        # Act
        result = await expander_with_llm.expand("test query", method="none")

        # Assert
        assert result.method == "none"
        assert result.expansions == ["test query"]
        assert len(result.expansions) == 1

    async def test_short_query_fallback(self, expander_without_llm):
        """Test fallback behavior with short queries."""
        # Act
        result = await expander_without_llm.expand("prices", method="multi_query")

        # Assert
        assert len(result.expansions) == 1  # Too short to shorten
        assert result.expansions == ["prices"]

    async def test_llm_reformulations_parsing(self, expander_with_llm, mock_llm_client):
        """Test parsing of LLM-generated reformulations."""
        # Arrange
        mock_llm_client.generate = AsyncMock(
            return_value="Query 1: How much?\nQuery 2: What's the price?\nQuery 3: Cost information?"
        )

        # Act
        result = await expander_with_llm.expand("Price question", method="multi_query")

        # Assert
        assert len(result.expansions) >= 2
        assert result.original in result.expansions
        # Should extract up to 3 reformulations
        assert len(result.expansions) <= 4  # Original + 3 reformulations

    async def test_empty_llm_response_handling(
        self, expander_with_llm, mock_llm_client
    ):
        """Test handling of empty LLM responses."""
        # Arrange
        mock_llm_client.generate = AsyncMock(return_value="")

        # Act
        result = await expander_with_llm.expand("test", method="multi_query")

        # Assert
        assert len(result.expansions) >= 1
        assert result.original in result.expansions


class TestExpandedQuery:
    """Test ExpandedQuery data model."""

    def test_expanded_query_creation(self):
        """Test creating an expanded query."""
        query = ExpandedQuery(
            original="What is the price?",
            expansions=["What is the price?", "How much does it cost?"],
            method="multi_query",
        )

        assert query.original == "What is the price?"
        assert len(query.expansions) == 2
        assert query.method == "multi_query"

    def test_expanded_query_single_expansion(self):
        """Test expanded query with only original."""
        query = ExpandedQuery(
            original="test",
            expansions=["test"],
            method="none",
        )

        assert query.expansions == ["test"]
        assert query.method == "none"
