# Phase 3 Production Monitoring Setup Guide

**Version:** 1.0.0
**Created:** January 10, 2026
**Status:** Production Ready
**Business Value:** $265K-440K annually

---

## Overview

This guide provides comprehensive setup instructions for monitoring Phase 3 features in production, tracking real business impact, and ensuring SLA compliance.

### Monitored Features

| Feature | Annual Value | Key Metric | Target |
|---------|-------------|------------|--------|
| Real-Time Lead Intelligence | $75K-120K | WebSocket Latency | <50ms (P95) |
| Multimodal Property Intelligence | $75K-150K | Vision Analysis | <1.5s (P95) |
| Proactive Churn Prevention | $55K-80K | Intervention Latency | <30s (P95) |
| AI-Powered Coaching | $60K-90K | Analysis Time | <2s (P95) |

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Metrics Collection](#metrics-collection)
4. [Dashboard Configuration](#dashboard-configuration)
5. [Alert Configuration](#alert-configuration)
6. [Business Impact Tracking](#business-impact-tracking)
7. [A/B Testing Monitoring](#ab-testing-monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

```bash
# Install required packages
pip install prometheus-client redis prometheus-api-client pandas

# Verify services are running
docker-compose -f config/monitoring/docker-compose.monitoring.yml ps
```

### Start Phase 3 Monitoring (5 minutes)

```bash
# 1. Start monitoring stack
cd /Users/cave/enterprisehub
python scripts/monitoring/manage_monitoring.py start

# 2. Start Phase 3 metrics exporter
python -m ghl_real_estate_ai.services.monitoring.phase3_metrics_exporter

# 3. Deploy Grafana dashboards
python scripts/monitoring/manage_monitoring.py deploy-dashboards

# 4. Verify setup
python scripts/monitoring/track_phase3_impact.py --daily
```

**Access Points:**
- Grafana: http://localhost:3000 (admin/enterprisehub_admin)
- Prometheus: http://localhost:9090
- Phase 3 Metrics: http://localhost:8009/metrics

---

## Infrastructure Setup

### 1. Prometheus Configuration

The Phase 3 alert rules are automatically loaded from `config/monitoring/phase3_alerts.yml`.

**Verify Configuration:**

```bash
# Check Prometheus config is valid
promtool check config config/monitoring/prometheus.yml

# Check Phase 3 alert rules
promtool check rules config/monitoring/phase3_alerts.yml

# Reload Prometheus configuration
python scripts/monitoring/manage_monitoring.py reload-prometheus
```

**Key Configuration Elements:**

```yaml
# config/monitoring/prometheus.yml
scrape_configs:
  - job_name: 'phase3-metrics'
    static_configs:
      - targets: ['localhost:8009']
    scrape_interval: 10s  # Real-time monitoring
    labels:
      phase: '3'
      business_value: '265k-440k'

rule_files:
  - "phase3_alerts.yml"  # Phase 3 specific alerts
```

### 2. Phase 3 Metrics Exporter

The metrics exporter runs as a standalone service, collecting real-time data from Redis and PostgreSQL.

**Start Metrics Exporter:**

```bash
# Development
python -m ghl_real_estate_ai.services.monitoring.phase3_metrics_exporter

# Production (with systemd)
sudo systemctl start phase3-metrics-exporter
sudo systemctl enable phase3-metrics-exporter
```

**Systemd Service File:** `/etc/systemd/system/phase3-metrics-exporter.service`

```ini
[Unit]
Description=Phase 3 Metrics Exporter
After=network.target redis.service postgresql.service

[Service]
Type=simple
User=enterprisehub
WorkingDirectory=/opt/enterprisehub
ExecStart=/opt/enterprisehub/venv/bin/python -m ghl_real_estate_ai.services.monitoring.phase3_metrics_exporter
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Health Check:**

```bash
# Verify metrics are being exported
curl http://localhost:8009/metrics | grep phase3_

# Expected output includes:
# - websocket_latency_seconds
# - vision_analysis_duration_seconds
# - churn_intervention_latency_seconds
# - coaching_analysis_duration_seconds
# - phase3_revenue_impact_dollars
```

### 3. Grafana Dashboard Deployment

**Deploy Phase 3 Dashboard:**

```bash
# Automated deployment
python scripts/monitoring/manage_monitoring.py deploy-dashboards

# Manual deployment via Grafana UI
# 1. Go to http://localhost:3000
# 2. Dashboards -> Import
# 3. Upload config/monitoring/grafana/dashboards/phase3_production_monitoring.json
```

**Dashboard Features:**

- Executive summary with total revenue impact
- Per-feature performance metrics
- Real-time latency tracking with targets
- Business impact visualization
- A/B test monitoring
- Cost vs revenue analysis
- NPS scores and adoption rates

**Key Panels:**

1. **Phase 3 Executive Summary** - High-level KPIs
2. **WebSocket Latency** - Real-time intelligence performance
3. **Vision Analysis Time** - Property intelligence performance
4. **Churn Intervention Latency** - Churn prevention performance
5. **Coaching Analysis Time** - AI coaching performance
6. **Revenue by Feature** - Business impact breakdown
7. **Conversion Rate Impact** - A/B test results
8. **Infrastructure Costs** - Cost tracking

---

## Metrics Collection

### Real-Time Metrics

Phase 3 metrics are collected every 10 seconds from:

1. **Application Metrics** (via Prometheus Python client)
2. **Redis** (real-time state and session data)
3. **PostgreSQL** (business analytics and historical data)

### Recording Metrics in Your Application

**Example: Recording WebSocket Latency**

```python
from ghl_real_estate_ai.services.monitoring.phase3_metrics_exporter import (
    get_phase3_metrics_exporter
)

# Get metrics exporter instance
metrics = get_phase3_metrics_exporter()

# Record WebSocket latency
start_time = time.time()
# ... process WebSocket message ...
latency = time.time() - start_time

metrics.record_websocket_latency(
    feature="realtime_intelligence",
    message_type="lead_update",
    latency_seconds=latency
)
```

**Example: Recording Vision Analysis**

```python
# Record Vision API analysis
start_time = time.time()
try:
    result = await claude_vision_analyze(property_image)
    duration = time.time() - start_time

    metrics.record_vision_analysis(
        feature="property_intelligence",
        analysis_type="luxury_detection",
        duration_seconds=duration,
        success=True
    )
except Exception as e:
    duration = time.time() - start_time
    metrics.record_vision_analysis(
        feature="property_intelligence",
        analysis_type="luxury_detection",
        duration_seconds=duration,
        success=False
    )
```

**Example: Recording Churn Intervention**

```python
# Record churn intervention
intervention_start = time.time()
await send_churn_prevention_notification(user_id)
latency = time.time() - intervention_start

metrics.record_churn_intervention(
    feature="churn_prevention",
    intervention_type="high_risk_email",
    latency_seconds=latency
)
```

**Example: Recording Revenue Impact**

```python
# Record revenue impact when conversion happens
if lead_converted:
    estimated_commission = lead.property_price * 0.03  # 3% commission

    metrics.record_revenue_impact(
        feature="realtime_intelligence",
        amount_dollars=estimated_commission
    )
```

### Metric Storage in Redis

Phase 3 uses Redis for real-time metric aggregation:

**Redis Key Patterns:**

```python
# Connection count
redis.set("phase3:realtime:connections", active_connections_count)

# Event bus lag
redis.set("phase3:realtime:event_bus_lag", lag_seconds)

# Data stream health (for 6 streams)
redis.set("phase3:realtime:stream:lead_scoring:health", "1")  # 1=healthy, 0=failed

# Business metrics
redis.set("phase3:business:nps:realtime_intelligence", nps_score)
redis.set("phase3:business:adoption:realtime_intelligence", adoption_rate)
redis.set("phase3:business:conversion_rate_with_phase3", conversion_rate)
```

---

## Dashboard Configuration

### Accessing Dashboards

**Grafana Dashboard:**
- URL: http://localhost:3000
- Username: admin
- Password: enterprisehub_admin (or check GRAFANA_ADMIN_PASSWORD env var)

**Navigate to:**
1. Dashboards → Manage
2. Select "Phase 3 Production Monitoring"

### Dashboard Variables

The Phase 3 dashboard includes template variables for filtering:

- **feature**: Filter by specific Phase 3 feature
- **time_range**: Adjust time window (5m, 15m, 1h, 6h, 24h, 7d)

### Customizing Dashboards

**Add Custom Panel:**

1. Edit dashboard → Add Panel
2. Select Prometheus data source
3. Enter query (examples below)
4. Configure visualization

**Useful Queries:**

```promql
# WebSocket latency P95
histogram_quantile(0.95, rate(websocket_latency_seconds_bucket{feature="realtime_intelligence"}[5m])) * 1000

# Vision analysis success rate
rate(vision_api_requests_total{feature="property_intelligence",status="success"}[5m]) /
rate(vision_api_requests_total{feature="property_intelligence"}[5m]) * 100

# Daily revenue impact
sum(rate(phase3_revenue_impact_dollars[24h])) * 24

# Cost efficiency ratio
sum(rate(phase3_revenue_impact_dollars[24h])) /
(sum(rate(feature_infrastructure_cost_dollars{phase="3"}[24h])) +
 sum(rate(claude_api_cost_dollars[24h])))
```

---

## Alert Configuration

### Alert Severity Levels

Phase 3 alerts are categorized by severity:

| Severity | Response Time | Example |
|----------|--------------|---------|
| **Critical** | Immediate (5-15 min) | Vision API error rate >5%, Service down |
| **Warning** | 1-2 hours | Latency above target, Low adoption |
| **Info** | Next business day | Model retraining, Cache miss rate increase |

### Critical Alerts

**1. Service Availability**

```yaml
# WebSocket latency critically high (>100ms)
- alert: WebSocketLatencyCritical
  severity: critical
  business_impact: critical
  revenue_risk: "$410-660/day"
  action: "Consider emergency rollback"
```

**2. Revenue Impact**

```yaml
# Phase 3 revenue below minimum target
- alert: Phase3RevenueImpactBelowTarget
  severity: warning
  projected_annual: "<$265K"
  action: "Review feature adoption and performance"
```

**3. A/B Test Performance**

```yaml
# A/B test showing significant negative impact
- alert: ABTestNegativeImpact
  severity: critical
  impact: "Feature harming user experience"
  action: "Halt test and rollback feature"
```

### Alert Routing

**AlertManager Configuration:** `config/monitoring/alertmanager.yml`

```yaml
route:
  group_by: ['alertname', 'feature']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 12h
  receiver: 'phase3-team'

  routes:
    # Critical alerts go to PagerDuty
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true

    # Revenue alerts go to business team
    - match_re:
        alertname: '.*Revenue.*|.*ROI.*'
      receiver: 'business-team'

    # Performance alerts go to engineering
    - match_re:
        alertname: '.*Latency.*|.*Performance.*'
      receiver: 'engineering-team'

receivers:
  - name: 'phase3-team'
    slack_configs:
      - channel: '#phase3-alerts'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<PAGERDUTY_SERVICE_KEY>'

  - name: 'business-team'
    email_configs:
      - to: 'business-team@company.com'

  - name: 'engineering-team'
    email_configs:
      - to: 'engineering-team@company.com'
```

### Testing Alerts

```bash
# Test alert rules are valid
promtool check rules config/monitoring/phase3_alerts.yml

# Query active alerts
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.phase=="3")'

# Test AlertManager routing
amtool alert add --alertmanager.url=http://localhost:9093 \
  alertname=TestAlert \
  severity=warning \
  feature=realtime_intelligence
```

---

## Business Impact Tracking

### Daily Impact Reports

**Generate Daily Report:**

```bash
# Console output
python scripts/monitoring/track_phase3_impact.py --daily

# Export to CSV
python scripts/monitoring/track_phase3_impact.py --export-csv --output daily_impact.csv

# Specific feature
python scripts/monitoring/track_phase3_impact.py --feature realtime_intelligence
```

**Sample Output:**

```
================================================================================
PHASE 3 DAILY BUSINESS IMPACT REPORT - 2026-01-10
================================================================================

📊 OVERALL PERFORMANCE
  Daily Revenue:        $1,245.50
  Projected Annual:     $454,607.50
  Target Range:         $265K-440K
  On Track:             ✅ YES
  Overall ROI:          12.3x

👥 USER METRICS
  Active Users:         342
  Average NPS:          54.2
  Average Adoption:     67.3%

💰 COST BREAKDOWN
  Infrastructure:       $45.20/day
  API Costs:            $55.80/day
  Total Costs:          $101.00/day
  Net Impact:           $1,144.50/day

🎯 SLA COMPLIANCE
  Status:               ✅ All SLAs Met

📈 FEATURE BREAKDOWN
Feature                                  Revenue/Day     Projected Annual     Status
------------------------------------------------------------------------------------------
Real-Time Lead Intelligence              $      340.20   $      124,173.00 ✅ On Track
Multimodal Property Intelligence         $      412.80   $      150,672.00 ✅ On Track
Proactive Churn Prevention               $      285.30   $      104,134.50 ✅ On Track
AI-Powered Coaching                      $      207.20   $       75,628.00 ✅ On Track
================================================================================
```

### Weekly Trend Analysis

```bash
python scripts/monitoring/track_phase3_impact.py --weekly
```

**Sample Output:**

```
================================================================================
PHASE 3 WEEKLY TREND ANALYSIS
================================================================================

📊 WEEK-OVER-WEEK CHANGES
  Revenue:              +12.3%
  NPS Score:            +2.4 points
  Adoption Rate:        +5.7%

📈 7-DAY PERFORMANCE
Date         Revenue         NPS      Adoption     SLA Met
------------------------------------------------------------
2026-01-04   $    1,105.20   51.8       61.6% ✅
2026-01-05   $    1,142.30   52.4       63.2% ✅
2026-01-06   $    1,189.50   53.1       64.8% ✅
2026-01-07   $    1,214.80   53.7       65.9% ✅
2026-01-08   $    1,231.20   54.0       66.5% ❌
2026-01-09   $    1,238.90   54.1       67.0% ✅
2026-01-10   $    1,245.50   54.2       67.3% ✅
================================================================================
```

### Automated Reporting

**Setup Cron Job for Daily Reports:**

```bash
# Add to crontab
crontab -e

# Daily report at 9 AM
0 9 * * * cd /Users/cave/enterprisehub && /opt/enterprisehub/venv/bin/python scripts/monitoring/track_phase3_impact.py --daily --export-csv --output /var/reports/phase3_$(date +\%Y\%m\%d).csv

# Weekly report on Mondays
0 9 * * 1 cd /Users/cave/enterprisehub && /opt/enterprisehub/venv/bin/python scripts/monitoring/track_phase3_impact.py --weekly > /var/reports/phase3_weekly_$(date +\%Y\%m\%d).txt
```

### Business Metrics in Code

**Track Conversion Events:**

```python
from ghl_real_estate_ai.services.monitoring.phase3_metrics_exporter import (
    get_phase3_metrics_exporter
)

async def handle_lead_conversion(lead_id: str, property_price: float):
    """Track when a lead converts to a sale."""

    # Calculate revenue impact (3% commission)
    commission = property_price * 0.03

    # Attribute to responsible features
    metrics = get_phase3_metrics_exporter()

    # Check which features were used
    if await was_feature_used(lead_id, "realtime_intelligence"):
        metrics.record_revenue_impact("realtime_intelligence", commission * 0.4)

    if await was_feature_used(lead_id, "property_intelligence"):
        metrics.record_revenue_impact("property_intelligence", commission * 0.3)

    if await was_feature_used(lead_id, "churn_prevention"):
        metrics.record_revenue_impact("churn_prevention", commission * 0.2)

    if await was_feature_used(lead_id, "ai_coaching"):
        metrics.record_revenue_impact("ai_coaching", commission * 0.1)
```

---

## A/B Testing Monitoring

### Setting Up A/B Tests

**Feature Flag Configuration:**

```python
import redis.asyncio as redis

async def setup_ab_test(test_name: str, feature: str,
                       control_percentage: float = 0.5):
    """Configure A/B test for a Phase 3 feature."""

    r = await redis.from_url("redis://localhost:6379/3")

    # Store test configuration
    await r.set(f"phase3:ab_test:{test_name}:config", json.dumps({
        "feature": feature,
        "control_percentage": control_percentage,
        "treatment_percentage": 1 - control_percentage,
        "start_time": datetime.now().isoformat(),
        "metrics": ["conversion_rate", "revenue_per_user", "satisfaction"]
    }))

    # Initialize counters
    await r.set(f"phase3:ab_test:{test_name}:control_size", 0)
    await r.set(f"phase3:ab_test:{test_name}:treatment_size", 0)
```

**User Assignment:**

```python
async def assign_ab_test_group(user_id: str, test_name: str) -> str:
    """Assign user to control or treatment group."""

    r = await redis.from_url("redis://localhost:6379/3")

    # Check if user already assigned
    existing = await r.get(f"phase3:ab_test:{test_name}:user:{user_id}")
    if existing:
        return existing.decode()

    # Get test configuration
    config = json.loads(await r.get(f"phase3:ab_test:{test_name}:config"))

    # Random assignment based on user_id hash
    import hashlib
    hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
    group = "control" if (hash_val % 100) < (config["control_percentage"] * 100) else "treatment"

    # Store assignment
    await r.set(f"phase3:ab_test:{test_name}:user:{user_id}", group)
    await r.incr(f"phase3:ab_test:{test_name}:{group}_size")

    # Record in Prometheus
    from ghl_real_estate_ai.services.monitoring.phase3_metrics_exporter import (
        get_phase3_metrics_exporter
    )
    metrics = get_phase3_metrics_exporter()
    metrics.ab_test_assignments.labels(test_name=test_name, group=group).inc()

    return group
```

### Monitoring A/B Test Results

**View Test Status in Grafana:**

Navigate to "A/B Test Statistical Significance" panel in Phase 3 dashboard.

**Query Test Results:**

```promql
# Control vs Treatment group sizes
ab_test_control_size{test_name="realtime_intelligence_rollout"}
ab_test_treatment_size{test_name="realtime_intelligence_rollout"}

# Performance comparison
ab_test_control_metric{test_name="realtime_intelligence_rollout", metric_name="conversion_rate"}
ab_test_treatment_metric{test_name="realtime_intelligence_rollout", metric_name="conversion_rate"}

# Statistical significance
ab_test_p_value{test_name="realtime_intelligence_rollout"}
```

**Calculate Statistical Significance:**

```python
from scipy import stats

async def calculate_ab_test_significance(test_name: str) -> dict:
    """Calculate statistical significance of A/B test."""

    r = await redis.from_url("redis://localhost:6379/3")

    # Get test data
    control_conversions = int(await r.get(f"phase3:ab_test:{test_name}:control_conversions") or 0)
    control_size = int(await r.get(f"phase3:ab_test:{test_name}:control_size") or 0)
    treatment_conversions = int(await r.get(f"phase3:ab_test:{test_name}:treatment_conversions") or 0)
    treatment_size = int(await r.get(f"phase3:ab_test:{test_name}:treatment_size") or 0)

    # Calculate conversion rates
    control_rate = control_conversions / control_size if control_size > 0 else 0
    treatment_rate = treatment_conversions / treatment_size if treatment_size > 0 else 0

    # Two-proportion z-test
    count = np.array([control_conversions, treatment_conversions])
    nobs = np.array([control_size, treatment_size])
    stat, p_value = proportions_ztest(count, nobs)

    # Store p-value in Redis for Prometheus
    await r.set(f"phase3:ab_test:{test_name}:p_value", p_value)
    await r.set(f"phase3:ab_test:{test_name}:control_metric", control_rate)
    await r.set(f"phase3:ab_test:{test_name}:treatment_metric", treatment_rate)

    return {
        "control_rate": control_rate,
        "treatment_rate": treatment_rate,
        "lift": (treatment_rate - control_rate) / control_rate if control_rate > 0 else 0,
        "p_value": p_value,
        "significant": p_value < 0.05,
        "sample_sizes": {"control": control_size, "treatment": treatment_size}
    }
```

---

## Troubleshooting

### Common Issues

#### 1. Metrics Not Appearing in Grafana

**Symptoms:** Dashboard panels show "No Data"

**Diagnosis:**

```bash
# Check if Phase 3 metrics exporter is running
curl http://localhost:8009/metrics

# Check Prometheus is scraping Phase 3 metrics
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="phase3-metrics")'

# Check for scrape errors
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="phase3-metrics") | .lastError'
```

**Solutions:**

```bash
# Restart Phase 3 metrics exporter
sudo systemctl restart phase3-metrics-exporter

# Reload Prometheus configuration
python scripts/monitoring/manage_monitoring.py reload-prometheus

# Verify network connectivity
telnet localhost 8009
```

#### 2. High Alert Volume

**Symptoms:** Too many alerts firing

**Diagnosis:**

```bash
# Check active alerts
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.phase=="3")'

# Check alert history
python scripts/monitoring/manage_monitoring.py test-alerts
```

**Solutions:**

- Adjust alert thresholds in `config/monitoring/phase3_alerts.yml`
- Increase `for` duration to reduce flapping
- Review alert grouping in AlertManager

#### 3. Missing Business Metrics

**Symptoms:** Revenue impact shows $0 or incorrect values

**Diagnosis:**

```bash
# Check Redis connectivity
redis-cli -n 3 ping

# Verify business metrics in Redis
redis-cli -n 3 keys "phase3:business:*"
redis-cli -n 3 get "phase3:business:conversion_rate_with_phase3"

# Check application is recording metrics
grep "record_revenue_impact" /var/log/enterprisehub/app.log
```

**Solutions:**

- Ensure application code calls `record_revenue_impact()`
- Verify Redis key expiration policies
- Check database connectivity for historical data

#### 4. Dashboard Performance Issues

**Symptoms:** Grafana dashboard loads slowly

**Diagnosis:**

- Check query response times in Grafana
- Review Prometheus query complexity
- Monitor Prometheus resource usage

**Solutions:**

```bash
# Reduce time range or increase refresh interval
# In dashboard settings: Time range: 1h → 6h, Refresh: 10s → 30s

# Optimize slow queries
# Add recording rules in prometheus.yml:
recording_rules:
  - record: phase3:revenue:daily
    expr: sum(rate(phase3_revenue_impact_dollars[24h])) * 24
```

---

## Production Checklist

### Pre-Deployment

- [ ] Monitoring stack running (Prometheus, Grafana, AlertManager)
- [ ] Phase 3 metrics exporter deployed and healthy
- [ ] Grafana dashboards deployed
- [ ] Alert rules validated with `promtool`
- [ ] AlertManager routing configured
- [ ] PagerDuty integration tested (if using)
- [ ] Slack notifications tested
- [ ] Business impact tracking script tested

### Post-Deployment

- [ ] All metrics appearing in Grafana
- [ ] Alerts configured and routing correctly
- [ ] Daily impact reports generating successfully
- [ ] A/B test tracking operational
- [ ] Cost tracking accurate
- [ ] Team trained on dashboard usage
- [ ] Runbook created for common issues
- [ ] On-call rotation established

### Ongoing Operations

- [ ] Review daily impact reports
- [ ] Monitor alert trends
- [ ] Optimize slow queries
- [ ] Update alert thresholds based on actual performance
- [ ] Conduct weekly trend analysis
- [ ] Export monthly reports for stakeholders
- [ ] Review and optimize infrastructure costs

---

## Support and Resources

### Documentation

- **Phase 3 Deployment Guide:** `docs/PHASE_3_PRODUCTION_DEPLOYMENT_STRATEGY.md`
- **Alert Rules:** `config/monitoring/phase3_alerts.yml`
- **Metrics Exporter:** `ghl_real_estate_ai/services/monitoring/phase3_metrics_exporter.py`
- **Impact Tracker:** `scripts/monitoring/track_phase3_impact.py`

### Useful Commands

```bash
# Start/stop monitoring
python scripts/monitoring/manage_monitoring.py start
python scripts/monitoring/manage_monitoring.py stop

# Health check
python scripts/monitoring/manage_monitoring.py health

# Reload configuration
python scripts/monitoring/manage_monitoring.py reload-prometheus

# Deploy dashboards
python scripts/monitoring/manage_monitoring.py deploy-dashboards

# Daily impact report
python scripts/monitoring/track_phase3_impact.py --daily

# Weekly trends
python scripts/monitoring/track_phase3_impact.py --weekly

# Export CSV
python scripts/monitoring/track_phase3_impact.py --export-csv
```

### Getting Help

- **Engineering Team:** #phase3-engineering
- **Business Team:** #phase3-business-impact
- **Alerts Channel:** #phase3-alerts
- **On-Call:** PagerDuty Phase 3 Production service

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-10 | Initial monitoring setup guide |

---

**Status:** ✅ Production Ready
**Next Review:** After 1 week of production monitoring
**Contact:** ops-team@yourcompany.com
