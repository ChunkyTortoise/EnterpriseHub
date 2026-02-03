"""Vector store module for Advanced RAG System.

Provides vector storage and retrieval capabilities with support
for multiple backends and metadata filtering.
"""

from src.vector_store.base import VectorStore, VectorStoreConfig, SearchOptions
from src.vector_store.in_memory_store import InMemoryVectorStore

__all__ = [
    "VectorStore",
    "VectorStoreConfig",
    "SearchOptions",
    "InMemoryVectorStore",
]

# ChromaVectorStore import is optional due to chromadb compatibility issues
# with pydantic v2 on Python 3.14+
try:
    from src.vector_store.chroma_store import ChromaVectorStore
    __all__.append("ChromaVectorStore")
except (ImportError, Exception):
    pass

# Production ChromaDB with enterprise features
try:
    from src.vector_store.chroma_production import (
        ProductionChromaStore,
        ProductionVectorStoreConfig,
        ConnectionPool,
        ConnectionPoolConfig,
        RetryManager,
        RetryConfig,
        BackupManager,
        BackupConfig,
        BackupType,
        MigrationManager,
        MigrationConfig,
    )
    __all__.extend([
        "ProductionChromaStore",
        "ProductionVectorStoreConfig",
        "ConnectionPool",
        "ConnectionPoolConfig",
        "RetryManager",
        "RetryConfig",
        "BackupManager",
        "BackupConfig",
        "BackupType",
        "MigrationManager",
        "MigrationConfig",
    ])
except (ImportError, Exception):
    pass