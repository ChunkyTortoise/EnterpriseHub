"""Optional vector store backends for AgentForge.

This package provides optional vector store implementations that can be
installed as extras. Each backend is lazily imported to avoid requiring
dependencies that aren't needed.

Available backends:
- Qdrant: Production-grade vector database (pip install agentforge[qdrant])
- ChromaDB: Embedded vector database (pip install agentforge[chroma])
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agentforge.memory.stores.chroma_store import ChromaVectorStore
    from agentforge.memory.stores.qdrant_store import QdrantVectorStore

__all__ = [
    "QdrantVectorStore",
    "ChromaVectorStore",
]


def __getattr__(name: str):
    """Lazy import of optional backends."""
    if name == "QdrantVectorStore":
        from agentforge.memory.stores.qdrant_store import QdrantVectorStore

        return QdrantVectorStore
    elif name == "ChromaVectorStore":
        from agentforge.memory.stores.chroma_store import ChromaVectorStore

        return ChromaVectorStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
