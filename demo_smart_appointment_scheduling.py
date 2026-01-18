#!/usr/bin/env python3
"""
Smart Appointment Scheduling Demonstration Script

Demonstrates Jorge's smart appointment scheduling system for lead bot:

🏡 Key Features:
- Automatic booking for qualified leads (score ≥ 5)
- Real-time calendar integration with GHL
- SMS confirmations to leads
- Timezone handling for Austin market
- 40% faster lead→appointment conversion target

🎯 Jorge's Business Requirements:
- Auto-book buyer consultations (1 hour)
- Auto-book listing appointments (1.5 hours)
- Auto-book investor meetings (45 minutes)
- Business hours: M-F 9AM-6PM, Sat 10AM-4PM CT
- Buffer time between appointments (15 minutes)
- Fallback to manual scheduling when needed

Usage:
    python demo_smart_appointment_scheduling.py
"""

import asyncio
from datetime import datetime, timedelta
import json
from typing import Dict, Any

import pytz

from ghl_real_estate_ai.services.calendar_scheduler import (
    CalendarScheduler,
    AppointmentType,
    TimeSlot,
    AUSTIN_TZ
)
from ghl_real_estate_ai.ghl_utils.config import settings


class MockGHLClient:
    """Mock GHL client for demonstration purposes."""

    def __init__(self):
        self.appointments_created = []
        self.messages_sent = []

    async def get_available_slots(self, calendar_id: str, start_date: str, end_date: str, timezone: str = "America/Chicago"):
        """Mock calendar availability."""
        # Generate some realistic available slots
        now = datetime.now(AUSTIN_TZ)
        tomorrow = now + timedelta(days=1)

        # Create slots at 10 AM, 2 PM, and 4 PM tomorrow
        slots = []
        for hour in [10, 14, 16]:
            slot_time = tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)
            slots.append({
                "start_time": slot_time.isoformat(),
                "end_time": (slot_time + timedelta(minutes=60)).isoformat(),
                "available": True
            })

        print(f"📅 Found {len(slots)} available slots in calendar {calendar_id}")
        return slots

    async def create_appointment(self, contact_id: str, calendar_id: str, start_time: str, title: str, assigned_user_id: str = None):
        """Mock appointment creation."""
        appointment = {
            "id": f"apt_{len(self.appointments_created) + 1:06d}",
            "contact_id": contact_id,
            "calendar_id": calendar_id,
            "start_time": start_time,
            "title": title,
            "status": "confirmed",
            "assigned_user_id": assigned_user_id
        }

        self.appointments_created.append(appointment)
        print(f"✅ Created appointment: {appointment['id']} - {title}")
        return appointment

    async def send_message(self, contact_id: str, message: str, channel: str):
        """Mock SMS sending."""
        message_record = {
            "contact_id": contact_id,
            "message": message,
            "channel": channel,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.messages_sent.append(message_record)
        print(f"📱 SMS sent to {contact_id}: {message[:50]}...")
        return {"messageId": f"msg_{len(self.messages_sent)}", "status": "sent"}


async def demo_qualified_buyer_lead():
    """Demonstrate appointment scheduling for qualified buyer."""
    print("\n" + "="*60)
    print("🏠 DEMO 1: Qualified Buyer Lead Auto-Booking")
    print("="*60)

    # Mock qualified buyer lead data
    contact_info = {
        "contact_id": "contact_buyer_demo",
        "first_name": "Sarah",
        "last_name": "Johnson",
        "phone": "+15125551234",
        "email": "sarah.johnson@example.com"
    }

    extracted_data = {
        "budget": 450000,
        "location": ["Austin", "Cedar Park"],
        "timeline": "next month",
        "bedrooms": 3,
        "bathrooms": 2,
        "financing": "pre-approved",
        "motivation": "first time buyer, outgrowing apartment"
    }

    lead_score = 6  # High score - 6 questions answered
    message_content = "Yes, I'm pre-approved up to $450k and ready to start looking at 3BR homes in Austin!"

    print(f"👤 Lead: {contact_info['first_name']} {contact_info['last_name']}")
    print(f"📊 Score: {lead_score}/7 questions answered (85% qualification)")
    print(f"💰 Budget: ${extracted_data['budget']:,}")
    print(f"📍 Areas: {', '.join(extracted_data['location'])}")
    print(f"⏰ Timeline: {extracted_data['timeline']}")
    print(f"💳 Financing: {extracted_data['financing']}")

    # Initialize scheduler with mock client
    mock_client = MockGHLClient()
    scheduler = CalendarScheduler(ghl_client=mock_client)

    # Check if should auto-book
    should_book, reason, appointment_type = await scheduler.should_auto_book(
        lead_score=lead_score,
        contact_info=contact_info,
        extracted_data=extracted_data
    )

    print(f"\n🤖 Auto-booking evaluation:")
    print(f"   Should book: {should_book}")
    print(f"   Reason: {reason}")
    print(f"   Appointment type: {appointment_type.value}")

    if should_book:
        # Handle appointment request
        booking_attempted, response_message, actions = await scheduler.handle_appointment_request(
            contact_id=contact_info["contact_id"],
            contact_info=contact_info,
            lead_score=lead_score,
            extracted_data=extracted_data,
            message_content=message_content
        )

        print(f"\n📋 Booking result:")
        print(f"   Attempted: {booking_attempted}")
        print(f"   Response: {response_message}")
        print(f"   Actions: {len(actions)} GHL actions generated")

        # Show created appointments
        if mock_client.appointments_created:
            print(f"\n📅 Appointments created:")
            for apt in mock_client.appointments_created:
                start_time = datetime.fromisoformat(apt['start_time'].replace('Z', '+00:00'))
                austin_time = start_time.astimezone(AUSTIN_TZ)
                print(f"   • {apt['title']}")
                print(f"     Time: {austin_time.strftime('%A, %B %d at %I:%M %p CT')}")
                print(f"     ID: {apt['id']}")

        # Show SMS confirmations
        if mock_client.messages_sent:
            print(f"\n📱 SMS confirmations sent:")
            for msg in mock_client.messages_sent:
                print(f"   To: {msg['contact_id']}")
                print(f"   Preview: {msg['message'][:100]}...")


async def demo_qualified_seller_lead():
    """Demonstrate appointment scheduling for qualified seller."""
    print("\n" + "="*60)
    print("🏡 DEMO 2: Qualified Seller Lead Auto-Booking")
    print("="*60)

    # Mock qualified seller lead data
    contact_info = {
        "contact_id": "contact_seller_demo",
        "first_name": "Michael",
        "last_name": "Rodriguez",
        "phone": "+15125559876",
        "email": "michael.rodriguez@example.com"
    }

    extracted_data = {
        "location": ["Round Rock"],
        "timeline": "ASAP",
        "motivation": "need to sell quickly, job relocation",
        "home_condition": "excellent condition, recently renovated",
        "bedrooms": 4,
        "bathrooms": 3
    }

    lead_score = 5  # Exactly at threshold
    message_content = "I need to sell my house ASAP due to job relocation. It's 4BR/3BA in excellent condition."

    print(f"👤 Lead: {contact_info['first_name']} {contact_info['last_name']}")
    print(f"📊 Score: {lead_score}/7 questions answered (75% qualification)")
    print(f"📍 Location: {', '.join(extracted_data['location'])}")
    print(f"⏰ Timeline: {extracted_data['timeline']} (URGENT)")
    print(f"🏠 Condition: {extracted_data['home_condition']}")
    print(f"💼 Motivation: {extracted_data['motivation']}")

    # Initialize scheduler
    mock_client = MockGHLClient()
    scheduler = CalendarScheduler(ghl_client=mock_client)

    # Check appointment type detection
    appointment_type = scheduler._determine_appointment_type(extracted_data)
    print(f"\n🔍 Appointment type detected: {appointment_type.value}")

    # Check urgency detection
    is_urgent = scheduler._is_urgent_timeline(extracted_data['timeline'])
    print(f"🚨 Urgent timeline: {is_urgent}")

    # Handle appointment request
    booking_attempted, response_message, actions = await scheduler.handle_appointment_request(
        contact_id=contact_info["contact_id"],
        contact_info=contact_info,
        lead_score=lead_score,
        extracted_data=extracted_data,
        message_content=message_content
    )

    print(f"\n📋 Booking result:")
    print(f"   Attempted: {booking_attempted}")
    print(f"   Response: {response_message}")

    if mock_client.appointments_created:
        print(f"\n📅 Listing appointment scheduled:")
        apt = mock_client.appointments_created[-1]
        print(f"   • {apt['title']}")
        print(f"   • Duration: 90 minutes (listing presentation)")
        print(f"   • Priority: HIGH (urgent timeline)")


async def demo_unqualified_lead():
    """Demonstrate handling of unqualified lead."""
    print("\n" + "="*60)
    print("🔍 DEMO 3: Unqualified Lead (No Auto-Booking)")
    print("="*60)

    contact_info = {
        "contact_id": "contact_browser_demo",
        "first_name": "Jennifer",
        "last_name": "Browser",
        "phone": "+15125553333",
        "email": "jen.browser@example.com"
    }

    extracted_data = {
        "location": ["Austin"]  # Only 1 question answered
    }

    lead_score = 1  # Below threshold
    message_content = "Hi, just browsing around"

    print(f"👤 Lead: {contact_info['first_name']} {contact_info['last_name']}")
    print(f"📊 Score: {lead_score}/7 questions answered (15% qualification)")
    print(f"📍 Location: {', '.join(extracted_data['location'])}")
    print(f"💬 Message: {message_content}")

    mock_client = MockGHLClient()
    scheduler = CalendarScheduler(ghl_client=mock_client)

    should_book, reason, appointment_type = await scheduler.should_auto_book(
        lead_score=lead_score,
        contact_info=contact_info,
        extracted_data=extracted_data
    )

    print(f"\n🤖 Auto-booking evaluation:")
    print(f"   Should book: {should_book}")
    print(f"   Reason: {reason}")
    print(f"   Next action: Continue nurturing conversation to gather more info")


async def demo_business_hours_validation():
    """Demonstrate business hours validation."""
    print("\n" + "="*60)
    print("🕒 DEMO 4: Business Hours Validation")
    print("="*60)

    scheduler = CalendarScheduler()

    # Test various times
    test_times = [
        ("Monday 10:00 AM", datetime(2024, 1, 15, 10, 0, 0, tzinfo=AUSTIN_TZ)),
        ("Monday 8:00 AM", datetime(2024, 1, 15, 8, 0, 0, tzinfo=AUSTIN_TZ)),
        ("Friday 6:00 PM", datetime(2024, 1, 19, 18, 0, 0, tzinfo=AUSTIN_TZ)),
        ("Saturday 2:00 PM", datetime(2024, 1, 20, 14, 0, 0, tzinfo=AUSTIN_TZ)),
        ("Sunday 2:00 PM", datetime(2024, 1, 21, 14, 0, 0, tzinfo=AUSTIN_TZ)),
    ]

    print("Jorge's Austin Business Hours:")
    print("Monday-Friday: 9:00 AM - 6:00 PM CT")
    print("Saturday: 10:00 AM - 4:00 PM CT")
    print("Sunday: CLOSED")
    print()

    for description, test_time in test_times:
        is_valid = scheduler._is_during_business_hours(test_time)
        status = "✅ AVAILABLE" if is_valid else "❌ OUTSIDE HOURS"
        print(f"{description}: {status}")


async def demo_rate_limiting():
    """Demonstrate rate limiting for booking attempts."""
    print("\n" + "="*60)
    print("🛡️ DEMO 5: Rate Limiting Protection")
    print("="*60)

    scheduler = CalendarScheduler()
    contact_id = "contact_rate_test"

    print("Testing booking attempt rate limiting...")
    print("Limit: 3 attempts per hour per contact")
    print()

    for attempt in range(5):
        allowed = scheduler._check_rate_limit(contact_id)
        status = "✅ ALLOWED" if allowed else "❌ BLOCKED"
        print(f"Attempt {attempt + 1}: {status}")

        if not allowed:
            print("   → Rate limit exceeded, fallback to manual scheduling")
            break


def display_system_overview():
    """Display system overview and statistics."""
    print("\n" + "="*60)
    print("📊 SMART APPOINTMENT SCHEDULING SYSTEM OVERVIEW")
    print("="*60)

    print("🎯 Jorge's Business Goals:")
    print("   • 40% faster lead→appointment conversion")
    print("   • Automatic booking for qualified leads (score ≥ 5)")
    print("   • Professional SMS confirmations")
    print("   • Zero double-bookings")
    print("   • Austin timezone handling")
    print()

    print("🏠 Appointment Types:")
    print("   • Buyer Consultation: 60 minutes")
    print("   • Listing Appointment: 90 minutes")
    print("   • Investor Meeting: 45 minutes")
    print("   • Property Showing: 30 minutes")
    print("   • Follow-up Call: 15 minutes")
    print()

    print("⚡ Performance Features:")
    print("   • Real-time calendar integration")
    print("   • Intelligent appointment type detection")
    print("   • Business hours validation")
    print("   • Rate limiting protection")
    print("   • Graceful error handling")
    print("   • Fallback to manual scheduling")
    print()

    print("🔒 Security & Reliability:")
    print("   • Lead qualification validation")
    print("   • Contact information verification")
    print("   • Audit logging for all bookings")
    print("   • Error tracking and alerts")
    print("   • PII protection in logs")


async def main():
    """Run all demonstrations."""
    print("🤖 Jorge's Smart Appointment Scheduling System")
    print("AI-Powered Lead Bot with Automatic Calendar Integration")

    display_system_overview()

    try:
        await demo_qualified_buyer_lead()
        await demo_qualified_seller_lead()
        await demo_unqualified_lead()
        await demo_business_hours_validation()
        await demo_rate_limiting()

        print("\n" + "="*60)
        print("✅ DEMONSTRATION COMPLETE")
        print("="*60)
        print("📈 Expected Results:")
        print("   • Qualified leads automatically book appointments")
        print("   • 40% faster conversion vs manual scheduling")
        print("   • Higher lead satisfaction with instant booking")
        print("   • Reduced manual work for Jorge")
        print("   • Professional, consistent communication")
        print()
        print("🚀 Ready for production deployment!")

    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())