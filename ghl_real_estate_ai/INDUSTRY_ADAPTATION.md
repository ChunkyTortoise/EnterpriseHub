# Jorge Bots — Industry Adaptation Guide

**Framework version**: 4.7 | **Last updated**: February 2026

This guide shows how to adapt the Jorge qualification bots for three non-real-estate verticals: Insurance, Mortgage Brokerage, and SaaS Sales. Each section identifies which files, prompts, env vars, and GHL custom fields to modify, along with a sample conversation flow and expected qualification output.

The bot framework is industry-agnostic by design. Industry-specific behavior is driven by YAML configs in `config/industries/`, prompt questions in `ghl_utils/jorge_config.py`, and GHL custom field mappings. No core bot logic needs to change.

---

## Architecture Overview

```
config/industries/<vertical>.yaml    ← personality, intent markers, compliance
ghl_utils/jorge_config.py           ← qualification questions, field mappings, thresholds
config/jorge_bots.yaml              ← scoring weights, temperature thresholds, features
config/jorge_config_loader.py       ← typed config dataclasses
agents/lead/config.py               ← LeadBotConfig dataclass
```

**Key adaptation points**:

| What to change | File | Variable / Section |
|---|---|---|
| Bot personality & system prompt | `config/industries/<vertical>.yaml` | `personality.system_prompt_template` |
| Qualification questions (simple) | `ghl_utils/jorge_config.py` | `JorgeSellerConfig.SELLER_QUESTIONS_SIMPLE` |
| Qualification questions (full) | `ghl_utils/jorge_config.py` | `JorgeSellerConfig.SELLER_QUESTIONS_FULL` |
| Question-to-field mapping | `ghl_utils/jorge_config.py` | `JorgeSellerConfig.QUESTION_FIELD_MAPPING_FULL` |
| GHL custom fields | `ghl_utils/jorge_config.py` | `JorgeSellerConfig.CUSTOM_FIELDS` |
| Scoring weights (FRS) | `config/jorge_bots.yaml` | `lead_bot.scoring.frs_weights` |
| Temperature thresholds | `config/jorge_bots.yaml` | `lead_bot.temperature_thresholds` |
| Intent markers | `config/industries/<vertical>.yaml` | `intents.seller.markers` |
| Activation/deactivation tags | `ghl_utils/jorge_config.py` | `JorgeSellerConfig.ACTIVATION_TAGS` |
| Handoff trigger phrases | `config/jorge_bots.yaml` | `shared.handoff` |
| Env var overrides | `.env` | `JORGE_LEAD_MODE`, `JORGE_SIMPLE_MODE`, etc. |

---

## 1. Insurance Lead Qualification

### Overview

Rename Lead Bot to "Insurance Qualifier". Adapt from real estate seller qualification to insurance coverage needs assessment. The 4-question simple flow maps directly to insurance qualification signals.

### Environment Variables

```bash
# .env
JORGE_LEAD_MODE=true
JORGE_SIMPLE_MODE=true

# Rename temperature tags for insurance context
HOT_SELLER_TAG=Hot-Insurance-Lead
WARM_SELLER_TAG=Warm-Insurance-Lead
COLD_SELLER_TAG=Cold-Insurance-Lead

# GHL custom fields (create these in GHL first)
CUSTOM_FIELD_SELLER_TEMPERATURE=insurance_lead_temperature
CUSTOM_FIELD_SELLER_MOTIVATION=coverage_needs
CUSTOM_FIELD_TIMELINE_URGENCY=renewal_timeline
CUSTOM_FIELD_PROPERTY_CONDITION=current_coverage_status
CUSTOM_FIELD_PRICE_EXPECTATION=budget_range
CUSTOM_FIELD_PCS_SCORE=insurance_qualification_score
```

### Prompt Changes

**File**: `ghl_utils/jorge_config.py` — `JorgeSellerConfig`

```python
# Replace SELLER_QUESTIONS_SIMPLE
SELLER_QUESTIONS_SIMPLE = {
    1: "What type of coverage are you looking for — auto, home, life, or something else?",
    2: "Do you currently have a policy, and when is it up for renewal?",
    3: "What's your monthly budget range for insurance premiums?",
    4: "Are there any specific concerns — claims history, coverage gaps, or bundling options?",
}

# Replace QUESTION_FIELD_MAPPING for simple mode
QUESTION_FIELD_MAPPING_SIMPLE = {
    1: {"field": "coverage_needs", "secondary": "coverage_type"},
    2: {"field": "current_provider", "secondary": "renewal_timeline"},
    3: {"field": "budget_range", "secondary": "budget_flexibility"},
    4: {"field": "special_concerns", "secondary": "bundling_interest"},
}
```

### GHL Custom Fields to Rename

| Real Estate Field | Insurance Field | GHL Custom Field ID |
|---|---|---|
| `seller_temperature` | `insurance_lead_temperature` | Create new |
| `seller_motivation` | `coverage_needs` | Create new |
| `timeline_urgency` | `renewal_timeline` | Create new |
| `property_condition` | `current_coverage_status` | Create new |
| `price_expectation` | `budget_range` | Create new |
| `qualification_score` | `insurance_qualification_score` | Create new |

### Industry Config

Create `config/industries/insurance.yaml`:

```yaml
industry: insurance

market:
  name: SecureShield Insurance
  state: CA
  regulatory_authority: California Department of Insurance
  service_areas:
    - Rancho Cucamonga
    - Ontario
    - Upland
    - Fontana
  compliance_notes:
    - Licensed by California Department of Insurance
    - Fair dealing requirements
    - 30-day cancellation notice required
    - Good faith claims handling obligation

personality:
  name: Sarah
  role: Insurance Advisor
  approach: HELPFUL, TRANSPARENT, and CONSULTATIVE
  core_values:
    - Help clients find the right coverage, not the most expensive
    - Explain policy details in plain language
    - Proactively identify coverage gaps
    - Respect budget constraints
  system_prompt_template: |
    You are {{ name }}, a licensed insurance advisor at SecureShield Insurance.
    Your approach is: {{ approach }}.
    You help clients find the right coverage for their needs and budget.

    NEVER provide specific policy quotes — only qualify and route to a licensed agent.
    ALWAYS disclose that you are an AI assistant.
```

### Scoring Weights

**File**: `config/jorge_bots.yaml` — replace `lead_bot.scoring.frs_weights`:

```yaml
lead_bot:
  scoring:
    frs_weights:
      renewal_urgency: 0.30      # Was: timeline_urgency
      budget_clarity: 0.25       # Was: budget_clarity
      coverage_gap_severity: 0.25 # Was: motivation_strength
      current_provider_status: 0.20 # Was: property_specificity
```

### Example Conversation Flow

```
Bot:  Hi! I'm Sarah from SecureShield Insurance. I'd love to help you find
      the right coverage. What type of insurance are you looking for — auto,
      home, life, or something else?

Lead: I need home and auto insurance. Moving to a new place next month.

Bot:  Great, bundling home and auto usually saves 15-25%! Do you currently
      have policies with another provider, and when are they up for renewal?

Lead: Yeah I have State Farm but my renewal is in 3 weeks and the rates went
      up 40% this year.

Bot:  That's a big jump — we hear that a lot lately. What monthly budget range
      works for you for the combined home and auto coverage?

Lead: I'd like to stay under $300/month total if possible.

Bot:  Under $300 combined is very doable. Last question — are there any specific
      concerns I should flag for your agent? Things like recent claims, coverage
      gaps, or specific riders you need?

Lead: I had one auto claim last year, fender bender. And I want flood coverage
      on the home policy.

Bot:  Perfect, I've got everything I need. Let me connect you with a licensed
      agent who specializes in home+auto bundles. They'll have quotes ready
      within 24 hours. What's the best time to reach you?
```

### Expected Qualification Output

```json
{
  "temperature": "Hot-Insurance-Lead",
  "qualification_score": 92,
  "coverage_needs": "home + auto bundle",
  "current_provider": "State Farm",
  "renewal_timeline": "3 weeks",
  "budget_range": "$300/month combined",
  "special_concerns": ["prior claim (auto, minor)", "flood coverage needed"],
  "questions_answered": 4,
  "handoff_recommendation": "licensed_agent",
  "priority": "high"
}
```

---

## 2. Mortgage Broker Qualification

### Overview

Adapt for mortgage loan origination: purchase vs refinance, loan amount, credit score range, down payment, and timeline. Maps cleanly to the 4-question simple flow with financial readiness scoring.

### Environment Variables

```bash
# .env
JORGE_LEAD_MODE=true
JORGE_SIMPLE_MODE=true

HOT_SELLER_TAG=Hot-Mortgage-Lead
WARM_SELLER_TAG=Warm-Mortgage-Lead
COLD_SELLER_TAG=Cold-Mortgage-Lead

CUSTOM_FIELD_SELLER_TEMPERATURE=mortgage_lead_temperature
CUSTOM_FIELD_SELLER_MOTIVATION=loan_purpose
CUSTOM_FIELD_TIMELINE_URGENCY=purchase_timeline
CUSTOM_FIELD_PROPERTY_CONDITION=credit_score_range
CUSTOM_FIELD_PRICE_EXPECTATION=target_loan_amount
CUSTOM_FIELD_PCS_SCORE=mortgage_qualification_score
```

### Prompt Changes

**File**: `ghl_utils/jorge_config.py` — `JorgeSellerConfig`

```python
SELLER_QUESTIONS_SIMPLE = {
    1: "Are you looking to purchase a new home or refinance an existing mortgage?",
    2: "What's your target price range or loan amount, and do you have a down payment ready?",
    3: "Do you know your approximate credit score range — excellent, good, fair, or not sure?",
    4: "What's your timeline — are you actively shopping, or just exploring your options?",
}

QUESTION_FIELD_MAPPING_SIMPLE = {
    1: {"field": "loan_purpose", "secondary": "property_type"},
    2: {"field": "target_loan_amount", "secondary": "down_payment_status"},
    3: {"field": "credit_score_range", "secondary": "credit_concerns"},
    4: {"field": "purchase_timeline", "secondary": "urgency_level"},
}
```

### GHL Custom Fields to Rename

| Real Estate Field | Mortgage Field | GHL Custom Field ID |
|---|---|---|
| `seller_temperature` | `mortgage_lead_temperature` | Create new |
| `seller_motivation` | `loan_purpose` | Create new |
| `timeline_urgency` | `purchase_timeline` | Create new |
| `property_condition` | `credit_score_range` | Create new |
| `price_expectation` | `target_loan_amount` | Create new |
| `qualification_score` | `mortgage_qualification_score` | Create new |

### Industry Config

Create `config/industries/mortgage_broker.yaml`:

```yaml
industry: mortgage_broker

market:
  name: PrimeLend Mortgage
  state: CA
  regulatory_authority: California DFPI (Dept of Financial Protection and Innovation)
  service_areas:
    - Rancho Cucamonga
    - Inland Empire
    - Los Angeles County
    - Orange County
  compliance_notes:
    - NMLS licensed mortgage loan originator
    - RESPA disclosure requirements
    - TILA (Truth in Lending Act) compliance
    - Equal Credit Opportunity Act (ECOA)
    - Cannot guarantee rates or approval

personality:
  name: Marcus
  role: Mortgage Advisor
  approach: KNOWLEDGEABLE, PATIENT, and STRAIGHTFORWARD
  core_values:
    - Explain loan options without jargon
    - Never pressure clients into larger loans
    - Transparent about rates, fees, and timelines
    - Respect financial privacy
  system_prompt_template: |
    You are {{ name }}, a mortgage advisor at PrimeLend Mortgage.
    Your approach is: {{ approach }}.
    You help clients understand their mortgage options and connect them with
    a licensed loan officer for pre-approval.

    NEVER quote specific rates or guarantee approval.
    ALWAYS disclose that you are an AI assistant.
    NEVER ask for SSN, bank account numbers, or other sensitive financial data.
```

### Scoring Weights

```yaml
lead_bot:
  scoring:
    frs_weights:
      purchase_timeline: 0.30
      down_payment_readiness: 0.25
      credit_score_clarity: 0.25
      loan_amount_specificity: 0.20
```

### Example Conversation Flow

```
Bot:  Hi, I'm Marcus from PrimeLend Mortgage! Are you looking to purchase a
      new home or refinance an existing mortgage?

Lead: Purchase. We're first-time buyers looking in the Inland Empire area.

Bot:  Exciting! First-time buyers have some great program options. What's your
      target price range, and do you have a down payment saved up?

Lead: Looking at $500-600K homes. We have about $50K saved for down payment.

Bot:  That's a solid start — roughly 8-10% down, which opens up conventional
      and FHA options. Do you know your approximate credit score range —
      excellent (740+), good (670-739), fair (580-669), or not sure?

Lead: My wife and I are both around 720 I think. Good but not excellent.

Bot:  720 is great — you'll qualify for competitive rates. Last question:
      what's your timeline? Are you actively shopping with an agent, or still
      in the early research phase?

Lead: We have a realtor and we're looking at homes this weekend actually.

Bot:  Perfect timing. Let me connect you with a loan officer who can get you
      pre-approved before your showings this weekend. They'll walk you through
      rates and programs for your situation. Is tomorrow morning good for a
      quick call?
```

### Expected Qualification Output

```json
{
  "temperature": "Hot-Mortgage-Lead",
  "qualification_score": 95,
  "loan_purpose": "purchase",
  "buyer_type": "first_time",
  "target_loan_amount": "$500K-600K",
  "down_payment_status": "$50K saved (8-10%)",
  "credit_score_range": "good (720)",
  "purchase_timeline": "active — showings this weekend",
  "questions_answered": 4,
  "handoff_recommendation": "loan_officer_preapproval",
  "priority": "urgent",
  "program_eligibility": ["conventional", "FHA"]
}
```

---

## 3. SaaS Sales Qualification (BANT)

### Overview

Adapt for B2B SaaS sales using BANT methodology: Budget, Authority, Need, Timeline. The 4-question simple flow maps 1:1 to BANT qualification signals.

### Environment Variables

```bash
# .env
JORGE_LEAD_MODE=true
JORGE_SIMPLE_MODE=true

HOT_SELLER_TAG=Hot-SaaS-Lead
WARM_SELLER_TAG=Warm-SaaS-Lead
COLD_SELLER_TAG=Cold-SaaS-Lead

CUSTOM_FIELD_SELLER_TEMPERATURE=saas_lead_temperature
CUSTOM_FIELD_SELLER_MOTIVATION=business_need
CUSTOM_FIELD_TIMELINE_URGENCY=purchase_timeline
CUSTOM_FIELD_PROPERTY_CONDITION=decision_authority
CUSTOM_FIELD_PRICE_EXPECTATION=budget_range
CUSTOM_FIELD_PCS_SCORE=bant_score
```

### Prompt Changes

**File**: `ghl_utils/jorge_config.py` — `JorgeSellerConfig`

```python
SELLER_QUESTIONS_SIMPLE = {
    1: "What challenge are you trying to solve, and what tools are you using today?",
    2: "Do you have a budget allocated for this, or are you still building the business case?",
    3: "Who else would be involved in the decision — is this your call, or does it go through a team?",
    4: "What's your ideal timeline — do you need something in place this quarter, or is this more exploratory?",
}

QUESTION_FIELD_MAPPING_SIMPLE = {
    1: {"field": "business_need", "secondary": "current_tools"},
    2: {"field": "budget_range", "secondary": "budget_status"},
    3: {"field": "decision_authority", "secondary": "buying_committee"},
    4: {"field": "purchase_timeline", "secondary": "urgency_level"},
}
```

### GHL Custom Fields to Rename

| Real Estate Field | SaaS Field | GHL Custom Field ID |
|---|---|---|
| `seller_temperature` | `saas_lead_temperature` | Create new |
| `seller_motivation` | `business_need` | Create new |
| `timeline_urgency` | `purchase_timeline` | Create new |
| `property_condition` | `decision_authority` | Create new |
| `price_expectation` | `budget_range` | Create new |
| `qualification_score` | `bant_score` | Create new |

### Industry Config

Create `config/industries/saas_sales.yaml`:

```yaml
industry: saas_sales

market:
  name: AcmeSoft
  state: US
  regulatory_authority: N/A
  service_areas: []
  compliance_notes:
    - SOC 2 Type II certified
    - GDPR compliant (EU customers)
    - CCPA compliant (California customers)
    - Standard MSA and DPA available

personality:
  name: Alex
  role: Solutions Consultant
  approach: CONSULTATIVE, CURIOUS, and VALUE-FOCUSED
  core_values:
    - Understand the problem before pitching the solution
    - Respect the prospect's time and buying process
    - Be transparent about pricing and limitations
    - Focus on ROI and business outcomes
  system_prompt_template: |
    You are {{ name }}, a solutions consultant at AcmeSoft.
    Your approach is: {{ approach }}.
    You qualify inbound leads using BANT methodology and route qualified
    prospects to the right account executive.

    NEVER pressure prospects into demos they don't need.
    ALWAYS position discovery as helping them, not selling to them.
    Keep messages concise — B2B buyers are busy.
```

### Scoring Weights

```yaml
lead_bot:
  scoring:
    frs_weights:
      need_severity: 0.30        # Was: timeline_urgency
      budget_clarity: 0.25       # Was: budget_clarity
      authority_confirmed: 0.25  # Was: motivation_strength
      timeline_urgency: 0.20    # Was: property_specificity
```

### BANT Scoring Matrix

| BANT Dimension | Hot (3 pts) | Warm (2 pts) | Cold (1 pt) |
|---|---|---|---|
| **Budget** | Allocated, approved | Building business case | No budget / unknown |
| **Authority** | Decision maker | Influencer / champion | Researcher / end user |
| **Need** | Active pain point, incumbent failing | Evaluating options | Curious / no urgency |
| **Timeline** | This quarter | This half | Next year / exploratory |

**Temperature mapping**: Hot >= 10, Warm >= 6, Cold < 6 (out of 12 max)

### Example Conversation Flow

```
Bot:  Hi! I'm Alex from AcmeSoft. Thanks for reaching out. What challenge
      are you trying to solve, and what tools are you using today?

Lead: We're struggling with our customer onboarding flow. Using a mix of
      Notion docs and manual emails. It takes 2 weeks per customer and
      we're scaling fast.

Bot:  Onboarding bottleneck at scale — that's exactly what we solve. Do you
      have a budget allocated for an onboarding platform, or are you still
      building the business case?

Lead: We got approved for $2K/month in our Q1 planning. Looking to deploy
      something by end of March.

Bot:  Perfect — $2K/month fits our Growth plan well. Quick question: who else
      would be involved in the decision? Is this your call, or does it go
      through a team?

Lead: I'm the VP of Customer Success. I own the decision but our CTO will
      want to review the technical integration.

Bot:  Great — VP CS as the decision maker with CTO for technical review is
      a clean buying process. And just to confirm, you mentioned end of March
      — is that a hard deadline or flexible?

Lead: Hard deadline. We're onboarding 50 new customers in April and the
      current process won't scale.

Bot:  Got it — this is urgent and well-scoped. I'm going to connect you with
      Jamie, your dedicated account executive. She'll set up a 30-minute
      discovery call with a live demo of our onboarding workflows. Does
      tomorrow or Thursday work better?
```

### Expected Qualification Output

```json
{
  "temperature": "Hot-SaaS-Lead",
  "bant_score": 12,
  "bant_breakdown": {
    "budget": {"score": 3, "detail": "$2K/month approved, Q1 budget"},
    "authority": {"score": 3, "detail": "VP Customer Success, decision maker"},
    "need": {"score": 3, "detail": "Active pain — manual onboarding won't scale"},
    "timeline": {"score": 3, "detail": "Hard deadline end of March"}
  },
  "business_need": "customer onboarding automation",
  "current_tools": "Notion + manual emails",
  "budget_range": "$2,000/month",
  "decision_authority": "VP CS (decision maker) + CTO (technical review)",
  "purchase_timeline": "end of March (hard deadline)",
  "questions_answered": 4,
  "handoff_recommendation": "account_executive_demo",
  "priority": "urgent",
  "company_signals": {
    "growth_stage": "scaling",
    "team_size_indicator": "50+ new customers/month"
  }
}
```

---

## General Adaptation Checklist

When adapting to any new vertical:

1. **Create industry YAML** in `config/industries/<vertical>.yaml` with personality, intent markers, and compliance notes
2. **Update qualification questions** in `ghl_utils/jorge_config.py` — both `SELLER_QUESTIONS_SIMPLE` (4Q) and `SELLER_QUESTIONS_FULL` (10Q)
3. **Update field mappings** in `ghl_utils/jorge_config.py` — `QUESTION_FIELD_MAPPING_SIMPLE` and `QUESTION_FIELD_MAPPING_FULL`
4. **Create GHL custom fields** in the GHL location settings to match the new field names
5. **Update env vars** in `.env` — temperature tags, custom field IDs, mode flags
6. **Adjust scoring weights** in `config/jorge_bots.yaml` — FRS and PCS weights for vertical-specific signals
7. **Update activation tags** in `ghl_utils/jorge_config.py` — `ACTIVATION_TAGS` and `DEACTIVATION_TAGS`
8. **Test the flow** — run `pytest tests/ -k jorge` and verify all question paths complete
9. **Update handoff triggers** in `config/jorge_bots.yaml` — cross-bot handoff phrases for the new vertical

### Files Modified Per Adaptation

| File | Changes Required |
|---|---|
| `config/industries/<vertical>.yaml` | New file (personality, intents, compliance) |
| `ghl_utils/jorge_config.py` | Questions, field mappings, tags, thresholds |
| `config/jorge_bots.yaml` | Scoring weights, temperature thresholds |
| `.env` | Custom field IDs, mode flags, workflow IDs |
| GHL Admin Panel | Create custom fields, workflows, calendars |
