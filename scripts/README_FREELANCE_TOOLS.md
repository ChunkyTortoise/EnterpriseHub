# Freelance Acceleration Tools

**Purpose**: Python scripts for WS-6 Freelance Acceleration — proposal generation and market intelligence.

**Created**: 2026-02-14 (WS-6 Phase 2)

---

## Tools Overview

| Script | Purpose | Time Saved |
|--------|---------|------------|
| `proposal_generator.py` | Generate Upwork proposals with auto-scoring | 10-15 min → <5 min |
| `rate_intelligence.py` | Analyze market rates and positioning | Manual research → instant report |

---

## 1. Proposal Generator

### Quick Start

```bash
# Interactive mode (paste job description)
./scripts/proposal_generator.py

# Load from file
./scripts/proposal_generator.py --input job.txt

# Quick scoring only (no proposal)
./scripts/proposal_generator.py --score-only --input job.txt

# Override template selection
./scripts/proposal_generator.py --template rag --client-name "Sarah"
```

### Features

1. **Auto-Scoring (0-10 points)**
   - Budget alignment (0-3)
   - Client history (0-3)
   - Scope clarity (0-2)
   - Tech fit (0-2)
   - Red flags (-1 each)

2. **Priority Classification**
   - **P1 (8-10)**: Bid within 2 hours, heavy customization
   - **P2 (5-7)**: Batch for later, light customization
   - **Skip (<5)**: Not worth time investment

3. **Template Auto-Detection**
   - RAG (document search, embeddings, Q&A)
   - Chatbot (conversational AI, support bots)
   - Dashboard (analytics, BI, visualization)
   - API (backend, integration, webhooks)
   - Consulting (architecture, strategy, advisory)

4. **Output**
   - Saves to `proposals/draft-{type}-{timestamp}.md`
   - Copies to clipboard (macOS)
   - Marks [CUSTOMIZE] sections for manual review

### Examples

#### P1 Job (9/10)
```bash
$ cat job_rag.txt
Need document Q&A system for 5K+ legal contracts. OpenAI embeddings,
pgvector, FastAPI. $4K fixed-price. Payment verified, $25K spent, 4.8 stars.

$ ./scripts/proposal_generator.py --input job_rag.txt --client-name "Sarah"

=== JOB QUALIFICATION SCORE ===
Budget Alignment:  3/3 (fixed: $4,000)
Client History:    2/3
Scope Clarity:     2/2
Tech Fit:          2/2
Red Flags:         -0

TOTAL: 9/10
Priority: P1

✓ Bid within 2 hours. Research client, customize heavily.

Template: rag
Saved: proposals/draft-rag-20260214-152743.md
✓ Copied to clipboard
```

#### Skip Job (0/10)
```bash
$ cat job_bad.txt
Need AI expert. $30/hr. Test project. Need it this weekend.
No payment method. 15+ proposals already.

$ ./scripts/proposal_generator.py --score-only --input job_bad.txt

=== JOB QUALIFICATION SCORE ===
Budget Alignment:  0/3 (hourly: $30)
Client History:    1/3
Scope Clarity:     0/2
Tech Fit:          2/2
Red Flags:         -5
  Flags: No Payment, Low Spend, Test Project, Urgent, High Proposals

TOTAL: 0/10
Priority: Skip

✗ Skip. Not worth the time investment.
```

### Workflow

1. **Copy job description** from Upwork
2. **Paste into terminal** or save to file
3. **Review score** (use `--score-only` for quick triage)
4. **Generate proposal** for P1/P2 jobs
5. **Customize [CUSTOMIZE] sections** (2-5 minutes)
6. **Submit** within priority timeframe

---

## 2. Rate Intelligence

### Quick Start

```bash
# Analyze default rate ($85/hr)
./scripts/rate_intelligence.py

# Analyze specific rate
./scripts/rate_intelligence.py --rate 125

# JSON output for scripting
./scripts/rate_intelligence.py --rate 100 --json

# Skip web scraping (use fallback data)
./scripts/rate_intelligence.py --no-scrape
```

### Features

1. **Market Rate Benchmarks**
   - AI/ML Junior, Mid, Senior, Expert
   - Python Developer
   - RAG Specialist
   - Multi-Agent Systems
   - FastAPI, Chatbot, Dashboard Developer

2. **Percentile Positioning**
   - Calculate where your rate falls in each category
   - Color-coded indicators (🔴 Below / 🟡 Competitive / 🟢 Strong / 🔵 Expert)
   - Average percentile across all categories

3. **Recommendations**
   - Rate adjustment suggestions
   - Positioning strategy (mid-level vs senior vs expert)
   - Specialty emphasis (RAG, multi-agent)
   - Growth path (3-6-12 month plan)

4. **Output**
   - Terminal with color coding
   - Markdown report saved to `reports/rate-intelligence-{date}.md`
   - JSON format for automation

### Examples

#### $85/hr Analysis
```bash
$ ./scripts/rate_intelligence.py --rate 85 --no-scrape

=== RATE INTELLIGENCE ANALYSIS ===
Target Rate: $85/hr

Market Positioning:

🔵 AI/ML Junior              $ 40-$ 65/hr → 100.0th percentile
🟢 Python Developer          $ 50-$100/hr →  70.0th percentile
🟢 AI/ML Mid-Level           $ 65-$100/hr →  57.1th percentile
🟢 Dashboard Developer       $ 60-$110/hr →  50.0th percentile
🔴 FastAPI Developer         $ 75-$125/hr →  20.0th percentile
🔴 RAG Specialist            $100-$175/hr →   0.0th percentile

Overall: 30.5th percentile (Mid-Level)

Recommendations:
  Your rate ($85/hr) is competitive but below median for specialized work.
  You're positioned well for mid-level roles.
  Emphasize specialized skills (RAG, multi-agent) to justify $100+/hr rates.

✓ Report saved: reports/rate-intelligence-2026-02-14.md
```

#### $125/hr Analysis (JSON)
```bash
$ ./scripts/rate_intelligence.py --rate 125 --json --no-scrape | jq '.category, .average_percentile'

"Mid-Level"
65.8
```

### Use Cases

1. **Initial Rate Setting**
   - Analyze your proposed rate vs market
   - Determine if you're underpriced/overpriced
   - Find your experience level category

2. **Quarterly Rate Review**
   - Re-analyze every 3 months
   - Track market movement
   - Adjust rates based on portfolio growth

3. **Specialty Positioning**
   - See where RAG/multi-agent rates fall
   - Justify higher rates with specialization
   - Target specific rate bands

4. **Client Negotiation**
   - Show market data to justify rates
   - Demonstrate competitive positioning
   - Provide growth path

---

## Integration with Proposal System

Both tools integrate with the content in `content/upwork-proposal-system/`:

| File | Used By | Purpose |
|------|---------|---------|
| `QUALIFICATION_SCORECARD.md` | `proposal_generator.py` | Scoring logic, thresholds |
| `TEMPLATE_*.md` | `proposal_generator.py` | Base templates for proposals |
| `PROOF_POINTS.md` | Manual customization | Copy-paste proof points into [CUSTOMIZE] sections |
| `CTA_LIBRARY.md` | Manual customization | Choose call-to-action based on client type |

### Workflow Example

1. **Score job** with `proposal_generator.py --score-only`
2. **Generate proposal** for P1/P2 jobs
3. **Load PROOF_POINTS.md** and copy 2-3 relevant bullets
4. **Paste into [CUSTOMIZE] sections**
5. **Add CTA** from `CTA_LIBRARY.md`
6. **Submit proposal** (P1 within 2hr, P2 within 24hr)

---

## Rate Strategy Recommendations

Based on `rate_intelligence.py` analysis:

### Current Positioning ($85/hr)
- **Mid-level** for most AI/ML work
- **Competitive** for Python/dashboard work
- **Below market** for RAG/multi-agent specialization

### Recommended Strategy

| Timeline | Target Rate | Focus |
|----------|-------------|-------|
| **Q1 2026** | $85/hr | Build portfolio, P1 jobs, 5-10 case studies |
| **Q2 2026** | $95/hr | Raise rates as portfolio grows, emphasize RAG |
| **Q3 2026** | $100-110/hr | Target specialized work (RAG, multi-agent) |
| **Q4 2026** | $110-125/hr | Enterprise clients, consulting premium |

### Job-Specific Rates

| Job Type | Suggested Rate | Justification |
|----------|---------------|---------------|
| RAG Systems | $85-95/hr | Specialized, high-value |
| Chatbots | $80-90/hr | Multi-agent expertise |
| Dashboards | $75-85/hr | Standard BI work |
| APIs | $80-90/hr | FastAPI + async |
| Consulting | $100-125/hr | Architecture/strategy |

---

## Troubleshooting

### Proposal Generator

**Issue**: Template not found
```bash
Error: Template not found: /path/to/TEMPLATE_rag.md
```
**Solution**: Ensure `content/upwork-proposal-system/TEMPLATE_*.md` files exist.

**Issue**: Clipboard copy failed
```bash
! Could not copy to clipboard (pbcopy not available)
```
**Solution**: This is a macOS-only feature. Proposal is still saved to file.

### Rate Intelligence

**Issue**: Scraping failed
```bash
Scraping failed: HTTP Error 403: Forbidden
```
**Solution**: Use `--no-scrape` flag to use fallback data. Scraping may be blocked by Bonsai.

**Issue**: JSON output has headers
```bash
=== RATE INTELLIGENCE ANALYSIS ===
{...json...}
```
**Solution**: This was fixed in v2. If still present, redirect stderr: `2>/dev/null`

---

## Development Notes

### Proposal Generator Architecture
- **Scoring**: Regex-based pattern matching for budgets, red flags
- **Template Detection**: Keyword frequency analysis
- **Proposal Assembly**: String replacement with [CUSTOMIZE] markers
- **No external dependencies**: stdlib only (argparse, json, re, subprocess, datetime)

### Rate Intelligence Architecture
- **Scraping**: Best-effort urllib + html.parser (may fail)
- **Fallback Data**: Hardcoded market rates from research (Feb 2026)
- **Percentile Calc**: Linear interpolation within rate ranges
- **No external dependencies**: stdlib only

### Future Enhancements
- [ ] Support for other platforms (Fiverr, Toptal)
- [ ] LLM integration for proof point selection
- [ ] Historical rate tracking and trend analysis
- [ ] A/B testing on proposal templates
- [ ] Integration with Upwork API (auto-submit)

---

## Version History

**v1.0** (2026-02-14)
- Initial release
- Proposal scoring and generation
- Rate intelligence analysis
- Markdown and JSON output
- macOS clipboard support

---

**Last Updated**: 2026-02-14
**Author**: Cayman Roden
**License**: MIT
