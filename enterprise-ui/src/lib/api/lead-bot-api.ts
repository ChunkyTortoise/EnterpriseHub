/**
 * Lead Bot API Service
 *
 * Manages Lead Bot 3-7-30 day sequence automation via backend API
 * Provides sequence creation, monitoring, and control capabilities
 */

import { ApiClient } from './client';

export interface CreateSequencePayload {
  lead_id: string;
  lead_name: string;
  phone: string;
  email?: string;
  property_address?: string;
  start_delay_minutes?: number;
}

export interface SequenceResponse {
  success: boolean;
  message: string;
  sequence_id?: string;
  scheduled_actions?: {
    day_3_sms?: string;
    day_7_call?: string;
    day_14_email?: string;
    day_30_sms?: string;
  };
}

export interface SequenceProgress {
  day_3_completed: boolean;
  day_7_completed: boolean;
  day_14_completed: boolean;
  day_30_completed: boolean;
  day_3_delivered_at?: string;
  day_7_delivered_at?: string;
  day_14_delivered_at?: string;
  day_30_delivered_at?: string;
  response_count: number;
  engagement_status: string;
}

export interface SequenceStatusResponse {
  lead_id: string;
  current_day?: 'DAY_3' | 'DAY_7' | 'DAY_14' | 'DAY_30';
  status: 'active' | 'paused' | 'completed' | 'failed';
  progress: SequenceProgress;
  next_action?: {
    action: string;
    scheduled_for?: string;
  };
  sequence_started_at?: string;
  last_activity_at?: string;
}

export interface SchedulerHealthResponse {
  status: 'healthy' | 'degraded' | 'failed' | 'not_started';
  uptime_seconds?: number;
  active_jobs: number;
  scheduler_running: boolean;
  last_error?: string;
}

export interface ManualTriggerPayload {
  lead_id: string;
  sequence_day: 'DAY_3' | 'DAY_7' | 'DAY_14' | 'DAY_30';
  action_type: 'sms' | 'call' | 'email';
}

export interface SequenceAction {
  type: 'success' | 'error';
  message: string;
}

export class LeadBotApiService {
  private apiClient: ApiClient;

  constructor() {
    this.apiClient = new ApiClient();
  }

  /**
   * Create a new 3-7-30 day lead sequence
   */
  async createSequence(payload: CreateSequencePayload): Promise<SequenceResponse> {
    return this.apiClient.post<SequenceResponse>('/api/lead-bot/sequences', payload);
  }

  /**
   * Get current status of a lead's sequence
   */
  async getSequenceStatus(leadId: string): Promise<SequenceStatusResponse> {
    return this.apiClient.get<SequenceStatusResponse>(`/api/lead-bot/sequences/${leadId}`);
  }

  /**
   * Pause an active sequence
   */
  async pauseSequence(leadId: string): Promise<SequenceAction> {
    return this.apiClient.post<SequenceAction>(`/api/lead-bot/sequences/${leadId}/pause`);
  }

  /**
   * Resume a paused sequence
   */
  async resumeSequence(leadId: string): Promise<SequenceAction> {
    return this.apiClient.post<SequenceAction>(`/api/lead-bot/sequences/${leadId}/resume`);
  }

  /**
   * Cancel an active sequence
   */
  async cancelSequence(leadId: string): Promise<SequenceAction> {
    return this.apiClient.post<SequenceAction>(`/api/lead-bot/sequences/${leadId}/cancel`);
  }

  /**
   * Get scheduler health status
   */
  async getSchedulerHealth(): Promise<SchedulerHealthResponse> {
    return this.apiClient.get<SchedulerHealthResponse>('/api/lead-bot/scheduler/status');
  }

  /**
   * Manually trigger a sequence action (testing/recovery)
   */
  async manualTrigger(payload: ManualTriggerPayload): Promise<{ success: boolean; message: string; executed_at: string }> {
    return this.apiClient.post<{ success: boolean; message: string; executed_at: string }>('/api/lead-bot/manual-trigger', payload);
  }

  /**
   * Create a test sequence for validation
   */
  async createTestSequence(leadId: string = 'test-lead-1'): Promise<{ success: boolean; message: string; lead_id: string; triggered_at: string }> {
    return this.apiClient.post<{ success: boolean; message: string; lead_id: string; triggered_at: string }>(`/api/lead-bot/test-sequence?lead_id=${leadId}`);
  }

  /**
   * Health check for load balancers
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.apiClient.get<{ status: string; timestamp: string }>('/api/lead-bot/health');
  }

  /**
   * Restart the scheduler (admin function)
   */
  async restartScheduler(): Promise<{ success: boolean; message: string; restarted_at?: string; error?: string }> {
    return this.apiClient.post<{ success: boolean; message: string; restarted_at?: string; error?: string }>('/api/lead-bot/scheduler/restart');
  }
}

// Export singleton instance
export const leadBotApi = new LeadBotApiService();