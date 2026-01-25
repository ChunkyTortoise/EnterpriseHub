#!/bin/bash

# Jorge's BI Dashboard Database Backup Script
# Automated backup for OLAP data warehouse

# Configuration
DB_NAME="enterprise_hub"
DB_HOST="localhost"
DB_USER="cave"
BACKUP_DIR="/Users/cave/Documents/GitHub/EnterpriseHub/infrastructure/backups"
DATE=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=30

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Full database backup
echo "Starting database backup for $DB_NAME..."
/opt/homebrew/Cellar/postgresql@17/17.7_1/bin/pg_dump \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=custom \
    --compress=9 \
    --verbose \
    --file="$BACKUP_DIR/jorge_bi_full_backup_$DATE.dump"

if [ $? -eq 0 ]; then
    echo "Full backup completed successfully: jorge_bi_full_backup_$DATE.dump"
else
    echo "ERROR: Full backup failed!"
    exit 1
fi

# OLAP schema only backup (lighter, faster restore)
echo "Creating OLAP schema backup..."
/opt/homebrew/Cellar/postgresql@17/17.7_1/bin/pg_dump \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=custom \
    --compress=9 \
    --verbose \
    --schema-only \
    --file="$BACKUP_DIR/jorge_bi_schema_$DATE.dump"

if [ $? -eq 0 ]; then
    echo "Schema backup completed successfully: jorge_bi_schema_$DATE.dump"
else
    echo "ERROR: Schema backup failed!"
fi

# Data-only backup for OLAP tables
echo "Creating OLAP data backup..."
/opt/homebrew/Cellar/postgresql@17/17.7_1/bin/pg_dump \
    -h "$DB_HOST" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=custom \
    --compress=9 \
    --verbose \
    --data-only \
    --table=fact_lead_interactions \
    --table=fact_commission_events \
    --table=fact_bot_performance \
    --table=agg_daily_metrics \
    --table=agg_hourly_metrics \
    --file="$BACKUP_DIR/jorge_bi_olap_data_$DATE.dump"

if [ $? -eq 0 ]; then
    echo "OLAP data backup completed successfully: jorge_bi_olap_data_$DATE.dump"
else
    echo "ERROR: OLAP data backup failed!"
fi

# Cleanup old backups (retain only last 30 days)
echo "Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "jorge_bi_*.dump" -mtime +$RETENTION_DAYS -delete

# Display backup summary
echo ""
echo "=== BACKUP SUMMARY ==="
echo "Database: $DB_NAME"
echo "Date: $DATE"
echo "Backup Directory: $BACKUP_DIR"
ls -lah "$BACKUP_DIR"/jorge_bi_*"$DATE"*.dump
echo ""
echo "Total backup files: $(ls "$BACKUP_DIR"/jorge_bi_*.dump | wc -l)"
echo "Disk usage: $(du -sh "$BACKUP_DIR" | cut -f1)"
echo "=== BACKUP COMPLETE ==="