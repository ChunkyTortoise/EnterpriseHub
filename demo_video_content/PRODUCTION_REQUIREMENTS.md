# EnterpriseHub Demo Video Production Requirements

**Document Version:** 1.0
**Created:** 2026-02-14
**Status:** Ready for Production
**Total Videos:** 3

---

## Executive Summary

This document contains comprehensive production requirements for creating three promotional videos showcasing the EnterpriseHub platform:

| Video | Duration | Purpose | Priority |
|-------|----------|---------|----------|
| Social Teaser | 60 seconds | Social media, LinkedIn, Instagram | P0 |
| Product Demo | 5 minutes | Website, sales calls | P0 |
| Deep Dive | 15 minutes | Technical audiences, YouTube | P1 |

---

## Part 1: Pre-Production Requirements

### 1.1 Demo Environment Setup

Before any filming, the demo environment must be verified and prepared:

#### Required Systems

| System | Purpose | Status |
|--------|---------|--------|
| Docker Compose | Local environment | Must verify `make demo` works |
| PostgreSQL | Data persistence | Pre-loaded with sample leads |
| Redis | Cache layer | Configured with test data |
| FastAPI | API layer | Running on localhost:8000 |
| Streamlit | BI Dashboard | Running on localhost:8501 |
| Jorge Command Center | Bot management | Running on localhost:8502 |

#### Sample Data Required

- [ ] 10 sample leads in various stages (new, qualified, converted, lost)
- [ ] 3 complete conversation flows (Lead→Buyer→Seller handoff)
- [ ] Demo GHL account with test contacts
- [ ] Pre-generated analytics data (30 days)
- [ ] RAG documents uploaded (market reports, FAQ)

#### Demo Scripts

Prepare 3 conversation scenarios for screen recording:

1. **Scenario A: Buyer Journey**
   - Lead enters via chat
   - Lead Bot qualifies (budget, timeline)
   - Handoff to Buyer Bot
   - Financial readiness assessment
   - Appointment booked

2. **Scenario B: Seller Journey**
   - Lead enters via SMS
   - Lead Bot qualifies
   - Handoff to Seller Bot
   - CMA generation
   - Listing consultation scheduled

3. **Scenario C: Cold Lead Nurture**
   - Lead enters via web form
   - Lead Bot qualifies (low score)
   - Lead added to nurture sequence
   - Follow-up triggered after 24 hours

### 1.2 Technical Assets Required

#### Logo & Branding

| Asset | Format | Requirements |
|-------|--------|--------------|
| Primary Logo | SVG, PNG | White + dark versions |
| Logo Animation | AE/Premiere | 5-second intro |
| Brand Colors | Hex codes | Primary, accent, background |
| Typography | Font files | Headline, body fonts |

#### Graphics & Templates

- [ ] Architecture diagram (animated)
- [ ] Bot icon set (Lead, Buyer, Seller)
- [ ] Metrics cards (conversion, cost, time)
- [ ] Flow diagrams (handoff, caching)
- [ ] End card template
- [ ] Lower third template

#### Screen Recording Setup

| Setting | Specification |
|---------|---------------|
| Resolution | 1920x1080 minimum |
| Frame rate | 30 fps |
| Cursor | Highlighted (Mac accessibility) |
| Browser zoom | 125% |
| Terminal font | 18pt minimum |
| Color scheme | Dark mode preferred |

---

## Part 2: Production Equipment

### 2.1 Filming Equipment Checklist

#### Primary Equipment

| Item | Model | Purpose | Priority |
|------|-------|---------|----------|
| Camera | Sony A7IV or iPhone 15 Pro | Main video capture | Required |
| Lens | 24-70mm f/2.8 | Primary lens | Required |
| Tripod | Manfrotto or similar | Stable shots | Required |
| Gimbal | DJI RS3 or similar | Movement shots | Recommended |
| Lighting | 3-point softbox kit | Professional lighting | Required |

#### Audio Equipment

| Item | Model | Purpose | Priority |
|------|-------|---------|----------|
| Microphone | Shure SM7B or Rode Procaster | Primary voice | Required |
| Preamp | Cloudlifter or similar | Signal boost | Required |
| Headphones | Sony MDR-7506 | Monitoring | Required |
| Lavalier | Rode Wireless Go II | Backup/mobile | Recommended |

#### Screen Capture

| Item | Purpose | Priority |
|------|---------|----------|
| OBS Studio | Primary capture | Required |
| Loom Pro | Quick captures | Recommended |
| Clean feed | No notifications | Required |

### 2.2 Software Requirements

| Software | Purpose | License |
|----------|---------|---------|
| Adobe Premiere Pro | Video editing | Subscription |
| After Effects | Motion graphics | Subscription |
| DaVinci Resolve | Color grading | Free/Studio |
| Descript | Captions, transcription | Subscription |
| Epidemic Sound | Background music | Subscription |
| Rev.com | Professional captions | Per-minute |

---

## Part 3: Production Schedule

### 3.1 Recommended Timeline

| Day | Activity | Deliverables |
|-----|----------|--------------|
| Day 1 | Pre-production review | Scripts approved, assets ready |
| Day 2 | B-roll filming | Office, screen recording |
| Day 3 | Primary filming | Presenter shots, screen demos |
| Day 4 | Screen recording | All demo scenarios captured |
| Day 5 | Editing - Rough cut | All 3 videos rough cuts |
| Day 6 | Editing - Fine cut | Revisions, graphics added |
| Day 7 | Color & Audio | Final color, audio mix |
| Day 8 | Captions & Export | All formats exported |
| Day 9 | Review & Upload | Final review, platform upload |

### 3.2 Filming Day Requirements

#### Pre-Film Checklist

- [ ] All equipment charged/tested
- [ ] Demo environment running
- [ ] Scripts printed (2 copies)
- [ ] Teleprompter set up
- [ ] Backup recording ready
- [ ] Water and breaks scheduled

#### Filming Order

1. **Morning:** Presenter shots (fresh energy)
2. **Mid-day:** Screen recordings (demo environment warm)
3. **Afternoon:** B-roll, additional angles

---

## Part 4: Video Specifications

### 4.1 Social Teaser (60 seconds)

#### Technical Specs

| Attribute | Specification |
|-----------|----------------|
| Aspect Ratio | 9:16 (vertical) + 16:9 (horizontal) |
| Resolution | 1080x1920 / 1920x1080 |
| Frame Rate | 30 fps |
| File Format | MP4 (H.264) |
| Audio | Stereo, -16 LUFS |
| Captions | Burned-in required |

#### Distribution

| Platform | Format | Specs |
|----------|--------|-------|
| LinkedIn | 16:9 | Native upload |
| Instagram | 9:16 | Reels |
| Twitter/X | 16:9 | Native upload |
| YouTube Shorts | 9:16 | Shorts |

### 4.2 Product Demo (5 minutes)

#### Technical Specs

| Attribute | Specification |
|-----------|----------------|
| Aspect Ratio | 16:9 |
| Resolution | 1920x1080 |
| Frame Rate | 30 fps |
| File Format | MP4 (H.264) |
| Audio | Stereo, -16 LUFS |
| Captions | SRT + burned-in |

#### Chapters

| Timestamp | Chapter |
|-----------|---------|
| 0:00 | Platform Overview |
| 1:00 | Lead Bot Demo |
| 2:30 | Bot Handoff System |
| 3:30 | Analytics Dashboard |
| 4:30 | Book Your Demo |

### 4.3 Deep Dive (15 minutes)

#### Technical Specs

| Attribute | Specification |
|-----------|----------------|
| Aspect Ratio | 16:9 |
| Resolution | 1920x1080 |
| Frame Rate | 30 fps |
| File Format | MP4 (H.264) |
| Audio | Stereo, -16 LUFS |
| Captions | SRT + burned-in |
| PiP | Presenter overlay |

#### Chapters

| Timestamp | Chapter |
|-----------|---------|
| 0:00 | Platform Architecture |
| 3:00 | Claude Orchestrator |
| 6:00 | Jorge Handoff Service |
| 9:00 | RAG System |
| 12:00 | Integration Options |
| 14:00 | Summary & CTA |

---

## Part 5: Script Overview

### 5.1 Social Teaser Script Summary

**File:** [`SOCIAL_TEASER_60SEC.md`](SOCIAL_TEASER_60SEC.md)

| Scene | Timestamp | Content |
|-------|-----------|---------|
| Hook | 0:00-0:05 | Problem statement + emotion |
| Problem | 0:05-0:12 | Lead loss statistics |
| Solution | 0:12-0:25 | EnterpriseHub reveal |
| Demo | 0:25-0:45 | Bot demonstration |
| Results | 0:45-0:55 | Key metrics |
| CTA | 0:55-1:00 | Book demo |

### 5.2 Product Demo Script Summary

**File:** [`PRODUCT_DEMO_5MIN.md`](PRODUCT_DEMO_5MIN.md)

| Section | Timestamp | Content |
|---------|-----------|---------|
| Overview | 0:00-1:00 | Problem + solution preview |
| Lead Bot | 1:00-2:30 | Live qualification demo |
| Handoff | 2:30-3:30 | Buyer/Seller bots |
| Analytics | 3:30-4:30 | Dashboard walkthrough |
| CTA | 4:30-5:00 | Summary + booking |

### 5.3 Deep Dive Script Summary

**File:** [`DEEP_DIVE_15MIN.md`](DEEP_DIVE_15MIN.md)

| Section | Timestamp | Content |
|---------|-----------|---------|
| Architecture | 0:00-3:00 | Full system overview |
| Orchestrator | 3:00-6:00 | Claude + caching |
| Handoff | 6:00-9:00 | Jorge service deep dive |
| RAG | 9:00-12:00 | Document intelligence |
| Integrations | 12:00-14:00 | GHL + API |
| Conclusion | 14:00-15:00 | Summary + CTA |

---

## Part 6: Talent & Team

### 6.1 Roles Required

| Role | Responsibility | Notes |
|------|-----------------|-------|
| Presenter | On-camera talent | Must know script |
| Screen operator | Demo management | Controls live demos |
| Camera operator | Filming | Could be same as editor |
| Editor | Post-production | Primary creative role |
| Sound engineer | Audio mixing | Optional, can be editor |

### 6.2 Presenter Guidelines

#### Appearance

- Professional attire (business casual or suit)
- Solid color clothing (no patterns)
- Minimal jewelry
- Natural makeup (for on-camera)

#### Delivery

- Speak slightly slower than normal
- Pause after key numbers
- Maintain eye contact with camera
- Use deliberate hand gestures
- Stay within teleprompter frame

---

## Part 7: Post-Production

### 7.1 Editing Checklist

#### Rough Cut

- [ ] All footage organized in project
- [ ] Best takes selected
- [ ] Basic timeline assembled
- [ ] Timing verified against script
- [ ] Gaps identified and filled

#### Fine Cut

- [ ] All graphics added
- [ ] Transitions smoothed
- [ ] Color grades applied
- [ ] Audio levels balanced
- [ ] Music bed mixed

#### Final

- [ ] Captions generated
- [ ] Captions synced
- [ ] All formats exported
- [ ] Thumbnails created
- [ ] Metadata added

### 7.2 Color Grading

| Video | Look | Notes |
|-------|------|-------|
| Social | High contrast, punchy | Pop on mobile |
| Demo | Clean, professional | Trustworthy |
| Deep Dive | Technical, clear | Easy to read |

### 7.3 Audio Mix

| Element | Level | Notes |
|---------|-------|-------|
| Voice | -3 dB peak | Primary focus |
| Music | -18 dB | 10% of voice |
| SFX | -6 dB | As needed |

---

## Part 8: Distribution

### 8.1 Platform Checklist

#### YouTube

- [ ] Video uploaded
- [ ] Title optimized
- [ ] Description with timestamps
- [ ] Tags added
- [ ] Thumbnail uploaded
- [ ] Chapters added
- [ ] End screen configured

#### LinkedIn

- [ ] Native video uploaded
- [ ] Hook optimized (first 3 seconds)
- [ ] Hashtags added
- [ ] CTA in comments prepared

#### Instagram

- [ ] Vertical version prepared
- [ ] Reels uploaded
- [ ] Hashtags added
- [ ] Profile link ready

#### Twitter/X

- [ ] Short version prepared
- [ ] Tweet thread prepared
- [ ] Media optimized

### 8.2 UTM Tracking

| Source | Medium | Campaign |
|--------|--------|----------|
| youtube | video | demo_video_2026 |
| linkedin | social | social_teaser_2026 |
| instagram | social | social_teaser_2026 |

---

## Part 9: Success Metrics

### 9.1 Targets by Video

| Video | Metric | 30-Day Target | 90-Day Target |
|-------|--------|---------------|---------------|
| Social Teaser | Views | 5,000 | 15,000 |
| Social Teaser | Engagement | 3% | 4% |
| Social Teaser | Demo bookings | 5 | 15 |
| Product Demo | Views | 2,000 | 8,000 |
| Product Demo | Watch time | 60% | 65% |
| Product Demo | Demo bookings | 15 | 40 |
| Deep Dive | Views | 1,000 | 5,000 |
| Deep Dive | Watch time | 70% | 75% |
| Deep Dive | Enterprise inquiries | 5 | 15 |

### 9.2 Tracking Plan

| Metric | Tool | Frequency |
|--------|------|-----------|
| Views | YouTube Analytics | Weekly |
| Engagement | Platform native | Weekly |
| Website visits | Google Analytics | Daily |
| Demo bookings | Calendar | Per booking |
| Conversions | HubSpot | Weekly |

---

## Part 10: Budget Estimate

### 10.1 Estimated Costs

| Category | Item | Cost |
|----------|------|------|
| Equipment | Existing (already owned) | $0 |
| Software | Adobe Creative Cloud | $55/mo |
| Music | Epidemic Sound | $15/mo |
| Captions | Rev.com | ~$100 |
| Talent | Self | $0 |
| **Total** | | **~$170** |

### 10.2 Optional Upgrades

| Item | Cost | Notes |
|------|------|-------|
| Professional editor | $500-1,500 | If outsourcing |
| Stock footage | $100-300 | B-roll supplement |
| Teleprompter rental | $50/day | If needed |
| Studio rental | $200/day | If needed |

---

## Part 11: Risk Mitigation

### 11.1 Potential Issues

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-------------|
| Demo environment fails | Medium | High | Pre-record backup |
| Audio issues | Medium | High | Lav mic backup |
| Presenter unavailable | Low | High | Self-filming |
| Platform outage | Low | Medium | Distribute widely |

### 11.2 Backup Plans

1. **Demo Failure:** Have pre-recorded screen capture as backup
2. **Audio Issues:** Use lav mic + boom as backup
3. **Scheduling:** Build 2-day buffer into timeline

---

## Part 12: Files Created

| File | Path | Description |
|------|------|-------------|
| Social Teaser | `demo_video_content/SOCIAL_TEASER_60SEC.md` | 60-sec social media script |
| Product Demo | `demo_video_content/PRODUCT_DEMO_5MIN.md` | 5-min product walkthrough |
| Deep Dive | `demo_video_content/DEEP_DIVE_15MIN.md` | 15-min technical demo |
| This Document | `demo_video_content/PRODUCTION_REQUIREMENTS.md` | Master production guide |

---

## Appendix A: Quick Reference

### Filming Checklist (Day Of)

- [ ] Demo environment verified
- [ ] Camera battery charged
- [ ] Memory card formatted
- [ ] Lighting checked
- [ ] Audio levels tested
- [ ] Teleprompter loaded
- [ ] Scripts printed
- [ ] Backup recording ready
- [ ] Water/snacks available
- [ ] Emergency contacts shared

### Export Checklist (Per Video)

- [ ] Master file (full quality)
- [ ] Social versions (compressed)
- [ ] Captions file (SRT)
- [ ] Thumbnail image
- [ ] Metadata document

---

**Document Status:** Complete
**Ready for Production:** Yes
**Next Steps:** Schedule filming dates
