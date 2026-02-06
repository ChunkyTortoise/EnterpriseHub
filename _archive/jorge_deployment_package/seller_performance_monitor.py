#!/usr/bin/env python3
"""
Seller Performance Monitor - Advanced Analytics Engine

Real-time performance tracking and analytics for Jorge's Seller Bot with
comprehensive business intelligence, SLA compliance monitoring, and
automated reporting capabilities.

Key Features:
- Real-time performance dashboards
- Conversion funnel analysis
- SLA compliance monitoring (5-minute rule, <500ms analysis)
- ROI tracking and commission pipeline analytics
- Automated performance reporting
- Business rule compliance validation

Author: Claude Code Assistant
Created: January 23, 2026
"""

import os
import sys
import asyncio
import logging
import json
import time
import sqlite3
import aiosqlite
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

# Add paths for existing components
sys.path.append("../ghl_real_estate_ai")
sys.path.append(".")

try:
    from seller_models import (
        SellerTemperature, SellerPriority, SellerMetricsResponse,
        SellerAnalysisResponse, SellerBotConfig
    )
    SELLER_MODELS_AVAILABLE = True
except ImportError:
    SELLER_MODELS_AVAILABLE = False

try:
    from claude_concierge_service import ClaudeConciergeService
    CONCIERGE_AVAILABLE = True
except ImportError:
    CONCIERGE_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of performance metrics"""
    RESPONSE_TIME = "response_time"
    CONVERSION_RATE = "conversion_rate"
    BUSINESS_RULE_COMPLIANCE = "business_rule_compliance"
    COMMISSION_PIPELINE = "commission_pipeline"
    ERROR_RATE = "error_rate"
    SLA_COMPLIANCE = "sla_compliance"


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    metric_type: MetricType
    value: float
    target_value: float
    timestamp: datetime
    metadata: Dict[str, Any]

    @property
    def compliance_percentage(self) -> float:
        """Calculate compliance as percentage of target"""
        if self.target_value == 0:
            return 100.0
        return min((self.value / self.target_value) * 100, 100.0)

    @property
    def variance_percentage(self) -> float:
        """Calculate variance from target as percentage"""
        if self.target_value == 0:
            return 0.0
        return ((self.value - self.target_value) / self.target_value) * 100


@dataclass
class ConversionFunnelStage:
    """Conversion funnel stage metrics"""
    stage_name: str
    total_entries: int
    successful_exits: int
    avg_time_in_stage: float
    drop_off_rate: float
    key_actions: List[str]


@dataclass
class BusinessRuleCompliance:
    """Business rule compliance tracking"""
    rule_name: str
    compliance_rate: float
    violations_count: int
    last_violation: Optional[datetime]
    impact_score: float


@dataclass
class PerformanceAlert:
    """Performance alert"""
    alert_id: str
    level: AlertLevel
    metric_type: MetricType
    title: str
    description: str
    current_value: float
    target_value: float
    recommendations: List[str]
    timestamp: datetime
    acknowledged: bool = False


class SellerPerformanceMonitor:
    """Advanced performance monitoring and analytics service"""

    def __init__(self, db_path: str = "seller_performance.db"):
        self.db_path = db_path
        self.performance_cache: Dict[str, Any] = {}
        self.active_alerts: List[PerformanceAlert] = []
        self.conversion_funnel: List[ConversionFunnelStage] = []
        self.business_rules: List[BusinessRuleCompliance] = []
        self.config = SellerBotConfig() if SELLER_MODELS_AVAILABLE else None

        # Initialize concierge service if available
        self.concierge = ClaudeConciergeService() if CONCIERGE_AVAILABLE else None

    async def initialize(self):
        """Initialize the performance monitor"""
        await self._create_database_tables()
        await self._load_performance_targets()
        logger.info("Seller Performance Monitor initialized")

    async def _create_database_tables(self):
        """Create database tables for performance tracking"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS seller_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_id TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    message_content TEXT,
                    analysis_time_ms REAL,
                    temperature TEXT,
                    priority TEXT,
                    questions_answered INTEGER,
                    business_rules_passed BOOLEAN,
                    commission_potential REAL,
                    error_occurred BOOLEAN,
                    error_message TEXT
                )
            ''')

            await db.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    target_value REAL,
                    metadata TEXT
                )
            ''')

            await db.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE NOT NULL,
                    level TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    current_value REAL,
                    target_value REAL,
                    recommendations TEXT,
                    timestamp DATETIME NOT NULL,
                    acknowledged BOOLEAN DEFAULT FALSE
                )
            ''')

            await db.commit()

    async def _load_performance_targets(self):
        """Load Jorge's performance targets and business rules"""
        self.targets = {
            "response_time_ms": 500,
            "webhook_timeout_ms": 2000,
            "hot_conversion_rate": 0.20,  # 20% of sellers should reach HOT
            "warm_conversion_rate": 0.50,  # 50% should reach WARM
            "five_minute_rule_compliance": 0.99,  # 99% compliance
            "error_rate": 0.02,  # <2% error rate
            "commission_per_seller": 25000,  # Target commission potential
            "business_rule_compliance": 0.95  # 95% business rule compliance
        }

        # Initialize conversion funnel stages
        self.conversion_funnel = [
            ConversionFunnelStage("Initial Contact", 0, 0, 0.0, 0.0, ["Message received"]),
            ConversionFunnelStage("Qualification Started", 0, 0, 0.0, 0.0, ["First question answered"]),
            ConversionFunnelStage("Warm Seller", 0, 0, 0.0, 0.0, ["2+ questions answered"]),
            ConversionFunnelStage("Hot Seller", 0, 0, 0.0, 0.0, ["4 questions completed"]),
            ConversionFunnelStage("Qualified Lead", 0, 0, 0.0, 0.0, ["Business rules passed"])
        ]

        # Initialize business rules
        self.business_rules = [
            BusinessRuleCompliance("Budget Range Validation", 0.0, 0, None, 0.9),
            BusinessRuleCompliance("Service Area Validation", 0.0, 0, None, 0.8),
            BusinessRuleCompliance("Timeline Validation", 0.0, 0, None, 0.7),
            BusinessRuleCompliance("Response Time SLA", 0.0, 0, None, 1.0)
        ]

    async def record_seller_interaction(self, interaction_data: Dict[str, Any]):
        """Record a seller interaction for performance tracking"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO seller_interactions (
                        contact_id, timestamp, message_content, analysis_time_ms,
                        temperature, priority, questions_answered, business_rules_passed,
                        commission_potential, error_occurred, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    interaction_data.get('contact_id'),
                    datetime.now(),
                    interaction_data.get('message', '')[:500],  # Truncate for storage
                    interaction_data.get('analysis_time_ms', 0),
                    interaction_data.get('temperature'),
                    interaction_data.get('priority'),
                    interaction_data.get('questions_answered', 0),
                    interaction_data.get('business_rules_passed', False),
                    interaction_data.get('commission_potential', 0.0),
                    interaction_data.get('error_occurred', False),
                    interaction_data.get('error_message')
                ))
                await db.commit()

            # Update real-time metrics
            await self._update_real_time_metrics(interaction_data)

            # Check for alerts
            await self._check_performance_alerts(interaction_data)

        except Exception as e:
            logger.error(f"Failed to record seller interaction: {e}")

    async def _update_real_time_metrics(self, interaction_data: Dict[str, Any]):
        """Update real-time performance metrics"""

        # Update response time metrics
        analysis_time = interaction_data.get('analysis_time_ms', 0)
        await self._record_metric(
            MetricType.RESPONSE_TIME,
            analysis_time,
            self.targets["response_time_ms"],
            {"contact_id": interaction_data.get('contact_id')}
        )

        # Update conversion funnel
        await self._update_conversion_funnel(interaction_data)

        # Update business rule compliance
        await self._update_business_rule_compliance(interaction_data)

    async def _update_conversion_funnel(self, interaction_data: Dict[str, Any]):
        """Update conversion funnel metrics"""
        questions_answered = interaction_data.get('questions_answered', 0)
        temperature = interaction_data.get('temperature')

        # Update funnel stages based on progress
        for i, stage in enumerate(self.conversion_funnel):
            stage.total_entries += 1

            # Determine if this interaction succeeded in this stage
            if i == 0:  # Initial Contact - all interactions start here
                stage.successful_exits += 1
            elif i == 1 and questions_answered >= 1:  # Qualification Started
                stage.successful_exits += 1
            elif i == 2 and temperature in ['WARM', 'HOT']:  # Warm Seller
                stage.successful_exits += 1
            elif i == 3 and temperature == 'HOT':  # Hot Seller
                stage.successful_exits += 1
            elif i == 4 and interaction_data.get('business_rules_passed'):  # Qualified
                stage.successful_exits += 1

            # Calculate drop-off rate
            if stage.total_entries > 0:
                stage.drop_off_rate = 1.0 - (stage.successful_exits / stage.total_entries)

    async def _update_business_rule_compliance(self, interaction_data: Dict[str, Any]):
        """Update business rule compliance tracking"""

        # Response Time SLA
        analysis_time = interaction_data.get('analysis_time_ms', 0)
        sla_rule = next(r for r in self.business_rules if r.rule_name == "Response Time SLA")

        if analysis_time <= self.targets["response_time_ms"]:
            sla_rule.compliance_rate = (sla_rule.compliance_rate + 1) / 2  # Rolling average
        else:
            sla_rule.violations_count += 1
            sla_rule.last_violation = datetime.now()
            sla_rule.compliance_rate = (sla_rule.compliance_rate + 0) / 2

    async def _record_metric(
        self,
        metric_type: MetricType,
        value: float,
        target: float,
        metadata: Dict[str, Any]
    ):
        """Record a performance metric"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO performance_metrics (timestamp, metric_type, metric_value, target_value, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (datetime.now(), metric_type.value, value, target, json.dumps(metadata)))
            await db.commit()

    async def _check_performance_alerts(self, interaction_data: Dict[str, Any]):
        """Check for performance alerts based on interaction"""

        # Response time alert
        analysis_time = interaction_data.get('analysis_time_ms', 0)
        if analysis_time > self.targets["response_time_ms"] * 1.5:  # 50% over target
            await self._create_alert(
                AlertLevel.WARNING,
                MetricType.RESPONSE_TIME,
                "Response Time Above Target",
                f"Analysis took {analysis_time:.0f}ms (target: {self.targets['response_time_ms']}ms)",
                analysis_time,
                self.targets["response_time_ms"],
                [
                    "Enable response caching",
                    "Optimize Claude API calls",
                    "Review system resource usage"
                ]
            )

        # Error rate alert
        if interaction_data.get('error_occurred'):
            await self._create_alert(
                AlertLevel.CRITICAL,
                MetricType.ERROR_RATE,
                "Seller Analysis Error",
                f"Error in analysis: {interaction_data.get('error_message', 'Unknown error')}",
                1.0,
                0.0,
                [
                    "Check seller analysis pipeline",
                    "Verify GHL integration",
                    "Review error logs for patterns"
                ]
            )

    async def _create_alert(
        self,
        level: AlertLevel,
        metric_type: MetricType,
        title: str,
        description: str,
        current_value: float,
        target_value: float,
        recommendations: List[str]
    ):
        """Create a performance alert"""
        alert_id = f"{metric_type.value}_{int(time.time())}"

        alert = PerformanceAlert(
            alert_id=alert_id,
            level=level,
            metric_type=metric_type,
            title=title,
            description=description,
            current_value=current_value,
            target_value=target_value,
            recommendations=recommendations,
            timestamp=datetime.now()
        )

        self.active_alerts.append(alert)

        # Store in database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO alerts (
                    alert_id, level, metric_type, title, description,
                    current_value, target_value, recommendations, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.alert_id, alert.level.value, alert.metric_type.value,
                alert.title, alert.description, alert.current_value,
                alert.target_value, json.dumps(alert.recommendations),
                alert.timestamp
            ))
            await db.commit()

        logger.warning(f"Performance Alert: {level.value} - {title}")

    async def get_performance_dashboard_data(
        self,
        timeframe: str = "24h"
    ) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data"""

        # Calculate timeframe
        if timeframe == "24h":
            since = datetime.now() - timedelta(hours=24)
        elif timeframe == "7d":
            since = datetime.now() - timedelta(days=7)
        elif timeframe == "30d":
            since = datetime.now() - timedelta(days=30)
        else:
            since = datetime.now() - timedelta(hours=24)

        # Get performance metrics from database
        async with aiosqlite.connect(self.db_path) as db:
            # Response time metrics
            cursor = await db.execute('''
                SELECT AVG(analysis_time_ms), COUNT(*) FROM seller_interactions
                WHERE timestamp > ?
            ''', (since,))
            avg_response_time, interaction_count = await cursor.fetchone()

            # Temperature distribution
            cursor = await db.execute('''
                SELECT temperature, COUNT(*) FROM seller_interactions
                WHERE timestamp > ? AND temperature IS NOT NULL
                GROUP BY temperature
            ''', (since,))
            temperature_dist = dict(await cursor.fetchall())

            # Conversion rates
            cursor = await db.execute('''
                SELECT
                    AVG(CASE WHEN temperature = 'HOT' THEN 1.0 ELSE 0.0 END) as hot_rate,
                    AVG(CASE WHEN temperature IN ('HOT', 'WARM') THEN 1.0 ELSE 0.0 END) as warm_plus_rate,
                    AVG(CASE WHEN business_rules_passed = 1 THEN 1.0 ELSE 0.0 END) as qualified_rate
                FROM seller_interactions
                WHERE timestamp > ?
            ''', (since,))
            hot_rate, warm_plus_rate, qualified_rate = await cursor.fetchone()

            # Commission pipeline
            cursor = await db.execute('''
                SELECT SUM(commission_potential), AVG(commission_potential)
                FROM seller_interactions
                WHERE timestamp > ? AND commission_potential > 0
            ''', (since,))
            total_commission, avg_commission = await cursor.fetchone()

            # Error rate
            cursor = await db.execute('''
                SELECT AVG(CASE WHEN error_occurred = 1 THEN 1.0 ELSE 0.0 END)
                FROM seller_interactions
                WHERE timestamp > ?
            ''', (since,))
            error_rate = (await cursor.fetchone())[0] or 0.0

        # Calculate SLA compliance
        sla_compliance = 1.0 - max(0, (avg_response_time or 0 - self.targets["response_time_ms"]) / self.targets["response_time_ms"])

        # Build dashboard data
        dashboard_data = {
            "timeframe": timeframe,
            "last_updated": datetime.now().isoformat(),
            "total_interactions": interaction_count or 0,

            # Performance metrics
            "performance_metrics": {
                "avg_response_time_ms": avg_response_time or 0,
                "sla_compliance": max(0, min(1, sla_compliance)),
                "error_rate": error_rate,
                "target_response_time": self.targets["response_time_ms"]
            },

            # Conversion metrics
            "conversion_metrics": {
                "hot_conversion_rate": hot_rate or 0,
                "warm_plus_conversion_rate": warm_plus_rate or 0,
                "qualified_rate": qualified_rate or 0,
                "temperature_distribution": temperature_dist
            },

            # Business metrics
            "business_metrics": {
                "total_commission_pipeline": total_commission or 0,
                "avg_commission_per_seller": avg_commission or 0,
                "business_rule_compliance": [asdict(rule) for rule in self.business_rules]
            },

            # Operational status
            "operational_status": {
                "active_alerts": len([a for a in self.active_alerts if not a.acknowledged]),
                "critical_alerts": len([a for a in self.active_alerts if a.level == AlertLevel.CRITICAL and not a.acknowledged]),
                "system_health": "healthy" if error_rate < 0.05 and sla_compliance > 0.9 else "degraded"
            },

            # Conversion funnel
            "conversion_funnel": [asdict(stage) for stage in self.conversion_funnel],

            # Recent alerts
            "recent_alerts": [asdict(alert) for alert in self.active_alerts[-5:]]
        }

        # Add concierge insights if available
        if self.concierge:
            try:
                # Get recent interactions for insights
                async with aiosqlite.connect(self.db_path) as db:
                    cursor = await db.execute('''
                        SELECT contact_id, message_content, analysis_time_ms, temperature, questions_answered
                        FROM seller_interactions
                        WHERE timestamp > ?
                        ORDER BY timestamp DESC
                        LIMIT 50
                    ''', (since,))
                    recent_interactions = await cursor.fetchall()

                # Convert to format expected by concierge
                conversation_data = [
                    {
                        "contact_id": row[0],
                        "message": row[1],
                        "response_time_ms": row[2],
                        "temperature": row[3],
                        "questions_answered": row[4]
                    }
                    for row in recent_interactions if row[1]  # Only include rows with message content
                ]

                if conversation_data:
                    insights = await self.concierge.analyze_conversation_batch(conversation_data, timeframe)
                    dashboard_data["ai_insights"] = [insight.to_dict() for insight in insights[:5]]

            except Exception as e:
                logger.error(f"Failed to get concierge insights: {e}")
                dashboard_data["ai_insights"] = []

        return dashboard_data

    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active performance alerts"""
        return [asdict(alert) for alert in self.active_alerts if not alert.acknowledged]

    async def acknowledge_alert(self, alert_id: str):
        """Acknowledge a performance alert"""
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                break

        # Update in database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE alerts SET acknowledged = TRUE WHERE alert_id = ?
            ''', (alert_id,))
            await db.commit()

    async def generate_performance_report(
        self,
        timeframe: str = "24h"
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report"""

        dashboard_data = await self.get_performance_dashboard_data(timeframe)

        # Calculate performance scores
        performance_score = self._calculate_overall_performance_score(dashboard_data)

        # Generate recommendations
        recommendations = await self._generate_performance_recommendations(dashboard_data)

        return {
            "report_timestamp": datetime.now().isoformat(),
            "timeframe": timeframe,
            "overall_performance_score": performance_score,
            "dashboard_data": dashboard_data,
            "recommendations": recommendations,
            "executive_summary": {
                "total_sellers_processed": dashboard_data["total_interactions"],
                "avg_response_time": f"{dashboard_data['performance_metrics']['avg_response_time_ms']:.0f}ms",
                "hot_conversion_rate": f"{dashboard_data['conversion_metrics']['hot_conversion_rate']:.1%}",
                "sla_compliance": f"{dashboard_data['performance_metrics']['sla_compliance']:.1%}",
                "commission_pipeline": f"${dashboard_data['business_metrics']['total_commission_pipeline']:,.0f}",
                "system_status": dashboard_data['operational_status']['system_health']
            }
        }

    def _calculate_overall_performance_score(self, dashboard_data: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)"""

        # Weight factors for different metrics
        weights = {
            "response_time": 0.25,
            "conversion": 0.30,
            "error_rate": 0.20,
            "business_rules": 0.25
        }

        # Normalize metrics to 0-1 scale
        response_time_score = min(1.0, self.targets["response_time_ms"] / max(1, dashboard_data["performance_metrics"]["avg_response_time_ms"]))
        conversion_score = dashboard_data["conversion_metrics"]["hot_conversion_rate"] / self.targets["hot_conversion_rate"]
        error_score = max(0, 1.0 - (dashboard_data["performance_metrics"]["error_rate"] / self.targets["error_rate"]))
        business_rules_score = dashboard_data["performance_metrics"]["sla_compliance"]

        # Calculate weighted score
        total_score = (
            response_time_score * weights["response_time"] +
            conversion_score * weights["conversion"] +
            error_score * weights["error_rate"] +
            business_rules_score * weights["business_rules"]
        )

        return min(100, total_score * 100)

    async def _generate_performance_recommendations(
        self,
        dashboard_data: Dict[str, Any]
    ) -> List[str]:
        """Generate performance improvement recommendations"""

        recommendations = []

        # Response time recommendations
        avg_response_time = dashboard_data["performance_metrics"]["avg_response_time_ms"]
        if avg_response_time > self.targets["response_time_ms"]:
            recommendations.append(
                f"⚡ Optimize response time: Currently {avg_response_time:.0f}ms vs {self.targets['response_time_ms']}ms target"
            )

        # Conversion rate recommendations
        hot_rate = dashboard_data["conversion_metrics"]["hot_conversion_rate"]
        if hot_rate < self.targets["hot_conversion_rate"]:
            recommendations.append(
                f"🎯 Improve HOT conversion: Currently {hot_rate:.1%} vs {self.targets['hot_conversion_rate']:.1%} target"
            )

        # Error rate recommendations
        error_rate = dashboard_data["performance_metrics"]["error_rate"]
        if error_rate > self.targets["error_rate"]:
            recommendations.append(
                f"🚨 Reduce error rate: Currently {error_rate:.1%} vs {self.targets['error_rate']:.1%} target"
            )

        # Business rule compliance
        sla_compliance = dashboard_data["performance_metrics"]["sla_compliance"]
        if sla_compliance < self.targets["five_minute_rule_compliance"]:
            recommendations.append(
                f"📋 Improve SLA compliance: Currently {sla_compliance:.1%} vs {self.targets['five_minute_rule_compliance']:.1%} target"
            )

        return recommendations


# Main service instance
performance_monitor = None

async def get_performance_monitor() -> SellerPerformanceMonitor:
    """Get the global performance monitor instance"""
    global performance_monitor
    if performance_monitor is None:
        performance_monitor = SellerPerformanceMonitor()
        await performance_monitor.initialize()
    return performance_monitor


# Async helper functions for integration
async def record_seller_performance(interaction_data: Dict[str, Any]):
    """Record seller interaction performance data"""
    monitor = await get_performance_monitor()
    await monitor.record_seller_interaction(interaction_data)


async def get_dashboard_data(timeframe: str = "24h") -> Dict[str, Any]:
    """Get performance dashboard data"""
    monitor = await get_performance_monitor()
    return await monitor.get_performance_dashboard_data(timeframe)


async def get_performance_alerts() -> List[Dict[str, Any]]:
    """Get active performance alerts"""
    monitor = await get_performance_monitor()
    return await monitor.get_active_alerts()


if __name__ == "__main__":
    # Test the performance monitor
    import asyncio

    async def test_monitor():
        monitor = SellerPerformanceMonitor()
        await monitor.initialize()

        # Test recording a seller interaction
        test_interaction = {
            "contact_id": "test_123",
            "message": "I want to sell my house in Plano for $500k",
            "analysis_time_ms": 245,
            "temperature": "HOT",
            "priority": "high",
            "questions_answered": 3,
            "business_rules_passed": True,
            "commission_potential": 30000.0,
            "error_occurred": False
        }

        await monitor.record_seller_interaction(test_interaction)
        print("✅ Recorded test interaction")

        # Get dashboard data
        dashboard = await monitor.get_performance_dashboard_data()
        print(f"\n📊 Dashboard Summary:")
        print(f"   Total interactions: {dashboard['total_interactions']}")
        print(f"   Avg response time: {dashboard['performance_metrics']['avg_response_time_ms']:.0f}ms")
        print(f"   HOT conversion: {dashboard['conversion_metrics']['hot_conversion_rate']:.1%}")

        # Generate performance report
        report = await monitor.generate_performance_report()
        print(f"\n📈 Performance Score: {report['overall_performance_score']:.1f}/100")

        # Show alerts
        alerts = await monitor.get_active_alerts()
        if alerts:
            print(f"\n🚨 Active Alerts: {len(alerts)}")
            for alert in alerts:
                print(f"   {alert['level'].upper()}: {alert['title']}")

    asyncio.run(test_monitor())