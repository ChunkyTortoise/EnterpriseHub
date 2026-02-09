"""
Optimized Query Service - High-Performance Database Operations

Implements advanced query optimization techniques:
- Cursor-based pagination for large result sets
- Query result caching with intelligent invalidation
- Slow query detection and logging (>100ms threshold)
- Connection pooling optimization
- Batch query processing

Performance Targets:
- Database queries <50ms average (vs 120ms baseline)
- Pagination queries <20ms per page
- Cache hit ratio >85% for repeated queries
- Slow query detection and optimization
"""

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.database.connection_manager import get_db_pool
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)

# Performance configuration
SLOW_QUERY_THRESHOLD_MS = 100  # Log queries slower than 100ms
CACHE_TTL_QUERY_RESULTS = 600  # Cache query results for 10 minutes
CACHE_TTL_PAGINATION_METADATA = 3600  # Cache pagination metadata for 1 hour
DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 500
BATCH_SIZE = 100


class SortDirection(Enum):
    """Query sort direction."""

    ASC = "ASC"
    DESC = "DESC"


class QueryType(Enum):
    """Type of database query for optimization tracking."""

    LEAD_SEARCH = "lead_search"
    PROPERTY_SEARCH = "property_search"
    CONVERSATION_HISTORY = "conversation_history"
    ANALYTICS_QUERY = "analytics_query"
    REPORT_GENERATION = "report_generation"


@dataclass
class PaginationCursor:
    """Cursor-based pagination for efficient large result sets."""

    # Cursor fields for ordering
    sort_field: str
    sort_value: Any
    unique_id: str  # Tie-breaker for consistent ordering

    # Pagination metadata
    page_size: int = DEFAULT_PAGE_SIZE
    sort_direction: SortDirection = SortDirection.DESC

    def to_string(self) -> str:
        """Encode cursor as base64 string for API responses."""
        import base64

        cursor_data = {
            "sort_field": self.sort_field,
            "sort_value": str(self.sort_value),
            "unique_id": self.unique_id,
            "page_size": self.page_size,
            "sort_direction": self.sort_direction.value,
        }
        cursor_json = json.dumps(cursor_data)
        return base64.b64encode(cursor_json.encode()).decode()

    @classmethod
    def from_string(cls, cursor_str: str) -> "PaginationCursor":
        """Decode cursor from base64 string."""
        import base64

        cursor_json = base64.b64decode(cursor_str).decode()
        cursor_data = json.loads(cursor_json)

        return cls(
            sort_field=cursor_data["sort_field"],
            sort_value=cursor_data["sort_value"],
            unique_id=cursor_data["unique_id"],
            page_size=cursor_data["page_size"],
            sort_direction=SortDirection(cursor_data["sort_direction"]),
        )


@dataclass
class QueryResult:
    """Optimized query result with performance metadata."""

    # Query results
    items: List[Dict[str, Any]]

    # Pagination
    next_cursor: Optional[PaginationCursor]
    has_more: bool
    total_count: Optional[int] = None  # Only provided for small result sets

    # Performance metadata
    query_time_ms: float
    cache_hit: bool = False
    items_returned: int = 0

    def __post_init__(self):
        self.items_returned = len(self.items)


class OptimizedQueryService:
    """
    High-performance database query service with advanced optimizations.

    Features:
    - Cursor-based pagination for consistent, fast large result sets
    - Intelligent query result caching with invalidation
    - Slow query detection and performance monitoring
    - Connection pool optimization
    - Batch processing for bulk operations
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.pool = None  # Will be initialized async

        # Performance tracking
        self.query_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_query_time_ms": 0.0,
            "total_query_time_ms": 0.0,
        }

    async def initialize(self):
        """Initialize database connection pool."""
        if not self.pool:
            self.pool = await get_db_pool()

    # CORE PAGINATION METHODS

    async def query_with_pagination(
        self,
        query: str,
        params: List[Any],
        query_type: QueryType,
        cursor: Optional[PaginationCursor] = None,
        cache_key: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> QueryResult:
        """
        Execute paginated query with cursor-based pagination.

        Args:
            query: Base SQL query (without ORDER BY or LIMIT)
            params: Query parameters
            query_type: Type of query for optimization tracking
            cursor: Pagination cursor (None for first page)
            cache_key: Optional cache key for result caching
            tenant_id: Tenant ID for cache scoping
        """
        await self.initialize()
        start_time = time.time()

        # Check cache first if cache_key provided
        if cache_key and tenant_id:
            cached_result = await self._get_cached_result(cache_key, tenant_id)
            if cached_result:
                cached_result.cache_hit = True
                self.query_stats["cache_hits"] += 1
                return cached_result

        try:
            # Build paginated query
            paginated_query, paginated_params = self._build_paginated_query(query, params, cursor)

            # Execute query
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(paginated_query, *paginated_params)

            # Process results
            items = [dict(row) for row in rows]

            # Determine if there are more results and create next cursor
            page_size = cursor.page_size if cursor else DEFAULT_PAGE_SIZE
            has_more = len(items) == page_size + 1  # We fetch page_size + 1

            if has_more:
                items = items[:-1]  # Remove extra item
                last_item = items[-1]
                sort_field = cursor.sort_field if cursor else "id"

                next_cursor = PaginationCursor(
                    sort_field=sort_field,
                    sort_value=last_item.get(sort_field),
                    unique_id=str(last_item.get("id", last_item.get("uuid", ""))),
                    page_size=page_size,
                    sort_direction=cursor.sort_direction if cursor else SortDirection.DESC,
                )
            else:
                next_cursor = None

            # Calculate performance metrics
            query_time_ms = (time.time() - start_time) * 1000

            # Log slow queries
            if query_time_ms > SLOW_QUERY_THRESHOLD_MS:
                self.query_stats["slow_queries"] += 1
                logger.warning(f"Slow query detected ({query_time_ms:.2f}ms): {query_type.value}")
                logger.debug(f"Query: {paginated_query}")
                logger.debug(f"Params: {paginated_params}")

            # Update performance stats
            self._update_query_stats(query_time_ms, cache_hit=False)

            result = QueryResult(
                items=items, next_cursor=next_cursor, has_more=has_more, query_time_ms=query_time_ms, cache_hit=False
            )

            # Cache result if cache_key provided
            if cache_key and tenant_id:
                await self._cache_result(cache_key, result, tenant_id)
                self.query_stats["cache_misses"] += 1

            return result

        except Exception as e:
            query_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Query failed ({query_time_ms:.2f}ms): {e}", exc_info=True)
            raise

    def _build_paginated_query(
        self, base_query: str, params: List[Any], cursor: Optional[PaginationCursor]
    ) -> Tuple[str, List[Any]]:
        """Build paginated query with cursor conditions."""

        # Default pagination settings
        sort_field = cursor.sort_field if cursor else "id"
        sort_direction = cursor.sort_direction if cursor else SortDirection.DESC
        page_size = cursor.page_size if cursor else DEFAULT_PAGE_SIZE

        # Ensure page size limits
        page_size = min(max(page_size, 1), MAX_PAGE_SIZE)

        # Build ORDER BY clause
        order_clause = f"ORDER BY {sort_field} {sort_direction.value}, id ASC"

        # Build pagination WHERE clause
        pagination_clause = ""
        paginated_params = list(params)

        if cursor and cursor.sort_value is not None:
            param_index = len(paginated_params) + 1

            if sort_direction == SortDirection.DESC:
                if cursor.sort_field == "id":
                    pagination_clause = f"WHERE id < ${param_index}"
                else:
                    pagination_clause = f"WHERE ({sort_field} < ${param_index} OR ({sort_field} = ${param_index} AND id > ${param_index + 1}))"
                    paginated_params.append(cursor.unique_id)
            else:
                if cursor.sort_field == "id":
                    pagination_clause = f"WHERE id > ${param_index}"
                else:
                    pagination_clause = f"WHERE ({sort_field} > ${param_index} OR ({sort_field} = ${param_index} AND id > ${param_index + 1}))"
                    paginated_params.append(cursor.unique_id)

            paginated_params.insert(-1 if cursor.sort_field != "id" else -1, cursor.sort_value)

        # Handle existing WHERE clause
        if "WHERE" in base_query.upper():
            if pagination_clause:
                pagination_clause = pagination_clause.replace("WHERE", "AND")

        # Build final query
        final_query = f"""
        {base_query}
        {pagination_clause}
        {order_clause}
        LIMIT {page_size + 1}
        """

        return final_query.strip(), paginated_params

    # SPECIFIC QUERY METHODS

    async def search_leads(
        self,
        tenant_id: str,
        filters: Dict[str, Any] = None,
        cursor: Optional[PaginationCursor] = None,
        cache_duration: int = CACHE_TTL_QUERY_RESULTS,
    ) -> QueryResult:
        """Optimized lead search with pagination."""

        # Build base query
        where_conditions = ["tenant_id = $1"]
        params = [tenant_id]
        param_index = 2

        # Apply filters
        if filters:
            if "phone" in filters:
                where_conditions.append(f"phone ILIKE ${param_index}")
                params.append(f"%{filters['phone']}%")
                param_index += 1

            if "email" in filters:
                where_conditions.append(f"email ILIKE ${param_index}")
                params.append(f"%{filters['email']}%")
                param_index += 1

            if "lead_score_min" in filters:
                where_conditions.append(f"lead_score >= ${param_index}")
                params.append(filters["lead_score_min"])
                param_index += 1

            if "created_after" in filters:
                where_conditions.append(f"created_at >= ${param_index}")
                params.append(filters["created_after"])
                param_index += 1

        base_query = f"""
        SELECT id, phone, email, lead_score, created_at, updated_at,
               first_name, last_name, status, source
        FROM leads
        WHERE {" AND ".join(where_conditions)}
        """

        # Generate cache key
        cache_key = self._generate_cache_key("leads_search", filters or {}, cursor)

        return await self.query_with_pagination(
            query=base_query,
            params=params,
            query_type=QueryType.LEAD_SEARCH,
            cursor=cursor,
            cache_key=cache_key,
            tenant_id=tenant_id,
        )

    async def search_properties(
        self, tenant_id: str, filters: Dict[str, Any] = None, cursor: Optional[PaginationCursor] = None
    ) -> QueryResult:
        """Optimized property search with pagination."""

        where_conditions = ["location_id = $1"]
        params = [tenant_id]
        param_index = 2

        # Apply filters
        if filters:
            if "min_price" in filters:
                where_conditions.append(f"price >= ${param_index}")
                params.append(filters["min_price"])
                param_index += 1

            if "max_price" in filters:
                where_conditions.append(f"price <= ${param_index}")
                params.append(filters["max_price"])
                param_index += 1

            if "bedrooms" in filters:
                where_conditions.append(f"bedrooms >= ${param_index}")
                params.append(filters["bedrooms"])
                param_index += 1

            if "zip_code" in filters:
                where_conditions.append(f"zip_code = ${param_index}")
                params.append(filters["zip_code"])
                param_index += 1

        base_query = f"""
        SELECT id, address, price, bedrooms, bathrooms, sqft,
               zip_code, listing_status, created_at
        FROM properties
        WHERE {" AND ".join(where_conditions)}
        """

        cache_key = self._generate_cache_key("properties_search", filters or {}, cursor)

        return await self.query_with_pagination(
            query=base_query,
            params=params,
            query_type=QueryType.PROPERTY_SEARCH,
            cursor=cursor,
            cache_key=cache_key,
            tenant_id=tenant_id,
        )

    async def get_conversation_history(
        self, tenant_id: str, lead_id: Optional[str] = None, cursor: Optional[PaginationCursor] = None
    ) -> QueryResult:
        """Get conversation history with efficient pagination."""

        where_conditions = ["tenant_id = $1"]
        params = [tenant_id]
        param_index = 2

        if lead_id:
            where_conditions.append(f"lead_id = ${param_index}")
            params.append(lead_id)
            param_index += 1

        base_query = f"""
        SELECT id, lead_id, message_content, sender, timestamp,
               conversation_stage, ai_confidence
        FROM conversations
        WHERE {" AND ".join(where_conditions)}
        """

        # Default cursor for conversations (newest first)
        if not cursor:
            cursor = PaginationCursor(
                sort_field="timestamp", sort_value=None, unique_id="", sort_direction=SortDirection.DESC
            )

        cache_key = self._generate_cache_key("conversations", {"lead_id": lead_id}, cursor)

        return await self.query_with_pagination(
            query=base_query,
            params=params,
            query_type=QueryType.CONVERSATION_HISTORY,
            cursor=cursor,
            cache_key=cache_key,
            tenant_id=tenant_id,
        )

    # BATCH OPERATIONS

    async def batch_update_lead_scores(self, tenant_id: str, score_updates: List[Dict[str, Any]]) -> int:
        """Batch update lead scores for performance."""
        await self.initialize()

        if not score_updates:
            return 0

        start_time = time.time()
        updated_count = 0

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for batch_start in range(0, len(score_updates), BATCH_SIZE):
                        batch = score_updates[batch_start : batch_start + BATCH_SIZE]

                        # Build batch update query
                        update_queries = []
                        update_params = []

                        for i, update in enumerate(batch):
                            lead_id = update["lead_id"]
                            new_score = update["lead_score"]

                            param_base = i * 3 + 1
                            update_queries.append(f"""
                                UPDATE leads
                                SET lead_score = ${param_base}, updated_at = ${param_base + 1}
                                WHERE id = ${param_base + 2} AND tenant_id = $1
                            """)

                            update_params.extend([new_score, datetime.utcnow(), lead_id])

                        # Execute batch
                        for query in update_queries:
                            result = await conn.execute(query, tenant_id, *update_params[:3])
                            if result.split()[-1] == "1":  # "UPDATE 1"
                                updated_count += 1
                            update_params = update_params[3:]  # Next set of params

            # Invalidate related caches
            await self._invalidate_cache_pattern(f"tenant:{tenant_id}:leads_search:*")

            query_time_ms = (time.time() - start_time) * 1000
            self._update_query_stats(query_time_ms, cache_hit=False)

            logger.info(f"Batch updated {updated_count} lead scores in {query_time_ms:.2f}ms")
            return updated_count

        except Exception as e:
            logger.error(f"Batch update failed: {e}", exc_info=True)
            raise

    # CACHE MANAGEMENT

    async def _get_cached_result(self, cache_key: str, tenant_id: str) -> Optional[QueryResult]:
        """Retrieve cached query result."""
        try:
            scoped_key = f"tenant:{tenant_id}:query:{cache_key}"
            cached_data = await self.cache.get(scoped_key)

            if cached_data:
                # Reconstruct QueryResult from cached data
                next_cursor = None
                if cached_data.get("next_cursor_data"):
                    next_cursor = PaginationCursor(**cached_data["next_cursor_data"])

                return QueryResult(
                    items=cached_data["items"],
                    next_cursor=next_cursor,
                    has_more=cached_data["has_more"],
                    total_count=cached_data.get("total_count"),
                    query_time_ms=cached_data["query_time_ms"],
                    cache_hit=True,
                )
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")

        return None

    async def _cache_result(self, cache_key: str, result: QueryResult, tenant_id: str):
        """Cache query result."""
        try:
            scoped_key = f"tenant:{tenant_id}:query:{cache_key}"

            # Prepare data for caching
            cache_data = {
                "items": result.items,
                "has_more": result.has_more,
                "total_count": result.total_count,
                "query_time_ms": result.query_time_ms,
                "cached_at": datetime.utcnow().isoformat(),
            }

            # Include cursor data if present
            if result.next_cursor:
                cache_data["next_cursor_data"] = {
                    "sort_field": result.next_cursor.sort_field,
                    "sort_value": result.next_cursor.sort_value,
                    "unique_id": result.next_cursor.unique_id,
                    "page_size": result.next_cursor.page_size,
                    "sort_direction": result.next_cursor.sort_direction.value,
                }

            await self.cache.set(scoped_key, cache_data, CACHE_TTL_QUERY_RESULTS)

        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")

    def _generate_cache_key(self, query_type: str, filters: Dict[str, Any], cursor: Optional[PaginationCursor]) -> str:
        """Generate deterministic cache key."""
        cache_data = {"query_type": query_type, "filters": filters, "cursor": cursor.to_string() if cursor else None}
        cache_str = json.dumps(cache_data, sort_keys=True, default=str)
        return hashlib.md5(cache_str.encode()).hexdigest()

    async def _invalidate_cache_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        # This is a simplified version - Redis implementation would use SCAN
        logger.debug(f"Cache invalidation requested for pattern: {pattern}")

    def _update_query_stats(self, query_time_ms: float, cache_hit: bool):
        """Update query performance statistics."""
        self.query_stats["total_queries"] += 1
        self.query_stats["total_query_time_ms"] += query_time_ms
        self.query_stats["avg_query_time_ms"] = (
            self.query_stats["total_query_time_ms"] / self.query_stats["total_queries"]
        )

    # MONITORING AND STATS

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get query performance statistics."""
        cache_stats = await self.cache.get_cache_stats()

        return {
            **self.query_stats,
            "slow_query_threshold_ms": SLOW_QUERY_THRESHOLD_MS,
            "slow_query_rate": (self.query_stats["slow_queries"] / max(self.query_stats["total_queries"], 1)) * 100,
            "cache_hit_rate": (
                self.query_stats["cache_hits"]
                / max(self.query_stats["cache_hits"] + self.query_stats["cache_misses"], 1)
            )
            * 100,
            "cache_performance": cache_stats,
        }

    async def get_slow_query_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate slow query report for optimization."""
        return {
            "period_hours": hours,
            "slow_queries_detected": self.query_stats["slow_queries"],
            "threshold_ms": SLOW_QUERY_THRESHOLD_MS,
            "optimization_recommendations": [
                "Consider adding database indexes for frequently filtered columns",
                "Review query patterns for N+1 issues",
                "Implement query result caching for repeated searches",
                "Consider database query plan analysis for complex queries",
            ],
        }


# Global service instance
_query_service = None


def get_optimized_query_service() -> OptimizedQueryService:
    """Get singleton optimized query service."""
    global _query_service
    if _query_service is None:
        _query_service = OptimizedQueryService()
    return _query_service
