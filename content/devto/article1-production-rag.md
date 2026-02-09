---
title: Building Production RAG Without LangChain
published: false
tags: python, ai, rag, machinelearning
---

# Building Production RAG Without LangChain

I spent 4 months building a production RAG (Retrieval-Augmented Generation) system for a real estate AI platform. After wrestling with LangChain's abstractions, I rebuilt it from scratch using BM25, TF-IDF, and Claude. The result? 322 tests, <200ms p95 latency, and 94% citation accuracy.

Here's why I ditched LangChain and what I built instead.

## The LangChain Problem

LangChain promises to make LLM applications easier. In practice, it often does the opposite.

**Abstraction Overload**: Simple tasks require learning LangChain's mental model. Want to call an API? You need to understand Chains, Agents, Tools, and Memory. The framework adds cognitive load instead of removing it.

**Version Instability**: Breaking changes happen frequently. Code that worked in 0.0.200 breaks in 0.0.210. Production systems need stability.

**Debug Difficulty**: When something fails, you're debugging LangChain's abstractions instead of your logic. Stack traces go through 15 layers of framework code before reaching your function.

**Performance Overhead**: LangChain's generality comes at a cost. Extra abstractions mean extra function calls, extra memory allocations, and slower response times.

For a weekend prototype? LangChain is fine. For production? You need control.

## What We Built Instead

Our RAG system has three core components: ingestion, retrieval, and generation. No framework required.

### 1. Ingestion Pipeline

Documents flow through a custom chunking algorithm that preserves semantic boundaries:

```python
def chunk_document(text: str, max_chunk_size: int = 500) -> list[dict]:
    """Split text into overlapping chunks with metadata."""
    sentences = text.split('. ')
    chunks = []
    current_chunk = []
    current_size = 0

    for sentence in sentences:
        sentence_size = len(sentence.split())

        if current_size + sentence_size > max_chunk_size and current_chunk:
            chunk_text = '. '.join(current_chunk) + '.'
            chunks.append({
                'text': chunk_text,
                'word_count': current_size,
                'sentence_count': len(current_chunk)
            })
            # Overlap: keep last 2 sentences
            current_chunk = current_chunk[-2:]
            current_size = sum(len(s.split()) for s in current_chunk)

        current_chunk.append(sentence)
        current_size += sentence_size

    if current_chunk:
        chunk_text = '. '.join(current_chunk) + '.'
        chunks.append({
            'text': chunk_text,
            'word_count': current_size,
            'sentence_count': len(current_chunk)
        })

    return chunks
```

Why custom chunking? LangChain's text splitters break on fixed character counts. Ours respects sentence boundaries and adds overlaps to prevent context loss at chunk edges.

### 2. Hybrid Retrieval

We combine three retrieval strategies for maximum recall:

**BM25 (Keyword Search)**: Fast, exact matches, works without embeddings.

```python
from rank_bm25 import BM25Okapi

class BM25Retriever:
    def __init__(self, documents: list[str]):
        tokenized_docs = [doc.lower().split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized_docs)
        self.documents = documents

    def retrieve(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Retrieve top-k documents with BM25 scores."""
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        # Get top-k indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        return [(self.documents[i], scores[i]) for i in top_indices]
```

**TF-IDF (Statistical Relevance)**: Better than pure keyword matching, captures term importance.

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class TFIDFRetriever:
    def __init__(self, documents: list[str]):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.doc_vectors = self.vectorizer.fit_transform(documents)
        self.documents = documents

    def retrieve(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Retrieve top-k documents with TF-IDF cosine similarity."""
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.doc_vectors)[0]

        top_indices = np.argsort(similarities)[-top_k:][::-1]
        return [(self.documents[i], similarities[i]) for i in top_indices]
```

**Semantic Search (Embeddings)**: Captures meaning, finds conceptually similar content.

We use ChromaDB for vector storage, but the interface is simple:

```python
import chromadb

class SemanticRetriever:
    def __init__(self, collection_name: str = "documents"):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(collection_name)

    def add_documents(self, documents: list[str], ids: list[str]):
        """Add documents to vector store."""
        self.collection.add(documents=documents, ids=ids)

    def retrieve(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        """Retrieve top-k documents with semantic similarity."""
        results = self.collection.query(query_texts=[query], n_results=top_k)

        docs = results['documents'][0]
        distances = results['distances'][0]
        # Convert distance to similarity score (1 - normalized_distance)
        scores = [1 - (d / 2) for d in distances]

        return list(zip(docs, scores))
```

**Fusion**: We combine all three retrievers using Reciprocal Rank Fusion (RRF):

```python
def fuse_results(
    bm25_results: list[tuple[str, float]],
    tfidf_results: list[tuple[str, float]],
    semantic_results: list[tuple[str, float]],
    k: int = 60
) -> list[str]:
    """Fuse multiple retrieval results using RRF."""
    scores = {}

    for rank, (doc, _) in enumerate(bm25_results, 1):
        scores[doc] = scores.get(doc, 0) + 1 / (k + rank)

    for rank, (doc, _) in enumerate(tfidf_results, 1):
        scores[doc] = scores.get(doc, 0) + 1 / (k + rank)

    for rank, (doc, _) in enumerate(semantic_results, 1):
        scores[doc] = scores.get(doc, 0) + 1 / (k + rank)

    # Sort by fused score
    ranked_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc for doc, _ in ranked_docs]
```

RRF is simple and effective. Documents that appear in multiple retrieval results get boosted.

### 3. Citation Tracking

The killer feature: automatic citation extraction and verification.

```python
def extract_citations(response: str, source_chunks: list[str]) -> list[dict]:
    """Extract and verify citations from LLM response."""
    citations = []

    # Find quoted text in response
    import re
    quoted_pattern = r'"([^"]{20,})"'
    quotes = re.findall(quoted_pattern, response)

    for quote in quotes:
        # Find best matching source chunk
        best_match = None
        best_score = 0

        for idx, chunk in enumerate(source_chunks):
            # Simple substring match (production uses fuzzy matching)
            if quote.lower() in chunk.lower():
                score = len(quote) / len(chunk)
                if score > best_score:
                    best_score = score
                    best_match = idx

        if best_match is not None and best_score > 0.5:
            citations.append({
                'quote': quote,
                'source_index': best_match,
                'confidence': best_score,
                'verified': True
            })
        else:
            citations.append({
                'quote': quote,
                'source_index': None,
                'confidence': 0,
                'verified': False
            })

    return citations
```

We track:
- **Quote text**: What the LLM claimed
- **Source index**: Which chunk it came from
- **Confidence**: How well the quote matches the source
- **Verified**: Whether we found the quote in our corpus

This prevents hallucinations. If the LLM makes up a quote, citation tracking catches it.

### 4. Generation with Claude

The final step is simple. We send retrieved chunks and the user query to Claude:

```python
import anthropic

def generate_answer(
    query: str,
    context_chunks: list[str],
    api_key: str
) -> dict:
    """Generate answer using Claude with retrieved context."""
    client = anthropic.Anthropic(api_key=api_key)

    # Format context
    context = "\n\n".join([
        f"[Source {i+1}]\n{chunk}"
        for i, chunk in enumerate(context_chunks)
    ])

    # System prompt
    system = """You are a helpful assistant that answers questions using only the provided context.

Rules:
1. Only use information from the provided sources
2. Include direct quotes with source numbers: "quote" [Source N]
3. If the context doesn't contain the answer, say so
4. Be concise and accurate"""

    # User prompt
    prompt = f"""Context:
{context}

Question: {query}

Answer:"""

    # Call Claude
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text

    # Extract citations
    citations = extract_citations(response_text, context_chunks)

    return {
        'answer': response_text,
        'citations': citations,
        'source_chunks': context_chunks,
        'usage': {
            'input_tokens': message.usage.input_tokens,
            'output_tokens': message.usage.output_tokens
        }
    }
```

No chains. No agents. Just a clear system prompt and structured context.

## REST API

We expose the RAG system as a FastAPI endpoint:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class QueryResponse(BaseModel):
    answer: str
    citations: list[dict]
    sources: list[str]
    latency_ms: float

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the RAG system."""
    import time
    start = time.time()

    # Retrieve
    bm25_results = bm25_retriever.retrieve(request.query, request.top_k)
    tfidf_results = tfidf_retriever.retrieve(request.query, request.top_k)
    semantic_results = semantic_retriever.retrieve(request.query, request.top_k)

    # Fuse
    fused_docs = fuse_results(bm25_results, tfidf_results, semantic_results)
    top_chunks = fused_docs[:request.top_k]

    # Generate
    result = generate_answer(request.query, top_chunks, api_key=CLAUDE_API_KEY)

    latency = (time.time() - start) * 1000

    return QueryResponse(
        answer=result['answer'],
        citations=result['citations'],
        sources=top_chunks,
        latency_ms=latency
    )
```

The entire request flow: retrieve, fuse, generate, extract citations. Clean and testable.

## Results

After 4 months in production:

- **322 tests** (unit, integration, e2e)
- **<200ms p95 latency** (retrieve + generate)
- **94% citation accuracy** (verified quotes match sources)
- **Zero downtime** (thanks to circuit breakers and fallbacks)

Compare this to our LangChain prototype:
- 47 tests (most were mocking LangChain internals)
- ~800ms p95 latency
- 67% citation accuracy (LangChain's citation extraction was unreliable)
- Frequent version-related outages

## When to Use This Approach

**Use custom RAG when:**
- You need production reliability
- Latency matters (<500ms responses)
- You want full control over retrieval logic
- Citation accuracy is critical
- You're building a long-term product

**Use LangChain when:**
- Prototyping quickly
- Exploring different approaches
- Building internal tools
- Your team is already invested in the ecosystem

## Try It Yourself

- **GitHub**: [ChunkyTortoise/docqa-engine](https://github.com/ChunkyTortoise/docqa-engine)
- **Live Demo**: [ct-document-engine.streamlit.app](https://ct-document-engine.streamlit.app)
- **Starter Kit**: Production-ready RAG template with tests ($25)

Questions? Drop them in the comments. I'm building in public and sharing lessons learned.

---

*Building AI systems that work in production. Follow for more posts on RAG, LLMs, and practical AI engineering.*
