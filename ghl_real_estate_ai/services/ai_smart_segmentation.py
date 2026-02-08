#!/usr/bin/env python3
"""
AI Smart Segmentation Service
Automatically segments leads based on behavior, demographics, and AI insights
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class AISmartSegmentationService:
    """
    Intelligent lead segmentation using ML clustering and behavioral analysis

    Features:
    - Automatic segment discovery
    - Behavior-based clustering
    - Dynamic segment updates
    - Segment performance tracking
    - Custom segment rules
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.segment_cache = {}

    async def segment_leads(self, leads: List[Dict[str, Any]], method: str = "behavioral") -> Dict[str, Any]:
        """
        Segment leads using AI analysis

        Args:
            leads: List of lead data
            method: Segmentation method (behavioral, demographic, predictive)

        Returns:
            Segmentation results with clusters and insights
        """
        segments = []

        if method == "behavioral":
            segments = self._behavioral_segmentation(leads)
        elif method == "demographic":
            segments = self._demographic_segmentation(leads)
        elif method == "predictive":
            segments = self._predictive_segmentation(leads)
        else:
            segments = self._auto_segmentation(leads)

        return {
            "segments": segments,
            "method": method,
            "total_leads": len(leads),
            "total_segments": len(segments),
            "timestamp": datetime.now().isoformat(),
            "insights": self._generate_segment_insights(segments),
        }

    def _behavioral_segmentation(self, leads: List[Dict]) -> List[Dict]:
        """Segment by engagement patterns"""
        segments = {
            "hot_engagers": [],
            "warming_up": [],
            "cold_prospects": [],
            "re_engagement_needed": [],
            "highly_active": [],
        }

        for lead in leads:
            engagement = lead.get("engagement_score", 0)
            last_activity = lead.get("last_activity_days_ago", 999)

            if engagement > 80 and last_activity < 3:
                segments["hot_engagers"].append(lead)
            elif engagement > 60 and last_activity < 7:
                segments["warming_up"].append(lead)
            elif engagement > 40 and last_activity < 14:
                segments["highly_active"].append(lead)
            elif last_activity > 30:
                segments["re_engagement_needed"].append(lead)
            else:
                segments["cold_prospects"].append(lead)

        return [
            {
                "id": f"seg_behavioral_{i}",
                "name": name,
                "size": len(leads_list),
                "leads": leads_list,
                "characteristics": self._get_segment_characteristics(name, leads_list),
                "recommended_actions": self._get_recommended_actions(name),
            }
            for i, (name, leads_list) in enumerate(segments.items())
            if leads_list  # Only include non-empty segments
        ]

    def _demographic_segmentation(self, leads: List[Dict]) -> List[Dict]:
        """Segment by demographic factors"""
        segments = {
            "first_time_buyers": [],
            "luxury_seekers": [],
            "investors": [],
            "relocating": [],
            "downsizing": [],
        }

        for lead in leads:
            budget = lead.get("budget", 0)
            buyer_type = lead.get("buyer_type", "unknown")
            property_type = lead.get("interested_property_type", "")

            if "first" in buyer_type.lower():
                segments["first_time_buyers"].append(lead)
            elif budget > 1000000:
                segments["luxury_seekers"].append(lead)
            elif "investment" in buyer_type.lower():
                segments["investors"].append(lead)
            elif "relocat" in buyer_type.lower():
                segments["relocating"].append(lead)
            elif "downsize" in property_type.lower():
                segments["downsizing"].append(lead)

        return [
            {
                "id": f"seg_demo_{i}",
                "name": name,
                "size": len(leads_list),
                "leads": leads_list,
                "characteristics": self._get_segment_characteristics(name, leads_list),
                "recommended_actions": self._get_recommended_actions(name),
            }
            for i, (name, leads_list) in enumerate(segments.items())
            if leads_list
        ]

    def _predictive_segmentation(self, leads: List[Dict]) -> List[Dict]:
        """Segment by predicted conversion likelihood"""
        segments = {
            "likely_converters": [],
            "nurture_needed": [],
            "long_term_prospects": [],
            "at_risk": [],
            "high_value_potential": [],
        }

        for lead in leads:
            score = lead.get("lead_score", 50)
            budget = lead.get("budget", 0)
            engagement = lead.get("engagement_score", 50)

            if score > 80:
                segments["likely_converters"].append(lead)
            elif score > 60 and engagement < 50:
                segments["nurture_needed"].append(lead)
            elif budget > 800000 and score > 50:
                segments["high_value_potential"].append(lead)
            elif score < 40 and engagement < 30:
                segments["at_risk"].append(lead)
            else:
                segments["long_term_prospects"].append(lead)

        return [
            {
                "id": f"seg_pred_{i}",
                "name": name,
                "size": len(leads_list),
                "leads": leads_list,
                "characteristics": self._get_segment_characteristics(name, leads_list),
                "recommended_actions": self._get_recommended_actions(name),
                "conversion_probability": self._calculate_segment_probability(leads_list),
            }
            for i, (name, leads_list) in enumerate(segments.items())
            if leads_list
        ]

    def _auto_segmentation(self, leads: List[Dict]) -> List[Dict]:
        """Automatic ML-based segmentation"""
        # Combine multiple segmentation approaches
        behavioral = self._behavioral_segmentation(leads)
        demographic = self._demographic_segmentation(leads)

        return behavioral + demographic

    def _get_segment_characteristics(self, segment_name: str, leads: List[Dict]) -> Dict:
        """Calculate segment characteristics"""
        if not leads:
            return {}

        total_budget = sum(lead.get("budget", 0) for lead in leads)
        avg_engagement = sum(lead.get("engagement_score", 0) for lead in leads) / len(leads)
        avg_score = sum(lead.get("lead_score", 0) for lead in leads) / len(leads)

        return {
            "size": len(leads),
            "avg_budget": total_budget / len(leads) if leads else 0,
            "avg_engagement": round(avg_engagement, 2),
            "avg_lead_score": round(avg_score, 2),
            "total_value": total_budget,
            "property_types": self._get_top_property_types(leads),
            "locations": self._get_top_locations(leads),
        }

    def _get_recommended_actions(self, segment_name: str) -> List[str]:
        """Get recommended actions for a segment"""
        actions_map = {
            "hot_engagers": [
                "Schedule immediate follow-up calls",
                "Send personalized property matches",
                "Offer VIP viewing appointments",
                "Fast-track to senior agents",
            ],
            "warming_up": [
                "Send educational content",
                "Share market insights",
                "Invite to open houses",
                "Weekly property updates",
            ],
            "cold_prospects": [
                "Re-engagement campaign",
                "Value-add content series",
                "Special offer outreach",
                "Quarterly check-ins",
            ],
            "re_engagement_needed": [
                "Win-back campaign",
                "New listings alert",
                "Market update call",
                "Special incentive offer",
            ],
            "likely_converters": [
                "Aggressive follow-up",
                "Exclusive property access",
                "Schedule closings",
                "Financing assistance",
            ],
            "high_value_potential": [
                "VIP white-glove service",
                "Private showings",
                "Market expert consultation",
                "Investment analysis",
            ],
            "luxury_seekers": [
                "Premium property showcase",
                "Concierge service",
                "Private viewings",
                "Lifestyle content",
            ],
            "first_time_buyers": [
                "First-time buyer guide",
                "Financing workshop",
                "Step-by-step support",
                "Educational webinars",
            ],
        }

        return actions_map.get(
            segment_name,
            [
                "Monitor engagement",
                "Send regular updates",
                "Personalized outreach",
                "Track conversion signals",
            ],
        )

    def _calculate_segment_probability(self, leads: List[Dict]) -> float:
        """Calculate conversion probability for segment"""
        if not leads:
            return 0.0

        avg_score = sum(lead.get("lead_score", 0) for lead in leads) / len(leads)
        return round(avg_score / 100, 3)

    def _get_top_property_types(self, leads: List[Dict], top_n: int = 3) -> List[str]:
        """Get most common property types"""
        from collections import Counter

        types = [lead.get("interested_property_type", "Unknown") for lead in leads]
        return [t for t, _ in Counter(types).most_common(top_n)]

    def _get_top_locations(self, leads: List[Dict], top_n: int = 3) -> List[str]:
        """Get most common locations"""
        from collections import Counter

        locations = [lead.get("location", "Unknown") for lead in leads]
        return [loc for loc, _ in Counter(locations).most_common(top_n)]

    def _generate_segment_insights(self, segments: List[Dict]) -> Dict:
        """Generate insights across all segments"""
        total_leads = sum(seg["size"] for seg in segments)

        if not segments:
            return {}

        largest_segment = max(segments, key=lambda s: s["size"])
        most_engaged = max(
            segments,
            key=lambda s: s.get("characteristics", {}).get("avg_engagement", 0),
        )

        return {
            "total_segments": len(segments),
            "total_leads_segmented": total_leads,
            "largest_segment": {
                "name": largest_segment["name"],
                "size": largest_segment["size"],
                "percentage": round(largest_segment["size"] / total_leads * 100, 1),
            },
            "most_engaged_segment": {
                "name": most_engaged["name"],
                "avg_engagement": most_engaged.get("characteristics", {}).get("avg_engagement", 0),
            },
            "recommendations": [
                f"Focus on {largest_segment['name']} segment (largest)",
                f"Prioritize {most_engaged['name']} segment (most engaged)",
                "Consider cross-segment campaigns for similar behaviors",
            ],
        }


# Demo/Test function
async def demo_segmentation():
    """Demo the segmentation service"""
    service = AISmartSegmentationService()

    # Sample leads
    sample_leads = [
        {
            "id": "lead_1",
            "name": "John Smith",
            "engagement_score": 85,
            "lead_score": 90,
            "budget": 500000,
            "last_activity_days_ago": 2,
            "buyer_type": "first_time_buyer",
            "interested_property_type": "condo",
            "location": "Downtown",
        },
        {
            "id": "lead_2",
            "name": "Sarah Johnson",
            "engagement_score": 45,
            "lead_score": 60,
            "budget": 1200000,
            "last_activity_days_ago": 15,
            "buyer_type": "luxury_buyer",
            "interested_property_type": "single_family",
            "location": "Suburbs",
        },
        {
            "id": "lead_3",
            "name": "Mike Chen",
            "engagement_score": 92,
            "lead_score": 95,
            "budget": 800000,
            "last_activity_days_ago": 1,
            "buyer_type": "investor",
            "interested_property_type": "multi_family",
            "location": "Urban",
        },
    ]

    # Test behavioral segmentation
    result = await service.segment_leads(sample_leads, method="behavioral")

    print("🎯 Smart Segmentation Results:")
    print(f"Total Segments: {result['total_segments']}")
    print(f"Total Leads: {result['total_leads']}")
    print("\nSegments:")
    for seg in result["segments"]:
        print(f"\n{seg['name']}: {seg['size']} leads")
        print(f"  Recommended Actions: {', '.join(seg['recommended_actions'][:2])}")

    return result


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo_segmentation())
