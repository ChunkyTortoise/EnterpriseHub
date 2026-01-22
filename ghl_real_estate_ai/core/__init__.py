"""
Core modules for GHL Real Estate AI.

This module provides the foundational components including:
- ServiceRegistry: Unified access point for all backend services
- RAG Engine: Retrieval-augmented generation for AI responses
- LLM Client: Language model integration
- Embeddings: Vector embeddings for semantic search
"""

from .service_registry import ServiceRegistry
from .hooks import hooks, HookEvent, HookContext
from .gemini_logger import log_metrics

# Metrics Logger Hook
def metrics_logger_hook(ctx: HookContext):
    """Lifecycle hook to log LLM usage metrics."""
    if ctx.event == HookEvent.POST_GENERATION and ctx.output_data:
        resp = ctx.output_data
        # Ensure it's an LLMResponse object
        if hasattr(resp, 'provider') and hasattr(resp, 'model'):
            log_metrics(
                provider=resp.provider.value if hasattr(resp.provider, 'value') else str(resp.provider),
                model=resp.model,
                input_tokens=resp.input_tokens,
                output_tokens=resp.output_tokens,
                task_type=ctx.metadata.get("task_type", "general") if ctx.metadata else "general",
                tenant_id=ctx.metadata.get("tenant_id") if ctx.metadata else None
            )

# Register the metrics hook globally
hooks.register(HookEvent.POST_GENERATION, metrics_logger_hook)

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
