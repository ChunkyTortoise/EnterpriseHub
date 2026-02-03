"""SQL query engine for structured data.

This module provides SQL-like query capabilities on structured data using
DuckDB for efficient SQL execution on DataFrames.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

import pandas as pd

from src.core.exceptions import ValidationError
from src.core.types import DocumentChunk, Metadata, SearchResult


@dataclass
class QueryResult:
    """Result of a SQL query execution.

    Attributes:
        data: Query result as DataFrame
        row_count: Number of rows returned
        columns: List of column names
        execution_time_ms: Query execution time in milliseconds
        query: The executed SQL query
    """

    data: pd.DataFrame = field(default_factory=lambda: pd.DataFrame())
    row_count: int = 0
    columns: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0
    query: str = ""


class SQLQueryEngine:
    """SQL query engine for structured data.

    This class provides SQL-like query capabilities on pandas DataFrames
    using DuckDB for efficient query execution. It supports standard SQL
    operations including SELECT, WHERE, ORDER BY, GROUP BY, and aggregations.

    Features:
    - SQL queries on registered DataFrames
    - Semantic search on specific columns
    - Support for complex WHERE clauses
    - Aggregation functions (COUNT, AVG, SUM, etc.)
    - Result conversion to DocumentChunk objects

    Example:
        ```python
        engine = SQLQueryEngine()

        # Register a table
        engine.register_table("products", df)

        # Execute SQL query
        result = engine.execute_query(
            "SELECT * FROM products WHERE price > 100 ORDER BY price DESC LIMIT 10"
        )

        # Semantic search on columns
        results = engine.search_columns(
            "laptop computer",
            columns=["name", "description"],
            table_name="products"
        )
        ```
    """

    def __init__(self) -> None:
        """Initialize the SQL query engine."""
        self._tables: Dict[str, pd.DataFrame] = {}
        self._duckdb_available = self._check_duckdb()

    def _check_duckdb(self) -> bool:
        """Check if DuckDB is available.

        Returns:
            True if DuckDB is installed
        """
        try:
            import duckdb
            return True
        except ImportError:
            return False

    def register_table(
        self,
        name: str,
        dataframe: pd.DataFrame,
    ) -> None:
        """Register a DataFrame as a queryable table.

        Args:
            name: Table name for SQL queries
            dataframe: DataFrame to register

        Raises:
            ValidationError: If table name is invalid
        """
        if not name or not name.strip():
            raise ValidationError(
                message="Table name cannot be empty",
                details={"name": name},
            )

        # Validate table name (alphanumeric and underscores only)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
            raise ValidationError(
                message=f"Invalid table name: {name}. Must start with letter/underscore and contain only alphanumeric characters and underscores.",
                details={"name": name},
            )

        if dataframe.empty:
            raise ValidationError(
                message=f"Cannot register empty DataFrame as table: {name}",
                details={"name": name},
            )

        self._tables[name] = dataframe.copy()

    def unregister_table(self, name: str) -> bool:
        """Unregister a table.

        Args:
            name: Table name to unregister

        Returns:
            True if table was found and removed, False otherwise
        """
        if name in self._tables:
            del self._tables[name]
            return True
        return False

    def list_tables(self) -> List[str]:
        """List all registered table names.

        Returns:
            List of registered table names
        """
        return list(self._tables.keys())

    def get_table(self, name: str) -> Optional[pd.DataFrame]:
        """Get a registered table by name.

        Args:
            name: Table name

        Returns:
            DataFrame if found, None otherwise
        """
        return self._tables.get(name)

    def execute_query(self, sql_query: str) -> QueryResult:
        """Execute a SQL query on registered tables.

        Supports standard SQL SELECT statements with WHERE, ORDER BY,
        GROUP BY, LIMIT, and aggregation functions.

        Args:
            sql_query: SQL query string

        Returns:
            QueryResult containing the results

        Raises:
            ValidationError: If query is invalid or tables not found
        """
        import time

        start_time = time.time()

        if not sql_query or not sql_query.strip():
            raise ValidationError(
                message="SQL query cannot be empty",
            )

        # Validate query is a SELECT statement
        query_upper = sql_query.strip().upper()
        if not query_upper.startswith("SELECT"):
            raise ValidationError(
                message="Only SELECT queries are supported",
                details={"query": sql_query},
            )

        try:
            if self._duckdb_available:
                result_df = self._execute_with_duckdb(sql_query)
            else:
                result_df = self._execute_with_pandas(sql_query)

            execution_time = (time.time() - start_time) * 1000

            return QueryResult(
                data=result_df,
                row_count=len(result_df),
                columns=list(result_df.columns),
                execution_time_ms=execution_time,
                query=sql_query,
            )

        except Exception as e:
            raise ValidationError(
                message=f"Query execution failed: {str(e)}",
                details={"query": sql_query, "error": str(e)},
            )

    def _execute_with_duckdb(self, sql_query: str) -> pd.DataFrame:
        """Execute query using DuckDB.

        Args:
            sql_query: SQL query string

        Returns:
            Query result as DataFrame
        """
        import duckdb

        # Create a connection and register tables
        con = duckdb.connect(database=":memory:")

        for name, df in self._tables.items():
            con.register(name, df)

        # Execute query
        result = con.execute(sql_query).fetchdf()
        con.close()

        return result

    def _execute_with_pandas(self, sql_query: str) -> pd.DataFrame:
        """Execute query using pandas (fallback).

        This provides limited SQL functionality using pandas operations.

        Args:
            sql_query: SQL query string

        Returns:
            Query result as DataFrame
        """
        # Parse simple SELECT * FROM table WHERE ... queries
        match = re.match(
            r"SELECT\s+(.+?)\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+?))?(?:\s+ORDER\s+BY\s+(.+?))?(?:\s+LIMIT\s+(\d+))?",
            sql_query,
            re.IGNORECASE,
        )

        if not match:
            raise ValidationError(
                message="Query parsing failed. Supported format: SELECT ... FROM table [WHERE ...] [ORDER BY ...] [LIMIT n]",
                details={"query": sql_query},
            )

        select_cols, table_name, where_clause, order_by, limit = match.groups()

        if table_name not in self._tables:
            raise ValidationError(
                message=f"Table not found: {table_name}",
                details={"table": table_name, "available": list(self._tables.keys())},
            )

        df = self._tables[table_name].copy()

        # Apply WHERE clause (basic support)
        if where_clause:
            df = self._apply_where_clause(df, where_clause)

        # Apply ORDER BY
        if order_by:
            parts = order_by.strip().split()
            col = parts[0]
            ascending = len(parts) < 2 or parts[1].upper() != "DESC"
            if col in df.columns:
                df = df.sort_values(by=col, ascending=ascending)

        # Apply LIMIT
        if limit:
            df = df.head(int(limit))

        # Apply column selection
        select_cols = select_cols.strip()
        if select_cols != "*":
            cols = [c.strip() for c in select_cols.split(",")]
            # Filter to existing columns
            cols = [c for c in cols if c in df.columns]
            if cols:
                df = df[cols]

        return df

    def _apply_where_clause(self, df: pd.DataFrame, where_clause: str) -> pd.DataFrame:
        """Apply a simple WHERE clause to a DataFrame.

        Args:
            df: DataFrame to filter
            where_clause: WHERE clause string

        Returns:
            Filtered DataFrame
        """
        # Basic WHERE clause parsing (col op value)
        # Supports: =, !=, <>, <, >, <=, >=, LIKE, IN

        # Handle AND conditions
        conditions = re.split(r"\s+AND\s+", where_clause, flags=re.IGNORECASE)

        for condition in conditions:
            condition = condition.strip()

            # Parse condition
            match = re.match(
                r"(\w+)\s*(=|!=|<>|<=|>=|<|>|LIKE|IN)\s*(.+)",
                condition,
                re.IGNORECASE,
            )

            if not match:
                continue

            col, op, value = match.groups()
            col = col.strip()
            op = op.strip().upper()
            value = value.strip()

            if col not in df.columns:
                continue

            # Remove quotes from value
            if (value.startswith("'") and value.endswith("'")) or \
               (value.startswith('"') and value.endswith('"')):
                value = value[1:-1]

            # Apply operator
            if op == "=":
                try:
                    df = df[df[col] == value]
                except Exception:
                    pass
            elif op in ("!=", "<>"):
                try:
                    df = df[df[col] != value]
                except Exception:
                    pass
            elif op == "<":
                try:
                    df = df[df[col] < float(value)]
                except Exception:
                    pass
            elif op == ">":
                try:
                    df = df[df[col] > float(value)]
                except Exception:
                    pass
            elif op == "<=":
                try:
                    df = df[df[col] <= float(value)]
                except Exception:
                    pass
            elif op == ">=":
                try:
                    df = df[df[col] >= float(value)]
                except Exception:
                    pass
            elif op == "LIKE":
                pattern = value.replace("%", ".*").replace("_", ".")
                try:
                    df = df[df[col].astype(str).str.match(pattern, case=False, na=False)]
                except Exception:
                    pass

        return df

    def search_columns(
        self,
        query: str,
        columns: List[str],
        table_name: Optional[str] = None,
        top_k: int = 10,
        case_sensitive: bool = False,
    ) -> List[SearchResult]:
        """Perform semantic-like search on specific columns.

        This performs a keyword-based search on specified columns, useful
        for finding rows matching search terms.

        Args:
            query: Search query string
            columns: Columns to search in
            table_name: Specific table to search (searches all if None)
            top_k: Maximum results to return
            case_sensitive: Whether search is case sensitive

        Returns:
            List of SearchResult objects
        """
        if not query or not query.strip():
            return []

        if not columns:
            return []

        results = []
        query_terms = query.lower().split()

        tables_to_search = {}
        if table_name:
            if table_name in self._tables:
                tables_to_search = {table_name: self._tables[table_name]}
        else:
            tables_to_search = self._tables

        doc_id = uuid4()

        for tname, df in tables_to_search.items():
            # Filter to available columns
            search_cols = [c for c in columns if c in df.columns]

            if not search_cols:
                continue

            # Score each row
            scored_rows = []
            for idx, row in df.iterrows():
                score = 0.0
                matched_texts = []

                for col in search_cols:
                    if pd.notna(row[col]):
                        cell_text = str(row[col])
                        cell_text_cmp = cell_text if case_sensitive else cell_text.lower()

                        # Count term matches
                        matches = sum(1 for term in query_terms if term in cell_text_cmp)
                        if matches > 0:
                            score += matches / len(query_terms)
                            matched_texts.append(f"{col}: {cell_text}")

                if score > 0:
                    scored_rows.append((idx, score, matched_texts, row))

            # Sort by score and take top_k
            scored_rows.sort(key=lambda x: x[1], reverse=True)

            for rank, (idx, score, matched_texts, row) in enumerate(scored_rows[:top_k], 1):
                content = "\n".join(matched_texts) if matched_texts else str(row.to_dict())

                metadata = Metadata(
                    source=f"table:{tname}",
                    custom={
                        "table": tname,
                        "row_index": int(idx),
                        **{str(k): str(v) for k, v in row.items() if pd.notna(v)},
                    },
                )

                chunk = DocumentChunk(
                    document_id=doc_id,
                    content=content,
                    metadata=metadata,
                    index=int(idx),
                )

                result = SearchResult(
                    chunk=chunk,
                    score=min(score, 1.0),
                    rank=rank,
                    distance=1.0 - min(score, 1.0),
                    explanation=f"Matched {len(matched_texts)} columns with score {score:.3f}",
                )
                results.append(result)

        # Re-rank all results
        results.sort(key=lambda x: x.score, reverse=True)
        for i, result in enumerate(results[:top_k], 1):
            result.rank = i

        return results[:top_k]

    def convert_to_chunks(
        self,
        query_result: QueryResult,
        source: Optional[str] = None,
    ) -> List[DocumentChunk]:
        """Convert a QueryResult to DocumentChunk objects.

        Args:
            query_result: Query result to convert
            source: Source identifier

        Returns:
            List of DocumentChunk objects
        """
        if query_result.data.empty:
            return []

        doc_id = uuid4()
        chunks = []

        for idx, row in query_result.data.iterrows():
            # Create content from all columns
            content_parts = []
            for col in query_result.columns:
                if pd.notna(row[col]):
                    content_parts.append(f"{col}: {row[col]}")

            content = "\n".join(content_parts)

            metadata = Metadata(
                source=source or "sql_query",
                custom={
                    "query": query_result.query,
                    "row_index": int(idx),
                    **{str(k): str(v) for k, v in row.items() if pd.notna(v)},
                },
            )

            chunk = DocumentChunk(
                document_id=doc_id,
                content=content,
                metadata=metadata,
                index=int(idx),
            )
            chunks.append(chunk)

        return chunks

    def clear_all_tables(self) -> None:
        """Clear all registered tables."""
        self._tables.clear()
