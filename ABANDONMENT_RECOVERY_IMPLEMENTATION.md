# Lead Abandonment Recovery System - Implementation Summary

**Phase 2.1: Lead Abandonment Recovery**
**Status**: ✅ Complete
**Date**: February 10, 2026

## Overview

Automated system to detect silent leads (no response >24h) and trigger personalized recovery campaigns using market intelligence as re-engagement hooks.

**Target**: 15% of abandoned leads re-engage within 30 days

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 Background Task (Every 4 hours)                 │
│                                                                 │
│  ┌──────────────────┐      ┌─────────────────────┐            │
│  │ Abandonment      │ ───► │ Recovery            │            │
│  │ Detector         │      │ Orchestrator        │            │
│  └────────┬─────────┘      └──────────┬──────────┘            │
│           │                           │                        │
│           ▼                           ▼                        │
│  ┌──────────────────┐      ┌─────────────────────┐            │
│  │ abandonment_     │      │ Market Trigger      │            │
│  │ events (DB)      │      │ Service             │            │
│  └──────────────────┘      └─────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │ GHL Send Message    │
                    └─────────────────────┘
```

---

## Files Created

### Core Services
1. **`ghl_real_estate_ai/services/jorge/abandonment_detector.py`** (NEW)
   - Detects leads with no response >24h
   - Tracks abandonment stage: 24h, 3d, 7d, 14d, 30d
   - Queries `abandonment_events` table
   - Determines recovery eligibility

2. **`ghl_real_estate_ai/services/jorge/recovery_orchestrator.py`** (NEW)
   - Orchestrates multi-stage recovery sequence
   - Day 3: Quick check-in with market intel
   - Day 7: "Still thinking?" with price/rate alerts
   - Day 14: Market update with neighborhood activity
   - Day 30: Hail Mary with seasonal timing
   - Integrates with `MarketTriggerService` for re-engagement hooks

3. **`ghl_real_estate_ai/services/jorge/abandonment_background_task.py`** (NEW)
   - Background task runner (4-hour interval)
   - Periodic detection → orchestration loop
   - Graceful startup/shutdown

### Database
4. **`alembic/versions/2026_02_10_004_add_abandonment_events_table.py`** (NEW)
   - Creates `abandonment_events` table
   - Fields: contact_id, location_id, bot_type, last_contact_timestamp, current_stage, recovery_attempt_count, metadata
   - Indexes on contact_id, location+timestamp, stage

### Tests
5. **`ghl_real_estate_ai/tests/services/jorge/test_abandonment_detector.py`** (NEW)
   - Stage detection tests (24h → 30d)
   - Recovery eligibility logic
   - Database recording/clearing
   - Edge cases and error handling

6. **`ghl_real_estate_ai/tests/services/jorge/test_recovery_orchestrator.py`** (NEW)
   - Message generation per stage
   - Market trigger integration
   - GHL client interaction
   - Batch orchestration

7. **`ghl_real_estate_ai/tests/services/jorge/test_abandonment_integration.py`** (NEW)
   - End-to-end flow: detection → recovery
   - Multi-stage progression
   - Background task behavior
   - Re-engagement clearing

---

## Files Modified

### Market Trigger Service
**`ghl_real_estate_ai/services/jorge/market_trigger_service.py`**
- Added `ABANDONMENT_RECOVERY` trigger type
- Added `create_abandonment_trigger()` method
- Template for custom recovery messages

### FastAPI Main
**`ghl_real_estate_ai/api/main.py`**
- Added startup section for abandonment background task
- Wired GHL client + DB pool into services
- Added shutdown logic for graceful task termination

---

## Recovery Strategy

### Stage-Based Messaging

| Stage | Timing | Approach | Hook |
|-------|--------|----------|------|
| **24h** | First silence detection | Internal tracking only | - |
| **Day 3** | Quick check-in | Friendly, low-pressure | Recent market intel |
| **Day 7** | Still thinking? | Market urgency | Price drops, rate changes |
| **Day 14** | Market update | Comprehensive analysis | Neighborhood activity |
| **Day 30** | Hail Mary | Last chance, strategic timing | Seasonal opportunities |

### Message Personalization
- Uses `contact_metadata`: name, interest_area, budget, preferences
- Integrates real market triggers: price drops, rate changes, sales
- Fallback to generic market updates if no specific trigger available
- Random template selection for variety

### Safeguards
- **Circular prevention**: Won't re-attempt at same stage
- **Stage progression**: Only advances, never regresses
- **Rate limiting**: Built into GHL client (10 req/s)
- **Error resilience**: Database failures logged, never block in-memory operation

---

## Database Schema

```sql
CREATE TABLE abandonment_events (
    id SERIAL PRIMARY KEY,
    contact_id VARCHAR(100) UNIQUE NOT NULL,
    location_id VARCHAR(100) NOT NULL,
    bot_type VARCHAR(50) NOT NULL,  -- 'lead', 'buyer', 'seller'
    last_contact_timestamp FLOAT NOT NULL,  -- Unix timestamp
    current_stage VARCHAR(10) NOT NULL DEFAULT '24h',  -- '24h', '3d', '7d', '14d', '30d'
    recovery_attempt_count INT NOT NULL DEFAULT 0,
    metadata JSONB,  -- Contact preferences, interests, budget
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_abandonment_contact_id ON abandonment_events(contact_id);
CREATE INDEX idx_abandonment_location_timestamp ON abandonment_events(location_id, last_contact_timestamp);
CREATE INDEX idx_abandonment_stage ON abandonment_events(current_stage);
```

---

## Startup Configuration

### Environment Variables Required
- `GHL_API_KEY` - GoHighLevel API key
- `GHL_LOCATION_ID` - Primary location ID
- `DATABASE_URL` - PostgreSQL connection string

### Startup Log Output
```
✅ Jorge metrics repository initialized
✅ Lead Abandonment Recovery background task started (4-hour interval)
```

### Background Task Behavior
- Runs every 4 hours automatically
- Scans `abandonment_events` table for eligible contacts
- Orchestrates recovery batch (max 100 contacts per run)
- Marks successful attempts in database
- Continues on errors (non-blocking)

---

## Testing

### Run Tests
```bash
# Unit tests
pytest ghl_real_estate_ai/tests/services/jorge/test_abandonment_detector.py -v
pytest ghl_real_estate_ai/tests/services/jorge/test_recovery_orchestrator.py -v

# Integration tests
pytest ghl_real_estate_ai/tests/services/jorge/test_abandonment_integration.py -v

# All abandonment tests
pytest ghl_real_estate_ai/tests/services/jorge/test_abandonment* -v
```

### Test Coverage
- ✅ Stage detection (24h → 30d)
- ✅ Recovery eligibility logic
- ✅ Message generation per stage
- ✅ Market trigger integration
- ✅ Database recording/clearing
- ✅ End-to-end flow
- ✅ Background task behavior
- ✅ Error handling

---

## Migration

### Apply Database Migration
```bash
# From project root
alembic upgrade head
```

### Verify Table Created
```sql
SELECT * FROM abandonment_events LIMIT 5;
```

---

## Success Metrics

### KPIs to Monitor
1. **Re-engagement Rate**: % of abandoned leads that respond after recovery
   - **Target**: 15% within 30 days
2. **Recovery Conversion**: % of re-engaged leads that convert
3. **Stage Effectiveness**: Which stages (3d/7d/14d/30d) have highest response rates
4. **Time to Re-engagement**: Average days from abandonment to response

### Logging Output
```
INFO: Starting abandonment detection scan...
INFO: Found 23 abandoned contacts
INFO: Recovery batch complete: 21/23 successful
INFO: Sleeping for 14400s until next scan...
```

---

## Next Steps

### Phase 2.2 Enhancements (Future)
1. **A/B Testing**: Test different message templates per stage
2. **Channel Optimization**: Test SMS vs email recovery effectiveness
3. **Predictive Scoring**: ML model to predict re-engagement likelihood
4. **Dynamic Intervals**: Adjust timing based on contact behavior
5. **Multi-location Support**: Scale to handle multiple GHL locations

### Integration Points
- **Bot Conversation Hooks**: Auto-track last contact timestamp on every message
- **Re-engagement Detection**: Clear abandonment when contact responds
- **Handoff Integration**: Use abandonment data in cross-bot handoff decisions
- **BI Dashboard**: Add abandonment recovery analytics panel

---

## Notes

- **GHL Rate Limits**: 10 req/s enforced by `EnhancedGHLClient`
- **Background Task Interval**: 4 hours (configurable)
- **Max Contacts per Run**: 100 (configurable)
- **Stage Thresholds**: 24h/3d/7d/14d/30d (fixed, based on requirements)

**Implementation Date**: February 10, 2026
**Developer**: abandonment-dev (jorge-wave2 team)
**Status**: ✅ Ready for Testing
