"""
Campaign Performance Analytics (Phase 2 Enhancement)

Provides comprehensive campaign tracking, ROI analysis, and conversion funnel insights.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict
import statistics


class CampaignTracker:
    """
    Tracks campaigns across multiple channels and provides performance analytics.
    """
    
    def __init__(self, location_id: str):
        """
        Initialize campaign tracker for a specific GHL location.
        
        Args:
            location_id: GHL Location ID for multi-tenant support
        """
        self.location_id = location_id
        self.campaigns_dir = Path(__file__).parent.parent / "data" / "campaigns" / location_id
        self.campaigns_dir.mkdir(parents=True, exist_ok=True)
        self.campaigns_file = self.campaigns_dir / "campaigns.json"
        self.campaigns = self._load_campaigns()
    
    def _load_campaigns(self) -> Dict:
        """Load existing campaigns from file."""
        if self.campaigns_file.exists():
            with open(self.campaigns_file, 'r') as f:
                return json.load(f)
        return {
            "active": {},
            "completed": {},
            "archived": {}
        }
    
    def _save_campaigns(self):
        """Save campaigns to file."""
        with open(self.campaigns_file, 'w') as f:
            json.dump(self.campaigns, f, indent=2)
    
    def create_campaign(
        self,
        name: str,
        channel: str,
        budget: float,
        start_date: str,
        end_date: Optional[str] = None,
        target_metrics: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new marketing campaign.
        
        Args:
            name: Campaign name
            channel: Channel type (sms, email, social, paid_ads, organic)
            budget: Total budget allocated ($)
            start_date: Campaign start date (ISO format)
            end_date: Optional campaign end date (ISO format)
            target_metrics: Expected performance targets
            metadata: Additional campaign data
        
        Returns:
            campaign_id: Unique identifier for the campaign
        """
        import time
        # Use microseconds to ensure unique IDs
        campaign_id = f"camp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000000) % 1000000}"
        
        campaign = {
            "id": campaign_id,
            "name": name,
            "channel": channel,
            "location_id": self.location_id,
            "budget": budget,
            "start_date": start_date,
            "end_date": end_date,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "target_metrics": target_metrics or {
                "target_leads": 100,
                "target_conversions": 10,
                "target_roi": 3.0
            },
            "metadata": metadata or {},
            "performance": {
                "impressions": 0,
                "clicks": 0,
                "leads_generated": 0,
                "qualified_leads": 0,
                "hot_leads": 0,
                "appointments_booked": 0,
                "conversions": 0,
                "revenue_generated": 0.0,
                "cost_per_lead": 0.0,
                "cost_per_conversion": 0.0,
                "roi": 0.0,
                "conversion_rate": 0.0
            },
            "daily_metrics": [],
            "funnel_data": {
                "awareness": 0,
                "interest": 0,
                "consideration": 0,
                "intent": 0,
                "conversion": 0
            }
        }
        
        self.campaigns["active"][campaign_id] = campaign
        self._save_campaigns()
        
        return campaign_id
    
    def update_campaign_metrics(
        self,
        campaign_id: str,
        metrics: Dict[str, Any],
        date: Optional[str] = None
    ):
        """
        Update campaign performance metrics.
        
        Args:
            campaign_id: Campaign identifier
            metrics: Dictionary of metric updates
            date: Date for daily tracking (defaults to today)
        """
        if campaign_id not in self.campaigns["active"]:
            return
        
        campaign = self.campaigns["active"][campaign_id]
        perf = campaign["performance"]
        
        # Update aggregate metrics
        for key, value in metrics.items():
            if key in perf:
                if isinstance(value, (int, float)):
                    perf[key] += value
                else:
                    perf[key] = value
        
        # Calculate derived metrics
        if perf["leads_generated"] > 0:
            perf["cost_per_lead"] = campaign["budget"] / perf["leads_generated"]
        
        if perf["conversions"] > 0:
            perf["cost_per_conversion"] = campaign["budget"] / perf["conversions"]
        
        if perf["revenue_generated"] > 0:
            perf["roi"] = (perf["revenue_generated"] - campaign["budget"]) / campaign["budget"]
        
        if perf["leads_generated"] > 0:
            perf["conversion_rate"] = perf["conversions"] / perf["leads_generated"]
        
        # Track daily metrics
        daily_entry = {
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "metrics": metrics.copy(),
            "cumulative": perf.copy()
        }
        campaign["daily_metrics"].append(daily_entry)
        
        self._save_campaigns()
    
    def update_funnel_stage(
        self,
        campaign_id: str,
        stage: str,
        count: int = 1
    ):
        """
        Update conversion funnel data.
        
        Args:
            campaign_id: Campaign identifier
            stage: Funnel stage (awareness, interest, consideration, intent, conversion)
            count: Number to add to stage
        """
        if campaign_id not in self.campaigns["active"]:
            return
        
        campaign = self.campaigns["active"][campaign_id]
        funnel = campaign["funnel_data"]
        
        if stage in funnel:
            funnel[stage] += count
            self._save_campaigns()
    
    def get_campaign_performance(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get comprehensive performance report for a campaign.
        
        Returns:
            {
                "campaign_info": {...},
                "performance": {...},
                "roi_analysis": {...},
                "funnel_metrics": {...},
                "trend_data": [...]
            }
        """
        campaign = None
        for status in ["active", "completed", "archived"]:
            if campaign_id in self.campaigns[status]:
                campaign = self.campaigns[status][campaign_id]
                break
        
        if not campaign:
            return {"error": "Campaign not found"}
        
        perf = campaign["performance"]
        funnel = campaign["funnel_data"]
        
        # Calculate funnel conversion rates
        funnel_rates = {}
        stages = ["awareness", "interest", "consideration", "intent", "conversion"]
        for i in range(len(stages) - 1):
            current = funnel[stages[i]]
            next_stage = funnel[stages[i + 1]]
            if current > 0:
                funnel_rates[f"{stages[i]}_to_{stages[i+1]}"] = (next_stage / current) * 100
            else:
                funnel_rates[f"{stages[i]}_to_{stages[i+1]}"] = 0.0
        
        # Calculate overall funnel efficiency
        overall_efficiency = 0.0
        if funnel["awareness"] > 0:
            overall_efficiency = (funnel["conversion"] / funnel["awareness"]) * 100
        
        # ROI analysis
        roi_analysis = {
            "total_spent": campaign["budget"],
            "revenue_generated": perf["revenue_generated"],
            "net_profit": perf["revenue_generated"] - campaign["budget"],
            "roi_percentage": perf["roi"] * 100,
            "break_even_point": campaign["budget"],
            "profit_margin": ((perf["revenue_generated"] - campaign["budget"]) / perf["revenue_generated"] * 100) if perf["revenue_generated"] > 0 else 0
        }
        
        # Target comparison
        targets = campaign["target_metrics"]
        target_comparison = {
            "leads_vs_target": {
                "actual": perf["leads_generated"],
                "target": targets.get("target_leads", 0),
                "achievement_rate": (perf["leads_generated"] / targets.get("target_leads", 1)) * 100
            },
            "conversions_vs_target": {
                "actual": perf["conversions"],
                "target": targets.get("target_conversions", 0),
                "achievement_rate": (perf["conversions"] / targets.get("target_conversions", 1)) * 100
            },
            "roi_vs_target": {
                "actual": perf["roi"],
                "target": targets.get("target_roi", 0),
                "achievement_rate": (perf["roi"] / targets.get("target_roi", 1)) * 100 if targets.get("target_roi", 0) > 0 else 0
            }
        }
        
        return {
            "campaign_info": {
                "id": campaign["id"],
                "name": campaign["name"],
                "channel": campaign["channel"],
                "status": campaign["status"],
                "start_date": campaign["start_date"],
                "end_date": campaign["end_date"],
                "budget": campaign["budget"]
            },
            "performance": perf,
            "roi_analysis": roi_analysis,
            "funnel_metrics": {
                "stages": funnel,
                "conversion_rates": funnel_rates,
                "overall_efficiency": overall_efficiency
            },
            "target_comparison": target_comparison,
            "trend_data": campaign["daily_metrics"]
        }
    
    def compare_campaigns(self, campaign_ids: List[str]) -> Dict[str, Any]:
        """
        Compare performance across multiple campaigns.
        
        Args:
            campaign_ids: List of campaign IDs to compare
        
        Returns:
            Comparative analysis with rankings and recommendations
        """

        # ALGORITHM: Multi-Campaign Comparison
        # 1. Fetch metrics for all specified campaigns
        # 2. Normalize metrics to same time period
        # 3. Calculate percentage differences
        # 4. Rank campaigns by performance score
        # 5. Generate comparative insights
        
        # Performance Score = (conversion_rate * 0.4) + (engagement_rate * 0.3) + (roi * 0.3)

        campaigns_data = []
        
        for camp_id in campaign_ids:
            perf_data = self.get_campaign_performance(camp_id)
            if "error" not in perf_data:
                campaigns_data.append(perf_data)
        
        if not campaigns_data:
            return {"error": "No valid campaigns found", "rankings": {"by_roi": []}}
        
        # Rank by different metrics
        rankings = {
            "roi": sorted(campaigns_data, key=lambda x: x["performance"]["roi"], reverse=True),
            "conversion_rate": sorted(campaigns_data, key=lambda x: x["performance"]["conversion_rate"], reverse=True),
            "cost_per_lead": sorted(campaigns_data, key=lambda x: x["performance"]["cost_per_lead"] or float('inf')),
            "leads_generated": sorted(campaigns_data, key=lambda x: x["performance"]["leads_generated"], reverse=True)
        }
        
        # Calculate channel performance
        channel_stats = defaultdict(lambda: {
            "campaigns": 0,
            "total_budget": 0,
            "total_leads": 0,
            "total_conversions": 0,
            "total_revenue": 0,
            "avg_roi": []
        })
        
        for camp in campaigns_data:
            channel = camp["campaign_info"]["channel"]
            channel_stats[channel]["campaigns"] += 1
            channel_stats[channel]["total_budget"] += camp["campaign_info"]["budget"]
            channel_stats[channel]["total_leads"] += camp["performance"]["leads_generated"]
            channel_stats[channel]["total_conversions"] += camp["performance"]["conversions"]
            channel_stats[channel]["total_revenue"] += camp["performance"]["revenue_generated"]
            channel_stats[channel]["avg_roi"].append(camp["performance"]["roi"])
        
        # Calculate averages
        for channel, stats in channel_stats.items():
            if stats["avg_roi"]:
                stats["avg_roi"] = statistics.mean(stats["avg_roi"])
            else:
                stats["avg_roi"] = 0.0
            
            if stats["total_leads"] > 0:
                stats["cost_per_lead"] = stats["total_budget"] / stats["total_leads"]
            else:
                stats["cost_per_lead"] = 0.0
        
        # Generate recommendations
        recommendations = []
        
        # Best performing campaign
        best_roi_campaign = rankings["roi"][0]
        recommendations.append({
            "type": "best_performer",
            "priority": "high",
            "message": f"Campaign '{best_roi_campaign['campaign_info']['name']}' has the highest ROI at {best_roi_campaign['performance']['roi']*100:.1f}%. Consider scaling this approach.",
            "action": "increase_budget"
        })
        
        # Underperforming campaigns
        for camp in campaigns_data:
            if camp["performance"]["roi"] < 0:
                recommendations.append({
                    "type": "underperformer",
                    "priority": "critical",
                    "message": f"Campaign '{camp['campaign_info']['name']}' has negative ROI. Review targeting and messaging.",
                    "action": "optimize_or_pause"
                })
        
        # Channel recommendations
        best_channel = max(channel_stats.items(), key=lambda x: x[1]["avg_roi"])
        recommendations.append({
            "type": "channel_optimization",
            "priority": "medium",
            "message": f"{best_channel[0].title()} channel has the best average ROI. Consider reallocating budget from lower-performing channels.",
            "action": "reallocate_budget"
        })
        
        return {
            "campaigns_compared": len(campaigns_data),
            "rankings": {
                "by_roi": [{"name": c["campaign_info"]["name"], "value": c["performance"]["roi"]} for c in rankings["roi"][:5]],
                "by_conversion_rate": [{"name": c["campaign_info"]["name"], "value": c["performance"]["conversion_rate"]} for c in rankings["conversion_rate"][:5]],
                "by_cost_efficiency": [{"name": c["campaign_info"]["name"], "value": c["performance"]["cost_per_lead"]} for c in rankings["cost_per_lead"][:5]]
            },
            "channel_performance": dict(channel_stats),
            "recommendations": recommendations,
            "summary_stats": {
                "total_budget": sum(c["campaign_info"]["budget"] for c in campaigns_data),
                "total_leads": sum(c["performance"]["leads_generated"] for c in campaigns_data),
                "total_revenue": sum(c["performance"]["revenue_generated"] for c in campaigns_data),
                "avg_roi": statistics.mean([c["performance"]["roi"] for c in campaigns_data]),
                "avg_conversion_rate": statistics.mean([c["performance"]["conversion_rate"] for c in campaigns_data])
            }
        }
    
    def get_channel_analytics(self) -> Dict[str, Any]:
        """
        Get performance analytics grouped by channel.
        
        Returns:
            Channel-level performance metrics and trends
        """
        all_campaigns = []
        for status in ["active", "completed"]:
            all_campaigns.extend(self.campaigns[status].values())
        
        channel_data = defaultdict(lambda: {
            "campaigns": [],
            "total_budget": 0,
            "total_leads": 0,
            "total_conversions": 0,
            "total_revenue": 0,
            "avg_cpl": 0,
            "avg_roi": 0
        })
        
        for camp in all_campaigns:
            channel = camp["channel"]
            perf = camp["performance"]
            
            channel_data[channel]["campaigns"].append(camp["name"])
            channel_data[channel]["total_budget"] += camp["budget"]
            channel_data[channel]["total_leads"] += perf["leads_generated"]
            channel_data[channel]["total_conversions"] += perf["conversions"]
            channel_data[channel]["total_revenue"] += perf["revenue_generated"]
        
        # Calculate averages
        for channel, data in channel_data.items():
            if data["total_leads"] > 0:
                data["avg_cpl"] = data["total_budget"] / data["total_leads"]
            if data["total_budget"] > 0:
                data["avg_roi"] = (data["total_revenue"] - data["total_budget"]) / data["total_budget"]
            data["campaign_count"] = len(data["campaigns"])
            data["campaigns"] = data["campaigns"][:5]  # Limit to top 5 for display
        
        return dict(channel_data)
    
    def complete_campaign(self, campaign_id: str):
        """Mark a campaign as completed."""
        if campaign_id in self.campaigns["active"]:
            campaign = self.campaigns["active"].pop(campaign_id)
            campaign["status"] = "completed"
            campaign["completed_at"] = datetime.now().isoformat()
            self.campaigns["completed"][campaign_id] = campaign
            self._save_campaigns()
    
    def list_active_campaigns(self) -> List[Dict]:
        """List all active campaigns for this location."""
        return [
            {
                "id": camp_id,
                "name": camp["name"],
                "channel": camp["channel"],
                "budget": camp["budget"],
                "start_date": camp["start_date"],
                "leads_generated": camp["performance"]["leads_generated"],
                "roi": camp["performance"]["roi"]
            }
            for camp_id, camp in self.campaigns["active"].items()
        ]


if __name__ == "__main__":
    # Demo usage
    print("Campaign Performance Analytics Demo\n")
    print("=" * 70)
    
    tracker = CampaignTracker("demo_location")
    
    # Create sample campaigns
    camp1 = tracker.create_campaign(
        name="Spring SMS Campaign",
        channel="sms",
        budget=5000.0,
        start_date="2026-01-01",
        target_metrics={
            "target_leads": 150,
            "target_conversions": 15,
            "target_roi": 2.5
        }
    )
    
    # Simulate performance
    tracker.update_campaign_metrics(camp1, {
        "impressions": 10000,
        "clicks": 500,
        "leads_generated": 120,
        "qualified_leads": 80,
        "hot_leads": 30,
        "conversions": 12,
        "revenue_generated": 18000.0
    })
    
    # Update funnel
    tracker.update_funnel_stage(camp1, "awareness", 10000)
    tracker.update_funnel_stage(camp1, "interest", 500)
    tracker.update_funnel_stage(camp1, "consideration", 120)
    tracker.update_funnel_stage(camp1, "intent", 30)
    tracker.update_funnel_stage(camp1, "conversion", 12)
    
    # Get performance report
    report = tracker.get_campaign_performance(camp1)
    
    print(f"Campaign: {report['campaign_info']['name']}")
    print(f"Channel: {report['campaign_info']['channel']}")
    print(f"\nPerformance:")
    print(f"  Leads: {report['performance']['leads_generated']}")
    print(f"  Conversions: {report['performance']['conversions']}")
    print(f"  ROI: {report['roi_analysis']['roi_percentage']:.1f}%")
    print(f"  Cost per Lead: ${report['performance']['cost_per_lead']:.2f}")
    print(f"\nFunnel Efficiency: {report['funnel_metrics']['overall_efficiency']:.1f}%")
    print("=" * 70)
