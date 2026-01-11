#!/bin/bash
# Railway Backend Deployment Script for Phase 3
# Deploys all backend services to Railway with proper configuration

set -e

echo "=========================================="
echo "Phase 3 Railway Backend Deployment"
echo "=========================================="

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Environment (default to production)
ENVIRONMENT=${1:-production}

echo -e "${YELLOW}Environment: $ENVIRONMENT${NC}"
echo ""

# Verify Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}Error: Railway CLI not found. Install with: npm install -g @railway/cli${NC}"
    exit 1
fi

# Verify logged in
echo "Step 1: Verifying Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo -e "${RED}Error: Not logged in to Railway. Run: railway login${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Authenticated${NC}"

# Link project if not already linked
echo ""
echo "Step 2: Linking Railway project..."
if ! railway status &> /dev/null; then
    echo "Project not linked. Linking now..."
    railway link
fi
echo -e "${GREEN}✓ Project linked${NC}"

# Set environment
echo ""
echo "Step 3: Setting environment..."
railway environment $ENVIRONMENT
echo -e "${GREEN}✓ Environment set to $ENVIRONMENT${NC}"

# Verify required environment variables
echo ""
echo "Step 4: Verifying environment variables..."

REQUIRED_VARS=(
    "DATABASE_URL"
    "REDIS_URL"
    "ANTHROPIC_API_KEY"
    "GHL_API_KEY"
)

for var in "${REQUIRED_VARS[@]}"; do
    if ! railway variables --environment $ENVIRONMENT | grep -q "$var"; then
        echo -e "${RED}Error: Required variable $var not set${NC}"
        echo "Set it with: railway variables set $var=<value> --environment $ENVIRONMENT"
        exit 1
    fi
    echo -e "${GREEN}✓ $var configured${NC}"
done

# Create Dockerfiles if they don't exist
echo ""
echo "Step 5: Creating service Dockerfiles..."

mkdir -p docker

# WebSocket Manager Dockerfile
cat > docker/Dockerfile.websocket << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ghl_real_estate_ai/ ./ghl_real_estate_ai/
COPY scripts/ ./scripts/

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/health/websocket')"

# Run WebSocket Manager
CMD ["uvicorn", "ghl_real_estate_ai.api.websocket_server:app", "--host", "0.0.0.0", "--port", "8001"]
EOF

# ML Services Dockerfile
cat > docker/Dockerfile.ml << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ghl_real_estate_ai/ ./ghl_real_estate_ai/
COPY scripts/ ./scripts/

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8002/health/ml')"

# Run ML Services
CMD ["uvicorn", "ghl_real_estate_ai.api.ml_server:app", "--host", "0.0.0.0", "--port", "8002"]
EOF

# Coaching Engine Dockerfile
cat > docker/Dockerfile.coaching << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ghl_real_estate_ai/ ./ghl_real_estate_ai/
COPY scripts/ ./scripts/

# Expose port
EXPOSE 8003

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8003/health/coaching')"

# Run Coaching Engine
CMD ["uvicorn", "ghl_real_estate_ai.api.coaching_server:app", "--host", "0.0.0.0", "--port", "8003"]
EOF

# Churn Orchestrator Dockerfile
cat > docker/Dockerfile.churn << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ghl_real_estate_ai/ ./ghl_real_estate_ai/
COPY scripts/ ./scripts/

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8004/health/churn')"

# Run Churn Orchestrator
CMD ["uvicorn", "ghl_real_estate_ai.api.churn_server:app", "--host", "0.0.0.0", "--port", "8004"]
EOF

echo -e "${GREEN}✓ Dockerfiles created${NC}"

# Deploy services
echo ""
echo "Step 6: Deploying services to Railway..."

# Deploy each service
SERVICES=("websocket" "ml" "coaching" "churn")

for service in "${SERVICES[@]}"; do
    echo ""
    echo -e "${YELLOW}Deploying $service service...${NC}"

    # Create service if it doesn't exist
    if ! railway service list | grep -q "$service-manager"; then
        echo "Creating $service-manager service..."
        railway service create $service-manager
    fi

    # Deploy the service
    railway up \
        --service $service-manager \
        --environment $ENVIRONMENT \
        --dockerfile docker/Dockerfile.$service

    echo -e "${GREEN}✓ $service service deployed${NC}"
done

# Wait for deployments to complete
echo ""
echo "Step 7: Waiting for deployments to stabilize..."
sleep 30

# Verify health checks
echo ""
echo "Step 8: Verifying service health..."

for service in "${SERVICES[@]}"; do
    echo -e "${YELLOW}Checking $service service...${NC}"

    # Get service URL
    SERVICE_URL=$(railway service $service-manager --environment $ENVIRONMENT | grep "URL" | awk '{print $2}')

    if [ -z "$SERVICE_URL" ]; then
        echo -e "${RED}Warning: Could not get URL for $service service${NC}"
        continue
    fi

    # Check health endpoint
    if curl -f -s "${SERVICE_URL}/health/$service" > /dev/null; then
        echo -e "${GREEN}✓ $service service healthy${NC}"
    else
        echo -e "${RED}✗ $service service health check failed${NC}"
        echo "Check logs with: railway logs --service $service-manager --environment $ENVIRONMENT"
    fi
done

# Database migration
echo ""
echo "Step 9: Running database migrations..."
python scripts/run_migrations.py --environment $ENVIRONMENT
echo -e "${GREEN}✓ Database migrations complete${NC}"

# Initialize Redis
echo ""
echo "Step 10: Initializing Redis configuration..."
bash scripts/setup_redis_production.sh
echo -e "${GREEN}✓ Redis initialized${NC}"

# Final status
echo ""
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify all services: railway status --environment $ENVIRONMENT"
echo "2. View logs: railway logs --environment $ENVIRONMENT"
echo "3. Enable features: python scripts/set_feature_rollout.py --status"
echo ""
echo "Dashboard: https://railway.app/dashboard"
echo ""
