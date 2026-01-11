#!/bin/bash
# PostgreSQL Read Replica Setup Script for EnterpriseHub
# Sets up streaming replication for high availability

set -e

echo "Setting up PostgreSQL read replica..."

# Wait for master to be ready
echo "Waiting for master PostgreSQL to be ready..."
until pg_isready -h postgres -p 5432 -U "${POSTGRES_USER}"; do
    echo "Master not ready, waiting..."
    sleep 2
done

echo "Master is ready. Setting up replication..."

# Stop PostgreSQL if running
pg_ctl stop -D "$PGDATA" -m fast || true

# Remove existing data directory
rm -rf "$PGDATA"/*

# Create base backup from master
echo "Creating base backup from master..."
PGPASSWORD="$POSTGRES_REPLICATION_PASSWORD" pg_basebackup \
    -h postgres \
    -D "$PGDATA" \
    -U "$POSTGRES_REPLICATION_USER" \
    -W \
    -v \
    -P \
    -R \
    -X stream

# Set proper permissions
chmod 0700 "$PGDATA"

# Create recovery configuration for replica
cat > "$PGDATA/postgresql.auto.conf" << EOF
# Replica-specific configuration
hot_standby = on
max_standby_archive_delay = 30s
max_standby_streaming_delay = 30s
wal_receiver_status_interval = 10s
hot_standby_feedback = on
wal_receiver_timeout = 60s
primary_conninfo = 'host=postgres port=5432 user=$POSTGRES_REPLICATION_USER password=$POSTGRES_REPLICATION_PASSWORD'
EOF

# Create standby.signal file to indicate this is a standby server
touch "$PGDATA/standby.signal"

echo "PostgreSQL replica setup completed!"
echo "Starting replica in standby mode..."

# Start PostgreSQL in replica mode
exec postgres -D "$PGDATA"