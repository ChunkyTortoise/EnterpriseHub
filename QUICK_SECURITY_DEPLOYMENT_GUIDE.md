# Quick Security Deployment Guide
**Jorge's Revenue Acceleration Platform - Week 1 Actions**

**Status:** ⚠️ **CRITICAL ACTIONS REQUIRED BEFORE PRODUCTION**

---

## Pre-Flight Checklist (30 Minutes)

```bash
# 1. Check current security status
python3 scripts/validate_enterprise_security.py

# 2. Run security test suite
pytest tests/security/test_enterprise_security_comprehensive.py -v

# 3. Verify no secrets in repo
git ls-files | grep -E '\.env$|\.env\.' | grep -v '.template'

# If any files found above, proceed to Critical Actions
```

---

## Critical Actions (Week 1 - 4 Hours)

### Action 1: Remove Secrets from Repository (30 min)

**CRITICAL:** Prevents credential exposure in git history

```bash
# Step 1: Backup current .env files (LOCAL ONLY - DO NOT COMMIT)
cp .env .env.backup.$(date +%Y%m%d).local
cp .env.service6 .env.service6.backup.$(date +%Y%m%d).local
cp .env.service6.production .env.service6.production.backup.$(date +%Y%m%d).local
cp ghl_real_estate_ai/.env ghl_real_estate_ai/.env.backup.$(date +%Y%m%d).local

# Step 2: Remove from git (but keep local copies)
git rm --cached .env
git rm --cached .env.service6
git rm --cached .env.service6.production
git rm --cached ghl_real_estate_ai/.env

# Step 3: Update .gitignore
cat >> .gitignore << 'EOF'

# Environment files (NEVER commit)
.env
.env.local
.env.*.local
.env.service6
.env.service6.production
*.env.backup*
ghl_real_estate_ai/.env

# Keep templates only
!.env*.template
!.env*.example
EOF

# Step 4: Commit .gitignore changes
git add .gitignore
git commit -m "security: prevent .env files from being committed"
git push origin main

# Step 5: Verify files are removed from git (but exist locally)
git ls-files | grep -E '\.env$|\.env\.'  # Should only show templates
ls -la .env*  # Should show local files still exist

# Step 6: Secure local backup files
chmod 600 *.local  # Make backups readable only by you
```

---

### Action 2: Rotate All Secrets (45 min)

**CRITICAL:** All secrets that were in repository must be rotated

```bash
# Generate new secrets
echo "Generating new secrets..."

# JWT Secret (64 characters minimum)
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(64))" > .env.new.secrets

# GHL Webhook Secret (32 characters)
python3 -c "import secrets; print('GHL_WEBHOOK_SECRET=' + secrets.token_urlsafe(32))" >> .env.new.secrets

# Field Encryption Key (for future PII encryption)
python3 -c "import secrets; print('FIELD_ENCRYPTION_KEY=' + secrets.token_urlsafe(32))" >> .env.new.secrets

# Apollo Webhook Secret
python3 -c "import secrets; print('APOLLO_WEBHOOK_SECRET=' + secrets.token_urlsafe(32))" >> .env.new.secrets

# Twilio Webhook Secret
python3 -c "import secrets; print('TWILIO_WEBHOOK_SECRET=' + secrets.token_urlsafe(32))" >> .env.new.secrets

# SendGrid Webhook Secret
python3 -c "import secrets; print('SENDGRID_WEBHOOK_SECRET=' + secrets.token_urlsafe(32))" >> .env.new.secrets

# Redis Password (if not set)
python3 -c "import secrets; print('REDIS_PASSWORD=' + secrets.token_urlsafe(32))" >> .env.new.secrets

# Display generated secrets
echo "New secrets generated in .env.new.secrets:"
cat .env.new.secrets

# IMPORTANT: Save these secrets securely
# - Copy to password manager
# - Do NOT commit this file
# - Delete after updating production environment
```

---

### Action 3: Update Production Environment (60 min)

**Platform-Specific Instructions:**

#### Railway Deployment

```bash
# Set environment variables in Railway
railway variables set JWT_SECRET_KEY="$(grep JWT_SECRET_KEY .env.new.secrets | cut -d= -f2)"
railway variables set GHL_WEBHOOK_SECRET="$(grep GHL_WEBHOOK_SECRET .env.new.secrets | cut -d= -f2)"
railway variables set FIELD_ENCRYPTION_KEY="$(grep FIELD_ENCRYPTION_KEY .env.new.secrets | cut -d= -f2)"
railway variables set APOLLO_WEBHOOK_SECRET="$(grep APOLLO_WEBHOOK_SECRET .env.new.secrets | cut -d= -f2)"
railway variables set TWILIO_WEBHOOK_SECRET="$(grep TWILIO_WEBHOOK_SECRET .env.new.secrets | cut -d= -f2)"
railway variables set SENDGRID_WEBHOOK_SECRET="$(grep SENDGRID_WEBHOOK_SECRET .env.new.secrets | cut -d= -f2)"

# Enable database SSL
railway variables set DATABASE_URL="$(railway variables get DATABASE_URL)?sslmode=require"

# Set environment to production
railway variables set ENVIRONMENT="production"

# Verify variables set correctly
railway variables list
```

#### Heroku Deployment

```bash
# Set config vars
heroku config:set JWT_SECRET_KEY="$(grep JWT_SECRET_KEY .env.new.secrets | cut -d= -f2)"
heroku config:set GHL_WEBHOOK_SECRET="$(grep GHL_WEBHOOK_SECRET .env.new.secrets | cut -d= -f2)"
# ... repeat for other secrets

# Enable database SSL
heroku config:set DATABASE_URL="$(heroku config:get DATABASE_URL)?sslmode=require"

# Verify
heroku config
```

#### Docker/Manual Deployment

```bash
# Update .env file on server (SSH into server first)
ssh user@production-server

# Backup current .env
sudo cp /app/.env /app/.env.backup.$(date +%Y%m%d)

# Update with new secrets (use secure editor)
sudo nano /app/.env
# Paste new secrets from .env.new.secrets

# Verify file permissions
sudo chmod 600 /app/.env

# Restart services
sudo docker-compose down
sudo docker-compose up -d

# Verify services started
sudo docker-compose ps
```

---

### Action 4: Deploy Hardened Docker Configuration (60 min)

**Update Dockerfile:**

```dockerfile
# Multi-stage build for security
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=appuser:appuser . .

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "ghl_real_estate_ai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Deploy:**

```bash
# Rebuild Docker image
docker-compose build --no-cache

# Deploy
docker-compose up -d

# Verify non-root user
docker exec <container_id> whoami  # Should output: appuser
```

---

### Action 5: Harden CORS Configuration (30 min)

**Update `ghl_real_estate_ai/api/main.py`:**

```python
def get_cors_origins():
    """Get CORS origins with strict production filtering."""
    environment = os.getenv("ENVIRONMENT", "development")

    production_origins = [
        "https://app.gohighlevel.com",
        "https://*.gohighlevel.com",
    ]

    if environment == "production":
        # Only HTTPS origins in production
        streamlit_url = os.getenv("STREAMLIT_URL")
        if streamlit_url and streamlit_url.startswith("https://"):
            production_origins.append(streamlit_url)

        frontend_url = os.getenv("FRONTEND_URL")
        if frontend_url and frontend_url.startswith("https://"):
            production_origins.append(frontend_url)

        return production_origins

    elif environment == "development":
        return production_origins + [
            "http://localhost:8501",
            "http://localhost:3000",
            "http://127.0.0.1:8501",
        ]

    else:
        raise ValueError(f"Invalid ENVIRONMENT: {environment}")

# Replace existing ALLOWED_ORIGINS with:
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    max_age=600
)
```

**Deploy:**

```bash
# Commit changes
git add ghl_real_estate_ai/api/main.py
git commit -m "security: harden CORS configuration for production"
git push origin main

# Deploy to production
railway up  # or heroku deploy, docker restart, etc.
```

---

## Validation (15 Minutes)

### Post-Deployment Verification

```bash
# 1. Verify secrets removed from repository
git ls-files | grep -E '\.env$|\.env\.' | grep -v '.template'
# Expected: Only .template files

# 2. Run security validation
python3 scripts/validate_enterprise_security.py
# Expected: Risk score <20, 0 critical issues

# 3. Run security tests
pytest tests/security/test_enterprise_security_comprehensive.py -v
# Expected: 100+ tests passed

# 4. Test production endpoints
curl https://your-app.railway.app/health
# Expected: {"status": "healthy"}

# 5. Verify HTTPS redirect
curl -I http://your-app.railway.app
# Expected: 301/302 redirect to https://

# 6. Test JWT authentication
curl -H "Authorization: Bearer invalid_token" \
     https://your-app.railway.app/api/leads
# Expected: 401 Unauthorized

# 7. Test rate limiting
for i in {1..105}; do
    curl -s https://your-app.railway.app/health > /dev/null
done
# Expected: Last requests return 429 Too Many Requests

# 8. Test webhook signature (example with GHL)
curl -X POST https://your-app.railway.app/api/webhooks/ghl \
     -H "Content-Type: application/json" \
     -d '{"test":"data"}'
# Expected: 401 Unauthorized (no signature)
```

---

## Cleanup (5 Minutes)

```bash
# 1. Securely delete temporary secret files
shred -u .env.new.secrets  # Linux
rm -P .env.new.secrets  # macOS

# 2. Keep local .env files secure
chmod 600 .env .env.service6 .env.service6.production

# 3. Keep local backups secure (move to secure location)
mkdir -p ~/.secure-backups/jorge-platform
mv *.env.backup*.local ~/.secure-backups/jorge-platform/
chmod 700 ~/.secure-backups/jorge-platform
chmod 600 ~/.secure-backups/jorge-platform/*

# 4. Update documentation
echo "Secrets rotated on $(date)" >> SECURITY_CHANGELOG.md
```

---

## Security Monitoring Setup (30 Minutes)

### Enable Real-Time Alerts

```bash
# 1. Configure email alerts (example with SendGrid)
railway variables set ALERT_EMAIL="security@example.com"
railway variables set SENDGRID_API_KEY="your_sendgrid_key"

# 2. Set alert thresholds
railway variables set ALERT_THRESHOLD_FAILED_LOGINS="5"
railway variables set ALERT_THRESHOLD_RATE_LIMIT="100"

# 3. Enable Slack notifications (optional)
railway variables set SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# 4. Deploy security monitoring dashboard
railway run streamlit run ghl_real_estate_ai/streamlit_demo/components/security_monitoring_dashboard.py
```

### Configure Logging

```bash
# 1. Enable verbose security logging
railway variables set LOG_LEVEL="INFO"
railway variables set AUDIT_LOG_VERBOSE="true"

# 2. Set log retention
railway variables set AUDIT_LOG_RETENTION_DAYS="730"  # 2 years

# 3. Verify logging
railway logs --tail
# Look for: "AUDIT:" entries
```

---

## Troubleshooting

### Issue: Services won't start after secret rotation

```bash
# Check environment variables
railway variables list

# Verify secrets format (no quotes, spaces, newlines)
railway variables get JWT_SECRET_KEY

# Check container logs
railway logs --tail 100

# Common fix: Restart services
railway restart
```

### Issue: Database connection fails

```bash
# Verify DATABASE_URL has sslmode parameter
railway variables get DATABASE_URL
# Should contain: ?sslmode=require

# Test database connection
railway run python3 -c "
from ghl_real_estate_ai.database.connection import get_database_engine
engine = get_database_engine()
print('Database connection: OK')
"
```

### Issue: 401 errors on all API calls

```bash
# Verify JWT secret is set correctly
railway variables get JWT_SECRET_KEY

# Check if secret has special characters that need escaping
# Re-generate if needed
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## Emergency Rollback

If issues occur, rollback procedure:

```bash
# 1. Restore previous secrets
railway variables set JWT_SECRET_KEY="<previous_value>"

# 2. Rollback code
git revert <commit_hash>
git push origin main

# 3. Redeploy
railway up

# 4. Verify services
curl https://your-app.railway.app/health
```

---

## Next Steps

After completing Week 1 critical actions:

### Week 2-4: High Priority
- [ ] Implement PII field encryption
- [ ] Deploy log data masking
- [ ] Set up automated dependency scanning
- [ ] Configure security monitoring dashboard
- [ ] Complete GDPR documentation

### Month 2: Validation
- [ ] Schedule external penetration test
- [ ] SOC2 audit preparation
- [ ] Load testing with security
- [ ] Security architecture review

---

## Support & Resources

### Documentation
- **Full Security Guide:** `ENTERPRISE_SECURITY_HARDENING_GUIDE.md`
- **Incident Response:** `INCIDENT_RESPONSE_PLAYBOOK.md`
- **Validation Report:** `SECURITY_VALIDATION_SUMMARY.md`
- **Complete Handoff:** `PHASE_4.3_SECURITY_COMPLIANCE_COMPLETE.md`

### Scripts
- **Security Validation:** `scripts/validate_enterprise_security.py`
- **Security Tests:** `tests/security/test_enterprise_security_comprehensive.py`

### Contact
- Security Team: security@example.com
- Emergency: +1-XXX-XXX-XXXX

---

**Time Estimate:** 4 hours total
**Risk Level:** CRITICAL (must complete before production)
**Dependencies:** Git, Python 3.11+, Railway CLI (or equivalent)

**Status after completion:** ✅ Production ready with enterprise-grade security

---

**Last Updated:** January 18, 2026
**Version:** 1.0
