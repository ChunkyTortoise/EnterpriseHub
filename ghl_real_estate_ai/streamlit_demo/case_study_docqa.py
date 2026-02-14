"""
DocQA Engine Case Study Page
Case study for the DocQA Engine project - RAG Document Q&A Platform
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def render_docqa_case_study():
    """Render the DocQA Engine case study page."""
    st.set_page_config(page_title="DocQA Engine Case Study", page_icon="📄", layout="wide")
    
    # Header
    st.markdown("# 📄 DocQA Engine Case Study")
    st.markdown("### RAG-Powered Document Q&A with Prompt Engineering Lab")
    st.markdown("---")
    
    # Two-column layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        render_main_content()
    
    with col2:
        render_metrics_sidebar()
    
    # Full-width sections
    st.markdown("---")
    render_technical_stack()
    
    st.markdown("---")
    render_architecture()
    
    st.markdown("---")
    render_testimonials()
    
    st.markdown("---")
    render_cta()


def render_main_content():
    """Render the main case study content."""
    st.markdown("## Challenge")
    st.markdown("""
    Organizations struggle to extract value from their document repositories:
    
    - **Information Overload:** 10,000+ documents with no unified search
    - **Poor Search Results:** Traditional keyword search misses context
    - **Manual Processing:** Hours spent reading and summarizing documents
    - **Knowledge Gaps:** Experts leaving, knowledge walking out the door
    - **Compliance Risks:** Can't find required information for audits
    """)
    
    st.markdown("## Solution")
    st.markdown("""
    DocQA Engine provides an end-to-end document intelligence platform:
    
    ### Core Features
    - **Multi-Format Upload:** PDF, Word, Excel, PowerPoint, images (OCR)
    - **Hybrid RAG Pipeline:** BM25 + Dense embeddings for optimal retrieval
    - **Prompt Engineering Lab:** Test and optimize prompts for your use case
    - **Citation Tracking:** Every answer linked to source document sections
    - **Conversation Memory:** Multi-turn Q&A with context preservation
    
    ### Advanced Capabilities
    - **Table Extraction:** Structured data from PDF tables
    - **Multi-Document QA:** Cross-document analysis and synthesis
    - **Summarization:** Executive summaries with key points
    - **Entity Extraction:** Names, dates, amounts, locations auto-extracted
    
    ### Production Features
    - **Role-Based Access:** Document permissions by user/department
    - **Audit Logging:** Complete query and response history
    - **Export Options:** Answers in PDF, Word, or Markdown
    - **API Integration:** REST API for embedding in other applications
    """)
    
    st.markdown("## Implementation Timeline")
    
    timeline_data = {
        "Week 1": "Core Pipeline & Document Processing",
        "Week 2": "RAG Integration & Vector Store",
        "Week 3": "Prompt Engineering Lab & UI",
        "Week 4": "Security, Auth & Deployment"
    }
    
    for week, task in timeline_data.items():
        st.markdown(f"**{week}:** {task}")


def render_metrics_sidebar():
    """Render metrics sidebar with key outcomes."""
    st.markdown("### 📊 Key Metrics")
    st.markdown("---")
    
    metrics = [
        ("10+", "Document Formats Supported"),
        ("85%", "Answer Accuracy"),
        ("<3s", "Average Response Time"),
        ("50%", "Research Time Reduction"),
        ("100%", "Source Citations"),
        ("4.5/5", "User Satisfaction"),
    ]
    
    for value, label in metrics:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%); 
                    padding: 1rem; border-radius: 12px; margin-bottom: 0.75rem; border: 1px solid rgba(139, 92, 246, 0.2);'>
            <div style='font-size: 2rem; font-weight: 800; color: #8B5CF6;'>{value}</div>
            <div style='font-size: 0.85rem; color: #64748B; font-weight: 500;'>{label}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 💰 Use Cases")
    st.markdown("""
    **Legal:** Contract analysis & discovery  
    **HR:** Policy Q&A & handbook search  
    **Finance:** Report analysis & compliance  
    **Research:** Literature review synthesis
    """)
    
    st.markdown("---")
    st.markdown("### 🔗 Links")
    st.markdown("""
    - [GitHub Repository](https://github.com/ChunkyTortoise/docqa-engine)
    - [Live Demo](https://github.com/ChunkyTortoise/docqa-engine)
    - [Prompt Lab Guide](https://github.com/ChunkyTortoise/docqa-engine)
    """)


def render_technical_stack():
    """Render technical stack section."""
    st.markdown("## Technical Stack")
    
    tech_stack = {
        "Processing": ["PyPDF2", "python-docx", "Tesseract OCR", "OpenCV"],
        "RAG": ["LangChain", "ChromaDB", "OpenAI Embeddings", "BM25"],
        "UI": ["Streamlit", "Plotly", "Pandas", "Pydantic"],
        "API": ["FastAPI", "Redis", "PostgreSQL", "JWT Auth"],
        "Utils": ["tiktoken", "spaCy", "NLTK", " sentence-transformers"],
    }
    
    cols = st.columns(len(tech_stack))
    
    for col, (category, technologies) in zip(cols, tech_stack.items()):
        with col:
            st.markdown(f"**{category}**")
            for tech in technologies:
                st.markdown(f"- {tech}")


def render_architecture():
    """Render architecture diagram."""
    st.markdown("## Architecture")
    
    st.markdown("""
    ```
    ┌─────────────────────────────────────────────────────────────────┐
    │                     Document Ingestion                          │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐      │
    │  │   PDFs      │  │   Word/Excel│  │   Images (OCR)      │      │
    │  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘      │
    └─────────┼────────────────┼────────────────────┼─────────────────┘
              │                │                    │
              ▼                ▼                    ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    Document Processing                          │
    │         Text Extraction → Chunking → Embedding                   │
    └──────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    Vector Store (ChromaDB)                      │
    │         Dense Embeddings + Metadata + Document Links            │
    └──────────────────────────┬──────────────────────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌─────────────────┐ ┌──────────────┐ ┌─────────────────┐
    │  Query Interface│ │ Prompt Lab   │ │ Admin Dashboard │
    │                 │ │              │ │                 │
    │  • Natural lang │ │  • A/B test  │ │  • User mgmt    │
    │  • Citation     │ │  • Optimize  │ │  • Analytics    │
    │  • Follow-up Q  │ │  • Version   │ │  • Settings     │
    └────────┬────────┘ └──────┬───────┘ └────────┬────────┘
             │                 │                  │
             └─────────────────┼──────────────────┘
                               ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                    LLM Response Generation                      │
    │         Claude/GPT-4 + Retrieved Context + Citations          │
    └─────────────────────────────────────────────────────────────────┘
    ```
    """)


def render_testimonials():
    """Render client testimonials section."""
    st.markdown("## Client Impact")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        > "Our legal team used to spend days reviewing contracts. Now they 
        > ask questions in natural language and get cited answers in seconds."
        > 
        > **— General Counsel, Tech Company**
        """)
    
    with col2:
        st.markdown("""
        > "The prompt engineering lab let us fine-tune responses for our 
        > specific compliance requirements. Game changer."
        > 
        > **— Compliance Officer, Financial Services**
        """)


def render_cta():
    """Render call-to-action section."""
    st.markdown("## Unlock Your Document Intelligence")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%); border-radius: 16px; color: white;'>
            <div style='font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;'>📊 Try Demo</div>
            <div style='font-size: 0.9rem; opacity: 0.9;'>Upload & query documents</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("[Live Demo](https://github.com/ChunkyTortoise/docqa-engine)")
    
    with col2:
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #10B981 0%, #059669 100%); border-radius: 16px; color: white;'>
            <div style='font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;'>💻 Source Code</div>
            <div style='font-size: 0.9rem; opacity: 0.9;'>Full RAG implementation</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("[GitHub Repository](https://github.com/ChunkyTortoise/docqa-engine)")
    
    with col3:
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); border-radius: 16px; color: white;'>
            <div style='font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;'>📧 Contact</div>
            <div style='font-size: 0.9rem; opacity: 0.9;'>Custom RAG solutions</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("caymanroden@gmail.com")


if __name__ == "__main__":
    render_docqa_case_study()
