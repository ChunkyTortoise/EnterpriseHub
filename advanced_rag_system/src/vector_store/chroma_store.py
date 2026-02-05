"""ChromaDB vector store implementation.

Production-ready vector storage using ChromaDB with support for
metadata filtering, batch operations, and efficient similarity search.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings as ChromaSettings

from src.core.config import get_settings
from src.core.exceptions import NotFoundError, VectorStoreError
from src.core.types import DocumentChunk, SearchResult
from src.vector_store.base import SearchOptions, VectorStore, VectorStoreConfig


class ChromaVectorStore(VectorStore):
    """ChromaDB vector store implementation.

    Provides persistent vector storage with:
    - Automatic collection management
    - Metadata filtering
    - Batch operations
    - Efficient similarity search

    Example:
        ```python
        config = VectorStoreConfig(
            collection_name="documents",
            dimension=1536,
            distance_metric="cosine"
        )
        store = ChromaVectorStore(config)
        await store.initialize()

        # Add chunks
        await store.add_chunks(chunks)

        # Search
        results = await store.search(embedding, SearchOptions(top_k=5))
        ```
    """

    def __init__(
        self,
        config: Optional[VectorStoreConfig] = None,
        persist_directory: Optional[str] = None,
    ) -> None:
        """Initialize ChromaDB vector store.

        Args:
            config: Vector store configuration
            persist_directory: Directory for persistent storage
        """
        super().__init__(config)
        settings = get_settings()

        self._persist_directory = persist_directory or settings.vector_store_path
        self._client: Optional[chromadb.Client] = None
        self._collection: Optional[Collection] = None

    async def initialize(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            # Configure ChromaDB settings (v1.4.1+ uses new client API)
            # Use PersistentClient for local storage
            self._client = chromadb.PersistentClient(
                path=self._persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False),
            )

            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={
                    "hnsw:space": self._map_distance_metric(self.config.distance_metric),
                    "dimension": str(self.config.dimension),
                },
            )

            self._initialized = True

        except Exception as e:
            raise VectorStoreError(
                message=f"Failed to initialize ChromaDB: {str(e)}",
                error_code="INIT_ERROR",
                store_type="chroma",
            )

    async def close(self) -> None:
        """Close ChromaDB client and persist data."""
        if self._client is not None:
            # ChromaDB persists automatically
            self._client = None
            self._collection = None
        self._initialized = False

    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks to the store.

        Args:
            chunks: List of chunks to add

        Raises:
            VectorStoreError: If operation fails
        """
        self._ensure_initialized()

        if not chunks:
            return

        try:
            # Prepare batch data
            ids = []
            embeddings = []
            documents = []
            metadatas = []

            for chunk in chunks:
                if chunk.embedding is None:
                    raise VectorStoreError(
                        message=f"Chunk {chunk.id} has no embedding",
                        error_code="MISSING_EMBEDDING",
                        store_type="chroma",
                    )

                self._validate_embedding(chunk.embedding)

                ids.append(str(chunk.id))
                embeddings.append(chunk.embedding)
                documents.append(chunk.content)
                metadatas.append(self._chunk_to_metadata(chunk))

            # Add to collection
            if self._collection is None:
                raise VectorStoreError(
                    message="Collection not initialized",
                    error_code="NOT_INITIALIZED",
                    store_type="chroma",
                )

            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )

        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(
                message=f"Failed to add chunks: {str(e)}",
                error_code="ADD_ERROR",
                store_type="chroma",
            )

    async def delete_chunks(self, chunk_ids: List[UUID]) -> None:
        """Delete chunks by their IDs.

        Args:
            chunk_ids: List of chunk IDs to delete

        Raises:
            VectorStoreError: If operation fails
        """
        self._ensure_initialized()

        if not chunk_ids:
            return

        try:
            if self._collection is None:
                raise VectorStoreError(
                    message="Collection not initialized",
                    error_code="NOT_INITIALIZED",
                    store_type="chroma",
                )

            self._collection.delete(ids=[str(id) for id in chunk_ids])

        except Exception as e:
            raise VectorStoreError(
                message=f"Failed to delete chunks: {str(e)}",
                error_code="DELETE_ERROR",
                store_type="chroma",
            )

    async def search(
        self,
        query_embedding: List[float],
        options: Optional[SearchOptions] = None,
    ) -> List[SearchResult]:
        """Search for similar vectors.

        Args:
            query_embedding: Query vector
            options: Search options

        Returns:
            List of search results

        Raises:
            VectorStoreError: If search fails
        """
        self._ensure_initialized()

        if options is None:
            options = SearchOptions()

        self._validate_embedding(query_embedding)

        try:
            if self._collection is None:
                raise VectorStoreError(
                    message="Collection not initialized",
                    error_code="NOT_INITIALIZED",
                    store_type="chroma",
                )

            # Build where clause for filters
            where_clause = self._build_where_clause(options.filters)

            # Execute query
            results = self._collection.query(
                query_embeddings=[query_embedding],
                n_results=options.top_k,
                where=where_clause if where_clause else None,
                include=["metadatas", "documents", "distances", "embeddings"]
                if options.include_embeddings
                else ["metadatas", "documents", "distances"],
            )

            # Convert to SearchResult objects
            search_results: List[SearchResult] = []

            if not results["ids"] or not results["ids"][0]:
                return search_results

            for i, chunk_id in enumerate(results["ids"][0]):
                # Get distance and convert to score
                distance = results["distances"][0][i]
                score = self._distance_to_score(distance)

                # Skip if below threshold
                if score < options.threshold:
                    continue

                # Get metadata and document
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                document = results["documents"][0][i] if results["documents"] else ""
                embedding = None
                if options.include_embeddings and results.get("embeddings"):
                    embedding = results["embeddings"][0][i]

                # Create chunk
                chunk_data = {
                    "id": chunk_id,
                    "document_id": metadata.get("document_id", ""),
                    "content": document,
                    "index": metadata.get("index", 0),
                    "token_count": metadata.get("token_count", 0),
                    "metadata": metadata,
                }
                chunk = self._dict_to_chunk(chunk_data, embedding)

                # Create search result
                search_result = SearchResult(
                    chunk=chunk,
                    score=score,
                    rank=i + 1,
                    distance=distance,
                )
                search_results.append(search_result)

            return search_results

        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(
                message=f"Search failed: {str(e)}",
                error_code="SEARCH_ERROR",
                store_type="chroma",
            )

    async def get_chunk(self, chunk_id: UUID) -> Optional[DocumentChunk]:
        """Get a specific chunk by ID.

        Args:
            chunk_id: Chunk ID

        Returns:
            Document chunk or None if not found
        """
        self._ensure_initialized()

        try:
            if self._collection is None:
                raise VectorStoreError(
                    message="Collection not initialized",
                    error_code="NOT_INITIALIZED",
                    store_type="chroma",
                )

            result = self._collection.get(
                ids=[str(chunk_id)],
                include=["metadatas", "documents", "embeddings"],
            )

            if not result["ids"] or not result["ids"][0]:
                return None

            metadata = result["metadatas"][0] if result["metadatas"] else {}
            document = result["documents"][0] if result["documents"] else ""
            embedding = result["embeddings"][0] if result.get("embeddings") else None

            chunk_data = {
                "id": str(chunk_id),
                "document_id": metadata.get("document_id", ""),
                "content": document,
                "index": metadata.get("index", 0),
                "token_count": metadata.get("token_count", 0),
                "metadata": metadata,
            }

            return self._dict_to_chunk(chunk_data, embedding)

        except Exception as e:
            raise VectorStoreError(
                message=f"Failed to get chunk: {str(e)}",
                error_code="GET_ERROR",
                store_type="chroma",
            )

    async def update_chunk(self, chunk: DocumentChunk) -> None:
        """Update an existing chunk.

        Args:
            chunk: Updated chunk data

        Raises:
            VectorStoreError: If chunk doesn't exist or update fails
        """
        self._ensure_initialized()

        if chunk.embedding is None:
            raise VectorStoreError(
                message=f"Chunk {chunk.id} has no embedding",
                error_code="MISSING_EMBEDDING",
                store_type="chroma",
            )

        try:
            # Check if chunk exists
            existing = await self.get_chunk(chunk.id)
            if existing is None:
                raise NotFoundError(
                    message=f"Chunk {chunk.id} not found",
                    resource_type="chunk",
                    resource_id=str(chunk.id),
                )

            if self._collection is None:
                raise VectorStoreError(
                    message="Collection not initialized",
                    error_code="NOT_INITIALIZED",
                    store_type="chroma",
                )

            # Update the chunk
            self._collection.update(
                ids=[str(chunk.id)],
                embeddings=[chunk.embedding],
                documents=[chunk.content],
                metadatas=[self._chunk_to_metadata(chunk)],
            )

        except NotFoundError:
            raise
        except VectorStoreError:
            raise
        except Exception as e:
            raise VectorStoreError(
                message=f"Failed to update chunk: {str(e)}",
                error_code="UPDATE_ERROR",
                store_type="chroma",
            )

    async def count(self) -> int:
        """Get the total number of chunks in the store.

        Returns:
            Total chunk count
        """
        self._ensure_initialized()

        try:
            if self._collection is None:
                return 0

            count_result = self._collection.count()
            return int(count_result) if count_result is not None else 0

        except Exception:
            return 0

    async def clear(self) -> None:
        """Clear all chunks from the store."""
        self._ensure_initialized()

        try:
            if self._collection is None:
                return

            # Delete and recreate collection
            if self._client is not None:
                self._client.delete_collection(self.config.collection_name)
                self._collection = self._client.get_or_create_collection(
                    name=self.config.collection_name,
                    metadata={
                        "hnsw:space": self._map_distance_metric(
                            self.config.distance_metric
                        ),
                        "dimension": str(self.config.dimension),
                    },
                )

        except Exception as e:
            raise VectorStoreError(
                message=f"Failed to clear store: {str(e)}",
                error_code="CLEAR_ERROR",
                store_type="chroma",
            )

    async def health_check(self) -> bool:
        """Check if the vector store is healthy.

        Returns:
            True if the store is accessible
        """
        try:
            if not self._initialized or self._client is None:
                return False

            # Try a simple operation
            self._client.heartbeat()
            return True

        except Exception:
            return False

    def _map_distance_metric(self, metric: str) -> str:
        """Map our distance metric names to ChromaDB names.

        Args:
            metric: Our metric name (cosine, euclidean, dot)

        Returns:
            ChromaDB metric name
        """
        mapping = {
            "cosine": "cosine",
            "euclidean": "l2",
            "dot": "ip",  # inner product
        }
        return mapping.get(metric.lower(), "cosine")

    def _distance_to_score(self, distance: float) -> float:
        """Convert ChromaDB distance to similarity score.

        Args:
            distance: Raw distance from ChromaDB

        Returns:
            Similarity score between 0 and 1
        """
        metric = self.config.distance_metric.lower()

        if metric == "cosine":
            # Cosine distance is 1 - cosine similarity
            return 1.0 - distance
        elif metric == "euclidean":
            # Convert L2 distance to similarity (approximate)
            # Using exponential decay
            import math

            return math.exp(-distance)
        elif metric == "dot":
            # For inner product, normalize to 0-1 range
            # Assuming inputs are normalized, dot product is cosine similarity
            return (distance + 1.0) / 2.0

        return max(0.0, min(1.0, 1.0 - distance))

    def _chunk_to_metadata(self, chunk: DocumentChunk) -> Dict[str, Any]:
        """Convert chunk to ChromaDB metadata format.

        Args:
            chunk: Document chunk

        Returns:
            Metadata dictionary
        """
        metadata = {
            "document_id": str(chunk.document_id),
            "index": chunk.index,
            "token_count": chunk.token_count,
            "source": chunk.metadata.source or "",
            "title": chunk.metadata.title or "",
            "author": chunk.metadata.author or "",
            "language": chunk.metadata.language,
            "tags": ",".join(chunk.metadata.tags),
        }

        # Add custom metadata fields
        for key, value in chunk.metadata.custom.items():
            # ChromaDB only supports simple types
            if isinstance(value, (str, int, float, bool)):
                metadata[key] = value

        return metadata

    def _build_where_clause(
        self, filters: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Build ChromaDB where clause from filters.

        Args:
            filters: Metadata filters

        Returns:
            ChromaDB where clause or None
        """
        if not filters:
            return None

        # Simple filter support for now
        # ChromaDB supports: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin, $and, $or
        where_clause: Dict[str, Any] = {}

        for key, value in filters.items():
            if isinstance(value, dict):
                # Already a ChromaDB-style filter
                where_clause[key] = value
            elif isinstance(value, list):
                # List becomes $in filter
                where_clause[key] = {"$in": value}
            else:
                # Simple equality
                where_clause[key] = {"$eq": value}

        return where_clause if where_clause else None