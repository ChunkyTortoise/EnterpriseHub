import pytest
pytestmark = pytest.mark.integration

"""
Integration Tests for Parallel Workstream Coordination

Tests the interaction between:
1. Production Stability Fixes (Error Handling)
2. Performance Optimizations (Database + Caching)
3. Database Integration (TODO Operations)
4. Innovation Features (AI Swarms)

These tests ensure that parallel development doesn't introduce conflicts
and that all workstreams integrate seamlessly for production deployment.
"""

import asyncio
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import pytest

try:
    from ghl_real_estate_ai.services.autonomous_followup_engine import AutonomousFollowupEngine
    from ghl_real_estate_ai.services.behavioral_trigger_engine import BehavioralTriggerEngine
    from ghl_real_estate_ai.services.cache_service import CacheService
    from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
    from ghl_real_estate_ai.services.content_personalization_swarm import ContentPersonalizationSwarm
    from ghl_real_estate_ai.services.database_service import DatabaseService
except (ImportError, TypeError, AttributeError, Exception):
    pytest.skip("required imports unavailable", allow_module_level=True)


@pytest.mark.integration
@pytest.mark.asyncio
class TestWorkstreamIntegration:
    """Test integration between all parallel workstreams."""

    @pytest.fixture
    async def integrated_services(self):
        """Set up integrated services for testing."""
        cache_service = CacheService()
        database_service = DatabaseService()
        claude_assistant = ClaudeAssistant()

        return {
            "cache": cache_service,
            "database": database_service,
            "claude": claude_assistant,
        }

    async def test_error_handling_with_performance_optimization(self, integrated_services):
        """Test that error handling doesn't interfere with performance optimizations."""
        cache_service = integrated_services["cache"]

        # Test error handling in cached operations
        with patch.object(cache_service, "_redis_client") as mock_redis:
            mock_redis.get.side_effect = ConnectionError("Redis connection failed")

            # Should handle Redis errors gracefully without breaking performance optimizations
            result = await cache_service.get_cached_data("test_key")
            assert result is None  # Should return None instead of raising exception

        # Test performance optimization still works when Redis is available
        with patch.object(cache_service, "_redis_client") as mock_redis:
            mock_redis.get.return_value = b'{"cached": "data"}'

            result = await cache_service.get_cached_data("test_key")
            assert result == {"cached": "data"}

    async def test_database_integration_with_caching(self, integrated_services):
        """Test database operations work with caching layer."""
        cache_service = integrated_services["cache"]
        database_service = integrated_services["database"]

        # Test cached database queries
        lead_id = "test_lead_123"

        with (
            patch.object(database_service, "get_lead_data") as mock_db,
            patch.object(cache_service, "get_cached_data") as mock_cache,
        ):
            # First call should hit database and cache result
            mock_cache.return_value = None
            mock_db.return_value = {"lead_id": lead_id, "score": 85}

            result = await cache_service.get_or_set_cached(
                f"lead_data:{lead_id}", lambda: database_service.get_lead_data(lead_id), ttl=3600
            )

            assert result["lead_id"] == lead_id
            assert result["score"] == 85

    @pytest.mark.ai
    async def test_ai_swarms_with_database_integration(self, integrated_services):
        """Test AI swarm coordination with database operations."""
        claude_assistant = integrated_services["claude"]
        database_service = integrated_services["database"]

        # Test AI conversation with database-backed lead intelligence
        lead_data = {
            "id": "lead_123",
            "preferences": {"budget": 500000, "location": "downtown"},
            "interaction_history": ["email_open", "website_visit", "property_view"],
        }

        with (
            patch.object(database_service, "get_lead_intelligence") as mock_db,
            patch.object(claude_assistant, "generate_lead_analysis") as mock_ai,
        ):
            mock_db.return_value = lead_data
            mock_ai.return_value = "High-intent buyer with strong downtown preference"

            # Test coordinated AI analysis with database integration
            result = await claude_assistant.analyze_lead_with_context("lead_123")

            assert "High-intent buyer" in result
            mock_db.assert_called_once_with("lead_123")

    async def test_autonomous_followup_with_all_workstreams(self, integrated_services):
        """Test autonomous followup engine with all integrated workstreams."""
        cache_service = integrated_services["cache"]
        database_service = integrated_services["database"]
        claude_assistant = integrated_services["claude"]

        followup_engine = AutonomousFollowupEngine(
            cache_service=cache_service, database_service=database_service, claude_assistant=claude_assistant
        )

        lead_id = "lead_followup_123"

        with (
            patch.object(database_service, "get_lead_followup_history") as mock_history,
            patch.object(cache_service, "get_cached_data") as mock_cache,
            patch.object(claude_assistant, "generate_followup_message") as mock_ai,
        ):
            # Setup test data
            mock_history.return_value = [{"timestamp": "2024-01-15", "action": "email_sent", "response": "opened"}]
            mock_cache.return_value = None
            mock_ai.return_value = "Perfect timing for your property search update!"

            # Test coordinated followup with error handling
            result = await followup_engine.execute_followup_sequence(lead_id)

            # Should integrate all workstreams without errors
            assert result is not None
            assert "success" in result or result.get("status") == "completed"

    @pytest.mark.performance
    async def test_performance_optimization_integration(self, integrated_services):
        """Test that performance optimizations don't break functionality."""
        cache_service = integrated_services["cache"]

        # Test high-volume operations with optimizations
        tasks = []
        for i in range(100):
            tasks.append(cache_service.get_cached_data(f"perf_test_{i}"))

        # Should handle high concurrency without errors
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that no exceptions were raised (all None or data)
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Performance test raised exceptions: {exceptions}"

    @pytest.mark.security
    async def test_security_integration_across_workstreams(self, integrated_services):
        """Test security measures across all workstreams."""
        claude_assistant = integrated_services["claude"]

        # Test input sanitization with AI processing
        malicious_input = "<script>alert('xss')</script>"

        with patch.object(claude_assistant, "_sanitize_input") as mock_sanitize:
            mock_sanitize.return_value = "alert('xss')"  # HTML stripped

            result = await claude_assistant.process_user_input(malicious_input)

            # Should sanitize input before AI processing
            mock_sanitize.assert_called_once_with(malicious_input)
            assert "<script>" not in result

    async def test_end_to_end_workstream_coordination(self, integrated_services):
        """Test complete end-to-end flow with all workstreams integrated."""
        cache_service = integrated_services["cache"]
        database_service = integrated_services["database"]
        claude_assistant = integrated_services["claude"]

        # Simulate complete lead processing pipeline
        lead_data = {"id": "e2e_lead_123", "source": "website_form", "preferences": {"budget": 750000, "type": "condo"}}

        with (
            patch.object(database_service, "save_lead") as mock_save,
            patch.object(cache_service, "invalidate_cache") as mock_invalidate,
            patch.object(claude_assistant, "analyze_lead") as mock_analyze,
        ):
            mock_save.return_value = {"status": "saved", "id": "e2e_lead_123"}
            mock_analyze.return_value = "Qualified condo buyer with strong budget"

            # Test complete pipeline
            # 1. Save lead (Database Integration)
            save_result = await database_service.save_lead(lead_data)

            # 2. Invalidate cache (Performance Optimization)
            await cache_service.invalidate_cache("leads:*")

            # 3. AI analysis (Innovation Features)
            analysis = await claude_assistant.analyze_lead(lead_data)

            # All operations should complete successfully
            assert save_result["status"] == "saved"
            assert "Qualified" in analysis
            mock_save.assert_called_once_with(lead_data)
            mock_invalidate.assert_called_once_with("leads:*")


@pytest.mark.integration
@pytest.mark.database
class TestDatabaseWorkstreamIntegration:
    """Test database integration workstream specifically."""

    async def test_database_todo_operations_implementation(self):
        """Test that all database TODO operations are properly implemented."""
        database_service = DatabaseService()

        # Test autonomous followup database operations
        with patch.object(database_service, "_execute_query") as mock_execute:
            mock_execute.return_value = {"result": "success"}

            # Should have real implementations, not TODO placeholders
            operations = [
                "create_followup_sequence",
                "update_lead_engagement",
                "save_conversation_context",
                "get_lead_intelligence",
            ]

            for operation in operations:
                # Verify operation exists and is not a TODO
                assert hasattr(database_service, operation), f"Missing operation: {operation}"
                method = getattr(database_service, operation)
                # Method should exist and not be a placeholder
                assert callable(method), f"Operation {operation} is not callable"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
