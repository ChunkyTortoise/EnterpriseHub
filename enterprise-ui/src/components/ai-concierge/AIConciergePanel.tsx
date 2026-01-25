/**
 * AI Concierge Panel - Real-time Proactive Intelligence Dashboard
 *
 * Integrates with Jorge's Phase 7 AI Concierge backend to provide real-time
 * insights, coaching opportunities, and strategic recommendations with
 * interactive acceptance/dismissal workflows.
 *
 * Features:
 * - Real-time insight streaming via WebSocket
 * - Interactive insight cards with confidence scoring
 * - Coaching opportunity acceptance/dismissal
 * - Strategy recommendation implementation tracking
 * - Performance metrics and effectiveness measurement
 */

'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  Brain,
  Target,
  TrendingUp,
  CheckCircle,
  XCircle,
  Clock,
  MessageSquare,
  Lightbulb,
  Zap,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  Eye,
  ArrowRight,
  Activity,
  Timer,
  Star,
  Coffee,
  Users,
  DollarSign
} from 'lucide-react';
import { useWebSocket } from '@/components/providers/WebSocketProvider';
import { useAgentStore } from '@/store/useAgentStore';

// Types for AI Concierge data models
interface ProactiveInsight {
  insight_id: string;
  insight_type: 'coaching' | 'strategy_pivot' | 'objection_prediction' | 'opportunity_detection' | 'conversation_quality' | 'relationship_building' | 'value_articulation';
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  reasoning: string;
  recommended_actions: string[];
  suggested_responses?: string[];
  confidence_score: number;
  expected_impact: number;
  conversation_context: any;
  applicable_stage: string;
  created_at: string;
  expires_at: string;
  dismissed: boolean;
  acted_upon: boolean;
  effectiveness_score?: number;
}

interface ConversationInsightsResponse {
  conversation_id: string;
  total_insights: number;
  active_insights: ProactiveInsight[];
  historical_insights: ProactiveInsight[];
  monitoring_status: string;
  last_analysis_at?: string;
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
}

interface AIConciegePanelProps {
  conversationId?: string;
  className?: string;
}

export function AIConciergePanel({ conversationId = 'demo-conversation', className = '' }: AIConciegePanelProps) {
  // State Management
  const [insights, setInsights] = useState<ConversationInsightsResponse | null>(null);
  const [metrics, setMetrics] = useState<AIConciergeMetrics | null>(null);
  const [selectedInsight, setSelectedInsight] = useState<ProactiveInsight | null>(null);
  const [actionDialog, setActionDialog] = useState<'accept' | 'dismiss' | null>(null);
  const [actionNotes, setActionNotes] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [monitoringActive, setMonitoringActive] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  // WebSocket and Store Integration
  const { connected } = useWebSocket();
  const { addEntry, addIntelligenceAlert, addPredictiveInsight } = useAgentStore();
  const wsRef = useRef<WebSocket | null>(null);

  // Initialize component and fetch initial data
  useEffect(() => {
    initializeConcierge();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [conversationId]);

  const initializeConcierge = async () => {
    try {
      setIsLoading(true);

      // Fetch initial insights
      await fetchConversationInsights();

      // Fetch performance metrics
      await fetchMetrics();

      // Initialize WebSocket connection for real-time updates
      if (connected) {
        setupWebSocketConnection();
      }

    } catch (error) {
      console.error('Failed to initialize AI Concierge:', error);
      addIntelligenceAlert({
        type: 'bot_failure',
        severity: 'high',
        title: 'AI Concierge Connection Failed',
        message: 'Unable to connect to AI Concierge backend services',
        timestamp: new Date().toISOString()
      });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchConversationInsights = async () => {
    try {
      const response = await fetch(`/api/v1/concierge/insights/${conversationId}?include_historical=true`, {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch insights: ${response.status}`);
      }

      const data: ConversationInsightsResponse = await response.json();
      setInsights(data);
      setMonitoringActive(data.monitoring_status === 'active');
      setLastUpdate(new Date().toISOString());

      // Update agent store with insights for system tracking
      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'ai_concierge',
        key: 'insights_loaded',
        value: {
          conversation_id: conversationId,
          active_count: data.active_insights.length,
          total_count: data.total_insights
        }
      });

    } catch (error) {
      console.error('Failed to fetch insights:', error);
      throw error;
    }
  };

  const fetchMetrics = async () => {
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
      setMetrics(data.service_metrics);

    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  };

  const setupWebSocketConnection = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    const wsUrl = `ws://localhost:8000/api/v1/concierge/stream/${conversationId}?token=${getAuthToken()}`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('AI Concierge WebSocket connected');
      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'ai_concierge_websocket',
        key: 'connection_established',
        value: { conversation_id: conversationId }
      });
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    wsRef.current.onerror = (error) => {
      console.error('AI Concierge WebSocket error:', error);
      addIntelligenceAlert({
        type: 'bot_failure',
        severity: 'medium',
        title: 'AI Concierge Connection Issue',
        message: 'WebSocket connection to AI Concierge experienced an error',
        timestamp: new Date().toISOString()
      });
    };

    wsRef.current.onclose = () => {
      console.log('AI Concierge WebSocket disconnected');
      // Attempt reconnection after 5 seconds
      setTimeout(() => {
        if (connected) {
          setupWebSocketConnection();
        }
      }, 5000);
    };
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.event_type) {
      case 'proactive_insight':
        // New insight received - refresh insights
        fetchConversationInsights();
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
          message: data.data.title,
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
        setLastUpdate(new Date().toISOString());
        break;

      default:
        console.debug('Unhandled AI Concierge event:', data.event_type);
    }
  };

  const handleInsightAction = async (action: 'accept' | 'dismiss') => {
    if (!selectedInsight) return;

    setIsProcessing(true);

    try {
      const endpoint = `/api/v1/concierge/insights/${selectedInsight.insight_id}/${action}`;
      const requestData = action === 'accept'
        ? {
            action_taken: actionNotes || 'Used insight recommendation',
            implementation_notes: actionNotes,
            effectiveness_prediction: 0.8
          }
        : {
            dismissal_reason: 'not_relevant', // Could be made configurable
            feedback_notes: actionNotes
          };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        throw new Error(`Failed to ${action} insight: ${response.status}`);
      }

      const result = await response.json();

      // Refresh insights after action
      await fetchConversationInsights();

      // Add to agent store for tracking
      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'ai_concierge',
        key: `insight_${action}`,
        value: {
          insight_id: selectedInsight.insight_id,
          tracking_id: result.tracking_id,
          action_notes: actionNotes
        }
      });

      // Close dialog and reset state
      setActionDialog(null);
      setSelectedInsight(null);
      setActionNotes('');

    } catch (error) {
      console.error(`Failed to ${action} insight:`, error);
      addIntelligenceAlert({
        type: 'bot_failure',
        severity: 'medium',
        title: `Insight ${action} Failed`,
        message: `Unable to ${action} insight: ${selectedInsight.title}`,
        timestamp: new Date().toISOString()
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const toggleMonitoring = async () => {
    try {
      const action = monitoringActive ? 'stop' : 'start';
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
      setMonitoringActive(result.monitoring_active);

      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'ai_concierge',
        key: 'monitoring_toggle',
        value: { action, status: result.status }
      });

    } catch (error) {
      console.error('Failed to toggle monitoring:', error);
    }
  };

  const getAuthToken = () => {
    // In production, this would get the actual JWT token
    // For now, return a placeholder
    return 'demo-token';
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-500/10 text-red-500 border-red-500/20';
      case 'high': return 'bg-orange-500/10 text-orange-500 border-orange-500/20';
      case 'medium': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
      case 'low': return 'bg-blue-500/10 text-blue-500 border-blue-500/20';
      default: return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
    }
  };

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'coaching': return <Target className="h-4 w-4" />;
      case 'strategy_pivot': return <TrendingUp className="h-4 w-4" />;
      case 'objection_prediction': return <AlertTriangle className="h-4 w-4" />;
      case 'opportunity_detection': return <DollarSign className="h-4 w-4" />;
      case 'conversation_quality': return <Star className="h-4 w-4" />;
      case 'relationship_building': return <Users className="h-4 w-4" />;
      case 'value_articulation': return <Lightbulb className="h-4 w-4" />;
      default: return <Brain className="h-4 w-4" />;
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const past = new Date(timestamp);
    const diffMs = now.getTime() - past.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  const renderInsightCard = (insight: ProactiveInsight) => (
    <Card key={insight.insight_id} className="bg-slate-900/50 border-slate-800 hover:border-blue-500/30 transition-all duration-200 group">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 flex-1">
            <div className={`p-2 rounded-lg ${getPriorityColor(insight.priority)}`}>
              {getInsightIcon(insight.insight_type)}
            </div>
            <div className="flex-1 min-w-0">
              <CardTitle className="text-slate-100 text-sm leading-tight mb-1">
                {insight.title}
              </CardTitle>
              <CardDescription className="text-slate-400 text-xs">
                {insight.reasoning}
              </CardDescription>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-shrink-0">
            <Badge variant="outline" className={`text-xs ${getPriorityColor(insight.priority)}`}>
              {insight.priority}
            </Badge>
            <div className="text-xs text-slate-500">
              {formatTimeAgo(insight.created_at)}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <p className="text-slate-300 text-sm mb-4 leading-relaxed">
          {insight.description}
        </p>

        {insight.recommended_actions && insight.recommended_actions.length > 0 && (
          <div className="space-y-2 mb-4">
            <h4 className="text-slate-100 text-xs font-medium">Recommended Actions:</h4>
            <ul className="space-y-1">
              {insight.recommended_actions.map((action, index) => (
                <li key={index} className="text-slate-400 text-xs flex items-start gap-2">
                  <ArrowRight className="h-3 w-3 text-blue-400 mt-0.5 flex-shrink-0" />
                  {action}
                </li>
              ))}
            </ul>
          </div>
        )}

        {insight.suggested_responses && insight.suggested_responses.length > 0 && (
          <div className="space-y-2 mb-4">
            <h4 className="text-slate-100 text-xs font-medium">Suggested Responses:</h4>
            <div className="space-y-2">
              {insight.suggested_responses.map((response, index) => (
                <div key={index} className="bg-slate-800/50 p-2 rounded border-l-2 border-blue-500/30">
                  <p className="text-slate-300 text-xs italic">"{response}"</p>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="flex items-center gap-4 text-xs text-slate-500 mb-4">
          <div className="flex items-center gap-1">
            <Zap className="h-3 w-3" />
            Confidence: {Math.round(insight.confidence_score * 100)}%
          </div>
          <div className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            Impact: {Math.round(insight.expected_impact * 100)}%
          </div>
          <div className="flex items-center gap-1">
            <Timer className="h-3 w-3" />
            Expires: {formatTimeAgo(insight.expires_at)}
          </div>
        </div>
      </CardContent>

      <CardFooter className="pt-0">
        <div className="flex items-center gap-2 w-full">
          <Button
            size="sm"
            onClick={() => {
              setSelectedInsight(insight);
              setActionDialog('accept');
            }}
            className="bg-green-600 hover:bg-green-500 text-white flex-1"
          >
            <ThumbsUp className="h-3 w-3 mr-1" />
            Accept
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              setSelectedInsight(insight);
              setActionDialog('dismiss');
            }}
            className="border-slate-600 text-slate-300 hover:bg-slate-800 flex-1"
          >
            <ThumbsDown className="h-3 w-3 mr-1" />
            Dismiss
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => {
              setSelectedInsight(insight);
              // Could implement a detailed view dialog
            }}
            className="text-slate-400 hover:text-slate-300 px-3"
          >
            <Eye className="h-3 w-3" />
          </Button>
        </div>
      </CardFooter>
    </Card>
  );

  const renderMetricsPanel = () => (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
      <Card className="bg-slate-900/30 border-slate-800">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-500/10 rounded text-blue-400">
              <Activity className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xl font-bold text-slate-100">{metrics?.active_monitors || 0}</div>
              <div className="text-xs text-slate-500">Active Monitors</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-900/30 border-slate-800">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-500/10 rounded text-green-400">
              <Lightbulb className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xl font-bold text-slate-100">{metrics?.insights_per_hour || 0}</div>
              <div className="text-xs text-slate-500">Insights/Hour</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-900/30 border-slate-800">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-500/10 rounded text-purple-400">
              <CheckCircle className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xl font-bold text-slate-100">
                {metrics?.acceptance_rate ? Math.round(metrics.acceptance_rate * 100) : 0}%
              </div>
              <div className="text-xs text-slate-500">Acceptance Rate</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-900/30 border-slate-800">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500/10 rounded text-orange-400">
              <Zap className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xl font-bold text-slate-100">
                {metrics?.avg_confidence ? Math.round(metrics.avg_confidence * 100) : 0}%
              </div>
              <div className="text-xs text-slate-500">Avg Confidence</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-900/30 border-slate-800">
        <CardContent className="p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-yellow-500/10 rounded text-yellow-400">
              <Star className="h-4 w-4" />
            </div>
            <div>
              <div className="text-xl font-bold text-slate-100">
                {metrics?.avg_effectiveness ? Math.round(metrics.avg_effectiveness * 100) : 0}%
              </div>
              <div className="text-xs text-slate-500">Effectiveness</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <Brain className="h-8 w-8 text-blue-400 animate-pulse mx-auto mb-4" />
          <p className="text-slate-400">Loading AI Concierge...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-100 mb-2">AI Concierge Intelligence</h2>
          <p className="text-slate-400 text-sm">
            Proactive conversation insights and strategic recommendations
          </p>
        </div>

        <div className="flex items-center gap-3">
          {lastUpdate && (
            <div className="text-xs text-slate-500">
              Last update: {formatTimeAgo(lastUpdate)}
            </div>
          )}

          <Badge
            variant={connected ? 'default' : 'destructive'}
            className={connected ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}
          >
            {connected ? 'Connected' : 'Disconnected'}
          </Badge>

          <Button
            size="sm"
            variant={monitoringActive ? 'destructive' : 'default'}
            onClick={toggleMonitoring}
            className={monitoringActive ? 'bg-red-600 hover:bg-red-500' : 'bg-blue-600 hover:bg-blue-500'}
          >
            {monitoringActive ? (
              <>
                <XCircle className="h-3 w-3 mr-1" />
                Stop Monitoring
              </>
            ) : (
              <>
                <CheckCircle className="h-3 w-3 mr-1" />
                Start Monitoring
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Performance Metrics */}
      {metrics && renderMetricsPanel()}

      {/* Main Content */}
      <Tabs defaultValue="active" className="space-y-4">
        <TabsList className="bg-slate-900 border-slate-800">
          <TabsTrigger value="active" className="data-[state=active]:bg-slate-800">
            Active Insights ({insights?.active_insights.length || 0})
          </TabsTrigger>
          <TabsTrigger value="historical" className="data-[state=active]:bg-slate-800">
            Historical ({insights?.historical_insights.length || 0})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4">
          {insights?.active_insights.length === 0 ? (
            <Card className="bg-slate-900/30 border-slate-800">
              <CardContent className="p-8 text-center">
                <Coffee className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">No active insights at the moment</p>
                <p className="text-slate-500 text-sm mt-2">
                  {monitoringActive
                    ? 'AI Concierge is monitoring conversations for opportunities...'
                    : 'Start monitoring to begin receiving proactive insights'
                  }
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {insights?.active_insights.map(renderInsightCard)}
            </div>
          )}
        </TabsContent>

        <TabsContent value="historical" className="space-y-4">
          {insights?.historical_insights.length === 0 ? (
            <Card className="bg-slate-900/30 border-slate-800">
              <CardContent className="p-8 text-center">
                <MessageSquare className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">No historical insights available</p>
                <p className="text-slate-500 text-sm mt-2">
                  Previous insights will appear here as you interact with recommendations
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {insights?.historical_insights.map(renderInsightCard)}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Action Dialog */}
      <Dialog
        open={actionDialog !== null}
        onOpenChange={(open) => {
          if (!open) {
            setActionDialog(null);
            setSelectedInsight(null);
            setActionNotes('');
          }
        }}
      >
        <DialogContent className="bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-slate-100">
              {actionDialog === 'accept' ? 'Accept Insight' : 'Dismiss Insight'}
            </DialogTitle>
            <DialogDescription className="text-slate-400">
              {selectedInsight?.title}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-300 mb-2 block">
                {actionDialog === 'accept' ? 'Implementation Notes' : 'Dismissal Reason'}
              </label>
              <Textarea
                value={actionNotes}
                onChange={(e) => setActionNotes(e.target.value)}
                placeholder={
                  actionDialog === 'accept'
                    ? 'Describe how you plan to implement this insight...'
                    : 'Why are you dismissing this insight?'
                }
                className="bg-slate-800 border-slate-700 text-slate-300"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setActionDialog(null);
                setSelectedInsight(null);
                setActionNotes('');
              }}
              className="border-slate-600 text-slate-300"
            >
              Cancel
            </Button>
            <Button
              onClick={() => handleInsightAction(actionDialog!)}
              disabled={isProcessing}
              className={
                actionDialog === 'accept'
                  ? 'bg-green-600 hover:bg-green-500'
                  : 'bg-red-600 hover:bg-red-500'
              }
            >
              {isProcessing ? 'Processing...' : actionDialog === 'accept' ? 'Accept Insight' : 'Dismiss Insight'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default AIConciergePanel;