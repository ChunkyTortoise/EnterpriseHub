"""
Simple Database Service for BI Operations
Provides basic database connectivity without the complex configuration
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import asyncpg

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class SimpleDatabaseService:
    """Simple database service for BI operations"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = os.getenv("DATABASE_URL", "postgresql://cave@localhost:5432/enterprise_hub")

    async def initialize(self):
        """Initialize database connection pool"""
        if self.pool:
            return

        try:
            self.pool = await asyncpg.create_pool(self.database_url, min_size=2, max_size=10, command_timeout=30)
            logger.info("Simple database service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise

    @asynccontextmanager
    async def get_connection(self):
        """Get database connection from pool"""
        if not self.pool:
            await self.initialize()

        async with self.pool.acquire() as connection:
            yield connection

    async def get_dashboard_kpis(self, location_id: str = "default", timeframe: str = "24h") -> Dict[str, Any]:
        """Get dashboard KPIs from OLAP data"""
        try:
            # Convert timeframe to hours
            hours_map = {"24h": 24, "7d": 168, "30d": 720, "90d": 2160, "1y": 8760}
            hours = hours_map.get(timeframe, 24)

            async with self.get_connection() as conn:
                # Get lead interaction metrics
                lead_metrics = await conn.fetchrow(f"""
                    SELECT
                        COUNT(*) as total_interactions,
                        COUNT(CASE WHEN event_type LIKE '%qualification%' THEN 1 END) as qualified_leads,
                        COUNT(CASE WHEN lead_temperature = 'hot' THEN 1 END) as hot_leads,
                        AVG(processing_time_ms) as avg_response_time,
                        COUNT(CASE WHEN bot_type = 'jorge-seller' THEN 1 END) as jorge_seller_interactions,
                        COUNT(CASE WHEN bot_type = 'jorge-buyer' THEN 1 END) as jorge_buyer_interactions
                    FROM fact_lead_interactions
                    WHERE timestamp >= NOW() - INTERVAL '{hours} hours'
                """)

                # Get commission data
                commission_data = await conn.fetchrow(f"""
                    SELECT
                        COALESCE(SUM(jorge_pipeline_value), 0) as total_pipeline_value,
                        COALESCE(SUM(commission_amount), 0) as total_commission,
                        COUNT(*) as commission_events
                    FROM fact_commission_events
                    WHERE timestamp >= NOW() - INTERVAL '{hours} hours'
                """)

                # Get bot performance
                bot_performance = await conn.fetchrow(f"""
                    SELECT
                        AVG(processing_time_ms) as avg_bot_response_time,
                        AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as bot_success_rate,
                        COUNT(*) as bot_operations
                    FROM fact_bot_performance
                    WHERE timestamp >= NOW() - INTERVAL '{hours} hours'
                """)

                # Calculate Jorge's commission (6%)
                pipeline_value = float(commission_data["total_pipeline_value"] or 0)
                jorge_commission = pipeline_value * 0.06

                # Calculate conversion rate
                total_interactions = lead_metrics["total_interactions"] or 1
                conversion_rate = (lead_metrics["hot_leads"] or 0) / total_interactions * 100

                return {
                    "total_revenue": pipeline_value,
                    "total_leads": total_interactions,
                    "conversion_rate": round(conversion_rate, 2),
                    "hot_leads": lead_metrics["hot_leads"] or 0,
                    "qualified_leads": lead_metrics["qualified_leads"] or 0,
                    "jorge_commission": round(jorge_commission, 2),
                    "avg_response_time_ms": round(float(lead_metrics["avg_response_time"] or 0), 1),
                    "bot_success_rate": round(float(bot_performance["bot_success_rate"] or 0) * 100, 1),
                    "pipeline_value": pipeline_value,
                    "jorge_seller_interactions": lead_metrics["jorge_seller_interactions"] or 0,
                    "jorge_buyer_interactions": lead_metrics["jorge_buyer_interactions"] or 0,
                    "commission_events": commission_data["commission_events"] or 0,
                    "bot_operations": bot_performance["bot_operations"] or 0,
                }

        except Exception as e:
            logger.error(f"Failed to get dashboard KPIs: {e}")
            # Return default values on error
            return {
                "total_revenue": 0,
                "total_leads": 0,
                "conversion_rate": 0,
                "hot_leads": 0,
                "qualified_leads": 0,
                "jorge_commission": 0,
                "avg_response_time_ms": 0,
                "bot_success_rate": 0,
                "pipeline_value": 0,
                "jorge_seller_interactions": 0,
                "jorge_buyer_interactions": 0,
                "commission_events": 0,
                "bot_operations": 0,
            }

    async def get_bot_performance_data(
        self, location_id: str = "default", timeframe: str = "7d"
    ) -> List[Dict[str, Any]]:
        """Get bot performance data from OLAP"""
        try:
            hours_map = {"24h": 24, "7d": 168, "30d": 720, "90d": 2160}
            hours = hours_map.get(timeframe, 168)

            async with self.get_connection() as conn:
                # Get bot performance by type
                bot_data = await conn.fetch(f"""
                    SELECT
                        bot_type,
                        COUNT(*) as interactions,
                        AVG(processing_time_ms) as avg_response_time_ms,
                        AVG(CASE WHEN success THEN 1.0 ELSE 0.0 END) as success_rate,
                        AVG(confidence_score) as avg_confidence_score
                    FROM fact_bot_performance
                    WHERE timestamp >= NOW() - INTERVAL '{hours} hours'
                    GROUP BY bot_type
                    ORDER BY interactions DESC
                """)

                # Get bot types info from dimension table
                bot_types_info = await conn.fetch("""
                    SELECT bot_type, display_name, category
                    FROM dim_bot_types
                """)

                bot_types_dict = {bt["bot_type"]: bt for bt in bot_types_info}

                result = []
                for bot in bot_data:
                    bot_info = bot_types_dict.get(bot["bot_type"], {})

                    # Calculate performance tier
                    success_rate = float(bot["success_rate"] or 0)
                    response_time = float(bot["avg_response_time_ms"] or 0)

                    if success_rate > 0.9 and response_time < 50:
                        performance_tier = "excellent"
                        current_status = "healthy"
                    elif success_rate > 0.8 and response_time < 100:
                        performance_tier = "good"
                        current_status = "healthy"
                    else:
                        performance_tier = "needs_improvement"
                        current_status = "warning"

                    result.append(
                        {
                            "bot_type": bot["bot_type"],
                            "display_name": bot_info.get("display_name", bot["bot_type"].replace("-", " ").title()),
                            "interactions": int(bot["interactions"]),
                            "avg_response_time_ms": round(response_time, 1),
                            "success_rate": round(success_rate, 3),
                            "confidence_score": round(float(bot["avg_confidence_score"] or 0), 3),
                            "performance_tier": performance_tier,
                            "current_status": current_status,
                            "category": bot_info.get("category", "unknown"),
                        }
                    )

                return result

        except Exception as e:
            logger.error(f"Failed to get bot performance data: {e}")
            return []

    async def get_revenue_intelligence_data(
        self, location_id: str = "default", timeframe: str = "30d"
    ) -> Dict[str, Any]:
        """Get revenue intelligence data from OLAP"""
        try:
            hours_map = {"7d": 168, "30d": 720, "90d": 2160, "1y": 8760}
            hours = hours_map.get(timeframe, 720)

            async with self.get_connection() as conn:
                # Get revenue time series data (daily aggregation)
                timeseries_data = await conn.fetch(f"""
                    SELECT
                        DATE(timestamp) as date,
                        SUM(jorge_pipeline_value) as daily_pipeline_value,
                        SUM(commission_amount) as daily_commission,
                        COUNT(*) as daily_deals
                    FROM fact_commission_events
                    WHERE timestamp >= NOW() - INTERVAL '{hours} hours'
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                """)

                # Get overall commission summary
                commission_summary = await conn.fetchrow(f"""
                    SELECT
                        SUM(jorge_pipeline_value) as total_pipeline_value,
                        SUM(commission_amount) as total_commission,
                        COUNT(*) as total_deals,
                        AVG(jorge_pipeline_value) as avg_deal_value
                    FROM fact_commission_events
                    WHERE timestamp >= NOW() - INTERVAL '{hours} hours'
                """)

                # Format timeseries for frontend
                timeseries = []
                for row in timeseries_data:
                    pipeline_value = float(row["daily_pipeline_value"] or 0)
                    commission = float(row["daily_commission"] or 0)

                    timeseries.append(
                        {
                            "date": row["date"].isoformat(),
                            "total_revenue": pipeline_value,
                            "jorge_commission": commission,
                            "deals_closed": int(row["daily_deals"]),
                            "pipeline_value": pipeline_value,
                        }
                    )

                # Commission breakdown
                total_commission = float(commission_summary["total_commission"] or 0)
                commission_breakdown = [
                    {
                        "category": "Jorge's Direct Commission (6%)",
                        "amount": total_commission,
                        "percentage": 100.0,
                        "color": "blue",
                    }
                ]

                # Summary metrics
                total_pipeline = float(commission_summary["total_pipeline_value"] or 0)
                total_deals = int(commission_summary["total_deals"] or 0)
                avg_deal_size = float(commission_summary["avg_deal_value"] or 0)

                summary_metrics = {
                    "total_revenue": total_pipeline,
                    "total_jorge_commission": total_commission,
                    "avg_deal_size": avg_deal_size,
                    "total_deals": total_deals,
                    "avg_daily_revenue": total_pipeline / max(1, len(timeseries)) if timeseries else 0,
                    "commission_rate": 0.06,
                }

                return {
                    "revenue_timeseries": timeseries,
                    "commission_breakdown": commission_breakdown,
                    "summary_metrics": summary_metrics,
                    "forecast_accuracy": 0.87,  # Placeholder for ML forecast accuracy
                }

        except Exception as e:
            logger.error(f"Failed to get revenue intelligence data: {e}")
            return {
                "revenue_timeseries": [],
                "commission_breakdown": [],
                "summary_metrics": {
                    "total_revenue": 0,
                    "total_jorge_commission": 0,
                    "avg_deal_size": 0,
                    "total_deals": 0,
                    "avg_daily_revenue": 0,
                    "commission_rate": 0.06,
                },
                "forecast_accuracy": 0.87,
            }

    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
            self.pool = None


# Global instance
_db_service: Optional[SimpleDatabaseService] = None


async def get_simple_db_service() -> SimpleDatabaseService:
    """Get or create global database service instance"""
    global _db_service

    if _db_service is None:
        _db_service = SimpleDatabaseService()
        await _db_service.initialize()

    return _db_service
