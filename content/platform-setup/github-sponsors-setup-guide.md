# GitHub Sponsors Setup Guide - ChunkyTortoise

**Status**: Manual setup required (Chrome extension not connected)
**Date**: 2026-02-15

## Prerequisites

1. **Chrome Extension**: Install Claude browser extension from https://claude.ai/chrome
2. **GitHub Login**: Log into github.com/ChunkyTortoise in Chrome browser
3. **Email Access**: Have access to caymanroden@gmail.com for verification

---

## Step-by-Step Setup

### 1. Navigate to GitHub Sponsors
- Go to: https://github.com/sponsors
- If not logged in, log in as ChunkyTortoise

### 2. Start Enrollment
- Click "Join the waitlist" or "Set up GitHub Sponsors" button
- If there's a waitlist, join it and note the expected approval time

### 3. Complete Eligibility Requirements
- [ ] Confirm account ownership
- [ ] Verify email: caymanroden@gmail.com (check inbox for verification email)
- [ ] Accept GitHub Sponsors Program Terms

### 4. Set Up Payout Information

**Recommended**: Stripe Connect (for existing Stripe account integration)

#### Option A: Stripe Connect (Preferred)
- Click "Connect with Stripe"
- If you have an existing Stripe account: Link it
- If not: Create new Stripe account
  - Business name: Cayman Roden (or business entity)
  - Email: caymanroden@gmail.com
  - Business type: Individual or LLC

#### Option B: ACH Direct Deposit
- Routing number: [Your bank routing number]
- Account number: [Your bank account number]
- Bank name: [Your bank name]

**Tax Information**:
- If W-9 required: Download and complete
  - Name: Cayman Roden
  - TIN/SSN: [Your tax ID]
  - Business type: Individual or LLC
  - Upload completed form

### 5. Create Sponsor Profile

**Profile Headline**:
```
Building production-ready AI/ML tools & frameworks
```

**Bio** (copy from bio file):
```
Senior AI/ML engineer with 20+ years of software development experience. I build open-source tools that help developers ship AI-powered products faster and cheaper.

## What I'm Working On
- **AgentForge**: Multi-LLM orchestration framework (4.3M dispatches/sec, 89% cost reduction)
- **DocQA Engine**: Production RAG system with BM25/semantic hybrid search
- **Streamlit Dashboards**: BI templates for AI metrics, forecasting, churn detection
- **MCP Server Toolkit**: Model Context Protocol servers for AI agent development

## Why Sponsor?
Your sponsorship helps me:
- Maintain and improve existing open-source projects
- Create tutorials and documentation
- Provide community support and code reviews
- Develop new AI/ML tools based on real-world needs

## Stats
- 11 public repositories
- 8,500+ automated tests (all passing)
- 5 live Streamlit demos
- 1 PyPI package (mcp-server-toolkit)
- Docker support across all projects
```

**Featured Repositories** (select 3):
1. `ai-orchestrator` - AgentForge: Multi-LLM orchestration
2. `docqa-engine` - DocQA: RAG question-answering
3. `insight-engine` - Streamlit BI dashboards

**Goals Section**:
- Goal 1: Support development of open-source AI tools
- Goal 2: Dedicate 10hrs/month to community support
- Goal 3: Create tutorials & documentation

### 6. Create Sponsorship Tiers

#### Tier 1: Supporter ($5/month)
**Name**: Supporter
**Description**:
```
Support open-source AI/ML development

Benefits:
✓ Name listed in SPONSORS.md
✓ Early access to new features
✓ Monthly progress updates via email
✓ Sponsor badge on your profile
```

#### Tier 2: Contributor ($10/month)
**Name**: Contributor
**Description**:
```
All Supporter benefits, plus:

✓ Priority issue responses (24hr SLA)
✓ Access to private Discord/Slack community
✓ Vote on feature roadmap
✓ Exclusive development insights
```

#### Tier 3: Partner ($25/month)
**Name**: Partner
**Description**:
```
All Contributor benefits, plus:

✓ 1hr/month consultation call
✓ Feature request priority
✓ Direct Slack/email access
✓ Early access to experimental features
```

#### Tier 4: Professional ($50/month)
**Name**: Professional
**Description**:
```
All Partner benefits, plus:

✓ Code review for your projects (2hrs/month)
✓ Custom integration support
✓ Architecture consultation
✓ Priority bug fixes
```

#### Tier 5: Enterprise ($100/month)
**Name**: Enterprise
**Description**:
```
All Professional benefits, plus:

✓ 4hrs/month dedicated support
✓ Custom feature development
✓ SLA guarantees (4hr response time)
✓ Named in project credits
✓ Quarterly roadmap input
```

### 7. Set Monthly Goal
- **Goal Amount**: $500/month
- **Goal Description**: "Dedicate 20hrs/month to open-source development and community support"

### 8. Enable Sponsor Button
- [ ] Check "Display sponsor button on repositories"
- [ ] Verify it appears on these repos:
  - ai-orchestrator
  - docqa-engine
  - insight-engine
  - (All other public repos should automatically show it)

### 9. Review & Publish
- [ ] Review all information for accuracy
- [ ] Click "Publish profile"
- [ ] Note any verification steps or waiting periods

### 10. Post-Publication Tasks

#### Add SPONSORS.md to Repositories
Create a file at the root of each major repo:

```markdown
# Sponsors

Thank you to all our sponsors! Your support enables continued development of this project.

## Current Sponsors

[Sponsors will be listed here automatically via GitHub API]

## Become a Sponsor

Support this project: [github.com/sponsors/ChunkyTortoise](https://github.com/sponsors/ChunkyTortoise)

Sponsorship tiers start at $5/month with benefits including:
- Priority support
- Feature request input
- Code reviews
- Custom development

See all tiers and benefits: https://github.com/sponsors/ChunkyTortoise
```

#### Update README.md Files
Add sponsor badge to each major repo's README:

```markdown
# Project Name

[![Sponsor](https://img.shields.io/badge/Sponsor-ChunkyTortoise-blue?logo=github-sponsors)](https://github.com/sponsors/ChunkyTortoise)

[rest of README...]
```

#### Create .github/FUNDING.yml
Add to each repo to enable sponsor button:

```yaml
# .github/FUNDING.yml
github: ChunkyTortoise
```

---

## Verification Checklist

After setup is complete, verify:

- [ ] Profile is live at https://github.com/sponsors/ChunkyTortoise
- [ ] All 5 tiers are visible and correctly priced
- [ ] Payout method is connected and verified
- [ ] Featured repositories appear correctly
- [ ] Sponsor button shows on repo pages
- [ ] Bio and goals are formatted properly
- [ ] Monthly goal ($500) is displayed
- [ ] Profile photo and banner look professional

---

## Expected Timeline

- **Immediate**: Profile creation (15-30 minutes)
- **1-3 days**: Stripe verification (if new account)
- **1-7 days**: Bank account verification (if ACH)
- **Varies**: GitHub Sponsors waitlist approval (if applicable)

---

## Next Steps After Approval

1. **Announce on Social Media**:
   - LinkedIn: "Now accepting GitHub Sponsors! Support open-source AI/ML tools"
   - Twitter/X: Link to sponsor page
   - Dev.to: Write blog post about sponsorship tiers

2. **Create Content**:
   - Video walkthrough of AgentForge features
   - Tutorial series on RAG systems
   - "Sponsor spotlight" monthly updates

3. **Engage Sponsors**:
   - Send welcome email to new sponsors
   - Schedule monthly consultation calls
   - Provide exclusive updates/insights

4. **Track Metrics**:
   - Monthly recurring revenue (MRR)
   - Sponsor retention rate
   - Community engagement
   - Feature requests from sponsors

---

## Troubleshooting

**Issue**: Profile rejected or waitlisted
- **Solution**: Ensure account has 12+ months of activity, 2FA enabled, no ToS violations

**Issue**: Payout verification failing
- **Solution**: Check bank account details, ensure tax form is complete, contact GitHub Support

**Issue**: Sponsor button not appearing
- **Solution**: Create `.github/FUNDING.yml` file, wait 10 minutes for cache refresh

**Issue**: Cannot create tiers
- **Solution**: Ensure minimum $1/month tier, maximum $12,000/year, all tiers must be multiples of $1

---

## Resources

- GitHub Sponsors Docs: https://docs.github.com/en/sponsors
- Stripe Connect: https://stripe.com/connect
- GitHub Support: https://support.github.com/contact

---

**Setup Status**: PENDING MANUAL COMPLETION
**Last Updated**: 2026-02-15
