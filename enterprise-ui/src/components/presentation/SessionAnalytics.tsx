// Session Analytics Component
// Real-time analytics and insights for presentation sessions

'use client'

import { useState, useEffect } from 'react'
import {
  TrendingUp,
  TrendingDown,
  Users,
  Eye,
  MousePointer2,
  MessageSquare,
  Clock,
  Target,
  Award,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  Activity,
  Zap,
  Brain
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

interface SessionAnalyticsProps {
  sessionId: string
  engagementData: Array<{
    timestamp: number
    attention: number
    interaction: number
    sentiment: number
  }>
  currentMetrics: {
    attentionScore: number
    interactionLevel: number
    sentimentScore: number
    questionsAsked: number
    objectionsRaised: number
    commitmentSignals: number
  }
  behaviorProfile?: {
    engagementLevel: 'low' | 'medium' | 'high'
    attentionSpan: number
    interactionPreference: 'visual' | 'auditory' | 'kinesthetic'
    questioningPattern: 'early' | 'throughout' | 'end' | 'none'
    decisionMakingStyle: 'analytical' | 'emotional' | 'social' | 'driver'
  }
  predictiveInsights?: Array<{
    type: string
    confidence: number
    recommendation: string
    urgency: 'low' | 'medium' | 'high'
  }>
  className?: string
}

export function SessionAnalytics({
  sessionId,
  engagementData,
  currentMetrics,
  behaviorProfile,
  predictiveInsights = [],
  className
}: SessionAnalyticsProps) {
  const [timeWindow, setTimeWindow] = useState<'live' | '5min' | '15min' | 'session'>('live')
  const [realTimeData, setRealTimeData] = useState(engagementData)

  // Simulate real-time data updates
  useEffect(() => {
    const interval = setInterval(() => {
      const now = Date.now()
      const newDataPoint = {
        timestamp: now,
        attention: Math.max(0, Math.min(100, currentMetrics.attentionScore + (Math.random() * 10 - 5))),
        interaction: Math.max(0, Math.min(100, currentMetrics.interactionLevel + (Math.random() * 8 - 4))),
        sentiment: Math.max(-100, Math.min(100, currentMetrics.sentimentScore + (Math.random() * 6 - 3)))
      }

      setRealTimeData(prev => {
        const updated = [...prev, newDataPoint]
        // Keep last 50 data points for performance
        return updated.slice(-50)
      })
    }, 2000)

    return () => clearInterval(interval)
  }, [currentMetrics])

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getScoreBackground = (score: number) => {
    if (score >= 80) return 'bg-green-500/10'
    if (score >= 60) return 'bg-yellow-500/10'
    return 'bg-red-500/10'
  }

  const getTrendIcon = (current: number, previous: number) => {
    const diff = current - previous
    if (Math.abs(diff) < 2) return null
    return diff > 0 ? (
      <TrendingUp className="w-4 h-4 text-green-400" />
    ) : (
      <TrendingDown className="w-4 h-4 text-red-400" />
    )
  }

  const getEngagementLevel = (score: number) => {
    if (score >= 80) return { level: 'Excellent', color: 'text-green-400' }
    if (score >= 60) return { level: 'Good', color: 'text-yellow-400' }
    if (score >= 40) return { level: 'Fair', color: 'text-orange-400' }
    return { level: 'Poor', color: 'text-red-400' }
  }

  const formatChartData = () => {
    return realTimeData.map((point, index) => ({
      time: new Date(point.timestamp).toLocaleTimeString('en-US', {
        hour12: false,
        minute: '2-digit',
        second: '2-digit'
      }),
      attention: point.attention,
      interaction: point.interaction,
      sentiment: (point.sentiment + 100) / 2 // Convert -100,100 to 0,100 for chart
    }))
  }

  const getInsightIcon = (type: string) => {
    switch (type) {
      case 'conversion_likelihood': return <Target className="w-4 h-4" />
      case 'attention_drop': return <AlertTriangle className="w-4 h-4" />
      case 'confusion_detected': return <Eye className="w-4 h-4" />
      case 'interest_peak': return <TrendingUp className="w-4 h-4" />
      default: return <Brain className="w-4 h-4" />
    }
  }

  const getInsightColor = (urgency: string) => {
    switch (urgency) {
      case 'high': return 'border-red-500 bg-red-500/10 text-red-300'
      case 'medium': return 'border-yellow-500 bg-yellow-500/10 text-yellow-300'
      case 'low': return 'border-green-500 bg-green-500/10 text-green-300'
      default: return 'border-gray-500 bg-gray-500/10 text-gray-300'
    }
  }

  const chartData = formatChartData()

  return (
    <div className={cn('space-y-6', className)}>
      {/* Real-time Metrics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-blue-400" />
                <span className="text-sm text-gray-300">Attention</span>
              </div>
              {getTrendIcon(currentMetrics.attentionScore, 75)}
            </div>
            <div className={cn('text-2xl font-bold mb-1', getScoreColor(currentMetrics.attentionScore))}>
              {Math.round(currentMetrics.attentionScore)}%
            </div>
            <div className="text-xs text-gray-400">
              {getEngagementLevel(currentMetrics.attentionScore).level}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <MousePointer2 className="w-4 h-4 text-purple-400" />
                <span className="text-sm text-gray-300">Interaction</span>
              </div>
              {getTrendIcon(currentMetrics.interactionLevel, 65)}
            </div>
            <div className={cn('text-2xl font-bold mb-1', getScoreColor(currentMetrics.interactionLevel))}>
              {Math.round(currentMetrics.interactionLevel)}%
            </div>
            <div className="text-xs text-gray-400">
              {getEngagementLevel(currentMetrics.interactionLevel).level}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-green-400" />
                <span className="text-sm text-gray-300">Sentiment</span>
              </div>
              {getTrendIcon(currentMetrics.sentimentScore, 0)}
            </div>
            <div className={cn('text-2xl font-bold mb-1', getScoreColor((currentMetrics.sentimentScore + 100) / 2))}>
              {currentMetrics.sentimentScore > 0 ? '+' : ''}{Math.round(currentMetrics.sentimentScore)}
            </div>
            <div className="text-xs text-gray-400">
              {currentMetrics.sentimentScore > 20 ? 'Positive' :
               currentMetrics.sentimentScore > -20 ? 'Neutral' : 'Negative'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Engagement Chart */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Live Engagement Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis
                  dataKey="time"
                  stroke="#9CA3AF"
                  fontSize={12}
                />
                <YAxis
                  stroke="#9CA3AF"
                  fontSize={12}
                  domain={[0, 100]}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    borderRadius: '8px'
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="attention"
                  stackId="1"
                  stroke="#3B82F6"
                  fill="#3B82F6"
                  fillOpacity={0.2}
                  name="Attention"
                />
                <Area
                  type="monotone"
                  dataKey="interaction"
                  stackId="2"
                  stroke="#8B5CF6"
                  fill="#8B5CF6"
                  fillOpacity={0.2}
                  name="Interaction"
                />
                <Area
                  type="monotone"
                  dataKey="sentiment"
                  stackId="3"
                  stroke="#10B981"
                  fill="#10B981"
                  fillOpacity={0.2}
                  name="Sentiment"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Interaction Summary */}
        <Card className="bg-white/5 border-white/10">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <MessageSquare className="w-5 h-5" />
              Client Interactions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-3 bg-white/5 rounded-lg">
                <div className="text-2xl font-bold text-blue-400 mb-1">
                  {currentMetrics.questionsAsked}
                </div>
                <div className="text-xs text-gray-400">Questions Asked</div>
              </div>
              <div className="text-center p-3 bg-white/5 rounded-lg">
                <div className="text-2xl font-bold text-red-400 mb-1">
                  {currentMetrics.objectionsRaised}
                </div>
                <div className="text-xs text-gray-400">Objections</div>
              </div>
              <div className="text-center p-3 bg-white/5 rounded-lg">
                <div className="text-2xl font-bold text-green-400 mb-1">
                  {currentMetrics.commitmentSignals}
                </div>
                <div className="text-xs text-gray-400">Commitment</div>
              </div>
            </div>

            {/* Interaction Quality */}
            <div className="space-y-3">
              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-300">Question Quality</span>
                  <span className="text-green-400">High</span>
                </div>
                <Progress value={85} className="h-2" />
              </div>

              <div>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-300">Engagement Depth</span>
                  <span className="text-blue-400">Medium</span>
                </div>
                <Progress value={70} className="h-2" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Behavior Profile */}
        {behaviorProfile && (
          <Card className="bg-white/5 border-white/10">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Users className="w-5 h-5" />
                Client Profile
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-400">Engagement Level</span>
                  <div className={cn('font-semibold capitalize',
                    behaviorProfile.engagementLevel === 'high' ? 'text-green-400' :
                    behaviorProfile.engagementLevel === 'medium' ? 'text-yellow-400' : 'text-red-400'
                  )}>
                    {behaviorProfile.engagementLevel}
                  </div>
                </div>

                <div>
                  <span className="text-gray-400">Attention Span</span>
                  <div className="text-white font-semibold">
                    {Math.round(behaviorProfile.attentionSpan)}s
                  </div>
                </div>

                <div>
                  <span className="text-gray-400">Learning Style</span>
                  <div className="text-white font-semibold capitalize">
                    {behaviorProfile.interactionPreference}
                  </div>
                </div>

                <div>
                  <span className="text-gray-400">Decision Style</span>
                  <div className="text-white font-semibold capitalize">
                    {behaviorProfile.decisionMakingStyle}
                  </div>
                </div>
              </div>

              <div>
                <span className="text-gray-400 text-sm">Questioning Pattern</span>
                <div className="text-white font-semibold capitalize">
                  {behaviorProfile.questioningPattern === 'none' ? 'No questions yet' : behaviorProfile.questioningPattern}
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* AI Insights */}
      {predictiveInsights.length > 0 && (
        <Card className="bg-white/5 border-white/10">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Zap className="w-5 h-5 text-yellow-400" />
              AI Insights & Recommendations
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {predictiveInsights.map((insight, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className={cn(
                    'p-4 rounded-lg border text-sm',
                    getInsightColor(insight.urgency)
                  )}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-0.5">
                      {getInsightIcon(insight.type)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-semibold capitalize">
                          {insight.type.replace(/_/g, ' ')}
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {Math.round(insight.confidence * 100)}% confidence
                        </Badge>
                      </div>
                      <p className="opacity-90">{insight.recommendation}</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Session Summary Stats */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Award className="w-5 h-5" />
            Session Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400 mb-1">
                {Math.round((currentMetrics.attentionScore + currentMetrics.interactionLevel) / 2)}%
              </div>
              <div className="text-sm text-gray-400">Overall Score</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400 mb-1">
                {currentMetrics.questionsAsked + currentMetrics.commitmentSignals > 3 ? 'High' : 'Medium'}
              </div>
              <div className="text-sm text-gray-400">Conversion Potential</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-green-400 mb-1">
                {currentMetrics.objectionsRaised === 0 ? 'Excellent' : currentMetrics.objectionsRaised < 3 ? 'Good' : 'Challenging'}
              </div>
              <div className="text-sm text-gray-400">Client Receptiveness</div>
            </div>

            <div className="text-center">
              <div className="text-2xl font-bold text-amber-400 mb-1">
                A{currentMetrics.attentionScore > 80 ? '+' : currentMetrics.attentionScore > 60 ? '' : '-'}
              </div>
              <div className="text-sm text-gray-400">Presentation Grade</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default SessionAnalytics