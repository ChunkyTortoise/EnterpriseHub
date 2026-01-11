"""
Enhanced Real-Time Lead Intelligence Demo

Demonstrates the capabilities of the performance-optimized lead intelligence service
with real-world scenarios and advanced AI-powered analysis.

Features:
- Real-time conversation analysis (<50ms)
- ML-powered insights and predictions
- Comprehensive lead health assessment
- Next best action recommendations
- Performance monitoring and metrics

Usage:
    python examples/enhanced_lead_intelligence_demo.py
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
import sys
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.services.enhanced_realtime_lead_intelligence import (
    EnhancedRealTimeLeadIntelligence,
    RealTimeInsightType,
    LeadIntelligenceLevel,
    ConversationMomentum
)


class LeadIntelligenceDemo:
    """Demo showcasing enhanced lead intelligence capabilities"""

    def __init__(self):
        self.service = None
        self.demo_scenarios = self._create_demo_scenarios()

    async def initialize(self):
        """Initialize the enhanced lead intelligence service"""
        print("🚀 Initializing Enhanced Lead Intelligence Service...")

        config = {
            "redis_url": "redis://localhost:6379",
            "model_cache_dir": "demo_models",
            "enable_performance_monitoring": True
        }

        start_time = time.time()
        self.service = EnhancedRealTimeLeadIntelligence(config)

        try:
            await self.service.initialize()
            init_time = (time.time() - start_time) * 1000
            print(f"✅ Service initialized successfully in {init_time:.1f}ms")
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            print("📝 Note: Some services may be mocked for demo purposes")
            # Continue with mocked services for demo
            await self._setup_demo_mocks()

        print()

    async def run_demo(self):
        """Run comprehensive demo of lead intelligence features"""
        print("=" * 80)
        print("🎯 ENHANCED REAL-TIME LEAD INTELLIGENCE DEMO")
        print("=" * 80)
        print()

        await self.initialize()

        # Run demo scenarios
        for i, scenario in enumerate(self.demo_scenarios, 1):
            print(f"📋 SCENARIO {i}: {scenario['name']}")
            print("-" * 50)
            await self._run_scenario(scenario)
            print()

        # Run performance benchmarks
        await self._run_performance_demo()

        # Health check
        await self._run_health_check()

        # Cleanup
        await self._cleanup()

    async def _run_scenario(self, scenario):
        """Run a single demo scenario"""
        lead_id = scenario["lead_id"]
        conversation_data = scenario["conversation_data"]
        expected_insight = scenario["expected_insight"]

        print(f"👤 Lead ID: {lead_id}")
        print(f"💬 Conversation: {len(conversation_data['messages'])} messages")
        print()

        # Display conversation
        for i, msg in enumerate(conversation_data["messages"][:3], 1):
            print(f"  {i}. \"{msg['content'][:60]}{'...' if len(msg['content']) > 60 else ''}\"")

        if len(conversation_data["messages"]) > 3:
            print(f"  ... and {len(conversation_data['messages']) - 3} more messages")

        print()

        try:
            # Real-time analysis
            print("🔍 Performing real-time analysis...")
            start_time = time.time()

            insight = await self.service.analyze_lead_realtime(
                lead_id=lead_id,
                conversation_data=conversation_data,
                context=scenario.get("context", {})
            )

            analysis_time = (time.time() - start_time) * 1000

            # Display results
            print(f"⚡ Analysis completed in {analysis_time:.1f}ms")
            print()

            self._display_insight_results(insight, expected_insight)

            # Lead health assessment
            print("🏥 Generating lead health assessment...")
            start_time = time.time()

            health_assessment = await self.service.assess_lead_health(
                lead_id=lead_id,
                historical_data=scenario.get("historical_data")
            )

            health_time = (time.time() - start_time) * 1000
            print(f"⚡ Health assessment completed in {health_time:.1f}ms")
            print()

            self._display_health_assessment(health_assessment)

            # Next best actions
            print("🎯 Generating next best actions...")
            start_time = time.time()

            actions = await self.service.get_next_best_actions(
                lead_id=lead_id,
                current_context=conversation_data
            )

            actions_time = (time.time() - start_time) * 1000
            print(f"⚡ Actions generated in {actions_time:.1f}ms")
            print()

            self._display_next_best_actions(actions)

        except Exception as e:
            print(f"❌ Error in scenario: {e}")

        print("=" * 80)

    def _display_insight_results(self, insight, expected):
        """Display insight analysis results"""
        print(f"📊 REAL-TIME INSIGHT RESULTS")
        print(f"  🏷️  Type: {insight.insight_type.value.title()}")
        print(f"  📝 Title: {insight.title}")
        print(f"  📄 Description: {insight.description}")
        print(f"  🎯 Priority Score: {insight.priority_score:.1f}/100")
        print(f"  🧠 ML Confidence: {insight.ml_confidence:.2f}")
        print(f"  ⚡ Urgency Level: {insight.urgency_level}/5")
        print(f"  🔮 Predicted Outcome: {insight.predicted_outcome or 'Unknown'}")
        print(f"  📈 Impact Assessment: {insight.impact_assessment.title()}")

        if insight.behavioral_signals:
            print(f"  🔍 Behavioral Signals: {', '.join(insight.behavioral_signals)}")

        if insight.recommended_actions:
            print(f"  💡 Recommended Actions:")
            for i, action in enumerate(insight.recommended_actions[:3], 1):
                print(f"     {i}. {action}")

        # Validation against expected results
        if expected:
            validation_score = self._validate_insight(insight, expected)
            print(f"  ✅ Validation Score: {validation_score:.0f}%")

        print()

    def _display_health_assessment(self, assessment):
        """Display health assessment results"""
        print(f"🏥 LEAD HEALTH ASSESSMENT")
        print(f"  📊 Overall Health: {assessment.overall_health_score:.1f}/100")
        print(f"  🎚️  Intelligence Level: {assessment.intelligence_level.value.title()}")
        print(f"  📈 Momentum: {assessment.momentum.value.title()}")
        print(f"  💫 Engagement Score: {assessment.engagement_score:.1f}/100")
        print(f"  ✅ Qualification Score: {assessment.qualification_score:.1f}/100")
        print(f"  ⚡ Urgency Score: {assessment.urgency_score:.1f}/100")
        print(f"  🎯 Conversion Probability: {assessment.conversion_probability:.1%}")

        if assessment.estimated_time_to_close:
            print(f"  📅 Estimated Time to Close: {assessment.estimated_time_to_close} days")

        if assessment.risk_factors:
            print(f"  ⚠️  Risk Factors: {', '.join(assessment.risk_factors)}")

        if assessment.growth_opportunities:
            print(f"  📈 Growth Opportunities: {', '.join(assessment.growth_opportunities)}")

        print()

    def _display_next_best_actions(self, actions):
        """Display next best actions"""
        print(f"🎯 NEXT BEST ACTIONS")

        if not actions:
            print("  No specific actions recommended")
            return

        for action in actions:
            print(f"  {action['priority']}. {action['action']}")
            print(f"     📊 Confidence: {action['confidence']:.2f}")
            print(f"     ⚡ Urgency: {action['urgency']}/5")
            print(f"     📈 Impact: {action['estimated_impact'].title()}")

        print()

    def _validate_insight(self, insight, expected):
        """Validate insight against expected results"""
        score = 0
        total = 100

        # Type validation (30 points)
        if insight.insight_type.value == expected.get("type"):
            score += 30

        # Priority validation (30 points)
        expected_priority = expected.get("priority_range", [0, 100])
        if expected_priority[0] <= insight.priority_score <= expected_priority[1]:
            score += 30

        # Confidence validation (20 points)
        expected_confidence = expected.get("min_confidence", 0)
        if insight.ml_confidence >= expected_confidence:
            score += 20

        # Urgency validation (20 points)
        expected_urgency = expected.get("urgency_range", [1, 5])
        if expected_urgency[0] <= insight.urgency_level <= expected_urgency[1]:
            score += 20

        return score

    async def _run_performance_demo(self):
        """Run performance benchmarks"""
        print("📊 PERFORMANCE BENCHMARK DEMO")
        print("-" * 50)

        # Test concurrent processing
        print("🚀 Testing concurrent lead analysis...")

        conversations = []
        for i in range(10):
            conversations.append({
                "lead_id": f"perf_test_lead_{i:03d}",
                "conversation_data": {
                    "id": f"perf_conv_{i:03d}",
                    "messages": [
                        {"content": f"Performance test message {i}", "timestamp": datetime.now().isoformat()}
                    ]
                }
            })

        start_time = time.time()

        # Process all conversations concurrently
        analysis_tasks = [
            self.service.analyze_lead_realtime(
                lead_id=conv["lead_id"],
                conversation_data=conv["conversation_data"]
            )
            for conv in conversations
        ]

        insights = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        total_time = (time.time() - start_time) * 1000
        avg_time = total_time / len(conversations)

        # Results
        successful_analyses = len([i for i in insights if not isinstance(i, Exception)])
        print(f"✅ Processed {successful_analyses}/{len(conversations)} conversations")
        print(f"⚡ Total time: {total_time:.1f}ms")
        print(f"📊 Average time per lead: {avg_time:.1f}ms")
        print(f"🎯 Performance target: <50ms (Met: {'✅' if avg_time < 50 else '❌'})")

        print()

        # Test individual performance targets
        test_conversation = {
            "id": "perf_test_individual",
            "messages": [{"content": "Individual performance test", "timestamp": datetime.now().isoformat()}]
        }

        # Real-time analysis performance
        start_time = time.time()
        await self.service.analyze_lead_realtime("perf_individual", test_conversation)
        analysis_time = (time.time() - start_time) * 1000

        # Health assessment performance
        start_time = time.time()
        await self.service.assess_lead_health("perf_individual")
        health_time = (time.time() - start_time) * 1000

        # Next best actions performance
        start_time = time.time()
        await self.service.get_next_best_actions("perf_individual", test_conversation)
        actions_time = (time.time() - start_time) * 1000

        print("🎯 INDIVIDUAL PERFORMANCE RESULTS")
        print(f"  📊 Real-time Analysis: {analysis_time:.1f}ms (target: <50ms) {'✅' if analysis_time < 50 else '❌'}")
        print(f"  🏥 Health Assessment: {health_time:.1f}ms (target: <100ms) {'✅' if health_time < 100 else '❌'}")
        print(f"  🎯 Next Best Actions: {actions_time:.1f}ms (target: <75ms) {'✅' if actions_time < 75 else '❌'}")

        print()

    async def _run_health_check(self):
        """Run service health check"""
        print("🏥 SERVICE HEALTH CHECK")
        print("-" * 50)

        try:
            health_status = await self.service.health_check()

            print(f"Overall Status: {'🟢 Healthy' if health_status['healthy'] else '🔴 Unhealthy'}")
            print(f"Service: {health_status['service']}")
            print(f"Version: {health_status['version']}")

            print("\nDependent Services:")
            for service_name, status in health_status['checks'].items():
                service_status = '🟢' if status.get('healthy', False) else '🔴'
                print(f"  {service_status} {service_name.title()}")

            print("\nPerformance Targets:")
            for target, value in health_status['performance_targets'].items():
                print(f"  🎯 {target.replace('_', ' ').title()}: {value}")

        except Exception as e:
            print(f"❌ Health check failed: {e}")

        print()

    async def _setup_demo_mocks(self):
        """Setup mocked services for demo when real services unavailable"""
        from unittest.mock import AsyncMock, MagicMock

        # Mock Redis client
        self.service.redis_client = MagicMock()
        self.service.redis_client.optimized_get = AsyncMock(return_value=None)
        self.service.redis_client.optimized_set = AsyncMock(return_value=True)
        self.service.redis_client.health_check = AsyncMock(return_value={"healthy": True})

        # Mock ML service
        self.service.ml_service = MagicMock()
        self.service.ml_service.predict_batch = AsyncMock(return_value=[
            MagicMock(success=True, request_id="mock_sentiment", predictions={"sentiment": 0.7}),
            MagicMock(success=True, request_id="mock_intent", predictions={"intents": {"buying": 0.8}}),
            MagicMock(success=True, request_id="mock_urgency", predictions={"urgency": 0.6})
        ])
        self.service.ml_service.predict_single = AsyncMock(return_value=MagicMock(
            success=True, predictions={"actions": ["Schedule call", "Send information"]}
        ))
        self.service.ml_service.health_check = AsyncMock(return_value={"healthy": True})

        # Mock database cache
        self.service.db_cache = MagicMock()
        self.service.db_cache.cached_query = AsyncMock(return_value=[])
        self.service.db_cache.health_check = AsyncMock(return_value={"healthy": True})

        # Mock HTTP client
        self.service.http_client = MagicMock()
        self.service.http_client.health_check = AsyncMock(return_value={"healthy": True})

    async def _cleanup(self):
        """Cleanup demo resources"""
        print("🧹 Cleaning up demo resources...")
        try:
            await self.service.cleanup()
            print("✅ Cleanup completed successfully")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

    def _create_demo_scenarios(self):
        """Create demo scenarios for different lead types"""
        return [
            {
                "name": "High Urgency Lead",
                "lead_id": "demo_urgent_001",
                "conversation_data": {
                    "id": "urgent_conversation",
                    "messages": [
                        {
                            "content": "Hi! I need to find a house IMMEDIATELY. My lease expires next week and I haven't found anything yet!",
                            "timestamp": "2024-01-10T09:00:00Z"
                        },
                        {
                            "content": "I'm losing my security deposit if I don't find something by Friday. This is urgent!",
                            "timestamp": "2024-01-10T09:05:00Z"
                        },
                        {
                            "content": "I'm pre-approved for $400k and can close in 2 weeks. Please help me find something today!",
                            "timestamp": "2024-01-10T09:10:00Z"
                        },
                        {
                            "content": "I can be flexible on location but need 2+ bedrooms. My timeline is critical!",
                            "timestamp": "2024-01-10T09:15:00Z"
                        }
                    ]
                },
                "context": {"channel": "website_chat", "referral_source": "google"},
                "expected_insight": {
                    "type": "urgency",
                    "priority_range": [80, 100],
                    "min_confidence": 0.7,
                    "urgency_range": [1, 2]
                },
                "historical_data": {
                    "previous_searches": 15,
                    "properties_viewed": 8,
                    "email_opens": 12
                }
            },
            {
                "name": "Strong Buying Intent Lead",
                "lead_id": "demo_buyer_002",
                "conversation_data": {
                    "id": "buyer_conversation",
                    "messages": [
                        {
                            "content": "I absolutely love the property at 123 Oak Street! It's exactly what I've been looking for.",
                            "timestamp": "2024-01-10T14:00:00Z"
                        },
                        {
                            "content": "I'm ready to make an offer and can put down 20%. When can we schedule a showing?",
                            "timestamp": "2024-01-10T14:05:00Z"
                        },
                        {
                            "content": "My financing is already approved and I can be flexible on the closing date.",
                            "timestamp": "2024-01-10T14:10:00Z"
                        },
                        {
                            "content": "I've been house hunting for 6 months and this is THE ONE. Let's move quickly!",
                            "timestamp": "2024-01-10T14:15:00Z"
                        }
                    ]
                },
                "context": {"channel": "email", "property_id": "prop_123_oak"},
                "expected_insight": {
                    "type": "buying_intent",
                    "priority_range": [70, 100],
                    "min_confidence": 0.8,
                    "urgency_range": [1, 3]
                },
                "historical_data": {
                    "properties_viewed": 25,
                    "showings_attended": 8,
                    "offer_attempts": 2
                }
            },
            {
                "name": "Price Objection Lead",
                "lead_id": "demo_objection_003",
                "conversation_data": {
                    "id": "objection_conversation",
                    "messages": [
                        {
                            "content": "The properties you showed me are all over my budget. These prices seem too high for what you get.",
                            "timestamp": "2024-01-10T16:00:00Z"
                        },
                        {
                            "content": "I was hoping to stay under $300k but everything decent seems to be $350k+. Are there any options?",
                            "timestamp": "2024-01-10T16:05:00Z"
                        },
                        {
                            "content": "I've seen similar properties in other areas for much less. Can we negotiate on any of these?",
                            "timestamp": "2024-01-10T16:10:00Z"
                        },
                        {
                            "content": "I'm concerned I'm being priced out of this market. What are my realistic options?",
                            "timestamp": "2024-01-10T16:15:00Z"
                        }
                    ]
                },
                "context": {"channel": "phone_call", "budget_range": "250-300k"},
                "expected_insight": {
                    "type": "objection",
                    "priority_range": [60, 90],
                    "min_confidence": 0.6,
                    "urgency_range": [2, 4]
                },
                "historical_data": {
                    "properties_viewed": 12,
                    "budget_revisions": 3,
                    "saved_searches": 5
                }
            },
            {
                "name": "Casual Browser Lead",
                "lead_id": "demo_browser_004",
                "conversation_data": {
                    "id": "browser_conversation",
                    "messages": [
                        {
                            "content": "Hi, just looking around at what's available in the area. Not in any rush.",
                            "timestamp": "2024-01-10T11:00:00Z"
                        },
                        {
                            "content": "The market seems interesting. Tell me about the neighborhood trends.",
                            "timestamp": "2024-01-10T11:30:00Z"
                        },
                        {
                            "content": "I might be interested in buying in the next year or so. Just getting a feel for prices.",
                            "timestamp": "2024-01-10T12:00:00Z"
                        }
                    ]
                },
                "context": {"channel": "website", "session_duration": 1200},
                "expected_insight": {
                    "type": "engagement",
                    "priority_range": [20, 50],
                    "min_confidence": 0.4,
                    "urgency_range": [4, 5]
                },
                "historical_data": {
                    "site_visits": 3,
                    "pages_viewed": 15,
                    "time_on_site": 3600
                }
            }
        ]


async def main():
    """Main demo function"""
    demo = LeadIntelligenceDemo()
    await demo.run_demo()


if __name__ == "__main__":
    print("🎯 Enhanced Real-Time Lead Intelligence Demo")
    print("=" * 80)
    print("This demo showcases the performance-optimized lead intelligence service")
    print("with real-world scenarios and advanced AI-powered analysis.")
    print()

    asyncio.run(main())