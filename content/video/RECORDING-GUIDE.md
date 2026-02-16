# Video Recording Guide

**Last Updated:** 2026-02-16
**Total Videos:** 5 (1 long-form + 1 short-form + 3 product demos)

---

## Video Inventory

| # | Product | Duration | Script Location | Status |
|---|---------|----------|-----------------|--------|
| 1 | EnterpriseHub (full walkthrough) | 6:30 | `content/video/enterprisehub-walkthrough-script.md` | Script ready |
| 2 | EnterpriseHub (90s demo) | 1:30 | `content/video/enterprisehub-90s-demo-script.md` | Script ready |
| 3 | AgentForge | 2:00 | `content/video/agentforge-demo-script.md` | Script ready |
| 4 | DocQA Engine | 2:00 | `content/video/docqa-demo-script.md` | Script ready |
| 5 | Prompt Engineering Toolkit | 2:00 | `content/video/prompt-lab-demo-script.md` | Script ready |
| 6 | AI Integration Starter Kit | 2:00 | `content/video/llm-starter-demo-script.md` | Script ready |

---

## Recording Priority Order

1. **EnterpriseHub 90s demo** -- Highest ROI. Short, shareable, good for LinkedIn/socials.
2. **EnterpriseHub 6:30 walkthrough** -- Deep-dive for portfolio page, YouTube, Gumroad.
3. **AgentForge 2min** -- Flagship product, live Streamlit demo available.
4. **Prompt Lab 2min** -- Lowest price point, widest audience.
5. **LLM Starter 2min** -- Complements Prompt Lab, live demo available.
6. **DocQA 2min** -- Highest price product, strongest technical depth.

---

## Technical Setup

### Hardware
- **Microphone:** USB condenser mic (Blue Yeti, Rode NT-USB) or lapel mic. Avoid laptop built-in.
- **Camera:** 1080p minimum. Webcam or phone on tripod for face shots.
- **Lighting:** Ring light or window light. Avoid overhead shadows.
- **Display:** 1440p or higher for crisp screen recordings.

### Software
| Tool | Purpose | Cost |
|------|---------|------|
| OBS Studio | Screen recording + webcam | Free |
| DaVinci Resolve | Video editing | Free |
| Descript | Transcription + captions | $24/mo |
| Canva | Thumbnails + title cards | Free tier |

### Recording Settings
- **Resolution:** 1440p (2560x1440) for screen recordings, 1080p for face
- **Frame rate:** 30fps (screen), 30fps (face)
- **Audio:** 48kHz, mono, noise gate enabled
- **Format:** MKV (OBS) -- remux to MP4 after recording

---

## Pre-Recording Checklist

### For Every Video
- [ ] Close all unrelated browser tabs and apps
- [ ] Disable notifications (Focus mode on macOS)
- [ ] Set terminal font to 16pt+ for readability
- [ ] Set browser zoom to 125% for Streamlit demos
- [ ] Test microphone levels (peak at -12dB to -6dB)
- [ ] Clean desktop background
- [ ] Verify demo URLs are live and responsive

### Live Demo URLs to Verify
- [ ] https://ct-enterprise-ai.streamlit.app (wake 30min before)
- [ ] https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/
- [ ] https://ct-prompt-lab.streamlit.app/
- [ ] https://ct-llm-starter.streamlit.app/

### Environment
- [ ] API keys set (for live LLM demos -- use low-cost models)
- [ ] Docker running (for `docker-compose up` demos)
- [ ] Git repos cloned with green CI badges visible

---

## Recording Workflow

### Step 1: Record Each Section Separately
Record each timestamped section as an individual clip. This allows:
- Multiple takes without re-doing the whole video
- Easier editing and timing adjustments
- Flexibility to reorder sections in post

### Step 2: Delivery Pace
- **Hook (Act 1):** 2.7 words/sec -- energetic, punchy
- **Demo (Act 2):** 2.3 words/sec -- slower, let visuals breathe
- **CTA (Act 3):** 2.5 words/sec -- confident, direct

### Step 3: Screen Recording Tips
- Move cursor slowly and deliberately
- Pause 1-2 seconds after clicking before narrating the result
- Highlight key UI elements with cursor circles (OBS filter or post-production)
- Use keyboard shortcuts instead of menus when possible

### Step 4: Common Mistakes to Avoid
- Do NOT say "um", "like", "you know" -- re-take the section
- Do NOT rush through metrics -- pause for emphasis on key numbers
- Do NOT demo with small font sizes -- viewers watch on phones
- Do NOT show API keys, env files, or personal information on screen

---

## Post-Production Checklist

### For Every Video
- [ ] Trim dead air at start/end of each section
- [ ] Add title card (first 3 seconds)
- [ ] Add lower-third text for key metrics (numbers on screen)
- [ ] Add subtle background music (royalty-free, low volume)
- [ ] Add captions (Descript auto-transcribe, review for accuracy)
- [ ] Export: H.264, 1080p, ~8Mbps bitrate
- [ ] Create thumbnail (product name + 1 key metric + face optional)

### Thumbnail Templates
Each thumbnail should include:
- Product name (large, bold)
- One headline metric (e.g., "4.3M dispatches/sec", "500+ tests")
- Technology badges (Python, Docker, FastAPI icons)
- Clean background (dark gradient or solid)

---

## Distribution Plan

### Per Video
| Platform | Format | Notes |
|----------|--------|-------|
| YouTube | Full video + chapters | SEO-optimized title and description |
| LinkedIn | Native upload (max 10min) | First 3 seconds must hook |
| Gumroad | Embed on product page | Increases conversion 2-3x |
| GitHub README | YouTube embed link | Social proof for repo visitors |
| Portfolio site | Embed or link | chunkytortoise.github.io |

### YouTube Metadata Template
```
Title: [Product Name]: [Key Benefit] | [Key Metric]
Description:
  Line 1: One-sentence value prop
  Line 2: Blank
  Line 3-5: Timestamps (chapters)
  Line 6: Blank
  Line 7: Links (GitHub, Gumroad, demo)
  Line 8: Blank
  Line 9: About me (1 sentence + portfolio link)
Tags: python, ai, llm, [product-specific tags]
```

### Example YouTube Title
```
AgentForge: Multi-LLM Orchestration in 5 Minutes | 4.3M Dispatches/sec
```

---

## Metrics Cheat Sheet (For On-Screen Graphics)

| Product | Metric 1 | Metric 2 | Metric 3 |
|---------|----------|----------|----------|
| EnterpriseHub | 8,500+ tests | 89% cost reduction | <200ms overhead |
| AgentForge | 4.3M dispatches/sec | 550+ tests | 15KB core |
| DocQA | 500+ tests | 5 chunking strategies | $0/mo hosting |
| Prompt Lab | 8 prompt patterns | 190+ tests | A/B testing |
| LLM Starter | 220+ tests | Circuit breaker | 15 examples |

---

*Guide Version: 1.0*
*Created: February 16, 2026*
