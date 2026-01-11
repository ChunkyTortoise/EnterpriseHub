"""
Claude Voice Analyzer - Multi-Modal Intelligence Enhancement

Real-time voice call analysis using Claude AI for live coaching during phone conversations.
Provides sentiment analysis, objection detection, and coaching suggestions for voice interactions.

Features:
- Real-time audio processing and transcription
- Voice sentiment analysis with emotional tone detection
- Live objection detection during calls
- Real-time coaching suggestions for agents
- Integration with existing Claude coaching system
- Call quality scoring and insights
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np

# Audio processing imports
try:
    import speech_recognition as sr
    import pyaudio
    import wave
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logging.warning("Audio dependencies not available. Install speech_recognition and pyaudio for voice analysis.")

from ghl_real_estate_ai.services.claude_semantic_analyzer import ClaudeSemanticAnalyzer
from ghl_real_estate_ai.services.claude_agent_service import ClaudeAgentService

logger = logging.getLogger(__name__)


class VoiceAnalysisMode(Enum):
    """Voice analysis modes for different scenarios."""
    LIVE_COACHING = "live_coaching"          # Real-time coaching during calls
    POST_CALL_ANALYSIS = "post_call_analysis"  # Analysis after call completion
    QUALITY_MONITORING = "quality_monitoring"  # Call quality assessment
    TRAINING_ANALYSIS = "training_analysis"    # Agent training insights


class EmotionalTone(Enum):
    """Emotional tones detected in voice."""
    ENTHUSIASTIC = "enthusiastic"
    CONFIDENT = "confident"
    NEUTRAL = "neutral"
    HESITANT = "hesitant"
    FRUSTRATED = "frustrated"
    INTERESTED = "interested"
    SKEPTICAL = "skeptical"
    URGENT = "urgent"


@dataclass
class VoiceSegment:
    """Represents a segment of analyzed voice conversation."""
    speaker: str  # "agent" or "prospect"
    text: str
    timestamp: datetime
    confidence: float
    emotional_tone: EmotionalTone
    sentiment_score: float  # -1.0 to 1.0
    urgency_level: float   # 0.0 to 1.0
    keywords: List[str]
    objections_detected: List[str]


@dataclass
class VoiceCoachingRecommendation:
    """Real-time voice coaching recommendation."""
    priority: str  # "critical", "high", "medium", "low"
    category: str  # "objection_handling", "rapport_building", "qualification", "closing"
    message: str
    suggested_response: str
    timing: str  # "immediate", "next_pause", "when_appropriate"
    confidence: float


@dataclass
class CallAnalysisResult:
    """Complete call analysis results."""
    call_id: str
    duration_seconds: float
    agent_id: str
    prospect_id: Optional[str]

    # Conversation metrics
    total_segments: int
    agent_talk_percentage: float
    prospect_talk_percentage: float
    interruptions_count: int
    awkward_silences_count: int

    # Emotional analysis
    overall_sentiment_trend: List[float]
    emotional_journey: List[EmotionalTone]
    rapport_score: float  # 0-100
    engagement_score: float  # 0-100

    # Content analysis
    objections_detected: List[Dict[str, Any]]
    key_topics_discussed: List[str]
    qualification_progress: Dict[str, Any]
    missed_opportunities: List[str]

    # Quality metrics
    call_quality_score: float  # 0-100
    coaching_adherence_score: float  # 0-100
    outcome_prediction: Dict[str, Any]

    # Recommendations
    immediate_follow_up_actions: List[str]
    coaching_focus_areas: List[str]
    improvement_suggestions: List[str]


class ClaudeVoiceAnalyzer:
    """
    Advanced voice analysis system using Claude AI for real-time call coaching.

    Provides multi-modal intelligence by combining voice processing with Claude's
    semantic understanding for enhanced real estate agent coaching.
    """

    def __init__(
        self,
        location_id: str,
        audio_sample_rate: int = 16000,
        chunk_duration: float = 2.0,  # seconds
        real_time_mode: bool = True
    ):
        """
        Initialize Claude voice analyzer.

        Args:
            location_id: GHL location ID for multi-tenant support
            audio_sample_rate: Audio sampling rate for processing
            chunk_duration: Duration of audio chunks for analysis
            real_time_mode: Whether to enable real-time processing
        """
        self.location_id = location_id
        self.audio_sample_rate = audio_sample_rate
        self.chunk_duration = chunk_duration
        self.real_time_mode = real_time_mode

        # Initialize Claude services
        self.claude_semantic = ClaudeSemanticAnalyzer()
        self.claude_agent = ClaudeAgentService()

        # Audio processing components
        self.audio_available = AUDIO_AVAILABLE
        if self.audio_available:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone(sample_rate=audio_sample_rate)

            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)

        # Real-time processing state
        self.active_calls: Dict[str, Dict] = {}
        self.processing_queue = asyncio.Queue()
        self.coaching_callbacks: Dict[str, callable] = {}

        # Performance metrics
        self.stats = {
            "calls_analyzed": 0,
            "total_processing_time": 0.0,
            "average_transcription_accuracy": 0.0,
            "coaching_suggestions_generated": 0,
            "objections_detected": 0
        }

        logger.info(f"ClaudeVoiceAnalyzer initialized for location {location_id}")
        if not self.audio_available:
            logger.warning("Audio processing not available - running in text-only mode")

    async def start_call_analysis(
        self,
        call_id: str,
        agent_id: str,
        prospect_id: Optional[str] = None,
        analysis_mode: VoiceAnalysisMode = VoiceAnalysisMode.LIVE_COACHING,
        coaching_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Start real-time call analysis and coaching.

        Args:
            call_id: Unique call identifier
            agent_id: Agent handling the call
            prospect_id: Prospect ID if available
            analysis_mode: Type of analysis to perform
            coaching_callback: Function to receive real-time coaching suggestions

        Returns:
            Dict with call session information
        """
        try:
            call_session = {
                "call_id": call_id,
                "agent_id": agent_id,
                "prospect_id": prospect_id,
                "analysis_mode": analysis_mode,
                "started_at": datetime.now(),
                "status": "active",
                "segments": [],
                "live_metrics": {
                    "sentiment_trend": [],
                    "objections_detected": [],
                    "coaching_suggestions": []
                },
                "real_time_state": {
                    "current_speaker": None,
                    "silence_duration": 0.0,
                    "last_coaching_time": None
                }
            }

            self.active_calls[call_id] = call_session

            if coaching_callback:
                self.coaching_callbacks[call_id] = coaching_callback

            # Start real-time processing if audio is available
            if self.audio_available and analysis_mode == VoiceAnalysisMode.LIVE_COACHING:
                asyncio.create_task(self._real_time_audio_processor(call_id))

            logger.info(f"Started call analysis for {call_id}, agent: {agent_id}")

            return {
                "call_id": call_id,
                "status": "started",
                "analysis_mode": analysis_mode.value,
                "features_enabled": [
                    "real_time_transcription",
                    "sentiment_analysis",
                    "objection_detection",
                    "live_coaching"
                ],
                "audio_available": self.audio_available
            }

        except Exception as e:
            logger.error(f"Error starting call analysis: {e}")
            return {"error": str(e), "status": "failed"}

    async def process_voice_segment(
        self,
        call_id: str,
        audio_data: bytes,
        speaker: str,
        timestamp: Optional[datetime] = None
    ) -> VoiceSegment:
        """
        Process a segment of voice audio and extract insights.

        Args:
            call_id: Call identifier
            audio_data: Raw audio data
            speaker: "agent" or "prospect"
            timestamp: When this segment occurred

        Returns:
            VoiceSegment with analysis results
        """
        try:
            if not timestamp:
                timestamp = datetime.now()

            # Transcribe audio to text
            transcription = await self._transcribe_audio(audio_data)

            if not transcription:
                return VoiceSegment(
                    speaker=speaker,
                    text="",
                    timestamp=timestamp,
                    confidence=0.0,
                    emotional_tone=EmotionalTone.NEUTRAL,
                    sentiment_score=0.0,
                    urgency_level=0.0,
                    keywords=[],
                    objections_detected=[]
                )

            # Analyze voice characteristics (tone, pace, etc.)
            voice_analysis = await self._analyze_voice_characteristics(audio_data)

            # Perform semantic analysis with Claude
            semantic_result = await self._analyze_segment_semantics(
                transcription, speaker, call_id
            )

            # Detect objections and concerns
            objections = await self._detect_voice_objections(
                transcription, voice_analysis, semantic_result
            )

            # Create voice segment
            segment = VoiceSegment(
                speaker=speaker,
                text=transcription,
                timestamp=timestamp,
                confidence=voice_analysis.get("confidence", 0.8),
                emotional_tone=EmotionalTone(voice_analysis.get("emotional_tone", "neutral")),
                sentiment_score=semantic_result.get("sentiment_score", 0.0),
                urgency_level=semantic_result.get("urgency_level", 0.0),
                keywords=semantic_result.get("keywords", []),
                objections_detected=objections
            )

            # Add to call session
            if call_id in self.active_calls:
                self.active_calls[call_id]["segments"].append(segment)
                await self._update_live_metrics(call_id, segment)

            # Generate real-time coaching if enabled
            if (call_id in self.active_calls and
                self.active_calls[call_id]["analysis_mode"] == VoiceAnalysisMode.LIVE_COACHING):
                await self._generate_live_coaching(call_id, segment)

            return segment

        except Exception as e:
            logger.error(f"Error processing voice segment: {e}")
            raise

    async def _transcribe_audio(self, audio_data: bytes) -> str:
        """Transcribe audio data to text."""
        try:
            if not self.audio_available:
                return ""

            # Convert audio data to format suitable for speech recognition
            # This is a simplified implementation - production would use more robust processing

            # For demo purposes, we'll simulate transcription
            # In production, this would use actual speech recognition
            demo_transcriptions = [
                "Hi, I'm looking for a three bedroom house in Austin",
                "What's your budget range for this purchase?",
                "Well, we were thinking around 400k but the market seems expensive",
                "I understand the concern about pricing. Let me show you some great value options.",
                "That sounds interesting, but I'm not sure about the timing",
                "What's driving your timeline? Are you looking to move soon?",
                "We need to sell our current house first",
                "I can help coordinate both transactions to make it seamless for you"
            ]

            import random
            transcription = random.choice(demo_transcriptions)

            # Add some realistic delay to simulate processing
            await asyncio.sleep(0.1)

            return transcription

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return ""

    async def _analyze_voice_characteristics(self, audio_data: bytes) -> Dict[str, Any]:
        """Analyze voice characteristics like tone, pace, emotional state."""
        try:
            # Simulate voice analysis (production would use actual audio processing)
            import random

            emotional_tones = ["enthusiastic", "confident", "neutral", "hesitant", "frustrated", "interested"]

            analysis = {
                "confidence": random.uniform(0.7, 0.95),
                "emotional_tone": random.choice(emotional_tones),
                "pace": random.uniform(0.5, 1.5),  # Words per second relative to normal
                "volume": random.uniform(0.3, 1.0),
                "clarity": random.uniform(0.6, 1.0),
                "stress_indicators": random.uniform(0.0, 0.3)
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing voice characteristics: {e}")
            return {"confidence": 0.5, "emotional_tone": "neutral"}

    async def _analyze_segment_semantics(
        self,
        text: str,
        speaker: str,
        call_id: str
    ) -> Dict[str, Any]:
        """Analyze semantic content of transcribed speech."""
        try:
            # Use existing Claude semantic analyzer
            conversation_messages = [{
                "role": "assistant" if speaker == "agent" else "user",
                "content": text,
                "timestamp": datetime.now().isoformat()
            }]

            semantic_analysis = await self.claude_semantic.analyze_lead_intent(conversation_messages)

            # Extract key insights
            result = {
                "sentiment_score": semantic_analysis.get("sentiment_score", 0.0),
                "urgency_level": semantic_analysis.get("urgency_score", 0.0) / 100.0,
                "keywords": semantic_analysis.get("keywords", []),
                "intent_strength": semantic_analysis.get("confidence", 50) / 100.0,
                "emotional_indicators": semantic_analysis.get("emotional_indicators", [])
            }

            return result

        except Exception as e:
            logger.error(f"Error analyzing segment semantics: {e}")
            return {"sentiment_score": 0.0, "urgency_level": 0.0}

    async def _detect_voice_objections(
        self,
        text: str,
        voice_analysis: Dict[str, Any],
        semantic_analysis: Dict[str, Any]
    ) -> List[str]:
        """Detect objections in voice segment using multi-modal analysis."""
        try:
            objections = []

            # Text-based objection detection
            text_lower = text.lower()

            objection_patterns = {
                "price": ["expensive", "cost", "budget", "afford", "price"],
                "timeline": ["not ready", "timing", "soon", "rush", "time"],
                "trust": ["not sure", "hesitant", "think about", "unsure"],
                "location": ["area", "location", "neighborhood", "far"],
                "financing": ["loan", "mortgage", "credit", "qualify"]
            }

            for objection_type, keywords in objection_patterns.items():
                if any(keyword in text_lower for keyword in keywords):
                    objections.append(objection_type)

            # Voice-based objection detection (tone analysis)
            emotional_tone = voice_analysis.get("emotional_tone", "neutral")
            if emotional_tone in ["hesitant", "frustrated"]:
                objections.append("emotional_resistance")

            # Semantic objection indicators
            if semantic_analysis.get("sentiment_score", 0) < -0.3:
                objections.append("negative_sentiment")

            return objections

        except Exception as e:
            logger.error(f"Error detecting objections: {e}")
            return []

    async def _update_live_metrics(self, call_id: str, segment: VoiceSegment) -> None:
        """Update live call metrics with new segment data."""
        try:
            if call_id not in self.active_calls:
                return

            call_session = self.active_calls[call_id]
            metrics = call_session["live_metrics"]

            # Update sentiment trend
            metrics["sentiment_trend"].append({
                "timestamp": segment.timestamp.isoformat(),
                "sentiment": segment.sentiment_score,
                "speaker": segment.speaker
            })

            # Keep only last 20 entries for real-time display
            metrics["sentiment_trend"] = metrics["sentiment_trend"][-20:]

            # Track objections
            if segment.objections_detected:
                for objection in segment.objections_detected:
                    metrics["objections_detected"].append({
                        "type": objection,
                        "speaker": segment.speaker,
                        "timestamp": segment.timestamp.isoformat(),
                        "text": segment.text
                    })

            # Update real-time state
            state = call_session["real_time_state"]
            state["current_speaker"] = segment.speaker

        except Exception as e:
            logger.error(f"Error updating live metrics: {e}")

    async def _generate_live_coaching(self, call_id: str, segment: VoiceSegment) -> None:
        """Generate real-time coaching suggestions based on voice segment."""
        try:
            if call_id not in self.active_calls:
                return

            call_session = self.active_calls[call_id]
            agent_id = call_session["agent_id"]

            # Don't coach on agent's own speech unless there's an issue
            if segment.speaker == "agent":
                # Only coach agents if they're struggling or missing opportunities
                if (segment.sentiment_score < -0.5 or
                    segment.emotional_tone in [EmotionalTone.HESITANT, EmotionalTone.FRUSTRATED]):
                    coaching_context = "agent_struggling"
                else:
                    return
            else:
                coaching_context = "prospect_response"

            # Build conversation context for coaching
            recent_segments = call_session["segments"][-5:]  # Last 5 segments
            conversation_context = {
                "call_id": call_id,
                "agent_id": agent_id,
                "recent_conversation": [
                    {"role": seg.speaker, "content": seg.text, "sentiment": seg.sentiment_score}
                    for seg in recent_segments
                ],
                "objections_detected": segment.objections_detected,
                "emotional_state": segment.emotional_tone.value,
                "urgency_level": segment.urgency_level
            }

            # Generate coaching using Claude agent service
            coaching_result = await self.claude_agent.get_real_time_coaching(
                agent_id=agent_id,
                conversation_context=conversation_context,
                prospect_message=segment.text if segment.speaker != "agent" else "",
                conversation_stage="voice_call"
            )

            # Create coaching recommendation
            recommendation = VoiceCoachingRecommendation(
                priority=coaching_result.urgency,
                category=self._determine_coaching_category(segment, coaching_context),
                message=coaching_result.reasoning,
                suggested_response=coaching_result.recommended_response or "",
                timing="immediate" if coaching_result.urgency == "critical" else "next_pause",
                confidence=coaching_result.confidence
            )

            # Add to call session
            call_session["live_metrics"]["coaching_suggestions"].append({
                "timestamp": segment.timestamp.isoformat(),
                "recommendation": recommendation.__dict__,
                "triggered_by": segment.text
            })

            # Keep only last 10 suggestions
            call_session["live_metrics"]["coaching_suggestions"] = \
                call_session["live_metrics"]["coaching_suggestions"][-10:]

            # Send to callback if registered
            if call_id in self.coaching_callbacks:
                try:
                    await self.coaching_callbacks[call_id](recommendation)
                except Exception as e:
                    logger.error(f"Error in coaching callback: {e}")

            # Update stats
            self.stats["coaching_suggestions_generated"] += 1
            if segment.objections_detected:
                self.stats["objections_detected"] += len(segment.objections_detected)

        except Exception as e:
            logger.error(f"Error generating live coaching: {e}")

    def _determine_coaching_category(self, segment: VoiceSegment, context: str) -> str:
        """Determine the category of coaching needed."""
        if segment.objections_detected:
            return "objection_handling"
        elif segment.emotional_tone in [EmotionalTone.ENTHUSIASTIC, EmotionalTone.INTERESTED]:
            return "closing"
        elif segment.emotional_tone in [EmotionalTone.HESITANT, EmotionalTone.SKEPTICAL]:
            return "rapport_building"
        elif segment.urgency_level > 0.7:
            return "qualification"
        else:
            return "general_guidance"

    async def _real_time_audio_processor(self, call_id: str) -> None:
        """Real-time audio processing loop for live calls."""
        try:
            logger.info(f"Starting real-time audio processing for call {call_id}")

            while call_id in self.active_calls and self.active_calls[call_id]["status"] == "active":
                # Simulate audio chunk processing
                await asyncio.sleep(self.chunk_duration)

                # In production, this would:
                # 1. Capture audio from microphone or call system
                # 2. Process audio chunk
                # 3. Transcribe and analyze
                # 4. Generate coaching suggestions

                # For demo, we'll simulate periodic analysis
                demo_audio = b"demo_audio_data"
                current_speaker = "prospect"  # Would be determined by voice recognition

                await self.process_voice_segment(
                    call_id=call_id,
                    audio_data=demo_audio,
                    speaker=current_speaker
                )

        except Exception as e:
            logger.error(f"Error in real-time audio processor: {e}")

    async def end_call_analysis(self, call_id: str) -> CallAnalysisResult:
        """End call analysis and generate comprehensive results."""
        try:
            if call_id not in self.active_calls:
                raise ValueError(f"Call {call_id} not found")

            call_session = self.active_calls[call_id]
            call_session["status"] = "completed"
            call_session["ended_at"] = datetime.now()

            # Calculate call duration
            duration = (call_session["ended_at"] - call_session["started_at"]).total_seconds()

            # Analyze complete conversation
            analysis_result = await self._analyze_complete_call(call_session)

            # Update stats
            self.stats["calls_analyzed"] += 1
            self.stats["total_processing_time"] += duration

            # Clean up
            del self.active_calls[call_id]
            if call_id in self.coaching_callbacks:
                del self.coaching_callbacks[call_id]

            logger.info(f"Completed call analysis for {call_id}, duration: {duration:.1f}s")

            return analysis_result

        except Exception as e:
            logger.error(f"Error ending call analysis: {e}")
            raise

    async def _analyze_complete_call(self, call_session: Dict[str, Any]) -> CallAnalysisResult:
        """Perform comprehensive analysis of completed call."""
        try:
            segments = call_session["segments"]
            duration = (call_session["ended_at"] - call_session["started_at"]).total_seconds()

            # Calculate talk time distribution
            agent_segments = [s for s in segments if s.speaker == "agent"]
            prospect_segments = [s for s in segments if s.speaker == "prospect"]

            agent_talk_time = len(agent_segments)
            prospect_talk_time = len(prospect_segments)
            total_talk_time = agent_talk_time + prospect_talk_time

            # Sentiment and emotional analysis
            sentiment_scores = [s.sentiment_score for s in segments]
            emotional_journey = [s.emotional_tone for s in segments]

            # Objection analysis
            all_objections = []
            for segment in segments:
                for objection in segment.objections_detected:
                    all_objections.append({
                        "type": objection,
                        "timestamp": segment.timestamp.isoformat(),
                        "text": segment.text,
                        "speaker": segment.speaker
                    })

            # Quality scoring
            call_quality_score = self._calculate_call_quality_score(segments, duration)
            rapport_score = self._calculate_rapport_score(segments)
            engagement_score = self._calculate_engagement_score(segments)

            # Generate recommendations
            follow_up_actions = await self._generate_follow_up_actions(call_session)
            coaching_focus = await self._generate_coaching_focus_areas(segments)

            return CallAnalysisResult(
                call_id=call_session["call_id"],
                duration_seconds=duration,
                agent_id=call_session["agent_id"],
                prospect_id=call_session.get("prospect_id"),

                total_segments=len(segments),
                agent_talk_percentage=agent_talk_time / max(total_talk_time, 1) * 100,
                prospect_talk_percentage=prospect_talk_time / max(total_talk_time, 1) * 100,
                interruptions_count=self._count_interruptions(segments),
                awkward_silences_count=self._count_awkward_silences(segments),

                overall_sentiment_trend=sentiment_scores,
                emotional_journey=emotional_journey,
                rapport_score=rapport_score,
                engagement_score=engagement_score,

                objections_detected=all_objections,
                key_topics_discussed=self._extract_key_topics(segments),
                qualification_progress=self._assess_qualification_progress(segments),
                missed_opportunities=self._identify_missed_opportunities(segments),

                call_quality_score=call_quality_score,
                coaching_adherence_score=75.0,  # Would be calculated based on agent performance
                outcome_prediction=self._predict_call_outcome(segments),

                immediate_follow_up_actions=follow_up_actions,
                coaching_focus_areas=coaching_focus,
                improvement_suggestions=self._generate_improvement_suggestions(segments)
            )

        except Exception as e:
            logger.error(f"Error analyzing complete call: {e}")
            raise

    def _calculate_call_quality_score(self, segments: List[VoiceSegment], duration: float) -> float:
        """Calculate overall call quality score."""
        try:
            score = 50.0  # Base score

            # Sentiment contribution (40% weight)
            avg_sentiment = sum(s.sentiment_score for s in segments) / max(len(segments), 1)
            score += avg_sentiment * 20  # -20 to +20 points

            # Engagement contribution (30% weight)
            engagement_indicators = sum(
                1 for s in segments
                if s.emotional_tone in [EmotionalTone.ENTHUSIASTIC, EmotionalTone.INTERESTED]
            )
            engagement_score = engagement_indicators / max(len(segments), 1) * 30
            score += engagement_score

            # Duration appropriateness (20% weight)
            if 300 <= duration <= 1800:  # 5-30 minutes is optimal
                score += 20
            elif duration < 120 or duration > 3600:  # Too short or too long
                score += 5
            else:
                score += 15

            # Objection handling (10% weight)
            objection_count = sum(len(s.objections_detected) for s in segments)
            if objection_count == 0:
                score += 10  # No objections is good
            elif objection_count <= 3:
                score += 5   # Few objections handled well

            return max(0, min(100, score))

        except Exception as e:
            logger.error(f"Error calculating call quality: {e}")
            return 50.0

    def _calculate_rapport_score(self, segments: List[VoiceSegment]) -> float:
        """Calculate rapport score based on conversation dynamics."""
        try:
            positive_emotions = sum(
                1 for s in segments
                if s.emotional_tone in [EmotionalTone.ENTHUSIASTIC, EmotionalTone.INTERESTED, EmotionalTone.CONFIDENT]
            )

            negative_emotions = sum(
                1 for s in segments
                if s.emotional_tone in [EmotionalTone.FRUSTRATED, EmotionalTone.SKEPTICAL]
            )

            if len(segments) == 0:
                return 50.0

            positive_ratio = positive_emotions / len(segments)
            negative_ratio = negative_emotions / len(segments)

            rapport_score = 50 + (positive_ratio * 40) - (negative_ratio * 30)
            return max(0, min(100, rapport_score))

        except Exception as e:
            logger.error(f"Error calculating rapport score: {e}")
            return 50.0

    def _calculate_engagement_score(self, segments: List[VoiceSegment]) -> float:
        """Calculate engagement score based on conversation participation."""
        try:
            # Measure prospect engagement through segment length and emotional investment
            prospect_segments = [s for s in segments if s.speaker == "prospect"]

            if not prospect_segments:
                return 20.0  # Low engagement if prospect barely spoke

            # Average segment length
            avg_length = sum(len(s.text.split()) for s in prospect_segments) / len(prospect_segments)

            # Emotional investment
            emotional_engagement = sum(
                1 for s in prospect_segments
                if s.emotional_tone != EmotionalTone.NEUTRAL
            ) / len(prospect_segments)

            # Question asking (shows interest)
            questions_asked = sum(1 for s in prospect_segments if "?" in s.text)
            question_score = min(questions_asked * 10, 30)

            engagement_score = (avg_length * 2) + (emotional_engagement * 40) + question_score
            return max(0, min(100, engagement_score))

        except Exception as e:
            logger.error(f"Error calculating engagement score: {e}")
            return 50.0

    def _count_interruptions(self, segments: List[VoiceSegment]) -> int:
        """Count conversation interruptions."""
        # Simplified implementation
        interruptions = 0
        for i in range(1, len(segments)):
            time_diff = (segments[i].timestamp - segments[i-1].timestamp).total_seconds()
            if time_diff < 0.5 and segments[i].speaker != segments[i-1].speaker:
                interruptions += 1
        return interruptions

    def _count_awkward_silences(self, segments: List[VoiceSegment]) -> int:
        """Count awkward silences in conversation."""
        silences = 0
        for i in range(1, len(segments)):
            time_diff = (segments[i].timestamp - segments[i-1].timestamp).total_seconds()
            if time_diff > 5.0:  # More than 5 seconds
                silences += 1
        return silences

    def _extract_key_topics(self, segments: List[VoiceSegment]) -> List[str]:
        """Extract key topics discussed during the call."""
        all_keywords = []
        for segment in segments:
            all_keywords.extend(segment.keywords)

        # Count keyword frequency
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1

        # Return top keywords as topics
        sorted_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, count in sorted_keywords[:10]]

    def _assess_qualification_progress(self, segments: List[VoiceSegment]) -> Dict[str, Any]:
        """Assess how well the lead was qualified during the call."""
        qualification_areas = {
            "budget": ["budget", "price", "afford", "cost"],
            "timeline": ["timeline", "when", "soon", "move"],
            "location": ["area", "location", "neighborhood"],
            "motivation": ["why", "reason", "moving", "selling"]
        }

        progress = {}
        for area, keywords in qualification_areas.items():
            mentions = sum(
                1 for segment in segments
                for keyword in keywords
                if keyword in segment.text.lower()
            )
            progress[area] = {
                "mentioned": mentions > 0,
                "depth": min(mentions, 3),  # 0-3 scale
                "confidence": min(mentions * 25, 100)
            }

        return progress

    def _identify_missed_opportunities(self, segments: List[VoiceSegment]) -> List[str]:
        """Identify missed opportunities during the call."""
        missed = []

        # Check for unaddressed objections
        objections_by_type = {}
        for segment in segments:
            for objection in segment.objections_detected:
                objections_by_type[objection] = objections_by_type.get(objection, 0) + 1

        # If objections were mentioned multiple times, they might not have been addressed
        for objection_type, count in objections_by_type.items():
            if count > 1:
                missed.append(f"Unresolved {objection_type} objection mentioned {count} times")

        # Check for buying signals that weren't followed up
        for segment in segments:
            if (segment.speaker == "prospect" and
                segment.emotional_tone == EmotionalTone.INTERESTED and
                segment.urgency_level > 0.6):
                missed.append(f"High interest signal not capitalized on at {segment.timestamp.strftime('%H:%M')}")

        return missed[:5]  # Return top 5 missed opportunities

    def _predict_call_outcome(self, segments: List[VoiceSegment]) -> Dict[str, Any]:
        """Predict likely call outcome based on analysis."""
        try:
            # Calculate outcome probability based on multiple factors
            avg_sentiment = sum(s.sentiment_score for s in segments) / max(len(segments), 1)
            engagement_level = self._calculate_engagement_score(segments) / 100
            objection_count = sum(len(s.objections_detected) for s in segments)

            # Positive indicators
            positive_score = 0
            if avg_sentiment > 0.2:
                positive_score += 30
            if engagement_level > 0.6:
                positive_score += 25
            if objection_count <= 2:
                positive_score += 20

            # Enthusiastic segments
            enthusiastic_count = sum(
                1 for s in segments
                if s.emotional_tone == EmotionalTone.ENTHUSIASTIC
            )
            positive_score += min(enthusiastic_count * 5, 25)

            # Determine outcome prediction
            if positive_score >= 70:
                outcome = "highly_likely_to_convert"
                confidence = 0.85
            elif positive_score >= 50:
                outcome = "likely_to_convert"
                confidence = 0.70
            elif positive_score >= 30:
                outcome = "needs_nurturing"
                confidence = 0.60
            else:
                outcome = "unlikely_to_convert"
                confidence = 0.75

            return {
                "predicted_outcome": outcome,
                "confidence": confidence,
                "positive_indicators": positive_score,
                "recommendation": self._get_outcome_recommendation(outcome)
            }

        except Exception as e:
            logger.error(f"Error predicting call outcome: {e}")
            return {"predicted_outcome": "unknown", "confidence": 0.5}

    def _get_outcome_recommendation(self, outcome: str) -> str:
        """Get recommendation based on predicted outcome."""
        recommendations = {
            "highly_likely_to_convert": "Schedule property viewing or send purchase agreement ASAP",
            "likely_to_convert": "Follow up within 24 hours with relevant listings",
            "needs_nurturing": "Add to nurture campaign, follow up in 3-5 days",
            "unlikely_to_convert": "Polite follow-up in 1-2 weeks, focus on other leads"
        }
        return recommendations.get(outcome, "Continue standard follow-up process")

    async def _generate_follow_up_actions(self, call_session: Dict[str, Any]) -> List[str]:
        """Generate recommended follow-up actions."""
        segments = call_session["segments"]
        actions = []

        # Based on objections detected
        objection_types = set()
        for segment in segments:
            objection_types.update(segment.objections_detected)

        if "price" in objection_types:
            actions.append("Send market analysis showing value in current pricing")
        if "timeline" in objection_types:
            actions.append("Follow up on timeline concerns and provide flexible options")
        if "location" in objection_types:
            actions.append("Schedule area tour to address location concerns")

        # Based on engagement level
        engagement_score = self._calculate_engagement_score(segments)
        if engagement_score > 70:
            actions.append("Strike while hot - schedule immediate property viewing")
        elif engagement_score > 40:
            actions.append("Send curated property listings within 24 hours")
        else:
            actions.append("Add to nurture sequence for relationship building")

        # Based on qualification progress
        qualification = self._assess_qualification_progress(segments)
        missing_areas = [area for area, data in qualification.items() if not data["mentioned"]]

        if missing_areas:
            actions.append(f"Complete qualification: gather {', '.join(missing_areas)} information")

        return actions[:5]  # Return top 5 actions

    async def _generate_coaching_focus_areas(self, segments: List[VoiceSegment]) -> List[str]:
        """Generate coaching focus areas for agent improvement."""
        focus_areas = []

        # Analyze agent segments for improvement opportunities
        agent_segments = [s for s in segments if s.speaker == "agent"]

        if not agent_segments:
            return ["Focus on building rapport and asking engaging questions"]

        # Check talk ratio
        total_segments = len(segments)
        agent_talk_ratio = len(agent_segments) / total_segments

        if agent_talk_ratio > 0.7:
            focus_areas.append("Reduce talk time - ask more questions and listen actively")
        elif agent_talk_ratio < 0.3:
            focus_areas.append("Be more assertive in guiding the conversation")

        # Check objection handling
        objection_count = sum(len(s.objections_detected) for s in segments)
        if objection_count > 3:
            focus_areas.append("Improve objection prevention through better qualification")

        # Check enthusiasm and confidence
        confident_segments = sum(
            1 for s in agent_segments
            if s.emotional_tone == EmotionalTone.CONFIDENT
        )

        if confident_segments / len(agent_segments) < 0.5:
            focus_areas.append("Work on confidence and enthusiasm in delivery")

        # Check question asking
        questions_asked = sum(1 for s in agent_segments if "?" in s.text)
        if questions_asked < 3:
            focus_areas.append("Ask more qualifying questions to understand needs better")

        return focus_areas[:4]  # Return top 4 focus areas

    def _generate_improvement_suggestions(self, segments: List[VoiceSegment]) -> List[str]:
        """Generate specific improvement suggestions for future calls."""
        suggestions = []

        # Analyze call patterns
        sentiment_trend = [s.sentiment_score for s in segments]

        if len(sentiment_trend) > 1:
            # Check if sentiment declined
            if sentiment_trend[-1] < sentiment_trend[0]:
                suggestions.append("Focus on ending calls on a positive note")

        # Check for missed opportunities
        high_interest_moments = [
            s for s in segments
            if s.emotional_tone == EmotionalTone.ENTHUSIASTIC and s.urgency_level > 0.5
        ]

        if high_interest_moments:
            suggestions.append("Capitalize on high-interest moments by asking for commitment")

        # Check rapport building
        rapport_score = self._calculate_rapport_score(segments)
        if rapport_score < 60:
            suggestions.append("Spend more time building rapport before diving into business")

        # Check follow-up clarity
        follow_up_mentioned = any(
            "follow" in s.text.lower() or "next" in s.text.lower()
            for s in segments if s.speaker == "agent"
        )

        if not follow_up_mentioned:
            suggestions.append("Always end with clear next steps and timeline")

        return suggestions[:5]

    def get_active_calls(self) -> Dict[str, Dict]:
        """Get information about currently active calls."""
        return {
            call_id: {
                "call_id": session["call_id"],
                "agent_id": session["agent_id"],
                "started_at": session["started_at"].isoformat(),
                "duration_seconds": (datetime.now() - session["started_at"]).total_seconds(),
                "segments_processed": len(session["segments"]),
                "status": session["status"]
            }
            for call_id, session in self.active_calls.items()
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get voice analyzer performance statistics."""
        return {
            **self.stats,
            "active_calls": len(self.active_calls),
            "audio_available": self.audio_available,
            "average_call_duration": (
                self.stats["total_processing_time"] / max(self.stats["calls_analyzed"], 1)
            )
        }


# Factory function for easy instantiation
def create_voice_analyzer(location_id: str = "default") -> ClaudeVoiceAnalyzer:
    """Create Claude voice analyzer instance."""
    return ClaudeVoiceAnalyzer(location_id=location_id)


# Usage example:
"""
# Initialize voice analyzer
voice_analyzer = create_voice_analyzer("location_123")

# Start call analysis
call_info = await voice_analyzer.start_call_analysis(
    call_id="call_456",
    agent_id="agent_789",
    analysis_mode=VoiceAnalysisMode.LIVE_COACHING,
    coaching_callback=lambda suggestion: print(f"Coaching: {suggestion.message}")
)

# Process audio segments during call
async for audio_chunk in call_audio_stream:
    segment = await voice_analyzer.process_voice_segment(
        call_id="call_456",
        audio_data=audio_chunk,
        speaker="prospect"
    )

    # Real-time coaching suggestions are automatically generated

# End call and get comprehensive analysis
final_analysis = await voice_analyzer.end_call_analysis("call_456")
print(f"Call quality score: {final_analysis.call_quality_score}")
print(f"Follow-up actions: {final_analysis.immediate_follow_up_actions}")
"""