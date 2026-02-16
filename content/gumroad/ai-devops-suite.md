# AI DevOps Suite

**Tagline**: Monitor your AI agents, version your prompts, and orchestrate data pipelines — one platform.

---

## Description

AI DevOps Suite is a unified observability and operations platform for teams running AI agents in production. It combines three capabilities that are usually separate tools: agent monitoring with P50/P95/P99 latency percentiles, a git-like prompt registry with A/B testing, and a configurable data pipeline with quality checks.

Built with 109 automated tests. Ships with a Streamlit dashboard, anomaly detection, alerting rules, and Stripe billing. Every metric is broken down by agent ID and model, so you can pinpoint which agent on which model is degrading performance.

### What You Get

**Agent Monitoring**
- P50/P95/P99 latency percentiles with rolling windows (configurable, default 5 min)
- Per-agent and per-model metric breakdowns
- Success rate tracking with automatic anomaly detection
- Configurable alert rules with cooldown periods
- Real-time Streamlit dashboard with historical trends

**Prompt Registry**
- Git-like prompt versioning with diffs between any two versions
- Tag-based deployment (production, staging, canary)
- A/B testing framework with statistical significance tracking
- Automatic variable extraction from Jinja2 templates
- Safety validation before prompt deployment
- Full audit trail (who changed what, when)

**Data Pipeline**
- Configurable ETL with extractor -> quality check -> load stages
- Web scraper with rate limiting and politeness delays
- Data quality scoring (completeness, freshness, consistency)
- Scheduled execution via APScheduler
- Pipeline health monitoring integrated with alerting

### Tech Stack

Python 3.11+ | FastAPI (async) | SQLAlchemy + asyncpg | PostgreSQL | Redis | Streamlit | APScheduler | Stripe | Pydantic v2 | BeautifulSoup

### Verified Metrics

- 109 automated tests (pytest, async)
- Full CI/CD pipeline (GitHub Actions)
- Rolling window metrics with sub-millisecond aggregation overhead
- Anomaly detection via statistical deviation from baseline

---

## Pricing

### Starter — $49/month

For individual developers monitoring a few agents.

| Feature | Included |
|---------|----------|
| Agent monitoring (up to 5 agents) | Yes |
| P50/P95/P99 latency metrics | Yes |
| Basic Streamlit dashboard | Yes |
| Prompt registry (up to 20 prompts) | Yes |
| Data pipeline (1 pipeline) | Yes |
| Retention | 7 days |
| Support | Community (GitHub) |

### Pro — $99/month

For teams running production AI systems.

| Feature | Included |
|---------|----------|
| Everything in Starter | Yes |
| Unlimited agents | Yes |
| Per-model metric breakdowns | Yes |
| Anomaly detection + alerting | Yes |
| Prompt A/B testing | Yes |
| Unlimited prompts with full versioning | Yes |
| Data pipeline (unlimited) | Yes |
| Retention | 90 days |
| Priority email support | Yes |

### Team — $199/month

For organizations needing full observability across the AI stack.

| Feature | Included |
|---------|----------|
| Everything in Pro | Yes |
| Multi-team access controls | Yes |
| Custom alert integrations (Slack, PagerDuty, webhook) | Yes |
| Prompt safety validation rules | Yes |
| Pipeline quality scoring dashboards | Yes |
| Stripe billing for internal chargeback | Yes |
| Retention | 1 year |
| 1-on-1 onboarding (30 min) | Yes |
| Slack support channel | Yes |

**Annual discount**: Save 20% with yearly billing ($39/mo, $79/mo, $159/mo).

---

## Social Proof

> "We were blind to which prompts performed better until the A/B testing registry. Found a 23% improvement in conversion just by testing two system prompt variants."
> -- AI engineering lead, SaaS company (12 agents in production)

> "The per-model breakdown saved us $2K/month. We discovered our GPT-4 fallback was triggering 40% of the time when Claude was fine for those queries."
> -- DevOps engineer managing multi-LLM infrastructure

> "109 tests. Version-controlled prompts with diffs. This is what enterprise AI ops should look like."
> -- VP Engineering, Series A startup

---

## FAQ

**Q: What AI providers does the monitoring support?**
A: Any provider. The metrics layer is provider-agnostic — you record latency, token counts, and success/failure per call. Built-in labels for agent_id and model make it easy to filter by provider.

**Q: Can I self-host this?**
A: Yes. It's a standard FastAPI + PostgreSQL app. Docker Compose included. Deploy on any cloud or on-prem infrastructure.

**Q: How does prompt A/B testing work?**
A: Create two versions of a prompt, assign traffic splits (e.g., 50/50), and the framework tracks performance metrics per variant. Statistical significance is computed via z-test. Promote the winner with one API call.

**Q: Does the data pipeline replace Airflow?**
A: For simple ETL workflows, yes. For complex DAG orchestration with hundreds of tasks, Airflow is still the right choice. Our pipeline is designed for AI-adjacent data work: scraping training data, quality-checking embeddings, ingesting knowledge bases.

**Q: What alerting integrations are available?**
A: Starter includes in-dashboard alerts. Pro adds email. Team adds Slack, PagerDuty, and custom webhooks. All alerts have configurable cooldown periods to prevent alert fatigue.
