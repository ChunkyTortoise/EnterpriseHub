# AgentForge — Multi-LLM Orchestrator — $39

## Tagline
**Unified async interface for Claude, Gemini, OpenAI, and Perplexity**

## Description

AgentForge is a lightweight, production-grade orchestrator that unifies access to four leading LLM providers under a single, elegant Python interface. Built for developers who need flexibility without complexity, AgentForge delivers token-aware rate limiting, exponential backoff, structured JSON outputs, and granular cost tracking—all in a 15KB core that's 3x smaller than LangChain.

Gone are the days of wrestling with different API signatures, rate limit handling, and response parsing for each provider. AgentForge normalizes everything: single method calls, consistent response structures, and intelligent provider fallback. The mock provider enables cost-free testing, while per-request cost tracking helps you stay within budget.

Whether you're building AI agents, chat applications, or automation workflows, AgentForge provides the foundation to switch providers, compare models, and scale with confidence.

**Perfect for**: AI application developers, startups building LLM-powered products, teams comparing model performance, and anyone needing reliable multi-provider LLM access.

---

## Key Features

- **Unified Async Interface**: Single API for Claude, Gemini, OpenAI, and Perplexity with consistent response formats
- **Token-Aware Rate Limiting**: Automatic throttling based on provider-specific token limits
- **Exponential Backoff**: Intelligent retry with configurable backoff for rate limits and errors
- **Function Calling**: Native support for tool/function calling across all providers
- **Structured JSON Output**: Guaranteed JSON responses with Pydantic validation
- **Cost Tracking**: Per-request and cumulative cost monitoring with configurable budgets
- **Streaming Support**: Full streaming response handling for real-time applications
- **Mock Provider**: Built-in mock LLM for development and testing without costs
- **CLI Tool**: Command-line interface for quick testing and scripting
- **15KB Core**: Minimal dependencies versus LangChain's 50MB+ footprint

---

## Tech Stack

- **Language**: Python 3.11+
- **HTTP Client**: httpx (async/sync support)
- **CLI Framework**: Click
- **UI Framework**: Streamlit (demo app)
- **API Framework**: FastAPI (optional REST wrapper)
- **Validation**: Pydantic
- **Configuration**: YAML/environment variables

---

## Differentiators

| Aspect | AgentForge | LangChain |
|--------|------------|-----------|
| **Core Size** | ~15KB | 50MB+ |
| **Dependencies** | Minimal | Heavy |
| **Mock Provider** | Built-in | Requires setup |
| **Cost Tracking** | Per-request, granular | Basic |
| **Learning Curve** | Simple, Pythonic | Complex abstractions |
| **Provider Addition** | Easy, documented | Plugin system |
| **JSON Validation** | Native Pydantic | Optional |

---

## What's Included in Your ZIP

```
ai-orchestrator/
├── README.md                    # Getting started guide
├── requirements.txt             # Python dependencies
├── setup.py                     # Package installation
├── pyproject.toml              # Poetry/uv configuration
├── Dockerfile                   # Container deployment
├── docker-compose.yml           # Local development stack
├── config/
│   └── config.yaml             # Provider configurations
├── src/
│   ├── core/
│   │   ├── orchestrator.py      # Main orchestrator class
│   │   ├── client.py           # Base LLM client
│   │   └── types.py            # Request/response types
│   ├── providers/
│   │   ├── base.py             # Provider interface
│   │   ├── anthropic.py        # Claude provider
│   │   ├── google.py           # Gemini provider
│   │   ├── openai.py           # OpenAI provider
│   │   ├── perplexity.py        # Perplexity provider
│   │   └── mock.py             # Mock provider for testing
│   ├── api/
│   │   ├── chat.py             # Chat completion API
│   │   ├── completions.py      # Text completion API
│   │   └── streaming.py        # Streaming response API
│   ├── features/
│   │   ├── rate_limiter.py     # Token-aware rate limiting
│   │   ├── retry.py            # Exponential backoff
│   │   ├── cost_tracker.py     # Usage and cost tracking
│   │   ├── function_calling.py # Tool/function calling
│   │   └── structured_output.py # JSON/Pydantic output
│   └── utils/
│       ├── response.py          # Response normalization
│       └── metrics.py          # Metrics collection
├── cli/
│   └── main.py                 # Click CLI tool
├── ui/
│   ├── app.py                  # Streamlit demo application
│   ├── pages/
│   │   ├── chat.py             # Chat interface
│   │   ├── compare.py          # Model comparison
│   │   └── costs.py            # Cost dashboard
│   └── components/
│       ├── model_selector.py   # Provider/model picker
│       └── response_view.py    # Response display
├── examples/
│   ├── basic_chat.py           # Simple chat example
│   ├── function_calling.py     # Tool usage example
│   ├── cost_tracking.py        # Budget monitoring example
│   └── streaming.py            # Streaming example
├── tests/
│   ├── test_providers.py       # Provider tests
│   ├── test_rate_limiting.py   # Rate limit tests
│   └── test_cost_tracking.py   # Cost tracking tests
├── CUSTOMIZATION.md            # Provider customization guide
├── API_REFERENCE.md            # Complete API documentation
├── COST_GUIDE.md               # Cost optimization strategies
└── ARCHITECTURE.md             # System design overview
```

---

## Suggested Thumbnail Screenshot

**Primary**: Screenshot of the Streamlit demo showing provider comparison with response times and costs

**Secondary options**:
- CLI tool in action showing quick provider testing
- Architecture diagram showing the unified interface layer
- Cost tracking dashboard with usage metrics

---

## Tags for Discoverability

`llm-orchestrator`, `multi-provider`, `claude`, `gemini`, `openai`, `perplexity`, `ai-api`, `async-python`, `rate-limiting`, `cost-tracking`, `function-calling`, `structured-output`, `streaming`, `agent-framework`, `chatbot`, `llm-gateway`, `api-aggregation`, `python`, `lightweight`, `production-ready`

---

## Related Products (Upsell)

| Product | Price | Rationale |
|---------|-------|-----------|
| [AI Document Q&A Engine](/products/product1-docqa-engine.md) | $49 | AgentForge powers the LLM layer for RAG generation |
| [Web Scraper & Price Monitor Toolkit](/products/product3-scrape-and-serve.md) | $29 | Enrich prompts with scraped data via AgentForge |
| [Data Intelligence Dashboard](/products/product4-insight-engine.md) | $39 | Visualize AgentForge usage and cost metrics |

---

## Quick Start Example

```python
from agentforge import AgentForge

# Initialize with any provider
orchestrator = AgentForge(provider="anthropic")

# Unified API for all providers
response = await orchestrator.chat(
    messages=[{"role": "user", "content": "Hello!"}],
    temperature=0.7,
    max_tokens=1000
)

# Check costs
print(f"This request cost: ${orchestrator.get_last_cost():.4f}")
```

---

## Support

- Documentation: See `README.md` and `API_REFERENCE.md` in your ZIP
- Examples: `/examples` directory with ready-to-run scripts
- Issues: Create an issue on the GitHub repository
- Email: caymanroden@gmail.com

---

**License**: MIT License — Use in unlimited projects

**Refund Policy**: 30-day money-back guarantee if the product doesn't meet your requirements