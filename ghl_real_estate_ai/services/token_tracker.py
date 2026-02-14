"""
Token Tracker - Monitor Progressive Skills Performance
Tracks token usage, cost savings, and efficiency improvements.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis.asyncio as redis

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class TokenTracker:
    """
    Track token usage for progressive skills optimization.
    Monitors the validated 68% token reduction and cost savings.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize with Redis connection for tracking storage"""
        self.redis_url = redis_url
        self._redis = None

    async def _get_redis(self):
        """Lazy Redis connection"""
        if self._redis is None:
            try:
                self._redis = await redis.from_url(self.redis_url)
                await self._redis.ping()
                logger.info("Token tracker connected to Redis")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self._redis = None
        return self._redis

    async def record_usage(
        self,
        task_id: str,
        tokens_used: int,
        task_type: str,
        user_id: str,
        model: str,
        approach: str = "progressive",
        skill_name: Optional[str] = None,
        confidence: Optional[float] = None,
    ):
        """
        Record detailed token usage for analysis

        Args:
            task_id: Unique identifier for this task
            tokens_used: Total tokens consumed
            task_type: Type of task (e.g., "jorge_qualification", "skill_discovery")
            user_id: Lead/user identifier
            model: Model used (e.g., "claude-opus")
            approach: "progressive" or "current" for A/B testing
            skill_name: Which skill was used (for progressive approach)
            confidence: Confidence score from skill execution
        """

        redis_client = await self._get_redis()
        if not redis_client:
            logger.warning("Redis not available, token tracking disabled")
            return

        usage_data = {
            "task_id": task_id,
            "tokens_used": tokens_used,
            "task_type": task_type,
            "user_id": user_id,
            "model": model,
            "approach": approach,
            "skill_name": skill_name,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "cost_estimate": self._calculate_cost(tokens_used, model),
        }

        try:
            # Store detailed record (keep for 7 days)
            await redis_client.set(f"token_usage:{task_id}", json.dumps(usage_data), ex=86400 * 7)

            # Update daily aggregates
            date_key = datetime.now().strftime("%Y-%m-%d")

            # Aggregate by approach (progressive vs current)
            await redis_client.incr(f"daily_tokens:{date_key}:{approach}", tokens_used)
            await redis_client.incr(f"daily_interactions:{date_key}:{approach}", 1)

            # Aggregate by task type
            await redis_client.incr(f"daily_tokens_by_type:{date_key}:{task_type}", tokens_used)

            # Aggregate by skill (for progressive approach)
            if approach == "progressive" and skill_name:
                await redis_client.incr(f"daily_tokens_by_skill:{date_key}:{skill_name}", tokens_used)

            # Track cost
            cost = self._calculate_cost(tokens_used, model)
            await redis_client.incrbyfloat(f"daily_cost:{date_key}:{approach}", cost)

            logger.debug(f"Token usage recorded: {task_id} - {tokens_used} tokens ({approach})")

        except Exception as e:
            logger.error(f"Failed to record token usage: {e}")

    def _calculate_cost(self, tokens: int, model: str) -> float:
        """Calculate cost based on token usage and model"""

        # Claude pricing (approximate)
        pricing = {
            "claude-opus": {"input": 15.00 / 1_000_000, "output": 75.00 / 1_000_000},
            "claude-sonnet": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
            "claude-haiku": {"input": 0.25 / 1_000_000, "output": 1.25 / 1_000_000},
        }

        # Default to sonnet pricing
        model_key = "claude-sonnet"
        if "opus" in model.lower():
            model_key = "claude-opus"
        elif "haiku" in model.lower():
            model_key = "claude-haiku"

        # Estimate 80% input, 20% output tokens
        input_tokens = int(tokens * 0.8)
        output_tokens = int(tokens * 0.2)

        cost = input_tokens * pricing[model_key]["input"] + output_tokens * pricing[model_key]["output"]

        return cost

    async def get_efficiency_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate token efficiency comparison report

        Args:
            days: Number of days to analyze

        Returns:
            Comprehensive efficiency report
        """

        redis_client = await self._get_redis()
        if not redis_client:
            return {"error": "Redis not available for reporting"}

        report = {
            "period_days": days,
            "analysis_date": datetime.now().isoformat(),
            "daily_trends": [],
            "summary": {},
            "skill_breakdown": {},
            "recommendations": [],
        }

        total_current_tokens = 0
        total_progressive_tokens = 0
        total_current_cost = 0
        total_progressive_cost = 0

        # Gather data for each day
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")

            try:
                # Get tokens by approach
                current_tokens = int(await redis_client.get(f"daily_tokens:{date}:current") or 0)
                progressive_tokens = int(await redis_client.get(f"daily_tokens:{date}:progressive") or 0)

                # Get interaction counts
                current_interactions = int(await redis_client.get(f"daily_interactions:{date}:current") or 0)
                progressive_interactions = int(await redis_client.get(f"daily_interactions:{date}:progressive") or 0)

                # Get costs
                current_cost = float(await redis_client.get(f"daily_cost:{date}:current") or 0)
                progressive_cost = float(await redis_client.get(f"daily_cost:{date}:progressive") or 0)

                # Calculate metrics for this day
                day_report = {
                    "date": date,
                    "current_tokens": current_tokens,
                    "progressive_tokens": progressive_tokens,
                    "current_interactions": current_interactions,
                    "progressive_interactions": progressive_interactions,
                    "current_cost": current_cost,
                    "progressive_cost": progressive_cost,
                }

                # Calculate efficiency metrics
                if current_tokens > 0:
                    day_report["token_reduction_percent"] = (
                        (current_tokens - progressive_tokens) / current_tokens
                    ) * 100
                    day_report["cost_reduction_percent"] = ((current_cost - progressive_cost) / current_cost) * 100
                else:
                    day_report["token_reduction_percent"] = 0
                    day_report["cost_reduction_percent"] = 0

                # Average tokens per interaction
                if current_interactions > 0:
                    day_report["avg_tokens_current"] = current_tokens / current_interactions
                if progressive_interactions > 0:
                    day_report["avg_tokens_progressive"] = progressive_tokens / progressive_interactions

                report["daily_trends"].append(day_report)

                # Add to totals
                total_current_tokens += current_tokens
                total_progressive_tokens += progressive_tokens
                total_current_cost += current_cost
                total_progressive_cost += progressive_cost

            except Exception as e:
                logger.error(f"Error gathering data for date {date}: {e}")

        # Calculate summary metrics
        if total_current_tokens > 0:
            report["summary"] = {
                "total_current_tokens": total_current_tokens,
                "total_progressive_tokens": total_progressive_tokens,
                "overall_token_reduction": ((total_current_tokens - total_progressive_tokens) / total_current_tokens)
                * 100,
                "total_current_cost": total_current_cost,
                "total_progressive_cost": total_progressive_cost,
                "overall_cost_reduction": ((total_current_cost - total_progressive_cost) / total_current_cost) * 100,
                "cost_savings": total_current_cost - total_progressive_cost,
                "projected_monthly_savings": (total_current_cost - total_progressive_cost) * (30 / days)
                if days > 0
                else 0,
                "projected_annual_savings": (total_current_cost - total_progressive_cost) * (365 / days)
                if days > 0
                else 0,
            }

            # Validation against research predictions
            research_prediction = 68.1  # Our validated reduction percentage
            actual_reduction = report["summary"]["overall_token_reduction"]

            report["summary"]["research_validation"] = {
                "predicted_reduction": research_prediction,
                "actual_reduction": actual_reduction,
                "accuracy": min(100, (actual_reduction / research_prediction) * 100) if research_prediction > 0 else 0,
            }

        # Get skill-specific breakdown
        try:
            skill_breakdown = await self._get_skill_breakdown(days)
            report["skill_breakdown"] = skill_breakdown
        except Exception as e:
            logger.error(f"Error generating skill breakdown: {e}")

        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)

        return report

    async def _get_skill_breakdown(self, days: int) -> Dict[str, Any]:
        """Get breakdown of token usage by individual skills"""

        redis_client = await self._get_redis()
        if not redis_client:
            return {}

        skill_stats = {}

        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")

            # Get all skill keys for this date
            pattern = f"daily_tokens_by_skill:{date}:*"
            try:
                keys = await redis_client.keys(pattern)

                for key in keys:
                    key_str = key.decode() if isinstance(key, bytes) else str(key)
                    skill_name = key_str.split(":")[-1]  # Extract skill name

                    tokens = int(await redis_client.get(key) or 0)

                    if skill_name not in skill_stats:
                        skill_stats[skill_name] = {"total_tokens": 0, "usage_days": 0, "avg_daily_tokens": 0}

                    skill_stats[skill_name]["total_tokens"] += tokens
                    if tokens > 0:
                        skill_stats[skill_name]["usage_days"] += 1

            except Exception as e:
                logger.error(f"Error getting skill breakdown for {date}: {e}")

        # Calculate averages
        for skill_name, stats in skill_stats.items():
            if stats["usage_days"] > 0:
                stats["avg_daily_tokens"] = stats["total_tokens"] / stats["usage_days"]

        return skill_stats

    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on performance data"""

        recommendations = []
        summary = report.get("summary", {})

        if not summary:
            return ["Insufficient data for recommendations"]

        token_reduction = summary.get("overall_token_reduction", 0)
        cost_savings = summary.get("cost_savings", 0)
        research_accuracy = summary.get("research_validation", {}).get("accuracy", 0)

        # Token efficiency recommendations
        if token_reduction > 60:
            recommendations.append(
                f"✅ Excellent token reduction ({token_reduction:.1f}%) - consider scaling to other bots"
            )
        elif token_reduction > 40:
            recommendations.append(
                f"⚠️ Moderate token reduction ({token_reduction:.1f}%) - investigate skill selection logic"
            )
        else:
            recommendations.append(f"❌ Low token reduction ({token_reduction:.1f}%) - review skill implementation")

        # Cost impact recommendations
        if cost_savings > 50:  # $50+ daily savings
            recommendations.append(f"💰 Significant cost savings (${cost_savings:.2f}) - ROI validated")
        elif cost_savings > 10:
            recommendations.append(f"💵 Moderate cost savings (${cost_savings:.2f}) - positive ROI")

        # Research validation
        if research_accuracy > 80:
            recommendations.append(f"🎯 Research validation excellent ({research_accuracy:.1f}%) - findings confirmed")
        elif research_accuracy > 60:
            recommendations.append(f"📊 Research validation good ({research_accuracy:.1f}%) - mostly accurate")
        else:
            recommendations.append(f"🔍 Research validation low ({research_accuracy:.1f}%) - investigate discrepancies")

        # Operational recommendations
        monthly_savings = summary.get("projected_monthly_savings", 0)
        if monthly_savings > 100:
            recommendations.append(
                f"🚀 Scale to all bots immediately - projected monthly savings: ${monthly_savings:.2f}"
            )

        return recommendations

    async def get_realtime_dashboard(self) -> Dict[str, Any]:
        """Get real-time performance dashboard data"""

        redis_client = await self._get_redis()
        if not redis_client:
            return {"error": "Redis not available"}

        today = datetime.now().strftime("%Y-%m-%d")

        try:
            # Current hour's data
            datetime.now().replace(minute=0, second=0, microsecond=0)

            # Get today's totals
            progressive_tokens_today = int(await redis_client.get(f"daily_tokens:{today}:progressive") or 0)
            current_tokens_today = int(await redis_client.get(f"daily_tokens:{today}:current") or 0)

            progressive_interactions_today = int(await redis_client.get(f"daily_interactions:{today}:progressive") or 0)
            current_interactions_today = int(await redis_client.get(f"daily_interactions:{today}:current") or 0)

            # Calculate efficiency
            efficiency = 0
            if current_tokens_today > 0:
                efficiency = ((current_tokens_today - progressive_tokens_today) / current_tokens_today) * 100

            return {
                "date": today,
                "realtime_metrics": {
                    "progressive_tokens_today": progressive_tokens_today,
                    "current_tokens_today": current_tokens_today,
                    "progressive_interactions_today": progressive_interactions_today,
                    "current_interactions_today": current_interactions_today,
                    "efficiency_percent": efficiency,
                    "avg_tokens_progressive": progressive_tokens_today / progressive_interactions_today
                    if progressive_interactions_today > 0
                    else 0,
                    "avg_tokens_current": current_tokens_today / current_interactions_today
                    if current_interactions_today > 0
                    else 0,
                },
                "status": "operational" if efficiency > 0 else "insufficient_data",
            }

        except Exception as e:
            logger.error(f"Error generating realtime dashboard: {e}")
            return {"error": str(e)}


# Global instance for easy import
_token_tracker = None


def get_token_tracker() -> TokenTracker:
    """Get singleton token tracker instance"""
    global _token_tracker
    if _token_tracker is None:
        _token_tracker = TokenTracker()
    return _token_tracker
