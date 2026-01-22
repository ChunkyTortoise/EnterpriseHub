"""
Script to seed the component documentation registry.
"""
import sys
import os
from pathlib import Path

sys.path.append(os.getcwd())

from ghl_real_estate_ai.agent_system.skills.base import registry

def seed_registry():
    """Reads docs and registers them."""
    print("🌱 Seeding Component Documentation Registry...")
    
    doc_dir = Path("docs/component_docs")
    if not doc_dir.exists():
        print(f"❌ Documentation directory not found: {doc_dir}")
        return
        
    for doc_file in doc_dir.glob("*.md"):
        with open(doc_file, "r") as f:
            content = f.read()
            name = doc_file.stem
            
            print(f"  -> Registering '{name}'...")
            registry.register_document(
                name=name,
                content=content,
                tags=["component", "frontend", "react", "tremor"],
                location_id="frontend" # Use a specific location for frontend docs
            )
            
    print("✅ Seeding complete.")
    
def verify_seeding():
    """Queries the registry to verify docs were added."""
    print("\n🔬 Verifying Component Registry...")
    
    query = "How do I make a card with a blue top border?"
    print(f"Query: \"{query}\"")
    
    results = registry.find_relevant_docs(query, location_id="frontend")
    
    if not results:
        print("❌ Verification FAILED: No documents found.")
        return
        
    print("\nTop search results:")
    for result in results:
        print(f"- ID: {result['id']} (Distance: {result['distance']:.4f})")
    
    # Check if the expected doc is in the top results
    if any(result['id'] == "TremorCard" for result in results):
        print("\n✅ Verification SUCCESS: 'TremorCard' found in search results.")
    else:
        print("\n❌ Verification FAILED: 'TremorCard' not found in top search results.")

if __name__ == "__main__":
    seed_registry()
    verify_seeding()
