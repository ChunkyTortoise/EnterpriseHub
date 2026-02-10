#!/usr/bin/env python3
"""
Jorge's Optimized AI Engines - Enhanced for Production Performance

Optimized versions of Jorge's engines with improved prompting,
better error handling, and enhanced tone calibration.

Author: Claude Code Assistant
Created: 2026-01-22
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class OptimizedResponse:
    """Enhanced response structure with quality metrics"""
    message: str
    confidence_score: float
    tone_quality: str
    business_context: Dict[str, Any]
    fallback_used: bool = False


class JorgeSellerEngineOptimized:
    """
    Optimized seller engine with enhanced confrontational tone
    and improved qualification logic.
    """

    def __init__(self, conversation_manager, ghl_client):
        self.conversation_manager = conversation_manager
        self.ghl_client = ghl_client
        self.logger = logging.getLogger(__name__)

        # Jorge's authentic phrases and patterns
        self.jorge_confrontational_phrases = [
            "Look, I'm not here to waste time",
            "Let me be straight with you",
            "I buy houses fast, but only if you're serious",
            "Don't give me the runaround",
            "Are you actually ready to sell, or just shopping around?",
            "I need the truth, not some sugar-coated BS",
            "If you're not serious, don't waste my time",
            "Here's the deal - no games, no nonsense"
        ]

        self.jorge_qualification_questions = {
            1: "What condition is the house in? Be honest - does it need major repairs, minor fixes, or is it move-in ready? I need the truth, not what you think I want to hear.",
            2: "What do you REALISTICALLY think it's worth as-is? Don't tell me what Zillow says - what would you actually pay for it if you were buying it yourself?",
            3: "What's your real motivation here? Job transfer, financial problems, inherited property, divorce - what's the actual situation? I need to know you're serious.",
            4: "If I can offer you [CALCULATED_OFFER] cash and close in 2-3 weeks with no repairs needed on your end - would you take that deal today, or are you going to shop it around?"
        }

    async def process_seller_response(
        self,
        contact_id: str,
        user_message: str,
        location_id: str,
        tenant_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Enhanced seller response processing with optimized prompting
        """

        try:
            # Get conversation context with error handling
            context = await self._safe_get_context(contact_id, location_id)

            # Analyze seller motivation and urgency
            seller_analysis = self._analyze_seller_intent(user_message)

            # Determine which question to ask next
            questions_answered = context.get("seller_questions_answered", 0)

            # Generate Jorge's authentic response
            response = await self._generate_jorge_response(
                user_message,
                seller_analysis,
                questions_answered,
                context
            )

            # Update conversation state
            await self._update_seller_context(
                contact_id,
                location_id,
                user_message,
                response,
                seller_analysis,
                questions_answered
            )

            # Calculate seller temperature
            temperature = self._calculate_seller_temperature(
                seller_analysis,
                questions_answered,
                context
            )

            # Generate actions for GHL
            actions = self._generate_seller_actions(temperature, seller_analysis)

            return {
                "message": response.message,
                "temperature": temperature,
                "questions_answered": questions_answered + 1,
                "actions": actions,
                "seller_motivation": seller_analysis.get("motivation_score", 0.5),
                "urgency_level": seller_analysis.get("urgency_score", 0.5),
                "confidence": response.confidence_score,
                "tone_quality": response.tone_quality
            }

        except Exception as e:
            self.logger.error(f"Seller processing error: {e}")
            return await self._fallback_seller_response(user_message)

    def _analyze_seller_intent(self, message: str) -> Dict[str, Any]:
        """Enhanced seller intent analysis with better keyword detection"""

        message_lower = message.lower()

        # High urgency indicators - ENHANCED FOR JORGE'S BUSINESS
        urgency_keywords = [
            "asap", "quickly", "fast", "urgent", "need to sell",
            "divorce", "job transfer", "relocating", "moving",
            "inherited", "foreclosure", "behind on payments",
            "financial problems", "emergency", "immediately",
            "don't want to deal", "just want it gone", "tired of"
        ]

        # Motivation indicators
        motivation_keywords = {
            "financial": ["foreclosure", "behind payments", "debt", "financial", "money problems"],
            "relocation": ["job transfer", "relocating", "moving", "new job", "transferred"],
            "divorce": ["divorce", "separation", "ex-husband", "ex-wife", "split"],
            "inheritance": ["inherited", "dad's house", "mom's house", "estate", "passed away"],
            "investment": ["rental", "investment property", "cash flow", "tired of landlord"]
        }

        # Calculate scores
        urgency_score = sum(1 for keyword in urgency_keywords if keyword in message_lower) / len(urgency_keywords)
        urgency_score = min(1.0, urgency_score * 3)  # Boost score

        # Detect motivation type
        motivation_type = "unknown"
        motivation_score = 0.3  # Default

        for mot_type, keywords in motivation_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                motivation_type = mot_type
                # Higher score for urgent situations Jorge targets
                if mot_type in ["divorce", "financial", "relocation"]:
                    motivation_score = 0.9
                else:
                    motivation_score = 0.8
                break

        # Detect time sensitivity
        timeline_keywords = ["30 days", "60 days", "month", "weeks", "soon", "quick"]
        has_timeline = any(keyword in message_lower for keyword in timeline_keywords)

        # Property condition hints
        condition_keywords = ["needs work", "repairs", "updated", "renovated", "as-is"]
        mentions_condition = any(keyword in message_lower for keyword in condition_keywords)

        return {
            "urgency_score": urgency_score,
            "motivation_score": motivation_score,
            "motivation_type": motivation_type,
            "has_timeline": has_timeline,
            "mentions_condition": mentions_condition,
            "message_length": len(message),
            "question_count": message.count("?"),
            "sounds_serious": urgency_score > 0.3 or motivation_score > 0.6
        }

    async def _generate_jorge_response(
        self,
        user_message: str,
        analysis: Dict,
        questions_answered: int,
        context: Dict
    ) -> OptimizedResponse:
        """Generate Jorge's authentic confrontational response"""

        try:
            # Select appropriate Jorge opening
            if questions_answered == 0:
                # Initial response - establish Jorge's tone
                opener = random.choice([
                    "Look, I'm not here to give free appraisals.",
                    "Let me be straight with you -",
                    "I buy houses fast for cash, but only if you're serious."
                ])

                if analysis["sounds_serious"]:
                    middle = "I can tell you might actually be ready to sell. Here's what I need to know:"
                else:
                    middle = "Are you actually ready to sell in the next 30-45 days, or are you just shopping around? Because if you're not serious, don't waste my time."

                question = self.jorge_qualification_questions[1]
                response_text = f"{opener} {middle} {question}"

            elif questions_answered < 4:
                # Continue with qualification questions
                question_num = questions_answered + 1

                # Acknowledge their answer first
                if analysis["motivation_score"] > 0.6:
                    ack = random.choice([
                        "Alright, that makes sense.",
                        "Fair enough.",
                        "I appreciate the honesty."
                    ])
                else:
                    ack = random.choice([
                        "Okay...",
                        "I see.",
                        "Uh-huh."
                    ])

                question = self.jorge_qualification_questions[question_num]
                response_text = f"{ack} {question}"

            else:
                # All questions answered - make decision
                if analysis["motivation_score"] > 0.7 and analysis["urgency_score"] > 0.5:
                    response_text = "Perfect! That's exactly what I needed to hear. You sound like someone I can work with. Let me get some basic property details and we'll set up a quick walkthrough. You just found your cash buyer."
                elif analysis["motivation_score"] > 0.4:
                    response_text = "Alright, I think we can work together. It's not my ideal scenario, but I can probably make you an offer. Let's talk details."
                else:
                    response_text = "Look, I'm going to be honest with you - this doesn't sound like a good fit for what I do. I buy from people who need to sell fast, not people who are just curious about the market. Good luck with your search."

            confidence = 0.9 if analysis["sounds_serious"] else 0.6
            tone_quality = "authentic_jorge" if len(response_text) > 50 else "needs_improvement"

            return OptimizedResponse(
                message=response_text,
                confidence_score=confidence,
                tone_quality=tone_quality,
                business_context={
                    "questions_answered": questions_answered,
                    "seller_motivation": analysis["motivation_score"],
                    "urgency_level": analysis["urgency_score"]
                }
            )

        except Exception as e:
            self.logger.error(f"Response generation error: {e}")
            return self._fallback_jorge_response()

    def _fallback_jorge_response(self) -> OptimizedResponse:
        """Fallback response when AI generation fails"""

        fallback_responses = [
            "Look, I buy houses fast for cash. If you're serious about selling in the next 30-45 days, let's talk. If not, don't waste my time.",
            "I'm Jorge, and I make cash offers on houses. Are you actually ready to sell, or are you just shopping around?",
            "Here's the deal - I can close in 2-3 weeks with cash if you're serious. What's your situation?"
        ]

        return OptimizedResponse(
            message=random.choice(fallback_responses),
            confidence_score=0.7,
            tone_quality="fallback_authentic",
            business_context={"fallback_used": True},
            fallback_used=True
        )

    async def _safe_get_context(self, contact_id: str, location_id: str) -> Dict:
        """Safely retrieve conversation context with error handling"""

        try:
            return await self.conversation_manager.get_context(contact_id, location_id)
        except Exception as e:
            self.logger.warning(f"Context retrieval error: {e}")
            return {
                "conversation_history": [],
                "seller_questions_answered": 0,
                "seller_temperature": "cold"
            }

    def _calculate_seller_temperature(
        self,
        analysis: Dict,
        questions_answered: int,
        context: Dict
    ) -> str:
        """Enhanced temperature calculation"""

        # Base score from analysis
        score = analysis["motivation_score"] * 0.4 + analysis["urgency_score"] * 0.4

        # Bonus for completing questions
        completion_bonus = (questions_answered / 4) * 0.2
        score += completion_bonus

        # Temperature thresholds - OPTIMIZED FOR MOTIVATED SELLERS
        if score >= 0.7:  # Lowered from 0.8
            return "hot"
        elif score >= 0.4:  # Lowered from 0.5
            return "warm"
        else:
            return "cold"

    def _generate_seller_actions(self, temperature: str, analysis: Dict) -> List[Dict]:
        """Generate GHL actions based on seller qualification"""

        actions = []

        # Temperature-based tagging
        actions.append({"type": "add_tag", "tag": f"{temperature.capitalize()}-Seller"})

        # Remove other temperature tags
        other_temps = ["Hot-Seller", "Warm-Seller", "Cold-Seller"]
        other_temps.remove(f"{temperature.capitalize()}-Seller")
        for temp_tag in other_temps:
            actions.append({"type": "remove_tag", "tag": temp_tag})

        # Motivation-based tagging
        if analysis["motivation_type"] != "unknown":
            actions.append({"type": "add_tag", "tag": f"Motivation-{analysis['motivation_type'].capitalize()}"})

        # Urgency-based actions
        if analysis["urgency_score"] > 0.7:
            actions.append({"type": "add_tag", "tag": "Urgent-Seller"})
            actions.append({"type": "trigger_workflow", "workflow_id": "urgent_seller_sequence"})

        # Update custom fields
        actions.append({
            "type": "update_custom_field",
            "field": "seller_temperature",
            "value": temperature
        })

        actions.append({
            "type": "update_custom_field",
            "field": "motivation_score",
            "value": str(analysis["motivation_score"])
        })

        return actions

    async def _update_seller_context(
        self,
        contact_id: str,
        location_id: str,
        user_message: str,
        response: OptimizedResponse,
        analysis: Dict,
        questions_answered: int
    ) -> None:
        """Update conversation context with seller data"""

        try:
            seller_temperature = self._calculate_seller_temperature(
                analysis=analysis,
                questions_answered=questions_answered + 1,
                context={}
            )
            context_update = {
                "seller_questions_answered": questions_answered + 1,
                "last_user_message": user_message,
                "last_ai_response": response.message,
                "last_ai_response_time": datetime.now().isoformat(),
                "seller_motivation_score": analysis["motivation_score"],
                "seller_urgency_score": analysis["urgency_score"],
                "seller_motivation_type": analysis["motivation_type"],
                "seller_temperature": seller_temperature,
                "response_confidence": response.confidence_score
            }

            extracted_data = {
                "lead_type": "seller",
                "motivation_score": analysis.get("motivation_score"),
                "urgency_score": analysis.get("urgency_score"),
                "motivation_type": analysis.get("motivation_type"),
                "questions_answered": questions_answered + 1
            }

            await self.conversation_manager.update_context(
                contact_id=contact_id,
                user_message=user_message,
                ai_response=response.message,
                extracted_data=extracted_data,
                location_id=location_id,
                **context_update
            )

        except Exception as e:
            self.logger.error(f"Context update error: {e}")

    async def _fallback_seller_response(self, user_message: str) -> Dict[str, Any]:
        """Fallback response when everything fails"""

        return {
            "message": "Thanks for reaching out about selling your house. Let me have our team review your situation and get back to you with next steps.",
            "temperature": "warm",
            "questions_answered": 0,
            "actions": [{"type": "add_tag", "tag": "Needs-Manual-Review"}],
            "seller_motivation": 0.5,
            "urgency_level": 0.5,
            "confidence": 0.5,
            "tone_quality": "fallback"
        }


import random  # Add this import for random.choice


class JorgeLeadEngineOptimized:
    """
    Optimized lead engine with enhanced buyer qualification
    and improved response generation.
    """

    def __init__(self, conversation_manager, ghl_client):
        self.conversation_manager = conversation_manager
        self.ghl_client = ghl_client
        self.logger = logging.getLogger(__name__)

    async def process_lead_message(
        self,
        contact_id: str,
        user_message: str,
        location_id: str,
        tenant_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Enhanced lead processing with robust error handling"""

        try:
            # Analyze lead with better extraction
            lead_data = self._enhanced_lead_analysis(user_message)

            # Get safe context
            context = await self._safe_get_context(contact_id, location_id)

            # Generate intelligent response
            response = await self._generate_lead_response(user_message, lead_data, context)

            # Calculate enhanced lead score
            lead_score = self._calculate_enhanced_lead_score(lead_data, context)

            # Determine temperature
            temperature = self._calculate_lead_temperature(lead_score)

            # Generate actions
            actions = self._generate_lead_actions(temperature, lead_data)

            # Update context safely
            await self._safe_update_context(contact_id, location_id, user_message, response, lead_data, lead_score)

            return {
                "message": response.message,
                "lead_score": lead_score,
                "lead_temperature": temperature,
                "budget_max": lead_data.get("budget_max"),
                "timeline": lead_data.get("timeline"),
                "location_preferences": lead_data.get("location"),
                "financing_status": lead_data.get("financing_status"),
                "actions": actions,
                "confidence": response.confidence_score
            }

        except Exception as e:
            self.logger.error(f"Lead processing error: {e}")
            return await self._fallback_lead_response(user_message)

    def _enhanced_lead_analysis(self, message: str) -> Dict[str, Any]:
        """Enhanced lead analysis with better pattern recognition"""

        message_lower = message.lower()

        # Budget extraction with improved patterns
        budget_patterns = [
            r'\$([0-9,]+)k',  # $700k
            r'\$([0-9,]+),000',  # $500,000
            r'([0-9]+)k budget',  # 700k budget
            r'under \$([0-9,]+)',  # under $700k
            r'up to \$([0-9,]+)'  # up to $700k
        ]

        budget_max = None
        for pattern in budget_patterns:
            import re
            match = re.search(pattern, message_lower)
            if match:
                try:
                    amount = int(match.group(1).replace(',', ''))
                    if 'k' in pattern:
                        amount *= 1000
                    budget_max = amount
                    break
                except ValueError:
                    continue

        # Timeline extraction
        timeline_keywords = {
            "immediate": ["immediately", "asap", "right now", "urgent"],
            "30_days": ["30 days", "month", "within a month"],
            "60_days": ["60 days", "two months", "couple months"],
            "90_days": ["90 days", "three months", "quarter"],
            "flexible": ["flexible", "no rush", "whenever", "eventually"]
        }

        timeline = "unknown"
        for period, keywords in timeline_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                timeline = period
                break

        # Location extraction
        rancho_cucamonga_areas = [
            "west lake", "alta_loma", "bee cave", "lakeway", "dripping springs",
            "round rock", "cedar park", "leander", "georgetown", "day_creek",
            "north rancho_cucamonga", "south rancho_cucamonga", "east rancho_cucamonga", "central rancho_cucamonga",
            "central_rc", "mueller", "domain", "arboretum"
        ]

        location_preferences = []
        for area in rancho_cucamonga_areas:
            if area in message_lower:
                location_preferences.append(area.title())

        # Financing status
        financing_indicators = {
            "pre_approved": ["pre-approved", "preapproved", "pre approved", "already approved"],
            "cash": ["cash", "cash buyer", "all cash"],
            "needs_financing": ["need financing", "getting approved", "loan"],
            "unknown": []
        }

        financing_status = "unknown"
        for status, keywords in financing_indicators.items():
            if any(keyword in message_lower for keyword in keywords):
                financing_status = status
                break

        # Urgency indicators
        urgency_keywords = ["urgent", "quickly", "fast", "asap", "need to", "have to"]
        urgency_score = sum(1 for keyword in urgency_keywords if keyword in message_lower) / len(urgency_keywords)

        # Quality indicators
        quality_indicators = [
            "relocating", "job", "pre-approved", "cash", "specific area",
            "budget", "timeline", "ready to buy", "serious"
        ]
        quality_score = sum(1 for indicator in quality_indicators if indicator in message_lower) / len(quality_indicators)

        return {
            "budget_max": budget_max,
            "timeline": timeline,
            "location": location_preferences,
            "financing_status": financing_status,
            "urgency_score": urgency_score,
            "quality_score": quality_score,
            "message_length": len(message),
            "mentions_specific_needs": len(location_preferences) > 0 or budget_max is not None,
            "sounds_qualified": quality_score > 0.3 and (budget_max is not None or financing_status != "unknown")
        }

    async def _generate_lead_response(self, user_message: str, lead_data: Dict, context: Dict) -> OptimizedResponse:
        """Generate intelligent lead response"""

        # Determine response type based on lead data
        if lead_data["sounds_qualified"]:
            # High-quality lead response
            response_parts = []

            # Acknowledge their specific needs
            if lead_data["budget_max"]:
                response_parts.append(f"Great! I have several options in your ${lead_data['budget_max']:,} price range.")

            if lead_data["location"]:
                areas = ", ".join(lead_data["location"][:2])  # Limit to first 2 areas
                response_parts.append(f"The {areas} area has some excellent properties right now.")

            if lead_data["financing_status"] == "pre_approved":
                response_parts.append("Since you're already pre-approved, we can move quickly on anything you like.")

            # Add helpful next step
            response_parts.append("Let me ask you a couple quick questions to narrow down the perfect options for you:")

            # Ask relevant follow-up questions
            if not lead_data["budget_max"]:
                response_parts.append("What's your budget range?")
            if not lead_data["location"]:
                response_parts.append("Which areas of Rancho Cucamonga interest you most?")
            if lead_data["financing_status"] == "unknown":
                response_parts.append("Are you pre-approved for financing or paying cash?")

            response_text = " ".join(response_parts)
            confidence = 0.9
            tone_quality = "professional_helpful"

        else:
            # Lower-quality lead - still helpful but more qualifying
            response_text = "I'd love to help you find the right home in Rancho Cucamonga! To make sure I show you properties that fit your needs, can you tell me more about your budget range and which areas you're considering?"
            confidence = 0.6
            tone_quality = "qualifying"

        return OptimizedResponse(
            message=response_text,
            confidence_score=confidence,
            tone_quality=tone_quality,
            business_context=lead_data
        )

    def _calculate_enhanced_lead_score(self, lead_data: Dict, context: Dict) -> float:
        """Enhanced lead scoring with robust error handling"""

        try:
            score = 50.0  # Base score

            # Budget score
            if lead_data.get("budget_max"):
                if lead_data["budget_max"] >= 700000:
                    score += 20  # High budget
                elif lead_data["budget_max"] >= 700000:
                    score += 15  # Medium budget
                else:
                    score += 10  # Any budget mentioned

            # Timeline score
            timeline_scores = {
                "immediate": 20,
                "30_days": 15,
                "60_days": 10,
                "90_days": 5,
                "flexible": -5
            }
            score += timeline_scores.get(lead_data.get("timeline", "unknown"), 0)

            # Financing score
            financing_scores = {
                "cash": 20,
                "pre_approved": 15,
                "needs_financing": 5,
                "unknown": -5
            }
            score += financing_scores.get(lead_data.get("financing_status", "unknown"), 0)

            # Location specificity
            if lead_data.get("location") and len(lead_data["location"]) > 0:
                score += 10

            # Quality indicators
            score += lead_data.get("quality_score", 0) * 15

            # Urgency
            score += lead_data.get("urgency_score", 0) * 10

            # Conversation engagement (from context)
            conversation_count = len(context.get("conversation_history", []))
            if conversation_count > 1:
                score += min(conversation_count * 2, 10)  # Cap at 10 points

            return max(0, min(100, score))  # Clamp between 0-100

        except Exception as e:
            self.logger.error(f"Lead scoring error: {e}")
            return 50.0  # Safe fallback score

    def _calculate_lead_temperature(self, score: float) -> str:
        """Calculate lead temperature from score"""

        if score >= 80:
            return "hot"
        elif score >= 60:
            return "warm"
        else:
            return "cold"

    def _generate_lead_actions(self, temperature: str, lead_data: Dict) -> List[Dict]:
        """Generate GHL actions for lead"""

        actions = []

        # Temperature tagging
        actions.append({"type": "add_tag", "tag": f"{temperature.capitalize()}-Lead"})

        # Budget-based tagging
        if lead_data.get("budget_max"):
            if lead_data["budget_max"] >= 700000:
                actions.append({"type": "add_tag", "tag": "High-Budget"})
            elif lead_data["budget_max"] >= 700000:
                actions.append({"type": "add_tag", "tag": "Medium-Budget"})
            else:
                actions.append({"type": "add_tag", "tag": "Budget-Conscious"})

        # Timeline tagging
        if lead_data.get("timeline") in ["immediate", "30_days"]:
            actions.append({"type": "add_tag", "tag": "Urgent-Buyer"})

        # Financing tagging
        if lead_data.get("financing_status") == "cash":
            actions.append({"type": "add_tag", "tag": "Cash-Buyer"})
        elif lead_data.get("financing_status") == "pre_approved":
            actions.append({"type": "add_tag", "tag": "Pre-Approved"})

        # Custom field updates
        if lead_data.get("budget_max"):
            actions.append({
                "type": "update_custom_field",
                "field": "budget_range",
                "value": f"${lead_data['budget_max']:,}"
            })

        if lead_data.get("location"):
            actions.append({
                "type": "update_custom_field",
                "field": "location_preference",
                "value": ", ".join(lead_data["location"])
            })

        return actions

    async def _safe_get_context(self, contact_id: str, location_id: str) -> Dict:
        """Safely get conversation context"""

        try:
            return await self.conversation_manager.get_context(contact_id, location_id)
        except Exception as e:
            self.logger.warning(f"Context retrieval error: {e}")
            return {
                "conversation_history": [],
                "lead_score": 50.0,
                "lead_temperature": "cold"
            }

    async def _safe_update_context(self, contact_id: str, location_id: str, user_message: str, response: OptimizedResponse, lead_data: Dict, lead_score: float):
        """Safely update conversation context"""

        try:
            lead_temperature = self._calculate_lead_temperature(lead_score)
            context_update = {
                "last_user_message": user_message,
                "last_ai_response": response.message,
                "last_ai_response_time": datetime.now().isoformat(),
                "lead_score": lead_score,
                "lead_temperature": lead_temperature,
                "budget_max": lead_data.get("budget_max"),
                "timeline": lead_data.get("timeline"),
                "financing_status": lead_data.get("financing_status"),
                "response_confidence": response.confidence_score
            }

            extracted_data = dict(lead_data)
            extracted_data["lead_type"] = "buyer"
            extracted_data["lead_score"] = lead_score

            await self.conversation_manager.update_context(
                contact_id=contact_id,
                user_message=user_message,
                ai_response=response.message,
                extracted_data=extracted_data,
                location_id=location_id,
                **context_update
            )

        except Exception as e:
            self.logger.error(f"Context update error: {e}")

    async def _fallback_lead_response(self, user_message: str) -> Dict[str, Any]:
        """Fallback lead response when everything fails"""

        return {
            "message": "Thanks for your interest in buying a home in Rancho Cucamonga! I'd love to help you find the perfect property. Let me connect you with our team to discuss your needs in detail.",
            "lead_score": 50.0,
            "lead_temperature": "warm",
            "budget_max": None,
            "timeline": "unknown",
            "location_preferences": [],
            "financing_status": "unknown",
            "actions": [{"type": "add_tag", "tag": "Needs-Manual-Follow-up"}],
            "confidence": 0.5
        }
