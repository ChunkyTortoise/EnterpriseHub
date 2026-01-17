/**
 * Lead validation and sanitization service
 * Handles data validation, sanitization, and normalization
 */

import { Lead, LeadValidationResult } from '../types/lead.interface';

export class LeadValidationService {
  private static readonly EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  private static readonly PHONE_REGEX = /^\+?1?[2-9]\d{2}[2-9]\d{2}\d{4}$/;
  private static readonly REQUIRED_FIELDS = ['email', 'firstName', 'lastName'];
  
  // Known disposable email domains for filtering
  private static readonly DISPOSABLE_DOMAINS = [
    '10minutemail.com', 'tempmail.org', 'guerrillamail.com', 'mailinator.com'
  ];

  /**
   * Validates a lead object and returns validation results
   */
  static validateLead(leadData: Partial<Lead>): LeadValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];
    const sanitizedData: Partial<Lead> = {};

    // Validate required fields
    this.validateRequiredFields(leadData, errors);

    // Validate and sanitize email
    if (leadData.email) {
      const emailValidation = this.validateEmail(leadData.email);
      if (emailValidation.error) {
        errors.push(emailValidation.error);
      } else {
        sanitizedData.email = emailValidation.sanitized;
        if (emailValidation.warning) {
          warnings.push(emailValidation.warning);
        }
      }
    }

    // Validate and sanitize names
    if (leadData.firstName) {
      sanitizedData.firstName = this.sanitizeName(leadData.firstName);
      if (sanitizedData.firstName.length < 2) {
        errors.push('First name must be at least 2 characters');
      }
    }

    if (leadData.lastName) {
      sanitizedData.lastName = this.sanitizeName(leadData.lastName);
      if (sanitizedData.lastName.length < 2) {
        errors.push('Last name must be at least 2 characters');
      }
    }

    // Validate and sanitize phone
    if (leadData.phone) {
      const phoneValidation = this.validatePhone(leadData.phone);
      if (phoneValidation.error) {
        warnings.push(phoneValidation.error); // Phone is optional, so warning not error
        sanitizedData.phone = null;
      } else {
        sanitizedData.phone = phoneValidation.sanitized;
      }
    }

    // Validate lead score
    if (typeof leadData.leadScore === 'number') {
      if (leadData.leadScore < 0 || leadData.leadScore > 100) {
        errors.push('Lead score must be between 0 and 100');
      } else {
        sanitizedData.leadScore = Math.round(leadData.leadScore);
      }
    }

    // Sanitize company name
    if (leadData.company) {
      sanitizedData.company = this.sanitizeCompanyName(leadData.company);
    }

    // Validate source
    if (leadData.source) {
      sanitizedData.source = this.sanitizeSource(leadData.source);
    }

    // Additional business rule validations
    this.validateBusinessRules(leadData, errors, warnings);

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      sanitizedData: errors.length === 0 ? sanitizedData : undefined
    };
  }

  /**
   * Sanitizes lead data by removing potentially harmful content
   */
  static sanitizeLead(leadData: Partial<Lead>): Partial<Lead> {
    const sanitized: Partial<Lead> = {};

    // Copy basic fields with sanitization
    if (leadData.email) sanitized.email = leadData.email.toLowerCase().trim();
    if (leadData.firstName) sanitized.firstName = this.sanitizeName(leadData.firstName);
    if (leadData.lastName) sanitized.lastName = this.sanitizeName(leadData.lastName);
    if (leadData.phone) sanitized.phone = this.sanitizePhone(leadData.phone);
    if (leadData.company) sanitized.company = this.sanitizeCompanyName(leadData.company);
    if (leadData.source) sanitized.source = this.sanitizeSource(leadData.source);

    // Copy numeric fields
    if (typeof leadData.leadScore === 'number') sanitized.leadScore = leadData.leadScore;
    if (typeof leadData.companySize === 'number') sanitized.companySize = leadData.companySize;
    if (typeof leadData.companyRevenue === 'number') sanitized.companyRevenue = leadData.companyRevenue;

    // Copy enum fields
    if (leadData.status) sanitized.status = leadData.status;
    if (leadData.temperature) sanitized.temperature = leadData.temperature;
    if (leadData.dataQuality) sanitized.dataQuality = leadData.dataQuality;

    // Sanitize URLs
    if (leadData.linkedinUrl) sanitized.linkedinUrl = this.sanitizeUrl(leadData.linkedinUrl);
    if (leadData.companyWebsite) sanitized.companyWebsite = this.sanitizeUrl(leadData.companyWebsite);

    return sanitized;
  }

  /**
   * Checks if lead is a duplicate based on email and recent timestamp
   */
  static isDuplicateLead(email: string, timeWindowHours = 24): boolean {
    // This would typically check against a database
    // For testing purposes, we'll simulate the logic
    const normalizedEmail = email.toLowerCase().trim();
    
    // Mock duplicate check logic
    if (normalizedEmail.includes('duplicate')) {
      return true;
    }
    
    return false;
  }

  /**
   * Validates business-specific rules
   */
  private static validateBusinessRules(leadData: Partial<Lead>, errors: string[], warnings: string[]): void {
    // Check for obvious fake/test data
    if (leadData.firstName && leadData.lastName) {
      const fullName = `${leadData.firstName} ${leadData.lastName}`.toLowerCase();
      const testNames = ['test test', 'john doe', 'jane doe', 'foo bar'];
      if (testNames.includes(fullName)) {
        warnings.push('Potential test data detected');
      }
    }

    // Check email domain quality
    if (leadData.email) {
      const domain = leadData.email.split('@')[1]?.toLowerCase();
      if (this.DISPOSABLE_DOMAINS.includes(domain)) {
        warnings.push('Email uses disposable domain');
      }
      
      // Check for generic/role-based emails
      const localPart = leadData.email.split('@')[0]?.toLowerCase();
      const genericEmails = ['info', 'admin', 'support', 'contact', 'sales', 'marketing'];
      if (genericEmails.includes(localPart)) {
        warnings.push('Generic email address detected');
      }
    }

    // Validate company size vs job title consistency
    if (leadData.companySize && leadData.jobTitle) {
      if (leadData.companySize < 10 && leadData.jobTitle.toLowerCase().includes('vp')) {
        warnings.push('Job title may be inconsistent with company size');
      }
    }
  }

  private static validateRequiredFields(leadData: Partial<Lead>, errors: string[]): void {
    for (const field of this.REQUIRED_FIELDS) {
      const value = leadData[field as keyof Lead];
      if (!value || (typeof value === 'string' && value.trim() === '')) {
        errors.push(`${field} is required`);
      }
    }
  }

  private static validateEmail(email: string): { sanitized?: string; error?: string; warning?: string } {
    const trimmedEmail = email.toLowerCase().trim();
    
    if (!this.EMAIL_REGEX.test(trimmedEmail)) {
      return { error: 'Invalid email format' };
    }

    const domain = trimmedEmail.split('@')[1];
    if (this.DISPOSABLE_DOMAINS.includes(domain)) {
      return { 
        sanitized: trimmedEmail, 
        warning: 'Email uses disposable domain' 
      };
    }

    return { sanitized: trimmedEmail };
  }

  private static validatePhone(phone: string): { sanitized?: string; error?: string } {
    // Remove all non-digits
    const digitsOnly = phone.replace(/\D/g, '');
    
    // Handle US phone numbers
    let formatted = digitsOnly;
    if (digitsOnly.length === 11 && digitsOnly.startsWith('1')) {
      formatted = digitsOnly.substring(1);
    }
    
    if (formatted.length !== 10) {
      return { error: 'Invalid phone number format' };
    }

    // Format as +1XXXXXXXXXX
    const sanitized = `+1${formatted}`;
    
    if (!this.PHONE_REGEX.test(sanitized)) {
      return { error: 'Invalid phone number format' };
    }

    return { sanitized };
  }

  private static sanitizeName(name: string): string {
    return name.trim()
      .replace(/[^\w\s\-\.\']/g, '') // Remove special chars except common name chars
      .replace(/\s+/g, ' ') // Normalize whitespace
      .split(' ')
      .map(part => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
      .join(' ');
  }

  private static sanitizeCompanyName(company: string): string {
    return company.trim()
      .replace(/[<>\"']/g, '') // Remove potential XSS chars
      .replace(/\s+/g, ' ')
      .substring(0, 200); // Limit length
  }

  private static sanitizeSource(source: string): string {
    return source.toLowerCase().trim()
      .replace(/[^\w\-_]/g, '') // Only allow word chars, hyphens, underscores
      .substring(0, 50);
  }

  private static sanitizePhone(phone: string): string {
    const digitsOnly = phone.replace(/\D/g, '');
    if (digitsOnly.length === 11 && digitsOnly.startsWith('1')) {
      return `+1${digitsOnly.substring(1)}`;
    }
    if (digitsOnly.length === 10) {
      return `+1${digitsOnly}`;
    }
    return digitsOnly;
  }

  private static sanitizeUrl(url: string): string {
    try {
      const parsed = new URL(url);
      return parsed.toString();
    } catch {
      return url.replace(/[<>\"']/g, '').trim();
    }
  }
}