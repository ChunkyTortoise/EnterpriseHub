"""
rag_pipeline.py — Self-contained RAG pipeline for demo app.
No cross-repo imports. Dependencies: chromadb, pypdf, httpx, beautifulsoup4, openai, anthropic.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from uuid import uuid4

from typing import Any

import anthropic
import httpx
from bs4 import BeautifulSoup
from openai import OpenAI


@dataclass
class ProviderConfig:
    embedding_provider: str  # "glm" | "openai" | "anthropic"
    llm_provider: str  # "glm" | "anthropic" | "openai"
    api_key: str
    embedding_model: str = "embedding-3"
    llm_model: str = "glm-4-flash"
    glm_base_url: str = "https://api.z.ai/api/paas/v4"


@dataclass
class SourceChunk:
    content: str  # first 200 chars of chunk
    score: float
    chunk_index: int


@dataclass
class RAGResponse:
    answer: str
    sources: list[SourceChunk]
    latency_ms: int


# --- Chunking ---


def _chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 100) -> list[str]:
    """Split text into overlapping chunks using sentence boundaries."""
    # Split on sentence endings
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    chunks = []
    current_chunk = []
    current_len = 0

    for sentence in sentences:
        words = sentence.split()
        word_count = len(words)

        if current_len + word_count > chunk_size and current_chunk:
            # Save current chunk
            chunks.append(" ".join(current_chunk))
            # Keep overlap words from end of current chunk
            overlap_words = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else current_chunk[:]
            current_chunk = overlap_words + words
            current_len = len(current_chunk)
        else:
            current_chunk.extend(words)
            current_len += word_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks if chunks else [text[:4000]]  # fallback for very short text


# --- Embedding ---


def _embed_texts(texts: list[str], config: ProviderConfig) -> list[list[float]]:
    """Embed a list of texts using the configured provider."""
    provider = config.embedding_provider

    # Anthropic has no embeddings API — fall back to GLM
    if provider == "anthropic":
        provider = "glm"

    if provider == "openai":
        client = OpenAI(api_key=config.api_key)
        response = client.embeddings.create(model="text-embedding-3-small", input=texts)
        return [item.embedding for item in response.data]

    # Default: GLM via OpenAI-compatible endpoint
    client = OpenAI(base_url=config.glm_base_url, api_key=config.api_key)
    response = client.embeddings.create(model=config.embedding_model, input=texts)
    return [item.embedding for item in response.data]


# --- LLM Answer ---


def _generate_answer(question: str, chunks: list[str], config: ProviderConfig) -> str:
    """Generate an answer using the configured LLM with retrieved chunks as context."""
    sources_text = "\n\n".join(f"[Source {i + 1}]\n{chunk}" for i, chunk in enumerate(chunks))

    system_prompt = (
        "You are a helpful AI assistant. Answer the user's question based on the provided sources. "
        "Reference sources as [Source 1], [Source 2], etc. Be concise and accurate. "
        "If the answer is not in the sources, say so clearly."
    )
    user_message = f"Sources:\n{sources_text}\n\nQuestion: {question}"

    if config.llm_provider == "anthropic":
        client = anthropic.Anthropic(api_key=config.api_key)
        response = client.messages.create(
            model=config.llm_model if config.llm_model != "glm-4-flash" else "claude-3-5-haiku-20241022",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text

    if config.llm_provider == "openai":
        client = OpenAI(api_key=config.api_key)
        response = client.chat.completions.create(
            model=config.llm_model if config.llm_model != "glm-4-flash" else "gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1024,
        )
        return response.choices[0].message.content

    # Default: GLM via OpenAI-compatible endpoint
    client = OpenAI(base_url=config.glm_base_url, api_key=config.api_key)
    response = client.chat.completions.create(
        model=config.llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        max_tokens=1024,
    )
    return response.choices[0].message.content


# --- ChromaDB client (lazy singleton to avoid pydantic v1 import errors on Python 3.14+) ---
_chroma_client: Any = None


def _get_chroma_client() -> Any:
    global _chroma_client
    if _chroma_client is None:
        import chromadb

        _chroma_client = chromadb.EphemeralClient()
    return _chroma_client


# --- Public API ---


def ingest_document(content: bytes, filename: str, provider_config: ProviderConfig) -> str:
    """Chunk, embed, and store document content. Returns collection_id."""
    if not content or not content.strip():
        raise ValueError("Document content is empty")

    # Extract text based on file type
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "txt"

    if ext == "pdf":
        import io

        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            text = content.decode("latin-1")

    text = text.strip()
    if not text:
        raise ValueError("No text could be extracted from document")

    # Chunk
    chunks = _chunk_text(text)

    # Embed
    embeddings = _embed_texts(chunks, provider_config)

    # Store in ChromaDB
    collection_id = f"doc_{uuid4().hex[:8]}"
    collection = _get_chroma_client().create_collection(name=collection_id)

    collection.add(
        ids=[f"chunk_{i}" for i in range(len(chunks))],
        embeddings=embeddings,
        documents=chunks,
        metadatas=[{"chunk_index": i, "source_filename": filename} for i in range(len(chunks))],
    )

    return collection_id


def ingest_url(url: str, provider_config: ProviderConfig) -> str:
    """Fetch URL, extract text, ingest as document. Returns collection_id."""
    response = httpx.get(url, timeout=30, follow_redirects=True, headers={"User-Agent": "RAGBot/1.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    # Remove script/style tags
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)  # collapse excessive newlines

    filename = url.split("/")[-1] or "webpage.html"
    if not filename.endswith((".html", ".htm")):
        filename = "webpage.html"

    return ingest_document(text.encode("utf-8"), filename, provider_config)


def query(question: str, collection_id: str, provider_config: ProviderConfig) -> RAGResponse:
    """Embed question, retrieve top-5 chunks, generate answer with citations."""
    start = time.time()

    # Embed question
    question_embedding = _embed_texts([question], provider_config)[0]

    # Retrieve from ChromaDB
    collection = _get_chroma_client().get_collection(name=collection_id)
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=min(5, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # Generate answer
    answer = _generate_answer(question, chunks, provider_config)

    latency_ms = int((time.time() - start) * 1000)

    sources = [
        SourceChunk(
            content=chunk[:200],
            score=float(1.0 - dist),  # convert distance to similarity score
            chunk_index=meta.get("chunk_index", i),
        )
        for i, (chunk, meta, dist) in enumerate(zip(chunks, metadatas, distances))
    ]

    return RAGResponse(answer=answer, sources=sources, latency_ms=latency_ms)


# --- Hybrid RAG Pipeline ---

from collections import defaultdict


@dataclass
class HybridSourceChunk:
    content: str
    bm25_score: float
    dense_score: float
    fused_score: float
    chunk_index: int


@dataclass
class HybridRAGResponse:
    answer: str
    sources: list[HybridSourceChunk]
    latency_ms: int


class HybridRAGPipeline:
    """BM25 + dense retrieval with Reciprocal Rank Fusion."""

    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 100):
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._corpus: list[str] = []
        self._bm25: Any = None  # lazy init
        self._chroma_collection: Any = None
        self._collection_name: str | None = None

    def ingest(self, content: bytes, filename: str, provider_config: ProviderConfig) -> str:
        """Ingest document: builds BM25 index + dense embeddings in ChromaDB."""
        from rank_bm25 import BM25Okapi

        # Extract text
        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "txt"
        if ext == "pdf":
            import io

            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1")

        text = text.strip()
        if not text:
            raise ValueError("No text could be extracted from document")

        chunks = _chunk_text(text, self._chunk_size, self._chunk_overlap)
        self._corpus = chunks

        # BM25
        tokenized = [c.lower().split() for c in chunks]
        self._bm25 = BM25Okapi(tokenized)

        # Dense (ChromaDB)
        embeddings = _embed_texts(chunks, provider_config)
        collection_id = f"hyb_{uuid4().hex[:8]}"
        collection = _get_chroma_client().create_collection(name=collection_id)
        collection.add(
            ids=[f"chunk_{i}" for i in range(len(chunks))],
            embeddings=embeddings,
            documents=chunks,
            metadatas=[{"chunk_index": i, "source_filename": filename} for i in range(len(chunks))],
        )
        self._chroma_collection = collection
        self._collection_name = collection_id
        return collection_id

    def query(self, question: str, provider_config: ProviderConfig, top_k: int = 5) -> HybridRAGResponse:
        """Hybrid search: BM25 + dense + RRF fusion, then LLM answer."""
        if self._bm25 is None or self._chroma_collection is None:
            raise RuntimeError("Pipeline not initialized. Call ingest() first.")

        start = time.time()

        # BM25 scores
        tokenized_q = question.lower().split()
        bm25_scores = self._bm25.get_scores(tokenized_q)
        bm25_ranked = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)

        # Dense scores
        q_emb = _embed_texts([question], provider_config)[0]
        n_results = min(top_k * 2, len(self._corpus))
        results = self._chroma_collection.query(
            query_embeddings=[q_emb],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        dense_metas = results["metadatas"][0]
        dense_distances = results["distances"][0]
        dense_ranked = [meta.get("chunk_index", i) for i, meta in enumerate(dense_metas)]

        # RRF fusion (k=60 standard)
        rrf_k = 60
        rrf_scores: dict[int, float] = defaultdict(float)
        for rank, idx in enumerate(bm25_ranked[: top_k * 2]):
            rrf_scores[idx] += 1.0 / (rrf_k + rank + 1)
        for rank, idx in enumerate(dense_ranked):
            rrf_scores[idx] += 1.0 / (rrf_k + rank + 1)

        # Top-k fused
        top_indices = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)[:top_k]

        # Normalize dense distances to scores
        max_dist = max(dense_distances) if dense_distances else 1.0
        dense_score_map: dict[int, float] = {}
        for i, idx in enumerate(dense_ranked):
            dense_score_map[idx] = float(1.0 - dense_distances[i] / (max_dist + 1e-9))

        # Normalize BM25 scores
        max_bm25 = max(bm25_scores) if any(s > 0 for s in bm25_scores) else 1.0
        bm25_score_map: dict[int, float] = {
            i: float(bm25_scores[i] / (max_bm25 + 1e-9)) for i in range(len(bm25_scores))
        }

        # Normalize fused scores
        max_rrf = max(rrf_scores.values()) if rrf_scores else 1.0

        chunks_for_answer = [self._corpus[i] for i in top_indices]
        answer = _generate_answer(question, chunks_for_answer, provider_config)
        latency_ms = int((time.time() - start) * 1000)

        sources = [
            HybridSourceChunk(
                content=self._corpus[i][:200],
                bm25_score=round(bm25_score_map.get(i, 0.0), 4),
                dense_score=round(dense_score_map.get(i, 0.0), 4),
                fused_score=round(rrf_scores[i] / (max_rrf + 1e-9), 4),
                chunk_index=i,
            )
            for i in top_indices
        ]
        return HybridRAGResponse(answer=answer, sources=sources, latency_ms=latency_ms)
