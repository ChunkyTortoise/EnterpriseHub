"""
Test Webhook Validators
"""

import pytest
import hashlib
import hmac
import os
from unittest.mock import patch

from ghl_integration.validators import WebhookValidator, MultiValidator


class TestWebhookValidator:
    """Test suite for webhook signature validation"""

    @pytest.fixture
    def validator(self):
        return WebhookValidator()

    def test_init_reads_env_vars(self):
        """Test that validator reads environment variables"""
        with patch.dict(os.environ, {
            "GHL_WEBHOOK_SECRET": "test_secret",
            "GHL_WEBHOOK_PUBLIC_KEY": "test_key",
            "GHL_SKIP_SIGNATURE_VERIFICATION": "true"
        }):
            validator = WebhookValidator()
            assert validator.hmac_secret == "test_secret"
            assert validator.rsa_public_key == "test_key"
            assert validator.skip_in_dev is True

    @pytest.mark.asyncio
    async def test_validate_hmac_success(self, validator):
        """Test successful HMAC validation"""
        with patch.dict(os.environ, {"GHL_WEBHOOK_SECRET": "my_secret"}):
            payload = b'{"test": "data"}'
            expected_sig = hmac.new(
                b"my_secret",
                payload,
                hashlib.sha256
            ).hexdigest()
            
            is_valid = await validator.validate(payload, expected_sig, {}, "hmac")
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_hmac_with_prefix(self, validator):
        """Test HMAC validation with sha256= prefix"""
        with patch.dict(os.environ, {"GHL_WEBHOOK_SECRET": "my_secret"}):
            payload = b'{"test": "data"}'
            expected_sig = "sha256=" + hmac.new(
                b"my_secret",
                payload,
                hashlib.sha256
            ).hexdigest()
            
            is_valid = await validator.validate(payload, expected_sig, {}, "hmac")
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_hmac_invalid(self, validator):
        """Test failed HMAC validation"""
        with patch.dict(os.environ, {"GHL_WEBHOOK_SECRET": "my_secret"}):
            payload = b'{"test": "data"}'
            invalid_sig = "wrong_signature"
            
            is_valid = await validator.validate(payload, invalid_sig, {}, "hmac")
            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_missing_secret(self, validator):
        """Test validation when secret is not configured"""
        with patch.dict(os.environ, {}, clear=True):
            payload = b'{"test": "data"}'
            
            is_valid = await validator.validate(payload, "some_sig", {}, "hmac")
            assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_auto_detect_hmac(self, validator):
        """Test automatic scheme detection for HMAC"""
        with patch.dict(os.environ, {"GHL_WEBHOOK_SECRET": "my_secret"}):
            payload = b'{"test": "data"}'
            sig = hmac.new(b"my_secret", payload, hashlib.sha256).hexdigest()
            
            is_valid = await validator.validate(payload, sig, {}, "auto")
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_dev_mode_skip(self, validator):
        """Test signature skip in dev mode"""
        with patch.dict(os.environ, {
            "GHL_WEBHOOK_SECRET": "my_secret",
            "GHL_SKIP_SIGNATURE_VERIFICATION": "true"
        }):
            payload = b'{"test": "data"}'
            
            is_valid = await validator.validate(payload, None, {}, "hmac")
            assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_timestamp_valid(self, validator):
        """Test valid timestamp validation"""
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        timestamp = now.isoformat()
        
        is_valid = await validator.validate_timestamp(timestamp, max_age_seconds=300)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_timestamp_expired(self, validator):
        """Test expired timestamp validation"""
        from datetime import datetime, timezone, timedelta
        
        old_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        timestamp = old_time.isoformat()
        
        is_valid = await validator.validate_timestamp(timestamp, max_age_seconds=300)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_timestamp_future(self, validator):
        """Test future timestamp validation"""
        from datetime import datetime, timezone, timedelta
        
        future_time = datetime.now(timezone.utc) + timedelta(minutes=2)
        timestamp = future_time.isoformat()
        
        is_valid = await validator.validate_timestamp(timestamp, max_age_seconds=300)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_timestamp_with_z(self, validator):
        """Test timestamp with Z suffix"""
        from datetime import datetime, timezone
        
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        is_valid = await validator.validate_timestamp(timestamp, max_age_seconds=300)
        assert is_valid is True


class TestMultiValidator:
    """Test suite for multi-layer validation"""

    @pytest.fixture
    def multi_validator(self):
        return MultiValidator()

    @pytest.mark.asyncio
    async def test_full_validation_success(self, multi_validator):
        """Test successful full validation"""
        with patch.dict(os.environ, {"GHL_WEBHOOK_SECRET": "test_secret"}):
            payload = b'{"test": "data"}'
            sig = hmac.new(b"test_secret", payload, hashlib.sha256).hexdigest()
            
            result = await multi_validator.validate(
                payload, sig, {"X-GHL-Timestamp": "2026-02-11T10:00:00Z"}
            )
            
            assert result["valid"] is True
            assert result["signature_valid"] is True
            assert result["timestamp_valid"] is True
            assert result["source_valid"] is True
            assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_full_validation_invalid_signature(self, multi_validator):
        """Test full validation with invalid signature"""
        with patch.dict(os.environ, {"GHL_WEBHOOK_SECRET": "test_secret"}):
            payload = b'{"test": "data"}'
            
            result = await multi_validator.validate(
                payload, "invalid_sig", {"X-GHL-Timestamp": "2026-02-11T10:00:00Z"}
            )
            
            assert result["valid"] is False
            assert result["signature_valid"] is False
            assert "Invalid signature" in result["errors"]

    @pytest.mark.asyncio
    async def test_full_validation_invalid_ip(self, multi_validator):
        """Test full validation with invalid IP"""
        with patch.dict(os.environ, {
            "GHL_WEBHOOK_SECRET": "test_secret",
            "GHL_ALLOWED_IPS": "1.2.3.4,5.6.7.8"
        }):
            multi_validator = MultiValidator()  # Re-init with new env
            
            payload = b'{"test": "data"}'
            sig = hmac.new(b"test_secret", payload, hashlib.sha256).hexdigest()
            
            result = await multi_validator.validate(
                payload, sig, 
                {"X-GHL-Timestamp": "2026-02-11T10:00:00Z"},
                client_ip="9.10.11.12"
            )
            
            assert result["valid"] is False
            assert result["source_valid"] is False

    @pytest.mark.asyncio
    async def test_full_validation_valid_ip(self, multi_validator):
        """Test full validation with valid IP"""
        with patch.dict(os.environ, {
            "GHL_WEBHOOK_SECRET": "test_secret",
            "GHL_ALLOWED_IPS": "1.2.3.4,5.6.7.8"
        }):
            multi_validator = MultiValidator()  # Re-init with new env
            
            payload = b'{"test": "data"}'
            sig = hmac.new(b"test_secret", payload, hashlib.sha256).hexdigest()
            
            result = await multi_validator.validate(
                payload, sig,
                {"X-GHL-Timestamp": "2026-02-11T10:00:00Z"},
                client_ip="1.2.3.4"
            )
            
            assert result["source_valid"] is True
