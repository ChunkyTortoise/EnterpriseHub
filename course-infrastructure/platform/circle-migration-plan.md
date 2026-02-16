# Circle Migration Plan

Plan for migrating from Maven to Circle after Cohort 1, targeting Cohort 3+ for full transition.

## Why Migrate

| Factor | Maven | Circle |
|--------|-------|--------|
| Platform fee | 10% of revenue | $89-$399/mo flat fee |
| Community features | Basic discussion | Full community platform |
| Custom branding | Limited | Full white-label |
| Payment flexibility | Maven-only checkout | Stripe direct integration |
| Content hosting | Built-in | Built-in + API access |
| Break-even point | < 15 students/cohort | > 15 students/cohort |

At 25 students paying $1,297 average, Maven takes ~$3,242/cohort vs Circle's $399/mo ($2,394/6mo). Circle saves $848+ per cohort at scale.

## Migration Timeline

### Phase 1: Parallel Operation (Cohort 2)

**Timeline**: During Cohort 2 delivery

| Task | Description |
|------|-------------|
| Create Circle space | Set up "Production AI Systems" space |
| Mirror Discord structure | Replicate channel categories in Circle |
| Import content | Upload recorded sessions from Cohort 1 |
| Test payment flow | Configure Stripe checkout in Circle |
| Invite beta testers | 3-5 Cohort 1 alumni to test Circle experience |

### Phase 2: Soft Launch (Cohort 3)

**Timeline**: Cohort 3 enrollment period

| Task | Description |
|------|-------------|
| List course on Circle | Full course listing with pricing tiers |
| Redirect marketing | Update landing page, email sequences to Circle links |
| Migrate self-paced | Move $397 self-paced option to Circle |
| Keep Maven listing | Maintain for discoverability, link to Circle |

### Phase 3: Full Migration (Cohort 4+)

**Timeline**: After Cohort 3 completes

| Task | Description |
|------|-------------|
| Archive Maven course | Set to "not accepting enrollment" |
| Consolidate community | Merge Discord into Circle community |
| Alumni migration | Invite all previous students to Circle |
| Update all links | Marketing, email sequences, social profiles |

## Circle Space Structure

```
Production AI Systems (Space)
├── Welcome
│   ├── Start Here (pinned)
│   ├── Introductions
│   └── Course Calendar
├── Cohort [N] (per-cohort)
│   ├── Announcements
│   ├── Week 1: Agent Architecture
│   ├── Week 2: RAG Systems
│   ├── Week 3: MCP Integration
│   ├── Week 4: Production Hardening
│   ├── Week 5: Observability
│   └── Week 6: Deployment
├── Labs
│   ├── Lab Help
│   ├── Submissions
│   └── Showcase
├── Community
│   ├── General Discussion
│   ├── Jobs & Opportunities
│   ├── Resources
│   └── Off-Topic
└── Self-Paced
    ├── Getting Started
    ├── Recorded Sessions
    └── Q&A Forum
```

## Feature Comparison

| Feature | Maven | Circle | Discord (current) |
|---------|-------|--------|-------------------|
| Course content hosting | Yes | Yes | No |
| Payment processing | Yes | Yes (Stripe) | No |
| Community discussions | Basic | Rich (threads, reactions) | Rich |
| Live events | Zoom integration | Zoom/native | Voice channels |
| Mobile app | Yes | Yes | Yes |
| Custom domain | No | Yes ($) | No |
| API access | Limited | Full REST API | Bot API |
| Analytics | Basic | Advanced | Bot-dependent |
| Price | 10% revenue share | $89-$399/mo | Free |

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Student confusion during transition | Clear communication 4 weeks before switch |
| Lost community engagement | Run both platforms in parallel for 1 cohort |
| Payment disruption | Test Stripe integration thoroughly before switch |
| SEO/discoverability loss | Maintain Maven listing as redirect |
| Content migration issues | Export and re-upload incrementally, verify each module |

## Decision Criteria

Migrate to Circle when:
1. Cohort enrollment consistently exceeds 15 students
2. Self-paced sales exceed 20/month
3. Community size exceeds 100 active members
4. Corporate training requests require white-label solution

Stay on Maven if:
1. Enrollment stays below 15/cohort (platform discovery value outweighs fees)
2. Self-paced is not yet a significant revenue stream
3. Admin overhead of running own platform is not justified
