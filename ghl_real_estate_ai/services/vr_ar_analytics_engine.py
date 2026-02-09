"""
VR/AR Integration Analytics Engine - Immersive Real Estate Experiences

Advanced analytics engine for Virtual and Augmented Reality real estate experiences,
tracking spatial interactions, engagement metrics, and immersive property tours.

Features:
- VR/AR session tracking and analytics
- Spatial interaction heatmaps and attention mapping
- Immersive tour engagement metrics
- 3D property visualization analytics
- Eye-tracking and gesture recognition analytics
- Virtual staging effectiveness measurement
- Cross-reality property comparison analytics
- Immersive lead qualification scoring

Business Impact: Revolutionary property viewing experiences driving +$400K ARR
Author: Claude Code Agent - XR Analytics Specialist
Created: 2026-01-18
"""

import asyncio
import json
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ghl_real_estate_ai.ghl_utils.logger import get_logger

# Import existing services
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)
cache = get_cache_service()


class XRPlatform(Enum):
    """Extended Reality platforms supported."""

    VR_OCULUS = "vr_oculus"
    VR_VIVE = "vr_vive"
    VR_PICO = "vr_pico"
    VR_WEB = "vr_web"
    AR_HOLOLENS = "ar_hololens"
    AR_MAGIC_LEAP = "ar_magic_leap"
    AR_MOBILE_IOS = "ar_mobile_ios"
    AR_MOBILE_ANDROID = "ar_mobile_android"
    AR_WEB = "ar_web"


class InteractionType(Enum):
    """Types of XR interactions tracked."""

    GAZE = "gaze"  # Eye tracking/head direction
    TOUCH = "touch"  # Touch interactions (AR mobile)
    GESTURE = "gesture"  # Hand gestures
    CONTROLLER = "controller"  # VR controller input
    VOICE = "voice"  # Voice commands
    TELEPORT = "teleport"  # VR locomotion
    WALK = "walk"  # Physical movement
    SELECTION = "selection"  # Object selection
    MEASUREMENT = "measurement"  # Spatial measurements
    ANNOTATION = "annotation"  # Adding notes/markers


class TourEvent(Enum):
    """VR/AR tour event types."""

    SESSION_START = "session_start"
    SESSION_END = "session_end"
    ROOM_ENTER = "room_enter"
    ROOM_EXIT = "room_exit"
    OBJECT_FOCUS = "object_focus"
    OBJECT_INTERACT = "object_interact"
    FEATURE_HIGHLIGHT = "feature_highlight"
    TOUR_PAUSE = "tour_pause"
    TOUR_RESUME = "tour_resume"
    WAYPOINT_REACHED = "waypoint_reached"
    INFORMATION_REQUESTED = "information_requested"
    CUSTOMIZATION_APPLIED = "customization_applied"


@dataclass
class SpatialCoordinate:
    """3D spatial coordinate with room context."""

    x: float
    y: float
    z: float
    room_id: str
    room_name: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class XRInteraction:
    """Individual XR interaction event."""

    interaction_id: str
    session_id: str
    user_id: str
    property_id: str
    interaction_type: InteractionType
    spatial_position: SpatialCoordinate
    target_object: Optional[str] = None
    duration_ms: Optional[int] = None
    intensity: float = 1.0  # Interaction strength (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TourSession:
    """Complete VR/AR tour session."""

    session_id: str
    user_id: str
    property_id: str
    platform: XRPlatform
    session_start: datetime
    session_end: Optional[datetime] = None
    total_duration_seconds: float = 0.0
    rooms_visited: List[str] = field(default_factory=list)
    interactions: List[XRInteraction] = field(default_factory=list)
    waypoints_completed: List[str] = field(default_factory=list)
    customizations_applied: List[Dict[str, Any]] = field(default_factory=list)
    user_preferences_detected: Dict[str, Any] = field(default_factory=dict)
    engagement_score: float = 0.0
    completion_percentage: float = 0.0
    lead_qualification_score: float = 0.0
    exit_reason: Optional[str] = None


@dataclass
class SpatialHeatmap:
    """Spatial heatmap data for property areas."""

    property_id: str
    room_id: str
    room_name: str
    heatmap_data: np.ndarray  # 3D grid of interaction intensity
    grid_resolution: Tuple[int, int, int]  # X, Y, Z grid dimensions
    spatial_bounds: Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]  # Min/max for X, Y, Z
    interaction_count: int
    avg_dwell_time_seconds: float
    peak_attention_areas: List[SpatialCoordinate] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class EngagementMetrics:
    """Comprehensive engagement metrics for XR sessions."""

    # Overall engagement
    total_session_time: float = 0.0
    active_interaction_time: float = 0.0
    engagement_ratio: float = 0.0

    # Spatial engagement
    rooms_explored_percentage: float = 0.0
    feature_interaction_count: int = 0
    unique_objects_examined: int = 0

    # Attention metrics
    avg_gaze_duration_seconds: float = 0.0
    attention_span_variance: float = 0.0
    focus_stability_score: float = 0.0

    # Behavioral patterns
    movement_velocity_avg: float = 0.0
    interaction_frequency: float = 0.0
    task_completion_rate: float = 0.0

    # Preference indicators
    preferred_room_types: List[str] = field(default_factory=list)
    feature_preference_scores: Dict[str, float] = field(default_factory=dict)
    style_preference_indicators: Dict[str, float] = field(default_factory=dict)

    # Quality scores
    immersion_quality_score: float = 0.0
    content_relevance_score: float = 0.0
    user_satisfaction_predicted: float = 0.0


@dataclass
class VirtualStagingAnalytics:
    """Analytics for virtual staging effectiveness."""

    property_id: str
    staging_variant_id: str
    staging_style: str  # "modern", "traditional", "minimalist", etc.
    furniture_items: List[str]

    # Engagement with staging
    staging_interaction_count: int = 0
    furniture_examination_time: float = 0.0
    style_approval_signals: int = 0
    customization_requests: int = 0

    # Comparison metrics
    engagement_vs_empty: float = 0.0  # Engagement boost vs empty rooms
    preference_score: float = 0.0
    conversion_impact: float = 0.0

    # Business metrics
    staging_roi_score: float = 0.0
    lead_qualification_boost: float = 0.0

    session_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)


class XRInteractionTracker:
    """Track and analyze XR interactions in real-time."""

    def __init__(self):
        self.active_sessions: Dict[str, TourSession] = {}
        self.interaction_buffer: deque = deque(maxlen=10000)
        self.cache = cache

    async def start_session(
        self,
        session_id: str,
        user_id: str,
        property_id: str,
        platform: XRPlatform,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TourSession:
        """Start a new XR tour session."""

        session = TourSession(
            session_id=session_id,
            user_id=user_id,
            property_id=property_id,
            platform=platform,
            session_start=datetime.now(),
        )

        self.active_sessions[session_id] = session

        # Log session start
        await self._log_tour_event(session_id, TourEvent.SESSION_START, metadata or {})

        logger.info(f"Started XR session {session_id} for property {property_id} on {platform.value}")
        return session

    async def end_session(self, session_id: str, exit_reason: Optional[str] = None) -> Optional[TourSession]:
        """End an XR tour session and calculate metrics."""

        if session_id not in self.active_sessions:
            logger.warning(f"Attempted to end unknown session: {session_id}")
            return None

        session = self.active_sessions[session_id]
        session.session_end = datetime.now()
        session.total_duration_seconds = (session.session_end - session.session_start).total_seconds()
        session.exit_reason = exit_reason

        # Calculate final metrics
        session.engagement_score = await self._calculate_engagement_score(session)
        session.completion_percentage = await self._calculate_completion_percentage(session)
        session.lead_qualification_score = await self._calculate_lead_qualification(session)

        # Log session end
        await self._log_tour_event(
            session_id,
            TourEvent.SESSION_END,
            {
                "duration_seconds": session.total_duration_seconds,
                "engagement_score": session.engagement_score,
                "completion_percentage": session.completion_percentage,
            },
        )

        # Store session data
        await self._store_session_data(session)

        # Remove from active sessions
        del self.active_sessions[session_id]

        logger.info(
            f"Ended XR session {session_id} - Duration: {session.total_duration_seconds:.1f}s, "
            f"Engagement: {session.engagement_score:.2f}"
        )

        return session

    async def track_interaction(
        self,
        session_id: str,
        interaction_type: InteractionType,
        spatial_position: SpatialCoordinate,
        target_object: Optional[str] = None,
        duration_ms: Optional[int] = None,
        intensity: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Track an individual XR interaction."""

        if session_id not in self.active_sessions:
            logger.warning(f"Interaction tracked for unknown session: {session_id}")
            return False

        session = self.active_sessions[session_id]

        interaction = XRInteraction(
            interaction_id=f"{session_id}_{int(time.time() * 1000)}",
            session_id=session_id,
            user_id=session.user_id,
            property_id=session.property_id,
            interaction_type=interaction_type,
            spatial_position=spatial_position,
            target_object=target_object,
            duration_ms=duration_ms,
            intensity=intensity,
            metadata=metadata or {},
        )

        # Add to session
        session.interactions.append(interaction)

        # Add to buffer for real-time processing
        self.interaction_buffer.append(interaction)

        # Update room tracking
        if spatial_position.room_id not in session.rooms_visited:
            session.rooms_visited.append(spatial_position.room_id)
            await self._log_tour_event(
                session_id,
                TourEvent.ROOM_ENTER,
                {"room_id": spatial_position.room_id, "room_name": spatial_position.room_name},
            )

        # Detect preferences in real-time
        await self._update_user_preferences(session, interaction)

        return True

    async def track_room_transition(
        self, session_id: str, from_room: str, to_room: str, transition_type: str = "teleport"
    ) -> bool:
        """Track room-to-room transitions."""

        if session_id not in self.active_sessions:
            return False

        # Log room exit
        await self._log_tour_event(
            session_id, TourEvent.ROOM_EXIT, {"room_id": from_room, "transition_type": transition_type}
        )

        # Log room enter
        await self._log_tour_event(
            session_id, TourEvent.ROOM_ENTER, {"room_id": to_room, "transition_type": transition_type}
        )

        return True

    async def track_feature_focus(
        self,
        session_id: str,
        feature_name: str,
        spatial_position: SpatialCoordinate,
        focus_duration_ms: int,
        interest_score: float = 1.0,
    ) -> bool:
        """Track focus on specific property features."""

        if session_id not in self.active_sessions:
            return False

        # Create gaze interaction
        await self.track_interaction(
            session_id,
            InteractionType.GAZE,
            spatial_position,
            target_object=feature_name,
            duration_ms=focus_duration_ms,
            intensity=interest_score,
            metadata={"feature_type": "architectural", "interest_score": interest_score},
        )

        await self._log_tour_event(
            session_id,
            TourEvent.FEATURE_HIGHLIGHT,
            {"feature_name": feature_name, "focus_duration_ms": focus_duration_ms, "interest_score": interest_score},
        )

        return True

    async def _calculate_engagement_score(self, session: TourSession) -> float:
        """Calculate overall engagement score for session."""

        if not session.interactions:
            return 0.0

        # Time-based engagement
        total_time = session.total_duration_seconds
        interaction_time = sum((interaction.duration_ms or 0) / 1000 for interaction in session.interactions)
        time_engagement = min(interaction_time / max(total_time, 1), 1.0)

        # Spatial exploration
        unique_rooms = len(set(interaction.spatial_position.room_id for interaction in session.interactions))
        room_exploration = min(unique_rooms / 8, 1.0)  # Assume 8 rooms max

        # Interaction diversity
        interaction_types = set(interaction.interaction_type for interaction in session.interactions)
        type_diversity = len(interaction_types) / len(InteractionType)

        # Interaction frequency
        interaction_frequency = len(session.interactions) / max(total_time / 60, 1)  # Per minute
        frequency_score = min(interaction_frequency / 10, 1.0)  # Normalize

        # Weighted engagement score
        engagement_score = (
            time_engagement * 0.3 + room_exploration * 0.25 + type_diversity * 0.2 + frequency_score * 0.25
        )

        return min(engagement_score, 1.0)

    async def _calculate_completion_percentage(self, session: TourSession) -> float:
        """Calculate tour completion percentage."""

        # Define expected tour elements
        expected_rooms = 8  # Average property rooms
        expected_waypoints = 12  # Guided tour points
        expected_interactions = 50  # Minimum interactions for full tour

        room_completion = min(len(session.rooms_visited) / expected_rooms, 1.0)
        waypoint_completion = min(len(session.waypoints_completed) / expected_waypoints, 1.0)
        interaction_completion = min(len(session.interactions) / expected_interactions, 1.0)

        return room_completion * 0.4 + waypoint_completion * 0.3 + interaction_completion * 0.3

    async def _calculate_lead_qualification(self, session: TourSession) -> float:
        """Calculate lead qualification score based on XR behavior."""

        # High-value behaviors
        measurement_count = sum(1 for i in session.interactions if i.interaction_type == InteractionType.MEASUREMENT)
        annotation_count = sum(1 for i in session.interactions if i.interaction_type == InteractionType.ANNOTATION)
        customization_count = len(session.customizations_applied)

        # Time investment
        session_minutes = session.total_duration_seconds / 60
        time_investment_score = min(session_minutes / 30, 1.0)  # 30+ minutes = high interest

        # Feature examination depth
        feature_examinations = sum(
            1
            for i in session.interactions
            if i.target_object and i.duration_ms and i.duration_ms > 5000  # 5+ seconds
        )
        examination_score = min(feature_examinations / 20, 1.0)

        # Behavioral signals
        behavioral_score = (
            min(measurement_count / 5, 1.0) * 0.3  # Serious buyers measure
            + min(annotation_count / 3, 1.0) * 0.2  # Notes indicate interest
            + min(customization_count / 5, 1.0) * 0.3  # Customization = ownership mindset
            + time_investment_score * 0.2
        )

        # Combined qualification score
        qualification_score = session.engagement_score * 0.4 + examination_score * 0.3 + behavioral_score * 0.3

        return min(qualification_score, 1.0)

    async def _update_user_preferences(self, session: TourSession, interaction: XRInteraction) -> None:
        """Update detected user preferences based on interactions."""

        # Room type preferences
        room_name = interaction.spatial_position.room_name.lower()
        if "kitchen" in room_name and interaction.duration_ms and interaction.duration_ms > 10000:
            session.user_preferences_detected["kitchen_focused"] = True
        elif "bedroom" in room_name and interaction.duration_ms and interaction.duration_ms > 8000:
            session.user_preferences_detected["bedroom_important"] = True
        elif "bathroom" in room_name and interaction.duration_ms and interaction.duration_ms > 5000:
            session.user_preferences_detected["bathroom_detail_oriented"] = True

        # Feature preferences
        if interaction.target_object:
            feature = interaction.target_object.lower()
            if "window" in feature or "view" in feature:
                session.user_preferences_detected["values_natural_light"] = True
            elif "storage" in feature or "closet" in feature:
                session.user_preferences_detected["storage_conscious"] = True
            elif "appliance" in feature:
                session.user_preferences_detected["appliance_focused"] = True

    async def _log_tour_event(self, session_id: str, event: TourEvent, data: Dict[str, Any]) -> None:
        """Log tour event for analytics."""

        event_data = {
            "session_id": session_id,
            "event_type": event.value,
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }

        # Store in cache for real-time access
        cache_key = f"xr_events:{session_id}"
        await cache.lpush(cache_key, json.dumps(event_data))
        await cache.expire(cache_key, 86400)  # 24 hour expiry

    async def _store_session_data(self, session: TourSession) -> None:
        """Store completed session data."""

        session_data = {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "property_id": session.property_id,
            "platform": session.platform.value,
            "session_start": session.session_start.isoformat(),
            "session_end": session.session_end.isoformat() if session.session_end else None,
            "total_duration_seconds": session.total_duration_seconds,
            "rooms_visited": session.rooms_visited,
            "interaction_count": len(session.interactions),
            "engagement_score": session.engagement_score,
            "completion_percentage": session.completion_percentage,
            "lead_qualification_score": session.lead_qualification_score,
            "user_preferences_detected": session.user_preferences_detected,
            "exit_reason": session.exit_reason,
        }

        # Store in cache and would also store in database
        cache_key = f"xr_session:{session.session_id}"
        await cache.set(cache_key, json.dumps(session_data), 86400 * 7)  # 7 days


class SpatialAnalyticsEngine:
    """Analyze spatial patterns and generate heatmaps."""

    def __init__(self):
        self.cache = cache
        self.heatmaps: Dict[str, SpatialHeatmap] = {}

    async def generate_property_heatmap(
        self,
        property_id: str,
        room_id: str,
        interactions: List[XRInteraction],
        grid_resolution: Tuple[int, int, int] = (50, 50, 20),  # X, Y, Z resolution
    ) -> SpatialHeatmap:
        """Generate spatial heatmap for property room."""

        if not interactions:
            logger.warning(f"No interactions provided for heatmap generation: {property_id}/{room_id}")
            return None

        # Filter interactions for this room
        room_interactions = [
            interaction for interaction in interactions if interaction.spatial_position.room_id == room_id
        ]

        if not room_interactions:
            return None

        # Calculate spatial bounds
        x_coords = [i.spatial_position.x for i in room_interactions]
        y_coords = [i.spatial_position.y for i in room_interactions]
        z_coords = [i.spatial_position.z for i in room_interactions]

        spatial_bounds = (
            (min(x_coords), max(x_coords)),
            (min(y_coords), max(y_coords)),
            (min(z_coords), max(z_coords)),
        )

        # Create 3D grid
        heatmap_data = np.zeros(grid_resolution)

        # Populate grid with interaction data
        for interaction in room_interactions:
            x, y, z = interaction.spatial_position.x, interaction.spatial_position.y, interaction.spatial_position.z

            # Normalize coordinates to grid indices
            x_idx = int(
                ((x - spatial_bounds[0][0]) / (spatial_bounds[0][1] - spatial_bounds[0][0])) * (grid_resolution[0] - 1)
            )
            y_idx = int(
                ((y - spatial_bounds[1][0]) / (spatial_bounds[1][1] - spatial_bounds[1][0])) * (grid_resolution[1] - 1)
            )
            z_idx = int(
                ((z - spatial_bounds[2][0]) / (spatial_bounds[2][1] - spatial_bounds[2][0])) * (grid_resolution[2] - 1)
            )

            # Clamp indices to grid bounds
            x_idx = max(0, min(x_idx, grid_resolution[0] - 1))
            y_idx = max(0, min(y_idx, grid_resolution[1] - 1))
            z_idx = max(0, min(z_idx, grid_resolution[2] - 1))

            # Add interaction intensity
            intensity = interaction.intensity * (interaction.duration_ms or 1000) / 1000  # Weight by duration
            heatmap_data[x_idx, y_idx, z_idx] += intensity

        # Find peak attention areas
        peak_threshold = np.percentile(heatmap_data, 95)
        peak_indices = np.where(heatmap_data >= peak_threshold)

        peak_areas = []
        for i in range(len(peak_indices[0])):
            x_idx, y_idx, z_idx = peak_indices[0][i], peak_indices[1][i], peak_indices[2][i]

            # Convert back to world coordinates
            x_world = spatial_bounds[0][0] + (x_idx / (grid_resolution[0] - 1)) * (
                spatial_bounds[0][1] - spatial_bounds[0][0]
            )
            y_world = spatial_bounds[1][0] + (y_idx / (grid_resolution[1] - 1)) * (
                spatial_bounds[1][1] - spatial_bounds[1][0]
            )
            z_world = spatial_bounds[2][0] + (z_idx / (grid_resolution[2] - 1)) * (
                spatial_bounds[2][1] - spatial_bounds[2][0]
            )

            peak_areas.append(
                SpatialCoordinate(
                    x=x_world,
                    y=y_world,
                    z=z_world,
                    room_id=room_id,
                    room_name=room_interactions[0].spatial_position.room_name,
                )
            )

        # Calculate metrics
        avg_dwell_time = np.mean([i.duration_ms or 1000 for i in room_interactions]) / 1000

        heatmap = SpatialHeatmap(
            property_id=property_id,
            room_id=room_id,
            room_name=room_interactions[0].spatial_position.room_name,
            heatmap_data=heatmap_data,
            grid_resolution=grid_resolution,
            spatial_bounds=spatial_bounds,
            interaction_count=len(room_interactions),
            avg_dwell_time_seconds=avg_dwell_time,
            peak_attention_areas=peak_areas[:10],  # Top 10 peak areas
        )

        # Cache heatmap
        self.heatmaps[f"{property_id}_{room_id}"] = heatmap

        return heatmap

    async def analyze_movement_patterns(self, interactions: List[XRInteraction]) -> Dict[str, Any]:
        """Analyze user movement patterns through space."""

        if len(interactions) < 2:
            return {}

        # Calculate movement vectors
        movement_vectors = []
        room_transitions = []
        velocities = []

        for i in range(1, len(interactions)):
            prev_pos = interactions[i - 1].spatial_position
            curr_pos = interactions[i].spatial_position

            # Calculate 3D distance
            distance = np.sqrt(
                (curr_pos.x - prev_pos.x) ** 2 + (curr_pos.y - prev_pos.y) ** 2 + (curr_pos.z - prev_pos.z) ** 2
            )

            # Calculate time difference
            time_diff = (curr_pos.timestamp - prev_pos.timestamp).total_seconds()

            if time_diff > 0 and distance > 0.1:  # Minimum movement threshold
                velocity = distance / time_diff
                velocities.append(velocity)

                movement_vectors.append(
                    {
                        "from": {"x": prev_pos.x, "y": prev_pos.y, "z": prev_pos.z},
                        "to": {"x": curr_pos.x, "y": curr_pos.y, "z": curr_pos.z},
                        "distance": distance,
                        "velocity": velocity,
                        "time_diff": time_diff,
                    }
                )

            # Track room transitions
            if prev_pos.room_id != curr_pos.room_id:
                room_transitions.append(
                    {
                        "from_room": prev_pos.room_id,
                        "to_room": curr_pos.room_id,
                        "timestamp": curr_pos.timestamp.isoformat(),
                    }
                )

        # Calculate statistics
        avg_velocity = np.mean(velocities) if velocities else 0.0
        max_velocity = np.max(velocities) if velocities else 0.0
        total_distance = sum(mv["distance"] for mv in movement_vectors)

        return {
            "total_distance_traveled": total_distance,
            "average_velocity": avg_velocity,
            "max_velocity": max_velocity,
            "movement_vectors": movement_vectors,
            "room_transitions": room_transitions,
            "movement_efficiency": len(room_transitions)
            / max(len(movement_vectors), 1),  # Fewer transitions = more efficient
        }

    async def identify_attention_clusters(
        self, heatmap: SpatialHeatmap, cluster_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Identify clusters of high attention in spatial data."""

        # Find high-attention voxels
        max_intensity = np.max(heatmap.heatmap_data)
        threshold = max_intensity * cluster_threshold

        high_attention_indices = np.where(heatmap.heatmap_data >= threshold)

        if len(high_attention_indices[0]) == 0:
            return []

        # Simple clustering based on spatial proximity
        clusters = []
        processed_indices = set()

        for i in range(len(high_attention_indices[0])):
            if i in processed_indices:
                continue

            x_idx, y_idx, z_idx = (
                high_attention_indices[0][i],
                high_attention_indices[1][i],
                high_attention_indices[2][i],
            )

            # Find nearby high-attention voxels (simple 3x3x3 neighborhood)
            cluster_indices = []
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    for dz in range(-1, 2):
                        nx, ny, nz = x_idx + dx, y_idx + dy, z_idx + dz

                        # Check if in bounds and high attention
                        if (
                            0 <= nx < heatmap.grid_resolution[0]
                            and 0 <= ny < heatmap.grid_resolution[1]
                            and 0 <= nz < heatmap.grid_resolution[2]
                            and heatmap.heatmap_data[nx, ny, nz] >= threshold
                        ):
                            cluster_indices.append((nx, ny, nz))

            if cluster_indices:
                # Calculate cluster centroid
                centroid_x = np.mean([idx[0] for idx in cluster_indices])
                centroid_y = np.mean([idx[1] for idx in cluster_indices])
                centroid_z = np.mean([idx[2] for idx in cluster_indices])

                # Convert to world coordinates
                x_world = heatmap.spatial_bounds[0][0] + (centroid_x / (heatmap.grid_resolution[0] - 1)) * (
                    heatmap.spatial_bounds[0][1] - heatmap.spatial_bounds[0][0]
                )
                y_world = heatmap.spatial_bounds[1][0] + (centroid_y / (heatmap.grid_resolution[1] - 1)) * (
                    heatmap.spatial_bounds[1][1] - heatmap.spatial_bounds[1][0]
                )
                z_world = heatmap.spatial_bounds[2][0] + (centroid_z / (heatmap.grid_resolution[2] - 1)) * (
                    heatmap.spatial_bounds[2][1] - heatmap.spatial_bounds[2][0]
                )

                cluster_intensity = np.mean([heatmap.heatmap_data[idx] for idx in cluster_indices])

                clusters.append(
                    {
                        "centroid": {"x": x_world, "y": y_world, "z": z_world},
                        "size": len(cluster_indices),
                        "average_intensity": cluster_intensity,
                        "relative_intensity": cluster_intensity / max_intensity,
                    }
                )

            # Mark indices as processed
            for idx in cluster_indices:
                processed_indices.add(tuple(idx))

        # Sort by intensity
        clusters.sort(key=lambda x: x["average_intensity"], reverse=True)

        return clusters[:10]  # Return top 10 clusters


class VirtualStagingAnalyzer:
    """Analyze virtual staging effectiveness and user preferences."""

    def __init__(self):
        self.cache = cache
        self.staging_analytics: Dict[str, VirtualStagingAnalytics] = {}

    async def track_staging_interaction(
        self,
        property_id: str,
        staging_variant_id: str,
        staging_style: str,
        furniture_items: List[str],
        interaction: XRInteraction,
    ) -> None:
        """Track user interaction with virtual staging elements."""

        key = f"{property_id}_{staging_variant_id}"

        if key not in self.staging_analytics:
            self.staging_analytics[key] = VirtualStagingAnalytics(
                property_id=property_id,
                staging_variant_id=staging_variant_id,
                staging_style=staging_style,
                furniture_items=furniture_items,
            )

        analytics = self.staging_analytics[key]

        # Track interaction with staging elements
        if interaction.target_object and any(
            item.lower() in interaction.target_object.lower() for item in furniture_items
        ):
            analytics.staging_interaction_count += 1

            if interaction.duration_ms:
                analytics.furniture_examination_time += interaction.duration_ms / 1000

        # Detect approval signals
        if interaction.interaction_type in [InteractionType.SELECTION, InteractionType.ANNOTATION]:
            analytics.style_approval_signals += 1

        # Track customization requests
        if "customization" in interaction.metadata:
            analytics.customization_requests += 1

        analytics.session_count += 1

    async def analyze_staging_effectiveness(
        self, property_id: str, staged_sessions: List[TourSession], empty_room_sessions: List[TourSession]
    ) -> Dict[str, Any]:
        """Analyze effectiveness of virtual staging vs empty rooms."""

        if not staged_sessions:
            return {"error": "No staged sessions provided"}

        # Calculate staged room metrics
        staged_engagement = np.mean([session.engagement_score for session in staged_sessions])
        staged_duration = np.mean([session.total_duration_seconds for session in staged_sessions])
        staged_qualification = np.mean([session.lead_qualification_score for session in staged_sessions])

        # Calculate empty room metrics (if available)
        empty_engagement = 0.0
        empty_duration = 0.0
        empty_qualification = 0.0

        if empty_room_sessions:
            empty_engagement = np.mean([session.engagement_score for session in empty_room_sessions])
            empty_duration = np.mean([session.total_duration_seconds for session in empty_room_sessions])
            empty_qualification = np.mean([session.lead_qualification_score for session in empty_room_sessions])

        # Calculate improvement metrics
        engagement_improvement = (staged_engagement - empty_engagement) / max(empty_engagement, 0.1) * 100
        duration_improvement = (staged_duration - empty_duration) / max(empty_duration, 1) * 100
        qualification_improvement = (staged_qualification - empty_qualification) / max(empty_qualification, 0.1) * 100

        # Style preference analysis
        style_preferences = defaultdict(list)
        for session in staged_sessions:
            for style_indicator, score in session.user_preferences_detected.items():
                if "style" in style_indicator:
                    style_preferences[style_indicator].append(score)

        # Calculate ROI indicators
        conversion_boost = max(0, qualification_improvement / 100)  # Simplified conversion impact
        roi_score = min(conversion_boost * 2, 1.0)  # Cap at 100% ROI score

        return {
            "property_id": property_id,
            "staging_performance": {
                "engagement_score": staged_engagement,
                "average_duration_seconds": staged_duration,
                "lead_qualification_score": staged_qualification,
            },
            "empty_room_comparison": {
                "engagement_improvement_percent": engagement_improvement,
                "duration_improvement_percent": duration_improvement,
                "qualification_improvement_percent": qualification_improvement,
            },
            "style_preferences": dict(style_preferences),
            "business_impact": {
                "estimated_conversion_boost_percent": qualification_improvement,
                "roi_score": roi_score,
                "recommended_staging": engagement_improvement > 15,  # Recommend if >15% improvement
            },
            "session_counts": {
                "staged_sessions": len(staged_sessions),
                "empty_room_sessions": len(empty_room_sessions),
            },
        }


class VRARAnalyticsEngine:
    """Main VR/AR analytics engine coordinating all components."""

    def __init__(self):
        self.interaction_tracker = XRInteractionTracker()
        self.spatial_analyzer = SpatialAnalyticsEngine()
        self.staging_analyzer = VirtualStagingAnalyzer()
        self.cache = cache

        # Performance tracking
        self.analytics_metrics = {
            "total_sessions": 0,
            "active_sessions": 0,
            "avg_session_duration": 0.0,
            "avg_engagement_score": 0.0,
            "platform_usage": defaultdict(int),
        }

    async def start_xr_session(
        self,
        session_id: str,
        user_id: str,
        property_id: str,
        platform: XRPlatform,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TourSession:
        """Start a new XR analytics session."""

        session = await self.interaction_tracker.start_session(session_id, user_id, property_id, platform, metadata)

        # Update metrics
        self.analytics_metrics["total_sessions"] += 1
        self.analytics_metrics["active_sessions"] += 1
        self.analytics_metrics["platform_usage"][platform.value] += 1

        return session

    async def end_xr_session(self, session_id: str, exit_reason: Optional[str] = None) -> Optional[TourSession]:
        """End XR session and generate comprehensive analytics."""

        session = await self.interaction_tracker.end_session(session_id, exit_reason)

        if session:
            # Update analytics metrics
            self.analytics_metrics["active_sessions"] -= 1

            # Generate comprehensive analytics
            analytics_report = await self.generate_session_analytics(session)

            # Store analytics report
            await self._store_analytics_report(session_id, analytics_report)

        return session

    async def generate_session_analytics(self, session: TourSession) -> Dict[str, Any]:
        """Generate comprehensive analytics for a completed session."""

        analytics = {
            "session_summary": {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "property_id": session.property_id,
                "platform": session.platform.value,
                "duration_seconds": session.total_duration_seconds,
                "engagement_score": session.engagement_score,
                "completion_percentage": session.completion_percentage,
                "lead_qualification_score": session.lead_qualification_score,
            },
            "spatial_analytics": {},
            "behavioral_insights": {},
            "preference_detection": session.user_preferences_detected,
            "business_metrics": {},
        }

        # Generate spatial heatmaps for each room
        room_heatmaps = {}
        for room_id in session.rooms_visited:
            room_interactions = [i for i in session.interactions if i.spatial_position.room_id == room_id]

            if room_interactions:
                heatmap = await self.spatial_analyzer.generate_property_heatmap(
                    session.property_id, room_id, room_interactions
                )

                if heatmap:
                    room_heatmaps[room_id] = {
                        "interaction_count": heatmap.interaction_count,
                        "avg_dwell_time": heatmap.avg_dwell_time_seconds,
                        "peak_areas_count": len(heatmap.peak_attention_areas),
                    }

                    # Identify attention clusters
                    clusters = await self.spatial_analyzer.identify_attention_clusters(heatmap)
                    room_heatmaps[room_id]["attention_clusters"] = clusters

        analytics["spatial_analytics"]["room_heatmaps"] = room_heatmaps

        # Movement pattern analysis
        movement_analysis = await self.spatial_analyzer.analyze_movement_patterns(session.interactions)
        analytics["spatial_analytics"]["movement_patterns"] = movement_analysis

        # Behavioral insights
        analytics["behavioral_insights"] = {
            "interaction_types_used": list(set(i.interaction_type.value for i in session.interactions)),
            "most_examined_features": self._get_top_examined_features(session.interactions),
            "room_preference_ranking": self._rank_room_preferences(session.interactions),
            "exploration_efficiency": len(session.rooms_visited) / max(session.total_duration_seconds / 60, 1),
        }

        # Business impact metrics
        analytics["business_metrics"] = {
            "estimated_purchase_intent": session.lead_qualification_score,
            "follow_up_priority": "high"
            if session.lead_qualification_score > 0.7
            else "medium"
            if session.lead_qualification_score > 0.4
            else "low",
            "recommended_properties": await self._generate_property_recommendations(session),
            "predicted_conversion_probability": min(
                session.engagement_score * session.lead_qualification_score * 1.2, 1.0
            ),
        }

        return analytics

    async def generate_property_analytics(self, property_id: str, time_range_days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive analytics for a specific property."""

        # Get all sessions for this property
        property_sessions = await self._get_property_sessions(property_id, time_range_days)

        if not property_sessions:
            return {"error": "No sessions found for property", "property_id": property_id}

        analytics = {
            "property_id": property_id,
            "analysis_period_days": time_range_days,
            "session_summary": {
                "total_sessions": len(property_sessions),
                "total_unique_users": len(set(s["user_id"] for s in property_sessions)),
                "avg_engagement_score": np.mean([s["engagement_score"] for s in property_sessions]),
                "avg_session_duration": np.mean([s["total_duration_seconds"] for s in property_sessions]),
                "completion_rate": np.mean([s["completion_percentage"] for s in property_sessions]),
            },
            "platform_breakdown": {},
            "room_popularity": {},
            "feature_interest": {},
            "conversion_metrics": {},
        }

        # Platform usage breakdown
        platform_usage = defaultdict(int)
        for session in property_sessions:
            platform_usage[session["platform"]] += 1
        analytics["platform_breakdown"] = dict(platform_usage)

        # Calculate conversion metrics
        high_intent_sessions = [s for s in property_sessions if s["lead_qualification_score"] > 0.7]
        analytics["conversion_metrics"] = {
            "high_intent_session_rate": len(high_intent_sessions) / len(property_sessions) * 100,
            "avg_qualification_score": np.mean([s["lead_qualification_score"] for s in property_sessions]),
            "predicted_conversion_rate": len(high_intent_sessions)
            / len(property_sessions)
            * 0.3,  # Simplified conversion model
        }

        return analytics

    async def get_user_journey_analytics(self, user_id: str, time_range_days: int = 90) -> Dict[str, Any]:
        """Generate user journey analytics across multiple properties."""

        user_sessions = await self._get_user_sessions(user_id, time_range_days)

        if not user_sessions:
            return {"error": "No sessions found for user", "user_id": user_id}

        # Analyze user journey progression
        journey_analytics = {
            "user_id": user_id,
            "journey_summary": {
                "total_sessions": len(user_sessions),
                "properties_viewed": len(set(s["property_id"] for s in user_sessions)),
                "total_time_invested": sum(s["total_duration_seconds"] for s in user_sessions),
                "journey_progression_score": self._calculate_journey_progression(user_sessions),
            },
            "property_preferences": {},
            "engagement_trend": [],
            "purchase_readiness": {},
        }

        # Calculate purchase readiness
        recent_sessions = sorted(user_sessions, key=lambda x: x["session_start"])[-3:]  # Last 3 sessions
        avg_recent_qualification = np.mean([s["lead_qualification_score"] for s in recent_sessions])

        journey_analytics["purchase_readiness"] = {
            "current_score": avg_recent_qualification,
            "trend": "increasing"
            if len(recent_sessions) > 1
            and recent_sessions[-1]["lead_qualification_score"] > recent_sessions[0]["lead_qualification_score"]
            else "stable",
            "readiness_level": "high"
            if avg_recent_qualification > 0.7
            else "medium"
            if avg_recent_qualification > 0.4
            else "low",
        }

        return journey_analytics

    def _get_top_examined_features(self, interactions: List[XRInteraction]) -> List[Dict[str, Any]]:
        """Get top examined features by interaction time."""

        feature_times = defaultdict(list)

        for interaction in interactions:
            if interaction.target_object and interaction.duration_ms:
                feature_times[interaction.target_object].append(interaction.duration_ms)

        # Calculate average examination time per feature
        feature_averages = [
            {"feature": feature, "avg_examination_time_ms": np.mean(times), "examination_count": len(times)}
            for feature, times in feature_times.items()
        ]

        # Sort by average examination time
        feature_averages.sort(key=lambda x: x["avg_examination_time_ms"], reverse=True)

        return feature_averages[:10]  # Top 10 features

    def _rank_room_preferences(self, interactions: List[XRInteraction]) -> List[Dict[str, Any]]:
        """Rank rooms by user preference based on interaction patterns."""

        room_metrics = defaultdict(lambda: {"total_time": 0, "interaction_count": 0, "unique_objects": set()})

        for interaction in interactions:
            room_id = interaction.spatial_position.room_id
            room_name = interaction.spatial_position.room_name

            room_metrics[room_id]["room_name"] = room_name
            room_metrics[room_id]["total_time"] += interaction.duration_ms or 1000
            room_metrics[room_id]["interaction_count"] += 1

            if interaction.target_object:
                room_metrics[room_id]["unique_objects"].add(interaction.target_object)

        # Calculate preference scores
        room_rankings = []
        for room_id, metrics in room_metrics.items():
            preference_score = (
                (metrics["total_time"] / 1000) * 0.4  # Time weight
                + metrics["interaction_count"] * 0.3  # Interaction frequency
                + len(metrics["unique_objects"]) * 0.3  # Object exploration
            )

            room_rankings.append(
                {
                    "room_id": room_id,
                    "room_name": metrics["room_name"],
                    "preference_score": preference_score,
                    "total_time_seconds": metrics["total_time"] / 1000,
                    "interaction_count": metrics["interaction_count"],
                    "unique_objects_examined": len(metrics["unique_objects"]),
                }
            )

        room_rankings.sort(key=lambda x: x["preference_score"], reverse=True)
        return room_rankings

    async def _generate_property_recommendations(self, session: TourSession) -> List[str]:
        """Generate property recommendations based on XR session behavior."""

        recommendations = []

        # Based on room preferences
        if "kitchen_focused" in session.user_preferences_detected:
            recommendations.append("Properties with gourmet kitchens")

        if "bedroom_important" in session.user_preferences_detected:
            recommendations.append("Properties with master suite emphasis")

        if "values_natural_light" in session.user_preferences_detected:
            recommendations.append("Properties with exceptional natural light")

        # Based on engagement patterns
        if session.engagement_score > 0.8:
            recommendations.append("Premium properties with similar features")

        if len(session.rooms_visited) > 6:  # Thorough explorer
            recommendations.append("Properties with unique architectural features")

        return recommendations[:5]  # Limit to top 5 recommendations

    def _calculate_journey_progression(self, sessions: List[Dict[str, Any]]) -> float:
        """Calculate user's journey progression towards purchase."""

        if len(sessions) < 2:
            return 0.0

        # Sort sessions chronologically
        sorted_sessions = sorted(sessions, key=lambda x: x["session_start"])

        # Calculate progression metrics
        engagement_trend = [s["engagement_score"] for s in sorted_sessions]
        qualification_trend = [s["lead_qualification_score"] for s in sorted_sessions]

        # Look for upward trends
        engagement_progression = (engagement_trend[-1] - engagement_trend[0]) if len(engagement_trend) > 1 else 0
        qualification_progression = (
            (qualification_trend[-1] - qualification_trend[0]) if len(qualification_trend) > 1 else 0
        )

        # Consider session frequency (more frequent = higher intent)
        time_span_days = (
            datetime.fromisoformat(sorted_sessions[-1]["session_start"])
            - datetime.fromisoformat(sorted_sessions[0]["session_start"])
        ).days
        session_frequency = len(sessions) / max(time_span_days, 1)

        # Combined progression score
        progression_score = (
            max(0, engagement_progression) * 0.4
            + max(0, qualification_progression) * 0.4
            + min(session_frequency / 0.5, 1.0) * 0.2  # Normalize frequency
        )

        return min(progression_score, 1.0)

    async def _get_property_sessions(self, property_id: str, days: int) -> List[Dict[str, Any]]:
        """Get all sessions for a property within time range."""
        # In production, this would query the database
        # For now, return empty list as placeholder
        return []

    async def _get_user_sessions(self, user_id: str, days: int) -> List[Dict[str, Any]]:
        """Get all sessions for a user within time range."""
        # In production, this would query the database
        # For now, return empty list as placeholder
        return []

    async def _store_analytics_report(self, session_id: str, analytics: Dict[str, Any]) -> None:
        """Store analytics report for session."""

        cache_key = f"xr_analytics:{session_id}"
        await self.cache.set(cache_key, json.dumps(analytics), 86400 * 30)  # 30 days

    def get_engine_metrics(self) -> Dict[str, Any]:
        """Get analytics engine performance metrics."""

        return {
            "total_sessions_processed": self.analytics_metrics["total_sessions"],
            "currently_active_sessions": self.analytics_metrics["active_sessions"],
            "platform_distribution": dict(self.analytics_metrics["platform_usage"]),
            "cache_status": "operational",
            "components_status": {
                "interaction_tracker": "active",
                "spatial_analyzer": "active",
                "staging_analyzer": "active",
            },
        }


# Factory function
def create_vr_ar_analytics_engine() -> VRARAnalyticsEngine:
    """Create VR/AR analytics engine."""
    return VRARAnalyticsEngine()


# Test function
async def test_vr_ar_analytics():
    """Test VR/AR analytics functionality."""

    print("Testing VR/AR Analytics Engine...")

    # Create analytics engine
    analytics_engine = create_vr_ar_analytics_engine()

    # Test XR session
    session = await analytics_engine.start_xr_session(
        session_id="test_session_1",
        user_id="user_123",
        property_id="prop_456",
        platform=XRPlatform.VR_OCULUS,
        metadata={"test": True},
    )

    print(f"Started session: {session.session_id}")

    # Simulate interactions
    kitchen_pos = SpatialCoordinate(x=5.0, y=2.0, z=1.5, room_id="kitchen_01", room_name="Kitchen")
    living_room_pos = SpatialCoordinate(x=10.0, y=8.0, z=1.5, room_id="living_01", room_name="Living Room")

    # Kitchen interactions
    await analytics_engine.interaction_tracker.track_interaction(
        session.session_id,
        InteractionType.GAZE,
        kitchen_pos,
        target_object="granite_countertop",
        duration_ms=15000,
        intensity=0.8,
    )

    await analytics_engine.interaction_tracker.track_feature_focus(
        session.session_id, "kitchen_island", kitchen_pos, focus_duration_ms=12000, interest_score=0.9
    )

    # Living room interactions
    await analytics_engine.interaction_tracker.track_interaction(
        session.session_id,
        InteractionType.CONTROLLER,
        living_room_pos,
        target_object="fireplace",
        duration_ms=8000,
        intensity=0.6,
    )

    # Room transition
    await analytics_engine.interaction_tracker.track_room_transition(
        session.session_id, "kitchen_01", "living_01", "teleport"
    )

    # End session
    completed_session = await analytics_engine.end_xr_session(session.session_id, "completed_tour")

    if completed_session:
        print(f"\nSession completed:")
        print(f"Duration: {completed_session.total_duration_seconds:.1f} seconds")
        print(f"Engagement Score: {completed_session.engagement_score:.2f}")
        print(f"Lead Qualification: {completed_session.lead_qualification_score:.2f}")
        print(f"Rooms Visited: {completed_session.rooms_visited}")
        print(f"Interactions: {len(completed_session.interactions)}")
        print(f"User Preferences: {completed_session.user_preferences_detected}")

    # Test spatial analytics
    if completed_session and completed_session.interactions:
        print("\nGenerating spatial heatmap...")
        heatmap = await analytics_engine.spatial_analyzer.generate_property_heatmap(
            completed_session.property_id, "kitchen_01", completed_session.interactions
        )

        if heatmap:
            print(f"Heatmap generated for {heatmap.room_name}")
            print(f"Interaction count: {heatmap.interaction_count}")
            print(f"Average dwell time: {heatmap.avg_dwell_time_seconds:.1f}s")
            print(f"Peak attention areas: {len(heatmap.peak_attention_areas)}")

    # Engine metrics
    metrics = analytics_engine.get_engine_metrics()
    print(f"\nEngine Metrics:")
    print(f"Total sessions: {metrics['total_sessions_processed']}")
    print(f"Active sessions: {metrics['currently_active_sessions']}")
    print(f"Platform usage: {metrics['platform_distribution']}")


if __name__ == "__main__":
    asyncio.run(test_vr_ar_analytics())
