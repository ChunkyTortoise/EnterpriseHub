#!/bin/bash
# Performance Index Migration Script
# Phase 2 Performance Foundation - Week 3 Quick Wins
#
# This script safely applies performance indexes with minimal downtime
# Target: <50ms P90 query performance

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MIGRATION_FILE="ghl_real_estate_ai/database/migrations/001_performance_indexes.sql"
LOG_FILE="migration_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Performance Index Migration${NC}"
echo -e "${BLUE}Phase 2 Week 3 Quick Wins${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo -e "${RED}ERROR: DATABASE_URL environment variable not set${NC}"
    echo "Please set DATABASE_URL to your PostgreSQL connection string"
    echo "Example: export DATABASE_URL='postgresql://user:pass@localhost:5432/dbname'"
    exit 1
fi

# Extract database name for display (hide credentials)
DB_HOST=$(echo $DATABASE_URL | sed 's/.*@//' | sed 's/\/.*//')
echo -e "Database: ${GREEN}${DB_HOST}${NC}"
echo ""

# Verify migration file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}ERROR: Migration file not found: ${MIGRATION_FILE}${NC}"
    exit 1
fi

echo -e "${YELLOW}Pre-Migration Checks${NC}"
echo "-----------------------------------"

# Check PostgreSQL version
echo -n "Checking PostgreSQL version... "
PG_VERSION=$(psql "$DATABASE_URL" -t -c "SELECT version();" 2>&1)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC}"
    echo "  $PG_VERSION" | head -1
else
    echo -e "${RED}✗${NC}"
    echo "  Could not connect to database"
    exit 1
fi

# Check if pg_stat_statements is enabled (recommended for monitoring)
echo -n "Checking pg_stat_statements extension... "
PG_STAT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM pg_extension WHERE extname = 'pg_stat_statements';" 2>/dev/null)
if [ "$PG_STAT" == "1" ]; then
    echo -e "${GREEN}✓ Enabled${NC}"
else
    echo -e "${YELLOW}⚠ Not enabled (recommended for query monitoring)${NC}"
    echo "  To enable: CREATE EXTENSION pg_stat_statements;"
fi

# Check if PostGIS is available (for spatial indexes)
echo -n "Checking PostGIS extension... "
PG_POSTGIS=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM pg_extension WHERE extname = 'postgis';" 2>/dev/null)
if [ "$PG_POSTGIS" == "1" ]; then
    echo -e "${GREEN}✓ Available${NC}"
else
    echo -e "${YELLOW}⚠ Not available (spatial indexes will use B-tree fallback)${NC}"
fi

# Check current database size
echo -n "Checking database size... "
DB_SIZE=$(psql "$DATABASE_URL" -t -c "SELECT pg_size_pretty(pg_database_size(current_database()));" 2>/dev/null)
echo -e "${GREEN}$DB_SIZE${NC}"

# Check existing indexes count
echo -n "Existing indexes... "
INDEX_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';" 2>/dev/null)
echo -e "${GREEN}$INDEX_COUNT indexes${NC}"

echo ""
echo -e "${YELLOW}Migration Safety Checks${NC}"
echo "-----------------------------------"

# Check for locks that might block migration
echo -n "Checking for blocking locks... "
LOCKS=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM pg_locks WHERE NOT granted;" 2>/dev/null)
if [ "$LOCKS" == "0" ]; then
    echo -e "${GREEN}✓ No blocking locks${NC}"
else
    echo -e "${YELLOW}⚠ $LOCKS blocking locks detected${NC}"
    echo "  Consider running during low-traffic period"
fi

# Check available disk space (indexes require additional space)
echo -n "Estimating required disk space... "
ESTIMATED_SIZE=$(psql "$DATABASE_URL" -t -c "
    SELECT pg_size_pretty(
        (SELECT SUM(pg_total_relation_size(tablename::regclass))
         FROM pg_tables
         WHERE schemaname = 'public'
           AND tablename IN ('leads', 'properties', 'conversations', 'property_interactions')) * 0.2
    );
" 2>/dev/null)
echo -e "${GREEN}~$ESTIMATED_SIZE (20% of table sizes)${NC}"

echo ""
echo -e "${BLUE}Starting Migration${NC}"
echo "-----------------------------------"

# Confirmation prompt
echo -e "${YELLOW}This migration will:${NC}"
echo "  • Create 16 new performance indexes"
echo "  • Use CONCURRENTLY to avoid locking tables"
echo "  • Target: <50ms P90 query performance"
echo "  • Estimated time: 2-10 minutes depending on data size"
echo ""
read -p "Continue with migration? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Migration cancelled${NC}"
    exit 0
fi

# Execute migration
echo ""
echo -e "${GREEN}Executing migration...${NC}"
echo "Logging to: $LOG_FILE"
echo ""

START_TIME=$(date +%s)

# Run migration with logging
psql "$DATABASE_URL" -f "$MIGRATION_FILE" 2>&1 | tee "$LOG_FILE"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo ""
    echo -e "${GREEN}======================================${NC}"
    echo -e "${GREEN}Migration Completed Successfully!${NC}"
    echo -e "${GREEN}======================================${NC}"
    echo "Duration: ${DURATION}s"
    echo "Log file: $LOG_FILE"
else
    echo ""
    echo -e "${RED}======================================${NC}"
    echo -e "${RED}Migration Failed${NC}"
    echo -e "${RED}======================================${NC}"
    echo "Check log file: $LOG_FILE"
    exit 1
fi

# Post-migration validation
echo ""
echo -e "${YELLOW}Post-Migration Validation${NC}"
echo "-----------------------------------"

# Count new indexes
echo -n "New indexes created... "
NEW_INDEX_COUNT=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';" 2>/dev/null)
NEW_INDEXES=$((NEW_INDEX_COUNT - INDEX_COUNT))
echo -e "${GREEN}$NEW_INDEXES${NC}"

# Run validation function
echo ""
echo "Running index validation..."
psql "$DATABASE_URL" -c "SELECT * FROM validate_performance_indexes();" 2>/dev/null

# Check index sizes
echo ""
echo "Index size summary:"
psql "$DATABASE_URL" -c "
    SELECT
        tablename,
        COUNT(*) as index_count,
        pg_size_pretty(SUM(pg_relation_size(indexname::regclass))) as total_index_size
    FROM pg_indexes
    WHERE schemaname = 'public'
      AND tablename IN ('leads', 'properties', 'conversations', 'property_interactions')
    GROUP BY tablename
    ORDER BY tablename;
" 2>/dev/null

echo ""
echo -e "${BLUE}Next Steps${NC}"
echo "-----------------------------------"
echo "1. Monitor query performance: python scripts/analyze_query_performance.py"
echo "2. Run ANALYZE to update statistics: psql \$DATABASE_URL -c 'ANALYZE;'"
echo "3. Test critical queries with EXPLAIN ANALYZE"
echo "4. Monitor index usage over next 24-48 hours"
echo "5. Verify P90 query performance <50ms target"
echo ""

# Offer to run query analysis
read -p "Run query performance analysis now? (yes/no): " RUN_ANALYSIS

if [ "$RUN_ANALYSIS" == "yes" ]; then
    echo ""
    echo -e "${GREEN}Running query performance analysis...${NC}"
    python ghl_real_estate_ai/scripts/analyze_query_performance.py --export performance_report.json
    echo ""
    echo -e "${GREEN}Analysis complete! Report saved to performance_report.json${NC}"
fi

echo ""
echo -e "${GREEN}Migration process complete!${NC}"
