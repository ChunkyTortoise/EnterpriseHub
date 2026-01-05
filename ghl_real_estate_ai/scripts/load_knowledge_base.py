"""
Knowledge Base Loader Script.

Loads property listings and FAQ data into Chroma vector database
for RAG-powered AI responses.

Usage:
    python scripts/load_knowledge_base.py
"""
import json
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ghl_real_estate_ai.core.rag_engine import RAGEngine
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

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


def load_property_listings(location_id: str = "global"):
    """Load property listings into vector database."""
    logger.info(f"Loading property listings for location: {location_id}...")

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
        ids.append(f"property_{location_id}_{i}")

    # Add to collection
    rag_engine.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        location_id=location_id
    )

    logger.info(f"Loaded {len(documents)} property listings")


def load_faq(location_id: str = "global"):
    """Load FAQ data into vector database."""
    logger.info(f"Loading FAQ data for location: {location_id}...")

    # Files to load
    faq_files = [
        'data/knowledge_base/real_estate_faq.json',
        'data/knowledge_base/seller_faq.json'
    ]

    # Initialize RAG engine
    rag_engine = RAGEngine(
        collection_name=settings.chroma_collection_name,
        persist_directory=settings.chroma_persist_directory
    )

    total_loaded = 0
    for filepath in faq_files:
        if not Path(filepath).exists():
            logger.warning(f"FAQ file not found: {filepath}")
            continue

        data = load_json_file(filepath)
        faqs = data.get('faq', [])

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
                "question": faq['question'],
                "source_file": filepath
            })
            # Use unique IDs based on location, filename and index
            file_slug = Path(filepath).stem
            ids.append(f"faq_{location_id}_{file_slug}_{i}")

        # Add to collection
        if documents:
            rag_engine.add_documents(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
                location_id=location_id
            )
            total_loaded += len(documents)
            logger.info(f"Loaded {len(documents)} FAQ entries from {filepath}")

    logger.info(f"Total FAQ entries loaded: {total_loaded}")


def main():
    """Main function to load all knowledge base data."""
    parser = argparse.ArgumentParser(description="Load knowledge base into RAG engine.")
    parser.add_argument("--location_id", type=str, default="global", help="Location ID for the documents (default: global)")
    parser.add_argument("--clear", action="store_true", help="Clear the collection before loading")
    args = parser.parse_args()

    logger.info(f"Starting knowledge base loading for location: {args.location_id}")

    try:
        if args.clear:
            rag_engine = RAGEngine(
                collection_name=settings.chroma_collection_name,
                persist_directory=settings.chroma_persist_directory
            )
            rag_engine.clear()
            logger.info("Cleared existing vector store")

        # Load property listings
        load_property_listings(location_id=args.location_id)

        # Load FAQ
        load_faq(location_id=args.location_id)

        logger.info("Knowledge base loaded successfully!")
        logger.info(f"Data persisted to: {settings.chroma_persist_directory}")

    except Exception as e:
        logger.error(f"Error loading knowledge base: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
