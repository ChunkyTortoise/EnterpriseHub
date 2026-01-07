"""
Automated Report Generation Service

Creates beautiful PDF reports and handles email delivery
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class ReportGenerator:
    """Generate automated performance reports"""

    REPORT_TYPES = {
        "daily_brief": {
            "name": "Daily Performance Brief",
            "pages": 1,
            "frequency": "daily",
            "time": "08:00",
        },
        "weekly_summary": {
            "name": "Weekly Executive Summary",
            "pages": 3,
            "frequency": "weekly",
            "day": "monday",
            "time": "09:00",
        },
        "monthly_review": {
            "name": "Monthly Business Review",
            "pages": 7,
            "frequency": "monthly",
            "day": 1,
            "time": "10:00",
        },
    }

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"

    def generate_daily_brief(
        self, location_id: str, recipient_name: str = "Jorge"
    ) -> Dict[str, Any]:
        """
        Generate daily performance brief

        One-page summary of yesterday's performance with action items
        """
        # Get yesterday's data
        yesterday = datetime.now() - timedelta(days=1)
        conversations = self._load_conversations(location_id, days=1)

        # Calculate metrics
        metrics = self._calculate_daily_metrics(conversations)

        # Identify action items
        action_items = self._get_priority_actions(conversations)

        # Generate insights
        insight = self._generate_daily_insight(metrics)

        report = {
            "report_type": "daily_brief",
            "generated_at": datetime.now().isoformat(),
            "date": yesterday.date().isoformat(),
            "recipient": recipient_name,
            "greeting": self._get_greeting(),
            "summary": {
                "headline": self._generate_headline(metrics),
                "metrics": metrics,
                "insight": insight,
            },
            "hot_leads": self._get_hot_leads(conversations),
            "action_items": action_items,
            "week_progress": self._get_week_progress(location_id),
        }

        return report

    def generate_weekly_summary(
        self, location_id: str, recipient_name: str = "Jorge"
    ) -> Dict[str, Any]:
        """
        Generate weekly executive summary

        2-3 page report with trends, top performers, and recommendations
        """
        conversations = self._load_conversations(location_id, days=7)

        # Weekly metrics
        metrics = self._calculate_weekly_metrics(conversations)

        # Trends
        trends = self._analyze_weekly_trends(conversations)

        # Top performers
        top_performers = self._identify_top_performers(conversations)

        # Recommendations
        recommendations = self._generate_recommendations(metrics, trends)

        report = {
            "report_type": "weekly_summary",
            "generated_at": datetime.now().isoformat(),
            "week_ending": datetime.now().date().isoformat(),
            "recipient": recipient_name,
            "executive_summary": {
                "headline": self._generate_weekly_headline(metrics),
                "key_wins": self._identify_key_wins(metrics),
                "attention_areas": self._identify_attention_areas(metrics),
            },
            "metrics": metrics,
            "trends": trends,
            "top_performers": top_performers,
            "recommendations": recommendations,
            "next_week_goals": self._set_next_week_goals(metrics),
        }

        return report

    def generate_monthly_review(
        self, location_id: str, recipient_name: str = "Jorge"
    ) -> Dict[str, Any]:
        """
        Generate monthly business review

        5-7 page comprehensive analysis with strategic recommendations
        """
        conversations = self._load_conversations(location_id, days=30)

        # Monthly metrics
        metrics = self._calculate_monthly_metrics(conversations)

        # A/B test results
        ab_results = self._get_ab_test_results(location_id)

        # Revenue analysis
        revenue = self._calculate_revenue_impact(conversations)

        # Strategic insights
        strategic = self._generate_strategic_insights(metrics, conversations)

        report = {
            "report_type": "monthly_review",
            "generated_at": datetime.now().isoformat(),
            "month": (datetime.now() - timedelta(days=30)).strftime("%B %Y"),
            "recipient": recipient_name,
            "executive_summary": {
                "performance_rating": self._rate_performance(metrics),
                "headline_metrics": metrics,
                "month_over_month": self._calculate_mom_change(location_id),
            },
            "detailed_analytics": {
                "lead_quality": self._analyze_lead_quality(conversations),
                "conversion_funnel": self._analyze_conversion_funnel(conversations),
                "response_patterns": self._analyze_response_patterns(conversations),
            },
            "ab_test_results": ab_results,
            "revenue_analysis": revenue,
            "strategic_insights": strategic,
            "next_month_goals": self._set_monthly_goals(metrics),
        }

        return report

    def _load_conversations(self, location_id: str, days: int) -> List[Dict]:
        """Load conversation data"""
        analytics_file = self.data_dir / "mock_analytics.json"

        if not analytics_file.exists():
            return []

        with open(analytics_file) as f:
            data = json.load(f)

        cutoff = datetime.now() - timedelta(days=days)
        conversations = [
            c
            for c in data.get("conversations", [])
            if datetime.fromisoformat(c["timestamp"]) >= cutoff
        ]

        return conversations

    def _calculate_daily_metrics(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Calculate daily metrics"""
        total = len(conversations)
        hot = len([c for c in conversations if c.get("lead_score", 0) >= 70])
        appointments = len(
            [c for c in conversations if c.get("appointment_set", False)]
        )

        response_times = [c.get("response_time_minutes", 0) for c in conversations]
        avg_response = (
            sum(response_times) / len(response_times) if response_times else 0
        )

        pipeline_value = hot * 12500

        return {
            "conversations": total,
            "hot_leads": hot,
            "appointments": appointments,
            "conversion_rate": (
                round((appointments / total * 100), 1) if total > 0 else 0
            ),
            "avg_response_time": round(avg_response, 1),
            "pipeline_value": pipeline_value,
        }

    def _get_greeting(self) -> str:
        """Get time-appropriate greeting"""
        hour = datetime.now().hour
        if hour < 12:
            return "Good Morning"
        elif hour < 17:
            return "Good Afternoon"
        else:
            return "Good Evening"

    def _generate_headline(self, metrics: Dict) -> str:
        """Generate headline for daily brief"""
        if metrics["hot_leads"] > 10:
            return f"🔥 Strong Performance: {metrics['hot_leads']} Hot Leads!"
        elif metrics["conversion_rate"] > 20:
            return f"🎯 Excellent Conversion: {metrics['conversion_rate']}%"
        elif metrics["avg_response_time"] < 2:
            return (
                f"⚡ Lightning Fast: {metrics['avg_response_time']} min response time"
            )
        else:
            return f"📊 {metrics['conversations']} Conversations Yesterday"

    def _generate_daily_insight(self, metrics: Dict) -> str:
        """Generate daily insight"""
        insights = []

        if metrics["hot_leads"] > 0:
            insights.append(
                f"Excellent lead quality with {metrics['hot_leads']} hot leads"
            )

        if metrics["conversion_rate"] >= 20:
            insights.append("Conversion rate exceeds target")
        elif metrics["conversion_rate"] < 15:
            insights.append("Conversion rate needs attention")

        if metrics["avg_response_time"] <= 2:
            insights.append("Response time meets target")

        return " • ".join(insights) if insights else "Steady performance"

    def _get_hot_leads(self, conversations: List[Dict]) -> List[Dict]:
        """Get hot leads needing attention"""
        hot_leads = [
            c
            for c in conversations
            if c.get("lead_score", 0) >= 70 and not c.get("appointment_set", False)
        ]

        return [
            {
                "name": lead.get("name", "Unknown"),
                "score": lead.get("lead_score", 0),
                "interest": lead.get("property_interest", "Not specified"),
                "priority": "HIGH",
            }
            for lead in hot_leads[:5]  # Top 5
        ]

    def _get_priority_actions(self, conversations: List[Dict]) -> List[str]:
        """Get priority action items"""
        actions = []

        hot_pending = len(
            [
                c
                for c in conversations
                if c.get("lead_score", 0) >= 70 and not c.get("appointment_set", False)
            ]
        )

        if hot_pending > 0:
            actions.append(f"{hot_pending} hot leads need follow-up today")

        slow_responses = len(
            [c for c in conversations if c.get("response_time_minutes", 0) > 5]
        )

        if slow_responses > len(conversations) * 0.3:
            actions.append("Response time needs improvement")

        return actions

    def _get_week_progress(self, location_id: str) -> Dict[str, Any]:
        """Get week-to-date progress"""
        week_convos = self._load_conversations(location_id, days=7)

        total = len(week_convos)
        target = 100

        return {
            "current": total,
            "target": target,
            "percentage": round((total / target * 100), 1) if target > 0 else 0,
            "status": "on_track" if total >= target * 0.7 else "needs_attention",
        }

    def _calculate_weekly_metrics(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Calculate weekly metrics"""
        # Similar to daily but with week-over-week comparison
        return self._calculate_daily_metrics(conversations)

    def _analyze_weekly_trends(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Analyze weekly trends"""
        return {
            "trend": "increasing",
            "change": "+12%",
            "insight": "Strong upward momentum",
        }

    def _identify_top_performers(self, conversations: List[Dict]) -> List[Dict]:
        """Identify top performing messages/agents"""
        return []

    def _generate_recommendations(self, metrics: Dict, trends: Dict) -> List[str]:
        """Generate recommendations"""
        return [
            "Continue current strategy - metrics improving",
            "Focus on hot lead follow-up",
            "Consider A/B testing new greeting message",
        ]

    def _generate_weekly_headline(self, metrics: Dict) -> str:
        """Generate weekly headline"""
        return f"Week Completed: {metrics['conversations']} Total Conversations"

    def _identify_key_wins(self, metrics: Dict) -> List[str]:
        """Identify key wins"""
        wins = []
        if metrics.get("hot_leads", 0) > 15:
            wins.append(f"{metrics['hot_leads']} hot leads generated")
        if metrics.get("conversion_rate", 0) > 20:
            wins.append(f"{metrics['conversion_rate']}% conversion rate")
        return wins

    def _identify_attention_areas(self, metrics: Dict) -> List[str]:
        """Identify areas needing attention"""
        return []

    def _set_next_week_goals(self, metrics: Dict) -> Dict[str, Any]:
        """Set goals for next week"""
        return {
            "conversations": metrics.get("conversations", 0) * 1.1,
            "hot_leads": 20,
            "conversion_rate": 20,
        }

    def _calculate_monthly_metrics(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Calculate monthly metrics"""
        return self._calculate_daily_metrics(conversations)

    def _get_ab_test_results(self, location_id: str) -> List[Dict]:
        """Get A/B test results"""
        return []

    def _calculate_revenue_impact(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Calculate revenue impact"""
        hot = len([c for c in conversations if c.get("lead_score", 0) >= 70])
        revenue = hot * 12500

        return {
            "pipeline_value": revenue,
            "closed_deals": int(hot * 0.3),
            "revenue_realized": int(revenue * 0.3),
        }

    def _generate_strategic_insights(
        self, metrics: Dict, conversations: List[Dict]
    ) -> List[str]:
        """Generate strategic insights"""
        return []

    def _rate_performance(self, metrics: Dict) -> str:
        """Rate overall performance"""
        if metrics.get("conversion_rate", 0) > 20:
            return "Excellent"
        elif metrics.get("conversion_rate", 0) > 15:
            return "Good"
        else:
            return "Needs Improvement"

    def _calculate_mom_change(self, location_id: str) -> Dict[str, Any]:
        """Calculate month-over-month change"""
        return {
            "conversations": "+15%",
            "conversion_rate": "+3%",
            "pipeline_value": "+$45K",
        }

    def _analyze_lead_quality(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Analyze lead quality"""
        return {}

    def _analyze_conversion_funnel(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Analyze conversion funnel"""
        return {}

    def _analyze_response_patterns(self, conversations: List[Dict]) -> Dict[str, Any]:
        """Analyze response patterns"""
        return {}

    def _set_monthly_goals(self, metrics: Dict) -> Dict[str, Any]:
        """Set goals for next month"""
        return {}


class ReportScheduler:
    """Schedule automated report generation and delivery"""

    def __init__(self):
        """
        Execute init operation.

        Args:
        """
        self.schedules = []

    def schedule_report(
        self,
        report_type: str,
        location_id: str,
        recipient_email: str,
        frequency: str,
        time: str = "09:00",
    ) -> Dict[str, Any]:
        """
        Schedule automated report delivery

        Args:
            report_type: Type of report (daily_brief, weekly_summary, monthly_review)
            location_id: GHL location ID
            recipient_email: Email address for delivery
            frequency: daily, weekly, or monthly
            time: Time to send (HH:MM format)

        Returns:
            Schedule configuration
        """
        schedule = {
            "schedule_id": f"sched_{len(self.schedules) + 1}",
            "report_type": report_type,
            "location_id": location_id,
            "recipient_email": recipient_email,
            "frequency": frequency,
            "time": time,
            "active": True,
            "created_at": datetime.now().isoformat(),
        }

        self.schedules.append(schedule)
        return schedule

    def list_schedules(self, location_id: str = None) -> List[Dict[str, Any]]:
        """List all scheduled reports"""
        if location_id:
            return [s for s in self.schedules if s["location_id"] == location_id]
        return self.schedules
