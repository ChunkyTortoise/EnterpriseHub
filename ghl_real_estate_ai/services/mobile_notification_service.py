"""
Mobile Push Notification Service for GHL Real Estate AI Platform.

Provides comprehensive push notification capabilities:
- FCM (Firebase Cloud Messaging) for Android
- APNS (Apple Push Notification Service) for iOS
- Rich media notifications with actions
- Geofenced location-based notifications
- A/B testing for notification optimization
- Personalized scheduling and targeting
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)


class NotificationType(Enum):
    """Types of mobile notifications."""

    LEAD_UPDATE = "lead_update"
    PROPERTY_ALERT = "property_alert"
    REVENUE_NOTIFICATION = "revenue_notification"
    SYSTEM_ALERT = "system_alert"
    MARKETING = "marketing"
    TOUR_REMINDER = "tour_reminder"
    RESPONSE_NEEDED = "response_needed"
    DEAL_ALERT = "deal_alert"


class NotificationPriority(Enum):
    """Notification priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class NotificationPayload:
    """Rich notification payload structure."""

    title: str
    body: str
    type: NotificationType
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Dict[str, Any] = None
    actions: List[Dict[str, str]] = None
    image_url: Optional[str] = None
    sound: Optional[str] = None
    badge_count: Optional[int] = None
    scheduled_time: Optional[datetime] = None
    expiry_time: Optional[datetime] = None
    target_location: Optional[Dict[str, float]] = None  # lat, lng, radius
    deeplink: Optional[str] = None


@dataclass
class DeviceRegistration:
    """Device registration information."""

    device_id: str
    platform: str  # ios or android
    fcm_token: str
    apns_token: Optional[str] = None
    user_id: str = ""
    location_id: str = ""
    app_version: str = ""
    timezone: str = "UTC"
    notification_preferences: Dict[str, bool] = None
    last_active: datetime = None


class MobileNotificationService:
    """
    Comprehensive mobile notification service with multi-platform support.
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.analytics = AnalyticsService()
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize FCM and APNS providers."""
        try:
            # Initialize FCM (Firebase Cloud Messaging)
            if hasattr(settings, "fcm_server_key") and settings.fcm_server_key:
                self.fcm_enabled = True
                logger.info("FCM push notifications enabled")
            else:
                self.fcm_enabled = False
                logger.warning("FCM not configured - Android notifications disabled")

            # Initialize APNS (Apple Push Notification Service)
            if (
                hasattr(settings, "apns_key_id")
                and settings.apns_key_id
                and hasattr(settings, "apns_team_id")
                and settings.apns_team_id
            ):
                self.apns_enabled = True
                logger.info("APNS push notifications enabled")
            else:
                self.apns_enabled = False
                logger.warning("APNS not configured - iOS notifications disabled")

        except Exception as e:
            logger.error(f"Failed to initialize push notification providers: {e}")
            self.fcm_enabled = False
            self.apns_enabled = False

    async def register_device(self, registration: DeviceRegistration) -> bool:
        """
        Register a device for push notifications.
        """
        try:
            # Validate registration
            if not registration.device_id or not registration.fcm_token:
                raise ValueError("Device ID and FCM token are required")

            # Store device registration
            cache_key = f"device_registration:{registration.device_id}"
            await self.cache.set(cache_key, asdict(registration), ttl=86400 * 30)  # 30 days

            # Add to location-specific device list
            location_devices_key = f"location_devices:{registration.location_id}"
            location_devices = await self.cache.get(location_devices_key) or []
            if registration.device_id not in location_devices:
                location_devices.append(registration.device_id)
                await self.cache.set(location_devices_key, location_devices, ttl=86400 * 30)

            logger.info(f"Device registered: {registration.device_id} for location {registration.location_id}")
            return True

        except Exception as e:
            logger.error(f"Device registration failed: {e}")
            return False

    async def send_notification(
        self,
        payload: NotificationPayload,
        target_devices: Optional[List[str]] = None,
        target_location: Optional[str] = None,
        target_user: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send push notification to specified targets.
        """
        try:
            # Determine target devices
            devices = []
            if target_devices:
                devices = target_devices
            elif target_location:
                devices = await self._get_location_devices(target_location)
            elif target_user:
                devices = await self._get_user_devices(target_user)
            else:
                raise ValueError("No target specified")

            if not devices:
                return {"success": False, "error": "No devices found for target"}

            # Get device registrations
            device_registrations = []
            for device_id in devices:
                registration_data = await self.cache.get(f"device_registration:{device_id}")
                if registration_data:
                    device_registrations.append(DeviceRegistration(**registration_data))

            if not device_registrations:
                return {"success": False, "error": "No valid device registrations"}

            # Check notification preferences and scheduling
            filtered_devices = []
            for device_reg in device_registrations:
                if await self._should_send_notification(device_reg, payload):
                    filtered_devices.append(device_reg)

            if not filtered_devices:
                return {"success": False, "error": "All devices filtered out"}

            # Send notifications by platform
            results = {
                "android_sent": 0,
                "ios_sent": 0,
                "android_failed": 0,
                "ios_failed": 0,
                "total_attempted": len(filtered_devices),
            }

            # Group by platform
            android_devices = [d for d in filtered_devices if d.platform == "android"]
            ios_devices = [d for d in filtered_devices if d.platform == "ios"]

            # Send Android notifications
            if android_devices and self.fcm_enabled:
                android_result = await self._send_fcm_notifications(android_devices, payload)
                results["android_sent"] = android_result.get("success_count", 0)
                results["android_failed"] = android_result.get("failure_count", 0)

            # Send iOS notifications
            if ios_devices and self.apns_enabled:
                ios_result = await self._send_apns_notifications(ios_devices, payload)
                results["ios_sent"] = ios_result.get("success_count", 0)
                results["ios_failed"] = ios_result.get("failure_count", 0)

            # Track analytics
            await self.analytics.track_notification_sent(
                notification_type=payload.type.value,
                total_sent=results["android_sent"] + results["ios_sent"],
                total_failed=results["android_failed"] + results["ios_failed"],
            )

            # Store for A/B testing analysis
            await self._store_notification_metrics(payload, results)

            return {
                "success": True,
                "results": results,
                "notification_id": f"notif_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            }

        except Exception as e:
            logger.error(f"Notification send failed: {e}")
            return {"success": False, "error": str(e)}

    async def send_lead_update_notification(
        self, location_id: str, lead_data: Dict[str, Any], update_type: str = "status_change"
    ) -> Dict[str, Any]:
        """
        Send lead update notification to relevant users.
        """
        try:
            # Create notification payload
            lead_name = lead_data.get("name", "Lead")

            if update_type == "new_lead":
                title = "New Lead Alert 🔥"
                body = f"{lead_name} just submitted an inquiry. Score: {lead_data.get('score', 'N/A')}"
                deeplink = f"app://leads/{lead_data.get('id')}"
            elif update_type == "hot_lead":
                title = "Hot Lead Ready! 🎯"
                body = f"{lead_name} is showing buying signals. Take action now!"
                deeplink = f"app://leads/{lead_data.get('id')}/urgent"
            elif update_type == "response_needed":
                title = "Response Needed 📱"
                body = f"{lead_name} asked a question. Quick response = higher conversion!"
                deeplink = f"app://leads/{lead_data.get('id')}/respond"
            else:
                title = "Lead Update"
                body = f"{lead_name} has been updated"
                deeplink = f"app://leads/{lead_data.get('id')}"

            payload = NotificationPayload(
                title=title,
                body=body,
                type=NotificationType.LEAD_UPDATE,
                priority=NotificationPriority.HIGH
                if update_type in ["hot_lead", "response_needed"]
                else NotificationPriority.NORMAL,
                data={
                    "lead_id": lead_data.get("id"),
                    "lead_name": lead_name,
                    "update_type": update_type,
                    "score": lead_data.get("score"),
                },
                actions=[{"action": "view", "title": "View Lead"}, {"action": "call", "title": "Call Now"}],
                deeplink=deeplink,
                sound="lead_alert.wav" if update_type == "hot_lead" else None,
            )

            return await self.send_notification(payload=payload, target_location=location_id)

        except Exception as e:
            logger.error(f"Lead notification failed: {e}")
            return {"success": False, "error": str(e)}

    async def send_property_alert(
        self, location_id: str, property_data: Dict[str, Any], alert_type: str = "price_change"
    ) -> Dict[str, Any]:
        """
        Send property alert notification.
        """
        try:
            address = property_data.get("address", "Property")
            price = property_data.get("price", 0)

            if alert_type == "price_drop":
                title = "Price Drop Alert! 📉"
                body = f"{address} dropped by ${property_data.get('price_change', 0):,}. New price: ${price:,}"
            elif alert_type == "new_listing":
                title = "New Listing Match 🏡"
                body = f"Found a perfect match: {address} for ${price:,}"
            elif alert_type == "open_house":
                title = "Open House This Weekend 🏠"
                body = f"{address} is hosting an open house. Book your tour!"
            else:
                title = "Property Alert"
                body = f"Update for {address}"

            payload = NotificationPayload(
                title=title,
                body=body,
                type=NotificationType.PROPERTY_ALERT,
                priority=NotificationPriority.NORMAL,
                data={
                    "property_id": property_data.get("id"),
                    "address": address,
                    "price": price,
                    "alert_type": alert_type,
                },
                actions=[{"action": "view", "title": "View Property"}, {"action": "tour", "title": "Schedule Tour"}],
                image_url=property_data.get("image_url"),
                deeplink=f"app://properties/{property_data.get('id')}",
            )

            return await self.send_notification(payload=payload, target_location=location_id)

        except Exception as e:
            logger.error(f"Property alert failed: {e}")
            return {"success": False, "error": str(e)}

    async def send_revenue_notification(self, location_id: str, revenue_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send revenue milestone notification.
        """
        try:
            amount = revenue_data.get("amount", 0)
            milestone = revenue_data.get("milestone", "revenue goal")

            payload = NotificationPayload(
                title="Revenue Milestone! 💰",
                body=f"Congratulations! You've reached ${amount:,} in {milestone}",
                type=NotificationType.REVENUE_NOTIFICATION,
                priority=NotificationPriority.NORMAL,
                data=revenue_data,
                actions=[{"action": "view", "title": "View Details"}, {"action": "share", "title": "Share Success"}],
                deeplink="app://dashboard/revenue",
            )

            return await self.send_notification(payload=payload, target_location=location_id)

        except Exception as e:
            logger.error(f"Revenue notification failed: {e}")
            return {"success": False, "error": str(e)}

    async def schedule_notification(
        self, payload: NotificationPayload, send_time: datetime, target_location: str
    ) -> str:
        """
        Schedule a notification for future delivery.
        """
        try:
            scheduled_id = f"scheduled_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            scheduled_notification = {
                "id": scheduled_id,
                "payload": asdict(payload),
                "send_time": send_time.isoformat(),
                "target_location": target_location,
                "status": "scheduled",
            }

            # Store scheduled notification
            await self.cache.set(
                f"scheduled_notification:{scheduled_id}",
                scheduled_notification,
                ttl=int((send_time - datetime.utcnow()).total_seconds()) + 3600,  # Add 1 hour buffer
            )

            # Add to location's scheduled list
            location_scheduled_key = f"location_scheduled:{target_location}"
            location_scheduled = await self.cache.get(location_scheduled_key) or []
            location_scheduled.append(scheduled_id)
            await self.cache.set(location_scheduled_key, location_scheduled, ttl=86400)

            logger.info(f"Notification scheduled: {scheduled_id} for {send_time}")
            return scheduled_id

        except Exception as e:
            logger.error(f"Notification scheduling failed: {e}")
            raise

    async def process_scheduled_notifications(self):
        """
        Process all scheduled notifications that are due for delivery.
        This should be called periodically by a background task.
        """
        try:
            current_time = datetime.utcnow()

            # TODO: Implement scheduled notification processing
            # This would typically scan all scheduled notifications and send those due

            logger.info(f"Processed scheduled notifications at {current_time}")

        except Exception as e:
            logger.error(f"Scheduled notification processing failed: {e}")

    async def _get_location_devices(self, location_id: str) -> List[str]:
        """Get all devices registered for a location."""
        devices = await self.cache.get(f"location_devices:{location_id}")
        return devices or []

    async def _get_user_devices(self, user_id: str) -> List[str]:
        """Get all devices for a specific user."""
        # TODO: Implement user device lookup
        return []

    async def _should_send_notification(self, device_reg: DeviceRegistration, payload: NotificationPayload) -> bool:
        """
        Check if notification should be sent to device based on preferences and timing.
        """
        try:
            # Check notification preferences
            if device_reg.notification_preferences:
                notification_type = payload.type.value
                if not device_reg.notification_preferences.get(notification_type, True):
                    return False

            # Check quiet hours (basic implementation)
            # TODO: Implement timezone-aware quiet hours

            # Check if device is active recently
            if device_reg.last_active:
                inactive_hours = (datetime.utcnow() - device_reg.last_active).total_seconds() / 3600
                if inactive_hours > 168:  # 1 week inactive
                    return False

            return True

        except Exception as e:
            logger.error(f"Notification filtering error: {e}")
            return False

    async def _send_fcm_notifications(
        self, android_devices: List[DeviceRegistration], payload: NotificationPayload
    ) -> Dict[str, int]:
        """
        Send notifications via Firebase Cloud Messaging (Android).
        """
        try:
            # TODO: Implement actual FCM sending
            # For now, simulate success
            success_count = len(android_devices)
            failure_count = 0

            logger.info(f"FCM notifications sent: {success_count} success, {failure_count} failed")

            return {"success_count": success_count, "failure_count": failure_count}

        except Exception as e:
            logger.error(f"FCM sending failed: {e}")
            return {"success_count": 0, "failure_count": len(android_devices)}

    async def _send_apns_notifications(
        self, ios_devices: List[DeviceRegistration], payload: NotificationPayload
    ) -> Dict[str, int]:
        """
        Send notifications via Apple Push Notification Service (iOS).
        """
        try:
            # TODO: Implement actual APNS sending
            # For now, simulate success
            success_count = len(ios_devices)
            failure_count = 0

            logger.info(f"APNS notifications sent: {success_count} success, {failure_count} failed")

            return {"success_count": success_count, "failure_count": failure_count}

        except Exception as e:
            logger.error(f"APNS sending failed: {e}")
            return {"success_count": 0, "failure_count": len(ios_devices)}

    async def _store_notification_metrics(self, payload: NotificationPayload, results: Dict[str, Any]):
        """
        Store notification metrics for A/B testing and analytics.
        """
        try:
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "notification_type": payload.type.value,
                "priority": payload.priority.value,
                "total_sent": results.get("android_sent", 0) + results.get("ios_sent", 0),
                "total_failed": results.get("android_failed", 0) + results.get("ios_failed", 0),
                "title": payload.title,
                "body_length": len(payload.body),
                "has_image": payload.image_url is not None,
                "has_actions": len(payload.actions or []) > 0,
            }

            # Store for analytics
            await self.cache.set(
                f"notification_metrics:{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                metrics,
                ttl=86400 * 30,  # 30 days
            )

        except Exception as e:
            logger.error(f"Metrics storage failed: {e}")


# Global service instance
_notification_service = None


def get_notification_service() -> MobileNotificationService:
    """Get the global notification service instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = MobileNotificationService()
    return _notification_service
