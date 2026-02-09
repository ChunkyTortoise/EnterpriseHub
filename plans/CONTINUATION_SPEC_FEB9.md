# Portfolio Expansion Wave 3 — Continuation Spec

**Date**: Feb 9, 2026
**Status**: 5 workstreams, 3 repos, ~30 hours estimated
**Goal**: Transform portfolio from "shows code" to "closes deals" — demos, adapters, case study

---

## Execution Teams (3 parallel streams)

```
TEAM ALPHA (EnterpriseHub)          TEAM BETA (docqa-engine)       TEAM GAMMA (ai-orchestrator)
─────────────────────────           ─────────────────────────      ──────────────────────────────
WS1: Bot Config (cnq) P1           WS2: Client Demo (lcx) P1     WS3: Flow Visualizer (tml) P2
  └→ WS1.1: BotPersonality ABC       └→ WS2.1: Session mgmt        └→ WS3.1: Event collector
  └→ WS1.2: YAML schema+loader       └→ WS2.2: Upload UX           └→ WS3.2: Trace dataclasses
  └→ WS1.3: RE extraction            └→ WS2.3: Demo questions       └→ WS3.3: Streamlit app
  └→ WS1.4: Dental vertical          └→ WS2.4: Tests                └→ WS3.4: Tests
  └→ WS1.5: Tests
                                    WS5: RAG Case Study (ia3) P2
WS4: HubSpot Adapter (gwn) P2        └→ Architecture diagram
  └→ WS4.1: CRM Protocol ABC         └→ Performance data
  └→ WS4.2: GHL extraction           └→ Prose + publish
  └→ WS4.3: HubSpot adapter
  └→ WS4.4: Tests

THEN (blocked):
  s7y: Interactive chatbot widget ← blocked by cnq
  hfi: REST API + templates     ← blocked by tml
  58t: docqa REST API + auth    ← blocked by ruy (DONE)
```

---

## WS1: Industry-Agnostic Bot Configuration (cnq — P1, IN_PROGRESS)

**Repo**: EnterpriseHub
**Effort**: ~8 hours
**Unblocks**: s7y (Interactive chatbot demo widget)

### What Exists
- `IndustrySolutions` + `IndustryVertical` enum (10 verticals)
- `BaseMarketService` ABC with `MarketConfig`
- `JorgeSellerConfig`, `BuyerBudgetConfig`, `LeadBotConfig` dataclasses
- Feature flags via `JorgeFeatureConfig`
- Environment override pattern via `from_environment()`

### What's Hardcoded (Must Abstract)
- Bot personality (tone, style, approach)
- Intent patterns (real-estate-specific: "CMA", "pre-approval", "move-in ready")
- Conversation flow (lead → qualify → hot/warm/cold)
- Temperature classification (based on RE deal readiness)
- Handoff signals (buyer/seller-specific triggers)

### Implementation Plan

#### WS1.1: BotPersonality ABC + Domain Intent Decoder
**File**: `ghl_real_estate_ai/agents/bot_personality.py`
```python
class BotPersonality(ABC):
    """Industry-agnostic bot personality configuration."""
    industry: str
    bot_type: str  # "lead", "qualifier", "specialist"
    tone: str  # "friendly", "consultative", "transactional"

    @abstractmethod
    def get_qualification_questions(self) -> list[QualificationQuestion]

    @abstractmethod
    def get_intent_signals(self) -> dict[str, list[str]]  # signal → keywords

    @abstractmethod
    def get_temperature_thresholds(self) -> dict[str, float]

    @abstractmethod
    def get_handoff_triggers(self) -> list[HandoffTrigger]

    @abstractmethod
    def get_system_prompt(self) -> str

class BotPersonalityRegistry:
    """Registry for industry-specific personality implementations."""
    _personalities: dict[str, type[BotPersonality]] = {}

    @classmethod
    def register(cls, industry: str, personality_cls: type[BotPersonality])

    @classmethod
    def get(cls, industry: str, bot_type: str) -> BotPersonality
```

#### WS1.2: YAML Config Schema + Loader
**File**: `ghl_real_estate_ai/agents/personality_config.py`
```python
class PersonalityConfig(BaseModel):
    """Pydantic schema for YAML personality config."""
    industry: str
    bot_type: str
    tone: str
    system_prompt_template: str
    qualification_questions: list[QualificationQuestionConfig]
    intent_signals: dict[str, list[str]]
    temperature_thresholds: TemperatureConfig
    handoff_triggers: list[HandoffTriggerConfig]

    @classmethod
    def from_yaml(cls, path: Path) -> "PersonalityConfig"
```

**Files**: `config/personalities/real_estate_lead.yaml`, `config/personalities/dental_lead.yaml`

#### WS1.3: Extract Real Estate as First Implementation
**File**: `ghl_real_estate_ai/agents/personalities/real_estate.py`
- Extract current hardcoded personality from `lead_bot.py`, `jorge_buyer_bot.py`, `jorge_seller_bot.py`
- Implement `RealEstateBotPersonality(BotPersonality)`
- Wire existing bots to use personality config (backward compatible)

#### WS1.4: Dental Vertical Implementation
**File**: `ghl_real_estate_ai/agents/personalities/dental.py`
- `DentalBotPersonality(BotPersonality)`
- Dental-specific intent signals: "teeth whitening", "root canal", "insurance accepted"
- Dental qualification: procedure type, insurance, urgency, budget
- Dental handoff: general → cosmetic → orthodontic

#### WS1.5: Tests
**File**: `tests/agents/test_bot_personality.py` (~20 tests)
- ABC contract tests
- YAML loading + validation
- Real estate personality matches current behavior
- Dental personality loads and qualifies correctly
- Registry lookup + fallback
- Environment override

---

## WS2: Client Demo Mode — docqa-engine (lcx — P1, UNBLOCKED)

**Repo**: docqa-engine (`/Users/cave/Documents/GitHub/docqa-engine`)
**Effort**: ~4 hours
**Dependency**: ruy (DONE — vector DB adapters shipped)

### What Exists
- 5-tab Streamlit app (Documents, Ask, Prompt Lab, Chunking Lab, Stats)
- File upload (TXT, MD, PDF, DOCX, CSV) with ingestion pipeline
- Hybrid retrieval (BM25 + dense + RRF)
- Citations with relevance scores
- 271 tests passing

### What to Build

#### WS2.1: Session Management
**Modify**: `app.py`
- Session-scoped pipeline (per browser tab via `st.session_state`)
- "Start New Demo" button (resets pipeline, clears docs)
- Auto-reset after 30 min inactivity
- Upload progress tracking

#### WS2.2: Simplified Upload UX
**Modify**: `app.py` Documents tab
- Large drop zone with clear instructions
- File list with ingestion status (pending/processing/done)
- Chunk count + readiness indicator
- "Demo Ready" badge when docs ingested

#### WS2.3: Demo Questions + Copy Buttons
**Modify**: `app.py` Ask tab
- 5 pre-canned questions in expandable section:
  1. "What is the main topic of these documents?"
  2. "Summarize the key findings"
  3. "What are the most important dates or deadlines?"
  4. "List any recommendations or action items"
  5. "What risks or concerns are mentioned?"
- Copy buttons for answers and citations
- Retrieval time + citation confidence display

#### WS2.4: Tests
**File**: `tests/test_client_demo.py` (~15 tests)
- Session isolation (no bleed between demos)
- Reset clears all state
- Pre-canned questions return valid results
- Large PDF handling (100+ pages)
- Upload progress tracking

---

## WS3: Streamlit Agent Flow Visualizer — ai-orchestrator (tml — P2)

**Repo**: ai-orchestrator (`/Users/cave/Documents/GitHub/ai-orchestrator`)
**Effort**: ~8 hours
**Unblocks**: hfi (REST API + templates)

### What Exists
- `AIOrchestrator` with 5 providers (Claude, Gemini, OpenAI, Perplexity, Mock)
- `ToolRegistry` with validation and execution
- Cost tracking, rate limiting, retry strategies
- 171 tests, CLI interface, no Streamlit demo

### What to Build

#### WS3.1: Event Collection Layer
**File**: `agentforge/observability/flow_event.py`
```python
@dataclass
class FlowEvent:
    timestamp: float
    sequence_id: int
    component: str      # "user", "orchestrator", "provider", "tool"
    event_type: str     # "message", "tool_call", "tool_result", "response"
    content: str
    metadata: dict
    parent_id: int | None = None

@dataclass
class ConversationTrace:
    conversation_id: str
    events: list[FlowEvent]
    total_cost_usd: float
    total_elapsed_ms: float
```

**File**: `agentforge/observability/trace_collector.py`
- `TraceCollector` — accumulates events during execution
- Hook into `AIOrchestrator.chat()`, `ToolRegistry.execute()`
- Non-intrusive (disabled by default, enabled via `trace=True`)

#### WS3.2: Streamlit App — Flow Diagram
**File**: `streamlit_demo/app.py` (main entry)
**File**: `streamlit_demo/components/flow_diagram.py`
- Timeline visualization: User → Provider → Tool → Result → Response
- Color-coded nodes (success=green, tool=blue, fallback=orange, error=red)
- Click-to-inspect node details

#### WS3.3: Streamlit App — Metrics + Inspector
**File**: `streamlit_demo/components/message_inspector.py`
- Full prompt/response content on click
- Token counts, cost, latency breakdown

**File**: `streamlit_demo/components/metrics_dashboard.py`
- Provider latency comparison
- Cost breakdown by provider/model
- Tool execution frequency

#### WS3.4: Tests
**File**: `tests/test_flow_visualization.py` (~15 tests)
- Event collection captures all flow steps
- Trace serialization to JSON
- Streamlit component data preparation
- Mock provider traces

---

## WS4: HubSpot CRM Adapter (gwn — P2)

**Repo**: EnterpriseHub
**Effort**: ~6 hours
**Independent** (no blockers or dependents)

### What Exists
- `EnhancedGHLClient` — full GoHighLevel integration (rate limited, real-time sync)
- GHL-specific abstractions throughout services

### What to Build

#### WS4.1: CRM Protocol ABC
**File**: `ghl_real_estate_ai/services/crm_protocol.py`
```python
class CRMProtocol(Protocol):
    """CRM-agnostic interface for contact/lead management."""
    async def get_contact(self, contact_id: str) -> CRMContact
    async def update_contact(self, contact_id: str, fields: dict) -> None
    async def add_tag(self, contact_id: str, tag: str) -> None
    async def remove_tag(self, contact_id: str, tag: str) -> None
    async def create_task(self, contact_id: str, task: CRMTask) -> str
    async def get_pipeline_stage(self, contact_id: str) -> str
    async def update_pipeline_stage(self, contact_id: str, stage: str) -> None
```

#### WS4.2: GHL Adapter (Extract from EnhancedGHLClient)
**File**: `ghl_real_estate_ai/services/crm_adapters/ghl_adapter.py`
- Implement `CRMProtocol` wrapping existing `EnhancedGHLClient`
- Backward compatible — existing code still works

#### WS4.3: HubSpot Adapter
**File**: `ghl_real_estate_ai/services/crm_adapters/hubspot_adapter.py`
- Implement `CRMProtocol` using HubSpot API v3
- Contact CRUD, tags (as properties), pipeline stages
- Rate limiting (10 req/s standard tier)

#### WS4.4: Tests
**File**: `tests/services/test_crm_protocol.py` (~20 tests)
- Protocol contract tests (both adapters)
- GHL adapter wraps existing client correctly
- HubSpot adapter mocked API calls
- CRM factory/registry

---

## WS5: RAG Case Study (ia3 — P2, IN_PROGRESS)

**Repo**: EnterpriseHub (docs/)
**Effort**: ~2 hours
**Type**: Writing, not code

### Deliverable
**File**: `docs/case_studies/rag_service.md`
- Architecture diagram (ASCII or Mermaid)
- Performance data from docqa-engine tests
- Chunking strategy comparison (fixed vs sentence vs semantic)
- Citation scoring methodology
- Hallucination detection approach
- Before/after metrics (BM25 only → hybrid retrieval)
- Deployment considerations

---

## Priority Execution Order

```
Session 1 (immediate — highest ROI):
  PARALLEL:
    Team Alpha: WS1 (cnq — bot config)     ~8 hrs
    Team Beta:  WS2 (lcx — client demo)     ~4 hrs

Session 2 (next):
  PARALLEL:
    Team Alpha: WS4 (gwn — HubSpot)        ~6 hrs
    Team Gamma: WS3 (tml — flow viz)        ~8 hrs
    Writing:    WS5 (ia3 — case study)      ~2 hrs

Session 3 (unblocked by Sessions 1-2):
    s7y: Interactive chatbot widget          ~6 hrs  (needs cnq)
    hfi: REST API + agent templates          ~8 hrs  (needs tml)
    58t: docqa REST API + auth               ~8 hrs  (needs ruy ✅)
```

## Test Targets

| Workstream | New Tests | Repo Total After |
|------------|-----------|------------------|
| WS1 (bot config) | ~20 | ~3,600 |
| WS2 (client demo) | ~15 | ~286 |
| WS3 (flow viz) | ~15 | ~186 |
| WS4 (HubSpot) | ~20 | ~3,620 |
| **Total new** | **~70** | |

## Verification Checklist
```
[ ] All new tests passing per workstream
[ ] ruff check clean on all modified files
[ ] No import errors (python -c "import module")
[ ] Beads closed for each completed workstream
[ ] bd sync + git push after each session
```
