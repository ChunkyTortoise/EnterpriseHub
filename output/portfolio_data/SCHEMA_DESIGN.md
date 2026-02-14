# Canonical Portfolio Data Schemas

**Version:** 1.0  
**Date:** 2026-02-11  
**Purpose:** Single source of truth for portfolio data across all channels (Upwork, GitHub, portfolio website, proposals)

---

## Overview

This document defines the canonical YAML schemas for the portfolio operating system. These schemas serve as the foundation for:

1. **Service Catalog** - 31 services (S01-S26 + QW1-QW7) with pricing, deliverables, and proof links
2. **Certification Inventory** - 19 certifications with verification and service mapping
3. **Proof Assets** - Screenshots, demos, videos, benchmarks, and testimonials
4. **Case Studies** - Problem→Solution→Outcome narratives with metrics

All schemas are designed to be:
- **Cross-referenced** via ID-based linking
- **Validatable** with clear required/optional field rules
- **Channel-agnostic** for use across Upwork, GitHub, portfolio site, and proposals
- **Extensible** for future additions

---

## Schema 1: services.yaml

### Purpose

Defines the complete service catalog with pricing, deliverables, buyer personas, and proof links. This is the primary schema that drives all portfolio content.

### Field Definitions

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `id` | string | Yes | Unique service identifier | Pattern: `^S(0[1-9]\|1[0-9]\|2[0-6])$` or `^QW[1-7]$` |
| `name` | string | Yes | Service display name | Max 100 chars |
| `category` | enum | Yes | Service category | `Strategy`, `Agentic AI`, `Data/BI`, `Marketing`, `Infra/MLOps`, `Ops/Governance`, `Quick-Win` |
| `buyer_persona` | string | Yes | Target buyer description | Max 200 chars |
| `core_problem` | string | Yes | Problem this service solves | Max 500 chars |
| `deliverables` | list | Yes | List of deliverable items | 1-10 items, max 100 chars each |
| `timeline` | string | Yes | Typical delivery timeline | Max 100 chars |
| `price_min` | integer | Yes | Minimum project price | USD, >= 0 |
| `price_max` | integer | Yes | Maximum project price | USD, >= price_min |
| `hourly_equivalent_min` | integer | Yes | Min hourly rate equivalent | USD, >= 0 |
| `hourly_equivalent_max` | integer | Yes | Max hourly rate equivalent | USD, >= hourly_equivalent_min |
| `repos` | list | Yes | Proof-of-work repository links | 1-5 items, valid URLs |
| `case_studies` | list | No | Related case study IDs | References `case_studies.yaml` IDs |
| `certifications` | list | No | Required certification IDs | References `certifications.yaml` IDs |
| `status` | enum | Yes | Service readiness status | `ready`, `needs-proof`, `needs-rewrite` |
| `priority` | enum | Yes | Development priority | `P1`, `P2`, `P3` |
| `description` | string | No | Extended description | Max 1000 chars |
| `tags` | list | No | Searchable tags | 1-10 items, max 50 chars each |

### Example Entry

```yaml
- id: S04
  name: Multi-Agent Workflows
  category: Agentic AI
  buyer_persona: "CTOs and engineering leads building AI agent systems"
  core_problem: "Manual coordination between AI agents leads to errors, race conditions, and poor user experience"
  deliverables:
    - "Agent architecture design document"
    - "Multi-agent orchestration framework"
    - "Handoff logic and state management"
    - "Monitoring and observability setup"
    - "Documentation and deployment guide"
  timeline: "2-4 weeks"
  price_min: 5000
  price_max: 15000
  hourly_equivalent_min: 90
  hourly_equivalent_max: 150
  repos:
    - "https://github.com/ChunkyTortoise/EnterpriseHub"
    - "https://github.com/ChunkyTortoise/Revenue-Sprint"
  case_studies:
    - "CS001"
    - "CS002"
  certifications:
    - "C003"
    - "C004"
  status: ready
  priority: P1
  description: "Design and implement multi-agent AI systems with proper handoff orchestration, context management, and monitoring"
  tags:
    - "agents"
    - "orchestration"
    - "automation"
```

### Validation Rules

1. **ID Format**: Must match `^S(0[1-9]|1[0-9]|2[0-6])$` for core services or `^QW[1-7]$` for quick-wins
2. **Price Consistency**: `price_max` must be >= `price_min`
3. **Hourly Consistency**: `hourly_equivalent_max` must be >= `hourly_equivalent_min`
4. **Repo Count**: Must have at least 1 repository link
5. **Deliverables**: Must have 1-10 deliverable items
6. **Case Study References**: All IDs must exist in `case_studies.yaml`
7. **Certification References**: All IDs must exist in `certifications.yaml`

---

## Schema 2: certifications.yaml

### Purpose

Tracks all certifications with verification URLs, hours, and service mappings. Enables automatic certification badges on repos and service pages.

### Field Definitions

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `id` | string | Yes | Unique certification identifier | Pattern: `^C[0-9]{3}$` |
| `name` | string | Yes | Certification name | Max 150 chars |
| `provider` | string | Yes | Certification provider | Max 100 chars |
| `status` | enum | Yes | Completion status | `completed`, `in-progress` |
| `hours` | integer | Yes | Total hours invested | >= 0 |
| `year` | integer | Yes | Year started/completed | >= 2020, <= current year + 1 |
| `verification_url` | string | No | Credential verification URL | Valid URL if provided |
| `service_ids` | list | No | Related service IDs | References `services.yaml` IDs |
| `repo_ids` | list | No | Repository applications | 1-10 repo identifiers |
| `positioning_snippet` | string | Yes | 1-sentence sales copy | Max 200 chars |
| `badge_url` | string | No | Badge image URL | Valid URL if provided |
| `category` | enum | No | Certification category | `AI/ML`, `GenAI`, `Data/BI`, `Marketing`, `Engineering` |

### Example Entry

```yaml
- id: C003
  name: IBM RAG and Agentic AI Professional Certificate
  provider: IBM
  status: in-progress
  hours: 80
  year: 2026
  verification_url: "https://www.credly.com/badges/example"
  service_ids:
    - "S03"
    - "S04"
    - "S24"
  repo_ids:
    - "docqa-engine"
    - "EnterpriseHub"
  positioning_snippet: "Expertise in building production RAG systems with hybrid retrieval and agentic workflows"
  badge_url: "https://img.shields.io/badge/IBM-RAG-blue"
  category: GenAI
```

### Validation Rules

1. **ID Format**: Must match `^C[0-9]{3}$`
2. **Hours**: Must be >= 0
3. **Year**: Must be between 2020 and current year + 1
4. **Service References**: All IDs must exist in `services.yaml`
5. **Positioning Snippet**: Must be <= 200 characters
6. **Verification URL**: Must be valid URL if provided
7. **Badge URL**: Must be valid URL if provided

---

## Schema 3: proof_assets.yaml

### Purpose

Catalogs all visual and demonstrative proof assets (screenshots, videos, GIFs, benchmarks, testimonials) with service mappings and verification dates.

### Field Definitions

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `id` | string | Yes | Unique asset identifier | Pattern: `^PA[0-9]{4}$` |
| `asset_type` | enum | Yes | Type of proof asset | `screenshot`, `gif`, `video`, `architecture`, `benchmark`, `testimonial` |
| `service_ids` | list | Yes | Related service IDs | 1-5 items, references `services.yaml` |
| `repo` | string | Yes | Repository identifier | Max 100 chars |
| `path_or_url` | string | Yes | Local path or remote URL | Valid path or URL |
| `business_claim_supported` | string | Yes | Claim this asset proves | Max 300 chars |
| `last_verified_date` | string | Yes | Last verification date | ISO 8601 format (YYYY-MM-DD) |
| `title` | string | No | Asset display title | Max 150 chars |
| `description` | string | No | Extended description | Max 500 chars |
| `thumbnail_url` | string | No | Thumbnail image URL | Valid URL if provided |
| `duration_seconds` | integer | No | Duration for video/GIF | >= 0, required for video/gif |
| `file_size_bytes` | integer | No | File size for local assets | >= 0 |
| `alt_text` | string | No | Accessibility text | Max 200 chars |

### Example Entry

```yaml
- id: PA0001
  asset_type: screenshot
  service_ids:
    - "S04"
    - "S08"
  repo: "EnterpriseHub"
  path_or_url: "assets/screenshots/platform-overview.png"
  business_claim_supported: "Demonstrates multi-agent bot dashboard with real-time metrics and handoff visualization"
  last_verified_date: "2026-02-10"
  title: "EnterpriseHub Platform Overview"
  description: "Main dashboard showing Lead, Seller, and Buyer bot performance metrics"
  thumbnail_url: "https://example.com/thumb.png"
  file_size_bytes: 245678
  alt_text: "Screenshot of EnterpriseHub dashboard with three bot panels and performance charts"
```

### Validation Rules

1. **ID Format**: Must match `^PA[0-9]{4}$`
2. **Service References**: All IDs must exist in `services.yaml`
3. **Path/URL**: Must be valid local path or remote URL
4. **Date Format**: Must be ISO 8601 (YYYY-MM-DD)
5. **Duration**: Required for `video` and `gif` types, must be >= 0
6. **File Size**: Required for local assets, must be >= 0
7. **Business Claim**: Must be <= 300 characters

---

## Schema 4: case_studies.yaml

### Purpose

Documents detailed problem→solution→outcome narratives with quantitative metrics, technical stack, and call-to-action links.

### Field Definitions

| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| `id` | string | Yes | Unique case study identifier | Pattern: `^CS[0-9]{3}$` |
| `title` | string | Yes | Case study title | Max 150 chars |
| `service_ids` | list | Yes | Related service IDs | 1-5 items, references `services.yaml` |
| `industry` | string | Yes | Client industry | Max 100 chars |
| `problem` | string | Yes | Problem statement | Max 1000 chars |
| `constraints` | list | No | Project constraints | 1-5 items, max 200 chars each |
| `solution` | string | Yes | Solution description | Max 2000 chars |
| `stack` | list | Yes | Technology stack | 1-15 items, max 50 chars each |
| `outcomes` | object | Yes | Quantitative outcomes | See structure below |
| `artifacts` | list | No | Deliverable artifacts | 1-10 items, see structure below |
| `cta` | object | Yes | Call-to-action | See structure below |
| `client_type` | enum | No | Client type | `enterprise`, `startup`, `agency`, `freelance` |
| `project_duration` | string | No | Project duration | Max 50 chars |
| `team_size` | integer | No | Team size | >= 1 |
| `published_date` | string | No | Publication date | ISO 8601 format (YYYY-MM-DD) |

### Nested Structures

#### outcomes object

```yaml
outcomes:
  metric_1: "value with unit"
  metric_2: "value with unit"
  # Example:
  lead_response_time: "reduced from 45min to 2min (95% improvement)"
  cost_savings: "$240,000 annual savings"
  conversion_rate: "increased from 12% to 28%"
```

#### artifacts list items

```yaml
artifacts:
  - type: "code" | "document" | "demo" | "diagram"
    name: "Artifact name"
    url: "https://example.com/artifact"
    description: "Brief description"
```

#### cta object

```yaml
cta:
  text: "Book a consultation"
  url: "https://calendly.com/example"
  type: "booking" | "contact" | "demo"
```

### Example Entry

```yaml
- id: CS001
  title: "Real Estate Lead Qualification Automation"
  service_ids:
    - "S04"
    - "S06"
    - "S08"
  industry: "Real Estate"
  problem: |
    A real estate brokerage was losing 40% of leads due to slow response times.
    Manual qualification took 45+ minutes per lead, and agents struggled to
    prioritize high-value prospects.
  constraints:
    - "Must integrate with existing GoHighLevel CRM"
    - "5-minute response SLA requirement"
    - "Support English and Spanish leads"
  solution: |
    Built a multi-agent AI system with three specialized bots (Lead, Seller, Buyer)
    using a Q0-Q4 qualification framework. Implemented 3-tier Redis caching for
    89% cost reduction and integrated with GoHighLevel for real-time CRM sync.
    Added Streamlit BI dashboard for visibility into lead flow and bot performance.
  stack:
    - "FastAPI"
    - "Claude API"
    - "PostgreSQL"
    - "Redis"
    - "Streamlit"
    - "GoHighLevel"
  outcomes:
    lead_response_time: "reduced from 45min to 2min (95% improvement)"
    cost_savings: "$240,000 annual savings"
    conversion_rate: "increased from 12% to 28%"
    cache_hit_rate: "87% for repeated queries"
    token_cost_reduction: "89% via 3-tier caching"
  artifacts:
    - type: demo
      name: "Live Dashboard"
      url: "https://ct-enterprise-ai.streamlit.app"
      description: "Interactive demo of the BI dashboard"
    - type: code
      name: "GitHub Repository"
      url: "https://github.com/ChunkyTortoise/EnterpriseHub"
      description: "Full source code with 4,937 tests"
  cta:
    text: "See the live demo"
    url: "https://ct-enterprise-ai.streamlit.app"
    type: demo
  client_type: enterprise
  project_duration: "8 weeks"
  team_size: 1
  published_date: "2026-02-01"
```

### Validation Rules

1. **ID Format**: Must match `^CS[0-9]{3}$`
2. **Service References**: All IDs must exist in `services.yaml`
3. **Outcomes**: Must have at least 1 outcome metric
4. **Artifacts**: Each artifact must have valid type, name, and URL
5. **CTA**: Must have text, URL, and type
6. **Stack**: Must have 1-15 technology items
7. **Team Size**: Must be >= 1 if provided
8. **Date Format**: Must be ISO 8601 (YYYY-MM-DD) if provided

---

## Cross-Referencing Strategy

### ID-Based Linking

All schemas use ID-based references to maintain data integrity:

```
services.yaml (S01-S26, QW1-QW7)
    ├── case_studies (CS001, CS002, ...)
    ├── certifications (C001, C002, ...)
    └── repos (repo identifiers)

certifications.yaml (C001-C019)
    ├── service_ids (S01, S02, ...)
    └── repo_ids (repo identifiers)

proof_assets.yaml (PA0001-PA9999)
    └── service_ids (S01, S02, ...)

case_studies.yaml (CS001-CS999)
    └── service_ids (S01, S02, ...)
```

### Reference Validation

1. **Forward References**: A service can reference case studies and certifications that don't exist yet (for planning)
2. **Backward References**: Certifications and case studies must reference existing services
3. **Orphan Detection**: Validation should flag:
   - Services with no repos
   - Certifications with no service mappings
   - Case studies with no proof assets

### Circular Dependency Prevention

The schema design prevents circular dependencies:
- Services reference case studies and certifications
- Certifications reference services (not case studies)
- Case studies reference services (not certifications)
- Proof assets reference services only

---

## Three-Layer Proof Stack

### Layer 1: Service-Level Proof

**Purpose**: Establish service credibility with repository links

**Validation Checklist**:
- [ ] Service has at least 1 repository link
- [ ] Repository is publicly accessible
- [ ] Repository README includes service mapping
- [ ] Repository has CI/CD badges
- [ ] Repository has demo mode or live link

**Example**:
```yaml
repos:
  - "https://github.com/ChunkyTortoise/EnterpriseHub"
```

### Layer 2: Asset-Level Proof

**Purpose**: Provide visual evidence of capability

**Validation Checklist**:
- [ ] Asset type matches service category
- [ ] Business claim is specific and measurable
- [ ] Asset is accessible (URL valid or file exists)
- [ ] Asset has been verified within last 90 days
- [ ] Asset has alt text for accessibility

**Example**:
```yaml
asset_type: screenshot
business_claim_supported: "Demonstrates multi-agent bot dashboard with real-time metrics"
last_verified_date: "2026-02-10"
```

### Layer 3: Case Study Proof

**Purpose**: Tell complete story with quantitative outcomes

**Validation Checklist**:
- [ ] Case study has at least 1 service mapping
- [ ] Problem statement is clear and specific
- [ ] Solution describes technical approach
- [ ] Outcomes include at least 2 quantitative metrics
- [ ] Stack lists all major technologies
- [ ] CTA is actionable and relevant
- [ ] At least 1 artifact is linked

**Example**:
```yaml
outcomes:
  lead_response_time: "reduced from 45min to 2min (95% improvement)"
  cost_savings: "$240,000 annual savings"
```

### Proof Stack Validation Matrix

| Service | Layer 1 (Repos) | Layer 2 (Assets) | Layer 3 (Case Studies) | Status |
|---------|-----------------|------------------|------------------------|--------|
| S01 | ✅ 2 repos | ✅ 3 assets | ✅ 1 case study | Complete |
| S02 | ✅ 1 repo | ⚠️ 1 asset | ❌ 0 case studies | Needs case study |
| S03 | ✅ 2 repos | ❌ 0 assets | ✅ 1 case study | Needs assets |
| S04 | ✅ 3 repos | ✅ 5 assets | ✅ 2 case studies | Complete |

---

## Validation Rules Summary

### Required vs Optional Fields

| Schema | Required Fields | Optional Fields |
|--------|-----------------|-----------------|
| services.yaml | id, name, category, buyer_persona, core_problem, deliverables, timeline, price_min, price_max, hourly_equivalent_min, hourly_equivalent_max, repos, status, priority | description, tags, case_studies, certifications |
| certifications.yaml | id, name, provider, status, hours, year, positioning_snippet | verification_url, service_ids, repo_ids, badge_url, category |
| proof_assets.yaml | id, asset_type, service_ids, repo, path_or_url, business_claim_supported, last_verified_date | title, description, thumbnail_url, duration_seconds, file_size_bytes, alt_text |
| case_studies.yaml | id, title, service_ids, industry, problem, solution, stack, outcomes, cta | constraints, artifacts, client_type, project_duration, team_size, published_date |

### Data Type Constraints

| Type | Format | Example |
|------|--------|---------|
| Service ID | `^S(0[1-9]|1[0-9]|2[0-6])$` or `^QW[1-7]$` | S04, QW1 |
| Certification ID | `^C[0-9]{3}$` | C003 |
| Proof Asset ID | `^PA[0-9]{4}$` | PA0001 |
| Case Study ID | `^CS[0-9]{3}$` | CS001 |
| Date | ISO 8601 (YYYY-MM-DD) | 2026-02-10 |
| URL | Valid HTTP/HTTPS URL | https://github.com/... |
| Price | Integer (USD) | 5000 |
| Hours | Integer | 80 |

### Enum Values

| Field | Allowed Values |
|-------|----------------|
| service.category | Strategy, Agentic AI, Data/BI, Marketing, Infra/MLOps, Ops/Governance, Quick-Win |
| service.status | ready, needs-proof, needs-rewrite |
| service.priority | P1, P2, P3 |
| certification.status | completed, in-progress |
| certification.category | AI/ML, GenAI, Data/BI, Marketing, Engineering |
| proof_asset.asset_type | screenshot, gif, video, architecture, benchmark, testimonial |
| case_study.client_type | enterprise, startup, agency, freelance |
| cta.type | booking, contact, demo |

---

## Usage Examples

### Example 1: Service with Complete Proof Stack

```yaml
# services.yaml
- id: S04
  name: Multi-Agent Workflows
  category: Agentic AI
  buyer_persona: "CTOs and engineering leads building AI agent systems"
  core_problem: "Manual coordination between AI agents leads to errors, race conditions, and poor user experience"
  deliverables:
    - "Agent architecture design document"
    - "Multi-agent orchestration framework"
    - "Handoff logic and state management"
    - "Monitoring and observability setup"
    - "Documentation and deployment guide"
  timeline: "2-4 weeks"
  price_min: 5000
  price_max: 15000
  hourly_equivalent_min: 90
  hourly_equivalent_max: 150
  repos:
    - "https://github.com/ChunkyTortoise/EnterpriseHub"
    - "https://github.com/ChunkyTortoise/Revenue-Sprint"
  case_studies:
    - "CS001"
    - "CS002"
  certifications:
    - "C003"
    - "C004"
  status: ready
  priority: P1
```

### Example 2: Certification with Service Mapping

```yaml
# certifications.yaml
- id: C003
  name: IBM RAG and Agentic AI Professional Certificate
  provider: IBM
  status: in-progress
  hours: 80
  year: 2026
  verification_url: "https://www.credly.com/badges/example"
  service_ids:
    - "S03"
    - "S04"
    - "S24"
  repo_ids:
    - "docqa-engine"
    - "EnterpriseHub"
  positioning_snippet: "Expertise in building production RAG systems with hybrid retrieval and agentic workflows"
  badge_url: "https://img.shields.io/badge/IBM-RAG-blue"
  category: GenAI
```

### Example 3: Proof Asset with Business Claim

```yaml
# proof_assets.yaml
- id: PA0001
  asset_type: screenshot
  service_ids:
    - "S04"
    - "S08"
  repo: "EnterpriseHub"
  path_or_url: "assets/screenshots/platform-overview.png"
  business_claim_supported: "Demonstrates multi-agent bot dashboard with real-time metrics and handoff visualization"
  last_verified_date: "2026-02-10"
  title: "EnterpriseHub Platform Overview"
  description: "Main dashboard showing Lead, Seller, and Buyer bot performance metrics"
  alt_text: "Screenshot of EnterpriseHub dashboard with three bot panels and performance charts"
```

### Example 4: Case Study with Quantitative Outcomes

```yaml
# case_studies.yaml
- id: CS001
  title: "Real Estate Lead Qualification Automation"
  service_ids:
    - "S04"
    - "S06"
    - "S08"
  industry: "Real Estate"
  problem: |
    A real estate brokerage was losing 40% of leads due to slow response times.
    Manual qualification took 45+ minutes per lead, and agents struggled to
    prioritize high-value prospects.
  solution: |
    Built a multi-agent AI system with three specialized bots (Lead, Seller, Buyer)
    using a Q0-Q4 qualification framework. Implemented 3-tier Redis caching for
    89% cost reduction and integrated with GoHighLevel for real-time CRM sync.
  stack:
    - "FastAPI"
    - "Claude API"
    - "PostgreSQL"
    - "Redis"
    - "Streamlit"
    - "GoHighLevel"
  outcomes:
    lead_response_time: "reduced from 45min to 2min (95% improvement)"
    cost_savings: "$240,000 annual savings"
    conversion_rate: "increased from 12% to 28%"
    cache_hit_rate: "87% for repeated queries"
    token_cost_reduction: "89% via 3-tier caching"
  cta:
    text: "See the live demo"
    url: "https://ct-enterprise-ai.streamlit.app"
    type: demo
  client_type: enterprise
  project_duration: "8 weeks"
  team_size: 1
  published_date: "2026-02-01"
```

---

## Implementation Notes

### File Locations

```
output/portfolio_data/
├── SCHEMA_DESIGN.md          # This document
├── services.yaml             # Service catalog (S01-S26, QW1-QW7)
├── certifications.yaml       # Certification inventory (C001-C019)
├── proof_assets.yaml         # Proof assets catalog (PA0001-PA9999)
└── case_studies.yaml         # Case studies (CS001-CS999)
```

### Validation Tooling

Recommended validation approach:

1. **YAML Schema Validation**: Use `pydantic` or `jsonschema` for structural validation
2. **Reference Integrity**: Custom validator to check ID references across files
3. **Proof Stack Validation**: Automated check for Three-Layer Proof Stack completeness
4. **Orphan Detection**: Report services/certifications/case studies with no references

### Channel-Specific Rendering

The canonical schemas can be rendered for different channels:

- **Upwork Profile**: Extract services with `status: ready` and `priority: P1`
- **GitHub README**: Generate service/certification mapping blocks
- **Portfolio Website**: Render all services with proof links and case studies
- **Proposals**: Filter by service_ids and include relevant case studies

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-11 | Initial schema design |

---

## Appendix: Service ID Reference

### Core Services (S01-S26)

| ID | Category | Name |
|----|----------|------|
| S01 | Strategy | AI Strategy & Readiness Assessment |
| S02 | Strategy | Technical Due Diligence |
| S03 | Agentic AI | Custom RAG Conversational Agents |
| S04 | Agentic AI | Multi-Agent Workflows |
| S05 | Agentic AI | Prompt Engineering & Optimization |
| S06 | Agentic AI | AI-Powered Personal and Business Automation |
| S07 | Data/BI | Deep Learning Custom ML Models |
| S08 | Data/BI | Interactive Business Intelligence Dashboards |
| S09 | Data/BI | Automated Reporting Pipelines |
| S10 | Data/BI | Predictive Analytics and Lead Scoring |
| S11 | Data/BI | Data Engineering & ETL Pipelines |
| S12 | Marketing | Programmatic SEO Content Engine |
| S13 | Marketing | Email Marketing Automation |
| S14 | Marketing | Social Media Content Automation |
| S15 | Marketing | Marketing Attribution Analysis |
| S16 | Marketing | Competitor Intelligence & Monitoring |
| S17 | Infra/MLOps | MLOps Deployment & CI/CD |
| S18 | Infra/MLOps | LLM Application Modernization |
| S19 | Infra/MLOps | Excel to Web App Modernization |
| S20 | Infra/MLOps | Custom API Development |
| S21 | Ops/Governance | AI Compliance & Governance |
| S22 | Ops/Governance | Knowledge Management System |
| S23 | Ops/Governance | AI Training & Enablement |
| S24 | Ops/Governance | Fractional AI Leadership |
| S25 | Ops/Governance | AI System Audit & Optimization |
| S26 | Ops/Governance | Technical Documentation & Knowledge Base |

### Quick-Win Services (QW1-QW7)

| ID | Name | Price |
|----|------|-------|
| QW1 | CSV-to-Dashboard | $500 |
| QW2 | LLM API Integration | $300 |
| QW3 | Prompt Audit | $400 |
| QW4 | Excel-to-Web App | $800 |
| QW5 | Scraping Setup | $600 |
| QW6 | RAG Quick Start | $700 |
| QW7 | BI Report Template | $450 |

---

## Appendix: Certification ID Reference

| ID | Name | Provider | Hours | Status |
|----|------|----------|-------|--------|
| C001 | Deep Learning Specialization | DeepLearning.AI | 120 | completed |
| C002 | IBM GenAI Engineering | IBM | 90 | completed |
| C003 | IBM RAG and Agentic AI | IBM | 80 | in-progress |
| C004 | AI & ML Engineering | Microsoft | 96 | in-progress |
| C005 | Generative AI Strategic Leader | Vanderbilt | 40 | completed |
| C006 | LLMOps | Duke University | 30 | completed |
| C007 | ChatGPT Personal Automation | Vanderbilt | 24 | in-progress |
| C008 | Google Data Analytics | Google | 181 | completed |
| C009 | Google Advanced Data Analytics | Google | 160 | in-progress |
| C010 | Google Business Intelligence | Google | 110 | in-progress |
| C011 | IBM Business Intelligence Analyst | IBM | 141 | completed |
| C012 | GenAI for Data Analysis | Microsoft | 108 | completed |
| C013 | Data Visualization | Microsoft | 72 | in-progress |
| C014 | AI-Enhanced Data Analysis | Microsoft | 48 | in-progress |
| C015 | Python for Everybody | University of Michigan | 80 | completed |
| C016 | Google Digital Marketing | Google | 120 | in-progress |
| C017 | Meta Social Media Marketing | Meta | 68 | in-progress |
| C018 | AI For Everyone | DeepLearning.AI | 10 | completed |
| C019 | Google Cloud GenAI Leader | Google | 40 | completed |
