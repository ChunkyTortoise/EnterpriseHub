"""
Social Media Auto-Syndication
Post new listings to multiple platforms instantly

Features:
- Instagram, Facebook, LinkedIn posting
- Auto-generate platform-specific content
- Carousel posts with property highlights
- Schedule posts for optimal engagement
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class SocialMediaSyndication:
    """Service for multi-platform listing syndication"""

    def create_social_posts(self, listing: Dict[str, Any], platforms: List[str] = None) -> Dict[str, Any]:
        """
        Generate social media posts for listing

        Args:
            listing: Property listing data
            platforms: Target platforms

        Returns:
            Platform-specific posts ready to publish
        """
        platforms = platforms or ["instagram", "facebook", "linkedin"]

        posts = {}
        for platform in platforms:
            if platform == "instagram":
                posts["instagram"] = self._create_instagram_post(listing)
            elif platform == "facebook":
                posts["facebook"] = self._create_facebook_post(listing)
            elif platform == "linkedin":
                posts["linkedin"] = self._create_linkedin_post(listing)

        return {
            "listing_id": listing.get("id", "unknown"),
            "posts": posts,
            "scheduled_time": self._get_optimal_post_time(),
            "created_at": datetime.utcnow().isoformat(),
        }

    def _create_instagram_post(self, listing: Dict) -> Dict[str, Any]:
        """Create Instagram-optimized post"""
        address = listing.get("address", "Beautiful Property")
        price = listing.get("price", 0)
        beds = listing.get("bedrooms", 0)
        baths = listing.get("bathrooms", 0)

        caption = f"✨ NEW LISTING ALERT! ✨\n\n"
        caption += f"📍 {address}\n"
        caption += f"💰 ${price:,}\n"
        caption += f"🛏️ {beds} bed | 🛁 {baths} bath\n\n"
        caption += f"DM for private showing! 🏡\n\n"
        caption += "#realestate #newlisting #dreamhome #househunting #realtor #property #forsale"

        return {
            "platform": "instagram",
            "type": "carousel",
            "caption": caption,
            "images": listing.get("photos", [])[:10],
            "hashtags": ["realestate", "newlisting", "dreamhome", "househunting"],
            "optimal_time": "6:00 PM",
        }

    def _create_facebook_post(self, listing: Dict) -> Dict[str, Any]:
        """Create Facebook-optimized post"""
        address = listing.get("address", "Beautiful Property")
        price = listing.get("price", 0)
        beds = listing.get("bedrooms", 0)
        baths = listing.get("bathrooms", 0)
        sqft = listing.get("sqft", 0)

        caption = f"🏡 JUST LISTED!\n\n"
        caption += f"{address}\n"
        caption += f"${price:,} | {beds} BR | {baths} BA | {sqft:,} sqft\n\n"
        caption += f"Beautiful home in sought-after neighborhood! "
        caption += f"Schedule your private showing today.\n\n"
        caption += f"📞 Call or message for details!"

        return {
            "platform": "facebook",
            "type": "photo_album",
            "text": caption,
            "images": listing.get("photos", []),
            "call_to_action": "Learn More",
            "optimal_time": "1:00 PM",
        }

    def _create_linkedin_post(self, listing: Dict) -> Dict[str, Any]:
        """Create LinkedIn-optimized post"""
        address = listing.get("address", "Property")
        price = listing.get("price", 0)

        caption = f"🏠 New Investment Opportunity\n\n"
        caption += f"I'm pleased to present {address}.\n\n"
        caption += f"Key Details:\n"
        caption += f"• Price: ${price:,}\n"
        caption += f"• Status: Active\n"
        caption += f"• Market: Strong appreciation area\n\n"
        caption += f"Excellent opportunity for investors or owner-occupants.\n\n"
        caption += f"Contact me for detailed information and showing schedule."

        return {
            "platform": "linkedin",
            "type": "article",
            "text": caption,
            "images": [listing.get("photos", [])[0]] if listing.get("photos") else [],
            "optimal_time": "8:00 AM",
        }

    def _get_optimal_post_time(self) -> str:
        """Get optimal posting time"""
        return (datetime.utcnow() + timedelta(hours=2)).strftime("%Y-%m-%d %I:%M %p")


def demo_social_syndication():
    service = SocialMediaSyndication()

    print("📱 Social Media Auto-Syndication Demo\n")

    listing = {
        "id": "L123",
        "address": "123 Oak Street",
        "price": 525000,
        "bedrooms": 4,
        "bathrooms": 2.5,
        "sqft": 2400,
        "photos": ["photo1.jpg", "photo2.jpg", "photo3.jpg"],
    }

    posts = service.create_social_posts(listing)

    print("SOCIAL MEDIA POSTS GENERATED\n")

    for platform, post in posts["posts"].items():
        print(f"{'=' * 70}")
        print(f"{platform.upper()}")
        print(f"{'=' * 70}")
        print(post.get("caption") or post.get("text"))
        print(f"\nOptimal Time: {post['optimal_time']}")
        print(f"Type: {post['type']}\n")

    return service


if __name__ == "__main__":
    demo_social_syndication()
