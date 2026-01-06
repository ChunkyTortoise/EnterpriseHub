import requests
import json
import os

# Credentials from chat history
AGENCY_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IjN4dDRxYXlBaDM1QmxETGFVdjdQIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUzODYxMTU4OTk3LCJzdWIiOiJPcjRJbVNVeFVhclBKUXlhd0E1VyJ9._2BeC7R5a1X3R05N40iDcxLhy8Kz8L1vBydudDLL_As"
# The provided key looks like a Location/User JWT, but let's try it as a Bearer token.

def discover_locations():
    print("🔍 Attempting to discover GHL Locations...")
    
    # Try V1 endpoint first (classic API key)
    headers_v1 = {
        "Authorization": f"Bearer {AGENCY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Try V2 locations endpoint (Agency Level)
    # Usually requires OAuth, but sometimes API keys work for direct access
    url = "https://services.leadconnectorhq.com/locations/search"
    
    try:
        response = requests.get(
            "https://rest.gohighlevel.com/v1/locations/", 
            headers=headers_v1
        )
        
        if response.status_code == 200:
            data = response.json()
            locations = data.get('locations', [])
            print(f"✅ Success! Found {len(locations)} locations via V1 API.")
            for loc in locations:
                print(f" - {loc.get('name')}: {loc.get('id')}")
            return
        else:
             print(f"⚠️ V1 API Failed ({response.status_code}): {response.text}")

    except Exception as e:
        print(f"❌ Error during discovery: {e}")

if __name__ == "__main__":
    discover_locations()
