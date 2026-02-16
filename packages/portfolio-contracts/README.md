# portfolio-contracts

Shared Pydantic v2 type contracts for AI portfolio products.

## Install

```bash
pip install portfolio-contracts
```

## Usage

```python
from portfolio_contracts import LLMResponse, LLMProvider, TokenUsage

response = LLMResponse(
    content="Hello",
    provider=LLMProvider.ANTHROPIC,
    model="claude-opus-4-6",
    usage=TokenUsage(input_tokens=10, output_tokens=20),
)
```

## Modules

- `portfolio_contracts.llm` — LLMProvider, TokenUsage, CostEstimate, LLMResponse
- `portfolio_contracts.documents` — DocumentType, DocumentChunk, DocumentMetadata
- `portfolio_contracts.api` — APIError, ErrorDetail, PaginationMeta
- `portfolio_contracts.agents` — AgentStatus, AgentAction
