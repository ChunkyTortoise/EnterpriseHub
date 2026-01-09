"""
Property Data Service Integration Layer

High-level service that integrates Repository Pattern with Strategy Pattern.
Provides unified property data access with intelligent repository selection.
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from pathlib import Path

try:
    from .interfaces import (
        IPropertyRepository, PropertyQuery, RepositoryResult, RepositoryError,
        QueryOperator, SortOrder
    )
    from .query_builder import PropertyQueryBuilder, FluentPropertyQuery
    from .repository_factory import RepositoryFactory, ConfiguredFactories
    from .json_repository import JsonPropertyRepository
    from .mls_repository import MLSAPIRepository
    from .rag_repository import RAGPropertyRepository
except ImportError:
    from interfaces import (
        IPropertyRepository, PropertyQuery, RepositoryResult, RepositoryError,
        QueryOperator, SortOrder
    )
    from query_builder import PropertyQueryBuilder, FluentPropertyQuery
    from repository_factory import RepositoryFactory, ConfiguredFactories
    from json_repository import JsonPropertyRepository
    from mls_repository import MLSAPIRepository
    from rag_repository import RAGPropertyRepository


class PropertyDataService:
    """
    High-level property data service that provides:
    - Intelligent repository selection
    - Fallback mechanisms
    - Performance monitoring
    - Integration with Strategy Pattern
    - Unified query interface
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize property data service.

        Config options:
        - repositories: List of repository configurations
        - fallback_strategy: How to handle repository failures
        - performance_monitoring: Enable performance tracking
        - cache_enabled: Enable cross-repository caching
        """
        self.config = config or {}

        # Repository management
        self._repositories: List[IPropertyRepository] = []
        self._primary_repository: Optional[IPropertyRepository] = None
        self._fallback_repositories: List[IPropertyRepository] = []

        # Configuration
        self.fallback_strategy = self.config.get("fallback_strategy", "cascade")
        self.performance_monitoring = self.config.get("performance_monitoring", True)
        self.max_concurrent_repos = self.config.get("max_concurrent_repos", 3)

        # Performance tracking
        self.performance_stats = {
            "total_queries": 0,
            "successful_queries": 0,
            "failed_queries": 0,
            "repository_stats": {},
            "average_response_time": 0.0
        }

        # Factory for creating repositories
        self.factory = RepositoryFactory()

    async def initialize(self, repositories_config: List[Dict[str, Any]]):
        """
        Initialize repositories from configuration.

        Args:
            repositories_config: List of repository configurations
                [
                    {
                        "name": "primary_json",
                        "type": "json",
                        "config": {...},
                        "priority": 1,
                        "fallback": true
                    }
                ]
        """
        for repo_config in repositories_config:
            try:
                repo = await self._create_repository_from_config(repo_config)
                await repo.connect()

                self._repositories.append(repo)

                # Set primary repository (highest priority)
                priority = repo_config.get("priority", 0)
                if not self._primary_repository or priority > getattr(self._primary_repository, '_priority', 0):
                    self._primary_repository = repo
                    repo._priority = priority

                # Add to fallback list if configured
                if repo_config.get("fallback", False) and repo != self._primary_repository:
                    self._fallback_repositories.append(repo)

            except Exception as e:
                print(f"Failed to initialize repository {repo_config.get('name', 'unknown')}: {e}")

        if not self._repositories:
            raise RepositoryError("No repositories successfully initialized")

    async def find_properties(self, query: PropertyQuery,
                            prefer_repository: Optional[str] = None) -> RepositoryResult:
        """
        Find properties with intelligent repository selection.

        Args:
            query: Property query specification
            prefer_repository: Preferred repository name (optional)

        Returns:
            Combined results from selected repositories
        """
        start_time = datetime.now()
        self.performance_stats["total_queries"] += 1

        try:
            # Select repositories based on query type and preferences
            selected_repos = self._select_repositories(query, prefer_repository)

            if not selected_repos:
                return RepositoryResult(
                    success=False,
                    errors=["No suitable repositories available"]
                )

            # Execute query based on strategy
            if self.fallback_strategy == "parallel":
                result = await self._execute_parallel_query(selected_repos, query)
            elif self.fallback_strategy == "cascade":
                result = await self._execute_cascade_query(selected_repos, query)
            else:
                result = await self._execute_single_query(selected_repos[0], query)

            # Update performance statistics
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_performance_stats(result.success, execution_time)

            return result

        except Exception as e:
            self.performance_stats["failed_queries"] += 1
            return RepositoryResult(
                success=False,
                errors=[f"Property search failed: {str(e)}"]
            )

    async def get_property_by_id(self, property_id: str,
                               source_hint: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get specific property by ID with repository selection.

        Args:
            property_id: Property identifier
            source_hint: Hint about which repository might have the property

        Returns:
            Property data or None if not found
        """
        # Try hinted repository first
        if source_hint:
            for repo in self._repositories:
                if repo.name == source_hint:
                    try:
                        result = await repo.get_property_by_id(property_id)
                        if result:
                            return result
                    except Exception as e:
                        print(f"Failed to get property from {source_hint}: {e}")

        # Try all repositories
        for repo in [self._primary_repository] + self._fallback_repositories:
            if repo:
                try:
                    result = await repo.get_property_by_id(property_id)
                    if result:
                        return result
                except Exception as e:
                    print(f"Failed to get property from {repo.name}: {e}")

        return None

    async def count_properties(self, query: PropertyQuery) -> int:
        """Count properties across all repositories"""
        if self.fallback_strategy == "parallel":
            # Sum counts from all repositories
            tasks = [repo.count_properties(query) for repo in self._repositories]
            counts = await asyncio.gather(*tasks, return_exceptions=True)
            total = sum(count for count in counts if isinstance(count, int))
            return total
        else:
            # Use primary repository
            if self._primary_repository:
                return await self._primary_repository.count_properties(query)
            return 0

    def create_query(self) -> PropertyQueryBuilder:
        """Create new property query builder"""
        return PropertyQueryBuilder()

    def semantic_search(self, query_text: str,
                       similarity_threshold: float = 0.6) -> PropertyQueryBuilder:
        """Create semantic search query"""
        return FluentPropertyQuery.semantic(query_text).cache_control(use_cache=True)

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for all repositories"""
        service_health = {
            "status": "healthy",
            "repositories": [],
            "performance": self.performance_stats.copy(),
            "issues": []
        }

        # Check each repository
        for repo in self._repositories:
            try:
                repo_health = await repo.health_check()
                repo_health["name"] = repo.name
                service_health["repositories"].append(repo_health)

                if repo_health.get("status") != "healthy":
                    service_health["issues"].append(f"Repository {repo.name}: {repo_health.get('status')}")

            except Exception as e:
                service_health["repositories"].append({
                    "name": repo.name,
                    "status": "error",
                    "error": str(e)
                })
                service_health["issues"].append(f"Repository {repo.name}: health check failed")

        # Overall status
        if service_health["issues"]:
            if len(service_health["issues"]) == len(self._repositories):
                service_health["status"] = "unhealthy"
            else:
                service_health["status"] = "degraded"

        return service_health

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        metrics = {
            "service_stats": self.performance_stats.copy(),
            "repository_metrics": {}
        }

        for repo in self._repositories:
            try:
                repo_metrics = repo.get_performance_metrics()
                metrics["repository_metrics"][repo.name] = repo_metrics
            except Exception as e:
                metrics["repository_metrics"][repo.name] = {"error": str(e)}

        return metrics

    # Integration methods for Strategy Pattern
    def get_properties_for_scoring(self, lead_preferences: Dict[str, Any],
                                  max_properties: int = 100) -> PropertyQueryBuilder:
        """
        Create optimized query for property scoring with Strategy Pattern.

        This method bridges the Repository Pattern with the existing Strategy Pattern
        by providing properties in the format expected by property scorers.

        Args:
            lead_preferences: Lead preferences from Strategy Pattern
            max_properties: Maximum number of properties to return for scoring

        Returns:
            Configured query builder for scoring use case
        """
        query_builder = self.create_query()

        # Apply lead preferences as filters
        if lead_preferences.get("budget"):
            # Add some buffer above budget for scoring comparison
            max_price = int(lead_preferences["budget"] * 1.2)  # 20% buffer
            query_builder.filter_by_price(max_price=max_price)

        if lead_preferences.get("location"):
            query_builder.filter_by_location(location=lead_preferences["location"])

        if lead_preferences.get("bedrooms"):
            min_beds = max(1, lead_preferences["bedrooms"] - 1)  # Allow some flexibility
            max_beds = lead_preferences["bedrooms"] + 1
            query_builder.filter_by_bedrooms(min_beds, max_beds)

        if lead_preferences.get("bathrooms"):
            min_baths = max(1, lead_preferences["bathrooms"] - 0.5)
            query_builder.filter_by_bathrooms(min_baths=min_baths)

        if lead_preferences.get("property_type"):
            query_builder.filter_by_property_types([lead_preferences["property_type"]])

        if lead_preferences.get("must_haves"):
            query_builder.filter_by_amenities(required=lead_preferences["must_haves"])

        # Optimize for scoring performance
        return (query_builder
                .sort_by("price", SortOrder.ASC)  # Start with lower prices
                .paginate(page=1, limit=max_properties)
                .include_metadata(True)
                .cache_control(use_cache=True, cache_ttl_seconds=300))

    async def load_properties_for_strategy_pattern(self, lead_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Load properties optimized for Strategy Pattern scoring.

        This replaces the _load_demo_properties() function in property_matcher_ai.py
        with Repository Pattern data loading.

        Args:
            lead_preferences: Lead preferences for filtering

        Returns:
            List of property dictionaries for Strategy Pattern scoring
        """
        query = self.get_properties_for_scoring(lead_preferences).build()
        result = await self.find_properties(query)

        if result.success:
            return result.data
        else:
            # Fallback to empty list if repositories fail
            print(f"Repository query failed: {result.errors}")
            return []

    # Private methods
    def _select_repositories(self, query: PropertyQuery,
                           prefer_repository: Optional[str] = None) -> List[IPropertyRepository]:
        """Select repositories based on query characteristics"""
        selected = []

        # Preferred repository first
        if prefer_repository:
            for repo in self._repositories:
                if repo.name == prefer_repository:
                    selected.append(repo)
                    break

        # Semantic query -> prefer RAG repository
        if query.semantic_query and not selected:
            for repo in self._repositories:
                if isinstance(repo, RAGPropertyRepository):
                    selected.append(repo)
                    break

        # Real-time data needed -> prefer MLS
        if not selected and (query.max_days_on_market is not None and query.max_days_on_market <= 7):
            for repo in self._repositories:
                if isinstance(repo, MLSAPIRepository):
                    selected.append(repo)
                    break

        # Default to primary + fallbacks
        if not selected:
            if self._primary_repository:
                selected.append(self._primary_repository)
            selected.extend(self._fallback_repositories)

        return selected[:self.max_concurrent_repos]

    async def _execute_single_query(self, repository: IPropertyRepository,
                                   query: PropertyQuery) -> RepositoryResult:
        """Execute query on single repository"""
        return await repository.find_properties(query)

    async def _execute_cascade_query(self, repositories: List[IPropertyRepository],
                                    query: PropertyQuery) -> RepositoryResult:
        """Execute query with cascade fallback"""
        last_error = None

        for repo in repositories:
            try:
                result = await repo.find_properties(query)
                if result.success and result.has_data:
                    return result
                last_error = result.errors
            except Exception as e:
                last_error = [str(e)]

        # All repositories failed
        return RepositoryResult(
            success=False,
            errors=last_error or ["All repositories failed"]
        )

    async def _execute_parallel_query(self, repositories: List[IPropertyRepository],
                                     query: PropertyQuery) -> RepositoryResult:
        """Execute query on multiple repositories in parallel"""
        tasks = [repo.find_properties(query) for repo in repositories]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge successful results
        all_properties = []
        all_errors = []
        total_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                all_errors.append(f"Repository {repositories[i].name}: {str(result)}")
            elif result.success:
                all_properties.extend(result.data)
                total_count = max(total_count, result.total_count or 0)
            else:
                all_errors.extend(result.errors)

        # Remove duplicates based on property ID
        unique_properties = []
        seen_ids = set()
        for prop in all_properties:
            prop_id = prop.get("id")
            if prop_id and prop_id not in seen_ids:
                unique_properties.append(prop)
                seen_ids.add(prop_id)

        return RepositoryResult(
            data=unique_properties,
            total_count=len(unique_properties),
            success=len(unique_properties) > 0,
            errors=all_errors,
            warnings=["Results merged from multiple repositories"] if len(unique_properties) > 0 else []
        )

    async def _create_repository_from_config(self, config: Dict[str, Any]) -> IPropertyRepository:
        """Create repository instance from configuration"""
        repo_type = config.get("type")
        repo_config = config.get("config", {})
        enable_caching = config.get("caching", {}).get("enabled", True)
        cache_config = config.get("caching", {})

        return await self.factory.create(
            repository_type=repo_type,
            config=repo_config,
            enable_caching=enable_caching,
            cache_config=cache_config
        )

    def _update_performance_stats(self, success: bool, execution_time_ms: float):
        """Update performance statistics"""
        if success:
            self.performance_stats["successful_queries"] += 1
        else:
            self.performance_stats["failed_queries"] += 1

        # Update rolling average
        total = self.performance_stats["total_queries"]
        current_avg = self.performance_stats["average_response_time"]
        self.performance_stats["average_response_time"] = (
            (current_avg * (total - 1) + execution_time_ms) / total
        )


# Convenience factory functions for common configurations
class PropertyDataServiceFactory:
    """Factory for creating pre-configured PropertyDataService instances"""

    @staticmethod
    async def create_demo_service(data_dir: str = "./data/knowledge_base") -> PropertyDataService:
        """Create service with JSON demo data"""
        data_path = Path(data_dir)
        json_files = list(data_path.glob("*.json"))

        if not json_files:
            raise RepositoryError(f"No JSON files found in {data_dir}")

        config = {
            "fallback_strategy": "cascade",
            "performance_monitoring": True
        }

        service = PropertyDataService(config)
        await service.initialize([
            {
                "name": "demo_json",
                "type": "json",
                "config": {
                    "data_paths": [str(f) for f in json_files],
                    "cache_ttl": 300,
                    "auto_refresh": True,
                    "normalize_data": True
                },
                "priority": 1,
                "fallback": False,
                "caching": {
                    "enabled": True,
                    "backend": "memory",
                    "max_size": 500
                }
            }
        ])

        return service

    @staticmethod
    async def create_production_service(mls_config: Dict[str, Any],
                                      json_fallback_paths: List[str] = None) -> PropertyDataService:
        """Create production service with MLS primary and JSON fallback"""
        config = {
            "fallback_strategy": "cascade",
            "performance_monitoring": True,
            "max_concurrent_repos": 2
        }

        repos_config = [
            {
                "name": "primary_mls",
                "type": "mls",
                "config": mls_config,
                "priority": 1,
                "fallback": False,
                "caching": {
                    "enabled": True,
                    "backend": "redis",
                    "redis_url": "redis://localhost:6379",
                    "ttl": 1800  # 30 minutes
                }
            }
        ]

        if json_fallback_paths:
            repos_config.append({
                "name": "fallback_json",
                "type": "json",
                "config": {
                    "data_paths": json_fallback_paths,
                    "cache_ttl": 600,
                    "auto_refresh": True
                },
                "priority": 0,
                "fallback": True,
                "caching": {
                    "enabled": True,
                    "backend": "memory",
                    "max_size": 1000
                }
            })

        service = PropertyDataService(config)
        await service.initialize(repos_config)
        return service

    @staticmethod
    async def create_hybrid_service(json_paths: List[str], mls_config: Dict[str, Any] = None,
                                  rag_config: Dict[str, Any] = None) -> PropertyDataService:
        """Create hybrid service with multiple repository types"""
        config = {
            "fallback_strategy": "parallel",
            "performance_monitoring": True,
            "max_concurrent_repos": 3
        }

        repos_config = []

        # JSON repository (always included)
        repos_config.append({
            "name": "json_data",
            "type": "json",
            "config": {
                "data_paths": json_paths,
                "cache_ttl": 300,
                "auto_refresh": True,
                "normalize_data": True
            },
            "priority": 1,
            "fallback": True,
            "caching": {"enabled": True, "backend": "memory"}
        })

        # MLS repository (if configured)
        if mls_config:
            repos_config.append({
                "name": "mls_api",
                "type": "mls",
                "config": mls_config,
                "priority": 2,
                "fallback": True,
                "caching": {"enabled": True, "backend": "memory"}
            })

        # RAG repository (if configured)
        if rag_config:
            repos_config.append({
                "name": "semantic_search",
                "type": "rag",
                "config": rag_config,
                "priority": 3,
                "fallback": True,
                "caching": {"enabled": True, "backend": "memory"}
            })

        service = PropertyDataService(config)
        await service.initialize(repos_config)
        return service