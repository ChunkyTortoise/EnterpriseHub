import os
import requests
import json
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GHLSyncService:
    def __init__(self, api_key=None, location_id=None, db_path=None):
        self.base_url = "https://services.leadconnectorhq.com"
        self.api_key = api_key or os.getenv("GHL_API_KEY", "YOUR_KEY")
        self.location_id = location_id or os.getenv("GHL_LOCATION_ID", "YOUR_LOC_ID")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Version": "2021-07-28",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        if db_path is None:
            db_url = os.getenv("DATABASE_URL")
            if db_url and db_url.startswith("sqlite:///"):
                self.db_path = db_url.replace("sqlite:///", "")
            else:
                self.db_path = os.getenv("DB_PATH", "real_estate_engine.db")
        else:
            self.db_path = db_path
        
        # -----------------------------------------------------------------------------
        # ⚠️ CRITICAL: REPLACE THESE WITH YOUR ACTUAL FIELD IDS FROM 'inspect_ghl_fields.py'
        # -----------------------------------------------------------------------------
        self.field_property_interest = os.getenv("FIELD_PROPERTY_INTEREST", "ghl_field_property_interest_id")
        self.field_ai_tag = os.getenv("FIELD_AI_TAG", "ghl_field_ai_tag_id")
        self.field_budget = os.getenv("FIELD_BUDGET", "ghl_field_budget_id")
        
        # Internal mapping for incoming sync
        self.field_map = {
            self.field_budget: "max_budget",
            # Add other mappings as discovered
        }

    def sync_contacts_from_ghl(self, limit=20):
        """
        Pulls contacts from GHL and upserts them into our local SQLite DB.
        """
        print("🔄 Starting GHL Sync...")
        
        url = f"{self.base_url}/contacts/?locationId={self.location_id}&limit={limit}"
        
        try:
            if self.api_key == "YOUR_KEY":
                print("⚠️ Using Mock GHL Response (No API Key set)")
                return self._mock_sync()

            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            contacts = response.json().get('contacts', [])
            
            return self._process_contacts(contacts)

        except Exception as e:
            print(f"❌ Sync Failed: {e}")
            return 0

    def _process_contacts(self, contacts):
        count = 0
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for c in contacts:
            c_id = c['id']
            # GHL V2 returns 'firstName' and 'lastName' or sometimes 'contactName'
            first_name = c.get('firstName', '')
            last_name = c.get('lastName', '')
            name = f"{first_name} {last_name}".strip() or c.get('contactName', 'Unknown')
            phone = c.get('phone', '')
            
            custom_fields = c.get('customFields', [])
            parsed_data = self._parse_custom_fields(custom_fields)
            
            budget = parsed_data.get('max_budget', 500000) 
            beds = parsed_data.get('min_beds', 2)
            must_haves = json.dumps(parsed_data.get('tags', []))

            cursor.execute("""
                INSERT OR REPLACE INTO leads (id, name, phone, max_budget, min_beds, must_haves)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (c_id, name, phone, budget, beds, must_haves))
            count += 1
            
        conn.commit()
        conn.close()
        print(f"✅ Synced {count} contacts from GHL.")
        return count

    def update_contact_field(self, contact_id, field_id, value):
        """
        Updates a SINGLE custom field for a specific contact.
        """
        if not contact_id or not field_id or field_id.startswith("ghl_field_"):
            print(f"⚠️ Skipping GHL Update: Invalid field ID {field_id}")
            return False

        url = f"{self.base_url}/contacts/{contact_id}"
        payload = {
            "customFields": [
                {
                    "id": field_id,
                    "value": str(value)
                }
            ]
        }

        try:
            if self.api_key == "YOUR_KEY":
                print(f"🚀 [MOCK] GHL Update Success: Contact {contact_id} -> {value}")
                return True

            response = requests.put(url, headers=self.headers, json=payload)
            if response.status_code == 200:
                print(f"✅ GHL Update Success: Contact {contact_id} updated with {value}")
                return True
            else:
                print(f"❌ Update Failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Update Exception: {e}")
            return False

    def add_tag_to_contact(self, contact_id, tag):
        """
        Adds a text tag (e.g., 'Hot Lead') to the contact.
        """
        if self.api_key == "YOUR_KEY":
            print(f"🚀 [MOCK] Tagged {contact_id} with '{tag}'")
            return True

        url = f"{self.base_url}/contacts/{contact_id}/tags"
        payload = {"tags": [tag]}
        
        try:
            response = requests.post(url, headers=self.headers, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Tagging Failed: {e}")
            return False

    def trigger_match_webhook(self, contact_id, match_data):
        """
        Pushes a 'Match Found' event back to GHL to send the SMS.
        """
        webhook_url = os.getenv("GHL_WEBHOOK_URL", "YOUR_GHL_WORKFLOW_WEBHOOK_URL") 
        
        # Exact payload structure from the Webhook Integration Guide
        payload = {
            "event_type": "high_intent_match",
            "contact_id": contact_id,
            "match_score": match_data.get('score', 95),
            "property": {
                "id": match_data.get('property_id'),
                "address": match_data.get('address'),
                "price": match_data.get('price'),
                "beds": match_data.get('beds'),
                "baths": match_data.get('baths'),
                "link": f"https://portal.jorgesalas.ai/p/{match_data.get('property_id', 'demo')}",
                "image_url": match_data.get('image_url', "https://placeholder.com/house.jpg")
            },
            "lead_context": {
                "name": match_data.get('buyer_name', "Valued Client"),
                "tags": match_data.get('buyer_tags', ["Interested"])
            },
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if webhook_url == "YOUR_GHL_WORKFLOW_WEBHOOK_URL":
                print(f"🚀 [MOCK] Triggered GHL Webhook for {contact_id}: {payload['property']['address']}")
                return True
            
            requests.post(webhook_url, json=payload)
            print(f"🚀 Triggered GHL Webhook for {contact_id}")
            return True
        except Exception as e:
            print(f"❌ Webhook Failed: {e}")
            return False

    def _parse_custom_fields(self, fields_list):
        result = {"tags": []}
        for f in fields_list:
            fid = f.get('id')
            val = f.get('value')
            if not fid: continue
            
            if fid == self.field_budget:
                result['max_budget'] = int(val) if val else 0
            # Add more parsing logic as needed
        return result

    def inspect_custom_fields(self):
        """Fetches all custom fields from GHL."""
        url = f"{self.base_url}/locations/{self.location_id}/customFields"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            fields = response.json().get('customFields', [])
            return fields
        except Exception as e:
            print(f"❌ Failed to fetch fields: {e}")
            return []

    def _mock_sync(self):
        """Generates mock data to simulate a GHL sync."""
        mock_contacts = [
            {"id": "ghl_1", "firstName": "GHL Test", "lastName": "Lead 1", "customFields": []},
            {"id": "ghl_2", "firstName": "GHL Test", "lastName": "Lead 2", "customFields": []}
        ]
        return self._process_contacts(mock_contacts)