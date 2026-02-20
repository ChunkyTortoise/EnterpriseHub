"""Regression tests for lead_bot_management route contract alignment."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from ghl_real_estate_ai.api.routes.lead_bot_management import (
    CreateSequenceRequest,
    cancel_sequence,
    create_sequence,
    get_sequence_status,
    pause_sequence,
    resume_sequence,
)
from ghl_real_estate_ai.services.lead_sequence_state_service import LeadSequenceState, SequenceDay, SequenceStatus

pytestmark = pytest.mark.asyncio


async def test_create_sequence_uses_service_contract_with_create_sequence():
    """Regression: route should use sequence_service.create_sequence contract and schedule requested start day."""
    now = datetime.now(timezone.utc)
    sequence_state = LeadSequenceState(
        lead_id="lead_123",
        current_day=SequenceDay.INITIAL,
        sequence_status=SequenceStatus.PENDING,
        sequence_started_at=now,
    )

    sequence_service = MagicMock()
    sequence_service.create_sequence = AsyncMock(return_value=sequence_state)
    sequence_service.save_state = AsyncMock(return_value=True)

    lead_scheduler = MagicMock()
    lead_scheduler.enabled = True
    lead_scheduler.schedule_sequence_start = AsyncMock(return_value=True)

    request = CreateSequenceRequest(
        lead_id="lead_123",
        lead_name="Jordan",
        phone="+15555550123",
        email="lead@example.com",
        start_delay_minutes=0,
    )

    with patch(
        "ghl_real_estate_ai.api.routes.lead_bot_management.get_sequence_service",
        return_value=sequence_service,
    ), patch(
        "ghl_real_estate_ai.api.routes.lead_bot_management.get_lead_scheduler",
        return_value=lead_scheduler,
    ):
        response = await create_sequence(request, scheduler_service=MagicMock(), _auth=True)

    assert response.success is True
    assert response.sequence_id == "lead_123"
    sequence_service.create_sequence.assert_awaited_once_with("lead_123", initial_day=SequenceDay.INITIAL)
    lead_scheduler.schedule_sequence_start.assert_awaited_once_with(
        lead_id="lead_123",
        sequence_day=SequenceDay.INITIAL,
        delay_minutes=0,
    )


async def test_get_sequence_status_maps_sequence_status_and_started_at_fields():
    """Regression: route should map sequence_status/sequence_started_at from service state."""
    started_at = datetime(2026, 2, 17, 15, 0, tzinfo=timezone.utc)
    state = LeadSequenceState(
        lead_id="lead_456",
        current_day=SequenceDay.DAY_7,
        sequence_status=SequenceStatus.IN_PROGRESS,
        sequence_started_at=started_at,
    )

    sequence_service = MagicMock()
    sequence_service.get_state = AsyncMock(return_value=state)

    with patch(
        "ghl_real_estate_ai.api.routes.lead_bot_management.get_sequence_service",
        return_value=sequence_service,
    ):
        response = await get_sequence_status("lead_456", _auth=True)

    assert response.status == "in_progress"
    assert response.current_day == "day_7"
    assert response.sequence_started_at == started_at.isoformat()


@pytest.mark.parametrize(
    "route_fn,service_method,service_args",
    [
        (pause_sequence, "pause_sequence", ("lead_999",)),
        (resume_sequence, "resume_sequence", ("lead_999",)),
        (cancel_sequence, "complete_sequence", ("lead_999", "cancelled")),
    ],
)
async def test_sequence_control_routes_map_tuple_success(route_fn, service_method, service_args):
    """Regression: pause/resume/cancel should treat tuple success as HTTP 200."""
    sequence_service = MagicMock()
    setattr(sequence_service, service_method, AsyncMock(return_value=(True, None)))

    with patch(
        "ghl_real_estate_ai.api.routes.lead_bot_management.get_sequence_service",
        return_value=sequence_service,
    ):
        response = await route_fn("lead_999", _auth=True)

    assert response["success"] is True


@pytest.mark.parametrize(
    "route_fn,service_method,service_args",
    [
        (pause_sequence, "pause_sequence", ("lead_missing",)),
        (resume_sequence, "resume_sequence", ("lead_missing",)),
        (cancel_sequence, "complete_sequence", ("lead_missing", "cancelled")),
    ],
)
async def test_sequence_control_routes_map_missing_state_to_404(route_fn, service_method, service_args):
    """Regression: tuple error with no state should become 404 for pause/resume/cancel."""
    sequence_service = MagicMock()
    setattr(
        sequence_service,
        service_method,
        AsyncMock(return_value=(False, "No sequence state found for lead lead_missing")),
    )

    with patch(
        "ghl_real_estate_ai.api.routes.lead_bot_management.get_sequence_service",
        return_value=sequence_service,
    ):
        with pytest.raises(HTTPException) as exc:
            await route_fn("lead_missing", _auth=True)

    assert exc.value.status_code == 404


@pytest.mark.parametrize(
    "route_fn,service_method,service_args",
    [
        (pause_sequence, "pause_sequence", ("lead_bad",)),
        (resume_sequence, "resume_sequence", ("lead_bad",)),
        (cancel_sequence, "complete_sequence", ("lead_bad", "cancelled")),
    ],
)
async def test_sequence_control_routes_map_validation_errors_to_400(route_fn, service_method, service_args):
    """Regression: tuple error other than missing state should become 400 for pause/resume/cancel."""
    sequence_service = MagicMock()
    setattr(sequence_service, service_method, AsyncMock(return_value=(False, "Invalid status transition")))

    with patch(
        "ghl_real_estate_ai.api.routes.lead_bot_management.get_sequence_service",
        return_value=sequence_service,
    ):
        with pytest.raises(HTTPException) as exc:
            await route_fn("lead_bad", _auth=True)

    assert exc.value.status_code == 400
