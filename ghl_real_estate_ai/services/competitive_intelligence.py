"""
Competitive Intelligence Tracker - Wow Factor Feature #5
Tracks market competition and provides strategic insights

⚠️ DEPRECATION WARNING ⚠️
This service is being consolidated into CompetitiveIntelligenceHub.
Please migrate to: ghl_real_estate_ai.services.competitive_intelligence_hub

Migration Guide: See COMPETITIVE_INTELLIGENCE_CONSOLIDATION_MIGRATION_GUIDE.md
Target Removal: 2026-02-15
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List


@dataclass
class CompetitiveInsight:
    """Competitive intelligence insight"""

    insight_type: str
    competitor_name: str
    description: str
    threat_level: str  # "high", "medium", "low"
    recommended_response: str
    data_source: str

    def to_dict(self) -> Dict:
        return asdict(self)


class CompetitiveIntelligenceService:
    """
    🎯 WOW FEATURE: Competitive Intelligence Tracker

    Monitors competitive threats and provides strategic insights
    to help Jorge win deals against other agents.

    Features:
    - Competitor detection in conversations
    - Market positioning analysis
    - Win/loss tracking by competitor
    - Differentiation recommendations
    - Pricing intelligence
    """

    def __init__(self):
        import warnings

        warnings.warn(
            "CompetitiveIntelligenceService is deprecated and will be removed in v3.0. "
            "Please migrate to CompetitiveIntelligenceHub from "
            "ghl_real_estate_ai.services.competitive_intelligence_hub. "
            "See COMPETITIVE_INTELLIGENCE_CONSOLIDATION_MIGRATION_GUIDE.md for details.",
            DeprecationWarning,
            stacklevel=2,
        )

        self.known_competitors = self._load_competitor_database()
        self.win_loss_data = {}

    def analyze_competitive_landscape(self, lead_data: Dict) -> Dict:
        """
        Analyze competitive threats for a specific lead

        Returns insights and recommended responses
        """
        insights = []
        conversations = lead_data.get("conversations", [])
        metadata = lead_data.get("metadata", {})

        # Detect competitor mentions
        competitors = self._detect_competitors(conversations)

        if competitors:
            for competitor in competitors:
                threat_level = self._assess_threat_level(competitor, metadata)

                insights.append(
                    CompetitiveInsight(
                        insight_type="competitor_detected",
                        competitor_name=competitor,
                        description=f"Lead mentioned {competitor} as alternative option",
                        threat_level=threat_level,
                        recommended_response=self._get_differentiation_strategy(competitor),
                        data_source="conversation_analysis",
                    )
                )

        # Pricing competition
        if metadata.get("mentioned_lower_price"):
            insights.append(
                CompetitiveInsight(
                    insight_type="pricing_pressure",
                    competitor_name="Unknown competitor",
                    description="Lead mentioned receiving lower price quote",
                    threat_level="medium",
                    recommended_response="Emphasize Jorge's dual-path advantage and value-add services",
                    data_source="conversation_analysis",
                )
            )

        # Time-to-market competition
        if metadata.get("urgency") == "high":
            insights.append(
                CompetitiveInsight(
                    insight_type="speed_competition",
                    competitor_name="Market timing",
                    description="Lead needs fast action - may go with quickest responder",
                    threat_level="high",
                    recommended_response="Highlight cash offer with 7-day close option",
                    data_source="urgency_analysis",
                )
            )

        return {
            "lead_id": lead_data.get("lead_id"),
            "analysis_date": datetime.now().isoformat(),
            "competitors_detected": len(competitors),
            "highest_threat_level": self._get_highest_threat(insights),
            "insights": [i.to_dict() for i in insights],
            "jorge_advantages": self._get_jorge_advantages(),
            "recommended_strategy": self._get_overall_strategy(insights),
        }

    def track_win_loss(self, deal_id: str, won: bool, competitor: str, reason: str):
        """Track wins and losses against competitors"""
        if competitor not in self.win_loss_data:
            self.win_loss_data[competitor] = {"wins": 0, "losses": 0, "reasons": []}

        if won:
            self.win_loss_data[competitor]["wins"] += 1
        else:
            self.win_loss_data[competitor]["losses"] += 1
            self.win_loss_data[competitor]["reasons"].append(reason)

    def get_competitor_report(self, competitor_name: str = None) -> Dict:
        """Generate competitive intelligence report"""
        if competitor_name:
            data = self.win_loss_data.get(competitor_name, {})
            total = data.get("wins", 0) + data.get("losses", 0)
            win_rate = data.get("wins", 0) / total if total > 0 else 0

            return {
                "competitor": competitor_name,
                "wins": data.get("wins", 0),
                "losses": data.get("losses", 0),
                "win_rate": f"{win_rate * 100:.1f}%",
                "common_loss_reasons": self._get_top_reasons(data.get("reasons", [])),
                "recommended_counter_strategies": self._get_counter_strategies(competitor_name),
            }
        else:
            # Overall report
            return {
                "total_competitors": len(self.win_loss_data),
                "overall_win_rate": self._calculate_overall_win_rate(),
                "top_competitors": self._get_top_competitors(5),
                "market_position": self._assess_market_position(),
                "strategic_opportunities": self._identify_opportunities(),
            }

    def _detect_competitors(self, conversations: List) -> List[str]:
        """Detect competitor mentions in conversations"""
        competitors = []
        competitor_keywords = {
            "remax": "RE/MAX",
            "re/max": "RE/MAX",
            "keller williams": "Keller Williams",
            "coldwell": "Coldwell Banker",
            "century 21": "Century 21",
            "exp realty": "eXp Realty",
            "compass": "Compass",
            "other agent": "Independent Agent",
            "another realtor": "Independent Agent",
        }

        for conv in conversations:
            message = conv.get("message", "").lower()
            for keyword, name in competitor_keywords.items():
                if keyword in message and name not in competitors:
                    competitors.append(name)

        return competitors

    def _assess_threat_level(self, competitor: str, metadata: Dict) -> str:
        """Assess threat level from specific competitor"""
        # Big names = higher threat
        major_brands = ["RE/MAX", "Keller Williams", "Coldwell Banker", "Compass"]

        if competitor in major_brands:
            threat = "high"
        else:
            threat = "medium"

        # Adjust based on lead quality
        if metadata.get("score", 0) > 8:
            # High-value lead makes any competition high threat
            threat = "high"

        return threat

    def _get_differentiation_strategy(self, competitor: str) -> str:
        """Get strategy to differentiate from specific competitor"""
        strategies = {
            "RE/MAX": "Highlight personal service - 'Big franchises treat you like a number. We treat you like family.'",
            "Keller Williams": "Emphasize dual-path option - 'They only list. We can buy cash OR list.'",
            "Coldwell Banker": "Focus on speed - 'Traditional agents take 60+ days. We close cash deals in 7.'",
            "Compass": "Value proposition - 'Same tech, better local knowledge, no fancy office overhead.'",
            "Independent Agent": "Proven track record - 'We close 10x more deals per month. Experience matters.'",
        }

        return strategies.get(competitor, "Emphasize Jorge's unique dual-path approach and speed to close")

    def _get_jorge_advantages(self) -> List[str]:
        """List Jorge's competitive advantages"""
        return [
            "🏆 Dual-Path Option: Cash offer OR traditional listing",
            "⚡ Speed: Close cash deals in 7 days vs 60+ for traditional",
            "💰 No Hidden Fees: Transparent pricing, no surprises",
            "🎯 Local Expert: Deep Miami market knowledge",
            "🤝 Personal Service: Direct access to decision makers",
            "📊 Data-Driven: AI-powered property matching",
            "💬 24/7 Communication: Never miss a hot lead",
        ]

    def _get_overall_strategy(self, insights: List[CompetitiveInsight]) -> str:
        """Determine overall competitive strategy"""
        if not insights:
            return "No immediate competitive threats detected. Focus on building relationship."

        high_threats = [i for i in insights if i.threat_level == "high"]

        if high_threats:
            return "🚨 HIGH THREAT: Move fast. Schedule in-person meeting ASAP and close before competition does."
        else:
            return "⚠️ MODERATE THREAT: Differentiate with dual-path advantage and local expertise."

    def _get_highest_threat(self, insights: List[CompetitiveInsight]) -> str:
        """Get highest threat level from insights"""
        if any(i.threat_level == "high" for i in insights):
            return "high"
        elif any(i.threat_level == "medium" for i in insights):
            return "medium"
        else:
            return "low"

    def _calculate_overall_win_rate(self) -> str:
        """Calculate overall win rate across all competitors"""
        total_wins = sum(data.get("wins", 0) for data in self.win_loss_data.values())
        total_deals = sum(data.get("wins", 0) + data.get("losses", 0) for data in self.win_loss_data.values())

        if total_deals == 0:
            return "N/A"

        win_rate = total_wins / total_deals
        return f"{win_rate * 100:.1f}%"

    def _get_top_competitors(self, limit: int) -> List[Dict]:
        """Get top competitors by deal volume"""
        competitors = []
        for name, data in self.win_loss_data.items():
            total = data.get("wins", 0) + data.get("losses", 0)
            competitors.append(
                {
                    "name": name,
                    "total_deals": total,
                    "win_rate": (f"{data.get('wins', 0) / total * 100:.1f}%" if total > 0 else "N/A"),
                }
            )

        return sorted(competitors, key=lambda x: x["total_deals"], reverse=True)[:limit]

    def _assess_market_position(self) -> str:
        """Assess Jorge's overall market position"""
        win_rate_str = self._calculate_overall_win_rate()

        if win_rate_str == "N/A":
            return "Insufficient data"

        win_rate = float(win_rate_str.rstrip("%"))

        if win_rate > 70:
            return "🏆 DOMINANT: Consistently winning against competition"
        elif win_rate > 50:
            return "💪 STRONG: Competitive position with room for improvement"
        else:
            return "⚠️ CHALLENGED: Need to refine value proposition"

    def _identify_opportunities(self) -> List[str]:
        """Identify strategic opportunities"""
        return [
            "Emphasize 7-day cash close speed advantage",
            "Promote dual-path flexibility more prominently",
            "Leverage AI-powered property matching as differentiator",
            "Build case studies of successful fast closes",
        ]

    def _get_top_reasons(self, reasons: List[str]) -> List[str]:
        """Get most common loss reasons"""
        if not reasons:
            return []

        # Count frequency
        reason_counts = {}
        for reason in reasons:
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

        # Sort by frequency
        sorted_reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)

        return [reason for reason, count in sorted_reasons[:3]]

    def _get_counter_strategies(self, competitor: str) -> List[str]:
        """Get strategies to counter specific competitor"""
        return [
            f"When {competitor} is mentioned, immediately highlight dual-path advantage",
            "Provide faster response time than typical agents",
            "Offer same-day property evaluation",
            "Share recent success stories and testimonials",
        ]

    def _load_competitor_database(self) -> Dict:
        """Load known competitor database"""
        return {
            "RE/MAX": {"market_share": 0.15, "avg_days_to_close": 45},
            "Keller Williams": {"market_share": 0.18, "avg_days_to_close": 50},
            "Coldwell Banker": {"market_share": 0.12, "avg_days_to_close": 55},
            "Compass": {"market_share": 0.08, "avg_days_to_close": 40},
        }


# Example usage
if __name__ == "__main__":
    intel_service = CompetitiveIntelligenceService()

    # Example lead with competition
    competitive_lead = {
        "lead_id": "L999",
        "conversations": [
            {"sender": "lead", "message": "I'm also talking to a RE/MAX agent"},
            {
                "sender": "agent",
                "message": "That's smart to compare. What made you reach out to us too?",
            },
            {
                "sender": "lead",
                "message": "They said 60 days to close. You mentioned 7 days?",
            },
        ],
        "metadata": {"score": 8.2, "urgency": "high", "mentioned_lower_price": False},
    }

    analysis = intel_service.analyze_competitive_landscape(competitive_lead)

    print("🎯 Competitive Intelligence Report\n")
    print(f"Competitors Detected: {analysis['competitors_detected']}")
    print(f"Threat Level: {analysis['highest_threat_level'].upper()}\n")
    print("Jorge's Advantages:")
    for advantage in analysis["jorge_advantages"][:3]:
        print(f"  {advantage}")
    print(f"\nRecommended Strategy:\n  {analysis['recommended_strategy']}")
