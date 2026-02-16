"""Tests for audit logging."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from rag_service.compliance.audit_logger import AuditLogger, AuditEntry


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def audit_logger_with_db(mock_db):
    """Audit logger with database."""
    return AuditLogger(db_session=mock_db)


@pytest.fixture
def audit_logger_no_db():
    """Audit logger without database (buffer mode)."""
    return AuditLogger(db_session=None)


class TestAuditLogger:
    """Test audit logging functionality."""

    async def test_log_audit_event_to_db(self, audit_logger_with_db, mock_db):
        """Test logging audit event to database."""
        # Act
        entry = await audit_logger_with_db.log(
            tenant_id="tenant-123",
            action="document.upload",
            resource_type="document",
            resource_id="doc-456",
            user_id="user-789",
            metadata={"filename": "report.pdf", "size": 1024},
            ip_address="192.168.1.100",
        )

        # Assert
        assert isinstance(entry, AuditEntry)
        assert entry.tenant_id == "tenant-123"
        assert entry.action == "document.upload"
        assert entry.resource_type == "document"
        assert entry.resource_id == "doc-456"
        assert entry.user_id == "user-789"
        assert entry.metadata["filename"] == "report.pdf"
        assert entry.ip_address == "192.168.1.100"
        mock_db.execute.assert_called_once()

    async def test_log_audit_event_to_buffer(self, audit_logger_no_db):
        """Test logging audit event to in-memory buffer."""
        # Act
        entry = await audit_logger_no_db.log(
            tenant_id="tenant-123",
            action="query.execute",
            resource_type="query",
        )

        # Assert
        assert isinstance(entry, AuditEntry)
        assert entry.tenant_id == "tenant-123"
        assert entry.action == "query.execute"

        # Should be in buffer
        buffered = audit_logger_no_db.get_buffered_entries()
        assert len(buffered) == 1
        assert buffered[0].id == entry.id

    async def test_multiple_audit_entries(self, audit_logger_no_db):
        """Test logging multiple audit entries."""
        # Act
        await audit_logger_no_db.log(
            tenant_id="tenant-1", action="auth.login", resource_type="session"
        )
        await audit_logger_no_db.log(
            tenant_id="tenant-1", action="document.upload", resource_type="document"
        )
        await audit_logger_no_db.log(
            tenant_id="tenant-2", action="query.execute", resource_type="query"
        )

        # Assert
        buffered = audit_logger_no_db.get_buffered_entries()
        assert len(buffered) == 3
        actions = [e.action for e in buffered]
        assert "auth.login" in actions
        assert "document.upload" in actions
        assert "query.execute" in actions

    async def test_query_logs_by_tenant(self, audit_logger_no_db):
        """Test querying logs filtered by tenant."""
        # Arrange
        await audit_logger_no_db.log(
            tenant_id="tenant-1", action="action1", resource_type="type1"
        )
        await audit_logger_no_db.log(
            tenant_id="tenant-2", action="action2", resource_type="type2"
        )
        await audit_logger_no_db.log(
            tenant_id="tenant-1", action="action3", resource_type="type3"
        )

        # Act
        results = await audit_logger_no_db.query_logs(tenant_id="tenant-1")

        # Assert
        assert len(results) == 2
        assert all(e.tenant_id == "tenant-1" for e in results)

    async def test_query_logs_by_action(self, audit_logger_no_db):
        """Test querying logs filtered by action."""
        # Arrange
        await audit_logger_no_db.log(
            tenant_id="tenant-1", action="document.upload", resource_type="document"
        )
        await audit_logger_no_db.log(
            tenant_id="tenant-1", action="document.delete", resource_type="document"
        )
        await audit_logger_no_db.log(
            tenant_id="tenant-1", action="document.upload", resource_type="document"
        )

        # Act
        results = await audit_logger_no_db.query_logs(
            tenant_id="tenant-1", action="document.upload"
        )

        # Assert
        assert len(results) == 2
        assert all(e.action == "document.upload" for e in results)

    async def test_query_logs_by_resource_type(self, audit_logger_no_db):
        """Test querying logs filtered by resource type."""
        # Arrange
        await audit_logger_no_db.log(
            tenant_id="tenant-1", action="create", resource_type="document"
        )
        await audit_logger_no_db.log(
            tenant_id="tenant-1", action="create", resource_type="collection"
        )
        await audit_logger_no_db.log(
            tenant_id="tenant-1", action="delete", resource_type="document"
        )

        # Act
        results = await audit_logger_no_db.query_logs(
            tenant_id="tenant-1", resource_type="document"
        )

        # Assert
        assert len(results) == 2
        assert all(e.resource_type == "document" for e in results)

    async def test_query_logs_with_limit(self, audit_logger_no_db):
        """Test querying logs with result limit."""
        # Arrange
        for i in range(10):
            await audit_logger_no_db.log(
                tenant_id="tenant-1",
                action=f"action{i}",
                resource_type="test",
            )

        # Act
        results = await audit_logger_no_db.query_logs(tenant_id="tenant-1", limit=5)

        # Assert
        assert len(results) == 5

    async def test_clear_buffer(self, audit_logger_no_db):
        """Test clearing the audit buffer."""
        # Arrange
        await audit_logger_no_db.log(
            tenant_id="tenant-1", action="test", resource_type="test"
        )
        assert len(audit_logger_no_db.get_buffered_entries()) == 1

        # Act
        audit_logger_no_db.clear_buffer()

        # Assert
        assert len(audit_logger_no_db.get_buffered_entries()) == 0

    async def test_audit_entry_has_timestamp(self, audit_logger_no_db):
        """Test that audit entries include timestamps."""
        # Act
        entry = await audit_logger_no_db.log(
            tenant_id="tenant-1", action="test", resource_type="test"
        )

        # Assert
        assert entry.timestamp is not None
        assert isinstance(entry.timestamp, str)
        # Should be ISO format
        assert "T" in entry.timestamp

    async def test_audit_entry_has_uuid(self, audit_logger_no_db):
        """Test that audit entries have unique IDs."""
        # Act
        entry1 = await audit_logger_no_db.log(
            tenant_id="tenant-1", action="test1", resource_type="test"
        )
        entry2 = await audit_logger_no_db.log(
            tenant_id="tenant-1", action="test2", resource_type="test"
        )

        # Assert
        assert entry1.id != entry2.id
        assert isinstance(entry1.id, str)

    async def test_log_without_optional_fields(self, audit_logger_no_db):
        """Test logging with only required fields."""
        # Act
        entry = await audit_logger_no_db.log(
            tenant_id="tenant-1",
            action="test",
            resource_type="test",
        )

        # Assert
        assert entry.user_id is None
        assert entry.resource_id is None
        assert entry.metadata == {}
        assert entry.ip_address is None

    async def test_db_persistence_sql(self, audit_logger_with_db, mock_db):
        """Test SQL execution for database persistence."""
        # Act
        await audit_logger_with_db.log(
            tenant_id="tenant-123",
            action="document.upload",
            resource_type="document",
            resource_id="doc-456",
        )

        # Assert
        call_args = mock_db.execute.call_args
        sql = str(call_args[0][0])
        params = call_args[0][1]

        assert "INSERT INTO shared.audit_logs" in sql
        assert params["tenant_id"] == "tenant-123"
        assert params["action"] == "document.upload"
        assert params["resource_type"] == "document"
        assert params["resource_id"] == "doc-456"


class TestAuditEntry:
    """Test AuditEntry data model."""

    def test_audit_entry_creation(self):
        """Test creating an audit entry."""
        entry = AuditEntry(
            tenant_id="tenant-123",
            user_id="user-456",
            action="document.upload",
            resource_type="document",
            resource_id="doc-789",
            metadata={"filename": "test.pdf"},
            ip_address="192.168.1.1",
        )

        assert entry.tenant_id == "tenant-123"
        assert entry.user_id == "user-456"
        assert entry.action == "document.upload"
        assert entry.resource_type == "document"
        assert entry.resource_id == "doc-789"
        assert entry.metadata["filename"] == "test.pdf"
        assert entry.ip_address == "192.168.1.1"

    def test_audit_entry_defaults(self):
        """Test audit entry with default values."""
        entry = AuditEntry()

        assert entry.tenant_id == ""
        assert entry.user_id is None
        assert entry.action == ""
        assert entry.resource_type == ""
        assert entry.resource_id is None
        assert entry.metadata == {}
        assert entry.ip_address is None
        assert entry.id is not None
        assert entry.timestamp is not None


class TestAuditLoggerIntegration:
    """Integration-style tests for audit logging."""

    async def test_audit_trail_for_document_lifecycle(self, audit_logger_no_db):
        """Test complete audit trail for document operations."""
        # Arrange & Act
        doc_id = "doc-123"

        # Upload
        await audit_logger_no_db.log(
            tenant_id="tenant-1",
            action="document.upload",
            resource_type="document",
            resource_id=doc_id,
            user_id="user-1",
        )

        # Query
        await audit_logger_no_db.log(
            tenant_id="tenant-1",
            action="document.query",
            resource_type="document",
            resource_id=doc_id,
            user_id="user-2",
        )

        # Delete
        await audit_logger_no_db.log(
            tenant_id="tenant-1",
            action="document.delete",
            resource_type="document",
            resource_id=doc_id,
            user_id="user-1",
        )

        # Assert
        logs = await audit_logger_no_db.query_logs(
            tenant_id="tenant-1", resource_type="document"
        )
        assert len(logs) == 3
        actions = [e.action for e in logs]
        assert "document.upload" in actions
        assert "document.query" in actions
        assert "document.delete" in actions
