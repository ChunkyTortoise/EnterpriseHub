#!/bin/bash
# Infrastructure Verification Script for Phase 3
# Validates all services are deployed and healthy

set -e

echo "=========================================="
echo "Phase 3 Infrastructure Verification"
echo "=========================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ENVIRONMENT=${1:-production}

echo -e "${YELLOW}Environment: $ENVIRONMENT${NC}"
echo ""

# Track overall status
ALL_HEALTHY=true

# Function to check health endpoint
check_health() {
    local service_name=$1
    local health_url=$2

    echo -e "${YELLOW}Checking $service_name...${NC}"

    if curl -f -s "$health_url" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $service_name healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ $service_name health check failed${NC}"
        ALL_HEALTHY=false
        return 1
    fi
}

# Check Railway services
echo "Step 1: Verifying Railway backend services..."
echo ""

# Get Railway service URLs (you'll need to replace these with actual URLs)
WEBSOCKET_URL=$(railway service websocket-manager --environment $ENVIRONMENT 2>/dev/null | grep "URL" | awk '{print $2}' || echo "")
ML_URL=$(railway service ml-manager --environment $ENVIRONMENT 2>/dev/null | grep "URL" | awk '{print $2}' || echo "")
COACHING_URL=$(railway service coaching-manager --environment $ENVIRONMENT 2>/dev/null | grep "URL" | awk '{print $2}' || echo "")
CHURN_URL=$(railway service churn-manager --environment $ENVIRONMENT 2>/dev/null | grep "URL" | awk '{print $2}' || echo "")

if [ -n "$WEBSOCKET_URL" ]; then
    check_health "WebSocket Manager" "${WEBSOCKET_URL}/health/websocket"
else
    echo -e "${RED}✗ WebSocket Manager URL not found${NC}"
    ALL_HEALTHY=false
fi

if [ -n "$ML_URL" ]; then
    check_health "ML Services" "${ML_URL}/health/ml"
else
    echo -e "${RED}✗ ML Services URL not found${NC}"
    ALL_HEALTHY=false
fi

if [ -n "$COACHING_URL" ]; then
    check_health "Coaching Engine" "${COACHING_URL}/health/coaching"
else
    echo -e "${RED}✗ Coaching Engine URL not found${NC}"
    ALL_HEALTHY=false
fi

if [ -n "$CHURN_URL" ]; then
    check_health "Churn Orchestrator" "${CHURN_URL}/health/churn"
else
    echo -e "${RED}✗ Churn Orchestrator URL not found${NC}"
    ALL_HEALTHY=false
fi

# Check Vercel deployment
echo ""
echo "Step 2: Verifying Vercel frontend deployment..."
echo ""

VERCEL_URL=$(vercel ls --json 2>/dev/null | jq -r '.[0].url' || echo "")

if [ -n "$VERCEL_URL" ]; then
    if curl -f -s "https://$VERCEL_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Vercel frontend accessible${NC}"
    else
        echo -e "${RED}✗ Vercel frontend not accessible${NC}"
        ALL_HEALTHY=false
    fi
else
    echo -e "${RED}✗ Vercel deployment URL not found${NC}"
    ALL_HEALTHY=false
fi

# Check database connectivity
echo ""
echo "Step 3: Verifying database connectivity..."
echo ""

python3 << EOF
import sys
import os
try:
    import asyncpg
    import asyncio

    async def check_db():
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("${RED}✗ DATABASE_URL not set${NC}")
            return False

        try:
            conn = await asyncpg.connect(database_url)
            await conn.execute('SELECT 1')
            await conn.close()
            print("${GREEN}✓ Database connection successful${NC}")
            return True
        except Exception as e:
            print(f"${RED}✗ Database connection failed: {e}${NC}")
            return False

    result = asyncio.run(check_db())
    sys.exit(0 if result else 1)

except ImportError:
    print("${YELLOW}⚠ asyncpg not installed, skipping database check${NC}")
    sys.exit(0)
EOF

if [ $? -ne 0 ]; then
    ALL_HEALTHY=false
fi

# Check Redis connectivity
echo ""
echo "Step 4: Verifying Redis connectivity..."
echo ""

python3 << EOF
import sys
import os
try:
    import redis.asyncio as redis
    import asyncio

    async def check_redis():
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            print("${RED}✗ REDIS_URL not set${NC}")
            return False

        try:
            client = redis.from_url(redis_url)
            await client.ping()
            await client.close()
            print("${GREEN}✓ Redis connection successful${NC}")
            return True
        except Exception as e:
            print(f"${RED}✗ Redis connection failed: {e}${NC}")
            return False

    result = asyncio.run(check_redis())
    sys.exit(0 if result else 1)

except ImportError:
    print("${YELLOW}⚠ redis not installed, skipping Redis check${NC}")
    sys.exit(0)
EOF

if [ $? -ne 0 ]; then
    ALL_HEALTHY=false
fi

# Check feature flags
echo ""
echo "Step 5: Verifying feature flags..."
echo ""

python scripts/set_feature_rollout.py --status || {
    echo -e "${RED}✗ Feature flag check failed${NC}"
    ALL_HEALTHY=false
}

# Check monitoring setup
echo ""
echo "Step 6: Verifying monitoring configuration..."
echo ""

# Check if Sentry DSN is configured
if [ -n "$SENTRY_DSN" ]; then
    echo -e "${GREEN}✓ Sentry DSN configured${NC}"
else
    echo -e "${YELLOW}⚠ Sentry DSN not configured${NC}"
fi

# Check if monitoring endpoints are accessible
# (This would check your Grafana/Prometheus setup)

# Final summary
echo ""
echo "=========================================="
if [ "$ALL_HEALTHY" = true ]; then
    echo -e "${GREEN}✓ All Infrastructure Checks Passed${NC}"
    echo "=========================================="
    echo ""
    echo "System is ready for production traffic!"
    echo ""
    echo "Next steps:"
    echo "1. Enable features: python scripts/set_feature_rollout.py --percentage 10 --all-features"
    echo "2. Monitor dashboards: Check Grafana/Railway logs"
    echo "3. Begin A/B testing with 10% rollout"
    exit 0
else
    echo -e "${RED}✗ Infrastructure Verification Failed${NC}"
    echo "=========================================="
    echo ""
    echo "Please fix the issues above before proceeding."
    echo ""
    echo "Troubleshooting:"
    echo "  - Check Railway logs: railway logs --environment $ENVIRONMENT"
    echo "  - Check Vercel logs: vercel logs"
    echo "  - Verify environment variables are set correctly"
    exit 1
fi
