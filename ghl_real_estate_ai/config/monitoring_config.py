"""
Monitoring Configuration for GHL Real Estate AI Platform
======================================================

Centralized configuration for all monitoring dashboards, metrics collection,
alerting thresholds, and performance targets.

Features:
- Dashboard-specific configurations
- Performance thresholds and SLA targets
- Alerting rules and notification settings
- Data retention and caching policies
- Security and compliance settings
- Export and reporting configurations
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import os


class MetricType(Enum):
    """Types of metrics collected."""
    BUSINESS = "business"
    OPERATIONAL = "operational"
    ML_PERFORMANCE = "ml_performance"
    SECURITY = "security"


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ThresholdConfig:
    """Configuration for metric thresholds and alerting."""
    warning_threshold: float
    critical_threshold: float
    comparison_type: str = "greater_than"  # greater_than, less_than, equals
    enabled: bool = True


@dataclass
class MetricConfig:
    """Configuration for individual metrics."""
    name: str
    display_name: str
    unit: str
    metric_type: MetricType
    collection_interval: int = 60  # seconds
    retention_days: int = 90
    threshold: Optional[ThresholdConfig] = None
    description: str = ""
    enabled: bool = True


@dataclass
class DashboardStyleConfig:
    """Configuration for dashboard styling and theming."""
    primary_color: str = "#667eea"
    secondary_color: str = "#764ba2"
    accent_color: str = "#f093fb"
    background_color: str = "#ffffff"
    text_color: str = "#333333"
    chart_colors: List[str] = field(default_factory=lambda: [
        "#667eea", "#764ba2", "#f093fb", "#f5576c", "#4facfe",
        "#00f2fe", "#43e97b", "#38f9d7", "#fa709a", "#fee140"
    ])
    font_family: str = "Inter, sans-serif"
    card_border_radius: str = "10px"
    chart_height: int = 400


@dataclass
class ExportConfig:
    """Configuration for data export functionality."""
    enabled: bool = True
    formats: List[str] = field(default_factory=lambda: ["pdf", "excel", "json", "csv"])
    max_file_size_mb: int = 100
    retention_days: int = 30
    include_charts: bool = True
    include_raw_data: bool = True
    watermark_enabled: bool = True
    watermark_text: str = "EnterpriseHub - Confidential"


@dataclass
class CacheConfig:
    """Configuration for caching behavior."""
    redis_enabled: bool = True
    redis_url: str = "redis://localhost:6379/0"
    default_ttl: int = 300  # seconds
    dashboard_cache_ttl: int = 60  # seconds
    metrics_cache_ttl: int = 30  # seconds
    max_memory_usage: str = "512mb"


@dataclass
class RealtimeConfig:
    """Configuration for real-time data updates."""
    websocket_enabled: bool = True
    websocket_url: str = "ws://localhost:8000/ws"
    update_interval: int = 5  # seconds
    max_connections: int = 100
    heartbeat_interval: int = 30  # seconds
    reconnect_attempts: int = 3
    buffer_size: int = 1000


@dataclass
class SecurityConfig:
    """Configuration for security and compliance monitoring."""
    gdpr_enabled: bool = True
    ccpa_enabled: bool = True
    audit_logging_enabled: bool = True
    data_anonymization_enabled: bool = True
    encryption_at_rest: bool = True
    encryption_in_transit: bool = True
    access_log_retention_days: int = 365
    security_scan_interval: int = 3600  # seconds
    threat_detection_enabled: bool = True


class MonitoringConfig:
    """
    Main monitoring configuration class combining all settings.
    """

    def __init__(self, environment: str = "production"):
        """Initialize monitoring configuration for specified environment."""
        self.environment = environment
        self.load_environment_config()

    def load_environment_config(self):
        """Load environment-specific configuration."""
        # Dashboard styling
        self.style = DashboardStyleConfig()

        # Caching configuration
        self.cache = CacheConfig(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0")
        )

        # Real-time configuration
        self.realtime = RealtimeConfig(
            websocket_url=os.getenv("WEBSOCKET_URL", "ws://localhost:8000/ws")
        )

        # Export configuration
        self.export = ExportConfig()

        # Security configuration
        self.security = SecurityConfig()

        # Performance targets
        self.performance_targets = self.get_performance_targets()

        # Business metrics configuration
        self.business_metrics = self.get_business_metrics_config()

        # Operational metrics configuration
        self.operational_metrics = self.get_operational_metrics_config()

        # ML performance metrics configuration
        self.ml_metrics = self.get_ml_metrics_config()

        # Security metrics configuration
        self.security_metrics = self.get_security_metrics_config()

        # Alerting configuration
        self.alerts = self.get_alerting_config()

    def get_performance_targets(self) -> Dict[str, float]:
        """Get performance targets for the platform."""
        return {
            # API Performance
            "api_response_time_95th": 200.0,  # ms
            "api_response_time_avg": 150.0,   # ms
            "api_error_rate": 0.1,            # %
            "api_throughput": 1000.0,         # requests/minute

            # ML Performance
            "ml_inference_time": 500.0,       # ms
            "ml_batch_processing": 10000.0,   # predictions/hour
            "lead_scoring_accuracy": 95.0,    # %
            "property_match_accuracy": 88.0,  # %
            "churn_prediction_accuracy": 92.0, # %

            # System Performance
            "system_uptime": 99.95,           # %
            "cpu_utilization": 80.0,          # %
            "memory_utilization": 85.0,       # %
            "disk_utilization": 90.0,         # %

            # Database Performance
            "db_query_time_95th": 50.0,       # ms
            "db_connection_utilization": 80.0, # %
            "db_replication_lag": 100.0,      # ms

            # Business Targets
            "monthly_revenue_growth": 15.0,   # %
            "lead_conversion_rate": 20.0,     # %
            "agent_productivity_score": 85.0, # %
            "customer_satisfaction": 4.5,     # out of 5

            # Security Targets
            "security_compliance_score": 95.0, # %
            "vulnerability_remediation": 7.0,  # days
            "security_incident_response": 30.0, # minutes
        }

    def get_business_metrics_config(self) -> List[MetricConfig]:
        """Get configuration for business metrics."""
        return [
            MetricConfig(
                name="monthly_revenue",
                display_name="Monthly Revenue",
                unit="USD",
                metric_type=MetricType.BUSINESS,
                collection_interval=3600,  # hourly
                retention_days=365,
                threshold=ThresholdConfig(100000.0, 80000.0, "greater_than"),
                description="Total monthly revenue from platform"
            ),
            MetricConfig(
                name="lead_conversion_rate",
                display_name="Lead Conversion Rate",
                unit="%",
                metric_type=MetricType.BUSINESS,
                collection_interval=1800,  # 30 minutes
                retention_days=180,
                threshold=ThresholdConfig(18.0, 15.0, "greater_than"),
                description="Percentage of leads converted to customers"
            ),
            MetricConfig(
                name="agent_productivity",
                display_name="Agent Productivity Score",
                unit="%",
                metric_type=MetricType.BUSINESS,
                collection_interval=3600,  # hourly
                retention_days=180,
                threshold=ThresholdConfig(80.0, 70.0, "greater_than"),
                description="Combined agent productivity and efficiency score"
            ),
            MetricConfig(
                name="platform_roi",
                display_name="Platform ROI",
                unit="%",
                metric_type=MetricType.BUSINESS,
                collection_interval=86400,  # daily
                retention_days=365,
                threshold=ThresholdConfig(500.0, 300.0, "greater_than"),
                description="Return on investment for platform implementation"
            ),
            MetricConfig(
                name="customer_acquisition_cost",
                display_name="Customer Acquisition Cost",
                unit="USD",
                metric_type=MetricType.BUSINESS,
                collection_interval=3600,  # hourly
                retention_days=180,
                threshold=ThresholdConfig(150.0, 200.0, "less_than"),
                description="Average cost to acquire a new customer"
            )
        ]

    def get_operational_metrics_config(self) -> List[MetricConfig]:
        """Get configuration for operational metrics."""
        return [
            MetricConfig(
                name="system_uptime",
                display_name="System Uptime",
                unit="%",
                metric_type=MetricType.OPERATIONAL,
                collection_interval=60,  # 1 minute
                retention_days=365,
                threshold=ThresholdConfig(99.9, 99.5, "greater_than"),
                description="Overall system availability percentage"
            ),
            MetricConfig(
                name="api_response_time",
                display_name="API Response Time",
                unit="ms",
                metric_type=MetricType.OPERATIONAL,
                collection_interval=60,
                retention_days=90,
                threshold=ThresholdConfig(250.0, 500.0, "less_than"),
                description="95th percentile API response time"
            ),
            MetricConfig(
                name="api_error_rate",
                display_name="API Error Rate",
                unit="%",
                metric_type=MetricType.OPERATIONAL,
                collection_interval=300,  # 5 minutes
                retention_days=90,
                threshold=ThresholdConfig(1.0, 5.0, "less_than"),
                description="Percentage of API requests resulting in errors"
            ),
            MetricConfig(
                name="webhook_processing_time",
                display_name="Webhook Processing Time",
                unit="ms",
                metric_type=MetricType.OPERATIONAL,
                collection_interval=60,
                retention_days=90,
                threshold=ThresholdConfig(1000.0, 2000.0, "less_than"),
                description="Time to process GoHighLevel webhooks"
            ),
            MetricConfig(
                name="database_query_time",
                display_name="Database Query Time",
                unit="ms",
                metric_type=MetricType.OPERATIONAL,
                collection_interval=60,
                retention_days=90,
                threshold=ThresholdConfig(100.0, 200.0, "less_than"),
                description="95th percentile database query execution time"
            ),
            MetricConfig(
                name="redis_cache_hit_rate",
                display_name="Cache Hit Rate",
                unit="%",
                metric_type=MetricType.OPERATIONAL,
                collection_interval=300,
                retention_days=30,
                threshold=ThresholdConfig(85.0, 70.0, "greater_than"),
                description="Redis cache hit rate percentage"
            )
        ]

    def get_ml_metrics_config(self) -> List[MetricConfig]:
        """Get configuration for ML performance metrics."""
        return [
            MetricConfig(
                name="lead_scoring_accuracy",
                display_name="Lead Scoring Accuracy",
                unit="%",
                metric_type=MetricType.ML_PERFORMANCE,
                collection_interval=3600,  # hourly
                retention_days=180,
                threshold=ThresholdConfig(93.0, 90.0, "greater_than"),
                description="Lead scoring model accuracy percentage"
            ),
            MetricConfig(
                name="property_match_accuracy",
                display_name="Property Matching Accuracy",
                unit="%",
                metric_type=MetricType.ML_PERFORMANCE,
                collection_interval=3600,
                retention_days=180,
                threshold=ThresholdConfig(85.0, 80.0, "greater_than"),
                description="Property matching algorithm accuracy"
            ),
            MetricConfig(
                name="churn_prediction_precision",
                display_name="Churn Prediction Precision",
                unit="%",
                metric_type=MetricType.ML_PERFORMANCE,
                collection_interval=3600,
                retention_days=180,
                threshold=ThresholdConfig(89.0, 85.0, "greater_than"),
                description="Churn prediction model precision score"
            ),
            MetricConfig(
                name="ml_inference_latency",
                display_name="ML Inference Latency",
                unit="ms",
                metric_type=MetricType.ML_PERFORMANCE,
                collection_interval=300,
                retention_days=90,
                threshold=ThresholdConfig(600.0, 1000.0, "less_than"),
                description="Average ML model inference time"
            ),
            MetricConfig(
                name="model_drift_score",
                display_name="Model Drift Score",
                unit="score",
                metric_type=MetricType.ML_PERFORMANCE,
                collection_interval=3600,
                retention_days=180,
                threshold=ThresholdConfig(0.1, 0.2, "less_than"),
                description="Statistical drift detection score"
            ),
            MetricConfig(
                name="prediction_confidence",
                display_name="Average Prediction Confidence",
                unit="%",
                metric_type=MetricType.ML_PERFORMANCE,
                collection_interval=1800,
                retention_days=90,
                threshold=ThresholdConfig(85.0, 70.0, "greater_than"),
                description="Average confidence score of ML predictions"
            )
        ]

    def get_security_metrics_config(self) -> List[MetricConfig]:
        """Get configuration for security metrics."""
        return [
            MetricConfig(
                name="security_compliance_score",
                display_name="Security Compliance Score",
                unit="%",
                metric_type=MetricType.SECURITY,
                collection_interval=3600,  # hourly
                retention_days=365,
                threshold=ThresholdConfig(95.0, 90.0, "greater_than"),
                description="Overall security compliance percentage"
            ),
            MetricConfig(
                name="failed_authentication_attempts",
                display_name="Failed Authentication Attempts",
                unit="count",
                metric_type=MetricType.SECURITY,
                collection_interval=300,  # 5 minutes
                retention_days=90,
                threshold=ThresholdConfig(10.0, 20.0, "less_than"),
                description="Number of failed login attempts per hour"
            ),
            MetricConfig(
                name="security_incidents",
                display_name="Security Incidents",
                unit="count",
                metric_type=MetricType.SECURITY,
                collection_interval=3600,
                retention_days=365,
                threshold=ThresholdConfig(1.0, 3.0, "less_than"),
                description="Number of security incidents per day"
            ),
            MetricConfig(
                name="vulnerability_count",
                display_name="Active Vulnerabilities",
                unit="count",
                metric_type=MetricType.SECURITY,
                collection_interval=86400,  # daily
                retention_days=365,
                threshold=ThresholdConfig(5.0, 15.0, "less_than"),
                description="Number of unpatched security vulnerabilities"
            ),
            MetricConfig(
                name="data_encryption_coverage",
                display_name="Data Encryption Coverage",
                unit="%",
                metric_type=MetricType.SECURITY,
                collection_interval=86400,  # daily
                retention_days=365,
                threshold=ThresholdConfig(99.0, 95.0, "greater_than"),
                description="Percentage of data encrypted at rest and in transit"
            ),
            MetricConfig(
                name="gdpr_compliance_score",
                display_name="GDPR Compliance Score",
                unit="%",
                metric_type=MetricType.SECURITY,
                collection_interval=86400,  # daily
                retention_days=365,
                threshold=ThresholdConfig(98.0, 95.0, "greater_than"),
                description="GDPR compliance assessment score"
            )
        ]

    def get_alerting_config(self) -> Dict[str, Any]:
        """Get alerting configuration."""
        return {
            "enabled": True,
            "notification_channels": {
                "email": {
                    "enabled": True,
                    "recipients": [
                        "alerts@enterprisehub.ai",
                        "ops@enterprisehub.ai"
                    ],
                    "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                    "smtp_port": int(os.getenv("SMTP_PORT", "587"))
                },
                "slack": {
                    "enabled": True,
                    "webhook_url": os.getenv("SLACK_WEBHOOK_URL"),
                    "channel": "#alerts"
                },
                "sms": {
                    "enabled": False,  # Enable for critical alerts only
                    "provider": "twilio",
                    "phone_numbers": []
                }
            },
            "escalation_rules": {
                "low": {
                    "delay_minutes": 30,
                    "max_escalations": 2
                },
                "medium": {
                    "delay_minutes": 15,
                    "max_escalations": 3
                },
                "high": {
                    "delay_minutes": 5,
                    "max_escalations": 4
                },
                "critical": {
                    "delay_minutes": 0,  # Immediate
                    "max_escalations": 5
                }
            },
            "quiet_hours": {
                "enabled": True,
                "start_hour": 22,  # 10 PM
                "end_hour": 6,     # 6 AM
                "timezone": "UTC"
            },
            "alert_aggregation": {
                "enabled": True,
                "window_minutes": 5,
                "max_alerts_per_window": 10
            }
        }

    def get_dashboard_specific_config(self, dashboard_type: str) -> Dict[str, Any]:
        """Get configuration specific to a dashboard type."""
        configs = {
            "executive": {
                "refresh_interval": 300,  # 5 minutes
                "chart_types": ["line", "bar", "pie", "funnel"],
                "kpi_cards": 4,
                "max_data_points": 12,  # months
                "enable_forecasting": True,
                "export_formats": ["pdf", "excel"]
            },
            "operations": {
                "refresh_interval": 60,   # 1 minute
                "chart_types": ["line", "bar", "gauge", "heatmap"],
                "kpi_cards": 4,
                "max_data_points": 24,  # hours
                "enable_realtime": True,
                "export_formats": ["json", "csv"]
            },
            "ml_performance": {
                "refresh_interval": 300,  # 5 minutes
                "chart_types": ["line", "scatter", "histogram", "box"],
                "kpi_cards": 4,
                "max_data_points": 30,  # days
                "enable_model_comparison": True,
                "export_formats": ["json", "csv", "pickle"]
            },
            "security": {
                "refresh_interval": 300,  # 5 minutes
                "chart_types": ["bar", "pie", "timeline", "sankey"],
                "kpi_cards": 4,
                "max_data_points": 7,   # days for security events
                "enable_incident_tracking": True,
                "export_formats": ["pdf", "json"]
            }
        }

        return configs.get(dashboard_type, {})


# Global monitoring configuration instance
monitoring_config = MonitoringConfig(
    environment=os.getenv("ENVIRONMENT", "production")
)