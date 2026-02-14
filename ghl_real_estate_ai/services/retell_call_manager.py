"""
Retell Call Manager - Handles voice call creation and completion monitoring

Bridges the gap between Lead Bot scheduler and Retell.AI voice calls.
Provides call completion waiting (not fire-and-forget) and result processing.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.integrations.retell import RetellClient
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)


class CallStatus(Enum):
    """Call status enumeration"""

    QUEUED = "queued"
    RINGING = "ringing"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    CANCELLED = "cancelled"


@dataclass
class CallResult:
    """Result of a completed call"""

    call_id: str
    status: CallStatus
    duration_seconds: int
    answered: bool
    transcript: Optional[str] = None
    summary: Optional[str] = None
    engagement_score: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime = None
    completed_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class RetellCallManager:
    """
    Manages Retell.AI call creation and completion monitoring

    Unlike fire-and-forget calls, this manager waits for call completion
    and provides detailed results for Lead Bot sequence management.
    """

    def __init__(self):
        self.retell_client = RetellClient()
        self.cache_service = get_cache_service()
        self.max_wait_minutes = 10  # Maximum time to wait for call completion
        self.poll_interval_seconds = 10  # How often to check call status

    async def create_and_wait_for_call(
        self, lead_id: str, phone: str, context: Dict[str, Any], max_wait_minutes: Optional[int] = None
    ) -> CallResult:
        """
        Create a Retell call and wait for completion

        Args:
            lead_id: Lead identifier for tracking
            phone: Phone number to call
            context: Call context (lead info, sequence day, purpose)
            max_wait_minutes: Optional override for max wait time

        Returns:
            CallResult with completion status and details
        """
        try:
            max_wait = max_wait_minutes or self.max_wait_minutes
            logger.info(f"Creating Retell call for lead {lead_id}, phone {phone[-4:]}...")

            # Prepare call configuration
            call_config = {
                "agent_id": "your_retell_agent_id",  # Configure your Retell agent
                "to_number": phone,
                "from_number": "+15125551234",  # Configure your Retell number
                "metadata": {
                    "lead_id": lead_id,
                    "sequence_day": context.get("sequence_day", "unknown"),
                    "call_purpose": context.get("call_purpose", "follow_up"),
                    "lead_name": context.get("lead_name", f"Lead {lead_id}"),
                    "created_by": "lead_bot_scheduler",
                },
            }

            # Create the call
            call_response = await self.retell_client.create_call(call_config)

            if not call_response or not call_response.get("call_id"):
                error_msg = "Failed to create call - no call ID returned"
                logger.error(f"{error_msg} for lead {lead_id}")
                return CallResult(
                    call_id="", status=CallStatus.FAILED, duration_seconds=0, answered=False, error_message=error_msg
                )

            call_id = call_response["call_id"]
            logger.info(f"Created Retell call {call_id} for lead {lead_id}")

            # Cache call info for tracking
            await self._cache_call_info(call_id, lead_id, context)

            # Wait for call completion
            result = await self._wait_for_call_completion(call_id, max_wait)

            # Update cache with final result
            await self._cache_call_result(call_id, result)

            return result

        except Exception as e:
            error_msg = f"Exception creating call for lead {lead_id}: {str(e)}"
            logger.error(error_msg)
            return CallResult(
                call_id="", status=CallStatus.FAILED, duration_seconds=0, answered=False, error_message=error_msg
            )

    async def _wait_for_call_completion(self, call_id: str, max_wait_minutes: int) -> CallResult:
        """
        Poll call status until completion or timeout

        This replaces the fire-and-forget behavior with actual completion waiting
        """
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=max_wait_minutes)

        logger.info(f"Waiting for call {call_id} completion (max {max_wait_minutes} minutes)...")

        while datetime.now() < end_time:
            try:
                # Get current call status
                status_response = await self.retell_client.get_call_status(call_id)

                if not status_response:
                    await asyncio.sleep(self.poll_interval_seconds)
                    continue

                call_status = status_response.get("status", "unknown").lower()
                logger.debug(f"Call {call_id} status: {call_status}")

                # Check if call is completed (any terminal state)
                if call_status in ["completed", "failed", "no_answer", "busy", "cancelled"]:
                    logger.info(f"Call {call_id} completed with status: {call_status}")

                    # Get full call details
                    call_details = await self.retell_client.get_call_details(call_id)

                    return await self._build_call_result(call_id, call_status, call_details)

                # Call still in progress, continue waiting
                await asyncio.sleep(self.poll_interval_seconds)

            except Exception as e:
                logger.error(f"Error polling call {call_id} status: {e}")
                await asyncio.sleep(self.poll_interval_seconds)

        # Timeout reached
        logger.warning(f"Call {call_id} monitoring timed out after {max_wait_minutes} minutes")

        return CallResult(
            call_id=call_id,
            status=CallStatus.FAILED,
            duration_seconds=0,
            answered=False,
            error_message=f"Monitoring timeout after {max_wait_minutes} minutes",
            completed_at=datetime.now(),
        )

    async def _build_call_result(self, call_id: str, status: str, details: Dict[str, Any]) -> CallResult:
        """Build CallResult from Retell API response"""
        try:
            # Map Retell status to our enum
            status_mapping = {
                "completed": CallStatus.COMPLETED,
                "failed": CallStatus.FAILED,
                "no_answer": CallStatus.NO_ANSWER,
                "busy": CallStatus.BUSY,
                "cancelled": CallStatus.CANCELLED,
            }

            call_status = status_mapping.get(status, CallStatus.FAILED)

            # Extract call details
            duration = details.get("duration_seconds", 0)
            answered = call_status == CallStatus.COMPLETED and duration > 0
            transcript = details.get("transcript", "")

            # Calculate engagement score based on call length and interaction
            engagement_score = self._calculate_engagement_score(duration, transcript)

            # Generate summary if transcript exists
            summary = await self._generate_call_summary(transcript) if transcript else None

            logger.info(f"Call {call_id} result: {call_status.value}, duration: {duration}s, answered: {answered}")

            return CallResult(
                call_id=call_id,
                status=call_status,
                duration_seconds=duration,
                answered=answered,
                transcript=transcript,
                summary=summary,
                engagement_score=engagement_score,
                completed_at=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Error building call result for {call_id}: {e}")
            return CallResult(
                call_id=call_id,
                status=CallStatus.FAILED,
                duration_seconds=0,
                answered=False,
                error_message=str(e),
                completed_at=datetime.now(),
            )

    def _calculate_engagement_score(self, duration: int, transcript: str) -> float:
        """
        Calculate engagement score based on call metrics

        Returns score from 0.0 to 1.0 indicating lead engagement level
        """
        try:
            if duration == 0:
                return 0.0

            # Base score from call duration
            duration_score = min(duration / 180, 1.0)  # Max at 3 minutes

            # Transcript-based scoring
            transcript_score = 0.0
            if transcript:
                word_count = len(transcript.split())
                transcript_score = min(word_count / 100, 1.0)  # Max at 100 words

                # Bonus for positive keywords
                positive_keywords = ["yes", "interested", "tell me more", "when", "how"]
                bonus = sum(0.1 for keyword in positive_keywords if keyword.lower() in transcript.lower())
                transcript_score = min(transcript_score + bonus, 1.0)

            # Weighted average
            final_score = (duration_score * 0.6) + (transcript_score * 0.4)

            return round(final_score, 2)

        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 0.0

    async def _generate_call_summary(self, transcript: str) -> Optional[str]:
        """Generate a brief summary of the call interaction"""
        try:
            if not transcript or len(transcript.strip()) < 10:
                return None

            # Simple summarization logic
            # In production, you might use Claude API or another LLM for this
            word_count = len(transcript.split())

            if word_count < 20:
                return "Brief interaction"
            elif word_count < 50:
                return "Short conversation"
            elif word_count < 100:
                return "Moderate discussion"
            else:
                return "Extended conversation"

        except Exception as e:
            logger.error(f"Error generating call summary: {e}")
            return None

    async def _cache_call_info(self, call_id: str, lead_id: str, context: Dict[str, Any]):
        """Cache call information for tracking"""
        try:
            cache_key = f"retell_call:{call_id}"
            cache_data = {
                "call_id": call_id,
                "lead_id": lead_id,
                "context": context,
                "created_at": datetime.now().isoformat(),
                "status": "initiated",
            }

            # Cache for 24 hours
            await self.cache_service.set_json(cache_key, cache_data, ttl=86400)

        except Exception as e:
            logger.error(f"Error caching call info for {call_id}: {e}")

    async def _cache_call_result(self, call_id: str, result: CallResult):
        """Cache final call result"""
        try:
            cache_key = f"retell_call_result:{call_id}"
            cache_data = {
                "call_id": result.call_id,
                "status": result.status.value,
                "duration_seconds": result.duration_seconds,
                "answered": result.answered,
                "transcript": result.transcript,
                "summary": result.summary,
                "engagement_score": result.engagement_score,
                "error_message": result.error_message,
                "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            }

            # Cache for 7 days
            await self.cache_service.set_json(cache_key, cache_data, ttl=604800)

        except Exception as e:
            logger.error(f"Error caching call result for {call_id}: {e}")

    async def get_call_status(self, call_id: str) -> Optional[CallResult]:
        """Get cached call result"""
        try:
            cache_key = f"retell_call_result:{call_id}"
            cached_data = await self.cache_service.get_json(cache_key)

            if not cached_data:
                return None

            return CallResult(
                call_id=cached_data["call_id"],
                status=CallStatus(cached_data["status"]),
                duration_seconds=cached_data["duration_seconds"],
                answered=cached_data["answered"],
                transcript=cached_data.get("transcript"),
                summary=cached_data.get("summary"),
                engagement_score=cached_data.get("engagement_score"),
                error_message=cached_data.get("error_message"),
                completed_at=datetime.fromisoformat(cached_data["completed_at"])
                if cached_data.get("completed_at")
                else None,
            )

        except Exception as e:
            logger.error(f"Error getting call status for {call_id}: {e}")
            return None

    async def cancel_call(self, call_id: str) -> bool:
        """Cancel an active call"""
        try:
            response = await self.retell_client.cancel_call(call_id)

            if response and response.get("success"):
                logger.info(f"Successfully cancelled call {call_id}")

                # Update cache
                result = CallResult(
                    call_id=call_id,
                    status=CallStatus.CANCELLED,
                    duration_seconds=0,
                    answered=False,
                    completed_at=datetime.now(),
                )
                await self._cache_call_result(call_id, result)

                return True
            else:
                logger.warning(f"Failed to cancel call {call_id}")
                return False

        except Exception as e:
            logger.error(f"Error cancelling call {call_id}: {e}")
            return False


# Singleton instance
_retell_call_manager = None


def get_retell_call_manager() -> RetellCallManager:
    """Get singleton RetellCallManager instance"""
    global _retell_call_manager
    if _retell_call_manager is None:
        _retell_call_manager = RetellCallManager()
    return _retell_call_manager
