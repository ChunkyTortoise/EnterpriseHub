# Jorge's Real Estate AI Platform - Production Operations Guide

**Document Version**: 2.0.0
**Created**: January 2026
**Status**: Production Ready
**Classification**: Internal Operations

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Deployment Procedures](#deployment-procedures)
4. [Monitoring & Alerting](#monitoring--alerting)
5. [Security Operations](#security-operations)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance Procedures](#maintenance-procedures)
8. [Incident Response](#incident-response)
9. [Disaster Recovery](#disaster-recovery)
10. [Contact Information](#contact-information)

---

## Overview

### Platform Summary

Jorge's Real Estate AI Platform is an enterprise-grade system providing:
- **Jorge Bot Ecosystem**: AI-powered lead qualification and nurturing
- **ML Analytics Engine**: 95% accuracy, sub-50ms inference time
- **Client Demonstration Environment**: Professional demo capabilities
- **Business Intelligence**: Real-time analytics and ROI reporting
- **GHL Integration**: Deep GoHighLevel CRM integration

### SLA Commitments
- **Uptime**: 99.99% (≤4.32 minutes downtime/month)
- **API Response Time**: <200ms (95th percentile)
- **ML Inference**: <50ms (target achieved: 42.3ms)
- **Jorge Bot Response**: <3 seconds
- **Security Incident Response**: <5 minutes

### Production Environment
- **Cloud**: AWS (EKS, RDS Aurora, ElastiCache)
- **Container Orchestration**: Kubernetes with Helm
- **Monitoring**: Prometheus + Grafana + Alertmanager
- **CI/CD**: GitHub Actions with blue-green deployment
- **Security**: SOC2/GDPR compliant, enterprise hardening

---

## System Architecture

### Production Infrastructure

```
┌─────────────────────────────────────────────────────────┐
│                    AWS EKS Cluster                      │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │   Jorge     │  │  Enterprise  │  │   Monitoring   │ │
│  │  Backend    │  │   Frontend   │  │     Stack      │ │
│  │   (API)     │  │    (UI)      │  │ (Prometheus)   │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ RDS Aurora  │  │ ElastiCache  │  │  EFS Storage   │ │
│  │(PostgreSQL) │  │   (Redis)    │  │ (Shared Data)  │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Key Services

| Service | Purpose | Health Endpoint | Port |
|---------|---------|-----------------|------|
| Jorge Backend API | Core business logic, bot orchestration | `/health/detailed` | 8000 |
| Enterprise Frontend | Professional UI, client demos | `/api/health` | 3000 |
| Prometheus | Metrics collection | `/metrics` | 9090 |
| Grafana | Metrics visualization | `/api/health` | 3000 |
| Alertmanager | Alert routing | `/api/v1/status` | 9093 |

### External Dependencies

| Service | Purpose | Rate Limits | Health Check |
|---------|---------|-------------|--------------|
| Claude API | AI inference, conversation intelligence | 500 req/min | Monitor latency |
| GoHighLevel API | CRM integration, lead sync | 1000 req/hour | Check remaining quota |
| Redis | Caching, session storage | - | Connection count |
| PostgreSQL | Primary data storage | - | Query performance |

---

## Deployment Procedures

### Production Deployment Checklist

#### Pre-Deployment
- [ ] **Security Scan**: All CI/CD security gates passed
- [ ] **Testing**: 650+ tests passing with 80%+ coverage
- [ ] **Performance**: ML inference <50ms, API response <200ms
- [ ] **Dependencies**: No critical vulnerabilities in dependencies
- [ ] **Backup**: Database backup completed
- [ ] **Monitoring**: All monitoring systems operational

#### Deployment Process (Automated)

1. **Trigger Deployment**
   ```bash
   # Push to main branch triggers production deployment
   git push origin main
   ```

2. **CI/CD Pipeline Execution**
   - Security scanning (Bandit, Safety, Semgrep)
   - Jorge bot ecosystem testing
   - ML pipeline validation
   - Container build and security scan
   - Staging deployment and validation

3. **Production Deployment (Manual Approval Required)**
   - Blue-green deployment with zero downtime
   - Health check validation
   - Performance validation
   - Business validation (Jorge bots functional)

#### Post-Deployment Verification

```bash
# 1. Verify deployment health
kubectl get pods -n jorge-revenue-platform
kubectl get services -n jorge-revenue-platform

# 2. Test critical endpoints
curl -f https://api.jorge-revenue.com/health/detailed
curl -f https://app.jorge-revenue.com/api/health

# 3. Verify Jorge bot functionality
curl -X POST https://api.jorge-revenue.com/api/v1/bots/jorge-seller/health

# 4. Check monitoring systems
curl -f https://monitoring.jorge-revenue.com/api/health
```

### Rollback Procedures

#### Automatic Rollback (CI/CD)
- Triggers on deployment failure or health check failure
- Automatic rollback to previous stable version
- Alert notifications sent to all channels

#### Manual Rollback
```bash
# 1. Connect to production cluster
aws eks update-kubeconfig --region us-east-1 --name jorge-revenue-platform-prod

# 2. Execute rollback
helm rollback jorge-platform -n jorge-revenue-platform

# 3. Verify rollback success
kubectl rollout status deployment/jorge-backend -n jorge-revenue-platform
```

---

## Monitoring & Alerting

### Grafana Dashboards

Access: https://monitoring.jorge-revenue.com

#### Primary Dashboard: "Jorge Platform Operations Center"
- **Platform Health**: Service status, uptime metrics
- **Jorge Bot Metrics**: Success rate, response time, error rate
- **ML Pipeline**: Inference time, accuracy, feature drift
- **Business Metrics**: Conversion rates, ROI calculations
- **Infrastructure**: CPU, memory, network, storage

### Alert Channels

#### Slack Integration
- **#alerts-critical** - PagerDuty escalation, immediate response
- **#jorge-bots-critical** - Jorge bot ecosystem issues
- **#infrastructure-critical** - Infrastructure failures
- **#performance-monitoring** - Performance degradation
- **#business-insights** - Business metric trends

#### PagerDuty Integration
- **Critical Alerts**: Service down, SLA breach, security incidents
- **Escalation**: Primary → Backup → Management
- **Response Time**: <5 minutes for critical, <30 minutes for high

### Key Metrics to Monitor

#### Business Metrics (Jorge Bots)
```promql
# Jorge Seller Bot Success Rate (Target: >98.5%)
(
  rate(jorge_seller_bot_interactions_total[5m]) - rate(jorge_seller_bot_failures_total[5m])
) / rate(jorge_seller_bot_interactions_total[5m])

# ML Inference Latency (Target: <50ms)
histogram_quantile(0.95,
  sum(rate(ml_prediction_duration_seconds_bucket[5m])) by (le)
)

# API Response Time (Target: <200ms)
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
)
```

#### Infrastructure Metrics
```promql
# Memory Usage (Alert: >85%)
(
  container_memory_working_set_bytes{pod=~"jorge-revenue-api.*"}
  /
  container_spec_memory_limit_bytes{pod=~"jorge-revenue-api.*"}
) * 100

# Database Connections (Alert: >90%)
(
  database_connections_active
  /
  database_connections_max
) * 100
```

### Alert Response Times

| Severity | Response Time | Escalation Time | Examples |
|----------|---------------|-----------------|-----------|
| **Critical** | <5 minutes | 15 minutes | Service down, security breach |
| **High** | <30 minutes | 2 hours | Performance degradation, high error rate |
| **Warning** | <2 hours | Next business day | Resource usage, minor issues |
| **Info** | <24 hours | Weekly review | Business insights, trends |

---

## Security Operations

### Security Monitoring

#### Falco Runtime Security
- **Location**: `/etc/falco/rules/jorge-platform.yaml`
- **Monitoring**: Unauthorized access, sensitive data access, high auth failures
- **Alerts**: Real-time security event detection

#### Audit Logging
- **Retention**: 7 years (compliance requirement)
- **Events**: 24 audit event types tracked
- **PII Masking**: Sensitive data automatically masked
- **SIEM Integration**: Ready for external SIEM systems

### Security Incident Response

#### Severity Classification

| Level | Response Time | Actions |
|-------|---------------|---------|
| **Critical** | Immediate | Isolate affected systems, activate incident response team |
| **High** | <1 hour | Investigate and contain, escalate if needed |
| **Medium** | <4 hours | Standard investigation and resolution |
| **Low** | <24 hours | Log and monitor, address during maintenance |

#### Incident Response Procedures

1. **Detection**: Automated alerts or manual detection
2. **Assessment**: Classify severity and impact
3. **Containment**: Isolate affected systems
4. **Eradication**: Remove threat and vulnerabilities
5. **Recovery**: Restore systems and monitor
6. **Lessons Learned**: Document and improve procedures

#### Emergency Contacts

```
Security Team Lead: [security-lead@jorge-revenue.com]
Incident Commander: [incident-commander@jorge-revenue.com]
CISO/Security Officer: [ciso@jorge-revenue.com]
External SOC: [soc-partner@security-provider.com]
```

### Compliance Monitoring

#### SOC2 Controls
- **Access Control**: Quarterly access reviews
- **Data Protection**: Encryption validation
- **System Operations**: Change management tracking
- **Monitoring**: Continuous compliance monitoring

#### GDPR Compliance
- **Data Subject Requests**: Response within 30 days
- **Breach Notification**: Internal <1 hour, authorities <72 hours
- **Data Retention**: Automatic deletion per policy
- **Consent Management**: Audit trail maintained

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Jorge Bot Response Time Slow (>3 seconds)

**Symptoms**: Dashboard shows high bot response times

**Diagnosis**:
```bash
# Check ML inference performance
curl -s https://api.jorge-revenue.com/metrics | grep ml_prediction_duration

# Check Claude API latency
curl -s https://api.jorge-revenue.com/metrics | grep claude_api_request_duration

# Check resource usage
kubectl top pods -n jorge-revenue-platform
```

**Resolution**:
1. Check ML model performance - may need re-optimization
2. Verify Claude API rate limits and latency
3. Scale backend pods if CPU/memory high
4. Check Redis cache hit rates

**Escalation**: If >5 minutes, escalate to ML team

#### 2. High Error Rate (>1%)

**Symptoms**: Prometheus alert "HighErrorRate"

**Diagnosis**:
```bash
# Check error breakdown
curl -s https://api.jorge-revenue.com/metrics | grep http_requests_total

# Check application logs
kubectl logs -f deployment/jorge-backend -n jorge-revenue-platform --tail=100

# Check external API status
curl -s https://api.jorge-revenue.com/health/detailed | jq '.external_services'
```

**Resolution**:
1. Identify error source (4xx vs 5xx)
2. Check external API connectivity (Claude, GHL)
3. Verify database connection pool
4. Review recent deployments

**Escalation**: If critical services affected >15 minutes

#### 3. Database Connection Pool Exhausted

**Symptoms**: "DatabaseConnectionPoolExhausted" alert

**Diagnosis**:
```bash
# Check connection pool metrics
curl -s https://api.jorge-revenue.com/metrics | grep database_connections

# Check slow queries
kubectl exec -it postgres-primary-0 -- psql -U postgres -c "
SELECT query, state, query_start
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY query_start;"
```

**Resolution**:
1. Kill long-running queries if safe
2. Restart backend pods to reset connections
3. Scale database if needed
4. Review query performance

**Escalation**: If unable to resolve in 10 minutes

#### 4. Redis Cache Issues

**Symptoms**: Low cache hit rate, slow responses

**Diagnosis**:
```bash
# Check Redis metrics
curl -s https://api.jorge-revenue.com/metrics | grep redis

# Connect to Redis
kubectl exec -it redis-master-0 -- redis-cli INFO memory
kubectl exec -it redis-master-0 -- redis-cli INFO stats
```

**Resolution**:
1. Check memory usage - may need scaling
2. Review cache expiration policies
3. Clear cache if corrupted data suspected
4. Restart Redis if necessary

### Performance Troubleshooting

#### ML Inference Optimization

```bash
# Check current performance
curl -X POST https://api.jorge-revenue.com/api/v1/ml/performance-test

# Expected response:
# {
#   "inference_time_ms": 42.3,
#   "accuracy": 0.95,
#   "model_version": "v2.1.0",
#   "status": "healthy"
# }
```

#### API Response Optimization

```bash
# Load test critical endpoints
curl -w "@curl-format.txt" -s -o /dev/null https://api.jorge-revenue.com/api/v1/leads/score

# Where curl-format.txt contains:
#     time_namelookup:  %{time_namelookup}\n
#        time_connect:  %{time_connect}\n
#     time_appconnect:  %{time_appconnect}\n
#    time_pretransfer:  %{time_pretransfer}\n
#       time_redirect:  %{time_redirect}\n
#  time_starttransfer:  %{time_starttransfer}\n
#                     ----------\n
#          time_total:  %{time_total}\n
```

---

## Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Tasks (Automated)
- [ ] Health check verification
- [ ] Backup validation
- [ ] Security scan results review
- [ ] Performance metrics review
- [ ] Error log analysis

#### Weekly Tasks
- [ ] **Jorge Bot Performance Review**
  - Analyze success rates and response times
  - Review ML model accuracy metrics
  - Check for feature drift indicators

- [ ] **Security Review**
  - Review security alerts and incidents
  - Validate access controls
  - Update security configurations if needed

- [ ] **Capacity Planning**
  - Review resource usage trends
  - Plan for scaling if needed
  - Update cost projections

#### Monthly Tasks
- [ ] **Disaster Recovery Test**
  - Test backup and recovery procedures
  - Validate RTO/RPO targets
  - Update DR documentation

- [ ] **Security Updates**
  - Apply security patches
  - Update dependencies
  - Review compliance status

- [ ] **Performance Optimization**
  - Analyze performance trends
  - Optimize database queries
  - Review caching strategies

#### Quarterly Tasks
- [ ] **Access Review**
  - Review user access and permissions
  - Remove unused accounts
  - Update role assignments

- [ ] **Architecture Review**
  - Review system architecture
  - Plan for improvements
  - Update documentation

### Backup Procedures

#### Database Backup (Automated)
```bash
# Daily automated backups via AWS RDS
# Retention: 7 days point-in-time recovery

# Manual backup
aws rds create-db-snapshot \
  --db-instance-identifier jorge-production-db \
  --db-snapshot-identifier manual-backup-$(date +%Y%m%d)
```

#### Configuration Backup
```bash
# Kubernetes configurations
kubectl get all -n jorge-revenue-platform -o yaml > jorge-k8s-backup-$(date +%Y%m%d).yaml

# Helm values
helm get values jorge-platform -n jorge-revenue-platform > jorge-helm-values-$(date +%Y%m%d).yaml
```

### Update Procedures

#### Security Updates (High Priority)
1. **Assessment**: Review CVE impact on Jorge platform
2. **Testing**: Test updates in staging environment
3. **Deployment**: Use CI/CD pipeline for production deployment
4. **Validation**: Verify all systems functional post-update

#### Feature Updates (Regular)
1. **Development**: Feature development and testing
2. **Code Review**: Security and performance review
3. **Staging**: Deploy to staging for validation
4. **Production**: Blue-green deployment with monitoring

---

## Incident Response

### Incident Classification

#### Incident Types
- **P0 (Critical)**: Complete service outage, data breach
- **P1 (High)**: Partial outage, degraded performance
- **P2 (Medium)**: Feature issues, minor performance impact
- **P3 (Low)**: Cosmetic issues, non-critical bugs

### Response Procedures

#### P0 - Critical Incidents

**Response Time**: <5 minutes

**Actions**:
1. **Immediate Response**
   - Acknowledge incident
   - Assess impact and scope
   - Activate incident response team

2. **Communication**
   ```
   Subject: [P0] Critical Incident - Jorge Platform Outage

   INCIDENT SUMMARY:
   - Start Time: [timestamp]
   - Impact: [service affected]
   - Status: Investigating
   - ETA: TBD

   ACTIONS TAKEN:
   - [list actions]

   NEXT UPDATE: 15 minutes
   ```

3. **Resolution Process**
   - Implement immediate workaround if available
   - Identify root cause
   - Apply permanent fix
   - Monitor for stability

4. **Post-Incident**
   - Conduct post-mortem within 48 hours
   - Document lessons learned
   - Implement improvements

#### P1 - High Priority Incidents

**Response Time**: <30 minutes

**Process**: Similar to P0 but with extended timelines
- Updates every 1 hour during business hours
- Resolution target: <4 hours
- Full team notification

### Communication Templates

#### Status Page Updates
```
Jorge Real Estate AI Platform - Incident Status

IDENTIFIED: We are currently investigating an issue affecting [service]
INVESTIGATING: We have identified the issue and are working on a resolution
MONITORING: A fix has been implemented and we are monitoring the situation
RESOLVED: The issue has been resolved and all services are operational
```

#### Client Communication
```
Subject: Service Update - Jorge AI Platform

Dear Jorge,

We experienced a brief service disruption today affecting [specific functionality].

Timeline:
- Issue detected: [time]
- Resolution applied: [time]
- Full service restored: [time]

Impact: [description of what was affected]

Root Cause: [brief technical explanation]

Prevention: [steps taken to prevent recurrence]

We apologize for any inconvenience. Please contact us with any questions.

Best regards,
Jorge Platform Operations Team
```

---

## Disaster Recovery

### Recovery Objectives

- **RTO (Recovery Time Objective)**: 2 hours
- **RPO (Recovery Point Objective)**: 1 hour
- **Data Loss Tolerance**: <1 hour of transactions

### Disaster Scenarios

#### 1. Complete AWS Region Failure

**Recovery Plan**:
1. **Activate DR Site**: Switch to backup AWS region
2. **Database Recovery**: Restore from cross-region backup
3. **DNS Failover**: Update DNS to point to DR site
4. **Validation**: Run full system validation
5. **Communication**: Notify stakeholders

**Estimated Recovery Time**: 4 hours

#### 2. Database Corruption

**Recovery Plan**:
1. **Immediate**: Switch to read replica
2. **Assessment**: Determine corruption extent
3. **Recovery**: Restore from last known good backup
4. **Validation**: Verify data integrity
5. **Cutover**: Switch traffic back to primary

**Estimated Recovery Time**: 2 hours

#### 3. Kubernetes Cluster Failure

**Recovery Plan**:
1. **New Cluster**: Create new EKS cluster
2. **Configuration**: Apply stored configurations
3. **Data Recovery**: Reconnect to existing databases
4. **Deployment**: Deploy latest application version
5. **Testing**: Verify all functionality

**Estimated Recovery Time**: 3 hours

### DR Testing Schedule

#### Monthly DR Tests
- **Database Recovery**: Test backup restoration
- **Application Recovery**: Deploy to DR environment
- **Network Connectivity**: Verify all connections
- **Monitoring**: Confirm monitoring systems work

#### Quarterly Full DR Test
- **Complete Failover**: Full switch to DR environment
- **Business Validation**: Test Jorge bot functionality
- **Performance Validation**: Verify SLA compliance
- **Failback**: Return to primary environment

### Backup Strategy

#### Database Backups
- **Frequency**: Continuous (point-in-time recovery)
- **Retention**: 7 days automated, monthly for 1 year
- **Location**: Cross-region replication
- **Validation**: Daily backup validation tests

#### Application Backups
- **Container Images**: Stored in ECR with 30-day retention
- **Configurations**: Daily backup of Kubernetes configs
- **Secrets**: Encrypted backup of all secrets
- **Code**: Git repository with tags for all releases

---

## Contact Information

### Production Support Team

#### Primary Contacts
```
Production Operations Lead
Email: operations@jorge-revenue.com
Phone: [24/7 on-call number]
Slack: @ops-lead

Platform Engineering Team
Email: platform@jorge-revenue.com
Slack: #platform-engineering

Security Team
Email: security@jorge-revenue.com
Phone: [emergency security line]
Slack: #security-incidents
```

#### Jorge (Client)
```
Email: realtorjorgesales@gmail.com
Phone: [client phone number]
Preferred Contact: Slack during incidents
```

#### Escalation Matrix

| Issue Type | Primary | Secondary | Executive |
|------------|---------|-----------|-----------|
| Critical Outage | Ops Lead | Platform Team | CTO |
| Security Incident | Security Team | Ops Lead | CISO |
| Performance Issues | Platform Team | ML Team | CTO |
| Jorge Bot Issues | Product Team | ML Team | CPO |

#### External Vendors

```
AWS Support (Business)
Case Priority: High for P0/P1 incidents
TAM Contact: [tam-email@amazon.com]

Anthropic Support
Email: support@anthropic.com
Priority: Claude API issues

GoHighLevel Support
Email: support@gohighlevel.com
Priority: CRM integration issues
```

### Emergency Procedures

#### After-Hours Incidents
1. **P0/P1**: Immediately contact on-call engineer
2. **Assessment**: Determine if client notification needed
3. **Communication**: Use incident communication templates
4. **Documentation**: Log all actions in incident tracker

#### Business Hours Support
- **Slack**: #jorge-platform-support (monitored 9 AM - 6 PM ET)
- **Email**: support@jorge-revenue.com
- **Phone**: [business hours support line]

### Documentation Updates

This document should be reviewed and updated:
- **Monthly**: Update contact information and procedures
- **Quarterly**: Review and update all procedures
- **After Incidents**: Update based on lessons learned
- **Platform Changes**: Update when architecture changes

**Document Owner**: Platform Operations Team
**Next Review Date**: [Monthly review schedule]
**Version Control**: Stored in `/docs/production/` in main repository

---

**End of Production Operations Guide**

*This document contains sensitive operational information and should be treated as confidential. Distribution is limited to authorized personnel only.*