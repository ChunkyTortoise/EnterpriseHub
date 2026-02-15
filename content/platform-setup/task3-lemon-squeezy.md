# Task 3: Lemon Squeezy Account + Product Upload

**Agent Model**: Claude Sonnet 4.5
**Tools Required**: Browser automation (claude-in-chrome)
**Estimated Time**: 25-30 minutes
**Priority**: P1 (Medium - Gumroad alternative, better EU support)

---

## Objective

Create Lemon Squeezy account and upload 3 priority products with MRR subscription options.

## Prerequisites

**Products to Upload**:
1. AgentForge Multi-LLM Orchestrator (3 tiers: $49, $199, $999)
2. DocQA Engine (3 tiers: $59, $249, $1,499)
3. Prompt Engineering Toolkit (3 tiers: $29, $79, $199)

**Product Files Ready**:
- ZIP files in: `/Users/cave/Documents/GitHub/EnterpriseHub/content/gumroad/zips/`
- Product descriptions in: `/Users/cave/Documents/GitHub/EnterpriseHub/content/gumroad/`

**Required Info**:
- Email: caymanroden@gmail.com
- Business name: ChunkyTortoise Dev
- Location: Palm Springs, CA, USA
- Tax ID: SSN or EIN (user will provide if required)

---

## Agent Prompt

```
You are setting up a Lemon Squeezy account to sell AI/ML software products.

CONTEXT:
- Lemon Squeezy = Gumroad alternative with better EU VAT handling
- User has 3 products ready to upload
- Each product has 3 pricing tiers (Starter/Pro/Enterprise)
- Goal: Create account + upload 9 product variants (3 products x 3 tiers)

TASK CHECKLIST:

1. Navigate to lemonsqueezy.com/signup
2. Create account with caymanroden@gmail.com
3. Verify email if required

4. Complete store setup:
   - Store name: "ChunkyTortoise Dev"
   - Store URL: lemonsqueezy.com/chunkytoirtoise (or best available)
   - Country: United States
   - Currency: USD
   - Business type: Individual/Sole Proprietor
   - Tax settings: US-based, will collect sales tax

5. Add payout method:
   - Choose: Bank account (ACH) or PayPal
   - If tax ID required: Note for user to provide SSN/EIN
   - If manual verification needed: Note expected timeline

6. Upload Product #1: AgentForge Multi-LLM Orchestrator

   Read product info from: /Users/cave/Documents/GitHub/EnterpriseHub/content/gumroad/agentforge-orchestrator.md

   **Starter Tier**:
   - Product name: "AgentForge - Starter"
   - Price: $49 (one-time) OR $9/month (subscription)
   - Description: (from markdown file)
   - File: /Users/cave/Documents/GitHub/EnterpriseHub/content/gumroad/zips/agentforge-starter-v1.0.zip
   - License: Personal use, 1 project
   - Support: Email support
   - Updates: 6 months

   **Pro Tier**:
   - Product name: "AgentForge - Pro"
   - Price: $199 (one-time) OR $29/month (subscription)
   - Description: (from markdown file)
   - File: /Users/cave/Documents/GitHub/EnterpriseHub/content/gumroad/zips/agentforge-pro-v1.0.zip
   - License: Commercial use, unlimited projects
   - Support: Priority email + Slack
   - Updates: Lifetime

   **Enterprise Tier**:
   - Product name: "AgentForge - Enterprise"
   - Price: $999 (one-time) OR $149/month (subscription)
   - Description: (from markdown file)
   - File: /Users/cave/Documents/GitHub/EnterpriseHub/content/gumroad/zips/agentforge-enterprise-v1.0.zip
   - License: Commercial + redistribution
   - Support: Priority + 2hrs consultation
   - Updates: Lifetime + feature requests

7. Upload Product #2: DocQA Engine

   Read product info from: /Users/cave/Documents/GitHub/EnterpriseHub/content/gumroad/docqa-engine.md

   **Starter Tier**: $59 or $12/month
   **Pro Tier**: $249 or $39/month
   **Enterprise Tier**: $1,499 or $199/month

   (Same file structure as AgentForge, adjust paths accordingly)

8. Upload Product #3: Prompt Engineering Toolkit

   Read product info from: /Users/cave/Documents/GitHub/EnterpriseHub/content/gumroad/prompt-toolkit.md

   **Starter Tier**: $29 or $5/month
   **Pro Tier**: $79 or $12/month
   **Enterprise Tier**: $199 or $29/month

9. Configure email settings:
   - Purchase confirmation: ON
   - Download delivery: Immediate
   - License key generation: Auto
   - Refund policy: 14 days, no questions asked

10. Set up analytics:
    - Enable conversion tracking
    - Connect Google Analytics if available
    - Set up webhook for sales notifications (optional)

11. Publish all 9 product variants

12. Save store URL and product links to: /Users/cave/Documents/GitHub/EnterpriseHub/content/platform-setup/lemonsqueezy-complete.txt

SUCCESS CRITERIA:
✅ Lemon Squeezy account created
✅ Store published and live
✅ 9 product variants uploaded (3 products x 3 tiers)
✅ Each product has both one-time and subscription pricing
✅ Payout method configured
✅ All product URLs saved

IMPORTANT NOTES:
- If ZIP file upload fails, note file size and error
- If tax ID required before publishing, download form and notify user
- Lemon Squeezy auto-handles EU VAT - verify this is enabled
- Take screenshots of each published product
- If subscription billing setup is complex, prioritize one-time purchases first
```

---

## Expected Output

**File**: `content/platform-setup/lemonsqueezy-complete.txt`

```
Lemon Squeezy Setup - COMPLETE
Date: 2026-02-15
Store URL: https://chunkytoirtoise.lemonsqueezy.com
Status: Active

✅ Account created and verified
✅ Payout method: ACH Bank Account (pending verification)
✅ Tax settings: US-based, sales tax enabled
✅ EU VAT handling: Automatic

Products Published (9 variants):

AgentForge Multi-LLM Orchestrator:
- Starter: $49 one-time / $9/month - https://chunkytoirtoise.lemonsqueezy.com/buy/agentforge-starter
- Pro: $199 one-time / $29/month - https://chunkytoirtoise.lemonsqueezy.com/buy/agentforge-pro
- Enterprise: $999 one-time / $149/month - https://chunkytoirtoise.lemonsqueezy.com/buy/agentforge-enterprise

DocQA Engine:
- Starter: $59 one-time / $12/month - https://chunkytoirtoise.lemonsqueezy.com/buy/docqa-starter
- Pro: $249 one-time / $39/month - https://chunkytoirtoise.lemonsqueezy.com/buy/docqa-pro
- Enterprise: $1,499 one-time / $199/month - https://chunkytoirtoise.lemonsqueezy.com/buy/docqa-enterprise

Prompt Engineering Toolkit:
- Starter: $29 one-time / $5/month - https://chunkytoirtoise.lemonsqueezy.com/buy/prompt-starter
- Pro: $79 one-time / $12/month - https://chunkytoirtoise.lemonsqueezy.com/buy/prompt-pro
- Enterprise: $199 one-time / $29/month - https://chunkytoirtoise.lemonsqueezy.com/buy/prompt-enterprise

Screenshots saved:
- lemonsqueezy-dashboard.png
- lemonsqueezy-agentforge-products.png
- lemonsqueezy-docqa-products.png
- lemonsqueezy-prompt-products.png

Next Steps:
- If tax ID required: Complete form (saved to Downloads)
- If bank verification pending: Check email in 1-3 business days
- Add product links to portfolio website
- Share on LinkedIn/Twitter
- Set up upsell email sequences
```

---

## Why Lemon Squeezy vs Gumroad?

**Advantages**:
- ✅ Automatic EU VAT handling (no manual setup)
- ✅ Better subscription management (MRR focus)
- ✅ Lower fees on subscriptions (5% vs Gumroad's 10%)
- ✅ Affiliate program built-in
- ✅ More developer-friendly (API, webhooks)

**Use Cases**:
- **Lemon Squeezy**: Subscriptions, EU customers, SaaS products
- **Gumroad**: One-time sales, US customers, simple setup

**Strategy**: Use both platforms, cross-promote products.

---

## Revenue Impact

**One-Time Sales** (first 90 days):
- Conservative: 15 sales x $150 avg = $2,250
- Optimistic: 40 sales x $200 avg = $8,000

**MRR Subscriptions** (Month 3):
- Conservative: 10 subs x $25 avg = $250/month
- Optimistic: 30 subs x $45 avg = $1,350/month

**Annual Potential**: $15K-$35K (combined one-time + subscriptions)
