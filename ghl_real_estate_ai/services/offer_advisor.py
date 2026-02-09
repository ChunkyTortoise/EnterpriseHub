"""Market-aware offer strategy advisor for buyers."""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class OfferStrategy:
    """Recommended offer strategy for a property."""
    suggested_price: float
    price_rationale: str
    contingencies: List[str] = field(default_factory=list)
    earnest_money_pct: float = 2.0
    escalation_clause: Optional[Dict] = None
    closing_timeline_days: int = 30
    competitive_assessment: str = "moderate"  # "strong", "moderate", "weak"


class OfferAdvisor:
    """Generates market-aware offer recommendations."""

    # Default contingencies
    STANDARD_CONTINGENCIES = ["inspection", "appraisal", "financing"]

    # Market condition thresholds
    SELLERS_MARKET_DOM = 15  # days on market threshold
    BUYERS_MARKET_DOM = 45

    async def analyze_offer_position(
        self,
        property_data: Dict,
        buyer_profile: Dict,
        market_conditions: Optional[Dict] = None,
    ) -> OfferStrategy:
        """Generate an offer strategy based on property, buyer, and market data."""
        market = market_conditions or {}
        list_price = property_data.get("price", 0)
        dom = property_data.get("days_on_market", 0)
        market_type = self._determine_market_type(market, dom)

        # Calculate suggested price
        suggested_price = self._calculate_suggested_price(list_price, dom, market_type)
        rationale = self._generate_rationale(list_price, suggested_price, dom, market_type)

        # Determine contingencies
        contingencies = self._recommend_contingencies(market_type, buyer_profile)

        # Earnest money
        earnest_pct = self._recommend_earnest_money(market_type)

        # Escalation clause
        escalation = self._recommend_escalation(market_type, list_price, buyer_profile)

        # Closing timeline
        timeline = self._recommend_timeline(market_type, buyer_profile)

        # Competitive assessment
        assessment = self._assess_competitiveness(
            suggested_price, list_price, contingencies, earnest_pct, market_type
        )

        return OfferStrategy(
            suggested_price=suggested_price,
            price_rationale=rationale,
            contingencies=contingencies,
            earnest_money_pct=earnest_pct,
            escalation_clause=escalation,
            closing_timeline_days=timeline,
            competitive_assessment=assessment,
        )

    def _determine_market_type(self, market: Dict, dom: int) -> str:
        """Determine if it's a buyer's or seller's market."""
        market_type = market.get("market_type", "")
        if market_type:
            return market_type

        # Infer from days on market
        if dom > 0 and dom <= self.SELLERS_MARKET_DOM:
            return "sellers"
        elif dom > self.BUYERS_MARKET_DOM:
            return "buyers"
        return "balanced"

    def _calculate_suggested_price(
        self, list_price: float, dom: int, market_type: str
    ) -> float:
        """Calculate suggested offer price."""
        if list_price <= 0:
            return 0

        if market_type == "sellers":
            # At or slightly above list in seller's market
            return round(list_price * 1.02, -3)  # 2% above, rounded to nearest $1000
        elif market_type == "buyers":
            # Below list in buyer's market
            discount = 0.05  # 5% base discount
            if dom > 60:
                discount = 0.08  # 8% for stale listings
            elif dom > 90:
                discount = 0.10  # 10% for very stale
            return round(list_price * (1 - discount), -3)
        else:
            # Balanced: at list
            return round(list_price, -3)

    def _generate_rationale(
        self, list_price: float, suggested: float, dom: int, market_type: str
    ) -> str:
        """Generate a human-readable price rationale."""
        if suggested > list_price:
            pct = ((suggested - list_price) / list_price) * 100
            return (
                f"Offering {pct:.0f}% above list price to remain competitive "
                f"in this seller's market."
            )
        elif suggested < list_price:
            pct = ((list_price - suggested) / list_price) * 100
            reason = f"Property has been on market {dom} days. " if dom > 30 else ""
            return (
                f"{reason}Offering {pct:.0f}% below list is reasonable "
                f"in current buyer-favorable conditions."
            )
        return "Offering at list price reflects fair market value in balanced conditions."

    def _recommend_contingencies(
        self, market_type: str, buyer_profile: Dict
    ) -> List[str]:
        """Recommend contingencies based on market conditions."""
        if market_type == "sellers":
            # Fewer contingencies in seller's market
            contingencies = ["inspection"]
            if buyer_profile.get("financing_status") != "cash":
                contingencies.append("financing")
            return contingencies
        elif market_type == "buyers":
            # Full contingencies in buyer's market
            contingencies = list(self.STANDARD_CONTINGENCIES)
            if buyer_profile.get("has_home_to_sell"):
                contingencies.append("sale")
            return contingencies
        # Balanced
        return list(self.STANDARD_CONTINGENCIES)

    def _recommend_earnest_money(self, market_type: str) -> float:
        """Recommend earnest money percentage."""
        if market_type == "sellers":
            return 3.0  # Show commitment
        elif market_type == "buyers":
            return 1.0  # Minimize risk
        return 2.0

    def _recommend_escalation(
        self, market_type: str, list_price: float, buyer_profile: Dict
    ) -> Optional[Dict]:
        """Recommend escalation clause for competitive situations."""
        if market_type != "sellers" or list_price <= 0:
            return None

        budget_max = buyer_profile.get("budget_max", 0)
        if budget_max <= list_price:
            return None

        return {
            "max_price": min(budget_max, list_price * 1.10),
            "increment": round(list_price * 0.005, -2),  # 0.5% increments
        }

    def _recommend_timeline(self, market_type: str, buyer_profile: Dict) -> int:
        """Recommend closing timeline in days."""
        if buyer_profile.get("financing_status") == "cash":
            return 14  # Cash closes fast
        if market_type == "sellers":
            return 21  # Shorter = more competitive
        return 30  # Standard

    def _assess_competitiveness(
        self,
        suggested: float,
        list_price: float,
        contingencies: List[str],
        earnest_pct: float,
        market_type: str,
    ) -> str:
        """Assess overall offer competitiveness."""
        score = 0

        # Price factor
        if list_price > 0:
            ratio = suggested / list_price
            if ratio >= 1.02:
                score += 3
            elif ratio >= 1.0:
                score += 2
            elif ratio >= 0.97:
                score += 1

        # Contingency factor (fewer = stronger)
        if len(contingencies) <= 1:
            score += 2
        elif len(contingencies) <= 2:
            score += 1

        # Earnest money factor
        if earnest_pct >= 3.0:
            score += 1

        if score >= 5:
            return "strong"
        elif score >= 3:
            return "moderate"
        return "weak"
