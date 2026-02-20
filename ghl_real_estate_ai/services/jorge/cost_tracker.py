"""API cost tracker -- logs token usage per conversation to Postgres."""
from __future__ import annotations

import logging
from typing import Optional

from ghl_real_estate_ai.core.llm_client import LLMResponse
from ghl_real_estate_ai.database.connection_manager import get_db_manager

logger = logging.getLogger(__name__)

PRICING_INPUT_PER_MTOK = 3.00  # USD per million input tokens
PRICING_OUTPUT_PER_MTOK = 15.00  # USD per million output tokens
PRICING_CACHE_READ_PER_MTOK = 0.30  # 10% of input


def _calculate_cost(
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
) -> float:
    """Calculate estimated USD cost from token counts."""
    return (
        input_tokens * PRICING_INPUT_PER_MTOK / 1_000_000
        + output_tokens * PRICING_OUTPUT_PER_MTOK / 1_000_000
        + cache_read_tokens * PRICING_CACHE_READ_PER_MTOK / 1_000_000
    )


class CostTracker:
    """Fire-and-forget cost logger backed by the llm_cost_log table."""

    async def record_usage(
        self,
        conversation_id: str,
        contact_id: Optional[str],
        bot_type: str,
        response: LLMResponse,
        model: str = "claude-3-5-sonnet",
    ) -> None:
        """Insert a cost record. Never raises -- logs errors and returns."""
        try:
            input_tok = response.input_tokens or 0
            output_tok = response.output_tokens or 0
            cache_creation = response.cache_creation_input_tokens or 0
            cache_read = response.cache_read_input_tokens or 0
            cost = _calculate_cost(input_tok, output_tok, cache_read)
            model_name = response.model or model

            db = await get_db_manager()
            await db.execute_command(
                """
                INSERT INTO llm_cost_log
                    (conversation_id, contact_id, bot_type, model,
                     input_tokens, output_tokens,
                     cache_creation_tokens, cache_read_tokens,
                     estimated_cost_usd)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                conversation_id,
                contact_id,
                bot_type,
                model_name,
                input_tok,
                output_tok,
                cache_creation,
                cache_read,
                cost,
            )
        except Exception:
            logger.exception("cost_tracker.record_usage failed")

    async def record_from_response(
        self,
        conversation_id: str,
        contact_id: Optional[str],
        bot_type: str,
        llm_response: LLMResponse,
    ) -> None:
        """Convenience wrapper around record_usage."""
        await self.record_usage(conversation_id, contact_id, bot_type, llm_response)

    async def record_bot_call(
        self,
        conversation_id: str,
        contact_id: Optional[str],
        bot_type: str,
        model: str = "claude-3-5-sonnet",
    ) -> None:
        """Record a bot API call without detailed token info.

        Useful when LLMResponse is not directly accessible (e.g. from
        the bot process_* methods where the workflow consumes tokens
        internally).  Inserts a row with zero tokens so call counts are
        still tracked.
        """
        try:
            db = await get_db_manager()
            await db.execute_command(
                """
                INSERT INTO llm_cost_log
                    (conversation_id, contact_id, bot_type, model,
                     input_tokens, output_tokens,
                     cache_creation_tokens, cache_read_tokens,
                     estimated_cost_usd)
                VALUES ($1, $2, $3, $4, 0, 0, 0, 0, 0)
                """,
                conversation_id,
                contact_id,
                bot_type,
                model,
            )
        except Exception:
            logger.exception("cost_tracker.record_bot_call failed")

    async def get_month_total(self, year: int, month: int) -> dict:
        """Return aggregate stats for a calendar month.

        Returns dict with keys: input_tokens, output_tokens, cost_usd, call_count.
        """
        try:
            db = await get_db_manager()
            row = await db.execute_fetchrow(
                """
                SELECT
                    COALESCE(SUM(input_tokens), 0)  AS input_tokens,
                    COALESCE(SUM(output_tokens), 0) AS output_tokens,
                    COALESCE(SUM(estimated_cost_usd), 0)::float AS cost_usd,
                    COUNT(*)::int AS call_count
                FROM llm_cost_log
                WHERE EXTRACT(YEAR FROM created_at) = $1
                  AND EXTRACT(MONTH FROM created_at) = $2
                """,
                year,
                month,
            )
            if row:
                return {
                    "input_tokens": int(row["input_tokens"]),
                    "output_tokens": int(row["output_tokens"]),
                    "cost_usd": float(row["cost_usd"]),
                    "call_count": int(row["call_count"]),
                }
        except Exception:
            logger.exception("cost_tracker.get_month_total failed")

        return {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "call_count": 0}

    async def get_conversation_cost(self, conversation_id: str) -> float:
        """Return total estimated cost for a single conversation."""
        try:
            db = await get_db_manager()
            val = await db.execute_fetchval(
                """
                SELECT COALESCE(SUM(estimated_cost_usd), 0)::float
                FROM llm_cost_log
                WHERE conversation_id = $1
                """,
                conversation_id,
            )
            return float(val) if val is not None else 0.0
        except Exception:
            logger.exception("cost_tracker.get_conversation_cost failed")
            return 0.0

    async def get_top_contacts_by_cost(self, limit: int = 10) -> list:
        """Return contacts ranked by total estimated cost (descending)."""
        try:
            db = await get_db_manager()
            rows = await db.execute_query(
                """
                SELECT
                    contact_id,
                    COALESCE(SUM(estimated_cost_usd), 0)::float AS total_cost,
                    COUNT(*)::int AS call_count
                FROM llm_cost_log
                WHERE contact_id IS NOT NULL
                GROUP BY contact_id
                ORDER BY total_cost DESC
                LIMIT $1
                """,
                limit,
            )
            return [
                {
                    "contact_id": r["contact_id"],
                    "total_cost": float(r["total_cost"]),
                    "call_count": int(r["call_count"]),
                }
                for r in rows
            ]
        except Exception:
            logger.exception("cost_tracker.get_top_contacts_by_cost failed")
            return []


cost_tracker = CostTracker()
