/**
 * Unit tests for Lead Scoring Service
 * Tests: 40 tests covering scoring algorithm and factors
 */

import { LeadScoringService } from '../../src/services/lead-scoring.service';
import { Lead } from '../../src/types/lead.interface';
import { LeadFactory } from '../factories/lead.factory';

describe('LeadScoringService', () => {
  describe('calculateLeadScore', () => {
    describe('Overall Scoring', () => {
      test('should calculate score for high-value lead', () => {
        const lead = LeadFactory.createHighScoreLead({
          email: 'ceo@techcorp.com',
          jobTitle: 'CEO',
          companySize: 1000,
          companyIndustry: 'Technology',
          source: 'referral',
          companyRevenue: 50000000
        });

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.score).toBeGreaterThan(70);
        expect(result.confidence).toBeGreaterThan(0.7);
        expect(result.recommendations).toContain('High priority - contact within 1 hour');
      });

      test('should calculate score for low-value lead', () => {
        const lead = LeadFactory.createLowScoreLead({
          email: 'user@gmail.com',
          jobTitle: 'Individual Contributor',
          companySize: 5,
          companyIndustry: 'Other',
          source: 'cold_outreach'
        });

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.score).toBeLessThan(40);
        expect(result.recommendations).toContain('Low priority - automated nurture only');
      });

      test('should calculate score for medium-value lead', () => {
        const lead = LeadFactory.createValidLead({
          email: 'manager@company.com',
          jobTitle: 'Manager',
          companySize: 100,
          companyIndustry: 'Professional Services',
          source: 'website'
        });

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.score).toBeGreaterThan(40);
        expect(result.score).toBeLessThan(80);
        expect(result.recommendations).toContain('Medium priority - contact within 4 hours');
      });

      test('should enforce score boundaries (0-100)', () => {
        const extremeHighLead = LeadFactory.createValidLead({
          email: 'ceo@fortune500companies.com',
          jobTitle: 'CEO',
          seniority: 'C-Level',
          companySize: 10000,
          companyIndustry: 'Technology',
          source: 'referral',
          companyRevenue: 1000000000,
          customFields: {
            pageViews: 20,
            timeOnSite: 600,
            downloadedContent: true,
            emailOpens: 10,
            emailClicks: 5,
            emailReplies: 2
          }
        });

        const result = LeadScoringService.calculateLeadScore(extremeHighLead);

        expect(result.score).toBeLessThanOrEqual(100);
        expect(result.score).toBeGreaterThanOrEqual(0);
      });
    });

    describe('Email Domain Scoring', () => {
      test('should score high-value company domains highly', () => {
        const lead = LeadFactory.createValidLead({
          email: 'user@fortune500companies.com'
        });

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.emailDomain).toBeGreaterThan(80);
      });

      test('should score generic email providers lower', () => {
        const genericEmails = [
          'user@gmail.com',
          'user@yahoo.com',
          'user@hotmail.com',
          'user@outlook.com'
        ];

        genericEmails.forEach(email => {
          const lead = LeadFactory.createValidLead({ email });
          const result = LeadScoringService.calculateLeadScore(lead);
          
          expect(result.factors.emailDomain).toBe(30);
        });
      });

      test('should score corporate domains medium-high', () => {
        const lead = LeadFactory.createValidLead({
          email: 'user@randomcorp.com'
        });

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.emailDomain).toBe(70);
      });

      test('should handle missing email domain', () => {
        const lead = LeadFactory.createValidLead();
        delete lead.email;

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.emailDomain).toBe(0);
      });
    });

    describe('Company Size Scoring', () => {
      test('should score enterprise companies (1000+) highest', () => {
        const lead = LeadFactory.createValidLead({ companySize: 5000 });
        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.companySize).toBe(90);
      });

      test('should score large companies (500-999) high', () => {
        const lead = LeadFactory.createValidLead({ companySize: 750 });
        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.companySize).toBe(80);
      });

      test('should score medium companies (100-499) moderately', () => {
        const lead = LeadFactory.createValidLead({ companySize: 250 });
        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.companySize).toBe(70);
      });

      test('should score small companies (20-99) lower', () => {
        const companySizes = [25, 50, 75, 99];
        
        companySizes.forEach(size => {
          const lead = LeadFactory.createValidLead({ companySize: size });
          const result = LeadScoringService.calculateLeadScore(lead);
          
          if (size >= 50) {
            expect(result.factors.companySize).toBe(60);
          } else {
            expect(result.factors.companySize).toBe(50);
          }
        });
      });

      test('should score very small companies (1-19) lowest', () => {
        const lead = LeadFactory.createValidLead({ companySize: 10 });
        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.companySize).toBe(30);
      });

      test('should handle missing company size with default score', () => {
        const lead = LeadFactory.createValidLead();
        delete lead.companySize;

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.companySize).toBe(40);
      });
    });

    describe('Job Seniority Scoring', () => {
      test('should score C-level positions highest', () => {
        const cLevelTitles = [
          'CEO', 'Chief Executive Officer', 'CTO', 'Chief Technology Officer',
          'CFO', 'Chief Financial Officer', 'COO', 'President', 'Founder'
        ];

        cLevelTitles.forEach(title => {
          const lead = LeadFactory.createValidLead({ jobTitle: title });
          const result = LeadScoringService.calculateLeadScore(lead);
          
          expect(result.factors.jobSeniority).toBeGreaterThan(90);
        });
      });

      test('should score VP positions highly', () => {
        const vpTitles = [
          'VP Sales', 'Vice President', 'VP Marketing', 'VP Operations'
        ];

        vpTitles.forEach(title => {
          const lead = LeadFactory.createValidLead({ jobTitle: title });
          const result = LeadScoringService.calculateLeadScore(lead);
          
          expect(result.factors.jobSeniority).toBe(85);
        });
      });

      test('should score Directors moderately', () => {
        const directorTitles = [
          'Director', 'Director of Sales', 'Marketing Director'
        ];

        directorTitles.forEach(title => {
          const lead = LeadFactory.createValidLead({ jobTitle: title });
          const result = LeadScoringService.calculateLeadScore(lead);
          
          expect(result.factors.jobSeniority).toBe(70);
        });
      });

      test('should use explicit seniority when available', () => {
        const lead = LeadFactory.createValidLead({ 
          jobTitle: 'Sales Executive',
          seniority: 'VP'
        });

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.jobSeniority).toBe(85);
      });

      test('should handle missing job title', () => {
        const lead = LeadFactory.createValidLead();
        delete lead.jobTitle;

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.jobSeniority).toBe(40);
      });
    });

    describe('Industry Scoring', () => {
      test('should score high-value industries highly', () => {
        const highValueIndustries = [
          'Technology', 'Finance', 'Healthcare', 'Manufacturing'
        ];

        highValueIndustries.forEach(industry => {
          const lead = LeadFactory.createValidLead({ companyIndustry: industry });
          const result = LeadScoringService.calculateLeadScore(lead);
          
          expect(result.factors.industry).toBe(80);
        });
      });

      test('should score medium-value industries moderately', () => {
        const mediumValueIndustries = [
          'Consulting', 'Professional Services', 'Real Estate'
        ];

        mediumValueIndustries.forEach(industry => {
          const lead = LeadFactory.createValidLead({ companyIndustry: industry });
          const result = LeadScoringService.calculateLeadScore(lead);
          
          expect(result.factors.industry).toBe(60);
        });
      });

      test('should score other industries with default score', () => {
        const lead = LeadFactory.createValidLead({ companyIndustry: 'Agriculture' });
        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.industry).toBe(40);
      });
    });

    describe('Lead Source Scoring', () => {
      test('should score referrals highest', () => {
        const lead = LeadFactory.createValidLead({ source: 'referral' });
        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.leadSource).toBe(90);
      });

      test('should score webinars and trade shows highly', () => {
        const highValueSources = ['webinar', 'trade_show'];

        highValueSources.forEach(source => {
          const lead = LeadFactory.createValidLead({ source });
          const result = LeadScoringService.calculateLeadScore(lead);
          
          expect(result.factors.leadSource).toBeGreaterThan(65);
        });
      });

      test('should score cold outreach lowest', () => {
        const lead = LeadFactory.createValidLead({ source: 'cold_outreach' });
        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.leadSource).toBe(30);
      });

      test('should handle unknown sources with default score', () => {
        const lead = LeadFactory.createValidLead({ source: 'unknown_source' });
        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.leadSource).toBe(40);
      });
    });

    describe('Behavioral Signals Scoring', () => {
      test('should score high engagement positively', () => {
        const lead = LeadFactory.createValidLead({
          customFields: {
            pageViews: 10,
            timeOnSite: 400,
            downloadedContent: true,
            multipleFormSubmissions: true
          }
        });

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.behavioralSignals).toBeGreaterThan(70);
      });

      test('should score low engagement negatively', () => {
        const lead = LeadFactory.createValidLead({
          customFields: {
            pageViews: 1,
            timeOnSite: 30,
            contactedOutsideHours: true
          }
        });

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.behavioralSignals).toBeLessThan(50);
      });

      test('should handle missing behavioral data with default score', () => {
        const lead = LeadFactory.createValidLead();
        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.behavioralSignals).toBe(50);
      });
    });

    describe('Engagement History Scoring', () => {
      test('should score email engagement positively', () => {
        const lead = LeadFactory.createValidLead({
          customFields: {
            emailOpens: 5,
            emailClicks: 3,
            emailReplies: 1,
            linkedinConnection: true
          }
        });

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.engagementHistory).toBeGreaterThan(70);
      });

      test('should handle no engagement history with default score', () => {
        const lead = LeadFactory.createValidLead();
        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.engagementHistory).toBe(50);
      });
    });

    describe('Firmographics Scoring', () => {
      test('should score high revenue companies highly', () => {
        const lead = LeadFactory.createValidLead({
          companyRevenue: 500000000, // $500M
          companyWebsite: 'https://company.com',
          linkedinUrl: 'https://linkedin.com/in/user'
        });

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.firmographics).toBeGreaterThan(70);
      });

      test('should score missing firmographics with default', () => {
        const lead = LeadFactory.createValidLead();
        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.factors.firmographics).toBe(50);
      });
    });

    describe('Confidence Calculation', () => {
      test('should have high confidence with complete enriched data', () => {
        const lead = LeadFactory.createLeadWithEnrichment({
          dataQuality: 'enriched',
          lastActivity: new Date() // Recent activity
        });

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.confidence).toBeGreaterThan(0.8);
      });

      test('should have lower confidence with incomplete data', () => {
        const lead = {
          email: 'test@example.com',
          firstName: 'John',
          lastName: 'Doe'
        };

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.confidence).toBeLessThan(0.7);
      });

      test('should increase confidence with recent activity', () => {
        const recentLead = LeadFactory.createValidLead({
          lastActivity: new Date()
        });

        const oldLead = LeadFactory.createValidLead({
          lastActivity: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) // 7 days ago
        });

        const recentResult = LeadScoringService.calculateLeadScore(recentLead);
        const oldResult = LeadScoringService.calculateLeadScore(oldLead);

        expect(recentResult.confidence).toBeGreaterThan(oldResult.confidence);
      });
    });

    describe('Recommendations Generation', () => {
      test('should recommend immediate contact for high scores', () => {
        const highScoreLead = LeadFactory.createHighScoreLead();
        const result = LeadScoringService.calculateLeadScore(highScoreLead);

        expect(result.recommendations).toContain('High priority - contact within 1 hour');
        expect(result.recommendations).toContain('Assign to senior sales rep');
      });

      test('should recommend nurture sequence for medium scores', () => {
        const mediumLead = LeadFactory.createValidLead({ leadScore: 50 });
        const result = LeadScoringService.calculateLeadScore(mediumLead);

        expect(result.recommendations).toContain('Add to nurture sequence');
      });

      test('should recommend automated nurture for low scores', () => {
        const lowScoreLead = LeadFactory.createLowScoreLead();
        const result = LeadScoringService.calculateLeadScore(lowScoreLead);

        expect(result.recommendations).toContain('Low priority - automated nurture only');
      });

      test('should include specific factor recommendations', () => {
        const lead = LeadFactory.createValidLead({
          email: 'user@gmail.com' // Low domain score
        });

        const result = LeadScoringService.calculateLeadScore(lead);

        expect(result.recommendations).toContain('Verify business email address');
      });
    });
  });

  describe('scoreLeadsBatch', () => {
    test('should score multiple leads efficiently', () => {
      const leads = LeadFactory.createBatchOfLeads(50);
      
      const startTime = Date.now();
      const results = LeadScoringService.scoreLeadsBatch(leads);
      const executionTime = Date.now() - startTime;

      expect(results).toHaveLength(50);
      expect(executionTime).toBeLessThan(100); // Should complete in under 100ms
      expect(results.every(r => typeof r.score === 'number')).toBe(true);
    });

    test('should handle empty batch', () => {
      const results = LeadScoringService.scoreLeadsBatch([]);
      expect(results).toHaveLength(0);
    });
  });

  describe('rescoreLead', () => {
    test('should update score with new information', () => {
      const originalLead = LeadFactory.createLowScoreLead() as Lead;
      const originalResult = LeadScoringService.calculateLeadScore(originalLead);

      const updates = {
        jobTitle: 'CEO',
        companySize: 1000,
        source: 'referral'
      };

      const newResult = LeadScoringService.rescoreLead(originalLead, updates);

      expect(newResult.score).toBeGreaterThan(originalResult.score);
    });

    test('should maintain original data not being updated', () => {
      const originalLead = LeadFactory.createValidLead() as Lead;
      const originalEmail = originalLead.email;

      const updates = { jobTitle: 'CEO' };
      const newResult = LeadScoringService.rescoreLead(originalLead, updates);

      // Should still use original email for domain scoring
      expect(newResult.factors.emailDomain).toBe(
        LeadScoringService.calculateLeadScore(originalLead).factors.emailDomain
      );
    });
  });

  describe('Performance and Edge Cases', () => {
    test('should handle null and undefined values gracefully', () => {
      const incompleteData = {
        email: null,
        firstName: 'John',
        lastName: null,
        companySize: undefined
      } as any;

      expect(() => {
        LeadScoringService.calculateLeadScore(incompleteData);
      }).not.toThrow();
    });

    test('should complete scoring within performance threshold', () => {
      const lead = LeadFactory.createLeadWithEnrichment();
      
      const startTime = Date.now();
      LeadScoringService.calculateLeadScore(lead);
      const executionTime = Date.now() - startTime;

      expect(executionTime).toBeLessThan(5); // Should complete in under 5ms
    });

    test('should return consistent scores for identical data', () => {
      const lead = LeadFactory.createValidLead();
      
      const result1 = LeadScoringService.calculateLeadScore(lead);
      const result2 = LeadScoringService.calculateLeadScore(lead);

      expect(result1.score).toBe(result2.score);
      expect(result1.confidence).toBe(result2.confidence);
    });
  });
});