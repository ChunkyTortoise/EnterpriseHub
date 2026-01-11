# AI-Enhanced Operations Production Runbook

## Overview
This runbook provides operational procedures for the AI-Enhanced Operations platform.

## Emergency Contacts
- Platform Owner: AI Operations Team
- Escalation: Engineering Leadership
- Business Impact: High (Revenue Impact: $720,000+ annually)

## Architecture Overview
- 6 AI Operations Components
- Load Balanced with NGINX
- Redis Caching Layer
- PostgreSQL with TimescaleDB
- Kubernetes Orchestration

## Component Status Checks

### Quick Health Check
```bash
# Check all component health
kubectl get pods -n ai-operations
kubectl get services -n ai-operations

# Check dashboard accessibility
curl -f https://ai-operations.enterprisehub.local/health
```

### Detailed Component Status
```bash
# Individual component checks
curl http://intelligent-monitoring-engine:8001/health
curl http://auto-scaling-controller:8002/health
curl http://self-healing-system:8003/health
curl http://performance-predictor:8004/health
curl http://enhanced-ml-integration:8005/health
curl http://operations-dashboard:8080/health
```

## Common Issues and Resolution

### 1. High Anomaly Detection Rate
**Symptoms:** Excessive alerts, false positives
**Resolution:**
1. Check anomaly threshold: `kubectl edit configmap intelligent-monitoring-config`
2. Review recent metric patterns in Grafana
3. Consider retraining ML models if data drift detected

### 2. Auto-Scaling Not Working
**Symptoms:** Services not scaling under load
**Resolution:**
1. Check HPA status: `kubectl get hpa -n ai-operations`
2. Verify metrics server: `kubectl top pods -n ai-operations`
3. Review scaling policies in controller configuration

### 3. Dashboard Unavailable
**Symptoms:** UI not accessible, WebSocket errors
**Resolution:**
1. Check dashboard pod status: `kubectl describe pod -l app=operations-dashboard`
2. Verify NGINX configuration: `kubectl logs nginx-pod`
3. Test WebSocket connectivity: `wscat -c ws://dashboard:8080/ws`

### 4. Self-Healing Failed
**Symptoms:** Incidents not auto-resolved
**Resolution:**
1. Review incident classification accuracy
2. Check knowledge base update status
3. Validate resolution success rate threshold

### 5. ML Model Performance Degraded
**Symptoms:** Prediction accuracy below 85%
**Resolution:**
1. Trigger model retraining: `kubectl exec -it ml-pod -- python retrain_models.py`
2. Check training data quality and volume
3. Review feature drift analysis

## Scaling Procedures

### Manual Scaling
```bash
# Scale specific component
kubectl scale deployment intelligent-monitoring-engine --replicas=3

# Scale all components
for comp in intelligent-monitoring-engine auto-scaling-controller self-healing-system performance-predictor enhanced-ml-integration operations-dashboard; do
  kubectl scale deployment $comp --replicas=2
done
```

### Load Testing
```bash
# Generate test load
kubectl run load-test --image=busybox --rm -it --restart=Never -- /bin/sh
# Inside pod: use curl or ab to generate load
```

## Backup and Recovery

### Database Backup
```bash
# Backup PostgreSQL
kubectl exec postgres-pod -- pg_dump ai_operations > ai_operations_backup_$(date +%Y%m%d).sql

# Backup Redis
kubectl exec redis-pod -- redis-cli save
kubectl cp redis-pod:/data/dump.rdb ./redis_backup_$(date +%Y%m%d).rdb
```

### Configuration Backup
```bash
# Backup all configurations
kubectl get configmaps -n ai-operations -o yaml > configmaps_backup.yaml
kubectl get secrets -n ai-operations -o yaml > secrets_backup.yaml
```

## Monitoring and Alerts

### Key Metrics to Monitor
1. Component Health (uptime > 99.5%)
2. API Response Times (< 200ms 95th percentile)
3. ML Model Accuracy (> 85%)
4. Auto-scaling Success Rate (> 95%)
5. Incident Auto-resolution Rate (> 80%)

### Critical Alerts
1. Any component down for > 1 minute
2. API response time > 500ms for 5 minutes
3. ML accuracy < 85% for 10 minutes
4. Database connections exhausted
5. Redis memory usage > 90%

## Maintenance Procedures

### Regular Maintenance (Weekly)
1. Review anomaly detection false positive rate
2. Check ML model accuracy trends
3. Analyze auto-scaling efficiency
4. Update incident resolution knowledge base

### Monthly Tasks
1. ML model retraining with latest data
2. Performance optimization review
3. Security patch updates
4. Capacity planning review

### Quarterly Reviews
1. Business value assessment
2. Architecture optimization opportunities
3. Technology stack updates
4. Disaster recovery testing

## Performance Tuning

### Database Optimization
```sql
-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC LIMIT 10;

-- Update table statistics
ANALYZE metrics;
ANALYZE alerts;
ANALYZE scaling_decisions;
```

### Redis Optimization
```bash
# Check memory usage
kubectl exec redis-pod -- redis-cli info memory

# Optimize memory
kubectl exec redis-pod -- redis-cli config set maxmemory-policy allkeys-lru
```

## Security Procedures

### Certificate Renewal
```bash
# Check certificate expiry
openssl x509 -in ssl/ai-operations.crt -text -noout | grep "Not After"

# Renew certificates (process varies by CA)
# Update certificates in Kubernetes secrets
kubectl create secret tls ai-operations-tls --cert=new.crt --key=new.key --dry-run=client -o yaml | kubectl apply -f -
```

### Security Hardening
```bash
# Update container images
kubectl set image deployment/intelligent-monitoring-engine intelligent-monitoring-engine=ai-operations/intelligent-monitoring-engine:latest

# Scan for vulnerabilities
kubectl exec security-scanner -- trivy image ai-operations/intelligent-monitoring-engine:latest
```

## Troubleshooting Decision Tree

1. **Is the issue affecting users?**
   - Yes: Follow incident response procedures
   - No: Continue with standard troubleshooting

2. **Is it a single component or system-wide?**
   - Single: Focus on that component's logs and health
   - System-wide: Check infrastructure (Redis, PostgreSQL, Network)

3. **Is it performance or availability?**
   - Performance: Check metrics, consider scaling
   - Availability: Check pod status, restart if needed

4. **Are ML models involved?**
   - Yes: Check model accuracy, consider retraining
   - No: Focus on infrastructure and configuration

## Contact Information
- Slack Channel: #ai-operations-support
- On-call Engineer: Pager duty rotation
- Escalation Manager: Engineering Team Lead
- Business Stakeholder: Product Manager

## SLAs and Business Impact
- Target Uptime: 99.9%
- Max Response Time: < 200ms (95th percentile)
- Business Impact: $720,000+ annual revenue at risk
- Customer Impact: Real-time AI operations affecting all Enhanced ML services
