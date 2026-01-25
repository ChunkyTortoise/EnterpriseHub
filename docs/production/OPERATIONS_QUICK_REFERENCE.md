# Jorge's Real Estate AI Platform - Operations Quick Reference

**Emergency Contact**: operations@jorge-revenue.com | Slack: #jorge-platform-support

## 🚨 Emergency Response (P0/P1)

### Immediate Actions
```bash
# 1. Check overall health
curl -s https://api.jorge-revenue.com/health/detailed | jq .

# 2. Check service status in Kubernetes
kubectl get pods -n jorge-revenue-platform

# 3. Check recent deployments
kubectl rollout history deployment/jorge-backend -n jorge-revenue-platform

# 4. Emergency rollback if needed
helm rollback jorge-platform -n jorge-revenue-platform
```

### Alert Response Times
- **🔴 Critical (P0)**: <5 minutes | Service down, security breach
- **🟠 High (P1)**: <30 minutes | Performance degradation, errors >1%
- **🟡 Medium (P2)**: <2 hours | Feature issues, warnings
- **🟢 Low (P3)**: <24 hours | Cosmetic issues, minor bugs

---

## 📊 Key Monitoring URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Primary Health** | https://api.jorge-revenue.com/health/detailed | Overall system health |
| **Grafana Dashboard** | https://monitoring.jorge-revenue.com | Real-time metrics |
| **Jorge Bot Health** | https://api.jorge-revenue.com/api/v1/bots/health | Bot ecosystem status |
| **Client Demo Portal** | https://app.jorge-revenue.com | Frontend health check |
| **Prometheus Metrics** | https://monitoring.jorge-revenue.com:9090 | Raw metrics access |

---

## 🎯 Critical Metrics & Thresholds

### Jorge Bot Performance (Target: >98.5% success rate)
```promql
# Jorge Bot Success Rate
(rate(jorge_seller_bot_interactions_total[5m]) - rate(jorge_seller_bot_failures_total[5m])) / rate(jorge_seller_bot_interactions_total[5m]) * 100

# Alert if < 98.5%
```

### ML Pipeline Performance (Target: <50ms)
```promql
# ML Inference Latency
histogram_quantile(0.95, sum(rate(ml_prediction_duration_seconds_bucket[5m])) by (le)) * 1000

# Current: 42.3ms | Alert if >50ms
```

### API Response Time (Target: <200ms)
```promql
# API Response Time (95th percentile)
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) * 1000

# Alert if >200ms for 5+ minutes
```

### Error Rate (Target: <1%)
```promql
# Overall Error Rate
(sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) * 100

# Alert if >1%
```

---

## 🔧 Common Operations

### Kubernetes Operations
```bash
# Connect to production cluster
aws eks update-kubeconfig --region us-east-1 --name jorge-revenue-platform-prod

# Check pod status
kubectl get pods -n jorge-revenue-platform -o wide

# View pod logs
kubectl logs -f deployment/jorge-backend -n jorge-revenue-platform --tail=50

# Scale deployment
kubectl scale deployment jorge-backend --replicas=3 -n jorge-revenue-platform

# Restart deployment (if needed)
kubectl rollout restart deployment/jorge-backend -n jorge-revenue-platform

# Check ingress status
kubectl get ingress -n jorge-revenue-platform
```

### Database Operations
```bash
# Check database connections
kubectl exec -it postgres-primary-0 -n jorge-revenue-platform -- psql -U postgres -c "
SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Check slow queries
kubectl exec -it postgres-primary-0 -n jorge-revenue-platform -- psql -U postgres -c "
SELECT query, query_start, state, wait_event FROM pg_stat_activity
WHERE state != 'idle' AND query_start < now() - interval '30 seconds';"

# Database backup status
aws rds describe-db-snapshots --db-instance-identifier jorge-production-db --max-records 5
```

### Redis Operations
```bash
# Connect to Redis
kubectl exec -it redis-master-0 -n jorge-revenue-platform -- redis-cli

# Check Redis memory usage
kubectl exec -it redis-master-0 -n jorge-revenue-platform -- redis-cli INFO memory

# Check cache hit rate
kubectl exec -it redis-master-0 -n jorge-revenue-platform -- redis-cli INFO stats | grep keyspace
```

### Application Health Checks
```bash
# Comprehensive health check
curl -s https://api.jorge-revenue.com/health/detailed | jq '
{
  status: .status,
  response_time_ms: .response_time_ms,
  jorge_bots: .services.jorge_bots,
  ml_engine: .services.ml_analytics,
  external_apis: .external_services
}'

# Jorge Bot specific health
curl -s https://api.jorge-revenue.com/api/v1/bots/jorge-seller/health | jq .

# ML Engine performance test
curl -X POST https://api.jorge-revenue.com/api/v1/ml/performance-test | jq .
```

---

## 🚀 Deployment Quick Actions

### Check Latest Deployment
```bash
# View recent deployments
kubectl rollout history deployment/jorge-backend -n jorge-revenue-platform

# Check deployment status
kubectl rollout status deployment/jorge-backend -n jorge-revenue-platform

# View current image versions
kubectl get deployments -n jorge-revenue-platform -o jsonpath='{.items[*].spec.template.spec.containers[*].image}'
```

### Emergency Rollback
```bash
# Rollback to previous version
helm rollback jorge-platform -n jorge-revenue-platform

# Or rollback to specific revision
helm rollback jorge-platform 5 -n jorge-revenue-platform

# Verify rollback
kubectl get pods -n jorge-revenue-platform
curl -f https://api.jorge-revenue.com/health
```

### Manual Deployment Trigger
```bash
# Force redeploy current version (if stuck)
kubectl patch deployment jorge-backend -n jorge-revenue-platform -p '{"spec":{"template":{"metadata":{"annotations":{"redeployedAt":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}}}}}'
```

---

## 🔍 Troubleshooting Decision Tree

### High Error Rate (>1%)
```
1. Check error breakdown:
   curl -s https://api.jorge-revenue.com/metrics | grep http_requests_total

2. If 5xx errors → Check application logs
3. If 4xx errors → Check for API misuse
4. If external API errors → Check Claude/GHL status
5. If database errors → Check DB connection pool
```

### Slow Response Times (>200ms)
```
1. Check ML inference time:
   curl -s https://api.jorge-revenue.com/metrics | grep ml_prediction_duration

2. If ML slow → Check model cache, consider scaling
3. If API slow → Check database query performance
4. If external APIs slow → Check Claude/GHL latency
5. Check Redis cache hit rate
```

### Jorge Bot Failures (>5%)
```
1. Check Jorge bot health:
   curl -s https://api.jorge-revenue.com/api/v1/bots/health

2. Check ML model accuracy:
   curl -s https://api.jorge-revenue.com/api/v1/ml/model-status

3. Check conversation intelligence service
4. Verify GHL integration status
5. Check for recent model deployments
```

### Memory/CPU Issues
```
1. Check resource usage:
   kubectl top pods -n jorge-revenue-platform

2. Check for memory leaks in logs
3. Scale deployment if needed:
   kubectl scale deployment jorge-backend --replicas=5 -n jorge-revenue-platform

4. Check database connection leaks
```

---

## 📞 Escalation Contacts

### Production Issues
- **Platform Engineering**: #platform-engineering
- **On-Call Engineer**: operations@jorge-revenue.com
- **Emergency Phone**: [24/7 emergency line]

### Business Impact
- **Product Team**: #product-team
- **Jorge (Client)**: realtorjorgesales@gmail.com
- **Business Stakeholders**: business@jorge-revenue.com

### Security Incidents
- **Security Team**: security@jorge-revenue.com
- **CISO**: #security-incidents
- **Emergency Security**: [security emergency line]

### External Vendor Support
- **AWS Support**: Business tier, escalate for P0/P1
- **Anthropic**: support@anthropic.com (Claude API issues)
- **GoHighLevel**: support@gohighlevel.com (CRM integration)

---

## 📋 Weekly Checklist

### Monday - Weekly Health Check
- [ ] Review weekend alert summary
- [ ] Check backup validation reports
- [ ] Verify security scan results
- [ ] Review resource utilization trends

### Wednesday - Performance Review
- [ ] Analyze Jorge bot success rates
- [ ] Review ML model accuracy metrics
- [ ] Check for performance degradation trends
- [ ] Validate SLA compliance

### Friday - Preparation & Updates
- [ ] Review upcoming maintenance
- [ ] Check for available security updates
- [ ] Verify disaster recovery tests scheduled
- [ ] Update documentation if needed

---

## 🎯 Performance Targets

| Metric | Target | Current | Alert Threshold |
|--------|--------|---------|-----------------|
| **Uptime** | 99.99% | 99.99%+ | <99.95% |
| **API Response** | <200ms | ~150ms | >200ms |
| **ML Inference** | <50ms | 42.3ms | >50ms |
| **Jorge Bot Success** | >98.5% | ~99.2% | <98.5% |
| **Error Rate** | <1% | ~0.3% | >1% |
| **Memory Usage** | <80% | ~60% | >85% |
| **CPU Usage** | <70% | ~45% | >80% |

---

## 🛡️ Security Quick Actions

### Security Incident Detection
```bash
# Check security alerts
kubectl logs -f deployment/falco -n security | grep CRITICAL

# Review audit logs
kubectl exec -it audit-logger-0 -n security -- tail -f /var/log/audit/security.log

# Check unauthorized access attempts
curl -s https://api.jorge-revenue.com/metrics | grep auth_failures_total
```

### Access Review
```bash
# Check active sessions
kubectl get secrets -n jorge-revenue-platform | grep jwt

# Review user access logs
kubectl logs deployment/auth-service -n jorge-revenue-platform | grep "access_granted"
```

---

## 🔄 Maintenance Windows

### Standard Maintenance Window
- **When**: Saturday 2:00 AM - 4:00 AM ET (lowest traffic)
- **Notification**: 48 hours advance notice to Jorge
- **Rollback Plan**: Always ready if issues detected

### Emergency Maintenance
- **Authorization**: Operations Lead or higher
- **Communication**: Immediate notification via all channels
- **Duration**: Minimize impact, <30 minutes when possible

---

**Quick Reference Version**: 2.0.0 | **Last Updated**: January 2026
**For emergencies**: Slack #jorge-platform-support or operations@jorge-revenue.com