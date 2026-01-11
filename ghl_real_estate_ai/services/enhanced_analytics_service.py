"""
Enhanced Analytics Service (Phase 1 Implementation)

Extends existing analytics with:
- Revenue intelligence and market performance metrics
- Advanced reporting engine (PDF, Excel, PowerBI integration)
- Multi-format export system with automated scheduling
- Real-time analytics with sub-100ms performance targets
- Agent productivity KPIs and benchmarking

Built for enterprise-scale performance and business intelligence.
"""

import asyncio
import json
import statistics
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib
import io
import base64

# External libraries (to be installed if not present)
try:
    import redis
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
except ImportError as e:
    print(f"Enhanced Analytics: Some optional dependencies not available: {e}")
    print("Install with: pip install redis pandas plotly reportlab openpyxl")

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_engine import AnalyticsEngine, ConversationMetrics
from ghl_real_estate_ai.services.executive_dashboard import ExecutiveDashboardService
from ghl_real_estate_ai.services.revenue_attribution import RevenueAttributionEngine

logger = get_logger(__name__)


@dataclass
class RevenueMetrics:
    """Revenue intelligence metrics."""

    total_pipeline_value: float = 0.0
    closed_deals_value: float = 0.0
    average_deal_size: float = 0.0
    conversion_rate: float = 0.0
    revenue_per_lead: float = 0.0
    cost_per_acquisition: float = 0.0
    roi_percentage: float = 0.0
    monthly_recurring_revenue: float = 0.0
    pipeline_velocity_days: float = 0.0
    win_rate: float = 0.0


@dataclass
class MarketPerformanceMetrics:
    """Market performance and competitive analysis."""

    market_share_percentage: float = 0.0
    lead_quality_index: float = 0.0
    property_match_accuracy: float = 0.0
    client_satisfaction_score: float = 0.0
    time_to_close_avg_days: float = 0.0
    competitive_win_rate: float = 0.0
    price_accuracy_percentage: float = 0.0
    market_penetration_rate: float = 0.0


@dataclass
class AgentProductivityKPIs:
    """Agent productivity key performance indicators."""

    contacts_per_day: float = 0.0
    qualified_leads_per_day: float = 0.0
    appointments_booked_per_day: float = 0.0
    response_time_avg_minutes: float = 0.0
    conversion_rate_leads_to_appointments: float = 0.0
    deals_closed_per_month: float = 0.0
    revenue_per_agent_per_month: float = 0.0
    coaching_sessions_completed: int = 0
    ai_assistance_usage_rate: float = 0.0
    performance_score: float = 0.0


class RealtimeAnalyticsCache:
    """Redis-based caching for sub-100ms analytics performance."""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize Redis cache for real-time analytics."""
        self.redis_client = None
        try:
            import redis
            self.redis_client = redis.from_url(
                redis_url or "redis://localhost:6379/0",
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized for real-time analytics")
        except Exception as e:
            logger.warning(f"Redis cache not available, using in-memory cache: {e}")
            self.memory_cache = {}

    async def get_cached_metrics(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached metrics with sub-100ms target."""
        try:
            if self.redis_client:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)
            else:
                return self.memory_cache.get(cache_key)
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
        return None

    async def set_cached_metrics(
        self,
        cache_key: str,
        data: Dict[str, Any],
        ttl_seconds: int = 300
    ) -> None:
        """Cache metrics with TTL for real-time performance."""
        try:
            if self.redis_client:
                self.redis_client.setex(
                    cache_key,
                    ttl_seconds,
                    json.dumps(data, default=str)
                )
            else:
                self.memory_cache[cache_key] = data
                # Simple TTL simulation for memory cache
                asyncio.create_task(self._expire_memory_cache(cache_key, ttl_seconds))
        except Exception as e:
            logger.error(f"Cache storage error: {e}")

    async def _expire_memory_cache(self, key: str, ttl: int):
        """Simple TTL for memory cache."""
        await asyncio.sleep(ttl)
        self.memory_cache.pop(key, None)


class ReportGenerator:
    """Advanced reporting engine for PDF, Excel, and PowerBI integration."""

    def __init__(self, output_dir: Path = None):
        """Initialize report generator."""
        self.output_dir = output_dir or Path("reports")
        self.output_dir.mkdir(exist_ok=True)
        self.styles = self._setup_report_styles()

    def _setup_report_styles(self) -> Dict[str, Any]:
        """Setup consistent report styling."""
        try:
            from reportlab.lib.styles import getSampleStyleSheet
            styles = getSampleStyleSheet()

            # Custom styles for enterprise reports
            enterprise_title = ParagraphStyle(
                'EnterpriseTitle',
                parent=styles['Title'],
                fontSize=24,
                textColor=colors.HexColor('#2E3B4E'),
                spaceAfter=20,
                alignment=1  # Center
            )

            enterprise_heading = ParagraphStyle(
                'EnterpriseHeading',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor('#3A5F7D'),
                spaceBefore=16,
                spaceAfter=12
            )

            styles.add(enterprise_title)
            styles.add(enterprise_heading)

            return styles
        except ImportError:
            return {}

    async def generate_revenue_intelligence_pdf(
        self,
        revenue_data: Dict[str, Any],
        location_id: str
    ) -> str:
        """Generate comprehensive revenue intelligence PDF report."""
        try:
            filename = f"revenue_intelligence_{location_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            filepath = self.output_dir / filename

            # Create PDF document
            doc = SimpleDocTemplate(str(filepath), pagesize=letter)
            story = []

            # Title
            story.append(Paragraph("Revenue Intelligence Report", self.styles.get('EnterpriseTitle')))
            story.append(Spacer(1, 20))

            # Executive Summary
            story.append(Paragraph("Executive Summary", self.styles.get('EnterpriseHeading')))

            exec_summary = [
                f"• Total Pipeline Value: ${revenue_data.get('total_pipeline_value', 0):,.2f}",
                f"• Conversion Rate: {revenue_data.get('conversion_rate', 0):.1%}",
                f"• Average Deal Size: ${revenue_data.get('average_deal_size', 0):,.2f}",
                f"• ROI: {revenue_data.get('roi_percentage', 0):.1%}",
            ]

            for item in exec_summary:
                story.append(Paragraph(item, self.styles.get('Normal')))

            story.append(Spacer(1, 20))

            # Revenue Metrics Table
            story.append(Paragraph("Revenue Metrics", self.styles.get('EnterpriseHeading')))

            revenue_table_data = [
                ['Metric', 'Value', 'Trend'],
                ['Pipeline Value', f"${revenue_data.get('total_pipeline_value', 0):,.2f}", '↗'],
                ['Closed Deals', f"${revenue_data.get('closed_deals_value', 0):,.2f}", '↗'],
                ['Win Rate', f"{revenue_data.get('win_rate', 0):.1%}", '→'],
                ['Cost per Acquisition', f"${revenue_data.get('cost_per_acquisition', 0):,.2f}", '↘'],
            ]

            revenue_table = Table(revenue_table_data)
            revenue_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))

            story.append(revenue_table)
            story.append(Spacer(1, 30))

            # Build PDF
            doc.build(story)

            logger.info(f"Revenue intelligence PDF generated: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            return ""

    async def generate_excel_dashboard(
        self,
        analytics_data: Dict[str, Any],
        location_id: str
    ) -> str:
        """Generate Excel dashboard with multiple worksheets."""
        try:
            import pandas as pd

            filename = f"analytics_dashboard_{location_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
            filepath = self.output_dir / filename

            with pd.ExcelWriter(str(filepath), engine='openpyxl') as writer:
                # Revenue Intelligence Sheet
                revenue_df = pd.DataFrame([analytics_data.get('revenue_metrics', {})])
                revenue_df.to_excel(writer, sheet_name='Revenue Intelligence', index=False)

                # Agent Performance Sheet
                agent_data = analytics_data.get('agent_kpis', {})
                agent_df = pd.DataFrame([agent_data])
                agent_df.to_excel(writer, sheet_name='Agent Performance', index=False)

                # Market Analysis Sheet
                market_data = analytics_data.get('market_performance', {})
                market_df = pd.DataFrame([market_data])
                market_df.to_excel(writer, sheet_name='Market Analysis', index=False)

                # Trends Sheet (time series data)
                if 'historical_data' in analytics_data:
                    trends_df = pd.DataFrame(analytics_data['historical_data'])
                    trends_df.to_excel(writer, sheet_name='Trends', index=False)

            logger.info(f"Excel dashboard generated: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Excel generation failed: {e}")
            return ""

    async def generate_powerbi_dataset(
        self,
        analytics_data: Dict[str, Any],
        location_id: str
    ) -> str:
        """Generate PowerBI-compatible dataset (JSON format)."""
        try:
            filename = f"powerbi_dataset_{location_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            filepath = self.output_dir / filename

            # Structure data for PowerBI consumption
            powerbi_data = {
                "tables": [
                    {
                        "name": "RevenueMetrics",
                        "columns": [
                            {"name": "Date", "dataType": "DateTime"},
                            {"name": "PipelineValue", "dataType": "Double"},
                            {"name": "ClosedDeals", "dataType": "Double"},
                            {"name": "ConversionRate", "dataType": "Double"},
                            {"name": "ROI", "dataType": "Double"}
                        ],
                        "rows": self._format_powerbi_rows(analytics_data.get('revenue_metrics', {}))
                    },
                    {
                        "name": "AgentKPIs",
                        "columns": [
                            {"name": "Date", "dataType": "DateTime"},
                            {"name": "ContactsPerDay", "dataType": "Double"},
                            {"name": "QualifiedLeadsPerDay", "dataType": "Double"},
                            {"name": "ConversionRate", "dataType": "Double"},
                            {"name": "PerformanceScore", "dataType": "Double"}
                        ],
                        "rows": self._format_powerbi_rows(analytics_data.get('agent_kpis', {}))
                    }
                ],
                "relationships": [
                    {
                        "name": "DateRelationship",
                        "fromTable": "RevenueMetrics",
                        "fromColumn": "Date",
                        "toTable": "AgentKPIs",
                        "toColumn": "Date"
                    }
                ]
            }

            with open(filepath, 'w') as f:
                json.dump(powerbi_data, f, indent=2, default=str)

            logger.info(f"PowerBI dataset generated: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"PowerBI dataset generation failed: {e}")
            return ""

    def _format_powerbi_rows(self, data: Dict[str, Any]) -> List[List[Any]]:
        """Format data rows for PowerBI consumption."""
        now = datetime.now()
        return [[now.isoformat(), *data.values()]]


class ScheduledReportingEngine:
    """Automated report scheduling and delivery system."""

    def __init__(self, report_generator: ReportGenerator):
        """Initialize scheduled reporting engine."""
        self.report_generator = report_generator
        self.schedules = {}
        self.schedule_file = Path("data/report_schedules.json")
        self._load_schedules()

    def _load_schedules(self):
        """Load existing report schedules."""
        if self.schedule_file.exists():
            try:
                with open(self.schedule_file) as f:
                    self.schedules = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load schedules: {e}")
                self.schedules = {}

    def _save_schedules(self):
        """Save report schedules to file."""
        self.schedule_file.parent.mkdir(exist_ok=True, parents=True)
        with open(self.schedule_file, 'w') as f:
            json.dump(self.schedules, f, indent=2, default=str)

    def schedule_report(
        self,
        schedule_name: str,
        report_type: str,  # "revenue_pdf", "excel_dashboard", "powerbi_dataset"
        location_id: str,
        frequency: str,  # "daily", "weekly", "monthly"
        delivery_method: str = "file",  # "file", "email" (future)
        recipients: List[str] = None
    ) -> str:
        """Schedule automated report generation."""
        schedule_id = hashlib.md5(f"{schedule_name}{location_id}{report_type}".encode()).hexdigest()

        schedule = {
            "id": schedule_id,
            "name": schedule_name,
            "report_type": report_type,
            "location_id": location_id,
            "frequency": frequency,
            "delivery_method": delivery_method,
            "recipients": recipients or [],
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "next_run": self._calculate_next_run(frequency),
            "status": "active"
        }

        self.schedules[schedule_id] = schedule
        self._save_schedules()

        logger.info(f"Scheduled report '{schedule_name}' created with ID: {schedule_id}")
        return schedule_id

    def _calculate_next_run(self, frequency: str) -> str:
        """Calculate next run time based on frequency."""
        now = datetime.now()

        if frequency == "daily":
            next_run = now + timedelta(days=1)
        elif frequency == "weekly":
            next_run = now + timedelta(weeks=1)
        elif frequency == "monthly":
            next_run = now + timedelta(days=30)
        else:
            next_run = now + timedelta(days=1)  # Default to daily

        return next_run.isoformat()

    async def process_scheduled_reports(self) -> List[str]:
        """Process due scheduled reports."""
        now = datetime.now()
        generated_reports = []

        for schedule_id, schedule in self.schedules.items():
            if schedule["status"] != "active":
                continue

            next_run = datetime.fromisoformat(schedule["next_run"])

            if now >= next_run:
                try:
                    # Generate report based on type
                    report_path = await self._generate_scheduled_report(schedule)

                    if report_path:
                        generated_reports.append(report_path)

                        # Update schedule for next run
                        schedule["last_run"] = now.isoformat()
                        schedule["next_run"] = self._calculate_next_run(schedule["frequency"])

                        logger.info(f"Generated scheduled report: {report_path}")

                except Exception as e:
                    logger.error(f"Failed to generate scheduled report {schedule_id}: {e}")

        self._save_schedules()
        return generated_reports

    async def _generate_scheduled_report(self, schedule: Dict[str, Any]) -> str:
        """Generate a specific scheduled report."""
        # This would integrate with the analytics service to get current data
        # For now, returning a placeholder
        report_type = schedule["report_type"]
        location_id = schedule["location_id"]

        # Mock data - in production, this would fetch real analytics data
        analytics_data = {
            "revenue_metrics": {"total_pipeline_value": 500000, "conversion_rate": 0.15},
            "agent_kpis": {"contacts_per_day": 25, "performance_score": 85},
            "market_performance": {"lead_quality_index": 0.92}
        }

        if report_type == "revenue_pdf":
            return await self.report_generator.generate_revenue_intelligence_pdf(
                analytics_data["revenue_metrics"], location_id
            )
        elif report_type == "excel_dashboard":
            return await self.report_generator.generate_excel_dashboard(
                analytics_data, location_id
            )
        elif report_type == "powerbi_dataset":
            return await self.report_generator.generate_powerbi_dataset(
                analytics_data, location_id
            )

        return ""


class EnhancedAnalyticsService:
    """
    Enhanced Analytics Service with enterprise-grade capabilities.

    Provides:
    - Revenue intelligence and market performance metrics
    - Agent productivity KPIs and benchmarking
    - Real-time analytics with sub-100ms performance
    - Advanced reporting (PDF, Excel, PowerBI integration)
    - Automated report scheduling and delivery
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        data_dir: Path = None
    ):
        """Initialize Enhanced Analytics Service."""
        self.base_analytics = AnalyticsEngine()
        self.executive_dashboard = ExecutiveDashboardService(data_dir)
        self.revenue_attribution = RevenueAttributionEngine()
        self.realtime_cache = RealtimeAnalyticsCache(redis_url)
        self.report_generator = ReportGenerator()
        self.scheduled_reporting = ScheduledReportingEngine(self.report_generator)

        logger.info("Enhanced Analytics Service initialized with enterprise capabilities")

    async def get_revenue_intelligence(
        self,
        location_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> RevenueMetrics:
        """
        Get comprehensive revenue intelligence metrics.

        Target performance: <100ms with caching
        """
        cache_key = f"revenue_intel:{location_id}:{start_date}:{end_date}"

        # Check cache first
        cached_metrics = await self.realtime_cache.get_cached_metrics(cache_key)
        if cached_metrics:
            logger.debug(f"Revenue intelligence cache hit for {location_id}")
            return RevenueMetrics(**cached_metrics)

        # Calculate metrics
        start_time = datetime.now()

        # Get base conversion funnel
        funnel = await self.base_analytics.get_conversion_funnel(location_id, start_date, end_date)

        # Get revenue attribution data
        revenue_report = self.revenue_attribution.get_full_attribution_report(location_id)

        # Calculate enhanced revenue metrics
        revenue_metrics = RevenueMetrics(
            total_pipeline_value=revenue_report.get("total_pipeline_value", 0.0),
            closed_deals_value=revenue_report.get("closed_revenue", 0.0),
            average_deal_size=revenue_report.get("average_deal_size", 0.0),
            conversion_rate=funnel.overall_conversion_rate,
            revenue_per_lead=self._calculate_revenue_per_lead(revenue_report, funnel),
            cost_per_acquisition=self._calculate_cost_per_acquisition(revenue_report),
            roi_percentage=self._calculate_roi(revenue_report),
            monthly_recurring_revenue=revenue_report.get("monthly_recurring", 0.0),
            pipeline_velocity_days=self._calculate_pipeline_velocity(revenue_report),
            win_rate=funnel.hot_to_appointment_rate
        )

        # Cache for performance
        await self.realtime_cache.set_cached_metrics(cache_key, asdict(revenue_metrics))

        # Log performance
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"Revenue intelligence calculated in {processing_time:.2f}ms for {location_id}")

        return revenue_metrics

    async def get_market_performance(
        self,
        location_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> MarketPerformanceMetrics:
        """Get market performance and competitive analysis."""
        cache_key = f"market_perf:{location_id}:{start_date}:{end_date}"

        cached_metrics = await self.realtime_cache.get_cached_metrics(cache_key)
        if cached_metrics:
            return MarketPerformanceMetrics(**cached_metrics)

        # Calculate market performance metrics
        exec_summary = self.executive_dashboard.get_executive_summary(location_id)

        market_metrics = MarketPerformanceMetrics(
            market_share_percentage=self._calculate_market_share(location_id),
            lead_quality_index=self._calculate_lead_quality_index(exec_summary),
            property_match_accuracy=self._calculate_property_match_accuracy(location_id),
            client_satisfaction_score=self._calculate_satisfaction_score(location_id),
            time_to_close_avg_days=self._calculate_time_to_close(location_id),
            competitive_win_rate=self._calculate_competitive_win_rate(location_id),
            price_accuracy_percentage=self._calculate_price_accuracy(location_id),
            market_penetration_rate=self._calculate_market_penetration(location_id)
        )

        await self.realtime_cache.set_cached_metrics(cache_key, asdict(market_metrics))
        return market_metrics

    async def get_agent_productivity_kpis(
        self,
        location_id: str,
        agent_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> AgentProductivityKPIs:
        """Get comprehensive agent productivity KPIs."""
        cache_key = f"agent_kpis:{location_id}:{agent_id}:{start_date}:{end_date}"

        cached_metrics = await self.realtime_cache.get_cached_metrics(cache_key)
        if cached_metrics:
            return AgentProductivityKPIs(**cached_metrics)

        # Get base analytics
        response_times = await self.base_analytics.analyze_response_times(location_id, start_date, end_date)
        funnel = await self.base_analytics.get_conversion_funnel(location_id, start_date, end_date)

        # Calculate agent productivity
        agent_kpis = AgentProductivityKPIs(
            contacts_per_day=self._calculate_contacts_per_day(location_id, start_date, end_date),
            qualified_leads_per_day=self._calculate_qualified_leads_per_day(location_id, funnel),
            appointments_booked_per_day=self._calculate_appointments_per_day(location_id, funnel),
            response_time_avg_minutes=response_times.get("avg_response_time_ms", 0) / (1000 * 60),
            conversion_rate_leads_to_appointments=funnel.overall_conversion_rate,
            deals_closed_per_month=self._calculate_deals_per_month(location_id),
            revenue_per_agent_per_month=self._calculate_revenue_per_agent(location_id),
            coaching_sessions_completed=self._get_coaching_sessions(location_id, agent_id),
            ai_assistance_usage_rate=self._calculate_ai_usage_rate(location_id, agent_id),
            performance_score=self._calculate_performance_score(funnel, response_times)
        )

        await self.realtime_cache.set_cached_metrics(cache_key, asdict(agent_kpis))
        return agent_kpis

    async def generate_comprehensive_report(
        self,
        location_id: str,
        report_format: str = "pdf",  # "pdf", "excel", "powerbi"
        include_sections: List[str] = None
    ) -> str:
        """
        Generate comprehensive analytics report in specified format.

        Args:
            location_id: GHL location identifier
            report_format: Output format (pdf, excel, powerbi)
            include_sections: Sections to include (revenue, market, agents, all)

        Returns:
            File path of generated report
        """
        if include_sections is None:
            include_sections = ["revenue", "market", "agents"]

        # Gather all analytics data
        analytics_data = {}

        if "revenue" in include_sections:
            analytics_data["revenue_metrics"] = asdict(
                await self.get_revenue_intelligence(location_id)
            )

        if "market" in include_sections:
            analytics_data["market_performance"] = asdict(
                await self.get_market_performance(location_id)
            )

        if "agents" in include_sections:
            analytics_data["agent_kpis"] = asdict(
                await self.get_agent_productivity_kpis(location_id)
            )

        # Generate report based on format
        if report_format == "pdf":
            return await self.report_generator.generate_revenue_intelligence_pdf(
                analytics_data.get("revenue_metrics", {}), location_id
            )
        elif report_format == "excel":
            return await self.report_generator.generate_excel_dashboard(
                analytics_data, location_id
            )
        elif report_format == "powerbi":
            return await self.report_generator.generate_powerbi_dataset(
                analytics_data, location_id
            )
        else:
            raise ValueError(f"Unsupported report format: {report_format}")

    async def schedule_automated_report(
        self,
        schedule_name: str,
        location_id: str,
        report_type: str,
        frequency: str,
        recipients: List[str] = None
    ) -> str:
        """Schedule automated report generation and delivery."""
        return self.scheduled_reporting.schedule_report(
            schedule_name=schedule_name,
            report_type=report_type,
            location_id=location_id,
            frequency=frequency,
            recipients=recipients or []
        )

    async def process_scheduled_reports(self) -> List[str]:
        """Process all due scheduled reports."""
        return await self.scheduled_reporting.process_scheduled_reports()

    # Helper methods for metric calculations
    def _calculate_revenue_per_lead(self, revenue_report: Dict, funnel) -> float:
        """Calculate revenue per lead metric."""
        total_revenue = revenue_report.get("total_pipeline_value", 0)
        total_leads = funnel.cold_leads + funnel.warm_leads + funnel.hot_leads
        return total_revenue / max(total_leads, 1)

    def _calculate_cost_per_acquisition(self, revenue_report: Dict) -> float:
        """Calculate cost per acquisition."""
        return revenue_report.get("cost_per_acquisition", 0)

    def _calculate_roi(self, revenue_report: Dict) -> float:
        """Calculate return on investment percentage."""
        revenue = revenue_report.get("closed_revenue", 0)
        cost = revenue_report.get("total_cost", 1)
        return ((revenue - cost) / cost) * 100 if cost > 0 else 0

    def _calculate_pipeline_velocity(self, revenue_report: Dict) -> float:
        """Calculate average days for deals to close."""
        return revenue_report.get("avg_deal_cycle_days", 30)

    def _calculate_market_share(self, location_id: str) -> float:
        """Calculate estimated market share percentage."""
        # This would integrate with market data APIs in production
        return 12.5  # Mock value

    def _calculate_lead_quality_index(self, exec_summary: Dict) -> float:
        """Calculate lead quality index (0-1)."""
        metrics = exec_summary.get("metrics", {})
        qualified_rate = metrics.get("qualified_rate", 0.5)
        conversion_rate = metrics.get("conversion_rate", 0.1)
        return (qualified_rate + conversion_rate) / 2

    def _calculate_property_match_accuracy(self, location_id: str) -> float:
        """Calculate property matching accuracy percentage."""
        # This would integrate with property matching service
        return 88.5  # Mock value from existing service

    def _calculate_satisfaction_score(self, location_id: str) -> float:
        """Calculate client satisfaction score."""
        return 4.2  # Mock NPS-style score

    def _calculate_time_to_close(self, location_id: str) -> float:
        """Calculate average time to close in days."""
        return 32.0  # Mock value

    def _calculate_competitive_win_rate(self, location_id: str) -> float:
        """Calculate win rate against competitors."""
        return 0.65  # Mock value

    def _calculate_price_accuracy(self, location_id: str) -> float:
        """Calculate pricing accuracy percentage."""
        return 92.3  # Mock value

    def _calculate_market_penetration(self, location_id: str) -> float:
        """Calculate market penetration rate."""
        return 0.08  # Mock value

    def _calculate_contacts_per_day(self, location_id: str, start_date: str, end_date: str) -> float:
        """Calculate average contacts per day."""
        return 25.0  # Mock value

    def _calculate_qualified_leads_per_day(self, location_id: str, funnel) -> float:
        """Calculate qualified leads per day."""
        return 8.5  # Mock value

    def _calculate_appointments_per_day(self, location_id: str, funnel) -> float:
        """Calculate appointments booked per day."""
        return 2.3  # Mock value

    def _calculate_deals_per_month(self, location_id: str) -> float:
        """Calculate deals closed per month."""
        return 12.0  # Mock value

    def _calculate_revenue_per_agent(self, location_id: str) -> float:
        """Calculate revenue per agent per month."""
        return 45000.0  # Mock value

    def _get_coaching_sessions(self, location_id: str, agent_id: Optional[str]) -> int:
        """Get completed coaching sessions count."""
        return 15  # Mock value

    def _calculate_ai_usage_rate(self, location_id: str, agent_id: Optional[str]) -> float:
        """Calculate AI assistance usage rate."""
        return 0.85  # Mock value

    def _calculate_performance_score(self, funnel, response_times: Dict) -> float:
        """Calculate overall performance score."""
        conversion_score = funnel.overall_conversion_rate * 100
        response_score = max(0, 100 - (response_times.get("avg_response_time_ms", 0) / 1000))
        return (conversion_score + response_score) / 2


# Export main class
__all__ = [
    "EnhancedAnalyticsService",
    "RevenueMetrics",
    "MarketPerformanceMetrics",
    "AgentProductivityKPIs"
]