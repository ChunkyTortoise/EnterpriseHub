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

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

import httpx

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

            # ROADMAP-060: Maintain user-to-device mapping
            if registration.user_id:
                user_devices_key = f"user_devices:{registration.user_id}"
                user_devices = await self.cache.get(user_devices_key) or []
                if registration.device_id not in user_devices:
                    user_devices.append(registration.device_id)
                    await self.cache.set(user_devices_key, user_devices, ttl=86400 * 30)

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

            # Maintain global location index for scheduled notification sweep (ROADMAP-062)
            all_locations_key = "scheduled_locations_index"
            location_ids = await self.cache.get(all_locations_key) or []
            if target_location not in location_ids:
                location_ids.append(target_location)
                await self.cache.set(all_locations_key, location_ids, ttl=86400 * 7)

            logger.info(f"Notification scheduled: {scheduled_id} for {send_time}")
            return scheduled_id

        except Exception as e:
            logger.error(f"Notification scheduling failed: {e}")
            raise

    async def process_scheduled_notifications(self):
        """
        ROADMAP-062: Process all scheduled notifications that are due for delivery.
        Scans all location scheduled lists, finds due notifications, sends them,
        and marks them as sent. Should be called periodically by a background task.
        """
        try:
            current_time = datetime.now(timezone.utc)
            processed = 0
            sent = 0
            failed = 0

            # Scan scheduled notification keys via pattern match
            # Location-keyed lists stored as location_scheduled:{location_id}
            all_locations_key = "scheduled_locations_index"
            location_ids = await self.cache.get(all_locations_key) or []

            # Also check any location_scheduled keys from the schedule_notification method
            for location_id in location_ids:
                location_key = f"location_scheduled:{location_id}"
                scheduled_ids = await self.cache.get(location_key) or []
                remaining_ids = []

                for sched_id in scheduled_ids:
                    processed += 1
                    sched_data = await self.cache.get(f"scheduled_notification:{sched_id}")
                    if not sched_data:
                        continue

                    if sched_data.get("status") != "scheduled":
                        continue

                    send_time_str = sched_data.get("send_time", "")
                    try:
                        send_time = datetime.fromisoformat(send_time_str)
                        if send_time.tzinfo is None:
                            send_time = send_time.replace(tzinfo=timezone.utc)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid send_time for {sched_id}: {send_time_str}")
                        continue

                    if send_time > current_time:
                        remaining_ids.append(sched_id)
                        continue

                    # Due — reconstruct payload and send
                    try:
                        payload_data = sched_data["payload"]
                        payload_data["type"] = NotificationType(payload_data["type"])
                        payload_data["priority"] = NotificationPriority(payload_data["priority"])
                        # Remove None datetimes that can't be passed to dataclass directly
                        for dt_field in ("scheduled_time", "expiry_time", "last_active"):
                            if dt_field in payload_data and payload_data[dt_field] is None:
                                payload_data.pop(dt_field, None)
                        payload = NotificationPayload(**payload_data)

                        result = await self.send_notification(
                            payload=payload,
                            target_location=sched_data.get("target_location"),
                        )
                        if result.get("success"):
                            sent += 1
                            sched_data["status"] = "sent"
                            sched_data["sent_at"] = current_time.isoformat()
                        else:
                            failed += 1
                            sched_data["status"] = "failed"
                            sched_data["error"] = result.get("error", "unknown")
                            remaining_ids.append(sched_id)
                    except Exception as send_err:
                        failed += 1
                        sched_data["status"] = "failed"
                        sched_data["error"] = str(send_err)
                        logger.error(f"Failed to send scheduled {sched_id}: {send_err}")

                    await self.cache.set(f"scheduled_notification:{sched_id}", sched_data, ttl=86400)

                # Update remaining list
                if remaining_ids != scheduled_ids:
                    await self.cache.set(location_key, remaining_ids, ttl=86400)

            logger.info(
                f"Scheduled notification sweep: {processed} scanned, "
                f"{sent} sent, {failed} failed"
            )

        except Exception as e:
            logger.error(f"Scheduled notification processing failed: {e}")

    async def _get_location_devices(self, location_id: str) -> List[str]:
        """Get all devices registered for a location."""
        devices = await self.cache.get(f"location_devices:{location_id}")
        return devices or []

    async def _get_user_devices(self, user_id: str) -> List[str]:
        """ROADMAP-060: Get user device tokens from user-to-device mapping."""
        try:
            user_devices_key = f"user_devices:{user_id}"
            device_ids = await self.cache.get(user_devices_key) or []

            # Filter to only active devices
            active_devices = []
            for device_id in device_ids:
                reg_data = await self.cache.get(f"device_registration:{device_id}")
                if reg_data and reg_data.get("active", True):
                    active_devices.append(device_id)

            return active_devices
        except Exception as e:
            logger.error(f"Failed to get user devices: {e}")
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

            # ROADMAP-061: Timezone-aware quiet hours enforcement
            if not self._is_within_allowed_hours(device_reg, payload):
                logger.info(f"Notification suppressed for {device_reg.device_id} due to quiet hours")
                return False

            # Check if device is active recently
            if device_reg.last_active:
                inactive_hours = (datetime.utcnow() - device_reg.last_active).total_seconds() / 3600
                if inactive_hours > 168:  # 1 week inactive
                    return False

            return True

        except Exception as e:
            logger.error(f"Notification filtering error: {e}")
            return False

    def _is_within_allowed_hours(self, device_reg: DeviceRegistration, payload: NotificationPayload) -> bool:
        """ROADMAP-061: Timezone-aware quiet hours enforcement.

        Urgent notifications bypass quiet hours. Otherwise, suppress
        between 21:00-08:00 in the device's local timezone.
        """
        if payload.priority == NotificationPriority.URGENT:
            return True

        try:
            tz = ZoneInfo(device_reg.timezone) if device_reg.timezone else ZoneInfo("UTC")
        except (KeyError, Exception):
            tz = ZoneInfo("UTC")

        local_now = datetime.now(tz)
        local_hour = local_now.hour

        quiet_start = 21  # 9 PM
        quiet_end = 8     # 8 AM

        if local_hour >= quiet_start or local_hour < quiet_end:
            return False

        return True

    async def _send_fcm_notifications(
        self, android_devices: List[DeviceRegistration], payload: NotificationPayload
    ) -> Dict[str, int]:
        """ROADMAP-058: Send notifications via FCM v1 API with google.oauth2."""
        success_count = 0
        failure_count = 0
        try:
            fcm_project_id = getattr(settings, "fcm_project_id", None)
            fcm_service_account = getattr(settings, "fcm_service_account_json", None)

            if not fcm_project_id or not fcm_service_account:
                logger.warning("FCM project_id or service account not configured, simulating send")
                return {"success_count": len(android_devices), "failure_count": 0}

            # Obtain OAuth2 access token from service account
            access_token = await self._get_fcm_access_token(fcm_service_account)
            if not access_token:
                return {"success_count": 0, "failure_count": len(android_devices)}

            fcm_url = f"https://fcm.googleapis.com/v1/projects/{fcm_project_id}/messages:send"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                for device in android_devices:
                    message_body = {
                        "message": {
                            "token": device.fcm_token,
                            "notification": {
                                "title": payload.title,
                                "body": payload.body,
                            },
                            "data": {k: str(v) for k, v in (payload.data or {}).items()},
                            "android": {
                                "priority": "high" if payload.priority in (
                                    NotificationPriority.HIGH, NotificationPriority.URGENT
                                ) else "normal",
                            },
                        }
                    }
                    if payload.image_url:
                        message_body["message"]["notification"]["image"] = payload.image_url

                    try:
                        resp = await client.post(fcm_url, headers=headers, json=message_body)
                        if resp.status_code == 200:
                            success_count += 1
                        else:
                            failure_count += 1
                            logger.warning(f"FCM send failed for {device.device_id}: {resp.status_code}")
                            if resp.status_code == 404:
                                await self._deactivate_device(device.device_id)
                    except Exception as send_err:
                        failure_count += 1
                        logger.error(f"FCM send error for {device.device_id}: {send_err}")

            logger.info(f"FCM notifications sent: {success_count} success, {failure_count} failed")
            return {"success_count": success_count, "failure_count": failure_count}

        except Exception as e:
            logger.error(f"FCM sending failed: {e}")
            return {"success_count": success_count, "failure_count": failure_count + len(android_devices) - success_count}

    async def _get_fcm_access_token(self, service_account_json: str) -> Optional[str]:
        """Get OAuth2 access token for FCM v1 API from service account credentials."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account

            sa_info = json.loads(service_account_json) if isinstance(service_account_json, str) else service_account_json
            credentials = service_account.Credentials.from_service_account_info(
                sa_info,
                scopes=["https://www.googleapis.com/auth/firebase.messaging"],
            )
            credentials.refresh(Request())
            return credentials.token
        except ImportError:
            logger.warning("google-auth not installed, FCM OAuth2 unavailable")
            return None
        except Exception as e:
            logger.error(f"Failed to get FCM access token: {e}")
            return None

    async def _deactivate_device(self, device_id: str) -> None:
        """Mark a device token as inactive after delivery failure."""
        try:
            cache_key = f"device_registration:{device_id}"
            reg_data = await self.cache.get(cache_key)
            if reg_data:
                reg_data["active"] = False
                await self.cache.set(cache_key, reg_data, ttl=86400 * 30)
                logger.info(f"Deactivated device {device_id} due to delivery failure")
        except Exception as e:
            logger.error(f"Failed to deactivate device {device_id}: {e}")

    async def _send_apns_notifications(
        self, ios_devices: List[DeviceRegistration], payload: NotificationPayload
    ) -> Dict[str, int]:
        """ROADMAP-059: Send notifications via APNS HTTP/2 with JWT auth."""
        success_count = 0
        failure_count = 0
        try:
            apns_key_id = getattr(settings, "apns_key_id", None)
            apns_team_id = getattr(settings, "apns_team_id", None)
            apns_key_path = getattr(settings, "apns_key_path", None)
            apns_bundle_id = getattr(settings, "apns_bundle_id", "com.enterprisehub.app")
            apns_use_sandbox = getattr(settings, "apns_use_sandbox", True)

            if not all([apns_key_id, apns_team_id, apns_key_path]):
                logger.warning("APNS credentials not fully configured, simulating send")
                return {"success_count": len(ios_devices), "failure_count": 0}

            jwt_token = self._generate_apns_jwt(apns_key_id, apns_team_id, apns_key_path)
            if not jwt_token:
                return {"success_count": 0, "failure_count": len(ios_devices)}

            host = "api.sandbox.push.apple.com" if apns_use_sandbox else "api.push.apple.com"

            apns_payload = {
                "aps": {
                    "alert": {
                        "title": payload.title,
                        "body": payload.body,
                    },
                    "sound": payload.sound or "default",
                },
            }
            if payload.badge_count is not None:
                apns_payload["aps"]["badge"] = payload.badge_count
            if payload.data:
                apns_payload["custom_data"] = payload.data

            priority = "10" if payload.priority in (
                NotificationPriority.HIGH, NotificationPriority.URGENT
            ) else "5"

            async with httpx.AsyncClient(http2=True, timeout=10.0) as client:
                for device in ios_devices:
                    device_token = device.apns_token or device.fcm_token
                    url = f"https://{host}/3/device/{device_token}"
                    headers = {
                        "authorization": f"bearer {jwt_token}",
                        "apns-topic": apns_bundle_id,
                        "apns-priority": priority,
                        "apns-push-type": "alert",
                    }
                    if payload.expiry_time:
                        headers["apns-expiration"] = str(int(payload.expiry_time.timestamp()))

                    try:
                        resp = await client.post(url, headers=headers, json=apns_payload)
                        if resp.status_code == 200:
                            success_count += 1
                        else:
                            failure_count += 1
                            logger.warning(f"APNS send failed for {device.device_id}: {resp.status_code}")
                            if resp.status_code in (400, 410):
                                await self._deactivate_device(device.device_id)
                    except Exception as send_err:
                        failure_count += 1
                        logger.error(f"APNS send error for {device.device_id}: {send_err}")

            logger.info(f"APNS notifications sent: {success_count} success, {failure_count} failed")
            return {"success_count": success_count, "failure_count": failure_count}

        except Exception as e:
            logger.error(f"APNS sending failed: {e}")
            return {"success_count": success_count, "failure_count": failure_count + len(ios_devices) - success_count}

    def _generate_apns_jwt(self, key_id: str, team_id: str, key_path: str) -> Optional[str]:
        """Generate JWT token for APNS authentication."""
        try:
            import time

            import jwt

            with open(key_path, "r") as f:
                auth_key = f.read()

            token = jwt.encode(
                {"iss": team_id, "iat": int(time.time())},
                auth_key,
                algorithm="ES256",
                headers={"alg": "ES256", "kid": key_id},
            )
            return token
        except ImportError:
            logger.warning("PyJWT not installed, APNS JWT generation unavailable")
            return None
        except Exception as e:
            logger.error(f"Failed to generate APNS JWT: {e}")
            return None

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
