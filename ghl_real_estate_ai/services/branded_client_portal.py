"""
Branded Client Portal
White-labeled client dashboard with real-time updates

Features:
- Real-time property updates for buyers
- Showing history and feedback tracking
- Document uploads and e-signatures
- Mobile-responsive white-labeled experience
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class BrandedClientPortal:
    """Service for branded client portal"""

    def create_client_portal(
        self, client_info: Dict[str, Any], agent_branding: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create personalized client portal

        Args:
            client_info: Client details
            agent_branding: Agent/company branding

        Returns:
            Portal configuration and access details
        """

        portal_id = f"PORTAL-{datetime.utcnow().strftime('%Y%m%d%H%M')}"

        # Generate portal
        portal = {
            "portal_id": portal_id,
            "client": client_info,
            "branding": agent_branding or self._default_branding(),
            "url": f"https://portal.example.com/{portal_id}",
            "access_code": self._generate_access_code(),
            "features": self._get_portal_features(),
            "dashboard": self._create_dashboard(client_info),
            "created_at": datetime.utcnow().isoformat(),
        }

        return portal

    def get_portal_dashboard(self, portal_id: str) -> Dict[str, Any]:
        """Get portal dashboard data"""
        return {
            "portal_id": portal_id,
            "saved_properties": self._get_saved_properties(),
            "showing_history": self._get_showing_history(),
            "documents": self._get_documents(),
            "messages": self._get_messages(),
            "activity_feed": self._get_activity_feed(),
            "next_steps": self._get_next_steps(),
        }

    def _default_branding(self) -> Dict[str, Any]:
        """Default branding configuration"""
        return {
            "agent_name": "Sarah Johnson",
            "company_name": "Dream Homes Realty",
            "logo_url": "https://example.com/logo.png",
            "primary_color": "#2563eb",
            "secondary_color": "#1e40af",
            "phone": "555-HOMES",
            "email": "sarah@dreamhomes.com",
        }

    def _generate_access_code(self) -> str:
        """Generate secure access code"""
        import random

        return "".join([str(random.randint(0, 9)) for _ in range(6)])

    def _get_portal_features(self) -> List[str]:
        """List of portal features"""
        return [
            "Property Search & Saved Listings",
            "Showing Scheduler",
            "Document Center",
            "Secure Messaging",
            "Market Updates",
            "Neighborhood Insights",
            "Mortgage Calculator",
            "E-Signatures",
        ]

    def _create_dashboard(self, client_info: Dict) -> Dict[str, Any]:
        """Create personalized dashboard"""
        return {
            "welcome_message": f"Welcome back, {client_info.get('name', 'Client')}!",
            "stats": {
                "properties_viewed": 12,
                "properties_saved": 5,
                "showings_completed": 3,
                "documents_pending": 2,
            },
            "quick_actions": [
                "Schedule Showing",
                "Search Properties",
                "Message Agent",
                "Upload Document",
            ],
        }

    def _get_saved_properties(self) -> List[Dict[str, Any]]:
        """Get saved properties"""
        return [
            {
                "address": "123 Oak Street",
                "price": 525000,
                "bedrooms": 4,
                "bathrooms": 2.5,
                "sqft": 2400,
                "saved_date": "2026-01-05",
                "notes": "Love the kitchen!",
                "showing_scheduled": True,
                "showing_date": "2026-01-08",
            },
            {
                "address": "456 Maple Avenue",
                "price": 485000,
                "bedrooms": 3,
                "bathrooms": 2,
                "sqft": 1800,
                "saved_date": "2026-01-04",
                "notes": "Great neighborhood",
                "showing_scheduled": False,
            },
        ]

    def _get_showing_history(self) -> List[Dict[str, Any]]:
        """Get showing history with feedback"""
        return [
            {
                "property": "789 Pine Road",
                "date": "2026-01-03",
                "feedback": "Too small for our needs",
                "rating": 3,
                "agent_notes": "Looking for larger space",
            },
            {
                "property": "321 Elm Street",
                "date": "2026-01-02",
                "feedback": "Loved it! Top choice",
                "rating": 5,
                "agent_notes": "Very interested, discussing offer",
            },
        ]

    def _get_documents(self) -> List[Dict[str, Any]]:
        """Get document list"""
        return [
            {
                "name": "Pre-Approval Letter",
                "type": "PDF",
                "status": "Uploaded",
                "date": "2025-12-20",
                "size": "1.2 MB",
            },
            {
                "name": "Purchase Agreement",
                "type": "PDF",
                "status": "Pending Signature",
                "date": "2026-01-05",
                "requires_action": True,
            },
        ]

    def _get_messages(self) -> List[Dict[str, Any]]:
        """Get recent messages"""
        return [
            {
                "from": "Sarah Johnson",
                "message": "Great news! The seller accepted your offer on 321 Elm!",
                "timestamp": "2026-01-05 10:30 AM",
                "unread": True,
            },
            {
                "from": "You",
                "message": "Can we schedule a second showing at 321 Elm?",
                "timestamp": "2026-01-04 3:15 PM",
                "unread": False,
            },
        ]

    def _get_activity_feed(self) -> List[Dict[str, Any]]:
        """Get activity feed"""
        return [
            {
                "type": "new_match",
                "message": "New property matches your criteria",
                "details": "987 Birch Lane - $510,000",
                "timestamp": "2 hours ago",
            },
            {
                "type": "price_change",
                "message": "Price reduced on saved property",
                "details": "456 Maple Ave - Now $475,000",
                "timestamp": "1 day ago",
            },
            {
                "type": "showing_complete",
                "message": "Showing completed",
                "details": "789 Pine Road",
                "timestamp": "3 days ago",
            },
        ]

    def _get_next_steps(self) -> List[Dict[str, Any]]:
        """Get recommended next steps"""
        return [
            {
                "title": "Review Offer on 321 Elm",
                "description": "Seller has countered your offer",
                "priority": "high",
                "due": "Today",
            },
            {
                "title": "Schedule Home Inspection",
                "description": "Book inspection for accepted offer",
                "priority": "high",
                "due": "Within 5 days",
            },
            {
                "title": "Upload Proof of Funds",
                "description": "Required for closing",
                "priority": "medium",
                "due": "This week",
            },
        ]


def demo_client_portal():
    service = BrandedClientPortal()

    print("🎨 Branded Client Portal Demo\n")

    client = {
        "name": "Michael Chen",
        "email": "michael@example.com",
        "phone": "555-9876",
        "buying_stage": "active",
    }

    # Create portal
    portal = service.create_client_portal(client)

    print(f"{'='*70}")
    print("CLIENT PORTAL CREATED")
    print(f"{'='*70}")
    print(f"Portal ID: {portal['portal_id']}")
    print(f"URL: {portal['url']}")
    print(f"Access Code: {portal['access_code']}")

    print(f"\n🎨 BRANDING:")
    branding = portal["branding"]
    print(f"   Agent: {branding['agent_name']}")
    print(f"   Company: {branding['company_name']}")

    # Get dashboard
    dashboard = service.get_portal_dashboard(portal["portal_id"])

    print(f"\n📊 DASHBOARD STATS:")
    stats = dashboard.get("dashboard", {}).get("stats", {})
    for key, value in stats.items():
        print(f"   {key.replace('_', ' ').title()}: {value}")

    print(f"\n🏠 SAVED PROPERTIES ({len(dashboard['saved_properties'])}):")
    for prop in dashboard["saved_properties"][:2]:
        print(f"   • {prop['address']} - ${prop['price']:,}")
        if prop["showing_scheduled"]:
            print(f"     Showing: {prop['showing_date']}")

    print(f"\n📋 NEXT STEPS:")
    for step in dashboard["next_steps"]:
        print(f"   [{step['priority'].upper()}] {step['title']}")
        print(f"      Due: {step['due']}")

    print(f"\n💬 UNREAD MESSAGES:")
    unread = [m for m in dashboard["messages"] if m.get("unread")]
    for msg in unread:
        print(f"   From {msg['from']}: {msg['message'][:50]}...")

    return service


if __name__ == "__main__":
    demo_client_portal()
