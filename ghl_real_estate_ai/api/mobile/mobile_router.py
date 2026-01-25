"""
Mobile Router - Main routing module for mobile API endpoints
Integrates authentication, AR/VR, voice, and mobile-optimized data endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, Header, Request
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional, Union
import asyncio
from datetime import datetime, timedelta
import json

from ghl_real_estate_ai.api.mobile.auth import router as auth_router, mobile_auth_service
from ghl_real_estate_ai.api.mobile.ar_endpoints import router as ar_router
from ghl_real_estate_ai.api.middleware.jwt_auth import get_current_user
from ghl_real_estate_ai.services.voice_claude_service import VoiceClaudeService
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.api.schemas.mobile import *
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# Create main mobile router
router = APIRouter(prefix="/mobile", tags=["Mobile API"])

# Include sub-routers
router.include_router(auth_router)
router.include_router(ar_router)

# Initialize services
voice_service = VoiceClaudeService()
claude_assistant = ClaudeAssistant(context_type="mobile")

@router.get("/", response_model=Dict[str, Any])
async def mobile_api_info():
    """
    Mobile API information and capabilities.
    """
    return {
        "name": "Jorge Real Estate Mobile API",
        "version": "1.0.0",
        "description": "Mobile-optimized API with AR/VR and voice capabilities",
        "features": [
            "JWT Authentication with Biometric Support",
            "AR/VR Property Visualization",
            "Voice Assistant Integration",
            "Offline Sync Capabilities",
            "Location-based Services",
            "Push Notifications",
            "Mobile-optimized Data Formats"
        ],
        "platforms_supported": ["iOS", "Android", "Web App"],
        "api_endpoints": {
            "authentication": "/mobile/auth/*",
            "ar_vr": "/mobile/ar/*",
            "voice": "/mobile/voice/*",
            "properties": "/mobile/properties/*",
            "leads": "/mobile/leads/*",
            "analytics": "/mobile/analytics/*"
        }
    }

# Voice Integration Endpoints

@router.post("/voice/process", response_model=MobileVoiceResponse)
async def process_voice_interaction(
    voice_request: MobileVoiceRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Process voice interaction with AI assistant.
    
    Features:
    - Speech-to-text processing
    - Intent classification
    - AI response generation
    - Optional text-to-speech output
    - Session-based context management
    """
    try:
        user_id = current_user["user_id"]
        
        # Process the voice interaction
        voice_response = await voice_service.process_voice_interaction(
            voice_request=voice_request,
            user_id=user_id
        )
        
        return voice_response
        
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voice processing failed"
        )

@router.get("/voice/session/{session_id}/summary")
async def get_voice_session_summary(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get summary of voice interaction session.
    """
    try:
        user_id = current_user["user_id"]
        summary = await voice_service.get_session_summary(session_id, user_id)
        return build_mobile_success_response(summary)
        
    except Exception as e:
        logger.error(f"Voice session summary error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session summary failed"
        )

@router.delete("/voice/session/{session_id}")
async def clear_voice_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Clear voice session data.
    """
    try:
        success = await voice_service.clear_session(session_id)
        if success:
            return build_mobile_success_response({"session_cleared": True})
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Voice session clear error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Session clear failed"
        )

# Property Endpoints (Mobile-Optimized)

@router.get("/properties", response_model=MobileListResponse)
async def get_mobile_properties(
    page: int = Query(1, ge=1, le=100),
    limit: int = Query(20, ge=1, le=50),
    location: Optional[str] = Query(None, description="GPS coordinates as 'lat,lng'"),
    radius: Optional[float] = Query(25.0, ge=1, le=100),
    min_price: Optional[int] = Query(None, ge=0),
    max_price: Optional[int] = Query(None, ge=0),
    bedrooms: Optional[int] = Query(None, ge=0, le=10),
    bathrooms: Optional[float] = Query(None, ge=0, le=10),
    property_type: Optional[str] = Query(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get mobile-optimized property listings with location-based filtering.
    
    Features:
    - GPS-based proximity search
    - Compressed property data for mobile bandwidth
    - Pagination optimized for mobile scrolling
    - Image URLs optimized for mobile screens
    """
    try:
        # Parse location if provided
        user_coordinates = None
        if location:
            try:
                lat, lng = map(float, location.split(','))
                user_coordinates = GPSCoordinate(latitude=lat, longitude=lng)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid location format. Use 'latitude,longitude'"
                )
        
        # Build filters
        filters = {}
        if min_price:
            filters["min_price"] = min_price
        if max_price:
            filters["max_price"] = max_price
        if bedrooms:
            filters["bedrooms"] = bedrooms
        if bathrooms:
            filters["bathrooms"] = bathrooms
        if property_type:
            filters["property_type"] = property_type
        if user_coordinates and radius:
            filters["location"] = user_coordinates.dict()
            filters["radius"] = radius
        
        # Get cached property data
        cache = get_cache_service()
        cache_key = f"mobile_properties:{page}:{limit}:{json.dumps(filters, sort_keys=True)}"
        
        cached_data = await cache.get(cache_key)
        if cached_data:
            return MobileListResponse(**cached_data)
        
        # Mock property data (in production, this would query the actual property database)
        mock_properties = []
        total_count = 150  # Mock total
        
        for i in range((page - 1) * limit, min(page * limit, total_count)):
            # Calculate mock distance if location provided
            distance_miles = None
            if user_coordinates:
                # Mock distance calculation
                distance_miles = round(5.0 + (i % 20), 1)
            
            property_summary = MobilePropertySummary(
                property_id=f"prop_austin_{i+1:03d}",
                mls_id=f"ATX{12345 + i}",
                address=f"{1234 + i} Example Street",
                city="Austin",
                state="TX",
                zip_code=f"787{46 + (i % 10):02d}",
                price=450000 + (i * 25000),
                price_formatted=f"${450000 + (i * 25000):,}",
                bedrooms=3 + (i % 3),
                bathrooms=2.5 + (i % 2) * 0.5,
                sqft=1800 + (i * 200),
                lot_size="0.25 acres",
                property_type="Single Family",
                days_on_market=5 + (i % 30),
                primary_image_url=f"https://images.example.com/prop_{i+1}_primary.jpg",
                thumbnail_url=f"https://images.example.com/prop_{i+1}_thumb.jpg",
                coordinates=GPSCoordinate(
                    latitude=30.2672 + (i * 0.001),
                    longitude=-97.7431 + (i * 0.001)
                ) if user_coordinates else None,
                distance_miles=distance_miles,
                favorite=i % 7 == 0,  # Some favorites
                viewed_at=datetime.now() - timedelta(days=i % 10) if i % 5 == 0 else None
            )
            
            mock_properties.append(property_summary.dict())
        
        # Build pagination metadata
        total_pages = (total_count + limit - 1) // limit
        pagination = MobilePaginationMetadata(
            current_page=page,
            total_pages=total_pages,
            total_count=total_count,
            page_size=limit,
            has_next=page < total_pages,
            has_previous=page > 1,
            next_cursor=f"page_{page + 1}" if page < total_pages else None,
            previous_cursor=f"page_{page - 1}" if page > 1 else None
        )
        
        response = MobileListResponse(
            data=mock_properties,
            pagination=pagination,
            filters_applied=filters
        )
        
        # Cache for 5 minutes
        await cache.set(cache_key, response.dict(), ttl=300)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mobile properties error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Property retrieval failed"
        )

@router.get("/properties/{property_id}", response_model=MobilePropertyDetails)
async def get_mobile_property_details(
    property_id: str,
    include_ai_insights: bool = Query(default=True),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get detailed property information optimized for mobile viewing.
    
    Features:
    - Comprehensive property details
    - AI-generated insights and recommendations
    - Mobile-optimized image galleries
    - Comparable sales and market data
    - Investment analysis
    """
    try:
        # Check cache first
        cache = get_cache_service()
        cache_key = f"mobile_property_details:{property_id}:{include_ai_insights}"
        
        cached_data = await cache.get(cache_key)
        if cached_data:
            return MobilePropertyDetails(**cached_data)
        
        # Mock detailed property data
        property_details = MobilePropertyDetails(
            property_id=property_id,
            mls_id=f"ATX{property_id[-6:]}",
            address="1234 Hill Country Drive",
            city="Austin",
            state="TX",
            zip_code="78746",
            coordinates=GPSCoordinate(latitude=30.2672, longitude=-97.7431),
            price=750000,
            price_formatted="$750,000",
            price_per_sqft=300,
            bedrooms=4,
            bathrooms=3.5,
            sqft=2500,
            lot_size="0.25 acres",
            year_built=2018,
            property_type="Single Family",
            days_on_market=12,
            images=[
                f"https://images.example.com/{property_id}/exterior_1.jpg",
                f"https://images.example.com/{property_id}/kitchen_1.jpg",
                f"https://images.example.com/{property_id}/living_1.jpg",
                f"https://images.example.com/{property_id}/master_1.jpg"
            ],
            virtual_tour_url=f"https://tours.example.com/{property_id}",
            features=[
                "Open Floor Plan",
                "Updated Kitchen",
                "Hardwood Floors",
                "Two-Car Garage",
                "Covered Patio"
            ],
            amenities=[
                "Swimming Pool",
                "Community Gym",
                "Walking Trails",
                "Playground"
            ],
            neighborhood="Hill Country",
            school_district="Lake Travis ISD",
            nearby_schools=[
                {"name": "Lake Travis Elementary", "rating": 9, "distance": 0.5},
                {"name": "Lake Travis Middle", "rating": 9, "distance": 1.2},
                {"name": "Lake Travis High", "rating": 10, "distance": 2.1}
            ],
            walkability_score=65,
            market_trends={
                "appreciation_1y": 8.5,
                "median_price_trend": "increasing",
                "inventory_level": "low",
                "days_on_market_avg": 15
            },
            comparable_sales=[
                {
                    "address": "1245 Hill Country Drive",
                    "price": 740000,
                    "sold_date": "2024-01-10",
                    "sqft": 2400,
                    "price_per_sqft": 308
                }
            ],
            investment_score=85,
            favorite=False,
            viewed_at=datetime.now()
        )
        
        # Generate AI insights if requested
        if include_ai_insights:
            try:
                ai_context = {
                    "property_data": property_details.dict(),
                    "market_context": "austin",
                    "user_id": current_user["user_id"]
                }
                
                # Use Claude assistant for insights
                insights = await claude_assistant.generate_market_aware_retention_script(
                    lead_data={"lead_name": "Property Viewer", "property_interest": property_id},
                    market_id="austin"
                )
                
                property_details.ai_insights = insights.get("reasoning", "This property shows strong potential in the current Austin market.")
                
            except Exception as e:
                logger.warning(f"Could not generate AI insights: {e}")
                property_details.ai_insights = "AI insights temporarily unavailable."
        
        # Cache for 10 minutes
        await cache.set(cache_key, property_details.dict(), ttl=600)
        
        return property_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Property details error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Property details retrieval failed"
        )

# Lead Endpoints (Mobile-Optimized)

@router.get("/leads", response_model=MobileListResponse)
async def get_mobile_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    status_filter: Optional[str] = Query(None),
    priority_filter: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    location: Optional[str] = Query(None, description="GPS coordinates as 'lat,lng'"),
    radius: Optional[float] = Query(25.0, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get mobile-optimized lead listings with filtering and search.
    
    Features:
    - Status-based filtering
    - Priority sorting
    - Location-based lead discovery
    - Search by name, phone, or email
    - Mobile-optimized data format
    """
    try:
        # Build filters
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        if priority_filter:
            filters["priority"] = priority_filter
        if search:
            filters["search"] = search
        
        # Parse location if provided
        user_coordinates = None
        if location:
            try:
                lat, lng = map(float, location.split(','))
                user_coordinates = GPSCoordinate(latitude=lat, longitude=lng)
                filters["location"] = user_coordinates.dict()
                filters["radius"] = radius
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid location format. Use 'latitude,longitude'"
                )
        
        # Mock lead data (in production, query actual CRM/database)
        mock_leads = []
        total_count = 85  # Mock total
        
        statuses = ["new", "contacted", "qualified", "hot", "cold"]
        priorities = ["low", "medium", "high", "urgent"]
        
        for i in range((page - 1) * limit, min(page * limit, total_count)):
            # Calculate mock distance if location provided
            distance_miles = None
            if user_coordinates:
                distance_miles = round(2.0 + (i % 15), 1)
            
            lead_summary = MobileLeadSummary(
                lead_id=f"lead_{i+1:03d}",
                name=f"Client {i+1}",
                phone=f"512-555-{1000 + i:04d}",
                email=f"client{i+1}@example.com",
                status=statuses[i % len(statuses)],
                lead_score=max(10, 100 - (i * 2) % 90),
                last_contact=datetime.now() - timedelta(days=i % 14),
                next_followup=datetime.now() + timedelta(days=(i % 7) + 1) if i % 3 == 0 else None,
                source="Website",
                assigned_agent=current_user.get("username", "Jorge"),
                priority=priorities[i % len(priorities)],
                property_interest=f"prop_austin_{(i % 50) + 1:03d}",
                estimated_budget=300000 + (i * 50000),
                coordinates=GPSCoordinate(
                    latitude=30.2672 + (i * 0.01),
                    longitude=-97.7431 + (i * 0.01)
                ) if user_coordinates else None,
                distance_miles=distance_miles,
                unread_messages=i % 5
            )
            
            mock_leads.append(lead_summary.dict())
        
        # Build pagination metadata
        total_pages = (total_count + limit - 1) // limit
        pagination = MobilePaginationMetadata(
            current_page=page,
            total_pages=total_pages,
            total_count=total_count,
            page_size=limit,
            has_next=page < total_pages,
            has_previous=page > 1
        )
        
        return MobileListResponse(
            data=mock_leads,
            pagination=pagination,
            filters_applied=filters
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mobile leads error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lead retrieval failed"
        )

@router.get("/leads/{lead_id}", response_model=MobileLeadDetails)
async def get_mobile_lead_details(
    lead_id: str,
    include_ai_insights: bool = Query(default=True),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get detailed lead information with AI insights and recommendations.
    """
    try:
        # Mock detailed lead data
        lead_details = MobileLeadDetails(
            lead_id=lead_id,
            name="Sarah Chen",
            first_name="Sarah",
            last_name="Chen",
            phone="512-555-2001",
            email="sarah.chen@example.com",
            address="789 Tech Boulevard, Austin, TX",
            coordinates=GPSCoordinate(latitude=30.2672, longitude=-97.7431),
            status="qualified",
            lead_score=92,
            qualification_status="pre_approved",
            last_contact=datetime.now() - timedelta(hours=6),
            next_followup=datetime.now() + timedelta(days=2),
            contact_attempts=3,
            response_rate=85,
            property_preferences={
                "min_bedrooms": 3,
                "max_price": 800000,
                "preferred_style": "modern",
                "must_have_garage": True
            },
            price_range={"min": 600000, "max": 800000},
            preferred_areas=["Downtown", "South Austin", "Hill Country"],
            must_have_features=["Home Office", "Updated Kitchen", "Pool"],
            conversion_probability=85,
            recommended_properties=["prop_austin_001", "prop_austin_015", "prop_austin_032"],
            recent_activities=[
                {
                    "type": "property_view",
                    "property_id": "prop_austin_001",
                    "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "duration_minutes": 15
                },
                {
                    "type": "message_sent",
                    "content": "Very interested in scheduling a showing",
                    "timestamp": (datetime.now() - timedelta(hours=6)).isoformat()
                }
            ],
            assigned_agent="Jorge Sales",
            source="Website Inquiry",
            tags=["High Priority", "Tech Professional", "Quick Close"]
        )
        
        # Generate AI insights if requested
        if include_ai_insights:
            try:
                behavioral_insights = await claude_assistant.generate_market_aware_retention_script(
                    lead_data={
                        "lead_name": lead_details.name,
                        "lead_id": lead_id,
                        "conversion_probability": lead_details.conversion_probability,
                        "last_interaction_days": 0.25  # 6 hours ago
                    },
                    market_id="austin"
                )
                
                lead_details.behavioral_insights = behavioral_insights.get("reasoning", "High-engagement lead showing strong buying signals.")
                
            except Exception as e:
                logger.warning(f"Could not generate AI insights: {e}")
                lead_details.behavioral_insights = "AI insights temporarily unavailable."
        
        return lead_details
        
    except Exception as e:
        logger.error(f"Lead details error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lead details retrieval failed"
        )

# Analytics Endpoints

@router.get("/analytics/summary", response_model=MobileAnalyticsSummary)
async def get_mobile_analytics_summary(
    period: str = Query("week", pattern="^(Union[day, week]|month)$"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get mobile-optimized analytics summary with key performance indicators.
    """
    try:
        # Mock analytics data
        analytics_summary = MobileAnalyticsSummary(
            period=period,
            leads_summary={
                "total": 127,
                "new": 23,
                "qualified": 45,
                "converted": 8
            },
            properties_summary={
                "active_listings": 89,
                "new_listings": 12,
                "under_contract": 15,
                "sold": 6
            },
            performance_metrics={
                "conversion_rate": 18.5,
                "avg_response_time": 2.3,
                "lead_score_avg": 72.8,
                "revenue_projection": 450000
            },
            top_performing_areas=[
                {"area": "Downtown", "leads": 15, "conversions": 3},
                {"area": "Hill Country", "leads": 12, "conversions": 4},
                {"area": "South Austin", "leads": 10, "conversions": 2}
            ],
            recent_activities=[
                {"type": "lead_converted", "description": "Sarah Chen - Contract signed", "timestamp": datetime.now().isoformat()},
                {"type": "property_listed", "description": "New listing in Hill Country", "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()}
            ],
            alerts=[
                {"type": "high_priority", "message": "3 hot leads need immediate follow-up"},
                {"type": "opportunity", "message": "New listing matches 5 active buyers"}
            ],
            trend_indicators={
                "lead_volume": "increasing",
                "conversion_rate": "stable",
                "avg_sale_price": "increasing"
            }
        )
        
        return analytics_summary
        
    except Exception as e:
        logger.error(f"Mobile analytics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analytics retrieval failed"
        )

# Settings and Sync Endpoints

@router.get("/settings")
async def get_mobile_app_settings(
    device_id: str = Header(..., alias="X-Device-ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get mobile app settings and preferences.
    """
    try:
        # Mock settings (in production, retrieve from user preferences database)
        settings = MobileAppSettings(
            user_id=current_user["user_id"],
            device_id=device_id,
            push_enabled=True,
            lead_notifications=True,
            property_alerts=True,
            appointment_reminders=True,
            market_updates=False,
            default_search_radius=25.0,
            preferred_units="imperial",
            map_type="standard",
            theme="auto",
            location_sharing=True,
            analytics_enabled=True,
            crash_reporting=True,
            ar_enabled=True,
            voice_enabled=True,
            biometric_enabled=True
        )
        
        return build_mobile_success_response(settings.dict())
        
    except Exception as e:
        logger.error(f"Settings retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Settings retrieval failed"
        )

@router.put("/settings")
async def update_mobile_app_settings(
    settings_update: Dict[str, Any] = Body(...),
    device_id: str = Header(..., alias="X-Device-ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update mobile app settings and preferences.
    """
    try:
        user_id = current_user["user_id"]
        
        # Validate and save settings (mock implementation)
        # In production, this would validate against MobileAppSettings model
        # and save to user preferences database
        
        updated_settings = {
            "user_id": user_id,
            "device_id": device_id,
            "updated_at": datetime.now().isoformat(),
            **settings_update
        }
        
        return build_mobile_success_response({
            "settings_updated": True,
            "updated_fields": list(settings_update.keys()),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Settings update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Settings update failed"
        )

@router.post("/sync", response_model=MobileSyncResponse)
async def mobile_sync(
    sync_request: MobileSyncRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Synchronize mobile app data with server.
    
    Handles offline sync, conflict resolution, and incremental updates.
    """
    try:
        # Process pending operations (mock implementation)
        processed_operations = []
        conflicts = []
        
        for operation in sync_request.pending_operations:
            # Process each operation
            processed_operations.append({
                "operation_id": operation.get("id", "unknown"),
                "type": operation.get("type", "unknown"),
                "status": "success",
                "server_timestamp": datetime.now().isoformat()
            })
        
        # Mock server updates
        server_updates = [
            {
                "type": "lead_update",
                "lead_id": "lead_001",
                "changes": {"status": "hot", "last_contact": datetime.now().isoformat()},
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        sync_response = MobileSyncResponse(
            sync_id=f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            processed_operations=processed_operations,
            server_updates=server_updates,
            conflicts=conflicts,
            next_sync_recommended=datetime.now() + timedelta(minutes=30),
            full_sync_required=False
        )
        
        return sync_response
        
    except Exception as e:
        logger.error(f"Mobile sync error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sync operation failed"
        )

# Search Endpoint

@router.post("/search", response_model=MobileSearchResponse)
async def mobile_search(
    search_request: MobileSearchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Mobile-optimized search across properties and leads.
    
    Features:
    - Unified search across multiple data types
    - Location-based results
    - Mobile-optimized response format
    - Search suggestions
    """
    try:
        search_start = datetime.now()
        
        # Mock search results
        results = {
            "properties": [
                {
                    "property_id": "prop_austin_001",
                    "address": "1234 Hill Country Drive",
                    "price": 750000,
                    "match_score": 0.95,
                    "match_reason": "Address matches search query"
                }
            ],
            "leads": [
                {
                    "lead_id": "lead_001",
                    "name": "Sarah Chen",
                    "status": "qualified",
                    "match_score": 0.88,
                    "match_reason": "Name matches search query"
                }
            ]
        }
        
        # Calculate search time
        search_time = int((datetime.now() - search_start).total_seconds() * 1000)
        
        # Build pagination for results
        total_results = sum(len(results[key]) for key in results)
        pagination = MobilePaginationMetadata(
            current_page=search_request.page,
            total_pages=1,
            total_count=total_results,
            page_size=search_request.page_size,
            has_next=False,
            has_previous=False
        )
        
        search_response = MobileSearchResponse(
            query=search_request.query,
            results=results,
            total_count=total_results,
            search_time_ms=search_time,
            suggestions=["Hill Country", "Sarah", "Austin properties"],
            filters_applied=search_request.filters or {},
            pagination=pagination
        )
        
        return search_response
        
    except Exception as e:
        logger.error(f"Mobile search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search operation failed"
        )