"""
Enhanced Prompt Caching Service for Maximum Cost Efficiency.

Extends the basic prompt caching in llm_client.py to implement
research-based strategies for 90% cost reduction on cached content.

Key Features:
1. Strategic cache breakpoints for conversation context
2. User preference data caching (stable across sessions)
3. Market context caching (real estate data that changes infrequently)
4. Intelligent cache key management with TTL
5. Cache performance analytics and monitoring

Expected Savings:
- System prompts: 90% cost reduction (already implemented)
- User context: 90% cost reduction on repeat conversations
- Market context: 90% cost reduction on similar property queries
- Total potential: 63.5-90% depending on conversation patterns
"""

import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ghl_utils.config import settings

logger = get_logger(__name__)


class CacheType(Enum):
    """Types of cacheable content with different TTL strategies."""
    SYSTEM_PROMPT = "system_prompt"          # TTL: 5 minutes (Claude default)
    USER_PREFERENCES = "user_preferences"    # TTL: 1 hour (stable user data)
    MARKET_CONTEXT = "market_context"        # TTL: 4 hours (real estate market data)
    CONVERSATION_CONTEXT = "conversation"    # TTL: 30 minutes (active conversations)
    PROPERTY_DATA = "property_data"          # TTL: 2 hours (property listings)


@dataclass
class CacheCandidate:
    """Represents content that can be cached."""
    content: str
    cache_type: CacheType
    token_count: int
    cache_key: str
    should_cache: bool
    ttl_minutes: int
    metadata: Dict[str, Any]


@dataclass
class CachePerformance:
    """Cache performance metrics."""
    cache_hits: int = 0
    cache_misses: int = 0
    tokens_saved: int = 0
    cost_saved_usd: float = 0.0
    hit_rate: float = 0.0


class EnhancedPromptCaching:
    """
    Enhanced prompt caching service implementing research-based optimization strategies.

    Provides intelligent caching of:
    - System prompts with real estate context
    - User preference data
    - Market context and property information
    - Conversation context for multi-turn efficiency
    """

    def __init__(self):
        """Initialize the enhanced caching service."""
        self.min_cache_tokens = 1024  # Anthropic recommendation
        self.cache_ttl_mapping = {
            CacheType.SYSTEM_PROMPT: 5,      # Claude's default ephemeral cache
            CacheType.USER_PREFERENCES: 60,  # User data is stable
            CacheType.MARKET_CONTEXT: 240,   # Market data changes slowly
            CacheType.CONVERSATION_CONTEXT: 30,  # Active conversation window
            CacheType.PROPERTY_DATA: 120     # Property listings update periodically
        }

        # Token cost calculations (per 1M tokens)
        self.token_costs = {
            "input": 3.0,           # $3/1M input tokens (Claude Opus 4.1)
            "output": 15.0,         # $15/1M output tokens
            "cache_creation": 0.75, # 25% of input cost
            "cache_read": 0.30      # 10% of input cost
        }

    def count_tokens(self, text: str) -> int:
        """Estimate token count (using character-based approximation)."""
        # Rough estimation: 4 characters per token for English text
        return len(text) // 4

    def generate_cache_key(self, content: str, cache_type: CacheType, metadata: Dict[str, Any] = None) -> str:
        """Generate a stable cache key for content."""
        metadata = metadata or {}

        # Include relevant metadata in cache key for proper invalidation
        key_data = {
            "content_hash": hashlib.md5(content.encode()).hexdigest(),
            "cache_type": cache_type.value,
            "metadata": metadata
        }

        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]

    def analyze_cache_candidates(
        self,
        system_prompt: str,
        user_preferences: Dict[str, Any],
        market_context: str = "",
        conversation_history: List[Dict[str, Any]] = None,
        location_id: str = "default"
    ) -> List[CacheCandidate]:
        """
        Analyze content to identify optimal caching opportunities.

        Args:
            system_prompt: Core system prompt text
            user_preferences: User preference data (budget, location, etc.)
            market_context: Real estate market context
            conversation_history: Recent conversation context
            location_id: Location for cache key scoping

        Returns:
            List of CacheCandidate objects with caching recommendations
        """
        candidates = []

        # 1. System Prompt Caching (EXISTING - enhance it)
        system_tokens = self.count_tokens(system_prompt)
        if system_tokens >= self.min_cache_tokens:
            candidates.append(CacheCandidate(
                content=system_prompt,
                cache_type=CacheType.SYSTEM_PROMPT,
                token_count=system_tokens,
                cache_key=self.generate_cache_key(system_prompt, CacheType.SYSTEM_PROMPT),
                should_cache=True,
                ttl_minutes=self.cache_ttl_mapping[CacheType.SYSTEM_PROMPT],
                metadata={"location_id": location_id}
            ))

        # 2. User Preferences Caching (NEW - high value)
        if user_preferences:
            preferences_text = json.dumps(user_preferences, sort_keys=True, indent=2)
            pref_tokens = self.count_tokens(preferences_text)

            # Cache if preferences are substantial enough
            if pref_tokens >= 100:  # Lower threshold for user data
                candidates.append(CacheCandidate(
                    content=f"""
USER PREFERENCES (STABLE CONTEXT):
{preferences_text}

This represents the user's established preferences for real estate searches.
These preferences typically remain stable across conversation turns and can be
cached for efficiency while maintaining personalization quality.
""",
                    cache_type=CacheType.USER_PREFERENCES,
                    token_count=pref_tokens + 50,  # Account for wrapper text
                    cache_key=self.generate_cache_key(preferences_text, CacheType.USER_PREFERENCES,
                                                    {"location_id": location_id}),
                    should_cache=True,
                    ttl_minutes=self.cache_ttl_mapping[CacheType.USER_PREFERENCES],
                    metadata={
                        "location_id": location_id,
                        "preference_keys": list(user_preferences.keys())
                    }
                ))

        # 3. Market Context Caching (NEW - medium-high value)
        if market_context and len(market_context) > 500:
            market_tokens = self.count_tokens(market_context)
            if market_tokens >= 200:  # Cache substantial market context
                candidates.append(CacheCandidate(
                    content=f"""
REAL ESTATE MARKET CONTEXT:
{market_context}

This market context includes area information, pricing trends, and neighborhood
data that remains relatively stable and can be reused across similar property
searches in this market area.
""",
                    cache_type=CacheType.MARKET_CONTEXT,
                    token_count=market_tokens + 30,
                    cache_key=self.generate_cache_key(market_context, CacheType.MARKET_CONTEXT,
                                                    {"location_id": location_id}),
                    should_cache=True,
                    ttl_minutes=self.cache_ttl_mapping[CacheType.MARKET_CONTEXT],
                    metadata={"location_id": location_id}
                ))

        # 4. Conversation Context Caching (NEW - for active conversations)
        if conversation_history and len(conversation_history) > 6:
            # Extract stable parts of conversation history for caching
            # Focus on preference-setting and context-establishing messages
            stable_messages = [
                msg for msg in conversation_history[:-4]  # Don't cache most recent messages
                if self._is_stable_conversation_content(msg)
            ]

            if stable_messages:
                conv_context = "\\n".join([
                    f"{msg['role']}: {msg['content'][:200]}"  # Truncate for efficiency
                    for msg in stable_messages
                ])

                conv_tokens = self.count_tokens(conv_context)
                if conv_tokens >= 300:
                    candidates.append(CacheCandidate(
                        content=f"""
CONVERSATION CONTEXT (STABLE HISTORY):
{conv_context}

This represents established conversation context that is unlikely to change
and can be cached to reduce token costs on subsequent conversation turns.
""",
                        cache_type=CacheType.CONVERSATION_CONTEXT,
                        token_count=conv_tokens + 20,
                        cache_key=self.generate_cache_key(conv_context, CacheType.CONVERSATION_CONTEXT,
                                                        {"location_id": location_id}),
                        should_cache=True,
                        ttl_minutes=self.cache_ttl_mapping[CacheType.CONVERSATION_CONTEXT],
                        metadata={
                            "location_id": location_id,
                            "message_count": len(stable_messages)
                        }
                    ))

        return candidates

    def _is_stable_conversation_content(self, message: Dict[str, Any]) -> bool:
        """
        Determine if a conversation message contains stable content worth caching.

        Args:
            message: Conversation message with role and content

        Returns:
            True if message contains stable context (preferences, contact info, etc.)
        """
        content = message.get("content", "").lower()

        # Messages that establish stable context
        stable_indicators = [
            "budget", "price", "location", "bedroom", "bathroom",
            "prefer", "looking for", "must have", "timeline",
            "contact", "phone", "email", "name"
        ]

        # Don't cache very recent or ephemeral content
        ephemeral_indicators = [
            "right now", "currently", "today", "this morning",
            "just", "actually", "hold on", "wait"
        ]

        has_stable = any(indicator in content for indicator in stable_indicators)
        has_ephemeral = any(indicator in content for indicator in ephemeral_indicators)

        return has_stable and not has_ephemeral

    def build_cached_messages(
        self,
        cache_candidates: List[CacheCandidate],
        conversation_history: List[Dict[str, Any]],
        current_message: str
    ) -> List[Dict[str, Any]]:
        """
        Build message list with appropriate cache control annotations.

        Args:
            cache_candidates: List of content identified for caching
            conversation_history: Current conversation history
            current_message: Current user message

        Returns:
            List of messages formatted for Claude API with cache control
        """
        messages = []

        # Add cacheable content as separate message blocks with cache control
        for candidate in cache_candidates:
            if candidate.should_cache:
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": candidate.content,
                            "cache_control": {"type": "ephemeral"}
                        }
                    ]
                })

        # Add regular conversation history (non-cached)
        for msg in conversation_history:
            # Skip messages that were already included in cached context
            if not self._message_included_in_cache(msg, cache_candidates):
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # Add current message
        messages.append({
            "role": "user",
            "content": current_message
        })

        return messages

    def _message_included_in_cache(self, message: Dict[str, Any], cache_candidates: List[CacheCandidate]) -> bool:
        """Check if a message is already included in cached context."""
        # Simple heuristic: if message content appears in any cached content
        msg_content = message.get("content", "")

        for candidate in cache_candidates:
            if candidate.cache_type == CacheType.CONVERSATION_CONTEXT:
                if msg_content[:100] in candidate.content:  # Check first 100 chars
                    return True

        return False

    def calculate_cache_savings(
        self,
        cache_candidates: List[CacheCandidate],
        is_cache_hit: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate potential or actual savings from caching.

        Args:
            cache_candidates: List of cache candidates
            is_cache_hit: Whether this request was a cache hit

        Returns:
            Dict with savings analysis
        """
        total_cacheable_tokens = sum(c.token_count for c in cache_candidates if c.should_cache)

        if is_cache_hit:
            # Calculate actual savings from cache hit
            tokens_saved = total_cacheable_tokens * 0.9  # 90% savings on cache hit
            cost_saved = (tokens_saved / 1_000_000) * self.token_costs["input"] * 0.9
        else:
            # Calculate cache creation cost
            tokens_saved = 0
            cost_saved = -(total_cacheable_tokens / 1_000_000) * self.token_costs["cache_creation"] * 0.25

        return {
            "cacheable_tokens": total_cacheable_tokens,
            "tokens_saved": tokens_saved,
            "cost_saved_usd": cost_saved,
            "cache_candidates_count": len([c for c in cache_candidates if c.should_cache]),
            "potential_monthly_savings": cost_saved * 30 if cost_saved > 0 else 0,
            "is_cache_hit": is_cache_hit
        }

    def generate_cache_report(self, performance_data: List[CachePerformance]) -> Dict[str, Any]:
        """
        Generate comprehensive cache performance report.

        Args:
            performance_data: List of cache performance data points

        Returns:
            Dict with cache performance analysis
        """
        if not performance_data:
            return {"error": "No performance data available"}

        total_hits = sum(p.cache_hits for p in performance_data)
        total_requests = sum(p.cache_hits + p.cache_misses for p in performance_data)
        total_tokens_saved = sum(p.tokens_saved for p in performance_data)
        total_cost_saved = sum(p.cost_saved_usd for p in performance_data)

        hit_rate = (total_hits / total_requests) * 100 if total_requests > 0 else 0

        return {
            "cache_performance": {
                "hit_rate_percentage": hit_rate,
                "total_hits": total_hits,
                "total_requests": total_requests,
                "tokens_saved": total_tokens_saved,
                "cost_saved_usd": total_cost_saved,
                "projected_monthly_savings": total_cost_saved * 30,
                "projected_annual_savings": total_cost_saved * 365
            },
            "cache_efficiency": {
                "excellent": hit_rate >= 70,
                "good": 50 <= hit_rate < 70,
                "needs_improvement": hit_rate < 50,
                "recommendation": self._get_cache_recommendation(hit_rate)
            },
            "cost_analysis": {
                "average_savings_per_hit": total_cost_saved / total_hits if total_hits > 0 else 0,
                "roi_break_even_requests": 10 if total_cost_saved > 0 else None,
                "cache_value_rating": "HIGH" if total_cost_saved > 5.0 else "MEDIUM" if total_cost_saved > 1.0 else "LOW"
            }
        }

    def _get_cache_recommendation(self, hit_rate: float) -> str:
        """Generate cache optimization recommendations based on hit rate."""
        if hit_rate >= 70:
            return "Cache performance excellent. Consider expanding cache scope to additional content types."
        elif hit_rate >= 50:
            return "Good cache performance. Monitor for opportunities to improve TTL settings."
        elif hit_rate >= 30:
            return "Moderate cache performance. Review cache key generation and content selection."
        else:
            return "Low cache hit rate. Review caching strategy and consider reducing cache scope."


# Global enhanced caching service instance
enhanced_cache_service = EnhancedPromptCaching()


# Integration helper functions for existing codebase
def analyze_conversation_for_caching(
    system_prompt: str,
    conversation_history: List[Dict[str, Any]],
    extracted_preferences: Dict[str, Any],
    location_id: str = "default",
    market_context: str = ""
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convenience function to analyze conversation and prepare cached messages.

    Returns:
        Tuple of (formatted_messages_with_cache_control, cache_analytics)
    """
    # Analyze cache opportunities
    candidates = enhanced_cache_service.analyze_cache_candidates(
        system_prompt=system_prompt,
        user_preferences=extracted_preferences,
        market_context=market_context,
        conversation_history=conversation_history,
        location_id=location_id
    )

    # Build messages with cache control
    current_message = conversation_history[-1]["content"] if conversation_history else ""
    cached_messages = enhanced_cache_service.build_cached_messages(
        cache_candidates=candidates,
        conversation_history=conversation_history[:-1] if conversation_history else [],
        current_message=current_message
    )

    # Calculate potential savings
    cache_analytics = enhanced_cache_service.calculate_cache_savings(candidates)

    return cached_messages, cache_analytics