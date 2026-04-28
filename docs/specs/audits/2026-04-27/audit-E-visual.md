# Audit E — Visual / UX / Demo Polish
**Date:** 2026-04-27
**Auditor:** Agent E (Visual/UX)
**Scope:** Live demo URL, README hero, Streamlit Cloud app, Obsidian Ember theme

---

## DEMO STATUS — P0 CONFIRMED: Viewer Authentication Gate

**Verdict:** The 303 redirect loop at `https://ct-enterprise-ai.streamlit.app` is **not a broken deployment** and not a sleeping-app wake. It is Streamlit Community Cloud's **Viewer Authentication** feature, which was switched on in the Streamlit Cloud dashboard. The redirect chain is:

```
GET ct-enterprise-ai.streamlit.app
  -> 303 share.streamlit.io/-/auth/app?redirect_uri=...
  -> 303 ct-enterprise-ai.streamlit.app/-/login?payload=<jwt>
  -> 303 ct-enterprise-ai.streamlit.app/
  -> 303 share.streamlit.io/-/auth/app?...   (loop)
```

This loop is produced because curl carries no browser session cookies and cannot complete the OAuth handshake. In a real browser the flow completes, but it lands on a **Google/GitHub login wall** and then a **viewer allowlist check**. Anyone not on the allowlist is rejected — they never see the demo. A hiring manager clicking the badge in README gets this exact loop or an "Access denied" screen.

**Severity: P0.** Portfolio-link-broken. The README "demo-live" badge and the Live Demo table both link directly to this URL. A gated demo that requires the owner to whitelist each visitor is functionally equivalent to no demo for cold outreach.

**Root cause (confirmed):** Streamlit Cloud "Viewer auth" setting is on. This is a dashboard toggle (Settings > Sharing > "Only specific people can view this app"). The code itself is correct and self-contained (no external dependencies, full mock data).

**Fix plan (Week 1 must-do):**

1. Log in to share.streamlit.io with the ChunkyTortoise account.
2. Open the `ct-enterprise-ai` app settings.
3. Under Sharing, switch from "Only specific people" to "This app is public".
4. Save. Verify `curl -sI https://ct-enterprise-ai.streamlit.app` returns `HTTP/2 200`.
5. Check that the chatbot demo page at `/chatbot_demo` also loads without auth.
6. Update the README Live Demo table note to remove the demo_user/Demo1234! credentials block (they apply to the FastAPI auth layer, not Streamlit Cloud viewer auth, and having them there implies the Streamlit app has its own login, which it does not).

**ETA to fix:** 5 minutes in the dashboard, zero code changes required.

---

## Screenshot Inventory

Screenshots available in `/Users/cave/Projects/EnterpriseHub/assets/screenshots/`:

| File | Dimensions | Size | Date | Notes |
|---|---|---|---|---|
| `banner.png` | 1200x630 | 170 KB | 2026-03-28 | Obsidian Ember hero; OG-card compliant |
| `platform-overview.png` | 1440x900 | 121 KB | 2026-03-28 | Refreshed with Ember theme |
| `lead-intelligence.png` | unknown | 94 KB | 2026-03-25 | Pre-Ember palette? (older date) |
| `cache-performance.png` | unknown | 127 KB | 2026-03-25 | Pre-Ember palette? |
| `jorge_dashboard_01.png` | 3840x2160 | 4.1 MB | 2026-02-18 | 4K retina, indigo/teal palette — OLD THEME |
| `content-engine.png` | unknown | 2.1 MB | 2026-02-18 | OLD THEME |
| `design-system.png` | unknown | 1.8 MB | 2026-02-18 | OLD THEME |
| `market-pulse.png` | unknown | 1.9 MB | 2026-02-18 | OLD THEME |
| `Screenshot_1.jpg` — `Screenshot_10.jpg` | unknown | — | 2026-02-18 | Unlabeled, OLD THEME |

**Key finding:** Five major screenshots (`jorge_dashboard_01.png`, `content-engine.png`, `design-system.png`, `market-pulse.png`, `Screenshot_*.jpg`) were captured in February 2026 with the old "Obsidian Command" indigo/teal palette. The Obsidian Ember theme was applied in March 2026. Only `banner.png` and `platform-overview.png` reflect the current theme. The README Screenshots section shows two of the three images from pre-Ember captures.

**Live screenshots:** None captured from browser — the demo URL is auth-gated and Chrome MCP could not complete the OAuth loop. Screenshots reflect static asset inspection only.

---

## Per-Rubric Scores

### 1. Live Demo Accessibility and First Impression — 1/10

The demo URL is unreachable without being on the Streamlit Cloud viewer allowlist. A hiring manager receives either an infinite redirect loop (via curl/some clients) or a Google/GitHub login screen followed by "Access denied." There is no fallback, no error message, no indication that credentials are needed. The README demo_user/Demo1234! credentials are for the FastAPI layer, not for Streamlit Cloud auth — they will not unlock the demo.

**Target score after fix: 8/10** — the app code is solid, mock data is realistic, no external dependencies.

### 2. README Hero Quality — 6/10

Strengths:
- `banner.png` (1200x630) is OG-card compliant and on-theme (Obsidian Ember was added 2026-03-28).
- The executive summary opens with a concrete business problem ("40% of leads lost after 5-minute SLA") — this is strong.
- The business impact table leads with hard numbers before the architecture, which is the right order for non-technical scanners.
- The "demo-live" badge is visually prominent.

Weaknesses:
- The broken demo badge actively undermines the hero. A hiring manager who clicks it immediately loses trust — a "live" badge that goes nowhere is worse than no badge.
- `platform-overview.png` (1440x900, Ember-themed) is not in the hero position. It is buried below the Architecture section in a two-column table.
- The banner is a generated graphic with text overlay, not a real dashboard screenshot. It signals "this is a project" not "this is a product."
- "7,678 collectible tests" in the badge reads oddly — "collectible" sounds like a marketing qualifier that invites skepticism. "7,678 test functions" is used in the footer, which is more precise.

### 3. Visual Consistency Across Surfaces — 4/10

There are three distinct theme generations active simultaneously:

| Surface | Palette | Theme name |
|---|---|---|
| `.streamlit/config.toml` | #E8734A primary (Ember orange) | Obsidian Ember |
| `theme_service.py` | #E8734A brand.primary | Obsidian Ember |
| `streamlit_cloud/app.py` | Uses config.toml; no custom CSS injection | Obsidian Ember (partial) |
| `obsidian_theme.py` (ghl_real_estate_ai demo) | #6366F1 elite-accent (indigo) | Obsidian Command v2.0 (OLD) |
| February screenshots | Indigo/teal (#6366F1, #00E5FF) | Obsidian Command v2.0 (OLD) |

The Streamlit Cloud app correctly uses the `config.toml` Ember palette (orange primaryColor) but does NOT inject the custom CSS from `obsidian_theme.py` — so widgets render in the base dark theme with an orange accent, not the full glassmorphism/SaaS-Noir treatment that the `ghl_real_estate_ai` demo uses.

The README Screenshots section displays `platform-overview.png` (Ember, new) next to `lead-intelligence.png` (unknown age, likely old indigo palette). This creates a visible color clash on the GitHub README.

### 4. Accessibility (axe-core) — N/A (estimated 3/10)

Browser access was blocked by the auth gate; axe-core could not be injected. Static code review findings:

- `inject_elite_css()` in `obsidian_theme.py` sets `color: var(--text-secondary)` as the global body color (`#8B949E` — gray). This is approximately 4.5:1 contrast on the `#0A0706` background, which passes AA for large text but fails AA for body text (<18px regular). For small captions and status labels, likely fails WCAG 2.1 AA.
- All navigation is via `st.radio()` with `label_visibility="collapsed"` — the label is visually hidden, which hides the control's semantic label from screen readers. Streamlit's built-in radio renders as a fieldset, so this may partially degrade.
- `unsafe_allow_html=True` is used extensively. Custom HTML blocks (`.elite-card`, `.dossier-container`) lack ARIA roles or landmark labels.
- The Obsidian Ember palette does better: `#E8734A` on `#0A0706` is approximately 5.2:1 — passes AA for normal text.
- No `alt` attributes are possible on `st.image()` calls in Streamlit Cloud without explicit parameter; must be checked.

### 5. Demo Flow Completeness — 5/10

The `streamlit_cloud/app.py` is a well-structured 1,016-line self-contained demo with 7 navigation sections and a bonus chatbot page. The demo flow, if accessible, is:

**Suggested "wow" path (3 minutes):**
Executive Dashboard -> Lead Intelligence -> Bot Orchestration -> Cache Performance

This path covers: business outcomes, lead scoring with real names/budgets, multi-bot handoff with Sankey diagram, and the 89% cost reduction proof point. These are the four strongest portfolio signals.

**Gaps that prevent a full "wow":**
- The demo is read-only. There is no interactive lead submission, no "type a message and watch qualification happen" on the main dashboard. The chatbot demo page (`/chatbot_demo`) has a live input widget, but it is a separate page not surfaced in the sidebar radio navigation — a reviewer clicking through the sidebar will never find it.
- The Circuit Breaker and AI Cost Tracking pages exist but require context to appreciate. A cold reviewer has no cue that these are architectural differentiators, not just charts.
- No guided tour / onboarding tooltip. The first page lacks a "Start here" prompt or a 2-sentence orientation of what they're looking at.

---

## P0 Fixes — Week 1

| # | Issue | Action | Owner | ETA |
|---|---|---|---|---|
| P0-E1 | Auth gate on `ct-enterprise-ai.streamlit.app` | Set Streamlit Cloud viewer setting to Public | Human (Cayman) | 5 min |
| P0-E2 | README demo badge links to auth-gated URL | After P0-E1 fix, verify badge works; until then, add parenthetical "(auth-gated; email for access)" | Human | 10 min |

---

## Wave 3: Demo Video Script Implications

The auth gate resolving (P0-E1) unblocks the ability to record a demo video without workarounds. Recommended screen capture flow:

**Scene 1 — Hook (0:00-0:15):** Open `ct-enterprise-ai.streamlit.app`. Show the Executive Dashboard loading with the 95% faster / $240K savings / 133% conversion stat block visible above the fold.

**Scene 2 — Lead scoring (0:15-0:40):** Click "Lead Intelligence." Hover over a lead card (Robert Chen, score 82, Hot). Expand the Scoring Breakdown and Signals panel. Narrate: "Each lead gets a Q0-Q4 qualification score in under 2 minutes — no agent time."

**Scene 3 — Handoff (0:40-1:05):** Click "Bot Orchestration." Show the Sankey diagram of Lead -> Buyer -> Seller flows. Point to the confidence thresholds in the Handoff Safeguards panel. Narrate: "The system prevents circular handoffs and defers transfers when a target bot is under load."

**Scene 4 — Cache ROI (1:05-1:25):** Click "Cache Performance." Show the 93K vs 7.8K token bar comparison. Narrate: "89% token cost reduction from the 3-tier cache. This is the cost model that makes the platform economically viable at scale."

**Scene 5 — Chatbot live (1:25-1:50):** Navigate to the Chatbot Demo page. Type "I'm looking to buy a house in Rancho Cucamonga, budget around $650K." Show the qualification scores updating in real time.

**Scene 6 — Close (1:50-2:00):** Return to Executive Dashboard. Show GitHub badge, test count badge. Narrate: "7,678 test functions, full observability stack, zero external dependencies in demo mode."

**Key requirement:** Record AFTER P0-E1 is fixed and AFTER the February screenshots are re-captured with Ember palette (see Wave 4).

---

## Wave 4: Design System Implications (Obsidian Ember)

The theme situation requires resolution before the design system can be called "coherent":

**Current state — two active palettes:**
- Obsidian Ember (new, March 2026): `#E8734A` primary, `#0A0706` background, `#1A1210` card. Defined in `theme_service.py` and `config.toml`.
- Obsidian Command v2.0 (old, pre-March): `#6366F1` elite-accent, `#00E5FF` neon, `#05070A` background. Defined in `obsidian_theme.py`.

**Required actions for Wave 4:**

1. **Retire `obsidian_theme.py`** or update it to Ember palette. The `inject_elite_css()` function still uses indigo as its primary. Any page calling it renders in the old palette. If the `ghl_real_estate_ai/streamlit_demo/` is ever deployed or recorded, it will clash with all Ember-palette assets.

2. **Re-capture five screenshots** in Ember palette: `jorge_dashboard_01.png`, `content-engine.png`, `design-system.png`, `market-pulse.png`, and the `Screenshot_*.jpg` batch. These are the most visually impressive (4K, full glassmorphism) but they show the wrong brand color.

3. **Inject Ember custom CSS into `streamlit_cloud/app.py`**: Currently the Cloud app renders using only `config.toml` theme — Streamlit's stock widget chrome with an orange accent. The glassmorphism card treatment, JetBrains Mono console blocks, and gradient metric widgets are absent. The demo looks functional but not premium. Extracting Ember-compatible CSS (replacing `#6366F1` with `#E8734A` throughout `obsidian_theme.py`) and injecting it into the Cloud app would materially upgrade the demo's visual impact.

4. **Accessibility token pass**: Audit `--text-secondary` (#8B949E) and `--text-muted` (#64748b) values against `#0A0706` background. Replace any failing pairs before the design system is declared production-ready.

5. **Mobile breakpoints**: The Cloud app uses `st.columns(4)` in multiple sections with no mobile override. Streamlit's responsive breakpoint is ~768px; a 4-column layout on mobile collapses incorrectly. Add `st.columns([1,1,1,1], gap="small")` and test at 375px width.

---

## Compounding Leverage — Screenshot Feed Matrix

| Asset | README hero | Blog header | Video thumbnail | LinkedIn card | OG preview |
|---|---|---|---|---|---|
| `banner.png` (1200x630, Ember) | Current (line 1) | Yes | Yes | Yes | Yes — correct OG size |
| `platform-overview.png` (1440x900, Ember) | Move to hero position | Yes | Crop 1200x630 | Yes | Needs crop |
| `jorge_dashboard_01.png` (3840x2160, OLD) | Do not use until re-captured | No | Needs Ember re-capture | No | No |
| Re-captured `jorge_dashboard_01.png` (Ember) | Strong candidate for hero | Best blog header | Best thumbnail | Yes | Crop needed |

**Recommendation:** After P0-E1 fix and demo is accessible, capture a live screenshot of the Executive Dashboard at 1440x900 in Obsidian Ember. This single screenshot would serve as README hero (replacing the generated graphic), blog header, video thumbnail, and LinkedIn card simultaneously. It takes one screenshot to update four surfaces.

---

## Summary Scores

| Dimension | Score | Blocker |
|---|---|---|
| Live demo accessibility | 1/10 | P0-E1: auth gate must be removed |
| README hero quality | 6/10 | Demo badge broken; banner is generated not real |
| Visual consistency | 4/10 | Two active palettes; 5 screenshots in wrong theme |
| Accessibility | 3/10 est. | CSS contrast, collapsed radio labels, no axe data |
| Demo flow completeness | 5/10 | Chatbot page hidden; no guided onboarding |
| **Overall** | **3.8/10** | **Auth gate is the single highest-leverage fix** |
