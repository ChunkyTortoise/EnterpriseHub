"""
Value Justification API Routes

FastAPI endpoints for the Dynamic Value Justification Engine, providing REST API
access to real-time value tracking, ROI calculations, pricing optimization,
and value communication capabilities.

Key Endpoints:
- GET /api/v1/value/track/{agent_id} - Real-time value tracking
- GET /api/v1/roi/calculate/{agent_id} - ROI calculation
- POST /api/v1/pricing/optimize - Dynamic pricing optimization
- GET /api/v1/communication/package/{agent_id}/{client_id} - Value communication
- POST /api/v1/justification/document - Generate justification documentation
- GET /api/v1/dashboard/data/{agent_id} - Dashboard data for UI
- POST /api/v1/messages/generate - Generate value messages

Business Impact:
- Enable seamless integration with external systems
- Support real-time value demonstration workflows
- Provide programmatic access to value calculation engine
- Enable automated reporting and communication

Author: Claude Code Agent
Created: 2026-01-18
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ghl_real_estate_ai.services.dynamic_value_justification_engine import (
    RealTimeROICalculation,
    ValueTrackingStatus,
    get_dynamic_value_justification_engine,
)
from ghl_real_estate_ai.services.value_communication_templates import (
    CommunicationStyle,
    MessageType,
    get_value_communication_templates,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/value-justification", tags=["Value Justification"])


# Request/Response Models
class ValueTrackingRequest(BaseModel):
    """Request model for value tracking"""

    agent_id: str = Field(..., description="Agent identifier")
    client_id: Optional[str] = Field(None, description="Client identifier")
    transaction_id: Optional[str] = Field(None, description="Transaction identifier")
    value_data: Optional[Dict[str, Any]] = Field(None, description="Additional value data")


class ValueTrackingResponse(BaseModel):
    """Response model for value tracking"""

    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    value_metrics: List[Dict[str, Any]] = Field(..., description="Tracked value metrics")
    total_value: float = Field(..., description="Total value across all dimensions")
    verification_rate: float = Field(..., description="Overall verification rate")
    timestamp: datetime = Field(..., description="Response timestamp")


class ROICalculationRequest(BaseModel):
    """Request model for ROI calculation"""

    agent_id: str = Field(..., description="Agent identifier")
    client_id: Optional[str] = Field(None, description="Client identifier")
    transaction_id: Optional[str] = Field(None, description="Transaction identifier")
    period_days: int = Field(365, description="Period for calculation in days", ge=1, le=1095)


class ROICalculationResponse(BaseModel):
    """Response model for ROI calculation"""

    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    roi_calculation: Dict[str, Any] = Field(..., description="Complete ROI calculation")
    summary: Dict[str, Any] = Field(..., description="ROI summary metrics")
    timestamp: datetime = Field(..., description="Response timestamp")


class PricingOptimizationRequest(BaseModel):
    """Request model for pricing optimization"""

    agent_id: str = Field(..., description="Agent identifier")
    target_roi_percentage: Optional[float] = Field(None, description="Target ROI percentage", ge=0, le=1000)
    market_conditions: Optional[Dict[str, Any]] = Field(None, description="Current market conditions")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Pricing constraints")


class PricingOptimizationResponse(BaseModel):
    """Response model for pricing optimization"""

    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    pricing_recommendation: Dict[str, Any] = Field(..., description="Pricing recommendation")
    justification: Dict[str, Any] = Field(..., description="Pricing justification")
    implementation_plan: Dict[str, Any] = Field(..., description="Implementation recommendations")
    timestamp: datetime = Field(..., description="Response timestamp")


class ValueCommunicationRequest(BaseModel):
    """Request model for value communication package"""

    agent_id: str = Field(..., description="Agent identifier")
    client_id: str = Field(..., description="Client identifier")
    communication_type: str = Field("comprehensive", description="Type of communication package")
    personalization_preferences: Optional[Dict[str, Any]] = Field(None, description="Personalization preferences")


class ValueCommunicationResponse(BaseModel):
    """Response model for value communication package"""

    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    communication_package: Dict[str, Any] = Field(..., description="Value communication package")
    delivery_options: List[str] = Field(..., description="Available delivery methods")
    timestamp: datetime = Field(..., description="Response timestamp")


class JustificationDocumentRequest(BaseModel):
    """Request model for justification documentation"""

    agent_id: str = Field(..., description="Agent identifier")
    client_id: Optional[str] = Field(None, description="Client identifier")
    transaction_id: Optional[str] = Field(None, description="Transaction identifier")
    include_verification: bool = Field(True, description="Include verification details")
    include_competitive_analysis: bool = Field(True, description="Include competitive analysis")
    document_format: str = Field("comprehensive", description="Document format type")


class JustificationDocumentResponse(BaseModel):
    """Response model for justification documentation"""

    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    documentation: Dict[str, Any] = Field(..., description="Complete justification documentation")
    export_options: List[str] = Field(..., description="Available export formats")
    timestamp: datetime = Field(..., description="Response timestamp")


class MessageGenerationRequest(BaseModel):
    """Request model for message generation"""

    template_id: str = Field(..., description="Message template identifier")
    agent_id: str = Field(..., description="Agent identifier")
    client_id: str = Field(..., description="Client identifier")
    personalization_data: Optional[Dict[str, Any]] = Field(None, description="Additional personalization data")
    communication_style: Optional[str] = Field(None, description="Preferred communication style")
    delivery_method: str = Field("email", description="Delivery method")


class MessageGenerationResponse(BaseModel):
    """Response model for message generation"""

    success: bool = Field(..., description="Success status")
    message: str = Field(..., description="Response message")
    generated_message: Dict[str, Any] = Field(..., description="Generated message content")
    personalization_details: Dict[str, Any] = Field(..., description="Personalization details applied")
    timestamp: datetime = Field(..., description="Response timestamp")


# Dependencies
async def get_value_engine():
    """Dependency to get value justification engine"""
    return get_dynamic_value_justification_engine()


async def get_communication_templates():
    """Dependency to get value communication templates"""
    return get_value_communication_templates()


# Utility functions
def serialize_decimal(obj):
    """Convert Decimal objects to float for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: serialize_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_decimal(item) for item in obj]
    return obj


def convert_roi_calculation_to_dict(roi_calc: RealTimeROICalculation) -> Dict[str, Any]:
    """Convert ROI calculation to dictionary with serializable values"""
    data = {
        "calculation_id": roi_calc.calculation_id,
        "agent_id": roi_calc.agent_id,
        "client_id": roi_calc.client_id,
        "transaction_id": roi_calc.transaction_id,
        "service_fees_paid": float(roi_calc.service_fees_paid),
        "additional_costs": float(roi_calc.additional_costs),
        "total_investment": float(roi_calc.total_investment),
        "financial_value": float(roi_calc.financial_value),
        "time_value": float(roi_calc.time_value),
        "risk_mitigation_value": float(roi_calc.risk_mitigation_value),
        "experience_value": float(roi_calc.experience_value),
        "information_advantage_value": float(roi_calc.information_advantage_value),
        "relationship_value": float(roi_calc.relationship_value),
        "total_value_delivered": float(roi_calc.total_value_delivered),
        "net_benefit": float(roi_calc.net_benefit),
        "roi_percentage": float(roi_calc.roi_percentage),
        "roi_multiple": float(roi_calc.roi_multiple),
        "payback_period_days": roi_calc.payback_period_days,
        "value_per_dollar": float(roi_calc.value_per_dollar),
        "vs_discount_broker": serialize_decimal(roi_calc.vs_discount_broker),
        "vs_traditional_agent": serialize_decimal(roi_calc.vs_traditional_agent),
        "vs_fsbo": serialize_decimal(roi_calc.vs_fsbo),
        "overall_confidence": roi_calc.overall_confidence,
        "verification_rate": roi_calc.verification_rate,
        "calculation_timestamp": roi_calc.calculation_timestamp.isoformat(),
        "period_start": roi_calc.period_start.isoformat(),
        "period_end": roi_calc.period_end.isoformat(),
        "projected_annual_value": float(roi_calc.projected_annual_value) if roi_calc.projected_annual_value else None,
        "projected_lifetime_value": float(roi_calc.projected_lifetime_value)
        if roi_calc.projected_lifetime_value
        else None,
    }
    return data


# API Endpoints


@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint for value justification API"""
    return {
        "status": "healthy",
        "service": "Dynamic Value Justification Engine",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/value/track", response_model=ValueTrackingResponse)
async def track_real_time_value(request: ValueTrackingRequest, value_engine=Depends(get_value_engine)):
    """
    Track real-time value across all dimensions

    This endpoint tracks value delivery in real-time across financial value,
    time value, risk mitigation, experience value, information advantage,
    and relationship value dimensions.
    """
    try:
        logger.info(f"Tracking real-time value for agent {request.agent_id}")

        # Track value metrics
        value_metrics = await value_engine.track_real_time_value(
            agent_id=request.agent_id,
            client_id=request.client_id,
            transaction_id=request.transaction_id,
            value_data=request.value_data,
        )

        # Convert metrics to serializable format
        metrics_data = []
        total_value = 0.0
        verified_metrics = 0

        for metric in value_metrics:
            metric_data = {
                "metric_id": metric.metric_id,
                "dimension": metric.dimension.value,
                "description": metric.description,
                "value_amount": float(metric.value_amount),
                "tracking_status": metric.tracking_status.value,
                "verification_confidence": metric.verification_confidence,
                "supporting_evidence": metric.supporting_evidence,
                "calculation_method": metric.calculation_method,
                "timestamp": metric.timestamp.isoformat(),
                "client_id": metric.client_id,
                "transaction_id": metric.transaction_id,
                "competitive_benchmark": metric.competitive_benchmark,
            }
            metrics_data.append(metric_data)
            total_value += float(metric.value_amount) * metric.verification_confidence

            if metric.tracking_status == ValueTrackingStatus.VERIFIED:
                verified_metrics += 1

        verification_rate = verified_metrics / len(value_metrics) if value_metrics else 0.0

        return ValueTrackingResponse(
            success=True,
            message=f"Successfully tracked {len(value_metrics)} value metrics",
            value_metrics=metrics_data,
            total_value=total_value,
            verification_rate=verification_rate,
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error tracking value: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/roi/calculate", response_model=ROICalculationResponse)
async def calculate_real_time_roi(request: ROICalculationRequest, value_engine=Depends(get_value_engine)):
    """
    Calculate comprehensive real-time ROI with all value dimensions

    This endpoint calculates real-time ROI including investment analysis,
    value breakdown by dimension, competitive comparisons, and confidence metrics.
    """
    try:
        logger.info(f"Calculating ROI for agent {request.agent_id}")

        # Calculate ROI
        roi_calculation = await value_engine.calculate_real_time_roi(
            agent_id=request.agent_id,
            client_id=request.client_id,
            transaction_id=request.transaction_id,
            period_days=request.period_days,
        )

        # Convert to serializable format
        roi_data = convert_roi_calculation_to_dict(roi_calculation)

        # Create summary
        summary = {
            "roi_percentage": float(roi_calculation.roi_percentage),
            "total_value_delivered": float(roi_calculation.total_value_delivered),
            "total_investment": float(roi_calculation.total_investment),
            "net_benefit": float(roi_calculation.net_benefit),
            "value_per_dollar": float(roi_calculation.value_per_dollar),
            "verification_rate": roi_calculation.verification_rate,
            "confidence_level": roi_calculation.overall_confidence,
            "payback_period_days": roi_calculation.payback_period_days,
        }

        return ROICalculationResponse(
            success=True,
            message=f"Successfully calculated ROI: {roi_calculation.roi_percentage:.1f}%",
            roi_calculation=roi_data,
            summary=summary,
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error calculating ROI: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/pricing/optimize", response_model=PricingOptimizationResponse)
async def optimize_dynamic_pricing(request: PricingOptimizationRequest, value_engine=Depends(get_value_engine)):
    """
    Generate dynamic pricing recommendations based on value delivery

    This endpoint optimizes pricing based on demonstrated value, performance
    metrics, market conditions, and target ROI requirements.
    """
    try:
        logger.info(f"Optimizing pricing for agent {request.agent_id}")

        # Optimize pricing
        pricing_recommendation = await value_engine.optimize_dynamic_pricing(
            agent_id=request.agent_id,
            target_roi_percentage=request.target_roi_percentage,
            market_conditions=request.market_conditions,
        )

        # Convert to serializable format
        recommendation_data = {
            "recommendation_id": pricing_recommendation.recommendation_id,
            "agent_id": pricing_recommendation.agent_id,
            "current_commission_rate": float(pricing_recommendation.current_commission_rate),
            "recommended_commission_rate": float(pricing_recommendation.recommended_commission_rate),
            "pricing_tier": pricing_recommendation.pricing_tier.value,
            "value_based_rate": float(pricing_recommendation.value_based_rate),
            "performance_multiplier": float(pricing_recommendation.performance_multiplier),
            "market_premium_justified": float(pricing_recommendation.market_premium_justified),
            "competitive_positioning": pricing_recommendation.competitive_positioning,
            "guaranteed_roi_percentage": float(pricing_recommendation.guaranteed_roi_percentage),
            "value_guarantee": float(pricing_recommendation.value_guarantee),
            "risk_adjusted_pricing": float(pricing_recommendation.risk_adjusted_pricing),
            "confidence_level": pricing_recommendation.confidence_level,
            "implementation_priority": pricing_recommendation.implementation_priority,
            "generated_at": pricing_recommendation.generated_at.isoformat(),
        }

        # Create justification
        justification = {
            "pricing_tier": pricing_recommendation.pricing_tier.value,
            "value_justification": f"Recommended {float(pricing_recommendation.recommended_commission_rate) * 100:.1f}% rate based on demonstrated value delivery",
            "roi_guarantee": f"{float(pricing_recommendation.guaranteed_roi_percentage):.0f}% ROI guaranteed",
            "competitive_position": pricing_recommendation.competitive_positioning,
            "confidence_level": f"{pricing_recommendation.confidence_level:.1%}",
        }

        # Create implementation plan
        implementation_plan = {
            "rollout_strategy": pricing_recommendation.rollout_strategy,
            "communication_plan": pricing_recommendation.client_communication_plan,
            "success_metrics": serialize_decimal(pricing_recommendation.success_metrics),
            "review_date": pricing_recommendation.review_date.isoformat(),
            "priority": pricing_recommendation.implementation_priority,
        }

        return PricingOptimizationResponse(
            success=True,
            message=f"Generated pricing recommendation: {pricing_recommendation.pricing_tier.value} tier",
            pricing_recommendation=recommendation_data,
            justification=justification,
            implementation_plan=implementation_plan,
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error optimizing pricing: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/communication/package/{agent_id}/{client_id}", response_model=ValueCommunicationResponse)
async def generate_value_communication_package(
    agent_id: str,
    client_id: str,
    communication_type: str = Query("comprehensive", description="Type of communication package"),
    value_engine=Depends(get_value_engine),
):
    """
    Generate client-facing value communication package

    This endpoint creates personalized value communication packages with
    executive summaries, value breakdowns, competitive advantages, and
    evidence documentation.
    """
    try:
        logger.info(f"Generating value communication package for client {client_id}")

        # Generate communication package
        communication_package = await value_engine.generate_value_communication_package(
            agent_id=agent_id, client_id=client_id, communication_type=communication_type
        )

        # Convert to serializable format
        package_data = {
            "package_id": communication_package.package_id,
            "agent_id": communication_package.agent_id,
            "client_id": communication_package.client_id,
            "executive_summary": communication_package.executive_summary,
            "key_value_highlights": communication_package.key_value_highlights,
            "roi_headline": communication_package.roi_headline,
            "value_dimensions": serialize_decimal(communication_package.value_dimensions),
            "competitive_advantages": communication_package.competitive_advantages,
            "success_metrics": serialize_decimal(communication_package.success_metrics),
            "verification_documents": communication_package.verification_documents,
            "client_testimonials": communication_package.client_testimonials,
            "success_stories": communication_package.success_stories,
            "performance_certifications": communication_package.performance_certifications,
            "client_specific_benefits": communication_package.client_specific_benefits,
            "customized_messaging": communication_package.customized_messaging,
            "generated_at": communication_package.generated_at.isoformat(),
            "expires_at": communication_package.expires_at.isoformat(),
        }

        # Define delivery options
        delivery_options = ["email", "presentation", "web_dashboard", "pdf_report", "mobile_app"]

        return ValueCommunicationResponse(
            success=True,
            message="Successfully generated value communication package",
            communication_package=package_data,
            delivery_options=delivery_options,
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error generating communication package: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/justification/document", response_model=JustificationDocumentResponse)
async def create_justification_documentation(
    request: JustificationDocumentRequest, value_engine=Depends(get_value_engine)
):
    """
    Create comprehensive justification documentation with evidence

    This endpoint creates complete justification documentation including
    evidence collection, performance analysis, value verification,
    market positioning, and compliance documentation.
    """
    try:
        logger.info(f"Creating justification documentation for agent {request.agent_id}")

        # Create documentation
        documentation = await value_engine.create_justification_documentation(
            agent_id=request.agent_id, client_id=request.client_id, transaction_id=request.transaction_id
        )

        # Add request-specific filtering
        if not request.include_verification:
            documentation.pop("value_verification", None)

        if not request.include_competitive_analysis:
            documentation.pop("market_positioning", None)

        # Define export options
        export_options = ["pdf", "word", "html", "json", "excel", "presentation"]

        return JustificationDocumentResponse(
            success=True,
            message="Successfully created justification documentation",
            documentation=documentation,
            export_options=export_options,
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error creating documentation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/dashboard/data/{agent_id}")
async def get_dashboard_data(
    agent_id: str,
    client_id: Optional[str] = Query(None, description="Client identifier for client-specific view"),
    period_days: int = Query(30, description="Period for dashboard data", ge=1, le=365),
    value_engine=Depends(get_value_engine),
):
    """
    Get comprehensive dashboard data for real-time value dashboard

    This endpoint provides all data needed for the real-time value dashboard
    including ROI calculations, value tracking, competitive analysis,
    and verification status.
    """
    try:
        logger.info(f"Getting dashboard data for agent {agent_id}")

        # Get comprehensive data
        roi_calculation, value_metrics = await asyncio.gather(
            value_engine.calculate_real_time_roi(agent_id, client_id, period_days=period_days),
            value_engine.track_real_time_value(agent_id, client_id),
        )

        # Prepare dashboard data
        dashboard_data = {
            "agent_id": agent_id,
            "client_id": client_id,
            "period_days": period_days,
            "last_updated": datetime.now().isoformat(),
            # ROI Summary
            "roi_summary": {
                "roi_percentage": float(roi_calculation.roi_percentage),
                "total_value_delivered": float(roi_calculation.total_value_delivered),
                "total_investment": float(roi_calculation.total_investment),
                "net_benefit": float(roi_calculation.net_benefit),
                "value_per_dollar": float(roi_calculation.value_per_dollar),
                "verification_rate": roi_calculation.verification_rate,
                "confidence_level": roi_calculation.overall_confidence,
            },
            # Value Breakdown
            "value_breakdown": {
                "financial_value": float(roi_calculation.financial_value),
                "time_value": float(roi_calculation.time_value),
                "risk_mitigation_value": float(roi_calculation.risk_mitigation_value),
                "experience_value": float(roi_calculation.experience_value),
                "information_advantage_value": float(roi_calculation.information_advantage_value),
                "relationship_value": float(roi_calculation.relationship_value),
            },
            # Competitive Analysis
            "competitive_analysis": {
                "vs_discount_broker": serialize_decimal(roi_calculation.vs_discount_broker),
                "vs_traditional_agent": serialize_decimal(roi_calculation.vs_traditional_agent),
                "vs_fsbo": serialize_decimal(roi_calculation.vs_fsbo),
            },
            # Value Metrics
            "value_metrics_count": len(value_metrics),
            "verified_metrics": len([m for m in value_metrics if m.tracking_status == ValueTrackingStatus.VERIFIED]),
            # Performance Indicators
            "performance_indicators": {
                "payback_period_days": roi_calculation.payback_period_days,
                "projected_annual_value": float(roi_calculation.projected_annual_value)
                if roi_calculation.projected_annual_value
                else None,
                "calculation_timestamp": roi_calculation.calculation_timestamp.isoformat(),
            },
        }

        return JSONResponse(
            content={
                "success": True,
                "message": "Dashboard data retrieved successfully",
                "data": dashboard_data,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/messages/generate", response_model=MessageGenerationResponse)
async def generate_value_message(
    request: MessageGenerationRequest, communication_templates=Depends(get_communication_templates)
):
    """
    Generate personalized value communication message

    This endpoint generates personalized messages using predefined templates
    for ROI reports, pricing justifications, success stories, and other
    value communication needs.
    """
    try:
        logger.info(f"Generating message for client {request.client_id}")

        # Generate personalized message
        message = await communication_templates.generate_personalized_message(
            template_id=request.template_id,
            agent_id=request.agent_id,
            client_id=request.client_id,
            additional_data=request.personalization_data,
        )

        # Convert to serializable format
        message_data = {
            "message_id": message.message_id,
            "template_id": message.template_id,
            "agent_id": message.agent_id,
            "client_id": message.client_id,
            "message_type": message.message_type.value,
            "subject_line": message.subject_line,
            "content": message.content,
            "delivery_method": message.delivery_method,
            "generated_at": message.generated_at.isoformat(),
            "expires_at": message.expires_at.isoformat() if message.expires_at else None,
        }

        return MessageGenerationResponse(
            success=True,
            message="Successfully generated personalized message",
            generated_message=message_data,
            personalization_details=message.personalization_data,
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error generating message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/templates/list")
async def list_message_templates(
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    communication_style: Optional[str] = Query(None, description="Filter by communication style"),
    communication_templates=Depends(get_communication_templates),
):
    """
    List available message templates

    This endpoint returns all available message templates with their
    metadata, personalization variables, and use cases.
    """
    try:
        templates = communication_templates.templates

        # Filter templates if requested
        filtered_templates = {}
        for template_id, template in templates.items():
            include_template = True

            if message_type and template.message_type.value != message_type:
                include_template = False

            if communication_style and template.communication_style.value != communication_style:
                include_template = False

            if include_template:
                filtered_templates[template_id] = {
                    "template_id": template.template_id,
                    "title": template.title,
                    "message_type": template.message_type.value,
                    "communication_style": template.communication_style.value,
                    "personalization_variables": template.personalization_variables,
                    "use_cases": template.use_cases,
                    "created_at": template.created_at.isoformat(),
                }

        return JSONResponse(
            content={
                "success": True,
                "message": f"Retrieved {len(filtered_templates)} templates",
                "templates": filtered_templates,
                "available_message_types": [mt.value for mt in MessageType],
                "available_communication_styles": [cs.value for cs in CommunicationStyle],
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Export router
__all__ = ["router"]
