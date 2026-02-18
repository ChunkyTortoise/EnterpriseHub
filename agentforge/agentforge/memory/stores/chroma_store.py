"""ChromaDB vector store backend for AgentForge.

This module provides a ChromaDB-based vector store implementation for
embedded vector database needs. ChromaDB is an open-source embedding
database that's easy to get started with.

Installation:
    pip install agentforge[chroma]

Features:
- Embedded (local) or server mode
- Automatic embedding generation (optional)
- Persistent storage
- Metadata filtering
"""

from typing import Any, Optional

from agentforge.memory.vector_base import VectorEntry, VectorSearchResult, VectorStore


class ChromaVectorStore(VectorStore):
    """ChromaDB vector store backend.

    An embedded vector store using ChromaDB. Supports both ephemeral
    (in-memory) and persistent storage modes.

    Features:
    - Easy setup and use
    - Persistent storage option
    - Metadata filtering
    - Optional automatic embedding generation

    Example:
        ```python
        # Ephemeral (in-memory) mode
        store = ChromaVectorStore()

        # Persistent mode
        store = ChromaVectorStore(persist_directory="./chroma_db")

        # Insert and search
        entry = VectorEntry(
            id="doc1",
            vector=[0.1, 0.2, 0.3, ...],
            content="Hello world",
            metadata={"source": "greeting"}
        )
        await store.insert(entry)
        results = await store.search(query_vector, top_k=5)
        ```
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "agentforge",
        embedding_function: Optional[Any] = None,
    ) -> None:
        """Initialize ChromaDB vector store.

        Args:
            persist_directory: Directory for persistent storage. If None,
                uses ephemeral (in-memory) mode.
            collection_name: Name of the collection to use.
            embedding_function: Optional embedding function for automatic
                embedding generation. If provided, you can add documents
                without pre-computed embeddings.

        Raises:
            ImportError: If chromadb is not installed.
        """
        try:
            import chromadb
        except ImportError as e:
            raise ImportError(
                "chromadb is required for ChromaVectorStore. "
                "Install with: pip install agentforge[chroma]"
            ) from e

        self.collection_name = collection_name
        self._embedding_function = embedding_function

        # Initialize client
        if persist_directory:
            self._client = chromadb.PersistentClient(path=persist_directory)
        else:
            self._client = chromadb.EphemeralClient()

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )

    async def insert(self, entry: VectorEntry) -> str:
        """Insert a vector entry into ChromaDB.

        Args:
            entry: The vector entry to insert.

        Returns:
            The ID of the inserted entry.
        """
        # Build metadata with content and created_at
        metadata: dict[str, Any] = entry.metadata.copy()
        if entry.content:
            metadata["_content"] = entry.content
        if entry.created_at:
            metadata["_created_at"] = entry.created_at

        self._collection.upsert(
            ids=[entry.id],
            embeddings=[entry.vector],
            metadatas=[metadata],
            documents=[entry.content] if entry.content else None,
        )

        return entry.id

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        filter_metadata: Optional[dict[str, Any]] = None,
    ) -> list[VectorSearchResult]:
        """Search for similar vectors in ChromaDB.

        Args:
            query_vector: The query embedding vector.
            top_k: Maximum number of results to return.
            filter_metadata: Optional metadata filters.

        Returns:
            List of search results sorted by similarity.
        """
        # Build where filter for metadata
        where_filter = None
        if filter_metadata:
            # ChromaDB uses $and for multiple conditions
            conditions = [{k: v} for k, v in filter_metadata.items()]
            if len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = {"$and": conditions}

        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where_filter,
            include=["metadatas", "distances", "documents"],
        )

        # ChromaDB returns lists of lists
        ids = results.get("ids", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        documents = results.get("documents", [[]])[0]

        search_results = []
        for i, id_ in enumerate(ids):
            metadata = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else 0.0
            document = documents[i] if i < len(documents) else None

            # Extract stored content from metadata
            content = metadata.pop("_content", document)
            created_at = metadata.pop("_created_at", None)

            # Convert distance to similarity score (ChromaDB uses L2 by default)
            # For cosine similarity, we need to convert
            score = 1.0 / (1.0 + distance)  # Convert distance to similarity

            search_results.append(
                VectorSearchResult(
                    id=id_,
                    score=score,
                    metadata=metadata,
                    content=content,
                )
            )

        return search_results

    async def delete(self, id: str) -> bool:
        """Delete an entry by ID.

        Args:
            id: The unique identifier to delete.

        Returns:
            True if deleted, False if not found.
        """
        try:
            # Check if exists first
            existing = self._collection.get(ids=[id])
            if not existing or not existing.get("ids"):
                return False

            self._collection.delete(ids=[id])
            return True
        except Exception:
            return False

    async def get(self, id: str) -> Optional[VectorEntry]:
        """Get an entry by ID.

        Args:
            id: The unique identifier.

        Returns:
            The vector entry, or None if not found.
        """
        try:
            results = self._collection.get(
                ids=[id],
                include=["embeddings", "metadatas", "documents"],
            )

            if not results or not results.get("ids"):
                return None

            ids = results.get("ids", [])
            embeddings = results.get("embeddings", [])
            metadatas = results.get("metadatas", [])
            documents = results.get("documents", [])

            if not ids:
                return None

            metadata = metadatas[0] if metadatas else {}
            embedding = embeddings[0] if embeddings else []
            document = documents[0] if documents else None

            # Extract stored content and created_at
            content = metadata.pop("_content", document)
            created_at = metadata.pop("_created_at", None)

            return VectorEntry(
                id=ids[0],
                vector=embedding,
                metadata=metadata,
                content=content,
                created_at=created_at,
            )
        except Exception:
            return None

    async def count(self) -> int:
        """Count total entries in the collection.

        Returns:
            Number of entries in the collection.
        """
        return self._collection.count()

    async def insert_batch(self, entries: list[VectorEntry]) -> list[str]:
        """Insert multiple entries efficiently.

        Args:
            entries: List of vector entries to insert.

        Returns:
            List of inserted entry IDs.
        """
        ids = []
        embeddings = []
        metadatas = []
        documents = []

        for entry in entries:
            ids.append(entry.id)
            embeddings.append(entry.vector)

            metadata = entry.metadata.copy()
            if entry.content:
                metadata["_content"] = entry.content
            if entry.created_at:
                metadata["_created_at"] = entry.created_at
            metadatas.append(metadata)

            documents.append(entry.content if entry.content else None)

        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )

        return ids

    async def delete_batch(self, ids: list[str]) -> list[bool]:
        """Delete multiple entries by ID.

        Args:
            ids: List of entry IDs to delete.

        Returns:
            List of deletion success flags.
        """
        try:
            self._collection.delete(ids=ids)
            return [True] * len(ids)
        except Exception:
            return [False] * len(ids)

    async def clear(self) -> None:
        """Clear all entries from the collection."""
        # Get all IDs and delete them
        all_ids = await self.get_all_ids()
        if all_ids:
            self._collection.delete(ids=all_ids)

    async def get_all_ids(self) -> list[str]:
        """Get all entry IDs in the collection.

        Note: This retrieves all entries which can be slow for large collections.

        Returns:
            List of all entry IDs.
        """
        results = self._collection.get(include=[])
        return results.get("ids", [])

    def __repr__(self) -> str:
        """String representation of the ChromaDB store."""
        return (
            f"ChromaVectorStore(collection={self.collection_name}, "
            f"entries={self._collection.count()})"
        )


__all__ = ["ChromaVectorStore"]
