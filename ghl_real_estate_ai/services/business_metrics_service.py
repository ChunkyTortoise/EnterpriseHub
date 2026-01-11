"""
Business Metrics Service for GHL Real Estate AI Platform.

Comprehensive business intelligence and KPI tracking system that integrates with
GHL webhooks, behavioral learning, and real-time performance monitoring.

Features:
- Real-time GHL integration metrics (webhook success, contact enrichment)
- Business impact KPIs (revenue per lead, conversion rates)
- Agent productivity tracking (deals per agent, performance trends)
- Property matching effectiveness (recommendation acceptance rates)
- AI performance correlation (score accuracy vs. conversions)

Architecture:
- Redis for real-time metrics caching
- PostgreSQL for historical trending
- Event-driven metrics collection from webhook flows
- Service registry integration for behavioral learning correlation
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from enum import Enum

import redis
import asyncpg
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ghl_utils.config import settings

logger = get_logger(__name__)


class MetricType(Enum):
    """Business metric types for categorization and routing."""
    GHL_INTEGRATION = "ghl_integration"
    BUSINESS_IMPACT = "business_impact"
    AGENT_PRODUCTIVITY = "agent_productivity"
    AI_PERFORMANCE = "ai_performance"
    PROPERTY_MATCHING = "property_matching"
    USER_ENGAGEMENT = "user_engagement"
    REVENUE_ATTRIBUTION = "revenue_attribution"


class ConversionStage(Enum):
    """Lead conversion pipeline stages."""
    LEAD_CREATED = "lead_created"
    AI_QUALIFIED = "ai_qualified"
    HUMAN_CONTACTED = "human_contacted"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    PROPERTY_SHOWING = "property_showing"
    OFFER_SUBMITTED = "offer_submitted"
    CONTRACT_SIGNED = "contract_signed"
    DEAL_CLOSED = "deal_closed"


@dataclass
class BusinessMetric:
    """Standard business metric structure."""
    metric_type: MetricType
    name: str
    value: Union[int, float, Decimal]
    timestamp: datetime
    location_id: str
    contact_id: Optional[str] = None
    agent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage and API responses."""
        data = asdict(self)
        data['metric_type'] = self.metric_type.value
        data['timestamp'] = self.timestamp.isoformat()
        if isinstance(self.value, Decimal):
            data['value'] = float(self.value)
        return data


@dataclass
class WebhookPerformanceMetrics:
    """GHL webhook processing performance metrics."""
    total_webhooks: int = 0
    successful_webhooks: int = 0
    failed_webhooks: int = 0
    avg_processing_time: float = 0.0
    contact_enrichment_rate: float = 0.0
    ai_activation_rate: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate webhook success rate percentage."""
        if self.total_webhooks == 0:
            return 0.0
        return (self.successful_webhooks / self.total_webhooks) * 100

    @property
    def meets_sla(self) -> bool:
        """Check if processing time meets <1s SLA."""
        return self.avg_processing_time < 1.0


@dataclass
class BusinessImpactMetrics:
    """Core business impact KPI metrics."""
    total_revenue: Decimal = Decimal('0')
    revenue_per_lead: Decimal = Decimal('0')
    lead_to_conversion_rate: float = 0.0
    avg_deal_size: Decimal = Decimal('0')
    time_to_conversion_days: float = 0.0
    ai_score_correlation: float = 0.0  # Correlation between AI score and conversion

    def calculate_revenue_attribution(
        self,
        ai_assisted_deals: int,
        total_deals: int,
        total_revenue: Decimal
    ) -> Decimal:
        """Calculate revenue attribution to AI assistance."""
        if total_deals == 0:
            return Decimal('0')
        ai_attribution_rate = ai_assisted_deals / total_deals
        return total_revenue * Decimal(str(ai_attribution_rate))


@dataclass
class AgentProductivityMetrics:
    """Agent performance and productivity metrics."""
    agent_id: str
    deals_closed: int = 0
    avg_deal_value: Decimal = Decimal('0')
    conversion_rate: float = 0.0
    response_time_minutes: float = 0.0
    ai_recommendation_usage: float = 0.0
    property_match_effectiveness: float = 0.0

    @property
    def productivity_score(self) -> float:
        """Calculate composite productivity score (0-100)."""
        # Weighted scoring: conversion (40%), response time (20%),
        # deal value (25%), AI usage (15%)
        conversion_score = min(self.conversion_rate * 100, 100)
        response_score = max(100 - (self.response_time_minutes / 60) * 100, 0)
        deal_score = min(float(self.avg_deal_value) / 10000, 100)  # $10k = 100%
        ai_score = self.ai_recommendation_usage * 100

        return (
            conversion_score * 0.4 +
            response_score * 0.2 +
            deal_score * 0.25 +
            ai_score * 0.15
        )


class BusinessMetricsService:
    """
    Comprehensive business metrics tracking and analytics service.

    Provides real-time metrics collection, historical analysis, and
    business intelligence for the GHL Real Estate AI platform.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        postgres_url: Optional[str] = None
    ):
        """
        Initialize business metrics service.

        Args:
            redis_url: Redis connection string for real-time caching
            postgres_url: PostgreSQL connection string for historical data
        """
        self.redis_url = redis_url or settings.redis_url
        self.postgres_url = postgres_url or settings.database_url

        # Initialize connections
        self.redis_client = None
        self.pg_pool = None

        # Performance tracking
        self._webhook_start_times: Dict[str, float] = {}
        self._daily_metrics_cache: Dict[str, Dict] = {}

        logger.info("BusinessMetricsService initialized")

    async def initialize(self) -> None:
        """Initialize database connections."""
        try:
            # Initialize Redis connection
            if self.redis_url:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.ping
                )
                logger.info("Redis connection established for metrics")

            # Initialize PostgreSQL connection pool
            if self.postgres_url:
                self.pg_pool = await asyncpg.create_pool(
                    self.postgres_url,
                    min_size=2,
                    max_size=10,
                    command_timeout=60
                )
                logger.info("PostgreSQL pool created for metrics")

                # Create metrics tables
                await self._create_metrics_tables()

        except Exception as e:
            logger.error(f"Failed to initialize business metrics service: {e}")
            # Continue in fallback mode without persistence

    async def _create_metrics_tables(self) -> None:
        """Create metrics storage tables if they don't exist."""
        if not self.pg_pool:
            return

        async with self.pg_pool.acquire() as conn:
            # Business metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS business_metrics (
                    id SERIAL PRIMARY KEY,
                    metric_type VARCHAR(50) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    value DECIMAL(15,2) NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    location_id VARCHAR(50) NOT NULL,
                    contact_id VARCHAR(50),
                    agent_id VARCHAR(50),
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            # Webhook performance tracking
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS webhook_performance (
                    id SERIAL PRIMARY KEY,
                    location_id VARCHAR(50) NOT NULL,
                    contact_id VARCHAR(50),
                    webhook_type VARCHAR(50),
                    processing_time_ms INTEGER,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    timestamp TIMESTAMPTZ NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            # Conversion pipeline tracking
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversion_pipeline (
                    id SERIAL PRIMARY KEY,
                    contact_id VARCHAR(50) NOT NULL,
                    location_id VARCHAR(50) NOT NULL,
                    stage VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    ai_score INTEGER,
                    agent_id VARCHAR(50),
                    deal_value DECIMAL(15,2),
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)

            # Agent performance tracking
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_performance (
                    id SERIAL PRIMARY KEY,
                    agent_id VARCHAR(50) NOT NULL,
                    location_id VARCHAR(50) NOT NULL,
                    metric_date DATE NOT NULL,
                    deals_closed INTEGER DEFAULT 0,
                    total_deal_value DECIMAL(15,2) DEFAULT 0,
                    leads_contacted INTEGER DEFAULT 0,
                    ai_recommendations_used INTEGER DEFAULT 0,
                    avg_response_time_minutes DECIMAL(8,2) DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(agent_id, location_id, metric_date)
                );
            """)

            # Create indexes for performance
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_business_metrics_location_date
                ON business_metrics(location_id, date_trunc('day', timestamp));
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_webhook_performance_location_date
                ON webhook_performance(location_id, date_trunc('day', timestamp));
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversion_pipeline_contact
                ON conversion_pipeline(contact_id, timestamp);
            """)

            logger.info("Business metrics tables created/verified")

    # ========================================================================
    # GHL Integration Metrics
    # ========================================================================

    async def track_webhook_start(
        self,
        location_id: str,
        contact_id: str,
        webhook_type: str = "message"
    ) -> str:
        """
        Start tracking webhook processing time.

        Args:
            location_id: GHL location identifier
            contact_id: GHL contact identifier
            webhook_type: Type of webhook being processed

        Returns:
            Tracking ID for this webhook processing
        """
        tracking_id = f"{location_id}_{contact_id}_{int(time.time() * 1000)}"
        self._webhook_start_times[tracking_id] = time.time()

        # Track webhook received count
        await self._increment_redis_metric(
            f"webhooks_received:{location_id}:{datetime.now().strftime('%Y-%m-%d')}",
            1
        )

        return tracking_id

    async def track_webhook_completion(
        self,
        tracking_id: str,
        location_id: str,
        contact_id: str,
        success: bool,
        error_message: Optional[str] = None,
        webhook_type: str = "message",
        enrichment_data: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Complete webhook tracking and record performance metrics.

        Args:
            tracking_id: Tracking ID from webhook start
            location_id: GHL location identifier
            contact_id: GHL contact identifier
            success: Whether webhook processing succeeded
            error_message: Error message if failed
            webhook_type: Type of webhook processed
            enrichment_data: Data about contact enrichment performed

        Returns:
            Processing time in milliseconds
        """
        start_time = self._webhook_start_times.pop(tracking_id, time.time())
        processing_time_ms = (time.time() - start_time) * 1000

        # Store webhook performance record
        if self.pg_pool:
            try:
                async with self.pg_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO webhook_performance
                        (location_id, contact_id, webhook_type, processing_time_ms,
                         success, error_message, timestamp)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, location_id, contact_id, webhook_type, int(processing_time_ms),
                    success, error_message, datetime.now())
            except Exception as e:
                logger.error(f"Failed to store webhook performance: {e}")

        # Update Redis metrics
        date_key = datetime.now().strftime('%Y-%m-%d')

        if success:
            await self._increment_redis_metric(
                f"webhooks_successful:{location_id}:{date_key}", 1
            )

            # Track contact enrichment if data was added
            if enrichment_data:
                enrichment_count = len([k for k, v in enrichment_data.items()
                                      if v is not None and v != ""])
                if enrichment_count > 0:
                    await self._increment_redis_metric(
                        f"contacts_enriched:{location_id}:{date_key}", 1
                    )
        else:
            await self._increment_redis_metric(
                f"webhooks_failed:{location_id}:{date_key}", 1
            )

        # Update processing time running average
        await self._update_redis_average(
            f"webhook_processing_time:{location_id}:{date_key}",
            processing_time_ms
        )

        # Business metric record
        metric = BusinessMetric(
            metric_type=MetricType.GHL_INTEGRATION,
            name="webhook_processing_time",
            value=processing_time_ms,
            timestamp=datetime.now(),
            location_id=location_id,
            contact_id=contact_id,
            metadata={
                "success": success,
                "webhook_type": webhook_type,
                "enrichment_fields": len(enrichment_data) if enrichment_data else 0
            }
        )
        await self.record_metric(metric)

        logger.info(
            f"Webhook tracking completed: {processing_time_ms:.1f}ms "
            f"(success={success}, location={location_id})"
        )

        return processing_time_ms

    async def get_webhook_performance_metrics(
        self,
        location_id: str,
        days: int = 7
    ) -> WebhookPerformanceMetrics:
        """
        Get webhook performance metrics for a location.

        Args:
            location_id: GHL location identifier
            days: Number of days to analyze (default: 7)

        Returns:
            WebhookPerformanceMetrics instance with aggregated data
        """
        if not self.pg_pool:
            return WebhookPerformanceMetrics()

        try:
            async with self.pg_pool.acquire() as conn:
                since_date = datetime.now() - timedelta(days=days)

                # Get webhook statistics
                stats = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_webhooks,
                        SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful_webhooks,
                        SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed_webhooks,
                        AVG(processing_time_ms) as avg_processing_time_ms
                    FROM webhook_performance
                    WHERE location_id = $1 AND timestamp >= $2
                """, location_id, since_date)

                # Get enrichment rate
                enriched_contacts = await conn.fetchval("""
                    SELECT COUNT(DISTINCT contact_id)
                    FROM webhook_performance
                    WHERE location_id = $1 AND timestamp >= $2 AND success = true
                """, location_id, since_date) or 0

                total_contacts = await conn.fetchval("""
                    SELECT COUNT(DISTINCT contact_id)
                    FROM webhook_performance
                    WHERE location_id = $1 AND timestamp >= $2
                """, location_id, since_date) or 0

                # Get AI activation rate from Redis
                ai_activations = await self._get_redis_sum(
                    f"ai_activations:{location_id}",
                    days=days
                ) or 0

                return WebhookPerformanceMetrics(
                    total_webhooks=stats['total_webhooks'] or 0,
                    successful_webhooks=stats['successful_webhooks'] or 0,
                    failed_webhooks=stats['failed_webhooks'] or 0,
                    avg_processing_time=(stats['avg_processing_time_ms'] or 0) / 1000.0,
                    contact_enrichment_rate=(
                        enriched_contacts / total_contacts * 100
                        if total_contacts > 0 else 0.0
                    ),
                    ai_activation_rate=(
                        ai_activations / (stats['total_webhooks'] or 1) * 100
                    )
                )

        except Exception as e:
            logger.error(f"Error getting webhook performance metrics: {e}")
            return WebhookPerformanceMetrics()

    # ========================================================================
    # Business Impact Metrics
    # ========================================================================

    async def track_conversion_stage(
        self,
        contact_id: str,
        location_id: str,
        stage: ConversionStage,
        ai_score: Optional[int] = None,
        agent_id: Optional[str] = None,
        deal_value: Optional[Decimal] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track lead progression through conversion pipeline.

        Args:
            contact_id: GHL contact identifier
            location_id: GHL location identifier
            stage: Current conversion stage
            ai_score: AI lead score (if available)
            agent_id: Agent handling the lead
            deal_value: Deal value (for closed deals)
            metadata: Additional tracking data
        """
        if self.pg_pool:
            try:
                async with self.pg_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO conversion_pipeline
                        (contact_id, location_id, stage, timestamp, ai_score,
                         agent_id, deal_value, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, contact_id, location_id, stage.value, datetime.now(),
                    ai_score, agent_id, deal_value,
                    json.dumps(metadata) if metadata else None)
            except Exception as e:
                logger.error(f"Failed to track conversion stage: {e}")

        # Update Redis counters
        date_key = datetime.now().strftime('%Y-%m-%d')
        await self._increment_redis_metric(
            f"conversions:{stage.value}:{location_id}:{date_key}", 1
        )

        if stage == ConversionStage.DEAL_CLOSED and deal_value:
            await self._increment_redis_metric(
                f"revenue:{location_id}:{date_key}", float(deal_value)
            )

        # Record business metric
        metric = BusinessMetric(
            metric_type=MetricType.BUSINESS_IMPACT,
            name=f"conversion_{stage.value}",
            value=1,
            timestamp=datetime.now(),
            location_id=location_id,
            contact_id=contact_id,
            agent_id=agent_id,
            metadata={
                "ai_score": ai_score,
                "deal_value": float(deal_value) if deal_value else None,
                **(metadata or {})
            }
        )
        await self.record_metric(metric)

        logger.info(
            f"Conversion stage tracked: {contact_id} -> {stage.value} "
            f"(score={ai_score}, value={deal_value})"
        )

    async def calculate_revenue_per_lead(
        self,
        location_id: str,
        days: int = 30
    ) -> Decimal:
        """
        Calculate revenue per lead for a location and time period.

        Args:
            location_id: GHL location identifier
            days: Number of days to analyze

        Returns:
            Revenue per lead as Decimal
        """
        if not self.pg_pool:
            return Decimal('0')

        try:
            async with self.pg_pool.acquire() as conn:
                since_date = datetime.now() - timedelta(days=days)

                # Get total revenue from closed deals
                total_revenue = await conn.fetchval("""
                    SELECT COALESCE(SUM(deal_value), 0)
                    FROM conversion_pipeline
                    WHERE location_id = $1
                      AND stage = $2
                      AND timestamp >= $3
                      AND deal_value IS NOT NULL
                """, location_id, ConversionStage.DEAL_CLOSED.value, since_date) or 0

                # Get total unique leads created
                total_leads = await conn.fetchval("""
                    SELECT COUNT(DISTINCT contact_id)
                    FROM conversion_pipeline
                    WHERE location_id = $1
                      AND stage = $2
                      AND timestamp >= $3
                """, location_id, ConversionStage.LEAD_CREATED.value, since_date) or 0

                if total_leads == 0:
                    return Decimal('0')

                return Decimal(str(total_revenue)) / Decimal(str(total_leads))

        except Exception as e:
            logger.error(f"Error calculating revenue per lead: {e}")
            return Decimal('0')

    async def get_business_impact_metrics(
        self,
        location_id: str,
        days: int = 30
    ) -> BusinessImpactMetrics:
        """
        Get comprehensive business impact metrics.

        Args:
            location_id: GHL location identifier
            days: Number of days to analyze

        Returns:
            BusinessImpactMetrics with calculated values
        """
        if not self.pg_pool:
            return BusinessImpactMetrics()

        try:
            async with self.pg_pool.acquire() as conn:
                since_date = datetime.now() - timedelta(days=days)

                # Calculate core metrics
                revenue_stats = await conn.fetchrow("""
                    SELECT
                        COALESCE(SUM(deal_value), 0) as total_revenue,
                        COALESCE(AVG(deal_value), 0) as avg_deal_size,
                        COUNT(*) as closed_deals
                    FROM conversion_pipeline
                    WHERE location_id = $1
                      AND stage = $2
                      AND timestamp >= $3
                      AND deal_value IS NOT NULL
                """, location_id, ConversionStage.DEAL_CLOSED.value, since_date)

                # Get lead counts
                total_leads = await conn.fetchval("""
                    SELECT COUNT(DISTINCT contact_id)
                    FROM conversion_pipeline
                    WHERE location_id = $1
                      AND stage = $2
                      AND timestamp >= $3
                """, location_id, ConversionStage.LEAD_CREATED.value, since_date) or 0

                # Calculate conversion rate
                conversion_rate = 0.0
                if total_leads > 0:
                    conversion_rate = (revenue_stats['closed_deals'] / total_leads) * 100

                # Calculate revenue per lead
                revenue_per_lead = Decimal('0')
                if total_leads > 0:
                    revenue_per_lead = (
                        Decimal(str(revenue_stats['total_revenue'])) /
                        Decimal(str(total_leads))
                    )

                # Calculate average time to conversion
                avg_conversion_time = await conn.fetchval("""
                    SELECT AVG(
                        EXTRACT(EPOCH FROM (closed.timestamp - created.timestamp)) / 86400
                    )
                    FROM conversion_pipeline closed
                    JOIN conversion_pipeline created ON created.contact_id = closed.contact_id
                    WHERE closed.location_id = $1
                      AND closed.stage = $2
                      AND created.stage = $3
                      AND closed.timestamp >= $4
                """, location_id, ConversionStage.DEAL_CLOSED.value,
                ConversionStage.LEAD_CREATED.value, since_date) or 0.0

                # Calculate AI score correlation
                ai_correlation = await self._calculate_ai_score_correlation(
                    location_id, since_date
                )

                return BusinessImpactMetrics(
                    total_revenue=Decimal(str(revenue_stats['total_revenue'])),
                    revenue_per_lead=revenue_per_lead,
                    lead_to_conversion_rate=conversion_rate,
                    avg_deal_size=Decimal(str(revenue_stats['avg_deal_size'])),
                    time_to_conversion_days=float(avg_conversion_time),
                    ai_score_correlation=ai_correlation
                )

        except Exception as e:
            logger.error(f"Error getting business impact metrics: {e}")
            return BusinessImpactMetrics()

    async def _calculate_ai_score_correlation(
        self,
        location_id: str,
        since_date: datetime
    ) -> float:
        """Calculate correlation between AI scores and conversion success."""
        if not self.pg_pool:
            return 0.0

        try:
            async with self.pg_pool.acquire() as conn:
                # Get AI scores for converted and non-converted leads
                converted_scores = await conn.fetch("""
                    SELECT DISTINCT c.ai_score
                    FROM conversion_pipeline c
                    WHERE c.location_id = $1
                      AND c.timestamp >= $2
                      AND c.ai_score IS NOT NULL
                      AND EXISTS (
                          SELECT 1 FROM conversion_pipeline c2
                          WHERE c2.contact_id = c.contact_id
                            AND c2.stage = $3
                      )
                """, location_id, since_date, ConversionStage.DEAL_CLOSED.value)

                non_converted_scores = await conn.fetch("""
                    SELECT DISTINCT c.ai_score
                    FROM conversion_pipeline c
                    WHERE c.location_id = $1
                      AND c.timestamp >= $2
                      AND c.ai_score IS NOT NULL
                      AND NOT EXISTS (
                          SELECT 1 FROM conversion_pipeline c2
                          WHERE c2.contact_id = c.contact_id
                            AND c2.stage = $3
                      )
                """, location_id, since_date, ConversionStage.DEAL_CLOSED.value)

                if not converted_scores or not non_converted_scores:
                    return 0.0

                # Simple correlation: difference in average scores
                converted_avg = sum(r['ai_score'] for r in converted_scores) / len(converted_scores)
                non_converted_avg = sum(r['ai_score'] for r in non_converted_scores) / len(non_converted_scores)

                # Return normalized correlation (-1 to 1)
                if converted_avg > non_converted_avg:
                    return min((converted_avg - non_converted_avg) / 100.0, 1.0)
                else:
                    return max((converted_avg - non_converted_avg) / 100.0, -1.0)

        except Exception as e:
            logger.error(f"Error calculating AI score correlation: {e}")
            return 0.0

    # ========================================================================
    # Agent Productivity Metrics
    # ========================================================================

    async def track_agent_activity(
        self,
        agent_id: str,
        location_id: str,
        activity_type: str,
        contact_id: Optional[str] = None,
        deal_value: Optional[Decimal] = None,
        response_time_minutes: Optional[float] = None,
        ai_recommendation_used: bool = False
    ) -> None:
        """
        Track agent activity and performance metrics.

        Args:
            agent_id: Agent identifier
            location_id: GHL location identifier
            activity_type: Type of activity (contact, deal_closed, etc.)
            contact_id: Contact involved (if applicable)
            deal_value: Deal value for closed deals
            response_time_minutes: Response time in minutes
            ai_recommendation_used: Whether agent used AI recommendation
        """
        date_key = datetime.now().date()

        if self.pg_pool:
            try:
                async with self.pg_pool.acquire() as conn:
                    # Upsert daily agent performance
                    await conn.execute("""
                        INSERT INTO agent_performance
                        (agent_id, location_id, metric_date, deals_closed,
                         total_deal_value, leads_contacted, ai_recommendations_used,
                         avg_response_time_minutes)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (agent_id, location_id, metric_date)
                        DO UPDATE SET
                            deals_closed = agent_performance.deals_closed + EXCLUDED.deals_closed,
                            total_deal_value = agent_performance.total_deal_value + EXCLUDED.total_deal_value,
                            leads_contacted = agent_performance.leads_contacted + EXCLUDED.leads_contacted,
                            ai_recommendations_used = agent_performance.ai_recommendations_used + EXCLUDED.ai_recommendations_used,
                            avg_response_time_minutes = (
                                agent_performance.avg_response_time_minutes + EXCLUDED.avg_response_time_minutes
                            ) / 2
                    """, agent_id, location_id, date_key,
                    1 if activity_type == 'deal_closed' else 0,
                    deal_value or Decimal('0'),
                    1 if activity_type == 'contact' else 0,
                    1 if ai_recommendation_used else 0,
                    response_time_minutes or 0.0)

            except Exception as e:
                logger.error(f"Failed to track agent activity: {e}")

        # Update Redis metrics
        redis_date = datetime.now().strftime('%Y-%m-%d')

        if activity_type == 'deal_closed' and deal_value:
            await self._increment_redis_metric(
                f"agent_deals:{agent_id}:{redis_date}", 1
            )
            await self._increment_redis_metric(
                f"agent_revenue:{agent_id}:{redis_date}", float(deal_value)
            )

        if ai_recommendation_used:
            await self._increment_redis_metric(
                f"agent_ai_usage:{agent_id}:{redis_date}", 1
            )

        if response_time_minutes:
            await self._update_redis_average(
                f"agent_response_time:{agent_id}:{redis_date}",
                response_time_minutes
            )

        # Record business metric
        metric = BusinessMetric(
            metric_type=MetricType.AGENT_PRODUCTIVITY,
            name=f"agent_{activity_type}",
            value=deal_value or 1,
            timestamp=datetime.now(),
            location_id=location_id,
            contact_id=contact_id,
            agent_id=agent_id,
            metadata={
                "response_time_minutes": response_time_minutes,
                "ai_recommendation_used": ai_recommendation_used
            }
        )
        await self.record_metric(metric)

    async def get_agent_productivity_metrics(
        self,
        agent_id: str,
        location_id: str,
        days: int = 30
    ) -> AgentProductivityMetrics:
        """
        Get comprehensive agent productivity metrics.

        Args:
            agent_id: Agent identifier
            location_id: GHL location identifier
            days: Number of days to analyze

        Returns:
            AgentProductivityMetrics with calculated values
        """
        if not self.pg_pool:
            return AgentProductivityMetrics(agent_id=agent_id)

        try:
            async with self.pg_pool.acquire() as conn:
                since_date = datetime.now().date() - timedelta(days=days)

                # Get aggregated performance data
                perf_data = await conn.fetchrow("""
                    SELECT
                        SUM(deals_closed) as total_deals,
                        AVG(total_deal_value / NULLIF(deals_closed, 0)) as avg_deal_value,
                        SUM(leads_contacted) as total_contacts,
                        AVG(avg_response_time_minutes) as avg_response_time,
                        SUM(ai_recommendations_used) as total_ai_usage
                    FROM agent_performance
                    WHERE agent_id = $1
                      AND location_id = $2
                      AND metric_date >= $3
                """, agent_id, location_id, since_date)

                # Calculate conversion rate
                conversion_rate = 0.0
                if perf_data['total_contacts'] and perf_data['total_contacts'] > 0:
                    conversion_rate = (
                        (perf_data['total_deals'] or 0) /
                        perf_data['total_contacts'] * 100
                    )

                # Calculate AI recommendation usage rate
                ai_usage_rate = 0.0
                if perf_data['total_contacts'] and perf_data['total_contacts'] > 0:
                    ai_usage_rate = (
                        (perf_data['total_ai_usage'] or 0) /
                        perf_data['total_contacts']
                    )

                # Get property match effectiveness from recent recommendations
                match_effectiveness = await self._calculate_property_match_effectiveness(
                    agent_id, location_id, since_date
                )

                return AgentProductivityMetrics(
                    agent_id=agent_id,
                    deals_closed=perf_data['total_deals'] or 0,
                    avg_deal_value=Decimal(str(perf_data['avg_deal_value'] or 0)),
                    conversion_rate=conversion_rate,
                    response_time_minutes=float(perf_data['avg_response_time'] or 0),
                    ai_recommendation_usage=ai_usage_rate,
                    property_match_effectiveness=match_effectiveness
                )

        except Exception as e:
            logger.error(f"Error getting agent productivity metrics: {e}")
            return AgentProductivityMetrics(agent_id=agent_id)

    async def _calculate_property_match_effectiveness(
        self,
        agent_id: str,
        location_id: str,
        since_date: datetime.date
    ) -> float:
        """Calculate how effective property matches are for this agent."""
        try:
            # This would integrate with property matching service
            # For now, return a calculated value based on closed deals
            if self.pg_pool:
                async with self.pg_pool.acquire() as conn:
                    effectiveness = await conn.fetchval("""
                        SELECT
                            COALESCE(
                                SUM(CASE WHEN deal_value > 0 THEN 1 ELSE 0 END)::float /
                                COUNT(*)::float * 100,
                                0
                            )
                        FROM conversion_pipeline
                        WHERE agent_id = $1
                          AND location_id = $2
                          AND date_trunc('day', timestamp) >= $3
                          AND stage IN ($4, $5)
                    """, agent_id, location_id, since_date,
                    ConversionStage.PROPERTY_SHOWING.value,
                    ConversionStage.DEAL_CLOSED.value)

                    return float(effectiveness or 0.0)

        except Exception as e:
            logger.error(f"Error calculating property match effectiveness: {e}")

        return 0.0

    # ========================================================================
    # Property Matching Metrics
    # ========================================================================

    async def track_property_recommendation(
        self,
        contact_id: str,
        location_id: str,
        property_id: str,
        recommendation_score: float,
        agent_id: Optional[str] = None
    ) -> str:
        """
        Track a property recommendation being made to a lead.

        Args:
            contact_id: GHL contact identifier
            location_id: GHL location identifier
            property_id: Property identifier
            recommendation_score: AI confidence score (0-1)
            agent_id: Agent making/approving recommendation

        Returns:
            Recommendation tracking ID
        """
        recommendation_id = f"rec_{contact_id}_{property_id}_{int(time.time())}"

        # Store in Redis with expiration (30 days)
        if self.redis_client:
            try:
                recommendation_data = {
                    "contact_id": contact_id,
                    "location_id": location_id,
                    "property_id": property_id,
                    "score": recommendation_score,
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat(),
                    "status": "pending"
                }

                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.redis_client.setex(
                        f"property_rec:{recommendation_id}",
                        30 * 24 * 60 * 60,  # 30 days
                        json.dumps(recommendation_data)
                    )
                )
            except Exception as e:
                logger.error(f"Failed to cache property recommendation: {e}")

        # Record business metric
        metric = BusinessMetric(
            metric_type=MetricType.PROPERTY_MATCHING,
            name="property_recommendation",
            value=recommendation_score,
            timestamp=datetime.now(),
            location_id=location_id,
            contact_id=contact_id,
            agent_id=agent_id,
            metadata={
                "property_id": property_id,
                "recommendation_id": recommendation_id
            }
        )
        await self.record_metric(metric)

        logger.info(
            f"Property recommendation tracked: {recommendation_id} "
            f"(contact={contact_id}, property={property_id}, score={recommendation_score})"
        )

        return recommendation_id

    async def track_property_interaction(
        self,
        recommendation_id: str,
        interaction_type: str,
        contact_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track user interaction with property recommendation.

        Args:
            recommendation_id: Recommendation tracking ID
            interaction_type: Type of interaction (viewed, liked, scheduled, rejected)
            contact_id: Contact identifier (for validation)
            metadata: Additional interaction data
        """
        # Update recommendation status in Redis
        if self.redis_client:
            try:
                rec_data = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.redis_client.get(f"property_rec:{recommendation_id}")
                )

                if rec_data:
                    rec_dict = json.loads(rec_data)
                    rec_dict["status"] = interaction_type
                    rec_dict["interaction_timestamp"] = datetime.now().isoformat()

                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.redis_client.set(
                            f"property_rec:{recommendation_id}",
                            json.dumps(rec_dict)
                        )
                    )

                    # Track interaction metrics
                    date_key = datetime.now().strftime('%Y-%m-%d')
                    location_id = rec_dict.get("location_id", "unknown")

                    await self._increment_redis_metric(
                        f"property_interactions:{interaction_type}:{location_id}:{date_key}",
                        1
                    )

                    # Calculate recommendation acceptance rate
                    if interaction_type in ["liked", "scheduled"]:
                        await self._increment_redis_metric(
                            f"property_accepted:{location_id}:{date_key}", 1
                        )

            except Exception as e:
                logger.error(f"Failed to track property interaction: {e}")

        logger.info(
            f"Property interaction tracked: {recommendation_id} -> {interaction_type}"
        )

    async def get_property_matching_metrics(
        self,
        location_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get property matching effectiveness metrics.

        Args:
            location_id: GHL location identifier
            days: Number of days to analyze

        Returns:
            Dictionary with property matching KPIs
        """
        metrics = {
            "total_recommendations": 0,
            "acceptance_rate": 0.0,
            "showing_rate": 0.0,
            "avg_recommendation_score": 0.0,
            "top_properties": [],
            "recommendation_trends": []
        }

        try:
            # Get metrics from Redis
            date_range = [
                (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                for i in range(days)
            ]

            total_recommendations = 0
            total_accepted = 0
            total_showings = 0

            for date_key in date_range:
                recs = await self._get_redis_metric(
                    f"property_interactions:pending:{location_id}:{date_key}"
                ) or 0
                accepted = await self._get_redis_metric(
                    f"property_accepted:{location_id}:{date_key}"
                ) or 0
                showings = await self._get_redis_metric(
                    f"property_interactions:scheduled:{location_id}:{date_key}"
                ) or 0

                total_recommendations += recs
                total_accepted += accepted
                total_showings += showings

            # Calculate rates
            if total_recommendations > 0:
                metrics["acceptance_rate"] = (total_accepted / total_recommendations) * 100
                metrics["showing_rate"] = (total_showings / total_recommendations) * 100

            metrics["total_recommendations"] = total_recommendations

            # Get average recommendation scores from business metrics
            if self.pg_pool:
                async with self.pg_pool.acquire() as conn:
                    since_date = datetime.now() - timedelta(days=days)

                    avg_score = await conn.fetchval("""
                        SELECT AVG(value)
                        FROM business_metrics
                        WHERE location_id = $1
                          AND metric_type = $2
                          AND name = 'property_recommendation'
                          AND timestamp >= $3
                    """, location_id, MetricType.PROPERTY_MATCHING.value, since_date)

                    metrics["avg_recommendation_score"] = float(avg_score or 0.0)

        except Exception as e:
            logger.error(f"Error getting property matching metrics: {e}")

        return metrics

    # ========================================================================
    # Core Metrics Infrastructure
    # ========================================================================

    async def record_metric(self, metric: BusinessMetric) -> None:
        """
        Record a business metric to persistent storage.

        Args:
            metric: BusinessMetric instance to store
        """
        if self.pg_pool:
            try:
                async with self.pg_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO business_metrics
                        (metric_type, name, value, timestamp, location_id,
                         contact_id, agent_id, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, metric.metric_type.value, metric.name, float(metric.value),
                    metric.timestamp, metric.location_id, metric.contact_id,
                    metric.agent_id, json.dumps(metric.metadata) if metric.metadata else None)
            except Exception as e:
                logger.error(f"Failed to record business metric: {e}")

    async def _increment_redis_metric(
        self,
        key: str,
        value: Union[int, float]
    ) -> None:
        """Increment a Redis metric value."""
        if not self.redis_client:
            return

        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.incrbyfloat(key, float(value))
            )
            # Set expiration to 90 days for cleanup
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.expire(key, 90 * 24 * 60 * 60)
            )
        except Exception as e:
            logger.error(f"Failed to increment Redis metric {key}: {e}")

    async def _get_redis_metric(self, key: str) -> Optional[float]:
        """Get a Redis metric value."""
        if not self.redis_client:
            return None

        try:
            value = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.get(key)
            )
            return float(value) if value else 0.0
        except Exception as e:
            logger.error(f"Failed to get Redis metric {key}: {e}")
            return None

    async def _update_redis_average(
        self,
        key: str,
        new_value: float
    ) -> None:
        """Update a Redis metric as a running average."""
        if not self.redis_client:
            return

        try:
            # Use a Lua script for atomic average calculation
            lua_script = """
                local key = KEYS[1]
                local new_value = tonumber(ARGV[1])

                local current = redis.call('HGET', key, 'value')
                local count = redis.call('HGET', key, 'count')

                if current == false then
                    current = 0
                    count = 0
                else
                    current = tonumber(current)
                    count = tonumber(count)
                end

                local new_count = count + 1
                local new_avg = (current * count + new_value) / new_count

                redis.call('HSET', key, 'value', new_avg)
                redis.call('HSET', key, 'count', new_count)
                redis.call('EXPIRE', key, 90 * 24 * 60 * 60)

                return new_avg
            """

            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.redis_client.eval(lua_script, 1, key, new_value)
            )
        except Exception as e:
            logger.error(f"Failed to update Redis average {key}: {e}")

    async def _get_redis_sum(
        self,
        key_pattern: str,
        days: int = 7
    ) -> Optional[float]:
        """Get sum of Redis metrics matching a pattern over date range."""
        if not self.redis_client:
            return None

        try:
            total = 0.0
            for i in range(days):
                date_key = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                full_key = f"{key_pattern}:{date_key}"
                value = await self._get_redis_metric(full_key)
                if value:
                    total += value

            return total
        except Exception as e:
            logger.error(f"Failed to get Redis sum for {key_pattern}: {e}")
            return None

    # ========================================================================
    # Dashboard and Reporting
    # ========================================================================

    async def get_executive_dashboard_metrics(
        self,
        location_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive executive dashboard metrics.

        Args:
            location_id: GHL location identifier
            days: Number of days to analyze

        Returns:
            Dictionary with all key business metrics
        """
        try:
            # Get all metric categories in parallel
            webhook_metrics, business_metrics, property_metrics = await asyncio.gather(
                self.get_webhook_performance_metrics(location_id, days),
                self.get_business_impact_metrics(location_id, days),
                self.get_property_matching_metrics(location_id, days),
                return_exceptions=True
            )

            # Handle any exceptions
            if isinstance(webhook_metrics, Exception):
                logger.error(f"Error getting webhook metrics: {webhook_metrics}")
                webhook_metrics = WebhookPerformanceMetrics()

            if isinstance(business_metrics, Exception):
                logger.error(f"Error getting business metrics: {business_metrics}")
                business_metrics = BusinessImpactMetrics()

            if isinstance(property_metrics, Exception):
                logger.error(f"Error getting property metrics: {property_metrics}")
                property_metrics = {}

            # Get top performing agents
            top_agents = await self._get_top_performing_agents(location_id, days)

            return {
                "summary": {
                    "total_revenue": float(business_metrics.total_revenue),
                    "revenue_per_lead": float(business_metrics.revenue_per_lead),
                    "conversion_rate": business_metrics.lead_to_conversion_rate,
                    "avg_deal_size": float(business_metrics.avg_deal_size),
                    "webhook_success_rate": webhook_metrics.success_rate,
                    "property_acceptance_rate": property_metrics.get("acceptance_rate", 0.0)
                },
                "ghl_integration": {
                    "total_webhooks": webhook_metrics.total_webhooks,
                    "success_rate": webhook_metrics.success_rate,
                    "avg_processing_time": webhook_metrics.avg_processing_time,
                    "meets_sla": webhook_metrics.meets_sla,
                    "contact_enrichment_rate": webhook_metrics.contact_enrichment_rate,
                    "ai_activation_rate": webhook_metrics.ai_activation_rate
                },
                "business_impact": {
                    "total_revenue": float(business_metrics.total_revenue),
                    "revenue_per_lead": float(business_metrics.revenue_per_lead),
                    "conversion_rate": business_metrics.lead_to_conversion_rate,
                    "avg_deal_size": float(business_metrics.avg_deal_size),
                    "time_to_conversion": business_metrics.time_to_conversion_days,
                    "ai_score_correlation": business_metrics.ai_score_correlation
                },
                "property_matching": property_metrics,
                "top_agents": top_agents,
                "generated_at": datetime.now().isoformat(),
                "period_days": days
            }

        except Exception as e:
            logger.error(f"Error generating executive dashboard metrics: {e}")
            return {
                "error": "Failed to generate metrics",
                "generated_at": datetime.now().isoformat()
            }

    async def _get_top_performing_agents(
        self,
        location_id: str,
        days: int = 30,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get top performing agents for the location."""
        if not self.pg_pool:
            return []

        try:
            async with self.pg_pool.acquire() as conn:
                since_date = datetime.now().date() - timedelta(days=days)

                agents = await conn.fetch("""
                    SELECT
                        agent_id,
                        SUM(deals_closed) as total_deals,
                        SUM(total_deal_value) as total_revenue,
                        AVG(avg_response_time_minutes) as avg_response_time,
                        SUM(ai_recommendations_used) as ai_usage,
                        SUM(leads_contacted) as contacts
                    FROM agent_performance
                    WHERE location_id = $1 AND metric_date >= $2
                    GROUP BY agent_id
                    ORDER BY total_revenue DESC
                    LIMIT $3
                """, location_id, since_date, limit)

                result = []
                for agent in agents:
                    productivity_metrics = AgentProductivityMetrics(
                        agent_id=agent['agent_id'],
                        deals_closed=agent['total_deals'],
                        avg_deal_value=Decimal(str(agent['total_revenue'] or 0)) / max(agent['total_deals'], 1),
                        conversion_rate=(agent['total_deals'] / max(agent['contacts'], 1)) * 100,
                        response_time_minutes=float(agent['avg_response_time'] or 0),
                        ai_recommendation_usage=(agent['ai_usage'] / max(agent['contacts'], 1))
                    )

                    result.append({
                        "agent_id": agent['agent_id'],
                        "total_deals": agent['total_deals'],
                        "total_revenue": float(agent['total_revenue'] or 0),
                        "productivity_score": productivity_metrics.productivity_score,
                        "conversion_rate": productivity_metrics.conversion_rate,
                        "ai_usage_rate": productivity_metrics.ai_recommendation_usage * 100
                    })

                return result

        except Exception as e:
            logger.error(f"Error getting top performing agents: {e}")
            return []

    async def close(self) -> None:
        """Clean up connections and resources."""
        try:
            if self.redis_client:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.close
                )
                logger.info("Redis connection closed")

            if self.pg_pool:
                await self.pg_pool.close()
                logger.info("PostgreSQL pool closed")

        except Exception as e:
            logger.error(f"Error closing business metrics service: {e}")


# ========================================================================
# Utility Functions
# ========================================================================

async def create_business_metrics_service(
    redis_url: Optional[str] = None,
    postgres_url: Optional[str] = None
) -> BusinessMetricsService:
    """
    Factory function to create and initialize BusinessMetricsService.

    Args:
        redis_url: Redis connection string (optional)
        postgres_url: PostgreSQL connection string (optional)

    Returns:
        Initialized BusinessMetricsService instance
    """
    service = BusinessMetricsService(redis_url, postgres_url)
    await service.initialize()
    return service


def calculate_performance_grade(metrics: Dict[str, float]) -> str:
    """
    Calculate overall performance grade based on key metrics.

    Args:
        metrics: Dictionary of performance metrics

    Returns:
        Letter grade (A+, A, B+, B, C+, C, D, F)
    """
    # Define scoring criteria
    score = 0
    max_score = 0

    # Webhook performance (25%)
    if 'webhook_success_rate' in metrics:
        if metrics['webhook_success_rate'] >= 99:
            score += 25
        elif metrics['webhook_success_rate'] >= 95:
            score += 20
        elif metrics['webhook_success_rate'] >= 90:
            score += 15
        else:
            score += max(0, metrics['webhook_success_rate'] / 90 * 15)
    max_score += 25

    # Conversion rate (30%)
    if 'conversion_rate' in metrics:
        if metrics['conversion_rate'] >= 20:
            score += 30
        elif metrics['conversion_rate'] >= 15:
            score += 25
        elif metrics['conversion_rate'] >= 10:
            score += 20
        else:
            score += max(0, metrics['conversion_rate'] / 10 * 20)
    max_score += 30

    # Revenue per lead (25%)
    if 'revenue_per_lead' in metrics:
        # Normalize based on typical real estate values
        normalized = min(metrics['revenue_per_lead'] / 5000, 1.0)  # $5k = 100%
        score += normalized * 25
    max_score += 25

    # Property acceptance rate (20%)
    if 'property_acceptance_rate' in metrics:
        if metrics['property_acceptance_rate'] >= 60:
            score += 20
        elif metrics['property_acceptance_rate'] >= 40:
            score += 15
        elif metrics['property_acceptance_rate'] >= 20:
            score += 10
        else:
            score += max(0, metrics['property_acceptance_rate'] / 20 * 10)
    max_score += 20

    # Calculate percentage
    if max_score == 0:
        return "N/A"

    percentage = (score / max_score) * 100

    # Assign grades
    if percentage >= 97:
        return "A+"
    elif percentage >= 93:
        return "A"
    elif percentage >= 90:
        return "A-"
    elif percentage >= 87:
        return "B+"
    elif percentage >= 83:
        return "B"
    elif percentage >= 80:
        return "B-"
    elif percentage >= 77:
        return "C+"
    elif percentage >= 73:
        return "C"
    elif percentage >= 70:
        return "C-"
    elif percentage >= 60:
        return "D"
    else:
        return "F"