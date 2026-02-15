# Observability Configuration

This directory contains configuration files for the OpenTelemetry observability stack.

## Files

- **prometheus.yml** - Prometheus scrape configuration
- **otel_config.py** - OpenTelemetry initialization and auto-instrumentation
- **workflow_tracing.py** - LangGraph workflow tracing decorators and utilities

## Quick Start

```bash
# 1. Start Jaeger and Prometheus
docker-compose -f docker-compose.observability.yml up -d

# 2. Enable tracing in .env
OTEL_ENABLED=true
OTEL_ENDPOINT=http://localhost:4317

# 3. Access Jaeger UI
open http://localhost:16686
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OTEL_ENABLED` | Enable/disable tracing | `false` |
| `OTEL_SERVICE_NAME` | Service name in traces | `enterprisehub` |
| `OTEL_EXPORTER_TYPE` | Exporter type (`otlp`, `jaeger`, `console`) | `otlp` |
| `OTEL_ENDPOINT` | OTLP endpoint URL | `http://localhost:4317` |

### Prometheus Scrape Targets

Edit `prometheus.yml` to add new scrape targets:

```yaml
scrape_configs:
  - job_name: 'my-service'
    static_configs:
      - targets: ['my-service:9090']
```

## Usage

See [DISTRIBUTED_TRACING_GUIDE.md](../docs/DISTRIBUTED_TRACING_GUIDE.md) for full usage documentation.

## Production

For production deployments, use a managed observability backend:

- **Honeycomb** - https://www.honeycomb.io/
- **Datadog** - https://www.datadoghq.com/
- **New Relic** - https://newrelic.com/
- **Grafana Cloud** - https://grafana.com/products/cloud/

Update `OTEL_ENDPOINT` to point to your provider's OTLP endpoint.
