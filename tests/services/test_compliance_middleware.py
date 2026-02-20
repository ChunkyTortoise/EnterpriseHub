import pytest

pytestmark = pytest.mark.integration

"""
Tests for FHA/RESPA Compliance Middleware.

Covers:
- School quality steering detection
- Safety/crime steering detection
- Familial status steering detection
- Availability steering detection
- RESPA violation detection
- RESPA disclosure tracking
- Risk score computation
- Status determination (PASSED / FLAGGED / BLOCKED)
- Conversation-level escalation
- Safe alternative messages
"""

import os

os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_fake_for_testing")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_fake")

import pytest

from ghl_real_estate_ai.services.compliance_guard import ComplianceStatus
from ghl_real_estate_ai.services.compliance_middleware import (
    ComplianceMiddleware,
    ComplianceResult,
    ViolationCategory,
    ViolationSeverity,
)


@pytest.fixture
def middleware():
    return ComplianceMiddleware()


# ---------------------------------------------------------------------------
# School Quality Steering
# ---------------------------------------------------------------------------


class TestSchoolSteering:
    @pytest.mark.asyncio
    async def test_good_schools_flagged(self, middleware):
        result = await middleware.enforce(
            message="This area has really good schools for your kids",
            contact_id="c1",
        )
        assert any(v.category == ViolationCategory.STEERING for v in result.violations)
        assert result.risk_score > 0

    @pytest.mark.asyncio
    async def test_best_schools_flagged(self, middleware):
        result = await middleware.enforce(
            message="The best schools in the county are right here",
            contact_id="c2",
        )
        steering = [v for v in result.violations if v.category == ViolationCategory.STEERING]
        assert len(steering) >= 1

    @pytest.mark.asyncio
    async def test_neutral_school_mention_passes(self, middleware):
        """Mentioning 'school' without quality framing should pass."""
        result = await middleware.enforce(
            message="There is a school nearby on Main Street",
            contact_id="c3",
        )
        school_violations = [v for v in result.violations if "school" in v.pattern.lower()]
        assert len(school_violations) == 0


# ---------------------------------------------------------------------------
# Safety Steering
# ---------------------------------------------------------------------------


class TestSafetySteering:
    @pytest.mark.asyncio
    async def test_safe_neighborhood_blocked(self, middleware):
        result = await middleware.enforce(
            message="This is a very safe neighborhood, you'll love it",
            contact_id="c10",
        )
        assert result.status == ComplianceStatus.BLOCKED
        assert any(v.category == ViolationCategory.STEERING for v in result.violations)

    @pytest.mark.asyncio
    async def test_bad_area_blocked(self, middleware):
        result = await middleware.enforce(
            message="I'd avoid that bad part of town if I were you",
            contact_id="c11",
        )
        assert result.status == ComplianceStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_low_crime_flagged(self, middleware):
        result = await middleware.enforce(
            message="This area has very low crime rates",
            contact_id="c12",
        )
        assert any(v.category == ViolationCategory.STEERING for v in result.violations)


# ---------------------------------------------------------------------------
# Familial Status
# ---------------------------------------------------------------------------


class TestFamilialStatus:
    @pytest.mark.asyncio
    async def test_quiet_neighborhood_flagged(self, middleware):
        result = await middleware.enforce(
            message="It's a quiet neighborhood, perfect for couples",
            contact_id="c20",
        )
        fam_violations = [v for v in result.violations if v.category == ViolationCategory.FAMILIAL_STATUS]
        assert len(fam_violations) >= 1

    @pytest.mark.asyncio
    async def test_adult_community_blocked(self, middleware):
        result = await middleware.enforce(
            message="This is an adult only community",
            contact_id="c21",
        )
        assert result.status == ComplianceStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_no_kids_blocked(self, middleware):
        result = await middleware.enforce(
            message="There are no kids in this building",
            contact_id="c22",
        )
        assert result.status == ComplianceStatus.BLOCKED


# ---------------------------------------------------------------------------
# Availability Steering
# ---------------------------------------------------------------------------


class TestAvailabilitySteering:
    @pytest.mark.asyncio
    async def test_sold_out_area_blocked(self, middleware):
        result = await middleware.enforce(
            message="Everything is sold out in that area unfortunately",
            contact_id="c30",
        )
        assert result.status == ComplianceStatus.BLOCKED
        assert any(v.category == ViolationCategory.AVAILABILITY_STEERING for v in result.violations)

    @pytest.mark.asyncio
    async def test_wouldnt_recommend_blocked(self, middleware):
        result = await middleware.enforce(
            message="I wouldn't recommend that neighborhood for you",
            contact_id="c31",
        )
        assert result.status == ComplianceStatus.BLOCKED


# ---------------------------------------------------------------------------
# RESPA Violations
# ---------------------------------------------------------------------------


class TestRESPA:
    @pytest.mark.asyncio
    async def test_kickback_language_blocked(self, middleware):
        result = await middleware.enforce(
            message="I'll give you a kickback if you use our lender",
            contact_id="c40",
        )
        assert result.status == ComplianceStatus.BLOCKED
        respa = [v for v in result.violations if v.category == ViolationCategory.RESPA_REFERRAL]
        assert len(respa) >= 1

    @pytest.mark.asyncio
    async def test_require_service_provider_blocked(self, middleware):
        result = await middleware.enforce(
            message="We require you to use our title company for this transaction",
            contact_id="c41",
        )
        assert result.status == ComplianceStatus.BLOCKED

    @pytest.mark.asyncio
    async def test_affiliated_lender_needs_disclosure(self, middleware):
        result = await middleware.enforce(
            message="You should use our lender, they give great rates",
            contact_id="c42",
        )
        assert len(result.respa_disclosures_needed) >= 1
        assert any("AfBA" in d or "affiliated" in d.lower() for d in result.respa_disclosures_needed)


# ---------------------------------------------------------------------------
# Clean Messages
# ---------------------------------------------------------------------------


class TestCleanMessages:
    @pytest.mark.asyncio
    async def test_normal_message_passes(self, middleware):
        result = await middleware.enforce(
            message="The property at 123 Main St has 3 bedrooms and 2 bathrooms",
            contact_id="c50",
        )
        assert result.status == ComplianceStatus.PASSED
        assert result.risk_score == 0.0
        assert len(result.violations) == 0

    @pytest.mark.asyncio
    async def test_price_discussion_passes(self, middleware):
        result = await middleware.enforce(
            message="Based on recent sales, I'd estimate your home at $750,000",
            contact_id="c51",
        )
        assert result.status == ComplianceStatus.PASSED

    @pytest.mark.asyncio
    async def test_qualification_question_passes(self, middleware):
        result = await middleware.enforce(
            message="What price would incentivize you to sell?",
            contact_id="c52",
        )
        assert result.status == ComplianceStatus.PASSED


# ---------------------------------------------------------------------------
# Conversation-Level Escalation
# ---------------------------------------------------------------------------


class TestConversationEscalation:
    @pytest.mark.asyncio
    async def test_accumulated_violations_escalate(self, middleware):
        """3+ medium violations across turns should escalate to blocked."""
        # Turn 1: school steering (medium)
        await middleware.enforce(
            message="The school district is great here",
            contact_id="escalation_test",
        )
        # Turn 2: another school mention (medium)
        await middleware.enforce(
            message="The best schools are in this area",
            contact_id="escalation_test",
        )
        # Turn 3: should trigger conversation-level escalation
        result = await middleware.enforce(
            message="The top rated school is right down the street",
            contact_id="escalation_test",
        )
        assert result.status == ComplianceStatus.BLOCKED
        assert any("cumulative" in v.explanation for v in result.violations)

    @pytest.mark.asyncio
    async def test_clear_history_resets(self, middleware):
        await middleware.enforce(
            message="Good schools here",
            contact_id="clear_test",
        )
        middleware.clear_history("clear_test")
        result = await middleware.enforce(
            message="The property has a nice yard",
            contact_id="clear_test",
        )
        assert result.status == ComplianceStatus.PASSED


# ---------------------------------------------------------------------------
# Safe Alternatives
# ---------------------------------------------------------------------------


class TestSafeAlternatives:
    @pytest.mark.asyncio
    async def test_blocked_seller_gets_safe_alternative(self, middleware):
        result = await middleware.enforce(
            message="That bad area of town is dangerous",
            contact_id="c60",
            mode="seller",
        )
        assert result.status == ComplianceStatus.BLOCKED
        assert result.safe_alternative is not None
        assert "property" in result.safe_alternative.lower()

    @pytest.mark.asyncio
    async def test_blocked_buyer_gets_safe_alternative(self, middleware):
        result = await middleware.enforce(
            message="This is a safe neighborhood with no kids",
            contact_id="c61",
            mode="buyer",
        )
        assert result.status == ComplianceStatus.BLOCKED
        assert result.safe_alternative is not None
        assert "home" in result.safe_alternative.lower() or "neighborhood" in result.safe_alternative.lower()

    @pytest.mark.asyncio
    async def test_passed_message_no_alternative(self, middleware):
        result = await middleware.enforce(
            message="The kitchen was recently renovated",
            contact_id="c62",
        )
        assert result.safe_alternative is None


# ---------------------------------------------------------------------------
# Risk Score
# ---------------------------------------------------------------------------


class TestRiskScore:
    @pytest.mark.asyncio
    async def test_critical_violation_max_risk(self, middleware):
        result = await middleware.enforce(
            message="I'll give you a referral fee kickback",
            contact_id="c70",
        )
        assert result.risk_score >= 0.9

    @pytest.mark.asyncio
    async def test_no_violation_zero_risk(self, middleware):
        result = await middleware.enforce(
            message="Hello, how can I help you today?",
            contact_id="c71",
        )
        assert result.risk_score == 0.0

    @pytest.mark.asyncio
    async def test_risk_score_bounded(self, middleware):
        result = await middleware.enforce(
            message="Avoid that bad area, it's dangerous, not safe, sold out in that area",
            contact_id="c72",
        )
        assert 0.0 <= result.risk_score <= 1.0