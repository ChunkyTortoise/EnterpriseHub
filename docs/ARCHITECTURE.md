# EnterpriseHub Architecture

## System Overview
```mermaid
graph LR
  UI[Streamlit UI] --> API[FastAPI API]
  API --> DB[(Postgres)]
  API --> Cache[(Redis)]
  API --> Vector[(Vector Store)]
  API --> Agents[AgentForge Services]
  Agents --> RAG[Advanced RAG System]
  Worker[Background Worker] --> DB
  Worker --> Cache
```

## Agent Orchestration Flow
```mermaid
graph TD
  Planner --> Researcher --> Reviewer --> Publisher
  Reviewer --> Researcher
```

## Data Flow
```mermaid
graph TD
  Ingest[Inbound Leads & Events] --> API
  API --> Models[SQLAlchemy Models]
  Models --> DB
  API --> Agents
  Agents --> RAG
  RAG --> Vector
  Agents --> Response[Responses & Actions]
  Response --> API
```

## Deployment Topology
```mermaid
graph TD
  LB[Load Balancer] --> API[API Service]
  API --> DB[(Postgres)]
  API --> Cache[(Redis)]
  API --> Vector[(Vector Store)]
  API --> Worker[Worker Service]
  UI[Streamlit UI] --> API
```

## Key Subsystems
- **AgentForge**: Multi-agent orchestration with LangGraph state management.
- **Advanced RAG**: Hybrid retrieval, reranking, citations, and conversational memory.
- **Smart Analyst**: NL2SQL, data grid, self-healing Python execution, PDF reporting.
- **Observability**: Metrics + health endpoints for operational readiness.
