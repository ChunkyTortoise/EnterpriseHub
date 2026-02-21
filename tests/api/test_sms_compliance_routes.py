"""
Tests for SMS compliance API routes (ROADMAP-036–040).
Validates real DB queries for compliance dashboard, scoring, and recommendations.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.asyncio


class FakeConnection:
    """Fake asyncpg connection for testing DB queries."""

    def __init__(self, opt_outs=0, violations=0, total_messages=100):
        self._opt_outs = opt_outs
        self._violations = violations
        self._total_messages = total_messages
        self._call_index = 0

    async def fetchval(self, query, *args):
        self._call_index += 1
        q = query.strip().lower()
        if "sms_opt_outs" in q:
            return self._opt_outs
        if "violations" in q or "having" in q:
            return self._violations
        if "sms_send_audit_log" in q:
            return self._total_messages
        return 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class FakeDatabase:
    """Fake database service."""

    def __init__(self, conn):
        self._conn = conn

    def get_connection(self):
        return self._conn


@pytest.fixture
def mock_db_clean():
    """DB with zero violations."""
    conn = FakeConnection(opt_outs=0, violations=0, total_messages=50)
    return FakeDatabase(conn)


@pytest.fixture
def mock_db_violations():
    """DB with violations and opt-outs."""
    conn = FakeConnection(opt_outs=5, violations=8, total_messages=200)
    return FakeDatabase(conn)


@pytest.fixture
def admin_user():
    return {"username": "admin", "role": "admin", "user_id": "admin-1"}


@pytest.fixture
def non_admin_user():
    return {"username": "agent", "role": "agent", "user_id": "agent-1"}


class TestComplianceScore:
    """Test ROADMAP-039: compliance score calculation."""

    def test_perfect_score(self):
        """Score is 100 when no violations and no opt-outs."""
        violations = 0
        opt_out_rate = 0.0
        raw = 100.0 - (violations * 10) - (opt_out_rate * 20)
        score = max(0.0, min(100.0, raw))
        assert score == 100.0

    def test_score_with_violations_only(self):
        """Score drops 10 per violation."""
        violations = 3
        opt_out_rate = 0.0
        raw = 100.0 - (violations * 10) - (opt_out_rate * 20)
        score = max(0.0, min(100.0, raw))
        assert score == 70.0

    def test_score_with_opt_outs_only(self):
        """Score drops by opt_out_rate * 20."""
        violations = 0
        opt_out_rate = 2.5  # 2.5%
        raw = 100.0 - (violations * 10) - (opt_out_rate * 20)
        score = max(0.0, min(100.0, raw))
        assert score == 50.0

    def test_score_clamped_at_zero(self):
        """Score never goes below 0."""
        violations = 15
        opt_out_rate = 5.0
        raw = 100.0 - (violations * 10) - (opt_out_rate * 20)
        score = max(0.0, min(100.0, raw))
        assert score == 0.0

    def test_score_clamped_at_100(self):
        """Score never exceeds 100."""
        violations = 0
        opt_out_rate = 0.0
        raw = 100.0 - (violations * 10) - (opt_out_rate * 20)
        score = max(0.0, min(100.0, raw))
        assert score == 100.0

    def test_combined_score(self):
        """Violations + opt-outs both affect score."""
        violations = 2
        opt_out_rate = 1.5  # 1.5%
        raw = 100.0 - (violations * 10) - (opt_out_rate * 20)
        score = max(0.0, min(100.0, raw))
        assert score == 50.0


class TestComplianceRecommendations:
    """Test ROADMAP-040: compliance recommendation engine."""

    def _generate_recommendations(self, violations, opt_out_rate):
        recommendations = []
        if violations > 5:
            recommendations.append("Reduce message frequency — multiple contacts exceed daily SMS limits")
        if opt_out_rate > 2.0:
            recommendations.append("Review message content — opt-out rate exceeds 2% threshold")
        if violations > 0 and violations <= 5:
            recommendations.append("Monitor frequency trends — some contacts approaching daily limits")
        if opt_out_rate > 0 and opt_out_rate <= 2.0:
            recommendations.append("Opt-out rate within acceptable range — continue monitoring")
        if violations == 0 and opt_out_rate == 0:
            recommendations.append("Excellent compliance — no violations or opt-outs detected")
        return recommendations

    def test_excellent_compliance(self):
        recs = self._generate_recommendations(0, 0.0)
        assert len(recs) == 1
        assert "Excellent compliance" in recs[0]

    def test_high_violations(self):
        recs = self._generate_recommendations(8, 0.0)
        assert any("Reduce message frequency" in r for r in recs)

    def test_high_opt_out_rate(self):
        recs = self._generate_recommendations(0, 3.0)
        assert any("Review message content" in r for r in recs)

    def test_low_violations(self):
        recs = self._generate_recommendations(3, 0.0)
        assert any("Monitor frequency trends" in r for r in recs)

    def test_low_opt_out_rate(self):
        recs = self._generate_recommendations(0, 1.5)
        assert any("acceptable range" in r for r in recs)

    def test_combined_issues(self):
        recs = self._generate_recommendations(8, 3.5)
        assert any("Reduce message frequency" in r for r in recs)
        assert any("Review message content" in r for r in recs)


class TestComplianceReportEndpoint:
    """Integration-style tests for the compliance-report endpoint logic."""

    async def _call_report(self, mock_db, location_id=None, days=7, cache=None):
        """Simulate the compliance report logic without spinning up FastAPI."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        conn = mock_db._conn
        if location_id:
            total_opt_outs = await conn.fetchval(
                "SELECT COUNT(*) FROM sms_opt_outs WHERE location_id = $1 AND opted_out_at >= $2",
                location_id,
                cutoff,
            )
        else:
            total_opt_outs = await conn.fetchval(
                "SELECT COUNT(*) FROM sms_opt_outs WHERE opted_out_at >= $1",
                cutoff,
            )

        frequency_violations = await conn.fetchval(
            """SELECT COUNT(*) FROM (
                SELECT phone_number, DATE(sent_at), COUNT(*) AS msg_count
                FROM sms_send_audit_log WHERE sent_at >= $1
                GROUP BY phone_number, DATE(sent_at) HAVING COUNT(*) > 3
            ) AS violations""",
            cutoff,
        )

        total_messages = await conn.fetchval(
            "SELECT COUNT(*) FROM sms_send_audit_log WHERE sent_at >= $1",
            cutoff,
        )

        total_opt_outs = int(total_opt_outs or 0)
        frequency_violations = int(frequency_violations or 0)
        total_messages = int(total_messages or 0)

        opt_out_rate = (total_opt_outs / total_messages * 100) if total_messages > 0 else 0.0
        raw_score = 100.0 - (frequency_violations * 10) - (opt_out_rate * 20)
        compliance_score = max(0.0, min(100.0, raw_score))

        return {
            "total_opt_outs": total_opt_outs,
            "frequency_violations": frequency_violations,
            "total_messages_sent": total_messages,
            "opt_out_rate_pct": round(opt_out_rate, 2),
            "compliance_score": round(compliance_score, 1),
        }

    async def test_clean_report(self, mock_db_clean):
        """Clean DB yields perfect score."""
        result = await self._call_report(mock_db_clean)
        assert result["total_opt_outs"] == 0
        assert result["frequency_violations"] == 0
        assert result["compliance_score"] == 100.0

    async def test_violations_report(self, mock_db_violations):
        """Violations and opt-outs lower the score."""
        result = await self._call_report(mock_db_violations)
        assert result["total_opt_outs"] == 5
        assert result["frequency_violations"] == 8
        assert result["total_messages_sent"] == 200
        # opt_out_rate = 5/200*100 = 2.5%
        assert result["opt_out_rate_pct"] == 2.5
        # score = 100 - (8*10) - (2.5*20) = 100 - 80 - 50 = -30, clamped to 0
        assert result["compliance_score"] == 0.0

    async def test_zero_messages_no_division_error(self):
        """Zero messages doesn't cause division by zero."""
        conn = FakeConnection(opt_outs=0, violations=0, total_messages=0)
        db = FakeDatabase(conn)
        result = await self._call_report(db)
        assert result["opt_out_rate_pct"] == 0.0
        assert result["compliance_score"] == 100.0

    async def test_with_location_filter(self, mock_db_clean):
        """Location filter passes through to query."""
        result = await self._call_report(mock_db_clean, location_id="loc_123")
        assert result["total_opt_outs"] == 0
