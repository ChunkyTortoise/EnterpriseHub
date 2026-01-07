# scripts/inspect_ghl_fields.py
from modules.ghl_sync import GHLSyncService
import os
import json

# Setup
API_KEY = os.getenv("GHL_API_KEY", "YOUR_KEY")
LOC_ID = os.getenv("GHL_LOCATION_ID", "YOUR_LOC_ID")

if API_KEY == "YOUR_KEY" or LOC_ID == "YOUR_LOC_ID":
    print("❌ Error: Please set your GHL_API_KEY and GHL_LOCATION_ID environment variables.")
else:
    ghl = GHLSyncService(API_KEY, LOC_ID)
    fields = ghl.inspect_custom_fields()

    print("\n--- GHL CUSTOM FIELDS INSPECTOR ---")
    print(f"{ 'Field Name':<30} | {'Field ID':<40}")
    print("-" * 75)
    for f in fields:
        print(f"{f['name']:<30} | {f['id']:<40}")
    print("-" * 75)
    print("\nCopy these IDs into modules/ghl_sync.py in the self.field_map dictionary.")
