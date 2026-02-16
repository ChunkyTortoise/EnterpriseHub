"""RAG Engine — orchestrates the full query -> retrieve -> rerank -> generate pipeline."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from rag_service.core.embedding_service import EmbeddingService
from rag_service.core.query_expander import QueryExpander
from rag_service.core.retriever import RetrievedChunk, Retriever

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Complete RAG response with answer and sources."""
    answer: str
    sources: list[SourceReference]
    query: str
    latency_ms: int = 0
    metadata: dict = field(default_factory=dict)


@dataclass
class SourceReference:
    """Reference to a source chunk used in generating the answer."""
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict = field(default_factory=dict)


class RAGEngine:
    """Orchestrates the RAG pipeline: query -> expand -> retrieve -> rerank -> generate."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        retriever: Retriever,
        query_expander: QueryExpander | None = None,
        llm_client=None,
        rerank_top_k: int = 5,
    ):
        self.embedding_service = embedding_service
        self.retriever = retriever
        self.query_expander = query_expander or QueryExpander()
        self.llm_client = llm_client
        self.rerank_top_k = rerank_top_k

    async def query(
        self,
        query_text: str,
        collection_id: str | None = None,
        top_k: int = 10,
        expand: bool = True,
        expansion_method: str = "multi_query",
    ) -> RAGResponse:
        """Execute the full RAG pipeline."""
        start = time.monotonic()

        # Step 1: Query expansion
        if expand and self.query_expander:
            expanded = await self.query_expander.expand(query_text, method=expansion_method)
            queries = expanded.expansions
        else:
            queries = [query_text]

        # Step 2: Embed and retrieve for each expanded query
        all_chunks: list[RetrievedChunk] = []
        seen_ids: set[str] = set()

        for q in queries:
            embedding = await self.embedding_service.embed_query(q)
            chunks = await self.retriever.search(
                query=q,
                query_embedding=embedding,
                collection_id=collection_id,
                top_k=top_k,
            )
            for chunk in chunks:
                if chunk.chunk_id not in seen_ids:
                    seen_ids.add(chunk.chunk_id)
                    all_chunks.append(chunk)

        # Step 3: Rerank (cross-encoder or score-based)
        reranked = self._rerank(all_chunks, query_text)

        # Step 4: Generate answer
        top_chunks = reranked[: self.rerank_top_k]
        answer = await self._generate_answer(query_text, top_chunks)

        # Build sources
        sources = [
            SourceReference(
                chunk_id=c.chunk_id,
                document_id=c.document_id,
                content=c.content[:500],  # Truncate for response
                score=c.score,
                metadata=c.metadata,
            )
            for c in top_chunks
        ]

        elapsed_ms = int((time.monotonic() - start) * 1000)

        return RAGResponse(
            answer=answer,
            sources=sources,
            query=query_text,
            latency_ms=elapsed_ms,
            metadata={
                "expanded_queries": len(queries),
                "total_chunks_retrieved": len(all_chunks),
                "reranked_count": len(top_chunks),
            },
        )

    def _rerank(self, chunks: list[RetrievedChunk], query: str) -> list[RetrievedChunk]:
        """Rerank chunks by score. In production, use a cross-encoder model."""
        # Simple score-based reranking with query term overlap boost
        query_terms = set(query.lower().split())

        for chunk in chunks:
            chunk_terms = set(chunk.content.lower().split())
            overlap = len(query_terms & chunk_terms)
            # Boost score by overlap ratio
            chunk.score += overlap * 0.01

        return sorted(chunks, key=lambda c: c.score, reverse=True)

    async def _generate_answer(
        self, query: str, chunks: list[RetrievedChunk]
    ) -> str:
        """Generate an answer from the retrieved chunks using LLM."""
        if not chunks:
            return "I couldn't find any relevant information to answer your question."

        context = "\n\n".join(
            f"[Source {i + 1}]: {c.content}" for i, c in enumerate(chunks)
        )

        prompt = (
            f"Based on the following context, answer the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            f"Answer:"
        )

        if self.llm_client:
            return await self.llm_client.generate(prompt=prompt, max_tokens=500)

        # Fallback: return context summary
        return f"Based on {len(chunks)} relevant sources: {chunks[0].content[:200]}..."

    async def query_stream(
        self,
        query_text: str,
        collection_id: str | None = None,
        top_k: int = 10,
    ):
        """Stream the RAG response token by token (SSE-compatible)."""
        # Get full response first, then simulate streaming
        response = await self.query(query_text, collection_id=collection_id, top_k=top_k)

        # Yield tokens
        words = response.answer.split()
        for word in words:
            yield word + " "

        # Yield sources at the end
        yield "\n\n---\nSources:\n"
        for i, src in enumerate(response.sources):
            yield f"[{i + 1}] {src.metadata.get('source', 'unknown')}\n"
