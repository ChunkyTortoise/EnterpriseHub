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
  ComposedChart,
  Area,
  AreaChart,
  Cell,
  PieChart,
  Pie
} from 'recharts'
import {
  DollarSign,
  TrendingUp,
  Calendar,
  Target,
  Award,
  Zap,
  ArrowUp,
  ArrowDown,
  Minus
} from 'lucide-react'
import { useAnalytics } from '@/hooks/useAnalytics'

export function RevenueAnalysis() {
  const { metrics, revenueWaterfallData, formatMetric, isLoading } = useAnalytics()

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

  const revenue = metrics.revenueMetrics

  // Revenue waterfall data (already available from useAnalytics)
  const waterfallData = revenueWaterfallData

  // Monthly revenue projection
  const monthlyProjection = [
    { month: 'Jan', beforeAI: 360000, afterAI: 985000, growth: 173.6 },
    { month: 'Feb', beforeAI: 360000, afterAI: 1045000, growth: 190.3 },
    { month: 'Mar', beforeAI: 360000, afterAI: 1125000, growth: 212.5 },
    { month: 'Apr', beforeAI: 360000, afterAI: 1180000, growth: 227.8 },
    { month: 'May', beforeAI: 360000, afterAI: 1245000, growth: 245.8 },
    { month: 'Jun', beforeAI: 360000, afterAI: 1320000, growth: 266.7 }
  ]

  // ROI breakdown
  const roiBreakdown = [
    { category: 'Transaction Volume', value: 96, description: '+96% more deals closed' },
    { category: 'Commission Rate', value: 36, description: '+36% average commission' },
    { category: 'Operational Efficiency', value: 67, description: '67% cost reduction' },
    { category: 'Lead Quality', value: 255, description: '255% better conversion' }
  ]

  // Commission analysis by bot
  const commissionByBot = [
    { bot: 'Jorge Seller', commissions: 145000, deals: 18, avg: 8055 },
    { bot: 'Lead Bot', commissions: 89000, deals: 12, avg: 7416 },
    { bot: 'Direct Sales', commissions: 67000, deals: 8, avg: 8375 },
    { bot: 'Referrals', commissions: 134000, deals: 9, avg: 14888 }
  ]

  // Key revenue metrics
  const revenueMetrics = [
    {
      title: 'Annual Revenue',
      value: formatMetric(revenue.totalRevenue, 'currency'),
      change: '+155%',
      changeType: 'positive',
      description: 'vs pre-AI baseline',
      icon: DollarSign
    },
    {
      title: 'Monthly ROI',
      value: formatMetric(revenue.monthlyROI, 'percentage'),
      change: '8.3x',
      changeType: 'positive',
      description: 'return on investment',
      icon: TrendingUp
    },
    {
      title: 'Avg Commission',
      value: formatMetric(revenue.averageCommission, 'currency'),
      change: '+36%',
      changeType: 'positive',
      description: 'per transaction',
      icon: Award
    },
    {
      title: 'Payback Period',
      value: `${revenue.paybackPeriod.toFixed(1)} mo`,
      change: 'Excellent',
      changeType: 'positive',
      description: 'AI investment recovery',
      icon: Calendar
    }
  ]

  // Market share projection
  const marketShareData = [
    { quarter: 'Q1', share: 18.5, revenue: 2.1 },
    { quarter: 'Q2', share: 21.3, revenue: 2.6 },
    { quarter: 'Q3', share: 24.8, revenue: 3.2 },
    { quarter: 'Q4', share: 28.1, revenue: 3.8 }
  ]

  return (
    <div className="space-y-6">
      {/* Revenue Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {revenueMetrics.map((metric) => (
          <Card key={metric.title} className="bg-gradient-to-r from-slate-800/50 to-green-900/20 border-slate-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-400">{metric.title}</p>
                  <p className="text-2xl font-bold text-white">{metric.value}</p>
                  <p className="text-sm text-green-400">{metric.change}</p>
                  <p className="text-xs text-slate-500">{metric.description}</p>
                </div>
                <div className="p-3 rounded-full bg-green-600/20">
                  <metric.icon className="h-6 w-6 text-green-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Revenue Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Waterfall */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <DollarSign className="h-5 w-5" />
              Revenue Impact Waterfall
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={waterfallData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="category" stroke="#9CA3AF" fontSize={12} />
                <YAxis stroke="#9CA3AF" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F3F4F6'
                  }}
                  formatter={(value, name) => [
                    formatMetric(Number(value), 'currency'),
                    'Revenue Impact'
                  ]}
                />
                <Bar dataKey="value">
                  {waterfallData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        entry.type === 'positive' ? '#10B981' :
                        entry.type === 'negative' ? '#EF4444' :
                        '#3B82F6'
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Monthly Revenue Growth */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Revenue Growth Trajectory
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <ComposedChart data={monthlyProjection}>
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
                    formatMetric(Number(value), name === 'growth' ? 'percentage' : 'currency'),
                    name === 'beforeAI' ? 'Before Jorge AI' :
                    name === 'afterAI' ? 'With Jorge AI' : 'Growth %'
                  ]}
                />
                <Area
                  type="monotone"
                  dataKey="beforeAI"
                  fill="#64748B"
                  fillOpacity={0.3}
                  stroke="#64748B"
                />
                <Area
                  type="monotone"
                  dataKey="afterAI"
                  fill="#10B981"
                  fillOpacity={0.4}
                  stroke="#10B981"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="growth"
                  stroke="#F59E0B"
                  strokeWidth={3}
                  dot={{ fill: '#F59E0B', strokeWidth: 2, r: 4 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* ROI Breakdown and Commission Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ROI Impact Breakdown */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Target className="h-5 w-5" />
              ROI Impact Breakdown
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {roiBreakdown.map((item, index) => (
                <div key={index} className="p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-medium text-white">{item.category}</h4>
                    <Badge className="bg-green-900 text-green-200">
                      +{item.value}%
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-300">{item.description}</p>
                  <div className="mt-3 bg-slate-800 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full transition-all duration-500"
                      style={{ width: `${Math.min(item.value, 100)}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Commission by Source */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Award className="h-5 w-5" />
              Commission Analysis by Source
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={commissionByBot} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#9CA3AF" fontSize={12} />
                <YAxis dataKey="bot" type="category" stroke="#9CA3AF" fontSize={12} width={80} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F3F4F6'
                  }}
                  formatter={(value, name) => [
                    formatMetric(Number(value), 'currency'),
                    'Total Commissions'
                  ]}
                />
                <Bar dataKey="commissions" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>

            <div className="mt-4 grid grid-cols-2 gap-4">
              {commissionByBot.map((source, index) => (
                <div key={index} className="text-center p-3 bg-slate-700/20 rounded">
                  <p className="text-sm text-slate-400">{source.bot}</p>
                  <p className="font-semibold text-white">{source.deals} deals</p>
                  <p className="text-xs text-slate-500">
                    Avg: {formatMetric(source.avg, 'currency')}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Market Share Growth */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Award className="h-5 w-5" />
            Market Share & Revenue Growth Projection
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={marketShareData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="quarter" stroke="#9CA3AF" fontSize={12} />
                <YAxis stroke="#9CA3AF" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1F2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                    color: '#F3F4F6'
                  }}
                  formatter={(value, name) => [
                    name === 'share' ? `${value}%` : `$${value}M`,
                    name === 'share' ? 'Market Share' : 'Revenue'
                  ]}
                />
                <Area
                  type="monotone"
                  dataKey="share"
                  fill="#8B5CF6"
                  fillOpacity={0.3}
                  stroke="#8B5CF6"
                  strokeWidth={2}
                />
                <Bar dataKey="revenue" fill="#10B981" />
              </ComposedChart>
            </ResponsiveContainer>

            <div className="space-y-4">
              <div className="p-4 bg-green-900/20 border border-green-800/50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <ArrowUp className="h-5 w-5 text-green-400" />
                  <h4 className="font-medium text-green-200">Revenue Growth</h4>
                </div>
                <p className="text-2xl font-bold text-white">$3.8M</p>
                <p className="text-sm text-green-100">Projected Q4 revenue (+155% YoY)</p>
              </div>

              <div className="p-4 bg-blue-900/20 border border-blue-800/50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="h-5 w-5 text-blue-400" />
                  <h4 className="font-medium text-blue-200">Market Share</h4>
                </div>
                <p className="text-2xl font-bold text-white">28.1%</p>
                <p className="text-sm text-blue-100">Projected Q4 market share (+52% growth)</p>
              </div>

              <div className="p-4 bg-yellow-900/20 border border-yellow-800/50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="h-5 w-5 text-yellow-400" />
                  <h4 className="font-medium text-yellow-200">Jorge Advantage</h4>
                </div>
                <p className="text-sm text-yellow-100">
                  AI-powered growth trajectory outpacing traditional competitors by 340%.
                  Technology advantage creating sustainable competitive moat.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Financial Insights */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Financial Performance Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-green-900/20 border border-green-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="h-5 w-5 text-green-400" />
                <h4 className="font-medium text-green-200">Revenue Excellence</h4>
              </div>
              <p className="text-sm text-green-100">
                Jorge AI has delivered a 155% increase in annual revenue through
                improved transaction volume and higher average commissions.
              </p>
            </div>

            <div className="p-4 bg-blue-900/20 border border-blue-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Award className="h-5 w-5 text-blue-400" />
                <h4 className="font-medium text-blue-200">ROI Leadership</h4>
              </div>
              <p className="text-sm text-blue-100">
                8.3x ROI on AI investment with 2.1-month payback period.
                Industry-leading return demonstrating exceptional value.
              </p>
            </div>

            <div className="p-4 bg-purple-900/20 border border-purple-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-5 w-5 text-purple-400" />
                <h4 className="font-medium text-purple-200">Growth Trajectory</h4>
              </div>
              <p className="text-sm text-purple-100">
                Sustainable growth model with expanding market share and
                increasing competitive advantage through AI differentiation.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}