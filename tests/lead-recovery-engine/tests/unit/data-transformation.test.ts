/**
 * Unit tests for Data Transformation Service
 * Tests: 25 tests covering data mapping and transformation logic
 */

import { DataTransformationService } from '../../src/services/data-transformation.service';
import { Lead, EnrichmentData, CommunicationRecord } from '../../src/types/lead.interface';
import { LeadFactory } from '../factories/lead.factory';
import { ExternalAPIMocks } from '../mocks/external-apis.mock';

describe('DataTransformationService', () => {
  describe('transformWebhookData', () => {
    test('should transform standard webhook data correctly', () => {
      const webhookData = {
        email: 'john.doe@company.com',
        firstName: 'John',
        lastName: 'Doe',
        phone: '(555) 123-4567',
        company: 'TechCorp',
        jobTitle: 'VP Sales'
      };

      const result = DataTransformationService.transformWebhookData(webhookData, 'website');

      expect(result.email).toBe('john.doe@company.com');
      expect(result.firstName).toBe('John');
      expect(result.lastName).toBe('Doe');
      expect(result.phone).toBe('(555) 123-4567');
      expect(result.company).toBe('TechCorp');
      expect(result.jobTitle).toBe('VP Sales');
      expect(result.source).toBe('website');
      expect(result.dataQuality).toBe('basic');
    });

    test('should handle alternate field name formats', () => {
      const webhookData = {
        email_address: 'test@example.com',
        first_name: 'Jane',
        last_name: 'Smith',
        phone_number: '555-987-6543',
        company_name: 'StartupInc',
        job_title: 'CEO'
      };

      const result = DataTransformationService.transformWebhookData(webhookData, 'linkedin');

      expect(result.email).toBe('test@example.com');
      expect(result.firstName).toBe('Jane');
      expect(result.lastName).toBe('Smith');
      expect(result.phone).toBe('555-987-6543');
      expect(result.company).toBe('StartupInc');
      expect(result.jobTitle).toBe('CEO');
      expect(result.source).toBe('linkedin');
    });

    test('should split full name when separate names not available', () => {
      const webhookData = {
        email: 'user@domain.com',
        fullName: 'Michael Johnson Jr.',
        company: 'Enterprise Corp'
      };

      const result = DataTransformationService.transformWebhookData(webhookData, 'webinar');

      expect(result.firstName).toBe('Michael');
      expect(result.lastName).toBe('Johnson Jr.');
    });

    test('should handle single name gracefully', () => {
      const webhookData = {
        email: 'user@domain.com',
        name: 'Madonna'
      };

      const result = DataTransformationService.transformWebhookData(webhookData, 'contact_form');

      expect(result.firstName).toBe('Madonna');
      expect(result.lastName).toBe('');
    });

    test('should extract custom fields correctly', () => {
      const webhookData = {
        email: 'user@domain.com',
        firstName: 'John',
        lastName: 'Doe',
        utm_source: 'google',
        utm_campaign: 'summer2024',
        lead_interest: 'enterprise_plan',
        budget_range: '$10k-$50k'
      };

      const result = DataTransformationService.transformWebhookData(webhookData, 'landing_page');

      expect(result.customFields).toEqual({
        utm_source: 'google',
        utm_campaign: 'summer2024',
        lead_interest: 'enterprise_plan',
        budget_range: '$10k-$50k'
      });
    });

    test('should handle missing fields gracefully', () => {
      const incompleteData = {
        email: 'incomplete@example.com'
        // Missing other required fields
      };

      const result = DataTransformationService.transformWebhookData(incompleteData, 'unknown');

      expect(result.email).toBe('incomplete@example.com');
      expect(result.firstName).toBeUndefined();
      expect(result.lastName).toBeUndefined();
      expect(result.source).toBe('unknown');
    });

    test('should set timestamps correctly', () => {
      const webhookData = { email: 'test@example.com' };
      const beforeTransform = new Date();
      
      const result = DataTransformationService.transformWebhookData(webhookData, 'test');
      const afterTransform = new Date();

      expect(result.createdAt).toBeInstanceOf(Date);
      expect(result.updatedAt).toBeInstanceOf(Date);
      expect(result.lastActivity).toBeInstanceOf(Date);
      expect(result.createdAt!.getTime()).toBeGreaterThanOrEqual(beforeTransform.getTime());
      expect(result.createdAt!.getTime()).toBeLessThanOrEqual(afterTransform.getTime());
    });
  });

  describe('enrichLeadData', () => {
    test('should enrich lead with Apollo data', () => {
      const lead = LeadFactory.createValidLead();
      const enrichmentData = ExternalAPIMocks.generateMockEnrichmentData();

      const enriched = DataTransformationService.enrichLeadData(lead, enrichmentData);

      expect(enriched.dataQuality).toBe('enriched');
      expect(enriched.linkedinUrl).toBe('https://linkedin.com/in/johndoe');
      expect(enriched.jobTitle).toBe('VP Sales');
      expect(enriched.seniority).toBe('VP');
      expect(enriched.companyIndustry).toBe('Technology');
      expect(enriched.companySize).toBe(500);
      expect(enriched.companyRevenue).toBe(50000000);
      expect(enriched.apolloId).toContain('apollo_');
    });

    test('should preserve existing data when enriching', () => {
      const lead = LeadFactory.createValidLead({
        email: 'original@company.com',
        firstName: 'Original',
        leadScore: 75
      });

      const enrichmentData = ExternalAPIMocks.generateMockEnrichmentData();

      const enriched = DataTransformationService.enrichLeadData(lead, enrichmentData);

      expect(enriched.email).toBe('original@company.com');
      expect(enriched.firstName).toBe('Original');
      expect(enriched.leadScore).toBe(75);
    });

    test('should handle partial enrichment data', () => {
      const lead = LeadFactory.createValidLead();
      const partialEnrichment: EnrichmentData = {
        source: 'clearbit',
        confidence: 0.8,
        data: {
          personal: {
            jobTitle: 'Senior Manager'
          }
          // Missing company data
        },
        enrichedAt: new Date()
      };

      const enriched = DataTransformationService.enrichLeadData(lead, partialEnrichment);

      expect(enriched.jobTitle).toBe('Senior Manager');
      expect(enriched.companyIndustry).toBeUndefined();
    });

    test('should update timestamps when enriching', () => {
      const lead = LeadFactory.createValidLead();
      const originalUpdatedAt = lead.updatedAt;
      
      // Wait a bit to ensure timestamp difference
      await new Promise(resolve => setTimeout(resolve, 1));

      const enrichmentData = ExternalAPIMocks.generateMockEnrichmentData();
      const enriched = DataTransformationService.enrichLeadData(lead, enrichmentData);

      expect(enriched.updatedAt!.getTime()).toBeGreaterThan(originalUpdatedAt.getTime());
    });
  });

  describe('normalizeCRMData', () => {
    test('should normalize HubSpot data format', () => {
      const hubspotData = {
        properties: {
          email: 'hubspot@example.com',
          firstname: 'Hub',
          lastname: 'Spot',
          phone: '555-0123',
          company: 'HubSpot Corp',
          jobtitle: 'Marketing Manager'
        }
      };

      const result = DataTransformationService.normalizeCRMData(hubspotData, 'hubspot');

      expect(result.email).toBe('hubspot@example.com');
      expect(result.firstName).toBe('Hub');
      expect(result.lastName).toBe('Spot');
      expect(result.phone).toBe('555-0123');
      expect(result.company).toBe('HubSpot Corp');
      expect(result.jobTitle).toBe('Marketing Manager');
      expect(result.source).toBe('hubspot');
      expect(result.dataQuality).toBe('enriched');
    });

    test('should normalize Salesforce data format', () => {
      const salesforceData = {
        Email: 'sf@example.com',
        FirstName: 'Sales',
        LastName: 'Force',
        Phone: '555-0456',
        Company: 'Salesforce Inc',
        Title: 'Sales Rep'
      };

      const result = DataTransformationService.normalizeCRMData(salesforceData, 'salesforce');

      expect(result.email).toBe('sf@example.com');
      expect(result.firstName).toBe('Sales');
      expect(result.lastName).toBe('Force');
      expect(result.source).toBe('salesforce');
    });

    test('should normalize GoHighLevel data format', () => {
      const ghlData = {
        email: 'ghl@example.com',
        firstName: 'Go',
        lastName: 'High',
        phone: '555-0789',
        companyName: 'GHL Corp'
      };

      const result = DataTransformationService.normalizeCRMData(ghlData, 'ghl');

      expect(result.email).toBe('ghl@example.com');
      expect(result.firstName).toBe('Go');
      expect(result.lastName).toBe('High');
      expect(result.company).toBe('GHL Corp');
      expect(result.source).toBe('ghl');
    });

    test('should throw error for unsupported CRM type', () => {
      const data = { email: 'test@example.com' };

      expect(() => {
        DataTransformationService.normalizeCRMData(data, 'unknown' as any);
      }).toThrow('Unsupported CRM type: unknown');
    });
  });

  describe('transformCommunicationData', () => {
    test('should generate communication summary', () => {
      const communications: CommunicationRecord[] = [
        LeadFactory.createCommunicationRecord('lead123', {
          channel: 'email',
          direction: 'outbound',
          status: 'delivered',
          openedAt: new Date()
        }),
        LeadFactory.createCommunicationRecord('lead123', {
          channel: 'email',
          direction: 'outbound',
          status: 'delivered',
          openedAt: new Date(),
          clickedAt: new Date()
        }),
        LeadFactory.createCommunicationRecord('lead123', {
          channel: 'sms',
          direction: 'outbound',
          status: 'sent'
        }),
        LeadFactory.createCommunicationRecord('lead123', {
          channel: 'email',
          direction: 'inbound',
          status: 'delivered',
          repliedAt: new Date()
        })
      ];

      const summary = DataTransformationService.transformCommunicationData(communications);

      expect(summary.totalCommunications).toBe(4);
      expect(summary.byChannel.email).toBe(3);
      expect(summary.byChannel.sms).toBe(1);
      expect(summary.byDirection.outbound).toBe(3);
      expect(summary.byDirection.inbound).toBe(1);
      expect(summary.engagementMetrics.opens).toBe(2);
      expect(summary.engagementMetrics.clicks).toBe(1);
      expect(summary.engagementMetrics.replies).toBe(1);
      expect(summary.engagementMetrics.deliveryRate).toBe(1.0); // All were delivered
    });

    test('should handle empty communication list', () => {
      const summary = DataTransformationService.transformCommunicationData([]);

      expect(summary.totalCommunications).toBe(0);
      expect(summary.engagementMetrics.deliveryRate).toBe(0);
    });

    test('should calculate delivery rate correctly', () => {
      const communications: CommunicationRecord[] = [
        LeadFactory.createCommunicationRecord('lead123', { status: 'delivered' }),
        LeadFactory.createCommunicationRecord('lead123', { status: 'delivered' }),
        LeadFactory.createCommunicationRecord('lead123', { status: 'failed' }),
        LeadFactory.createCommunicationRecord('lead123', { status: 'bounced' })
      ];

      const summary = DataTransformationService.transformCommunicationData(communications);

      expect(summary.engagementMetrics.deliveryRate).toBe(0.5); // 2 out of 4 delivered
    });
  });

  describe('mergeLeadRecords', () => {
    test('should merge two lead records correctly', () => {
      const primaryLead = LeadFactory.createValidLead({
        email: 'primary@example.com',
        firstName: 'Primary',
        lastName: 'Lead',
        phone: '+15551234567',
        company: 'Primary Corp',
        dataQuality: 'basic'
      }) as Lead;

      const duplicateLead = LeadFactory.createValidLead({
        email: 'duplicate@example.com', // Different email
        firstName: 'Duplicate',
        lastName: 'Lead',
        jobTitle: 'VP Sales', // Additional data
        companySize: 1000, // Additional data
        dataQuality: 'enriched', // Higher quality
        tags: ['premium', 'enterprise']
      }) as Lead;

      const merged = DataTransformationService.mergeLeadRecords(primaryLead, duplicateLead);

      // Primary data should be preserved
      expect(merged.email).toBe('primary@example.com');
      expect(merged.firstName).toBe('Primary');

      // Missing data should be filled from duplicate
      expect(merged.jobTitle).toBe('VP Sales');
      expect(merged.companySize).toBe(1000);

      // Higher quality data should be used
      expect(merged.dataQuality).toBe('enriched');

      // Tags should be merged
      expect(merged.tags).toContain('premium');
      expect(merged.tags).toContain('enterprise');
    });

    test('should handle partial data in both records', () => {
      const lead1 = LeadFactory.createValidLead({
        firstName: 'John',
        email: 'john@example.com'
      }) as Lead;

      const lead2 = LeadFactory.createValidLead({
        lastName: 'Doe',
        phone: '+15555551234',
        company: 'Example Corp'
      }) as Lead;

      const merged = DataTransformationService.mergeLeadRecords(lead1, lead2);

      expect(merged.firstName).toBe('John');
      expect(merged.lastName).toBe('Doe');
      expect(merged.email).toBe('john@example.com');
      expect(merged.phone).toBe('+15555551234');
      expect(merged.company).toBe('Example Corp');
    });

    test('should merge custom fields', () => {
      const lead1 = LeadFactory.createValidLead({
        customFields: { source: 'website', campaign: 'summer2024' }
      }) as Lead;

      const lead2 = LeadFactory.createValidLead({
        customFields: { utm_source: 'google', budget: '$10k' }
      }) as Lead;

      const merged = DataTransformationService.mergeLeadRecords(lead1, lead2);

      expect(merged.customFields).toEqual({
        source: 'website',
        campaign: 'summer2024',
        utm_source: 'google',
        budget: '$10k'
      });
    });

    test('should update timestamp on merge', () => {
      const lead1 = LeadFactory.createValidLead() as Lead;
      const lead2 = LeadFactory.createValidLead() as Lead;
      const beforeMerge = new Date();

      const merged = DataTransformationService.mergeLeadRecords(lead1, lead2);

      expect(merged.updatedAt.getTime()).toBeGreaterThanOrEqual(beforeMerge.getTime());
    });
  });

  describe('validateTransformation', () => {
    test('should validate successful transformation', () => {
      const original = {
        email: 'test@example.com',
        firstName: 'John',
        lastName: 'Doe',
        phone: '555-1234567'
      };

      const transformed = {
        email: 'test@example.com',
        firstName: 'John',
        lastName: 'Doe',
        phone: '+15551234567'
      };

      const result = DataTransformationService.validateTransformation(original, transformed);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    test('should detect lost email during transformation', () => {
      const original = {
        email: 'test@example.com',
        firstName: 'John'
      };

      const transformed = {
        firstName: 'John'
        // Email missing
      };

      const result = DataTransformationService.validateTransformation(original, transformed);

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Email lost during transformation');
    });

    test('should warn about lost names', () => {
      const original = {
        email: 'test@example.com',
        first_name: 'John',
        last_name: 'Doe'
      };

      const transformed = {
        email: 'test@example.com'
        // Names missing
      };

      const result = DataTransformationService.validateTransformation(original, transformed);

      expect(result.warnings).toContain('First name lost during transformation');
      expect(result.warnings).toContain('Last name lost during transformation');
    });

    test('should detect invalid email format after transformation', () => {
      const original = {
        email: 'test@example.com'
      };

      const transformed = {
        email: 'invalid-email-format'
      };

      const result = DataTransformationService.validateTransformation(original, transformed);

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain('Invalid email format after transformation');
    });

    test('should warn about incomplete phone transformation', () => {
      const original = {
        email: 'test@example.com',
        phone: '555-123-4567'
      };

      const transformed = {
        email: 'test@example.com',
        phone: '555'
      };

      const result = DataTransformationService.validateTransformation(original, transformed);

      expect(result.warnings).toContain('Phone number may be incomplete after transformation');
    });
  });

  describe('Performance Tests', () => {
    test('should transform webhook data efficiently', () => {
      const webhookData = {
        email: 'perf@example.com',
        firstName: 'Performance',
        lastName: 'Test',
        company: 'Speed Corp'
      };

      const startTime = Date.now();
      DataTransformationService.transformWebhookData(webhookData, 'performance');
      const executionTime = Date.now() - startTime;

      expect(executionTime).toBeLessThan(5);
    });

    test('should handle large communication datasets efficiently', () => {
      const communications = Array.from({ length: 1000 }, (_, i) => 
        LeadFactory.createCommunicationRecord(`lead_${i}`)
      );

      const startTime = Date.now();
      DataTransformationService.transformCommunicationData(communications);
      const executionTime = Date.now() - startTime;

      expect(executionTime).toBeLessThan(50); // Should complete in under 50ms
    });
  });

  describe('Edge Cases', () => {
    test('should handle null and undefined values gracefully', () => {
      const problematicData = {
        email: null,
        firstName: undefined,
        lastName: '',
        phone: null,
        company: undefined
      };

      expect(() => {
        DataTransformationService.transformWebhookData(problematicData as any, 'test');
      }).not.toThrow();
    });

    test('should handle very long field values', () => {
      const longData = {
        email: 'test@example.com',
        firstName: 'A'.repeat(1000),
        notes: 'B'.repeat(10000)
      };

      const result = DataTransformationService.transformWebhookData(longData, 'test');

      expect(result.firstName).toBe('A'.repeat(1000));
      expect(result.customFields?.notes).toBe('B'.repeat(10000));
    });

    test('should handle malformed data types', () => {
      const malformedData = {
        email: 123,
        firstName: true,
        lastName: [],
        phone: {}
      };

      const result = DataTransformationService.transformWebhookData(malformedData as any, 'test');

      // Should not crash, but invalid data should not be included
      expect(result.email).toBeNull();
      expect(result.firstName).toBeNull();
      expect(result.lastName).toBeNull();
      expect(result.phone).toBeNull();
    });
  });
});