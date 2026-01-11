"""
Mobile Agent Assistance System

Location-aware AI assistance for real estate agents in the field.
Provides real-time market intelligence, property suggestions, and
conversational support optimized for mobile interactions.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import math

from .advanced_market_intelligence import AdvancedMarketIntelligenceEngine
from .predictive_engagement_engine import predictive_engagement_engine
from .redis_conversation_service import redis_conversation_service
from ..ghl_utils.config import settings

logger = logging.getLogger(__name__)


class LocationContext(Enum):
    """Agent location context types"""
    OFFICE = "office"
    CLIENT_MEETING = "client_meeting"
    PROPERTY_SHOWING = "property_showing"
    NEIGHBORHOOD_TOUR = "neighborhood_tour"
    DRIVING = "driving"
    HOME = "home"
    OTHER = "other"


class AssistanceType(Enum):
    """Types of mobile assistance"""
    PROPERTY_LOOKUP = "property_lookup"
    MARKET_UPDATE = "market_update"
    CLIENT_PREP = "client_prep"
    NEIGHBORHOOD_INFO = "neighborhood_info"
    ROUTE_OPTIMIZATION = "route_optimization"
    EMERGENCY_SUPPORT = "emergency_support"
    QUICK_FACTS = "quick_facts"


@dataclass
class LocationData:
    """Agent location and context data"""
    latitude: float
    longitude: float
    accuracy: float  # meters
    timestamp: datetime
    context: LocationContext
    address: Optional[str] = None
    nearby_properties: Optional[List[str]] = None


@dataclass
class NearbyProperty:
    """Property near agent's current location"""
    property_id: str
    address: str
    distance_meters: float
    estimated_value: int
    property_type: str
    bedrooms: int
    bathrooms: int
    sqft: int
    status: str  # active, pending, sold, off-market
    listing_agent: Optional[str] = None


@dataclass
class MobileAssistanceResponse:
    """Response for mobile assistance request"""
    assistance_type: AssistanceType
    response_text: str
    quick_actions: List[Dict[str, str]]
    location_context: Dict[str, Any]
    relevant_properties: List[NearbyProperty]
    market_insights: List[str]
    suggested_follow_up: Optional[str]
    confidence_score: float


class MobileAgentAssistance:
    """
    Mobile assistance system for real estate agents in the field.

    Features:
    - Location-aware property suggestions
    - Real-time market intelligence
    - Quick access to client information
    - Route optimization for property tours
    - Emergency client support capabilities
    - Voice-optimized responses for hands-free use
    """

    def __init__(self):
        self.market_intelligence = AdvancedMarketIntelligenceEngine("default_location")
        self.engagement_engine = predictive_engagement_engine
        self.redis_service = redis_conversation_service

        # Location tracking cache (agent_id -> LocationData)
        self.agent_locations = {}

        # Geofence radius for property searches (meters)
        self.proximity_radius = 1000  # 1km default

    async def update_agent_location(
        self,
        agent_id: str,
        latitude: float,
        longitude: float,
        accuracy: float,
        context: LocationContext = LocationContext.OTHER
    ) -> Dict[str, Any]:
        """
        Update agent's location and provide contextual assistance.

        Args:
            agent_id: Agent identifier
            latitude: GPS latitude
            longitude: GPS longitude
            accuracy: Location accuracy in meters
            context: Current context (meeting, showing, etc.)

        Returns:
            Location update response with contextual assistance
        """
        try:
            # Create location data
            location_data = LocationData(
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy,
                timestamp=datetime.now(),
                context=context
            )

            # Geocode address if possible
            location_data.address = await self._geocode_location(latitude, longitude)

            # Store location
            self.agent_locations[agent_id] = location_data

            # Get nearby properties
            nearby_properties = await self._find_nearby_properties(
                latitude, longitude, self.proximity_radius
            )
            location_data.nearby_properties = [p.property_id for p in nearby_properties]

            # Generate contextual assistance
            assistance = await self._generate_contextual_assistance(
                agent_id, location_data, nearby_properties
            )

            logger.info(f"Updated location for agent {agent_id}: {context.value} at ({latitude:.4f}, {longitude:.4f})")

            return {
                "agent_id": agent_id,
                "location_updated": True,
                "context": context.value,
                "address": location_data.address,
                "nearby_properties_count": len(nearby_properties),
                "contextual_assistance": assistance,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error updating agent location: {str(e)}")
            return {
                "error": str(e),
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat()
            }

    async def get_mobile_assistance(
        self,
        agent_id: str,
        assistance_type: AssistanceType,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> MobileAssistanceResponse:
        """
        Get mobile assistance for specific request.

        Args:
            agent_id: Agent identifier
            assistance_type: Type of assistance needed
            query: Specific query or request
            context: Additional context (client info, property details, etc.)

        Returns:
            MobileAssistanceResponse with tailored assistance
        """
        try:
            # Get agent's current location
            location_data = self.agent_locations.get(agent_id)

            # Generate assistance based on type
            if assistance_type == AssistanceType.PROPERTY_LOOKUP:
                response = await self._handle_property_lookup(agent_id, query, location_data, context)
            elif assistance_type == AssistanceType.MARKET_UPDATE:
                response = await self._handle_market_update(agent_id, query, location_data, context)
            elif assistance_type == AssistanceType.CLIENT_PREP:
                response = await self._handle_client_prep(agent_id, query, location_data, context)
            elif assistance_type == AssistanceType.NEIGHBORHOOD_INFO:
                response = await self._handle_neighborhood_info(agent_id, query, location_data, context)
            elif assistance_type == AssistanceType.ROUTE_OPTIMIZATION:
                response = await self._handle_route_optimization(agent_id, query, location_data, context)
            elif assistance_type == AssistanceType.EMERGENCY_SUPPORT:
                response = await self._handle_emergency_support(agent_id, query, location_data, context)
            else:  # QUICK_FACTS
                response = await self._handle_quick_facts(agent_id, query, location_data, context)

            logger.info(f"Generated mobile assistance for {agent_id}: {assistance_type.value}")
            return response

        except Exception as e:
            logger.error(f"Error generating mobile assistance: {str(e)}")
            return await self._generate_fallback_response(agent_id, assistance_type, query)

    async def get_nearby_opportunities(
        self,
        agent_id: str,
        radius_meters: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get nearby property opportunities based on agent's location.

        Args:
            agent_id: Agent identifier
            radius_meters: Search radius (defaults to 1km)

        Returns:
            Nearby opportunities with market intelligence
        """
        try:
            location_data = self.agent_locations.get(agent_id)
            if not location_data:
                return {"error": "Agent location not available"}

            radius = radius_meters or self.proximity_radius

            # Find nearby properties
            nearby_properties = await self._find_nearby_properties(
                location_data.latitude, location_data.longitude, radius
            )

            # Get market intelligence for area
            area_name = await self._get_area_name(location_data.latitude, location_data.longitude)
            market_context = await self.market_intelligence.get_claude_market_context(area_name)

            # Categorize opportunities
            opportunities = {
                "listings": [p for p in nearby_properties if p.status == "active"],
                "pending": [p for p in nearby_properties if p.status == "pending"],
                "recent_sales": [p for p in nearby_properties if p.status == "sold"],
                "off_market": [p for p in nearby_properties if p.status == "off-market"]
            }

            # Generate insights
            insights = await self._analyze_local_opportunities(opportunities, market_context)

            return {
                "agent_id": agent_id,
                "location": {
                    "latitude": location_data.latitude,
                    "longitude": location_data.longitude,
                    "address": location_data.address
                },
                "search_radius_meters": radius,
                "opportunities": opportunities,
                "market_insights": insights,
                "total_properties": len(nearby_properties),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting nearby opportunities: {str(e)}")
            return {
                "error": str(e),
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat()
            }

    async def optimize_route(
        self,
        agent_id: str,
        destinations: List[Dict[str, Any]],
        start_location: Optional[Tuple[float, float]] = None
    ) -> Dict[str, Any]:
        """
        Optimize route for multiple property showings or client meetings.

        Args:
            agent_id: Agent identifier
            destinations: List of destinations with addresses/coordinates
            start_location: Optional start location (uses current location if not provided)

        Returns:
            Optimized route with timing and insights
        """
        try:
            # Get starting location
            if start_location:
                start_lat, start_lon = start_location
            else:
                location_data = self.agent_locations.get(agent_id)
                if not location_data:
                    return {"error": "Agent location not available and no start location provided"}
                start_lat, start_lon = location_data.latitude, location_data.longitude

            # Optimize route (simplified implementation)
            optimized_route = await self._calculate_optimal_route(
                (start_lat, start_lon), destinations
            )

            # Calculate timing estimates
            timing_estimates = await self._calculate_timing_estimates(optimized_route)

            # Generate location-specific insights for each stop
            location_insights = []
            for stop in optimized_route:
                insight = await self._get_location_insights(stop)
                location_insights.append(insight)

            return {
                "agent_id": agent_id,
                "optimized_route": optimized_route,
                "timing_estimates": timing_estimates,
                "total_distance_km": sum(stop.get("distance_to_next", 0) for stop in optimized_route),
                "estimated_total_time_minutes": sum(timing_estimates.values()),
                "location_insights": location_insights,
                "recommendations": await self._generate_route_recommendations(optimized_route),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error optimizing route: {str(e)}")
            return {
                "error": str(e),
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat()
            }

    async def _geocode_location(self, latitude: float, longitude: float) -> Optional[str]:
        """Convert coordinates to address (demo implementation)"""
        # In production, use Google Maps Geocoding API
        await asyncio.sleep(0.1)  # Simulate API call

        # Generate demo address based on coordinates
        street_num = int(abs(latitude * longitude * 10000)) % 9999 + 1
        streets = ["Main St", "Oak Ave", "Park Blvd", "River Dr", "Hill Rd"]
        street = streets[int(abs(latitude * 1000)) % len(streets)]

        return f"{street_num} {street}, Austin, TX"

    async def _find_nearby_properties(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int
    ) -> List[NearbyProperty]:
        """Find properties within radius of location"""
        properties = []

        # Generate demo properties based on location
        property_count = 5 + hash(f"{latitude}{longitude}") % 10

        for i in range(property_count):
            # Generate nearby coordinates
            angle = (i * 2 * math.pi) / property_count
            distance = (hash(f"{latitude}{longitude}{i}") % radius_meters) * 0.8

            # Convert to lat/lon offset (approximate)
            lat_offset = (distance * math.cos(angle)) / 111000  # meters to degrees
            lon_offset = (distance * math.sin(angle)) / (111000 * math.cos(math.radians(latitude)))

            prop_lat = latitude + lat_offset
            prop_lon = longitude + lon_offset

            # Generate property data
            prop_id = f"prop_{hash(f'{prop_lat}{prop_lon}') % 10000}"

            properties.append(NearbyProperty(
                property_id=prop_id,
                address=await self._geocode_location(prop_lat, prop_lon) or f"{1000 + i} Local St",
                distance_meters=distance,
                estimated_value=300000 + (hash(prop_id) % 700000),
                property_type=["Single Family", "Condo", "Townhouse"][hash(prop_id) % 3],
                bedrooms=2 + (hash(prop_id + "bed") % 4),
                bathrooms=1 + (hash(prop_id + "bath") % 3),
                sqft=1200 + (hash(prop_id + "sqft") % 2000),
                status=["active", "pending", "sold", "off-market"][hash(prop_id + "status") % 4],
                listing_agent=f"Agent_{hash(prop_id) % 100}" if hash(prop_id) % 3 == 0 else None
            ))

        return sorted(properties, key=lambda p: p.distance_meters)

    async def _generate_contextual_assistance(
        self,
        agent_id: str,
        location_data: LocationData,
        nearby_properties: List[NearbyProperty]
    ) -> Dict[str, Any]:
        """Generate contextual assistance based on location and context"""

        assistance = {
            "context": location_data.context.value,
            "suggestions": [],
            "quick_actions": [],
            "alerts": []
        }

        if location_data.context == LocationContext.PROPERTY_SHOWING:
            assistance["suggestions"].extend([
                "Property comparison data is available for this area",
                "Market insights ready for client questions",
                f"Found {len(nearby_properties)} comparable properties within 1km"
            ])
            assistance["quick_actions"].extend([
                {"action": "get_comps", "label": "Get Comparables"},
                {"action": "market_update", "label": "Market Update"},
                {"action": "neighborhood_info", "label": "Area Info"}
            ])

        elif location_data.context == LocationContext.CLIENT_MEETING:
            assistance["suggestions"].extend([
                "Client preparation materials available",
                "Recent market activity in this area",
                "Property recommendations ready"
            ])
            assistance["quick_actions"].extend([
                {"action": "client_prep", "label": "Client Prep"},
                {"action": "property_search", "label": "Find Properties"},
                {"action": "market_brief", "label": "Market Brief"}
            ])

        elif location_data.context == LocationContext.NEIGHBORHOOD_TOUR:
            assistance["suggestions"].extend([
                "Neighborhood insights and amenities available",
                "Recent sales data for the area",
                "Local market trends and pricing"
            ])
            assistance["quick_actions"].extend([
                {"action": "neighborhood_guide", "label": "Area Guide"},
                {"action": "local_amenities", "label": "Amenities"},
                {"action": "school_info", "label": "Schools"}
            ])

        # Add general quick actions
        assistance["quick_actions"].extend([
            {"action": "voice_assistant", "label": "Voice Assistant"},
            {"action": "emergency_support", "label": "Get Help"}
        ])

        return assistance

    async def _handle_property_lookup(
        self,
        agent_id: str,
        query: str,
        location_data: Optional[LocationData],
        context: Optional[Dict[str, Any]]
    ) -> MobileAssistanceResponse:
        """Handle property lookup requests"""

        response_text = "Let me find property information for you."
        relevant_properties = []
        quick_actions = []

        if location_data:
            # Find nearby properties
            nearby = await self._find_nearby_properties(
                location_data.latitude, location_data.longitude, self.proximity_radius
            )
            relevant_properties = nearby[:5]  # Top 5 closest

            if "comps" in query.lower() or "comparable" in query.lower():
                response_text = f"Found {len(relevant_properties)} comparable properties within 1km. "
                response_text += "These properties show similar characteristics and recent market activity."

                quick_actions = [
                    {"action": "view_details", "label": "View Details"},
                    {"action": "get_more_comps", "label": "Find More"},
                    {"action": "price_analysis", "label": "Price Analysis"}
                ]

            elif "active" in query.lower() or "listing" in query.lower():
                active_properties = [p for p in relevant_properties if p.status == "active"]
                response_text = f"Found {len(active_properties)} active listings nearby. "
                response_text += "These properties are currently available for viewing."

        else:
            response_text = "I need your location to find nearby properties. Please share your location for property recommendations."

        return MobileAssistanceResponse(
            assistance_type=AssistanceType.PROPERTY_LOOKUP,
            response_text=response_text,
            quick_actions=quick_actions,
            location_context={"has_location": location_data is not None},
            relevant_properties=relevant_properties,
            market_insights=[],
            suggested_follow_up="Would you like detailed information about any specific property?",
            confidence_score=0.8 if location_data else 0.5
        )

    async def _handle_market_update(
        self,
        agent_id: str,
        query: str,
        location_data: Optional[LocationData],
        context: Optional[Dict[str, Any]]
    ) -> MobileAssistanceResponse:
        """Handle market update requests"""

        market_insights = []
        response_text = "Here's the current market update for your area."

        if location_data:
            # Get area name and market intelligence
            area_name = await self._get_area_name(location_data.latitude, location_data.longitude)
            market_context = await self.market_intelligence.get_claude_market_context(area_name)

            if market_context and not market_context.get("error"):
                market_insights = market_context.get("key_insights", [])
                market_summary = market_context.get("market_summary", {})

                response_text = f"Market update for {area_name}: "
                response_text += f"Market is {market_summary.get('activity_level', 'Moderate').lower()} activity "
                response_text += f"with {market_summary.get('trend_direction', 'stable').lower()} trend."

        quick_actions = [
            {"action": "full_report", "label": "Full Report"},
            {"action": "price_trends", "label": "Price Trends"},
            {"action": "investment_outlook", "label": "Investment View"}
        ]

        return MobileAssistanceResponse(
            assistance_type=AssistanceType.MARKET_UPDATE,
            response_text=response_text,
            quick_actions=quick_actions,
            location_context={"area": area_name if location_data else "Unknown"},
            relevant_properties=[],
            market_insights=market_insights[:3],  # Top 3 insights
            suggested_follow_up="Would you like detailed price trends or investment analysis?",
            confidence_score=0.9 if location_data else 0.4
        )

    async def _handle_client_prep(
        self,
        agent_id: str,
        query: str,
        location_data: Optional[LocationData],
        context: Optional[Dict[str, Any]]
    ) -> MobileAssistanceResponse:
        """Handle client preparation requests"""

        response_text = "Client preparation materials ready."
        quick_actions = [
            {"action": "client_profile", "label": "Client Profile"},
            {"action": "talking_points", "label": "Talking Points"},
            {"action": "property_matches", "label": "Property Matches"}
        ]

        # Get client context if available
        client_info = context.get("client_info", {}) if context else {}

        if client_info:
            client_name = client_info.get("name", "Client")
            budget = client_info.get("budget", 0)

            response_text = f"Preparation for {client_name} meeting ready. "

            if budget > 0:
                response_text += f"Budget: ${budget:,.0f}. "

            # Get engagement prediction for client prep
            lead_id = client_info.get("lead_id")
            if lead_id:
                try:
                    prediction = await self.engagement_engine.predict_optimal_engagement(
                        lead_id, agent_id, context
                    )
                    response_text += f"Recommended approach: {prediction.recommended_message}"

                    quick_actions.extend([
                        {"action": "engagement_strategy", "label": "Strategy"},
                        {"action": "objection_handling", "label": "Objections"}
                    ])
                except:
                    pass

        market_insights = []
        if location_data:
            area_name = await self._get_area_name(location_data.latitude, location_data.longitude)
            market_context = await self.market_intelligence.get_claude_market_context(area_name)
            if market_context:
                market_insights = market_context.get("agent_talking_points", [])[:2]

        return MobileAssistanceResponse(
            assistance_type=AssistanceType.CLIENT_PREP,
            response_text=response_text,
            quick_actions=quick_actions,
            location_context={"client_meeting": True},
            relevant_properties=[],
            market_insights=market_insights,
            suggested_follow_up="Need specific talking points or property recommendations?",
            confidence_score=0.85
        )

    async def _handle_neighborhood_info(
        self,
        agent_id: str,
        query: str,
        location_data: Optional[LocationData],
        context: Optional[Dict[str, Any]]
    ) -> MobileAssistanceResponse:
        """Handle neighborhood information requests"""

        response_text = "Neighborhood information available."
        market_insights = []

        if location_data:
            area_name = await self._get_area_name(location_data.latitude, location_data.longitude)

            # Generate neighborhood insights (demo implementation)
            insights = await self._get_neighborhood_insights(location_data.latitude, location_data.longitude)
            market_insights = insights

            response_text = f"Neighborhood guide for {area_name}: "
            response_text += "Local amenities, schools, and market activity information available."

        quick_actions = [
            {"action": "amenities", "label": "Amenities"},
            {"action": "schools", "label": "Schools"},
            {"action": "transportation", "label": "Transport"},
            {"action": "safety_info", "label": "Safety"}
        ]

        return MobileAssistanceResponse(
            assistance_type=AssistanceType.NEIGHBORHOOD_INFO,
            response_text=response_text,
            quick_actions=quick_actions,
            location_context={"neighborhood": True},
            relevant_properties=[],
            market_insights=market_insights,
            suggested_follow_up="Would you like specific details about schools or amenities?",
            confidence_score=0.8
        )

    async def _handle_route_optimization(
        self,
        agent_id: str,
        query: str,
        location_data: Optional[LocationData],
        context: Optional[Dict[str, Any]]
    ) -> MobileAssistanceResponse:
        """Handle route optimization requests"""

        response_text = "Route optimization available."

        # Get destinations from context
        destinations = context.get("destinations", []) if context else []

        if destinations:
            response_text = f"Optimizing route for {len(destinations)} destinations. "
            response_text += "Estimated time savings and efficient ordering calculated."
        else:
            response_text = "Please provide destination addresses for route optimization."

        quick_actions = [
            {"action": "add_destination", "label": "Add Stop"},
            {"action": "optimize_route", "label": "Optimize"},
            {"action": "traffic_update", "label": "Traffic"},
            {"action": "send_eta", "label": "Send ETA"}
        ]

        return MobileAssistanceResponse(
            assistance_type=AssistanceType.ROUTE_OPTIMIZATION,
            response_text=response_text,
            quick_actions=quick_actions,
            location_context={"route_planning": True},
            relevant_properties=[],
            market_insights=[],
            suggested_follow_up="Ready to start navigation or need to add more stops?",
            confidence_score=0.9 if destinations else 0.6
        )

    async def _handle_emergency_support(
        self,
        agent_id: str,
        query: str,
        location_data: Optional[LocationData],
        context: Optional[Dict[str, Any]]
    ) -> MobileAssistanceResponse:
        """Handle emergency support requests"""

        response_text = "Emergency support activated. How can I help you immediately?"

        quick_actions = [
            {"action": "call_broker", "label": "Call Broker"},
            {"action": "client_contact", "label": "Contact Client"},
            {"action": "office_support", "label": "Office Help"},
            {"action": "technical_support", "label": "Tech Support"}
        ]

        # Check for specific emergency types
        if "client" in query.lower():
            response_text = "Client support emergency detected. Broker contact information and client management tools available."
        elif "technical" in query.lower() or "app" in query.lower():
            response_text = "Technical support activated. Common solutions and support contact information available."

        return MobileAssistanceResponse(
            assistance_type=AssistanceType.EMERGENCY_SUPPORT,
            response_text=response_text,
            quick_actions=quick_actions,
            location_context={"emergency": True},
            relevant_properties=[],
            market_insights=[],
            suggested_follow_up="Is this resolved or do you need additional assistance?",
            confidence_score=1.0
        )

    async def _handle_quick_facts(
        self,
        agent_id: str,
        query: str,
        location_data: Optional[LocationData],
        context: Optional[Dict[str, Any]]
    ) -> MobileAssistanceResponse:
        """Handle quick facts and general queries"""

        response_text = "Quick facts available."
        market_insights = []

        # Parse query for specific information
        if "price" in query.lower():
            if location_data:
                area_name = await self._get_area_name(location_data.latitude, location_data.longitude)
                response_text = f"Average home price in {area_name} is approximately $650,000. Median price per sqft is $220."
                market_insights = [f"Price trends for {area_name} area"]

        elif "market" in query.lower():
            response_text = "Current market conditions show balanced activity with moderate inventory levels."
            market_insights = ["Market velocity stable", "Inventory levels normal"]

        elif "school" in query.lower():
            response_text = "Local school information available. Top-rated districts in the area with performance data."
            market_insights = ["School district ratings", "Educational amenities"]

        quick_actions = [
            {"action": "more_details", "label": "More Details"},
            {"action": "related_info", "label": "Related Info"},
            {"action": "save_info", "label": "Save"}
        ]

        return MobileAssistanceResponse(
            assistance_type=AssistanceType.QUICK_FACTS,
            response_text=response_text,
            quick_actions=quick_actions,
            location_context={"quick_lookup": True},
            relevant_properties=[],
            market_insights=market_insights,
            suggested_follow_up="Need more detailed information about anything specific?",
            confidence_score=0.75
        )

    async def _get_area_name(self, latitude: float, longitude: float) -> str:
        """Get area name from coordinates"""
        # Simplified area mapping for demo
        if 30.25 <= latitude <= 30.35 and -97.8 <= longitude <= -97.7:
            return "Downtown Austin"
        elif 30.35 <= latitude <= 30.45 and -97.8 <= longitude <= -97.7:
            return "North Austin"
        else:
            return "Austin Metro"

    async def _get_neighborhood_insights(self, latitude: float, longitude: float) -> List[str]:
        """Get neighborhood-specific insights"""
        area_name = await self._get_area_name(latitude, longitude)

        insights = [
            f"Growing area with strong community development",
            f"Access to major employment centers",
            f"Good walkability and public amenities"
        ]

        if "Downtown" in area_name:
            insights.extend([
                "Urban lifestyle with entertainment districts",
                "Public transportation access"
            ])
        elif "North" in area_name:
            insights.extend([
                "Family-friendly neighborhoods",
                "Top-rated school districts"
            ])

        return insights[:3]

    async def _calculate_optimal_route(
        self,
        start: Tuple[float, float],
        destinations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Calculate optimal route for multiple destinations"""

        # Simplified route optimization (in production, use Google Maps API)
        optimized_stops = []

        current_location = start
        remaining_destinations = destinations.copy()

        while remaining_destinations:
            # Find closest destination
            closest_dest = min(
                remaining_destinations,
                key=lambda d: self._calculate_distance(
                    current_location,
                    (d.get("latitude", 0), d.get("longitude", 0))
                )
            )

            distance_to_next = self._calculate_distance(
                current_location,
                (closest_dest.get("latitude", 0), closest_dest.get("longitude", 0))
            )

            optimized_stops.append({
                **closest_dest,
                "distance_to_next": distance_to_next,
                "order": len(optimized_stops) + 1
            })

            current_location = (closest_dest.get("latitude", 0), closest_dest.get("longitude", 0))
            remaining_destinations.remove(closest_dest)

        return optimized_stops

    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate distance between two points in kilometers"""
        lat1, lon1 = point1
        lat2, lon2 = point2

        # Haversine formula
        R = 6371  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(lat1_rad) * math.cos(lat2_rad) *
             math.sin(delta_lon / 2) * math.sin(delta_lon / 2))

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        return distance

    async def _calculate_timing_estimates(self, route: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate timing estimates for route"""
        timing = {}

        for i, stop in enumerate(route):
            travel_time = stop.get("distance_to_next", 0) * 2  # 2 minutes per km (simplified)
            meeting_time = 30  # 30 minutes per stop

            timing[f"stop_{i+1}_travel"] = travel_time
            timing[f"stop_{i+1}_meeting"] = meeting_time

        return timing

    async def _get_location_insights(self, stop: Dict[str, Any]) -> Dict[str, Any]:
        """Get insights for a specific location"""
        return {
            "address": stop.get("address", "Unknown"),
            "insights": [
                "Good parking availability",
                "Professional meeting environment",
                "Easy client access"
            ],
            "recommendations": [
                "Arrive 5 minutes early",
                "Prepare market materials",
                "Check traffic before departure"
            ]
        }

    async def _generate_route_recommendations(self, route: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for the route"""
        recommendations = []

        total_distance = sum(stop.get("distance_to_next", 0) for stop in route)

        if total_distance > 20:
            recommendations.append("Consider scheduling lunch break between stops")

        if len(route) > 4:
            recommendations.append("Allow buffer time for unexpected delays")

        recommendations.append("Prepare materials for all stops before departure")
        recommendations.append("Share ETAs with clients 30 minutes before arrival")

        return recommendations

    async def _analyze_local_opportunities(
        self,
        opportunities: Dict[str, List[NearbyProperty]],
        market_context: Dict[str, Any]
    ) -> List[str]:
        """Analyze local opportunities and generate insights"""
        insights = []

        active_count = len(opportunities.get("listings", []))
        pending_count = len(opportunities.get("pending", []))

        if active_count > 0:
            insights.append(f"{active_count} active listings available for immediate showing")

        if pending_count > 0:
            insights.append(f"{pending_count} properties pending - good market activity indicator")

        # Add market context insights
        if market_context and not market_context.get("error"):
            market_insights = market_context.get("key_insights", [])
            insights.extend(market_insights[:2])

        return insights[:4]

    async def _generate_fallback_response(
        self,
        agent_id: str,
        assistance_type: AssistanceType,
        query: str
    ) -> MobileAssistanceResponse:
        """Generate fallback response when assistance fails"""
        return MobileAssistanceResponse(
            assistance_type=assistance_type,
            response_text="I'm temporarily unable to provide detailed assistance. Basic support is available.",
            quick_actions=[
                {"action": "retry", "label": "Try Again"},
                {"action": "contact_support", "label": "Get Help"}
            ],
            location_context={"error": True},
            relevant_properties=[],
            market_insights=[],
            suggested_follow_up="Please try again or contact support if the issue persists.",
            confidence_score=0.3
        )

    async def health_check(self) -> Dict[str, Any]:
        """Health check for mobile assistance system"""
        try:
            # Test location update
            test_result = await self.update_agent_location(
                "test_agent", 30.2672, -97.7431, 10.0, LocationContext.OFFICE
            )

            return {
                "status": "healthy",
                "components": {
                    "location_tracking": not test_result.get("error"),
                    "market_intelligence": hasattr(self.market_intelligence, 'get_claude_market_context'),
                    "engagement_engine": hasattr(self.engagement_engine, 'predict_optimal_engagement'),
                    "redis_service": self.redis_service.redis_client is not None
                },
                "active_agents": len(self.agent_locations),
                "last_test": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global service instance
mobile_agent_assistance = MobileAgentAssistance()