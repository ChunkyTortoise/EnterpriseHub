"use client";

import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  Title,
  Text,
  Flex,
  Badge,
  Metric,
  BarChart,
  LineChart,
  DonutChart,
  Grid,
  ProgressBar,
  Callout
} from '@tremor/react';
import {
  Bot,
  Activity,
  Zap,
  Target,
  Clock,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  Users,
  MessageCircle,
  Brain,
  Settings,
  RefreshCw
} from 'lucide-react';
import { useAgentStore } from '../store/useAgentStore';

interface BotMetrics {
  bot_type: string;
  display_name: string;
  interactions: number;
  avg_response_time_ms: number;
  success_rate: number;
  confidence_score: number;
  qualification_rate?: number;
  hot_rate?: number;
  completion_rate?: number;
  handoff_rate: number;
  error_rate: number;
  daily_trend: Array<{ date: string; interactions: number; success_rate: number }>;
  current_status: 'healthy' | 'warning' | 'error' | 'maintenance';
  performance_tier: 'excellent' | 'good' | 'acceptable' | 'needs_improvement';
}

interface CoordinationMetrics {
  handoff_success_rate: number;
  avg_handoff_time_ms: number;
  coordination_events: number;
  context_preservation_rate: number;
  multi_bot_conversations: number;
}

interface BotPerformanceMatrixProps {
  locationId?: string;
  timeframe?: '24h' | '7d' | '30d';
  showCoordination?: boolean;
  realTimeUpdates?: boolean;
}

export function BotPerformanceMatrix({
  locationId = 'default',
  timeframe = '7d',
  showCoordination = true,
  realTimeUpdates = true
}: BotPerformanceMatrixProps) {
  const { addEntry } = useAgentStore();

  const [botMetrics, setBotMetrics] = useState<BotMetrics[]>([]);
  const [coordinationMetrics, setCoordinationMetrics] = useState<CoordinationMetrics | null>(null);
  const [selectedBot, setSelectedBot] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Real-time WebSocket connection
  useEffect(() => {
    if (!realTimeUpdates) return;

    const ws = new WebSocket(`${process.env.NEXT_PUBLIC_SOCKET_URL?.replace('http', 'ws')}/ws/bot-performance/${locationId}`);

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.event_type === 'BOT_STATUS_UPDATE') {
          updateBotMetrics(data.data);
        } else if (data.event_type === 'BOT_HANDOFF_REQUEST') {
          updateCoordinationMetrics(data.data);
        }
      } catch (error) {
        console.error('Bot performance WebSocket error:', error);
      }
    };

    ws.onopen = () => {
      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'bot_performance_matrix',
        key: 'websocket_connected',
        value: 'Real-time bot monitoring active'
      });
    };

    return () => ws.close();
  }, [realTimeUpdates, locationId, addEntry]);

  // Fetch bot performance data
  useEffect(() => {
    const fetchBotMetrics = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE}/api/bi/bot-performance?location_id=${locationId}&timeframe=${timeframe}&include_coordination=${showCoordination}`
        );
        const data = await response.json();

        setBotMetrics(data.bot_metrics || generateMockBotMetrics());
        setCoordinationMetrics(data.coordination_metrics || generateMockCoordinationMetrics());
        setLastUpdated(new Date());

        addEntry({
          timestamp: new Date().toISOString(),
          agent: 'bot_performance_matrix',
          key: 'metrics_refresh',
          value: `Updated metrics for ${data.bot_metrics?.length || 4} bots`
        });
      } catch (error) {
        console.error('Bot metrics fetch error:', error);
        setBotMetrics(generateMockBotMetrics());
        setCoordinationMetrics(generateMockCoordinationMetrics());
      } finally {
        setIsLoading(false);
      }
    };

    fetchBotMetrics();
    const interval = setInterval(fetchBotMetrics, 60000); // 1 minute
    return () => clearInterval(interval);
  }, [locationId, timeframe, showCoordination, addEntry]);

  const generateMockBotMetrics = (): BotMetrics[] => [
    {
      bot_type: 'jorge-seller',
      display_name: 'Jorge Seller Bot',
      interactions: 324,
      avg_response_time_ms: 38.2,
      success_rate: 0.92,
      confidence_score: 0.89,
      hot_rate: 0.15,
      handoff_rate: 0.08,
      error_rate: 0.02,
      daily_trend: generateDailyTrend(),
      current_status: 'healthy',
      performance_tier: 'excellent'
    },
    {
      bot_type: 'jorge-buyer',
      display_name: 'Jorge Buyer Bot',
      interactions: 156,
      avg_response_time_ms: 42.1,
      success_rate: 0.89,
      confidence_score: 0.85,
      qualification_rate: 0.28,
      handoff_rate: 0.12,
      error_rate: 0.03,
      daily_trend: generateDailyTrend(),
      current_status: 'healthy',
      performance_tier: 'excellent'
    },
    {
      bot_type: 'lead-bot',
      display_name: 'Lead Lifecycle Bot',
      interactions: 89,
      avg_response_time_ms: 125.3,
      success_rate: 0.85,
      confidence_score: 0.82,
      completion_rate: 0.67,
      handoff_rate: 0.05,
      error_rate: 0.04,
      daily_trend: generateDailyTrend(),
      current_status: 'warning',
      performance_tier: 'good'
    },
    {
      bot_type: 'intent-decoder',
      display_name: 'Intent Analysis Engine',
      interactions: 567,
      avg_response_time_ms: 24.1,
      success_rate: 0.94,
      confidence_score: 0.87,
      handoff_rate: 0.15,
      error_rate: 0.01,
      daily_trend: generateDailyTrend(),
      current_status: 'healthy',
      performance_tier: 'excellent'
    }
  ];

  const generateDailyTrend = () => {
    const days = timeframe === '24h' ? 24 : timeframe === '7d' ? 7 : 30;
    return Array.from({ length: days }, (_, i) => {
      const date = new Date();
      date.setDate(date.getDate() - (days - i - 1));
      return {
        date: date.toISOString().split('T')[0],
        interactions: Math.floor(Math.random() * 50) + 10,
        success_rate: 0.8 + Math.random() * 0.15
      };
    });
  };

  const generateMockCoordinationMetrics = (): CoordinationMetrics => ({
    handoff_success_rate: 0.94,
    avg_handoff_time_ms: 1247,
    coordination_events: 67,
    context_preservation_rate: 0.89,
    multi_bot_conversations: 23
  });

  const updateBotMetrics = (data: any) => {
    setBotMetrics(prev => prev.map(bot =>
      bot.bot_type === data.bot_type
        ? { ...bot, current_status: data.status, last_activity: data.timestamp }
        : bot
    ));
  };

  const updateCoordinationMetrics = (data: any) => {
    setCoordinationMetrics(prev => prev ? {
      ...prev,
      coordination_events: prev.coordination_events + 1,
      avg_handoff_time_ms: (prev.avg_handoff_time_ms * 0.9) + ((data.processing_time_ms || 1000) * 0.1)
    } : null);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'emerald';
      case 'warning': return 'amber';
      case 'error': return 'red';
      case 'maintenance': return 'blue';
      default: return 'slate';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="h-4 w-4" />;
      case 'warning': return <AlertTriangle className="h-4 w-4" />;
      case 'error': return <AlertTriangle className="h-4 w-4" />;
      case 'maintenance': return <Settings className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'excellent': return 'emerald';
      case 'good': return 'blue';
      case 'acceptable': return 'amber';
      case 'needs_improvement': return 'red';
      default: return 'slate';
    }
  };

  const formatResponseTime = (ms: number) => {
    return ms < 1000 ? `${ms.toFixed(1)}ms` : `${(ms / 1000).toFixed(2)}s`;
  };

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;

  // Calculate overall system health
  const systemHealth = useMemo(() => {
    const avgSuccessRate = botMetrics.reduce((sum, bot) => sum + bot.success_rate, 0) / botMetrics.length;
    const avgResponseTime = botMetrics.reduce((sum, bot) => sum + bot.avg_response_time_ms, 0) / botMetrics.length;
    const healthyBots = botMetrics.filter(bot => bot.current_status === 'healthy').length;

    return {
      overall_health: avgSuccessRate > 0.9 && avgResponseTime < 100 ? 'excellent' :
                     avgSuccessRate > 0.85 && avgResponseTime < 200 ? 'good' : 'needs_attention',
      avg_success_rate: avgSuccessRate,
      avg_response_time: avgResponseTime,
      healthy_bots_percentage: healthyBots / botMetrics.length
    };
  }, [botMetrics]);

  return (
    <div className="space-y-6">
      {/* Header with System Health */}
      <Card className="bg-slate-900 border-slate-800">
        <Flex justifyContent="between" alignItems="start">
          <div>
            <Title className="text-slate-100 text-2xl flex items-center space-x-2">
              <Bot className="h-6 w-6 text-blue-400" />
              <span>Jorge's Bot Performance Matrix</span>
            </Title>
            <Text className="text-slate-400 mt-1">
              Real-time monitoring and performance analytics for the bot ecosystem
            </Text>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-xs text-slate-500">
              Last updated: {lastUpdated.toLocaleTimeString()}
            </div>
            <Badge color={getStatusColor(systemHealth.overall_health)}>
              System: {systemHealth.overall_health}
            </Badge>
          </div>
        </Flex>

        {/* System Overview */}
        <Grid numItemsLg={4} className="gap-4 mt-6">
          <Card className="bg-slate-800 border-slate-700">
            <Flex justifyContent="between">
              <Text className="text-slate-400">Average Success Rate</Text>
              <Activity className="h-4 w-4 text-emerald-400" />
            </Flex>
            <Metric className="text-emerald-100">{formatPercentage(systemHealth.avg_success_rate)}</Metric>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <Flex justifyContent="between">
              <Text className="text-slate-400">Average Response Time</Text>
              <Zap className="h-4 w-4 text-blue-400" />
            </Flex>
            <Metric className="text-blue-100">{formatResponseTime(systemHealth.avg_response_time)}</Metric>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <Flex justifyContent="between">
              <Text className="text-slate-400">Healthy Bots</Text>
              <CheckCircle className="h-4 w-4 text-green-400" />
            </Flex>
            <Metric className="text-green-100">
              {formatPercentage(systemHealth.healthy_bots_percentage)}
            </Metric>
          </Card>

          <Card className="bg-slate-800 border-slate-700">
            <Flex justifyContent="between">
              <Text className="text-slate-400">Total Interactions</Text>
              <MessageCircle className="h-4 w-4 text-purple-400" />
            </Flex>
            <Metric className="text-purple-100">
              {botMetrics.reduce((sum, bot) => sum + bot.interactions, 0).toLocaleString()}
            </Metric>
          </Card>
        </Grid>
      </Card>

      {/* Bot Performance Heat Map */}
      <Card className="bg-slate-900 border-slate-800">
        <Title className="text-slate-100 mb-6">Bot Performance Heat Map</Title>

        <div className="space-y-4">
          {botMetrics.map((bot) => (
            <Card
              key={bot.bot_type}
              className={`
                bg-slate-800 border-slate-700 transition-all duration-200 cursor-pointer
                hover:border-slate-600 hover:shadow-lg
                ${selectedBot === bot.bot_type ? 'border-blue-500 bg-blue-950/20' : ''}
              `}
              onClick={() => setSelectedBot(selectedBot === bot.bot_type ? null : bot.bot_type)}
            >
              <Flex justifyContent="between" alignItems="start">
                <div className="flex items-center space-x-4">
                  <div className={`p-3 rounded-lg bg-slate-700 text-slate-300`}>
                    <Brain className="h-6 w-6" />
                  </div>

                  <div>
                    <Title className="text-slate-100">{bot.display_name}</Title>
                    <Text className="text-slate-400 text-sm">{bot.bot_type}</Text>

                    <div className="flex items-center space-x-4 mt-2">
                      <Badge color={getStatusColor(bot.current_status)}>
                        {getStatusIcon(bot.current_status)}
                        {bot.current_status}
                      </Badge>
                      <Badge color={getTierColor(bot.performance_tier)}>
                        {bot.performance_tier}
                      </Badge>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-right">
                  <div>
                    <Text className="text-slate-400 text-sm">Interactions</Text>
                    <Metric className="text-slate-100">{bot.interactions.toLocaleString()}</Metric>
                  </div>

                  <div>
                    <Text className="text-slate-400 text-sm">Success Rate</Text>
                    <Metric className="text-emerald-100">{formatPercentage(bot.success_rate)}</Metric>
                  </div>

                  <div>
                    <Text className="text-slate-400 text-sm">Response Time</Text>
                    <Metric className="text-blue-100">{formatResponseTime(bot.avg_response_time_ms)}</Metric>
                  </div>

                  <div>
                    <Text className="text-slate-400 text-sm">Confidence</Text>
                    <Metric className="text-purple-100">{formatPercentage(bot.confidence_score)}</Metric>
                  </div>
                </div>
              </Flex>

              {/* Performance Bars */}
              <div className="mt-4 space-y-2">
                <div>
                  <Flex justifyContent="between" className="mb-1">
                    <Text className="text-slate-400 text-xs">Success Rate</Text>
                    <Text className="text-slate-400 text-xs">{formatPercentage(bot.success_rate)}</Text>
                  </Flex>
                  <Progress
                    value={bot.success_rate * 100}
                    color={bot.success_rate > 0.9 ? "emerald" : bot.success_rate > 0.8 ? "amber" : "red"}
                    className="w-full"
                  />
                </div>

                <div>
                  <Flex justifyContent="between" className="mb-1">
                    <Text className="text-slate-400 text-xs">Response Time (vs 50ms target)</Text>
                    <Text className="text-slate-400 text-xs">{formatResponseTime(bot.avg_response_time_ms)}</Text>
                  </Flex>
                  <Progress
                    value={Math.max(0, 100 - (bot.avg_response_time_ms / 50) * 100)}
                    color={bot.avg_response_time_ms < 50 ? "emerald" : bot.avg_response_time_ms < 100 ? "amber" : "red"}
                    className="w-full"
                  />
                </div>
              </div>

              {/* Bot-specific Metrics */}
              {bot.bot_type === 'jorge-seller' && (
                <div className="mt-4 grid grid-cols-2 gap-4">
                  <div>
                    <Text className="text-slate-400 text-sm">Hot Lead Rate</Text>
                    <Metric className="text-orange-100">{formatPercentage(bot.hot_rate || 0)}</Metric>
                  </div>
                  <div>
                    <Text className="text-slate-400 text-sm">Handoff Rate</Text>
                    <Metric className="text-blue-100">{formatPercentage(bot.handoff_rate)}</Metric>
                  </div>
                </div>
              )}

              {bot.bot_type === 'jorge-buyer' && (
                <div className="mt-4 grid grid-cols-2 gap-4">
                  <div>
                    <Text className="text-slate-400 text-sm">Qualification Rate</Text>
                    <Metric className="text-emerald-100">{formatPercentage(bot.qualification_rate || 0)}</Metric>
                  </div>
                  <div>
                    <Text className="text-slate-400 text-sm">Handoff Rate</Text>
                    <Metric className="text-blue-100">{formatPercentage(bot.handoff_rate)}</Metric>
                  </div>
                </div>
              )}

              {bot.bot_type === 'lead-bot' && (
                <div className="mt-4 grid grid-cols-2 gap-4">
                  <div>
                    <Text className="text-slate-400 text-sm">Completion Rate</Text>
                    <Metric className="text-purple-100">{formatPercentage(bot.completion_rate || 0)}</Metric>
                  </div>
                  <div>
                    <Text className="text-slate-400 text-sm">Error Rate</Text>
                    <Metric className={`${bot.error_rate > 0.05 ? 'text-red-100' : 'text-green-100'}`}>
                      {formatPercentage(bot.error_rate)}
                    </Metric>
                  </div>
                </div>
              )}

              {/* Expanded Details */}
              {selectedBot === bot.bot_type && (
                <div className="mt-6 p-4 bg-slate-700 rounded-lg">
                  <Title className="text-slate-100 mb-4">7-Day Performance Trend</Title>
                  <LineChart
                    data={bot.daily_trend}
                    index="date"
                    categories={["success_rate"]}
                    colors={["emerald"]}
                    showLegend={false}
                    showGridLines={true}
                    className="h-32"
                    valueFormatter={formatPercentage}
                  />
                </div>
              )}
            </Card>
          ))}
        </div>
      </Card>

      {/* Bot Coordination Metrics */}
      {showCoordination && coordinationMetrics && (
        <Card className="bg-slate-900 border-slate-800">
          <Title className="text-slate-100 mb-6 flex items-center space-x-2">
            <RefreshCw className="h-5 w-5 text-blue-400" />
            <span>Multi-Bot Coordination</span>
          </Title>

          <Grid numItemsLg={3} className="gap-6">
            <Card className="bg-slate-800 border-slate-700">
              <Title className="text-slate-100 mb-4">Handoff Performance</Title>
              <DonutChart
                data={[
                  { name: "Successful", value: coordinationMetrics.handoff_success_rate * 100 },
                  { name: "Failed", value: (1 - coordinationMetrics.handoff_success_rate) * 100 }
                ]}
                category="value"
                index="name"
                colors={["emerald", "red"]}
                className="h-32"
              />
              <Text className="text-emerald-400 text-center mt-2">
                {formatPercentage(coordinationMetrics.handoff_success_rate)} Success Rate
              </Text>
            </Card>

            <div className="space-y-4">
              <Card className="bg-slate-800 border-slate-700">
                <Flex justifyContent="between">
                  <Text className="text-slate-400">Avg Handoff Time</Text>
                  <Clock className="h-4 w-4 text-blue-400" />
                </Flex>
                <Metric className="text-blue-100">
                  {formatResponseTime(coordinationMetrics.avg_handoff_time_ms)}
                </Metric>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <Flex justifyContent="between">
                  <Text className="text-slate-400">Context Preservation</Text>
                  <Brain className="h-4 w-4 text-purple-400" />
                </Flex>
                <Metric className="text-purple-100">
                  {formatPercentage(coordinationMetrics.context_preservation_rate)}
                </Metric>
              </Card>
            </div>

            <div className="space-y-4">
              <Card className="bg-slate-800 border-slate-700">
                <Flex justifyContent="between">
                  <Text className="text-slate-400">Coordination Events</Text>
                  <Activity className="h-4 w-4 text-emerald-400" />
                </Flex>
                <Metric className="text-emerald-100">
                  {coordinationMetrics.coordination_events}
                </Metric>
              </Card>

              <Card className="bg-slate-800 border-slate-700">
                <Flex justifyContent="between">
                  <Text className="text-slate-400">Multi-Bot Conversations</Text>
                  <Users className="h-4 w-4 text-amber-400" />
                </Flex>
                <Metric className="text-amber-100">
                  {coordinationMetrics.multi_bot_conversations}
                </Metric>
              </Card>
            </div>
          </Grid>
        </Card>
      )}

      {/* Performance Alerts */}
      {botMetrics.some(bot => bot.current_status !== 'healthy') && (
        <Card className="bg-red-950 border-red-800">
          <Callout title="Performance Alerts" icon={AlertTriangle} color="red">
            <div className="space-y-2">
              {botMetrics
                .filter(bot => bot.current_status !== 'healthy')
                .map(bot => (
                  <div key={bot.bot_type} className="flex items-center justify-between">
                    <Text className="text-red-100">
                      {bot.display_name}: {bot.current_status}
                    </Text>
                    <Badge color="red">{bot.performance_tier}</Badge>
                  </div>
                ))}
            </div>
          </Callout>
        </Card>
      )}
    </div>
  );
}