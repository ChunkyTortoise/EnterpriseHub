# EnterpriseHub Product Suite Walkthrough

**Duration**: 6 minutes 30 seconds
**Format**: Screen recording with voiceover
**Tools**: OBS Studio or Loom, VS Code, terminal, browser (Streamlit dashboards)

---

## Section 1: Intro (0:00 - 0:30)

**Screen**: GitHub repo overview (EnterpriseHub monorepo, showing 5 product directories)

**Script**:

"This is EnterpriseHub — a suite of 5 AI products built for real estate and SaaS operations. Voice AI agents, a multi-tenant RAG platform, AI monitoring, MCP servers, and the shared infrastructure that ties them together.

Everything you're about to see has automated tests, CI/CD pipelines, and Docker deployment. This is production code, not a prototype.

Let me walk you through each product."

**Speaker Notes**:
- Keep energy high but technical. This audience is engineers and agency owners.
- Show the monorepo structure briefly: voice-ai-platform/, rag-as-a-service/, ai-devops-suite/, mcp-server-toolkit/, shared-schemas/

**Transition**: Cut to VS Code with voice-ai-platform source open

---

## Section 2: Architecture Overview (0:30 - 1:30)

**Screen**: VS Code showing the monorepo structure, then switch to a Mermaid architecture diagram (render in browser)

**Script**:

"The architecture follows a clean separation. Each product is a standalone FastAPI service with its own database schema, test suite, and CI pipeline. They share common infrastructure through the shared-schemas package — Pydantic v2 models for multi-tenant isolation, auth, billing, and events.

[Switch to Mermaid diagram]

Here's how data flows: A voice call comes in through Twilio, hits the Voice AI Pipeline where Deepgram transcribes in real-time, Claude generates the response, and ElevenLabs converts it to speech. All contact data syncs back to GoHighLevel.

Meanwhile, the RAG service handles document-backed conversations — each tenant gets schema-isolated storage in PostgreSQL with pgvector. The MCP toolkit connects AI assistants like Claude Desktop directly to GHL, databases, and files.

Everything is monitored by the AI DevOps Suite — P50, P95, P99 latency per agent, per model.

The shared-schemas package provides tenant lifecycle, JWT auth, Stripe billing, and rate limiting that every product inherits."

**Speaker Notes**:
- Have the Mermaid diagram pre-rendered in a browser tab
- Show the pyproject.toml briefly to demonstrate the dependency chain
- Keep it high-level — details come in product-specific sections

**Transition**: Cut to voice-ai-platform/src/voice_ai/pipeline/voice_pipeline.py

---

## Section 3: Voice AI Demo (1:30 - 3:00)

**Screen**: VS Code showing voice_pipeline.py, then switch to terminal running tests, then Streamlit dashboard

**Script**:

"Voice AI Platform handles real-time phone conversations. Let me show you the core pipeline.

[Show voice_pipeline.py]

This is the voice pipeline — STT, LLM, TTS orchestrated as an async data flow. Audio comes in from Twilio via WebSocket, streams to Deepgram for transcription, feeds the transcript to Claude for response generation, and streams the response through ElevenLabs back to the caller.

The key feature is barge-in support. If the caller starts speaking while the bot is talking, TTS is cancelled immediately and the pipeline switches back to listening. This is what makes it feel like a real conversation instead of a voicemail tree.

[Switch to terminal]

66 automated tests covering the pipeline, telephony, services, and API layers. Let me run them.

[Run: pytest voice-ai-platform/tests/ --tb=short -q]

[Switch to services directory]

The platform also includes PII detection — strips Social Security numbers, credit cards, and phone numbers before anything hits storage. Sentiment tracking flags frustrated callers for human escalation. And calendar booking auto-schedules appointments through the GHL calendar API.

[Show Streamlit dashboard if available, or show dashboard/ directory]

The Streamlit dashboard gives you real-time call analytics — active calls, average handling time, sentiment trends, and conversion funnels."

**Speaker Notes**:
- Run tests live if they pass quickly; otherwise show pre-recorded output
- Highlight the barge-in code specifically — it's a differentiator
- If dashboard isn't running, show the component files and describe them
- Mention: "66 tests, not 6 — this is production-grade"

**Transition**: Cut to rag-as-a-service/src/rag_service/core/rag_engine.py

---

## Section 4: RAG Demo (3:00 - 4:00)

**Screen**: VS Code showing rag_engine.py, multi-tenant isolation, then terminal

**Script**:

"RAG-as-a-Service is a multi-tenant retrieval-augmented generation platform. Each tenant — each client — gets their own isolated schema in PostgreSQL. No data leakage.

[Show rag_engine.py]

The RAG engine runs a 4-stage pipeline: query expansion generates multiple search variants for better recall, pgvector handles semantic search, results get reranked, then the LLM generates a cited answer with source references.

[Show multi_tenant/isolation.py]

This is the tenant isolation middleware. It extracts the tenant from the API key header, resolves the tenant's schema, and sets the database search path. Every query is scoped to that tenant's data automatically.

[Show compliance/pii_detector.py briefly]

PII detection runs before documents enter the vector store. SSNs, credit card numbers, emails — detected and redacted before embedding.

[Switch to terminal — run test count]

120 automated tests across the RAG engine, multi-tenant isolation, compliance, billing, and API layers.

This is what you'd sell as a knowledge base API to your clients. Upload their documents, they get an intelligent search endpoint. Stripe billing handles the metering."

**Speaker Notes**:
- Focus on multi-tenancy as the differentiator — most RAG tools are single-tenant
- Show the TIER_LIMITS from shared-schemas if time permits
- Mention "pgvector inside PostgreSQL — no separate vector DB to manage"

**Transition**: Cut to ai-devops-suite source

---

## Section 5: DevOps Suite Demo (4:00 - 5:00)

**Screen**: VS Code showing metrics.py, prompt versioning, then Streamlit dashboard

**Script**:

"AI DevOps Suite solves a problem every team running AI agents hits: you don't know when things are degrading until a user complains.

[Show monitoring/metrics.py]

This metrics aggregator tracks P50, P95, and P99 latency with rolling windows. Every metric is labeled by agent ID and model, so you can pinpoint which agent on which model is causing issues.

[Show prompt_registry/versioning.py]

The prompt registry versions your prompts like git versions code. Create a version, tag it for production, diff between versions, and run A/B tests. The A/B framework uses z-tests for statistical significance — no more guessing which prompt is better.

[Show monitoring/anomaly.py briefly]

Anomaly detection flags metrics that deviate from baseline. Combined with configurable alerting rules and cooldown periods, you get actionable alerts without fatigue.

[Switch to terminal — run tests]

109 tests. Streamlit dashboard included for real-time monitoring.

If you're running more than 2 AI agents in production, you need observability. This is it."

**Speaker Notes**:
- Show a test run or test count
- The prompt versioning diff feature is visually interesting — highlight it
- Keep the anomaly detection explanation brief

**Transition**: Cut to mcp-server-toolkit source

---

## Section 6: MCP Toolkit Demo (5:00 - 5:45)

**Screen**: VS Code showing base_server.py, then server directory listing, then CRM server

**Script**:

"MCP Server Toolkit is for teams building AI tool integrations. MCP — Model Context Protocol — is the standard that lets Claude, GPT, and other AI assistants call external tools.

[Show base_server.py]

The core is EnhancedMCP. It extends the official FastMCP with three things every production server needs: caching, rate limiting, and telemetry. One decorator and your tool responses are cached. Another decorator and per-caller rate limits are enforced.

[Show server directory listing — 7 servers]

The toolkit ships with 7 pre-built servers: GoHighLevel CRM, database queries with natural language to SQL, analytics with chart generation, calendar scheduling, email with templates, file processing for PDF and DOCX, and web scraping with rate limiting.

[Show crm_ghl/server.py briefly]

The GHL server maps contacts, fields, and pipelines. Combined with the caching layer, you avoid hitting GHL's rate limits even during bulk operations.

190 tests across the full toolkit. These servers work with Claude Desktop, Cursor, and any MCP-compatible client."

**Speaker Notes**:
- Show the cached_tool decorator — it's the "aha" moment
- List the 7 servers quickly — the breadth is impressive
- Mention: "190 tests for MCP servers — nobody else tests their MCP tools this thoroughly"

**Transition**: Cut to pricing slide (pre-made graphic or markdown)

---

## Section 7: Pricing & CTA (5:45 - 6:30)

**Screen**: Pricing comparison table (pre-rendered), then contact information

**Script**:

"Here's the pricing for the full suite.

[Show pricing table]

Voice AI Platform starts at $99/month. RAG-as-a-Service at $99/month. AI DevOps Suite at $49/month. MCP Toolkit at $29/month for all-access. And Shared Schemas is free and open source — MIT licensed.

Every product has a 14-day trial. Annual plans save 20%.

Enterprise tiers include white-label dashboards, Stripe billing integration so you can resell to your own clients, and a 1-on-1 onboarding call.

[Show contact info]

If you're a GHL agency, a SaaS builder, or an AI team that needs production infrastructure — not demos — check out the links below. I'm available for custom deployments, consulting, and ongoing support.

I'm Cayman Roden, AI Automation Engineer. You can reach me at caymanroden@gmail.com or find me on GitHub at ChunkyTortoise.

Thanks for watching."

**Speaker Notes**:
- Have pricing table pre-rendered (use the pricing-tables.md file)
- Speak the prices clearly — this is where the viewer decides to click
- End on the GitHub link — engineers want to see code, not landing pages
- Total runtime should be around 6:15-6:30

---

## Production Notes

- **Resolution**: 1920x1080, 30fps
- **Audio**: External mic, normalize to -14 LUFS
- **Code font**: JetBrains Mono or Fira Code, 16pt minimum for readability
- **VS Code theme**: Dark (Dracula or One Dark Pro) — high contrast for screen recording
- **Browser tabs**: Pre-open all pages before recording. No live loading.
- **Terminal**: Use a clean shell with minimal prompt. No personal info visible.
- **Pacing**: Aim for conversational speed. Pause briefly between sections.
- **B-roll**: Consider split-screen showing code on left, diagram on right during architecture section
