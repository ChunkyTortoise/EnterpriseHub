"""Multi-property comparison service for buyer decision support."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RankedProperty:
    """A property with fit scoring and analysis."""

    property_data: Dict[str, Any]
    fit_score: float = 0.0  # 0-100
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    price_vs_budget: str = "unknown"  # "under", "at", "over"


@dataclass
class ComparisonMatrix:
    """Side-by-side comparison of multiple properties."""

    properties: List[RankedProperty] = field(default_factory=list)
    comparison_dimensions: List[str] = field(
        default_factory=lambda: [
            "price",
            "bedrooms",
            "bathrooms",
            "sqft",
            "lot_size",
            "year_built",
        ]
    )
    best_overall: Optional[RankedProperty] = None
    best_value: Optional[RankedProperty] = None
    closest_to_budget: Optional[RankedProperty] = None


class PropertyComparator:
    """Compares properties against buyer preferences and generates rankings."""

    def compare(
        self, properties: List[Dict], buyer_preferences: Dict
    ) -> ComparisonMatrix:
        """Compare properties and generate a ranked comparison matrix."""
        if not properties:
            return ComparisonMatrix()

        budget_max = buyer_preferences.get("budget_max", 0)
        budget_min = buyer_preferences.get("budget_min", 0)

        ranked = []
        for prop in properties:
            score = self._calculate_fit_score(prop, buyer_preferences)
            pros = self._identify_pros(prop, buyer_preferences)
            cons = self._identify_cons(prop, buyer_preferences)
            price_vs = self._price_vs_budget(
                prop.get("price", 0), budget_min, budget_max
            )

            ranked.append(
                RankedProperty(
                    property_data=prop,
                    fit_score=score,
                    pros=pros,
                    cons=cons,
                    price_vs_budget=price_vs,
                )
            )

        # Sort by fit score descending
        ranked.sort(key=lambda r: r.fit_score, reverse=True)

        matrix = ComparisonMatrix(properties=ranked)

        if ranked:
            matrix.best_overall = ranked[0]
            matrix.best_value = self._find_best_value(ranked)
            matrix.closest_to_budget = self._find_closest_to_budget(
                ranked, budget_max
            )

        return matrix

    def rank_by_fit(
        self, properties: List[Dict], preferences: Dict
    ) -> List[RankedProperty]:
        """Rank properties by fit score."""
        matrix = self.compare(properties, preferences)
        return matrix.properties

    def generate_summary(self, matrix: ComparisonMatrix) -> str:
        """Generate SMS-friendly comparison summary (< 320 chars)."""
        if not matrix.properties:
            return "No properties to compare yet. Let me know your preferences!"

        lines = [f"Top {min(3, len(matrix.properties))} matches:"]
        for i, prop in enumerate(matrix.properties[:3], 1):
            p = prop.property_data
            price = p.get("price", 0)
            beds = p.get("bedrooms", "?")
            baths = p.get("bathrooms", "?")
            addr = p.get("address", "Address TBD")
            # Shorten address
            if len(addr) > 20:
                addr = addr[:17] + "..."

            price_str = f"${price / 1000:.0f}K" if price >= 1000 else f"${price}"
            label = ""
            if i == 1 and matrix.best_overall == prop:
                label = " Best Match"

            lines.append(f"{i}. {addr} {price_str} {beds}bd/{baths}ba{label}")

        lines.append("Reply # for details!")

        result = "\n".join(lines)
        if len(result) > 320:
            result = result[:317] + "..."
        return result

    def _calculate_fit_score(self, prop: Dict, prefs: Dict) -> float:
        """Calculate 0-100 fit score based on preference matching."""
        score = 50.0  # Base score

        budget_max = prefs.get("budget_max", 0)
        price = prop.get("price", 0)

        # Price fit (30 points)
        if budget_max > 0 and price > 0:
            ratio = price / budget_max
            if ratio <= 1.0:
                score += 30 * (1 - abs(0.85 - ratio) / 0.85)  # Sweet spot at 85%
            else:
                score -= min(30, (ratio - 1.0) * 100)  # Penalty for over budget

        # Bedroom match (20 points)
        pref_beds = prefs.get("bedrooms", 0)
        prop_beds = prop.get("bedrooms", 0)
        if pref_beds > 0 and prop_beds > 0:
            if prop_beds >= pref_beds:
                score += 20
            elif prop_beds == pref_beds - 1:
                score += 10

        # Bathroom match (10 points)
        pref_baths = prefs.get("bathrooms", 0)
        prop_baths = prop.get("bathrooms", 0)
        if pref_baths > 0 and prop_baths > 0:
            if prop_baths >= pref_baths:
                score += 10
            elif prop_baths >= pref_baths - 0.5:
                score += 5

        # Feature match (10 points)
        pref_features = set(f.lower() for f in prefs.get("features", []))
        prop_features = set(f.lower() for f in prop.get("features", []))
        if pref_features:
            overlap = len(pref_features & prop_features)
            score += (overlap / len(pref_features)) * 10

        return max(0.0, min(100.0, score))

    def _identify_pros(self, prop: Dict, prefs: Dict) -> List[str]:
        """Identify property strengths relative to preferences."""
        pros = []
        budget_max = prefs.get("budget_max", 0)
        price = prop.get("price", 0)

        if budget_max > 0 and price > 0 and price <= budget_max:
            savings = budget_max - price
            if savings > 10000:
                pros.append(f"${savings / 1000:.0f}K under budget")

        pref_beds = prefs.get("bedrooms", 0)
        if prop.get("bedrooms", 0) > pref_beds > 0:
            pros.append("Extra bedroom")

        if prop.get("year_built", 0) >= 2020:
            pros.append("Newer construction")

        for feature in prop.get("features", []):
            if feature.lower() in [f.lower() for f in prefs.get("features", [])]:
                pros.append(f"Has {feature}")

        return pros

    def _identify_cons(self, prop: Dict, prefs: Dict) -> List[str]:
        """Identify property weaknesses relative to preferences."""
        cons = []
        budget_max = prefs.get("budget_max", 0)
        price = prop.get("price", 0)

        if budget_max > 0 and price > budget_max:
            over = price - budget_max
            cons.append(f"${over / 1000:.0f}K over budget")

        pref_beds = prefs.get("bedrooms", 0)
        if 0 < prop.get("bedrooms", 0) < pref_beds:
            cons.append("Fewer bedrooms than preferred")

        if prop.get("year_built", 0) > 0 and prop.get("year_built", 0) < 1980:
            cons.append("Older construction")

        return cons

    def _price_vs_budget(
        self, price: float, budget_min: float, budget_max: float
    ) -> str:
        """Classify price relative to budget."""
        if budget_max <= 0 or price <= 0:
            return "unknown"
        if price > budget_max:
            return "over"
        if budget_min > 0 and price < budget_min:
            return "under"
        if price >= budget_max * 0.95:
            return "at"
        return "under"

    def _find_best_value(self, ranked: List[RankedProperty]) -> RankedProperty:
        """Find property with best price-per-sqft ratio."""
        best = ranked[0]
        best_ratio = float("inf")
        for r in ranked:
            price = r.property_data.get("price", 0)
            sqft = r.property_data.get("sqft", 0)
            if price > 0 and sqft > 0:
                ratio = price / sqft
                if ratio < best_ratio:
                    best_ratio = ratio
                    best = r
        return best

    def _find_closest_to_budget(
        self, ranked: List[RankedProperty], budget_max: float
    ) -> RankedProperty:
        """Find property closest to (but not exceeding) budget."""
        if budget_max <= 0:
            return ranked[0]

        under_budget = [
            r
            for r in ranked
            if r.property_data.get("price", 0) <= budget_max
        ]
        if not under_budget:
            return ranked[-1]  # Least over budget

        # Closest to budget_max without exceeding
        return max(under_budget, key=lambda r: r.property_data.get("price", 0))
