# GitHub Sponsors - Quick Reference Card

**URL**: https://github.com/sponsors
**Account**: ChunkyTortoise
**Email**: caymanroden@gmail.com

---

## Setup Flow (5 Steps)

1. **Enroll** → 2. **Verify** → 3. **Payout** → 4. **Profile** → 5. **Publish**

---

## Profile Info (Copy/Paste)

**Headline**:
```
Building production-ready AI/ML tools & frameworks
```

**Featured Repos** (select 3):
- `ai-orchestrator` (AgentForge)
- `docqa-engine` (DocQA)
- `insight-engine` (Streamlit dashboards)

**Monthly Goal**:
- Amount: **$500**
- Purpose: "Dedicate 20hrs/month to open-source development and community support"

**Goals** (3 items):
1. Support development of open-source AI tools
2. Dedicate 10hrs/month to community support
3. Create tutorials & documentation

---

## Tier Pricing (5 Tiers)

| Tier | Price | Key Benefits |
|------|-------|-------------|
| **Supporter** | $5/mo | Name in SPONSORS.md, early access, monthly updates |
| **Contributor** | $10/mo | + Priority support (24hr), private community |
| **Partner** | $25/mo | + 1hr consultation/month, feature priority |
| **Professional** | $50/mo | + Code reviews (2hrs/mo), custom integration |
| **Enterprise** | $100/mo | + 4hrs/mo support, SLA, custom features |

*Full tier descriptions in setup guide (github-sponsors-setup-guide.md, pages 3-5)*

---

## Payout Setup

**Recommended**: Stripe Connect (easiest)
- Business: Individual or LLC
- Email: caymanroden@gmail.com

**Tax Form**: W-9 (if US) / W-8BEN (if international)
- Name: Cayman Roden
- TIN/SSN: [Your tax ID]

---

## After Publishing

### 1. Add to Repos
```bash
# For each repo:
cp FUNDING.yml <repo>/.github/
cp SPONSORS.md <repo>/
# Add badge to README (see assets file)
```

### 2. Verify
```bash
./verify-sponsors-setup.sh
```

### 3. Announce
- LinkedIn ✓
- Twitter/X ✓
- Dev.to ✓
- HackerNews ✓

*Templates in: github-sponsors-assets.md*

---

## Profile URLs

- **Live Profile**: https://github.com/sponsors/ChunkyTortoise
- **Settings**: https://github.com/settings/sponsors
- **Payouts**: https://github.com/settings/sponsors/payouts

---

## Files Reference

| File | Purpose |
|------|---------|
| `github-sponsors-setup-guide.md` | Detailed step-by-step (7KB) |
| `github-sponsors-bio.md` | Bio text (already exists) |
| `github-sponsors-assets.md` | Templates, badges, emails (10KB) |
| `github-sponsors-status.md` | Progress tracker (5KB) |
| `SPONSORS.md` | Repo sponsor file (4KB) |
| `FUNDING.yml` | Sponsor button config (48B) |
| `verify-sponsors-setup.sh` | Verification script |
| `GITHUB_SPONSORS_SETUP_SUMMARY.md` | Full summary |
| `QUICK_REFERENCE.md` | This file |

---

## Common Issues

**Issue**: Waitlisted
→ **Fix**: Join waitlist, expect 1-7 days

**Issue**: Payout verification failed
→ **Fix**: Check bank details, tax form

**Issue**: Sponsor button not showing
→ **Fix**: Add `.github/FUNDING.yml`, wait 10 min

**Issue**: Can't create tiers
→ **Fix**: Ensure $1 minimum, whole dollar amounts

---

## Contact

- **GitHub Support**: https://support.github.com/contact
- **Stripe Support**: https://support.stripe.com

---

**Time Estimate**: 1-2 hours setup, 30-60 min announcement
**First Sponsor**: Week 1-2
**Goal**: $500/month by Month 6

---

**Quick Start**: Open `github-sponsors-setup-guide.md` → Go to github.com/sponsors → Follow steps 1-10
