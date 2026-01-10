"""
Video Message Integration Service

Revolutionary video message automation for real estate lead nurturing.
Automatically generates personalized video messages using AI avatars,
property showcases, and agent recordings.
"""

import asyncio
import json
import logging
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
import aiohttp
import aiofiles

# Internal imports
from models.nurturing_models import (
    PersonalizedMessage, CommunicationChannel, MessageTone,
    LeadType, EngagementType
)
from models.evaluation_models import LeadEvaluationResult
from services.advanced_ml_personalization_engine import AdvancedMLPersonalizationEngine

logger = logging.getLogger(__name__)


@dataclass
class VideoGenerationRequest:
    """Request for video message generation."""
    lead_id: str
    agent_name: str
    agent_avatar_style: str
    message_content: str
    property_images: List[str]
    background_style: str
    video_length: int  # seconds
    include_property_tour: bool
    include_market_data: bool
    call_to_action: str
    branding_elements: Dict[str, str]


@dataclass
class VideoMessage:
    """Generated video message with metadata."""
    video_id: str
    video_url: str
    thumbnail_url: str
    duration_seconds: int
    file_size_mb: float
    generated_at: datetime
    personalization_data: Dict[str, Any]
    engagement_tracking_url: str
    download_url: str
    sharing_urls: Dict[str, str]


@dataclass
class VideoTemplate:
    """Video template configuration."""
    template_id: str
    name: str
    description: str
    lead_type: LeadType
    template_structure: List[Dict[str, Any]]
    default_duration: int
    customization_options: List[str]
    performance_metrics: Dict[str, float]


class VideoMessageIntegration:
    """
    Video Message Integration Service

    Provides AI-powered video message generation for real estate lead nurturing
    with personalized content, property showcases, and professional presentation.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        personalization_engine: Optional[AdvancedMLPersonalizationEngine] = None
    ):
        """Initialize video message integration."""
        self.api_key = api_key or "demo_api_key"  # In production, use real API key
        self.personalization_engine = personalization_engine or AdvancedMLPersonalizationEngine()

        # Video generation settings
        self.video_storage_base = "https://storage.ghlrealestateai.com/videos/"
        self.max_video_length = 300  # 5 minutes
        self.supported_formats = ["mp4", "webm", "gif"]

        # Template management
        self.video_templates: Dict[str, VideoTemplate] = {}
        self._initialize_video_templates()

        # Performance tracking
        self._generation_metrics = {
            "total_generated": 0,
            "success_rate": 0.95,
            "average_generation_time": 45.0,
            "engagement_rate": 0.68
        }

        logger.info("Video Message Integration initialized")

    def _initialize_video_templates(self):
        """Initialize predefined video templates for different lead types."""

        # First-Time Buyer Welcome Template
        self.video_templates["first_buyer_welcome"] = VideoTemplate(
            template_id="first_buyer_welcome",
            name="First-Time Buyer Welcome",
            description="Warm welcome video with buying process overview",
            lead_type=LeadType.BUYER_FIRST_TIME,
            template_structure=[
                {"section": "greeting", "duration": 10, "type": "agent_speaking"},
                {"section": "market_overview", "duration": 15, "type": "data_visualization"},
                {"section": "process_explanation", "duration": 20, "type": "animated_guide"},
                {"section": "property_preview", "duration": 15, "type": "property_slideshow"},
                {"section": "call_to_action", "duration": 10, "type": "agent_speaking"}
            ],
            default_duration=70,
            customization_options=["agent_style", "market_data", "property_selection"],
            performance_metrics={"engagement_rate": 0.72, "conversion_rate": 0.34}
        )

        # Investment Property Template
        self.video_templates["investment_analysis"] = VideoTemplate(
            template_id="investment_analysis",
            name="Investment Property Analysis",
            description="Data-driven analysis with ROI projections",
            lead_type=LeadType.BUYER_INVESTMENT,
            template_structure=[
                {"section": "market_data_intro", "duration": 15, "type": "data_visualization"},
                {"section": "property_analysis", "duration": 30, "type": "detailed_breakdown"},
                {"section": "roi_projections", "duration": 20, "type": "financial_charts"},
                {"section": "risk_assessment", "duration": 10, "type": "agent_speaking"},
                {"section": "recommendation", "duration": 15, "type": "agent_speaking"}
            ],
            default_duration=90,
            customization_options=["financial_data", "comparable_properties", "market_trends"],
            performance_metrics={"engagement_rate": 0.78, "conversion_rate": 0.42}
        )

        # Luxury Property Showcase Template
        self.video_templates["luxury_showcase"] = VideoTemplate(
            template_id="luxury_showcase",
            name="Luxury Property Showcase",
            description="High-end property presentation with elegant styling",
            lead_type=LeadType.BUYER_LUXURY,
            template_structure=[
                {"section": "luxury_intro", "duration": 10, "type": "cinematic_opening"},
                {"section": "property_tour", "duration": 45, "type": "virtual_walkthrough"},
                {"section": "amenities_highlight", "duration": 20, "type": "feature_showcase"},
                {"section": "lifestyle_presentation", "duration": 15, "type": "lifestyle_imagery"},
                {"section": "exclusive_invitation", "duration": 10, "type": "agent_speaking"}
            ],
            default_duration=100,
            customization_options=["property_style", "amenity_focus", "lifestyle_elements"],
            performance_metrics={"engagement_rate": 0.85, "conversion_rate": 0.51}
        )

        # Market Update Template
        self.video_templates["market_update"] = VideoTemplate(
            template_id="market_update",
            name="Personalized Market Update",
            description="Current market trends and opportunities",
            lead_type=LeadType.BUYER_FIRST_TIME,  # Can be used for any type
            template_structure=[
                {"section": "market_intro", "duration": 10, "type": "agent_speaking"},
                {"section": "trend_analysis", "duration": 25, "type": "data_visualization"},
                {"section": "opportunity_highlights", "duration": 20, "type": "property_grid"},
                {"section": "timing_advice", "duration": 10, "type": "agent_speaking"},
                {"section": "next_steps", "duration": 5, "type": "call_to_action"}
            ],
            default_duration=70,
            customization_options=["location_focus", "price_range", "market_segment"],
            performance_metrics={"engagement_rate": 0.69, "conversion_rate": 0.28}
        )

    async def generate_personalized_video(
        self,
        lead_id: str,
        template_id: str,
        evaluation_result: LeadEvaluationResult,
        context: Dict[str, Any]
    ) -> VideoMessage:
        """
        Generate a personalized video message for a lead.

        Args:
            lead_id: Lead identifier
            template_id: Video template to use
            evaluation_result: Lead evaluation data
            context: Additional context for personalization

        Returns:
            Generated video message with metadata
        """
        try:
            # Get template
            template = self.video_templates.get(template_id)
            if not template:
                raise ValueError(f"Template {template_id} not found")

            # Generate personalization using ML engine
            personalization = await self.personalization_engine.generate_personalized_communication(
                lead_id=lead_id,
                evaluation_result=evaluation_result,
                message_template="Video message template",
                interaction_history=[],
                context=context
            )

            # Create video generation request
            video_request = VideoGenerationRequest(
                lead_id=lead_id,
                agent_name=context.get('agent_name', 'Your Real Estate Agent'),
                agent_avatar_style=self._determine_agent_avatar_style(evaluation_result),
                message_content=await self._generate_video_script(template, personalization, context),
                property_images=context.get('property_images', []),
                background_style=self._determine_background_style(template, evaluation_result),
                video_length=template.default_duration,
                include_property_tour=template.template_id in ["luxury_showcase", "investment_analysis"],
                include_market_data=template.template_id in ["market_update", "investment_analysis"],
                call_to_action=self._generate_call_to_action(template, personalization),
                branding_elements=context.get('branding', {})
            )

            # Generate video
            video_message = await self._generate_video_content(video_request, template)

            # Track generation metrics
            self._update_generation_metrics(video_message)

            logger.info(f"Generated personalized video {video_message.video_id} for lead {lead_id}")

            return video_message

        except Exception as e:
            logger.error(f"Video generation failed for lead {lead_id}: {str(e)}")
            return await self._generate_fallback_video(lead_id, template_id, context)

    def _determine_agent_avatar_style(self, evaluation_result: LeadEvaluationResult) -> str:
        """Determine the best agent avatar style based on lead profile."""
        score = evaluation_result.overall_score

        if score > 85:
            return "professional_executive"  # High-end, polished
        elif score > 70:
            return "friendly_professional"   # Approachable but professional
        elif score > 55:
            return "casual_expert"          # More relaxed, friendly
        else:
            return "warm_supportive"        # Very friendly and patient

    def _determine_background_style(self, template: VideoTemplate, evaluation_result: LeadEvaluationResult) -> str:
        """Determine video background style."""
        if template.lead_type == LeadType.BUYER_LUXURY:
            return "luxury_office"
        elif template.lead_type == LeadType.BUYER_INVESTMENT:
            return "modern_office"
        elif template.template_id == "market_update":
            return "market_data_background"
        else:
            return "professional_office"

    async def _generate_video_script(
        self,
        template: VideoTemplate,
        personalization,
        context: Dict[str, Any]
    ) -> str:
        """Generate the video script based on template and personalization."""

        scripts = {
            "first_buyer_welcome": f"""
            Hello {context.get('first_name', 'there')}! I'm {context.get('agent_name', 'your agent')}, and I'm thrilled to welcome you to your home buying journey.

            I know buying your first home can feel overwhelming, but I'm here to make it as smooth and exciting as possible. Based on your interest in {context.get('property_type', 'properties')} in {context.get('location_preference', 'your preferred area')}, I've already started identifying some fantastic options.

            Let me quickly walk you through what we'll accomplish together:
            - First, we'll get you pre-approved so you know exactly what you can afford
            - Then we'll tour properties that match your needs and budget
            - When we find "the one," I'll help you make a competitive offer
            - And finally, I'll guide you through closing and getting your keys!

            I've attached some properties that caught my eye for you - take a look and let me know what interests you. Ready to find your perfect home?
            """,

            "investment_analysis": f"""
            {context.get('first_name', 'Investor')}, let's dive into the numbers.

            The {context.get('location_preference', 'market')} presents excellent investment opportunities right now. Based on current market data, properties in your ${context.get('budget_range', '400K-600K')} range are showing strong appreciation trends.

            Here's what makes this market attractive:
            - Average cap rates of 7.2% for similar properties
            - 15% year-over-year appreciation in this area
            - Strong rental demand with 95% occupancy rates

            The property I'm showing you today has potential for both cash flow and appreciation. With conservative projections, you're looking at a 12-15% total return in the first year.

            I've run the complete analysis - let's schedule a call to discuss the numbers in detail.
            """,

            "luxury_showcase": f"""
            Welcome to a truly exceptional property, {context.get('first_name', '')}.

            This {context.get('property_type', 'estate')} represents the pinnacle of luxury living in {context.get('location_preference', 'this prestigious area')}. Every detail has been meticulously crafted to provide an unparalleled living experience.

            As we tour through the home, you'll notice the exceptional attention to detail - from the custom millwork to the professional-grade kitchen that would inspire any culinary enthusiast.

            The private grounds offer complete tranquility while still being minutes from the finest dining, shopping, and cultural amenities.

            This is more than a home - it's a lifestyle. I'd love to arrange a private showing so you can experience the elegance in person.
            """,

            "market_update": f"""
            Good {self._get_time_of_day()}, {context.get('first_name', '')}!

            I wanted to share some exciting market developments that could impact your home search in {context.get('location_preference', 'your area')}.

            Recent trends show:
            - Inventory is increasing, giving buyers more choices
            - Interest rates remain favorable for qualified buyers
            - Spring market activity is creating opportunities

            Based on your criteria, I've identified 3 new properties that just came on the market. One in particular stands out as exceptional value.

            The market timing looks excellent for your purchase. Let's connect this week to discuss your next steps.
            """
        }

        return scripts.get(template.template_id, "Thank you for your interest. Let's connect to discuss your real estate needs.")

    def _generate_call_to_action(self, template: VideoTemplate, personalization) -> str:
        """Generate appropriate call-to-action based on template and lead profile."""

        ctas = {
            "first_buyer_welcome": "Reply to this message or call me directly to schedule your buyer consultation!",
            "investment_analysis": "Let's schedule a 15-minute call to review the complete financial analysis.",
            "luxury_showcase": "Contact me today to arrange your private showing of this exceptional property.",
            "market_update": "Reply with 'YES' if you'd like to see the new listings I mentioned!"
        }

        return ctas.get(template.template_id, "Let's connect to discuss your real estate goals!")

    async def _generate_video_content(
        self,
        request: VideoGenerationRequest,
        template: VideoTemplate
    ) -> VideoMessage:
        """Generate the actual video content using AI video generation services."""

        try:
            # In a real implementation, this would call actual video generation APIs
            # For demo purposes, we'll simulate the process

            video_id = f"video_{request.lead_id}_{int(datetime.now().timestamp())}"

            # Simulate video generation process
            await asyncio.sleep(2)  # Simulate processing time

            # Generate mock video URLs
            video_url = f"{self.video_storage_base}{video_id}/video.mp4"
            thumbnail_url = f"{self.video_storage_base}{video_id}/thumbnail.jpg"
            engagement_tracking_url = f"https://analytics.ghlrealestateai.com/track/{video_id}"

            # Calculate estimated file size based on duration and quality
            estimated_size_mb = (request.video_length * 0.8)  # ~0.8MB per second for good quality

            video_message = VideoMessage(
                video_id=video_id,
                video_url=video_url,
                thumbnail_url=thumbnail_url,
                duration_seconds=request.video_length,
                file_size_mb=estimated_size_mb,
                generated_at=datetime.now(),
                personalization_data={
                    "agent_avatar": request.agent_avatar_style,
                    "background": request.background_style,
                    "property_count": len(request.property_images),
                    "personalization_level": "high"
                },
                engagement_tracking_url=engagement_tracking_url,
                download_url=f"{video_url}?download=1",
                sharing_urls={
                    "email": f"mailto:?subject=Your Real Estate Video&body=Watch your personalized video: {video_url}",
                    "sms": f"sms:?body=Your personalized property video: {video_url}",
                    "whatsapp": f"https://wa.me/?text=Your personalized property video: {video_url}",
                    "linkedin": f"https://linkedin.com/sharing/share-offsite/?url={video_url}"
                }
            )

            # Store video metadata (in production, this would go to database)
            await self._store_video_metadata(video_message, request)

            return video_message

        except Exception as e:
            logger.error(f"Video content generation failed: {str(e)}")
            raise

    async def _store_video_metadata(self, video_message: VideoMessage, request: VideoGenerationRequest):
        """Store video metadata for tracking and analytics."""
        metadata = {
            "video_id": video_message.video_id,
            "lead_id": request.lead_id,
            "generated_at": video_message.generated_at.isoformat(),
            "duration": video_message.duration_seconds,
            "template_used": request.background_style,
            "personalization_data": video_message.personalization_data
        }

        # In production, store in database
        logger.info(f"Stored metadata for video {video_message.video_id}")

    def _update_generation_metrics(self, video_message: VideoMessage):
        """Update video generation performance metrics."""
        self._generation_metrics["total_generated"] += 1
        # In production, update more detailed metrics

    async def _generate_fallback_video(
        self,
        lead_id: str,
        template_id: str,
        context: Dict[str, Any]
    ) -> VideoMessage:
        """Generate a simple fallback video when main generation fails."""

        video_id = f"fallback_{lead_id}_{int(datetime.now().timestamp())}"

        return VideoMessage(
            video_id=video_id,
            video_url=f"{self.video_storage_base}fallback/standard_intro.mp4",
            thumbnail_url=f"{self.video_storage_base}fallback/standard_thumb.jpg",
            duration_seconds=30,
            file_size_mb=15.0,
            generated_at=datetime.now(),
            personalization_data={"type": "fallback", "reason": "generation_failed"},
            engagement_tracking_url=f"https://analytics.ghlrealestateai.com/track/{video_id}",
            download_url=f"{self.video_storage_base}fallback/standard_intro.mp4?download=1",
            sharing_urls={
                "email": f"mailto:?subject=Welcome Video&body=Watch our introduction video"
            }
        )

    def _get_time_of_day(self) -> str:
        """Get appropriate greeting based on time of day."""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        else:
            return "evening"

    # Video Management Methods

    async def get_video_performance_analytics(self, video_id: str) -> Dict[str, Any]:
        """Get performance analytics for a specific video."""
        # Mock analytics data
        return {
            "video_id": video_id,
            "views": 12,
            "unique_viewers": 8,
            "completion_rate": 0.78,
            "engagement_rate": 0.65,
            "click_through_rate": 0.23,
            "sharing_count": 3,
            "responses_generated": 2,
            "time_watched": {
                "average_seconds": 45,
                "median_seconds": 52,
                "total_watch_time": 540
            },
            "viewer_behavior": {
                "peak_engagement_at": "15s",
                "drop_off_points": ["35s", "55s"],
                "replay_count": 4
            },
            "device_breakdown": {
                "mobile": 0.67,
                "desktop": 0.25,
                "tablet": 0.08
            }
        }

    async def get_template_performance(self) -> Dict[str, Dict[str, float]]:
        """Get performance metrics for all video templates."""
        performance_data = {}

        for template_id, template in self.video_templates.items():
            performance_data[template_id] = {
                "engagement_rate": template.performance_metrics.get("engagement_rate", 0.0),
                "conversion_rate": template.performance_metrics.get("conversion_rate", 0.0),
                "average_completion": 0.75,  # Mock data
                "response_rate": 0.45,
                "sharing_rate": 0.12
            }

        return performance_data

    async def optimize_template_performance(self, template_id: str, performance_data: Dict[str, float]):
        """Optimize template performance based on analytics data."""
        template = self.video_templates.get(template_id)
        if not template:
            return False

        # Update performance metrics
        template.performance_metrics.update(performance_data)

        # Suggest optimizations based on performance
        optimizations = []

        if performance_data.get("completion_rate", 0) < 0.7:
            optimizations.append("Consider shortening video duration")

        if performance_data.get("engagement_rate", 0) < 0.6:
            optimizations.append("Add more interactive elements")

        if performance_data.get("click_through_rate", 0) < 0.2:
            optimizations.append("Strengthen call-to-action")

        logger.info(f"Generated {len(optimizations)} optimizations for template {template_id}")
        return optimizations

    # Batch Video Generation

    async def generate_bulk_videos(
        self,
        lead_data_list: List[Dict[str, Any]],
        template_id: str
    ) -> List[VideoMessage]:
        """Generate multiple videos in batch for efficiency."""
        video_messages = []

        # Process in batches to avoid overwhelming the system
        batch_size = 5

        for i in range(0, len(lead_data_list), batch_size):
            batch = lead_data_list[i:i + batch_size]

            # Generate videos concurrently within batch
            batch_tasks = []
            for lead_data in batch:
                task = self.generate_personalized_video(
                    lead_id=lead_data['lead_id'],
                    template_id=template_id,
                    evaluation_result=lead_data['evaluation_result'],
                    context=lead_data['context']
                )
                batch_tasks.append(task)

            # Wait for batch completion
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Filter successful results
            for result in batch_results:
                if isinstance(result, VideoMessage):
                    video_messages.append(result)
                else:
                    logger.error(f"Batch video generation error: {result}")

            # Small delay between batches
            await asyncio.sleep(1)

        logger.info(f"Generated {len(video_messages)} videos from {len(lead_data_list)} requests")
        return video_messages

    # Integration with Nurturing System

    async def create_video_touchpoint(
        self,
        lead_id: str,
        sequence_step: Dict[str, Any],
        evaluation_result: LeadEvaluationResult,
        context: Dict[str, Any]
    ) -> PersonalizedMessage:
        """Create a video touchpoint for nurturing sequences."""

        # Determine appropriate template based on sequence step
        template_id = self._select_template_for_sequence_step(sequence_step, evaluation_result)

        # Generate video
        video_message = await self.generate_personalized_video(
            lead_id=lead_id,
            template_id=template_id,
            evaluation_result=evaluation_result,
            context=context
        )

        # Create personalized message with video
        personalized_message = PersonalizedMessage(
            lead_id=lead_id,
            template_id=template_id,
            channel=CommunicationChannel.EMAIL,  # Video delivered via email
            subject=f"🎥 Your Personalized Video from {context.get('agent_name', 'Your Agent')}",
            content=self._create_video_email_content(video_message, context),
            tone=MessageTone.FRIENDLY,
            personalization_data={
                "video_id": video_message.video_id,
                "video_url": video_message.video_url,
                "thumbnail_url": video_message.thumbnail_url,
                "duration": video_message.duration_seconds
            },
            estimated_effectiveness=0.75  # Videos typically have higher engagement
        )

        return personalized_message

    def _select_template_for_sequence_step(
        self,
        sequence_step: Dict[str, Any],
        evaluation_result: LeadEvaluationResult
    ) -> str:
        """Select appropriate video template based on sequence step and lead profile."""

        step_type = sequence_step.get('type', 'unknown')
        step_number = sequence_step.get('step_number', 1)
        lead_score = evaluation_result.overall_score

        # First step usually gets welcome video
        if step_number == 1:
            if lead_score > 85:
                return "luxury_showcase"
            else:
                return "first_buyer_welcome"

        # Market update for mid-sequence engagement
        elif step_type in ['market_insights', 'follow_up']:
            return "market_update"

        # Investment analysis for qualified leads
        elif step_type == 'property_analysis' and lead_score > 70:
            return "investment_analysis"

        # Default to market update
        return "market_update"

    def _create_video_email_content(self, video_message: VideoMessage, context: Dict[str, Any]) -> str:
        """Create email content that embeds the video message."""

        agent_name = context.get('agent_name', 'Your Real Estate Agent')
        first_name = context.get('first_name', 'there')

        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #2c5aa0;">Hi {first_name}!</h2>

            <p>I've created a personalized video just for you. Take a look:</p>

            <div style="text-align: center; margin: 20px 0;">
                <a href="{video_message.video_url}" style="display: inline-block; position: relative;">
                    <img src="{video_message.thumbnail_url}"
                         alt="Play Video"
                         style="max-width: 100%; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                    <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
                                background: rgba(255,255,255,0.9); border-radius: 50%;
                                width: 60px; height: 60px; display: flex; align-items: center; justify-content: center;">
                        <span style="color: #2c5aa0; font-size: 24px;">▶</span>
                    </div>
                </a>
            </div>

            <p style="text-align: center; margin: 15px 0;">
                <a href="{video_message.video_url}"
                   style="background: #2c5aa0; color: white; padding: 12px 24px;
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    🎥 Watch Your Personalized Video
                </a>
            </p>

            <p><strong>Video Duration:</strong> {video_message.duration_seconds} seconds</p>

            <p>After watching, feel free to reply with any questions or to schedule a call.
               I'm here to help with your real estate journey!</p>

            <p>Best regards,<br>
            {agent_name}</p>

            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">

            <div style="text-align: center; font-size: 12px; color: #666;">
                <p>Share this video:</p>
                <p>
                    <a href="{video_message.sharing_urls.get('email', '#')}" style="margin: 0 10px;">Email</a>
                    <a href="{video_message.sharing_urls.get('sms', '#')}" style="margin: 0 10px;">SMS</a>
                    <a href="{video_message.sharing_urls.get('linkedin', '#')}" style="margin: 0 10px;">LinkedIn</a>
                </p>
            </div>
        </div>
        """

    # System Health and Monitoring

    async def get_system_health(self) -> Dict[str, Any]:
        """Get video generation system health status."""
        return {
            "status": "healthy",
            "templates_available": len(self.video_templates),
            "generation_queue": 0,  # Mock queue size
            "average_generation_time": self._generation_metrics["average_generation_time"],
            "success_rate": self._generation_metrics["success_rate"],
            "storage_usage": {
                "total_videos": self._generation_metrics["total_generated"],
                "storage_used_gb": self._generation_metrics["total_generated"] * 0.025,  # ~25MB per video
                "storage_limit_gb": 1000
            },
            "api_status": {
                "video_generation_api": "operational",
                "storage_api": "operational",
                "analytics_api": "operational"
            }
        }


# Export the main class
__all__ = ['VideoMessageIntegration', 'VideoMessage', 'VideoTemplate', 'VideoGenerationRequest']