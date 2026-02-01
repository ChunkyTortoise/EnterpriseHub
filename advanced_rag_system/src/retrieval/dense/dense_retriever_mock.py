"""Mock dense retriever for development and testing when ChromaDB has dependency issues.

This is a temporary implementation that provides the same interface as the
production DenseRetriever but uses simple similarity calculations without ChromaDB.
"""

from __future__ import annotations

import asyncio
import time
from typing import List, Optional
import numpy as np

from src.core.exceptions import RetrievalError
from src.core.types import DocumentChunk, SearchResult


class MockDenseRetriever:
    """Mock dense retriever using simple similarity calculations.

    This is a temporary implementation for testing when ChromaDB dependencies
    are not available. Uses simple cosine similarity with mock embeddings.
    """

    def __init__(
        self,
        collection_name: str = "mock_dense_retrieval",
        embedding_model: str = "mock-embedding-model",
        dimensions: int = 1536,
        distance_metric: str = "cosine"
    ):
        """Initialize mock dense retriever."""
        self._collection_name = collection_name
        self._embedding_model = embedding_model
        self._dimensions = dimensions
        self._distance_metric = distance_metric

        # Store documents and their mock embeddings
        self._documents: List[DocumentChunk] = []
        self._embeddings: List[np.ndarray] = []
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize mock dense retriever."""
        self._initialized = True
        print(f"✅ Mock dense retriever initialized ({self._embedding_model})")

    def _ensure_initialized(self) -> None:
        """Ensure the retriever is initialized."""
        if not self._initialized:
            raise RetrievalError("Mock dense retriever not initialized. Call initialize() first.")

    def _create_mock_embedding(self, text: str) -> np.ndarray:
        """Create a simple mock embedding based on text characteristics.

        This creates deterministic embeddings based on text content for testing.
        """
        # Simple hash-based embedding for consistency
        text_lower = text.lower()

        # Create embedding based on text characteristics
        embedding = np.zeros(self._dimensions)

        # Add some signal based on word count, length, and character distribution
        words = text_lower.split()
        embedding[0] = len(words) / 100.0  # Word count signal
        embedding[1] = len(text) / 1000.0  # Length signal

        # Add character frequency signals
        for i, char in enumerate("abcdefghijklmnopqrstuvwxyz"):
            if i + 2 < self._dimensions:
                embedding[i + 2] = text_lower.count(char) / len(text) if text else 0

        # Add some topic signals based on keywords
        keywords = {
            'python': 100, 'programming': 101, 'code': 102, 'data': 103,
            'machine': 104, 'learning': 105, 'artificial': 106, 'intelligence': 107,
            'database': 108, 'query': 109, 'search': 110, 'retrieval': 111
        }

        for keyword, idx in keywords.items():
            if idx < self._dimensions and keyword in text_lower:
                embedding[idx] = 1.0

        # Add some random but deterministic variation based on text hash
        text_hash = hash(text) % 1000000
        np.random.seed(text_hash)
        noise = np.random.normal(0, 0.1, min(50, self._dimensions - 150))
        if len(noise) < self._dimensions - 150:
            embedding[150:150+len(noise)] = noise

        # Normalize to unit vector
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)

        if norm_product == 0:
            return 0.0

        return dot_product / norm_product

    async def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """Add documents to the mock dense index."""
        self._ensure_initialized()

        if not chunks:
            return

        try:
            start_time = time.time()

            # Create mock embeddings for each document
            for chunk in chunks:
                embedding = self._create_mock_embedding(chunk.content)
                self._documents.append(chunk)
                self._embeddings.append(embedding)

            elapsed_time = time.time() - start_time
            print(f"✅ Mock: Added {len(chunks)} documents in {elapsed_time:.3f}s")

        except Exception as e:
            raise RetrievalError(f"Failed to add documents to mock index: {str(e)}") from e

    async def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """Search using mock dense retrieval."""
        self._ensure_initialized()

        if not query.strip():
            return []

        if not self._documents:
            return []

        try:
            start_time = time.time()

            # Create query embedding
            query_embedding = self._create_mock_embedding(query)

            # Calculate similarities
            similarities = []
            for i, doc_embedding in enumerate(self._embeddings):
                similarity = self._cosine_similarity(query_embedding, doc_embedding)
                similarities.append((similarity, i))

            # Sort by similarity and get top_k
            similarities.sort(key=lambda x: x[0], reverse=True)
            top_similarities = similarities[:top_k]

            # Create search results
            results = []
            for similarity, doc_idx in top_similarities:
                if similarity > 0.0:  # Only include positive similarities
                    chunk = self._documents[doc_idx]
                    result = SearchResult(
                        chunk=chunk,
                        score=float(similarity),
                        retrieval_method="mock_dense",
                        metadata={
                            "similarity": similarity,
                            "embedding_model": self._embedding_model,
                            "mock_retriever": True
                        }
                    )
                    results.append(result)

            elapsed_time = time.time() - start_time

            # Log performance
            if elapsed_time > 0.05:  # Log if >50ms
                print(f"Mock dense search took {elapsed_time:.3f}s for {len(results)} results")

            return results

        except Exception as e:
            raise RetrievalError(f"Mock dense search failed: {str(e)}") from e

    def clear(self) -> None:
        """Clear the mock dense index."""
        self._documents.clear()
        self._embeddings.clear()

    async def async_clear(self) -> None:
        """Async version of clear operation."""
        self.clear()

    @property
    def document_count(self) -> int:
        """Get number of documents in the mock index."""
        return len(self._documents)

    @property
    def is_initialized(self) -> bool:
        """Check if the retriever is initialized."""
        return self._initialized

    async def close(self) -> None:
        """Close and cleanup resources."""
        self._initialized = False

    async def get_stats(self) -> dict:
        """Get mock retriever statistics."""
        return {
            "document_count": self.document_count,
            "collection_name": self._collection_name,
            "embedding_model": self._embedding_model,
            "dimensions": self._dimensions,
            "distance_metric": self._distance_metric,
            "initialized": self._initialized,
            "mock_retriever": True,
            "embeddings_stored": len(self._embeddings)
        }