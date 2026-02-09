# ADR 0005: Pydantic V2 Strict Validation

## Status

Accepted

## Context

The platform exchanges data across multiple boundaries: CRM webhooks from GoHighLevel, LLM responses from Claude/Gemini/Perplexity, PostgreSQL database models, and FastAPI API endpoints. Historically, loose dict-based data passing caused subtle bugs — missing fields, wrong types, and silent data loss — that only surfaced in production.

Specific pain points:
- Dict-based payloads allowed typos in field names to pass silently (e.g., `lead_scroe` instead of `lead_score`)
- LLM response parsing relied on manual key checking, missing fields caused `KeyError` in production
- CRM webhook payloads varied between event types with no compile-time distinction
- Bot response types (Lead, Buyer, Seller) were differentiated by string checks instead of type-safe unions
- Request validation contributed ~15ms per API call at P95 under Pydantic V1 (measured via `PerformanceTracker`)

## Decision

Adopt Pydantic V2 for all data models with strict validation enforced at every system boundary. Key design decisions:

**Strict Validation at Boundaries**: All API request/response schemas, CRM webhook payloads, LLM parsed outputs, and database transfer objects use Pydantic `BaseModel` with `model_config = ConfigDict(strict=True)` where appropriate. Data is validated on entry and exit, never passed as raw dicts between services.

**Structured Error Responses**: All validation errors follow a standard JSON format with `error`, `message`, `field`, and `code` keys. This enables consistent error handling across API consumers and bot conversation flows.

**Discriminated Unions**: Polymorphic models use Pydantic's `Discriminator` and `Tag` pattern to eliminate `isinstance` chains. For example, bot response types (LeadBotResponse, BuyerBotResponse, SellerBotResponse) are unified under a discriminated union keyed on `bot_type`, enabling type-safe dispatch without runtime type checking.

**ORM Integration**: Replace V1's `orm_mode = True` with `from_attributes = True` in `model_config`. This works reliably with SQLAlchemy 2.0 relationship loading and prevents the subtle bugs caused by V1's attribute access patterns.

**Validators**: Migrate from `@validator` to `@field_validator` with explicit `mode='before'` or `mode='after'` declarations. This eliminates ambiguity in validator execution order.

**Serialization**: Replace `.dict()` with `.model_dump()` and `.json()` with `.model_dump_json()`. Add explicit `exclude_none=True` where JSON payloads should omit null fields.

## Consequences

### Positive
- Type errors caught at system boundaries before propagating into business logic
- Self-documenting API contracts via OpenAPI schema generation from Pydantic models
- 10x faster validation vs Pydantic V1 (Rust-based `pydantic-core`): P95 from 15ms to ~1.5ms
- Discriminated unions eliminate `isinstance` chains for bot response routing
- Structured error format enables consistent client-side error handling across all endpoints
- `@field_validator` with explicit mode eliminates validator ordering bugs

### Negative
- Migration effort from dict-based code required updating 47 models and 89 serialization call sites
- Some third-party integrations (GHL webhooks, Stripe events) need manual adapter models for loose payloads
- Strict mode rejects previously-accepted loose inputs (e.g., string "123" no longer auto-coerced to int)
- Discriminated union pattern requires all polymorphic models to carry a discriminator field
- Team members needed to learn V2 patterns; V1 muscle memory caused initial friction
