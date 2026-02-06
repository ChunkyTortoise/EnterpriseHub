"""
Win/Loss Analysis Service - Agent 3: Revenue Maximizer
Learn from closed and lost deals to continuously improve performance.

Revenue Impact: +$30K-50K/year through pattern recognition
Features:
- Track reasons for won/lost deals
- Identify patterns and trends
- Competitive intelligence gathering
- Continuous improvement recommendations
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter
from enum import Enum
import json


class DealOutcome(Enum):
    """Deal outcome types."""
    WON = "won"
    LOST = "lost"
    PENDING = "pending"


class LossReason(Enum):
    """Common reasons for losing deals."""
    PRICE = "price_too_high"
    COMPETITION = "chose_competitor"
    TIMING = "timing_not_right"
    FINANCING = "financing_fell_through"
    PROPERTY = "property_issues"
    COMMUNICATION = "poor_communication"
    TRUST = "trust_concerns"
    LOCATION = "location_concerns"
    OTHER = "other"


class WinReason(Enum):
    """Common reasons for winning deals."""
    RELATIONSHIP = "strong_relationship"
    EXPERTISE = "local_expertise"
    RESPONSIVENESS = "quick_response"
    PRICING = "competitive_pricing"
    MARKETING = "effective_marketing"
    NEGOTIATION = "strong_negotiation"
    REFERRAL = "referral_trust"
    TECHNOLOGY = "tech_advantage"
    OTHER = "other"


class WinLossAnalysis:
    """
    Comprehensive win/loss analysis system to learn from every deal.
    Tracks outcomes, identifies patterns, and provides actionable insights.
    """
    
    def __init__(self):
        """Initialize Win/Loss Analysis system."""
        self.deals = []
        self.insights_cache = None
        self.last_analysis = None
    
    def record_outcome(
        self,
        deal_id: str,
        client_name: str,
        property_address: str,
        property_price: float,
        outcome: DealOutcome,
        reason: str,
        reason_category: Optional[Enum] = None,
        competitor_name: Optional[str] = None,
        deal_duration_days: int = 0,
        commission_value: float = 0,
        automation_features_used: Optional[List[str]] = None,
        notes: Optional[str] = None,
        date: Optional[datetime] = None
    ) -> Dict:
        """
        Record a deal outcome (won or lost).
        
        Args:
            deal_id: Unique deal identifier
            client_name: Client name
            property_address: Property address
            property_price: Property value
            outcome: Won, Lost, or Pending
            reason: Detailed reason text
            reason_category: Categorized reason
            competitor_name: Name of competing agent/agency (if lost)
            deal_duration_days: Days from lead to outcome
            commission_value: Commission earned (if won)
            automation_features_used: Which automations were used
            notes: Additional notes
            date: Outcome date
            
        Returns:
            Recorded deal data
        """
        if date is None:
            date = datetime.now()
        
        record = {
            "deal_id": deal_id,
            "client_name": client_name,
            "property_address": property_address,
            "property_price": property_price,
            "outcome": outcome.value,
            "reason": reason,
            "reason_category": reason_category.value if reason_category else self._auto_categorize_reason(reason, outcome),
            "competitor_name": competitor_name,
            "deal_duration_days": deal_duration_days,
            "commission_value": commission_value if outcome == DealOutcome.WON else 0,
            "automation_features": automation_features_used or [],
            "notes": notes,
            "date": date.isoformat(),
            "recorded_at": datetime.now().isoformat()
        }
        
        self.deals.append(record)
        self.insights_cache = None  # Invalidate cache
        
        return record
    
    def _auto_categorize_reason(self, reason: str, outcome: DealOutcome) -> str:
        """Auto-categorize reason based on keywords."""
        reason_lower = reason.lower()
        
        if outcome == DealOutcome.LOST:
            if any(word in reason_lower for word in ["price", "expensive", "cost", "afford"]):
                return LossReason.PRICE.value
            elif any(word in reason_lower for word in ["competitor", "agent", "another", "other"]):
                return LossReason.COMPETITION.value
            elif any(word in reason_lower for word in ["timing", "wait", "not ready", "later"]):
                return LossReason.TIMING.value
            elif any(word in reason_lower for word in ["financing", "loan", "mortgage", "credit"]):
                return LossReason.FINANCING.value
            elif any(word in reason_lower for word in ["property", "condition", "repair", "inspection"]):
                return LossReason.PROPERTY.value
            elif any(word in reason_lower for word in ["communication", "response", "follow", "contact"]):
                return LossReason.COMMUNICATION.value
            elif any(word in reason_lower for word in ["trust", "concern", "worry", "hesitant"]):
                return LossReason.TRUST.value
            elif any(word in reason_lower for word in ["location", "neighborhood", "area"]):
                return LossReason.LOCATION.value
            else:
                return LossReason.OTHER.value
        
        else:  # WON
            if any(word in reason_lower for word in ["relationship", "rapport", "connection"]):
                return WinReason.RELATIONSHIP.value
            elif any(word in reason_lower for word in ["expertise", "knowledge", "experienced"]):
                return WinReason.EXPERTISE.value
            elif any(word in reason_lower for word in ["responsive", "quick", "fast", "available"]):
                return WinReason.RESPONSIVENESS.value
            elif any(word in reason_lower for word in ["price", "pricing", "value"]):
                return WinReason.PRICING.value
            elif any(word in reason_lower for word in ["marketing", "listing", "photos"]):
                return WinReason.MARKETING.value
            elif any(word in reason_lower for word in ["negotiation", "deal", "terms"]):
                return WinReason.NEGOTIATION.value
            elif any(word in reason_lower for word in ["referral", "recommended", "referred"]):
                return WinReason.REFERRAL.value
            elif any(word in reason_lower for word in ["technology", "tech", "automation", "system"]):
                return WinReason.TECHNOLOGY.value
            else:
                return WinReason.OTHER.value
    
    def get_win_rate(self, days: Optional[int] = None) -> Dict:
        """
        Calculate overall win rate.
        
        Args:
            days: Optional filter for recent N days
            
        Returns:
            Win rate statistics
        """
        deals = self._filter_deals(days)
        
        if not deals:
            return {
                "total_deals": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "period": f"Last {days} days" if days else "All time"
            }
        
        won = len([d for d in deals if d["outcome"] == DealOutcome.WON.value])
        lost = len([d for d in deals if d["outcome"] == DealOutcome.LOST.value])
        pending = len([d for d in deals if d["outcome"] == DealOutcome.PENDING.value])
        
        concluded = won + lost
        win_rate = (won / concluded * 100) if concluded > 0 else 0
        
        total_commission = sum(d["commission_value"] for d in deals if d["outcome"] == DealOutcome.WON.value)
        
        return {
            "total_deals": len(deals),
            "won": won,
            "lost": lost,
            "pending": pending,
            "concluded": concluded,
            "win_rate": round(win_rate, 1),
            "total_commission_won": round(total_commission, 2),
            "avg_commission_per_win": round(total_commission / won, 2) if won > 0 else 0,
            "period": f"Last {days} days" if days else "All time"
        }
    
    def analyze_loss_patterns(self, limit: int = 10) -> Dict:
        """
        Analyze patterns in lost deals.
        
        Args:
            limit: Number of recent losses to analyze
            
        Returns:
            Loss pattern analysis
        """
        lost_deals = [d for d in self.deals if d["outcome"] == DealOutcome.LOST.value]
        recent_losses = sorted(lost_deals, key=lambda x: x["date"], reverse=True)[:limit]
        
        if not recent_losses:
            return {
                "total_losses": 0,
                "top_reasons": [],
                "recommendations": ["No losses to analyze yet - keep up the good work!"]
            }
        
        # Count reasons
        reason_counts = Counter(d["reason_category"] for d in recent_losses)
        top_reasons = reason_counts.most_common(5)
        
        # Analyze competitors
        competitors = [d["competitor_name"] for d in recent_losses if d["competitor_name"]]
        competitor_counts = Counter(competitors).most_common(3)
        
        # Calculate average deal value lost
        avg_lost_value = sum(d["property_price"] for d in recent_losses) / len(recent_losses)
        
        # Estimate lost commission
        estimated_lost_commission = avg_lost_value * 0.025 * 0.80 * len(recent_losses)
        
        # Generate recommendations
        recommendations = self._generate_loss_recommendations(reason_counts)
        
        return {
            "total_losses": len(lost_deals),
            "recent_losses_analyzed": len(recent_losses),
            "top_reasons": [
                {
                    "reason": reason,
                    "count": count,
                    "percentage": round(count / len(recent_losses) * 100, 1)
                }
                for reason, count in top_reasons
            ],
            "top_competitors": [
                {"name": comp, "losses_to": count}
                for comp, count in competitor_counts
            ],
            "avg_lost_deal_value": round(avg_lost_value, 2),
            "estimated_lost_commission": round(estimated_lost_commission, 2),
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
    
    def analyze_win_patterns(self, limit: int = 10) -> Dict:
        """
        Analyze patterns in won deals.
        
        Args:
            limit: Number of recent wins to analyze
            
        Returns:
            Win pattern analysis
        """
        won_deals = [d for d in self.deals if d["outcome"] == DealOutcome.WON.value]
        recent_wins = sorted(won_deals, key=lambda x: x["date"], reverse=True)[:limit]
        
        if not recent_wins:
            return {
                "total_wins": 0,
                "top_reasons": [],
                "recommendations": ["No wins recorded yet"]
            }
        
        # Count reasons
        reason_counts = Counter(d["reason_category"] for d in recent_wins)
        top_reasons = reason_counts.most_common(5)
        
        # Analyze automation impact
        automation_usage = []
        for deal in recent_wins:
            automation_usage.extend(deal["automation_features"])
        
        automation_counts = Counter(automation_usage).most_common(5)
        
        # Calculate metrics
        avg_deal_duration = sum(d["deal_duration_days"] for d in recent_wins) / len(recent_wins)
        total_commission = sum(d["commission_value"] for d in recent_wins)
        
        return {
            "total_wins": len(won_deals),
            "recent_wins_analyzed": len(recent_wins),
            "top_win_factors": [
                {
                    "factor": reason,
                    "count": count,
                    "percentage": round(count / len(recent_wins) * 100, 1)
                }
                for reason, count in top_reasons
            ],
            "top_automation_features": [
                {
                    "feature": feature,
                    "wins_with_feature": count,
                    "percentage": round(count / len(recent_wins) * 100, 1)
                }
                for feature, count in automation_counts
            ],
            "avg_deal_duration_days": round(avg_deal_duration, 1),
            "total_commission": round(total_commission, 2),
            "avg_commission": round(total_commission / len(recent_wins), 2),
            "recommendations": self._generate_win_recommendations(reason_counts),
            "generated_at": datetime.now().isoformat()
        }
    
    def _generate_loss_recommendations(self, reason_counts: Counter) -> List[str]:
        """Generate actionable recommendations from loss patterns."""
        recommendations = []
        
        top_reason = reason_counts.most_common(1)[0][0] if reason_counts else None
        
        recommendations_map = {
            LossReason.PRICE.value: [
                "Consider improving CMA accuracy to justify pricing",
                "Use Commission Calculator to show value vs. discount agents",
                "Implement better property valuation automation"
            ],
            LossReason.COMPETITION.value: [
                "Strengthen unique value proposition (UVP)",
                "Use Deal Closer AI to handle competitive objections",
                "Collect and showcase more client testimonials"
            ],
            LossReason.TIMING.value: [
                "Implement longer nurture sequences for 'not ready' leads",
                "Use Hot Lead Fast Lane to prioritize ready buyers",
                "Set up automated timeline-based follow-ups"
            ],
            LossReason.FINANCING.value: [
                "Build stronger lender partnerships",
                "Qualify leads earlier on financing capacity",
                "Provide pre-qualification assistance"
            ],
            LossReason.PROPERTY.value: [
                "Offer pre-inspection services",
                "Set better expectations on property conditions",
                "Provide renovation cost estimates upfront"
            ],
            LossReason.COMMUNICATION.value: [
                "Use automation to ensure no lead falls through cracks",
                "Implement Voice Receptionist for 24/7 availability",
                "Set up auto-follow-up sequences"
            ],
            LossReason.TRUST.value: [
                "Strengthen online presence and reviews",
                "Provide more transparency in process",
                "Share credentials and past success stories"
            ]
        }
        
        if top_reason in recommendations_map:
            recommendations.extend(recommendations_map[top_reason])
        
        return recommendations[:5]
    
    def _generate_win_recommendations(self, reason_counts: Counter) -> List[str]:
        """Generate recommendations to amplify winning strategies."""
        recommendations = []
        
        top_reason = reason_counts.most_common(1)[0][0] if reason_counts else None
        
        recommendations_map = {
            WinReason.RELATIONSHIP.value: [
                "Double down on relationship-building activities",
                "Implement more personalized communication",
                "Consider client appreciation events"
            ],
            WinReason.EXPERTISE.value: [
                "Create more educational content showcasing expertise",
                "Offer free market analysis to demonstrate knowledge",
                "Share neighborhood insights regularly"
            ],
            WinReason.RESPONSIVENESS.value: [
                "Maintain fast response times with automation",
                "Advertise 24/7 availability via Voice Receptionist",
                "Use Hot Lead Fast Lane for instant prioritization"
            ],
            WinReason.PRICING.value: [
                "Highlight competitive pricing strategy in marketing",
                "Use data-driven CMAs as differentiator",
                "Share success stories of well-priced listings"
            ],
            WinReason.TECHNOLOGY.value: [
                "Showcase technology advantage in marketing",
                "Educate clients on automation benefits",
                "Create demos showing tech capabilities"
            ],
            WinReason.REFERRAL.value: [
                "Build formal referral reward program",
                "Ask for referrals more systematically",
                "Stay in touch with past clients"
            ]
        }
        
        if top_reason in recommendations_map:
            recommendations.extend(recommendations_map[top_reason])
        
        return recommendations[:5]
    
    def get_comprehensive_report(self, days: Optional[int] = 90) -> Dict:
        """
        Generate comprehensive win/loss report.
        
        Args:
            days: Number of days to analyze (default 90)
            
        Returns:
            Complete analysis report
        """
        win_rate = self.get_win_rate(days)
        loss_patterns = self.analyze_loss_patterns()
        win_patterns = self.analyze_win_patterns()
        
        # Calculate trends
        trends = self._calculate_trends(days)
        
        # Competitive intelligence
        competitive_intel = self._analyze_competitive_landscape()
        
        return {
            "report_period": f"Last {days} days" if days else "All time",
            "win_rate": win_rate,
            "loss_analysis": loss_patterns,
            "win_analysis": win_patterns,
            "trends": trends,
            "competitive_intelligence": competitive_intel,
            "key_insights": self._generate_key_insights(win_rate, loss_patterns, win_patterns),
            "action_items": self._generate_action_items(loss_patterns, win_patterns),
            "generated_at": datetime.now().isoformat()
        }
    
    def _filter_deals(self, days: Optional[int]) -> List[Dict]:
        """Filter deals by date range."""
        if not days:
            return self.deals
        
        cutoff = datetime.now() - timedelta(days=days)
        return [d for d in self.deals if datetime.fromisoformat(d["date"]) > cutoff]
    
    def _calculate_trends(self, days: int) -> Dict:
        """Calculate performance trends over time."""
        # Compare recent period vs previous period
        recent = self._filter_deals(days)
        previous = self._filter_deals(days * 2)
        previous = [d for d in previous if datetime.fromisoformat(d["date"]) <= datetime.now() - timedelta(days=days)]
        
        recent_wr = self.get_win_rate(days)["win_rate"]
        
        if previous:
            prev_won = len([d for d in previous if d["outcome"] == DealOutcome.WON.value])
            prev_lost = len([d for d in previous if d["outcome"] == DealOutcome.LOST.value])
            prev_wr = (prev_won / (prev_won + prev_lost) * 100) if (prev_won + prev_lost) > 0 else 0
            trend = recent_wr - prev_wr
        else:
            trend = 0
        
        return {
            "win_rate_trend": round(trend, 1),
            "trend_direction": "improving" if trend > 0 else "declining" if trend < 0 else "stable",
            "recent_win_rate": recent_wr,
            "comparison_period": f"{days} days vs previous {days} days"
        }
    
    def _analyze_competitive_landscape(self) -> Dict:
        """Analyze competitive landscape from lost deals."""
        lost_deals = [d for d in self.deals if d["outcome"] == DealOutcome.LOST.value and d["competitor_name"]]
        
        if not lost_deals:
            return {"competitors_identified": 0, "top_competitors": []}
        
        competitor_counts = Counter(d["competitor_name"] for d in lost_deals)
        
        return {
            "competitors_identified": len(competitor_counts),
            "top_competitors": [
                {"name": comp, "losses_to": count}
                for comp, count in competitor_counts.most_common(5)
            ],
            "note": "Track these competitors to understand their strategies"
        }
    
    def _generate_key_insights(self, win_rate: Dict, loss_patterns: Dict, win_patterns: Dict) -> List[str]:
        """Generate key insights from analysis."""
        insights = []
        
        # Win rate insights
        if win_rate["win_rate"] >= 70:
            insights.append(f"🎉 Excellent {win_rate['win_rate']}% win rate - well above industry average")
        elif win_rate["win_rate"] >= 50:
            insights.append(f"✅ Solid {win_rate['win_rate']}% win rate - room for improvement")
        else:
            insights.append(f"⚠️ {win_rate['win_rate']}% win rate needs attention - focus on loss prevention")
        
        # Loss insights
        if loss_patterns["top_reasons"]:
            top_loss = loss_patterns["top_reasons"][0]
            insights.append(f"📉 Main loss reason: {top_loss['reason']} ({top_loss['percentage']}% of losses)")
        
        # Win insights
        if win_patterns["top_win_factors"]:
            top_win = win_patterns["top_win_factors"][0]
            insights.append(f"📈 Primary win factor: {top_win['factor']} ({top_win['percentage']}% of wins)")
        
        return insights
    
    def _generate_action_items(self, loss_patterns: Dict, win_patterns: Dict) -> List[str]:
        """Generate prioritized action items."""
        actions = []
        
        # From losses
        if loss_patterns.get("recommendations"):
            actions.append(f"Priority: {loss_patterns['recommendations'][0]}")
        
        # From wins
        if win_patterns.get("recommendations"):
            actions.append(f"Amplify: {win_patterns['recommendations'][0]}")
        
        # General
        actions.append("Continue tracking all deal outcomes for better insights")
        
        return actions


if __name__ == "__main__":
    # Demo usage
    analyzer = WinLossAnalysis()
    
    print("📊 Win/Loss Analysis - Demo\n")
    
    # Record some sample outcomes
    analyzer.record_outcome(
        deal_id="D001",
        client_name="Sarah Johnson",
        property_address="123 Main St",
        property_price=850000,
        outcome=DealOutcome.WON,
        reason="Quick response time and strong local knowledge",
        commission_value=17000,
        automation_features_used=["hot_lead_fastlane", "deal_closer_ai"],
        deal_duration_days=45
    )
    
    analyzer.record_outcome(
        deal_id="D002",
        client_name="Mike Chen",
        property_address="456 Oak Ave",
        property_price=650000,
        outcome=DealOutcome.LOST,
        reason="Client felt price was too high",
        competitor_name="Smith Realty",
        deal_duration_days=30
    )
    
    # Get win rate
    wr = analyzer.get_win_rate()
    print(f"Win Rate: {wr['win_rate']}%")
    print(f"Won: {wr['won']} | Lost: {wr['lost']}")
    print()
    
    # Analyze patterns
    report = analyzer.get_comprehensive_report()
    print("Key Insights:")
    for insight in report["key_insights"]:
        print(f"  {insight}")
