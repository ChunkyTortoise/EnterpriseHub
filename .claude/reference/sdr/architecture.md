# Autonomous SDR Agent Module — Architecture (6ql1)

**Status**: Design complete | **Phase**: MVP build next | **Estimated**: 60h total

---

## Directory Structure

```
ghl_real_estate_ai/
├── agents/sdr/
│   ├── __init__.py
│   ├── sdr_agent.py              # SDRAgent(BaseBotWorkflow) — main orchestrator
│   ├── objection_handler.py      # Pattern match + Claude fallback for objections
│   ├── personalization_engine.py # Claude-driven prospect personalization
│   └── prospect_profiler.py      # MLS data enrichment (Phase 2)
├── services/sdr/
│   ├── __init__.py
│   ├── prospect_sourcer.py       # ProspectSourcer — GHL pipeline, stale, expired, FSBO
│   ├── outreach_sequence_engine.py # OutreachSequenceEngine — multi-touch dispatch
│   ├── cadence_scheduler.py      # CadenceScheduler — cron + AI timing
│   ├── qualification_gate.py     # QualificationGate — FRS/PCS threshold
│   ├── sdr_booking_service.py    # Composes CalendarBookingService (Phase 3)
│   ├── sdr_performance_tracker.py # Rolling windows 1h/24h/7d (Phase 3)
│   └── sdr_metrics_collector.py  # AlertingService integration (Phase 3)
├── models/
│   ├── sdr_models.py             # ORM + Pydantic schemas
│   └── sdr_state.py              # OutreachState TypedDict
├── api/routes/
│   └── sdr.py                    # FastAPI router — /sdr/* endpoints
└── config/
    └── sdr_config.yaml           # Sequence timing, thresholds, rate limits
```

---

## Core Classes

### SDRAgent (agents/sdr/sdr_agent.py)
```python
class SDRAgent(BaseBotWorkflow):
    async def run_prospecting_cycle(location_id, sources, max_per_source) -> Dict
    async def process_inbound_reply(contact_id, message, channel, location_id) -> None
    async def evaluate_and_handoff(contact_id, location_id) -> Optional[HandoffData]
```

### ProspectSourcer (services/sdr/prospect_sourcer.py)
```python
class ProspectSource(Enum):
    GHL_PIPELINE | EXPIRED_MLS | FSBO | STALE_LEAD

class ProspectSourcer:
    async def fetch_prospects(location_id, sources, max_per_source=50) -> List[ProspectProfile]
    async def _fetch_ghl_pipeline_leads(location_id, stage_ids) -> List[ProspectProfile]
    async def _fetch_stale_leads(location_id, inactive_days=14) -> List[ProspectProfile]
    # Phase 2: _fetch_expired_listings, _fetch_fsbo_signals
```

### OutreachSequenceEngine (services/sdr/outreach_sequence_engine.py)
```python
class SequenceStep(Enum):
    ENROLLED | SMS_1 | EMAIL_1 | SMS_2 | VOICEMAIL_1 | EMAIL_2 | SMS_3
    VOICEMAIL_2 | NURTURE_PAUSE | QUALIFIED | BOOKED | DISQUALIFIED | OPTED_OUT

class OutreachSequenceEngine:
    async def enroll_prospect(prospect, sequence_variant="default") -> OutreachRecord
    async def advance_sequence(record, reply_received=False, engagement_signal=None) -> OutreachRecord
    async def dispatch_touch(record, step, personalization_context) -> bool
    async def _build_message(record, step, personalization_context) -> str  # Claude, 160-char SMS cap
```

### CadenceScheduler (services/sdr/cadence_scheduler.py)
```python
class CadenceScheduler:
    async def process_webhook_trigger(contact_id, location_id, trigger_type, webhook_data) -> None
    async def process_due_touches(batch_size=50, location_id=None) -> Dict  # cron every 15min
    async def compute_next_touch_time(record, next_step, engagement_signals) -> datetime  # AI-driven Phase 2
    async def get_statistics(location_id, days=30) -> Dict
```

### QualificationGate (services/sdr/qualification_gate.py)
```python
@dataclass
class GateDecision:
    passed: bool
    frs_score: float
    pcs_score: float
    lead_type: str  # "buyer" | "seller" | "ambiguous"
    confidence: float
    intent_profile: LeadIntentProfile
    handoff_target: Optional[str]   # "lead_bot" | "buyer_bot" | "seller_bot"
    disqualify_reason: Optional[str]

class QualificationGate:
    FRS_THRESHOLD = 60.0
    CONF_THRESHOLD = 0.70  # matches existing handoff_service constant
    async def evaluate(contact_id, conversation_history, prospect_profile) -> GateDecision
```

### ObjectionHandler (agents/sdr/objection_handler.py)
```python
OBJECTION_PATTERNS = {
    "not_interested": ["not interested", "don't contact", "remove me", "stop texting"],
    "already_agent":  ["have an agent", "working with someone", "my realtor"],
    "timing":         ["not ready", "maybe later", "few months", "next year"],
    "price":          ["too expensive", "can't afford", "market is crazy"],
    "info_request":   ["tell me more", "what's this about", "how did you get my number"],
}

class ObjectionHandler:
    def classify_objection(message) -> Optional[str]  # pattern-match first, Claude fallback
    async def generate_rebuttal(objection_type, prospect_profile, record) -> ObjectionResult
    def should_opt_out(objection_type) -> bool  # True for not_interested
```

---

## Database Schema (4 new tables)

```python
class SDRProspect(Base):          # sdr_prospects — one row per contact
    id, contact_id, location_id, source, lead_type, frs_score, pcs_score, enrolled_at

class SDROutreachSequence(Base):  # sdr_outreach_sequences — current step + scheduling
    id, prospect_id, contact_id, location_id, current_step, ab_variant, next_touch_at

class SDROutreachTouch(Base):     # sdr_outreach_touches — every touch sent + replies
    id, sequence_id, contact_id, step, channel, message_body, sent_at, replied_at, reply_body

class SDRObjectionLog(Base):      # sdr_objection_logs — objection analytics
    id, contact_id, objection_type, raw_message, rebuttal_used, outcome
```

**PII**: `reply_body` and `raw_message` — encrypt with Fernet at ORM level.

---

## API Endpoints (api/routes/sdr.py)

```
POST   /sdr/prospects/source          # Trigger prospecting cycle (background)
POST   /sdr/prospects/enroll          # Manually enroll contact_ids
GET    /sdr/prospects/{contact_id}    # Get profile + sequence state

POST   /sdr/sequences/process-batch   # Cron endpoint — due touches
GET    /sdr/sequences/{contact_id}    # Inspect sequence record
DELETE /sdr/sequences/{contact_id}    # Manually disenroll

POST   /sdr/webhook/reply             # GHL ContactReply webhook
POST   /sdr/webhook/booking-confirmed # GHL AppointmentScheduled webhook
POST   /sdr/webhook/opt-out           # GHL DND/stop webhook
POST   /sdr/webhook/stage-change      # GHL pipeline stage webhook

GET    /sdr/stats                     # SDRMetricWindow
GET    /sdr/stats/sequences           # Per-sequence conversion
GET    /sdr/stats/objections          # Objection analytics
```

---

## GHL Integration Points

### 4 New Methods on EnhancedGHLClient
```python
async def get_contacts_by_pipeline_stage(location_id, stage_id, limit=100) -> List[GHLContactData]
async def send_sms(contact_id, message, location_id) -> GHLAPIResponse
async def trigger_workflow(contact_id, workflow_id, location_id, event_data=None) -> GHLAPIResponse
async def get_contacts_inactive_since(location_id, since, limit=100) -> List[GHLContactData]
```

### GHL Webhooks Consumed
| Event | SDR Endpoint |
|-------|-------------|
| ContactReply | POST /sdr/webhook/reply |
| AppointmentScheduled | POST /sdr/webhook/booking-confirmed |
| ContactOptedOut | POST /sdr/webhook/opt-out |
| OpportunityStageChanged | POST /sdr/webhook/stage-change |

### Required Env Vars
```
SDR_WORKFLOW_SMS_1=<ghl_workflow_id>
SDR_WORKFLOW_EMAIL_1=<ghl_workflow_id>
SDR_WORKFLOW_VOICEMAIL_DROP=<ghl_workflow_id>
SDR_CALENDAR_ID=<ghl_calendar_id>
SDR_PIPELINE_STAGE_IDS=stage1,stage2   # comma-separated
```

---

## Data Flow

```
SOURCING: POST /sdr/prospects/source
  → ProspectSourcer.fetch_prospects() → EnhancedGHLClient (pipeline + stale)
  → OutreachSequenceEngine.enroll_prospect() → Claude builds SMS_1 → GHL send
  → CadenceScheduler sets next_touch_at

CADENCE: POST /sdr/sequences/process-batch (every 15min)
  → SELECT sdr_outreach_sequences WHERE next_touch_at <= NOW()
  → OutreachSequenceEngine.advance_sequence() → dispatch_touch() → update record

INBOUND: GHL webhook → POST /sdr/webhook/reply
  → SDRAgent.process_inbound_reply()
  → ObjectionHandler.classify_objection()
    - opt-out: tag DND, stop sequence
    - objection: generate rebuttal, advance sequence
    - engagement: advance_sequence(reply_received=True)
  → QualificationGate.evaluate()  [FRS >= 60 + confidence >= 0.70]
    - passed: SDRBookingService (if HOT) + JorgeHandoffService.evaluate_handoff_from_profile()
    - failed: stay in sequence, record FRS/PCS
```

---

## Critical Constraints

- **TCPA**: All SMS through existing `response_pipeline` 5-stage processor — do NOT bypass
- **Rate limits**: `max_touches_per_contact_per_day: 1`, `daily_sms_cap: 500/location`
  Redis key: `sdr:sms:daily:{location_id}:{date}`
- **Circuit breaker**: GHL dispatch wrapped in `services/circuit_breaker.py`; 3 failures → alert
- **Idempotency**: `contact_id + step + sent_at::date` dedup in `sdr_outreach_touches`
- **Handoff**: Reuses `JorgeHandoffService.evaluate_handoff_from_profile()` — no new handoff code

---

## Build Sequence

### Phase 1 — MVP (~20h)
1. `models/sdr_models.py` + `models/sdr_state.py`
2. Alembic migration (requires explicit approval)
3. `services/sdr/prospect_sourcer.py` (GHL pipeline + stale only)
4. `services/sdr/outreach_sequence_engine.py` (fixed-schedule dispatch)
5. `services/sdr/cadence_scheduler.py` (config defaults only)
6. `services/sdr/qualification_gate.py` (uses existing LeadIntentDecoder)
7. `agents/sdr/sdr_agent.py` (SDRAgent with run_prospecting_cycle + process_inbound_reply)
8. 4 new methods on `enhanced_ghl_client.py`
9. `api/routes/sdr.py` + mount in app.py
10. `config/sdr_config.yaml`
11. Unit tests: qualification_gate, sequence step logic

### Phase 2 — AI Timing + Objections (~15h)
- `agents/sdr/objection_handler.py` (Claude fallback)
- `agents/sdr/personalization_engine.py`
- AI-driven `compute_next_touch_time()`
- FSBO + expired listing sourcing

### Phase 3 — Booking + Dashboard (~15h)
- `services/sdr/sdr_booking_service.py`
- `services/sdr/sdr_performance_tracker.py`
- Streamlit `sdr_dashboard.py`
- AlertingService integration

### Phase 4 — A/B Testing (~10h)
- ABTestingService integration for sequence variants
- `/sdr/ab-tests` endpoints
