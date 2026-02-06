
import { create } from 'zustand';
import { subscribeWithSelector } from 'zustand/middleware';

interface BlackboardEntry {
  timestamp: string;
  agent: string;
  key: string;
  value: any;
}

interface IntelligenceAlert {
  id: string;
  type: 'anomaly' | 'performance' | 'revenue' | 'bot_failure';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  data?: any;
}

interface PredictiveInsight {
  id: string;
  type: 'trend_prediction' | 'revenue_forecast' | 'performance_warning';
  confidence: number;
  title: string;
  description: string;
  recommended_action?: string;
  timestamp: string;
  relevance_score: number;
}

interface DashboardMetric {
  component: string;
  data: any;
  last_updated: string;
  cache_hit: boolean;
}

interface IntelligenceState extends AgentState {
  // BI Dashboard State
  dashboardMetrics: Record<string, DashboardMetric>;
  liveAlerts: IntelligenceAlert[];
  predictiveInsights: PredictiveInsight[];

  // WebSocket Connections
  activeConnections: Map<string, WebSocket>;
  connectionStatus: Record<string, 'connected' | 'disconnected' | 'connecting' | 'error'>;

  // Real-time Intelligence Methods
  updateDashboardMetric: (component: string, values: any) => void;
  addIntelligenceAlert: (alert: Omit<IntelligenceAlert, 'id'>) => void;
  acknowledgeAlert: (alertId: string) => void;
  addPredictiveInsight: (insight: Omit<PredictiveInsight, 'id'>) => void;
  subscribeToIntelligence: (components: string[]) => () => void;

  // Enhanced BI WebSocket Subscriptions (Phase 7)
  connectBIWebSockets: (locationId: string) => void;
  disconnectBIWebSockets: () => void;
  getBIConnectionHealth: () => { connected: number; total: number; status: string };

  // WebSocket Management
  connectWebSocket: (endpoint: string, identifier: string) => void;
  disconnectWebSocket: (identifier: string) => void;
  getConnectionStatus: (identifier: string) => string;

  // Analytics & Metrics
  getMetricHistory: (component: string, limit?: number) => BlackboardEntry[];
  getInsightsByType: (type: string) => PredictiveInsight[];
  getAlertsByType: (type: string) => IntelligenceAlert[];
  getSystemHealth: () => { status: string; details: any };

  // Cache & Performance
  clearStaleData: (maxAge: number) => void;
  getPerformanceMetrics: () => any;
}

interface AgentState {
  history: BlackboardEntry[];
  thinking: string;
  currentDeltas: Record<string, any>;
  isGenerating: boolean;
  addEntry: (entry: BlackboardEntry) => void;
  setThinking: (thought: string) => void;
  startStreaming: () => void;
}

const intelligenceEventTypes = [
  'REALTIME_BI_UPDATE',     // Live metric updates
  'DRILL_DOWN_DATA',        // Interactive exploration results
  'ANOMALY_ALERT',          // Predictive performance warnings
  'REVENUE_PIPELINE_CHANGE', // Commission calculations
  'BOT_COORDINATION_UPDATE', // Multi-bot status
  'PERFORMANCE_WARNING',     // System performance alerts
  'JORGE_QUALIFICATION_PROGRESS', // Jorge bot progress
  'LEAD_BOT_SEQUENCE_UPDATE', // Lead bot lifecycle updates
  'SMS_COMPLIANCE',         // Compliance events
  'SYSTEM_HEALTH_UPDATE',   // Component health status

  // Phase 8: AI Concierge Events
  'AI_CONCIERGE_INSIGHT',   // New proactive insight generated
  'COACHING_OPPORTUNITY',   // Coaching opportunity detected
  'STRATEGY_RECOMMENDATION', // Strategy recommendation
  'CONVERSATION_QUALITY'    // Conversation quality assessment
];

export const useAgentStore = create<IntelligenceState>()(
  subscribeWithSelector((set, get) => ({
    // Original AgentState
    history: [],
    thinking: '',
    currentDeltas: {},
    isGenerating: false,

    // Enhanced BI Dashboard State
    dashboardMetrics: {},
    liveAlerts: [],
    predictiveInsights: [],
    activeConnections: new Map(),
    connectionStatus: {},

    addEntry: (entry) => {
      set((state) => {
        const newHistory = [...state.history, entry];

        // Keep history manageable (last 1000 entries)
        const trimmedHistory = newHistory.length > 1000 ? newHistory.slice(-1000) : newHistory;

        return {
          history: trimmedHistory,
          // If the key is a UI component, update deltas
          currentDeltas: entry.key.startsWith('ui_component_')
            ? { ...state.currentDeltas, [entry.key]: entry.value }
            : state.currentDeltas,
          // Update thinking if it's a thought key
          thinking: entry.key === 'agent_thought' ? entry.value : state.thinking
        };
      });
    },

    setThinking: (thought) => set({ thinking: thought }),

    startStreaming: () => {
      set({ isGenerating: true });

      const eventSource = new EventSource('/api/agent-ui/stream-ui-updates');

      eventSource.onmessage = (event) => {
        const entry = JSON.parse(event.data);
        get().addEntry(entry);
      };

      eventSource.onerror = (err) => {
        console.error('SSE connection failed:', err);
        eventSource.close();
        set({ isGenerating: false });
      };

      return () => eventSource.close();
    },

    // BI Dashboard Methods
    updateDashboardMetric: (component, values) => {
      set((state) => ({
        dashboardMetrics: {
          ...state.dashboardMetrics,
          [component]: {
            component,
            data: values,
            last_updated: new Date().toISOString(),
            cache_hit: false
          }
        }
      }));

      // Also add to history for tracking
      get().addEntry({
        timestamp: new Date().toISOString(),
        agent: 'bi_dashboard',
        key: `metric_update_${component}`,
        value: values
      });
    },

    addIntelligenceAlert: (alert) => {
      const newAlert: IntelligenceAlert = {
        ...alert,
        id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        acknowledged: false
      };

      set((state) => ({
        liveAlerts: [newAlert, ...state.liveAlerts].slice(0, 50) // Keep last 50 alerts
      }));

      // Critical alerts go to history immediately
      if (alert.severity === 'critical') {
        get().addEntry({
          timestamp: newAlert.timestamp,
          agent: 'intelligence_system',
          key: 'critical_alert',
          value: newAlert
        });
      }
    },

    acknowledgeAlert: (alertId) => {
      set((state) => ({
        liveAlerts: state.liveAlerts.map(alert =>
          alert.id === alertId ? { ...alert, acknowledged: true } : alert
        )
      }));
    },

    addPredictiveInsight: (insight) => {
      const newInsight: PredictiveInsight = {
        ...insight,
        id: `insight_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      };

      set((state) => ({
        predictiveInsights: [newInsight, ...state.predictiveInsights]
          .sort((a, b) => b.relevance_score - a.relevance_score)
          .slice(0, 20) // Keep top 20 insights
      }));
    },

    subscribeToIntelligence: (components) => {
      const subscriptions: (() => void)[] = [];

      // Subscribe to each component's WebSocket feed
      components.forEach(component => {
        const identifier = `bi_${component}`;
        const endpoint = `ws://localhost:8000/ws/bi/${component}`;

        get().connectWebSocket(endpoint, identifier);
      });

      // Return cleanup function
      return () => {
        subscriptions.forEach(cleanup => cleanup());
        components.forEach(component => {
          get().disconnectWebSocket(`bi_${component}`);
        });
      };
    },

    connectWebSocket: (endpoint, identifier) => {
      const existingWs = get().activeConnections.get(identifier);
      if (existingWs && existingWs.readyState === WebSocket.OPEN) {
        return; // Already connected
      }

      set((state) => ({
        connectionStatus: { ...state.connectionStatus, [identifier]: 'connecting' }
      }));

      try {
        const ws = new WebSocket(endpoint);

        ws.onopen = () => {
          set((state) => ({
            connectionStatus: { ...state.connectionStatus, [identifier]: 'connected' }
          }));

          get().addEntry({
            timestamp: new Date().toISOString(),
            agent: 'websocket_manager',
            key: `connection_established`,
            value: { endpoint, identifier }
          });
        };

        ws.onmessage = (event) => {
          try {
            const eventReceiveTime = Date.now();
            const data = JSON.parse(event.data);

            // 📊 ENHANCED LATENCY TRACKING (Phase 8+ Optimization)
            if (data._server_timestamp) {
              const endToEndLatency = eventReceiveTime - data._server_timestamp;

              // Track performance in agent store
              get().addEntry({
                timestamp: new Date().toISOString(),
                agent: 'websocket_performance',
                key: 'event_latency_measurement',
                value: {
                  event_type: data.event_type,
                  latency_ms: endToEndLatency,
                  target_10ms_met: endToEndLatency < 10,
                  server_timestamp: data._server_timestamp,
                  client_timestamp: eventReceiveTime
                }
              });

              // Alert on high latency for UI responsiveness
              if (endToEndLatency > 50) {
                console.warn(`🚨 High event latency: ${endToEndLatency}ms for ${data.event_type}`);
              } else if (endToEndLatency < 10) {
                console.debug(`✅ Excellent latency: ${endToEndLatency}ms for ${data.event_type}`);
              }

              // Clean up server timestamp before processing
              delete data._server_timestamp;
            }

            // Route message based on event type
            if (intelligenceEventTypes.includes(data.event_type)) {
              handleIntelligenceEvent(data);
            }

            // Add to history for debugging
            get().addEntry({
              timestamp: new Date().toISOString(),
              agent: 'websocket_intelligence',
              key: `${data.event_type}_received`,
              value: data.data
            });
          } catch (error) {
            console.error('WebSocket message parsing error:', error);
          }
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          set((state) => ({
            connectionStatus: { ...state.connectionStatus, [identifier]: 'error' }
          }));
        };

        ws.onclose = () => {
          set((state) => ({
            connectionStatus: { ...state.connectionStatus, [identifier]: 'disconnected' }
          }));

          // Attempt reconnection after delay
          setTimeout(() => {
            get().connectWebSocket(endpoint, identifier);
          }, 5000);
        };

        set((state) => {
          const newConnections = new Map(state.activeConnections);
          newConnections.set(identifier, ws);
          return { activeConnections: newConnections };
        });
      } catch (error) {
        console.error('WebSocket connection failed:', error);
        set((state) => ({
          connectionStatus: { ...state.connectionStatus, [identifier]: 'error' }
        }));
      }
    },

    disconnectWebSocket: (identifier) => {
      const ws = get().activeConnections.get(identifier);
      if (ws) {
        ws.close();
        set((state) => {
          const newConnections = new Map(state.activeConnections);
          newConnections.delete(identifier);
          return {
            activeConnections: newConnections,
            connectionStatus: { ...state.connectionStatus, [identifier]: 'disconnected' }
          };
        });
      }
    },

    getConnectionStatus: (identifier) => {
      return get().connectionStatus[identifier] || 'disconnected';
    },

    // Analytics Methods
    getMetricHistory: (component, limit = 50) => {
      return get().history
        .filter(entry => entry.key.includes(component))
        .slice(-limit);
    },

    getInsightsByType: (type) => {
      return get().predictiveInsights.filter(insight => insight.type === type);
    },

    getAlertsByType: (type) => {
      return get().liveAlerts.filter(alert => alert.type === type);
    },

    getSystemHealth: () => {
      const connections = get().connectionStatus;
      const alerts = get().liveAlerts.filter(alert => !alert.acknowledged);
      const criticalAlerts = alerts.filter(alert => alert.severity === 'critical');

      const healthStatus =
        criticalAlerts.length > 0 ? 'critical' :
        alerts.length > 3 ? 'warning' :
        Object.values(connections).some(status => status === 'error') ? 'degraded' :
        'healthy';

      return {
        status: healthStatus,
        details: {
          active_connections: Object.values(connections).filter(status => status === 'connected').length,
          total_connections: Object.keys(connections).length,
          unacknowledged_alerts: alerts.length,
          critical_alerts: criticalAlerts.length,
          last_update: new Date().toISOString()
        }
      };
    },

    clearStaleData: (maxAge = 3600000) => { // 1 hour default
      const cutoff = Date.now() - maxAge;

      set((state) => ({
        liveAlerts: state.liveAlerts.filter(
          alert => new Date(alert.timestamp).getTime() > cutoff
        ),
        predictiveInsights: state.predictiveInsights.filter(
          insight => new Date(insight.timestamp).getTime() > cutoff
        ),
        history: state.history.filter(
          entry => new Date(entry.timestamp).getTime() > cutoff
        )
      }));
    },

    getPerformanceMetrics: () => {
      const state = get();

      return {
        total_entries: state.history.length,
        active_connections: state.activeConnections.size,
        unacknowledged_alerts: state.liveAlerts.filter(a => !a.acknowledged).length,
        predictive_insights: state.predictiveInsights.length,
        dashboard_metrics: Object.keys(state.dashboardMetrics).length,
        system_health: state.getSystemHealth().status,
        memory_usage: {
          history_entries: state.history.length,
          dashboard_metrics: Object.keys(state.dashboardMetrics).length,
          alerts: state.liveAlerts.length,
          insights: state.predictiveInsights.length
        }
      };
    },

    // Enhanced BI WebSocket Management (Phase 7 Integration)
    connectBIWebSockets: (locationId) => {
      const biEndpoints = [
        { id: 'bi_dashboard', endpoint: `ws://localhost:8000/ws/dashboard/${locationId}` },
        { id: 'bi_revenue_intelligence', endpoint: `ws://localhost:8000/ws/bi/revenue-intelligence/${locationId}` },
        { id: 'bi_bot_performance', endpoint: `ws://localhost:8000/ws/bot-performance/${locationId}` },
        { id: 'bi_business_intelligence', endpoint: `ws://localhost:8000/ws/business-intelligence/${locationId}` },
        { id: 'ai_concierge_insights', endpoint: `ws://localhost:8000/ws/ai-concierge/${locationId}` },
        { id: 'advanced_analytics', endpoint: `ws://localhost:8000/ws/analytics/advanced/${locationId}` }
      ];

      biEndpoints.forEach(({ id, endpoint }) => {
        get().connectWebSocket(endpoint, id);
      });

      get().addEntry({
        timestamp: new Date().toISOString(),
        agent: 'bi_websocket_manager',
        key: 'bi_connections_initialized',
        value: `Connected to ${biEndpoints.length} BI WebSocket endpoints for location: ${locationId}`
      });
    },

    disconnectBIWebSockets: () => {
      const biIdentifiers = [
        'bi_dashboard',
        'bi_revenue_intelligence',
        'bi_bot_performance',
        'bi_business_intelligence',
        'ai_concierge_insights',
        'advanced_analytics'
      ];

      biIdentifiers.forEach(identifier => {
        get().disconnectWebSocket(identifier);
      });

      get().addEntry({
        timestamp: new Date().toISOString(),
        agent: 'bi_websocket_manager',
        key: 'bi_connections_terminated',
        value: `Disconnected from all BI WebSocket endpoints`
      });
    },

    getBIConnectionHealth: () => {
      const biIdentifiers = [
        'bi_dashboard',
        'bi_revenue_intelligence',
        'bi_bot_performance',
        'bi_business_intelligence',
        'ai_concierge_insights',
        'advanced_analytics'
      ];

      const connectionStatus = get().connectionStatus;
      const connected = biIdentifiers.filter(id => connectionStatus[id] === 'connected').length;
      const total = biIdentifiers.length;

      const healthStatus =
        connected === total ? 'excellent' :
        connected >= total * 0.8 ? 'good' :
        connected >= total * 0.5 ? 'warning' : 'critical';

      return {
        connected,
        total,
        status: healthStatus,
        percentage: Math.round((connected / total) * 100)
      };
    }
  }))
);

// Helper function to handle intelligence events
function handleIntelligenceEvent(eventData: any) {
  const store = useAgentStore.getState();

  switch (eventData.event_type) {
    case 'REALTIME_BI_UPDATE':
      if (eventData.data.component && eventData.data.metrics) {
        store.updateDashboardMetric(eventData.data.component, eventData.data.metrics);
      }
      break;

    case 'ANOMALY_ALERT':
      store.addIntelligenceAlert({
        type: 'anomaly',
        severity: eventData.data.severity || 'medium',
        title: 'Performance Anomaly Detected',
        message: eventData.data.message || 'An unusual pattern has been detected',
        timestamp: eventData.timestamp || new Date().toISOString(),
        data: eventData.data
      });
      break;

    case 'REVENUE_PIPELINE_CHANGE':
      store.addPredictiveInsight({
        type: 'revenue_forecast',
        confidence: eventData.data.confidence || 0.8,
        title: 'Revenue Pipeline Update',
        description: `Pipeline value changed: ${eventData.data.summary}`,
        timestamp: eventData.timestamp || new Date().toISOString(),
        relevance_score: eventData.data.impact === 'high' ? 0.9 : 0.6
      });
      break;

    case 'PERFORMANCE_WARNING':
      store.addIntelligenceAlert({
        type: 'performance',
        severity: eventData.data.response_time_ms > 1000 ? 'high' : 'medium',
        title: 'Performance Degradation',
        message: `${eventData.data.component} response time: ${eventData.data.response_time_ms}ms`,
        timestamp: eventData.timestamp || new Date().toISOString(),
        data: eventData.data
      });
      break;

    case 'BOT_COORDINATION_UPDATE':
      if (eventData.data.status === 'error') {
        store.addIntelligenceAlert({
          type: 'bot_failure',
          severity: 'high',
          title: 'Bot Coordination Issue',
          message: `${eventData.data.bot_type} coordination failed: ${eventData.data.summary}`,
          timestamp: eventData.timestamp || new Date().toISOString(),
          data: eventData.data
        });
      }
      break;

    // Phase 8: AI Concierge Event Handlers
    case 'AI_CONCIERGE_INSIGHT':
      store.addPredictiveInsight({
        type: 'trend_prediction',
        confidence: eventData.data.confidence_score || 0.8,
        title: `${eventData.data.insight_type}: ${eventData.data.title}`,
        description: eventData.data.description,
        recommended_action: eventData.data.recommended_actions?.[0],
        timestamp: eventData.timestamp || new Date().toISOString(),
        relevance_score: eventData.data.expected_impact || 0.7
      });

      // High priority insights also generate alerts
      if (eventData.data.priority === 'critical' || eventData.data.priority === 'high') {
        store.addIntelligenceAlert({
          type: 'performance',
          severity: eventData.data.priority === 'critical' ? 'critical' : 'high',
          title: `AI Concierge: ${eventData.data.title}`,
          message: eventData.data.description,
          timestamp: eventData.timestamp || new Date().toISOString(),
          data: eventData.data
        });
      }
      break;

    case 'COACHING_OPPORTUNITY':
      store.addIntelligenceAlert({
        type: 'performance',
        severity: 'medium',
        title: 'Coaching Opportunity Available',
        message: `${eventData.data.coaching_category}: ${eventData.data.coaching_insight}`,
        timestamp: eventData.timestamp || new Date().toISOString(),
        data: eventData.data
      });

      store.addPredictiveInsight({
        type: 'performance_warning',
        confidence: eventData.data.success_probability || 0.8,
        title: `Coaching: ${eventData.data.coaching_category}`,
        description: eventData.data.coaching_insight,
        recommended_action: eventData.data.recommended_technique,
        timestamp: eventData.timestamp || new Date().toISOString(),
        relevance_score: eventData.data.success_probability || 0.7
      });
      break;

    case 'STRATEGY_RECOMMENDATION':
      store.addPredictiveInsight({
        type: 'trend_prediction',
        confidence: eventData.data.impact_score || 0.8,
        title: `Strategy: ${eventData.data.strategy_title}`,
        description: eventData.data.strategy_description,
        recommended_action: eventData.data.conversation_pivot,
        timestamp: eventData.timestamp || new Date().toISOString(),
        relevance_score: eventData.data.impact_score || 0.8
      });

      // Urgent strategies generate alerts
      if (eventData.data.urgency_level === 'immediate') {
        store.addIntelligenceAlert({
          type: 'performance',
          severity: 'high',
          title: `Immediate Strategy: ${eventData.data.strategy_title}`,
          message: eventData.data.rationale,
          timestamp: eventData.timestamp || new Date().toISOString(),
          data: eventData.data
        });
      }
      break;

    case 'CONVERSATION_QUALITY':
      // Track conversation quality metrics
      if (eventData.data.component && eventData.data.quality_score) {
        store.updateDashboardMetric('conversation_quality', {
          overall_score: eventData.data.quality_score,
          quality_grade: eventData.data.quality_grade,
          conversation_id: eventData.data.conversation_id,
          timestamp: eventData.timestamp
        });
      }

      // Low quality scores trigger alerts
      if (eventData.data.quality_score && eventData.data.quality_score < 60) {
        store.addIntelligenceAlert({
          type: 'performance',
          severity: 'medium',
          title: 'Conversation Quality Alert',
          message: `Quality score dropped to ${eventData.data.quality_score}% (Grade: ${eventData.data.quality_grade})`,
          timestamp: eventData.timestamp || new Date().toISOString(),
          data: eventData.data
        });
      }
      break;

    default:
      // Log unhandled event types for debugging
      console.debug('Unhandled intelligence event:', eventData.event_type);
  }
}
