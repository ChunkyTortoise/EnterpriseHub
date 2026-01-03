"""
Knowledge Base Loader Script.

Loads property listings and FAQ data into Chroma vector database
for RAG-powered AI responses.

Usage:
    python scripts/load_knowledge_base.py
"""
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rag_engine import RAGEngine
from ghl_utils.config import settings
from ghl_utils.logger import get_logger

logger = get_logger(__name__)


def load_json_file(filepath: str) -> list:
    """
    Load JSON file and return data.

    Args:
        filepath: Path to JSON file

    Returns:
        List of data objects
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def load_property_listings():
    """Load property listings into vector database."""
    logger.info("Loading property listings...")

    # Load property data
    data = load_json_file('data/knowledge_base/property_listings.json')
    properties = data.get('listings', [])

    # Initialize RAG engine
    rag_engine = RAGEngine(
        collection_name=settings.chroma_collection_name,
        persist_directory=settings.chroma_persist_directory
    )

    # Prepare documents
    documents = []
    metadatas = []
    ids = []

    for i, prop in enumerate(properties):
        # Extract address details
        address_dict = prop.get('address', {})
        street = address_dict.get('street', 'Unknown')
        neighborhood = address_dict.get('neighborhood', 'Unknown')
        full_address = f"{street}, {address_dict.get('city', 'Austin')}, {address_dict.get('state', 'TX')} {address_dict.get('zip', '')}"

        # Create rich document text
        doc_text = f"""Property: {full_address}
Price: ${prop['price']:,}
Bedrooms: {prop['bedrooms']} | Bathrooms: {prop['bathrooms']} | Square Feet: {prop['sqft']}
Neighborhood: {neighborhood}
Description: {prop['description']}
Features: {', '.join(prop.get('features', []))}
Schools: {', '.join([s['name'] for s in prop.get('schools', [])])}
"""

        documents.append(doc_text)
        metadatas.append({
            "type": "property_listing",
            "category": "listing",
            "address": full_address,
            "price": prop['price'],
            "bedrooms": prop['bedrooms'],
            "bathrooms": prop['bathrooms'],
            "neighborhood": neighborhood
        })
        ids.append(f"property_{i}")

    # Add to collection
    rag_engine.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    logger.info(f"Loaded {len(documents)} property listings")


def load_faq():
    """Load FAQ data into vector database."""
    logger.info("Loading FAQ data...")

    # Load FAQ data
    data = load_json_file('data/knowledge_base/real_estate_faq.json')
    faqs = data.get('faq', [])

    # Initialize RAG engine
    rag_engine = RAGEngine(
        collection_name=settings.chroma_collection_name,
        persist_directory=settings.chroma_persist_directory
    )

    # Prepare documents
    documents = []
    metadatas = []
    ids = []

    for i, faq in enumerate(faqs):
        # Create document text
        doc_text = f"""Question: {faq['question']}
Answer: {faq['answer']}
"""

        documents.append(doc_text)
        metadatas.append({
            "type": "faq",
            "category": faq.get('category', 'general'),
            "question": faq['question']
        })
        ids.append(f"faq_{i}")

    # Add to collection
    rag_engine.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    logger.info(f"Loaded {len(documents)} FAQ entries")


def main():
    """Main function to load all knowledge base data."""
    logger.info("Starting knowledge base loading...")

    try:
        # Load property listings
        load_property_listings()

        # Load FAQ
        load_faq()

        logger.info("Knowledge base loaded successfully!")
        logger.info(f"Data persisted to: {settings.chroma_persist_directory}")

    except Exception as e:
        logger.error(f"Error loading knowledge base: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
