# Layer 2: Business Logic Validation

## Complete Implementation Reference

This layer validates business rules, workflow constraints, and domain-specific logic.

### Registration Business Logic

```python
"""
Business logic validation for user registration workflows.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re


class BusinessLogicValidator:
    """Validates business rules and constraints."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.max_registration_attempts = self.config.get('max_registration_attempts', 5)
        self.registration_window_minutes = self.config.get('registration_window_minutes', 60)

    def validate_registration_workflow(
        self,
        email: str,
        user_data: Dict,
        existing_attempts: List[Dict]
    ) -> ValidationResult:
        """Validate complete registration workflow."""
        errors = []
        warnings = []

        # Layer 1: Rate limiting validation
        recent_attempts = self._get_recent_attempts(existing_attempts)
        if len(recent_attempts) >= self.max_registration_attempts:
            errors.append(
                f"Too many registration attempts. "
                f"Maximum {self.max_registration_attempts} per {self.registration_window_minutes} minutes."
            )

        # Layer 2: Email domain validation
        domain_result = self._validate_email_domain(email)
        if not domain_result.is_valid:
            errors.extend(domain_result.errors)
            warnings.extend(domain_result.warnings)

        # Layer 3: User data completeness
        required_fields = ['first_name', 'last_name', 'phone', 'role']
        missing_fields = [field for field in required_fields if field not in user_data]
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")

        # Layer 4: Role-based validation
        role_result = self._validate_user_role(user_data.get('role'))
        if not role_result.is_valid:
            errors.extend(role_result.errors)

        # Layer 5: Business hours validation (optional)
        if self.config.get('enforce_business_hours', False):
            if not self._is_business_hours():
                warnings.append("Registration outside business hours may delay verification")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            severity=ValidationSeverity.ERROR if errors else ValidationSeverity.INFO
        )

    def _get_recent_attempts(self, attempts: List[Dict]) -> List[Dict]:
        """Filter attempts within the registration window."""
        cutoff_time = datetime.now() - timedelta(minutes=self.registration_window_minutes)
        return [
            attempt for attempt in attempts
            if datetime.fromisoformat(attempt.get('timestamp', '')) > cutoff_time
        ]

    def _validate_email_domain(self, email: str) -> ValidationResult:
        """Validate email domain against business rules."""
        errors = []
        warnings = []

        domain = email.split('@')[1].lower()

        # Blacklisted domains
        blacklisted_domains = self.config.get('blacklisted_domains', [])
        if domain in blacklisted_domains:
            errors.append(f"Email domain '{domain}' is not allowed")

        # Whitelisted domains (if enforced)
        if self.config.get('enforce_domain_whitelist', False):
            whitelisted_domains = self.config.get('whitelisted_domains', [])
            if domain not in whitelisted_domains:
                errors.append(f"Email domain '{domain}' is not in approved list")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _validate_user_role(self, role: Optional[str]) -> ValidationResult:
        """Validate user role against allowed roles."""
        errors = []
        warnings = []

        if not role:
            errors.append("User role is required")
            return ValidationResult(False, errors, warnings)

        allowed_roles = self.config.get('allowed_roles', [
            'agent', 'broker', 'admin', 'viewer'
        ])

        if role not in allowed_roles:
            errors.append(f"Invalid role '{role}'. Allowed: {', '.join(allowed_roles)}")

        # Role-specific validation
        if role == 'admin' and not self.config.get('allow_admin_registration', False):
            errors.append("Admin role cannot be self-assigned")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _is_business_hours(self) -> bool:
        """Check if current time is within business hours."""
        now = datetime.now()
        business_hours = self.config.get('business_hours', {
            'start': 9,  # 9 AM
            'end': 17,   # 5 PM
            'timezone': 'UTC'
        })

        current_hour = now.hour
        return business_hours['start'] <= current_hour < business_hours['end']
```

### Transaction Validation

```python
def validate_transaction(
    self,
    transaction_type: str,
    amount: float,
    user_context: Dict,
    account_balance: float
) -> ValidationResult:
    """Validate financial transaction business logic."""
    errors = []
    warnings = []

    # Layer 1: Transaction type validation
    allowed_transactions = ['deposit', 'withdrawal', 'transfer', 'payment']
    if transaction_type not in allowed_transactions:
        errors.append(f"Invalid transaction type: {transaction_type}")

    # Layer 2: Amount validation
    if amount <= 0:
        errors.append("Transaction amount must be positive")

    max_transaction = self.config.get('max_transaction_amount', 100000)
    if amount > max_transaction:
        errors.append(f"Transaction amount exceeds maximum: ${max_transaction}")

    # Layer 3: Balance validation for withdrawals
    if transaction_type in ['withdrawal', 'transfer', 'payment']:
        if amount > account_balance:
            errors.append("Insufficient funds for transaction")

        min_balance = self.config.get('minimum_balance', 100)
        if account_balance - amount < min_balance:
            warnings.append(f"Transaction will leave balance below minimum: ${min_balance}")

    # Layer 4: Daily limit validation
    daily_limit_result = self._check_daily_transaction_limit(
        user_context.get('user_id'),
        amount
    )
    if not daily_limit_result.is_valid:
        errors.extend(daily_limit_result.errors)

    # Layer 5: Fraud detection
    fraud_score = self._calculate_fraud_score(transaction_type, amount, user_context)
    if fraud_score > 0.8:
        errors.append("Transaction flagged for potential fraud - requires manual review")
    elif fraud_score > 0.5:
        warnings.append("Transaction requires additional verification")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        severity=ValidationSeverity.CRITICAL if errors else ValidationSeverity.INFO
    )

def _check_daily_transaction_limit(
    self,
    user_id: str,
    amount: float
) -> ValidationResult:
    """Check if transaction exceeds daily limits."""
    errors = []

    # This would query actual transaction history
    daily_total = self._get_daily_transaction_total(user_id)
    daily_limit = self.config.get('daily_transaction_limit', 10000)

    if daily_total + amount > daily_limit:
        errors.append(
            f"Transaction would exceed daily limit: "
            f"${daily_total + amount} > ${daily_limit}"
        )

    return ValidationResult(len(errors) == 0, errors, [])

def _calculate_fraud_score(
    self,
    transaction_type: str,
    amount: float,
    user_context: Dict
) -> float:
    """Calculate fraud risk score (0.0 - 1.0)."""
    score = 0.0

    # High amount transactions
    if amount > 5000:
        score += 0.3

    # New account
    account_age_days = user_context.get('account_age_days', 0)
    if account_age_days < 30:
        score += 0.2

    # Unusual transaction pattern
    avg_transaction = user_context.get('avg_transaction_amount', 0)
    if avg_transaction > 0 and amount > avg_transaction * 5:
        score += 0.3

    # Geographic anomaly
    if user_context.get('location_anomaly', False):
        score += 0.2

    return min(score, 1.0)

def _get_daily_transaction_total(self, user_id: str) -> float:
    """Get total transactions for user today."""
    # This would query actual database
    # Placeholder implementation
    return 0.0
```

### Lead Qualification Validation (Real Estate Specific)

```python
def validate_lead_qualification(
    self,
    lead_data: Dict,
    property_data: Dict
) -> ValidationResult:
    """Validate lead qualification business logic for real estate."""
    errors = []
    warnings = []

    # Layer 1: Basic lead data completeness
    required_lead_fields = ['budget', 'location_preference', 'bedrooms', 'timeline']
    missing_fields = [f for f in required_lead_fields if f not in lead_data]
    if missing_fields:
        errors.append(f"Lead missing required fields: {', '.join(missing_fields)}")

    # Layer 2: Budget alignment
    if 'budget' in lead_data and 'price' in property_data:
        budget_max = lead_data['budget'].get('max', 0)
        property_price = property_data['price']

        if property_price > budget_max * 1.2:  # 20% tolerance
            warnings.append(
                f"Property price ${property_price} exceeds lead budget ${budget_max}"
            )

    # Layer 3: Timeline validation
    timeline = lead_data.get('timeline', '')
    valid_timelines = ['immediate', '1-3_months', '3-6_months', '6+_months']
    if timeline not in valid_timelines:
        errors.append(f"Invalid timeline: {timeline}")

    # Layer 4: Pre-qualification check
    if lead_data.get('pre_qualified', False):
        if 'pre_qualification_amount' not in lead_data:
            warnings.append("Pre-qualified lead missing qualification amount")

    # Layer 5: Lead score threshold
    lead_score = lead_data.get('score', 0)
    min_score = self.config.get('min_lead_score', 50)
    if lead_score < min_score:
        warnings.append(
            f"Lead score {lead_score} below minimum threshold {min_score}"
        )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )
```

## Best Practices

1. **Validate workflows end-to-end**, not just individual inputs
2. **Implement rate limiting** to prevent abuse
3. **Use configurable business rules** for flexibility
4. **Log business rule violations** for analytics
5. **Provide clear error messages** for business logic failures
6. **Consider time-based constraints** (business hours, deadlines)
7. **Implement fraud detection** for sensitive operations
