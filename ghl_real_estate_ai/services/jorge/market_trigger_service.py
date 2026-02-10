"""Market trigger re-engagement service.

Monitors market conditions and generates re-engagement triggers
for contacts that have gone cold. Triggers include:
- Price drop alerts for watched areas
- Interest rate change impact notifications
- Neighborhood sale notifications
- Seasonal timing opportunities
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TriggerType(str, Enum):
    PRICE_DROP = "price_drop"
    RATE_CHANGE = "rate_change"
    NEIGHBORHOOD_SALE = "neighborhood_sale"
    SEASONAL_TIMING = "seasonal_timing"
    NEW_LISTING = "new_listing"
    ABANDONMENT_RECOVERY = "abandonment_recovery"


class TriggerPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class MarketTrigger:
    """A market event that should trigger re-engagement."""

    trigger_type: TriggerType
    priority: TriggerPriority
    contact_id: str
    title: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    expires_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger_type": self.trigger_type.value,
            "priority": self.priority.value,
            "contact_id": self.contact_id,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }


@dataclass
class ContactWatchlist:
    """Market conditions a contact is watching."""

    contact_id: str
    watched_zips: List[str] = field(default_factory=list)
    max_price: Optional[float] = None
    min_beds: Optional[int] = None
    property_types: List[str] = field(default_factory=list)
    preferred_areas: List[str] = field(default_factory=list)
    last_active: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# Message templates
TRIGGER_TEMPLATES = {
    TriggerType.PRICE_DROP: (
        "Great news! A property you might like in {area} just dropped "
        "from ${original_price:,.0f} to ${new_price:,.0f} — that's a "
        "{drop_percent:.0f}% reduction. Want me to send you the details?"
    ),
    TriggerType.RATE_CHANGE: (
        "Heads up: mortgage rates just moved to {new_rate}%. "
        "Based on your ${budget:,.0f} budget, this could change your "
        "monthly payment by about ${payment_change:,.0f}/mo. "
        "Want to talk about how this affects your search?"
    ),
    TriggerType.NEIGHBORHOOD_SALE: (
        "A home just sold in {neighborhood} for ${sold_price:,.0f} "
        "({price_per_sqft:.0f}/sqft). This is {comparison} the area average. "
        "Would you like a market update for this area?"
    ),
    TriggerType.SEASONAL_TIMING: (
        "Spring is historically the best time to {action} in Rancho Cucamonga. "
        "Last year, {season_stat}. Would you like to discuss timing strategy?"
    ),
    TriggerType.NEW_LISTING: (
        "Just listed: {property_summary} in {area} at ${price:,.0f}. "
        "This matches your criteria. Would you like to know more?"
    ),
    TriggerType.ABANDONMENT_RECOVERY: (
        "{message}"  # Custom message from recovery orchestrator
    ),
}


class MarketTriggerService:
    """Evaluates market conditions against contact watchlists."""

    def __init__(self):
        self._watchlists: Dict[str, ContactWatchlist] = {}
        self._trigger_history: Dict[str, List[str]] = {}  # contact → trigger types sent

    def register_watchlist(self, watchlist: ContactWatchlist) -> None:
        """Register or update a contact's watchlist."""
        self._watchlists[watchlist.contact_id] = watchlist
        logger.info("Registered watchlist for contact %s", watchlist.contact_id)

    def remove_watchlist(self, contact_id: str) -> None:
        """Remove a contact's watchlist."""
        self._watchlists.pop(contact_id, None)

    def get_watchlist(self, contact_id: str) -> Optional[ContactWatchlist]:
        """Get a contact's watchlist."""
        return self._watchlists.get(contact_id)

    def evaluate_price_drop(
        self,
        area: str,
        original_price: float,
        new_price: float,
        property_data: Optional[Dict[str, Any]] = None,
    ) -> List[MarketTrigger]:
        """Check if a price drop triggers any watchlist alerts."""
        triggers = []
        drop_percent = ((original_price - new_price) / original_price) * 100

        if drop_percent < 3:  # Ignore trivial reductions
            return triggers

        for contact_id, watchlist in self._watchlists.items():
            if watchlist.max_price and new_price > watchlist.max_price:
                continue
            if watchlist.preferred_areas and area not in watchlist.preferred_areas:
                continue

            priority = (
                TriggerPriority.HIGH if drop_percent >= 10 else TriggerPriority.MEDIUM
            )

            try:
                message = TRIGGER_TEMPLATES[TriggerType.PRICE_DROP].format(
                    area=area,
                    original_price=original_price,
                    new_price=new_price,
                    drop_percent=drop_percent,
                )
            except (KeyError, ValueError):
                message = f"Price drop in {area}: ${new_price:,.0f}"

            triggers.append(
                MarketTrigger(
                    trigger_type=TriggerType.PRICE_DROP,
                    priority=priority,
                    contact_id=contact_id,
                    title=f"Price drop in {area}",
                    message=message,
                    data={
                        "area": area,
                        "original_price": original_price,
                        "new_price": new_price,
                        "drop_percent": round(drop_percent, 1),
                        **(property_data or {}),
                    },
                )
            )
        return triggers

    def evaluate_rate_change(
        self,
        new_rate: float,
        previous_rate: float,
    ) -> List[MarketTrigger]:
        """Generate triggers for interest rate changes."""
        triggers = []
        rate_delta = new_rate - previous_rate

        if abs(rate_delta) < 0.1:  # Ignore tiny movements
            return triggers

        for contact_id, watchlist in self._watchlists.items():
            budget = watchlist.max_price or 500000
            # Rough monthly payment impact: ~$60/mo per 0.25% on $500K
            payment_change = (rate_delta / 0.25) * 60 * (budget / 500000)

            priority = (
                TriggerPriority.HIGH
                if abs(rate_delta) >= 0.5
                else TriggerPriority.MEDIUM
            )

            try:
                message = TRIGGER_TEMPLATES[TriggerType.RATE_CHANGE].format(
                    new_rate=new_rate,
                    budget=budget,
                    payment_change=abs(payment_change),
                )
            except (KeyError, ValueError):
                message = f"Rate changed to {new_rate}%"

            triggers.append(
                MarketTrigger(
                    trigger_type=TriggerType.RATE_CHANGE,
                    priority=priority,
                    contact_id=contact_id,
                    title=f"Rate {'increase' if rate_delta > 0 else 'decrease'} to {new_rate}%",
                    message=message,
                    data={
                        "new_rate": new_rate,
                        "previous_rate": previous_rate,
                        "rate_delta": round(rate_delta, 3),
                        "estimated_payment_change": round(payment_change, 2),
                    },
                )
            )
        return triggers

    def evaluate_neighborhood_sale(
        self,
        neighborhood: str,
        sold_price: float,
        price_per_sqft: float,
        area_avg_per_sqft: float,
    ) -> List[MarketTrigger]:
        """Generate triggers for neighborhood sales."""
        triggers = []

        comparison = (
            "above" if price_per_sqft > area_avg_per_sqft else "below"
        )

        for contact_id, watchlist in self._watchlists.items():
            if (
                watchlist.preferred_areas
                and neighborhood not in watchlist.preferred_areas
            ):
                continue

            try:
                message = TRIGGER_TEMPLATES[TriggerType.NEIGHBORHOOD_SALE].format(
                    neighborhood=neighborhood,
                    sold_price=sold_price,
                    price_per_sqft=price_per_sqft,
                    comparison=comparison,
                )
            except (KeyError, ValueError):
                message = f"Sale in {neighborhood}: ${sold_price:,.0f}"

            triggers.append(
                MarketTrigger(
                    trigger_type=TriggerType.NEIGHBORHOOD_SALE,
                    priority=TriggerPriority.MEDIUM,
                    contact_id=contact_id,
                    title=f"New sale in {neighborhood}",
                    message=message,
                    data={
                        "neighborhood": neighborhood,
                        "sold_price": sold_price,
                        "price_per_sqft": price_per_sqft,
                        "area_avg_per_sqft": area_avg_per_sqft,
                    },
                )
            )
        return triggers

    def get_active_watchlists(self) -> List[ContactWatchlist]:
        """Get all active watchlists."""
        return list(self._watchlists.values())

    def get_trigger_stats(self) -> Dict[str, int]:
        """Get trigger statistics."""
        return {
            "active_watchlists": len(self._watchlists),
            "contacts_with_history": len(self._trigger_history),
        }

    def create_abandonment_trigger(
        self,
        contact_id: str,
        message: str,
        stage: str,
        priority: TriggerPriority = TriggerPriority.MEDIUM,
    ) -> MarketTrigger:
        """Create an abandonment recovery trigger.

        Args:
            contact_id: GHL contact ID
            message: Personalized recovery message
            stage: Abandonment stage (24h, 3d, 7d, 14d, 30d)
            priority: Trigger priority (default: MEDIUM)

        Returns:
            MarketTrigger for abandonment recovery
        """
        return MarketTrigger(
            trigger_type=TriggerType.ABANDONMENT_RECOVERY,
            priority=priority,
            contact_id=contact_id,
            title=f"Recovery attempt - {stage} stage",
            message=message,
            data={"stage": stage, "type": "abandonment_recovery"},
        )


# Singleton
_service: Optional[MarketTriggerService] = None


def get_market_trigger_service() -> MarketTriggerService:
    global _service
    if _service is None:
        _service = MarketTriggerService()
    return _service
