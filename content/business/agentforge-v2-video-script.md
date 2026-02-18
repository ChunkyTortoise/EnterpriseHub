# AgentForge v2.0 Loom Walkthrough Script

**Duration**: ~7:30 | **Format**: Loom screen recording | **Audience**: Senior engineers, tech leads
**Repo**: github.com/ChunkyTortoise/multi-agent-starter-kit

---

## HOOK (0:00 - 0:30)

**[ON SCREEN]**: Terminal open, dark theme. Cursor blinking.

**[NARRATION]**: Building agent pipelines is easy. LangChain, CrewAI, AutoGen -- there are a dozen frameworks that'll get you a demo in 20 minutes. Making them production-ready? That's where it falls apart. You need retry logic. You need human approval gates. You need to evaluate your agents before you ship them. And suddenly you're fighting framework abstractions instead of writing your actual logic.

[PAUSE]

**[NARRATION]**: This is AgentForge v2 -- a multi-agent orchestration kit in pure Python. No framework dependencies. 101 tests passing. Everything you need to go from prototype to production. Let me show you how it works.

---

## REPO OVERVIEW (0:30 - 1:30)

**[ON SCREEN]**: Browser -- GitHub repo page for `multi-agent-starter-kit`

**[ACTION]**: Navigate to the GitHub repo. Scroll slowly past the badges at the top.

**[NARRATION]**: Here's the repo. First thing -- look at the badges. CI green, Python 3.11+, 101 tests passing, MIT license. This is not a weekend experiment. It's tested and it ships clean.

[PAUSE]

**[ACTION]**: Scroll down to the "What This Solves" section. Pause briefly on each bullet.

**[NARRATION]**: The README lays out the five problems this solves: agent coordination -- running multi-step workflows with explicit dependencies. High-stakes decisions -- human-in-the-loop approval gates. RAG without the bloat -- multi-knowledge-base retrieval with self-correction, no vector DB required. Blind deployment -- evaluate agents with P50/P95/P99 latency before they touch production. And framework bloat -- this whole thing runs on pure Python plus Pydantic. That's it.

**[ACTION]**: Scroll to the "Project Structure" section. [ZOOM IN] on the file tree.

**[NARRATION]**: The structure is clean. Six files in the orchestrator core -- `dag.py` for the execution engine, `base_agent.py` for the agent contract, `hitl.py` for approval gates, `rag.py` for retrieval, `eval.py` for evaluation, and `monitor.py` for the ASCII dashboard. Three example agents under `agents/`, three runnable demos under `examples/`, and four test files with 101 tests. The whole thing is about 2,000 lines of actual code.

---

## BASIC PIPELINE DEMO (1:30 - 2:30)

**[ON SCREEN]**: Terminal

**[ACTION]**: Type and run: `python examples/pipeline.py`

**[NARRATION]**: Let's run the basic pipeline. This is a three-agent DAG -- Research, Analysis, Report. Research gathers data. Analysis depends on Research and scores the findings. Report depends on both.

[PAUSE -- let the output render]

**[ON SCREEN]**: Terminal output showing execution order, per-agent timing, then the Pipeline Summary, then the monitor dashboard with the Gantt chart.

**[NARRATION]**: Watch the output. The orchestrator resolves the execution order automatically using topological sort -- Kahn's algorithm. Research runs first, then Analysis consumes its findings, then Report pulls from both. Each agent gets timed. You see the Pipeline Summary -- pass/fail, milliseconds per step, total tokens, total cost.

**[ACTION]**: [ZOOM IN] on the ASCII monitor dashboard -- the performance table and Gantt chart.

**[NARRATION]**: And this is the monitor dashboard. No Grafana, no Prometheus, no setup. You get a performance table with status, duration, tokens, and cost for every agent. And below that -- a Gantt chart showing the execution timeline. You can see exactly where time is being spent. It also exports to JSON, so you can pipe this into whatever observability stack you already have.

---

## BASE AGENT (2:30 - 3:15)

**[ON SCREEN]**: Editor -- open `examples/custom_agent.py`

**[ACTION]**: Open the file. [ZOOM IN] on the `SentimentAgent` class, lines 15-40.

**[NARRATION]**: Here's how you build your own agent. This is the entire custom agent example -- a sentiment analyzer. Subclass `BaseAgent`, set a `name`, implement `execute()`. That's it. The orchestrator wraps your `execute()` call with timing, error handling, structured output, and cost tracking. You just write your logic.

**[ACTION]**: [HIGHLIGHT] lines 20-40 -- the `execute` method body.

**[NARRATION]**: The `execute` method receives an `AgentInput` with a context dict and any upstream results from dependencies. You return a plain dict and the framework wraps it into an `AgentOutput` with success status, duration, token usage, and cost. Your agent is now compatible with the DAG orchestrator, the eval framework, the monitor -- everything. Twenty lines of code.

[PAUSE]

**[ACTION]**: Scroll down to the `if __name__` block showing the agent wired into a DAG.

**[NARRATION]**: And plugging it into a pipeline is four lines. Create a DAG, add a node, run it. All the retry logic, dependency resolution, and monitoring come for free.

---

## HITL GATE DEMO (3:15 - 4:30)

**[ON SCREEN]**: Editor -- open `examples/hitl_pipeline.py`

**[NARRATION]**: This is the feature I'm most proud of. Human-in-the-loop approval gates. You're building a data pipeline, a deployment workflow, anything where a human needs to sign off before something irreversible happens. HITL gates let you pause the pipeline and wait.

**[ACTION]**: [ZOOM IN] on `demo_auto_approve()` function, lines 69-95. Highlight the `HITLGate` constructor.

**[NARRATION]**: There are three modes. Mode one -- auto-approve after a timeout. You create a gate with `auto_approve_after` and `interactive=False`. The pipeline pauses, waits for a human, and if nobody responds in half a second -- or whatever timeout you set -- it auto-approves. Safety net for CI pipelines.

**[ACTION]**: Switch to terminal. Run: `python examples/hitl_pipeline.py`

[PAUSE -- let output render for all three demos]

**[ON SCREEN]**: Terminal output showing all three HITL demos running in sequence.

**[NARRATION]**: Mode two -- external approval. The gate fires an `on_request` callback -- that's where you send your Slack notification, your PagerDuty alert, whatever. A separate thread or webhook handler calls `gate.approve()` with the gate ID, the approver's email, and notes. Full audit trail. Watch the output -- you can see the external approver thread pick up the gate ID and approve it.

[PAUSE]

**[NARRATION]**: Mode three -- rejection. Same setup, but the reviewer calls `gate.reject()`. The pipeline halts. Downstream agents are skipped. Look at the summary -- ingest ran, but export got skipped because the gate was rejected. The error message tells you exactly who rejected it and why. No data corruption, no accidental deploys.

**[ACTION]**: [ZOOM IN] on the rejection output showing "HITL gate rejected" and the export agent showing "FAIL".

**[NARRATION]**: And the gate tracks everything -- approval rate, average wait time, full history. You get `gate.summary()`, `gate.history`, `gate.approval_rate()`. Production-grade audit trail out of the box.

---

## RAG DEMO (4:30 - 5:45)

**[ON SCREEN]**: Editor -- open `orchestrator/rag.py`

**[NARRATION]**: Next -- agentic RAG. Not just retrieval-augmented generation. This is a full retrieval loop with self-correction and answer validation.

**[ACTION]**: [ZOOM IN] on the `RAGAgent.execute()` method, lines 274-322.

**[NARRATION]**: Here's the loop. The agent queries all knowledge bases, computes a confidence score, and if confidence is below your threshold, it automatically refines the query and retries. It does this up to three iterations -- configurable. When it's satisfied, it calls `synthesize_answer()` -- which you override with your LLM call -- and then validates the answer for groundedness. It checks that the answer terms actually appear in the source documents. If they don't, it flags a warning.

[PAUSE]

**[ACTION]**: Scroll up to the `KnowledgeBase` class. [HIGHLIGHT] the `search()` method.

**[NARRATION]**: The knowledge base uses TF-IDF relevance scoring out of the box. Zero external dependencies. But the interface is clean -- you override `search()` with your embedding provider. OpenAI, Cohere, your own fine-tuned model, whatever. The self-correction loop doesn't care how retrieval works under the hood.

**[ACTION]**: Scroll to the README's RAG example code block.

**[NARRATION]**: Using it is straightforward. Create knowledge bases, add documents, subclass `RAGAgent`, implement `synthesize_answer()`. You get back an answer, a confidence score, source labels, iteration count, groundedness flag, and any warnings. Multi-KB queries merge results and re-sort by score. You can have an HR policy knowledge base, a legal knowledge base, and a product docs knowledge base, and the agent queries all of them in one call.

[PAUSE]

**[NARRATION]**: The key insight here is self-correction. Most RAG implementations do one retrieval pass and hope for the best. This one iterates. Low confidence? Refine the query using terms from the top result, strip stopwords, and try again. It's the difference between a demo and a system you can actually deploy.

---

## EVAL + LEADERBOARD (5:45 - 7:00)

**[ON SCREEN]**: Terminal

**[ACTION]**: Run: `python examples/eval_demo.py`

[PAUSE -- let the full output render]

**[NARRATION]**: Last feature -- the evaluation framework. This is how you know your agents actually work before you ship them. I'm running the eval demo, which tests two agents -- MathAgent, which is correct, and SloppyMathAgent, which has a deliberate bug in multiplication.

**[ON SCREEN]**: Terminal showing the eval reports for both agents.

**[ACTION]**: [ZOOM IN] on the MathAgent eval report.

**[NARRATION]**: MathAgent -- 6 test cases, 100% pass rate, average score 1.0, average latency under 1 millisecond. Clean. Now look at SloppyMathAgent -- same 6 test cases, but only 83% pass rate. It fails the multiplication test because it has a bug. The report tells you exactly which cases failed. No guessing.

**[ACTION]**: [ZOOM IN] on the benchmark output.

**[NARRATION]**: Below that, the benchmark. This runs every test case 5 times and gives you P50, P95, P99 latency. You know your worst-case performance before you deploy. And the error rate across all runs. This is what you show in a design review when someone asks "how do you know it works."

**[ACTION]**: [ZOOM IN] on the leaderboard output.

**[NARRATION]**: And the leaderboard. BenchmarkSuite lets you add multiple agents and rank them. Pass rate, score, latency, cost -- all in one table. Gold, silver, bronze. When you're iterating on a prompt or swapping an LLM provider, this is how you compare. Run the suite, check the leaderboard, ship the winner.

[PAUSE]

**[ACTION]**: [ZOOM IN] on the comparison output.

**[NARRATION]**: There's also a head-to-head comparison mode. MathAgent versus SloppyMathAgent on the same test suite. Pass rate, score, latency, cost, side by side. Winner declared. You can wire this into CI -- if the new agent doesn't beat the old one, the build fails.

**[ACTION]**: Briefly show the exported `eval_report.json` file.

**[NARRATION]**: Everything exports to JSON. Pipe it into your CI dashboard, your monitoring stack, whatever. Structured data, not just terminal output.

---

## WRAP + CTA (7:00 - 7:30)

**[ON SCREEN]**: Back on the GitHub repo README. Scroll to the top.

**[NARRATION]**: So that's AgentForge v2. DAG orchestration with retry and graceful degradation. Human-in-the-loop approval gates with full audit trails. Agentic RAG with self-correction and answer validation. And an evaluation framework with P50/P95/P99 benchmarking and leaderboards. 101 tests. Pure Python. One dependency -- Pydantic.

[PAUSE]

**[NARRATION]**: The link is in the description. Star the repo if it's useful. And if you're building multi-agent systems for a client and you want someone who's already done this -- I do consulting and contract work. There's a link for that too.

[PAUSE]

**[NARRATION]**: Thanks for watching.

**[ON SCREEN]**: Freeze on the repo README with badges visible.

---

## RECORDING NOTES

**Total estimated duration**: 7:15-7:30

**Pre-recording checklist**:
- [ ] Clone fresh copy of the repo and run all three examples to verify output
- [ ] Terminal: dark theme, large font (16-18pt), clear scrollback
- [ ] Browser: GitHub dark mode, zoom to 125%
- [ ] Editor: VS Code with file minimap hidden, large font
- [ ] Close all notifications, Slack, email
- [ ] Run `pytest tests/ -v` once to confirm 101 passing

**Key moments to zoom in**:
1. (0:30) GitHub badges -- CI, tests, license
2. (1:15) File structure tree in README
3. (2:15) ASCII monitor dashboard with Gantt chart
4. (2:45) SentimentAgent class definition -- 20 lines
5. (3:30) HITLGate constructor with `auto_approve_after`
6. (4:15) Rejection output -- gate rejected, export skipped
7. (5:00) RAGAgent.execute() loop -- retrieve, evaluate, refine
8. (6:00) Eval report showing 100% vs 83% pass rate
9. (6:30) Benchmark P50/P95/P99 output
10. (6:45) Leaderboard with gold/silver ranking

**Tone reminders**:
- Confident but not salesy -- let the code speak
- Never say "simple" or "easy" -- say "clean" or "straightforward"
- Pause after key moments to let viewers read the output
- No filler words -- if you need to think, just pause silently
