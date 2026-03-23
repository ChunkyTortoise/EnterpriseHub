# ADR 0010: Structured Logging with structlog

## Status

Accepted

## Context

EnterpriseHub's hot-path services — LLM orchestration, error handling, rate limiting — use standard Python `logging.getLogger()` throughout. This produces unstructured text logs that are difficult to query, correlate, and alert on.

Specific observability gaps:
- LLM calls log model name and token count as plain text strings; post-hoc parsing is required to compute cost-per-request metrics
- Error handler logs `correlation_id` as a string field in the message body, making cross-request tracing a grep exercise rather than a structured query
- Rate limiter logs IP addresses and quota status as unstructured text; incident response requires manual log parsing

`structlog` is already listed in `requirements.txt` but is not initialized or used anywhere in the application. The OpenTelemetry SDK is also present; structured logs act as the complement to OTel traces by providing human-readable context at each request boundary.

## Decision

Wire `structlog` into the application via a shared configuration module at `ghl_real_estate_ai/logging_config.py`. Configure structlog to:
- Use `structlog.stdlib.ProcessorFormatter` for compatibility with the standard `logging` module (allows third-party libraries to emit structured logs through the same pipeline)
- In development: render with `structlog.dev.ConsoleRenderer` (color, aligned output)
- In production: render with `structlog.processors.JSONRenderer` (machine-parseable, compatible with Elasticsearch/Kibana)
- Bind `request_id`, `environment`, and `service` to the thread-local context at request startup

Replace `logging.getLogger()` with `structlog.get_logger()` in the three highest-signal locations:

| File | Key bound fields |
|------|-----------------|
| `services/claude_orchestrator.py` | `model`, `provider`, `tokens_in`, `tokens_out`, `cache_hit`, `cost_usd`, `latency_ms` |
| `api/middleware/error_handler.py` | `correlation_id`, `error_type`, `retryable`, `status_code`, `path` |
| `api/middleware/rate_limiter.py` | `ip`, `user_id`, `endpoint`, `remaining_quota`, `window_ms`, `blocked` |

All existing `logger.info(f"...")` calls in these files are replaced with `log.info("event_name", field=value, ...)` style, ensuring fields are queryable without regex parsing.

## Consequences

### Positive
- LLM cost and latency become directly queryable fields in log aggregators (Kibana, Loki, CloudWatch Insights)
- Correlation IDs are automatically propagated as structured fields, enabling cross-request trace reconstruction without grep
- Rate limit events include enough context for automated IP blocking rules without manual log parsing
- Zero behavioral change: structlog integrates transparently with the existing `logging` module configuration

### Negative
- `ProcessorFormatter` adds ~0.5ms per log call vs. bare `logging` — negligible at current request volumes but relevant at >10K RPS
- Structured log output is harder to read in raw `docker logs` output (mitigated by `ConsoleRenderer` in development)
- Migrating all services incrementally means mixed log formats in the transition period; log queries must handle both formats until migration is complete
