#!/bin/bash
# Vercel Frontend Deployment Script for Phase 3
# Deploys Streamlit dashboards to Vercel

set -e

echo "=========================================="
echo "Phase 3 Vercel Frontend Deployment"
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

# Verify Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}Error: Vercel CLI not found. Install with: npm install -g vercel${NC}"
    exit 1
fi

# Verify logged in
echo "Step 1: Verifying Vercel authentication..."
if ! vercel whoami &> /dev/null; then
    echo -e "${RED}Error: Not logged in to Vercel. Run: vercel login${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Authenticated${NC}"

# Link project if not already linked
echo ""
echo "Step 2: Linking Vercel project..."
if [ ! -f ".vercel/project.json" ]; then
    echo "Project not linked. Linking now..."
    vercel link
fi
echo -e "${GREEN}✓ Project linked${NC}"

# Create vercel.json configuration
echo ""
echo "Step 3: Creating Vercel configuration..."

cat > vercel.json << 'EOF'
{
  "version": 2,
  "name": "enterprisehub-phase3",
  "builds": [
    {
      "src": "ghl_real_estate_ai/streamlit_components/realtime_lead_intelligence_hub.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb"
      }
    },
    {
      "src": "ghl_real_estate_ai/streamlit_components/agent_coaching_dashboard.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb"
      }
    },
    {
      "src": "ghl_real_estate_ai/streamlit_components/multimodal_document_intelligence_dashboard.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb"
      }
    },
    {
      "src": "ghl_real_estate_ai/streamlit_components/business_intelligence_dashboard.py",
      "use": "@vercel/python",
      "config": {
        "maxLambdaSize": "50mb"
      }
    }
  ],
  "routes": [
    {
      "src": "/intelligence/(.*)",
      "dest": "/ghl_real_estate_ai/streamlit_components/realtime_lead_intelligence_hub.py"
    },
    {
      "src": "/coaching/(.*)",
      "dest": "/ghl_real_estate_ai/streamlit_components/agent_coaching_dashboard.py"
    },
    {
      "src": "/property-intelligence/(.*)",
      "dest": "/ghl_real_estate_ai/streamlit_components/multimodal_document_intelligence_dashboard.py"
    },
    {
      "src": "/analytics/(.*)",
      "dest": "/ghl_real_estate_ai/streamlit_components/business_intelligence_dashboard.py"
    },
    {
      "src": "/(.*)",
      "dest": "/ghl_real_estate_ai/streamlit_components/realtime_lead_intelligence_hub.py"
    }
  ],
  "env": {
    "ENVIRONMENT": "production",
    "STREAMLIT_SERVER_ENABLE_CORS": "false",
    "STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION": "true"
  }
}
EOF

echo -e "${GREEN}✓ Vercel configuration created${NC}"

# Set environment variables
echo ""
echo "Step 4: Configuring environment variables..."

# Check if variables need to be set
REQUIRED_VARS=(
    "RAILWAY_API_URL"
    "REDIS_URL"
    "DATABASE_URL"
    "ANTHROPIC_API_KEY"
)

for var in "${REQUIRED_VARS[@]}"; do
    # Check if variable exists
    if ! vercel env ls production 2>&1 | grep -q "$var"; then
        echo -e "${YELLOW}Setting $var...${NC}"

        # Get value from environment
        VALUE="${!var}"

        if [ -z "$VALUE" ]; then
            echo -e "${RED}Error: $var not found in environment. Please set it.${NC}"
            echo "Example: export $var=<value>"
            exit 1
        fi

        # Add to Vercel
        echo "$VALUE" | vercel env add "$var" production

        echo -e "${GREEN}✓ $var configured${NC}"
    else
        echo -e "${GREEN}✓ $var already configured${NC}"
    fi
done

# Build and deploy
echo ""
echo "Step 5: Building and deploying to Vercel..."

if [ "$ENVIRONMENT" == "production" ]; then
    vercel --prod --yes
else
    vercel --yes
fi

echo -e "${GREEN}✓ Deployment complete${NC}"

# Get deployment URLs
echo ""
echo "Step 6: Retrieving deployment URLs..."

DEPLOYMENT_URL=$(vercel ls --json | jq -r '.[0].url')

echo ""
echo "=========================================="
echo -e "${GREEN}Frontend Deployed Successfully!${NC}"
echo "=========================================="
echo ""
echo "Deployment URL: https://$DEPLOYMENT_URL"
echo ""
echo "Dashboard URLs:"
echo "  Intelligence Hub:    https://$DEPLOYMENT_URL/intelligence"
echo "  Coaching Dashboard:  https://$DEPLOYMENT_URL/coaching"
echo "  Property Intel:      https://$DEPLOYMENT_URL/property-intelligence"
echo "  Analytics:           https://$DEPLOYMENT_URL/analytics"
echo ""
echo "Next steps:"
echo "1. Test dashboards in browser"
echo "2. Configure custom domain (optional): vercel domains add <domain>"
echo "3. Monitor performance: https://vercel.com/dashboard"
echo ""
