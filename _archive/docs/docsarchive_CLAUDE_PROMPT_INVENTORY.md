# Claude Prompt: Inventory Intelligence Upgrade

**Copy and paste the text below into Claude:**

---

"I am working on a Real Estate AI project with a Python/Streamlit stack. We currently have a functional Inventory Manager and Match Engine using SQLite.

**Current Architecture:**
- `modules/inventory_manager.py`: Contains `InventoryManager` class for DB ops and matching.
- `inventory_dashboard.py`: Streamlit UI for data entry and match visualization.

**Goal:** 
I want to upgrade the 'Intelligence' of this system. Please provide the code for:
1. **Weighted Matching:** Instead of a simple binary match, calculate a 'Match Score' (0-100) based on:
   - Price (closer to budget is better).
   - Bedrooms (extra beds are a bonus).
   - Property Tags vs Lead Preferences.
2. **Preference Mapping:** Update the `leads` table and ingestion to include a 'Must-Haves' list (e.g., 'Pool', 'Modern Kitchen').
3. **UI Polish:** Update the Streamlit table in `inventory_dashboard.py` to show these scores with a heat-map effect or color-coded text.

Please generate the updated `modules/inventory_manager.py` methods and the relevant `inventory_dashboard.py` code blocks. I will have Gemini integrate them into my local environment."
