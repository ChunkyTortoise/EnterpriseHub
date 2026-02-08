import csv
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# Constants
CSV_FILE = "gemini_metrics.csv"


def init_logging():
    """Initialize CSV file with headers if it doesn't exist."""
    if not os.path.exists(CSV_FILE):
        try:
            with open(CSV_FILE, "w", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "timestamp",
                        "model",
                        "provider",
                        "task_type",
                        "input_tokens",
                        "output_tokens",
                        "cache_creation_input_tokens",
                        "cache_read_input_tokens",
                        "total_tokens",
                        "cost_usd",
                        "accuracy_score",
                        "tenant_id",
                        "is_failover",
                    ],
                )
                writer.writeheader()
            logger.info(f"Initialized metrics log: {CSV_FILE}")
        except Exception as e:
            logger.error(f"Failed to initialize metrics log: {e}")


def calculate_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> float:
    """
    Calculate cost based on provider, model, and token counts.
    Rates updated as of Jan 2026.
    Includes Anthropic Prompt Caching rates:
    - Standard Input: $3.00 / MTok
    - Cache Write (Creation): $3.75 / MTok (1.25x)
    - Cache Read (Hit): $0.30 / MTok (0.10x)
    """
    # Default rates (can be moved to config/settings)
    rates = {
        "gemini": {
            "gemini-2.5-flash": {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000},
            "gemini-2.0-flash": {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000},
            "gemini-2.0-pro": {"input": 1.50 / 1_000_000, "output": 6.00 / 1_000_000},
            "gemini-1.5-flash": {"input": 0.075 / 1_000_000, "output": 0.30 / 1_000_000},
            "gemini-1.5-pro": {"input": 1.25 / 1_000_000, "output": 5.00 / 1_000_000},
            "default": {"input": 0.125 / 1_000_000, "output": 0.375 / 1_000_000},
        },
        "claude": {
            "claude-sonnet-4-5-20250514": {
                "input": 3.0 / 1_000_000,
                "output": 15.0 / 1_000_000,
                "cache_write": 3.75 / 1_000_000,
                "cache_read": 0.30 / 1_000_000,
            },
            "claude-opus-4-5-20251101": {
                "input": 15.0 / 1_000_000,
                "output": 75.0 / 1_000_000,
                "cache_write": 18.75 / 1_000_000,
                "cache_read": 1.50 / 1_000_000,
            },
            "claude-3-5-sonnet-20241022": {
                "input": 3.0 / 1_000_000,
                "output": 15.0 / 1_000_000,
                "cache_write": 3.75 / 1_000_000,
                "cache_read": 0.30 / 1_000_000,
            },
            "claude-3-5-sonnet-latest": {
                "input": 3.0 / 1_000_000,
                "output": 15.0 / 1_000_000,
                "cache_write": 3.75 / 1_000_000,
                "cache_read": 0.30 / 1_000_000,
            },
            "claude-3-5-haiku-latest": {
                "input": 0.80 / 1_000_000,
                "output": 4.00 / 1_000_000,
                "cache_write": 1.00 / 1_000_000,
                "cache_read": 0.08 / 1_000_000,
            },
            "claude-3-haiku-20240307": {"input": 0.25 / 1_000_000, "output": 1.25 / 1_000_000},
            "default": {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
        },
    }

    provider_rates = rates.get(provider.lower(), rates["gemini"])
    model_rate = provider_rates.get(model, provider_rates.get("default"))

    # Base input (excluding tokens that were cached or creating cache)
    base_input_tokens = max(0, input_tokens - cache_creation_tokens - cache_read_tokens)

    cost = base_input_tokens * model_rate.get("input", 0)
    cost += output_tokens * model_rate.get("output", 0)

    # Add caching costs if available for the model
    if cache_creation_tokens > 0:
        cost += cache_creation_tokens * model_rate.get("cache_write", model_rate.get("input", 0) * 1.25)

    if cache_read_tokens > 0:
        cost += cache_read_tokens * model_rate.get("cache_read", model_rate.get("input", 0) * 0.10)

    return cost


def log_metrics(
    provider: str,
    model: str,
    input_tokens: Optional[int],
    output_tokens: Optional[int],
    task_type: str = "general",
    accuracy_score: Optional[float] = None,
    tenant_id: Optional[str] = None,
    is_failover: bool = False,
    cache_creation_input_tokens: int = 0,
    cache_read_input_tokens: int = 0,
):
    """
    Log metrics for an LLM API call.
    """
    input_tokens = input_tokens or 0
    output_tokens = output_tokens or 0
    total_tokens = input_tokens + output_tokens

    cost = calculate_cost(
        provider,
        model,
        input_tokens,
        output_tokens,
        cache_creation_tokens=cache_creation_input_tokens,
        cache_read_tokens=cache_read_input_tokens,
    )

    entry = {
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "provider": provider,
        "task_type": task_type,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_creation_input_tokens": cache_creation_input_tokens,
        "cache_read_input_tokens": cache_read_input_tokens,
        "total_tokens": total_tokens,
        "cost_usd": round(cost, 6),
        "accuracy_score": accuracy_score if accuracy_score is not None else "N/A",
        "tenant_id": tenant_id or "system",
        "is_failover": is_failover,
    }

    try:
        init_logging()
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "timestamp",
                    "model",
                    "provider",
                    "task_type",
                    "input_tokens",
                    "output_tokens",
                    "cache_creation_input_tokens",
                    "cache_read_input_tokens",
                    "total_tokens",
                    "cost_usd",
                    "accuracy_score",
                    "tenant_id",
                    "is_failover",
                ],
            )
            writer.writerow(entry)
    except Exception as e:
        logger.error(f"Failed to log metrics: {e}")


def get_metrics_summary():
    """Print summary of API usage."""
    if not os.path.exists(CSV_FILE):
        return {"total_cost": 0.0, "tasks": {}}

    total_cost = 0.0
    task_breakdown = {}

    try:
        with open(CSV_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cost = float(row.get("cost_usd", 0))
                task = row.get("task_type", "general")
                total_cost += cost
                task_breakdown[task] = task_breakdown.get(task, 0) + cost
    except Exception as e:
        logger.error(f"Error reading metrics: {e}")

    return {"total_cost": round(total_cost, 4), "tasks": {k: round(v, 4) for k, v in task_breakdown.items()}}


# Register lifecycle hook for automatic logging
try:
    from ghl_real_estate_ai.core.hooks import HookContext, HookEvent, hooks

    def on_generation_complete(ctx: HookContext):
        if ctx.agent_name == "LLMClient" and ctx.output_data:
            res = ctx.output_data
            log_metrics(
                provider=res.provider.value if hasattr(res.provider, "value") else str(res.provider),
                model=res.model,
                input_tokens=res.input_tokens,
                output_tokens=res.output_tokens,
                tenant_id=ctx.metadata.get("tenant_id") if ctx.metadata else None,
                is_failover=ctx.metadata.get("is_failover", False) if ctx.metadata else False,
                cache_creation_input_tokens=getattr(res, "cache_creation_input_tokens", 0) or 0,
                cache_read_input_tokens=getattr(res, "cache_read_input_tokens", 0) or 0,
            )

    hooks.register(HookEvent.POST_GENERATION, on_generation_complete)
    logger.info("Registered LLM performance tracking hook")
except ImportError:
    pass
