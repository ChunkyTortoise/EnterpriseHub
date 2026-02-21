"""
Advanced RAG System Demo - Streamlit Cloud Deployment
Mock embeddings and search - no real API calls needed
"""

from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Advanced RAG System Demo", page_icon="🔍", layout="wide", initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown(
    """
<style>
    .rag-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .source-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 15px;
        margin: 10px 0;
        border-radius: 5px;
    }
    .result-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Mock document corpus
@st.cache_data(ttl=3600)
def get_mock_documents():
    """Generate mock document corpus for demo"""
    documents = [
        {
            "id": "doc_001",
            "title": "Rancho Cucamonga Housing Market Trends 2024",
            "content": "The Rancho Cucamonga housing market has shown steady growth with median home prices increasing 8.5% year-over-year. Current median price stands at $720,000. Days on market have decreased to 28 on average, indicating strong buyer demand.",
            "source": "Market Report",
            "chunk_id": "chunk_001",
        },
        {
            "id": "doc_002",
            "title": "First-Time Buyer Guide - California",
            "content": "California offers several first-time homebuyer programs including CALHFA loans with down payment assistance up to 3% of the purchase price. Minimum credit score requirements typically start at 640 for conventional loans.",
            "source": "Buyer Guide",
            "chunk_id": "chunk_002",
        },
        {
            "id": "doc_003",
            "title": "Seller's Guide to Pricing Your Home",
            "content": "Comparative Market Analysis (CMA) is essential for pricing your home correctly. Look at recent sales of similar properties (comps) within 1 mile and 6 months. Price your home 2-5% below market value for faster sales in current conditions.",
            "source": "Seller Guide",
            "chunk_id": "chunk_003",
        },
        {
            "id": "doc_004",
            "title": "EnterpriseHub AI Features Overview",
            "content": "EnterpriseHub offers AI-powered lead qualification with 3 specialized bots: LeadBot for initial contact, BuyerBot for qualified buyers, and SellerBot for home sellers. All bots use Claude AI for natural conversations.",
            "source": "Product Docs",
            "chunk_id": "chunk_004",
        },
        {
            "id": "doc_005",
            "title": "Mortgage Rate Trends Q4 2024",
            "content": "Mortgage rates have stabilized around 6.5-7.0% for 30-year fixed loans. Federal Reserve signals suggest rates may decrease in mid-2025. Consider rate buydown points to reduce effective rate by 0.25-0.5%.",
            "source": "Finance",
            "chunk_id": "chunk_005",
        },
        {
            "id": "doc_006",
            "title": "Investment Property Analysis - Rancho Cucamonga",
            "content": "Rental properties in Rancho Cucamonga show 5.2% average ROI. Strong rental demand from young professionals and families. Average rent for 3-bedroom home: $2,800/month.",
            "source": "Investment",
            "chunk_id": "chunk_006",
        },
    ]
    return documents


@st.cache_data(ttl=3600)
def get_mock_embeddings():
    """Generate mock embedding vectors for documents"""
    np.random.seed(42)
    docs = get_mock_documents()
    for doc in docs:
        doc["embedding"] = np.random.randn(1536)  # OpenAI ada-002 dimension
    return docs


def hybrid_search_mock(query, documents, use_hybrid=True, top_k=3):
    """Mock hybrid search - keyword + semantic"""
    np.random.seed(hash(query) % (2**32))

    results = []
    for doc in documents:
        # Simulate relevance score
        base_score = np.random.uniform(0.5, 0.98)

        # Keyword boost if query terms present
        query_lower = query.lower()
        keyword_boost = 0.0
        if any(term in doc["content"].lower() for term in query_lower.split()):
            keyword_boost = 0.1

        score = min(base_score + keyword_boost, 0.99)
        results.append(
            {
                **doc,
                "relevance_score": score,
                "semantic_score": np.random.uniform(0.5, 0.95) if use_hybrid else score,
                "keyword_score": np.random.uniform(0.3, 0.9) if use_hybrid else score,
            }
        )

    # Sort by relevance and return top_k
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results[:top_k]


def generate_mock_answer(query, top_documents):
    """Generate mock answer based on retrieved documents"""
    np.random.seed(hash(query) % (2**32))

    # Generate contextual response
    response_templates = [
        f"Based on the retrieved documents, here are the key insights about '{query}':\n\n",
        f"Here's what our knowledge base indicates regarding '{query}':\n\n",
        f"From analyzing available data on '{query}':\n\n",
    ]

    answer = np.random.choice(response_templates)

    # Summarize top documents
    for i, doc in enumerate(top_documents[:2], 1):
        answer += f"**{i}. {doc['title']}**\n{doc['content'][:200]}...\n\n"

    answer += f"\n*Confidence Score: {top_documents[0]['relevance_score']:.2%}*"
    return answer


def main():
    """Main demo application"""

    # Header
    st.markdown('<div class="rag-header">🔍 Advanced RAG System Demo</div>', unsafe_allow_html=True)
    st.markdown("**Hybrid Search + AI-powered Knowledge Retrieval** | Powered by EnterpriseHub")

    # Sidebar
    with st.sidebar:
        st.title("⚙️ Search Settings")

        hybrid_mode = st.toggle("Enable Hybrid Search", value=True)

        st.markdown("---")
        st.markdown("### Search Parameters")
        top_k = st.slider("Results per query", 1, 5, 3)

        st.markdown("---")
        st.markdown("### Sample Queries")
        sample_queries = [
            "Rancho Cucamonga home prices",
            "first-time buyer programs",
            "mortgage rates 2024",
            "investment property returns",
            "AI lead qualification",
        ]

        for sq in sample_queries:
            if st.button(sq, key=f"btn_{sq}"):
                st.session_state.query = sq

        st.markdown("---")
        st.markdown("### System Info")
        st.info("Mock mode: Using simulated embeddings and search results")
        st.caption(f"Document corpus: {len(get_mock_documents())} documents")

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        # Query input
        query = st.text_input(
            "Enter your query:",
            value=st.session_state.get("query", ""),
            placeholder="Ask about real estate, mortgage, or market trends...",
            label_visibility="collapsed",
        )

        search_btn = st.button("🔍 Search", type="primary", disabled=not query)

    with col2:
        st.markdown("### Quick Stats")
        docs = get_mock_documents()
        st.metric("Documents Indexed", len(docs))
        st.metric("Index Type", "Hybrid (Keyword + Vector)")

    if search_btn and query:
        with st.spinner("Searching knowledge base..."):
            # Perform mock search
            documents = get_mock_documents()
            results = hybrid_search_mock(query, documents, use_hybrid=hybrid_mode, top_k=top_k)

            # Generate answer
            answer = generate_mock_answer(query, results)

        # Display results
        st.markdown("---")
        st.subheader("📋 Search Results")

        for i, result in enumerate(results, 1):
            st.markdown(
                f"""
            <div class="result-card">
                <h4>#{i} {result["title"]}</h4>
                <p>{result["content"][:300]}...</p>
                <small>
                    <span style="color: #667eea;">📄 {result["source"]}</span> | 
                    <span style="color: #28a745;">Relevance: {result["relevance_score"]:.1%}</span>
                </small>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Display generated answer
        st.markdown("---")
        st.subheader("🤖 AI-Generated Answer")
        st.markdown(
            f"""
        <div class="source-card">
            {answer}
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Show retrieval details
        with st.expander("View Retrieval Details"):
            df = pd.DataFrame(
                [
                    {
                        "Document": r["title"],
                        "Relevance": r["relevance_score"],
                        "Semantic": r["semantic_score"],
                        "Keyword": r["keyword_score"],
                    }
                    for r in results
                ]
            )
            st.dataframe(df, use_container_width=True)

    else:
        # Show welcome/empty state
        st.markdown("---")
        st.subheader("🎯 How It Works")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("""
            ### 1. Query Input
            Enter your natural language query about real estate, mortgages, or market trends.
            """)

        with col2:
            st.markdown("""
            ### 2. Hybrid Search
            Combines keyword matching with semantic similarity for accurate results.
            """)

        with col3:
            st.markdown("""
            ### 3. AI Answer
            Generates contextual answers using retrieved knowledge.
            """)

        # Show sample documents
        st.markdown("---")
        st.subheader("📚 Available Knowledge Base")

        docs = get_mock_documents()
        for doc in docs:
            st.markdown(
                f"""
            <div class="source-card">
                <strong>{doc["title"]}</strong><br>
                <small>{doc["source"]}</small>
            </div>
            """,
                unsafe_allow_html=True,
            )


if __name__ == "__main__":
    main()
