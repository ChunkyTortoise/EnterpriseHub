"""
ROI Attribution System

Advanced ROI tracking and attribution system for measuring the business impact
of automated lead nurturing campaigns, with detailed attribution models,
revenue tracking, and performance analytics.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from pathlib import Path

# Internal imports
from models.nurturing_models import (
    NurturingCampaign, EngagementInteraction, CampaignStatus,
    CommunicationChannel, EngagementType
)
from models.evaluation_models import LeadEvaluationResult

logger = logging.getLogger(__name__)


class ConversionEventType(str, Enum):
    """Types of conversion events for attribution."""
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    SHOWING_ATTENDED = "showing_attended"
    OFFER_SUBMITTED = "offer_submitted"
    CONTRACT_SIGNED = "contract_signed"
    CLOSING_COMPLETED = "closing_completed"
    LISTING_SIGNED = "listing_signed"
    REFERRAL_GENERATED = "referral_generated"


class AttributionModel(str, Enum):
    """Attribution models for revenue attribution."""
    FIRST_TOUCH = "first_touch"
    LAST_TOUCH = "last_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"
    POSITION_BASED = "position_based"
    DATA_DRIVEN = "data_driven"


@dataclass
class ConversionEvent:
    """Conversion event with attribution data."""
    event_id: str
    lead_id: str
    event_type: ConversionEventType
    event_value: float  # Revenue value
    occurred_at: datetime
    attributed_touchpoints: List[str]  # Touchpoint IDs
    attribution_weights: Dict[str, float]  # Touchpoint -> weight
    conversion_probability: float
    time_to_conversion: timedelta
    metadata: Dict[str, Any]


@dataclass
class TouchpointAttribution:
    """Attribution data for a specific touchpoint."""
    touchpoint_id: str
    campaign_id: str
    lead_id: str
    channel: CommunicationChannel
    engagement_type: EngagementType
    occurred_at: datetime
    attributed_revenue: float
    attribution_weight: float
    attribution_model: AttributionModel
    conversion_assists: int
    final_conversions: int
    incremental_value: float


@dataclass
class CampaignROI:
    """ROI metrics for a nurturing campaign."""
    campaign_id: str
    total_investment: float
    total_revenue: float
    roi_percentage: float
    roas: float  # Return on Ad Spend
    conversion_rate: float
    average_deal_size: float
    customer_lifetime_value: float
    cost_per_conversion: float
    attribution_by_model: Dict[str, float]
    time_to_roi: Optional[timedelta]
    confidence_interval: Tuple[float, float]


@dataclass
class ChannelPerformance:
    """Performance metrics by communication channel."""
    channel: CommunicationChannel
    total_touchpoints: int
    total_revenue: float
    conversion_rate: float
    cost_per_touchpoint: float
    roi_percentage: float
    average_time_to_conversion: timedelta
    best_performing_sequences: List[str]
    optimization_recommendations: List[str]


class ROIAttributionSystem:
    """
    ROI Attribution System

    Comprehensive system for tracking, measuring, and attributing revenue
    to automated lead nurturing campaigns with multiple attribution models
    and advanced analytics.
    """

    def __init__(self):
        """Initialize the ROI attribution system."""

        # Attribution configuration
        self.attribution_models = {
            AttributionModel.FIRST_TOUCH: self._first_touch_attribution,
            AttributionModel.LAST_TOUCH: self._last_touch_attribution,
            AttributionModel.LINEAR: self._linear_attribution,
            AttributionModel.TIME_DECAY: self._time_decay_attribution,
            AttributionModel.POSITION_BASED: self._position_based_attribution,
            AttributionModel.DATA_DRIVEN: self._data_driven_attribution
        }

        # Cost tracking
        self.channel_costs = {
            CommunicationChannel.EMAIL: 0.05,   # $0.05 per email
            CommunicationChannel.SMS: 0.25,     # $0.25 per SMS
            CommunicationChannel.PHONE: 2.50,   # $2.50 per call
            CommunicationChannel.LINKEDIN: 0.15, # $0.15 per LinkedIn message
            CommunicationChannel.GHL_TASK: 0.10  # $0.10 per GHL task
        }

        # Revenue tracking
        self.conversion_values = {
            ConversionEventType.APPOINTMENT_SCHEDULED: 150.0,
            ConversionEventType.SHOWING_ATTENDED: 300.0,
            ConversionEventType.OFFER_SUBMITTED: 750.0,
            ConversionEventType.CONTRACT_SIGNED: 2500.0,
            ConversionEventType.CLOSING_COMPLETED: 8500.0,  # Average commission
            ConversionEventType.LISTING_SIGNED: 3500.0,
            ConversionEventType.REFERRAL_GENERATED: 1200.0
        }

        # Data storage
        self.conversion_events: List[ConversionEvent] = []
        self.touchpoint_attributions: List[TouchpointAttribution] = []
        self.campaign_rois: Dict[str, CampaignROI] = {}

        # Performance tracking
        self._attribution_cache = {}
        self._performance_cache = {}

        logger.info("ROI Attribution System initialized")

    # Core Attribution Methods

    async def track_conversion_event(
        self,
        lead_id: str,
        event_type: ConversionEventType,
        event_value: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversionEvent:
        """
        Track a conversion event and calculate attribution.

        Args:
            lead_id: Lead identifier
            event_type: Type of conversion event
            event_value: Custom revenue value (optional)
            metadata: Additional event data

        Returns:
            Created conversion event with attribution data
        """
        try:
            # Get touchpoint history for the lead
            touchpoint_history = await self._get_lead_touchpoint_history(lead_id)

            if not touchpoint_history:
                logger.warning(f"No touchpoint history found for lead {lead_id}")
                return await self._create_organic_conversion_event(lead_id, event_type, event_value, metadata)

            # Calculate attribution across all models
            attribution_results = await self._calculate_multi_model_attribution(
                touchpoint_history, event_value or self.conversion_values.get(event_type, 0)
            )

            # Create conversion event
            conversion_event = ConversionEvent(
                event_id=f"conv_{lead_id}_{int(datetime.now().timestamp())}",
                lead_id=lead_id,
                event_type=event_type,
                event_value=event_value or self.conversion_values.get(event_type, 0),
                occurred_at=datetime.now(),
                attributed_touchpoints=[tp['touchpoint_id'] for tp in touchpoint_history],
                attribution_weights=attribution_results[AttributionModel.DATA_DRIVEN],
                conversion_probability=await self._calculate_conversion_probability(touchpoint_history),
                time_to_conversion=await self._calculate_time_to_conversion(touchpoint_history),
                metadata=metadata or {}
            )

            # Store conversion event
            self.conversion_events.append(conversion_event)

            # Update touchpoint attributions
            await self._update_touchpoint_attributions(conversion_event, attribution_results)

            # Update campaign ROI metrics
            await self._update_campaign_roi_metrics(conversion_event)

            logger.info(f"Tracked conversion event {conversion_event.event_id} with value ${conversion_event.event_value}")

            return conversion_event

        except Exception as e:
            logger.error(f"Failed to track conversion event: {str(e)}")
            raise

    async def _calculate_multi_model_attribution(
        self,
        touchpoint_history: List[Dict[str, Any]],
        total_value: float
    ) -> Dict[AttributionModel, Dict[str, float]]:
        """Calculate attribution weights using multiple attribution models."""

        attribution_results = {}

        for model, attribution_func in self.attribution_models.items():
            try:
                weights = await attribution_func(touchpoint_history, total_value)
                attribution_results[model] = weights
            except Exception as e:
                logger.error(f"Attribution calculation failed for {model}: {str(e)}")
                # Fallback to equal distribution
                equal_weight = total_value / len(touchpoint_history)
                attribution_results[model] = {
                    tp['touchpoint_id']: equal_weight for tp in touchpoint_history
                }

        return attribution_results

    # Attribution Model Implementations

    async def _first_touch_attribution(
        self,
        touchpoint_history: List[Dict[str, Any]],
        total_value: float
    ) -> Dict[str, float]:
        """First-touch attribution: 100% credit to first touchpoint."""
        if not touchpoint_history:
            return {}

        first_touchpoint = min(touchpoint_history, key=lambda x: x['occurred_at'])
        return {
            tp['touchpoint_id']: total_value if tp['touchpoint_id'] == first_touchpoint['touchpoint_id'] else 0.0
            for tp in touchpoint_history
        }

    async def _last_touch_attribution(
        self,
        touchpoint_history: List[Dict[str, Any]],
        total_value: float
    ) -> Dict[str, float]:
        """Last-touch attribution: 100% credit to last touchpoint."""
        if not touchpoint_history:
            return {}

        last_touchpoint = max(touchpoint_history, key=lambda x: x['occurred_at'])
        return {
            tp['touchpoint_id']: total_value if tp['touchpoint_id'] == last_touchpoint['touchpoint_id'] else 0.0
            for tp in touchpoint_history
        }

    async def _linear_attribution(
        self,
        touchpoint_history: List[Dict[str, Any]],
        total_value: float
    ) -> Dict[str, float]:
        """Linear attribution: equal credit to all touchpoints."""
        if not touchpoint_history:
            return {}

        equal_weight = total_value / len(touchpoint_history)
        return {tp['touchpoint_id']: equal_weight for tp in touchpoint_history}

    async def _time_decay_attribution(
        self,
        touchpoint_history: List[Dict[str, Any]],
        total_value: float,
        decay_rate: float = 0.5
    ) -> Dict[str, float]:
        """Time-decay attribution: more credit to recent touchpoints."""
        if not touchpoint_history:
            return {}

        # Sort by time
        sorted_touchpoints = sorted(touchpoint_history, key=lambda x: x['occurred_at'])

        # Calculate weights with exponential decay
        weights = []
        for i, tp in enumerate(sorted_touchpoints):
            days_from_conversion = (datetime.now() - tp['occurred_at']).days
            weight = np.exp(-decay_rate * days_from_conversion)
            weights.append(weight)

        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            return await self._linear_attribution(touchpoint_history, total_value)

        attribution = {}
        for i, tp in enumerate(sorted_touchpoints):
            attribution[tp['touchpoint_id']] = (weights[i] / total_weight) * total_value

        return attribution

    async def _position_based_attribution(
        self,
        touchpoint_history: List[Dict[str, Any]],
        total_value: float,
        first_touch_weight: float = 0.4,
        last_touch_weight: float = 0.4
    ) -> Dict[str, float]:
        """Position-based attribution: 40% first, 40% last, 20% middle."""
        if not touchpoint_history:
            return {}

        if len(touchpoint_history) == 1:
            return {touchpoint_history[0]['touchpoint_id']: total_value}

        if len(touchpoint_history) == 2:
            return {
                touchpoint_history[0]['touchpoint_id']: total_value * 0.5,
                touchpoint_history[1]['touchpoint_id']: total_value * 0.5
            }

        # Sort by time
        sorted_touchpoints = sorted(touchpoint_history, key=lambda x: x['occurred_at'])

        attribution = {}
        middle_weight = 1.0 - first_touch_weight - last_touch_weight
        middle_touchpoints = len(sorted_touchpoints) - 2

        # First touch
        attribution[sorted_touchpoints[0]['touchpoint_id']] = total_value * first_touch_weight

        # Last touch
        attribution[sorted_touchpoints[-1]['touchpoint_id']] = total_value * last_touch_weight

        # Middle touches
        if middle_touchpoints > 0:
            middle_weight_per_touch = (total_value * middle_weight) / middle_touchpoints
            for tp in sorted_touchpoints[1:-1]:
                attribution[tp['touchpoint_id']] = middle_weight_per_touch

        return attribution

    async def _data_driven_attribution(
        self,
        touchpoint_history: List[Dict[str, Any]],
        total_value: float
    ) -> Dict[str, float]:
        """Data-driven attribution using machine learning insights."""
        if not touchpoint_history:
            return {}

        # For now, use a hybrid approach based on engagement data
        # In production, this would use ML models trained on historical conversion data

        attribution = {}
        total_weight = 0

        for tp in touchpoint_history:
            # Base weight from engagement
            base_weight = 1.0

            # Channel effectiveness multiplier
            channel_multiplier = {
                CommunicationChannel.PHONE: 2.5,
                CommunicationChannel.EMAIL: 1.0,
                CommunicationChannel.SMS: 1.5,
                CommunicationChannel.LINKEDIN: 1.2,
                CommunicationChannel.GHL_TASK: 0.8
            }.get(tp.get('channel', CommunicationChannel.EMAIL), 1.0)

            # Engagement type multiplier
            engagement_multiplier = {
                EngagementType.APPOINTMENT_SCHEDULED: 3.0,
                EngagementType.PHONE_ANSWERED: 2.5,
                EngagementType.EMAIL_REPLIED: 2.0,
                EngagementType.EMAIL_CLICKED: 1.5,
                EngagementType.SMS_RESPONDED: 2.0,
                EngagementType.PROPERTY_VIEWED: 1.8,
                EngagementType.EMAIL_OPENED: 1.0
            }.get(tp.get('engagement_type', EngagementType.EMAIL_OPENED), 1.0)

            # Time proximity to conversion (higher weight for recent interactions)
            days_ago = (datetime.now() - tp['occurred_at']).days
            time_weight = 1.0 / (1.0 + days_ago * 0.1)  # Decay factor

            # Calculate final weight
            final_weight = base_weight * channel_multiplier * engagement_multiplier * time_weight
            attribution[tp['touchpoint_id']] = final_weight
            total_weight += final_weight

        # Normalize to total value
        if total_weight > 0:
            for touchpoint_id in attribution:
                attribution[touchpoint_id] = (attribution[touchpoint_id] / total_weight) * total_value

        return attribution

    # Support Methods

    async def _get_lead_touchpoint_history(self, lead_id: str) -> List[Dict[str, Any]]:
        """Get chronological touchpoint history for a lead."""
        # In production, this would query the database
        # For demo, return mock data
        mock_touchpoints = [
            {
                'touchpoint_id': f'tp_001_{lead_id}',
                'campaign_id': f'camp_{lead_id}',
                'channel': CommunicationChannel.EMAIL,
                'engagement_type': EngagementType.EMAIL_OPENED,
                'occurred_at': datetime.now() - timedelta(days=7)
            },
            {
                'touchpoint_id': f'tp_002_{lead_id}',
                'campaign_id': f'camp_{lead_id}',
                'channel': CommunicationChannel.EMAIL,
                'engagement_type': EngagementType.EMAIL_CLICKED,
                'occurred_at': datetime.now() - timedelta(days=5)
            },
            {
                'touchpoint_id': f'tp_003_{lead_id}',
                'campaign_id': f'camp_{lead_id}',
                'channel': CommunicationChannel.SMS,
                'engagement_type': EngagementType.SMS_RESPONDED,
                'occurred_at': datetime.now() - timedelta(days=2)
            }
        ]

        return mock_touchpoints

    async def _calculate_conversion_probability(self, touchpoint_history: List[Dict[str, Any]]) -> float:
        """Calculate conversion probability based on touchpoint history."""
        if not touchpoint_history:
            return 0.0

        # Simple heuristic based on engagement level and recency
        base_probability = 0.2
        engagement_bonus = len(touchpoint_history) * 0.1
        recency_bonus = min(0.3, 0.1 / ((datetime.now() - max(tp['occurred_at'] for tp in touchpoint_history)).days + 1))

        return min(base_probability + engagement_bonus + recency_bonus, 1.0)

    async def _calculate_time_to_conversion(self, touchpoint_history: List[Dict[str, Any]]) -> timedelta:
        """Calculate time from first touch to conversion."""
        if not touchpoint_history:
            return timedelta(0)

        first_touch = min(tp['occurred_at'] for tp in touchpoint_history)
        return datetime.now() - first_touch

    async def _create_organic_conversion_event(
        self,
        lead_id: str,
        event_type: ConversionEventType,
        event_value: Optional[float],
        metadata: Optional[Dict[str, Any]]
    ) -> ConversionEvent:
        """Create conversion event for organic (non-attributed) conversions."""
        return ConversionEvent(
            event_id=f"organic_{lead_id}_{int(datetime.now().timestamp())}",
            lead_id=lead_id,
            event_type=event_type,
            event_value=event_value or self.conversion_values.get(event_type, 0),
            occurred_at=datetime.now(),
            attributed_touchpoints=[],
            attribution_weights={},
            conversion_probability=0.1,  # Lower probability for organic
            time_to_conversion=timedelta(0),
            metadata=metadata or {"source": "organic"}
        )

    async def _update_touchpoint_attributions(
        self,
        conversion_event: ConversionEvent,
        attribution_results: Dict[AttributionModel, Dict[str, float]]
    ):
        """Update touchpoint attribution records."""
        # Use data-driven attribution as primary model
        primary_attribution = attribution_results.get(AttributionModel.DATA_DRIVEN, {})

        for touchpoint_id, attributed_value in primary_attribution.items():
            if attributed_value > 0:
                touchpoint_attribution = TouchpointAttribution(
                    touchpoint_id=touchpoint_id,
                    campaign_id=conversion_event.attributed_touchpoints[0] if conversion_event.attributed_touchpoints else "unknown",
                    lead_id=conversion_event.lead_id,
                    channel=CommunicationChannel.EMAIL,  # Would get from touchpoint data
                    engagement_type=EngagementType.EMAIL_OPENED,  # Would get from touchpoint data
                    occurred_at=conversion_event.occurred_at,
                    attributed_revenue=attributed_value,
                    attribution_weight=attributed_value / conversion_event.event_value if conversion_event.event_value > 0 else 0,
                    attribution_model=AttributionModel.DATA_DRIVEN,
                    conversion_assists=1 if attributed_value < conversion_event.event_value else 0,
                    final_conversions=1 if attributed_value == conversion_event.event_value else 0,
                    incremental_value=attributed_value * 0.1  # Estimated incremental value
                )

                self.touchpoint_attributions.append(touchpoint_attribution)

    async def _update_campaign_roi_metrics(self, conversion_event: ConversionEvent):
        """Update campaign-level ROI metrics."""
        # In production, this would aggregate all conversions for the campaign
        # For demo, create/update mock campaign ROI

        campaign_id = conversion_event.attributed_touchpoints[0] if conversion_event.attributed_touchpoints else "organic"

        if campaign_id not in self.campaign_rois:
            # Create new campaign ROI record
            self.campaign_rois[campaign_id] = CampaignROI(
                campaign_id=campaign_id,
                total_investment=250.0,  # Mock investment
                total_revenue=conversion_event.event_value,
                roi_percentage=(conversion_event.event_value - 250.0) / 250.0 * 100,
                roas=conversion_event.event_value / 250.0,
                conversion_rate=0.25,  # Mock conversion rate
                average_deal_size=conversion_event.event_value,
                customer_lifetime_value=conversion_event.event_value * 1.5,
                cost_per_conversion=250.0,
                attribution_by_model={
                    AttributionModel.DATA_DRIVEN.value: conversion_event.event_value,
                    AttributionModel.FIRST_TOUCH.value: conversion_event.event_value,
                    AttributionModel.LAST_TOUCH.value: conversion_event.event_value
                },
                time_to_roi=conversion_event.time_to_conversion,
                confidence_interval=(0.8, 1.2)
            )
        else:
            # Update existing campaign ROI
            existing_roi = self.campaign_rois[campaign_id]
            existing_roi.total_revenue += conversion_event.event_value
            existing_roi.roi_percentage = (existing_roi.total_revenue - existing_roi.total_investment) / existing_roi.total_investment * 100
            existing_roi.roas = existing_roi.total_revenue / existing_roi.total_investment

    # Analytics and Reporting

    async def calculate_campaign_roi(self, campaign_id: str) -> CampaignROI:
        """Calculate comprehensive ROI for a specific campaign."""
        if campaign_id in self.campaign_rois:
            return self.campaign_rois[campaign_id]

        # Calculate from scratch if not cached
        campaign_conversions = [ce for ce in self.conversion_events if campaign_id in ce.attributed_touchpoints]
        campaign_touchpoints = [ta for ta in self.touchpoint_attributions if ta.campaign_id == campaign_id]

        total_revenue = sum(ce.event_value for ce in campaign_conversions)
        total_investment = await self._calculate_campaign_investment(campaign_id)

        roi = CampaignROI(
            campaign_id=campaign_id,
            total_investment=total_investment,
            total_revenue=total_revenue,
            roi_percentage=(total_revenue - total_investment) / total_investment * 100 if total_investment > 0 else 0,
            roas=total_revenue / total_investment if total_investment > 0 else 0,
            conversion_rate=await self._calculate_campaign_conversion_rate(campaign_id),
            average_deal_size=total_revenue / len(campaign_conversions) if campaign_conversions else 0,
            customer_lifetime_value=total_revenue * 1.5,  # Estimated CLV
            cost_per_conversion=total_investment / len(campaign_conversions) if campaign_conversions else 0,
            attribution_by_model=await self._calculate_attribution_by_model(campaign_conversions),
            time_to_roi=await self._calculate_average_time_to_roi(campaign_conversions),
            confidence_interval=await self._calculate_roi_confidence_interval(campaign_id)
        )

        self.campaign_rois[campaign_id] = roi
        return roi

    async def _calculate_campaign_investment(self, campaign_id: str) -> float:
        """Calculate total investment for a campaign."""
        # In production, sum up all costs: staff time, platform costs, etc.
        campaign_touchpoints = [ta for ta in self.touchpoint_attributions if ta.campaign_id == campaign_id]

        total_cost = 0.0
        for touchpoint in campaign_touchpoints:
            channel_cost = self.channel_costs.get(touchpoint.channel, 0.10)
            total_cost += channel_cost

        # Add operational overhead (30%)
        operational_overhead = total_cost * 0.3
        return total_cost + operational_overhead

    async def _calculate_campaign_conversion_rate(self, campaign_id: str) -> float:
        """Calculate conversion rate for a campaign."""
        # Mock calculation
        return 0.25  # 25% conversion rate

    async def _calculate_attribution_by_model(self, conversions: List[ConversionEvent]) -> Dict[str, float]:
        """Calculate revenue attribution across different models."""
        attribution_totals = {model.value: 0.0 for model in AttributionModel}

        for conversion in conversions:
            # In production, would recalculate with each model
            attribution_totals[AttributionModel.DATA_DRIVEN.value] += conversion.event_value

        return attribution_totals

    async def _calculate_average_time_to_roi(self, conversions: List[ConversionEvent]) -> Optional[timedelta]:
        """Calculate average time to ROI for conversions."""
        if not conversions:
            return None

        total_time = sum((ce.time_to_conversion for ce in conversions), timedelta(0))
        return total_time / len(conversions)

    async def _calculate_roi_confidence_interval(self, campaign_id: str) -> Tuple[float, float]:
        """Calculate confidence interval for ROI estimate."""
        # Simplified confidence interval calculation
        roi = self.campaign_rois.get(campaign_id)
        if not roi:
            return (0.0, 0.0)

        margin_of_error = roi.roi_percentage * 0.15  # ±15% margin
        return (roi.roi_percentage - margin_of_error, roi.roi_percentage + margin_of_error)

    async def analyze_channel_performance(self) -> List[ChannelPerformance]:
        """Analyze performance across all communication channels."""
        channel_data = {}

        # Group touchpoints by channel
        for touchpoint in self.touchpoint_attributions:
            channel = touchpoint.channel
            if channel not in channel_data:
                channel_data[channel] = {
                    'touchpoints': [],
                    'revenue': 0.0,
                    'conversions': 0
                }

            channel_data[channel]['touchpoints'].append(touchpoint)
            channel_data[channel]['revenue'] += touchpoint.attributed_revenue
            if touchpoint.final_conversions > 0:
                channel_data[channel]['conversions'] += 1

        # Calculate performance metrics
        channel_performances = []
        for channel, data in channel_data.items():
            touchpoint_count = len(data['touchpoints'])
            total_cost = touchpoint_count * self.channel_costs.get(channel, 0.10)

            performance = ChannelPerformance(
                channel=channel,
                total_touchpoints=touchpoint_count,
                total_revenue=data['revenue'],
                conversion_rate=data['conversions'] / touchpoint_count if touchpoint_count > 0 else 0,
                cost_per_touchpoint=self.channel_costs.get(channel, 0.10),
                roi_percentage=(data['revenue'] - total_cost) / total_cost * 100 if total_cost > 0 else 0,
                average_time_to_conversion=timedelta(days=5),  # Mock data
                best_performing_sequences=await self._get_best_sequences_for_channel(channel),
                optimization_recommendations=await self._get_channel_optimization_recommendations(channel, data)
            )

            channel_performances.append(performance)

        return channel_performances

    async def _get_best_sequences_for_channel(self, channel: CommunicationChannel) -> List[str]:
        """Get best performing sequences for a channel."""
        # Mock data - in production, analyze actual performance
        return [
            f"First-Time Buyer Journey ({channel.value})",
            f"Investment Analysis ({channel.value})",
            f"Market Update ({channel.value})"
        ]

    async def _get_channel_optimization_recommendations(
        self,
        channel: CommunicationChannel,
        data: Dict[str, Any]
    ) -> List[str]:
        """Generate optimization recommendations for a channel."""
        recommendations = []

        conversion_rate = data['conversions'] / len(data['touchpoints']) if data['touchpoints'] else 0
        revenue_per_touchpoint = data['revenue'] / len(data['touchpoints']) if data['touchpoints'] else 0

        if conversion_rate < 0.15:
            recommendations.append(f"Improve {channel.value} message content and timing")

        if revenue_per_touchpoint < 50:
            recommendations.append(f"Focus {channel.value} on higher-value prospects")

        if channel == CommunicationChannel.EMAIL and conversion_rate > 0.25:
            recommendations.append("Consider increasing email frequency for this high-performing channel")

        if channel == CommunicationChannel.PHONE and conversion_rate < 0.4:
            recommendations.append("Improve phone script and agent training")

        return recommendations

    # Advanced Analytics

    async def generate_attribution_comparison_report(self) -> Dict[str, Any]:
        """Generate comprehensive attribution model comparison."""
        model_comparison = {}

        for model in AttributionModel:
            total_attributed = sum(
                ce.event_value for ce in self.conversion_events
                # In production, recalculate with each model
            )

            model_comparison[model.value] = {
                "total_attributed_revenue": total_attributed,
                "attribution_percentage": total_attributed / sum(ce.event_value for ce in self.conversion_events) * 100 if self.conversion_events else 0,
                "average_attribution_per_conversion": total_attributed / len(self.conversion_events) if self.conversion_events else 0,
                "use_case": self._get_attribution_model_use_case(model)
            }

        return {
            "model_comparison": model_comparison,
            "recommended_model": AttributionModel.DATA_DRIVEN.value,
            "total_conversions": len(self.conversion_events),
            "total_revenue": sum(ce.event_value for ce in self.conversion_events),
            "attribution_variance": await self._calculate_attribution_variance()
        }

    def _get_attribution_model_use_case(self, model: AttributionModel) -> str:
        """Get use case description for attribution model."""
        use_cases = {
            AttributionModel.FIRST_TOUCH: "Best for brand awareness and top-of-funnel analysis",
            AttributionModel.LAST_TOUCH: "Good for direct response and closing analysis",
            AttributionModel.LINEAR: "Fair for balanced view across customer journey",
            AttributionModel.TIME_DECAY: "Useful when recent interactions are more important",
            AttributionModel.POSITION_BASED: "Good for valuing introduction and closing touches",
            AttributionModel.DATA_DRIVEN: "Most accurate for optimizing overall campaign performance"
        }
        return use_cases.get(model, "Unknown use case")

    async def _calculate_attribution_variance(self) -> float:
        """Calculate variance in attribution across models."""
        if len(self.conversion_events) < 2:
            return 0.0

        # Simplified variance calculation
        revenues = [ce.event_value for ce in self.conversion_events]
        mean_revenue = np.mean(revenues)
        variance = np.var(revenues)

        return float(variance / mean_revenue if mean_revenue > 0 else 0)

    # System Health and Performance

    async def get_system_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the attribution system."""
        return {
            "total_conversion_events": len(self.conversion_events),
            "total_touchpoint_attributions": len(self.touchpoint_attributions),
            "total_campaigns_tracked": len(self.campaign_rois),
            "attribution_models_active": len(self.attribution_models),
            "average_time_to_conversion_days": float(
                np.mean([(ce.time_to_conversion.days) for ce in self.conversion_events])
                if self.conversion_events else 0
            ),
            "total_attributed_revenue": sum(ce.event_value for ce in self.conversion_events),
            "average_conversion_value": (
                sum(ce.event_value for ce in self.conversion_events) / len(self.conversion_events)
                if self.conversion_events else 0
            ),
            "cache_hit_rate": 0.85,  # Mock cache performance
            "attribution_processing_time_ms": 150,  # Mock processing time
            "data_quality_score": 0.92  # Mock data quality score
        }

    async def optimize_attribution_models(self) -> Dict[str, Any]:
        """Optimize attribution models based on performance data."""
        optimization_results = {
            "recommendations": [],
            "model_adjustments": {},
            "expected_improvement": 0.0
        }

        # Analyze current performance
        current_variance = await self._calculate_attribution_variance()

        if current_variance > 0.3:
            optimization_results["recommendations"].append(
                "High attribution variance detected - consider using position-based model"
            )

        if len(self.conversion_events) > 50:
            optimization_results["recommendations"].append(
                "Sufficient data for data-driven attribution - recommend switching to ML-based model"
            )

        # Suggest model parameters
        if len(self.conversion_events) > 20:
            avg_time_to_conversion = np.mean([ce.time_to_conversion.days for ce in self.conversion_events])
            if avg_time_to_conversion > 14:
                optimization_results["model_adjustments"]["time_decay_rate"] = 0.3
                optimization_results["recommendations"].append(
                    "Long conversion cycles detected - use slower time decay rate"
                )

        optimization_results["expected_improvement"] = 0.15  # Mock improvement estimate

        return optimization_results


# Export the main class and data models
__all__ = [
    'ROIAttributionSystem',
    'ConversionEvent',
    'TouchpointAttribution',
    'CampaignROI',
    'ChannelPerformance',
    'ConversionEventType',
    'AttributionModel'
]