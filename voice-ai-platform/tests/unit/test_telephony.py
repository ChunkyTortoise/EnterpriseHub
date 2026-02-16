"""Unit tests for telephony components (TwilioHandler, CallManager)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from voice_ai.telephony.twilio_handler import TwilioHandler
from voice_ai.telephony.call_manager import CallManager, VALID_TRANSITIONS
from voice_ai.models.call import Call, CallStatus, CallDirection


class TestTwilioHandler:
    """Test Twilio integration handler."""

    @pytest.fixture
    def handler(self):
        """Create a TwilioHandler instance."""
        return TwilioHandler(
            account_sid="test_sid",
            auth_token="test_token",
            base_url="example.com",
            phone_number="+15551234567",
        )

    def test_generate_stream_twiml_contains_websocket_url(self, handler):
        """Test that TwiML contains the correct WebSocket URL."""
        call_id = "test_call_123"
        twiml = handler.generate_stream_twiml(call_id)

        assert "wss://example.com/api/v1/voice/ws" in twiml
        assert "<Connect>" in twiml
        assert "<Stream" in twiml

    @pytest.mark.asyncio
    async def test_initiate_outbound_call_returns_sid(self, handler):
        """Test that initiating an outbound call returns a Twilio SID."""
        with patch("twilio.rest.Client") as mock_client_class:
            mock_client = MagicMock()
            mock_call = MagicMock(sid="CA123456", status="initiated")
            mock_client.calls.create.return_value = mock_call
            mock_client_class.return_value = mock_client

            result = await handler.initiate_outbound_call(
                to_number="+15559876543",
                from_number="+15551234567",
                call_id="test_call",
            )

            assert result["call_sid"] == "CA123456"
            assert result["status"] == "initiated"
            mock_client.calls.create.assert_called_once()

    def test_decode_twilio_audio_converts_mulaw_to_pcm(self, handler):
        """Test that audio decoding converts mulaw 8kHz to linear16 16kHz."""
        import base64
        import audioop

        # Create fake mulaw audio
        fake_pcm = b"\x00\x01" * 100  # 200 bytes of PCM
        fake_mulaw = audioop.lin2ulaw(fake_pcm, 2)
        encoded_payload = base64.b64encode(fake_mulaw).decode("ascii")

        decoded = handler.decode_twilio_audio(encoded_payload)

        # Should return PCM data (upsampled to 16kHz)
        assert isinstance(decoded, bytes)
        assert len(decoded) > 0

    def test_encode_audio_for_twilio_converts_pcm_to_mulaw(self, handler):
        """Test that audio encoding converts linear16 16kHz to mulaw 8kHz."""
        fake_pcm_16k = b"\x00\x01" * 100  # 200 bytes of PCM at 16kHz

        encoded = handler.encode_audio_for_twilio(fake_pcm_16k)

        # Should return base64-encoded mulaw
        assert isinstance(encoded, str)
        import base64

        base64.b64decode(encoded)  # Should not raise

    def test_validate_twilio_signature_with_valid_signature(self, handler):
        """Test that Twilio signature validation works for valid requests."""
        with patch("twilio.request_validator.RequestValidator") as mock_validator_class:
            mock_validator = MagicMock()
            mock_validator.validate.return_value = True
            mock_validator_class.return_value = mock_validator

            url = "https://example.com/webhook"
            params = {"CallSid": "CA123", "From": "+15551234567"}
            signature = "valid_signature"

            is_valid = handler.validate_twilio_signature(url, params, signature)

            assert is_valid is True
            mock_validator.validate.assert_called_once_with(url, params, signature)

    def test_validate_twilio_signature_with_invalid_signature(self, handler):
        """Test that Twilio signature validation rejects invalid requests."""
        with patch("twilio.request_validator.RequestValidator") as mock_validator_class:
            mock_validator = MagicMock()
            mock_validator.validate.return_value = False
            mock_validator_class.return_value = mock_validator

            url = "https://example.com/webhook"
            params = {"CallSid": "CA123"}
            signature = "invalid_signature"

            is_valid = handler.validate_twilio_signature(url, params, signature)

            assert is_valid is False


class TestCallManager:
    """Test call lifecycle management."""

    @pytest.fixture
    def mock_db(self):
        """Mock async database session."""
        db = AsyncMock()
        # Mock flush and execute
        db.flush = AsyncMock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def manager(self, mock_db):
        """Create a CallManager with mocked database."""
        return CallManager(db_session=mock_db)

    @pytest.mark.asyncio
    async def test_create_call_returns_call_object(self, manager, mock_db):
        """Test that creating a call returns a Call object with correct fields."""
        tenant_id = str(uuid.uuid4())
        call = await manager.create_call(
            tenant_id=tenant_id,
            direction="inbound",
            from_number="+15551234567",
            to_number="+15559876543",
            bot_type="lead",
            twilio_call_sid="CA123456",
        )

        assert isinstance(call, Call)
        assert call.tenant_id == uuid.UUID(tenant_id)
        assert call.direction == CallDirection.INBOUND
        assert call.from_number == "+15551234567"
        assert call.to_number == "+15559876543"
        assert call.bot_type == "lead"
        assert call.status == CallStatus.INITIATED
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_status_validates_state_transitions(self, manager, mock_db):
        """Test that status updates respect the state machine."""
        call_id = uuid.uuid4()
        existing_call = Call(
            id=call_id,
            tenant_id=uuid.uuid4(),
            direction=CallDirection.INBOUND,
            from_number="+15551234567",
            to_number="+15559876543",
            status=CallStatus.INITIATED,
        )

        # Mock the database query to return the existing call
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_call
        mock_db.execute.return_value = mock_result

        # Valid transition: initiated -> ringing
        updated = await manager.update_status(str(call_id), CallStatus.RINGING)

        assert updated is not None
        assert updated.status == CallStatus.RINGING

    @pytest.mark.asyncio
    async def test_update_status_rejects_invalid_transitions(self, manager, mock_db):
        """Test that invalid status transitions are rejected."""
        call_id = uuid.uuid4()
        existing_call = Call(
            id=call_id,
            tenant_id=uuid.uuid4(),
            direction=CallDirection.INBOUND,
            from_number="+15551234567",
            to_number="+15559876543",
            status=CallStatus.COMPLETED,  # Terminal state
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_call
        mock_db.execute.return_value = mock_result

        # Invalid transition: completed -> ringing (completed is terminal)
        updated = await manager.update_status(str(call_id), CallStatus.RINGING)

        assert updated is None  # Transition rejected

    @pytest.mark.asyncio
    async def test_update_status_sets_ended_at_for_terminal_states(self, manager, mock_db):
        """Test that ended_at is set when call reaches terminal state."""
        call_id = uuid.uuid4()
        existing_call = Call(
            id=call_id,
            tenant_id=uuid.uuid4(),
            direction=CallDirection.INBOUND,
            from_number="+15551234567",
            to_number="+15559876543",
            status=CallStatus.IN_PROGRESS,
            created_at=datetime.now(timezone.utc),
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_call
        mock_db.execute.return_value = mock_result

        updated = await manager.update_status(str(call_id), CallStatus.COMPLETED)

        assert updated.ended_at is not None
        assert updated.duration_seconds > 0

    @pytest.mark.asyncio
    async def test_get_call_returns_call_by_id(self, manager, mock_db):
        """Test fetching a call by ID."""
        call_id = uuid.uuid4()
        expected_call = Call(
            id=call_id,
            tenant_id=uuid.uuid4(),
            direction=CallDirection.INBOUND,
            from_number="+15551234567",
            to_number="+15559876543",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_call
        mock_db.execute.return_value = mock_result

        call = await manager.get_call(str(call_id))

        assert call == expected_call

    @pytest.mark.asyncio
    async def test_get_call_by_sid_returns_call(self, manager, mock_db):
        """Test fetching a call by Twilio SID."""
        twilio_sid = "CA123456"
        expected_call = Call(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            direction=CallDirection.INBOUND,
            from_number="+15551234567",
            to_number="+15559876543",
            twilio_call_sid=twilio_sid,
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = expected_call
        mock_db.execute.return_value = mock_result

        call = await manager.get_call_by_sid(twilio_sid)

        assert call == expected_call
        assert call.twilio_call_sid == twilio_sid

    @pytest.mark.asyncio
    async def test_list_calls_filters_by_tenant(self, manager, mock_db):
        """Test listing calls filters by tenant ID."""
        tenant_id = uuid.uuid4()
        calls = [
            Call(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                direction=CallDirection.INBOUND,
                from_number="+15551234567",
                to_number="+15559876543",
            )
            for _ in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = calls
        mock_db.execute.return_value = mock_result

        result = await manager.list_calls(str(tenant_id))

        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_update_call_costs_updates_cost_fields(self, manager, mock_db):
        """Test that cost tracking fields are updated correctly."""
        call_id = uuid.uuid4()
        existing_call = Call(
            id=call_id,
            tenant_id=uuid.uuid4(),
            direction=CallDirection.INBOUND,
            from_number="+15551234567",
            to_number="+15559876543",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_call
        mock_db.execute.return_value = mock_result

        await manager.update_call_costs(
            str(call_id),
            cost_stt=0.05,
            cost_tts=0.10,
            cost_llm=0.15,
            cost_telephony=0.02,
        )

        assert existing_call.cost_stt == 0.05
        assert existing_call.cost_tts == 0.10
        assert existing_call.cost_llm == 0.15
        assert existing_call.cost_telephony == 0.02
        mock_db.flush.assert_called_once()


def test_valid_transitions_state_machine():
    """Test that the state machine has valid transitions."""
    # INITIATED can transition to RINGING or FAILED
    assert CallStatus.RINGING in VALID_TRANSITIONS[CallStatus.INITIATED]
    assert CallStatus.FAILED in VALID_TRANSITIONS[CallStatus.INITIATED]

    # RINGING can transition to IN_PROGRESS, NO_ANSWER, or FAILED
    assert CallStatus.IN_PROGRESS in VALID_TRANSITIONS[CallStatus.RINGING]
    assert CallStatus.NO_ANSWER in VALID_TRANSITIONS[CallStatus.RINGING]

    # IN_PROGRESS can transition to COMPLETED or FAILED
    assert CallStatus.COMPLETED in VALID_TRANSITIONS[CallStatus.IN_PROGRESS]
    assert CallStatus.FAILED in VALID_TRANSITIONS[CallStatus.IN_PROGRESS]

    # Terminal states have no outgoing transitions
    assert len(VALID_TRANSITIONS[CallStatus.COMPLETED]) == 0
    assert len(VALID_TRANSITIONS[CallStatus.FAILED]) == 0
    assert len(VALID_TRANSITIONS[CallStatus.NO_ANSWER]) == 0
