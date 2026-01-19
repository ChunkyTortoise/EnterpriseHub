# Jorge's Revenue Platform - Production Deployment Guide

**Version:** 1.0.0
**Last Updated:** 2026-01-17
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Infrastructure Setup](#infrastructure-setup)
4. [Deployment Process](#deployment-process)
5. [Monitoring & Observability](#monitoring--observability)
6. [Rollback Procedures](#rollback-procedures)
7. [Troubleshooting](#troubleshooting)
8. [Business Operations](#business-operations)

---

## Overview

This guide provides complete instructions for deploying Jorge's Revenue Acceleration Platform to production with:

- **Zero-downtime deployments** via rolling updates
- **Auto-scaling** based on load (3-20 pods)
- **99.9% uptime SLA** capability
- **Comprehensive monitoring** and alerting
- **Automated rollback** on failure
- **Business intelligence** tracking

### Architecture Components

```
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer (Ingress)               │
│                  SSL/TLS Termination                     │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│         Jorge Revenue API (3-20 replicas)                │
│    - Dynamic Pricing Engine                              │
│    - ROI Calculator                                      │
│    - Predictive Analytics                                │
│    - Attribution Reports                                 │
└─────────────────────────────────────────────────────────┘
            │                           │
┌───────────────────┐      ┌────────────────────┐
│   PostgreSQL      │      │   Redis Cache      │
│   (RDS/Managed)   │      │  (ElastiCache)     │
└───────────────────┘      └────────────────────┘
```

---

## Prerequisites

### Required Tools

```bash
# Kubernetes CLI
kubectl version --client
# Minimum: v1.28.0

# Helm package manager
helm version
# Minimum: v3.12.0

# Terraform (for infrastructure)
terraform version
# Minimum: v1.6.0

# Docker (for local builds)
docker version
# Minimum: v24.0.0

# Python (for scripts)
python --version
# Minimum: 3.11
```

### Cloud Provider Accounts

1. **AWS Account** (recommended) or GCP/Azure
   - IAM permissions for EKS, RDS, ElastiCache, S3
   - VPC and networking permissions
   - Secrets Manager access

2. **GitHub Account**
   - Access to repository
   - GitHub Actions permissions
   - Container Registry access (ghcr.io)

3. **Third-Party Services**
   - GoHighLevel API credentials
   - Anthropic (Claude) API key
   - Slack webhook (optional, for notifications)

### Access Requirements

- AWS CLI configured with appropriate credentials
- kubectl configured for target cluster
- Repository access and SSH keys
- Secrets management access (AWS Secrets Manager)

---

## Infrastructure Setup

### Step 1: Provision Cloud Infrastructure

```bash
# Navigate to Terraform directory
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Review planned changes
terraform plan -var-file="environments/production.tfvars"

# Apply infrastructure
terraform apply -var-file="environments/production.tfvars"
```

**Created Resources:**
- VPC with public/private subnets across 3 AZs
- EKS cluster with managed node groups
- RDS PostgreSQL (Multi-AZ for production)
- ElastiCache Redis (with replication)
- S3 buckets (analytics, backups)
- CloudWatch log groups
- Security groups and IAM roles

### Step 2: Configure Kubernetes Cluster

```bash
# Get cluster credentials
aws eks update-kubeconfig --region us-east-1 --name jorge-revenue-production

# Verify connection
kubectl cluster-info
kubectl get nodes

# Install NGINX Ingress Controller
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=LoadBalancer

# Install cert-manager for SSL
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --set installCRDs=true

# Install Prometheus & Grafana
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --values infrastructure/monitoring/prometheus-values.yaml
```

### Step 3: Configure Secrets

```bash
# Create namespace
kubectl create namespace jorge-revenue-platform

# Create secrets from AWS Secrets Manager
kubectl create secret generic jorge-app-secrets \
  --namespace jorge-revenue-platform \
  --from-literal=GHL_API_KEY="$(aws secretsmanager get-secret-value --secret-id jorge-revenue/production/ghl-api-key --query SecretString --output text)" \
  --from-literal=ANTHROPIC_API_KEY="$(aws secretsmanager get-secret-value --secret-id jorge-revenue/production/anthropic-api-key --query SecretString --output text)" \
  --from-literal=DATABASE_URL="$(terraform output -raw rds_connection_string)" \
  --from-literal=REDIS_URL="$(terraform output -raw redis_connection_string)"

# Verify secrets created
kubectl get secrets -n jorge-revenue-platform
```

### Step 4: Database Initialization

```bash
# Run database migrations
kubectl run db-migration \
  --namespace jorge-revenue-platform \
  --image=ghcr.io/jorge-salas/revenue-platform:latest \
  --restart=Never \
  --env="DATABASE_URL=$(kubectl get secret jorge-app-secrets -n jorge-revenue-platform -o jsonpath='{.data.DATABASE_URL}' | base64 -d)" \
  -- alembic upgrade head

# Verify migration
kubectl logs db-migration -n jorge-revenue-platform

# Cleanup migration pod
kubectl delete pod db-migration -n jorge-revenue-platform
```

---

## Deployment Process

### Automated Deployment (Recommended)

The platform includes automated CI/CD via GitHub Actions:

```bash
# Trigger production deployment
git push origin main

# Or manually trigger via GitHub Actions UI
# Go to Actions > Production Deployment Pipeline > Run workflow
```

**Deployment Pipeline Stages:**
1. Code quality checks (Ruff, mypy)
2. Unit tests (80% coverage required)
3. Integration tests
4. Security scanning (Trivy, Bandit)
5. Docker build and push
6. Deploy to staging
7. Load testing on staging
8. Manual approval gate
9. Deploy to production
10. Post-deployment monitoring

### Manual Deployment

For manual deployments or emergency updates:

```bash
# Build and push Docker image
docker build -f Dockerfile.production -t ghcr.io/jorge-salas/revenue-platform:v1.0.0 .
docker push ghcr.io/jorge-salas/revenue-platform:v1.0.0

# Deploy using automated script
./scripts/deploy-production.sh production v1.0.0

# Or deploy using Helm directly
helm upgrade --install jorge-revenue-platform \
  infrastructure/helm/jorge-revenue-platform/ \
  --namespace jorge-revenue-platform \
  --values infrastructure/helm/jorge-revenue-platform/values-production.yaml \
  --set image.tag=v1.0.0 \
  --wait \
  --timeout 10m
```

### Deployment Verification

```bash
# Check deployment status
kubectl rollout status deployment/jorge-revenue-api -n jorge-revenue-platform

# View pods
kubectl get pods -n jorge-revenue-platform

# Check logs
kubectl logs -f deployment/jorge-revenue-api -n jorge-revenue-platform

# Run smoke tests
./scripts/smoke-tests.sh production

# Check metrics
kubectl top pods -n jorge-revenue-platform
```

---

## Monitoring & Observability

### Accessing Dashboards

**Grafana Dashboard:**
```bash
# Port-forward Grafana
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80

# Access at: http://localhost:3000
# Default credentials: admin / (get from secret)
kubectl get secret -n monitoring monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 -d
```

**Prometheus:**
```bash
# Port-forward Prometheus
kubectl port-forward -n monitoring svc/monitoring-prometheus 9090:9090

# Access at: http://localhost:9090
```

### Key Metrics to Monitor

#### Business Metrics
- **Total Revenue (24h):** `sum(increase(revenue_total_dollars[24h]))`
- **ARPU:** `avg_over_time(average_revenue_per_user[1h])`
- **Lead Conversion Rate:** `(leads_converted / leads_created) * 100`
- **Active Clients:** `count(count by (location_id) (pricing_calculations_total))`

#### Application Metrics
- **Request Rate:** `rate(http_requests_total[5m])`
- **Response Time (P95):** `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
- **Error Rate:** `(rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])) * 100`

#### Infrastructure Metrics
- **Pod Memory Usage:** `container_memory_working_set_bytes`
- **Pod CPU Usage:** `rate(container_cpu_usage_seconds_total[5m])`
- **Database Connections:** `database_connections_active / database_connections_max`
- **Redis Cache Hit Rate:** `(redis_cache_hits / (redis_cache_hits + redis_cache_misses)) * 100`

### Alert Configuration

Alerts are automatically configured via Prometheus AlertManager.

**Critical Alerts** (immediate notification):
- Service down
- High error rate (>1%)
- Database connection pool exhausted
- Pod crash looping

**Warning Alerts** (5-15 min delay):
- High response time (>1s)
- High memory/CPU usage (>80%)
- Low cache hit rate (<70%)
- Abnormal ARPU

**Alert Channels:**
- Email (configured in AlertManager)
- Slack webhook (optional)
- PagerDuty (production only)

---

## Rollback Procedures

### Automatic Rollback

The deployment script automatically rolls back on failure:
- Health check failures
- High error rate detection
- Failed smoke tests

### Manual Rollback

```bash
# View deployment history
kubectl rollout history deployment/jorge-revenue-api -n jorge-revenue-platform

# Rollback to previous version
kubectl rollout undo deployment/jorge-revenue-api -n jorge-revenue-platform

# Rollback to specific revision
kubectl rollout undo deployment/jorge-revenue-api -n jorge-revenue-platform --to-revision=3

# Verify rollback
kubectl rollout status deployment/jorge-revenue-api -n jorge-revenue-platform
./scripts/smoke-tests.sh production
```

### Database Rollback

```bash
# View migration history
kubectl exec -it deployment/jorge-revenue-api -n jorge-revenue-platform -- alembic history

# Rollback database (if needed)
kubectl exec -it deployment/jorge-revenue-api -n jorge-revenue-platform -- alembic downgrade -1

# Verify database state
kubectl exec -it deployment/jorge-revenue-api -n jorge-revenue-platform -- alembic current
```

---

## Troubleshooting

### Common Issues

#### 1. Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n jorge-revenue-platform

# Common causes:
# - Image pull errors (check registry credentials)
# - Resource limits (check node capacity)
# - Configuration errors (check ConfigMap/Secrets)

# Fix image pull errors
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=<username> \
  --docker-password=<token> \
  -n jorge-revenue-platform
```

#### 2. High Error Rate

```bash
# Check application logs
kubectl logs deployment/jorge-revenue-api -n jorge-revenue-platform --tail=100

# Check for common errors:
# - Database connection issues
# - Redis connection issues
# - External API failures (GHL, Anthropic)

# Restart pods if needed
kubectl rollout restart deployment/jorge-revenue-api -n jorge-revenue-platform
```

#### 3. Performance Issues

```bash
# Check resource usage
kubectl top pods -n jorge-revenue-platform

# Check HPA status
kubectl get hpa -n jorge-revenue-platform

# Scale manually if needed
kubectl scale deployment/jorge-revenue-api --replicas=10 -n jorge-revenue-platform

# Check database performance
# (Use RDS Performance Insights in AWS Console)
```

#### 4. Database Connection Issues

```bash
# Verify database connectivity
kubectl run db-test \
  --image=postgres:15-alpine \
  --rm -it \
  --restart=Never \
  --env="PGPASSWORD=<password>" \
  -- psql -h <db-host> -U jorge_admin -d jorge_revenue

# Check connection pool
kubectl logs deployment/jorge-revenue-api -n jorge-revenue-platform | grep "database"
```

### Emergency Procedures

#### Complete System Failure

```bash
# 1. Check cluster health
kubectl get nodes
kubectl get pods --all-namespaces

# 2. Check ingress
kubectl get ingress -n jorge-revenue-platform

# 3. Restore from backup
./scripts/restore-from-backup.sh <backup-timestamp>

# 4. Notify stakeholders
# Use incident response playbook
```

#### Data Corruption

```bash
# 1. Stop accepting new requests
kubectl scale deployment/jorge-revenue-api --replicas=0 -n jorge-revenue-platform

# 2. Restore database from backup
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier jorge-revenue-restored \
  --db-snapshot-identifier <snapshot-id>

# 3. Update database connection
# (Update secrets with new database endpoint)

# 4. Resume service
kubectl scale deployment/jorge-revenue-api --replicas=3 -n jorge-revenue-platform
```

---

## Business Operations

### Client Onboarding

```bash
# Create new client tenant
kubectl exec -it deployment/jorge-revenue-api -n jorge-revenue-platform -- \
  python -m ghl_real_estate_ai.scripts.create_tenant \
  --location-id "<ghl-location-id>" \
  --name "Client Name" \
  --tier "premium"
```

### Revenue Tracking

Access revenue metrics via:
1. **Grafana Dashboard:** Business Metrics panel
2. **API Endpoint:** `GET /api/analytics/revenue?days=30`
3. **S3 Analytics Bucket:** Daily aggregated reports

### Backup & Recovery

**Automated Backups:**
- Database: Daily snapshots (30-day retention)
- Redis: AOF persistence with daily snapshots
- Configuration: Stored in Git repository
- Analytics data: S3 lifecycle policies

**Manual Backup:**
```bash
# Create database snapshot
aws rds create-db-snapshot \
  --db-instance-identifier jorge-revenue-production \
  --db-snapshot-identifier manual-backup-$(date +%Y%m%d)

# Backup Redis
kubectl exec -it redis-0 -n jorge-revenue-platform -- redis-cli BGSAVE
```

### Scaling Operations

**Auto-scaling is configured for:**
- CPU usage >70%
- Memory usage >80%
- Request rate >1000 req/s

**Manual scaling:**
```bash
# Scale up
kubectl scale deployment/jorge-revenue-api --replicas=15 -n jorge-revenue-platform

# Update HPA limits
kubectl patch hpa jorge-revenue-api-hpa -n jorge-revenue-platform -p '{"spec":{"maxReplicas":30}}'
```

---

## Production Readiness Checklist

### Pre-Deployment

- [ ] All secrets configured in AWS Secrets Manager
- [ ] Database migrations tested in staging
- [ ] Load testing completed (1000+ req/s)
- [ ] Security scans passed (Trivy, Bandit)
- [ ] Test coverage ≥80%
- [ ] Documentation updated
- [ ] Stakeholders notified

### Post-Deployment

- [ ] Smoke tests passed
- [ ] Health checks green
- [ ] Metrics flowing to Grafana
- [ ] Alerts configured and tested
- [ ] Error rate <0.1%
- [ ] Response time <500ms (P95)
- [ ] Business metrics tracking correctly
- [ ] Deployment report generated

### Ongoing Operations

- [ ] Daily metrics review
- [ ] Weekly capacity planning
- [ ] Monthly security updates
- [ ] Quarterly disaster recovery drills
- [ ] Customer feedback integration

---

## Support & Escalation

### Support Tiers

**Tier 1 - Monitoring Alerts**
- Automated alerts via Prometheus
- Self-healing via Kubernetes

**Tier 2 - Engineering On-Call**
- Critical alerts (service down, high error rate)
- Response time: <15 minutes
- PagerDuty escalation

**Tier 3 - Incident Response Team**
- Data corruption, security breaches
- Response time: <5 minutes
- Executive notification

### Contact Information

- **Engineering Lead:** jorge@example.com
- **DevOps Team:** devops@example.com
- **Emergency Hotline:** +1-XXX-XXX-XXXX

---

## Additional Resources

- [API Documentation](./API_DOCUMENTATION.md)
- [Architecture Overview](./ARCHITECTURE.md)
- [Security Guide](./SECURITY_GUIDE.md)
- [Runbook Collection](./runbooks/)
- [Incident Response Playbook](./INCIDENT_RESPONSE.md)

---

**Document Version:** 1.0.0
**Last Review Date:** 2026-01-17
**Next Review Date:** 2026-02-17
