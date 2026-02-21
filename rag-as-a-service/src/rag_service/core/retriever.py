"""Hybrid retriever — vector similarity + BM25 keyword search with RRF fusion."""

from __future__ import annotations

import logging
import math
import re
from collections import defaultdict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """A retrieved chunk with relevance scores."""

    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict = field(default_factory=dict)
    vector_score: float = 0.0
    keyword_score: float = 0.0


class Retriever:
    """Hybrid search with pgvector cosine similarity + BM25, fused via RRF."""

    RRF_K = 60  # RRF constant

    def __init__(self, db_session=None, embedding_service=None, top_k: int = 10):
        self.db = db_session
        self.embedding_service = embedding_service
        self.top_k = top_k

    async def search(
        self,
        query: str,
        query_embedding: list[float],
        collection_id: str | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """Hybrid search: vector + keyword, fused with RRF."""
        k = top_k or self.top_k

        # Run both searches
        vector_results = await self._vector_search(query_embedding, collection_id, k * 2)
        keyword_results = await self._keyword_search(query, collection_id, k * 2)

        # Fuse with Reciprocal Rank Fusion
        fused = self._rrf_fusion(vector_results, keyword_results)
        return fused[:k]

    async def _vector_search(
        self,
        embedding: list[float],
        collection_id: str | None,
        limit: int,
    ) -> list[RetrievedChunk]:
        """Search using pgvector cosine similarity."""
        if self.db is None:
            return []

        # Build query with optional collection filter
        query = """
            SELECT c.id, c.document_id, c.content, c.metadata,
                   1 - (c.embedding <=> :embedding::vector) as similarity
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
        """
        params: dict = {"embedding": str(embedding)}

        if collection_id:
            query += " WHERE d.collection_id = :collection_id"
            params["collection_id"] = collection_id

        query += " ORDER BY c.embedding <=> :embedding::vector LIMIT :limit"
        params["limit"] = limit

        result = await self.db.execute(query, params)
        rows = result.fetchall()

        return [
            RetrievedChunk(
                chunk_id=str(row.id),
                document_id=str(row.document_id),
                content=row.content,
                score=float(row.similarity),
                metadata=row.metadata or {},
                vector_score=float(row.similarity),
            )
            for row in rows
        ]

    async def _keyword_search(
        self,
        query: str,
        collection_id: str | None,
        limit: int,
    ) -> list[RetrievedChunk]:
        """BM25-style keyword search using PostgreSQL full-text search."""
        if self.db is None:
            return self._in_memory_keyword_search(query, limit)

        tsquery = " & ".join(re.findall(r"\w+", query))
        if not tsquery:
            return []

        sql = """
            SELECT c.id, c.document_id, c.content, c.metadata,
                   ts_rank(to_tsvector('english', c.content), to_tsquery('english', :tsquery)) as rank
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            WHERE to_tsvector('english', c.content) @@ to_tsquery('english', :tsquery)
        """
        params: dict = {"tsquery": tsquery}

        if collection_id:
            sql += " AND d.collection_id = :collection_id"
            params["collection_id"] = collection_id

        sql += " ORDER BY rank DESC LIMIT :limit"
        params["limit"] = limit

        result = await self.db.execute(sql, params)
        rows = result.fetchall()

        return [
            RetrievedChunk(
                chunk_id=str(row.id),
                document_id=str(row.document_id),
                content=row.content,
                score=float(row.rank),
                metadata=row.metadata or {},
                keyword_score=float(row.rank),
            )
            for row in rows
        ]

    def _in_memory_keyword_search(self, query: str, limit: int) -> list[RetrievedChunk]:
        """Fallback in-memory BM25 approximation for testing without DB."""
        return []

    def _rrf_fusion(
        self,
        vector_results: list[RetrievedChunk],
        keyword_results: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """Reciprocal Rank Fusion to combine vector and keyword results."""
        scores: dict[str, float] = defaultdict(float)
        chunks: dict[str, RetrievedChunk] = {}

        for rank, chunk in enumerate(vector_results):
            scores[chunk.chunk_id] += 1.0 / (self.RRF_K + rank + 1)
            if chunk.chunk_id not in chunks:
                chunks[chunk.chunk_id] = chunk

        for rank, chunk in enumerate(keyword_results):
            scores[chunk.chunk_id] += 1.0 / (self.RRF_K + rank + 1)
            if chunk.chunk_id not in chunks:
                chunks[chunk.chunk_id] = chunk
            else:
                chunks[chunk.chunk_id].keyword_score = chunk.keyword_score

        # Sort by combined RRF score
        sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

        result = []
        for cid in sorted_ids:
            chunk = chunks[cid]
            chunk.score = scores[cid]
            result.append(chunk)

        return result

    @staticmethod
    def bm25_score(
        query_terms: list[str],
        doc_terms: list[str],
        avg_doc_len: float,
        doc_count: int,
        term_doc_freqs: dict[str, int],
        k1: float = 1.5,
        b: float = 0.75,
    ) -> float:
        """Compute BM25 score for a document against a query."""
        score = 0.0
        doc_len = len(doc_terms)
        doc_term_freqs = defaultdict(int)
        for t in doc_terms:
            doc_term_freqs[t] += 1

        for term in query_terms:
            if term not in doc_term_freqs:
                continue
            tf = doc_term_freqs[term]
            df = term_doc_freqs.get(term, 0)
            idf = math.log((doc_count - df + 0.5) / (df + 0.5) + 1)
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * doc_len / avg_doc_len)
            score += idf * numerator / denominator

        return score
