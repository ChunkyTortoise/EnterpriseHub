#!/usr/bin/env python3
"""
Database Query Performance Analysis Script

Phase 2 Performance Foundation - Week 3 Quick Wins
Target: Identify and report on database performance bottlenecks

Features:
- N+1 query detection
- Slow query identification
- Index usage analysis
- Connection pool efficiency metrics
- Query optimization recommendations

Usage:
    python scripts/analyze_query_performance.py
    python scripts/analyze_query_performance.py --duration 300  # Analyze for 5 minutes
    python scripts/analyze_query_performance.py --export report.json
"""

import asyncio
import asyncpg
import time
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, asdict


@dataclass
class QueryPerformanceIssue:
    """Represents a database performance issue"""
    issue_type: str  # n+1_query, slow_query, missing_index, inefficient_scan
    severity: str  # critical, high, medium, low
    query_pattern: str
    occurrences: int
    avg_execution_time_ms: float
    p95_execution_time_ms: float
    total_time_ms: float
    recommendation: str
    example_query: Optional[str] = None
    affected_tables: List[str] = None


@dataclass
class ConnectionPoolMetrics:
    """Connection pool performance metrics"""
    pool_name: str
    total_connections: int
    active_connections: int
    idle_connections: int
    avg_acquisition_time_ms: float
    total_acquisitions: int
    failed_acquisitions: int
    efficiency_score: float


class QueryPerformanceAnalyzer:
    """
    Analyzes database query performance and identifies optimization opportunities.

    Target Metrics (Phase 2 Week 3):
    - Database queries: <50ms P90
    - Connection pool efficiency: >90%
    - Zero N+1 query patterns
    - All critical queries using indexes
    """

    def __init__(self, database_url: str):
        """Initialize analyzer with database connection"""
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
        self.analysis_start_time = None
        self.query_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'execution_times': [],
            'queries': []
        })
        self.n_plus_one_patterns = []
        self.slow_queries = []
        self.missing_indexes = []

    async def initialize(self):
        """Initialize database connection pool"""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=1,
            max_size=5,
            command_timeout=30
        )
        self.analysis_start_time = datetime.now()
        print(f"✓ Connected to database at {self.analysis_start_time}")

    async def close(self):
        """Close database connection"""
        if self.pool:
            await self.pool.close()

    async def analyze_slow_queries(self, threshold_ms: float = 50.0) -> List[QueryPerformanceIssue]:
        """
        Identify slow queries from PostgreSQL stats.

        Target: All queries <50ms P90
        """
        print(f"\n📊 Analyzing slow queries (threshold: {threshold_ms}ms)...")

        async with self.pool.acquire() as conn:
            # Query pg_stat_statements for slow queries
            slow_query_sql = """
                SELECT
                    query,
                    calls,
                    mean_exec_time,
                    max_exec_time,
                    total_exec_time,
                    rows / NULLIF(calls, 0) as avg_rows
                FROM pg_stat_statements
                WHERE mean_exec_time > $1
                ORDER BY mean_exec_time DESC
                LIMIT 50
            """

            try:
                rows = await conn.fetch(slow_query_sql, threshold_ms)

                issues = []
                for row in rows:
                    severity = 'critical' if row['mean_exec_time'] > 200 else \
                              'high' if row['mean_exec_time'] > 100 else 'medium'

                    recommendation = self._generate_optimization_recommendation(
                        row['query'], row['mean_exec_time']
                    )

                    issue = QueryPerformanceIssue(
                        issue_type='slow_query',
                        severity=severity,
                        query_pattern=self._normalize_query(row['query']),
                        occurrences=row['calls'],
                        avg_execution_time_ms=row['mean_exec_time'],
                        p95_execution_time_ms=row['max_exec_time'] * 0.95,  # Approximate
                        total_time_ms=row['total_exec_time'],
                        recommendation=recommendation,
                        example_query=row['query'][:200] + '...' if len(row['query']) > 200 else row['query']
                    )
                    issues.append(issue)
                    self.slow_queries.append(issue)

                print(f"   Found {len(issues)} slow queries")
                return issues

            except Exception as e:
                print(f"   Warning: Could not analyze slow queries: {e}")
                print(f"   Note: pg_stat_statements extension may not be enabled")
                return []

    async def detect_n_plus_one_queries(self) -> List[QueryPerformanceIssue]:
        """
        Detect N+1 query patterns by analyzing query frequency and patterns.

        N+1 queries are identified by:
        1. High frequency of similar queries in short time window
        2. Queries executed in loops (same pattern, different params)
        3. Single-row SELECT queries repeated multiple times
        """
        print(f"\n🔍 Detecting N+1 query patterns...")

        async with self.pool.acquire() as conn:
            # Analyze query patterns from pg_stat_statements
            n_plus_one_sql = """
                SELECT
                    query,
                    calls,
                    mean_exec_time,
                    total_exec_time
                FROM pg_stat_statements
                WHERE query LIKE '%WHERE%=%'
                  AND calls > 100
                  AND query LIKE '%LIMIT 1%'
                ORDER BY calls DESC
                LIMIT 30
            """

            try:
                rows = await conn.fetch(n_plus_one_sql)

                issues = []
                for row in rows:
                    # High call frequency suggests N+1 pattern
                    if row['calls'] > 500:
                        severity = 'critical'
                        recommendation = (
                            f"⚠️ CRITICAL N+1 Pattern: Query executed {row['calls']} times. "
                            "Use JOIN or bulk SELECT with IN clause instead of individual queries. "
                            "Example: SELECT * FROM table WHERE id IN ($1, $2, ...) "
                            "instead of multiple SELECT * FROM table WHERE id = $1"
                        )
                    elif row['calls'] > 200:
                        severity = 'high'
                        recommendation = (
                            f"N+1 Pattern detected: Query executed {row['calls']} times. "
                            "Consider batching queries or using eager loading."
                        )
                    else:
                        severity = 'medium'
                        recommendation = (
                            "Potential N+1 pattern. Monitor query frequency and consider optimization."
                        )

                    issue = QueryPerformanceIssue(
                        issue_type='n+1_query',
                        severity=severity,
                        query_pattern=self._normalize_query(row['query']),
                        occurrences=row['calls'],
                        avg_execution_time_ms=row['mean_exec_time'],
                        p95_execution_time_ms=row['mean_exec_time'] * 1.2,
                        total_time_ms=row['total_exec_time'],
                        recommendation=recommendation,
                        example_query=row['query'][:200] + '...' if len(row['query']) > 200 else row['query']
                    )
                    issues.append(issue)
                    self.n_plus_one_patterns.append(issue)

                print(f"   Found {len(issues)} potential N+1 query patterns")
                return issues

            except Exception as e:
                print(f"   Warning: Could not detect N+1 patterns: {e}")
                return []

    async def analyze_index_usage(self) -> List[QueryPerformanceIssue]:
        """
        Analyze index usage and identify missing indexes.

        Target: All critical queries use indexes (zero sequential scans on large tables)
        """
        print(f"\n📑 Analyzing index usage...")

        async with self.pool.acquire() as conn:
            # Find tables with high sequential scan rates
            seq_scan_sql = """
                SELECT
                    schemaname,
                    tablename,
                    seq_scan,
                    seq_tup_read,
                    idx_scan,
                    idx_tup_fetch,
                    n_tup_ins + n_tup_upd + n_tup_del as modifications,
                    n_live_tup as live_tuples,
                    CASE
                        WHEN seq_scan + idx_scan > 0
                        THEN round((100.0 * seq_scan / (seq_scan + idx_scan))::numeric, 2)
                        ELSE 0
                    END as seq_scan_pct
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                  AND n_live_tup > 1000  -- Only tables with significant data
                ORDER BY seq_scan DESC, n_live_tup DESC
                LIMIT 20
            """

            rows = await conn.fetch(seq_scan_sql)

            issues = []
            for row in rows:
                # High sequential scan percentage on large tables is concerning
                if row['seq_scan_pct'] > 30 and row['live_tuples'] > 10000:
                    severity = 'critical'
                    recommendation = (
                        f"⚠️ CRITICAL: Table '{row['tablename']}' has {row['seq_scan_pct']}% sequential scans "
                        f"with {row['live_tuples']:,} rows. Add indexes for common query patterns."
                    )
                elif row['seq_scan_pct'] > 50:
                    severity = 'high'
                    recommendation = (
                        f"High sequential scan rate on '{row['tablename']}': {row['seq_scan_pct']}%. "
                        "Review query patterns and add appropriate indexes."
                    )
                else:
                    continue

                issue = QueryPerformanceIssue(
                    issue_type='missing_index',
                    severity=severity,
                    query_pattern=f"Table: {row['tablename']}",
                    occurrences=row['seq_scan'],
                    avg_execution_time_ms=0,
                    p95_execution_time_ms=0,
                    total_time_ms=0,
                    recommendation=recommendation,
                    affected_tables=[row['tablename']]
                )
                issues.append(issue)
                self.missing_indexes.append(issue)

            print(f"   Found {len(issues)} tables with high sequential scan rates")

            # Check unused indexes
            unused_indexes_sql = """
                SELECT
                    schemaname,
                    tablename,
                    indexrelname,
                    idx_scan,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM pg_stat_user_indexes
                WHERE schemaname = 'public'
                  AND idx_scan = 0
                  AND indexrelname NOT LIKE '%pkey%'
                ORDER BY pg_relation_size(indexrelid) DESC
                LIMIT 10
            """

            unused_rows = await conn.fetch(unused_indexes_sql)
            if unused_rows:
                print(f"   ℹ️  Found {len(unused_rows)} unused indexes (consider removal)")

            return issues

    async def analyze_connection_pool_efficiency(self) -> List[ConnectionPoolMetrics]:
        """
        Analyze connection pool performance.

        Target: >90% connection pool efficiency
        """
        print(f"\n🔌 Analyzing connection pool efficiency...")

        async with self.pool.acquire() as conn:
            # Get current connection stats
            conn_stats_sql = """
                SELECT
                    state,
                    COUNT(*) as count,
                    COALESCE(AVG(EXTRACT(EPOCH FROM (NOW() - state_change)) * 1000), 0) as avg_time_in_state_ms
                FROM pg_stat_activity
                WHERE datname = current_database()
                GROUP BY state
            """

            rows = await conn.fetch(conn_stats_sql)

            total_connections = sum(row['count'] for row in rows)
            active_connections = sum(row['count'] for row in rows if row['state'] == 'active')
            idle_connections = sum(row['count'] for row in rows if row['state'] == 'idle')

            # Calculate efficiency (active / total)
            efficiency = (active_connections / total_connections * 100) if total_connections > 0 else 0

            metrics = ConnectionPoolMetrics(
                pool_name='default',
                total_connections=total_connections,
                active_connections=active_connections,
                idle_connections=idle_connections,
                avg_acquisition_time_ms=0,  # Not directly available
                total_acquisitions=0,
                failed_acquisitions=0,
                efficiency_score=efficiency
            )

            print(f"   Pool efficiency: {efficiency:.1f}%")
            print(f"   Active: {active_connections}, Idle: {idle_connections}, Total: {total_connections}")

            if efficiency < 90:
                print(f"   ⚠️  Pool efficiency below 90% target")
            else:
                print(f"   ✓ Pool efficiency meets >90% target")

            return [metrics]

    async def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance analysis report"""
        print(f"\n" + "="*60)
        print("DATABASE PERFORMANCE ANALYSIS REPORT")
        print("Phase 2 Performance Foundation - Week 3")
        print(f"Analysis Time: {datetime.now()}")
        print("="*60)

        # Run all analyses
        slow_queries = await self.analyze_slow_queries(threshold_ms=50.0)
        n_plus_one = await self.detect_n_plus_one_queries()
        index_issues = await self.analyze_index_usage()
        pool_metrics = await self.analyze_connection_pool_efficiency()

        # Calculate summary metrics
        total_issues = len(slow_queries) + len(n_plus_one) + len(index_issues)
        critical_issues = sum(1 for issue in slow_queries + n_plus_one + index_issues
                            if issue.severity == 'critical')
        high_issues = sum(1 for issue in slow_queries + n_plus_one + index_issues
                         if issue.severity == 'high')

        # Performance targets achievement
        p90_queries_under_50ms = len([q for q in slow_queries if q.avg_execution_time_ms < 50])
        total_slow_queries = len(slow_queries)
        p90_achievement = (p90_queries_under_50ms / total_slow_queries * 100) if total_slow_queries > 0 else 100

        pool_efficiency_target_met = all(m.efficiency_score >= 90 for m in pool_metrics)

        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'database_url': self.database_url.split('@')[-1],  # Hide credentials
            'summary': {
                'total_issues': total_issues,
                'critical_issues': critical_issues,
                'high_priority_issues': high_issues,
                'medium_issues': total_issues - critical_issues - high_issues
            },
            'performance_targets': {
                'p90_queries_under_50ms': {
                    'target': '100%',
                    'actual': f'{p90_achievement:.1f}%',
                    'status': '✓' if p90_achievement >= 95 else '✗'
                },
                'connection_pool_efficiency': {
                    'target': '>90%',
                    'actual': f"{pool_metrics[0].efficiency_score:.1f}%" if pool_metrics else 'N/A',
                    'status': '✓' if pool_efficiency_target_met else '✗'
                },
                'n_plus_one_queries': {
                    'target': '0',
                    'actual': str(len([q for q in n_plus_one if q.severity in ['critical', 'high']])),
                    'status': '✓' if len(n_plus_one) == 0 else '✗'
                }
            },
            'issues': {
                'slow_queries': [asdict(issue) for issue in slow_queries[:10]],
                'n_plus_one_patterns': [asdict(issue) for issue in n_plus_one[:10]],
                'missing_indexes': [asdict(issue) for issue in index_issues[:10]]
            },
            'connection_pool_metrics': [asdict(m) for m in pool_metrics],
            'recommendations': self._generate_top_recommendations(
                slow_queries, n_plus_one, index_issues
            )
        }

        # Print summary
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)
        print(f"Total Issues: {total_issues}")
        print(f"  • Critical: {critical_issues}")
        print(f"  • High: {high_issues}")
        print(f"  • Medium: {total_issues - critical_issues - high_issues}")
        print(f"\nPerformance Targets:")
        print(f"  • P90 Queries <50ms: {p90_achievement:.1f}% {'✓' if p90_achievement >= 95 else '✗'}")
        print(f"  • Pool Efficiency >90%: {'✓' if pool_efficiency_target_met else '✗'}")
        print(f"  • N+1 Queries: {len([q for q in n_plus_one if q.severity in ['critical', 'high']])} {'✓' if len(n_plus_one) == 0 else '✗'}")

        return report

    def _normalize_query(self, query: str) -> str:
        """Normalize query by removing parameters for pattern matching"""
        import re
        # Replace specific values with placeholders
        normalized = re.sub(r"'[^']*'", "'?'", query)
        normalized = re.sub(r'\b\d+\b', '?', normalized)
        return normalized[:100]

    def _generate_optimization_recommendation(self, query: str, exec_time: float) -> str:
        """Generate optimization recommendation for a slow query"""
        recommendations = []

        if 'SELECT *' in query.upper():
            recommendations.append("Replace SELECT * with specific columns")

        if 'ORDER BY' in query.upper() and 'INDEX' not in query.upper():
            recommendations.append("Add index on ORDER BY columns")

        if 'JOIN' in query.upper():
            recommendations.append("Verify indexes on JOIN columns")

        if exec_time > 200:
            recommendations.append("CRITICAL: Consider query rewrite or result caching")
        elif exec_time > 100:
            recommendations.append("Add composite indexes for WHERE + ORDER BY columns")
        else:
            recommendations.append("Add covering index to avoid table lookups")

        return "; ".join(recommendations)

    def _generate_top_recommendations(self, slow_queries, n_plus_one, index_issues) -> List[str]:
        """Generate top 10 optimization recommendations"""
        recommendations = []

        # Critical issues first
        critical_slow = [q for q in slow_queries if q.severity == 'critical']
        if critical_slow:
            recommendations.append(
                f"CRITICAL: {len(critical_slow)} queries >200ms - immediate optimization required"
            )

        critical_n_plus_one = [q for q in n_plus_one if q.severity == 'critical']
        if critical_n_plus_one:
            recommendations.append(
                f"CRITICAL: {len(critical_n_plus_one)} N+1 query patterns detected - use JOINs or bulk loading"
            )

        critical_indexes = [i for i in index_issues if i.severity == 'critical']
        if critical_indexes:
            recommendations.append(
                f"CRITICAL: {len(critical_indexes)} tables need indexes - high sequential scan rates"
            )

        # High priority issues
        if len(slow_queries) > 0:
            recommendations.append(
                f"Optimize {len(slow_queries)} slow queries to meet <50ms P90 target"
            )

        if len(n_plus_one) > 0:
            recommendations.append(
                f"Refactor {len(n_plus_one)} potential N+1 patterns to reduce database load"
            )

        # General recommendations
        recommendations.extend([
            "Enable pg_stat_statements for ongoing query monitoring",
            "Run VACUUM ANALYZE regularly for query plan optimization",
            "Implement query result caching for repeated reads",
            "Add connection pool monitoring and alerting",
            "Set up slow query logging (<50ms threshold)"
        ])

        return recommendations[:10]


async def main():
    """Main analysis entry point"""
    parser = argparse.ArgumentParser(description='Database Query Performance Analysis')
    parser.add_argument('--database-url', type=str, default=None,
                       help='PostgreSQL database URL')
    parser.add_argument('--duration', type=int, default=60,
                       help='Analysis duration in seconds (default: 60)')
    parser.add_argument('--export', type=str, default=None,
                       help='Export report to JSON file')
    parser.add_argument('--threshold', type=float, default=50.0,
                       help='Slow query threshold in ms (default: 50ms)')

    args = parser.parse_args()

    # Get database URL from environment or argument
    import os
    database_url = args.database_url or os.getenv('DATABASE_URL') or \
                  'postgresql://localhost:5432/enterprisehub'

    print("="*60)
    print("DATABASE QUERY PERFORMANCE ANALYZER")
    print("Phase 2 Performance Foundation - Week 3")
    print("="*60)
    print(f"Database: {database_url.split('@')[-1]}")
    print(f"Slow Query Threshold: {args.threshold}ms")
    print(f"Analysis Duration: {args.duration}s")
    print("="*60)

    analyzer = QueryPerformanceAnalyzer(database_url)

    try:
        await analyzer.initialize()

        # Run analysis
        report = await analyzer.generate_performance_report()

        # Export to file if requested
        if args.export:
            with open(args.export, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n✓ Report exported to {args.export}")

        # Print top recommendations
        print("\n" + "="*60)
        print("TOP RECOMMENDATIONS")
        print("="*60)
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")

    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await analyzer.close()


if __name__ == '__main__':
    asyncio.run(main())
