# Multi-Tenant Partner Onboarding Guide

**GHL Real Estate AI - Agency Multi-Tenancy System**

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Step-by-Step Onboarding](#step-by-step-onboarding)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Topics](#advanced-topics)
7. [FAQ](#faq)

---

## Overview

The GHL Real Estate AI system supports **multi-tenancy**, allowing your agency to onboard multiple real estate partners/sub-accounts. Each partner operates in complete isolation with:

- **Dedicated API credentials** (Anthropic + GHL)
- **Separate billing** (each partner is charged on their own account)
- **Isolated knowledge bases** and conversation history
- **Optional calendar integration** for appointment scheduling

### Architecture

```
Agency (Your Organization)
├── Partner A (Location ID: loc_001)
│   ├── Anthropic API Key: sk-ant-partner-a-...
│   ├── GHL API Key: ghl-partner-a-...
│   └── Calendar: cal_partner_a_primary
├── Partner B (Location ID: loc_002)
│   ├── Anthropic API Key: sk-ant-partner-b-...
│   ├── GHL API Key: ghl-partner-b-...
│   └── Calendar: (not configured)
└── Partner C (Location ID: loc_003)
    └── (Uses Agency Master Key)
```

---

## Prerequisites

Before onboarding a new partner, ensure you have:

1. **Partner's GHL Location ID**
   - Found in GHL dashboard under Settings > Business Profile
   - Format: Usually alphanumeric (e.g., `abc123xyz`)

2. **Partner's Anthropic API Key** (recommended)
   - Created at: https://console.anthropic.com/
   - Format: `sk-ant-api03-...` or `sk-ant-sid01-...`
   - Partner must create this under their own billing account

3. **Partner's GHL API Key or OAuth Token**
   - Created in GHL under Settings > API Keys
   - Format: Long alphanumeric string or JWT token

4. **(Optional) Partner's GHL Calendar ID**
   - For appointment booking integration
   - Found in GHL Calendar settings

---

## Quick Start

### Basic Onboarding (3 Minutes)

```bash
# Navigate to project root
cd /path/to/ghl-real-estate-ai

# Activate virtual environment (if using one)
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate     # Windows

# Run onboarding tool
python scripts/onboard_partner.py
```

Follow the interactive prompts:

1. Enter **Partner Name** (e.g., "Acme Real Estate")
2. Enter **GHL Location ID** (e.g., "loc_acme_001")
3. Enter **Anthropic API Key** (starts with `sk-ant-`)
4. Enter **GHL API Key**
5. Enter **Calendar ID** (optional - press Enter to skip)
6. Confirm and save

**Done!** Your partner is now registered.

---

## Step-by-Step Onboarding

### Step 1: Gather Partner Information

**Before starting**, collect the following from your partner:

| Field | Example | Required | Where to Find |
|-------|---------|----------|---------------|
| Partner Name | "Acme Real Estate" | Yes | Business name |
| Location ID | `loc_acme_001` | Yes | GHL Dashboard > Settings > Business Profile |
| Anthropic API Key | `sk-ant-api03-abc123...` | Yes | https://console.anthropic.com/ |
| GHL API Key | `ghl-api-key-xyz789...` | Yes | GHL Dashboard > Settings > API Keys |
| Calendar ID | `cal_acme_primary` | No | GHL Calendar Settings |

### Step 2: Run Onboarding Tool

```bash
python scripts/onboard_partner.py
```

You'll see:

```
======================================================================
  GHL Real Estate AI - Partner Onboarding System
======================================================================

This tool will register a new real estate partner/tenant.
Each partner gets their own API credentials and isolated system.

Step 1: Partner Information
Enter Partner/Tenant Name (e.g., 'Acme Real Estate'): _
```

### Step 3: Input Validation

The tool validates all inputs in real-time:

- **Partner Name**: Minimum 3 characters
- **Location ID**: Minimum 5 characters, checks for duplicates
- **Anthropic Key**: Must start with `sk-ant-` and be 20+ characters
- **GHL Key**: Minimum 10 characters
- **Calendar ID**: Optional (can be empty)

**Example validation failure:**

```
✗ Invalid Anthropic API key. Must start with 'sk-ant-' and be at least 20 characters.

Enter Anthropic API Key (starts with 'sk-ant-'): _
```

### Step 4: Duplicate Detection

If a tenant with the same Location ID already exists:

```
✗ A tenant with Location ID 'loc_acme_001' already exists!

⚠ Please use a different Location ID or update the existing tenant manually.
Try a different Location ID? (y/n): _
```

### Step 5: Review and Confirm

Before saving, you'll see a summary:

```
Summary:
  Partner Name:     Acme Real Estate
  Location ID:      loc_acme_001
  Anthropic Key:    **********abc123
  GHL Key:          **********xyz789
  Calendar ID:      cal_acme_primary

Confirm registration? (y/n): _
```

### Step 6: Completion

On success:

```
✓ Registration Complete!

Partner 'Acme Real Estate' has been successfully onboarded.
Configuration saved to: data/tenants/loc_acme_001.json

Next Steps:
  1. Share the Location ID with the partner: loc_acme_001
  2. Configure their GHL webhook to point to your bot
  3. Test the integration with a sample message
```

---

## Troubleshooting

### Common Issues

#### Issue 1: "Invalid Anthropic API key"

**Symptom:**
```
✗ Invalid Anthropic API key. Must start with 'sk-ant-' and be at least 20 characters.
```

**Solutions:**
- Verify key starts with `sk-ant-` (case-sensitive)
- Check for extra spaces before/after the key
- Ensure using a valid production key (not expired)
- Confirm partner created key at https://console.anthropic.com/

#### Issue 2: "Tenant already exists"

**Symptom:**
```
✗ A tenant with Location ID 'loc_abc_123' already exists!
```

**Solutions:**
- **Option A**: Use a different Location ID
- **Option B**: Update existing tenant manually:
  ```bash
  # Edit existing file
  nano data/tenants/loc_abc_123.json
  ```
- **Option C**: Delete old tenant and re-register:
  ```bash
  rm data/tenants/loc_abc_123.json
  python scripts/onboard_partner.py
  ```

#### Issue 3: "Failed to save configuration"

**Symptom:**
```
✗ Failed to save configuration: [Errno 13] Permission denied
```

**Solutions:**
- Check file permissions on `data/tenants/` directory
- Ensure you have write access:
  ```bash
  chmod -R 755 data/tenants/
  ```
- Verify disk space is available:
  ```bash
  df -h
  ```

#### Issue 4: Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'services.tenant_service'
```

**Solutions:**
- Ensure you're running from project root:
  ```bash
  pwd  # Should show /path/to/ghl-real-estate-ai
  ```
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- Activate virtual environment if using one

#### Issue 5: Calendar ID Not Working

**Symptom:**
Appointments not being scheduled despite calendar ID being configured.

**Solutions:**
- Verify Calendar ID in GHL dashboard
- Check calendar permissions (must allow API access)
- Test manually with GHL API:
  ```bash
  curl -X GET "https://rest.gohighlevel.com/v1/calendars/{calendar_id}" \
       -H "Authorization: Bearer YOUR_GHL_API_KEY"
  ```

---

## Advanced Topics

### Manual Tenant Registration

If you prefer command-line arguments over interactive mode, use the legacy tool:

```bash
python scripts/register_tenant.py \
  --location_id "loc_manual_001" \
  --anthropic_key "sk-ant-api03-xyz123..." \
  --ghl_key "ghl-api-key-abc789..."
```

### Bulk Onboarding

For onboarding multiple partners at once, create a CSV file:

**partners.csv:**
```csv
partner_name,location_id,anthropic_key,ghl_key,calendar_id
Acme Realty,loc_acme_001,sk-ant-...,ghl-key-...,cal_acme
Smith & Co,loc_smith_002,sk-ant-...,ghl-key-...,
Sunset RE,loc_sunset_003,sk-ant-...,ghl-key-...,cal_sunset
```

**Bulk import script:**
```python
import csv
import asyncio
from services.tenant_service import TenantService

async def bulk_import(csv_file):
    service = TenantService()
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            await service.save_tenant_config(
                location_id=row['location_id'],
                anthropic_api_key=row['anthropic_key'],
                ghl_api_key=row['ghl_key'],
                ghl_calendar_id=row.get('calendar_id') or None
            )
            print(f"✓ Registered {row['partner_name']}")

asyncio.run(bulk_import('partners.csv'))
```

### Updating Existing Tenants

To update an existing tenant's configuration:

```bash
# 1. Find existing file
ls data/tenants/

# 2. Edit JSON directly
nano data/tenants/loc_abc_123.json

# 3. Update fields as needed
{
  "location_id": "loc_abc_123",
  "anthropic_api_key": "sk-ant-NEW-KEY",
  "ghl_api_key": "ghl-NEW-KEY",
  "ghl_calendar_id": "cal_NEW_ID",
  "updated_at": "2026-01-04T12:00:00Z"
}

# 4. Save and exit (Ctrl+O, Enter, Ctrl+X)
```

### Tenant Configuration File Structure

Each tenant is stored as a JSON file in `data/tenants/{location_id}.json`:

```json
{
  "location_id": "loc_acme_001",
  "anthropic_api_key": "sk-ant-api03-abc123xyz...",
  "ghl_api_key": "ghl-api-key-xyz789abc...",
  "ghl_calendar_id": "cal_acme_primary",
  "updated_at": "2026-01-04T10:30:00.123456"
}
```

**Security Note:** These files contain sensitive API keys. Ensure:
- Files have restricted permissions (`chmod 600`)
- Directory is excluded from version control (`.gitignore`)
- Backups are encrypted

### Agency Master Key Fallback

If a tenant doesn't have dedicated credentials, the system falls back to the **Agency Master Key** configured in `.env`:

```bash
# .env file
GHL_AGENCY_API_KEY=your-agency-master-key
```

This allows partners to start using the system immediately while they prepare their own API keys.

---

## FAQ

### Q1: Do partners need their own Anthropic account?

**A: Yes (recommended).** Each partner should create their own Anthropic account at https://console.anthropic.com/ and provide you with an API key. This ensures:
- They're billed directly for their AI usage
- You're not responsible for their overage costs
- They can monitor their own usage

**Alternative:** You can use your agency's Anthropic key initially, but switch to partner-specific keys before going to production.

---

### Q2: What if a partner doesn't have an Anthropic API key?

**A: Two options:**

1. **Use Agency Master Key** (temporary)
   - Set `GHL_AGENCY_API_KEY` in `.env`
   - System auto-falls back to this for unregistered tenants
   - **Downside:** You're billed for their usage

2. **Help them create one** (recommended)
   - Guide: https://console.anthropic.com/
   - Create account → Billing → Generate API Key
   - Takes 2-3 minutes

---

### Q3: Can I change a tenant's API keys later?

**A: Yes.** Edit the JSON file directly:

```bash
nano data/tenants/{location_id}.json
# Update keys
# Save and exit
```

Or delete and re-register:

```bash
rm data/tenants/{location_id}.json
python scripts/onboard_partner.py
```

---

### Q4: How do I delete a tenant?

**A: Delete the tenant file:**

```bash
rm data/tenants/{location_id}.json
```

**Note:** This doesn't delete their conversation history or knowledge base. For complete removal:

```bash
# Delete tenant config
rm data/tenants/{location_id}.json

# Delete knowledge base
rm -rf data/knowledge_base/{location_id}/

# Delete embeddings
rm -rf data/embeddings/{location_id}/

# Clear conversation memory (Redis)
redis-cli DEL "conversation:{location_id}:*"
```

---

### Q5: What's the difference between Location ID and Partner Name?

- **Location ID**: Technical identifier used by GHL and our system. Must be unique. Used in file names and API calls.
- **Partner Name**: Human-readable label for your reference. Can be anything (e.g., "Acme Real Estate"). Only stored in logs.

---

### Q6: Do I need a Calendar ID for every partner?

**A: No, it's optional.** Calendar ID is only required if you want to enable:
- Appointment booking via AI conversation
- Automatic scheduling integration

Partners can still use the AI bot without calendar integration.

---

### Q7: How many partners can I onboard?

**A: Unlimited.** The system is designed to scale horizontally. Each partner is isolated, so onboarding 10 or 1,000 partners has the same process.

**Performance note:** Beyond 100+ partners, consider:
- Redis for caching
- PostgreSQL for metadata
- Load balancing for webhook endpoints

---

### Q8: Can partners share the same GHL Location ID?

**A: No.** Each partner must have a unique Location ID. This ensures complete isolation and prevents data leakage.

---

### Q9: What happens if a partner's API key expires?

**A: The bot will fail for that partner.** You'll see errors in logs:

```
ERROR: Anthropic API request failed for location loc_abc_123: Invalid API key
```

**Fix:**
1. Contact partner for new API key
2. Update tenant file:
   ```bash
   nano data/tenants/loc_abc_123.json
   # Update anthropic_api_key
   ```
3. Restart bot (if needed)

---

### Q10: Can I test the onboarding without real API keys?

**A: Yes, for testing:**

```bash
# Use dummy keys
Partner Name: Test Partner
Location ID: test_loc_001
Anthropic Key: sk-ant-api03-test-dummy-key-123456789
GHL Key: ghl-test-key-dummy-123456789
Calendar ID: (leave empty)
```

This will create the tenant file, but API calls will fail. Use this for:
- Testing the onboarding flow
- Training staff
- Validating file creation

---

## Support

For issues not covered in this guide:

1. **Check logs:**
   ```bash
   tail -f logs/bot.log
   ```

2. **Verify tenant file exists:**
   ```bash
   cat data/tenants/{location_id}.json
   ```

3. **Test API keys manually:**
   ```bash
   # Test Anthropic
   curl https://api.anthropic.com/v1/messages \
     -H "x-api-key: YOUR_KEY" \
     -H "anthropic-version: 2023-06-01" \
     -H "content-type: application/json" \
     -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'

   # Test GHL
   curl https://rest.gohighlevel.com/v1/locations/YOUR_LOCATION_ID \
     -H "Authorization: Bearer YOUR_GHL_KEY"
   ```

4. **Contact developer:** See `README.md` for contact information

---

## Appendix: File Locations

```
ghl-real-estate-ai/
├── scripts/
│   ├── onboard_partner.py          ← Interactive onboarding tool
│   └── register_tenant.py          ← Legacy CLI-args tool
├── data/
│   └── tenants/
│       ├── loc_abc_001.json        ← Tenant config files
│       ├── loc_xyz_002.json
│       └── agency_master.json      ← Agency master key (if used)
├── services/
│   └── tenant_service.py           ← Backend service
└── tests/
    └── test_onboarding.py          ← Test suite
```

---

**Last Updated:** January 4, 2026
**Version:** 1.0.0
**Maintainer:** GHL Real Estate AI Development Team
