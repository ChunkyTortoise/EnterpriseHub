# Task 2: GitHub Sponsors Setup

**Agent Model**: Claude Sonnet 4.5
**Tools Required**: Browser automation (claude-in-chrome)
**Estimated Time**: 10-15 minutes
**Priority**: P0 (High - Passive income, already on GitHub)

---

## Objective

Enable GitHub Sponsors on existing account (ChunkyTortoise) with tiered sponsorship options and compelling profile.

## Prerequisites

**Account**: github.com/ChunkyTortoise (already active)
**Repos**: 11 public repos (ai-orchestrator, docqa-engine, etc.)
**Email**: caymanroden@gmail.com

**Required Info**:
- Bank account or Stripe Connect (for payouts)
- Tax information (W-9 for US)
- Sponsorship tiers: $5, $10, $25, $50, $100/month

---

## Agent Prompt

```
You are enabling GitHub Sponsors for an open-source AI/ML developer.

CONTEXT:
- Account: github.com/ChunkyTortoise
- 11 public repos with 8,500+ tests
- Focus: AI orchestration, RAG systems, multi-agent frameworks
- Goal: Set up 5 sponsorship tiers with clear value props

TASK CHECKLIST:

1. Navigate to github.com/sponsors
2. Log in as ChunkyTortoise (if not already logged in)
3. Click "Join the waitlist" or "Set up GitHub Sponsors"

4. Complete eligibility requirements:
   - Confirm account ownership
   - Verify email: caymanroden@gmail.com
   - Accept GitHub Sponsors Program Terms

5. Set up payout information:
   - Choose: Stripe Connect (preferred) or ACH Direct
   - If Stripe: Connect existing Stripe account or create new
   - If tax form required: Download W-9, note for user to complete

6. Create sponsor profile:
   - Profile headline: "Building production-ready AI/ML tools & frameworks"
   - Bio (read from file): /Users/cave/Documents/GitHub/EnterpriseHub/content/platform-setup/github-sponsors-bio.md
   - Featured repositories:
     * ai-orchestrator (AgentForge - Multi-LLM orchestration)
     * docqa-engine (DocQA - RAG question-answering)
     * insight-engine (Streamlit BI dashboards)
   - Goals section:
     * "Support development of open-source AI tools"
     * "Dedicate 10hrs/month to community support"
     * "Create tutorials & documentation"

7. Create sponsorship tiers:

   **$5/month - Supporter**
   - Name in SPONSORS.md
   - Early access to new features
   - Monthly progress updates

   **$10/month - Contributor**
   - All Supporter benefits
   - Priority issue responses (24hr)
   - Access to private Discord/Slack

   **$25/month - Partner**
   - All Contributor benefits
   - 1hr/month consultation call
   - Feature request priority

   **$50/month - Professional**
   - All Partner benefits
   - Code review for your projects (2hrs/month)
   - Custom integration support

   **$100/month - Enterprise**
   - All Professional benefits
   - 4hrs/month dedicated support
   - Custom feature development
   - SLA guarantees

8. Set a monthly goal:
   - Initial goal: $500/month
   - Use for: "Dedicate 20hrs/month to open-source development"

9. Enable sponsor button on repositories:
   - Check: "Display sponsor button on repositories"
   - Confirm it appears on ai-orchestrator, docqa-engine, insight-engine

10. Publish GitHub Sponsors profile

11. Save profile URL to: /Users/cave/Documents/GitHub/EnterpriseHub/content/platform-setup/github-sponsors-complete.txt

SUCCESS CRITERIA:
✅ GitHub Sponsors profile live
✅ 5 tiers configured ($5-$100/month)
✅ Payout method connected
✅ Sponsor button visible on repos
✅ Profile URL saved

IMPORTANT NOTES:
- If tax form required, download and notify user
- If payout setup requires manual bank verification, note timing
- GitHub Sponsors may have waitlist - if so, join waitlist and note expected approval time
- Take screenshot of completed profile
```

---

## Bio Content File

**Create**: `content/platform-setup/github-sponsors-bio.md`

```markdown
# GitHub Sponsors Bio

## Headline
Building production-ready AI/ML tools & frameworks

## About Me
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

## Contact
- Website: chunkytortoise.github.io
- LinkedIn: linkedin.com/in/caymanroden
- Email: caymanroden@gmail.com
```

---

## Expected Output

**File**: `content/platform-setup/github-sponsors-complete.txt`

```
GitHub Sponsors Setup - COMPLETE
Date: 2026-02-15
Profile URL: https://github.com/sponsors/ChunkyTortoise
Status: Active (or Pending Approval)

✅ Sponsors profile created
✅ 5 tiers configured:
   - $5/month: Supporter
   - $10/month: Contributor
   - $25/month: Partner
   - $50/month: Professional
   - $100/month: Enterprise
✅ Payout method: Stripe Connect (or ACH Direct)
✅ Sponsor button enabled on repos
✅ Featured repos: ai-orchestrator, docqa-engine, insight-engine
✅ Monthly goal: $500

Screenshots saved:
- github-sponsors-profile.png
- github-sponsors-tiers.png

Next Steps:
- If waitlisted: Expect approval in 1-2 weeks
- If tax form required: Complete W-9 (saved to Downloads)
- Share profile on LinkedIn/Twitter
- Add sponsor badge to README files
```

---

## Post-Setup Actions (Manual)

After agent completes setup:

1. **Add SPONSORS.md to each repo**:
   ```markdown
   # Sponsors

   Thank you to our sponsors! 🙏

   [Become a sponsor](https://github.com/sponsors/ChunkyTortoise)
   ```

2. **Update README badges**:
   ```markdown
   [![GitHub Sponsors](https://img.shields.io/github/sponsors/ChunkyTortoise)](https://github.com/sponsors/ChunkyTortoise)
   ```

3. **Announce on LinkedIn**:
   - "Just launched GitHub Sponsors! Supporting open-source AI/ML development."
   - Link to profile
   - Highlight featured projects

---

## Revenue Impact

- **Passive income**: $100-500/month (conservative estimate)
- **Time to first sponsor**: 2-6 weeks
- **Typical enterprise sponsor**: $50-100/month
- **Long-term potential**: $1K-3K/month (with 20-30 sponsors)
