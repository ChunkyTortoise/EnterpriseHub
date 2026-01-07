import os
import sys
import json
import random
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.inventory_manager import InventoryManager

def run_stress_test():
    print("🚀 Initializing Stress & Integrity Test...")
    
    # 1. Setup Manager (uses local real_estate_engine.db)
    manager = InventoryManager("stress_test.db")
    
    # 2. Generate Bulk Properties (50 Listings)
    print("\n🏠 Ingesting 50 properties with mixed features...")
    property_types = [
        "Modern hillside estate with a luxury pool and chef's kitchen.",
        "Cozy suburban home with a large backyard and updated appliances.",
        "Urban loft featuring industrial design and granite countertops.",
        "Fixer-upper with massive potential and a huge lot size.",
        "Beachfront property with infinity pool and open floor plan."
    ]
    
    start_time = time.time()
    for i in range(50):
        prop = {
            "id": f"prop_{i:03d}",
            "price": random.randint(400000, 2500000),
            "bedrooms": random.randint(2, 6),
            "bathrooms": random.randint(2, 5),
            "sqft": random.randint(1200, 5000),
            "address": {
                "street": f"{random.randint(100, 9999)} Oak Street",
                "city": "Rancho Cucamonga"
            },
            "description": random.choice(property_types)
        }
        manager.ingest_listing(prop)
    
    ingest_duration = time.time() - start_time
    print(f"✅ Ingested 50 properties in {ingest_duration:.2f} seconds.")

    # 3. Generate Leads with Specific Profiles
    print("\n👤 Creating 5 Lead Personas...")
    leads = [
        {
            "id": "lead_luxury",
            "name": "Luxury Larry",
            "preferences": {"budget": 2000000, "bedrooms": 5, "must_haves": ["has_pool", "modern_kitchen"]}
        },
        {
            "id": "lead_budget",
            "name": "Budget Bob",
            "preferences": {"budget": 600000, "bedrooms": 3, "must_haves": []}
        },
        {
            "id": "lead_investor",
            "name": "Investor Ivy",
            "preferences": {"budget": 800000, "bedrooms": 2, "must_haves": ["large_lot"]}
        }
    ]
    
    for lead in leads:
        manager.ingest_lead(lead)

    # 4. Verify Matching Integrity
    print("\n🎯 Verifying Matching Integrity...")
    for lead in leads:
        deck = manager.get_smart_deck(lead['id'])
        print(f"\nResults for {lead['name']} (Budget: ${lead['preferences']['budget']:,}):")
        if not deck:
            print("  ❌ No matches found.")
            continue
            
        top_matches = deck[:3]
        for m in top_matches:
            print(f"  ✨ {m['address']}: ${m['price']:,} | Score: {m['match_score']}% ")
            
            # Integrity Checks
            if m['price'] > lead['preferences']['budget'] * 1.1:
                print(f"    ⚠️ CRITICAL ERROR: Property ${m['price']} exceeds budget wiggle room for ${lead['preferences']['budget']}")
            
            if lead['id'] == "lead_luxury" and "has_pool" not in m['tags']:
                 print(f"    ⚠️ WARNING: Luxury lead prefers pool, but top match tags are: {m['tags']}")

    print("\n🏁 Stress Test Complete. Database saved to stress_test.db")

if __name__ == "__main__":
    run_stress_test()
