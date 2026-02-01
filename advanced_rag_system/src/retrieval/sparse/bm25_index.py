"""BM25 sparse retrieval implementation.

This module implements BM25 (Best Matching 25) sparse retrieval using
rank-bm25 library with custom preprocessing and integration with the
Advanced RAG System type system.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from uuid import UUID

from rank_bm25 import BM25Okapi

from src.core.exceptions import RetrievalError
from src.core.types import DocumentChunk, SearchResult


@dataclass
class BM25Config:
    """Configuration for BM25 retriever.

    Attributes:
        k1: Term frequency saturation parameter (default: 1.5)
        b: Length normalization parameter (default: 0.75)
        top_k: Maximum number of results to return (default: 100)
        lowercase: Whether to convert text to lowercase (default: True)
        remove_stopwords: Whether to remove stopwords (default: True)
        min_token_length: Minimum token length to include (default: 2)
    """

    k1: float = 1.5
    b: float = 0.75
    top_k: int = 100
    lowercase: bool = True
    remove_stopwords: bool = True
    min_token_length: int = 2


class TextPreprocessor:
    """Text preprocessing pipeline for BM25 indexing."""

    def __init__(self, config: BM25Config):
        """Initialize preprocessor with configuration.

        Args:
            config: BM25 configuration containing preprocessing options
        """
        self.config = config
        self._stopwords = self._get_english_stopwords()

    def preprocess(self, text: str) -> List[str]:
        """Preprocess text into tokens for BM25 indexing.

        Args:
            text: Input text to preprocess

        Returns:
            List of preprocessed tokens

        Raises:
            ValueError: If input text is empty or invalid
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Convert to lowercase
        if self.config.lowercase:
            text = text.lower()

        # Tokenize (split on non-alphanumeric characters)
        tokens = re.findall(r'\b[a-zA-Z]+\b', text)

        # Filter tokens
        filtered_tokens = []
        for token in tokens:
            # Skip short tokens
            if len(token) < self.config.min_token_length:
                continue

            # Skip stopwords
            if self.config.remove_stopwords and token in self._stopwords:
                continue

            filtered_tokens.append(token)

        return filtered_tokens

    def _get_english_stopwords(self) -> Set[str]:
        """Get common English stopwords.

        Returns:
            Set of common English stopwords
        """
        # Common English stopwords
        return {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'will', 'with', 'i', 'me', 'my', 'myself', 'we', 'our',
            'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves',
            'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'they',
            'them', 'their', 'theirs', 'themselves', 'this', 'these', 'those',
            'am', 'been', 'being', 'have', 'had', 'having', 'do', 'does', 'did',
            'doing', 'would', 'could', 'should', 'ought', 'can', 'may', 'might',
            'must', 'shall'
        }


class BM25Index:
    """BM25 sparse retrieval index.

    This class implements BM25 ranking using the rank-bm25 library with
    custom preprocessing and integration with DocumentChunk types.
    """

    def __init__(self, config: Optional[BM25Config] = None):
        """Initialize BM25 index.

        Args:
            config: Optional configuration for BM25 parameters
        """
        self.config = config or BM25Config()
        self.preprocessor = TextPreprocessor(self.config)

        # Internal storage
        self._corpus: List[List[str]] = []
        self._documents: List[DocumentChunk] = []
        self._document_map: Dict[UUID, DocumentChunk] = {}
        self._bm25: Optional[BM25Okapi] = None

    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """Add documents to the BM25 index.

        Args:
            chunks: List of document chunks to index

        Raises:
            RetrievalError: If document processing fails
        """
        if not chunks:
            return

        try:
            for chunk in chunks:
                # Preprocess content
                tokens = self.preprocessor.preprocess(chunk.content)

                # Add to corpus and storage
                self._corpus.append(tokens)
                self._documents.append(chunk)
                self._document_map[chunk.id] = chunk

            # Rebuild BM25 index
            self._rebuild_index()

        except Exception as e:
            raise RetrievalError(
                message=f"Failed to add documents to BM25 index: {str(e)}",
                error_code="BM25_INDEX_ERROR"
            ) from e

    def search(self, query: str, top_k: Optional[int] = None) -> List[SearchResult]:
        """Search the BM25 index for relevant documents.

        Args:
            query: Search query string
            top_k: Maximum number of results to return

        Returns:
            List of search results ranked by BM25 score

        Raises:
            ValueError: If query is empty
            RetrievalError: If search operation fails
        """
        # Validate query
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        if not self._bm25:
            return []  # No documents indexed

        try:
            # Preprocess query
            query_tokens = self.preprocessor.preprocess(query)
            if not query_tokens:
                return []

            # Get BM25 scores
            scores = self._bm25.get_scores(query_tokens)

            # Create ranked results
            top_k = top_k or self.config.top_k
            doc_scores = list(enumerate(scores))

            # Sort by score (descending) and take top_k
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            doc_scores = doc_scores[:top_k]

            # Filter out zero scores
            doc_scores = [(idx, score) for idx, score in doc_scores if score > 0]

            # Convert to SearchResult objects
            results = []
            for rank, (doc_idx, score) in enumerate(doc_scores, 1):
                if doc_idx < len(self._documents):
                    result = SearchResult(
                        chunk=self._documents[doc_idx],
                        score=min(score / 10.0, 1.0),  # Normalize BM25 score to 0-1
                        rank=rank,
                        distance=1.0 - min(score / 10.0, 1.0),  # Distance is inverse of score
                        explanation=f"BM25 score: {score:.4f}, matched tokens: {len(query_tokens)}"
                    )
                    results.append(result)

            return results

        except Exception as e:
            raise RetrievalError(
                message=f"BM25 search failed: {str(e)}",
                error_code="BM25_SEARCH_ERROR"
            ) from e

    def get_document_by_id(self, chunk_id: UUID) -> Optional[DocumentChunk]:
        """Retrieve a document chunk by its ID.

        Args:
            chunk_id: Unique identifier of the chunk

        Returns:
            DocumentChunk if found, None otherwise
        """
        return self._document_map.get(chunk_id)

    def clear(self) -> None:
        """Clear all documents from the index."""
        self._corpus.clear()
        self._documents.clear()
        self._document_map.clear()
        self._bm25 = None

    def get_corpus(self) -> List[List[str]]:
        """Get the preprocessed corpus.

        Returns:
            List of tokenized documents
        """
        return self._corpus.copy()

    @property
    def document_count(self) -> int:
        """Get the number of documents in the index.

        Returns:
            Number of indexed documents
        """
        return len(self._documents)

    def _rebuild_index(self) -> None:
        """Rebuild the BM25 index with current corpus."""
        if self._corpus:
            # Create BM25 index with custom parameters
            self._bm25 = BM25Okapi(
                self._corpus,
                k1=self.config.k1,
                b=self.config.b
            )
        else:
            self._bm25 = None