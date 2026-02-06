"""
Advanced Query Performance Monitoring System.

Comprehensive monitoring for:
- Real-time query performance tracking
- Slow query detection and alerting
- Query plan analysis and optimization suggestions
- Performance trend analysis
- Automated optimization recommendations
"""

import asyncio
import logging
import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager
from collections import defaultdict, deque
import statistics

from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.engine import Engine
from sqlalchemy.sql import ClauseElement

logger = logging.getLogger(__name__)

@dataclass
class QueryExecutionMetrics:
    """Detailed metrics for a single query execution."""
    query_hash: str
    query_text: str
    execution_time_ms: float
    rows_examined: int
    rows_returned: int
    connection_id: str
    timestamp: datetime
    execution_plan: Optional[Dict[str, Any]] = None
    parameters: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    table_scans: int = 0
    index_scans: int = 0
    joins: int = 0
    sorts: int = 0
    memory_usage_kb: Optional[float] = None

@dataclass
class QueryPattern:
    """Aggregated metrics for a query pattern."""
    query_hash: str
    query_template: str
    execution_count: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    total_rows_examined: int
    total_rows_returned: int
    error_count: int
    last_execution: datetime
    first_execution: datetime
    tables_accessed: Set[str]
    optimization_opportunities: List[str]

@dataclass
class PerformanceAlert:
    """Performance alert data."""
    alert_type: str
    severity: str  # low, medium, high, critical
    query_hash: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False

class QueryPerformanceMonitor:
    """Advanced query performance monitoring and analysis."""

    def __init__(
        self,
        engine: AsyncEngine,
        slow_query_threshold_ms: float = 100,
        enable_query_plans: bool = True,
        enable_real_time_monitoring: bool = True,
        retention_hours: int = 24,
        alert_thresholds: Optional[Dict[str, float]] = None
    ):
        self.engine = engine
        self.slow_query_threshold_ms = slow_query_threshold_ms
        self.enable_query_plans = enable_query_plans
        self.enable_real_time_monitoring = enable_real_time_monitoring
        self.retention_hours = retention_hours

        # Alert thresholds
        self.alert_thresholds = alert_thresholds or {
            'avg_query_time_ms': 200,
            'slow_query_percentage': 10.0,
            'error_rate_percentage': 1.0,
            'high_scan_ratio': 0.8,  # table_scans / total_operations
            'memory_usage_mb': 100
        }

        # Data storage
        self.query_metrics: deque = deque(maxlen=50000)  # Last 50k queries
        self.query_patterns: Dict[str, QueryPattern] = {}
        self.alerts: List[PerformanceAlert] = []

        # Real-time tracking
        self.active_queries: Dict[str, QueryExecutionMetrics] = {}
        self.performance_trends: Dict[str, deque] = {
            'avg_response_time': deque(maxlen=1440),  # 24 hours of minutes
            'queries_per_minute': deque(maxlen=1440),
            'slow_queries_per_minute': deque(maxlen=1440),
            'error_rate_per_minute': deque(maxlen=1440)
        }

        # Background tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        self._stop_monitoring = False

    async def start_monitoring(self):
        """Start the query performance monitoring system."""
        # Set up SQLAlchemy event listeners
        self._setup_engine_events()

        # Start background tasks
        if self.enable_real_time_monitoring:
            self.monitoring_tasks.extend([
                asyncio.create_task(self._trend_aggregation_task()),
                asyncio.create_task(self._alert_monitoring_task()),
                asyncio.create_task(self._cleanup_task())
            ])

        logger.info("Query performance monitoring started")

    async def stop_monitoring(self):
        """Stop monitoring and cleanup resources."""
        self._stop_monitoring = True

        # Cancel background tasks
        for task in self.monitoring_tasks:
            task.cancel()

        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        logger.info("Query performance monitoring stopped")

    def _setup_engine_events(self):
        """Set up SQLAlchemy engine event listeners."""

        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Track query start time."""
            context._query_start_time = time.perf_counter()
            context._query_statement = statement
            context._query_parameters = parameters

        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Track query completion and record metrics."""
            if hasattr(context, '_query_start_time'):
                execution_time = (time.perf_counter() - context._query_start_time) * 1000

                # Create metrics record
                asyncio.create_task(self._record_query_execution(
                    statement=statement,
                    parameters=parameters,
                    execution_time_ms=execution_time,
                    rows_affected=cursor.rowcount,
                    connection_id=str(id(conn))
                ))

        @event.listens_for(Engine, "handle_error")
        def receive_handle_error(exception_context):
            """Track query errors."""
            if hasattr(exception_context.execution_context, '_query_start_time'):
                execution_time = (time.perf_counter() - exception_context.execution_context._query_start_time) * 1000

                asyncio.create_task(self._record_query_execution(
                    statement=exception_context.statement,
                    parameters=exception_context.parameters,
                    execution_time_ms=execution_time,
                    rows_affected=0,
                    connection_id=str(id(exception_context.connection)),
                    error=str(exception_context.original_exception)
                ))

    async def _record_query_execution(
        self,
        statement: str,
        parameters: Optional[Dict[str, Any]],
        execution_time_ms: float,
        rows_affected: int,
        connection_id: str,
        error: Optional[str] = None
    ):
        """Record query execution metrics."""
        try:
            # Normalize query for pattern matching
            query_hash = self._hash_query(statement)
            normalized_query = self._normalize_query(statement)

            # Create execution metrics
            metrics = QueryExecutionMetrics(
                query_hash=query_hash,
                query_text=statement[:1000],  # Truncate long queries
                execution_time_ms=execution_time_ms,
                rows_examined=rows_affected,  # Approximation
                rows_returned=rows_affected,
                connection_id=connection_id,
                timestamp=datetime.utcnow(),
                parameters=self._sanitize_parameters(parameters),
                error=error
            )

            # Get execution plan for slow queries
            if (execution_time_ms > self.slow_query_threshold_ms and
                self.enable_query_plans and
                not error):
                metrics.execution_plan = await self._get_query_plan(statement, parameters)
                metrics.table_scans, metrics.index_scans, metrics.joins, metrics.sorts = \
                    self._analyze_execution_plan(metrics.execution_plan)

            # Store metrics
            self.query_metrics.append(metrics)

            # Update query patterns
            await self._update_query_pattern(metrics, normalized_query)

            # Check for alerts
            await self._check_performance_alerts(metrics)

        except Exception as e:
            logger.error(f"Error recording query metrics: {e}")

    def _hash_query(self, query: str) -> str:
        """Generate hash for query pattern matching."""
        # Normalize and hash the query
        normalized = self._normalize_query(query)
        return hashlib.md5(normalized.encode()).hexdigest()[:12]

    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern matching."""
        # Remove literals and normalize whitespace
        import re

        # Replace string literals
        query = re.sub(r"'[^']*'", "'?'", query)

        # Replace numeric literals
        query = re.sub(r'\b\d+\b', '?', query)

        # Replace UUID patterns
        query = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '?', query, flags=re.IGNORECASE)

        # Normalize whitespace
        query = ' '.join(query.split())

        return query.lower()

    def _sanitize_parameters(self, parameters: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Sanitize query parameters for storage."""
        if not parameters:
            return None

        sanitized = {}
        for key, value in parameters.items():
            if isinstance(value, (str, int, float, bool)):
                # Truncate long strings
                if isinstance(value, str) and len(value) > 100:
                    sanitized[key] = f"{value[:97]}..."
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = str(type(value))

        return sanitized

    async def _get_query_plan(self, statement: str, parameters: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get query execution plan."""
        try:
            async with self.engine.begin() as conn:
                # Use EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) for detailed plan
                explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {statement}"

                result = await conn.execute(text(explain_query), parameters or {})
                plan_data = result.fetchone()

                if plan_data and plan_data[0]:
                    return plan_data[0][0] if isinstance(plan_data[0], list) else plan_data[0]

        except Exception as e:
            logger.debug(f"Could not get execution plan: {e}")

        return None

    def _analyze_execution_plan(self, plan: Optional[Dict[str, Any]]) -> Tuple[int, int, int, int]:
        """Analyze execution plan to extract key metrics."""
        if not plan:
            return 0, 0, 0, 0

        table_scans = 0
        index_scans = 0
        joins = 0
        sorts = 0

        def traverse_plan(node):
            nonlocal table_scans, index_scans, joins, sorts

            node_type = node.get('Node Type', '').lower()

            if 'seq scan' in node_type:
                table_scans += 1
            elif 'index' in node_type:
                index_scans += 1
            elif 'join' in node_type:
                joins += 1
            elif 'sort' in node_type:
                sorts += 1

            # Traverse child plans
            for child in node.get('Plans', []):
                traverse_plan(child)

        traverse_plan(plan.get('Plan', {}))
        return table_scans, index_scans, joins, sorts

    async def _update_query_pattern(self, metrics: QueryExecutionMetrics, normalized_query: str):
        """Update aggregated query pattern statistics."""
        query_hash = metrics.query_hash

        if query_hash not in self.query_patterns:
            # Create new pattern
            self.query_patterns[query_hash] = QueryPattern(
                query_hash=query_hash,
                query_template=normalized_query,
                execution_count=0,
                total_time_ms=0.0,
                avg_time_ms=0.0,
                min_time_ms=float('inf'),
                max_time_ms=0.0,
                p95_time_ms=0.0,
                p99_time_ms=0.0,
                total_rows_examined=0,
                total_rows_returned=0,
                error_count=0,
                first_execution=metrics.timestamp,
                last_execution=metrics.timestamp,
                tables_accessed=set(),
                optimization_opportunities=[]
            )

        pattern = self.query_patterns[query_hash]

        # Update basic stats
        pattern.execution_count += 1
        pattern.total_time_ms += metrics.execution_time_ms
        pattern.avg_time_ms = pattern.total_time_ms / pattern.execution_count
        pattern.min_time_ms = min(pattern.min_time_ms, metrics.execution_time_ms)
        pattern.max_time_ms = max(pattern.max_time_ms, metrics.execution_time_ms)
        pattern.total_rows_examined += metrics.rows_examined
        pattern.total_rows_returned += metrics.rows_returned
        pattern.last_execution = metrics.timestamp

        if metrics.error:
            pattern.error_count += 1

        # Update percentiles (simplified calculation)
        if pattern.execution_count >= 10:
            recent_times = [
                m.execution_time_ms for m in list(self.query_metrics)[-100:]
                if m.query_hash == query_hash
            ]
            if recent_times:
                pattern.p95_time_ms = statistics.quantiles(recent_times, n=20)[18]  # 95th percentile
                pattern.p99_time_ms = statistics.quantiles(recent_times, n=100)[98]  # 99th percentile

        # Extract table names from query
        pattern.tables_accessed.update(self._extract_table_names(metrics.query_text))

        # Generate optimization opportunities
        pattern.optimization_opportunities = self._generate_optimization_suggestions(pattern, metrics)

    def _extract_table_names(self, query: str) -> Set[str]:
        """Extract table names from SQL query."""
        import re

        # Simple regex to find table names after FROM and JOIN
        table_pattern = r'(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        matches = re.findall(table_pattern, query, re.IGNORECASE)

        return set(matches)

    def _generate_optimization_suggestions(self, pattern: QueryPattern, metrics: QueryExecutionMetrics) -> List[str]:
        """Generate optimization suggestions for query pattern."""
        suggestions = []

        # Slow query suggestions
        if pattern.avg_time_ms > self.slow_query_threshold_ms:
            suggestions.append("Query is consistently slow - consider optimization")

        # High table scan ratio
        if metrics.table_scans > metrics.index_scans and metrics.index_scans > 0:
            suggestions.append("High table scan ratio - missing indexes may improve performance")

        # High row examination ratio
        if metrics.rows_examined > metrics.rows_returned * 10:
            suggestions.append("High row examination ratio - query may benefit from better filtering")

        # Multiple joins
        if metrics.joins > 3:
            suggestions.append("Complex joins detected - consider query restructuring or materialized views")

        # Frequent sorts
        if metrics.sorts > 1:
            suggestions.append("Multiple sorts in query - indexes on ORDER BY columns may help")

        # High execution frequency with slow performance
        if pattern.execution_count > 100 and pattern.avg_time_ms > 50:
            suggestions.append("Frequently executed slow query - high impact optimization opportunity")

        return suggestions

    async def _check_performance_alerts(self, metrics: QueryExecutionMetrics):
        """Check for performance alerts based on metrics."""
        alerts_to_create = []

        # Slow query alert
        if metrics.execution_time_ms > self.alert_thresholds['avg_query_time_ms']:
            alerts_to_create.append(PerformanceAlert(
                alert_type="slow_query",
                severity="high" if metrics.execution_time_ms > 1000 else "medium",
                query_hash=metrics.query_hash,
                message=f"Slow query detected: {metrics.execution_time_ms:.2f}ms",
                details={
                    "execution_time_ms": metrics.execution_time_ms,
                    "query_preview": metrics.query_text[:200],
                    "connection_id": metrics.connection_id
                },
                timestamp=datetime.utcnow()
            ))

        # High table scan alert
        total_operations = metrics.table_scans + metrics.index_scans
        if total_operations > 0 and metrics.table_scans / total_operations > self.alert_thresholds['high_scan_ratio']:
            alerts_to_create.append(PerformanceAlert(
                alert_type="high_table_scans",
                severity="medium",
                query_hash=metrics.query_hash,
                message=f"High table scan ratio: {metrics.table_scans}/{total_operations}",
                details={
                    "table_scans": metrics.table_scans,
                    "index_scans": metrics.index_scans,
                    "query_preview": metrics.query_text[:200]
                },
                timestamp=datetime.utcnow()
            ))

        # Query error alert
        if metrics.error:
            alerts_to_create.append(PerformanceAlert(
                alert_type="query_error",
                severity="high",
                query_hash=metrics.query_hash,
                message=f"Query execution error: {metrics.error}",
                details={
                    "error": metrics.error,
                    "query_preview": metrics.query_text[:200],
                    "execution_time_ms": metrics.execution_time_ms
                },
                timestamp=datetime.utcnow()
            ))

        # Add alerts
        self.alerts.extend(alerts_to_create)

        # Keep only recent alerts (last 1000)
        if len(self.alerts) > 1000:
            self.alerts = self.alerts[-1000:]

    async def _trend_aggregation_task(self):
        """Background task to aggregate performance trends."""
        while not self._stop_monitoring:
            try:
                await asyncio.sleep(60)  # Run every minute

                # Calculate metrics for the last minute
                now = datetime.utcnow()
                one_minute_ago = now - timedelta(minutes=1)

                recent_queries = [
                    m for m in self.query_metrics
                    if m.timestamp >= one_minute_ago
                ]

                if recent_queries:
                    avg_response_time = sum(q.execution_time_ms for q in recent_queries) / len(recent_queries)
                    slow_queries = [q for q in recent_queries if q.execution_time_ms > self.slow_query_threshold_ms]
                    error_queries = [q for q in recent_queries if q.error]

                    self.performance_trends['avg_response_time'].append(avg_response_time)
                    self.performance_trends['queries_per_minute'].append(len(recent_queries))
                    self.performance_trends['slow_queries_per_minute'].append(len(slow_queries))
                    self.performance_trends['error_rate_per_minute'].append(len(error_queries))

            except Exception as e:
                logger.error(f"Error in trend aggregation: {e}")

    async def _alert_monitoring_task(self):
        """Background task to monitor for system-wide performance alerts."""
        while not self._stop_monitoring:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes

                # System-wide metrics
                if self.performance_trends['avg_response_time']:
                    recent_avg = statistics.mean(list(self.performance_trends['avg_response_time'])[-10:])

                    if recent_avg > self.alert_thresholds['avg_query_time_ms']:
                        self.alerts.append(PerformanceAlert(
                            alert_type="system_performance",
                            severity="high",
                            query_hash="system_wide",
                            message=f"System-wide performance degradation: {recent_avg:.2f}ms avg response time",
                            details={"avg_response_time_ms": recent_avg},
                            timestamp=datetime.utcnow()
                        ))

                # Error rate monitoring
                if self.performance_trends['error_rate_per_minute'] and self.performance_trends['queries_per_minute']:
                    recent_errors = sum(list(self.performance_trends['error_rate_per_minute'])[-10:])
                    recent_queries = sum(list(self.performance_trends['queries_per_minute'])[-10:])

                    if recent_queries > 0:
                        error_rate = (recent_errors / recent_queries) * 100

                        if error_rate > self.alert_thresholds['error_rate_percentage']:
                            self.alerts.append(PerformanceAlert(
                                alert_type="high_error_rate",
                                severity="critical",
                                query_hash="system_wide",
                                message=f"High error rate detected: {error_rate:.2f}%",
                                details={"error_rate_percentage": error_rate},
                                timestamp=datetime.utcnow()
                            ))

            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")

    async def _cleanup_task(self):
        """Background task to cleanup old data."""
        while not self._stop_monitoring:
            try:
                await asyncio.sleep(3600)  # Run every hour

                cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)

                # Cleanup old query metrics
                original_count = len(self.query_metrics)
                self.query_metrics = deque([
                    m for m in self.query_metrics
                    if m.timestamp >= cutoff_time
                ], maxlen=50000)

                # Cleanup old alerts
                self.alerts = [
                    a for a in self.alerts
                    if a.timestamp >= cutoff_time
                ]

                cleaned_count = original_count - len(self.query_metrics)
                if cleaned_count > 0:
                    logger.info(f"Cleaned up {cleaned_count} old query metrics")

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    async def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get slowest query patterns."""
        # Sort patterns by average execution time
        sorted_patterns = sorted(
            self.query_patterns.values(),
            key=lambda p: p.avg_time_ms,
            reverse=True
        )

        return [
            {
                "query_hash": pattern.query_hash,
                "query_template": pattern.query_template,
                "avg_time_ms": pattern.avg_time_ms,
                "execution_count": pattern.execution_count,
                "total_time_ms": pattern.total_time_ms,
                "p95_time_ms": pattern.p95_time_ms,
                "error_count": pattern.error_count,
                "tables_accessed": list(pattern.tables_accessed),
                "optimization_opportunities": pattern.optimization_opportunities
            }
            for pattern in sorted_patterns[:limit]
        ]

    async def get_performance_dashboard_data(self) -> Dict[str, Any]:
        """Get data for performance monitoring dashboard."""
        # Calculate summary metrics
        if self.query_metrics:
            recent_queries = list(self.query_metrics)[-1000:]  # Last 1000 queries
            avg_response_time = sum(q.execution_time_ms for q in recent_queries) / len(recent_queries)
            slow_queries = [q for q in recent_queries if q.execution_time_ms > self.slow_query_threshold_ms]
            error_queries = [q for q in recent_queries if q.error]

            slow_query_percentage = (len(slow_queries) / len(recent_queries)) * 100
            error_percentage = (len(error_queries) / len(recent_queries)) * 100
        else:
            avg_response_time = 0
            slow_query_percentage = 0
            error_percentage = 0

        # Get top slow queries
        slow_queries_data = await self.get_slow_queries(10)

        # Get recent alerts
        recent_alerts = sorted(
            [a for a in self.alerts if not a.resolved],
            key=lambda a: a.timestamp,
            reverse=True
        )[:20]

        return {
            "summary": {
                "avg_response_time_ms": avg_response_time,
                "slow_query_percentage": slow_query_percentage,
                "error_percentage": error_percentage,
                "total_queries_monitored": len(self.query_metrics),
                "unique_query_patterns": len(self.query_patterns),
                "active_alerts": len([a for a in self.alerts if not a.resolved])
            },
            "trends": {
                "avg_response_time": list(self.performance_trends['avg_response_time'])[-60:],  # Last hour
                "queries_per_minute": list(self.performance_trends['queries_per_minute'])[-60:],
                "slow_queries_per_minute": list(self.performance_trends['slow_queries_per_minute'])[-60:],
                "error_rate_per_minute": list(self.performance_trends['error_rate_per_minute'])[-60:]
            },
            "slow_queries": slow_queries_data,
            "recent_alerts": [
                {
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "details": alert.details
                }
                for alert in recent_alerts
            ],
            "timestamp": datetime.utcnow().isoformat()
        }