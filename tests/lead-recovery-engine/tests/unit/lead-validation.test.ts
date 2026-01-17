/**
 * Unit tests for Lead Validation Service
 * Tests: 30 tests covering validation and sanitization functions
 */

import { LeadValidationService } from '../../src/services/lead-validation.service';
import { Lead } from '../../src/types/lead.interface';
import { LeadFactory } from '../factories/lead.factory';

describe('LeadValidationService', () => {
  describe('validateLead', () => {
    describe('Required Fields Validation', () => {
      test('should pass validation with all required fields', () => {
        const lead = LeadFactory.createValidLead();
        const result = LeadValidationService.validateLead(lead);

        expect(result.isValid).toBe(true);
        expect(result.errors).toHaveLength(0);
        expect(result.sanitizedData).toBeDefined();
      });

      test('should fail when email is missing', () => {
        const lead = LeadFactory.createValidLead();
        delete lead.email;

        const result = LeadValidationService.validateLead(lead);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('email is required');
      });

      test('should fail when firstName is missing', () => {
        const lead = LeadFactory.createValidLead();
        delete lead.firstName;

        const result = LeadValidationService.validateLead(lead);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('firstName is required');
      });

      test('should fail when lastName is missing', () => {
        const lead = LeadFactory.createValidLead();
        delete lead.lastName;

        const result = LeadValidationService.validateLead(lead);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('lastName is required');
      });

      test('should fail when required fields are empty strings', () => {
        const lead = {
          email: '',
          firstName: '   ',
          lastName: ''
        };

        const result = LeadValidationService.validateLead(lead);

        expect(result.isValid).toBe(false);
        expect(result.errors).toHaveLength(3);
        expect(result.errors).toContain('email is required');
        expect(result.errors).toContain('firstName is required');
        expect(result.errors).toContain('lastName is required');
      });
    });

    describe('Email Validation', () => {
      test('should validate correct email formats', () => {
        const validEmails = [
          'john.doe@company.com',
          'user@domain.co.uk',
          'test+tag@example.org',
          'firstname.lastname@subdomain.domain.com'
        ];

        validEmails.forEach(email => {
          const lead = LeadFactory.createValidLead({ email });
          const result = LeadValidationService.validateLead(lead);
          
          expect(result.isValid).toBe(true);
          expect(result.sanitizedData?.email).toBe(email.toLowerCase());
        });
      });

      test('should reject invalid email formats', () => {
        const invalidEmails = [
          'invalid-email',
          '@domain.com',
          'user@',
          'user.domain.com',
          'user@domain',
          ''
        ];

        invalidEmails.forEach(email => {
          const lead = LeadFactory.createValidLead({ email });
          const result = LeadValidationService.validateLead(lead);
          
          expect(result.isValid).toBe(false);
          expect(result.errors).toContain('Invalid email format');
        });
      });

      test('should normalize email to lowercase', () => {
        const lead = LeadFactory.createValidLead({ 
          email: 'John.Doe@COMPANY.COM' 
        });
        const result = LeadValidationService.validateLead(lead);

        expect(result.isValid).toBe(true);
        expect(result.sanitizedData?.email).toBe('john.doe@company.com');
      });

      test('should warn about disposable email domains', () => {
        const lead = LeadFactory.createValidLead({ 
          email: 'test@10minutemail.com' 
        });
        const result = LeadValidationService.validateLead(lead);

        expect(result.isValid).toBe(true);
        expect(result.warnings).toContain('Email uses disposable domain');
      });

      test('should warn about generic email addresses', () => {
        const genericEmails = ['info@company.com', 'admin@test.com', 'support@domain.org'];
        
        genericEmails.forEach(email => {
          const lead = LeadFactory.createValidLead({ email });
          const result = LeadValidationService.validateLead(lead);
          
          expect(result.warnings).toContain('Generic email address detected');
        });
      });
    });

    describe('Name Validation', () => {
      test('should sanitize and capitalize names correctly', () => {
        const lead = LeadFactory.createValidLead({
          firstName: 'john',
          lastName: 'DOE-smith'
        });
        const result = LeadValidationService.validateLead(lead);

        expect(result.isValid).toBe(true);
        expect(result.sanitizedData?.firstName).toBe('John');
        expect(result.sanitizedData?.lastName).toBe('Doe-Smith');
      });

      test('should reject names that are too short', () => {
        const lead = LeadFactory.createValidLead({
          firstName: 'J',
          lastName: 'D'
        });
        const result = LeadValidationService.validateLead(lead);

        expect(result.isValid).toBe(false);
        expect(result.errors).toContain('First name must be at least 2 characters');
        expect(result.errors).toContain('Last name must be at least 2 characters');
      });

      test('should handle names with special characters', () => {
        const lead = LeadFactory.createValidLead({
          firstName: "O'Connor",
          lastName: 'José-María'
        });
        const result = LeadValidationService.validateLead(lead);

        expect(result.isValid).toBe(true);
        expect(result.sanitizedData?.firstName).toBe("O'Connor");
        expect(result.sanitizedData?.lastName).toBe('José-María');
      });

      test('should detect potential test data', () => {
        const testCases = [
          { firstName: 'Test', lastName: 'Test' },
          { firstName: 'John', lastName: 'Doe' },
          { firstName: 'Jane', lastName: 'Doe' },
          { firstName: 'Foo', lastName: 'Bar' }
        ];

        testCases.forEach(({ firstName, lastName }) => {
          const lead = LeadFactory.createValidLead({ firstName, lastName });
          const result = LeadValidationService.validateLead(lead);
          
          expect(result.warnings).toContain('Potential test data detected');
        });
      });
    });

    describe('Phone Validation', () => {
      test('should validate and format US phone numbers', () => {
        const phoneNumbers = [
          { input: '(555) 123-4567', expected: '+15551234567' },
          { input: '555-123-4567', expected: '+15551234567' },
          { input: '5551234567', expected: '+15551234567' },
          { input: '+1 555 123 4567', expected: '+15551234567' },
          { input: '1-555-123-4567', expected: '+15551234567' }
        ];

        phoneNumbers.forEach(({ input, expected }) => {
          const lead = LeadFactory.createValidLead({ phone: input });
          const result = LeadValidationService.validateLead(lead);
          
          expect(result.isValid).toBe(true);
          expect(result.sanitizedData?.phone).toBe(expected);
        });
      });

      test('should handle invalid phone numbers gracefully', () => {
        const invalidPhones = ['123', '555-123', 'not-a-phone', ''];
        
        invalidPhones.forEach(phone => {
          const lead = LeadFactory.createValidLead({ phone });
          const result = LeadValidationService.validateLead(lead);
          
          expect(result.isValid).toBe(true); // Phone is optional
          expect(result.warnings.some(w => w.includes('Invalid phone'))).toBe(true);
          expect(result.sanitizedData?.phone).toBeNull();
        });
      });
    });

    describe('Lead Score Validation', () => {
      test('should accept valid lead scores', () => {
        const validScores = [0, 25, 50, 75, 100];
        
        validScores.forEach(score => {
          const lead = LeadFactory.createValidLead({ leadScore: score });
          const result = LeadValidationService.validateLead(lead);
          
          expect(result.isValid).toBe(true);
          expect(result.sanitizedData?.leadScore).toBe(score);
        });
      });

      test('should reject out-of-range lead scores', () => {
        const invalidScores = [-1, 101, 150, -10];
        
        invalidScores.forEach(score => {
          const lead = LeadFactory.createValidLead({ leadScore: score });
          const result = LeadValidationService.validateLead(lead);
          
          expect(result.isValid).toBe(false);
          expect(result.errors).toContain('Lead score must be between 0 and 100');
        });
      });

      test('should round decimal lead scores', () => {
        const lead = LeadFactory.createValidLead({ leadScore: 75.7 });
        const result = LeadValidationService.validateLead(lead);

        expect(result.isValid).toBe(true);
        expect(result.sanitizedData?.leadScore).toBe(76);
      });
    });

    describe('Business Rules Validation', () => {
      test('should warn about company size vs job title inconsistency', () => {
        const lead = LeadFactory.createValidLead({
          companySize: 5,
          jobTitle: 'VP Sales'
        });
        const result = LeadValidationService.validateLead(lead);

        expect(result.warnings).toContain('Job title may be inconsistent with company size');
      });
    });
  });

  describe('sanitizeLead', () => {
    test('should sanitize all lead fields properly', () => {
      const dirtyLead = {
        email: '  JOHN.DOE@COMPANY.COM  ',
        firstName: 'john',
        lastName: 'o\'connor-smith',
        phone: '(555) 123-4567',
        company: 'Test Corp   ',
        source: 'WEB-SITE_form',
        linkedinUrl: 'https://linkedin.com/in/john-doe',
        companyWebsite: 'https://company.com'
      };

      const result = LeadValidationService.sanitizeLead(dirtyLead);

      expect(result.email).toBe('john.doe@company.com');
      expect(result.firstName).toBe('John');
      expect(result.lastName).toBe('O\'Connor-Smith');
      expect(result.phone).toBe('+15551234567');
      expect(result.company).toBe('Test Corp');
      expect(result.source).toBe('website_form');
    });

    test('should handle missing or null values', () => {
      const incompleteLead = {
        email: 'test@example.com',
        firstName: 'John'
        // Missing other fields
      };

      const result = LeadValidationService.sanitizeLead(incompleteLead);

      expect(result.email).toBe('test@example.com');
      expect(result.firstName).toBe('John');
      expect(result.lastName).toBeUndefined();
      expect(result.phone).toBeUndefined();
    });

    test('should preserve numeric and enum fields correctly', () => {
      const lead = {
        email: 'test@example.com',
        leadScore: 85,
        companySize: 1000,
        companyRevenue: 50000000,
        status: 'qualified' as const,
        temperature: 'hot' as const,
        dataQuality: 'enriched' as const
      };

      const result = LeadValidationService.sanitizeLead(lead);

      expect(result.leadScore).toBe(85);
      expect(result.companySize).toBe(1000);
      expect(result.companyRevenue).toBe(50000000);
      expect(result.status).toBe('qualified');
      expect(result.temperature).toBe('hot');
      expect(result.dataQuality).toBe('enriched');
    });
  });

  describe('isDuplicateLead', () => {
    test('should detect duplicate leads by email', () => {
      const isDuplicate = LeadValidationService.isDuplicateLead('duplicate@example.com');
      expect(isDuplicate).toBe(true);
    });

    test('should return false for non-duplicate emails', () => {
      const isDuplicate = LeadValidationService.isDuplicateLead('unique@example.com');
      expect(isDuplicate).toBe(false);
    });

    test('should handle email case sensitivity', () => {
      const isDuplicate = LeadValidationService.isDuplicateLead('DUPLICATE@EXAMPLE.COM');
      expect(isDuplicate).toBe(true);
    });
  });

  describe('Edge Cases and Error Handling', () => {
    test('should handle empty lead object', () => {
      const result = LeadValidationService.validateLead({});

      expect(result.isValid).toBe(false);
      expect(result.errors).toHaveLength(3); // Missing required fields
    });

    test('should handle null and undefined values', () => {
      const lead = {
        email: null,
        firstName: undefined,
        lastName: '',
        phone: null
      } as any;

      const result = LeadValidationService.validateLead(lead);

      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });

    test('should handle extremely long field values', () => {
      const longString = 'a'.repeat(1000);
      const lead = LeadFactory.createValidLead({
        company: longString
      });

      const sanitized = LeadValidationService.sanitizeLead(lead);

      expect(sanitized.company?.length).toBeLessThanOrEqual(200);
    });

    test('should handle malicious input attempts', () => {
      const maliciousLead = {
        email: 'test@example.com',
        firstName: '<script>alert("xss")</script>',
        lastName: '"><img src=x onerror=alert(1)>',
        company: '<script>malicious()</script>Company'
      };

      const sanitized = LeadValidationService.sanitizeLead(maliciousLead);

      expect(sanitized.firstName).not.toContain('<script>');
      expect(sanitized.lastName).not.toContain('<img');
      expect(sanitized.company).not.toContain('<script>');
    });
  });

  describe('Performance Tests', () => {
    test('should validate lead within performance threshold', async () => {
      const lead = LeadFactory.createValidLead();
      
      const startTime = Date.now();
      LeadValidationService.validateLead(lead);
      const executionTime = Date.now() - startTime;

      expect(executionTime).toBeLessThan(10); // Should complete in under 10ms
    });

    test('should handle batch validation efficiently', async () => {
      const leads = LeadFactory.createBatchOfLeads(100);
      
      const startTime = Date.now();
      leads.forEach(lead => LeadValidationService.validateLead(lead));
      const executionTime = Date.now() - startTime;

      expect(executionTime).toBeLessThan(100); // Should complete batch in under 100ms
    });
  });
});