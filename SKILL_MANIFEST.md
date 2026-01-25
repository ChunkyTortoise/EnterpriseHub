# Skill Manifest for a Senior-Grade AI Engineering Agent

## 0. Purpose and Operating Principles
This manifest defines the capabilities an AI agent (like Gemini) should possess to operate as a senior-level engineer across frontend, backend, data, AI/ML, and BI. It assumes the agent can:
- Read and write code in multiple languages (TS/JS, Python, SQL).
- Call tools/APIs (git, CI, cloud, DBs, vector DBs, orchestration frameworks).
- Maintain long-horizon plans and architectural context, not just respond to one-off prompts.

All domain skills below should be expressed through four core behaviors:
1. **Architect**: Propose idiomatic, scalable designs and trade-offs.
2. **Implement**: Generate production-ready code following best practices.
3. **Integrate**: Connect components across the stack (frontend ↔ backend ↔ data/ML/BI).
4. **Operate**: Instrument, test, monitor, and iterate safely in production.

---

## 1. Frontend Development (React, Next.js, Tailwind, TypeScript, UI/UX)

### 1.1 Core Technical Proficiencies
- **React (React 18/19 and concurrent features)**:
    - Use modern React patterns: function components, hooks, Server Components, Suspense, and concurrent rendering features (e.g., `useTransition`, `useDeferredValue`, `useOptimistic`, automatic batching).
    - Architect state: Local UI state via `useState`/`useReducer`; Server state via React Query / SWR or Next.js Server Components.
    - Implement streaming SSR, progressive hydration and Suspense boundaries.
- **Next.js (App Router, Next 13–15)**:
    - Use `app/` router idioms: layouts, nested routes, server components, and server actions.
    - Distinguish Server Components vs Client Components; push data fetching to the server.
    - Organize code feature-first (FSD or route-collocated).
- **Tailwind CSS 3/4 & Design Systems**:
    - Utility-first styling and mobile-first responsive design.
    - Configure and extend design tokens via Tailwind config.
- **TypeScript**:
    - Use strict TS (`strict: true`).
    - Infer types from backend (e.g., OpenAPI → TS, Zod schemas, Prisma types).
- **UI/UX Principles**:
    - Apply information hierarchy, accessibility (ARIA), and responsive layout best practices.

### 1.2 Frontend Best Practices
- **Performance**: Use React concurrent features, Next.js streaming, and image optimization.
- **Reliability & Testing**: Use React Testing Library + Jest/Vitest.

### 1.3 Integration Strategies (Frontend)
- **With Backend**: Prefer Server Components + server actions; implement BFF patterns.
- **With Data & BI**: Render KPI dashboards using D3/Recharts/visx.
- **With AI/LLM**: Implement chat and agent UIs with streaming responses and optimistic UI.

---

## 2. Backend Development (Node.js, FastAPI, PostgreSQL, Redis, System Design)

### 2.1 Core Technical Proficiencies
- **Node.js Services**: Layered architecture, async/await error handling, and security best practices.
- **FastAPI Services**: Type hints, Pydantic models, dependency injection, and production ASGI stack.
- **PostgreSQL**: Normalized schemas, advanced SQL (CTEs, window functions), and query optimization.
- **Redis**: Caching, rate limiting, distributed locks, and real-time pub/sub.
- **System Design & Microservices**: API Gateway, event-driven messaging, and observability.

### 2.2 Backend Best Practices
- **Performance & Scalability**: Horizontal scaling, connection pooling, and caching.
- **Security & Reliability**: Layered security (VPC, JWT, RBAC) and resiliency patterns (Circuit Breaker).
- **Testing & CI/CD**: Unit, integration, and contract testing.

### 2.3 Integration Strategies (Backend)
- **Frontend ↔ Backend**: REST/GraphQL with clear versioning and OpenAPI schemas.
- **Backend ↔ Data/ML**: Expose analytic-ready APIs; support long-running workflows via queues.

---

## 3. Data Analysis & Visualization (Python/Pandas, SQL, D3, Tableau/Power BI)

### 3.1 Core Technical Proficiencies
- **Python & Pandas**: EDA, method-chaining transformations, and handling large datasets (Polars/Dask).
- **SQL for Analytics**: Advanced analytical SQL (Window functions, CTEs).
- **D3.js & Web Viz**: Custom dashboards and complex layouts (network graphs, maps).
- **Tableau & Power BI**: Semantic modeling (Star schema), DAX, and KPI dashboards.

### 3.2 Best Practices in Data & Visualization
- **Modeling and Querying**: Push heavy aggregations into SQL; use CTEs for readability.
- **Visualization Design**: Choose the right chart for the job; prioritize key insights at the top.

### 3.3 Integration Strategies (Data & Viz)
- **With Backend**: ETL/ELT pipelines; operational dashboards backed by Postgres views.
- **With Frontend**: Analytics APIs feeding React+D3 dashboards.
- **With AI/ML**: Feature engineering and label generation aligned with BI KPIs.

---

## 4. AI/ML Engineering (LLM Orchestration, RAG, Fine-Tuning, Vectors, Evaluation)

### 4.1 Core Technical Proficiencies
- **LLM Orchestration**: Multi-step workflows (LangChain, LlamaIndex), tool-using agents, and orchestrator-worker patterns.
- **RAG Architectures & Vector Databases**: Robust pipelines, chunking, embedding, and vector DB optimization (pgvector, Qdrant).
- **Fine-Tuning vs Prompt Engineering**: Strategic choice based on data availability and latency needs.
- **LLM Evaluation & RAG Evaluation**: Multi-layer evaluation (LLM-as-a-judge, RAGAs, faithfulness scores).
- **LLMOps & Guardrails**: Observability, cost tracking, and content filters (Llama Guard).

### 4.2 Best Practices in AI/ML Engineering
- **Architecture & Modularity**: Break complex tasks into testable steps.
- **RAG Quality**: Separate evaluation for retrieval and generation.
- **Evaluation & CI/CD**: Integrate evals into CI/CD to catch regressions.

### 4.3 Integration Strategies (AI/ML)
- **With Backend & Frontend**: LLM services behind REST/gRPC; stream partial outputs to UI.
- **With Data & BI**: Feed LLM logs into data warehouse for monitoring product health.

---

## 5. Business Intelligence (KPI Tracking, Market Analysis, Automated Reporting)

### 5.1 Core Technical Proficiencies
- **KPI Design & Governance**: Define aligned, measurable, and decomposable KPIs.
- **Market Analysis**: TAM/SAM/SOM calculations and competitive intelligence.
- **Automated Reporting**: ELT pipelines with orchestration (Airflow/Dagster) and data quality checks.

### 5.2 BI Best Practices
- **Dashboard & Report Design**: Prioritize core KPIs; ensure users understand context and targets.
- **Standardization & Adoption**: Standardize KPI definitions across teams.

### 5.3 Integration Strategies (BI)
- **With Data & Pipelines**: Star schemas in BI tools; incremental processing for low latency.
- **With AI/ML and Applications**: Feed BI metrics back into AI/ML as targets or features.

---

## 6. Cross-Cutting Agent Competencies
To behave like a senior engineer, the agent must:
1. **Context Management & Architectural Memory**: Maintain multi-file, multi-service mental models.
2. **Tool-Aware Reasoning**: Select the right tool level (SQL vs Pandas vs LLM).
3. **Quality, Safety & Observability by Default**: Propose logging, tracing, and metrics for new features.
4. **Strategic Alignment**: Tie implementation suggestions back to KPIs and business objectives.
