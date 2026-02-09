"""
Lead Sequence Scheduler - Manages automated 3-7-30 day sequence execution.

Uses APScheduler to trigger lead sequence actions at the correct intervals.
Integrates with sequence state service for persistence and GHL for message delivery.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from ghl_real_estate_ai.api.schemas.ghl import MessageType
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.agent_state_sync import sync_service
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.lead_sequence_state_service import (
    SequenceDay,
    get_sequence_service,
)

logger = get_logger(__name__)


@dataclass
class ScheduledAction:
    """Represents a scheduled sequence action."""

    lead_id: str
    sequence_day: SequenceDay
    action_type: str  # "sms", "call", "email"
    scheduled_for: datetime
    job_id: str
    retry_count: int = 0
    max_retries: int = 3


class LeadSequenceScheduler:
    """Manages scheduling and execution of lead sequence actions."""

    def __init__(self):
        try:
            from apscheduler.executors.asyncio import AsyncIOExecutor
            from apscheduler.jobstores.redis import RedisJobStore
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from pytz import utc

            self.sequence_service = get_sequence_service()
            self.cache_service = get_cache_service()
            self.ghl_client = GHLClient()

            # Configure APScheduler with Redis persistence
            redis_url = settings.redis_url or "redis://localhost:6379/0"
            parsed = urlparse(redis_url)
            redis_host = parsed.hostname or "localhost"
            redis_port = parsed.port or 6379
            redis_password = parsed.password
            jobstores = {"default": RedisJobStore(host=redis_host, port=redis_port, db=1, password=redis_password)}
            executors = {"default": AsyncIOExecutor()}
            job_defaults = {"coalesce": False, "max_instances": 3, "misfire_grace_time": 30}

            self.scheduler = AsyncIOScheduler(
                jobstores=jobstores, executors=executors, job_defaults=job_defaults, timezone=utc
            )

            self.enabled = True
            logger.info("Initialized LeadSequenceScheduler with Redis persistence")

        except ImportError as e:
            logger.error(f"APScheduler dependencies missing: {e}")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}")
            self.enabled = False

    async def start(self):
        """Start the scheduler and restore any persisted jobs."""
        if not self.enabled:
            logger.warning("Scheduler not enabled due to initialization errors")
            return False

        try:
            self.scheduler.start()

            # Restore any active sequences that need scheduling
            await self._restore_pending_schedules()

            logger.info("Lead sequence scheduler started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            return False

    async def stop(self):
        """Stop the scheduler gracefully."""
        if self.enabled and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Lead sequence scheduler stopped")

    async def schedule_sequence_start(self, lead_id: str, delay_minutes: int = 0) -> bool:
        """Schedule the start of a new lead sequence."""
        if not self.enabled:
            logger.warning("Cannot schedule - scheduler not enabled")
            return False

        try:
            # Create or get sequence state
            sequence_state = await self.sequence_service.get_state(lead_id)
            if not sequence_state:
                sequence_state = await self.sequence_service.create_sequence(lead_id)

            # Schedule Day 3 action
            run_time = datetime.now() + timedelta(minutes=delay_minutes)
            job_id = f"lead_{lead_id}_day3_sms"

            self.scheduler.add_job(
                func=self._execute_sequence_action,
                trigger="date",
                run_date=run_time,
                args=[lead_id, SequenceDay.DAY_3, "sms"],
                id=job_id,
                replace_existing=True,
            )

            logger.info(f"Scheduled Day 3 SMS for lead {lead_id} at {run_time}")
            return True

        except Exception as e:
            logger.error(f"Failed to schedule sequence start for lead {lead_id}: {e}")
            return False

    async def schedule_next_action(self, lead_id: str, current_day: SequenceDay) -> bool:
        """Schedule the next action in the sequence based on current day."""
        if not self.enabled:
            return False

        try:
            now = datetime.now()

            # Calculate next action timing
            if current_day == SequenceDay.DAY_3:
                next_day = SequenceDay.DAY_7
                next_time = now + timedelta(days=4)
                action_type = "call"
            elif current_day == SequenceDay.DAY_7:
                next_day = SequenceDay.DAY_14
                next_time = now + timedelta(days=7)
                action_type = "email"
            elif current_day == SequenceDay.DAY_14:
                next_day = SequenceDay.DAY_30
                next_time = now + timedelta(days=16)
                action_type = "sms"
            else:
                # No more actions to schedule
                logger.info(f"No more actions to schedule for lead {lead_id}")
                return True

            job_id = f"lead_{lead_id}_{next_day.value}_{action_type}"

            self.scheduler.add_job(
                func=self._execute_sequence_action,
                trigger="date",
                run_date=next_time,
                args=[lead_id, next_day, action_type],
                id=job_id,
                replace_existing=True,
            )

            logger.info(f"Scheduled {next_day.value} {action_type} for lead {lead_id} at {next_time}")
            return True

        except Exception as e:
            logger.error(f"Failed to schedule next action for lead {lead_id}: {e}")
            return False

    async def _execute_sequence_action(self, lead_id: str, sequence_day: SequenceDay, action_type: str):
        """Execute a scheduled sequence action."""
        logger.info(f"Executing {sequence_day.value} {action_type} for lead {lead_id}")

        try:
            # Get current sequence state
            sequence_state = await self.sequence_service.get_state(lead_id)
            if not sequence_state:
                logger.error(f"No sequence state found for lead {lead_id}")
                return

            # Verify the action is still needed
            if sequence_day == SequenceDay.DAY_3 and sequence_state.day_3_completed:
                logger.info(f"Day 3 already completed for lead {lead_id}, skipping")
                return
            elif sequence_day == SequenceDay.DAY_7 and sequence_state.day_7_completed:
                logger.info(f"Day 7 already completed for lead {lead_id}, skipping")
                return
            elif sequence_day == SequenceDay.DAY_14 and sequence_state.day_14_completed:
                logger.info(f"Day 14 already completed for lead {lead_id}, skipping")
                return
            elif sequence_day == SequenceDay.DAY_30 and sequence_state.day_30_completed:
                logger.info(f"Day 30 already completed for lead {lead_id}, skipping")
                return

            # Execute the appropriate action
            if action_type == "sms":
                success = await self._send_sequence_sms(lead_id, sequence_day)
            elif action_type == "call":
                success = await self._initiate_sequence_call(lead_id, sequence_day)
            elif action_type == "email":
                success = await self._send_sequence_email(lead_id, sequence_day)
            else:
                logger.error(f"Unknown action type: {action_type}")
                return

            if success:
                # Mark action as completed
                await self.sequence_service.mark_action_completed(lead_id, sequence_day, f"{action_type}_delivered")

                # Schedule next action
                await self.schedule_next_action(lead_id, sequence_day)

                # Advance sequence state
                await self.sequence_service.advance_to_next_day(lead_id)

                logger.info(f"Successfully executed and advanced {sequence_day.value} {action_type} for lead {lead_id}")
            else:
                # Schedule retry
                await self._schedule_retry(lead_id, sequence_day, action_type)

        except Exception as e:
            logger.error(f"Error executing {sequence_day.value} {action_type} for lead {lead_id}: {e}")
            await self._schedule_retry(lead_id, sequence_day, action_type)

    async def _send_sequence_sms(self, lead_id: str, sequence_day: SequenceDay) -> bool:
        """Send SMS for the specified sequence day."""
        try:
            # Import here to avoid circular imports
            from ghl_real_estate_ai.services.ghost_followup_engine import GhostState, get_ghost_followup_engine

            # Get lead information (this would come from your lead database/GHL)
            # For now, we'll create a minimal state for the action
            ghost_engine = get_ghost_followup_engine()

            # Create ghost state for message generation
            ghost_state = GhostState(
                contact_id=lead_id,
                current_day=int(sequence_day.value.split("_")[1]) if "day_" in sequence_day.value else 3,
                frs_score=70,  # Default score, would normally come from sequence state
            )

            # Generate message content
            action = await ghost_engine.process_lead_step(ghost_state, [])
            message = action["content"]

            # Get lead contact information
            contact_info = await self._get_lead_contact_info(lead_id)
            if not contact_info:
                logger.error(f"Could not get contact info for lead {lead_id}")
                return False

            contact_id = contact_info.get("contact_id", lead_id)

            # Send SMS via GHL API
            try:
                logger.info(f"Sending SMS to contact {contact_id}: {message[:100]}...")

                response = await self.ghl_client.send_message(
                    contact_id=contact_id, message=message, channel=MessageType.SMS
                )

                if response and response.get("messageId"):
                    logger.info(f"Successfully sent SMS to contact {contact_id}, message_id: {response['messageId']}")
                else:
                    logger.warning(f"SMS sent but no message ID returned for contact {contact_id}")

            except Exception as ghl_error:
                logger.error(f"Failed to send SMS via GHL for contact {contact_id}: {ghl_error}")
                return False

            await sync_service.record_lead_event(lead_id, "AI", f"Scheduler sent {sequence_day.value} SMS", "sms")
            return True

        except Exception as e:
            logger.error(f"Failed to send SMS for lead {lead_id}, day {sequence_day.value}: {e}")
            return False

    async def _initiate_sequence_call(self, lead_id: str, sequence_day: SequenceDay) -> bool:
        """Initiate call for the specified sequence day with completion waiting."""
        try:
            from ghl_real_estate_ai.services.retell_call_manager import get_retell_call_manager

            call_manager = get_retell_call_manager()

            # Get lead contact information
            contact_info = await self._get_lead_contact_info(lead_id)
            if not contact_info:
                logger.error(f"Could not get contact info for lead {lead_id}")
                return False

            phone = contact_info.get("phone")
            if not phone:
                logger.error(f"No phone number available for lead {lead_id}")
                return False

            # Create comprehensive call context
            context = {
                "lead_id": lead_id,
                "lead_name": contact_info.get("name", f"Lead {lead_id}"),
                "sequence_day": sequence_day.value,
                "call_purpose": f"Day {sequence_day.value.split('_')[1]} follow-up call from Lead Bot sequence",
                "property_address": contact_info.get("property_address", "Unknown"),
                "lead_source": contact_info.get("source", "Web"),
                "created_by": "lead_bot_scheduler",
            }

            logger.info(f"Initiating {sequence_day.value} call for lead {lead_id}, phone {phone[-4:]}...")

            # Create call and wait for completion (not fire-and-forget)
            call_result = await call_manager.create_and_wait_for_call(
                lead_id=lead_id,
                phone=phone,
                context=context,
                max_wait_minutes=8,  # Reasonable wait time for lead calls
            )

            # Process call result
            if call_result.answered and call_result.duration_seconds > 30:
                # Successful call with meaningful interaction
                logger.info(
                    f"Successful {sequence_day.value} call for lead {lead_id}: {call_result.duration_seconds}s, engagement: {call_result.engagement_score}"
                )

                await sync_service.record_lead_event(
                    lead_id,
                    "AI",
                    f"Scheduler completed {sequence_day.value} call - {call_result.duration_seconds}s conversation",
                    "call_completed",
                )

                # Update sequence state with call results
                sequence_state = await self.sequence_service.get_state(lead_id)
                if sequence_state:
                    # Store call results in metadata
                    call_metadata = {
                        "call_id": call_result.call_id,
                        "duration_seconds": call_result.duration_seconds,
                        "engagement_score": call_result.engagement_score,
                        "summary": call_result.summary,
                        "completed_at": call_result.completed_at.isoformat() if call_result.completed_at else None,
                    }

                    # Update sequence state with call results
                    if sequence_day == SequenceDay.DAY_7:
                        sequence_state.day_7_call_metadata = call_metadata
                        sequence_state.day_7_delivered_at = datetime.now()

                    await self.sequence_service.save_state(sequence_state)

                return True

            elif call_result.status.value in ["no_answer", "busy"]:
                # No answer or busy - schedule retry
                logger.warning(f"{sequence_day.value} call for lead {lead_id} result: {call_result.status.value}")

                await sync_service.record_lead_event(
                    lead_id,
                    "AI",
                    f"Scheduler {sequence_day.value} call - {call_result.status.value}, will retry",
                    "call_no_answer",
                )

                # Return False to trigger retry logic
                return False

            else:
                # Call failed or other issue
                logger.error(
                    f"{sequence_day.value} call for lead {lead_id} failed: {call_result.status.value} - {call_result.error_message}"
                )

                await sync_service.record_lead_event(
                    lead_id,
                    "AI",
                    f"Scheduler {sequence_day.value} call failed: {call_result.error_message}",
                    "call_failed",
                )

                return False

        except Exception as e:
            logger.error(f"Failed to initiate call for lead {lead_id}, day {sequence_day.value}: {e}")
            return False

    async def _send_sequence_email(self, lead_id: str, sequence_day: SequenceDay) -> bool:
        """Send email for the specified sequence day."""
        try:
            from ghl_real_estate_ai.services.ghost_followup_engine import GhostState, get_ghost_followup_engine

            ghost_engine = get_ghost_followup_engine()

            ghost_state = GhostState(
                contact_id=lead_id,
                current_day=int(sequence_day.value.split("_")[1]) if "day_" in sequence_day.value else 14,
                frs_score=70,
            )

            action = await ghost_engine.process_lead_step(ghost_state, [])
            email_content = action["content"]

            # Get lead contact information
            contact_info = await self._get_lead_contact_info(lead_id)
            if not contact_info:
                logger.error(f"Could not get contact info for lead {lead_id}")
                return False

            contact_id = contact_info.get("contact_id", lead_id)

            # Send Email via GHL API
            try:
                logger.info(f"Sending email to contact {contact_id}: {email_content[:100]}...")

                response = await self.ghl_client.send_message(
                    contact_id=contact_id, message=email_content, channel=MessageType.EMAIL
                )

                if response and response.get("messageId"):
                    logger.info(f"Successfully sent email to contact {contact_id}, message_id: {response['messageId']}")
                else:
                    logger.warning(f"Email sent but no message ID returned for contact {contact_id}")

            except Exception as ghl_error:
                logger.error(f"Failed to send email via GHL for contact {contact_id}: {ghl_error}")
                return False

            await sync_service.record_lead_event(lead_id, "AI", f"Scheduler sent {sequence_day.value} email", "email")
            return True

        except Exception as e:
            logger.error(f"Failed to send email for lead {lead_id}, day {sequence_day.value}: {e}")
            return False

    async def _schedule_retry(self, lead_id: str, sequence_day: SequenceDay, action_type: str, retry_count: int = 1):
        """Schedule a retry for a failed action."""
        if retry_count > 3:
            logger.error(f"Max retries exceeded for {sequence_day.value} {action_type} for lead {lead_id}")
            await sync_service.record_lead_event(
                lead_id, "AI", f"Failed to deliver {sequence_day.value} {action_type} after 3 retries", "error"
            )
            return

        # Exponential backoff: 5 min, 15 min, 30 min
        delay_minutes = 5 * (retry_count**2)
        retry_time = datetime.now() + timedelta(minutes=delay_minutes)
        job_id = f"lead_{lead_id}_{sequence_day.value}_{action_type}_retry_{retry_count}"

        self.scheduler.add_job(
            func=self._execute_sequence_action,
            trigger="date",
            run_date=retry_time,
            args=[lead_id, sequence_day, action_type],
            id=job_id,
            replace_existing=True,
        )

        logger.info(
            f"Scheduled retry {retry_count} for {sequence_day.value} {action_type} for lead {lead_id} in {delay_minutes} minutes"
        )

    async def cancel_sequence(self, lead_id: str) -> bool:
        """Cancel all scheduled actions for a lead."""
        if not self.enabled:
            return False

        try:
            # Find and remove all jobs for this lead
            jobs = self.scheduler.get_jobs()
            cancelled_count = 0

            for job in jobs:
                if f"lead_{lead_id}_" in job.id:
                    self.scheduler.remove_job(job.id)
                    cancelled_count += 1

            logger.info(f"Cancelled {cancelled_count} scheduled actions for lead {lead_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel sequence for lead {lead_id}: {e}")
            return False

    async def pause_sequence(self, lead_id: str) -> bool:
        """Pause all scheduled actions for a lead."""
        if not self.enabled:
            return False

        try:
            jobs = self.scheduler.get_jobs()
            paused_count = 0

            for job in jobs:
                if f"lead_{lead_id}_" in job.id:
                    job.pause()
                    paused_count += 1

            await self.sequence_service.pause_sequence(lead_id, "scheduler_paused")
            logger.info(f"Paused {paused_count} scheduled actions for lead {lead_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to pause sequence for lead {lead_id}: {e}")
            return False

    async def resume_sequence(self, lead_id: str) -> bool:
        """Resume paused scheduled actions for a lead."""
        if not self.enabled:
            return False

        try:
            jobs = self.scheduler.get_jobs()
            resumed_count = 0

            for job in jobs:
                if f"lead_{lead_id}_" in job.id:
                    job.resume()
                    resumed_count += 1

            await self.sequence_service.resume_sequence(lead_id)
            logger.info(f"Resumed {resumed_count} scheduled actions for lead {lead_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to resume sequence for lead {lead_id}: {e}")
            return False

    async def _restore_pending_schedules(self):
        """Restore any sequences that need scheduling after restart."""
        try:
            # Get all active sequences that might need rescheduling
            active_sequences = await self.sequence_service.get_all_active_sequences()

            restored_count = 0
            for sequence in active_sequences:
                if sequence.next_scheduled_at and sequence.next_scheduled_at > datetime.now():
                    # Calculate action type based on current day
                    if sequence.current_day == SequenceDay.DAY_3:
                        action_type = "sms"
                    elif sequence.current_day == SequenceDay.DAY_7:
                        action_type = "call"
                    elif sequence.current_day == SequenceDay.DAY_14:
                        action_type = "email"
                    elif sequence.current_day == SequenceDay.DAY_30:
                        action_type = "sms"
                    else:
                        continue

                    job_id = f"lead_{sequence.lead_id}_{sequence.current_day.value}_{action_type}"

                    self.scheduler.add_job(
                        func=self._execute_sequence_action,
                        trigger="date",
                        run_date=sequence.next_scheduled_at,
                        args=[sequence.lead_id, sequence.current_day, action_type],
                        id=job_id,
                        replace_existing=True,
                    )

                    restored_count += 1

            logger.info(f"Restored {restored_count} pending sequence schedules")

        except Exception as e:
            logger.error(f"Failed to restore pending schedules: {e}")

    async def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status and job counts."""
        if not self.enabled:
            return {"enabled": False, "error": "Scheduler not initialized"}

        try:
            jobs = self.scheduler.get_jobs()

            # Categorize jobs by lead
            lead_jobs = {}
            for job in jobs:
                if "lead_" in job.id:
                    parts = job.id.split("_")
                    if len(parts) >= 2:
                        lead_id = parts[1]
                        if lead_id not in lead_jobs:
                            lead_jobs[lead_id] = []
                        lead_jobs[lead_id].append(
                            {
                                "job_id": job.id,
                                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                                "paused": job.coalesce if hasattr(job, "coalesce") else False,
                            }
                        )

            return {
                "enabled": True,
                "running": self.scheduler.running,
                "total_jobs": len(jobs),
                "lead_count": len(lead_jobs),
                "lead_jobs": lead_jobs,
            }

        except Exception as e:
            logger.error(f"Failed to get scheduler status: {e}")
            return {"enabled": True, "error": str(e)}

    async def _get_lead_contact_info(self, lead_id: str) -> Optional[Dict[str, str]]:
        """Get lead contact information from GHL."""
        try:
            # Check cache first
            contact_key = f"contact:{lead_id}"
            cached_contact = await self.cache_service.get(contact_key)

            if cached_contact:
                logger.debug(f"Using cached contact info for lead {lead_id}")
                return cached_contact

            # Fetch from GHL API
            # First, assume lead_id is the GHL contact_id
            try:
                contact_data = await self.ghl_client.get_contact(lead_id)

                if contact_data:
                    # Extract relevant information
                    contact_info = {
                        "contact_id": contact_data.get("id", lead_id),
                        "phone": contact_data.get("phone"),
                        "email": contact_data.get("email"),
                        "first_name": contact_data.get("firstName", ""),
                        "last_name": contact_data.get("lastName", ""),
                        "full_name": f"{contact_data.get('firstName', '')} {contact_data.get('lastName', '')}".strip(),
                    }

                    # Cache for 1 hour
                    await self.cache_service.set(contact_key, contact_info, ttl=3600)
                    logger.info(f"Fetched and cached contact info for {contact_info['full_name']} ({lead_id})")
                    return contact_info

            except Exception as api_error:
                logger.warning(f"Could not fetch contact {lead_id} from GHL API: {api_error}")

            # Fallback: treat lead_id as contact_id (for compatibility)
            logger.info(f"Falling back to using lead_id {lead_id} as GHL contact_id")

            fallback_info = {
                "contact_id": lead_id,
                "phone": None,
                "email": None,
                "first_name": "Lead",
                "last_name": lead_id[-4:],  # Last 4 chars as identifier
                "full_name": f"Lead {lead_id[-4:]}",
            }

            # Cache fallback info for shorter time
            await self.cache_service.set(contact_key, fallback_info, ttl=300)
            return fallback_info

        except Exception as e:
            logger.error(f"Failed to get contact info for lead {lead_id}: {e}")
            return None

    async def _get_contact_phone(self, contact_id: str) -> Optional[str]:
        """Get contact phone number from GHL."""
        try:
            # Note: GHL send_message uses contact_id, not phone number directly
            # We still return the contact_id which is what we need
            return contact_id
        except Exception as e:
            logger.error(f"Failed to get phone for contact {contact_id}: {e}")
            return None

    async def _get_contact_email(self, contact_id: str) -> Optional[str]:
        """Get contact email from GHL."""
        try:
            # Note: GHL send_message uses contact_id, not email directly
            # We still return the contact_id which is what we need
            return contact_id
        except Exception as e:
            logger.error(f"Failed to get email for contact {contact_id}: {e}")
            return None


# Global service instance
_scheduler: Optional[LeadSequenceScheduler] = None


def get_lead_scheduler() -> LeadSequenceScheduler:
    """Get global lead scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = LeadSequenceScheduler()
    return _scheduler


async def start_lead_scheduler() -> bool:
    """Start the global lead scheduler."""
    scheduler = get_lead_scheduler()
    return await scheduler.start()


async def stop_lead_scheduler():
    """Stop the global lead scheduler."""
    scheduler = get_lead_scheduler()
    await scheduler.stop()
