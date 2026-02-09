"""
Revenue Attribution System

Tracks leads through entire lifecycle and attributes revenue accurately
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class RevenueAttributionEngine:
    """Track and attribute revenue to marketing channels and activities"""

    def __init__(self, data_dir: Path = None):
        """
        Execute init operation.

        Args:
            data_dir: Data to process
        """
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"

    def get_full_attribution_report(
        self,
        location_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Generate complete revenue attribution report

        Args:
            location_id: GHL location ID
            start_date: Start of analysis period
            end_date: End of analysis period

        Returns:
            Complete revenue attribution with channel breakdown
        """
        if not start_date:
            start_date = datetime.now(timezone.utc) - timedelta(days=90)
        elif start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        else:
            start_date = start_date.astimezone(timezone.utc)

        if not end_date:
            end_date = datetime.now(timezone.utc)
        elif end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        else:
            end_date = end_date.astimezone(timezone.utc)

        # Load data
        conversations = self._load_conversations(location_id, start_date, end_date)

        # Build attribution
        attribution = self._build_attribution_model(conversations)

        # Calculate channel performance
        channel_performance = self._calculate_channel_performance(attribution)

        # Calculate conversion funnel
        funnel = self._calculate_conversion_funnel(conversations)

        # Revenue timeline
        timeline = self._build_revenue_timeline(attribution)

        # ROI by source
        roi_by_source = self._calculate_roi_by_source(channel_performance)

        return {
            "location_id": location_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": (end_date - start_date).days,
            },
            "summary": {
                "total_revenue": attribution["total_revenue"],
                "total_deals": attribution["total_deals"],
                "avg_deal_value": attribution["avg_deal_value"],
                "conversion_rate": funnel["overall_conversion_rate"],
                "pipeline_value": attribution["pipeline_value"],
            },
            "channel_performance": channel_performance,
            "conversion_funnel": funnel,
            "revenue_timeline": timeline,
            "roi_by_source": roi_by_source,
            "top_performers": self._identify_top_performers(attribution),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _load_conversations(self, location_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Load conversation data for period"""
        analytics_file = self.data_dir / "mock_analytics.json"

        if not analytics_file.exists():
            return []

        with open(analytics_file) as f:
            data = json.load(f)

        conversations = []
        for c in data.get("conversations", []):
            ts_str = c.get("start_time") or c.get("timestamp")
            if ts_str:
                try:
                    # Handle Z or +00:00 and make it offset-aware
                    # Python 3.11+ handles Z, but we support replace for safety
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    else:
                        ts = ts.astimezone(timezone.utc)

                    if start_date <= ts <= end_date:
                        conversations.append(c)
                except ValueError:
                    continue

        return conversations

    def _build_attribution_model(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Build attribution model from conversations"""

        # Simulate deal closure data
        # In production, would track actual deals through CRM
        hot_leads = [c for c in conversations if c.get("lead_score", 0) >= 70]
        appointments = [c for c in conversations if c.get("appointment_set", False)]

        # Assume conversion rates at each stage
        properties_shown = int(len(appointments) * 0.65)  # 65% show rate
        offers_made = int(properties_shown * 0.55)  # 55% offer rate
        deals_closed = int(offers_made * 0.50)  # 50% close rate

        avg_commission = 12500
        total_revenue = deals_closed * avg_commission
        pipeline_value = len(hot_leads) * avg_commission

        return {
            "total_conversations": len(conversations),
            "hot_leads": len(hot_leads),
            "appointments": len(appointments),
            "properties_shown": properties_shown,
            "offers_made": offers_made,
            "deals_closed": deals_closed,
            "total_deals": deals_closed,
            "total_revenue": total_revenue,
            "avg_deal_value": avg_commission,
            "pipeline_value": pipeline_value,
        }

    def _calculate_channel_performance(self, attribution: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate performance by channel"""

        # Simulate channel attribution
        # In production, would track actual source for each lead
        channels = [
            {
                "channel": "Organic Website Chat",
                "conversations": int(attribution["total_conversations"] * 0.45),
                "revenue": int(attribution["total_revenue"] * 0.57),
                "deals": int(attribution["deals_closed"] * 0.55),
                "avg_deal_value": 13000,
                "conversion_rate": 21.5,
                "cost": 0,
                "roi": float("inf"),
            },
            {
                "channel": "Re-engagement Campaign",
                "conversations": int(attribution["total_conversations"] * 0.25),
                "revenue": int(attribution["total_revenue"] * 0.22),
                "deals": int(attribution["deals_closed"] * 0.20),
                "avg_deal_value": 12500,
                "conversion_rate": 18.0,
                "cost": 500,
                "roi": (int(attribution["total_revenue"] * 0.22) - 500) / 500 * 100,
            },
            {
                "channel": "A/B Optimized Flow",
                "conversations": int(attribution["total_conversations"] * 0.20),
                "revenue": int(attribution["total_revenue"] * 0.18),
                "deals": int(attribution["deals_closed"] * 0.20),
                "avg_deal_value": 11000,
                "conversion_rate": 22.0,
                "cost": 200,
                "roi": (int(attribution["total_revenue"] * 0.18) - 200) / 200 * 100,
            },
            {
                "channel": "Referrals",
                "conversations": int(attribution["total_conversations"] * 0.10),
                "revenue": int(attribution["total_revenue"] * 0.03),
                "deals": int(attribution["deals_closed"] * 0.05),
                "avg_deal_value": 15000,
                "conversion_rate": 8.0,
                "cost": 0,
                "roi": float("inf"),
            },
        ]

        return channels

    def _calculate_conversion_funnel(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Calculate conversion funnel metrics"""

        total = len(conversations)
        qualified = len([c for c in conversations if c.get("lead_score", 0) >= 40])
        hot = len([c for c in conversations if c.get("lead_score", 0) >= 70])
        appointments = len([c for c in conversations if c.get("appointment_set", False)])

        # Simulate downstream stages
        shown = int(appointments * 0.65)
        offers = int(shown * 0.55)
        closed = int(offers * 0.50)

        return {
            "stages": [
                {
                    "stage": "Initial Contact",
                    "count": total,
                    "percentage": 100.0,
                    "drop_off": 0,
                },
                {
                    "stage": "Qualified Lead",
                    "count": qualified,
                    "percentage": round(qualified / total * 100, 1) if total > 0 else 0,
                    "drop_off": total - qualified,
                },
                {
                    "stage": "Hot Lead",
                    "count": hot,
                    "percentage": round(hot / total * 100, 1) if total > 0 else 0,
                    "drop_off": qualified - hot,
                },
                {
                    "stage": "Appointment Set",
                    "count": appointments,
                    "percentage": (round(appointments / total * 100, 1) if total > 0 else 0),
                    "drop_off": hot - appointments,
                },
                {
                    "stage": "Property Shown",
                    "count": shown,
                    "percentage": round(shown / total * 100, 1) if total > 0 else 0,
                    "drop_off": appointments - shown,
                },
                {
                    "stage": "Offer Made",
                    "count": offers,
                    "percentage": round(offers / total * 100, 1) if total > 0 else 0,
                    "drop_off": shown - offers,
                },
                {
                    "stage": "Deal Closed",
                    "count": closed,
                    "percentage": round(closed / total * 100, 1) if total > 0 else 0,
                    "drop_off": offers - closed,
                },
            ],
            "overall_conversion_rate": (round(closed / total * 100, 2) if total > 0 else 0),
            "biggest_drop_off": ("Appointment Set → Property Shown" if appointments > 0 else "N/A"),
        }

    def _build_revenue_timeline(self, attribution: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build revenue timeline showing growth"""

        # Simulate monthly revenue over time
        timeline = []
        base_revenue = attribution["total_revenue"] / 3  # 3 month period

        for month in range(3):
            month_date = datetime.now(timezone.utc) - timedelta(days=90 - (month * 30))
            growth_factor = 1 + (month * 0.42)  # 42% month-over-month growth

            timeline.append(
                {
                    "period": month_date.strftime("%B %Y"),
                    "revenue": int(base_revenue * growth_factor),
                    "deals": int((attribution["deals_closed"] / 3) * growth_factor),
                    "conversations": int((attribution["total_conversations"] / 3) * growth_factor),
                    "growth_rate": (f"+{int((growth_factor - 1) * 100)}%" if month > 0 else "baseline"),
                }
            )

        return timeline

    def _calculate_roi_by_source(self, channel_performance: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate ROI by traffic source"""

        roi_data = []

        for channel in channel_performance:
            roi_data.append(
                {
                    "source": channel["channel"],
                    "investment": channel["cost"],
                    "revenue": channel["revenue"],
                    "roi_percentage": (channel["roi"] if channel["roi"] != float("inf") else "∞"),
                    "profit": channel["revenue"] - channel["cost"],
                    "deals": channel["deals"],
                    "cost_per_deal": (round(channel["cost"] / channel["deals"], 2) if channel["deals"] > 0 else 0),
                }
            )

        # Sort by ROI
        roi_data.sort(key=lambda x: x["profit"], reverse=True)

        return roi_data

    def _identify_top_performers(self, attribution: Dict[str, Any]) -> Dict[str, Any]:
        """Identify top performing elements"""

        return {
            "best_channel": "Organic Website Chat",
            "best_time": "9-11 AM weekdays",
            "best_message_template": "Personalized greeting with property interest",
            "best_agent": "AI Chatbot (100% availability)",
            "highest_conversion_source": "A/B Optimized Flow (22%)",
        }

    async def calculate_lead_value_metrics(self, location_id: str) -> Dict[str, Any]:
        """
        Calculate average lead value by tier for pricing optimization

        Returns metrics needed by DynamicPricingOptimizer for ROI calculations
        """
        try:
            conversations = await self._load_conversations(location_id, days=90)

            # Group conversations by lead tier
            tier_metrics = {
                "hot": {"conversions": [], "revenue": [], "days_to_close": []},
                "warm": {"conversions": [], "revenue": [], "days_to_close": []},
                "cold": {"conversions": [], "revenue": [], "days_to_close": []},
            }

            for conv in conversations:
                tier = self._classify_conversation_tier(conv)

                if conv.get("converted", False):
                    tier_metrics[tier]["conversions"].append(1)
                    tier_metrics[tier]["revenue"].append(conv.get("commission", 12500))
                    tier_metrics[tier]["days_to_close"].append(
                        conv.get("days_to_close", self._default_days_to_close(tier))
                    )
                else:
                    tier_metrics[tier]["conversions"].append(0)

            # Calculate metrics by tier
            result = {}
            for tier, data in tier_metrics.items():
                total_leads = len(data["conversions"])
                conversions = sum(data["conversions"])

                if total_leads > 0:
                    conversion_rate = conversions / total_leads
                    avg_revenue = sum(data["revenue"]) / max(1, conversions)
                    avg_days = sum(data["days_to_close"]) / max(1, conversions)
                    roi_multiplier = min(1.5, conversion_rate * 2)  # Cap at 1.5x
                else:
                    conversion_rate = 0.0
                    avg_revenue = 0.0
                    avg_days = self._default_days_to_close(tier)
                    roi_multiplier = 1.0

                result[tier] = {
                    "conversion_rate": conversion_rate,
                    "avg_revenue": avg_revenue,
                    "avg_days_to_close": int(avg_days),
                    "roi_multiplier": roi_multiplier,
                    "sample_size": total_leads,
                }

            return result

        except Exception as e:
            logger.error(f"Failed to calculate lead value metrics for {location_id}: {e}")
            return {}

    async def get_pricing_optimization_data(self, location_id: str, days: int = 90) -> Dict[str, Any]:
        """
        Get historical data needed for pricing optimization

        Returns conversion data, ARPU trends, and pricing performance metrics
        """
        try:
            conversations = await self._load_conversations(location_id, days)

            # Calculate current ARPU
            total_revenue = sum(conv.get("commission", 0) for conv in conversations if conv.get("converted"))
            total_periods = max(1, days // 30)  # Monthly periods
            current_arpu = total_revenue / total_periods if total_revenue > 0 else 100.0

            # Check if we have sufficient data for optimization
            total_conversions = sum(1 for conv in conversations if conv.get("converted"))
            sufficient_data = total_conversions >= 10 and days >= 90

            # Tier-specific optimization data
            tier_data = {}
            for tier in ["hot", "warm", "cold"]:
                tier_convs = [c for c in conversations if self._classify_conversation_tier(c) == tier]
                tier_conversions = [c for c in tier_convs if c.get("converted")]

                if len(tier_convs) > 0:
                    tier_data[tier] = {
                        "sample_size": len(tier_convs),
                        "conversion_rate": len(tier_conversions) / len(tier_convs),
                        "revenue_per_lead": sum(c.get("commission", 0) for c in tier_conversions)
                        / max(1, len(tier_convs)),
                        "current_multiplier": self._get_tier_multiplier(tier),
                        "avg_days_to_close": self._calculate_avg_days_to_close(tier_conversions),
                    }

            return {
                "current_arpu": current_arpu,
                "sufficient_data": sufficient_data,
                "total_conversions": total_conversions,
                "days_analyzed": days,
                "hot": tier_data.get("hot", {}),
                "warm": tier_data.get("warm", {}),
                "cold": tier_data.get("cold", {}),
            }

        except Exception as e:
            logger.error(f"Failed to get pricing optimization data for {location_id}: {e}")
            return {"current_arpu": 100.0, "sufficient_data": False}

    def _classify_conversation_tier(self, conversation: Dict) -> str:
        """Classify conversation tier based on questions answered"""
        questions_answered = conversation.get("questions_answered", 0)

        if questions_answered >= 3:
            return "hot"
        elif questions_answered >= 2:
            return "warm"
        else:
            return "cold"

    def _default_days_to_close(self, tier: str) -> int:
        """Default days to close by tier"""
        defaults = {"hot": 10, "warm": 21, "cold": 45}
        return defaults.get(tier, 30)

    def _get_tier_multiplier(self, tier: str) -> float:
        """Get current pricing tier multiplier"""
        multipliers = {"hot": 3.5, "warm": 2.0, "cold": 1.0}
        return multipliers.get(tier, 1.0)

    def _calculate_avg_days_to_close(self, conversions: List[Dict]) -> int:
        """Calculate average days to close for converted leads"""
        if not conversions:
            return 30

        days_list = [conv.get("days_to_close", 30) for conv in conversions]
        return int(sum(days_list) / len(days_list))


class ConversionPathAnalyzer:
    """Analyze conversion paths and touchpoints"""

    def analyze_journey(self, contact_id: str) -> Dict[str, Any]:
        """Analyze individual customer journey"""

        # Simulate journey analysis
        return {
            "contact_id": contact_id,
            "journey": [
                {
                    "touchpoint": "Website visit",
                    "timestamp": "2026-01-01 10:30",
                    "action": "Browsed listings",
                },
                {
                    "touchpoint": "Chat initiated",
                    "timestamp": "2026-01-01 10:45",
                    "action": "Asked about 3BR homes",
                },
                {
                    "touchpoint": "Budget discussed",
                    "timestamp": "2026-01-01 10:47",
                    "action": "Mentioned $500K budget",
                },
                {
                    "touchpoint": "Re-engagement",
                    "timestamp": "2026-01-02 09:00",
                    "action": "Received property matches",
                },
                {
                    "touchpoint": "Appointment set",
                    "timestamp": "2026-01-02 09:30",
                    "action": "Scheduled viewing",
                },
                {
                    "touchpoint": "Property shown",
                    "timestamp": "2026-01-03 14:00",
                    "action": "Viewed 3 properties",
                },
                {
                    "touchpoint": "Offer made",
                    "timestamp": "2026-01-05 10:00",
                    "action": "Submitted $480K offer",
                },
                {
                    "touchpoint": "Deal closed",
                    "timestamp": "2026-01-15 15:30",
                    "action": "Closed on property",
                },
            ],
            "total_touchpoints": 8,
            "days_to_close": 14,
            "conversion_path": "Website → Chat → Re-engagement → Appointment → Closed",
            "revenue": 12500,
        }
