#!/bin/bash
# Health Check Script

ENDPOINT="${1:-http://localhost:8000/health}"

echo "🏥 Checking health endpoint: $ENDPOINT"

response=$(curl -s -o /dev/null -w "%{http_code}" "$ENDPOINT")

if [ "$response" == "200" ]; then
    echo "✅ Health check passed"
    exit 0
else
    echo "❌ Health check failed (HTTP $response)"
    exit 1
fi
