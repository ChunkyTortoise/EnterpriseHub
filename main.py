import os
from typing import Dict, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from modules.appointment_manager import AppointmentManager
from modules.ghl_sync import GHLSyncService
from modules.inventory_manager import InventoryManager
from modules.voice_trigger import trigger_outbound_call
from pydantic import BaseModel

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="GHL Real Estate AI API")

# Enable CORS for React frontend
# In production, you should restrict origins to your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
# Note: These will use default DB paths as defined in their respective modules
inventory = InventoryManager()
ghl = GHLSyncService()
appointment = AppointmentManager()


# --- Models ---
class Interaction(BaseModel):
    contact_id: str
    property_id: str
    action: str  # 'like' or 'pass'
    location_id: Optional[str] = None
    time_on_card: Optional[float] = None
    feedback: Optional[Dict] = None


class VapiToolCall(BaseModel):
    message: Dict  # Vapi sends a 'message' object containing 'toolCalls'


# --- Endpoints ---


@app.get("/")
async def root():
    return {"message": "GHL Real Estate AI API is running"}


@app.post("/vapi/tools/check-availability")
async def vapi_check_availability(payload: Dict):
    """
    Vapi Tool: Checks Jorge's calendar for open slots.
    """
    # Vapi sends the tool call info in different formats depending on config
    # We'll handle the standard function calling structure
    tool_call = payload.get("toolCall", {})
    args = tool_call.get("function", {}).get("arguments", {})

    date_query = args.get("date")
    result = appointment.check_calendar_availability(date_query)

    return {"results": [{"toolCallId": tool_call.get("id"), "result": json.dumps(result)}]}


@app.post("/vapi/tools/book-tour")
async def vapi_book_tour(payload: Dict):
    """
    Vapi Tool: Finalizes the appointment in GHL.
    """
    tool_call = payload.get("toolCall", {})
    args = tool_call.get("function", {}).get("arguments", {})

    # We can retrieve contact_id from Vapi's call metadata if injected
    # or the AI can pass it if we shared it in the system prompt
    contact_id = args.get("contact_id")
    slot_time = args.get("slot_time")
    property_addr = args.get("property_address", "Private Viewing")

    # If contact_id is missing, we try to find it by phone from the metadata
    if not contact_id:
        customer_phone = payload.get("call", {}).get("customer", {}).get("number")
        # In a real scenario, you'd lookup contact_id by phone in your DB
        # contact_id = inventory.get_lead_by_phone(customer_phone)['id']

    result = appointment.book_tour(contact_id, slot_time, property_addr)

    return {"results": [{"toolCallId": tool_call.get("id"), "result": json.dumps(result)}]}


@app.get("/portal/deck")
async def get_smart_deck(contact_id: str):
    """
    Fetches a personalized deck of properties for a lead.
    This is used by the SwipeDeck React component.
    """
    deck = inventory.get_smart_deck(contact_id)
    return {"deck": deck}


@app.post("/portal/swipe")
async def log_swipe(interaction: Interaction):
    """
    Logs a swipe interaction and potentially triggers GHL webhooks for high-intent leads.
    """
    # 1. Log to local SQLite for analytics and preference learning
    inventory.log_interaction(
        lead_id=interaction.contact_id,
        property_id=interaction.property_id,
        action=interaction.action,
        feedback=interaction.feedback,
        time_on_card=interaction.time_on_card,
    )

    response = {"status": "success", "high_intent": False, "trigger_sms": False, "adjustments": []}

    # 2. Logic for Likes
    if interaction.action == "like":
        response["high_intent"] = True

        # A. Fetch real property data for the webhook
        prop_data = inventory.get_property(interaction.property_id)
        lead_data = inventory.get_lead(interaction.contact_id)

        # B. Tag in GHL
        ghl.add_tag_to_contact(interaction.contact_id, "Property Liked")

        # C. Update "Property Interest" field in GHL
        address = prop_data["address"] if prop_data else f"ID: {interaction.property_id}"
        ghl.update_contact_field(interaction.contact_id, ghl.field_property_interest, address)

        # D. Trigger Vapi Call (Voice AI)
        if lead_data and lead_data.get("phone"):
            trigger_outbound_call(
                contact_phone=lead_data["phone"],
                contact_name=lead_data["name"],
                property_address=address,
                contact_id=interaction.contact_id,
            )

        # E. Trigger GHL Webhook with rich match data
        match_data = {
            "score": 95,
            "property_id": interaction.property_id,
            "address": address,
            "price": prop_data["price"] if prop_data else "Contact for Price",
            "beds": prop_data["beds"] if prop_data else 0,
            "baths": prop_data["baths"] if prop_data else 0,
            "buyer_name": lead_data["name"] if lead_data else "Valued Client",
        }

        success = ghl.trigger_match_webhook(interaction.contact_id, match_data)
        response["trigger_sms"] = success

    return response


@app.post("/ghl/sync")
async def sync_ghl():
    """
    Manually triggers a sync of contacts from GHL into the local database.
    """
    try:
        count = ghl.sync_contacts_from_ghl()
        return {"status": "success", "synced_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ghl/fields")
async def get_ghl_fields():
    """
    Fetches custom fields from GHL to help developers map the field IDs.
    """
    fields = ghl.inspect_custom_fields()
    if not fields:
        return {"message": "No fields found or API key not configured"}
    return fields


if __name__ == "__main__":
    # Get port from environment variable for deployment (e.g., Railway)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
