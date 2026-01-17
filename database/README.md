# Service 6 Database Initialization

This directory contains the complete database initialization scripts for the Service 6 Lead Recovery & Nurture Engine.

## Directory Structure

```
database/
├── init/                           # Database initialization scripts (executed by Docker)
│   ├── 01_setup_extensions.sql     # PostgreSQL extensions and custom types
│   ├── 02_create_tables.sql        # Core application tables
│   ├── 03_create_compliance_tables.sql  # GDPR and compliance tables
│   ├── 04_create_monitoring_tables.sql  # System monitoring and error tracking
│   ├── 05_create_indexes.sql       # Performance indexes
│   ├── 06_create_functions_triggers.sql # Stored functions and triggers
│   ├── 07_create_views.sql         # Views and materialized views
│   ├── 08_sample_data.sql          # Sample data (development only)
│   ├── 09_permissions_security.sql # User roles and security configuration
│   └── 10_final_validation.sql     # Validation and optimization
├── migrations/                     # Production migration scripts
│   ├── 001_initial_migration.sql   # Initial schema migration
│   └── 002_sample_data_migration.sql # Sample data (dev/test only)
└── schema.sql                      # Legacy single-file schema
```

## Quick Start

### Docker Compose Automatic Initialization

The database is automatically initialized when using the Service 6 Docker Compose setup:

```bash
# Start with automatic database initialization
docker-compose -f docker-compose.service6.yml up -d postgres

# The init scripts in /database/init/ are automatically executed by PostgreSQL
# in alphabetical order during first container startup
```

### Manual Database Setup

For manual setup or existing PostgreSQL installations:

```bash
# Connect to PostgreSQL as superuser
psql -h localhost -U postgres

# Create database and user
CREATE DATABASE service6_leads;
CREATE USER service6_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE service6_leads TO service6_user;

# Connect to the new database
\c service6_leads

# Run the initialization scripts in order
\i database/init/01_setup_extensions.sql
\i database/init/02_create_tables.sql
\i database/init/03_create_compliance_tables.sql
\i database/init/04_create_monitoring_tables.sql
\i database/init/05_create_indexes.sql
\i database/init/06_create_functions_triggers.sql
\i database/init/07_create_views.sql
\i database/init/08_sample_data.sql        # Development only
\i database/init/09_permissions_security.sql
\i database/init/10_final_validation.sql
```

## Database Schema Overview

### Core Tables

- **leads** - Central lead records with contact information and scoring
- **lead_intelligence** - AI-powered lead scoring and enrichment data
- **communications** - All communication history (email, SMS, calls)
- **nurture_sequences** - Automated follow-up campaign management
- **agents** - Sales team members and performance tracking
- **workflow_executions** - n8n automation workflow tracking

### Compliance & GDPR

- **consent_logs** - GDPR consent tracking with full audit trail
- **data_retention** - Automated data retention and deletion policies
- **data_subject_requests** - GDPR Article 15-22 request management
- **audit_log** - Complete audit trail for accountability
- **processing_activities** - GDPR Article 30 processing register
- **data_breaches** - Incident management and notification tracking

### Monitoring & Operations

- **error_queue** - Error tracking and retry mechanism
- **system_health_checks** - Automated system monitoring
- **performance_metrics** - Detailed performance measurements
- **alerts** - Alert configuration and incident tracking
- **sla_tracking** - Service level agreement monitoring
- **resource_utilization** - System resource monitoring

### Security Features

- **Row Level Security (RLS)** - Agent-based data access control
- **Audit Triggers** - Automatic change tracking for compliance
- **Role-Based Access** - Five distinct user roles with appropriate permissions
- **Data Encryption** - Sensitive data protection at rest

## Environment Configuration

### Development Environment

```bash
# Load with sample data for testing
docker-compose -f docker-compose.service6.yml up -d

# Or manually apply sample data migration
psql -d service6_leads -f database/migrations/002_sample_data_migration.sql
```

### Production Environment

```bash
# Production deployment (no sample data)
export ENVIRONMENT=production
docker-compose -f docker-compose.service6.yml up -d postgres

# Or use production migration
psql -d service6_leads -f database/migrations/001_initial_migration.sql
```

## User Roles and Permissions

| Role | Purpose | Access Level |
|------|---------|--------------|
| `service6_user` | Main application | Full CRUD on application tables |
| `service6_readonly` | Reporting/Analytics | Read-only access to all tables |
| `service6_admin` | Maintenance | Full access for migrations and maintenance |
| `service6_compliance` | GDPR/Audit | Access to compliance and audit data |
| `service6_analytics` | Metrics/BI | Access to metrics and performance data |

## Data Security

### Row Level Security (RLS)

Agents can only access leads assigned to them unless they have manager/admin role:

```sql
-- Set current agent context in application
SELECT set_current_agent('agent_uuid', 'senior');

-- Queries automatically filtered by RLS policies
SELECT * FROM leads; -- Only returns leads assigned to current agent
```

### Audit Logging

All changes to sensitive data are automatically logged:

```sql
-- View audit trail for a specific lead
SELECT * FROM audit_log 
WHERE table_name = 'leads' AND record_id = 'lead_uuid'
ORDER BY created_at DESC;
```

## Performance Optimization

### Indexes

40+ optimized indexes for common query patterns:
- Lead assignment and scoring queries
- Communication effectiveness analysis
- Agent performance metrics
- Time-based data access

### Materialized Views

Pre-aggregated data for performance:
```sql
-- Refresh hourly metrics (automated)
REFRESH MATERIALIZED VIEW mv_hourly_metrics;
```

### Query Optimization

Built-in performance monitoring:
```sql
-- Check query performance
SELECT * FROM analyze_database_performance();

-- Validate schema health
SELECT * FROM validate_schema_health();
```

## Maintenance

### Automated Maintenance

Key maintenance tasks are automated through PostgreSQL functions:

```sql
-- Data retention cleanup (run daily)
SELECT enforce_data_retention();

-- Schema health validation (run weekly)  
SELECT * FROM validate_schema_health();

-- Security configuration check (run monthly)
SELECT * FROM validate_database_security();
```

### Manual Maintenance

```sql
-- Update table statistics
ANALYZE;

-- Refresh materialized views
REFRESH MATERIALIZED VIEW mv_hourly_metrics;

-- Cleanup old audit logs (example: keep 2 years)
DELETE FROM audit_log WHERE created_at < NOW() - INTERVAL '2 years';
```

## Migration Management

### Schema Versions

Track applied migrations:
```sql
-- View migration history
SELECT * FROM schema_migrations ORDER BY applied_at;

-- Current schema version
SELECT version, description FROM schema_versions ORDER BY applied_at DESC LIMIT 1;
```

### Applying New Migrations

1. Test on development environment first
2. Backup production database
3. Apply migration during maintenance window
4. Validate with health checks

```sql
-- Example migration application
\ir database/migrations/003_new_feature.sql

-- Validate after migration
SELECT * FROM validate_complete_setup();
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Check user roles and RLS policies
2. **Performance Issues**: Review index usage and query plans
3. **Data Quality**: Run validation functions
4. **Compliance**: Check audit logs and consent tracking

### Health Checks

```sql
-- Complete system health check
SELECT * FROM v_system_health;

-- Database performance analysis
SELECT * FROM analyze_database_performance();

-- Setup validation
SELECT * FROM validate_complete_setup();
```

### Connection Issues

Check connection limits and active connections:
```sql
-- View active connections
SELECT * FROM pg_stat_activity WHERE state = 'active';

-- Check role connection limits
SELECT rolname, rolconnlimit FROM pg_roles WHERE rolname LIKE 'service6_%';
```

## Support

For database-related issues:

1. Check the setup log: `SELECT * FROM setup_log ORDER BY completed_at;`
2. Run health validation: `SELECT * FROM validate_complete_setup();`
3. Review PostgreSQL logs for errors
4. Consult the Service 6 technical documentation

## Security Notes

⚠️ **Important Security Reminders:**

1. **Change Default Passwords**: All default passwords must be changed in production
2. **SSL/TLS**: Use encrypted connections in production
3. **Firewall**: Restrict database access to application servers only
4. **Backups**: Implement encrypted backup strategy
5. **Monitoring**: Set up alerting for security events

## Performance Benchmarks

Expected performance metrics for Service 6 database:

- **Lead Insertion**: <50ms per lead with enrichment
- **Query Response**: <100ms for dashboard queries
- **Communication Logging**: <25ms per message
- **Scoring Updates**: <200ms per lead rescore
- **Report Generation**: <2s for standard reports

Monitor actual performance with the built-in metrics collection system.
