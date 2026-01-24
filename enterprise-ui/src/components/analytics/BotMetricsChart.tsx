"use client";

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
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
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ComposedChart,
  Area
} from 'recharts'
import {
  Bot,
  Clock,
  Target,
  TrendingUp,
  Activity,
  CheckCircle,
  AlertTriangle,
  Star,
  Zap,
  Users
} from 'lucide-react'
import { useAnalytics } from '@/hooks/useAnalytics'

export function BotMetricsChart() {
  const { metrics, formatMetric, isLoading } = useAnalytics()

  if (isLoading || !metrics) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="bg-slate-800/50 border-slate-700">
            <CardContent className="p-6">
              <div className="animate-pulse">
                <div className="h-4 bg-slate-600 rounded w-3/4 mb-4"></div>
                <div className="h-40 bg-slate-600 rounded"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  // Prepare bot performance data
  const botPerformanceData = metrics.botMetrics.map(bot => ({
    name: bot.botName.replace(' Bot', ''),
    accuracy: (bot.accuracy * 100).toFixed(1),
    responseTime: bot.responseTime.average,
    satisfaction: bot.clientSatisfactionScore,
    conversations: bot.conversationVolume,
    conversion: (bot.conversionRate * 100).toFixed(1),
    uptime: (bot.uptime * 100).toFixed(1)
  }))

  // Radar chart data for comprehensive bot comparison
  const radarData = [
    {
      metric: 'Accuracy',
      'Jorge Seller': (metrics.botMetrics.find(b => b.botType === 'jorge-seller')?.accuracy || 0) * 100,
      'Lead Bot': (metrics.botMetrics.find(b => b.botType === 'lead-bot')?.accuracy || 0) * 100,
      'Intent Decoder': (metrics.botMetrics.find(b => b.botType === 'intent-decoder')?.accuracy || 0) * 100,
    },
    {
      metric: 'Satisfaction',
      'Jorge Seller': (metrics.botMetrics.find(b => b.botType === 'jorge-seller')?.clientSatisfactionScore || 0) * 20,
      'Lead Bot': (metrics.botMetrics.find(b => b.botType === 'lead-bot')?.clientSatisfactionScore || 0) * 20,
      'Intent Decoder': (metrics.botMetrics.find(b => b.botType === 'intent-decoder')?.clientSatisfactionScore || 0) * 20,
    },
    {
      metric: 'Conversion',
      'Jorge Seller': (metrics.botMetrics.find(b => b.botType === 'jorge-seller')?.conversionRate || 0) * 100,
      'Lead Bot': (metrics.botMetrics.find(b => b.botType === 'lead-bot')?.conversionRate || 0) * 100,
      'Intent Decoder': (metrics.botMetrics.find(b => b.botType === 'intent-decoder')?.conversionRate || 0) * 100,
    },
    {
      metric: 'Uptime',
      'Jorge Seller': (metrics.botMetrics.find(b => b.botType === 'jorge-seller')?.uptime || 0) * 100,
      'Lead Bot': (metrics.botMetrics.find(b => b.botType === 'lead-bot')?.uptime || 0) * 100,
      'Intent Decoder': (metrics.botMetrics.find(b => b.botType === 'intent-decoder')?.uptime || 0) * 100,
    }
  ]

  // Response time trends (simulated data for demonstration)
  const responseTimeTrends = [
    { time: '00:00', jorge: 1.2, lead: 0.3, decoder: 0.04 },
    { time: '04:00', jorge: 1.1, lead: 0.28, decoder: 0.038 },
    { time: '08:00', jorge: 1.3, lead: 0.35, decoder: 0.045 },
    { time: '12:00', jorge: 1.4, lead: 0.4, decoder: 0.05 },
    { time: '16:00', jorge: 1.25, lead: 0.32, decoder: 0.042 },
    { time: '20:00', jorge: 1.15, lead: 0.29, decoder: 0.039 }
  ]

  // Volume trends over the last week
  const volumeTrends = [
    { day: 'Mon', jorge: 45, lead: 32, decoder: 67 },
    { day: 'Tue', jorge: 52, lead: 38, decoder: 71 },
    { day: 'Wed', jorge: 38, lead: 29, decoder: 58 },
    { day: 'Thu', jorge: 61, lead: 42, decoder: 78 },
    { day: 'Fri', jorge: 48, lead: 35, decoder: 65 },
    { day: 'Sat', jorge: 23, lead: 18, decoder: 34 },
    { day: 'Sun', jorge: 19, lead: 15, decoder: 28 }
  ]

  // Bot status indicators
  const botStatusData = metrics.botMetrics.map(bot => {
    const getStatusColor = (uptime: number, errorRate: number) => {
      if (uptime > 0.99 && errorRate < 0.01) return 'green'
      if (uptime > 0.95 && errorRate < 0.05) return 'yellow'
      return 'red'
    }

    const status = getStatusColor(bot.uptime, bot.errorRate)

    return {
      ...bot,
      status,
      statusText: status === 'green' ? 'Excellent' : status === 'yellow' ? 'Good' : 'Needs Attention'
    }
  })

  return (
    <div className="space-y-6">
      {/* Bot Status Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {botStatusData.map((bot) => (
          <Card key={bot.botType} className="bg-slate-800/50 border-slate-700">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-white text-lg flex items-center gap-2">
                  <Bot className="h-5 w-5" />
                  {bot.botName}
                </CardTitle>
                <Badge
                  className={`${
                    bot.status === 'green' ? 'bg-green-900 text-green-200' :
                    bot.status === 'yellow' ? 'bg-yellow-900 text-yellow-200' :
                    'bg-red-900 text-red-200'
                  }`}
                >
                  {bot.statusText}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-400">Accuracy</p>
                  <p className="text-lg font-semibold text-white">{(bot.accuracy * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Uptime</p>
                  <p className="text-lg font-semibold text-white">{(bot.uptime * 100).toFixed(1)}%</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Conversations</p>
                  <p className="text-lg font-semibold text-white">{bot.conversationVolume}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400">Satisfaction</p>
                  <p className="text-lg font-semibold text-white">{bot.clientSatisfactionScore}/5</p>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-600">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4 text-slate-400" />
                  <span className="text-sm text-slate-300">
                    Avg Response: {formatMetric(bot.responseTime.average, 'time')}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-1">
                  <Target className="h-4 w-4 text-slate-400" />
                  <span className="text-sm text-slate-300">
                    Conversion: {(bot.conversionRate * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Detailed Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Comprehensive Bot Comparison Radar */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Multi-Dimensional Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#374151" />
                <PolarAngleAxis dataKey="metric" className="text-slate-300" fontSize={12} />
                <PolarRadiusAxis
                  domain={[0, 100]}
                  className="text-slate-400"
                  fontSize={10}
                />
                <Radar
                  name="Jorge Seller"
                  dataKey="Jorge Seller"
                  stroke="#EF4444"
                  fill="#EF4444"
                  fillOpacity={0.1}
                  strokeWidth={2}
                />
                <Radar
                  name="Lead Bot"
                  dataKey="Lead Bot"
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  fillOpacity={0.1}
                  strokeWidth={2}
                />
                <Radar
                  name="Intent Decoder"
                  dataKey="Intent Decoder"
                  stroke="#10B981"
                  fill="#10B981"
                  fillOpacity={0.1}
                  strokeWidth={2}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F3F4F6'
                  }}
                />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Response Time Trends */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Response Time Performance (24hrs)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={responseTimeTrends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9CA3AF" fontSize={12} />
                <YAxis stroke="#9CA3AF" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F3F4F6'
                  }}
                  formatter={(value, name) => [
                    `${Number(value).toFixed(2)}s`,
                    name === 'jorge' ? 'Jorge Seller' : name === 'lead' ? 'Lead Bot' : 'Intent Decoder'
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="jorge"
                  stroke="#EF4444"
                  strokeWidth={3}
                  dot={{ fill: '#EF4444', strokeWidth: 2, r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="lead"
                  stroke="#3B82F6"
                  strokeWidth={3}
                  dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="decoder"
                  stroke="#10B981"
                  strokeWidth={3}
                  dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Conversation Volume Trends */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Users className="h-5 w-5" />
              Weekly Conversation Volume
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={volumeTrends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="day" stroke="#9CA3AF" fontSize={12} />
                <YAxis stroke="#9CA3AF" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F3F4F6'
                  }}
                />
                <Bar dataKey="jorge" fill="#EF4444" name="Jorge Seller" />
                <Bar dataKey="lead" fill="#3B82F6" name="Lead Bot" />
                <Bar dataKey="decoder" fill="#10B981" name="Intent Decoder" />
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Jorge-Specific Performance Details */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Star className="h-5 w-5" />
              Jorge Seller Bot Excellence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-white">Confrontational Qualification</h4>
                  <Badge className="bg-green-900 text-green-200">87% Success</Badge>
                </div>
                <p className="text-sm text-slate-300">
                  Industry-leading qualification accuracy with stall-breaking methodology
                </p>
                <div className="mt-2 bg-slate-800 rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{ width: '87%' }}></div>
                </div>
              </div>

              <div className="p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-white">Temperature Scoring</h4>
                  <Badge className="bg-blue-900 text-blue-200">95% Accuracy</Badge>
                </div>
                <p className="text-sm text-slate-300">
                  Hot/Warm/Cold lead classification with psychological analysis
                </p>
                <div className="mt-2 bg-slate-800 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: '95%' }}></div>
                </div>
              </div>

              <div className="p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-white">Stall Breaking</h4>
                  <Badge className="bg-purple-900 text-purple-200">73% Success</Badge>
                </div>
                <p className="text-sm text-slate-300">
                  Breakthrough objections and identify true motivation
                </p>
                <div className="mt-2 bg-slate-800 rounded-full h-2">
                  <div className="bg-purple-500 h-2 rounded-full" style={{ width: '73%' }}></div>
                </div>
              </div>

              <div className="p-3 bg-yellow-900/20 border border-yellow-800/50 rounded-lg">
                <div className="flex items-start gap-2">
                  <Zap className="h-5 w-5 text-yellow-400 mt-0.5" />
                  <div>
                    <h5 className="font-medium text-yellow-200">Jorge Advantage</h5>
                    <p className="text-sm text-yellow-100">
                      Only agent in the market with confrontational AI qualification.
                      480% better than industry standard.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Insights */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Bot Performance Insights & Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 bg-green-900/20 border border-green-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-5 w-5 text-green-400" />
                <h4 className="font-medium text-green-200">Jorge Seller Excellence</h4>
              </div>
              <p className="text-sm text-green-100">
                Leading all metrics with 87% qualification accuracy.
                Confrontational methodology proving superior to traditional approaches.
              </p>
            </div>

            <div className="p-4 bg-blue-900/20 border border-blue-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-5 w-5 text-blue-400" />
                <h4 className="font-medium text-blue-200">Lead Bot Optimization</h4>
              </div>
              <p className="text-sm text-blue-100">
                3-7-30 sequence performing excellently. Consider expanding
                voice integration to all touchpoints for maximum impact.
              </p>
            </div>

            <div className="p-4 bg-purple-900/20 border border-purple-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="h-5 w-5 text-purple-400" />
                <h4 className="font-medium text-purple-200">Intent Decoder Speed</h4>
              </div>
              <p className="text-sm text-purple-100">
                42.3ms response time maintains competitive advantage.
                95% accuracy enables real-time decision making.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}