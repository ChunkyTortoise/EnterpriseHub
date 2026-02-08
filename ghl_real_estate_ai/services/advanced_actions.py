"""
Advanced Workflow Actions Library

Extended library of intelligent workflow actions including:
- Smart content generation
- Multi-channel coordination
- Advanced lead scoring
- Dynamic property matching
- Automated follow-up sequences
"""

import asyncio
import json
import logging
import random
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class ActionPriority(Enum):
    """Action execution priorities"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class ActionStatus(Enum):
    """Action execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ActionResult:
    """Result of action execution"""

    success: bool
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    next_actions: List[str] = field(default_factory=list)
    delay_next: Optional[int] = None  # Seconds to delay next action
    error_details: Optional[str] = None


class BaseAction(ABC):
    """Base class for all workflow actions"""

    def __init__(self, action_id: str, config: Dict[str, Any]):
        self.action_id = action_id
        self.config = config
        self.priority = ActionPriority(config.get("priority", ActionPriority.MEDIUM.value))
        self.max_retries = config.get("max_retries", 2)
        self.retry_delay = config.get("retry_delay", 60)  # seconds

    @abstractmethod
    async def execute(self, lead_data: Dict[str, Any], execution_context: Dict[str, Any]) -> ActionResult:
        """Execute the action"""
        pass

    def validate_config(self) -> List[str]:
        """Validate action configuration"""
        errors = []
        # Base validation - override in subclasses
        return errors


class SmartEmailAction(BaseAction):
    """Intelligent email action with content personalization"""

    async def execute(self, lead_data: Dict[str, Any], execution_context: Dict[str, Any]) -> ActionResult:
        """Execute smart email sending"""
        try:
            template_id = self.config.get("template_id")
            subject_template = self.config.get("subject", "Hello {{first_name}}!")

            # Generate personalized content
            personalized_content = await self._generate_personalized_content(lead_data, execution_context)

            # Apply intelligent subject line optimization
            optimized_subject = await self._optimize_subject_line(subject_template, lead_data, execution_context)

            # Prepare email data
            email_data = {
                "to": lead_data.get("email"),
                "subject": optimized_subject,
                "content": personalized_content,
                "template_id": template_id,
                "personalization_score": personalized_content.get("score", 0.5),
            }

            # Execute email sending (mock implementation)
            success = await self._send_email(email_data)

            if success:
                # Update lead data with email activity
                execution_context["variables"]["last_email"] = {
                    "sent_at": datetime.now().isoformat(),
                    "subject": optimized_subject,
                    "personalization_score": personalized_content.get("score", 0.5),
                }

                return ActionResult(
                    success=True,
                    message=f"Smart email sent to {lead_data.get('email')}",
                    data={"email_data": email_data},
                )
            else:
                return ActionResult(success=False, message="Failed to send email", error_details="Email service error")

        except Exception as e:
            logger.error(f"Smart email action failed: {e}")
            return ActionResult(success=False, message="Smart email action encountered an error", error_details=str(e))

    async def _generate_personalized_content(
        self, lead_data: Dict[str, Any], execution_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate personalized email content"""

        # Base template
        template = self.config.get("content_template", "")

        # Personalization variables
        variables = {
            "first_name": lead_data.get("first_name", "there"),
            "last_name": lead_data.get("last_name", ""),
            "property_interest": lead_data.get("property_interest", "properties"),
            "budget_range": lead_data.get("budget_range", ""),
            "location_preference": lead_data.get("location_preference", ""),
            "lead_source": lead_data.get("source", "our website"),
        }

        # Add contextual variables
        if "last_activity" in execution_context.get("variables", {}):
            variables["last_activity"] = execution_context["variables"]["last_activity"]

        # Smart content selection based on lead score/behavior
        lead_score = lead_data.get("lead_score", 0)
        if lead_score > 70:
            content_variant = "high_intent"
        elif lead_score > 40:
            content_variant = "medium_intent"
        else:
            content_variant = "nurture"

        # Apply content variants
        content = await self._apply_content_variant(template, variables, content_variant)

        # Calculate personalization score
        score = await self._calculate_personalization_score(content, lead_data)

        return {
            "content": content,
            "score": score,
            "variant": content_variant,
            "variables_used": list(variables.keys()),
        }

    async def _optimize_subject_line(
        self, subject_template: str, lead_data: Dict[str, Any], execution_context: Dict[str, Any]
    ) -> str:
        """Optimize email subject line"""

        # Replace variables
        subject = subject_template
        for key, value in lead_data.items():
            subject = subject.replace(f"{{{{{key}}}}}", str(value))

        # Apply A/B testing insights (if available)
        if "ab_test_winner" in execution_context.get("variables", {}):
            winner_pattern = execution_context["variables"]["ab_test_winner"]
            # Apply winning pattern
            subject = await self._apply_subject_pattern(subject, winner_pattern)

        # Add urgency/scarcity if appropriate
        if self.config.get("add_urgency", False):
            urgency_phrases = ["Limited Time", "Act Now", "Don't Miss Out", "Ending Soon"]
            if not any(phrase in subject for phrase in urgency_phrases):
                subject = f"{random.choice(urgency_phrases)}: {subject}"

        return subject

    async def _send_email(self, email_data: Dict[str, Any]) -> bool:
        """Mock email sending implementation"""
        # In real implementation, integrate with email service
        logger.info(f"Sending email to {email_data['to']}: {email_data['subject']}")
        await asyncio.sleep(0.1)  # Simulate API call
        return True

    async def _apply_content_variant(self, template: str, variables: Dict[str, Any], variant: str) -> str:
        """Apply content variant based on lead intent"""

        content_variations = {
            "high_intent": {
                "greeting": "I noticed your strong interest in {property_interest}",
                "cta": "I'd love to schedule a showing this week. When works best for you?",
                "urgency": "These properties are moving quickly in today's market.",
            },
            "medium_intent": {
                "greeting": "Thanks for your interest in {property_interest}",
                "cta": "Would you like me to send you some additional options that match your criteria?",
                "urgency": "I have several clients looking in this area.",
            },
            "nurture": {
                "greeting": "I hope you're doing well in your property search",
                "cta": "Feel free to reach out when you're ready to take the next step.",
                "urgency": "No pressure - I'm here when you need me.",
            },
        }

        variation = content_variations.get(variant, content_variations["nurture"])

        # Replace template placeholders
        content = template
        for placeholder, replacement in variation.items():
            content = content.replace(f"{{{{{placeholder}}}}}", replacement)

        # Replace lead data variables
        for key, value in variables.items():
            content = content.replace(f"{{{{{key}}}}}", str(value))

        return content

    async def _calculate_personalization_score(self, content: str, lead_data: Dict[str, Any]) -> float:
        """Calculate how personalized the content is"""

        score = 0.0
        total_possible = 0.0

        # Check for personal name usage
        if lead_data.get("first_name") and lead_data["first_name"].lower() in content.lower():
            score += 0.3
        total_possible += 0.3

        # Check for specific property interest
        if lead_data.get("property_interest") and lead_data["property_interest"].lower() in content.lower():
            score += 0.2
        total_possible += 0.2

        # Check for location reference
        if lead_data.get("location_preference") and lead_data["location_preference"].lower() in content.lower():
            score += 0.2
        total_possible += 0.2

        # Check for budget reference
        if lead_data.get("budget_range") and lead_data["budget_range"] in content:
            score += 0.2
        total_possible += 0.2

        # Check for lead source reference
        if lead_data.get("source") and lead_data["source"].lower() in content.lower():
            score += 0.1
        total_possible += 0.1

        return score / total_possible if total_possible > 0 else 0.0

    async def _apply_subject_pattern(self, subject: str, pattern: str) -> str:
        """Apply A/B test winning pattern to subject"""
        # This would implement learned patterns from A/B tests
        return subject


class SmartSMSAction(BaseAction):
    """Intelligent SMS action with timing optimization"""

    async def execute(self, lead_data: Dict[str, Any], execution_context: Dict[str, Any]) -> ActionResult:
        """Execute smart SMS sending"""
        try:
            message_template = self.config.get("message", "Hi {{first_name}}, checking in on your property search!")

            # Personalize message
            personalized_message = await self._personalize_sms(message_template, lead_data, execution_context)

            # Check timing appropriateness
            if not await self._is_appropriate_time_for_sms(lead_data):
                return ActionResult(
                    success=False,
                    message="SMS delayed - inappropriate timing",
                    delay_next=3600,  # Retry in 1 hour
                )

            # Prepare SMS data
            sms_data = {
                "to": lead_data.get("phone"),
                "message": personalized_message,
                "sender_id": self.config.get("sender_id", "RealEstate"),
            }

            # Execute SMS sending
            success = await self._send_sms(sms_data)

            if success:
                execution_context["variables"]["last_sms"] = {
                    "sent_at": datetime.now().isoformat(),
                    "message_length": len(personalized_message),
                }

                return ActionResult(
                    success=True, message=f"Smart SMS sent to {lead_data.get('phone')}", data={"sms_data": sms_data}
                )
            else:
                return ActionResult(success=False, message="Failed to send SMS", error_details="SMS service error")

        except Exception as e:
            logger.error(f"Smart SMS action failed: {e}")
            return ActionResult(success=False, message="Smart SMS action encountered an error", error_details=str(e))

    async def _personalize_sms(
        self, template: str, lead_data: Dict[str, Any], execution_context: Dict[str, Any]
    ) -> str:
        """Personalize SMS message"""

        message = template

        # Replace lead data variables
        for key, value in lead_data.items():
            message = message.replace(f"{{{{{key}}}}}", str(value))

        # Ensure SMS length limits
        if len(message) > 160:
            message = message[:157] + "..."

        return message

    async def _is_appropriate_time_for_sms(self, lead_data: Dict[str, Any]) -> bool:
        """Check if current time is appropriate for SMS"""
        now = datetime.now()
        hour = now.hour

        # Basic business hours check (can be enhanced with timezone detection)
        if hour < 8 or hour > 20:
            return False

        # Weekend restrictions
        if now.weekday() in [5, 6] and (hour < 10 or hour > 18):
            return False

        return True

    async def _send_sms(self, sms_data: Dict[str, Any]) -> bool:
        """Mock SMS sending implementation"""
        logger.info(f"Sending SMS to {sms_data['to']}: {sms_data['message'][:50]}...")
        await asyncio.sleep(0.1)
        return True


class LeadScoringAction(BaseAction):
    """Advanced lead scoring action"""

    async def execute(self, lead_data: Dict[str, Any], execution_context: Dict[str, Any]) -> ActionResult:
        """Execute lead scoring update"""
        try:
            # Calculate behavioral score
            behavioral_score = await self._calculate_behavioral_score(lead_data, execution_context)

            # Calculate demographic score
            demographic_score = await self._calculate_demographic_score(lead_data)

            # Calculate engagement score
            engagement_score = await self._calculate_engagement_score(lead_data, execution_context)

            # Combined score
            total_score = behavioral_score * 0.4 + demographic_score * 0.3 + engagement_score * 0.3

            # Update lead data
            lead_data["lead_score"] = round(total_score, 2)
            lead_data["score_breakdown"] = {
                "behavioral": behavioral_score,
                "demographic": demographic_score,
                "engagement": engagement_score,
            }
            lead_data["score_updated_at"] = datetime.now().isoformat()

            # Determine score category
            if total_score >= 80:
                category = "hot"
            elif total_score >= 60:
                category = "warm"
            elif total_score >= 40:
                category = "lukewarm"
            else:
                category = "cold"

            lead_data["lead_category"] = category

            return ActionResult(
                success=True,
                message=f"Lead score updated to {total_score} ({category})",
                data={"new_score": total_score, "category": category, "breakdown": lead_data["score_breakdown"]},
                next_actions=self._recommend_next_actions(category),
            )

        except Exception as e:
            logger.error(f"Lead scoring action failed: {e}")
            return ActionResult(success=False, message="Lead scoring encountered an error", error_details=str(e))

    async def _calculate_behavioral_score(self, lead_data: Dict[str, Any], execution_context: Dict[str, Any]) -> float:
        """Calculate behavioral score based on actions"""

        score = 0.0

        # Website behavior
        if "page_views" in lead_data:
            score += min(lead_data["page_views"] * 2, 20)

        if "time_on_site" in lead_data:
            score += min(lead_data["time_on_site"] / 60, 15)  # Minutes to score

        # Property interaction
        if "properties_viewed" in lead_data:
            score += min(lead_data["properties_viewed"] * 3, 25)

        if "favorites_saved" in lead_data:
            score += lead_data["favorites_saved"] * 5

        # Search behavior
        if "searches_performed" in lead_data:
            score += min(lead_data["searches_performed"] * 2, 15)

        # Form interactions
        if "forms_completed" in lead_data:
            score += lead_data["forms_completed"] * 10

        # Email/SMS responses
        execution_vars = execution_context.get("variables", {})
        if "email_opens" in execution_vars:
            score += execution_vars["email_opens"] * 2

        if "email_clicks" in execution_vars:
            score += execution_vars["email_clicks"] * 5

        return min(score, 100)

    async def _calculate_demographic_score(self, lead_data: Dict[str, Any]) -> float:
        """Calculate demographic score"""

        score = 0.0

        # Budget alignment
        budget_range = lead_data.get("budget_range", "")
        if budget_range:
            if "$500k+" in budget_range or "$400k-$500k" in budget_range:
                score += 30
            elif "$300k-$400k" in budget_range:
                score += 25
            elif "$200k-$300k" in budget_range:
                score += 20
            else:
                score += 10

        # Location preference specificity
        location = lead_data.get("location_preference", "")
        if location:
            # More specific location = higher intent
            if "," in location:  # City, State
                score += 20
            elif len(location) > 5:
                score += 15
            else:
                score += 10

        # Contact information completeness
        if lead_data.get("phone"):
            score += 15
        if lead_data.get("email"):
            score += 10
        if lead_data.get("address"):
            score += 10

        # Timeline urgency
        timeline = lead_data.get("timeline", "").lower()
        if "asap" in timeline or "immediately" in timeline:
            score += 20
        elif "30 days" in timeline or "month" in timeline:
            score += 15
        elif "90 days" in timeline:
            score += 10

        # Property type specificity
        property_type = lead_data.get("property_type", "")
        if property_type:
            score += 10

        return min(score, 100)

    async def _calculate_engagement_score(self, lead_data: Dict[str, Any], execution_context: Dict[str, Any]) -> float:
        """Calculate engagement score"""

        score = 0.0
        execution_vars = execution_context.get("variables", {})

        # Response to communications
        if "email_replied" in execution_vars:
            score += 25

        if "phone_answered" in execution_vars:
            score += 30

        if "sms_replied" in execution_vars:
            score += 20

        # Scheduled appointments
        if "appointment_scheduled" in execution_vars:
            score += 40

        if "appointment_attended" in execution_vars:
            score += 50

        # Social media engagement
        if "social_follows" in lead_data:
            score += lead_data["social_follows"] * 5

        # Referral activity
        if "referrals_made" in lead_data:
            score += lead_data["referrals_made"] * 15

        # Recent activity
        last_activity = lead_data.get("last_activity_date")
        if last_activity:
            days_since = (datetime.now() - datetime.fromisoformat(last_activity)).days
            if days_since <= 1:
                score += 15
            elif days_since <= 7:
                score += 10
            elif days_since <= 30:
                score += 5

        return min(score, 100)

    def _recommend_next_actions(self, category: str) -> List[str]:
        """Recommend next workflow actions based on score"""

        recommendations = {
            "hot": ["schedule_call", "send_priority_properties", "assign_top_agent"],
            "warm": ["send_targeted_email", "schedule_callback", "send_market_update"],
            "lukewarm": ["send_nurture_sequence", "add_to_newsletter", "social_media_follow"],
            "cold": ["add_to_long_term_nurture", "quarterly_check_in"],
        }

        return recommendations.get(category, [])


class PropertyMatchingAction(BaseAction):
    """Intelligent property matching action"""

    async def execute(self, lead_data: Dict[str, Any], execution_context: Dict[str, Any]) -> ActionResult:
        """Execute property matching"""
        try:
            # Extract matching criteria
            criteria = await self._extract_matching_criteria(lead_data)

            # Find matching properties
            matches = await self._find_property_matches(criteria)

            # Score and rank matches
            ranked_matches = await self._rank_matches(matches, criteria, lead_data)

            # Prepare property recommendations
            recommendations = await self._prepare_recommendations(ranked_matches, lead_data)

            # Update execution context
            execution_context["variables"]["property_matches"] = {
                "count": len(ranked_matches),
                "top_match_score": ranked_matches[0]["match_score"] if ranked_matches else 0,
                "generated_at": datetime.now().isoformat(),
            }

            return ActionResult(
                success=True,
                message=f"Found {len(ranked_matches)} property matches",
                data={"matches": ranked_matches, "recommendations": recommendations, "criteria": criteria},
                next_actions=["send_property_recommendations"] if ranked_matches else [],
            )

        except Exception as e:
            logger.error(f"Property matching action failed: {e}")
            return ActionResult(success=False, message="Property matching encountered an error", error_details=str(e))

    async def _extract_matching_criteria(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract property matching criteria from lead data"""

        criteria = {
            "budget_min": 0,
            "budget_max": float("inf"),
            "location": [],
            "property_type": [],
            "bedrooms": None,
            "bathrooms": None,
            "min_sqft": None,
            "max_sqft": None,
            "features": [],
            "must_haves": [],
            "nice_to_haves": [],
        }

        # Parse budget range
        budget_range = lead_data.get("budget_range", "")
        if budget_range:
            # Example: "$200k-$300k" -> min: 200000, max: 300000
            budget_match = re.findall(r"\$(\d+)k", budget_range)
            if len(budget_match) >= 2:
                criteria["budget_min"] = int(budget_match[0]) * 1000
                criteria["budget_max"] = int(budget_match[1]) * 1000
            elif len(budget_match) == 1:
                if "+" in budget_range:
                    criteria["budget_min"] = int(budget_match[0]) * 1000
                else:
                    criteria["budget_max"] = int(budget_match[0]) * 1000

        # Location preferences
        location_pref = lead_data.get("location_preference", "")
        if location_pref:
            criteria["location"] = [loc.strip() for loc in location_pref.split(",")]

        # Property type
        property_type = lead_data.get("property_type", "")
        if property_type:
            criteria["property_type"] = [property_type]

        # Specific requirements
        if "bedrooms" in lead_data:
            criteria["bedrooms"] = lead_data["bedrooms"]

        if "bathrooms" in lead_data:
            criteria["bathrooms"] = lead_data["bathrooms"]

        # Parse free-text requirements
        requirements = lead_data.get("requirements", "")
        if requirements:
            # Simple keyword extraction
            if "garage" in requirements.lower():
                criteria["must_haves"].append("garage")
            if "pool" in requirements.lower():
                criteria["nice_to_haves"].append("pool")
            if "garden" in requirements.lower():
                criteria["nice_to_haves"].append("garden")

        return criteria

    async def _find_property_matches(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find properties matching criteria (mock implementation)"""

        # Mock property database
        mock_properties = [
            {
                "id": "prop_1",
                "address": "123 Main St, Austin, TX",
                "price": 275000,
                "bedrooms": 3,
                "bathrooms": 2,
                "sqft": 1800,
                "property_type": "Single Family",
                "features": ["garage", "garden"],
                "location": "Austin",
                "listed_date": "2024-01-01",
                "agent_id": "agent_1",
            },
            {
                "id": "prop_2",
                "address": "456 Oak Ave, Austin, TX",
                "price": 320000,
                "bedrooms": 4,
                "bathrooms": 3,
                "sqft": 2200,
                "property_type": "Single Family",
                "features": ["garage", "pool"],
                "location": "Austin",
                "listed_date": "2024-01-05",
                "agent_id": "agent_2",
            },
            {
                "id": "prop_3",
                "address": "789 Pine Rd, Austin, TX",
                "price": 180000,
                "bedrooms": 2,
                "bathrooms": 2,
                "sqft": 1200,
                "property_type": "Condo",
                "features": ["balcony"],
                "location": "Austin",
                "listed_date": "2024-01-10",
                "agent_id": "agent_1",
            },
        ]

        matches = []

        for property in mock_properties:
            # Budget filter
            if property["price"] >= criteria["budget_min"] and property["price"] <= criteria["budget_max"]:
                # Location filter
                if not criteria["location"] or any(
                    loc.lower() in property["location"].lower() for loc in criteria["location"]
                ):
                    matches.append(property)

        return matches

    async def _rank_matches(
        self, matches: List[Dict[str, Any]], criteria: Dict[str, Any], lead_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Score and rank property matches"""

        ranked_matches = []

        for property in matches:
            score = await self._calculate_match_score(property, criteria, lead_data)

            property_with_score = property.copy()
            property_with_score["match_score"] = score
            property_with_score["match_reasons"] = await self._get_match_reasons(property, criteria)

            ranked_matches.append(property_with_score)

        # Sort by match score descending
        ranked_matches.sort(key=lambda x: x["match_score"], reverse=True)

        return ranked_matches

    async def _calculate_match_score(
        self, property: Dict[str, Any], criteria: Dict[str, Any], lead_data: Dict[str, Any]
    ) -> float:
        """Calculate match score for a property"""

        score = 0.0

        # Budget alignment (0-30 points)
        property_price = property["price"]
        if criteria["budget_min"] <= property_price <= criteria["budget_max"]:
            # Perfect budget match
            budget_range = criteria["budget_max"] - criteria["budget_min"]
            if budget_range > 0:
                # Score based on how close to budget center
                budget_center = (criteria["budget_min"] + criteria["budget_max"]) / 2
                distance_from_center = abs(property_price - budget_center)
                budget_score = 30 * (1 - (distance_from_center / (budget_range / 2)))
                score += max(budget_score, 15)  # Minimum 15 points if in range
            else:
                score += 30
        else:
            # Penalty for being outside budget
            score -= 20

        # Bedroom match (0-20 points)
        if criteria.get("bedrooms"):
            if property["bedrooms"] == criteria["bedrooms"]:
                score += 20
            elif abs(property["bedrooms"] - criteria["bedrooms"]) == 1:
                score += 10

        # Bathroom match (0-15 points)
        if criteria.get("bathrooms"):
            if property["bathrooms"] == criteria["bathrooms"]:
                score += 15
            elif abs(property["bathrooms"] - criteria["bathrooms"]) <= 0.5:
                score += 10

        # Must-have features (0-25 points)
        must_haves = criteria.get("must_haves", [])
        property_features = property.get("features", [])

        for must_have in must_haves:
            if must_have in property_features:
                score += 25 / len(must_haves) if must_haves else 0

        # Nice-to-have features (0-10 points)
        nice_to_haves = criteria.get("nice_to_haves", [])
        for nice_to_have in nice_to_haves:
            if nice_to_have in property_features:
                score += 10 / len(nice_to_haves) if nice_to_haves else 0

        # Property type match (0-10 points)
        if criteria.get("property_type") and property.get("property_type") in criteria["property_type"]:
            score += 10

        return min(score, 100)

    async def _get_match_reasons(self, property: Dict[str, Any], criteria: Dict[str, Any]) -> List[str]:
        """Get reasons why property matches"""

        reasons = []

        # Budget
        if criteria["budget_min"] <= property["price"] <= criteria["budget_max"]:
            reasons.append(f"Within budget range")

        # Bedrooms
        if criteria.get("bedrooms") and property["bedrooms"] == criteria["bedrooms"]:
            reasons.append(f"Exact bedroom match ({property['bedrooms']} bedrooms)")

        # Features
        property_features = property.get("features", [])
        for feature in criteria.get("must_haves", []):
            if feature in property_features:
                reasons.append(f"Has required feature: {feature}")

        for feature in criteria.get("nice_to_haves", []):
            if feature in property_features:
                reasons.append(f"Has desired feature: {feature}")

        # Location
        if criteria.get("location"):
            for loc in criteria["location"]:
                if loc.lower() in property.get("location", "").lower():
                    reasons.append(f"In preferred location: {loc}")

        return reasons

    async def _prepare_recommendations(
        self, ranked_matches: List[Dict[str, Any]], lead_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare property recommendations"""

        if not ranked_matches:
            return {
                "message": "No properties found matching your criteria",
                "suggestions": ["Expand your search area", "Adjust your budget range"],
            }

        top_match = ranked_matches[0]

        message = f"Found {len(ranked_matches)} properties that match your criteria. "
        message += f"The top match at {top_match['address']} scores {top_match['match_score']:.0f}% "
        message += f"and is priced at ${top_match['price']:,}."

        return {
            "message": message,
            "top_properties": ranked_matches[:3],  # Top 3 matches
            "total_matches": len(ranked_matches),
            "avg_match_score": sum(p["match_score"] for p in ranked_matches) / len(ranked_matches),
        }


# Action Registry
class ActionRegistry:
    """Registry for all available workflow actions"""

    def __init__(self):
        self.actions: Dict[str, type] = {
            "smart_email": SmartEmailAction,
            "smart_sms": SmartSMSAction,
            "lead_scoring": LeadScoringAction,
            "property_matching": PropertyMatchingAction,
        }

    def register_action(self, action_type: str, action_class: type):
        """Register a new action type"""
        self.actions[action_type] = action_class

    def create_action(self, action_type: str, action_id: str, config: Dict[str, Any]) -> BaseAction:
        """Create action instance"""
        if action_type not in self.actions:
            raise ValueError(f"Unknown action type: {action_type}")

        return self.actions[action_type](action_id, config)

    def get_available_actions(self) -> List[str]:
        """Get list of available action types"""
        return list(self.actions.keys())


# Global registry instance
action_registry = ActionRegistry()
