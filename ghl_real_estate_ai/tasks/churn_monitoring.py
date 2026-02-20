"""
Churn Monitoring Scheduled Task

This module provides scheduled tasks for monitoring churn risk and
triggering recovery actions for at-risk contacts.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.churn_detection_service import (
    ChurnDetectionService,
    ChurnRiskLevel,
    RecoveryStrategy,
)

logger = get_logger(__name__)


class ChurnMonitorScheduler:
    """
    Scheduled task for monitoring churn risk.
    
    This scheduler:
    - Runs daily churn risk assessment for all active contacts
    - Schedules recovery actions for at-risk contacts
    - Tracks recovery outcomes
    """
    
    def __init__(
        self,
        churn_service: Optional[ChurnDetectionService] = None,
    ):
        """
        Initialize the churn monitoring scheduler.
        
        Args:
            churn_service: Optional churn detection service
        """
        self.scheduler = AsyncIOScheduler()
        self.churn_service = churn_service or ChurnDetectionService()
        
        logger.info("ChurnMonitorScheduler initialized")
    
    async def run_daily_churn_assessment(self):
        """
        Run daily churn risk assessment for all active contacts.
        
        This task:
        1. Gets all contacts with activity in last 60 days
        2. Batch assesses churn risk
        3. Schedules recovery actions for at-risk contacts
        """
        logger.info("Starting daily churn assessment")
        
        try:
            # Get all contacts with activity in last 60 days
            active_contacts = await self._get_active_contacts()
            
            if not active_contacts:
                logger.info("No active contacts found for churn assessment")
                return
            
            logger.info(f"Found {len(active_contacts)} active contacts for assessment")
            
            # Batch assess churn risk
            assessments = await self.churn_service.batch_assess_contacts(
                [c["id"] for c in active_contacts]
            )
            
            logger.info(f"Completed churn risk assessment for {len(assessments)} contacts")
            
            # Schedule recovery actions for at-risk contacts
            high_risk_count = 0
            critical_risk_count = 0
            
            for assessment in assessments:
                if assessment.risk_level in [ChurnRiskLevel.HIGH, ChurnRiskLevel.CRITICAL]:
                    if assessment.risk_level == ChurnRiskLevel.HIGH:
                        high_risk_count += 1
                    else:
                        critical_risk_count += 1
                    
                    # Get contact data
                    contact_data = await self._get_contact_data(assessment.contact_id)
                    
                    # Schedule recovery action
                    strategy = await self.churn_service.get_recovery_strategy(assessment)
                    action = await self.churn_service.schedule_recovery_action(
                        contact_id=assessment.contact_id,
                        strategy=strategy,
                        contact_data=contact_data,
                    )
                    
                    # Store action in database
                    await self._store_recovery_action(action, assessment)
                    
                    logger.info(
                        f"Scheduled recovery action for {assessment.contact_id}: "
                        f"strategy={strategy.value}, risk_level={assessment.risk_level.value}"
                    )
            
            logger.info(
                f"Daily churn assessment completed: "
                f"{high_risk_count} high risk, {critical_risk_count} critical risk"
            )
            
        except Exception as e:
            logger.error(f"Error in daily churn assessment: {e}", exc_info=True)
    
    async def _get_active_contacts(self) -> List[Dict]:
        """
        Get all contacts with activity in last 60 days.
        
        Returns:
            List of contact dictionaries with id and last_activity
        """
        # This would query the database for active contacts
        # For now, return empty list
        logger.info("Fetching active contacts from database")
        return []
    
    async def _get_contact_data(self, contact_id: str) -> Dict:
        """
        Get contact data for personalization.
        
        Args:
            contact_id: The contact ID
            
        Returns:
            Dictionary with contact data
        """
        # This would query the database for contact data
        # For now, return default data
        return {
            "name": "there",
            "topic": "our conversation",
            "market": "the market",
            "incentive": "a special offer",
            "days_inactive": 0,
        }
    
    async def _store_recovery_action(
        self,
        action,
        assessment,
    ):
        """
        Store recovery action in database.
        
        Args:
            action: The recovery action to store
            assessment: The churn risk assessment
        """
        # This would insert the recovery action into the database
        # For now, just log it
        logger.info(
            f"Storing recovery action for {action.contact_id}: "
            f"strategy={action.strategy.value}, scheduled_at={action.scheduled_at.isoformat()}"
        )
    
    async def execute_scheduled_recovery_actions(self):
        """
        Execute scheduled recovery actions that are due.
        
        This task:
        1. Gets all pending recovery actions that are due
        2. Executes each action
        3. Updates status in database
        """
        logger.info("Executing scheduled recovery actions")
        
        try:
            # Get pending recovery actions that are due
            pending_actions = await self._get_pending_recovery_actions()
            
            if not pending_actions:
                logger.info("No pending recovery actions to execute")
                return
            
            logger.info(f"Found {len(pending_actions)} pending recovery actions")
            
            # Execute each action
            success_count = 0
            failure_count = 0
            
            for action in pending_actions:
                try:
                    success = await self.churn_service.execute_recovery_action(action)
                    
                    if success:
                        success_count += 1
                        await self._update_recovery_action_status(action.id, "sent")
                    else:
                        failure_count += 1
                        await self._update_recovery_action_status(action.id, "failed")
                    
                except Exception as e:
                    logger.error(f"Error executing recovery action {action.id}: {e}")
                    failure_count += 1
                    await self._update_recovery_action_status(action.id, "failed")
            
            logger.info(
                f"Recovery actions executed: {success_count} success, {failure_count} failure"
            )
            
        except Exception as e:
            logger.error(f"Error in executing scheduled recovery actions: {e}", exc_info=True)
    
    async def _get_pending_recovery_actions(self) -> List:
        """
        Get pending recovery actions that are due.
        
        Returns:
            List of pending recovery actions
        """
        # This would query the database for pending actions
        # For now, return empty list
        logger.info("Fetching pending recovery actions from database")
        return []
    
    async def _update_recovery_action_status(
        self,
        action_id: str,
        status: str,
    ):
        """
        Update recovery action status in database.
        
        Args:
            action_id: The recovery action ID
            status: The new status
        """
        # This would update the recovery action in the database
        # For now, just log it
        logger.info(f"Updating recovery action {action_id} status to {status}")
    
    def start(self):
        """
        Start the churn monitoring scheduler.
        
        This adds the scheduled jobs and starts the scheduler.
        """
        # Add daily churn assessment job (runs at 2 AM daily)
        self.scheduler.add_job(
            self.run_daily_churn_assessment,
            'cron',
            hour=2,
            minute=0,
            id='daily_churn_assessment',
            replace_existing=True,
        )
        
        # Add recovery action execution job (runs every hour)
        self.scheduler.add_job(
            self.execute_scheduled_recovery_actions,
            'interval',
            hours=1,
            id='execute_recovery_actions',
            replace_existing=True,
        )
        
        # Start the scheduler
        self.scheduler.start()
        
        logger.info("Churn monitoring scheduler started")
    
    def stop(self):
        """
        Stop the churn monitoring scheduler.
        """
        self.scheduler.shutdown()
        logger.info("Churn monitoring scheduler stopped")


async def run_churn_monitoring():
    """
    Run churn monitoring as a standalone task.
    
    This function can be called directly to run churn monitoring
    without starting the scheduler.
    """
    scheduler = ChurnMonitorScheduler()
    
    # Run daily churn assessment
    await scheduler.run_daily_churn_assessment()
    
    # Execute scheduled recovery actions
    await scheduler.execute_scheduled_recovery_actions()


if __name__ == "__main__":
    # Run churn monitoring
    asyncio.run(run_churn_monitoring())
