# AgentForge vs LangChain

A detailed comparison for teams evaluating multi-agent frameworks. Includes feature comparison, code examples for the same RAG task, and a migration guide.

---

## Feature Comparison

| Feature | AgentForge | LangChain |
|---------|:----------:|:---------:|
| **Architecture** | DAG-first pipeline orchestration | Chain/graph composition (LCEL) |
| **Dependencies (base install)** | 1 (Pydantic v2) | 112+ transitive deps |
| **Base memory footprint** | ~8 MB | ~520 MB |
| **P50 framework overhead** | 12ms | ~78ms |
| **Async/await native** | Full async throughout | Partial (sync wrappers exist) |
| **MCP tool protocol** | Native client + server | Community adapter only |
| **LLM provider support** | 100+ via LiteLLM optional extra | 60+ via built-in integrations |
| **YAML pipeline definition** | Built-in with `PipelineBuilder.from_yaml` | Not built-in (LangServe separate) |
| **OpenTelemetry tracing** | Built-in optional extra | Via LangSmith (proprietary SaaS) |
| **Plugin architecture** | Python entry points | Callbacks + middleware |
| **Streaming support** | Async generators | LCEL streaming |
| **Memory systems** | Working, session, persistent, checkpoint | ConversationBuffer, Summary, Vector |
| **Agent-to-Agent protocol** | Built-in A2A support | Not built-in |
| **Test suite** | 680+ tests, ~80% coverage | ~400 tests |
| **Python version** | 3.11+ | 3.9+ |
| **License** | MIT | MIT |

---

## Code Comparison: RAG Query Pipeline

### The task

Build a pipeline that: (1) takes a user question, (2) retrieves relevant documents, (3) generates an answer using the retrieved context.

### AgentForge

```python
"""RAG pipeline in AgentForge — 25 lines, zero LangChain deps."""
import asyncio
from agentforge import Agent, DAG, ExecutionEngine, AgentInput

# Define agents with instructions
retriever = Agent(
    name="retriever",
    instructions="Search the knowledge base and return relevant passages.",
    tools=[vector_search],  # your search function decorated with @tool
)
synthesizer = Agent(
    name="synthesizer",
    instructions="Answer the question using only the provided context. Cite sources.",
)

# Wire them into a DAG
dag = DAG(name="rag-pipeline")
dag.add_node("retriever", retriever)
dag.add_node("synthesizer", synthesizer)
dag.add_edge("retriever", "synthesizer")

# Execute
engine = ExecutionEngine()
result = await engine.execute(
    dag,
    input=AgentInput(messages=[{"role": "user", "content": "What is MCP?"}]),
)
print(result.outputs["synthesizer"].content)
```

### LangChain (LCEL)

```python
"""RAG pipeline in LangChain — 35 lines, requires langchain + langchain-openai
   + langchain-community + faiss-cpu (or chromadb)."""
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Set up retriever
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.load_local("index", embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# Define prompt template
prompt = ChatPromptTemplate.from_template(
    "Answer the question using only this context:\n\n{context}\n\nQuestion: {question}"
)

# Build LCEL chain
llm = ChatOpenAI(model="gpt-4o")
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Execute
result = chain.invoke("What is MCP?")
print(result)
```

### Key differences in this example

| Aspect | AgentForge | LangChain |
|--------|-----------|-----------|
| Install size | `pip install agentforge` (1 dep) | `pip install langchain langchain-openai langchain-community faiss-cpu` (100+ deps) |
| Composition model | DAG with named nodes and edges | LCEL pipe operators |
| Async | Native `await` | Requires `.ainvoke()` variant |
| Observability | Built-in tracing (add `[observe]` extra) | Requires LangSmith account |
| Tool integration | `@tool` decorator, MCP native | `Tool` class, various adapters |

---

## Migration Guide: LangChain to AgentForge

### Step 1: Replace LLM providers

LangChain:
```python
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
response = llm.invoke([HumanMessage(content="Hello")])
```

AgentForge:
```python
from agentforge.llm import get_provider
provider = get_provider("openai", model="gpt-4o", temperature=0.7)
response = await provider.complete([{"role": "user", "content": "Hello"}])
```

For 100+ providers (Anthropic, Cohere, Mistral, etc.), use the LiteLLM extra:
```bash
pip install agentforge[llm]
```
```python
provider = get_provider("litellm", model="anthropic/claude-sonnet-4-20250514")
```

### Step 2: Replace Chains with DAG pipelines

LangChain chains are linear by default. AgentForge DAGs support parallel execution and branching.

LangChain:
```python
chain = prompt | llm | parser  # linear, sequential
```

AgentForge:
```python
dag = DAG(name="pipeline")
dag.add_node("research", research_agent)
dag.add_node("analysis", analysis_agent)
dag.add_node("writer", writer_agent)
dag.add_edge("research", "writer")
dag.add_edge("analysis", "writer")  # research and analysis run in parallel
```

### Step 3: Replace Tools

LangChain:
```python
from langchain.tools import Tool
search_tool = Tool(
    name="search",
    func=search_function,
    description="Search the web",
)
```

AgentForge:
```python
from agentforge import tool

@tool
def search(query: str) -> str:
    """Search the web."""
    return search_function(query)
```

For MCP tools (no LangChain equivalent):
```python
from agentforge import MCPToolRegistry, MCPConfig
registry = MCPToolRegistry()
tools = await registry.register_mcp_server(
    config=MCPConfig(command="npx", args=["-y", "@anthropic/mcp-server-filesystem"]),
    prefix="fs",
)
```

### Step 4: Replace Memory

| LangChain Memory | AgentForge Equivalent |
|---|---|
| `ConversationBufferMemory` | `WorkingMemory` |
| `ConversationSummaryMemory` | `SessionMemory(config=SessionMemoryConfig(...))` |
| `VectorStoreRetrieverMemory` | `FileMemory(config=FileMemoryConfig(...))` |
| N/A | `CheckpointStore` (pipeline state snapshots) |

```python
# LangChain
from langchain.memory import ConversationBufferMemory
memory = ConversationBufferMemory()

# AgentForge
from agentforge import WorkingMemory
memory = WorkingMemory()
```

### Step 5: Replace Observability

LangChain uses LangSmith (proprietary SaaS). AgentForge uses open-standard OpenTelemetry.

```bash
pip install agentforge[observe]
```

```python
from agentforge import AgentTracer, TracerConfig

tracer = AgentTracer(config=TracerConfig(
    service_name="my-pipeline",
    exporter="otlp",
    endpoint="http://localhost:4318",
))
```

Works with Jaeger, Zipkin, Datadog, Grafana Tempo, or any OTel-compatible backend.

### Step 6: Replace Agent definitions

LangChain:
```python
from langchain.agents import initialize_agent, AgentType
agent = initialize_agent(
    tools=[search_tool],
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
)
result = agent.run("Find recent AI news")
```

AgentForge:
```python
from agentforge import Agent, AgentInput

agent = Agent(
    name="researcher",
    instructions="Find and summarize recent AI news.",
    tools=[search],
    llm="openai/gpt-4o",
)
result = await agent(AgentInput(
    messages=[{"role": "user", "content": "Find recent AI news"}]
))
```

---

## When to Choose Each

### Choose AgentForge when:

- **Production performance matters** — use benchmark artifacts in `evidence/benchmarks/`
- **Dependency hygiene is a priority** — 1 dependency vs 112+, smaller attack surface
- **You're building MCP-native pipelines** — first-class Model Context Protocol support
- **You want open observability** — OpenTelemetry instead of proprietary SaaS (LangSmith)
- **You need DAG orchestration** — parallel agent execution with automatic cycle detection
- **You're deploying to lightweight targets** — 8 MB base footprint vs 520 MB

### Choose LangChain when:

- **You need the broadest ecosystem** — 60+ built-in integrations, largest community
- **Your team already uses LangChain** — migration cost may outweigh performance gains
- **You need LangSmith's UI** — hosted tracing/evaluation platform with no setup
- **You're building prototypes** — LCEL pipe syntax is fast for one-off experiments
- **You need Python 3.9 support** — AgentForge requires 3.11+
- **You want pre-built chains** — LangChain Hub has hundreds of community templates

### The pragmatic middle ground

You can use both. AgentForge's `LiteLLMProvider` supports the same model strings as LangChain, and the `@tool` decorator is compatible with any Python function. Start new pipelines in AgentForge for the performance and simplicity benefits, while keeping existing LangChain code running until you have time to migrate it.
