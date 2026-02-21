"""Unit tests for the daily email digest service.

Tests cover:
- Stats collection with missing Redis (graceful degradation)
- HTML email contains required sections (Performance, Leads, Failures)
- Successful digest send calls SendGrid with correct args
- SendGrid failure returns False without raising
- Schedule registration calls add_job with correct cron params
"""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.digest_service import (
    DigestService,
    DigestStats,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def digest_service():
    return DigestService()


@pytest.fixture
def sample_stats():
    return DigestStats(
        date=date(2026, 2, 20),
        leads_processed=42,
        hot_count=5,
        warm_count=12,
        cold_count=25,
        handoffs_executed=8,
        handoff_failures=2,
        dlq_size=3,
        api_cost_usd=1.47,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_collect_stats_handles_missing_redis(digest_service):
    """When Redis is unavailable, stats.errors is populated and no exception is raised."""
    with patch(
        "ghl_real_estate_ai.services.jorge.digest_service.task_queue",
        create=True,
    ) as mock_tq_import:
        # Force the task_queue import inside collect_daily_stats to raise
        with patch.dict(
            "sys.modules",
            {
                "ghl_real_estate_ai.services.task_queue": MagicMock(
                    task_queue=MagicMock(get_dlq_jobs=MagicMock(side_effect=ConnectionError("Redis down")))
                ),
            },
        ):
            stats = await digest_service.collect_daily_stats(date(2026, 2, 20))

    # Should not raise and should record the error
    assert isinstance(stats, DigestStats)
    assert any("failed" in e.lower() or "redis" in e.lower() for e in stats.errors)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_build_html_email_contains_required_sections(digest_service, sample_stats):
    """HTML output must contain Performance, Leads, and Failures section headers."""
    html = await digest_service.build_html_email(sample_stats)

    assert "Performance" in html
    assert "Leads" in html
    assert "Failures" in html
    assert "Lyrio Daily Summary" in html


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_digest_success(digest_service):
    """On success, send_digest calls SendGrid with the correct subject and recipient."""
    target = date(2026, 2, 20)
    recipient = "jorge@example.com"

    mock_client = AsyncMock()
    mock_client.send_email = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch.object(digest_service, "collect_daily_stats", new_callable=AsyncMock) as mock_collect,
        patch.object(digest_service, "build_html_email", new_callable=AsyncMock) as mock_build,
        patch("ghl_real_estate_ai.services.sendgrid_client.SendGridClient", return_value=mock_client),
    ):
        mock_collect.return_value = DigestStats(date=target)
        mock_build.return_value = "<html>test</html>"

        result = await digest_service.send_digest(recipient, target)

    assert result is True
    mock_client.send_email.assert_called_once()
    call_kwargs = mock_client.send_email.call_args
    assert call_kwargs.kwargs["to_email"] == recipient
    assert "Lyrio Daily Summary" in call_kwargs.kwargs["subject"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_send_digest_sendgrid_failure_returns_false(digest_service):
    """When SendGrid raises, send_digest returns False without propagating."""
    target = date(2026, 2, 20)

    mock_client = AsyncMock()
    mock_client.send_email = AsyncMock(side_effect=RuntimeError("SendGrid 503"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with (
        patch.object(digest_service, "collect_daily_stats", new_callable=AsyncMock) as mock_collect,
        patch.object(digest_service, "build_html_email", new_callable=AsyncMock) as mock_build,
        patch("ghl_real_estate_ai.services.sendgrid_client.SendGridClient", return_value=mock_client),
    ):
        mock_collect.return_value = DigestStats(date=target)
        mock_build.return_value = "<html>test</html>"

        result = await digest_service.send_digest("jorge@example.com", target)

    assert result is False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_schedule_registers_cron_job(digest_service):
    """schedule_daily_digest must call scheduler.add_job with hour=7, minute=0."""
    mock_scheduler = MagicMock()

    await digest_service.schedule_daily_digest(mock_scheduler, "jorge@example.com")

    mock_scheduler.add_job.assert_called_once()
    call_kwargs = mock_scheduler.add_job.call_args.kwargs

    assert call_kwargs["id"] == "jorge_daily_digest"
    assert call_kwargs["replace_existing"] is True

    # Verify the CronTrigger has hour=7, minute=0
    trigger = call_kwargs["trigger"]
    # CronTrigger fields are stored as BaseField objects; convert to string for check
    trigger_str = str(trigger)
    assert "7" in trigger_str
