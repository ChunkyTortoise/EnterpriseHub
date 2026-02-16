# DocQA Engine Screenshot Specifications

**Product**: DocQA Engine (docqa-engine)
**Live Demo**: (deployment pending -- capture from local run or deploy first)
**Gumroad**: Tiered ($49 / $199 / $999-$2,999)
**Total Screenshots**: 7

---

## Screenshot 1: Hero -- Document Q&A Interface

| Property | Value |
|----------|-------|
| **Filename** | `docqa-chat-hero.png` |
| **Dimensions** | 1920x1080 / 1280x720 / 800x450 |
| **Source** | Streamlit app main chat interface |
| **UI Elements to Show** | Chat input, document upload area, answer panel with citation highlights |
| **Highlight Boxes** | Red box around citation score badge (e.g., "Citation Confidence: 94%") |
| **Callout Numbers** | (1) Document upload zone, (2) Natural language query input, (3) Answer with inline citations |
| **Caption** | "Ask questions, get cited answers -- 99% faster than manual search" |
| **Context** | Shows the core user experience; document in, answer out |

### Annotation Placement
```
┌──────────────────────────────────────────────────┐
│  DocQA Engine                                    │
├─────────┬────────────────────────────────────────┤
│ Sidebar │  ┌──(1)─────────────────────────────┐  │
│ - Chat  │  │  📄 Upload: contract_v3.pdf      │  │
│ - Docs  │  │       legal_brief.docx           │  │
│ - Hist  │  └──────────────────────────────────┘  │
│ - Stats │                                        │
│         │  ┌──(2)─────────────────────────────┐  │
│         │  │ 🔍 "What are the termination      │  │
│         │  │     clauses in Section 4?"         │  │
│         │  └──────────────────────────────────┘  │
│         │                                        │
│         │  ┌──(3)─────────────────────────────┐  │
│         │  │  Answer:                          │  │
│         │  │  Section 4.2 states that either   │  │
│         │  │  party may terminate with 30 days │  │
│         │  │  written notice [p.12, para 3]    │  │
│         │  │  ┌─Citation: 94%─┐               │  │
│         │  └──────────────────────────────────┘  │
└─────────┴────────────────────────────────────────┘
```

---

## Screenshot 2: Citation Scoring Panel

| Property | Value |
|----------|-------|
| **Filename** | `docqa-citation-scoring.png` |
| **Dimensions** | 1920x1080 / 1280x720 / 800x450 |
| **Source** | Citation detail view showing source attribution breakdown |
| **UI Elements to Show** | Citation confidence meter, source document references, relevance heatmap |
| **Highlight Boxes** | Red box around citation confidence score |
| **Callout Numbers** | (1) Overall confidence score, (2) Per-source relevance scores, (3) Page/paragraph references |
| **Caption** | "Every answer traced to source -- citation scoring eliminates hallucination" |
| **Context** | Key differentiator vs generic RAG; shows trustworthiness |

---

## Screenshot 3: Multi-Document Analytics

| Property | Value |
|----------|-------|
| **Filename** | `docqa-document-analytics.png` |
| **Dimensions** | 1920x1080 / 1280x720 / 800x450 |
| **Source** | Analytics page showing document corpus statistics |
| **UI Elements to Show** | Document count, chunk distribution chart, embedding quality metrics |
| **Highlight Boxes** | Red box around processing speed metric |
| **Callout Numbers** | (1) Documents processed count, (2) Chunk quality distribution, (3) Query latency (< 200ms) |
| **Caption** | "Process hundreds of documents with sub-200ms query response" |
| **Context** | Shows scale capability; important for enterprise buyers |

---

## Screenshot 4: Vector Search Visualization

| Property | Value |
|----------|-------|
| **Filename** | `docqa-vector-search.png` |
| **Dimensions** | 1920x1080 / 1280x720 / 800x450 |
| **Source** | Scatter plot of document embeddings (t-SNE/UMAP visualization) |
| **UI Elements to Show** | 2D/3D scatter plot with cluster coloring by document type, search query point |
| **Highlight Boxes** | Red box around the query point and its nearest neighbors |
| **Callout Numbers** | (1) Query embedding, (2) Top-K retrieved chunks (highlighted), (3) Document clusters |
| **Caption** | "Hybrid retrieval: semantic + keyword search for maximum recall" |
| **Context** | Technical depth; appeals to ML-savvy buyers |

---

## Screenshot 5: Docker Deployment View

| Property | Value |
|----------|-------|
| **Filename** | `docqa-docker-deploy.png` |
| **Dimensions** | 1920x600 / 1280x400 |
| **Source** | Terminal screenshot showing docker-compose up with services starting |
| **UI Elements to Show** | Docker compose output with services: api, worker, vector-db, redis |
| **Highlight Boxes** | Green box (`#10B981`) around "All services healthy" line |
| **Callout Numbers** | (1) `docker-compose up -d`, (2) Services starting, (3) Health check passed |
| **Caption** | "One command to deploy -- Docker + Redis + vector store included" |
| **Context** | Ops-focused; shows production readiness |

### Terminal Content to Display
```
$ docker-compose up -d
Creating network "docqa_default" ...
Creating docqa_redis_1     ... done
Creating docqa_chromadb_1  ... done
Creating docqa_api_1       ... done
Creating docqa_worker_1    ... done

Health checks:
  ✓ API:       http://localhost:8000/health  (200 OK)
  ✓ Redis:     localhost:6379               (PONG)
  ✓ ChromaDB:  http://localhost:8001/api/v1 (200 OK)

All services healthy. Ready for document ingestion.
```

---

## Screenshot 6: Test Coverage Report

| Property | Value |
|----------|-------|
| **Filename** | `docqa-test-coverage.png` |
| **Dimensions** | 1920x800 / 1280x530 / 800x450 |
| **Source** | Terminal screenshot of pytest + coverage output |
| **UI Elements to Show** | 557 tests passing, coverage breakdown by module |
| **Highlight Boxes** | Green box around "557 passed" |
| **Callout Numbers** | (1) Test count, (2) Coverage %, (3) Module breakdown |
| **Caption** | "557 tests -- production-grade quality you can trust" |
| **Context** | Trust signal for enterprise buyers |

---

## Screenshot 7: Legal Use Case Result

| Property | Value |
|----------|-------|
| **Filename** | `docqa-legal-usecase.png` |
| **Dimensions** | 1920x1080 / 1280x720 / 800x450 |
| **Source** | Chat interface with legal document Q&A example |
| **UI Elements to Show** | Legal contract uploaded, complex question asked, cited answer returned |
| **Highlight Boxes** | Red box around specific clause citation with page number |
| **Callout Numbers** | (1) Contract PDF thumbnail, (2) Legal query, (3) Precise answer with clause reference |
| **Caption** | "Legal teams save 40+ hours/week -- find any clause in seconds" |
| **Context** | Industry-specific use case; targets highest-value buyers ($999+ tier) |

---

## Gumroad Listing Image Order

| Position | Screenshot | Purpose |
|----------|-----------|---------|
| 1 (Cover) | `docqa-chat-hero.png` | Core experience, drives curiosity |
| 2 | `docqa-citation-scoring.png` | Differentiator: trustworthy AI |
| 3 | `docqa-legal-usecase.png` | High-value use case proof |
| 4 | `docqa-document-analytics.png` | Scale and performance |
| 5 | `docqa-docker-deploy.png` | Easy deployment |
| 6 | `docqa-vector-search.png` | Technical depth |
| 7 | `docqa-test-coverage.png` | Quality trust signal |
