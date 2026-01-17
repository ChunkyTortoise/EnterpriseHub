/**
 * Data transformation service
 * Handles data mapping, normalization, and enrichment workflows
 */

import { Lead, EnrichmentData, CommunicationRecord } from '../types/lead.interface';

export class DataTransformationService {
  /**
   * Transforms raw webhook data into standardized lead format
   */
  static transformWebhookData(webhookData: Record<string, any>, source: string): Partial<Lead> {
    const transformed: Partial<Lead> = {
      source,
      createdAt: new Date(),
      updatedAt: new Date(),
      lastActivity: new Date(),
      dataQuality: 'basic'
    };

    // Email field mapping variations
    const emailField = this.findFieldValue(webhookData, [
      'email', 'email_address', 'emailAddress', 'userEmail', 'contactEmail'
    ]);
    if (emailField) transformed.email = emailField;

    // Name field mapping
    const firstNameField = this.findFieldValue(webhookData, [
      'firstName', 'first_name', 'fname', 'given_name', 'givenName'
    ]);
    if (firstNameField) transformed.firstName = firstNameField;

    const lastNameField = this.findFieldValue(webhookData, [
      'lastName', 'last_name', 'lname', 'family_name', 'familyName', 'surname'
    ]);
    if (lastNameField) transformed.lastName = lastNameField;

    // Handle full name field if separate names not available
    if (!firstNameField || !lastNameField) {
      const fullNameField = this.findFieldValue(webhookData, [
        'fullName', 'full_name', 'name', 'displayName', 'contact_name'
      ]);
      if (fullNameField) {
        const nameParts = this.splitFullName(fullNameField);
        if (!firstNameField) transformed.firstName = nameParts.firstName;
        if (!lastNameField) transformed.lastName = nameParts.lastName;
      }
    }

    // Phone field mapping
    const phoneField = this.findFieldValue(webhookData, [
      'phone', 'phoneNumber', 'phone_number', 'mobile', 'cell', 'telephone'
    ]);
    if (phoneField) transformed.phone = phoneField;

    // Company field mapping
    const companyField = this.findFieldValue(webhookData, [
      'company', 'companyName', 'company_name', 'organization', 'employer'
    ]);
    if (companyField) transformed.company = companyField;

    // Job title mapping
    const jobTitleField = this.findFieldValue(webhookData, [
      'jobTitle', 'job_title', 'title', 'position', 'role'
    ]);
    if (jobTitleField) transformed.jobTitle = jobTitleField;

    // Custom fields
    transformed.customFields = this.extractCustomFields(webhookData, transformed);

    return transformed;
  }

  /**
   * Enriches lead data with external data source
   */
  static enrichLeadData(lead: Partial<Lead>, enrichmentData: EnrichmentData): Partial<Lead> {
    const enriched = { ...lead };

    // Update data quality
    enriched.dataQuality = 'enriched';
    enriched.updatedAt = new Date();

    // Personal enrichment
    if (enrichmentData.data.personal) {
      const personal = enrichmentData.data.personal;
      if (personal.linkedinUrl) enriched.linkedinUrl = personal.linkedinUrl;
      if (personal.jobTitle) enriched.jobTitle = personal.jobTitle;
      if (personal.seniority) enriched.seniority = personal.seniority;
    }

    // Company enrichment
    if (enrichmentData.data.company) {
      const company = enrichmentData.data.company;
      if (company.name && !enriched.company) enriched.company = company.name;
      if (company.industry) enriched.companyIndustry = company.industry;
      if (company.size) enriched.companySize = company.size;
      if (company.revenue) enriched.companyRevenue = company.revenue;
      if (company.website) enriched.companyWebsite = company.website;
      if (company.linkedinUrl) enriched.companyLinkedin = company.linkedinUrl;
    }

    // Set Apollo ID if from Apollo
    if (enrichmentData.source === 'apollo') {
      enriched.apolloId = `apollo_${Date.now()}`;
    }

    return enriched;
  }

  /**
   * Normalizes lead data across different CRM formats
   */
  static normalizeCRMData(crmData: Record<string, any>, crmType: 'hubspot' | 'salesforce' | 'ghl'): Partial<Lead> {
    const normalized: Partial<Lead> = {};

    switch (crmType) {
      case 'hubspot':
        return this.normalizeHubSpotData(crmData);
      case 'salesforce':
        return this.normalizeSalesforceData(crmData);
      case 'ghl':
        return this.normalizeGHLData(crmData);
      default:
        throw new Error(`Unsupported CRM type: ${crmType}`);
    }
  }

  /**
   * Transforms communication records for analytics
   */
  static transformCommunicationData(
    communications: CommunicationRecord[]
  ): Record<string, any> {
    const summary = {
      totalCommunications: communications.length,
      byChannel: {} as Record<string, number>,
      byDirection: {} as Record<string, number>,
      byStatus: {} as Record<string, number>,
      engagementMetrics: {
        opens: 0,
        clicks: 0,
        replies: 0,
        deliveryRate: 0
      },
      timeline: this.generateTimelineSummary(communications)
    };

    communications.forEach(comm => {
      // Count by channel
      summary.byChannel[comm.channel] = (summary.byChannel[comm.channel] || 0) + 1;
      
      // Count by direction
      summary.byDirection[comm.direction] = (summary.byDirection[comm.direction] || 0) + 1;
      
      // Count by status
      summary.byStatus[comm.status] = (summary.byStatus[comm.status] || 0) + 1;

      // Engagement metrics
      if (comm.openedAt) summary.engagementMetrics.opens++;
      if (comm.clickedAt) summary.engagementMetrics.clicks++;
      if (comm.repliedAt) summary.engagementMetrics.replies++;
    });

    // Calculate delivery rate
    const sentMessages = communications.filter(c => c.status === 'sent' || c.status === 'delivered').length;
    summary.engagementMetrics.deliveryRate = communications.length > 0 
      ? sentMessages / communications.length 
      : 0;

    return summary;
  }

  /**
   * Merges duplicate lead records
   */
  static mergeLeadRecords(primary: Lead, duplicate: Lead): Lead {
    const merged = { ...primary };

    // Use more complete data from either record
    Object.keys(duplicate).forEach(key => {
      const primaryValue = primary[key as keyof Lead];
      const duplicateValue = duplicate[key as keyof Lead];

      // Use duplicate value if primary is empty/null
      if (!primaryValue && duplicateValue) {
        (merged as any)[key] = duplicateValue;
      }

      // For specific fields, prefer higher quality data
      if (key === 'dataQuality') {
        const qualityOrder = ['basic', 'enriched', 'validated', 'premium'];
        const primaryIndex = qualityOrder.indexOf(primaryValue as string);
        const duplicateIndex = qualityOrder.indexOf(duplicateValue as string);
        if (duplicateIndex > primaryIndex) {
          merged.dataQuality = duplicate.dataQuality;
        }
      }
    });

    // Merge tags
    if (duplicate.tags && duplicate.tags.length > 0) {
      merged.tags = [...(merged.tags || []), ...duplicate.tags].filter((tag, index, arr) => 
        arr.indexOf(tag) === index
      );
    }

    // Merge custom fields
    if (duplicate.customFields) {
      merged.customFields = { ...merged.customFields, ...duplicate.customFields };
    }

    // Update timestamps
    merged.updatedAt = new Date();
    
    return merged;
  }

  /**
   * Validates data transformation results
   */
  static validateTransformation(original: any, transformed: Partial<Lead>): {
    isValid: boolean;
    errors: string[];
    warnings: string[];
  } {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check required fields are preserved
    if (original.email && !transformed.email) {
      errors.push('Email lost during transformation');
    }

    if ((original.firstName || original.first_name) && !transformed.firstName) {
      warnings.push('First name lost during transformation');
    }

    if ((original.lastName || original.last_name) && !transformed.lastName) {
      warnings.push('Last name lost during transformation');
    }

    // Check data format consistency
    if (transformed.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(transformed.email)) {
      errors.push('Invalid email format after transformation');
    }

    if (transformed.phone && transformed.phone.replace(/\D/g, '').length < 10) {
      warnings.push('Phone number may be incomplete after transformation');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    };
  }

  // Private helper methods

  private static findFieldValue(data: Record<string, any>, fieldNames: string[]): string | null {
    for (const fieldName of fieldNames) {
      if (data[fieldName] && typeof data[fieldName] === 'string') {
        return data[fieldName].trim();
      }
    }
    return null;
  }

  private static splitFullName(fullName: string): { firstName: string; lastName: string } {
    const parts = fullName.trim().split(/\s+/);
    
    if (parts.length === 1) {
      return { firstName: parts[0], lastName: '' };
    } else if (parts.length === 2) {
      return { firstName: parts[0], lastName: parts[1] };
    } else {
      // Multiple parts - first is firstName, rest is lastName
      return { 
        firstName: parts[0], 
        lastName: parts.slice(1).join(' ') 
      };
    }
  }

  private static extractCustomFields(
    webhookData: Record<string, any>, 
    standardFields: Partial<Lead>
  ): Record<string, any> {
    const customFields: Record<string, any> = {};
    const standardFieldNames = Object.keys(standardFields);

    Object.keys(webhookData).forEach(key => {
      if (!standardFieldNames.includes(key) && 
          !this.isStandardWebhookField(key)) {
        customFields[key] = webhookData[key];
      }
    });

    return customFields;
  }

  private static isStandardWebhookField(fieldName: string): boolean {
    const standardFields = [
      'email', 'email_address', 'emailAddress', 'userEmail', 'contactEmail',
      'firstName', 'first_name', 'fname', 'given_name', 'givenName',
      'lastName', 'last_name', 'lname', 'family_name', 'familyName', 'surname',
      'fullName', 'full_name', 'name', 'displayName', 'contact_name',
      'phone', 'phoneNumber', 'phone_number', 'mobile', 'cell', 'telephone',
      'company', 'companyName', 'company_name', 'organization', 'employer',
      'jobTitle', 'job_title', 'title', 'position', 'role'
    ];

    return standardFields.includes(fieldName);
  }

  private static normalizeHubSpotData(hubspotData: Record<string, any>): Partial<Lead> {
    const properties = hubspotData.properties || hubspotData;
    
    return {
      email: properties.email,
      firstName: properties.firstname,
      lastName: properties.lastname,
      phone: properties.phone,
      company: properties.company,
      jobTitle: properties.jobtitle,
      source: 'hubspot',
      dataQuality: 'enriched'
    };
  }

  private static normalizeSalesforceData(sfData: Record<string, any>): Partial<Lead> {
    return {
      email: sfData.Email,
      firstName: sfData.FirstName,
      lastName: sfData.LastName,
      phone: sfData.Phone,
      company: sfData.Company,
      jobTitle: sfData.Title,
      source: 'salesforce',
      dataQuality: 'enriched'
    };
  }

  private static normalizeGHLData(ghlData: Record<string, any>): Partial<Lead> {
    return {
      email: ghlData.email,
      firstName: ghlData.firstName,
      lastName: ghlData.lastName,
      phone: ghlData.phone,
      company: ghlData.companyName,
      source: 'ghl',
      dataQuality: 'enriched'
    };
  }

  private static generateTimelineSummary(communications: CommunicationRecord[]): any {
    const timeline: Record<string, number> = {};
    
    communications.forEach(comm => {
      const date = comm.sentAt.toISOString().split('T')[0]; // YYYY-MM-DD
      timeline[date] = (timeline[date] || 0) + 1;
    });

    return timeline;
  }
}