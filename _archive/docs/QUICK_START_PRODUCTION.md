# Jorge's Revenue Platform - Quick Start Production Guide

**For:** Jorge Salas and DevOps Team
**Version:** 1.0.0
**Date:** 2026-01-17

---

## 🚀 Deploy to Production in 10 Minutes

### Prerequisites Checklist

```bash
# 1. Verify tools installed
kubectl version --client    # Need v1.28+
helm version               # Need v3.12+
terraform version          # Need v1.6+
aws --version             # Need AWS CLI

# 2. Verify access
aws sts get-caller-identity  # Check AWS access
kubectl cluster-info         # Check Kubernetes access
```

### Step 1: Provision Infrastructure (5 min)

```bash
# Navigate to terraform directory
cd infrastructure/terraform

# Initialize and apply
terraform init
terraform apply -var-file="environments/production.tfvars" -auto-approve

# Get outputs
terraform output rds_endpoint
terraform output redis_endpoint
```

### Step 2: Configure Secrets (2 min)

```bash
# Set environment variables
export GHL_API_KEY="your-ghl-api-key"
export GHL_LOCATION_ID="your-location-id"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export DATABASE_URL="$(terraform output -raw rds_connection_string)"
export REDIS_URL="$(terraform output -raw redis_connection_string)"

# Create Kubernetes secrets
kubectl create namespace jorge-revenue-platform
kubectl create secret generic jorge-app-secrets \
  --namespace jorge-revenue-platform \
  --from-literal=GHL_API_KEY="$GHL_API_KEY" \
  --from-literal=GHL_LOCATION_ID="$GHL_LOCATION_ID" \
  --from-literal=ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  --from-literal=DATABASE_URL="$DATABASE_URL" \
  --from-literal=REDIS_URL="$REDIS_URL"
```

### Step 3: Deploy Application (3 min)

```bash
# Return to project root
cd ../..

# Run automated deployment
./scripts/deploy-production.sh production v1.0.0

# Wait for deployment to complete (automatic)
# Script will:
# ✅ Run pre-deployment tests
# ✅ Deploy to Kubernetes
# ✅ Run health checks
# ✅ Execute smoke tests
# ✅ Monitor for errors
# ⚠️ Auto-rollback on failure
```

### Step 4: Verify Deployment (1 min)

```bash
# Check deployment status
kubectl get pods -n jorge-revenue-platform

# Run smoke tests
./scripts/smoke-tests.sh production

# View logs
kubectl logs -f deployment/jorge-revenue-api -n jorge-revenue-platform
```

---

## 🎯 Common Operations

### Deploy New Version

```bash
# Trigger via GitHub (recommended)
git tag v1.1.0
git push origin v1.1.0

# Or manually
./scripts/deploy-production.sh production v1.1.0
```

### Rollback to Previous Version

```bash
# Automatic rollback on failure
# Manual rollback if needed:
kubectl rollout undo deployment/jorge-revenue-api -n jorge-revenue-platform
```

### View Metrics & Monitoring

```bash
# Access Grafana dashboard
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
# Open: http://localhost:3000

# Access Prometheus
kubectl port-forward -n monitoring svc/monitoring-prometheus 9090:9090
# Open: http://localhost:9090
```

### Scale Application

```bash
# Manual scaling
kubectl scale deployment/jorge-revenue-api --replicas=10 -n jorge-revenue-platform

# Auto-scaling is automatic based on:
# - CPU usage >70%
# - Memory usage >80%
# - Request rate >1000 req/s
```

### View Logs

```bash
# Real-time logs
kubectl logs -f deployment/jorge-revenue-api -n jorge-revenue-platform

# Logs from specific pod
kubectl logs -f <pod-name> -n jorge-revenue-platform

# CloudWatch logs (AWS Console)
# Log group: /aws/jorge-revenue/production/application
```

---

## 🔍 Troubleshooting Quick Fixes

### Issue: Pods not starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n jorge-revenue-platform

# Common fixes:
# 1. Check secrets exist
kubectl get secrets -n jorge-revenue-platform

# 2. Check image exists
kubectl get pods -n jorge-revenue-platform -o jsonpath='{.items[0].spec.containers[0].image}'

# 3. Check resource limits
kubectl describe nodes
```

### Issue: High error rate

```bash
# Check application logs
kubectl logs deployment/jorge-revenue-api -n jorge-revenue-platform --tail=100

# Restart deployment
kubectl rollout restart deployment/jorge-revenue-api -n jorge-revenue-platform

# Monitor recovery
kubectl rollout status deployment/jorge-revenue-api -n jorge-revenue-platform
```

### Issue: Database connection problems

```bash
# Test database connectivity
kubectl run db-test --image=postgres:15-alpine --rm -it --restart=Never \
  --env="PGPASSWORD=$DB_PASSWORD" \
  -- psql -h $DB_HOST -U jorge_admin -d jorge_revenue

# Check connection pool
kubectl logs deployment/jorge-revenue-api -n jorge-revenue-platform | grep "database"
```

---

## 📊 Key Metrics to Watch

### Business Metrics
- **Revenue (24h):** Target >$1000/day
- **ARPU:** Target $400/client
- **Conversion Rate:** Target >10%
- **Active Clients:** Growing weekly

### Technical Metrics
- **Uptime:** Target 99.9%
- **Response Time (P95):** Target <1s
- **Error Rate:** Target <0.1%
- **Request Rate:** Handle 1000+ req/s

### Infrastructure Metrics
- **Pod Count:** 3-20 (auto-scaling)
- **CPU Usage:** Target <70%
- **Memory Usage:** Target <80%
- **Database Connections:** <90% of max

---

## 🚨 Emergency Contacts

### Critical Alerts (Response <5 min)
- Service Down
- Data Corruption
- Security Breach

**Contact:** devops-oncall@example.com
**PagerDuty:** +1-XXX-XXX-XXXX

### Warning Alerts (Response <15 min)
- High Error Rate
- Performance Degradation
- Resource Exhaustion

**Contact:** engineering-team@example.com

---

## 📚 Quick Reference Links

- [Full Deployment Guide](docs/PRODUCTION_DEPLOYMENT_GUIDE.md)
- [Production Readiness Checklist](PRODUCTION_READINESS_CHECKLIST.md)
- [Complete Package Documentation](JORGE_PRODUCTION_DEPLOYMENT_PACKAGE_2026-01-17.md)
- API Documentation: https://api.jorge-revenue.example.com/docs
- Grafana Dashboards: (port-forward required)
- Prometheus Metrics: (port-forward required)

---

## ✅ Pre-Launch Checklist

Before going live, verify:

- [ ] All infrastructure provisioned
- [ ] Secrets configured correctly
- [ ] Deployment successful
- [ ] Smoke tests passing
- [ ] Health checks green
- [ ] Monitoring dashboards accessible
- [ ] Alerts configured
- [ ] Backup procedures tested
- [ ] Team trained on runbooks
- [ ] On-call rotation established

---

## 🎯 Success Criteria

**Week 1:**
- [ ] Zero critical incidents
- [ ] 99.9%+ uptime
- [ ] P95 response time <1s
- [ ] Error rate <0.1%

**Month 1:**
- [ ] 10+ active clients
- [ ] ARPU >$300/client
- [ ] Customer satisfaction >90%
- [ ] No security incidents

**Quarter 1:**
- [ ] 50+ active clients
- [ ] ARPU >$400/client
- [ ] Revenue >$20,000/month
- [ ] Platform ROI positive

---

## 🔄 Continuous Improvement

### Daily
- Review monitoring dashboards
- Check alert notifications
- Monitor error logs
- Track business metrics

### Weekly
- Performance optimization review
- Capacity planning check
- Security audit review
- Customer feedback analysis

### Monthly
- Cost optimization analysis
- Infrastructure right-sizing
- Feature usage analytics
- Business metrics review

### Quarterly
- Disaster recovery drill
- Security posture assessment
- Infrastructure upgrade planning
- Strategic roadmap alignment

---

## 💡 Pro Tips

1. **Use Automated Deployment**
   - Let CI/CD handle deployments
   - Manual deployment only for emergencies

2. **Monitor Business Metrics**
   - Technical metrics matter, but business metrics pay bills
   - Track ARPU, conversion rate, revenue daily

3. **Trust Auto-Scaling**
   - Let Kubernetes handle scaling
   - Manual scaling only for known traffic spikes

4. **Leverage Monitoring**
   - Set up Slack/email alerts
   - Review Grafana dashboards daily
   - Act on trends before they become incidents

5. **Document Everything**
   - Update runbooks after incidents
   - Share learnings with team
   - Keep documentation current

---

**Remember:** The platform is designed to be self-healing and auto-scaling. Trust the automation, but verify with monitoring!

**Questions?** Check the full documentation or contact the team.

---

**Version:** 1.0.0
**Last Updated:** 2026-01-17
**Status:** Production Ready 🚀
