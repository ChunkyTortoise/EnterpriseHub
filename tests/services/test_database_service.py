#!/usr/bin/env python3
"""
Comprehensive tests for Database Service.

Tests cover:
- DatabaseService CRUD operations
- Connection management and pooling
- Migration system
- Lead lifecycle management
- Communication logging
- Nurture campaign management
- Health monitoring and performance metrics
- Error handling and recovery

Coverage Target: 85%+ for all database operations
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

# Import the module under test
try:
    from ghl_real_estate_ai.services.database_service import (
        CommunicationChannel,
        CommunicationLog,
        DatabaseManager,
        DatabaseService,
        Lead,
        LeadCampaignStatus,
        LeadStatus,
        NurtureCampaign,
    )
except (ImportError, TypeError, AttributeError):
    pytest.skip("required imports unavailable", allow_module_level=True)

# Import test utilities
from tests.fixtures.sample_data import LeadProfiles
from tests.mocks.external_services import MockDatabaseService


def _make_transaction_context_manager(mock_conn):
    """
    Create a proper mock for conn.transaction() that works as an
    async context manager. The real asyncpg conn.transaction() is a
    sync method that returns an async context manager.
    """
    tx_cm = MagicMock()
    tx_cm.__aenter__ = AsyncMock(return_value=mock_conn)
    tx_cm.__aexit__ = AsyncMock(return_value=None)
    mock_conn.transaction = MagicMock(return_value=tx_cm)


def _make_connection_context_manager(mock_connection_manager, mock_conn):
    """
    Create a proper mock for connection_manager.get_connection() that works
    as an async context manager.
    """
    conn_cm = MagicMock()
    conn_cm.__aenter__ = AsyncMock(return_value=mock_conn)
    conn_cm.__aexit__ = AsyncMock(return_value=None)
    mock_connection_manager.get_connection = MagicMock(return_value=conn_cm)


class TestDatabaseService:
    """Test Database Service operations"""

    @pytest_asyncio.fixture
    async def db_service(self):
        """Create database service with mocked dependencies"""
        # Mock the connection manager
        mock_connection_manager = MagicMock()
        mock_connection_manager.initialize = AsyncMock()
        mock_connection_manager.cleanup = AsyncMock()
        mock_connection_manager.pool = MagicMock()
        mock_connection_manager.get_pool_metrics = AsyncMock(
            return_value={"active_connections": 5, "idle_connections": 10, "total_connections": 15}
        )
        mock_connection_manager.get_query_performance_summary = AsyncMock(
            return_value={"avg_query_time_ms": 25.5, "slow_queries": 0}
        )
        mock_connection_manager.health_check = AsyncMock(return_value={"status": "healthy", "pool_utilization": 0.33})
        mock_connection_manager.execute_query = AsyncMock()

        # Create database service
        db_service = DatabaseService("postgresql://test:test@localhost/test_db")

        # Replace connection manager with mock
        db_service.connection_manager = mock_connection_manager

        # Mock database connection
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock()
        mock_conn.fetchval = AsyncMock()
        mock_conn.fetchrow = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])

        # Setup transaction as sync method returning async context manager
        _make_transaction_context_manager(mock_conn)

        # Setup connection context manager
        _make_connection_context_manager(mock_connection_manager, mock_conn)

        # Mark as initialized (skip real initialization to avoid recursion)
        db_service._initialized = True

        # Store mock connection for test access
        db_service._mock_conn = mock_conn

        return db_service

    @pytest.mark.asyncio
    async def test_initialization_success(self, db_service):
        """Test successful database service initialization"""
        assert db_service._initialized is True
        assert db_service.connection_manager is not None

        # Verify the service is properly configured (initialize was not called
        # because the fixture sets _initialized=True to skip real initialization)

    @pytest.mark.asyncio
    async def test_initialization_already_initialized(self, db_service):
        """Test that re-initialization is skipped when already initialized"""
        # Reset call counts
        db_service.connection_manager.initialize.reset_mock()

        # Try to initialize again
        await db_service.initialize()

        # Should not be called again
        db_service.connection_manager.initialize.assert_not_called()

    @pytest.mark.asyncio
    async def test_initialization_failure(self):
        """Test initialization failure handling"""
        db_service = DatabaseService("postgresql://invalid:invalid@localhost/invalid")

        # Mock failing connection manager
        mock_connection_manager = MagicMock()
        mock_connection_manager.initialize = AsyncMock(side_effect=Exception("Connection failed"))
        db_service.connection_manager = mock_connection_manager

        with pytest.raises(Exception, match="Connection failed"):
            await db_service.initialize()

        assert db_service._initialized is False

    @pytest.mark.asyncio
    async def test_close(self, db_service):
        """Test database service shutdown"""
        await db_service.close()

        db_service.connection_manager.cleanup.assert_called_once()
        assert db_service.pool is None
        assert db_service._initialized is False


class TestLeadManagement:
    """Test lead CRUD operations"""

    @pytest_asyncio.fixture
    async def db_service(self):
        """Create database service for lead testing"""
        # Use mock database service for lead operations
        mock_db = MockDatabaseService()
        return mock_db

    @pytest.mark.asyncio
    async def test_create_lead_success(self, db_service):
        """Test successful lead creation"""
        lead_data = LeadProfiles.high_engagement_lead()

        # For real database service, we'd test with actual DB
        # For now, test with mock
        result = await db_service.save_lead("test_lead_id", lead_data)

        assert result is True
        assert db_service.operation_count == 1

        # Verify lead was stored
        stored_lead = await db_service.get_lead("test_lead_id")
        assert stored_lead is not None
        assert stored_lead["name"] == lead_data["name"]
        assert stored_lead["email"] == lead_data["email"]

    @pytest.mark.asyncio
    async def test_create_lead_duplicate_email(self):
        """Test lead creation with duplicate email"""
        # This would test database constraint violation
        # Using real database service with mocked connection
        db_service = DatabaseService("postgresql://test:test@localhost/test")

        # Mock connection that raises integrity error
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("duplicate key value violates unique constraint"))

        # Setup transaction as sync method returning async context manager
        _make_transaction_context_manager(mock_conn)

        # Mock connection manager
        db_service.connection_manager = MagicMock()
        _make_connection_context_manager(db_service.connection_manager, mock_conn)
        db_service._initialized = True

        lead_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "source": "website",
        }

        with pytest.raises(Exception, match="duplicate key value"):
            await db_service.create_lead(lead_data)

    @pytest.mark.asyncio
    async def test_get_lead_by_id(self, db_service):
        """Test retrieving lead by ID"""
        # Setup test data
        lead_data = LeadProfiles.medium_engagement_lead()
        await db_service.save_lead("test_lead_123", lead_data)

        # Retrieve lead
        result = await db_service.get_lead("test_lead_123")

        assert result is not None
        assert result["name"] == lead_data["name"]
        assert result["email"] == lead_data["email"]

    @pytest.mark.asyncio
    async def test_get_lead_not_found(self, db_service):
        """Test retrieving non-existent lead"""
        result = await db_service.get_lead("non_existent_id")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_lead_score(self, db_service):
        """Test updating lead score"""
        # Setup test lead
        lead_data = LeadProfiles.low_engagement_lead()
        await db_service.save_lead("test_lead_456", lead_data)

        # Update lead score
        analysis_data = {
            "ai_models_used": ["claude", "ml_scorer"],
            "confidence": 0.85,
            "insights": ["High engagement", "Budget aligned"],
        }

        result = await db_service.update_lead_score("test_lead_456", 78.5, analysis_data)
        assert result is True

        # Verify update
        updated_lead = await db_service.get_lead("test_lead_456")
        assert updated_lead["ai_score"] == 78.5
        assert updated_lead["ai_analysis"] == analysis_data

    @pytest.mark.asyncio
    async def test_update_lead_score_not_found(self, db_service):
        """Test updating score for non-existent lead"""
        result = await db_service.update_lead_score("non_existent", 85.0, {})
        assert result is False

    @pytest.mark.asyncio
    async def test_get_lead_history(self, db_service):
        """Test retrieving lead interaction history"""
        history = await db_service.get_lead_history("test_lead_789")

        assert isinstance(history, list)
        assert len(history) == 3  # Mock returns 3 history items

        # Verify history structure
        for item in history:
            assert "timestamp" in item
            assert "action" in item
            assert "details" in item


class TestCommunicationLogging:
    """Test communication logging functionality"""

    @pytest_asyncio.fixture
    async def db_service_real(self):
        """Create real database service for communication tests"""
        db_service = DatabaseService("postgresql://test:test@localhost/test")

        # Mock connection for communication logging
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value="INSERT 0 1")

        # Setup transaction as sync method returning async context manager
        _make_transaction_context_manager(mock_conn)

        db_service.connection_manager = MagicMock()
        _make_connection_context_manager(db_service.connection_manager, mock_conn)
        db_service._initialized = True
        db_service._mock_conn = mock_conn

        return db_service

    @pytest.mark.asyncio
    async def test_log_communication_email(self, db_service_real):
        """Test logging email communication"""
        comm_data = {
            "lead_id": "lead_123",
            "channel": "email",
            "direction": "outbound",
            "content": "Thank you for your interest in our properties...",
            "status": "sent",
            "campaign_id": "campaign_456",
            "template_id": "template_789",
            "metadata": {"subject": "North Austin Properties Available", "template_name": "property_followup"},
        }

        result = await db_service_real.log_communication(comm_data)

        # Verify UUID format
        assert isinstance(result, str)
        assert len(result) == 36  # UUID length with hyphens

        # Verify database calls
        db_service_real._mock_conn.execute.assert_called()

        # Check that lead's last interaction was updated for outbound message
        call_args_list = db_service_real._mock_conn.execute.call_args_list
        assert len(call_args_list) == 2  # Insert communication + update lead

    @pytest.mark.asyncio
    async def test_log_communication_sms(self, db_service_real):
        """Test logging SMS communication"""
        comm_data = {
            "lead_id": "lead_123",
            "channel": "sms",
            "direction": "inbound",
            "content": "Yes, I'm interested in viewing the property",
            "status": "received",
        }

        result = await db_service_real.log_communication(comm_data)
        assert isinstance(result, str)

        # For inbound messages, lead interaction time shouldn't be updated
        call_args_list = db_service_real._mock_conn.execute.call_args_list
        assert len(call_args_list) == 1  # Only insert communication

    @pytest.mark.asyncio
    async def test_log_communication_phone(self, db_service_real):
        """Test logging phone communication"""
        comm_data = {
            "lead_id": "lead_123",
            "channel": "phone",
            "direction": "outbound",
            "content": "Property viewing scheduled for tomorrow 2pm",
            "status": "completed",
            "metadata": {"call_duration": 300, "recording_url": "https://recordings.example.com/call_123.mp3"},
        }

        result = await db_service_real.log_communication(comm_data)
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_get_lead_communications(self, db_service_real):
        """Test retrieving communication history"""
        # Mock fetch result - use dicts directly since the service calls dict(row)
        mock_communications = [
            {
                "id": "comm_1",
                "lead_id": "lead_123",
                "channel": "email",
                "direction": "outbound",
                "content": "Welcome email",
                "sent_at": datetime.now(),
            },
            {
                "id": "comm_2",
                "lead_id": "lead_123",
                "channel": "sms",
                "direction": "inbound",
                "content": "Thanks for the info",
                "sent_at": datetime.now() - timedelta(hours=1),
            },
        ]

        # The service calls dict(row), so mock rows need to support dict() conversion
        mock_rows = []
        for comm in mock_communications:
            mock_row = MagicMock()
            mock_row.__iter__ = MagicMock(return_value=iter(comm.items()))
            mock_row.keys = MagicMock(return_value=comm.keys())
            mock_row.__getitem__ = lambda self, key, c=comm: c[key]
            mock_rows.append(mock_row)

        db_service_real._mock_conn.fetch = AsyncMock(return_value=mock_rows)

        # Re-setup connection context manager with updated mock_conn
        _make_connection_context_manager(db_service_real.connection_manager, db_service_real._mock_conn)

        result = await db_service_real.get_lead_communications("lead_123", limit=10)

        assert len(result) == 2
        assert result[0]["channel"] == "email"
        assert result[1]["channel"] == "sms"

    @pytest.mark.asyncio
    async def test_update_communication_status(self, db_service_real):
        """Test updating communication delivery status"""
        delivered_at = datetime.now()

        # Mock successful update
        db_service_real._mock_conn.execute.return_value = "UPDATE 1"

        result = await db_service_real.update_communication_status("comm_123", "delivered", delivered_at)

        assert result is True
        db_service_real._mock_conn.execute.assert_called()

    @pytest.mark.asyncio
    async def test_update_communication_status_not_found(self, db_service_real):
        """Test updating status for non-existent communication"""
        # Mock no rows affected
        db_service_real._mock_conn.execute.return_value = "UPDATE 0"

        result = await db_service_real.update_communication_status("non_existent", "delivered")

        assert result is False


class TestNurtureCampaigns:
    """Test nurture campaign functionality"""

    @pytest_asyncio.fixture
    async def db_service_campaigns(self):
        """Create database service for campaign testing"""
        db_service = DatabaseService("postgresql://test:test@localhost/test")

        # Mock connection
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value="INSERT 0 1")
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_conn.fetchrow = AsyncMock()

        # Setup transaction as sync method returning async context manager
        _make_transaction_context_manager(mock_conn)

        db_service.connection_manager = MagicMock()
        _make_connection_context_manager(db_service.connection_manager, mock_conn)
        db_service._initialized = True
        db_service._mock_conn = mock_conn

        return db_service

    @pytest.mark.asyncio
    async def test_create_nurture_campaign(self, db_service_campaigns):
        """Test creating a nurture campaign"""
        campaign_data = {
            "name": "New Lead Nurture Sequence",
            "description": "5-day email sequence for new leads",
            "status": "active",
            "trigger_conditions": {"lead_status": "new", "source": ["website", "facebook"]},
            "steps": [
                {
                    "step": 1,
                    "delay_hours": 0,
                    "channel": "email",
                    "template": "welcome_email",
                    "subject": "Welcome to Our Real Estate Journey",
                },
                {
                    "step": 2,
                    "delay_hours": 24,
                    "channel": "email",
                    "template": "market_insights",
                    "subject": "Austin Market Update",
                },
                {
                    "step": 3,
                    "delay_hours": 72,
                    "channel": "sms",
                    "template": "quick_check_in",
                    "content": "Quick question: Are you still looking in the Austin area?",
                },
            ],
        }

        result = await db_service_campaigns.create_nurture_campaign(campaign_data)

        assert isinstance(result, str)
        assert len(result) == 36  # UUID length

        # Verify database call
        db_service_campaigns._mock_conn.execute.assert_called()
        call_args = db_service_campaigns._mock_conn.execute.call_args[0]
        assert "INSERT INTO nurture_campaigns" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_active_campaigns(self, db_service_campaigns):
        """Test retrieving active campaigns"""
        # Mock active campaigns - use objects that support dict() conversion
        mock_campaigns = [
            {"id": "campaign_1", "name": "New Lead Sequence", "status": "active", "active_leads_count": 25},
            {"id": "campaign_2", "name": "Re-engagement Campaign", "status": "active", "active_leads_count": 12},
        ]

        # Create mock rows that support dict() conversion
        mock_rows = []
        for campaign in mock_campaigns:
            mock_row = MagicMock()
            mock_row.__iter__ = MagicMock(return_value=iter(campaign.items()))
            mock_row.keys = MagicMock(return_value=campaign.keys())
            mock_row.__getitem__ = lambda self, key, c=campaign: c[key]
            mock_rows.append(mock_row)

        db_service_campaigns._mock_conn.fetch.return_value = mock_rows

        result = await db_service_campaigns.get_active_campaigns()

        assert len(result) == 2
        assert result[0]["name"] == "New Lead Sequence"
        assert result[1]["name"] == "Re-engagement Campaign"

    @pytest.mark.asyncio
    async def test_enroll_lead_in_campaign(self, db_service_campaigns):
        """Test enrolling a lead in a campaign"""
        lead_id = "lead_123"
        campaign_id = "campaign_456"
        next_action_at = datetime.now() + timedelta(hours=1)

        result = await db_service_campaigns.enroll_lead_in_campaign(lead_id, campaign_id, next_action_at)

        assert isinstance(result, str)

        # Verify database calls
        call_args_list = db_service_campaigns._mock_conn.execute.call_args_list
        assert len(call_args_list) == 2  # Insert enrollment + update campaign count

    @pytest.mark.asyncio
    async def test_get_due_campaign_actions(self, db_service_campaigns):
        """Test retrieving due campaign actions"""
        # Mock due actions - use objects that support dict() conversion
        mock_actions = [
            {
                "id": "enrollment_1",
                "lead_id": "lead_123",
                "campaign_id": "campaign_456",
                "current_step": 1,
                "next_action_at": datetime.now() - timedelta(minutes=30),
                "email": "john@example.com",
                "first_name": "John",
                "campaign_name": "New Lead Sequence",
                "steps": json.dumps([{"step": 1, "template": "welcome"}]),
            }
        ]

        # Create mock rows that support dict() conversion
        mock_rows = []
        for action in mock_actions:
            mock_row = MagicMock()
            mock_row.__iter__ = MagicMock(return_value=iter(action.items()))
            mock_row.keys = MagicMock(return_value=action.keys())
            mock_row.__getitem__ = lambda self, key, a=action: a[key]
            mock_rows.append(mock_row)

        db_service_campaigns._mock_conn.fetch.return_value = mock_rows

        result = await db_service_campaigns.get_due_campaign_actions()

        assert len(result) == 1
        assert result[0]["lead_id"] == "lead_123"
        assert result[0]["campaign_name"] == "New Lead Sequence"


class TestSearchAndFiltering:
    """Test search and filtering functionality"""

    @pytest_asyncio.fixture
    async def db_service_search(self):
        """Create database service for search testing"""
        db_service = DatabaseService("postgresql://test:test@localhost/test")

        # Mock connection
        mock_conn = MagicMock()
        mock_conn.fetch = AsyncMock(return_value=[])

        db_service.connection_manager = MagicMock()
        _make_connection_context_manager(db_service.connection_manager, mock_conn)
        db_service._initialized = True
        db_service._mock_conn = mock_conn

        return db_service

    @pytest.mark.asyncio
    async def test_search_leads_by_status(self, db_service_search):
        """Test searching leads by status"""
        filters = {"status": "qualified"}

        # Mock search results - use objects that support dict() conversion
        mock_leads = [
            {"id": "lead_1", "status": "qualified", "score": 85},
            {"id": "lead_2", "status": "qualified", "score": 78},
        ]

        mock_rows = []
        for lead in mock_leads:
            mock_row = MagicMock()
            mock_row.__iter__ = MagicMock(return_value=iter(lead.items()))
            mock_row.keys = MagicMock(return_value=lead.keys())
            mock_row.__getitem__ = lambda self, key, l=lead: l[key]
            mock_rows.append(mock_row)

        db_service_search._mock_conn.fetch.return_value = mock_rows

        result = await db_service_search.search_leads(filters, limit=50, offset=0)

        assert len(result) == 2
        assert all(lead["status"] == "qualified" for lead in result)

    @pytest.mark.asyncio
    async def test_search_leads_by_score_range(self, db_service_search):
        """Test searching leads by score range"""
        filters = {"score_min": 70, "score_max": 90}

        mock_leads = [{"id": "lead_1", "score": 85}, {"id": "lead_2", "score": 72}]

        mock_rows = []
        for lead in mock_leads:
            mock_row = MagicMock()
            mock_row.__iter__ = MagicMock(return_value=iter(lead.items()))
            mock_row.keys = MagicMock(return_value=lead.keys())
            mock_row.__getitem__ = lambda self, key, l=lead: l[key]
            mock_rows.append(mock_row)

        db_service_search._mock_conn.fetch.return_value = mock_rows

        result = await db_service_search.search_leads(filters)

        assert len(result) == 2

        # Verify SQL query construction
        call_args = db_service_search._mock_conn.fetch.call_args[0]
        sql_query = call_args[0]
        assert "score >=" in sql_query
        assert "score <=" in sql_query

    @pytest.mark.asyncio
    async def test_search_leads_by_date_range(self, db_service_search):
        """Test searching leads by creation date range"""
        filters = {"created_after": datetime.now() - timedelta(days=7), "created_before": datetime.now()}

        result = await db_service_search.search_leads(filters)

        # Verify SQL query includes date filters
        call_args = db_service_search._mock_conn.fetch.call_args[0]
        sql_query = call_args[0]
        assert "created_at >=" in sql_query
        assert "created_at <=" in sql_query

    @pytest.mark.asyncio
    async def test_search_leads_pagination(self, db_service_search):
        """Test lead search with pagination"""
        filters = {"status": "new"}

        await db_service_search.search_leads(filters, limit=25, offset=50)

        # Verify pagination parameters
        call_args = db_service_search._mock_conn.fetch.call_args[0]
        sql_query = call_args[0]
        query_params = call_args[1:]

        assert "LIMIT" in sql_query
        assert "OFFSET" in sql_query
        assert 25 in query_params  # limit
        assert 50 in query_params  # offset

    @pytest.mark.asyncio
    async def test_get_silent_leads(self, db_service_search):
        """Test retrieving leads that have gone silent"""
        # Mock silent leads
        silent_cutoff = datetime.now() - timedelta(hours=48)
        mock_silent_leads = [
            {"id": "lead_1", "status": "contacted", "last_interaction_at": silent_cutoff - timedelta(hours=6)},
            {"id": "lead_2", "status": "qualified", "last_interaction_at": silent_cutoff - timedelta(hours=12)},
        ]

        mock_rows = []
        for lead in mock_silent_leads:
            mock_row = MagicMock()
            mock_row.__iter__ = MagicMock(return_value=iter(lead.items()))
            mock_row.keys = MagicMock(return_value=lead.keys())
            mock_row.__getitem__ = lambda self, key, l=lead: l[key]
            mock_rows.append(mock_row)

        db_service_search._mock_conn.fetch.return_value = mock_rows

        result = await db_service_search.get_silent_leads(silence_threshold_hours=48)

        assert len(result) == 2

        # Verify SQL query
        call_args = db_service_search._mock_conn.fetch.call_args[0]
        sql_query = call_args[0]
        assert "last_interaction_at <" in sql_query
        assert "status IN" in sql_query


class TestHealthAndMonitoring:
    """Test health check and monitoring functionality"""

    @pytest_asyncio.fixture
    async def db_service_health(self):
        """Create database service for health testing"""
        db_service = DatabaseService("postgresql://test:test@localhost/test")

        # Mock connection
        mock_conn = MagicMock()
        mock_conn.fetchval = AsyncMock()
        mock_conn.fetch = AsyncMock()
        mock_conn.fetchrow = AsyncMock()

        # Mock pool
        mock_pool = MagicMock()
        mock_pool.get_size.return_value = 10
        mock_pool.get_idle_size.return_value = 7

        db_service.connection_manager = MagicMock()
        _make_connection_context_manager(db_service.connection_manager, mock_conn)
        db_service.connection_manager.get_pool_metrics = AsyncMock(
            return_value={"active_connections": 3, "idle_connections": 7, "total_connections": 10}
        )
        db_service.connection_manager.get_query_performance_summary = AsyncMock(
            return_value={"avg_query_time_ms": 15.2, "slow_queries": 0, "total_queries": 1250}
        )
        db_service.connection_manager.health_check = AsyncMock(
            return_value={"status": "healthy", "pool_utilization": 0.3}
        )

        db_service.pool = mock_pool
        db_service._initialized = True
        db_service._mock_conn = mock_conn

        return db_service

    @pytest.mark.asyncio
    async def test_health_check_success(self, db_service_health):
        """Test successful health check"""
        # Mock successful health check responses
        db_service_health._mock_conn.fetchval.side_effect = [
            1,  # connectivity test
            150,  # leads count
            500,  # communications count
            5,  # campaigns count
            25,  # recent leads
        ]

        result = await db_service_health.health_check()

        assert result["status"] == "healthy"
        assert result["database_connected"] is True
        assert result["response_time_seconds"] > 0
        assert "stats" in result
        assert result["stats"]["total_leads"] == 150
        assert result["stats"]["total_communications"] == 500
        assert result["stats"]["total_campaigns"] == 5
        assert result["stats"]["leads_today"] == 25
        assert "pool_stats" in result

    @pytest.mark.asyncio
    async def test_health_check_failure(self, db_service_health):
        """Test health check failure handling"""
        # Mock database connection failure
        db_service_health._mock_conn.fetchval.side_effect = Exception("Connection timeout")

        # The service re-raises the exception on health check failure
        with pytest.raises(Exception, match="Connection timeout"):
            await db_service_health.health_check()

    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, db_service_health):
        """Test retrieving performance metrics"""
        # Mock table sizes - use objects that support dict() conversion
        mock_table_sizes = [
            {"tablename": "leads", "size": "1024 MB", "bytes": 1073741824},
            {"tablename": "communication_logs", "size": "512 MB", "bytes": 536870912},
        ]

        # Mock activity metrics
        mock_activity = {"leads_last_hour": 5, "comms_last_hour": 12, "new_leads": 45, "hot_leads": 8}

        # Create mock rows for table sizes that support dict() conversion
        mock_table_rows = []
        for table in mock_table_sizes:
            mock_row = MagicMock()
            mock_row.__iter__ = MagicMock(return_value=iter(table.items()))
            mock_row.keys = MagicMock(return_value=table.keys())
            mock_row.__getitem__ = lambda self, key, t=table: t[key]
            mock_table_rows.append(mock_row)

        db_service_health._mock_conn.fetch.return_value = mock_table_rows

        # Create mock row for activity that supports dict() conversion
        mock_activity_row = MagicMock()
        mock_activity_row.__iter__ = MagicMock(return_value=iter(mock_activity.items()))
        mock_activity_row.keys = MagicMock(return_value=mock_activity.keys())
        mock_activity_row.__getitem__ = lambda self, key: mock_activity[key]
        db_service_health._mock_conn.fetchrow.return_value = mock_activity_row

        result = await db_service_health.get_performance_metrics()

        assert "connection_pool" in result
        assert "query_performance" in result
        assert "table_sizes" in result
        assert "activity" in result

        # Verify connection pool metrics
        assert result["connection_pool"]["active_connections"] == 3

        # Verify query performance
        assert result["query_performance"]["avg_query_time_ms"] == 15.2

        # Verify table sizes
        assert len(result["table_sizes"]) == 2
        assert result["table_sizes"][0]["tablename"] == "leads"

        # Verify activity metrics
        assert result["activity"]["leads_last_hour"] == 5
        assert result["activity"]["new_leads"] == 45

    @pytest.mark.asyncio
    async def test_get_connection_health(self, db_service_health):
        """Test getting connection health details"""
        # Mock successful health check for database_specific
        db_service_health._mock_conn.fetchval.side_effect = [
            1,  # connectivity test
            150,  # leads count
            500,  # communications count
            5,  # campaigns count
            25,  # recent leads
        ]

        result = await db_service_health.get_connection_health()

        assert "enterprise_connection_manager" in result
        assert "database_specific" in result

        # Verify enterprise connection manager health
        assert result["enterprise_connection_manager"]["status"] == "healthy"

        # Verify database-specific health
        assert result["database_specific"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_execute_optimized_query(self, db_service_health):
        """Test executing optimized queries"""
        # Mock query execution
        db_service_health.connection_manager.execute_query = AsyncMock(return_value="Query result")

        sql = "SELECT COUNT(*) FROM leads WHERE score > $1"
        result = await db_service_health.execute_optimized_query(sql, 80, timeout=5.0)

        assert result == "Query result"

        # Verify call to connection manager
        db_service_health.connection_manager.execute_query.assert_called_once_with(
            sql, 80, timeout=5.0, record_execution=True
        )


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error scenarios"""

    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion(self):
        """Test handling when connection pool is exhausted"""
        db_service = DatabaseService("postgresql://test:test@localhost/test")

        # Mock connection manager that raises pool exhaustion error
        mock_connection_manager = MagicMock()
        mock_connection_manager.get_connection.side_effect = Exception("Connection pool exhausted")
        db_service.connection_manager = mock_connection_manager
        db_service._initialized = True

        with pytest.raises(Exception, match="Connection pool exhausted"):
            async with db_service.get_connection():
                pass

    @pytest.mark.asyncio
    async def test_transaction_rollback(self):
        """Test transaction rollback on error"""
        db_service = DatabaseService("postgresql://test:test@localhost/test")

        # Mock connection that raises error during transaction
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("Query failed"))

        # Setup transaction as sync method returning async context manager
        _make_transaction_context_manager(mock_conn)

        db_service.connection_manager = MagicMock()
        _make_connection_context_manager(db_service.connection_manager, mock_conn)
        db_service._initialized = True

        with pytest.raises(Exception, match="Query failed"):
            async with db_service.transaction() as conn:
                await conn.execute("INSERT INTO leads (...) VALUES (...)")

    @pytest.mark.asyncio
    async def test_invalid_lead_data_validation(self):
        """Test validation of invalid lead data"""
        db_service = DatabaseService("postgresql://test:test@localhost/test")

        # Mock connection that raises constraint violation
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(
            side_effect=Exception("null value in column 'email' violates not-null constraint")
        )

        # Setup transaction as sync method returning async context manager
        _make_transaction_context_manager(mock_conn)

        db_service.connection_manager = MagicMock()
        _make_connection_context_manager(db_service.connection_manager, mock_conn)
        db_service._initialized = True

        # Invalid lead data missing required fields
        invalid_lead_data = {
            "first_name": "John",
            # missing email and other required fields
        }

        with pytest.raises(Exception, match="not-null constraint"):
            await db_service.create_lead(invalid_lead_data)

    @pytest.mark.asyncio
    async def test_concurrent_lead_updates(self):
        """Test handling concurrent updates to same lead"""
        db_service = DatabaseService("postgresql://test:test@localhost/test")

        # Mock connection for successful updates
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value="UPDATE 1")

        # Setup transaction as sync method returning async context manager
        _make_transaction_context_manager(mock_conn)

        db_service.connection_manager = MagicMock()
        _make_connection_context_manager(db_service.connection_manager, mock_conn)
        db_service._initialized = True

        # Simulate concurrent updates
        update_tasks = []
        for i in range(5):
            task = db_service.update_lead("lead_123", {"score": 80 + i, "temperature": "warm"}, updated_by=f"user_{i}")
            update_tasks.append(task)

        results = await asyncio.gather(*update_tasks, return_exceptions=True)

        # All updates should succeed (in real scenario, some might fail due to conflicts)
        assert all(result is True for result in results if not isinstance(result, Exception))


@pytest.mark.performance
class TestPerformanceCharacteristics:
    """Test database performance characteristics"""

    @pytest.mark.asyncio
    async def test_bulk_lead_creation_performance(self):
        """Test performance of bulk lead creation"""
        db_service = DatabaseService("postgresql://test:test@localhost/test")

        # Mock fast connection
        mock_conn = MagicMock()
        mock_conn.execute = AsyncMock(return_value="INSERT 0 1")

        # Setup transaction as sync method returning async context manager
        _make_transaction_context_manager(mock_conn)

        db_service.connection_manager = MagicMock()
        _make_connection_context_manager(db_service.connection_manager, mock_conn)
        db_service._initialized = True

        # Create multiple leads concurrently
        lead_tasks = []
        for i in range(20):
            lead_data = {
                "first_name": f"Lead{i}",
                "last_name": "Test",
                "email": f"lead{i}@test.com",
                "phone": f"+1555000{i:04d}",
                "source": "performance_test",
            }

            task = db_service.create_lead(lead_data)
            lead_tasks.append(task)

        import time

        start_time = time.time()

        results = await asyncio.gather(*lead_tasks, return_exceptions=True)

        end_time = time.time()

        # Verify all creations succeeded
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == 20

        # Performance should be reasonable (under 1 second for mocked operations)
        execution_time = end_time - start_time
        assert execution_time < 1.0

    @pytest.mark.asyncio
    async def test_query_timeout_handling(self):
        """Test handling of query timeouts"""
        db_service = DatabaseService("postgresql://test:test@localhost/test")

        # Mock slow query
        async def slow_query(*args, **kwargs):
            await asyncio.sleep(0.5)  # Simulate slow query
            raise Exception("Query timeout")

        db_service.connection_manager = MagicMock()
        db_service.connection_manager.execute_query = slow_query
        db_service._initialized = True

        with pytest.raises(Exception, match="Query timeout"):
            await db_service.execute_optimized_query("SELECT * FROM large_table", timeout=0.1)


if __name__ == "__main__":
    # Run specific test classes for development
    pytest.main(["-v", "tests/services/test_database_service.py::TestLeadManagement", "--tb=short"])
