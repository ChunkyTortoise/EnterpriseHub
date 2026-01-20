"""
Core modules for GHL Real Estate AI.

This module provides the foundational components including:
- ServiceRegistry: Unified access point for all backend services
- RAG Engine: Retrieval-augmented generation for AI responses
- LLM Client: Language model integration
- Embeddings: Vector embeddings for semantic search
"""

from .service_registry import ServiceRegistry

# Optional imports - don't fail if not available
try:
    from .rag_engine import RAGEngine
except (ImportError, Exception):
    RAGEngine = None

try:
    from .llm_client import LLMClient
except ImportError:
    LLMClient = None

try:
    from .embeddings import EmbeddingManager
except ImportError:
    try:
        from .embeddings import EmbeddingService
    except ImportError:
        EmbeddingManager = None
        EmbeddingService = None

try:
    from .conversation_manager import ConversationManager
except ImportError:
    ConversationManager = None

__all__ = [
    "ServiceRegistry",
    "RAGEngine",
    "LLMClient",
    "EmbeddingManager",
    "ConversationManager",
]
