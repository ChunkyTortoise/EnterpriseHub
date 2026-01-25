"""
Mobile API Gateway - Optimized endpoints for iOS/Android apps.

Provides mobile-specific optimizations:
- Compressed response payloads
- Pagination for bandwidth efficiency
- GPS-based filtering
- Offline sync support
- Device authentication
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Header
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional, Union
import asyncio
from datetime import datetime, timedelta
import json
import logging

from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.api.middleware.jwt_auth import get_current_user
from ghl_real_estate_ai.services.ghl_service import GHLService
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mobile", tags=["Mobile API"])

class MobileDashboardResponse(BaseModel):
    """Optimized dashboard data for mobile apps."""
    leads_summary: Dict[str, Any]
    quick_actions: List[Dict[str, str]]
    notifications_count: int
    performance_metrics: Dict[str, float]
    sync_timestamp: datetime

class LocationFilter(BaseModel):
    """GPS-based location filtering."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_miles: float = Field(default=25, ge=1, le=100)

class MobileLeadUpdate(BaseModel):
    """Quick lead update for mobile."""
    status: Optional[str] = None
    notes: Optional[str] = None
    next_followup: Optional[datetime] = None
    tags: Optional[List[str]] = None

class SyncRequest(BaseModel):
    """Offline sync request."""
    device_id: str
    last_sync: datetime
    pending_operations: List[Dict[str, Any]] = []
    app_version: str

@router.get("/dashboard", response_model=MobileDashboardResponse)
async def get_mobile_dashboard(
    current_user = Depends(get_current_user),
    device_type: str = Header(default="ios", description="ios or android")
):
    """
    Get optimized dashboard data for mobile apps.
    Includes compressed metrics and quick actions.
    """
    try:
        cache = get_cache_service()
        cache_key = f"mobile_dashboard:{current_user['location_id']}:{device_type}"

        # Try cache first (2 minute TTL)
        cached_data = await cache.get(cache_key)
        if cached_data:
            return cached_data

        # Fetch data with mobile optimizations
        ghl_service = GHLService(current_user['ghl_api_key'], current_user['location_id'])
        analytics = AnalyticsService()

        # Get lead summary (compressed)
        leads = await ghl_service.get_recent_leads(limit=50)  # Mobile limit
        leads_summary = {
            "total_count": len(leads),
            "hot_leads": sum(1 for lead in leads if lead.get('status') == 'hot'),
            "pending_followup": sum(1 for lead in leads if lead.get('next_followup')),
            "new_today": sum(1 for lead in leads if _is_today(lead.get('created_date')))
        }

        # Quick actions for mobile UI
        quick_actions = [
            {"id": "add_lead", "title": "Add Lead", "icon": "person-plus"},
            {"id": "scan_card", "title": "Scan Card", "icon": "camera"},
            {"id": "voice_note", "title": "Voice Note", "icon": "mic"},
            {"id": "schedule_tour", "title": "Schedule Tour", "icon": "calendar"}
        ]

        # Performance metrics (lightweight)
        performance_metrics = {
            "conversion_rate": await analytics.get_conversion_rate(current_user['location_id']),
            "avg_response_time": await analytics.get_avg_response_time(current_user['location_id']),
            "leads_this_week": len([l for l in leads if _is_this_week(l.get('created_date'))])
        }

        dashboard_data = MobileDashboardResponse(
            leads_summary=leads_summary,
            quick_actions=quick_actions,
            notifications_count=await _get_unread_notifications_count(current_user['location_id']),
            performance_metrics=performance_metrics,
            sync_timestamp=datetime.utcnow()
        )

        # Cache for mobile performance
        await cache.set(cache_key, dashboard_data, ttl=120)

        return dashboard_data

    except Exception as e:
        logger.error(f"Mobile dashboard error: {e}")
        raise HTTPException(status_code=500, detail="Dashboard unavailable")

@router.get("/leads/nearby")
async def get_leads_nearby(
    location: LocationFilter = Depends(),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    current_user = Depends(get_current_user)
):
    """
    Get leads filtered by GPS location with pagination.
    Optimized for mobile bandwidth.
    """
    try:
        cache = get_cache_service()
        cache_key = f"leads_nearby:{current_user['location_id']}:{location.latitude}:{location.longitude}:{location.radius_miles}:{page}"

        cached_leads = await cache.get(cache_key)
        if cached_leads:
            return cached_leads

        ghl_service = GHLService(current_user['ghl_api_key'], current_user['location_id'])

        # Get all leads and filter by location
        all_leads = await ghl_service.get_recent_leads(limit=500)

        # Filter by GPS proximity (simplified calculation)
        nearby_leads = []
        for lead in all_leads:
            if _is_within_radius(
                lead.get('latitude'), lead.get('longitude'),
                location.latitude, location.longitude,
                location.radius_miles
            ):
                # Mobile-optimized lead data
                mobile_lead = {
                    "id": lead.get('id'),
                    "name": lead.get('name'),
                    "phone": lead.get('phone'),
                    "status": lead.get('status'),
                    "score": lead.get('lead_score', 0),
                    "last_contact": lead.get('last_contact'),
                    "distance_miles": _calculate_distance(
                        lead.get('latitude'), lead.get('longitude'),
                        location.latitude, location.longitude
                    ),
                    "priority": _get_mobile_priority(lead)
                }
                nearby_leads.append(mobile_lead)

        # Sort by distance and priority
        nearby_leads.sort(key=lambda x: (x['distance_miles'], -x.get('score', 0)))

        # Paginate
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_leads = nearby_leads[start_idx:end_idx]

        result = {
            "leads": paginated_leads,
            "pagination": {
                "current_page": page,
                "total_pages": (len(nearby_leads) + limit - 1) // limit,
                "total_count": len(nearby_leads),
                "has_next": end_idx < len(nearby_leads)
            },
            "search_center": {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "radius_miles": location.radius_miles
            }
        }

        # Cache for 5 minutes
        await cache.set(cache_key, result, ttl=300)

        return result

    except Exception as e:
        logger.error(f"Nearby leads error: {e}")
        raise HTTPException(status_code=500, detail="Location search failed")

@router.post("/leads/{lead_id}/quick-update")
async def quick_update_lead(
    lead_id: str,
    update_data: MobileLeadUpdate,
    current_user = Depends(get_current_user)
):
    """
    Fast lead update optimized for mobile use.
    Minimal payload, immediate response.
    """
    try:
        ghl_service = GHLService(current_user['ghl_api_key'], current_user['location_id'])

        # Build update payload
        update_payload = {}
        if update_data.status:
            update_payload['status'] = update_data.status
        if update_data.notes:
            update_payload['notes'] = update_data.notes
        if update_data.next_followup:
            update_payload['next_followup'] = update_data.next_followup.isoformat()
        if update_data.tags:
            update_payload['tags'] = update_data.tags

        # Update in GHL
        success = await ghl_service.update_lead(lead_id, update_payload)

        if success:
            # Clear related cache
            cache = get_cache_service()
            await cache.delete(f"mobile_dashboard:{current_user['location_id']}:ios")
            await cache.delete(f"mobile_dashboard:{current_user['location_id']}:android")

            return {
                "success": True,
                "lead_id": lead_id,
                "updated_fields": list(update_payload.keys()),
                "timestamp": datetime.utcnow()
            }
        else:
            raise HTTPException(status_code=400, detail="Update failed")

    except Exception as e:
        logger.error(f"Quick update error: {e}")
        raise HTTPException(status_code=500, detail="Update failed")

@router.get("/properties/swipe-stack")
async def get_property_swipe_stack(
    lead_id: Optional[str] = None,
    limit: int = Query(10, ge=5, le=20),
    current_user = Depends(get_current_user)
):
    """
    Get property matching stack for Tinder-style mobile UI.
    Optimized for Phase 7 autonomous property matching.
    """
    try:
        cache = get_cache_service()
        cache_key = f"swipe_stack:{current_user['location_id']}:{lead_id}:{limit}"

        cached_stack = await cache.get(cache_key)
        if cached_stack:
            return cached_stack

        from ghl_real_estate_ai.services.database_service import get_database
        from ghl_real_estate_ai.services.repositories.mls_repository import MLSAPIRepository
        from ghl_real_estate_ai.services.property_matching_strategy import BasicFilteringStrategy
        from ghl_real_estate_ai.services.repositories.interfaces import PropertyQuery

        db = await get_database()
        
        # 1. Get lead preferences
        preferences = {}
        if lead_id:
            lead_profile = await db.get_lead_profile_data(lead_id)
            preferences = lead_profile.get("preferences", {})
        
        # 2. Query MLS for properties
        # In production, these config values come from settings/env
        mls_repo = MLSAPIRepository({
            "api_base_url": "https://api.mlsgrid.com/v2",
            "api_key": "mock_key",
            "provider": "generic"
        })
        
        query = PropertyQuery()
        query.max_price = preferences.get("max_price") or 600000
        query.min_bedrooms = preferences.get("min_bedrooms") or 3
        query.pagination.limit = limit * 2 # Get more to allow filtering
        
        # Use mock data if MLS is not configured
        try:
            mls_result = await mls_repo.find_properties(query)
            listings = mls_result.data if mls_result.success else []
        except Exception:
            listings = []

        # 3. Fallback to mock data if no listings found
        if not listings:
            listings = [
                {
                    "id": f"prop_{i}",
                    "address": f"{100+i} Market St, Austin, TX",
                    "price": 450000 + (i * 25000),
                    "bedrooms": 3 + (i % 2),
                    "bathrooms": 2.5,
                    "sqft": 1800 + (i * 100),
                    "description": "Beautiful home in high growth area."
                } for i in range(20)
            ]

        # 4. Apply matching strategy
        matcher = BasicFilteringStrategy()
        matches = matcher.find_matches(listings, preferences, limit=limit)

        properties = []
        for match in matches:
            properties.append({
                "property_id": match.get("id"),
                "images": [
                    f"https://images.lyrio.io/p/{match.get('id')}_1.jpg",
                    f"https://images.lyrio.io/p/{match.get('id')}_2.jpg"
                ],
                "price": match.get("price"),
                "address": match.get("address"),
                "bedrooms": match.get("bedrooms"),
                "bathrooms": match.get("bathrooms"),
                "sqft": match.get("sqft"),
                "match_score": int(match.get("match_score", 0.5) * 100),
                "why_matched": f"Matches your {preferences.get('location', 'Austin')} preference with {match.get('match_type')} scoring.",
                "tour_available": True
            })

        result = {
            "properties": properties,
            "stack_id": f"stack_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "lead_preferences": preferences or {
                "max_price": 600000,
                "min_bedrooms": 3,
                "preferred_areas": ["Austin Central"]
            }
        }

        # Cache for 30 minutes
        await cache.set(cache_key, result, ttl=1800)

        return result

    except Exception as e:
        logger.error(f"Swipe stack error: {e}")
        raise HTTPException(status_code=500, detail="Property stack unavailable")

@router.post("/sync")
async def offline_sync(
    sync_request: SyncRequest,
    current_user = Depends(get_current_user)
):
    """
    Offline synchronization endpoint.
    Handles conflict resolution and batch updates for Phase 7.
    """
    try:
        from ghl_real_estate_ai.services.database_service import get_database
        db = await get_database()
        
        sync_results = []
        conflicts = []

        for operation in sync_request.pending_operations:
            try:
                op_type = operation.get('type')
                
                if op_type == 'lead_update':
                    lead_id = operation.get('lead_id')
                    client_timestamp = datetime.fromisoformat(operation.get('client_updated_at').replace('Z', '+00:00'))
                    
                    server_lead = await db.get_lead(lead_id)
                    if not server_lead:
                        sync_results.append({"operation_id": operation.get('id'), "status": "failed", "error": "Not found"})
                        continue
                        
                    server_timestamp = server_lead.get('updated_at')
                    if server_timestamp > client_timestamp:
                        conflicts.append({
                            "operation_id": operation.get('id'),
                            "lead_id": lead_id,
                            "error": "Conflict: Server has newer data",
                            "server_version": server_lead
                        })
                        continue

                    await db.update_lead(lead_id, operation.get('updates'))
                    sync_results.append({"operation_id": operation.get('id'), "status": "success"})

                elif op_type == 'note_create':
                    # Implementation for Note Creation (Phase 7)
                    lead_id = operation.get('lead_id')
                    content = operation.get('content')
                    
                    # Store as communication log or internal note
                    await db.log_communication({
                        "lead_id": lead_id,
                        "channel": "webhook",
                        "direction": "outbound",
                        "content": f"[MOBILE NOTE] {content}",
                        "status": "delivered",
                        "metadata": {"source": "mobile_app", "device_id": sync_request.device_id}
                    })
                    
                    sync_results.append({"operation_id": operation.get('id'), "status": "success"})

                else:
                    sync_results.append({"operation_id": operation.get('id'), "status": "unsupported"})

            except Exception as op_error:
                logger.warning(f"Operation error: {op_error}")
                conflicts.append({"operation_id": operation.get('id'), "error": str(op_error)})

        updates_since_sync = await _get_updates_since(current_user['location_id'], sync_request.last_sync)

        return {
            "sync_id": f"sync_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "sync_timestamp": datetime.utcnow(),
            "processed_operations": sync_results,
            "conflicts": conflicts,
            "server_updates": updates_since_sync
        }

    except Exception as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail="Sync failed")

@router.get("/analytics/summary")
async def get_mobile_analytics(
    period: str = Query("week", pattern="^(Union[day, week]|month)$"),
    current_user = Depends(get_current_user)
):
    """
    Mobile-optimized analytics summary.
    """
    try:
        cache = get_cache_service()
        cache_key = f"mobile_analytics:{current_user['location_id']}:{period}"

        cached_analytics = await cache.get(cache_key)
        if cached_analytics:
            return cached_analytics

        analytics = AnalyticsService()
        days_back = {"day": 1, "week": 7, "month": 30}[period]

        summary = {
            "period": period,
            "leads": {
                "total": await analytics.get_lead_count(current_user['location_id'], days_back),
                "converted": await analytics.get_conversion_count(current_user['location_id'], days_back),
                "response_rate": await analytics.get_response_rate(current_user['location_id'], days_back)
            },
            "performance": {
                "avg_response_time": await analytics.get_avg_response_time(current_user['location_id'], days_back),
                "lead_score_avg": await analytics.get_avg_lead_score(current_user['location_id'], days_back)
            },
            "trends": await _get_mobile_trends(current_user['location_id'], period)
        }

        await cache.set(cache_key, summary, ttl=900)
        return summary

    except Exception as e:
        logger.error(f"Mobile analytics error: {e}")
        raise HTTPException(status_code=500, detail="Analytics unavailable")

# Helper functions
def _is_today(date_str: str) -> bool:
    """Check if date string is today."""
    if not date_str:
        return False
    try:
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date.date() == datetime.utcnow().date()
    except:
        return False

def _is_this_week(date_str: str) -> bool:
    """Check if date string is within this week."""
    if not date_str:
        return False
    try:
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        week_start = datetime.utcnow() - timedelta(days=7)
        return date >= week_start
    except:
        return False

def _is_within_radius(lat1: float, lon1: float, lat2: float, lon2: float, radius_miles: float) -> bool:
    """Check if coordinates are within radius (simplified calculation)."""
    if not all([lat1, lon1, lat2, lon2]):
        return False

    # Simplified distance calculation for demo
    lat_diff = abs(lat1 - lat2)
    lon_diff = abs(lon1 - lon2)
    distance_approx = (lat_diff + lon_diff) * 69  # Rough miles conversion

    return distance_approx <= radius_miles

def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates."""
    if not all([lat1, lon1, lat2, lon2]):
        return float('inf')

    # Simplified for demo
    lat_diff = abs(lat1 - lat2)
    lon_diff = abs(lon1 - lon2)
    return (lat_diff + lon_diff) * 69  # Rough miles conversion

def _get_mobile_priority(lead: Dict[str, Any]) -> int:
    """Calculate mobile-specific priority score."""
    priority = 0
    if lead.get('lead_score', 0) > 80: priority += 10
    if _is_today(lead.get('last_contact')): priority += 5
    status = lead.get('status', '').lower()
    if status in ['hot', 'urgent']: priority += 8
    elif status in ['warm', 'qualified']: priority += 4
    return priority

async def _get_unread_notifications_count(location_id: str) -> int:
    """Get count of unread notifications from PostgreSQL."""
    try:
        from ghl_real_estate_ai.services.database_service import get_database
        db = await get_database()
        async with db.get_connection() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM notifications 
                WHERE location_id = $1 AND is_read = FALSE
            """, location_id)
            return count or 0
    except Exception as e:
        logger.error(f"Error getting notifications count: {e}")
        return 0

async def _get_updates_since(location_id: str, since: datetime) -> List[Dict[str, Any]]:
    """Get all updates since timestamp for sync from PostgreSQL."""
    try:
        from ghl_real_estate_ai.services.database_service import get_database
        db = await get_database()
        updates = []
        
        async with db.get_connection() as conn:
            # 1. Get lead updates
            lead_rows = await conn.fetch("""
                SELECT id as lead_id, updated_at, status, tags, preferences
                FROM leads
                WHERE updated_at > $1
                LIMIT 100
            """, since)
            
            for row in lead_rows:
                updates.append({
                    "type": "lead_update",
                    "data": dict(row),
                    "timestamp": row['updated_at']
                })
                
            # 2. Get new communications
            comm_rows = await conn.fetch("""
                SELECT id as comm_id, lead_id, channel, direction, content, sent_at
                FROM communication_logs
                WHERE sent_at > $1
                LIMIT 100
            """, since)
            
            for row in comm_rows:
                updates.append({
                    "type": "new_communication",
                    "data": dict(row),
                    "timestamp": row['sent_at']
                })
        
        # Sort by timestamp
        updates.sort(key=lambda x: x['timestamp'])
        
        # Convert timestamps for JSON
        for update in updates:
            update['timestamp'] = update['timestamp'].isoformat()
            if 'updated_at' in update['data']:
                update['data']['updated_at'] = update['data']['updated_at'].isoformat()
            if 'sent_at' in update['data']:
                update['data']['sent_at'] = update['data']['sent_at'].isoformat()
                
        return updates
    except Exception as e:
        logger.error(f"Error getting updates since {since}: {e}")
        return []

async def _get_mobile_trends(location_id: str, period: str) -> Dict[str, Any]:
    """Get mobile-optimized trend data from PostgreSQL (Phase 7)."""
    try:
        from ghl_real_estate_ai.services.database_service import get_database
        db = await get_database()
        
        days = {"day": 1, "week": 7, "month": 30}[period]
        cutoff = datetime.utcnow() - timedelta(days=days)
        prev_cutoff = datetime.utcnow() - timedelta(days=days*2)
        
        async with db.get_connection() as conn:
            # 1. Lead Trend
            current_leads = await conn.fetchval("SELECT COUNT(*) FROM leads WHERE created_at > $1", cutoff)
            prev_leads = await conn.fetchval("SELECT COUNT(*) FROM leads WHERE created_at > $1 AND created_at <= $2", prev_cutoff, cutoff)
            
            lead_trend = "increasing" if current_leads > prev_leads else "decreasing" if current_leads < prev_leads else "stable"
            
            # 2. Response Trend
            current_responses = await conn.fetchval("SELECT COUNT(*) FROM communication_logs WHERE direction = 'inbound' AND sent_at > $1", cutoff)
            prev_responses = await conn.fetchval("SELECT COUNT(*) FROM communication_logs WHERE direction = 'inbound' AND sent_at > $1 AND sent_at <= $2", prev_cutoff, cutoff)
            
            response_trend = "improving" if current_responses > prev_responses else "stable"
            
            return {
                "lead_trend": lead_trend,
                "response_trend": response_trend,
                "conversion_trend": "stable",
                "summary": f"{current_leads} new leads in the last {period}"
            }
    except Exception as e:
        logger.error(f"Trend calculation failed: {e}")
        return {"lead_trend": "stable", "response_trend": "stable", "conversion_trend": "stable"}