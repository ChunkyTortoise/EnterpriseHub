# AgentForge Screenshot Specifications

**Product**: AgentForge (ai-orchestrator)
**Live Demo**: https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/
**Gumroad**: Tiered ($49 / $199 / $999)
**Total Screenshots**: 7

---

## Screenshot 1: Hero Dashboard Overview

| Property | Value |
|----------|-------|
| **Filename** | `agentforge-dashboard-hero.png` |
| **Dimensions** | 1920x1080 (capture), 1280x720 (Gumroad), 800x450 (README) |
| **Source** | Streamlit app main page |
| **UI Elements to Show** | Sidebar navigation, main metrics row, execution trace panel |
| **Highlight Boxes** | Red box around metrics row (KPI strip showing cost savings, latency, throughput) |
| **Callout Numbers** | (1) Provider status indicators, (2) Cost savings metric, (3) Trace viewer |
| **Caption** | "Multi-provider AI orchestration with real-time cost tracking" |
| **Context** | First impression screenshot; shows the breadth of the platform at a glance |
| **Dark Mode** | Yes (Obsidian theme) |

### Annotation Placement
```
┌──────────────────────────────────────────────────┐
│  AgentForge Dashboard                            │
├─────────┬────────────────────────────────────────┤
│ Sidebar │  ┌─(1)──────────────────────────────┐  │
│ - Home  │  │  Provider: Claude  Gemini  GPT-4 │  │
│ - Trace │  └──────────────────────────────────┘  │
│ - Bench │  ┌─────────┐ ┌──(2)───┐ ┌──────────┐  │
│ - Cost  │  │ Requests│ │ Saved  │ │ Latency  │  │
│         │  │  1,247  │ │ $847  ↓│ │  142ms   │  │
│         │  └─────────┘ └────────┘ └──────────┘  │
│         │  ┌──(3)─────────────────────────────┐  │
│         │  │  Execution Trace                 │  │
│         │  │  ├─ Provider Selection            │  │
│         │  │  ├─ Tool Dispatch                 │  │
│         │  │  └─ Response Merge                │  │
│         │  └──────────────────────────────────┘  │
│         │  [Caption: Multi-provider AI...]       │
└─────────┴────────────────────────────────────────┘
```

---

## Screenshot 2: Provider Benchmark Comparison

| Property | Value |
|----------|-------|
| **Filename** | `agentforge-provider-benchmark.png` |
| **Dimensions** | 1920x1080 / 1280x720 / 800x450 |
| **Source** | Streamlit app benchmark page (or generate from benchmark data) |
| **UI Elements to Show** | Bar chart comparing Claude vs GPT-4 vs Gemini on latency, cost, quality |
| **Highlight Boxes** | Red box around the "winner" column showing AgentForge's optimal routing |
| **Callout Numbers** | (1) Latency comparison bars, (2) Cost per 1K tokens, (3) Quality score |
| **Caption** | "Automatic provider routing: 89% cost reduction vs single-provider" |
| **Context** | Key differentiator; shows why multi-provider matters |

---

## Screenshot 3: Cost Savings Dashboard

| Property | Value |
|----------|-------|
| **Filename** | `agentforge-cost-savings.png` |
| **Dimensions** | 1920x1080 / 1280x720 / 800x450 |
| **Source** | Cost tracking view within Streamlit or generated Plotly chart |
| **UI Elements to Show** | Line chart (monthly cost before vs after), cumulative savings counter |
| **Highlight Boxes** | Red box around cumulative savings total |
| **Callout Numbers** | (1) "Before" line ($18.5K/mo), (2) "After" line ($6.2K/mo), (3) Savings: $147K/yr |
| **Arrow** | Amber arrow from "Before" to "After" showing gap |
| **Caption** | "LegalTech case study: $147K annual savings validated" |
| **Context** | Ties directly to the LegalTech case study in the repo |

---

## Screenshot 4: Agent Mesh Topology

| Property | Value |
|----------|-------|
| **Filename** | `agentforge-agent-mesh.png` |
| **Dimensions** | 1920x1080 / 1280x720 / 800x450 |
| **Source** | Architecture diagram (Mermaid rendered to PNG or Plotly network graph) |
| **UI Elements to Show** | Network graph showing agents, tool dispatch routes, handoff connections |
| **Highlight Boxes** | Red box around the mesh coordinator node |
| **Callout Numbers** | (1) Coordinator, (2) Worker agents, (3) Tool dispatch paths, (4) Fallback routes |
| **Caption** | "Production-ready multi-agent mesh with governance and auto-scaling" |
| **Context** | Shows enterprise architecture; differentiates from simple chain-based tools |

---

## Screenshot 5: CLI Quick Start

| Property | Value |
|----------|-------|
| **Filename** | `agentforge-cli-quickstart.png` |
| **Dimensions** | 1920x600 (wide terminal, shorter height) / 1280x400 (Gumroad) |
| **Source** | Terminal screenshot (iTerm2 or VS Code terminal, dark theme) |
| **UI Elements to Show** | 5-line install + first API call with colored output |
| **Highlight Boxes** | Green box (`#10B981`) around the successful response output |
| **Callout Numbers** | (1) `pip install agentforge`, (2) 3-line Python script, (3) Response with cost shown |
| **Caption** | "From install to first API call in under 5 minutes" |
| **Context** | Developer-focused; shows ease of getting started |

### Terminal Content to Display
```
$ pip install agentforge
Successfully installed agentforge-1.2.0

$ python -c "
from agentforge import Agent
agent = Agent(providers=['claude', 'gpt4'])
result = agent.run('Summarize this contract...')
print(f'Response: {result.text[:80]}...')
print(f'Cost: ${result.cost:.4f} | Latency: {result.latency_ms}ms')
"
Response: This contract establishes a commercial lease agreement between...
Cost: $0.0032 | Latency: 142ms | Provider: claude-3-haiku (auto-selected)
```

---

## Screenshot 6: Test Suite Dashboard

| Property | Value |
|----------|-------|
| **Filename** | `agentforge-test-suite.png` |
| **Dimensions** | 1920x800 / 1280x530 / 800x450 |
| **Source** | Terminal screenshot of pytest output or CI badge summary |
| **UI Elements to Show** | pytest summary showing 494 tests passing, coverage %, module breakdown |
| **Highlight Boxes** | Green box around "494 passed" line |
| **Callout Numbers** | (1) Test count, (2) Coverage percentage, (3) Zero failures |
| **Caption** | "494 tests across 29 modules -- production-grade quality assurance" |
| **Context** | Trust signal; shows this is not a toy project |

### Terminal Content to Display
```
$ pytest --tb=short -q
...............................................................
...............................................................
...............................................................  [100%]

494 passed in 12.34s

---------- coverage: 87% ----------
agents/         94%    services/       89%
providers/      91%    utils/          82%
```

---

## Screenshot 7: Dependency Comparison Infographic

| Property | Value |
|----------|-------|
| **Filename** | `agentforge-deps-comparison.png` |
| **Dimensions** | 1280x720 (standalone graphic, not app screenshot) |
| **Source** | Custom-designed graphic (Figma/Canva) |
| **UI Elements to Show** | Side-by-side: AgentForge (5 deps, 2MB) vs LangChain (50+ deps, 150MB) |
| **Color Scheme** | AgentForge side uses primary `#6366F1`, LangChain side uses muted `#8B949E` |
| **Callout Numbers** | (1) "5 dependencies", (2) "~2MB bundle", (3) "5 min setup" |
| **Caption** | "10x lighter than LangChain, same production power" |
| **Context** | Key competitive differentiator; used in README and Gumroad listing |

### Layout Spec
```
┌────────────────────────────────────────────────────────┐
│              Dependencies Comparison                    │
│                                                        │
│   AgentForge                    LangChain              │
│   ┌──────────┐                  ┌──────────────────┐   │
│   │ 5 deps   │ ◄──── vs ────► │ 50+ deps          │   │
│   │ ~2MB     │                 │ ~150MB             │   │
│   │ 5 min    │                 │ 2-4 hours          │   │
│   └──────────┘                  └──────────────────┘   │
│   (#6366F1)                     (#8B949E)              │
│                                                        │
│   [Caption: 10x lighter...]                            │
└────────────────────────────────────────────────────────┘
```

---

## Gumroad Listing Image Order

| Position | Screenshot | Purpose |
|----------|-----------|---------|
| 1 (Cover) | `agentforge-dashboard-hero.png` | First impression, shows full platform |
| 2 | `agentforge-cost-savings.png` | ROI proof, drives purchase decision |
| 3 | `agentforge-provider-benchmark.png` | Technical differentiation |
| 4 | `agentforge-deps-comparison.png` | Competitive advantage |
| 5 | `agentforge-cli-quickstart.png` | Ease of use proof |
| 6 | `agentforge-agent-mesh.png` | Enterprise architecture |
| 7 | `agentforge-test-suite.png` | Quality trust signal |
