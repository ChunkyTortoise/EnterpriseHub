"""
Executive Dashboard Service

Provides KPI calculations and executive-level insights
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import json


class ExecutiveDashboardService:
    """Generate executive-level KPIs and insights"""
    
    def __init__(self, data_dir: Path = None):
        """
        Execute init operation.

        Args:
            data_dir: Data to process
        """
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"
        
    def get_executive_summary(
        self, 
        location_id: str, 
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get executive summary with key metrics
        
        Args:
            location_id: GHL location ID
            days: Number of days to analyze
            
        Returns:
            Executive summary with KPIs and trends
        """
        # Load conversation data
        conversations = self._load_conversations(location_id, days)
        
        # Calculate metrics
        metrics = self._calculate_metrics(conversations, days)
        
        # Generate insights
        insights = self._generate_insights(metrics)
        
        # Identify action items
        action_items = self._identify_action_items(metrics, conversations)
        
        from datetime import timezone
        now = datetime.now(timezone.utc)
        return {
            "period": {
                "days": days,
                "start_date": (now - timedelta(days=days)).isoformat(),
                "end_date": now.isoformat()
            },
            "metrics": metrics,
            "insights": insights,
            "action_items": action_items,
            "trends": self._calculate_trends(conversations, days)
        }
    
    def _load_conversations(self, location_id: str, days: int) -> List[Dict]:
        """Load conversation data for analysis"""
        from datetime import timezone
        # Load from analytics data
        analytics_file = self.data_dir / "mock_analytics.json"
        
        if not analytics_file.exists():
            return []
            
        with open(analytics_file) as f:
            data = json.load(f)
            
        # Filter by date range
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        conversations = []
        for c in data.get("conversations", []):
            ts_str = c.get("timestamp") or c.get("start_time")
            if ts_str:
                try:
                    # Handle Z or +00:00 and make it offset-aware
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    
                    if ts >= cutoff:
                        conversations.append(c)
                except ValueError:
                    continue
        
        return conversations
    
    def _calculate_metrics(self, conversations: List[Dict], days: int) -> Dict[str, Any]:
        """Calculate executive KPIs"""
        total_convos = len(conversations)
        
        # Lead quality metrics
        hot_leads = [c for c in conversations if c.get("lead_score", 0) >= 70]
        warm_leads = [c for c in conversations if 40 <= c.get("lead_score", 0) < 70]
        cold_leads = [c for c in conversations if c.get("lead_score", 0) < 40]
        
        # Response time metrics
        response_times = [c.get("response_time_minutes", 0) for c in conversations]
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        # Conversion metrics
        appointments = [c for c in conversations if c.get("appointment_set", False)]
        conversion_rate = (len(appointments) / total_convos * 100) if total_convos > 0 else 0
        
        # Pipeline value (assuming $12,500 avg commission per hot lead)
        pipeline_value = len(hot_leads) * 12500
        
        return {
            "conversations": {
                "total": total_convos,
                "daily_average": total_convos / days if days > 0 else 0,
                "change_vs_previous": self._calculate_change(total_convos, days)
            },
            "lead_quality": {
                "hot_leads": len(hot_leads),
                "warm_leads": len(warm_leads),
                "cold_leads": len(cold_leads),
                "hot_percentage": (len(hot_leads) / total_convos * 100) if total_convos > 0 else 0
            },
            "response_time": {
                "average_minutes": round(avg_response, 1),
                "target_minutes": 2.0,
                "meeting_target": avg_response <= 2.0,
                "fastest_response": min(response_times) if response_times else 0
            },
            "conversion": {
                "appointments_set": len(appointments),
                "conversion_rate": round(conversion_rate, 1),
                "target_rate": 20.0,
                "meeting_target": conversion_rate >= 20.0
            },
            "pipeline": {
                "value": pipeline_value,
                "currency": "USD",
                "hot_lead_value": 12500
            }
        }
    
    def _calculate_change(self, current_value: int, days: int) -> float:
        """Calculate percentage change vs previous period"""
        # Simulate previous period comparison
        # In production, would load actual previous period data
        previous_value = int(current_value * 0.85)  # Simulate 15% growth
        
        if previous_value == 0:
            return 0.0
            
        change = ((current_value - previous_value) / previous_value) * 100
        return round(change, 1)
    
    def _generate_insights(self, metrics: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate executive insights from metrics"""
        insights = []
        
        # Response time insight
        if metrics["response_time"]["meeting_target"]:
            insights.append({
                "type": "success",
                "title": "Response Time Excellence",
                "message": f"Average response time of {metrics['response_time']['average_minutes']} minutes beats target"
            })
        else:
            insights.append({
                "type": "warning",
                "title": "Response Time Needs Attention",
                "message": f"Current {metrics['response_time']['average_minutes']}min vs {metrics['response_time']['target_minutes']}min target"
            })
        
        # Conversion insight
        if metrics["conversion"]["meeting_target"]:
            insights.append({
                "type": "success",
                "title": "Conversion Target Achieved",
                "message": f"{metrics['conversion']['conversion_rate']}% conversion rate exceeds {metrics['conversion']['target_rate']}% goal"
            })
        else:
            gap = metrics["conversion"]["target_rate"] - metrics["conversion"]["conversion_rate"]
            insights.append({
                "type": "opportunity",
                "title": "Conversion Opportunity",
                "message": f"Need {gap:.1f}% improvement to hit target. Focus on hot lead follow-up."
            })
        
        # Lead quality insight
        hot_pct = metrics["lead_quality"]["hot_percentage"]
        if hot_pct > 20:
            insights.append({
                "type": "success",
                "title": "High-Quality Lead Generation",
                "message": f"{hot_pct:.1f}% hot leads - excellent qualification"
            })
        
        # Pipeline insight
        pipeline_value = metrics["pipeline"]["value"]
        insights.append({
            "type": "info",
            "title": "Pipeline Value",
            "message": f"${pipeline_value:,} in potential commissions from hot leads"
        })
        
        return insights
    
    def _identify_action_items(
        self, 
        metrics: Dict[str, Any], 
        conversations: List[Dict]
    ) -> List[Dict[str, str]]:
        """Identify executive action items"""
        action_items = []
        
        # Hot leads waiting for follow-up
        hot_leads_pending = [
            c for c in conversations 
            if c.get("lead_score", 0) >= 70 and not c.get("appointment_set", False)
        ]
        
        if hot_leads_pending:
            action_items.append({
                "priority": "high",
                "title": f"{len(hot_leads_pending)} hot leads need follow-up",
                "action": "Review and schedule appointments today",
                "impact": f"Potential ${len(hot_leads_pending) * 12500:,} in pipeline"
            })
        
        # Response time issue
        if not metrics["response_time"]["meeting_target"]:
            action_items.append({
                "priority": "medium",
                "title": "Response time above target",
                "action": "Review staffing during peak hours",
                "impact": "Faster response = higher conversion"
            })
        
        # Conversion rate gap
        if not metrics["conversion"]["meeting_target"]:
            gap = metrics["conversion"]["target_rate"] - metrics["conversion"]["conversion_rate"]
            potential_leads = int((gap / 100) * metrics["conversations"]["total"])
            action_items.append({
                "priority": "medium",
                "title": f"Conversion rate {gap:.1f}% below target",
                "action": "A/B test new qualification questions",
                "impact": f"Could add {potential_leads} appointments/week"
            })
        
        return action_items
    
    def _calculate_trends(self, conversations: List[Dict], days: int) -> Dict[str, List[Dict]]:
        """Calculate day-by-day trends"""
        from datetime import timezone
        # Group conversations by day
        daily_data = {}
        
        for conv in conversations:
            ts_str = conv.get("timestamp") or conv.get("start_time")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    
                    date = ts.date()
                    if date not in daily_data:
                        daily_data[date] = []
                    daily_data[date].append(conv)
                except ValueError:
                    continue
        
        # Calculate daily metrics
        trend_data = []
        for date in sorted(daily_data.keys()):
            day_convos = daily_data[date]
            hot_leads = [c for c in day_convos if c.get("lead_score", 0) >= 70]
            
            trend_data.append({
                "date": date.isoformat(),
                "conversations": len(day_convos),
                "hot_leads": len(hot_leads),
                "conversion_rate": (len([c for c in day_convos if c.get("appointment_set", False)]) / len(day_convos) * 100) if day_convos else 0
            })
        
        return {
            "daily": trend_data
        }


def calculate_roi(
    system_cost_monthly: float = 170.0,
    conversations_per_month: int = 300,
    conversion_rate: float = 0.196,
    avg_commission: float = 12500.0
) -> Dict[str, Any]:
    """
    Calculate ROI for executive reporting
    
    Args:
        system_cost_monthly: Monthly cost of system
        conversations_per_month: Number of conversations
        conversion_rate: Percentage that convert to appointments
        avg_commission: Average commission per deal
        
    Returns:
        ROI calculation breakdown
    """
    appointments = int(conversations_per_month * conversion_rate)
    # Assume 50% of appointments lead to closed deals
    deals_closed = int(appointments * 0.5)
    revenue = deals_closed * avg_commission
    
    roi_percentage = ((revenue - system_cost_monthly) / system_cost_monthly) * 100
    payback_days = (system_cost_monthly / (revenue / 30)) if revenue > 0 else 0
    
    return {
        "investment": {
            "monthly_cost": system_cost_monthly,
            "annual_cost": system_cost_monthly * 12
        },
        "results": {
            "conversations": conversations_per_month,
            "appointments": appointments,
            "deals_closed": deals_closed,
            "revenue_generated": revenue
        },
        "roi": {
            "percentage": round(roi_percentage, 1),
            "payback_days": round(payback_days, 1),
            "net_profit_monthly": revenue - system_cost_monthly,
            "net_profit_annual": (revenue * 12) - (system_cost_monthly * 12)
        }
    }
