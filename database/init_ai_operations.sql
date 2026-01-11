
-- Create AI Operations Database Schema
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Metrics table for time-series data
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    service_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    value DOUBLE PRECISION NOT NULL,
    tags JSONB DEFAULT '{}',
    anomaly_score DOUBLE PRECISION DEFAULT NULL,
    is_anomaly BOOLEAN DEFAULT FALSE
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('metrics', 'timestamp', if_not_exists => TRUE);

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    service_name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ DEFAULT NULL
);

-- Scaling decisions table
CREATE TABLE IF NOT EXISTS scaling_decisions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    service_name VARCHAR(100) NOT NULL,
    action VARCHAR(20) NOT NULL, -- scale_up, scale_down, no_action
    current_instances INTEGER NOT NULL,
    target_instances INTEGER NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    cost_impact DOUBLE PRECISION DEFAULT 0
);

-- Incidents table for self-healing
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    service_name VARCHAR(100) NOT NULL,
    incident_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'open', -- open, resolved, escalated
    resolution_time_seconds INTEGER DEFAULT NULL,
    auto_resolved BOOLEAN DEFAULT FALSE,
    resolution_action TEXT DEFAULT NULL
);

-- Performance predictions table
CREATE TABLE IF NOT EXISTS performance_predictions (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    service_name VARCHAR(100) NOT NULL,
    prediction_horizon_minutes INTEGER NOT NULL,
    predicted_bottleneck VARCHAR(100) DEFAULT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    recommended_action TEXT DEFAULT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_metrics_service_time ON metrics(service_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_service_time ON alerts(service_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_scaling_service_time ON scaling_decisions(service_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_service_time ON incidents(service_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_service_time ON performance_predictions(service_name, timestamp DESC);

-- Create retention policies (keep 90 days of detailed data, 1 year of aggregated)
SELECT add_retention_policy('metrics', INTERVAL '90 days', if_not_exists => TRUE);

-- Create continuous aggregates for performance
CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS hour,
    service_name,
    metric_name,
    AVG(value) AS avg_value,
    MAX(value) AS max_value,
    MIN(value) AS min_value,
    COUNT(*) AS data_points,
    COUNT(*) FILTER (WHERE is_anomaly = TRUE) AS anomaly_count
FROM metrics
GROUP BY hour, service_name, metric_name;

SELECT add_continuous_aggregate_policy('metrics_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Create users and permissions
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ai_operations_app') THEN
        CREATE USER ai_operations_app WITH PASSWORD 'secure_production_password';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE ai_operations TO ai_operations_app;
GRANT USAGE ON SCHEMA public TO ai_operations_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO ai_operations_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ai_operations_app;

-- Grant permissions on hypertables and continuous aggregates
GRANT SELECT ON metrics_hourly TO ai_operations_app;

COMMIT;
