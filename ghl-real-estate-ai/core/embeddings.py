"""
Embedding model wrapper for sentence transformers.

Provides a simple interface for generating embeddings using sentence-transformers.
"""
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from ghl_utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingModel:
    """
    Wrapper around sentence-transformers for generating embeddings.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding model.

        Args:
            model_name: Name of the sentence-transformers model to use
        """
        self.model_name = model_name
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded successfully")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.

        Args:
            texts: List of text documents to embed

        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a single query.

        Args:
            query: Text query to embed

        Returns:
            Embedding vector as list of floats
        """
        embedding = self.model.encode([query], convert_to_numpy=True)
        return embedding[0].tolist()
