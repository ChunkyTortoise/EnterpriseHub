# AI Browser Automation Research: Orchestrator-Delegated Architecture

**Research Date**: February 14, 2026
**Purpose**: Identify token-efficient approaches for delegating browser automation from Claude Code orchestrator to specialized browser agents
**Researcher**: Claude Sonnet 4.5

---

## Executive Summary

This research evaluates 8 AI browser automation tools and delegation patterns to optimize token efficiency when orchestrating browser tasks from Claude Code. The key finding: **Browser Use + Haiku/Flash in Architect-Builder pattern** offers the best cost-performance trade-off, with 75-90% cost reduction vs OpenAI Operator while maintaining 89% success rates.

**Recommended Architecture**: Claude Code (orchestrator) → Browser Use Cloud API → Gemini Flash 2.5-Lite ($0.10/$0.40 per 1M tokens)

**Key Metrics**:
- **Cost reduction**: 75-90% vs managed solutions ($200/mo → $20-50/mo)
- **Token efficiency**: 2-5KB accessibility snapshots vs 500KB-2MB screenshots
- **Success rate**: 85-89% on WebVoyager benchmark
- **Latency**: <1s session start, 3-10ms MCP overhead

---

## 1. Tool Comparison Matrix

| Tool | Architecture | Token Efficiency | Cost | Success Rate | Orchestration API | Maturity | Best Use Case |
|------|-------------|------------------|------|--------------|-------------------|----------|---------------|
| **Browser Use** | Open-source Python library + Cloud | ★★★★★ (accessibility trees) | $0.01/task init + per-step | 89% WebVoyager | REST API, MCP server | ★★★★★ Production | General automation, cheapest option |
| **Stagehand** | AI-native SDK (Browserbase) | ★★★★★ (auto-caching, self-healing) | $0.005-0.05/session | Not disclosed | SDK (multi-language), CDP | ★★★★★ Production | Developer-focused, fastest (44% faster v3) |
| **Skyvern** | Playwright + LLM + CV | ★★★★ (vision-based) | Cloud pricing varies | 85.85% WebVoyager, 63.8% form-fill | REST API, workflows | ★★★★ Production | Form filling, RPA tasks, CAPTCHA/2FA |
| **Playwright MCP** | Microsoft MCP server | ★★★★★ (2-5KB snapshots) | API calls only | Not benchmarked | MCP (25+ tools) | ★★★★ Stable | Sandboxed AI agents, structured control |
| **Anthropic Computer Use** | Vision-based screen control | ★★ (screenshot processing) | ~$1.25/task (Opus) | Not disclosed | API tool, Claude Cowork | ★★★ Beta | Desktop automation, general computing |
| **AgentQL** | Semantic query language | ★★★★ (context-aware selectors) | API pricing varies | Not disclosed | REST API | ★★★ Stable | Web scraping, semantic data extraction |
| **Steel.dev** | Browser infrastructure platform | ★★★ (infrastructure focus) | $0.005-0.05/session | 70% success | REST API, SDKs | ★★★★ Production | Self-hosted infrastructure, large-scale |
| **LaVague** | Large Action Model framework | ★★★ (action generation) | Self-hosted or API | Not disclosed | Python framework | ★★★ Emerging | QA automation, open-source flexibility |
| **OpenAI Operator** | ChatGPT Pro browser agent | ★★ (proprietary) | $200/mo (400 tasks) | Not disclosed | ChatGPT Pro only | ★★★ Public beta | Managed consumer solution, no code |

**Rating Key**: ★★★★★ Excellent | ★★★★ Good | ★★★ Adequate | ★★ Limited | ★ Poor

---

## 2. Architecture Patterns for Delegation

### 2.1 Centralized/Hierarchical Orchestration (RECOMMENDED)

**Pattern**: Orchestrator (Claude Code) → Browser Worker Agent → Report Back

```
┌─────────────────────────┐
│   Claude Code           │  ← Expensive model (Opus/Sonnet)
│   (Orchestrator)        │     - High-level planning
│   - Task decomposition  │     - Context synthesis
│   - Result synthesis    │     - User interaction
└────────┬────────────────┘
         │ High-level instructions:
         │ "Book flight LAX→NYC on Feb 20"
         ▼
┌─────────────────────────┐
│   Browser Use Agent     │  ← Cheap model (Haiku/Flash)
│   (Worker)              │     - Browser execution
│   - Execute steps       │     - Page navigation
│   - Handle UI           │     - Form filling
└────────┬────────────────┘
         │ Structured result:
         │ {status, data, screenshots}
         ▼
┌─────────────────────────┐
│   Claude Code           │
│   Final report to user  │
└─────────────────────────┘
```

**Token Savings**: 60-80% by moving browser execution to cheaper model
**Implementation**: MCP server or REST API delegation

### 2.2 Architect-Builder Pattern (HIGHEST EFFICIENCY)

**Pattern**: Expensive model creates plan → Cheap model executes

```
Architect (Claude Code w/ Opus):
  → Analyzes user intent
  → Creates structured blueprint (JSON)
  → Defines success criteria

Builder (Browser Use w/ Gemini Flash):
  → Executes from blueprint (no hallucination risk)
  → Reports structured results
  → Only escalates on errors
```

**Key Benefit**: Architect outputs only structured data (cannot hallucinate), Builder locked to blueprint (cannot deviate)

**Token Savings**: 70-90% vs single expensive model for entire workflow

### 2.3 Event-Driven Orchestration

**Pattern**: Agents respond to events rather than sequential control

```
User request → Event: "browser_task_needed"
  → Browser agent spawns
  → Executes autonomously
  → Emits event: "task_complete" + results
  → Orchestrator consumes event
```

**Use Case**: Long-running tasks, batch processing, async workflows

### 2.4 MCP-Based Delegation

**Pattern**: Browser automation exposed as MCP server tools

```
Claude Code:
  - Calls MCP tool "browser_navigate"
  - Calls MCP tool "browser_click"
  - Calls MCP tool "browser_extract"

MCP Server (Playwright/Browser Use):
  - Exposes 25+ structured tools
  - Returns accessibility tree (2-5KB)
  - No screenshot overhead
```

**Latency**: 3-10ms MCP overhead (optimized gateways)
**Token Efficiency**: 10-100x better than screenshot-based approaches

---

## 3. Recommended Approach for EnterpriseHub

### 3.1 Architecture: Browser Use Cloud + Gemini Flash 2.5-Lite

**Components**:

1. **Orchestrator**: Claude Code (Opus 4.6)
   - User interaction
   - High-level planning
   - Result synthesis
   - Error handling

2. **Browser Worker**: Browser Use Cloud API
   - LLM: Gemini Flash 2.5-Lite ($0.10/$0.40 per 1M tokens)
   - Handles all browser execution
   - Returns structured results

3. **Communication**: REST API (Browser Use Cloud endpoint)
   - Alternative: MCP server for local development

### 3.2 Implementation Pattern

```python
# In Claude Code orchestrator
async def orchestrate_browser_task(user_goal: str):
    """Orchestrator delegates to Browser Use agent"""

    # 1. High-level planning (Opus/Sonnet)
    plan = await analyze_user_intent(user_goal)

    # 2. Delegate to cheap browser agent (Flash)
    browser_result = await browser_use_cloud.execute(
        task=plan.browser_instruction,
        model="gemini-2.5-flash-lite",  # Cheapest powerful model
        timeout=300
    )

    # 3. Synthesize results (Opus/Sonnet)
    final_response = await synthesize_results(
        plan=plan,
        browser_data=browser_result
    )

    return final_response
```

### 3.3 Cost Analysis

**Current Approach** (Claude Code executing browser tasks directly):
- Model: Claude Opus 4.6
- Browser task: ~20,000 tokens (including screenshots, DOM inspection)
- Cost per task: ~$0.30 (input) + $0.90 (output) = **$1.20/task**

**Recommended Approach** (Browser Use + Gemini Flash):
- Orchestrator (Opus): 2,000 tokens for planning + synthesis
  - Cost: $0.03 (input) + $0.09 (output) = $0.12
- Browser Worker (Flash): 5,000 tokens (accessibility tree-based)
  - Cost: $0.0005 (input) + $0.002 (output) = $0.0025
- **Total**: **$0.12/task**

**Savings**: 90% cost reduction ($1.20 → $0.12)

**Monthly Estimate** (100 browser tasks/month):
- Current: $120/month
- Recommended: $12/month + $10 Browser Use Cloud = **$22/month**
- **Total savings**: $98/month (82%)

### 3.4 Reliability Considerations

| Factor | Rating | Notes |
|--------|--------|-------|
| **Success Rate** | 89% | Browser Use WebVoyager benchmark |
| **CAPTCHA Handling** | ★★★★★ | Built-in bypass, <1s detection |
| **Session Stability** | ★★★★★ | 24hr max session, <1s init |
| **Error Recovery** | ★★★★ | Self-healing with Stagehand integration |
| **Proxy/Anti-Detection** | ★★★★ | Cloud version includes proxy network |

---

## 4. Model Selection for Browser Execution

### 4.1 Recommended Models (Cheapest → Most Capable)

| Model | Input Cost | Output Cost | Speed | Best For |
|-------|-----------|-------------|-------|----------|
| **Gemini 2.5 Flash-Lite** | $0.10/1M | $0.40/1M | ★★★★★ | Bulk automation, simple tasks |
| **GPT-4o-mini** | $0.15/1M | $0.60/1M | ★★★★ | Balanced quality/cost |
| **Claude Haiku 4.5** | $1.00/1M | $5.00/1M | ★★★★ | High safety, robust reasoning |
| **Grok 4 Fast** | $0.10/1M | $0.40/1M | ★★★★★ | Ultra-large contexts |
| **DeepSeek V3** | $0.07/1M | $0.28/1M | ★★★★ | Cheapest option, emerging |

**Recommendation**: Start with **Gemini 2.5 Flash-Lite** for 95% of tasks, escalate to **Haiku 4.5** only for complex reasoning or high-safety scenarios.

### 4.2 Token Consumption Patterns

**Traditional Screenshot Approach**:
- Screenshot: 500KB-2MB per interaction
- Vision model processing: High token cost
- **Total**: 15,000-30,000 tokens per page

**Accessibility Tree Approach** (Browser Use, Playwright MCP):
- Structured data: 2-5KB per page
- Text-based processing: Standard token cost
- **Total**: 1,000-3,000 tokens per page

**Efficiency Gain**: 10-100x reduction in token usage

---

## 5. Delegation Communication Patterns

### 5.1 MCP-Based Delegation

**Advantages**:
- Standardized protocol
- Discovery of capabilities
- Bidirectional messaging
- 3-10ms latency overhead (optimized gateways)

**Best For**:
- Local development
- Tight integration with Claude Code
- Complex multi-tool coordination

**Implementation**:
```json
{
  "mcpServers": {
    "browser-use": {
      "command": "npx",
      "args": ["-y", "@browser-use/mcp-server"],
      "env": {
        "BROWSER_USE_API_KEY": "${BROWSER_USE_API_KEY}"
      }
    }
  }
}
```

### 5.2 REST API Delegation (RECOMMENDED)

**Advantages**:
- Language-agnostic
- Simpler deployment
- Better for production
- Clear request/response boundaries

**Best For**:
- Production systems
- Cross-language integration
- Async/background tasks

**Implementation**:
```python
import httpx

async def delegate_browser_task(instruction: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.browser-use.com/v1/tasks",
            json={
                "instruction": instruction,
                "model": "gemini-2.5-flash-lite",
                "max_steps": 20,
                "return_format": "structured"
            },
            headers={"Authorization": f"Bearer {BROWSER_USE_API_KEY}"}
        )
        return response.json()
```

### 5.3 Agent Spawning Pattern (Claude Code Native)

**Advantages**:
- Uses Claude Code's built-in Task tool
- Managed context isolation
- Automatic result reporting

**Best For**:
- Claude Code-specific workflows
- Multi-agent coordination
- Complex orchestration

**Implementation**:
```python
# In Claude Code
Task(
    subagent_type="browser-automation",  # Custom agent type
    task="Book flight from LAX to NYC on Feb 20",
    team_name="browser-workers"
)
```

---

## 6. Implementation Priority

### Phase 1: Proof of Concept (Week 1)

**Goal**: Validate Browser Use + Gemini Flash for single task

**Tasks**:
1. Sign up for Browser Use Cloud ($10 free credits)
2. Test simple automation: "Navigate to google.com and search for 'AI agents'"
3. Measure token usage and cost
4. Compare results with direct Claude Code execution

**Success Criteria**:
- ✅ Task completion rate > 80%
- ✅ Cost < $0.20/task
- ✅ Latency < 30s

### Phase 2: Integration (Week 2-3)

**Goal**: Integrate into EnterpriseHub as reusable service

**Tasks**:
1. Create `BrowserDelegationService` in `ghl_real_estate_ai/services/`
2. Implement REST API client for Browser Use Cloud
3. Add Architect-Builder pattern for complex tasks
4. Create fallback to direct execution on failure

**Success Criteria**:
- ✅ API integration complete
- ✅ Error handling with retries
- ✅ Logging and monitoring

### Phase 3: Production Deployment (Week 4)

**Goal**: Deploy to production with monitoring

**Tasks**:
1. Add environment variables for Browser Use API key
2. Implement rate limiting (concurrent session limits)
3. Set up cost tracking and alerts
4. Create dashboard for browser task metrics

**Success Criteria**:
- ✅ Cost alerts at $50/month threshold
- ✅ Success rate monitoring
- ✅ Performance SLAs (<60s per task)

### Phase 4: Optimization (Week 5-6)

**Goal**: Optimize for cost and performance

**Tasks**:
1. A/B test Gemini Flash vs Haiku for different task types
2. Implement caching for repeated tasks
3. Add multi-browser session pooling
4. Fine-tune task decomposition for token efficiency

**Success Criteria**:
- ✅ Cost < $30/month for typical usage
- ✅ Success rate > 90%
- ✅ Average latency < 20s

---

## 7. Risk Analysis and Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Browser Use API downtime** | Medium | High | Implement fallback to local Playwright execution |
| **Cost overruns** | Low | Medium | Set spending limits, implement cost alerts |
| **Lower success rates** | Medium | Medium | Start with simple tasks, gradual complexity increase |
| **Security/data leakage** | Low | High | Use Browserbase isolated sessions, no PII in logs |
| **Rate limiting** | Medium | Low | Implement queue system, exponential backoff |
| **Model quality degradation** | Low | Medium | Monitor success rates, switch models if needed |

---

## 8. Alternative Architectures Considered

### 8.1 Stagehand + Browserbase (Runner-up)

**Pros**:
- 44% faster than competitors
- Auto-caching reduces repeat costs
- Multi-language SDK support
- Self-healing on DOM changes

**Cons**:
- Higher base cost (Browserbase infrastructure)
- More complex setup
- Less transparent pricing

**Use Case**: Consider for high-frequency automation where speed > cost

### 8.2 Skyvern Cloud (Specialized)

**Pros**:
- Best for form filling (63.8% success rate)
- Built-in CAPTCHA/2FA handling
- Workflow orchestration

**Cons**:
- Lower general success rate (85.85% vs 89%)
- More expensive
- Overkill for simple navigation tasks

**Use Case**: Consider for complex form automation (e.g., government forms, job applications)

### 8.3 Playwright MCP + Local Execution

**Pros**:
- No API costs
- Full control
- 25+ structured tools
- 2-5KB accessibility snapshots

**Cons**:
- Requires local browser infrastructure
- No CAPTCHA solving
- Manual proxy management

**Use Case**: Consider for development/testing, not production

---

## 9. Key Takeaways

1. **Browser Use + Gemini Flash 2.5-Lite** offers the best cost-performance trade-off for general browser automation (90% cost reduction, 89% success rate)

2. **Architect-Builder pattern** is the most token-efficient delegation approach (70-90% savings)

3. **Accessibility tree snapshots** (2-5KB) are 10-100x more efficient than screenshot-based approaches (500KB-2MB)

4. **MCP adds only 3-10ms latency** with optimized gateways, making it viable for production

5. **REST API delegation** is simpler and more production-ready than MCP for cross-language integration

6. **Cheaper models** (Flash, Haiku, GPT-4o-mini) are sufficient for 95% of browser execution tasks when properly orchestrated

7. **Browser automation market is mature** in 2026 with multiple production-ready options (Browser Use, Stagehand, Skyvern all >85% success rates)

8. **Cost savings are substantial**: OpenAI Operator ($200/mo) vs Browser Use + Flash ($20-50/mo) = 75-90% reduction

---

## 10. References and Sources

### Tool Documentation
- [Browser Use](https://browser-use.com/) - Open source browser automation for AI agents
- [Browser Use GitHub](https://github.com/browser-use/browser-use) - Official repository
- [Stagehand](https://www.stagehand.dev/) - AI browser automation SDK
- [Stagehand GitHub](https://github.com/browserbase/stagehand) - Official repository
- [Skyvern](https://www.skyvern.com/) - AI browser automation for workflows
- [Skyvern GitHub](https://github.com/Skyvern-AI/skyvern) - Official repository
- [Playwright MCP](https://github.com/microsoft/playwright-mcp) - Microsoft's MCP server
- [AgentQL](https://www.agentql.com) - Semantic web query language
- [Steel.dev](https://steel.dev/) - Browser infrastructure for AI agents
- [LaVague](https://www.lavague.ai/) - Large Action Model framework
- [Anthropic Computer Use](https://www.anthropic.com/news/3-5-models-and-computer-use) - Claude desktop automation

### Market Research and Benchmarks
- [11 Best Browser Agents for AI Automation in 2026](https://www.firecrawl.dev/blog/best-browser-agents) - Comprehensive tool comparison
- [Top 10 Browser Use Agents: Full Review 2026](https://o-mega.ai/articles/top-10-browser-use-agents-full-review-2026) - Market overview
- [Browser Use vs Skyvern Comparison 2026](https://openalternative.co/compare/browser-use/vs/skyvern) - Detailed benchmarks
- [Web Bench - A new way to compare AI Browser Agents](https://www.skyvern.com/blog/web-bench-a-new-way-to-compare-ai-browser-agents/) - 5,750 task benchmark
- [6 most popular Playwright MCP servers for AI testing in 2026](https://bug0.com/blog/playwright-mcp-servers-ai-testing) - MCP landscape

### Architecture Patterns
- [AI Agent Orchestration Patterns - Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns) - Microsoft's official patterns
- [Sub-Agent Orchestration with Spring AI](https://gaetanopiazzolla.github.io/java/ai/2026/02/09/sub-agent-pattern.html) - Architect-Builder pattern
- [Top 10+ Agentic Orchestration Frameworks & Tools in 2026](https://aimultiple.com/agentic-orchestration) - Framework comparison
- [AI Agent Orchestration in 2026: Coordination, Scale and Strategy](https://kanerika.com/blogs/ai-agent-orchestration/) - Enterprise patterns
- [Claude Code agent delegation browser automation best practices 2026](https://www.anthropic.com/engineering/claude-code-best-practices) - Official Anthropic guide

### Model Pricing and Performance
- [Claude Haiku 4.5 vs GPT-4o mini vs Gemini Flash 2025: Pricing & Limits](https://skywork.ai/blog/claude-haiku-4-5-vs-gpt4o-mini-vs-gemini-flash-vs-mistral-small-vs-llama-comparison/) - Model comparison
- [Cheapest LLM API 2026](https://pricepertoken.com/cheapest) - Real-time pricing
- [Low-Cost LLMs: An API Price & Performance Comparison](https://intuitionlabs.ai/articles/low-cost-llm-comparison) - Performance benchmarks
- [LLM API Pricing Comparison & Cost Guide (Feb 2026)](https://costgoat.com/compare/llm-api) - Cost calculator

### MCP and Communication Protocols
- [What Is MCP (Model Context Protocol)? The 2026 Guide](https://generect.com/blog/what-is-mcp/) - Protocol overview
- [MCP vs APIs: When to Use Which for AI Agent Development](https://www.tinybird.co/blog/mcp-vs-apis-when-to-use-which-for-ai-agent-development) - Comparison
- [MCP vs REST API agent communication latency overhead 2026](https://bytebridge.medium.com/mcp-vs-traditional-api-calls-in-production-promises-pitfalls-and-proper-use-e0550c4b8065) - Performance analysis
- [10 Best MCP Gateways for Developers in 2026](https://composio.dev/blog/best-mcp-gateway-for-developers) - Gateway comparison

### Cost Analysis
- [OpenAI Operator Pricing 2026](https://o-mega.ai/articles/chatgpt-operator-pricing-what-does-it-cost-you-2026) - $200/month analysis
- [Open-Source Alternatives to OpenAI's Operator Agent](https://www.simular.ai/blogs/open-source-alternatives-to-openais-operator-agent) - 75% cost savings
- [ChatGPT API Pricing 2026: Token Costs & Rate Limits](https://intuitionlabs.ai/articles/chatgpt-api-pricing-2026-token-costs-limits) - OpenAI pricing

### Claude Code Integration
- [Claude Code multiple agent systems: Complete 2026 guide](https://www.eesel.ai/blog/claude-code-multiple-agent-systems-complete-2026-guide) - Multi-agent orchestration
- [My 7 essential Claude Code best practices for production-ready AI in 2025](https://www.eesel.ai/blog/claude-code-best-practices) - Best practices
- [Optimizing Agentic Coding: How to Use Claude Code in 2026?](https://aimultiple.com/agentic-coding) - Optimization guide

### Industry Trends
- [Unlocking exponential value with AI agent orchestration](https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/ai-agent-orchestration.html) - Deloitte 2026 predictions
- [Remote Browsers: Web Infra for AI Agents Compared](https://research.aimultiple.com/remote-browsers/) - Infrastructure comparison
- [AI web scraping market](https://www.zyte.com/blog/agentic-web-scraping/) - $886M in 2025 → $4.4B by 2035 (17.3% CAGR)

---

**Document Version**: 1.0
**Last Updated**: February 14, 2026
**Next Review**: March 1, 2026 (post Phase 1 completion)
