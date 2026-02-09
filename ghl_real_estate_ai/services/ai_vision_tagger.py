"""
AI Vision Tagger - Claude 3.5 Sonnet powered image analysis.

Analyzes property photos to extract high-value "Lifestyle Tags"
and architectural features.
"""

import base64
import os
from typing import List, Optional

import requests
from anthropic import Anthropic

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class VisionTagger:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("ANTHROPIC_API_KEY not found. Vision tagging will be disabled.")

    def analyze_property_image(self, image_url: str) -> List[str]:
        """
        Analyzes an image URL and returns a list of lifestyle and feature tags.
        """
        if not self.client:
            return []

        try:
            # 1. Fetch image and convert to base64
            response = requests.get(image_url)
            response.raise_for_status()
            image_data = base64.b64encode(response.content).decode("utf-8")
            media_type = response.headers.get("Content-Type", "image/jpeg")

            # 2. Call Claude 3.5 Sonnet with Vision
            # Note: Using Sonnet 3.5 as it's the current flagship for vision
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=200,
                temperature=0,
                system="You are an expert real estate appraiser and interior designer. Analyze the property image and return ONLY a comma-separated list of high-value lifestyle and architectural tags. Focus on things buyers care about (e.g., 'Modern Minimalist', 'Chef's Kitchen', 'Natural Light', 'Open Concept', 'Entertainer's Backyard'). Max 10 tags.",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {"type": "text", "text": "Analyze this property photo."},
                        ],
                    }
                ],
            )

            # 3. Parse tags
            tags_text = message.content[0].text
            tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
            logger.info(f"Vision Tags Generated: {tags}")
            return tags

        except Exception as e:
            logger.error(f"Vision Tagging Failed for {image_url}: {e}")
            return []


if __name__ == "__main__":
    # Test with a sample image
    tagger = VisionTagger()
    sample_url = (
        "https://images.unsplash.com/photo-1600585014340-be6161a56a0c?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80"
    )
    tags = tagger.analyze_property_image(sample_url)
    print(f"Sample Tags: {tags}")
