"""
AI Property Listing Writer
Generate professional, SEO-optimized property descriptions in seconds

This service uses AI to create compelling listing descriptions that:
- Highlight key property features
- Tell an emotional story
- Are optimized for search engines
- Match the target buyer persona
"""

import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ListingStyle(Enum):
    """Listing description styles"""

    PROFESSIONAL = "professional"  # Standard, factual
    LUXURY = "luxury"  # High-end, aspirational
    FIRST_TIME_BUYER = "first_time_buyer"  # Warm, encouraging
    INVESTMENT = "investment"  # ROI-focused
    FAMILY = "family"  # Lifestyle, community-focused


class PropertyType(Enum):
    """Property types"""

    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    LAND = "land"
    COMMERCIAL = "commercial"


class AIListingWriterService:
    """Service for generating AI-powered property listings"""

    def __init__(self):
        self.style_templates = self._load_style_templates()

    def generate_listing(
        self,
        property_data: Dict[str, Any],
        style: str = ListingStyle.PROFESSIONAL.value,
        include_seo: bool = True,
        max_length: int = 500,
    ) -> Dict[str, Any]:
        """
        Generate a professional property listing description

        Args:
            property_data: Property details (address, beds, baths, sqft, price, features)
            style: Writing style (professional, luxury, first_time_buyer, investment, family)
            include_seo: Include SEO-optimized keywords
            max_length: Maximum character length

        Returns:
            Dictionary with title, description, highlights, and SEO keywords
        """
        # Extract property details
        address = property_data.get("address", "Beautiful Property")
        bedrooms = property_data.get("bedrooms", 0)
        bathrooms = property_data.get("bathrooms", 0)
        sqft = property_data.get("sqft", 0)
        price = property_data.get("price", 0)
        property_type = property_data.get("type", PropertyType.SINGLE_FAMILY.value)
        features = property_data.get("features", [])
        neighborhood = property_data.get("neighborhood", "")
        year_built = property_data.get("year_built", None)
        lot_size = property_data.get("lot_size", None)

        # Generate based on style
        if style == ListingStyle.LUXURY.value:
            listing = self._generate_luxury_listing(address, bedrooms, bathrooms, sqft, price, features, neighborhood)
        elif style == ListingStyle.FIRST_TIME_BUYER.value:
            listing = self._generate_first_time_buyer_listing(
                address, bedrooms, bathrooms, sqft, price, features, neighborhood
            )
        elif style == ListingStyle.INVESTMENT.value:
            listing = self._generate_investment_listing(
                address, bedrooms, bathrooms, sqft, price, features, property_type
            )
        elif style == ListingStyle.FAMILY.value:
            listing = self._generate_family_listing(address, bedrooms, bathrooms, sqft, price, features, neighborhood)
        else:  # Professional
            listing = self._generate_professional_listing(
                address, bedrooms, bathrooms, sqft, price, features, property_type
            )

        # Add SEO keywords if requested
        if include_seo:
            listing["seo_keywords"] = self._generate_seo_keywords(property_data, style)

        # Add metadata
        listing["generated_at"] = datetime.utcnow().isoformat()
        listing["style"] = style
        listing["word_count"] = len(listing["description"].split())
        listing["char_count"] = len(listing["description"])

        # Truncate if too long
        if len(listing["description"]) > max_length:
            listing["description"] = listing["description"][: max_length - 3] + "..."

        return listing

    def _generate_professional_listing(
        self,
        address: str,
        bedrooms: int,
        bathrooms: float,
        sqft: int,
        price: int,
        features: List[str],
        property_type: str,
    ) -> Dict[str, Any]:
        """Generate professional, factual listing"""

        title = f"{bedrooms} Bed, {bathrooms} Bath {property_type.replace('_', ' ').title()}"

        description = f"Welcome to {address}. "

        if sqft:
            description += f"This {sqft:,} sq ft {property_type.replace('_', ' ')} "
        else:
            description += f"This {property_type.replace('_', ' ')} "

        description += f"offers {bedrooms} bedrooms and {bathrooms} bathrooms. "

        if features:
            description += f"\n\nKey Features:\n"
            for feature in features[:5]:
                description += f"• {feature}\n"

        description += f"\n\nPriced at ${price:,}, this property offers excellent value. "
        description += "Schedule your private showing today."

        highlights = [
            f"{bedrooms} Bedrooms",
            f"{bathrooms} Bathrooms",
            f"{sqft:,} Sq Ft" if sqft else "Spacious Layout",
            f"${price:,}",
        ]
        highlights.extend(features[:3])

        return {
            "title": title,
            "description": description.strip(),
            "highlights": highlights,
            "call_to_action": "Schedule Your Showing Today",
        }

    def _generate_luxury_listing(
        self,
        address: str,
        bedrooms: int,
        bathrooms: float,
        sqft: int,
        price: int,
        features: List[str],
        neighborhood: str,
    ) -> Dict[str, Any]:
        """Generate luxury, aspirational listing"""

        title = f"Exquisite {bedrooms}-Bedroom Estate"

        description = f"Discover unparalleled luxury at {address}. "

        if neighborhood:
            description += f"Nestled in the prestigious {neighborhood} neighborhood, "

        description += f"this exceptional {sqft:,} sq ft masterpiece "
        description += f"redefines elegant living. "

        description += f"\n\nFeaturing {bedrooms} generously-appointed bedrooms and "
        description += f"{bathrooms} spa-inspired bathrooms, every detail has been "
        description += "meticulously curated to create an atmosphere of refined sophistication. "

        if features:
            luxury_features = [f.lower() for f in features]
            if any("gourmet" in f or "kitchen" in f for f in luxury_features):
                description += "\n\nThe chef's kitchen is a culinary masterpiece. "
            if any("master" in f or "suite" in f for f in luxury_features):
                description += "The primary suite offers a private sanctuary. "
            if any("view" in f or "outdoor" in f for f in luxury_features):
                description += "Breathtaking views captivate from every vantage point. "

        description += f"\n\nPresented at ${price:,}. An extraordinary opportunity for the discerning buyer."

        highlights = [
            f"{bedrooms} Bedroom Suites",
            f"{bathrooms} Luxury Baths",
            f"{sqft:,} Sq Ft of Elegance",
            "Premium Finishes",
            "Exclusive Location",
        ]

        return {
            "title": title,
            "description": description.strip(),
            "highlights": highlights,
            "call_to_action": "Schedule Your Private Tour",
        }

    def _generate_first_time_buyer_listing(
        self,
        address: str,
        bedrooms: int,
        bathrooms: float,
        sqft: int,
        price: int,
        features: List[str],
        neighborhood: str,
    ) -> Dict[str, Any]:
        """Generate warm, encouraging listing for first-time buyers"""

        title = f"Perfect Starter Home - {bedrooms} Bed/{bathrooms} Bath"

        description = f"Welcome home! This charming {bedrooms}-bedroom property at {address} "
        description += "is perfect for first-time buyers. "

        if neighborhood:
            description += f"\n\nLocated in the friendly {neighborhood} community, "
            description += "you'll love the neighborhood feel and convenience. "

        description += f"\n\nInside, you'll find {sqft:,} sq ft of comfortable living space "
        description += f"with {bedrooms} cozy bedrooms and {bathrooms} updated bathrooms. "

        if features:
            description += "\n\nWhat makes this home special:\n"
            for feature in features[:4]:
                description += f"✓ {feature}\n"

        description += f"\n\nPriced at ${price:,}, this home offers incredible value. "
        description += "Start building equity today instead of paying rent!"

        highlights = [
            "Perfect for First-Time Buyers",
            f"{bedrooms} Bedrooms",
            f"{bathrooms} Bathrooms",
            "Move-In Ready",
            "Great Neighborhood",
        ]

        return {
            "title": title,
            "description": description.strip(),
            "highlights": highlights,
            "call_to_action": "Let's Make Your Dream a Reality!",
        }

    def _generate_investment_listing(
        self,
        address: str,
        bedrooms: int,
        bathrooms: float,
        sqft: int,
        price: int,
        features: List[str],
        property_type: str,
    ) -> Dict[str, Any]:
        """Generate ROI-focused listing for investors"""

        title = f"Investment Opportunity - {bedrooms}BR {property_type.replace('_', ' ').title()}"

        # Calculate basic metrics
        price_per_sqft = price / sqft if sqft > 0 else 0
        estimated_rent = bedrooms * 1000 + bathrooms * 200  # Rough estimate

        description = f"Solid investment opportunity at {address}. "
        description += f"This {bedrooms}-bedroom, {bathrooms}-bathroom {property_type.replace('_', ' ')} "
        description += f"is priced to sell at ${price:,}. "

        description += f"\n\nKey Investment Metrics:\n"
        description += f"• {sqft:,} sq ft (${price_per_sqft:.2f}/sq ft)\n" if sqft else ""
        description += f"• Estimated rental income: ${estimated_rent:,}/month\n"
        description += f"• {bedrooms} bedrooms attract stable tenants\n"

        if features:
            description += f"\n\nValue-Add Features:\n"
            for feature in features[:4]:
                description += f"• {feature}\n"

        description += "\n\nStrong rental demand in the area. Low maintenance. Excellent cash flow potential."

        highlights = [
            f"${price:,} Investment",
            f"Est. ${estimated_rent:,}/mo Rent",
            f"{bedrooms}BR/{bathrooms}BA",
            "Strong Rental Market",
            "Value-Add Opportunity",
        ]

        return {
            "title": title,
            "description": description.strip(),
            "highlights": highlights,
            "call_to_action": "Analyze the Numbers Today",
        }

    def _generate_family_listing(
        self,
        address: str,
        bedrooms: int,
        bathrooms: float,
        sqft: int,
        price: int,
        features: List[str],
        neighborhood: str,
    ) -> Dict[str, Any]:
        """Generate family-focused listing emphasizing lifestyle"""

        title = f"Perfect Family Home in {neighborhood or 'Great Neighborhood'}"

        description = f"Your family will love calling {address} home! "

        description += f"This {bedrooms}-bedroom, {bathrooms}-bathroom home offers "
        description += f"{sqft:,} sq ft of family-friendly living space. "

        if neighborhood:
            description += f"\n\nThe {neighborhood} neighborhood is perfect for families - "
            description += "great schools nearby, parks, and a friendly community atmosphere. "

        description += f"\n\nInside, you'll find plenty of room for everyone:\n"
        description += f"• {bedrooms} bedrooms for the whole family\n"
        description += f"• {bathrooms} bathrooms (no more morning battles!)\n"

        # Highlight family-friendly features
        family_keywords = ["yard", "garage", "basement", "playroom", "school", "park"]
        family_features = [f for f in features if any(k in f.lower() for k in family_keywords)]

        if family_features:
            description += f"\n\nFamily-Friendly Features:\n"
            for feature in family_features[:4]:
                description += f"• {feature}\n"

        description += f"\n\nPriced at ${price:,}. Make memories here!"

        highlights = [
            "Perfect for Families",
            f"{bedrooms} Spacious Bedrooms",
            "Great School District",
            "Safe Neighborhood",
            "Move-In Ready",
        ]

        return {
            "title": title,
            "description": description.strip(),
            "highlights": highlights,
            "call_to_action": "Schedule a Family Tour Today!",
        }

    def _generate_seo_keywords(self, property_data: Dict[str, Any], style: str) -> List[str]:
        """Generate SEO-optimized keywords"""

        keywords = []

        # Location keywords
        if property_data.get("address"):
            keywords.append(property_data["address"])
        if property_data.get("neighborhood"):
            keywords.append(f"{property_data['neighborhood']} homes")
            keywords.append(f"{property_data['neighborhood']} real estate")
        if property_data.get("city"):
            keywords.append(f"{property_data['city']} homes for sale")

        # Property type keywords
        property_type = property_data.get("type", "home")
        keywords.extend(
            [
                f"{property_type.replace('_', ' ')} for sale",
                f"{property_data.get('bedrooms', 3)} bedroom home",
                f"{property_data.get('bedrooms', 3)} bed {property_data.get('bathrooms', 2)} bath",
            ]
        )

        # Style-specific keywords
        if style == ListingStyle.LUXURY.value:
            keywords.extend(["luxury homes", "estate property", "high-end real estate"])
        elif style == ListingStyle.FIRST_TIME_BUYER.value:
            keywords.extend(["starter home", "affordable housing", "first home"])
        elif style == ListingStyle.INVESTMENT.value:
            keywords.extend(["investment property", "rental property", "cash flow"])
        elif style == ListingStyle.FAMILY.value:
            keywords.extend(["family home", "school district", "family neighborhood"])

        return keywords[:15]  # Return top 15 keywords

    def _load_style_templates(self) -> Dict[str, Any]:
        """Load style-specific templates"""
        return {
            "professional": {
                "opening": ["Welcome to", "Presenting", "Discover"],
                "closing": [
                    "Schedule your showing today",
                    "Don't miss this opportunity",
                ],
            },
            "luxury": {
                "opening": ["Discover", "Experience", "Indulge in"],
                "closing": [
                    "An extraordinary opportunity",
                    "Schedule your private tour",
                ],
            },
            "first_time_buyer": {
                "opening": [
                    "Welcome home",
                    "Your dream starts here",
                    "Perfect for you",
                ],
                "closing": [
                    "Let's make your dream a reality",
                    "Start building equity today",
                ],
            },
        }

    def generate_multiple_versions(self, property_data: Dict[str, Any], styles: List[str] = None) -> Dict[str, Any]:
        """
        Generate multiple listing versions for A/B testing

        Args:
            property_data: Property details
            styles: List of styles to generate (defaults to all)

        Returns:
            Dictionary of style -> listing
        """
        if styles is None:
            styles = [s.value for s in ListingStyle]

        versions = {}
        for style in styles:
            versions[style] = self.generate_listing(property_data, style=style)

        return versions


# Demo/Test function
def demo_listing_writer():
    """Demonstrate AI listing writer"""
    service = AIListingWriterService()

    print("🤖 AI Property Listing Writer Demo\n")

    # Sample property
    property_data = {
        "address": "123 Maple Street",
        "bedrooms": 4,
        "bathrooms": 2.5,
        "sqft": 2400,
        "price": 525000,
        "type": "single_family",
        "neighborhood": "Riverside",
        "city": "Springfield",
        "features": [
            "Updated gourmet kitchen",
            "Hardwood floors throughout",
            "Large backyard with deck",
            "Master suite with walk-in closet",
            "Two-car garage",
            "Near top-rated schools",
        ],
    }

    # Generate different styles
    styles = ["professional", "luxury", "first_time_buyer", "family"]

    for style in styles:
        print(f"\n{'=' * 70}")
        print(f"Style: {style.upper()}")
        print("=" * 70)

        listing = service.generate_listing(property_data, style=style)

        print(f"\nTitle: {listing['title']}")
        print(f"\nDescription:\n{listing['description']}")
        print(f"\nHighlights:")
        for highlight in listing["highlights"]:
            print(f"  • {highlight}")
        print(f"\nCTA: {listing['call_to_action']}")
        print(f"\nStats: {listing['word_count']} words, {listing['char_count']} characters")

        if "seo_keywords" in listing:
            print(f"\nSEO Keywords: {', '.join(listing['seo_keywords'][:5])}...")

    return service


if __name__ == "__main__":
    demo_listing_writer()
