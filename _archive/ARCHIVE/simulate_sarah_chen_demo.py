
import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.getcwd())

from ghl_real_estate_ai.services.enhanced_property_matcher import EnhancedPropertyMatcher

def run_simulation():
    print("🚀 Starting Sarah Chen Simulation...")
    
    # 1. Define Sarah Chen's Profile (mimicking app.py)
    sarah_preferences = {
        "lead_id": "tech_professional_sarah",
        "name": "Sarah Chen",
        "occupation": "Software Engineer at Apple",
        "budget": 550000,
        "location": "Round Rock", 
        "workplace_location": "Apple",
        "timeline": "URGENT - 45 days",
        "bedrooms": 3,
        "bathrooms": 2,
        "must_haves": ["Home office", "High-speed internet", "Gigabit fiber"],
        "financing": "Pre-approved",
        "motivation": "Relocating for Apple expansion",
        "home_condition": "Modern / Move-in Ready",
        "property_type": "Single Family Home",
        "max_home_age": 10, # Prefers newer homes
        "max_hoa": 150,
        "min_sqft": 1800
    }
    
    # 2. Initialize Matcher
    # Ensure it picks up the correct listings file
    listings_path = str(Path("ghl_real_estate_ai/data/knowledge_base/property_listings.json"))
    matcher = EnhancedPropertyMatcher(listings_path=listings_path)
    
    # 3. Execute Match
    matches = matcher.find_enhanced_matches(sarah_preferences, limit=5)
    
    # 4. Verify Results
    found_teravista = False
    print(f"\nFound {len(matches)} matches.")
    
    for match in matches:
        prop_name = match.property.get('address', {}).get('street', 'Unknown')
        neighborhood = match.property.get('address', {}).get('neighborhood', 'Unknown')
        score = match.overall_score
        
        print(f"\n🏠 {prop_name} ({neighborhood}) - Score: {score:.1%}")
        print(f"   Reasoning: {match.reasoning.primary_strengths}")
        
        # Specific check for the target property
        if "Glenwood" in prop_name and "Teravista" in neighborhood:
            found_teravista = True
            if score > 0.9:
                print("   ✅ SUCCESS: High confidence match found!")
            else:
                print("   ⚠️ WARNING: Match found but score is lower than expected.")
                
    if found_teravista:
        print("\n✅ Simulation Passed: Sarah Chen matched with Teravista property.")
        sys.exit(0)
    else:
        print("\n❌ Simulation Failed: Teravista property not found in top matches.")
        sys.exit(1)

if __name__ == "__main__":
    run_simulation()
