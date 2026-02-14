#!/usr/bin/env python3
"""
Mock objects for external services used in Service 6 testing.

Provides realistic mocks for:
- Claude API responses
- Redis cache operations
- Database connections
- Apollo API calls
- Twilio SMS/Voice
- SendGrid email
- GoHighLevel webhooks
"""

import asyncio
import json
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from unittest.mock import AsyncMock, MagicMock

import pytest
from freezegun import freeze_time

# Import the actual response types for proper mocking
from ghl_real_estate_ai.services.service6_ai_integration import (
    CallAnalysis,
    InferenceResponse,
    MLScoringResult,
    RequestPriority,
    Service6AIResponse,
)


class MockClaudeClient:
    """Mock Claude API client for testing"""

    def __init__(self, response_delay: float = 0.1):
        self.response_delay = response_delay
        self.call_count = 0
        self.last_request = None

    async def generate(self, prompt: str, **kwargs) -> str:
        """Mock Claude text generation"""
        await asyncio.sleep(self.response_delay)
        self.call_count += 1
        self.last_request = {"prompt": prompt, "kwargs": kwargs}

        # Return realistic responses based on prompt content
        if "lead analysis" in prompt.lower():
            return self._generate_lead_analysis_response()
        elif "property match" in prompt.lower():
            return self._generate_property_match_response()
        elif "conversation" in prompt.lower():
            return self._generate_conversation_response()
        else:
            return "This is a mock Claude response for testing purposes."

    def _generate_lead_analysis_response(self) -> str:
        return """Based on the lead data analysis:

**Key Insights:**
- High engagement lead with 85% email open rate
- Budget of $550K aligns with viewed properties ($525K-$580K range)
- Fast response time (3.5 hours avg) indicates strong interest
- Active searcher with 15 page views and multiple location searches

**Immediate Actions:**
1. Schedule property viewing for North Rancho Cucamonga properties
2. Send personalized neighborhood analysis
3. Provide school district information for searched areas

**Strategic Recommendations:**
- Focus on move-in ready properties in the $530K-$570K range
- Emphasize proximity to good schools
- Highlight market timing advantages

**Risk Factors:**
- None identified - strong conversion signals

**Opportunity Signals:**
- Ready to move timeline suggests urgency
- Budget pre-approved based on viewing patterns
- High engagement across multiple touchpoints"""

    def _generate_property_match_response(self) -> str:
        return """Property Match Analysis:

This 3-bedroom home at $545K in North Rancho Cucamonga is an excellent fit because:
- Matches their $550K budget perfectly
- Located in highly-rated Round Rock ISD
- Move-in ready condition aligns with 'soon' timeline
- Similar to previously viewed properties in price range"""

    def _generate_conversation_response(self) -> str:
        return """Based on current market conditions and your timeline, I'd recommend moving forward now. Here's why:

Interest rates are showing signs of stabilization, and inventory in North Rancho Cucamonga remains competitive. With your pre-approved budget and the excellent schools you're prioritizing, waiting could mean fewer options.

The properties you've been viewing are well-positioned, and given your active search pattern, I can help you structure a competitive offer that protects your interests while moving quickly on the right opportunity."""


class MockRedisClient:
    """Mock Redis client for caching tests"""

    def __init__(self):
        self._storage = {}
        self._ttl = {}
        self.operation_count = 0

    async def get(self, key: str) -> Optional[str]:
        self.operation_count += 1

        # Check if key has expired
        if key in self._ttl and datetime.now() > self._ttl[key]:
            del self._storage[key]
            del self._ttl[key]
            return None

        return self._storage.get(key)

    async def set(self, key: str, value: str, ttl: Optional[int] = None) -> bool:
        self.operation_count += 1
        self._storage[key] = value

        if ttl:
            self._ttl[key] = datetime.now() + timedelta(seconds=ttl)

        return True

    async def delete(self, key: str) -> bool:
        self.operation_count += 1
        if key in self._storage:
            del self._storage[key]
            if key in self._ttl:
                del self._ttl[key]
            return True
        return False

    async def exists(self, key: str) -> bool:
        self.operation_count += 1
        return key in self._storage

    def clear(self):
        """Clear all stored data - useful for test isolation"""
        self._storage.clear()
        self._ttl.clear()
        self.operation_count = 0


class MockDatabaseService:
    """Mock database service for testing"""

    def __init__(self):
        self._leads = {}
        self._analytics = {}
        self.operation_count = 0

    async def get_lead(self, lead_id: str) -> Optional[Dict[str, Any]]:
        self.operation_count += 1
        return self._leads.get(lead_id)

    async def save_lead(self, lead_id: str, lead_data: Dict[str, Any]) -> bool:
        self.operation_count += 1
        self._leads[lead_id] = {**lead_data, "updated_at": datetime.now().isoformat()}
        return True

    async def update_lead_score(self, lead_id: str, score: float, analysis_data: Dict[str, Any]) -> bool:
        self.operation_count += 1
        if lead_id in self._leads:
            self._leads[lead_id].update(
                {"ai_score": score, "ai_analysis": analysis_data, "scored_at": datetime.now().isoformat()}
            )
            return True
        return False

    async def save_analytics(self, analytics_id: str, data: Dict[str, Any]) -> bool:
        self.operation_count += 1
        self._analytics[analytics_id] = data
        return True

    async def get_lead_history(self, lead_id: str) -> List[Dict[str, Any]]:
        self.operation_count += 1
        # Return mock historical data
        return [
            {
                "timestamp": "2026-01-15T10:00:00Z",
                "action": "email_open",
                "details": {"subject": "North Rancho Cucamonga Properties"},
            },
            {
                "timestamp": "2026-01-15T14:30:00Z",
                "action": "property_view",
                "details": {"property_id": "prop_123", "price": 545000},
            },
            {
                "timestamp": "2026-01-16T09:15:00Z",
                "action": "message_sent",
                "details": {"content": "What about schools in the area?"},
            },
        ]


class MockApolloClient:
    """Mock Apollo API client for lead enrichment"""

    def __init__(self):
        self.api_calls = []
        self.rate_limit_remaining = 1000

    async def enrich_lead(self, email: str, phone: str = None) -> Dict[str, Any]:
        self.api_calls.append(
            {
                "endpoint": "enrich_lead",
                "params": {"email": email, "phone": phone},
                "timestamp": datetime.now().isoformat(),
            }
        )

        self.rate_limit_remaining -= 1

        # Simulate API rate limiting
        if self.rate_limit_remaining <= 0:
            raise Exception("Apollo API rate limit exceeded")

        # Return mock enriched data
        return {
            "email": email,
            "first_name": "Sarah",
            "last_name": "Johnson",
            "company": "Tech Solutions Inc",
            "title": "Software Engineer",
            "linkedin_url": "https://linkedin.com/in/sarahj",
            "location": "Rancho Cucamonga, CA",
            "estimated_income": 120000,
            "homeowner": True,
            "confidence_score": 0.92,
        }

    async def search_companies(self, ontario_mills: str) -> Dict[str, Any]:
        self.api_calls.append(
            {"endpoint": "search_companies", "params": {"ontario_mills": ontario_mills}, "timestamp": datetime.now().isoformat()}
        )

        return {
            "company_name": "Tech Solutions Inc",
            "industry": "Software Development",
            "size": "100-500 employees",
            "revenue": "$10M-$50M",
            "location": "Rancho Cucamonga, CA",
        }


class MockTwilioClient:
    """Mock Twilio client for SMS/Voice operations"""

    def __init__(self):
        self.sent_messages = []
        self.call_logs = []

    async def send_sms(self, to: str, message: str, from_number: str = None) -> Dict[str, Any]:
        message_data = {
            "sid": f"SM{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "to": to,
            "from": from_number or "+15551234567",
            "body": message,
            "status": "sent",
            "timestamp": datetime.now().isoformat(),
        }

        self.sent_messages.append(message_data)

        return {"success": True, "message_sid": message_data["sid"], "status": "sent"}

    async def make_call(self, to: str, from_number: str = None, twiml_url: str = None) -> Dict[str, Any]:
        call_data = {
            "sid": f"CA{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "to": to,
            "from": from_number or "+15551234567",
            "status": "initiated",
            "timestamp": datetime.now().isoformat(),
        }

        self.call_logs.append(call_data)

        return {"success": True, "call_sid": call_data["sid"], "status": "initiated"}

    async def get_call_details(self, call_sid: str) -> Dict[str, Any]:
        # Find call in logs
        call = next((c for c in self.call_logs if c["sid"] == call_sid), None)

        if not call:
            raise Exception(f"Call {call_sid} not found")

        return {
            **call,
            "duration": "120",  # seconds
            "recording_url": "https://api.twilio.com/recordings/xyz.mp3",
            "transcription": "Hello, I am interested in viewing the property...",
        }


class MockSendGridClient:
    """Mock SendGrid client for email operations"""

    def __init__(self):
        self.sent_emails = []
        self.email_stats = {"delivered": 0, "opened": 0, "clicked": 0, "bounced": 0}

    async def send_email(
        self,
        to_email: str,
        subject: str,
        content: str = None,
        html_content: str = None,
        plain_content: str = None,
        from_email: str = None,
        template_id: str = None,
        lead_id: str = None,
        campaign_id: str = None,
        attachments: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        email_data = {
            "message_id": f"sg_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "to": to_email,
            "from": from_email or "noreply@enterprisehub.ai",
            "subject": subject,
            "content": content,
            "html_content": html_content,
            "plain_content": plain_content,
            "template_id": template_id,
            "lead_id": lead_id,
            "campaign_id": campaign_id,
            "attachments": attachments or [],
            "status": "sent",
            "timestamp": datetime.now().isoformat(),
        }

        self.sent_emails.append(email_data)
        self.email_stats["delivered"] += 1

        return {"success": True, "message_id": email_data["message_id"], "status": "sent"}

    async def track_email_events(self, message_id: str) -> List[Dict[str, Any]]:
        # Simulate email tracking events
        events = []

        # Delivered event
        events.append({"event": "delivered", "timestamp": datetime.now().isoformat(), "message_id": message_id})

        # Simulate random opens/clicks
        import random

        if random.random() < 0.7:  # 70% open rate
            events.append({"event": "open", "timestamp": datetime.now().isoformat(), "message_id": message_id})
            self.email_stats["opened"] += 1

            if random.random() < 0.3:  # 30% click rate
                events.append(
                    {
                        "event": "click",
                        "timestamp": datetime.now().isoformat(),
                        "message_id": message_id,
                        "url": "https://enterprisehub.ai/properties/rancho_cucamonga",
                    }
                )
                self.email_stats["clicked"] += 1

        return events


class MockWebhookPayloads:
    """Mock webhook payloads for testing signature validation"""

    @staticmethod
    def ghl_lead_webhook(lead_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate mock GHL lead webhook payload"""
        default_data = {
            "id": "lead_123456789",
            "email": "test.lead@example.com",
            "firstName": "John",
            "lastName": "Doe",
            "phone": "+15551234567",
            "source": "Website Form",
            "customFields": {"budget": "500000", "timeline": "soon", "location": "Rancho Cucamonga"},
        }

        return {
            "type": "ContactCreate",
            "timestamp": datetime.now().isoformat(),
            "objectType": "contact",
            "data": {**default_data, **(lead_data or {})},
        }

    @staticmethod
    def twilio_voice_webhook(call_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate mock Twilio voice webhook payload"""
        default_data = {
            "CallSid": "CA1234567890abcdef",
            "From": "+15551234567",
            "To": "+15559876543",
            "CallStatus": "completed",
            "Direction": "inbound",
            "Duration": "180",
        }

        return {**default_data, **(call_data or {})}

    @staticmethod
    def sendgrid_event_webhook(event_data: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate mock SendGrid event webhook payload"""
        default_events = [
            {
                "email": "test@example.com",
                "event": "delivered",
                "timestamp": int(datetime.now().timestamp()),
                "sg_message_id": "sendgrid_message_123",
            },
            {
                "email": "test@example.com",
                "event": "open",
                "timestamp": int(datetime.now().timestamp()),
                "sg_message_id": "sendgrid_message_123",
            },
        ]

        return event_data or default_events

    @staticmethod
    def apollo_webhook(enrichment_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate mock Apollo enrichment webhook payload"""
        default_data = {
            "person_id": "apollo_person_123",
            "email": "enriched@example.com",
            "first_name": "Jane",
            "last_name": "Smith",
            "organization": {"name": "Example Corp", "industry": "Technology"},
        }

        return {"event_type": "person_enriched", "data": {**default_data, **(enrichment_data or {})}}


class MockSignatureValidator:
    """Mock webhook signature validation"""

    def __init__(self, valid_signature: str = "valid_signature_hash"):
        self.valid_signature = valid_signature
        self.validation_calls = []

    def validate_ghl_signature(self, payload: str, signature: str) -> bool:
        self.validation_calls.append(
            {
                "service": "ghl",
                "payload_length": len(payload),
                "signature": signature,
                "timestamp": datetime.now().isoformat(),
            }
        )
        return signature == self.valid_signature

    def validate_twilio_signature(self, payload: str, signature: str, url: str) -> bool:
        self.validation_calls.append(
            {
                "service": "twilio",
                "payload_length": len(payload),
                "signature": signature,
                "url": url,
                "timestamp": datetime.now().isoformat(),
            }
        )
        return signature == self.valid_signature

    def validate_sendgrid_signature(self, payload: str, signature: str, timestamp: str) -> bool:
        self.validation_calls.append(
            {"service": "sendgrid", "payload_length": len(payload), "signature": signature, "timestamp": timestamp}
        )
        return signature == self.valid_signature


# Test data factories
def create_test_lead_data(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create realistic test lead data"""
    default_data = {
        "lead_id": "test_lead_001",
        "name": "Sarah Johnson",
        "email": "sarah.j@example.com",
        "phone": "+1-555-0123",
        "budget": 550000,
        "timeline": "soon",
        "location": "North Rancho Cucamonga",
        "email_open_rate": 0.85,
        "email_click_rate": 0.42,
        "avg_response_time_hours": 3.5,
        "avg_message_length": 180,
        "page_views": 15,
        "searched_locations": ["North Rancho Cucamonga", "Round Rock", "Cedar Park"],
        "viewed_property_prices": [525000, 545000, 560000, 580000],
        "messages_per_day": 1.8,
        "questions_asked": 4,
        "last_interaction": "2026-01-16T10:30:00Z",
        "source": "website_form",
        "created_at": "2026-01-10T14:20:00Z",
    }

    if overrides:
        default_data.update(overrides)

    return default_data


def _create_mock_feature_vector():
    """Create a mock MLFeatureVector with realistic test data"""
    from ghl_real_estate_ai.services.advanced_ml_lead_scoring_engine import MLFeatureVector

    return MLFeatureVector(
        email_open_rate=0.85,
        email_click_rate=0.42,
        response_velocity=3.5,
        conversation_depth=180.0,
        engagement_consistency=0.15,
        property_view_frequency=2.5,
        search_refinement_count=4,
        price_range_stability=0.85,
        location_focus_score=0.78,
        timing_urgency_signals=0.72,
        budget_clarity_score=0.88,
        financial_readiness=0.82,
        price_sensitivity=0.45,
        affordability_ratio=0.92,
        question_sophistication=0.75,
        decision_maker_confidence=0.80,
        family_situation_clarity=0.70,
        relocation_urgency=0.65,
        previous_interactions=5,
        conversion_funnel_stage=0.60,
        seasonal_patterns=0.50,
        market_conditions_score=0.72,
        communication_style_score=0.78,
        technical_sophistication=0.65,
        local_market_knowledge=0.55,
        data_completeness=0.90,
        recency_weight=0.95,
    )


def create_mock_ml_scoring_result(lead_id: str = "test_lead_001") -> MLScoringResult:
    """Create mock ML scoring result"""
    return MLScoringResult(
        lead_id=lead_id,
        timestamp=datetime.now(),
        conversion_probability=82.5,
        intent_strength=78.0,
        timing_urgency=65.0,
        financial_readiness=88.0,
        engagement_quality=85.0,
        final_ml_score=85.5,
        confidence_interval=(82.1, 88.9),
        prediction_uncertainty=3.4,
        top_features=[{"budget_alignment": 0.3}, {"engagement_rate": 0.25}, {"timeline": 0.2}],
        feature_vector=_create_mock_feature_vector(),
        model_version="v2.1.0",
        prediction_latency_ms=145.7,
        ensemble_agreement=0.92,
        recommended_actions=[
            "Schedule property viewing within 48 hours",
            "Send personalized market analysis",
            "Provide pre-approval guidance",
        ],
        optimal_contact_time=None,
        expected_conversion_timeline="1-2 weeks",
        risk_factors=["High competition in price range"],
        opportunity_signals=["Fast response time", "Multiple property views", "Budget pre-qualified"],
    )


def create_mock_service6_response(lead_id: str = "test_lead_001") -> Service6AIResponse:
    """Create complete mock Service6AIResponse"""
    return Service6AIResponse(
        operation_id=f"s6_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{lead_id}",
        lead_id=lead_id,
        timestamp=datetime.now(),
        ml_scoring_result=create_mock_ml_scoring_result(lead_id),
        voice_analysis_result=None,
        predictive_insights={"confidence_score": 0.88, "conversion_probability": 0.82},
        personalized_content=None,
        unified_lead_score=86.2,
        confidence_level=0.87,
        priority_level="high",
        immediate_actions=["Schedule property viewing", "Send market analysis", "Provide school information"],
        strategic_recommendations=[
            "Focus on move-in ready properties",
            "Emphasize North Rancho Cucamonga locations",
            "Highlight investment potential",
        ],
        risk_alerts=[],
        opportunity_signals=["High engagement lead", "Budget aligned with market", "Ready to move timeline"],
        processing_time_ms=234.5,
        models_used=["advanced_ml_scorer", "predictive_analytics"],
        data_sources=["lead_data", "behavioral_features", "historical_patterns"],
        enhanced_claude_integration=True,
        realtime_inference_active=True,
        voice_ai_enabled=False,
    )


# Service 6 Specific Mock Services
class MockMLScoringEngine:
    """Mock Machine Learning Scoring Engine for Service 6"""

    def __init__(self):
        self.scoring_calls = []
        self.performance_metrics = {"success_rate": 0.95, "avg_latency_ms": 120, "requests_processed": 1500}
        self.failure_mode = False
        self.mock_response_data = {}

    def setup_mock_response(self, response_data: Dict[str, Any]):
        """Configure mock response data"""
        self.mock_response_data = response_data

    def setup_failure_mode(self, enabled: bool):
        """Enable/disable failure mode for testing"""
        self.failure_mode = enabled

    def setup_health_metrics(self, metrics: Dict[str, Any]):
        """Configure health metrics"""
        self.performance_metrics.update(metrics)

    async def score_lead_comprehensive(self, lead_id: str, lead_data: Dict[str, Any]) -> MLScoringResult:
        """Mock comprehensive lead scoring"""
        self.scoring_calls.append(
            {"lead_id": lead_id, "timestamp": datetime.now().isoformat(), "data_keys": list(lead_data.keys())}
        )

        if self.failure_mode:
            raise Exception("ML scoring engine is in failure mode")

        # Use mock response data if available
        score_data = (
            self.mock_response_data
            if self.mock_response_data
            else {
                "final_ml_score": 85.5,
                "confidence_interval": [82.1, 88.9],
                "recommended_actions": ["Schedule showing", "Send market analysis"],
                "risk_factors": ["Budget concerns"],
                "opportunity_signals": ["High engagement"],
            }
        )

        return MLScoringResult(
            lead_id=lead_id,
            final_ml_score=score_data.get("final_ml_score", 85.5),
            confidence_interval=tuple(score_data.get("confidence_interval", [82.1, 88.9])),
            feature_importance={"budget": 0.3, "engagement": 0.25, "timeline": 0.2},
            model_version="mock_v1.0.0",
            recommended_actions=score_data.get("recommended_actions", ["Test action"]),
            risk_factors=score_data.get("risk_factors", []),
            opportunity_signals=score_data.get("opportunity_signals", []),
            processing_time_ms=125.0,
        )

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Return performance metrics"""
        return self.performance_metrics


class MockVoiceAIClient:
    """Mock Voice AI Integration for Service 6"""

    def __init__(self):
        self.call_analyses = []
        self.active_calls = {}
        self.performance_metrics = {"success_rate": 0.92, "avg_transcription_accuracy": 0.94, "calls_processed": 450}
        self.start_call_analysis_called = False
        self.failure_mode = False

    def setup_call_analysis_success(self, success: bool):
        """Configure call analysis success/failure"""
        self.start_call_analysis_called = False  # Reset flag

    def setup_failure_mode(self, enabled: bool):
        """Enable/disable failure mode"""
        self.failure_mode = enabled

    async def start_call_analysis(self, call_id: str, lead_id: str, agent_id: str) -> bool:
        """Mock start call analysis"""
        self.start_call_analysis_called = True

        if self.failure_mode:
            return False

        self.active_calls[call_id] = {
            "lead_id": lead_id,
            "agent_id": agent_id,
            "started_at": datetime.now().isoformat(),
            "status": "active",
        }

        return True

    async def process_audio_stream(self, call_id: str, audio_chunk: bytes, speaker_id: str) -> Dict[str, Any]:
        """Mock audio stream processing"""
        if self.failure_mode:
            return {"error": "Voice AI processing failed"}

        return {
            "call_id": call_id,
            "speaker_id": speaker_id,
            "transcript_segment": "This is a mock transcription segment",
            "sentiment": "positive",
            "intent": "information_seeking",
            "confidence": 0.89,
        }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Return performance metrics"""
        return self.performance_metrics


class MockPredictiveAnalytics:
    """Mock Predictive Analytics Engine for Service 6"""

    def __init__(self):
        self.analysis_calls = []
        self.performance_metrics = {"system_health": "healthy", "prediction_accuracy": 0.87, "analyses_completed": 2100}
        self.failure_mode = False
        self.mock_response_data = {}

    def setup_mock_response(self, response_data: Dict[str, Any]):
        """Configure mock response data"""
        self.mock_response_data = response_data

    def setup_failure_mode(self, enabled: bool):
        """Enable/disable failure mode"""
        self.failure_mode = enabled

    async def run_comprehensive_analysis(
        self, lead_data: Dict[str, Any], historical_context: List[Dict]
    ) -> Dict[str, Any]:
        """Mock comprehensive predictive analysis"""
        self.analysis_calls.append(
            {
                "timestamp": datetime.now().isoformat(),
                "data_keys": list(lead_data.keys()),
                "history_length": len(historical_context),
            }
        )

        if self.failure_mode:
            raise Exception("Predictive analytics is in failure mode")

        # Use mock response data if configured
        if self.mock_response_data:
            return self.mock_response_data

        return {
            "confidence_score": 0.85,
            "analysis_duration_seconds": 2.3,
            "behavioral_patterns": [
                {"pattern": "high_engagement", "confidence": 0.92},
                {"pattern": "budget_qualified", "confidence": 0.87},
            ],
            "comprehensive_insights": {
                "actions": ["Send premium listings", "Schedule call"],
                "risks": ["Market competition"],
                "opportunities": ["Investment potential", "Quick timeline"],
            },
            "conversion_probability": 0.78,
            "churn_risk": 0.15,
        }

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Return performance metrics"""
        return self.performance_metrics

    # Add content personalization mock
    class ContentPersonalizationMock:
        async def generate_personalized_content(self, lead_id: str, lead_data: Dict[str, Any], content_type: str):
            """Mock content personalization"""
            return type(
                "PersonalizedContent",
                (),
                {
                    "content_type": content_type,
                    "personalized_message": f"Personalized {content_type} for {lead_id}",
                    "engagement_probability": 0.72,
                    "personalization_factors": ["budget", "location", "timeline"],
                },
            )()

    def __init__(self):
        super().__init__()
        self.content_personalization = self.ContentPersonalizationMock()


class MockRealTimeInferenceEngine:
    """Mock Real-time Inference Engine for Service 6"""

    def __init__(self):
        self.inference_calls = []
        self.system_status = {
            "status": "healthy",
            "performance": {"avg_latency_ms": 45, "throughput_rps": 150, "success_rate": 0.98},
        }
        self.failure_mode = False

    def setup_failure_mode(self, enabled: bool):
        """Enable/disable failure mode"""
        self.failure_mode = enabled

    async def start(self):
        """Mock engine startup"""
        if self.failure_mode:
            raise Exception("Failed to start real-time inference engine")

    async def predict(self, request) -> InferenceResponse:
        """Mock inference prediction"""
        self.inference_calls.append(
            {
                "request_id": request.request_id,
                "lead_id": request.lead_id,
                "timestamp": datetime.now().isoformat(),
                "features": list(request.features.keys()) if hasattr(request, "features") else [],
            }
        )

        if self.failure_mode:
            raise Exception("Inference engine prediction failed")

        from ghl_real_estate_ai.services.realtime_inference_engine import InferenceResponse

        return InferenceResponse(
            request_id=request.request_id,
            lead_id=request.lead_id,
            model_id="mock_model_v1.0",
            model_version="1.0.0",
            scores={"primary": 82.5, "engagement": 0.87, "conversion": 0.74},
            primary_score=82.5,
            confidence=0.89,
            prediction_class="qualified_lead",
            feature_importance={"budget": 0.3, "engagement": 0.25},
            reasoning=["High budget alignment", "Strong engagement signals"],
            risk_factors=["Market competition"],
            opportunities=["Quick timeline", "Budget qualified"],
            processed_at=datetime.now(),
            processing_time_ms=47.2,
            model_latency_ms=35.1,
            cache_hit=False,
            data_quality_score=0.92,
            prediction_uncertainty=0.11,
            requires_human_review=False,
        )

    async def get_system_status(self) -> Dict[str, Any]:
        """Return system status"""
        return self.system_status


# Enhanced mock cache service with Service 6 specific functionality
class MockTieredCacheService(MockRedisClient):
    """Enhanced cache service mock for Service 6 tiered caching"""

    def __init__(self):
        super().__init__()
        self.cache_layers = {"memory": {}, "redis": {}, "database": {}}
        self.cache_hits = {"memory": 0, "redis": 0, "database": 0}
        self.cache_misses = 0
        self.set_called = False
        self.last_set_key = None
        self.last_set_data = None
        self.get_response = None
        self.update_called = False
        self.last_update_data = None

    def setup_get_response(self, key: str, response_data: Any):
        """Configure specific get response"""
        self.get_response = response_data
        self._storage[key] = (
            json.dumps(response_data) if isinstance(response_data, (dict, list)) else str(response_data)
        )

    async def get_from_layer(self, key: str, layer: str) -> Optional[Any]:
        """Mock layered cache get"""
        if layer in self.cache_layers and key in self.cache_layers[layer]:
            self.cache_hits[layer] += 1
            return self.cache_layers[layer][key]

        self.cache_misses += 1
        return None

    async def set_in_layer(self, key: str, value: Any, layer: str, ttl: Optional[int] = None) -> bool:
        """Mock layered cache set"""
        self.set_called = True
        self.last_set_key = key
        self.last_set_data = value

        self.cache_layers[layer][key] = value
        return True

    async def invalidate_key(self, key: str) -> bool:
        """Mock cache invalidation across all layers"""
        invalidated = False
        for layer in self.cache_layers:
            if key in self.cache_layers[layer]:
                del self.cache_layers[layer][key]
                invalidated = True
        return invalidated

    def get_cache_stats(self) -> Dict[str, Any]:
        """Return cache performance statistics"""
        total_hits = sum(self.cache_hits.values())
        total_requests = total_hits + self.cache_misses

        return {
            "hit_rate": total_hits / total_requests if total_requests > 0 else 0,
            "layer_hits": self.cache_hits.copy(),
            "misses": self.cache_misses,
            "total_requests": total_requests,
        }


class MockEnhancedDatabaseService(MockDatabaseService):
    """Enhanced database service mock for Service 6"""

    def __init__(self):
        super().__init__()
        self.lead_scores = {}
        self.ai_analyses = {}
        self.update_called = False
        self.last_update_data = None

    async def store_ai_analysis(self, lead_id: str, analysis_data: Service6AIResponse) -> bool:
        """Mock storing AI analysis results"""
        self.operation_count += 1
        self.ai_analyses[lead_id] = asdict(analysis_data)
        return True

    async def get_lead_ai_history(self, lead_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Mock retrieving AI analysis history"""
        self.operation_count += 1
        # Return mock historical AI analyses
        return [
            {
                "analysis_id": f"ai_analysis_{i}",
                "timestamp": (datetime.now() - timedelta(days=i)).isoformat(),
                "unified_score": 75.0 + (i * 2),
                "priority": "high" if i < 3 else "medium",
                "models_used": ["ml_scorer", "predictive"],
            }
            for i in range(min(limit, 5))
        ]

    async def update_lead_intelligence(self, lead_id: str, intelligence_data: Dict[str, Any]) -> bool:
        """Mock updating lead intelligence"""
        self.update_called = True
        self.last_update_data = intelligence_data

        if lead_id not in self._leads:
            self._leads[lead_id] = {}

        self._leads[lead_id].update(
            {"intelligence": intelligence_data, "intelligence_updated_at": datetime.now().isoformat()}
        )
        return True

    async def get_performance_analytics(self, date_range: Dict[str, str]) -> Dict[str, Any]:
        """Mock performance analytics retrieval"""
        self.operation_count += 1
        return {
            "total_analyses": 1250,
            "avg_score": 72.3,
            "score_distribution": {"high": 425, "medium": 600, "low": 225},
            "conversion_rate": 0.24,
            "avg_processing_time_ms": 185.5,
        }


# Test fixture factories for Service 6
@pytest.fixture
def mock_service6_components():
    """Provide all Service 6 mock components"""
    return {
        "ml_scoring": MockMLScoringEngine(),
        "voice_ai": MockVoiceAIClient(),
        "predictive": MockPredictiveAnalytics(),
        "inference": MockRealTimeInferenceEngine(),
        "cache": MockTieredCacheService(),
        "database": MockEnhancedDatabaseService(),
        "claude": MockClaudeClient(),
        "twilio": MockTwilioClient(),
        "sendgrid": MockSendGridClient(),
        "apollo": MockApolloClient(),
    }


@pytest.fixture
def service6_test_data():
    """Provide realistic test data for Service 6"""
    return {
        "leads": [
            create_test_lead_data({"lead_id": "high_intent_001", "budget": 650000, "timeline": "immediate"}),
            create_test_lead_data({"lead_id": "medium_intent_002", "budget": 400000, "timeline": "soon"}),
            create_test_lead_data({"lead_id": "low_intent_003", "budget": 300000, "timeline": "exploring"}),
        ],
        "features": {
            "email_open_rate": 0.75,
            "response_time_hours": 2.5,
            "page_views": 12,
            "budget": 500000,
            "timeline_urgency": 0.8,
        },
        "historical_context": [
            {"interaction": "email_open", "timestamp": "2026-01-15T10:00:00Z"},
            {"interaction": "property_view", "timestamp": "2026-01-15T14:30:00Z"},
            {"interaction": "message_sent", "timestamp": "2026-01-16T09:15:00Z"},
        ],
    }
