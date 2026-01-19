# Security Incident Response Playbook
**Jorge's Revenue Acceleration Platform**

**Version:** 1.0
**Last Updated:** January 18, 2026
**Classification:** Internal - Confidential
**Owner:** Security Team

---

## Table of Contents

1. [Overview](#overview)
2. [Incident Classification](#incident-classification)
3. [Response Team](#response-team)
4. [Response Procedures](#response-procedures)
5. [Communication Protocols](#communication-protocols)
6. [Technical Response Actions](#technical-response-actions)
7. [Post-Incident Activities](#post-incident-activities)
8. [Compliance Requirements](#compliance-requirements)
9. [Emergency Contacts](#emergency-contacts)
10. [Appendices](#appendices)

---

## Overview

### Purpose
This playbook provides standardized procedures for responding to security incidents affecting Jorge's Revenue Acceleration Platform. It ensures rapid, effective, and compliant incident response.

### Scope
- All production systems and services
- Customer data and PII
- Authentication and authorization systems
- Third-party integrations (GHL, Apollo, Twilio, SendGrid)
- Infrastructure and cloud services

### Objectives
- Minimize business impact and data loss
- Preserve evidence for investigation
- Restore normal operations quickly
- Meet compliance requirements (GDPR, HIPAA, SOC2)
- Learn and improve security posture

---

## Incident Classification

### Severity Levels

#### P1 - CRITICAL (Response Time: 15 minutes)

**Definition:** Severe impact to confidentiality, integrity, or availability

**Examples:**
- Active data breach with confirmed PII exposure
- Ransomware attack encrypting production systems
- Complete system compromise by unauthorized actor
- Authentication system breach allowing unauthorized access
- Mass data exfiltration detected
- Zero-day exploit affecting production

**Response Requirements:**
- Immediate notification to C-suite
- 24/7 response team activation
- External incident response team (if needed)
- Legal and compliance team notification
- Customer notification preparation

---

#### P2 - HIGH (Response Time: 1 hour)

**Definition:** Significant security impact requiring urgent attention

**Examples:**
- Unauthorized access to sensitive data (not confirmed exposure)
- DDoS attack degrading service availability
- Malware detected on production systems
- Privilege escalation vulnerability actively exploited
- Insider threat detected
- Failed ransomware attempt
- Compromise of administrative accounts

**Response Requirements:**
- Security team lead notification
- Investigation team mobilization
- Evidence preservation
- Preliminary containment actions

---

#### P3 - MEDIUM (Response Time: 4 hours)

**Definition:** Moderate security concern requiring investigation

**Examples:**
- Suspicious activity detected by monitoring
- Multiple failed authentication attempts from single source
- Vulnerability disclosure from researcher
- Policy violations by internal users
- Anomalous data access patterns
- Phishing attempt targeting employees

**Response Requirements:**
- Security team investigation
- Documentation of findings
- Remediation planning
- User communication (if applicable)

---

#### P4 - LOW (Response Time: 24 hours)

**Definition:** Minor security issue requiring routine handling

**Examples:**
- Security misconfigurations without exploitation
- Minor policy violations
- Low-severity vulnerability findings
- False positive from security tools
- Informational security notices

**Response Requirements:**
- Documentation in ticketing system
- Routine remediation
- Update security controls

---

## Response Team

### Core Response Team

#### Incident Commander (IC)
- **Role:** Overall incident coordination and decision-making
- **Primary:** Security Team Lead
- **Backup:** Engineering Manager
- **Responsibilities:**
  - Declare incidents and assign severity
  - Coordinate response activities
  - Manage communications
  - Make critical decisions
  - Interface with executive team

#### Technical Lead
- **Role:** Technical investigation and remediation
- **Primary:** Senior Security Engineer
- **Backup:** Platform Engineer
- **Responsibilities:**
  - Lead technical investigation
  - Coordinate containment actions
  - Direct remediation efforts
  - Preserve evidence
  - Document technical findings

#### Communications Lead
- **Role:** Internal and external communications
- **Primary:** Product Manager
- **Backup:** Customer Success Manager
- **Responsibilities:**
  - Draft and send communications
  - Manage customer notifications
  - Coordinate with PR/legal
  - Update stakeholders
  - Maintain communication log

#### Compliance Lead
- **Role:** Ensure regulatory compliance
- **Primary:** Legal Counsel
- **Backup:** Compliance Officer
- **Responsibilities:**
  - Assess notification requirements
  - Ensure GDPR/HIPAA/SOC2 compliance
  - Document compliance actions
  - Interface with regulators
  - Manage breach notifications

### Extended Team (On-Call)
- Database Administrator
- Cloud Infrastructure Engineer
- Application Developers
- Customer Support Lead
- External IR Consultant (if needed)

### Escalation Chain
1. Security Team → Incident Commander
2. Incident Commander → CTO
3. CTO → CEO
4. CEO → Board of Directors (P1 only)

---

## Response Procedures

### Phase 1: Detection & Analysis (Target: 15-60 minutes)

#### 1.1 Incident Detection Sources
- Security monitoring dashboard alerts
- Audit log anomalies
- User reports
- External notifications (security researchers, partners)
- Threat intelligence feeds
- Automated security tools

#### 1.2 Initial Analysis Steps

```markdown
[ ] Confirm incident is real (not false positive)
[ ] Document initial observations with timestamps
[ ] Classify severity level (P1-P4)
[ ] Identify affected systems and data
[ ] Assess scope and impact
[ ] Preserve evidence (logs, screenshots, memory dumps)
[ ] Declare incident and activate response team
```

#### 1.3 Evidence Collection

**Logs to Preserve:**
```bash
# Application logs
tail -n 10000 /var/log/application.log > evidence/app-$(date +%Y%m%d-%H%M%S).log

# Audit logs from Redis
redis-cli LRANGE audit_log 0 -1 > evidence/audit-$(date +%Y%m%d-%H%M%S).log

# Database logs
psql -c "SELECT * FROM audit_events WHERE timestamp > NOW() - INTERVAL '24 hours'" > evidence/db-audit.log

# System logs
journalctl --since "2 hours ago" > evidence/system-$(date +%Y%m%d-%H%M%S).log

# Network logs (if available)
tcpdump -w evidence/network-$(date +%Y%m%d-%H%M%S).pcap -i eth0

# Create hash of evidence files
sha256sum evidence/* > evidence/checksums.txt
```

**Screenshots:**
- Security monitoring dashboards
- Suspicious activity indicators
- Error messages
- Configuration screens

**Memory Dumps (if needed):**
```bash
# Docker container memory
docker exec <container> gcore <pid>

# System memory (advanced)
lime-forensics capture
```

---

### Phase 2: Containment (Target: 30 minutes - 2 hours)

#### 2.1 Short-term Containment
Immediate actions to stop active attack while maintaining evidence.

**Isolate Affected Systems:**
```bash
# Disable affected user accounts
redis-cli SADD "disabled_users" "user123"

# Block malicious IP addresses
iptables -A INPUT -s <malicious_ip> -j DROP
iptables-save > /etc/iptables/rules.v4

# Rate limit suspicious endpoints
redis-cli SET "emergency_rate_limit:/api/target" "1"  # 1 request/minute

# Revoke compromised JWT tokens
redis-cli SADD "blacklist_token:*" "<token_id>"

# Disable compromised API keys
redis-cli SET "disabled_api_keys:<key_id>" "1"
```

**Network Segmentation:**
```bash
# Isolate affected containers/services
docker network disconnect app-network <container_id>

# Create isolated investigation network
docker network create --internal incident-investigation
docker network connect incident-investigation <container_id>
```

**Enable Enhanced Logging:**
```python
# Increase logging verbosity
# Update environment variable
export LOG_LEVEL=DEBUG
export AUDIT_LOG_VERBOSE=true

# Restart services with enhanced logging
docker-compose restart app
```

#### 2.2 Long-term Containment
Sustainable containment while remediation occurs.

```markdown
[ ] Implement network access restrictions
[ ] Deploy additional monitoring
[ ] Enable enhanced authentication
[ ] Backup affected systems (for forensics)
[ ] Prepare for system rebuild if needed
[ ] Document all containment actions
```

---

### Phase 3: Eradication (Target: 2-8 hours)

#### 3.1 Remove Threat

**Malware Removal:**
```bash
# Scan for malware
clamscan -r /app --infected --remove

# Check for backdoors in common locations
find /app -name "*.php" -o -name "*.py" | xargs grep -l "eval\|exec\|system"

# Remove unauthorized files
rm -rf /app/malicious-files/
```

**Patch Vulnerabilities:**
```bash
# Update dependencies
pip install --upgrade -r requirements.txt

# Apply security patches
apt-get update && apt-get upgrade -y

# Update application code
git pull origin main  # After code review
```

**Reset Compromised Credentials:**
```bash
# Generate new secrets
python3 -c "import secrets; print(secrets.token_urlsafe(64))" > new-jwt-secret.txt
python3 -c "import secrets; print(secrets.token_urlsafe(32))" > new-webhook-secret.txt

# Update secrets in production
# (Using Railway, Heroku, or cloud provider's secrets management)
railway variables set JWT_SECRET_KEY=$(cat new-jwt-secret.txt)

# Rotate database passwords
psql -c "ALTER USER appuser PASSWORD 'new_secure_password';"

# Revoke and regenerate API keys
# Update GHL API key, Anthropic key, etc.
```

#### 3.2 Strengthen Defenses

```python
# Enable additional security controls
# Update security configuration

# Add IP to blacklist
from ghl_real_estate_ai.services.security_framework import SecurityFramework
security = SecurityFramework()
await security.blacklist_ip("<malicious_ip>", duration_hours=720)  # 30 days

# Increase authentication requirements
# Temporarily require MFA for all users (if available)

# Enhanced monitoring rules
# Add detection for similar attack patterns
```

---

### Phase 4: Recovery (Target: 2-24 hours)

#### 4.1 System Restoration

**Restore from Clean Backup:**
```bash
# Verify backup integrity
sha256sum backup.tar.gz
# Compare against known-good checksum

# Restore database
pg_restore -d enterprisehub backup.sql

# Restore application files
tar -xzf backup.tar.gz -C /app

# Verify restoration
python3 scripts/verify_integrity.py
```

**Rebuild Compromised Systems:**
```bash
# Rebuild Docker images from scratch
docker-compose down -v  # Remove volumes
docker-compose build --no-cache
docker-compose up -d

# Verify services are healthy
docker-compose ps
curl http://localhost:8000/health
```

#### 4.2 Service Restoration

```markdown
[ ] Test all critical functionality
[ ] Verify data integrity
[ ] Confirm security controls active
[ ] Monitor for re-infection
[ ] Gradually restore user access
[ ] Resume normal operations
[ ] Document recovery process
```

**Gradual Rollout:**
```bash
# Phase 1: Internal testing (30 min)
# - Engineering team access only
# - Functional testing
# - Security validation

# Phase 2: Limited user access (2 hours)
# - 10% of users
# - Monitor metrics
# - Watch for issues

# Phase 3: Full restoration (6 hours)
# - All users
# - Continued monitoring
# - On-call support ready
```

---

### Phase 5: Post-Incident Activities (Target: 1-2 weeks)

#### 5.1 Lessons Learned Meeting (Within 48 hours)

**Agenda:**
1. Incident timeline review
2. What went well?
3. What could be improved?
4. Root cause analysis
5. Action items and owners

**Required Attendees:**
- Incident Commander
- All core response team members
- Relevant stakeholders

#### 5.2 Post-Incident Report

**Report Sections:**
1. Executive Summary
2. Incident Timeline
3. Impact Assessment
4. Root Cause Analysis
5. Response Actions
6. Lessons Learned
7. Recommendations
8. Compliance Documentation

**Template:**
```markdown
# Post-Incident Report: [Incident ID]

## Executive Summary
- Incident Type:
- Severity:
- Detection Time:
- Resolution Time:
- Systems Affected:
- Data Impact:

## Detailed Timeline
| Time | Event | Action Taken | Owner |
|------|-------|--------------|-------|
| ... | ... | ... | ... |

## Root Cause
[Detailed analysis of how incident occurred]

## Impact Assessment
- Users Affected:
- Data Compromised:
- Service Downtime:
- Financial Impact:

## Response Effectiveness
- What Worked:
- What Didn't Work:
- Gaps Identified:

## Remediation Actions
| Action | Priority | Owner | Due Date | Status |
|--------|----------|-------|----------|--------|
| ... | ... | ... | ... | ... |

## Compliance Actions
- Notifications sent:
- Regulatory filings:
- Documentation completed:
```

#### 5.3 Security Improvements

```markdown
[ ] Update security policies
[ ] Enhance detection rules
[ ] Implement new controls
[ ] Conduct additional training
[ ] Update incident response procedures
[ ] Schedule follow-up review (30 days)
```

---

## Communication Protocols

### Internal Communications

#### P1 Incidents
- **Immediate:** Slack #security-incidents channel
- **Within 30 min:** Email to executive team
- **Within 1 hour:** All-hands notification (if warranted)

#### P2 Incidents
- **Immediate:** Slack #security-incidents channel
- **Within 2 hours:** Email to relevant stakeholders

#### P3-P4 Incidents
- **Standard:** Slack #security-incidents channel
- **Weekly:** Security summary email

### External Communications

#### Customer Notifications

**When Required:**
- Confirmed data breach
- Extended service outage
- Security issue affecting their data
- Compliance requirement (GDPR, HIPAA)

**Approval Required:**
- P1: CEO + Legal
- P2: CTO + Legal
- P3-P4: Security Team Lead

**Template:**
```
Subject: Security Notice - [Brief Description]

Dear [Customer Name],

We are writing to inform you of a security incident that occurred on [date]
affecting [scope].

What Happened:
[Brief, clear explanation]

What Information Was Affected:
[Specific data types]

What We're Doing:
[Response actions taken]

What You Should Do:
[Recommended actions for customers]

Resources:
[Support contact, FAQ link]

We sincerely apologize for this incident and are committed to protecting your data.

[Signature]
```

### Regulatory Notifications

#### GDPR (EU Customers)
- **Timing:** Within 72 hours of becoming aware
- **Who:** Data Protection Authority in relevant EU country
- **What:** Use GDPR breach notification template
- **Process:** Compliance Lead coordinates

#### HIPAA (Healthcare Customers)
- **Timing:** Within 60 days
- **Who:** HHS Office for Civil Rights + affected individuals
- **What:** Use HHS breach notification template
- **Process:** HIPAA Compliance Officer coordinates

#### PCI DSS (Payment Processing)
- **Timing:** Within 24 hours
- **Who:** Payment card brands (Visa, Mastercard, etc.)
- **What:** PCI incident report
- **Process:** PCI Compliance Lead coordinates

---

## Technical Response Actions

### Emergency Access Controls

#### Revoke All JWT Tokens
```python
# Emergency token revocation
from ghl_real_estate_ai.api.middleware.enhanced_auth import enhanced_auth
import redis.asyncio as aioredis

async def emergency_revoke_all_tokens():
    """Revoke all JWT tokens - forces re-authentication."""
    redis = await aioredis.from_url(settings.redis_url)

    # Add all active token IDs to blacklist
    # (This is a simplified example - actual implementation would track tokens)

    # Set emergency flag to require re-auth
    await redis.set("emergency_reauth_required", "1")

    print("All tokens revoked - users must re-authenticate")

# Run
asyncio.run(emergency_revoke_all_tokens())
```

#### Disable User Account
```python
from ghl_real_estate_ai.services.tenant_service import TenantService

async def disable_user(user_id: str, reason: str):
    """Disable user account."""
    redis = await aioredis.from_url(settings.redis_url)

    # Add to disabled users set
    await redis.sadd("disabled_users", user_id)

    # Log action
    logger.critical(
        f"User account disabled: {user_id}",
        extra={"reason": reason, "action": "emergency_disable"}
    )
```

#### Block IP Address
```bash
# Block at firewall level
iptables -A INPUT -s <ip_address> -j DROP

# Block at application level
redis-cli SADD "blocked_ips" "<ip_address>"

# Block at cloud provider level (Railway example)
railway firewall block <ip_address>
```

### System Isolation

#### Isolate Compromised Service
```bash
# Docker: Disconnect from network
docker network disconnect app-network service-name

# Kubernetes: Delete service (maintain pod for investigation)
kubectl delete service service-name

# Stop accepting new requests
kubectl scale deployment service-name --replicas=0
```

#### Enable Maintenance Mode
```python
# Set maintenance mode flag
redis-cli SET "maintenance_mode" "1" EX 3600  # 1 hour

# Application checks this flag and returns 503
@app.middleware("http")
async def maintenance_mode_middleware(request: Request, call_next):
    redis = await get_redis()
    if await redis.get("maintenance_mode"):
        return JSONResponse(
            status_code=503,
            content={"message": "System under maintenance"}
        )
    return await call_next(request)
```

### Forensic Data Collection

#### Database Snapshot
```bash
# PostgreSQL dump with timestamps
pg_dump enterprisehub > forensics/db-snapshot-$(date +%Y%m%d-%H%M%S).sql

# Dump specific tables
pg_dump -t audit_events -t access_logs enterprisehub > forensics/security-tables.sql
```

#### Redis Snapshot
```bash
# Trigger Redis save
redis-cli BGSAVE

# Copy RDB file
cp /var/lib/redis/dump.rdb forensics/redis-snapshot-$(date +%Y%m%d-%H%M%S).rdb
```

#### Application State
```bash
# Docker logs
docker logs app-container > forensics/app-logs-$(date +%Y%m%d-%H%M%S).log

# Process list
docker exec app-container ps aux > forensics/processes.txt

# Network connections
docker exec app-container netstat -an > forensics/connections.txt

# Environment variables (careful with secrets)
docker exec app-container env | grep -v SECRET > forensics/env.txt
```

---

## Post-Incident Activities

### Security Hardening Checklist

```markdown
## Authentication
[ ] Review and rotate all API keys
[ ] Update JWT secret key
[ ] Enable MFA for all admin accounts
[ ] Review user access permissions
[ ] Update password policies

## Network Security
[ ] Review firewall rules
[ ] Update IP blocklists
[ ] Verify TLS configuration
[ ] Check for exposed services

## Application Security
[ ] Scan for vulnerabilities
[ ] Update dependencies
[ ] Review code for backdoors
[ ] Update security headers
[ ] Verify input validation

## Infrastructure
[ ] Patch all systems
[ ] Review Docker configurations
[ ] Update access controls
[ ] Enable additional logging

## Monitoring
[ ] Add new detection rules
[ ] Configure new alerts
[ ] Update monitoring dashboards
[ ] Test incident detection

## Documentation
[ ] Update runbooks
[ ] Document lessons learned
[ ] Update IR procedures
[ ] Train team on new procedures
```

### Compliance Documentation

#### Evidence Preservation
```bash
# Create evidence package
mkdir -p evidence-package/
cp -r forensics/* evidence-package/
cp incident-timeline.md evidence-package/
cp response-actions.log evidence-package/

# Create evidence manifest
ls -lhR evidence-package/ > evidence-package/manifest.txt
sha256sum evidence-package/* > evidence-package/checksums.txt

# Encrypt evidence package
tar -czf evidence.tar.gz evidence-package/
gpg --encrypt --recipient security@example.com evidence.tar.gz

# Store securely (encrypted cloud storage)
aws s3 cp evidence.tar.gz.gpg s3://security-incidents/incident-001/
```

---

## Emergency Contacts

### Internal Contacts

| Role | Name | Phone | Email | Backup |
|------|------|-------|-------|--------|
| Incident Commander | [Name] | [Phone] | [Email] | [Backup] |
| CTO | [Name] | [Phone] | [Email] | [Backup] |
| CEO | [Name] | [Phone] | [Email] | - |
| Legal Counsel | [Name] | [Phone] | [Email] | [Backup] |
| PR Lead | [Name] | [Phone] | [Email] | [Backup] |

### External Contacts

| Service | Contact | Phone | Notes |
|---------|---------|-------|-------|
| Cloud Provider Support | | | P1 escalation process |
| External IR Firm | | | Retainer agreement |
| Law Enforcement | FBI IC3 | https://www.ic3.gov | For serious incidents |
| Legal Counsel (External) | | | Data breach specialist |

### Regulatory Contacts

| Regulator | Contact | Notes |
|-----------|---------|-------|
| EU Data Protection Authority | | GDPR breaches |
| HHS Office for Civil Rights | | HIPAA breaches |
| PCI Security Standards Council | | Payment card breaches |

---

## Appendices

### Appendix A: Incident Report Template

See [incident-report-template.md](./templates/incident-report-template.md)

### Appendix B: Communication Templates

See [communication-templates.md](./templates/communication-templates.md)

### Appendix C: Compliance Notification Templates

See [compliance-notifications.md](./templates/compliance-notifications.md)

### Appendix D: Forensic Collection Scripts

See [forensic-scripts/](./scripts/forensic-scripts/)

### Appendix E: Recovery Procedures

See [recovery-procedures.md](./runbooks/recovery-procedures.md)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-18 | Security Team | Initial version |

---

## Review and Updates

**Next Review Date:** February 18, 2026
**Review Frequency:** Monthly
**Update Triggers:**
- After any P1 or P2 incident
- Significant security changes
- New compliance requirements
- Organizational changes

---

**END OF PLAYBOOK**
