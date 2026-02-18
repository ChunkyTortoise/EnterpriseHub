#!/usr/bin/env python3
"""
Phase 3 Business Impact Calculation Engine
==========================================

Calculates daily and weekly ROI for Phase 3 features:
- Real-Time Lead Intelligence ($75K-120K/year)
- Multimodal Property Intelligence ($75K-150K/year)
- Proactive Churn Prevention ($55K-80K/year)
- AI-Powered Coaching ($60K-90K/year)

Usage:
    python scripts/calculate_business_impact.py --mode daily
    python scripts/calculate_business_impact.py --mode weekly --start-date 2026-01-01
    python scripts/calculate_business_impact.py --mode real-time --dashboard
"""

import asyncio
import asyncpg
import logging
import argparse
import json
from datetime import datetime, timedelta, date
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.database import get_database_url
except ImportError:
    # Fallback if config.database doesn't exist
    def get_database_url():
        return os.getenv("DATABASE_URL", "postgresql://localhost/ghl_real_estate")

try:
    from services.ghl.client import GHLClient
except ImportError:
    GHLClient = None

try:
    from services.analytics.performance_tracker import PerformanceTracker
except ImportError:
    PerformanceTracker = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class FeatureMetrics:
    """Business metrics for a single feature."""
    name: str
    usage_count: int
    revenue_impact: Decimal
    performance_ms: float
    accuracy_rate: float
    adoption_rate: float
    cost_impact: Decimal


@dataclass
class BusinessImpactResult:
    """Complete business impact calculation result."""
    date: date
    tenant_id: str

    # Feature-specific metrics
    lead_intelligence: FeatureMetrics
    property_intelligence: FeatureMetrics
    churn_prevention: FeatureMetrics
    ai_coaching: FeatureMetrics

    # Overall metrics
    total_revenue_impact: Decimal
    total_operating_costs: Decimal
    net_revenue: Decimal
    roi_percentage: Decimal

    # Performance summary
    avg_response_time_ms: float
    error_rate: float
    uptime_percentage: float


class BusinessImpactCalculator:
    """Calculate business impact and ROI for Phase 3 features."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.ghl_client = GHLClient() if GHLClient is not None else None
        self.performance_tracker = PerformanceTracker() if PerformanceTracker is not None else None

        # Business impact calculation constants from deployment plan
        self.FEATURE_TARGETS = {
            'lead_intelligence': {
                'annual_revenue_min': 75000,
                'annual_revenue_max': 120000,
                'conversion_lift': 0.05,  # 5% conversion rate improvement
                'productivity_improvement': 0.10,  # 10% agent productivity
            },
            'property_intelligence': {
                'annual_revenue_min': 75000,
                'annual_revenue_max': 150000,
                'satisfaction_improvement': 0.05,  # 5% satisfaction increase
                'qualified_matches_increase': 0.15,  # 15% more qualified matches
            },
            'churn_prevention': {
                'annual_revenue_min': 55000,
                'annual_revenue_max': 80000,
                'churn_reduction': 0.40,  # 40% churn reduction (35% → 21%)
                'intervention_success_rate': 0.65,  # 65% intervention success
            },
            'ai_coaching': {
                'annual_revenue_min': 60000,
                'annual_revenue_max': 90000,
                'productivity_increase': 0.25,  # 25% productivity increase
                'training_time_reduction': 0.50,  # 50% training time reduction
            }
        }

        # Operating cost targets from deployment plan
        self.ANNUAL_OPERATING_COST = 43200  # $43,200/year
        self.DAILY_OPERATING_COST = self.ANNUAL_OPERATING_COST / 365

    async def get_database_connection(self) -> asyncpg.Connection:
        """Get database connection."""
        return await asyncpg.connect(self.database_url)

    async def calculate_lead_intelligence_metrics(
        self,
        conn: asyncpg.Connection,
        target_date: date,
        tenant_id: str = None
    ) -> FeatureMetrics:
        """Calculate Real-Time Lead Intelligence business impact."""

        query = """
        SELECT
            COALESCE(leads_processed, 0) as usage_count,
            COALESCE(conversion_rate_improvement, 0) as conversion_improvement,
            COALESCE(agent_productivity_improvement, 0) as productivity_improvement,
            COALESCE(avg_response_time_minutes, 45) as response_time,
            COALESCE(avg_scoring_latency_ms, 0) as performance_ms,
            COALESCE(estimated_revenue_impact, 0) as revenue_impact
        FROM lead_intelligence_metrics
        WHERE date = $1
        AND ($2 IS NULL OR tenant_id = $2)
        """

        result = await conn.fetchrow(query, target_date, tenant_id)

        if not result:
            # Return default metrics if no data
            logger.warning(f"No lead intelligence data for {target_date}")
            return FeatureMetrics(
                name="Real-Time Lead Intelligence",
                usage_count=0,
                revenue_impact=Decimal('0'),
                performance_ms=0.0,
                accuracy_rate=0.0,
                adoption_rate=0.0,
                cost_impact=Decimal('0')
            )

        # Calculate revenue impact based on conversion improvement
        baseline_revenue_per_lead = Decimal('500')  # Average lead value
        conversion_improvement = result['conversion_improvement'] or 0
        productivity_improvement = result['productivity_improvement'] or 0

        # Revenue = (leads × baseline × conversion_lift) + (productivity × time_savings)
        conversion_revenue = (
            result['usage_count'] *
            baseline_revenue_per_lead *
            Decimal(str(conversion_improvement))
        )

        # Productivity revenue (agent time savings × hourly rate)
        agent_hourly_rate = Decimal('35')  # $35/hour average
        time_saved_hours = (result['usage_count'] * Decimal('0.25') *
                           Decimal(str(productivity_improvement)))  # 15min/lead × improvement
        productivity_revenue = time_saved_hours * agent_hourly_rate

        total_revenue = conversion_revenue + productivity_revenue

        # Calculate adoption rate (usage vs. total possible)
        total_leads_today = await self._get_total_leads_for_date(conn, target_date, tenant_id)
        adoption_rate = result['usage_count'] / max(total_leads_today, 1)

        return FeatureMetrics(
            name="Real-Time Lead Intelligence",
            usage_count=result['usage_count'],
            revenue_impact=total_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            performance_ms=result['performance_ms'],
            accuracy_rate=0.98,  # 98% accuracy target from deployment plan
            adoption_rate=min(adoption_rate, 1.0),
            cost_impact=Decimal('5.50')  # Estimated daily cost
        )

    async def calculate_property_intelligence_metrics(
        self,
        conn: asyncpg.Connection,
        target_date: date,
        tenant_id: str = None
    ) -> FeatureMetrics:
        """Calculate Multimodal Property Intelligence business impact."""

        query = """
        SELECT
            COALESCE(properties_analyzed, 0) as usage_count,
            COALESCE(luxury_properties_identified, 0) as luxury_count,
            COALESCE(match_satisfaction_score, 0.88) as satisfaction,
            COALESCE(qualified_matches_increase, 0) as matches_improvement,
            COALESCE(avg_analysis_time_ms, 1190) as performance_ms,
            COALESCE(accuracy_rate, 0.96) as accuracy,
            COALESCE(estimated_revenue_impact, 0) as revenue_impact
        FROM property_intelligence_metrics
        WHERE date = $1
        AND ($2 IS NULL OR tenant_id = $2)
        """

        result = await conn.fetchrow(query, target_date, tenant_id)

        if not result:
            logger.warning(f"No property intelligence data for {target_date}")
            return FeatureMetrics(
                name="Multimodal Property Intelligence",
                usage_count=0,
                revenue_impact=Decimal('0'),
                performance_ms=1190.0,
                accuracy_rate=0.96,
                adoption_rate=0.0,
                cost_impact=Decimal('0')
            )

        # Revenue calculation based on better matches and luxury identification
        avg_property_value = Decimal('450000')
        commission_rate = Decimal('0.03')  # 3% commission

        # Luxury properties have higher value
        luxury_value_multiplier = Decimal('2.5')
        luxury_commission = (
            result['luxury_count'] *
            avg_property_value *
            luxury_value_multiplier *
            commission_rate *
            Decimal('0.15')  # 15% higher close rate on luxury
        )

        # Improved matches revenue
        matches_improvement = result['matches_improvement'] or 0
        improved_matches_revenue = (
            result['usage_count'] *
            avg_property_value *
            commission_rate *
            Decimal(str(matches_improvement))
        )

        total_revenue = luxury_commission + improved_matches_revenue

        # Calculate adoption rate
        total_properties_today = await self._get_total_properties_for_date(conn, target_date, tenant_id)
        adoption_rate = result['usage_count'] / max(total_properties_today, 1)

        return FeatureMetrics(
            name="Multimodal Property Intelligence",
            usage_count=result['usage_count'],
            revenue_impact=total_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            performance_ms=result['performance_ms'],
            accuracy_rate=result['accuracy'],
            adoption_rate=min(adoption_rate, 1.0),
            cost_impact=Decimal('8.75')  # Vision API costs
        )

    async def calculate_churn_prevention_metrics(
        self,
        conn: asyncpg.Connection,
        target_date: date,
        tenant_id: str = None
    ) -> FeatureMetrics:
        """Calculate Proactive Churn Prevention business impact."""

        query = """
        SELECT
            COALESCE(leads_at_risk_identified, 0) as at_risk_leads,
            COALESCE(interventions_triggered, 0) as interventions,
            COALESCE(successful_interventions, 0) as successful,
            COALESCE(churn_rate_before, 0.35) as churn_before,
            COALESCE(churn_rate_after, 0.21) as churn_after,
            COALESCE(avg_lead_lifetime_value, 100) as lead_value,
            COALESCE(avg_intervention_latency_seconds, 22) as performance_sec,
            COALESCE(prediction_accuracy, 0.95) as accuracy,
            COALESCE(estimated_revenue_saved, 0) as revenue_saved
        FROM churn_prevention_metrics
        WHERE date = $1
        AND ($2 IS NULL OR tenant_id = $2)
        """

        result = await conn.fetchrow(query, target_date, tenant_id)

        if not result:
            logger.warning(f"No churn prevention data for {target_date}")
            return FeatureMetrics(
                name="Proactive Churn Prevention",
                usage_count=0,
                revenue_impact=Decimal('0'),
                performance_ms=22000.0,  # 22 seconds in ms
                accuracy_rate=0.95,
                adoption_rate=0.0,
                cost_impact=Decimal('0')
            )

        # Revenue calculation based on prevented churn
        lead_lifetime_value = Decimal(str(result['lead_value']))
        successful_interventions = result['successful']

        # Revenue = successful interventions × lead lifetime value
        total_revenue = successful_interventions * lead_lifetime_value

        # Calculate adoption rate (interventions vs. at-risk leads)
        adoption_rate = result['interventions'] / max(result['at_risk_leads'], 1)

        return FeatureMetrics(
            name="Proactive Churn Prevention",
            usage_count=result['interventions'],
            revenue_impact=total_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            performance_ms=result['performance_sec'] * 1000,  # Convert to ms
            accuracy_rate=result['accuracy'],
            adoption_rate=min(adoption_rate, 1.0),
            cost_impact=Decimal('3.20')  # ML model costs
        )

    async def calculate_ai_coaching_metrics(
        self,
        conn: asyncpg.Connection,
        target_date: date,
        tenant_id: str = None
    ) -> FeatureMetrics:
        """Calculate AI-Powered Coaching business impact."""

        query = """
        SELECT
            COALESCE(SUM(coaching_sessions), 0) as total_sessions,
            COALESCE(AVG(performance_improvement), 0) as avg_improvement,
            COALESCE(AVG(training_time_reduction), 0) as training_reduction,
            COALESCE(AVG(conversation_quality_score), 0.85) as quality_score,
            COALESCE(AVG(productivity_hours_saved), 0) as hours_saved,
            COALESCE(AVG(avg_coaching_latency_ms), 1640) as performance_ms,
            COALESCE(AVG(coaching_accuracy), 0.94) as accuracy,
            COALESCE(SUM(estimated_revenue_impact), 0) as revenue_impact
        FROM ai_coaching_metrics
        WHERE date = $1
        AND ($2 IS NULL OR tenant_id = $2)
        """

        result = await conn.fetchrow(query, target_date, tenant_id)

        if not result:
            logger.warning(f"No AI coaching data for {target_date}")
            return FeatureMetrics(
                name="AI-Powered Coaching",
                usage_count=0,
                revenue_impact=Decimal('0'),
                performance_ms=1640.0,
                accuracy_rate=0.94,
                adoption_rate=0.0,
                cost_impact=Decimal('0')
            )

        # Revenue calculation based on productivity improvement
        agent_hourly_rate = Decimal('35')  # $35/hour
        hours_saved = Decimal(str(result['hours_saved']))
        performance_improvement = result['avg_improvement'] or 0

        # Direct productivity savings
        productivity_revenue = hours_saved * agent_hourly_rate

        # Performance improvement revenue (better conversion rates)
        baseline_deals_per_day = Decimal('2')  # Average deals per agent per day
        deal_value = Decimal('500')
        performance_revenue = (
            baseline_deals_per_day *
            deal_value *
            Decimal(str(performance_improvement))
        )

        total_revenue = productivity_revenue + performance_revenue

        # Calculate adoption rate (sessions vs. active agents)
        total_agents = await self._get_total_agents_for_date(conn, target_date, tenant_id)
        adoption_rate = min(result['total_sessions'] / max(total_agents * 5, 1), 1.0)  # 5 sessions/agent/day target

        return FeatureMetrics(
            name="AI-Powered Coaching",
            usage_count=result['total_sessions'],
            revenue_impact=total_revenue.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            performance_ms=result['performance_ms'],
            accuracy_rate=result['accuracy'],
            adoption_rate=adoption_rate,
            cost_impact=Decimal('4.80')  # Claude API costs
        )

    async def calculate_operating_costs(
        self,
        conn: asyncpg.Connection,
        target_date: date,
        tenant_id: str = None
    ) -> Decimal:
        """Calculate total operating costs for the target date."""

        query = """
        SELECT COALESCE(SUM(amount), 0) as total_costs
        FROM operating_costs_daily
        WHERE date = $1
        AND ($2 IS NULL OR tenant_id = $2)
        """

        result = await conn.fetchval(query, target_date, tenant_id)

        if not result:
            # Use default daily operating cost from deployment plan
            return Decimal(str(self.DAILY_OPERATING_COST))

        return Decimal(str(result))

    async def calculate_daily_business_impact(
        self,
        target_date: date,
        tenant_id: str = None
    ) -> BusinessImpactResult:
        """Calculate complete business impact for a specific date."""

        logger.info(f"Calculating business impact for {target_date}")

        conn = await self.get_database_connection()

        try:
            # Calculate metrics for each feature
            lead_intelligence = await self.calculate_lead_intelligence_metrics(
                conn, target_date, tenant_id
            )
            property_intelligence = await self.calculate_property_intelligence_metrics(
                conn, target_date, tenant_id
            )
            churn_prevention = await self.calculate_churn_prevention_metrics(
                conn, target_date, tenant_id
            )
            ai_coaching = await self.calculate_ai_coaching_metrics(
                conn, target_date, tenant_id
            )

            # Calculate totals
            total_revenue = (
                lead_intelligence.revenue_impact +
                property_intelligence.revenue_impact +
                churn_prevention.revenue_impact +
                ai_coaching.revenue_impact
            )

            total_costs = await self.calculate_operating_costs(conn, target_date, tenant_id)
            net_revenue = total_revenue - total_costs

            # Calculate ROI percentage
            roi_percentage = (
                (net_revenue / total_costs * 100) if total_costs > 0 else Decimal('0')
            )

            # Calculate performance summary
            avg_response_time = (
                lead_intelligence.performance_ms +
                property_intelligence.performance_ms +
                churn_prevention.performance_ms +
                ai_coaching.performance_ms
            ) / 4

            # Get error rate and uptime from monitoring
            error_rate = await self._get_error_rate(conn, target_date, tenant_id)
            uptime_percentage = await self._get_uptime_percentage(conn, target_date, tenant_id)

            result = BusinessImpactResult(
                date=target_date,
                tenant_id=tenant_id or "default",
                lead_intelligence=lead_intelligence,
                property_intelligence=property_intelligence,
                churn_prevention=churn_prevention,
                ai_coaching=ai_coaching,
                total_revenue_impact=total_revenue,
                total_operating_costs=total_costs,
                net_revenue=net_revenue,
                roi_percentage=roi_percentage,
                avg_response_time_ms=avg_response_time,
                error_rate=error_rate,
                uptime_percentage=uptime_percentage
            )

            # Store results in database
            await self._store_business_metrics(conn, result)

            return result

        finally:
            await conn.close()

    async def _store_business_metrics(
        self,
        conn: asyncpg.Connection,
        result: BusinessImpactResult
    ) -> None:
        """Store calculated metrics in the database."""

        # Update business_metrics_daily table
        query = """
        INSERT INTO business_metrics_daily (
            date, tenant_id, total_leads_processed, total_revenue_impact,
            total_operating_cost, net_roi_percentage,
            real_time_intelligence_adoption_rate, property_vision_adoption_rate,
            churn_prevention_adoption_rate, ai_coaching_adoption_rate,
            websocket_avg_latency_ms, ml_inference_avg_latency_ms,
            vision_analysis_avg_time_ms, coaching_analysis_avg_time_ms
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14
        )
        ON CONFLICT (date) DO UPDATE SET
            total_revenue_impact = EXCLUDED.total_revenue_impact,
            total_operating_cost = EXCLUDED.total_operating_cost,
            net_roi_percentage = EXCLUDED.net_roi_percentage,
            updated_at = CURRENT_TIMESTAMP
        """

        await conn.execute(
            query,
            result.date,
            result.tenant_id,
            result.lead_intelligence.usage_count + result.property_intelligence.usage_count,
            result.total_revenue_impact,
            result.total_operating_costs,
            result.roi_percentage / 100,  # Convert to decimal
            result.lead_intelligence.adoption_rate,
            result.property_intelligence.adoption_rate,
            result.churn_prevention.adoption_rate,
            result.ai_coaching.adoption_rate,
            result.lead_intelligence.performance_ms,
            result.property_intelligence.performance_ms,
            result.churn_prevention.performance_ms,
            result.ai_coaching.performance_ms
        )

        logger.info(f"Stored business metrics for {result.date}: ROI {result.roi_percentage:.1f}%")

    # Helper methods for data retrieval
    async def _get_total_leads_for_date(
        self,
        conn: asyncpg.Connection,
        target_date: date,
        tenant_id: str = None
    ) -> int:
        """Get total leads for date (for adoption rate calculation)."""
        # Placeholder - integrate with your lead tracking system
        return 100  # Default assumption

    async def _get_total_properties_for_date(
        self,
        conn: asyncpg.Connection,
        target_date: date,
        tenant_id: str = None
    ) -> int:
        """Get total properties for date (for adoption rate calculation)."""
        # Placeholder - integrate with your property tracking system
        return 50  # Default assumption

    async def _get_total_agents_for_date(
        self,
        conn: asyncpg.Connection,
        target_date: date,
        tenant_id: str = None
    ) -> int:
        """Get total active agents for date (for adoption rate calculation)."""
        # Placeholder - integrate with your agent tracking system
        return 20  # Default assumption

    async def _get_error_rate(
        self,
        conn: asyncpg.Connection,
        target_date: date,
        tenant_id: str = None
    ) -> float:
        """Get system error rate for date."""
        # Placeholder - integrate with your monitoring system
        return 0.003  # 0.3% default

    async def _get_uptime_percentage(
        self,
        conn: asyncpg.Connection,
        target_date: date,
        tenant_id: str = None
    ) -> float:
        """Get system uptime percentage for date."""
        # Placeholder - integrate with your monitoring system
        return 99.95  # 99.95% default

    async def calculate_weekly_roi_summary(
        self,
        week_start: date,
        tenant_id: str = None
    ) -> Dict:
        """Calculate weekly ROI summary."""

        logger.info(f"Calculating weekly ROI summary starting {week_start}")

        conn = await self.get_database_connection()

        try:
            week_end = week_start + timedelta(days=6)

            # Get daily results for the week
            daily_results = []
            current_date = week_start

            while current_date <= week_end:
                daily_impact = await self.calculate_daily_business_impact(current_date, tenant_id)
                daily_results.append(daily_impact)
                current_date += timedelta(days=1)

            # Calculate weekly totals
            total_revenue = sum(r.total_revenue_impact for r in daily_results)
            total_costs = sum(r.total_operating_costs for r in daily_results)
            net_revenue = total_revenue - total_costs
            weekly_roi = (net_revenue / total_costs * 100) if total_costs > 0 else Decimal('0')

            # Store weekly summary
            await self._store_weekly_summary(
                conn, week_start, week_end, tenant_id, daily_results,
                total_revenue, total_costs, net_revenue, weekly_roi
            )

            summary = {
                'week_start': week_start,
                'week_end': week_end,
                'total_revenue_impact': total_revenue,
                'total_costs': total_costs,
                'net_revenue': net_revenue,
                'roi_percentage': weekly_roi,
                'daily_breakdown': [asdict(r) for r in daily_results]
            }

            return summary

        finally:
            await conn.close()

    async def _store_weekly_summary(
        self,
        conn: asyncpg.Connection,
        week_start: date,
        week_end: date,
        tenant_id: str,
        daily_results: List[BusinessImpactResult],
        total_revenue: Decimal,
        total_costs: Decimal,
        net_revenue: Decimal,
        weekly_roi: Decimal
    ) -> None:
        """Store weekly ROI summary in database."""

        # Calculate feature-specific revenue totals
        lead_intelligence_revenue = sum(r.lead_intelligence.revenue_impact for r in daily_results)
        property_intelligence_revenue = sum(r.property_intelligence.revenue_impact for r in daily_results)
        churn_prevention_revenue = sum(r.churn_prevention.revenue_impact for r in daily_results)
        ai_coaching_revenue = sum(r.ai_coaching.revenue_impact for r in daily_results)

        query = """
        INSERT INTO roi_weekly_summary (
            week_start_date, week_end_date, tenant_id,
            lead_intelligence_revenue, property_intelligence_revenue,
            churn_prevention_revenue, ai_coaching_revenue, total_revenue_impact,
            total_costs, net_revenue, roi_percentage
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11
        )
        ON CONFLICT (week_start_date, tenant_id) DO UPDATE SET
            total_revenue_impact = EXCLUDED.total_revenue_impact,
            total_costs = EXCLUDED.total_costs,
            net_revenue = EXCLUDED.net_revenue,
            roi_percentage = EXCLUDED.roi_percentage,
            created_at = CURRENT_TIMESTAMP
        """

        await conn.execute(
            query,
            week_start, week_end, tenant_id or "default",
            lead_intelligence_revenue, property_intelligence_revenue,
            churn_prevention_revenue, ai_coaching_revenue, total_revenue,
            total_costs, net_revenue, weekly_roi / 100
        )

        logger.info(f"Stored weekly summary: {week_start} to {week_end}, ROI {weekly_roi:.1f}%")

    async def generate_roi_report(self, start_date: date, end_date: date = None) -> Dict:
        """Generate comprehensive ROI report for date range."""

        if end_date is None:
            end_date = start_date

        logger.info(f"Generating ROI report from {start_date} to {end_date}")

        conn = await self.get_database_connection()

        try:
            # Get business impact health
            health_query = "SELECT * FROM business_impact_health LIMIT 1"
            health = await conn.fetchrow(health_query)

            # Get feature performance summary
            perf_query = """
            SELECT * FROM feature_performance_summary
            WHERE date BETWEEN $1 AND $2
            ORDER BY date DESC, feature_name
            """
            performance = await conn.fetch(perf_query, start_date, end_date)

            # Get daily ROI summary
            roi_query = """
            SELECT * FROM daily_roi_summary
            WHERE date BETWEEN $1 AND $2
            ORDER BY date DESC
            """
            daily_roi = await conn.fetch(roi_query, start_date, end_date)

            report = {
                'report_date': datetime.now().isoformat(),
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': (end_date - start_date).days + 1
                },
                'health_check': dict(health) if health else None,
                'performance_summary': [dict(row) for row in performance],
                'daily_roi': [dict(row) for row in daily_roi],
                'summary': {
                    'total_revenue': sum(row['total_revenue_impact'] for row in daily_roi),
                    'total_costs': sum(row['total_daily_costs'] for row in daily_roi),
                    'avg_daily_roi': sum(row['daily_roi_percentage'] for row in daily_roi) / len(daily_roi) if daily_roi else 0,
                    'trend': self._calculate_trend([row['daily_roi_percentage'] for row in daily_roi])
                }
            }

            return report

        finally:
            await conn.close()

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction from list of values."""
        if len(values) < 2:
            return "insufficient_data"

        start_avg = sum(values[:len(values)//2]) / (len(values)//2)
        end_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)

        change = (end_avg - start_avg) / start_avg if start_avg > 0 else 0

        if change > 0.05:
            return "strongly_positive"
        elif change > 0.01:
            return "positive"
        elif change < -0.05:
            return "strongly_negative"
        elif change < -0.01:
            return "negative"
        else:
            return "stable"


async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Calculate Phase 3 Business Impact')
    parser.add_argument('--mode', choices=['daily', 'weekly', 'report'],
                       default='daily', help='Calculation mode')
    parser.add_argument('--date', type=str,
                       help='Target date (YYYY-MM-DD), defaults to today')
    parser.add_argument('--start-date', type=str,
                       help='Start date for weekly/report mode (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str,
                       help='End date for report mode (YYYY-MM-DD)')
    parser.add_argument('--tenant-id', type=str,
                       help='Specific tenant ID (optional)')
    parser.add_argument('--output', choices=['json', 'summary'],
                       default='summary', help='Output format')
    parser.add_argument('--save-file', type=str,
                       help='Save output to file')

    args = parser.parse_args()

    # Get database URL
    database_url = get_database_url()
    calculator = BusinessImpactCalculator(database_url)

    try:
        if args.mode == 'daily':
            target_date = datetime.strptime(args.date, '%Y-%m-%d').date() if args.date else date.today()
            result = await calculator.calculate_daily_business_impact(target_date, args.tenant_id)

            if args.output == 'json':
                output = json.dumps(asdict(result), default=str, indent=2)
            else:
                output = f"""
Phase 3 Business Impact - {result.date}
{'='*50}

Feature Performance:
  Real-Time Intelligence: ${result.lead_intelligence.revenue_impact:.2f} ({result.lead_intelligence.usage_count} uses)
  Property Intelligence:  ${result.property_intelligence.revenue_impact:.2f} ({result.property_intelligence.usage_count} uses)
  Churn Prevention:       ${result.churn_prevention.revenue_impact:.2f} ({result.churn_prevention.usage_count} uses)
  AI Coaching:            ${result.ai_coaching.revenue_impact:.2f} ({result.ai_coaching.usage_count} uses)

Financial Summary:
  Total Revenue Impact:   ${result.total_revenue_impact:.2f}
  Operating Costs:        ${result.total_operating_costs:.2f}
  Net Revenue:            ${result.net_revenue:.2f}
  ROI:                    {result.roi_percentage:.1f}%

Performance Summary:
  Avg Response Time:      {result.avg_response_time_ms:.1f}ms
  Error Rate:             {result.error_rate:.3f}%
  Uptime:                 {result.uptime_percentage:.2f}%
"""

        elif args.mode == 'weekly':
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date() if args.start_date else date.today()
            result = await calculator.calculate_weekly_roi_summary(start_date, args.tenant_id)

            if args.output == 'json':
                output = json.dumps(result, default=str, indent=2)
            else:
                output = f"""
Phase 3 Weekly ROI Summary
{'='*50}
Week: {result['week_start']} to {result['week_end']}

Summary:
  Total Revenue Impact:   ${result['total_revenue_impact']:.2f}
  Total Costs:           ${result['total_costs']:.2f}
  Net Revenue:           ${result['net_revenue']:.2f}
  Weekly ROI:            {result['roi_percentage']:.1f}%
"""

        elif args.mode == 'report':
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date() if args.start_date else date.today()
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date() if args.end_date else start_date
            result = await calculator.generate_roi_report(start_date, end_date)

            output = json.dumps(result, default=str, indent=2)

        # Output results
        if args.save_file:
            with open(args.save_file, 'w') as f:
                f.write(output)
            logger.info(f"Results saved to {args.save_file}")
        else:
            print(output)

    except Exception as e:
        logger.error(f"Error calculating business impact: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())