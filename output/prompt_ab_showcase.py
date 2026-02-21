"""
Prompt Engineering Lab -- A/B Testing Showcase
===============================================
A Streamlit app demonstrating prompt optimization through side-by-side
comparison, mock quality scoring, and actionable engineering tips.

Run:
    streamlit run output/prompt_ab_showcase.py

No API keys required -- all execution is mocked.
"""

import hashlib
import time

import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Prompt Lab -- A/B Testing",
    page_icon="🔬",
    layout="wide",
)

# ── Obsidian dark theme CSS ──────────────────────────────────────────────────
st.markdown(
    """
<style>
    .stApp { background-color: #0d1117; color: #e6edf3; }
    .main-header {
        font-size: 2.5rem; font-weight: 800;
        background: linear-gradient(90deg, #58a6ff, #bc8cff);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .section-header {
        font-size: 1.4rem; font-weight: 700;
        color: #58a6ff; margin-top: 1rem;
    }
    .feature-box {
        background: #161b22; border: 1px solid #30363d;
        border-radius: 8px; padding: 16px; margin: 8px 0;
    }
    .before-card {
        background: #21262d; border-left: 3px solid #f85149;
        border-radius: 6px; padding: 12px; margin: 6px 0;
    }
    .after-card {
        background: #0d2818; border-left: 3px solid #3fb950;
        border-radius: 6px; padding: 12px; margin: 6px 0;
    }
    .tip-card {
        background: #161b22; border-left: 3px solid #d2a8ff;
        border-radius: 6px; padding: 12px; margin: 8px 0;
    }
    .potd-box {
        background: linear-gradient(135deg, #161b22, #1a1f2e);
        border: 1px solid #30363d; border-radius: 10px;
        padding: 20px; margin: 12px 0;
    }
    .improvement-tag {
        display: inline-block; background: #238636; color: white;
        border-radius: 12px; padding: 2px 10px; margin: 2px;
        font-size: 0.8rem; font-weight: 600;
    }
    div[data-testid="stMetricValue"] { color: #58a6ff; font-size: 2rem; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Mock scoring engine ──────────────────────────────────────────────────────

STRUCTURE_MARKERS = [
    "1.",
    "2.",
    "3.",
    "-",
    "*",
    "##",
    "###",
    "step",
    "first",
    "second",
    "third",
    "finally",
]
SPECIFICITY_KEYWORDS = [
    "roi",
    "metric",
    "percent",
    "%",
    "revenue",
    "cost",
    "example",
    "case study",
    "data",
    "result",
    "specific",
    "measurable",
    "increase",
    "decrease",
    "improve",
    "audience",
    "persona",
    "format",
    "constraint",
    "paragraph",
    "sentence",
    "word",
    "bullet",
]


def score_prompt(prompt_text: str) -> dict:
    """Score a prompt based on heuristics. Returns component scores and total."""
    text_lower = prompt_text.lower()
    words = text_lower.split()
    word_count = len(words)

    # Length score: longer prompts with detail score higher (cap at 10)
    length_score = min(word_count / 8.0, 10.0)

    # Structure score: presence of structured output instructions
    structure_hits = sum(1 for m in STRUCTURE_MARKERS if m in text_lower)
    structure_score = min(structure_hits * 1.8, 10.0)

    # Specificity score: domain terms, constraints, measurables
    specificity_hits = sum(1 for kw in SPECIFICITY_KEYWORDS if kw in text_lower)
    specificity_score = min(specificity_hits * 1.5, 10.0)

    # Audience awareness: mentions of who the output is for
    audience_terms = [
        "audience",
        "reader",
        "user",
        "customer",
        "client",
        "beginner",
        "expert",
        "technical",
        "non-technical",
        "executive",
        "developer",
        "manager",
        "vp",
        "ceo",
    ]
    audience_hits = sum(1 for t in audience_terms if t in text_lower)
    audience_score = min(audience_hits * 3.0, 10.0)

    # Constraint score: word/format/length constraints
    constraint_terms = [
        "paragraph",
        "sentence",
        "word",
        "bullet",
        "json",
        "markdown",
        "table",
        "list",
        "maximum",
        "minimum",
        "exactly",
        "no more than",
    ]
    constraint_hits = sum(1 for t in constraint_terms if t in text_lower)
    constraint_score = min(constraint_hits * 2.5, 10.0)

    # Weighted total
    total = (
        length_score * 0.15
        + structure_score * 0.20
        + specificity_score * 0.25
        + audience_score * 0.20
        + constraint_score * 0.20
    )

    return {
        "total": round(total, 1),
        "length": round(length_score, 1),
        "structure": round(structure_score, 1),
        "specificity": round(specificity_score, 1),
        "audience": round(audience_score, 1),
        "constraints": round(constraint_score, 1),
    }


def mock_execute(prompt_text: str) -> dict:
    """Simulate LLM execution. Returns latency, tokens, and mock output."""
    # Deterministic "randomness" from prompt content
    h = int(hashlib.md5(prompt_text.encode()).hexdigest()[:8], 16)
    word_count = len(prompt_text.split())

    token_count = word_count * 4 + 80 + (h % 60)
    latency_ms = 120 + word_count * 3 + (h % 80)

    scores = score_prompt(prompt_text)

    # Mock output text based on quality
    if scores["total"] >= 7:
        output = (
            "## Executive Summary\n\n"
            "AI-powered sales automation delivers measurable ROI:\n\n"
            "1. **Lead response time**: reduced from 45 min to under 2 min "
            "(96% improvement)\n"
            "2. **Conversion rate**: increased from 12% to 28% (+133%)\n\n"
            "### Case Study: Regional Brokerage\n"
            "A 15-agent team deployed AI qualification bots and recovered "
            "$180K in annual revenue from previously lost leads."
        )
    elif scores["total"] >= 4:
        output = (
            "AI is changing B2B sales in several ways. Companies are using "
            "chatbots and automation tools to handle leads faster. Some "
            "reports suggest this can improve conversion rates significantly. "
            "Many sales teams are adopting these tools."
        )
    else:
        output = (
            "AI is transforming many industries including sales. There are "
            "many applications and the technology continues to evolve rapidly."
        )

    return {
        "output": output,
        "token_count": token_count,
        "latency_ms": latency_ms,
        "scores": scores,
    }


# ── Sidebar: Prompt Engineering Tips ─────────────────────────────────────────

TIPS = [
    {
        "title": "Be specific about format",
        "before": "Explain machine learning.",
        "after": "Explain machine learning in 3 bullet points, each under 20 words, for a non-technical audience.",
    },
    {
        "title": "Define the audience",
        "before": "Write about cloud migration.",
        "after": "Write a 2-paragraph briefing on cloud migration risks for a CTO evaluating AWS vs Azure.",
    },
    {
        "title": "Add measurable constraints",
        "before": "Give me marketing ideas.",
        "after": "List 5 B2B marketing tactics that cost under $500/month, with expected ROI percentage for each.",
    },
    {
        "title": "Request structure",
        "before": "How do I improve my website?",
        "after": "Audit my website and return findings as a markdown table with columns: Issue, Severity (1-5), Fix, and Estimated Impact.",
    },
    {
        "title": "Provide context and role",
        "before": "Write a follow-up email.",
        "after": "You are a real estate agent. Write a 3-sentence follow-up email to a warm lead who attended an open house but hasn't responded in 48 hours. Tone: friendly, not pushy.",
    },
]

with st.sidebar:
    st.markdown('<div class="main-header">Prompt Lab</div>', unsafe_allow_html=True)
    st.caption("A/B Testing Showcase")
    st.divider()

    with st.expander("Prompt Engineering Tips", expanded=False):
        for i, tip in enumerate(TIPS):
            st.markdown(f'<div class="tip-card">', unsafe_allow_html=True)
            st.markdown(f"**Tip {i + 1}: {tip['title']}**")
            st.markdown(
                f'<div class="before-card"><strong>Before:</strong> {tip["before"]}</div>', unsafe_allow_html=True
            )
            st.markdown(f'<div class="after-card"><strong>After:</strong> {tip["after"]}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.divider()
    st.caption("No API keys required. All execution is mocked.")


# ── Main content ─────────────────────────────────────────────────────────────

st.markdown('<h1 class="main-header">A/B Prompt Comparison</h1>', unsafe_allow_html=True)
st.caption("Compare two prompts side by side. See how specificity, structure, and constraints affect quality.")

# ── A/B Comparison Section ───────────────────────────────────────────────────

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("**Prompt A** (baseline)")
    prompt_a = st.text_area(
        "prompt_a",
        value="Write about AI",
        height=120,
        label_visibility="collapsed",
    )

with col_b:
    st.markdown("**Prompt B** (optimized)")
    prompt_b = st.text_area(
        "prompt_b",
        value=(
            "Write a 3-paragraph executive summary of how AI is transforming "
            "B2B sales, including 2 specific ROI metrics and one real-world "
            "case study. Audience: VP of Sales with no technical background."
        ),
        height=120,
        label_visibility="collapsed",
    )

run_btn = st.button("Run Comparison", type="primary", use_container_width=True)

if run_btn:
    with st.spinner("Executing prompts..."):
        time.sleep(0.8)
        result_a = mock_execute(prompt_a)
        result_b = mock_execute(prompt_b)

    st.divider()

    # ── Metrics row ──────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    quality_delta = result_b["scores"]["total"] - result_a["scores"]["total"]
    latency_delta = result_b["latency_ms"] - result_a["latency_ms"]
    token_delta = result_b["token_count"] - result_a["token_count"]

    m1.metric("Quality A", f"{result_a['scores']['total']}/10")
    m2.metric(
        "Quality B",
        f"{result_b['scores']['total']}/10",
        delta=f"+{quality_delta:.1f}" if quality_delta > 0 else f"{quality_delta:.1f}",
    )
    m3.metric("Latency Delta", f"{latency_delta:+d} ms")
    m4.metric("Token Delta", f"{token_delta:+d}")

    # ── Bar chart comparison ─────────────────────────────────────────────────
    categories = ["Quality", "Latency (ms)", "Tokens"]
    values_a = [result_a["scores"]["total"], result_a["latency_ms"], result_a["token_count"]]
    values_b = [result_b["scores"]["total"], result_b["latency_ms"], result_b["token_count"]]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Prompt A",
            x=categories,
            y=values_a,
            marker_color="#f85149",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Prompt B",
            x=categories,
            y=values_b,
            marker_color="#3fb950",
        )
    )
    fig.update_layout(
        barmode="group",
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        plot_bgcolor="#161b22",
        font=dict(color="#e6edf3"),
        height=350,
        margin=dict(t=30, b=30),
        legend=dict(orientation="h", y=1.12),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Quality breakdown radar ──────────────────────────────────────────────
    breakdown_cats = ["Length", "Structure", "Specificity", "Audience", "Constraints"]
    breakdown_a = [result_a["scores"][k] for k in ["length", "structure", "specificity", "audience", "constraints"]]
    breakdown_b = [result_b["scores"][k] for k in ["length", "structure", "specificity", "audience", "constraints"]]

    radar = go.Figure()
    radar.add_trace(
        go.Scatterpolar(
            r=breakdown_a + [breakdown_a[0]],
            theta=breakdown_cats + [breakdown_cats[0]],
            fill="toself",
            name="Prompt A",
            line_color="#f85149",
            fillcolor="rgba(248, 81, 73, 0.15)",
        )
    )
    radar.add_trace(
        go.Scatterpolar(
            r=breakdown_b + [breakdown_b[0]],
            theta=breakdown_cats + [breakdown_cats[0]],
            fill="toself",
            name="Prompt B",
            line_color="#3fb950",
            fillcolor="rgba(63, 185, 80, 0.15)",
        )
    )
    radar.update_layout(
        polar=dict(
            bgcolor="#161b22",
            radialaxis=dict(visible=True, range=[0, 10], gridcolor="#30363d"),
            angularaxis=dict(gridcolor="#30363d"),
        ),
        template="plotly_dark",
        paper_bgcolor="#0d1117",
        font=dict(color="#e6edf3"),
        height=380,
        margin=dict(t=40, b=20),
        legend=dict(orientation="h", y=1.12),
        title=dict(text="Quality Breakdown", font=dict(size=14)),
    )
    st.plotly_chart(radar, use_container_width=True)

    # ── Side-by-side outputs ─────────────────────────────────────────────────
    st.markdown('<p class="section-header">Mock LLM Output</p>', unsafe_allow_html=True)
    out_a, out_b = st.columns(2)
    with out_a:
        st.markdown(f'<div class="before-card">{result_a["output"]}</div>', unsafe_allow_html=True)
    with out_b:
        st.markdown(f'<div class="after-card">{result_b["output"]}</div>', unsafe_allow_html=True)

st.divider()

# ── Prompt of the Day ────────────────────────────────────────────────────────

st.markdown('<p class="section-header">Prompt of the Day</p>', unsafe_allow_html=True)

st.markdown('<div class="potd-box">', unsafe_allow_html=True)

potd_a, potd_b = st.columns(2)

with potd_a:
    st.markdown("**Before**")
    st.markdown(
        '<div class="before-card">"Write about AI"<br><br><strong>Score: 3.2 / 10</strong></div>',
        unsafe_allow_html=True,
    )

with potd_b:
    st.markdown("**After**")
    st.markdown(
        '<div class="after-card">'
        '"Write a 3-paragraph executive summary of how AI is transforming B2B sales, '
        "including 2 specific ROI metrics and one real-world case study. "
        'Audience: VP of Sales with no technical background."'
        "<br><br><strong>Score: 8.7 / 10</strong>"
        "</div>",
        unsafe_allow_html=True,
    )

st.markdown("**Why it improved:**")
improvements = ["Specificity +", "Structure +", "Audience awareness +", "Constraints +"]
tags_html = " ".join(f'<span class="improvement-tag">{tag}</span>' for tag in improvements)
st.markdown(tags_html, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    '<div class="feature-box" style="margin-top: 16px;">'
    "<strong>What changed:</strong> The optimized prompt specifies "
    "<em>format</em> (3 paragraphs), <em>content requirements</em> "
    "(2 ROI metrics, 1 case study), and <em>audience</em> (non-technical VP). "
    "This gives the LLM clear constraints, producing structured, "
    "measurable, audience-appropriate output instead of generic filler."
    "</div>",
    unsafe_allow_html=True,
)
