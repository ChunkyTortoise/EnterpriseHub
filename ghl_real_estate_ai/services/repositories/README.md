# Repository Pattern Implementation for GHL Real Estate AI

## Overview

This repository pattern implementation provides a flexible, enterprise-grade data access layer for property data. It integrates seamlessly with the existing Strategy Pattern to provide a complete property matching solution.

## Architecture

```
Repository Pattern Architecture:
├── Core Interfaces
│   ├── IPropertyRepository (Abstract Base)
│   ├── PropertyQuery (Query Specification)
│   └── RepositoryResult (Result Container)
├── Concrete Repositories
│   ├── JsonPropertyRepository (JSON files)
│   ├── MLSAPIRepository (MLS APIs)
│   ├── RAGPropertyRepository (Semantic search)
│   └── DatabasePropertyRepository (SQL databases)
├── Query & Caching Layer
│   ├── PropertyQueryBuilder (Fluent interface)
│   ├── CachingRepository (Decorator)
│   └── RepositoryFactory (Creation)
└── Integration Layer
    ├── PropertyDataService (High-level service)
    └── StrategyIntegration (Strategy Pattern bridge)
```

## Quick Start

### 1. Basic Usage with JSON Data

```python
from repositories import json_repository
from repositories.query_builder import FluentPropertyQuery

# Create repository for JSON data
repo = await (json_repository(["/path/to/properties.json"])
              .with_memory_cache(max_size=1000, ttl_minutes=15)
              .build())

# Build and execute query
query = (FluentPropertyQuery
         .by_price_range(400000, 800000)
         .filter_by_bedrooms(min_beds=2, max_beds=4)
         .filter_by_location(location="Rancho Cucamonga")
         .sort_by("price")
         .paginate(limit=20)
         .build())

result = await repo.find_properties(query)
print(f"Found {len(result.data)} properties")
```

### 2. Integration with Strategy Pattern

```python
from repositories.strategy_integration import enhanced_generate_property_matches

# Enhanced property matching with Repository Pattern
lead_context = {
    'extracted_preferences': {
        'budget': 750000,
        'location': 'Rancho Cucamonga',
        'bedrooms': 3,
        'property_type': 'Single Family',
        'must_haves': ['garage']
    }
}

# Configuration for data sources
data_config = {
    "type": "demo",
    "json_data_dir": "/path/to/data/knowledge_base"
}

# Get scored properties using Repository + Strategy Pattern
properties = await enhanced_generate_property_matches(
    lead_context=lead_context,
    data_sources_config=data_config
)

for prop in properties:
    print(f"{prop['address']}: {prop['match_score']}% match")
```

### 3. Production Configuration with Multiple Sources

```python
from repositories import PropertyDataServiceFactory

# Production service with MLS primary + JSON fallback
mls_config = {
    "api_base_url": "https://api.mls-provider.com",
    "api_key": "your-api-key",
    "provider": "trestle",
    "rate_limit": 10
}

service = await PropertyDataServiceFactory.create_production_service(
    mls_config=mls_config,
    json_fallback_paths=["/path/to/fallback/data.json"]
)

# Execute query with intelligent source selection
query = PropertyQueryBuilder().semantic_search("luxury downtown condo with pool").build()
result = await service.find_properties(query)
```

## Detailed Usage Guide

### Query Building

#### Fluent Interface
```python
from repositories.query_builder import PropertyQueryBuilder, FluentPropertyQuery, Q

# Method 1: Explicit builder
query = (PropertyQueryBuilder()
         .filter_by_price(min_price=300000, max_price=800000)
         .filter_by_bedrooms(min_beds=2, max_beds=4)
         .filter_by_location(location="Rancho Cucamonga")
         .filter_by_amenities(required=["garage"], preferred=["pool"])
         .semantic_search("modern downtown condo")
         .sort_by("price", SortOrder.ASC)
         .paginate(page=1, limit=25)
         .include_images(True)
         .cache_control(use_cache=True, cache_ttl_seconds=300)
         .build())

# Method 2: Shortcut methods
query = Q.luxury_homes(min_price=1000000, min_sqft=3000).build()
query = Q.starter_homes(max_price=400000).build()
query = Q.family_homes(min_bedrooms=3).build()

# Method 3: Geographic search
query = Q.near_coordinates(lat=30.2672, lon=-97.7431, radius_miles=10).build()
```

#### Custom Filters
```python
from repositories.interfaces import QueryOperator

query = (PropertyQueryBuilder()
         .add_custom_filter("days_on_market", QueryOperator.LESS_THAN, 30)
         .add_custom_filter("year_built", QueryOperator.GREATER_THAN, 2010)
         .add_custom_filter("property_type", QueryOperator.IN, ["Single Family", "Townhome"])
         .build())
```

### Repository Types

#### JSON Repository
```python
from repositories import JsonPropertyRepository

config = {
    "data_paths": [
        "/data/properties.json",
        "/data/additional_listings.json"
    ],
    "cache_ttl": 300,  # 5 minutes
    "auto_refresh": True,
    "normalize_data": True
}

repo = JsonPropertyRepository(config)
await repo.connect()
```

#### MLS API Repository
```python
from repositories import MLSAPIRepository

config = {
    "api_base_url": "https://api.trestle.com",
    "api_key": "your-trestle-api-key",
    "provider": "trestle",
    "rate_limit": 10,  # requests/second
    "timeout": 30,
    "retry_attempts": 3,
    "cache_ttl": 1800  # 30 minutes
}

repo = MLSAPIRepository(config)
await repo.connect()

# Health check
health = await repo.health_check()
print(f"MLS Status: {health['status']}")
```

#### RAG/Semantic Search Repository
```python
from repositories import RAGPropertyRepository

config = {
    "data_paths": ["/data/properties.json"],
    "embedding_model": "all-MiniLM-L6-v2",
    "openai_api_key": "sk-...",  # Optional: use OpenAI embeddings
    "similarity_threshold": 0.6,
    "vector_index_path": "./embeddings/",
    "max_semantic_results": 100
}

repo = RAGPropertyRepository(config)
await repo.connect()

# Semantic search
query = PropertyQueryBuilder().semantic_search(
    "modern downtown condo with amenities",
    similarity_threshold=0.7
).build()

result = await repo.find_properties(query)
```

#### Database Repository
```python
from repositories import DatabasePropertyRepository

# PostgreSQL
config = {
    "database_url": "postgresql://user:pass@localhost/properties",
    "database_type": "postgresql",
    "table_name": "properties",
    "pool_size": 10
}

# MySQL
config = {
    "database_url": "mysql://user:pass@localhost/properties",
    "database_type": "mysql",
    "table_name": "property_listings"
}

# SQLite
config = {
    "database_url": "sqlite:///./properties.db",
    "database_type": "sqlite"
}

repo = DatabasePropertyRepository(config)
await repo.connect()

# Optionally create table with schema
await repo.create_table()
```

### Caching Strategies

#### Memory Cache
```python
from repositories.caching_repository import MemoryCacheBackend, CachingRepository

cache_backend = MemoryCacheBackend(max_size=1000)
cached_repo = CachingRepository(base_repo, cache_backend)

# Cache statistics
metrics = await cached_repo.get_performance_metrics()
print(f"Cache hit rate: {metrics['cache_metrics']['cache_hit_rate']:.2f}%")
```

#### Redis Cache
```python
from repositories.caching_repository import RedisCacheBackend

cache_backend = RedisCacheBackend(
    redis_url="redis://localhost:6379",
    key_prefix="prop_cache:"
)

cached_repo = CachingRepository(base_repo, cache_backend)
await cached_repo.connect()

# Cache management
await cached_repo.invalidate_cache()  # Clear all cache
```

### High-Level Data Service

#### Service Configuration
```python
from repositories import PropertyDataService

config = {
    "fallback_strategy": "cascade",  # or "parallel"
    "performance_monitoring": True,
    "max_concurrent_repos": 3
}

service = PropertyDataService(config)

repositories_config = [
    {
        "name": "primary_mls",
        "type": "mls",
        "config": {...},
        "priority": 1,
        "fallback": False,
        "caching": {
            "enabled": True,
            "backend": "redis",
            "ttl": 1800
        }
    },
    {
        "name": "fallback_json",
        "type": "json",
        "config": {...},
        "priority": 0,
        "fallback": True,
        "caching": {
            "enabled": True,
            "backend": "memory",
            "max_size": 1000
        }
    }
]

await service.initialize(repositories_config)
```

#### Service Usage
```python
# Smart repository selection
query = PropertyQueryBuilder().semantic_search("luxury waterfront").build()
result = await service.find_properties(query, prefer_repository="rag_semantic")

# Health monitoring
health = await service.health_check()
print(f"Service status: {health['status']}")
print(f"Issues: {health['issues']}")

# Performance metrics
metrics = await service.get_performance_metrics()
```

## Integration with Existing Strategy Pattern

### Drop-in Replacement

Replace the existing `_load_demo_properties()` function in `property_matcher_ai.py`:

```python
# OLD: Manual property loading
def _load_demo_properties() -> List[Dict]:
    return [
        {"id": "prop-001", "price": 750000, ...},
        # ... hardcoded properties
    ]

# NEW: Repository-based loading
from repositories.strategy_integration import enhanced_generate_property_matches

async def generate_property_matches(lead_context: Dict) -> List[Dict]:
    return await enhanced_generate_property_matches(
        lead_context=lead_context,
        data_sources_config={"type": "demo"}
    )
```

### Custom Integration

```python
from repositories import PropertyDataServiceFactory
from repositories.strategy_integration import RepositoryPropertyMatcher

# Create data service
service = await PropertyDataServiceFactory.create_demo_service(
    data_dir="./data/knowledge_base"
)

# Create integrated matcher
matcher = RepositoryPropertyMatcher(
    property_data_service=service,
    strategy_name="enhanced",
    fallback_strategy="basic"
)

# Use with existing Strategy Pattern
lead_preferences = {
    'budget': 750000,
    'location': 'Rancho Cucamonga',
    'bedrooms': 3,
    'must_haves': ['garage']
}

scored_properties = await matcher.score_properties_with_repository(
    lead_preferences=lead_preferences,
    max_properties=10
)
```

## Configuration Examples

### Development Configuration
```python
# repositories_config.py
DEVELOPMENT_CONFIG = {
    "type": "demo",
    "json_data_dir": "/Users/cave/enterprisehub/ghl_real_estate_ai/data/knowledge_base"
}
```

### Production Configuration
```python
PRODUCTION_CONFIG = {
    "type": "hybrid",
    "json_paths": ["/app/data/properties.json"],
    "mls_config": {
        "api_base_url": "https://api.trestle.com",
        "api_key": os.getenv("MLS_API_KEY"),
        "provider": "trestle",
        "rate_limit": 20,
        "market_area": "rancho_cucamonga"
    },
    "rag_config": {
        "data_paths": ["/app/data/properties.json"],
        "embedding_model": "all-MiniLM-L6-v2",
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "vector_index_path": "/app/embeddings/"
    }
}
```

### Environment-based Configuration
```python
import os
from repositories.repository_factory import create_from_environment

# Set environment variables
os.environ["PROPERTY_REPO_TYPE"] = "json"
os.environ["PROPERTY_REPO_CONFIG"] = json.dumps({
    "data_paths": ["/app/data/properties.json"]
})
os.environ["PROPERTY_CACHE_ENABLED"] = "true"
os.environ["PROPERTY_CACHE_BACKEND"] = "redis"

# Create repository from environment
repo = create_from_environment()
```

## Performance Optimization

### Query Optimization
```python
# Use specific filters to reduce data scan
query = (PropertyQueryBuilder()
         .filter_by_price(min_price=400000, max_price=800000)  # Reduces scan
         .filter_by_location(location="Rancho Cucamonga")  # Index-friendly
         .paginate(limit=25)  # Limit results
         .build())

# Enable caching for repeated queries
query = (PropertyQueryBuilder()
         .filter_by_bedrooms(min_beds=3)
         .cache_control(use_cache=True, cache_ttl_seconds=600)  # 10 minute cache
         .build())
```

### Repository Selection
```python
# Use appropriate repository for query type
service = PropertyDataService()

# Semantic queries -> RAG repository
result = await service.find_properties(
    query=PropertyQueryBuilder().semantic_search("waterfront property").build(),
    prefer_repository="rag_semantic"
)

# Real-time queries -> MLS repository
result = await service.find_properties(
    query=PropertyQueryBuilder().filter_by_days_on_market(max_days=7).build(),
    prefer_repository="mls_api"
)

# Historical queries -> JSON repository
result = await service.find_properties(
    query=PropertyQueryBuilder().filter_by_year_built(min_year=1990, max_year=2000).build(),
    prefer_repository="json_data"
)
```

### Parallel Processing
```python
# Configure parallel repository access
config = {
    "fallback_strategy": "parallel",  # Query multiple repos simultaneously
    "max_concurrent_repos": 3
}

service = PropertyDataService(config)
```

## Error Handling

### Repository Errors
```python
from repositories.interfaces import RepositoryError

try:
    result = await repo.find_properties(query)
    if not result.success:
        print(f"Query failed: {result.errors}")
except RepositoryError as e:
    print(f"Repository error: {e}")
    print(f"Repository type: {e.repository_type}")
```

### Service-Level Error Handling
```python
# Service handles repository failures automatically
result = await service.find_properties(query)

if result.success:
    print(f"Found {len(result.data)} properties")
else:
    print(f"All repositories failed: {result.errors}")
    # Service logs which repositories failed
```

### Graceful Degradation
```python
# Configure fallback repositories
repositories_config = [
    {"name": "primary", "type": "mls", "priority": 1},
    {"name": "secondary", "type": "json", "priority": 0, "fallback": True}
]

# If MLS fails, automatically falls back to JSON
await service.initialize(repositories_config)
```

## Monitoring and Metrics

### Performance Monitoring
```python
# Repository-level metrics
metrics = repo.get_performance_metrics()
print(f"Query time: {metrics.get('average_query_time', 0):.2f}ms")

# Service-level metrics
service_metrics = await service.get_performance_metrics()
print(f"Success rate: {service_metrics['service_stats']['successful_queries']/service_metrics['service_stats']['total_queries']*100:.2f}%")

# Cache performance
if isinstance(repo, CachingRepository):
    cache_metrics = repo.get_performance_metrics()['cache_metrics']
    print(f"Cache hit rate: {cache_metrics['cache_hit_rate']:.2f}%")
```

### Health Monitoring
```python
# Individual repository health
health = await repo.health_check()
print(f"Repository {repo.name}: {health['status']}")

# Service health (all repositories)
service_health = await service.health_check()
for repo_health in service_health['repositories']:
    print(f"{repo_health['name']}: {repo_health['status']}")
```

## Testing

### Unit Testing
```python
import pytest
from repositories.test_repository_pattern import *

# Run specific test
pytest.main(["test_repository_pattern.py::TestJsonPropertyRepository", "-v"])

# Run all tests
pytest.main(["test_repository_pattern.py", "-v"])
```

### Integration Testing
```python
# Test with real data
@pytest.mark.integration
async def test_real_data_integration():
    service = await PropertyDataServiceFactory.create_demo_service()
    query = PropertyQueryBuilder().filter_by_location(location="Rancho Cucamonga").build()
    result = await service.find_properties(query)
    assert result.success
```

## SOLID Principles Compliance

1. **Single Responsibility**: Each class has one reason to change
   - `PropertyQuery`: Query specification only
   - `JsonPropertyRepository`: JSON data access only
   - `CachingRepository`: Caching behavior only

2. **Open/Closed**: Open for extension, closed for modification
   - New repository types can be added without changing existing code
   - New query operators can be added via the interface

3. **Liskov Substitution**: Derived classes are substitutable
   - All repository implementations can be used interchangeably
   - CachingRepository can wrap any IPropertyRepository

4. **Interface Segregation**: Clients depend only on needed interfaces
   - IPropertyRepository defines minimal necessary methods
   - Query building is separate from execution

5. **Dependency Inversion**: Depend on abstractions, not concretions
   - PropertyDataService depends on IPropertyRepository interface
   - Factory creates concrete implementations

## Next Steps

1. **Add New Data Sources**: Implement additional repository types
2. **Advanced Caching**: Add distributed caching with Redis clustering
3. **Query Optimization**: Add query planning and optimization
4. **Monitoring Integration**: Connect to APM tools like New Relic or Datadog
5. **Schema Evolution**: Add versioning for data schema changes

## Contributing

When adding new repository implementations:

1. Implement `IPropertyRepository` interface
2. Add comprehensive error handling
3. Include performance metrics
4. Write thorough tests
5. Update factory registration
6. Document configuration options

See `test_repository_pattern.py` for testing patterns and examples.