#!/usr/bin/env python3
"""
Phase 3 Business Impact Tracking Script
Real-time tracking of $265K-440K annual value features

Generates comprehensive reports on:
- Feature performance vs targets
- Revenue impact and ROI
- User adoption and satisfaction
- Cost optimization
- A/B test results

Usage:
    python scripts/monitoring/track_phase3_impact.py --daily
    python scripts/monitoring/track_phase3_impact.py --weekly
    python scripts/monitoring/track_phase3_impact.py --feature realtime_intelligence
    python scripts/monitoring/track_phase3_impact.py --export-csv
"""

import asyncio
import argparse
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import csv

import redis.asyncio as redis
from prometheus_api_client import PrometheusConnect
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class FeatureImpactReport:
    """Business impact report for a Phase 3 feature."""
    feature_name: str
    date: str

    # Performance Metrics
    p95_latency_ms: float
    target_latency_ms: float
    latency_met: bool

    # Volume Metrics
    total_requests: int
    error_rate: float
    active_users: int

    # Business Metrics
    revenue_impact_daily: float
    projected_annual: float
    target_annual_min: float
    target_annual_max: float
    on_track: bool

    # User Satisfaction
    nps_score: float
    adoption_rate: float

    # Cost Metrics
    infrastructure_cost_daily: float
    api_cost_daily: float
    total_cost_daily: float
    net_impact_daily: float
    roi_multiplier: float


@dataclass
class Phase3SummaryReport:
    """Overall Phase 3 business impact summary."""
    date: str

    # Overall Revenue
    total_revenue_daily: float
    projected_annual: float
    target_range: str
    on_track: bool

    # Feature Breakdown
    features: List[FeatureImpactReport]

    # Overall Metrics
    avg_nps: float
    avg_adoption: float
    total_active_users: int

    # Costs
    total_infrastructure_cost: float
    total_api_cost: float
    total_cost: float
    net_impact: float
    overall_roi: float

    # SLA Compliance
    all_slas_met: bool
    sla_breaches: List[str]


class Phase3ImpactTracker:
    """
    Track and report on Phase 3 business impact.

    Connects to Prometheus and Redis to collect real-time metrics
    and generate comprehensive impact reports.
    """

    def __init__(self,
                 prometheus_url: str = "http://localhost:9090",
                 redis_url: str = "redis://localhost:6379/3",
                 db_url: str = "postgresql://localhost/enterprisehub"):

        self.prom = PrometheusConnect(url=prometheus_url, disable_ssl=True)
        self.redis_client = redis.from_url(redis_url)
        self.db_engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.db_engine)

        # Feature definitions with targets
        self.features = {
            "realtime_intelligence": {
                "name": "Real-Time Lead Intelligence",
                "annual_min": 75000,
                "annual_max": 120000,
                "latency_target_ms": 50,
                "latency_metric": "websocket_latency_seconds"
            },
            "property_intelligence": {
                "name": "Multimodal Property Intelligence",
                "annual_min": 75000,
                "annual_max": 150000,
                "latency_target_ms": 1500,
                "latency_metric": "vision_analysis_duration_seconds"
            },
            "churn_prevention": {
                "name": "Proactive Churn Prevention",
                "annual_min": 55000,
                "annual_max": 80000,
                "latency_target_ms": 30000,
                "latency_metric": "churn_intervention_latency_seconds"
            },
            "ai_coaching": {
                "name": "AI-Powered Coaching",
                "annual_min": 60000,
                "annual_max": 90000,
                "latency_target_ms": 2000,
                "latency_metric": "coaching_analysis_duration_seconds"
            }
        }

    async def get_feature_impact_report(self, feature_id: str,
                                       date: Optional[datetime] = None) -> FeatureImpactReport:
        """Generate impact report for a specific feature."""

        if date is None:
            date = datetime.now()

        feature_config = self.features[feature_id]
        date_str = date.strftime("%Y-%m-%d")

        # Get performance metrics from Prometheus
        latency_query = f'histogram_quantile(0.95, rate({feature_config["latency_metric"]}_bucket{{feature="{feature_id}"}}[1h])) * 1000'
        latency_result = self.prom.custom_query(latency_query)
        p95_latency = float(latency_result[0]['value'][1]) if latency_result else 0

        # Get request volume
        requests_query = f'sum(increase(phase3_revenue_impact_dollars{{feature="{feature_id}"}}[24h]))'
        requests_result = self.prom.custom_query(requests_query)
        total_requests = int(float(requests_result[0]['value'][1])) if requests_result else 0

        # Get error rate
        error_query = f'rate(vision_api_errors_total{{feature="{feature_id}"}}[1h]) / rate(vision_api_requests_total{{feature="{feature_id}"}}[1h])'
        error_result = self.prom.custom_query(error_query)
        error_rate = float(error_result[0]['value'][1]) if error_result else 0

        # Get revenue impact
        revenue_query = f'sum(rate(phase3_revenue_impact_dollars{{feature="{feature_id}"}}[24h])) * 24'
        revenue_result = self.prom.custom_query(revenue_query)
        revenue_daily = float(revenue_result[0]['value'][1]) if revenue_result else 0
        projected_annual = revenue_daily * 365

        # Get user metrics from Redis
        active_users = int(await self.redis_client.get(f"phase3:metrics:{feature_id}:active_users") or 0)
        nps_score = float(await self.redis_client.get(f"phase3:business:nps:{feature_id}") or 0)
        adoption_rate = float(await self.redis_client.get(f"phase3:business:adoption:{feature_id}") or 0)

        # Get cost metrics
        infra_cost_query = f'sum(rate(feature_infrastructure_cost_dollars{{feature="{feature_id}"}}[24h])) * 24'
        infra_cost_result = self.prom.custom_query(infra_cost_query)
        infra_cost = float(infra_cost_result[0]['value'][1]) if infra_cost_result else 0

        api_cost_query = f'sum(rate(claude_api_cost_dollars{{feature="{feature_id}"}}[24h])) * 24'
        api_cost_result = self.prom.custom_query(api_cost_query)
        api_cost = float(api_cost_result[0]['value'][1]) if api_cost_result else 0

        total_cost = infra_cost + api_cost
        net_impact = revenue_daily - total_cost
        roi_multiplier = revenue_daily / total_cost if total_cost > 0 else 0

        # Check if on track
        latency_met = p95_latency <= feature_config["latency_target_ms"]
        on_track = (projected_annual >= feature_config["annual_min"] and
                   projected_annual <= feature_config["annual_max"] * 1.2)  # Allow 20% over

        return FeatureImpactReport(
            feature_name=feature_config["name"],
            date=date_str,
            p95_latency_ms=p95_latency,
            target_latency_ms=feature_config["latency_target_ms"],
            latency_met=latency_met,
            total_requests=total_requests,
            error_rate=error_rate,
            active_users=active_users,
            revenue_impact_daily=revenue_daily,
            projected_annual=projected_annual,
            target_annual_min=feature_config["annual_min"],
            target_annual_max=feature_config["annual_max"],
            on_track=on_track,
            nps_score=nps_score,
            adoption_rate=adoption_rate,
            infrastructure_cost_daily=infra_cost,
            api_cost_daily=api_cost,
            total_cost_daily=total_cost,
            net_impact_daily=net_impact,
            roi_multiplier=roi_multiplier
        )

    async def get_phase3_summary_report(self,
                                       date: Optional[datetime] = None) -> Phase3SummaryReport:
        """Generate overall Phase 3 impact summary."""

        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")

        # Get reports for all features
        feature_reports = []
        for feature_id in self.features.keys():
            report = await self.get_feature_impact_report(feature_id, date)
            feature_reports.append(report)

        # Calculate overall metrics
        total_revenue = sum(r.revenue_impact_daily for r in feature_reports)
        projected_annual = total_revenue * 365

        avg_nps = sum(r.nps_score for r in feature_reports) / len(feature_reports)
        avg_adoption = sum(r.adoption_rate for r in feature_reports) / len(feature_reports)
        total_active_users = sum(r.active_users for r in feature_reports)

        total_infra_cost = sum(r.infrastructure_cost_daily for r in feature_reports)
        total_api_cost = sum(r.api_cost_daily for r in feature_reports)
        total_cost = total_infra_cost + total_api_cost
        net_impact = total_revenue - total_cost
        overall_roi = total_revenue / total_cost if total_cost > 0 else 0

        # Check SLA compliance
        sla_breaches = [r.feature_name for r in feature_reports if not r.latency_met]
        all_slas_met = len(sla_breaches) == 0

        # Check if overall revenue is on track
        on_track = (projected_annual >= 265000 and  # Minimum target
                   projected_annual <= 440000 * 1.2)  # Maximum target + 20%

        return Phase3SummaryReport(
            date=date_str,
            total_revenue_daily=total_revenue,
            projected_annual=projected_annual,
            target_range="$265K-440K",
            on_track=on_track,
            features=feature_reports,
            avg_nps=avg_nps,
            avg_adoption=avg_adoption,
            total_active_users=total_active_users,
            total_infrastructure_cost=total_infra_cost,
            total_api_cost=total_api_cost,
            total_cost=total_cost,
            net_impact=net_impact,
            overall_roi=overall_roi,
            all_slas_met=all_slas_met,
            sla_breaches=sla_breaches
        )

    async def print_daily_report(self) -> None:
        """Print formatted daily impact report."""

        summary = await self.get_phase3_summary_report()

        print("\n" + "="*80)
        print(f"PHASE 3 DAILY BUSINESS IMPACT REPORT - {summary.date}")
        print("="*80)

        print(f"\n📊 OVERALL PERFORMANCE")
        print(f"  Daily Revenue:        ${summary.total_revenue_daily:,.2f}")
        print(f"  Projected Annual:     ${summary.projected_annual:,.2f}")
        print(f"  Target Range:         {summary.target_range}")
        print(f"  On Track:             {'✅ YES' if summary.on_track else '❌ NO'}")
        print(f"  Overall ROI:          {summary.overall_roi:.1f}x")

        print(f"\n👥 USER METRICS")
        print(f"  Active Users:         {summary.total_active_users:,}")
        print(f"  Average NPS:          {summary.avg_nps:.1f}")
        print(f"  Average Adoption:     {summary.avg_adoption*100:.1f}%")

        print(f"\n💰 COST BREAKDOWN")
        print(f"  Infrastructure:       ${summary.total_infrastructure_cost:,.2f}/day")
        print(f"  API Costs:            ${summary.total_api_cost:,.2f}/day")
        print(f"  Total Costs:          ${summary.total_cost:,.2f}/day")
        print(f"  Net Impact:           ${summary.net_impact:,.2f}/day")

        print(f"\n🎯 SLA COMPLIANCE")
        if summary.all_slas_met:
            print(f"  Status:               ✅ All SLAs Met")
        else:
            print(f"  Status:               ⚠️  SLA Breaches Detected")
            for breach in summary.sla_breaches:
                print(f"    - {breach}")

        print(f"\n📈 FEATURE BREAKDOWN")
        print(f"{'Feature':<40} {'Revenue/Day':<15} {'Projected Annual':<20} {'Status':<10}")
        print("-"*90)

        for feature in summary.features:
            status = "✅ On Track" if feature.on_track else "⚠️ Review"
            print(f"{feature.feature_name:<40} ${feature.revenue_impact_daily:>13,.2f} "
                  f"${feature.projected_annual:>18,.2f} {status}")

        print("\n" + "="*80)
        print(f"Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")

    async def export_to_csv(self, output_file: str = "phase3_impact_report.csv") -> None:
        """Export impact report to CSV."""

        summary = await self.get_phase3_summary_report()

        # Flatten data for CSV
        rows = []
        for feature in summary.features:
            row = {
                'date': summary.date,
                'feature': feature.feature_name,
                'revenue_daily': feature.revenue_impact_daily,
                'projected_annual': feature.projected_annual,
                'target_min': feature.target_annual_min,
                'target_max': feature.target_annual_max,
                'on_track': feature.on_track,
                'p95_latency_ms': feature.p95_latency_ms,
                'target_latency_ms': feature.target_latency_ms,
                'latency_met': feature.latency_met,
                'active_users': feature.active_users,
                'nps_score': feature.nps_score,
                'adoption_rate': feature.adoption_rate,
                'infrastructure_cost': feature.infrastructure_cost_daily,
                'api_cost': feature.api_cost_daily,
                'total_cost': feature.total_cost_daily,
                'net_impact': feature.net_impact_daily,
                'roi_multiplier': feature.roi_multiplier,
                'error_rate': feature.error_rate
            }
            rows.append(row)

        # Write to CSV
        df = pd.DataFrame(rows)
        df.to_csv(output_file, index=False)

        logger.info(f"Report exported to {output_file}")

    async def get_weekly_trend_report(self) -> None:
        """Generate weekly trend analysis."""

        print("\n" + "="*80)
        print(f"PHASE 3 WEEKLY TREND ANALYSIS")
        print("="*80)

        # Get data for last 7 days
        daily_summaries = []
        for days_ago in range(7):
            date = datetime.now() - timedelta(days=days_ago)
            summary = await self.get_phase3_summary_report(date)
            daily_summaries.append(summary)

        # Calculate week-over-week changes
        latest = daily_summaries[0]
        week_ago = daily_summaries[6]

        revenue_change = ((latest.total_revenue_daily - week_ago.total_revenue_daily) /
                         week_ago.total_revenue_daily * 100)
        nps_change = latest.avg_nps - week_ago.avg_nps
        adoption_change = (latest.avg_adoption - week_ago.avg_adoption) * 100

        print(f"\n📊 WEEK-OVER-WEEK CHANGES")
        print(f"  Revenue:              {revenue_change:+.1f}%")
        print(f"  NPS Score:            {nps_change:+.1f} points")
        print(f"  Adoption Rate:        {adoption_change:+.1f}%")

        print(f"\n📈 7-DAY PERFORMANCE")
        print(f"{'Date':<12} {'Revenue':<15} {'NPS':<8} {'Adoption':<12} {'SLA Met'}")
        print("-"*60)

        for summary in reversed(daily_summaries):
            sla_status = "✅" if summary.all_slas_met else "❌"
            print(f"{summary.date:<12} ${summary.total_revenue_daily:>13,.2f} "
                  f"{summary.avg_nps:>6.1f} {summary.avg_adoption*100:>10.1f}% {sla_status}")

        print("\n" + "="*80 + "\n")


async def main():
    """Main entry point for Phase 3 impact tracking."""

    parser = argparse.ArgumentParser(
        description="Track Phase 3 business impact and performance"
    )
    parser.add_argument("--daily", action="store_true",
                       help="Generate daily impact report")
    parser.add_argument("--weekly", action="store_true",
                       help="Generate weekly trend analysis")
    parser.add_argument("--feature", type=str,
                       help="Generate report for specific feature")
    parser.add_argument("--export-csv", action="store_true",
                       help="Export report to CSV")
    parser.add_argument("--output", type=str, default="phase3_impact_report.csv",
                       help="Output CSV filename")

    args = parser.parse_args()

    tracker = Phase3ImpactTracker()

    try:
        if args.daily or (not args.weekly and not args.feature and not args.export_csv):
            await tracker.print_daily_report()

        if args.weekly:
            await tracker.get_weekly_trend_report()

        if args.feature:
            report = await tracker.get_feature_impact_report(args.feature)
            print(json.dumps(asdict(report), indent=2))

        if args.export_csv:
            await tracker.export_to_csv(args.output)

    finally:
        await tracker.redis_client.close()


if __name__ == "__main__":
    asyncio.run(main())
