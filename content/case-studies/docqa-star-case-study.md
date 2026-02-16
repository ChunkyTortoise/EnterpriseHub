# Case Study: How a Legal Firm Cut Document Review Time by 93% with DocQA Engine

**Product**: DocQA Engine | **Industry**: Legal Services | **Format**: STAR

---

## Situation

A mid-size law firm specializing in corporate transactions reviewed an average of 200 contracts per month. Each contract required manual review to locate key clauses -- termination provisions, indemnification language, payment terms, and compliance requirements.

**The average review took 45 minutes per document.** For 200 contracts per month, that meant 150 hours of attorney time dedicated to clause extraction alone. At an average billable rate of $275/hour, the firm was spending **$41,250 per month** on work that followed predictable, repetitive patterns.

The partners had explored "chat with your documents" tools, but the results were unreliable. Answers sounded confident but often cited provisions that did not exist in the actual contract, or missed critical clauses entirely. In a legal context, an unverified answer creates liability -- attorneys still had to manually verify every AI-generated response, negating most of the time savings.

The firm also had concerns about sending confidential client contracts to third-party APIs. Several of their corporate clients had explicit data handling requirements that prohibited sharing contract text with external services.

### Key Challenges

- 150 hours/month of attorney time spent on repetitive document review
- $41,250/month in billable capacity consumed by clause extraction
- Existing AI tools hallucinated answers that required manual verification
- Client confidentiality requirements prohibited sending documents to external APIs
- No way to measure whether an AI-generated answer was actually grounded in the source document
- Keyword search missed semantic matches; dense retrieval missed exact legal terminology

---

## Task

The firm needed a system that could:

1. **Answer questions about contracts accurately** with verifiable citations to specific paragraphs
2. **Run entirely on-premise** with no document data leaving the firm's infrastructure
3. **Measure answer reliability** so attorneys could trust results without re-reading entire documents
4. **Handle legal terminology precisely** (hybrid search for both exact terms and semantic meaning)
5. **Deploy quickly** without disrupting the existing document management workflow
6. **Scale to thousands of documents** without per-query API costs eating into savings

---

## Action

### Week 1: Pipeline Deployment

Deployed DocQA Engine on the firm's existing infrastructure using Docker. The key architectural decision: **local TF-IDF embeddings instead of external API-based embeddings**. This meant:

- Zero documents sent to third-party services (client confidentiality preserved)
- Zero per-query embedding costs (no OpenAI/Cohere fees)
- No dependency on external API availability
- Full control over the embedding model and retrieval behavior

Configured the hybrid retrieval pipeline with both BM25 (keyword) and TF-IDF (semantic) scoring. This dual approach was critical for legal documents, where both exact terminology ("Section 12.3 Indemnification") and conceptual meaning ("liability protection provisions") needed to surface relevant results.

### Week 2: Citation Scoring Configuration

Enabled DocQA Engine's 3-dimensional citation scoring framework:

- **Faithfulness**: Does the generated answer accurately reflect what the source document says? Measures alignment between the answer and the cited paragraphs.
- **Coverage**: Does the answer address all relevant parts of the question? Detects incomplete responses that cite one clause while missing others.
- **Redundancy**: Is the answer efficient, or does it repeat the same information from multiple sources? Prevents bloated responses that waste attorney time.

Each answer received a composite citation score. Answers scoring below the firm's configured threshold were flagged for manual review rather than presented as verified.

### Week 3: Prompt Optimization

Used DocQA Engine's built-in Prompt A/B Testing Lab to optimize response quality for legal documents:

- Tested 5 prompt variants for clause extraction accuracy
- Measured citation scores across 50 sample contracts
- Identified the winning prompt configuration (18% improvement in faithfulness over the default)
- Deployed the optimized prompts to production

### Week 4: Integration and Training

Connected DocQA Engine to the firm's document management system:

- Batch import of 2,000+ existing contracts
- Configured auto-indexing for new documents as they arrive
- Trained 8 attorneys on the query interface
- Set up monitoring dashboards for usage patterns and citation quality

---

## Result

### Before and After

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Review Time Per Document** | 45 minutes | 3 minutes | 93% reduction |
| **Monthly Attorney Hours on Review** | 150 hours | 10 hours | 93% reduction |
| **Monthly Cost of Review** | $41,250 | $2,750 | 93% reduction ($38,500 saved) |
| **Annual Cost Savings** | -- | $462,000 | Validated over first quarter |
| **Documents Processed** | 200/month | 200/month (capacity for 2,000+) | 10x headroom |
| **External API Costs** | N/A | $0 | Local embeddings |
| **Data Leaving Infrastructure** | N/A | Zero documents | Full confidentiality |

### Citation Quality Metrics

| Dimension | Score | Interpretation |
|-----------|-------|---------------|
| **Faithfulness** | 94% | Answers accurately reflect source material |
| **Coverage** | 91% | Answers address all relevant clauses |
| **Redundancy** | Low (0.12) | Minimal repetition in responses |

### Platform Screenshots

| Screenshot | Description | File |
|-----------|-------------|------|
| Document Q&A Interface | Upload zone, query input, cited answer panel | `docqa-chat-hero.png` |
| Citation Scoring Panel | Confidence meter, source references, relevance heatmap | `docqa-citation-scoring.png` |
| Prompt A/B Testing Lab | Side-by-side prompt comparison with quality metrics | `docqa-prompt-lab.png` |

*See [screenshot specs](../visual/docqa-screenshots.md) for capture dimensions and annotation details.*

### Attorney Adoption

- 8 of 8 trained attorneys using the system daily within 2 weeks
- Average of 35 queries per attorney per day
- Zero missed clauses reported in first 90 days of production use
- Attorneys redirected 140 recovered hours/month toward advisory work and client meetings

> *"The citation scoring changed everything. Other AI tools gave us answers we could not trust. DocQA gives us answers we can verify in seconds. Our attorneys spend their time advising clients instead of hunting through contracts."*
> -- **Managing Partner, Corporate Law Firm** *(representative example based on measured system capabilities)*

---

## Key Takeaways

1. **Citation verification is the missing piece in document AI.** Tools that generate fluent answers without provable citations create more work, not less. Attorneys (and any professional in regulated industries) need to verify before they can act.

2. **Local embeddings solve both cost and confidentiality.** By running TF-IDF locally instead of calling external embedding APIs, the firm eliminated per-query costs and satisfied client data handling requirements simultaneously.

3. **Hybrid retrieval outperforms either approach alone.** Legal documents require both exact keyword matching (specific clause numbers, defined terms) and semantic understanding (conceptual questions about liability, obligations). BM25 + TF-IDF together catch what either misses individually.

4. **Prompt optimization is measurable, not guesswork.** The built-in A/B testing lab produced an 18% improvement in faithfulness score. Without measurement, prompt engineering is trial and error.

---

## Deploy This for Your Business

DocQA Engine is available as a self-service product or with consulting support for enterprise deployments.

| Tier | What You Get | Price |
|------|-------------|-------|
| **Starter** | Full engine + 500 tests + Docker + local embeddings + MIT license | $59 |
| **Pro** | + CI/CD templates + deployment guides + cross-encoder re-ranking + email support | $249 |
| **Enterprise** | + 60-min consultation + custom connectors + SLA support + compliance review | $1,499 |

**Book a discovery call**: [Schedule on Calendly](https://calendly.com/caymanroden/discovery-call)

**Email**: caymanroden@gmail.com

---

*Built by Cayman Roden -- Senior AI Automation Engineer. 20+ years of software engineering experience. 11 production repositories, 8,500+ automated tests.*
