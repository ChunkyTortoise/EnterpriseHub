#!/bin/bash
# ==============================================================================
# Start OpenTelemetry Observability Stack for Local Development
# ==============================================================================
# Starts Jaeger for distributed tracing visualization
#
# Usage:
#   ./scripts/start_tracing.sh          # Start services
#   ./scripts/start_tracing.sh stop     # Stop services
#   ./scripts/start_tracing.sh restart  # Restart services
# ==============================================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.observability.yml"

cd "$PROJECT_ROOT"

case "${1:-start}" in
    start)
        echo "Starting OpenTelemetry observability stack..."
        docker-compose -f "$COMPOSE_FILE" up -d
        
        echo ""
        echo "✅ Observability stack started!"
        echo ""
        echo "Access Points:"
        echo "  Jaeger UI:    http://localhost:16686"
        echo "  Prometheus:   http://localhost:9090"
        echo "  OTLP gRPC:    localhost:4317"
        echo "  OTLP HTTP:    localhost:4318"
        echo ""
        echo "Next steps:"
        echo "  1. Add to .env:"
        echo "     OTEL_ENABLED=true"
        echo "     OTEL_ENDPOINT=http://localhost:4317"
        echo ""
        echo "  2. Start your application:"
        echo "     uvicorn ghl_real_estate_ai.app:app --reload"
        echo ""
        echo "  3. Trigger some bot workflows (via webhook or API)"
        echo ""
        echo "  4. View traces in Jaeger UI: http://localhost:16686"
        ;;
    
    stop)
        echo "Stopping OpenTelemetry observability stack..."
        docker-compose -f "$COMPOSE_FILE" down
        echo "✅ Observability stack stopped!"
        ;;
    
    restart)
        echo "Restarting OpenTelemetry observability stack..."
        docker-compose -f "$COMPOSE_FILE" restart
        echo "✅ Observability stack restarted!"
        ;;
    
    logs)
        docker-compose -f "$COMPOSE_FILE" logs -f
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|logs}"
        exit 1
        ;;
esac
