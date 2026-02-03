#!/usr/bin/env python3
"""
Service 6 Test Configuration and Fixtures
========================================

Comprehensive test configuration for Service 6 testing framework:

Global Test Configuration:
- Async test support with pytest-asyncio
- Test markers for categorizing tests (unit, integration, performance, security)
- Coverage configuration for 80%+ target
- Environment setup and cleanup
- Shared fixtures for database, cache, and external services
- Performance monitoring integration
- Security testing utilities

Test Categories:
- unit: Fast unit tests (<100ms each)
- integration: Cross-service integration tests
- performance: Load and performance tests
- security: Security and vulnerability tests
- slow: Long-running tests (>10 seconds)
- critical: Business-critical path tests

Coverage Requirements:
- Minimum 80% line coverage
- 90% coverage for critical business logic
- 100% coverage for security-related code
- Branch coverage for error handling paths
"""

import pytest
import pytest_asyncio
import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional
import logging

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def pytest_configure(config):
    """Configure pytest with custom markers and options"""
    
    # Register custom markers
    config.addinivalue_line("markers", "unit: Unit tests - fast, isolated tests")
    config.addinivalue_line("markers", "integration: Integration tests - cross-service tests")
    config.addinivalue_line("markers", "performance: Performance tests - load and latency tests")
    config.addinivalue_line("markers", "security: Security tests - vulnerability and penetration tests")
    config.addinivalue_line("markers", "slow: Slow tests - tests that take >10 seconds")
    config.addinivalue_line("markers", "critical: Critical path tests - business-critical functionality")
    config.addinivalue_line("markers", "smoke: Smoke tests - basic functionality verification")
    
    # Configure coverage for Service 6
    config.option.cov_source = ['ghl_real_estate_ai/services']
    config.option.cov_report = ['term-missing', 'html']
    config.option.cov_fail_under = 80
    
    logger.info("Service 6 test configuration loaded")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add automatic markers"""
    
    for item in items:
        # Auto-mark tests based on file location
        if "performance" in item.fspath.basename:
            item.add_marker(pytest.mark.performance)
        elif "security" in item.fspath.basename:
            item.add_marker(pytest.mark.security)
        elif "integration" in item.fspath.dirname:
            item.add_marker(pytest.mark.integration)
        elif "unit" in item.fspath.dirname:
            item.add_marker(pytest.mark.unit)
        
        # Auto-mark slow tests based on function name
        if "endurance" in item.name or "load" in item.name or "stress" in item.name:
            item.add_marker(pytest.mark.slow)
        
        # Auto-mark critical tests
        if any(keyword in item.name for keyword in ["critical", "security", "auth", "webhook"]):
            item.add_marker(pytest.mark.critical)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_environment():
    """Set up test environment configuration"""
    
    # Mock environment variables for testing
    test_env = {
        'TESTING': 'true',
        'ENVIRONMENT': 'test',
        'DATABASE_URL': 'postgresql://test_user:test_pass@localhost:5432/test_db',
        'REDIS_URL': 'redis://localhost:6379/1',
        'CLAUDE_API_KEY': 'test_claude_key_12345',
        'GHL_API_KEY': 'test_ghl_key_67890',
        'TWILIO_ACCOUNT_SID': 'test_twilio_sid',
        'TWILIO_AUTH_TOKEN': 'test_twilio_token',
        'SENDGRID_API_KEY': 'test_sendgrid_key',
        'APOLLO_API_KEY': 'test_apollo_key',
        'WEBHOOK_SECRET_KEY': 'test_webhook_secret'
    }
    
    # Set environment variables
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    logger.info(f"Test environment configured with {len(test_env)} variables")
    
    yield test_env
    
    # Restore original environment
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value
    
    logger.info("Test environment cleaned up")


@pytest.fixture
async def mock_database_service():
    """Mock database service for testing"""
    from tests.mocks.external_services import MockDatabaseService
    
    db_service = MockDatabaseService()
    
    # Pre-populate with test data
    test_leads = [
        {
            'lead_id': 'TEST_LEAD_001',
            'email': 'test1@example.com',
            'first_name': 'Test',
            'last_name': 'User1',
            'created_at': '2026-01-17T10:00:00Z'
        },
        {
            'lead_id': 'TEST_LEAD_002', 
            'email': 'test2@example.com',
            'first_name': 'Test',
            'last_name': 'User2',
            'created_at': '2026-01-17T11:00:00Z'
        }
    ]
    
    for lead in test_leads:
        await db_service.save_lead(lead['lead_id'], lead)
    
    logger.info(f"Mock database initialized with {len(test_leads)} test leads")
    return db_service


@pytest.fixture
async def mock_redis_cache():
    """Mock Redis cache service for testing"""
    from tests.mocks.external_services import MockRedisClient
    
    cache_service = MockRedisClient()
    
    # Pre-populate with test cache data
    test_cache_data = {
        'test_key_1': '{"data": "test_value_1"}',
        'test_key_2': '{"data": "test_value_2"}',
        'lead_score:TEST_LEAD_001': '{"score": 85.5, "confidence": 0.92}'
    }
    
    for key, value in test_cache_data.items():
        await cache_service.set(key, value, ttl=3600)
    
    logger.info(f"Mock cache initialized with {len(test_cache_data)} test entries")
    return cache_service


@pytest.fixture
async def mock_external_services():
    """Mock all external services for integration testing"""
    from tests.mocks.external_services import (
        MockClaudeClient, MockApolloClient, 
        MockTwilioClient, MockSendGridClient
    )
    
    services = {
        'claude': MockClaudeClient(),
        'apollo': MockApolloClient(),
        'twilio': MockTwilioClient(),
        'sendgrid': MockSendGridClient()
    }
    
    logger.info("Mock external services initialized")
    return services


@pytest.fixture
async def service6_test_config():
    """Service 6 test configuration"""
    from ghl_real_estate_ai.services.service6_ai_integration import Service6AIConfig
    
    config = Service6AIConfig(
        enable_advanced_ml_scoring=True,
        enable_voice_ai=True,
        enable_predictive_analytics=True,
        enable_realtime_inference=True,
        enable_claude_enhancement=True,
        max_concurrent_operations=10,  # Reduced for testing
        default_cache_ttl_seconds=60,  # Shorter for tests
        ml_model_confidence_threshold=0.6,  # Lower for testing
        enable_background_processing=False  # Disabled for deterministic tests
    )
    
    logger.info("Service 6 test configuration created")
    return config


@pytest.fixture
async def integrated_service6_stack(mock_database_service, mock_redis_cache, 
                                  mock_external_services, service6_test_config):
    """Fully integrated Service 6 stack for testing"""
    from ghl_real_estate_ai.services.service6_ai_integration import Service6AIOrchestrator
    from ghl_real_estate_ai.services.autonomous_followup_engine import AutonomousFollowUpEngine
    
    # Create orchestrator
    orchestrator = Service6AIOrchestrator(service6_test_config)
    
    # Create follow-up engine
    followup_engine = AutonomousFollowUpEngine()
    followup_engine.database_service = mock_database_service
    followup_engine.cache = mock_redis_cache
    
    # Mock orchestrator's AI companion
    orchestrator.ai_companion = MagicMock()
    orchestrator.ai_companion.initialize = AsyncMock()
    
    # Create realistic AI analysis mock
    async def mock_analysis(lead_id, lead_data, **kwargs):
        from tests.mocks.external_services import create_mock_service6_response
        await asyncio.sleep(0.01)  # Simulate processing time
        return create_mock_service6_response(lead_id)
    
    orchestrator.ai_companion.comprehensive_lead_analysis = mock_analysis
    orchestrator.ai_companion.realtime_lead_scoring = AsyncMock()
    orchestrator.ai_companion.voice_call_coaching = AsyncMock()
    orchestrator.ai_companion.generate_behavioral_insights = AsyncMock()
    
    # Initialize services
    await orchestrator.initialize()
    
    stack = {
        'orchestrator': orchestrator,
        'followup_engine': followup_engine,
        'database': mock_database_service,
        'cache': mock_redis_cache,
        'external_services': mock_external_services
    }
    
    logger.info("Integrated Service 6 stack initialized for testing")
    return stack


@pytest.fixture
def test_lead_data():
    """Generate test lead data"""
    from tests.mocks.external_services import create_test_lead_data
    
    return create_test_lead_data({
        'lead_id': 'FIXTURE_TEST_LEAD_001',
        'email': 'fixture.test@example.com',
        'first_name': 'Fixture',
        'last_name': 'TestLead'
    })


@pytest.fixture
def webhook_test_payloads():
    """Generate test webhook payloads"""
    from tests.mocks.external_services import MockWebhookPayloads
    
    return {
        'ghl_lead': MockWebhookPayloads.ghl_lead_webhook(),
        'twilio_voice': MockWebhookPayloads.twilio_voice_webhook(),
        'sendgrid_events': MockWebhookPayloads.sendgrid_event_webhook(),
        'apollo_enrichment': MockWebhookPayloads.apollo_webhook()
    }


@pytest.fixture
async def performance_metrics():
    """Performance metrics collector for testing"""
    from tests.performance.test_service6_performance_load import PerformanceMetrics
    
    metrics = PerformanceMetrics()
    yield metrics
    
    # Log performance summary if metrics were collected
    if metrics.response_times:
        summary = metrics.get_summary()
        logger.info(f"Test performance summary: {summary}")


@pytest.fixture
def security_test_config():
    """Security testing configuration"""
    return {
        'enable_signature_validation': True,
        'enable_rate_limiting': True,
        'enable_input_sanitization': True,
        'webhook_signature_secrets': {
            'ghl': 'test_ghl_secret_key',
            'twilio': 'test_twilio_auth_token',
            'sendgrid': 'test_sendgrid_webhook_secret'
        },
        'rate_limits': {
            'requests_per_minute': 100,
            'burst_allowance': 20
        }
    }


# Test data cleanup fixtures
@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_data():
    """Automatically clean up test data after each test"""
    yield
    
    # Cleanup operations would go here
    # For mocked services, this is handled automatically
    # For real services, we would clean up test data
    
    logger.debug("Test data cleanup completed")


# Performance monitoring fixtures
@pytest.fixture(autouse=True)
def monitor_test_performance(request):
    """Monitor test performance automatically"""
    import time
    import psutil
    
    # Start monitoring
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    yield
    
    # End monitoring
    end_time = time.time()
    end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    test_duration = end_time - start_time
    memory_delta = end_memory - start_memory
    
    # Log performance warnings
    if test_duration > 10.0:  # 10 second threshold
        logger.warning(f"Slow test {request.node.name}: {test_duration:.2f}s")
    
    if memory_delta > 100:  # 100MB threshold
        logger.warning(f"High memory test {request.node.name}: +{memory_delta:.1f}MB")


# Error handling fixtures
@pytest.fixture
def error_scenarios():
    """Common error scenarios for testing"""
    return {
        'database_connection_error': Exception("Database connection failed"),
        'external_service_timeout': Exception("External service timeout"),
        'invalid_data_format': ValueError("Invalid data format"),
        'authentication_failure': Exception("Authentication failed"),
        'rate_limit_exceeded': Exception("Rate limit exceeded"),
        'insufficient_permissions': Exception("Insufficient permissions")
    }


# Logging fixtures
@pytest.fixture(autouse=True)
def capture_logs(caplog):
    """Automatically capture logs for all tests"""
    caplog.set_level(logging.INFO)
    yield caplog


# Skip markers for CI/CD
def pytest_runtest_setup(item):
    """Setup function to skip tests based on environment"""
    
    # Skip slow tests in CI unless specifically requested
    if item.get_closest_marker("slow") and os.environ.get("CI") and not os.environ.get("RUN_SLOW_TESTS"):
        pytest.skip("Slow test skipped in CI environment")
    
    # Skip performance tests in limited environments
    if item.get_closest_marker("performance") and os.environ.get("LIMITED_RESOURCES"):
        pytest.skip("Performance test skipped due to resource limitations")


# Async test configuration
pytest_plugins = ['pytest_asyncio']

# Configure async test mode
@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for async tests"""
    try:
        return asyncio.DefaultEventLoopPolicy()
    except DeprecationWarning:
        # Python 3.16+ removes DefaultEventLoopPolicy
        return None


# Test report generation hooks removed to avoid dependency on pytest-html

if __name__ == "__main__":
    # This file is imported, not executed directly
    pass