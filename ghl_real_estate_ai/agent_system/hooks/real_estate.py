"""
Real Estate Domain Hooks.
Implements: Market Oracle, Lead Persona Simulator, Sentiment Decoder.
"""

from ghl_real_estate_ai.agent_system.skills.real_estate import analyze_lead_behavior, search_properties


class MarketOracle:
    """Provides expert market insights and property data."""

    def get_market_trends(self, location: str):
        # In a real implementation, this would call a deeper analysis skill
        return f"Market trends for {location} show a 5% year-over-year growth."

    def search_listings(self, budget: float, location: str):
        return search_properties(budget=budget, location=location)


class LeadPersonaSimulator:
    """Simulates lead behavior for testing and training."""

    async def simulate_lead(self, lead_id: str):
        insights = await analyze_lead_behavior(lead_id)
        return f"Simulated lead {lead_id} with engagement {insights['engagement_score']}"


class SentimentDecoder:
    """Analyzes lead sentiment and emotional state."""

    def analyze(self, text: str):
        """Simple rule-based sentiment analysis for MVP."""
        text_lower = text.lower()

        urgent_keywords = ["asap", "urgent", "quick", "immediately"]
        angry_keywords = ["stop", "unprofessional", "don't want", "complaint"]
        positive_keywords = ["great", "thanks", "perfect", "interested"]

        sentiment = "neutral"
        if any(kw in text_lower for kw in urgent_keywords):
            sentiment = "urgent"
        elif any(kw in text_lower for kw in angry_keywords):
            sentiment = "frustrated"
        elif any(kw in text_lower for kw in positive_keywords):
            sentiment = "positive"

        return {
            "sentiment": sentiment,
            "raw_text_length": len(text),
            "emotional_state": "stable" if sentiment != "frustrated" else "volatile",
        }


from ghl_real_estate_ai.agent_system.dojo.evaluator import DojoEvaluator


class SenseiHook:
    """LLM-based coaching hook for qualitative feedback."""

    def __init__(self):
        self.evaluator = DojoEvaluator()

    async def coach(self, history: list):
        """Grades the conversation and returns coaching tips."""
        evaluation = await self.evaluator.grade_conversation(history)
        return {
            "feedback": evaluation["feedback"],
            "tips": evaluation["coaching_tips"],
            "overall_score": evaluation["overall"],
        }
