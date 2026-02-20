"""
revenue_auto_update.py — ETL: Stripe + Gumroad + Upwork MCPs → revenue-tracker.md

Queries available MCP data sources for revenue transactions, normalizes to a
unified schema, and updates ~/.claude/reference/freelance/revenue-tracker.md.

Usage:
    python scripts/revenue_auto_update.py
    python scripts/revenue_auto_update.py --dry-run
    python scripts/revenue_auto_update.py --source stripe
    python scripts/revenue_auto_update.py --since 2026-02-01

Always exits 0. MCP unavailability is a warning, not an error.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import re
import subprocess
import tempfile
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TRACKER_PATH = Path.home() / ".claude" / "reference" / "freelance" / "revenue-tracker.md"

SOURCES = ("stripe", "gumroad", "upwork")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Transaction:
    id: str
    date: str               # ISO date "YYYY-MM-DD"
    channel: str            # "Stripe" | "Gumroad" | "Upwork" | "Manual"
    client: str
    description: str
    amount_usd: float
    transaction_type: str   # "one-time" | "subscription" | "hourly" | "fixed"
    status: str             # "completed" | "pending" | "refunded"


@dataclass
class ETLResult:
    source: str
    transactions: list[Transaction] = field(default_factory=list)
    error: Optional[str] = None
    warning: Optional[str] = None


# ---------------------------------------------------------------------------
# MCP helpers — each returns a list of Transaction or raises gracefully
# ---------------------------------------------------------------------------

def _unix_to_iso(ts: int | float) -> str:
    """Convert Unix timestamp to ISO date string."""
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def _cents_to_usd(cents: int) -> float:
    return round(cents / 100, 2)


def _call_mcp_tool(server: str, tool: str, args: dict) -> dict:
    """
    Call an MCP tool via subprocess using the claude CLI.
    Returns parsed JSON result or raises RuntimeError.
    """
    payload = json.dumps({"tool": tool, "arguments": args})
    result = subprocess.run(
        ["claude", "mcp", "call", server, "--json", payload],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"MCP call failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Stripe ETL
# ---------------------------------------------------------------------------

def _extract_stripe(since: Optional[date]) -> ETLResult:
    result = ETLResult(source="stripe")
    api_key = os.environ.get("STRIPE_SECRET_KEY")
    if not api_key:
        result.warning = "STRIPE_SECRET_KEY not set — skipping Stripe"
        log.warning(result.warning)
        return result

    try:
        # Attempt to list charges via MCP
        args: dict = {"limit": 100}
        if since:
            # Stripe uses Unix timestamp for created[gte]
            args["created[gte]"] = int(datetime(since.year, since.month, since.day, tzinfo=timezone.utc).timestamp())

        try:
            response = _call_mcp_tool("stripe", "list_charges", args)
            charges = response.get("data", [])
        except (RuntimeError, FileNotFoundError):
            # Try direct Stripe API as fallback via httpx if available
            result.warning = "Stripe MCP unavailable — skipping Stripe"
            log.warning(result.warning)
            return result

        for charge in charges:
            if charge.get("status") != "succeeded":
                continue
            tx = Transaction(
                id=f"stripe_{charge['id']}",
                date=_unix_to_iso(charge["created"]),
                channel="Stripe",
                client=charge.get("billing_details", {}).get("email") or "Anonymous",
                description=charge.get("description") or charge.get("metadata", {}).get("product", "Stripe Payment"),
                amount_usd=_cents_to_usd(charge.get("amount", 0)),
                transaction_type="one-time",
                status="completed",
            )
            result.transactions.append(tx)

    except Exception as exc:
        result.warning = f"Stripe extraction error: {exc}"
        log.warning(result.warning)

    log.info(f"Stripe: {len(result.transactions)} transactions extracted")
    return result


# ---------------------------------------------------------------------------
# Gumroad ETL
# ---------------------------------------------------------------------------

def _extract_gumroad(since: Optional[date]) -> ETLResult:
    result = ETLResult(source="gumroad")
    token = os.environ.get("GUMROAD_ACCESS_TOKEN")
    if not token:
        result.warning = "GUMROAD_ACCESS_TOKEN not set — skipping Gumroad"
        log.warning(result.warning)
        return result

    try:
        args: dict = {}
        if since:
            args["after"] = since.isoformat()

        try:
            response = _call_mcp_tool("gumroad", "list_sales", args)
            sales = response.get("sales", [])
        except (RuntimeError, FileNotFoundError):
            result.warning = "Gumroad MCP unavailable — skipping Gumroad"
            log.warning(result.warning)
            return result

        for sale in sales:
            # Skip refunds and chargebacks
            if sale.get("refunded") or sale.get("chargebacked"):
                continue
            created_at = sale.get("created_at", "")
            iso_date = created_at[:10] if created_at else date.today().isoformat()
            recurrence = sale.get("recurrence")
            tx_type = "subscription" if recurrence else "one-time"
            tx = Transaction(
                id=f"gumroad_{sale['id']}",
                date=iso_date,
                channel="Gumroad",
                client=sale.get("email") or "Anonymous",
                description=sale.get("product_name", "Gumroad Product"),
                amount_usd=_cents_to_usd(int(sale.get("price", 0))),
                transaction_type=tx_type,
                status="completed",
            )
            result.transactions.append(tx)

    except Exception as exc:
        result.warning = f"Gumroad extraction error: {exc}"
        log.warning(result.warning)

    log.info(f"Gumroad: {len(result.transactions)} transactions extracted")
    return result


# ---------------------------------------------------------------------------
# Upwork ETL
# ---------------------------------------------------------------------------

def _extract_upwork(since: Optional[date]) -> ETLResult:
    result = ETLResult(source="upwork")
    try:
        args: dict = {}
        if since:
            args["start_date"] = since.isoformat()

        try:
            response = _call_mcp_tool("upwork", "get_earnings", args)
            earnings = response.get("earnings", [])
            contracts_resp = _call_mcp_tool("upwork", "get_contracts", {})
            contracts = {c["id"]: c for c in contracts_resp.get("contracts", [])}
        except (RuntimeError, FileNotFoundError):
            result.warning = "Upwork MCP unavailable — skipping Upwork"
            log.warning(result.warning)
            return result

        for earning in earnings:
            contract_id = earning.get("contract_id", "unknown")
            contract = contracts.get(contract_id, {})
            tx = Transaction(
                id=f"upwork_{contract_id}_{earning.get('date', 'unknown')}",
                date=earning.get("date", date.today().isoformat()),
                channel="Upwork",
                client=contract.get("client_name", "Upwork Client"),
                description=contract.get("title", "Upwork Contract"),
                amount_usd=float(earning.get("amount", 0)),
                transaction_type=contract.get("contract_type", "hourly"),
                status="completed",
            )
            result.transactions.append(tx)

    except Exception as exc:
        result.warning = f"Upwork extraction error: {exc}"
        log.warning(result.warning)

    log.info(f"Upwork: {len(result.transactions)} transactions extracted")
    return result


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _parse_existing_ids(tracker_content: str) -> set[str]:
    """
    Extract transaction IDs already in the tracker file.
    IDs appear as the first cell in Transaction Log table rows.
    Pattern: | stripe_ch_xxx | or | gumroad_xxx | or | upwork_xxx_date |
    """
    ids: set[str] = set()
    pattern = re.compile(r"^\|\s*((?:stripe|gumroad|upwork|manual)_\S+)\s*\|", re.MULTILINE)
    for match in pattern.finditer(tracker_content):
        ids.add(match.group(1))
    return ids


# ---------------------------------------------------------------------------
# Tracker update
# ---------------------------------------------------------------------------

def _month_key(iso_date: str) -> str:
    """Convert '2026-02-19' to 'Feb 2026'."""
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    return dt.strftime("%b %Y")


def _build_monthly_summary(all_transactions: list[Transaction]) -> dict[str, dict[str, float]]:
    """Aggregate transactions into monthly channel buckets."""
    summary: dict[str, dict[str, float]] = {}
    channels = ["Upwork", "Gumroad", "Stripe", "Other"]
    for tx in all_transactions:
        if tx.status == "refunded":
            continue
        month = _month_key(tx.date)
        if month not in summary:
            summary[month] = {ch: 0.0 for ch in channels}
            summary[month]["Fiverr"] = 0.0
            summary[month]["GitHub Sponsors"] = 0.0
            summary[month]["Cold Outreach"] = 0.0
        channel = tx.channel if tx.channel in channels else "Other"
        summary[month][channel] = round(summary[month].get(channel, 0.0) + tx.amount_usd, 2)
    return summary


def _format_transaction_rows(new_txs: list[Transaction]) -> list[str]:
    rows = []
    for tx in new_txs:
        row = f"| {tx.id} | {tx.date} | {tx.channel} | {tx.client[:30]} | {tx.description[:40]} | ${tx.amount_usd:.2f} | {tx.status} |"
        rows.append(row)
    return rows


def _update_tracker(
    tracker_path: Path,
    new_transactions: list[Transaction],
    dry_run: bool = False,
) -> dict:
    """
    Read, update, and write the revenue tracker.
    Returns summary dict.
    """
    content = tracker_path.read_text(encoding="utf-8") if tracker_path.exists() else ""

    # Deduplicate
    existing_ids = _parse_existing_ids(content)
    truly_new = [tx for tx in new_transactions if tx.id not in existing_ids]
    log.info(f"New transactions to add: {len(truly_new)} (skipped {len(new_transactions) - len(truly_new)} duplicates)")

    if not truly_new and not dry_run:
        log.info("No new transactions — tracker is up to date")
        return {"added": 0, "total_new_revenue": 0.0}

    # Build updated last_updated line
    today = date.today().isoformat()
    if "**Last Updated**:" in content:
        content = re.sub(r"\*\*Last Updated\*\*:.*", f"**Last Updated**: {today}", content)
    else:
        content = f"**Last Updated**: {today}\n\n" + content

    # Append new transaction rows to Transaction Log table
    new_rows = _format_transaction_rows(truly_new)
    if new_rows:
        # Find the Transaction Log section
        if "| _No transactions yet_" in content:
            # Replace placeholder row
            header_row = "| Date | Channel | Client | Description | Amount | Status |"
            new_header = (
                "| ID | Date | Channel | Client | Description | Amount | Status |\n"
                "|-----|------|---------|--------|-------------|--------|--------|\n"
            )
            # Replace no-transactions placeholder
            content = content.replace(
                "| _No transactions yet_ | — | — | — | — | — |",
                "\n".join(new_rows),
            )
        else:
            # Find end of transaction log table and append
            log_section_match = re.search(r"## Transaction Log\n", content)
            if log_section_match:
                # Find the last table row in this section
                after_log = content[log_section_match.end():]
                # Append after the last | row before the next ##
                next_section = re.search(r"\n##", after_log)
                if next_section:
                    insert_pos = log_section_match.end() + next_section.start()
                    content = content[:insert_pos] + "\n" + "\n".join(new_rows) + content[insert_pos:]
                else:
                    content += "\n" + "\n".join(new_rows)

    # Update YTD total
    total_revenue = sum(tx.amount_usd for tx in truly_new if tx.status == "completed")
    ytd_match = re.search(r"## YTD Total: \$[\d,\.]+", content)
    if ytd_match:
        # Extract existing total and add new revenue
        existing_total_match = re.search(r"\$([0-9,]+(?:\.[0-9]{2})?)", ytd_match.group())
        existing_total = 0.0
        if existing_total_match:
            try:
                existing_total = float(existing_total_match.group(1).replace(",", ""))
            except ValueError:
                existing_total = 0.0
        new_total = existing_total + total_revenue
        content = content[:ytd_match.start()] + f"## YTD Total: ${new_total:,.2f}" + content[ytd_match.end():]

    if dry_run:
        log.info("[DRY RUN] Would write updated tracker — no file changes made")
        log.info(f"[DRY RUN] New transactions:\n" + "\n".join(new_rows))
    else:
        # Atomic write via temp file
        tmp = tracker_path.with_suffix(".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.rename(tracker_path)
        log.info(f"Tracker updated: {tracker_path}")

    return {
        "added": len(truly_new),
        "total_new_revenue": round(total_revenue, 2),
        "new_transaction_ids": [tx.id for tx in truly_new],
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Revenue auto-update ETL script")
    parser.add_argument(
        "--source",
        choices=list(SOURCES) + ["all"],
        default="all",
        help="Which data source to query (default: all)",
    )
    parser.add_argument(
        "--since",
        type=str,
        default=None,
        help="Only fetch transactions on or after this date (ISO format, e.g. 2026-02-01)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would be updated without writing to file",
    )
    args = parser.parse_args()

    since: Optional[date] = None
    if args.since:
        try:
            since = date.fromisoformat(args.since)
        except ValueError:
            log.error(f"Invalid --since date: {args.since} — must be YYYY-MM-DD")
            sys.exit(0)  # Always exit 0

    sources_to_run = list(SOURCES) if args.source == "all" else [args.source]

    # Extract from each source
    all_transactions: list[Transaction] = []
    for source in sources_to_run:
        if source == "stripe":
            etl_result = _extract_stripe(since)
        elif source == "gumroad":
            etl_result = _extract_gumroad(since)
        elif source == "upwork":
            etl_result = _extract_upwork(since)
        else:
            continue
        all_transactions.extend(etl_result.transactions)

    log.info(f"Total transactions extracted: {len(all_transactions)}")

    # Update tracker
    if not TRACKER_PATH.parent.exists():
        log.warning(f"Tracker directory does not exist: {TRACKER_PATH.parent}")
        if not args.dry_run:
            TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)

    summary = _update_tracker(TRACKER_PATH, all_transactions, dry_run=args.dry_run)

    log.info(
        f"Done. Added {summary['added']} transactions, "
        f"${summary['total_new_revenue']:.2f} new revenue."
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
