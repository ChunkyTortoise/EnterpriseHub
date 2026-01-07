import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GHL_API_KEY = os.getenv("GHL_API_KEY")
GHL_LOCATION_ID = os.getenv("GHL_LOCATION_ID")
# Standard GHL V2 API Base URL
BASE_URL = "https://services.leadconnectorhq.com" 

def fetch_custom_fields():
    """
    Fetches all custom fields for the configured Location ID
    to map human-readable names to GHL Field IDs.
    """
    if not GHL_API_KEY or not GHL_LOCATION_ID:
        print("❌ Error: GHL_API_KEY or GHL_LOCATION_ID not found in .env")
        return

    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Version": "2021-07-28", # Standard GHL V2 Header
        "Accept": "application/json"
    }

    print(f"🔍 Inspecting Custom Fields for Location: {GHL_LOCATION_ID}...")
    
    try:
        url = f"{BASE_URL}/locations/{GHL_LOCATION_ID}/customFields"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            fields = response.json().get('customFields', [])
            print(f"✅ Connection Successful. Found {len(fields)} custom fields.\n")
            
            print(f"{ 'FIELD ID':<35} | {'FIELD NAME'}")
            print("-" * 60)
            
            found_targets = []
            
            for field in fields:
                # We are looking for these specific keys based on our Logic Layer
                name = field.get('name', '').lower()
                fid = field.get('id')
                print(f"{fid:<35} | {field.get('name')}")
                
                # Check for critical fields we need for the AI Engine
                if 'budget' in name or 'interest' in name or 'tags' in name:
                    found_targets.append((field.get('name'), fid))

            print("\n" + "="*60)
            print("🚀 CRITICAL CONFIG DATA (Copy these to your .env or constants):")
            for target in found_targets:
                print(f"Found '{target[0]}': {target[1]}")
                
        else:
            print(f"❌ API Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"❌ Execution Error: {str(e)}")

if __name__ == "__main__":
    fetch_custom_fields()
