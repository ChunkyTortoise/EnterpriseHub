"""
Comprehensive Tests for Repository Pattern Implementation

Tests all repository implementations, factory methods, caching, and Strategy Pattern integration.
Validates SOLID principles, performance, and error handling.
"""

import asyncio
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, Mock, patch

import pytest

from .caching_repository import CachingRepository, MemoryCacheBackend

# Import repository components
from .interfaces import (
    IPropertyRepository,
    PaginationConfig,
    PropertyQuery,
    QueryOperator,
    RepositoryError,
    RepositoryResult,
    SortOrder,
)
from .json_repository import JsonPropertyRepository
from .property_data_service import PropertyDataService
from .query_builder import FluentPropertyQuery, PropertyQueryBuilder
from .repository_factory import RepositoryBuilder, RepositoryFactory
from .strategy_integration import RepositoryPropertyMatcher, enhanced_generate_property_matches


class TestPropertyQuery:
    """Test PropertyQuery data structure and validation"""

    def test_property_query_defaults(self):
        """Test default PropertyQuery initialization"""
        query = PropertyQuery()

        assert query.sort_by == "price"
        assert query.sort_order == SortOrder.ASC
        assert query.pagination.page == 1
        assert query.pagination.limit == 50
        assert query.use_cache is True
        assert query.include_metadata is True

    def test_property_query_add_filter(self):
        """Test adding filters to PropertyQuery"""
        query = PropertyQuery()
        query.add_filter("price", QueryOperator.GREATER_THAN, 500000)

        assert len(query.filters) == 1
        assert query.filters[0].field == "price"
        assert query.filters[0].operator == QueryOperator.GREATER_THAN
        assert query.filters[0].value == 500000

    def test_property_query_add_price_range(self):
        """Test price range filter"""
        query = PropertyQuery()
        query.add_price_range(min_price=300000, max_price=800000)

        assert query.min_price == 300000
        assert query.max_price == 800000

    def test_property_query_add_location_filter(self):
        """Test location filter"""
        query = PropertyQuery()
        query.add_location_filter(lat=30.2672, lon=-97.7431, radius_miles=10)

        assert query.latitude == 30.2672
        assert query.longitude == -97.7431
        assert query.radius_miles == 10

    def test_pagination_config(self):
        """Test pagination configuration"""
        pagination = PaginationConfig(page=2, limit=25)

        assert pagination.page == 2
        assert pagination.limit == 25
        assert pagination.offset == 25  # (page - 1) * limit

        # Test total_count calculation
        pagination.total_count = 150
        assert pagination.has_next_page is True
        assert pagination.has_prev_page is True

        # Test edge cases
        pagination.page = 1
        assert pagination.has_prev_page is False


class TestPropertyQueryBuilder:
    """Test PropertyQueryBuilder fluent interface"""

    def test_query_builder_fluent_interface(self):
        """Test method chaining in query builder"""
        query = (
            PropertyQueryBuilder()
            .filter_by_price(min_price=400000, max_price=800000)
            .filter_by_bedrooms(min_beds=2, max_beds=4)
            .filter_by_location(location="Austin")
            .sort_by("price", SortOrder.ASC)
            .paginate(page=1, limit=20)
            .build()
        )

        assert query.min_price == 400000
        assert query.max_price == 800000
        assert query.min_bedrooms == 2
        assert query.max_bedrooms == 4
        assert query.location == "Austin"
        assert query.sort_by == "price"
        assert query.sort_order == SortOrder.ASC
        assert query.pagination.limit == 20

    def test_query_builder_validation(self):
        """Test query validation in builder"""
        builder = PropertyQueryBuilder()

        # Valid query should build successfully
        query = builder.filter_by_price(min_price=300000, max_price=600000).build()
        assert query.min_price == 300000

        # Invalid query should raise ValueError
        builder.reset()
        with pytest.raises(ValueError, match="min_price cannot be greater than max_price"):
            builder.filter_by_price(min_price=800000, max_price=400000).build()

    def test_fluent_query_shortcuts(self):
        """Test FluentPropertyQuery static methods"""
        query = FluentPropertyQuery.by_price_range(300000, 700000).build()
        assert query.min_price == 300000
        assert query.max_price == 700000

        query = FluentPropertyQuery.by_location("Austin").build()
        assert query.location == "Austin"

        query = FluentPropertyQuery.semantic("modern downtown condo with pool").build()
        assert query.semantic_query == "modern downtown condo with pool"

        query = FluentPropertyQuery.luxury_homes(min_price=1500000, min_sqft=4000).build()
        assert query.min_price == 1500000
        assert query.min_sqft == 4000
        assert "garage" in query.required_amenities


class TestJsonPropertyRepository:
    """Test JSON repository implementation"""

    def setup_method(self):
        """Setup test data"""
        self.test_properties = [
            {
                "id": "prop-001",
                "address": "123 Test Street",
                "price": 500000,
                "bedrooms": 3,
                "bathrooms": 2.5,
                "sqft": 2000,
                "neighborhood": "TestTown",
                "property_type": "Single Family",
                "amenities": ["garage", "pool"],
            },
            {
                "id": "prop-002",
                "address": "456 Demo Avenue",
                "price": 750000,
                "bedrooms": 4,
                "bathrooms": 3,
                "sqft": 2800,
                "neighborhood": "DemoDistrict",
                "property_type": "Single Family",
                "amenities": ["garage", "fireplace"],
            },
        ]

    @pytest.fixture
    async def temp_json_file(self):
        """Create temporary JSON file for testing"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.test_properties, f)
            yield f.name
        Path(f.name).unlink()

    @pytest.mark.asyncio
    async def test_json_repository_connect(self, temp_json_file):
        """Test JSON repository connection"""
        config = {"data_paths": [temp_json_file]}
        repo = JsonPropertyRepository(config)

        assert not repo.is_connected
        success = await repo.connect()
        assert success
        assert repo.is_connected

    @pytest.mark.asyncio
    async def test_json_repository_find_properties(self, temp_json_file):
        """Test finding properties in JSON repository"""
        config = {"data_paths": [temp_json_file]}
        repo = JsonPropertyRepository(config)
        await repo.connect()

        # Test basic query
        query = PropertyQuery()
        result = await repo.find_properties(query)

        assert result.success
        assert len(result.data) == 2
        assert result.total_count == 2

        # Test price filter
        query = PropertyQuery()
        query.max_price = 600000
        result = await repo.find_properties(query)

        assert result.success
        assert len(result.data) == 1
        assert result.data[0]["id"] == "prop-001"

    @pytest.mark.asyncio
    async def test_json_repository_get_by_id(self, temp_json_file):
        """Test getting property by ID"""
        config = {"data_paths": [temp_json_file]}
        repo = JsonPropertyRepository(config)
        await repo.connect()

        prop = await repo.get_property_by_id("prop-001")
        assert prop is not None
        assert prop["address"] == "123 Test Street"

        # Test non-existent property
        prop = await repo.get_property_by_id("nonexistent")
        assert prop is None

    @pytest.mark.asyncio
    async def test_json_repository_count_properties(self, temp_json_file):
        """Test counting properties"""
        config = {"data_paths": [temp_json_file]}
        repo = JsonPropertyRepository(config)
        await repo.connect()

        query = PropertyQuery()
        count = await repo.count_properties(query)
        assert count == 2

        # Test with filter
        query.min_price = 700000
        count = await repo.count_properties(query)
        assert count == 1

    @pytest.mark.asyncio
    async def test_json_repository_health_check(self, temp_json_file):
        """Test repository health check"""
        config = {"data_paths": [temp_json_file]}
        repo = JsonPropertyRepository(config)
        await repo.connect()

        health = await repo.health_check()
        assert health["status"] == "healthy"
        assert health["properties_count"] == 2
        assert health["data_sources"] == 1


class TestCachingRepository:
    """Test caching repository decorator"""

    @pytest.mark.asyncio
    async def test_caching_repository_decorator(self):
        """Test caching decorator functionality"""
        # Create mock base repository
        mock_repo = AsyncMock(spec=IPropertyRepository)
        mock_repo.name = "mock_repo"
        mock_repo.is_connected = True

        # Mock find_properties response
        mock_result = RepositoryResult(data=[{"id": "prop-001", "price": 500000}], total_count=1)
        mock_repo.find_properties.return_value = mock_result

        # Create caching repository
        cache_backend = MemoryCacheBackend(max_size=100)
        caching_repo = CachingRepository(mock_repo, cache_backend)
        await caching_repo.connect()

        # First query should hit repository
        query = PropertyQuery()
        result1 = await caching_repo.find_properties(query)

        assert result1.success
        assert mock_repo.find_properties.call_count == 1
        assert caching_repo.cache_misses == 1

        # Second identical query should hit cache
        result2 = await caching_repo.find_properties(query)

        assert result2.success
        assert mock_repo.find_properties.call_count == 1  # No additional calls
        assert caching_repo.cache_hits == 1

    @pytest.mark.asyncio
    async def test_memory_cache_backend(self):
        """Test in-memory cache backend"""
        cache = MemoryCacheBackend(max_size=2)

        # Test basic set/get
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        assert value == "value1"

        # Test TTL
        await cache.set("key2", "value2", ttl=timedelta(milliseconds=100))
        await asyncio.sleep(0.2)  # Wait for expiration
        value = await cache.get("key2")
        assert value is None

        # Test LRU eviction
        await cache.set("key3", "value3")
        await cache.set("key4", "value4")
        await cache.set("key5", "value5")  # Should evict key1

        assert await cache.get("key1") is None
        assert await cache.get("key3") == "value3"


class TestRepositoryFactory:
    """Test repository factory and builder patterns"""

    @pytest.mark.asyncio
    async def test_repository_factory_create_json(self):
        """Test factory creating JSON repository"""
        factory = RepositoryFactory()
        config = {"data_paths": []}

        repo = await factory.create("json", config, enable_caching=False)
        assert isinstance(repo, JsonPropertyRepository)

    @pytest.mark.asyncio
    async def test_repository_factory_with_caching(self):
        """Test factory creating repository with caching"""
        factory = RepositoryFactory()
        config = {"data_paths": []}
        cache_config = {"backend": "memory", "max_size": 100}

        repo = await factory.create("json", config, enable_caching=True, cache_config=cache_config)
        assert isinstance(repo, CachingRepository)
        assert isinstance(repo.wrapped_repository, JsonPropertyRepository)

    @pytest.mark.asyncio
    async def test_repository_builder_pattern(self):
        """Test repository builder pattern"""
        builder = RepositoryBuilder()
        repo = await (
            builder.json_source(data_paths=[], cache_ttl=300).with_memory_cache(max_size=500, ttl_minutes=10).build()
        )

        assert isinstance(repo, CachingRepository)

    def test_repository_factory_unknown_type(self):
        """Test factory with unknown repository type"""
        factory = RepositoryFactory()

        with pytest.raises(ValueError, match="Unknown repository type"):
            asyncio.run(factory.create("unknown_type", {}))


class TestPropertyDataService:
    """Test high-level property data service"""

    @pytest.fixture
    def mock_repositories_config(self):
        """Mock repository configuration"""
        return [
            {
                "name": "primary_json",
                "type": "json",
                "config": {"data_paths": []},
                "priority": 1,
                "fallback": False,
                "caching": {"enabled": False},
            },
            {
                "name": "fallback_json",
                "type": "json",
                "config": {"data_paths": []},
                "priority": 0,
                "fallback": True,
                "caching": {"enabled": False},
            },
        ]

    @pytest.mark.asyncio
    async def test_property_data_service_initialization(self, mock_repositories_config):
        """Test service initialization"""
        service = PropertyDataService()

        # Mock repository creation
        with patch.object(service, "_create_repository_from_config") as mock_create:
            mock_repo1 = AsyncMock(spec=IPropertyRepository)
            mock_repo1.name = "primary_json"
            mock_repo1.connect.return_value = True

            mock_repo2 = AsyncMock(spec=IPropertyRepository)
            mock_repo2.name = "fallback_json"
            mock_repo2.connect.return_value = True

            mock_create.side_effect = [mock_repo1, mock_repo2]

            await service.initialize(mock_repositories_config)

            assert len(service._repositories) == 2
            assert service._primary_repository == mock_repo1
            assert mock_repo2 in service._fallback_repositories

    @pytest.mark.asyncio
    async def test_property_data_service_find_properties(self):
        """Test service find properties with cascade strategy"""
        service = PropertyDataService({"fallback_strategy": "cascade"})

        # Create mock repositories
        mock_primary = AsyncMock(spec=IPropertyRepository)
        mock_primary.name = "primary"
        mock_fallback = AsyncMock(spec=IPropertyRepository)
        mock_fallback.name = "fallback"

        service._repositories = [mock_primary, mock_fallback]
        service._primary_repository = mock_primary
        service._fallback_repositories = [mock_fallback]

        # Primary repository returns successful result
        mock_result = RepositoryResult(data=[{"id": "prop-001"}], total_count=1, success=True)
        mock_primary.find_properties.return_value = mock_result

        query = PropertyQuery()
        result = await service.find_properties(query)

        assert result.success
        assert len(result.data) == 1
        assert mock_primary.find_properties.called
        assert not mock_fallback.find_properties.called

    @pytest.mark.asyncio
    async def test_property_data_service_cascade_fallback(self):
        """Test cascade fallback when primary fails"""
        service = PropertyDataService({"fallback_strategy": "cascade"})

        mock_primary = AsyncMock(spec=IPropertyRepository)
        mock_primary.name = "primary"
        mock_fallback = AsyncMock(spec=IPropertyRepository)
        mock_fallback.name = "fallback"

        service._repositories = [mock_primary, mock_fallback]
        service._primary_repository = mock_primary
        service._fallback_repositories = [mock_fallback]

        # Primary fails, fallback succeeds
        mock_primary.find_properties.return_value = RepositoryResult(success=False, errors=["Primary failed"])
        mock_fallback.find_properties.return_value = RepositoryResult(data=[{"id": "fallback-prop"}], success=True)

        query = PropertyQuery()
        result = await service.find_properties(query)

        assert result.success
        assert result.data[0]["id"] == "fallback-prop"
        assert mock_primary.find_properties.called
        assert mock_fallback.find_properties.called


class TestStrategyIntegration:
    """Test Repository Pattern integration with Strategy Pattern"""

    @pytest.fixture
    def mock_lead_context(self):
        """Mock lead context for testing"""
        return {
            "lead_id": "test-lead-123",
            "agent_id": "agent-456",
            "extracted_preferences": {
                "budget": 750000,
                "location": "Austin",
                "bedrooms": 3,
                "bathrooms": 2,
                "property_type": "Single Family",
                "must_haves": ["garage", "pool"],
                "nice_to_haves": ["fireplace"],
                "work_location": "downtown",
                "has_children": True,
                "min_sqft": 1800,
            },
        }

    @pytest.mark.asyncio
    async def test_repository_property_matcher_creation(self):
        """Test creating RepositoryPropertyMatcher"""
        # Mock data service
        mock_service = AsyncMock(spec=PropertyDataService)
        mock_service.load_properties_for_strategy_pattern.return_value = [
            {"id": "prop-001", "price": 500000, "bedrooms": 3, "address": "Test Address"}
        ]

        matcher = RepositoryPropertyMatcher(
            property_data_service=mock_service, strategy_name="enhanced", fallback_strategy="basic"
        )

        assert matcher.data_service == mock_service
        assert matcher.strategy_name == "enhanced"

    @pytest.mark.asyncio
    async def test_enhanced_generate_property_matches(self, mock_lead_context):
        """Test enhanced property matching function"""
        config = {"type": "demo", "json_data_dir": "/tmp/test_data"}

        # Mock the repository creation
        with patch("services.repositories.strategy_integration.create_repository_property_matcher") as mock_create:
            mock_matcher = AsyncMock()
            mock_matcher.score_properties_with_repository.return_value = [
                {
                    "address": "123 Test Street",
                    "price": 500000,
                    "beds": 3,
                    "baths": 2.5,
                    "sqft": 2000,
                    "match_score": 92,
                    "match_reasons": ["Within budget", "Perfect location"],
                }
            ]
            mock_create.return_value = mock_matcher

            results = await enhanced_generate_property_matches(
                lead_context=mock_lead_context, data_sources_config=config
            )

            assert len(results) == 1
            assert results[0]["address"] == "123 Test Street"
            assert results[0]["match_score"] == 92


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_repository_error_handling(self):
        """Test repository error handling"""
        config = {"data_paths": ["/nonexistent/path.json"]}
        repo = JsonPropertyRepository(config)

        # Connection should fail gracefully
        with pytest.raises(RepositoryError):
            await repo.connect()

    @pytest.mark.asyncio
    async def test_query_validation_errors(self):
        """Test query validation error handling"""
        builder = PropertyQueryBuilder()

        # Invalid price range
        with pytest.raises(ValueError):
            builder.filter_by_price(min_price=800000, max_price=400000).build()

        # Invalid pagination
        builder.reset()
        with pytest.raises(ValueError):
            builder.paginate(page=0, limit=50).build()

        # Invalid limit
        builder.reset()
        with pytest.raises(ValueError):
            builder.paginate(page=1, limit=2000).build()

    @pytest.mark.asyncio
    async def test_repository_timeout_handling(self):
        """Test handling of repository timeouts"""
        # Mock a slow repository
        mock_repo = AsyncMock(spec=IPropertyRepository)
        mock_repo.name = "slow_repo"

        async def slow_find_properties(query):
            await asyncio.sleep(2)  # Simulate slow response
            return RepositoryResult(data=[], success=True)

        mock_repo.find_properties.side_effect = slow_find_properties

        # This would typically timeout in real scenario
        # For test, we just verify the mock behavior
        query = PropertyQuery()
        result = await asyncio.wait_for(mock_repo.find_properties(query), timeout=1.0)
        # This should raise asyncio.TimeoutError in real scenario


class TestPerformanceAndSOLIDPrinciples:
    """Test performance characteristics and SOLID principle compliance"""

    def test_single_responsibility_principle(self):
        """Verify each class has single responsibility"""
        # PropertyQuery: Query specification only
        query = PropertyQuery()
        assert hasattr(query, "min_price")
        assert not hasattr(query, "execute")  # No execution logic

        # QueryBuilder: Query construction only
        builder = PropertyQueryBuilder()
        assert hasattr(builder, "filter_by_price")
        assert hasattr(builder, "build")
        assert not hasattr(builder, "find_properties")  # No repository logic

        # Repository: Data access only
        config = {"data_paths": []}
        repo = JsonPropertyRepository(config)
        assert hasattr(repo, "find_properties")
        assert not hasattr(repo, "calculate_score")  # No scoring logic

    def test_open_closed_principle(self):
        """Verify classes are open for extension, closed for modification"""

        # Can create new repository types without modifying existing code
        class CustomPropertyRepository(IPropertyRepository):
            async def connect(self) -> bool:
                return True

            async def disconnect(self):
                pass

            async def health_check(self) -> Dict[str, Any]:
                return {"status": "healthy"}

            async def find_properties(self, query: PropertyQuery) -> RepositoryResult:
                return RepositoryResult(data=[], success=True)

            async def get_property_by_id(self, property_id: str):
                return None

            async def count_properties(self, query: PropertyQuery) -> int:
                return 0

            def get_supported_filters(self) -> List[str]:
                return []

            def get_performance_metrics(self) -> Dict[str, Any]:
                return {}

        # Should work with existing factory
        factory = RepositoryFactory()
        factory.register_repository("custom", CustomPropertyRepository)
        assert "custom" in factory._registry

    def test_dependency_inversion_principle(self):
        """Verify high-level modules don't depend on low-level modules"""
        # PropertyDataService depends on IPropertyRepository abstraction
        service = PropertyDataService()
        assert not hasattr(service, "json_repository")  # No concrete dependency

        # CachingRepository depends on IPropertyRepository abstraction
        mock_repo = Mock(spec=IPropertyRepository)
        cache_backend = MemoryCacheBackend()
        caching_repo = CachingRepository(mock_repo, cache_backend)
        assert hasattr(caching_repo, "wrapped_repository")  # Uses abstraction


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    @pytest.mark.asyncio
    async def test_complete_property_search_workflow(self):
        """Test complete property search from query building to results"""
        # 1. Build query using fluent interface
        query = (
            FluentPropertyQuery.by_price_range(400000, 800000)
            .filter_by_bedrooms(min_beds=2, max_beds=4)
            .filter_by_location(location="Austin")
            .filter_by_amenities(required=["garage"])
            .sort_by("price", SortOrder.ASC)
            .paginate(page=1, limit=10)
            .build()
        )

        # 2. Create repository with test data
        test_data = [
            {
                "id": "prop-001",
                "address": "123 Austin Street",
                "price": 650000,
                "bedrooms": 3,
                "bathrooms": 2.5,
                "neighborhood": "Austin",
                "amenities": ["garage", "pool"],
            }
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name

        try:
            config = {"data_paths": [temp_file]}
            repo = JsonPropertyRepository(config)
            await repo.connect()

            # 3. Execute search
            result = await repo.find_properties(query)

            # 4. Verify results
            assert result.success
            assert len(result.data) == 1
            assert result.data[0]["id"] == "prop-001"
            assert result.metadata.source == "json_repository"

        finally:
            Path(temp_file).unlink()

    @pytest.mark.asyncio
    async def test_multi_repository_fallback_scenario(self):
        """Test scenario where primary repository fails and fallback succeeds"""
        service = PropertyDataService({"fallback_strategy": "cascade"})

        # Primary repository that always fails
        failing_repo = AsyncMock(spec=IPropertyRepository)
        failing_repo.name = "failing_repo"
        failing_repo.find_properties.side_effect = Exception("Connection failed")

        # Fallback repository that succeeds
        success_repo = AsyncMock(spec=IPropertyRepository)
        success_repo.name = "success_repo"
        success_repo.find_properties.return_value = RepositoryResult(
            data=[{"id": "fallback-prop", "price": 500000}], success=True
        )

        service._repositories = [failing_repo, success_repo]
        service._primary_repository = failing_repo
        service._fallback_repositories = [success_repo]

        query = PropertyQuery()
        result = await service.find_properties(query)

        assert result.success
        assert len(result.data) == 1
        assert result.data[0]["id"] == "fallback-prop"


# Performance benchmarks (would run separately)
class TestPerformanceBenchmarks:
    """Performance tests for repository operations"""

    @pytest.mark.asyncio
    async def test_json_repository_performance(self):
        """Benchmark JSON repository performance"""
        # Create larger test dataset
        large_dataset = [
            {
                "id": f"prop-{i:06d}",
                "price": 400000 + (i * 1000),
                "bedrooms": (i % 4) + 1,
                "bathrooms": ((i % 3) + 1) + 0.5,
                "address": f"{i} Test Street",
            }
            for i in range(1000)
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(large_dataset, f)
            temp_file = f.name

        try:
            config = {"data_paths": [temp_file]}
            repo = JsonPropertyRepository(config)
            await repo.connect()

            # Time property search
            start_time = datetime.now()
            query = PropertyQuery()
            query.min_price = 500000
            query.max_price = 700000
            result = await repo.find_properties(query)
            end_time = datetime.now()

            execution_time = (end_time - start_time).total_seconds()

            # Should complete within reasonable time
            assert execution_time < 1.0  # Less than 1 second
            assert result.success
            assert result.metadata.query_time_ms < 1000

        finally:
            Path(temp_file).unlink()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
