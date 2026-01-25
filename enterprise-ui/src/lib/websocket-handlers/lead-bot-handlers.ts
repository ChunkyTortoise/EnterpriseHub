/**
 * Lead Bot WebSocket Event Handlers
 *
 * Handles real-time events for Lead Bot 3-7-30 day sequences
 * Integrates with agent ecosystem and concierge stores
 */

import { useEffect } from 'react';
import { useAgentEcosystemStore } from '@/store/agentEcosystemStore';
import { useConciergeStore } from '@/store/claudeConciergeStore';
import type { SequenceStatusResponse } from '@/lib/api/lead-bot-api';

// Lead Bot WebSocket Event Types
interface LeadBotSequenceProgressEvent {
  type: 'lead_bot_sequence_progress';
  lead_id: string;
  current_day: 'DAY_3' | 'DAY_7' | 'DAY_14' | 'DAY_30';
  status: 'active' | 'paused' | 'completed' | 'failed';
  progress: {
    day_3_completed: boolean;
    day_7_completed: boolean;
    day_14_completed: boolean;
    day_30_completed: boolean;
    response_count: number;
    engagement_status: string;
  };
  next_action?: {
    action: string;
    scheduled_for?: string;
  };
  timestamp: string;
}

interface LeadBotActionExecutedEvent {
  type: 'lead_bot_action_executed';
  lead_id: string;
  action_type: 'sms' | 'call' | 'email';
  sequence_day: 'DAY_3' | 'DAY_7' | 'DAY_14' | 'DAY_30';
  success: boolean;
  duration_seconds?: number;
  engagement_score?: number;
  error_message?: string;
  executed_at: string;
}

interface LeadBotSchedulerHealthEvent {
  type: 'lead_bot_scheduler_health';
  status: 'healthy' | 'degraded' | 'failed' | 'not_started';
  active_jobs: number;
  scheduler_running: boolean;
  last_error?: string;
  timestamp: string;
}

interface LeadBotSequenceStateEvent {
  type: 'lead_bot_sequence_state_changed';
  lead_id: string;
  old_status: string;
  new_status: 'active' | 'paused' | 'completed' | 'failed';
  reason?: string;
  timestamp: string;
}

interface LeadResponseDetectedEvent {
  type: 'lead_response_detected';
  lead_id: string;
  response_method: 'sms' | 'call_answer' | 'email_reply';
  response_content?: string;
  sentiment?: 'positive' | 'negative' | 'neutral';
  detected_at: string;
}

export function useLeadBotWebSocketHandlers() {
  const {
    updateBotMetrics,
    setBotStatus,
    addBotEvent,
    updateBotConfig
  } = useAgentEcosystemStore();

  const {
    addInsight,
    updateSystemStatus
  } = useConciergeStore();

  useEffect(() => {
    const handleSequenceProgress = (event: LeadBotSequenceProgressEvent) => {
      console.log('[LeadBot] Sequence progress update:', event);

      // Update bot metrics with sequence progress
      updateBotMetrics('lead-bot', {
        activeSequences: 1,
        completedSequences: event.progress.day_30_completed ? 1 : 0,
        responseRate: event.progress.response_count > 0 ? 0.8 : 0.2,
        averageEngagementScore: event.progress.engagement_status === 'high' ? 0.9 :
                               event.progress.engagement_status === 'medium' ? 0.6 : 0.3,
        lastSequenceUpdate: event.timestamp,
        currentDay: event.current_day,
        leadId: event.lead_id
      });

      // Update bot status based on sequence state
      setBotStatus('lead-bot', event.status === 'active' ? 'active' :
                   event.status === 'paused' ? 'idle' : 'inactive');

      // Add timeline event
      addBotEvent('lead-bot', {
        timestamp: event.timestamp,
        type: 'sequence_progress',
        message: `Day ${event.current_day?.replace('DAY_', '')} - ${event.next_action?.action || 'Progress update'}`,
        data: {
          leadId: event.lead_id,
          currentDay: event.current_day,
          progress: event.progress,
          nextAction: event.next_action
        }
      });

      // Claude Concierge insight
      if (event.progress.response_count > 0) {
        addInsight('lead-engagement', {
          type: 'lead_response_detected',
          title: `Lead ${event.lead_id} Responded`,
          description: `Lead engagement detected on ${event.current_day}. Response count: ${event.progress.response_count}`,
          confidence: 0.9,
          suggestedAction: 'Review conversation and consider personalized follow-up',
          metadata: {
            leadId: event.lead_id,
            responseCount: event.progress.response_count,
            engagementStatus: event.progress.engagement_status
          },
          timestamp: event.timestamp
        });
      }
    };

    const handleActionExecuted = (event: LeadBotActionExecutedEvent) => {
      console.log('[LeadBot] Action executed:', event);

      // Add timeline event for action execution
      addBotEvent('lead-bot', {
        timestamp: event.executed_at,
        type: event.success ? 'action_success' : 'action_error',
        message: `${event.action_type.toUpperCase()} ${event.success ? 'delivered' : 'failed'} - ${event.sequence_day}`,
        data: {
          leadId: event.lead_id,
          actionType: event.action_type,
          sequenceDay: event.sequence_day,
          duration: event.duration_seconds,
          engagementScore: event.engagement_score,
          error: event.error_message
        }
      });

      // Update metrics with action results
      if (event.success && event.engagement_score) {
        updateBotMetrics('lead-bot', {
          lastActionSuccess: event.success,
          lastActionTime: event.executed_at,
          averageEngagementScore: event.engagement_score,
          totalActionsExecuted: (prev: number) => prev + 1
        });
      }

      // Claude Concierge insight for failed actions
      if (!event.success) {
        addInsight('sequence-failure', {
          type: 'action_failure',
          title: `Lead Bot Action Failed`,
          description: `${event.action_type} failed for lead ${event.lead_id} on ${event.sequence_day}`,
          confidence: 1.0,
          suggestedAction: event.error_message?.includes('phone') ?
            'Verify phone number and retry' : 'Check system logs and retry action',
          metadata: {
            leadId: event.lead_id,
            actionType: event.action_type,
            sequenceDay: event.sequence_day,
            errorMessage: event.error_message
          },
          timestamp: event.executed_at
        });
      }
    };

    const handleSchedulerHealth = (event: LeadBotSchedulerHealthEvent) => {
      console.log('[LeadBot] Scheduler health update:', event);

      // Update system status based on scheduler health
      updateSystemStatus('lead-bot-scheduler', {
        status: event.status,
        activeJobs: event.active_jobs,
        running: event.scheduler_running,
        lastError: event.last_error,
        lastUpdate: event.timestamp
      });

      // Update bot status based on scheduler health
      setBotStatus('lead-bot', event.scheduler_running && event.status === 'healthy' ? 'active' :
                   event.status === 'degraded' ? 'warning' : 'error');

      // Alert if scheduler is unhealthy
      if (event.status !== 'healthy') {
        addInsight('scheduler-health', {
          type: 'system_alert',
          title: 'Lead Bot Scheduler Issue',
          description: `Scheduler status: ${event.status}. ${event.last_error || 'Unknown issue'}`,
          confidence: 1.0,
          suggestedAction: event.status === 'failed' ? 'Restart scheduler immediately' :
                          'Monitor scheduler and prepare for restart if needed',
          metadata: {
            schedulerStatus: event.status,
            activeJobs: event.active_jobs,
            schedulerRunning: event.scheduler_running,
            lastError: event.last_error
          },
          timestamp: event.timestamp
        });
      }
    };

    const handleSequenceStateChanged = (event: LeadBotSequenceStateEvent) => {
      console.log('[LeadBot] Sequence state changed:', event);

      // Add timeline event for state change
      addBotEvent('lead-bot', {
        timestamp: event.timestamp,
        type: 'state_change',
        message: `Sequence ${event.old_status} → ${event.new_status}${event.reason ? ` (${event.reason})` : ''}`,
        data: {
          leadId: event.lead_id,
          oldStatus: event.old_status,
          newStatus: event.new_status,
          reason: event.reason
        }
      });

      // Claude Concierge insight for sequence completion
      if (event.new_status === 'completed') {
        addInsight('sequence-completion', {
          type: 'sequence_completed',
          title: `Sequence Completed`,
          description: `30-day sequence completed for lead ${event.lead_id}`,
          confidence: 1.0,
          suggestedAction: 'Review engagement results and plan next steps',
          metadata: {
            leadId: event.lead_id,
            completionReason: event.reason
          },
          timestamp: event.timestamp
        });
      }
    };

    const handleLeadResponse = (event: LeadResponseDetectedEvent) => {
      console.log('[LeadBot] Lead response detected:', event);

      // Update metrics with response detection
      updateBotMetrics('lead-bot', {
        totalResponses: (prev: number) => prev + 1,
        lastResponseTime: event.detected_at,
        responseRate: (prev: number) => Math.min(prev + 0.1, 1.0)
      });

      // Add timeline event
      addBotEvent('lead-bot', {
        timestamp: event.detected_at,
        type: 'lead_response',
        message: `Lead responded via ${event.response_method}${event.sentiment ? ` (${event.sentiment})` : ''}`,
        data: {
          leadId: event.lead_id,
          responseMethod: event.response_method,
          content: event.response_content,
          sentiment: event.sentiment
        }
      });

      // Claude Concierge insight for lead engagement
      addInsight('lead-engagement', {
        type: 'lead_response',
        title: 'Lead Response Detected',
        description: `Lead ${event.lead_id} responded via ${event.response_method}`,
        confidence: 0.95,
        suggestedAction: event.sentiment === 'positive' ?
          'Follow up with personalized message and schedule showing' :
          event.sentiment === 'negative' ? 'Address concerns and provide value' :
          'Continue with standard sequence while monitoring engagement',
        metadata: {
          leadId: event.lead_id,
          responseMethod: event.response_method,
          sentiment: event.sentiment,
          content: event.response_content
        },
        timestamp: event.detected_at
      });
    };

    // Return handlers for WebSocket setup
    return {
      lead_bot_sequence_progress: handleSequenceProgress,
      lead_bot_action_executed: handleActionExecuted,
      lead_bot_scheduler_health: handleSchedulerHealth,
      lead_bot_sequence_state_changed: handleSequenceStateChanged,
      lead_response_detected: handleLeadResponse
    };
  }, [updateBotMetrics, setBotStatus, addBotEvent, updateBotConfig, addInsight, updateSystemStatus]);
}