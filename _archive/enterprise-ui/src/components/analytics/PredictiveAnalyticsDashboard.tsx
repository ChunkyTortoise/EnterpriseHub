/**
 * Predictive Analytics Dashboard - Jorge's Crystal Ball Technology
 * Comprehensive visualization of market predictions, client behavior, and business forecasting
 */

'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import {
  TrendingUp,
  TrendingDown,
  Brain,
  Target,
  DollarSign,
  Users,
  MapPin,
  Calendar,
  AlertTriangle,
  CheckCircle,
  Clock,
  Zap,
  Eye,
  Lightbulb
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ScatterPlot,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar
} from 'recharts';
import usePredictiveIntelligence, {
  MarketMovementPrediction,
  ClientBehaviorPrediction,
  DealOutcomePrediction,
  BusinessForecast
} from '@/hooks/usePredictiveIntelligence';

interface DashboardProps {
  className?: string;
  refreshInterval?: number;
}

const PredictiveAnalyticsDashboard: React.FC<DashboardProps> = ({
  className = '',
  refreshInterval = 300000 // 5 minutes
}) => {
  const {
    predictMarketMovement,
    predictClientBehavior,
    predictDealOutcome,
    generateBusinessForecast,
    requestBulkPredictions,
    isConnected
  } = usePredictiveIntelligence();

  // Dashboard state
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  // Prediction data state
  const [marketPredictions, setMarketPredictions] = useState<MarketMovementPrediction[]>([]);
  const [clientPredictions, setClientPredictions] = useState<ClientBehaviorPrediction[]>([]);
  const [dealPredictions, setDealPredictions] = useState<DealOutcomePrediction[]>([]);
  const [businessForecast, setBusinessForecast] = useState<BusinessForecast | null>(null);

  // Performance tracking
  const [predictionAccuracy, setPredictionAccuracy] = useState({
    market: 87.5,
    client: 91.2,
    deals: 93.8,
    business: 95.1
  });

  // Mock data for demonstration (replace with real data loading)
  const mockMarketData = [
    { month: 'Jan', predicted: 520000, actual: 518000, accuracy: 96.2 },
    { month: 'Feb', predicted: 535000, actual: 542000, accuracy: 98.7 },
    { month: 'Mar', predicted: 545000, actual: 548000, accuracy: 99.4 },
    { month: 'Apr', predicted: 558000, actual: null, accuracy: null }
  ];

  const mockClientBehaviorData = [
    { segment: 'Hot Leads', probability: 85, count: 23, avgValue: 450000 },
    { segment: 'Warm Prospects', probability: 65, count: 47, avgValue: 380000 },
    { segment: 'Cold Inquiries', probability: 25, count: 89, avgValue: 320000 },
    { segment: 'Referrals', probability: 78, count: 12, avgValue: 520000 }
  ];

  const mockDealPipelineData = [
    { stage: 'Initial Contact', deals: 45, avgProbability: 30, totalValue: 15750000 },
    { stage: 'Property Viewing', deals: 28, avgProbability: 55, totalValue: 12600000 },
    { stage: 'Offer Submitted', deals: 18, avgProbability: 75, totalValue: 9450000 },
    { stage: 'Under Contract', deals: 12, avgProbability: 92, totalValue: 6840000 },
    { stage: 'Closing', deals: 8, avgProbability: 98, totalValue: 4560000 }
  ];

  // Load dashboard data
  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      // Load business forecast
      const forecast = await generateBusinessForecast('revenue', 'quarterly');
      setBusinessForecast(forecast);

      // Load market predictions for key areas
      const marketLocations = [
        { lat: 40.7128, lng: -74.0060 }, // NYC
        { lat: 34.0522, lng: -118.2437 }, // LA
        { lat: 41.8781, lng: -87.6298 } // Chicago
      ];

      const marketPromises = marketLocations.map(location =>
        predictMarketMovement(location, 'medium_term')
      );
      const markets = await Promise.all(marketPromises);
      setMarketPredictions(markets);

      // Mock client predictions (replace with real API calls)
      // const clientPromises = activeClients.map(client =>
      //   predictClientBehavior(client.id, 'purchase_timing')
      // );
      // const clients = await Promise.all(clientPromises);
      // setClientPredictions(clients);

      setLastRefresh(new Date());
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-refresh dashboard
  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  // Calculate summary metrics
  const summaryMetrics = useMemo(() => {
    const avgMarketAccuracy = predictionAccuracy.market;
    const avgClientAccuracy = predictionAccuracy.client;
    const avgDealAccuracy = predictionAccuracy.deals;
    const totalDealsInPipeline = mockDealPipelineData.reduce((sum, stage) => sum + stage.deals, 0);
    const totalPipelineValue = mockDealPipelineData.reduce((sum, stage) => sum + stage.totalValue, 0);
    const avgDealValue = totalPipelineValue / totalDealsInPipeline;

    return {
      avgMarketAccuracy,
      avgClientAccuracy,
      avgDealAccuracy,
      totalDealsInPipeline,
      totalPipelineValue,
      avgDealValue
    };
  }, [predictionAccuracy]);

  // Market trends analysis
  const marketTrends = useMemo(() => {
    return marketPredictions.map(prediction => ({
      location: prediction.location_id,
      currentPrice: prediction.current_median_price,
      predicted30Day: prediction.predicted_price_30_days,
      predicted90Day: prediction.predicted_price_90_days,
      changePercent: prediction.price_change_percentage,
      velocity: prediction.market_velocity,
      jorgeAdvantage: prediction.jorge_advantage_score
    }));
  }, [marketPredictions]);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white">Jorge's Crystal Ball</h2>
          <p className="text-gray-400 mt-1">Predictive Intelligence Dashboard</p>
        </div>

        <div className="flex items-center gap-4">
          <Badge variant={isConnected ? 'success' : 'destructive'} className="px-3 py-1">
            {isConnected ? 'Live' : 'Offline'}
          </Badge>

          <div className="text-sm text-gray-400">
            Last updated: {lastRefresh.toLocaleTimeString()}
          </div>

          <Button onClick={loadDashboardData} disabled={isLoading} variant="outline">
            {isLoading ? 'Updating...' : 'Refresh'}
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Overall Accuracy</p>
                  <p className="text-2xl font-bold text-green-400">
                    {((summaryMetrics.avgMarketAccuracy + summaryMetrics.avgClientAccuracy + summaryMetrics.avgDealAccuracy) / 3).toFixed(1)}%
                  </p>
                </div>
                <Brain className="h-8 w-8 text-green-400" />
              </div>
              <Progress value={92.1} className="mt-4" />
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Pipeline Value</p>
                  <p className="text-2xl font-bold text-blue-400">
                    ${(summaryMetrics.totalPipelineValue / 1000000).toFixed(1)}M
                  </p>
                </div>
                <DollarSign className="h-8 w-8 text-blue-400" />
              </div>
              <div className="mt-2 flex items-center text-sm">
                <TrendingUp className="h-4 w-4 text-green-400 mr-1" />
                <span className="text-green-400">+15.3%</span>
                <span className="text-gray-400 ml-1">vs last month</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Active Deals</p>
                  <p className="text-2xl font-bold text-purple-400">
                    {summaryMetrics.totalDealsInPipeline}
                  </p>
                </div>
                <Target className="h-8 w-8 text-purple-400" />
              </div>
              <div className="mt-2 flex items-center text-sm">
                <CheckCircle className="h-4 w-4 text-green-400 mr-1" />
                <span className="text-gray-400">85% close probability</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          <Card className="bg-gray-800/50 border-gray-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm">Avg Deal Value</p>
                  <p className="text-2xl font-bold text-yellow-400">
                    ${Math.round(summaryMetrics.avgDealValue / 1000)}K
                  </p>
                </div>
                <Zap className="h-8 w-8 text-yellow-400" />
              </div>
              <div className="mt-2 flex items-center text-sm">
                <Calendar className="h-4 w-4 text-blue-400 mr-1" />
                <span className="text-gray-400">28 days avg close</span>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Main Dashboard Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-gray-800 border-gray-700">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <Eye className="h-4 w-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="market" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Market Intelligence
          </TabsTrigger>
          <TabsTrigger value="clients" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Client Behavior
          </TabsTrigger>
          <TabsTrigger value="deals" className="flex items-center gap-2">
            <Target className="h-4 w-4" />
            Deal Outcomes
          </TabsTrigger>
          <TabsTrigger value="business" className="flex items-center gap-2">
            <DollarSign className="h-4 w-4" />
            Business Forecast
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Prediction Accuracy Radar */}
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  Prediction Accuracy
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={[
                    { subject: 'Market', accuracy: predictionAccuracy.market, fullMark: 100 },
                    { subject: 'Clients', accuracy: predictionAccuracy.client, fullMark: 100 },
                    { subject: 'Deals', accuracy: predictionAccuracy.deals, fullMark: 100 },
                    { subject: 'Business', accuracy: predictionAccuracy.business, fullMark: 100 }
                  ]}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                    <PolarRadiusAxis
                      angle={90}
                      domain={[0, 100]}
                      tick={{ fill: '#9CA3AF', fontSize: 10 }}
                    />
                    <Radar
                      name="Accuracy"
                      dataKey="accuracy"
                      stroke="#10B981"
                      fill="#10B981"
                      fillOpacity={0.3}
                      strokeWidth={2}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Real-time Opportunities */}
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Lightbulb className="h-5 w-5" />
                  Jorge's Advantage Opportunities
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <motion.div
                    className="p-4 bg-green-500/20 rounded-lg border border-green-500/30"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-green-400 font-medium">High Market Leverage</p>
                        <p className="text-sm text-gray-300">Downtown NYC - seller's market weakening</p>
                      </div>
                      <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                        Hot
                      </Badge>
                    </div>
                  </motion.div>

                  <motion.div
                    className="p-4 bg-blue-500/20 rounded-lg border border-blue-500/30"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 }}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-blue-400 font-medium">Client Ready to Move</p>
                        <p className="text-sm text-gray-300">Sarah Johnson - 89% purchase probability</p>
                      </div>
                      <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                        Urgent
                      </Badge>
                    </div>
                  </motion.div>

                  <motion.div
                    className="p-4 bg-purple-500/20 rounded-lg border border-purple-500/30"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-purple-400 font-medium">Deal Acceleration</p>
                        <p className="text-sm text-gray-300">123 Oak St - apply pressure now</p>
                      </div>
                      <Badge className="bg-purple-500/20 text-purple-400 border-purple-500/30">
                        Action
                      </Badge>
                    </div>
                  </motion.div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Market Overview Chart */}
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Market Prediction vs Reality
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={mockMarketData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="month" tick={{ fill: '#9CA3AF' }} />
                  <YAxis tick={{ fill: '#9CA3AF' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px'
                    }}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="predicted"
                    stroke="#3B82F6"
                    strokeWidth={2}
                    name="Predicted Price"
                  />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    stroke="#10B981"
                    strokeWidth={2}
                    name="Actual Price"
                    connectNulls={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Market Intelligence Tab */}
        <TabsContent value="market" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {marketTrends.map((market, index) => (
              <motion.div
                key={market.location}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Card className="bg-gray-800/50 border-gray-700">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <MapPin className="h-4 w-4" />
                      {market.location}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Current Price</span>
                        <span className="text-white font-medium">
                          ${market.currentPrice.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">30-Day Forecast</span>
                        <span className="text-green-400 font-medium">
                          ${market.predicted30Day.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">90-Day Forecast</span>
                        <span className="text-blue-400 font-medium">
                          ${market.predicted90Day.toLocaleString()}
                        </span>
                      </div>
                    </div>

                    <div className="pt-4 border-t border-gray-700">
                      <div className="flex justify-between items-center">
                        <span className="text-gray-400">Jorge Advantage</span>
                        <div className="flex items-center gap-2">
                          <Progress value={market.jorgeAdvantage} className="w-16" />
                          <span className="text-yellow-400 font-medium">
                            {market.jorgeAdvantage}%
                          </span>
                        </div>
                      </div>
                    </div>

                    <Badge
                      className={`w-full justify-center ${
                        market.velocity === 'accelerating'
                          ? 'bg-green-500/20 text-green-400 border-green-500/30'
                          : market.velocity === 'slowing'
                          ? 'bg-red-500/20 text-red-400 border-red-500/30'
                          : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                      }`}
                    >
                      {market.velocity.charAt(0).toUpperCase() + market.velocity.slice(1)} Market
                    </Badge>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        {/* Client Behavior Tab */}
        <TabsContent value="clients" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white">Client Segment Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={mockClientBehaviorData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="segment" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
                    <YAxis tick={{ fill: '#9CA3AF' }} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1F2937',
                        border: '1px solid #374151',
                        borderRadius: '8px'
                      }}
                    />
                    <Bar dataKey="probability" fill="#3B82F6" name="Purchase Probability %" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card className="bg-gray-800/50 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white">Client Value Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={mockClientBehaviorData}
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="avgValue"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {mockClientBehaviorData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6'][index % 4]}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1F2937',
                        border: '1px solid #374151',
                        borderRadius: '8px'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Deal Outcomes Tab */}
        <TabsContent value="deals" className="space-y-6">
          <Card className="bg-gray-800/50 border-gray-700">
            <CardHeader>
              <CardTitle className="text-white">Deal Pipeline Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <AreaChart data={mockDealPipelineData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="stage" tick={{ fill: '#9CA3AF', fontSize: 10 }} />
                  <YAxis tick={{ fill: '#9CA3AF' }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px'
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="totalValue"
                    stroke="#3B82F6"
                    fill="#3B82F6"
                    fillOpacity={0.3}
                    name="Pipeline Value ($)"
                  />
                  <Area
                    type="monotone"
                    dataKey="avgProbability"
                    stroke="#10B981"
                    fill="#10B981"
                    fillOpacity={0.3}
                    name="Avg Probability (%)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Business Forecast Tab */}
        <TabsContent value="business" className="space-y-6">
          {businessForecast && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card className="bg-gray-800/50 border-gray-700">
                <CardHeader>
                  <CardTitle className="text-white">Revenue Forecast</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400">Base Forecast</span>
                      <span className="text-white font-bold text-xl">
                        ${businessForecast.revenue_forecast.base.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400">Optimistic</span>
                      <span className="text-green-400 font-medium">
                        ${businessForecast.revenue_forecast.optimistic.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400">Conservative</span>
                      <span className="text-red-400 font-medium">
                        ${businessForecast.revenue_forecast.conservative.toLocaleString()}
                      </span>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-gray-700">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-400">Confidence Level</span>
                      <div className="flex items-center gap-2">
                        <Progress value={businessForecast.revenue_forecast.confidence * 100} className="w-20" />
                        <span className="text-blue-400 font-medium">
                          {(businessForecast.revenue_forecast.confidence * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gray-800/50 border-gray-700">
                <CardHeader>
                  <CardTitle className="text-white">Growth Opportunities</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {businessForecast.business_opportunities.map((opportunity, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 bg-gray-700/50 rounded-lg border border-gray-600"
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-white font-medium">{opportunity.type}</p>
                          <p className="text-sm text-gray-400">
                            Market Size: ${(opportunity.market_size / 1000000).toFixed(1)}M
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-green-400 font-medium">
                            {opportunity.roi_projection.toFixed(1)}% ROI
                          </p>
                          <p className="text-sm text-gray-400">
                            {opportunity.success_probability.toFixed(0)}% success
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PredictiveAnalyticsDashboard;