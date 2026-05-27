# Demo Video Script: EnterpriseHub Hiring Showcase

**Target runtime:** 85-95 seconds
**Audience:** Technical hiring managers evaluating AI backend engineering work
**Tone:** Direct, first-person, honest. No hype.

---

## Recording Checklist (Do Before Pressing Record)

**Screen setup**
- Resolution: 1920 x 1080
- Terminal font size: 16pt minimum (18pt preferred)
- Browser zoom: 115% so UI elements are readable
- macOS Notification Center: turn on Do Not Disturb
- Close Slack, mail, and any apps that might pop up a notification

**Tabs and files to pre-load (in order)**
1. Browser tab 1: `https://ct-enterprise-ai.streamlit.app` (logged in as `demo_user` / `Demo1234!`)
2. Browser tab 2: `evals/judge.py` open in VS Code or terminal-based editor (scroll to the rubric definitions, line ~50)
3. Browser tab 3: `evals/golden_dataset.json` open (first 10-15 lines visible)
4. Terminal window: repo root, clean prompt, nothing running

**Mic check**
- Record 15 seconds of silence first, verify background noise level
- Speak at a measured pace. 90 seconds total means roughly 140-150 spoken words in voiceover

**Cursor**
- Use a cursor-highlighting app (e.g. Cursor Highlighter or Keystroke Pro) so mouse position is visible on a compressed video

---

## Storyboard and Voiceover

---

### Scene 1: Hook [0:00 - 0:15]

**Screen action:** Talking-head or static title card showing the repo name and GitHub URL. No code yet.

**Voiceover:**

> "I built an AI backend for real estate lead qualification. It ran in production for about three months, processed over 500 CRM leads, and the engagement ended. What you're watching is the artifact."

**Notes:** Past tense is intentional and honest. Do not say "it's currently running for a client."

---

### Scene 2: Live Demo [0:15 - 0:30]

**Screen action:** Switch to browser tab 1 (Streamlit dashboard at ct-enterprise-ai.streamlit.app). Slowly pan across the Executive Command Center screen showing lead pipeline state and bot status. Log in if needed, but pre-login is smoother.

**Voiceover:**

> "The live demo is running now at ct-enterprise-ai.streamlit.app. Three specialized bots handle lead intake, buyer qualification, and seller qualification. Each bot feeds a shared dashboard. This is synthetic demo data."

**Notes:** Explicitly call out "synthetic demo data" on screen or in voice. Do not imply this is a live client view.

---

### Scene 3: The Eval System [0:30 - 0:55]

**Screen action:** Switch to VS Code or terminal with `evals/judge.py` visible. Then briefly cut to `evals/golden_dataset.json` showing 2-3 test case objects. Then briefly show `.github/workflows/nightly-eval.yml` with the cron line visible.

**Voiceover:**

> "The strongest artifact is the eval system. Fifty hand-curated cases across seller qualification, buyer scheduling, lead intake, edge cases, and compliance scenarios. Each case runs through 4 LLM-as-judge rubrics plus deterministic property checks. A nightly cron compares results against a frozen baseline. If the score drops more than 10 percent, the regression alert path fires."

**Notes:** Do not say "eval harness" in the voiceover (say "eval system" or "the 50-case golden run"). "harness" is acceptable only in file names shown on screen.

---

### Scene 4: Test Count via make reviewer-smoke [0:55 - 1:15]

**Screen action:** Switch to terminal. Run `make reviewer-smoke`. Let output scroll. When it finishes, also show the line count from `python3 -m pytest --collect-only --override-ini='addopts=' -q | tail -3`.

**Voiceover:**

> "`make reviewer-smoke` runs lint, format check, compile check, the eval suite, health routes, webhook signature tests, orchestrator tests, and SQL-safety tests. The repo collects 7,665 tests locally. CI verifies over 1,100. The commands are in HIRING_REVIEW_GUIDE so any reviewer can reproduce this output in under five minutes."

**Notes:** Let the terminal output be legible. Pause briefly on the final summary lines. Do not speed-cut past the pass/fail counts.

---

### Scene 5: Honest Admission and Architecture Evidence [1:15 - 1:27]

**Screen action:** Switch to file browser showing `docs/adr/` directory with 10 ADR files visible. Keep it brief.

**Voiceover:**

> "The engagement ended. No live billing data, no client CRM export in the repo. What survived is 10 architecture decision records, a versioned prompt changelog with 31 entries, and 50 eval cases with a regression baseline. That is what eval-driven delivery produces."

**Notes:** This beat is the credibility anchor. Say it plainly without apology. Reviewers who care about honesty will note it positively.

---

### Scene 6: Close [1:27 - 1:30]

**Screen action:** Return to repo GitHub page or the README banner screenshot.

**Voiceover:**

> "Repo is at github.com/ChunkyTortoise/EnterpriseHub."

**Notes:** 3 seconds is enough. End clean.

---

## Runtime Breakdown

| Scene | Duration | Cumulative |
|-------|----------|------------|
| Scene 1: Hook | 15 s | 0:15 |
| Scene 2: Live demo | 15 s | 0:30 |
| Scene 3: Eval system | 25 s | 0:55 |
| Scene 4: make reviewer-smoke | 20 s | 1:15 |
| Scene 5: Honest admission | 12 s | 1:27 |
| Scene 6: Close | 3 s | 1:30 |

**Total runtime estimate: 88-92 seconds** (within the 85-95 target)

Voiceover word count: approximately 195 words at 140 wpm = 83 seconds of speech. Scene transitions and terminal wait time bring total to target range.

---

## Key Numbers to Mention (Do Not Improvise These)

| Fact | Source |
|------|--------|
| 7,665 tests collectible locally | `pytest --collect-only --override-ini='addopts=' -q`, May 23, 2026 |
| 1,100+ tests in CI | CI badge in README |
| 50 golden eval cases | `evals/golden_dataset.json` |
| 5 eval categories | seller qualification (15), buyer scheduling (10), lead intake (10), edge cases (10), compliance (5) |
| 4 LLM-as-judge rubrics | `evals/judge.py` |
| 7 compliance pipeline stages | `response_pipeline/factory.py` |
| 10 ADRs | `docs/adr/0001-0010` |
| 31 prompt changelog entries | `PROMPT_CHANGELOG.md` |
| 3 months production | CASE_STUDY.md, self-reported |
| 500+ leads processed | CASE_STUDY.md, operator-attested |
| 3 bot types | Lead, Buyer, Seller |

---

## What Not to Say

- Do not claim live cache-hit-rate measurements (the 88% figure is a synthetic benchmark target, not a measured result)
- Do not claim specific dollar savings (the 93K to 7.8K token figure is a projection)
- Do not call it "currently running" for a client
- Do not say the demo login uses real production data
