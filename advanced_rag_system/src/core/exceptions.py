"""Custom exceptions for Advanced RAG System.

This module defines the exception hierarchy used throughout the system
for consistent error handling and reporting.
"""

from typing import Any, Dict, Optional


class RAGException(Exception):
    """Base exception for all RAG system errors.

    Attributes:
        message: Error message
        details: Additional error details
        error_code: Machine-readable error code
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: str = "RAG_ERROR",
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message
            details: Additional context about the error
            error_code: Machine-readable error identifier
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.error_code = error_code

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization.

        Returns:
            Dictionary representation of the error
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        """String representation of the exception."""
        if self.details:
            return f"[{self.error_code}] {self.message} - Details: {self.details}"
        return f"[{self.error_code}] {self.message}"


class ConfigurationError(RAGException):
    """Exception raised for configuration-related errors.

    This includes missing environment variables, invalid settings,
    or configuration file errors.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize configuration error."""
        super().__init__(
            message=message,
            details=details,
            error_code="CONFIG_ERROR",
        )


class ValidationError(RAGException):
    """Exception raised for data validation errors.

    This includes invalid document formats, malformed queries,
    or schema violations.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize validation error."""
        super().__init__(
            message=message,
            details=details,
            error_code="VALIDATION_ERROR",
        )


class EmbeddingError(RAGException):
    """Exception raised for embedding generation errors.

    This includes API failures, model errors, or embedding
    dimension mismatches.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        provider: Optional[str] = None,
        error_code: str = "EMBEDDING_ERROR",
    ) -> None:
        """Initialize embedding error.

        Args:
            message: Error message
            details: Additional details
            provider: Name of the embedding provider that failed
            error_code: Optional custom error code
        """
        super().__init__(
            message=message,
            details=details,
            error_code=error_code,
        )
        self.provider = provider


class VectorStoreError(RAGException):
    """Exception raised for vector store operations.

    This includes connection errors, query failures, or
    collection management errors.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        store_type: Optional[str] = None,
        error_code: str = "VECTOR_STORE_ERROR",
    ) -> None:
        """Initialize vector store error.

        Args:
            message: Error message
            details: Additional details
            store_type: Type of vector store (e.g., 'chroma', 'pinecone')
            error_code: Optional custom error code
        """
        super().__init__(
            message=message,
            details=details,
            error_code=error_code,
        )
        self.store_type = store_type


class CacheError(RAGException):
    """Exception raised for caching operations.

    This includes Redis connection errors, serialization failures,
    or cache invalidation errors.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        cache_layer: Optional[str] = None,
    ) -> None:
        """Initialize cache error.

        Args:
            message: Error message
            details: Additional details
            cache_layer: Cache layer identifier (e.g., 'L1', 'L2', 'redis')
        """
        super().__init__(
            message=message,
            details=details,
            error_code="CACHE_ERROR",
        )
        self.cache_layer = cache_layer


class RetrievalError(RAGException):
    """Exception raised for retrieval operations.

    This includes search failures, re-ranking errors, or
    fusion algorithm failures.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize retrieval error."""
        super().__init__(
            message=message,
            details=details,
            error_code="RETRIEVAL_ERROR",
        )


class GenerationError(RAGException):
    """Exception raised for text generation operations.

    This includes LLM API failures, prompt errors, or
    response parsing failures.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize generation error."""
        super().__init__(
            message=message,
            details=details,
            error_code="GENERATION_ERROR",
        )


class RateLimitError(RAGException):
    """Exception raised when rate limits are exceeded.

    This includes API rate limits, quota exceeded errors,
    or throttling responses.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None,
    ) -> None:
        """Initialize rate limit error.

        Args:
            message: Error message
            details: Additional details
            retry_after: Seconds to wait before retry
        """
        super().__init__(
            message=message,
            details=details,
            error_code="RATE_LIMIT_ERROR",
        )
        self.retry_after = retry_after


class NotFoundError(RAGException):
    """Exception raised when a requested resource is not found.

    This includes missing documents, collections, or queries.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ) -> None:
        """Initialize not found error.

        Args:
            message: Error message
            details: Additional details
            resource_type: Type of resource not found
            resource_id: Identifier of the missing resource
        """
        super().__init__(
            message=message,
            details=details,
            error_code="NOT_FOUND",
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class DuplicateError(RAGException):
    """Exception raised when attempting to create a duplicate resource.

    This includes duplicate documents, collections, or IDs.
    """

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
    ) -> None:
        """Initialize duplicate error.

        Args:
            message: Error message
            details: Additional details
            resource_type: Type of duplicate resource
            resource_id: Identifier of the duplicate resource
        """
        super().__init__(
            message=message,
            details=details,
            error_code="DUPLICATE_ERROR",
        )
        self.resource_type = resource_type
        self.resource_id = resource_id