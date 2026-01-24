#!/usr/bin/env python3
"""
Jorge's Seller Bot - Streamlined for Immediate GHL Integration

This is a simplified wrapper around Jorge's comprehensive seller engine,
designed for immediate deployment and easy GHL integration.

Author: Claude Code Assistant  
Created: 2026-01-22
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

# Import standalone modules (OPTIMIZED)
from jorge_engines_optimized import JorgeSellerEngineOptimized, JorgeLeadEngineOptimized
from jorge_engines import JorgeFollowUpEngine  # Keep original for follow-up
from ghl_client import GHLClient
from conversation_manager import ConversationManager
from config_settings import settings

logger = logging.getLogger(__name__)


class SellerStatus(Enum):
    """Seller lead status levels"""
    HOT = "hot"      # Ready for immediate handoff
    WARM = "warm"    # Qualified but needs nurturing  
    COLD = "cold"    # Needs more qualification


@dataclass
class SellerResult:
    """Result from seller bot processing"""
    response_message: str
    seller_temperature: str
    questions_answered: int
    qualification_complete: bool
    actions_taken: List[Dict]
    next_steps: str
    analytics: Dict[str, Any]


class JorgeSellerBot:
    """
    Simplified wrapper for Jorge's seller bot system.
    
    This provides a clean interface for GHL integration while leveraging
    the full power of Jorge's sophisticated seller qualification engine.
    
    Features:
    - 4-question qualification sequence
    - Jorge's confrontational tone
    - Automated temperature scoring (Hot/Warm/Cold)
    - Follow-up automation
    - GHL integration
    """

    def __init__(self, ghl_client: Optional[GHLClient] = None):
        """Initialize seller bot with GHL integration"""
        
        # Initialize core components
        self.ghl_client = ghl_client or GHLClient()
        self.conversation_manager = ConversationManager()
        
        # Initialize Jorge's seller engine (OPTIMIZED)
        self.seller_engine = JorgeSellerEngineOptimized(
            conversation_manager=self.conversation_manager,
            ghl_client=self.ghl_client
        )
        
        # Initialize follow-up engine
        self.followup_engine = JorgeFollowUpEngine(
            conversation_manager=self.conversation_manager,
            ghl_client=self.ghl_client
        )
        
        self.logger = logging.getLogger(__name__)

    async def process_seller_message(
        self,
        contact_id: str,
        location_id: str,
        message: str,
        contact_info: Optional[Dict] = None
    ) -> SellerResult:
        """
        Main entry point for processing seller messages.
        
        Args:
            contact_id: GHL contact ID
            location_id: GHL location ID  
            message: Seller's message text
            contact_info: Optional contact information from GHL
            
        Returns:
            SellerResult with response and actions
        """
        try:
            self.logger.info(f"Processing seller message for contact {contact_id}")
            
            # Use Jorge's seller engine to process the message
            result = await self.seller_engine.process_seller_response(
                contact_id=contact_id,
                user_message=message,
                location_id=location_id,
                tenant_config={}  # Use default config
            )
            
            # Transform result into simplified format
            seller_result = SellerResult(
                response_message=result.get("message", ""),
                seller_temperature=result.get("temperature", "cold"),
                questions_answered=result.get("questions_answered", 0),
                qualification_complete=(result.get("questions_answered", 0) >= 4),
                actions_taken=result.get("actions", []),
                next_steps=self._determine_next_steps(result),
                analytics=result.get("analytics", {})
            )
            
            # Apply actions to GHL
            if seller_result.actions_taken:
                await self._apply_ghl_actions(
                    contact_id, location_id, seller_result.actions_taken
                )
            
            return seller_result
            
        except Exception as e:
            self.logger.error(f"Error processing seller message: {e}")
            # Return safe fallback response
            return SellerResult(
                response_message="Thanks for your interest in selling. Our team will get back to you shortly.",
                seller_temperature="cold",
                questions_answered=0,
                qualification_complete=False,
                actions_taken=[],
                next_steps="Manual follow-up required",
                analytics={"error": str(e)}
            )

    async def schedule_seller_followup(
        self,
        contact_id: str,
        location_id: str,
        seller_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Schedule automated follow-up for seller lead.
        
        Args:
            contact_id: GHL contact ID
            location_id: GHL location ID
            seller_data: Current seller profile data
            
        Returns:
            Follow-up scheduling result
        """
        try:
            # Get seller data if not provided
            if not seller_data:
                context = await self.conversation_manager.get_context(contact_id, location_id)
                seller_data = context.get("seller_preferences", {})
            
            # Use follow-up engine to schedule
            followup_result = await self.followup_engine.process_follow_up_trigger(
                contact_id=contact_id,
                location_id=location_id,
                trigger_type="time_based",
                seller_data=seller_data
            )
            
            return followup_result
            
        except Exception as e:
            self.logger.error(f"Follow-up scheduling failed: {e}")
            return {"error": str(e)}

    async def get_seller_analytics(
        self,
        contact_id: str,
        location_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a seller lead.
        
        Args:
            contact_id: GHL contact ID
            location_id: GHL location ID
            
        Returns:
            Analytics data including scores, qualification status, and timeline
        """
        try:
            # Get conversation context
            context = await self.conversation_manager.get_context(contact_id, location_id)
            seller_data = context.get("seller_preferences", {})
            
            # Calculate analytics
            analytics = {
                "contact_id": contact_id,
                "seller_temperature": context.get("seller_temperature", "cold"),
                "questions_answered": seller_data.get("questions_answered", 0),
                "qualification_progress": f"{seller_data.get('questions_answered', 0)}/4",
                "qualification_complete": seller_data.get("questions_answered", 0) >= 4,
                "last_interaction": context.get("last_ai_response_time"),
                "response_quality": seller_data.get("response_quality", 0.0),
                "timeline_acceptable": seller_data.get("timeline_acceptable"),
                "property_condition": seller_data.get("property_condition"),
                "price_expectation": seller_data.get("price_expectation"),
                "motivation": seller_data.get("motivation"),
                "next_follow_up": context.get("next_follow_up"),
                "conversation_history_count": len(context.get("conversation_history", [])),
                
                # Jorge's specific metrics
                "jorge_qualification_status": self._get_jorge_qualification_status(seller_data),
                "urgency_score": self._calculate_urgency_score(seller_data),
                "readiness_for_listing": self._assess_listing_readiness(seller_data)
            }
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Analytics retrieval failed: {e}")
            return {"error": str(e)}

    def _determine_next_steps(self, result: Dict[str, Any]) -> str:
        """Determine next steps based on seller processing result"""
        
        temperature = result.get("temperature", "cold")
        questions_answered = result.get("questions_answered", 0)
        
        if temperature == "hot":
            return "Schedule immediate consultation call"
        elif temperature == "warm":
            return "Continue nurturing with follow-up sequence"
        elif questions_answered == 0:
            return "Begin qualification with first question"
        elif questions_answered < 4:
            return f"Continue qualification - {4 - questions_answered} questions remaining"
        else:
            return "Complete qualification review and determine next steps"

    async def _apply_ghl_actions(
        self,
        contact_id: str,
        location_id: str,
        actions: List[Dict[str, Any]]
    ) -> None:
        """Apply actions to GHL contact"""
        
        try:
            for action in actions:
                action_type = action.get("type")
                
                if action_type == "add_tag":
                    await self.ghl_client.add_tag(contact_id, action["tag"])
                    
                elif action_type == "remove_tag":
                    await self.ghl_client.remove_tag(contact_id, action["tag"])
                    
                elif action_type == "update_custom_field":
                    await self.ghl_client.update_custom_field(
                        contact_id, action["field"], action["value"]
                    )
                    
                elif action_type == "trigger_workflow":
                    await self.ghl_client.trigger_workflow(
                        contact_id, action["workflow_id"]
                    )
                    
                # Add more action types as needed
                
        except Exception as e:
            self.logger.error(f"Failed to apply GHL actions: {e}")

    def _get_jorge_qualification_status(self, seller_data: Dict) -> str:
        """Get Jorge's specific qualification status"""
        
        questions_answered = seller_data.get("questions_answered", 0)
        timeline_acceptable = seller_data.get("timeline_acceptable")
        
        if questions_answered == 4 and timeline_acceptable is True:
            return "Ready for Jorge's Team"
        elif questions_answered >= 3:
            return "Nearly Qualified"
        elif questions_answered >= 2:
            return "Partially Qualified"
        elif questions_answered >= 1:
            return "Initial Contact Made"
        else:
            return "Not Qualified"

    def _calculate_urgency_score(self, seller_data: Dict) -> float:
        """Calculate urgency score for seller (0-1.0)"""
        
        score = 0.0
        
        # Timeline urgency
        if seller_data.get("timeline_acceptable") is True:
            score += 0.4  # Accepts 30-45 day timeline
        
        # Response quality
        response_quality = seller_data.get("response_quality", 0.0)
        score += response_quality * 0.3
        
        # Motivation clarity
        if seller_data.get("motivation"):
            score += 0.2
            
        # Price expectation provided
        if seller_data.get("price_expectation"):
            score += 0.1
            
        return min(1.0, score)

    def _assess_listing_readiness(self, seller_data: Dict) -> str:
        """Assess how ready the seller is to list"""
        
        urgency = self._calculate_urgency_score(seller_data)
        questions_answered = seller_data.get("questions_answered", 0)
        
        if urgency >= 0.8 and questions_answered >= 4:
            return "Ready to List"
        elif urgency >= 0.6 and questions_answered >= 3:
            return "Nearly Ready"
        elif urgency >= 0.4 and questions_answered >= 2:
            return "Considering"
        else:
            return "Exploring Options"

    async def bulk_process_sellers(
        self,
        seller_contacts: List[Dict[str, str]],
        location_id: str
    ) -> List[Dict[str, Any]]:
        """
        Process multiple seller contacts for batch operations.
        
        Args:
            seller_contacts: List of contact info dicts with contact_id and message
            location_id: GHL location ID
            
        Returns:
            List of processing results
        """
        results = []
        
        for contact in seller_contacts:
            try:
                result = await self.process_seller_message(
                    contact_id=contact["contact_id"],
                    location_id=location_id,
                    message=contact.get("message", ""),
                    contact_info=contact.get("contact_info")
                )
                results.append({
                    "contact_id": contact["contact_id"],
                    "success": True,
                    "result": result.__dict__
                })
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                results.append({
                    "contact_id": contact["contact_id"],
                    "success": False,
                    "error": str(e)
                })
                
        return results


# Factory function for easy instantiation
def create_jorge_seller_bot(ghl_client: Optional[GHLClient] = None) -> JorgeSellerBot:
    """Create and configure Jorge's seller bot"""
    return JorgeSellerBot(ghl_client=ghl_client)


# Helper functions for quick setup
async def quick_seller_response(
    contact_id: str,
    location_id: str,
    message: str,
    ghl_access_token: Optional[str] = None
) -> str:
    """
    Quick helper function for getting seller response without full setup.
    
    Args:
        contact_id: GHL contact ID
        location_id: GHL location ID
        message: Seller's message
        ghl_access_token: Optional GHL access token
        
    Returns:
        Response message string
    """
    try:
        # Initialize bot with minimal setup
        ghl_client = None
        if ghl_access_token:
            ghl_client = GHLClient(access_token=ghl_access_token)
            
        bot = create_jorge_seller_bot(ghl_client)
        
        # Process message
        result = await bot.process_seller_message(
            contact_id=contact_id,
            location_id=location_id,
            message=message
        )
        
        return result.response_message
        
    except Exception as e:
        logger.error(f"Quick seller response failed: {e}")
        return "Thanks for your message. Our team will get back to you shortly."


if __name__ == "__main__":
    # Example usage for testing
    import asyncio
    
    async def test_seller_bot():
        """Test the seller bot with sample data"""
        
        bot = create_jorge_seller_bot()
        
        # Test seller message
        result = await bot.process_seller_message(
            contact_id="test_contact_123",
            location_id="test_location_456", 
            message="I'm thinking about selling my house. What's it worth?"
        )
        
        print(f"Response: {result.response_message}")
        print(f"Temperature: {result.seller_temperature}")
        print(f"Questions Answered: {result.questions_answered}")
        print(f"Next Steps: {result.next_steps}")
        
    # Run test
    # asyncio.run(test_seller_bot())