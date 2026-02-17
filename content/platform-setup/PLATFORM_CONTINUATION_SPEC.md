# Platform Continuation Spec — Gumroad, Contra, Toptal, Lemon Squeezy

**Date**: 2026-02-17
**Goal**: Advance all 4 platforms in parallel using agent swarm
**Estimated Total Time**: 3-4 hours (agent work) + ~30 min (manual steps)

---

## Current State Summary

| Platform | Account | Products/Listings | Revenue Potential | Blocker |
|----------|---------|-------------------|-------------------|---------|
| **Gumroad** | Verified, bank set up | 0 of 21 uploaded | $75K-$125K/yr | Need to upload 21 products + 3 bundles |
| **Lemon Squeezy** | Store created (test mode) | 0 of 9 uploaded | Backup processor (lower fees) | Identity verification (SSN/bank) |
| **Contra** | Created (11%) | 0 of 3 services | $1,200-$2,000/project | Profile completion + service listings |
| **Toptal** | Not created | N/A | $100-$200+/hr | Application submission |

---

## Workstream 1: Gumroad Product Upload (HIGHEST PRIORITY)

**Bead**: `EnterpriseHub-j9oi` (P1) + `EnterpriseHub-14du` (P0)
**Agent**: Chrome extension browser automation
**Estimated Time**: 90 min

### Assets Ready
- **24 ZIP files** in `content/gumroad/zips/`
- **17 listing descriptions** in `content/gumroad/*-LISTING.md`
- **Repricing strategy** in `content/gumroad/REPRICING-STRATEGY.md`
- **Bank account**: Verified (2026-02-15)

### Products to Upload (21 listings + 3 bundles)

#### Original Products (4 x 3 tiers = 12)
| Product | Starter | Pro | Enterprise |
|---------|---------|-----|------------|
| AgentForge | $49 | $199 | $999 |
| DocQA Engine | $59 | $249 | $1,499 |
| Insight Engine | $49 | $199 | $999 |
| Scrape-and-Serve | $49 | $149 | $699 |

#### Revenue-Sprint Products (3 x 3 tiers = 9)
| Product | Starter | Pro | Enterprise |
|---------|---------|-----|------------|
| Prompt Engineering Toolkit | $29 | $79 | $199 |
| AI Integration Starter Kit | $39 | $99 | $249 |
| Streamlit Dashboard Templates | $49 | $99 | $249 |

#### Bundles (3)
| Bundle | Price | Contents |
|--------|-------|----------|
| All Starters Bundle | $149 | 4 original starters (save 28%) |
| All Pro Bundle | $549 | 4 original pro (save 31%) |
| Revenue Sprint Bundle | $99 | 3 sprint starters (save 16%) |

### Execution Plan
1. Open Gumroad dashboard in Chrome (user must be logged in)
2. For each product: Create → Set name, price, description → Upload ZIP → Publish
3. Create 3 bundles with discount codes
4. Verify all 24 products are published and accessible

### Known Risks
- Gumroad ProseMirror editor: Use clipboard paste, NOT innerHTML injection
- "Publish and continue" only works if bank is verified (confirmed done)
- MCP tools can only get/enable/disable — NOT create products
- Chrome ext `left_click` by coordinate unreliable — use `ref`-based clicks

---

## Workstream 2: Lemon Squeezy Setup (P0)

**Bead**: `EnterpriseHub-lueo` (P0) + `EnterpriseHub-nlfr` (P2)
**Agent**: Chrome extension + manual user step
**Estimated Time**: 60 min (after verification)

### Current State
- Account: caymanroden@gmail.com
- Store: chunkytortoise.lemonsqueezy.com
- Status: **Test Mode** (identity verification pending)
- Spec: `content/platform-setup/GEMINI_LEMONSQUEEZY_COMPLETION_SPEC.md`

### MANUAL STEP REQUIRED
User must complete identity verification at:
`https://app.lemonsqueezy.com/settings/general/identity`
- Requires: SSN or EIN
- Requires: Bank account details (Stripe Connect)
- Timeline: 1-3 business days after submission

### After Verification (Agent Work)
Upload 9 products (3 products x 3 tiers), each with:
- One-time purchase variant
- Monthly subscription variant

| Product | Starter (1x/mo) | Pro (1x/mo) | Enterprise (1x/mo) |
|---------|-----------------|-------------|---------------------|
| AgentForge | $49/$9 | $199/$29 | $999/$149 |
| DocQA Engine | $59/$12 | $249/$39 | $1,499/$199 |
| Prompt Toolkit | $29/$5 | $79/$12 | $199/$29 |

### Execution Plan
1. Check if identity verification is complete
2. If verified: Upload 9 products via Chrome ext
3. Configure email delivery, license keys, tax settings
4. Publish store and verify URLs

---

## Workstream 3: Contra Profile Completion (P2)

**Bead**: `EnterpriseHub-s0zp` (P2)
**Agent**: Chrome extension browser automation
**Estimated Time**: 30 min

### Current State
- Account created: caymanroden@gmail.com
- Profile URL: https://contra.com/cayman_roden_mb0ejazi
- Completeness: ~11% (name, headline, bio, location, photo)
- Content ready: `content/contra/CONTRA_COPY_PASTE_PACKAGE.md`

### Remaining Steps
1. **Add social links** (5 min):
   - LinkedIn: linkedin.com/in/caymanroden
   - GitHub: github.com/ChunkyTortoise
   - Portfolio: chunkytortoise.github.io

2. **Add skills** (3 min):
   Python, FastAPI, AI/ML, RAG Systems, LLM Integration, Chatbot Development, Streamlit, PostgreSQL, Redis, Docker

3. **Create 3 service listings** (15-20 min):
   | Service | Price | Delivery |
   |---------|-------|----------|
   | Custom RAG AI System | $1,500 | 5-7 days |
   | Claude/GPT Chatbot Integration | $2,000 | 7-10 days |
   | Streamlit Analytics Dashboard | $1,200 | 5-7 days |

4. **Set hourly rate**: $65-75/hr
5. **Add work samples** (optional): 4 portfolio items

### Execution Plan
1. Navigate to Contra profile edit page
2. Add social links, skills
3. Create each service listing with full description from content files
4. Set rates and availability
5. Verify profile completeness

---

## Workstream 4: Toptal Application (P1)

**Bead**: `EnterpriseHub-iet4` (P1)
**Agent**: Chrome extension + research agent
**Estimated Time**: 30 min (application only)

### Current State
- Not applied
- Full application content ready: `content/platform-applications/toptal-APPLICATION.md`
- 4-stage screening process (3-8 weeks total)

### What We Can Do Now
1. **Submit initial application** via toptal.com
2. **Fill in profile** with prepared content:
   - Title: Senior Python/AI Engineer | RAG Systems, LLM Orchestration, Production GenAI
   - Summary: From application file
   - Skills: Python, FastAPI, PostgreSQL, Redis, Docker, Claude API, etc.
   - Availability: Part-time or full-time, immediate, remote

### What Requires User Prep (Later)
- Stage 2: LeetCode/Codility prep (1-2 weeks recommended)
- Stage 3: Live technical interview prep
- Stage 4: Test project (1-3 weeks)

### Execution Plan
1. Navigate to toptal.com/talent/apply
2. Fill application form with prepared content
3. Submit and note confirmation/next steps
4. Create prep bead for Stage 2 practice

---

## Agent Swarm Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Team Lead (Main)                     │
│  Coordinates all 4 workstreams, tracks beads           │
└──────┬──────────┬──────────┬──────────┬───────────────┘
       │          │          │          │
   ┌───▼───┐ ┌───▼───┐ ┌───▼───┐ ┌───▼───┐
   │Gumroad│ │Lemon  │ │Contra │ │Toptal │
   │Upload │ │Squeezy│ │Setup  │ │Apply  │
   │Agent  │ │Agent  │ │Agent  │ │Agent  │
   └───────┘ └───────┘ └───────┘ └───────┘
   Chrome    Chrome    Chrome    Chrome
   ext       ext       ext       ext
   21+3      9 prod    3 svc     1 app
   products  (if ver)  listings  form
```

### Parallel Execution Strategy
- **Phase 1** (immediate): Contra + Toptal + Gumroad (all independent)
- **Phase 2** (after user action): Lemon Squeezy (blocked on identity verification)
- **Phase 3** (verification): Cross-check all platforms, update beads + platform-profiles.md

### Beads to Update
| Bead | Action |
|------|--------|
| `EnterpriseHub-j9oi` | Close after Gumroad upload |
| `EnterpriseHub-14du` | Partial (metrics on pages) |
| `EnterpriseHub-lueo` | Close or note blocker |
| `EnterpriseHub-nlfr` | Close after LS upload |
| `EnterpriseHub-s0zp` | Close after Contra setup |
| `EnterpriseHub-iet4` | Close after Toptal apply |

---

## Success Criteria

- [ ] **Gumroad**: 21 products + 3 bundles published and purchasable
- [ ] **Lemon Squeezy**: Identity verification submitted (or products uploaded if already verified)
- [ ] **Contra**: Profile 90%+ complete with 3 service listings live
- [ ] **Toptal**: Application submitted
- [ ] All relevant beads closed or updated
- [ ] `platform-profiles.md` updated with new status
- [ ] `revenue-tracker.md` updated if any sales occur
