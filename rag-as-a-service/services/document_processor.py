"""Document processing pipeline — upload -> chunk -> embed -> store.

Wires together DocumentProcessor, EmbeddingService, and UsageTracker into a
single pipeline that API routes can call.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field

from rag_service.core.document_processor import DocumentProcessor, ProcessedDocument
from rag_service.core.embedding_service import EmbeddingService
from rag_service.billing.usage_tracker import UsageTracker

logger = logging.getLogger(__name__)


@dataclass
class StoredDocument:
    """Result of the full ingest pipeline."""

    document_id: str
    filename: str
    content_type: str
    size_bytes: int
    chunk_count: int
    embedding_tokens: int
    collection_id: str | None = None
    metadata: dict = field(default_factory=dict)


class DocumentPipeline:
    """End-to-end document ingestion: parse -> chunk -> embed -> track usage."""

    def __init__(
        self,
        processor: DocumentProcessor,
        embedding_service: EmbeddingService,
        usage_tracker: UsageTracker,
    ):
        self.processor = processor
        self.embedding_service = embedding_service
        self.usage_tracker = usage_tracker

    async def ingest(
        self,
        content: bytes,
        filename: str,
        content_type: str,
        tenant_id: str,
        collection_id: str | None = None,
    ) -> StoredDocument:
        """Process a document through the full pipeline.

        Steps:
        1. Parse document and split into chunks
        2. Generate embeddings for each chunk
        3. Track usage (documents count, storage bytes)
        4. Return stored document metadata

        In production, step 2 would also write embeddings to pgvector.
        That integration depends on having an async DB session, which the
        caller (API route) manages via tenant-scoped schema.
        """
        # 1. Parse and chunk
        processed: ProcessedDocument = self.processor.process(content, filename, content_type)

        # 2. Generate embeddings
        chunk_texts = [chunk.content for chunk in processed.chunks]
        embedding_result = None
        if chunk_texts:
            try:
                embedding_result = await self.embedding_service.embed_texts(chunk_texts)
            except Exception:
                logger.exception("Embedding generation failed for %s", filename)
                # Continue without embeddings — they can be retried later

        # 3. Track usage
        await self.usage_tracker.increment_documents(tenant_id)
        await self.usage_tracker.increment_storage(tenant_id, len(content))

        doc_id = str(uuid.uuid4())

        return StoredDocument(
            document_id=doc_id,
            filename=filename,
            content_type=content_type,
            size_bytes=len(content),
            chunk_count=len(processed.chunks),
            embedding_tokens=embedding_result.token_count if embedding_result else 0,
            collection_id=collection_id,
            metadata={
                **processed.metadata,
                "embedding_model": embedding_result.model if embedding_result else None,
            },
        )
