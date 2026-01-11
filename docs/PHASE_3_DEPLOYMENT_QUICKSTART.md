# Phase 3 Production Deployment - Quick Start Guide

**Version:** 1.0.0
**Last Updated:** January 10, 2026
**Estimated Time:** 2-3 hours for initial deployment

---

## Overview

This guide provides step-by-step instructions for deploying all Phase 3 features to production. Follow these steps in order for a successful deployment.

### What You'll Deploy

- **4 Backend Services** on Railway (WebSocket, ML, Coaching, Churn)
- **4 Frontend Dashboards** on Vercel (Intelligence, Coaching, Property, Analytics)
- **Database Schema** for tracking and analytics
- **Redis Configuration** for caching and feature flags
- **Monitoring Setup** for performance tracking

### Prerequisites

Before starting, ensure you have:

- [x] Railway account and CLI installed (`npm install -g @railway/cli`)
- [x] Vercel account and CLI installed (`npm install -g vercel`)
- [x] PostgreSQL database provisioned (or will create on Railway)
- [x] Redis instance provisioned (or will create on Railway)
- [x] Required API keys:
  - Anthropic API key (for Claude services)
  - GoHighLevel API key (for CRM integration)
- [x] Environment variables prepared (see below)
- [x] Python 3.11+ installed locally for scripts

---

## Environment Setup

### Required Environment Variables

Create a `.env.production` file with these variables:

```bash
# Core Infrastructure
ENVIRONMENT=production
DEPLOYMENT_ENV=production

# Database (Railway will provide this)
DATABASE_URL=postgresql://user:pass@host:5432/database

# Redis (Railway will provide this)
REDIS_URL=redis://host:6379/0

# API Keys
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
GHL_API_KEY=xxxxx

# Performance Targets
WEBSOCKET_TARGET_LATENCY_MS=50
ML_INFERENCE_TARGET_MS=35
VISION_ANALYSIS_TARGET_MS=1500
CHURN_INTERVENTION_TARGET_S=30
COACHING_ANALYSIS_TARGET_MS=2000

# Monitoring (optional but recommended)
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxxxx

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)
```

### Export Variables for Deployment

```bash
# Load environment variables
export $(cat .env.production | xargs)

# Verify all required variables are set
python scripts/verify_environment.py
```

---

## Step-by-Step Deployment

### Step 1: Deploy Railway Backend (30-45 minutes)

Deploy all backend services to Railway:

```bash
# Navigate to project directory
cd /Users/cave/enterprisehub

# Run Railway deployment script
./scripts/deploy_railway_backend.sh production
```

This script will:
- ✅ Verify Railway CLI authentication
- ✅ Link project to Railway
- ✅ Create Dockerfiles for each service
- ✅ Deploy WebSocket Manager
- ✅ Deploy ML Services
- ✅ Deploy Coaching Engine
- ✅ Deploy Churn Orchestrator
- ✅ Run database migrations
- ✅ Initialize Redis configuration

**Expected Output:**
```
==========================================
Deployment Complete!
==========================================

Next steps:
1. Verify all services: railway status --environment production
2. View logs: railway logs --environment production
3. Enable features: python scripts/set_feature_rollout.py --status
```

**Troubleshooting:**
- If deployment fails, check logs: `railway logs --service <service-name>`
- Verify environment variables: `railway variables --environment production`
- Ensure database is accessible: `python scripts/test_database_connection.py`

### Step 2: Deploy Vercel Frontend (15-20 minutes)

Deploy Streamlit dashboards to Vercel:

```bash
# Run Vercel deployment script
./scripts/deploy_vercel_frontend.sh production
```

This script will:
- ✅ Verify Vercel CLI authentication
- ✅ Link project to Vercel
- ✅ Create vercel.json configuration
- ✅ Set environment variables
- ✅ Deploy all dashboard components
- ✅ Provide deployment URLs

**Expected Output:**
```
==========================================
Frontend Deployed Successfully!
==========================================

Dashboard URLs:
  Intelligence Hub:    https://your-app.vercel.app/intelligence
  Coaching Dashboard:  https://your-app.vercel.app/coaching
  Property Intel:      https://your-app.vercel.app/property-intelligence
  Analytics:           https://your-app.vercel.app/analytics
```

**Troubleshooting:**
- If build fails, check Vercel logs: `vercel logs`
- Verify environment variables: `vercel env ls production`
- Test locally first: `streamlit run ghl_real_estate_ai/streamlit_components/realtime_lead_intelligence_hub.py`

### Step 3: Verify Infrastructure (10-15 minutes)

Run comprehensive infrastructure verification:

```bash
# Run verification script
./scripts/verify_infrastructure.sh production
```

This script will check:
- ✅ Railway service health endpoints
- ✅ Vercel frontend accessibility
- ✅ Database connectivity
- ✅ Redis connectivity
- ✅ Feature flag configuration
- ✅ Monitoring setup

**Expected Output:**
```
==========================================
✓ All Infrastructure Checks Passed
==========================================

System is ready for production traffic!

Next steps:
1. Enable features: python scripts/set_feature_rollout.py --percentage 10 --all-features
2. Monitor dashboards: Check Grafana/Railway logs
3. Begin A/B testing with 10% rollout
```

**If Checks Fail:**
- Review error messages carefully
- Fix issues before proceeding
- Re-run verification after fixes

### Step 4: Enable Features with 10% Rollout (5 minutes)

Start with conservative 10% rollout for validation:

```bash
# Enable all features at 10%
python scripts/set_feature_rollout.py --percentage 10 --all-features

# Verify feature flags
python scripts/set_feature_rollout.py --status
```

**Expected Output:**
```
============================================================
PHASE 3 FEATURE ROLLOUT STATUS
============================================================

✅ Realtime Intelligence
   Enabled: True
   Rollout: 10%
   Updated: 2026-01-10T12:00:00

✅ Property Vision
   Enabled: True
   Rollout: 10%
   Updated: 2026-01-10T12:00:00

✅ Churn Prevention
   Enabled: True
   Rollout: 10%
   Updated: 2026-01-10T12:00:00

✅ AI Coaching
   Enabled: True
   Rollout: 10%
   Updated: 2026-01-10T12:00:00
```

### Step 5: Monitor Initial Performance (24-48 hours)

Monitor system performance for 24-48 hours before expanding rollout:

**Key Metrics to Watch:**

1. **Performance Metrics:**
   ```bash
   # Check performance in real-time
   railway logs --environment production | grep "latency"

   # Or use monitoring dashboard
   open https://railway.app/project/<your-project>/metrics
   ```

   Target Latencies:
   - WebSocket: <50ms (P95)
   - ML Inference: <35ms (P95)
   - Vision Analysis: <1.5s (P95)
   - Churn Intervention: <30s (avg)
   - Coaching Analysis: <2s (avg)

2. **Business Impact:**
   ```bash
   # Generate daily impact report
   python scripts/calculate_business_impact.py --yesterday

   # View in dashboard
   streamlit run streamlit_components/phase3_roi_dashboard.py
   ```

3. **Error Rates:**
   ```bash
   # Check error rates
   railway logs --environment production | grep "ERROR"

   # Target: <1% error rate
   ```

**Success Criteria for Week 1:**
- [ ] All performance targets met
- [ ] No critical errors or crashes
- [ ] User satisfaction >80%
- [ ] Feature usage >50% of enabled tenants

---

## Progressive Rollout Schedule

### Week 1: 10% Validation
- **Days 1-2:** Deploy and monitor
- **Days 3-5:** Validate performance
- **Days 6-7:** Analyze initial business impact

**Go/No-Go Decision:** Review metrics, proceed if all targets met

### Week 2: 25% Expansion
```bash
# Expand to 25%
python scripts/set_feature_rollout.py --percentage 25 --all-features
```

Monitor for 5-7 days, validate business impact

### Week 3: 50% Expansion
```bash
# Expand to 50%
python scripts/set_feature_rollout.py --percentage 50 --all-features
```

Monitor for 5-7 days, validate ROI

### Week 4: 100% Full Release
```bash
# Full rollout
python scripts/set_feature_rollout.py --percentage 100 --all-features
```

Monitor continuously, document final business impact

---

## Monitoring & Dashboards

### Real-Time Monitoring

**Railway Logs:**
```bash
# All services
railway logs --environment production

# Specific service
railway logs --service websocket-manager --environment production

# Follow logs
railway logs --environment production --follow
```

**Performance Dashboard:**
```bash
# Open Railway metrics
open https://railway.app/project/<your-project>/metrics
```

**Business Impact Dashboard:**
```bash
# Local Streamlit dashboard
streamlit run ghl_real_estate_ai/streamlit_components/phase3_roi_dashboard.py

# Or access deployed version
open https://your-app.vercel.app/analytics
```

### Automated Alerts

Alerts are configured for:
- Performance degradation (latency >2x target)
- Error rate spikes (>5%)
- Feature usage drops (>50% decrease)
- Churn intervention failures

Alerts sent to:
- Slack: #phase3-alerts
- Email: ops-team@yourcompany.com
- PagerDuty: Phase 3 Production service

---

## Rollback Procedures

If issues are detected:

### Emergency Rollback (Disable All Features)

```bash
# Immediate disable
python scripts/set_feature_rollout.py --disable --all-features

# Verify
python scripts/set_feature_rollout.py --status
```

### Specific Feature Rollback

```bash
# Disable specific feature
python scripts/set_feature_rollout.py --feature churn_prevention --disable

# Verify
python scripts/set_feature_rollout.py --status
```

### Full Infrastructure Rollback

```bash
# Run rollback script
./scripts/rollback_phase3.sh all production

# Follow prompts and verify
```

**Rollback Time:** <5 minutes to disable features, <30 minutes for full infrastructure rollback

---

## Business Impact Measurement

### Daily Reports

Generate daily business impact:

```bash
# Yesterday's impact
python scripts/calculate_business_impact.py --yesterday

# Specific date
python scripts/calculate_business_impact.py --date 2026-01-10
```

**Example Output:**
```
REALTIME_INTELLIGENCE:
  Revenue Impact: $1,245.00
  Operating Cost: $16.50
  Net Impact: $1,228.50
  Usage Count: 1,250
  Conversion Lift: 4.8%
  Time Saved: 62.5 hours
```

### Weekly Reports

Generate comprehensive weekly report:

```bash
# Last 7 days
python scripts/calculate_business_impact.py --weekly
```

**Example Output:**
```
WEEKLY SUMMARY
==============================================================
Total Platform Impact:
  Revenue: $8,750.00
  Cost: $115.00
  Net: $8,635.00
  ROI: 7,608.7%
```

### ROI Dashboard

Access real-time ROI tracking:

```bash
# Local dashboard
streamlit run ghl_real_estate_ai/streamlit_components/phase3_roi_dashboard.py

# Or deployed version
open https://your-app.vercel.app/analytics
```

---

## Common Issues & Solutions

### Issue: WebSocket Connection Failures

**Symptoms:** High connection failure rate, timeouts

**Solution:**
```bash
# Check WebSocket service logs
railway logs --service websocket-manager | grep "ERROR"

# Restart service
railway service restart websocket-manager --environment production

# Scale up if needed
railway service scale websocket-manager --replicas 3
```

### Issue: ML Inference Slow

**Symptoms:** ML latency >50ms (P95)

**Solution:**
```bash
# Check ML service performance
railway logs --service ml-manager | grep "latency"

# Scale up ML service
railway service scale ml-manager --replicas 5

# Increase resources
railway service update ml-manager --cpu 4000m --memory 8Gi
```

### Issue: Vision Analysis Timeouts

**Symptoms:** Property vision analysis >3s or timeouts

**Solution:**
```bash
# Check Claude API rate limits
python scripts/check_anthropic_quota.py

# Increase timeout if needed
railway variables set VISION_ANALYSIS_TIMEOUT_MS=5000

# Check image sizes (should be <5MB)
python scripts/validate_image_sizes.py
```

### Issue: Feature Not Showing for Users

**Symptoms:** Feature enabled but users not seeing it

**Solution:**
```bash
# Verify feature flag
python scripts/set_feature_rollout.py --status

# Check A/B test assignment
python scripts/check_ab_assignment.py --tenant-id <tenant-id> --feature <feature-name>

# Clear Redis cache
python scripts/clear_feature_cache.py --feature <feature-name>
```

---

## Success Checklist

### Pre-Deployment
- [ ] All environment variables configured
- [ ] Railway account and CLI set up
- [ ] Vercel account and CLI set up
- [ ] API keys validated
- [ ] Team notified of deployment

### Post-Deployment
- [ ] All Railway services healthy
- [ ] All Vercel dashboards accessible
- [ ] Database migrations complete
- [ ] Redis configured correctly
- [ ] Feature flags set to 10%
- [ ] Monitoring dashboards operational
- [ ] Alert notifications working

### Week 1 Validation
- [ ] Performance targets met
- [ ] No critical errors
- [ ] User satisfaction >80%
- [ ] Feature usage >50%
- [ ] Business impact visible

### Week 4 Completion
- [ ] 100% rollout achieved
- [ ] ROI validated (>500%)
- [ ] All documentation updated
- [ ] Team trained on features
- [ ] Support runbooks complete

---

## Support & Resources

### Documentation
- **Full Deployment Strategy:** `docs/PHASE_3_PRODUCTION_DEPLOYMENT_STRATEGY.md`
- **Railway Setup:** `docs/DEPLOYMENT_RAILWAY_VERCEL.md`
- **API Documentation:** `docs/API_DOCUMENTATION.md`

### Scripts
- **Feature Rollout:** `scripts/set_feature_rollout.py`
- **Business Impact:** `scripts/calculate_business_impact.py`
- **Deploy Railway:** `scripts/deploy_railway_backend.sh`
- **Deploy Vercel:** `scripts/deploy_vercel_frontend.sh`
- **Verify Infrastructure:** `scripts/verify_infrastructure.sh`

### Dashboards
- **Railway:** https://railway.app/dashboard
- **Vercel:** https://vercel.com/dashboard
- **ROI Tracking:** https://your-app.vercel.app/analytics

### Team Contacts
- **Technical Lead:** [Name/Email]
- **DevOps:** [Name/Email]
- **Product Manager:** [Name/Email]
- **Support:** support@yourcompany.com

---

## Next Steps After Deployment

1. **Monitor Continuously:** Check metrics daily for first week
2. **Gather Feedback:** Survey users in 10% cohort
3. **Optimize Performance:** Address any bottlenecks found
4. **Expand Rollout:** Progress through 25% → 50% → 100%
5. **Document Learnings:** Update runbooks with production insights
6. **Celebrate Success:** Share wins with the team!

---

**Deployment Started:** _________________
**Deployment Completed:** _________________
**Deployed By:** _________________
**Status:** _________________

