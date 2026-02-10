# Adaptive PCS Calculation - Implementation Summary

**Phase**: 1.3
**Date**: 2026-02-10
**Status**: ✅ Complete

## Overview

Replaced static PCS (Psychological Commitment Score) calculation with dynamic, conversation-based scoring that updates after each message in the seller bot workflow.

## Problem Solved

**Before**: PCS was calculated once at conversation start and never updated. A seller who starts cold but warms up during the conversation would be scored incorrectly.

**After**: PCS now recalculates dynamically after each message, tracking engagement evolution in real-time.

## Implementation Details

### 1. New Method: `recalculate_pcs()` in `SellerPsychologyAnalyzer`

Location: `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/services/seller_psychology_analyzer.py`

**Engagement Factors Tracked**:
- **Engagement Velocity**: Response expansion/contraction over time (-1.0 to 1.0)
  - Compares recent message lengths to earlier messages
  - Positive = expanding responses (warming)
  - Negative = shortening responses (cooling)

- **Question Depth**: Detailed vs yes/no answers (0.0 to 1.0)
  - Word count analysis
  - Detail marker detection (because, so, need to, $, timeline, etc.)

- **Objection Handling**: Resistance vs acceptance
  - Resistance markers: "not interested", "no thanks", "too expensive", etc.
  - Acceptance markers: "sounds good", "let's do it", "tell me more", etc.

- **Commitment Indicators**: Count of commitment signals (0-5+)
  - "when can you", "what's the next step", "I'm ready", etc.

**PCS Adjustment Range**: -10 to +10 points per message
- Engagement velocity: ±3 points
- Question depth: ±3 points
- Objection handling: ±2 points
- Commitment indicators: ±2 points

### 2. New Workflow Node: `recalculate_pcs_node()`

Location: `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/agents/jorge_seller_bot.py`

**Integration**:
- Added to both standard and adaptive workflows
- Executes after `generate_jorge_response` / `generate_adaptive_response`
- Updates `intent_profile` with new PCS score
- Syncs to GHL custom field "PCS"
- Emits event for PCS update tracking

**Workflow Flow**:
```
generate_jorge_response → recalculate_pcs → END
                       ↓
                   GHL Sync
                       ↓
                Event Emission
```

## Success Criteria

✅ **PCS updates dynamically** - Minimum 1 update per message after initial calc
✅ **Trend detection works** - Warming/cooling/stable trends identified correctly
✅ **GHL sync** - Updated PCS synced to GHL "PCS" custom field
✅ **Accurate engagement tracking** - All 4 engagement factors tracked correctly

## Test Results

All 5 test scenarios passed:

1. **Cold Seller (Short Answers)** → PCS decreased from 50.0 to 44.0 (trend: cooling) ✅
2. **Warming Seller (Expanding Responses)** → PCS increased from 50.0 to 54.0 (trend: warming) ✅
3. **Acceptance Signals** → PCS increased from 60.0 to 62.0 (objection_handling: acceptance) ✅
4. **Resistance Signals** → PCS decreased from 60.0 to 54.0 (objection_handling: resistance) ✅
5. **High Commitment Indicators** → PCS increased from 70.0 to 75.0 (3+ commitment signals) ✅

## Files Modified

1. `/ghl_real_estate_ai/services/seller_psychology_analyzer.py`
   - Added `recalculate_pcs()` method
   - Added 4 helper methods for engagement analysis

2. `/ghl_real_estate_ai/agents/jorge_seller_bot.py`
   - Added `recalculate_pcs_node()` workflow node
   - Integrated into standard workflow
   - Integrated into adaptive workflow

## API Response Changes

The `process_seller_message()` response now includes updated PCS after each conversation turn:

```python
{
    "response_content": "...",
    "lead_id": "...",
    "current_step": "...",
    "engagement_status": "...",
    "frs_score": 75.0,
    "pcs_score": 68.5,  # ← Dynamically updated!
    "handoff_signals": {...},
    "ab_test": {...}
}
```

## Next Steps

- [ ] Collect historical conversation data to validate PCS correlation with conversion (target R² > 0.75)
- [ ] Monitor PCS trend accuracy (target 80%+ for warming/cooling detection)
- [ ] A/B test adaptive PCS vs static PCS for qualification accuracy improvement (+5-8% expected)

## Impact

**Expected Impact**: +5-8% seller qualification accuracy

**Key Benefit**: Sellers who start cold but warm up during conversation will now be scored correctly, improving qualification accuracy and reducing false negatives.

## Testing

Run the test suite:
```bash
python3 test_adaptive_pcs.py
```

All tests validate:
- PCS decreases for disengaged sellers
- PCS increases for engaged sellers
- Trend detection (warming/cooling/stable)
- Engagement metrics accuracy
