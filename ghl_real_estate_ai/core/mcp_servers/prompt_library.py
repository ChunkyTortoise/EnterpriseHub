"""
FastMCP Server: Prompt Library Manager for Gemini
Versions, tests, and retrieves prompts and personas.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Gemini Prompt Library")

PROMPTS_DIR = "ghl_real_estate_ai/prompts"


@mcp.tool()
async def save_prompt(name: str, content: str, persona: str, tags: List[str]) -> Dict:
    """
    Store a prompt + persona in versioned library.
    """
    os.makedirs(PROMPTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.json"
    filepath = os.path.join(PROMPTS_DIR, filename)

    entry = {
        "name": name,
        "content": content,
        "persona": persona,
        "tags": tags,
        "version": timestamp,
        "created_at": datetime.now().isoformat(),
    }

    with open(filepath, "w") as f:
        json.dump(entry, f, indent=2)

    return {"stored": True, "path": filepath, "version": timestamp}


@mcp.tool()
async def list_prompts(tag: Optional[str] = None) -> List[Dict]:
    """
    Retrieve prompts filtered by tag.
    """
    if not os.path.exists(PROMPTS_DIR):
        return []

    prompts = []
    for filename in os.listdir(PROMPTS_DIR):
        if filename.endswith(".json"):
            with open(os.path.join(PROMPTS_DIR, filename), "r") as f:
                try:
                    data = json.load(f)
                    if not tag or tag in data.get("tags", []):
                        prompts.append(data)
                except Exception:
                    continue

    # Return latest versions first
    return sorted(prompts, key=lambda x: x["created_at"], reverse=True)


@mcp.tool()
async def get_latest_prompt(name: str) -> Optional[Dict]:
    """
    Retrieve the latest version of a prompt by name.
    """
    all_prompts = await list_prompts()
    for p in all_prompts:
        if p["name"] == name:
            return p
    return None


if __name__ == "__main__":
    mcp.run()
