"""
RAG Engine - Vector Database and Retrieval Logic.

Demonstrates:
- ChromaDB integration
- Semantic search implementation
- Document management
"""

import os
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.core.embeddings import EmbeddingModel
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

try:
    import chromadb
    from chromadb.config import Settings

    CHROMA_AVAILABLE = True
except (ImportError, Exception) as e:
    logger.warning(f"ChromaDB not available: {e}. Using dummy vector store.")
    CHROMA_AVAILABLE = False
    chromadb = None


@dataclass
class SearchResult:
    """Standardized search result."""

    text: str
    source: str
    id: str
    distance: float
    metadata: Dict[str, Any]


class VectorStore:
    """
    Wrapper around ChromaDB for document storage and retrieval.
    """

    def __init__(
        self,
        collection_name: str = "agentforge_docs",
        embedding_model: Optional[EmbeddingModel] = None,
        persist_directory: str = "./.chroma_db",
    ):
        """
        Initialize the Vector Store.

        Args:
            collection_name: Name of the Chroma collection
            embedding_model: Instance of EmbeddingModel class
            persist_directory: Path to save the database
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.embedding_model = embedding_model or EmbeddingModel()

        if CHROMA_AVAILABLE:
            # Initialize Client
            try:
                self._client = chromadb.PersistentClient(path=persist_directory)

                # Get or Create Collection
                # Note: Chroma handles the embedding function adapter, but we'll manage embeddings explicitly
                # to simplify swapping providers in our clean architecture.
                self._collection = self._client.get_or_create_collection(
                    name=collection_name, metadata={"hnsw:space": "cosine"}
                )
                logger.info(f"VectorStore initialized at {persist_directory}, Collection: {collection_name}")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB client: {e}")
                self._client = None
                self._collection = None
        else:
            self._client = None
            self._collection = None
            logger.warning("VectorStore initialized in DUMMY mode (ChromaDB unavailable)")

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        location_id: Optional[str] = None,
    ) -> List[str]:
        """
        Add texts to the vector store.
        """
        if not self._collection:
            logger.warning("VectorStore: add_texts called but no collection available.")
            return []

        if not ids:
            ids = [str(uuid.uuid4()) for _ in texts]

        if not metadatas:
            metadatas = [{"source": "unknown"} for _ in texts]

        # Add location_id to all metadatas
        loc = location_id or "global"
        for meta in metadatas:
            meta["location_id"] = loc

        try:
            # Generate embeddings
            embeddings = self.embedding_model.embed_documents(texts)

            # Add to Chroma
            self._collection.add(documents=texts, embeddings=embeddings, metadatas=metadatas, ids=ids)
            logger.info(f"Added {len(texts)} documents to vector store (location: {location_id or 'global'})")
            return ids
        except Exception as e:
            logger.error(f"Error adding texts to vector store: {e}")
            raise

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        location_id: Optional[str] = None,
    ) -> List[str]:
        """Alias for add_texts."""
        return self.add_texts(documents, metadatas, ids, location_id=location_id)

    def search(
        self,
        query: str,
        n_results: int = 4,
        location_id: Optional[str] = None,
        neighborhood: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
        mode: str = "semantic",  # semantic, keyword, hybrid
    ) -> List[SearchResult]:
        """
        Search for relevant documents.
        Supports 'semantic' (default), 'keyword' (exact match boost), or 'hybrid'.

        Args:
            query: The search query
            n_results: Number of results to return
            location_id: Scope results to this location
            neighborhood: Bias results toward this neighborhood (Neighborhood Persona)
            filter_metadata: Additional metadata filters
            mode: Search mode
        """
        if not self._collection:
            return []

        try:
            # Build filter metadata
            where_filter = {}

            # If location_id is provided, we want documents for this location OR global documents
            loc_filter = {"location_id": {"$in": [location_id or "global", "global"]}}

            filters = [loc_filter]

            if neighborhood:
                # If neighborhood is provided, we can either filter strictly or bias
                # For "Neighborhood Persona", we'll try to find neighborhood-specific docs
                neighborhood_filter = {"neighborhood": {"$in": [neighborhood, "all"]}}
                filters.append(neighborhood_filter)

            if filter_metadata:
                filters.append(filter_metadata)

            if len(filters) > 1:
                where_filter = {"$and": filters}
            else:
                where_filter = filters[0]

            # 1. Semantic Search (Base)
            query_embedding = self.embedding_model.embed_query(query)

            # Biasing: If neighborhood is specified, boost the query with neighborhood name
            biased_query = f"{neighborhood} {query}" if neighborhood else query
            biased_embedding = self.embedding_model.embed_query(biased_query) if neighborhood else query_embedding

            results = self._collection.query(
                query_embeddings=[biased_embedding],
                n_results=n_results * 2 if mode == "hybrid" else n_results,
                where=where_filter if where_filter else None,
            )

            candidates = {}
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    doc_id = results["ids"][0][i]
                    candidates[doc_id] = SearchResult(
                        id=doc_id,
                        text=results["documents"][0][i],
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                        source=results["metadatas"][0][i].get("source", "unknown")
                        if results["metadatas"]
                        else "unknown",
                        distance=results["distances"][0][i] if results["distances"] else 0.0,
                    )

            if mode in ["keyword", "hybrid"]:
                # 2. Simple Keyword Scoring (Reranking)
                # In a real system, we'd query an Inverted Index. here we scan candidates.
                # Just rerank the semantic candidates based on keyword overlap
                query_terms = set(query.lower().split())

                for doc_id, res in candidates.items():
                    doc_lower = res.text.lower()
                    score = sum(1 for term in query_terms if term in doc_lower)
                    # Normalize simple score
                    keyword_boost = score * 0.1
                    # Reduce distance (which is bad in cosine distance, usually smaller is better?
                    # Chroma returns distance. If cosine DISTANCE, 0 is identical.
                    # We want to reduce distance if keywords match.
                    res.distance = max(0.0, res.distance - keyword_boost)

            # Sort and Slice
            final_results = list(candidates.values())
            final_results.sort(key=lambda x: x.distance)

            return final_results[:n_results]

        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []

    async def search_corrective(
        self,
        query: str,
        n_results: int = 4,
        location_id: Optional[str] = None,
        neighborhood: Optional[str] = None,
        threshold: float = 0.6,
    ) -> List[SearchResult]:
        """
        Corrective RAG (CRAG) Implementation.

        Evaluates retrieval quality and triggers web search fallback if relevance is low.
        """
        # 1. Standard semantic search
        results = self.search(query=query, n_results=n_results, location_id=location_id, neighborhood=neighborhood)

        # 2. Evaluate relevance
        # Chroma cosine distance: 0 is identical, > 0.6 is generally low relevance
        is_relevant = False
        if results and results[0].distance < threshold:
            is_relevant = True

        if is_relevant:
            logger.info(f"CRAG: Local results relevant (best distance: {results[0].distance:.4f})")
            return results

        # 3. Web Search Fallback (Low relevance or no results)
        logger.warning(
            f"CRAG: Low relevance detected (distance: {results[0].distance if results else 'N/A'}). Triggering Web Search."
        )

        try:
            from ghl_real_estate_ai.services.perplexity_researcher import get_perplexity_researcher

            researcher = get_perplexity_researcher()

            research_query = query
            if neighborhood or location_id:
                research_query += f" specifically for {neighborhood or ''} {location_id or ''}"

            web_content = await researcher.research_topic(
                topic=research_query, context="Provide specific real-time data for real estate decisions."
            )

            # 4. Ingest new data for future use (Self-Correction Loop)
            new_doc_id = f"crag_{uuid.uuid4().hex[:8]}"
            self.add_texts(
                texts=[web_content],
                metadatas=[
                    {
                        "source": "perplexity_web_search",
                        "query": query,
                        "category": "market_data",
                        "retrieved_at": datetime.now().isoformat(),
                    }
                ],
                ids=[new_doc_id],
                location_id=location_id,
            )

            # 5. Return web result as a SearchResult
            web_result = SearchResult(
                id=new_doc_id,
                text=web_content,
                metadata={"source": "perplexity", "category": "market_data"},
                source="perplexity",
                distance=0.1,  # Artificially high relevance for fresh web data
            )

            return [web_result] + results[: n_results - 1]

        except Exception as e:
            logger.error(f"CRAG: Web search fallback failed: {e}")
            return results

    def clear(self) -> None:
        """Clear all documents from the collection."""
        if not self._client:
            return

        try:
            self._client.delete_collection(self.collection_name)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name, metadata={"hnsw:space": "cosine"}
            )
            logger.info("Vector store cleared")
        except Exception as e:
            logger.error(f"Error clearing vector store: {e}")

    def ingest_neighborhood_data(
        self,
        neighborhood: str,
        data_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        location_id: Optional[str] = None,
    ) -> str:
        """
        Ingest hyper-local neighborhood data (zoning, schools, stats).

        Args:
            neighborhood: Name of the neighborhood
            data_type: Type of data (e.g., 'zoning', 'schools', 'market_stats')
            content: Text content to ingest
            metadata: Additional metadata
            location_id: Scope to this location

        Returns:
            ID of the ingested document
        """
        doc_id = f"local_{neighborhood}_{data_type}_{uuid.uuid4().hex[:8]}"

        final_metadata = {
            "neighborhood": neighborhood,
            "data_type": data_type,
            "source": f"local_{data_type}",
            "ingested_at": datetime.now().isoformat(),
        }
        if metadata:
            final_metadata.update(metadata)

        self.add_texts(texts=[content], metadatas=[final_metadata], ids=[doc_id], location_id=location_id)

        logger.info(f"Ingested {data_type} data for neighborhood: {neighborhood}")
        return doc_id


# Alias for backward compatibility and internal consistency
RAGEngine = VectorStore
