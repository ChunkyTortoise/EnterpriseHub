# Advanced RAG System - Performance Benchmarks

**Testing Strategy and Performance Targets**

---

## Overview

This document defines the comprehensive benchmarking strategy for the Advanced RAG System. Benchmarks are designed to validate performance targets and demonstrate production-ready engineering.

---

## Performance Targets

### Latency Targets

| Metric | Target | Stretch Goal | Measurement |
|--------|--------|--------------|-------------|
| API Response (p50) | <30ms | <20ms | End-to-end |
| API Response (p95) | <50ms | <35ms | End-to-end |
| API Response (p99) | <100ms | <75ms | End-to-end |
| Embedding Generation | <20ms | <15ms | Single query |
| Dense Retrieval | <15ms | <10ms | ChromaDB HNSW |
| Sparse Retrieval | <10ms | <5ms | BM25 index |
| Re-ranking | <25ms | <15ms | 10 candidates |
| LLM Generation | <50ms | <30ms | Cached queries |

### Quality Targets

| Metric | Target | Stretch Goal | Evaluation Method |
|--------|--------|--------------|-------------------|
| Retrieval Recall@5 | >85% | >90% | Labeled dataset |
| Retrieval Recall@10 | >90% | >95% | Labeled dataset |
| NDCG@10 | >0.85 | >0.90 | Labeled dataset |
| Answer Relevance | >4.0/5.0 | >4.5/5.0 | LLM-as-judge |
| Faithfulness | >0.90 | >0.95 | LLM evaluation |
| Context Precision | >0.80 | >0.85 | Manual evaluation |
| Context Recall | >0.85 | >0.90 | Manual evaluation |

### Throughput Targets

| Metric | Target | Stretch Goal | Notes |
|--------|--------|--------------|-------|
| Requests/minute | 1000+ | 5000+ | Sustained |
| Concurrent users | 100 | 500 | Without degradation |
| Documents indexed/min | 1000+ | 5000+ | Batch ingestion |
| Cache hit rate | >90% | >95% | Multi-layer |

### Resource Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Memory per instance | <2GB | Docker container |
| CPU utilization | <70% | Under normal load |
| Token efficiency | -50% | With compression |
| Cost per query | <$0.01 | Average |

---

## Benchmark Categories

### 1. Unit Performance Benchmarks

#### Embedding Performance

```python
# tests/benchmarks/test_embedding_perf.py

class TestEmbeddingPerformance:
    """Benchmark embedding generation performance."""
    
    @pytest.mark.benchmark
    async def test_single_embedding_latency(self, embedder):
        """Measure latency for single embedding."""
        latencies = []
        for _ in range(100):
            start = time.perf_counter()
            await embedder.embed("Sample query text")
            latencies.append((time.perf_counter() - start) * 1000)
        
        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)
        
        assert p50 < 20, f"p50 latency {p50}ms exceeds 20ms target"
        assert p95 < 30, f"p95 latency {p95}ms exceeds 30ms target"
    
    @pytest.mark.benchmark
    async def test_batch_embedding_throughput(self, embedder):
        """Measure batch embedding throughput."""
        texts = [f"Sample text {i}" for i in range(100)]
        
        start = time.perf_counter()
        await embedder.embed(texts, batch_size=32)
        elapsed = (time.perf_counter() - start) * 1000
        
        throughput = len(texts) / (elapsed / 1000)  # texts/sec
        assert throughput > 50, f"Throughput {throughput} < 50 texts/sec"
```

#### Retrieval Performance

```python
# tests/benchmarks/test_retrieval_perf.py

class TestRetrievalPerformance:
    """Benchmark retrieval performance."""
    
    @pytest.mark.benchmark
    async def test_dense_retrieval_latency(self, retriever, test_queries):
        """Measure dense retrieval latency."""
        latencies = []
        for query in test_queries:
            start = time.perf_counter()
            await retriever.dense_search(query, top_k=10)
            latencies.append((time.perf_counter() - start) * 1000)
        
        p95 = np.percentile(latencies, 95)
        assert p95 < 15, f"Dense retrieval p95 {p95}ms exceeds 15ms"
    
    @pytest.mark.benchmark
    async def test_hybrid_retrieval_latency(self, retriever, test_queries):
        """Measure hybrid retrieval end-to-end latency."""
        latencies = []
        for query in test_queries:
            start = time.perf_counter()
            await retriever.hybrid_search(
                query,
                top_k=10,
                rerank=True
            )
            latencies.append((time.perf_counter() - start) * 1000)
        
        p95 = np.percentile(latencies, 95)
        assert p95 < 50, f"Hybrid retrieval p95 {p95}ms exceeds 50ms"
```

### 2. End-to-End API Benchmarks

```python
# tests/benchmarks/test_api_perf.py

class TestAPIPerformance:
    """Benchmark API endpoint performance."""
    
    @pytest.mark.benchmark
    async def test_query_endpoint_latency(self, client):
        """Measure /query endpoint latency."""
        latencies = []
        
        for _ in range(100):
            start = time.perf_counter()
            response = await client.post("/query", json={
                "query": "What is RAG?",
                "retrieval_config": {"top_k": 5}
            })
            latencies.append((time.perf_counter() - start) * 1000)
            assert response.status_code == 200
        
        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)
        
        print(f"Query endpoint - p50: {p50:.1f}ms, p95: {p95:.1f}ms, p99: {p99:.1f}ms")
        
        assert p50 < 30
        assert p95 < 50
        assert p99 < 100
    
    @pytest.mark.benchmark
    async def test_cache_performance(self, client):
        """Measure cache hit performance improvement."""
        # First request (cache miss)
        start = time.perf_counter()
        await client.post("/query", json={"query": "Cached query"})
        miss_latency = (time.perf_counter() - start) * 1000
        
        # Second request (cache hit)
        start = time.perf_counter()
        await client.post("/query", json={"query": "Cached query"})
        hit_latency = (time.perf_counter() - start) * 1000
        
        improvement = (miss_latency - hit_latency) / miss_latency * 100
        print(f"Cache improvement: {improvement:.1f}%")
        
        assert hit_latency < miss_latency * 0.3  # 70% improvement
```

### 3. Quality Benchmarks

#### Retrieval Accuracy

```python
# tests/benchmarks/test_retrieval_quality.py

class TestRetrievalQuality:
    """Benchmark retrieval accuracy."""
    
    @pytest.mark.quality
    async def test_recall_at_k(self, retriever, labeled_dataset):
        """Measure recall@k on labeled dataset."""
        recalls_at_5 = []
        recalls_at_10 = []
        
        for item in labeled_dataset:
            results = await retriever.search(
                item["query"],
                top_k=10
            )
            retrieved_ids = {r.id for r in results}
            relevant_ids = set(item["relevant_docs"])
            
            # Recall@5
            recall_5 = len(retrieved_ids & relevant_ids) / len(relevant_ids)
            recalls_at_5.append(recall_5)
            
            # Recall@10
            recall_10 = len(retrieved_ids & relevant_ids) / len(relevant_ids)
            recalls_at_10.append(recall_10)
        
        mean_recall_5 = np.mean(recalls_at_5)
        mean_recall_10 = np.mean(recalls_at_10)
        
        print(f"Recall@5: {mean_recall_5:.3f}, Recall@10: {mean_recall_10:.3f}")
        
        assert mean_recall_5 > 0.85
        assert mean_recall_10 > 0.90
    
    @pytest.mark.quality
    async def test_ndcg_at_k(self, retriever, ranked_dataset):
        """Measure NDCG@k on ranked dataset."""
        ndcg_scores = []
        
        for item in ranked_dataset:
            results = await retriever.search(
                item["query"],
                top_k=10
            )
            
            # Calculate NDCG
            dcg = sum(
                (2 ** rel - 1) / np.log2(i + 2)
                for i, rel in enumerate(item["relevance_scores"])
            )
            
            ideal_dcg = sum(
                (2 ** rel - 1) / np.log2(i + 2)
                for i, rel in enumerate(sorted(item["relevance_scores"], reverse=True))
            )
            
            ndcg = dcg / ideal_dcg if ideal_dcg > 0 else 0
            ndcg_scores.append(ndcg)
        
        mean_ndcg = np.mean(ndcg_scores)
        print(f"NDCG@10: {mean_ndcg:.3f}")
        
        assert mean_ndcg > 0.85
```

#### Answer Quality

```python
# tests/benchmarks/test_answer_quality.py

class TestAnswerQuality:
    """Benchmark generated answer quality."""
    
    @pytest.mark.quality
    async def test_faithfulness(self, rag_system, qa_dataset):
        """Measure answer faithfulness to context."""
        faithfulness_scores = []
        
        for item in qa_dataset:
            response = await rag_system.query(item["query"])
            
            # Use LLM to evaluate faithfulness
            score = await evaluate_faithfulness(
                answer=response.answer,
                context=response.sources
            )
            faithfulness_scores.append(score)
        
        mean_faithfulness = np.mean(faithfulness_scores)
        print(f"Faithfulness: {mean_faithfulness:.3f}")
        
        assert mean_faithfulness > 0.90
    
    @pytest.mark.quality
    async def test_answer_relevance(self, rag_system, qa_dataset):
        """Measure answer relevance to query."""
        relevance_scores = []
        
        for item in qa_dataset:
            response = await rag_system.query(item["query"])
            
            # Use LLM-as-judge for relevance
            score = await evaluate_relevance(
                query=item["query"],
                answer=response.answer
            )
            relevance_scores.append(score)
        
        mean_relevance = np.mean(relevance_scores)
        print(f"Answer relevance: {mean_relevance:.2f}/5.0")
        
        assert mean_relevance > 4.0
```

### 4. Load Testing

#### Locust Load Tests

```python
# tests/load/locustfile.py

from locust import HttpUser, task, between
import random

class RAGUser(HttpUser):
    """Simulate RAG API users."""
    wait_time = between(1, 5)  # 1-5 seconds between requests
    
    def on_start(self):
        """Setup test queries."""
        self.queries = [
            "What is retrieval-augmented generation?",
            "How does vector search work?",
            "Explain embedding models",
            "What is the difference between BM25 and dense retrieval?",
            "How to implement hybrid search?",
        ]
    
    @task(10)
    def query_basic(self):
        """Basic query request."""
        query = random.choice(self.queries)
        response = self.client.post("/query", json={
            "query": query,
            "retrieval_config": {"top_k": 5}
        })
        assert response.status_code == 200
        assert response.elapsed.total_seconds() < 0.1  # 100ms
    
    @task(5)
    def query_hybrid(self):
        """Hybrid retrieval query."""
        query = random.choice(self.queries)
        response = self.client.post("/query", json={
            "query": query,
            "retrieval_config": {
                "top_k": 10,
                "retrieval_mode": "hybrid",
                "rerank": True
            }
        })
        assert response.status_code == 200
    
    @task(2)
    def query_streaming(self):
        """Streaming query request."""
        query = random.choice(self.queries)
        response = self.client.post("/query/stream", json={
            "query": query,
            "generation_config": {"stream": True}
        }, stream=True)
        assert response.status_code == 200
    
    @task(1)
    def ingest_document(self):
        """Document ingestion."""
        response = self.client.post("/ingest", json={
            "documents": [{
                "content": f"Sample document content {random.randint(1, 1000)}",
                "metadata": {"source": "load_test"}
            }]
        })
        assert response.status_code == 200
```

#### K6 Load Test Script

```javascript
// tests/load/k6_script.js

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const queryLatency = new Trend('query_latency');
const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp up
    { duration: '5m', target: 100 },   // Steady state
    { duration: '2m', target: 200 },   // Spike
    { duration: '5m', target: 200 },   // Sustained load
    { duration: '2m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<50'],    // 95% under 50ms
    http_req_failed: ['rate<0.01'],     // <1% errors
    query_latency: ['p(95)<50'],
  },
};

const queries = [
  "What is RAG?",
  "How does vector search work?",
  "Explain embeddings",
];

export default function () {
  const query = queries[Math.floor(Math.random() * queries.length)];
  
  const start = Date.now();
  const response = http.post('http://localhost:8000/query', JSON.stringify({
    query: query,
    retrieval_config: { top_k: 5 }
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  const latency = Date.now() - start;
  
  queryLatency.add(latency);
  
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'latency < 100ms': (r) => latency < 100,
    'has answer': (r) => JSON.parse(r.body).answer !== undefined,
  });
  
  errorRate.add(!success);
  
  sleep(Math.random() * 3 + 1);  // 1-4s between requests
}
```

---

## Benchmark Datasets

### 1. MS MARCO (Retrieval)

```python
# src/evaluation/datasets.py

async def load_ms_maro_subset(size: int = 1000) -> Dataset:
    """Load MS MARCO subset for benchmarking."""
    # Download and process MS MARCO
    pass

async def load_natural_questions(size: int = 500) -> Dataset:
    """Load Natural Questions subset."""
    pass

async def load_custom_qa(path: str) -> Dataset:
    """Load custom QA dataset."""
    pass
```

### 2. Synthetic Test Data

```python
# tests/fixtures/generate_test_data.py

def generate_synthetic_documents(count: int = 1000) -> List[Document]:
    """Generate synthetic documents for testing."""
    documents = []
    for i in range(count):
        doc = Document(
            id=f"doc-{i}",
            content=f"Synthetic document content {i}...",
            metadata={
                "source": f"synthetic_{i % 10}.txt",
                "category": random.choice(["tech", "science", "business"]),
                "created_at": datetime.utcnow().isoformat()
            }
        )
        documents.append(doc)
    return documents

def generate_test_queries(count: int = 100) -> List[Dict]:
    """Generate test queries with ground truth."""
    queries = []
    for i in range(count):
        query = {
            "query": f"Test query {i}",
            "relevant_docs": [f"doc-{i}", f"doc-{i+1}"],
            "relevance_scores": [3, 2]
        }
        queries.append(query)
    return queries
```

---

## Continuous Benchmarking

### CI/CD Integration

```yaml
# .github/workflows/benchmark.yml

name: Performance Benchmarks

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      
      - name: Run unit benchmarks
        run: |
          pytest tests/benchmarks/ -v --benchmark-only
      
      - name: Run quality benchmarks
        run: |
          pytest tests/benchmarks/test_retrieval_quality.py -v
          pytest tests/benchmarks/test_answer_quality.py -v
      
      - name: Store benchmark results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: benchmark_results.json
      
      - name: Compare with baseline
        run: |
          python scripts/compare_benchmarks.py \
            --current benchmark_results.json \
            --baseline baseline_results.json
```

### Benchmark Reporting

```python
# scripts/generate_benchmark_report.py

import json
from datetime import datetime
from typing import Dict, List

def generate_report(results: Dict) -> str:
    """Generate markdown benchmark report."""
    
    report = f"""# Benchmark Report

Generated: {datetime.utcnow().isoformat()}

## Performance Summary

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Query p95 latency | <50ms | {results['query_p95']:.1f}ms | {'✅' if results['query_p95'] < 50 else '❌'} |
| Recall@10 | >90% | {results['recall_at_10']:.1%} | {'✅' if results['recall_at_10'] > 0.9 else '❌'} |
| Faithfulness | >90% | {results['faithfulness']:.1%} | {'✅' if results['faithfulness'] > 0.9 else '❌'} |

## Detailed Results

### Latency Distribution

```
p50: {results['latency_p50']:.1f}ms
p95: {results['latency_p95']:.1f}ms
p99: {results['latency_p99']:.1f}ms
```

### Quality Metrics

- **Retrieval Recall@5**: {results['recall_at_5']:.1%}
- **Retrieval Recall@10**: {results['recall_at_10']:.1%}
- **NDCG@10**: {results['ndcg_at_10']:.3f}
- **Answer Relevance**: {results['answer_relevance']:.2f}/5.0
- **Faithfulness**: {results['faithfulness']:.1%}

## Regression Analysis

{generate_regression_analysis(results)}
"""
    
    return report

def generate_regression_analysis(results: Dict) -> str:
    """Compare with previous benchmark."""
    # Implementation
    pass
```

---

## Benchmark Execution

### Running Benchmarks

```bash
# Run all benchmarks
make benchmark

# Run specific benchmark category
pytest tests/benchmarks/test_embedding_perf.py -v
pytest tests/benchmarks/test_retrieval_quality.py -v

# Run with profiling
pytest tests/benchmarks/ --profile-svg

# Run load tests
locust -f tests/load/locustfile.py --host=http://localhost:8000
k6 run tests/load/k6_script.js
```

### Makefile Targets

```makefile
# Makefile

.PHONY: benchmark benchmark-unit benchmark-quality benchmark-load

benchmark: benchmark-unit benchmark-quality
	@echo "All benchmarks complete"

benchmark-unit:
	pytest tests/benchmarks/test_*_perf.py -v --benchmark-only

benchmark-quality:
	pytest tests/benchmarks/test_*_quality.py -v

benchmark-load:
	locust -f tests/load/locustfile.py --host=http://localhost:8000 -u 100 -r 10 --run-time 5m

benchmark-report:
	python scripts/generate_benchmark_report.py --output benchmark_report.md
```

---

## Summary

This benchmarking strategy ensures:

1. **Performance Validation**: All latency and throughput targets are measurable
2. **Quality Assurance**: Retrieval and generation quality is quantified
3. **Regression Detection**: Continuous benchmarking catches performance degradation
4. **Load Validation**: System behavior under load is validated
5. **Production Readiness**: Benchmarks simulate real-world conditions

The benchmarks serve as both:
- **Development targets** during implementation
- **Quality gates** in CI/CD
- **Portfolio evidence** for Principal AI Engineer interviews
