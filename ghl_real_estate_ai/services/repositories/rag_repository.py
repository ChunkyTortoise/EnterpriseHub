"""
RAG (Retrieval Augmented Generation) Property Repository Implementation

Handles property data using semantic search and vector embeddings.
Provides AI-powered property matching based on natural language queries.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path

try:
    # Optional dependencies for embeddings
    import openai
    from sentence_transformers import SentenceTransformer
    import faiss
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False

from .interfaces import (
    IPropertyRepository, PropertyQuery, RepositoryResult, RepositoryMetadata,
    RepositoryError, QueryOperator, SortOrder
)


class RAGPropertyRepository(IPropertyRepository):
    """
    Repository implementation using RAG (Retrieval Augmented Generation).

    Features:
    - Semantic search with natural language queries
    - Vector embeddings for property descriptions
    - Similarity-based ranking
    - Fallback to traditional filtering
    - Multiple embedding model support
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize RAG repository.

        Config options:
        - embedding_model: Model for generating embeddings
        - vector_index_path: Path to store/load vector index
        - openai_api_key: OpenAI API key for embeddings
        - similarity_threshold: Minimum similarity score
        - max_semantic_results: Maximum results from semantic search
        - fallback_to_traditional: Use traditional search as fallback
        """
        super().__init__("rag_repository", config)

        if not HAS_EMBEDDINGS:
            raise RepositoryError(
                "RAG repository requires optional dependencies: sentence-transformers, faiss-cpu, openai",
                repository_type="rag"
            )

        # Configuration
        self.embedding_model_name = config.get("embedding_model", "all-MiniLM-L6-v2")
        self.vector_index_path = config.get("vector_index_path", "./data/embeddings/")
        self.openai_api_key = config.get("openai_api_key")
        self.similarity_threshold = config.get("similarity_threshold", 0.6)
        self.max_semantic_results = config.get("max_semantic_results", 100)
        self.fallback_to_traditional = config.get("fallback_to_traditional", True)

        # Data source configuration
        self.data_paths = config.get("data_paths", [])
        self.index_refresh_interval = config.get("index_refresh_interval", 3600)  # 1 hour

        # Internal state
        self.embedding_model: Optional[SentenceTransformer] = None
        self.vector_index: Optional[Any] = None  # FAISS index
        self.property_documents: List[Dict[str, Any]] = []
        self.document_embeddings: Optional[np.ndarray] = None
        self._last_indexed: Optional[datetime] = None
        self._index_lock = asyncio.Lock()

    async def connect(self) -> bool:
        """Initialize embedding model and vector index"""
        try:
            # Initialize embedding model
            if self.openai_api_key:
                openai.api_key = self.openai_api_key
                self.use_openai_embeddings = True
            else:
                self.embedding_model = SentenceTransformer(self.embedding_model_name)
                self.use_openai_embeddings = False

            # Load or create vector index
            await self._load_or_create_index()

            self._is_connected = True
            return True

        except Exception as e:
            raise RepositoryError(
                f"Failed to connect to RAG repository: {e}",
                repository_type="rag",
                original_error=e
            )

    async def disconnect(self):
        """Clean up resources"""
        if self.vector_index:
            # Save index if needed
            await self._save_index()

        self.embedding_model = None
        self.vector_index = None
        self.property_documents.clear()
        self.document_embeddings = None
        self._is_connected = False

    async def health_check(self) -> Dict[str, Any]:
        """Check RAG repository health"""
        health = {
            "status": "healthy",
            "embedding_model": self.embedding_model_name,
            "use_openai": self.use_openai_embeddings,
            "indexed_properties": len(self.property_documents),
            "vector_dimension": self.document_embeddings.shape[1] if self.document_embeddings is not None else 0,
            "last_indexed": self._last_indexed.isoformat() if self._last_indexed else None,
            "issues": []
        }

        # Check embedding model
        if not self.embedding_model and not self.use_openai_embeddings:
            health["issues"].append("No embedding model available")
            health["status"] = "unhealthy"

        # Check vector index
        if not self.vector_index:
            health["issues"].append("Vector index not initialized")
            health["status"] = "degraded"

        # Check data freshness
        if self._should_refresh_index():
            health["issues"].append("Vector index may be stale")
            if health["status"] == "healthy":
                health["status"] = "warning"

        return health

    async def find_properties(self, query: PropertyQuery) -> RepositoryResult:
        """Find properties using semantic search and traditional filters"""
        start_time = datetime.now()

        try:
            # Ensure index is ready
            if self._should_refresh_index():
                await self._refresh_index()

            results = []
            total_count = 0

            # Semantic search if query text provided
            if query.semantic_query:
                semantic_results = await self._semantic_search(query.semantic_query, query)
                results.extend(semantic_results)

            # Traditional filtering for remaining criteria
            if self.fallback_to_traditional or not query.semantic_query:
                traditional_results = await self._traditional_search(query)

                # Merge results, avoiding duplicates
                existing_ids = {prop.get("id") for prop in results}
                for prop in traditional_results:
                    if prop.get("id") not in existing_ids:
                        results.append(prop)

            # Apply final sorting and pagination
            sorted_results = await self._sort_results(results, query)
            paginated_results, total_count = await self._paginate_results(sorted_results, query)

            # Create metadata
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            metadata = RepositoryMetadata(
                source=self.name,
                query_time_ms=execution_time,
                cache_hit=False,  # RAG is always computed
                total_scanned=len(self.property_documents)
            )

            return RepositoryResult(
                data=paginated_results,
                total_count=total_count,
                pagination=query.pagination,
                metadata=metadata,
                execution_time_ms=execution_time
            )

        except Exception as e:
            return RepositoryResult(
                success=False,
                errors=[f"RAG search failed: {str(e)}"]
            )

    async def get_property_by_id(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get property by ID"""
        for prop in self.property_documents:
            if str(prop.get("id")) == str(property_id):
                return prop
        return None

    async def count_properties(self, query: PropertyQuery) -> int:
        """Count properties matching query"""
        result = await self.find_properties(query)
        return result.total_count if result.success else 0

    def get_supported_filters(self) -> List[str]:
        """Get supported filter fields"""
        return [
            "id", "address", "price", "bedrooms", "bathrooms", "sqft",
            "property_type", "neighborhood", "amenities", "description",
            "semantic_query"
        ]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get RAG repository performance metrics"""
        return {
            "repository_type": "rag",
            "embedding_model": self.embedding_model_name,
            "use_openai_embeddings": self.use_openai_embeddings,
            "indexed_properties": len(self.property_documents),
            "vector_dimension": self.document_embeddings.shape[1] if self.document_embeddings is not None else 0,
            "last_indexed": self._last_indexed.isoformat() if self._last_indexed else None,
            "similarity_threshold": self.similarity_threshold
        }

    # Private methods
    async def _load_or_create_index(self):
        """Load existing index or create new one"""
        async with self._index_lock:
            index_path = Path(self.vector_index_path)

            # Try to load existing index
            if await self._load_existing_index(index_path):
                return

            # Create new index from data
            await self._create_new_index()

    async def _load_existing_index(self, index_path: Path) -> bool:
        """Load existing vector index from disk"""
        try:
            if not index_path.exists():
                return False

            # Load FAISS index
            import faiss
            faiss_path = index_path / "properties.faiss"
            if faiss_path.exists():
                self.vector_index = faiss.read_index(str(faiss_path))

            # Load property documents
            docs_path = index_path / "documents.json"
            if docs_path.exists():
                with open(docs_path, 'r') as f:
                    self.property_documents = json.load(f)

            # Load embeddings
            embeddings_path = index_path / "embeddings.npy"
            if embeddings_path.exists():
                self.document_embeddings = np.load(str(embeddings_path))

            # Load metadata
            meta_path = index_path / "metadata.json"
            if meta_path.exists():
                with open(meta_path, 'r') as f:
                    metadata = json.load(f)
                    self._last_indexed = datetime.fromisoformat(metadata["last_indexed"])

            return (self.vector_index is not None and
                   self.property_documents and
                   self.document_embeddings is not None)

        except Exception as e:
            print(f"Failed to load existing index: {e}")
            return False

    async def _create_new_index(self):
        """Create new vector index from property data"""
        # Load property data from configured sources
        await self._load_property_data()

        if not self.property_documents:
            raise RepositoryError("No property data available for indexing")

        # Generate embeddings for properties
        document_texts = [self._create_property_document(prop) for prop in self.property_documents]
        embeddings = await self._generate_embeddings(document_texts)

        # Create FAISS index
        import faiss
        dimension = embeddings.shape[1]
        self.vector_index = faiss.IndexFlatIP(dimension)  # Inner product (cosine similarity)

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        self.vector_index.add(embeddings)

        self.document_embeddings = embeddings
        self._last_indexed = datetime.now()

        # Save index to disk
        await self._save_index()

    async def _load_property_data(self):
        """Load property data from configured sources"""
        self.property_documents = []

        for data_path in self.data_paths:
            try:
                path_obj = Path(data_path)
                if not path_obj.exists():
                    continue

                with open(path_obj, 'r') as f:
                    data = json.load(f)

                # Extract properties from various JSON structures
                if isinstance(data, list):
                    properties = data
                elif isinstance(data, dict):
                    # Check common keys
                    properties = data.get("properties", data.get("listings", data.get("data", [])))
                    if not properties and any(k in data for k in ["id", "address", "price"]):
                        properties = [data]
                else:
                    properties = []

                # Add source metadata
                for prop in properties:
                    if isinstance(prop, dict):
                        prop["_source"] = data_path
                        self.property_documents.append(prop)

            except Exception as e:
                print(f"Failed to load data from {data_path}: {e}")

    def _create_property_document(self, property_data: Dict[str, Any]) -> str:
        """Create searchable text document from property data"""
        doc_parts = []

        # Basic information
        address = property_data.get("address", "")
        if address:
            doc_parts.append(f"Address: {address}")

        price = property_data.get("price")
        if price:
            doc_parts.append(f"Price: ${price:,}")

        # Property details
        bedrooms = property_data.get("bedrooms")
        if bedrooms:
            doc_parts.append(f"Bedrooms: {bedrooms}")

        bathrooms = property_data.get("bathrooms")
        if bathrooms:
            doc_parts.append(f"Bathrooms: {bathrooms}")

        sqft = property_data.get("sqft") or property_data.get("square_feet")
        if sqft:
            doc_parts.append(f"Square feet: {sqft}")

        property_type = property_data.get("property_type")
        if property_type:
            doc_parts.append(f"Type: {property_type}")

        # Location
        neighborhood = property_data.get("neighborhood")
        if neighborhood:
            doc_parts.append(f"Neighborhood: {neighborhood}")

        city = property_data.get("city")
        if city:
            doc_parts.append(f"City: {city}")

        # Amenities
        amenities = property_data.get("amenities", [])
        if amenities:
            if isinstance(amenities, str):
                amenities_text = amenities
            else:
                amenities_text = ", ".join(str(a) for a in amenities)
            doc_parts.append(f"Amenities: {amenities_text}")

        # Description (if available)
        description = property_data.get("description")
        if description:
            doc_parts.append(f"Description: {description}")

        # Additional features
        year_built = property_data.get("year_built")
        if year_built:
            doc_parts.append(f"Year built: {year_built}")

        return ". ".join(doc_parts)

    async def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for text documents"""
        if self.use_openai_embeddings:
            return await self._generate_openai_embeddings(texts)
        else:
            return await self._generate_local_embeddings(texts)

    async def _generate_openai_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using OpenAI API"""
        embeddings = []

        # Process in batches to avoid rate limits
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                response = await openai.Embedding.acreate(
                    model="text-embedding-ada-002",
                    input=batch
                )

                batch_embeddings = [item["embedding"] for item in response["data"]]
                embeddings.extend(batch_embeddings)

                # Rate limiting
                await asyncio.sleep(0.1)

            except Exception as e:
                raise RepositoryError(f"OpenAI embedding generation failed: {e}")

        return np.array(embeddings, dtype=np.float32)

    async def _generate_local_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using local model"""
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None, self.embedding_model.encode, texts
        )
        return embeddings.astype(np.float32)

    async def _semantic_search(self, query_text: str, query: PropertyQuery) -> List[Dict[str, Any]]:
        """Perform semantic search using vector similarity"""
        if not self.vector_index or not self.document_embeddings.size:
            return []

        # Generate query embedding
        query_embedding = await self._generate_embeddings([query_text])

        # Normalize for cosine similarity
        import faiss
        faiss.normalize_L2(query_embedding)

        # Search vector index
        k = min(self.max_semantic_results, len(self.property_documents))
        scores, indices = self.vector_index.search(query_embedding, k)

        # Filter by similarity threshold
        results = []
        threshold = query.similarity_threshold or self.similarity_threshold

        for score, idx in zip(scores[0], indices[0]):
            if score >= threshold and idx < len(self.property_documents):
                prop = self.property_documents[idx].copy()
                prop["_similarity_score"] = float(score)
                prop["_search_type"] = "semantic"
                results.append(prop)

        return results

    async def _traditional_search(self, query: PropertyQuery) -> List[Dict[str, Any]]:
        """Perform traditional filtering on properties"""
        filtered = self.property_documents.copy()

        # Apply traditional filters
        if query.min_price is not None:
            filtered = [p for p in filtered if p.get("price", 0) >= query.min_price]

        if query.max_price is not None:
            filtered = [p for p in filtered if p.get("price", 0) <= query.max_price]

        if query.min_bedrooms is not None:
            filtered = [p for p in filtered if p.get("bedrooms", 0) >= query.min_bedrooms]

        if query.property_types:
            filtered = [p for p in filtered if p.get("property_type", "").lower() in
                       [pt.lower() for pt in query.property_types]]

        # Add traditional search metadata
        for prop in filtered:
            if "_search_type" not in prop:
                prop["_search_type"] = "traditional"

        return filtered

    async def _sort_results(self, results: List[Dict[str, Any]], query: PropertyQuery) -> List[Dict[str, Any]]:
        """Sort results with semantic score priority"""
        def sort_key(prop: Dict[str, Any]):
            # Prioritize semantic results by similarity score
            if "_similarity_score" in prop:
                return (-prop["_similarity_score"], 0)  # Negative for descending

            # Traditional sorting for non-semantic results
            if query.sort_by == "price":
                value = prop.get("price", 0)
            elif query.sort_by == "bedrooms":
                value = prop.get("bedrooms", 0)
            else:
                value = 0

            return (0, value if query.sort_order == SortOrder.ASC else -value)

        return sorted(results, key=sort_key)

    async def _paginate_results(self, results: List[Dict[str, Any]], query: PropertyQuery) -> tuple:
        """Apply pagination to results"""
        total_count = len(results)
        query.pagination.total_count = total_count

        start = query.pagination.offset
        end = start + query.pagination.limit
        paginated = results[start:end]

        return paginated, total_count

    def _should_refresh_index(self) -> bool:
        """Check if index should be refreshed"""
        if not self._last_indexed:
            return True

        age = datetime.now() - self._last_indexed
        return age.total_seconds() > self.index_refresh_interval

    async def _refresh_index(self):
        """Refresh the vector index with latest data"""
        await self._create_new_index()

    async def _save_index(self):
        """Save vector index and metadata to disk"""
        try:
            index_path = Path(self.vector_index_path)
            index_path.mkdir(parents=True, exist_ok=True)

            # Save FAISS index
            if self.vector_index:
                import faiss
                faiss.write_index(self.vector_index, str(index_path / "properties.faiss"))

            # Save property documents
            if self.property_documents:
                with open(index_path / "documents.json", 'w') as f:
                    json.dump(self.property_documents, f, default=str)

            # Save embeddings
            if self.document_embeddings is not None:
                np.save(str(index_path / "embeddings.npy"), self.document_embeddings)

            # Save metadata
            metadata = {
                "last_indexed": self._last_indexed.isoformat() if self._last_indexed else None,
                "property_count": len(self.property_documents),
                "embedding_model": self.embedding_model_name
            }
            with open(index_path / "metadata.json", 'w') as f:
                json.dump(metadata, f)

        except Exception as e:
            print(f"Failed to save index: {e}")