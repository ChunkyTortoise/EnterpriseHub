"""
Property Repository Pattern Implementation

Enterprise-grade Repository Pattern for flexible property data access.
Supports multiple data sources: JSON, MLS API, RAG/semantic search, databases.
"""

# Core interfaces
from .interfaces import (
    IPropertyRepository,
    IPropertyQueryBuilder,
    PropertyQuery,
    RepositoryResult,
    RepositoryError,
    QueryFilter,
    SortOrder,
    PaginationConfig
)

# Concrete repository implementations
from .json_repository import JsonPropertyRepository
from .mls_repository import MLSAPIRepository
from .rag_repository import RAGPropertyRepository
from .database_repository import DatabasePropertyRepository

# Query and caching layer
from .query_builder import PropertyQueryBuilder
from .caching_repository import CachingRepository
from .repository_factory import RepositoryFactory, create_repository

# Data service integration
from .property_data_service import PropertyDataService

__all__ = [
    # Core interfaces
    'IPropertyRepository',
    'IPropertyQueryBuilder',
    'PropertyQuery',
    'RepositoryResult',
    'RepositoryError',
    'QueryFilter',
    'SortOrder',
    'PaginationConfig',

    # Concrete repositories
    'JsonPropertyRepository',
    'MLSAPIRepository',
    'RAGPropertyRepository',
    'DatabasePropertyRepository',

    # Query and caching
    'PropertyQueryBuilder',
    'CachingRepository',
    'RepositoryFactory',
    'create_repository',

    # Integration
    'PropertyDataService'
]

# Version info
__version__ = "1.0.0"
__author__ = "GHL Real Estate AI Team"
__description__ = "Enterprise property data access with Repository Pattern"