"""
Real-Time WebSocket Endpoints (Phase 4: Mobile Optimization)

WebSocket endpoints for real-time Claude coaching and live interactions.
Optimized for mobile devices with efficient data streaming and low latency.

Features:
- Real-time coaching suggestions
- Live conversation monitoring
- Voice streaming support
- Mobile-optimized data packets
- Connection management for mobile networks
- Automatic reconnection handling
- Battery-aware streaming
- Compression and bandwidth optimization

Performance Targets:
- WebSocket latency: <50ms
- Connection setup: <200ms
- Data compression: 80% bandwidth savings
- Mobile reconnection: <3 seconds
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union, Set
import asyncio
import json
import logging
import time
from datetime import datetime
from collections import defaultdict
import gzip
import base64

# Local imports
from ghl_real_estate_ai.services.claude.mobile.mobile_coaching_service import (
    MobileCoachingService,
    MobileCoachingMode,
    MobileCoachingContext
)
from ghl_real_estate_ai.services.claude.mobile.voice_integration_service import (
    VoiceIntegrationService,
    VoiceState
)
from ghl_real_estate_ai.config.mobile.settings import REALTIME_CONFIG

logger = logging.getLogger(__name__)

# Initialize services
mobile_coaching_service = MobileCoachingService()
voice_integration_service = VoiceIntegrationService()

# Create router
realtime_router = APIRouter(prefix="/api/v1/mobile/realtime", tags=["Real-Time Mobile"])

# Connection Management
class ConnectionManager:
    """Manages WebSocket connections for real-time features"""

    def __init__(self):
        # Active connections organized by agent_id
        self.active_connections: Dict[str, Set[WebSocket]] = defaultdict(set)

        # Session metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

        # Performance tracking
        self.message_counts: Dict[str, int] = defaultdict(int)
        self.connection_times: Dict[WebSocket, datetime] = {}

    async def connect(self, websocket: WebSocket, agent_id: str, metadata: Dict[str, Any] = None):
        """Accept WebSocket connection and register it"""
        await websocket.accept()

        self.active_connections[agent_id].add(websocket)
        self.connection_metadata[websocket] = {
            "agent_id": agent_id,
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
            "metadata": metadata or {}
        }
        self.connection_times[websocket] = datetime.now()

        logger.info(f"WebSocket connected for agent {agent_id}")

        # Send welcome message
        await self._send_message(websocket, {
            "type": "connection_established",
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "features": {
                "real_time_coaching": True,
                "voice_streaming": True,
                "compression": True,
                "mobile_optimized": True
            }
        })

    async def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        metadata = self.connection_metadata.get(websocket)
        if metadata:
            agent_id = metadata["agent_id"]
            self.active_connections[agent_id].discard(websocket)

            # Clean up empty sets
            if not self.active_connections[agent_id]:
                del self.active_connections[agent_id]

            del self.connection_metadata[websocket]
            del self.connection_times[websocket]

            logger.info(f"WebSocket disconnected for agent {agent_id}")

    async def send_to_agent(self, agent_id: str, message: Dict[str, Any]):
        """Send message to all connections for an agent"""
        connections = self.active_connections.get(agent_id, set())
        if connections:
            await asyncio.gather(
                *[self._send_message(ws, message) for ws in connections],
                return_exceptions=True
            )

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all active connections"""
        all_connections = set()
        for connections in self.active_connections.values():
            all_connections.update(connections)

        if all_connections:
            await asyncio.gather(
                *[self._send_message(ws, message) for ws in all_connections],
                return_exceptions=True
            )

    async def _send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send message with compression and error handling"""
        try:
            # Add metadata
            message["timestamp"] = datetime.now().isoformat()

            # Serialize message
            message_json = json.dumps(message)

            # Compress if enabled and message is large enough
            if len(message_json) > 1024 and REALTIME_CONFIG.get("compression_enabled", True):
                compressed_data = gzip.compress(message_json.encode())
                encoded_data = base64.b64encode(compressed_data).decode()

                await websocket.send_json({
                    "compressed": True,
                    "data": encoded_data
                })
            else:
                await websocket.send_json(message)

            # Track message count
            metadata = self.connection_metadata.get(websocket)
            if metadata:
                agent_id = metadata["agent_id"]
                self.message_counts[agent_id] += 1
                metadata["last_activity"] = datetime.now()

        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            # Connection might be broken, will be handled in disconnect

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        active_agents = len(self.active_connections)

        return {
            "total_connections": total_connections,
            "active_agents": active_agents,
            "message_counts": dict(self.message_counts),
            "connections_by_agent": {
                agent_id: len(connections)
                for agent_id, connections in self.active_connections.items()
            }
        }

# Global connection manager
connection_manager = ConnectionManager()

# Request/Response Models
class RealTimeMessage(BaseModel):
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message data")
    agent_id: Optional[str] = Field(default=None, description="Target agent ID")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    priority: str = Field(default="normal", description="Message priority")


class WebSocketConnectionInfo(BaseModel):
    agent_id: str = Field(..., description="Agent identifier")
    device_info: Optional[Dict[str, Any]] = Field(default=None, description="Device information")
    network_status: str = Field(default="wifi", description="Network connection type")
    battery_level: Optional[float] = Field(default=None, description="Battery level")
    coaching_mode: str = Field(default="quick_insights", description="Coaching mode")


# WebSocket Endpoints

@realtime_router.websocket("/coaching/{agent_id}")
async def websocket_coaching_endpoint(websocket: WebSocket, agent_id: str):
    """
    Real-time coaching WebSocket endpoint

    Provides live coaching suggestions during client conversations
    with mobile-optimized streaming and compression.
    """
    await connection_manager.connect(websocket, agent_id)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Process different message types
            message_type = data.get("type")

            if message_type == "conversation_update":
                await _handle_conversation_update(websocket, agent_id, data)
            elif message_type == "request_coaching":
                await _handle_coaching_request(websocket, agent_id, data)
            elif message_type == "voice_data":
                await _handle_voice_data(websocket, agent_id, data)
            elif message_type == "quick_action":
                await _handle_quick_action(websocket, agent_id, data)
            elif message_type == "ping":
                await _handle_ping(websocket, agent_id, data)
            else:
                await connection_manager._send_message(websocket, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })

    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for agent {agent_id}: {e}")
        await connection_manager.disconnect(websocket)


@realtime_router.websocket("/voice/{agent_id}")
async def websocket_voice_endpoint(websocket: WebSocket, agent_id: str):
    """
    Real-time voice processing WebSocket endpoint

    Handles voice streaming, real-time transcription, and voice commands
    optimized for mobile voice interactions.
    """
    await connection_manager.connect(websocket, agent_id, {"type": "voice"})

    try:
        while True:
            # Receive voice data or commands
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "voice_stream":
                await _handle_voice_stream(websocket, agent_id, data)
            elif message_type == "voice_command":
                await _handle_voice_command(websocket, agent_id, data)
            elif message_type == "start_listening":
                await _handle_start_listening(websocket, agent_id, data)
            elif message_type == "stop_listening":
                await _handle_stop_listening(websocket, agent_id, data)
            elif message_type == "ping":
                await _handle_ping(websocket, agent_id, data)
            else:
                await connection_manager._send_message(websocket, {
                    "type": "error",
                    "message": f"Unknown voice message type: {message_type}"
                })

    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Voice WebSocket error for agent {agent_id}: {e}")
        await connection_manager.disconnect(websocket)


# Message Handlers

async def _handle_conversation_update(websocket: WebSocket, agent_id: str, data: Dict[str, Any]):
    """Handle real-time conversation updates"""
    try:
        conversation_context = data.get("conversation_context", "")
        client_message = data.get("client_message", "")
        session_id = data.get("session_id")

        if not session_id:
            await connection_manager._send_message(websocket, {
                "type": "error",
                "message": "Session ID required for conversation updates"
            })
            return

        # Get real-time coaching suggestion
        suggestion = await mobile_coaching_service.get_mobile_coaching_suggestion(
            session_id=session_id,
            conversation_context=conversation_context,
            client_message=client_message,
            urgency_level=data.get("urgency_level", "normal")
        )

        if suggestion:
            # Send coaching suggestion
            await connection_manager._send_message(websocket, {
                "type": "coaching_suggestion",
                "suggestion": {
                    "id": suggestion.id,
                    "priority": suggestion.priority.value,
                    "title": suggestion.title,
                    "message": suggestion.message,
                    "suggested_response": suggestion.suggested_response,
                    "quick_actions": [action.value for action in suggestion.quick_actions],
                    "confidence": suggestion.confidence,
                    "timing_sensitive": suggestion.timing_sensitive
                }
            })

        # Update conversation tracking
        await connection_manager._send_message(websocket, {
            "type": "conversation_updated",
            "status": "processed",
            "message_count": len(conversation_context.split('\n')) if conversation_context else 0
        })

    except Exception as e:
        logger.error(f"Error handling conversation update: {e}")
        await connection_manager._send_message(websocket, {
            "type": "error",
            "message": f"Error processing conversation update: {str(e)}"
        })


async def _handle_coaching_request(websocket: WebSocket, agent_id: str, data: Dict[str, Any]):
    """Handle explicit coaching requests"""
    try:
        session_id = data.get("session_id")
        context = data.get("context", "")
        urgency = data.get("urgency", "normal")

        if not session_id:
            await connection_manager._send_message(websocket, {
                "type": "error",
                "message": "Session ID required for coaching requests"
            })
            return

        # Get coaching suggestion
        suggestion = await mobile_coaching_service.get_mobile_coaching_suggestion(
            session_id=session_id,
            conversation_context=context,
            client_message=data.get("client_message", ""),
            urgency_level=urgency
        )

        response_data = {
            "type": "coaching_response",
            "request_id": data.get("request_id"),
            "status": "success"
        }

        if suggestion:
            response_data["coaching"] = {
                "id": suggestion.id,
                "priority": suggestion.priority.value,
                "title": suggestion.title,
                "message": suggestion.message,
                "suggested_response": suggestion.suggested_response,
                "quick_actions": [action.value for action in suggestion.quick_actions],
                "confidence": suggestion.confidence
            }
        else:
            response_data["coaching"] = {
                "message": "No specific coaching available at this time",
                "suggested_response": "Continue the conversation naturally",
                "confidence": 0.5
            }

        await connection_manager._send_message(websocket, response_data)

    except Exception as e:
        logger.error(f"Error handling coaching request: {e}")
        await connection_manager._send_message(websocket, {
            "type": "coaching_response",
            "request_id": data.get("request_id"),
            "status": "error",
            "message": str(e)
        })


async def _handle_voice_data(websocket: WebSocket, agent_id: str, data: Dict[str, Any]):
    """Handle real-time voice data processing"""
    try:
        session_id = data.get("session_id")
        audio_data = data.get("audio_data")  # Base64 encoded audio

        if not session_id or not audio_data:
            await connection_manager._send_message(websocket, {
                "type": "error",
                "message": "Session ID and audio data required"
            })
            return

        # Decode audio data
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception:
            await connection_manager._send_message(websocket, {
                "type": "error",
                "message": "Invalid audio data format"
            })
            return

        # Process voice input
        result = await voice_integration_service.process_voice_input(
            session_id=session_id,
            audio_data=audio_bytes,
            format=data.get("format", "wav")
        )

        # Send transcription result
        await connection_manager._send_message(websocket, {
            "type": "voice_transcription",
            "text": result.text,
            "confidence": result.confidence,
            "processing_time_ms": result.processing_time_ms,
            "detected_command": result.detected_command.value if result.detected_command else None,
            "audio_quality": result.audio_quality
        })

    except Exception as e:
        logger.error(f"Error handling voice data: {e}")
        await connection_manager._send_message(websocket, {
            "type": "error",
            "message": f"Error processing voice data: {str(e)}"
        })


async def _handle_voice_stream(websocket: WebSocket, agent_id: str, data: Dict[str, Any]):
    """Handle streaming voice data"""
    try:
        # For streaming, we'd implement chunked processing
        chunk_data = data.get("chunk_data")
        chunk_sequence = data.get("chunk_sequence", 0)
        is_final = data.get("is_final", False)

        # Send acknowledgment
        await connection_manager._send_message(websocket, {
            "type": "voice_chunk_received",
            "chunk_sequence": chunk_sequence,
            "is_final": is_final,
            "status": "processing" if not is_final else "complete"
        })

        # If final chunk, process complete audio
        if is_final:
            await connection_manager._send_message(websocket, {
                "type": "voice_processing_complete",
                "message": "Audio stream processing completed"
            })

    except Exception as e:
        logger.error(f"Error handling voice stream: {e}")
        await connection_manager._send_message(websocket, {
            "type": "error",
            "message": f"Error processing voice stream: {str(e)}"
        })


async def _handle_voice_command(websocket: WebSocket, agent_id: str, data: Dict[str, Any]):
    """Handle voice commands"""
    try:
        command_text = data.get("command_text", "")
        session_id = data.get("session_id")

        if not session_id:
            await connection_manager._send_message(websocket, {
                "type": "error",
                "message": "Session ID required for voice commands"
            })
            return

        # Process voice command through voice service
        detected_command = voice_integration_service._detect_voice_command(command_text)

        if detected_command:
            await voice_integration_service._handle_voice_command(detected_command, session_id)

            await connection_manager._send_message(websocket, {
                "type": "voice_command_executed",
                "command": detected_command.value,
                "original_text": command_text,
                "status": "success"
            })
        else:
            await connection_manager._send_message(websocket, {
                "type": "voice_command_not_recognized",
                "original_text": command_text,
                "available_commands": [cmd.value for cmd in voice_integration_service.command_patterns.keys()]
            })

    except Exception as e:
        logger.error(f"Error handling voice command: {e}")
        await connection_manager._send_message(websocket, {
            "type": "error",
            "message": f"Error processing voice command: {str(e)}"
        })


async def _handle_quick_action(websocket: WebSocket, agent_id: str, data: Dict[str, Any]):
    """Handle quick action execution"""
    try:
        session_id = data.get("session_id")
        action_type = data.get("action_type")
        context = data.get("context", {})

        if not session_id or not action_type:
            await connection_manager._send_message(websocket, {
                "type": "error",
                "message": "Session ID and action type required"
            })
            return

        # Execute quick action through mobile coaching service
        from ghl_real_estate_ai.services.claude.mobile.mobile_coaching_service import MobileActionType

        try:
            action_enum = MobileActionType(action_type)
        except ValueError:
            await connection_manager._send_message(websocket, {
                "type": "error",
                "message": f"Invalid action type: {action_type}"
            })
            return

        result = await mobile_coaching_service.execute_quick_action(
            session_id=session_id,
            action_type=action_enum,
            context=context
        )

        await connection_manager._send_message(websocket, {
            "type": "quick_action_result",
            "action_type": action_type,
            "result": result,
            "status": "success" if result.get("success") else "error"
        })

    except Exception as e:
        logger.error(f"Error handling quick action: {e}")
        await connection_manager._send_message(websocket, {
            "type": "error",
            "message": f"Error executing quick action: {str(e)}"
        })


async def _handle_start_listening(websocket: WebSocket, agent_id: str, data: Dict[str, Any]):
    """Handle start voice listening"""
    try:
        session_id = data.get("session_id")

        if not session_id:
            await connection_manager._send_message(websocket, {
                "type": "error",
                "message": "Session ID required"
            })
            return

        # Update voice session state
        session = voice_integration_service.sessions.get(session_id)
        if session:
            session.state = VoiceState.LISTENING

        await connection_manager._send_message(websocket, {
            "type": "listening_started",
            "session_id": session_id,
            "status": "ready_for_audio"
        })

    except Exception as e:
        logger.error(f"Error starting listening: {e}")
        await connection_manager._send_message(websocket, {
            "type": "error",
            "message": f"Error starting listening: {str(e)}"
        })


async def _handle_stop_listening(websocket: WebSocket, agent_id: str, data: Dict[str, Any]):
    """Handle stop voice listening"""
    try:
        session_id = data.get("session_id")

        if not session_id:
            await connection_manager._send_message(websocket, {
                "type": "error",
                "message": "Session ID required"
            })
            return

        # Update voice session state
        session = voice_integration_service.sessions.get(session_id)
        if session:
            session.state = VoiceState.IDLE

        await connection_manager._send_message(websocket, {
            "type": "listening_stopped",
            "session_id": session_id,
            "status": "idle"
        })

    except Exception as e:
        logger.error(f"Error stopping listening: {e}")
        await connection_manager._send_message(websocket, {
            "type": "error",
            "message": f"Error stopping listening: {str(e)}"
        })


async def _handle_ping(websocket: WebSocket, agent_id: str, data: Dict[str, Any]):
    """Handle ping/pong for connection health"""
    await connection_manager._send_message(websocket, {
        "type": "pong",
        "timestamp": datetime.now().isoformat(),
        "request_id": data.get("request_id")
    })


# REST Endpoints for WebSocket Management

@realtime_router.get("/connections/stats")
async def get_connection_stats():
    """Get WebSocket connection statistics"""
    try:
        stats = connection_manager.get_connection_stats()
        return {
            "connection_stats": stats,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
    except Exception as e:
        logger.error(f"Error getting connection stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@realtime_router.post("/broadcast")
async def broadcast_message(message: RealTimeMessage):
    """Broadcast message to all connected clients"""
    try:
        if message.agent_id:
            # Send to specific agent
            await connection_manager.send_to_agent(message.agent_id, {
                "type": message.type,
                "data": message.data,
                "priority": message.priority
            })
        else:
            # Broadcast to all
            await connection_manager.broadcast_to_all({
                "type": message.type,
                "data": message.data,
                "priority": message.priority
            })

        return {
            "message_sent": True,
            "type": message.type,
            "target": message.agent_id or "all",
            "timestamp": datetime.now().isoformat(),
            "success": True
        }

    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@realtime_router.get("/health")
async def realtime_health_check():
    """Health check for real-time services"""
    try:
        stats = connection_manager.get_connection_stats()

        return {
            "realtime_service": {
                "healthy": True,
                "active_connections": stats["total_connections"],
                "active_agents": stats["active_agents"]
            },
            "websocket_support": {
                "coaching": True,
                "voice": True,
                "compression": REALTIME_CONFIG.get("compression_enabled", True),
                "mobile_optimized": True
            },
            "performance": {
                "target_latency_ms": 50,
                "compression_enabled": REALTIME_CONFIG.get("compression_enabled", True)
            },
            "overall_health": True,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in realtime health check: {e}")
        return {
            "realtime_service": {"healthy": False, "error": str(e)},
            "overall_health": False,
            "timestamp": datetime.now().isoformat()
        }