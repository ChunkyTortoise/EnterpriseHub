"""Daily email digest -- collects Lyrio stats and emails Jorge at 7am PT."""
from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DigestStats:
    date: date
    leads_processed: int = 0
    hot_count: int = 0
    warm_count: int = 0
    cold_count: int = 0
    handoffs_executed: int = 0
    handoff_failures: int = 0
    dlq_size: int = 0
    api_cost_usd: Optional[float] = None
    errors: List[str] = field(default_factory=list)


class DigestService:
    """Aggregates daily Lyrio metrics and sends a summary email digest."""

    async def collect_daily_stats(self, target_date: date) -> DigestStats:
        """Aggregate daily stats -- gracefully handles missing dependencies."""
        stats = DigestStats(date=target_date)

        # DLQ size from task_queue
        try:
            from ghl_real_estate_ai.services.task_queue import task_queue

            dlq_info = task_queue.get_dlq_jobs()
            stats.dlq_size = dlq_info.get("count", 0)
        except Exception as exc:
            stats.errors.append(f"DLQ fetch failed: {exc}")

        # Handoff counts from HandoffRedisStore / analytics
        try:
            from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
                JorgeHandoffService,
            )

            summary = JorgeHandoffService.get_analytics_summary()
            stats.handoffs_executed = summary.get("successful_handoffs", 0)
            stats.handoff_failures = summary.get("failed_handoffs", 0)
            stats.leads_processed = summary.get("total_handoffs", 0)

            # Derive temperature counts from route data if available
            by_route = summary.get("handoffs_by_route", {})
            stats.hot_count = by_route.get("hot", 0)
            stats.warm_count = by_route.get("warm", 0)
            stats.cold_count = by_route.get("cold", 0)
        except Exception as exc:
            stats.errors.append(f"Handoff stats failed: {exc}")

        # API cost from token tracker (optional)
        try:
            from ghl_real_estate_ai.services.token_tracker import TokenTracker

            tracker = TokenTracker()
            # TokenTracker doesn't expose get_month_total; skip gracefully
            stats.api_cost_usd = None
        except Exception as exc:
            stats.errors.append(f"API cost fetch failed: {exc}")

        return stats

    async def build_html_email(self, stats: DigestStats) -> str:
        """Build inline-styled HTML email with 3 sections: Performance, Leads, Failures."""
        date_str = stats.date.strftime("%B %d, %Y")

        errors_html = ""
        if stats.errors:
            error_items = "".join(
                f"<li style='color:#b91c1c;'>{e}</li>" for e in stats.errors
            )
            errors_html = f"<ul style='margin:0;padding-left:20px;'>{error_items}</ul>"
        else:
            errors_html = "<p style='color:#15803d;margin:0;'>No collection errors.</p>"

        cost_line = (
            f"${stats.api_cost_usd:.2f}"
            if stats.api_cost_usd is not None
            else "N/A"
        )

        html = f"""\
<html>
<body style="font-family:Arial,sans-serif;background:#f9fafb;padding:20px;">
<div style="max-width:600px;margin:0 auto;background:#ffffff;border-radius:8px;overflow:hidden;">

  <div style="background:#1e40af;color:#ffffff;padding:20px;">
    <h1 style="margin:0;font-size:22px;">Lyrio Daily Summary</h1>
    <p style="margin:4px 0 0 0;font-size:14px;opacity:0.9;">{date_str}</p>
  </div>

  <div style="padding:20px;">

    <!-- Performance Section -->
    <div style="margin-bottom:24px;">
      <h2 style="font-size:16px;color:#1e40af;border-bottom:2px solid #1e40af;padding-bottom:6px;">
        Performance
      </h2>
      <table style="width:100%;font-size:14px;border-collapse:collapse;">
        <tr><td style="padding:4px 0;">Total interactions</td><td style="text-align:right;font-weight:bold;">{stats.leads_processed}</td></tr>
        <tr><td style="padding:4px 0;">API cost (est.)</td><td style="text-align:right;font-weight:bold;">{cost_line}</td></tr>
      </table>
    </div>

    <!-- Leads Section -->
    <div style="margin-bottom:24px;">
      <h2 style="font-size:16px;color:#1e40af;border-bottom:2px solid #1e40af;padding-bottom:6px;">
        Leads
      </h2>
      <table style="width:100%;font-size:14px;border-collapse:collapse;">
        <tr><td style="padding:4px 0;">Hot</td><td style="text-align:right;font-weight:bold;color:#dc2626;">{stats.hot_count}</td></tr>
        <tr><td style="padding:4px 0;">Warm</td><td style="text-align:right;font-weight:bold;color:#d97706;">{stats.warm_count}</td></tr>
        <tr><td style="padding:4px 0;">Cold</td><td style="text-align:right;font-weight:bold;color:#2563eb;">{stats.cold_count}</td></tr>
        <tr><td style="padding:4px 0;">Handoffs executed</td><td style="text-align:right;font-weight:bold;">{stats.handoffs_executed}</td></tr>
        <tr><td style="padding:4px 0;">Total processed</td><td style="text-align:right;font-weight:bold;">{stats.leads_processed}</td></tr>
      </table>
    </div>

    <!-- Failures Section -->
    <div style="margin-bottom:12px;">
      <h2 style="font-size:16px;color:#1e40af;border-bottom:2px solid #1e40af;padding-bottom:6px;">
        Failures
      </h2>
      <table style="width:100%;font-size:14px;border-collapse:collapse;">
        <tr><td style="padding:4px 0;">DLQ size</td><td style="text-align:right;font-weight:bold;">{stats.dlq_size}</td></tr>
        <tr><td style="padding:4px 0;">Handoff failures</td><td style="text-align:right;font-weight:bold;">{stats.handoff_failures}</td></tr>
      </table>
      <div style="margin-top:8px;">
        <strong style="font-size:13px;">Collection errors:</strong>
        {errors_html}
      </div>
    </div>

  </div>

  <div style="background:#f3f4f6;padding:12px 20px;font-size:12px;color:#6b7280;text-align:center;">
    Lyrio AI &mdash; Automated daily digest
  </div>

</div>
</body>
</html>"""
        return html

    async def send_digest(self, recipient_email: str, target_date: date) -> bool:
        """Send digest email. Returns True on success, False on failure. Never raises."""
        try:
            stats = await self.collect_daily_stats(target_date)
            html = await self.build_html_email(stats)
            subject = f"Lyrio Daily Summary \u2014 {target_date.strftime('%b %-d, %Y')}"

            from ghl_real_estate_ai.services.sendgrid_client import SendGridClient

            async with SendGridClient() as client:
                await client.send_email(
                    to_email=recipient_email,
                    subject=subject,
                    html_content=html,
                )

            logger.info("Digest sent to %s for %s", recipient_email, target_date)
            return True
        except Exception as e:
            logger.error("Failed to send digest: %s", e)
            return False

    async def schedule_daily_digest(self, scheduler, recipient_email: str) -> None:
        """Register 7am PT daily cron job with APScheduler."""
        from apscheduler.triggers.cron import CronTrigger

        def _run_digest():
            """Sync wrapper so APScheduler can invoke the async send."""
            loop = asyncio.new_event_loop()
            try:
                loop.run_until_complete(
                    self.send_digest(recipient_email, date.today())
                )
            finally:
                loop.close()

        trigger = CronTrigger(
            hour=7,
            minute=0,
            timezone="America/Los_Angeles",
        )

        scheduler.add_job(
            func=_run_digest,
            trigger=trigger,
            id="jorge_daily_digest",
            replace_existing=True,
        )

        logger.info(
            "Scheduled daily digest for %s at 7:00 AM PT", recipient_email
        )
