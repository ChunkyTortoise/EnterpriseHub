# Jorge AI Bot Suite — GHL Real Estate

AI-powered lead qualification bots for GoHighLevel. Three bots handle your full lead lifecycle: initial qualification, buyer conversion, and seller listing pipeline — all via SMS through your GHL workflows.

## What's Included

| Bot | Activates On Tag | Does |
|-----|-----------------|------|
| **Lead Bot** | `Needs Qualifying` | Initial qualification, temperature scoring (Hot/Warm/Cold), cross-bot routing |
| **Seller Bot** | `Needs Qualifying` (seller intent) | 4-question CMA conversation, hot/warm classification, workflow triggers |
| **Buyer Bot** | `Buyer-Lead` | Budget/timeline/pre-approval discovery, property matching, showing coordination |

## Quick Start

```bash
# 1. Copy the environment template
cp .env.example .env

# 2. Fill in required values (see .env.example for full reference)
#    Minimum required:
#      ANTHROPIC_API_KEY
#      GHL_API_KEY + GHL_LOCATION_ID
#      DATABASE_URL
#      REDIS_URL

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the admin dashboard
streamlit run streamlit_demo/app.py
```

## Deployment (Railway)

See `agents/DEPLOYMENT_CHECKLIST.md` for the complete step-by-step Railway deployment guide including:
- Environment variable setup
- GHL webhook configuration
- Custom field creation
- Smoke test procedure

## GHL Setup

See `agents/JORGE_GHL_SETUP_GUIDE.md` for:
- Creating the 6 required automation workflows
- Setting up custom fields
- Configuring webhook endpoints

## Key Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key (console.anthropic.com) |
| `GHL_API_KEY` | Yes | GoHighLevel JWT token |
| `GHL_LOCATION_ID` | Yes | Your GHL location ID |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | Yes | Redis connection string |
| `HOT_SELLER_WORKFLOW_ID` | Yes | GHL workflow ID for hot sellers |
| `HOT_BUYER_WORKFLOW_ID` | Yes | GHL workflow ID for hot buyers |
| `NOTIFY_AGENT_WORKFLOW_ID` | Yes | GHL workflow for agent notifications |
| `JORGE_CALENDAR_ID` | Recommended | GHL calendar for appointment booking |

See `.env.example` for the complete variable reference with descriptions.

## Bot Performance

- Lead qualification: 45 min manual → under 2 min automated
- Response cost: ~$0.03 per qualification (3-tier cache, 88% hit rate)
- 181 unit tests + 114 integration tests passing

## Support

For deployment questions or issues, refer to `agents/DEPLOYMENT_CHECKLIST.md` troubleshooting section.
