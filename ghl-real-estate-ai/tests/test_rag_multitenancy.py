"""
Tests for RAG Multitenancy scoping.
"""
import pytest
import os
import shutil
from core.rag_engine import RAGEngine

def create_rag(name):
    """Create a RAG engine with a specific directory."""
    persist_dir = f"./.test_chroma_db_{name}"
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)
        
    rag = RAGEngine(
        collection_name=f"test_collection_{name}",
        persist_directory=persist_dir
    )
    return rag, persist_dir

def test_multitenancy_scoping():
    """Verify that search is correctly scoped by location_id."""
    temp_rag, persist_dir = create_rag("scoping")
    try:
        # 1. Add global document
        temp_rag.add_documents(
            documents=["This is a global real estate guide."],
            metadatas=[{"type": "faq"}],
            ids=["global_1"],
            location_id="global"
        )
        
        # 2. Add Tenant A document
        temp_rag.add_documents(
            documents=["Private listing for Tenant A in Austin."],
            metadatas=[{"type": "listing"}],
            ids=["tenant_a_1"],
            location_id="TENANT_A"
        )
        
        # 3. Add Tenant B document
        temp_rag.add_documents(
            documents=["Private listing for Tenant B in Dallas."],
            metadatas=[{"type": "listing"}],
            ids=["tenant_b_1"],
            location_id="TENANT_B"
        )
        
        # 4. Search as Tenant A
        results_a = temp_rag.search("listing", location_id="TENANT_A")
        texts_a = [r.text for r in results_a]
        assert any("Tenant A" in t for t in texts_a)
        assert any("global" in t.lower() for t in texts_a)
        assert not any("Tenant B" in t for t in texts_a)
        
        # 5. Search as Tenant B
        results_b = temp_rag.search("listing", location_id="TENANT_B")
        texts_b = [r.text for r in results_b]
        assert any("Tenant B" in t for t in texts_b)
        assert any("global" in t.lower() for t in texts_b)
        assert not any("Tenant A" in t for t in texts_b)
    finally:
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)

def test_multitenancy_no_global():
    """Verify scoping when no global documents exist."""
    temp_rag, persist_dir = create_rag("no_global")
    try:
        temp_rag.add_documents(
            documents=["Tenant A info"],
            ids=["a1"],
            location_id="TENANT_A"
        )
        
        # Search as Tenant B
        results_b = temp_rag.search("info", location_id="TENANT_B")
        assert len(results_b) == 0
        
        # Search as Tenant A
        results_a = temp_rag.search("info", location_id="TENANT_A")
        assert len(results_a) == 1
        assert "Tenant A" in results_a[0].text
    finally:
        if os.path.exists(persist_dir):
            shutil.rmtree(persist_dir)
