# Visual Assets Master Plan

**Author**: Visual Assets Agent (dashboard-design)
**Date**: 2026-02-16
**Scope**: 4 products, 28 screenshots, 8 metrics graphics
**Brand System**: Obsidian theme (dark mode primary) + Light mode variants for Gumroad

---

## Brand Consistency Guidelines

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| Primary | `#6366F1` | CTAs, highlights, chart accents |
| Primary Glow | `rgba(99, 102, 241, 0.4)` | Hover states, focus rings |
| Secondary | `#8B5CF6` | Secondary accents, gradient endpoints |
| Background Deep | `#05070A` | App backgrounds (dark mode) |
| Card BG | `#161B22` | Card surfaces, panels |
| Elevated BG | `#1C2128` | Modal overlays, dropdown menus |
| Text Primary | `#FFFFFF` | Headings, primary labels |
| Text Secondary | `#E6EDF3` | Body text, descriptions |
| Text Muted | `#8B949E` | Captions, metadata |
| Status Hot | `#EF4444` | Hot leads, critical alerts |
| Status Warm | `#F59E0B` | Warm leads, warnings |
| Status Cold | `#3B82F6` | Cold leads, informational |
| Status Success | `#10B981` | Positive metrics, active status |

### Typography

| Element | Font Family | Size | Weight |
|---------|------------|------|--------|
| Page Title | Space Grotesk | 2.5rem (40px) | 700 (Bold) |
| Section Header | Space Grotesk | 1.5rem (24px) | 600 (SemiBold) |
| Card Title | Inter | 1.125rem (18px) | 600 |
| Body Text | Inter | 1rem (16px) | 400 (Regular) |
| Metric Value | Space Grotesk | 2rem (32px) | 700 |
| Metric Label | Inter | 0.875rem (14px) | 500 (Medium) |
| Caption/Muted | Inter | 0.75rem (12px) | 400 |
| Code | JetBrains Mono | 0.875rem (14px) | 400 |

### Annotation Style

| Element | Style | Color |
|---------|-------|-------|
| Highlight Box | 2px solid, 4px border-radius | `#EF4444` (red) |
| Arrow | 2px stroke, triangle head | `#F59E0B` (amber) |
| Callout Number | 24px circle, centered digit | `#6366F1` (primary) |
| Caption Banner | Bottom-anchored, 60% opacity BG | `#161B22` at 80% opacity |
| Tooltip | Rounded rect, 8px padding | `#1C2128` with `#E6EDF3` text |

### Capture Standards

| Setting | Value |
|---------|-------|
| Window Dimensions | 1920x1080 (16:9 primary) |
| Retina Export | 2x (3840x2160 actual pixels) |
| Gumroad Thumbnails | 1280x720 (16:9, optimized for listing) |
| README Inline | 800x450 (compressed PNG, <200KB) |
| File Format | PNG (screenshots), SVG (diagrams), WebP (web) |
| Compression | pngquant --quality=80-95 |
| Naming Convention | `{product}-{feature}-{variant}.png` |
| DPI | 144 (Retina) / 72 (standard web) |

---

## Screenshot Inventory Summary

| Product | Screenshots | Priority | Live Demo URL |
|---------|------------|----------|---------------|
| EnterpriseHub | 7 | P0 | https://ct-enterprise-ai.streamlit.app |
| AgentForge | 7 | P0 | https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/ |
| DocQA Engine | 7 | P0 | (deploy pending) |
| Insight Engine | 7 | P0 | (deploy pending) |
| **Total** | **28** | | |

## Metrics Graphics Inventory

| Graphic Type | Count | Priority |
|-------------|-------|----------|
| Before/After Comparison | 4 | P0 |
| ROI Waterfall Charts | 2 | P1 |
| Feature Comparison Matrix | 2 | P1 |
| **Total** | **8** | |

---

## Capture Workflow

### Step 1: Environment Setup
1. Set browser to 1920x1080 viewport (Chrome DevTools device toolbar)
2. Use dark mode for Streamlit apps (matches Obsidian theme)
3. Disable browser extensions that add UI clutter
4. Clear notification badges, close other tabs

### Step 2: Capture Sequence (per product)
1. Load the live Streamlit URL
2. Wait for all charts/data to render (check for loading spinners)
3. Use Chrome screenshot (Ctrl+Shift+P > "Capture screenshot") for full page
4. For specific sections, use element-level capture
5. Save raw capture to `content/visual/raw/{product}/`

### Step 3: Annotation
1. Open raw screenshot in annotation tool (Figma, Snagit, or Preview)
2. Apply highlight boxes per spec (red `#EF4444`, 2px solid)
3. Add numbered callouts per spec (primary `#6366F1` circles)
4. Add caption banner at bottom
5. Export to `content/visual/final/{product}/`

### Step 4: Optimization
1. Run `pngquant --quality=80-95 --strip` on all PNGs
2. Generate 1280x720 thumbnail variant for Gumroad
3. Generate 800x450 variant for README embedding
4. Verify all files < 200KB for README variants

---

## Deliverable Files

| File | Description |
|------|-------------|
| `SCREENSHOT_PLAN.md` | This master plan (you are reading it) |
| `agentforge-screenshots.md` | 7 screenshot specs for AgentForge |
| `docqa-screenshots.md` | 7 screenshot specs for DocQA Engine |
| `insight-screenshots.md` | 7 screenshot specs for Insight Engine |
| `enterprisehub-screenshots.md` | 7 screenshot specs for EnterpriseHub |
| `metrics-graphics-spec.md` | 8 before/after and ROI graphics specs |

---

## Cross-Product Consistency Checklist

- [ ] All screenshots use same 1920x1080 viewport
- [ ] Annotation colors match brand palette (red highlight, amber arrows, primary callouts)
- [ ] Caption font is Inter 14px Medium, white on dark overlay
- [ ] Gumroad thumbnails all 1280x720 with consistent title placement
- [ ] README images all 800x450 with < 200KB file size
- [ ] Dark mode active for all Streamlit captures
- [ ] Chart color schemes use primary/secondary palette consistently
- [ ] No PII, dummy data only in all screenshots
- [ ] File naming follows `{product}-{feature}-{variant}.png` pattern
