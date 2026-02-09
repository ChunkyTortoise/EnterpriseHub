# ADR 0005: Pydantic V2 Migration

## Status

Accepted

## Context

The platform's entire data validation layer was built on Pydantic V1, which reached end-of-life status. Pydantic V2, built on a Rust core (`pydantic-core`), offers 5-50x faster validation depending on schema complexity. Given that every API request, webhook event, CRM sync payload, and bot response passes through Pydantic validation, the performance impact was significant.

Specific pain points with V1:
- Request validation contributed ~15ms per API call at P95 (measured via `PerformanceTracker`)
- Complex nested schemas (e.g., `LeadQualificationResult` with 12 nested models) took 8-12ms to validate
- V1's `orm_mode` configuration caused subtle bugs when mixing SQLAlchemy models with Pydantic schemas
- No native support for `Annotated` types, requiring verbose `Field()` declarations

The migration scope included:
- 47 Pydantic models across billing, API schemas, and service layers
- 23 API route handlers with request/response models
- 8 webhook event schemas
- 12 internal service DTOs

## Decision

Perform a full migration of all Pydantic schemas to V2, using the `model_config` pattern instead of the inner `Config` class. Key changes:

**Configuration**: Replace `class Config` with `model_config = ConfigDict(...)` at the class level. This is more explicit and enables better IDE support.

**ORM Mode**: Replace `orm_mode = True` with `from_attributes = True` in `model_config`. This clarifies intent and works more reliably with SQLAlchemy 2.0.

**Validators**: Migrate from `@validator` to `@field_validator` with explicit `mode='before'` or `mode='after'` declarations. This eliminates the ambiguity in V1's validator execution order.

**Serialization**: Replace `.dict()` with `.model_dump()` and `.json()` with `.model_dump_json()`. Add explicit `exclude_none=True` where JSON payloads should omit null fields.

**Migration Strategy**: All-at-once migration (not incremental) to avoid maintaining V1/V2 compatibility shims. The migration was performed across a single release cycle with comprehensive test coverage validating every schema.

## Consequences

### Positive
- 5x faster request validation at P95 (15ms down to ~3ms per request)
- Complex nested schema validation (e.g., `LeadQualificationResult`) reduced from 8-12ms to 1-2ms
- `from_attributes` works correctly with SQLAlchemy 2.0 relationship loading
- `@field_validator` with explicit mode eliminates validator ordering bugs
- Better error messages with structured `ValidationError` details (loc, msg, type fields)
- Native `Annotated` type support enables cleaner field declarations

### Negative
- Breaking change for any external V1 consumers of API response schemas
- All 47 models required manual migration and testing (no automated migration path for custom validators)
- `.dict()` and `.json()` calls across the entire codebase needed updating (89 call sites)
- Some V1 validator behaviors (e.g., `pre=True` with `always=True`) required non-trivial refactoring
- Team members needed to learn V2 patterns; V1 muscle memory caused initial friction
