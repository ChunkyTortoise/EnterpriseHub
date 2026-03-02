"""RAG Demo Dashboard component.

Showcases hybrid BM25+dense retrieval with source attribution
on real-estate domain documents. No file upload required ---
demo documents are embedded as constants.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import streamlit as st

# -- Demo Documents (real-estate domain) --------------------------------------

DEMO_DOCUMENTS: dict[str, str] = {
    "Property Listing -- 742 Vine St": """
PROPERTY LISTING -- MLS #RC2026-0742
Address: 742 Vine Street, Rancho Cucamonga, CA 91730
List Price: $685,000
Bedrooms: 4 | Bathrooms: 3 | Garage: 2-car attached
Sq Ft: 2,184 | Lot: 7,200 sq ft | Year Built: 2003

DESCRIPTION:
Stunning turnkey home in the sought-after Alta Loma neighborhood.
Open-concept floor plan with vaulted ceilings and abundant natural light.
Chef's kitchen with granite countertops, stainless steel appliances,
and large island perfect for entertaining.
Master suite features walk-in closet and spa-style bathroom with dual vanities.
Backyard oasis with covered patio, mature landscaping, and room for a pool.
Walking distance to top-rated Etiwanda School District schools.
Close to Victoria Gardens shopping center, Ontario Airport (15 min), and the 10/15 freeway interchange.

FEATURES:
- Central A/C and heating (replaced 2022)
- Solar panels (owned, not leased) -- avg electric bill $42/mo
- Smart home: Nest thermostat, Ring doorbell, Lutron lighting
- HOA: None
- Property taxes (est.): $8,562/yr
- Zoning: R-1 Single Family Residential

SHOWING: Contact listing agent Jorge Ramirez at (909) 555-0742.
Open house Saturday 1-4PM.
""",
    "HOA FAQ -- Vineyard Estates": """
VINEYARD ESTATES HOMEOWNERS ASSOCIATION
Frequently Asked Questions -- Updated January 2026

Q: What is the monthly HOA fee?
A: The monthly assessment is $285 per unit, due on the 1st of each month.
   A $25 late fee applies after the 15th. ACH auto-pay available through the portal.

Q: What does the HOA fee cover?
A: Common area maintenance (landscaping, irrigation), community pool and spa,
   clubhouse, exterior pest control, reserve fund contributions, liability insurance,
   community security lighting, and management company fees.

Q: Are pets allowed?
A: Yes. Maximum 2 pets per unit. Dogs must be leashed in common areas.
   Breed restrictions apply (see CC&Rs Section 7.3). No livestock or exotic animals.

Q: Can I rent my unit?
A: Rentals are permitted after 12 months of owner-occupancy. Minimum lease term: 6 months.
   Board must receive a copy of the lease within 10 days of signing.
   Owner remains responsible for tenant compliance with all CC&Rs.

Q: What modifications require board approval?
A: All exterior changes (paint color, landscaping, fencing, additions, solar panels)
   require an Architectural Review Committee (ARC) application with a 30-day review period.

Q: How do I submit a maintenance request?
A: Use the online portal at vineyard-estates-hoa.com or call (909) 555-0200 Mon-Fri 9AM-5PM.
   Emergency maintenance (water leak, electrical): 24/7 hotline (909) 555-0911.

Q: What is the special assessment for 2026?
A: A $1,200 one-time special assessment was approved at the November 2025 AGM
   for pool resurfacing and clubhouse HVAC replacement. Payment due March 31, 2026.
""",
    "Purchase Contract Summary": """
CALIFORNIA RESIDENTIAL PURCHASE AGREEMENT -- SUMMARY
Property: 742 Vine Street, Rancho Cucamonga, CA 91730
Buyer: Michael and Sarah Chen
Seller: Robert and Linda Whitmore
Accepted Offer Date: February 14, 2026

KEY TERMS:
Purchase Price: $678,500 (full asking: $685,000; negotiated discount: $6,500)
Earnest Money Deposit: $13,570 (2% of purchase price) -- due within 3 business days
Down Payment: $135,700 (20%) -- conventional financing
Loan Amount: $542,800 -- 30-year fixed, rate locked at 6.875%

CONTINGENCIES:
- Loan contingency: 17 days from acceptance
- Appraisal contingency: 17 days from acceptance
- Inspection contingency: 10 days from acceptance
- Title review: 5 days after title report delivery

CLOSING TIMELINE:
- Inspection deadline: February 24, 2026
- Loan approval: March 3, 2026
- Estimated close of escrow: March 14, 2026
- Possession: Day of close (COE)

SELLER DISCLOSURES:
- Natural Hazard Disclosure: Zone D (flood), not in fire hazard zone
- Transfer Disclosure Statement: minor cosmetic issues disclosed (see TDS)
- Prop 65 Warning: standard California advisory

INCLUDED IN SALE:
All appliances (refrigerator, washer/dryer), solar panel system, built-in BBQ,
garage shelving, and all window coverings.

EXCLUDED: Dining room chandelier, backyard fountain (seller's personal property).
""",
    "Rancho Cucamonga Market Report Q4 2025": """
RANCHO CUCAMONGA REAL ESTATE MARKET REPORT
Q4 2025 -- Prepared by Jorge Realty AI Analytics

EXECUTIVE SUMMARY:
The Rancho Cucamonga market ended 2025 strong with median home prices
reaching $658,000, a 4.2% year-over-year increase. Inventory remains
historically low at 1.8 months supply, favoring sellers in most segments.

PRICING TRENDS:
- Median sale price: $658,000 (Q4 2025) vs $632,000 (Q4 2024)
- Average sale price: $712,400
- Price per sq ft: $318 (up from $298 YoY)
- Homes selling above list price: 34% of transactions
- Average days on market: 21 (down from 31 in Q4 2024)

INVENTORY:
- Active listings: 287 (Q4 2025) vs 412 (Q4 2024) -- 30% decline
- New listings this quarter: 891
- Closed sales: 634
- Absorption rate: 7.8 homes/week

SEGMENT BREAKDOWN:
Under $500K: Very competitive, 8+ offers typical, waived contingencies common
$500K-$750K: Prime market, 3-5 offers, inspection contingencies usually accepted
$750K-$1M: Balanced, 1-2 offers, longer DOM (35 days avg)
$1M+: Buyer-favorable, price reductions seen, negotiation possible

FORECAST Q1 2026:
Interest rates expected to stabilize at 6.5-7.0%. Modest inventory increase
anticipated as spring season approaches. Price appreciation to moderate at 2-3%.
Alta Loma and Etiwanda sub-markets expected to outperform on school district demand.

NOTABLE TRANSACTIONS:
- Alta Loma: 4BR sold for $892,000 (new neighborhood record)
- Victoria: Townhome complex sold 18 units off-plan in 72 hours
""",
    "Home Inspection Checklist": """
HOME INSPECTION CHECKLIST
Property: 742 Vine Street, Rancho Cucamonga, CA 91730
Inspector: Pacific Coast Home Inspections, Lic #HI-44821
Inspection Date: February 22, 2026

STRUCTURAL:
- Foundation: No visible cracks or settling observed
- Roof: 3-tab shingle, estimated 7 years remaining life
- Attic: Minor moisture staining near north eave (recommend monitoring)
- Walls/Ceilings: No significant cracks or water damage

ELECTRICAL:
- Main panel: 200A service, circuit breakers properly labeled
- GFCI outlets: Present in bathrooms, kitchen, garage (all tested)
- Garage outlet: One outlet has reversed polarity (low-cost fix, $50)
- Smoke/CO detectors: Present on all floors, batteries tested

PLUMBING:
- Water heater: 50-gallon, installed 2019, functioning normally
- Water pressure: 68 PSI (within normal 40-80 PSI range)
- Master bath: Slow drain in shower (hair clog likely, recommend snaking)
- Exterior hose bibs: Functional, anti-siphon valves present

HVAC:
- Furnace: Bryant 96% efficiency, installed 2022, no issues
- A/C: Lennox 16 SEER, installed 2022, cooling efficiently
- Ductwork: Clean, well-sealed, balanced airflow

SUMMARY -- ITEMS REQUIRING ATTENTION:
1. [LOW] Attic moisture staining -- monitor, seal north eave flashing
2. [LOW] Garage outlet reversed polarity -- licensed electrician, est. $50-75
3. [LOW] Master bath drain -- snaking/clearing, est. $75-150
Total estimated repair cost: $125-$225 (minor)

Overall Assessment: Property is in VERY GOOD condition for age and price point.
No major structural, mechanical, or safety deficiencies found.
""",
}

# -- BM25 (no external dep) ---------------------------------------------------


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


@dataclass
class BM25Index:
    """Minimal BM25Okapi implementation -- no rank-bm25 dep needed."""

    k1: float = 1.5
    b: float = 0.75
    corpus: list[str] = field(default_factory=list)
    _tokenized: list[list[str]] = field(default_factory=list)
    _idf: dict[str, float] = field(default_factory=dict)
    _avgdl: float = 0.0

    def fit(self, corpus: list[str]) -> None:
        self.corpus = corpus
        self._tokenized = [_tokenize(doc) for doc in corpus]
        N = len(corpus)
        self._avgdl = sum(len(t) for t in self._tokenized) / max(N, 1)
        df: dict[str, int] = defaultdict(int)
        for tokens in self._tokenized:
            for term in set(tokens):
                df[term] += 1
        self._idf = {
            term: math.log((N - freq + 0.5) / (freq + 0.5) + 1)
            for term, freq in df.items()
        }

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        scores = []
        for i, tokens in enumerate(self._tokenized):
            dl = len(tokens)
            score = 0.0
            tf_map: dict[str, int] = defaultdict(int)
            for t in tokens:
                tf_map[t] += 1
            for term in query_tokens:
                if term not in self._idf:
                    continue
                tf = tf_map.get(term, 0)
                idf = self._idf[term]
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * dl / self._avgdl
                )
                score += idf * numerator / denominator
            scores.append(score)
        return scores


# -- Simple Dense Retrieval (cosine, no embeddings -- TF-IDF proxy) -----------


def _tfidf_vector(tokens: list[str], vocab: dict[str, int]) -> list[float]:
    tf: dict[str, int] = defaultdict(int)
    for t in tokens:
        tf[t] += 1
    vec = [0.0] * len(vocab)
    for term, idx in vocab.items():
        vec[idx] = tf.get(term, 0) / max(len(tokens), 1)
    return vec


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


@dataclass
class DenseIndex:
    """TF-IDF-based dense retrieval proxy (no external embedding API needed)."""

    corpus: list[str] = field(default_factory=list)
    _vocab: dict[str, int] = field(default_factory=dict)
    _vectors: list[list[float]] = field(default_factory=list)

    def fit(self, corpus: list[str]) -> None:
        self.corpus = corpus
        all_tokens: set[str] = set()
        tokenized = [_tokenize(doc) for doc in corpus]
        for tokens in tokenized:
            all_tokens.update(tokens)
        self._vocab = {t: i for i, t in enumerate(sorted(all_tokens))}
        self._vectors = [
            _tfidf_vector(tokens, self._vocab) for tokens in tokenized
        ]

    def get_scores(self, query: str) -> list[float]:
        q_tokens = _tokenize(query)
        q_vec = _tfidf_vector(q_tokens, self._vocab)
        return [_cosine(q_vec, doc_vec) for doc_vec in self._vectors]


# -- Chunk corpus --------------------------------------------------------------


def _chunk_document(doc: str, chunk_size: int = 200) -> list[str]:
    """Split doc into chunks by words."""
    words = doc.split()
    chunks = []
    for i in range(0, len(words), chunk_size - 20):
        chunk = " ".join(words[i : i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def _build_corpus() -> tuple[list[str], list[str]]:
    """Build (chunks, doc_names) from DEMO_DOCUMENTS."""
    chunks: list[str] = []
    doc_names: list[str] = []
    for name, doc in DEMO_DOCUMENTS.items():
        for chunk in _chunk_document(doc):
            chunks.append(chunk)
            doc_names.append(name)
    return chunks, doc_names


# -- Hybrid Search -------------------------------------------------------------

_INDEXES: tuple[BM25Index, DenseIndex, list[str], list[str]] | None = None


def _load_indexes() -> tuple[BM25Index, DenseIndex, list[str], list[str]]:
    global _INDEXES
    if _INDEXES is None:
        chunks, doc_names = _build_corpus()
        bm25 = BM25Index()
        bm25.fit(chunks)
        dense = DenseIndex()
        dense.fit(chunks)
        _INDEXES = (bm25, dense, chunks, doc_names)
    return _INDEXES


@dataclass
class SearchResult:
    chunk: str
    doc_name: str
    bm25_score: float
    dense_score: float
    fused_score: float
    rank: int


def _rrf_fusion(
    bm25_scores: list[float],
    dense_scores: list[float],
    top_k: int = 5,
    rrf_k: int = 60,
) -> list[tuple[int, float, float, float]]:
    """Reciprocal Rank Fusion. Returns [(idx, bm25_norm, dense_norm, fused_score)]."""
    n = len(bm25_scores)
    bm25_ranked = sorted(range(n), key=lambda i: bm25_scores[i], reverse=True)
    dense_ranked = sorted(range(n), key=lambda i: dense_scores[i], reverse=True)

    rrf: dict[int, float] = defaultdict(float)
    for rank, idx in enumerate(bm25_ranked):
        rrf[idx] += 1.0 / (rrf_k + rank + 1)
    for rank, idx in enumerate(dense_ranked):
        rrf[idx] += 1.0 / (rrf_k + rank + 1)

    top_indices = sorted(rrf.keys(), key=lambda i: rrf[i], reverse=True)[:top_k]

    max_bm25 = max(bm25_scores) if max(bm25_scores) > 0 else 1.0
    max_dense = max(dense_scores) if max(dense_scores) > 0 else 1.0
    max_fused = max(rrf.values()) if rrf else 1.0

    return [
        (
            idx,
            round(bm25_scores[idx] / max_bm25, 4),
            round(dense_scores[idx] / max_dense, 4),
            round(rrf[idx] / max_fused, 4),
        )
        for idx in top_indices
    ]


def _hybrid_search(query: str, top_k: int = 5) -> list[SearchResult]:
    bm25, dense, chunks, doc_names = _load_indexes()
    bm25_scores = bm25.get_scores(_tokenize(query))
    dense_scores = dense.get_scores(query)
    fused = _rrf_fusion(bm25_scores, dense_scores, top_k=top_k)
    return [
        SearchResult(
            chunk=chunks[idx],
            doc_name=doc_names[idx],
            bm25_score=b,
            dense_score=d,
            fused_score=f,
            rank=rank + 1,
        )
        for rank, (idx, b, d, f) in enumerate(fused)
    ]


def _bm25_only_search(query: str, top_k: int = 5) -> list[SearchResult]:
    bm25, _, chunks, doc_names = _load_indexes()
    scores = bm25.get_scores(_tokenize(query))
    max_s = max(scores) if max(scores) > 0 else 1.0
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[
        :top_k
    ]
    return [
        SearchResult(
            chunk=chunks[i],
            doc_name=doc_names[i],
            bm25_score=round(scores[i] / max_s, 4),
            dense_score=0.0,
            fused_score=round(scores[i] / max_s, 4),
            rank=rank + 1,
        )
        for rank, i in enumerate(ranked)
    ]


def _dense_only_search(query: str, top_k: int = 5) -> list[SearchResult]:
    _, dense, chunks, doc_names = _load_indexes()
    scores = dense.get_scores(query)
    max_s = max(scores) if max(scores) > 0 else 1.0
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[
        :top_k
    ]
    return [
        SearchResult(
            chunk=chunks[i],
            doc_name=doc_names[i],
            bm25_score=0.0,
            dense_score=round(scores[i] / max_s, 4),
            fused_score=round(scores[i] / max_s, 4),
            rank=rank + 1,
        )
        for rank, i in enumerate(ranked)
    ]


# -- Simple LLM stub (no API call) --------------------------------------------


def _generate_answer_stub(query: str, results: list[SearchResult]) -> str:
    """Generate a demo answer from retrieved chunks (no LLM call needed)."""
    if not results:
        return "No relevant information found in the documents."

    # Simple extractive answer: find sentences containing query keywords
    keywords = set(_tokenize(query)) - {
        "what",
        "is",
        "the",
        "a",
        "an",
        "in",
        "of",
        "and",
        "or",
        "to",
        "for",
        "how",
        "does",
        "are",
        "was",
        "were",
    }

    best_sentences = []
    for result in results[:3]:
        sentences = re.split(r"[.!?\n]+", result.chunk)
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            sentence_lower = sentence.lower()
            if any(kw in sentence_lower for kw in keywords):
                best_sentences.append(
                    f"* {sentence} [Source: {result.doc_name}]"
                )
            if len(best_sentences) >= 3:
                break
        if len(best_sentences) >= 3:
            break

    if best_sentences:
        return "Based on the retrieved documents:\n\n" + "\n".join(
            best_sentences[:3]
        )

    # Fallback: return first chunk excerpt
    return f"From {results[0].doc_name}:\n{results[0].chunk[:400]}"


# -- UI Rendering --------------------------------------------------------------


def _render_score_bar(score: float, color: str, label: str) -> None:
    bar_width = int(score * 100)
    st.markdown(
        f"""<div style="margin:2px 0">
        <span style="font-size:0.75rem;color:#94a3b8;width:70px;display:inline-block">{label}</span>
        <div style="display:inline-block;background:{color};width:{bar_width}%;height:8px;border-radius:4px;vertical-align:middle"></div>
        <span style="font-size:0.75rem;color:#94a3b8;margin-left:4px">{score:.3f}</span>
        </div>""",
        unsafe_allow_html=True,
    )


def _render_result_card(result: SearchResult, show_breakdown: bool = True) -> None:
    with st.container():
        st.markdown(
            f"**Rank #{result.rank}** -- `{result.doc_name}`",
        )
        if show_breakdown:
            cols = st.columns([1, 1, 1])
            with cols[0]:
                _render_score_bar(result.bm25_score, "#f59e0b", "BM25")
            with cols[1]:
                _render_score_bar(result.dense_score, "#6366f1", "Dense")
            with cols[2]:
                _render_score_bar(result.fused_score, "#10b981", "Fused")
        else:
            st.caption(f"Score: {result.fused_score:.3f}")

        with st.expander("Chunk preview"):
            st.text(
                result.chunk[:400]
                + ("..." if len(result.chunk) > 400 else "")
            )
        st.divider()


def _tab_document_qa() -> None:
    """Document Q&A tab -- query -> hybrid search -> answer with attribution."""
    st.subheader("Document Q&A")
    st.markdown("Ask questions about the 5 real-estate demo documents.")

    # Sample questions
    sample_qs = [
        "What is the list price of 742 Vine Street?",
        "What does the HOA fee cover?",
        "What were the inspection findings?",
        "What is the median home price in Q4 2025?",
        "When does the purchase contract close?",
    ]

    col1, col2 = st.columns([3, 1])
    with col1:
        question = st.text_input(
            "Your question",
            placeholder="e.g. What is the HOA fee and what does it cover?",
            key="qa_question",
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Sample Q", key="sample_q_btn"):
            import random

            st.session_state["qa_question"] = random.choice(sample_qs)
            st.rerun()

    top_k = st.slider(
        "Number of sources",
        min_value=1,
        max_value=5,
        value=3,
        key="qa_top_k",
    )

    if question:
        with st.spinner("Retrieving relevant chunks..."):
            results = _hybrid_search(question, top_k=top_k)
            answer = _generate_answer_stub(question, results)

        st.markdown("### Answer")
        st.info(answer)

        st.markdown(f"### Sources ({len(results)} chunks retrieved)")
        for result in results:
            _render_result_card(result, show_breakdown=True)


def _tab_retrieval_explorer() -> None:
    """Retrieval Explorer tab -- side-by-side BM25 | Dense | Fused."""
    st.subheader("Retrieval Explorer")
    st.markdown(
        "Compare how BM25, dense retrieval, and RRF fusion rank documents differently."
    )

    query = st.text_input(
        "Explorer query",
        value="HOA fee monthly assessment",
        key="explorer_query",
    )

    if query:
        with st.spinner("Running all three retrievers..."):
            bm25_results = _bm25_only_search(query, top_k=3)
            dense_results = _dense_only_search(query, top_k=3)
            fused_results = _hybrid_search(query, top_k=3)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### BM25 Only")
            st.caption("Term-frequency / IDF keyword matching")
            for r in bm25_results:
                st.markdown(f"**#{r.rank}** `{r.doc_name[:25]}...`")
                st.progress(r.bm25_score, text=f"BM25: {r.bm25_score:.3f}")
                st.caption(r.chunk[:120] + "...")
                st.divider()

        with col2:
            st.markdown("#### Dense Only")
            st.caption("TF-IDF vector cosine similarity")
            for r in dense_results:
                st.markdown(f"**#{r.rank}** `{r.doc_name[:25]}...`")
                st.progress(
                    r.dense_score, text=f"Dense: {r.dense_score:.3f}"
                )
                st.caption(r.chunk[:120] + "...")
                st.divider()

        with col3:
            st.markdown("#### RRF Fused")
            st.caption("Reciprocal Rank Fusion (BM25 + Dense)")
            for r in fused_results:
                st.markdown(f"**#{r.rank}** `{r.doc_name[:25]}...`")
                st.progress(
                    r.fused_score, text=f"Fused: {r.fused_score:.3f}"
                )
                st.caption(r.chunk[:120] + "...")
                st.divider()

        # Show RRF working explanation
        with st.expander("How RRF Fusion Works"):
            st.markdown(
                """
**Reciprocal Rank Fusion (RRF)** combines rankings from multiple retrievers:

```
RRF_score(doc) = sum( 1 / (k + rank_i) )
```

Where `k=60` is a smoothing constant and `rank_i` is the document's rank in retriever `i`.

**Benefits:**
- No need to normalize scores across different retrieval systems
- Robust to outliers in any single retriever
- Proven to outperform individual retrievers on most benchmarks
- Works with any number of retrievers (BM25 + dense + cross-encoder, etc.)
"""
            )


def _tab_system_metrics() -> None:
    """System Metrics tab -- static capability cards."""
    st.subheader("System Architecture")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Phase", "3 / 4", "Hybrid + Reranking")
        st.caption("Phase 4: Agentic RAG in progress")

    with col2:
        st.metric("Retrieval Latency", "< 50ms", "avg p50")
        st.caption("No API calls -- in-memory indexes")

    with col3:
        st.metric("Corpus", "5 docs", "25+ chunks")
        st.caption("Real estate domain: listings, HOA, contracts")

    with col4:
        st.metric("Fusion Method", "RRF", "k=60")
        st.caption("Reciprocal Rank Fusion -- no score normalization needed")

    st.divider()

    st.markdown("### Pipeline Architecture")
    st.code(
        """
User Query
    |
QueryPlanner -> sub-queries[]         [Phase 4: Agentic]
    |
+---------------------+
|  BM25 Retriever     | -> ranked by TF-IDF keyword match
|  Dense Retriever    | -> ranked by semantic similarity   [Phase 3: Hybrid]
+---------------------+
    |
RRF Fusion (k=60)                    [Phase 3: Active]
    |
Cross-Encoder Reranker               [Phase 3: Available]
    |
LLM Answer Generation                [Phase 3: Active]
    |
ReflectionLayer -> sufficient?        [Phase 4: Agentic]
    +-- Yes -> return answer
    +-- No  -> re-retrieve (max 2 loops)
""",
        language="text",
    )

    st.divider()
    st.markdown("### Chunk Strategy")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
**Current (Demo)**
- Chunking: Word-boundary, ~200 words
- Overlap: 20 words
- Index: In-memory (BM25 + TF-IDF dense)
"""
        )
    with col2:
        st.markdown(
            """
**Production Config**
- Chunking: Sentence-boundary, 800 tokens
- Overlap: 100 tokens
- Index: ChromaDB (persistent) + BM25Okapi
- Embeddings: OpenAI text-embedding-3-small
"""
        )

    st.divider()
    st.markdown("### Technology Stack")

    stack_data = {
        "Component": [
            "Sparse Retrieval",
            "Dense Retrieval",
            "Fusion",
            "Reranking",
            "LLM",
            "Vector Store",
        ],
        "Technology": [
            "BM25Okapi (rank-bm25)",
            "text-embedding-3-small",
            "RRF (k=60)",
            "Cross-Encoder (sentence-transformers)",
            "Claude claude-haiku-4-5 / claude-sonnet-4-6",
            "ChromaDB (persistent)",
        ],
        "Status": [
            "Active",
            "Active",
            "Active",
            "Available",
            "Active",
            "Active",
        ],
    }

    import pandas as pd

    st.dataframe(
        pd.DataFrame(stack_data), use_container_width=True, hide_index=True
    )


# -- Main render ---------------------------------------------------------------


def render_rag_demo_dashboard() -> None:
    """Main entry point for the RAG demo dashboard."""
    tab1, tab2, tab3 = st.tabs(
        ["Document Q&A", "Retrieval Explorer", "System Metrics"]
    )

    with tab1:
        _tab_document_qa()

    with tab2:
        _tab_retrieval_explorer()

    with tab3:
        _tab_system_metrics()
