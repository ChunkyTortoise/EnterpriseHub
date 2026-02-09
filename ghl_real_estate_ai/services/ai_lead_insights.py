"""
AI Lead Insights Service - Wow Factor Feature #1
Provides intelligent analysis and predictions about leads using AI
"""

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class LeadInsight:
    """Intelligent insight about a lead"""

    lead_id: str
    insight_type: str  # "opportunity", "risk", "action", "prediction"
    title: str
    description: str
    confidence: float  # 0.0 to 1.0
    priority: int  # 1 (highest) to 5 (lowest)
    recommended_action: str
    estimated_impact: str  # "High", "Medium", "Low"
    created_at: datetime

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat()
        return d


class AILeadInsightsService:
    """
    🎯 WOW FEATURE: AI-Powered Lead Intelligence

    This service analyzes lead behavior and conversation patterns to provide
    actionable insights that help Jorge close more deals.

    Key Features:
    - Predicts likelihood of closing
    - Identifies hidden objections
    - Suggests optimal follow-up timing
    - Detects urgency signals
    - Recommends personalized approaches
    """

    def __init__(self):
        self.insights_cache = {}

    def analyze_lead(self, lead_data: Dict) -> List[LeadInsight]:
        """
        Analyze a lead and generate intelligent insights

        Args:
            lead_data: Dict containing:
                - lead_id: str
                - conversations: List[Dict]
                - score: float
                - metadata: Dict

        Returns:
            List of actionable insights
        """
        insights = []
        lead_id = lead_data.get("lead_id")
        conversations = lead_data.get("conversations", [])
        score = lead_data.get("score", 0)
        metadata = lead_data.get("metadata", {})

        # Insight 1: Closing Probability
        closing_prob = self._calculate_closing_probability(conversations, score, metadata)
        if closing_prob > 0.7:
            insights.append(
                LeadInsight(
                    lead_id=lead_id,
                    insight_type="opportunity",
                    title="High Probability Close",
                    description=f"This lead has a {closing_prob * 100:.0f}% probability of closing within 30 days based on engagement patterns.",
                    confidence=closing_prob,
                    priority=1,
                    recommended_action="Schedule in-person property viewing within 48 hours",
                    estimated_impact="High",
                    created_at=datetime.now(),
                )
            )

        # Insight 2: Urgency Detection
        urgency = self._detect_urgency_signals(conversations)
        if urgency["score"] > 0.6:
            insights.append(
                LeadInsight(
                    lead_id=lead_id,
                    insight_type="action",
                    title="High Urgency Detected",
                    description=f"Lead mentioned: {', '.join(urgency['signals'])}. They need to act fast.",
                    confidence=urgency["score"],
                    priority=1,
                    recommended_action="Call immediately - don't wait for text response",
                    estimated_impact="High",
                    created_at=datetime.now(),
                )
            )

        # Insight 3: Hidden Objections
        objections = self._identify_hidden_objections(conversations)
        if objections:
            insights.append(
                LeadInsight(
                    lead_id=lead_id,
                    insight_type="risk",
                    title="Potential Objections Detected",
                    description=f"Lead may have concerns about: {', '.join(objections)}",
                    confidence=0.75,
                    priority=2,
                    recommended_action=f"Proactively address {objections[0]} in next conversation",
                    estimated_impact="Medium",
                    created_at=datetime.now(),
                )
            )

        # Insight 4: Optimal Follow-Up Time
        best_time = self._predict_best_follow_up_time(conversations, metadata)
        insights.append(
            LeadInsight(
                lead_id=lead_id,
                insight_type="action",
                title="Optimal Follow-Up Window",
                description=f"Based on response patterns, best time to reach this lead is {best_time}",
                confidence=0.8,
                priority=3,
                recommended_action=f"Schedule follow-up for {best_time}",
                estimated_impact="Medium",
                created_at=datetime.now(),
            )
        )

        # Insight 5: Competitive Pressure
        competition = self._detect_competitive_signals(conversations)
        if competition["detected"]:
            insights.append(
                LeadInsight(
                    lead_id=lead_id,
                    insight_type="risk",
                    title="Competing with Other Agents",
                    description=f"Lead mentioned talking to {competition['count']} other agent(s)",
                    confidence=0.85,
                    priority=1,
                    recommended_action="Differentiate with unique value prop - mention Jorge's dual path approach",
                    estimated_impact="High",
                    created_at=datetime.now(),
                )
            )

        # Insight 6: Budget Reality Check
        budget_insight = self._analyze_budget_reality(conversations, metadata)
        if budget_insight:
            insights.append(budget_insight)

        return insights

    def _calculate_closing_probability(self, conversations: List, score: float, metadata: Dict) -> float:
        """Calculate probability of closing based on multiple factors"""
        probability = 0.0

        # Factor 1: Lead score (0-10)
        probability += (score / 10) * 0.3  # 30% weight

        # Factor 2: Engagement level
        if len(conversations) > 5:
            probability += 0.2
        elif len(conversations) > 3:
            probability += 0.1

        # Factor 3: Response speed
        avg_response_time = self._calculate_avg_response_time(conversations)
        if avg_response_time < 300:  # < 5 minutes
            probability += 0.2
        elif avg_response_time < 3600:  # < 1 hour
            probability += 0.1

        # Factor 4: Questions answered
        answered_questions = metadata.get("answered_questions", 0)
        probability += min(answered_questions / 7, 1.0) * 0.3  # 30% weight

        return min(probability, 1.0)

    def _detect_urgency_signals(self, conversations: List) -> Dict:
        """Detect urgency signals in conversation"""
        urgency_keywords = [
            "asap",
            "urgent",
            "quickly",
            "soon",
            "immediate",
            "right away",
            "this week",
            "today",
            "tomorrow",
            "need to move",
            "deadline",
            "losing my lease",
            "closing date",
            "already sold",
            "cash buyer",
        ]

        signals = []
        score = 0.0

        for conv in conversations:
            message = conv.get("message", "").lower()
            for keyword in urgency_keywords:
                if keyword in message:
                    signals.append(keyword)
                    score += 0.15

        return {
            "score": min(score, 1.0),
            "signals": list(set(signals))[:3],  # Top 3 unique signals
        }

    def _identify_hidden_objections(self, conversations: List) -> List[str]:
        """Identify potential objections from conversation patterns"""
        objections = []

        # Pattern 1: Price concerns
        price_keywords = [
            "expensive",
            "afford",
            "budget",
            "too much",
            "price",
            "cheaper",
        ]
        for conv in conversations:
            message = conv.get("message", "").lower()
            if any(kw in message for kw in price_keywords):
                if "price" not in objections:
                    objections.append("pricing")
                break

        # Pattern 2: Timing concerns
        timing_keywords = ["not ready", "not sure", "thinking", "maybe", "later"]
        for conv in conversations:
            message = conv.get("message", "").lower()
            if any(kw in message for kw in timing_keywords):
                if "timing" not in objections:
                    objections.append("timing")
                break

        # Pattern 3: Trust/credibility
        trust_keywords = [
            "reviews",
            "references",
            "credentials",
            "license",
            "experience",
        ]
        for conv in conversations:
            message = conv.get("message", "").lower()
            if any(kw in message for kw in trust_keywords):
                if "credibility" not in objections:
                    objections.append("credibility")
                break

        return objections[:3]  # Top 3 objections

    def _predict_best_follow_up_time(self, conversations: List, metadata: Dict) -> str:
        """Predict best time to follow up based on response patterns"""
        # Analyze when lead typically responds
        response_hours = []
        for i, conv in enumerate(conversations):
            if i > 0 and conv.get("sender") == "lead":
                timestamp = conv.get("timestamp")
                if timestamp:
                    dt = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
                    response_hours.append(dt.hour)

        if response_hours:
            # Most common response hour
            most_common_hour = max(set(response_hours), key=response_hours.count)

            if 9 <= most_common_hour < 12:
                return "Late morning (10-11am)"
            elif 12 <= most_common_hour < 17:
                return "Early afternoon (1-3pm)"
            elif 17 <= most_common_hour < 21:
                return "Evening (6-8pm)"
            else:
                return "Next business day morning (9-10am)"

        return "Afternoon (2-4pm)"  # Default

    def _detect_competitive_signals(self, conversations: List) -> Dict:
        """Detect if lead is talking to other agents"""
        competitive_keywords = [
            "other agent",
            "another realtor",
            "comparing",
            "other offers",
            "someone else",
            "different agent",
            "multiple offers",
        ]

        count = 0
        for conv in conversations:
            message = conv.get("message", "").lower()
            for keyword in competitive_keywords:
                if keyword in message:
                    count += 1
                    break

        return {"detected": count > 0, "count": count}

    def _calculate_avg_response_time(self, conversations: List) -> float:
        """Calculate average response time in seconds"""
        response_times = []

        for i in range(1, len(conversations)):
            prev_conv = conversations[i - 1]
            curr_conv = conversations[i]

            if prev_conv.get("sender") != curr_conv.get("sender"):
                prev_time = prev_conv.get("timestamp")
                curr_time = curr_conv.get("timestamp")

                if prev_time and curr_time:
                    prev_dt = datetime.fromisoformat(prev_time) if isinstance(prev_time, str) else prev_time
                    curr_dt = datetime.fromisoformat(curr_time) if isinstance(curr_time, str) else curr_time
                    diff = (curr_dt - prev_dt).total_seconds()
                    if diff > 0:
                        response_times.append(diff)

        return sum(response_times) / len(response_times) if response_times else 3600

    def _analyze_budget_reality(self, conversations: List, metadata: Dict) -> Optional[LeadInsight]:
        """Analyze if lead's budget matches their expectations"""
        budget = metadata.get("budget")
        location = metadata.get("location", "").lower()

        # Simplified budget analysis
        if budget and location:
            # Check for disconnect between budget and expectations
            high_cost_areas = ["miami beach", "downtown", "brickell", "coral gables"]

            if any(area in location for area in high_cost_areas):
                if budget < 400000:
                    return LeadInsight(
                        lead_id=metadata.get("lead_id"),
                        insight_type="risk",
                        title="Budget-Location Mismatch",
                        description=f"Lead's budget (${budget:,}) may be low for {location}. May need education on market prices.",
                        confidence=0.7,
                        priority=2,
                        recommended_action="Share recent comparable sales in their target area",
                        estimated_impact="Medium",
                        created_at=datetime.now(),
                    )

        return None

    def get_daily_insights_summary(self, tenant_id: str, leads: List[Dict]) -> Dict:
        """
        Generate a daily summary of insights across all leads

        Returns a dashboard-ready summary with key metrics
        """
        all_insights = []
        for lead in leads:
            insights = self.analyze_lead(lead)
            all_insights.extend(insights)

        # Categorize insights
        opportunities = [i for i in all_insights if i.insight_type == "opportunity"]
        risks = [i for i in all_insights if i.insight_type == "risk"]
        actions = [i for i in all_insights if i.insight_type == "action"]

        # Priority breakdown
        urgent = [i for i in all_insights if i.priority == 1]
        important = [i for i in all_insights if i.priority == 2]

        return {
            "tenant_id": tenant_id,
            "date": datetime.now().isoformat(),
            "summary": {
                "total_insights": len(all_insights),
                "opportunities": len(opportunities),
                "risks": len(risks),
                "actions_needed": len(actions),
                "urgent_items": len(urgent),
                "important_items": len(important),
            },
            "top_opportunities": [
                i.to_dict() for i in sorted(opportunities, key=lambda x: x.confidence, reverse=True)[:5]
            ],
            "urgent_actions": [i.to_dict() for i in urgent[:10]],
            "risk_alerts": [i.to_dict() for i in risks[:5]],
        }

    def predict_next_best_action(self, lead_data: Dict) -> Dict:
        """
        🆕 ENHANCEMENT: AI-powered next best action predictor

        Analyzes all signals and recommends the single most effective action
        """
        insights = self.analyze_lead(lead_data)
        score = lead_data.get("score", 0)
        conversations = lead_data.get("conversations", [])
        metadata = lead_data.get("metadata", {})

        # Calculate action priorities
        actions = []

        # Action 1: Call if hot and urgent
        if score > 7.5 and any("urgent" in str(c.get("message", "")).lower() for c in conversations):
            actions.append(
                {
                    "action": "call_now",
                    "priority": 10,
                    "reason": "Hot lead with urgency - strike while iron is hot",
                    "expected_impact": "High",
                    "timing": "Within 15 minutes",
                }
            )

        # Action 2: Schedule appointment if engaged
        if len(conversations) > 3 and not metadata.get("appointment_scheduled"):
            actions.append(
                {
                    "action": "schedule_appointment",
                    "priority": 8,
                    "reason": "Engaged lead without appointment scheduled",
                    "expected_impact": "High",
                    "timing": "Today",
                }
            )

        # Action 3: Break-up text if unresponsive
        agent_msgs = [c for c in conversations[-3:] if c.get("sender") == "agent"]
        if len(agent_msgs) >= 2:
            actions.append(
                {
                    "action": "breakup_text",
                    "priority": 7,
                    "reason": "Lead stopped responding - re-engage with break-up text",
                    "expected_impact": "Medium",
                    "timing": "Within 4 hours",
                }
            )

        # Action 4: Address objections
        if any(i.insight_type == "risk" for i in insights):
            actions.append(
                {
                    "action": "address_objections",
                    "priority": 6,
                    "reason": "Objections detected - need to be addressed proactively",
                    "expected_impact": "Medium",
                    "timing": "Next conversation",
                }
            )

        # Action 5: Send value content
        if score < 5 and len(conversations) < 3:
            actions.append(
                {
                    "action": "send_value_content",
                    "priority": 4,
                    "reason": "Build trust with educational content",
                    "expected_impact": "Low",
                    "timing": "Within 24 hours",
                }
            )

        # Sort by priority
        actions.sort(key=lambda x: x["priority"], reverse=True)

        return {
            "lead_id": lead_data.get("lead_id"),
            "next_best_action": actions[0] if actions else None,
            "alternative_actions": actions[1:3] if len(actions) > 1 else [],
            "confidence": 0.85,
            "generated_at": datetime.now().isoformat(),
        }

    def get_lead_health_score(self, lead_data: Dict) -> Dict:
        """
        🆕 ENHANCEMENT: Comprehensive lead health assessment

        Returns 0-100 health score with breakdown
        """
        score = lead_data.get("score", 0)
        conversations = lead_data.get("conversations", [])
        metadata = lead_data.get("metadata", {})

        # Calculate health components
        engagement_health = min(len(conversations) * 10, 100)
        response_health = 100 if conversations and conversations[-1].get("sender") == "lead" else 50
        qualification_health = (metadata.get("answered_questions", 0) / 7) * 100
        momentum_health = self._calculate_momentum(conversations)

        # Weighted average
        overall_health = (
            engagement_health * 0.3 + response_health * 0.2 + qualification_health * 0.3 + momentum_health * 0.2
        )

        # Determine status
        if overall_health >= 80:
            status = "🟢 Excellent"
        elif overall_health >= 60:
            status = "🟡 Good"
        elif overall_health >= 40:
            status = "🟠 Fair"
        else:
            status = "🔴 Poor"

        return {
            "lead_id": lead_data.get("lead_id"),
            "overall_health": round(overall_health),
            "status": status,
            "components": {
                "engagement": round(engagement_health),
                "responsiveness": round(response_health),
                "qualification": round(qualification_health),
                "momentum": round(momentum_health),
            },
            "trend": self._get_health_trend(conversations),
            "recommendation": self._get_health_recommendation(overall_health),
        }

    def _calculate_momentum(self, conversations: List) -> float:
        """Calculate conversation momentum (0-100)"""
        if len(conversations) < 2:
            return 50

        # Check if conversations are getting more frequent
        recent = conversations[-3:] if len(conversations) >= 3 else conversations
        older = conversations[-6:-3] if len(conversations) >= 6 else []

        if len(recent) > len(older):
            return 80  # Increasing momentum
        elif len(recent) == len(older):
            return 60  # Stable
        else:
            return 30  # Decreasing

    def _get_health_trend(self, conversations: List) -> str:
        """Get trend direction"""
        momentum = self._calculate_momentum(conversations)
        if momentum > 70:
            return "📈 Improving"
        elif momentum < 40:
            return "📉 Declining"
        else:
            return "➡️ Stable"

    def _get_health_recommendation(self, health: float) -> str:
        """Get recommendation based on health score"""
        if health >= 80:
            return "Keep engaging - this lead is hot!"
        elif health >= 60:
            return "Good progress - push for appointment"
        elif health >= 40:
            return "Needs attention - re-engagement required"
        else:
            return "At risk - consider break-up text or pause"


# Example usage
if __name__ == "__main__":
    service = AILeadInsightsService()

    # Example lead data
    sample_lead = {
        "lead_id": "L123",
        "conversations": [
            {
                "sender": "agent",
                "message": "Hey! Are you looking to buy or sell?",
                "timestamp": "2026-01-05T10:00:00",
            },
            {
                "sender": "lead",
                "message": "Looking to sell ASAP, already found my next place",
                "timestamp": "2026-01-05T10:02:00",
            },
            {
                "sender": "agent",
                "message": "Got it! Cash offer or list for top dollar?",
                "timestamp": "2026-01-05T10:03:00",
            },
            {
                "sender": "lead",
                "message": "What would be faster? Need to move in 2 weeks",
                "timestamp": "2026-01-05T10:05:00",
            },
        ],
        "score": 8.5,
        "metadata": {
            "lead_id": "L123",
            "answered_questions": 5,
            "budget": 350000,
            "location": "Miami Beach",
        },
    }

    insights = service.analyze_lead(sample_lead)

    print("🎯 AI Lead Insights Demo\n")
    for insight in insights:
        print(f"{'🔥' if insight.priority == 1 else '⚠️'} {insight.title}")
        print(f"   {insight.description}")
        print(f"   → Action: {insight.recommended_action}")
        print(f"   Confidence: {insight.confidence * 100:.0f}% | Impact: {insight.estimated_impact}\n")
