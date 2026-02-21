"""Query expansion — HyDE and multi-query expansion for better retrieval."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExpandedQuery:
    """Result of query expansion."""

    original: str
    expansions: list[str]
    method: str  # "hyde", "multi_query", "none"


class QueryExpander:
    """Expand queries using HyDE or multi-query techniques."""

    def __init__(self, llm_client=None):
        """Initialize with optional LLM client for generating expansions."""
        self.llm_client = llm_client

    async def expand(self, query: str, method: str = "multi_query") -> ExpandedQuery:
        """Expand a query using the specified method."""
        if method == "hyde":
            return await self._hyde_expand(query)
        elif method == "multi_query":
            return await self._multi_query_expand(query)
        else:
            return ExpandedQuery(original=query, expansions=[query], method="none")

    async def _hyde_expand(self, query: str) -> ExpandedQuery:
        """Hypothetical Document Embedding (HyDE).

        Generate a hypothetical answer, then use it as the search query
        for better semantic matching.
        """
        if self.llm_client:
            hypothetical = await self.llm_client.generate(
                prompt=f"Write a short passage that would answer this question:\n{query}",
                max_tokens=200,
            )
            return ExpandedQuery(
                original=query,
                expansions=[query, hypothetical],
                method="hyde",
            )

        # Fallback: return original query
        return ExpandedQuery(original=query, expansions=[query], method="hyde")

    async def _multi_query_expand(self, query: str) -> ExpandedQuery:
        """Generate multiple reformulations of the query."""
        if self.llm_client:
            reformulations = await self.llm_client.generate(
                prompt=(f"Generate 3 different ways to ask this question, one per line:\n{query}"),
                max_tokens=200,
            )
            lines = [line.strip() for line in reformulations.strip().split("\n") if line.strip()]
            return ExpandedQuery(
                original=query,
                expansions=[query] + lines[:3],
                method="multi_query",
            )

        # Fallback: simple keyword expansion
        expansions = [query]
        words = query.lower().split()
        if len(words) > 3:
            # Add a shorter version
            expansions.append(" ".join(words[:3]))
        return ExpandedQuery(original=query, expansions=expansions, method="multi_query")
