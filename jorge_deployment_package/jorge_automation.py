#!/usr/bin/env python3
"""
Jorge's Automation System - Scheduling & Follow-up

This system handles automated scheduling, follow-up sequences, and client
communication to ensure no leads fall through the cracks.

Author: Claude Code Assistant
Created: 2026-01-22
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import schedule
import threading
import time

# Import the bot services
from jorge_lead_bot import JorgeLeadBot
from jorge_seller_bot import JorgeSellerBot
from ghl_client import GHLClient

logger = logging.getLogger(__name__)


class FollowUpType(Enum):
    """Types of automated follow-ups"""
    INITIAL_RESPONSE = "initial_response"      # Immediate response to new lead
    QUALIFICATION_FOLLOWUP = "qualification"   # Follow up incomplete qualification
    NURTURE_SEQUENCE = "nurture"              # Long-term nurturing
    APPOINTMENT_REMINDER = "appointment"       # Appointment reminders
    HOT_LEAD_ESCALATION = "hot_escalation"    # Urgent hot lead follow-up


class ScheduleType(Enum):
    """Types of scheduling automation"""
    CONSULTATION_CALL = "consultation"         # Initial consultation calls
    PROPERTY_SHOWING = "showing"              # Property showings
    LISTING_APPOINTMENT = "listing"           # Listing appointments
    FOLLOW_UP_CALL = "followup_call"          # Follow-up calls


@dataclass
class AutomationTask:
    """Represents an automation task to be executed"""
    task_id: str
    contact_id: str
    location_id: str
    task_type: str  # FollowUpType or ScheduleType
    scheduled_time: datetime
    data: Dict[str, Any]
    priority: int = 5  # 1-10, 1 being highest priority
    retry_count: int = 0
    max_retries: int = 3


@dataclass 
class AutomationResult:
    """Result from automation task execution"""
    task_id: str
    success: bool
    message: str
    next_action: Optional[AutomationTask] = None
    error: Optional[str] = None


class JorgeAutomationSystem:
    """
    Comprehensive automation system for Jorge's real estate bots.
    
    Features:
    - Automated follow-up sequences
    - Smart scheduling
    - Appointment reminders  
    - Lead nurturing campaigns
    - Hot lead escalation
    - Performance monitoring
    """

    def __init__(self, ghl_client: Optional[GHLClient] = None):
        """Initialize automation system"""
        
        self.ghl_client = ghl_client or GHLClient()
        self.lead_bot = JorgeLeadBot(ghl_client)
        self.seller_bot = JorgeSellerBot(ghl_client)
        
        # Task management
        self.pending_tasks: List[AutomationTask] = []
        self.completed_tasks: List[AutomationTask] = []
        self.failed_tasks: List[AutomationTask] = []
        
        # Automation state
        self.is_running = False
        self.scheduler_thread = None
        
        # Performance tracking
        self.automation_stats = {
            "tasks_executed": 0,
            "tasks_failed": 0,
            "average_response_time": 0.0,
            "last_execution": None
        }
        
        self.logger = logging.getLogger(__name__)

    def start_automation(self):
        """Start the automation system"""
        
        if self.is_running:
            self.logger.warning("Automation system is already running")
            return
            
        self.is_running = True
        self.logger.info("Starting Jorge's automation system...")
        
        # Set up scheduled tasks
        self._setup_scheduled_tasks()
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Automation system started successfully")

    def stop_automation(self):
        """Stop the automation system"""
        
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
            
        self.logger.info("Automation system stopped")

    def schedule_follow_up(
        self,
        contact_id: str,
        location_id: str,
        followup_type: FollowUpType,
        delay_minutes: int = 0,
        delay_hours: int = 0,
        delay_days: int = 0,
        data: Optional[Dict] = None
    ) -> str:
        """
        Schedule a follow-up task.
        
        Args:
            contact_id: GHL contact ID
            location_id: GHL location ID
            followup_type: Type of follow-up
            delay_minutes: Minutes to wait before execution
            delay_hours: Hours to wait before execution  
            delay_days: Days to wait before execution
            data: Additional data for the task
            
        Returns:
            Task ID for tracking
        """
        
        # Calculate execution time
        execution_time = datetime.now() + timedelta(
            minutes=delay_minutes,
            hours=delay_hours, 
            days=delay_days
        )
        
        # Create task
        task = AutomationTask(
            task_id=f"followup_{contact_id}_{int(time.time())}",
            contact_id=contact_id,
            location_id=location_id,
            task_type=followup_type.value,
            scheduled_time=execution_time,
            data=data or {},
            priority=self._get_followup_priority(followup_type)
        )
        
        # Add to pending tasks
        self.pending_tasks.append(task)
        self.pending_tasks.sort(key=lambda t: (t.scheduled_time, t.priority))
        
        self.logger.info(
            f"Scheduled {followup_type.value} for contact {contact_id} "
            f"at {execution_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return task.task_id

    def schedule_appointment(
        self,
        contact_id: str,
        location_id: str,
        appointment_type: ScheduleType,
        preferred_time: Optional[datetime] = None,
        data: Optional[Dict] = None
    ) -> str:
        """
        Schedule an appointment.
        
        Args:
            contact_id: GHL contact ID
            location_id: GHL location ID
            appointment_type: Type of appointment
            preferred_time: Preferred appointment time
            data: Additional appointment data
            
        Returns:
            Task ID for tracking
        """
        
        # Use preferred time or default to next business day
        if not preferred_time:
            preferred_time = self._get_next_business_slot()
            
        # Create scheduling task
        task = AutomationTask(
            task_id=f"schedule_{contact_id}_{int(time.time())}",
            contact_id=contact_id,
            location_id=location_id,
            task_type=appointment_type.value,
            scheduled_time=datetime.now() + timedelta(minutes=5),  # Process soon
            data={
                "appointment_time": preferred_time.isoformat(),
                "appointment_type": appointment_type.value,
                **(data or {})
            },
            priority=2  # High priority for appointments
        )
        
        self.pending_tasks.append(task)
        self.pending_tasks.sort(key=lambda t: (t.scheduled_time, t.priority))
        
        self.logger.info(
            f"Scheduled {appointment_type.value} for contact {contact_id} "
            f"at {preferred_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        return task.task_id

    async def execute_task(self, task: AutomationTask) -> AutomationResult:
        """Execute a single automation task"""
        
        try:
            self.logger.info(f"Executing task {task.task_id} ({task.task_type})")
            start_time = time.time()
            
            # Execute based on task type
            if task.task_type in [ft.value for ft in FollowUpType]:
                result = await self._execute_followup_task(task)
            elif task.task_type in [st.value for st in ScheduleType]:
                result = await self._execute_scheduling_task(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
            
            # Update stats
            execution_time = time.time() - start_time
            self._update_automation_stats(execution_time, success=result.success)
            
            # Move to appropriate list
            if result.success:
                self.completed_tasks.append(task)
            else:
                task.retry_count += 1
                if task.retry_count >= task.max_retries:
                    self.failed_tasks.append(task)
                else:
                    # Reschedule with exponential backoff
                    task.scheduled_time = datetime.now() + timedelta(minutes=2 ** task.retry_count)
                    self.pending_tasks.append(task)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            
            # Handle failure
            task.retry_count += 1
            if task.retry_count >= task.max_retries:
                self.failed_tasks.append(task)
            
            return AutomationResult(
                task_id=task.task_id,
                success=False,
                message="Task execution failed",
                error=str(e)
            )

    async def _execute_followup_task(self, task: AutomationTask) -> AutomationResult:
        """Execute a follow-up task"""
        
        followup_type = FollowUpType(task.task_type)
        
        try:
            if followup_type == FollowUpType.INITIAL_RESPONSE:
                # Send initial response to new lead
                message = "Thanks for your interest! I'll review your information and get back to you within the hour with next steps."
                
            elif followup_type == FollowUpType.QUALIFICATION_FOLLOWUP:
                # Follow up on incomplete qualification
                lead_analytics = await self.lead_bot.get_lead_analytics(task.contact_id, task.location_id)
                
                if lead_analytics.get("qualification_status") == "Needs Qualification":
                    message = "Hi! I wanted to follow up on your property search. Do you have 2 minutes to answer a quick question about your timeline?"
                else:
                    message = "Just checking in on your home search. Any updates on your timeline or requirements?"
                    
            elif followup_type == FollowUpType.NURTURE_SEQUENCE:
                # Long-term nurturing message
                messages = [
                    "Market update: Home inventory is still low in your area. Great time for buyers!",
                    "New listings just came on the market in your preferred area. Worth taking a look?",
                    "Interest rates shifted this week. This could affect your buying power. Let's chat.",
                    "Price reduction alert: A few properties in your range just dropped their prices."
                ]
                message = messages[task.retry_count % len(messages)]
                
            elif followup_type == FollowUpType.HOT_LEAD_ESCALATION:
                # Urgent hot lead follow-up
                message = "Jorge here. I saw your interest in our listing. Can we schedule a quick 10-minute call today? I have some options that just came on the market."
                
            elif followup_type == FollowUpType.APPOINTMENT_REMINDER:
                # Appointment reminder
                appointment_time = task.data.get("appointment_time", "tomorrow")
                message = f"Reminder: We have our call scheduled for {appointment_time}. Looking forward to helping you with your real estate goals!"
                
            else:
                message = "Thanks for your interest. Our team will be in touch soon."
            
            # Send message via GHL
            await self.ghl_client.send_message(task.contact_id, message)
            
            # Update contact with follow-up tag
            await self.ghl_client.add_tag(task.contact_id, f"FollowUp-{followup_type.value}")
            
            # Schedule next follow-up if appropriate
            next_task = self._determine_next_followup(task, followup_type)
            
            return AutomationResult(
                task_id=task.task_id,
                success=True,
                message=f"Follow-up sent successfully: {message[:50]}...",
                next_action=next_task
            )
            
        except Exception as e:
            self.logger.error(f"Follow-up task failed: {e}")
            return AutomationResult(
                task_id=task.task_id,
                success=False,
                message="Follow-up failed",
                error=str(e)
            )

    async def _execute_scheduling_task(self, task: AutomationTask) -> AutomationResult:
        """Execute a scheduling task"""
        
        schedule_type = ScheduleType(task.task_type)
        
        try:
            appointment_time = task.data.get("appointment_time")
            
            if schedule_type == ScheduleType.CONSULTATION_CALL:
                # Schedule consultation call
                calendar_result = await self._create_calendar_appointment(
                    contact_id=task.contact_id,
                    appointment_type="Consultation Call",
                    appointment_time=appointment_time,
                    duration_minutes=30
                )
                
                # Send confirmation message
                message = f"Perfect! I've scheduled our consultation call for {appointment_time}. You'll receive a calendar invite shortly."
                
            elif schedule_type == ScheduleType.PROPERTY_SHOWING:
                # Schedule property showing
                property_address = task.data.get("property_address", "the property")
                calendar_result = await self._create_calendar_appointment(
                    contact_id=task.contact_id,
                    appointment_type=f"Property Showing - {property_address}",
                    appointment_time=appointment_time,
                    duration_minutes=60
                )
                
                message = f"Great! Property showing scheduled for {appointment_time} at {property_address}. See you there!"
                
            elif schedule_type == ScheduleType.LISTING_APPOINTMENT:
                # Schedule listing appointment
                calendar_result = await self._create_calendar_appointment(
                    contact_id=task.contact_id,
                    appointment_type="Listing Consultation", 
                    appointment_time=appointment_time,
                    duration_minutes=90
                )
                
                message = f"Excellent! Listing consultation scheduled for {appointment_time}. I'll bring comps and market analysis."
                
            else:  # FOLLOW_UP_CALL
                calendar_result = await self._create_calendar_appointment(
                    contact_id=task.contact_id,
                    appointment_type="Follow-up Call",
                    appointment_time=appointment_time,
                    duration_minutes=15
                )
                
                message = f"Follow-up call scheduled for {appointment_time}. Talk soon!"
            
            # Send confirmation
            await self.ghl_client.send_message(task.contact_id, message)
            
            # Add tags
            await self.ghl_client.add_tag(task.contact_id, "Appointment-Scheduled")
            await self.ghl_client.add_tag(task.contact_id, f"Appt-{schedule_type.value}")
            
            # Schedule reminder
            reminder_task = self._create_appointment_reminder(task)
            
            return AutomationResult(
                task_id=task.task_id,
                success=True,
                message=f"Appointment scheduled successfully for {appointment_time}",
                next_action=reminder_task
            )
            
        except Exception as e:
            self.logger.error(f"Scheduling task failed: {e}")
            return AutomationResult(
                task_id=task.task_id,
                success=False,
                message="Scheduling failed",
                error=str(e)
            )

    async def _create_calendar_appointment(
        self,
        contact_id: str,
        appointment_type: str,
        appointment_time: str,
        duration_minutes: int
    ) -> Dict[str, Any]:
        """Create calendar appointment in GHL"""
        
        try:
            # Parse appointment time
            appt_datetime = datetime.fromisoformat(appointment_time.replace('Z', '+00:00'))
            
            # Create appointment data
            appointment_data = {
                "title": appointment_type,
                "startTime": appt_datetime.isoformat(),
                "endTime": (appt_datetime + timedelta(minutes=duration_minutes)).isoformat(),
                "contactId": contact_id,
                "calendarId": "jorge_main_calendar",  # Configure this for Jorge's calendar
                "description": f"Automated booking via Jorge's bot system"
            }
            
            # Create via GHL API
            result = await self.ghl_client.create_appointment(appointment_data)
            
            self.logger.info(f"Calendar appointment created: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"Calendar appointment creation failed: {e}")
            raise e

    def _setup_scheduled_tasks(self):
        """Set up recurring scheduled tasks"""
        
        # Daily tasks
        schedule.every().day.at("09:00").do(self._daily_lead_review)
        schedule.every().day.at("17:00").do(self._end_of_day_summary)
        
        # Hourly tasks  
        schedule.every().hour.do(self._process_pending_tasks)
        
        # Every 15 minutes
        schedule.every(15).minutes.do(self._check_hot_leads)
        
        # Every 5 minutes
        schedule.every(5).minutes.do(self._process_urgent_tasks)

    def _run_scheduler(self):
        """Run the task scheduler"""
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                self.logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Wait a minute before retrying

    def _process_pending_tasks(self):
        """Process pending tasks that are due"""
        
        if not self.pending_tasks:
            return
            
        current_time = datetime.now()
        due_tasks = [t for t in self.pending_tasks if t.scheduled_time <= current_time]
        
        if due_tasks:
            self.logger.info(f"Processing {len(due_tasks)} due tasks")
            
            # Process in separate thread to avoid blocking scheduler
            def process_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    for task in due_tasks:
                        if task in self.pending_tasks:
                            self.pending_tasks.remove(task)
                        loop.run_until_complete(self.execute_task(task))
                finally:
                    loop.close()
            
            threading.Thread(target=process_async, daemon=True).start()

    def _check_hot_leads(self):
        """Check for hot leads that need immediate attention"""
        
        # This would query GHL for hot leads and create urgent follow-up tasks
        self.logger.debug("Checking for hot leads...")

    def _daily_lead_review(self):
        """Daily lead review and follow-up planning"""
        
        self.logger.info("Performing daily lead review...")
        
        # This would:
        # 1. Review all leads from past 24 hours
        # 2. Identify leads that need follow-up
        # 3. Schedule appropriate follow-up sequences
        # 4. Generate daily report

    def _end_of_day_summary(self):
        """Generate end of day automation summary"""
        
        summary = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tasks_processed": len(self.completed_tasks),
            "tasks_failed": len(self.failed_tasks),
            "pending_tasks": len(self.pending_tasks),
            "automation_stats": self.automation_stats
        }
        
        self.logger.info(f"End of day summary: {summary}")

    def _get_followup_priority(self, followup_type: FollowUpType) -> int:
        """Get priority for follow-up type (1=highest, 10=lowest)"""
        
        priority_map = {
            FollowUpType.HOT_LEAD_ESCALATION: 1,
            FollowUpType.APPOINTMENT_REMINDER: 2,
            FollowUpType.INITIAL_RESPONSE: 3,
            FollowUpType.QUALIFICATION_FOLLOWUP: 4,
            FollowUpType.NURTURE_SEQUENCE: 7
        }
        
        return priority_map.get(followup_type, 5)

    def _get_next_business_slot(self) -> datetime:
        """Get next available business time slot"""
        
        now = datetime.now()
        
        # Business hours: 9 AM to 6 PM, Monday to Friday
        if now.weekday() >= 5:  # Weekend
            # Next Monday at 9 AM
            days_ahead = 7 - now.weekday()
            next_slot = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)
        elif now.hour < 9:
            # Today at 9 AM
            next_slot = now.replace(hour=9, minute=0, second=0, microsecond=0)
        elif now.hour >= 18:
            # Tomorrow at 9 AM (or Monday if Friday evening)
            if now.weekday() == 4:  # Friday
                next_slot = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=3)
            else:
                next_slot = now.replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        else:
            # Next hour during business hours
            next_slot = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
        return next_slot

    def _determine_next_followup(self, current_task: AutomationTask, followup_type: FollowUpType) -> Optional[AutomationTask]:
        """Determine if a next follow-up is needed"""
        
        # Logic to determine next follow-up based on current task and type
        # For demo purposes, return None (no automatic next follow-up)
        return None

    def _create_appointment_reminder(self, appointment_task: AutomationTask) -> AutomationTask:
        """Create appointment reminder task"""
        
        appointment_time = datetime.fromisoformat(appointment_task.data["appointment_time"])
        reminder_time = appointment_time - timedelta(hours=2)  # 2 hours before
        
        return AutomationTask(
            task_id=f"reminder_{appointment_task.contact_id}_{int(time.time())}",
            contact_id=appointment_task.contact_id,
            location_id=appointment_task.location_id,
            task_type=FollowUpType.APPOINTMENT_REMINDER.value,
            scheduled_time=reminder_time,
            data=appointment_task.data,
            priority=2
        )

    def _update_automation_stats(self, execution_time: float, success: bool):
        """Update automation performance statistics"""
        
        if success:
            self.automation_stats["tasks_executed"] += 1
        else:
            self.automation_stats["tasks_failed"] += 1
            
        # Update average response time
        current_avg = self.automation_stats["average_response_time"]
        total_tasks = self.automation_stats["tasks_executed"] + self.automation_stats["tasks_failed"]
        
        self.automation_stats["average_response_time"] = (
            (current_avg * (total_tasks - 1) + execution_time) / total_tasks
        )
        
        self.automation_stats["last_execution"] = datetime.now().isoformat()

    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation system status"""
        
        return {
            "is_running": self.is_running,
            "pending_tasks": len(self.pending_tasks),
            "completed_today": len([t for t in self.completed_tasks if t.scheduled_time.date() == datetime.now().date()]),
            "failed_today": len([t for t in self.failed_tasks if t.scheduled_time.date() == datetime.now().date()]),
            "next_task": self.pending_tasks[0].scheduled_time.isoformat() if self.pending_tasks else None,
            "stats": self.automation_stats
        }


# Factory function for easy setup
def create_jorge_automation(ghl_client: Optional[GHLClient] = None) -> JorgeAutomationSystem:
    """Create and configure Jorge's automation system"""
    return JorgeAutomationSystem(ghl_client=ghl_client)


if __name__ == "__main__":
    # Example usage
    automation = create_jorge_automation()
    
    # Start automation system
    automation.start_automation()
    
    # Schedule a follow-up
    task_id = automation.schedule_follow_up(
        contact_id="test_contact_123",
        location_id="test_location_456",
        followup_type=FollowUpType.QUALIFICATION_FOLLOWUP,
        delay_minutes=5
    )
    
    print(f"Scheduled follow-up: {task_id}")
    print(f"Status: {automation.get_automation_status()}")
    
    # Keep running for demo
    try:
        while True:
            time.sleep(60)
            print(f"Status: {automation.get_automation_status()}")
    except KeyboardInterrupt:
        automation.stop_automation()
        print("Automation stopped")