# Platform Setup Orchestration Guide

**Created**: 2026-02-15
**Purpose**: Run 5 parallel Claude Sonnet 4.5 agents to set up freelance/product platforms

---

## Quick Start

### Option 1: Parallel Execution (Fastest - 25-30 minutes total)

Run all 5 agents simultaneously in separate terminal windows:

```bash
# Terminal 1 - Contra
claude --model sonnet task1-contra-account.md

# Terminal 2 - GitHub Sponsors
claude --model sonnet task2-github-sponsors.md

# Terminal 3 - Lemon Squeezy
claude --model sonnet task3-lemon-squeezy.md

# Terminal 4 - Braintrust
claude --model sonnet task4-braintrust.md

# Terminal 5 - Polar.sh
claude --model sonnet task5-polar-sh.md
```

**Total Time**: 25-30 minutes (all agents finish around same time)

### Option 2: Sequential Execution (Slower - 2 hours total)

Run one at a time if you prefer to monitor each setup:

```bash
# 1. Fastest first (GitHub Sponsors - 10 min)
claude --model sonnet task2-github-sponsors.md

# 2. Quick setup (Contra - 15 min)
claude --model sonnet task1-contra-account.md

# 3. Medium complexity (Polar.sh - 20 min)
claude --model sonnet task5-polar-sh.md

# 4. Moderate setup (Braintrust - 25 min)
claude --model sonnet task4-braintrust.md

# 5. Most complex (Lemon Squeezy - 30 min)
claude --model sonnet task3-lemon-squeezy.md
```

**Total Time**: ~1 hour 40 minutes (sequential)

---

## Task Specifications

| Task | Platform | Time | Priority | Revenue Impact |
|------|----------|------|----------|----------------|
| 1 | Contra | 15-20 min | P0 | $1K-6K/month |
| 2 | GitHub Sponsors | 10-15 min | P0 | $100-500/month |
| 3 | Lemon Squeezy | 25-30 min | P1 | $2K-8K/month |
| 4 | Braintrust | 20-25 min | P1 | $6K-20K/month |
| 5 | Polar.sh | 15-20 min | P1 | $500-2K/month |

**Total Potential**: $9.6K-36.5K/month

---

## Files Created

### Task Specifications (for agents):
- ✅ `task1-contra-account.md` - Contra profile + 3 services
- ✅ `task2-github-sponsors.md` - GitHub Sponsors with 5 tiers
- ✅ `task3-lemon-squeezy.md` - Lemon Squeezy + 9 product variants
- ✅ `task4-braintrust.md` - Braintrust freelance profile
- ✅ `task5-polar-sh.md` - Polar.sh repo monetization

### Supporting Content:
- ✅ `github-sponsors-bio.md` - Bio for GitHub Sponsors profile
- ✅ `braintrust-summary.md` - Professional summary for Braintrust

### Output Files (created by agents):
- `contra-setup-complete.txt` - Contra account status + URLs
- `github-sponsors-complete.txt` - GitHub Sponsors profile URL
- `lemonsqueezy-complete.txt` - Lemon Squeezy store + product links
- `braintrust-complete.txt` - Braintrust profile status
- `polar-complete.txt` - Polar.sh page URL

---

## Prerequisites Checklist

Before running agents, verify you have:

### Account Credentials
- ✅ Email: caymanroden@gmail.com (access required)
- ✅ GitHub: ChunkyTortoise (logged in)
- ✅ LinkedIn: caymanroden (logged in, for connections)

### Content Files Ready
- ✅ Product ZIPs: `/Users/cave/Documents/GitHub/EnterpriseHub/content/gumroad/zips/`
- ✅ Gumroad descriptions: `/Users/cave/Documents/GitHub/EnterpriseHub/content/gumroad/*.md`
- ✅ Contra services: `/Users/cave/Documents/GitHub/EnterpriseHub/content/contra/service-*.md`

### Financial Setup (may be required by platforms)
- ⚠️ Bank account info (for ACH payouts)
- ⚠️ Stripe account (for Lemon Squeezy, Polar.sh)
- ⚠️ PayPal (alternative for some platforms)
- ⚠️ Tax ID (SSN or EIN for W-9 forms)

**Note**: Agents will pause and notify if financial info is required. You can complete this step manually.

---

## Expected Blockers

### Email Verification
- **Platforms**: All 5 may require email verification
- **Action**: Check caymanroden@gmail.com inbox during setup
- **Time**: 1-3 minutes per platform

### Tax Forms (W-9)
- **Platforms**: Lemon Squeezy, Braintrust (likely)
- **Action**: Agent will download form, you complete manually
- **Time**: 5-10 minutes to fill out

### Bank Account Verification
- **Platforms**: Lemon Squeezy, Polar.sh (if using ACH)
- **Action**: Micro-deposit verification (1-3 business days)
- **Workaround**: Use Stripe Connect instead (instant)

### Profile Review/Approval
- **Platforms**: Braintrust (high likelihood), Contra (possible)
- **Timeline**: 1-3 business days
- **Action**: None required, just wait for approval email

### File Upload Size Limits
- **Platform**: Lemon Squeezy
- **Issue**: ZIP files may exceed upload limit (100MB typical)
- **Workaround**: Agent will note which files failed, upload manually via web UI

---

## Post-Setup Actions (Manual)

After agents complete, you must:

### 1. Email Verifications
Check caymanroden@gmail.com and click verification links for:
- [ ] Contra
- [ ] GitHub Sponsors
- [ ] Lemon Squeezy
- [ ] Braintrust
- [ ] Polar.sh

### 2. Complete Tax Forms
If agents downloaded W-9 forms:
- [ ] Fill out W-9 for Lemon Squeezy
- [ ] Fill out W-9 for Braintrust
- [ ] Upload completed forms

### 3. Bank Account Verification
If using ACH direct deposit:
- [ ] Wait for micro-deposits (1-3 days)
- [ ] Enter verification amounts in platform

### 4. Update READMEs
Add sponsor/product badges to GitHub repos:
- [ ] ai-orchestrator: Add GitHub Sponsors + Polar badges
- [ ] docqa-engine: Add GitHub Sponsors + Polar badges
- [ ] insight-engine: Add GitHub Sponsors + Polar badges
- [ ] mcp-server-toolkit: Add GitHub Sponsors + Polar badges
- [ ] EnterpriseHub: Add GitHub Sponsors + Polar badges

### 5. Announce on Social Media
- [ ] LinkedIn post: "Now on 5 new platforms! Contra, GitHub Sponsors, Lemon Squeezy, Braintrust, Polar.sh"
- [ ] Twitter/X: Same announcement
- [ ] Dev.to article: "How I Monetized My GitHub Repos in One Day"

### 6. Set Up Analytics
- [ ] Google Analytics for Lemon Squeezy store
- [ ] Track conversions in Polar.sh
- [ ] Monitor Braintrust job matches

---

## Success Metrics

### Week 1 (Setup Complete)
- ✅ All 5 platform accounts active
- ✅ Email verified on all platforms
- ✅ At least 3/5 profiles 100% complete
- ✅ Payment methods connected (or pending verification)

### Week 2-4 (First Sales)
- 🎯 First GitHub sponsor: $5-10/month
- 🎯 First Lemon Squeezy sale: $29-199
- 🎯 First Contra inquiry: $1,500-2,000 project
- 🎯 Braintrust profile approved
- 🎯 Polar.sh: 50-100 newsletter subscribers

### Month 2-3 (Momentum)
- 🎯 5-10 GitHub sponsors: $50-150/month MRR
- 🎯 10-20 Lemon Squeezy sales: $1K-3K total
- 🎯 1 Contra project completed: $1,500-2,000
- 🎯 1 Braintrust contract: $6K-10K/month
- 🎯 Polar.sh: 200-500 subscribers, 5-10 paid

---

## Troubleshooting

### Agent Stuck on Email Verification
**Problem**: Agent waiting for email verification link
**Solution**:
1. Pause agent (Ctrl+C)
2. Check email, click verification link
3. Resume agent or mark step as complete

### File Upload Fails (Lemon Squeezy)
**Problem**: ZIP file too large (>100MB)
**Solution**:
1. Note which products failed
2. Upload manually via Lemon Squeezy web UI
3. Or compress ZIPs further (remove unnecessary files)

### Tax ID Required Before Publishing
**Problem**: Platform requires W-9 before going live
**Solution**:
1. Agent downloads blank W-9
2. Fill out manually (5-10 min)
3. Upload via platform web UI
4. Resume agent to publish

### Stripe Connect Fails
**Problem**: Stripe verification requires manual review
**Solution**:
1. Use alternative payout method (PayPal, ACH direct)
2. Or wait for Stripe review (1-3 business days)
3. Come back and reconnect after approval

### Browser Automation Blocked
**Problem**: Platform detects automation, shows CAPTCHA
**Solution**:
1. Complete CAPTCHA manually
2. Agent should resume automatically
3. Or switch to manual setup for that platform

---

## Revenue Timeline

### Immediate (Day 1)
- **Setup complete**: 5 new revenue channels active
- **Searchable**: Profiles indexed by Google, platform search
- **Ready to sell**: Products live, services bookable

### Week 1-2
- **First discovery**: Organic search traffic starts
- **First inquiry**: Contra/Braintrust messages
- **First sponsor**: GitHub Sponsors notification

### Month 1
- **Conservative**: $500-1,500 (first sales across platforms)
- **Optimistic**: $2,000-5,000 (early traction)

### Month 3
- **Conservative**: $2,000-5,000/month (steady pipeline)
- **Optimistic**: $8,000-15,000/month (1-2 contracts + product sales)

### Month 6
- **Conservative**: $5,000-10,000/month (established presence)
- **Optimistic**: $15,000-30,000/month (multiple contracts + MRR)

---

## Next Steps After Setup

1. **Content Marketing** (Week 2-4):
   - Publish 4 LinkedIn posts highlighting new offerings
   - Write Dev.to article: "How I Monetized GitHub Repos"
   - Share Lemon Squeezy products in AI/ML communities

2. **Product Optimization** (Month 2):
   - Analyze which products sell best
   - Create upsell sequences for buyers
   - Add testimonials to product pages

3. **Platform Expansion** (Month 3-4):
   - Add Arc.dev (pre-vetted dev marketplace)
   - Add Toptal (premium freelance network)
   - Add AppSumo (lifetime deal marketplace)

4. **Community Building** (Month 2-6):
   - Grow GitHub Sponsors to 20+ sponsors
   - Build Polar.sh newsletter to 1,000+ subscribers
   - Create Discord server for paid subscribers

5. **Revenue Optimization** (Month 6+):
   - Increase prices based on demand
   - Create bundles and upsells
   - Add annual subscription discounts (2 months free)
   - Launch affiliate program on Lemon Squeezy

---

## Total Time Investment

| Phase | Time | Value |
|-------|------|-------|
| Agent setup (parallel) | 30 min | 5 platform accounts |
| Manual verification steps | 30 min | Email + tax forms |
| Post-setup updates | 1 hour | READMEs, social media |
| **Total** | **2 hours** | **$9.6K-36.5K/month potential** |

**ROI**: 5,000% - 18,000% (based on first month revenue vs setup time)

---

## Support

If agents encounter errors:
1. Check output files in `content/platform-setup/`
2. Review screenshots saved by agents
3. Consult platform-specific troubleshooting sections
4. Manual fallback: Use web UI with agent-generated content

**Remember**: Each task file has a "Fallback Plan" section for manual setup if browser automation fails.
