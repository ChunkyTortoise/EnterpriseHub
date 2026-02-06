import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# Vapi Configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID") # The ID of the phone number you bought in Vapi
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")       # The ID of the "Jorge Assistant" persona created in Vapi dashboard

from modules.intelligence_orchestrator import synthesize_persona

def trigger_outbound_call(contact_phone, contact_name, property_address, contact_id):
    """
    Triggers an immediate outbound call via Vapi.ai.
    Injects context (Name, Property Address, Buyer Persona) so the AI knows what to talk about.
    """
    if not VAPI_API_KEY or not VAPI_PHONE_NUMBER_ID or not VAPI_ASSISTANT_ID:
        print("❌ Vapi Config Missing in .env")
        return False

    # Get the latest persona on the fly
    buyer_persona = synthesize_persona(contact_id)

    url = "https://api.vapi.ai/call/phone"
    
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Dynamic Context Injection: This overrides the default System Prompt variables
    payload = {
        "phoneNumberId": VAPI_PHONE_NUMBER_ID,
        "customer": {
            "number": contact_phone,
            "name": contact_name
        },
        "assistantId": VAPI_ASSISTANT_ID,
        "assistantOverrides": {
            "variableValues": {
                "lead_name": contact_name,
                "property_address": property_address,
                "buyer_context": buyer_persona
            }
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            print(f"📞 Call Initiated to {contact_name} regarding {property_address}")
            return True
        else:
            print(f"❌ Call Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Vapi Network Error: {str(e)}")
        return False
