"""
Test State Synchronization
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ghl_integration.state_sync import (
    GHLStateSynchronizer,
    SyncDirection,
    SyncStatus,
    get_synchronizer,
)


class TestGHLStateSynchronizer:
    """Test suite for bidirectional state synchronization"""

    @pytest.fixture
    def sync(self, mock_ghl_client):
        with patch("ghl_integration.state_sync.GHLAPIClient", return_value=mock_ghl_client):
            sync = GHLStateSynchronizer()
            sync.ghl_client = mock_ghl_client
            return sync

    @pytest.mark.asyncio
    async def test_sync_contact_from_ghl_success(self, sync, mock_cache_service):
        """Test successful sync from GHL to local"""
        sync.cache = mock_cache_service

        with patch("ghl_integration.state_sync._get_local_contact", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"first_name": "Old", "email": "old@example.com"}
            with patch("ghl_integration.state_sync._update_local_contact", new_callable=AsyncMock) as mock_update:
                result = await sync.sync_contact_from_ghl("contact_123")

                assert result["success"] is True
                assert result["contact_id"] == "contact_123"
                mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_contact_from_ghl_fetch_fails(self, sync, mock_ghl_client):
        """Test sync when GHL fetch fails"""
        mock_ghl_client.get_contact.return_value = {"success": False, "error": "Contact not found"}

        result = await sync.sync_contact_from_ghl("contact_123")

        assert result["success"] is False
        assert "Failed to fetch from GHL" in result["error"]

    @pytest.mark.asyncio
    async def test_sync_contact_from_ghl_concurrent_sync_prevention(self, sync, mock_cache_service):
        """Test that concurrent syncs are prevented"""
        sync.cache = mock_cache_service
        sync._sync_in_progress.add("contact_123")

        result = await sync.sync_contact_from_ghl("contact_123")

        assert result["success"] is False
        assert "Sync already in progress" in result["error"]

    @pytest.mark.asyncio
    async def test_sync_contact_to_ghl_success(self, sync, mock_cache_service):
        """Test successful sync from local to GHL"""
        sync.cache = mock_cache_service

        with patch("ghl_integration.state_sync._get_local_contact", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"ai_lead_score": 85, "lead_temperature": "hot", "buyer_score": 70}

            result = await sync.sync_contact_to_ghl("contact_123")

            assert result["success"] is True
            assert result["contact_id"] == "contact_123"
            sync.ghl_client.update_contact.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_contact_to_ghl_not_found_local(self, sync, mock_cache_service):
        """Test sync when local contact not found"""
        sync.cache = mock_cache_service

        with patch("ghl_integration.state_sync._get_local_contact", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await sync.sync_contact_to_ghl("contact_123")

            assert result["success"] is False
            assert "Contact not found in local database" in result["error"]

    @pytest.mark.asyncio
    async def test_sync_contact_to_ghl_update_fails(self, sync, mock_cache_service, mock_ghl_client):
        """Test sync when GHL update fails"""
        sync.cache = mock_cache_service
        mock_ghl_client.update_contact.return_value = {"success": False, "error": "API Error"}

        with patch("ghl_integration.state_sync._get_local_contact", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"ai_lead_score": 85}

            result = await sync.sync_contact_to_ghl("contact_123")

            assert result["success"] is False
            assert "GHL update failed" in result["error"]

    @pytest.mark.asyncio
    async def test_sync_pipeline_stage_local_source(self, sync):
        """Test pipeline stage sync from local source"""
        result = await sync.sync_pipeline_stage("contact_123", "stage_qualified", source="local")

        assert result["success"] is True
        assert "queued" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_sync_pipeline_stage_ghl_source(self, sync):
        """Test pipeline stage sync from GHL source"""
        with patch("ghl_integration.state_sync._update_local_stage", new_callable=AsyncMock) as mock_update:
            result = await sync.sync_pipeline_stage("contact_123", "stage_qualified", source="ghl")

            assert result["success"] is True
            assert result["pipeline_stage"] == "stage_qualified"
            mock_update.assert_called_once_with("contact_123", "stage_qualified")

    def test_resolve_conflict_last_write_wins_ghl_newer(self, sync):
        """Test conflict resolution when GHL data is newer"""
        ghl_data = {"firstName": "New", "dateUpdated": "2026-02-11T12:00:00Z"}
        local_data = {"first_name": "Old", "updated_at": "2026-02-11T10:00:00Z"}

        result = sync.resolve_conflict("contact_123", ghl_data, local_data, "last_write_wins")

        assert result["success"] is True
        assert result["winner"] == "ghl"
        assert result["resolution"] == ghl_data

    def test_resolve_conflict_last_write_wins_local_newer(self, sync):
        """Test conflict resolution when local data is newer"""
        ghl_data = {"firstName": "Old", "dateUpdated": "2026-02-11T10:00:00Z"}
        local_data = {"first_name": "New", "updated_at": "2026-02-11T12:00:00Z"}

        result = sync.resolve_conflict("contact_123", ghl_data, local_data, "last_write_wins")

        assert result["success"] is True
        assert result["winner"] == "local"
        assert result["resolution"] == local_data

    def test_resolve_conflict_ghl_wins(self, sync):
        """Test conflict resolution with ghl_wins strategy"""
        ghl_data = {"firstName": "GHL"}
        local_data = {"first_name": "Local"}

        result = sync.resolve_conflict("contact_123", ghl_data, local_data, "ghl_wins")

        assert result["winner"] == "ghl"
        assert result["resolution"] == ghl_data

    def test_resolve_conflict_local_wins(self, sync):
        """Test conflict resolution with local_wins strategy"""
        ghl_data = {"firstName": "GHL"}
        local_data = {"first_name": "Local"}

        result = sync.resolve_conflict("contact_123", ghl_data, local_data, "local_wins")

        assert result["winner"] == "local"
        assert result["resolution"] == local_data

    def test_resolve_conflict_merge(self, sync):
        """Test conflict resolution with merge strategy"""
        ghl_data = {"firstName": "GHL", "field1": "value1"}
        local_data = {"first_name": "Local", "field2": "value2"}

        result = sync.resolve_conflict("contact_123", ghl_data, local_data, "merge")

        assert result["winner"] == "merged"
        # Merged should have both fields (local overwrites GHL on overlap)
        assert "field1" in result["resolution"]
        assert "field2" in result["resolution"]

    def test_resolve_conflict_unknown_strategy(self, sync):
        """Test conflict resolution with unknown strategy"""
        result = sync.resolve_conflict("contact_123", {}, {}, "unknown")

        assert result["success"] is False
        assert "Unknown strategy" in result["error"]

    @pytest.mark.asyncio
    async def test_perform_full_sync_success(self, sync, mock_cache_service):
        """Test full sync for multiple contacts"""
        sync.cache = mock_cache_service

        with patch("ghl_integration.state_sync._get_contacts_needing_sync", new_callable=AsyncMock) as mock_get_ids:
            mock_get_ids.return_value = ["contact_1", "contact_2", "contact_3"]
            with patch.object(sync, "sync_contact_from_ghl", new_callable=AsyncMock) as mock_sync:
                mock_sync.return_value = {"success": True}

                result = await sync.perform_full_sync()

                assert result["total"] == 3
                assert result["successful"] == 3
                assert result["failed"] == 0
                assert len(result["details"]) == 3

    @pytest.mark.asyncio
    async def test_perform_full_sync_partial_failure(self, sync, mock_cache_service):
        """Test full sync with some failures"""
        sync.cache = mock_cache_service

        with patch("ghl_integration.state_sync._get_contacts_needing_sync", new_callable=AsyncMock) as mock_get_ids:
            mock_get_ids.return_value = ["contact_1", "contact_2"]
            with patch.object(sync, "sync_contact_from_ghl", new_callable=AsyncMock) as mock_sync:
                mock_sync.side_effect = [{"success": True}, {"success": False, "error": "Failed"}]

                result = await sync.perform_full_sync()

                assert result["total"] == 2
                assert result["successful"] == 1
                assert result["failed"] == 1

    @pytest.mark.asyncio
    async def test_get_sync_status(self, sync, mock_cache_service):
        """Test getting sync status for a contact"""
        sync.cache = mock_cache_service
        mock_cache_service.get.side_effect = [
            "2026-02-11T10:00:00Z",  # ghl_to_local
            "2026-02-11T11:00:00Z",  # local_to_ghl
        ]

        result = await sync.get_sync_status("contact_123")

        assert result["contact_id"] == "contact_123"
        assert result["last_ghl_to_local"] == "2026-02-11T10:00:00Z"
        assert result["last_local_to_ghl"] == "2026-02-11T11:00:00Z"
        assert result["sync_in_progress"] is False

    def test_get_changed_fields_with_differences(self, sync):
        """Test detecting changed fields"""
        ghl_data = {"firstName": "New", "lastName": "Name", "email": "new@example.com", "phone": "+1-555-0100"}
        local_data = {"first_name": "Old", "last_name": "Name", "email": "old@example.com", "phone": "+1-555-0100"}

        changed = sync._get_changed_fields(ghl_data, local_data)

        assert "firstName" in changed
        assert "email" in changed
        assert "lastName" not in changed  # Same value
        assert "phone" not in changed  # Same value

    def test_get_changed_fields_no_local(self, sync):
        """Test getting all fields when no local data exists"""
        ghl_data = {"firstName": "Test", "email": "test@example.com"}

        changed = sync._get_changed_fields(ghl_data, None)

        assert len(changed) == len(sync.GHL_TO_LOCAL_FIELDS)

    def test_map_ghl_to_local(self, sync):
        """Test field name mapping from GHL to local"""
        ghl_data = {"firstName": "John", "lastName": "Smith", "postalCode": "91730"}
        fields = ["firstName", "lastName", "postalCode"]

        result = sync._map_ghl_to_local(ghl_data, fields)

        assert result["first_name"] == "John"
        assert result["last_name"] == "Smith"
        assert result["zip_code"] == "91730"  # postalCode -> zip_code

    def test_map_local_to_ghl(self, sync):
        """Test field name mapping from local to GHL"""
        local_data = {
            "ai_lead_score": 85,
            "lead_temperature": "hot",
            "custom_field": "ignored",  # Not in sync list
        }

        result = sync._map_local_to_ghl(local_data)

        assert "customFields" in result
        # Only whitelisted fields should be included
        assert any(cf["key"] == "ai_lead_score" for cf in result["customFields"])
        assert any(cf["key"] == "lead_temperature" for cf in result["customFields"])

    def test_parse_timestamp_iso(self, sync):
        """Test parsing ISO timestamp"""
        ts = "2026-02-11T10:30:00+00:00"

        result = sync._parse_timestamp(ts)

        assert isinstance(result, datetime)
        assert result.year == 2026

    def test_parse_timestamp_with_z(self, sync):
        """Test parsing timestamp with Z suffix"""
        ts = "2026-02-11T10:30:00Z"

        result = sync._parse_timestamp(ts)

        assert isinstance(result, datetime)

    def test_parse_timestamp_invalid(self, sync):
        """Test parsing invalid timestamp"""
        result = sync._parse_timestamp("invalid")

        assert result is None


class TestSyncEnums:
    """Test sync enumeration values"""

    def test_sync_direction_values(self):
        """Test SyncDirection enum values"""
        assert SyncDirection.GHL_TO_LOCAL.value == "ghl_to_local"
        assert SyncDirection.LOCAL_TO_GHL.value == "local_to_ghl"
        assert SyncDirection.BIDIRECTIONAL.value == "bidirectional"

    def test_sync_status_values(self):
        """Test SyncStatus enum values"""
        assert SyncStatus.PENDING.value == "pending"
        assert SyncStatus.IN_PROGRESS.value == "in_progress"
        assert SyncStatus.SUCCESS.value == "success"
        assert SyncStatus.FAILED.value == "failed"
        assert SyncStatus.CONFLICT.value == "conflict"


class TestSynchronizerSingleton:
    """Test singleton pattern for synchronizer"""

    def test_get_synchronizer_creates_instance(self):
        """Test that get_synchronizer creates instance"""
        with patch("ghl_integration.state_sync.GHLStateSynchronizer") as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance

            result = get_synchronizer()

            assert result is mock_instance

    def test_get_synchronizer_returns_same_instance(self):
        """Test that get_synchronizer returns same instance"""
        with patch("ghl_integration.state_sync.GHLStateSynchronizer") as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance

            result1 = get_synchronizer()
            result2 = get_synchronizer()

            assert result1 is result2
            mock_class.assert_called_once()  # Only created once
