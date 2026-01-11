#!/usr/bin/env python3
"""
Setup Business Impact Tracking Database (SQLite version for local testing)
Converts PostgreSQL schema to SQLite for Phase 3 local deployment
"""

import sqlite3
import os
from datetime import datetime

def setup_business_db():
    """Set up SQLite database with business impact tracking tables"""

    # Create database connection
    db_path = "business_impact_tracking.db"
    if os.path.exists(db_path):
        print(f"📊 Database exists: {db_path}")
    else:
        print(f"📊 Creating new database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🏗️  Creating business impact tracking tables...")

    # Core tracking tables (SQLite compatible)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS business_metrics_daily (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL UNIQUE,
        tenant_id VARCHAR(50),

        -- Overall Platform Metrics
        total_leads_processed INTEGER DEFAULT 0,
        total_revenue_impact DECIMAL(12,2) DEFAULT 0,
        total_operating_cost DECIMAL(10,2) DEFAULT 0,
        net_roi_percentage DECIMAL(8,4) DEFAULT 0,

        -- Feature Adoption Rates
        real_time_intelligence_adoption_rate DECIMAL(5,4) DEFAULT 0,
        property_vision_adoption_rate DECIMAL(5,4) DEFAULT 0,
        churn_prevention_adoption_rate DECIMAL(5,4) DEFAULT 0,
        ai_coaching_adoption_rate DECIMAL(5,4) DEFAULT 0,

        -- Performance Metrics
        websocket_avg_latency_ms DECIMAL(8,3) DEFAULT 0,
        ml_inference_avg_latency_ms DECIMAL(8,3) DEFAULT 0,
        vision_analysis_avg_time_ms DECIMAL(10,3) DEFAULT 0,
        coaching_analysis_avg_time_ms DECIMAL(8,3) DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lead_intelligence_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        tenant_id VARCHAR(50),

        -- Core Metrics
        leads_processed INTEGER DEFAULT 0,
        avg_response_time_minutes DECIMAL(8,2) DEFAULT 0,
        conversion_rate_improvement DECIMAL(5,4) DEFAULT 0,
        agent_productivity_improvement DECIMAL(5,4) DEFAULT 0,

        -- Financial Impact
        estimated_revenue_impact DECIMAL(10,2) DEFAULT 0,
        cost_savings DECIMAL(8,2) DEFAULT 0,
        roi_percentage DECIMAL(8,4) DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS property_intelligence_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        tenant_id VARCHAR(50),

        -- Core Metrics
        property_analyses_completed INTEGER DEFAULT 0,
        avg_analysis_time_seconds DECIMAL(8,2) DEFAULT 0,
        accuracy_improvement DECIMAL(5,4) DEFAULT 0,

        -- Financial Impact
        estimated_value_accuracy_improvement DECIMAL(5,4) DEFAULT 0,
        time_savings_hours DECIMAL(8,2) DEFAULT 0,
        cost_savings DECIMAL(8,2) DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS churn_prevention_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        tenant_id VARCHAR(50),

        -- Core Metrics
        clients_analyzed INTEGER DEFAULT 0,
        churn_risks_identified INTEGER DEFAULT 0,
        successful_interventions INTEGER DEFAULT 0,
        churn_reduction_rate DECIMAL(5,4) DEFAULT 0,

        -- Financial Impact
        revenue_retention DECIMAL(12,2) DEFAULT 0,
        intervention_cost DECIMAL(8,2) DEFAULT 0,
        roi_percentage DECIMAL(8,4) DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_coaching_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        tenant_id VARCHAR(50),

        -- Core Metrics
        coaching_sessions INTEGER DEFAULT 0,
        avg_session_duration_minutes DECIMAL(8,2) DEFAULT 0,
        agent_skill_improvement DECIMAL(5,4) DEFAULT 0,

        -- Financial Impact
        productivity_improvement DECIMAL(5,4) DEFAULT 0,
        training_cost_reduction DECIMAL(8,2) DEFAULT 0,
        estimated_revenue_impact DECIMAL(10,2) DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operating_costs_daily (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        tenant_id VARCHAR(50),

        -- Infrastructure Costs
        hosting_cost DECIMAL(8,2) DEFAULT 0,
        api_usage_cost DECIMAL(8,2) DEFAULT 0,
        storage_cost DECIMAL(6,2) DEFAULT 0,

        -- Operational Costs
        support_cost DECIMAL(8,2) DEFAULT 0,
        maintenance_cost DECIMAL(6,2) DEFAULT 0,
        development_cost DECIMAL(8,2) DEFAULT 0,

        total_daily_cost DECIMAL(10,2) DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roi_weekly_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        week_start_date DATE NOT NULL,
        week_end_date DATE NOT NULL,
        tenant_id VARCHAR(50),

        -- Summary Metrics
        total_revenue_impact DECIMAL(12,2) DEFAULT 0,
        total_cost_savings DECIMAL(10,2) DEFAULT 0,
        total_operating_costs DECIMAL(10,2) DEFAULT 0,
        net_roi_percentage DECIMAL(8,4) DEFAULT 0,

        -- Feature Breakdown
        lead_intelligence_roi DECIMAL(8,4) DEFAULT 0,
        property_intelligence_roi DECIMAL(8,4) DEFAULT 0,
        churn_prevention_roi DECIMAL(8,4) DEFAULT 0,
        ai_coaching_roi DECIMAL(8,4) DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feature_rollout_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feature_name VARCHAR(100) NOT NULL,
        rollout_date DATE NOT NULL,
        tenant_id VARCHAR(50),

        -- Adoption Metrics
        target_adoption_rate DECIMAL(5,4) DEFAULT 0,
        current_adoption_rate DECIMAL(5,4) DEFAULT 0,
        active_users INTEGER DEFAULT 0,
        total_eligible_users INTEGER DEFAULT 0,

        -- Performance Metrics
        avg_performance_score DECIMAL(5,4) DEFAULT 0,
        error_rate DECIMAL(5,4) DEFAULT 0,
        user_satisfaction_score DECIMAL(3,2) DEFAULT 0,

        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS business_impact_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_type VARCHAR(50) NOT NULL,
        severity VARCHAR(20) NOT NULL,
        message TEXT NOT NULL,

        -- Context
        feature_name VARCHAR(100),
        metric_value DECIMAL(15,4),
        threshold_value DECIMAL(15,4),
        tenant_id VARCHAR(50),

        -- Status
        status VARCHAR(20) DEFAULT 'active',
        acknowledged_at TIMESTAMP,
        resolved_at TIMESTAMP,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Create views for quick summaries
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS daily_roi_summary AS
    SELECT
        date,
        total_leads_processed,
        total_revenue_impact,
        total_operating_cost,
        (total_revenue_impact - total_operating_cost) / total_operating_cost * 100 AS roi_percentage,
        (real_time_intelligence_adoption_rate +
         property_vision_adoption_rate +
         churn_prevention_adoption_rate +
         ai_coaching_adoption_rate) / 4 AS avg_adoption_rate
    FROM business_metrics_daily
    ORDER BY date DESC;
    """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS feature_performance_summary AS
    SELECT
        feature_name,
        current_adoption_rate,
        avg_performance_score,
        error_rate,
        user_satisfaction_score,
        status
    FROM feature_rollout_tracking
    WHERE status = 'active'
    ORDER BY current_adoption_rate DESC;
    """)

    cursor.execute("""
    CREATE VIEW IF NOT EXISTS business_impact_health AS
    SELECT
        COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_alerts,
        COUNT(CASE WHEN severity = 'warning' THEN 1 END) as warning_alerts,
        COUNT(CASE WHEN status = 'active' THEN 1 END) as active_alerts,
        COUNT(*) as total_alerts
    FROM business_impact_alerts
    WHERE created_at >= datetime('now', '-24 hours');
    """)

    # Insert sample data for testing
    print("📊 Inserting sample data...")

    today = datetime.now().strftime('%Y-%m-%d')

    cursor.execute("""
    INSERT OR REPLACE INTO business_metrics_daily (
        date, tenant_id, total_leads_processed, total_revenue_impact,
        total_operating_cost, net_roi_percentage,
        real_time_intelligence_adoption_rate, property_vision_adoption_rate,
        churn_prevention_adoption_rate, ai_coaching_adoption_rate,
        websocket_avg_latency_ms, ml_inference_avg_latency_ms
    ) VALUES (?, 'default', 150, 25000.00, 3500.00, 614.29, 0.87, 0.92, 0.78, 0.85, 45.2, 125.8)
    """, (today,))

    cursor.execute("""
    INSERT OR REPLACE INTO feature_rollout_tracking (
        feature_name, rollout_date, tenant_id, target_adoption_rate,
        current_adoption_rate, active_users, total_eligible_users,
        avg_performance_score, error_rate, user_satisfaction_score, status
    ) VALUES
        ('Real-Time Intelligence', ?, 'default', 0.90, 0.87, 43, 50, 0.98, 0.02, 4.6, 'active'),
        ('Property Vision Analysis', ?, 'default', 0.85, 0.92, 46, 50, 0.95, 0.01, 4.8, 'active'),
        ('Churn Prevention Engine', ?, 'default', 0.80, 0.78, 39, 50, 0.94, 0.03, 4.5, 'active'),
        ('AI Coaching System', ?, 'default', 0.85, 0.85, 42, 50, 0.96, 0.02, 4.7, 'active')
    """, (today, today, today, today))

    conn.commit()

    # Test the database
    print("🔍 Testing database connection...")
    cursor.execute("SELECT COUNT(*) FROM business_metrics_daily")
    daily_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM feature_rollout_tracking")
    feature_count = cursor.fetchone()[0]

    print(f"✅ Database setup complete!")
    print(f"   📊 Daily metrics records: {daily_count}")
    print(f"   🚀 Feature tracking records: {feature_count}")
    print(f"   📍 Database location: {os.path.abspath(db_path)}")

    conn.close()

    return True

if __name__ == "__main__":
    setup_business_db()