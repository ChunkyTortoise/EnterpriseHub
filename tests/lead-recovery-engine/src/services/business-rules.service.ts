/**
 * Business rules validation and enforcement service
 * Handles complex business logic validation for lead processing
 */

import { Lead, LeadStatus, LeadTemperature } from '../types/lead.interface';

export interface BusinessRule {
  name: string;
  description: string;
  validator: (data: any, context?: any) => BusinessRuleResult;
}

export interface BusinessRuleResult {
  isValid: boolean;
  severity: 'error' | 'warning' | 'info';
  message: string;
  suggestedAction?: string;
  metadata?: Record<string, any>;
}

export interface BusinessRuleContext {
  leadId?: string;
  workflowId?: string;
  userId?: string;
  currentStep?: string;
  businessHours?: boolean;
  timestamp: Date;
}

export class BusinessRulesService {
  private static readonly BUSINESS_HOURS = {
    start: 9, // 9 AM
    end: 17,  // 5 PM
    timezone: 'America/New_York',
    weekdays: [1, 2, 3, 4, 5] // Monday-Friday
  };

  private static readonly SLA_THRESHOLDS = {
    hot_lead_response: 60, // 60 seconds
    warm_lead_response: 240, // 4 minutes
    cold_lead_response: 3600, // 1 hour
    follow_up_sequence: 86400 // 24 hours
  };

  private static readonly LEAD_QUALITY_THRESHOLDS = {
    enterprise_min_company_size: 1000,
    enterprise_min_revenue: 100000000, // $100M
    qualified_min_score: 60,
    hot_lead_min_score: 80
  };

  /**
   * Validates lead against all applicable business rules
   */
  static validateLead(lead: Partial<Lead>, context: Partial<BusinessRuleContext> = {}): BusinessRuleResult[] {
    const results: BusinessRuleResult[] = [];
    const fullContext: BusinessRuleContext = {
      timestamp: new Date(),
      businessHours: this.isBusinessHours(),
      ...context
    };

    // Core validation rules
    results.push(this.validateLeadCompleteness(lead, fullContext));
    results.push(this.validateLeadQuality(lead, fullContext));
    results.push(this.validateBusinessHours(lead, fullContext));
    results.push(this.validateDuplicatePrevention(lead, fullContext));
    results.push(this.validateLeadScoring(lead, fullContext));
    results.push(this.validateContactPreferences(lead, fullContext));

    // Advanced validation rules
    if (lead.companySize && lead.companyRevenue) {
      results.push(this.validateEnterpriseRules(lead, fullContext));
    }

    if (lead.source) {
      results.push(this.validateSourceSpecificRules(lead, fullContext));
    }

    return results.filter(result => result !== null);
  }

  /**
   * Validates response time SLA compliance
   */
  static validateResponseSLA(
    leadCreatedAt: Date,
    responseTime: Date,
    leadTemperature: LeadTemperature,
    context: Partial<BusinessRuleContext> = {}
  ): BusinessRuleResult {
    const responseTimeMs = responseTime.getTime() - leadCreatedAt.getTime();
    const responseTimeSeconds = Math.floor(responseTimeMs / 1000);

    let threshold: number;
    let thresholdName: string;

    switch (leadTemperature) {
      case 'hot':
        threshold = this.SLA_THRESHOLDS.hot_lead_response;
        thresholdName = 'Hot Lead Response';
        break;
      case 'warm':
        threshold = this.SLA_THRESHOLDS.warm_lead_response;
        thresholdName = 'Warm Lead Response';
        break;
      case 'cold':
        threshold = this.SLA_THRESHOLDS.cold_lead_response;
        thresholdName = 'Cold Lead Response';
        break;
      default:
        threshold = this.SLA_THRESHOLDS.warm_lead_response;
        thresholdName = 'Default Lead Response';
    }

    const isValid = responseTimeSeconds <= threshold;
    const severity = isValid ? 'info' : (leadTemperature === 'hot' ? 'error' : 'warning');

    return {
      isValid,
      severity,
      message: `${thresholdName} SLA: ${responseTimeSeconds}s (threshold: ${threshold}s)`,
      suggestedAction: isValid ? undefined : 'Consider process optimization or automation improvements',
      metadata: {
        responseTimeSeconds,
        threshold,
        leadTemperature,
        slaBreached: !isValid
      }
    };
  }

  /**
   * Validates lead assignment rules
   */
  static validateLeadAssignment(lead: Lead, assignedToUserId: string, context: Partial<BusinessRuleContext> = {}): BusinessRuleResult {
    // Mock user data - in real implementation, this would come from user service
    const userCapacity = this.getUserCapacity(assignedToUserId);
    const userSkills = this.getUserSkills(assignedToUserId);
    const leadRequirements = this.getLeadRequirements(lead);

    // Check capacity
    if (userCapacity.currentLeads >= userCapacity.maxLeads) {
      return {
        isValid: false,
        severity: 'error',
        message: `User ${assignedToUserId} is at capacity (${userCapacity.currentLeads}/${userCapacity.maxLeads})`,
        suggestedAction: 'Assign to different user or increase capacity'
      };
    }

    // Check skill match
    const hasRequiredSkills = leadRequirements.requiredSkills.every(skill => 
      userSkills.includes(skill)
    );

    if (!hasRequiredSkills) {
      const missingSkills = leadRequirements.requiredSkills.filter(skill => 
        !userSkills.includes(skill)
      );

      return {
        isValid: false,
        severity: 'warning',
        message: `User lacks required skills: ${missingSkills.join(', ')}`,
        suggestedAction: 'Consider skill-based routing or training',
        metadata: { missingSkills }
      };
    }

    return {
      isValid: true,
      severity: 'info',
      message: 'Lead assignment validated successfully'
    };
  }

  /**
   * Validates workflow execution rules
   */
  static validateWorkflowExecution(workflowId: string, leadData: any, context: Partial<BusinessRuleContext> = {}): BusinessRuleResult {
    const workflowRules = this.getWorkflowRules(workflowId);

    // Check prerequisites
    if (workflowRules.prerequisites) {
      for (const prerequisite of workflowRules.prerequisites) {
        if (!this.checkPrerequisite(prerequisite, leadData, context)) {
          return {
            isValid: false,
            severity: 'error',
            message: `Workflow prerequisite not met: ${prerequisite.description}`,
            suggestedAction: prerequisite.suggestedAction
          };
        }
      }
    }

    // Check timing restrictions
    if (workflowRules.businessHoursOnly && !context.businessHours) {
      return {
        isValid: false,
        severity: 'warning',
        message: 'Workflow can only be executed during business hours',
        suggestedAction: 'Schedule for next business day or use alternative workflow'
      };
    }

    // Check rate limits
    if (workflowRules.rateLimit) {
      const recentExecutions = this.getRecentWorkflowExecutions(workflowId, workflowRules.rateLimit.windowMs);
      if (recentExecutions >= workflowRules.rateLimit.maxExecutions) {
        return {
          isValid: false,
          severity: 'error',
          message: `Workflow rate limit exceeded: ${recentExecutions}/${workflowRules.rateLimit.maxExecutions} executions`,
          suggestedAction: 'Wait for rate limit window to reset'
        };
      }
    }

    return {
      isValid: true,
      severity: 'info',
      message: 'Workflow execution validated'
    };
  }

  /**
   * Validates communication compliance rules
   */
  static validateCommunicationCompliance(
    channel: string,
    recipientData: any,
    content: string,
    context: Partial<BusinessRuleContext> = {}
  ): BusinessRuleResult {
    const results: BusinessRuleResult[] = [];

    // Check opt-out status
    if (recipientData.optedOut && recipientData.optedOutChannels?.includes(channel)) {
      return {
        isValid: false,
        severity: 'error',
        message: `Recipient has opted out of ${channel} communications`,
        suggestedAction: 'Remove from communication list or use alternative channel'
      };
    }

    // Check do-not-contact hours
    if (channel === 'sms' || channel === 'call') {
      const currentHour = new Date().getHours();
      if (currentHour < 8 || currentHour > 21) { // 8 AM - 9 PM
        return {
          isValid: false,
          severity: 'warning',
          message: 'Communication outside appropriate hours for voice/SMS',
          suggestedAction: 'Schedule for appropriate hours or use email'
        };
      }
    }

    // Check content compliance
    const contentIssues = this.checkContentCompliance(content);
    if (contentIssues.length > 0) {
      return {
        isValid: false,
        severity: 'error',
        message: `Content compliance issues: ${contentIssues.join(', ')}`,
        suggestedAction: 'Review and modify content before sending'
      };
    }

    return {
      isValid: true,
      severity: 'info',
      message: 'Communication compliance validated'
    };
  }

  /**
   * Checks if current time is within business hours
   */
  static isBusinessHours(timestamp = new Date()): boolean {
    const dayOfWeek = timestamp.getDay();
    const hour = timestamp.getHours();

    return (
      this.BUSINESS_HOURS.weekdays.includes(dayOfWeek) &&
      hour >= this.BUSINESS_HOURS.start &&
      hour < this.BUSINESS_HOURS.end
    );
  }

  // Private validation methods

  private static validateLeadCompleteness(lead: Partial<Lead>, context: BusinessRuleContext): BusinessRuleResult {
    const missingFields = [];
    const requiredFields = ['email', 'firstName', 'lastName'];

    requiredFields.forEach(field => {
      if (!lead[field as keyof Lead]) {
        missingFields.push(field);
      }
    });

    if (missingFields.length > 0) {
      return {
        isValid: false,
        severity: 'error',
        message: `Missing required fields: ${missingFields.join(', ')}`,
        suggestedAction: 'Collect missing information before proceeding'
      };
    }

    return {
      isValid: true,
      severity: 'info',
      message: 'Lead completeness validated'
    };
  }

  private static validateLeadQuality(lead: Partial<Lead>, context: BusinessRuleContext): BusinessRuleResult {
    let qualityScore = 0;
    const issues = [];

    // Email domain quality
    if (lead.email) {
      const domain = lead.email.split('@')[1];
      const genericDomains = ['gmail.com', 'yahoo.com', 'hotmail.com'];
      if (genericDomains.includes(domain?.toLowerCase())) {
        issues.push('Generic email domain');
      } else {
        qualityScore += 20;
      }
    }

    // Company information
    if (lead.company && lead.company.length > 2) {
      qualityScore += 15;
    } else {
      issues.push('Missing or insufficient company information');
    }

    // Job title
    if (lead.jobTitle && lead.jobTitle.length > 2) {
      qualityScore += 15;
    } else {
      issues.push('Missing job title information');
    }

    // Phone number
    if (lead.phone && lead.phone.length >= 10) {
      qualityScore += 10;
    }

    const severity = qualityScore >= 40 ? 'info' : qualityScore >= 20 ? 'warning' : 'error';

    return {
      isValid: qualityScore >= 20,
      severity,
      message: `Lead quality score: ${qualityScore}/60${issues.length > 0 ? ` (Issues: ${issues.join(', ')})` : ''}`,
      suggestedAction: qualityScore < 20 ? 'Consider lead enrichment before processing' : undefined,
      metadata: { qualityScore, issues }
    };
  }

  private static validateBusinessHours(lead: Partial<Lead>, context: BusinessRuleContext): BusinessRuleResult {
    if (context.businessHours) {
      return {
        isValid: true,
        severity: 'info',
        message: 'Lead received during business hours'
      };
    }

    const urgencyIndicators = [
      lead.temperature === 'hot',
      lead.leadScore && lead.leadScore > 80,
      lead.source === 'referral'
    ];

    const isUrgent = urgencyIndicators.some(Boolean);

    return {
      isValid: true,
      severity: isUrgent ? 'warning' : 'info',
      message: `Lead received outside business hours${isUrgent ? ' - high priority lead detected' : ''}`,
      suggestedAction: isUrgent ? 'Consider immediate notification to on-call team' : undefined
    };
  }

  private static validateDuplicatePrevention(lead: Partial<Lead>, context: BusinessRuleContext): BusinessRuleResult {
    // Mock duplicate check - in real implementation, this would query the database
    const isDuplicate = lead.email?.includes('duplicate');

    if (isDuplicate) {
      return {
        isValid: false,
        severity: 'warning',
        message: 'Potential duplicate lead detected',
        suggestedAction: 'Review existing lead record and consider merging'
      };
    }

    return {
      isValid: true,
      severity: 'info',
      message: 'No duplicate detected'
    };
  }

  private static validateLeadScoring(lead: Partial<Lead>, context: BusinessRuleContext): BusinessRuleResult {
    if (typeof lead.leadScore !== 'number') {
      return {
        isValid: false,
        severity: 'warning',
        message: 'Lead score not calculated',
        suggestedAction: 'Calculate lead score before routing'
      };
    }

    if (lead.leadScore < 0 || lead.leadScore > 100) {
      return {
        isValid: false,
        severity: 'error',
        message: `Invalid lead score: ${lead.leadScore} (must be 0-100)`,
        suggestedAction: 'Recalculate lead score'
      };
    }

    return {
      isValid: true,
      severity: 'info',
      message: `Lead score validated: ${lead.leadScore}`
    };
  }

  private static validateContactPreferences(lead: Partial<Lead>, context: BusinessRuleContext): BusinessRuleResult {
    // Check for contact preferences in custom fields
    const preferences = lead.customFields?.contactPreferences;
    
    if (!preferences) {
      return {
        isValid: true,
        severity: 'info',
        message: 'No specific contact preferences set'
      };
    }

    // Validate preference structure
    if (preferences.optOut && !preferences.reason) {
      return {
        isValid: false,
        severity: 'error',
        message: 'Opt-out preference requires reason',
        suggestedAction: 'Collect opt-out reason for compliance'
      };
    }

    return {
      isValid: true,
      severity: 'info',
      message: 'Contact preferences validated'
    };
  }

  private static validateEnterpriseRules(lead: Partial<Lead>, context: BusinessRuleContext): BusinessRuleResult {
    const isEnterprise = (
      (lead.companySize || 0) >= this.LEAD_QUALITY_THRESHOLDS.enterprise_min_company_size &&
      (lead.companyRevenue || 0) >= this.LEAD_QUALITY_THRESHOLDS.enterprise_min_revenue
    );

    if (isEnterprise) {
      // Additional validation for enterprise leads
      if (!lead.jobTitle || !['CEO', 'CTO', 'VP', 'Director'].some(title => 
        lead.jobTitle!.toLowerCase().includes(title.toLowerCase())
      )) {
        return {
          isValid: false,
          severity: 'warning',
          message: 'Enterprise lead without senior decision-maker title',
          suggestedAction: 'Verify contact authority and consider job title enrichment'
        };
      }
    }

    return {
      isValid: true,
      severity: 'info',
      message: isEnterprise ? 'Enterprise lead validation passed' : 'Standard lead validation passed'
    };
  }

  private static validateSourceSpecificRules(lead: Partial<Lead>, context: BusinessRuleContext): BusinessRuleResult {
    switch (lead.source) {
      case 'referral':
        if (!lead.customFields?.referrerInfo) {
          return {
            isValid: false,
            severity: 'warning',
            message: 'Referral lead missing referrer information',
            suggestedAction: 'Collect referrer details for tracking'
          };
        }
        break;

      case 'webinar':
        if (!lead.customFields?.webinarTitle) {
          return {
            isValid: false,
            severity: 'warning',
            message: 'Webinar lead missing webinar details',
            suggestedAction: 'Associate with specific webinar for follow-up'
          };
        }
        break;

      case 'trade_show':
        if (!lead.customFields?.eventName) {
          return {
            isValid: false,
            severity: 'warning',
            message: 'Trade show lead missing event information',
            suggestedAction: 'Record event details for context'
          };
        }
        break;
    }

    return {
      isValid: true,
      severity: 'info',
      message: `Source-specific validation passed for ${lead.source}`
    };
  }

  // Mock helper methods (in real implementation, these would integrate with other services)

  private static getUserCapacity(userId: string) {
    return { currentLeads: Math.floor(Math.random() * 20), maxLeads: 25 };
  }

  private static getUserSkills(userId: string) {
    return ['enterprise_sales', 'technology', 'cold_calling'];
  }

  private static getLeadRequirements(lead: Lead) {
    return {
      requiredSkills: lead.companySize && lead.companySize > 1000 ? ['enterprise_sales'] : ['sales']
    };
  }

  private static getWorkflowRules(workflowId: string) {
    return {
      prerequisites: [
        {
          description: 'Lead must be validated',
          suggestedAction: 'Run lead validation first'
        }
      ],
      businessHoursOnly: workflowId === 'voice_call_workflow',
      rateLimit: { maxExecutions: 100, windowMs: 60000 }
    };
  }

  private static checkPrerequisite(prerequisite: any, leadData: any, context: any) {
    // Mock prerequisite check
    return leadData.email && leadData.firstName;
  }

  private static getRecentWorkflowExecutions(workflowId: string, windowMs: number) {
    // Mock recent executions count
    return Math.floor(Math.random() * 10);
  }

  private static checkContentCompliance(content: string) {
    const issues = [];
    
    if (content.toLowerCase().includes('guaranteed')) {
      issues.push('Avoid absolute guarantees');
    }
    
    if (!content.includes('unsubscribe') && content.length > 100) {
      issues.push('Missing unsubscribe option');
    }
    
    return issues;
  }
}