"""
Demo State Manager
Shared state between Admin Dashboard and Buyer Portal for the live demo.
"""

import json
from pathlib import Path


class DemoStateManager:
    def __init__(self):
        self.state_file = Path(__file__).parent.parent / "data" / "demo_state.json"
        self._ensure_state_file()

    def _ensure_state_file(self):
        if not self.state_file.exists():
            initial_state = {
                "custom_listings": [],
                "user_actions": [],  # saved, liked, etc.
                "simulation_active": False,
            }
            self.save_state(initial_state)

    def load_state(self):
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
            logger.warning(f"Could not load demo state: {e}. Returning default state.")
            return {"custom_listings": [], "user_actions": []}

    def save_state(self, state):
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    def add_listing(self, listing):
        state = self.load_state()
        state["custom_listings"].append(listing)
        self.save_state(state)
        return True

    def get_all_listings(self):
        state = self.load_state()
        # Merge with file-based listings if needed, or just return custom ones for the demo "wow" factor
        return state.get("custom_listings", [])

    def clear_listings(self):
        state = self.load_state()
        state["custom_listings"] = []
        self.save_state(state)
