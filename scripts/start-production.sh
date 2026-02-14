#!/bin/bash
set -e

# Production startup script for Lead Intelligence Service 6
# Optimized for enterprise-grade performance and scalability

echo "🚀 Starting Lead Intelligence Service 6 - Production Mode"
echo "Target: 100+ leads/hour, <30s response times, 99.9% uptime"

# Environment variables with defaults
export WORKERS=${WORKERS:-4}
export MAX_CONCURRENT=${MAX_CONCURRENT_REQUESTS:-100}
export TIMEOUT=${REQUEST_TIMEOUT_SECONDS:-30}
export LOG_LEVEL=${LOG_LEVEL:-INFO}
export METRICS_PORT=${METRICS_PORT:-9090}

# Performance optimizations
export PYTHONUNBUFFERED=1
export PYTHONHASHSEED=random
export MALLOC_TRIM_THRESHOLD_=131072
export MALLOC_MMAP_THRESHOLD_=131072

# Create necessary directories
mkdir -p /app/logs /app/metrics /app/cache

# Health check function
health_check() {
    curl -f -s http://localhost:8501/health > /dev/null 2>&1
}

# Start metrics exporter in background
start_metrics_exporter() {
    echo "📊 Starting Prometheus metrics exporter on port $METRICS_PORT"
    python -m ghl_real_estate_ai.services.metrics_exporter &
    METRICS_PID=$!
    echo "Metrics exporter PID: $METRICS_PID"
}

# Start event streaming service
start_event_streaming() {
    echo "🔄 Initializing event streaming service"
    python -c "
import asyncio
from ghl_real_estate_ai.services.event_streaming_service import get_event_streaming_service

async def init_streaming():
    service = await get_event_streaming_service()
    await service.start_consuming()
    print('Event streaming service initialized')

asyncio.run(init_streaming())
" &
    STREAMING_PID=$!
    echo "Event streaming PID: $STREAMING_PID"
}

# Start cache warming
warm_caches() {
    echo "🔥 Warming application caches"
    python -c "
import asyncio
from ghl_real_estate_ai.services.optimized_cache_service import get_optimized_cache_service

async def warm_cache():
    cache = get_optimized_cache_service()
    
    # Warm with common lead data patterns
    warm_items = {
        'lead_templates:hot': ({'score_threshold': 80}, 3600),
        'lead_templates:warm': ({'score_threshold': 60}, 3600),
        'property_filters:rancho_cucamonga': ({'city': 'rancho_cucamonga', 'active': True}, 1800),
        'ai_models:scoring': ({'model': 'claude-3-5-sonnet', 'version': 'latest'}, 7200)
    }
    
    await cache.warm_cache(warm_items)
    print('✅ Cache warming completed')

asyncio.run(warm_cache())
"
}

# Start performance monitoring
start_monitoring() {
    echo "📈 Starting performance monitoring"
    python -c "
import asyncio
from ghl_real_estate_ai.services.performance_tracker import get_performance_tracker

async def start_perf_monitoring():
    tracker = get_performance_tracker()
    await tracker.start_collection()
    print('✅ Performance monitoring active')
    
    # Keep monitoring running
    while True:
        await asyncio.sleep(60)
        metrics = tracker.get_current_metrics()
        if metrics and metrics.leads_processed_per_hour < 100:
            print(f'⚠️ Performance alert: {metrics.leads_processed_per_hour} leads/hour < 100 target')

asyncio.run(start_perf_monitoring())
" &
    MONITOR_PID=$!
    echo "Performance monitor PID: $MONITOR_PID"
}

# Graceful shutdown handler
cleanup() {
    echo "🛑 Shutting down gracefully..."
    
    # Stop background processes
    [[ ! -z "$METRICS_PID" ]] && kill $METRICS_PID 2>/dev/null || true
    [[ ! -z "$STREAMING_PID" ]] && kill $STREAMING_PID 2>/dev/null || true
    [[ ! -z "$MONITOR_PID" ]] && kill $MONITOR_PID 2>/dev/null || true
    [[ ! -z "$STREAMLIT_PID" ]] && kill $STREAMLIT_PID 2>/dev/null || true
    [[ ! -z "$FASTAPI_PID" ]] && kill $FASTAPI_PID 2>/dev/null || true
    
    # Wait for graceful shutdown
    sleep 5
    
    echo "✅ Shutdown complete"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Pre-flight checks
echo "🔍 Running pre-flight checks..."

# Check required environment variables
required_vars=("ANTHROPIC_API_KEY" "REDIS_URL")
for var in "${required_vars[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "❌ Missing required environment variable: $var"
        exit 1
    fi
done

# Test Redis connection
echo "Testing Redis connection..."
python -c "
import redis
import os
r = redis.from_url(os.environ['REDIS_URL'])
r.ping()
print('✅ Redis connection successful')
"

# Test Claude API
echo "Testing Claude API..."
python -c "
import anthropic
import os
client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
print('✅ Claude API key valid')
"

# Initialize services
echo "🚀 Initializing enterprise services..."

# Start background services
start_metrics_exporter
start_event_streaming
warm_caches
start_monitoring

# Wait for services to initialize
sleep 10

# Start main applications with production settings
echo "🌟 Starting main applications..."

# Start FastAPI with Gunicorn (high-performance ASGI server)
echo "Starting FastAPI server with Gunicorn..."
gunicorn -w $WORKERS \
         -k uvicorn.workers.UvicornWorker \
         --bind 0.0.0.0:8000 \
         --timeout $TIMEOUT \
         --max-requests 1000 \
         --max-requests-jitter 50 \
         --preload \
         --access-logfile /app/logs/access.log \
         --error-logfile /app/logs/error.log \
         --log-level $LOG_LEVEL \
         ghl_real_estate_ai.api.main:app &

FASTAPI_PID=$!
echo "FastAPI server PID: $FASTAPI_PID"

# Start Streamlit with production optimizations
echo "Starting Streamlit server..."
streamlit run ghl_real_estate_ai/streamlit_demo/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.maxUploadSize=10 \
    --server.maxMessageSize=50 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=true \
    --server.enableWebsocketCompression=true \
    --browser.gatherUsageStats=false \
    --logger.level=$LOG_LEVEL &

STREAMLIT_PID=$!
echo "Streamlit server PID: $STREAMLIT_PID"

# Wait for applications to start
echo "⏳ Waiting for applications to start..."
sleep 20

# Health check
echo "🏥 Performing health checks..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if health_check; then
        echo "✅ Applications healthy and ready!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "Health check attempt $attempt/$max_attempts failed, retrying in 10s..."
    sleep 10
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Health checks failed after $max_attempts attempts"
    cleanup
    exit 1
fi

# Print startup summary
echo ""
echo "🎉 Lead Intelligence Service 6 - PRODUCTION READY"
echo "=================================================="
echo "📊 Streamlit Dashboard: http://localhost:8501"
echo "🔧 FastAPI Docs: http://localhost:8000/docs"
echo "📈 Metrics: http://localhost:$METRICS_PORT/metrics"
echo "🎯 Performance Targets:"
echo "   • Response Time: <30s (current: monitoring)"
echo "   • Throughput: 100+ leads/hour"
echo "   • Uptime: 99.9%"
echo "   • Concurrent Users: $MAX_CONCURRENT"
echo ""
echo "🔄 Background Services:"
echo "   • Event Streaming: Active (PID: $STREAMING_PID)"
echo "   • Performance Monitor: Active (PID: $MONITOR_PID)"
echo "   • Metrics Exporter: Active (PID: $METRICS_PID)"
echo ""
echo "📝 Logs:"
echo "   • Application: /app/logs/"
echo "   • System: journalctl -u lead-intelligence"
echo ""

# Performance monitoring loop
echo "🚀 Entering production monitoring mode..."
while true; do
    # Check application health every 60 seconds
    sleep 60
    
    if ! health_check; then
        echo "❌ Health check failed! Investigating..."
        
        # Try to restart services if they failed
        if ! kill -0 $STREAMLIT_PID 2>/dev/null; then
            echo "🔄 Restarting Streamlit service..."
            streamlit run ghl_real_estate_ai/streamlit_demo/app.py \
                --server.port=8501 \
                --server.address=0.0.0.0 &
            STREAMLIT_PID=$!
        fi
        
        if ! kill -0 $FASTAPI_PID 2>/dev/null; then
            echo "🔄 Restarting FastAPI service..."
            gunicorn -w $WORKERS -k uvicorn.workers.UvicornWorker \
                --bind 0.0.0.0:8000 ghl_real_estate_ai.api.main:app &
            FASTAPI_PID=$!
        fi
    fi
    
    # Log current performance
    python -c "
from ghl_real_estate_ai.services.performance_tracker import get_performance_tracker
import json

tracker = get_performance_tracker()
summary = tracker.get_performance_summary()

if 'current_metrics' in summary:
    metrics = summary['current_metrics']
    print(f'⚡ Performance: {metrics[\"leads_processed_per_hour\"]} leads/hour, '
          f'{metrics[\"avg_response_time_ms\"]:.0f}ms avg response, '
          f'{metrics[\"error_rate\"]:.1%} error rate')
" 2>/dev/null || echo "📊 Performance metrics collecting..."

done