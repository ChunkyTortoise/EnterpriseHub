"""
Claude Streaming Response Service - Real-time Response Streaming

Provides real-time streaming Claude responses for improved UX in coaching,
qualification, and semantic analysis with token-by-token delivery.

Features:
- Token-level streaming for real-time feedback
- Adaptive response caching for performance
- Event-driven updates to WebSocket clients
- Graceful fallback to standard responses
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from anthropic import AsyncAnthropic
import redis.asyncio as redis

from ..ghl_utils.config import settings
from .websocket_manager import get_websocket_manager, IntelligenceEventType
from .claude_agent_service import ClaudeResponse, CoachingResponse

logger = logging.getLogger(__name__)


class StreamingType(Enum):
    """Types of streaming responses."""
    COACHING = "coaching"
    QUALIFICATION = "qualification"
    SEMANTIC_ANALYSIS = "semantic_analysis"
    CONVERSATION = "conversation"


@dataclass
class StreamingToken:
    """Individual token in streaming response."""
    token: str
    timestamp: datetime
    confidence: float
    is_complete: bool = False
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class StreamingResponse:
    """Complete streaming response with accumulated content."""
    stream_id: str
    stream_type: StreamingType
    agent_id: str
    total_tokens: int
    accumulated_content: str
    final_response: Optional[ClaudeResponse] = None
    coaching_response: Optional[CoachingResponse] = None
    processing_time_ms: float = 0.0
    cache_hit: bool = False


class ClaudeStreamingService:
    """
    Advanced Claude streaming service for real-time response delivery.

    Provides token-level streaming with intelligent caching and WebSocket
    integration for maximum responsiveness.
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.websocket_manager = get_websocket_manager()
        self.redis_client = None
        self.active_streams: Dict[str, StreamingResponse] = {}

        # Initialize Redis for caching
        self._init_redis()

    async def _init_redis(self):
        """Initialize Redis connection for response caching."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Claude streaming service Redis connection established")
        except Exception as e:
            logger.warning(f"Redis unavailable for streaming service: {e}")
            self.redis_client = None

    async def start_streaming_coaching(
        self,
        agent_id: str,
        conversation_context: Dict[str, Any],
        prospect_message: str,
        conversation_stage: str
    ) -> str:
        """
        Start streaming real-time coaching response.

        Returns:
            stream_id: Unique identifier for this streaming session
        """
        stream_id = f"coaching_{agent_id}_{int(datetime.now().timestamp()*1000)}"

        try:
            # Check cache first for similar requests
            cache_key = self._generate_cache_key("coaching", {
                "stage": conversation_stage,
                "message_hash": hash(prospect_message),
                "context_hash": hash(str(conversation_context))
            })

            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                await self._deliver_cached_coaching(stream_id, agent_id, cached_response)
                return stream_id

            # Start streaming generation
            self.active_streams[stream_id] = StreamingResponse(
                stream_id=stream_id,
                stream_type=StreamingType.COACHING,
                agent_id=agent_id,
                total_tokens=0,
                accumulated_content=""
            )

            # Start background streaming task
            asyncio.create_task(self._stream_coaching_response(
                stream_id, agent_id, conversation_context, prospect_message, conversation_stage
            ))

            logger.info(f"Started streaming coaching for agent {agent_id}, stream: {stream_id}")
            return stream_id

        except Exception as e:
            logger.error(f"Error starting streaming coaching: {e}")
            raise

    async def _stream_coaching_response(
        self,
        stream_id: str,
        agent_id: str,
        conversation_context: Dict[str, Any],
        prospect_message: str,
        conversation_stage: str
    ):
        """Stream coaching response token by token."""
        start_time = datetime.now()

        try:
            # Build coaching prompt (reuse from existing service)
            from .claude_agent_service import claude_agent_service

            coaching_prompt = await claude_agent_service._build_coaching_system_prompt(
                agent_id, conversation_stage, conversation_context
            )

            coaching_query = f"""
            REAL-TIME COACHING REQUEST:

            Agent: {agent_id}
            Conversation Stage: {conversation_stage}
            Latest Prospect Message: "{prospect_message}"
            Context: {json.dumps(conversation_context, indent=2)}

            Please provide immediate coaching:
            1. What should they focus on in their response?
            2. Are there any objections to detect and address?
            3. What's the recommended next question?
            4. How urgent is this situation?
            """

            # Start streaming from Claude
            accumulated_content = ""
            async with self.client.messages.stream(
                model=settings.claude_model,
                max_tokens=600,
                temperature=0.3,
                system=coaching_prompt,
                messages=[{"role": "user", "content": coaching_query}]
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta" and hasattr(event.delta, 'text'):
                        token_text = event.delta.text
                        accumulated_content += token_text

                        # Create streaming token
                        token = StreamingToken(
                            token=token_text,
                            timestamp=datetime.now(),
                            confidence=0.8,  # Adjust based on context
                            metadata={"stream_id": stream_id, "agent_id": agent_id}
                        )

                        # Update active stream
                        if stream_id in self.active_streams:
                            self.active_streams[stream_id].accumulated_content = accumulated_content
                            self.active_streams[stream_id].total_tokens += 1

                        # Broadcast token to WebSocket clients
                        await self._broadcast_token_update(agent_id, token)

            # Generate final coaching response
            final_response = await claude_agent_service._parse_coaching_response(
                accumulated_content, conversation_stage, prospect_message
            )

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Update stream with final response
            if stream_id in self.active_streams:
                self.active_streams[stream_id].coaching_response = final_response
                self.active_streams[stream_id].processing_time_ms = processing_time

            # Cache successful response
            await self._cache_response(
                self._generate_cache_key("coaching", {
                    "stage": conversation_stage,
                    "message_hash": hash(prospect_message),
                    "context_hash": hash(str(conversation_context))
                }),
                {
                    "content": accumulated_content,
                    "coaching_response": asdict(final_response),
                    "processing_time_ms": processing_time
                }
            )

            # Broadcast completion
            await self._broadcast_stream_completion(stream_id, agent_id, final_response)

            logger.info(f"Completed streaming coaching for {agent_id} in {processing_time:.2f}ms")

        except Exception as e:
            logger.error(f"Error in streaming coaching: {e}")
            await self._broadcast_stream_error(stream_id, agent_id, str(e))

    async def start_streaming_qualification(
        self,
        agent_id: str,
        contact_data: Dict[str, Any],
        conversation_history: List[Dict]
    ) -> str:
        """Start streaming intelligent qualification analysis."""
        stream_id = f"qualification_{agent_id}_{int(datetime.now().timestamp()*1000)}"

        try:
            self.active_streams[stream_id] = StreamingResponse(
                stream_id=stream_id,
                stream_type=StreamingType.QUALIFICATION,
                agent_id=agent_id,
                total_tokens=0,
                accumulated_content=""
            )

            # Start background streaming task
            asyncio.create_task(self._stream_qualification_analysis(
                stream_id, agent_id, contact_data, conversation_history
            ))

            return stream_id

        except Exception as e:
            logger.error(f"Error starting streaming qualification: {e}")
            raise

    async def _stream_qualification_analysis(
        self,
        stream_id: str,
        agent_id: str,
        contact_data: Dict[str, Any],
        conversation_history: List[Dict]
    ):
        """Stream qualification analysis response."""
        start_time = datetime.now()

        try:
            # Build qualification analysis prompt
            qualification_prompt = f"""You are an expert real estate qualification analyst. Analyze this lead's qualification status and provide intelligent recommendations.

            Lead Data: {json.dumps(contact_data, indent=2)}
            Conversation History: {json.dumps(conversation_history[-5:], indent=2)}

            Please provide:
            1. Qualification completeness assessment (0-100%)
            2. Missing qualification areas
            3. Recommended next questions
            4. Lead readiness score
            5. Urgency assessment
            """

            # Stream qualification analysis
            accumulated_content = ""
            async with self.client.messages.stream(
                model=settings.claude_model,
                max_tokens=800,
                temperature=0.4,
                system=qualification_prompt,
                messages=[{"role": "user", "content": "Analyze this lead's qualification status and provide recommendations."}]
            ) as stream:
                async for event in stream:
                    if event.type == "content_block_delta" and hasattr(event.delta, 'text'):
                        token_text = event.delta.text
                        accumulated_content += token_text

                        # Create and broadcast token
                        token = StreamingToken(
                            token=token_text,
                            timestamp=datetime.now(),
                            confidence=0.85,
                            metadata={"stream_id": stream_id, "type": "qualification"}
                        )

                        await self._broadcast_token_update(agent_id, token)

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Parse qualification analysis
            qualification_analysis = await self._parse_qualification_analysis(accumulated_content)

            # Update stream
            if stream_id in self.active_streams:
                self.active_streams[stream_id].accumulated_content = accumulated_content
                self.active_streams[stream_id].processing_time_ms = processing_time

            # Broadcast completion
            await self._broadcast_qualification_completion(stream_id, agent_id, qualification_analysis)

            logger.info(f"Completed streaming qualification analysis in {processing_time:.2f}ms")

        except Exception as e:
            logger.error(f"Error in streaming qualification: {e}")
            await self._broadcast_stream_error(stream_id, agent_id, str(e))

    async def _broadcast_token_update(self, agent_id: str, token: StreamingToken):
        """Broadcast streaming token to WebSocket clients."""
        try:
            await self.websocket_manager.broadcast_intelligence_update(
                IntelligenceEventType.REAL_TIME_COACHING,
                {
                    "type": "token_update",
                    "agent_id": agent_id,
                    "token": asdict(token),
                    "timestamp": datetime.now().isoformat()
                },
                subscribers=[agent_id]  # Send only to specific agent
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast token update: {e}")

    async def _broadcast_stream_completion(self, stream_id: str, agent_id: str, response: Any):
        """Broadcast stream completion to WebSocket clients."""
        try:
            await self.websocket_manager.broadcast_intelligence_update(
                IntelligenceEventType.REAL_TIME_COACHING,
                {
                    "type": "stream_complete",
                    "stream_id": stream_id,
                    "agent_id": agent_id,
                    "final_response": asdict(response) if hasattr(response, '__dict__') else response,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast stream completion: {e}")

    async def _broadcast_qualification_completion(self, stream_id: str, agent_id: str, analysis: Dict):
        """Broadcast qualification analysis completion."""
        try:
            await self.websocket_manager.broadcast_intelligence_update(
                IntelligenceEventType.QUALIFICATION_UPDATE,
                {
                    "type": "qualification_complete",
                    "stream_id": stream_id,
                    "agent_id": agent_id,
                    "analysis": analysis,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast qualification completion: {e}")

    async def _broadcast_stream_error(self, stream_id: str, agent_id: str, error: str):
        """Broadcast stream error to WebSocket clients."""
        try:
            await self.websocket_manager.broadcast_intelligence_update(
                IntelligenceEventType.ERROR,
                {
                    "type": "stream_error",
                    "stream_id": stream_id,
                    "agent_id": agent_id,
                    "error": error,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast stream error: {e}")

    async def _parse_qualification_analysis(self, content: str) -> Dict[str, Any]:
        """Parse streamed qualification analysis content."""
        try:
            # Extract key metrics from the content
            analysis = {
                "qualification_score": 0,
                "missing_areas": [],
                "next_questions": [],
                "readiness_level": "unknown",
                "urgency": "medium",
                "recommendations": []
            }

            lines = content.split('\n')
            for line in lines:
                line = line.strip()

                # Extract qualification percentage
                if any(keyword in line.lower() for keyword in ["qualification", "complete", "%"]):
                    import re
                    percentage_match = re.search(r'(\d{1,3})%', line)
                    if percentage_match:
                        analysis["qualification_score"] = int(percentage_match.group(1))

                # Extract recommendations
                if line.startswith('-') and len(line) > 10:
                    if "question" in line.lower():
                        analysis["next_questions"].append(line.lstrip('- '))
                    elif "missing" in line.lower():
                        analysis["missing_areas"].append(line.lstrip('- '))
                    else:
                        analysis["recommendations"].append(line.lstrip('- '))

            return analysis

        except Exception as e:
            logger.warning(f"Error parsing qualification analysis: {e}")
            return {
                "qualification_score": 50,
                "missing_areas": ["Analysis parsing error"],
                "next_questions": ["What's most important to you in your next home?"],
                "readiness_level": "unknown",
                "urgency": "medium",
                "recommendations": ["Review lead data and schedule follow-up"]
            }

    def _generate_cache_key(self, response_type: str, context: Dict[str, Any]) -> str:
        """Generate cache key for response caching."""
        import hashlib
        context_str = json.dumps(context, sort_keys=True)
        hash_obj = hashlib.md5(context_str.encode())
        return f"claude_stream:{response_type}:{hash_obj.hexdigest()}"

    async def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Get cached response if available."""
        if not self.redis_client:
            return None

        try:
            cached = await self.redis_client.get(cache_key)
            return json.loads(cached) if cached else None
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
            return None

    async def _cache_response(self, cache_key: str, response: Dict, ttl_seconds: int = 300):
        """Cache response for future use."""
        if not self.redis_client:
            return

        try:
            await self.redis_client.setex(
                cache_key,
                ttl_seconds,
                json.dumps(response, default=str)
            )
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    async def _deliver_cached_coaching(self, stream_id: str, agent_id: str, cached_response: Dict):
        """Deliver cached coaching response as streaming tokens."""
        try:
            content = cached_response.get("content", "")
            coaching_data = cached_response.get("coaching_response", {})

            # Simulate streaming by sending content in chunks
            chunk_size = 10  # tokens per chunk
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]

            for i, chunk in enumerate(chunks):
                token = StreamingToken(
                    token=chunk,
                    timestamp=datetime.now(),
                    confidence=0.95,  # High confidence for cached content
                    is_complete=(i == len(chunks) - 1),
                    metadata={"cached": True, "stream_id": stream_id}
                )

                await self._broadcast_token_update(agent_id, token)
                await asyncio.sleep(0.02)  # Small delay to simulate streaming

            # Create coaching response from cached data
            from .claude_agent_service import CoachingResponse
            coaching_response = CoachingResponse(**coaching_data)

            await self._broadcast_stream_completion(stream_id, agent_id, coaching_response)

        except Exception as e:
            logger.error(f"Error delivering cached response: {e}")

    async def get_stream_status(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a streaming session."""
        if stream_id not in self.active_streams:
            return None

        stream = self.active_streams[stream_id]
        return {
            "stream_id": stream_id,
            "type": stream.stream_type.value,
            "agent_id": stream.agent_id,
            "tokens_received": stream.total_tokens,
            "content_length": len(stream.accumulated_content),
            "is_complete": stream.final_response is not None or stream.coaching_response is not None,
            "processing_time_ms": stream.processing_time_ms
        }

    async def cleanup_completed_streams(self, max_age_minutes: int = 30):
        """Clean up old completed streaming sessions."""
        cutoff_time = datetime.now() - timedelta(minutes=max_age_minutes)
        completed_streams = []

        for stream_id, stream in self.active_streams.items():
            if (stream.final_response or stream.coaching_response) and \
               datetime.now() - timedelta(seconds=stream.processing_time_ms/1000) < cutoff_time:
                completed_streams.append(stream_id)

        for stream_id in completed_streams:
            del self.active_streams[stream_id]

        if completed_streams:
            logger.info(f"Cleaned up {len(completed_streams)} completed streams")


# Global instance
claude_streaming_service = ClaudeStreamingService()


async def get_claude_streaming_service() -> ClaudeStreamingService:
    """Get global Claude streaming service instance."""
    return claude_streaming_service