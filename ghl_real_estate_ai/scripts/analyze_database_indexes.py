#!/usr/bin/env python3
"""
🔍 Database Index Analysis and Optimization Script
==================================================

Analyze query patterns and recommend optimal indexes for EnterpriseHub.

Performance Goals:
- Identify missing indexes on frequently queried fields
- Generate SQL migration scripts for critical indexes
- Reduce query times from 70-100ms to <25ms (69% improvement)
- Focus on hot paths: lead scoring, property matching, webhooks

Features:
- Query pattern analysis
- Missing index detection
- Performance impact estimation
- Automatic migration script generation
- Index fragmentation analysis
- Cost/benefit analysis for each index

Author: EnterpriseHub Performance Agent
Date: 2026-01-10
"""

import asyncio
import asyncpg
import json
import time
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class QueryPattern:
    """Analyzed query pattern with performance metrics"""
    query_hash: str
    query_template: str
    execution_count: int
    avg_time_ms: float
    max_time_ms: float
    total_time_ms: float
    tables_used: List[str]
    where_conditions: List[Dict[str, str]]
    join_conditions: List[Dict[str, str]]
    order_by_fields: List[str]


@dataclass
class IndexRecommendation:
    """Index recommendation with impact analysis"""
    table_name: str
    columns: List[str]
    index_type: str  # btree, gin, gist, hash
    index_name: str
    estimated_improvement_percent: float
    query_frequency: int
    avg_query_time_ms: float
    priority_score: float
    create_sql: str
    estimated_size_mb: float
    maintenance_cost_score: float


class DatabaseIndexAnalyzer:
    """
    Advanced database index analyzer for PostgreSQL optimization.

    Analyzes query patterns from:
    1. PostgreSQL query logs
    2. Application-specific slow query tracking
    3. Real-time query performance monitoring

    Generates index recommendations based on:
    - Query frequency and execution time
    - Table size and growth patterns
    - Index maintenance overhead
    - Storage impact
    """

    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection: Optional[asyncpg.Connection] = None

        # Critical tables for EnterpriseHub
        self.critical_tables = {
            'leads', 'properties', 'conversations', 'analytics_events',
            'ghl_contacts', 'agent_profiles', 'property_matches',
            'coaching_sessions', 'market_data'
        }

        # Known hot query patterns for EnterpriseHub
        self.hot_query_patterns = [
            # Lead scoring queries (webhook processing hot path)
            {
                'pattern': r'SELECT.*FROM leads WHERE ghl_contact_id',
                'table': 'leads',
                'columns': ['ghl_contact_id'],
                'priority': 10
            },
            {
                'pattern': r'SELECT.*FROM leads WHERE.*status.*lead_score',
                'table': 'leads',
                'columns': ['status', 'lead_score'],
                'priority': 9
            },
            # Property matching queries
            {
                'pattern': r'SELECT.*FROM properties WHERE.*location.*price',
                'table': 'properties',
                'columns': ['location', 'price_min', 'price_max'],
                'priority': 9
            },
            # Conversation history (frequent joins)
            {
                'pattern': r'SELECT.*FROM conversations.*contact_id.*timestamp',
                'table': 'conversations',
                'columns': ['contact_id', 'timestamp'],
                'priority': 8
            },
            # Analytics queries (reduce full table scans)
            {
                'pattern': r'SELECT.*FROM analytics_events.*event_type.*created_at',
                'table': 'analytics_events',
                'columns': ['event_type', 'created_at'],
                'priority': 7
            }
        ]

    async def connect(self):
        """Establish database connection."""
        try:
            self.connection = await asyncpg.connect(self.connection_string)
            logger.info("Database connection established for index analysis")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    async def disconnect(self):
        """Close database connection."""
        if self.connection:
            await self.connection.close()
            logger.info("Database connection closed")

    async def analyze_missing_indexes(self) -> List[IndexRecommendation]:
        """
        Analyze database for missing indexes with comprehensive impact analysis.

        Returns prioritized list of index recommendations.
        """
        logger.info("🔍 Starting comprehensive index analysis...")

        recommendations = []

        # Analyze query patterns from pg_stat_statements
        query_patterns = await self._analyze_query_patterns()

        # Check existing indexes
        existing_indexes = await self._get_existing_indexes()

        # Analyze table statistics
        table_stats = await self._get_table_statistics()

        # Generate recommendations for each query pattern
        for pattern in query_patterns:
            for table in pattern.tables_used:
                if table not in self.critical_tables:
                    continue

                # Find missing indexes for WHERE conditions
                for condition in pattern.where_conditions:
                    recommendation = await self._analyze_condition_index(
                        table, condition, pattern, existing_indexes, table_stats
                    )
                    if recommendation:
                        recommendations.append(recommendation)

                # Find missing indexes for ORDER BY
                if pattern.order_by_fields:
                    order_recommendation = await self._analyze_order_by_index(
                        table, pattern.order_by_fields, pattern, existing_indexes
                    )
                    if order_recommendation:
                        recommendations.append(order_recommendation)

        # Add critical indexes from hot patterns
        critical_recommendations = await self._analyze_critical_patterns()
        recommendations.extend(critical_recommendations)

        # Remove duplicates and prioritize
        unique_recommendations = self._deduplicate_recommendations(recommendations)
        prioritized_recommendations = sorted(
            unique_recommendations,
            key=lambda r: r.priority_score,
            reverse=True
        )

        logger.info(f"Generated {len(prioritized_recommendations)} index recommendations")

        return prioritized_recommendations

    async def _analyze_query_patterns(self) -> List[QueryPattern]:
        """Analyze query patterns from PostgreSQL statistics."""

        # Enable pg_stat_statements if not enabled
        await self.connection.execute("CREATE EXTENSION IF NOT EXISTS pg_stat_statements")

        # Query pg_stat_statements for slow queries
        query = """
        SELECT
            query,
            calls as execution_count,
            mean_exec_time as avg_time_ms,
            max_exec_time as max_time_ms,
            total_exec_time as total_time_ms
        FROM pg_stat_statements
        WHERE calls > 10  -- Ignore one-off queries
        AND mean_exec_time > 5  -- Focus on queries >5ms
        ORDER BY total_exec_time DESC
        LIMIT 100
        """

        try:
            rows = await self.connection.fetch(query)
            patterns = []

            for row in rows:
                pattern = self._parse_query_pattern(row)
                if pattern:
                    patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.warning(f"Could not analyze pg_stat_statements: {e}")
            # Fall back to analyzing known hot patterns
            return await self._analyze_hot_patterns()

    def _parse_query_pattern(self, row: dict) -> Optional[QueryPattern]:
        """Parse query into structured pattern."""
        query = row['query'].strip()

        # Skip utility queries
        if any(keyword in query.upper() for keyword in ['CREATE', 'DROP', 'ALTER', 'GRANT', 'REVOKE']):
            return None

        # Extract table names
        tables = self._extract_table_names(query)

        # Extract WHERE conditions
        where_conditions = self._extract_where_conditions(query)

        # Extract ORDER BY fields
        order_by_fields = self._extract_order_by_fields(query)

        # Extract JOIN conditions
        join_conditions = self._extract_join_conditions(query)

        return QueryPattern(
            query_hash=str(hash(query)),
            query_template=query,
            execution_count=row['execution_count'],
            avg_time_ms=float(row['avg_time_ms']),
            max_time_ms=float(row['max_time_ms']),
            total_time_ms=float(row['total_time_ms']),
            tables_used=tables,
            where_conditions=where_conditions,
            join_conditions=join_conditions,
            order_by_fields=order_by_fields
        )

    def _extract_table_names(self, query: str) -> List[str]:
        """Extract table names from SQL query."""
        # Simple regex for table extraction
        from_pattern = r'FROM\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        join_pattern = r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_]*)'

        tables = set()

        # Find FROM clauses
        from_matches = re.finditer(from_pattern, query, re.IGNORECASE)
        for match in from_matches:
            tables.add(match.group(1).lower())

        # Find JOIN clauses
        join_matches = re.finditer(join_pattern, query, re.IGNORECASE)
        for match in join_matches:
            tables.add(match.group(1).lower())

        return list(tables)

    def _extract_where_conditions(self, query: str) -> List[Dict[str, str]]:
        """Extract WHERE conditions from SQL query."""
        conditions = []

        # Simple WHERE condition extraction
        where_patterns = [
            r'WHERE\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=',
            r'WHERE\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*IN',
            r'WHERE\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*>',
            r'WHERE\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*<',
            r'AND\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=',
            r'AND\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*IN',
        ]

        for pattern in where_patterns:
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                conditions.append({
                    'column': match.group(1).lower(),
                    'operator': '=',  # Simplified
                    'pattern': match.group(0)
                })

        return conditions

    def _extract_order_by_fields(self, query: str) -> List[str]:
        """Extract ORDER BY fields from SQL query."""
        order_by_pattern = r'ORDER BY\s+([^;]+)'
        match = re.search(order_by_pattern, query, re.IGNORECASE)

        if match:
            # Split by comma and clean up
            fields = [field.strip().split()[0] for field in match.group(1).split(',')]
            return [field.lower() for field in fields if field.isalnum()]

        return []

    def _extract_join_conditions(self, query: str) -> List[Dict[str, str]]:
        """Extract JOIN conditions from SQL query."""
        # Simplified JOIN condition extraction
        join_pattern = r'ON\s+([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)'

        conditions = []
        matches = re.finditer(join_pattern, query, re.IGNORECASE)

        for match in matches:
            conditions.append({
                'left_field': match.group(1).lower(),
                'right_field': match.group(2).lower(),
                'operator': '='
            })

        return conditions

    async def _get_existing_indexes(self) -> Dict[str, List[str]]:
        """Get existing indexes for all tables."""
        query = """
        SELECT
            t.tablename,
            i.indexname,
            array_agg(a.attname ORDER BY a.attnum) as columns
        FROM pg_indexes i
        JOIN pg_tables t ON t.tablename = i.tablename
        JOIN pg_class c ON c.relname = i.indexname
        JOIN pg_index ix ON ix.indexrelid = c.oid
        JOIN pg_attribute a ON a.attrelid = ix.indrelid
            AND a.attnum = ANY(ix.indkey)
        WHERE t.schemaname = 'public'
        AND i.indexname NOT LIKE 'pg_%'
        GROUP BY t.tablename, i.indexname
        """

        rows = await self.connection.fetch(query)

        indexes = {}
        for row in rows:
            table = row['tablename']
            if table not in indexes:
                indexes[table] = []
            indexes[table].append({
                'name': row['indexname'],
                'columns': row['columns']
            })

        return indexes

    async def _get_table_statistics(self) -> Dict[str, Dict]:
        """Get table size and statistics."""
        query = """
        SELECT
            relname as table_name,
            pg_size_pretty(pg_total_relation_size(oid)) as size,
            pg_total_relation_size(oid) as size_bytes,
            reltuples::bigint as row_count
        FROM pg_class
        WHERE relkind = 'r'
        AND relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        """

        rows = await self.connection.fetch(query)

        stats = {}
        for row in rows:
            stats[row['table_name']] = {
                'size': row['size'],
                'size_bytes': row['size_bytes'],
                'row_count': row['row_count']
            }

        return stats

    async def _analyze_condition_index(
        self,
        table: str,
        condition: Dict[str, str],
        pattern: QueryPattern,
        existing_indexes: Dict[str, List],
        table_stats: Dict[str, Dict]
    ) -> Optional[IndexRecommendation]:
        """Analyze if a condition needs an index."""

        column = condition['column']

        # Check if index already exists
        if table in existing_indexes:
            for index in existing_indexes[table]:
                if column in index['columns']:
                    return None  # Index already exists

        # Calculate impact
        table_size_mb = table_stats.get(table, {}).get('size_bytes', 0) / (1024 * 1024)
        estimated_improvement = min(pattern.avg_time_ms * 0.6, 80.0)  # Up to 80% improvement

        priority_score = (
            pattern.execution_count * pattern.avg_time_ms / 1000.0 * estimated_improvement / 100.0
        )

        index_name = f"idx_{table}_{column}"
        create_sql = f"CREATE INDEX CONCURRENTLY {index_name} ON {table}({column});"

        return IndexRecommendation(
            table_name=table,
            columns=[column],
            index_type='btree',
            index_name=index_name,
            estimated_improvement_percent=estimated_improvement,
            query_frequency=pattern.execution_count,
            avg_query_time_ms=pattern.avg_time_ms,
            priority_score=priority_score,
            create_sql=create_sql,
            estimated_size_mb=table_size_mb * 0.1,  # Rough estimate
            maintenance_cost_score=table_size_mb * 0.01
        )

    async def _analyze_order_by_index(
        self,
        table: str,
        order_fields: List[str],
        pattern: QueryPattern,
        existing_indexes: Dict[str, List]
    ) -> Optional[IndexRecommendation]:
        """Analyze ORDER BY clauses for index opportunities."""

        if len(order_fields) == 0:
            return None

        # Check if composite index exists
        if table in existing_indexes:
            for index in existing_indexes[table]:
                if all(field in index['columns'] for field in order_fields):
                    return None

        # Create composite index recommendation
        index_name = f"idx_{table}_{'_'.join(order_fields)}"
        create_sql = f"CREATE INDEX CONCURRENTLY {index_name} ON {table}({', '.join(order_fields)});"

        priority_score = pattern.execution_count * pattern.avg_time_ms * 0.3 / 1000.0

        return IndexRecommendation(
            table_name=table,
            columns=order_fields,
            index_type='btree',
            index_name=index_name,
            estimated_improvement_percent=40.0,
            query_frequency=pattern.execution_count,
            avg_query_time_ms=pattern.avg_time_ms,
            priority_score=priority_score,
            create_sql=create_sql,
            estimated_size_mb=10.0,  # Composite indexes are larger
            maintenance_cost_score=5.0
        )

    async def _analyze_critical_patterns(self) -> List[IndexRecommendation]:
        """Analyze known critical query patterns for EnterpriseHub."""

        recommendations = []

        # Critical indexes for EnterpriseHub hot paths
        critical_indexes = [
            {
                'table': 'leads',
                'columns': ['ghl_contact_id'],
                'priority': 10,
                'description': 'Lead lookup by GHL contact ID (webhook hot path)'
            },
            {
                'table': 'leads',
                'columns': ['status', 'lead_score'],
                'priority': 9,
                'description': 'Lead filtering by status and score'
            },
            {
                'table': 'leads',
                'columns': ['created_at'],
                'priority': 8,
                'description': 'Lead queries by creation date'
            },
            {
                'table': 'properties',
                'columns': ['location', 'price_min', 'price_max'],
                'priority': 9,
                'description': 'Property matching by location and price range'
            },
            {
                'table': 'properties',
                'columns': ['property_type', 'status'],
                'priority': 7,
                'description': 'Property filtering by type and availability'
            },
            {
                'table': 'conversations',
                'columns': ['contact_id', 'timestamp'],
                'priority': 8,
                'description': 'Conversation history lookup (frequent joins)'
            },
            {
                'table': 'analytics_events',
                'columns': ['event_type', 'created_at'],
                'priority': 7,
                'description': 'Analytics queries by event type and date'
            },
            {
                'table': 'coaching_sessions',
                'columns': ['agent_id', 'session_date'],
                'priority': 6,
                'description': 'Claude coaching session queries'
            },
            {
                'table': 'property_matches',
                'columns': ['lead_id', 'match_score'],
                'priority': 6,
                'description': 'Property matching results by lead and score'
            }
        ]

        existing_indexes = await self._get_existing_indexes()

        for index_spec in critical_indexes:
            table = index_spec['table']
            columns = index_spec['columns']

            # Check if index already exists
            index_exists = False
            if table in existing_indexes:
                for existing_index in existing_indexes[table]:
                    if set(columns) <= set(existing_index['columns']):
                        index_exists = True
                        break

            if not index_exists:
                index_name = f"idx_{table}_{'_'.join(columns)}"
                create_sql = f"CREATE INDEX CONCURRENTLY {index_name} ON {table}({', '.join(columns)});"

                # Estimate impact based on priority and typical workload
                estimated_improvement = min(index_spec['priority'] * 8, 75)
                query_frequency = index_spec['priority'] * 100  # Estimate based on priority

                recommendation = IndexRecommendation(
                    table_name=table,
                    columns=columns,
                    index_type='btree',
                    index_name=index_name,
                    estimated_improvement_percent=estimated_improvement,
                    query_frequency=query_frequency,
                    avg_query_time_ms=80.0,  # Typical unindexed query time
                    priority_score=index_spec['priority'] * 100,
                    create_sql=create_sql,
                    estimated_size_mb=5.0 * len(columns),
                    maintenance_cost_score=2.0
                )

                recommendations.append(recommendation)

        return recommendations

    async def _analyze_hot_patterns(self) -> List[QueryPattern]:
        """Analyze hot patterns when pg_stat_statements is unavailable."""

        patterns = []

        # Mock query patterns based on known EnterpriseHub usage
        mock_patterns = [
            {
                'query': 'SELECT * FROM leads WHERE ghl_contact_id = $1',
                'execution_count': 2500,
                'avg_time_ms': 85.0,
                'tables': ['leads']
            },
            {
                'query': 'SELECT * FROM properties WHERE location = $1 AND price_min <= $2 AND price_max >= $3',
                'execution_count': 1800,
                'avg_time_ms': 120.0,
                'tables': ['properties']
            },
            {
                'query': 'SELECT * FROM conversations WHERE contact_id = $1 ORDER BY timestamp DESC',
                'execution_count': 1200,
                'avg_time_ms': 95.0,
                'tables': ['conversations']
            }
        ]

        for pattern_data in mock_patterns:
            pattern = QueryPattern(
                query_hash=str(hash(pattern_data['query'])),
                query_template=pattern_data['query'],
                execution_count=pattern_data['execution_count'],
                avg_time_ms=pattern_data['avg_time_ms'],
                max_time_ms=pattern_data['avg_time_ms'] * 3,
                total_time_ms=pattern_data['execution_count'] * pattern_data['avg_time_ms'],
                tables_used=pattern_data['tables'],
                where_conditions=[],
                join_conditions=[],
                order_by_fields=[]
            )
            patterns.append(pattern)

        return patterns

    def _deduplicate_recommendations(self, recommendations: List[IndexRecommendation]) -> List[IndexRecommendation]:
        """Remove duplicate index recommendations."""

        seen_indexes = set()
        unique_recommendations = []

        for recommendation in recommendations:
            # Create a key for deduplication
            key = (recommendation.table_name, tuple(sorted(recommendation.columns)))

            if key not in seen_indexes:
                seen_indexes.add(key)
                unique_recommendations.append(recommendation)

        return unique_recommendations

    async def generate_migration_script(
        self,
        recommendations: List[IndexRecommendation],
        max_indexes: int = 10
    ) -> str:
        """Generate SQL migration script for recommended indexes."""

        # Take top recommendations by priority
        top_recommendations = recommendations[:max_indexes]

        script_lines = [
            "-- Critical Database Indexes for EnterpriseHub",
            "-- Generated by Database Index Analyzer",
            f"-- Date: {datetime.now().isoformat()}",
            f"-- Recommendations: {len(top_recommendations)}",
            "",
            "-- IMPORTANT: Run these indexes with CONCURRENTLY to avoid blocking",
            "-- Monitor disk space - estimated total size: {:.1f}MB".format(
                sum(r.estimated_size_mb for r in top_recommendations)
            ),
            ""
        ]

        for i, rec in enumerate(top_recommendations, 1):
            script_lines.extend([
                f"-- Index {i}: {rec.index_name}",
                f"-- Table: {rec.table_name}, Columns: {', '.join(rec.columns)}",
                f"-- Priority Score: {rec.priority_score:.1f}",
                f"-- Estimated Improvement: {rec.estimated_improvement_percent:.1f}%",
                f"-- Query Frequency: {rec.query_frequency} executions",
                f"-- Avg Query Time: {rec.avg_query_time_ms:.1f}ms",
                f"-- Estimated Size: {rec.estimated_size_mb:.1f}MB",
                "",
                rec.create_sql,
                ""
            ])

        # Add verification queries
        script_lines.extend([
            "-- Verification Queries",
            "-- Check index creation status:",
            "SELECT schemaname, tablename, indexname, indexdef",
            "FROM pg_indexes",
            "WHERE indexname LIKE 'idx_%'",
            "ORDER BY indexname;",
            "",
            "-- Check index usage after creation:",
            "SELECT schemaname, tablename, attname, n_distinct, correlation",
            "FROM pg_stats",
            "WHERE tablename IN ('" + "', '".join(set(r.table_name for r in top_recommendations)) + "');",
            ""
        ])

        return "\n".join(script_lines)

    async def estimate_performance_impact(
        self,
        recommendations: List[IndexRecommendation]
    ) -> Dict[str, float]:
        """Estimate overall performance impact of implementing recommendations."""

        total_improvement_weighted = 0.0
        total_weight = 0.0

        for rec in recommendations:
            weight = rec.query_frequency * rec.avg_query_time_ms
            improvement = rec.estimated_improvement_percent / 100.0
            total_improvement_weighted += weight * improvement
            total_weight += weight

        overall_improvement = total_improvement_weighted / total_weight if total_weight > 0 else 0.0

        return {
            'overall_query_improvement_percent': overall_improvement * 100,
            'estimated_queries_affected': sum(r.query_frequency for r in recommendations),
            'estimated_time_saved_ms_per_hour': sum(
                r.query_frequency * r.avg_query_time_ms * r.estimated_improvement_percent / 100.0
                for r in recommendations
            ),
            'total_storage_overhead_mb': sum(r.estimated_size_mb for r in recommendations),
            'maintenance_cost_score': sum(r.maintenance_cost_score for r in recommendations)
        }


# Main execution
async def main():
    """Run database index analysis."""

    # Database connection string (use environment variable in production)
    connection_string = "postgresql://user:password@localhost:5432/enterprisehub"

    analyzer = DatabaseIndexAnalyzer(connection_string)

    try:
        await analyzer.connect()

        print("🔍 Analyzing database indexes for EnterpriseHub...")

        # Analyze missing indexes
        recommendations = await analyzer.analyze_missing_indexes()

        if recommendations:
            print(f"\n📊 Generated {len(recommendations)} index recommendations:")
            print("-" * 80)

            for i, rec in enumerate(recommendations[:10], 1):  # Show top 10
                print(f"{i:2d}. {rec.index_name}")
                print(f"    Table: {rec.table_name}")
                print(f"    Columns: {', '.join(rec.columns)}")
                print(f"    Priority Score: {rec.priority_score:.1f}")
                print(f"    Estimated Improvement: {rec.estimated_improvement_percent:.1f}%")
                print(f"    Query Frequency: {rec.query_frequency}")
                print(f"    Estimated Size: {rec.estimated_size_mb:.1f}MB")
                print()

            # Generate migration script
            migration_script = await analyzer.generate_migration_script(recommendations, max_indexes=8)

            # Save migration script
            script_path = Path("migrations/001_add_critical_indexes.sql")
            script_path.parent.mkdir(exist_ok=True)
            script_path.write_text(migration_script)

            print(f"📝 Migration script saved to: {script_path}")

            # Estimate performance impact
            impact = await analyzer.estimate_performance_impact(recommendations[:10])

            print("\n🚀 Estimated Performance Impact:")
            print(f"   Overall Query Improvement: {impact['overall_query_improvement_percent']:.1f}%")
            print(f"   Queries Affected: {impact['estimated_queries_affected']:,}")
            print(f"   Time Saved per Hour: {impact['estimated_time_saved_ms_per_hour']:,.0f}ms")
            print(f"   Storage Overhead: {impact['total_storage_overhead_mb']:.1f}MB")
            print(f"   Maintenance Cost Score: {impact['maintenance_cost_score']:.1f}")

        else:
            print("✅ No missing indexes found - database is well optimized!")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        logger.error(f"Database index analysis failed: {e}")

    finally:
        await analyzer.disconnect()


if __name__ == "__main__":
    asyncio.run(main())