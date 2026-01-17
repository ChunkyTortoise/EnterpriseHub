/**
 * Lead-related type definitions for the Lead Recovery & Nurture Engine
 */

export type LeadStatus = 'new' | 'contacted' | 'qualified' | 'disqualified' | 'converted' | 'lost';
export type LeadTemperature = 'hot' | 'warm' | 'cold' | 'unknown';
export type CommunicationChannel = 'email' | 'sms' | 'call' | 'voicemail' | 'linkedin' | 'other';
export type CommunicationDirection = 'inbound' | 'outbound';
export type CommunicationStatus = 'sent' | 'delivered' | 'opened' | 'clicked' | 'replied' | 'failed' | 'bounced';
export type DataQuality = 'basic' | 'enriched' | 'validated' | 'premium';

export interface Lead {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  phone?: string;
  company?: string;
  source: string;
  leadScore: number;
  temperature: LeadTemperature;
  status: LeadStatus;
  apolloId?: string;
  linkedinUrl?: string;
  jobTitle?: string;
  seniority?: string;
  companyLinkedin?: string;
  companyIndustry?: string;
  companySize?: number;
  companyRevenue?: number;
  companyWebsite?: string;
  scoringReasoning?: string;
  dataQuality: DataQuality;
  assignedTo?: string;
  routingRules?: string;
  createdAt: Date;
  updatedAt: Date;
  lastActivity: Date;
  timezone?: string;
  tags?: string[];
  customFields?: Record<string, any>;
}

export interface LeadValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  sanitizedData?: Partial<Lead>;
}

export interface LeadScoringFactors {
  emailDomain: number;
  companySize: number;
  jobSeniority: number;
  industry: number;
  behavioralSignals: number;
  engagementHistory: number;
  leadSource: number;
  firmographics: number;
}

export interface LeadScoringResult {
  score: number;
  factors: LeadScoringFactors;
  reasoning: string;
  confidence: number;
  recommendations: string[];
}

export interface CommunicationRecord {
  id: string;
  leadId: string;
  channel: CommunicationChannel;
  direction: CommunicationDirection;
  status: CommunicationStatus;
  subject?: string;
  message: string;
  sentAt: Date;
  deliveredAt?: Date;
  openedAt?: Date;
  clickedAt?: Date;
  repliedAt?: Date;
  metadata?: Record<string, any>;
}

export interface WorkflowExecution {
  id: string;
  workflowId: string;
  leadId: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  startedAt: Date;
  completedAt?: Date;
  steps: WorkflowStep[];
  errors?: string[];
  metadata?: Record<string, any>;
}

export interface WorkflowStep {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  executedAt?: Date;
  duration?: number;
  input?: Record<string, any>;
  output?: Record<string, any>;
  error?: string;
}

export interface EnrichmentData {
  source: 'apollo' | 'clearbit' | 'zoominfo' | 'manual';
  confidence: number;
  data: {
    personal?: {
      linkedinUrl?: string;
      jobTitle?: string;
      seniority?: string;
      skills?: string[];
    };
    company?: {
      name?: string;
      industry?: string;
      size?: number;
      revenue?: number;
      website?: string;
      linkedinUrl?: string;
      technologies?: string[];
    };
  };
  enrichedAt: Date;
}