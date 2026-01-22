#!/usr/bin/env python3
"""
Demo script for Jorge's Predictive Lead Scoring 2.0 System.

This script demonstrates the advanced ML-powered lead scoring system
with real-time predictions, action recommendations, and ROI optimization.
"""

import asyncio
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List
import numpy as np

from ghl_real_estate_ai.services.predictive_lead_scorer_v2 import PredictiveLeadScorerV2
from ghl_real_estate_ai.services.action_recommendations import ActionRecommendationsEngine
from ghl_real_estate_ai.ml.closing_probability_model import ClosingProbabilityModel
from ghl_real_estate_ai.ml.feature_engineering import FeatureEngineer


class PredictiveScoringDemo:
    """Demo class for showcasing the predictive lead scoring system."""

    def __init__(self):
        """Initialize demo components."""
        self.scorer = PredictiveLeadScorerV2()
        self.action_engine = ActionRecommendationsEngine()
        self.ml_model = ClosingProbabilityModel()
        self.feature_engineer = FeatureEngineer()

    def create_sample_leads(self) -> List[Dict]:
        """Create diverse sample leads for demonstration."""
        leads = [
            {
                "name": "Sarah Chen",
                "lead_id": "lead_001",
                "conversation_history": [
                    {"role": "user", "text": "Hi, I'm relocating to the area for work and need to find a house quickly"},
                    {"role": "assistant", "text": "I'd be happy to help! When do you need to move?"},
                    {"role": "user", "text": "I start my new job in 6 weeks, so I need to close within a month"},
                    {"role": "assistant", "text": "That's definitely doable. What's your budget range?"},
                    {"role": "user", "text": "Up to $750,000. I need at least 3 bedrooms and 2 bathrooms"},
                    {"role": "assistant", "text": "Great! Are you pre-approved for financing?"},
                    {"role": "user", "text": "Yes, I got pre-approved for $800k yesterday. Looking in the downtown area"},
                    {"role": "assistant", "text": "Perfect! I have several properties that would be perfect. When can we schedule viewings?"},
                    {"role": "user", "text": "This weekend would be ideal. I'm very motivated to find something soon!"}
                ],
                "extracted_preferences": {
                    "budget": "$750,000",
                    "location": "downtown",
                    "bedrooms": "3",
                    "bathrooms": "2",
                    "timeline": "within a month",
                    "motivation": "work relocation",
                    "financing": "pre-approved for $800k"
                },
                "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "location": "downtown"
            },
            {
                "name": "Mike Rodriguez",
                "lead_id": "lead_002",
                "conversation_history": [
                    {"role": "user", "text": "Hello, just exploring options"},
                    {"role": "assistant", "text": "Hi! I'd love to help you explore. What brings you to look at real estate?"},
                    {"role": "user", "text": "Maybe upgrading sometime in the future"},
                    {"role": "assistant", "text": "That's great! What type of home are you considering?"},
                    {"role": "user", "text": "Not sure yet, still researching"}
                ],
                "extracted_preferences": {
                    "timeline": "future"
                },
                "created_at": (datetime.now() - timedelta(days=3)).isoformat(),
                "location": "suburbs"
            },
            {
                "name": "Jennifer Park",
                "lead_id": "lead_003",
                "conversation_history": [
                    {"role": "user", "text": "I'm looking to buy my first home"},
                    {"role": "assistant", "text": "Congratulations on taking this exciting step! Tell me about your needs."},
                    {"role": "user", "text": "I want something under $400k, preferably 2 bedrooms"},
                    {"role": "assistant", "text": "Great budget to work with! Any specific areas you're interested in?"},
                    {"role": "user", "text": "Somewhere safe with good schools for the future. Timeline is flexible"},
                    {"role": "assistant", "text": "Have you been pre-approved for a mortgage yet?"},
                    {"role": "user", "text": "Not yet, but I have good credit and stable income. Been saving for a while"},
                    {"role": "assistant", "text": "Perfect! Let's get you connected with a great lender first."},
                    {"role": "user", "text": "That sounds good. Also, what areas would you recommend for someone like me?"}
                ],
                "extracted_preferences": {
                    "budget": "$400,000",
                    "bedrooms": "2",
                    "location": "safe area with good schools",
                    "timeline": "flexible",
                    "motivation": "first-time buyer"
                },
                "created_at": (datetime.now() - timedelta(hours=12)).isoformat(),
                "location": "family neighborhoods"
            },
            {
                "name": "David Thompson",
                "lead_id": "lead_004",
                "conversation_history": [
                    {"role": "user", "text": "Need to sell my house ASAP due to divorce"},
                    {"role": "assistant", "text": "I understand this is a difficult time. I'm here to help make the process as smooth as possible."},
                    {"role": "user", "text": "The house is in decent condition, 4 bed 3 bath in Westside. How quickly can we list it?"},
                    {"role": "assistant", "text": "We can typically get properties listed within 3-5 days. Have you had a recent appraisal?"},
                    {"role": "user", "text": "No, but neighbors sold similar houses for around $600-650k recently"},
                    {"role": "assistant", "text": "That's helpful context. I'd recommend a CMA to price it competitively. When do you need to close?"},
                    {"role": "user", "text": "Ideally within 45 days. Need to split proceeds and move on"},
                    {"role": "assistant", "text": "Understood. With proper pricing and staging, that timeline is very achievable."}
                ],
                "extracted_preferences": {
                    "property_type": "seller",
                    "location": "Westside",
                    "bedrooms": "4",
                    "bathrooms": "3",
                    "timeline": "45 days",
                    "motivation": "divorce",
                    "home_condition": "decent condition",
                    "expected_price": "$600-650k"
                },
                "created_at": (datetime.now() - timedelta(hours=6)).isoformat(),
                "location": "Westside"
            },
            {
                "name": "Lisa Wang",
                "lead_id": "lead_005",
                "conversation_history": [
                    {"role": "user", "text": "Looking for investment property opportunities"},
                    {"role": "assistant", "text": "Great! Are you looking for rental income or fix-and-flip opportunities?"},
                    {"role": "user", "text": "Rental income. Want something that cash flows well"},
                    {"role": "assistant", "text": "What's your target price range and preferred property type?"},
                    {"role": "user", "text": "Up to $300k, multi-family if possible, or single family in up-and-coming areas"},
                    {"role": "assistant", "text": "I know some great areas with strong rental demand. How many properties are you looking to acquire?"},
                    {"role": "user", "text": "Starting with one, but want to build a portfolio over time"},
                    {"role": "assistant", "text": "Perfect strategy! Do you have financing arranged for investment properties?"},
                    {"role": "user", "text": "Working with a commercial lender, should have approval soon"}
                ],
                "extracted_preferences": {
                    "property_type": "investment",
                    "budget": "$300,000",
                    "motivation": "rental income",
                    "location": "up-and-coming areas",
                    "financing": "commercial lender"
                },
                "created_at": (datetime.now() - timedelta(hours=18)).isoformat(),
                "location": "emerging markets"
            }
        ]

        return leads

    async def train_demo_model(self):
        """Train the ML model with synthetic data for demo purposes."""
        print("🤖 Training ML Model with Synthetic Data...")

        # Generate synthetic training data
        training_data = self.ml_model.generate_synthetic_training_data(
            num_samples=500,
            positive_rate=0.25
        )

        # Train the model
        metrics = await self.ml_model.train_model(training_data)

        print(f"✅ Model Training Complete!")
        print(f"   Accuracy: {metrics.accuracy:.1%}")
        print(f"   AUC Score: {metrics.auc_score:.1%}")
        print(f"   F1 Score: {metrics.f1_score:.1%}")
        print()

    async def analyze_lead(self, lead: Dict) -> Dict:
        """Analyze a single lead with full predictive scoring."""
        print(f"🔍 Analyzing Lead: {lead['name']} (ID: {lead['lead_id']})")
        print("-" * 60)

        # Get predictive score
        score = await self.scorer.calculate_predictive_score(
            {
                "conversation_history": lead["conversation_history"],
                "extracted_preferences": lead["extracted_preferences"],
                "created_at": lead["created_at"]
            },
            lead.get("location")
        )

        # Get insights
        insights = await self.scorer.generate_lead_insights(
            {
                "conversation_history": lead["conversation_history"],
                "extracted_preferences": lead["extracted_preferences"],
                "created_at": lead["created_at"]
            },
            lead.get("location")
        )

        # Get action recommendations
        actions = await self.action_engine.generate_action_recommendations(
            {
                "conversation_history": lead["conversation_history"],
                "extracted_preferences": lead["extracted_preferences"],
                "created_at": lead["created_at"]
            },
            lead.get("location")
        )

        # Format results
        result = {
            "name": lead["name"],
            "lead_id": lead["lead_id"],
            "score": {
                "overall_priority": f"{score.overall_priority_score:.1f}%",
                "priority_level": score.priority_level.value.upper(),
                "closing_probability": f"{score.closing_probability:.1%}",
                "qualification_score": f"{score.qualification_score}/7",
                "engagement_score": f"{score.engagement_score:.1f}/100",
                "urgency_score": f"{score.urgency_score:.1f}/100",
                "risk_score": f"{score.risk_score:.1f}/100"
            },
            "revenue": {
                "estimated_potential": f"${score.estimated_revenue_potential:,.0f}",
                "effort_efficiency": f"${score.effort_efficiency_score:.0f}/hour",
                "time_investment": score.time_investment_recommendation
            },
            "insights": {
                "engagement_trend": insights.engagement_trend,
                "conversation_quality": f"{insights.conversation_quality_score:.1f}/100",
                "time_to_close": f"{insights.estimated_time_to_close} days",
                "churn_probability": f"{insights.probability_of_churn:.1%}",
                "effort_level": insights.recommended_effort_level
            },
            "recommendations": {
                "next_best_action": insights.next_best_action,
                "communication_channel": insights.optimal_communication_channel,
                "contact_timing": score.optimal_contact_timing,
                "follow_up_interval": insights.recommended_follow_up_interval
            },
            "actions": [
                {
                    "title": action.title,
                    "priority": action.priority_level,
                    "timing": action.recommended_timing,
                    "channel": action.communication_channel.value,
                    "success_probability": f"{action.success_probability:.1%}",
                    "roi_potential": f"${action.roi_potential:,.0f}"
                }
                for action in actions[:3]  # Top 3 actions
            ],
            "risk_factors": score.risk_factors,
            "positive_signals": score.positive_signals
        }

        # Display results
        self.display_lead_analysis(result)

        return result

    def display_lead_analysis(self, result: Dict):
        """Display formatted lead analysis results."""

        # Priority and scoring
        priority_emoji = {
            "CRITICAL": "🚨",
            "HIGH": "🔥",
            "MEDIUM": "⚡",
            "LOW": "📝",
            "COLD": "❄️"
        }

        priority = result["score"]["priority_level"]
        emoji = priority_emoji.get(priority, "📊")

        print(f"{emoji} PRIORITY: {priority} ({result['score']['overall_priority']})")
        print(f"💰 Revenue Potential: {result['revenue']['estimated_potential']} | "
              f"Efficiency: {result['revenue']['effort_efficiency']}")
        print(f"📈 Closing Probability: {result['score']['closing_probability']} | "
              f"Time to Close: {result['insights']['time_to_close']}")
        print()

        # Key metrics
        print("📊 KEY METRICS:")
        print(f"   Qualification: {result['score']['qualification_score']}")
        print(f"   Engagement: {result['score']['engagement_score']}")
        print(f"   Urgency: {result['score']['urgency_score']}")
        print(f"   Risk Level: {result['score']['risk_score']}")
        print()

        # Insights
        print("🧠 INSIGHTS:")
        print(f"   Engagement Trend: {result['insights']['engagement_trend'].title()}")
        print(f"   Conversation Quality: {result['insights']['conversation_quality']}")
        print(f"   Churn Risk: {result['insights']['churn_probability']}")
        print(f"   Recommended Effort: {result['insights']['effort_level'].title()}")
        print()

        # Top recommendation
        print("🎯 NEXT BEST ACTION:")
        print(f"   {result['recommendations']['next_best_action']}")
        print(f"   Channel: {result['recommendations']['communication_channel']}")
        print(f"   Timing: {result['recommendations']['contact_timing']}")
        print()

        # Top actions
        if result["actions"]:
            print("📋 TOP ACTIONS:")
            for i, action in enumerate(result["actions"][:2], 1):
                print(f"   {i}. {action['title']} (Priority: {action['priority']}/10)")
                print(f"      🕒 {action['timing']} | 📞 {action['channel']} | "
                      f"💯 {action['success_probability']} success")
        print()

        # Signals
        if result["positive_signals"]:
            print("✅ POSITIVE SIGNALS:")
            for signal in result["positive_signals"][:3]:
                print(f"   • {signal}")
        print()

        if result["risk_factors"]:
            print("⚠️ RISK FACTORS:")
            for factor in result["risk_factors"][:3]:
                print(f"   • {factor}")
        print()

    async def generate_priority_report(self, leads_analysis: List[Dict]):
        """Generate a priority report for Jorge's workflow optimization."""
        print("📈 JORGE'S PRIORITY DASHBOARD")
        print("=" * 60)

        # Sort leads by priority score
        sorted_leads = sorted(
            leads_analysis,
            key=lambda x: float(x["score"]["overall_priority"].rstrip('%')),
            reverse=True
        )

        print("\n🚨 IMMEDIATE ACTION REQUIRED:")
        critical_high = [
            lead for lead in sorted_leads
            if lead["score"]["priority_level"] in ["CRITICAL", "HIGH"]
        ]

        if critical_high:
            for lead in critical_high:
                priority = lead["score"]["priority_level"]
                print(f"   {priority}: {lead['name']} ({lead['score']['overall_priority']}) - "
                      f"{lead['revenue']['estimated_potential']}")
        else:
            print("   No critical or high priority leads at this time")

        print("\n⏰ TODAY'S FOCUS AREAS:")
        total_revenue = sum(
            float(lead["revenue"]["estimated_potential"].replace('$', '').replace(',', ''))
            for lead in sorted_leads
        )

        high_efficiency_leads = [
            lead for lead in sorted_leads
            if float(lead["revenue"]["effort_efficiency"].split('$')[1].split('/')[0]) > 300
        ]

        print(f"   Total Pipeline Value: ${total_revenue:,.0f}")
        print(f"   High-Efficiency Leads: {len(high_efficiency_leads)}")
        print(f"   Leads Requiring Immediate Attention: {len(critical_high)}")

        print("\n📞 RECOMMENDED CALL SEQUENCE:")
        for i, lead in enumerate(sorted_leads[:3], 1):
            timing = lead["recommendations"]["contact_timing"]
            channel = lead["recommendations"]["communication_channel"]
            print(f"   {i}. {lead['name']} - {channel} ({timing})")

        print("\n💡 OPTIMIZATION INSIGHTS:")
        avg_closing_prob = np.mean([
            float(lead["score"]["closing_probability"].rstrip('%')) / 100
            for lead in sorted_leads
        ])

        avg_time_to_close = np.mean([
            int(lead["insights"]["time_to_close"].split(' ')[0])
            for lead in sorted_leads
        ])

        print(f"   Average Closing Probability: {avg_closing_prob:.1%}")
        print(f"   Average Time to Close: {avg_time_to_close:.0f} days")

        # Efficiency recommendations
        most_efficient = max(
            sorted_leads,
            key=lambda x: float(x["revenue"]["effort_efficiency"].split('$')[1].split('/')[0])
        )
        print(f"   Most Efficient Lead: {most_efficient['name']} "
              f"({most_efficient['revenue']['effort_efficiency']})")

        print("\n" + "=" * 60)

    async def run_demo(self):
        """Run the complete predictive scoring demo."""
        print("🏠 JORGE'S PREDICTIVE LEAD SCORING 2.0 DEMO")
        print("=" * 60)
        print("Advanced ML-Powered Lead Prioritization & Action Recommendations")
        print("=" * 60)
        print()

        # Train model
        await self.train_demo_model()

        # Create sample leads
        sample_leads = self.create_sample_leads()
        print(f"📋 Analyzing {len(sample_leads)} Sample Leads...")
        print()

        # Analyze each lead
        all_analysis = []
        for i, lead in enumerate(sample_leads, 1):
            print(f"LEAD {i}/{len(sample_leads)}")
            analysis = await self.analyze_lead(lead)
            all_analysis.append(analysis)
            print()

        # Generate priority report
        await self.generate_priority_report(all_analysis)

        # Model performance summary
        performance = await self.ml_model.get_model_performance()
        if performance:
            print("\n🤖 ML MODEL PERFORMANCE:")
            print(f"   Accuracy: {performance.accuracy:.1%}")
            print(f"   AUC Score: {performance.auc_score:.1%}")
            print(f"   Top Features: {list(performance.feature_importances.keys())[:3]}")

        print("\n✨ Demo Complete! Jorge's leads are now optimally prioritized.")


async def main():
    """Run the predictive scoring demo."""
    demo = PredictiveScoringDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())