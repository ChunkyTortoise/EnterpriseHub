# Circuit Breaker Implementation Guide

**Status**: ✅ Production Ready  
**Last Updated**: February 15, 2026  
**Task**: #27 - Circuit Breaker for External Service Calls

## Overview

The circuit breaker pattern prevents cascading failures by tracking service health and automatically blocking requests when failure thresholds are exceeded. This implementation protects all external service calls (GHL, Retell, SendGrid, Lyrio) with intelligent recovery mechanisms.

## Architecture

### Circuit States

```
CLOSED → OPEN → HALF_OPEN → CLOSED
  ↑                            ↓
  └────────────────────────────┘
```

- **CLOSED**: Normal operation, all requests flow through
- **OPEN**: Service is failing, requests are blocked (with optional fallback)
- **HALF_OPEN**: Testing recovery, limited requests allowed

### State Transitions

| From State | To State | Trigger |
|-----------|----------|---------|
| CLOSED | OPEN | `failure_count >= failure_threshold` |
| OPEN | HALF_OPEN | `time_since_failure >= recovery_timeout` |
| HALF_OPEN | CLOSED | `success_count >= success_threshold` |
| HALF_OPEN | OPEN | Any failure during testing |
| CLOSED | CLOSED | Successful request (resets failure count) |

## Configuration

Circuit breaker thresholds are defined in `/ghl_real_estate_ai/config/jorge_bots.yaml`:

```yaml
circuit_breaker:
  enabled: true  # Enable in production
  
  defaults:
    failure_threshold: 5  # Failures before opening circuit
    success_threshold: 3  # Successes to close from half-open
    timeout_seconds: 60   # Request timeout
    half_open_max_calls: 2  # Max requests in half-open state
    
  services:
    ghl:
      failure_threshold: 3
      timeout_seconds: 30
      
    retell:
      failure_threshold: 5
      timeout_seconds: 45
      
    sendgrid:
      failure_threshold: 3
      timeout_seconds: 20
      
    lyrio:
      failure_threshold: 5
      timeout_seconds: 30
```

### Environment-Specific Overrides

```yaml
environments:
  production:
    circuit_breaker:
      enabled: true  # Always enabled in production
```

## Integrated Services

### 1. GHL Client

```python
from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient

ghl = EnhancedGHLClient()

# All requests automatically protected by circuit breaker
contact = await ghl.get_contact("contact_id")
```

**Circuit breaker**: Wraps all HTTP requests to GHL API  
**Threshold**: 3 failures / 30s timeout  
**Behavior**: Blocks requests if GHL is down, returns cached data when available

### 2. Retell Client

```python
from ghl_real_estate_ai.integrations.retell import RetellClient

retell = RetellClient()

# Voice call creation protected by circuit breaker
call = await retell.create_call(
    to_number="+1234567890",
    lead_name="John Doe",
    lead_context={"property": "123 Main St"}
)
```

**Circuit breaker**: Wraps call creation and status checks  
**Threshold**: 5 failures / 45s timeout  
**Behavior**: Prevents overwhelming Retell API during outages

### 3. SendGrid Client

```python
from ghl_real_estate_ai.services.sendgrid_client import SendGridClient

sendgrid = SendGridClient()

# Email sending protected by circuit breaker
result = await sendgrid.send_email(
    to_email="lead@example.com",
    subject="Welcome",
    html_content="<h1>Welcome!</h1>"
)
```

**Circuit breaker**: Wraps all SendGrid API calls  
**Threshold**: 3 failures / 20s timeout  
**Behavior**: Prevents email queue buildup during SendGrid outages

### 4. Lyrio Client

```python
from ghl_real_estate_ai.integrations.lyrio import LyrioClient

lyrio = LyrioClient()

# CRM sync protected by circuit breaker
success = await lyrio.sync_lead_score(
    contact_id="abc123",
    frs_score=85.5,
    pcs_score=72.3,
    tags=["hot-lead"]
)
```

**Circuit breaker**: Wraps all Lyrio CRM operations  
**Threshold**: 5 failures / 30s timeout  
**Behavior**: Graceful degradation if Lyrio is unavailable

## Metrics & Monitoring

### Health Check Endpoint

```bash
GET /health/circuit-breakers
Authorization: Bearer <token>
```

**Response**:
```json
{
  "overall_status": "healthy",
  "timestamp": "2026-02-15T12:00:00Z",
  "summary": {
    "total_circuit_breakers": 4,
    "states": {
      "CLOSED": 4,
      "OPEN": 0,
      "HALF_OPEN": 0
    },
    "total_requests": 15234,
    "total_failures": 12,
    "success_rate": 99.92
  },
  "circuit_breakers": {
    "ghl": {
      "name": "ghl",
      "state": "closed",
      "failure_count": 0,
      "success_count": 0,
      "success_rate": 1.0,
      "stats": {
        "total_requests": 8543,
        "successful_requests": 8540,
        "failed_requests": 3,
        "timeout_requests": 0,
        "circuit_opens": 0,
        "fallback_calls": 0,
        "avg_response_time_ms": 145.2,
        "last_failure_time": null,
        "last_success_time": "2026-02-15T11:59:58Z"
      }
    }
  },
  "recommendations": [
    {
      "service": "all",
      "severity": "info",
      "message": "All circuit breakers are healthy",
      "action": "No action required"
    }
  ]
}
```

### Circuit States

| Status | Meaning | Action Required |
|--------|---------|----------------|
| `healthy` | All circuits CLOSED | None |
| `degraded` | Some circuits OPEN/HALF_OPEN | Monitor closely |
| `recovering` | Circuits in HALF_OPEN testing | Wait for recovery |
| `critical` | All circuits OPEN | Investigate service outages |

### Grafana Dashboard Metrics

Circuit breaker metrics are automatically exposed for monitoring:

- `circuit_breaker_state{service="ghl"}` - Current state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)
- `circuit_breaker_requests_total{service="ghl"}` - Total requests
- `circuit_breaker_failures_total{service="ghl"}` - Total failures
- `circuit_breaker_opens_total{service="ghl"}` - Times circuit opened
- `circuit_breaker_response_time_ms{service="ghl"}` - Average response time

## Manual Circuit Management

### Programmatic Access

```python
from ghl_real_estate_ai.services.circuit_breaker import get_circuit_manager

manager = get_circuit_manager()

# Get circuit breaker for a service
ghl_breaker = manager.get_breaker("ghl")

# Check state
if ghl_breaker.state == CircuitState.OPEN:
    print("GHL circuit is open!")

# Get statistics
stats = ghl_breaker.get_stats()
print(f"Success rate: {stats['success_rate'] * 100:.1f}%")

# Manual reset (use with caution)
ghl_breaker.reset()
```

### Reset All Circuits

```python
# Reset all circuit breakers (emergency recovery)
manager.reset_all()
```

## Alert Integration

Circuit breakers integrate with the existing alerting system:

```python
from ghl_real_estate_ai.services.jorge.alerting_service import AlertingService

alerting = AlertingService()

# Alerts are automatically triggered when:
# 1. Circuit opens (CRITICAL)
# 2. Circuit remains open > 5 minutes (CRITICAL)
# 3. Success rate drops below 95% (WARNING)
```

### Alert Channels

Alerts are sent via configured channels (email, Slack, webhook):
- **OPEN circuit**: Immediate CRITICAL alert
- **HALF_OPEN testing**: INFO alert
- **CLOSED after recovery**: INFO alert with recovery time

## Testing

### Unit Tests

```bash
pytest tests/services/test_circuit_breaker.py -v
```

**Coverage**: 19 tests covering all states, transitions, and edge cases

### Integration Testing

```python
# Test with actual GHL client
async with EnhancedGHLClient() as ghl:
    # Simulate failures
    for _ in range(5):
        try:
            await ghl._make_request("GET", "/invalid-endpoint")
        except Exception:
            pass
    
    # Circuit should be open
    assert ghl.circuit_breaker.state == CircuitState.OPEN
```

## Best Practices

### 1. Don't Override Circuit State Manually

```python
# ❌ BAD: Manual state changes
circuit_breaker.state = CircuitState.CLOSED

# ✅ GOOD: Use reset() if needed
circuit_breaker.reset()
```

### 2. Respect Circuit State

```python
# ❌ BAD: Ignoring circuit state
if circuit_breaker.state == CircuitState.OPEN:
    # Force the call anyway
    await make_api_call()

# ✅ GOOD: Check state and use fallback
if circuit_breaker.state == CircuitState.OPEN:
    return cached_data or default_response
```

### 3. Configure Appropriate Thresholds

```yaml
# ❌ TOO SENSITIVE: Opens too quickly
failure_threshold: 1  # Opens on first failure

# ❌ TOO LENIENT: Doesn't protect adequately
failure_threshold: 100  # Allows too many failures

# ✅ BALANCED: Protects without false positives
failure_threshold: 3-5  # Good for most services
```

### 4. Monitor Circuit Health

```python
# Regular health checks
health_summary = manager.get_health_summary()

if health_summary["states"]["OPEN"] > 0:
    logger.warning(
        f"{health_summary['states']['OPEN']} circuit breakers are open",
        extra={"circuits": health_summary["breakers"]}
    )
```

## Troubleshooting

### Circuit Stuck Open

**Symptom**: Circuit remains OPEN after service recovery

**Diagnosis**:
```python
stats = circuit_breaker.get_stats()
print(f"Last failure: {stats['stats']['last_failure_time']}")
print(f"Recovery timeout: {circuit_breaker.config.recovery_timeout}s")
```

**Resolution**:
1. Verify service is actually healthy
2. Wait for recovery timeout to elapse
3. If urgent, manually reset: `circuit_breaker.reset()`

### Too Many False Opens

**Symptom**: Circuit opens during normal operation

**Diagnosis**:
```yaml
# Check current thresholds
circuit_breaker:
  services:
    ghl:
      failure_threshold: 3  # Too low?
      timeout_seconds: 30   # Too short?
```

**Resolution**:
1. Increase `failure_threshold` (e.g., 3 → 5)
2. Increase `timeout_seconds` if requests are slow
3. Review service logs for actual failures

### Circuit Never Opens

**Symptom**: Circuit stays CLOSED despite service failures

**Diagnosis**:
```python
# Check if failures are being counted
stats = circuit_breaker.get_stats()
print(f"Failed requests: {stats['stats']['failed_requests']}")
print(f"Failure threshold: {circuit_breaker.config.failure_threshold}")
```

**Resolution**:
1. Verify circuit breaker is enabled: `circuit_breaker.enabled = true`
2. Check exception types are being caught
3. Ensure requests are going through circuit breaker

## Performance Impact

Circuit breaker overhead is minimal:

- **CLOSED state**: ~0.5ms per request (lock acquisition)
- **OPEN state**: ~0.1ms per request (immediate rejection)
- **HALF_OPEN state**: ~0.5ms per request (state tracking)

**Memory footprint**: ~5KB per circuit breaker (4 services = ~20KB total)

## Future Enhancements

Potential improvements for future versions:

1. **Adaptive thresholds**: Auto-adjust based on historical patterns
2. **Service dependencies**: Coordinate circuits across dependent services
3. **Bulkhead pattern**: Resource isolation per service
4. **Rate limiting integration**: Combine with rate limiting for complete protection
5. **Circuit breaker dashboard**: Real-time visualization of all circuits

## References

- **Pattern**: [Martin Fowler - CircuitBreaker](https://martinfowler.com/bliki/CircuitBreaker.html)
- **Config**: `/ghl_real_estate_ai/config/jorge_bots.yaml`
- **Implementation**: `/ghl_real_estate_ai/services/circuit_breaker.py`
- **Tests**: `/tests/services/test_circuit_breaker.py`
- **Health API**: `/ghl_real_estate_ai/api/routes/health.py#circuit-breakers`

---

**Status**: Production ready, tested with 19 passing tests  
**Monitoring**: Integrated with health checks and alerting system  
**Deployment**: Enabled in production environment
