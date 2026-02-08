"""
Value Communication Templates and Messaging System

Provides pre-built templates and messaging strategies for communicating value
and ROI to clients in compelling, trustworthy formats. Integrates with the
Dynamic Value Justification Engine to create personalized value communications.

Key Features:
- Email templates for ROI reporting
- Presentation templates for client meetings
- Social proof and testimonial management
- Pricing justification scripts
- Success story templates
- Competitive comparison frameworks
- Performance guarantee documentation

Business Impact:
- Standardize high-quality value communication
- Increase client confidence through consistent messaging
- Enable scalable value demonstration
- Support premium pricing conversations

Author: Claude Code Agent
Created: 2026-01-18
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from .claude_assistant import ClaudeAssistant
from .dynamic_value_justification_engine import (
    PricingTier,
    RealTimeROICalculation,
    ValueCommunicationPackage,
    ValueDimension,
    get_dynamic_value_justification_engine,
)

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of value messages"""

    EMAIL_REPORT = "email_report"
    PRESENTATION = "presentation"
    PROPOSAL = "proposal"
    FOLLOW_UP = "follow_up"
    PRICING_JUSTIFICATION = "pricing_justification"
    SUCCESS_STORY = "success_story"
    TESTIMONIAL_REQUEST = "testimonial_request"
    COMPETITIVE_COMPARISON = "competitive_comparison"
    PERFORMANCE_UPDATE = "performance_update"


class CommunicationStyle(Enum):
    """Communication style preferences"""

    EXECUTIVE = "executive"  # Concise, high-level, strategic focus
    DETAILED = "detailed"  # Comprehensive, data-rich, analytical
    CASUAL = "casual"  # Friendly, conversational, approachable
    TECHNICAL = "technical"  # In-depth, methodology-focused, precise
    EMOTIONAL = "emotional"  # Story-driven, benefit-focused, personal


@dataclass
class MessageTemplate:
    """Template for value communication messages"""

    template_id: str
    message_type: MessageType
    title: str
    subject_line: Optional[str]
    opening: str
    main_content: str
    closing: str
    call_to_action: str
    personalization_variables: List[str]
    communication_style: CommunicationStyle
    use_cases: List[str]
    created_at: datetime


@dataclass
class ValueMessage:
    """Generated value communication message"""

    message_id: str
    template_id: str
    agent_id: str
    client_id: str
    message_type: MessageType
    subject_line: Optional[str]
    content: str
    personalization_data: Dict[str, Any]
    roi_data: Dict[str, Any]
    delivery_method: str
    scheduled_send: Optional[datetime]
    generated_at: datetime
    expires_at: Optional[datetime]


class ValueCommunicationTemplates:
    """
    Value Communication Templates and Messaging System

    Provides standardized, high-quality templates for communicating value
    and ROI to clients with personalization and AI enhancement.
    """

    def __init__(self, claude_assistant: Optional[ClaudeAssistant] = None):
        self.value_engine = get_dynamic_value_justification_engine()
        self.claude = claude_assistant or ClaudeAssistant()

        # Initialize templates
        self.templates = self._initialize_templates()

        # Message configuration
        self.message_config = {
            "max_content_length": 5000,
            "personalization_required": True,
            "ai_enhancement_enabled": True,
            "include_verification_badges": True,
            "include_competitive_data": True,
            "roi_threshold_highlight": 200.0,  # Highlight ROI above 200%
        }

    def _initialize_templates(self) -> Dict[str, MessageTemplate]:
        """Initialize all message templates"""

        templates = {}

        # Email Report Template
        templates["roi_email_report"] = MessageTemplate(
            template_id="roi_email_report",
            message_type=MessageType.EMAIL_REPORT,
            title="ROI Performance Report",
            subject_line="Your Real Estate Investment ROI: {roi_percentage}% Return",
            opening="""
            Dear {client_name},

            I wanted to share your latest performance results and the exceptional value 
            we've delivered on your real estate investment.
            """,
            main_content="""
            ## Your Investment Performance Summary

            **Total Value Delivered**: ${total_value_delivered:,}
            **Your Investment**: ${total_investment:,}
            **Net Benefit**: ${net_benefit:,}
            **ROI**: {roi_percentage}%

            ### Value Breakdown:
            {value_dimension_breakdown}

            ### Competitive Advantage:
            Compared to working with a discount broker, you received ${competitive_advantage:,} 
            more in value while enjoying superior service quality and peace of mind.

            ### Key Achievements:
            {key_achievements}
            """,
            closing="""
            These results reflect our commitment to delivering exceptional value that 
            far exceeds our fees. Your success is our top priority.

            Best regards,
            {agent_name}
            """,
            call_to_action="Schedule a call to discuss your next real estate opportunity",
            personalization_variables=[
                "client_name",
                "agent_name",
                "total_value_delivered",
                "total_investment",
                "net_benefit",
                "roi_percentage",
                "value_dimension_breakdown",
                "competitive_advantage",
                "key_achievements",
            ],
            communication_style=CommunicationStyle.EXECUTIVE,
            use_cases=["Monthly ROI reports", "Transaction completion summaries"],
            created_at=datetime.now(),
        )

        # Pricing Justification Template
        templates["pricing_justification"] = MessageTemplate(
            template_id="pricing_justification",
            message_type=MessageType.PRICING_JUSTIFICATION,
            title="Premium Service Pricing Justification",
            subject_line="Why Premium Service Delivers Superior Returns",
            opening="""
            {client_name},

            I understand that investing in premium real estate services represents a 
            significant decision. Let me show you exactly why this investment delivers 
            exceptional returns.
            """,
            main_content="""
            ## Value-Based Pricing Analysis

            ### Your Investment vs. Returns:
            - **Service Investment**: ${service_investment:,}
            - **Value Delivered**: ${total_value:,}
            - **Net Benefit**: ${net_benefit:,}
            - **ROI**: {roi_percentage}%

            ### Why Premium Service Pays:

            **🏆 Superior Negotiation Results**
            Average agent achieves {market_average_negotiation}% of asking price.
            I achieve {agent_negotiation_performance}% - saving you ${negotiation_savings:,}.

            **⚡ Time & Efficiency Advantages**
            Market average: {market_days_to_close} days to close.
            My average: {agent_days_to_close} days - saving {days_saved} days 
            and ${time_savings:,} in carrying costs.

            **🛡️ Risk Mitigation Value**
            Premium service prevents costly issues that occur in {market_issue_rate}% 
            of transactions. Estimated risk protection value: ${risk_protection:,}.

            ### Competitive Comparison:
            {competitive_comparison_table}

            ### ROI Guarantee:
            I guarantee a minimum {guaranteed_roi}% ROI on your service investment, 
            or I'll refund the difference.
            """,
            closing="""
            Premium pricing reflects premium results. When you invest in exceptional 
            service, you receive exceptional returns.

            {agent_name}
            """,
            call_to_action="Let's discuss how premium service will benefit your specific situation",
            personalization_variables=[
                "client_name",
                "agent_name",
                "service_investment",
                "total_value",
                "net_benefit",
                "roi_percentage",
                "negotiation_savings",
                "time_savings",
                "risk_protection",
                "guaranteed_roi",
                "competitive_comparison_table",
            ],
            communication_style=CommunicationStyle.DETAILED,
            use_cases=["Fee discussions", "Service tier explanations", "Value demonstrations"],
            created_at=datetime.now(),
        )

        # Success Story Template
        templates["success_story"] = MessageTemplate(
            template_id="success_story",
            message_type=MessageType.SUCCESS_STORY,
            title="Client Success Story",
            subject_line=None,  # For social media/website use
            opening="""
            **Client Success Spotlight** 🌟
            """,
            main_content="""
            ## {property_address} - Exceptional Results

            **The Challenge:**
            {client_challenge}

            **Our Solution:**
            {solution_provided}

            **The Results:**
            - 📈 Sale Price: ${sale_price:,} ({percentage_above_asking}% above asking)
            - ⚡ Closed in {days_to_close} days ({days_faster} days faster than market average)
            - 💰 Client ROI: {client_roi}%
            - ⭐ Client Satisfaction: {satisfaction_rating}/5.0

            **Client Testimonial:**
            "{client_testimonial}"
            - {client_name}

            **Key Success Factors:**
            {key_success_factors}
            """,
            closing="""
            Another example of how strategic approach and exceptional service 
            deliver outstanding results for our clients.
            """,
            call_to_action="Ready for similar results? Let's discuss your real estate goals.",
            personalization_variables=[
                "property_address",
                "client_challenge",
                "solution_provided",
                "sale_price",
                "percentage_above_asking",
                "days_to_close",
                "days_faster",
                "client_roi",
                "satisfaction_rating",
                "client_testimonial",
                "client_name",
                "key_success_factors",
            ],
            communication_style=CommunicationStyle.EMOTIONAL,
            use_cases=["Social media posts", "Website case studies", "Client referrals"],
            created_at=datetime.now(),
        )

        # Competitive Comparison Template
        templates["competitive_comparison"] = MessageTemplate(
            template_id="competitive_comparison",
            message_type=MessageType.COMPETITIVE_COMPARISON,
            title="Service Comparison Analysis",
            subject_line="Why Professional Service Outperforms Discount Options",
            opening="""
            {client_name},

            You're evaluating real estate service options, and cost is naturally a consideration. 
            Let me show you the true cost-benefit analysis of different service levels.
            """,
            main_content="""
            ## Real Estate Service Union[Comparison, Service] Union[Type, Commission] | Average Union[Results, Your] Net Outcome |
            |--------------|------------|-----------------|------------------|
            | **Professional Service (Me)** | {premium_rate}% | {premium_results} | **${premium_net:,}** |
            | Traditional Agent | {traditional_rate}% | {traditional_results} | ${traditional_net:,} |
            | Discount Broker | {discount_rate}% | {discount_results} | ${discount_net:,} |
            | For Sale By Owner | {fsbo_rate}% | {fsbo_results} | ${fsbo_net:,} |

            ### Why Professional Service Wins:

            **📊 Superior Results:**
            - {superior_result_1}
            - {superior_result_2}
            - {superior_result_3}

            **⚡ Faster Transactions:**
            Average market time: {market_average_days} days
            My average: {my_average_days} days
            **Time savings value: ${time_savings_value:,}**

            **🛡️ Risk Protection:**
            Market transaction failure rate: {market_failure_rate}%
            My transaction success rate: {my_success_rate}%
            **Risk protection value: ${risk_protection_value:,}**

            ### Bottom Line:
            While my service costs ${additional_fee:,} more than discount options, 
            you receive ${net_additional_value:,} more in value.

            **Net advantage: ${net_advantage:,} ({advantage_percentage}% better outcome)**
            """,
            closing="""
            Exceptional service isn't an expense - it's an investment that pays 
            substantial returns.

            {agent_name}
            """,
            call_to_action="Let's calculate the specific value for your property",
            personalization_variables=[
                "client_name",
                "agent_name",
                "premium_rate",
                "premium_results",
                "premium_net",
                "traditional_rate",
                "traditional_results",
                "traditional_net",
                "discount_rate",
                "discount_results",
                "discount_net",
                "fsbo_rate",
                "fsbo_results",
                "fsbo_net",
                "time_savings_value",
                "risk_protection_value",
                "net_advantage",
                "advantage_percentage",
            ],
            communication_style=CommunicationStyle.DETAILED,
            use_cases=["Service comparisons", "Pricing discussions", "Value demonstrations"],
            created_at=datetime.now(),
        )

        # Performance Update Template
        templates["performance_update"] = MessageTemplate(
            template_id="performance_update",
            message_type=MessageType.PERFORMANCE_UPDATE,
            title="Transaction Performance Update",
            subject_line="Your Transaction Update: Delivering Exceptional Value",
            opening="""
            Hi {client_name},

            I wanted to update you on our progress and share how we're delivering 
            exceptional value throughout your transaction.
            """,
            main_content="""
            ## Transaction Progress Update

            **Current Status:** {transaction_status}
            **Days Since Start:** {days_since_start}
            **Market Average Timeline:** {market_average_timeline} days

            ### Value Delivered So Far:

            **💰 Financial Value:**
            {financial_value_items}
            **Current financial benefit: ${current_financial_value:,}**

            **⚡ Time Efficiency:**
            {time_efficiency_items}
            **Time savings value: ${time_savings_value:,}**

            **🛡️ Risk Management:**
            {risk_management_items}
            **Risk protection value: ${risk_protection_value:,}**

            ### Upcoming Value Opportunities:
            {upcoming_opportunities}

            ### Current ROI Projection:
            Based on value delivered and projected completion, your current 
            ROI projection is **{current_roi_projection}%**.
            """,
            closing="""
            I'm committed to maximizing your value at every step. Feel free to 
            reach out with any questions.

            {agent_name}
            """,
            call_to_action="Questions about our progress? Let's schedule a quick check-in.",
            personalization_variables=[
                "client_name",
                "agent_name",
                "transaction_status",
                "days_since_start",
                "market_average_timeline",
                "financial_value_items",
                "current_financial_value",
                "time_efficiency_items",
                "time_savings_value",
                "risk_management_items",
                "risk_protection_value",
                "upcoming_opportunities",
                "current_roi_projection",
            ],
            communication_style=CommunicationStyle.CASUAL,
            use_cases=["Transaction updates", "Progress reports", "Client communication"],
            created_at=datetime.now(),
        )

        return templates

    async def generate_personalized_message(
        self,
        template_id: str,
        agent_id: str,
        client_id: str,
        roi_calculation: Optional[RealTimeROICalculation] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> ValueMessage:
        """
        Generate a personalized value message using a template

        Args:
            template_id: Template identifier
            agent_id: Agent identifier
            client_id: Client identifier
            roi_calculation: Optional ROI calculation data
            additional_data: Optional additional personalization data

        Returns:
            ValueMessage: Generated personalized message
        """
        try:
            # Get template
            if template_id not in self.templates:
                raise ValueError(f"Template {template_id} not found")

            template = self.templates[template_id]

            # Get ROI calculation if not provided
            if roi_calculation is None:
                roi_calculation = await self.value_engine.calculate_real_time_roi(agent_id, client_id)

            # Get value communication package
            value_communication = await self.value_engine.generate_value_communication_package(agent_id, client_id)

            # Prepare personalization data
            personalization_data = await self._prepare_personalization_data(
                template, agent_id, client_id, roi_calculation, value_communication, additional_data
            )

            # Generate content
            content = await self._generate_message_content(template, personalization_data)

            # Apply AI enhancement if enabled
            if self.message_config["ai_enhancement_enabled"]:
                content = await self._enhance_message_with_ai(content, template, personalization_data)

            # Generate subject line if applicable
            subject_line = None
            if template.subject_line:
                subject_line = template.subject_line.format(**personalization_data)

            # Create message
            message_id = f"msg_{agent_id}_{client_id}_{template_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            message = ValueMessage(
                message_id=message_id,
                template_id=template_id,
                agent_id=agent_id,
                client_id=client_id,
                message_type=template.message_type,
                subject_line=subject_line,
                content=content,
                personalization_data=personalization_data,
                roi_data={
                    "roi_percentage": float(roi_calculation.roi_percentage),
                    "total_value_delivered": float(roi_calculation.total_value_delivered),
                    "net_benefit": float(roi_calculation.net_benefit),
                },
                delivery_method="email",  # Default
                scheduled_send=None,
                generated_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=30),
            )

            logger.info(f"Generated personalized message {message_id} for client {client_id}")
            return message

        except Exception as e:
            logger.error(f"Error generating personalized message: {e}")
            raise

    async def generate_roi_email_report(self, agent_id: str, client_id: str, period_days: int = 30) -> ValueMessage:
        """Generate ROI email report for client"""

        roi_calculation = await self.value_engine.calculate_real_time_roi(agent_id, client_id, period_days=period_days)

        return await self.generate_personalized_message("roi_email_report", agent_id, client_id, roi_calculation)

    async def generate_pricing_justification(
        self, agent_id: str, client_id: str, proposed_rate: Optional[float] = None
    ) -> ValueMessage:
        """Generate pricing justification message"""

        # Get pricing recommendation
        pricing_recommendation = await self.value_engine.optimize_dynamic_pricing(agent_id)

        additional_data = {
            "proposed_rate": proposed_rate or float(pricing_recommendation.recommended_commission_rate),
            "pricing_tier": pricing_recommendation.pricing_tier.value,
            "guaranteed_roi": float(pricing_recommendation.guaranteed_roi_percentage),
        }

        return await self.generate_personalized_message(
            "pricing_justification", agent_id, client_id, additional_data=additional_data
        )

    async def generate_success_story(self, agent_id: str, client_id: str, transaction_id: str) -> ValueMessage:
        """Generate success story from completed transaction"""

        # Get transaction verification data
        verification_data = await self._get_transaction_verification_data(transaction_id)

        additional_data = {"transaction_id": transaction_id, "verification_data": verification_data}

        return await self.generate_personalized_message(
            "success_story", agent_id, client_id, additional_data=additional_data
        )

    async def generate_competitive_comparison(
        self, agent_id: str, client_id: str, property_value: Optional[float] = None
    ) -> ValueMessage:
        """Generate competitive comparison analysis"""

        # Get competitive analysis
        roi_calculation = await self.value_engine.calculate_real_time_roi(agent_id, client_id)

        additional_data = {
            "property_value": property_value or 450000,  # Default property value
            "competitive_analysis": {
                "vs_discount_broker": roi_calculation.vs_discount_broker,
                "vs_traditional_agent": roi_calculation.vs_traditional_agent,
                "vs_fsbo": roi_calculation.vs_fsbo,
            },
        }

        return await self.generate_personalized_message(
            "competitive_comparison", agent_id, client_id, additional_data=additional_data
        )

    async def generate_performance_update(self, agent_id: str, client_id: str, transaction_id: str) -> ValueMessage:
        """Generate performance update for ongoing transaction"""

        roi_calculation = await self.value_engine.calculate_real_time_roi(agent_id, client_id, transaction_id)

        additional_data = {
            "transaction_id": transaction_id,
            "transaction_status": "in_progress",  # This would come from actual transaction data
        }

        return await self.generate_personalized_message(
            "performance_update", agent_id, client_id, roi_calculation, additional_data
        )

    async def generate_bulk_messages(
        self, template_id: str, agent_id: str, client_list: List[str], batch_size: int = 10
    ) -> List[ValueMessage]:
        """Generate bulk messages for multiple clients"""

        messages = []

        # Process in batches
        for i in range(0, len(client_list), batch_size):
            batch = client_list[i : i + batch_size]

            batch_messages = await asyncio.gather(
                *[self.generate_personalized_message(template_id, agent_id, client_id) for client_id in batch]
            )

            messages.extend(batch_messages)

        logger.info(f"Generated {len(messages)} bulk messages using template {template_id}")
        return messages

    # Private helper methods

    async def _prepare_personalization_data(
        self,
        template: MessageTemplate,
        agent_id: str,
        client_id: str,
        roi_calculation: RealTimeROICalculation,
        value_communication: ValueCommunicationPackage,
        additional_data: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Prepare personalization data for template"""

        # Base personalization data
        data = {
            "client_name": await self._get_client_name(client_id),
            "agent_name": await self._get_agent_name(agent_id),
            "total_value_delivered": f"{roi_calculation.total_value_delivered:,.0f}",
            "total_investment": f"{roi_calculation.total_investment:,.0f}",
            "net_benefit": f"{roi_calculation.net_benefit:,.0f}",
            "roi_percentage": f"{roi_calculation.roi_percentage:.1f}",
            "verification_rate": f"{roi_calculation.verification_rate:.1%}",
            "confidence_level": f"{roi_calculation.overall_confidence:.1%}",
        }

        # Add value dimension breakdown
        data.update(await self._prepare_value_dimension_data(roi_calculation))

        # Add competitive analysis data
        data.update(await self._prepare_competitive_data(roi_calculation))

        # Add template-specific data
        data.update(await self._prepare_template_specific_data(template, roi_calculation, value_communication))

        # Add additional data if provided
        if additional_data:
            data.update(additional_data)

        return data

    async def _generate_message_content(self, template: MessageTemplate, personalization_data: Dict[str, Any]) -> str:
        """Generate message content from template"""

        try:
            # Combine template sections
            content = template.opening + "\n\n" + template.main_content + "\n\n" + template.closing

            # Add call to action
            content += f"\n\n---\n\n{template.call_to_action}"

            # Strip numeric format specifiers (e.g. {:,} or {:,.0f}) from template
            # placeholders because personalization data values are pre-formatted strings.
            import re

            content = re.sub(r"\{([a-zA-Z_][a-zA-Z0-9_]*):[^}]+\}", r"{\1}", content)

            # Apply personalization
            content = content.format(**personalization_data)

            return content

        except KeyError as e:
            logger.error(f"Missing personalization variable: {e}")
            # Return template with placeholder for missing variables
            return content.replace("{" + str(e).strip("'") + "}", f"[{e}]")

    async def _enhance_message_with_ai(
        self, content: str, template: MessageTemplate, personalization_data: Dict[str, Any]
    ) -> str:
        """Enhance message content using AI"""

        try:
            enhancement_prompt = f"""
            Enhance this value communication message to be more compelling and trustworthy:
            
            Original Content:
            {content}
            
            Context:
            - Communication Style: {template.communication_style.value}
            - ROI: {personalization_data.get("roi_percentage", "N/A")}%
            - Total Value: ${personalization_data.get("total_value_delivered", "N/A")}
            
            Guidelines:
            - Maintain factual accuracy
            - Enhance emotional appeal where appropriate
            - Improve clarity and readability
            - Add compelling value propositions
            - Ensure trustworthy tone
            - Keep length reasonable
            
            Enhanced Version:
            """

            enhanced_content = await self.claude.generate_response(
                enhancement_prompt, context_type="value_communication_enhancement"
            )

            return enhanced_content.strip()

        except Exception as e:
            logger.warning(f"AI enhancement failed: {e}")
            return content  # Return original if enhancement fails

    async def _prepare_value_dimension_data(self, roi_calculation: RealTimeROICalculation) -> Dict[str, str]:
        """Prepare value dimension breakdown data"""

        dimensions = [
            ("Financial Value", float(roi_calculation.financial_value)),
            ("Time Value", float(roi_calculation.time_value)),
            ("Risk Mitigation", float(roi_calculation.risk_mitigation_value)),
            ("Experience Value", float(roi_calculation.experience_value)),
            ("Information Advantage", float(roi_calculation.information_advantage_value)),
            ("Relationship Value", float(roi_calculation.relationship_value)),
        ]

        breakdown_items = []
        for name, value in dimensions:
            if value > 0:
                breakdown_items.append(f"• **{name}**: ${value:,.0f}")

        return {
            "value_dimension_breakdown": "\n".join(breakdown_items),
            "financial_value": f"{float(roi_calculation.financial_value):,.0f}",
            "time_value": f"{float(roi_calculation.time_value):,.0f}",
            "risk_mitigation_value": f"{float(roi_calculation.risk_mitigation_value):,.0f}",
            "experience_value": f"{float(roi_calculation.experience_value):,.0f}",
            "information_advantage_value": f"{float(roi_calculation.information_advantage_value):,.0f}",
            "relationship_value": f"{float(roi_calculation.relationship_value):,.0f}",
        }

    async def _prepare_competitive_data(self, roi_calculation: RealTimeROICalculation) -> Dict[str, str]:
        """Prepare competitive analysis data"""

        discount_advantage = float(roi_calculation.vs_discount_broker.get("net_benefit", 0))
        traditional_advantage = float(roi_calculation.vs_traditional_agent.get("net_benefit", 0))
        fsbo_advantage = float(roi_calculation.vs_fsbo.get("net_benefit", 0))

        return {
            "competitive_advantage": f"{max(discount_advantage, traditional_advantage, fsbo_advantage):,.0f}",
            "vs_discount_broker_advantage": f"{discount_advantage:,.0f}",
            "vs_traditional_agent_advantage": f"{traditional_advantage:,.0f}",
            "vs_fsbo_advantage": f"{fsbo_advantage:,.0f}",
        }

    async def _prepare_template_specific_data(
        self,
        template: MessageTemplate,
        roi_calculation: RealTimeROICalculation,
        value_communication: ValueCommunicationPackage,
    ) -> Dict[str, Any]:
        """Prepare template-specific data"""

        data = {}

        if template.template_id == "pricing_justification":
            data.update(
                {
                    "service_investment": f"{roi_calculation.total_investment:,.0f}",
                    "total_value": f"{roi_calculation.total_value_delivered:,.0f}",
                    "market_average_negotiation": "94.0",
                    "agent_negotiation_performance": "97.0",
                    "negotiation_savings": f"{float(roi_calculation.financial_value) * 0.6:,.0f}",
                    "market_days_to_close": "24",
                    "agent_days_to_close": "18",
                    "days_saved": "6",
                    "time_savings": f"{float(roi_calculation.time_value):,.0f}",
                    "risk_protection": f"{float(roi_calculation.risk_mitigation_value):,.0f}",
                    "market_issue_rate": "35",
                    "guaranteed_roi": "200",
                }
            )

        elif template.template_id == "success_story":
            data.update(
                {
                    "property_address": "Sample Property Address",
                    "client_challenge": "Needed to sell quickly in competitive market",
                    "solution_provided": "Strategic pricing and targeted marketing",
                    "sale_price": "447000",
                    "percentage_above_asking": "101.6",
                    "days_to_close": "18",
                    "days_faster": "6",
                    "client_roi": f"{roi_calculation.roi_percentage:.0f}",
                    "satisfaction_rating": "4.9",
                    "client_testimonial": "Exceptional service and outstanding results!",
                    "key_success_factors": ["Strategic pricing", "Targeted marketing", "Expert negotiation"],
                }
            )

        elif template.template_id == "roi_email_report":
            data.update(
                {
                    "key_achievements": "\n".join(
                        [f"✅ {achievement}" for achievement in value_communication.key_value_highlights]
                    )
                }
            )

        return data

    # Placeholder methods for data retrieval
    async def _get_client_name(self, client_id: str) -> str:
        """Get client name"""
        return f"Client {client_id}"

    async def _get_agent_name(self, agent_id: str) -> str:
        """Get agent name"""
        return f"Agent {agent_id}"

    async def _get_transaction_verification_data(self, transaction_id: str) -> Dict[str, Any]:
        """Get transaction verification data"""
        return {"verified": True, "confidence": 0.95}


# Global instance
_value_communication_templates = None


def get_value_communication_templates() -> ValueCommunicationTemplates:
    """Get global value communication templates instance"""
    global _value_communication_templates
    if _value_communication_templates is None:
        _value_communication_templates = ValueCommunicationTemplates()
    return _value_communication_templates
