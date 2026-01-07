import os
import base64
import requests
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Initialize Anthropic Client
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

def analyze_property_image(image_url):
    """
    Sends a property image URL to Claude 3.5 Sonnet for architectural analysis.
    Returns a JSON object with tags, vibe, and estimated condition.
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Anthropic API Key missing")
        return None

    prompt = """
    Analyze this real estate image. Return ONLY a JSON object with these keys:
    {
      "architectural_style": "e.g., Mid-Century, Spanish, Ranch, Modern",
      "condition": "e.g., Fixer-Upper, Turn-Key, Dated, Luxury",
      "key_features": ["list", "of", "visible", "features", "e.g., Pool, ADU, High Ceilings"],
      "vibe_tags": ["list", "of", "emotional", "keywords", "e.g., Cozy, Airy, Dark, Minimalist"]
    }
    Do not include markdown formatting or explanation. Just the JSON.
    """

    try:
        # Download image and encode to base64 for reliable API delivery
        response = requests.get(image_url)
        response.raise_for_status()
        image_data = base64.b64encode(response.content).decode("utf-8")
        media_type = response.headers.get("Content-Type", "image/jpeg")

        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        )
        return message.content[0].text
    except Exception as e:
        print(f"❌ Vision Analysis Failed: {e}")
        return None
