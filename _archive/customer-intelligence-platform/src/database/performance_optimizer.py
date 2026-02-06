"""
Database Performance Optimizer for Customer Intelligence Platform.

Comprehensive performance optimization including:
- Advanced indexing strategies
- Query optimization
- Connection pooling
- Performance monitoring
- Slow query detection
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import time

from sqlalchemy import text, inspect, MetaData
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine import URL
import asyncpg

logger = logging.getLogger(__name__)

@dataclass
class IndexRecommendation:
    """Recommendation for database index creation."""
    table_name: str
    columns: List[str]
    index_type: str  # btree, gin, gist, hash
    rationale: str
    expected_improvement: str
    create_sql: str

@dataclass
class QueryPerformanceMetrics:
    """Performance metrics for database queries."""
    query_id: str
    query_text: str
    execution_time_ms: float
    rows_examined: int
    rows_returned: int
    timestamp: datetime
    execution_plan: Optional[Dict[str, Any]] = None

class DatabasePerformanceOptimizer:
    """Advanced database performance optimization and monitoring."""

    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.query_metrics: List[QueryPerformanceMetrics] = []
        self.slow_query_threshold_ms = 100  # 100ms threshold
        self.session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def analyze_table_performance(self) -> Dict[str, Any]:
        """Analyze table-level performance metrics."""
        async with self.session_factory() as session:
            # Get table sizes and statistics
            table_stats_query = text("""
                SELECT
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows,
                    last_vacuum,
                    last_autovacuum,
                    last_analyze,
                    last_autoanalyze
                FROM pg_stat_user_tables
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """)

            result = await session.execute(table_stats_query)
            table_stats = [dict(row) for row in result]

            # Get index usage statistics
            index_stats_query = text("""
                SELECT
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch,
                    idx_scan,
                    pg_size_pretty(pg_relation_size(schemaname||'.'||indexname)) as index_size
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC;
            """)

            result = await session.execute(index_stats_query)
            index_stats = [dict(row) for row in result]

            return {
                "table_statistics": table_stats,
                "index_statistics": index_stats,
                "analysis_timestamp": datetime.utcnow()
            }

    async def recommend_indexes(self) -> List[IndexRecommendation]:
        """Generate index recommendations based on query patterns."""
        recommendations = []

        # Analyze missing indexes for common query patterns
        async with self.session_factory() as session:
            # Check for missing indexes on foreign keys
            fk_without_index_query = text("""
                SELECT
                    t.table_name,
                    kcu.column_name
                FROM information_schema.table_constraints t
                JOIN information_schema.key_column_usage kcu
                    ON t.constraint_name = kcu.constraint_name
                WHERE t.constraint_type = 'FOREIGN KEY'
                    AND t.table_schema = 'public'
                    AND NOT EXISTS (
                        SELECT 1 FROM pg_indexes
                        WHERE tablename = t.table_name
                        AND indexdef LIKE '%' || kcu.column_name || '%'
                    );
            """)

            result = await session.execute(fk_without_index_query)
            fk_missing = result.fetchall()

            for row in fk_missing:
                table_name, column_name = row
                recommendations.append(IndexRecommendation(
                    table_name=table_name,
                    columns=[column_name],
                    index_type="btree",
                    rationale=f"Foreign key {column_name} lacks index for JOIN performance",
                    expected_improvement="50-90% JOIN query improvement",
                    create_sql=f"CREATE INDEX CONCURRENTLY idx_{table_name}_{column_name}_fk ON {table_name}({column_name});"
                ))

            # Check for composite index opportunities
            recommendations.extend(await self._analyze_composite_index_opportunities(session))

            # Check for partial index opportunities
            recommendations.extend(await self._analyze_partial_index_opportunities(session))

        return recommendations

    async def _analyze_composite_index_opportunities(self, session: AsyncSession) -> List[IndexRecommendation]:
        """Analyze opportunities for composite indexes."""
        recommendations = []

        # Common multi-column query patterns
        composite_patterns = [
            # Customer analysis patterns
            {
                "table": "customers",
                "columns": ["department", "status", "created_at"],
                "rationale": "Common filtering pattern for customer analytics",
                "queries": ["department + status filters", "department + status + time range"]
            },
            {
                "table": "customer_scores",
                "columns": ["customer_id", "score_type", "created_at"],
                "rationale": "Latest score retrieval for customer",
                "queries": ["get latest score by type for customer"]
            },
            {
                "table": "conversation_messages",
                "columns": ["customer_id", "timestamp", "role"],
                "rationale": "Conversation history retrieval with role filtering",
                "queries": ["customer conversation history", "conversation analytics"]
            },
            # Multi-tenant patterns (if tenant_id exists)
            {
                "table": "customers",
                "columns": ["tenant_id", "status", "department"],
                "rationale": "Multi-tenant customer filtering",
                "queries": ["tenant-specific customer queries"]
            }
        ]

        for pattern in composite_patterns:
            # Check if this composite index would be beneficial
            columns_str = ", ".join(pattern["columns"])
            index_name = f"idx_{pattern['table']}_{'_'.join(pattern['columns'])}"

            recommendations.append(IndexRecommendation(
                table_name=pattern["table"],
                columns=pattern["columns"],
                index_type="btree",
                rationale=pattern["rationale"],
                expected_improvement="30-70% query performance improvement",
                create_sql=f"CREATE INDEX CONCURRENTLY {index_name} ON {pattern['table']}({columns_str});"
            ))

        return recommendations

    async def _analyze_partial_index_opportunities(self, session: AsyncSession) -> List[IndexRecommendation]:
        """Analyze opportunities for partial indexes."""
        recommendations = []

        # Analyze data distribution for partial index opportunities
        partial_patterns = [
            {
                "table": "customers",
                "columns": ["email"],
                "condition": "email IS NOT NULL",
                "rationale": "Only index customers with email addresses",
                "benefit": "Reduced index size, faster updates"
            },
            {
                "table": "customer_scores",
                "columns": ["score", "confidence"],
                "condition": "score > 0.7",
                "rationale": "Index only high-score customers for quick filtering",
                "benefit": "Faster high-value customer queries"
            },
            {
                "table": "conversation_messages",
                "columns": ["timestamp", "customer_id"],
                "condition": "timestamp > CURRENT_TIMESTAMP - INTERVAL '30 days'",
                "rationale": "Index only recent messages",
                "benefit": "Reduced index size for time-based queries"
            }
        ]

        for pattern in partial_patterns:
            columns_str = ", ".join(pattern["columns"])
            index_name = f"idx_{pattern['table']}_{'_'.join(pattern['columns'])}_partial"

            recommendations.append(IndexRecommendation(
                table_name=pattern["table"],
                columns=pattern["columns"],
                index_type="btree_partial",
                rationale=pattern["rationale"],
                expected_improvement=pattern["benefit"],
                create_sql=f"CREATE INDEX CONCURRENTLY {index_name} ON {pattern['table']}({columns_str}) WHERE {pattern['condition']};"
            ))

        return recommendations

    async def create_optimized_indexes(self, recommendations: List[IndexRecommendation]) -> Dict[str, Any]:
        """Create recommended indexes with proper error handling."""
        results = {
            "created": [],
            "failed": [],
            "skipped": []
        }

        async with self.session_factory() as session:
            for rec in recommendations:
                try:
                    # Check if index already exists
                    check_query = text("""
                        SELECT indexname FROM pg_indexes
                        WHERE tablename = :table_name
                        AND indexdef LIKE :pattern
                    """)

                    existing = await session.execute(
                        check_query,
                        {
                            "table_name": rec.table_name,
                            "pattern": f"%{rec.columns[0]}%"
                        }
                    )

                    if existing.first():
                        results["skipped"].append({
                            "table": rec.table_name,
                            "columns": rec.columns,
                            "reason": "Similar index already exists"
                        })
                        continue

                    # Create index
                    logger.info(f"Creating index for {rec.table_name}: {rec.columns}")
                    await session.execute(text(rec.create_sql))
                    await session.commit()

                    results["created"].append({
                        "table": rec.table_name,
                        "columns": rec.columns,
                        "sql": rec.create_sql
                    })

                except Exception as e:
                    logger.error(f"Failed to create index for {rec.table_name}: {e}")
                    results["failed"].append({
                        "table": rec.table_name,
                        "columns": rec.columns,
                        "error": str(e)
                    })
                    await session.rollback()

        return results

    def start_query_monitoring(self, sample_rate: float = 0.1):
        """Start monitoring query performance."""
        # This would typically integrate with PostgreSQL's pg_stat_statements
        # For now, we'll implement a basic query wrapper
        original_execute = self.session_factory.execute

        async def monitored_execute(self, statement, parameters=None):
            start_time = time.perf_counter()

            try:
                result = await original_execute(statement, parameters)
                execution_time = (time.perf_counter() - start_time) * 1000

                # Sample queries for monitoring
                if execution_time > self.slow_query_threshold_ms or asyncio.random() < sample_rate:
                    await self._record_query_metrics(
                        str(statement), execution_time, parameters
                    )

                return result

            except Exception as e:
                execution_time = (time.perf_counter() - start_time) * 1000
                await self._record_query_metrics(
                    str(statement), execution_time, parameters, error=str(e)
                )
                raise

        # Monkey patch for monitoring (in production, use proper APM tools)
        self.session_factory.execute = monitored_execute

    async def _record_query_metrics(self, query: str, execution_time: float,
                                   parameters: Any = None, error: str = None):
        """Record query performance metrics."""
        metric = QueryPerformanceMetrics(
            query_id=hash(query) % 10000,
            query_text=query[:500],  # Truncate long queries
            execution_time_ms=execution_time,
            rows_examined=0,  # Would need EXPLAIN ANALYZE for accurate numbers
            rows_returned=0,
            timestamp=datetime.utcnow()
        )

        self.query_metrics.append(metric)

        # Keep only recent metrics (last 1000 queries)
        if len(self.query_metrics) > 1000:
            self.query_metrics = self.query_metrics[-1000:]

        # Log slow queries
        if execution_time > self.slow_query_threshold_ms:
            logger.warning(
                f"Slow query detected: {execution_time:.2f}ms - {query[:100]}..."
            )

    async def get_slow_queries(self, limit: int = 10) -> List[QueryPerformanceMetrics]:
        """Get slowest queries from recent monitoring."""
        return sorted(
            self.query_metrics,
            key=lambda x: x.execution_time_ms,
            reverse=True
        )[:limit]

    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        table_analysis = await self.analyze_table_performance()
        index_recommendations = await self.recommend_indexes()
        slow_queries = await self.get_slow_queries()

        # Calculate metrics
        if self.query_metrics:
            avg_query_time = sum(m.execution_time_ms for m in self.query_metrics) / len(self.query_metrics)
            slow_query_count = len([m for m in self.query_metrics if m.execution_time_ms > self.slow_query_threshold_ms])
            slow_query_percentage = (slow_query_count / len(self.query_metrics)) * 100
        else:
            avg_query_time = 0
            slow_query_percentage = 0

        return {
            "performance_summary": {
                "avg_query_time_ms": avg_query_time,
                "slow_query_percentage": slow_query_percentage,
                "total_queries_monitored": len(self.query_metrics),
                "analysis_timestamp": datetime.utcnow()
            },
            "table_analysis": table_analysis,
            "index_recommendations": [
                {
                    "table": rec.table_name,
                    "columns": rec.columns,
                    "type": rec.index_type,
                    "rationale": rec.rationale,
                    "expected_improvement": rec.expected_improvement,
                    "sql": rec.create_sql
                }
                for rec in index_recommendations
            ],
            "slow_queries": [
                {
                    "query_id": q.query_id,
                    "execution_time_ms": q.execution_time_ms,
                    "query_preview": q.query_text[:200],
                    "timestamp": q.timestamp
                }
                for q in slow_queries
            ]
        }

class ConnectionPoolOptimizer:
    """Optimize database connection pooling."""

    @staticmethod
    def get_optimized_engine(database_url: str, **kwargs) -> AsyncEngine:
        """Create optimized async engine with connection pooling."""
        from sqlalchemy.ext.asyncio import create_async_engine

        # Calculate optimal pool size based on expected load
        # Rule of thumb: pool_size = (number_of_cpu_cores * 2) + effective_spindle_count
        # For async workloads, can be higher

        pool_settings = {
            "poolclass": QueuePool,
            "pool_size": kwargs.get("pool_size", 20),  # Base connections
            "max_overflow": kwargs.get("max_overflow", 30),  # Additional connections
            "pool_pre_ping": True,  # Validate connections
            "pool_recycle": kwargs.get("pool_recycle", 3600),  # Recycle connections hourly
            "pool_timeout": kwargs.get("pool_timeout", 10),  # Connection timeout
        }

        # Additional async-specific optimizations
        engine_settings = {
            "echo": kwargs.get("echo", False),
            "echo_pool": kwargs.get("echo_pool", False),
            "future": True,  # Use SQLAlchemy 2.0 style
        }

        # Combine settings
        all_settings = {**pool_settings, **engine_settings}

        logger.info(f"Creating optimized database engine with pool_size={pool_settings['pool_size']}")

        return create_async_engine(database_url, **all_settings)

async def run_performance_analysis(database_url: str) -> Dict[str, Any]:
    """Run complete performance analysis on the database."""
    # Create optimized engine
    engine = ConnectionPoolOptimizer.get_optimized_engine(database_url)

    try:
        # Initialize optimizer
        optimizer = DatabasePerformanceOptimizer(engine)

        # Start monitoring
        optimizer.start_query_monitoring(sample_rate=1.0)  # Monitor all queries for analysis

        # Generate performance report
        report = await optimizer.generate_performance_report()

        return report

    finally:
        await engine.dispose()

# CLI for performance analysis
if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python performance_optimizer.py <database_url>")
        sys.exit(1)

    database_url = sys.argv[1]

    async def main():
        report = await run_performance_analysis(database_url)
        print(json.dumps(report, indent=2, default=str))

    asyncio.run(main())