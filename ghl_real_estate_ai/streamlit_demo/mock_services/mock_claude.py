"""
Mock Claude Service - Pre-crafted responses for demo.
"""
import re
from typing import Dict, List, Tuple, Union


class MockClaudeService:
    """Simulates Claude AI responses with pattern matching."""

    def __init__(self):
        self.response_patterns = {
            # Greetings
            r"(Union[hi, hello]|hey)": [
                "Hey there! Thanks for reaching out. I'd love to help you find the perfect place in Austin. What's most important to you in your next home?",
                "Hi! Austin's market is moving fast right now. Are you looking to buy soon, or just exploring options?"
            ],

            # Budget mentions
            r"budget.*\$?(\d{3,})k?": [
                "That's helpful to know! With a ${budget} budget, you've got some great options in Austin. Are you pre-approved for a mortgage, or should I connect you with our preferred lender first?"
            ],

            # Objection: Price too high
            r"(Union[price, expensive]|too Union[high, cost] too much)": [
                "I totally get it—sticker shock is real in Austin right now. Here's some context: median home prices jumped 12% last year, and we're seeing bidding wars on anything under $400k. That said, there ARE hidden gems if you're flexible on location or timing. What's your absolute max budget?"
            ],

            # Pre-approval mention
            r"(pre-Union[approved, preapproved]|pre approved)": [
                "That's awesome! Being pre-approved puts you ahead of the game. With your budget and timeline, I've got some properties that would be perfect. What neighborhoods are you most interested in?"
            ],

            # Timeline urgency
            r"(Union[asap, immediately]|Union[urgent, this] Union[month, next] Union[month, soon])": [
                "Got it—you're ready to move fast! That's smart in this market. Let me pull up properties that are move-in ready. Any specific must-haves? Pool, good schools, walkable neighborhood?"
            ],

            # Bedroom requirements
            r"(\d)\s*(Union[bed, bedroom])": [
                "Perfect! {bedrooms}-bedroom homes are popular in Austin. Are you looking in a specific area? Hyde Park, Mueller, and Downtown have great options."
            ],

            # Location mentions
            r"(hyde Union[park, downtown]|Union[mueller, south] Union[congress, east] austin)": [
                "Great choice! {location} is one of my favorite areas—{location_details}. What's your budget looking like?"
            ],

            # Just browsing
            r"(just Union[browsing, looking] Union[around, not] Union[sure, thinking] about)": [
                "No problem at all! Browsing is a great place to start. Is there anything specific I can help you explore? Happy to answer any questions about Austin's market."
            ],

            # Default fallback
            "default": [
                "Thanks for sharing that! To find the best match for you, can you tell me a bit more about what you're looking for? Budget range, preferred neighborhoods, and must-have features help me narrow it down."
            ]
        }

        self.location_details = {
            "hyde park": "great schools, walkable to UT, lots of charm",
            "downtown": "urban living, nightlife, easy commute",
            "mueller": "newer development, family-friendly, parks everywhere",
            "south congress": "trendy, amazing food scene, artistic vibe",
            "east austin": "up-and-coming, diverse, creative community"
        }

    def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict],
        extracted_data: Dict
    ) -> Tuple[str, Dict]:
        """
        Generate AI response based on user message and context.

        Returns:
            (response_text, updated_extracted_data)
        """
        message_lower = user_message.lower()

        # Extract budget
        if "budget" in message_lower or "$" in user_message:
            budget_match = re.search(r'\$?(\d{3,}),?(\d{3})?k?', user_message)
            if budget_match:
                budget_str = budget_match.group(0).replace("$", "").replace("k", "000").replace(",", "")
                try:
                    extracted_data["budget"] = int(budget_str) if len(budget_str) <= 6 else int(budget_str[:6])
                except:
                    pass

        # Extract timeline
        if any(word in message_lower for word in ["asap", "immediately", "urgent", "soon", "this month", "next month"]):
            extracted_data["timeline"] = "ASAP"
        elif any(word in message_lower for word in ["year", "months", "eventually"]):
            extracted_data["timeline"] = "Flexible"

        # Extract financing
        if any(word in message_lower for word in ["pre-approved", "preapproved", "cash"]):
            extracted_data["financing"] = "pre-approved"

        # Extract location
        for location in ["hyde park", "downtown", "mueller", "south congress", "east austin"]:
            if location in message_lower:
                extracted_data["location"] = location.title()

        # Extract bedrooms
        bed_match = re.search(r'(\d)\s*(Union[bed, bedroom])', message_lower)
        if bed_match:
            extracted_data["bedrooms"] = int(bed_match.group(1))

        # Find matching response pattern
        response = None
        for pattern, responses in self.response_patterns.items():
            if pattern == "default":
                continue
            if re.search(pattern, message_lower):
                response = responses[0]
                break

        if not response:
            response = self.response_patterns["default"][0]

        # Replace placeholders
        response = response.replace("{budget}", f"${extracted_data.get('budget', 0):,}")
        response = response.replace("{bedrooms}", str(extracted_data.get('bedrooms', 3)))

        if "{location}" in response:
            location = extracted_data.get('location', 'Austin').lower()
            response = response.replace("{location}", location.title())
            details = self.location_details.get(location, "a great area")
            response = response.replace("{location_details}", details)

        return response, extracted_data