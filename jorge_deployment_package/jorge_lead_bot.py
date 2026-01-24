#!/usr/bin/env python3
"""
Jorge's Lead Bot - Streamlined for Immediate GHL Integration

This is a simplified, production-ready lead bot specifically designed for Jorge's
immediate deployment needs. It handles buyer leads with qualification, scoring,
and follow-up automation.

Author: Claude Code Assistant
Created: 2026-01-22
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

# Core imports from standalone modules (OPTIMIZED)
from lead_intelligence_optimized import get_enhanced_lead_intelligence, PredictiveLeadScorerV2Optimized
from ghl_client import GHLClient
from config_settings import settings

logger = logging.getLogger(__name__)


class LeadType(Enum):
    """Types of leads Jorge works with"""
    BUYER = "buyer"
    SELLER = "seller"
    INVESTOR = "investor"
    UNKNOWN = "unknown"


@dataclass
class LeadQualification:
    """Lead qualification results"""
    budget_range: Optional[str] = None
    timeline: Optional[str] = None
    location_preference: Optional[str] = None
    property_type: Optional[str] = None
    financing_status: Optional[str] = None
    motivation: Optional[str] = None
    urgency_score: float = 0.0
    qualification_complete: bool = False


class JorgeLeadBot:
    """
    Jorge's streamlined lead bot for immediate GHL integration.
    
    Features:
    - Lead qualification and scoring
    - Conversation intelligence
    - Automated follow-up scheduling
    - KPI tracking and analytics
    - GHL webhook integration
    """

    def __init__(self, ghl_client: Optional[GHLClient] = None):
        """Initialize the lead bot with GHL integration"""
        self.ghl_client = ghl_client or GHLClient()
        self.predictive_scorer = PredictiveLeadScorerV2Optimized()
        self.logger = logging.getLogger(__name__)

    async def process_lead_message(
        self,
        contact_id: str,
        location_id: str,
        message: str,
        contact_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing lead messages.
        
        Args:
            contact_id: GHL contact ID
            location_id: GHL location ID
            message: Lead's message
            contact_data: Optional contact information
            
        Returns:
            Processing result with response, actions, and analytics
        """
        try:
            self.logger.info(f"Processing lead message for contact {contact_id}")

            # 1. Get or create lead profile
            lead_profile = await self._get_lead_profile(contact_id, location_id)
            
            # 2. Extract information from message
            extracted_data = await self._extract_lead_data(
                message, lead_profile, contact_data
            )
            
            # 3. Update qualification status
            qualification = await self._update_qualification(
                lead_profile, extracted_data
            )
            
            # 4. Calculate lead score
            lead_score = await self._calculate_lead_score(
                contact_id, location_id, qualification, extracted_data
            )
            
            # 5. Generate appropriate response
            response = await self._generate_response(
                qualification, lead_score, extracted_data, contact_data
            )
            
            # 6. Create GHL actions
            actions = await self._create_ghl_actions(
                contact_id, location_id, qualification, lead_score
            )
            
            # 7. Schedule follow-up if needed
            follow_up = await self._schedule_follow_up(
                contact_id, qualification, lead_score
            )
            
            # 8. Track analytics
            await self._track_interaction(
                contact_id, location_id, message, response, lead_score
            )

            return {
                "response": response,
                "message": response,  # Webhook server expects "message" field
                "actions": actions,
                "lead_score": lead_score.overall_score,
                "lead_temperature": getattr(lead_score, 'temperature', 'COLD'),
                "budget_max": getattr(lead_score, 'budget_detected', None),
                "timeline": getattr(lead_score, 'timeline_detected', 'unknown'),
                "location_preferences": extracted_data.get("enhanced_analysis", {}).get("location_analysis", []),
                "qualification": qualification.__dict__,
                "follow_up": follow_up,
                "analytics": {
                    "urgency_score": qualification.urgency_score,
                    "qualification_complete": qualification.qualification_complete,
                    "lead_type": extracted_data.get("lead_type", "unknown"),
                    "priority": lead_score.priority_level,
                    "is_pre_approved": getattr(lead_score, 'is_pre_approved', False),
                    "budget_detected": getattr(lead_score, 'budget_detected', None)
                }
            }

        except Exception as e:
            self.logger.error(f"Error processing lead message: {e}")
            return {
                "response": "Thanks for your message. Our team will get back to you shortly.",
                "actions": [],
                "error": str(e)
            }

    async def _get_lead_profile(
        self, contact_id: str, location_id: str
    ) -> Dict[str, Any]:
        """Get existing lead profile or create new one"""
        try:
            # Try to get existing profile from GHL custom fields
            contact = await self.ghl_client.get_contact(contact_id)
            
            profile = {
                "contact_id": contact_id,
                "location_id": location_id,
                "name": contact.get("firstName", "") + " " + contact.get("lastName", ""),
                "email": contact.get("email", ""),
                "phone": contact.get("phone", ""),
                "tags": contact.get("tags", []),
                "custom_fields": contact.get("customFields", {}),
                "last_updated": datetime.now().isoformat()
            }
            
            return profile
            
        except Exception as e:
            self.logger.warning(f"Could not fetch contact profile: {e}")
            return {
                "contact_id": contact_id,
                "location_id": location_id,
                "last_updated": datetime.now().isoformat()
            }

    async def _extract_lead_data(
        self,
        message: str,
        lead_profile: Dict,
        contact_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Extract relevant information from lead message"""
        try:
            # Use the enhanced lead intelligence service
            from lead_intelligence_optimized import get_enhanced_lead_intelligence
            analysis = get_enhanced_lead_intelligence(message, context=lead_profile)
            
            # Extract key information from enhanced analysis
            extracted = {
                "message_intent": "buying" if self._detect_lead_type(message) == "buyer" else "unknown",
                "lead_type": self._detect_lead_type(message),
                "urgency_indicators": [],
                "budget_mentions": f"${analysis.get('budget_max', 0):,}" if analysis.get('budget_max') else None,
                "timeline_mentions": analysis.get('timeline_analysis', 'unknown'),
                "location_mentions": ", ".join(analysis.get('location_analysis', [])),
                "property_type_mentions": self._extract_property_type(message),
                "financing_mentions": analysis.get('financing_analysis', 'unknown'),
                "motivation": "purchasing" if analysis.get('has_specific_budget') else "exploring",
                "sentiment": "positive" if analysis.get('lead_score', 0) > 70 else "neutral",
                "enhanced_analysis": analysis  # Keep full analysis for later use
            }
            
            return extracted
            
        except Exception as e:
            self.logger.warning(f"Lead data extraction failed: {e}")
            # Fallback to basic extraction
            return {
                "lead_type": self._detect_lead_type(message),
                "urgency_indicators": [],
                "sentiment": "neutral"
            }

    def _detect_lead_type(self, message: str) -> str:
        """Detect if lead is buyer, seller, or investor"""
        message_lower = message.lower()
        
        # Seller indicators
        seller_indicators = ["sell", "selling", "list", "listing", "agent", "market value"]
        if any(indicator in message_lower for indicator in seller_indicators):
            return LeadType.SELLER.value
            
        # Investor indicators  
        investor_indicators = ["invest", "rental", "flip", "portfolio", "cash flow", "roi"]
        if any(indicator in message_lower for indicator in investor_indicators):
            return LeadType.INVESTOR.value
            
        # Buyer indicators (default)
        buyer_indicators = ["buy", "buying", "looking for", "house hunt", "home search"]
        if any(indicator in message_lower for indicator in buyer_indicators):
            return LeadType.BUYER.value
            
        return LeadType.UNKNOWN.value

    def _extract_budget(self, message: str) -> Optional[str]:
        """Extract budget information from message"""
        import re
        
        # Look for dollar amounts
        dollar_pattern = r'\$[\d,]+(?:k|K)?'
        dollar_match = re.search(dollar_pattern, message)
        if dollar_match:
            return dollar_match.group()
            
        # Look for budget ranges
        budget_keywords = ["budget", "afford", "looking to spend", "price range"]
        for keyword in budget_keywords:
            if keyword in message.lower():
                # Extract numbers near budget keyword
                words = message.split()
                for i, word in enumerate(words):
                    if keyword.replace(" ", "") in word.lower():
                        # Look for numbers in next few words
                        for j in range(i+1, min(i+5, len(words))):
                            if re.search(r'\d+', words[j]):
                                return words[j]
        
        return None

    def _extract_timeline(self, message: str) -> Optional[str]:
        """Extract timeline information from message"""
        timeline_indicators = {
            "asap": "immediate",
            "immediately": "immediate", 
            "urgent": "immediate",
            "this week": "1 week",
            "this month": "1 month",
            "next month": "2 months",
            "6 months": "6 months",
            "year": "12 months",
            "no rush": "flexible"
        }
        
        message_lower = message.lower()
        for indicator, timeline in timeline_indicators.items():
            if indicator in message_lower:
                return timeline
                
        return None

    def _extract_location(self, message: str) -> Optional[str]:
        """Extract location preferences from message"""
        # Look for city names, zip codes, or neighborhoods
        import re
        
        # ZIP codes
        zip_match = re.search(r'\b\d{5}\b', message)
        if zip_match:
            return zip_match.group()
            
        # Common location keywords
        location_keywords = ["in ", "near ", "around ", "area", "neighborhood"]
        for keyword in location_keywords:
            if keyword in message.lower():
                words = message.split()
                for i, word in enumerate(words):
                    if keyword.strip() in word.lower():
                        # Get next word(s) as location
                        if i + 1 < len(words):
                            return words[i + 1]
        
        return None

    def _extract_property_type(self, message: str) -> Optional[str]:
        """Extract property type preferences"""
        property_types = {
            "house": "Single Family",
            "condo": "Condo", 
            "townhouse": "Townhouse",
            "apartment": "Apartment",
            "multi": "Multi-Family",
            "commercial": "Commercial"
        }
        
        message_lower = message.lower()
        for prop_type, formal_name in property_types.items():
            if prop_type in message_lower:
                return formal_name
                
        return None

    def _extract_financing(self, message: str) -> Optional[str]:
        """Extract financing status information"""
        financing_indicators = {
            "cash": "Cash",
            "pre-approved": "Pre-Approved",
            "pre-qualified": "Pre-Qualified", 
            "mortgage": "Financing Needed",
            "loan": "Financing Needed",
            "first time": "First Time Buyer"
        }
        
        message_lower = message.lower()
        for indicator, status in financing_indicators.items():
            if indicator in message_lower:
                return status
                
        return None

    async def _update_qualification(
        self, lead_profile: Dict, extracted_data: Dict
    ) -> LeadQualification:
        """Update lead qualification based on extracted data"""
        
        # Get existing qualification or create new
        qualification = LeadQualification()
        
        # Update fields based on extracted data
        if extracted_data.get("budget_mentions"):
            qualification.budget_range = extracted_data["budget_mentions"]
            
        if extracted_data.get("timeline_mentions"):
            qualification.timeline = extracted_data["timeline_mentions"]
            
        if extracted_data.get("location_mentions"):
            qualification.location_preference = extracted_data["location_mentions"]
            
        if extracted_data.get("property_type_mentions"):
            qualification.property_type = extracted_data["property_type_mentions"]
            
        if extracted_data.get("financing_mentions"):
            qualification.financing_status = extracted_data["financing_mentions"]
            
        if extracted_data.get("motivation"):
            qualification.motivation = extracted_data["motivation"]
        
        # Calculate urgency score
        urgency_factors = [
            ("immediate" in (qualification.timeline or ""), 0.4),
            (len(extracted_data.get("urgency_indicators", [])) > 0, 0.3),
            (extracted_data.get("sentiment") == "positive", 0.2),
            (qualification.budget_range is not None, 0.1)
        ]
        
        qualification.urgency_score = sum(score for condition, score in urgency_factors if condition)
        
        # Check if qualification is complete
        required_fields = [
            qualification.budget_range,
            qualification.timeline, 
            qualification.location_preference
        ]
        qualification.qualification_complete = all(field is not None for field in required_fields)
        
        return qualification

    async def _calculate_lead_score(
        self,
        contact_id: str,
        location_id: str,
        qualification: LeadQualification,
        extracted_data: Dict
    ) -> Any:
        """Calculate predictive lead score"""
        try:
            # Use the enhanced analysis data directly
            enhanced_analysis = extracted_data.get("enhanced_analysis", {})
            lead_score = enhanced_analysis.get("lead_score", 50.0)
            urgency_score = enhanced_analysis.get("urgency", 0.0)

            # Determine priority and temperature
            if lead_score >= 85:
                priority_level = "high"
                temperature = "HOT"
            elif lead_score >= 70:
                priority_level = "medium"
                temperature = "WARM"
            else:
                priority_level = "low"
                temperature = "COLD"

            return type('LeadScore', (), {
                'overall_score': lead_score,
                'priority_level': priority_level,
                'temperature': temperature,
                'urgency_score': urgency_score,
                'qualification_score': enhanced_analysis.get("qualification", 0.0),
                'budget_detected': enhanced_analysis.get("budget_max"),
                'timeline_detected': enhanced_analysis.get("timeline_analysis"),
                'is_pre_approved': enhanced_analysis.get("is_pre_approved", False)
            })()

        except Exception as e:
            self.logger.warning(f"Lead scoring failed: {e}")
            # Fallback scoring
            base_score = 50.0

            # Adjust based on qualification
            if qualification.qualification_complete:
                base_score += 20
            if qualification.urgency_score > 0.5:
                base_score += 15
            if qualification.budget_range:
                base_score += 10

            return type('LeadScore', (), {
                'overall_score': base_score,
                'priority_level': 'high' if base_score > 75 else 'medium' if base_score > 50 else 'low',
                'temperature': 'WARM' if base_score > 75 else 'COLD'
            })()

    async def _generate_response(
        self,
        qualification: LeadQualification,
        lead_score: Any,
        extracted_data: Dict,
        contact_data: Optional[Dict] = None
    ) -> str:
        """Generate appropriate response based on lead qualification"""
        
        lead_type = extracted_data.get("lead_type", "unknown")
        contact_name = ""
        
        if contact_data:
            first_name = contact_data.get("firstName", "")
            if first_name:
                contact_name = f"{first_name}, "
        
        # High priority/qualified leads - Jorge's authentic style
        if qualification.qualification_complete and lead_score.overall_score > 75:
            if lead_type == LeadType.BUYER.value:
                # Get specific details for personalized response
                budget_info = extracted_data.get("budget_mentions", "")
                location_info = extracted_data.get("location_mentions", "")
                timeline_info = extracted_data.get("timeline_mentions", "")

                # Check if pre-approved for VIP treatment
                is_preapproved = getattr(lead_score, 'is_pre_approved', False)

                if budget_info and location_info and is_preapproved:
                    return f"{contact_name}Perfect timing! Pre-approved with a {budget_info} budget in {location_info}? I've got 3 prime properties that just came on the market. Two are pre-market exclusives my competitors don't even know about yet. When can we set up a private showing? I can do this afternoon or tomorrow morning."
                elif budget_info and location_info:
                    return f"{contact_name}I like what I'm seeing - {budget_info} budget, {location_info}, {timeline_info} timeline. You're serious. I've got inventory that matches exactly. Let's talk today before these properties hit the MLS. What's your schedule like this afternoon?"
                else:
                    return f"{contact_name}I can tell you're serious about buying - and I respect that. Let me cut through the noise and show you exactly what's available in your price range. When's the best time for a 15-minute call today?"
            elif lead_type == LeadType.SELLER.value:
                # Redirect to seller bot
                return f"{contact_name}I'll connect you with our seller specialist who can give you an accurate market analysis. Expect a call within the hour."
            else:
                return f"{contact_name}Great! Let me connect you with our team to discuss your investment goals. When works best for a quick call?"
        
        # Medium priority - needs more qualification
        elif not qualification.qualification_complete:
            missing_info = []
            if not qualification.budget_range:
                missing_info.append("budget")
            if not qualification.timeline:
                missing_info.append("timeline") 
            if not qualification.location_preference:
                missing_info.append("preferred area")
                
            if len(missing_info) == 1:
                if "budget" in missing_info:
                    return f"{contact_name}What's your budget range? This helps me find the right options for you."
                elif "timeline" in missing_info:
                    return f"{contact_name}When are you looking to move? Timing affects our search strategy."
                else:  # location
                    return f"{contact_name}Which area are you focused on? I know the market well and can guide you to the best neighborhoods."
            else:
                return f"{contact_name}I need a few quick details to help you effectively. What's your budget, timeline, and preferred area?"
        
        # Lower priority - nurture response
        else:
            return f"{contact_name}Thanks for reaching out! I'll keep you updated on properties that match your criteria. The market is moving fast right now."

    async def _create_ghl_actions(
        self,
        contact_id: str,
        location_id: str,
        qualification: LeadQualification,
        lead_score: Any
    ) -> List[Dict[str, Any]]:
        """Create GHL actions based on lead qualification and score"""
        
        actions = []
        
        # Add lead score tag
        priority = getattr(lead_score, 'priority_level', 'low')
        actions.append({
            "type": "add_tag",
            "tag": f"Priority-{priority.capitalize()}"
        })
        
        # Add qualification status tag
        if qualification.qualification_complete:
            actions.append({
                "type": "add_tag",
                "tag": "Fully-Qualified"
            })
            actions.append({
                "type": "remove_tag",
                "tag": "Needs-Qualifying"
            })
        else:
            actions.append({
                "type": "add_tag",
                "tag": "Needs-Qualifying"
            })
        
        # Update custom fields with qualification data
        if qualification.budget_range:
            actions.append({
                "type": "update_custom_field",
                "field": "budget_range",
                "value": qualification.budget_range
            })
            
        if qualification.timeline:
            actions.append({
                "type": "update_custom_field", 
                "field": "timeline",
                "value": qualification.timeline
            })
            
        if qualification.location_preference:
            actions.append({
                "type": "update_custom_field",
                "field": "location_preference", 
                "value": qualification.location_preference
            })
        
        # Update lead score
        actions.append({
            "type": "update_custom_field",
            "field": "lead_score",
            "value": str(getattr(lead_score, 'overall_score', 0))
        })
        
        # High priority actions
        if priority == 'high':
            actions.append({
                "type": "trigger_workflow",
                "workflow_id": "high_priority_lead_workflow"
            })
            
        return actions

    async def _schedule_follow_up(
        self,
        contact_id: str,
        qualification: LeadQualification,
        lead_score: Any
    ) -> Optional[Dict[str, Any]]:
        """Schedule appropriate follow-up based on lead status"""
        
        priority = getattr(lead_score, 'priority_level', 'low')
        
        # High priority - immediate follow-up
        if priority == 'high':
            return {
                "type": "immediate_call",
                "scheduled_for": "within_1_hour",
                "reason": "High priority qualified lead"
            }
        
        # Medium priority - same day follow-up
        elif priority == 'medium':
            return {
                "type": "same_day_follow_up",
                "scheduled_for": "within_4_hours", 
                "reason": "Medium priority lead needs nurturing"
            }
        
        # Low priority - standard follow-up sequence
        else:
            return {
                "type": "nurture_sequence",
                "scheduled_for": "next_day",
                "sequence": "standard_lead_nurture"
            }

    async def _track_interaction(
        self,
        contact_id: str,
        location_id: str,
        message: str,
        response: str,
        lead_score: Any
    ) -> None:
        """Track interaction for analytics and reporting"""
        
        try:
            analytics_data = {
                "timestamp": datetime.now().isoformat(),
                "contact_id": contact_id,
                "location_id": location_id,
                "message_length": len(message),
                "response_length": len(response),
                "lead_score": getattr(lead_score, 'overall_score', 0),
                "priority": getattr(lead_score, 'priority_level', 'low'),
                "interaction_type": "lead_qualification"
            }
            
            # Log for analytics system
            self.logger.info(
                f"Lead interaction tracked",
                extra=analytics_data
            )
            
        except Exception as e:
            self.logger.error(f"Analytics tracking failed: {e}")

    async def get_lead_analytics(
        self, contact_id: str, location_id: str
    ) -> Dict[str, Any]:
        """Get analytics for a specific lead"""
        
        try:
            # Get lead profile and current status
            profile = await self._get_lead_profile(contact_id, location_id)
            
            # Calculate analytics
            analytics = {
                "contact_id": contact_id,
                "current_score": profile.get("custom_fields", {}).get("lead_score", 0),
                "qualification_status": "Qualified" if "Fully-Qualified" in profile.get("tags", []) else "Needs Qualification",
                "priority": "High" if "Priority-High" in profile.get("tags", []) else "Medium" if "Priority-Medium" in profile.get("tags", []) else "Low",
                "last_interaction": profile.get("last_updated"),
                "next_follow_up": profile.get("custom_fields", {}).get("next_follow_up"),
                "tags": profile.get("tags", [])
            }
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"Analytics retrieval failed: {e}")
            return {"error": str(e)}


# Factory function for easy instantiation
def create_jorge_lead_bot(ghl_client: Optional[GHLClient] = None) -> JorgeLeadBot:
    """Create and configure Jorge's lead bot"""
    return JorgeLeadBot(ghl_client=ghl_client)