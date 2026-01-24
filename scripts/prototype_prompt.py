"""
Prototype: Gemini Context Engine
Demonstrates the 'Boundary-Weighted' prompting strategy.
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.context_engine import ContextEngine

def main():
    engine = ContextEngine()
    
    # Simulate a task: "Refactor auth.py to use environment variables"
    task = "Refactor the authentication module to remove hardcoded credentials and use environment variables."
    
    # Identify relevant files (in a real agent, this would be done by a retrieval step)
    target_file = "ghl_real_estate_ai/api/routes/auth.py"
    
    # Read/Chunk the content
    chunks = engine.semantic_chunk(target_file)
    
    context_payload = [
        {"path": target_file, "content": chunks[0]}
    ]
    
    # Assemble the Prompt
    full_prompt = engine.assemble_prompt(task, context_payload)
    
    print("generated prompt preview (first 500 chars):\n")
    print(full_prompt[:500])
    print("\n...\n")
    print("generated prompt preview (last 500 chars):\n")
    print(full_prompt[-500:])
    
    print(f"\nTotal Prompt Length: {len(full_prompt)} chars")

if __name__ == "__main__":
    main()

