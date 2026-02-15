# Unified Configuration System

Centralized YAML-based configuration for all Jorge bots with type-safe Python access.

## Overview

All bot configuration is consolidated in `/ghl_real_estate_ai/config/jorge_bots.yaml` with:
- **Type-safe access** via Python dataclasses
- **Environment overrides** (development/staging/production)
- **Runtime reloading** without service restart
- **Single source of truth** for all operational parameters

## Quick Start

```python
from ghl_real_estate_ai.config.jorge_config_loader import get_config

# Get full configuration
config = get_config()

# Access shared settings
sla_target = config.shared.performance.sla_response_time_seconds  # 15 seconds (30 in dev)
enable_redis = config.shared.caching.enable_l1_redis  # True

# Access bot-specific settings
if config.lead_bot.features.enable_predictive_analytics:
    # Enable predictive features
    pass

# Access circuit breaker config (Task #27)
if config.circuit_breaker.enabled:
    ghl_timeout = config.circuit_breaker.services["ghl"]["timeout_seconds"]  # 30

# Access OpenTelemetry config (Task #25)
if config.opentelemetry.enabled:
    endpoint = config.opentelemetry.exporter["endpoint"]
    sampling_rate = config.opentelemetry.sampling["rate"]
```

## Configuration Structure

### Shared Settings
- **Performance**: SLA targets, concurrency limits, cost tracking
- **Caching**: L1 (Redis), L2 (memory), L3 (disk) with TTLs
- **Observability**: Logging, metrics, OpenTelemetry toggles
- **Integrations**: GHL, Retell, SendGrid, Lyrio, Stripe
- **Handoff**: Confidence thresholds, rate limits, pattern learning

### Bot-Specific Settings

#### Lead Bot
```yaml
lead_bot:
  features:
    enable_predictive_analytics: false
    enable_behavioral_optimization: false
    enable_track3_intelligence: false
  scoring:
    frs_weights:
      timeline_urgency: 0.30
      budget_clarity: 0.25
  temperature_thresholds:
    hot: 80  # HOT >= 80
    warm: 40  # WARM 40-79
```

#### Buyer Bot
```yaml
buyer_bot:
  affordability:
    default_dti_ratio: 0.43
    default_down_payment_percent: 0.20
    default_interest_rate: 0.065
  personas:
    - first_time_buyer
    - upgrader
    - investor
  memory:
    enable_redis_persistence: false  # Task #29
    conversation_window_size: 5
```

#### Seller Bot
```yaml
seller_bot:
  scoring:
    frs_weights:
      timeline_urgency: 0.30
      motivation_strength: 0.25
    pcs_weights:
      engagement_frequency: 0.30
      objection_severity: 0.25
  temperature_thresholds:
    hot: 75
    warm: 50
    lukewarm: 25
```

### Circuit Breaker (Task #27)
```yaml
circuit_breaker:
  enabled: true  # Will be enabled by Task #27
  defaults:
    failure_threshold: 5
    timeout_seconds: 60
  services:
    ghl:
      failure_threshold: 3
      timeout_seconds: 30
```

### OpenTelemetry (Task #25)
```yaml
opentelemetry:
  enabled: true  # Will be enabled by Task #25
  exporter:
    type: otlp
    endpoint: http://localhost:4318
  sampling:
    rate: 0.1  # 10% in production
```

## Environment Overrides

Set `DEPLOYMENT_ENV` environment variable to apply overrides:

```bash
# Development (default)
export DEPLOYMENT_ENV=development
# → log_level: DEBUG, sla: 30s

# Staging
export DEPLOYMENT_ENV=staging
# → log_level: INFO, sampling: 50%

# Production
export DEPLOYMENT_ENV=production
# → log_level: WARNING, circuit_breaker: enabled, sampling: 10%
```

### Development Overrides
- Relaxed SLA (30s vs 15s)
- Debug logging
- 100% sampling

### Production Overrides
- Warning-level logging
- L3 disk caching enabled
- Circuit breakers enabled
- 10% trace sampling

## Runtime Reloading

Update configuration without restarting services:

```python
from ghl_real_estate_ai.config.jorge_config_loader import reload_config

# Edit jorge_bots.yaml
# Then reload:
reload_config()

# New config takes effect immediately
config = get_config()
```

## Type Safety

All configuration values are typed using Python dataclasses:

```python
@dataclass
class PerformanceConfig:
    sla_response_time_seconds: int = 15
    max_concurrent_tasks: int = 5
    cost_per_token: float = 0.000015
    enable_response_streaming: bool = True

@dataclass
class LeadBotFeatures:
    enable_predictive_analytics: bool = False
    enable_behavioral_optimization: bool = False
    # ...
```

IDE autocomplete and type checking work out of the box.

## Configuration Validation

The loader validates:
- YAML syntax
- Required fields present
- Type correctness (int/float/bool/str/list/dict)
- Environment-specific overrides don't break structure

Missing or invalid config falls back to sensible defaults with warnings.

## Migration from Hardcoded Values

Before:
```python
# Scattered across bot files
SLA_TARGET = 15
ENABLE_PREDICTIVE = False
HOT_THRESHOLD = 80
```

After:
```python
from ghl_real_estate_ai.config.jorge_config_loader import get_config

config = get_config()
sla = config.shared.performance.sla_response_time_seconds
enable_predictive = config.lead_bot.features.enable_predictive_analytics
hot_threshold = config.lead_bot.temperature_thresholds["hot"]
```

## Best Practices

1. **Never hardcode operational parameters** - use config
2. **Always access via `get_config()`** - never parse YAML directly
3. **Use environment overrides** - don't edit base config for deployments
4. **Add new settings to YAML first** - then update dataclasses
5. **Document defaults** - explain why values are set

## File Locations

| File | Purpose |
|------|---------|
| `/ghl_real_estate_ai/config/jorge_bots.yaml` | YAML configuration source |
| `/ghl_real_estate_ai/config/jorge_config_loader.py` | Typed config loader |
| `/docs/UNIFIED_CONFIGURATION.md` | This documentation |

## Related Tasks

- **Task #26**: Create unified configuration system (DONE)
- **Task #27**: Add circuit breaker (uses `config.circuit_breaker`)
- **Task #25**: Add OpenTelemetry tracing (uses `config.opentelemetry`)
- **Task #29**: Buyer bot memory (uses `config.buyer_bot.memory`)

## Testing

```bash
# Validate config loads
python -c "from ghl_real_estate_ai.config.jorge_config_loader import get_config; print(get_config())"

# Check environment override
DEPLOYMENT_ENV=production python -c "from ghl_real_estate_ai.config.jorge_config_loader import get_config; print(get_config().shared.observability.log_level)"
```

---

**Created**: February 15, 2026  
**Owner**: DevOps Infrastructure Agent  
**Status**: Production-ready
