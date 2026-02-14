# Revenue Sprint Automation Scripts

**Purpose**: Reduce revenue sprint execution time from **5h 25m** to **19m** (93% reduction) through automation of repetitive preparatory work.

**Time Savings**:
- Cold Outreach: 2h 20m → 7m (95% reduction)
- Streamlit Deployment: 35m → 2m (94% reduction)
- LinkedIn Automation: 1h 10m → 4.5m (94% reduction)
- Call Prep Validation: 15m → 1m 10s (92% reduction)
- Fiverr Formatting: 1h 5m → 4m (94% reduction)

---

## Quick Start

### Prerequisites

```bash
# Install Python dependencies
pip install requests pandas jinja2 pyyaml markdown beautifulsoup4

# Optional: Google Calendar integration
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

# Set API keys
export HUNTER_API_KEY="your_hunter_io_api_key"  # For email verification
export APOLLO_API_KEY="your_apollo_io_api_key"  # Alternative to Hunter
```

### Script Overview

| Script | Purpose | Time Savings | Priority |
|--------|---------|--------------|----------|
| `call_prep_check.sh` | Pre-call validation (tests, demos, env) | 15m → 1m 10s | P0 |
| `streamlit_deploy_helper.sh` | Deploy validation & portfolio updates | 35m → 2m | P1 |
| `outreach_helper.py` | Email verification, UTM, CRM setup | 2h 20m → 7m | P1 |
| `linkedin_helper.py` | Calendar events, connections, tracking | 1h 10m → 4.5m | P2 |
| `fiverr_formatter.py` | SEO tags, descriptions, FAQs | 1h 5m → 4m | P2 |
| `upwork_job_monitor.py` | Automated job alert monitoring | Manual → 15m intervals | P1 |
| `crm_tracker.py` | Freelance pipeline management | Manual → Real-time | P1 |

---

## Script Documentation

### 1. Call Prep Check (`call_prep_check.sh`)

**Purpose**: Validate environment before client calls (test count, demo URLs, environment variables).

**Usage**:
```bash
# Run all checks
./scripts/call_prep_check.sh

# Check specific component
./scripts/call_prep_check.sh --tests-only
./scripts/call_prep_check.sh --demos-only
./scripts/call_prep_check.sh --env-only

# Generate checklist
./scripts/call_prep_check.sh --output call_prep_status.md
```

**Example**:
```bash
$ ./scripts/call_prep_check.sh
======================================
   Call Prep Validation Check
======================================

1. Test Count
----------------------------------------
Checking test count... ✓ Found 322 tests (expected: 322)

2. Required Files
----------------------------------------
Checking required files... ✓ All required files present

3. Demo URLs
----------------------------------------
Checking demo URLs...
  Testing https://agentforge.streamlit.app... ✓ OK (1234ms)
  Testing https://promptlab.streamlit.app... ✓ OK (987ms)
  ...

4. Environment Variables
----------------------------------------
Checking environment variables...
  Checking ANTHROPIC_API_KEY... ✓ Set
  Checking DATABASE_URL... ✓ Set

======================================
✓ ALL CHECKS PASSED
======================================
```

**Integration with Beads**:
```bash
bd update EnterpriseHub-ouj9 --status=in_progress
./scripts/call_prep_check.sh --output call_prep_status.md
# → Human reviews KIALASH_CALL_PREP_ENHANCED.md (30 min)
bd close EnterpriseHub-ouj9
```

---

### 2. Streamlit Deployment Helper (`streamlit_deploy_helper.sh`)

**Purpose**: Automate pre-deployment validation, post-deployment health checks, and portfolio updates.

**Usage**:
```bash
# Pre-deployment validation
./scripts/streamlit_deploy_helper.sh validate

# Post-deployment verification
./scripts/streamlit_deploy_helper.sh verify --urls deployment_urls.txt

# Generate portfolio HTML
./scripts/streamlit_deploy_helper.sh portfolio --tests 322 --coverage 94

# Full workflow (interactive)
./scripts/streamlit_deploy_helper.sh run --apps "AgentForge,PromptLab,LLMStarter"
```

**Example Workflow**:
```bash
$ ./scripts/streamlit_deploy_helper.sh validate
======================================
   Pre-Deployment Validation
======================================

  Validating AgentForge... ✓
  Validating PromptLab... ✓
  Validating LLMStarter... ✓

✓ All repositories valid

Next step: Deploy manually via https://share.streamlit.io/

# After manual deployment, create deployment_urls.txt:
$ cat deployment_urls.txt
https://agentforge.streamlit.app
https://promptlab.streamlit.app
https://llmstarter.streamlit.app

$ ./scripts/streamlit_deploy_helper.sh verify --urls deployment_urls.txt
======================================
   Post-Deployment Verification
======================================

  Testing https://agentforge.streamlit.app... ✓ OK (1234ms)
  Testing https://promptlab.streamlit.app... ✓ OK (987ms)
  Testing https://llmstarter.streamlit.app... ✓ OK (1456ms)

✓ Results saved to: deployment_status.json
✓ All deployments healthy
```

**Integration with Beads**:
```bash
bd update EnterpriseHub-oom6 --status=in_progress
./scripts/streamlit_deploy_helper.sh validate
# → Human deploys via share.streamlit.io (15-20 min)
./scripts/streamlit_deploy_helper.sh verify --urls deployment_urls.txt
./scripts/streamlit_deploy_helper.sh portfolio --tests 322 --coverage 94
bd close EnterpriseHub-oom6
```

---

### 3. Outreach Helper (`outreach_helper.py`)

**Purpose**: Automate email verification, UTM tracking, and CRM setup for cold outreach.

**Usage**:
```bash
# Verify email addresses
python scripts/outreach_helper.py verify --file contacts.csv --api-key $HUNTER_API_KEY

# Generate UTM-tracked URLs
python scripts/outreach_helper.py utm --base-url https://cave-tortoise.site --campaign feb-2026-outreach

# Create CRM spreadsheet
python scripts/outreach_helper.py crm --contacts verified_contacts.csv --output outreach_crm.csv

# Generate follow-up schedule
python scripts/outreach_helper.py schedule --contacts verified_contacts.csv --sequence standard --output followup_schedule.csv
```

**Input Format** (`contacts.csv`):
```csv
name,email,company,title,linkedin,category,priority,notes
John Doe,john@example.com,Acme Corp,CTO,https://linkedin.com/in/johndoe,AI Startup,P1,Met at conference
Jane Smith,jane@techco.com,TechCo,VP Engineering,https://linkedin.com/in/janesmith,Enterprise SaaS,P1,Warm intro from Sarah
```

**Example**:
```bash
$ python scripts/outreach_helper.py verify --file contacts.csv --api-key $HUNTER_API_KEY
Verifying 1/30: john@example.com... ✓ Valid (confidence: 0.95)
Verifying 2/30: jane@techco.com... ✓ Valid (confidence: 0.92)
Verifying 3/30: invalid@fake-ontario_mills-xyz.com... ✗ Invalid
...

✓ Results saved to: contacts_verified.csv
Valid: 28/30

$ python scripts/outreach_helper.py utm --base-url https://cave-tortoise.site --campaign feb-2026-outreach
✓ Generated: email -> https://cave-tortoise.site?utm_source=email&utm_medium=referral&utm_campaign=feb-2026-outreach
✓ Generated: linkedin -> https://cave-tortoise.site?utm_source=linkedin&utm_medium=referral&utm_campaign=feb-2026-outreach
...

✓ URLs saved to: utm_urls_feb-2026-outreach.json

$ python scripts/outreach_helper.py crm --contacts contacts_verified.csv --output outreach_crm.csv
✓ CRM spreadsheet created: outreach_crm.csv (28 contacts)

$ python scripts/outreach_helper.py schedule --contacts contacts_verified.csv --sequence standard --output followup_schedule.csv
✓ Follow-up schedule created: followup_schedule.csv (84 emails)
```

**Integration with Beads**:
```bash
bd update EnterpriseHub-nevv --status=in_progress
python scripts/outreach_helper.py verify --file contacts.csv
python scripts/outreach_helper.py utm --campaign feb-2026-outreach
python scripts/outreach_helper.py crm --contacts verified_contacts.csv --output outreach_crm.csv
python scripts/outreach_helper.py schedule --contacts verified_contacts.csv --output followup_schedule.csv
# → Human reviews personalization + sends emails (1 hour)
bd close EnterpriseHub-nevv
```

---

### 4. LinkedIn Helper (`linkedin_helper.py`)

**Purpose**: Automate calendar events, connection requests, and engagement tracking for LinkedIn.

**Usage**:
```bash
# Create calendar events from YAML
python scripts/linkedin_helper.py calendar --posts posts_week2.yaml --calendar "Work Calendar"

# Generate connection requests
python scripts/linkedin_helper.py requests --targets targets.csv --output connection_requests.csv

# Track post engagement
python scripts/linkedin_helper.py track --create --output engagement_tracker.csv
python scripts/linkedin_helper.py track \
  --post-date 2026-02-17 \
  --post-title "Building Multi-Agent AI Systems" \
  --post-url "https://linkedin.com/posts/..." \
  --impressions 1250 \
  --likes 34 \
  --comments 8 \
  --shares 5 \
  --output engagement_tracker.csv
```

**Input Format** (`posts_week2.yaml`):
```yaml
posts:
  - title: "Building Multi-Agent AI Systems"
    date: "2026-02-17 08:30"
    content: |
      Just shipped a multi-agent orchestration system that reduced
      client acquisition costs by 40%. Here's what I learned...

  - title: "Real Estate Tech Revolution"
    date: "2026-02-19 08:30"
    content: |
      Real estate is being transformed by AI. Here are 3 trends
      every agent should know...
```

**Input Format** (`targets.csv`):
```csv
name,company,linkedin,hook
John Doe,Acme Corp,https://linkedin.com/in/johndoe,saw your recent post on AI agents
Jane Smith,TechCo,https://linkedin.com/in/janesmith,impressed by your work on ML pipelines
```

**Example**:
```bash
$ python scripts/linkedin_helper.py calendar --posts posts_week2.yaml --calendar "Work Calendar"
✓ Created calendar event: https://calendar.google.com/event?eid=...
✓ Created calendar event: https://calendar.google.com/event?eid=...

✓ Created 2 calendar events

$ python scripts/linkedin_helper.py requests --targets targets.csv --output connection_requests.csv
✓ John Doe: Hi John, saw your recent post on AI agents. Would love to connect! (78 chars)
✓ Jane Smith: Hi Jane, impressed by your work on ML pipelines. Would love to connect! (85 chars)
...

✓ Generated 10 connection requests
✓ Saved to: connection_requests.csv
```

**Integration with Beads**:
```bash
bd update EnterpriseHub-jrgy --status=in_progress
python scripts/linkedin_helper.py calendar --posts posts_week2.yaml
python scripts/linkedin_helper.py requests --targets targets.csv --output connection_requests.csv
# → Human executes social engagement (ongoing)
bd close EnterpriseHub-jrgy
```

---

### 5. Fiverr Formatter (`fiverr_formatter.py`)

**Purpose**: Automate SEO tag generation, description formatting, and FAQ creation for Fiverr gigs.

**Usage**:
```bash
# Generate SEO tags
python scripts/fiverr_formatter.py tags --gig-type "AI Chatbot" --max 5

# Format gig description
python scripts/fiverr_formatter.py format --input content/fiverr/gig1-rag-qa-system.md --max-chars 1200

# Generate FAQs
python scripts/fiverr_formatter.py faq --gig-type "RAG Q&A System" --count 5 --output faqs.json

# Full workflow (process all gigs)
python scripts/fiverr_formatter.py build --gigs "content/fiverr/*.md" --output-dir fiverr_formatted
```

**Example**:
```bash
$ python scripts/fiverr_formatter.py tags --gig-type "AI Chatbot" --max 5
✓ Generated 5 SEO tags for 'AI Chatbot':
  1. ai chatbot (50,000 monthly searches)
  2. chatbot development (25,000 monthly searches)
  3. chatgpt integration (30,000 monthly searches)
  4. custom chatbot (20,000 monthly searches)
  5. conversational ai (18,000 monthly searches)

$ python scripts/fiverr_formatter.py format --input content/fiverr/gig1-rag-qa-system.md --max-chars 1200
✓ Description formatted: 1198 chars (within limit)

Structure validation:
  ✓ hook
  ✓ problem
  ✓ solution
  ✓ cta

✓ Saved to: content/fiverr/gig1-rag-qa-system_formatted.txt

$ python scripts/fiverr_formatter.py build --gigs "content/fiverr/*.md" --output-dir fiverr_formatted
Found 3 gig files

==================================================
Processing: gig1-rag-qa-system
==================================================

1. SEO Tags
--------------------------------------------------
✓ Generated 5 SEO tags for 'Rag Qa System'
  ...

2. Description
--------------------------------------------------
✓ Description formatted: 1198 chars (within limit)

3. FAQs
--------------------------------------------------
✓ Generated 5 FAQs for 'Rag Qa System'
  ...

✓ Saved to: fiverr_formatted/gig1-rag-qa-system

==================================================
✓ Processed 3 gigs
✓ Output directory: fiverr_formatted
==================================================
```

**Integration with Beads**:
```bash
bd update EnterpriseHub-c974 --status=in_progress
python scripts/fiverr_formatter.py build --gigs "content/fiverr/*.md" --output-dir fiverr_formatted
# → Human uploads photo (5 min) + lists gigs (25 min)
bd close EnterpriseHub-c974
```

---

## API Setup

### Hunter.io (Email Verification)

1. Sign up: https://hunter.io/
2. Free tier: 25 verifications/month
3. Paid tier: $49/month for 500 verifications
4. Set API key: `export HUNTER_API_KEY="your_key"`

### Apollo.io (Alternative Email Verification)

1. Sign up: https://www.apollo.io/
2. Free tier: 50 verifications/month
3. Paid tier: $49/month for 1,000 verifications
4. Set API key: `export APOLLO_API_KEY="your_key"`

### Google Calendar API (Optional)

1. Go to https://console.cloud.google.com/
2. Create project: "Revenue Sprint Automation"
3. Enable APIs: Calendar API, Gmail API, Google Sheets API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `credentials.json` to `~/.config/revenue-sprint/credentials.json`
6. First run will open browser for OAuth consent → generates `token.json`

---

## Troubleshooting

### Call Prep Check

**Issue**: Test count mismatch
```bash
# Check pytest collection
pytest --co -q | grep "^tests/" | wc -l

# Check markers
pytest --markers

# Verify test files
find . -name "test_*.py" -o -name "*_test.py"
```

**Issue**: Demo URLs failing
```bash
# Test URL manually
curl -I https://agentforge.streamlit.app

# Check DNS
dig agentforge.streamlit.app

# Verify SSL
openssl s_client -connect agentforge.streamlit.app:443
```

### Outreach Helper

**Issue**: Email verification failing
```bash
# Test API key
curl "https://api.hunter.io/v2/account?api_key=$HUNTER_API_KEY"

# Check quota
curl "https://api.hunter.io/v2/account?api_key=$HUNTER_API_KEY" | jq '.data.calls.available'

# Fallback to regex validation (no API)
python scripts/outreach_helper.py verify --file contacts.csv  # Uses regex if no API key
```

### LinkedIn Helper

**Issue**: Google Calendar API not working
```bash
# Check credentials
ls -la ~/.config/revenue-sprint/credentials.json

# Re-authenticate
rm ~/.config/revenue-sprint/token.json
python scripts/linkedin_helper.py calendar --posts posts.yaml  # Will trigger OAuth flow

# Fallback: Calendar events will print to console if API unavailable
```

---

## Best Practices

### Email Verification
- Verify email addresses in batches of 25-50 to stay within API quotas
- Use regex validation as fallback when API quotas exhausted
- Always review verification results before sending emails

### UTM Tracking
- Use consistent campaign names: `{month}-{year}-{channel}` (e.g., `feb-2026-outreach`)
- Track all links (email signatures, portfolio, social profiles)
- Review UTM data in Google Analytics weekly

### CRM Management
- Update CRM spreadsheet after each interaction
- Set follow-up reminders immediately
- Track response rates by category/template

### LinkedIn Engagement
- Post at consistent times (8:30am PT for tech audience)
- Respond to comments within 1 hour for maximum engagement
- Track engagement metrics weekly to optimize content

### Fiverr SEO
- Use all 5 tag slots with high-volume keywords
- Update descriptions quarterly based on search trends
- Monitor competitor gigs for pricing and positioning

---

## Freelance Automation Tools

### 6. Upwork Job Monitor (`upwork_job_monitor.py`)

**Purpose**: Automated monitoring of Upwork RSS feeds for matching freelance opportunities.

**Features**:
- Parses Upwork RSS feeds for AI/ML jobs
- Keyword filtering (positive + negative)
- Job scoring based on keyword match count
- Deduplication using persistent storage
- macOS desktop notifications
- Appends new jobs to `jobs/new-jobs.md`

**Setup**:
```bash
# Install dependency
pip install feedparser

# Make executable
chmod +x scripts/upwork_job_monitor.py

# Run manually
./scripts/upwork_job_monitor.py

# Add to crontab for automatic monitoring (every 15 minutes)
*/15 * * * * cd /Users/cave/Documents/GitHub/EnterpriseHub && python3 scripts/upwork_job_monitor.py
```

**Configuration**:
- **Positive keywords**: RAG, LLM, Claude, GPT, chatbot, FastAPI, multi-agent, AI automation, Python
- **Negative keywords**: WordPress, Shopify, $5/hr, data entry, blog writing
- **Minimum score**: 2 keyword matches
- **Storage**: `~/.upwork_seen_jobs.json`
- **Output**: `jobs/new-jobs.md`

**Example Output**:
```bash
$ ./scripts/upwork_job_monitor.py
[2026-02-14 15:00:00] Upwork Job Monitor started
Monitoring 4 RSS feeds...

NEW JOB: Build RAG-based chatbot with FastAPI (score: 5)
NEW JOB: Multi-agent AI automation system (score: 4)
REJECTED: WordPress blog setup (reason: wordpress)
LOW SCORE: Data entry task (score: 1)

Found 2 new matching jobs!

✓ Logged 2 jobs to jobs/new-jobs.md
✓ Desktop notification sent for top job

Top job: Build RAG-based chatbot with FastAPI (score: 5)
Link: https://www.upwork.com/jobs/~...
```

---

### 7. CRM Pipeline Tracker (`crm_tracker.py`)

**Purpose**: Lightweight CLI for tracking freelance prospects and pipeline.

**Features**:
- Add/update prospects with contact info
- Track pipeline status (lead → won/lost)
- Funnel visualization with colorized output
- Conversion rate analytics
- CSV export
- No external dependencies (stdlib only)

**Setup**:
```bash
# Make executable
chmod +x scripts/crm_tracker.py

# View help
./scripts/crm_tracker.py --help
```

**Commands**:

```bash
# Add prospect
./scripts/crm_tracker.py add "Acme Corp" \
  --source=upwork \
  --rate=150 \
  --contact="John Doe" \
  --deal-size=5000

# Update status
./scripts/crm_tracker.py update "Acme Corp" --status=proposal_sent

# View pipeline funnel
./scripts/crm_tracker.py pipeline

# Show conversion stats
./scripts/crm_tracker.py stats

# List prospects (with optional filtering)
./scripts/crm_tracker.py list --status=negotiation
./scripts/crm_tracker.py list --source=upwork

# Export to CSV
./scripts/crm_tracker.py export --output=pipeline.csv
```

**Pipeline Statuses**:
- `lead` - New prospect identified
- `contacted` - Initial outreach sent
- `proposal_sent` - Proposal submitted
- `negotiation` - In active negotiation
- `won` - Deal closed successfully
- `lost` - Deal lost to competitor or declined
- `inactive` - Prospect went cold

**Example Workflow**:
```bash
# Add new prospect from Upwork
./scripts/crm_tracker.py add "TechCo" --source=upwork --rate=175 --contact="Jane Smith" --deal-size=8000

# Update as you progress
./scripts/crm_tracker.py update "TechCo" --status=contacted
./scripts/crm_tracker.py update "TechCo" --status=proposal_sent
./scripts/crm_tracker.py update "TechCo" --status=negotiation --deal-size=12000  # Updated deal size
./scripts/crm_tracker.py update "TechCo" --status=won

# Check pipeline
./scripts/crm_tracker.py pipeline
```

**Example Output**:
```bash
$ ./scripts/crm_tracker.py pipeline

FREELANCE PIPELINE

Total Prospects: 15
Pipeline Value: $87,500

Lead            ████████████  8 ( 32,000 USD)
Contacted       ████████      4 ( 18,000 USD)
Proposal Sent   ████          2 ( 15,000 USD)
Negotiation     ██            1 ( 12,000 USD)
Won             ██████        3 ( 35,500 USD)
Lost            ██            2 (  8,000 USD)

Conversion Rate: 60.0%
```

**Storage**:
- Location: `~/.freelance_crm.json`
- Format: JSON with metadata
- Backup recommended before major updates

**Integration with Upwork Monitor**:
```bash
# Monitor new jobs
./scripts/upwork_job_monitor.py

# Review jobs/new-jobs.md and add promising leads
./scripts/crm_tracker.py add "Acme Corp" --source=upwork --rate=150

# Track progress through pipeline
./scripts/crm_tracker.py update "Acme Corp" --status=contacted
```

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review script source code (all scripts have inline documentation)
3. Check API provider documentation (Hunter.io, Google Calendar)
4. File issue: https://github.com/chunkytortoise/EnterpriseHub/issues

---

**Version**: 1.0
**Last Updated**: February 9, 2026
**Maintainer**: EnterpriseHub Team
