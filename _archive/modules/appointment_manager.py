import os
import requests
import json
import datetime
from dotenv import load_dotenv
from modules.ghl_sync import GHLSyncService

load_dotenv()

class AppointmentManager:
    def __init__(self):
        self.api_key = os.getenv("GHL_API_KEY")
        self.location_id = os.getenv("GHL_LOCATION_ID")
        self.calendar_id = os.getenv("GHL_CALENDAR_ID")
        self.base_url = "https://services.leadconnectorhq.com"
        self.ghl_service = GHLSyncService()

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Version": "2021-07-28",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def check_calendar_availability(self, date_str=None):
        """
        Checks for free slots for the next 5 days from the given date (or today).
        Returns a simple list of human-readable slots to feed back to the AI.
        """
        if not date_str:
            date_str = datetime.date.today().isoformat()
        
        try:
            # Parse start date
            if "T" in date_str:
                start_date_obj = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                start_date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            
            end_date_obj = start_date_obj + datetime.timedelta(days=5)

            # GHL Endpoint: Get Free Slots (V2 uses ms timestamps)
            start_ts = int(start_date_obj.timestamp() * 1000)
            end_ts = int(end_date_obj.timestamp() * 1000)

            url = f"{self.base_url}/calendars/{self.calendar_id}/free-slots?startDate={start_ts}&endDate={end_ts}"

            if not self.api_key or self.api_key == "YOUR_KEY":
                # Mock response for development
                return {
                    "status": "success", 
                    "slots": [
                        (start_date_obj + datetime.timedelta(hours=14)).isoformat(),
                        (start_date_obj + datetime.timedelta(hours=16)).isoformat()
                    ]
                }

            response = requests.get(url, headers=self.get_headers())
            if response.status_code == 200:
                slots_data = response.json() 
                available_times = []
                
                # GHL structure: { "2024-01-01": { "slots": [...] } } or similar
                count = 0
                for date_key in slots_data:
                    day_data = slots_data[date_key]
                    if isinstance(day_data, dict) and 'slots' in day_data:
                        for slot in day_data['slots']:
                            available_times.append(slot)
                            count += 1
                            if count >= 5: break
                    if count >= 5: break
                
                return {"status": "success", "slots": available_times}
            else:
                return {"status": "error", "message": f"GHL Error: {response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def book_tour(self, contact_id, slot_time, property_address="Generic Inquiry"):
        """
        Finalizes the booking in Jorge's GHL Calendar.
        """
        if not self.calendar_id or not self.location_id:
            return {"status": "error", "message": "Calendar or Location ID missing."}

        url = f"{self.base_url}/appointments/"
        
        payload = {
            "calendarId": self.calendar_id,
            "locationId": self.location_id,
            "contactId": contact_id,
            "startTime": slot_time,
            "title": f"Viewing: {property_address} (AI Booked)",
            "appointmentStatus": "confirmed",
            "toNotify": True
        }

        try:
            if not self.api_key or self.api_key == "YOUR_KEY":
                print(f"🚀 [MOCK] Appointment Booked: {contact_id} at {slot_time}")
                return {"status": "success", "confirmation": "Appointment booked successfully (MOCK)."}

            response = requests.post(url, headers=self.get_headers(), json=payload)
            if response.status_code == 201:
                return {"status": "success", "confirmation": "Appointment booked successfully."}
            else:
                return {"status": "error", "message": f"Booking failed: {response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}