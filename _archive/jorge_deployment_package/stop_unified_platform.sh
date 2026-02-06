#!/bin/bash

echo "🛑 Stopping Jorge's Unified Enhanced AI Bot Platform..."

# Kill services by port
echo "Stopping services on ports 8001, 8002, 8501, 8503..."

for port in 8001 8002 8501 8503; do
    PID=$(lsof -ti:$port)
    if [ ! -z "$PID" ]; then
        kill -TERM $PID 2>/dev/null
        echo "   ✅ Stopped service on port $port (PID: $PID)"
    else
        echo "   ℹ️  No service found on port $port"
    fi
done

echo "🎉 All services stopped successfully!"
