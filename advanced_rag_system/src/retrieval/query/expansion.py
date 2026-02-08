"""Query expansion module for enhancing retrieval performance.

This module provides query expansion capabilities using synonym-based
techniques to improve recall in retrieval systems. It supports both
WordNet-based and LLM-based expansion strategies.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

from src.core.exceptions import QueryEnhancementError


@dataclass
class ExpansionConfig:
    """Configuration for query expansion.

    Attributes:
        max_expansions: Maximum number of expanded queries to generate
        synonym_limit: Maximum synonyms per term
        use_wordnet: Whether to use WordNet for synonym lookup
        use_llm: Whether to use LLM for expansion
        min_word_length: Minimum word length to consider for expansion
        expansion_strategy: Strategy for combining expansions ('all', 'best', 'selective')
        preserve_original: Whether to always include the original query
        stopwords: Set of words to exclude from expansion
    """

    max_expansions: int = 5
    synonym_limit: int = 3
    use_wordnet: bool = True
    use_llm: bool = False
    min_word_length: int = 3
    expansion_strategy: str = "selective"
    preserve_original: bool = True
    stopwords: Optional[Set[str]] = None

    def __post_init__(self):
        """Initialize default stopwords if not provided."""
        if self.stopwords is None:
            self.stopwords = {
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "from",
                "as",
                "is",
                "was",
                "are",
                "be",
                "been",
                "being",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "will",
                "would",
                "could",
                "should",
                "may",
                "might",
                "must",
                "shall",
                "can",
                "this",
                "that",
                "these",
                "those",
            }


class QueryExpander:
    """Query expander using synonym-based techniques.

        This class expands queries by replacing terms with their synonyms
    to improve recall in retrieval systems. It supports WordNet-based
        expansion and can be extended with LLM-based expansion.

        Example:
            ```python
            config = ExpansionConfig(max_expansions=3)
            expander = QueryExpander(config)

            # Simple expansion
            expansions = expander.expand("machine learning algorithms")
            # Returns: ['machine learning algorithms', 'device learning algorithms', ...]
            ```
    """

    def __init__(self, config: Optional[ExpansionConfig] = None):
        """Initialize query expander.

        Args:
            config: Optional configuration for expansion parameters
        """
        self.config = config or ExpansionConfig()
        self._wordnet_available = self._check_wordnet()
        self._synonym_cache: Dict[str, List[str]] = {}

    def _check_wordnet(self) -> bool:
        """Check if WordNet is available.

        Returns:
            True if WordNet is available, False otherwise
        """
        try:
            from nltk.corpus import wordnet

            # Try to access wordnet to verify it's downloaded
            wordnet.synsets("test")
            return True
        except (ImportError, LookupError):
            return False

    def _ensure_wordnet(self) -> None:
        """Ensure WordNet is available, downloading if necessary.

        Raises:
            QueryEnhancementError: If WordNet cannot be loaded
        """
        if not self._wordnet_available:
            try:
                import nltk

                nltk.download("wordnet", quiet=True)
                nltk.download("omw-1.4", quiet=True)
                from nltk.corpus import wordnet

                wordnet.synsets("test")  # Verify it works
                self._wordnet_available = True
            except Exception as e:
                raise QueryEnhancementError(
                    message=f"Failed to load WordNet: {str(e)}", error_code="WORDNET_LOAD_ERROR"
                ) from e

    def expand(self, query: str) -> List[str]:
        """Expand a query using synonyms.

                Generates multiple query variations by replacing terms with
        their synonyms to improve retrieval recall.

                Args:
                    query: Original search query

                Returns:
                    List of expanded query strings including the original

                Raises:
                    ValueError: If query is empty or invalid
                    QueryEnhancementError: If expansion fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        query = query.strip().lower()

        # Tokenize query
        tokens = self._tokenize(query)

        if not tokens:
            return [query] if self.config.preserve_original else []

        # Get expansions for each token
        token_expansions: Dict[str, List[str]] = {}
        for token in tokens:
            if self._should_expand_token(token):
                synonyms = self._get_synonyms(token)
                if synonyms:
                    token_expansions[token] = synonyms[: self.config.synonym_limit]

        # Generate expanded queries
        expanded_queries = self._generate_expansions(query, tokens, token_expansions)

        # Add original if configured
        if self.config.preserve_original and query not in expanded_queries:
            expanded_queries.insert(0, query)

        # Limit results
        return expanded_queries[: self.config.max_expansions]

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words.

        Args:
            text: Input text

        Returns:
            List of tokens
        """
        # Simple tokenization - split on non-alphanumeric
        tokens = re.findall(r"\b[a-zA-Z]+\b", text.lower())
        return tokens

    def _should_expand_token(self, token: str) -> bool:
        """Check if a token should be expanded.

        Args:
            token: Token to check

        Returns:
            True if token should be expanded
        """
        # Skip short tokens
        if len(token) < self.config.min_word_length:
            return False

        # Skip stopwords
        if token in self.config.stopwords:
            return False

        # Skip numbers
        if token.isdigit():
            return False

        return True

    def _get_synonyms(self, word: str) -> List[str]:
        """Get synonyms for a word.

        Args:
            word: Word to find synonyms for

        Returns:
            List of synonyms
        """
        # Check cache first
        if word in self._synonym_cache:
            return self._synonym_cache[word]

        synonyms: Set[str] = set()

        if self.config.use_wordnet:
            try:
                wordnet_synonyms = self._get_wordnet_synonyms(word)
                synonyms.update(wordnet_synonyms)
            except Exception:
                pass  # Continue with other methods

        # Filter out the original word and multi-word synonyms
        filtered_synonyms = [s for s in synonyms if s.lower() != word.lower() and " " not in s and "-" not in s]

        # Cache and return
        result = filtered_synonyms[: self.config.synonym_limit]
        self._synonym_cache[word] = result
        return result

    def _get_wordnet_synonyms(self, word: str) -> Set[str]:
        """Get synonyms using WordNet.

        Args:
            word: Word to find synonyms for

        Returns:
            Set of synonyms
        """
        self._ensure_wordnet()

        from nltk.corpus import wordnet

        synonyms: Set[str] = set()

        # Get synsets for the word
        synsets = wordnet.synsets(word)

        for synset in synsets[:3]:  # Limit to top 3 synsets
            for lemma in synset.lemmas():
                synonym = lemma.name().replace("_", " ")
                if synonym.lower() != word.lower():
                    synonyms.add(synonym)

        return synonyms

    def _generate_expansions(
        self, original_query: str, tokens: List[str], token_expansions: Dict[str, List[str]]
    ) -> List[str]:
        """Generate expanded queries.

        Args:
            original_query: Original query string
            tokens: Tokenized query
            token_expansions: Mapping of tokens to their expansions

        Returns:
            List of expanded queries
        """
        if not token_expansions:
            return []

        expansions: List[str] = []

        if self.config.expansion_strategy == "all":
            # Generate all possible combinations
            expansions = self._generate_all_combinations(tokens, token_expansions)
        elif self.config.expansion_strategy == "best":
            # Use only the best synonym for each token
            expansions = self._generate_best_combinations(tokens, token_expansions)
        else:  # selective
            # Generate selective expansions (one token at a time)
            expansions = self._generate_selective_expansions(original_query, tokens, token_expansions)

        return expansions

    def _generate_all_combinations(self, tokens: List[str], token_expansions: Dict[str, List[str]]) -> List[str]:
        """Generate all possible expansion combinations.

        Args:
            tokens: Original tokens
            token_expansions: Mapping of tokens to expansions

        Returns:
            List of expanded queries
        """
        from itertools import product

        # Build options for each position
        options: List[List[str]] = []
        for token in tokens:
            if token in token_expansions:
                opts = [token] + token_expansions[token]
                options.append(opts)
            else:
                options.append([token])

        # Generate combinations
        combinations = list(product(*options))

        # Convert to query strings
        queries = [" ".join(combo) for combo in combinations[1:]]  # Skip original
        return queries[: self.config.max_expansions]

    def _generate_best_combinations(self, tokens: List[str], token_expansions: Dict[str, List[str]]) -> List[str]:
        """Generate expansions using best synonym only.

        Args:
            tokens: Original tokens
            token_expansions: Mapping of tokens to expansions

        Returns:
            List of expanded queries
        """
        # Replace each expandable token with its best synonym
        best_expansions = []
        for token in tokens:
            if token in token_expansions:
                best_synonym = token_expansions[token][0]  # Use first (best) synonym
                expanded_tokens = tokens.copy()
                expanded_tokens[expanded_tokens.index(token)] = best_synonym
                expanded_query = " ".join(expanded_tokens)
                best_expansions.append(expanded_query)

        return best_expansions[: self.config.max_expansions]

    def _generate_selective_expansions(
        self, original_query: str, tokens: List[str], token_expansions: Dict[str, List[str]]
    ) -> List[str]:
        """Generate selective expansions (one token at a time).

        Args:
            original_query: Original query string
            tokens: Tokenized query
            token_expansions: Mapping of tokens to expansions

        Returns:
            List of expanded queries
        """
        expansions = []

        # For each expandable token, create variants
        for token in tokens:
            if token in token_expansions:
                for synonym in token_expansions[token]:
                    # Replace token with synonym in original query
                    expanded_query = original_query.replace(token, synonym, 1)
                    if expanded_query != original_query:
                        expansions.append(expanded_query)

        return list(dict.fromkeys(expansions))[: self.config.max_expansions]  # Remove duplicates

    def clear_cache(self) -> None:
        """Clear the synonym cache."""
        self._synonym_cache.clear()

    def get_stats(self) -> Dict[str, int]:
        """Get expansion statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "cache_size": len(self._synonym_cache),
            "wordnet_available": self._wordnet_available,
            "max_expansions": self.config.max_expansions,
            "synonym_limit": self.config.synonym_limit,
        }
