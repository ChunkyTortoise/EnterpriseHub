"""
RAG Chatbot Demo — by Cayman Roden
Upload a PDF or paste a URL, get a RAG chatbot on your content in 60 seconds.
"""

import os

import streamlit as st
from rag_pipeline import (
    HybridRAGPipeline,
    HybridSourceChunk,
    ProviderConfig,
    ingest_document,
    ingest_url,
    query,
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RAG Chatbot Demo — Cayman Roden",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dark theme CSS ────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .main .block-container { background-color: #0f172a; padding-top: 2rem; }
    .stChatMessage { background-color: #1e293b; border-radius: 8px; padding: 0.5rem; margin: 0.25rem 0; }
    .stButton > button {
        background-color: #6366f1; color: white; border: none;
        border-radius: 6px; padding: 0.5rem 1.5rem; font-weight: 600;
    }
    .stButton > button:hover { background-color: #4f46e5; }
    .stTextInput > div > div > input { background-color: #1e293b; color: #f8fafc; border-color: #334155; }
    .stSelectbox > div > div { background-color: #1e293b; color: #f8fafc; }
    .stFileUploader { background-color: #1e293b; border-radius: 8px; padding: 1rem; }
    .stExpander { background-color: #1e293b; border-color: #334155; }
    .success-box { background-color: #064e3b; border: 1px solid #10b981; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
    .info-box { background-color: #1e3a5f; border: 1px solid #6366f1; border-radius: 8px; padding: 1rem; margin: 1rem 0; }
    .hire-card { background-color: #1e293b; border-radius: 12px; padding: 2rem; text-align: center; margin: 1rem 0; }
    .cta-button { display: inline-block; background-color: #6366f1; color: white !important;
        text-decoration: none; padding: 0.75rem 2rem; border-radius: 8px; font-weight: 600;
        margin: 0.5rem; font-size: 1rem; }
    .cta-button:hover { background-color: #4f46e5; }
    h1, h2, h3 { color: #f8fafc; }
    .metric-card { background-color: #1e293b; border-radius: 8px; padding: 1rem; text-align: center; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Session state init ────────────────────────────────────────────────────────
def _init_session():
    defaults = {
        "collection_id": None,
        "filename": None,
        "messages": [],
        "provider_config": ProviderConfig(
            embedding_provider="glm",
            llm_provider="glm",
            api_key=os.environ.get("GLM_API_KEY", ""),
        ),
        "page": "📄 Upload Document",
        "search_mode": "Basic",
        "hybrid_pipeline": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_session()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 RAG Chatbot Demo")
    st.markdown("**by Cayman Roden**")
    st.markdown("*Upload any PDF or URL → get a chatbot in 60s*")
    st.divider()

    # Provider config
    with st.expander("⚙️ Provider Config", expanded=False):
        provider_choice = st.selectbox(
            "LLM Provider",
            ["GLM-4-Flash (Free)", "OpenAI", "Anthropic"],
            key="provider_choice",
        )
        api_key = st.text_input(
            "API Key", type="password", key="api_key_input", value=st.session_state.provider_config.api_key
        )

        if st.button("Save Config", key="save_config"):
            provider_map = {
                "GLM-4-Flash (Free)": "glm",
                "OpenAI": "openai",
                "Anthropic": "anthropic",
            }
            p = provider_map[provider_choice]
            llm_model = {
                "glm": "glm-4-flash",
                "openai": "gpt-4o-mini",
                "anthropic": "claude-3-5-haiku-20241022",
            }[p]
            st.session_state.provider_config = ProviderConfig(
                embedding_provider=p,
                llm_provider=p,
                api_key=api_key,
                llm_model=llm_model,
            )
            st.success("Config saved!")

    st.divider()

    # Search mode toggle
    search_mode = st.radio("Search Mode", ["Basic", "Hybrid"], horizontal=True, key="search_mode_radio")
    st.session_state.search_mode = search_mode
    if search_mode == "Hybrid":
        st.caption("BM25 + dense retrieval with RRF fusion")

    st.divider()

    # Navigation
    page = st.radio(
        "Navigate",
        ["📄 Upload Document", "💬 Chat", "🔧 How It Works", "🤝 Hire Me"],
        key="nav_radio",
    )
    st.session_state.page = page

    st.divider()

    # Hire Me links
    st.markdown("**🔗 Hire Cayman**")
    st.markdown(
        """
<a href="https://www.fiverr.com/caymanroden" target="_blank" class="cta-button" style="font-size:0.85rem;padding:0.4rem 1rem;">Fiverr</a>
<a href="https://www.upwork.com/freelancers/caymanroden" target="_blank" class="cta-button" style="font-size:0.85rem;padding:0.4rem 1rem;">Upwork</a>
<a href="https://www.linkedin.com/in/caymanroden/" target="_blank" class="cta-button" style="font-size:0.85rem;padding:0.4rem 1rem;">LinkedIn</a>
""",
        unsafe_allow_html=True,
    )

# ── Pages ─────────────────────────────────────────────────────────────────────


def page_upload():
    st.title("📄 Upload Document")
    st.markdown("Upload a PDF, TXT, or Markdown file — or paste a URL — to create your RAG chatbot.")

    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a file", type=["pdf", "txt", "md"], help="Max ~50MB. Larger files may take longer to process."
        )
        st.markdown("**— or —**")
        url_input = st.text_input("Paste a URL", placeholder="https://example.com/article")

    with col2:
        if st.session_state.collection_id:
            st.markdown(
                f"""
<div class="success-box">
✅ <strong>Document loaded</strong><br>
📄 {st.session_state.filename}
</div>""",
                unsafe_allow_html=True,
            )

    if st.button("🚀 Process Document", type="primary"):
        cfg = st.session_state.provider_config
        if not cfg.api_key:
            st.warning("⚠️ Please add your API key in the sidebar **Provider Config** to continue.")
            return

        if not uploaded_file and not url_input.strip():
            st.error("Please upload a file or paste a URL.")
            return

        try:
            with st.spinner(""):
                progress = st.empty()
                progress.markdown("⏳ **Chunking...** splitting document into segments")

                if uploaded_file:
                    content = uploaded_file.read()
                    filename = uploaded_file.name
                    progress.markdown("⏳ **Embedding...** converting chunks to vectors")
                    collection_id = ingest_document(content, filename, cfg)

                    # Also ingest into hybrid pipeline if hybrid mode
                    if st.session_state.search_mode == "Hybrid":
                        progress.markdown("⏳ **Building hybrid index...** BM25 + dense vectors")
                        hybrid = HybridRAGPipeline()
                        hybrid.ingest(content, filename, cfg)
                        st.session_state.hybrid_pipeline = hybrid
                    else:
                        st.session_state.hybrid_pipeline = None
                else:
                    url = url_input.strip()
                    filename = url.split("/")[-1] or "webpage"
                    progress.markdown("⏳ **Fetching & Embedding...** downloading and indexing content")
                    collection_id = ingest_url(url, cfg)
                    st.session_state.hybrid_pipeline = None

                progress.markdown("✅ **Ready!** Your document is indexed and ready to chat.")

            st.session_state.collection_id = collection_id
            st.session_state.filename = filename
            st.session_state.messages = []

            st.markdown(
                f"""
<div class="success-box">
✅ <strong>Document processed successfully!</strong><br>
📄 <strong>{filename}</strong> is ready for questions.
</div>""",
                unsafe_allow_html=True,
            )

            if st.button("💬 Go to Chat →"):
                st.session_state.page = "💬 Chat"
                st.rerun()

        except ValueError as e:
            st.error(f"❌ Document error: {e}")
        except Exception as e:
            st.error(f"❌ Processing failed: {e}")
            st.info("Check your API key and try again.")


def page_chat():
    st.title("💬 Chat with Your Document")

    if not st.session_state.collection_id:
        st.markdown(
            """
<div class="info-box">
📄 No document loaded yet. Upload a document first to start chatting.
</div>""",
            unsafe_allow_html=True,
        )
        if st.button("📄 Go to Upload →"):
            st.session_state.page = "📄 Upload Document"
            st.rerun()
        return

    st.markdown(f"**Document**: 📄 `{st.session_state.filename}`")
    st.divider()

    # Clear chat button in sidebar
    with st.sidebar:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📚 Sources"):
                    for i, src in enumerate(msg["sources"]):
                        if isinstance(src, HybridSourceChunk):
                            st.markdown(f"**[Source {i + 1}]** (fused: {src.fused_score:.3f})")
                            cols = st.columns(3)
                            cols[0].metric("BM25", f"{src.bm25_score:.4f}")
                            cols[1].metric("Dense", f"{src.dense_score:.4f}")
                            cols[2].metric("Fused", f"{src.fused_score:.4f}")
                        else:
                            st.markdown(f"**[Source {i + 1}]** (score: {src.score:.3f})")
                        st.markdown(f"> {src.content}...")
                        st.divider()

    # Chat input
    if prompt := st.chat_input("Ask a question about your document..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    hybrid = st.session_state.get("hybrid_pipeline")
                    if hybrid is not None and st.session_state.search_mode == "Hybrid":
                        response = hybrid.query(prompt, st.session_state.provider_config)
                    else:
                        response = query(prompt, st.session_state.collection_id, st.session_state.provider_config)

                    st.markdown(response.answer)
                    st.caption(f"⚡ {response.latency_ms}ms")

                    if response.sources:
                        with st.expander("📚 Sources"):
                            for i, src in enumerate(response.sources):
                                if isinstance(src, HybridSourceChunk):
                                    st.markdown(f"**[Source {i + 1}]** (fused: {src.fused_score:.3f})")
                                    cols = st.columns(3)
                                    cols[0].metric("BM25", f"{src.bm25_score:.4f}")
                                    cols[1].metric("Dense", f"{src.dense_score:.4f}")
                                    cols[2].metric("Fused", f"{src.fused_score:.4f}")
                                else:
                                    st.markdown(f"**[Source {i + 1}]** (score: {src.score:.3f})")
                                st.markdown(f"> {src.content}...")
                                st.divider()

                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response.answer,
                            "sources": response.sources,
                        }
                    )
                except Exception as e:
                    err = f"❌ Error: {e}"
                    st.error(err)
                    st.session_state.messages.append({"role": "assistant", "content": err})


def page_how_it_works():
    st.title("🔧 How It Works")
    st.markdown("This demo runs a production-grade RAG pipeline entirely in-memory.")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="metric-card"><h3>800</h3><p>tokens per chunk</p></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-card"><h3>Top-5</h3><p>chunks retrieved</p></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-card"><h3>~15s</h3><p>avg. ingestion time</p></div>', unsafe_allow_html=True)

    st.divider()
    st.markdown("### Pipeline Steps")

    steps = [
        (
            "1. 📤 Upload",
            "You upload a PDF/TXT/MD file or paste a URL. Content is extracted using pypdf (PDF) or BeautifulSoup (HTML).",
        ),
        (
            "2. ✂️ Chunk",
            "Text is split into **800-token chunks** with a **100-token overlap** using sentence-boundary detection. Overlap ensures context is preserved across chunk boundaries.",
        ),
        (
            "3. 🔢 Embed",
            "Each chunk is converted to a high-dimensional vector using your chosen embedding model (GLM `embedding-3`, OpenAI `text-embedding-3-small`).",
        ),
        (
            "4. 🗄️ Store",
            "Embeddings are stored in **ChromaDB** (in-memory). Each upload gets its own isolated collection. No data persists between sessions.",
        ),
        (
            "5. 🔍 Retrieve",
            "Your question is embedded using the same model. The **top-5 most similar chunks** are retrieved via cosine similarity.",
        ),
        (
            "6. 🤖 Generate",
            "The retrieved chunks are passed to the LLM as context. The model synthesizes an answer that references **[Source 1]**, **[Source 2]**, etc.",
        ),
    ]

    for title, desc in steps:
        with st.expander(title, expanded=True):
            st.markdown(desc)

    st.divider()
    st.markdown("### Architecture")
    st.code(
        """
User Input (PDF / URL)
        │
        ▼
  Text Extraction (pypdf / BeautifulSoup4)
        │
        ▼
  Chunking (800 tokens, 100 overlap, sentence boundaries)
        │
        ▼
  Embedding (GLM embedding-3 / OpenAI text-embedding-3-small)
        │
        ▼
  ChromaDB In-Memory Store (EphemeralClient)
        │
  Question ──embed──► Top-5 Cosine Retrieval
                              │
                              ▼
                    LLM Answer + [Source N] Citations
                    (GLM-4-Flash / GPT-4o-mini / Claude Haiku)
""",
        language="text",
    )


def page_hire_me():
    st.title("🤝 Hire Me")
    st.markdown("### This demo is your deliverable.")
    st.markdown("*The production-grade RAG pipeline powering this app is exactly what I build for clients.*")

    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
<div class="hire-card">
<h3>🛒 Fiverr</h3>
<p><strong>RAG System</strong><br>$300 – $1,200</p>
<p><strong>AI Chatbot</strong><br>$400 – $1,500</p>
<p><strong>Dashboard</strong><br>$200 – $800</p>
<a href="https://www.fiverr.com/caymanroden" target="_blank" class="cta-button">View Gigs</a>
</div>""",
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
<div class="hire-card">
<h3>💼 Upwork</h3>
<p>Hourly & fixed-price projects</p>
<p><strong>AI / ML Engineering</strong><br>Custom scoping</p>
<p><strong>Multi-agent Systems</strong><br>Enterprise pricing</p>
<a href="https://www.upwork.com/freelancers/caymanroden" target="_blank" class="cta-button">View Profile</a>
</div>""",
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            """
<div class="hire-card">
<h3>🔗 LinkedIn</h3>
<p>Connect for consulting, contracts, and full-time opportunities</p>
<br><br>
<a href="https://www.linkedin.com/in/caymanroden/" target="_blank" class="cta-button">Connect</a>
</div>""",
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("### What I Build")
    services = [
        (
            "🔍 RAG Systems",
            "Production-grade retrieval-augmented generation with any document type, embedding provider, and vector store.",
        ),
        (
            "🤖 AI Chatbots",
            "Custom chatbots on your data with multi-turn memory, escalation logic, and CRM integration (GHL, HubSpot).",
        ),
        (
            "🔗 Multi-Agent Pipelines",
            "Autonomous agent teams for research, qualification, content generation, and workflow automation.",
        ),
        (
            "📊 AI Dashboards",
            "Streamlit / Gradio apps that turn raw data into actionable insight with LLM-powered analysis.",
        ),
        (
            "⚡ LLM Integrations",
            "Plug Claude, GPT-4, or Gemini into your existing product via clean, maintainable APIs.",
        ),
    ]
    for title, desc in services:
        st.markdown(f"**{title}** — {desc}")


# ── Router ────────────────────────────────────────────────────────────────────
page_map = {
    "📄 Upload Document": page_upload,
    "💬 Chat": page_chat,
    "🔧 How It Works": page_how_it_works,
    "🤝 Hire Me": page_hire_me,
}

current_page = st.session_state.get("page", "📄 Upload Document")
page_map.get(current_page, page_upload)()
