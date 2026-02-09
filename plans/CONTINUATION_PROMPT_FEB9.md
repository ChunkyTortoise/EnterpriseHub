# Wave 3 Continuation — Feb 9 Evening

**Status**: WS1, WS2, WS4, WS5, s7y, 58t, hfi ALL DONE. Only **WS3** remains.

---

## Verified Complete (code + tests exist in repos)

| Item | Repo | What | Tests |
|------|------|------|-------|
| WS1 (cnq) | EnterpriseHub | BotPersonality ABC, YAML loader, RE/dental personalities | 55 |
| WS2 (lcx) | docqa-engine | Session mgmt, upload UX, demo questions, pipeline.reset() | 15 |
| WS4 (gwn) | EnterpriseHub | CRM Protocol ABC, GHL adapter, HubSpot adapter | 10 |
| WS5 (ia3) | EnterpriseHub | RAG case study (plans/case-study-rag-system.md, 551 lines) | — |
| s7y | EnterpriseHub | Interactive chatbot demo widget (265 lines) | 18 |
| 58t | docqa-engine | REST API wrapper with auth & metering (234 lines) | 20 |
| hfi | ai-orchestrator | REST API + agent templates (157 lines) | 15 |

---

## ONLY REMAINING WORK: WS3 — Streamlit Agent Flow Visualizer

**Repo**: `/Users/cave/Documents/GitHub/ai-orchestrator`
**Parent bead**: `tml` (OPEN)
**Sub-tasks**: `9xu` → `7o9`, `5qn`, `uu2` (all OPEN, 7o9/5qn/uu2 blocked by 9xu)

### What Exists in ai-orchestrator
- `AIOrchestrator` — core class with chat(), stream(), compare()
- 5 providers: Claude, Gemini, OpenAI, Perplexity, Mock
- `ToolRegistry` + `ToolExecutor` for tool chaining
- `agentforge/api.py` — REST API (157 lines, 15 tests)
- 186 tests, CLI interface
- **NO** `agentforge/observability/` directory
- **NO** `streamlit_demo/` directory

### Sub-task Specs

#### 9xu — WS3.1: Event Collection + Trace Dataclasses
Create `agentforge/observability/__init__.py`, `flow_event.py`, `trace_collector.py`:
```python
@dataclass
class FlowEvent:
    timestamp: float
    sequence_id: int
    component: str      # "user", "orchestrator", "provider", "tool"
    event_type: str     # "message", "tool_call", "tool_result", "response"
    content: str
    metadata: dict
    parent_id: int | None = None

@dataclass
class ConversationTrace:
    conversation_id: str
    events: list[FlowEvent]
    total_cost_usd: float
    total_elapsed_ms: float
```
TraceCollector hooks into AIOrchestrator.chat() and ToolRegistry.execute(). Non-intrusive (disabled by default, enabled via `trace=True`).

#### 7o9 — WS3.2: Streamlit Flow Diagram Component
Create `streamlit_demo/app.py`, `streamlit_demo/components/flow_diagram.py`:
- Timeline: User → Provider → Tool → Result → Response
- Color-coded nodes (green=success, blue=tool, orange=fallback, red=error)
- Click-to-inspect node details

#### 5qn — WS3.3: Metrics Dashboard + Message Inspector
Create `streamlit_demo/components/message_inspector.py`, `metrics_dashboard.py`:
- Full prompt/response content on click
- Provider latency comparison, cost breakdown, tool execution frequency

#### uu2 — WS3.4: Tests (~15 tests)
Create `tests/test_flow_visualization.py`:
- Event collection captures all flow steps
- Trace serialization to JSON
- Streamlit component data preparation
- Mock provider traces

### Execution Order
```bash
bd update 9xu --status=in_progress    # Implement WS3.1
# ... code ...
bd close 9xu                          # Unblocks 7o9, 5qn, uu2
bd update 7o9 5qn --status=in_progress # Implement WS3.2 + WS3.3 in parallel
# ... code ...
bd update uu2 --status=in_progress    # Write tests
# ... code ...
bd close 7o9 5qn uu2 tml
bd sync && git push                    # ai-orchestrator repo
```

### Session Close Checklist
```
[ ] python -c "from agentforge.observability import FlowEvent, ConversationTrace, TraceCollector"
[ ] pytest tests/test_flow_visualization.py -v
[ ] ruff check agentforge/observability/ streamlit_demo/
[ ] bd close 9xu 7o9 5qn uu2 tml
[ ] bd sync
[ ] cd /Users/cave/Documents/GitHub/ai-orchestrator && git add . && git commit && git push
[ ] Update MEMORY.md
```

---

## Open Beads Summary

### Dev Work (WS3 only)
| Bead | Description | Status |
|------|-------------|--------|
| `tml` | WS3 parent: ai-orchestrator flow visualizer | OPEN |
| `9xu` | WS3.1: Event collection + trace dataclasses | OPEN (blocks 7o9, 5qn, uu2) |
| `7o9` | WS3.2: Streamlit flow diagram | OPEN (blocked by 9xu) |
| `5qn` | WS3.3: Metrics dashboard + inspector | OPEN (blocked by 9xu) |
| `uu2` | WS3.4: Tests (~15) | OPEN (blocked by 9xu) |

### Human Action Items
| Bead | Description |
|------|-------------|
| `4j2` | Upwork: Buy Connects + submit Round 2 proposals |
| `9je` | LinkedIn: Send 3-5 recommendation requests |
| `pbz` | LinkedIn: Weekly content cadence |
| `vp9` | Upwork: Profile improvements |

---

## Job Search Pipeline
| # | Company | Role | Status |
|---|---------|------|--------|
| 1 | FloPro Jamaica (Chase) | AI Secretary SaaS | Awaiting contract offer |
| 2 | Kialash Persad | Sr AI Agent Eng | **Call Tue Feb 10 4PM EST** |
| 3 | Code Intelligence | RAG/LLM Engineer | Viewed by client |
| 4 | Concourse | Founding AI/ML | YC signup needs password |
| 10 | Prompt Health | Sr AI Engineer | Submitted |
| 11 | Rula | Principal AI Eng | Submitted |
