# Revenue Intelligence Dashboard — ETL Architecture Design

**Date**: 2026-02-19 | **Version**: 1.0 | **Owner**: gtm-platform-builder

---

## Overview

The ETL pipeline reads from three MCP data sources (Stripe, Gumroad, Upwork), normalizes records into a unified transaction schema, and writes to `~/.claude/reference/freelance/revenue-tracker.md`. The Streamlit dashboard reads from this file.

All MCPs are treated as **read-only**. No writes to any external platform. All MCPs may be unavailable (not configured or credentials missing) — the ETL handles each source independently and exits 0 regardless.

---

## Data Sources

### Source 1: Stripe MCP

| Property | Value |
|----------|-------|
| MCP server | `stripe` (plugin, global) |
| Auth | `STRIPE_SECRET_KEY` env var |
| Access pattern | Read-only: payments, charges, subscriptions |
| Availability | Optional — may be unconfigured |

**Key endpoints / tools**:
- `list_charges` — one-time payments
- `list_subscriptions` — recurring revenue
- `list_balance_transactions` — settled transactions with fees

**Relevant fields**:
```
charge.id, charge.amount, charge.currency, charge.created (unix ts),
charge.description, charge.metadata, charge.status,
charge.payment_method_details.type,
subscription.id, subscription.plan.amount, subscription.plan.interval,
subscription.current_period_start, subscription.status
```

**Normalization notes**:
- Amount is in cents — divide by 100
- `created` is Unix timestamp — convert to ISO date
- Map `description` or `metadata.product` to `channel = "Stripe"`
- Status filter: `status == "succeeded"` only

---

### Source 2: Gumroad MCP

| Property | Value |
|----------|-------|
| MCP server | `gumroad` (`.mcp.json`) |
| Auth | `GUMROAD_ACCESS_TOKEN` env var |
| Access pattern | Read-only |
| Availability | Optional — may be unconfigured |

**Key endpoints / tools**:
- `list_sales` — all sales with buyer info and product data
- `get_product` — product name/price lookup by product_id

**Relevant fields**:
```
sale.id, sale.created_at (ISO datetime),
sale.price (cents), sale.product_name,
sale.product_id, sale.email (buyer),
sale.refunded (boolean), sale.chargebacked (boolean),
sale.recurrence (string — "monthly" | "yearly" | null)
```

**Normalization notes**:
- Price in cents — divide by 100
- Filter out `refunded=true` and `chargebacked=true`
- Channel: `"Gumroad"`
- Client: `sale.email` or `"Anonymous"` if blank

---

### Source 3: Upwork MCP

| Property | Value |
|----------|-------|
| MCP server | `upwork` (`.mcp.json`) |
| Auth | None required (per spec) |
| Access pattern | Job search, proposals |
| Availability | Optional — may be unconfigured |

**Key endpoints / tools**:
- `get_contracts` — active and completed contracts
- `get_earnings` — earnings by contract and time period

**Relevant fields**:
```
contract.id, contract.title, contract.client_name,
contract.contract_type ("hourly" | "fixed"),
contract.start_date, contract.end_date, contract.status,
earning.amount, earning.date, earning.contract_id
```

**Normalization notes**:
- Earnings are already in USD (no conversion)
- Channel: `"Upwork"`
- Client: `contract.client_name`
- For hourly contracts: sum weekly earnings into monthly buckets
- Status filter: include `status == "active"` and `status == "ended"`

---

## Normalized Transaction Schema

All three sources normalize to this common structure:

```python
@dataclass
class Transaction:
    id: str                   # Source-prefixed: "stripe_ch_xxx", "gumroad_xxx", "upwork_xxx"
    date: str                 # ISO date: "2026-02-19"
    channel: str              # "Stripe" | "Gumroad" | "Upwork" | "Manual"
    client: str               # Buyer email, company name, or "Anonymous"
    description: str          # Product name, job title, or service description
    amount_usd: float         # Always USD, rounded to 2 decimal places
    transaction_type: str     # "one-time" | "subscription" | "hourly" | "fixed"
    status: str               # "completed" | "pending" | "refunded"
    source_metadata: dict     # Raw fields preserved for debugging
```

---

## Monthly Summary Schema

After normalizing all transactions, aggregate into monthly buckets:

```python
@dataclass
class MonthlySummary:
    month: str         # "Feb 2026"
    upwork: float
    fiverr: float      # Manual entry only (no MCP)
    gumroad: float
    github_sponsors: float  # Manual entry only
    cold_outreach: float    # Manual entry only
    stripe: float      # Direct Stripe payments (non-Gumroad)
    other: float
    total: float
```

---

## ETL Flow

```
1. EXTRACT
   ├── Stripe MCP → list_charges, list_subscriptions
   ├── Gumroad MCP → list_sales
   └── Upwork MCP → get_earnings
   (each wrapped in try/except — MCP unavailability = empty list, logged as warning)

2. TRANSFORM
   ├── Normalize each source → List[Transaction]
   ├── Deduplicate by transaction.id
   ├── Filter: date >= current_month_start
   └── Aggregate: group by (channel, month) → MonthlySummary

3. LOAD
   ├── Read current revenue-tracker.md
   ├── Parse existing transaction log (avoid duplication)
   ├── Append new transactions to "Transaction Log" table
   ├── Update "Monthly Summary" table
   ├── Update "YTD Total"
   └── Write updated file (atomic: write to tmp, rename)
```

---

## Field Mappings: Source → Normalized

### Stripe

| Source Field | Normalized Field | Transformation |
|-------------|-----------------|----------------|
| `charge.id` | `id` | prefix "stripe_" |
| `charge.created` | `date` | Unix ts → ISO date |
| `"Stripe"` | `channel` | literal |
| `charge.description` | `description` | fallback to metadata.product |
| `charge.amount / 100` | `amount_usd` | cents to dollars |
| `"one-time"` | `transaction_type` | default |
| `charge.status` | `status` | "succeeded" → "completed" |

### Gumroad

| Source Field | Normalized Field | Transformation |
|-------------|-----------------|----------------|
| `sale.id` | `id` | prefix "gumroad_" |
| `sale.created_at` | `date` | ISO datetime → date |
| `"Gumroad"` | `channel` | literal |
| `sale.email` | `client` | fallback to "Anonymous" |
| `sale.product_name` | `description` | as-is |
| `sale.price / 100` | `amount_usd` | cents to dollars |
| `"one-time"` | `transaction_type` | "monthly"/"yearly" if recurrence set |
| `"completed"` | `status` | default (already filtered) |

### Upwork

| Source Field | Normalized Field | Transformation |
|-------------|-----------------|----------------|
| `earning.contract_id + earning.date` | `id` | concat, prefix "upwork_" |
| `earning.date` | `date` | as-is (already ISO date) |
| `"Upwork"` | `channel` | literal |
| `contract.client_name` | `client` | as-is |
| `contract.title` | `description` | as-is |
| `earning.amount` | `amount_usd` | as-is (USD) |
| `contract.contract_type` | `transaction_type` | "hourly" or "fixed" |
| `"completed"` | `status` | default |

---

## Revenue Tracker Update Logic

### Sections Updated

1. **Monthly Summary table** — recalculated from all known transactions
2. **YTD Total** — sum of all monthly totals
3. **Transaction Log** — append new rows (skip if `id` already present in log)

### Parsing Strategy

The revenue-tracker.md file uses GitHub-flavored markdown tables. Parse with:
- Split by `## ` to find sections
- Extract table rows with `| ` prefix
- Skip header rows (`| --- |` pattern)
- Match transaction IDs to detect duplicates

### Write Strategy

1. Read entire file to string
2. Replace the Monthly Summary table block
3. Replace the YTD total line
4. Append new transaction rows to Transaction Log table
5. Write atomically: `tmp_path = path + ".tmp"` → write → `rename(tmp_path, path)`

---

## Refresh Schedule

| Schedule | Trigger | Behavior |
|----------|---------|----------|
| On-demand | Manual `python scripts/revenue_auto_update.py` | Full ETL run |
| Weekly | Cron or GitHub Action (future) | Automated update |
| On dashboard load | Streamlit refresh button | Calls update script in subprocess |

---

## Error Handling

| Error Type | Handling |
|------------|----------|
| MCP not configured | Log warning, return empty list, continue |
| MCP auth failure | Log warning with masked key, skip source |
| MCP rate limit | Retry once after 2s, then skip |
| Parse error on response | Log raw response, skip malformed record |
| File write failure | Raise exception (this is critical path) |
| Duplicate transaction | Skip silently (idempotent) |

All errors logged to stderr. Script always exits 0 unless the tracker file write fails.

---

## Data Freshness

| Source | Latency | Notes |
|--------|---------|-------|
| Stripe | Real-time | Charges available immediately after payment |
| Gumroad | ~1hr | Sales API may have slight delay |
| Upwork | Daily | Earnings API updates once per day |

Dashboard displays "Last updated: [timestamp]" pulled from tracker file header.

---

## Security Considerations

- No credentials stored in script files — all via env vars
- Transaction data written only to local markdown file (not DB)
- Gumroad buyer emails stored as-is (PII) — acceptable for personal tracker
- No external API calls beyond MCP tools (no third-party logging)
