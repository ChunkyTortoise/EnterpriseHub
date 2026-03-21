# EnterpriseHub Security Issues Context (for Research Tools)

## Critical Security Vulnerabilities

### 1. SQL Injection — transaction_service.py (P0)
Lines 445-503: Direct f-string interpolation of user-controlled values into SQL:

```python
# VULNERABLE - transaction_id comes from API request parameter
result = await session.execute(f"""
    SELECT * FROM milestone_timeline_view
    WHERE transaction_id = (
        SELECT id FROM real_estate_transactions
        WHERE transaction_id = '{transaction_id}'
    )
    ORDER BY order_sequence
""")

# Also vulnerable - milestone[1] from DB result used in nested f-string query
celebration_check = await session.execute(f"""
    SELECT COUNT(*) FROM transaction_celebrations
    WHERE transaction_id = (
        SELECT id FROM real_estate_transactions
        WHERE transaction_id = '{transaction_id}'
    )
    AND milestone_type = '{milestone[1]}'
    AND triggered_at >= NOW() - INTERVAL '1 hour'
""")
```

**Fix needed**: Replace with SQLAlchemy parameterized queries using `text()` and bindparams.

### 2. SQL Injection — database_repository.py (P0)
Lines 197, 303, 452: Table name interpolated via f-string:
```python
sql = f"SELECT * FROM {self.table_name} WHERE id = $1 LIMIT 1"
```
While `table_name` is set in `__init__`, if it can be influenced by configuration or passed values, this is exploitable. Should use allowlist validation.

### 3. Incomplete Webhook Authentication (P0)
`api/routes/webhook.py` (2,715 lines):
- `@verify_webhook("ghl")` applied to only 3 of ~20+ endpoint functions (lines 498, 596, 2384)
- Many webhook handlers accept unauthenticated POST requests
- No HMAC-SHA256 signature verification on most endpoints
- No replay protection (missing timestamp validation)

### 4. Unauthenticated Billing Routes (P0)
`api/routes/billing.py` (1,525 lines):
- NO `Depends(get_current_user)` or JWT dependency on checkout/subscription routes
- Entirely excluded from ruff linting (ruff config: `["ALL"]` ignore for this file)
- Stripe webhook endpoint has no signature verification

### 5. Disabled Type Safety (P1)
`pyproject.toml` mypy config:
```toml
[[tool.mypy.overrides]]
module = ["ghl_real_estate_ai.*", "utils.*", "advanced_rag_system.*", ...]
ignore_errors = true  # Suppresses ALL type errors on main codebase
```
This means:
- Untyped function parameters pass mypy
- Wrong return types never flagged
- Potential `None` dereferences not caught

### 6. Linter Suppression (P1)
Ruff suppresses critical rules:
- `F401` unused imports (security: accidentally imported modules may execute)
- `F403` star imports (namespace pollution, undefined names)
- `F821` undefined names (runtime errors not caught statically)
- `E722` bare except (swallows all exceptions silently)

## Security Architecture Context
The app claims compliance with:
- DRE (California real estate regulations)
- Fair Housing Act
- CCPA
- CAN-SPAM

Given the SQL injection vulnerabilities and auth gaps, these compliance claims are aspirational, not verified.
