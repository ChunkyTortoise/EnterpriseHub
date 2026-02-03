# EnterpriseHub Feature Flags

**Version**: 1.0
**Last Updated**: February 2, 2026

---

## Overview

Feature flags allow runtime control of optional platform capabilities without redeployment. All flags are configured via environment variables and loaded by Pydantic settings at application startup.

**Configuration source**: `ghl_real_estate_ai/ghl_utils/config.py`

**Important**: Feature flag changes require a pod restart to take effect, since settings are loaded once at import time.

---

## Phase 1-2: Foundation Optimizations

### ENABLE_CONVERSATION_OPTIMIZATION

| Property | Value |
|----------|-------|
| **Default** | `false` |
| **Phase** | 1-2 |
| **Impact** | Reduces token usage by optimizing conversation history |
| **Dependencies** | None |

Optimizes conversation context sent to Claude by trimming irrelevant history and compressing older messages. Reduces token consumption for multi-turn conversations.

```bash
export ENABLE_CONVERSATION_OPTIMIZATION=true
```

---

### ENABLE_ENHANCED_CACHING

| Property | Value |
|----------|-------|
| **Default** | `false` |
| **Phase** | 1-2 |
| **Impact** | Improves response times via multi-tier caching |
| **Dependencies** | Redis (`REDIS_URL`) |

Enables the L1 (Redis) / L2 (Application) / L3 (Database) tiered caching strategy. Reduces database load and improves response times for frequently accessed data.

```bash
export ENABLE_ENHANCED_CACHING=true
```

---

### ENABLE_ASYNC_OPTIMIZATION

| Property | Value |
|----------|-------|
| **Default** | `false` |
| **Phase** | 1-2 |
| **Impact** | Parallelizes I/O operations for faster responses |
| **Dependencies** | None |

Enables async/await parallelization for independent I/O operations (database queries, API calls, cache lookups). Reduces response times by executing non-dependent operations concurrently.

```bash
export ENABLE_ASYNC_OPTIMIZATION=true
```

---

## Phase 3-4: Advanced Optimizations (80-90% Cost Reduction)

### ENABLE_TOKEN_BUDGET_ENFORCEMENT

| Property | Value |
|----------|-------|
| **Default** | `false` |
| **Phase** | 3-4 |
| **Impact** | Enforces monthly/daily token budgets per tenant |
| **Dependencies** | Database for tracking |

Enforces configurable token budgets to prevent runaway AI costs. Tracks usage per tenant and alerts when approaching limits.

**Related configuration**:
```bash
export ENABLE_TOKEN_BUDGET_ENFORCEMENT=true
export TOKEN_BUDGET_DEFAULT_MONTHLY=100000
export TOKEN_BUDGET_DEFAULT_DAILY=5000
```

---

### ENABLE_DATABASE_CONNECTION_POOLING

| Property | Value |
|----------|-------|
| **Default** | `false` |
| **Phase** | 3-4 |
| **Impact** | Optimizes database connection management |
| **Dependencies** | PostgreSQL (`DATABASE_URL`) |

Enables advanced connection pooling with configurable pool size and overflow. Prevents connection exhaustion under high load.

**Related configuration**:
```bash
export ENABLE_DATABASE_CONNECTION_POOLING=true
export DB_POOL_SIZE=20
export DB_MAX_OVERFLOW=10
```

---

### ENABLE_SEMANTIC_RESPONSE_CACHING

| Property | Value |
|----------|-------|
| **Default** | `false` |
| **Phase** | 3-4 |
| **Impact** | Caches semantically similar AI responses |
| **Dependencies** | Redis, vector embeddings |

Uses semantic similarity matching to cache and reuse AI responses for similar queries. Reduces Claude API calls for common question patterns (e.g., "What's available in Victoria?" vs "Show me Victoria homes").

**Related configuration**:
```bash
export ENABLE_SEMANTIC_RESPONSE_CACHING=true
export SEMANTIC_CACHE_SIMILARITY_THRESHOLD=0.85
export SEMANTIC_CACHE_TTL=3600
```

---

### ENABLE_MULTI_TENANT_OPTIMIZATION

| Property | Value |
|----------|-------|
| **Default** | `false` |
| **Phase** | 3-4 |
| **Impact** | Enables per-tenant resource isolation and optimization |
| **Dependencies** | Database, Redis |

Enables multi-tenant resource isolation, per-tenant configuration, and cross-tenant analytics. Required for SaaS deployments serving multiple real estate agencies.

```bash
export ENABLE_MULTI_TENANT_OPTIMIZATION=true
```

---

### ENABLE_ADVANCED_ANALYTICS

| Property | Value |
|----------|-------|
| **Default** | `false` |
| **Phase** | 3-4 |
| **Impact** | Enables predictive analytics, ML scoring, and BI features |
| **Dependencies** | Database, sufficient historical data |

Enables the advanced analytics engine including Monte Carlo scenario simulation, market sentiment analysis, predictive lead scoring, and the full BI dashboard capabilities.

```bash
export ENABLE_ADVANCED_ANALYTICS=true
```

---

### ENABLE_COST_PREDICTION

| Property | Value |
|----------|-------|
| **Default** | `false` |
| **Phase** | 3-4 |
| **Impact** | Predicts AI costs and optimizes model selection |
| **Dependencies** | Token tracking enabled |

Enables cost prediction and intelligent model routing. Automatically selects the most cost-effective model (Haiku vs Sonnet vs Opus) based on query complexity.

**Model cost reference** (per 1M tokens, configured in `config.py`):

| Model | Input | Output |
|-------|-------|--------|
| Claude Sonnet | $3.00 | $15.00 |
| Gemini Flash | $1.25 | $3.75 |
| Perplexity Sonar | $1.00 | $1.00 |

```bash
export ENABLE_COST_PREDICTION=true
```

---

## Jorge Seller Bot: Optional Features

Three fully-implemented but opt-in features for the Jorge Seller Bot. Managed by the centralized config at `ghl_real_estate_ai/config/feature_config.py`.

| Feature | Env Var | Benefit | Default |
|---------|---------|---------|---------|
| Progressive Skills | `ENABLE_PROGRESSIVE_SKILLS` | 68% token reduction | `false` |
| Agent Mesh | `ENABLE_AGENT_MESH` | Enterprise task orchestration | `false` |
| MCP Integration | `ENABLE_MCP_INTEGRATION` | Standardized CRM/MLS access | `false` |
| Adaptive Questioning | `ENABLE_ADAPTIVE_QUESTIONING` | Dynamic question selection | `false` |
| Track 3.1 Intelligence | `ENABLE_TRACK3_INTELLIGENCE` | ML-enhanced predictions | `true` |
| Bot Intelligence | `ENABLE_BOT_INTELLIGENCE` | Conversation middleware | `true` |

### Progressive Skills

68% token reduction through two-phase qualification (discovery + execution) instead of full-context prompts.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_PROGRESSIVE_SKILLS` | bool | `false` | Enable progressive skills |
| `PROGRESSIVE_SKILLS_MODEL` | string | `claude-sonnet-4` | Model for skill execution |
| `PROGRESSIVE_SKILLS_PATH` | string | `skills/` | Skills definition directory |
| `PROGRESSIVE_SKILLS_CACHE_TTL` | int | `3600` | Skill cache TTL (seconds) |

**Performance**: ~272 tokens per qualification vs 853 baseline (68% reduction).

**Monitoring**: `workflow_stats["progressive_skills_usage"]`, `workflow_stats["token_savings"]`

### Agent Mesh

Enterprise orchestration for parallel task execution (property valuation, market intelligence).

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_AGENT_MESH` | bool | `false` | Enable agent mesh |
| `AGENT_MESH_MAX_AGENTS` | int | `10` | Max concurrent agents |
| `AGENT_MESH_ROUTING_STRATEGY` | string | `capability_based` | Routing strategy |
| `AGENT_MESH_MAX_COST` | float | `5.0` | Max cost per task (USD) |
| `AGENT_MESH_TASK_TIMEOUT` | int | `30` | Task timeout (seconds) |

**Monitoring**: `workflow_stats["mesh_orchestrations"]`

### MCP Integration

Standardized access to CRM (GoHighLevel) and MLS data via Model Context Protocol.

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ENABLE_MCP_INTEGRATION` | bool | `false` | Enable MCP integration |
| `MCP_CONFIG_PATH` | string | `mcp_config.json` | MCP server config path |
| `MCP_REQUEST_TIMEOUT` | int | `10` | Request timeout (seconds) |
| `MCP_MAX_RETRIES` | int | `3` | Max retries per request |

**Monitoring**: `workflow_stats["mcp_calls"]`

### Factory Methods

```python
from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

# Standard: Track 3.1 only
bot = JorgeSellerBot.create_standard_jorge()

# Progressive: Track 3.1 + progressive skills + bot intelligence
bot = JorgeSellerBot.create_progressive_jorge()

# Enterprise: All features enabled
bot = JorgeSellerBot.create_enterprise_jorge()
```

### Using Centralized Config

```python
from ghl_real_estate_ai.config.feature_config import (
    load_feature_config_from_env,
    feature_config_to_jorge_kwargs,
)
from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot, JorgeFeatureConfig

config = load_feature_config_from_env()
kwargs = feature_config_to_jorge_kwargs(config)
bot = JorgeSellerBot(config=JorgeFeatureConfig(**kwargs))
```

### Jorge Bot Monitoring

Access runtime metrics via `bot.get_performance_metrics()`:

```python
metrics = await bot.get_performance_metrics()
# {
#   "workflow_statistics": { ... },
#   "features_enabled": { "progressive_skills": true, ... },
#   "progressive_skills": { "average_token_reduction_percent": 68.1, ... }
# }
```

---

## Recommended Configurations

### Development

```bash
# All flags off - use demo mode
ENVIRONMENT=development
ENABLE_CONVERSATION_OPTIMIZATION=false
ENABLE_ENHANCED_CACHING=false
ENABLE_ASYNC_OPTIMIZATION=false
```

### Staging

```bash
# Enable foundation optimizations for testing
ENVIRONMENT=staging
ENABLE_CONVERSATION_OPTIMIZATION=true
ENABLE_ENHANCED_CACHING=true
ENABLE_ASYNC_OPTIMIZATION=true
ENABLE_TOKEN_BUDGET_ENFORCEMENT=true
```

### Production

```bash
# Full optimization stack
ENVIRONMENT=production
ENABLE_CONVERSATION_OPTIMIZATION=true
ENABLE_ENHANCED_CACHING=true
ENABLE_ASYNC_OPTIMIZATION=true
ENABLE_TOKEN_BUDGET_ENFORCEMENT=true
ENABLE_DATABASE_CONNECTION_POOLING=true
ENABLE_SEMANTIC_RESPONSE_CACHING=true
ENABLE_MULTI_TENANT_OPTIMIZATION=true
ENABLE_ADVANCED_ANALYTICS=true
ENABLE_COST_PREDICTION=true

# Jorge Bot optional features
ENABLE_PROGRESSIVE_SKILLS=true
ENABLE_AGENT_MESH=true
ENABLE_MCP_INTEGRATION=true
ENABLE_ADAPTIVE_QUESTIONING=true
```

---

## Rollback Procedure

If a feature flag causes issues in production:

```bash
# 1. Disable the flag
kubectl set env deployment/jorge-api \
  ENABLE_PROBLEMATIC_FEATURE=false \
  -n production

# 2. Restart pods to apply (settings load at startup)
kubectl rollout restart deployment/jorge-api -n production

# 3. Monitor for stability
kubectl logs -n production -l app=jorge-api --tail=50 -f

# 4. Verify flag is disabled
kubectl exec -it jorge-api-pod -- python -c \
  "from ghl_real_estate_ai.ghl_utils.config import settings; \
   print(settings.enable_problematic_feature)"
```

---

## Adding New Feature Flags

1. Add the field to `Settings` class in `ghl_real_estate_ai/ghl_utils/config.py`:
   ```python
   enable_new_feature: bool = False
   ```

2. Add the environment variable to `.env.example`:
   ```bash
   ENABLE_NEW_FEATURE=false
   ```

3. Use in code:
   ```python
   from ghl_real_estate_ai.ghl_utils.config import settings

   if settings.enable_new_feature:
       # New feature logic
   else:
       # Default behavior
   ```

4. Document in this file with phase, impact, and dependencies.

---

**Version**: 1.0 | **Last Updated**: February 2, 2026
