"""Structured data module for Advanced RAG System.

Provides capabilities for loading, querying, and searching structured data
including CSV, Excel, and JSON tables with SQL-like query support.
"""

from src.structured_data.hybrid_searcher import StructuredHybridSearcher
from src.structured_data.sql_engine import QueryResult, SQLQueryEngine
from src.structured_data.table_loader import TableLoader, TableLoadOptions

__all__ = [
    "TableLoader",
    "TableLoadOptions",
    "SQLQueryEngine",
    "QueryResult",
    "StructuredHybridSearcher",
]
