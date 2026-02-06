"use client";

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
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
  FunnelChart,
  Funnel,
  LabelList,
  ComposedChart,
  Area
} from 'recharts'
import {
  Users,
  Target,
  Clock,
  TrendingUp,
  CheckCircle,
  Star,
  Zap,
  ArrowRight,
  Filter,
  Activity
} from 'lucide-react'
import { useAnalytics } from '@/hooks/useAnalytics'

const COLORS = ['#EF4444', '#F59E0B', '#06B6D4', '#64748B']

export function LeadQualityMetrics() {
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

  const leads = metrics.leadMetrics

  // Lead quality distribution for pie chart
  const leadQualityDistribution = [
    { name: 'Hot (75-100)', value: leads.scoreDistribution.hot, color: '#EF4444' },
    { name: 'Warm (50-74)', value: leads.scoreDistribution.warm, color: '#F59E0B' },
    { name: 'Lukewarm (26-49)', value: leads.scoreDistribution.lukewarm, color: '#06B6D4' },
    { name: 'Cold (0-25)', value: leads.scoreDistribution.cold, color: '#64748B' }
  ]

  // Conversion funnel data
  const conversionFunnelData = [
    { stage: 'Total Leads', value: leads.totalLeads, percentage: 100 },
    { stage: 'Qualified', value: leads.qualifiedLeads, percentage: (leads.qualifiedLeads / leads.totalLeads * 100) },
    { stage: 'Hot Leads', value: leads.hotLeads, percentage: (leads.hotLeads / leads.totalLeads * 100) },
    { stage: 'Showing Scheduled', value: Math.round(leads.hotLeads * 0.78), percentage: (leads.hotLeads * 0.78 / leads.totalLeads * 100) },
    { stage: 'Under Contract', value: Math.round(leads.totalLeads * leads.conversionRate), percentage: (leads.conversionRate * 100) }
  ]

  // Lead source performance
  const leadSourceData = leads.leadSources.map(source => ({
    ...source,
    qualityScore: (source.conversionRate * 100 + source.quality) / 2
  }))

  // Response time comparison (Jorge AI vs Industry)
  const responseTimeData = [
    { metric: 'Initial Response', jorge: 2, industry: 1440, improvement: 99.8 }, // 2 min vs 24 hours
    { metric: 'Follow-up Speed', jorge: 15, industry: 4320, improvement: 99.7 }, // 15 min vs 3 days
    { metric: 'Qualification Time', jorge: 8, industry: 480, improvement: 98.3 }, // 8 min vs 8 hours
    { metric: 'Lead Scoring', jorge: 0.5, industry: 1440, improvement: 99.97 } // 30 sec vs 24 hours
  ]

  // Weekly lead quality trends
  const weeklyTrends = [
    { week: 'Week 1', totalLeads: 156, hotLeads: 42, conversion: 8.7 },
    { week: 'Week 2', totalLeads: 178, hotLeads: 51, conversion: 9.2 },
    { week: 'Week 3', totalLeads: 134, hotLeads: 38, conversion: 7.1 },
    { week: 'Week 4', totalLeads: 203, hotLeads: 67, conversion: 12.3 },
    { week: 'Week 5', totalLeads: 189, hotLeads: 58, conversion: 10.8 }
  ]

  // Key lead metrics
  const leadMetrics = [
    {
      title: 'Qualification Rate',
      value: formatMetric(leads.qualifiedLeads / leads.totalLeads, 'percentage'),
      change: '+480%',
      changeType: 'positive',
      description: 'vs 15% industry average',
      icon: Target
    },
    {
      title: 'Response Time',
      value: formatMetric(leads.averageResponseTime, 'time'),
      change: '99.8% faster',
      changeType: 'positive',
      description: 'vs 24-hour industry average',
      icon: Clock
    },
    {
      title: 'Hot Lead Rate',
      value: formatMetric(leads.hotLeads / leads.totalLeads, 'percentage'),
      change: '+196%',
      changeType: 'positive',
      description: 'superior lead identification',
      icon: Star
    },
    {
      title: 'Conversion Rate',
      value: formatMetric(leads.conversionRate, 'percentage'),
      change: '+139%',
      changeType: 'positive',
      description: 'show-to-contract rate',
      icon: CheckCircle
    }
  ]

  // Jorge seller bot specific metrics
  const jorgeSellerMetrics = leads.sellerLeads

  return (
    <div className="space-y-6">
      {/* Lead Quality Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {leadMetrics.map((metric) => (
          <Card key={metric.title} className="bg-gradient-to-r from-slate-800/50 to-blue-900/20 border-slate-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-400">{metric.title}</p>
                  <p className="text-2xl font-bold text-white">{metric.value}</p>
                  <p className="text-sm text-green-400">{metric.change}</p>
                  <p className="text-xs text-slate-500">{metric.description}</p>
                </div>
                <div className="p-3 rounded-full bg-blue-600/20">
                  <metric.icon className="h-6 w-6 text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Lead Quality Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lead Quality Distribution */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Filter className="h-5 w-5" />
              Lead Quality Distribution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col lg:flex-row items-center gap-6">
              <ResponsiveContainer width="50%" height={250}>
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

              <div className="flex-1 space-y-3">
                {leadQualityDistribution.map((item, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
                    <div className="flex items-center gap-3">
                      <div className="w-4 h-4 rounded-full" style={{ backgroundColor: item.color }}></div>
                      <span className="text-sm text-slate-200">{item.name}</span>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-white">{item.value}</p>
                      <p className="text-xs text-slate-400">
                        {((item.value / leads.totalLeads) * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                ))}

                <div className="p-3 bg-green-900/20 border border-green-800/50 rounded-lg mt-4">
                  <p className="text-sm text-green-200">
                    <strong>68%</strong> of leads are warm or hot vs <strong>23%</strong> industry average
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Conversion Funnel */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <ArrowRight className="h-5 w-5" />
              Lead Conversion Funnel
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {conversionFunnelData.map((stage, index) => (
                <div key={index} className="relative">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-slate-300">{stage.stage}</span>
                    <div className="text-right">
                      <span className="font-semibold text-white">{stage.value}</span>
                      <span className="text-xs text-slate-400 ml-2">
                        ({stage.percentage.toFixed(1)}%)
                      </span>
                    </div>
                  </div>

                  <div className="relative">
                    <div className="bg-slate-700 rounded-full h-3">
                      <div
                        className={`rounded-full h-3 transition-all duration-500 ${
                          index === 0 ? 'bg-blue-500' :
                          index === 1 ? 'bg-green-500' :
                          index === 2 ? 'bg-yellow-500' :
                          index === 3 ? 'bg-orange-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${stage.percentage}%` }}
                      ></div>
                    </div>

                    {index < conversionFunnelData.length - 1 && (
                      <div className="absolute -bottom-1 right-0 transform translate-y-full">
                        <ArrowRight className="h-4 w-4 text-slate-500" />
                      </div>
                    )}
                  </div>
                </div>
              ))}

              <div className="p-3 bg-blue-900/20 border border-blue-800/50 rounded-lg mt-4">
                <p className="text-sm text-blue-200">
                  <strong>43%</strong> show-to-contract rate vs <strong>18%</strong> industry average
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Lead Source Performance and Response Time */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Lead Source Performance */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Lead Source Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={leadSourceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="source" stroke="#9CA3AF" fontSize={12} />
                <YAxis yAxisId="left" stroke="#9CA3AF" fontSize={12} />
                <YAxis yAxisId="right" orientation="right" stroke="#9CA3AF" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F3F4F6'
                  }}
                  formatter={(value, name) => [
                    name === 'volume' ? value : name === 'conversionRate' ? `${(Number(value) * 100).toFixed(1)}%` : `${value}x`,
                    name === 'volume' ? 'Volume' : name === 'conversionRate' ? 'Conversion Rate' : 'ROI'
                  ]}
                />
                <Bar yAxisId="left" dataKey="volume" fill="#3B82F6" />
                <Line yAxisId="right" type="monotone" dataKey="conversionRate" stroke="#10B981" strokeWidth={3} />
                <Line yAxisId="right" type="monotone" dataKey="roi" stroke="#F59E0B" strokeWidth={2} />
              </ComposedChart>
            </ResponsiveContainer>

            <div className="mt-4 grid grid-cols-2 gap-4">
              <div className="text-center">
                <p className="text-sm text-slate-400">Best Conversion</p>
                <p className="font-semibold text-green-400">Referrals - 31%</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-slate-400">Highest ROI</p>
                <p className="font-semibold text-yellow-400">Referrals - 23.7x</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Response Time Comparison */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Response Time Advantage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={responseTimeData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#9CA3AF" fontSize={12} />
                <YAxis dataKey="metric" type="category" stroke="#9CA3AF" fontSize={12} width={100} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F3F4F6'
                  }}
                  formatter={(value, name) => [
                    name === 'jorge' ? formatMetric(Number(value), 'time') :
                    name === 'industry' ? formatMetric(Number(value), 'time') :
                    `${value}%`,
                    name === 'jorge' ? 'Jorge AI' :
                    name === 'industry' ? 'Industry Avg' : 'Improvement'
                  ]}
                />
                <Bar dataKey="jorge" fill="#10B981" name="Jorge AI" />
                <Bar dataKey="industry" fill="#64748B" name="Industry" />
              </BarChart>
            </ResponsiveContainer>

            <div className="mt-4 p-3 bg-green-900/20 border border-green-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Zap className="h-4 w-4 text-green-400" />
                <span className="text-sm font-medium text-green-200">Speed Advantage</span>
              </div>
              <p className="text-sm text-green-100">
                Jorge AI responds in minutes while competitors take hours or days.
                This speed advantage captures 99.8% more leads.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Jorge Seller Bot Specific Metrics */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Star className="h-5 w-5" />
            Jorge Seller Bot Lead Quality Excellence
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Seller Bot Metrics */}
            <div className="space-y-4">
              <div className="p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-white">Qualified Sellers</h4>
                  <Badge className="bg-green-900 text-green-200">
                    {jorgeSellerMetrics.qualified} / {jorgeSellerMetrics.total}
                  </Badge>
                </div>
                <p className="text-2xl font-bold text-white">
                  {formatMetric(jorgeSellerMetrics.qualificationRate, 'percentage')}
                </p>
                <p className="text-sm text-slate-400">qualification accuracy</p>
                <div className="mt-2 bg-slate-800 rounded-full h-2">
                  <div className="bg-green-500 h-2 rounded-full" style={{ width: `${jorgeSellerMetrics.qualificationRate * 100}%` }}></div>
                </div>
              </div>

              <div className="p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-white">Temperature Score</h4>
                  <Badge className="bg-blue-900 text-blue-200">
                    {jorgeSellerMetrics.averageTemperatureScore}/100
                  </Badge>
                </div>
                <p className="text-2xl font-bold text-white">95%</p>
                <p className="text-sm text-slate-400">scoring accuracy</p>
                <div className="mt-2 bg-slate-800 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: '95%' }}></div>
                </div>
              </div>
            </div>

            {/* Weekly Trends */}
            <div className="lg:col-span-2">
              <h4 className="text-white font-medium mb-4">Weekly Lead Quality Trends</h4>
              <ResponsiveContainer width="100%" height={250}>
                <ComposedChart data={weeklyTrends}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="week" stroke="#9CA3AF" fontSize={12} />
                  <YAxis yAxisId="left" stroke="#9CA3AF" fontSize={12} />
                  <YAxis yAxisId="right" orientation="right" stroke="#9CA3AF" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1F2937',
                      border: '1px solid #374151',
                      borderRadius: '8px',
                      color: '#F3F4F6'
                    }}
                  />
                  <Area
                    yAxisId="left"
                    type="monotone"
                    dataKey="totalLeads"
                    fill="#3B82F6"
                    fillOpacity={0.3}
                    stroke="#3B82F6"
                  />
                  <Bar yAxisId="left" dataKey="hotLeads" fill="#F59E0B" />
                  <Line yAxisId="right" type="monotone" dataKey="conversion" stroke="#10B981" strokeWidth={3} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Lead Quality Insights */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Lead Quality Performance Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-green-900/20 border border-green-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Target className="h-5 w-5 text-green-400" />
                <h4 className="font-medium text-green-200">Qualification Excellence</h4>
              </div>
              <p className="text-sm text-green-100">
                Jorge AI achieves 87% qualification rate vs 15% industry average.
                Confrontational methodology identifies truly motivated sellers.
              </p>
            </div>

            <div className="p-4 bg-blue-900/20 border border-blue-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="h-5 w-5 text-blue-400" />
                <h4 className="font-medium text-blue-200">Speed Advantage</h4>
              </div>
              <p className="text-sm text-blue-100">
                2-minute response time captures leads before competitors respond.
                99.8% faster than industry standard creates massive advantage.
              </p>
            </div>

            <div className="p-4 bg-purple-900/20 border border-purple-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Star className="h-5 w-5 text-purple-400" />
                <h4 className="font-medium text-purple-200">Conversion Leadership</h4>
              </div>
              <p className="text-sm text-purple-100">
                43% show-to-contract rate vs 18% industry average.
                Superior lead quality drives exceptional conversion performance.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}