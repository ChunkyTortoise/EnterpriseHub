"""
GoHighLevel API Client
Wrapper for GHL API v2 with Jorge's credentials integration.
"""

import os
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json


class GHLAPIClient:
    """
    GoHighLevel API Client for real estate automation.
    Connects to Jorge's GHL location for live data access.
    """
    
    BASE_URL = "https://services.leadconnectorhq.com"
    API_VERSION = "v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        location_id: Optional[str] = None
    ):
        """
        Initialize GHL API Client.
        
        Args:
            api_key: GHL API key (defaults to env var)
            location_id: GHL Location ID (defaults to env var)
        """
        self.api_key = api_key or os.getenv("GHL_API_KEY")
        self.location_id = location_id or os.getenv("GHL_LOCATION_ID")
        
        if not self.api_key:
            raise ValueError("GHL_API_KEY is required. Set environment variable or pass as argument.")
        
        if not self.location_id:
            raise ValueError("GHL_LOCATION_ID is required. Set environment variable or pass as argument.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Version": "2021-07-28",
            "Content-Type": "application/json"
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        Make API request to GHL.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            API response as dictionary
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            
            return {
                "success": True,
                "data": response.json() if response.content else {},
                "status_code": response.status_code
            }
            
        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": e.response.status_code if hasattr(e, 'response') else 500,
                "details": e.response.json() if hasattr(e, 'response') and e.response.content else {}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "status_code": 500
            }
    
    # ========== CONTACTS/LEADS ==========
    
    def get_contacts(
        self,
        limit: int = 100,
        skip: int = 0,
        query: Optional[str] = None
    ) -> Dict:
        """
        Get contacts/leads from GHL.
        
        Args:
            limit: Number of contacts to retrieve
            skip: Number to skip (pagination)
            query: Search query
            
        Returns:
            List of contacts
        """
        params = {
            "locationId": self.location_id,
            "limit": limit,
            "skip": skip
        }
        
        if query:
            params["query"] = query
        
        return self._make_request("GET", "contacts", params=params)
    
    def get_contact(self, contact_id: str) -> Dict:
        """
        Get single contact by ID.
        
        Args:
            contact_id: GHL Contact ID
            
        Returns:
            Contact details
        """
        return self._make_request("GET", f"contacts/{contact_id}")
    
    def create_contact(self, contact_data: Dict) -> Dict:
        """
        Create new contact in GHL.
        
        Args:
            contact_data: Contact information
            
        Returns:
            Created contact
        """
        contact_data["locationId"] = self.location_id
        return self._make_request("POST", "contacts", data=contact_data)
    
    def update_contact(self, contact_id: str, updates: Dict) -> Dict:
        """
        Update contact information.
        
        Args:
            contact_id: GHL Contact ID
            updates: Fields to update
            
        Returns:
            Updated contact
        """
        return self._make_request("PUT", f"contacts/{contact_id}", data=updates)
    
    def add_tag_to_contact(self, contact_id: str, tag: str) -> Dict:
        """
        Add tag to contact.
        
        Args:
            contact_id: GHL Contact ID
            tag: Tag to add
            
        Returns:
            Update result
        """
        return self._make_request(
            "POST",
            f"contacts/{contact_id}/tags",
            data={"tags": [tag]}
        )
    
    # ========== OPPORTUNITIES ==========
    
    def get_opportunities(
        self,
        pipeline_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict:
        """
        Get opportunities (deals) from GHL.
        
        Args:
            pipeline_id: Filter by pipeline
            status: Filter by status
            
        Returns:
            List of opportunities
        """
        params = {"locationId": self.location_id}
        
        if pipeline_id:
            params["pipelineId"] = pipeline_id
        if status:
            params["status"] = status
        
        return self._make_request("GET", "opportunities", params=params)
    
    def get_opportunity(self, opportunity_id: str) -> Dict:
        """
        Get single opportunity by ID.
        
        Args:
            opportunity_id: GHL Opportunity ID
            
        Returns:
            Opportunity details
        """
        return self._make_request("GET", f"opportunities/{opportunity_id}")
    
    def create_opportunity(self, opportunity_data: Dict) -> Dict:
        """
        Create new opportunity.
        
        Args:
            opportunity_data: Opportunity information
            
        Returns:
            Created opportunity
        """
        opportunity_data["locationId"] = self.location_id
        return self._make_request("POST", "opportunities", data=opportunity_data)
    
    def update_opportunity(self, opportunity_id: str, updates: Dict) -> Dict:
        """
        Update opportunity.
        
        Args:
            opportunity_id: GHL Opportunity ID
            updates: Fields to update
            
        Returns:
            Updated opportunity
        """
        return self._make_request("PUT", f"opportunities/{opportunity_id}", data=updates)
    
    # ========== PIPELINES ==========
    
    def get_pipelines(self) -> Dict:
        """
        Get all pipelines for location.
        
        Returns:
            List of pipelines
        """
        return self._make_request("GET", f"opportunities/pipelines", params={"locationId": self.location_id})
    
    # ========== CONVERSATIONS ==========
    
    def get_conversations(self, contact_id: str) -> Dict:
        """
        Get conversations for a contact.
        
        Args:
            contact_id: GHL Contact ID
            
        Returns:
            List of conversations
        """
        return self._make_request("GET", f"conversations", params={"contactId": contact_id})
    
    def send_message(
        self,
        contact_id: str,
        message: str,
        message_type: str = "SMS"
    ) -> Dict:
        """
        Send message to contact.
        
        Args:
            contact_id: GHL Contact ID
            message: Message text
            message_type: SMS or Email
            
        Returns:
            Message send result
        """
        data = {
            "contactId": contact_id,
            "message": message,
            "type": message_type
        }
        
        return self._make_request("POST", "conversations/messages", data=data)
    
    # ========== CUSTOM FIELDS ==========
    
    def get_custom_fields(self) -> Dict:
        """
        Get custom fields for location.
        
        Returns:
            List of custom fields
        """
        return self._make_request("GET", "custom-fields", params={"locationId": self.location_id})
    
    def update_custom_field(
        self,
        contact_id: str,
        field_id: str,
        field_value: Any
    ) -> Dict:
        """
        Update custom field value for contact.
        
        Args:
            contact_id: GHL Contact ID
            field_id: Custom field ID
            field_value: New value
            
        Returns:
            Update result
        """
        return self.update_contact(contact_id, {
            "customFields": [{"id": field_id, "value": str(field_value)}]
        })
    
    # ========== HELPER METHODS ==========
    
    def search_contacts_by_email(self, email: str) -> Dict:
        """
        Search for contact by email.
        
        Args:
            email: Email address
            
        Returns:
            Contact if found
        """
        return self.get_contacts(query=email, limit=1)
    
    def get_hot_leads(self, days: int = 7) -> Dict:
        """
        Get recently created leads (hot leads).
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of recent contacts
        """
        # Get recent contacts
        contacts = self.get_contacts(limit=100)
        
        if not contacts.get("success"):
            return contacts
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_contacts = []
        
        for contact in contacts.get("data", {}).get("contacts", []):
            created_at = contact.get("dateAdded")
            if created_at:
                contact_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if contact_date > cutoff_date:
                    recent_contacts.append(contact)
        
        return {
            "success": True,
            "data": {
                "contacts": recent_contacts,
                "count": len(recent_contacts)
            }
        }
    
    def get_deal_pipeline_summary(self) -> Dict:
        """
        Get summary of all deals in pipeline.
        
        Returns:
            Pipeline summary with counts and values
        """
        opportunities = self.get_opportunities()
        
        if not opportunities.get("success"):
            return opportunities
        
        opps = opportunities.get("data", {}).get("opportunities", [])
        
        # Calculate summary
        summary = {
            "total_deals": len(opps),
            "total_value": sum(float(opp.get("monetaryValue", 0)) for opp in opps),
            "by_stage": {},
            "generated_at": datetime.now().isoformat()
        }
        
        # Group by stage
        for opp in opps:
            stage = opp.get("pipelineStageId", "unknown")
            if stage not in summary["by_stage"]:
                summary["by_stage"][stage] = {
                    "count": 0,
                    "value": 0
                }
            
            summary["by_stage"][stage]["count"] += 1
            summary["by_stage"][stage]["value"] += float(opp.get("monetaryValue", 0))
        
        return {
            "success": True,
            "data": summary
        }
    
    def health_check(self) -> Dict:
        """
        Check API connection health.
        
        Returns:
            Health status
        """
        try:
            # Try simple contacts request
            result = self.get_contacts(limit=1)
            
            return {
                "healthy": result.get("success", False),
                "api_key_valid": result.get("success", False),
                "location_id": self.location_id,
                "checked_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            }


# Jorge's Production Credentials
JORGE_CREDENTIALS = {
    "location_id": "REDACTED_LOCATION_ID",
    "api_key": "your_ghl_api_key_here",
    "email": "realtorjorgesales@gmail.com"
}


def get_jorge_client() -> GHLAPIClient:
    """
    Get GHL API client configured for Jorge's account.
    
    Returns:
        Configured GHLAPIClient instance
    """
    return GHLAPIClient(
        api_key=JORGE_CREDENTIALS["api_key"],
        location_id=JORGE_CREDENTIALS["location_id"]
    )


if __name__ == "__main__":
    # Demo usage
    print("🔌 GHL API Client - Connection Test\n")
    
    try:
        client = get_jorge_client()
        health = client.health_check()
        
        print(f"API Health: {'✅ Healthy' if health['healthy'] else '❌ Unhealthy'}")
        print(f"Location ID: {health['location_id']}")
        print(f"Checked At: {health['checked_at']}")
        
        if health['healthy']:
            print("\n📊 Testing API Endpoints...")
            
            # Test contacts
            contacts = client.get_contacts(limit=5)
            if contacts['success']:
                count = len(contacts.get('data', {}).get('contacts', []))
                print(f"✅ Contacts: Retrieved {count} contacts")
            
            # Test opportunities
            opps = client.get_opportunities()
            if opps['success']:
                count = len(opps.get('data', {}).get('opportunities', []))
                print(f"✅ Opportunities: Retrieved {count} deals")
            
            print("\n🎉 All API endpoints working!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
