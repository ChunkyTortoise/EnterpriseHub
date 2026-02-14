# Freelance Automation Scripts - Quick Start Guide

**Purpose**: WS-6 Phase 1 automation scripts for Upwork job monitoring and CRM pipeline tracking.

**Time Savings**: Automates job discovery, deduplication, and pipeline management.

---

## Prerequisites

### Python Dependencies

```bash
# For Upwork Job Monitor
pip install feedparser

# CRM Tracker has no dependencies (uses stdlib only)
```

### Make Scripts Executable

```bash
cd /Users/cave/Documents/GitHub/EnterpriseHub
chmod +x scripts/upwork_job_monitor.py
chmod +x scripts/crm_tracker.py
```

---

## 1. Upwork Job Monitor

### Overview

Automatically monitors Upwork RSS feeds for matching jobs, filters by keywords, scores opportunities, and sends desktop notifications.

### Quick Start

```bash
# Run manually
./scripts/upwork_job_monitor.py

# Set up automatic monitoring (every 15 minutes)
crontab -e

# Add this line:
*/15 * * * * cd /Users/cave/Documents/GitHub/EnterpriseHub && python3 scripts/upwork_job_monitor.py >> ~/upwork_monitor.log 2>&1
```

### Configuration

Edit `scripts/upwork_job_monitor.py` to customize:

**Positive Keywords** (current):
- RAG, LLM, Claude, GPT, OpenAI
- Chatbot, FastAPI, multi-agent
- AI automation, Python, LangChain
- Vector database, embeddings, semantic search
- PostgreSQL, Redis, async, Streamlit

**Negative Keywords** (current):
- WordPress, Shopify, Wix
- $5/hr, $10/hr
- Data entry, blog writing, SEO content
- Virtual assistant, logo design

**Minimum Score**: 2 keyword matches required

### Output Files

```bash
# Seen job IDs (deduplication)
~/.upwork_seen_jobs.json

# New matching jobs log
jobs/new-jobs.md
```

### Example Output

```markdown
## Build RAG-based chatbot with FastAPI

**Posted:** 2026-02-14 15:30:00
**Score:** 5/10 (5 keyword matches)
**Budget:** Fixed price: $3,000-$5,000
**Link:** https://www.upwork.com/jobs/~abc123

**Matched Keywords:** rag, fastapi, chatbot, python, postgresql

**Description:**
```
Looking for an experienced Python developer to build a RAG-based
chatbot using FastAPI. Must have experience with vector databases,
embeddings, and LLM integration...
```

---
```

### Troubleshooting

**Issue**: `ModuleNotFoundError: No module named 'feedparser'`
```bash
pip install feedparser
```

**Issue**: No jobs found
- Check RSS URLs are accessible
- Verify internet connection
- Lower minimum score threshold (edit script)

**Issue**: Too many notifications
- Increase minimum score threshold
- Add more negative keywords
- Reduce cron frequency (e.g., every 30 minutes)

---

## 2. CRM Pipeline Tracker

### Overview

Lightweight CLI for managing freelance prospects through the sales pipeline from lead to won/lost.

### Quick Start

```bash
# Add new prospect
./scripts/crm_tracker.py add "Acme Corp" \
  --source=upwork \
  --rate=150 \
  --contact="John Doe" \
  --deal-size=5000

# Update status as you progress
./scripts/crm_tracker.py update "Acme Corp" --status=contacted
./scripts/crm_tracker.py update "Acme Corp" --status=proposal_sent
./scripts/crm_tracker.py update "Acme Corp" --status=negotiation
./scripts/crm_tracker.py update "Acme Corp" --status=won

# View pipeline
./scripts/crm_tracker.py pipeline

# Show stats
./scripts/crm_tracker.py stats

# List all prospects
./scripts/crm_tracker.py list

# Filter by status
./scripts/crm_tracker.py list --status=negotiation

# Export to CSV
./scripts/crm_tracker.py export --output=pipeline.csv
```

### Pipeline Stages

| Status | Description | Next Action |
|--------|-------------|-------------|
| `lead` | New prospect identified | Send initial outreach |
| `contacted` | Initial outreach sent | Wait for response |
| `proposal_sent` | Proposal submitted | Follow up in 3-5 days |
| `negotiation` | In active negotiation | Close or walk away |
| `won` | Deal closed successfully | Deliver project |
| `lost` | Deal lost or declined | Archive and learn |
| `inactive` | Prospect went cold | Re-engagement campaign |

### Data Storage

```bash
# Location
~/.freelance_crm.json

# Backup (recommended weekly)
cp ~/.freelance_crm.json ~/.freelance_crm_backup_$(date +%Y%m%d).json
```

### Example Workflow

```bash
# Monday: Review new Upwork jobs
./scripts/upwork_job_monitor.py
cat jobs/new-jobs.md

# Add promising leads to CRM
./scripts/crm_tracker.py add "TechCo" --source=upwork --rate=175 --deal-size=8000
./scripts/crm_tracker.py add "StartupXYZ" --source=linkedin --rate=150 --deal-size=6000

# Tuesday: Send proposals
./scripts/crm_tracker.py update "TechCo" --status=contacted
# (draft and send proposal)
./scripts/crm_tracker.py update "TechCo" --status=proposal_sent

# Friday: Check pipeline
./scripts/crm_tracker.py pipeline
./scripts/crm_tracker.py stats

# Weekly: Export for review
./scripts/crm_tracker.py export --output=pipeline_$(date +%Y%m%d).csv
```

### Troubleshooting

**Issue**: `ERROR: Prospect 'X' already exists`
- Prospect names must be unique
- Use update command instead of add
- Or use more specific company names

**Issue**: Lost data after system crash
- Regularly backup `~/.freelance_crm.json`
- Consider version control: `git add ~/.freelance_crm.json`

**Issue**: Export doesn't include all fields
- Export includes: company, status, source, rate, contact, deal_size, created, updated, notes
- Custom fields require code modification

---

## Integrated Workflow

### Daily Routine (15 minutes)

```bash
# 1. Check for new Upwork jobs (auto-runs via cron)
# Review desktop notifications

# 2. Review new jobs
cat jobs/new-jobs.md | tail -50

# 3. Add promising leads to CRM
./scripts/crm_tracker.py add "Company Name" --source=upwork --rate=XXX --deal-size=YYYY

# 4. Update existing prospects
./scripts/crm_tracker.py update "Company Name" --status=contacted
./scripts/crm_tracker.py update "Another Company" --status=proposal_sent

# 5. Check pipeline health
./scripts/crm_tracker.py pipeline
```

### Weekly Review (30 minutes)

```bash
# 1. Full pipeline review
./scripts/crm_tracker.py stats

# 2. List stale prospects
./scripts/crm_tracker.py list --status=contacted  # No response > 5 days?
./scripts/crm_tracker.py list --status=proposal_sent  # Follow up?

# 3. Update inactive prospects
./scripts/crm_tracker.py update "Stale Company" --status=inactive

# 4. Export for analysis
./scripts/crm_tracker.py export --output=weekly_review_$(date +%Y%m%d).csv

# 5. Backup data
cp ~/.freelance_crm.json ~/.freelance_crm_backup_$(date +%Y%m%d).json
```

### Monthly Analysis (1 hour)

```bash
# 1. Export all data
./scripts/crm_tracker.py export --output=monthly_$(date +%Y%m).csv

# 2. Review conversion rates
./scripts/crm_tracker.py stats

# 3. Analyze trends
# - Which sources perform best?
# - What's the average deal size by source?
# - What's the typical time from lead → won?

# 4. Optimize keywords
# - Review jobs/new-jobs.md for false positives
# - Add negative keywords to upwork_job_monitor.py
# - Adjust minimum score threshold

# 5. Clean up old data
# - Archive won/lost deals older than 90 days
# - Remove test data
```

---

## Advanced Usage

### Custom Cron Schedule

```bash
# Check every 30 minutes during work hours (8am-6pm)
*/30 8-18 * * * cd /Users/cave/Documents/GitHub/EnterpriseHub && python3 scripts/upwork_job_monitor.py

# Check every hour on weekends
0 * * * 0,6 cd /Users/cave/Documents/GitHub/EnterpriseHub && python3 scripts/upwork_job_monitor.py

# Check every 15 minutes, Monday-Friday only
*/15 * * * 1-5 cd /Users/cave/Documents/GitHub/EnterpriseHub && python3 scripts/upwork_job_monitor.py
```

### Adding Custom Fields to CRM

Edit `crm_tracker.py` and add fields to the `prospect` dict in `cmd_add()`:

```python
prospect = {
    'company': args.company,
    'source': args.source,
    'rate': args.rate,
    'contact': args.contact or '',
    'status': 'lead',
    'created': datetime.now().isoformat(),
    'updated': datetime.now().isoformat(),
    'notes': args.notes or '',
    'deal_size': args.deal_size or 0,

    # Add custom fields here
    'industry': args.industry or '',
    'referral_source': args.referral or '',
    'estimated_close_date': args.close_date or '',
}
```

Then update the argparse section to accept new arguments.

### Filtering Upwork by Category

Edit `UPWORK_RSS_URLS` in `upwork_job_monitor.py`:

```python
UPWORK_RSS_URLS = [
    # AI/ML - Machine Learning
    "https://www.upwork.com/ab/feed/jobs/rss?q=machine+learning&sort=recency&category2=Machine+Learning",

    # AI/ML - Natural Language Processing
    "https://www.upwork.com/ab/feed/jobs/rss?q=NLP+OR+natural+language&sort=recency",

    # Web Development - Python
    "https://www.upwork.com/ab/feed/jobs/rss?q=python+backend&sort=recency&category2=Web+Development",
]
```

---

## Tips & Best Practices

### Job Monitoring

1. **Start conservative**: Begin with a minimum score of 3-4 to reduce noise
2. **Refine keywords weekly**: Add negatives based on false positives
3. **Check notifications daily**: Best jobs get claimed within hours
4. **Review RSS feeds monthly**: Upwork changes category URLs periodically

### CRM Management

1. **Be consistent**: Update status immediately after each interaction
2. **Use deal_size**: Helps prioritize high-value opportunities
3. **Add notes**: `--notes "warm intro from Sarah"` for context
4. **Track sources**: Identify which channels perform best
5. **Follow up systematically**: contacted → 3 days → proposal_sent → 5 days → negotiation

### Data Hygiene

1. **Backup weekly**: CRM data is valuable, protect it
2. **Export monthly**: CSV exports enable deeper analysis in Excel/Google Sheets
3. **Archive old deals**: Move won/lost deals > 90 days to separate file
4. **Clean test data**: Remove any test entries before real usage

### Performance Optimization

1. **Cron logging**: Redirect output to log file for debugging
   ```bash
   */15 * * * * script.py >> ~/log.txt 2>&1
   ```

2. **Rate limiting**: Don't hammer Upwork RSS (15min is safe)

3. **Notification volume**: Adjust minimum score to avoid alert fatigue

---

## Metrics to Track

### Job Monitoring KPIs

- Jobs discovered per week
- Jobs scored 4+ per week (high quality)
- False positive rate (rejected / total)
- Time from job posted → proposal sent

### CRM Pipeline KPIs

- Lead → Won conversion rate
- Average deal size by source
- Time in each pipeline stage
- Monthly revenue from won deals
- Win/loss reasons (add to notes)

### Sample Analysis

```bash
# Conversion rate by source
./scripts/crm_tracker.py export --output=analysis.csv

# In Excel/Google Sheets:
# - Pivot: source vs status
# - Calculate: won / (won + lost) per source
# - Identify: best performing channels

# Average deal size by source
# - Pivot: source vs deal_size
# - Calculate: AVERAGE(deal_size) per source
# - Optimize: focus on high-value sources
```

---

## Next Steps

### Phase 1 (This Week)
- [x] Install dependencies (`pip install feedparser`)
- [ ] Configure Upwork job monitor keywords
- [ ] Set up cron job for automatic monitoring
- [ ] Add first 3-5 prospects to CRM
- [ ] Establish daily review routine

### Phase 2 (Next Week)
- [ ] Refine keyword filters based on results
- [ ] Build proposal template library
- [ ] Add custom CRM fields (industry, referral source)
- [ ] Create weekly export automation
- [ ] Integrate with email/calendar

### Phase 3 (Future)
- [ ] Build web dashboard for CRM
- [ ] Add email integration (send proposals from CLI)
- [ ] Integrate with GoHighLevel CRM
- [ ] Build analytics dashboard
- [ ] Add AI proposal generation

---

## Support

**Issues**: Report bugs at https://github.com/chunkytortoise/EnterpriseHub/issues

**Documentation**: This file + inline script comments

**Community**: Share tips and workflows in project discussions

---

**Version**: 1.0
**Created**: 2026-02-14
**Part of**: Freelance Acceleration Plan - WS-6 Phase 1
