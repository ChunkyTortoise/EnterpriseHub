"""
Knowledge Base Manager for GHL Real Estate AI.

Provides a CLI for auditing, adding, and removing documents from the ChromaDB vector store.
"""
import os
import sys
import argparse
import json
from typing import List, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ghl_real_estate_ai.core.rag_engine import RAGEngine
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

def list_documents(rag: RAGEngine, limit: int = 100):
    """List all documents in the knowledge base."""
    # Note: RAGEngine doesn't have a direct 'list all' but we can access collection
    collection = rag.collection
    results = collection.get(limit=limit)
    
    if not results or not results['ids']:
        print("\nKnowledge base is empty.")
        return

    print(f"\nKnowledge Base Audit ({len(results['ids'])} documents):")
    print("-" * 80)
    for i in range(len(results['ids'])):
        doc_id = results['ids'][i]
        meta = results['metadatas'][i]
        content_preview = results['documents'][i][:100].replace('\n', ' ')
        
        print(f"ID: {doc_id}")
        print(f"Category: {meta.get('category', 'N/A')}")
        print(f"Location: {meta.get('location_id', 'Global')}")
        print(f"Preview: {content_preview}...")
        print("-" * 40)

def add_document(rag: RAGEngine, text: str, category: str, location_id: Optional[str] = None):
    """Add a single document to the knowledge base."""
    from ghl_real_estate_ai.core.rag_engine import Document
    
    doc = Document(
        text=text,
        metadata={
            "category": category,
            "location_id": location_id or "global"
        }
    )
    
    rag.add_documents([doc])
    print(f"\nSuccessfully added document to {category}.")

def import_json(rag: RAGEngine, file_path: str):
    """Import multiple documents from a JSON file."""
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    with open(file_path, 'r') as f:
        data = json.load(f)

    from ghl_real_estate_ai.core.rag_engine import Document
    docs = []
    for item in data:
        docs.append(Document(
            text=item['text'],
            metadata=item.get('metadata', {"category": "general", "location_id": "global"})
        ))
    
    rag.add_documents(docs)
    print(f"\nSuccessfully imported {len(docs)} documents.")

def clear_kb(rag: RAGEngine):
    """Clear all documents from the knowledge base."""
    confirm = input("Are you sure you want to CLEAR the entire knowledge base? (y/N): ")
    if confirm.lower() == 'y':
        # Re-initialize collection (deletes old one)
        rag.client.delete_collection(settings.chroma_collection_name)
        rag.collection = rag.client.create_collection(
            name=settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print("\nKnowledge base cleared.")
    else:
        print("\nOperation cancelled.")

def main():
    parser = argparse.ArgumentParser(description="Manage GHL Real Estate AI Knowledge Base")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # List
    subparsers.add_parser("list", help="List all documents")

    # Add
    add_parser = subparsers.add_parser("add", help="Add a document")
    add_parser.add_argument("--text", required=True, help="Document text")
    add_parser.add_argument("--category", default="general", help="Category (listing, market, faq)")
    add_parser.add_argument("--location", help="GHL Location ID (optional)")

    # Import
    import_parser = subparsers.add_parser("import", help="Import from JSON file")
    import_parser.add_argument("--file", required=True, help="Path to JSON file")

    # Clear
    subparsers.add_parser("clear", help="Clear all documents")

    args = parser.parse_args()

    # Initialize RAG
    rag = RAGEngine(
        collection_name=settings.chroma_collection_name,
        persist_directory=settings.chroma_persist_directory
    )

    if args.command == "list":
        list_documents(rag)
    elif args.command == "add":
        add_document(rag, args.text, args.category, args.location)
    elif args.command == "import":
        import_json(rag, args.file)
    elif args.command == "clear":
        clear_kb(rag)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
