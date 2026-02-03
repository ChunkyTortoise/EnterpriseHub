#!/usr/bin/env python3
"""
Sample test data fixtures for Service 6 testing.

Provides realistic test data for:
- Lead profiles and behavior patterns
- Property data and preferences
- Conversation histories
- Analytics data
- Performance metrics
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import json


class LeadProfiles:
    """Sample lead profiles for different test scenarios"""
    
    @staticmethod
    def high_engagement_lead() -> Dict[str, Any]:
        """High-quality lead with strong engagement signals"""
        return {
            'lead_id': 'lead_high_engagement_001',
            'name': 'Sarah Johnson',
            'email': 'sarah.johnson@tech-corp.com',
            'phone': '+1-512-555-0123',
            'budget': 650000,
            'timeline': 'immediate',
            'location_preferences': ['North Austin', 'Round Rock', 'Cedar Park'],
            
            # Engagement metrics
            'email_open_rate': 0.92,
            'email_click_rate': 0.68,
            'website_sessions': 28,
            'page_views_total': 156,
            'avg_session_duration_minutes': 8.5,
            'property_saves': 12,
            'property_views': 45,
            
            # Behavior patterns
            'avg_response_time_hours': 1.2,
            'messages_sent': 23,
            'questions_asked': 18,
            'calls_initiated': 3,
            'documents_requested': 7,
            
            # Demographics
            'age_range': '35-44',
            'income_estimated': 140000,
            'family_size': 4,
            'current_housing': 'renting',
            'pre_approved': True,
            'lender': 'First National Bank',
            
            # Preferences
            'home_type': 'single_family',
            'bedrooms_min': 4,
            'bathrooms_min': 2.5,
            'garage_required': True,
            'pool_preferred': True,
            'school_rating_min': 8,
            'commute_time_max_minutes': 30,
            
            # Timeline events
            'first_contact': '2026-01-01T10:00:00Z',
            'last_interaction': '2026-01-16T14:30:00Z',
            'next_follow_up': '2026-01-17T09:00:00Z'
        }
    
    @staticmethod
    def medium_engagement_lead() -> Dict[str, Any]:
        """Moderate quality lead with some engagement"""
        return {
            'lead_id': 'lead_medium_engagement_002',
            'name': 'Mike Chen',
            'email': 'mike.chen@outlook.com',
            'phone': '+1-512-555-0456',
            'budget': 425000,
            'timeline': '3-6 months',
            'location_preferences': ['South Austin', 'Buda', 'Kyle'],
            
            # Engagement metrics
            'email_open_rate': 0.67,
            'email_click_rate': 0.32,
            'website_sessions': 12,
            'page_views_total': 34,
            'avg_session_duration_minutes': 4.2,
            'property_saves': 5,
            'property_views': 18,
            
            # Behavior patterns
            'avg_response_time_hours': 8.5,
            'messages_sent': 9,
            'questions_asked': 6,
            'calls_initiated': 1,
            'documents_requested': 2,
            
            # Demographics
            'age_range': '28-35',
            'income_estimated': 95000,
            'family_size': 2,
            'current_housing': 'renting',
            'pre_approved': False,
            'lender': None,
            
            # Preferences
            'home_type': 'townhome',
            'bedrooms_min': 3,
            'bathrooms_min': 2,
            'garage_required': False,
            'pool_preferred': False,
            'school_rating_min': 6,
            'commute_time_max_minutes': 45,
            
            # Timeline events
            'first_contact': '2026-01-08T15:30:00Z',
            'last_interaction': '2026-01-15T11:20:00Z',
            'next_follow_up': '2026-01-18T14:00:00Z'
        }
    
    @staticmethod
    def low_engagement_lead() -> Dict[str, Any]:
        """Low engagement lead requiring nurturing"""
        return {
            'lead_id': 'lead_low_engagement_003',
            'name': 'Jennifer Martinez',
            'email': 'j.martinez@gmail.com',
            'phone': '+1-512-555-0789',
            'budget': 320000,
            'timeline': '6+ months',
            'location_preferences': ['East Austin', 'Manor', 'Del Valle'],
            
            # Engagement metrics
            'email_open_rate': 0.31,
            'email_click_rate': 0.08,
            'website_sessions': 4,
            'page_views_total': 11,
            'avg_session_duration_minutes': 1.8,
            'property_saves': 1,
            'property_views': 7,
            
            # Behavior patterns
            'avg_response_time_hours': 72.0,
            'messages_sent': 2,
            'questions_asked': 1,
            'calls_initiated': 0,
            'documents_requested': 0,
            
            # Demographics
            'age_range': '25-32',
            'income_estimated': 68000,
            'family_size': 1,
            'current_housing': 'family',
            'pre_approved': False,
            'lender': None,
            
            # Preferences
            'home_type': 'condo',
            'bedrooms_min': 2,
            'bathrooms_min': 1,
            'garage_required': False,
            'pool_preferred': False,
            'school_rating_min': 5,
            'commute_time_max_minutes': 60,
            
            # Timeline events
            'first_contact': '2026-01-12T16:45:00Z',
            'last_interaction': '2026-01-14T09:15:00Z',
            'next_follow_up': '2026-01-20T10:00:00Z'
        }
    
    @staticmethod
    def investor_lead() -> Dict[str, Any]:
        """Real estate investor lead profile"""
        return {
            'lead_id': 'lead_investor_004',
            'name': 'Robert Kim',
            'email': 'robert.kim@investments.com',
            'phone': '+1-512-555-0321',
            'budget': 800000,
            'timeline': 'flexible',
            'location_preferences': ['Austin Metro'],
            'investor_type': 'buy_and_hold',
            
            # Engagement metrics
            'email_open_rate': 0.78,
            'email_click_rate': 0.45,
            'website_sessions': 19,
            'page_views_total': 89,
            'avg_session_duration_minutes': 12.3,
            'property_saves': 23,
            'property_views': 67,
            
            # Behavior patterns  
            'avg_response_time_hours': 4.5,
            'messages_sent': 15,
            'questions_asked': 22,
            'calls_initiated': 5,
            'documents_requested': 12,
            
            # Demographics
            'age_range': '45-55',
            'income_estimated': 250000,
            'investment_properties': 3,
            'current_housing': 'owns',
            'pre_approved': True,
            'lender': 'Investment Capital Bank',
            
            # Investment criteria
            'home_type': 'any',
            'cap_rate_min': 0.06,
            'cash_flow_min': 500,
            'renovation_budget': 50000,
            'hold_period_years': 10,
            'market_analysis_requested': True,
            
            # Timeline events
            'first_contact': '2026-01-03T11:20:00Z',
            'last_interaction': '2026-01-16T16:45:00Z',
            'next_follow_up': '2026-01-17T08:30:00Z'
        }


class ConversationHistories:
    """Sample conversation histories for testing"""
    
    @staticmethod
    def high_engagement_conversation() -> List[Dict[str, Any]]:
        """Conversation history for engaged lead"""
        return [
            {
                'timestamp': '2026-01-14T10:00:00Z',
                'role': 'user',
                'content': 'Hi, I saw your listing for the home in North Austin. Can you tell me more about the neighborhood?',
                'channel': 'website_chat'
            },
            {
                'timestamp': '2026-01-14T10:05:00Z', 
                'role': 'assistant',
                'content': 'Great question! The North Austin area has excellent schools, including Westwood High School (rated 9/10), and is close to tech companies like Apple and Google. The neighborhood features mature trees, walking trails, and quick access to downtown.',
                'channel': 'website_chat'
            },
            {
                'timestamp': '2026-01-14T10:10:00Z',
                'role': 'user', 
                'content': 'That sounds perfect. What about the current market conditions? Should we move quickly on this one?',
                'channel': 'website_chat'
            },
            {
                'timestamp': '2026-01-14T10:15:00Z',
                'role': 'assistant',
                'content': 'Based on current market data, homes in this price range and location are averaging 12 days on market. Given your timeline and budget alignment, I\'d recommend viewing this property within the next 2-3 days.',
                'channel': 'website_chat'
            },
            {
                'timestamp': '2026-01-15T08:30:00Z',
                'role': 'user',
                'content': 'We viewed the property yesterday and loved it! What would be a competitive offer?',
                'channel': 'phone'
            },
            {
                'timestamp': '2026-01-15T08:45:00Z',
                'role': 'assistant',
                'content': 'Wonderful! Based on recent comps and market analysis, I recommend offering $545K with a 14-day close and $10K earnest money. This shows strong commitment while staying competitive.',
                'channel': 'phone'
            }
        ]
    
    @staticmethod
    def nurturing_conversation() -> List[Dict[str, Any]]:
        """Conversation history for lead requiring nurturing"""
        return [
            {
                'timestamp': '2026-01-12T16:45:00Z',
                'role': 'user',
                'content': 'I filled out the form but I am just looking for now',
                'channel': 'email'
            },
            {
                'timestamp': '2026-01-12T17:00:00Z',
                'role': 'assistant', 
                'content': 'No pressure at all! I am here to help when you are ready. In the meantime, would you like me to set up a monthly market update for your areas of interest?',
                'channel': 'email'
            },
            {
                'timestamp': '2026-01-14T09:15:00Z',
                'role': 'user',
                'content': 'Actually yes, that would be helpful. Mostly interested in East Austin area.',
                'channel': 'email'
            },
            {
                'timestamp': '2026-01-14T10:30:00Z',
                'role': 'assistant',
                'content': 'Perfect! I have set you up for monthly East Austin market reports. The area is seeing great development with new restaurants and art studios. Here is this month\\'s report...',
                'channel': 'email'
            }
        ]


class PropertyData:
    """Sample property data for matching tests"""
    
    @staticmethod
    def north_austin_properties() -> List[Dict[str, Any]]:
        """Properties in North Austin area"""
        return [
            {
                'property_id': 'prop_001',
                'address': '1234 Cedar Ridge Dr, Austin, TX 78758',
                'price': 545000,
                'bedrooms': 4,
                'bathrooms': 2.5,
                'sqft': 2100,
                'lot_size': 0.23,
                'year_built': 2018,
                'home_type': 'single_family',
                'garage': True,
                'pool': False,
                'school_district': 'Round Rock ISD',
                'elementary_rating': 9,
                'middle_school_rating': 8,
                'high_school_rating': 9,
                'hoa_fees': 150,
                'property_tax': 8900,
                'commute_to_downtown': 25,
                'walkability_score': 45,
                'nearby_amenities': ['HEB', 'Starbucks', 'Gym', 'Park'],
                'listing_date': '2026-01-10T00:00:00Z',
                'days_on_market': 6
            },
            {
                'property_id': 'prop_002', 
                'address': '5678 Oak Valley Ln, Austin, TX 78759',
                'price': 635000,
                'bedrooms': 5,
                'bathrooms': 3,
                'sqft': 2800,
                'lot_size': 0.35,
                'year_built': 2020,
                'home_type': 'single_family',
                'garage': True,
                'pool': True,
                'school_district': 'Round Rock ISD', 
                'elementary_rating': 10,
                'middle_school_rating': 9,
                'high_school_rating': 9,
                'hoa_fees': 200,
                'property_tax': 11200,
                'commute_to_downtown': 30,
                'walkability_score': 40,
                'nearby_amenities': ['Whole Foods', 'Target', 'Restaurants'],
                'listing_date': '2026-01-08T00:00:00Z',
                'days_on_market': 8
            }
        ]
    
    @staticmethod
    def investment_properties() -> List[Dict[str, Any]]:
        """Investment properties with cash flow potential"""
        return [
            {
                'property_id': 'invest_001',
                'address': '9876 Rental Ave, Austin, TX 78745',
                'price': 350000,
                'bedrooms': 3,
                'bathrooms': 2,
                'sqft': 1400,
                'year_built': 2015,
                'rental_income_potential': 2200,
                'cap_rate': 0.071,
                'cash_flow_estimated': 650,
                'tenant_occupied': True,
                'lease_expiration': '2026-08-31',
                'renovation_needed': 5000,
                'neighborhood_appreciation': 0.045
            }
        ]


class AnalyticsData:
    """Sample analytics data for testing"""
    
    @staticmethod
    def lead_funnel_metrics() -> Dict[str, Any]:
        """Lead funnel analytics data"""
        return {
            'period': '2026-01',
            'total_leads': 1247,
            'sources': {
                'website_form': 523,
                'social_media': 312,
                'referrals': 198,
                'paid_ads': 214
            },
            'conversion_funnel': {
                'leads_generated': 1247,
                'qualified_leads': 498,
                'appointments_scheduled': 187,
                'properties_shown': 98,
                'offers_made': 23,
                'closed_deals': 8
            },
            'conversion_rates': {
                'lead_to_qualified': 0.399,
                'qualified_to_appointment': 0.375,
                'appointment_to_showing': 0.524,
                'showing_to_offer': 0.235,
                'offer_to_close': 0.348
            },
            'average_days_to_convert': {
                'first_contact_to_qualified': 3.2,
                'qualified_to_appointment': 5.8,
                'appointment_to_showing': 7.1,
                'showing_to_offer': 12.4,
                'offer_to_close': 28.6
            }
        }
    
    @staticmethod
    def ai_performance_metrics() -> Dict[str, Any]:
        """AI model performance metrics"""
        return {
            'model_name': 'service6_lead_scorer_v2',
            'evaluation_period': '2026-01-01 to 2026-01-16',
            'predictions_made': 1247,
            'accuracy_metrics': {
                'overall_accuracy': 0.847,
                'precision': 0.823,
                'recall': 0.791,
                'f1_score': 0.807,
                'auc_roc': 0.889
            },
            'confidence_distribution': {
                'high_confidence': 423,  # >0.8
                'medium_confidence': 596,  # 0.6-0.8
                'low_confidence': 228  # <0.6
            },
            'processing_performance': {
                'avg_inference_time_ms': 145.7,
                'p95_inference_time_ms': 287.3,
                'cache_hit_rate': 0.334,
                'error_rate': 0.002
            },
            'feature_importance': {
                'email_engagement': 0.28,
                'budget_alignment': 0.24,
                'response_timing': 0.19,
                'property_views': 0.16,
                'communication_frequency': 0.13
            }
        }


class WebhookTestData:
    """Sample webhook payloads for testing"""
    
    @staticmethod
    def valid_signatures() -> Dict[str, str]:
        """Valid webhook signatures for testing"""
        return {
            'ghl': 'sha256=a8b4c6d2e5f8a1b3c9d7e4f2a6b8c1d5e9f3a7b2c8d4e1f6a9b5c2d8e3f7a4b1',
            'twilio': 'LxB2yBNfmOJdX/k2K1vB3c4D5e6F7g8H9i0J1k2L3m4N5o6P7q8R9s0T1u2V3w4X',
            'sendgrid': 'MEUCIQChKHC/R2LyULOFb8s+1QAnC9hPpqnP2PhQZv8jP/lf3QIgJzxaLvA5O2vB',
            'apollo': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0'
        }
    
    @staticmethod
    def invalid_signatures() -> Dict[str, str]:
        """Invalid webhook signatures for testing"""
        return {
            'ghl': 'sha256=invalid_signature_hash',
            'twilio': 'invalid_twilio_signature',
            'sendgrid': 'invalid_sendgrid_signature', 
            'apollo': 'invalid_jwt_token'
        }
    
    @staticmethod
    def ghl_lead_created() -> Dict[str, Any]:
        """GHL lead created webhook"""
        return {
            'type': 'ContactCreate',
            'timestamp': '2026-01-16T14:30:00Z',
            'locationId': 'location_123',
            'data': {
                'id': 'ghl_lead_789',
                'email': 'new.lead@example.com',
                'firstName': 'Alice',
                'lastName': 'Williams',
                'phone': '+15125551234',
                'source': 'Facebook Ad',
                'tags': ['austin', 'first-time-buyer'],
                'customFields': {
                    'budget': '450000',
                    'timeline': '2-3 months',
                    'bedrooms': '3+',
                    'location': 'South Austin'
                }
            }
        }
    
    @staticmethod  
    def twilio_call_completed() -> Dict[str, Any]:
        """Twilio call completed webhook"""
        return {
            'AccountSid': 'AC123456789',
            'CallSid': 'CA987654321',
            'From': '+15125551234',
            'To': '+15125559876',
            'CallStatus': 'completed',
            'Direction': 'inbound',
            'Duration': '180',
            'StartTime': '2026-01-16T15:00:00Z',
            'EndTime': '2026-01-16T15:03:00Z',
            'RecordingUrl': 'https://api.twilio.com/recordings/xyz.mp3'
        }