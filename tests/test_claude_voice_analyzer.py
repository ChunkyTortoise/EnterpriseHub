"""
Test Claude Voice Analyzer - Voice Intelligence Enhancement

Comprehensive tests for the new Claude voice analysis functionality including
real-time coaching, sentiment analysis, and call quality assessment.
"""

import asyncio
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from ghl_real_estate_ai.services.claude_voice_analyzer import (
    ClaudeVoiceAnalyzer,
    VoiceAnalysisMode,
    EmotionalTone,
    VoiceSegment,
    VoiceCoachingRecommendation,
    CallAnalysisResult
)


@pytest.fixture
def voice_analyzer():
    """Create voice analyzer instance for testing."""
    return ClaudeVoiceAnalyzer(
        location_id="test_location",
        real_time_mode=False  # Disable real-time for testing
    )


@pytest.fixture
def sample_conversation_segments():
    """Sample conversation segments for testing."""
    return [
        VoiceSegment(
            speaker="prospect",
            text="Hi, I'm looking for a three bedroom house under 500k",
            timestamp=datetime.now(),
            confidence=0.9,
            emotional_tone=EmotionalTone.INTERESTED,
            sentiment_score=0.3,
            urgency_level=0.6,
            keywords=["house", "three bedroom", "500k"],
            objections_detected=[]
        ),
        VoiceSegment(
            speaker="agent",
            text="Great! I can help you find some excellent options. What's your preferred area?",
            timestamp=datetime.now(),
            confidence=0.95,
            emotional_tone=EmotionalTone.CONFIDENT,
            sentiment_score=0.5,
            urgency_level=0.4,
            keywords=["help", "options", "area"],
            objections_detected=[]
        ),
        VoiceSegment(
            speaker="prospect",
            text="Well, the market seems really expensive right now. Not sure if we can afford it.",
            timestamp=datetime.now(),
            confidence=0.85,
            emotional_tone=EmotionalTone.HESITANT,
            sentiment_score=-0.2,
            urgency_level=0.3,
            keywords=["expensive", "afford"],
            objections_detected=["price", "trust"]
        )
    ]


class TestClaudeVoiceAnalyzer:
    """Test suite for Claude Voice Analyzer functionality."""

    def test_initialization(self, voice_analyzer):
        """Test voice analyzer initialization."""
        assert voice_analyzer.location_id == "test_location"
        assert voice_analyzer.active_calls == {}
        assert voice_analyzer.stats["calls_analyzed"] == 0
        assert not voice_analyzer.real_time_mode

    @pytest.mark.asyncio
    async def test_start_call_analysis(self, voice_analyzer):
        """Test starting voice call analysis."""
        result = await voice_analyzer.start_call_analysis(
            call_id="test_call_123",
            agent_id="agent_456",
            prospect_id="prospect_789",
            analysis_mode=VoiceAnalysisMode.LIVE_COACHING
        )

        assert result["call_id"] == "test_call_123"
        assert result["status"] == "started"
        assert "real_time_transcription" in result["features_enabled"]
        assert "test_call_123" in voice_analyzer.active_calls

        # Check call session structure
        call_session = voice_analyzer.active_calls["test_call_123"]
        assert call_session["agent_id"] == "agent_456"
        assert call_session["prospect_id"] == "prospect_789"
        assert call_session["status"] == "active"
        assert call_session["segments"] == []

    @pytest.mark.asyncio
    async def test_transcribe_audio_simulation(self, voice_analyzer):
        """Test audio transcription simulation."""
        audio_data = b"demo_audio_data"
        transcription = await voice_analyzer._transcribe_audio(audio_data)

        assert isinstance(transcription, str)
        assert len(transcription) > 0

    @pytest.mark.asyncio
    async def test_voice_characteristics_analysis(self, voice_analyzer):
        """Test voice characteristics analysis."""
        audio_data = b"demo_audio_data"
        analysis = await voice_analyzer._analyze_voice_characteristics(audio_data)

        assert "confidence" in analysis
        assert "emotional_tone" in analysis
        assert "pace" in analysis
        assert 0.0 <= analysis["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_semantic_analysis(self, voice_analyzer):
        """Test semantic analysis of voice content."""
        with patch.object(voice_analyzer.claude_semantic, 'analyze_lead_intent') as mock_analyze:
            mock_analyze.return_value = {
                "sentiment_score": 0.3,
                "urgency_score": 60,
                "keywords": ["house", "budget"],
                "confidence": 75
            }

            result = await voice_analyzer._analyze_segment_semantics(
                "Looking for a house with a budget of 500k",
                "prospect",
                "test_call"
            )

            assert result["sentiment_score"] == 0.3
            assert result["urgency_level"] == 0.6
            assert "house" in result["keywords"]

    @pytest.mark.asyncio
    async def test_objection_detection(self, voice_analyzer):
        """Test objection detection in voice segments."""
        text = "The price seems too high for our budget"
        voice_analysis = {"emotional_tone": "hesitant", "confidence": 0.8}
        semantic_analysis = {"sentiment_score": -0.4}

        objections = await voice_analyzer._detect_voice_objections(
            text, voice_analysis, semantic_analysis
        )

        assert "price" in objections
        assert "emotional_resistance" in objections
        assert "negative_sentiment" in objections

    @pytest.mark.asyncio
    async def test_process_voice_segment(self, voice_analyzer):
        """Test processing complete voice segment."""
        # Start a call first
        await voice_analyzer.start_call_analysis(
            call_id="test_call_456",
            agent_id="agent_123",
            analysis_mode=VoiceAnalysisMode.LIVE_COACHING
        )

        # Mock Claude semantic analysis
        with patch.object(voice_analyzer.claude_semantic, 'analyze_lead_intent') as mock_analyze:
            mock_analyze.return_value = {
                "sentiment_score": 0.4,
                "urgency_score": 70,
                "keywords": ["interested", "property"],
                "confidence": 80
            }

            audio_data = b"demo_audio_segment"
            segment = await voice_analyzer.process_voice_segment(
                call_id="test_call_456",
                audio_data=audio_data,
                speaker="prospect"
            )

            assert isinstance(segment, VoiceSegment)
            assert segment.speaker == "prospect"
            assert segment.confidence > 0
            assert isinstance(segment.emotional_tone, EmotionalTone)

        # Verify segment was added to call session
        call_session = voice_analyzer.active_calls["test_call_456"]
        assert len(call_session["segments"]) == 1
        assert call_session["segments"][0] == segment

    @pytest.mark.asyncio
    async def test_live_coaching_generation(self, voice_analyzer):
        """Test real-time coaching suggestion generation."""
        # Start call and add segments
        await voice_analyzer.start_call_analysis(
            call_id="test_call_789",
            agent_id="agent_456",
            analysis_mode=VoiceAnalysisMode.LIVE_COACHING
        )

        # Mock Claude agent service
        with patch.object(voice_analyzer.claude_agent, 'get_real_time_coaching') as mock_coaching:
            mock_coaching.return_value = Mock(
                urgency="high",
                reasoning="Prospect showing price objection - address value proposition",
                recommended_response="Let me show you the market analysis",
                confidence=85
            )

            # Create segment with objection
            segment = VoiceSegment(
                speaker="prospect",
                text="This seems expensive compared to other options",
                timestamp=datetime.now(),
                confidence=0.85,
                emotional_tone=EmotionalTone.SKEPTICAL,
                sentiment_score=-0.3,
                urgency_level=0.4,
                keywords=["expensive"],
                objections_detected=["price"]
            )

            # Trigger coaching
            await voice_analyzer._generate_live_coaching("test_call_789", segment)

            # Verify coaching was generated
            call_session = voice_analyzer.active_calls["test_call_789"]
            coaching_suggestions = call_session["live_metrics"]["coaching_suggestions"]
            assert len(coaching_suggestions) > 0

            latest_coaching = coaching_suggestions[-1]
            assert latest_coaching["recommendation"]["priority"] == "high"
            assert "objection_handling" in latest_coaching["recommendation"]["category"]

    def test_call_quality_scoring(self, voice_analyzer, sample_conversation_segments):
        """Test call quality score calculation."""
        duration = 900.0  # 15 minutes

        score = voice_analyzer._calculate_call_quality_score(
            sample_conversation_segments, duration
        )

        assert 0 <= score <= 100
        assert isinstance(score, float)

    def test_rapport_score_calculation(self, voice_analyzer, sample_conversation_segments):
        """Test rapport score calculation."""
        score = voice_analyzer._calculate_rapport_score(sample_conversation_segments)

        assert 0 <= score <= 100
        assert isinstance(score, float)

    def test_engagement_score_calculation(self, voice_analyzer, sample_conversation_segments):
        """Test engagement score calculation."""
        score = voice_analyzer._calculate_engagement_score(sample_conversation_segments)

        assert 0 <= score <= 100
        assert isinstance(score, float)

    def test_qualification_progress_assessment(self, voice_analyzer, sample_conversation_segments):
        """Test qualification progress assessment."""
        progress = voice_analyzer._assess_qualification_progress(sample_conversation_segments)

        assert "budget" in progress
        assert "timeline" in progress
        assert "location" in progress

        for area, data in progress.items():
            assert "mentioned" in data
            assert "depth" in data
            assert "confidence" in data
            assert isinstance(data["mentioned"], bool)
            assert 0 <= data["confidence"] <= 100

    def test_missed_opportunities_identification(self, voice_analyzer, sample_conversation_segments):
        """Test identification of missed opportunities."""
        missed = voice_analyzer._identify_missed_opportunities(sample_conversation_segments)

        assert isinstance(missed, list)
        # Should identify unresolved price objection
        assert any("price" in opportunity.lower() for opportunity in missed)

    def test_outcome_prediction(self, voice_analyzer, sample_conversation_segments):
        """Test call outcome prediction."""
        prediction = voice_analyzer._predict_call_outcome(sample_conversation_segments)

        assert "predicted_outcome" in prediction
        assert "confidence" in prediction
        assert "recommendation" in prediction
        assert 0 <= prediction["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_complete_call_analysis(self, voice_analyzer, sample_conversation_segments):
        """Test complete call analysis workflow."""
        # Start call
        await voice_analyzer.start_call_analysis(
            call_id="test_call_complete",
            agent_id="agent_789",
            analysis_mode=VoiceAnalysisMode.POST_CALL_ANALYSIS
        )

        # Add sample segments to call
        call_session = voice_analyzer.active_calls["test_call_complete"]
        call_session["segments"] = sample_conversation_segments
        call_session["ended_at"] = datetime.now()

        # Perform complete analysis
        analysis = await voice_analyzer._analyze_complete_call(call_session)

        assert isinstance(analysis, CallAnalysisResult)
        assert analysis.call_id == "test_call_complete"
        assert analysis.duration_seconds > 0
        assert 0 <= analysis.call_quality_score <= 100
        assert 0 <= analysis.rapport_score <= 100
        assert 0 <= analysis.engagement_score <= 100
        assert isinstance(analysis.objections_detected, list)
        assert isinstance(analysis.follow_up_actions, list)
        assert isinstance(analysis.coaching_focus_areas, list)

    @pytest.mark.asyncio
    async def test_end_call_analysis(self, voice_analyzer):
        """Test ending call analysis and cleanup."""
        # Start call
        await voice_analyzer.start_call_analysis(
            call_id="test_call_end",
            agent_id="agent_123",
            analysis_mode=VoiceAnalysisMode.LIVE_COACHING
        )

        assert "test_call_end" in voice_analyzer.active_calls

        # Add some segments
        call_session = voice_analyzer.active_calls["test_call_end"]
        call_session["segments"] = [
            VoiceSegment(
                speaker="prospect",
                text="Thank you for your help",
                timestamp=datetime.now(),
                confidence=0.9,
                emotional_tone=EmotionalTone.NEUTRAL,
                sentiment_score=0.1,
                urgency_level=0.2,
                keywords=["thank"],
                objections_detected=[]
            )
        ]

        # End call analysis
        result = await voice_analyzer.end_call_analysis("test_call_end")

        assert isinstance(result, CallAnalysisResult)
        assert result.call_id == "test_call_end"

        # Verify cleanup
        assert "test_call_end" not in voice_analyzer.active_calls
        assert voice_analyzer.stats["calls_analyzed"] == 1

    def test_performance_stats(self, voice_analyzer):
        """Test performance statistics tracking."""
        stats = voice_analyzer.get_performance_stats()

        assert "calls_analyzed" in stats
        assert "total_processing_time" in stats
        assert "coaching_suggestions_generated" in stats
        assert "active_calls" in stats
        assert "audio_available" in stats

    def test_active_calls_tracking(self, voice_analyzer):
        """Test active calls tracking."""
        # Should start empty
        active = voice_analyzer.get_active_calls()
        assert len(active) == 0

        # Start a call
        asyncio.run(voice_analyzer.start_call_analysis(
            call_id="test_active_1",
            agent_id="agent_123"
        ))

        active = voice_analyzer.get_active_calls()
        assert len(active) == 1
        assert "test_active_1" in active
        assert active["test_active_1"]["agent_id"] == "agent_123"

    def test_coaching_category_determination(self, voice_analyzer):
        """Test coaching category determination logic."""
        # Objection handling scenario
        segment_with_objection = VoiceSegment(
            speaker="prospect",
            text="Too expensive",
            timestamp=datetime.now(),
            confidence=0.8,
            emotional_tone=EmotionalTone.SKEPTICAL,
            sentiment_score=-0.3,
            urgency_level=0.4,
            keywords=["expensive"],
            objections_detected=["price"]
        )

        category = voice_analyzer._determine_coaching_category(segment_with_objection, "prospect_response")
        assert category == "objection_handling"

        # Closing opportunity scenario
        segment_enthusiastic = VoiceSegment(
            speaker="prospect",
            text="This looks perfect! When can we see it?",
            timestamp=datetime.now(),
            confidence=0.95,
            emotional_tone=EmotionalTone.ENTHUSIASTIC,
            sentiment_score=0.8,
            urgency_level=0.9,
            keywords=["perfect", "when"],
            objections_detected=[]
        )

        category = voice_analyzer._determine_coaching_category(segment_enthusiastic, "prospect_response")
        assert category == "closing"


class TestVoiceAnalysisEndpoints:
    """Test voice analysis API endpoints integration."""

    @pytest.mark.asyncio
    async def test_voice_api_integration(self):
        """Test that voice analysis can integrate with API endpoints."""
        from ghl_real_estate_ai.services.claude_voice_analyzer import create_voice_analyzer

        # Test factory function
        analyzer = create_voice_analyzer("api_test_location")
        assert analyzer.location_id == "api_test_location"

        # Test API-style workflow
        start_result = await analyzer.start_call_analysis(
            call_id="api_call_123",
            agent_id="api_agent_456",
            analysis_mode=VoiceAnalysisMode.LIVE_COACHING
        )

        assert start_result["status"] == "started"

        # Simulate processing segments
        test_segments = [
            ("prospect", "Hi, looking for a house"),
            ("agent", "Great! What's your budget?"),
            ("prospect", "Around 400k but flexible"),
        ]

        for speaker, text in test_segments:
            # Simulate pre-transcribed text processing
            segment = await analyzer.process_voice_segment(
                call_id="api_call_123",
                audio_data=b"",  # Empty audio data
                speaker=speaker
            )

            # Override with test text
            segment.text = text

        # End analysis
        final_result = await analyzer.end_call_analysis("api_call_123")

        assert isinstance(final_result, CallAnalysisResult)
        assert final_result.call_id == "api_call_123"
        assert final_result.duration_seconds >= 0


# Performance benchmarking tests
class TestVoiceAnalysisPerformance:
    """Performance tests for voice analysis system."""

    @pytest.mark.asyncio
    async def test_processing_speed(self, voice_analyzer):
        """Test voice processing speed benchmarks."""
        import time

        # Start call
        await voice_analyzer.start_call_analysis(
            call_id="perf_test",
            agent_id="perf_agent",
            analysis_mode=VoiceAnalysisMode.LIVE_COACHING
        )

        # Time segment processing
        start_time = time.time()

        for i in range(10):
            await voice_analyzer.process_voice_segment(
                call_id="perf_test",
                audio_data=b"demo_data",
                speaker="prospect" if i % 2 == 0 else "agent"
            )

        processing_time = time.time() - start_time

        # Should process 10 segments in under 2 seconds
        assert processing_time < 2.0
        print(f"Processed 10 segments in {processing_time:.2f}s")

    @pytest.mark.asyncio
    async def test_memory_usage(self, voice_analyzer):
        """Test memory usage during extended analysis."""
        # Start call
        await voice_analyzer.start_call_analysis(
            call_id="memory_test",
            agent_id="memory_agent"
        )

        # Process many segments
        for i in range(100):
            await voice_analyzer.process_voice_segment(
                call_id="memory_test",
                audio_data=b"test_data",
                speaker="prospect" if i % 2 == 0 else "agent"
            )

        # Check that segments are properly managed
        call_session = voice_analyzer.active_calls["memory_test"]
        assert len(call_session["segments"]) == 100

        # Metrics should be trimmed to reasonable size
        assert len(call_session["live_metrics"]["sentiment_trend"]) <= 20


if __name__ == "__main__":
    # Run basic functionality test
    async def demo_test():
        print("Running Claude Voice Analyzer Demo Tests...")

        analyzer = ClaudeVoiceAnalyzer("demo_location", real_time_mode=False)

        # Test start analysis
        result = await analyzer.start_call_analysis(
            call_id="demo_call",
            agent_id="demo_agent",
            analysis_mode=VoiceAnalysisMode.LIVE_COACHING
        )
        print(f"✅ Started analysis: {result['status']}")

        # Test segment processing
        segment = await analyzer.process_voice_segment(
            call_id="demo_call",
            audio_data=b"demo_audio",
            speaker="prospect"
        )
        print(f"✅ Processed segment: {segment.emotional_tone.value}")

        # Test ending analysis
        final_analysis = await analyzer.end_call_analysis("demo_call")
        print(f"✅ Completed analysis: Quality score {final_analysis.call_quality_score:.1f}")

        print("All voice analysis tests passed! 🎉")

    # Run the demo
    asyncio.run(demo_test())