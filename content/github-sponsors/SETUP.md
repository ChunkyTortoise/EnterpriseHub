# GitHub Sponsors Setup Guide

Step-by-step guide to setting up GitHub Sponsors for EnterpriseHub.

---

## Prerequisites

Before applying, ensure you have:

- [ ] **GitHub Account**: Must be at least 90 days old
- [ ] **Verified Email**: Primary email- [ ] ** must be verified
Two-Factor Authentication**: Must be enabled
- [ ] **Public Repositories**: At least one public repository with activity **Profile Completeness
- [ ]**: Bio, avatar, and website (optional)

---

## Step 1: Prepare Your Profile

### Profile Requirements

1. **Profile Bio** (150 characters max)
   ```
   Building AI-powered real estate solutions | EnterpriseHub creator | FastAPI, Streamlit, PostgreSQL
   ```

2. **Profile README** (recommended)
   - Create a public repository named exactly as your username
   - Add a detailed README explaining your projects
   - Include links to your key projects

3. **Profile Picture**
   - Use a professional headshot or logo

4. **Social Links**
   - LinkedIn (recommended)
   - Portfolio website or project links
   - Twitter/X (optional)

### Profile Checklist

```markdown
[ ] Profile photo uploaded
[ ] Bio written (150 chars)
[ ] Username is professional (consider updating if using a nickname)
[ ] Website points to portfolio or project
[ ] Profile README created with project overview
[ ] 2FA enabled in GitHub settings
```

---

## Step 2: Apply for GitHub Sponsors

### Application Process

1. **Navigate to GitHub Sponsors**
   ```
   https://github.com/sponsors/your-username
   ```

2. **Click "Become a Sponsor"**
   - If not eligible, you'll see an application form
   - If eligible, you can set up directly

3. **Fill Out Application**

   **Section 1: About You**
   ```
   Full legal name: [Your Name]
   Country of residence: [Country]
   How you develop: [Brief description of your development work]
   ```

   **Section 2: Why You Need Sponsorship**
   ```
   I'm building open-source tools for the real estate AI space.
   EnterpriseHub has 7,000+ tests, 5 live demos, and helps
   businesses automate lead qualification and CRM integration.

   Sponsorship will allow me to:
   - Dedicate more time to feature development
   - Improve documentation and tutorials
   - Support enterprise deployments
   ```

   **Section 3: Sponsorship Details**
   ```
   Primary repository: ChunkyTortoise/EnterpriseHub
   Open source since: [Date]
   Total contributors: [Number]
   Monthly recurring costs: $X (hosting, domains, services)
   ```

4. **Submit Application**
   - GitHub typically responds within 2-7 days
   - They may request additional information

---

## Step 3: Set Up Sponsors Profile

Once approved, configure your sponsors page:

### Tier Configuration

| Tier | Monthly Amount | Benefits |
|------|---------------|----------|
| Supporter | $5/mo | Name in README, sponsor badge |
| Builder | $15/mo | 24h issue responses, Builder badge, quarterly calls |
| Enterprise | $50/mo | Monthly calls, dedicated Slack, enterprise badge |

### Profile Settings

1. **Profile Picture**
   - Upload a logo or professional image
   - Minimum 64x64 pixels

2. **Tagline**
   ```
   AI-Powered Real Estate Platform
   ```

3. **Description**
   ```
   EnterpriseHub provides AI chatbots for lead qualification,
   buyer inquiries, and seller consultations. Built with FastAPI,
   Streamlit, and PostgreSQL for the Rancho Cucamonga market.
   ```

4. **Funding Links**
   - GitHub Sponsors (primary)
   - Patreon (optional)
   - Ko-fi (optional)

5. **Custom Amounts**
   - Enable "Custom amount" for flexible contributions
   - Minimum recommended: $3
   - Maximum recommended: $100

---

## Step 4: Set Up Payout (Stripe)

### Stripe Connect Setup

GitHub Sponsors uses Stripe Connect for payouts.

#### Option 1: Individual Account (Recommended for solo developers)

1. **Connect Stripe Account**
   - Click "Set up payouts" in GitHub Sponsors
   - Sign in or create Stripe account
   - Complete Stripe identity verification

2. **Verification Requirements**
   ```
   - Government-issued ID
   - Social Security Number (US) or equivalent
   - Bank account information
   - Address verification
   ```

3. **Bank Account Setup**
   ```
   Routing Number: [Your bank's routing number]
   Account Number: [Your bank account number]
   Account Type: Checking
   ```

#### Option 2: Business Account (For companies)

If receiving sponsorship as a business:

1. Create Stripe Connect Business account
2. Provide business registration documents
3. Add business bank account
4. Complete Stripe's business verification

### Payout Schedule

| Timeline | Details |
|----------|---------|
| Month 1 | Funds accumulate in Stripe balance |
| Month 2 | First payout (after 30-day holding period) |
| Ongoing | Monthly payouts on the 1st of each month |

### Fees

- **GitHub Fee**: None (free for sponsors)
- **Stripe Fee**: ~2.9% + $0.30 per transaction
- **Net to You**: ~97% of sponsorship amount

---

## Step 5: Configure Tiers and Benefits

### Set Up Tiers in GitHub Sponsors Dashboard

1. **Navigate to Sponsors Dashboard**
   ```
   https://github.com/sponsors/your-username/editor
   ```

2. **Add Tiers**

   **Tier 1: Supporter - $5/mo**
   ```
   Name: Supporter
   Monthly Amount: $5
   Description:
     Thank you for supporting EnterpriseHub!
     - Name in README sponsors section
     - Sponsor badge on your GitHub profile
     - Priority updates on releases
   ```

   **Tier 2: Builder - $15/mo**
   ```
   Name: Builder
   Monthly Amount: $15
   Description:
     For developers building on EnterpriseHub.
     - Everything in Supporter, plus:
     - 24-hour response to GitHub issues
     - Builder sponsor badge
     - Quarterly 30-min video calls
     - Early access to new features
   ```

   **Tier 3: Enterprise - $50/mo**
   ```
   Name: Enterprise
   Monthly Amount: $50
   Description:
     For organizations needing dedicated support.
     - Everything in Builder, plus:
     - Monthly 30-min consultation call
     - Dedicated Slack channel
     - 4-hour SLA-backed response
     - Enterprise sponsor badge
     - Co-marketing opportunity
   ```

3. **Enable/Disable Tiers**
   - Toggle visibility for each tier
   - Can hide higher tiers initially

---

## Step 6: Add Sponsors Button to Repositories

### Repository README

Add this to each relevant repository's README.md:

```markdown
---

## ❤️ Support the Project

If EnterpriseHub helps your business, consider sponsoring:

👉 [Sponsor via GitHub Sponsors](https://github.com/sponsors/ChunkyTortoise)

| Tier | Price | What You Get |
|------|-------|--------------|
| Supporter | $5/mo | Name in README |
| Builder | $15/mo | 24h issue support |
| Enterprise | $50/mo | Monthly calls |
```

### Profile README

Add to your personal profile README:

```markdown
---

## ❤️ Sponsorship

My open-source work is sponsored by:

[Become a sponsor](https://github.com/sponsors/ChunkyTortoise)

Thank you to all my sponsors! 🙏
```

---

## Step 7: Promote Your Sponsors Page

### Promotion Channels

1. **Repository READMEs**
   - Add sponsorship call-to-action to main repos

2. **Documentation**
   - Add sponsorship page to docs/
   - Link from "Support" or "About" sections

3. **Release Notes**
   ```
   v2.0.0 Release Notes
   ...
   Thank you to our sponsors for making this release possible!
   ```

4. **Social Media**
   - Announce sponsorship availability
   - Thank new sponsors publicly

5. **Website**
   - Add "Sponsor" link in navigation
   - Create dedicated sponsorship page

---

## Timeline Expectations

| Phase | Duration | What Happens |
|-------|----------|--------------|
| Application Review | 2-7 days | GitHub reviews application |
| Stripe Verification | 1-3 days | Complete Stripe setup |
| Profile Launch | 1 day | Sponsors page goes live |
| First Sponsor | Variable | Depends on promotion |
| First Payout | 60 days | 30-day hold + payout cycle |

### Typical Timeline

```
Week 1: Submit application
Week 2: Receive approval, set up Stripe
Week 3: Configure tiers, add CTAs to repos
Week 4-8: Promote, attract sponsors
Week 9+: Receive first payout
```

---

## Best Practices

### Do

- ✅ Complete your profile before applying
- ✅ Enable 2FA at least 2 weeks before applying
- ✅ Have active public repositories with meaningful contributions
- ✅ Promote your sponsors page consistently
- ✅ Thank sponsors publicly

### Don't

- ❌ Apply immediately after creating GitHub account
- ❌ Submit incomplete applications
- ❌ Set up without Stripe verification ready
- ❌ Forget to add sponsorship CTAs to repositories

---

## Troubleshooting

### "Not Eligible for GitHub Sponsors"

**Common reasons:**
- Account is less than 90 days old
- No verified email
- No 2FA enabled
- No public repository activity

**Solutions:**
1. Enable 2FA and wait 2 weeks
2. Make regular contributions to public repos
3. Complete profile with bio and avatar

### Stripe Verification Issues

**Solutions:**
1. Ensure legal name matches ID exactly
2. Use a checking account (not savings)
3. Contact Stripe support if stuck

### Low Sponsorship

**Solutions:**
1. Add sponsors button to all repositories
2. Announce in blog posts or social media
3. Show impact of sponsorship with metrics
4. Engage with potential sponsors in comments

---

## Additional Resources

- [GitHub Sponsors Help](https://docs.github.com/en/sponsors)
- [Stripe Connect Documentation](https://stripe.com/docs/connect)
- [Sponsorship Best Practices](https://opensource.guide/getting-paid/)

---

*Last updated: February 2026*
