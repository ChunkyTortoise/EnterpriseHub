# Case Study: Financial Document Q&A for an Investment Research Firm

## Client Profile

**Company**: Meridian Capital Research (anonymized)
**Industry**: Investment Research / Asset Management
**Team Size**: 25 analysts, 8 quant researchers
**Challenge**: Rapid Q&A across SEC filings, earnings transcripts, and research reports

---

## The Challenge

Meridian's analysts review 200+ SEC filings per quarter (10-Ks, 10-Qs, 8-Ks, proxy statements) plus hundreds of earnings call transcripts. Each filing averages 150-300 pages. Key challenges:

- **Research hours per filing**: An analyst spent 8 hours reading a 10-K to answer 15-20 specific questions
- **Cross-filing comparison**: Comparing revenue recognition policies across 12 competitors took 2 full days
- **Earnings transcript mining**: Extracting management guidance from 50+ transcripts per quarter was a week-long manual effort
- **Cost**: Their existing AI document tool charged $180 per 1,000 queries, costing $36,000/year

Their workflow was: read entire document, take notes, formulate answers, double-check citations. DocQA Engine replaced the "read entire document" step with targeted retrieval.

### Pain Points

| Problem | Impact |
|---------|--------|
| 8 hours per filing for 15-20 questions | 200 filings x 8 hours = 1,600 analyst-hours/quarter |
| Cross-filing comparison manual | 2 days per competitive analysis |
| Earnings guidance extraction manual | 1 week per quarter |
| $180/1K queries on existing tool | $36,000 annual spend |
| No citation verification | 2 hours verifying AI answers per report |

---

## The Solution: DocQA Engine for Financial Intelligence

Meridian deployed DocQA Engine's pipeline with batch processing, evaluator metrics, and the prompt engineering lab.

### Step 1: Batch Ingestion of SEC Filings

DocQA Engine's batch processor handles parallel document ingestion, critical when loading 200+ filings:

```python
from docqa_engine.pipeline import DocQAPipeline
from docqa_engine.batch import BatchProcessor

pipeline = DocQAPipeline(vector_backend="memory")
batch = BatchProcessor(pipeline=pipeline, max_workers=4)

# Parallel ingest of all Q4 10-K filings
results = await batch.ingest_directory(
    path="sec_filings/2025_Q4/",
    file_types=["pdf", "txt"],
    batch_size=20
)
print(f"Ingested {results.total_documents} filings, {results.total_chunks} chunks")
# Ingested 215 filings, 42,800 chunks
```

### Step 2: Targeted Financial Question Answering

Instead of reading entire 10-Ks, analysts ask specific questions and get cited answers:

```python
# Analyst workflow: targeted questions against full filing corpus
questions = [
    "What was AAPL's revenue recognition policy change in FY2025?",
    "What is MSFT's goodwill impairment risk disclosure?",
    "Compare AMZN and GOOG capital expenditure guidance for 2026",
    "What material weaknesses did META disclose in internal controls?",
]

for q in questions:
    answer = await pipeline.ask(q, top_k=10, method="hybrid")
    print(f"Q: {q}")
    print(f"A: {answer.text}")
    print(f"Sources: {[c.source for c in answer.citations]}")
    print(f"Faithfulness: {answer.citation_scores.faithfulness:.2f}")
    print("---")
```

The hybrid retrieval pipeline (BM25 + Dense + RRF) was particularly effective for financial terminology. A query about "revenue recognition" matched passages discussing "ASC 606 adoption," "performance obligation timing," and "contract revenue allocation" -- terms that pure keyword search would miss.

### Step 3: Evaluator for Retrieval Quality Assurance

Meridian's quant team used DocQA Engine's evaluator to measure and tune retrieval quality:

```python
from docqa_engine.evaluator import RetrievalEvaluator

evaluator = RetrievalEvaluator()

# Define test queries with known relevant passages
eval_cases = [
    {
        "query": "AAPL revenue recognition policy",
        "relevant_chunk_ids": ["10k_aapl_chunk_142", "10k_aapl_chunk_143"]
    },
    # ... 50 evaluation cases
]

metrics = evaluator.evaluate(pipeline, eval_cases)
print(f"MRR: {metrics.mrr:.3f}")        # Mean Reciprocal Rank
print(f"NDCG@5: {metrics.ndcg_at_5:.3f}")  # Normalized DCG
print(f"Precision@5: {metrics.precision_at_5:.3f}")
print(f"Recall@5: {metrics.recall_at_5:.3f}")
print(f"Hit Rate@5: {metrics.hit_rate_at_5:.3f}")
```

The evaluator supports MRR, NDCG@K, Precision@K, Recall@K, and Hit Rate -- the standard information retrieval metrics that Meridian's quant team was familiar with.

### Step 4: Prompt Engineering Lab for Answer Quality

Meridian used DocQA Engine's prompt lab to A/B test different prompt strategies for financial analysis:

```python
from docqa_engine.prompt_lab import PromptLibrary, compare_prompts

library = PromptLibrary()

# Register competing prompt strategies
library.add_template(
    name="concise_analyst",
    template="Based on the provided SEC filing excerpts, answer concisely: {{question}}"
)
library.add_template(
    name="detailed_with_caveats",
    template=(
        "You are a financial analyst. Based on the SEC filing excerpts below, "
        "provide a detailed answer to: {{question}}. "
        "Include specific numbers, dates, and note any forward-looking statement caveats."
    )
)

# Side-by-side comparison
comparison = compare_prompts(
    library=library,
    templates=["concise_analyst", "detailed_with_caveats"],
    query="What is AAPL's expected capital allocation for FY2026?",
    context=retrieved_passages
)
# Returns both answers for quality comparison
```

After testing 8 prompt variations, Meridian found that the "detailed_with_caveats" prompt produced answers that matched their internal report format, reducing analyst editing time by 60%.

### Step 5: Cost Tracking and Optimization

DocQA Engine's cost tracker revealed optimization opportunities:

```python
from docqa_engine.cost_tracker import CostTracker

tracker = CostTracker()

# Track cost per query across the quarter
quarterly_report = tracker.get_summary()
print(f"Total queries: {quarterly_report.total_queries}")
print(f"Total cost: ${quarterly_report.total_cost:.2f}")
print(f"Cost per query: ${quarterly_report.cost_per_query:.4f}")
print(f"Token efficiency: {quarterly_report.avg_tokens_per_query}")
```

### Step 6: Multi-Provider Model Comparison

Meridian tested different LLM providers for answer generation quality using DocQA Engine's model-agnostic architecture:

From DocQA Engine's benchmarks:

| Provider | Model | Faithfulness | Coverage | Latency | Cost/1K tokens |
|----------|-------|--------------|----------|---------|----------------|
| Anthropic | Claude 3.5 Sonnet | 0.91 | 0.88 | 1.2s | $0.003 |
| OpenAI | GPT-4o | 0.89 | 0.86 | 0.9s | $0.005 |
| Google | Gemini 1.5 Pro | 0.87 | 0.84 | 1.1s | $0.00125 |
| OpenAI | GPT-4o Mini | 0.84 | 0.81 | 0.4s | $0.0006 |

Meridian selected GPT-4o for routine queries (best latency/quality tradeoff) and Claude 3.5 Sonnet for compliance-critical answers (highest faithfulness at 0.91).

---

## Results

### Analyst Productivity

| Metric | Before DocQA | After DocQA | Change |
|--------|-------------|-------------|--------|
| Hours per filing (15-20 questions) | 8 hours | 45 minutes | **-91%** |
| Quarterly analyst-hours on filings | 1,600 | 150 | **-91%** |
| Cross-filing comparison | 2 days | 30 minutes | **-97%** |
| Earnings guidance extraction | 1 week | 4 hours | **-90%** |

### Cost

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Cost per 1,000 queries | $180 | $24 | **-87%** |
| Annual document Q&A spend | $36,000 | $4,800 | **-87%** |
| Answer verification time | 2 hours/report | 20 min/report | **-83%** |

### Quality

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Relevant results in top 5 | 38% | 86% | **+126%** |
| Citation faithfulness | N/A | 0.89 (GPT-4o) | **New capability** |
| Financial term coverage | Keyword only | Semantic + keyword | **Comprehensive** |

---

## Implementation Timeline

| Week | Activity | Outcome |
|------|----------|---------|
| 1 | Batch ingestion of 200+ SEC filings | 42,800 chunks indexed |
| 1 | Hybrid retrieval tuning for financial terminology | Semantic + keyword active |
| 2 | Evaluator setup with 50 benchmark queries | MRR/NDCG baselines |
| 2 | Prompt lab A/B testing (8 prompt variants) | Optimal prompt selected |
| 3 | Multi-provider testing (Claude vs GPT-4o) | Provider routing decided |
| 3 | Cost tracking and budget alerts | Real-time spend visibility |
| 4 | Analyst training and feedback integration | Production deployment |

**Total deployment**: 4 weeks.

---

## Key Takeaways

1. **Hybrid retrieval handles financial jargon naturally**. "Revenue recognition" matched "ASC 606 adoption" and "performance obligation timing" without manual synonym dictionaries.

2. **Evaluator metrics build quant team trust**. MRR, NDCG, and Precision@K are metrics quant researchers already understand, making adoption straightforward.

3. **Prompt engineering lab saved 60% editing time**. Testing 8 prompt variants found one that matched the firm's internal report format.

4. **91% reduction in research hours is real**. 8 hours per filing dropped to 45 minutes -- confirmed across 200+ filings over one quarter.

5. **Model-agnostic design enables cost/quality tradeoffs**. Using GPT-4o for routine queries and Claude for compliance answers optimized both quality and cost.

---

## About DocQA Engine

DocQA Engine provides 550+ automated tests, hybrid retrieval (BM25 + Dense + RRF), citation scoring, batch processing, evaluator metrics (MRR, NDCG, P@K), prompt engineering lab, and multi-provider support. Designed for high-volume document intelligence in regulated industries.

- **Repository**: [github.com/ChunkyTortoise/docqa-engine](https://github.com/ChunkyTortoise/docqa-engine)
- **Live Demo**: [ct-document-engine.streamlit.app](https://ct-document-engine.streamlit.app)
- **Query latency**: <100ms for 10K document corpus
- **Tests**: 550+ across 26 test files
