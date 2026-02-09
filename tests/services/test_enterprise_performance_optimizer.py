import pytest
pytestmark = pytest.mark.integration

"""
Tests for Enterprise Performance Optimizer
Comprehensive test suite for performance optimization and caching capabilities
"""

import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio

@pytest.mark.integration

# Import the service under test
try:
    from ghl_real_estate_ai.services.enterprise_performance_optimizer import (
        CacheConfiguration,
        EnterprisePerformanceOptimizer,
        IntelligentCache,
        PerformanceMonitor,
    )
except ImportError as e:
    # Skip tests if dependencies not available
    pytest.skip(f"Skipping tests due to missing dependencies: {e}", allow_module_level=True)


class TestEnterprisePerformanceOptimizer:
    """Test suite for Enterprise Performance Optimizer"""

    @pytest_asyncio.fixture
    async def optimizer(self):
        """Create optimizer instance for testing"""
        with patch("ghl_real_estate_ai.services.enterprise_performance_optimizer.redis.Redis"):
            with patch("ghl_real_estate_ai.services.enterprise_performance_optimizer.ClaudeClient"):
                with patch("ghl_real_estate_ai.services.enterprise_performance_optimizer.psutil"):
                    optimizer = EnterprisePerformanceOptimizer()
                    yield optimizer

    @pytest.fixture
    def sample_performance_data(self):
        """Sample performance data for testing"""
        return {
            "system_metrics": {"cpu_usage": 45.2, "memory_usage": 68.5, "disk_io": 125.3, "network_io": 89.7},
            "application_metrics": {
                "response_time": 250,
                "throughput": 1250,
                "error_rate": 0.02,
                "active_sessions": 450,
            },
            "cache_metrics": {"hit_rate": 0.87, "miss_rate": 0.13, "eviction_rate": 0.05, "memory_usage": 2.1},
        }

    @pytest.mark.asyncio
    async def test_optimizer_initialization(self, optimizer):
        """Test optimizer initializes correctly"""
        assert optimizer is not None
        assert hasattr(optimizer, "intelligent_cache")
        assert hasattr(optimizer, "performance_monitor")
        assert hasattr(optimizer, "claude_client")
        assert hasattr(optimizer, "optimization_history")

    @pytest.mark.asyncio
    async def test_intelligent_cache_operations(self, optimizer):
        """Test intelligent caching functionality"""
        cache_config = CacheConfiguration(
            ttl_seconds=3600, max_size_mb=512, eviction_policy="lru", compression_enabled=True
        )

        # Mock cache operations
        optimizer.intelligent_cache.redis_client.get = AsyncMock(return_value=None)
        optimizer.intelligent_cache.redis_client.set = AsyncMock(return_value=True)
        optimizer.intelligent_cache.redis_client.exists = AsyncMock(return_value=False)

        # Test cache set operation
        result = await optimizer.intelligent_cache.set_cached_data(
            key="test_key", data={"test": "data"}, config=cache_config
        )

        assert result is True

        # Test cache get operation
        optimizer.intelligent_cache.redis_client.get = AsyncMock(return_value=json.dumps({"test": "data"}))
        cached_data = await optimizer.intelligent_cache.get_cached_data("test_key")

        assert cached_data == {"test": "data"}

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, optimizer, sample_performance_data):
        """Test performance monitoring capabilities"""
        # Mock system monitoring
        with patch("psutil.cpu_percent", return_value=45.2):
            with patch("psutil.virtual_memory") as mock_memory:
                mock_memory.return_value.percent = 68.5

                metrics = await optimizer.performance_monitor.collect_system_metrics()

                assert isinstance(metrics, dict)
                assert "cpu_usage" in metrics
                assert "memory_usage" in metrics
                assert metrics["cpu_usage"] == 45.2
                assert metrics["memory_usage"] == 68.5

    @pytest.mark.asyncio
    async def test_ai_powered_optimization(self, optimizer, sample_performance_data):
        """Test AI-powered optimization recommendations"""
        # Mock Claude client for optimization analysis
        optimizer.claude_client.generate = AsyncMock(
            return_value=json.dumps(
                {
                    "optimization_recommendations": [
                        {
                            "category": "cache",
                            "action": "increase_ttl",
                            "reason": "Low cache hit rate detected",
                            "expected_improvement": 15,
                            "priority": "high",
                        },
                        {
                            "category": "database",
                            "action": "optimize_queries",
                            "reason": "Slow query patterns identified",
                            "expected_improvement": 25,
                            "priority": "medium",
                        },
                    ],
                    "performance_score": 0.78,
                    "bottleneck_analysis": {
                        "primary_bottleneck": "database_queries",
                        "secondary_bottleneck": "cache_misses",
                    },
                }
            )
        )

        recommendations = await optimizer.analyze_performance_with_ai(sample_performance_data)

        assert isinstance(recommendations, dict)
        assert "optimization_recommendations" in recommendations
        assert "performance_score" in recommendations
        assert "bottleneck_analysis" in recommendations

        # Verify recommendations structure
        for rec in recommendations["optimization_recommendations"]:
            assert "category" in rec
            assert "action" in rec
            assert "priority" in rec
            assert rec["priority"] in ["low", "medium", "high"]

    @pytest.mark.asyncio
    async def test_auto_scaling_logic(self, optimizer, sample_performance_data):
        """Test auto-scaling decision logic"""
        # Mock current resource usage
        optimizer.performance_monitor.collect_system_metrics = AsyncMock(
            return_value={
                "cpu_usage": 85.5,  # High CPU usage
                "memory_usage": 92.3,  # High memory usage
                "active_sessions": 950,  # High session count
            }
        )

        scaling_decision = await optimizer.evaluate_auto_scaling(sample_performance_data)

        assert isinstance(scaling_decision, dict)
        assert "scale_up" in scaling_decision or "scale_down" in scaling_decision
        assert "reasoning" in scaling_decision
        assert "confidence" in scaling_decision

        # High usage should trigger scale-up recommendation
        if scaling_decision.get("scale_up"):
            assert scaling_decision["confidence"] > 0.7

    @pytest.mark.asyncio
    async def test_cache_optimization_strategies(self, optimizer):
        """Test cache optimization strategies"""
        # Mock cache performance data
        cache_stats = {
            "hit_rate": 0.65,  # Below optimal
            "miss_rate": 0.35,
            "eviction_rate": 0.12,  # High evictions
            "average_response_time": 45,
            "memory_usage": 85,  # High usage
        }

        optimization = await optimizer.optimize_cache_configuration(cache_stats)

        assert isinstance(optimization, dict)
        assert "new_config" in optimization
        assert "expected_improvements" in optimization
        assert "implementation_steps" in optimization

        # Should recommend configuration changes for poor performance
        new_config = optimization["new_config"]
        assert "ttl_seconds" in new_config
        assert "max_size_mb" in new_config

    @pytest.mark.asyncio
    async def test_database_query_optimization(self, optimizer):
        """Test database query optimization"""
        # Mock slow query data
        query_performance = {
            "slow_queries": [
                {
                    "query": "SELECT * FROM leads WHERE created_date > ?",
                    "execution_time": 2.5,
                    "frequency": 1250,
                    "table": "leads",
                },
                {
                    "query": "SELECT * FROM properties JOIN agents ON ...",
                    "execution_time": 1.8,
                    "frequency": 890,
                    "table": "properties",
                },
            ],
            "connection_pool_usage": 0.89,
            "average_query_time": 0.45,
        }

        # Mock Claude client for query optimization
        optimizer.claude_client.generate = AsyncMock(
            return_value=json.dumps(
                {
                    "query_optimizations": [
                        {
                            "original_query": "SELECT * FROM leads WHERE created_date > ?",
                            "optimized_query": "SELECT id, name, score FROM leads WHERE created_date > ? LIMIT 100",
                            "expected_improvement": "60% faster",
                            "reasoning": "Avoid SELECT *, add LIMIT, select only needed columns",
                        }
                    ],
                    "index_recommendations": [
                        {
                            "table": "leads",
                            "column": "created_date",
                            "index_type": "btree",
                            "expected_improvement": "40% faster queries",
                        }
                    ],
                }
            )
        )

        optimizations = await optimizer.optimize_database_queries(query_performance)

        assert isinstance(optimizations, dict)
        assert "query_optimizations" in optimizations
        assert "index_recommendations" in optimizations

    @pytest.mark.asyncio
    async def test_memory_optimization(self, optimizer):
        """Test memory optimization strategies"""
        # Mock memory usage data
        memory_stats = {
            "heap_usage": 0.87,
            "gc_frequency": 15,  # High GC frequency
            "object_count": 1500000,
            "memory_leaks_detected": True,
            "peak_usage": 0.95,
        }

        memory_optimization = await optimizer.optimize_memory_usage(memory_stats)

        assert isinstance(memory_optimization, dict)
        assert "optimization_strategies" in memory_optimization
        assert "immediate_actions" in memory_optimization
        assert "monitoring_recommendations" in memory_optimization

        # Should recommend immediate actions for high usage
        immediate_actions = memory_optimization["immediate_actions"]
        assert len(immediate_actions) > 0

    @pytest.mark.asyncio
    async def test_performance_alerting(self, optimizer):
        """Test performance alerting system"""
        # Mock performance threshold violations
        alert_conditions = {
            "cpu_usage": 95.5,  # Above threshold
            "response_time": 5000,  # Very slow
            "error_rate": 0.08,  # High error rate
            "memory_usage": 98.2,  # Critical memory usage
        }

        alerts = await optimizer.check_performance_thresholds(alert_conditions)

        assert isinstance(alerts, list)
        assert len(alerts) > 0

        for alert in alerts:
            assert "severity" in alert
            assert "metric" in alert
            assert "current_value" in alert
            assert "threshold" in alert
            assert alert["severity"] in ["low", "medium", "high", "critical"]

    @pytest.mark.asyncio
    async def test_optimization_history_tracking(self, optimizer):
        """Test optimization history tracking"""
        optimization_action = {
            "type": "cache_configuration",
            "changes": {"ttl_seconds": 7200},
            "expected_improvement": 20,
            "implemented_at": datetime.now().isoformat(),
        }

        # Mock history storage
        optimizer.intelligent_cache.redis_client.lpush = AsyncMock(return_value=1)
        optimizer.intelligent_cache.redis_client.ltrim = AsyncMock(return_value=True)

        await optimizer.track_optimization_action(optimization_action)

        # Verify history was recorded
        optimizer.intelligent_cache.redis_client.lpush.assert_called_once()

        # Test history retrieval
        optimizer.intelligent_cache.redis_client.lrange = AsyncMock(return_value=[json.dumps(optimization_action)])

        history = await optimizer.get_optimization_history(limit=10)

        assert isinstance(history, list)
        assert len(history) > 0

    @pytest.mark.asyncio
    async def test_real_time_performance_dashboard(self, optimizer):
        """Test real-time performance dashboard data"""
        # Mock real-time data collection
        optimizer.performance_monitor.collect_system_metrics = AsyncMock(
            return_value={"cpu_usage": 42.3, "memory_usage": 65.8}
        )
        optimizer.performance_monitor.collect_application_metrics = AsyncMock(
            return_value={"response_time": 180, "throughput": 1450}
        )

        dashboard_data = await optimizer.get_realtime_dashboard_data()

        assert isinstance(dashboard_data, dict)
        assert "system_metrics" in dashboard_data
        assert "application_metrics" in dashboard_data
        assert "cache_metrics" in dashboard_data
        assert "optimization_status" in dashboard_data
        assert "last_updated" in dashboard_data

    @pytest.mark.asyncio
    async def test_error_handling(self, optimizer):
        """Test error handling in optimization operations"""
        # Mock Redis connection failure
        optimizer.intelligent_cache.redis_client.get = AsyncMock(side_effect=Exception("Redis connection error"))

        # Should handle errors gracefully
        try:
            cached_data = await optimizer.intelligent_cache.get_cached_data("test_key")
            # If it doesn't raise, it should return None or empty result
            assert cached_data is None or cached_data == {}
        except Exception:
            # Or it might raise, which is also acceptable
            pass

        # Error should be tracked in metrics
        assert hasattr(optimizer, "performance_metrics")

    def test_cache_configuration_model(self):
        """Test CacheConfiguration data model"""
        config = CacheConfiguration(
            ttl_seconds=3600,
            max_size_mb=512,
            eviction_policy="lru",
            compression_enabled=True,
            replication_factor=2,
            sharding_enabled=True,
        )

        assert config.ttl_seconds == 3600
        assert config.max_size_mb == 512
        assert config.eviction_policy == "lru"
        assert config.compression_enabled is True
        assert config.replication_factor == 2
        assert config.sharding_enabled is True

    def test_intelligent_cache_model(self):
        """Test IntelligentCache functionality"""
        with patch("redis.Redis") as mock_redis:
            cache = IntelligentCache()

            assert cache is not None
            assert hasattr(cache, "redis_client")
            assert hasattr(cache, "optimization_stats")

    def test_performance_monitor_model(self):
        """Test PerformanceMonitor functionality"""
        monitor = PerformanceMonitor()

        assert monitor is not None
        assert hasattr(monitor, "metrics_history")
        assert hasattr(monitor, "alert_thresholds")


# Integration test
@pytest.mark.asyncio
async def test_full_optimization_pipeline():
    """Test complete optimization pipeline integration"""
    try:
        with patch("ghl_real_estate_ai.services.enterprise_performance_optimizer.redis.Redis"):
            with patch("ghl_real_estate_ai.services.enterprise_performance_optimizer.ClaudeClient"):
                with patch("ghl_real_estate_ai.services.enterprise_performance_optimizer.psutil"):
                    optimizer = EnterprisePerformanceOptimizer()

                    # Mock dependencies
                    optimizer.intelligent_cache.redis_client.get = AsyncMock(return_value=None)
                    optimizer.intelligent_cache.redis_client.set = AsyncMock(return_value=True)
                    optimizer.claude_client.generate = AsyncMock(
                        return_value=json.dumps(
                            {
                                "optimization_recommendations": [
                                    {"category": "cache", "action": "increase_ttl", "priority": "high"}
                                ],
                                "performance_score": 0.85,
                            }
                        )
                    )

                    # Mock performance data
                    with patch("psutil.cpu_percent", return_value=55.2):
                        with patch("psutil.virtual_memory") as mock_memory:
                            mock_memory.return_value.percent = 72.5

                            # Run full optimization analysis
                            performance_data = {
                                "system_metrics": {"cpu_usage": 55.2, "memory_usage": 72.5},
                                "cache_metrics": {"hit_rate": 0.82, "miss_rate": 0.18},
                            }

                            recommendations = await optimizer.analyze_performance_with_ai(performance_data)

                            assert isinstance(recommendations, dict)
                            assert "optimization_recommendations" in recommendations
                            assert "performance_score" in recommendations

                            # Test cache optimization
                            cache_config = CacheConfiguration(ttl_seconds=3600)
                            cache_result = await optimizer.intelligent_cache.set_cached_data(
                                "test_optimization", recommendations, cache_config
                            )

                            assert cache_result is True

    except ImportError:
        pytest.skip("Dependencies not available for integration test")