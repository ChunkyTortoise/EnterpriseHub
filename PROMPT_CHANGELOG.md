# Prompt Changelog

All system prompts are versioned. Every change includes rationale.

---

## Seller Prompts

### jorge_seller_system v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/prompts/system_prompts.py` (line 268)
- **Content**: `You are Jorge's AI seller qualification bot. You communicate via SMS with a DIRECT, CONFRONTATIONAL approach...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Core seller qualification prompt implementing Jorge's 4-question confrontational flow (motivation, timeline, condition, price). Includes escalation tiers for vague responses, SMS compliance (<160 chars), temperature classification (hot/warm/cold), and re-engagement breakup texts.

### seller_qualification v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/prompts/system_prompts.py` (line 207)
- **Content**: `You are in lead qualification mode for a potential SELLER. ## QUALIFICATION FRAMEWORK (Jorge's 7 Que...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Extended seller qualification framework covering property address/type, motivation, timeline, condition, and price expectations. Used as contextual injection for the general buyer/seller system prompt.

### seller_personality v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/agents/personalities/real_estate.py` (line 536)
- **Content**: `You are Jorge Salas, a caring and knowledgeable real estate professional. Your approach is: HELPFUL, ...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Registered `BotPersonality` ABC implementation for seller bot. Consultative tone, 6 intent signal categories (motivation, timeline, condition, price, valuation, prep_readiness), scoring weights summing to 1.0, handoff trigger to buyer bot at 0.7 confidence.

### seller_response_generator v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/agents/seller/response_generator.py` (line 235)
- **Content**: f-string prompt building seller response with context, seller data, and optional `bot_settings_store` system_prompt override
- **Model**: claude-sonnet-4-6
- **Rationale**: Runtime response generation for seller conversations. Supports psychographic persona override via `get_system_prompt_override("seller")`.

### seller_linguistic_adaptation v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py` (line 1989)
- **Content**: `You are a linguistic adaptation engine. Keep responses SMS compliant (<160 chars, no emojis, no hyph...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Post-processing prompt that adapts seller responses for SMS compliance, used when psychographic persona override adjusts tone.

### seller_response_quality_analyzer v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py` (line 2307)
- **Content**: `You are a response quality analyzer. Return only valid JSON.`
- **Model**: claude-sonnet-4-6
- **Rationale**: Evaluates seller response quality (0.0-1.0 score) to determine if answers are substantive enough to advance qualification.

---

## Buyer Prompts

### buyer_qualification v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/prompts/system_prompts.py` (line 120)
- **Content**: `You are in lead qualification mode for a potential BUYER. ## QUALIFICATION FRAMEWORK (5 Key Data Po...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Buyer qualification framework covering 5 key data points: budget, location, timeline, must-haves, financing status. Includes Jorge's scoring criteria (3+ = HOT, 2 = WARM, 0-1 = COLD) and response examples for Rancho Cucamonga market.

### buyer_personality v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/agents/personalities/real_estate.py` (line 346)
- **Content**: `You are Jorge's Buyer Bot, helping {buyer_name} find their perfect home in Rancho Cucamonga, CA...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Registered `BotPersonality` for buyer bot. Supportive tone, 3 intent signal categories (urgency, financial_readiness, motivation), handoff to seller bot at 0.7 confidence for "sell before buying" scenarios.

### buyer_response_generator v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/agents/buyer/response_generator.py` (line 316)
- **Content**: f-string prompt building buyer response with context, buyer data, and optional `bot_settings_store` system_prompt override
- **Model**: claude-sonnet-4-6
- **Rationale**: Runtime response generation for buyer conversations. Supports `get_system_prompt_override("buyer")` from bot_settings_store.

---

## Lead Intake Prompts

### base_system_prompt v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/prompts/system_prompts.py` (line 10)
- **Content**: `You are Jorge, a real estate agent in Rancho Cucamonga. You qualify leads via SMS on behalf of your ...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Master system prompt defining Jorge's personality (professional, friendly, direct, curious), buyer 7-question and seller 4-question flows, SMS compliance (<160 chars), AI identity rules, re-engagement breakup texts, and tone examples from Jorge's actual messaging.

### lead_bot_simple v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/agents/lead_bot.py` (line 2263)
- **Content**: `You are Jorge Salas, a caring real estate professional in Rancho Cucamonga, CA. You help incoming le...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Simplified lead bot system prompt for the state-machine path. Rules: SMS <160 chars, no hyphens/emojis, warm tone, one question at a time, never repeat questions, pivot to scheduling after intent + timeline captured.

### lead_personality v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/agents/personalities/real_estate.py` (line 194)
- **Content**: `You are Jorge Salas, a caring and knowledgeable real estate professional in Rancho Cucamonga, CA...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Registered `BotPersonality` for lead qualification. Consultative tone, 4 intent signal categories (motivation, timeline, condition, price), handoff triggers to buyer (0.7) and seller (0.7) bots.

---

## Objection Handling Prompts

### objection_handlers v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/prompts/system_prompts.py` (line 479)
- **Content**: Template-based objection responses for 6 categories: price_too_high, need_to_think, credit_concerns, market_timing, inspection_issues, down_payment_concerns
- **Model**: N/A (template strings, not LLM-generated)
- **Rationale**: Static response templates with trigger phrases, key points, and contextual placeholders. Each handler provides 2-3 actionable alternatives and avoids dismissing lead concerns.

### sdr_objection_classifier v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/agents/sdr/objection_handler.py` (line 96)
- **Content**: `You are an objection classifier for a real estate SDR system. Classify the prospect's message into ...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Classifies inbound replies into objection types (not_interested, already_agent, timing, price, info_request, none). JSON-only output. Used as Claude fallback when pattern matching is ambiguous.

---

## Appointment Setting Prompts

### appointment_setting v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/prompts/system_prompts.py` (line 622)
- **Content**: `You are in appointment-setting mode. The lead is qualified and ready for next steps...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Appointment flow covering 3 types (property showing, buyer consultation, home valuation), buying signal detection, scheduling objection handling ("not ready", "can't I work with you"), GHL calendar integration, and agent notification workflow.

---

## Orchestrator System Prompts

### chat_assistant v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/services/claude_orchestrator.py` (line 194)
- **Content**: `You are Claude, Jorge's AI partner in real estate. You have deep knowledge of: GHL workflows, marke...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Dashboard chat interface prompt. Positions Claude as Jorge's trusted advisor with direct, actionable, data-driven responses.

### lead_analyzer v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/services/claude_orchestrator.py` (line 207)
- **Content**: `You are an expert lead intelligence analyst. Your job is to synthesize multiple data sources to crea...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Synthesizes qualification scores (0-7 + ML), behavioral patterns, sentiment, market context, and churn risk into strategic lead profiles with specific action recommendations.

### report_synthesizer v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/services/claude_orchestrator.py` (line 222)
- **Content**: `You are Jorge's business intelligence analyst. Generate executive-level reports that combine quantit...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Executive reporting in Jorge's voice: direct, data-driven, action-oriented. Covers pipeline health, conversion metrics, market opportunities, and growth recommendations.

### script_generator v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/services/claude_orchestrator.py` (line 232)
- **Content**: `You are Jorge's sales communication specialist. Generate personalized scripts that match each lead's...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Generates channel-appropriate (SMS/email/call) scripts with A/B test variants. Considers personality, objection history, market conditions, and urgency factors.

### omnipotent_assistant v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/services/claude_orchestrator.py` (line 247)
- **Content**: `You are the Omnipotent Claude Assistant for EnterpriseHub v6.0 and GHL Real Estate AI (Elite v4.0)...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Full-context assistant with knowledge of system architecture, AI engines (15-factor scoring, lifestyle matching, swarm intelligence), business goals (85+ hrs/month automation), and GHL integration.

### persona_optimizer v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/services/claude_orchestrator.py` (line 255)
- **Content**: `You are an AI Behavioral Psychologist and Prompt Engineer. Your task is to optimize real estate AI p...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Tunes bot neural weights (tone, empathy, persistence) for high-conversion digital identities. Outputs optimized system prompt instructions with engagement impact analysis.

### researcher_assistant v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/services/claude_orchestrator.py` (line 264)
- **Content**: `You are a real estate research specialist. Your goal is to synthesize real-time market data and prop...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Market research prompt for neighborhood analysis, property value drivers, competitive positioning. Provides data-backed reports with citations.

---

## Agent/Swarm Prompts

### overseer_strategic_decision v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/agents/jorge_overseer/overseer_agent.py` (line 186)
- **Content**: `You are Jorge's strategic AI overseer. Make a strategic decision using Jorge's proven real estate me...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Top-level strategic decision engine. Enforces Jorge's core principles: 6% commission non-negotiable, 95%+ success rate, 5-min response time, client experience drives referrals. Outputs JSON with ROI, implementation plan, and risk mitigation.

### swarm_agent_generic v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/agents/swarm_orchestrator.py` (line 396)
- **Content**: `You are {agent.name}, an expert {agent.description}. Use tools provided to achieve the objective.`
- **Model**: claude-sonnet-4-6
- **Rationale**: Generic agent prompt template for swarm orchestrator. Dynamically populated with agent name and description for multi-agent collaboration.

### arbitrage_specialist v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/agents/agent_swarm_orchestrator_v2.py` (line 248)
- **Content**: `You are a real estate arbitrage specialist.`
- **Model**: claude-sonnet-4-6
- **Rationale**: Specialized agent for multi-market property arbitrage analysis within swarm v2.

### data_cleaning_specialist v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/agents/agent_swarm_orchestrator_v2.py` (line 354)
- **Content**: `You are a data cleaning specialist.`
- **Model**: claude-sonnet-4-6
- **Rationale**: Specialized agent for data normalization and cleaning within swarm v2. Temperature 0 for deterministic output.

### relocation_strategist v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/agents/agent_swarm_orchestrator_v2.py` (line 410)
- **Content**: `You are a multi-market relocation strategist.`
- **Model**: claude-sonnet-4-6
- **Rationale**: Specialized agent for cross-market relocation analysis within swarm v2.

---

## Follow-up/Nurture Prompts

### followup_linguistic_adaptation v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/services/jorge/jorge_followup_engine.py` (line 267)
- **Content**: `You are a linguistic adaptation engine for SMS real estate marketing.`
- **Model**: claude-sonnet-4-6
- **Rationale**: Adapts follow-up message variants for SMS compliance and Jorge's confrontational style. Low temperature (0.3) for consistent output.

---

## Dental Industry Prompts (Multi-Tenant)

### dental_lead_personality v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/agents/personalities/dental.py` (line 212)
- **Content**: `You are a friendly dental practice assistant helping {patient_name} with their dental care needs...`
- **Model**: claude-sonnet-4-6
- **Rationale**: Multi-tenant industry portability proof. Friendly tone, 4 intent signal categories (urgency, procedure_value, insurance_status, motivation), 3 handoff targets (cosmetic at 0.7, orthodontic at 0.7, emergency at 0.5 lower threshold).

---

## Bot Settings Overrides

### bot_settings_store v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/services/jorge/bot_settings_store.py` (line 199)
- **Content**: Runtime-configurable `system_prompt` field per bot (buyer/seller)
- **Model**: N/A (override layer)
- **Rationale**: Allows runtime persona prefix injection into Claude prompts without code changes. Supports `system_prompt`, `jorge_phrases`, and `questions` overrides per bot type. Retrieved via `get_system_prompt_override(bot)`.

---

## YAML-Based Personality Config

### personality_config_template v1.0 (2026-04-07)
- **File**: `ghl_real_estate_ai/agents/personality_config.py` (line 102)
- **Content**: `system_prompt_template: You are {name}, a {role}. ...`
- **Model**: claude-sonnet-4-6
- **Rationale**: YAML-driven personality config schema supporting `system_prompt_template` with variable interpolation. Enables no-code personality creation with validated scoring weights (must sum to 1.0), intent signals, temperature thresholds, and handoff triggers.

---

## Version History

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-04-07 | v1.0 | Initial baseline of all production prompts | Claude Code |
