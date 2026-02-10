"""
HeyGen Service - Personalized Video Generation
Integrates with HeyGen API to create AI avatar videos presenting market reports.
"""

import logging
import os
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


class HeyGenService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("HEYGEN_API_KEY")
        self.avatar_id = os.getenv("HEYGEN_AVATAR_ID", "jorge_avatar_v1")
        self.base_url = "https://api.heygen.com/v2"
        self.http_client = httpx.AsyncClient(timeout=15.0)

        if not self.api_key:
            logger.warning("HEYGEN_API_KEY not found. Video generation will be mocked.")

    async def generate_personalized_video(
        self, lead_name: str, script_content: str, background_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Triggers a video generation task in HeyGen.
        """
        if not self.api_key:
            logger.info(f"🚀 [MOCK] Generating HeyGen Video for {lead_name}")
            return {
                "success": True,
                "video_id": "mock_video_123",
                "status": "processing",
                "preview_url": "https://www.heygen.com/demo-preview",
            }

        headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}

        payload = {
            "video_inputs": [
                {
                    "character": {"type": "avatar", "avatar_id": self.avatar_id, "avatar_style": "normal"},
                    "voice": {"type": "text", "input_text": script_content, "voice_id": "en-US-Standard-A"},
                }
            ],
            "dimension": {"width": 1080, "height": 1920},  # Vertical for mobile
        }

        if background_url:
            payload["video_inputs"][0]["background"] = {"type": "url", "url": background_url}

        try:
            url = f"{self.base_url}/video/generate"
            response = await self.http_client.post(url, headers=headers, json=payload)

            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ HeyGen Video Task Created: {data.get('data', {}).get('video_id')}")
                return {"success": True, "video_id": data.get("data", {}).get("video_id"), "status": "processing"}
            else:
                logger.error(f"❌ HeyGen API Error: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}

        except Exception as e:
            logger.error(f"❌ HeyGen Exception: {e}")
            return {"success": False, "error": str(e)}

    async def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """Check the status of a video generation task."""
        if not self.api_key:
            return {"status": "completed", "url": "https://v.heygen.com/mock_video.mp4"}

        headers = {"X-Api-Key": self.api_key}
        url = f"{self.base_url}/video/status/{video_id}"

        response = await self.http_client.get(url, headers=headers)
        return response.json()


_heygen_service = None


def get_heygen_service() -> HeyGenService:
    global _heygen_service
    if _heygen_service is None:
        _heygen_service = HeyGenService()
    return _heygen_service
