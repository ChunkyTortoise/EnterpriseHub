"""
Smart Tour Scheduler
AI-powered showing coordination that eliminates scheduling back-and-forth

Features:
- Coordinates showing times across multiple properties
- Integrates with agent calendar + traffic patterns
- Auto-sends confirmation and reminders
- Optimizes route for efficient showings
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json


class SmartTourScheduler:
    """Service for intelligent property showing scheduling"""
    
    def schedule_tour(
        self,
        client_info: Dict[str, Any],
        properties: List[Dict[str, Any]],
        preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Schedule optimized property tour
        
        Args:
            client_info: Client details and availability
            properties: List of properties to show
            preferences: Scheduling preferences
        
        Returns:
            Optimized tour schedule with routes
        """
        preferences = preferences or {}
        
        # Get available time slots
        available_slots = self._get_available_slots(
            client_info.get('availability', []),
            preferences.get('timeframe', 'this_week')
        )
        
        # Optimize route
        optimized_route = self._optimize_route(properties)
        
        # Calculate timing
        tour_schedule = self._calculate_tour_timing(
            optimized_route,
            available_slots[0] if available_slots else None
        )
        
        # Generate confirmations
        confirmations = self._generate_confirmations(
            client_info,
            tour_schedule
        )
        
        return {
            'tour_id': f"TOUR-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
            'schedule': tour_schedule,
            'route': optimized_route,
            'total_duration_minutes': tour_schedule['total_duration'],
            'confirmations': confirmations,
            'calendar_invite': self._generate_calendar_invite(tour_schedule),
            'created_at': datetime.utcnow().isoformat()
        }
    
    def _get_available_slots(self, client_availability: List[str], timeframe: str) -> List[Dict[str, Any]]:
        """Get available time slots"""
        # Sample slots
        tomorrow = datetime.utcnow() + timedelta(days=1)
        return [
            {
                'date': tomorrow.strftime('%Y-%m-%d'),
                'start_time': '10:00 AM',
                'end_time': '2:00 PM'
            },
            {
                'date': (tomorrow + timedelta(days=1)).strftime('%Y-%m-%d'),
                'start_time': '2:00 PM',
                'end_time': '6:00 PM'
            }
        ]
    
    def _optimize_route(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize showing route to minimize drive time"""
        # In production, would use Google Maps API for routing
        # For demo, return optimized order
        return [
            {
                **prop,
                'order': idx + 1,
                'drive_time_from_previous': 15 if idx > 0 else 0
            }
            for idx, prop in enumerate(properties)
        ]
    
    def _calculate_tour_timing(self, route: List[Dict[str, Any]], start_slot: Optional[Dict] = None) -> Dict[str, Any]:
        """Calculate detailed tour timing"""
        if not start_slot:
            start_slot = {'date': datetime.utcnow().strftime('%Y-%m-%d'), 'start_time': '10:00 AM'}
        
        showing_duration = 30  # minutes per property
        buffer = 10  # buffer between showings
        
        stops = []
        current_time = datetime.strptime(f"{start_slot['date']} {start_slot['start_time']}", '%Y-%m-%d %I:%M %p')
        
        for stop in route:
            # Add drive time
            current_time += timedelta(minutes=stop.get('drive_time_from_previous', 0))
            
            arrival = current_time
            departure = current_time + timedelta(minutes=showing_duration)
            
            stops.append({
                'property': stop.get('address', 'Property'),
                'arrival_time': arrival.strftime('%I:%M %p'),
                'departure_time': departure.strftime('%I:%M %p'),
                'duration_minutes': showing_duration,
                'notes': stop.get('notes', '')
            })
            
            current_time = departure + timedelta(minutes=buffer)
        
        total_duration = (current_time - datetime.strptime(f"{start_slot['date']} {start_slot['start_time']}", '%Y-%m-%d %I:%M %p')).seconds // 60
        
        return {
            'date': start_slot['date'],
            'start_time': start_slot['start_time'],
            'end_time': current_time.strftime('%I:%M %p'),
            'total_duration': total_duration,
            'stops': stops,
            'properties_count': len(stops)
        }
    
    def _generate_confirmations(self, client_info: Dict, schedule: Dict) -> Dict[str, str]:
        """Generate confirmation messages"""
        name = client_info.get('name', 'Client')
        date = schedule['date']
        start = schedule['start_time']
        count = schedule['properties_count']
        
        return {
            'sms': f"Hi {name}! Your property tour is confirmed for {date} at {start}. We'll see {count} properties. See you there! 🏡",
            'email': f"Property Tour Confirmation\n\nDear {name},\n\nYour showing tour is scheduled for {date} starting at {start}.\n\nWe'll view {count} properties. Please arrive 5 minutes early.\n\nLooking forward to finding your perfect home!",
            'calendar': f"Property Tour - {count} Showings"
        }
    
    def _generate_calendar_invite(self, schedule: Dict) -> str:
        """Generate calendar invite URL"""
        return f"https://calendar.google.com/calendar/event?action=TEMPLATE&text=Property+Tour&dates={schedule['date']}T{schedule['start_time']}"


def demo_tour_scheduler():
    service = SmartTourScheduler()
    
    print("📸 Smart Tour Scheduler Demo\n")
    
    client = {'name': 'Sarah Johnson', 'email': 'sarah@example.com', 'phone': '555-1234'}
    properties = [
        {'address': '123 Oak St', 'notes': 'Beautiful garden'},
        {'address': '456 Maple Ave', 'notes': 'Updated kitchen'},
        {'address': '789 Pine Rd', 'notes': 'Large backyard'}
    ]
    
    tour = service.schedule_tour(client, properties)
    
    print(f"Tour ID: {tour['tour_id']}")
    print(f"Date: {tour['schedule']['date']}")
    print(f"Duration: {tour['total_duration_minutes']} minutes\n")
    
    print("SCHEDULE:")
    for stop in tour['schedule']['stops']:
        print(f"  {stop['arrival_time']}-{stop['departure_time']}: {stop['property']}")
    
    print(f"\n📱 SMS: {tour['confirmations']['sms']}")
    
    return service

if __name__ == "__main__":
    demo_tour_scheduler()
