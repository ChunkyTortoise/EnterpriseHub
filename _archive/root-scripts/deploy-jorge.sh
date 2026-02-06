#!/bin/bash
# Jorge Salas - GHL Real Estate AI Deployment Script
# Deploys the AI system to Railway for Jorge's specific configuration

set -e  # Exit on any error

echo "🚀 Jorge Salas - GHL Real Estate AI Deployment"
echo "=============================================="

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
if [ ! -f ".env.jorge" ]; then
    echo "❌ .env.jorge file not found!"
    echo ""
    echo "Please create .env.jorge with Jorge's API keys:"
    echo "1. Copy .env.jorge.template to .env.jorge"
    echo "2. Fill in the required API keys:"
    echo "   - GHL_API_KEY"
    echo "   - GHL_LOCATION_ID"
    echo "   - ANTHROPIC_API_KEY"
    echo "3. Run this script again"
    exit 1
fi

echo "✅ Configuration file found"

# Load environment variables
source .env.jorge

# Validate required variables
if [ -z "$GHL_API_KEY" ] || [ "$GHL_API_KEY" = "your_ghl_api_key_here" ]; then
    echo "❌ GHL_API_KEY not set in .env.jorge"
    exit 1
fi

if [ -z "$GHL_LOCATION_ID" ] || [ "$GHL_LOCATION_ID" = "your_ghl_location_id_here" ]; then
    echo "❌ GHL_LOCATION_ID not set in .env.jorge"
    exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_anthropic_api_key_here" ]; then
    echo "❌ ANTHROPIC_API_KEY not set in .env.jorge"
    exit 1
fi

echo "✅ Required API keys configured"

# Create Railway project or connect to existing one
read -p "👤 Enter Railway project name (e.g., jorge-ai-assistant): " PROJECT_NAME

if [ -z "$PROJECT_NAME" ]; then
    PROJECT_NAME="jorge-ai-assistant"
fi

echo "🔧 Setting up Railway project: $PROJECT_NAME"

# Try to connect to existing project or create new one
railway link $PROJECT_NAME 2>/dev/null || railway init $PROJECT_NAME

echo "✅ Railway project ready: $PROJECT_NAME"

# Set environment variables in Railway
echo "🔐 Setting environment variables in Railway..."

railway variables set GHL_API_KEY="$GHL_API_KEY"
railway variables set GHL_LOCATION_ID="$GHL_LOCATION_ID"
railway variables set ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"

# Optional variables (only set if provided)
if [ ! -z "$GHL_CALENDAR_ID" ] && [ "$GHL_CALENDAR_ID" != "your_ghl_calendar_id_here" ]; then
    railway variables set GHL_CALENDAR_ID="$GHL_CALENDAR_ID"
fi

if [ ! -z "$NOTIFY_AGENT_WORKFLOW_ID" ] && [ "$NOTIFY_AGENT_WORKFLOW_ID" != "your_notification_workflow_id_here" ]; then
    railway variables set NOTIFY_AGENT_WORKFLOW_ID="$NOTIFY_AGENT_WORKFLOW_ID"
fi

if [ ! -z "$GHL_WEBHOOK_SECRET" ] && [ "$GHL_WEBHOOK_SECRET" != "your_webhook_secret_here" ]; then
    railway variables set GHL_WEBHOOK_SECRET="$GHL_WEBHOOK_SECRET"
fi

# Set Jorge's specific configuration
railway variables set AUTO_DEACTIVATE_THRESHOLD="70"
railway variables set ACTIVATION_TAGS='["Needs Qualifying"]'
railway variables set DEACTIVATION_TAGS='["AI-Off","Qualified","Stop-Bot","AI-Qualified"]'
railway variables set HOT_LEAD_THRESHOLD="3"
railway variables set WARM_LEAD_THRESHOLD="2"
railway variables set ENVIRONMENT="production"
railway variables set LOG_LEVEL="INFO"
railway variables set CLAUDE_MODEL="claude-sonnet-4-20250514"
railway variables set TEMPERATURE="0.7"
railway variables set MAX_TOKENS="150"

echo "✅ Environment variables configured"

# Deploy to Railway
echo "🚀 Deploying to Railway..."
railway deploy --config railway.jorge.toml

echo ""
echo "🎉 Deployment Complete!"
echo "======================="

# Get the deployment URL
DEPLOYMENT_URL=$(railway status | grep "URL:" | awk '{print $2}' 2>/dev/null || echo "")

if [ -z "$DEPLOYMENT_URL" ]; then
    echo "📋 Your webhook URL will be available at:"
    echo "   https://$PROJECT_NAME.up.railway.app/ghl/webhook"
else
    echo "📋 Your webhook URL is:"
    echo "   $DEPLOYMENT_URL/ghl/webhook"
fi

echo ""
echo "🔧 Next Steps for Jorge:"
echo "========================"
echo "1. Copy the webhook URL above"
echo "2. In GHL, go to Automations > Workflows"
echo "3. Find your workflow that applies 'Needs Qualifying' tag"
echo "4. Add webhook action with:"
echo "   - URL: [webhook URL above]"
echo "   - Method: POST"
echo "   - Events: Inbound Message"
echo "5. Test by tagging a contact 'Needs Qualifying' and sending a message"
echo ""
echo "💡 AI will:"
echo "   - Activate when contact has 'Needs Qualifying' tag"
echo "   - Ask Jorge's 7 qualification questions"
echo "   - Auto-deactivate at 70+ score (5+ questions answered)"
echo "   - Hand off to Jorge's team with 'AI-Qualified' tag"
echo ""
echo "📞 Support: If issues arise, check Railway logs:"
echo "   railway logs"
echo ""
echo "✅ Jorge's Real Estate AI is now live! 🏠"