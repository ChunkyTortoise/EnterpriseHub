"use client";

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Area,
  AreaChart,
  ComposedChart,
  Legend
} from 'recharts'
import {
  Bot,
  DollarSign,
  Target,
  TrendingUp,
  Users,
  Clock,
  Star,
  Zap,
  Award,
  Activity,
  CheckCircle,
  AlertTriangle
} from 'lucide-react'
import { useAnalytics } from '@/hooks/useAnalytics'
import { BotMetricsChart } from './BotMetricsChart'
import { RevenueAnalysis } from './RevenueAnalysis'
import { LeadQualityMetrics } from './LeadQualityMetrics'
import { CompetitiveAnalysis } from './CompetitiveAnalysis'

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#06B6D4']

export function PerformanceReports() {
  const {
    metrics,
    benchmarkComparisons,
    revenueWaterfallData,
    comparisonChartData,
    insights,
    isLoading,
    formatMetric
  } = useAnalytics()

  if (isLoading || !metrics) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i} className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="animate-pulse">
                  <div className="h-4 bg-slate-600 rounded w-3/4 mb-2"></div>
                  <div className="h-8 bg-slate-600 rounded w-1/2 mb-2"></div>
                  <div className="h-4 bg-slate-600 rounded w-1/4"></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  // Prepare chart data
  const botPerformanceData = metrics.botMetrics.map(bot => ({
    name: bot.botName.replace(' Bot', ''),
    accuracy: bot.accuracy * 100,
    responseTime: bot.responseTime.average,
    satisfaction: bot.clientSatisfactionScore,
    conversion: bot.conversionRate * 100,
    volume: bot.conversationVolume
  }))

  const leadQualityDistribution = [
    { name: 'Hot (75-100)', value: metrics.leadMetrics.scoreDistribution.hot, color: '#EF4444' },
    { name: 'Warm (50-74)', value: metrics.leadMetrics.scoreDistribution.warm, color: '#F59E0B' },
    { name: 'Lukewarm (26-49)', value: metrics.leadMetrics.scoreDistribution.lukewarm, color: '#06B6D4' },
    { name: 'Cold (0-25)', value: metrics.leadMetrics.scoreDistribution.cold, color: '#64748B' }
  ]

  const competitiveData = benchmarkComparisons.slice(0, 6).map(comp => ({
    metric: comp.metric,
    jorge: comp.jorgeValue,
    industry: comp.industryAverage,
    improvement: comp.improvement * 100
  }))

  const roiProjectionData = [
    { month: 'Jan', revenue: 180000, cost: 2500, roi: 7100 },
    { month: 'Feb', revenue: 195000, cost: 2500, roi: 7700 },
    { month: 'Mar', revenue: 210000, cost: 2500, roi: 8300 },
    { month: 'Apr', revenue: 225000, cost: 2500, roi: 8900 },
    { month: 'May', revenue: 240000, cost: 2500, roi: 9500 },
    { month: 'Jun', revenue: 255000, cost: 2500, roi: 10100 }
  ]

  // Hero metrics
  const heroMetrics = [
    {
      title: 'Total Revenue Impact',
      value: formatMetric(metrics.revenueMetrics.totalRevenue, 'currency'),
      change: `+${((metrics.revenueMetrics.monthlyROI) * 100).toFixed(1)}% ROI`,
      changeType: 'positive',
      icon: DollarSign,
      description: '8.3x return on AI investment'
    },
    {
      title: 'Jorge Seller Bot',
      value: `${(metrics.botMetrics.find(b => b.botType === 'jorge-seller')?.accuracy * 100 || 0).toFixed(1)}%`,
      change: '+480% vs industry',
      changeType: 'positive',
      icon: Bot,
      description: 'Qualification accuracy rate'
    },
    {
      title: 'Response Time',
      value: '2 min',
      change: '99.8% faster',
      changeType: 'positive',
      icon: Clock,
      description: 'vs 24-hour industry average'
    },
    {
      title: 'Client Satisfaction',
      value: `${metrics.clientSatisfaction.overallSatisfaction}/5`,
      change: `NPS: ${metrics.clientSatisfaction.npsScore}`,
      changeType: 'positive',
      icon: Star,
      description: '50% above industry average'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Hero Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {heroMetrics.map((metric) => (
          <Card key={metric.title} className="bg-gradient-to-r from-slate-800/50 to-blue-900/20 border-slate-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-400">{metric.title}</p>
                  <p className="text-3xl font-bold text-white">{metric.value}</p>
                  <p className="text-sm text-green-400">{metric.change}</p>
                  <p className="text-xs text-slate-500 mt-1">{metric.description}</p>
                </div>
                <div className="p-3 rounded-full bg-blue-600/20">
                  <metric.icon className="h-8 w-8 text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Analytics Tabs */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5 bg-slate-800 border-slate-700">
          <TabsTrigger value="overview" className="data-[state=active]:bg-blue-600">
            <Activity className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="bots" className="data-[state=active]:bg-blue-600">
            <Bot className="h-4 w-4 mr-2" />
            Bot Performance
          </TabsTrigger>
          <TabsTrigger value="revenue" className="data-[state=active]:bg-blue-600">
            <DollarSign className="h-4 w-4 mr-2" />
            Revenue
          </TabsTrigger>
          <TabsTrigger value="leads" className="data-[state=active]:bg-blue-600">
            <Users className="h-4 w-4 mr-2" />
            Leads
          </TabsTrigger>
          <TabsTrigger value="competitive" className="data-[state=active]:bg-blue-600">
            <Award className="h-4 w-4 mr-2" />
            Competitive
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Jorge AI vs Competition */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Jorge AI vs Industry Average
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={comparisonChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="metric" stroke="#9CA3AF" fontSize={12} />
                    <YAxis stroke="#9CA3AF" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1F2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        color: '#F3F4F6'
                      }}
                      formatter={(value, name) => [
                        name === 'before' ? 'Before Jorge AI' : 'After Jorge AI',
                        name === 'before' ? value : `${value} (+${comparisonChartData.find(d => d.before === value || d.after === value)?.improvement}%)`
                      ]}
                    />
                    <Bar dataKey="before" fill="#64748B" name="Before" />
                    <Bar dataKey="after" fill="#3B82F6" name="After" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* ROI Projection */}
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <DollarSign className="h-5 w-5" />
                  ROI Projection (6 Months)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={roiProjectionData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="month" stroke="#9CA3AF" fontSize={12} />
                    <YAxis stroke="#9CA3AF" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1F2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        color: '#F3F4F6'
                      }}
                      formatter={(value, name) => [
                        formatMetric(Number(value), name === 'roi' ? 'percentage' : 'currency'),
                        name === 'revenue' ? 'Revenue' : name === 'cost' ? 'AI Cost' : 'ROI %'
                      ]}
                    />
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      fill="#3B82F6"
                      fillOpacity={0.2}
                      stroke="#3B82F6"
                      strokeWidth={2}
                    />
                    <Bar dataKey="roi" fill="#10B981" />
                  </ComposedChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Lead Quality Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Lead Quality Distribution
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={leadQualityDistribution}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {leadQualityDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1F2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                        color: '#F3F4F6'
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="mt-4 space-y-2">
                  {leadQualityDistribution.map((item, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                      <span className="text-sm text-slate-300">{item.name}: {item.value}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Key Insights */}
            <Card className="lg:col-span-2 bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Key Performance Insights
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {insights.slice(0, 3).map((insight) => (
                    <div key={insight.id} className="p-4 rounded-lg bg-slate-700/30 border border-slate-600">
                      <div className="flex items-start gap-3">
                        <div className={`p-2 rounded-full ${
                          insight.impact === 'high' ? 'bg-red-900/50 text-red-400' :
                          insight.impact === 'medium' ? 'bg-yellow-900/50 text-yellow-400' :
                          'bg-green-900/50 text-green-400'
                        }`}>
                          <TrendingUp className="h-4 w-4" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between mb-2">
                            <h4 className="font-medium text-white">{insight.title}</h4>
                            <Badge
                              className={`${
                                insight.impact === 'high' ? 'bg-red-900 text-red-200' :
                                insight.impact === 'medium' ? 'bg-yellow-900 text-yellow-200' :
                                'bg-green-900 text-green-200'
                              }`}
                            >
                              {insight.impact}
                            </Badge>
                          </div>
                          <p className="text-slate-300 text-sm">{insight.description}</p>
                          {insight.recommendation && (
                            <div className="mt-2 p-2 bg-blue-900/20 border border-blue-800/50 rounded text-sm">
                              <p className="text-blue-200"><strong>Recommendation:</strong> {insight.recommendation}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Bot Performance Tab */}
        <TabsContent value="bots">
          <BotMetricsChart />
        </TabsContent>

        {/* Revenue Tab */}
        <TabsContent value="revenue">
          <RevenueAnalysis />
        </TabsContent>

        {/* Leads Tab */}
        <TabsContent value="leads">
          <LeadQualityMetrics />
        </TabsContent>

        {/* Competitive Tab */}
        <TabsContent value="competitive">
          <CompetitiveAnalysis />
        </TabsContent>
      </Tabs>
    </div>
  )
}