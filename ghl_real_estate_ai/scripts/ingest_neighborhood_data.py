"""
Batch Neighborhood Data Ingestor.

Ingests neighborhood-specific data (zoning, schools, market stats)
into Chroma vector database for Hyper-Local RAG.

Usage:
    python ghl_real_estate_ai/scripts/ingest_neighborhood_data.py --dir data/neighborhoods
"""
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ghl_real_estate_ai.core.rag_engine import RAGEngine
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

def parse_filename(filename: str) -> tuple:
    """
    Extract neighborhood and data type from filename.
    Expected format: NeighborhoodName_DataType.txt
    """
    stem = Path(filename).stem
    if '_' in stem:
        neighborhood, data_type = stem.split('_', 1)
        return neighborhood, data_type
    return stem, "general"

def ingest_directory(directory_path: str, location_id: str = "global"):
    """
    Iterate through directory and ingest all .txt files.
    """
    path = Path(directory_path)
    if not path.exists():
        logger.error(f"Directory not found: {directory_path}")
        return

    # Initialize RAG engine
    rag_engine = RAGEngine(
        collection_name=settings.chroma_collection_name,
        persist_directory=settings.chroma_persist_directory
    )

    files_processed = 0
    for file_path in path.glob("*.txt"):
        try:
            neighborhood, data_type = parse_filename(file_path.name)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            logger.info(f"Ingesting {data_type} for {neighborhood}...")
            rag_engine.ingest_neighborhood_data(
                neighborhood=neighborhood,
                data_type=data_type,
                content=content,
                location_id=location_id
            )
            files_processed += 1
        except Exception as e:
            logger.error(f"Failed to ingest {file_path.name}: {e}")

    logger.info(f"Batch ingestion complete. Processed {files_processed} files.")

def main():
    parser = argparse.ArgumentParser(description="Batch ingest neighborhood data.")
    parser.add_argument("--dir", type=str, required=True, help="Directory containing neighborhood .txt files")
    parser.add_argument("--location_id", type=str, default="global", help="Location ID (default: global)")
    args = parser.parse_args()

    ingest_directory(args.dir, args.location_id)

if __name__ == "__main__":
    main()
