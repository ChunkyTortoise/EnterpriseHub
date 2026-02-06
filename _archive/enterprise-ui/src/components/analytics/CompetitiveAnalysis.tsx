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
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ComposedChart,
  Area,
  ScatterChart,
  Scatter
} from 'recharts'
import {
  Award,
  TrendingUp,
  Target,
  Shield,
  Zap,
  Crown,
  Star,
  Trophy,
  Flame,
  ArrowUp,
  CheckCircle,
  AlertTriangle
} from 'lucide-react'
import { useAnalytics } from '@/hooks/useAnalytics'

export function CompetitiveAnalysis() {
  const { metrics, benchmarkComparisons, formatMetric, isLoading } = useAnalytics()

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

  const competitive = metrics.competitiveAnalysis

  // Competitive radar chart data
  const radarData = [
    {
      metric: 'Technology',
      Jorge: 95,
      'Premium Traditional': 25,
      'Discount Broker': 15,
      'Tech-Forward': 65
    },
    {
      metric: 'Response Time',
      Jorge: 98,
      'Premium Traditional': 20,
      'Discount Broker': 10,
      'Tech-Forward': 35
    },
    {
      metric: 'Conversion Rate',
      Jorge: 90,
      'Premium Traditional': 45,
      'Discount Broker': 25,
      'Tech-Forward': 35
    },
    {
      metric: 'Client Satisfaction',
      Jorge: 96,
      'Premium Traditional': 70,
      'Discount Broker': 40,
      'Tech-Forward': 55
    },
    {
      metric: 'Market Intelligence',
      Jorge: 93,
      'Premium Traditional': 60,
      'Discount Broker': 20,
      'Tech-Forward': 45
    },
    {
      metric: 'Lead Quality',
      Jorge: 87,
      'Premium Traditional': 40,
      'Discount Broker': 15,
      'Tech-Forward': 30
    }
  ]

  // Benchmark comparison chart data
  const benchmarkData = benchmarkComparisons.map(comp => ({
    metric: comp.metric,
    jorge: comp.jorgeValue,
    industry: comp.industryAverage,
    topQuartile: comp.topQuartile,
    improvement: comp.improvement * 100
  }))

  // Market share evolution
  const marketShareData = [
    { quarter: 'Q1 2023', jorge: 8.5, traditional: 45, discount: 35, tech: 11.5 },
    { quarter: 'Q2 2023', jorge: 12.3, traditional: 42, discount: 33, tech: 12.7 },
    { quarter: 'Q3 2023', jorge: 16.8, traditional: 39, discount: 31, tech: 13.2 },
    { quarter: 'Q4 2023', jorge: 21.2, traditional: 36, discount: 29, tech: 13.8 },
    { quarter: 'Q1 2024', jorge: 26.1, traditional: 33, discount: 27, tech: 13.9 }
  ]

  // Competitive positioning scatter plot
  const competitorPositioning = [
    { name: 'Jorge AI', technology: 95, marketShare: 26.1, efficiency: 93, color: '#10B981' },
    { name: 'Premium Traditional', technology: 25, marketShare: 33, efficiency: 45, color: '#3B82F6' },
    { name: 'Discount Broker', technology: 15, marketShare: 27, efficiency: 35, color: '#EF4444' },
    { name: 'Tech-Forward', technology: 65, marketShare: 13.9, efficiency: 55, color: '#F59E0B' }
  ]

  // Jorge advantages breakdown
  const jorgeAdvantages = [
    {
      category: 'AI Technology Leadership',
      advantage: 'Only agent with enterprise-grade AI ecosystem',
      metrics: [
        { metric: 'Response Time', value: '2 minutes', comparison: 'vs 24 hours industry' },
        { metric: 'AI Accuracy', value: '95%', comparison: 'vs 23% traditional' },
        { metric: 'Automation Level', value: '78%', comparison: 'vs 12% competition' }
      ],
      color: 'bg-purple-900/20 border-purple-800/50',
      icon: Zap
    },
    {
      category: 'Market Intelligence',
      advantage: 'Real-time competitive analysis and market insights',
      metrics: [
        { metric: 'CMA Accuracy', value: '93%', comparison: 'vs manual analysis' },
        { metric: 'Market Predictions', value: '78%', comparison: 'accuracy rate' },
        { metric: 'Pricing Optimization', value: '+15%', comparison: 'value increase' }
      ],
      color: 'bg-blue-900/20 border-blue-800/50',
      icon: Target
    },
    {
      category: 'Client Experience',
      advantage: 'Superior service quality through AI augmentation',
      metrics: [
        { metric: 'Satisfaction Score', value: '4.8/5', comparison: 'vs 3.2/5 industry' },
        { metric: 'NPS Score', value: '78', comparison: 'vs 34 industry' },
        { metric: 'Retention Rate', value: '94%', comparison: 'vs 67% industry' }
      ],
      color: 'bg-green-900/20 border-green-800/50',
      icon: Star
    }
  ]

  // Key competitive metrics
  const competitiveMetrics = [
    {
      title: 'Market Ranking',
      value: `#${competitive.marketRanking}`,
      change: 'Top 3 Position',
      changeType: 'positive',
      description: 'in local market',
      icon: Crown
    },
    {
      title: 'Market Share',
      value: formatMetric(competitive.marketShare, 'percentage'),
      change: '+52% growth',
      changeType: 'positive',
      description: 'and expanding rapidly',
      icon: TrendingUp
    },
    {
      title: 'Technology Lead',
      value: '89%',
      change: 'Ahead',
      changeType: 'positive',
      description: 'vs closest competitor',
      icon: Shield
    },
    {
      title: 'Conversion Advantage',
      value: '+67%',
      change: 'Higher',
      changeType: 'positive',
      description: 'than competition',
      icon: Trophy
    }
  ]

  return (
    <div className="space-y-6">
      {/* Competitive Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {competitiveMetrics.map((metric) => (
          <Card key={metric.title} className="bg-gradient-to-r from-slate-800/50 to-orange-900/20 border-slate-700">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-400">{metric.title}</p>
                  <p className="text-2xl font-bold text-white">{metric.value}</p>
                  <p className="text-sm text-orange-400">{metric.change}</p>
                  <p className="text-xs text-slate-500">{metric.description}</p>
                </div>
                <div className="p-3 rounded-full bg-orange-600/20">
                  <metric.icon className="h-6 w-6 text-orange-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Competitive Radar and Market Share */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Multi-dimensional Competitive Radar */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Competitive Performance Radar
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
                  name="Jorge AI"
                  dataKey="Jorge"
                  stroke="#10B981"
                  fill="#10B981"
                  fillOpacity={0.3}
                  strokeWidth={3}
                />
                <Radar
                  name="Premium Traditional"
                  dataKey="Premium Traditional"
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  fillOpacity={0.1}
                  strokeWidth={2}
                />
                <Radar
                  name="Discount Broker"
                  dataKey="Discount Broker"
                  stroke="#EF4444"
                  fill="#EF4444"
                  fillOpacity={0.1}
                  strokeWidth={2}
                />
                <Radar
                  name="Tech-Forward"
                  dataKey="Tech-Forward"
                  stroke="#F59E0B"
                  fill="#F59E0B"
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

            <div className="mt-4 p-3 bg-green-900/20 border border-green-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <Crown className="h-4 w-4 text-green-400" />
                <span className="text-sm font-medium text-green-200">Market Leadership</span>
              </div>
              <p className="text-sm text-green-100">
                Jorge AI leads in all critical performance dimensions with significant competitive gaps.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Market Share Evolution */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Market Share Evolution
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={marketShareData}>
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
                  formatter={(value, name) => [`${value}%`,
                    name === 'jorge' ? 'Jorge AI' :
                    name === 'traditional' ? 'Traditional Agents' :
                    name === 'discount' ? 'Discount Brokers' :
                    'Tech-Forward Agents'
                  ]}
                />
                <Area
                  type="monotone"
                  dataKey="jorge"
                  stackId="1"
                  stroke="#10B981"
                  fill="#10B981"
                  fillOpacity={0.8}
                />
                <Area
                  type="monotone"
                  dataKey="traditional"
                  stackId="1"
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  fillOpacity={0.6}
                />
                <Area
                  type="monotone"
                  dataKey="discount"
                  stackId="1"
                  stroke="#EF4444"
                  fill="#EF4444"
                  fillOpacity={0.6}
                />
                <Area
                  type="monotone"
                  dataKey="tech"
                  stackId="1"
                  stroke="#F59E0B"
                  fill="#F59E0B"
                  fillOpacity={0.6}
                />
              </AreaChart>
            </ResponsiveContainer>

            <div className="mt-4 flex justify-between items-center">
              <div className="text-center">
                <p className="text-sm text-slate-400">Jorge Growth</p>
                <p className="font-semibold text-green-400">+207% in 1 year</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-slate-400">Market Position</p>
                <p className="font-semibold text-orange-400">#2 and rising</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Benchmark Comparisons */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Award className="h-5 w-5" />
            Industry Benchmark Leadership
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={benchmarkData} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis type="number" stroke="#9CA3AF" fontSize={12} />
              <YAxis dataKey="metric" type="category" stroke="#9CA3AF" fontSize={12} width={120} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }}
                formatter={(value, name) => [
                  name === 'jorge' ? (typeof value === 'number' && value > 100 ? formatMetric(value, 'currency') : value) :
                  name === 'industry' ? (typeof value === 'number' && value > 100 ? formatMetric(value, 'currency') : value) :
                  name === 'topQuartile' ? (typeof value === 'number' && value > 100 ? formatMetric(value, 'currency') : value) :
                  `${value}%`,
                  name === 'jorge' ? 'Jorge AI' :
                  name === 'industry' ? 'Industry Average' :
                  name === 'topQuartile' ? 'Top Quartile' : 'Improvement'
                ]}
              />
              <Bar dataKey="industry" fill="#64748B" name="Industry Average" />
              <Bar dataKey="topQuartile" fill="#3B82F6" name="Top Quartile" />
              <Bar dataKey="jorge" fill="#10B981" name="Jorge AI" />
            </BarChart>
          </ResponsiveContainer>

          <div className="mt-4 grid grid-cols-2 lg:grid-cols-6 gap-4">
            {benchmarkComparisons.map((comp, index) => (
              <div key={index} className="text-center p-3 bg-slate-700/30 rounded">
                <div className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                  comp.ranking === 'leader' ? 'bg-green-900 text-green-200' :
                  comp.ranking === 'above-average' ? 'bg-blue-900 text-blue-200' :
                  'bg-yellow-900 text-yellow-200'
                }`}>
                  {comp.ranking === 'leader' && <Crown className="h-3 w-3" />}
                  {comp.ranking}
                </div>
                <p className="text-xs text-slate-400 mt-1">{comp.metric}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Jorge Competitive Advantages */}
      <div className="space-y-6">
        <h3 className="text-xl font-semibold text-white flex items-center gap-2">
          <Flame className="h-6 w-6 text-orange-400" />
          Jorge AI Competitive Advantages
        </h3>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {jorgeAdvantages.map((advantage, index) => (
            <Card key={index} className={`${advantage.color} bg-slate-800/50 border-slate-700`}>
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <advantage.icon className="h-5 w-5" />
                  {advantage.category}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-200 mb-4">{advantage.advantage}</p>

                <div className="space-y-3">
                  {advantage.metrics.map((metric, mIndex) => (
                    <div key={mIndex} className="flex justify-between items-center">
                      <span className="text-sm text-slate-300">{metric.metric}</span>
                      <div className="text-right">
                        <p className="font-semibold text-white">{metric.value}</p>
                        <p className="text-xs text-slate-400">{metric.comparison}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Competitive Positioning Map */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Target className="h-5 w-5" />
            Competitive Positioning Map
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="technology"
                domain={[0, 100]}
                name="Technology Score"
                stroke="#9CA3AF"
                fontSize={12}
                label={{ value: 'Technology Leadership →', position: 'bottom', style: { textAnchor: 'middle' } }}
              />
              <YAxis
                dataKey="marketShare"
                domain={[0, 35]}
                name="Market Share"
                stroke="#9CA3AF"
                fontSize={12}
                label={{ value: '← Market Share (%)', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '8px',
                  color: '#F3F4F6'
                }}
                formatter={(value, name) => [
                  name === 'technology' ? `${value}%` :
                  name === 'marketShare' ? `${value}%` :
                  `${value}%`,
                  name === 'technology' ? 'Technology Score' :
                  name === 'marketShare' ? 'Market Share' :
                  'Efficiency'
                ]}
                labelFormatter={(label) => competitorPositioning.find(c => c.efficiency === label)?.name || ''}
              />
              <Scatter data={competitorPositioning} fill="#8884d8">
                {competitorPositioning.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>

          <div className="mt-4 grid grid-cols-2 lg:grid-cols-4 gap-4">
            {competitorPositioning.map((competitor, index) => (
              <div key={index} className="flex items-center gap-2 p-2 bg-slate-700/30 rounded">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: competitor.color }}></div>
                <span className="text-sm text-slate-200">{competitor.name}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Strategic Insights */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Trophy className="h-5 w-5" />
            Strategic Competitive Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="p-4 bg-green-900/20 border border-green-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-5 w-5 text-green-400" />
                <h4 className="font-medium text-green-200">Market Dominance Path</h4>
              </div>
              <p className="text-sm text-green-100">
                Jorge AI's technology leadership creates sustainable competitive moat.
                207% market share growth in 12 months demonstrates clear trajectory to market dominance.
              </p>
            </div>

            <div className="p-4 bg-blue-900/20 border border-blue-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Shield className="h-5 w-5 text-blue-400" />
                <h4 className="font-medium text-blue-200">Competitive Moat</h4>
              </div>
              <p className="text-sm text-blue-100">
                AI-powered capabilities create barriers to entry competitors cannot replicate.
                89% technology lead over closest competitor widens continuously.
              </p>
            </div>

            <div className="p-4 bg-orange-900/20 border border-orange-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle className="h-5 w-5 text-orange-400" />
                <h4 className="font-medium text-orange-200">Disruption Impact</h4>
              </div>
              <p className="text-sm text-orange-100">
                Traditional competitors declining as Jorge AI captures market share.
                Technology disruption accelerating industry transformation.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}