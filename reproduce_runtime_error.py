import asyncio
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.services.claude_assistant_optimized import ClaudeAssistantOptimized

def test_init():
    print("Attempting to initialize ClaudeAssistantOptimized without an event loop...")
    try:
        assistant = ClaudeAssistantOptimized()
        print("Success!")
    except RuntimeError as e:
        print(f"Caught expected RuntimeError: {e}")
    except Exception as e:
        print(f"Caught unexpected Exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_init()