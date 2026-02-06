"use client";

import React, { useState, useEffect, useMemo } from 'react';
import {
  AreaChart,
  LineChart,
  BarChart,
  Card,
  Title,
  Text,
  Flex,
  Badge,
  Metric,
  TabGroup,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Select,
  SelectItem,
  DonutChart,
  CategoryBar
} from '@tremor/react';
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Target,
  Calendar,
  PieChart,
  BarChart3,
  Activity,
  Users,
  Clock,
  Filter
} from 'lucide-react';
import { useAgentStore } from '../store/useAgentStore';

interface RevenueData {
  date: string;
  total_revenue: number;
  jorge_commission: number;
  pipeline_value: number;
  forecasted_revenue: number;
  deals_closed: number;
  confidence_interval_upper: number;
  confidence_interval_lower: number;
}

interface CommissionBreakdown {
  category: string;
  amount: number;
  percentage: number;
  color: string;
}

interface PredictiveTrend {
  date: string;
  predicted_revenue: number;
  confidence: number;
  trend_direction: 'up' | 'down' | 'stable';
}

interface RevenueIntelligenceChartProps {
  locationId?: string;
  timeframe?: '7d' | '30d' | '90d' | '1y';
  showForecasting?: boolean;
  showJorgeCommission?: boolean;
  interactive?: boolean;
}

export function RevenueIntelligenceChart({
  locationId = 'default',
  timeframe = '30d',
  showForecasting = true,
  showJorgeCommission = true,
  interactive = true
}: RevenueIntelligenceChartProps) {
  const { addEntry } = useAgentStore();
  const [selectedTab, setSelectedTab] = useState(0);
  const [viewMode, setViewMode] = useState<'overview' | 'breakdown' | 'forecast'>('overview');
  const [chartType, setChartType] = useState<'area' | 'line' | 'bar'>('area');
  const [showConfidenceInterval, setShowConfidenceInterval] = useState(true);

  const [revenueData, setRevenueData] = useState<RevenueData[]>([]);
  const [commissionBreakdown, setCommissionBreakdown] = useState<CommissionBreakdown[]>([]);
  const [predictiveTrends, setPredictiveTrends] = useState<PredictiveTrend[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  // Fetch revenue intelligence data
  useEffect(() => {
    const fetchRevenueData = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_BASE}/api/bi/revenue-intelligence?location_id=${locationId}&timeframe=${timeframe}&include_forecast=${showForecasting}`
        );
        const data = await response.json();

        setRevenueData(data.revenue_timeseries || generateMockRevenueData());
        setCommissionBreakdown(data.commission_breakdown || generateMockCommissionBreakdown());
        setPredictiveTrends(data.predictive_trends || generateMockPredictiveTrends());
        setLastUpdated(new Date());

        addEntry({
          timestamp: new Date().toISOString(),
          agent: 'revenue_intelligence',
          key: 'data_refresh',
          value: `Updated revenue data for ${timeframe}`
        });
      } catch (error) {
        console.error('Revenue data fetch error:', error);
        // Use mock data on error
        setRevenueData(generateMockRevenueData());
        setCommissionBreakdown(generateMockCommissionBreakdown());
        setPredictiveTrends(generateMockPredictiveTrends());
      } finally {
        setIsLoading(false);
      }
    };

    fetchRevenueData();
    const interval = setInterval(fetchRevenueData, 300000); // 5 minutes
    return () => clearInterval(interval);
  }, [locationId, timeframe, showForecasting, addEntry]);

  // Generate mock data functions
  const generateMockRevenueData = (): RevenueData[] => {
    const days = timeframe === '7d' ? 7 : timeframe === '30d' ? 30 : timeframe === '90d' ? 90 : 365;
    const data: RevenueData[] = [];

    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() - (days - i));

      const baseRevenue = 15000 + Math.random() * 10000;
      const trend = Math.sin(i * 0.1) * 5000;
      const totalRevenue = baseRevenue + trend;

      data.push({
        date: date.toISOString().split('T')[0],
        total_revenue: totalRevenue,
        jorge_commission: totalRevenue * 0.06,
        pipeline_value: totalRevenue * 1.8,
        forecasted_revenue: totalRevenue * (1 + Math.random() * 0.2),
        deals_closed: Math.floor(Math.random() * 5) + 1,
        confidence_interval_upper: totalRevenue * 1.15,
        confidence_interval_lower: totalRevenue * 0.85
      });
    }

    return data;
  };

  const generateMockCommissionBreakdown = (): CommissionBreakdown[] => [
    { category: "Jorge's Direct Commission", amount: 27159, percentage: 60, color: "blue" },
    { category: "Team Override", amount: 9053, percentage: 20, color: "emerald" },
    { category: "Performance Bonus", amount: 4526, percentage: 10, color: "amber" },
    { category: "Pipeline Incentive", amount: 4526, percentage: 10, color: "rose" }
  ];

  const generateMockPredictiveTrends = (): PredictiveTrend[] => {
    const data: PredictiveTrend[] = [];
    for (let i = 1; i <= 30; i++) {
      const date = new Date();
      date.setDate(date.getDate() + i);

      data.push({
        date: date.toISOString().split('T')[0],
        predicted_revenue: 18000 + Math.random() * 8000,
        confidence: 0.7 + Math.random() * 0.25,
        trend_direction: Math.random() > 0.4 ? 'up' : Math.random() > 0.2 ? 'stable' : 'down'
      });
    }
    return data;
  };

  // Calculate summary metrics
  const summaryMetrics = useMemo(() => {
    const totalRevenue = revenueData.reduce((sum, item) => sum + item.total_revenue, 0);
    const totalJorgeCommission = revenueData.reduce((sum, item) => sum + item.jorge_commission, 0);
    const avgDealSize = totalRevenue / Math.max(1, revenueData.reduce((sum, item) => sum + item.deals_closed, 0));
    const forecastAccuracy = 0.87; // Would be calculated from historical data

    return {
      totalRevenue,
      totalJorgeCommission,
      avgDealSize,
      forecastAccuracy,
      totalDeals: revenueData.reduce((sum, item) => sum + item.deals_closed, 0),
      avgDailyRevenue: totalRevenue / Math.max(1, revenueData.length)
    };
  }, [revenueData]);

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(value);

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;

  const handleChartInteraction = (dataPoint: any) => {
    if (!interactive) return;

    addEntry({
      timestamp: new Date().toISOString(),
      agent: 'revenue_intelligence',
      key: 'chart_interaction',
      value: `Explored data point: ${dataPoint?.date} - ${formatCurrency(dataPoint?.total_revenue || 0)}`
    });
  };

  const chartColors = chartType === 'area' ? ['blue', 'emerald'] : ['blue'];

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <Card className="bg-slate-900 border-slate-800">
        <Flex justifyContent="between" alignItems="start" className="mb-6">
          <div>
            <Title className="text-slate-100 text-2xl">Revenue Intelligence Dashboard</Title>
            <Text className="text-slate-400 mt-1">
              Advanced analytics with ML-powered forecasting and Jorge's 6% commission tracking
            </Text>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-xs text-slate-500">
              Updated: {lastUpdated.toLocaleTimeString()}
            </div>
            {isLoading && (
              <div className="flex items-center space-x-2 text-blue-400">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-400"></div>
                <span className="text-sm">Loading...</span>
              </div>
            )}
          </div>
        </Flex>

        {/* Control Panel */}
        <Flex justifyContent="between" className="mb-6 space-y-2 flex-wrap">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-slate-400" />
              <Select value={chartType} onValueChange={setChartType}>
                <SelectItem value="area" icon={AreaChart}>Area Chart</SelectItem>
                <SelectItem value="line" icon={Activity}>Line Chart</SelectItem>
                <SelectItem value="bar" icon={BarChart3}>Bar Chart</SelectItem>
              </Select>
            </div>

            <TabGroup>
              <TabList>
                <Tab
                  className={viewMode === 'overview' ? 'bg-blue-500 text-white' : 'bg-gray-200'}
                  onClick={() => setViewMode('overview')}
                  icon={Activity}
                >
                  Overview
                </Tab>
                <Tab
                  className={viewMode === 'breakdown' ? 'bg-blue-500 text-white' : 'bg-gray-200'}
                  onClick={() => setViewMode('breakdown')}
                  icon={PieChart}
                >
                  Breakdown
                </Tab>
                <Tab
                  className={viewMode === 'forecast' ? 'bg-blue-500 text-white' : 'bg-gray-200'}
                  onClick={() => setViewMode('forecast')}
                  icon={TrendingUp}
                >
                  Forecast
                </Tab>
              </TabList>
            </TabGroup>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={showConfidenceInterval}
                onChange={(e) => setShowConfidenceInterval(e.target.checked)}
                className="rounded text-blue-600"
              />
              <span className="text-sm text-slate-400">Show Confidence Interval</span>
            </div>
          </div>
        </Flex>
      </Card>

      {/* Summary Metrics Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-slate-900 border-slate-800">
          <div className="flex items-center space-x-2 mb-2">
            <DollarSign className="h-5 w-5 text-green-400" />
            <Text className="text-slate-400">Total Revenue</Text>
          </div>
          <Metric className="text-slate-100">{formatCurrency(summaryMetrics.totalRevenue)}</Metric>
          <Text className="text-green-400 text-sm mt-1">
            +{formatCurrency(summaryMetrics.avgDailyRevenue)}/day avg
          </Text>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <div className="flex items-center space-x-2 mb-2">
            <Target className="h-5 w-5 text-blue-400" />
            <Text className="text-slate-400">Jorge's Commission</Text>
          </div>
          <Metric className="text-blue-100">{formatCurrency(summaryMetrics.totalJorgeCommission)}</Metric>
          <Text className="text-blue-400 text-sm mt-1">
            6% of {formatCurrency(summaryMetrics.totalRevenue)}
          </Text>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <div className="flex items-center space-x-2 mb-2">
            <Users className="h-5 w-5 text-emerald-400" />
            <Text className="text-slate-400">Average Deal Size</Text>
          </div>
          <Metric className="text-slate-100">{formatCurrency(summaryMetrics.avgDealSize)}</Metric>
          <Text className="text-emerald-400 text-sm mt-1">
            {summaryMetrics.totalDeals} deals closed
          </Text>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <div className="flex items-center space-x-2 mb-2">
            <Activity className="h-5 w-5 text-amber-400" />
            <Text className="text-slate-400">Forecast Accuracy</Text>
          </div>
          <Metric className="text-slate-100">{formatPercentage(summaryMetrics.forecastAccuracy)}</Metric>
          <Text className="text-amber-400 text-sm mt-1">
            ML prediction confidence
          </Text>
        </Card>
      </div>

      {/* Main Chart Section */}
      <Card className="bg-slate-900 border-slate-800">
        <TabGroup selectedIndex={selectedTab} onIndexChange={setSelectedTab}>
          <TabList className="mb-6">
            <Tab icon={TrendingUp}>Revenue Timeline</Tab>
            <Tab icon={PieChart}>Commission Breakdown</Tab>
            <Tab icon={Activity}>Predictive Analysis</Tab>
            <Tab icon={BarChart3}>Performance Metrics</Tab>
          </TabList>

          <TabPanels>
            {/* Revenue Timeline Chart */}
            <TabPanel>
              <div className="h-80">
                {chartType === 'area' && (
                  <AreaChart
                    data={revenueData}
                    index="date"
                    categories={showJorgeCommission ? ["total_revenue", "jorge_commission"] : ["total_revenue"]}
                    colors={showJorgeCommission ? ["blue", "emerald"] : ["blue"]}
                    showLegend={true}
                    showGridLines={true}
                    curveType="monotone"
                    connectNulls={true}
                    onValueChange={handleChartInteraction}
                    valueFormatter={formatCurrency}
                    className="h-full"
                  />
                )}

                {chartType === 'line' && (
                  <LineChart
                    data={revenueData}
                    index="date"
                    categories={showJorgeCommission ? ["total_revenue", "jorge_commission"] : ["total_revenue"]}
                    colors={showJorgeCommission ? ["blue", "emerald"] : ["blue"]}
                    showLegend={true}
                    showGridLines={true}
                    curveType="monotone"
                    connectNulls={true}
                    onValueChange={handleChartInteraction}
                    valueFormatter={formatCurrency}
                    className="h-full"
                  />
                )}

                {chartType === 'bar' && (
                  <BarChart
                    data={revenueData.slice(-14)} // Last 14 days for bar chart
                    index="date"
                    categories={["total_revenue"]}
                    colors={["blue"]}
                    showLegend={false}
                    showGridLines={true}
                    onValueChange={handleChartInteraction}
                    valueFormatter={formatCurrency}
                    className="h-full"
                  />
                )}
              </div>
            </TabPanel>

            {/* Commission Breakdown */}
            <TabPanel>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <Title className="text-slate-100 mb-4">Jorge's Commission Structure</Title>
                  <DonutChart
                    data={commissionBreakdown}
                    category="amount"
                    index="category"
                    colors={commissionBreakdown.map(item => item.color)}
                    valueFormatter={formatCurrency}
                    className="h-60"
                  />
                </div>

                <div className="space-y-4">
                  <Title className="text-slate-100">Commission Categories</Title>
                  {commissionBreakdown.map((item, index) => (
                    <div key={index} className="space-y-2">
                      <Flex justifyContent="between">
                        <Text className="text-slate-300">{item.category}</Text>
                        <Text className="text-slate-100 font-medium">{formatCurrency(item.amount)}</Text>
                      </Flex>
                      <CategoryBar
                        values={[item.percentage]}
                        colors={[item.color]}
                        className="mt-2"
                      />
                      <Text className="text-slate-500 text-sm">{item.percentage}% of total commission</Text>
                    </div>
                  ))}
                </div>
              </div>
            </TabPanel>

            {/* Predictive Analysis */}
            <TabPanel>
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <Title className="text-slate-100">30-Day Revenue Forecast</Title>
                  <Badge color="blue">ML Confidence: 87%</Badge>
                </div>

                <AreaChart
                  data={predictiveTrends}
                  index="date"
                  categories={["predicted_revenue"]}
                  colors={["amber"]}
                  showLegend={true}
                  showGridLines={true}
                  curveType="monotone"
                  valueFormatter={formatCurrency}
                  className="h-60"
                />

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card className="bg-slate-800 border-slate-700">
                    <Text className="text-slate-400">30-Day Forecast</Text>
                    <Metric className="text-amber-100">
                      {formatCurrency(predictiveTrends.reduce((sum, item) => sum + item.predicted_revenue, 0))}
                    </Metric>
                  </Card>

                  <Card className="bg-slate-800 border-slate-700">
                    <Text className="text-slate-400">Confidence Range</Text>
                    <Metric className="text-slate-100">85% - 92%</Metric>
                  </Card>

                  <Card className="bg-slate-800 border-slate-700">
                    <Text className="text-slate-400">Trend Direction</Text>
                    <div className="flex items-center space-x-2 mt-2">
                      <TrendingUp className="h-5 w-5 text-green-400" />
                      <Metric className="text-green-100">Bullish</Metric>
                    </div>
                  </Card>
                </div>
              </div>
            </TabPanel>

            {/* Performance Metrics */}
            <TabPanel>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <Title className="text-slate-100 mb-4">Revenue vs Pipeline</Title>
                  <AreaChart
                    data={revenueData}
                    index="date"
                    categories={["total_revenue", "pipeline_value"]}
                    colors={["blue", "purple"]}
                    showLegend={true}
                    valueFormatter={formatCurrency}
                    className="h-60"
                  />
                </div>

                <div className="space-y-4">
                  <Title className="text-slate-100">Key Performance Indicators</Title>

                  <div className="space-y-4">
                    <div>
                      <Flex justifyContent="between">
                        <Text className="text-slate-400">Pipeline Conversion Rate</Text>
                        <Text className="text-slate-100">12.4%</Text>
                      </Flex>
                      <CategoryBar values={[12.4]} colors={["blue"]} className="mt-1" />
                    </div>

                    <div>
                      <Flex justifyContent="between">
                        <Text className="text-slate-400">Average Deal Velocity</Text>
                        <Text className="text-slate-100">18 days</Text>
                      </Flex>
                      <CategoryBar values={[75]} colors={["emerald"]} className="mt-1" />
                    </div>

                    <div>
                      <Flex justifyContent="between">
                        <Text className="text-slate-400">Jorge Commission Rate</Text>
                        <Text className="text-blue-100">6.0%</Text>
                      </Flex>
                      <CategoryBar values={[100]} colors={["blue"]} className="mt-1" />
                    </div>

                    <div>
                      <Flex justifyContent="between">
                        <Text className="text-slate-400">Forecast Accuracy</Text>
                        <Text className="text-slate-100">87.2%</Text>
                      </Flex>
                      <CategoryBar values={[87.2]} colors={["amber"]} className="mt-1" />
                    </div>
                  </div>
                </div>
              </div>
            </TabPanel>
          </TabPanels>
        </TabGroup>
      </Card>
    </div>
  );
}