"""
AR/VR Integration API - Property Visualization and Spatial Computing
Advanced augmented and virtual reality endpoints for immersive property experiences.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
import asyncio
import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta
import base64
import hashlib

from ghl_real_estate_ai.api.middleware.jwt_auth import get_current_user
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant

logger = get_logger(__name__)

router = APIRouter(prefix="/mobile/ar", tags=["AR/VR Integration"])

# AR/VR Data Models

class SpatialCoordinate(BaseModel):
    """3D spatial coordinate for AR anchoring."""
    x: float = Field(..., description="X coordinate in meters")
    y: float = Field(..., description="Y coordinate in meters") 
    z: float = Field(..., description="Z coordinate in meters")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Coordinate accuracy confidence")

class ARPropertyOverlay(BaseModel):
    """AR overlay data for property visualization."""
    overlay_id: str = Field(..., description="Unique overlay identifier")
    property_id: str = Field(..., description="Property MLS or internal ID")
    overlay_type: str = Field(..., description="Type of overlay: price, info, highlight, virtual_staging")
    position: SpatialCoordinate = Field(..., description="3D position for overlay")
    rotation: Optional[Dict[str, float]] = Field(default=None, description="Rotation quaternion")
    scale: Optional[Dict[str, float]] = Field(default={"x": 1.0, "y": 1.0, "z": 1.0}, description="Scale factors")
    content: Dict[str, Any] = Field(..., description="Overlay content data")
    visibility_distance: float = Field(default=100.0, description="Maximum visibility distance in meters")
    auto_hide: bool = Field(default=True, description="Auto-hide when user looks away")

class VRTourWaypoint(BaseModel):
    """Virtual tour waypoint with spatial data."""
    waypoint_id: str = Field(..., description="Unique waypoint identifier")
    name: str = Field(..., description="Waypoint display name")
    description: Optional[str] = Field(None, description="Waypoint description")
    position: SpatialCoordinate = Field(..., description="3D position")
    look_direction: Optional[Dict[str, float]] = Field(None, description="Preferred look direction")
    panorama_url: Optional[str] = Field(None, description="360° panorama image URL")
    hotspots: List[Dict[str, Any]] = Field(default=[], description="Interactive hotspots")
    audio_narration: Optional[str] = Field(None, description="Audio narration URL")
    ai_insights: Optional[str] = Field(None, description="AI-generated insights for this view")

class Property3DModel(BaseModel):
    """3D model data for AR/VR visualization."""
    model_id: str = Field(..., description="Unique model identifier")
    property_id: str = Field(..., description="Associated property ID")
    model_format: str = Field(..., description="3D model format: gltf, usd, obj, fbx")
    model_url: str = Field(..., description="Model download URL")
    texture_urls: List[str] = Field(default=[], description="Texture file URLs")
    scale_factor: float = Field(default=1.0, description="Model scale factor")
    origin_offset: SpatialCoordinate = Field(..., description="Model origin offset")
    bounding_box: Dict[str, SpatialCoordinate] = Field(..., description="Model bounding box")
    level_of_detail: List[Dict[str, Any]] = Field(default=[], description="LOD variants for performance")
    interactive_elements: List[Dict[str, Any]] = Field(default=[], description="Interactive model elements")

class ARSpatialAnchor(BaseModel):
    """Spatial anchor for persistent AR content."""
    anchor_id: str = Field(..., description="Unique anchor identifier")
    property_id: str = Field(..., description="Associated property ID")
    world_position: SpatialCoordinate = Field(..., description="Real-world GPS position")
    local_position: SpatialCoordinate = Field(..., description="Local AR coordinate system position")
    anchor_type: str = Field(..., description="Anchor type: cloud, local, image, plane")
    tracking_image: Optional[str] = Field(None, description="Base64 encoded tracking image")
    persistence_duration: int = Field(default=24, description="Hours to persist anchor")
    created_at: datetime = Field(default_factory=datetime.now)
    accuracy_radius: float = Field(default=1.0, description="Accuracy radius in meters")

class PropertyVisualizationRequest(BaseModel):
    """Request for property AR/VR visualization setup."""
    property_id: str = Field(..., description="Property to visualize")
    user_location: Optional[Dict[str, float]] = Field(None, description="User's current GPS location")
    device_capabilities: Dict[str, Any] = Field(..., description="Device AR/VR capabilities")
    visualization_type: str = Field(..., description="Type: ar_overlay, vr_tour, mixed_reality")
    quality_preference: str = Field(default="balanced", description="Quality: low, balanced, high, ultra")
    include_ai_insights: bool = Field(default=True, description="Include AI-generated insights")

class SpatialMappingData(BaseModel):
    """Spatial mapping data from device for accurate AR placement."""
    mapping_id: str = Field(..., description="Mapping session identifier")
    point_cloud: List[SpatialCoordinate] = Field(..., description="3D point cloud data")
    plane_data: List[Dict[str, Any]] = Field(default=[], description="Detected planes")
    lighting_estimation: Optional[Dict[str, float]] = Field(None, description="Environmental lighting data")
    occlusion_mesh: List[Dict[str, Any]] = Field(default=[], description="Occlusion geometry")
    tracking_quality: float = Field(default=1.0, ge=0.0, le=1.0, description="Tracking quality score")

class ARVisualizationService:
    """Service for AR/VR property visualization."""
    
    def __init__(self):
        self.cache = None
        self.claude_assistant = ClaudeAssistant(context_type="ar_vr", market_id="austin")
    
    async def _get_cache(self):
        """Get cache service instance."""
        if not self.cache:
            self.cache = get_cache_service()
        return self.cache
    
    async def generate_property_ar_overlays(
        self,
        property_id: str,
        user_location: Optional[Dict[str, float]],
        device_capabilities: Dict[str, Any]
    ) -> List[ARPropertyOverlay]:
        """Generate AR overlays for a property based on device capabilities and user context."""
        try:
            cache = await self._get_cache()
            cache_key = f"ar_overlays:{property_id}:{hashlib.md5(json.dumps(device_capabilities, sort_keys=True).encode()).hexdigest()}"
            
            # Check cache first
            cached_overlays = await cache.get(cache_key)
            if cached_overlays:
                return [ARPropertyOverlay(**overlay) for overlay in cached_overlays]
            
            # Get property data (mock implementation)
            property_data = await self._get_property_data(property_id)
            if not property_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Property {property_id} not found"
                )
            
            overlays = []
            
            # Price overlay - always shown
            price_overlay = ARPropertyOverlay(
                overlay_id=f"price_{property_id}",
                property_id=property_id,
                overlay_type="price",
                position=SpatialCoordinate(x=0.0, y=2.0, z=0.0),
                content={
                    "price": property_data.get("price", 0),
                    "price_formatted": f"${property_data.get('price', 0):,}",
                    "price_per_sqft": property_data.get("price_per_sqft", 0),
                    "market_comparison": "5% above market average",
                    "financing_estimate": f"${property_data.get('price', 0) * 0.05 / 12:,.0f}/month"
                },
                visibility_distance=50.0
            )
            overlays.append(price_overlay)
            
            # Property info overlay
            info_overlay = ARPropertyOverlay(
                overlay_id=f"info_{property_id}",
                property_id=property_id,
                overlay_type="info",
                position=SpatialCoordinate(x=2.0, y=1.5, z=0.0),
                content={
                    "bedrooms": property_data.get("bedrooms", 0),
                    "bathrooms": property_data.get("bathrooms", 0),
                    "sqft": property_data.get("sqft", 0),
                    "year_built": property_data.get("year_built", "Unknown"),
                    "lot_size": property_data.get("lot_size", "Unknown"),
                    "property_type": property_data.get("property_type", "Single Family"),
                    "days_on_market": property_data.get("days_on_market", 0),
                    "mls_id": property_data.get("mls_id", "")
                },
                visibility_distance=30.0
            )
            overlays.append(info_overlay)
            
            # AI insights overlay (if Claude is available)
            try:
                ai_insights = await self._generate_ar_property_insights(property_data, user_location)
                insights_overlay = ARPropertyOverlay(
                    overlay_id=f"insights_{property_id}",
                    property_id=property_id,
                    overlay_type="ai_insights",
                    position=SpatialCoordinate(x=-2.0, y=1.5, z=0.0),
                    content={
                        "insights": ai_insights.get("insights", ""),
                        "highlights": ai_insights.get("highlights", []),
                        "concerns": ai_insights.get("concerns", []),
                        "investment_score": ai_insights.get("investment_score", 0),
                        "recommendation": ai_insights.get("recommendation", "")
                    },
                    visibility_distance=25.0
                )
                overlays.append(insights_overlay)
            except Exception as e:
                logger.warning(f"Could not generate AI insights for AR overlay: {e}")
            
            # Virtual staging overlays (if supported)
            if device_capabilities.get("supports_occlusion", False):
                staging_overlay = ARPropertyOverlay(
                    overlay_id=f"staging_{property_id}",
                    property_id=property_id,
                    overlay_type="virtual_staging",
                    position=SpatialCoordinate(x=0.0, y=0.0, z=0.0),
                    content={
                        "furniture_sets": ["modern", "traditional", "minimalist"],
                        "default_set": "modern",
                        "interactive": True,
                        "customizable": True
                    },
                    visibility_distance=15.0,
                    auto_hide=False
                )
                overlays.append(staging_overlay)
            
            # Cache the overlays
            overlay_data = [overlay.dict() for overlay in overlays]
            await cache.set(cache_key, overlay_data, ttl=3600)  # Cache for 1 hour
            
            return overlays
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating AR overlays: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate AR overlays"
            )
    
    async def generate_vr_tour_waypoints(
        self,
        property_id: str,
        quality_preference: str = "balanced"
    ) -> List[VRTourWaypoint]:
        """Generate VR tour waypoints for immersive property exploration."""
        try:
            cache = await self._get_cache()
            cache_key = f"vr_tour:{property_id}:{quality_preference}"
            
            # Check cache first
            cached_waypoints = await cache.get(cache_key)
            if cached_waypoints:
                return [VRTourWaypoint(**waypoint) for waypoint in cached_waypoints]
            
            # Get property data
            property_data = await self._get_property_data(property_id)
            if not property_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Property {property_id} not found"
                )
            
            waypoints = []
            
            # Exterior waypoints
            exterior_waypoint = VRTourWaypoint(
                waypoint_id=f"exterior_{property_id}",
                name="Exterior View",
                description="Front exterior and curb appeal",
                position=SpatialCoordinate(x=0.0, y=1.6, z=10.0),
                look_direction={"x": 0.0, "y": 0.0, "z": -1.0},
                panorama_url=f"https://vr-content.example.com/{property_id}/exterior_360.jpg",
                hotspots=[
                    {
                        "id": "front_door",
                        "position": {"x": 0.0, "y": 0.0, "z": -8.0},
                        "title": "Front Entrance",
                        "action": "navigate",
                        "target": "entry_foyer"
                    },
                    {
                        "id": "garage",
                        "position": {"x": 5.0, "y": 0.0, "z": -6.0},
                        "title": "2-Car Garage",
                        "action": "info",
                        "content": "Attached garage with direct home access"
                    }
                ]
            )
            waypoints.append(exterior_waypoint)
            
            # Entry foyer
            foyer_waypoint = VRTourWaypoint(
                waypoint_id=f"entry_foyer_{property_id}",
                name="Entry Foyer",
                description="Welcoming entrance with high ceilings",
                position=SpatialCoordinate(x=0.0, y=1.6, z=0.0),
                look_direction={"x": 0.0, "y": 0.1, "z": 1.0},
                panorama_url=f"https://vr-content.example.com/{property_id}/foyer_360.jpg",
                hotspots=[
                    {
                        "id": "living_room",
                        "position": {"x": 3.0, "y": 0.0, "z": 2.0},
                        "title": "Living Room",
                        "action": "navigate",
                        "target": "living_room"
                    },
                    {
                        "id": "stairs",
                        "position": {"x": -2.0, "y": 1.0, "z": 1.0},
                        "title": "Upstairs",
                        "action": "navigate",
                        "target": "upstairs_landing"
                    }
                ]
            )
            waypoints.append(foyer_waypoint)
            
            # Living room
            living_waypoint = VRTourWaypoint(
                waypoint_id=f"living_room_{property_id}",
                name="Living Room",
                description="Spacious open-concept living area",
                position=SpatialCoordinate(x=5.0, y=1.6, z=3.0),
                look_direction={"x": 1.0, "y": 0.0, "z": 0.0},
                panorama_url=f"https://vr-content.example.com/{property_id}/living_360.jpg",
                hotspots=[
                    {
                        "id": "fireplace",
                        "position": {"x": 8.0, "y": 1.0, "z": 3.0},
                        "title": "Gas Fireplace",
                        "action": "info",
                        "content": "Modern gas fireplace with stone surround"
                    },
                    {
                        "id": "kitchen",
                        "position": {"x": 5.0, "y": 0.0, "z": 8.0},
                        "title": "Kitchen",
                        "action": "navigate",
                        "target": "kitchen"
                    }
                ]
            )
            waypoints.append(living_waypoint)
            
            # Generate AI insights for each waypoint
            for waypoint in waypoints:
                try:
                    insights = await self._generate_vr_waypoint_insights(
                        property_data, waypoint.name, waypoint.description
                    )
                    waypoint.ai_insights = insights
                except Exception as e:
                    logger.warning(f"Could not generate AI insights for waypoint {waypoint.name}: {e}")
            
            # Cache the waypoints
            waypoint_data = [waypoint.dict() for waypoint in waypoints]
            await cache.set(cache_key, waypoint_data, ttl=7200)  # Cache for 2 hours
            
            return waypoints
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating VR tour waypoints: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate VR tour"
            )
    
    async def create_spatial_anchor(
        self,
        property_id: str,
        anchor_data: Dict[str, Any],
        user_id: str
    ) -> ARSpatialAnchor:
        """Create persistent spatial anchor for AR content."""
        try:
            anchor_id = str(uuid.uuid4())
            
            anchor = ARSpatialAnchor(
                anchor_id=anchor_id,
                property_id=property_id,
                world_position=SpatialCoordinate(**anchor_data["world_position"]),
                local_position=SpatialCoordinate(**anchor_data["local_position"]),
                anchor_type=anchor_data.get("anchor_type", "local"),
                tracking_image=anchor_data.get("tracking_image"),
                persistence_duration=anchor_data.get("persistence_duration", 24),
                accuracy_radius=anchor_data.get("accuracy_radius", 1.0)
            )
            
            # Store anchor in cache
            cache = await self._get_cache()
            await cache.set(
                f"spatial_anchor:{anchor_id}",
                anchor.dict(),
                ttl=anchor.persistence_duration * 3600  # Convert hours to seconds
            )
            
            # Also store by property for lookup
            property_anchors = await cache.get(f"property_anchors:{property_id}") or []
            property_anchors.append(anchor_id)
            await cache.set(f"property_anchors:{property_id}", property_anchors, ttl=86400 * 7)  # 1 week
            
            logger.info(f"Created spatial anchor {anchor_id} for property {property_id}")
            
            return anchor
            
        except Exception as e:
            logger.error(f"Error creating spatial anchor: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create spatial anchor"
            )
    
    async def _get_property_data(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get property data (mock implementation)."""
        # This would integrate with actual property database
        mock_properties = {
            "prop_austin_001": {
                "property_id": "prop_austin_001",
                "mls_id": "ATX123456",
                "address": "1234 Hill Country Drive, Austin, TX 78746",
                "price": 750000,
                "price_per_sqft": 300,
                "bedrooms": 4,
                "bathrooms": 3.5,
                "sqft": 2500,
                "lot_size": "0.25 acres",
                "year_built": 2018,
                "property_type": "Single Family",
                "days_on_market": 12,
                "neighborhood": "Hill Country",
                "school_district": "Lake Travis ISD",
                "latitude": 30.2672,
                "longitude": -97.7431
            }
        }
        
        return mock_properties.get(property_id)
    
    async def _generate_ar_property_insights(
        self,
        property_data: Dict[str, Any],
        user_location: Optional[Dict[str, float]]
    ) -> Dict[str, Any]:
        """Generate AI insights for AR overlay."""
        try:
            # Use Claude assistant to generate contextual insights
            context = {
                "property": property_data,
                "user_location": user_location,
                "ar_context": True
            }
            
            # This would call Claude for real insights
            # For now, return mock insights
            return {
                "insights": f"This {property_data.get('property_type', 'property')} in {property_data.get('neighborhood', 'the area')} shows strong investment potential with recent appreciation trends.",
                "highlights": [
                    "Recently built (2018) with modern features",
                    "Excellent school district rating",
                    "Growing neighborhood with tech proximity"
                ],
                "concerns": [
                    "Slightly above market average",
                    "Limited public transportation"
                ],
                "investment_score": 85,
                "recommendation": "Strong buy for long-term appreciation"
            }
        except Exception as e:
            logger.warning(f"Could not generate AI insights: {e}")
            return {"insights": "AI insights temporarily unavailable"}
    
    async def _generate_vr_waypoint_insights(
        self,
        property_data: Dict[str, Any],
        room_name: str,
        room_description: str
    ) -> str:
        """Generate AI insights for VR waypoint."""
        try:
            # This would call Claude for room-specific insights
            return f"This {room_name.lower()} showcases the property's {room_description.lower()}. Notice the high-quality finishes and thoughtful layout that maximizes both space and natural light."
        except Exception as e:
            logger.warning(f"Could not generate waypoint insights: {e}")
            return ""

# Initialize service
ar_visualization_service = ARVisualizationService()

# Routes

@router.post("/visualize/setup", response_model=Dict[str, Any])
async def setup_property_visualization(
    request: PropertyVisualizationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Set up AR/VR visualization for a property.
    
    Returns configuration data for AR overlays, VR tour waypoints,
    and 3D models based on device capabilities and user preferences.
    """
    try:
        user_id = current_user["user_id"]
        
        # Generate appropriate visualization content
        visualization_data = {}
        
        if request.visualization_type in ["ar_overlay", "mixed_reality"]:
            # Generate AR overlays
            ar_overlays = await ar_visualization_service.generate_property_ar_overlays(
                request.property_id,
                request.user_location,
                request.device_capabilities
            )
            visualization_data["ar_overlays"] = [overlay.dict() for overlay in ar_overlays]
        
        if request.visualization_type in ["vr_tour", "mixed_reality"]:
            # Generate VR tour waypoints
            vr_waypoints = await ar_visualization_service.generate_vr_tour_waypoints(
                request.property_id,
                request.quality_preference
            )
            visualization_data["vr_waypoints"] = [waypoint.dict() for waypoint in vr_waypoints]
        
        # Add device-specific optimizations
        device_optimizations = {
            "texture_quality": "high" if request.quality_preference == "ultra" else "medium",
            "polygon_count": "high" if request.device_capabilities.get("high_performance", False) else "medium",
            "lighting_quality": "realtime" if request.device_capabilities.get("supports_realtime_lighting", False) else "baked",
            "occlusion_enabled": request.device_capabilities.get("supports_occlusion", False),
            "hand_tracking": request.device_capabilities.get("supports_hand_tracking", False)
        }
        
        return {
            "property_id": request.property_id,
            "visualization_type": request.visualization_type,
            "visualization_data": visualization_data,
            "device_optimizations": device_optimizations,
            "session_id": str(uuid.uuid4()),
            "expires_at": (datetime.now() + timedelta(hours=4)).isoformat(),
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Property visualization setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Visualization setup failed"
        )

@router.get("/property/{property_id}/model", response_model=Property3DModel)
async def get_property_3d_model(
    property_id: str,
    quality: str = Query(default="medium", pattern="^(Union[low, medium]|Union[high, ultra])$"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get 3D model data for property visualization.
    
    Returns optimized 3D model URLs and metadata for AR/VR rendering.
    Includes LOD (Level of Detail) variants for performance optimization.
    """
    try:
        # Get property data to validate existence
        property_data = await ar_visualization_service._get_property_data(property_id)
        if not property_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Property {property_id} not found"
            )
        
        # Generate 3D model data (mock implementation)
        model = Property3DModel(
            model_id=f"model_{property_id}_{quality}",
            property_id=property_id,
            model_format="gltf",
            model_url=f"https://3d-models.example.com/{property_id}/{quality}/model.gltf",
            texture_urls=[
                f"https://3d-models.example.com/{property_id}/{quality}/exterior.jpg",
                f"https://3d-models.example.com/{property_id}/{quality}/interior.jpg",
                f"https://3d-models.example.com/{property_id}/{quality}/materials.jpg"
            ],
            scale_factor=1.0,
            origin_offset=SpatialCoordinate(x=0.0, y=0.0, z=0.0),
            bounding_box={
                "min": SpatialCoordinate(x=-15.0, y=0.0, z=-20.0),
                "max": SpatialCoordinate(x=15.0, y=8.0, z=20.0)
            },
            level_of_detail=[
                {
                    "distance": 0.0,
                    "polygon_count": 50000,
                    "texture_resolution": 2048,
                    "model_url": f"https://3d-models.example.com/{property_id}/{quality}/model_lod0.gltf"
                },
                {
                    "distance": 50.0,
                    "polygon_count": 10000,
                    "texture_resolution": 1024,
                    "model_url": f"https://3d-models.example.com/{property_id}/{quality}/model_lod1.gltf"
                },
                {
                    "distance": 200.0,
                    "polygon_count": 2000,
                    "texture_resolution": 512,
                    "model_url": f"https://3d-models.example.com/{property_id}/{quality}/model_lod2.gltf"
                }
            ],
            interactive_elements=[
                {
                    "id": "front_door",
                    "type": "door",
                    "position": {"x": 0.0, "y": 0.0, "z": -10.0},
                    "animation": "door_open",
                    "interaction": "tap_to_open"
                },
                {
                    "id": "windows",
                    "type": "window_group",
                    "count": 12,
                    "interaction": "tap_for_interior_view"
                }
            ]
        )
        
        return model
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"3D model retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="3D model retrieval failed"
        )

@router.post("/anchors/create", response_model=ARSpatialAnchor)
async def create_spatial_anchor(
    anchor_request: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create persistent spatial anchor for AR content.
    
    Anchors allow AR overlays to persist in real-world locations
    across multiple sessions and users.
    """
    try:
        user_id = current_user["user_id"]
        property_id = anchor_request.get("property_id")
        
        if not property_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Property ID is required"
            )
        
        anchor = await ar_visualization_service.create_spatial_anchor(
            property_id,
            anchor_request,
            user_id
        )
        
        return anchor
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Spatial anchor creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Spatial anchor creation failed"
        )

@router.get("/anchors/property/{property_id}")
async def get_property_anchors(
    property_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all spatial anchors for a property.
    
    Returns anchors created by all users for collaborative AR experiences.
    """
    try:
        cache = get_cache_service()
        
        # Get anchor IDs for property
        anchor_ids = await cache.get(f"property_anchors:{property_id}") or []
        
        # Retrieve anchor data
        anchors = []
        for anchor_id in anchor_ids:
            anchor_data = await cache.get(f"spatial_anchor:{anchor_id}")
            if anchor_data:
                anchors.append(ARSpatialAnchor(**anchor_data))
        
        return {
            "property_id": property_id,
            "anchors": [anchor.dict() for anchor in anchors],
            "count": len(anchors)
        }
        
    except Exception as e:
        logger.error(f"Property anchors retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Property anchors retrieval failed"
        )

@router.post("/mapping/upload")
async def upload_spatial_mapping(
    mapping_data: SpatialMappingData,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Upload spatial mapping data from AR device.
    
    Improves AR accuracy and enables better occlusion handling
    for future sessions.
    """
    try:
        cache = get_cache_service()
        user_id = current_user["user_id"]
        
        # Store mapping data
        mapping_key = f"spatial_mapping:{mapping_data.mapping_id}"
        mapping_record = {
            "user_id": user_id,
            "mapping_data": mapping_data.dict(),
            "uploaded_at": datetime.now().isoformat(),
            "tracking_quality": mapping_data.tracking_quality
        }
        
        await cache.set(mapping_key, mapping_record, ttl=86400 * 7)  # Keep for 1 week
        
        # Update mapping quality metrics
        quality_metrics = {
            "point_count": len(mapping_data.point_cloud),
            "plane_count": len(mapping_data.plane_data),
            "tracking_quality": mapping_data.tracking_quality,
            "has_lighting_data": mapping_data.lighting_estimation is not None,
            "has_occlusion_mesh": len(mapping_data.occlusion_mesh) > 0
        }
        
        return {
            "success": True,
            "mapping_id": mapping_data.mapping_id,
            "quality_metrics": quality_metrics,
            "improvements_enabled": [
                "Better occlusion handling" if quality_metrics["has_occlusion_mesh"] else None,
                "Improved lighting" if quality_metrics["has_lighting_data"] else None,
                "Enhanced plane detection" if quality_metrics["plane_count"] > 0 else None
            ]
        }
        
    except Exception as e:
        logger.error(f"Spatial mapping upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Spatial mapping upload failed"
        )

@router.get("/tour/{property_id}/waypoints")
async def get_vr_tour_waypoints(
    property_id: str,
    quality: str = Query(default="balanced", pattern="^(Union[low, balanced]|Union[high, ultra])$"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get VR tour waypoints for immersive property exploration.
    
    Returns optimized waypoints with 360° content and AI-generated
    insights for each room and area.
    """
    try:
        waypoints = await ar_visualization_service.generate_vr_tour_waypoints(
            property_id,
            quality
        )
        
        return {
            "property_id": property_id,
            "waypoints": [waypoint.dict() for waypoint in waypoints],
            "tour_duration_estimate": len(waypoints) * 2,  # 2 minutes per waypoint
            "total_waypoints": len(waypoints),
            "quality_level": quality
        }
        
    except Exception as e:
        logger.error(f"VR tour waypoints retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="VR tour waypoints retrieval failed"
        )

@router.get("/capabilities/check")
async def check_device_capabilities(
    device_type: str = Query(..., description="Device type: ios, android, hololens, quest"),
    os_version: str = Query(..., description="Operating system version"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Check device AR/VR capabilities and recommend optimal settings.
    
    Returns device-specific capability matrix and performance recommendations.
    """
    try:
        # Device capability matrix (mock implementation)
        capabilities = {
            "ios": {
                "ar_supported": True,
                "vr_supported": False,
                "hand_tracking": False,
                "face_tracking": True,
                "plane_detection": True,
                "occlusion": True,
                "lighting_estimation": True,
                "cloud_anchors": True,
                "recommended_quality": "high"
            },
            "android": {
                "ar_supported": True,
                "vr_supported": True,
                "hand_tracking": True,
                "face_tracking": True,
                "plane_detection": True,
                "occlusion": False,  # Varies by device
                "lighting_estimation": True,
                "cloud_anchors": True,
                "recommended_quality": "balanced"
            },
            "hololens": {
                "ar_supported": True,
                "vr_supported": True,
                "hand_tracking": True,
                "face_tracking": False,
                "plane_detection": True,
                "occlusion": True,
                "lighting_estimation": True,
                "cloud_anchors": True,
                "recommended_quality": "ultra"
            },
            "quest": {
                "ar_supported": True,
                "vr_supported": True,
                "hand_tracking": True,
                "face_tracking": False,
                "plane_detection": True,
                "occlusion": True,
                "lighting_estimation": False,
                "cloud_anchors": False,
                "recommended_quality": "high"
            }
        }
        
        device_caps = capabilities.get(device_type.lower(), {
            "ar_supported": False,
            "vr_supported": False,
            "recommended_quality": "low"
        })
        
        # Add version-specific adjustments
        if device_type.lower() == "ios" and float(os_version.split('.')[0]) < 14:
            device_caps["occlusion"] = False
            device_caps["recommended_quality"] = "balanced"
        
        return {
            "device_type": device_type,
            "os_version": os_version,
            "capabilities": device_caps,
            "features_available": [
                feature for feature, supported in device_caps.items() 
                if supported and feature not in ["recommended_quality"]
            ],
            "recommendations": {
                "quality_setting": device_caps.get("recommended_quality", "balanced"),
                "enable_features": [
                    "plane_detection" if device_caps.get("plane_detection") else None,
                    "lighting_estimation" if device_caps.get("lighting_estimation") else None,
                    "hand_tracking" if device_caps.get("hand_tracking") else None
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Device capabilities check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Device capabilities check failed"
        )