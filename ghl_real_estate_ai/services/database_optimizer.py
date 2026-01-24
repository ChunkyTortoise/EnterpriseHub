"""
Database Optimization Service for Jorge's Real Estate AI Dashboard.

Provides automated database optimization and maintenance:
- Query performance analysis
- Index optimization
- Database cleanup and maintenance
- Connection pool optimization
- Cache performance tuning
"""

import asyncio
import aiosqlite
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json

from ghl_real_estate_ai.core.logger import get_logger

logger = get_logger(__name__)

@dataclass
class QueryPerformance:
    """Query performance metrics."""
    query: str
    execution_time_ms: float
    rows_affected: int
    timestamp: datetime
    optimization_suggestion: Optional[str] = None

@dataclass
class IndexAnalysis:
    """Database index analysis."""
    table: str
    index_name: str
    columns: List[str]
    usage_count: int
    last_used: Optional[datetime]
    effectiveness_score: float
    recommendation: str

@dataclass
class DatabaseHealth:
    """Overall database health metrics."""
    database_size_mb: float
    total_queries_today: int
    avg_query_time_ms: float
    slow_queries_count: int
    cache_hit_ratio: float
    fragmentation_ratio: float
    last_optimization: datetime
    recommendations: List[str]

class DatabaseOptimizer:
    """Comprehensive database optimization service."""

    def __init__(self, database_paths: List[str] = None):
        """Initialize database optimizer."""
        self.database_paths = database_paths or [
            "data/auth.db",
            "data/monitoring.db",
            "data/dashboard.db"
        ]

        self.performance_log_path = "data/query_performance.db"
        self.optimization_history_path = "data/optimization_history.json"

        # Performance thresholds
        self.slow_query_threshold_ms = 1000
        self.index_usage_threshold = 10
        self.fragmentation_threshold = 0.3

        # Optimization settings
        self.auto_vacuum_enabled = True
        self.cache_size_pages = 10000  # ~40MB cache
        self.temp_store_memory = True

    async def initialize_optimizer(self):
        """Initialize optimization tracking database."""
        try:
            # Create data directory
            Path(self.performance_log_path).parent.mkdir(parents=True, exist_ok=True)

            async with aiosqlite.connect(self.performance_log_path) as db:
                # Query performance tracking
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS query_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        database_name TEXT NOT NULL,
                        query_hash TEXT NOT NULL,
                        query_text TEXT NOT NULL,
                        execution_time_ms REAL NOT NULL,
                        rows_affected INTEGER,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Index usage tracking
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS index_usage (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        database_name TEXT NOT NULL,
                        table_name TEXT NOT NULL,
                        index_name TEXT NOT NULL,
                        usage_count INTEGER DEFAULT 0,
                        last_used DATETIME,
                        effectiveness_score REAL DEFAULT 0.0
                    )
                """)

                # Optimization history
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS optimization_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        database_name TEXT NOT NULL,
                        optimization_type TEXT NOT NULL,
                        description TEXT,
                        before_metrics TEXT,
                        after_metrics TEXT,
                        improvement_ratio REAL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                await db.commit()

            logger.info("Database optimizer initialized")

        except Exception as e:
            logger.error(f"Failed to initialize database optimizer: {e}")
            raise

    async def analyze_database_health(self, db_path: str) -> DatabaseHealth:
        """Comprehensive database health analysis."""
        try:
            async with aiosqlite.connect(db_path) as db:
                # Enable query analysis
                await db.execute("PRAGMA optimize")

                # Get database size
                stat_result = Path(db_path).stat()
                size_mb = stat_result.st_size / (1024 * 1024)

                # Analyze query performance from log
                performance_metrics = await self._analyze_query_performance(db_path)

                # Get table and index information
                index_analysis = await self._analyze_indexes(db)

                # Calculate fragmentation
                fragmentation_ratio = await self._calculate_fragmentation(db)

                # Get cache hit ratio (SQLite specific)
                cache_stats = await self._get_cache_statistics(db)

                # Generate optimization recommendations
                recommendations = await self._generate_recommendations(
                    db, size_mb, performance_metrics, index_analysis, fragmentation_ratio
                )

                health = DatabaseHealth(
                    database_size_mb=size_mb,
                    total_queries_today=performance_metrics.get('total_queries', 0),
                    avg_query_time_ms=performance_metrics.get('avg_time_ms', 0.0),
                    slow_queries_count=performance_metrics.get('slow_queries', 0),
                    cache_hit_ratio=cache_stats.get('hit_ratio', 0.0),
                    fragmentation_ratio=fragmentation_ratio,
                    last_optimization=await self._get_last_optimization_time(db_path),
                    recommendations=recommendations
                )

                return health

        except Exception as e:
            logger.error(f"Database health analysis failed for {db_path}: {e}")
            return DatabaseHealth(
                database_size_mb=0.0,
                total_queries_today=0,
                avg_query_time_ms=999.0,
                slow_queries_count=999,
                cache_hit_ratio=0.0,
                fragmentation_ratio=1.0,
                last_optimization=datetime.now() - timedelta(days=365),
                recommendations=["Health check failed - manual investigation required"]
            )

    async def optimize_database(self, db_path: str) -> Dict[str, Any]:
        """Perform database optimization operations."""
        optimization_results = {
            'database': db_path,
            'start_time': datetime.now(),
            'operations': [],
            'improvements': {},
            'errors': []
        }

        try:
            # Get baseline metrics
            baseline_health = await self.analyze_database_health(db_path)

            async with aiosqlite.connect(db_path) as db:
                # 1. Update database statistics
                await self._update_statistics(db, optimization_results)

                # 2. Optimize indexes
                await self._optimize_indexes(db, optimization_results)

                # 3. Clean up unused space
                await self._vacuum_database(db, optimization_results)

                # 4. Update SQLite configuration
                await self._optimize_sqlite_settings(db, optimization_results)

                # 5. Analyze and reorganize tables if needed
                await self._analyze_tables(db, optimization_results)

            # Get post-optimization metrics
            final_health = await self.analyze_database_health(db_path)

            # Calculate improvements
            optimization_results['improvements'] = {
                'size_reduction_mb': baseline_health.database_size_mb - final_health.database_size_mb,
                'query_time_improvement_ms': baseline_health.avg_query_time_ms - final_health.avg_query_time_ms,
                'cache_hit_ratio_improvement': final_health.cache_hit_ratio - baseline_health.cache_hit_ratio
            }

            optimization_results['end_time'] = datetime.now()
            optimization_results['duration_seconds'] = (
                optimization_results['end_time'] - optimization_results['start_time']
            ).total_seconds()

            # Log optimization history
            await self._log_optimization_history(db_path, optimization_results)

            logger.info(f"Database optimization completed for {db_path}")
            return optimization_results

        except Exception as e:
            logger.error(f"Database optimization failed for {db_path}: {e}")
            optimization_results['errors'].append(str(e))
            return optimization_results

    async def monitor_query_performance(self, db_path: str, query: str, params: Tuple = None) -> QueryPerformance:
        """Monitor and log query performance."""
        start_time = time.time()
        rows_affected = 0

        try:
            async with aiosqlite.connect(db_path) as db:
                if params:
                    cursor = await db.execute(query, params)
                else:
                    cursor = await db.execute(query)

                rows_affected = cursor.rowcount
                await cursor.close()

            execution_time_ms = (time.time() - start_time) * 1000

            # Create performance record
            performance = QueryPerformance(
                query=query[:200] + '...' if len(query) > 200 else query,  # Truncate long queries
                execution_time_ms=execution_time_ms,
                rows_affected=rows_affected,
                timestamp=datetime.now(),
                optimization_suggestion=self._suggest_query_optimization(query, execution_time_ms)
            )

            # Log performance if it's a slow query
            if execution_time_ms > self.slow_query_threshold_ms:
                await self._log_slow_query(db_path, performance)

            return performance

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Query monitoring failed: {e}")

            return QueryPerformance(
                query=query[:200] + '...' if len(query) > 200 else query,
                execution_time_ms=execution_time_ms,
                rows_affected=0,
                timestamp=datetime.now(),
                optimization_suggestion=f"Query failed: {str(e)}"
            )

    async def _analyze_query_performance(self, db_path: str) -> Dict[str, Any]:
        """Analyze recent query performance from logs."""
        try:
            async with aiosqlite.connect(self.performance_log_path) as db:
                # Get today's query statistics
                async with db.execute("""
                    SELECT
                        COUNT(*) as total_queries,
                        AVG(execution_time_ms) as avg_time_ms,
                        COUNT(CASE WHEN execution_time_ms > ? THEN 1 END) as slow_queries
                    FROM query_performance
                    WHERE database_name = ? AND timestamp > datetime('now', '-1 day')
                """, (self.slow_query_threshold_ms, db_path)) as cursor:
                    row = await cursor.fetchone()

                    if row:
                        return {
                            'total_queries': row[0] or 0,
                            'avg_time_ms': row[1] or 0.0,
                            'slow_queries': row[2] or 0
                        }
                    else:
                        return {'total_queries': 0, 'avg_time_ms': 0.0, 'slow_queries': 0}

        except Exception as e:
            logger.error(f"Query performance analysis failed: {e}")
            return {'total_queries': 0, 'avg_time_ms': 999.0, 'slow_queries': 999}

    async def _analyze_indexes(self, db: aiosqlite.Connection) -> List[IndexAnalysis]:
        """Analyze database indexes for effectiveness."""
        indexes = []

        try:
            # Get all indexes
            async with db.execute("""
                SELECT name, tbl_name, sql FROM sqlite_master
                WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
            """) as cursor:
                index_rows = await cursor.fetchall()

            for index_row in index_rows:
                index_name = index_row[0]
                table_name = index_row[1]

                # Analyze index usage (simplified)
                usage_count = await self._get_index_usage_count(index_name)
                effectiveness_score = min(usage_count / 100.0, 1.0)  # Normalize to 0-1

                # Generate recommendation
                if usage_count < self.index_usage_threshold:
                    recommendation = "Consider dropping - low usage"
                elif effectiveness_score > 0.8:
                    recommendation = "Highly effective - keep"
                else:
                    recommendation = "Moderate effectiveness - review"

                indexes.append(IndexAnalysis(
                    table=table_name,
                    index_name=index_name,
                    columns=[],  # Would parse from SQL in real implementation
                    usage_count=usage_count,
                    last_used=datetime.now() - timedelta(days=1),  # Simplified
                    effectiveness_score=effectiveness_score,
                    recommendation=recommendation
                ))

        except Exception as e:
            logger.error(f"Index analysis failed: {e}")

        return indexes

    async def _calculate_fragmentation(self, db: aiosqlite.Connection) -> float:
        """Calculate database fragmentation ratio."""
        try:
            async with db.execute("PRAGMA freelist_count") as cursor:
                freelist_count = (await cursor.fetchone())[0]

            async with db.execute("PRAGMA page_count") as cursor:
                page_count = (await cursor.fetchone())[0]

            if page_count > 0:
                return freelist_count / page_count
            else:
                return 0.0

        except Exception as e:
            logger.error(f"Fragmentation calculation failed: {e}")
            return 1.0  # Assume worst case on error

    async def _get_cache_statistics(self, db: aiosqlite.Connection) -> Dict[str, float]:
        """Get SQLite cache statistics."""
        try:
            async with db.execute("PRAGMA cache_size") as cursor:
                cache_size = (await cursor.fetchone())[0]

            # Simplified cache hit ratio calculation
            # In a real implementation, this would track actual cache hits/misses
            cache_hit_ratio = 0.85  # Default assumption

            return {
                'cache_size': cache_size,
                'hit_ratio': cache_hit_ratio
            }

        except Exception as e:
            logger.error(f"Cache statistics failed: {e}")
            return {'cache_size': 0, 'hit_ratio': 0.0}

    async def _generate_recommendations(
        self,
        db: aiosqlite.Connection,
        size_mb: float,
        performance_metrics: Dict,
        index_analysis: List[IndexAnalysis],
        fragmentation_ratio: float
    ) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []

        # Size-based recommendations
        if size_mb > 100:
            recommendations.append("Consider archiving old data - database size is large")

        # Performance recommendations
        avg_query_time = performance_metrics.get('avg_time_ms', 0)
        if avg_query_time > 500:
            recommendations.append("High average query time - review query optimization")

        slow_queries = performance_metrics.get('slow_queries', 0)
        if slow_queries > 10:
            recommendations.append(f"{slow_queries} slow queries detected - investigate and optimize")

        # Index recommendations
        unused_indexes = [idx for idx in index_analysis if idx.usage_count < self.index_usage_threshold]
        if unused_indexes:
            recommendations.append(f"Consider dropping {len(unused_indexes)} unused indexes")

        # Fragmentation recommendations
        if fragmentation_ratio > self.fragmentation_threshold:
            recommendations.append("High fragmentation detected - run VACUUM operation")

        # Default recommendation if everything looks good
        if not recommendations:
            recommendations.append("Database health is good - no immediate optimizations needed")

        return recommendations

    async def _update_statistics(self, db: aiosqlite.Connection, results: Dict):
        """Update database statistics."""
        try:
            await db.execute("ANALYZE")
            results['operations'].append("Updated database statistics")
            logger.debug("Database statistics updated")
        except Exception as e:
            results['errors'].append(f"Statistics update failed: {e}")

    async def _optimize_indexes(self, db: aiosqlite.Connection, results: Dict):
        """Optimize database indexes."""
        try:
            # Reindex all indexes
            await db.execute("REINDEX")
            results['operations'].append("Reindexed all database indexes")
            logger.debug("Database indexes optimized")
        except Exception as e:
            results['errors'].append(f"Index optimization failed: {e}")

    async def _vacuum_database(self, db: aiosqlite.Connection, results: Dict):
        """Clean up unused space in database."""
        try:
            await db.execute("VACUUM")
            results['operations'].append("Vacuumed database to reclaim space")
            logger.debug("Database vacuumed")
        except Exception as e:
            results['errors'].append(f"Database vacuum failed: {e}")

    async def _optimize_sqlite_settings(self, db: aiosqlite.Connection, results: Dict):
        """Optimize SQLite configuration settings."""
        try:
            # Set cache size for better performance
            await db.execute(f"PRAGMA cache_size = {self.cache_size_pages}")

            # Enable Write-Ahead Logging for better concurrency
            await db.execute("PRAGMA journal_mode = WAL")

            # Optimize synchronous mode for performance
            await db.execute("PRAGMA synchronous = NORMAL")

            # Use memory for temporary storage
            if self.temp_store_memory:
                await db.execute("PRAGMA temp_store = MEMORY")

            results['operations'].append("Optimized SQLite configuration settings")
            logger.debug("SQLite settings optimized")

        except Exception as e:
            results['errors'].append(f"SQLite optimization failed: {e}")

    async def _analyze_tables(self, db: aiosqlite.Connection, results: Dict):
        """Analyze and optimize table structure."""
        try:
            # Get table statistics
            async with db.execute("""
                SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            """) as cursor:
                tables = await cursor.fetchall()

            for table in tables:
                table_name = table[0]
                await db.execute(f"ANALYZE {table_name}")

            results['operations'].append(f"Analyzed {len(tables)} tables")
            logger.debug(f"Analyzed {len(tables)} database tables")

        except Exception as e:
            results['errors'].append(f"Table analysis failed: {e}")

    async def _get_index_usage_count(self, index_name: str) -> int:
        """Get index usage count from tracking."""
        try:
            async with aiosqlite.connect(self.performance_log_path) as db:
                async with db.execute("""
                    SELECT usage_count FROM index_usage WHERE index_name = ?
                """, (index_name,)) as cursor:
                    row = await cursor.fetchone()
                    return row[0] if row else 0
        except Exception:
            return 0

    async def _get_last_optimization_time(self, db_path: str) -> datetime:
        """Get timestamp of last optimization."""
        try:
            async with aiosqlite.connect(self.performance_log_path) as db:
                async with db.execute("""
                    SELECT MAX(timestamp) FROM optimization_history WHERE database_name = ?
                """, (db_path,)) as cursor:
                    row = await cursor.fetchone()
                    if row and row[0]:
                        return datetime.fromisoformat(row[0])
        except Exception:
            pass

        return datetime.now() - timedelta(days=30)  # Default to 30 days ago

    async def _log_slow_query(self, db_path: str, performance: QueryPerformance):
        """Log slow query for analysis."""
        try:
            async with aiosqlite.connect(self.performance_log_path) as db:
                query_hash = str(hash(performance.query))
                await db.execute("""
                    INSERT INTO query_performance
                    (database_name, query_hash, query_text, execution_time_ms, rows_affected)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    db_path, query_hash, performance.query,
                    performance.execution_time_ms, performance.rows_affected
                ))
                await db.commit()

        except Exception as e:
            logger.error(f"Failed to log slow query: {e}")

    async def _log_optimization_history(self, db_path: str, results: Dict[str, Any]):
        """Log optimization operation to history."""
        try:
            async with aiosqlite.connect(self.performance_log_path) as db:
                await db.execute("""
                    INSERT INTO optimization_history
                    (database_name, optimization_type, description, improvement_ratio)
                    VALUES (?, ?, ?, ?)
                """, (
                    db_path,
                    "full_optimization",
                    f"Operations: {', '.join(results['operations'])}",
                    results.get('improvements', {}).get('query_time_improvement_ms', 0)
                ))
                await db.commit()

        except Exception as e:
            logger.error(f"Failed to log optimization history: {e}")

    def _suggest_query_optimization(self, query: str, execution_time_ms: float) -> Optional[str]:
        """Suggest query optimization based on analysis."""
        query_lower = query.lower()

        if execution_time_ms > 2000:
            if 'where' not in query_lower:
                return "Consider adding WHERE clause to filter results"
            elif 'order by' in query_lower and 'limit' not in query_lower:
                return "Consider adding LIMIT clause with ORDER BY"
            elif 'join' in query_lower:
                return "Review JOIN conditions and ensure proper indexing"
            else:
                return "Consider adding appropriate indexes for this query"
        elif execution_time_ms > 1000:
            return "Monitor this query - approaching slow query threshold"

        return None

# Global optimizer instance
_database_optimizer = None

def get_database_optimizer() -> DatabaseOptimizer:
    """Get singleton database optimizer instance."""
    global _database_optimizer
    if _database_optimizer is None:
        _database_optimizer = DatabaseOptimizer()
    return _database_optimizer