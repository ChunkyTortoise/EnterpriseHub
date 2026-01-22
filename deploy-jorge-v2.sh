#!/bin/bash
# Jorge Salas - GHL Real Estate AI Deployment Script (V2 - Phase 2)
# Deploys the Enhanced Bot Ecosystem (Lead + Seller + Analytics) to Railway

set -e  # Exit on any error

echo "🚀 Jorge Salas - GHL Real Estate AI Deployment (Phase 2)"
echo "========================================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it:"
    echo "   npm install -g @railway/cli"
    echo "   Then run: railway login"
    exit 1
fi

# Check if logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway. Please run:"
    echo "   railway login"
    exit 1
fi

echo "✅ Railway CLI ready"

# Check for required environment file
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.production.template to .env and fill in your keys."
    exit 1
fi

echo "✅ Configuration file found: $ENV_FILE"

# Load environment variables (exporting them for railway cli to pick up if needed, though we set explicitly)
set -a
source "$ENV_FILE"
set +a

# Validate Critical Keys
if [ -z "$VAPI_API_KEY" ] || [[ "$VAPI_API_KEY" == *"your_"* ]]; then
    echo "⚠️  WARNING: VAPI_API_KEY is not set or using default template value."
    echo "   Voice AI features will be disabled in production."
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create Railway project or connect to existing one
read -p "👤 Enter Railway project name (e.g., jorge-ai-ecosystem): " PROJECT_NAME
if [ -z "$PROJECT_NAME" ]; then
    PROJECT_NAME="jorge-ai-ecosystem"
fi

echo "🔧 Setting up Railway project: $PROJECT_NAME"
railway link $PROJECT_NAME 2>/dev/null || railway init $PROJECT_NAME

echo "✅ Railway project ready: $PROJECT_NAME"

# Set environment variables in Railway
echo "🔐 Setting environment variables in Railway..."

# Core Keys
railway variables set GHL_API_KEY="$GHL_API_KEY"
railway variables set GHL_LOCATION_ID="$GHL_LOCATION_ID"
railway variables set ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"

# Phase 2: Voice AI Keys
railway variables set VAPI_API_KEY="$VAPI_API_KEY"
railway variables set VAPI_ASSISTANT_ID="$VAPI_ASSISTANT_ID"

# Phase 2: Seller Bot Config
railway variables set JORGE_SELLER_MODE="$JORGE_SELLER_MODE"
railway variables set CONFRONTATIONAL_TONE="$CONFRONTATIONAL_TONE"
railway variables set JORGE_ANALYTICS_ENABLED="$JORGE_ANALYTICS_ENABLED"
railway variables set HOT_SELLER_THRESHOLD="$HOT_SELLER_THRESHOLD"

# Phase 2: GHL Workflow IDs
railway variables set HOT_SELLER_WORKFLOW_ID="$HOT_SELLER_WORKFLOW_ID"
railway variables set WARM_SELLER_WORKFLOW_ID="$WARM_SELLER_WORKFLOW_ID"
railway variables set AGENT_NOTIFICATION_WORKFLOW="$AGENT_NOTIFICATION_WORKFLOW"

# Phase 2: Custom Field IDs
railway variables set CUSTOM_FIELD_SELLER_TEMPERATURE="$CUSTOM_FIELD_SELLER_TEMPERATURE"
railway variables set CUSTOM_FIELD_SELLER_MOTIVATION="$CUSTOM_FIELD_SELLER_MOTIVATION"
railway variables set CUSTOM_FIELD_TIMELINE_URGENCY="$CUSTOM_FIELD_TIMELINE_URGENCY"
railway variables set CUSTOM_FIELD_PROPERTY_CONDITION="$CUSTOM_FIELD_PROPERTY_CONDITION"
railway variables set CUSTOM_FIELD_PRICE_EXPECTATION="$CUSTOM_FIELD_PRICE_EXPECTATION"

# Legacy/Shared Config
railway variables set ENVIRONMENT="production"
railway variables set LOG_LEVEL="INFO"

echo "✅ Environment variables configured"

# Deploy to Railway
echo "🚀 Deploying to Railway..."
railway deploy 

echo ""
echo "🎉 Deployment Complete!"
echo "======================="

# Get the deployment URL
DEPLOYMENT_URL=$(railway status | grep "URL:" | awk '{print $2}' 2>/dev/null || echo "")

if [ -z "$DEPLOYMENT_URL" ]; then
    echo "📋 Your App URL will be available at: https://$PROJECT_NAME.up.railway.app"
else
    echo "📋 Your App URL is: $DEPLOYMENT_URL"
fi

echo ""
echo "🔧 Post-Deployment Checklist:"
echo "1. Verify the Analytics Dashboard at $DEPLOYMENT_URL"
echo "2. Configure your Vapi.ai assistant using VAPI_ASSISTANT_CONFIG.json"
echo "3. Ensure GHL Webhooks point to $DEPLOYMENT_URL/ghl/webhook"
echo ""
echo "✅ Jorge's Phase 2 Bot Ecosystem is live! 🏠"
