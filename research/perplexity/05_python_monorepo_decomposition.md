# Python Monorepo Architecture & Service Decomposition 2025-2026

**Research date:** 2026-03-19
**Context:** FastAPI application with 555 service files, 86 route files, circular imports, inconsistent naming, all in one package (`ghl_real_estate_ai/`)

---

## Key Findings

1. **Modular monolith is the right intermediate step** for a codebase of this size and complexity. Jumping directly to microservices from an unstructured monolith adds distributed-systems overhead before the domain boundaries are even understood.

2. **uv workspaces** have emerged (2025-2026) as the canonical Python monorepo tool, superseding manual namespace packages and most Pants use cases for teams that don't need Bazel-level build graph control.

3. **import-linter** is the enforcement layer of choice for module boundaries — declarative contracts in a `.importlinter` file, runnable in CI, contract types cover independence, layering, and forbidden imports.

4. **Domain-Driven Design bounded contexts** map directly onto FastAPI router prefixes and Python sub-packages. Each domain gets `model/`, `service/`, `domain_api/`, and `web_api/` sub-modules.

5. **Circular imports are an architecture symptom**, not a Python problem. They reveal missing abstraction layers. The fix is dependency inversion, not `TYPE_CHECKING` hacks.

6. **Strangler fig is the safest decomposition path** — extract one well-bounded domain at a time, keep the monolith running, redirect traffic progressively. Do not extract the "most important" domain first; extract the one with the fewest cross-cutting dependencies.

---

## Modular Monolith vs Microservices Decision

### When to stay a modular monolith

- Team size < 8 engineers on the service
- Deployment frequency < daily per domain
- Shared database with complex cross-domain joins
- Domain boundaries are still being discovered
- No distinct scaling requirements per component

### When to split into microservices

A specific component warrants extraction when it has **meaningfully different** requirements in at least two of these dimensions:
- Scaling (one domain handles 100x more traffic)
- Deployment cadence (one team deploys 10x more often)
- Technology stack (ML inference needs GPU, API doesn't)
- Team ownership (separate org/contractor manages it)
- Compliance boundary (PCI, HIPAA isolation)

### The 2025-2026 consensus

Premature microservices decomposition is one of the most common sources of unnecessary engineering complexity in growing Python products. The industry has swung back toward **modular monolith first**: establish clean module boundaries in a single deployable, then extract services only when a specific operational trigger appears.

For a codebase with 555 service files and circular imports, **you cannot safely extract microservices until you first understand the domain boundaries**. The modular monolith phase is mandatory, not optional.

### Practical heuristic

| Signal | Recommendation |
|--------|---------------|
| < 10 endpoints per module | Centralized routes in main app |
| 10+ endpoints per module | Module-owned routers |
| Multiple teams on same module | Separate module package |
| Different scaling needs | Extract to microservice |
| Circular imports | Architecture problem — fix boundaries first |

---

## Domain-Driven Design for Python

### Core principle: bounded contexts

Each bounded context is a self-contained domain that owns its data model, business logic, and API contract. The catalog's "product" and the cart's "product" are **different classes** even if they share a name — they serve different purposes and evolve independently.

DDD's "Don't Repeat Yourself" is not about eliminating duplicate code; it is about avoiding **shared code with identical responsibilities**. A username-formatting function can legitimately exist in both Auth and Catalog contexts.

### Layer structure per domain

```
domains/
  {domain_name}/
    model/          # database entities, Pydantic schemas (domain-internal)
    service/        # business logic, orchestration — NO framework imports
    domain_api/     # explicit interface for cross-domain communication
    web_api/        # FastAPI routers, HTTP request/response handling
    tests/
```

The critical constraint: **service/ must not import FastAPI, Starlette, or any web framework**. Services return plain Python objects or raise standard Python exceptions. Route handlers in `web_api/` transform these into HTTP responses. This makes services independently testable and framework-agnostic.

### Cross-domain communication

Domains never import each other's internal `model/` or `service/` modules directly. All inter-domain calls go through `domain_api/`:

```python
# WRONG — breaks domain isolation
from domains.catalog.model import Product

# RIGHT — uses domain's public contract
from domains.catalog.domain_api import get_product_by_id
```

The `domain_api/` module is a facade: it exposes only what other domains are permitted to call, hiding all internal implementation.

### FastAPI integration: two approaches

1. **Multiple sub-applications** — mount separate `FastAPI()` instances under a root app. Each domain gets its own OpenAPI docs, middleware, and exception handlers. Best for teams with genuine domain autonomy.

2. **Multiple routers** — each domain defines an `APIRouter`, which the root app includes with a prefix. Unified docs. Simpler for single-team monoliths.

For a real estate AI app, routers are sufficient until team boundaries emerge.

---

## Decomposition Strategies

### Phase 1: Audit and map (before writing any code)

1. Run `pydeps ghl_real_estate_ai/ --max-bacon=3` to generate an import graph. Save the SVG as architecture documentation.
2. Run `pycycle --here` to enumerate all circular import chains.
3. Cluster the 555 service files by business capability (not by technical layer). What real-world nouns do they operate on?
4. Count how many services touch each noun. Services touching 5+ nouns are god-class candidates.

### Phase 2: Establish the target domain list

For a real estate AI + GHL application, natural bounded contexts are:

| Domain | Core Nouns | Likely Services |
|--------|-----------|----------------|
| Lead | Contact, Lead, Pipeline Stage | capture, scoring, routing, deduplication |
| Communication | Message, Email, SMS, Call | sending, templating, threading, opt-out |
| Campaign | Campaign, Sequence, Step | scheduling, enrollment, tracking |
| Property | Listing, Valuation, MLS Record | search, matching, comparison |
| Appointment | Slot, Booking, Calendar | scheduling, reminders, no-show handling |
| Integration | Webhook, GHL Event, API Key | inbound routing, event normalization |
| AI | Prompt, Completion, Tool Call | LLM orchestration, response parsing |
| Auth | User, Role, Tenant | authentication, authorization, scoping |

### Phase 3: God-class decomposition

For a service file that is 2,715 lines or handles 5+ responsibilities:

1. **Identify distinct responsibility clusters** — group methods by the data they primarily operate on. Methods that never call each other are likely in separate domains.
2. **Extract the simplest responsibility first** — the one with fewest inbound dependencies.
3. **Leave a shim** — the original class delegates to the new class for backward compatibility during the transition.
4. **Test the shim** — write a characterization test that proves behavior is unchanged.
5. **Migrate callers** — update imports one module at a time, running tests after each.
6. **Delete the shim** — only when callers are fully migrated.

Repeat for each responsibility cluster. Never try to decompose the whole god class in one commit.

### Phase 4: Enforce boundaries

Once domains are identified, add `import-linter` contracts (see Tools section) to prevent regression. The contract enforcement is the structural foundation that makes further refactoring safe.

---

## Tools and Tooling

### uv workspaces (primary monorepo tool, 2025-2026)

uv workspaces are inspired by Rust Cargo workspaces. The entire monorepo shares one lockfile (`uv.lock`), but each package has its own `pyproject.toml`.

Root `pyproject.toml`:
```toml
[tool.uv.workspace]
members = ["packages/*"]
```

Member cross-dependency:
```toml
# packages/core/pyproject.toml
[tool.uv.sources]
shared-schemas = { workspace = true }
```

Key behaviors:
- `uv lock` operates on the entire workspace
- `uv run --package lead-service pytest` runs tests for one member only
- Dependencies between members are editable by default
- A single `requires-python` applies across all members (intersection of constraints)

### import-linter (boundary enforcement)

Install: `pip install import-linter`

`.importlinter` configuration:
```ini
[importlinter]
root_package = ghl_real_estate_ai

[importlinter:contract:1]
name = Domains are independent
type = independence
modules =
    ghl_real_estate_ai.domains.lead
    ghl_real_estate_ai.domains.communication
    ghl_real_estate_ai.domains.campaign
    ghl_real_estate_ai.domains.property

[importlinter:contract:2]
name = Services do not import web layer
type = forbidden
source_modules = ghl_real_estate_ai.domains.*.service
forbidden_modules = fastapi | starlette

[importlinter:contract:3]
name = Layer hierarchy
type = layers
layers =
    ghl_real_estate_ai.domains.*.web_api
    ghl_real_estate_ai.domains.*.service
    ghl_real_estate_ai.domains.*.model
```

Run `lint-imports` in CI as a required check. Contract violations show exact file and line number.

### pydeps (import graph visualization)

```bash
pip install pydeps
pydeps ghl_real_estate_ai/ --max-bacon=3 --noshow -o import_graph.svg
```

Generates a visual dependency graph. Clusters of tightly interconnected nodes indicate undiscovered domain boundaries or god classes.

### pycycle (circular import detection)

```bash
pip install pycycle
pycycle --here
```

Lists all circular import chains with line numbers. Prioritize breaking chains that cross what will become domain boundaries.

### tach (import boundary enforcement, alternative to import-linter)

```bash
pip install tach
tach init  # auto-detects modules
tach check  # validates boundaries
```

tach can auto-generate boundary configuration from the existing import graph, which is useful when starting from a codebase with no declared boundaries.

### Pants (for large-scale monorepos with build graph needs)

Pants is appropriate when the repo contains multiple languages, needs incremental builds per file (not per package), or has Bazel-like CI requirements. For a pure Python FastAPI monorepo, uv workspaces provide 80% of Pants' value with 10% of the setup cost.

---

## Strangler Fig Pattern

### What it is

The strangler fig is a tree that grows around a host tree, eventually replacing it. Applied to software: new functionality is built as a separate, clean implementation while the old code continues to run. Traffic is progressively rerouted from old to new. The old code is retired only when it carries no traffic.

### Three-phase process

**1. Transform** — build the new domain module in parallel with the legacy code. Do not modify the legacy module during this phase.

**2. Coexist** — route a percentage of traffic to the new module using a feature flag or API gateway routing rule. Both implementations run simultaneously. Observe for correctness.

**3. Eliminate** — once new module handles 100% of traffic successfully, delete the legacy code.

### Implementation in FastAPI

```python
# Strangler facade router
from fastapi import APIRouter, Request
import feature_flags

router = APIRouter()

@router.post("/leads/capture")
async def capture_lead(request: Request, payload: LeadPayload):
    if feature_flags.is_enabled("new_lead_domain", request):
        return await new_lead_service.capture(payload)
    return await legacy_lead_handler.capture(payload)
```

The facade lives at the route layer. Once the flag reaches 100%, delete the legacy branch and the flag.

### What to extract first (critical guidance)

The instinct to extract the "most important" domain first is wrong. Start with the domain that has:
- Clear boundaries (few callers from other domains)
- Low database coupling (ideally its own tables)
- Low business risk if something goes wrong
- High test coverage already

In a real estate AI app, **Integration** (webhook ingestion, GHL event normalization) or **Auth** is often the safest first extraction because it is a well-defined input boundary with no downstream callers.

### Database decomposition

Application logic decomposition is straightforward. The database is where migrations stall. Patterns:
- **Separate schemas first** — move domain tables to their own PostgreSQL schema (`lead.*`, `communication.*`) before touching application code.
- **Shared database, separate schemas** — acceptable long-term for modular monolith; only split physical databases when a domain needs different consistency or scaling guarantees.
- **Change Data Capture (CDC)** — use tools like Debezium or PostgreSQL logical replication to keep legacy and new tables in sync during coexistence phase.

---

## Circular Dependency Resolution

### Root causes

Circular imports in Python FastAPI apps almost always trace to one of three architectural mistakes:

1. **Missing abstraction layer** — `service_a` needs something from `service_b`, and `service_b` needs something from `service_a`. The shared concept belongs in a third module that both import.

2. **Mixing layers** — route imports service, service imports schema from route module, schema imports from model, model imports from service.

3. **God service** — one service does so much that everything else depends on it, and it in turn depends on everything else.

### Resolution strategies

**Strategy 1: Extract shared types**
```python
# BEFORE: circular
# service_a.py imports service_b.ClientRecord
# service_b.py imports service_a.LeadStatus

# AFTER: extract to shared types module
# shared/types.py contains ClientRecord and LeadStatus
# both services import from shared/types.py
```

**Strategy 2: Dependency inversion**
```python
# BEFORE: service imports concrete implementation
from infrastructure.email_client import EmailClient

# AFTER: service depends on abstract interface
from domains.communication.domain_api import MessageSender  # Protocol/ABC
# Concrete EmailClient injected at startup via dependency injection
```

**Strategy 3: Late imports for unavoidable cycles**
Only use `TYPE_CHECKING` guards or function-level imports as a last resort. They mask architecture problems. If you need them, the code needs structural refactoring, not import tricks.

**Step-by-step process:**
1. Run `pycycle --here` to list all circular chains.
2. For each chain, identify the shared concept that both modules need.
3. Extract that concept to a `shared/` or `common/` module that has no dependencies on either module.
4. Replace both modules' direct cross-imports with imports from the shared module.
5. Run `lint-imports` to confirm the cycle is broken.
6. Add an import-linter `independence` contract to prevent re-introduction.

---

## Recommended Domain Boundaries for Real Estate AI App

Given 555 service files, 86 route files, and three conflicting "client" services, the following domain structure resolves the naming conflicts and establishes enforceable boundaries:

```
ghl_real_estate_ai/
  domains/
    lead/               # Contact acquisition, scoring, deduplication, pipeline placement
    communication/      # Outbound messages (SMS, email, voice), threading, opt-out
    campaign/           # Sequence enrollment, step scheduling, A/B logic
    property/           # MLS data, listing search, valuation, matching
    appointment/        # Calendar slots, booking, reminders, no-show handling
    integration/        # GHL webhook ingestion, event normalization, outbound API calls
    ai/                 # LLM prompt management, tool call dispatch, response parsing
    auth/               # User accounts, tenants, API keys, RBAC
  shared/
    types/              # Cross-domain value objects (PhoneNumber, Address, Money)
    events/             # Internal event bus schemas
    exceptions/         # Base exception classes
  infrastructure/
    db/                 # SQLAlchemy engine, session factory, base model
    redis/              # Cache client, rate limiter
    http/               # Outbound HTTP client wrappers
  api/
    v1/                 # Root FastAPI app, mounts all domain routers
    middleware/         # Auth middleware, logging, tracing
    dependencies/       # Common FastAPI Depends() factories
```

### Resolving the three "client" service conflict

If three files are all named something like `client_service.py`, audit what data they operate on:
- Client as a **GHL Contact** → lives in `lead/service/`
- Client as an **outbound HTTP caller** → lives in `infrastructure/http/`
- Client as a **business customer/tenant** → lives in `auth/service/`

Rename with domain prefix: `lead_contact_service.py`, `ghl_http_client.py`, `tenant_service.py`. Unambiguous names make cross-domain imports explicit about what is crossing a boundary.

### Decomposition order (safest to highest risk)

1. `auth/` — clean input boundary, well-understood, low coupling
2. `integration/` — webhook ingestion has clear in/out contract
3. `ai/` — LLM orchestration is a leaf node (nothing calls into it)
4. `property/` — mostly read-only MLS data, low write coupling
5. `appointment/` — calendar logic is self-contained
6. `lead/` — core domain, high coupling, extract last
7. `communication/` — shared by most domains, extract after lead
8. `campaign/` — depends on lead and communication, extract last

---

## Recommendations for EnterpriseHub

EnterpriseHub (`FastAPI/Streamlit/PostgreSQL/Redis/Claude`, 1553+ tests) is a different codebase from the GHL real estate bot, but the same architectural principles apply if it shares the single-package pattern.

1. **Do not restructure during feature development.** Decomposition is a dedicated sprint, not a background task. Mixed refactor + feature commits destroy test confidence.

2. **Start with tooling, not code movement.** Add `pydeps`, `pycycle`, and `import-linter` to the dev dependencies this week. Generate the import graph before touching anything. The graph tells you where the real boundaries are, not where you think they are.

3. **Write characterization tests before refactoring.** For any service file with < 80% coverage, add integration tests that capture current behavior (even if that behavior is wrong). These tests are the safety net during structural changes.

4. **Target the modular monolith structure, not microservices.** With a 1553-test suite and a single PostgreSQL database, extracting microservices adds operational overhead with no benefit. A clean domain package structure with import-linter contracts gives 90% of microservices' architectural benefits (team autonomy, clear boundaries, testability) with none of the distributed-systems cost (network latency, eventual consistency, separate deployments).

5. **uv workspaces are optional for now.** If EnterpriseHub remains a single deployed application, uv workspaces add complexity without benefit. Reserve them for when a domain genuinely needs a separate deployment or has conflicting dependency requirements.

6. **Enforce the strangler fig discipline.** Any service file > 500 lines is a god class. Extract one responsibility per PR. Each PR must include: (a) the extracted class, (b) a shim delegating to it, (c) tests proving behavior is unchanged, (d) updated import-linter contract.

---

## Sources

- [Modular Monoliths: The Architecture Pattern We Don't Talk Enough About](https://backendengineeringadventures.substack.com/p/modular-monoliths-the-architecture)
- [Architectural patterns for modular monoliths that enable fast flow](https://microservices.io/post/architecture/2024/09/09/modular-monolith-patterns-for-fast-flow.html)
- [Domain-driven design with Python and FastAPI - ActiDoo](https://www.actidoo.com/en/blog/python-fastapi-domain-driven-design)
- [Implementing Domain-Driven Design with FastAPI - Delivus/Medium](https://medium.com/delivus/implementing-domain-driven-design-with-fastapi-6aed788779af)
- [FastAPI Application Architecture with Domain-Driven Design - PySquad](https://pysquad.com/blogs/fastapi-application-architecture-with-domain-drive)
- [uv Workspaces - Astral official docs](https://docs.astral.sh/uv/concepts/projects/workspaces/)
- [Python Workspaces (Monorepos) - Tomas Repcik](https://tomasrepcik.dev/blog/2025/2025-10-26-python-workspaces/)
- [Building a Python Monorepo with UV - Medium (Feb 2026)](https://medium.com/@naorcho/building-a-python-monorepo-with-uv-the-modern-way-to-manage-multi-package-projects-4cbcc56df1b4)
- [FOSDEM 2026 - Modern Python monorepo with uv, workspaces, prek and shared libraries](https://fosdem.org/2026/schedule/event/WE7NHM-modern-python-monorepo-apache-airflow/)
- [Enforce import rules using the Python import linter](https://921kiyo.com/python-import-linter/)
- [Strangler Fig Pattern - AWS Prescriptive Guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-decomposing-monoliths/strangler-fig.html)
- [How to Handle Strangler Fig Migration Pattern - OneUptime](https://oneuptime.com/blog/post/2026-01-24-strangler-fig-migration-pattern/view)
- [Practical Monolith Decomposition & the Strangler-Fig Pattern - Medium](https://medium.com/@stephen.biston/practical-monolith-decomposition-the-strangler-fig-pattern-1aa49988072f)
- [GitHub - pycycle: Tool for pinpointing circular imports in Python](https://github.com/bndr/pycycle)
- [Circular Imports in Python: The Architecture Killer - DEV Community](https://dev.to/vivekjami/circular-imports-in-python-the-architecture-killer-that-breaks-production-539j)
- [GitHub - zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [FastAPI Project Structure: Production Architecture Guide (2026)](https://www.zestminds.com/blog/fastapi-project-structure/)
- [Monolith or Microservices: Architecture Choices for Python Developers - OpsMatters](https://opsmatters.com/posts/monolith-or-microservices-architecture-choices-python-developers)
- [GitHub - YoraiLevi/modular-monolith-fastapi](https://github.com/YoraiLevi/modular-monolith-fastapi)
- [GitHub - arctikant/fastapi-modular-monolith-starter-kit](https://github.com/arctikant/fastapi-modular-monolith-starter-kit)
