"""Structured data retrieval for tables, CSV, and JSON files.

This module provides the StructuredRetriever class that enables:
- Semantic search over tabular data (CSV, Excel, SQL tables)
- JSON document retrieval with nested field support
- Hybrid search combining structured filters with semantic similarity
- Automatic schema inference and description generation

Features:
- Table/CSV/JSON data embedding with semantic descriptions
- Structured query support with metadata filtering
- Integration with existing vector store infrastructure
- Async operations for optimal performance
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

import pandas as pd

from src.core.exceptions import RetrievalError, ValidationError
from src.core.types import DocumentChunk, Metadata, SearchResult
from src.embeddings.openai_provider import OpenAIEmbeddingConfig, OpenAIEmbeddingProvider
from src.vector_store.base import SearchOptions, VectorStore, VectorStoreConfig
from src.vector_store.chroma_store import ChromaVectorStore

logger = logging.getLogger(__name__)


@dataclass
class StructuredRetrieverConfig:
    """Configuration for structured data retriever.

    Attributes:
        collection_name: Name for the vector collection
        embedding_model: Embedding model to use
        dimensions: Embedding dimensions
        distance_metric: Distance metric for similarity
        max_rows_per_chunk: Maximum rows to include in a single chunk
        include_schema_in_description: Whether to include schema in text description
        persist_directory: Directory for persistent storage
        default_query_mode: Default query mode (semantic, structured, hybrid)
    """

    collection_name: str = "structured_data"
    embedding_model: str = "text-embedding-3-small"
    dimensions: int = 1536
    distance_metric: str = "cosine"
    max_rows_per_chunk: int = 100
    include_schema_in_description: bool = True
    persist_directory: Optional[str] = None
    default_query_mode: str = "hybrid"


@dataclass
class TableSchema:
    """Schema information for a table.

    Attributes:
        columns: Dictionary of column names to types
        sample_data: Sample rows from the table
        row_count: Total number of rows
        source: Source file or table name
    """

    columns: Dict[str, str] = field(default_factory=dict)
    sample_data: List[Dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    source: str = ""


@dataclass
class StructuredQuery:
    """Structured query for filtering data.

    Attributes:
        filters: Dictionary of column filters (column -> value or condition)
        columns: List of columns to return (None = all)
        sort_by: Column to sort by
        sort_order: Sort order (asc/desc)
        limit: Maximum number of rows to return
    """

    filters: Dict[str, Any] = field(default_factory=dict)
    columns: Optional[List[str]] = None
    sort_by: Optional[str] = None
    sort_order: str = "asc"
    limit: Optional[int] = None


class StructuredRetriever:
    """Retriever for structured data (tables, CSV, JSON).

    Provides capabilities for:
    - Semantic search over structured data using natural language
    - Structured queries with column filters
    - Hybrid search combining semantic and structured approaches
    - Automatic schema inference and description generation

    Example:
        ```python
        config = StructuredRetrieverConfig(collection_name="sales_data")
        retriever = StructuredRetriever(config)
        await retriever.initialize()

        # Index CSV file
        await retriever.index_csv("sales.csv", description="Monthly sales data")

        # Index JSON file
        await retriever.index_json("products.json", description="Product catalog")

        # Semantic search
        results = await retriever.semantic_search(
            "high value transactions in Q4",
            top_k=10
        )

        # Structured query
        query = StructuredQuery(
            filters={"region": "North America", "amount": "> 1000"},
            sort_by="date",
            sort_order="desc"
        )
        results = await retriever.structured_query(query)

        # Hybrid search
        results = await retriever.hybrid_search(
            query_text="premium customers",
            structured_query=StructuredQuery(filters={"tier": "premium"}),
            top_k=10
        )

        await retriever.close()
        ```
    """

    def __init__(self, config: Optional[StructuredRetrieverConfig] = None) -> None:
        """Initialize structured retriever.

        Args:
            config: Structured retriever configuration
        """
        self.config = config or StructuredRetrieverConfig()
        self._embedding_provider: Optional[OpenAIEmbeddingProvider] = None
        self._vector_store: Optional[VectorStore] = None
        self._initialized = False
        self._schemas: Dict[str, TableSchema] = {}
        self._document_count = 0

    async def initialize(self) -> None:
        """Initialize embedding provider and vector store.

        Raises:
            RetrievalError: If initialization fails
        """
        if self._initialized:
            return

        # Initialize embedding provider
        try:
            embed_config = OpenAIEmbeddingConfig(
                model=self.config.embedding_model,
                dimensions=self.config.dimensions,
            )
            self._embedding_provider = OpenAIEmbeddingProvider(embed_config)
            await self._embedding_provider.initialize()
            logger.info(f"Embedding provider initialized: {self.config.embedding_model}")
        except Exception as e:
            raise RetrievalError(f"Failed to initialize embedding provider: {e}") from e

        # Initialize vector store
        try:
            store_config = VectorStoreConfig(
                collection_name=self.config.collection_name,
                dimension=self.config.dimensions,
                distance_metric=self.config.distance_metric,
            )
            self._vector_store = ChromaVectorStore(
                store_config,
                persist_directory=self.config.persist_directory,
            )
            await self._vector_store.initialize()
            logger.info(f"Vector store initialized: {self.config.collection_name}")
        except Exception as e:
            raise RetrievalError(f"Failed to initialize vector store: {e}") from e

        self._initialized = True

    async def close(self) -> None:
        """Release resources and close connections."""
        if self._embedding_provider:
            await self._embedding_provider.close()
            self._embedding_provider = None

        if self._vector_store:
            await self._vector_store.close()
            self._vector_store = None

        self._initialized = False
        logger.info("Structured retriever closed")

    def _generate_table_description(
        self,
        df: pd.DataFrame,
        user_description: Optional[str] = None,
        source: str = "",
    ) -> str:
        """Generate semantic description of table for embedding.

        Args:
            df: DataFrame to describe
            user_description: Optional user-provided description
            source: Source identifier

        Returns:
            Text description suitable for embedding
        """
        parts = []

        if user_description:
            parts.append(user_description)

        parts.append(f"Table with {len(df)} rows and {len(df.columns)} columns.")

        if self.config.include_schema_in_description:
            parts.append("Columns:")
            for col in df.columns:
                dtype = str(df[col].dtype)
                sample_values = df[col].dropna().head(3).tolist()
                sample_str = ", ".join(str(v) for v in sample_values[:3])
                parts.append(f"  - {col} ({dtype}): {sample_str}")

        # Add sample data summary
        if len(df) > 0:
            parts.append("Sample data summary:")
            for col in df.select_dtypes(include=["number"]).columns:
                stats = df[col].describe()
                parts.append(f"  - {col}: min={stats['min']:.2f}, max={stats['max']:.2f}, mean={stats['mean']:.2f}")

        if source:
            parts.append(f"Source: {source}")

        return "\n".join(parts)

    def _generate_row_description(
        self,
        row: pd.Series,
        schema: TableSchema,
        table_description: str = "",
    ) -> str:
        """Generate semantic description of a single row.

        Args:
            row: DataFrame row
            schema: Table schema
            table_description: Description of the parent table

        Returns:
            Text description suitable for embedding
        """
        parts = []

        if table_description:
            parts.append(f"Record from: {table_description}")

        parts.append("Data:")
        for col, value in row.items():
            if pd.notna(value):
                parts.append(f"  {col}: {value}")

        return "\n".join(parts)

    async def index_csv(
        self,
        file_path: str,
        description: Optional[str] = None,
        **pandas_kwargs,
    ) -> List[UUID]:
        """Index a CSV file for retrieval.

        Args:
            file_path: Path to CSV file
            description: Optional description of the data
            **pandas_kwargs: Additional arguments for pd.read_csv()

        Returns:
            List of document IDs for indexed chunks

        Raises:
            RetrievalError: If indexing fails
        """
        self._ensure_initialized()

        if not os.path.exists(file_path):
            raise RetrievalError(f"File not found: {file_path}")

        try:
            df = pd.read_csv(file_path, **pandas_kwargs)
        except Exception as e:
            raise RetrievalError(f"Failed to read CSV: {e}") from e

        return await self._index_dataframe(df, file_path, description)

    async def index_excel(
        self,
        file_path: str,
        sheet_name: Union[str, int] = 0,
        description: Optional[str] = None,
        **pandas_kwargs,
    ) -> List[UUID]:
        """Index an Excel file for retrieval.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name or index
            description: Optional description of the data
            **pandas_kwargs: Additional arguments for pd.read_excel()

        Returns:
            List of document IDs for indexed chunks

        Raises:
            RetrievalError: If indexing fails
        """
        self._ensure_initialized()

        if not os.path.exists(file_path):
            raise RetrievalError(f"File not found: {file_path}")

        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name, **pandas_kwargs)
        except Exception as e:
            raise RetrievalError(f"Failed to read Excel: {e}") from e

        source = f"{file_path}#{sheet_name}"
        return await self._index_dataframe(df, source, description)

    async def index_json(
        self,
        file_path: str,
        description: Optional[str] = None,
        records_path: Optional[str] = None,
    ) -> List[UUID]:
        """Index a JSON file for retrieval.

        Args:
            file_path: Path to JSON file
            description: Optional description of the data
            records_path: Path to records if nested (e.g., "data.items")

        Returns:
            List of document IDs for indexed chunks

        Raises:
            RetrievalError: If indexing fails
        """
        self._ensure_initialized()

        if not os.path.exists(file_path):
            raise RetrievalError(f"File not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise RetrievalError(f"Failed to read JSON: {e}") from e

        # Navigate to records if path specified
        if records_path:
            parts = records_path.split(".")
            for part in parts:
                data = data.get(part, {})

        # Convert to DataFrame if list of records
        if isinstance(data, list):
            df = pd.json_normalize(data)
        elif isinstance(data, dict):
            # Single record
            df = pd.json_normalize([data])
        else:
            raise RetrievalError(f"Unsupported JSON structure in {file_path}")

        return await self._index_dataframe(df, file_path, description)

    async def index_dataframe(
        self,
        df: pd.DataFrame,
        source: str,
        description: Optional[str] = None,
    ) -> List[UUID]:
        """Index a pandas DataFrame directly.

        Args:
            df: DataFrame to index
            source: Source identifier
            description: Optional description

        Returns:
            List of document IDs for indexed chunks
        """
        self._ensure_initialized()
        return await self._index_dataframe(df, source, description)

    async def _index_dataframe(
        self,
        df: pd.DataFrame,
        source: str,
        description: Optional[str] = None,
    ) -> List[UUID]:
        """Internal method to index a DataFrame.

        Args:
            df: DataFrame to index
            source: Source identifier
            description: Optional description

        Returns:
            List of document IDs for indexed chunks
        """
        if df.empty:
            logger.warning(f"Empty DataFrame from {source}")
            return []

        # Store schema
        schema = TableSchema(
            columns={col: str(df[col].dtype) for col in df.columns},
            sample_data=df.head(5).to_dict("records"),
            row_count=len(df),
            source=source,
        )
        self._schemas[source] = schema

        # Generate table description
        table_desc = self._generate_table_description(df, description, source)

        # Split into chunks
        doc_ids = []
        chunks = []

        for start_idx in range(0, len(df), self.config.max_rows_per_chunk):
            end_idx = min(start_idx + self.config.max_rows_per_chunk, len(df))
            chunk_df = df.iloc[start_idx:end_idx]

            # Generate description for this chunk
            chunk_desc = f"Rows {start_idx} to {end_idx - 1} from {source}\n\n"
            chunk_desc += table_desc + "\n\n"
            chunk_desc += "Chunk data:\n"

            for _, row in chunk_df.iterrows():
                chunk_desc += self._generate_row_description(row, schema) + "\n---\n"

            # Generate embedding
            try:
                embedding = await self._embedding_provider.embed_query(chunk_desc)
            except Exception as e:
                raise RetrievalError(f"Failed to generate embedding: {e}") from e

            # Create document chunk
            doc_id = uuid4()
            doc_ids.append(doc_id)

            chunk = DocumentChunk(
                document_id=doc_id,
                content=chunk_desc,
                embedding=embedding,
                metadata=Metadata(
                    source=source,
                    title=f"{Path(source).name} (rows {start_idx}-{end_idx - 1})",
                    custom={
                        "modality": "structured",
                        "format": "table",
                        "row_start": start_idx,
                        "row_end": end_idx - 1,
                        "total_rows": len(df),
                        "columns": list(df.columns),
                        "schema": schema.columns,
                    },
                ),
                index=len(chunks),
            )
            chunks.append(chunk)

        # Add to vector store
        try:
            await self._vector_store.add_chunks(chunks)
            self._document_count += len(chunks)
            logger.info(f"Indexed {len(chunks)} chunks from {source}")
        except Exception as e:
            raise RetrievalError(f"Failed to add chunks to vector store: {e}") from e

        return doc_ids

    async def semantic_search(
        self,
        query: str,
        top_k: int = 10,
        threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search structured data using natural language.

        Args:
            query: Natural language query
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            filters: Optional metadata filters

        Returns:
            List of search results

        Raises:
            RetrievalError: If search fails
        """
        self._ensure_initialized()

        # Generate query embedding
        try:
            query_embedding = await self._embedding_provider.embed_query(query)
        except Exception as e:
            raise RetrievalError(f"Failed to embed query: {e}") from e

        # Search vector store
        options = SearchOptions(
            top_k=top_k,
            threshold=threshold,
            filters=filters,
            include_metadata=True,
        )

        try:
            results = await self._vector_store.search(query_embedding, options)
        except Exception as e:
            raise RetrievalError(f"Vector store search failed: {e}") from e

        logger.debug(f"Semantic search returned {len(results)} results")
        return results

    async def structured_query(
        self,
        query: StructuredQuery,
        source: Optional[str] = None,
    ) -> List[SearchResult]:
        """Execute structured query with filters.

        Note: This is a simplified implementation that uses metadata filtering
        on the vector store. Full structured query support would require
        integration with a SQL engine or document store.

        Args:
            query: Structured query specification
            source: Optional source to filter by

        Returns:
            List of matching results

        Raises:
            RetrievalError: If query fails
        """
        self._ensure_initialized()

        # Build metadata filters from query
        filters = {}

        if source:
            filters["source"] = source

        # Add structured filters as custom metadata filters
        # Note: This assumes filters are stored in metadata
        for col, value in query.filters.items():
            filters[f"custom.{col}"] = value

        # Search with filters (empty query to get all matching)
        # Use zero vector or retrieve all and filter
        try:
            # Get all documents matching filters
            options = SearchOptions(
                top_k=query.limit or 1000,
                filters=filters if filters else None,
                include_metadata=True,
            )
            # Use a dummy embedding (will match all roughly equally)
            dummy_embedding = [0.0] * self.config.dimensions
            results = await self._vector_store.search(dummy_embedding, options)

            # Apply sorting if specified
            if query.sort_by and results:
                reverse = query.sort_order == "desc"
                results.sort(
                    key=lambda r: r.metadata.custom.get(query.sort_by, "") if r.metadata else "",
                    reverse=reverse,
                )

            # Apply limit
            if query.limit:
                results = results[: query.limit]

        except Exception as e:
            raise RetrievalError(f"Structured query failed: {e}") from e

        logger.debug(f"Structured query returned {len(results)} results")
        return results

    async def hybrid_search(
        self,
        query_text: str,
        structured_query: Optional[StructuredQuery] = None,
        top_k: int = 10,
        threshold: float = 0.0,
    ) -> List[SearchResult]:
        """Combine semantic and structured search.

        Args:
            query_text: Natural language query
            structured_query: Optional structured filters
            top_k: Number of results to return
            threshold: Minimum similarity threshold

        Returns:
            List of search results
        """
        self._ensure_initialized()

        # If no structured query, fall back to semantic
        if not structured_query or not structured_query.filters:
            return await self.semantic_search(query_text, top_k, threshold)

        # Build filters from structured query
        filters = {}
        for col, value in structured_query.filters.items():
            filters[f"custom.{col}"] = value

        # Perform semantic search with filters
        return await self.semantic_search(query_text, top_k, threshold, filters)

    async def get_schema(self, source: str) -> Optional[TableSchema]:
        """Get schema for a data source.

        Args:
            source: Source identifier

        Returns:
            Table schema if available
        """
        return self._schemas.get(source)

    async def list_sources(self) -> List[str]:
        """List all indexed data sources.

        Returns:
            List of source identifiers
        """
        return list(self._schemas.keys())

    async def delete_source(self, source: str) -> None:
        """Delete all chunks from a source.

        Args:
            source: Source identifier

        Raises:
            RetrievalError: If deletion fails
        """
        self._ensure_initialized()

        # Note: This would require vector store to support deletion by filter
        # For now, we just remove from schema tracking
        if source in self._schemas:
            del self._schemas[source]
            logger.info(f"Removed schema for source: {source}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "initialized": self._initialized,
            "document_count": self._document_count,
            "collection_name": self.config.collection_name,
            "sources": list(self._schemas.keys()),
            "total_rows": sum(s.row_count for s in self._schemas.values()),
        }

    def _ensure_initialized(self) -> None:
        """Ensure retriever is initialized.

        Raises:
            RetrievalError: If not initialized
        """
        if not self._initialized:
            raise RetrievalError("Structured retriever not initialized. Call initialize() first.")

    async def health_check(self) -> bool:
        """Check if retriever is healthy.

        Returns:
            True if healthy
        """
        if not self._initialized:
            return False

        try:
            if hasattr(self._embedding_provider, "health_check"):
                provider_healthy = await self._embedding_provider.health_check()
                if not provider_healthy:
                    return False
            return True
        except Exception:
            return False
