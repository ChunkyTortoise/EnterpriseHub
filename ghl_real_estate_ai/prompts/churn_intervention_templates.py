"""
Churn Intervention Templates - Personalized Messaging for Automated Interventions

This module contains template generators for various intervention types with
personalization based on churn risk factors, lead preferences, and behavioral patterns.

Template Categories:
- Critical Risk Templates (immediate action required)
- High Risk Templates (urgent follow-up needed)
- Medium Risk Templates (nurture and re-engage)
- Low Risk Templates (standard engagement)

Each template includes:
- Subject line optimization
- Personalized content based on risk factors
- Clear call-to-action
- Urgency indicators where appropriate

Author: EnterpriseHub AI
Last Updated: 2026-01-09
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import random

class MessageTone(Enum):
    """Message tone variations for A/B testing"""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    URGENT = "urgent"
    CONSULTATIVE = "consultative"

class InterventionTemplate:
    """Base class for intervention message templates"""

    @staticmethod
    def personalize_template(template: str, personalization_data: Dict[str, Any]) -> str:
        """Apply personalization data to template securely"""
        from collections import defaultdict
        
        # Use a defaultdict to handle missing keys gracefully
        safe_data = defaultdict(lambda: "[DATA_MISSING]")
        safe_data.update(personalization_data)
        
        try:
            return template.format_map(safe_data)
        except Exception as e:
            # Fallback for complex format strings
            logger.error(f"Error personalizing template: {e}")
            return template

class CriticalRiskTemplates:
    """Templates for critical churn risk (80-100% probability)"""

    @staticmethod
    def agent_escalation_alert(personalization_data: Dict[str, Any]) -> Dict[str, str]:
        """Agent escalation alert template"""
        templates = {
            "subject": "🚨 CRITICAL: High Churn Risk Lead - Immediate Action Required",
            "body": """
URGENT LEAD ALERT: {lead_name}

Churn Risk Score: {risk_score} (CRITICAL)
Last Interaction: {days_since_interaction} days ago
Primary Risk Factor: {top_risk_factor}

IMMEDIATE ACTIONS REQUIRED:
• Call within 1 hour
• Offer emergency consultation
• Consider incentive package
• Escalate to senior agent if needed

Lead Preferences:
• Budget: {budget_range}
• Locations: {preferred_locations}
• Last Property Viewed: {last_property_viewed}

Recommended Talking Points:
{recommended_actions}

This lead requires personal attention to prevent churn.
""",
            "sms": "URGENT: {lead_name} showing critical churn risk. Call immediately - last interaction {days_since_interaction} days ago. Escalation required."
        }

        return {
            key: InterventionTemplate.personalize_template(template, personalization_data)
            for key, template in templates.items()
        }

    @staticmethod
    def incentive_offer_email(personalization_data: Dict[str, Any]) -> Dict[str, str]:
        """Critical intervention with incentive offer"""
        subject_variations = [
            "⏰ Limited Time: Exclusive Benefits for Your Home Search",
            "🏠 Special Offer: Let's Fast-Track Your Home Purchase",
            "💰 Exclusive: Closing Cost Assistance Available Now"
        ]

        template = """
Hi {lead_name},

I noticed it's been {days_since_interaction} days since we last connected about your home search. I want to make sure we're providing the best possible service for your journey to homeownership.

**EXCLUSIVE OPPORTUNITY - LIMITED TIME**
To help accelerate your home search, I'm pleased to offer:
• 5% assistance with closing costs
• Priority access to new listings in {preferred_locations}
• Complimentary consultation with our top mortgage specialist
• Fast-track property viewing appointments

Given your interest in {property_types} properties with a budget of {budget_range}, I believe this assistance could make a significant difference in securing your dream home.

{urgency_message}

Can we schedule a quick 15-minute call today to discuss how we can better support your home buying goals?

Best regards,
Your Real Estate Team

P.S. This exclusive offer expires in 7 days. Let's connect soon to ensure you don't miss out.

[Schedule Call Now] [View Latest Properties] [Contact Me Directly]
"""

        return {
            "subject": random.choice(subject_variations),
            "body": InterventionTemplate.personalize_template(template, personalization_data)
        }

    @staticmethod
    def emergency_consultation_offer(personalization_data: Dict[str, Any]) -> Dict[str, str]:
        """Emergency consultation scheduling template"""
        template = """
Hi {lead_name},

I hope this message finds you well. I've been thinking about your home search and want to ensure we're on track to help you find the perfect property.

**PRIORITY CONSULTATION AVAILABLE**

I'm setting aside time this week for a comprehensive consultation to:
✓ Review your current search criteria and preferences
✓ Analyze market opportunities in {preferred_locations}
✓ Discuss any challenges or concerns you might have
✓ Create a personalized action plan for the next 30 days

This won't cost you anything - it's my commitment to ensuring your success.

Available times:
• Today after 2 PM
• Tomorrow morning 9 AM - 12 PM
• This weekend (flexible timing)

With the current market conditions, timing is crucial. Let's make sure you're positioned to act quickly when the right property appears.

Can I reserve 30 minutes on your calendar?

Sincerely,
[Agent Name]

[Book Consultation] [Call Me Now] [Text Me Back]
"""

        return {
            "subject": f"Priority Consultation Available - {personalization_data.get('lead_name', 'Valued Client')}",
            "body": InterventionTemplate.personalize_template(template, personalization_data)
        }

class HighRiskTemplates:
    """Templates for high churn risk (60-80% probability)"""

    @staticmethod
    def urgent_followup_email(personalization_data: Dict[str, Any]) -> Dict[str, str]:
        """Urgent follow-up email template"""
        subject_variations = [
            "Quick Check-In: How's Your Home Search Going?",
            "Updates on {preferred_locations} Properties",
            "Haven't Heard From You - Everything OK?",
            "New Opportunities in Your Price Range"
        ]

        template = """
Hi {lead_name},

I hope you're doing well! I realized it's been a while since we last spoke about your home search, and I wanted to check in to see how things are progressing.

**What's Been Happening:**
• {days_since_interaction} days since our last conversation
• New properties have come on the market in {preferred_locations}
• Interest rates have [improved/remained stable]
• Several properties matching your criteria are getting quick offers

**I'm Here to Help:**
I know the home buying process can feel overwhelming sometimes. Whether you're:
- Still actively searching
- Taking a brief pause
- Facing any unexpected challenges
- Need help with financing or next steps

...I'm here to support you every step of the way.

**Next Steps:**
Would you like to hop on a brief call this week? I can share:
• New listings that match your {property_types} preferences
• Market insights for {budget_range} range
• Updated financing options
• Answers to any questions you might have

No pressure - just want to make sure you have all the support you need.

Looking forward to hearing from you!

Best regards,
[Agent Name]

[Schedule Call] [View New Properties] [Send Quick Update]
"""

        return {
            "subject": InterventionTemplate.personalize_template(random.choice(subject_variations), personalization_data),
            "body": InterventionTemplate.personalize_template(template, personalization_data)
        }

    @staticmethod
    def sms_urgent_callback(personalization_data: Dict[str, Any]) -> Dict[str, str]:
        """SMS template for urgent callback request"""
        sms_variations = [
            "Hi {lead_name}! Haven't connected in {days_since_interaction} days. Found some great properties in {preferred_locations}. Quick call today?",
            "Hey {lead_name}! Checking in on your home search. Have updates that might interest you. Good time to chat?",
            "Hi {lead_name}! Market's moving fast in your area. Can we touch base about your search? 15 min call?",
            "{lead_name}, wanted to ensure you're getting the support you need. Available for a quick call today?"
        ]

        template = random.choice(sms_variations)

        return {
            "subject": "Follow-up SMS",
            "body": InterventionTemplate.personalize_template(template, personalization_data)
        }

    @staticmethod
    def property_alert_reengagement(personalization_data: Dict[str, Any]) -> Dict[str, str]:
        """Property alert template to re-engage interest"""
        template = """
🏠 NEW PROPERTY ALERT: Perfect Match Found!

Hi {lead_name},

Exciting news! A property just hit the market that matches your search criteria perfectly:

**Property Highlights:**
• Location: {preferred_locations}
• Type: {property_types}
• Price Range: Fits your {budget_range} budget
• Features: [Key features that match preferences]

**Why This Could Be "The One":**
Based on your previous searches and saved favorites, this property checks all your important boxes. Properties like this in your preferred area typically receive multiple offers within 48-72 hours.

**Market Context:**
The {preferred_locations} market has been competitive lately, with similar properties averaging 3-5 showings in the first weekend. Given your timeline and preferences, I wanted to give you first priority.

**Next Steps:**
I can arrange a viewing as early as today or tomorrow morning. If you'd like, I can also:
• Provide detailed property analysis
• Prepare comparable market data
• Discuss offering strategy if you're interested

Shall I schedule a showing?

Best,
[Agent Name]

[View Full Details] [Schedule Showing] [Call Me About This Property]

P.S. I'm also tracking 2 other properties that should be listing soon in your area. Let's connect to discuss your full range of options.
"""

        return {
            "subject": f"🏠 Perfect Match Found in {personalization_data.get('preferred_locations', 'Your Area')} - View Today?",
            "body": InterventionTemplate.personalize_template(template, personalization_data)
        }

class MediumRiskTemplates:
    """Templates for medium churn risk (30-60% probability)"""

    @staticmethod
    def nurture_reengagement_email(personalization_data: Dict[str, Any]) -> Dict[str, str]:
        """Nurture email to maintain engagement"""
        subject_variations = [
            "Your Weekly Market Update - {preferred_locations}",
            "3 Things Happening in Your Local Market",
            "Market Insights: What Buyers Should Know This Week",
            "Quick Update on {preferred_locations} Market Activity"
        ]

        template = """
Hi {lead_name},

Hope you're having a great week! I wanted to share some insights about the {preferred_locations} market that might be relevant to your home search.

**This Week's Market Highlights:**

📊 **Market Stats:**
• Average days on market: X days (down from last month)
• Price trends for {property_types}: [Stable/Increasing/Decreasing]
• Inventory levels: X properties available in your price range

🏠 **Buyer Opportunities:**
• Interest rates holding steady at competitive levels
• Several properties reduced prices in {preferred_locations}
• New construction opportunities available

💡 **Market Insight:**
For buyers in your price range ({budget_range}), this could be an excellent time to make moves. Seller motivation is increasing as we head into [season], creating opportunities for better negotiations.

**Properties to Watch:**
I'm keeping an eye on several listings that might interest you:
• [Property type] properties coming to market next week
• Price reductions in your preferred neighborhoods
• New developments offering move-in incentives

**Your Home Search:**
No pressure on timing - everyone's journey is different! When you're ready to take next steps, I'm here to help with:
• Property viewings and analysis
• Market timing strategies
• Financing option reviews
• Negotiation support

Feel free to reach out anytime with questions or when you'd like to see something specific.

Best regards,
[Agent Name]

[View Current Listings] [Schedule Market Consultation] [Update My Preferences]

P.S. If your search criteria have changed or you'd like to pause updates temporarily, just let me know!
"""

        return {
            "subject": InterventionTemplate.personalize_template(random.choice(subject_variations), personalization_data),
            "body": InterventionTemplate.personalize_template(template, personalization_data)
        }

    @staticmethod
    def educational_content_email(personalization_data: Dict[str, Any]) -> Dict[str, str]:
        """Educational content email template"""
        template = """
Hi {lead_name},

I thought you might find this helpful for your home buying journey!

**📚 This Week's Educational Focus: [Topic Based on Journey Stage]**

Whether you're just starting to explore or getting ready to make an offer, here are some insights that could be valuable:

**Key Points:**
• Financing tip: [Relevant advice based on their stage]
• Market timing: [Current conditions affecting their search]
• Negotiation strategy: [Relevant to their price range and area]

**Resources for You:**
🔗 First-Time Buyer Guide (if applicable)
🔗 Market Analysis: {preferred_locations}
🔗 Financing Calculator
🔗 Moving Timeline Checklist

**Personal Insights for Your Search:**
Based on your interest in {property_types} properties in {preferred_locations}, here's what I recommend focusing on:

1. [Specific advice based on their preferences]
2. [Market timing consideration]
3. [Preparation steps]

**Questions I Often Get:**
- "What's the current market timeline for properties like mine?"
- "How do I know if I'm getting a fair deal?"
- "What should I expect during the closing process?"

Happy to answer these or any other questions you might have!

Take care,
[Agent Name]

[Read Full Market Guide] [Ask a Question] [Schedule Consultation]
"""

        return {
            "subject": f"Home Buying Insights for {personalization_data.get('lead_name', 'You')}",
            "body": InterventionTemplate.personalize_template(template, personalization_data)
        }

    @staticmethod
    def preference_update_request(personalization_data: Dict[str, Any]) -> Dict[str, str]:
        """Template requesting preference updates"""
        template = """
Hi {lead_name},

Quick question for you!

It's been {days_since_interaction} days since we last connected, and I want to make sure I'm sending you the most relevant property updates and market information.

**Current Preferences on File:**
• Budget Range: {budget_range}
• Preferred Locations: {preferred_locations}
• Property Types: {property_types}
• Key Features: [Previous requirements]

**Quick Check-In:**
• Are these preferences still accurate?
• Has your timeline changed at all?
• Any new features or areas you'd like to explore?
• Different price range considerations?

**Market Update:**
The good news is that we're seeing some great opportunities in your price range, and I want to make sure you're seeing the properties that best match what you're looking for.

**30-Second Update:**
Could you take just 30 seconds to let me know if anything has changed? You can:

1. Reply "All good" if everything's the same
2. Call/text me any updates
3. Click below to update preferences online

No pressure if you're taking a break from actively searching - just want to ensure I'm providing value when you're ready!

Thanks!
[Agent Name]

[Update Preferences] [Schedule Quick Call] [Email Me Changes]
"""

        return {
            "subject": f"Quick Preference Check - {personalization_data.get('lead_name', 'Valued Client')}",
            "body": InterventionTemplate.personalize_template(template, personalization_data)
        }

class LowRiskTemplates:
    """Templates for low churn risk (0-30% probability)"""

    @staticmethod
    def standard_nurture_email(personalization_data: Dict[str, Any]) -> Dict[str, str]:
        """Standard nurture email for engaged leads"""
        template = """
Hi {lead_name},

Hope you're doing well! Just a friendly update on your home search progress.

**This Week's Highlights:**
• X new properties listed in {preferred_locations}
• Market activity remains [strong/steady/competitive]
• Several properties in your {budget_range} range available

**For Your Consideration:**
I've saved a few properties that caught my attention for your search:

🏠 **Featured Property:**
[Property description that matches their criteria]

**Market Snapshot:**
{preferred_locations} continues to be an active market with good opportunities for qualified buyers. Your {property_types} search criteria puts you in a favorable position.

**Next Steps:**
When you're ready:
• Schedule property viewings
• Discuss current market opportunities
• Review any new requirements or preferences

No rush - just keeping you informed as your search evolves!

Best regards,
[Agent Name]

[View New Listings] [Schedule Showing] [Market Questions?]
"""

        return {
            "subject": f"Weekly Update - {personalization_data.get('preferred_locations', 'Your Area')} Market",
            "body": InterventionTemplate.personalize_template(template, personalization_data)
        }

    @staticmethod
    def success_story_email(personalization_data: Dict[str, Any]) -> Dict[str, str]:
        """Success story template for inspiration"""
        template = """
Hi {lead_name},

I wanted to share a quick success story that reminded me of your home search!

**Recent Success: [Similar Client Story]**
Last week, I helped a client find their perfect home in {preferred_locations}. Like you, they were looking for {property_types} properties in the {budget_range} range.

**What Made the Difference:**
• Staying informed about market conditions
• Being prepared with financing pre-approval
• Acting quickly on the right opportunity
• Having a clear understanding of priorities

**The Result:**
They found their dream home, negotiated a great deal, and are now happily settled in their new neighborhood!

**Your Journey:**
Everyone's timeline is different, and I know you'll find the right property when the timing is perfect for you. I'm here to support you whether you're actively searching now or planning for the future.

**Current Opportunities:**
If you'd like to see what's currently available in your search area, I'm happy to send updated listings that match your criteria.

Feel free to reach out anytime!

Best,
[Agent Name]

[See Current Listings] [Hear More Success Stories] [Schedule Chat]
"""

        return {
            "subject": f"Success Story from {personalization_data.get('preferred_locations', 'Your Area')}",
            "body": InterventionTemplate.personalize_template(template, personalization_data)
        }

class TemplateSelector:
    """Selects appropriate templates based on risk factors and personalization"""

    @staticmethod
    def select_template(risk_tier: str, intervention_type: str,
                       personalization_data: Dict[str, Any],
                       tone: MessageTone = MessageTone.PROFESSIONAL) -> Dict[str, str]:
        """
        Select appropriate template based on risk tier and intervention type

        Args:
            risk_tier: Risk tier (critical, high, medium, low)
            intervention_type: Type of intervention needed
            personalization_data: Data for personalization
            tone: Message tone preference

        Returns:
            Dict with subject and body templates
        """

        # Template mapping based on risk tier and intervention type
        template_map = {
            ("critical", "agent_escalation"): CriticalRiskTemplates.agent_escalation_alert,
            ("critical", "incentive_offer"): CriticalRiskTemplates.incentive_offer_email,
            ("critical", "personal_consultation"): CriticalRiskTemplates.emergency_consultation_offer,

            ("high", "email_reengagement"): HighRiskTemplates.urgent_followup_email,
            ("high", "sms_urgent"): HighRiskTemplates.sms_urgent_callback,
            ("high", "property_alert"): HighRiskTemplates.property_alert_reengagement,
            ("high", "phone_callback"): HighRiskTemplates.urgent_followup_email,

            ("medium", "email_reengagement"): MediumRiskTemplates.nurture_reengagement_email,
            ("medium", "market_update"): MediumRiskTemplates.educational_content_email,
            ("medium", "preference_update"): MediumRiskTemplates.preference_update_request,

            ("low", "email_reengagement"): LowRiskTemplates.standard_nurture_email,
            ("low", "success_story"): LowRiskTemplates.success_story_email,
        }

        # Find matching template
        template_function = template_map.get((risk_tier.lower(), intervention_type.lower()))

        if template_function:
            return template_function(personalization_data)
        else:
            # Default fallback template
            return TemplateSelector._get_fallback_template(personalization_data)

    @staticmethod
    def _get_fallback_template(personalization_data: Dict[str, Any]) -> Dict[str, str]:
        """Fallback template when specific template not found"""
        template = """
Hi {lead_name},

I wanted to reach out and see how your home search is progressing.

If there's anything I can help with or any questions you have about the current market, please don't hesitate to reach out.

Looking forward to hearing from you!

Best regards,
[Agent Name]

[Contact Me] [View Properties] [Market Update]
"""

        return {
            "subject": f"Following up on your home search - {personalization_data.get('lead_name', 'Valued Client')}",
            "body": InterventionTemplate.personalize_template(template, personalization_data)
        }

    @staticmethod
    def get_available_templates() -> Dict[str, List[str]]:
        """Get list of available templates by risk tier"""
        return {
            "critical": ["agent_escalation", "incentive_offer", "personal_consultation"],
            "high": ["email_reengagement", "sms_urgent", "property_alert", "phone_callback"],
            "medium": ["email_reengagement", "market_update", "preference_update"],
            "low": ["email_reengagement", "success_story"]
        }

# A/B Testing Support
class ABTestTemplates:
    """A/B test variations for template optimization"""

    @staticmethod
    def get_variant_template(base_template: Dict[str, str], variant: str) -> Dict[str, str]:
        """Get A/B test variant of base template"""
        variants = {
            "urgent": ABTestTemplates._apply_urgency_variant,
            "friendly": ABTestTemplates._apply_friendly_variant,
            "professional": ABTestTemplates._apply_professional_variant,
            "value_focused": ABTestTemplates._apply_value_variant
        }

        variant_function = variants.get(variant.lower())
        if variant_function:
            return variant_function(base_template)
        return base_template

    @staticmethod
    def _apply_urgency_variant(template: Dict[str, str]) -> Dict[str, str]:
        """Apply urgency-focused modifications"""
        # Add urgency indicators to subject and body
        template["subject"] = f"⏰ URGENT: {template['subject']}"
        template["body"] = template["body"].replace(
            "Best regards,",
            "Time is of the essence - let's connect soon!\n\nBest regards,"
        )
        return template

    @staticmethod
    def _apply_friendly_variant(template: Dict[str, str]) -> Dict[str, str]:
        """Apply friendly tone modifications"""
        # Make language more casual and friendly
        template["body"] = template["body"].replace("I hope this message finds you well.", "Hope you're doing great!")
        template["body"] = template["body"].replace("Best regards,", "Looking forward to hearing from you!\n\nCheers,")
        return template

    @staticmethod
    def _apply_professional_variant(template: Dict[str, str]) -> Dict[str, str]:
        """Apply professional tone modifications"""
        # Keep formal professional tone
        return template

    @staticmethod
    def _apply_value_variant(template: Dict[str, str]) -> Dict[str, str]:
        """Apply value-proposition focused modifications"""
        # Emphasize value and benefits
        template["subject"] = f"💰 Value Alert: {template['subject']}"
        return template

# Example usage
if __name__ == "__main__":
    # Sample personalization data
    sample_data = {
        "lead_name": "Sarah Johnson",
        "risk_score": "85%",
        "risk_tier": "critical",
        "top_risk_factor": "days_since_last_interaction",
        "days_since_interaction": "12",
        "preferred_locations": "Austin, TX",
        "budget_range": "$350K - $450K",
        "property_types": "Single-family homes",
        "last_property_viewed": "3-bedroom home in Cedar Park",
        "recommended_actions": ["Immediate phone call", "Property viewing"],
        "urgency_message": "The market is moving quickly in your area",
    }

    # Test template selection
    template = TemplateSelector.select_template(
        risk_tier="critical",
        intervention_type="incentive_offer",
        personalization_data=sample_data
    )

    print("Generated Template:")
    print(f"Subject: {template['subject']}")
    print(f"Body: {template['body'][:500]}...")  # First 500 characters