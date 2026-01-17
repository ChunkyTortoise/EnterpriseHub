"""
Comprehensive test suite for Voice AI Integration

Tests cover:
- Real-time audio processing and transcription
- Emotion and sentiment analysis
- Intent detection and coaching prompts
- Call analysis and conversion prediction
- Error handling and fallback behavior
- Performance requirements for real-time processing
- Silent failure detection
"""

import pytest
import asyncio
import time
import io
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from ghl_real_estate_ai.services.voice_ai_integration import (
    VoiceAIIntegration,
    VoiceSegment,
    CallAnalysis,
    LiveCoachingPrompt,
    AudioProcessor,
    SpeechTranscriptionService,
    EmotionAnalysisService,
    IntentAnalysisService,
    LiveCoachingEngine,
    create_voice_ai_integration
)


@pytest.fixture
def mock_audio_data():
    """Mock audio data for testing"""
    return b'\x00\x01' * 1000  # 2000 bytes of mock audio data


@pytest.fixture
def sample_transcript():
    """Sample transcript for testing"""
    return "Hi, I'm interested in a three bedroom house in downtown area, budget around 500K"


@pytest.fixture
def sample_voice_segment():
    """Sample voice segment for testing"""
    return VoiceSegment(
        start_time=0.0,
        end_time=5.0,
        speaker="customer",
        transcript="I'm looking for a house with good schools nearby",
        confidence=0.95,
        audio_features={
            "pitch_avg": 150.0,
            "energy": 0.7,
            "speaking_rate": 120.0
        },
        emotions={
            "excitement": 0.7,
            "confidence": 0.8,
            "anxiety": 0.2
        }
    )


@pytest.fixture
def sample_call_metadata():
    """Sample call metadata for testing"""
    return {
        "call_id": "call_123",
        "lead_id": "lead_456", 
        "agent_id": "agent_789",
        "start_time": datetime.now().isoformat(),
        "call_type": "inbound",
        "phone_number": "+1-555-123-4567"
    }


class TestVoiceAIIntegration:
    """Test suite for the main Voice AI integration"""

    @pytest.fixture
    def voice_ai(self):
        """Create Voice AI integration instance"""
        return VoiceAIIntegration()

    @pytest.mark.asyncio
    async def test_voice_ai_initialization(self, voice_ai):
        """Test Voice AI integration initializes correctly"""
        assert voice_ai.audio_processor is not None
        assert voice_ai.transcription_service is not None
        assert voice_ai.emotion_service is not None
        assert voice_ai.intent_service is not None
        assert voice_ai.coaching_engine is not None
        assert voice_ai.call_sessions == {}
        assert voice_ai.performance_metrics is not None

    @pytest.mark.asyncio
    async def test_start_call_analysis_success(self, voice_ai, sample_call_metadata):
        """Test successful call analysis initialization"""
        call_id = await voice_ai.start_call_analysis(sample_call_metadata)
        
        assert call_id == "call_123"
        assert call_id in voice_ai.call_sessions
        
        session = voice_ai.call_sessions[call_id]
        assert session["metadata"] == sample_call_metadata
        assert session["segments"] == []
        assert session["live_coaching_prompts"] == []
        assert session["status"] == "active"

    @pytest.mark.asyncio
    async def test_process_audio_stream_success(self, voice_ai, sample_call_metadata, mock_audio_data):
        """Test successful audio stream processing"""
        call_id = await voice_ai.start_call_analysis(sample_call_metadata)
        
        # Mock the audio processing chain
        with patch.object(voice_ai.audio_processor, 'detect_speech') as mock_detect:
            mock_detect.return_value = True
            
            with patch.object(voice_ai, '_process_speech_segment') as mock_process:
                mock_process.return_value = None  # Async function
                
                result = await voice_ai.process_audio_stream(call_id, mock_audio_data, "customer")
                
                assert result["status"] == "processed"
                assert result["call_id"] == call_id
                mock_detect.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_audio_stream_no_speech(self, voice_ai, sample_call_metadata, mock_audio_data):
        """Test audio processing when no speech is detected"""
        call_id = await voice_ai.start_call_analysis(sample_call_metadata)
        
        with patch.object(voice_ai.audio_processor, 'detect_speech') as mock_detect:
            mock_detect.return_value = False
            
            result = await voice_ai.process_audio_stream(call_id, mock_audio_data, "customer")
            
            assert result["status"] == "no_speech"
            assert result["call_id"] == call_id

    @pytest.mark.asyncio
    async def test_process_speech_segment(self, voice_ai, sample_call_metadata, mock_audio_data):
        """Test speech segment processing pipeline"""
        call_id = await voice_ai.start_call_analysis(sample_call_metadata)
        
        # Mock all the services in the pipeline
        with patch.object(voice_ai.transcription_service, 'transcribe_audio') as mock_transcribe:
            mock_transcribe.return_value = {
                "transcript": "I need a house with good schools",
                "confidence": 0.9
            }
            
            with patch.object(voice_ai.audio_processor, 'extract_audio_features') as mock_features:
                mock_features.return_value = {"pitch_avg": 150.0, "energy": 0.7}
                
                with patch.object(voice_ai.emotion_service, 'analyze_emotion') as mock_emotion:
                    mock_emotion.return_value = {
                        "emotions": {"excitement": 0.8, "confidence": 0.7},
                        "sentiment": "positive"
                    }
                    
                    with patch.object(voice_ai.intent_service, 'analyze_intent') as mock_intent:
                        mock_intent.return_value = {
                            "primary_intent": "property_search",
                            "confidence": 0.85,
                            "urgency_level": 0.7,
                            "objections": []
                        }
                        
                        await voice_ai._process_speech_segment(
                            call_id, mock_audio_data, "customer", 0.0, 5.0
                        )
                        
                        # Verify all services were called
                        mock_transcribe.assert_called_once()
                        mock_features.assert_called_once()
                        mock_emotion.assert_called_once()
                        mock_intent.assert_called_once()
                        
                        # Verify segment was added to session
                        session = voice_ai.call_sessions[call_id]
                        assert len(session["segments"]) == 1
                        
                        segment = session["segments"][0]
                        assert segment.transcript == "I need a house with good schools"
                        assert segment.speaker == "customer"

    @pytest.mark.asyncio
    async def test_end_call_analysis(self, voice_ai, sample_call_metadata):
        """Test call analysis completion"""
        call_id = await voice_ai.start_call_analysis(sample_call_metadata)
        
        # Add some mock segments
        voice_ai.call_sessions[call_id]["segments"] = [
            VoiceSegment(
                start_time=0.0, end_time=5.0, speaker="customer",
                transcript="I need a house", confidence=0.9,
                audio_features={}, emotions={}
            )
        ]
        
        analysis = await voice_ai.end_call_analysis(call_id)
        
        assert isinstance(analysis, CallAnalysis)
        assert analysis.call_id == call_id
        assert analysis.total_duration > 0
        assert isinstance(analysis.conversion_probability, float)
        assert 0 <= analysis.conversion_probability <= 1
        assert analysis.status == "completed"

    @pytest.mark.asyncio
    async def test_error_handling_invalid_call_id(self, voice_ai, mock_audio_data):
        """Test error handling with invalid call ID"""
        result = await voice_ai.process_audio_stream("invalid_call", mock_audio_data, "customer")
        
        assert result["status"] == "error"
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_error_handling_corrupted_audio(self, voice_ai, sample_call_metadata):
        """Test error handling with corrupted audio data"""
        call_id = await voice_ai.start_call_analysis(sample_call_metadata)
        
        # Send corrupted audio data
        corrupted_audio = b'\xff' * 10  # Very small, invalid audio
        
        result = await voice_ai.process_audio_stream(call_id, corrupted_audio, "customer")
        
        # Should handle gracefully, not crash
        assert "status" in result
        assert result["call_id"] == call_id

    @pytest.mark.asyncio
    async def test_concurrent_call_processing(self, voice_ai, mock_audio_data):
        """Test handling multiple concurrent calls"""
        call_metadata_1 = {"call_id": "call_001", "lead_id": "lead_001"}
        call_metadata_2 = {"call_id": "call_002", "lead_id": "lead_002"}
        
        call_id_1 = await voice_ai.start_call_analysis(call_metadata_1)
        call_id_2 = await voice_ai.start_call_analysis(call_metadata_2)
        
        # Process audio for both calls concurrently
        task1 = voice_ai.process_audio_stream(call_id_1, mock_audio_data, "customer")
        task2 = voice_ai.process_audio_stream(call_id_2, mock_audio_data, "customer")
        
        results = await asyncio.gather(task1, task2, return_exceptions=True)
        
        # Both should succeed
        assert len(results) == 2
        assert not any(isinstance(r, Exception) for r in results)
        
        # Verify sessions are separate
        assert call_id_1 in voice_ai.call_sessions
        assert call_id_2 in voice_ai.call_sessions
        assert call_id_1 != call_id_2

    @pytest.mark.asyncio
    async def test_performance_metrics_tracking(self, voice_ai, sample_call_metadata, mock_audio_data):
        """Test performance metrics are tracked correctly"""
        initial_metrics = voice_ai.get_performance_metrics()
        
        call_id = await voice_ai.start_call_analysis(sample_call_metadata)
        await voice_ai.process_audio_stream(call_id, mock_audio_data, "customer")
        
        updated_metrics = voice_ai.get_performance_metrics()
        
        # Metrics should be updated
        assert "total_calls" in updated_metrics
        assert "average_processing_time" in updated_metrics
        assert "error_rate" in updated_metrics


class TestAudioProcessor:
    """Test suite for audio processing component"""

    @pytest.fixture
    def processor(self):
        """Create audio processor instance"""
        return AudioProcessor()

    def test_detect_speech_with_audio(self, processor, mock_audio_data):
        """Test speech detection with audio data"""
        result = processor.detect_speech(mock_audio_data)
        
        # Should return boolean
        assert isinstance(result, bool)

    def test_detect_speech_empty_audio(self, processor):
        """Test speech detection with empty audio"""
        result = processor.detect_speech(b'')
        
        assert result is False

    def test_extract_audio_features(self, processor, mock_audio_data):
        """Test audio feature extraction"""
        features = processor.extract_audio_features(mock_audio_data)
        
        assert isinstance(features, dict)
        assert "pitch_avg" in features
        assert "energy" in features
        assert "speaking_rate" in features
        
        # Values should be reasonable
        assert isinstance(features["pitch_avg"], float)
        assert features["pitch_avg"] > 0
        assert 0 <= features["energy"] <= 1


class TestSpeechTranscriptionService:
    """Test suite for speech transcription"""

    @pytest.fixture
    def transcription_service(self):
        """Create transcription service instance"""
        return SpeechTranscriptionService()

    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, transcription_service, mock_audio_data):
        """Test successful audio transcription"""
        result = await transcription_service.transcribe_audio(mock_audio_data)
        
        assert isinstance(result, dict)
        assert "transcript" in result
        assert "confidence" in result
        assert isinstance(result["transcript"], str)
        assert isinstance(result["confidence"], float)
        assert 0 <= result["confidence"] <= 1

    @pytest.mark.asyncio
    async def test_transcribe_empty_audio(self, transcription_service):
        """Test transcription with empty audio"""
        result = await transcription_service.transcribe_audio(b'')
        
        assert result["transcript"] == ""
        assert result["confidence"] == 0.0

    @pytest.mark.asyncio
    async def test_transcription_fallback_behavior(self, transcription_service, mock_audio_data):
        """Test transcription fallback when external service fails"""
        # Mock external service failure
        with patch('ghl_real_estate_ai.services.voice_ai_integration.HAS_SPEECH_LIBS', False):
            result = await transcription_service.transcribe_audio(mock_audio_data)
            
            # Should use fallback transcription
            assert isinstance(result, dict)
            assert "transcript" in result
            assert result["confidence"] < 0.5  # Lower confidence for fallback


class TestEmotionAnalysisService:
    """Test suite for emotion analysis"""

    @pytest.fixture
    def emotion_service(self):
        """Create emotion analysis service instance"""
        return EmotionAnalysisService()

    @pytest.mark.asyncio
    async def test_analyze_emotion_with_text_and_audio(self, emotion_service, mock_audio_data):
        """Test emotion analysis with both text and audio"""
        result = await emotion_service.analyze_emotion(
            text="I'm really excited about this house!",
            audio_data=mock_audio_data,
            audio_features={"pitch_avg": 200.0, "energy": 0.8}
        )
        
        assert isinstance(result, dict)
        assert "emotions" in result
        assert "sentiment" in result
        assert "confidence" in result
        
        emotions = result["emotions"]
        assert isinstance(emotions, dict)
        
        # Should contain common emotions
        expected_emotions = ["excitement", "confidence", "anxiety", "frustration"]
        assert any(emotion in emotions for emotion in expected_emotions)
        
        # Emotion values should be between 0 and 1
        for emotion_value in emotions.values():
            assert 0 <= emotion_value <= 1

    @pytest.mark.asyncio
    async def test_analyze_emotion_text_only(self, emotion_service):
        """Test emotion analysis with text only"""
        result = await emotion_service.analyze_emotion(
            text="This house is perfect for my family!"
        )
        
        assert isinstance(result, dict)
        assert "emotions" in result
        assert "sentiment" in result

    @pytest.mark.asyncio
    async def test_analyze_emotion_negative_sentiment(self, emotion_service):
        """Test emotion analysis with negative sentiment"""
        result = await emotion_service.analyze_emotion(
            text="This is too expensive and the location is terrible"
        )
        
        assert result["sentiment"] in ["negative", "very_negative"]
        emotions = result["emotions"]
        
        # Should detect negative emotions
        negative_emotions = ["frustration", "disappointment", "anxiety"]
        assert any(emotions.get(emotion, 0) > 0.3 for emotion in negative_emotions)


class TestIntentAnalysisService:
    """Test suite for intent analysis"""

    @pytest.fixture
    def intent_service(self):
        """Create intent analysis service instance"""
        return IntentAnalysisService()

    @pytest.mark.asyncio
    async def test_analyze_intent_property_search(self, intent_service):
        """Test intent analysis for property search"""
        result = await intent_service.analyze_intent(
            "I'm looking for a three bedroom house with good schools in downtown"
        )
        
        assert isinstance(result, dict)
        assert "primary_intent" in result
        assert "confidence" in result
        assert "urgency_level" in result
        assert "keywords" in result
        assert "objections" in result
        
        # Should detect property search intent
        assert result["primary_intent"] in ["property_search", "information_gathering"]
        assert result["confidence"] > 0.5

    @pytest.mark.asyncio
    async def test_analyze_intent_objections(self, intent_service):
        """Test intent analysis for objections"""
        result = await intent_service.analyze_intent(
            "This is too expensive and I need to think about it more"
        )
        
        objections = result["objections"]
        assert isinstance(objections, list)
        
        # Should detect price objection
        objection_types = [obj["type"] for obj in objections]
        assert "price" in objection_types or "timeline" in objection_types

    @pytest.mark.asyncio
    async def test_analyze_intent_urgency_detection(self, intent_service):
        """Test urgency detection in intent analysis"""
        urgent_text = "I need to move next month and want to see properties this weekend"
        result = await intent_service.analyze_intent(urgent_text)
        
        assert result["urgency_level"] > 0.6  # High urgency

    @pytest.mark.asyncio
    async def test_analyze_intent_with_claude_integration(self, intent_service):
        """Test intent analysis with Claude AI integration"""
        with patch.object(intent_service, '_analyze_intent_with_claude') as mock_claude:
            mock_claude.return_value = {
                "primary_intent": "property_search",
                "confidence": 0.9,
                "urgency_level": 0.8,
                "keywords": ["house", "schools"],
                "objections": []
            }
            
            result = await intent_service.analyze_intent(
                "I want a house near good schools"
            )
            
            assert result["primary_intent"] == "property_search"
            assert result["confidence"] == 0.9


class TestLiveCoachingEngine:
    """Test suite for live coaching engine"""

    @pytest.fixture
    def coaching_engine(self):
        """Create coaching engine instance"""
        return LiveCoachingEngine()

    @pytest.mark.asyncio
    async def test_generate_coaching_prompt_objection(self, coaching_engine):
        """Test coaching prompt generation for objections"""
        call_context = {
            "customer_intent": "property_search",
            "detected_objections": [{"type": "price", "confidence": 0.8}],
            "customer_emotions": {"anxiety": 0.7, "interest": 0.6}
        }
        
        prompt = await coaching_engine.generate_coaching_prompt(call_context)
        
        assert isinstance(prompt, LiveCoachingPrompt)
        assert prompt.prompt_type in ["objection_handling", "price_negotiation"]
        assert prompt.priority in ["high", "medium", "low"]
        assert len(prompt.message) > 0
        assert isinstance(prompt.suggested_responses, list)

    @pytest.mark.asyncio
    async def test_generate_coaching_prompt_closing_opportunity(self, coaching_engine):
        """Test coaching prompt for closing opportunity"""
        call_context = {
            "customer_intent": "ready_to_buy",
            "urgency_level": 0.9,
            "customer_emotions": {"excitement": 0.8, "confidence": 0.7},
            "conversation_stage": "property_discussion"
        }
        
        prompt = await coaching_engine.generate_coaching_prompt(call_context)
        
        assert prompt.prompt_type == "closing_opportunity"
        assert prompt.priority == "high"
        assert "close" in prompt.message.lower() or "next steps" in prompt.message.lower()

    @pytest.mark.asyncio
    async def test_generate_coaching_prompt_information_gathering(self, coaching_engine):
        """Test coaching prompt for information gathering"""
        call_context = {
            "customer_intent": "information_gathering", 
            "missing_info": ["budget", "timeline", "location"],
            "conversation_stage": "initial"
        }
        
        prompt = await coaching_engine.generate_coaching_prompt(call_context)
        
        assert prompt.prompt_type == "information_gathering"
        assert any("budget" in response.lower() or "timeline" in response.lower() 
                  for response in prompt.suggested_responses)


class TestVoiceAIIntegrationPerformance:
    """Performance and load tests for Voice AI"""

    @pytest.mark.asyncio
    async def test_real_time_processing_latency(self, mock_audio_data):
        """Test real-time processing latency requirements"""
        voice_ai = VoiceAIIntegration()
        call_metadata = {"call_id": "latency_test", "lead_id": "lead_test"}
        
        call_id = await voice_ai.start_call_analysis(call_metadata)
        
        start_time = time.time()
        result = await voice_ai.process_audio_stream(call_id, mock_audio_data, "customer")
        processing_time = time.time() - start_time
        
        # Real-time processing should be fast (<500ms for 5s of audio)
        assert processing_time < 0.5, f"Processing took {processing_time:.3f}s, should be <0.5s"

    @pytest.mark.asyncio
    async def test_memory_usage_with_long_call(self):
        """Test memory usage doesn't grow excessively during long calls"""
        import psutil
        import os
        
        voice_ai = VoiceAIIntegration()
        call_metadata = {"call_id": "long_call", "lead_id": "lead_long"}
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        call_id = await voice_ai.start_call_analysis(call_metadata)
        
        # Simulate long call with many audio segments
        mock_audio = b'\x00\x01' * 500  # Smaller audio chunks
        for i in range(100):  # 100 audio segments
            await voice_ai.process_audio_stream(call_id, mock_audio, "customer")
        
        final_memory = process.memory_info().rss
        memory_growth_mb = (final_memory - initial_memory) / 1024 / 1024
        
        # Memory growth should be reasonable (<100MB for 100 segments)
        assert memory_growth_mb < 100, f"Memory grew by {memory_growth_mb:.1f}MB, should be <100MB"

    @pytest.mark.asyncio
    async def test_concurrent_call_performance(self, mock_audio_data):
        """Test performance with multiple concurrent calls"""
        voice_ai = VoiceAIIntegration()
        
        # Start 5 concurrent calls
        call_ids = []
        for i in range(5):
            metadata = {"call_id": f"concurrent_{i}", "lead_id": f"lead_{i}"}
            call_id = await voice_ai.start_call_analysis(metadata)
            call_ids.append(call_id)
        
        # Process audio concurrently
        start_time = time.time()
        tasks = [
            voice_ai.process_audio_stream(call_id, mock_audio_data, "customer")
            for call_id in call_ids
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Check for exceptions
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Found {len(exceptions)} exceptions in concurrent processing"
        
        # Should complete reasonably quickly
        assert total_time < 5.0, f"Concurrent processing took {total_time:.2f}s, should be <5s"


class TestVoiceAIErrorRecovery:
    """Test error recovery and fallback scenarios"""

    @pytest.mark.asyncio
    async def test_recovery_from_transcription_failure(self, mock_audio_data):
        """Test recovery when transcription service fails"""
        voice_ai = VoiceAIIntegration()
        call_metadata = {"call_id": "transcription_fail", "lead_id": "lead_fail"}
        
        call_id = await voice_ai.start_call_analysis(call_metadata)
        
        # Mock transcription failure
        with patch.object(voice_ai.transcription_service, 'transcribe_audio') as mock_transcribe:
            mock_transcribe.side_effect = Exception("Transcription service down")
            
            result = await voice_ai.process_audio_stream(call_id, mock_audio_data, "customer")
            
            # Should handle gracefully
            assert "status" in result
            assert result["call_id"] == call_id

    @pytest.mark.asyncio
    async def test_recovery_from_emotion_analysis_failure(self, mock_audio_data):
        """Test recovery when emotion analysis fails"""
        voice_ai = VoiceAIIntegration()
        call_metadata = {"call_id": "emotion_fail", "lead_id": "lead_fail"}
        
        call_id = await voice_ai.start_call_analysis(call_metadata)
        
        # Mock emotion analysis failure
        with patch.object(voice_ai.emotion_service, 'analyze_emotion') as mock_emotion:
            mock_emotion.side_effect = Exception("Emotion service down")
            
            result = await voice_ai.process_audio_stream(call_id, mock_audio_data, "customer")
            
            # Should handle gracefully
            assert "status" in result
            assert result["call_id"] == call_id

    @pytest.mark.asyncio
    async def test_factory_function(self):
        """Test factory function creates Voice AI correctly"""
        voice_ai = await create_voice_ai_integration()
        
        assert isinstance(voice_ai, VoiceAIIntegration)
        assert voice_ai.audio_processor is not None
        assert voice_ai.transcription_service is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])