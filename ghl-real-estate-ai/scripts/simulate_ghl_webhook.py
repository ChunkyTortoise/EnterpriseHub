"""
GHL Webhook Simulation Script.

Simulates a GoHighLevel webhook payload for testing the AI Assistant locally or in production.
Supports 'Hit List' seller simulation and generic buyer simulation.

Usage:
    # Test local server: python scripts/simulate_ghl_webhook.py
    # Test production server: python scripts/simulate_ghl_webhook.py --url https://your-app.railway.app/api/ghl/webhook
"""
import requests
import json
import uuid
import sys
import argparse
from datetime import datetime

# Default local server URL
DEFAULT_URL = "http://localhost:8000/api/ghl/webhook"

def simulate_hit_list_seller(url, message="I'm interested in selling my house."):
    """Simulates a seller in the 'Hit List' disposition."""
    print(f"\n🚀 Simulating 'Hit List' Seller Webhook to {url}...")
    
    payload = {
        "type": "InboundMessage",
        "contactId": f"test_contact_{uuid.uuid4().hex[:8]}",
        "locationId": "loc_closer_control_123",
        "message": {
            "type": "SMS",
            "body": message,
            "direction": "inbound",
            "timestamp": datetime.utcnow().isoformat()
        },
        "contact": {
            "firstName": "John",
            "lastName": "Seller",
            "phone": "+15125559999",
            "email": "john.seller@example.com",
            "tags": ["Hit List", "Need to Qualify"],
            "customFields": {
                "Primary Contact Type": "Seller",
                "disposition": "Hit List"
            }
        }
    }
    
    send_payload(url, payload)

def simulate_inactive_contact(url):
    """Simulates a contact that SHOULD NOT trigger the bot."""
    print(f"\n🛑 Simulating Inactive Contact (No Hit List tag) to {url}...")
    
    payload = {
        "type": "InboundMessage",
        "contactId": "inactive_test_123",
        "locationId": "loc_123",
        "message": {
            "type": "SMS",
            "body": "Just checking in.",
            "direction": "inbound"
        },
        "contact": {
            "firstName": "Jane",
            "lastName": "Doe",
            "tags": ["Untouched"],
            "customFields": {}
        }
    }
    
    send_payload(url, payload)

def send_payload(url, payload):
    """Sends the JSON payload to the specified webhook endpoint."""
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        try:
            resp_json = response.json()
            print("Response Body:")
            print(json.dumps(resp_json, indent=2))
            
            if response.status_code == 200 and resp_json.get("success"):
                print("✅ SUCCESS: Bot responded correctly.")
            elif response.status_code == 200 and not resp_json.get("success"):
                print(f"ℹ️ INFO: Bot correctly ignored the message: {resp_json.get('message')}")
            else:
                print("❌ ERROR: Unexpected response content.")
        except json.JSONDecodeError:
            print("❌ ERROR: Response was not valid JSON.")
            print(f"Raw response: {response.text[:500]}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Could not connect to {url}. Is the server running?")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real Estate AI Webhook Simulator")
    parser.add_argument("--url", type=str, default=DEFAULT_URL, help=f"Webhook URL (default: {DEFAULT_URL})")
    parser.add_argument("--type", type=str, choices=["seller", "inactive", "both"], default="both", help="Simulation type")
    parser.add_argument("--message", type=str, default="I'm interested in selling my house.", help="Custom message for seller")
    
    args = parser.parse_args()
    
    print("Real Estate AI Webhook Simulator")
    print("-" * 30)
    
    if args.type == "seller":
        simulate_hit_list_seller(args.url, args.message)
    elif args.type == "inactive":
        simulate_inactive_contact(args.url)
    else:
        simulate_hit_list_seller(args.url, args.message)
        simulate_inactive_contact(args.url)
