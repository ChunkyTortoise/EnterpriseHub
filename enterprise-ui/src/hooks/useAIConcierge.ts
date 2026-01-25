/**
 * AI Concierge Hook - Simplified Integration for Components
 *
 * Provides easy access to AI Concierge functionality throughout the application.
 * Handles authentication, WebSocket connections, and state management automatically.
 *
 * Usage:
 * const { insights, startMonitoring, acceptInsight } = useAIConcierge('conversation-123');
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useWebSocket } from '@/components/providers/WebSocketProvider';
import { useAgentStore } from '@/store/useAgentStore';

interface ProactiveInsight {
  insight_id: string;
  insight_type: string;
  priority: string;
  title: string;
  description: string;
  reasoning: string;
  recommended_actions: string[];
  suggested_responses?: string[];
  confidence_score: number;
  expected_impact: number;
  created_at: string;
  expires_at: string;
  dismissed: boolean;
  acted_upon: boolean;
}

interface ConversationInsights {
  conversation_id: string;
  total_insights: number;
  active_insights: ProactiveInsight[];
  historical_insights: ProactiveInsight[];
  monitoring_status: string;
  performance_summary: {
    insights_generated: number;
    insights_accepted: number;
    average_effectiveness: number;
  };
}

interface AIConciergeMetrics {
  active_monitors: number;
  insights_per_hour: number;
  acceptance_rate: number;
  avg_confidence: number;
  avg_effectiveness: number;
  endpoint_performance: Record<string, any>;
}

interface UseAIConciergeOptions {
  autoConnect?: boolean;
  enableMetrics?: boolean;
  refreshInterval?: number;
}

export function useAIConcierge(
  conversationId: string,
  options: UseAIConciergeOptions = {}
) {
  const {
    autoConnect = true,
    enableMetrics = true,
    refreshInterval = 30000 // 30 seconds
  } = options;

  // State
  const [insights, setInsights] = useState<ConversationInsights | null>(null);
  const [metrics, setMetrics] = useState<AIConciergeMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Hooks
  const { connected } = useWebSocket();
  const { addEntry, addIntelligenceAlert, addPredictiveInsight } = useAgentStore();

  // Refs
  const wsRef = useRef<WebSocket | null>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Get auth token (in production this would be from auth context)
  const getAuthToken = useCallback(() => {
    return 'demo-token'; // Placeholder
  }, []);

  // Fetch conversation insights
  const fetchInsights = useCallback(async () => {
    try {
      const response = await fetch(
        `/api/v1/concierge/insights/${conversationId}?include_historical=true`,
        {
          headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch insights: ${response.status}`);
      }

      const data: ConversationInsights = await response.json();
      setInsights(data);
      setLastUpdate(new Date().toISOString());
      setError(null);

      // Track in agent store
      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'ai_concierge_hook',
        key: 'insights_refreshed',
        value: {
          conversation_id: conversationId,
          active_count: data.active_insights.length,
          total_count: data.total_insights
        }
      });

      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch insights';
      setError(errorMessage);
      console.error('AI Concierge fetch error:', errorMessage);
      throw err;
    }
  }, [conversationId, getAuthToken, addEntry]);

  // Fetch performance metrics
  const fetchMetrics = useCallback(async () => {
    if (!enableMetrics) return;

    try {
      const response = await fetch('/api/v1/concierge/performance', {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch metrics: ${response.status}`);
      }

      const data = await response.json();
      setMetrics(data);
    } catch (err) {
      console.error('Failed to fetch AI Concierge metrics:', err);
    }
  }, [enableMetrics, getAuthToken]);

  // Setup WebSocket connection
  const setupWebSocket = useCallback(() => {
    if (!connected || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const wsUrl = `ws://localhost:8000/api/v1/concierge/stream/${conversationId}?token=${getAuthToken()}`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      setIsConnected(true);
      setError(null);
      console.log('AI Concierge WebSocket connected');

      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'ai_concierge_hook',
        key: 'websocket_connected',
        value: { conversation_id: conversationId }
      });
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketEvent(data);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('AI Concierge WebSocket error:', error);
      setIsConnected(false);
      setError('WebSocket connection error');
    };

    wsRef.current.onclose = () => {
      setIsConnected(false);
      console.log('AI Concierge WebSocket disconnected');

      // Auto-reconnect after delay
      if (connected) {
        setTimeout(() => {
          setupWebSocket();
        }, 5000);
      }
    };
  }, [connected, conversationId, getAuthToken, addEntry]);

  // Handle WebSocket events
  const handleWebSocketEvent = useCallback((data: any) => {
    setLastUpdate(new Date().toISOString());

    switch (data.event_type) {
      case 'proactive_insight':
        // New insight - refresh data
        fetchInsights();

        addPredictiveInsight({
          type: 'trend_prediction',
          confidence: data.data.confidence_score || 0.8,
          title: data.data.title,
          description: data.data.description,
          timestamp: new Date().toISOString(),
          relevance_score: data.data.expected_impact || 0.7
        });
        break;

      case 'coaching_opportunity':
        addIntelligenceAlert({
          type: 'performance',
          severity: 'medium',
          title: 'New Coaching Opportunity',
          message: data.data.title || 'Coaching opportunity detected',
          timestamp: new Date().toISOString(),
          data: data.data
        });
        break;

      case 'strategy_recommendation':
        addPredictiveInsight({
          type: 'trend_prediction',
          confidence: data.data.impact_score || 0.8,
          title: `Strategy: ${data.data.strategy_title}`,
          description: data.data.strategy_description,
          recommended_action: data.data.conversation_pivot,
          timestamp: new Date().toISOString(),
          relevance_score: data.data.impact_score || 0.8
        });
        break;

      case 'heartbeat':
        // Just update timestamp - no action needed
        break;

      default:
        console.debug('Unhandled AI Concierge event:', data.event_type);
    }
  }, [fetchInsights, addPredictiveInsight, addIntelligenceAlert]);

  // Control monitoring
  const controlMonitoring = useCallback(async (action: 'start' | 'stop' | 'pause' | 'resume') => {
    try {
      const response = await fetch(`/api/v1/concierge/conversations/${conversationId}/monitoring`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action })
      });

      if (!response.ok) {
        throw new Error(`Failed to ${action} monitoring: ${response.status}`);
      }

      const result = await response.json();

      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'ai_concierge_hook',
        key: 'monitoring_control',
        value: { action, status: result.status }
      });

      // Refresh insights after monitoring state change
      if (action === 'start') {
        setTimeout(() => fetchInsights(), 1000);
      }

      return result;
    } catch (err) {
      console.error(`Failed to ${action} monitoring:`, err);
      throw err;
    }
  }, [conversationId, getAuthToken, addEntry, fetchInsights]);

  // Accept insight
  const acceptInsight = useCallback(async (insightId: string, notes?: string, effectiveness?: number) => {
    try {
      const response = await fetch(`/api/v1/concierge/insights/${insightId}/accept`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action_taken: notes || 'Accepted via useAIConcierge hook',
          implementation_notes: notes,
          effectiveness_prediction: effectiveness || 0.8
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to accept insight: ${response.status}`);
      }

      const result = await response.json();

      // Refresh insights
      await fetchInsights();

      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'ai_concierge_hook',
        key: 'insight_accepted',
        value: { insight_id: insightId, tracking_id: result.tracking_id }
      });

      return result;
    } catch (err) {
      console.error('Failed to accept insight:', err);
      throw err;
    }
  }, [getAuthToken, fetchInsights, addEntry]);

  // Dismiss insight
  const dismissInsight = useCallback(async (insightId: string, reason?: string, feedback?: string) => {
    try {
      const response = await fetch(`/api/v1/concierge/insights/${insightId}/dismiss`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          dismissal_reason: reason || 'not_relevant',
          feedback_notes: feedback
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to dismiss insight: ${response.status}`);
      }

      const result = await response.json();

      // Refresh insights
      await fetchInsights();

      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'ai_concierge_hook',
        key: 'insight_dismissed',
        value: { insight_id: insightId, reason, tracking_id: result.tracking_id }
      });

      return result;
    } catch (err) {
      console.error('Failed to dismiss insight:', err);
      throw err;
    }
  }, [getAuthToken, fetchInsights, addEntry]);

  // Convenience methods
  const startMonitoring = useCallback(() => controlMonitoring('start'), [controlMonitoring]);
  const stopMonitoring = useCallback(() => controlMonitoring('stop'), [controlMonitoring]);
  const pauseMonitoring = useCallback(() => controlMonitoring('pause'), [controlMonitoring]);
  const resumeMonitoring = useCallback(() => controlMonitoring('resume'), [controlMonitoring]);

  // Initialize
  useEffect(() => {
    const initialize = async () => {
      setIsLoading(true);

      try {
        await fetchInsights();
        if (enableMetrics) {
          await fetchMetrics();
        }

        if (autoConnect && connected) {
          setupWebSocket();
        }
      } catch (err) {
        console.error('Failed to initialize AI Concierge:', err);
      } finally {
        setIsLoading(false);
      }
    };

    initialize();
  }, [conversationId, autoConnect, connected, fetchInsights, fetchMetrics, setupWebSocket, enableMetrics]);

  // Setup refresh interval
  useEffect(() => {
    if (refreshInterval && refreshInterval > 0) {
      refreshIntervalRef.current = setInterval(() => {
        fetchInsights();
        if (enableMetrics) {
          fetchMetrics();
        }
      }, refreshInterval);
    }

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, [refreshInterval, fetchInsights, fetchMetrics, enableMetrics]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current);
      }
    };
  }, []);

  return {
    // Data
    insights,
    metrics,
    isLoading,
    isConnected,
    lastUpdate,
    error,

    // Control functions
    startMonitoring,
    stopMonitoring,
    pauseMonitoring,
    resumeMonitoring,
    controlMonitoring,

    // Insight actions
    acceptInsight,
    dismissInsight,

    // Manual refresh
    refresh: fetchInsights,
    refreshMetrics: fetchMetrics,

    // Connection control
    setupWebSocket,

    // Status helpers
    isMonitoring: insights?.monitoring_status === 'active',
    activeInsightCount: insights?.active_insights.length || 0,
    totalInsightCount: insights?.total_insights || 0,
    acceptanceRate: metrics?.acceptance_rate || 0,
    avgConfidence: metrics?.avg_confidence || 0
  };
}

export default useAIConcierge;