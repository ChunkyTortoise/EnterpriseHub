# GHL Real Estate Platform - Defense-in-Depth Implementation

## Project-Specific Security Patterns

This guide shows how to apply defense-in-depth to the EnterpriseHub GHL Real Estate AI Platform.

### Lead Registration Validation

```python
"""
Complete defense-in-depth for lead registration in GHL platform.
"""

from typing import Dict, Any
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.core.llm_client import LLMClient


class LeadRegistrationSecurity:
    """Multi-layer security for lead registration."""

    def __init__(self):
        self.input_validator = InputValidator(strict_mode=True)
        self.business_validator = BusinessLogicValidator(config={
            'max_registration_attempts': 5,
            'registration_window_minutes': 60,
            'blacklisted_domains': ['tempmail.com', 'guerrillamail.com']
        })
        self.cache = CacheService()
        self.security_layer = ApplicationSecurityLayer()

    async def validate_and_register_lead(
        self,
        lead_data: Dict[str, Any],
        ghl_location_id: str,
        ip_address: str
    ) -> ValidationResult:
        """
        Complete validation pipeline for lead registration.

        Layers:
        1. Input validation (email, phone, data format)
        2. Business logic (rate limiting, domain checks)
        3. Database security (safe upsert)
        4. API security (GHL webhook signature)
        5. Application security (logging, monitoring)
        """
        errors = []
        warnings = []

        # LAYER 1: Input Validation
        email_result = self.input_validator.validate_email(lead_data.get('email', ''))
        if not email_result.is_valid:
            errors.extend(email_result.errors)
            self.security_layer.log_security_event(SecurityEvent(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                ValidationSeverity.WARNING,
                ip_address=ip_address,
                details={'reason': 'invalid_email', 'errors': email_result.errors}
            ))
            return ValidationResult(False, errors, warnings)

        phone_result = self._validate_phone(lead_data.get('phone', ''))
        if not phone_result.is_valid:
            errors.extend(phone_result.errors)

        # Sanitize text inputs
        for field in ['first_name', 'last_name', 'notes']:
            if field in lead_data and isinstance(lead_data[field], str):
                sanitized = self.input_validator.sanitize_html_input(lead_data[field])
                if sanitized.is_valid:
                    lead_data[field] = sanitized.sanitized_data

        # LAYER 2: Business Logic Validation
        existing_attempts = await self._get_registration_attempts(
            email_result.sanitized_data,
            ip_address
        )

        business_result = self.business_validator.validate_registration_workflow(
            email_result.sanitized_data,
            lead_data,
            existing_attempts
        )

        if not business_result.is_valid:
            errors.extend(business_result.errors)
            warnings.extend(business_result.warnings)

            # Log rate limit violation
            if 'Too many registration attempts' in str(business_result.errors):
                self.security_layer.log_security_event(SecurityEvent(
                    SecurityEventType.RATE_LIMIT_EXCEEDED,
                    ValidationSeverity.WARNING,
                    ip_address=ip_address,
                    details={'email': email_result.sanitized_data}
                ))

            return ValidationResult(False, errors, warnings)

        # LAYER 3: Database Security
        try:
            lead_id = await self._safe_insert_lead(lead_data, ghl_location_id)
        except Exception as e:
            errors.append(f"Database error: {str(e)}")
            self.security_layer.log_security_event(SecurityEvent(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                ValidationSeverity.ERROR,
                details={'error': str(e), 'operation': 'lead_insert'}
            ))
            return ValidationResult(False, errors, warnings)

        # LAYER 4: API Security (sync to GHL)
        try:
            await self._sync_to_ghl(lead_id, lead_data, ghl_location_id)
        except Exception as e:
            warnings.append(f"GHL sync failed: {str(e)}")

        # LAYER 5: Application Security
        self.security_layer.log_security_event(SecurityEvent(
            SecurityEventType.AUTH_FAILURE,  # Using as generic success event
            ValidationSeverity.INFO,
            details={
                'operation': 'lead_registration',
                'lead_id': lead_id,
                'location_id': ghl_location_id
            }
        ))

        # Cache the successful registration
        await self.cache.set(
            f"lead_registered:{email_result.sanitized_data}",
            {'lead_id': lead_id, 'timestamp': datetime.now().isoformat()},
            ttl=3600
        )

        return ValidationResult(
            is_valid=True,
            errors=errors,
            warnings=warnings,
            sanitized_data={'lead_id': lead_id}
        )

    def _validate_phone(self, phone: str) -> ValidationResult:
        """Validate phone number format."""
        errors = []
        warnings = []

        if not phone:
            errors.append("Phone number is required")
            return ValidationResult(False, errors, warnings)

        # Remove common formatting
        cleaned_phone = re.sub(r'[^\d+]', '', phone)

        # Validate length
        if len(cleaned_phone) < 10:
            errors.append("Phone number too short")

        if len(cleaned_phone) > 15:
            errors.append("Phone number too long")

        # Check for valid format
        phone_pattern = re.compile(r'^\+?1?\d{10,14}$')
        if not phone_pattern.match(cleaned_phone):
            errors.append("Invalid phone number format")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_data=cleaned_phone
        )

    async def _get_registration_attempts(
        self,
        email: str,
        ip_address: str
    ) -> List[Dict]:
        """Get recent registration attempts for rate limiting."""
        cache_key = f"registration_attempts:{email}:{ip_address}"
        attempts = await self.cache.get(cache_key) or []

        # Filter to last hour
        cutoff = datetime.now() - timedelta(hours=1)
        recent_attempts = [
            a for a in attempts
            if datetime.fromisoformat(a['timestamp']) > cutoff
        ]

        return recent_attempts

    async def _safe_insert_lead(
        self,
        lead_data: Dict[str, Any],
        ghl_location_id: str
    ) -> str:
        """Safely insert lead with SQL injection prevention."""
        # Use DatabaseSecurityLayer for safe insertion
        # This would integrate with actual database
        # Placeholder implementation
        return f"lead_{hashlib.sha256(lead_data['email'].encode()).hexdigest()[:16]}"

    async def _sync_to_ghl(
        self,
        lead_id: str,
        lead_data: Dict[str, Any],
        ghl_location_id: str
    ):
        """Sync lead to GoHighLevel CRM."""
        # This would use GHL API client
        # Placeholder implementation
        pass
```

### Property Matcher AI Security

```python
class PropertyMatcherSecurity:
    """Security for AI-powered property matching."""

    def __init__(self):
        self.input_validator = InputValidator()
        self.llm_client = LLMClient()
        self.cache = CacheService()

    async def validate_and_match_properties(
        self,
        lead_preferences: Dict[str, Any],
        user_id: str
    ) -> ValidationResult:
        """
        Validate property matching request with defense-in-depth.

        Layers:
        1. Input validation (preferences, budget, location)
        2. Business logic (budget reasonableness, location validation)
        3. Rate limiting (prevent AI abuse)
        4. AI prompt injection prevention
        5. Response sanitization
        """
        errors = []
        warnings = []

        # LAYER 1: Input Validation
        if 'budget' in lead_preferences:
            budget_result = self.input_validator.validate_numeric_input(
                lead_preferences['budget'],
                min_value=0,
                max_value=100000000
            )
            if not budget_result.is_valid:
                errors.extend(budget_result.errors)

        # LAYER 2: Business Logic
        if 'bedrooms' in lead_preferences:
            bedrooms = lead_preferences['bedrooms']
            if not isinstance(bedrooms, int) or bedrooms < 0 or bedrooms > 20:
                errors.append("Invalid bedroom count")

        # LAYER 3: Rate Limiting
        cache_key = f"property_match_requests:{user_id}"
        request_count = await self.cache.get(cache_key) or 0

        if request_count >= 100:  # Max 100 requests per hour
            errors.append("Property matching rate limit exceeded")
            return ValidationResult(False, errors, warnings)

        await self.cache.set(cache_key, request_count + 1, ttl=3600)

        # LAYER 4: AI Prompt Injection Prevention
        sanitized_preferences = self._sanitize_ai_input(lead_preferences)

        # LAYER 5: Execute AI matching with sanitized inputs
        try:
            matches = await self.llm_client.generate(
                f"Find properties matching: {json.dumps(sanitized_preferences)}"
            )
            sanitized_response = self._sanitize_ai_output(matches)
        except Exception as e:
            errors.append(f"AI matching failed: {str(e)}")
            return ValidationResult(False, errors, warnings)

        return ValidationResult(
            is_valid=True,
            errors=errors,
            warnings=warnings,
            sanitized_data=sanitized_response
        )

    def _sanitize_ai_input(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize inputs to prevent prompt injection."""
        sanitized = {}

        for key, value in preferences.items():
            if isinstance(value, str):
                # Remove potential prompt injection patterns
                value = re.sub(r'(ignore|forget|system|admin|prompt)', '', value, flags=re.IGNORECASE)
                value = html.escape(value)

            sanitized[key] = value

        return sanitized

    def _sanitize_ai_output(self, response: str) -> str:
        """Sanitize AI response before returning to user."""
        # Remove any potential script tags
        response = re.sub(r'<script.*?</script>', '', response, flags=re.DOTALL | re.IGNORECASE)

        # Escape HTML
        response = html.escape(response)

        return response
```

## Integration with Existing Services

### Cache Service Integration

```python
# ghl_real_estate_ai/services/cache_service.py
class CacheService:
    """Enhanced with security features."""

    async def set_with_validation(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ) -> ValidationResult:
        """Set cache value with validation."""
        errors = []
        warnings = []

        # Validate key format
        if not re.match(r'^[a-zA-Z0-9:_-]+$', key):
            errors.append("Invalid cache key format")

        # Validate TTL
        if ttl > 86400:  # Max 24 hours
            warnings.append("TTL exceeds recommended maximum")

        # Validate value size
        value_size = len(json.dumps(value))
        if value_size > 1024 * 1024:  # 1MB
            errors.append("Cache value too large")

        if errors:
            return ValidationResult(False, errors, warnings)

        await self.set(key, value, ttl)
        return ValidationResult(True, errors, warnings)
```

## Best Practices for GHL Platform

1. **Always validate GHL webhook signatures** before processing
2. **Rate limit AI operations** to prevent cost overruns
3. **Sanitize all AI inputs** to prevent prompt injection
4. **Cache lead data** with appropriate TTL
5. **Log all security events** to analytics service
6. **Validate location IDs** before GHL API calls
7. **Use encrypted connections** for all GHL communication
8. **Implement retry logic** with exponential backoff for GHL API
