import asyncio
import random
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ghl_utils.config import settings

logger = get_logger(__name__)

class WhisperCoachEngine:
    """
    Real-time coaching for Jorge during voice calls.
    Decodes sentiment, identifies objections, and generates 'Whisper' cues.
    Integrated with Retell AI and Claude 3.5 Sonnet.
    """
    
    OBJECTIONS = {
        "price": [
            "Comps show $900K in this zip. Don't budge. — Data Point: Zip 78704 is +12% YoY",
            "Zillow is missing the kitchen remodel value. — Data Point: Remodels adding 15% premium locally",
            "Ask if they've toured the neighbor's property that sold for $850K."
        ],
        "timeline": [
            "They mentioned 30 days earlier. Hold them to it. — Data Point: Average close is 42 days",
            "Remind them we have a cash buyer list ready for immediate close.",
            "If they're stalling, ask if the relocation date shifted."
        ],
        "agent": [
            "Ask: 'Has your agent actually toured these comps?'",
            "Differentiate on data. Show them the Zillow-Defense variance.",
            "Remind them our AI handles 24/7 follow-up which solo agents can't do."
        ]
    }

    def __init__(self):
        self.active_calls = {}
        self.retell_api_key = settings.retell_api_key if hasattr(settings, 'retell_api_key') else None

    async def process_call_stream(self, call_id: str, lead_data: Dict[str, Any]):
        """
        In production, this would subscribe to the Retell call stream.
        """
        logger.info(f"Starting Whisper coaching stream for call {call_id}")
        
        # This would be a real loop listening to Retell WebSockets
        # async with retell.listen_to_call(call_id) as stream:
        #     for event in stream:
        #         cue = await self.generate_jorge_cue(event.transcript, lead_data)
        #         await self.push_to_dashboard(call_id, cue)
        
        pass

    async def get_live_feed(self, call_id: str) -> Dict[str, Any]:
        """
        Fetch the latest coaching state for the dashboard using real data if available.
        """
        if not self.retell_api_key or "mock" in call_id:
            return await self.get_mock_live_feed(call_id)

        from ghl_real_estate_ai.integrations.retell import RetellClient
        retell = RetellClient()
        
        try:
            call_details = await retell.get_call_details(call_id)
            transcript = call_details.get("transcript", "")
            
            # Extract the last few lines of transcript
            lines = transcript.strip().split("\n")
            recent_transcript = " ".join(lines[-3:]) if lines else "Call in progress..."
            
            # Generate real-time cue using Claude
            # In a real app, we'd cache lead_data or fetch it from GHL
            lead_data = {"call_id": call_id, "status": "active"} 
            suggestion = await self.generate_jorge_cue(recent_transcript, lead_data)
            
            # Simple sentiment logic based on transcript (placeholders)
            sentiment = 75.0
            if "not interested" in transcript.lower(): sentiment = 20.0
            elif "love it" in transcript.lower(): sentiment = 95.0
            
            return {
                "call_id": call_id,
                "sentiment": sentiment,
                "objection_type": "detected" if "price" in recent_transcript.lower() or "cost" in recent_transcript.lower() else None,
                "suggestion": suggestion,
                "transcript_peek": recent_transcript,
                "timestamp": datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            logger.error(f"Failed to fetch live feed for {call_id}: {e}")
            return await self.get_mock_live_feed(call_id)

    async def get_mock_live_feed(self, call_id: str) -> Dict[str, Any]:
        """
        Generates a mock stream of coaching data for the dashboard.
        Now uses generate_jorge_cue to provide realistic Claude-powered cues for the demo.
        """
        second = datetime.now().second
        
        # Simulated transcript progression
        mock_transcripts = [
            "Hey, I'm just curious about the value of my home.",
            "I saw the Zestimate was around 800k, but I think it's worth more.",
            "I'm relocating for a job next month so I need to move fast.",
            "The kitchen was just redone with granite countertops.",
            "Actually, I'm a bit worried about the closing costs."
        ]
        
        # Select transcript based on time to simulate a conversation
        idx = (second // 12) % len(mock_transcripts)
        current_transcript = mock_transcripts[idx]
        
        # Get real Claude cue if possible
        lead_data = {
            "lead_name": "Sarah Johnson",
            "property": "123 Maple St",
            "frs_score": 88
        }
        
        suggestion = await self.generate_jorge_cue(current_transcript, lead_data)
        
        # Sentiment oscillation
        sentiment = 65 + (20 * (second % 15) / 15)
            
        return {
            "call_id": call_id,
            "sentiment": round(sentiment, 1),
            "objection_type": "price" if "zestimate" in current_transcript.lower() or "cost" in current_transcript.lower() else None,
            "suggestion": suggestion,
            "transcript_peek": current_transcript,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }

    async def generate_jorge_cue(self, transcript_chunk: str, lead_data: Dict[str, Any]) -> str:
        """
        Uses Claude 3.5 Sonnet to analyze a transcript chunk and provide a real-time coaching cue.
        """
        from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator, ClaudeRequest, ClaudeTaskType
        
        orchestrator = get_claude_orchestrator()
        
        prompt = f"""
        Analyze this transcript chunk from a live real estate call and provide a 1-sentence coaching cue for Jorge.
        The cue should be direct, tactical, and help Jorge move the deal forward.
        
        Transcript Chunk: "{transcript_chunk}"
        Lead Data: {json.dumps(lead_data, indent=2, default=str)}
        
        Coaching Goal: Counter objections, identify motivation markers, and suggest next best action.
        Tone: Jorge-style (Direct, Data-driven, No-BS).
        """
        
        request = ClaudeRequest(
            task_type=ClaudeTaskType.CHAT_QUERY, # Use chat query for flexible reasoning
            context=lead_data,
            prompt=prompt,
            max_tokens=100,
            temperature=0.5
        )
        
        try:
            response = await orchestrator.process_request(request)
            return response.content
        except Exception as e:
            logger.error(f"Error generating coaching cue with Claude: {e}")
            # Fallback to simple pattern matching if Claude fails
            if "zillow" in transcript_chunk.lower():
                return "LEVER: Zillow variance. Mention the gap in their Zestimate."
            if "too much" in transcript_chunk.lower():
                return "PIVOT: Value justification. Reference neighborhood appreciation."
            return "Listen for the 'Why' behind their move."
