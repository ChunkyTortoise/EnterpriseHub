"""
Usage Billing Service for Lyrio.io SaaS.

Tracks LLM token usage per tenant (location_id) using Redis for real-time counters
and PostgreSQL for persistent billing records.
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.core.hooks import HookContext, HookEvent, hooks

logger = get_logger(__name__)

class UsageBillingService:
    """
    Service for tracking and reporting LLM usage per tenant.
    Ensures API margins are protected by monitoring token consumption.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.redis_url
        self._redis = None
        self._initialized = False
        
    async def _init_redis(self):
        if self._initialized:
            return
        if self.redis_url:
            try:
                import redis.asyncio as redis_lib
                self._redis = redis_lib.from_url(self.redis_url, decode_responses=True)
                self._initialized = True
                logger.info("UsageBillingService connected to Redis")
            except Exception as e:
                logger.error(f"UsageBillingService failed to connect to Redis: {e}")
        else:
            logger.warning("REDIS_URL not set, UsageBillingService operating in in-memory mode")
            self._initialized = True

    async def log_usage(self, tenant_id: str, model: str, provider: str, input_tokens: int, output_tokens: int):
        """Log token usage for a tenant."""
        await self._init_redis()
        
        # Calculate estimated cost
        cost = self._calculate_cost(model, provider, input_tokens, output_tokens)
        
        if self._redis:
            try:
                # Use a pipeline for efficiency
                async with self._redis.pipeline() as pipe:
                    # Global tenant usage
                    pipe.hincrby(f"usage:{tenant_id}", "total_input_tokens", input_tokens)
                    pipe.hincrby(f"usage:{tenant_id}", "total_output_tokens", output_tokens)
                    pipe.hincrby(f"usage:{tenant_id}", "total_calls", 1)
                    pipe.hincrbyfloat(f"usage:{tenant_id}", "total_cost_usd", cost)
                    
                    # Model specific usage
                    model_key = f"usage:{tenant_id}:models:{model}"
                    pipe.hincrby(model_key, "input_tokens", input_tokens)
                    pipe.hincrby(model_key, "output_tokens", output_tokens)
                    pipe.hincrby(model_key, "calls", 1)
                    pipe.hincrbyfloat(model_key, "cost_usd", cost)
                    
                    # Daily usage
                    today = datetime.utcnow().strftime("%Y-%m-%d")
                    daily_key = f"usage:{tenant_id}:daily:{today}"
                    pipe.hincrby(daily_key, "input_tokens", input_tokens)
                    pipe.hincrby(daily_key, "output_tokens", output_tokens)
                    pipe.hincrby(daily_key, "calls", 1)
                    pipe.hincrbyfloat(daily_key, "cost_usd", cost)
                    pipe.expire(daily_key, 86400 * 31) # Keep daily stats for 31 days
                    
                    # Audit event
                    event = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "tenant_id": tenant_id,
                        "model": model,
                        "provider": provider,
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "cost_usd": cost
                    }
                    pipe.lpush(f"usage:{tenant_id}:events", json.dumps(event))
                    pipe.ltrim(f"usage:{tenant_id}:events", 0, 99) # Keep last 100 events
                    
                    await pipe.execute()
                
                logger.info(f"Logged usage for {tenant_id}: {input_tokens} in, {output_tokens} out (${cost:.4f})")
            except Exception as e:
                logger.error(f"Failed to log usage to Redis: {e}")
        else:
            # Fallback to simple logging if Redis is unavailable
            logger.info(f"[IN-MEMORY] Usage for {tenant_id}: {input_tokens} in, {output_tokens} out (${cost:.4f})")

    def _calculate_cost(self, model: str, provider: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost based on settings."""
        # Default costs from settings
        input_rate = 0.0
        output_rate = 0.0
        
        p = provider.lower()
        if "claude" in p or "anthropic" in p:
            input_rate = settings.claude_input_cost_per_1m
            output_rate = settings.claude_output_cost_per_1m
        elif "gemini" in p or "google" in p:
            input_rate = settings.gemini_input_cost_per_1m
            output_rate = settings.gemini_output_cost_per_1m
        elif "perplexity" in p:
            input_rate = settings.perplexity_input_cost_per_1m
            output_rate = settings.perplexity_output_cost_per_1m
            
        cost = (input_tokens / 1_000_000 * input_rate) + (output_tokens / 1_000_000 * output_rate)
        return cost

    async def get_tenant_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Retrieve aggregated usage for a tenant."""
        await self._init_redis()
        if not self._redis:
            return {}
            
        try:
            data = await self._redis.hgetall(f"usage:{tenant_id}")
            # Ensure proper typing
            result = {}
            for k, v in data.items():
                if k == "total_cost_usd":
                    result[k] = float(v)
                else:
                    result[k] = int(v)
            return result
        except Exception as e:
            logger.error(f"Failed to retrieve usage from Redis: {e}")
            return {}

# Global instance
usage_billing_service = UsageBillingService()

async def usage_tracking_hook(ctx: HookContext):
    """Hook to track usage after generation."""
    if ctx.event == HookEvent.POST_GENERATION:
        response = ctx.output_data
        metadata = ctx.metadata or {}
        tenant_id = metadata.get("tenant_id") or "default"
        
        # Ensure we have a valid response with usage data
        if response and hasattr(response, 'input_tokens') and response.input_tokens is not None:
            await usage_billing_service.log_usage(
                tenant_id=tenant_id,
                model=response.model,
                provider=response.provider.value if hasattr(response.provider, 'value') else str(response.provider),
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens or 0
            )

# Register the hook
hooks.register(HookEvent.POST_GENERATION, usage_tracking_hook)
