/**
 * Unit tests for Business Rules Service
 * Tests: 30 tests covering business logic validation
 */

import { BusinessRulesService, BusinessRuleContext } from '../../src/services/business-rules.service';
import { Lead, LeadTemperature } from '../../src/types/lead.interface';
import { LeadFactory } from '../factories/lead.factory';

describe('BusinessRulesService', () => {
  describe('validateLead', () => {
    test('should validate complete, high-quality lead', () => {
      const lead = LeadFactory.createLeadWithEnrichment({
        email: 'ceo@techcorp.com',
        firstName: 'John',
        lastName: 'Doe',
        company: 'TechCorp Inc',
        jobTitle: 'CEO',
        leadScore: 85,
        companySize: 1000,
        companyRevenue: 50000000
      });

      const results = BusinessRulesService.validateLead(lead);
      
      const errors = results.filter(r => r.severity === 'error');
      expect(errors).toHaveLength(0);
      
      const passed = results.filter(r => r.isValid);
      expect(passed.length).toBeGreaterThan(0);
    });

    test('should identify missing required fields', () => {
      const incompleteLead = {
        email: 'test@example.com'
        // Missing firstName, lastName
      };

      const results = BusinessRulesService.validateLead(incompleteLead);
      
      const completenessResult = results.find(r => r.message.includes('Missing required fields'));
      expect(completenessResult).toBeDefined();
      expect(completenessResult?.isValid).toBe(false);
      expect(completenessResult?.severity).toBe('error');
      expect(completenessResult?.message).toContain('firstName');
      expect(completenessResult?.message).toContain('lastName');
    });

    test('should validate lead quality based on available data', () => {
      const lowQualityLead = {
        email: 'user@gmail.com', // Generic domain
        firstName: 'John',
        lastName: 'Doe'
        // Missing company, job title
      };

      const results = BusinessRulesService.validateLead(lowQualityLead);
      
      const qualityResult = results.find(r => r.message.includes('Lead quality score'));
      expect(qualityResult).toBeDefined();
      expect(qualityResult?.metadata?.issues).toContain('Generic email domain');
      expect(qualityResult?.metadata?.issues).toContain('Missing or insufficient company information');
    });

    test('should validate high-quality lead data', () => {
      const highQualityLead = {
        email: 'ceo@company.com', // Corporate domain
        firstName: 'Jane',
        lastName: 'Smith',
        company: 'Enterprise Corp',
        jobTitle: 'Chief Executive Officer',
        phone: '+15551234567'
      };

      const results = BusinessRulesService.validateLead(highQualityLead);
      
      const qualityResult = results.find(r => r.message.includes('Lead quality score'));
      expect(qualityResult?.isValid).toBe(true);
      expect(qualityResult?.metadata?.qualityScore).toBeGreaterThan(40);
    });

    test('should detect duplicate leads', () => {
      const duplicateLead = {
        email: 'duplicate@example.com', // Contains 'duplicate' keyword
        firstName: 'John',
        lastName: 'Doe'
      };

      const results = BusinessRulesService.validateLead(duplicateLead);
      
      const duplicateResult = results.find(r => r.message.includes('duplicate'));
      expect(duplicateResult?.isValid).toBe(false);
      expect(duplicateResult?.severity).toBe('warning');
    });

    test('should validate lead scoring', () => {
      const invalidScoreLead = {
        email: 'test@example.com',
        firstName: 'John',
        lastName: 'Doe',
        leadScore: 150 // Invalid score
      };

      const results = BusinessRulesService.validateLead(invalidScoreLead);
      
      const scoreResult = results.find(r => r.message.includes('Invalid lead score'));
      expect(scoreResult?.isValid).toBe(false);
      expect(scoreResult?.severity).toBe('error');
    });

    test('should validate enterprise lead requirements', () => {
      const enterpriseLead = {
        email: 'user@bigcorp.com',
        firstName: 'John',
        lastName: 'Doe',
        company: 'BigCorp',
        jobTitle: 'Junior Developer', // Not senior enough for enterprise
        companySize: 5000, // Enterprise size
        companyRevenue: 200000000 // Enterprise revenue
      };

      const results = BusinessRulesService.validateLead(enterpriseLead);
      
      const enterpriseResult = results.find(r => r.message.includes('Enterprise lead without senior'));
      expect(enterpriseResult?.isValid).toBe(false);
      expect(enterpriseResult?.severity).toBe('warning');
    });

    test('should validate source-specific rules for referrals', () => {
      const referralLead = LeadFactory.createValidLead({
        source: 'referral'
        // Missing referrer info
      });

      const results = BusinessRulesService.validateLead(referralLead);
      
      const sourceResult = results.find(r => r.message.includes('Referral lead missing referrer'));
      expect(sourceResult?.isValid).toBe(false);
      expect(sourceResult?.severity).toBe('warning');
    });

    test('should validate business hours context', () => {
      const lead = LeadFactory.createValidLead();
      const context: Partial<BusinessRuleContext> = {
        businessHours: false // Outside business hours
      };

      const results = BusinessRulesService.validateLead(lead, context);
      
      const hoursResult = results.find(r => r.message.includes('outside business hours'));
      expect(hoursResult?.isValid).toBe(true); // Valid but informational
      expect(hoursResult?.severity).toBe('info');
    });

    test('should flag urgent leads outside business hours', () => {
      const urgentLead = LeadFactory.createHighScoreLead({
        temperature: 'hot' as LeadTemperature,
        leadScore: 95
      });
      
      const context: Partial<BusinessRuleContext> = {
        businessHours: false
      };

      const results = BusinessRulesService.validateLead(urgentLead, context);
      
      const hoursResult = results.find(r => r.message.includes('high priority lead detected'));
      expect(hoursResult?.severity).toBe('warning');
    });
  });

  describe('validateResponseSLA', () => {
    test('should validate hot lead response within SLA', () => {
      const leadCreatedAt = new Date('2024-01-15T10:00:00Z');
      const responseTime = new Date('2024-01-15T10:00:30Z'); // 30 seconds

      const result = BusinessRulesService.validateResponseSLA(
        leadCreatedAt,
        responseTime,
        'hot'
      );

      expect(result.isValid).toBe(true);
      expect(result.severity).toBe('info');
      expect(result.metadata?.responseTimeSeconds).toBe(30);
      expect(result.metadata?.threshold).toBe(60);
    });

    test('should flag hot lead response SLA breach', () => {
      const leadCreatedAt = new Date('2024-01-15T10:00:00Z');
      const responseTime = new Date('2024-01-15T10:02:00Z'); // 2 minutes

      const result = BusinessRulesService.validateResponseSLA(
        leadCreatedAt,
        responseTime,
        'hot'
      );

      expect(result.isValid).toBe(false);
      expect(result.severity).toBe('error');
      expect(result.metadata?.slaBreached).toBe(true);
    });

    test('should validate warm lead response within SLA', () => {
      const leadCreatedAt = new Date('2024-01-15T10:00:00Z');
      const responseTime = new Date('2024-01-15T10:03:00Z'); // 3 minutes

      const result = BusinessRulesService.validateResponseSLA(
        leadCreatedAt,
        responseTime,
        'warm'
      );

      expect(result.isValid).toBe(true);
      expect(result.metadata?.threshold).toBe(240); // 4 minutes
    });

    test('should flag warm lead response SLA breach as warning', () => {
      const leadCreatedAt = new Date('2024-01-15T10:00:00Z');
      const responseTime = new Date('2024-01-15T10:10:00Z'); // 10 minutes

      const result = BusinessRulesService.validateResponseSLA(
        leadCreatedAt,
        responseTime,
        'warm'
      );

      expect(result.isValid).toBe(false);
      expect(result.severity).toBe('warning'); // Less severe than hot lead breach
    });

    test('should handle cold lead response timeframes', () => {
      const leadCreatedAt = new Date('2024-01-15T10:00:00Z');
      const responseTime = new Date('2024-01-15T10:30:00Z'); // 30 minutes

      const result = BusinessRulesService.validateResponseSLA(
        leadCreatedAt,
        responseTime,
        'cold'
      );

      expect(result.isValid).toBe(true);
      expect(result.metadata?.threshold).toBe(3600); // 1 hour
    });

    test('should handle unknown temperature with default SLA', () => {
      const leadCreatedAt = new Date('2024-01-15T10:00:00Z');
      const responseTime = new Date('2024-01-15T10:03:00Z'); // 3 minutes

      const result = BusinessRulesService.validateResponseSLA(
        leadCreatedAt,
        responseTime,
        'unknown' as LeadTemperature
      );

      expect(result.isValid).toBe(true);
      expect(result.metadata?.threshold).toBe(240); // Default to warm lead threshold
    });
  });

  describe('validateLeadAssignment', () => {
    test('should validate successful lead assignment', () => {
      const lead = LeadFactory.createValidLead() as Lead;
      
      // Mock low capacity user
      jest.spyOn(BusinessRulesService as any, 'getUserCapacity')
        .mockReturnValue({ currentLeads: 5, maxLeads: 25 });
      jest.spyOn(BusinessRulesService as any, 'getUserSkills')
        .mockReturnValue(['sales', 'enterprise_sales']);
      jest.spyOn(BusinessRulesService as any, 'getLeadRequirements')
        .mockReturnValue({ requiredSkills: ['sales'] });

      const result = BusinessRulesService.validateLeadAssignment(lead, 'user123');

      expect(result.isValid).toBe(true);
      expect(result.severity).toBe('info');
    });

    test('should reject assignment when user at capacity', () => {
      const lead = LeadFactory.createValidLead() as Lead;
      
      // Mock at-capacity user
      jest.spyOn(BusinessRulesService as any, 'getUserCapacity')
        .mockReturnValue({ currentLeads: 25, maxLeads: 25 });

      const result = BusinessRulesService.validateLeadAssignment(lead, 'user456');

      expect(result.isValid).toBe(false);
      expect(result.severity).toBe('error');
      expect(result.message).toContain('at capacity');
    });

    test('should warn about skill mismatch', () => {
      const lead = LeadFactory.createValidLead() as Lead;
      
      jest.spyOn(BusinessRulesService as any, 'getUserCapacity')
        .mockReturnValue({ currentLeads: 10, maxLeads: 25 });
      jest.spyOn(BusinessRulesService as any, 'getUserSkills')
        .mockReturnValue(['cold_calling']); // Missing enterprise_sales
      jest.spyOn(BusinessRulesService as any, 'getLeadRequirements')
        .mockReturnValue({ requiredSkills: ['enterprise_sales'] });

      const result = BusinessRulesService.validateLeadAssignment(lead, 'user789');

      expect(result.isValid).toBe(false);
      expect(result.severity).toBe('warning');
      expect(result.message).toContain('lacks required skills');
      expect(result.metadata?.missingSkills).toContain('enterprise_sales');
    });
  });

  describe('validateWorkflowExecution', () => {
    test('should validate workflow execution successfully', () => {
      const leadData = { email: 'test@example.com', firstName: 'John' };
      const context = { businessHours: true };

      jest.spyOn(BusinessRulesService as any, 'getRecentWorkflowExecutions')
        .mockReturnValue(5); // Below rate limit

      const result = BusinessRulesService.validateWorkflowExecution('standard_workflow', leadData, context);

      expect(result.isValid).toBe(true);
      expect(result.message).toBe('Workflow execution validated');
    });

    test('should reject workflow when prerequisites not met', () => {
      const invalidLeadData = { firstName: 'John' }; // Missing email
      
      const result = BusinessRulesService.validateWorkflowExecution('standard_workflow', invalidLeadData);

      expect(result.isValid).toBe(false);
      expect(result.severity).toBe('error');
      expect(result.message).toContain('prerequisite not met');
    });

    test('should warn about business hours restriction', () => {
      const leadData = { email: 'test@example.com', firstName: 'John' };
      const context = { businessHours: false };

      const result = BusinessRulesService.validateWorkflowExecution('voice_call_workflow', leadData, context);

      expect(result.isValid).toBe(false);
      expect(result.severity).toBe('warning');
      expect(result.message).toContain('business hours');
    });

    test('should reject when rate limit exceeded', () => {
      const leadData = { email: 'test@example.com', firstName: 'John' };

      jest.spyOn(BusinessRulesService as any, 'getRecentWorkflowExecutions')
        .mockReturnValue(150); // Above rate limit

      const result = BusinessRulesService.validateWorkflowExecution('standard_workflow', leadData);

      expect(result.isValid).toBe(false);
      expect(result.severity).toBe('error');
      expect(result.message).toContain('rate limit exceeded');
    });
  });

  describe('validateCommunicationCompliance', () => {
    test('should validate compliant communication', () => {
      const recipientData = { optedOut: false };
      const content = 'Hello! We have an exciting offer. Click here to unsubscribe.';

      const result = BusinessRulesService.validateCommunicationCompliance(
        'email',
        recipientData,
        content
      );

      expect(result.isValid).toBe(true);
      expect(result.message).toBe('Communication compliance validated');
    });

    test('should reject communication to opted-out recipient', () => {
      const recipientData = { 
        optedOut: true, 
        optedOutChannels: ['email', 'sms'] 
      };
      const content = 'Test message';

      const result = BusinessRulesService.validateCommunicationCompliance(
        'email',
        recipientData,
        content
      );

      expect(result.isValid).toBe(false);
      expect(result.severity).toBe('error');
      expect(result.message).toContain('opted out');
    });

    test('should warn about inappropriate SMS timing', () => {
      // Mock current time to be outside appropriate hours
      const originalDate = Date;
      global.Date = class extends Date {
        constructor() {
          super();
          return new originalDate('2024-01-15T02:00:00Z'); // 2 AM
        }
        static now() {
          return new originalDate('2024-01-15T02:00:00Z').getTime();
        }
      } as any;

      const recipientData = { optedOut: false };
      const content = 'Urgent message';

      const result = BusinessRulesService.validateCommunicationCompliance(
        'sms',
        recipientData,
        content
      );

      expect(result.isValid).toBe(false);
      expect(result.severity).toBe('warning');
      expect(result.message).toContain('outside appropriate hours');

      // Restore original Date
      global.Date = originalDate;
    });

    test('should detect content compliance issues', () => {
      const recipientData = { optedOut: false };
      const content = 'We guarantee 100% success! This offer is guaranteed to work.'; // Contains "guaranteed"

      const result = BusinessRulesService.validateCommunicationCompliance(
        'email',
        recipientData,
        content
      );

      expect(result.isValid).toBe(false);
      expect(result.severity).toBe('error');
      expect(result.message).toContain('compliance issues');
    });

    test('should detect missing unsubscribe option', () => {
      const recipientData = { optedOut: false };
      const content = 'This is a very long marketing message without an unsubscribe option that goes on for quite a while.';

      const result = BusinessRulesService.validateCommunicationCompliance(
        'email',
        recipientData,
        content
      );

      expect(result.isValid).toBe(false);
      expect(result.message).toContain('Missing unsubscribe option');
    });
  });

  describe('isBusinessHours', () => {
    test('should return true during business hours on weekday', () => {
      const mondayAt2PM = new Date('2024-01-15T14:00:00Z'); // Monday 2 PM
      const isBusinessHours = BusinessRulesService.isBusinessHours(mondayAt2PM);
      
      expect(isBusinessHours).toBe(true);
    });

    test('should return false during business hours on weekend', () => {
      const saturdayAt2PM = new Date('2024-01-13T14:00:00Z'); // Saturday 2 PM
      const isBusinessHours = BusinessRulesService.isBusinessHours(saturdayAt2PM);
      
      expect(isBusinessHours).toBe(false);
    });

    test('should return false outside business hours on weekday', () => {
      const mondayAt7AM = new Date('2024-01-15T07:00:00Z'); // Monday 7 AM
      const mondayAt8PM = new Date('2024-01-15T20:00:00Z'); // Monday 8 PM
      
      expect(BusinessRulesService.isBusinessHours(mondayAt7AM)).toBe(false);
      expect(BusinessRulesService.isBusinessHours(mondayAt8PM)).toBe(false);
    });

    test('should handle edge cases at business hour boundaries', () => {
      const mondayAt9AM = new Date('2024-01-15T09:00:00Z'); // Monday 9 AM (start)
      const mondayAt5PM = new Date('2024-01-15T17:00:00Z'); // Monday 5 PM (end)
      
      expect(BusinessRulesService.isBusinessHours(mondayAt9AM)).toBe(true);
      expect(BusinessRulesService.isBusinessHours(mondayAt5PM)).toBe(false); // End is exclusive
    });
  });

  describe('Performance and Edge Cases', () => {
    test('should validate lead efficiently', () => {
      const lead = LeadFactory.createValidLead();
      
      const startTime = Date.now();
      BusinessRulesService.validateLead(lead);
      const executionTime = Date.now() - startTime;

      expect(executionTime).toBeLessThan(50); // Should complete in under 50ms
    });

    test('should handle batch validation efficiently', () => {
      const leads = LeadFactory.createBatchOfLeads(50);
      
      const startTime = Date.now();
      leads.forEach(lead => BusinessRulesService.validateLead(lead));
      const executionTime = Date.now() - startTime;

      expect(executionTime).toBeLessThan(200); // Should validate 50 leads in under 200ms
    });

    test('should handle null and undefined values gracefully', () => {
      expect(() => {
        BusinessRulesService.validateLead(null as any);
      }).not.toThrow();

      expect(() => {
        BusinessRulesService.validateLead(undefined as any);
      }).not.toThrow();
    });

    test('should handle malformed lead data', () => {
      const malformedLead = {
        email: 123, // Wrong type
        firstName: [], // Wrong type
        customFields: 'not an object' // Wrong type
      };

      expect(() => {
        BusinessRulesService.validateLead(malformedLead as any);
      }).not.toThrow();
    });

    test('should handle very large lead objects', () => {
      const largeLead = LeadFactory.createValidLead({
        customFields: Object.fromEntries(
          Array.from({ length: 1000 }, (_, i) => [`field${i}`, `value${i}`])
        )
      });

      const startTime = Date.now();
      const results = BusinessRulesService.validateLead(largeLead);
      const executionTime = Date.now() - startTime;

      expect(results).toBeDefined();
      expect(executionTime).toBeLessThan(100);
    });

    test('should maintain consistency in validation results', () => {
      const lead = LeadFactory.createValidLead();
      
      const result1 = BusinessRulesService.validateLead(lead);
      const result2 = BusinessRulesService.validateLead(lead);

      expect(result1).toEqual(result2);
    });

    test('should handle concurrent validation requests', async () => {
      const leads = LeadFactory.createBatchOfLeads(100);
      
      const promises = leads.map(lead => 
        Promise.resolve(BusinessRulesService.validateLead(lead))
      );

      const results = await Promise.all(promises);
      
      expect(results).toHaveLength(100);
      expect(results.every(r => Array.isArray(r))).toBe(true);
    });
  });
});