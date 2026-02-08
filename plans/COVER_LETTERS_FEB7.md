# Cover Letters -- February 7, 2026

Tailored cover letters for Tier 1 job applications.

---

## 1. Prompt Health -- Senior AI Engineer (Natural Language Systems)

Remote US | $160K-$220K

---

My LLM orchestration layer processes real-time natural language with under 200ms of added latency, routes across Claude, Gemini, GPT, and Perplexity, and cut token costs by 89% through a three-tier caching architecture. That system runs in production today, powering lead qualification conversations for a real estate AI platform -- and the engineering problems it solves are the same ones Prompt Health is tackling in clinical speech and language understanding.

I built EnterpriseHub as a full-stack AI platform: FastAPI async backend, PostgreSQL and Redis data layer, Docker Compose deployment, and a multi-agent chatbot system with three specialized bots handling lead qualification, buyer readiness, and seller engagement. The NLP pipeline includes intent decoding with confidence scoring, real-time CRM enrichment that boosts classification accuracy, and a handoff orchestration service with safeguards like circular prevention and rate limiting. Every conversation gets parsed through multiple strategies before a response is generated -- the kind of robustness you need when accuracy directly affects outcomes.

On the evaluation and monitoring side, I built an alerting service with configurable rules and cooldowns, a performance tracker capturing P50/P95/P99 latency with SLA compliance checks, and an A/B testing framework with z-test significance analysis for comparing response strategies. These are production guardrails, not experiments -- they run continuously and flag degradation before it reaches users. The full system is backed by 750+ automated tests across seven repositories, all CI green.

The technical overlap with what Prompt Health needs is direct: real-time NLP pipelines with strict latency requirements, LLM orchestration with cost controls, production monitoring and evaluation infrastructure, and Python/Docker deployment. I am particularly drawn to applying this work in healthcare, where the accuracy and reliability standards I have been engineering against actually matter for patient outcomes.

I would welcome the chance to discuss how my production LLM systems experience maps to your NLP engineering challenges.

Cayman Roden
Palm Springs, CA

---

## 2. Concourse (YC-backed) -- Founding AI/ML Engineer

NYC | $150K-$250K + equity

---

My production stack is Python, FastAPI, PostgreSQL, Redis, and multi-provider LLM APIs -- Claude, Gemini, GPT, and Perplexity -- orchestrated through a custom coordination layer with three-tier caching. When I saw Concourse's technical requirements, the overlap was almost exact: you are building multi-step AI agent workflows for corporate finance on the same foundational stack.

I have spent the past year building EnterpriseHub, a multi-agent AI platform where three specialized chatbots handle lead qualification, buyer readiness assessment, and seller engagement in real estate. The architecture includes cross-bot handoff orchestration with confidence-based routing at a 0.7 threshold, circular prevention, contact-level locking for conflict resolution, and rate limiting. Each bot runs intent decoding pipelines that integrate with CRM data in real-time to boost classification accuracy. The orchestration layer reduced token costs by 89% -- from 93K to 7.8K tokens per workflow -- through intelligent caching across memory, Redis, and PostgreSQL tiers.

Beyond the AI layer, I own the full infrastructure: async FastAPI endpoints, SQLAlchemy models with Alembic migrations, Pydantic validation on every input, JWT authentication, Streamlit BI dashboards for analytics, and Docker Compose for deployment. I built CI/CD pipelines with GitHub Actions across seven open-source repositories totaling 750+ passing tests. This is not prototype-grade work -- it is production engineering with monitoring, alerting, and performance tracking baked in from the start.

What excites me about Concourse is the problem shape: multi-step agent workflows that need to be reliable enough for Fortune 500 finance teams. I have built exactly that kind of system -- agents that coordinate, hand off context, and degrade gracefully -- just in a different domain. The infrastructure translates directly. And as a founding engineer at a YC-backed company with a16z and CRV behind it, the opportunity to shape the technical architecture from the ground up is exactly where I do my best work.

Cayman Roden
Palm Springs, CA

---

## 3. Rula -- Staff AI Engineer (AI Foundation)

Remote US

---

I built a production RAG pipeline with hybrid BM25 and dense retrieval, a multi-agent orchestration system with cross-bot handoff and confidence-based routing, and an evaluation framework with A/B testing and P50/P95/P99 latency tracking -- the three core technical pillars Rula's AI Foundation team is looking to define.

EnterpriseHub is the platform where this comes together: three specialized AI chatbots that qualify leads, assess buyer readiness, and handle seller engagement, all coordinated through a handoff service with a 0.7 confidence threshold, circular prevention, rate limiting, and pattern learning that dynamically adjusts routing based on outcome history. The LLM orchestration layer supports Claude, Gemini, GPT, and Perplexity with a three-tier cache (memory, Redis, PostgreSQL) that reduced token costs by 89%. On top of that, I built the monitoring and evaluation infrastructure -- an alerting service with seven configurable rules, a performance tracker with SLA compliance checks, and an A/B testing service with z-test significance for comparing strategies in production.

The regulated environment aspect is where my experience maps particularly well to healthcare. I have built systems under DRE licensing requirements, Fair Housing Act compliance, CCPA data privacy obligations, and CAN-SPAM regulations. That means PII encryption at rest with Fernet, Pydantic validation on every input boundary, JWT authentication with rate limiting, structured audit trails, and environment-only secret management. Compliance is not a bolt-on in my systems -- it is a design constraint from day one.

Rula's mission to make mental healthcare accessible through technology resonates with me. Building the AI foundation for a platform that serves real patients requires exactly the kind of production discipline I practice: 750+ automated tests, all CI green, with monitoring that catches degradation before it affects users. I would be eager to bring that rigor to a domain where reliability genuinely matters for people's wellbeing.

Cayman Roden
Palm Springs, CA

---

*Last updated: February 7, 2026*
