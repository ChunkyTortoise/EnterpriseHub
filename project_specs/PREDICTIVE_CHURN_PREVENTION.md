# Predictive Churn Prevention

> **Project Specification** | **Version**: 1.0 | **Price Point**: $15,000 | **Target**: Real Estate Agencies

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Specification](#architecture-specification)
3. [Feature Set](#feature-set)
4. [Technical Requirements](#technical-requirements)
5. [Deliverables](#deliverables)
6. [Success Metrics](#success-metrics)
7. [Timeline](#timeline)
8. [Pricing Breakdown](#pricing-breakdown)
9. [Appendix](#appendix)

---

## Executive Summary

### Project Overview

Predictive Churn Prevention is an AI-powered retention system designed for real estate agencies seeking to proactively identify and re-engage at-risk leads and customers. This solution leverages machine learning to analyze engagement patterns, predict churn probability, and trigger automated re-engagement workflows before leads disengage.

### The Challenge

Real estate agencies face critical retention challenges:

- **Lead Leakage**: 65% of leads go unconverted due to lack of follow-up
- **Reactive Response**: Agencies only respond after leads have already disengaged
- **No Visibility**: No early warning signals for lead attrition risk
- **Manual Processes**: Sales teams spend excessive time on low-value follow-ups
- **Missed Opportunities**: High-value leads slip through cracks during peak periods

### The Solution

A predictive churn prevention system featuring:

- **ML-Based Churn Prediction**: XGBoost/LightGBM models with 85%+ accuracy
- **Multi-Horizon Forecasting**: 30-day, 60-day, 90-day churn risk predictions
- **Engagement Pattern Analysis**: Behavioral scoring based on interaction history
- **Risk Factor Identification**: AI-driven analysis of churn drivers
- **Early Warning Signals**: Proactive alerts before lead disengagement
- **Automated Re-engagement**: GHL-integrated workflow triggers
- **Sentiment Analysis**: Conversation tone monitoring
- **Lead Aging Analysis**: Time-since-last-contact scoring
- **Real-time Scoring**: <100ms prediction latency

### The Result

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Lead Churn Rate | 65% | 48.75% | -25% |
| Re-engagement Rate | 15% | 17.25% | +15% |
| Prediction Latency | N/A | <100ms | New Capability |
| Sales Team Productivity | 20 hrs/week | 35 hrs/week | +75% |
| Annual Revenue/Lead | $2,400 | $3,600 | +50% |

---

## Architecture Specification

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PREDICTIVE CHURN PREVENTION                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         CLIENT LAYER                                   │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │
│  │  │   Admin    │  │   Sales     │  │    GHL     │  │   Bot      │ │  │
│  │  │  Dashboard │  │    Team     │  │   Widget   │  │  System    │ │  │
│  │  │  (Streamlit│  │   Portal    │  │            │  │            │ │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │  │
│  └─────────┼────────────────┼────────────────┼────────────────┼─────────┘  │
│            │                │                │                │             │
│            └────────────────┴────────┬───────┴────────────────┘             │
│                                       │                                      │
│  ┌────────────────────────────────────▼───────────────────────────────────┐  │
│  │                     API GATEWAY (FastAPI)                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │
│  │  │   Auth &    │  │   Rate      │  │   Request  │  │   Response │ │  │
│  │  │   JWT       │  │   Limiting  │  │   Validation│ │   Caching │ │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │  │
│  └────────────────────────────────────┬───────────────────────────────────┘  │
│                                       │                                      │
│  ┌────────────────────────────────────▼───────────────────────────────────┐  │
│  │                     CHURN ENGINE LAYER                                │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │              CHURN PREDICTION ORCHESTRATOR                      │ │  │
│  │  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │ │  │
│  │  │  │   Model      │  │    Feature    │  │    Risk      │       │ │  │
│  │  │  │  Selection   │  │   Aggregator  │  │   Calculator │       │ │  │
│  │  │  └───────────────┘  └───────────────┘  └───────────────┘       │ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                       │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │  │
│  │  │   30-Day       │  │   60-Day       │  │   90-Day       │     │  │
│  │  │   Churn Model  │  │   Churn Model  │  │   Churn Model  │     │  │
│  │  │                │  │                │  │                │     │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │  │
│  └────────────────────────────────────┬───────────────────────────────────┘  │
│                                       │                                      │
│  ┌────────────────────────────────────▼───────────────────────────────────┐  │
│  │                     FEATURE ENGINE LAYER                              │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │  │
│  │  │   Engagement    │  │    Sentiment    │  │   Lead Aging   │     │  │
│  │  │   Metrics       │  │    Analysis     │  │    Analysis    │     │  │
│  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐ │     │  │
│  │  │  │Frequency  │  │  │  │   Claude  │  │  │  │  Days     │ │     │  │
│  │  │  │ Recency   │  │  │  │  Sentiment│  │  │  │  Since    │ │     │  │
│  │  │  │Duration   │  │  │  │  Analyzer │  │  │  │  Contact  │ │     │  │
│  │  │  │ Response  │  │  │  │           │  │  │  │           │ │     │  │
│  │  │  │  Time     │  │  │  │           │  │  │  │           │ │     │  │
│  │  │  └───────────┘  │  │  └───────────┘  │  │  └───────────┘ │     │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │  │
│  │                                                                       │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │  │
│  │  │   Risk Factor  │  │  Behavioral    │  │  GHL CRM       │     │  │
│  │  │   Identifier   │  │   Patterns     │  │  Enrichment    │     │  │
│  │  │                │  │                │  │                │     │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │  │
│  └────────────────────────────────────┬───────────────────────────────────┘  │
│                                       │                                      │
│  ┌────────────────────────────────────▼───────────────────────────────────┐  │
│  │                     ML MODEL LAYER                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │                    XGBoost/LightGBM Ensemble                     │ │  │
│  │  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │ │  │
│  │  │  │ 30-Day Model │  │ 60-Day Model │  │ 90-Day Model │       │ │  │
│  │  │  │  (High Recall)│  │ (Balanced)   │  │ (High Prec.) │       │ │  │
│  │  │  └───────────────┘  └───────────────┘  └───────────────┘       │ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │  │
│  │  │                    Model Training Pipeline                        │ │  │
│  │  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐   │ │  │
│  │  │  │   Data    │  │ Feature   │  │   Model   │  │  Model    │   │ │  │
│  │  │  │Ingestion  │  │ Engineering│  │  Training │  │ Validation│   │ │  │
│  │  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘   │ │  │
│  │  └─────────────────────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────┬───────────────────────────────────┘  │
│                                       │                                      │
│  ┌────────────────────────────────────▼───────────────────────────────────┐  │
│  │                     RE-ENGAGEMENT LAYER                               │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │  │
│  │  │   Workflow      │  │    Trigger      │  │   Personalization│     │  │
│  │  │   Engine        │  │    Rules        │  │    Engine       │     │  │
│  │  │  ┌───────────┐  │  │  ┌───────────┐  │  │  ┌───────────┐ │     │  │
│  │  │  │   GHL    │  │  │  │   Risk    │  │  │  │   Claude  │ │     │  │
│  │  │  │   Workflow│  │  │  │   Threshold│  │  │  │   Content │ │     │  │
│  │  │  │   Triggers│  │  │  │   Based    │  │  │  │   Gen     │ │     │  │
│  │  │  └───────────┘  │  │  └───────────┘  │  │  └───────────┘ │     │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │  │
│  └────────────────────────────────────┬───────────────────────────────────┘  │
│                                       │                                      │
│  ┌────────────────────────────────────▼───────────────────────────────────┐  │
│  │                     INTEGRATION LAYER                                  │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │  │
│  │  │     GHL CRM    │  │    PostgreSQL   │  │     Redis       │     │  │
│  │  │    Client      │  │    Database     │  │     Cache      │     │  │
│  │  │  (10 req/s)    │  │    + Alembic    │  │  (L1/L2/L3)    │     │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │  │
│  │                                                                       │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │  │
│  │  │  Jorge Bots    │  │  Claude        │  │  Gemini         │     │  │
│  │  │  Integration   │  │  Orchestrator  │  │  Provider       │     │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │  │
│  └────────────────────────────────────┬───────────────────────────────────┘  │
│                                       │                                      │
│  ┌────────────────────────────────────▼───────────────────────────────────┐  │
│  │                     OBSERVABILITY LAYER                               │  │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │  │
│  │  │   Prometheus   │  │    Grafana      │  │  OpenTelemetry  │     │  │
│  │  │   Metrics      │  │   Dashboards    │  │   Tracing      │     │  │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
```

### ML Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ML PIPELINE ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DATA INGESTION                                                             │
│  ───────────                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Sources: GHL Contacts | Bot Conversations | Email | SMS | Call    │   │
│  │  Format: JSON/CSV streaming                                         │   │
│  │  Frequency: Real-time + Batch (hourly/daily)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  FEATURE ENGINEERING                                                         │
│  ──────────────────                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │   │
│  │  │ Engagement  │ │  Sentiment  │ │ Lead Aging  │ │   GHL      │   │   │
│  │  │   Features  │ │   Features  │ │   Features  │ │  Features  │   │   │
│  │  │ • Frequency │ │ • Polarity  │ │ • Days idle │ │ • Tags     │   │   │
│  │  │ • Recency   │ │ • Intensity │ │ • Last touch│ │ • Pipeline │   │   │
│  │  │ • Duration  │ │ • Topics    │ │ • Trend     │ │ • Stage    │   │   │
│  │  │ • Response  │ │ • Urgency   │ │ • Aging     │ │ • Owner    │   │   │
│  │  │   Time      │ │             │ │   Score     │ │            │   │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  MODEL TRAINING                                                             │
│  ─────────────                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌──────────────────────┐ ┌──────────────────────┐                 │   │
│  │  │   XGBoost Ensemble   │ │   LightGBM Ensemble │                 │   │
│  │  │  ┌────────────────┐  │ │  ┌────────────────┐  │                 │   │
│  │  │  │ 30-Day Model  │  │ │  │ 30-Day Model  │  │                 │   │
│  │  │  │ Recall-First  │  │ │  │ Recall-First  │  │                 │   │
│  │  │  └────────────────┘  │ │  └────────────────┘  │                 │   │
│  │  │  ┌────────────────┐  │ │  ┌────────────────┐  │                 │   │
│  │  │  │ 60-Day Model  │  │ │  │ 60-Day Model  │  │                 │   │
│  │  │  │ Balanced      │  │ │  │ Balanced      │  │                 │   │
│  │  │  └────────────────┘  │ │  └────────────────┘  │                 │   │
│  │  │  ┌────────────────┐  │ │  ┌────────────────┐  │                 │   │
│  │  │  │ 90-Day Model  │  │ │  │ 90-Day Model  │  │                 │   │
│  │  │  │ Precision-First│  │ │  │ Precision-First│  │                 │   │
│  │  │  └────────────────┘  │ │  └────────────────┘  │                 │   │
│  │  └──────────────────────┘ └──────────────────────┘                 │   │
│  │                                                                       │   │
│  │  Hyperparameter Tuning: Optuna (Bayesian)                           │   │
│  │  Cross-Validation: 5-Fold Stratified                               │   │
│  │  Class Imbalance: SMOTE + Class Weights                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  MODEL INFERENCE                                                            │
│  ──────────────                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌───────────────────────────────────────────────────────────────┐ │   │
│  │  │                    Real-Time Scoring API                       │ │   │
│  │  │  • <100ms p99 latency                                         │ │   │
│  │  │  • Batch scoring for bulk updates                             │ │   │
│  │  │  • Model versioning (A/B testing)                            │ │   │
│  │  │  • Feature importance explanations                            │ │   │
│  │  └───────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  OUTPUT INTERPRETATION                                                      │
│  ─────────────────────                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │   │
│  │  │   Churn     │ │    Risk     │ │   Action    │ │  Re-        │   │   │
│  │  │   Score     │ │   Factors   │ │  Recommend  │ │  engagement │   │   │
│  │  │  (0-100)    │ │  (Top 5)    │ │   (Top 3)   │ │  Priority   │   │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Feature Engineering Pipeline

| Feature Category | Feature Name | Description | Data Source |
|-----------------|--------------|-------------|-------------|
| **Engagement** | `engagement_frequency` | Number of interactions in last 30 days | Bot + GHL |
| | `days_since_last_contact` | Recency of last interaction | GHL |
| | `avg_response_time` | Average response time to leads | Bot system |
| | `conversation_duration` | Total conversation time | Bot system |
| | `message_count` | Total messages exchanged | Bot + GHL |
| | `response_rate` | Lead response rate to outreach | Bot system |
| **Sentiment** | `avg_sentiment_polarity` | Average tone (-1 to 1) | Claude |
| | `sentiment_trend` | Sentiment change over time | Claude |
| | `urgency_indicators` | Detected urgency in messages | Claude |
| | `frustration_signals` | Negative sentiment patterns | Claude |
| **Lead Aging** | `lead_age_days` | Days since lead created | GHL |
| | `idle_days` | Days since last meaningful interaction | Bot + GHL |
| | `aging_score` | Computed aging risk (0-100) | Engine |
| | `reactivation_count` | Previous re-engagement attempts | GHL |
| **GHL CRM** | `pipeline_stage` | Current pipeline position | GHL |
| | `opportunity_value` | Lead potential value | GHL |
| | `tag_count` | Number of tags applied | GHL |
| | `owner_assigned` | Has assigned owner | GHL |
| | `last_activity_type` | Last interaction type | GHL |

---

## Feature Set

### Feature Matrix

| Feature | Description | Priority | Complexity |
|---------|-------------|----------|------------|
| **30-Day Churn Prediction** | Predicts churn risk within 30 days | P0 | High |
| **60-Day Churn Prediction** | Predicts churn risk within 60 days | P0 | High |
| **90-Day Churn Prediction** | Predicts churn risk within 90 days | P0 | High |
| **Real-time Scoring** | Live churn score updates via API | P0 | High |
| **Engagement Metrics** | Track lead engagement patterns | P0 | High |
| **Risk Factor Analysis** | AI-driven churn driver identification | P0 | High |
| **Sentiment Analysis** | Conversation tone monitoring | P0 | Medium |
| **Lead Aging Analysis** | Time-based churn indicators | P0 | Medium |
| **GHL Workflow Triggers** | Automated re-engagement triggers | P0 | High |
| **Bot System Integration** | Integration with Jorge bots | P1 | High |
| **Admin Dashboard** | Churn risk management UI | P1 | Medium |
| **Historical Trend Analysis** | Churn trend visualization | P1 | Medium |
| **Batch Scoring** | Bulk lead scoring jobs | P1 | Medium |
| **A/B Testing** | Model variant testing | P2 | Medium |
| **Custom Thresholds** | Configurable risk thresholds | P2 | Low |

### Churn Risk Classification

| Risk Level | Churn Probability | Action |
|------------|-------------------|--------|
| **Critical** | 80-100% | Immediate outreach, priority workflow |
| **High** | 60-79% | Trigger re-engagement sequence |
| **Medium** | 40-59% | Add to nurture campaign |
| **Low** | 20-39% | Monitor, periodic check-in |
| **Minimal** | 0-19% | Standard follow-up schedule |

### Automated Re-engagement Triggers

| Trigger Condition | Action | Channel |
|-------------------|--------|---------|
| Churn score > 80 | Priority outreach task | GHL Task + SMS |
| Churn score > 60 + 3 days idle | Re-engagement sequence | Bot + Email |
| Sentiment turns negative | Alert sales team | GHL Notification |
| Lead aging > 30 days no contact | Re-activation campaign | Bot |
| Response rate drops 50%+ | Personal outreach suggestion | Dashboard |

---

## Technical Requirements

### AI Integration

| Provider | Model | Use Case | Cost Optimization |
|----------|-------|----------|-------------------|
| **Claude (Anthropic)** | Claude 3.5 Sonnet | Sentiment analysis, content generation | Primary inference |
| **Gemini (Google)** | Gemini Pro | Fast batch processing | Secondary, bulk |
| **XGBoost/LightGBM** | Ensemble | Churn prediction | Local ML |

### Performance Requirements

| Metric | Target | SLA |
|--------|--------|-----|
| Prediction Latency P50 | <50ms | 99.9% |
| Prediction Latency P95 | <80ms | 99.9% |
| Prediction Latency P99 | <100ms | 99.9% |
| Batch Scoring (1000 leads) | <30s | 99% |
| Model Accuracy (AUC) | >0.85 | Monthly eval |
| Model Recall (30-day) | >0.80 | Monthly eval |
| Model Precision (90-day) | >0.75 | Monthly eval |

> **Cold-Start Plan**: Initial deployment uses rule-based heuristics (engagement frequency, days since contact, sentiment thresholds) while the ML model trains on real data. Estimated 3-6 month learning period before ML models reach target accuracy. Rule-based system provides immediate value while training data accumulates.

### GHL CRM Integration

- **Rate Limit**: 10 requests/second
- **Features**:
  - Contact data sync
  - Custom field updates for churn scores
  - Workflow triggers
  - Task creation for at-risk leads
  - Tag management for risk segments
  - Pipeline stage tracking

### Data Storage

| Data Type | Storage | Retention |
|-----------|---------|-----------|
| Lead Features | PostgreSQL | 2 years |
| Churn Scores | Redis (L1) | 24 hours |
| Model Artifacts | S3/Local | Versioned |
| Training Data | PostgreSQL | Unlimited |
| Prediction Logs | PostgreSQL | 1 year |

---

## Deliverables

### 1. Churn Prediction API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/churn/predict` | POST | Get churn prediction for a lead |
| `/api/v1/churn/batch` | POST | Batch score multiple leads |
| `/api/v1/churn/history` | GET | Get historical churn data |
| `/api/v1/churn/factors/{lead_id}` | GET | Get risk factors for lead |
| `/api/v1/churn/webhook` | POST | Receive GHL webhook events |
| `/api/v1/churn/recommendations/{lead_id}` | GET | Get action recommendations |

### 2. Admin Dashboard Features

| Feature | Description |
|---------|-------------|
| Churn Risk Overview | High-level metrics and trends |
| At-Risk Leads List | Sortable/filterable lead table |
| Risk Factor Analysis | Top churn drivers visualization |
| Re-engagement Performance | Campaign effectiveness metrics |
| Model Performance | Accuracy, recall, precision tracking |
| Threshold Configuration | Custom risk level settings |
| Alert Management | Notification preferences |

### 3. Automated Workflows

| Workflow | Trigger | Action |
|----------|---------|--------|
| Critical Risk Alert | Score > 80 | Create GHL task, notify team |
| Re-engagement Sequence | Score > 60 + idle 3 days | Trigger bot sequence |
| Lead Reactivation | Idle > 30 days | Launch re-activation campaign |
| Daily Risk Scan | Scheduled (daily) | Batch score all active leads |
| Sentiment Alert | Negative sentiment detected | Alert sales team |

### 4. Integration Components

| Component | Description |
|-----------|-------------|
| GHL Webhook Handler | Process GHL contact events |
| Bot System Connector | Integrate with Jorge bots |
| Feature Pipeline | Real-time feature updates |
| Model Versioning | A/B testing support |

### 5. Documentation

| Document | Format | Pages |
|----------|--------|-------|
| API Specification | OpenAPI/YAML | - |
| Integration Guide | Markdown | 20+ |
| Admin Dashboard Guide | Markdown | 15+ |
| Model Documentation | Markdown | 10+ |

---

## Success Metrics

### Primary KPIs

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Lead Churn Rate | 65% | 48.75% (-25%) | Monthly GHL data |
| Re-engagement Rate | 15% | 17.25% (+15%) | Bot + GHL metrics |
| Prediction Latency P99 | N/A | <100ms | Prometheus |
| Model AUC Score | N/A | >0.85 | Monthly eval |
| False Positive Rate | N/A | <15% | Validation set |

### Secondary KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| Critical Risk Detection | >80% recall | Test set |
| Re-engagement Conversion | >20% | GHL workflow data |
| Sales Team Time Savings | 15 hrs/week | Team survey |
| Automated Outreach Rate | >60% | Bot metrics |
| Dashboard Active Users | >10 DAU | Analytics |

### Business Impact

Assumes 1,000 active leads, 25% annual churn rate (250 churning leads), $3,600 avg lead value.

| Metric | Conservative (5% churn reduction) | Optimistic (10% churn reduction) |
|--------|-----------------------------------|----------------------------------|
| Leads Saved | 12.5 | 25 |
| Revenue Protected | $45,000 | $90,000 |
| Productivity Gain (15 hrs/wk x $50/hr x 10 agents) | $39,000 | $39,000 |
| **Total Year 1 Value** | **$84,000** | **$129,000** |
| **ROI at $15K cost** | **~460%** | **~760%** |

> **Note**: Actual results depend on client data quality, lead volume, and engagement history. The conservative estimate assumes a 5% reduction in churn rate, which is achievable within 6-12 months of deployment.

---

## Timeline

### Implementation Phases

| Phase | Duration | Focus | Deliverables |
|-------|----------|-------|---------------|
| **Phase 1** | Week 1-2 | Foundation | Data pipeline, Feature engineering, GHL connector |
| **Phase 2** | Week 3-4 | ML Models | XGBoost/LightGBM training, 30/60/90-day models |
| **Phase 3** | Week 5-6 | API & Integration | FastAPI endpoints, webhook handlers, bot integration |
| **Phase 4** | Week 7-8 | Automation | GHL workflow triggers, re-engagement sequences |
| **Phase 5** | Week 9-10 | Dashboard | Streamlit admin UI, metrics visualization |
| **Phase 6** | Week 11-12 | Testing & Deploy | Integration tests, load testing, deployment |

### Milestones

| Milestone | Week | Criteria |
|-----------|------|----------|
| M1: Data Pipeline | Week 2 | Feature extraction working |
| M2: Model Training | Week 4 | AUC > 0.80 on validation |
| M3: API Ready | Week 6 | All endpoints functional |
| M4: Automation Live | Week 8 | GHL triggers operational |
| M5: Dashboard Live | Week 10 | UI deployed and tested |
| M6: Production | Week 12 | Full deployment complete |

---

## Pricing Breakdown

### Project Investment: $15,000

| Component | Cost | Description |
|-----------|------|-------------|
| **ML Development** | $5,500 | Feature engineering, model training, validation |
| **API Development** | $3,500 | FastAPI endpoints, webhook handlers, batch processing |
| **GHL Integration** | $2,500 | CRM connector, workflow triggers, contact sync |
| **Dashboard** | $2,000 | Streamlit admin UI, visualization |
| **Testing & QA** | $1,500 | Unit tests, integration tests, load testing |
| **TOTAL** | **$15,000** | Complete implementation |

### Optional Add-ons

| Add-on | Cost | Description |
|--------|------|-------------|
| Extended Support (6 mo) | $3,000 | Priority support, bug fixes |
| Custom Model Tuning | $2,500 | Industry-specific model refinement |
| Additional Integrations | $2,000 | Slack, email, other CRM |
| Advanced Analytics | $1,500 | Custom dashboard features |

### ROI Projection

| Metric | Conservative | Optimistic |
|--------|-------------|------------|
| Protected Revenue (Year 1) | $45,000 | $90,000 |
| Productivity Savings | $39,000 | $39,000 |
| Total Year 1 Value | $84,000 | $129,000 |
| Investment | $15,000 | $15,000 |
| **ROI** | **~460%** | **~760%** |

> ROI assumes 1,000 active leads with 25% annual churn and $3,600 avg lead value. Conservative = 5% churn reduction; Optimistic = 10% churn reduction.

---

## Appendix

### A. API Response Schema

```json
{
  "lead_id": "string",
  "prediction_timestamp": "ISO8601",
  "churn_predictions": {
    "30_day": {
      "probability": 0.75,
      "risk_level": "HIGH",
      "confidence": 0.88
    },
    "60_day": {
      "probability": 0.82,
      "risk_level": "CRITICAL",
      "confidence": 0.85
    },
    "90_day": {
      "probability": 0.89,
      "risk_level": "CRITICAL",
      "confidence": 0.82
    }
  },
  "risk_factors": [
    {
      "factor": "lead_aging",
      "importance": 0.35,
      "description": "No contact for 45 days"
    },
    {
      "factor": "engagement_decline",
      "importance": 0.28,
      "description": "Message frequency dropped 60%"
    },
    {
      "factor": "sentiment_negative",
      "importance": 0.22,
      "description": "Recent conversations show frustration"
    }
  ],
  "recommendations": [
    {
      "action": "immediate_outreach",
      "priority": 1,
      "channel": "phone",
      "message": "Hi {name}, I wanted to follow up..."
    },
    {
      "action": "schedule_task",
      "priority": 2,
      "description": "Create follow-up task in GHL"
    }
  ]
}
```

### B. Target Model Performance Metrics

> **Note**: These are target performance metrics based on industry benchmarks for similar real estate churn prediction systems. Actual performance depends on client data quality and volume. Minimum 6 months of historical data recommended for reliable model training.

| Model | AUC | Recall | Precision | F1-Score |
|-------|-----|--------|-----------|----------|
| 30-Day XGBoost | 0.87 | 0.82 | 0.75 | 0.78 |
| 30-Day LightGBM | 0.86 | 0.80 | 0.77 | 0.78 |
| 60-Day XGBoost | 0.85 | 0.78 | 0.76 | 0.77 |
| 60-Day LightGBM | 0.84 | 0.76 | 0.78 | 0.77 |
| 90-Day XGBoost | 0.83 | 0.72 | 0.80 | 0.76 |
| 90-Day LightGBM | 0.82 | 0.70 | 0.81 | 0.75 |

### C. Integration Points

| System | Integration Type | Data Flow |
|--------|-----------------|-----------|
| GHL CRM | REST API + Webhooks | Bidirectional |
| Jorge Bots | Python Module | Inbound scoring requests |
| Claude | API | Sentiment analysis |
| PostgreSQL | SQLAlchemy | Feature storage |
| Redis | Direct | Score caching |
| Streamlit | WebSocket | Dashboard updates |

### D. Security Considerations

- **Authentication**: JWT-based API authentication
- **Data Encryption**: PII encrypted at rest (Fernet)
- **Rate Limiting**: 100 requests/minute per client
- **Audit Logging**: All predictions logged with timestamp
- **GDPR Compliance**: Data retention policies enforced

---

> **Document Version**: 1.0  
> **Created**: February 14, 2026  
> **EnterpriseHub Portfolio**
