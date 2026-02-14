# Statement of Work: GHL + RAG Integration Build

---

**Prepared for**: {COMPANY}
**Prepared by**: Cayman Roden
**Date**: {DATE}
**SOW Reference**: {SOW_NUMBER}
**Valid Until**: {EXPIRY_DATE}

---

## 1. Overview

This Statement of Work defines the scope, deliverables, timeline, milestones, and terms for a production AI system integrating GoHighLevel CRM with a custom RAG pipeline, multi-LLM orchestration, and intelligent automation for {COMPANY}'s {USE_CASE_DESCRIPTION}.

---

## 2. Scope of Work

### In Scope

- **Custom RAG Pipeline**: BM25 + semantic search with hybrid score fusion (Reciprocal Rank Fusion), cross-encoder re-ranking, and query expansion. Tuned for {COMPANY}'s document corpus.
- **Multi-LLM Orchestration**: Integration with {LLM_PROVIDERS} with automatic fallback chains, cost-optimized routing, and structured output validation.
- **3-Tier Caching Layer**: L1 in-memory cache, L2 Redis pattern cache, L3 semantic similarity cache. Target: 70%+ cache hit rate.
- **GoHighLevel CRM Integration**: Bidirectional sync via GHL Contact API with rate limiting (10 req/s), error recovery, AI-powered lead scoring, tag management, and workflow triggers.
- **AI Chatbot(s)**: {NUMBER_OF_BOTS} specialized bot(s) with intent detection, confidence-scored handoff orchestration, and enriched context preservation.
- **FastAPI REST API**: Async endpoints with JWT authentication, per-user rate limiting, metering, and structured JSON error responses.
- **Streamlit Dashboard**: BI analytics dashboard with {DASHBOARD_COMPONENTS}.
- **Test Suite**: Minimum 80% code coverage with pytest. Unit, integration, and edge-case tests.
- **Docker Deployment**: Dockerfile + docker-compose configurations for development, staging, and production environments.
- **CI/CD Pipeline**: GitHub Actions workflow with automated testing, linting, and deployment.
- **Architecture Documentation**: Architecture Decision Records (ADRs), Mermaid diagrams, API documentation, and benchmark results.
- **Knowledge Transfer**: 90-minute session covering architecture, maintenance, and extension patterns.
- **Post-Delivery Support**: 4 weeks of bug fixes, configuration adjustments, and production stabilization.

### Out of Scope

- CRM platform subscription fees or API costs
- LLM API costs (OpenAI, Anthropic, Google)
- Cloud hosting and infrastructure costs
- Custom frontend development beyond Streamlit
- Mobile application development
- Data migration from legacy systems (can be quoted separately)
- Ongoing feature development beyond the 4-week support period

---

## 3. Deliverables

| # | Deliverable | Acceptance Criteria |
|---|-------------|-------------------|
| 1 | RAG Pipeline | Hybrid retrieval with >70% precision on {COMPANY}'s test query set. Re-ranking improves relevance by measurable margin. |
| 2 | LLM Orchestration | Multi-provider support with automatic fallback. <500ms orchestration overhead. Cost tracking per request. |
| 3 | Caching Layer | 3-tier implementation. >70% cache hit rate on representative query patterns after warm-up period. |
| 4 | GHL Integration | Bidirectional sync with <5s latency. Rate limiting prevents API throttling. Tag changes trigger workflows within 1 minute. |
| 5 | AI Chatbot(s) | Intent detection accuracy >85% on test conversations. Handoff preserves full conversation context. |
| 6 | REST API | All endpoints documented in OpenAPI spec. JWT auth functional. Rate limiting enforced. P95 response time <2s. |
| 7 | Streamlit Dashboard | All specified components render correctly. Data refreshes within acceptable latency. |
| 8 | Test Suite | >80% code coverage. All tests pass in CI. No critical or high-severity issues. |
| 9 | Docker Deployment | `docker-compose up` brings up a working system in all three environments. |
| 10 | CI/CD Pipeline | Push to main triggers automated test suite. Failures block deployment. |
| 11 | Documentation | ADRs for all major decisions. Mermaid architecture diagrams. API docs. Benchmark results. |
| 12 | Knowledge Transfer | 90-minute recorded session. Written maintenance guide. |

---

## 4. Milestones and Timeline

### Milestone 1: Architecture and Design (Week 1)

**Deliverables**:
- Architecture Decision Records for all major technical choices
- API specification (OpenAPI)
- Data model and schema design
- Infrastructure design (Docker, CI/CD)
- Detailed project plan with task breakdown

**Acceptance**: {COMPANY} reviews and approves architecture design before implementation begins.

### Milestone 2: Core Build (Weeks 2-3)

**Deliverables**:
- RAG pipeline with hybrid retrieval and re-ranking
- LLM orchestration with fallback chains
- 3-tier caching layer
- Core test suite (unit tests for all modules)

**Acceptance**: RAG pipeline returns relevant results for 10 sample queries provided by {COMPANY}. Caching demonstrably reduces LLM API calls.

### Milestone 3: Integration (Weeks 4-6)

**Deliverables**:
- GHL CRM bidirectional sync
- AI chatbot(s) with intent detection and handoff
- Tag management and workflow trigger automation
- Streamlit dashboard with core components
- Integration test suite

**Acceptance**: End-to-end flow from chatbot conversation through CRM update demonstrated. Dashboard displays live data.

### Milestone 4: Hardening and Delivery (Weeks 7-8)

**Deliverables**:
- Performance optimization and benchmarking
- Security hardening (auth, rate limiting, input validation)
- CI/CD pipeline configuration
- Complete documentation package
- Docker deployment configurations (dev/staging/prod)
- Knowledge transfer session

**Acceptance**: All acceptance criteria in Section 3 met. Test suite passes with >80% coverage. Performance benchmarks documented.

---

## 5. Payment Schedule

| Milestone | Percentage | Amount | Due |
|-----------|-----------|--------|-----|
| SOW execution (Kickoff) | 30% | ${MILESTONE_1_AMOUNT} | Upon signing |
| Milestone 2 (Core Build) | 30% | ${MILESTONE_2_AMOUNT} | Upon Milestone 2 acceptance |
| Milestone 3 (Integration) | 20% | ${MILESTONE_3_AMOUNT} | Upon Milestone 3 acceptance |
| Milestone 4 (Delivery) | 20% | ${MILESTONE_4_AMOUNT} | Upon final acceptance |
| **Total** | **100%** | **${TOTAL_AMOUNT}** | |

**Total project investment**: ${TOTAL_AMOUNT}

---

## 6. Requirements from {COMPANY}

1. **GHL API access**: API key with full contact, tag, workflow, and custom field permissions.
2. **LLM API keys**: Active API keys for {LLM_PROVIDERS} with sufficient quota for development and testing.
3. **Document corpus**: Representative sample of documents for RAG pipeline tuning (minimum 50 documents).
4. **Test query set**: 20-30 representative queries with expected answers for retrieval accuracy measurement.
5. **Test conversations**: 10-15 sample conversations for chatbot intent detection validation.
6. **Brand guidelines**: Logo, color palette, and copy style for dashboard customization.
7. **Point of contact**: Designated primary contact responsive within 1 business day for questions and approvals.
8. **Milestone reviews**: Timely review and approval of milestones (within 3 business days of notification).

---

## 7. Acceptance Process

1. Upon completion of each milestone, Cayman Roden will notify {COMPANY} and provide access to deliverables.
2. {COMPANY} has **5 business days** to review deliverables and provide written acceptance or a list of specific deficiencies.
3. Deficiencies that fall within the SOW scope will be addressed within **3 business days**.
4. If no response is received within 5 business days, the milestone is deemed accepted.
5. Acceptance of the final milestone constitutes acceptance of the complete project.

---

## 8. Change Management

Changes to scope, timeline, or deliverables after SOW execution will be handled as follows:

1. Either party submits a written Change Request describing the modification.
2. Cayman Roden provides a written impact assessment (schedule, cost) within 2 business days.
3. Both parties must approve the Change Request in writing before work begins.
4. Approved changes are documented as an addendum to this SOW.

Minor adjustments (reordering tasks, adjusting non-critical UI elements) do not require a formal Change Request.

---

## 9. Terms and Conditions

### Confidentiality

Both parties agree to treat all proprietary information shared during this engagement as confidential, including source code, business data, API credentials, and customer information.

### Intellectual Property

- All custom code, documentation, and configurations produced under this SOW become the property of {COMPANY} upon final payment.
- Open-source libraries and frameworks used retain their original licenses.
- Generic patterns, methodologies, and non-client-specific utilities remain the property of Cayman Roden and may be reused in future engagements.
- Cayman Roden retains the right to reference {COMPANY} as a client and describe the general nature of the engagement in marketing materials, unless {COMPANY} objects in writing.

### Warranty

- Cayman Roden warrants that deliverables will conform to the acceptance criteria specified in Section 3 for a period of **30 days** following final acceptance.
- Defects discovered during the warranty period will be corrected at no additional charge.
- The warranty does not cover issues caused by modifications made by {COMPANY} or third parties after delivery.

### Limitation of Liability

Cayman Roden's total liability under this SOW shall not exceed the total fees paid.

### Cancellation

- Either party may cancel this SOW with 14 days written notice.
- {COMPANY} will be invoiced for all completed milestones plus pro-rated work on the current milestone.
- All completed deliverables will be provided to {COMPANY} upon payment.

---

## 10. Assumptions

1. {COMPANY} will provide all required access and materials within 5 business days of kickoff.
2. GHL API rate limits are sufficient for the planned integration (10 req/s sustained).
3. LLM API quotas are sufficient for development, testing, and production use.
4. Document corpus is in machine-readable format (PDF, DOCX, TXT, MD, or CSV).
5. {COMPANY} has the authority to connect third-party systems (GHL, LLM providers) to the new platform.
6. All communication will be conducted in English via email, Slack, or video call.
7. Milestone reviews will be completed within 5 business days of notification.

---

## 11. Signatures

**Cayman Roden** (Service Provider)

Signature: _________________________

Name: Cayman Roden

Date: _________________________

---

**{COMPANY}** (Client)

Signature: _________________________

Name: {CLIENT_NAME}

Title: {CLIENT_TITLE}

Date: _________________________

---

*This SOW is subject to the terms above. Engagement begins upon execution by both parties and receipt of the initial payment.*
