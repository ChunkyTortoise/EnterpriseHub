"""
HeyGen Personalized Video Service

Generates personalized video avatars for lead engagement via the HeyGen API.
Supports dynamic script generation based on lead psychographics, delivery
tracking, cost management, and template-based video creation.

Usage::

    service = get_heygen_service()
    video = await service.create_personalized_video(
        lead_id="l_123",
        lead_name="Sarah",
        lead_profile={"temperature": "warm", "interests": ["family home"]},
        template="buyer_welcome",
    )
    print(video.video_url, video.cost)
"""

import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class VideoTemplate(Enum):
    """Pre-built video script templates by use-case."""

    BUYER_WELCOME = "buyer_welcome"
    SELLER_CMA = "seller_cma"
    LISTING_TOUR = "listing_tour"
    MARKET_UPDATE = "market_update"
    FOLLOW_UP_WARM = "follow_up_warm"
    FOLLOW_UP_COLD = "follow_up_cold"
    OPEN_HOUSE_INVITE = "open_house_invite"
    CLOSING_CONGRATS = "closing_congrats"


class VideoStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DELIVERED = "delivered"


class AvatarStyle(Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    LUXURY = "luxury"


@dataclass
class VideoScript:
    """Generated script for a personalized video."""

    template: VideoTemplate
    personalized_text: str
    duration_estimate_sec: int
    variables: Dict[str, str] = field(default_factory=dict)
    tone: str = "professional"


@dataclass
class VideoRequest:
    """Outbound video generation request."""

    request_id: str
    lead_id: str
    template: VideoTemplate
    script: VideoScript
    avatar_id: str
    status: VideoStatus = VideoStatus.PENDING
    created_at: float = field(default_factory=time.time)


@dataclass
class VideoResult:
    """Completed video generation result."""

    request_id: str
    lead_id: str
    video_url: str
    thumbnail_url: str
    duration_sec: int
    status: VideoStatus
    cost: float
    created_at: float
    delivered_at: Optional[float] = None
    view_count: int = 0
    engagement_score: float = 0.0


@dataclass
class CostTracker:
    """Tracks video generation costs."""

    total_videos: int = 0
    total_cost: float = 0.0
    daily_budget: float = 50.0
    daily_spent: float = 0.0
    daily_count: int = 0
    cost_per_video_avg: float = 0.0
    budget_day_start: float = field(default_factory=time.time)


# ---------------------------------------------------------------------------
# Script templates
# ---------------------------------------------------------------------------

SCRIPT_TEMPLATES: Dict[VideoTemplate, str] = {
    VideoTemplate.BUYER_WELCOME: (
        "Hi {lead_name}! I'm Jorge with Rancho Cucamonga Real Estate. "
        "I saw you're interested in finding a home in {area}. "
        "I've helped dozens of families find their perfect home here, "
        "and I'd love to help you too. {personalized_hook} "
        "Let me know when you're free for a quick chat!"
    ),
    VideoTemplate.SELLER_CMA: (
        "Hi {lead_name}, Jorge here. I put together a quick market analysis "
        "for your property on {address}. Homes in your area are "
        "{market_trend} right now, with an average price of {avg_price}. "
        "{valuation_insight} I'd love to walk you through the full report. "
        "When works best for a quick call?"
    ),
    VideoTemplate.LISTING_TOUR: (
        "Hey {lead_name}! I wanted to give you a personal preview of "
        "this amazing {bedrooms}-bedroom home at {address}. "
        "It features {top_features} and is priced at {price}. "
        "{urgency_note} Want me to schedule a showing?"
    ),
    VideoTemplate.MARKET_UPDATE: (
        "Hi {lead_name}, quick market update for {area}! "
        "{market_summary} "
        "This means {implication_for_lead}. "
        "Let me know if you want to discuss strategy."
    ),
    VideoTemplate.FOLLOW_UP_WARM: (
        "Hey {lead_name}, just checking in! "
        "I found {new_listings_count} new listings that match what you're looking for. "
        "{highlight_property} "
        "Would you like me to send over the details?"
    ),
    VideoTemplate.FOLLOW_UP_COLD: (
        "Hi {lead_name}, it's Jorge. I know it's been a while since we connected. "
        "The market in {area} has {market_change} since we last spoke. "
        "{re_engagement_hook} "
        "No pressure at all, just wanted to keep you in the loop!"
    ),
    VideoTemplate.OPEN_HOUSE_INVITE: (
        "Hi {lead_name}! I'm hosting an open house this {event_day} "
        "at {address}. It's a {property_summary} that I think you'd love. "
        "{personalized_reason} Hope to see you there!"
    ),
    VideoTemplate.CLOSING_CONGRATS: (
        "Congratulations {lead_name}! Your new home at {address} is officially yours. "
        "It's been a pleasure working with you through this journey. "
        "{personal_note} Welcome home!"
    ),
}

# Psychographic-driven hooks
PSYCHOGRAPHIC_HOOKS: Dict[str, List[str]] = {
    "family": [
        "With {bedrooms} bedrooms and top-rated schools nearby, this area is perfect for growing families.",
        "The neighborhood has great parks and family activities your kids would love.",
    ],
    "investment": [
        "This area has seen {appreciation_rate} appreciation over the past year, making it a solid investment.",
        "Rental demand in {area} is strong, with average rents around {avg_rent}.",
    ],
    "first_time": [
        "As a first-time buyer, you'll love the resources I have to make this process smooth and stress-free.",
        "There are some great programs available that could help with your down payment.",
    ],
    "luxury": [
        "This exclusive property offers the premium lifestyle and amenities you're looking for.",
        "The gated community and custom finishes set this apart from anything else on the market.",
    ],
    "downsizer": [
        "This low-maintenance home gives you all the space you need without the upkeep.",
        "The single-story layout and walkable location make this ideal for your next chapter.",
    ],
}


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class HeyGenVideoService:
    """
    Personalized video generation via the HeyGen API.

    Manages script generation, avatar selection, video creation,
    delivery tracking, and cost management ($0.15/video target).
    """

    BASE_URL = "https://api.heygen.com/v2"
    COST_PER_VIDEO = 0.15  # target cost

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HEYGEN_API_KEY")
        self.default_avatar_id = os.getenv("HEYGEN_AVATAR_ID", "default_jorge")
        self._cost_tracker = CostTracker()
        self._requests: Dict[str, VideoRequest] = {}
        self._results: Dict[str, VideoResult] = {}
        self._request_counter = 0

        if not self.api_key:
            logger.warning("HEYGEN_API_KEY not set. Video generation will use mock mode.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_personalized_video(
        self,
        lead_id: str,
        lead_name: str,
        lead_profile: Dict[str, Any],
        template: str = "buyer_welcome",
        variables: Optional[Dict[str, str]] = None,
        avatar_style: str = "professional",
    ) -> VideoResult:
        """
        Generate a personalized video for a lead.

        Returns a ``VideoResult`` with the video URL, cost, and status.
        """
        template_enum = self._resolve_template(template)
        script = self._generate_script(template_enum, lead_name, lead_profile, variables or {})

        self._request_counter += 1
        request_id = f"vid_{lead_id}_{int(time.time())}_{self._request_counter}"
        avatar_id = self._select_avatar(avatar_style)

        request = VideoRequest(
            request_id=request_id,
            lead_id=lead_id,
            template=template_enum,
            script=script,
            avatar_id=avatar_id,
        )
        self._requests[request_id] = request

        if not self._check_budget():
            logger.warning("Daily video budget exceeded for lead %s", lead_id)
            return VideoResult(
                request_id=request_id,
                lead_id=lead_id,
                video_url="",
                thumbnail_url="",
                duration_sec=0,
                status=VideoStatus.FAILED,
                cost=0.0,
                created_at=time.time(),
            )

        if self.api_key:
            result = await self._call_heygen_api(request)
        else:
            result = self._mock_video_result(request)

        self._track_cost(result)
        self._results[request_id] = result
        return result

    async def get_video_status(self, request_id: str) -> Optional[VideoResult]:
        """Check the status of a previously requested video."""
        return self._results.get(request_id)

    async def mark_delivered(self, request_id: str) -> bool:
        """Mark a video as delivered to the lead."""
        result = self._results.get(request_id)
        if not result:
            return False
        result.status = VideoStatus.DELIVERED
        result.delivered_at = time.time()
        return True

    async def record_view(self, request_id: str) -> bool:
        """Record a video view event."""
        result = self._results.get(request_id)
        if not result:
            return False
        result.view_count += 1
        result.engagement_score = min(result.view_count * 0.2, 1.0)
        return True

    def get_cost_summary(self) -> Dict[str, Any]:
        """Return current cost tracking summary."""
        ct = self._cost_tracker
        return {
            "total_videos": ct.total_videos,
            "total_cost": round(ct.total_cost, 2),
            "daily_spent": round(ct.daily_spent, 2),
            "daily_remaining": round(ct.daily_budget - ct.daily_spent, 2),
            "cost_per_video_avg": round(ct.cost_per_video_avg, 4),
            "daily_count": ct.daily_count,
        }

    def get_lead_videos(self, lead_id: str) -> List[VideoResult]:
        """Get all videos generated for a specific lead."""
        return [r for r in self._results.values() if r.lead_id == lead_id]

    # ------------------------------------------------------------------
    # Script generation
    # ------------------------------------------------------------------

    def _generate_script(
        self,
        template: VideoTemplate,
        lead_name: str,
        profile: Dict[str, Any],
        variables: Dict[str, str],
    ) -> VideoScript:
        """Generate a personalized script from template + profile."""
        base_text = SCRIPT_TEMPLATES.get(template, SCRIPT_TEMPLATES[VideoTemplate.BUYER_WELCOME])

        # Build variable map
        merged = {"lead_name": lead_name}
        merged.update(self._profile_to_variables(profile))
        merged.update(variables)

        # Inject psychographic hook
        persona = profile.get("persona", profile.get("psychographic", ""))
        hook = self._select_psychographic_hook(persona, merged)
        merged["personalized_hook"] = hook
        merged["re_engagement_hook"] = hook
        merged["personalized_reason"] = hook
        merged["personal_note"] = "Looking forward to being your neighbor resource!"

        # Safe format: leave unreplaced placeholders as-is
        personalized = self._safe_format(base_text, merged)

        # Estimate duration (~150 words/min for natural speech)
        word_count = len(personalized.split())
        duration = max(int(word_count / 2.5), 15)

        return VideoScript(
            template=template,
            personalized_text=personalized,
            duration_estimate_sec=duration,
            variables=merged,
            tone=profile.get("tone", "professional"),
        )

    @staticmethod
    def _profile_to_variables(profile: Dict[str, Any]) -> Dict[str, str]:
        """Extract template variables from lead profile."""
        return {
            "area": str(profile.get("area", "Rancho Cucamonga")),
            "bedrooms": str(profile.get("bedrooms", "3")),
            "price": str(profile.get("budget", "$600,000")),
            "address": str(profile.get("address", "")),
            "market_trend": str(profile.get("market_trend", "appreciating steadily")),
            "avg_price": str(profile.get("avg_price", "$650,000")),
            "top_features": str(profile.get("features", "modern kitchen and spacious backyard")),
            "market_summary": str(profile.get("market_summary", "Inventory is tightening with strong buyer demand")),
            "implication_for_lead": str(profile.get("implication", "now is a strategic time to make a move")),
            "new_listings_count": str(profile.get("new_listings", "3")),
            "highlight_property": str(profile.get("highlight", "One in particular stands out")),
            "market_change": str(profile.get("market_change", "shifted significantly")),
            "valuation_insight": str(profile.get("valuation_insight", "Your home could be worth more than you think.")),
            "urgency_note": str(profile.get("urgency", "This one won't last long.")),
            "event_day": str(profile.get("event_day", "Saturday")),
            "property_summary": str(profile.get("property_summary", "beautiful 3BR/2BA")),
            "appreciation_rate": str(profile.get("appreciation_rate", "8%")),
            "avg_rent": str(profile.get("avg_rent", "$2,800/mo")),
        }

    def _select_psychographic_hook(self, persona: str, variables: Dict[str, str]) -> str:
        """Choose a psychographic-driven hook based on lead persona."""
        persona_lower = persona.lower() if persona else ""
        for key, hooks in PSYCHOGRAPHIC_HOOKS.items():
            if key in persona_lower:
                raw = hooks[0]
                return self._safe_format(raw, variables)
        return "I think you're going to love what the Rancho Cucamonga market has to offer right now."

    @staticmethod
    def _safe_format(template: str, variables: Dict[str, str]) -> str:
        """Format template, leaving unknown placeholders intact."""
        result = template
        for key, val in variables.items():
            result = result.replace("{" + key + "}", val)
        return result

    # ------------------------------------------------------------------
    # Template / avatar helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_template(name: str) -> VideoTemplate:
        try:
            return VideoTemplate(name)
        except ValueError:
            return VideoTemplate.BUYER_WELCOME

    def _select_avatar(self, style: str) -> str:
        """Select avatar based on style preference."""
        style_map = {
            "professional": self.default_avatar_id,
            "casual": f"{self.default_avatar_id}_casual",
            "luxury": f"{self.default_avatar_id}_luxury",
        }
        return style_map.get(style, self.default_avatar_id)

    # ------------------------------------------------------------------
    # Budget / cost
    # ------------------------------------------------------------------

    def _check_budget(self) -> bool:
        """Check if daily budget allows another video."""
        ct = self._cost_tracker
        now = time.time()
        # Reset daily counter every 24h
        if now - ct.budget_day_start > 86400:
            ct.daily_spent = 0.0
            ct.daily_count = 0
            ct.budget_day_start = now
        return ct.daily_spent + self.COST_PER_VIDEO <= ct.daily_budget

    def _track_cost(self, result: VideoResult) -> None:
        ct = self._cost_tracker
        if result.status in (VideoStatus.COMPLETED, VideoStatus.DELIVERED):
            ct.total_videos += 1
            ct.total_cost += result.cost
            ct.daily_spent += result.cost
            ct.daily_count += 1
            ct.cost_per_video_avg = ct.total_cost / max(ct.total_videos, 1)

    # ------------------------------------------------------------------
    # API call / mock
    # ------------------------------------------------------------------

    async def _call_heygen_api(self, request: VideoRequest) -> VideoResult:
        """Call HeyGen API to generate video."""
        try:
            import aiohttp

            payload = {
                "video_inputs": [
                    {
                        "character": {
                            "type": "avatar",
                            "avatar_id": request.avatar_id,
                        },
                        "voice": {
                            "type": "text",
                            "input_text": request.script.personalized_text,
                        },
                    }
                ],
                "dimension": {"width": 1280, "height": 720},
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/video/generate",
                    json=payload,
                    headers={
                        "X-Api-Key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        video_id = data.get("data", {}).get("video_id", request.request_id)
                        return VideoResult(
                            request_id=request.request_id,
                            lead_id=request.lead_id,
                            video_url=f"https://api.heygen.com/v1/video/{video_id}",
                            thumbnail_url=f"https://api.heygen.com/v1/video/{video_id}/thumbnail",
                            duration_sec=request.script.duration_estimate_sec,
                            status=VideoStatus.PROCESSING,
                            cost=self.COST_PER_VIDEO,
                            created_at=time.time(),
                        )
                    else:
                        logger.error("HeyGen API error: %d", resp.status)
                        return self._mock_video_result(request)

        except ImportError:
            logger.warning("aiohttp not available, using mock mode")
            return self._mock_video_result(request)
        except Exception as exc:
            logger.error("HeyGen API call failed: %s", exc)
            return self._mock_video_result(request)

    def _mock_video_result(self, request: VideoRequest) -> VideoResult:
        """Mock result for testing/demo."""
        return VideoResult(
            request_id=request.request_id,
            lead_id=request.lead_id,
            video_url=f"https://mock.heygen.com/video/{request.request_id}",
            thumbnail_url=f"https://mock.heygen.com/thumb/{request.request_id}",
            duration_sec=request.script.duration_estimate_sec,
            status=VideoStatus.COMPLETED,
            cost=self.COST_PER_VIDEO,
            created_at=time.time(),
        )


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_service: Optional[HeyGenVideoService] = None


def get_heygen_service() -> HeyGenVideoService:
    global _service
    if _service is None:
        _service = HeyGenVideoService()
    return _service
