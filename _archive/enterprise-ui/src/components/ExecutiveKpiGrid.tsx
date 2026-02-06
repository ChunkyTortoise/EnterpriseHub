"use client";

import { Card, Metric, Text, Grid, BadgeDelta, Flex, AreaChart, SparkAreaChart } from "@tremor/react";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { TrendingUp, TrendingDown, Activity, DollarSign, Users, Target, Brain, Zap } from "lucide-react";
import { useAgentStore } from "../store/useAgentStore";

interface EnhancedKPIGridProps {
  timeframe?: '24h' | '7d' | '30d' | '90d';
  drillDownEnabled?: boolean;
  realtimeUpdates?: boolean;
  jorgeCommission?: boolean;
  locationId?: string;
}

interface KPIMetrics {
  total_revenue: number;
  total_leads: number;
  conversion_rate: number;
  hot_leads: number;
  jorge_commission: number;
  avg_response_time_ms: number;
  bot_success_rate: number;
  pipeline_value: number;
}

interface KPIComparisons {
  revenue_change: number;
  leads_change: number;
  conversion_change: number;
  hot_leads_change: number;
  jorge_commission_change: number;
}

interface KPITrends {
  revenue_trend: Array<{ hour: string; value: number }>;
  leads_trend: Array<{ hour: string; value: number }>;
  conversion_trend: Array<{ hour: string; value: number }>;
}

export function ExecutiveKpiGrid({
  timeframe = '24h',
  drillDownEnabled = true,
  realtimeUpdates = true,
  jorgeCommission = true,
  locationId = 'default'
}: EnhancedKPIGridProps) {
  const router = useRouter();
  const { addEntry, connectBIWebSockets, getBIConnectionHealth } = useAgentStore();

  // Drill-down navigation handlers
  const handleDrillDown = useCallback((metric: string, data: any) => {
    if (!drillDownEnabled) return;

    addEntry({
      timestamp: new Date().toISOString(),
      agent: 'executive_kpi_grid',
      key: 'drill_down_navigation',
      value: `Navigating to detailed ${metric} analytics`
    });

    switch (metric) {
      case 'revenue':
        router.push(`/bi-dashboard?tab=revenue&timeframe=${timeframe}&focus=pipeline`);
        break;
      case 'leads':
        router.push(`/analytics/leads?timeframe=${timeframe}&filter=active`);
        break;
      case 'conversion':
        router.push(`/analytics/conversion?timeframe=${timeframe}&bot=jorge-seller`);
        break;
      case 'commission':
        router.push(`/bi-dashboard?tab=revenue&timeframe=${timeframe}&focus=commission`);
        break;
      case 'performance':
        router.push(`/bi-dashboard?tab=bots&timeframe=${timeframe}&focus=response_time`);
        break;
      case 'success_rate':
        router.push(`/bi-dashboard?tab=bots&timeframe=${timeframe}&focus=success_metrics`);
        break;
      default:
        router.push(`/analytics/detailed?metric=${metric}&timeframe=${timeframe}`);
    }
  }, [drillDownEnabled, timeframe, router, addEntry]);

  const [metrics, setMetrics] = useState<KPIMetrics>({
    total_revenue: 452652,
    total_leads: 2345,
    conversion_rate: 4.2,
    hot_leads: 98,
    jorge_commission: 27159.12,
    avg_response_time_ms: 42.3,
    bot_success_rate: 94.2,
    pipeline_value: 2840000
  });

  const [comparisons, setComparisons] = useState<KPIComparisons>({
    revenue_change: 13.2,
    leads_change: 23.9,
    conversion_change: 10.1,
    hot_leads_change: 45.3,
    jorge_commission_change: 18.7
  });

  const [trends, setTrends] = useState<KPITrends>({
    revenue_trend: [],
    leads_trend: [],
    conversion_trend: []
  });

  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // WebSocket connection for real-time updates
  useEffect(() => {
    if (!realtimeUpdates) return;

    const connectWebSocket = () => {
      const ws = new WebSocket(`${process.env.NEXT_PUBLIC_SOCKET_URL?.replace('http', 'ws')}/ws/dashboard/${locationId}`);

      ws.onopen = () => {
        console.log('BI Dashboard WebSocket connected');
        addEntry({
          timestamp: new Date().toISOString(),
          agent: 'bi_dashboard',
          key: 'websocket_status',
          value: 'connected'
        });
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.event_type === 'REALTIME_BI_UPDATE') {
            updateMetricsFromEvent(data.data);
            setLastUpdated(new Date());
          }
        } catch (error) {
          console.error('WebSocket message parsing error:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected, attempting reconnect...');
        setTimeout(connectWebSocket, 5000);
      };

      return ws;
    };

    const ws = connectWebSocket();
    return () => ws?.close();
  }, [realtimeUpdates, locationId, addEntry]);

  const updateMetricsFromEvent = useCallback((eventData: any) => {
    if (eventData.metrics) {
      setMetrics(prev => ({ ...prev, ...eventData.metrics }));
    }
    if (eventData.comparisons) {
      setComparisons(prev => ({ ...prev, ...eventData.comparisons }));
    }
    if (eventData.trends) {
      setTrends(prev => ({ ...prev, ...eventData.trends }));
    }
  }, []);

  // Fetch initial data and periodic updates
  const fetchData = useCallback(async () => {
    if (isLoading) return;

    setIsLoading(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE}/api/bi/dashboard-kpis?location_id=${locationId}&timeframe=${timeframe}`
      );
      const data = await response.json();

      setMetrics(data.metrics || metrics);
      setComparisons(data.comparisons || comparisons);
      setTrends(data.trends || trends);
      setLastUpdated(new Date());

      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'bi_dashboard',
        key: 'kpi_refresh',
        value: `Updated ${Object.keys(data.metrics || {}).length} metrics`
      });
    } catch (error) {
      console.error("KPI fetch error:", error);
    } finally {
      setIsLoading(false);
    }
  }, [timeframe, locationId, isLoading, metrics, comparisons, trends, addEntry]);

  useEffect(() => {
    fetchData();

    // Periodic refresh (fallback if WebSocket fails)
    const interval = setInterval(fetchData, 30000); // 30 seconds
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleKPIClick = useCallback((kpiType: string) => {
    if (!drillDownEnabled) return;

    addEntry({
      timestamp: new Date().toISOString(),
      agent: 'bi_dashboard',
      key: 'drill_down_navigation',
      value: `Navigating to ${kpiType} details`
    });

    // Navigate to detailed view
    router.push(`/analytics/${kpiType}?timeframe=${timeframe}&location=${locationId}`);
  }, [drillDownEnabled, router, timeframe, locationId, addEntry]);

  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatNumber = (value: number): string => {
    return new Intl.NumberFormat('en-US').format(value);
  };

  const formatPercentage = (value: number): string => {
    return `${value.toFixed(1)}%`;
  };

  const getDeltaType = (change: number): "increase" | "decrease" | "moderateIncrease" | "moderateDecrease" | "unchanged" => {
    if (change > 15) return "increase";
    if (change > 5) return "moderateIncrease";
    if (change < -15) return "decrease";
    if (change < -5) return "moderateDecrease";
    return "unchanged";
  };

  const getIcon = (type: string) => {
    const iconClass = "h-5 w-5";
    switch (type) {
      case 'revenue': return <DollarSign className={iconClass} />;
      case 'leads': return <Users className={iconClass} />;
      case 'conversion': return <Target className={iconClass} />;
      case 'hot_leads': return <TrendingUp className={iconClass} />;
      case 'jorge_commission': return <DollarSign className={iconClass} />;
      case 'response_time': return <Zap className={iconClass} />;
      case 'bot_success': return <Brain className={iconClass} />;
      case 'pipeline': return <Activity className={iconClass} />;
      default: return <Activity className={iconClass} />;
    }
  };

  const kpis = [
    {
      id: 'revenue',
      title: "Total Revenue Pipeline",
      metric: formatCurrency(metrics.pipeline_value),
      delta: formatPercentage(comparisons.revenue_change),
      deltaType: getDeltaType(comparisons.revenue_change),
      icon: getIcon('revenue'),
      sparkData: trends.revenue_trend,
      description: "Total revenue in pipeline",
      drillDownUrl: "/analytics/revenue"
    },
    {
      id: 'leads',
      title: "Active Leads",
      metric: formatNumber(metrics.total_leads),
      delta: formatPercentage(comparisons.leads_change),
      deltaType: getDeltaType(comparisons.leads_change),
      icon: getIcon('leads'),
      sparkData: trends.leads_trend,
      description: "Total active leads",
      drillDownUrl: "/analytics/leads"
    },
    {
      id: 'hot_leads',
      title: "Hot Leads",
      metric: formatNumber(metrics.hot_leads),
      delta: formatPercentage(comparisons.hot_leads_change),
      deltaType: getDeltaType(comparisons.hot_leads_change),
      icon: getIcon('hot_leads'),
      sparkData: trends.conversion_trend,
      description: "High-intent qualified leads",
      drillDownUrl: "/analytics/conversion"
    },
    {
      id: 'jorge_commission',
      title: "Jorge's Commission (6%)",
      metric: formatCurrency(metrics.jorge_commission),
      delta: formatPercentage(comparisons.jorge_commission_change),
      deltaType: getDeltaType(comparisons.jorge_commission_change),
      icon: getIcon('jorge_commission'),
      sparkData: trends.revenue_trend,
      description: "Jorge's 6% commission tracking",
      drillDownUrl: "/analytics/jorge-commission",
      highlight: jorgeCommission
    },
    {
      id: 'response_time',
      title: "ML Response Time",
      metric: `${metrics.avg_response_time_ms.toFixed(1)}ms`,
      delta: "< 50ms target",
      deltaType: metrics.avg_response_time_ms < 50 ? "increase" : "moderateDecrease",
      icon: getIcon('response_time'),
      sparkData: [],
      description: "Average ML inference time",
      drillDownUrl: "/analytics/performance"
    },
    {
      id: 'bot_success',
      title: "Bot Success Rate",
      metric: formatPercentage(metrics.bot_success_rate),
      delta: "94%+ target",
      deltaType: metrics.bot_success_rate >= 94 ? "increase" : "moderateDecrease",
      icon: getIcon('bot_success'),
      sparkData: [],
      description: "Jorge bot ecosystem success",
      drillDownUrl: "/analytics/bots"
    }
  ];

  return (
    <div className="space-y-6">
      {/* Real-time Status Indicator */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-100">Executive Dashboard</h2>
        <div className="flex items-center space-x-4">
          <div className={`flex items-center space-x-2 text-sm ${realtimeUpdates ? 'text-green-400' : 'text-slate-400'}`}>
            <div className={`h-2 w-2 rounded-full ${realtimeUpdates ? 'bg-green-400 animate-pulse' : 'bg-slate-400'}`} />
            <span>{realtimeUpdates ? 'Live' : 'Static'}</span>
          </div>
          <Text className="text-slate-500 text-sm">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </Text>
        </div>
      </div>

      {/* Enhanced KPI Grid */}
      <Grid numItemsSm={1} numItemsMd={2} numItemsLg={3} className="gap-6">
        {kpis.map((kpi) => (
          <Card
            key={kpi.id}
            className={`
              bg-slate-900 border-slate-800 transition-all duration-200
              ${drillDownEnabled ? 'hover:border-slate-600 hover:shadow-lg cursor-pointer' : ''}
              ${kpi.highlight ? 'border-blue-500/50 bg-blue-950/20' : ''}
              ${isLoading ? 'opacity-50' : ''}
            `}
            onClick={() => handleKPIClick(kpi.id)}
          >
            {/* Header with Icon */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <div className={`p-2 rounded-lg ${kpi.highlight ? 'bg-blue-500/20 text-blue-400' : 'bg-slate-800 text-slate-400'}`}>
                  {kpi.icon}
                </div>
                <Text className="text-slate-400 font-medium">{kpi.title}</Text>
              </div>
              {drillDownEnabled && (
                <div className="text-slate-600 hover:text-slate-400 transition-colors">
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              )}
            </div>

            {/* Main Metric */}
            <Flex justifyContent="start" alignItems="baseline" className="space-x-3 mb-4">
              <Metric className={`text-2xl font-bold ${kpi.highlight ? 'text-blue-100' : 'text-slate-100'}`}>
                {kpi.metric}
              </Metric>
            </Flex>

            {/* Trend Sparkline (if data available) */}
            {kpi.sparkData && kpi.sparkData.length > 0 && (
              <div className="mb-3">
                <SparkAreaChart
                  data={kpi.sparkData}
                  categories={["value"]}
                  index="hour"
                  colors={[kpi.highlight ? "blue" : "slate"]}
                  className="h-8"
                />
              </div>
            )}

            {/* Delta and Description */}
            <Flex justifyContent="between" className="mt-4">
              <div className="flex items-center space-x-2">
                <BadgeDelta deltaType={kpi.deltaType} />
                <Text className="text-slate-500 text-sm">{kpi.delta}</Text>
              </div>
              {drillDownEnabled && (
                <Text className="text-slate-600 text-xs hover:text-slate-400 transition-colors">
                  View details →
                </Text>
              )}
            </Flex>

            {/* Description */}
            <Text className="text-slate-600 text-xs mt-2">{kpi.description}</Text>

            {/* Jorge Commission Special Highlight */}
            {kpi.id === 'jorge_commission' && jorgeCommission && (
              <div className="mt-3 p-2 bg-blue-500/10 rounded-lg border border-blue-500/20">
                <Text className="text-blue-400 text-xs font-medium">
                  🎯 Auto-calculated from ${formatCurrency(metrics.pipeline_value)} pipeline
                </Text>
              </div>
            )}
          </Card>
        ))}
      </Grid>

      {/* Timeframe Selector */}
      <div className="flex items-center justify-center space-x-2 mt-6">
        {(['24h', '7d', '30d', '90d'] as const).map((tf) => (
          <button
            key={tf}
            onClick={() => {
              // Would trigger parent component timeframe change
              addEntry({
                timestamp: new Date().toISOString(),
                agent: 'bi_dashboard',
                key: 'timeframe_change',
                value: tf
              });
            }}
            className={`
              px-3 py-1 rounded-md text-sm font-medium transition-colors
              ${timeframe === tf
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }
            `}
          >
            {tf}
          </button>
        ))}
      </div>
    </div>
  );
}
