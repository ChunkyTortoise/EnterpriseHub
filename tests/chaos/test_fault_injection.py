#!/usr/bin/env python3
"""
Chaos Engineering Suite for Fault Injection Testing
====================================================

Tests system resilience under failure conditions and validates graceful degradation.
Focuses on real-world failure scenarios that could impact business operations.

Chaos Engineering Strategy:
- AI service failures and fallback mechanisms
- Database connection loss recovery
- Redis cache failures with graceful degradation
- Network timeout handling and retries
- Circuit breaker validation under load
- Cascading failure prevention

Resilience Testing Coverage:
- External API unavailability (Claude, GHL, Apollo)
- Infrastructure failures (Redis, PostgreSQL)
- Partial system degradation scenarios
- Recovery behavior validation
- Business continuity under stress
"""

import asyncio
import random
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.enhanced_lead_intelligence import EnhancedLeadIntelligence
from ghl_real_estate_ai.services.lead_scorer import LeadScorer
from tests.mocks.external_services import MockClaudeClient, MockDatabaseService, MockRedisClient, create_test_lead_data


class FailureType(Enum):
    """Types of failures to inject"""

    TIMEOUT = "timeout"
    CONNECTION_ERROR = "connection_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    RATE_LIMIT = "rate_limit"
    PARTIAL_FAILURE = "partial_failure"
    DATA_CORRUPTION = "data_corruption"
    MEMORY_EXHAUSTION = "memory_exhaustion"
    NETWORK_PARTITION = "network_partition"


@dataclass
class ChaosExperiment:
    """Definition of a chaos engineering experiment"""

    name: str
    description: str
    failure_type: FailureType
    target_service: str
    failure_probability: float  # 0.0 to 1.0
    duration_seconds: float
    expected_behavior: str
    recovery_time_limit: float  # Maximum acceptable recovery time


class ChaosInjector:
    """Utility for injecting controlled failures"""

    def __init__(self):
        self.active_failures = {}
        self.failure_history = []

    @asynccontextmanager
    async def inject_failure(self, experiment: ChaosExperiment):
        """Context manager for controlled failure injection"""
        failure_id = f"{experiment.target_service}_{experiment.failure_type.value}_{int(time.time())}"

        try:
            # Start failure injection
            self.active_failures[failure_id] = {"experiment": experiment, "start_time": time.time(), "failure_count": 0}

            yield self._create_failure_function(experiment, failure_id)

        finally:
            # Clean up failure injection
            if failure_id in self.active_failures:
                failure_data = self.active_failures[failure_id]
                failure_data["end_time"] = time.time()
                failure_data["duration"] = failure_data["end_time"] - failure_data["start_time"]

                self.failure_history.append(failure_data)
                del self.active_failures[failure_id]

    def _create_failure_function(self, experiment: ChaosExperiment, failure_id: str) -> Callable:
        """Create a function that simulates the specified failure"""

        def should_fail() -> bool:
            """Determine if this call should fail based on probability"""
            if failure_id not in self.active_failures:
                return False

            # Check if failure duration exceeded
            failure_data = self.active_failures[failure_id]
            if time.time() - failure_data["start_time"] > experiment.duration_seconds:
                return False

            # Apply probability
            if random.random() < experiment.failure_probability:
                failure_data["failure_count"] += 1
                return True

            return False

        def failure_function(*args, **kwargs):
            """Function that conditionally raises failures"""
            if should_fail():
                if experiment.failure_type == FailureType.TIMEOUT:
                    raise asyncio.TimeoutError(f"Chaos timeout in {experiment.target_service}")
                elif experiment.failure_type == FailureType.CONNECTION_ERROR:
                    raise ConnectionError(f"Chaos connection error in {experiment.target_service}")
                elif experiment.failure_type == FailureType.SERVICE_UNAVAILABLE:
                    raise Exception(f"Chaos service unavailable: {experiment.target_service}")
                elif experiment.failure_type == FailureType.RATE_LIMIT:
                    raise Exception(f"Chaos rate limit exceeded: {experiment.target_service}")
                elif experiment.failure_type == FailureType.PARTIAL_FAILURE:
                    # Return corrupted/incomplete data instead of failing
                    return {"error": "partial_failure", "data": None}
                else:
                    raise Exception(f"Chaos {experiment.failure_type.value}: {experiment.target_service}")

            # Normal operation - call original function or return mock data
            return None  # Let the test handle normal operation

        return failure_function


class TestClaudeAPIResilience:
    """Chaos tests for Claude API failures and recovery"""

    def setup_method(self):
        self.intelligence = EnhancedLeadIntelligence()
        self.chaos_injector = ChaosInjector()

    @pytest.mark.asyncio
    async def test_claude_timeout_graceful_degradation(self):
        """
        Chaos Test: Claude API timeout should trigger fallback analysis
        Expected: System continues with reduced functionality, no complete failure
        """
        experiment = ChaosExperiment(
            name="Claude Timeout Test",
            description="Test graceful degradation when Claude API times out",
            failure_type=FailureType.TIMEOUT,
            target_service="claude_api",
            failure_probability=1.0,  # Always fail
            duration_seconds=10.0,
            expected_behavior="Fallback analysis provided",
            recovery_time_limit=2.0,
        )

        lead_data = create_test_lead_data(
            {"lead_name": "Timeout Test Lead", "budget": "$500,000", "timeline": "soon", "location": "Rancho Cucamonga"}
        )

        async with self.chaos_injector.inject_failure(experiment) as failure_func:
            # Inject Claude API timeout
            with patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator") as mock_claude:
                mock_claude_instance = MagicMock()
                mock_claude_instance.chat_query = AsyncMock(side_effect=asyncio.TimeoutError("Claude timeout"))
                mock_claude.return_value = mock_claude_instance

                # WHEN: Lead analysis is attempted during Claude failure
                start_time = time.time()

                try:
                    analysis_result = await self.intelligence.get_comprehensive_lead_analysis(
                        lead_name=lead_data["lead_name"],
                        lead_context={"extracted_preferences": lead_data},
                        force_refresh=True,
                    )

                    recovery_time = time.time() - start_time

                    # THEN: System should provide fallback analysis
                    assert analysis_result is not None, "No fallback analysis provided"
                    assert analysis_result.final_score > 0, "Fallback analysis has invalid score"
                    assert analysis_result.classification == "error", "Error state not properly indicated"
                    assert recovery_time < experiment.recovery_time_limit, f"Recovery too slow: {recovery_time}s"

                    # Validate fallback behavior
                    assert "error" in analysis_result.strategic_summary.lower(), "Fallback doesn't indicate error state"
                    assert analysis_result.confidence_score < 0.5, "Fallback confidence should be low"

                except Exception as e:
                    pytest.fail(f"System failed to provide graceful degradation: {e}")

    @pytest.mark.asyncio
    async def test_claude_intermittent_failure_circuit_breaker(self):
        """
        Chaos Test: Intermittent Claude failures should trigger circuit breaker
        Expected: Circuit breaker prevents cascading failures
        """
        experiment = ChaosExperiment(
            name="Claude Intermittent Failure",
            description="Test circuit breaker behavior with intermittent failures",
            failure_type=FailureType.SERVICE_UNAVAILABLE,
            target_service="claude_api",
            failure_probability=0.7,  # 70% failure rate
            duration_seconds=15.0,
            expected_behavior="Circuit breaker activation",
            recovery_time_limit=3.0,
        )

        test_leads = [create_test_lead_data({"lead_name": f"Test Lead {i}"}) for i in range(10)]

        async with self.chaos_injector.inject_failure(experiment) as failure_func:
            with patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator") as mock_claude:
                # Create unreliable Claude mock
                def unreliable_claude(*args, **kwargs):
                    if random.random() < 0.7:  # 70% failure rate
                        raise Exception("Claude service unavailable")
                    return AsyncMock()

                mock_claude_instance = MagicMock()
                mock_claude_instance.chat_query = AsyncMock(side_effect=unreliable_claude)
                mock_claude.return_value = mock_claude_instance

                # WHEN: Multiple requests are made during unreliable service
                successful_analyses = 0
                fallback_analyses = 0
                circuit_breaker_activations = 0

                for lead in test_leads:
                    try:
                        start_time = time.time()
                        analysis_result = await self.intelligence.get_comprehensive_lead_analysis(
                            lead_name=lead["lead_name"], lead_context={"extracted_preferences": lead}
                        )

                        response_time = time.time() - start_time

                        if analysis_result.classification == "error":
                            fallback_analyses += 1
                            # Fast response indicates circuit breaker (no actual API call)
                            if response_time < 0.1:
                                circuit_breaker_activations += 1
                        else:
                            successful_analyses += 1

                    except Exception as e:
                        fallback_analyses += 1

                # THEN: Circuit breaker should prevent system overload
                total_requests = len(test_leads)
                assert fallback_analyses > 0, "No fallback behavior detected"

                # At least some requests should be fast (circuit breaker active)
                circuit_breaker_rate = circuit_breaker_activations / total_requests
                assert circuit_breaker_rate > 0.3, f"Circuit breaker not activating effectively: {circuit_breaker_rate}"


class TestDatabaseResilienceUnderChaos:
    """Chaos tests for database connection failures and recovery"""

    def setup_method(self):
        self.intelligence = EnhancedLeadIntelligence()
        self.chaos_injector = ChaosInjector()

    @pytest.mark.asyncio
    async def test_database_connection_loss_recovery(self):
        """
        Chaos Test: Database connection loss should not crash lead analysis
        Expected: Degraded functionality with cache fallback
        """
        experiment = ChaosExperiment(
            name="Database Connection Loss",
            description="Test system behavior when database becomes unavailable",
            failure_type=FailureType.CONNECTION_ERROR,
            target_service="database",
            failure_probability=1.0,
            duration_seconds=5.0,
            expected_behavior="Cache fallback operation",
            recovery_time_limit=1.0,
        )

        lead_data = create_test_lead_data({"lead_name": "DB Failure Test"})

        async with self.chaos_injector.inject_failure(experiment):
            # Mock database failure
            with patch.object(self.intelligence, "_enhanced_analysis_with_optimizations") as mock_analysis:
                mock_analysis.side_effect = ConnectionError("Database connection failed")

                # WHEN: Analysis is attempted during database failure
                start_time = time.time()

                try:
                    analysis_result = await self.intelligence.get_comprehensive_lead_analysis(
                        lead_name=lead_data["lead_name"], lead_context={"extracted_preferences": lead_data}
                    )

                    recovery_time = time.time() - start_time

                    # THEN: System should handle database failure gracefully
                    assert analysis_result is not None, "No fallback provided for database failure"
                    assert recovery_time < experiment.recovery_time_limit, f"Recovery too slow: {recovery_time}s"

                    # Validate degraded but functional state
                    assert analysis_result.final_score >= 0, "Invalid fallback score"
                    assert "error" in analysis_result.strategic_summary.lower(), "Error state not indicated"

                except Exception as e:
                    pytest.fail(f"Database failure caused complete system failure: {e}")


class TestRedisResilienceUnderChaos:
    """Chaos tests for Redis cache failures and graceful degradation"""

    def setup_method(self):
        self.intelligence = EnhancedLeadIntelligence()
        self.chaos_injector = ChaosInjector()

    @pytest.mark.asyncio
    async def test_redis_failure_performance_degradation(self):
        """
        Chaos Test: Redis failure should degrade performance but maintain functionality
        Expected: Increased latency but successful operation
        """
        experiment = ChaosExperiment(
            name="Redis Cache Failure",
            description="Test performance degradation when Redis cache fails",
            failure_type=FailureType.SERVICE_UNAVAILABLE,
            target_service="redis_cache",
            failure_probability=1.0,
            duration_seconds=8.0,
            expected_behavior="Increased latency, maintained functionality",
            recovery_time_limit=10.0,  # Allows for slower operation without cache
        )

        test_leads = [create_test_lead_data({"lead_name": f"Cache Test Lead {i}"}) for i in range(3)]

        async with self.chaos_injector.inject_failure(experiment):
            # Mock Redis cache failure
            with patch.object(self.intelligence, "optimized_cache", None):
                # Force cache misses by removing cache layer

                # WHEN: Multiple analyses are performed without cache
                analysis_times = []
                successful_analyses = 0

                for lead in test_leads:
                    try:
                        start_time = time.time()

                        analysis_result = await self.intelligence.get_comprehensive_lead_analysis(
                            lead_name=lead["lead_name"], lead_context={"extracted_preferences": lead}
                        )

                        end_time = time.time()
                        analysis_times.append(end_time - start_time)

                        # Validate functionality maintained despite cache failure
                        assert analysis_result is not None, "Analysis failed without cache"
                        assert analysis_result.final_score > 0, "Invalid analysis without cache"
                        successful_analyses += 1

                    except Exception as e:
                        pytest.fail(f"Cache failure caused analysis failure: {e}")

                # THEN: All analyses should succeed despite performance impact
                assert successful_analyses == len(test_leads), "Not all analyses succeeded without cache"

                # Performance should be degraded but within acceptable limits
                avg_analysis_time = sum(analysis_times) / len(analysis_times)
                assert avg_analysis_time < experiment.recovery_time_limit, (
                    f"Performance degradation too severe: {avg_analysis_time}s"
                )


class TestCascadingFailurePrevention:
    """Chaos tests for preventing cascading failures across services"""

    def setup_method(self):
        self.intelligence = EnhancedLeadIntelligence()
        self.chaos_injector = ChaosInjector()

    @pytest.mark.asyncio
    async def test_multi_service_failure_isolation(self):
        """
        Chaos Test: Multiple service failures should be isolated, not cascading
        Expected: Partial functionality maintained despite multiple failures
        """
        # Simulate multiple simultaneous failures
        experiments = [
            ChaosExperiment(
                name="Multi-Service Failure - Claude",
                description="Claude API failure in multi-service chaos",
                failure_type=FailureType.TIMEOUT,
                target_service="claude_api",
                failure_probability=1.0,
                duration_seconds=10.0,
                expected_behavior="Isolated failure",
                recovery_time_limit=3.0,
            ),
            ChaosExperiment(
                name="Multi-Service Failure - Cache",
                description="Cache failure in multi-service chaos",
                failure_type=FailureType.CONNECTION_ERROR,
                target_service="redis_cache",
                failure_probability=1.0,
                duration_seconds=10.0,
                expected_behavior="Isolated failure",
                recovery_time_limit=3.0,
            ),
        ]

        lead_data = create_test_lead_data({"lead_name": "Multi-Failure Test"})

        # Inject multiple failures simultaneously
        with patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator") as mock_claude:
            mock_claude_instance = MagicMock()
            mock_claude_instance.chat_query = AsyncMock(side_effect=asyncio.TimeoutError("Claude failure"))
            mock_claude.return_value = mock_claude_instance

            with patch.object(self.intelligence, "optimized_cache", None):  # Simulate cache failure
                # WHEN: Analysis is attempted during multiple service failures
                start_time = time.time()

                try:
                    analysis_result = await self.intelligence.get_comprehensive_lead_analysis(
                        lead_name=lead_data["lead_name"], lead_context={"extracted_preferences": lead_data}
                    )

                    recovery_time = time.time() - start_time

                    # THEN: System should provide minimal viable service
                    assert analysis_result is not None, "Complete system failure during multi-service chaos"
                    assert recovery_time < 5.0, f"Recovery too slow during multi-failure: {recovery_time}s"

                    # Validate minimal viable functionality
                    assert analysis_result.final_score >= 0, "Invalid score during multi-failure"
                    assert analysis_result.lead_name == lead_data["lead_name"], "Lead identity lost during failures"

                    # Error state should be clearly indicated
                    assert analysis_result.confidence_score < 0.5, "Confidence should be low during multi-failure"

                except Exception as e:
                    pytest.fail(f"Cascading failure detected: {e}")


class TestSystemRecoveryBehavior:
    """Chaos tests for system recovery after failures are resolved"""

    def setup_method(self):
        self.intelligence = EnhancedLeadIntelligence()
        self.chaos_injector = ChaosInjector()

    @pytest.mark.asyncio
    async def test_service_recovery_detection(self):
        """
        Chaos Test: System should detect and utilize recovered services
        Expected: Gradual return to full functionality as services recover
        """
        lead_data = create_test_lead_data({"lead_name": "Recovery Test Lead"})

        # Test recovery from Claude API failure
        with patch("ghl_real_estate_ai.services.enhanced_lead_intelligence.get_claude_orchestrator") as mock_claude:
            # Phase 1: Service is failing
            mock_claude_instance = MagicMock()
            mock_claude_instance.chat_query = AsyncMock(side_effect=Exception("Claude temporarily unavailable"))
            mock_claude.return_value = mock_claude_instance

            # WHEN: Analysis during failure
            failed_analysis = await self.intelligence.get_comprehensive_lead_analysis(
                lead_name=lead_data["lead_name"], lead_context={"extracted_preferences": lead_data}
            )

            # THEN: Should get degraded service
            assert failed_analysis.classification == "error", "Error state not detected during failure"

            # Phase 2: Service recovers
            mock_claude_instance.chat_query = AsyncMock(
                return_value=MagicMock(content="Recovered analysis content", confidence=0.9)
            )

            # WHEN: Analysis after recovery
            await asyncio.sleep(0.1)  # Brief pause to simulate recovery
            recovered_analysis = await self.intelligence.get_comprehensive_lead_analysis(
                lead_name=lead_data["lead_name"],
                lead_context={"extracted_preferences": lead_data},
                force_refresh=True,  # Bypass cache to test recovery
            )

            # THEN: Should get restored functionality
            # Note: This test validates the contract that the system can recover
            # In practice, recovery detection might be more sophisticated
            assert recovered_analysis is not None, "System didn't recover after service restoration"


class TestBusinessContinuityUnderChaos:
    """Chaos tests for business continuity during various failure scenarios"""

    def setup_method(self):
        self.scorer = LeadScorer()
        self.intelligence = EnhancedLeadIntelligence()

    def test_core_business_logic_chaos_resistance(self):
        """
        Chaos Test: Core business logic should be resilient to infrastructure failures
        Expected: Lead scoring continues even when enhanced services fail
        """
        # Core business logic should always work
        test_scenarios = [
            {
                "name": "High Intent Lead - Infrastructure Chaos",
                "data": {"budget": "$600,000", "timeline": "immediate", "location": "Rancho Cucamonga", "financing": "cash"},
                "expected_min_score": 4,
            },
            {
                "name": "Standard Lead - Infrastructure Chaos",
                "data": {"budget": "$400,000", "location": "Rancho Cucamonga suburbs"},
                "expected_min_score": 2,
            },
        ]

        for scenario in test_scenarios:
            # WHEN: Core scoring during simulated infrastructure chaos
            context = {"extracted_preferences": scenario["data"]}

            # Core scorer should always work regardless of other service failures
            score = self.scorer.calculate(context)
            classification = self.scorer.classify(score)
            reasoning = self.scorer.calculate_with_reasoning(context)

            # THEN: Business logic should be unaffected by infrastructure
            assert score >= scenario["expected_min_score"], (
                f"{scenario['name']} core scoring degraded: {score} < {scenario['expected_min_score']}"
            )

            assert classification in ["hot", "warm", "cold"], (
                f"{scenario['name']} invalid classification during chaos: {classification}"
            )

            assert len(reasoning.get("recommended_actions", [])) > 0, (
                f"{scenario['name']} no recommended actions during chaos"
            )

            # Business continuity validation
            assert reasoning.get("score") == score, f"{scenario['name']} score consistency broken during chaos"


if __name__ == "__main__":
    # Run chaos engineering tests
    pytest.main([__file__, "-v", "--tb=short", "-x"])  # Stop on first failure for chaos tests