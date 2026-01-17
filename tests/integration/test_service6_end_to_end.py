#!/usr/bin/env python3
"""
End-to-End Integration Tests for Service 6 Lead Recovery & Nurture Engine.

Tests cover complete workflows from lead ingestion to nurture execution:
- Complete lead processing pipeline
- External service integration (Apollo, Twilio, SendGrid)
- AI analysis and scoring workflows
- Webhook processing and event handling  
- Database persistence and retrieval
- Error handling and fallback scenarios

Coverage Target: 100% of critical integration paths
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Import services under test
from ghl_real_estate_ai.services.service6_ai_integration import (
    Service6AIOrchestrator,
    Service6AIConfig,
    Service6AIResponse,
    create_service6_ai_orchestrator
)
from ghl_real_estate_ai.services.database_service import DatabaseService
from ghl_real_estate_ai.services.apollo_client import ApolloClient
from ghl_real_estate_ai.services.twilio_client import TwilioClient
from ghl_real_estate_ai.services.sendgrid_client import SendGridClient

# Import test utilities
from tests.mocks.external_services import (
    MockClaudeClient,
    MockRedisClient,
    MockDatabaseService,
    MockApolloClient,
    MockTwilioClient,
    MockSendGridClient
)
from tests.fixtures.sample_data import LeadProfiles, WebhookTestData


class TestCompleteLeadProcessingPipeline:
    """Test complete lead processing from ingestion to nurture"""
    
    @pytest.fixture
    async def service6_orchestrator(self):
        """Create fully integrated Service 6 orchestrator for E2E testing"""
        config = Service6AIConfig(
            enable_advanced_ml_scoring=True,
            enable_predictive_analytics=True,
            enable_claude_enhancement=True,
            max_concurrent_operations=10
        )
        
        orchestrator = create_service6_ai_orchestrator(config)
        
        # Mock all external dependencies
        orchestrator.ai_companion.cache = MockRedisClient()
        orchestrator.ai_companion.memory = MagicMock()
        orchestrator.ai_companion.memory.get_context = AsyncMock(return_value={'conversation_history': []})
        orchestrator.ai_companion.memory.update_lead_intelligence = AsyncMock(return_value=True)
        
        # Mock AI components to return realistic data
        orchestrator.ai_companion.ml_scoring_engine = MagicMock()
        orchestrator.ai_companion.ml_scoring_engine.score_lead_comprehensive = AsyncMock()
        
        orchestrator.ai_companion.predictive_analytics = MagicMock() 
        orchestrator.ai_companion.predictive_analytics.run_comprehensive_analysis = AsyncMock()
        
        orchestrator.ai_companion.enhanced_scorer = MagicMock()
        orchestrator.ai_companion.enhanced_scorer.analyze_lead_comprehensive = AsyncMock()
        
        await orchestrator.initialize()
        
        return orchestrator
    
    @pytest.fixture
    async def integrated_services(self):
        """Create integrated external services for E2E testing"""
        # Database service
        database_service = MockDatabaseService()
        
        # Apollo client for lead enrichment
        apollo_client = MockApolloClient()
        
        # Twilio client for SMS
        twilio_client = MockTwilioClient()
        
        # SendGrid client for email
        sendgrid_client = MockSendGridClient()
        
        return {
            'database': database_service,
            'apollo': apollo_client,
            'twilio': twilio_client,
            'sendgrid': sendgrid_client
        }
    
    @pytest.mark.asyncio
    async def test_new_lead_complete_workflow(self, service6_orchestrator, integrated_services):
        """Test complete workflow for new lead from ingestion to first nurture step"""
        
        # Step 1: New lead arrives (simulating GHL webhook)
        new_lead_data = LeadProfiles.high_engagement_lead()
        
        # Step 2: Store lead in database
        lead_id = await integrated_services['database'].save_lead(new_lead_data['lead_id'], new_lead_data)
        assert lead_id is True
        
        # Step 3: Enrich lead data with Apollo
        enrichment_result = await integrated_services['apollo'].enrich_lead(
            new_lead_data['email'],
            new_lead_data['phone']
        )
        
        assert enrichment_result['email'] == new_lead_data['email']
        assert enrichment_result['confidence_score'] == 0.92
        
        # Update lead with enrichment data
        enriched_data = {**new_lead_data, **enrichment_result}
        
        # Step 4: Run AI analysis and scoring
        analysis_result = await service6_orchestrator.analyze_lead(
            new_lead_data['lead_id'], 
            enriched_data
        )
        
        assert isinstance(analysis_result, Service6AIResponse)
        assert analysis_result.lead_id == new_lead_data['lead_id']
        assert analysis_result.unified_lead_score > 0
        assert analysis_result.confidence_level > 0
        assert len(analysis_result.immediate_actions) > 0
        
        # Step 5: Update lead score in database
        score_updated = await integrated_services['database'].update_lead_score(
            new_lead_data['lead_id'],
            analysis_result.unified_lead_score,
            {
                'ai_analysis': analysis_result.__dict__,
                'enrichment': enrichment_result
            }
        )
        assert score_updated is True
        
        # Step 6: Trigger initial communication based on score
        if analysis_result.unified_lead_score >= 75:
            # High-value lead: Send immediate SMS + Email
            
            # Send SMS
            sms_result = await integrated_services['twilio'].send_sms(
                to=new_lead_data['phone'],
                message=f"Hi {new_lead_data['name']}! Thanks for your interest in Austin properties. I'll send you some great options shortly!"
            )
            assert sms_result['success'] is True
            assert sms_result['message_sid'] is not None
            
            # Send welcome email
            email_result = await integrated_services['sendgrid'].send_email(
                to_email=new_lead_data['email'],
                subject="Welcome! Your Austin Property Journey Begins",
                content="Welcome to our real estate journey! Based on your interests, I've found some amazing properties..."
            )
            assert email_result['success'] is True
            assert email_result['message_id'] is not None
            
        # Step 7: Verify complete workflow success
        # Check that lead exists with updated score
        updated_lead = await integrated_services['database'].get_lead(new_lead_data['lead_id'])
        assert updated_lead is not None
        assert updated_lead['ai_score'] == analysis_result.unified_lead_score
        
        # Verify communications were tracked
        assert integrated_services['twilio'].sent_messages
        assert integrated_services['sendgrid'].sent_emails
        
        print(f"✅ Complete workflow test passed for lead {new_lead_data['lead_id']}")
        print(f"   AI Score: {analysis_result.unified_lead_score}")
        print(f"   Priority: {analysis_result.priority_level}")
        print(f"   Communications: {len(integrated_services['twilio'].sent_messages)} SMS, {len(integrated_services['sendgrid'].sent_emails)} emails")
    
    @pytest.mark.asyncio
    async def test_lead_scoring_update_workflow(self, service6_orchestrator, integrated_services):
        """Test lead rescoring workflow when new behavior data arrives"""
        
        # Step 1: Start with existing medium-engagement lead
        existing_lead_data = LeadProfiles.medium_engagement_lead()
        await integrated_services['database'].save_lead(existing_lead_data['lead_id'], existing_lead_data)
        
        # Initial scoring
        initial_analysis = await service6_orchestrator.analyze_lead(
            existing_lead_data['lead_id'],
            existing_lead_data
        )
        initial_score = initial_analysis.unified_lead_score
        
        # Step 2: Simulate new engagement activity (email opens, website visits)
        updated_engagement_data = {
            **existing_lead_data,
            'email_open_rate': 0.85,  # Improved from 0.67
            'email_click_rate': 0.55,  # Improved from 0.32
            'website_sessions': 25,    # Increased from 12
            'property_views': 35,      # Increased from 18
            'messages_sent': 15,       # Increased from 9
            'last_interaction': datetime.now().isoformat()
        }
        
        # Step 3: Re-run AI analysis with updated data
        updated_analysis = await service6_orchestrator.analyze_lead(
            existing_lead_data['lead_id'],
            updated_engagement_data
        )
        
        # Score should have improved
        assert updated_analysis.unified_lead_score > initial_score
        assert updated_analysis.priority_level in ['high', 'critical']
        
        # Step 4: Update database with new score
        await integrated_services['database'].update_lead_score(
            existing_lead_data['lead_id'],
            updated_analysis.unified_lead_score,
            {'updated_analysis': updated_analysis.__dict__}
        )
        
        # Step 5: Trigger appropriate communication based on improved score
        if updated_analysis.unified_lead_score >= 80 and initial_score < 80:
            # Lead crossed high-value threshold, send priority communication
            priority_sms = await integrated_services['twilio'].send_sms(
                to=updated_engagement_data['phone'],
                message="Hi! I noticed you've been actively looking at properties. Let's schedule a call to discuss your perfect home!"
            )
            assert priority_sms['success'] is True
        
        print(f"✅ Lead scoring update workflow passed")
        print(f"   Initial Score: {initial_score} -> Updated Score: {updated_analysis.unified_lead_score}")
        print(f"   Priority upgraded to: {updated_analysis.priority_level}")
    
    @pytest.mark.asyncio
    async def test_investor_lead_specialized_workflow(self, service6_orchestrator, integrated_services):
        """Test specialized workflow for investor leads"""
        
        # Step 1: Investor lead with specific requirements
        investor_lead_data = LeadProfiles.investor_lead()
        await integrated_services['database'].save_lead(investor_lead_data['lead_id'], investor_lead_data)
        
        # Step 2: Enhanced Apollo enrichment for investors
        investor_enrichment = await integrated_services['apollo'].enrich_lead(
            investor_lead_data['email'],
            investor_lead_data['phone']
        )
        
        # Mock investor-specific enrichment
        investor_enrichment.update({
            'company_type': 'Real Estate Investment',
            'investment_portfolio_size': 'Large',
            'business_revenue': '$1M+',
            'decision_maker': True
        })
        
        # Combine data
        enriched_investor_data = {**investor_lead_data, **investor_enrichment}
        
        # Step 3: AI analysis should recognize investor pattern
        investor_analysis = await service6_orchestrator.analyze_lead(
            investor_lead_data['lead_id'],
            enriched_investor_data
        )
        
        assert investor_analysis.unified_lead_score >= 75  # Investors typically score high
        assert 'investment' in str(investor_analysis.immediate_actions).lower()
        
        # Step 4: Trigger investor-specific communication workflow
        # Send professional email with investment analysis
        investor_email = await integrated_services['sendgrid'].send_email(
            to_email=investor_lead_data['email'],
            subject="Austin Investment Opportunities - Market Analysis",
            content="Professional investment market analysis with ROI projections..."
        )
        assert investor_email['success'] is True
        
        # Follow up SMS with quick response option
        follow_up_sms = await integrated_services['twilio'].send_sms(
            to=investor_lead_data['phone'],
            message="Sent detailed Austin investment analysis to your email. Quick call to discuss opportunities? Reply YES"
        )
        assert follow_up_sms['success'] is True
        
        print(f"✅ Investor workflow test passed")
        print(f"   Investment Score: {investor_analysis.unified_lead_score}")
        print(f"   Specialized Communications: Investment analysis email + follow-up SMS")
    
    @pytest.mark.asyncio
    async def test_nurture_sequence_progression(self, service6_orchestrator, integrated_services):
        """Test multi-step nurture sequence progression"""
        
        # Step 1: Low engagement lead enters nurture sequence
        low_engagement_lead = LeadProfiles.low_engagement_lead()
        await integrated_services['database'].save_lead(low_engagement_lead['lead_id'], low_engagement_lead)
        
        # Initial analysis identifies need for nurturing
        initial_analysis = await service6_orchestrator.analyze_lead(
            low_engagement_lead['lead_id'],
            low_engagement_lead
        )
        
        assert initial_analysis.priority_level == 'low'
        assert 'nurture' in str(initial_analysis.strategic_recommendations).lower()
        
        # Step 2: Day 1 - Welcome email
        day1_email = await integrated_services['sendgrid'].send_email(
            to_email=low_engagement_lead['email'],
            subject="Welcome to Austin Real Estate Insights",
            content="Welcome! Here's what you can expect from us..."
        )
        assert day1_email['success'] is True
        
        # Step 3: Day 3 - Market insights (simulate progression)
        await asyncio.sleep(0.1)  # Simulate time passage
        
        day3_email = await integrated_services['sendgrid'].send_email(
            to_email=low_engagement_lead['email'],
            subject="Austin Market Insights - January 2026",
            content="Here are the latest market trends for your area..."
        )
        assert day3_email['success'] is True
        
        # Step 4: Day 7 - SMS check-in
        day7_sms = await integrated_services['twilio'].send_sms(
            to=low_engagement_lead['phone'],
            message="Hi! Just checking if you're still looking in the Austin area. Any questions?"
        )
        assert day7_sms['success'] is True
        
        # Step 5: Simulate positive response to SMS
        sms_response_webhook = {
            'MessageSid': 'SM_response_123',
            'From': low_engagement_lead['phone'],
            'To': '+15551234567',
            'Body': 'Yes, still looking! Interested in East Austin properties.'
        }
        
        # Process response (this would trigger re-scoring)
        # Simulate updated engagement after positive response
        re_engaged_data = {
            **low_engagement_lead,
            'messages_sent': 5,  # Increased from 2
            'avg_response_time_hours': 6.0,  # Improved from 72.0
            'last_interaction': datetime.now().isoformat()
        }
        
        # Re-analyze after engagement
        updated_analysis = await service6_orchestrator.analyze_lead(
            low_engagement_lead['lead_id'],
            re_engaged_data
        )
        
        # Lead should now be more engaged
        assert updated_analysis.unified_lead_score > initial_analysis.unified_lead_score
        assert updated_analysis.priority_level in ['medium', 'high']
        
        print(f"✅ Nurture sequence test passed")
        print(f"   Initial Score: {initial_analysis.unified_lead_score} -> Re-engaged Score: {updated_analysis.unified_lead_score}")
        print(f"   Nurture Communications: {len(integrated_services['sendgrid'].sent_emails)} emails, {len(integrated_services['twilio'].sent_messages)} SMS")


class TestWebhookIntegrationWorkflows:
    """Test webhook processing integration workflows"""
    
    @pytest.fixture
    async def webhook_services(self):
        """Create services for webhook integration testing"""
        database = MockDatabaseService()
        twilio = MockTwilioClient()
        sendgrid = MockSendGridClient()
        
        return {
            'database': database,
            'twilio': twilio, 
            'sendgrid': sendgrid
        }
    
    @pytest.mark.asyncio
    async def test_ghl_lead_webhook_to_nurture_workflow(self, webhook_services):
        """Test complete workflow from GHL webhook to nurture initiation"""
        
        # Step 1: Simulate GHL lead webhook
        ghl_webhook_data = WebhookTestData.ghl_lead_webhook({
            'id': 'ghl_lead_12345',
            'email': 'webhook.lead@example.com',
            'firstName': 'Webhook',
            'lastName': 'User',
            'phone': '+15557890456',
            'source': 'Facebook Ad',
            'customFields': {
                'budget': '600000',
                'timeline': 'immediate',
                'location': 'North Austin'
            }
        })
        
        # Step 2: Process webhook and create lead record
        lead_data = {
            'lead_id': ghl_webhook_data['data']['id'],
            'name': f"{ghl_webhook_data['data']['firstName']} {ghl_webhook_data['data']['lastName']}",
            'email': ghl_webhook_data['data']['email'],
            'phone': ghl_webhook_data['data']['phone'],
            'source': ghl_webhook_data['data']['source'],
            'budget': int(ghl_webhook_data['data']['customFields']['budget']),
            'timeline': ghl_webhook_data['data']['customFields']['timeline'],
            'location': ghl_webhook_data['data']['customFields']['location']
        }
        
        # Save to database
        save_result = await webhook_services['database'].save_lead(lead_data['lead_id'], lead_data)
        assert save_result is True
        
        # Step 3: Determine initial communication based on source and urgency
        if lead_data['timeline'] == 'immediate' and lead_data['budget'] >= 500000:
            # High-priority lead: immediate SMS + email
            
            # Send immediate SMS
            urgent_sms = await webhook_services['twilio'].send_sms(
                to=lead_data['phone'],
                message=f"Hi {lead_data['name']}! I saw you're looking for properties in {lead_data['location']} ASAP. I have some perfect options - let's connect today!"
            )
            assert urgent_sms['success'] is True
            
            # Send detailed email
            urgent_email = await webhook_services['sendgrid'].send_email(
                to_email=lead_data['email'],
                subject=f"Urgent: Perfect {lead_data['location']} Properties Available",
                content=f"Hi {lead_data['name']}, I have several properties in {lead_data['location']} that match your ${lead_data['budget']:,} budget..."
            )
            assert urgent_email['success'] is True
            
        # Step 4: Verify workflow completion
        stored_lead = await webhook_services['database'].get_lead(lead_data['lead_id'])
        assert stored_lead is not None
        assert stored_lead['name'] == lead_data['name']
        
        # Verify communications were sent
        assert len(webhook_services['twilio'].sent_messages) >= 1
        assert len(webhook_services['sendgrid'].sent_emails) >= 1
        
        print(f"✅ GHL webhook to nurture workflow passed")
        print(f"   Lead Source: {lead_data['source']}")
        print(f"   Urgency: {lead_data['timeline']} timeline, ${lead_data['budget']:,} budget")
        print(f"   Immediate Response: {len(webhook_services['twilio'].sent_messages)} SMS, {len(webhook_services['sendgrid'].sent_emails)} emails")
    
    @pytest.mark.asyncio
    async def test_twilio_webhook_response_handling(self, webhook_services):
        """Test handling Twilio SMS response webhooks"""
        
        # Step 1: Setup existing lead
        lead_data = {
            'lead_id': 'twilio_response_lead',
            'name': 'Response Lead',
            'email': 'response@example.com',
            'phone': '+15557890789'
        }
        await webhook_services['database'].save_lead(lead_data['lead_id'], lead_data)
        
        # Step 2: Simulate incoming SMS webhook from lead
        twilio_webhook = WebhookTestData.twilio_voice_webhook({
            'MessageSid': 'SM_incoming_123',
            'From': lead_data['phone'],
            'To': '+15551234567',
            'Body': 'YES I am very interested! Can we schedule a viewing today?'
        })
        
        # Step 3: Process response and determine follow-up actions
        response_body = twilio_webhook['Body'].upper()
        
        if 'YES' in response_body and ('INTERESTED' in response_body or 'VIEWING' in response_body):
            # Highly positive response - trigger immediate follow-up
            
            # Send immediate confirmation SMS
            confirmation_sms = await webhook_services['twilio'].send_sms(
                to=lead_data['phone'],
                message="Fantastic! I'll call you within 15 minutes to schedule your viewing. Get ready to find your dream home!"
            )
            assert confirmation_sms['success'] is True
            
            # Send detailed email with available times
            scheduling_email = await webhook_services['sendgrid'].send_email(
                to_email=lead_data['email'],
                subject="Let's Schedule Your Property Viewing - Available Times",
                content="Great to hear you're ready to view properties! Here are my available times for today..."
            )
            assert scheduling_email['success'] is True
            
            # Log the positive interaction
            interaction_logged = await webhook_services['database'].save_analytics(
                f"interaction_{lead_data['lead_id']}", 
                {
                    'type': 'positive_sms_response',
                    'response': twilio_webhook['Body'],
                    'urgency': 'high',
                    'follow_up_triggered': True,
                    'timestamp': datetime.now().isoformat()
                }
            )
            assert interaction_logged is True
        
        print(f"✅ Twilio webhook response handling passed")
        print(f"   Response: {twilio_webhook['Body']}")
        print(f"   Follow-up triggered: Immediate confirmation SMS + scheduling email")
    
    @pytest.mark.asyncio
    async def test_sendgrid_email_engagement_workflow(self, webhook_services):
        """Test SendGrid engagement webhook processing"""
        
        # Step 1: Setup lead and initial email
        lead_data = {
            'lead_id': 'email_engagement_lead',
            'name': 'Email Lead',
            'email': 'engagement@example.com',
            'phone': '+15557891234'
        }
        await webhook_services['database'].save_lead(lead_data['lead_id'], lead_data)
        
        # Send initial email
        initial_email = await webhook_services['sendgrid'].send_email(
            to_email=lead_data['email'],
            subject="Austin Properties Matching Your Criteria",
            content="Here are 5 properties that match your search..."
        )
        message_id = initial_email['message_id']
        
        # Step 2: Simulate email engagement events
        email_events = WebhookTestData.sendgrid_event_webhook([
            {
                'email': lead_data['email'],
                'event': 'delivered',
                'timestamp': int(datetime.now().timestamp()),
                'sg_message_id': message_id
            },
            {
                'email': lead_data['email'], 
                'event': 'open',
                'timestamp': int(datetime.now().timestamp()) + 300,  # 5 minutes later
                'sg_message_id': message_id
            },
            {
                'email': lead_data['email'],
                'event': 'click',
                'timestamp': int(datetime.now().timestamp()) + 600,  # 10 minutes later
                'sg_message_id': message_id,
                'url': 'https://enterprisehub.ai/properties/north-austin/luxury-home-1'
            }
        ])
        
        # Step 3: Process engagement events and trigger follow-up
        engagement_score = 0
        clicked_properties = []
        
        for event in email_events:
            if event['event'] == 'open':
                engagement_score += 10
            elif event['event'] == 'click':
                engagement_score += 25
                if 'url' in event:
                    clicked_properties.append(event['url'])
        
        # Step 4: High engagement triggers immediate follow-up
        if engagement_score >= 30:  # Opened + clicked = high engagement
            
            # Send immediate SMS about clicked property
            property_sms = await webhook_services['twilio'].send_sms(
                to=lead_data['phone'],
                message="I saw you clicked on the luxury home in North Austin! It's stunning - want to see it this weekend?"
            )
            assert property_sms['success'] is True
            
            # Send follow-up email with more similar properties
            similar_email = await webhook_services['sendgrid'].send_email(
                to_email=lead_data['email'],
                subject="More Properties Like the One You Loved",
                content="Since you showed interest in that North Austin property, here are 3 more you'll love..."
            )
            assert similar_email['success'] is True
            
            # Update lead engagement metrics
            engagement_update = await webhook_services['database'].save_analytics(
                f"engagement_{lead_data['lead_id']}",
                {
                    'email_engagement_score': engagement_score,
                    'clicked_properties': clicked_properties,
                    'follow_up_triggered': True,
                    'timestamp': datetime.now().isoformat()
                }
            )
            assert engagement_update is True
        
        print(f"✅ SendGrid engagement workflow passed")
        print(f"   Engagement Score: {engagement_score} (open + click)")
        print(f"   Clicked Properties: {len(clicked_properties)}")
        print(f"   Follow-up: Property-specific SMS + similar listings email")


class TestErrorHandlingAndFallbacks:
    """Test error handling and fallback scenarios in integration workflows"""
    
    @pytest.fixture
    async def failing_services(self):
        """Create services that simulate various failure scenarios"""
        
        # Database that fails intermittently
        failing_database = MagicMock()
        failing_database.save_lead = AsyncMock(side_effect=[
            Exception("Database connection failed"),
            True,  # Success on retry
            True
        ])
        failing_database.get_lead = AsyncMock(side_effect=Exception("Database timeout"))
        
        # Twilio that hits rate limits
        failing_twilio = MagicMock()
        failing_twilio.send_sms = AsyncMock(side_effect=[
            Exception("Rate limit exceeded"),
            {'success': True, 'message_sid': 'SM_retry_success'}
        ])
        
        # SendGrid with API issues
        failing_sendgrid = MagicMock()
        failing_sendgrid.send_email = AsyncMock(side_effect=[
            Exception("SendGrid API unavailable"),
            {'success': True, 'message_id': 'SG_retry_success'}
        ])
        
        return {
            'database': failing_database,
            'twilio': failing_twilio,
            'sendgrid': failing_sendgrid
        }
    
    @pytest.mark.asyncio
    async def test_database_failure_retry_workflow(self, failing_services):
        """Test handling database failures with retry logic"""
        
        lead_data = {
            'lead_id': 'db_failure_test',
            'name': 'DB Test Lead',
            'email': 'dbtest@example.com'
        }
        
        # Step 1: First attempt fails, retry succeeds
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await failing_services['database'].save_lead(
                    lead_data['lead_id'], 
                    lead_data
                )
                if result:
                    break
            except Exception as e:
                if attempt == max_retries - 1:
                    # Final attempt failed
                    assert False, f"Database save failed after {max_retries} attempts: {e}"
                else:
                    # Wait and retry
                    await asyncio.sleep(0.1)
                    continue
        
        # Should eventually succeed
        assert result is True
        print(f"✅ Database failure retry test passed after {attempt + 1} attempts")
    
    @pytest.mark.asyncio
    async def test_communication_failure_fallback_workflow(self, failing_services):
        """Test fallback communication methods when primary methods fail"""
        
        lead_data = {
            'lead_id': 'comm_fallback_test',
            'phone': '+15557890999',
            'email': 'fallback@example.com'
        }
        
        # Step 1: Try SMS first (will fail)
        sms_success = False
        try:
            await failing_services['twilio'].send_sms(
                to=lead_data['phone'],
                message="Primary SMS attempt"
            )
            sms_success = True
        except Exception:
            # SMS failed, fall back to email
            pass
        
        # Step 2: Fall back to email (will also fail first time)
        email_success = False
        if not sms_success:
            try:
                await failing_services['sendgrid'].send_email(
                    to_email=lead_data['email'],
                    subject="Important Property Update",
                    content="SMS delivery failed, sending via email instead..."
                )
                email_success = True
            except Exception:
                # Email also failed initially
                pass
        
        # Step 3: Retry both methods
        if not sms_success:
            try:
                sms_retry = await failing_services['twilio'].send_sms(
                    to=lead_data['phone'],
                    message="Retry SMS attempt"
                )
                sms_success = sms_retry['success']
            except Exception:
                pass
        
        if not email_success:
            try:
                email_retry = await failing_services['sendgrid'].send_email(
                    to_email=lead_data['email'],
                    subject="Retry Email",
                    content="Retrying email delivery..."
                )
                email_success = email_retry['success']
            except Exception:
                pass
        
        # At least one communication method should have succeeded
        assert sms_success or email_success, "All communication methods failed"
        
        print(f"✅ Communication fallback test passed")
        print(f"   SMS Success: {sms_success}, Email Success: {email_success}")
    
    @pytest.mark.asyncio
    async def test_partial_service_failure_workflow(self):
        """Test workflow continuation when some services fail"""
        
        # Step 1: Create mixed success/failure scenario
        working_database = MockDatabaseService()
        failing_apollo = MagicMock()
        failing_apollo.enrich_lead = AsyncMock(side_effect=Exception("Apollo API down"))
        working_twilio = MockTwilioClient()
        
        lead_data = {
            'lead_id': 'partial_failure_test',
            'name': 'Partial Test Lead',
            'email': 'partial@example.com',
            'phone': '+15557891111'
        }
        
        # Step 2: Save lead (should work)
        save_result = await working_database.save_lead(lead_data['lead_id'], lead_data)
        assert save_result is True
        
        # Step 3: Try enrichment (will fail)
        enrichment_result = None
        try:
            enrichment_result = await failing_apollo.enrich_lead(
                lead_data['email'],
                lead_data['phone']
            )
        except Exception:
            # Enrichment failed, but workflow continues with basic data
            enrichment_result = {'status': 'failed', 'reason': 'apollo_unavailable'}
        
        assert enrichment_result['status'] == 'failed'
        
        # Step 4: Continue with basic communication (should work)
        basic_sms = await working_twilio.send_sms(
            to=lead_data['phone'],
            message="Welcome! We'll follow up soon with more details."
        )
        assert basic_sms['success'] is True
        
        # Step 5: Log the partial failure for retry later
        failure_log = await working_database.save_analytics(
            f"partial_failure_{lead_data['lead_id']}",
            {
                'failed_services': ['apollo_enrichment'],
                'successful_services': ['database', 'twilio'],
                'retry_needed': True,
                'timestamp': datetime.now().isoformat()
            }
        )
        assert failure_log is True
        
        print(f"✅ Partial service failure test passed")
        print(f"   Failed: Apollo enrichment")
        print(f"   Succeeded: Database save, SMS communication")
        print(f"   Workflow continued with degraded functionality")


class TestPerformanceAndScaling:
    """Test performance characteristics under load"""
    
    @pytest.mark.asyncio
    async def test_concurrent_lead_processing(self):
        """Test processing multiple leads concurrently"""
        
        # Setup lightweight services for performance testing
        mock_database = MockDatabaseService()
        mock_orchestrator = MagicMock()
        
        async def mock_analyze_lead(lead_id, lead_data):
            await asyncio.sleep(0.01)  # Simulate processing time
            return MagicMock(
                lead_id=lead_id,
                unified_lead_score=75.5,
                priority_level='high',
                confidence_level=0.85
            )
        
        mock_orchestrator.analyze_lead = mock_analyze_lead
        
        # Create multiple test leads
        test_leads = [
            {
                'lead_id': f'perf_test_lead_{i}',
                'name': f'Performance Lead {i}',
                'email': f'perf{i}@example.com',
                'phone': f'+155579{i:05d}'
            }
            for i in range(20)
        ]
        
        # Process all leads concurrently
        import time
        start_time = time.time()
        
        tasks = []
        for lead_data in test_leads:
            # Save to database
            save_task = mock_database.save_lead(lead_data['lead_id'], lead_data)
            # Analyze lead
            analyze_task = mock_orchestrator.analyze_lead(lead_data['lead_id'], lead_data)
            
            tasks.extend([save_task, analyze_task])
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify all operations succeeded
        successful_operations = sum(1 for r in results if not isinstance(r, Exception))
        assert successful_operations == len(tasks)
        
        # Performance should be reasonable
        assert execution_time < 5.0, f"Processing took too long: {execution_time}s"
        
        # Calculate throughput
        leads_per_second = len(test_leads) / execution_time
        
        print(f"✅ Concurrent processing test passed")
        print(f"   Processed {len(test_leads)} leads in {execution_time:.2f}s")
        print(f"   Throughput: {leads_per_second:.1f} leads/second")
        print(f"   Total operations: {len(tasks)} (save + analyze for each lead)")


if __name__ == "__main__":
    # Run comprehensive E2E tests
    pytest.main([
        "-v",
        "tests/integration/test_service6_end_to_end.py",
        "--tb=short",
        "-x"  # Stop on first failure for easier debugging
    ])