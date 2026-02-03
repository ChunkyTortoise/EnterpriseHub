"""
Embedding model wrapper for sentence transformers.

Provides a simple interface for generating embeddings using sentence-transformers.
"""
import numpy as np
from typing import List
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers not installed. Using dummy embeddings.")
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class EmbeddingModel:
    """
    Wrapper around sentence-transformers for generating embeddings.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding model (lazy-loaded on first use).

        Args:
            model_name: Name of the sentence-transformers model to use
        """
        self.model_name = model_name
        self._model = None
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.warning("Embedding model initialized in DUMMY mode")

    @property
    def model(self):
        if self._model is None and SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.info(f"Loading embedding model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
        return self._model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.

        Args:
            texts: List of text documents to embed

        Returns:
            List of embeddings (each embedding is a list of floats)
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            # Return dummy embeddings (zero vectors of typical size 384)
            return [[0.0] * 384 for _ in texts]
            
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
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return [0.0] * 384
            
        embedding = self.model.encode([query], convert_to_numpy=True)
        return embedding[0].tolist()
