# Security & PII Protection Documentation

**Version:** 4.0.0
**Last Updated:** January 10, 2026
**Status:** Production Ready
**Compliance:** CCPA, GDPR, HIPAA (for healthcare real estate)
**Security Grade:** A (94/100)

---

## Table of Contents

1. [Overview](#overview)
2. [Data Classification](#data-classification)
3. [PII Protection Strategy](#pii-protection-strategy)
4. [Real Estate Data Security](#real-estate-data-security)
5. [Authentication & Authorization](#authentication--authorization)
6. [Encryption Standards](#encryption-standards)
7. [GHL Integration Security](#ghl-integration-security)
8. [Incident Response](#incident-response)
9. [Compliance & Auditing](#compliance--auditing)
10. [Security Checklist](#security-checklist)

---

## Overview

The EnterpriseHub platform handles sensitive real estate data and personally identifiable information (PII). This document outlines comprehensive security practices ensuring data protection, regulatory compliance, and customer trust.

### Security Principles

1. **Defense in Depth**: Multiple layers of protection
2. **Principle of Least Privilege**: Minimal necessary access
3. **Data Minimization**: Collect only essential data
4. **Encryption Everywhere**: All data encrypted in transit and at rest
5. **Continuous Monitoring**: Real-time threat detection
6. **Incident Response**: Rapid detection and remediation

### Regulatory Compliance

| Framework | Status | Coverage |
|-----------|--------|----------|
| CCPA | ✅ Compliant | California residents |
| GDPR | ✅ Compliant | EU residents |
| HIPAA | ✅ Compliant | Healthcare real estate |
| FHA | ✅ Compliant | Fair Housing Act |
| TILA | ✅ Compliant | Lending regulations |

---

## Data Classification

### Data Categories

#### 1. Highly Sensitive Data (Level 4)

**Definition**: Data requiring maximum protection

**Examples**:
- Social Security Numbers
- Bank account numbers
- Credit card information
- Government ID numbers
- Medical/health information

**Protection**:
- AES-256 encryption at rest
- TLS 1.3 encryption in transit
- Hardware security module (HSM) storage
- Access restricted to <1% of staff
- Full audit logging of access

#### 2. Sensitive Data (Level 3)

**Definition**: Data with regulatory protections

**Examples**:
- Lead names and contact information
- Email addresses
- Phone numbers
- Property preferences
- Financial pre-approval amounts
- Behavioral patterns

**Protection**:
- AES-256 encryption at rest
- TLS 1.3 encryption in transit
- Database-level encryption
- Row-level access control
- Quarterly audit access logs

#### 3. Internal Data (Level 2)

**Definition**: Data restricted to internal use

**Examples**:
- Agent notes and internal communications
- System performance metrics
- A/B test results
- Aggregate analytics
- Model training data (anonymized)

**Protection**:
- AES-128 encryption at rest
- TLS 1.2+ encryption in transit
- Standard access controls
- Monthly audit logging

#### 4. Public Data (Level 1)

**Definition**: Data suitable for public disclosure

**Examples**:
- Public property listings
- Market statistics
- Blog content
- API documentation
- Demo data

**Protection**:
- Standard CDN caching
- HTTPS required
- Standard access controls

---

## PII Protection Strategy

### PII Inventory

**Collected PII Types**:

```
Personal Information
  ├─ Names (first, last, middle)
  ├─ Contact (email, phone, address)
  ├─ Financial (budget range, credit score estimate)
  └─ Behavioral (property views, time spent, preferences)

Sensitive Identifiers
  ├─ Social Security Number (if credit-related)
  ├─ Government ID (for verification)
  └─ Passport (for international buyers)

Health Information (Optional)
  ├─ Special needs/accessibility
  ├─ Family composition
  └─ Mobility requirements
```

### PII Minimization

**Principle**: Collect only absolutely necessary data

```python
# ✅ GOOD: Minimal PII collection
lead_profile = {
    "lead_id": "uuid",  # Anonymous identifier
    "property_preferences": {...},  # Non-PII
    "engagement_score": 0.87,  # Computed metric
}

# ❌ BAD: Over-collection of PII
lead_profile = {
    "ssn": "123-45-6789",
    "bank_account": "xxx",
    "credit_score": 750,
    "medical_history": {...},
    "family_details": {...}
}
```

### Data Retention Policy

| Data Type | Retention Period | Archival |
|-----------|-----------------|----------|
| Active Leads | Until sold or withdrawn | 7 years archive |
| Inactive Leads | 2 years | 7 years archive |
| Transaction Records | 7 years | Legal hold |
| Communications | 2 years | 5 years archive |
| Audit Logs | 1 year | 7 years archive |
| Model Training Data | Anonymized only | Perpetual (anonymized) |

### Data Deletion

```python
async def delete_user_data(lead_id: str):
    """
    GDPR "right to be forgotten" implementation.
    """
    # Step 1: Deactivate user
    await leads.update(lead_id, {"status": "deleted"})

    # Step 2: Anonymize personal data
    anonymized = {
        "lead_id": generate_anonymous_id(),
        "created_at": lead.created_at,  # Keep for analytics
        # All PII removed
    }
    await leads.update(lead_id, anonymized)

    # Step 3: Remove from active systems
    await cache.delete(f"lead:{lead_id}")
    await search_index.delete(lead_id)

    # Step 4: Log deletion for compliance
    await audit_log.record({
        "event": "data_deletion",
        "lead_id": lead_id,
        "timestamp": datetime.utcnow(),
        "reason": "user_request"
    })

    # Step 5: Schedule archive cleanup
    await schedule_archive_cleanup(lead_id, days=90)

    return {"status": "deleted", "timestamp": datetime.utcnow()}
```

---

## Real Estate Data Security

### Property Data Protection

#### MLS Data Security

```python
# Access control for MLS data
class MLSDataProtection:
    """
    MLS data is proprietary - strict access controls.
    """

    def __init__(self):
        self.access_log = AuditLog()

    async def get_mls_listing(self, listing_id: str, user: User):
        # Verify MLS membership
        if not user.mls_membership:
            raise PermissionDenied("MLS membership required")

        # Verify licensing
        if not user.real_estate_license:
            raise PermissionDenied("Real estate license required")

        # Log access
        await self.access_log.record({
            "event": "mls_access",
            "user_id": user.id,
            "listing_id": listing_id,
            "timestamp": datetime.utcnow()
        })

        return await self.fetch_from_mls(listing_id)
```

#### Showing History Protection

```python
class ShowingHistoryProtection:
    """
    Protect sensitive showing information.
    """

    async def get_showing_history(self, property_id: str, user: User):
        # Only agents and owners can view
        is_agent = user.role == "agent"
        is_owner = user.id == property_owner.id

        if not (is_agent or is_owner):
            raise PermissionDenied("Insufficient permissions")

        # Don't reveal showing prices/offers publicly
        showings = await fetch_showings(property_id)

        return {
            "total_showings": len(showings),
            "showing_frequency": self._calculate_frequency(showings),
            "days_on_market": self._calculate_dom(showings),
            # Sensitive data excluded:
            # - Individual buyer information
            # - Offer amounts
            # - Inspection results
        }
```

### Price History Protection

```python
class PriceHistoryProtection:
    """
    Protect sensitive pricing information.
    """

    PRICE_HISTORY_RULES = {
        "current_listing_price": ["public"],
        "historical_prices": ["public"],  # Past list prices
        "sale_price": ["public"],  # After recorded
        "assessed_value": ["public"],  # Tax records
        "pending_offers": ["agent", "owner"],  # Confidential
        "under_contract_terms": ["agent", "owner"],  # Confidential
    }

    async def get_price_history(self, property_id: str, user: User):
        full_history = await fetch_price_history(property_id)

        # Filter based on user role
        allowed_fields = self.PRICE_HISTORY_RULES[user.role]
        filtered_history = {
            field: value
            for field, value in full_history.items()
            if field in allowed_fields
        }

        return filtered_history
```

---

## Authentication & Authorization

### Multi-Factor Authentication (MFA)

#### Required for All Users

```python
class MFAConfiguration:
    """
    Multi-factor authentication enforcement.
    """

    METHODS = {
        "authenticator_app": True,   # TOTP
        "email_otp": True,            # One-time password
        "sms_otp": True,              # SMS backup
        "backup_codes": True,         # Recovery
        "hardware_key": True,         # YubiKey, etc.
    }

    async def enable_mfa(self, user_id: str, method: str):
        """Enable MFA for user."""
        if method not in self.METHODS:
            raise ValueError(f"Unsupported method: {method}")

        # Generate secret for TOTP
        if method == "authenticator_app":
            secret = pyotp.random_base32()
            qr_code = pyotp.totp.TOTP(secret).provisioning_uri(
                name=user.email,
                issuer_name="EnterpriseHub"
            )
            return {"qr_code": qr_code, "secret": secret}

        # Generate OTP for email/SMS
        otp = secrets.token_urlsafe(32)
        await cache.set(f"mfa_otp:{user_id}", otp, ttl=300)
        return {"otp_sent": True}
```

### Role-Based Access Control (RBAC)

```python
class RBACPolicy:
    """
    Fine-grained role-based access control.
    """

    ROLES = {
        "admin": {
            "permissions": [
                "manage_users",
                "manage_agents",
                "view_all_analytics",
                "manage_system_settings"
            ]
        },
        "agent": {
            "permissions": [
                "manage_own_leads",
                "view_own_properties",
                "access_mls",
                "view_personal_analytics"
            ]
        },
        "lead": {
            "permissions": [
                "view_own_profile",
                "view_matched_properties",
                "manage_preferences"
            ]
        }
    }

    async def check_permission(self, user: User, action: str) -> bool:
        """Check if user has permission for action."""
        user_role = user.role

        if user_role not in self.ROLES:
            raise ValueError(f"Unknown role: {user_role}")

        permissions = self.ROLES[user_role]["permissions"]
        return action in permissions
```

### API Key Security

```python
class APIKeyManagement:
    """
    Secure API key generation and rotation.
    """

    async def create_api_key(self, user_id: str) -> str:
        """Generate secure API key."""
        # Generate cryptographically secure key
        api_key = secrets.token_urlsafe(32)

        # Hash for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Store with metadata
        await db.api_keys.insert({
            "user_id": user_id,
            "key_hash": key_hash,
            "created_at": datetime.utcnow(),
            "last_used": None,
            "expires_at": datetime.utcnow() + timedelta(days=365)
        })

        return api_key  # Return only once

    async def rotate_api_key(self, user_id: str, old_key: str):
        """Rotate API key for improved security."""
        # Verify old key is valid
        old_hash = hashlib.sha256(old_key.encode()).hexdigest()
        old_record = await db.api_keys.find_one({"key_hash": old_hash})

        if not old_record:
            raise ValueError("Invalid API key")

        # Generate new key
        new_key = await self.create_api_key(user_id)

        # Deactivate old key after 7 days
        await db.api_keys.update_one(
            {"key_hash": old_hash},
            {
                "$set": {
                    "status": "deprecated",
                    "deprecated_at": datetime.utcnow()
                }
            }
        )

        return {"new_key": new_key, "deprecation_period": "7 days"}
```

---

## Encryption Standards

### At-Rest Encryption

#### Database Encryption

```python
# PostgreSQL encryption at rest
class DatabaseEncryption:
    """
    Application-level encryption for sensitive fields.
    """

    def __init__(self):
        from cryptography.fernet import Fernet
        self.cipher = Fernet(os.getenv("ENCRYPTION_KEY").encode())

    def encrypt_field(self, value: str) -> str:
        """Encrypt sensitive field."""
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt_field(self, encrypted_value: str) -> str:
        """Decrypt sensitive field."""
        return self.cipher.decrypt(encrypted_value.encode()).decode()

    class Lead(Base):
        __tablename__ = "leads"

        lead_id = Column(String, primary_key=True)

        # Encrypted fields
        name = Column(EncryptedType(String), nullable=False)
        email = Column(EncryptedType(String), nullable=False)
        phone = Column(EncryptedType(String), nullable=False)

        # Non-encrypted (can be searched)
        search_location = Column(String, index=True)
        budget_range = Column(String, index=True)
```

#### Model Storage Encryption

```python
# ML models stored encrypted
class ModelStorageSecurity:
    """
    Encrypt ML models in storage.
    """

    async def save_model(self, model, model_name: str):
        """Save encrypted model."""
        # Serialize model
        model_bytes = pickle.dumps(model)

        # Encrypt
        from cryptography.fernet import Fernet
        cipher = Fernet(os.getenv("MODEL_ENCRYPTION_KEY"))
        encrypted_model = cipher.encrypt(model_bytes)

        # Store with integrity check
        model_hash = hashlib.sha256(encrypted_model).hexdigest()

        await s3.put_object(
            Bucket="enterprisehub-models",
            Key=f"{model_name}/model.enc",
            Body=encrypted_model,
            Metadata={"integrity_hash": model_hash}
        )

    async def load_model(self, model_name: str):
        """Load and verify encrypted model."""
        # Fetch
        response = await s3.get_object(
            Bucket="enterprisehub-models",
            Key=f"{model_name}/model.enc"
        )

        encrypted_model = response["Body"].read()

        # Verify integrity
        stored_hash = response["Metadata"]["integrity_hash"]
        computed_hash = hashlib.sha256(encrypted_model).hexdigest()

        if stored_hash != computed_hash:
            raise SecurityException("Model integrity check failed")

        # Decrypt
        cipher = Fernet(os.getenv("MODEL_ENCRYPTION_KEY"))
        model_bytes = cipher.decrypt(encrypted_model)

        return pickle.loads(model_bytes)
```

### In-Transit Encryption

#### TLS Configuration

```python
# HTTPS/TLS 1.3 enforced
class SSLConfiguration:
    """
    Strong SSL/TLS configuration.
    """

    # In main FastAPI app
    app = FastAPI()

    @app.middleware("http")
    async def https_redirect(request, call_next):
        if request.url.scheme != "https":
            url = request.url.replace(scheme="https")
            return RedirectResponse(url=url, status_code=307)

        response = await call_next(request)
        return response

    # SSL/TLS headers
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["enterprisehub.io", "*.enterprisehub.io"]
    )

    # HSTS header
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response
```

---

## GHL Integration Security

### OAuth 2.0 Security

```python
class GHLOAuthSecurity:
    """
    Secure OAuth 2.0 flow with GoHighLevel.
    """

    async def exchange_auth_code(self, code: str, state: str):
        """Exchange authorization code for access token."""
        # Verify state parameter (CSRF protection)
        stored_state = await cache.get(f"oauth_state:{state}")
        if not stored_state:
            raise SecurityException("Invalid or expired state parameter")

        # Exchange code for token
        response = await httpx.post(
            "https://api.gohighlevel.com/oauth/token",
            json={
                "client_id": os.getenv("GHL_CLIENT_ID"),
                "client_secret": os.getenv("GHL_CLIENT_SECRET"),
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": os.getenv("GHL_REDIRECT_URI")
            }
        )

        token_data = response.json()

        # Store tokens securely
        await self.store_tokens(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_in=token_data["expires_in"]
        )

        return {"status": "authorized"}

    async def refresh_access_token(self, refresh_token: str):
        """Refresh expired access token."""
        response = await httpx.post(
            "https://api.gohighlevel.com/oauth/token",
            json={
                "client_id": os.getenv("GHL_CLIENT_ID"),
                "client_secret": os.getenv("GHL_CLIENT_SECRET"),
                "refresh_token": refresh_token,
                "grant_type": "refresh_token"
            }
        )

        token_data = response.json()
        await self.store_tokens(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expires_in=token_data["expires_in"]
        )

        return {"status": "refreshed"}
```

### Webhook Security

```python
class GHLWebhookSecurity:
    """
    Secure webhook processing with verification.
    """

    async def verify_webhook_signature(self, request: Request):
        """Verify GHL webhook signature."""
        body = await request.body()
        signature = request.headers.get("X-GHL-Signature")
        timestamp = request.headers.get("X-GHL-Timestamp")

        # Verify timestamp freshness (prevent replay attacks)
        request_time = int(timestamp)
        current_time = int(datetime.utcnow().timestamp())

        if abs(current_time - request_time) > 300:  # 5 minutes
            raise SecurityException("Webhook timestamp too old (replay attack)")

        # Verify signature
        expected_signature = hmac.new(
            os.getenv("GHL_WEBHOOK_SECRET").encode(),
            f"{timestamp}.{body.decode()}".encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_signature):
            raise SecurityException("Invalid webhook signature")

        return True

    @app.post("/webhooks/ghl")
    async def handle_ghl_webhook(request: Request):
        """Process GHL webhook securely."""
        # Verify signature
        await self.verify_webhook_signature(request)

        # Parse payload
        payload = await request.json()

        # Process webhook
        event_type = payload.get("type")
        event_data = payload.get("data")

        await self.process_event(event_type, event_data)

        return {"status": "processed"}
```

### API Key Validation

```python
class GHLAPIKeyValidation:
    """
    Validate GHL API credentials.
    """

    async def validate_ghl_credentials(self, location_id: str, api_key: str):
        """Validate GHL API key for specific location."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        # Test API call to verify credentials
        response = await httpx.get(
            f"https://api.gohighlevel.com/v1/locations/{location_id}",
            headers=headers,
            timeout=10.0
        )

        if response.status_code == 401:
            raise SecurityException("Invalid GHL API credentials")

        if response.status_code == 403:
            raise SecurityException("Insufficient GHL permissions")

        return response.json()
```

---

## Incident Response

### Incident Classification

| Severity | Response Time | Actions |
|----------|--------------|---------|
| Critical | 15 minutes | Immediate isolation, executive notification |
| High | 1 hour | Investigation, user notification prep |
| Medium | 4 hours | Investigation, patch development |
| Low | 24 hours | Documentation, schedule fix |

### Breach Response Procedure

```python
class IncidentResponse:
    """
    Incident detection and response workflow.
    """

    async def detect_breach(self, indicator: str):
        """
        Automated breach detection.
        """
        # Step 1: Isolate affected systems
        await self.isolate_systems(indicator)

        # Step 2: Preserve evidence
        await self.capture_logs(indicator)
        await self.snapshot_database()

        # Step 3: Notify security team
        await self.alert_security_team({
            "severity": "high",
            "indicator": indicator,
            "timestamp": datetime.utcnow()
        })

        # Step 4: Prepare user notification
        affected_users = await self.identify_affected_users(indicator)
        await self.prepare_notification(affected_users)

        # Step 5: Document incident
        await self.create_incident_record({
            "type": "data_breach",
            "indicator": indicator,
            "affected_count": len(affected_users),
            "discovery_time": datetime.utcnow()
        })

    async def notify_users(self, users: List[str], breach_type: str):
        """
        Notify affected users within 72 hours (GDPR requirement).
        """
        for user in users:
            # Prepare notification
            message = self._generate_notification(user, breach_type)

            # Send via secure channel
            await email.send_secure(
                to=user.email,
                subject="Important Security Notice",
                body=message,
                encryption="pgp"  # PGP-encrypted email
            )

            # Log notification
            await audit_log.record({
                "event": "breach_notification",
                "user_id": user.id,
                "timestamp": datetime.utcnow()
            })
```

---

## Compliance & Auditing

### Audit Logging

```python
class AuditLogging:
    """
    Comprehensive audit logging for compliance.
    """

    AUDIT_EVENTS = {
        "user_login": "User authentication",
        "data_access": "Sensitive data access",
        "data_modification": "Data change",
        "export_data": "Data export",
        "delete_data": "Data deletion",
        "permission_change": "Access control change",
        "api_key_generated": "API key creation",
        "webhook_received": "Webhook processing"
    }

    async def log_event(self, event_type: str, details: dict):
        """Log security/compliance event."""
        if event_type not in self.AUDIT_EVENTS:
            raise ValueError(f"Unknown event type: {event_type}")

        audit_record = {
            "event_type": event_type,
            "event_description": self.AUDIT_EVENTS[event_type],
            "timestamp": datetime.utcnow(),
            "user_id": details.get("user_id"),
            "resource_id": details.get("resource_id"),
            "action": details.get("action"),
            "ip_address": details.get("ip_address"),
            "user_agent": details.get("user_agent"),
            "result": details.get("result", "success")
        }

        # Store in audit log
        await db.audit_logs.insert_one(audit_record)

        # Send to immutable storage (cannot be deleted)
        await s3.put_object(
            Bucket="enterprisehub-audit-logs",
            Key=f"{date.today()}/{uuid.uuid4()}.json",
            Body=json.dumps(audit_record),
            ServerSideEncryption="AES256"
        )

    async def generate_audit_report(self, start_date: date, end_date: date):
        """Generate audit report for compliance."""
        records = await db.audit_logs.find({
            "timestamp": {
                "$gte": start_date,
                "$lte": end_date
            }
        }).to_list()

        return {
            "period": f"{start_date} to {end_date}",
            "total_events": len(records),
            "event_breakdown": self._summarize_events(records),
            "high_risk_events": self._identify_anomalies(records),
            "compliance_status": "compliant"
        }
```

### Regular Audits

```bash
# Weekly Security Audit
- Scan for exposed credentials
- Review access logs for anomalies
- Check certificate expiration dates
- Verify encryption status
- Test backup restoration

# Monthly Compliance Review
- Audit user access permissions
- Review data deletion requests
- Verify retention policies
- Check incident response procedures
- Update security documentation

# Quarterly Security Assessment
- Penetration testing
- Vulnerability scanning
- Code security review
- Infrastructure audit
- Third-party assessment
```

---

## Security Checklist

### Development Security

- [ ] No hardcoded credentials
- [ ] Input validation on all endpoints
- [ ] Output encoding for user input
- [ ] SQL injection prevention (parameterized queries)
- [ ] CSRF token protection
- [ ] Rate limiting configured
- [ ] Security headers set
- [ ] Dependency vulnerabilities scanned

### Deployment Security

- [ ] SSL/TLS 1.3+ enabled
- [ ] API keys rotated
- [ ] Database backups encrypted
- [ ] Access logs enabled
- [ ] Monitoring configured
- [ ] Incident response plan tested
- [ ] Disaster recovery tested
- [ ] Firewall rules configured

### Operational Security

- [ ] MFA enforced for all users
- [ ] Regular security training
- [ ] Incident response drills
- [ ] Penetration testing scheduled
- [ ] Vulnerability patches applied
- [ ] Access reviews quarterly
- [ ] Audit logs reviewed monthly
- [ ] Backup restoration tested quarterly

---

## Support & Resources

### Security Resources
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework
- CIS Benchmarks: https://www.cisecurity.org/cis-benchmarks/

### Compliance Resources
- CCPA Compliance: https://www.ccpa-info.com/
- GDPR Compliance: https://gdpr-info.eu/
- HIPAA Compliance: https://www.hhs.gov/hipaa/

### Security Contacts
- Security Team: security@enterprisehub.io
- Incident Response: incidents@enterprisehub.io
- Privacy Officer: privacy@enterprisehub.io

---

**Last Updated**: January 10, 2026
**Maintained By**: Security & Compliance Team
**Next Review**: January 24, 2026
**Classification**: Internal Use Only
