import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.inventory_manager import InventoryManager
from modules.orchestrator import RealEstateOrchestrator


def setup_data():
    """Populates DB with test data."""
    manager = InventoryManager()

    print("--- 🛠️  Setting up Data ---")

    # 1. Create a Lead
    lead = {
        "id": "demo_lead_005",
        "name": "Alice Wonderland",
        "preferences": {"budget": 2500000, "bedrooms": 3, "must_haves": ["view", "modern_kitchen", "smart_home"]},
    }
    manager.ingest_lead(lead)

    # 2. Create a Property
    prop = {
        "id": "prop_demo_99",
        "price": 2400000,
        "bedrooms": 3,
        "bathrooms": 2.5,
        "sqft": 2800,
        "address": {"street": "99 Rabbit Hole Ln", "city": "Wonderland"},
        "description": "Spectacular views of the Queen's garden. Features a modern kitchen with smart home integration and automated gates.",
        "tags": ["view", "modern_kitchen", "smart_home", "gated"],
    }
    manager.ingest_listing(prop)

    print("--- ✅ Data Setup Complete ---")
    return lead["id"]


def run_demo():
    # 1. Setup
    lead_id = setup_data()

    # 2. Initialize Orchestrator
    print("\n--- 🤖 Initializing Orchestrator ---")
    orchestrator = RealEstateOrchestrator()

    # 3. Run Workflow
    print(f"\n--- 🚀 Running Workflow for Lead: {lead_id} ---")
    result = orchestrator.run_workflow(lead_id)

    # 4. Display Output
    print("\n" + "=" * 50)
    print("   📢  ORCHESTRATION RESULT")
    print("=" * 50)

    if result["status"] == "completed":
        prop = result["selected_property"]
        print(f"\n🏡 MATCHED PROPERTY: {prop['address']}")
        print(f"💰 Price: ${prop['price']:,}")

        print("\n📝 GENERATED EMAIL DRAFT:")
        print("-" * 30)
        print(result["generated_content"])
        print("-" * 30)

        print("\n✅ LOGS:")
        for log in result["logs"]:
            print(f"  - {log}")
    else:
        print(f"❌ Workflow Failed or Stopped: {result['status']}")
        print(result)


if __name__ == "__main__":
    run_demo()
