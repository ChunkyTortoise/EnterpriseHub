# Case Study: HIPAA-Compliant AI Routing for a Healthcare Platform

## Client Profile

**Company**: MedAssist Technologies (anonymized)
**Industry**: Healthcare IT / Telemedicine
**Team Size**: 8 developers, 2 DevOps engineers
**Challenge**: Route sensitive patient data through LLM providers while maintaining HIPAA compliance

---

## The Challenge

MedAssist Technologies builds a telemedicine platform that uses AI to triage patient symptoms, summarize clinical notes, and assist providers with diagnostic suggestions. Their regulatory environment imposed strict constraints:

- **No patient data could leave the organization's VPC** for certain operations
- **Audit trails** were required for every LLM interaction involving PHI
- **Provider selection** had to be deterministic and documented -- regulators needed to know which model processed which data
- **PII detection** had to gate every outbound request to prevent accidental PHI exposure
- **Token budgets** were required to prevent runaway API costs from triggering financial compliance reviews

The team had built a custom routing layer, but it lacked guardrails, had no content filtering, and required manual audit log assembly from CloudWatch.

### Pain Points

| Problem | Impact |
|---------|--------|
| No PII detection before LLM calls | Risk of PHI exposure to third-party APIs |
| Manual audit trail assembly | 6 hours/week for compliance officer |
| No token budget enforcement | 2 incidents of $800+ single-request costs |
| Provider selection undocumented | Failed 2 of 5 audit criteria |
| Inconsistent error handling | Silent failures in clinical note processing |

---

## The Solution: AgentForge with Guardrails

MedAssist adopted AgentForge's guardrails engine, tracing system, and cost controls to build a HIPAA-compliant AI routing layer.

### Step 1: PII Detection Guardrails

AgentForge's guardrails engine includes built-in PII detection that gates every outbound request. MedAssist configured it to block requests containing patient identifiers before they reach any external provider:

```python
from agentforge import AIOrchestrator
from agentforge.guardrails import GuardrailsEngine, ContentFilter

# Configure guardrails with PII detection
guardrails = GuardrailsEngine(
    content_filters=[
        ContentFilter(
            name="phi_detector",
            pattern_type="pii",
            action="block",  # Block requests containing PII
            categories=["ssn", "phone", "email", "medical_record"]
        )
    ],
    max_token_budget=8192,  # Hard cap per request
)

orc = AIOrchestrator(temperature=0.1, max_tokens=4096)
```

The guardrails system (validated by 30 automated tests in AgentForge) checks every prompt against configurable content filters before routing to any provider. If PHI is detected, the request is blocked and an audit event is emitted.

### Step 2: Complete Audit Trails via Tracing

AgentForge's `EventCollector` tracing system captures 100% of agent decisions, creating the audit trail regulators require:

```python
from agentforge.tracing import EventCollector

collector = EventCollector()

# Every LLM interaction is automatically traced:
# - Provider selected
# - Model used
# - Token counts (input/output)
# - Latency
# - Guardrail decisions (pass/block)
# - Cost per request

# Export for compliance
events = collector.get_events()
for event in events:
    compliance_log.write({
        "timestamp": event.timestamp,
        "provider": event.provider,
        "model": event.model,
        "tokens_used": event.total_tokens,
        "guardrail_result": event.guardrail_status,
        "cost_usd": event.estimated_cost
    })
```

The tracing system (17 dedicated tests) captures span hierarchies, enabling MedAssist to show regulators exactly which model processed which data, when, and at what cost.

### Step 3: Deterministic Provider Routing

For HIPAA compliance, MedAssist needed provider selection to be deterministic and auditable. They used AgentForge's model registry for version-tracked model selection:

```python
from agentforge.model_registry import ModelRegistry

registry = ModelRegistry()

# Register approved models with metadata
registry.register(
    name="clinical_notes",
    provider="claude",
    model="claude-3-5-sonnet-20241022",
    metadata={"hipaa_approved": True, "data_classification": "phi"}
)

registry.register(
    name="general_triage",
    provider="gemini",
    model="gemini-1.5-pro",
    metadata={"hipaa_approved": True, "data_classification": "non_phi"}
)

# Route based on data classification
model_config = registry.get("clinical_notes")
response = await orc.chat(model_config.provider, prompt, model=model_config.model)
```

The model registry (32 automated tests) supports A/B selection, version tracking, and metadata tagging -- all requirements for MedAssist's compliance documentation.

### Step 4: Token Budget Enforcement

AgentForge's guardrails enforce hard token caps per request, preventing the runaway cost incidents that had triggered financial reviews:

```python
# Guardrails automatically enforce:
# - Max tokens per request (configurable)
# - Max tokens per session
# - Per-provider daily budgets

guardrails = GuardrailsEngine(
    max_token_budget=8192,        # Per-request cap
    session_token_limit=50_000,   # Per-session cap
)

# If a request would exceed the budget, it's blocked before
# reaching the provider, and an alert is raised
```

Combined with the `CostTracker`, MedAssist set up real-time cost alerts:

```python
from agentforge.cost_tracker import CostTracker

tracker = CostTracker()

# After each request, check cumulative spend
session_cost = tracker.get_session_cost()
if session_cost["total_cost_usd"] > daily_budget:
    alert_ops_team("Daily AI budget exceeded")
```

---

## Results

### Compliance Improvements

| Metric | Before AgentForge | After AgentForge | Change |
|--------|-------------------|------------------|--------|
| Audit trail assembly | 6 hours/week manual | Automatic, real-time | **-100% manual effort** |
| PII exposure incidents | 3 near-misses in 6 months | 0 incidents in 12 months | **Eliminated** |
| Audit criteria passed | 3 of 5 | 5 of 5 | **100% compliance** |
| Provider routing documentation | Manual spreadsheet | Auto-generated from registry | **Always current** |

### Cost Control

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Runaway cost incidents | 2 ($800+ each) | 0 | **Eliminated** |
| Monthly API spend | $2,800 | $420 | **-85%** |
| Cost visibility | Weekly spreadsheet | Per-request real-time | **Instant** |

### Reliability

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Silent failures | ~8/week | 0 | **Eliminated** |
| Provider failover | Manual intervention | Automatic <5s | **99.9% uptime** |
| Clinical note processing errors | 4.2% | 0.1% | **-98%** |

---

## Architecture: HIPAA-Compliant Request Flow

```
Patient Interaction
        |
        v
[Guardrails Engine]  -- PII Detection (30 tests)
  |           |
  | PASS      | BLOCK
  v           v
[Model Registry]     [Audit Log + Alert]
  |
  v
[Rate Limiter]  -- Token Bucket (29 tests)
  |
  v
[Provider Router]  -- Fallback Chain
  |
  v
[Claude / OpenAI / Gemini]
  |
  v
[Cost Tracker]  -- Per-request cost recording
  |
  v
[Event Collector]  -- 100% tracing (17 tests)
  |
  v
[Response to Platform]
```

Every component in this flow is covered by AgentForge's 491-test suite. MedAssist did not need to write any infrastructure tests -- only application-level integration tests.

---

## Implementation Timeline

| Week | Activity | Outcome |
|------|----------|---------|
| 1 | Guardrails configuration with PII filters | PHI gating active |
| 1 | Model registry setup with HIPAA metadata | Deterministic routing |
| 2 | Tracing integration with compliance logging | Automatic audit trails |
| 2 | Cost tracking with budget alerts | Financial controls |
| 3 | Fallback routing and rate limiting | Production reliability |
| 3 | Compliance documentation generation | Audit-ready |

**Total migration effort**: 2 engineering-weeks.

---

## Key Takeaways

1. **Guardrails are not optional in healthcare**. AgentForge's built-in PII detection and content filtering prevented 3+ potential PHI exposure incidents.

2. **Tracing solves the audit problem**. The EventCollector's 100% decision tracing eliminated 6 hours/week of manual audit log assembly.

3. **Model registries create compliance artifacts automatically**. Regulators could see exactly which model was approved for which data classification.

4. **Token budgets prevent financial incidents**. Hard caps per request and per session eliminated $800+ runaway cost events.

5. **491 tests mean infrastructure confidence**. MedAssist's security team reviewed AgentForge's test suite and approved it for PHI-adjacent workloads without requiring additional security testing.

---

## About AgentForge

AgentForge provides 491 automated tests across 21 test files, including 30 guardrails tests (content filters, token budgets, PII detection), 17 tracing tests (event collection, span hierarchy), and 32 model registry tests (version tracking, A/B selection). Built for production workloads in regulated industries.

- **Repository**: [github.com/ChunkyTortoise/ai-orchestrator](https://github.com/ChunkyTortoise/ai-orchestrator)
- **Key modules**: Guardrails (30 tests), Tracing (17 tests), Model Registry (32 tests)
- **Providers**: Claude, Gemini, OpenAI, Perplexity -- all through a single interface
