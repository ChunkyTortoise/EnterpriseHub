
import os
import shutil
import chromadb
from ghl_real_estate_ai.core.rag_engine import RAGEngine

def debug_rag():
    persist_dir = "./.debug_chroma"
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)
        
    rag = RAGEngine(
        collection_name="debug_collection",
        persist_directory=persist_dir
    )
    
    print("Adding document...")
    rag.add_documents(
        documents=["Tenant A info"],
        ids=["a1"],
        location_id="TENANT_A"
    )
    
    print("Searching with filter...")
    results = rag.search("info", location_id="TENANT_A")
    print(f"Results with filter: {len(results)}")
    for r in results:
        print(f" - {r.text} (metadata: {r.metadata})")
        
    print("Searching WITHOUT filter (modifying rag_engine.py logic temporarily in memory)...")
    # We can't easily modify it in memory here, but we can check raw chroma
    raw_results = rag._collection.get(ids=["a1"], include=['documents', 'metadatas'])
    print(f"Raw collection get: {raw_results}")

    raw_query = rag._collection.query(
        query_embeddings=[rag.embedding_model.embed_query("info")],
        n_results=10
    )
    print(f"Raw query (no filter) ids: {raw_query['ids']}")
    
    raw_query_filtered = rag._collection.query(
        query_embeddings=[rag.embedding_model.embed_query("info")],
        n_results=10,
        where={"location_id": "TENANT_A"}
    )
    print(f"Raw query (filtered $eq) ids: {raw_query_filtered['ids']}")

    raw_query_in = rag._collection.query(
        query_embeddings=[rag.embedding_model.embed_query("info")],
        n_results=10,
        where={"location_id": {"$in": ["TENANT_A", "global"]}}
    )
    print(f"Raw query (filtered $in) ids: {raw_query_in['ids']}")

if __name__ == "__main__":
    debug_rag()
