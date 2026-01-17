/**
 * Test data factories for Lead entities
 * Generates realistic test data for comprehensive testing
 */

import { v4 as uuidv4 } from 'uuid';
import { Lead, LeadStatus, LeadTemperature, DataQuality, CommunicationRecord, WorkflowExecution } from '../../src/types/lead.interface';

export class LeadFactory {
  private static domains = ['gmail.com', 'yahoo.com', 'company.com', 'startup.io', 'enterprise.com'];
  private static companies = ['TechCorp', 'InnovateLLC', 'StartupInc', 'BigEnterprise', 'LocalBusiness'];
  private static jobTitles = ['CEO', 'CTO', 'VP Sales', 'Marketing Director', 'Senior Developer', 'Account Manager'];
  private static industries = ['Technology', 'Healthcare', 'Finance', 'Manufacturing', 'Retail', 'Education'];
  private static sources = ['website', 'linkedin', 'referral', 'cold_outreach', 'webinar', 'trade_show'];

  static createValidLead(overrides: Partial<Lead> = {}): Lead {
    const firstName = this.generateRandomFirstName();
    const lastName = this.generateRandomLastName();
    const company = this.getRandomElement(this.companies);
    
    return {
      id: uuidv4(),
      email: `${firstName.toLowerCase()}.${lastName.toLowerCase()}@${this.getRandomElement(this.domains)}`,
      firstName,
      lastName,
      phone: this.generateRandomPhone(),
      company,
      source: this.getRandomElement(this.sources),
      leadScore: Math.floor(Math.random() * 100),
      temperature: this.getRandomElement(['hot', 'warm', 'cold', 'unknown'] as LeadTemperature[]),
      status: this.getRandomElement(['new', 'contacted', 'qualified'] as LeadStatus[]),
      jobTitle: this.getRandomElement(this.jobTitles),
      companyIndustry: this.getRandomElement(this.industries),
      companySize: this.generateRandomCompanySize(),
      dataQuality: 'basic' as DataQuality,
      createdAt: new Date(),
      updatedAt: new Date(),
      lastActivity: new Date(),
      tags: [],
      customFields: {},
      ...overrides
    };
  }

  static createInvalidLead(invalidField: string): Partial<Lead> {
    const baseLead = this.createValidLead();
    
    switch (invalidField) {
      case 'email':
        return { ...baseLead, email: 'invalid-email' };
      case 'firstName':
        return { ...baseLead, firstName: '' };
      case 'lastName':
        return { ...baseLead, lastName: '' };
      case 'phone':
        return { ...baseLead, phone: '123' }; // Too short
      case 'leadScore':
        return { ...baseLead, leadScore: 150 }; // Out of range
      default:
        return baseLead;
    }
  }

  static createLeadWithEnrichment(overrides: Partial<Lead> = {}): Lead {
    return this.createValidLead({
      apolloId: `apollo_${uuidv4()}`,
      linkedinUrl: `https://linkedin.com/in/${Math.random().toString(36).substring(7)}`,
      jobTitle: this.getRandomElement(this.jobTitles),
      seniority: this.getRandomElement(['C-Level', 'VP', 'Director', 'Manager', 'Individual Contributor']),
      companyLinkedin: `https://linkedin.com/company/${Math.random().toString(36).substring(7)}`,
      companyWebsite: `https://www.${Math.random().toString(36).substring(7)}.com`,
      companyRevenue: Math.floor(Math.random() * 100000000),
      dataQuality: 'enriched' as DataQuality,
      ...overrides
    });
  }

  static createHighScoreLead(overrides: Partial<Lead> = {}): Lead {
    return this.createLeadWithEnrichment({
      leadScore: Math.floor(Math.random() * 20) + 80, // 80-100
      temperature: 'hot' as LeadTemperature,
      jobTitle: this.getRandomElement(['CEO', 'CTO', 'VP Sales']),
      companySize: Math.floor(Math.random() * 5000) + 1000, // 1000+ employees
      source: 'referral',
      ...overrides
    });
  }

  static createLowScoreLead(overrides: Partial<Lead> = {}): Lead {
    return this.createValidLead({
      leadScore: Math.floor(Math.random() * 30), // 0-30
      temperature: 'cold' as LeadTemperature,
      companySize: Math.floor(Math.random() * 50) + 1, // 1-50 employees
      source: 'cold_outreach',
      ...overrides
    });
  }

  static createBatchOfLeads(count: number, template?: Partial<Lead>): Lead[] {
    return Array.from({ length: count }, () => this.createValidLead(template));
  }

  static createCommunicationRecord(leadId: string, overrides: Partial<CommunicationRecord> = {}): CommunicationRecord {
    return {
      id: uuidv4(),
      leadId,
      channel: this.getRandomElement(['email', 'sms', 'call'] as any),
      direction: this.getRandomElement(['inbound', 'outbound'] as any),
      status: this.getRandomElement(['sent', 'delivered', 'opened'] as any),
      subject: 'Test Subject',
      message: 'Test message content',
      sentAt: new Date(),
      metadata: {},
      ...overrides
    };
  }

  static createWorkflowExecution(leadId: string, overrides: Partial<WorkflowExecution> = {}): WorkflowExecution {
    return {
      id: uuidv4(),
      workflowId: 'instant-lead-response',
      leadId,
      status: 'completed',
      startedAt: new Date(),
      completedAt: new Date(),
      steps: [
        {
          id: uuidv4(),
          name: 'Lead Validation',
          status: 'completed',
          executedAt: new Date(),
          duration: 50
        },
        {
          id: uuidv4(),
          name: 'Lead Enrichment',
          status: 'completed',
          executedAt: new Date(),
          duration: 200
        }
      ],
      ...overrides
    };
  }

  private static generateRandomFirstName(): string {
    const names = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Lisa', 'James', 'Maria'];
    return this.getRandomElement(names);
  }

  private static generateRandomLastName(): string {
    const names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Davis', 'Miller', 'Wilson', 'Taylor', 'Anderson', 'Thomas'];
    return this.getRandomElement(names);
  }

  private static generateRandomPhone(): string {
    const areaCode = Math.floor(Math.random() * 900) + 100;
    const exchange = Math.floor(Math.random() * 900) + 100;
    const number = Math.floor(Math.random() * 9000) + 1000;
    return `+1${areaCode}${exchange}${number}`;
  }

  private static generateRandomCompanySize(): number {
    const sizes = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000];
    return this.getRandomElement(sizes);
  }

  private static getRandomElement<T>(array: T[]): T {
    return array[Math.floor(Math.random() * array.length)];
  }
}

export class TestDataSeeds {
  static getValidLeadScenarios() {
    return [
      { name: 'Basic Lead', data: LeadFactory.createValidLead() },
      { name: 'Enriched Lead', data: LeadFactory.createLeadWithEnrichment() },
      { name: 'High Score Lead', data: LeadFactory.createHighScoreLead() },
      { name: 'Low Score Lead', data: LeadFactory.createLowScoreLead() },
      { name: 'Enterprise Lead', data: LeadFactory.createValidLead({ companySize: 5000, jobTitle: 'CEO' }) },
      { name: 'Startup Lead', data: LeadFactory.createValidLead({ companySize: 10, jobTitle: 'Founder' }) }
    ];
  }

  static getInvalidLeadScenarios() {
    return [
      { name: 'Invalid Email', data: LeadFactory.createInvalidLead('email'), expectedError: 'Invalid email format' },
      { name: 'Missing First Name', data: LeadFactory.createInvalidLead('firstName'), expectedError: 'First name is required' },
      { name: 'Missing Last Name', data: LeadFactory.createInvalidLead('lastName'), expectedError: 'Last name is required' },
      { name: 'Invalid Phone', data: LeadFactory.createInvalidLead('phone'), expectedError: 'Invalid phone format' },
      { name: 'Invalid Score', data: LeadFactory.createInvalidLead('leadScore'), expectedError: 'Lead score must be 0-100' }
    ];
  }
}