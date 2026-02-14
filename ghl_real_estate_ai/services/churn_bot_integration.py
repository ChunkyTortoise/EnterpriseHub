"""
Churn Detection Bot Integration

This module provides integration utilities for adding churn detection
to the Lead, Buyer, and Seller bots without modifying their core code.
"""

from datetime import datetime
from typing import Dict, List, Optional

from ghl_real_estate_ai.services.churn_detection_service import (
    ChurnDetectionService,
    RecoveryStrategy,
)
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class ChurnBotIntegrator:
    """
    Integrates churn detection capabilities into bot workflows.
    
    This class provides methods to:
    - Assess churn risk after bot interactions
    - Store churn risk in bot state
    - Trigger recovery actions when needed
    """
    
    def __init__(
        self,
        churn_service: Optional[ChurnDetectionService] = None,
    ):
        """
        Initialize the churn bot integrator.
        
        Args:
            churn_service: Optional churn detection service
        """
        self.churn_service = churn_service or ChurnDetectionService()
        
        logger.info("ChurnBotIntegrator initialized")
    
    async def assess_and_store_churn_risk(
        self,
        contact_id: str,
        conversation_history: List[Dict],
        last_activity: datetime,
        bot_state: Dict,
    ) -> Dict:
        """
        Assess churn risk and store in bot state.
        
        Args:
            contact_id: The contact ID
            conversation_history: List of conversation messages
            last_activity: Timestamp of last activity
            bot_state: The bot state dictionary to update
            
        Returns:
            Updated bot state with churn risk information
        """
        try:
            # Assess churn risk
            assessment = await self.churn_service.assess_churn_risk(
                contact_id=contact_id,
                conversation_history=conversation_history,
                last_activity=last_activity,
                use_cache=True,
            )
            
            # Store churn risk in bot state
            bot_state["churn_risk_assessment"] = {
                "contact_id": assessment.contact_id,
                "risk_score": assessment.risk_score,
                "risk_level": assessment.risk_level.value,
                "signals": assessment.signals,
                "last_activity": assessment.last_activity.isoformat(),
                "days_inactive": assessment.days_inactive,
                "recommended_action": assessment.recommended_action.value,
                "assessed_at": assessment.assessed_at.isoformat(),
            }
            
            # Store individual fields for easy access
            bot_state["churn_risk_score"] = assessment.risk_score
            bot_state["churn_risk_level"] = assessment.risk_level.value
            bot_state["churn_days_inactive"] = assessment.days_inactive
            bot_state["churn_recommended_action"] = assessment.recommended_action.value
            
            logger.info(
                f"Churn risk assessed for {contact_id}: "
                f"score={assessment.risk_score:.2f}, "
                f"level={assessment.risk_level.value}"
            )
            
            return bot_state
            
        except Exception as e:
            logger.error(f"Error assessing churn risk for {contact_id}: {e}")
            # Set default values on error
            bot_state["churn_risk_score"] = 0.0
            bot_state["churn_risk_level"] = "low"
            bot_state["churn_days_inactive"] = 0
            bot_state["churn_recommended_action"] = "value_reminder"
            return bot_state
    
    async def should_trigger_recovery(
        self,
        bot_state: Dict,
    ) -> bool:
        """
        Determine if recovery action should be triggered.
        
        Args:
            bot_state: The bot state dictionary
            
        Returns:
            True if recovery should be triggered, False otherwise
        """
        risk_level = bot_state.get("churn_risk_level", "low")
        
        # Trigger recovery for high or critical risk
        return risk_level in ["high", "critical"]
    
    async def get_recovery_action(
        self,
        bot_state: Dict,
        contact_data: Dict,
    ) -> Optional[Dict]:
        """
        Get recovery action for at-risk contact.
        
        Args:
            bot_state: The bot state dictionary
            contact_data: Contact data for personalization
            
        Returns:
            Recovery action dictionary or None
        """
        try:
            if not await self.should_trigger_recovery(bot_state):
                return None
            
            contact_id = bot_state.get("lead_id") or bot_state.get("buyer_id") or bot_state.get("seller_id")
            if not contact_id:
                logger.warning("No contact ID found in bot state for recovery action")
                return None
            
            # Get recommended strategy
            strategy_name = bot_state.get("churn_recommended_action", "value_reminder")
            strategy = RecoveryStrategy(strategy_name)
            
            # Schedule recovery action
            action = await self.churn_service.schedule_recovery_action(
                contact_id=contact_id,
                strategy=strategy,
                contact_data=contact_data,
            )
            
            logger.info(
                f"Recovery action scheduled for {contact_id}: "
                f"strategy={strategy.value}"
            )
            
            return {
                "contact_id": action.contact_id,
                "strategy": action.strategy.value,
                "message_template": action.message_template,
                "channel": action.channel,
                "scheduled_at": action.scheduled_at.isoformat(),
                "status": action.status,
            }
            
        except Exception as e:
            logger.error(f"Error getting recovery action: {e}")
            return None
    
    async def get_churn_risk_summary(
        self,
        bot_state: Dict,
    ) -> Dict:
        """
        Get a summary of churn risk for display.
        
        Args:
            bot_state: The bot state dictionary
            
        Returns:
            Churn risk summary dictionary
        """
        risk_score = bot_state.get("churn_risk_score", 0.0)
        risk_level = bot_state.get("churn_risk_level", "low")
        days_inactive = bot_state.get("churn_days_inactive", 0)
        recommended_action = bot_state.get("churn_recommended_action", "value_reminder")
        
        # Determine risk category
        if risk_score >= 80:
            risk_category = "Critical"
            risk_color = "red"
        elif risk_score >= 60:
            risk_category = "High"
            risk_color = "orange"
        elif risk_score >= 30:
            risk_category = "Medium"
            risk_color = "yellow"
        else:
            risk_category = "Low"
            risk_color = "green"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_category": risk_category,
            "risk_color": risk_color,
            "days_inactive": days_inactive,
            "recommended_action": recommended_action,
            "needs_recovery": risk_level in ["high", "critical"],
        }


# Lead Bot Integration
async def integrate_churn_detection_to_lead_bot(
    lead_bot,
    contact_id: str,
    conversation_history: List[Dict],
    last_activity: datetime,
    bot_state: Dict,
) -> Dict:
    """
    Integrate churn detection into Lead Bot workflow.
    
    Args:
        lead_bot: The Lead Bot instance
        contact_id: The contact ID
        conversation_history: List of conversation messages
        last_activity: Timestamp of last activity
        bot_state: The bot state dictionary
        
    Returns:
        Updated bot state with churn risk information
    """
    integrator = ChurnBotIntegrator()
    
    # Assess and store churn risk
    bot_state = await integrator.assess_and_store_churn_risk(
        contact_id=contact_id,
        conversation_history=conversation_history,
        last_activity=last_activity,
        bot_state=bot_state,
    )
    
    # Check if recovery should be triggered
    if await integrator.should_trigger_recovery(bot_state):
        logger.info(f"Lead {contact_id} is at risk of churn, recovery action recommended")
    
    return bot_state


# Buyer Bot Integration
async def integrate_churn_detection_to_buyer_bot(
    buyer_bot,
    contact_id: str,
    conversation_history: List[Dict],
    last_activity: datetime,
    bot_state: Dict,
) -> Dict:
    """
    Integrate churn detection into Buyer Bot workflow.
    
    Args:
        buyer_bot: The Buyer Bot instance
        contact_id: The contact ID
        conversation_history: List of conversation messages
        last_activity: Timestamp of last activity
        bot_state: The bot state dictionary
        
    Returns:
        Updated bot state with churn risk information
    """
    integrator = ChurnBotIntegrator()
    
    # Assess and store churn risk
    bot_state = await integrator.assess_and_store_churn_risk(
        contact_id=contact_id,
        conversation_history=conversation_history,
        last_activity=last_activity,
        bot_state=bot_state,
    )
    
    # Check if recovery should be triggered
    if await integrator.should_trigger_recovery(bot_state):
        logger.info(f"Buyer {contact_id} is at risk of churn, recovery action recommended")
    
    return bot_state


# Seller Bot Integration
async def integrate_churn_detection_to_seller_bot(
    seller_bot,
    contact_id: str,
    conversation_history: List[Dict],
    last_activity: datetime,
    bot_state: Dict,
) -> Dict:
    """
    Integrate churn detection into Seller Bot workflow.
    
    Args:
        seller_bot: The Seller Bot instance
        contact_id: The contact ID
        conversation_history: List of conversation messages
        last_activity: Timestamp of last activity
        bot_state: The bot state dictionary
        
    Returns:
        Updated bot state with churn risk information
    """
    integrator = ChurnBotIntegrator()
    
    # Assess and store churn risk
    bot_state = await integrator.assess_and_store_churn_risk(
        contact_id=contact_id,
        conversation_history=conversation_history,
        last_activity=last_activity,
        bot_state=bot_state,
    )
    
    # Check if recovery should be triggered
    if await integrator.should_trigger_recovery(bot_state):
        logger.info(f"Seller {contact_id} is at risk of churn, recovery action recommended")
    
    return bot_state
