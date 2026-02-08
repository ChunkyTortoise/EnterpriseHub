"""
Real-time Compliance Alerts Module

WebSocket-based real-time alerting system for compliance violations,
score changes, and critical events across EU AI Act, SEC, and HIPAA frameworks.

Also includes:
- Redis pub/sub event system for inter-service communication
- Multi-channel notification delivery (Email, Slack, Webhook)
- Professional HTML email templates and Slack Block Kit formatting
- Real-time monitoring manager for orchestrating all monitoring components

Key Components:
- RealTimeMonitoringManager: Orchestrates WebSocket, Redis, and notifications
- MonitoringRule: Configurable monitoring rules with thresholds
- ComplianceMetrics: Real-time compliance metrics snapshot
"""

from ghl_real_estate_ai.compliance_platform.realtime.event_publisher import (
    ComplianceEvent,
    ComplianceEventBus,
    ComplianceEventPublisher,
    ComplianceEventSubscriber,
    ComplianceEventType,
)
from ghl_real_estate_ai.compliance_platform.realtime.monitoring_manager import (
    AlertSeverity,
    AlertStatus,
    ComplianceAlert,
    ComplianceMetrics,
    MonitoringRule,
    MonitoringThreshold,
    RealTimeMonitoringManager,
    ThresholdOperator,
    create_monitoring_manager,
)
from ghl_real_estate_ai.compliance_platform.realtime.notification_service import (
    ComplianceNotification,
    DeliveryResult,
    DeliveryStatus,
    EmailNotificationProvider,
    NotificationChannel,
    NotificationPriority,
    NotificationProvider,
    NotificationRecipient,
    NotificationService,
    SlackNotificationProvider,
    WebhookNotificationProvider,
    get_notification_service,
    reset_notification_service,
)
from ghl_real_estate_ai.compliance_platform.realtime.websocket_server import (
    AlertType,
    ConnectionManager,
    create_websocket_router,
)
from ghl_real_estate_ai.compliance_platform.realtime.websocket_server import (
    ComplianceAlert as WebSocketComplianceAlert,
)

__all__ = [
    # Monitoring Manager exports (orchestration layer)
    "RealTimeMonitoringManager",
    "create_monitoring_manager",
    "MonitoringRule",
    "MonitoringThreshold",
    "ComplianceMetrics",
    "ComplianceAlert",
    "AlertSeverity",
    "AlertStatus",
    "ThresholdOperator",
    # WebSocket exports
    "AlertType",
    "WebSocketComplianceAlert",
    "ConnectionManager",
    "create_websocket_router",
    # Pub/Sub exports
    "ComplianceEventType",
    "ComplianceEvent",
    "ComplianceEventPublisher",
    "ComplianceEventSubscriber",
    "ComplianceEventBus",
    # Notification service exports
    "NotificationChannel",
    "NotificationPriority",
    "DeliveryStatus",
    "NotificationRecipient",
    "ComplianceNotification",
    "DeliveryResult",
    "NotificationProvider",
    "EmailNotificationProvider",
    "SlackNotificationProvider",
    "WebhookNotificationProvider",
    "NotificationService",
    "get_notification_service",
    "reset_notification_service",
]
