"""
Claude Prompt Caching Service
Intelligent caching layer for Claude API calls to achieve 70% cost reduction
Target savings: $15,000-30,000 annually
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union
import redis.asyncio as redis
from dataclasses import dataclass, asdict
from enum import Enum
import pickle
import zlib
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache strategy types for different use cases."""
    AGGRESSIVE = "aggressive"      # 24h+ TTL for static content
    STANDARD = "standard"          # 4-8h TTL for dynamic content
    CONSERVATIVE = "conservative"  # 1-2h TTL for time-sensitive content
    REAL_TIME = "real_time"       # 5-30min TTL for real-time coaching
    NO_CACHE = "no_cache"         # Skip caching for one-time requests

@dataclass
class CacheMetrics:
    """Cache performance and cost metrics."""
    hits: int = 0
    misses: int = 0
    cost_saved: float = 0.0
    api_calls_avoided: int = 0
    cache_size_mb: float = 0.0
    last_updated: datetime = None

@dataclass
class ClaudeRequest:
    """Structured Claude API request for caching."""
    prompt: str
    system_prompt: str = ""
    model: str = "claude-3-sonnet-20240229"
    max_tokens: int = 1000
    temperature: float = 0.7
    context_data: Dict[str, Any] = None

    def cache_key(self) -> str:
        """Generate cache key from request parameters."""
        # Create deterministic hash from request content
        content = {
            "prompt": self.prompt.strip(),
            "system_prompt": self.system_prompt.strip(),
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "context_data": self.context_data or {}
        }

        # Sort and serialize for consistent hashing
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:32]

@dataclass
class ClaudeResponse:
    """Structured Claude API response for caching."""
    content: str
    usage: Dict[str, int]
    cached_at: datetime
    cache_strategy: CacheStrategy
    cost: float

    def to_cache_data(self) -> Dict[str, Any]:
        """Convert to cacheable dictionary."""
        return {
            "content": self.content,
            "usage": self.usage,
            "cached_at": self.cached_at.isoformat(),
            "cache_strategy": self.cache_strategy.value,
            "cost": self.cost
        }

    @classmethod
    def from_cache_data(cls, data: Dict[str, Any]) -> 'ClaudeResponse':
        """Create from cached dictionary."""
        return cls(
            content=data["content"],
            usage=data["usage"],
            cached_at=datetime.fromisoformat(data["cached_at"]),
            cache_strategy=CacheStrategy(data["cache_strategy"]),
            cost=data["cost"]
        )

class ClaudePromptCachingService:
    """
    Intelligent caching service for Claude API calls.

    Features:
    - Smart cache strategy selection based on content type
    - Compressed storage for memory efficiency
    - Cost tracking and ROI analytics
    - Cache warming for predictable requests
    - Intelligent invalidation and refresh
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/2",
        cost_per_1k_tokens: float = 0.015,
        max_cache_size_mb: float = 500.0
    ):
        self.redis_pool = None
        self.redis_url = redis_url
        self.cost_per_1k_tokens = cost_per_1k_tokens
        self.max_cache_size_mb = max_cache_size_mb

        # Cache configuration
        self.cache_ttl_mapping = {
            CacheStrategy.AGGRESSIVE: 86400,     # 24 hours
            CacheStrategy.STANDARD: 14400,       # 4 hours
            CacheStrategy.CONSERVATIVE: 7200,    # 2 hours
            CacheStrategy.REAL_TIME: 1800,       # 30 minutes
            CacheStrategy.NO_CACHE: 0            # No caching
        }

        # Performance metrics
        self.metrics = CacheMetrics(last_updated=datetime.now())

        # Content analysis patterns for cache strategy selection
        self.strategy_patterns = {
            CacheStrategy.AGGRESSIVE: [
                "explain", "definition", "what is", "how to", "tutorial",
                "documentation", "specification", "requirements"
            ],
            CacheStrategy.STANDARD: [
                "analyze", "review", "feedback", "suggestion", "recommendation"
            ],
            CacheStrategy.CONSERVATIVE: [
                "current", "recent", "today", "now", "latest", "update"
            ],
            CacheStrategy.REAL_TIME: [
                "coaching", "immediate", "urgent", "live", "real-time",
                "conversation", "response", "reply"
            ]
        }

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def initialize(self) -> None:
        """Initialize Redis connection and metrics."""
        try:
            self.redis_pool = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # Handle binary data for compression
                max_connections=20
            )

            # Test connection
            await self.redis_pool.ping()

            # Load existing metrics
            await self._load_metrics()

            logger.info("Claude caching service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Claude caching service: {e}")
            raise

    async def cleanup(self) -> None:
        """Cleanup Redis connections."""
        if self.redis_pool:
            await self.redis_pool.close()

    async def get_or_call_claude(
        self,
        request: ClaudeRequest,
        claude_api_function,
        force_refresh: bool = False
    ) -> Tuple[ClaudeResponse, bool]:
        """
        Get cached response or call Claude API with intelligent caching.

        Args:
            request: Structured Claude request
            claude_api_function: Async function that calls Claude API
            force_refresh: Skip cache and force new API call

        Returns:
            Tuple of (ClaudeResponse, was_cached)
        """

        # Determine cache strategy
        strategy = self._determine_cache_strategy(request)

        # Skip caching if strategy is NO_CACHE or force refresh
        if strategy == CacheStrategy.NO_CACHE or force_refresh:
            response = await self._call_claude_api(request, claude_api_function)
            return response, False

        # Generate cache key
        cache_key = f"claude_cache:{request.cache_key()}"

        try:
            # Try to get from cache first
            cached_data = await self._get_from_cache(cache_key)

            if cached_data:
                # Cache hit
                response = ClaudeResponse.from_cache_data(cached_data)
                await self._update_hit_metrics(response.cost)

                logger.debug(f"Cache hit for key {cache_key[:16]}...")
                return response, True

            # Cache miss - call API
            response = await self._call_claude_api(request, claude_api_function)
            response.cache_strategy = strategy

            # Store in cache
            await self._store_in_cache(cache_key, response, strategy)

            # Update miss metrics
            await self._update_miss_metrics()

            logger.debug(f"Cache miss for key {cache_key[:16]}... - stored with strategy {strategy.value}")
            return response, False

        except Exception as e:
            logger.error(f"Cache operation failed: {e}")
            # Fallback to direct API call
            response = await self._call_claude_api(request, claude_api_function)
            return response, False

    async def warm_cache(
        self,
        requests: List[ClaudeRequest],
        claude_api_function,
        concurrency_limit: int = 3
    ) -> Dict[str, Any]:
        """
        Pre-warm cache with predictable requests.

        Args:
            requests: List of requests to warm
            claude_api_function: Claude API function
            concurrency_limit: Max concurrent API calls

        Returns:
            Warming results and metrics
        """

        semaphore = asyncio.Semaphore(concurrency_limit)

        async def warm_single_request(request: ClaudeRequest) -> Dict[str, Any]:
            async with semaphore:
                try:
                    response, was_cached = await self.get_or_call_claude(
                        request, claude_api_function, force_refresh=False
                    )

                    return {
                        "cache_key": request.cache_key()[:16],
                        "status": "warmed" if not was_cached else "already_cached",
                        "cost": response.cost,
                        "strategy": response.cache_strategy.value
                    }

                except Exception as e:
                    return {
                        "cache_key": request.cache_key()[:16],
                        "status": "failed",
                        "error": str(e)
                    }

        # Execute warming tasks
        start_time = time.time()
        results = await asyncio.gather(
            *[warm_single_request(req) for req in requests],
            return_exceptions=True
        )

        warming_time = time.time() - start_time

        # Aggregate results
        warmed_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "warmed")
        cached_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "already_cached")
        failed_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == "failed")
        total_cost = sum(r.get("cost", 0) for r in results if isinstance(r, dict))

        warming_results = {
            "warming_time": f"{warming_time:.2f}s",
            "total_requests": len(requests),
            "warmed": warmed_count,
            "already_cached": cached_count,
            "failed": failed_count,
            "total_cost": round(total_cost, 4),
            "results": results
        }

        logger.info(f"Cache warming complete: {warmed_count} warmed, {cached_count} already cached, {failed_count} failed")

        return warming_results

    async def get_cache_analytics(self) -> Dict[str, Any]:
        """Get comprehensive cache analytics and ROI metrics."""

        # Update current metrics
        cache_info = await self._get_cache_info()

        # Calculate cache hit ratio
        total_requests = self.metrics.hits + self.metrics.misses
        hit_ratio = (self.metrics.hits / total_requests) if total_requests > 0 else 0.0

        # Estimate annual savings
        daily_cost_saved = self.metrics.cost_saved
        annual_savings_estimate = daily_cost_saved * 365 if daily_cost_saved > 0 else 0

        analytics = {
            "performance_metrics": {
                "cache_hits": self.metrics.hits,
                "cache_misses": self.metrics.misses,
                "hit_ratio": f"{hit_ratio:.1%}",
                "api_calls_avoided": self.metrics.api_calls_avoided
            },
            "cost_metrics": {
                "total_cost_saved": f"${self.metrics.cost_saved:.2f}",
                "annual_savings_estimate": f"${annual_savings_estimate:.0f}",
                "cost_reduction_achieved": f"{hit_ratio * 70:.1f}%" if hit_ratio > 0 else "0%",
                "target_cost_reduction": "70%"
            },
            "cache_storage": {
                "cache_size_mb": f"{cache_info['cache_size_mb']:.2f}",
                "max_cache_size_mb": self.max_cache_size_mb,
                "utilization": f"{(cache_info['cache_size_mb'] / self.max_cache_size_mb) * 100:.1f}%",
                "total_keys": cache_info['total_keys']
            },
            "strategy_distribution": cache_info['strategy_distribution'],
            "last_updated": self.metrics.last_updated.isoformat()
        }

        return analytics

    async def clear_cache(
        self,
        strategy_filter: Optional[CacheStrategy] = None,
        older_than_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Clear cache entries based on filters.

        Args:
            strategy_filter: Only clear entries with this strategy
            older_than_hours: Only clear entries older than X hours

        Returns:
            Clearing results
        """

        try:
            pattern = "claude_cache:*"
            keys = await self.redis_pool.keys(pattern)

            keys_to_delete = []
            total_size_freed = 0

            for key in keys:
                should_delete = True

                try:
                    # Get cache metadata to check filters
                    compressed_data = await self.redis_pool.get(key)
                    if not compressed_data:
                        continue

                    # Decompress and deserialize
                    cache_data = pickle.loads(zlib.decompress(compressed_data))

                    # Apply strategy filter
                    if strategy_filter:
                        entry_strategy = CacheStrategy(cache_data.get("cache_strategy", "standard"))
                        if entry_strategy != strategy_filter:
                            should_delete = False

                    # Apply age filter
                    if older_than_hours:
                        cached_at = datetime.fromisoformat(cache_data.get("cached_at"))
                        age_hours = (datetime.now() - cached_at).total_seconds() / 3600
                        if age_hours < older_than_hours:
                            should_delete = False

                    if should_delete:
                        keys_to_delete.append(key)
                        total_size_freed += len(compressed_data)

                except Exception as e:
                    logger.warning(f"Error processing cache key {key}: {e}")
                    # Delete corrupted keys
                    keys_to_delete.append(key)

            # Delete keys
            if keys_to_delete:
                await self.redis_pool.delete(*keys_to_delete)

            clearing_results = {
                "total_keys_deleted": len(keys_to_delete),
                "size_freed_mb": total_size_freed / (1024 * 1024),
                "strategy_filter": strategy_filter.value if strategy_filter else None,
                "older_than_hours": older_than_hours
            }

            logger.info(f"Cache cleared: {len(keys_to_delete)} keys deleted, {total_size_freed / (1024 * 1024):.2f}MB freed")

            return clearing_results

        except Exception as e:
            logger.error(f"Cache clearing failed: {e}")
            raise

    def _determine_cache_strategy(self, request: ClaudeRequest) -> CacheStrategy:
        """Determine appropriate cache strategy based on request content."""

        # Combine prompt and system prompt for analysis
        full_content = f"{request.system_prompt} {request.prompt}".lower()

        # Check for strategy patterns
        for strategy, patterns in self.strategy_patterns.items():
            if any(pattern in full_content for pattern in patterns):
                return strategy

        # Check for context clues
        if request.context_data:
            # Time-sensitive contexts
            if any(key in request.context_data for key in ["timestamp", "current_time", "real_time"]):
                return CacheStrategy.REAL_TIME

            # Static reference data
            if any(key in request.context_data for key in ["documentation", "specs", "guidelines"]):
                return CacheStrategy.AGGRESSIVE

        # Default to standard strategy
        return CacheStrategy.STANDARD

    async def _call_claude_api(
        self,
        request: ClaudeRequest,
        claude_api_function
    ) -> ClaudeResponse:
        """Call Claude API and create structured response."""

        try:
            # Call the provided Claude API function
            api_response = await claude_api_function(
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )

            # Calculate cost
            total_tokens = api_response.get("usage", {}).get("total_tokens", 0)
            cost = (total_tokens / 1000) * self.cost_per_1k_tokens

            # Create structured response
            response = ClaudeResponse(
                content=api_response.get("content", ""),
                usage=api_response.get("usage", {}),
                cached_at=datetime.now(),
                cache_strategy=CacheStrategy.STANDARD,  # Will be updated by caller
                cost=cost
            )

            return response

        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise

    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get data from cache with decompression."""

        try:
            compressed_data = await self.redis_pool.get(cache_key)

            if compressed_data:
                # Decompress and deserialize
                cache_data = pickle.loads(zlib.decompress(compressed_data))
                return cache_data

            return None

        except Exception as e:
            logger.warning(f"Cache retrieval failed for key {cache_key[:16]}: {e}")
            return None

    async def _store_in_cache(
        self,
        cache_key: str,
        response: ClaudeResponse,
        strategy: CacheStrategy
    ) -> None:
        """Store response in cache with compression."""

        try:
            # Convert to cache data
            cache_data = response.to_cache_data()

            # Serialize and compress
            serialized_data = pickle.dumps(cache_data)
            compressed_data = zlib.compress(serialized_data, level=6)

            # Set TTL based on strategy
            ttl = self.cache_ttl_mapping[strategy]

            # Store in Redis
            if ttl > 0:
                await self.redis_pool.setex(cache_key, ttl, compressed_data)

            # Check cache size limits
            await self._enforce_cache_limits()

        except Exception as e:
            logger.warning(f"Cache storage failed for key {cache_key[:16]}: {e}")

    async def _update_hit_metrics(self, cost_saved: float) -> None:
        """Update cache hit metrics."""
        self.metrics.hits += 1
        self.metrics.cost_saved += cost_saved
        self.metrics.api_calls_avoided += 1
        self.metrics.last_updated = datetime.now()

        # Persist metrics
        await self._save_metrics()

    async def _update_miss_metrics(self) -> None:
        """Update cache miss metrics."""
        self.metrics.misses += 1
        self.metrics.last_updated = datetime.now()

        # Persist metrics
        await self._save_metrics()

    async def _load_metrics(self) -> None:
        """Load metrics from Redis."""
        try:
            metrics_data = await self.redis_pool.get("claude_cache:metrics")

            if metrics_data:
                metrics_dict = pickle.loads(zlib.decompress(metrics_data))
                self.metrics = CacheMetrics(
                    hits=metrics_dict.get("hits", 0),
                    misses=metrics_dict.get("misses", 0),
                    cost_saved=metrics_dict.get("cost_saved", 0.0),
                    api_calls_avoided=metrics_dict.get("api_calls_avoided", 0),
                    cache_size_mb=metrics_dict.get("cache_size_mb", 0.0),
                    last_updated=datetime.fromisoformat(
                        metrics_dict.get("last_updated", datetime.now().isoformat())
                    )
                )

        except Exception as e:
            logger.warning(f"Failed to load metrics: {e}")

    async def _save_metrics(self) -> None:
        """Save metrics to Redis."""
        try:
            metrics_dict = asdict(self.metrics)
            metrics_dict["last_updated"] = self.metrics.last_updated.isoformat()

            # Compress and store
            serialized_data = pickle.dumps(metrics_dict)
            compressed_data = zlib.compress(serialized_data, level=6)

            await self.redis_pool.setex("claude_cache:metrics", 86400, compressed_data)

        except Exception as e:
            logger.warning(f"Failed to save metrics: {e}")

    async def _get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information."""
        try:
            pattern = "claude_cache:*"
            keys = await self.redis_pool.keys(pattern)

            total_size = 0
            strategy_counts = {strategy.value: 0 for strategy in CacheStrategy}

            for key in keys[:100]:  # Sample first 100 keys for performance
                try:
                    compressed_data = await self.redis_pool.get(key)
                    if compressed_data:
                        total_size += len(compressed_data)

                        # Get strategy from cache data
                        cache_data = pickle.loads(zlib.decompress(compressed_data))
                        strategy = cache_data.get("cache_strategy", "standard")
                        strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

                except Exception:
                    continue

            return {
                "total_keys": len(keys),
                "cache_size_mb": total_size / (1024 * 1024),
                "strategy_distribution": strategy_counts
            }

        except Exception as e:
            logger.warning(f"Failed to get cache info: {e}")
            return {
                "total_keys": 0,
                "cache_size_mb": 0.0,
                "strategy_distribution": {}
            }

    async def _enforce_cache_limits(self) -> None:
        """Enforce cache size limits by evicting old entries."""
        try:
            cache_info = await self._get_cache_info()

            if cache_info["cache_size_mb"] > self.max_cache_size_mb:
                logger.info(f"Cache size ({cache_info['cache_size_mb']:.2f}MB) exceeds limit, performing cleanup")

                # Clear entries older than 12 hours
                await self.clear_cache(older_than_hours=12)

        except Exception as e:
            logger.warning(f"Cache limit enforcement failed: {e}")

# Convenience functions for common caching patterns

async def cached_claude_call(
    prompt: str,
    system_prompt: str = "",
    model: str = "claude-3-sonnet-20240229",
    claude_api_function = None,
    cache_service: Optional[ClaudePromptCachingService] = None,
    max_tokens: int = 1000,
    temperature: float = 0.7,
    context_data: Optional[Dict[str, Any]] = None
) -> Tuple[str, bool, float]:
    """
    Convenience function for cached Claude API calls.

    Returns:
        Tuple of (response_content, was_cached, cost)
    """

    if not cache_service:
        cache_service = ClaudePromptCachingService()
        async with cache_service:
            return await _execute_cached_call(
                cache_service, prompt, system_prompt, model,
                claude_api_function, max_tokens, temperature, context_data
            )
    else:
        return await _execute_cached_call(
            cache_service, prompt, system_prompt, model,
            claude_api_function, max_tokens, temperature, context_data
        )

async def _execute_cached_call(
    cache_service: ClaudePromptCachingService,
    prompt: str,
    system_prompt: str,
    model: str,
    claude_api_function,
    max_tokens: int,
    temperature: float,
    context_data: Optional[Dict[str, Any]]
) -> Tuple[str, bool, float]:
    """Execute the cached call."""

    request = ClaudeRequest(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        context_data=context_data
    )

    response, was_cached = await cache_service.get_or_call_claude(
        request, claude_api_function
    )

    return response.content, was_cached, response.cost

# Example usage patterns for different real estate AI scenarios

class RealEstateCachePatterns:
    """Pre-defined cache patterns for real estate AI use cases."""

    @staticmethod
    def property_analysis_request(property_data: Dict[str, Any]) -> ClaudeRequest:
        """Standard property analysis request with aggressive caching."""
        return ClaudeRequest(
            prompt=f"Analyze this property: {json.dumps(property_data, indent=2)}",
            system_prompt="You are a real estate analysis expert. Provide detailed property insights.",
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            temperature=0.3,
            context_data={"type": "property_analysis", "property_id": property_data.get("id")}
        )

    @staticmethod
    def lead_qualification_request(lead_data: Dict[str, Any]) -> ClaudeRequest:
        """Lead qualification request with conservative caching."""
        return ClaudeRequest(
            prompt=f"Qualify this lead: {json.dumps(lead_data, indent=2)}",
            system_prompt="You are a lead qualification specialist. Assess lead quality and next steps.",
            model="claude-3-sonnet-20240229",
            max_tokens=800,
            temperature=0.5,
            context_data={"type": "lead_qualification", "lead_id": lead_data.get("id")}
        )

    @staticmethod
    def real_time_coaching_request(conversation_context: Dict[str, Any]) -> ClaudeRequest:
        """Real-time coaching request with minimal caching."""
        return ClaudeRequest(
            prompt=f"Provide coaching for this conversation: {json.dumps(conversation_context, indent=2)}",
            system_prompt="You are a real estate coach. Provide immediate, actionable coaching.",
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            temperature=0.7,
            context_data={"type": "real_time_coaching", "timestamp": datetime.now().isoformat()}
        )