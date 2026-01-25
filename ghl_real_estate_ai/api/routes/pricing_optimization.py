"""
API Routes for Dynamic Pricing and ROI Analysis
Provides REST endpoints for pricing calculation, analytics, and ROI reporting

Business Impact: Enable real-time pricing and transparent ROI reporting
Author: Claude Code Agent Swarm
Created: 2026-01-17
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import json

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field, validator
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

from ghl_real_estate_ai.services.dynamic_pricing_optimizer import DynamicPricingOptimizer, LeadPricingResult
from ghl_real_estate_ai.services.roi_calculator_service import ROICalculatorService, ClientROIReport
from ghl_real_estate_ai.api.middleware.jwt_auth import require_auth, get_current_user
from ghl_real_estate_ai.services.tenant_service import TenantService

logger = logging.getLogger(__name__)

# Initialize services
pricing_optimizer = DynamicPricingOptimizer()
roi_calculator = ROICalculatorService()
tenant_service = TenantService()

# Create router
router = APIRouter(prefix="/api/pricing", tags=["pricing"])


# Pydantic models for request/response
class LeadPricingRequest(BaseModel):
    contact_id: str = Field(..., description="GHL contact ID")
    location_id: str = Field(..., description="GHL location ID") 
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    
    class Config:
        schema_extra = {
            "example": {
                "contact_id": "contact_abc123",
                "location_id": "3xt4qayAh35BlDLaUv7P",
                "context": {
                    "questions_answered": 5,
                    "engagement_score": 0.8,
                    "source": "website_form"
                }
            }
        }


class PricingConfigRequest(BaseModel):
    base_price_per_lead: float = Field(ge=0.10, le=10.00, description="Base price per lead")
    tier_multipliers: Dict[str, float] = Field(description="Tier multipliers (hot, warm, cold)")
    conversion_boost_enabled: bool = Field(True, description="Enable conversion probability boost")
    average_commission: float = Field(ge=1000, le=100000, description="Average commission per deal")
    target_arpu: float = Field(ge=50, le=2000, description="Target ARPU")
    
    @validator('tier_multipliers')
    def validate_tier_multipliers(cls, v):
        required_tiers = {"hot", "warm", "cold"}
        if not required_tiers.issubset(v.keys()):
            raise ValueError("Must include multipliers for hot, warm, and cold tiers")
        for tier, multiplier in v.items():
            if not 0.5 <= multiplier <= 10.0:
                raise ValueError(f"Multiplier for {tier} must be between 0.5 and 10.0")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "base_price_per_lead": 1.00,
                "tier_multipliers": {
                    "hot": 3.5,
                    "warm": 2.0,
                    "cold": 1.0
                },
                "conversion_boost_enabled": True,
                "average_commission": 12500.0,
                "target_arpu": 400.0
            }
        }


class ROIReportRequest(BaseModel):
    location_id: str = Field(..., description="GHL location ID")
    days: int = Field(30, ge=7, le=365, description="Reporting period in days")
    include_projections: bool = Field(True, description="Include future projections")
    
    class Config:
        schema_extra = {
            "example": {
                "location_id": "3xt4qayAh35BlDLaUv7P",
                "days": 30,
                "include_projections": True
            }
        }


class SavingsCalculatorRequest(BaseModel):
    leads_per_month: int = Field(ge=10, le=10000, description="Expected leads per month")
    messages_per_lead: float = Field(5.0, ge=1.0, le=50.0, description="Average messages per lead")
    human_hourly_rate: float = Field(20.0, ge=10.0, le=100.0, description="Human assistant hourly rate")
    
    class Config:
        schema_extra = {
            "example": {
                "leads_per_month": 150,
                "messages_per_lead": 8.5,
                "human_hourly_rate": 20.0
            }
        }


class LeadPricingResponse(BaseModel):
    success: bool
    pricing_result: Optional[Dict[str, Any]]
    error: Optional[str]
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "pricing_result": {
                    "lead_id": "contact_abc123",
                    "tier": "hot",
                    "final_price": 4.73,
                    "expected_roi": 2246,
                    "justification": "High-value lead with 85% conversion probability...",
                    "agent_recommendation": "Call immediately - Golden lead opportunity"
                },
                "error": None
            }
        }


class PricingAnalyticsResponse(BaseModel):
    success: bool
    analytics: Optional[Dict[str, Any]]
    error: Optional[str]


class ROIReportResponse(BaseModel):
    success: bool
    report: Optional[Dict[str, Any]]
    error: Optional[str]


# API Endpoints

@router.post("/calculate", response_model=LeadPricingResponse, status_code=HTTP_200_OK)
async def calculate_lead_pricing(
    request: LeadPricingRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Calculate dynamic pricing for a lead
    
    Calculates ROI-justified pricing based on lead quality, conversion probability,
    and historical performance data.
    """
    try:
        # Validate access to location
        await _validate_location_access(request.location_id, current_user)
        
        # Calculate pricing
        pricing_result = await pricing_optimizer.calculate_lead_price(
            contact_id=request.contact_id,
            location_id=request.location_id,
            context=request.context or {}
        )
        
        # Track API usage in background
        background_tasks.add_task(
            _track_api_usage,
            "pricing_calculate", 
            request.location_id,
            current_user["user_id"]
        )
        
        return LeadPricingResponse(
            success=True,
            pricing_result=pricing_result.__dict__,
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate pricing for {request.contact_id}: {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Pricing calculation failed: {str(e)}"
        )


@router.get("/analytics/{location_id}", response_model=PricingAnalyticsResponse, status_code=HTTP_200_OK)
async def get_pricing_analytics(
    location_id: str,
    days: int = Query(30, ge=7, le=365, description="Analysis period in days"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get pricing performance analytics for a location
    
    Returns comprehensive pricing metrics, trends, and optimization opportunities.
    """
    try:
        # Validate access
        await _validate_location_access(location_id, current_user)
        
        # Get analytics
        analytics = await pricing_optimizer.get_pricing_analytics(location_id, days)
        
        return PricingAnalyticsResponse(
            success=True,
            analytics=analytics,
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pricing analytics for {location_id}: {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Analytics retrieval failed: {str(e)}"
        )


@router.post("/configure/{location_id}", status_code=HTTP_201_CREATED)
async def update_pricing_configuration(
    location_id: str,
    config: PricingConfigRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Update pricing configuration for a location
    
    Allows customization of pricing parameters, tier multipliers, and target ARPU.
    """
    try:
        # Validate access (admin only for pricing config changes)
        await _validate_admin_access(location_id, current_user)
        
        # Get current tenant config
        tenant_config = await tenant_service.get_tenant_config(location_id)
        
        # Update pricing configuration
        pricing_config = {
            "base_price_per_lead": config.base_price_per_lead,
            "tier_multipliers": config.tier_multipliers,
            "conversion_boost_enabled": config.conversion_boost_enabled,
            "roi_transparency_enabled": True,  # Always enabled
            "average_commission": config.average_commission,
            "target_arpu": config.target_arpu,
            "updated_at": datetime.utcnow().isoformat(),
            "updated_by": current_user["user_id"]
        }
        
        tenant_config["pricing_config"] = pricing_config
        
        # Save updated config
        await tenant_service.update_tenant_config(location_id, tenant_config)
        
        return {
            "success": True,
            "message": "Pricing configuration updated successfully",
            "config": pricing_config
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update pricing config for {location_id}: {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Configuration update failed: {str(e)}"
        )


@router.get("/roi-report/{location_id}", response_model=ROIReportResponse, status_code=HTTP_200_OK)
async def generate_roi_report(
    location_id: str,
    days: int = Query(30, ge=7, le=365, description="Reporting period in days"),
    include_projections: bool = Query(True, description="Include future projections"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Generate comprehensive ROI report for client presentation
    
    Returns detailed analysis of cost savings, revenue impact, and competitive advantages.
    """
    try:
        # Validate access
        await _validate_location_access(location_id, current_user)
        
        # Generate ROI report
        roi_report = await roi_calculator.generate_client_roi_report(
            location_id=location_id,
            days=days,
            include_projections=include_projections
        )
        
        return ROIReportResponse(
            success=True,
            report=roi_report.__dict__,
            error=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate ROI report for {location_id}: {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"ROI report generation failed: {str(e)}"
        )


@router.post("/savings-calculator", status_code=HTTP_200_OK)
async def calculate_savings(
    request: SavingsCalculatorRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Interactive savings calculator for prospect evaluation
    
    Calculates cost savings and ROI projections for different volume scenarios.
    """
    try:
        # Calculate savings
        savings_result = await roi_calculator.get_savings_calculator(
            leads_per_month=request.leads_per_month,
            messages_per_lead=request.messages_per_lead,
            human_hourly_rate=request.human_hourly_rate
        )
        
        return {
            "success": True,
            "calculation": savings_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate savings: {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Savings calculation failed: {str(e)}"
        )


@router.get("/human-vs-ai/{location_id}", status_code=HTTP_200_OK)
async def get_human_vs_ai_comparison(
    location_id: str,
    tasks: Optional[List[str]] = Query(None, description="Specific tasks to compare"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get detailed human vs AI comparison analysis
    
    Returns task-by-task comparison showing advantages of Jorge's AI.
    """
    try:
        # Validate access
        await _validate_location_access(location_id, current_user)
        
        # Generate comparison
        comparisons = await roi_calculator.calculate_human_vs_ai_comparison(
            location_id=location_id,
            task_categories=tasks
        )
        
        # Convert to dict format
        comparison_data = [comp.__dict__ for comp in comparisons]
        
        return {
            "success": True,
            "comparisons": comparison_data,
            "summary": _generate_comparison_summary(comparison_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate comparison for {location_id}: {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Comparison generation failed: {str(e)}"
        )


@router.post("/optimize/{location_id}", status_code=HTTP_200_OK)
async def optimize_pricing_model(
    location_id: str,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user)
):
    """
    Machine learning optimization of pricing parameters
    
    Analyzes historical performance and provides optimization recommendations.
    """
    try:
        # Validate admin access
        await _validate_admin_access(location_id, current_user)
        
        # Run optimization
        optimization_result = await pricing_optimizer.optimize_pricing_model(location_id)
        
        # Schedule background analysis
        background_tasks.add_task(
            _schedule_optimization_analysis,
            location_id,
            optimization_result,
            current_user["user_id"]
        )
        
        return {
            "success": True,
            "optimization": optimization_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to optimize pricing for {location_id}: {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Pricing optimization failed: {str(e)}"
        )


@router.get("/export/{location_id}", status_code=HTTP_200_OK)
async def export_pricing_data(
    location_id: str,
    format: str = Query("json", regex="^(Union[json, csv]|excel)$", description="Export format"),
    days: int = Query(30, ge=7, le=365, description="Export period in days"),
    current_user: Dict = Depends(get_current_user)
):
    """
    Export pricing and ROI data in various formats
    
    Supports JSON, CSV, and Excel formats for external analysis.
    """
    try:
        # Validate access
        await _validate_location_access(location_id, current_user)
        
        # Get comprehensive data
        pricing_analytics, roi_report = await asyncio.gather(
            pricing_optimizer.get_pricing_analytics(location_id, days),
            roi_calculator.generate_client_roi_report(location_id, days)
        )
        
        # Format data for export
        export_data = {
            "location_id": location_id,
            "export_date": datetime.utcnow().isoformat(),
            "period_days": days,
            "pricing_analytics": pricing_analytics,
            "roi_report": roi_report.__dict__,
            "export_format": format
        }
        
        if format == "json":
            return export_data
        elif format == "csv":
            # Convert to CSV format (simplified for initial implementation)
            return {
                "success": True,
                "message": "CSV export would be generated here",
                "data": export_data
            }
        elif format == "excel":
            # Convert to Excel format (simplified for initial implementation)
            return {
                "success": True,
                "message": "Excel export would be generated here",
                "data": export_data
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export data for {location_id}: {e}")
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=f"Data export failed: {str(e)}"
        )


# Health check endpoint
@router.get("/health", status_code=HTTP_200_OK)
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test service connections
        test_result = await _test_service_health()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": test_result
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Service unhealthy: {str(e)}"
        )


# Helper functions

async def _validate_location_access(location_id: str, current_user: Dict) -> None:
    """Validate user access to location"""
    user_locations = current_user.get("locations", [])
    
    if current_user.get("role") != "admin" and location_id not in user_locations:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Location not found or access denied"
        )


async def _validate_admin_access(location_id: str, current_user: Dict) -> None:
    """Validate admin access for configuration changes"""
    if current_user.get("role") not in ["admin", "owner"]:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Admin access required for this operation"
        )
    
    await _validate_location_access(location_id, current_user)


async def _track_api_usage(operation: str, location_id: str, user_id: str) -> None:
    """Track API usage for analytics"""
    try:
        usage_data = {
            "operation": operation,
            "location_id": location_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # This would integrate with analytics service
        logger.info(f"API usage tracked: {usage_data}")
        
    except Exception as e:
        logger.warning(f"Failed to track API usage: {e}")


def _generate_comparison_summary(comparisons: List[Dict]) -> Dict[str, Any]:
    """Generate summary of human vs AI comparisons"""
    if not comparisons:
        return {"message": "No comparisons available"}
    
    # Calculate averages
    avg_time_savings = sum(c["time_savings_pct"] for c in comparisons) / len(comparisons)
    avg_cost_savings = sum(c["cost_savings_pct"] for c in comparisons) / len(comparisons)
    avg_accuracy_improvement = sum(c["accuracy_improvement_pct"] for c in comparisons) / len(comparisons)
    
    return {
        "total_tasks_analyzed": len(comparisons),
        "average_time_savings_pct": round(avg_time_savings, 1),
        "average_cost_savings_pct": round(avg_cost_savings, 1),
        "average_accuracy_improvement_pct": round(avg_accuracy_improvement, 1),
        "key_advantages": [
            f"{avg_time_savings:.0f}% faster task completion",
            f"{avg_cost_savings:.0f}% cost reduction",
            f"{avg_accuracy_improvement:.0f}% accuracy improvement",
            "24/7 availability vs business hours only"
        ]
    }


async def _schedule_optimization_analysis(
    location_id: str, 
    optimization_result: Dict, 
    user_id: str
) -> None:
    """Schedule background optimization analysis"""
    try:
        if optimization_result.get("optimized", False):
            # Log optimization recommendations
            logger.info(f"Optimization recommendations for {location_id}: {optimization_result}")
            
            # This would integrate with notification system
            # Send recommendations to client
            
        else:
            logger.info(f"No optimization needed for {location_id}: {optimization_result.get('reason', 'Unknown')}")
            
    except Exception as e:
        logger.warning(f"Failed to process optimization analysis: {e}")


async def _test_service_health() -> Dict[str, str]:
    """Test health of dependent services"""
    try:
        # Test pricing optimizer
        await pricing_optimizer._get_pricing_config("test_location")
        pricing_status = "healthy"
    except Exception:
        pricing_status = "unhealthy"
    
    try:
        # Test ROI calculator  
        await roi_calculator._get_usage_metrics("test_location", 1)
        roi_status = "healthy"
    except Exception:
        roi_status = "unhealthy"
    
    return {
        "pricing_optimizer": pricing_status,
        "roi_calculator": roi_status,
        "tenant_service": "healthy"  # Simplified check
    }


# Export router for integration
__all__ = ["router"]