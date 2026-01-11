"""
RAG Knowledge Base Uploader - Allow AI to reference specific documents
"""
import streamlit as st
from typing import List, Dict
from pathlib import Path
import hashlib


def render_knowledge_base_uploader():
    """
    Render the RAG knowledge base uploader component
    Allows uploading PDFs, docs, and text files for AI context
    """
    
    st.markdown("### 📚 Knowledge Base (RAG)")
    st.markdown("*Upload neighborhood PDFs, HOA docs, or market reports for AI to reference*")
    
    # Initialize knowledge base in session state
    if 'knowledge_base' not in st.session_state:
        st.session_state.knowledge_base = []
    
    # Upload section
    col_upload, col_status = st.columns([2, 1])
    
    with col_upload:
        uploaded_files = st.file_uploader(
            "Upload Documents",
            type=['pdf', 'txt', 'docx', 'md'],
            accept_multiple_files=True,
            help="AI will use these documents to answer specific questions",
            key="kb_uploader"
        )
        
        if uploaded_files:
            for file in uploaded_files:
                # Check if already uploaded
                file_hash = hashlib.md5(file.read()).hexdigest()
                file.seek(0)  # Reset file pointer
                
                if not any(doc['hash'] == file_hash for doc in st.session_state.knowledge_base):
                    # Process and add to knowledge base
                    doc_info = process_document(file, file_hash)
                    st.session_state.knowledge_base.append(doc_info)
                    st.success(f"✅ '{file.name}' indexed for AI recall!")
                else:
                    st.info(f"ℹ️ '{file.name}' already in knowledge base")
    
    with col_status:
        st.metric("Documents Indexed", len(st.session_state.knowledge_base))
        
        if st.session_state.knowledge_base:
            total_size = sum(doc['size'] for doc in st.session_state.knowledge_base)
            st.caption(f"📦 Total: {total_size / 1024:.1f} KB")
    
    st.markdown("---")
    
    # Knowledge base list
    if st.session_state.knowledge_base:
        st.markdown("#### 📖 Indexed Documents")
        
        for idx, doc in enumerate(st.session_state.knowledge_base):
            with st.expander(f"{doc['icon']} {doc['name']}", expanded=False):
                col_info, col_action = st.columns([3, 1])
                
                with col_info:
                    st.markdown(f"**Type**: {doc['type']}")
                    st.markdown(f"**Size**: {doc['size'] / 1024:.1f} KB")
                    st.markdown(f"**Chunks**: {doc['chunks']} segments")
                    st.markdown(f"**Usage**: {doc['usage_count']} times referenced by AI")
                    
                    # Show preview of content
                    if doc.get('preview'):
                        st.caption(f"Preview: {doc['preview'][:150]}...")
                
                with col_action:
                    if st.button("🗑️ Remove", key=f"remove_{idx}", width='stretch'):
                        st.session_state.knowledge_base.pop(idx)
                        st.toast(f"Removed {doc['name']}", icon="🗑️")
                        st.rerun()
        
        # Clear all button
        if st.button("🗑️ Clear All Documents", type="secondary"):
            st.session_state.knowledge_base = []
            st.toast("Knowledge base cleared", icon="✅")
            st.rerun()
    
    else:
        st.info("📂 No documents uploaded yet. Upload PDFs or docs for the AI to reference.")
    
    st.markdown("---")
    
    # How it works section
    with st.expander("ℹ️ How RAG Knowledge Base Works"):
        st.markdown("""
        **What is RAG?**  
        Retrieval-Augmented Generation allows the AI to search uploaded documents 
        and include relevant facts in its responses.
        
        **Example Use Cases:**
        - **HOA Rules**: "Are dogs allowed in the Avery Ranch HOA?"  
          → AI searches HOA PDF and answers accurately
        
        - **School Zones**: "What elementary school serves this address?"  
          → AI references school district map
        
        - **Local Taxes**: "What's the property tax rate in this area?"  
          → AI pulls from uploaded tax documents
        
        **Supported Formats:**
        - 📄 PDF (most common for HOA docs, listings)
        - 📝 TXT/MD (market reports, notes)
        - 📃 DOCX (neighborhood guides)
        
        **Privacy:**  
        Documents are stored in your session only. Not shared between users.
        """)


def process_document(file, file_hash: str) -> Dict:
    """
    Process uploaded document and prepare for RAG
    
    In production, this would:
    1. Extract text from PDF/DOCX
    2. Chunk text into segments
    3. Generate embeddings
    4. Store in vector database (Pinecone/ChromaDB)
    
    For demo, we simulate this process
    """
    
    # Read file content
    try:
        content = file.read().decode('utf-8') if file.type == 'text/plain' else file.read()
        file.seek(0)
    except:
        content = file.read()
    
    # Determine file type and icon
    file_type = file.type
    if 'pdf' in file_type:
        icon = "📄"
    elif 'word' in file_type or 'docx' in file_type:
        icon = "📃"
    else:
        icon = "📝"
    
    # Simulate chunking (in production, use LangChain or LlamaIndex)
    # Each chunk should be ~500-1000 tokens
    content_length = len(content) if isinstance(content, str) else len(content)
    estimated_chunks = max(1, content_length // 1000)
    
    # Generate preview
    if isinstance(content, str):
        preview = content[:500]
    else:
        preview = "Binary content (PDF/DOCX)"
    
    return {
        'name': file.name,
        'type': file_type,
        'size': file.size,
        'hash': file_hash,
        'chunks': estimated_chunks,
        'usage_count': 0,
        'icon': icon,
        'preview': preview,
        'uploaded_at': str(st.session_state.get('current_time', 'now'))
    }


def get_knowledge_base_context(query: str) -> str:
    """
    Retrieve relevant context from knowledge base for a query
    
    In production, this would:
    1. Generate embedding for query
    2. Search vector database
    3. Return top-k most relevant chunks
    
    For demo, we return a simulated response
    """
    
    if 'knowledge_base' not in st.session_state or not st.session_state.knowledge_base:
        return ""
    
    # Simulate retrieval (in production, use semantic search)
    relevant_docs = []
    query_lower = query.lower()
    
    for doc in st.session_state.knowledge_base:
        # Simple keyword matching (in production, use embeddings)
        if any(keyword in query_lower for keyword in ['hoa', 'rules', 'breed', 'pet']):
            if 'hoa' in doc['name'].lower():
                relevant_docs.append(doc)
                doc['usage_count'] += 1
        
        if any(keyword in query_lower for keyword in ['school', 'education', 'elementary']):
            if 'school' in doc['name'].lower():
                relevant_docs.append(doc)
                doc['usage_count'] += 1
        
        if any(keyword in query_lower for keyword in ['tax', 'rate', 'property tax']):
            if 'tax' in doc['name'].lower():
                relevant_docs.append(doc)
                doc['usage_count'] += 1
    
    if relevant_docs:
        context = f"[Retrieved from {len(relevant_docs)} document(s): {', '.join(d['name'] for d in relevant_docs)}]\n\n"
        return context
    
    return ""
