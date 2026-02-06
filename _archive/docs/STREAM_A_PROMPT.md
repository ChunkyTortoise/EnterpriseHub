# Stream A: Buyer Bot Error Handling & Resilience
**Chat Purpose**: Complete 4 error handling TODO items in Buyer Bot  
**Duration**: 2-3 hours  
**Priority**: HIGH  
**Status**: Ready to begin

---

## Your Mission

Complete all 4 error handling TODOs in the Buyer Bot to make it production-grade. These are edge case handlers that improve resilience without affecting the happy path.

**Files You'll Work With**:
- `ghl_real_estate_ai/agents/jorge_buyer_bot.py` (MAIN - contains 4 TODOs)
- `tests/agents/test_jorge_buyer_bot.py` (Add tests)
- `ghl_real_estate_ai/services/buyer_error_handler.py` (Optional - may create)

---

## TODO Items to Complete

### TODO 1: Line 196 - Retry Mechanism with Exponential Backoff

**Current State**: 
```python
# External service calls have no retry logic
# If network fails, query fails immediately
```

**What to Implement**:
```python
# Exponential backoff retry wrapper
# - Max 3 retries
# - Backoff: 500ms → 1s → 2s
# - Jitter: ±10% to prevent thundering herd
# - Retry on: Network errors, timeouts, 5xx responses
# - Don't retry: Validation errors (4xx except 429)
```

**Target**:
- Wrap external service calls (financial assessment, property matching)
- Configuration-driven (max_retries, initial_backoff, exponential_base)
- Add 2+ test cases covering success on retry, failure after max retries
- Performance: <50ms retry logic overhead

---

### TODO 2: Line 211 - Escalate to Human Review

**Current State**:
```python
async def escalate_to_human_review(buyer_id: str, reason: str, context: Dict) -> Dict:
    # Stub - just passes silently
    pass
```

**What to Implement**:
```python
# Real escalation workflow
# 1. Create escalation ticket in GHL CRM
# 2. Send notification to human agent (email + SMS)
# 3. Flag conversation: needs_human_review = True
# 4. Log escalation with timestamp + reason
# 5. Return escalation_id for tracking
# 6. Graceful degradation: queue if human unavailable
```

**Target**:
- Integration with GHL API (enhanced_ghl_client)
- EventPublisher notification to human agents
- Database logging of escalation
- Graceful fallback if notification service fails
- Test case: verify CRM ticket creation + notification sent
- Test case: verify fallback when service unavailable

---

### TODO 3: Line 405 - Fallback Financial Assessment

**Current State**:
```python
# If external financial service fails, assessment fails
# Conversation breaks
```

**What to Implement**:
```python
# Multi-tier fallback strategy
# Primary: Call external_financial_service.assess(buyer_id)
# Fallback 1: Use conversation history heuristics
#   - "pre-approved" mentioned? → high confidence
#   - Price range mentioned? → use that
# Fallback 2: Default conservative assessment
#   - pre_approved=False
#   - requires_review=True
#   - confidence=0.6 (low confidence flag)
# Fallback 3: Queue for manual review + continue conversation
```

**Target**:
- Three-tier fallback with graceful degradation
- Never fails - always returns reasonable assessment
- Confidence score reflects data quality
- Logging: which fallback was used
- Test case: success path, failure → fallback 1, 2, 3
- Test case: verify conversation continues even if service down

---

### TODO 4: Line 418 - Escalate Compliance Violation

**Current State**:
```python
async def escalate_compliance_violation(buyer_id: str, violation_type: str, evidence: Dict) -> Dict:
    # Stub - just passes
    pass
```

**What to Implement**:
```python
# Compliance violation tracking & escalation
# 1. Log violation to audit database with full evidence
# 2. Determine severity: critical, high, medium, low
# 3. Notify compliance officer if critical/high
# 4. Create audit trail (timestamp, reason, evidence)
# 5. Flag contact in CRM with violation type
# 6. Pause bot interactions until human review
# 7. Return compliance_ticket_id
```

**Violation Types to Support**:
- fair_housing: Discrimination risk
- privacy: PII handling issue
- financial_regulation: Loan fraud risk
- licensing: Agent credential issue

**Target**:
- Full audit logging with evidence preservation
- Severity assessment logic
- CRM flagging system
- Notification to compliance officer
- Test case: log + escalate fair_housing violation
- Test case: verify CRM flag applied
- Test case: verify conversation pause on escalation

---

## Implementation Strategy

### Phase 1: Read & Understand (30 minutes)
1. Read `jorge_buyer_bot.py` lines 190-430 to understand context
2. Review existing error handling patterns in the file
3. Check `enhanced_ghl_client.py` to understand CRM integration API
4. Look at EventPublisher usage in other bots

### Phase 2: Implement TODOs (90 minutes)
1. **Start with TODO 1** (retry logic) - foundational
   - Create `retry_with_backoff` helper function
   - Apply to financial assessment call
   - Apply to property matching call
   - Write unit tests

2. **Implement TODO 2** (human escalation)
   - Create GHL ticket via enhanced_ghl_client
   - Send notification via EventPublisher
   - Log to database
   - Write integration test

3. **Implement TODO 3** (financial fallback)
   - Create three-tier fallback logic
   - Add heuristic parser for conversation history
   - Return conservative default
   - Write test for each fallback path

4. **Implement TODO 4** (compliance escalation)
   - Create audit log entry
   - Implement severity calculator
   - Apply CRM flag
   - Write test for each violation type

### Phase 3: Testing (30 minutes)
1. Run existing tests: `pytest tests/agents/test_jorge_buyer_bot.py` (ensure no regression)
2. Write 6+ new test cases for error handling paths
3. Verify all tests pass: `pytest tests/agents/test_jorge_buyer_bot.py -v`
4. Check test coverage: `pytest --cov=ghl_real_estate_ai.agents.jorge_buyer_bot`

### Phase 4: Validation (15 minutes)
1. Code review checklist:
   - [ ] No regression in existing tests
   - [ ] New tests all passing
   - [ ] Error messages are user-friendly
   - [ ] Performance: <50ms retry overhead
   - [ ] Logging is comprehensive
2. Performance test: <200ms response times with retry enabled
3. Security review: No PII leaked in error messages

---

## Key Constraints

1. **Don't break existing functionality**
   - All 20 existing tests must still pass
   - Happy path unchanged

2. **Error messages are user-friendly**
   - Never expose internal service names
   - Use buyer-friendly language
   - Suggest next steps

3. **Performance targets**
   - Retry logic: <50ms overhead
   - Total response: <500ms (maintained)
   - No blocking I/O in sync code

4. **Logging & observability**
   - Every error logged with context
   - Escalations logged to audit trail
   - No sensitive data in logs

5. **Testing**
   - All tests must pass
   - New tests must cover error paths
   - Mock external services appropriately

---

## Test Cases You Should Write

```python
# Stream A Tests (Add to test_jorge_buyer_bot.py)

def test_retry_mechanism_succeeds_on_second_attempt():
    # Mock: First call fails with network error, second succeeds
    # Assert: Response is correct

def test_retry_mechanism_fails_after_max_retries():
    # Mock: All calls fail
    # Assert: Raises appropriate error after 3 attempts

def test_escalate_to_human_review_creates_ticket():
    # Mock: GHL API
    # Assert: Ticket created with correct reason + context

def test_escalate_to_human_review_sends_notification():
    # Mock: EventPublisher
    # Assert: Human agent notified immediately

def test_fallback_financial_assessment_primary_path():
    # Mock: External service succeeds
    # Assert: Uses primary assessment

def test_fallback_financial_assessment_tier_1():
    # Mock: External service fails, conversation has "pre-approved"
    # Assert: Uses heuristic, returns high confidence

def test_fallback_financial_assessment_tier_2():
    # Mock: All services fail, no conversation data
    # Assert: Returns conservative default (requires_review=True)

def test_escalate_compliance_violation_fair_housing():
    # Mock: CRM + audit log
    # Assert: Violation logged, CRM flagged, notification sent

def test_escalate_compliance_violation_prevents_bot_response():
    # Mock: Compliance violation detected
    # Assert: Conversation paused, human review required
```

---

## Success Criteria Checklist

- [ ] TODO 1 (Retry): Implemented with tests passing
- [ ] TODO 2 (Human Escalation): GHL integration verified
- [ ] TODO 3 (Financial Fallback): Three-tier fallback working
- [ ] TODO 4 (Compliance): Audit logging + CRM flagging working
- [ ] All 20 existing tests still passing (no regression)
- [ ] 6+ new tests passing
- [ ] Code review approved
- [ ] Performance validated: <500ms total response
- [ ] No critical issues found in code review

---

## Files to Reference

### Primary Implementation File
- `ghl_real_estate_ai/agents/jorge_buyer_bot.py`
  - Lines 196, 211, 405, 418 (the 4 TODOs)
  - Look at lines 100-200 for context
  - Look at method signatures for pattern

### Test File
- `tests/agents/test_jorge_buyer_bot.py`
  - Review existing tests for patterns
  - Add new test cases here

### Supporting Services
- `ghl_real_estate_ai/services/enhanced_ghl_client.py` (CRM integration)
- `ghl_real_estate_ai/services/event_publisher.py` (Notifications)
- `ghl_real_estate_ai/models/` (Database models)

### Reference Implementations
- `ghl_real_estate_ai/agents/jorge_lead_bot.py` (Error handling patterns)
- `ghl_real_estate_ai/agents/jorge_seller_bot.py` (State management patterns)

---

## Command Reference

```bash
# Read the file to understand context
grep -n "TODO" ghl_real_estate_ai/agents/jorge_buyer_bot.py

# Run existing tests (baseline)
pytest tests/agents/test_jorge_buyer_bot.py -v

# Run with coverage
pytest tests/agents/test_jorge_buyer_bot.py --cov=ghl_real_estate_ai.agents.jorge_buyer_bot

# Run full test suite to ensure no regression
pytest tests/agents/test_jorge_*.py -v

# Type check
mypy ghl_real_estate_ai/agents/jorge_buyer_bot.py

# Lint
flake8 ghl_real_estate_ai/agents/jorge_buyer_bot.py
```

---

## Questions to Answer While Implementing

1. What should happen to the buyer's conversation if escalated to human?
2. Should retries happen automatically or with user notification?
3. How long should compliance violations pause bot interaction?
4. What's the preferred notification method for human escalations?

---

**Ready to start? Begin with reading the buyer bot file and existing error patterns!**

**Estimated completion**: 2-3 hours  
**Due by**: End of today
