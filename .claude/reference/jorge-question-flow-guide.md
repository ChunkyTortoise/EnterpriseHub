# Jorge Seller Bot: Question Flow Configuration Guide

**Created**: 2026-02-14
**Related Audit**: `.claude/audits/jorge-spec-audit-2026-02-14.md`

---

## Overview

The Jorge Seller Bot now supports **two qualification modes**:

1. **Simple Mode** (4 questions) - High conversion, friendly approach
2. **Full Mode** (10 questions) - Deep qualification, original spec

---

## Quick Start

### Environment Variable Configuration

Set in `.env` or environment:

```bash
# Simple Mode (default - 4 questions, high conversion)
JORGE_SIMPLE_MODE=true

# Full Mode (10 questions, deep qualification)
JORGE_SIMPLE_MODE=false
```

### Programmatic Configuration

```python
from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

# Switch to full mode
JorgeSellerConfig.set_mode(simple_mode=False)

# Switch to simple mode
JorgeSellerConfig.set_mode(simple_mode=True)

# Get questions for current mode
questions = JorgeSellerConfig.SELLER_QUESTIONS
```

---

## Question Flows

### Simple Mode (4 Questions)

**Optimized for**: High completion rate, mobile users, friendly experience

| Q# | Question | Captures |
|----|----------|----------|
| 1 | "What's got you considering wanting to sell, where would you move to?" | Motivation, relocation destination |
| 2 | "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?" | Timeline acceptance, urgency |
| 3 | "How would you describe your home, would you say it's move-in ready or would it need some work?" | Property condition, repair needs |
| 4 | "What price would incentivize you to sell?" | Price expectation, flexibility |

**Custom Fields Populated**:
- `seller_motivation`
- `relocation_destination`
- `timeline_urgency`
- `property_condition`
- `repair_estimate`
- `price_expectation`

**Classification Thresholds**:
- **HOT**: 4/4 questions + timeline accepted + 70%+ quality
- **WARM**: 3/4 questions + 50%+ quality
- **COLD**: Below warm threshold

**Expected Metrics**:
- Completion rate: 60%
- Hot conversion: 15%
- Opt-out rate: <5%

---

### Full Mode (10 Questions)

**Optimized for**: Deep qualification, investor leads, data completeness

| Q# | Question | Captures |
|----|----------|----------|
| 1 | "What's the address of the property you're thinking about selling?" | Property address, type |
| 2 | "What's got you considering wanting to sell, where would you move to?" | Motivation, relocation |
| 3 | "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?" | Timeline, urgency |
| 4 | "How would you describe your home, would you say it's move-in ready or would it need some work?" | Condition, repairs |
| 5 | "What price would incentivize you to sell?" | Price expectation |
| 6 | "Do you have any existing mortgage or liens on the property?" | Mortgage balance, liens |
| 7 | "Are there any repairs or improvements needed before listing?" | Repair estimate |
| 8 | "Have you tried listing this property before?" | Listing history |
| 9 | "Are you the primary decision-maker, or would anyone else need to be involved?" | Decision maker |
| 10 | "What's the best way to reach you - call, text, or email?" | Contact method |

**Custom Fields Populated** (all from Simple Mode plus):
- `property_address`
- `property_type`
- `mortgage_balance`
- `repair_estimate`
- `listing_history`
- `decision_maker_confirmed`
- `preferred_contact_method`

**Classification Thresholds**:
- **HOT**: 10/10 questions + timeline accepted + 70%+ quality
- **WARM**: 7/10 questions + 50%+ quality
- **COLD**: Below warm threshold

**Expected Metrics**:
- Completion rate: 40% (more challenging)
- Hot conversion: 20% (better qualified)
- Opt-out rate: <8% (longer flow)

---

## GHL Custom Field Setup

### Required for All Modes

```
seller_temperature (Dropdown: Hot-Seller, Warm-Seller, Cold-Seller)
seller_motivation (Text)
relocation_destination (Text)
timeline_urgency (Dropdown: <30 days, 30-60 days, 60-90 days, 90+ days)
property_condition (Dropdown: Move-in Ready, Minor Work, Major Work, Needs Renovation)
price_expectation (Currency)
questions_answered (Number)
qualification_score (Number)
lead_value_tier (Dropdown: A, B, C, D)
ai_valuation_price (Currency)
```

### Additional Fields for Full Mode

```
property_address (Text)
property_type (Dropdown: SFH, Condo, Townhouse, Multi-Family, Land)
mortgage_balance (Currency)
repair_estimate (Currency)
listing_history (Dropdown: Never Listed, Listed 0-6mo ago, Listed 6-12mo ago, Listed 1+ years ago)
decision_maker_confirmed (Dropdown: Yes - Primary, Yes - Joint, No - Multiple)
preferred_contact_method (Dropdown: Call, Text, Email, Any)
last_bot_interaction (DateTime)
qualification_complete (Boolean)
```

---

## Migration Guide

### From 4-Question to 10-Question Flow

**Step 1**: Backup current configuration
```bash
cp .env .env.backup
```

**Step 2**: Add GHL custom fields
- Log into GHL location settings
- Add missing custom fields from list above
- Note field IDs for `.env` configuration

**Step 3**: Update `.env`
```bash
# Enable full mode
JORGE_SIMPLE_MODE=false

# Add custom field IDs (if using semantic names)
CUSTOM_FIELD_PROPERTY_ADDRESS=your_field_id
CUSTOM_FIELD_MORTGAGE_BALANCE=your_field_id
CUSTOM_FIELD_REPAIR_ESTIMATE=your_field_id
CUSTOM_FIELD_LISTING_HISTORY=your_field_id
CUSTOM_FIELD_DECISION_MAKER_CONFIRMED=your_field_id
CUSTOM_FIELD_PREFERRED_CONTACT_METHOD=your_field_id
```

**Step 4**: Test with sample lead
```bash
# Use staging environment first
curl -X POST http://localhost:8000/api/jorge/seller/test \
  -H "Content-Type: application/json" \
  -d '{"mode": "full", "test_lead_id": "test_001"}'
```

**Step 5**: Monitor metrics
- Track completion rates
- Monitor opt-out rates
- Compare hot lead conversion
- Adjust thresholds if needed

---

## Decision Matrix: Which Mode to Use?

### Use Simple Mode (4 Questions) When:

✅ Optimizing for **high completion rates**
✅ Targeting **mobile-first** users
✅ Prioritizing **friendly user experience**
✅ Working with **general consumer** leads
✅ SMS is primary channel
✅ Speed to qualification is critical

**Pros**:
- 60% completion rate
- Faster time to hot lead
- Lower friction
- Better mobile UX

**Cons**:
- Less detailed qualification data
- May miss mortgage/repair insights
- Limited decision-maker clarity

---

### Use Full Mode (10 Questions) When:

✅ Targeting **investor** or **wholesale** leads
✅ Need **comprehensive** financial data
✅ Mortgage balance is **critical** to deal structure
✅ Working with **high-value** properties ($1M+)
✅ Multi-decision-maker deals common
✅ Repair estimates needed upfront

**Pros**:
- Complete qualification data
- 20% hot conversion (better qualified)
- Fewer wasted agent calls
- Mortgage/lien visibility

**Cons**:
- 40% completion rate (vs 60%)
- Higher opt-out risk (8% vs 5%)
- More messages required
- Slower qualification

---

## Hybrid Approach (Recommended)

Use **Simple Mode** by default, then **escalate** to additional questions for high-value leads:

```python
from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

# Start with simple mode
questions = JorgeSellerConfig.SELLER_QUESTIONS_SIMPLE

# After Q4, if HOT lead detected:
if lead_temperature == "hot":
    # Ask additional qualifying questions
    additional_questions = {
        6: JorgeSellerConfig.SELLER_QUESTIONS_FULL[6],  # Mortgage/liens
        7: JorgeSellerConfig.SELLER_QUESTIONS_FULL[7],  # Repairs
        9: JorgeSellerConfig.SELLER_QUESTIONS_FULL[9],  # Decision maker
    }
```

**Benefits**:
- ✅ High completion (60%) for all leads
- ✅ Deep qualification for hot leads only
- ✅ Best of both modes

---

## Testing & Validation

### Unit Tests

```bash
# Test mode switching
pytest tests/test_jorge_config.py::test_mode_switching

# Test question flow
pytest tests/test_jorge_seller_bot.py::test_full_question_flow

# Test custom field mapping
pytest tests/test_jorge_seller_bot.py::test_custom_field_population
```

### Integration Tests

```bash
# Test GHL field updates
pytest tests/integration/test_jorge_ghl_integration.py

# Test temperature classification (10 questions)
pytest tests/integration/test_jorge_classification_full_mode.py
```

---

## Monitoring & Analytics

### Key Metrics by Mode

Track in BI dashboard:

```sql
-- Completion rates by mode
SELECT
    mode,
    COUNT(*) as total_leads,
    SUM(CASE WHEN questions_answered = expected_questions THEN 1 ELSE 0 END) as completed,
    AVG(questions_answered::float / expected_questions) as completion_rate
FROM jorge_seller_interactions
GROUP BY mode;

-- Hot lead conversion by mode
SELECT
    mode,
    seller_temperature,
    COUNT(*) as leads,
    AVG(qualification_score) as avg_score
FROM jorge_seller_leads
GROUP BY mode, seller_temperature;
```

### Alert Thresholds

```python
# Update alerting rules for each mode
ALERT_RULES = {
    "simple_mode": {
        "min_completion_rate": 0.55,  # Alert if <55%
        "min_hot_conversion": 0.12,   # Alert if <12%
        "max_opt_out": 0.06,          # Alert if >6%
    },
    "full_mode": {
        "min_completion_rate": 0.35,  # Alert if <35%
        "min_hot_conversion": 0.15,   # Alert if <15%
        "max_opt_out": 0.10,          # Alert if >10%
    },
}
```

---

## Troubleshooting

### Issue: Low completion rate in Full Mode

**Symptoms**: <30% completion (expected: 40%)

**Diagnosis**:
```python
# Check drop-off points
SELECT question_number, COUNT(*) as drop_offs
FROM jorge_seller_interactions
WHERE mode = 'full' AND questions_answered < 10
GROUP BY question_number
ORDER BY drop_offs DESC;
```

**Solutions**:
1. Simplify question wording (Q6-Q10)
2. Add motivational messaging between questions
3. Consider hybrid approach
4. A/B test question order

---

### Issue: Missing custom field data

**Symptoms**: GHL custom fields not updating

**Diagnosis**:
```bash
# Check field mapping
python -c "from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig; print(JorgeSellerConfig.QUESTION_FIELD_MAPPING)"

# Check GHL field IDs
env | grep CUSTOM_FIELD_
```

**Solutions**:
1. Verify GHL custom field IDs in `.env`
2. Check field permissions in GHL
3. Review webhook payload logs
4. Validate field name mapping

---

## Changelog

### 2026-02-14 - Initial Implementation
- Added full 10-question flow support
- Implemented mode switching (`JORGE_SIMPLE_MODE`)
- Added 9 new custom fields for full mode
- Created configurable thresholds per mode
- Updated success metrics for both modes

---

## Next Steps

1. **Choose Mode**: Decide on simple vs full based on use case
2. **Configure GHL**: Add required custom fields
3. **Test Flow**: Run through sample leads in staging
4. **Monitor Metrics**: Track completion and conversion rates
5. **Iterate**: Adjust thresholds based on real data

---

**Need Help?**
- Review audit: `.claude/audits/jorge-spec-audit-2026-02-14.md`
- Check config: `ghl_real_estate_ai/ghl_utils/jorge_config.py`
- See tests: `tests/agents/test_jorge_seller_bot.py`
