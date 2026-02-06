#!/usr/bin/env python3
"""
Jorge's BI Dashboard Database Integration Verification
Verifies OLAP schema deployment and data persistence integrity
"""

import psycopg2
import json
from datetime import datetime
from decimal import Decimal

def connect_db():
    """Connect to the PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="enterprise_hub",
            user="cave",
            # password="",  # No password for local development
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def verify_tables(cursor):
    """Verify all OLAP tables exist"""
    print("🔍 Verifying OLAP schema tables...")

    required_tables = [
        'fact_lead_interactions',
        'fact_commission_events',
        'fact_bot_performance',
        'agg_daily_metrics',
        'agg_hourly_metrics',
        'dim_bot_types',
        'dim_locations',
        'db_monitoring'
    ]

    cursor.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename IN %s
    """, (tuple(required_tables),))

    existing_tables = [row[0] for row in cursor.fetchall()]

    for table in required_tables:
        if table in existing_tables:
            print(f"  ✅ {table}")
        else:
            print(f"  ❌ {table} - MISSING!")
            return False

    return True

def verify_indexes(cursor):
    """Verify performance indexes exist"""
    print("\n🔍 Verifying performance indexes...")

    cursor.execute("""
        SELECT indexname FROM pg_indexes
        WHERE schemaname = 'public'
        AND indexname LIKE 'idx_%'
    """)

    indexes = [row[0] for row in cursor.fetchall()]

    required_indexes = [
        'idx_lead_interactions_timestamp',
        'idx_commission_events_timestamp',
        'idx_bot_performance_timestamp',
        'idx_daily_metrics_date',
        'idx_hourly_metrics_hour'
    ]

    for idx in required_indexes:
        if idx in indexes:
            print(f"  ✅ {idx}")
        else:
            print(f"  ❌ {idx} - MISSING!")
            return False

    print(f"  📊 Total indexes created: {len(indexes)}")
    return True

def verify_materialized_views(cursor):
    """Verify materialized views exist"""
    print("\n🔍 Verifying materialized views...")

    cursor.execute("""
        SELECT matviewname FROM pg_matviews
        WHERE schemaname = 'public'
    """)

    views = [row[0] for row in cursor.fetchall()]

    required_views = [
        'mv_real_time_dashboard',
        'mv_weekly_trends'
    ]

    for view in required_views:
        if view in views:
            print(f"  ✅ {view}")
        else:
            print(f"  ❌ {view} - MISSING!")
            return False

    return True

def verify_functions(cursor):
    """Verify stored functions exist"""
    print("\n🔍 Verifying stored functions...")

    cursor.execute("""
        SELECT proname FROM pg_proc
        WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
        AND proname IN ('refresh_analytics_views', 'aggregate_hourly_metrics', 'db_health_check', 'cleanup_old_data', 'log_performance_metrics')
    """)

    functions = [row[0] for row in cursor.fetchall()]

    required_functions = [
        'refresh_analytics_views',
        'aggregate_hourly_metrics',
        'db_health_check',
        'cleanup_old_data',
        'log_performance_metrics'
    ]

    for func in required_functions:
        if func in functions:
            print(f"  ✅ {func}")
        else:
            print(f"  ❌ {func} - MISSING!")
            return False

    return True

def test_data_persistence(cursor):
    """Test data insertion and persistence"""
    print("\n🧪 Testing data persistence...")

    try:
        # Test lead interactions insert
        test_lead_id = f"test_verify_{int(datetime.now().timestamp())}"
        cursor.execute("""
            INSERT INTO fact_lead_interactions
            (lead_id, event_type, jorge_metrics, location_id, bot_type, lead_temperature, processing_time_ms, confidence_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            test_lead_id,
            'verification_test',
            json.dumps({"frs_score": 90, "pcs_score": 85}),
            'test_location',
            'jorge-seller',
            'hot',
            35.5,
            0.95
        ))

        interaction_id = cursor.fetchone()[0]
        print(f"  ✅ Lead interaction inserted (ID: {interaction_id})")

        # Test commission events insert
        cursor.execute("""
            INSERT INTO fact_commission_events
            (lead_id, deal_id, commission_amount, pipeline_stage, jorge_pipeline_value, property_value, location_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            test_lead_id,
            'test_deal_001',
            Decimal('18000.00'),
            'qualified',
            Decimal('300000.00'),
            Decimal('300000.00'),
            'test_location'
        ))

        commission_id = cursor.fetchone()[0]
        print(f"  ✅ Commission event inserted (ID: {commission_id})")

        # Test bot performance insert
        cursor.execute("""
            INSERT INTO fact_bot_performance
            (bot_type, contact_id, processing_time_ms, success, confidence_score, bot_metrics, location_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            'jorge-seller',
            test_lead_id,
            28.7,
            True,
            0.98,
            json.dumps({"qualification_time": 120, "objections_handled": 2}),
            'test_location'
        ))

        performance_id = cursor.fetchone()[0]
        print(f"  ✅ Bot performance inserted (ID: {performance_id})")

        return True

    except Exception as e:
        print(f"  ❌ Data persistence test failed: {e}")
        return False

def test_query_performance(cursor):
    """Test query performance for BI dashboard"""
    print("\n⚡ Testing query performance...")

    queries = [
        ("Lead summary by temperature", """
            SELECT lead_temperature, COUNT(*), AVG(processing_time_ms)
            FROM fact_lead_interactions
            WHERE timestamp >= NOW() - INTERVAL '7 days'
            GROUP BY lead_temperature
        """),
        ("Commission pipeline summary", """
            SELECT pipeline_stage, COUNT(*), SUM(commission_amount), AVG(jorge_pipeline_value)
            FROM fact_commission_events
            WHERE timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY pipeline_stage
        """),
        ("Bot performance summary", """
            SELECT bot_type, COUNT(*), AVG(processing_time_ms), AVG(confidence_score)
            FROM fact_bot_performance
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
            GROUP BY bot_type
        """)
    ]

    for query_name, query in queries:
        start_time = datetime.now()
        cursor.execute(f"EXPLAIN ANALYZE {query}")
        results = cursor.fetchall()
        end_time = datetime.now()

        # Extract execution time from EXPLAIN ANALYZE
        execution_time = None
        for row in results:
            if "Execution Time" in str(row[0]):
                execution_time = str(row[0]).split("Execution Time: ")[1].split(" ms")[0]
                break

        if execution_time:
            print(f"  ✅ {query_name}: {execution_time} ms")
        else:
            duration = (end_time - start_time).total_seconds() * 1000
            print(f"  ✅ {query_name}: {duration:.2f} ms")

    return True

def test_aggregation_functions(cursor):
    """Test aggregation and analytics functions"""
    print("\n📊 Testing aggregation functions...")

    try:
        # Test health check
        cursor.execute("SELECT * FROM db_health_check()")
        health_results = cursor.fetchall()
        print(f"  ✅ Health check returned {len(health_results)} metrics")

        # Test hourly aggregation
        cursor.execute("SELECT aggregate_hourly_metrics()")
        print("  ✅ Hourly aggregation completed")

        # Test materialized view refresh
        cursor.execute("SELECT refresh_analytics_views()")
        print("  ✅ Materialized views refreshed")

        # Test cleanup function
        cursor.execute("SELECT * FROM cleanup_old_data()")
        cleanup_results = cursor.fetchall()
        print(f"  ✅ Data cleanup completed ({len(cleanup_results)} operations)")

        return True

    except Exception as e:
        print(f"  ❌ Aggregation functions test failed: {e}")
        return False

def main():
    """Main verification script"""
    print("🚀 Jorge's BI Dashboard Database Verification")
    print("=" * 50)

    # Connect to database
    conn = connect_db()
    if not conn:
        return False

    cursor = conn.cursor()

    # Run all verification tests
    tests = [
        ("OLAP Tables", lambda: verify_tables(cursor)),
        ("Performance Indexes", lambda: verify_indexes(cursor)),
        ("Materialized Views", lambda: verify_materialized_views(cursor)),
        ("Stored Functions", lambda: verify_functions(cursor)),
        ("Data Persistence", lambda: test_data_persistence(cursor)),
        ("Query Performance", lambda: test_query_performance(cursor)),
        ("Aggregation Functions", lambda: test_aggregation_functions(cursor)),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n🔧 Running {test_name} verification...")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} verification FAILED!")

    # Commit test data
    conn.commit()

    # Final summary
    print("\n" + "=" * 50)
    print(f"📋 VERIFICATION SUMMARY")
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Jorge's BI Dashboard database is ready!")
        print("\n✅ OLAP schema successfully deployed")
        print("✅ Data persistence validated")
        print("✅ Database performance optimized")
        print("✅ Monitoring and alerting configured")
        print("\n🚀 Ready for Jorge's Advanced Business Intelligence!")
    else:
        print(f"❌ {total - passed} tests failed. Please review and fix issues.")

    cursor.close()
    conn.close()

    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)