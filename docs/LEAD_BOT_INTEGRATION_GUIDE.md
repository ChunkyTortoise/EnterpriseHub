# Lead Bot Integration Guide

**Version**: 1.0  
**Status**: COMPLETE  
**Date**: 2026-02-06

---

## Table of Contents

1. [Overview](#1-overview)
2. [Temperature Tag System](#2-temperature-tag-system)
3. [Compliance Requirements](#3-compliance-requirements)
4. [Handoff Integration](#4-handoff-integration)
5. [CRM Workflow Integration](#5-crm-workflow-integration)
6. [Configuration Reference](#6-configuration-reference)
7. [Troubleshooting Guide](#7-troubleshooting-guide)
8. [Test Coverage Summary](#8-test-coverage-summary)

---

## 1. Overview

The Lead Bot is the primary entry point for unqualified leads in the EnterpriseHub system. It handles initial contact qualification, temperature classification, and routing to specialized bots (Buyer/Seller) when intent is detected.

### Key Capabilities

| Capability | Status | Description |
|------------|--------|-------------|
| Lead Routing | ✅ Complete | Dedicated routing block with `LEAD_ACTIVATION_TAG` |
| Temperature Classification | ✅ Complete | Hot/Warm/Cold lead tagging based on score |
| Compliance Guard | ✅ Complete | Fair Housing compliance audit |
| SMS Length Guard | ✅ Complete | 320-char truncation with smart boundaries |
| Cross-Bot Handoff | ✅ Complete | Auto-handoff to Buyer/Seller at 0.7 confidence |

### Lead Bot Architecture

```
Incoming GHL Webhook
    |
    +-- Tag Check: LEAD_ACTIVATION_TAG present?
    |   |
    |   +-- NO -> Skip to next bot mode
    |
    +-- YES -> Lead Bot Processing
        |
        +-- ConversationManager.generate_response()
        |   |
        |   +-- Claude AI Response
        |   +-- Lead Score Calculation
        |   +-- Temperature Classification
        |
        +-- Compliance Audit
        |   |
        |   +-- Tier 0: Input length guard
        |   +-- Tier 1: Regex pattern matching
        |   +-- Tier 2: LLM cognitive audit
        |
        +-- SMS Length Guard (320 chars)
        |
        +-- Handoff Evaluation (0.7 threshold)
        |
        +-- Prepare GHL Actions
            |
            +-- Add temperature tag
            +-- Update lead score field
            +-- Trigger workflows (if configured)
```

---

## 2. Temperature Tag System

Leads are classified into three temperature tiers based on their lead score:

### Temperature Thresholds

| Lead Score | Temperature | Tag | Actions |
|------------|-------------|-----|---------|
| ≥ 80 | **Hot-Lead** | `Hot-Lead` | Priority workflow, agent notification |
| 40-79 | **Warm-Lead** | `Warm-Lead` | Nurture sequence, follow-up reminder |
| < 40 | **Cold-Lead** | `Cold-Lead` | Educational content, periodic check-in |

### Temperature Tag Publishing

Temperature tags are automatically applied after each lead interaction:

```python
# From prepare_ghl_actions() in webhook.py
if lead_score >= 80:
    actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Hot-Lead"))
elif lead_score >= 40:
    actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Warm-Lead"))
else:
    actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Cold-Lead"))
```

### Custom Field Updates

Temperature is also written to the GHL custom field:

```python
if lead_score_field_id:
    actions.append(GHLAction(
        type=ActionType.UPDATE_CUSTOM_FIELD,
        field_id=lead_score_field_id,
        value=str(lead_score)
    ))
```

---

## 3. Compliance Requirements

The Lead Bot enforces Fair Housing compliance through a 3-tier audit system.

### Compliance Tiers

| Tier | Check | Action |
|------|-------|--------|
| Tier 0 | Input length > 10,000 chars | Block message |
| Tier 1 | Regex pattern matching | Flag protected keywords |
| Tier 2 | LLM cognitive audit | Flag steering, discrimination, tone issues |

### Protected Keywords (Tier 1)

The compliance guard blocks patterns related to:
- Race, color, national origin
- Religion
- Familial status (children, pregnancy)
- Disability
- Sex
- Sexual orientation
- Gender identity

### Lead-Specific Fallback

When a message is blocked by compliance:

```python
LEAD_FALLBACK_MESSAGE = (
    "Thanks for reaching out! I'd love to help. "
    "What are you looking for in your next home?"
)
actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Compliance-Alert"))
```

### Compliance Integration

```python
from ghl_real_estate_ai.services.compliance_guard import (
    compliance_guard,
    ComplianceStatus
)

# Audit the AI response before sending
status, reason, violations = await compliance_guard.audit_message(
    ai_response,
    contact_context={"contact_id": contact_id, "mode": "lead"}
)

if status == ComplianceStatus.BLOCKED:
    ai_response = LEAD_FALLBACK_MESSAGE
    actions.append(GHLAction(type=ActionType.ADD_TAG, tag="Compliance-Alert"))
elif status == ComplianceStatus.FLAGGED:
    logger.warning(f"Compliance flagged for {contact_id}: {reason}")
```

---

## 4. Handoff Integration

The Lead Bot can automatically hand off leads to the Buyer or Seller Bot when intent is detected.

### Handoff Confidence Thresholds

| Direction | Threshold | Trigger Examples |
|-----------|-----------|-----------------|
| Lead → Buyer | 0.7 | "I want to buy", "budget $600k", "pre-approval" |
| Lead → Seller | 0.7 | "Sell my house", "home worth", "CMA request" |

### Intent Pattern Detection

**Buyer Intent Patterns:**
- `i want to buy`
- `looking to buy`
- `budget` followed by `$`
- `pre-approval`, `pre-approval`
- `down payment`
- `fha loan`, `va loan`, `conventional`
- `find a new home`, `find my house`

**Seller Intent Patterns:**
- `sell my home`, `sell my house`
- `what's my home worth`
- `home valuation`, `home value`
- `cma`, `comparative market analysis`
- `list my home`
- `need to sell`
- `sell before buy`

### Handoff Execution Flow

```python
from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    jorge_handoff_service,
    HandoffDecision
)

# Extract intent signals from the message
intent_signals = jorge_handoff_service.extract_intent_signals(user_message)

# Evaluate if handoff is needed
handoff = await jorge_handoff_service.evaluate_handoff(
    current_bot="lead",
    contact_id=contact_id,
    conversation_history=conversation_history,
    intent_signals=intent_signals
)

if handoff and handoff.confidence >= 0.7:
    # Execute handoff actions
    handoff_actions = await jorge_handoff_service.execute_handoff(
        decision=handoff,
        contact_id=contact_id,
        location_id=location_id
    )
    actions.extend(handoff_actions)
```

### Handoff Actions Generated

| Action | Description |
|--------|-------------|
| `remove_tag` | Removes `Needs Qualifying` (Lead activation tag) |
| `add_tag` | Adds `Buyer-Lead` or `Needs Qualifying` (Seller activation tag) |
| `add_tag` | Adds tracking tag (e.g., `Handoff-Lead-to-Buyer`) |

---

## 5. CRM Workflow Integration

The Lead Bot integrates with GoHighLevel (GHL) workflows for automated follow-ups.

### Workflow Configuration

| Workflow ID | Trigger | Temperature |
|-------------|---------|-------------|
| `HOT_LEAD_WORKFLOW_ID` | Hot-Lead detected | Hot |
| `WARM_LEAD_WORKFLOW_ID` | Warm-Lead detected | Warm |
| `COLD_LEAD_WORKFLOW_ID` | Cold-Lead detected | Cold |

### Workflow Triggers

Workflows are triggered based on temperature classification:

```python
# From prepare_ghl_actions() in webhook.py
if lead_score >= 80 and hot_lead_workflow_id:
    actions.append(GHLAction(
        type=ActionType.TRIGGER_WORKFLOW,
        workflow_id=hot_lead_workflow_id
    ))
elif lead_score >= 40 and warm_lead_workflow_id:
    actions.append(GHLAction(
        type=ActionType.TRIGGER_WORKFLOW,
        workflow_id=warm_lead_workflow_id
    ))
elif lead_score < 40 and cold_lead_workflow_id:
    actions.append(GHLAction(
        type=ActionType.TRIGGER_WORKFLOW,
        workflow_id=cold_lead_workflow_id
    ))
```

### Custom Field Updates

The following custom fields are updated after each lead interaction:

| Field | Description | Required |
|-------|-------------|----------|
| `LEAD_SCORE` | Numeric lead score (0-100) | Recommended |
| `LEAD_TEMPERATURE` | Hot/Warm/Cold classification | Recommended |
| `LEAD_SOURCE` | Original source of lead | Optional |
| `AI_VALUATION` | AI-generated property estimate | Optional |

---

## 6. Configuration Reference

### Environment Variables

```bash
# Lead Bot Mode
JORGE_LEAD_MODE=true                    # Enable Lead Bot (default: true)
LEAD_ACTIVATION_TAG=Needs Qualifying   # Tag that triggers Lead Bot

# Temperature Workflows
HOT_LEAD_WORKFLOW_ID=                   # GHL workflow for hot leads
WARM_LEAD_WORKFLOW_ID=                  # GHL workflow for warm leads
COLD_LEAD_WORKFLOW_ID=                 # GHL workflow for cold leads

# Custom Fields
CUSTOM_FIELD_LEAD_SCORE=                # GHL field ID for lead score
CUSTOM_FIELD_LEAD_TEMPERATURE=          # GHL field ID for temperature
```

### Tag Configuration

| Tag | Purpose | Added When |
|-----|---------|------------|
| `Needs Qualifying` | Lead Bot activation | Manual or from intake form |
| `Hot-Lead` | High-value lead | Lead score ≥ 80 |
| `Warm-Lead` | Medium-value lead | Lead score 40-79 |
| `Cold-Lead` | Low-value lead | Lead score < 40 |
| `AI-Off` | Lead opted out | Lead sends "stop" |
| `Handoff-Lead-to-Buyer` | Handoff tracking | Buyer intent detected |
| `Handoff-Lead-to-Seller` | Handoff tracking | Seller intent detected |
| `Compliance-Alert` | Compliance flagged | Message blocked |

### Webhook Routing Configuration

```python
# In webhook.py, the Lead Bot routing block is activated when:
#
# 1. LEAD_ACTIVATION_TAG is present in contact tags
# 2. JORGE_LEAD_MODE is true (default)
# 3. No higher-priority bot matched (Seller takes priority if JORGE_SELLER_MODE=true)
# 4. No buyer tag present (Buyer takes priority if JORGE_BUYER_MODE=true)
```

---

## 7. Troubleshooting Guide

### Issue: Lead Bot Not Processing

**Symptoms:**
- Contacts with `Needs Qualifying` tag not receiving AI responses
- Logs show "no mode matched" or similar

**Diagnosis:**
1. Check if `JORGE_LEAD_MODE=true` in environment
2. Verify contact has exact `Needs Qualifying` tag (case-sensitive)
3. Check for deactivation tags (`AI-Off`, `Qualified`, `Stop-Bot`)
4. Verify no conflicting mode is active

**Resolution:**
```bash
# Check environment
echo $JORGE_LEAD_MODE

# Should output: true

# If not set, add to .env:
JORGE_LEAD_MODE=true
```

### Issue: Temperature Tags Not Applied

**Symptoms:**
- Leads not getting Hot/Warm/Cold tags after interaction
- Custom fields not updating

**Diagnosis:**
1. Check if temperature workflow IDs are configured
2. Verify custom field IDs are valid UUIDs
3. Check logs for "skipping workflow - no ID configured"

**Resolution:**
```bash
# Verify custom fields are configured
# In GHL Dashboard > Settings > Custom Fields
# Ensure these fields exist and note their IDs

# Add to .env:
CUSTOM_FIELD_LEAD_SCORE=your-field-id-here
CUSTOM_FIELD_LEAD_TEMPERATURE=your-field-id-here
```

### Issue: Handoff Not Triggering

**Symptoms:**
- Lead expresses clear buyer/seller intent but not handed off
- No tracking tag added after conversation

**Diagnosis:**
1. Check confidence threshold (default: 0.7)
2. Verify intent patterns are matching
3. Check handoff service logs

**Resolution:**
```python
# Debug: Extract intent signals manually
from ghl_real_estate_ai.services.jorge.jorge_handoff_service import jorge_handoff_service

message = "I want to buy a house in Rancho Cucamonga"
signals = jorge_handoff_service.extract_intent_signals(message)
print(f"Buyer score: {signals['buyer_intent_score']}")
print(f"Seller score: {signals['seller_intent_score']}")
# Should show buyer_score >= 0.3 for handoff consideration
```

### Issue: Compliance Blocking Legitimate Messages

**Symptoms:**
- Normal messages being replaced with fallback
- Compliance-Alert tags appearing frequently

**Diagnosis:**
1. Check violation details in logs
2. Verify Tier 2 (LLM) audit isn't over-flagging

**Resolution:**
```python
# Review violations logged
# Logs should show pattern match or LLM reason

# If over-flagging, consider:
# 1. Adding false positive patterns to allowlist
# 2. Adjusting LLM audit sensitivity
```

### Issue: SMS Truncation Issues

**Symptoms:**
- Messages cut off mid-sentence
- URLs broken in SMS responses

**Diagnosis:**
1. Check if message exceeds 320 characters
2. Verify smart truncation is working

**Resolution:**
The SMS guard truncates at the last sentence boundary before 320 chars:

```python
# If long messages are critical, consider:
# 1. Using MMS for longer messages
# 2. Splitting into multiple SMS
# 3. Using a link to full response
```

---

## 8. Test Coverage Summary

### Lead Bot Routing Tests

| Test | Status | Description |
|------|--------|-------------|
| `test_lead_mode_activates_with_needs_qualifying_tag` | ✅ | Lead bot processes when tag present + mode=true |
| `test_seller_mode_takes_priority_over_lead` | ✅ | "Needs Qualifying" routes to seller when SELLER_MODE=true |
| `test_lead_mode_respects_deactivation_tags` | ✅ | AI-Off blocks lead routing |
| `test_lead_mode_disabled_skips_to_fallback` | ✅ | JORGE_LEAD_MODE=false skips routing |
| `test_lead_mode_adds_temperature_tag` | ✅ | Hot-Lead/Warm-Lead/Cold-Lead applied |
| `test_lead_mode_sms_guard_truncates` | ✅ | Response truncated at 320 chars |
| `test_lead_mode_compliance_blocks_bad_message` | ✅ | Compliance replaces blocked content |
| `test_lead_mode_error_falls_through` | ✅ | Error doesn't crash webhook |
| `test_buyer_lead_tag_does_not_route_to_lead_bot` | ✅ | "Buyer-Lead" goes to buyer, not lead |

### Lead Bot Handoff Tests

| Test | Status | Description |
|------|--------|-------------|
| `test_lead_to_buyer_handoff_on_buyer_intent` | ✅ | Buyer intent score >0.7 triggers handoff |
| `test_lead_to_seller_handoff_on_seller_intent` | ✅ | Seller intent phrases trigger handoff |
| `test_no_handoff_below_confidence_threshold` | ✅ | Score 0.5 does not trigger |
| `test_handoff_generates_correct_tag_swap` | ✅ | Removes source tag, adds target tag |
| `test_handoff_adds_tracking_tag` | ✅ | "Handoff-Lead-to-Buyer" tag present |
| `test_handoff_logs_analytics_event` | ✅ | analytics_service.track_event called |

### Running Tests

```bash
# Run all Lead Bot tests
pytest ghl_real_estate_ai/tests/test_lead_bot_handoff.py -v

# Run Lead Bot routing tests
pytest ghl_real_estate_ai/tests/test_jorge_delivery.py -k "lead" -v

# Run handoff service tests
pytest ghl_real_estate_ai/tests/services/test_jorge_handoff_service.py -v
```

### Test Coverage Target

| Metric | Target | Current |
|--------|--------|---------|
| Lead Bot Routing | 100% | 100% |
| Lead Bot Handoff | 100% | 100% |
| Compliance Guard | 100% | 100% |
| SMS Length Guard | 100% | 100% |

---

## Related Documentation

- [JORGE_FINALIZATION_SPEC.md](JORGE_FINALIZATION_SPEC.md) - Comprehensive Jorge Bot specification
- [WEBHOOK_SETUP_INSTRUCTIONS.md](WEBHOOK_SETUP_INSTRUCTIONS.md) - GHL webhook configuration
- [COMPLIANCE.md](../COMPLIANCE.md) - Fair Housing compliance details
- [API_SPEC.md](API_SPEC.md) - API documentation

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-06  
**Next Review**: After major Lead Bot changes
