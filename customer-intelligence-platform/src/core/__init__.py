"""Core modules for Customer Intelligence Platform."""
from .knowledge_engine import KnowledgeEngine, SearchResult
from .embeddings import EmbeddingModel
from .ai_client import AIClient, LLMResponse, LLMProvider, get_ai_client
from .conversation_manager import ConversationManager, AIResponse

__all__ = [
    "KnowledgeEngine", "SearchResult", "EmbeddingModel",
    "AIClient", "LLMResponse", "LLMProvider", "get_ai_client",
    "ConversationManager", "AIResponse"
]