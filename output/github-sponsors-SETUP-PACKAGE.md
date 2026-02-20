# GitHub Sponsors Setup Package

**For**: Cayman Roden (github.com/ChunkyTortoise)
**Date**: February 19, 2026
**Estimated Setup Time**: 15-20 minutes (excluding Stripe verification)

---

## Part 1: Step-by-Step Setup Instructions

### Phase A: Pre-Flight Checks (2 minutes)

1. Go to **https://github.com/settings/security** -- confirm 2FA is enabled
2. Go to **https://github.com/settings/emails** -- confirm your primary email is verified
3. Go to **https://github.com/settings/profile** -- confirm bio, avatar, and website are filled in

### Phase B: Apply for GitHub Sponsors (5 minutes)

4. Go to **https://github.com/sponsors/accounts**
5. Click **"Get started"** or **"Join the waitlist"** (depending on eligibility status)
6. If prompted with an application form, use this for the **"Why do you need sponsorship?"** field:

> I maintain 11 open-source repositories with 8,500+ tests, including mcp-server-toolkit (live on PyPI) and EnterpriseHub -- AI-powered real estate automation. Sponsorship funds ongoing maintenance, documentation, and new feature development for the developer community.

7. Complete the fiscal host selection -- choose **"Stripe Connect (Individual)"** for solo developer payouts
8. Submit the application. GitHub typically approves within 2-7 days.

### Phase C: Set Up Stripe Payouts (5 minutes, after approval)

9. Once approved, go to **https://github.com/sponsors/ChunkyTortoise/dashboard**
10. Click **"Set up Stripe Connect"**
11. Complete Stripe identity verification (government ID + bank account required)
12. Add your bank account (routing number + checking account number)
13. Confirm payout settings -- payouts arrive monthly after a 30-day holding period

### Phase D: Configure Tiers (5 minutes, after approval)

14. Go to **https://github.com/sponsors/ChunkyTortoise/dashboard/tiers**
15. Create **Tier 1** -- copy the exact text from Part 3 below (Supporter - $5/mo)
16. Create **Tier 2** -- copy the exact text from Part 3 below (Builder - $15/mo)
17. Create **Tier 3** -- copy the exact text from Part 3 below (Enterprise - $50/mo)
18. Toggle on **"Custom amounts"** with a $3 minimum
19. Click **"Publish sponsor profile"**

### Phase E: Add Sponsors Section to READMEs (3 minutes)

20. Copy the SPONSORS.md section from Part 4 below
21. Add it to READMEs of the repos listed in Part 5 (start with the top 3)
22. Commit and push

---

## Part 2: GitHub Sponsors Profile Bio

Copy this exactly into your Sponsors profile description (491 characters):

```
I build open-source developer tools and AI-powered applications. My work includes mcp-server-toolkit (live on PyPI), EnterpriseHub (real estate AI with 8,500+ tests), and 11 public repositories spanning FastAPI, Streamlit, PostgreSQL, and LLM integrations. Your sponsorship directly funds maintenance, new features, documentation, and keeping these tools free for the community. Every tier gets real benefits -- from README recognition to dedicated support calls.
```

---

## Part 3: Tier Descriptions (Copy-Paste Ready)

### Tier 1: Supporter -- $5/mo

**Name**: Supporter
**Amount**: $5

**Description** (paste into the tier description field):

```
Thank you for supporting my open-source work!

What you get:
- Your name listed in the Sponsors section of project READMEs
- Sponsor badge on your GitHub profile
- Priority release announcements via GitHub notifications
- Access to the #sponsors Discord channel
```

### Tier 2: Builder -- $15/mo

**Name**: Builder
**Amount**: $15

**Description** (paste into the tier description field):

```
For developers and teams building on my projects.

Everything in Supporter, plus:
- 24-hour guaranteed response to your GitHub issues (business days)
- Builder sponsor badge on your GitHub profile
- Feature request prioritization on the roadmap
- Quarterly 30-minute video call for technical questions
- Early access to new features before public release
```

### Tier 3: Enterprise -- $50/mo

**Name**: Enterprise
**Amount**: $50

**Description** (paste into the tier description field):

```
For organizations that need dedicated support and consultation.

Everything in Builder, plus:
- Monthly 30-minute consultation call (architecture review, integration guidance, or custom feature discussion)
- Dedicated Slack channel with direct access to me
- 4-hour SLA-backed response time during business hours
- Enterprise sponsor badge for maximum visibility
- Logo and link on the sponsors page (co-marketing)
- Priority consideration for custom feature development
```

---

## Part 4: SPONSORS.md Section for READMEs

Copy this block and paste it near the bottom of each README.md (before the license section if one exists):

```markdown
---

## Sponsors

[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-ec4899?style=for-the-badge&logo=github-sponsors)](https://github.com/sponsors/ChunkyTortoise)

This project is supported by sponsors. Your sponsorship funds ongoing development, maintenance, and documentation.

| Tier | Price | What You Get |
|------|-------|--------------|
| **Supporter** | $5/mo | Name in README, sponsor badge, priority updates |
| **Builder** | $15/mo | 24h issue response, quarterly calls, early access |
| **Enterprise** | $50/mo | Monthly consultation, dedicated Slack, 4h SLA |

[Become a sponsor](https://github.com/sponsors/ChunkyTortoise)

<!-- SPONSORS:START - Do not remove this section -->
<!-- SPONSORS:END -->
```

---

## Part 5: Repo Prioritization for Sponsors Section

Add the sponsors section to these repos first, ordered by visibility and traffic potential:

| Priority | Repository | Reason |
|----------|-----------|--------|
| 1 | **mcp-server-toolkit** | Live on PyPI, highest discoverability from external search, active user base |
| 2 | **EnterpriseHub** | Flagship project, most tests (8,500+), demonstrates depth |
| 3 | **ChunkyTortoise** (profile README) | Every GitHub profile visitor sees this first |
| 4 | Any repo with a Streamlit demo | Live demos attract visitors who linger longer |
| 5 | Any repo with CI/CD badges | Signals quality, attracts professional sponsors |
| 6-11 | Remaining public repos | Add to all eventually for consistent branding |

**Tip**: For repos 1-3, also add the badge (`[![Sponsor]...]`) to the very top of the README, right after the title/description line, so it is immediately visible.

---

## Part 6: Post-Setup Checklist

Complete these within 48 hours of your sponsors page going live:

### Announce (Day 1)

- [ ] **Tweet/X post**: "I just launched GitHub Sponsors! I maintain 11 open-source repos including mcp-server-toolkit (PyPI) and EnterpriseHub (8,500+ tests). If my work helps you, consider sponsoring. Every tier gets real benefits. https://github.com/sponsors/ChunkyTortoise"
- [ ] **LinkedIn post**: Write a short post about your open-source journey, the projects you maintain, and why you launched Sponsors. Tag #OpenSource #GitHubSponsors #Python #AI. Include the sponsors link.
- [ ] **Discord/Slack communities**: Share in any developer communities you are active in (Python, FastAPI, LLM/AI channels)

### Update Profiles (Day 1-2)

- [ ] **GitHub profile bio**: Add "Sponsor me: github.com/sponsors/ChunkyTortoise" or use the pinned link
- [ ] **Portfolio website**: Add a "Sponsor" button or link to your main navigation or footer
- [ ] **LinkedIn profile**: Add the sponsors link to your "Featured" section
- [ ] **PyPI mcp-server-toolkit page**: Update the project description or README to include the sponsors badge
- [ ] **Gumroad/Fiverr profiles**: Cross-link to sponsors page if you have bios that mention open-source work

### Ongoing (Weekly)

- [ ] Thank new sponsors publicly (a short tweet or GitHub post)
- [ ] Mention sponsors in release notes for new versions
- [ ] Include sponsors CTA in any blog posts, tutorials, or conference talks

---

## Quick Reference: Key URLs

| What | URL |
|------|-----|
| Sponsors Dashboard | https://github.com/sponsors/ChunkyTortoise/dashboard |
| Tier Editor | https://github.com/sponsors/ChunkyTortoise/dashboard/tiers |
| Public Sponsors Page | https://github.com/sponsors/ChunkyTortoise |
| GitHub 2FA Settings | https://github.com/settings/security |
| GitHub Email Settings | https://github.com/settings/emails |
| Stripe Connect (via GitHub) | Set up from Sponsors Dashboard |
| GitHub Sponsors Docs | https://docs.github.com/en/sponsors |

---

*Generated: February 19, 2026*
