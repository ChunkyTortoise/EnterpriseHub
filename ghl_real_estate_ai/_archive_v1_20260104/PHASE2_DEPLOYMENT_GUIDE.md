# Phase 2 Deployment Guide
**GHL Real Estate AI - Production Deployment**

Last Updated: January 4, 2026

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Feature-by-Feature Deployment](#feature-by-feature-deployment)
4. [Monitoring & Alerts](#monitoring--alerts)
5. [Security Checklist](#security-checklist)
6. [Rollback Procedures](#rollback-procedures)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- Python 3.9+
- 2GB RAM minimum (4GB recommended)
- 10GB disk space
- SSL certificate for webhook endpoints

### Required Access
- Railway account with Pro plan ($20/month)
- Anthropic API key (Claude access)
- GHL API keys (per tenant/location)
- Domain name (optional but recommended)

### Development Tools
```bash
pip install -r requirements.txt
pip install -r dev-requirements.txt  # For testing
```

---

## Environment Setup

### 1. Core Environment Variables

Create `.env` file (never commit this):

```bash
# Required - API Keys
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxx
GHL_API_KEY=your-ghl-api-key
GHL_LOCATION_ID=your-location-id

# Optional - Agency/Multi-tenant
GHL_AGENCY_API_KEY=your-agency-key  # For multi-tenant
GHL_AGENCY_ID=your-agency-id

# Optional - Advanced Features
DATABASE_URL=postgresql://...  # Auto-provided by Railway
REDIS_URL=redis://...          # For caching/sessions

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### 2. Secure File Permissions

```bash
# Protect sensitive files
chmod 600 .env
chmod 700 data/memory
chmod 700 data/embeddings

# Verify permissions
ls -la .env data/
```

### 3. Run Security Audit

```bash
# Run before each deployment
python scripts/security_audit.py

# Should show 80+ security score
# Address any CRITICAL findings immediately
```

---

## Feature-by-Feature Deployment

### Feature 1: Multi-Tenant Onboarding ✅

**What It Does:** Allows onboarding multiple real estate partners/teams

**Deployment Steps:**

1. **Test Onboarding Script:**
   ```bash
   python scripts/onboard_partner.py
   ```

2. **Onboard First Test Partner:**
   - Partner Name: "Test Partner"
   - Location ID: Use test/staging location
   - Use test API keys

3. **Verify Tenant Isolation:**
   ```bash
   python -m pytest tests/test_security_multitenant.py -v
   ```

4. **Production Onboarding:**
   ```bash
   # For each new partner
   python scripts/onboard_partner.py
   
   # Follow prompts, verify:
   # - Unique location ID
   # - Valid API keys
   # - Calendar ID (if booking appointments)
   ```

**Monitoring:**
- Check `data/tenants/` for tenant files
- Verify each tenant has isolated memory directory
- Test with one conversation per tenant

**Rollback:** Remove tenant file from `data/tenants/{location_id}.json`

---

### Feature 2: Re-engagement Engine ✅

**What It Does:** Auto-follows up with silent leads at 24h, 48h, 72h

**Deployment Steps:**

1. **Configure Triggers:**
   ```python
   # In ghl_utils/config.py (or environment)
   REENGAGEMENT_ENABLED=true
   REENGAGEMENT_INTERVALS="24,48,72"  # hours
   ```

2. **Test Re-engagement Messages:**
   ```bash
   # Dry run (won't send SMS)
   python -c "
   from services.reengagement_engine import ReengagementEngine
   engine = ReengagementEngine('test_location')
   await engine.process_all_silent_leads(dry_run=True)
   "
   ```

3. **Verify SMS Compliance:**
   ```bash
   python -c "
   from prompts.reengagement_templates import validate_all_templates
   validate_all_templates()
   "
   ```
   All messages must be < 160 characters

4. **Schedule Automated Checks:**
   
   **Option A: Cron Job (Railway)**
   ```bash
   # Add to Railway cron or use external scheduler
   0 */6 * * * cd /app && python -c "from services.reengagement_engine import ReengagementEngine; import asyncio; asyncio.run(ReengagementEngine.process_all_tenants())"
   ```
   
   **Option B: Background Worker**
   ```python
   # Create background.py
   import asyncio
   from services.reengagement_engine import ReengagementEngine
   
   async def reengagement_worker():
       while True:
           await ReengagementEngine.process_all_tenants()
           await asyncio.sleep(21600)  # 6 hours
   ```

**Monitoring:**
- Check `data/memory/{location_id}/` for last_reengagement timestamps
- Monitor SMS send rate (should not spam)
- Track conversion rate on re-engaged leads

**Rollback:** 
```bash
REENGAGEMENT_ENABLED=false
```

---

### Feature 3: Analytics Dashboard ✅

**What It Does:** Real-time multi-tenant analytics with charts

**Deployment Steps:**

1. **Generate Mock Data (First Time):**
   ```bash
   python -c "
   from streamlit_demo.analytics import generate_mock_data
   generate_mock_data()
   "
   ```

2. **Test Locally:**
   ```bash
   cd ghl-real-estate-ai
   streamlit run streamlit_demo/analytics.py
   ```
   Open http://localhost:8501

3. **Deploy to Streamlit Cloud:**
   
   a. Push to GitHub:
   ```bash
   git add streamlit_demo/
   git commit -m "Add analytics dashboard"
   git push origin main
   ```
   
   b. Deploy on Streamlit Cloud:
   - Go to https://share.streamlit.io
   - Connect repository
   - Set main file: `ghl-real-estate-ai/streamlit_demo/analytics.py`
   - Add secrets (if needed)
   - Deploy

4. **Custom Domain (Optional):**
   ```
   # In Streamlit Cloud settings
   Custom domain: analytics.yourdomain.com
   ```

**Monitoring:**
- Check dashboard loads in < 3 seconds
- Verify data updates in real-time
- Test filtering by tenant

**Rollback:** Pause Streamlit app from dashboard

---

### Feature 4: Advanced Analytics (A/B Testing) ✅

**What It Does:** Run experiments to optimize conversation strategies

**Deployment Steps:**

1. **Create First Experiment:**
   ```python
   from services.advanced_analytics import ABTestManager
   
   manager = ABTestManager("your_location_id")
   
   exp_id = manager.create_experiment(
       name="Opening Message Test",
       variant_a={"opening": "Hi! Looking for a home?"},
       variant_b={"opening": "Hey there! What can I help you with?"},
       metric="conversion_rate"
   )
   ```

2. **Integrate with Conversation Flow:**
   ```python
   # In api/routes/webhook.py
   from services.advanced_analytics import ABTestManager
   
   ab_manager = ABTestManager(location_id)
   variant = ab_manager.assign_variant(exp_id, contact_id)
   
   # Use variant config in conversation
   ```

3. **Monitor Results:**
   ```python
   analysis = manager.analyze_experiment(exp_id)
   print(analysis["recommendation"])
   ```

4. **Complete Experiment:**
   ```python
   # When you have enough data
   manager.complete_experiment(exp_id)
   ```

**Best Practices:**
- Run experiments for at least 30 conversations per variant
- Only test one variable at a time
- Document winning variants

**Monitoring:**
- Check `data/ab_tests.json` for experiment data
- Review analysis weekly
- Implement winning variants

---

### Feature 5: Monitoring & Alerting ✅

**What It Does:** Tracks performance, errors, and system health

**Deployment Steps:**

1. **Initialize Monitoring:**
   ```python
   from services.monitoring import SystemHealthDashboard
   
   dashboard = SystemHealthDashboard("your_location_id")
   ```

2. **Integrate with API:**
   ```python
   # In api/main.py
   from services.monitoring import PerformanceMonitor, ErrorTracker
   
   monitor = PerformanceMonitor(location_id)
   error_tracker = ErrorTracker(location_id)
   
   @app.middleware("http")
   async def monitor_requests(request, call_next):
       start = time.time()
       try:
           response = await call_next(request)
           duration = (time.time() - start) * 1000
           monitor.record_metric("api_response_time_ms", duration)
           return response
       except Exception as e:
           error_tracker.log_error(
               type(e).__name__,
               str(e),
               context={"path": request.url.path}
           )
           raise
   ```

3. **Set Up Health Check Endpoint:**
   ```python
   @app.get("/health")
   async def health_check():
       dashboard = SystemHealthDashboard(location_id)
       return dashboard.get_dashboard_data()
   ```

4. **Schedule Health Reports:**
   ```bash
   # Daily health report (email/Slack)
   0 9 * * * python -c "
   from services.monitoring import SystemHealthDashboard
   dashboard = SystemHealthDashboard('main')
   report = dashboard.generate_health_report()
   # Send via email/Slack
   "
   ```

**Monitoring:**
- Access `/health` endpoint
- Check `data/metrics/` and `data/errors/`
- Review alerts in `data/metrics/{location_id}/alerts.json`

**Alerting:**
- API response time > 500ms: Warning
- Error rate > 5%: Critical
- Memory usage > 500MB: Warning

---

## Monitoring & Alerts

### Health Check Endpoints

```bash
# System health
curl https://your-app.railway.app/health

# Specific metrics
curl https://your-app.railway.app/metrics/api_response_time
```

### Key Metrics to Monitor

| Metric | Threshold | Action |
|--------|-----------|--------|
| API Response Time | < 500ms | Scale if consistently high |
| Error Rate | < 5% | Investigate errors immediately |
| Memory Usage | < 80% | Optimize or scale up |
| Conversation Success Rate | > 70% | Review conversation logic |
| Re-engagement Conversion | > 15% | Tune message templates |

### Setting Up Alerts

**Option 1: Email Alerts**
```python
from services.monitoring import PerformanceMonitor

monitor = PerformanceMonitor(location_id)
monitor.alert_email = "admin@yourdomain.com"
```

**Option 2: Slack Webhook**
```python
import requests

def send_slack_alert(alert):
    requests.post(
        SLACK_WEBHOOK_URL,
        json={"text": f"🚨 {alert['title']}: {alert['message']}"}
    )
```

---

## Security Checklist

Before deploying to production, verify:

### Pre-Deployment

- [ ] Run security audit: `python scripts/security_audit.py`
- [ ] Security score > 80/100
- [ ] No CRITICAL findings unresolved
- [ ] All environment variables use secrets (no hardcoded keys)
- [ ] File permissions set correctly (600 for .env, 700 for data/)
- [ ] SSL/TLS enabled for all endpoints
- [ ] CORS configured properly
- [ ] Rate limiting implemented
- [ ] Input validation on all user inputs

### Post-Deployment

- [ ] Verify tenant isolation (test cross-tenant access)
- [ ] Test API authentication
- [ ] Review error logs for sensitive data leaks
- [ ] Confirm webhook signature verification
- [ ] Check that PII is not logged
- [ ] Verify data encryption at rest (if implemented)

### Ongoing

- [ ] Weekly security audit
- [ ] Monthly dependency vulnerability scan: `pip-audit`
- [ ] Review access logs for suspicious activity
- [ ] Rotate API keys every 90 days

---

## Rollback Procedures

### Emergency Rollback (< 5 minutes)

```bash
# 1. Stop current deployment
railway down

# 2. Revert to previous version
git revert HEAD
git push origin main

# 3. Redeploy
railway up

# 4. Verify health
curl https://your-app.railway.app/health
```

### Feature-Specific Rollback

**Disable Re-engagement:**
```bash
# Set in Railway environment
REENGAGEMENT_ENABLED=false
railway restart
```

**Disable A/B Testing:**
```python
# Complete all active experiments
from services.advanced_analytics import ABTestManager
manager = ABTestManager(location_id)
for exp in manager.list_active_experiments():
    manager.complete_experiment(exp["id"])
```

**Rollback Analytics Dashboard:**
```bash
# Pause on Streamlit Cloud
# Or remove from Railway if self-hosted
```

---

## Troubleshooting

### Issue: High API Response Time

**Symptoms:** `/health` shows api_response_time > 500ms

**Diagnosis:**
```python
from services.monitoring import PerformanceMonitor
monitor = PerformanceMonitor(location_id)
stats = monitor.get_metric_stats("api_response_time_ms", 60)
print(f"P95: {stats['p95']}ms")
```

**Solutions:**
1. Check database query performance
2. Review LLM API latency
3. Optimize RAG queries
4. Scale up Railway instance

---

### Issue: Re-engagement Not Sending

**Symptoms:** Silent leads not receiving follow-ups

**Diagnosis:**
```bash
# Check last re-engagement run
python -c "
from services.reengagement_engine import ReengagementEngine
engine = ReengagementEngine(location_id)
silent = await engine.scan_for_silent_leads()
print(f'Found {len(silent)} silent leads')
"
```

**Solutions:**
1. Verify `REENGAGEMENT_ENABLED=true`
2. Check GHL API key is valid
3. Review SMS quota/limits
4. Check `data/memory/` has conversation data

---

### Issue: Multi-tenant Data Leak

**Symptoms:** One tenant seeing another's data

**Diagnosis:**
```bash
# Run security tests
python -m pytest tests/test_security_multitenant.py -v
```

**Solutions:**
1. Verify `location_id` passed to all services
2. Check file paths include location_id
3. Review tenant isolation in database queries
4. Audit RAG query filters

---

### Issue: High Error Rate

**Symptoms:** Error rate > 5%

**Diagnosis:**
```python
from services.monitoring import ErrorTracker
tracker = ErrorTracker(location_id)
summary = tracker.get_error_summary(1)
print(summary["top_errors"])
```

**Solutions:**
1. Review top error types
2. Add error handling for common failures
3. Validate inputs more strictly
4. Check third-party API availability

---

## Production Checklist

### Before Going Live

- [ ] All tests passing (140+ tests)
- [ ] Security audit score > 80
- [ ] Performance tested with 100+ concurrent users
- [ ] Monitoring and alerting configured
- [ ] Backup strategy in place
- [ ] Rollback procedure documented and tested
- [ ] On-call rotation established
- [ ] Client training completed

### Go-Live Steps

1. **Morning (9 AM):**
   - Deploy to production
   - Verify health endpoint
   - Test with 3-5 real leads

2. **Midday (12 PM):**
   - Review first batch of conversations
   - Check error logs
   - Monitor performance metrics

3. **Evening (6 PM):**
   - Generate daily health report
   - Review all alerts
   - Plan adjustments for next day

### Post-Launch (Week 1)

- [ ] Daily health report review
- [ ] Monitor re-engagement conversion rates
- [ ] Review A/B test results
- [ ] Collect user feedback
- [ ] Document issues and resolutions
- [ ] Optimize based on real usage patterns

---

## Support & Maintenance

### Daily Tasks
- Review health dashboard
- Check error logs
- Monitor alert counts

### Weekly Tasks
- Run security audit
- Review A/B test results
- Analyze conversation patterns
- Update documentation

### Monthly Tasks
- Dependency updates: `pip list --outdated`
- Security scan: `pip-audit`
- Performance optimization review
- Backup verification

---

## Additional Resources

- **Security Audit:** `python scripts/security_audit.py`
- **Performance Report:** `services/advanced_analytics.py`
- **Health Dashboard:** `/health` endpoint
- **Test Suite:** `pytest tests/ -v`

---

**Questions or Issues?**
- Check `docs/` for detailed documentation
- Review `tests/` for usage examples
- Run security audit for security concerns
- Check monitoring dashboard for performance issues

---

**Last Updated:** January 4, 2026
**Version:** 2.0.0 (Phase 2 Complete)
