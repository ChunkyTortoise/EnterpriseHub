/**
 * Lead scoring service
 * Calculates lead scores based on multiple factors and machine learning
 */

import { Lead, LeadScoringResult, LeadScoringFactors } from '../types/lead.interface';

export class LeadScoringService {
  private static readonly SCORING_WEIGHTS = {
    emailDomain: 0.15,
    companySize: 0.20,
    jobSeniority: 0.25,
    industry: 0.10,
    behavioralSignals: 0.15,
    engagementHistory: 0.10,
    leadSource: 0.05
  };

  private static readonly HIGH_VALUE_DOMAINS = [
    'fortune500companies.com', 'techcorp.com', 'bigenterprise.com'
  ];

  private static readonly HIGH_VALUE_INDUSTRIES = [
    'Technology', 'Finance', 'Healthcare', 'Manufacturing'
  ];

  private static readonly SENIORITY_SCORES = {
    'C-Level': 100,
    'VP': 85,
    'Director': 70,
    'Manager': 55,
    'Senior': 40,
    'Individual Contributor': 25
  };

  private static readonly SOURCE_SCORES = {
    'referral': 90,
    'webinar': 75,
    'trade_show': 70,
    'linkedin': 60,
    'website': 50,
    'cold_outreach': 30
  };

  /**
   * Calculates comprehensive lead score
   */
  static calculateLeadScore(lead: Partial<Lead>): LeadScoringResult {
    const factors: LeadScoringFactors = {
      emailDomain: this.scoreEmailDomain(lead.email),
      companySize: this.scoreCompanySize(lead.companySize),
      jobSeniority: this.scoreJobSeniority(lead.jobTitle, lead.seniority),
      industry: this.scoreIndustry(lead.companyIndustry),
      behavioralSignals: this.scoreBehavioralSignals(lead),
      engagementHistory: this.scoreEngagementHistory(lead),
      leadSource: this.scoreLeadSource(lead.source),
      firmographics: this.scoreFirmographics(lead)
    };

    const weightedScore = this.calculateWeightedScore(factors);
    const finalScore = Math.min(100, Math.max(0, Math.round(weightedScore)));
    
    const confidence = this.calculateConfidence(lead, factors);
    const reasoning = this.generateScoreReasoning(factors, finalScore);
    const recommendations = this.generateRecommendations(factors, finalScore);

    return {
      score: finalScore,
      factors,
      reasoning,
      confidence,
      recommendations
    };
  }

  /**
   * Calculates score for email domain quality
   */
  private static scoreEmailDomain(email?: string): number {
    if (!email) return 0;

    const domain = email.split('@')[1]?.toLowerCase();
    if (!domain) return 0;

    // High-value company domains
    if (this.HIGH_VALUE_DOMAINS.includes(domain)) return 90;

    // Generic email providers (lower score)
    const genericDomains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com'];
    if (genericDomains.includes(domain)) return 30;

    // Corporate domains (medium-high score)
    if (!domain.includes('.edu') && !domain.includes('.gov')) {
      // Assume corporate email
      return 70;
    }

    return 50;
  }

  /**
   * Calculates score based on company size
   */
  private static scoreCompanySize(size?: number): number {
    if (!size) return 40; // Unknown size gets medium score

    if (size >= 1000) return 90;     // Enterprise
    if (size >= 500) return 80;      // Large
    if (size >= 100) return 70;      // Medium
    if (size >= 50) return 60;       // Small-medium
    if (size >= 20) return 50;       // Small
    return 30;                       // Very small/startup
  }

  /**
   * Calculates score based on job title and seniority
   */
  private static scoreJobSeniority(jobTitle?: string, seniority?: string): number {
    if (!jobTitle) return 40;

    // Use explicit seniority if available
    if (seniority && this.SENIORITY_SCORES[seniority as keyof typeof this.SENIORITY_SCORES]) {
      return this.SENIORITY_SCORES[seniority as keyof typeof this.SENIORITY_SCORES];
    }

    // Infer from job title
    const title = jobTitle.toLowerCase();
    
    if (title.includes('ceo') || title.includes('president') || title.includes('founder')) return 100;
    if (title.includes('cto') || title.includes('cfo') || title.includes('coo')) return 95;
    if (title.includes('vp') || title.includes('vice president')) return 85;
    if (title.includes('director')) return 70;
    if (title.includes('manager')) return 55;
    if (title.includes('senior') || title.includes('lead')) return 40;
    
    return 30;
  }

  /**
   * Calculates score based on industry
   */
  private static scoreIndustry(industry?: string): number {
    if (!industry) return 50;

    if (this.HIGH_VALUE_INDUSTRIES.includes(industry)) return 80;

    const mediumValueIndustries = ['Consulting', 'Professional Services', 'Real Estate'];
    if (mediumValueIndustries.includes(industry)) return 60;

    return 40;
  }

  /**
   * Calculates score based on behavioral signals
   */
  private static scoreBehavioralSignals(lead: Partial<Lead>): number {
    let score = 50; // Base score

    // Website activity signals (would come from tracking)
    if (lead.customFields?.pageViews > 5) score += 15;
    if (lead.customFields?.timeOnSite > 300) score += 10; // 5+ minutes
    if (lead.customFields?.downloadedContent) score += 20;

    // Engagement timing
    if (lead.customFields?.contactedOutsideHours) score -= 10;
    if (lead.customFields?.multipleFormSubmissions) score += 15;

    return Math.min(100, Math.max(0, score));
  }

  /**
   * Calculates score based on engagement history
   */
  private static scoreEngagementHistory(lead: Partial<Lead>): number {
    let score = 50; // Base score

    // Email engagement
    if (lead.customFields?.emailOpens > 0) score += 10;
    if (lead.customFields?.emailClicks > 0) score += 15;
    if (lead.customFields?.emailReplies > 0) score += 25;

    // Social engagement
    if (lead.customFields?.linkedinConnection) score += 10;
    if (lead.customFields?.socialShares > 0) score += 5;

    return Math.min(100, Math.max(0, score));
  }

  /**
   * Calculates score based on lead source
   */
  private static scoreLeadSource(source?: string): number {
    if (!source) return 40;

    return this.SOURCE_SCORES[source as keyof typeof this.SOURCE_SCORES] || 40;
  }

  /**
   * Calculates firmographic score
   */
  private static scoreFirmographics(lead: Partial<Lead>): number {
    let score = 50;

    if (lead.companyRevenue) {
      if (lead.companyRevenue >= 100000000) score += 25; // $100M+
      else if (lead.companyRevenue >= 10000000) score += 15; // $10M+
      else if (lead.companyRevenue >= 1000000) score += 10; // $1M+
    }

    if (lead.companyWebsite) score += 5; // Has website
    if (lead.linkedinUrl) score += 5; // Has LinkedIn profile

    return Math.min(100, Math.max(0, score));
  }

  /**
   * Calculates weighted final score
   */
  private static calculateWeightedScore(factors: LeadScoringFactors): number {
    return (
      factors.emailDomain * this.SCORING_WEIGHTS.emailDomain +
      factors.companySize * this.SCORING_WEIGHTS.companySize +
      factors.jobSeniority * this.SCORING_WEIGHTS.jobSeniority +
      factors.industry * this.SCORING_WEIGHTS.industry +
      factors.behavioralSignals * this.SCORING_WEIGHTS.behavioralSignals +
      factors.engagementHistory * this.SCORING_WEIGHTS.engagementHistory +
      factors.leadSource * this.SCORING_WEIGHTS.leadSource
    );
  }

  /**
   * Calculates confidence level in the score
   */
  private static calculateConfidence(lead: Partial<Lead>, factors: LeadScoringFactors): number {
    let confidence = 0.5; // Base confidence

    // Data completeness increases confidence
    const dataPoints = [
      lead.email, lead.company, lead.jobTitle, lead.companySize, 
      lead.companyIndustry, lead.source
    ].filter(Boolean).length;
    
    confidence += (dataPoints / 6) * 0.3; // Up to 30% boost for complete data

    // Enriched data increases confidence
    if (lead.dataQuality === 'enriched' || lead.dataQuality === 'premium') {
      confidence += 0.15;
    }

    // Recent activity increases confidence
    if (lead.lastActivity && 
        new Date().getTime() - new Date(lead.lastActivity).getTime() < 24 * 60 * 60 * 1000) {
      confidence += 0.1;
    }

    return Math.min(1.0, confidence);
  }

  /**
   * Generates human-readable scoring reasoning
   */
  private static generateScoreReasoning(factors: LeadScoringFactors, finalScore: number): string {
    const reasons: string[] = [];

    if (factors.jobSeniority >= 80) reasons.push('Senior decision-maker role');
    if (factors.companySize >= 80) reasons.push('Large enterprise company');
    if (factors.emailDomain >= 70) reasons.push('Corporate email domain');
    if (factors.behavioralSignals >= 70) reasons.push('Strong engagement signals');
    if (factors.leadSource >= 70) reasons.push('High-quality lead source');

    if (reasons.length === 0) {
      if (finalScore >= 70) reasons.push('Multiple positive indicators');
      else if (finalScore >= 40) reasons.push('Mixed signals, needs nurturing');
      else reasons.push('Limited qualifying information available');
    }

    return reasons.join('; ');
  }

  /**
   * Generates actionable recommendations
   */
  private static generateRecommendations(factors: LeadScoringFactors, finalScore: number): string[] {
    const recommendations: string[] = [];

    if (finalScore >= 80) {
      recommendations.push('High priority - contact within 1 hour');
      recommendations.push('Assign to senior sales rep');
    } else if (finalScore >= 60) {
      recommendations.push('Medium priority - contact within 4 hours');
      recommendations.push('Schedule discovery call');
    } else if (finalScore >= 40) {
      recommendations.push('Add to nurture sequence');
      recommendations.push('Gather more qualifying information');
    } else {
      recommendations.push('Low priority - automated nurture only');
      recommendations.push('Monitor for engagement improvements');
    }

    // Specific factor recommendations
    if (factors.behavioralSignals < 40) {
      recommendations.push('Increase content engagement');
    }
    if (factors.emailDomain < 50) {
      recommendations.push('Verify business email address');
    }

    return recommendations;
  }

  /**
   * Bulk scoring for multiple leads
   */
  static scoreLeadsBatch(leads: Partial<Lead>[]): LeadScoringResult[] {
    return leads.map(lead => this.calculateLeadScore(lead));
  }

  /**
   * Re-scores lead with updated information
   */
  static rescoreLead(existingLead: Lead, updates: Partial<Lead>): LeadScoringResult {
    const updatedLead = { ...existingLead, ...updates };
    return this.calculateLeadScore(updatedLead);
  }
}