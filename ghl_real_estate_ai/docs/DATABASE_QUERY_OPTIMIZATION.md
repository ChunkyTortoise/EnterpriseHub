# Database Query Optimization Guide

**Phase 2 Performance Foundation - Week 3 Quick Wins**

Target Performance Metrics:
- Database query time: **<50ms P90**
- Connection pool efficiency: **>90%**
- Index usage: **100% on critical queries**
- N+1 query patterns: **0**

## Table of Contents

1. [Performance Index Migration](#performance-index-migration)
2. [Connection Pool Optimization](#connection-pool-optimization)
3. [Query Optimization Patterns](#query-optimization-patterns)
4. [N+1 Query Detection and Prevention](#n1-query-detection-and-prevention)
5. [Performance Monitoring](#performance-monitoring)
6. [Troubleshooting](#troubleshooting)

---

## Performance Index Migration

### Quick Start

```bash
# 1. Set database connection
export DATABASE_URL="postgresql://user:pass@localhost:5432/enterprisehub"

# 2. Run migration script
./ghl_real_estate_ai/scripts/run_performance_migration.sh

# 3. Verify performance improvements
python ghl_real_estate_ai/scripts/analyze_query_performance.py
```

### New Performance Indexes

The migration adds 16 high-performance indexes targeting <50ms P90 query performance:

#### Leads Table Indexes

1. **`idx_leads_created_scored`** - Primary active lead queries
   ```sql
   CREATE INDEX CONCURRENTLY idx_leads_created_scored
       ON leads(created_at DESC, ml_score DESC)
       WHERE status = 'active';
   ```
   **Optimizes:**
   ```python
   # Active leads ordered by recency and score
   leads = await db.execute(
       "SELECT * FROM leads WHERE status = 'active' "
       "ORDER BY created_at DESC, ml_score DESC LIMIT 50"
   )
   ```

2. **`idx_leads_score_status_created`** - Covering index for dashboards
   ```sql
   CREATE INDEX CONCURRENTLY idx_leads_score_status_created
       ON leads(ml_score DESC, status, created_at DESC)
       INCLUDE (contact_id, name, email, phone);
   ```
   **Optimizes:** Dashboard queries with index-only scans (no table lookups)

3. **`idx_leads_hot_leads`** - High-value lead filtering
   ```sql
   CREATE INDEX CONCURRENTLY idx_leads_hot_leads
       ON leads(ml_score DESC, created_at DESC)
       WHERE status = 'active' AND ml_score >= 7;
   ```
   **Optimizes:**
   ```python
   # Hot leads (score >= 7) for priority follow-up
   hot_leads = await db.execute(
       "SELECT * FROM leads "
       "WHERE status = 'active' AND ml_score >= 7 "
       "ORDER BY ml_score DESC, created_at DESC"
   )
   ```

4. **`idx_leads_search_gin`** - Full-text search
   ```sql
   CREATE INDEX CONCURRENTLY idx_leads_search_gin
       ON leads USING GIN(to_tsvector('english',
           COALESCE(name, '') || ' ' ||
           COALESCE(email, '') || ' ' ||
           COALESCE(phone, '')
       ));
   ```
   **Optimizes:** Lead search across name, email, phone

#### Properties Table Indexes

5. **`idx_properties_location_price`** - Spatial + price search
   ```sql
   CREATE INDEX CONCURRENTLY idx_properties_location_price
       ON properties USING GiST (
           ST_MakePoint(longitude, latitude),
           price_range
       )
       WHERE status = 'Active';
   ```
   **Optimizes:**
   ```python
   # Properties near location within price range
   properties = await db.execute(
       "SELECT * FROM properties "
       "WHERE status = 'Active' "
       "  AND ST_DWithin(ST_Point(longitude, latitude)::geography, "
       "                 ST_Point($1, $2)::geography, $3) "
       "  AND price BETWEEN $4 AND $5"
   )
   ```

6. **`idx_properties_search_common`** - Common search pattern
   ```sql
   CREATE INDEX CONCURRENTLY idx_properties_search_common
       ON properties(price, bedrooms, bathrooms, property_type, status)
       WHERE status = 'Active';
   ```
   **Optimizes:**
   ```python
   # Standard property search
   properties = await db.execute(
       "SELECT * FROM properties "
       "WHERE status = 'Active' "
       "  AND price BETWEEN $1 AND $2 "
       "  AND bedrooms >= $3 "
       "  AND bathrooms >= $4 "
       "  AND property_type = $5"
   )
   ```

### Connection Pool Configuration

**Updated Configuration** (Lines 158-160 in `database_optimization.py`):

```python
@dataclass
class DatabaseOptimizationConfig:
    # Connection pool settings (optimized for Phase 2 Week 3)
    master_pool_size: int = 50  # Increased from 20 for higher write throughput
    replica_pool_size: int = 100  # Increased from 30 for read-heavy workloads
    analytics_pool_size: int = 10
    cache_pool_size: int = 15
```

**Performance Impact:**
- Master pool: 20 → 50 (+150%) for write-heavy operations
- Replica pool: 30 → 100 (+233%) for read-heavy workloads
- Target: >90% connection pool efficiency

### Rollback Instructions

If issues arise, rollback the migration:

```bash
# Connect to database
psql $DATABASE_URL

# Drop new indexes
DROP INDEX CONCURRENTLY IF EXISTS idx_leads_created_scored;
DROP INDEX CONCURRENTLY IF EXISTS idx_leads_score_status_created;
DROP INDEX CONCURRENTLY IF EXISTS idx_leads_hot_leads;
DROP INDEX CONCURRENTLY IF EXISTS idx_leads_search_gin;
DROP INDEX CONCURRENTLY IF EXISTS idx_leads_status_updated;
DROP INDEX CONCURRENTLY IF EXISTS idx_properties_location_price;
DROP INDEX CONCURRENTLY IF EXISTS idx_properties_location_btree;
DROP INDEX CONCURRENTLY IF EXISTS idx_properties_search_common;
DROP INDEX CONCURRENTLY IF EXISTS idx_properties_listing_page;
DROP INDEX CONCURRENTLY IF EXISTS idx_properties_featured;
DROP INDEX CONCURRENTLY IF EXISTS idx_properties_amenities_gin;
DROP INDEX CONCURRENTLY IF EXISTS idx_properties_location_text;

# Remove migration record
DELETE FROM schema_migrations WHERE version = '001';
```

---

## Query Optimization Patterns

### Pattern 1: Eliminate N+1 Queries

**❌ BAD - N+1 Query Pattern:**

```python
# Fetches leads individually in a loop - 1 + N queries
async def get_leads_with_properties_bad(lead_ids: List[str]):
    leads = []
    for lead_id in lead_ids:  # N queries
        lead = await db.fetchrow(
            "SELECT * FROM leads WHERE id = $1", lead_id
        )
        leads.append(lead)
    return leads
```

**✅ GOOD - Bulk Query:**

```python
# Single query with IN clause - 1 query total
async def get_leads_with_properties_good(lead_ids: List[str]):
    leads = await db.fetch(
        "SELECT * FROM leads WHERE id = ANY($1)",
        lead_ids
    )
    return leads
```

**Performance Improvement:** 100+ queries → 1 query (99% reduction)

### Pattern 2: Use Covering Indexes

**❌ BAD - Requires table lookup:**

```python
# Query needs to look up table for additional columns
leads = await db.fetch(
    "SELECT name, email, phone, created_at "
    "FROM leads "
    "WHERE status = 'active' "
    "ORDER BY created_at DESC"
)
```

**✅ GOOD - Index-only scan with INCLUDE:**

```python
# All columns in index - no table lookup needed
leads = await db.fetch(
    "SELECT ml_score, status, created_at, contact_id, name, email, phone "
    "FROM leads "
    "WHERE status = 'active' "
    "ORDER BY ml_score DESC, created_at DESC"
)
# Uses idx_leads_score_status_created with INCLUDE clause
```

**Performance Improvement:** 50-80% faster (eliminates random I/O)

### Pattern 3: Optimize WHERE + ORDER BY

**❌ BAD - Separate indexes inefficiently combined:**

```python
# Uses one index for WHERE, sorts in memory
leads = await db.fetch(
    "SELECT * FROM leads "
    "WHERE status = 'active' "
    "ORDER BY created_at DESC, ml_score DESC"
)
```

**✅ GOOD - Composite index matches query pattern:**

```python
# Uses idx_leads_created_scored - no sorting needed
leads = await db.fetch(
    "SELECT * FROM leads "
    "WHERE status = 'active' "
    "ORDER BY created_at DESC, ml_score DESC "
    "LIMIT 50"
)
```

**Performance Improvement:** Eliminates sort operation (2-5x faster)

### Pattern 4: Use Partial Indexes for Filtered Queries

**❌ BAD - Full index scan:**

```python
# Scans all leads, filters in application
all_leads = await db.fetch("SELECT * FROM leads")
hot_leads = [l for l in all_leads if l['ml_score'] >= 7 and l['status'] == 'active']
```

**✅ GOOD - Partial index:**

```python
# Uses idx_leads_hot_leads partial index
hot_leads = await db.fetch(
    "SELECT * FROM leads "
    "WHERE status = 'active' AND ml_score >= 7 "
    "ORDER BY ml_score DESC"
)
```

**Performance Improvement:** 10-100x faster depending on data distribution

### Pattern 5: Batch Property Interactions

**❌ BAD - Individual inserts:**

```python
async def record_property_views_bad(views: List[PropertyView]):
    for view in views:  # N queries
        await db.execute(
            "INSERT INTO property_interactions (conversation_id, property_id, ...) "
            "VALUES ($1, $2, ...)",
            view.conversation_id, view.property_id, ...
        )
```

**✅ GOOD - Bulk insert:**

```python
async def record_property_views_good(views: List[PropertyView]):
    # 1 query with multiple rows
    values = [(v.conversation_id, v.property_id, ...) for v in views]
    await db.executemany(
        "INSERT INTO property_interactions (conversation_id, property_id, ...) "
        "VALUES ($1, $2, ...)",
        values
    )
```

**Performance Improvement:** 50-100x faster for batch operations

---

## N+1 Query Detection and Prevention

### Detection Methods

#### 1. Manual Code Review

Look for these patterns:

```python
# RED FLAG: Loop with database query
for item in items:
    result = await db.execute("SELECT ...", item.id)

# RED FLAG: List comprehension with database query
results = [await get_item(id) for id in item_ids]

# RED FLAG: Nested queries in loops
for lead in leads:
    properties = await db.fetch("SELECT * FROM properties WHERE lead_id = $1", lead.id)
```

#### 2. Automated Detection

Run the query performance analyzer:

```bash
python ghl_real_estate_ai/scripts/analyze_query_performance.py
```

The script identifies N+1 patterns by detecting:
- High query frequency (>500 calls)
- Similar query patterns with different parameters
- Single-row SELECT queries repeated many times

#### 3. Database Statistics

Check `pg_stat_statements`:

```sql
-- Find queries executed very frequently
SELECT
    query,
    calls,
    mean_exec_time,
    total_exec_time
FROM pg_stat_statements
WHERE calls > 1000
  AND query LIKE '%WHERE%id%=%'
ORDER BY calls DESC;
```

### Prevention Strategies

#### Strategy 1: Eager Loading with JOINs

```python
# Load leads with their properties in single query
async def get_leads_with_properties(tenant_id: str):
    return await db.fetch("""
        SELECT
            l.*,
            json_agg(
                json_build_object(
                    'id', p.id,
                    'address', p.address,
                    'price', p.price
                )
            ) as properties
        FROM leads l
        LEFT JOIN property_interactions pi ON l.id = pi.lead_id
        LEFT JOIN properties p ON pi.property_id = p.id
        WHERE l.tenant_id = $1
        GROUP BY l.id
    """, tenant_id)
```

#### Strategy 2: Batch Loading

```python
# Load all related data in one query
async def get_conversations_with_preferences(conversation_ids: List[str]):
    # Single query for all conversations
    conversations = await db.fetch(
        "SELECT * FROM conversations WHERE id = ANY($1)",
        conversation_ids
    )

    # Single query for all preferences
    preferences = await db.fetch(
        "SELECT * FROM behavioral_preferences WHERE conversation_id = ANY($1)",
        conversation_ids
    )

    # Combine in application
    prefs_by_conv = defaultdict(list)
    for pref in preferences:
        prefs_by_conv[pref['conversation_id']].append(pref)

    return [(conv, prefs_by_conv[conv['id']]) for conv in conversations]
```

#### Strategy 3: Use Subqueries

```python
# Get lead counts without N+1
async def get_lead_stats_by_agent():
    return await db.fetch("""
        SELECT
            agent_id,
            COUNT(*) as total_leads,
            COUNT(*) FILTER (WHERE ml_score >= 7) as hot_leads,
            AVG(ml_score) as avg_score
        FROM leads
        WHERE status = 'active'
        GROUP BY agent_id
    """)
```

---

## Performance Monitoring

### Real-Time Query Analysis

```bash
# Run performance analysis
python ghl_real_estate_ai/scripts/analyze_query_performance.py

# Export report
python ghl_real_estate_ai/scripts/analyze_query_performance.py --export report.json

# Custom threshold
python ghl_real_estate_ai/scripts/analyze_query_performance.py --threshold 30.0
```

### Database Statistics

Enable `pg_stat_statements` extension:

```sql
-- Enable extension (requires superuser)
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Add to postgresql.conf
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all
pg_stat_statements.max = 10000

-- Restart PostgreSQL
```

### Monitoring Queries

```sql
-- Top 10 slowest queries
SELECT
    query,
    calls,
    mean_exec_time,
    max_exec_time,
    total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Queries with high total time (cumulative impact)
SELECT
    query,
    calls,
    mean_exec_time,
    total_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Index usage statistics
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Tables with high sequential scan rates
SELECT
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    n_live_tup,
    ROUND(100.0 * seq_scan / NULLIF(seq_scan + idx_scan, 0), 2) as seq_scan_pct
FROM pg_stat_user_tables
WHERE schemaname = 'public'
  AND n_live_tup > 1000
ORDER BY seq_scan DESC;
```

### Connection Pool Monitoring

```python
# Get connection pool metrics
from ghl_real_estate_ai.services.database_optimization import get_optimized_database_manager

db_manager = await get_optimized_database_manager()
health = await db_manager.get_connection_health()
metrics = await db_manager.get_optimization_metrics()

print(f"Pool Efficiency: {metrics['connection_pools']['master_0']['efficiency']:.1%}")
print(f"Avg Query Time: {metrics['query_performance']['avg_execution_time_ms']:.1f}ms")
print(f"P95 Query Time: {metrics['query_performance']['p95_execution_time_ms']:.1f}ms")
print(f"Cache Hit Rate: {metrics['query_performance']['cache_hit_rate']:.1%}")
```

---

## Troubleshooting

### Issue: Queries Still Slow After Migration

**Diagnosis:**

```sql
-- Check if indexes are being used
EXPLAIN ANALYZE
SELECT * FROM leads
WHERE status = 'active'
ORDER BY created_at DESC, ml_score DESC
LIMIT 50;

-- Look for "Index Scan" or "Index Only Scan" in output
-- If you see "Seq Scan", index is not being used
```

**Solutions:**

1. **Update statistics:**
   ```sql
   ANALYZE leads;
   ```

2. **Check index validity:**
   ```sql
   SELECT * FROM validate_performance_indexes();
   ```

3. **Rebuild index if corrupted:**
   ```sql
   REINDEX INDEX CONCURRENTLY idx_leads_created_scored;
   ```

### Issue: High Connection Pool Contention

**Diagnosis:**

```python
health = await db_manager.get_connection_health()
for pool_name, pool_health in health.items():
    if pool_health['pool_efficiency'] < 0.9:
        print(f"Low efficiency: {pool_name} - {pool_health['pool_efficiency']:.1%}")
```

**Solutions:**

1. **Increase pool size temporarily:**
   ```python
   config = DatabaseOptimizationConfig(
       master_pool_size=75,  # Increase further if needed
       replica_pool_size=150
   )
   ```

2. **Optimize connection acquisition:**
   ```python
   # Use connection timeout
   async with asyncio.timeout(5):
       result = await db_manager.execute_query(query)
   ```

3. **Add more read replicas** if read-heavy workload

### Issue: Index Bloat

**Diagnosis:**

```sql
-- Check index bloat
SELECT
    schemaname,
    tablename,
    indexrelname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
    idx_scan
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;
```

**Solutions:**

1. **Rebuild bloated indexes:**
   ```sql
   REINDEX INDEX CONCURRENTLY idx_name;
   ```

2. **Regular maintenance:**
   ```sql
   VACUUM ANALYZE leads;
   VACUUM ANALYZE properties;
   ```

### Issue: Out of Memory During Migration

**Diagnosis:** Large tables causing OOM during index creation

**Solutions:**

1. **Increase maintenance_work_mem:**
   ```sql
   SET maintenance_work_mem = '2GB';
   CREATE INDEX CONCURRENTLY ...;
   ```

2. **Create indexes one at a time** instead of all at once

3. **Run during low-traffic period** to reduce concurrent load

---

## Performance Targets Summary

| Metric | Target | Measurement |
|--------|--------|-------------|
| P90 Query Time | <50ms | 95% of queries under 50ms |
| P95 Query Time | <100ms | 95th percentile under 100ms |
| Connection Pool Efficiency | >90% | Active connections / Total |
| Index Usage Rate | 100% | Critical queries use indexes |
| N+1 Query Patterns | 0 | No loops with queries |
| Cache Hit Rate | >70% | Query result cache effectiveness |

**Validation:**

```bash
# Run comprehensive analysis
python ghl_real_estate_ai/scripts/analyze_query_performance.py --export validation.json

# Check targets met
jq '.performance_targets' validation.json
```

Expected output:
```json
{
  "p90_queries_under_50ms": {
    "target": "100%",
    "actual": "98.5%",
    "status": "✓"
  },
  "connection_pool_efficiency": {
    "target": ">90%",
    "actual": "94.2%",
    "status": "✓"
  },
  "n_plus_one_queries": {
    "target": "0",
    "actual": "0",
    "status": "✓"
  }
}
```

---

## Resources

- **Migration Script:** `ghl_real_estate_ai/scripts/run_performance_migration.sh`
- **Analysis Tool:** `ghl_real_estate_ai/scripts/analyze_query_performance.py`
- **Migration SQL:** `ghl_real_estate_ai/database/migrations/001_performance_indexes.sql`
- **Database Optimizer:** `ghl_real_estate_ai/services/database_optimization.py`

**Next Steps:**

1. Run migration: `./ghl_real_estate_ai/scripts/run_performance_migration.sh`
2. Analyze performance: `python ghl_real_estate_ai/scripts/analyze_query_performance.py`
3. Monitor for 24-48 hours
4. Verify <50ms P90 target achieved
5. Document any remaining slow queries for Phase 2 Week 4
