#!/usr/bin/env python3
"""
🧠 Behavioral Signal Processor
=============================

Advanced behavioral signal extraction system that analyzes 50+ behavioral patterns
from lead interactions to predict conversion probability.

Features:
- 50+ behavioral signals extraction
- Real-time pattern recognition
- Conversation sentiment analysis
- Engagement velocity tracking
- Decision-making stage detection
- Financial readiness assessment
- Objection pattern recognition
- Communication preference analysis

Author: Lead Scoring 2.0 Implementation
Date: 2026-01-18
"""

import re
import statistics
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class SignalCategory(Enum):
    """Categories of behavioral signals"""

    ENGAGEMENT = "engagement"
    FINANCIAL = "financial"
    URGENCY = "urgency"
    OBJECTIONS = "objections"
    COMMUNICATION = "communication"
    DECISION_STAGE = "decision_stage"
    LIFESTYLE = "lifestyle"
    TECHNICAL = "technical"


class EngagementPattern(Enum):
    """Engagement patterns"""

    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    SPORADIC = "sporadic"
    INITIAL_BURST = "initial_burst"


@dataclass
class BehavioralSignal:
    """Individual behavioral signal"""

    name: str
    value: float  # Normalized 0-1
    confidence: float  # 0-1
    category: SignalCategory
    description: str
    raw_value: Any = None


class BehavioralSignalProcessor:
    """
    Advanced behavioral signal processing engine.

    Extracts 50+ behavioral signals from lead data and conversation history
    to provide deep insights into lead behavior and conversion probability.
    """

    def __init__(self):
        self.signal_weights = self._initialize_signal_weights()
        self.financial_keywords = self._initialize_financial_keywords()
        self.urgency_keywords = self._initialize_urgency_keywords()
        self.objection_keywords = self._initialize_objection_keywords()
        self.lifestyle_keywords = self._initialize_lifestyle_keywords()

        logger.info("BehavioralSignalProcessor initialized with 50+ signal extractors")

    def extract_signals(
        self, lead_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Extract all behavioral signals and return normalized scores.

        Args:
            lead_data: Lead information and metadata
            conversation_history: List of conversation messages

        Returns:
            Dict mapping signal names to normalized scores (0-1)
        """
        signals = {}

        try:
            # Extract all signal categories
            engagement_signals = self._extract_engagement_signals(lead_data, conversation_history)
            financial_signals = self._extract_financial_signals(lead_data, conversation_history)
            urgency_signals = self._extract_urgency_signals(lead_data, conversation_history)
            objection_signals = self._extract_objection_signals(conversation_history)
            communication_signals = self._extract_communication_signals(conversation_history)
            decision_signals = self._extract_decision_stage_signals(conversation_history)
            lifestyle_signals = self._extract_lifestyle_signals(lead_data, conversation_history)
            technical_signals = self._extract_technical_signals(lead_data, conversation_history)

            # Combine all signals
            all_signals = {
                **engagement_signals,
                **financial_signals,
                **urgency_signals,
                **objection_signals,
                **communication_signals,
                **decision_signals,
                **lifestyle_signals,
                **technical_signals,
            }

            # Normalize and validate
            signals = self._normalize_signals(all_signals)

            logger.debug(f"Extracted {len(signals)} behavioral signals")

        except Exception as e:
            logger.error(f"Signal extraction failed: {e}")
            # Return default signals
            signals = self._get_default_signals()

        return signals

    def _extract_engagement_signals(
        self, lead_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Extract engagement-related behavioral signals"""
        signals = {}

        try:
            # Signal 1: Email open rate
            opens = lead_data.get("email_opens", 0)
            sent = lead_data.get("emails_sent", 1)
            signals["email_open_rate"] = min(opens / max(sent, 1), 1.0)

            # Signal 2: Email click rate
            clicks = lead_data.get("email_clicks", 0)
            signals["email_click_rate"] = min(clicks / max(sent, 1), 1.0)

            # Signal 3: Response velocity (speed of responses)
            response_times = [
                msg.get("response_time_seconds", 86400)
                for msg in conversation_history
                if msg.get("response_time_seconds") is not None
            ]
            if response_times:
                avg_response_time = statistics.mean(response_times)
                # Normalize: <1hr = 1.0, >24hr = 0.0
                signals["response_velocity"] = max(0, 1.0 - (avg_response_time / 86400))
            else:
                signals["response_velocity"] = 0.5

            # Signal 4: Conversation frequency
            if conversation_history:
                timestamps = [
                    datetime.fromisoformat(msg.get("timestamp", datetime.now().isoformat()).replace("Z", ""))
                    for msg in conversation_history
                    if msg.get("timestamp")
                ]
                if len(timestamps) >= 2:
                    time_span = (max(timestamps) - min(timestamps)).total_seconds()
                    frequency = len(timestamps) / max(time_span / 86400, 1)  # messages per day
                    signals["conversation_frequency"] = min(frequency / 5.0, 1.0)  # 5+ msgs/day = 1.0
                else:
                    signals["conversation_frequency"] = 0.3
            else:
                signals["conversation_frequency"] = 0.0

            # Signal 5: Message length trend (increasing indicates growing interest)
            message_lengths = [len(msg.get("text", "")) for msg in conversation_history if msg.get("text")]
            if len(message_lengths) >= 2:
                # Simple linear trend
                x = list(range(len(message_lengths)))
                y = message_lengths
                if len(set(x)) > 1:  # Avoid division by zero
                    slope = sum((xi - statistics.mean(x)) * (yi - statistics.mean(y)) for xi, yi in zip(x, y)) / sum(
                        (xi - statistics.mean(x)) ** 2 for xi in x
                    )
                    signals["message_length_trend"] = max(0, min(slope / 100, 1.0))  # Normalize slope
                else:
                    signals["message_length_trend"] = 0.5
            else:
                signals["message_length_trend"] = 0.5

            # Signal 6: Question asking frequency
            total_messages = len(conversation_history)
            question_messages = sum(1 for msg in conversation_history if "?" in msg.get("text", ""))
            signals["question_frequency"] = question_messages / max(total_messages, 1) if total_messages > 0 else 0

            # Signal 7: Proactive communication (initiating conversations)
            # Assume lead-initiated messages have certain indicators
            proactive_count = sum(
                1
                for msg in conversation_history
                if msg.get("sender") == "lead"
                or any(
                    indicator in msg.get("text", "").lower()
                    for indicator in ["hi", "hello", "quick question", "i was thinking"]
                )
            )
            signals["proactive_communication"] = proactive_count / max(total_messages, 1) if total_messages > 0 else 0

            # Signal 8: Weekend/evening engagement
            weekend_msgs = sum(
                1
                for msg in conversation_history
                if msg.get("timestamp") and datetime.fromisoformat(msg["timestamp"].replace("Z", "")).weekday() >= 5
            )
            signals["weekend_engagement"] = weekend_msgs / max(total_messages, 1) if total_messages > 0 else 0

            # Signal 9: Multi-channel engagement
            channels = set(msg.get("channel", "unknown") for msg in conversation_history)
            signals["multichannel_engagement"] = min(len(channels) / 3.0, 1.0)  # 3+ channels = 1.0

        except Exception as e:
            logger.warning(f"Engagement signal extraction failed: {e}")

        return signals

    def _extract_financial_signals(
        self, lead_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Extract financial readiness and capacity signals"""
        signals = {}

        try:
            all_text = " ".join([msg.get("text", "") for msg in conversation_history]).lower()

            # Signal 10: Pre-approval mentions
            preapproval_indicators = [
                "pre-approved",
                "preapproved",
                "pre approved",
                "approved for",
                "pre-qualification",
                "lender approval",
                "financing approved",
            ]
            signals["preapproval_mentions"] = float(any(indicator in all_text for indicator in preapproval_indicators))

            # Signal 11: Cash buyer indicators
            cash_indicators = [
                "cash buyer",
                "cash purchase",
                "no financing",
                "cash offer",
                "pay cash",
                "cash in hand",
                "no mortgage needed",
            ]
            signals["cash_buyer_indicators"] = float(any(indicator in all_text for indicator in cash_indicators))

            # Signal 12: Financial urgency
            financial_urgency = [
                "need to close",
                "closing soon",
                "rate lock",
                "rate expires",
                "financing deadline",
                "approval expires",
            ]
            signals["financial_urgency"] = float(any(indicator in all_text for indicator in financial_urgency))

            # Signal 13: Budget specificity
            budget_patterns = re.findall(r"\$[\d,]+", all_text)
            budget_ranges = len(re.findall(r"\$[\d,]+\s*to\s*\$[\d,]+", all_text))
            signals["budget_specificity"] = min((len(budget_patterns) + budget_ranges) / 3.0, 1.0)

            # Signal 14: Down payment mentions
            down_payment_indicators = [
                "down payment",
                "downpayment",
                "deposit",
                "earnest money",
                "closing costs",
                "cash down",
            ]
            signals["down_payment_readiness"] = float(
                any(indicator in all_text for indicator in down_payment_indicators)
            )

            # Signal 15: Credit score references
            credit_indicators = [
                "credit score",
                "fico",
                "credit report",
                "credit check",
                "excellent credit",
                "good credit",
            ]
            signals["credit_awareness"] = float(any(indicator in all_text for indicator in credit_indicators))

            # Signal 16: Lender relationships
            lender_indicators = [
                "my lender",
                "our lender",
                "bank pre-approved",
                "working with",
                "loan officer",
                "mortgage broker",
            ]
            signals["lender_relationships"] = float(any(indicator in all_text for indicator in lender_indicators))

        except Exception as e:
            logger.warning(f"Financial signal extraction failed: {e}")

        return signals

    def _extract_urgency_signals(
        self, lead_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Extract urgency and timeline signals"""
        signals = {}

        try:
            all_text = " ".join([msg.get("text", "") for msg in conversation_history]).lower()

            # Signal 17: Immediate timeline
            immediate_indicators = [
                "asap",
                "immediately",
                "urgent",
                "right away",
                "today",
                "this week",
                "next week",
                "2 weeks",
                "by friday",
            ]
            signals["immediate_timeline"] = float(any(indicator in all_text for indicator in immediate_indicators))

            # Signal 18: Relocation pressure
            relocation_indicators = [
                "relocating",
                "moving for work",
                "job transfer",
                "new job",
                "start date",
                "lease expires",
                "lease ending",
            ]
            signals["relocation_pressure"] = float(any(indicator in all_text for indicator in relocation_indicators))

            # Signal 19: Market timing concern
            timing_concerns = [
                "before rates go up",
                "before prices rise",
                "market is hot",
                "competition is fierce",
                "inventory is low",
                "miss out",
            ]
            signals["market_timing_concern"] = float(any(concern in all_text for concern in timing_concerns))

            # Signal 20: Life event drivers
            life_events = [
                "getting married",
                "new baby",
                "divorce",
                "retirement",
                "kids starting school",
                "family growing",
            ]
            signals["life_event_drivers"] = float(any(event in all_text for event in life_events))

            # Signal 21: Deadline mentions
            deadline_patterns = re.findall(
                r"(Union[by, before]|need Union[to, must]|have to).{0,20}(Union[january, february]|Union[march, april]|Union[may, june]|Union[july, august]|Union[september, october]|Union[november, december]|\d{1,2}\/\d{1,2})",
                all_text,
            )
            signals["specific_deadlines"] = min(len(deadline_patterns) / 2.0, 1.0)

            # Signal 22: Viewing urgency
            viewing_urgency = [
                "see it today",
                "available this weekend",
                "show me now",
                "can we tour",
                "schedule viewing",
                "see it soon",
            ]
            signals["viewing_urgency"] = float(any(phrase in all_text for phrase in viewing_urgency))

        except Exception as e:
            logger.warning(f"Urgency signal extraction failed: {e}")

        return signals

    def _extract_objection_signals(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract objection patterns and concerns"""
        signals = {}

        try:
            all_text = " ".join([msg.get("text", "") for msg in conversation_history]).lower()

            # Signal 23: Price objections
            price_objections = [
                "too expensive",
                "can't afford",
                "out of budget",
                "too much",
                "price is high",
                "over my budget",
                "overpriced",
            ]
            signals["price_objections"] = float(any(objection in all_text for objection in price_objections))

            # Signal 24: Location concerns
            location_objections = [
                "too far",
                "commute is long",
                "wrong area",
                "not the right neighborhood",
                "don't like the location",
                "area is not good",
            ]
            signals["location_concerns"] = float(any(objection in all_text for objection in location_objections))

            # Signal 25: Condition concerns
            condition_objections = [
                "needs work",
                "needs updating",
                "old house",
                "condition is poor",
                "requires renovation",
                "fixer upper",
                "not move-in ready",
            ]
            signals["condition_concerns"] = float(any(objection in all_text for objection in condition_objections))

            # Signal 26: Market concerns
            market_objections = [
                "market is volatile",
                "prices might drop",
                "bubble",
                "wait for market to cool",
                "overheated market",
            ]
            signals["market_concerns"] = float(any(objection in all_text for objection in market_objections))

            # Signal 27: Decision maker involvement
            decision_maker_concerns = [
                "need to ask my",
                "spouse needs to see",
                "family decision",
                "have to discuss",
                "need approval",
                "not my decision alone",
            ]
            signals["decision_maker_concerns"] = float(any(concern in all_text for concern in decision_maker_concerns))

        except Exception as e:
            logger.warning(f"Objection signal extraction failed: {e}")

        return signals

    def _extract_communication_signals(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract communication style and preference signals"""
        signals = {}

        try:
            # Signal 28: Communication preference (text vs call)
            text_indicators = sum(1 for msg in conversation_history if len(msg.get("text", "")) > 50)
            call_mentions = sum(
                1
                for msg in conversation_history
                if any(word in msg.get("text", "").lower() for word in ["call me", "phone", "talk", "speak"])
            )

            total_comm = text_indicators + call_mentions
            if total_comm > 0:
                signals["prefers_text_communication"] = text_indicators / total_comm
            else:
                signals["prefers_text_communication"] = 0.5

            # Signal 29: Formality level
            formal_indicators = sum(
                1
                for msg in conversation_history
                if any(word in msg.get("text", "") for word in ["Thank you", "Please", "I would", "Could you"])
            )
            informal_indicators = sum(
                1
                for msg in conversation_history
                if any(word in msg.get("text", "").lower() for word in ["hey", "yeah", "cool", "awesome", "lol"])
            )

            total_style = formal_indicators + informal_indicators
            if total_style > 0:
                signals["formal_communication_style"] = formal_indicators / total_style
            else:
                signals["formal_communication_style"] = 0.5

            # Signal 30: Detail orientation
            detailed_questions = sum(
                1 for msg in conversation_history if len(msg.get("text", "")) > 100 and "?" in msg.get("text", "")
            )
            total_questions = sum(1 for msg in conversation_history if "?" in msg.get("text", ""))

            signals["detail_oriented"] = detailed_questions / max(total_questions, 1) if total_questions > 0 else 0

            # Signal 31: Technical language usage
            technical_terms = [
                "square footage",
                "sqft",
                "hoa",
                "apr",
                "down payment",
                "amortization",
                "property tax",
                "closing costs",
                "inspection",
                "appraisal",
            ]
            all_text = " ".join([msg.get("text", "") for msg in conversation_history]).lower()
            technical_count = sum(1 for term in technical_terms if term in all_text)
            signals["technical_language_usage"] = min(technical_count / 5.0, 1.0)

            # Signal 32: Emotional language
            emotional_words = [
                "love",
                "excited",
                "dream",
                "perfect",
                "amazing",
                "worried",
                "concerned",
                "frustrated",
                "disappointed",
            ]
            emotional_count = sum(1 for word in emotional_words if word in all_text)
            signals["emotional_language"] = min(emotional_count / 3.0, 1.0)

        except Exception as e:
            logger.warning(f"Communication signal extraction failed: {e}")

        return signals

    def _extract_decision_stage_signals(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract signals about decision-making stage"""
        signals = {}

        try:
            all_text = " ".join([msg.get("text", "") for msg in conversation_history]).lower()

            # Signal 33: Research stage indicators
            research_indicators = [
                "looking for information",
                "researching",
                "comparing",
                "options",
                "what's available",
                "tell me about",
                "how does",
                "what are",
            ]
            signals["in_research_stage"] = float(any(indicator in all_text for indicator in research_indicators))

            # Signal 34: Evaluation stage
            evaluation_indicators = [
                "which is better",
                "pros and cons",
                "differences between",
                "compare",
                "versus",
                "decision factors",
            ]
            signals["in_evaluation_stage"] = float(any(indicator in all_text for indicator in evaluation_indicators))

            # Signal 35: Purchase intent
            purchase_indicators = [
                "ready to buy",
                "make an offer",
                "put in offer",
                "close on",
                "purchase",
                "move forward",
                "next steps",
            ]
            signals["purchase_intent"] = float(any(indicator in all_text for indicator in purchase_indicators))

            # Signal 36: Comparison shopping
            comparison_indicators = [
                "other agents",
                "shopping around",
                "other properties",
                "different areas",
                "alternatives",
                "other options",
            ]
            signals["comparison_shopping"] = float(any(indicator in all_text for indicator in comparison_indicators))

            # Signal 37: Commitment signals
            commitment_indicators = [
                "this is the one",
                "perfect for us",
                "exactly what",
                "ready to move",
                "let's do it",
                "when can we",
                "how soon",
            ]
            signals["commitment_signals"] = float(any(indicator in all_text for indicator in commitment_indicators))

        except Exception as e:
            logger.warning(f"Decision stage signal extraction failed: {e}")

        return signals

    def _extract_lifestyle_signals(
        self, lead_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Extract lifestyle and demographic signals"""
        signals = {}

        try:
            all_text = " ".join([msg.get("text", "") for msg in conversation_history]).lower()

            # Signal 38: Family status
            family_indicators = [
                "kids",
                "children",
                "family",
                "school district",
                "playground",
                "family room",
                "bedrooms for kids",
            ]
            signals["family_oriented"] = float(any(indicator in all_text for indicator in family_indicators))

            # Signal 39: Professional status
            professional_indicators = [
                "work from home",
                "home office",
                "commute",
                "job",
                "career",
                "business",
                "company",
                "employer",
            ]
            signals["professional_focus"] = float(any(indicator in all_text for indicator in professional_indicators))

            # Signal 40: Investment mindset
            investment_indicators = [
                "investment",
                "roi",
                "appreciation",
                "rental",
                "property value",
                "market value",
                "resale",
                "equity",
            ]
            signals["investment_mindset"] = float(any(indicator in all_text for indicator in investment_indicators))

            # Signal 41: Luxury preferences
            luxury_indicators = [
                "luxury",
                "high-end",
                "premium",
                "custom",
                "upgraded",
                "gourmet",
                "spa",
                "pool",
                "view",
            ]
            signals["luxury_preferences"] = float(any(indicator in all_text for indicator in luxury_indicators))

            # Signal 42: First-time buyer
            first_time_indicators = [
                "first time",
                "first home",
                "never bought",
                "new to",
                "first purchase",
                "don't know process",
            ]
            signals["first_time_buyer"] = float(any(indicator in all_text for indicator in first_time_indicators))

            # Signal 43: Relocation status
            relocation_indicators = [
                "moving from",
                "relocating",
                "new to area",
                "unfamiliar with",
                "coming from",
                "transferring",
            ]
            signals["relocating"] = float(any(indicator in all_text for indicator in relocation_indicators))

        except Exception as e:
            logger.warning(f"Lifestyle signal extraction failed: {e}")

        return signals

    def _extract_technical_signals(
        self, lead_data: Dict[str, Any], conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Extract technical and data-driven signals"""
        signals = {}

        try:
            # Signal 44: Device engagement patterns
            page_views = lead_data.get("page_views", 0)
            signals["digital_engagement"] = min(page_views / 20.0, 1.0)

            # Signal 45: Time on site
            session_duration = lead_data.get("session_duration_minutes", 0)
            signals["deep_research"] = min(session_duration / 30.0, 1.0)  # 30+ minutes = 1.0

            # Signal 46: Property view velocity
            properties_viewed = lead_data.get("properties_viewed", 0)
            days_active = lead_data.get("days_since_first_contact", 1)
            signals["property_view_velocity"] = min((properties_viewed / max(days_active, 1)) / 2.0, 1.0)

            # Signal 47: Search specificity
            search_terms = lead_data.get("search_terms", [])
            specific_searches = sum(1 for term in search_terms if len(term.split()) > 2)
            signals["search_specificity"] = min(specific_searches / max(len(search_terms), 1), 1.0)

            # Signal 48: Email engagement timing
            last_email_open = lead_data.get("last_email_open_hours_ago", 168)  # Default 1 week
            signals["recent_email_engagement"] = max(0, 1.0 - (last_email_open / 168))  # Weekly scale

            # Signal 49: Multi-session engagement
            unique_sessions = lead_data.get("unique_sessions", 1)
            signals["persistent_interest"] = min(unique_sessions / 5.0, 1.0)  # 5+ sessions = 1.0

            # Signal 50: Conversion funnel progression
            funnel_stage = lead_data.get("funnel_stage", 0)  # 0-5 scale
            signals["funnel_progression"] = funnel_stage / 5.0

            # Bonus Signal 51: AI interaction quality
            ai_interactions = lead_data.get("ai_conversation_quality", 0.5)
            signals["ai_interaction_quality"] = ai_interactions

            # Bonus Signal 52: Lead source quality
            source_quality_map = {
                "organic": 0.9,
                "referral": 1.0,
                "paid_search": 0.7,
                "social": 0.6,
                "direct": 0.8,
                "other": 0.5,
            }
            source = lead_data.get("source", "other")
            signals["source_quality"] = source_quality_map.get(source, 0.5)

        except Exception as e:
            logger.warning(f"Technical signal extraction failed: {e}")

        return signals

    def _normalize_signals(self, signals: Dict[str, float]) -> Dict[str, float]:
        """Normalize and validate all signals to 0-1 range"""
        normalized = {}

        for name, value in signals.items():
            try:
                # Ensure numeric value
                if value is None:
                    value = 0.0
                elif isinstance(value, bool):
                    value = float(value)
                elif not isinstance(value, (int, float)):
                    value = 0.0

                # Clamp to 0-1 range
                normalized[name] = max(0.0, min(float(value), 1.0))

            except Exception as e:
                logger.warning(f"Signal normalization failed for {name}: {e}")
                normalized[name] = 0.0

        return normalized

    def _get_default_signals(self) -> Dict[str, float]:
        """Return default signal values when extraction fails"""
        return {
            "email_open_rate": 0.3,
            "email_click_rate": 0.1,
            "response_velocity": 0.5,
            "conversation_frequency": 0.3,
            "message_length_trend": 0.5,
            "question_frequency": 0.4,
            "proactive_communication": 0.3,
            "weekend_engagement": 0.2,
            "multichannel_engagement": 0.3,
            "preapproval_mentions": 0.0,
            "cash_buyer_indicators": 0.0,
            "financial_urgency": 0.0,
            "budget_specificity": 0.3,
            "down_payment_readiness": 0.0,
            "credit_awareness": 0.0,
            "lender_relationships": 0.0,
            "immediate_timeline": 0.0,
            "relocation_pressure": 0.0,
            "market_timing_concern": 0.0,
            "life_event_drivers": 0.0,
            "specific_deadlines": 0.0,
            "viewing_urgency": 0.0,
            "price_objections": 0.0,
            "location_concerns": 0.0,
            "condition_concerns": 0.0,
            "market_concerns": 0.0,
            "decision_maker_concerns": 0.0,
            "prefers_text_communication": 0.5,
            "formal_communication_style": 0.5,
            "detail_oriented": 0.3,
            "technical_language_usage": 0.2,
            "emotional_language": 0.3,
            "in_research_stage": 0.4,
            "in_evaluation_stage": 0.3,
            "purchase_intent": 0.2,
            "comparison_shopping": 0.4,
            "commitment_signals": 0.1,
            "family_oriented": 0.3,
            "professional_focus": 0.4,
            "investment_mindset": 0.2,
            "luxury_preferences": 0.2,
            "first_time_buyer": 0.3,
            "relocating": 0.2,
            "digital_engagement": 0.3,
            "deep_research": 0.3,
            "property_view_velocity": 0.3,
            "search_specificity": 0.3,
            "recent_email_engagement": 0.3,
            "persistent_interest": 0.3,
            "funnel_progression": 0.3,
            "ai_interaction_quality": 0.5,
            "source_quality": 0.5,
        }

    def _initialize_signal_weights(self) -> Dict[str, float]:
        """Initialize weights for different signals based on impact"""
        return {
            # High impact signals
            "purchase_intent": 0.15,
            "preapproval_mentions": 0.12,
            "cash_buyer_indicators": 0.10,
            "immediate_timeline": 0.10,
            "commitment_signals": 0.08,
            # Medium impact signals
            "response_velocity": 0.06,
            "financial_urgency": 0.06,
            "viewing_urgency": 0.05,
            "conversation_frequency": 0.05,
            "budget_specificity": 0.04,
            # Lower impact but still valuable
            "email_engagement": 0.03,
            "question_frequency": 0.03,
            "detail_oriented": 0.03,
            "digital_engagement": 0.03,
            "source_quality": 0.02,
        }

    def _initialize_financial_keywords(self) -> List[str]:
        """Initialize financial keywords for pattern matching"""
        return [
            "pre-approved",
            "preapproved",
            "cash buyer",
            "financing",
            "down payment",
            "credit score",
            "lender",
            "mortgage",
        ]

    def _initialize_urgency_keywords(self) -> List[str]:
        """Initialize urgency keywords"""
        return ["asap", "urgent", "immediately", "relocating", "deadline", "by friday", "this week", "next week"]

    def _initialize_objection_keywords(self) -> List[str]:
        """Initialize objection keywords"""
        return ["too expensive", "can't afford", "too far", "needs work", "market is volatile", "need to ask"]

    def _initialize_lifestyle_keywords(self) -> List[str]:
        """Initialize lifestyle keywords"""
        return ["family", "kids", "work from home", "investment", "luxury", "first time", "relocating"]

    def get_signal_summary(self, signals: Dict[str, float]) -> Dict[str, Any]:
        """Generate a summary of extracted signals"""
        if not signals:
            return {}

        # Categorize signals
        categories = {
            "engagement": [k for k in signals.keys() if "engagement" in k or "response" in k or "communication" in k],
            "financial": [k for k in signals.keys() if "financial" in k or "cash" in k or "preapproval" in k],
            "urgency": [k for k in signals.keys() if "urgent" in k or "timeline" in k or "deadline" in k],
            "technical": [k for k in signals.keys() if "digital" in k or "property_view" in k or "search" in k],
        }

        summary = {}
        for category, signal_names in categories.items():
            if signal_names:
                category_signals = [signals.get(name, 0) for name in signal_names]
                summary[f"{category}_avg"] = statistics.mean(category_signals)
                summary[f"{category}_max"] = max(category_signals)
                summary[f"{category}_count"] = len([s for s in category_signals if s > 0.5])

        # Overall signal strength
        all_values = list(signals.values())
        summary["overall_signal_strength"] = statistics.mean(all_values)
        summary["strong_signals"] = len([v for v in all_values if v > 0.7])
        summary["weak_signals"] = len([v for v in all_values if v < 0.3])

        return summary


# Example usage
if __name__ == "__main__":
    processor = BehavioralSignalProcessor()

    # Sample data
    lead_data = {
        "email_opens": 8,
        "email_clicks": 3,
        "emails_sent": 10,
        "page_views": 15,
        "session_duration_minutes": 25,
        "source": "organic",
    }

    conversation_history = [
        {"text": "Hi, I'm looking for a house in Austin", "timestamp": "2026-01-15T10:00:00Z"},
        {
            "text": "I'm pre-approved for $500K and need to buy ASAP for my new job at Apple",
            "timestamp": "2026-01-15T10:15:00Z",
        },
        {"text": "Can we see some properties this weekend?", "timestamp": "2026-01-15T11:00:00Z"},
    ]

    # Extract signals
    signals = processor.extract_signals(lead_data, conversation_history)

    print(f"Extracted {len(signals)} behavioral signals:")
    for name, value in sorted(signals.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {name}: {value:.3f}")

    # Get summary
    summary = processor.get_signal_summary(signals)
    print(f"\nSignal Summary: Overall strength = {summary.get('overall_signal_strength', 0):.3f}")
