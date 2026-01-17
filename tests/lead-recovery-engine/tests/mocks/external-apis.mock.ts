/**
 * Mock implementations for external API services
 * Provides realistic mock responses for testing
 */

import nock from 'nock';
import { EnrichmentData } from '../../src/types/lead.interface';

export class ExternalAPIMocks {
  static setupApolloMocks() {
    // Apollo.io API mock
    nock('https://api.apollo.io')
      .persist()
      .post('/v1/people/search')
      .reply(200, {
        people: [{
          id: 'apollo_123',
          email: 'test@example.com',
          first_name: 'John',
          last_name: 'Doe',
          title: 'VP Sales',
          linkedin_url: 'https://linkedin.com/in/johndoe',
          organization: {
            name: 'TechCorp',
            industry: 'Technology',
            size: 500,
            website_url: 'https://techcorp.com'
          }
        }]
      });

    nock('https://api.apollo.io')
      .persist()
      .post('/v1/people/enrich')
      .reply(200, {
        person: {
          id: 'apollo_123',
          email: 'test@example.com',
          first_name: 'John',
          last_name: 'Doe',
          title: 'VP Sales',
          seniority: 'VP',
          linkedin_url: 'https://linkedin.com/in/johndoe',
          organization: {
            name: 'TechCorp',
            industry: 'Technology',
            estimated_num_employees: 500,
            website_url: 'https://techcorp.com'
          }
        }
      });

    // Apollo rate limiting mock
    nock('https://api.apollo.io')
      .post('/v1/people/search')
      .query({ test_rate_limit: 'true' })
      .reply(429, { 
        error: 'Rate limit exceeded',
        retry_after: 60
      });

    // Apollo error mock
    nock('https://api.apollo.io')
      .post('/v1/people/search')
      .query({ test_error: 'true' })
      .reply(500, { error: 'Internal server error' });
  }

  static setupTwilioMocks() {
    // Twilio SMS API mock
    nock('https://api.twilio.com')
      .persist()
      .post('/2010-04-01/Accounts/test-twilio-sid/Messages.json')
      .reply(201, {
        sid: 'SM123456789',
        status: 'sent',
        to: '+15551234567',
        from: '+15559876543',
        body: 'Test message',
        date_created: new Date().toISOString()
      });

    // Twilio call API mock
    nock('https://api.twilio.com')
      .persist()
      .post('/2010-04-01/Accounts/test-twilio-sid/Calls.json')
      .reply(201, {
        sid: 'CA123456789',
        status: 'ringing',
        to: '+15551234567',
        from: '+15559876543',
        date_created: new Date().toISOString()
      });

    // Twilio webhook status update mock
    nock('https://api.twilio.com')
      .persist()
      .get('/2010-04-01/Accounts/test-twilio-sid/Messages/SM123456789.json')
      .reply(200, {
        sid: 'SM123456789',
        status: 'delivered',
        to: '+15551234567',
        from: '+15559876543',
        date_sent: new Date().toISOString()
      });
  }

  static setupSendGridMocks() {
    // SendGrid email API mock
    nock('https://api.sendgrid.com')
      .persist()
      .post('/v3/mail/send')
      .reply(202, { message: 'Email queued for delivery' });

    // SendGrid webhook event mock
    nock('https://api.sendgrid.com')
      .persist()
      .post('/webhook/sendgrid')
      .reply(200, [
        {
          event: 'delivered',
          email: 'test@example.com',
          timestamp: Math.floor(Date.now() / 1000),
          smtp_id: 'sg123456789'
        }
      ]);

    // SendGrid template API mock
    nock('https://api.sendgrid.com')
      .persist()
      .get('/v3/templates')
      .reply(200, {
        templates: [
          {
            id: 'template_123',
            name: 'Lead Response Template',
            generation: 'dynamic'
          }
        ]
      });
  }

  static setupGoHighLevelMocks() {
    // GHL contacts API mock
    nock('https://services.leadconnectorhq.com')
      .persist()
      .post('/contacts/')
      .reply(201, {
        contact: {
          id: 'ghl_contact_123',
          email: 'test@example.com',
          firstName: 'John',
          lastName: 'Doe',
          phone: '+15551234567',
          tags: ['new-lead']
        }
      });

    // GHL workflow trigger mock
    nock('https://services.leadconnectorhq.com')
      .persist()
      .post('/workflows/trigger')
      .reply(200, {
        success: true,
        workflow_id: 'workflow_123',
        execution_id: 'exec_123'
      });

    // GHL opportunity creation mock
    nock('https://services.leadconnectorhq.com')
      .persist()
      .post('/opportunities/')
      .reply(201, {
        opportunity: {
          id: 'opp_123',
          name: 'New Lead Opportunity',
          contact_id: 'ghl_contact_123',
          pipeline_id: 'pipeline_123',
          stage_id: 'stage_123',
          monetary_value: 5000
        }
      });
  }

  static setupHubSpotMocks() {
    // HubSpot contacts API mock
    nock('https://api.hubapi.com')
      .persist()
      .post('/crm/v3/objects/contacts')
      .reply(201, {
        id: 'hubspot_contact_123',
        properties: {
          email: 'test@example.com',
          firstname: 'John',
          lastname: 'Doe',
          phone: '+15551234567',
          lifecyclestage: 'lead'
        }
      });

    // HubSpot deal creation mock
    nock('https://api.hubapi.com')
      .persist()
      .post('/crm/v3/objects/deals')
      .reply(201, {
        id: 'hubspot_deal_123',
        properties: {
          dealname: 'New Lead Deal',
          amount: 5000,
          dealstage: 'qualifiedtobuy'
        }
      });
  }

  static setupN8NMocks() {
    // n8n webhook trigger mock
    nock('http://localhost:5678')
      .persist()
      .post('/webhook/lead-capture')
      .reply(200, {
        success: true,
        execution_id: 'n8n_exec_123',
        message: 'Workflow triggered successfully'
      });

    // n8n workflow status mock
    nock('http://localhost:5678')
      .persist()
      .get('/api/v1/executions/n8n_exec_123')
      .reply(200, {
        data: {
          id: 'n8n_exec_123',
          mode: 'webhook',
          status: 'success',
          startedAt: new Date().toISOString(),
          stoppedAt: new Date().toISOString(),
          workflowData: {}
        }
      });
  }

  static setupAllMocks() {
    this.setupApolloMocks();
    this.setupTwilioMocks();
    this.setupSendGridMocks();
    this.setupGoHighLevelMocks();
    this.setupHubSpotMocks();
    this.setupN8NMocks();
  }

  static cleanAllMocks() {
    nock.cleanAll();
  }

  static generateMockEnrichmentData(): EnrichmentData {
    return {
      source: 'apollo',
      confidence: 0.95,
      data: {
        personal: {
          linkedinUrl: 'https://linkedin.com/in/johndoe',
          jobTitle: 'VP Sales',
          seniority: 'VP',
          skills: ['Sales', 'Business Development', 'Lead Generation']
        },
        company: {
          name: 'TechCorp',
          industry: 'Technology',
          size: 500,
          revenue: 50000000,
          website: 'https://techcorp.com',
          linkedinUrl: 'https://linkedin.com/company/techcorp',
          technologies: ['JavaScript', 'Python', 'AWS']
        }
      },
      enrichedAt: new Date()
    };
  }
}

// Helper class for mock response builders
export class MockResponseBuilder {
  static apolloPersonResponse(overrides: any = {}) {
    return {
      person: {
        id: 'apollo_123',
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe',
        title: 'VP Sales',
        linkedin_url: 'https://linkedin.com/in/johndoe',
        ...overrides
      }
    };
  }

  static twilioMessageResponse(overrides: any = {}) {
    return {
      sid: 'SM123456789',
      status: 'sent',
      to: '+15551234567',
      from: '+15559876543',
      body: 'Test message',
      date_created: new Date().toISOString(),
      ...overrides
    };
  }

  static ghlContactResponse(overrides: any = {}) {
    return {
      contact: {
        id: 'ghl_contact_123',
        email: 'test@example.com',
        firstName: 'John',
        lastName: 'Doe',
        phone: '+15551234567',
        tags: ['new-lead'],
        ...overrides
      }
    };
  }
}