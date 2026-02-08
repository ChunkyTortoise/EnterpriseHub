"""
Semantic Cache Service
Implements similarity-based caching for agentic reasoning results.
Reduces token usage and improves response time for repetitive or similar queries.
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ghl_real_estate_ai.core.embeddings import EmbeddingModel
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)


class SemanticCache:
    def __init__(self, threshold: float = 0.92, ttl: int = 3600 * 24):
        self.embedding_model = EmbeddingModel()
        self.cache_service = get_cache_service()
        self.threshold = threshold
        self.ttl = ttl
        self.index_key = "semantic_cache:index"

    async def _get_index(self) -> List[Dict[str, Any]]:
        index = await self.cache_service.get(self.index_key)
        return index if index else []

    async def _save_index(self, index: List[Dict[str, Any]]):
        await self.cache_service.set(self.index_key, index, ttl=self.ttl)

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        a = np.array(v1)
        b = np.array(v2)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    async def get(self, query: str) -> Optional[Any]:
        """Find a semantically similar query in the cache."""
        query_embedding = self.embedding_model.embed_query(query)
        index = await self._get_index()

        best_match = None
        highest_score = 0.0

        for entry in index:
            score = self._cosine_similarity(query_embedding, entry["embedding"])
            if score > highest_score:
                highest_score = score
                best_match = entry

        if highest_score >= self.threshold:
            logger.info(f"🎯 Semantic cache HIT (score: {highest_score:.4f}) for: {query[:50]}...")
            return await self.cache_service.get(best_match["cache_key"])

        logger.info(f"🧊 Semantic cache MISS (best score: {highest_score:.4f}) for: {query[:50]}...")
        return None

    async def set(self, query: str, value: Any):
        """Store a value in the semantic cache with its embedding."""
        query_embedding = self.embedding_model.embed_query(query)
        cache_key = f"semantic_cache:data:{hash(query)}"

        # Save actual data
        await self.cache_service.set(cache_key, value, ttl=self.ttl)

        # Update index
        index = await self._get_index()
        index.append({"query": query, "embedding": query_embedding, "cache_key": cache_key, "timestamp": time.time()})

        # Limit index size (simple eviction)
        if len(index) > 500:
            index = index[-500:]

        await self._save_index(index)
        logger.info(f"📥 Cached new entry semantically: {query[:50]}...")


semantic_cache = SemanticCache()
