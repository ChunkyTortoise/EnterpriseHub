// Claude Concierge Interface - Omnipresent AI Platform Guide
// Advanced interface for the platform's omnipresent AI concierge with 40+ agent awareness

'use client'

import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Brain, Sparkles, Eye, Zap, Users, Activity, MessageSquare,
  Settings, HelpCircle, TrendingUp, AlertTriangle, CheckCircle2,
  Bot, Clock, Target, Star, Shield, Globe, ArrowRight, ChevronDown,
  Search, Filter, MoreVertical, Send, Mic, MicOff, Volume2
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

// Concierge Types
interface PlatformActivity {
  id: string
  type: 'agent_coordination' | 'user_interaction' | 'system_alert' | 'performance_insight'
  title: string
  description: string
  agentId?: string
  agentName?: string
  userId?: string
  timestamp: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  status: 'active' | 'resolved' | 'monitoring'
  metadata?: any
}

interface ProactiveSuggestion {
  id: string
  type: 'optimization' | 'escalation' | 'automation' | 'insight'
  title: string
  description: string
  impact: 'low' | 'medium' | 'high'
  confidence: number
  actionable: boolean
  estimatedBenefit?: string
  relatedAgents: string[]
}

interface ConciergeInsight {
  category: string
  title: string
  value: string | number
  trend: 'up' | 'down' | 'stable'
  trendValue: number
  description: string
}

import { useConciergeInsights, useProactiveSuggestions, useConciergeChat } from '@/lib/api/ClaudeConciergeAPI'
import { usePlatformActivities } from '@/store/agentEcosystemStore'
import { useAgentEcosystemIntegration } from '@/hooks/useAgentEcosystemIntegration'

// Mock platform activities will be replaced by real data
const mockPlatformActivities: PlatformActivity[] = [
  {
    id: 'activity-001',
    type: 'agent_coordination',
    title: 'Multi-agent handoff initiated',
    description: 'Jorge Seller Bot → Property Intelligence Agent for premium analysis',
    agentId: 'jorge-seller',
    agentName: 'Jorge Seller Bot',
    timestamp: '2026-01-24T12:30:00Z',
    priority: 'medium',
    status: 'active'
  },
  {
    id: 'activity-002',
    type: 'user_interaction',
    title: 'Customer escalation detected',
    description: 'Sarah Johnson expressing frustration with property search results',
    userId: 'user-sarah',
    timestamp: '2026-01-24T12:28:00Z',
    priority: 'high',
    status: 'monitoring'
  },
  {
    id: 'activity-003',
    type: 'performance_insight',
    title: 'Response time optimization opportunity',
    description: 'Property Intelligence Agent averaging 28s response time (target: <20s)',
    agentId: 'property-intelligence',
    agentName: 'Property Intelligence Agent',
    timestamp: '2026-01-24T12:25:00Z',
    priority: 'low',
    status: 'monitoring'
  },
  {
    id: 'activity-004',
    type: 'system_alert',
    title: 'High coordination success rate',
    description: 'Customer Journey Orchestrator achieving 94% handoff efficiency',
    agentId: 'journey-orchestrator',
    agentName: 'Customer Journey Orchestrator',
    timestamp: '2026-01-24T12:20:00Z',
    priority: 'low',
    status: 'resolved'
  }
]

// Mock proactive suggestions
const mockSuggestions: ProactiveSuggestion[] = [
  {
    id: 'suggestion-001',
    type: 'optimization',
    title: 'Optimize Property Intelligence workflow',
    description: 'Implement parallel processing for investment scoring to reduce analysis time by 35%',
    impact: 'high',
    confidence: 87,
    actionable: true,
    estimatedBenefit: '35% faster analysis',
    relatedAgents: ['property-intelligence', 'enhanced-orchestrator']
  },
  {
    id: 'suggestion-002',
    type: 'escalation',
    title: 'Customer satisfaction intervention needed',
    description: 'Michael Chen showing signs of decision paralysis - suggest human broker consultation',
    impact: 'medium',
    confidence: 92,
    actionable: true,
    estimatedBenefit: 'Prevent churn',
    relatedAgents: ['journey-orchestrator', 'claude-concierge']
  },
  {
    id: 'suggestion-003',
    type: 'insight',
    title: 'Market trend opportunity',
    description: 'Rancho Cucamonga market showing 12% increase in investor interest - suggest proactive outreach',
    impact: 'medium',
    confidence: 78,
    actionable: true,
    estimatedBenefit: '15-20% lead increase',
    relatedAgents: ['market-intelligence', 'lead-generator']
  }
]

// Mock insights
const mockInsights: ConciergeInsight[] = [
  {
    category: 'Agent Performance',
    title: 'Average Response Time',
    value: '2.4s',
    trend: 'down',
    trendValue: -12,
    description: '12% improvement in last hour'
  },
  {
    category: 'User Experience',
    title: 'Customer Satisfaction',
    value: '94%',
    trend: 'up',
    trendValue: 3,
    description: '3% increase from yesterday'
  },
  {
    category: 'Coordination',
    title: 'Agent Handoffs',
    value: '47',
    trend: 'up',
    trendValue: 8,
    description: '8 successful handoffs in last hour'
  },
  {
    category: 'Intelligence',
    title: 'Pattern Recognition',
    value: '98.7%',
    trend: 'stable',
    trendValue: 0,
    description: 'Consistent accuracy maintained'
  }
]

function ActivityTypeIcon({ type }: { type: PlatformActivity['type'] }) {
  const icons = {
    agent_coordination: <Bot className="w-4 h-4 text-blue-500" />,
    user_interaction: <Users className="w-4 h-4 text-purple-500" />,
    system_alert: <AlertTriangle className="w-4 h-4 text-yellow-500" />,
    performance_insight: <TrendingUp className="w-4 h-4 text-green-500" />
  }
  return icons[type]
}

function PriorityIndicator({ priority }: { priority: PlatformActivity['priority'] }) {
  const colors = {
    low: 'bg-gray-500',
    medium: 'bg-blue-500',
    high: 'bg-yellow-500',
    urgent: 'bg-red-500'
  }

  return (
    <div className={cn(
      "w-2 h-2 rounded-full",
      colors[priority],
      priority === 'urgent' && "animate-pulse"
    )} />
  )
}

function ActivityCard({ activity }: { activity: PlatformActivity }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="group"
    >
      <Card className="bg-white/5 border-white/10 hover:border-white/20 transition-all">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <div className="flex flex-col items-center gap-2">
              <ActivityTypeIcon type={activity.type} />
              <PriorityIndicator priority={activity.priority} />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h4 className="text-sm font-semibold text-white truncate">{activity.title}</h4>
                <Badge variant="outline" className="text-[10px] bg-white/5 border-white/10 ml-auto">
                  {activity.status}
                </Badge>
              </div>

              <p className="text-xs text-gray-400 leading-relaxed mb-2">{activity.description}</p>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Clock className="w-3 h-3" />
                  <span>{new Date(activity.timestamp).toLocaleTimeString()}</span>
                </div>

                {activity.agentName && (
                  <span className="text-xs text-blue-400">{activity.agentName}</span>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

function SuggestionCard({ suggestion, onApply, onDismiss }: {
  suggestion: ProactiveSuggestion
  onApply?: (suggestionId: string) => void
  onDismiss?: (suggestionId: string) => void
}) {
  const impactColors = {
    low: 'text-gray-400',
    medium: 'text-yellow-400',
    high: 'text-red-400'
  }

  const handleApply = () => {
    if (onApply) {
      onApply(suggestion.id)
    }
  }

  const handleDismiss = () => {
    if (onDismiss) {
      onDismiss(suggestion.id)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.02 }}
      className="group"
    >
      <Card className="bg-gradient-to-br from-blue-500/5 to-purple-500/5 border-blue-500/20 hover:border-blue-500/30 transition-all">
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-blue-400" />
              <span className="text-xs text-blue-400 uppercase font-mono tracking-wider">AI Suggestion</span>
            </div>
            <Badge variant="outline" className={cn("text-xs", impactColors[suggestion.impact])}>
              {suggestion.impact} impact
            </Badge>
          </div>

          <h4 className="text-sm font-semibold text-white mb-2">{suggestion.title}</h4>
          <p className="text-xs text-gray-400 leading-relaxed mb-3">{suggestion.description}</p>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-400">Confidence</span>
              <span className="text-blue-400 font-semibold">{suggestion.confidence}%</span>
            </div>
            <Progress value={suggestion.confidence} className="h-1.5" />
          </div>

          {suggestion.estimatedBenefit && (
            <div className="mt-3 p-2 bg-green-500/10 border border-green-500/20 rounded-lg">
              <div className="flex items-center gap-2">
                <Target className="w-3 h-3 text-green-400" />
                <span className="text-xs text-green-400 font-semibold">{suggestion.estimatedBenefit}</span>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between mt-4">
            <span className="text-xs text-gray-500">
              {suggestion.relatedAgents.length} agents involved
            </span>

            <div className="flex gap-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={handleDismiss}
                className="h-7 text-xs text-gray-400 hover:text-white"
              >
                Dismiss
              </Button>
              {suggestion.actionable && (
                <Button
                  size="sm"
                  onClick={handleApply}
                  className="bg-blue-600 hover:bg-blue-500 text-white h-7 text-xs"
                >
                  <ArrowRight className="w-3 h-3 mr-1" />
                  Apply
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

function InsightCard({ insight }: { insight: ConciergeInsight }) {
  const trendColors = {
    up: 'text-green-400',
    down: 'text-red-400',
    stable: 'text-blue-400'
  }

  const trendIcons = {
    up: '↗',
    down: '↘',
    stable: '→'
  }

  return (
    <Card className="bg-white/5 border-white/10">
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-400 uppercase tracking-wider">{insight.category}</span>
          <div className={cn("flex items-center gap-1 text-xs", trendColors[insight.trend])}>
            <span>{trendIcons[insight.trend]}</span>
            <span>{Math.abs(insight.trendValue)}%</span>
          </div>
        </div>

        <div className="text-2xl font-bold text-white mb-1">{insight.value}</div>
        <div className="text-xs text-gray-400">{insight.title}</div>
        <div className="text-xs text-gray-500 mt-2">{insight.description}</div>
      </CardContent>
    </Card>
  )
}

function ConciergeChatInterface() {
  const [isListening, setIsListening] = useState(false)
  const [message, setMessage] = useState('')

  return (
    <Card className="bg-white/5 border-white/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <Brain className="w-5 h-5 text-purple-500" />
          Ask Claude Concierge
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="relative">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask about platform performance, agent coordination, or get insights..."
              className="pr-20 bg-black/20 border-white/10 text-white placeholder:text-gray-500"
            />
            <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
              <Button
                size="sm"
                variant={isListening ? "default" : "ghost"}
                className={cn(
                  "h-7 w-7 p-0",
                  isListening && "bg-red-500 hover:bg-red-600"
                )}
                onClick={() => setIsListening(!isListening)}
              >
                {isListening ? <MicOff className="w-3 h-3" /> : <Mic className="w-3 h-3" />}
              </Button>
              <Button size="sm" className="h-7 w-7 p-0 bg-purple-600 hover:bg-purple-500">
                <Send className="w-3 h-3" />
              </Button>
            </div>
          </div>

          <div className="space-y-2">
            <h4 className="text-xs text-gray-400 uppercase tracking-wider">Quick Actions</h4>
            <div className="grid grid-cols-2 gap-2">
              {[
                'Platform health check',
                'Agent performance review',
                'Customer satisfaction analysis',
                'Optimization suggestions'
              ].map((action, index) => (
                <Button
                  key={index}
                  size="sm"
                  variant="outline"
                  className="border-white/20 text-white hover:bg-white/10 text-xs h-8 justify-start"
                  onClick={() => setMessage(action)}
                >
                  {action}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

interface ClaudeConciergeInterfaceProps {
  className?: string
}

export function ClaudeConciergeInterface({ className = '' }: ClaudeConciergeInterfaceProps) {
  const [selectedView, setSelectedView] = useState('activity')
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Use real data from hooks and store
  const { insights } = useConciergeInsights()
  const { suggestions, applySuggestion, dismissSuggestion } = useProactiveSuggestions()
  const { messages, isTyping, sendMessage } = useConciergeChat()
  const platformActivities = usePlatformActivities()

  // Initialize the integration
  const integration = useAgentEcosystemIntegration({
    autoRefresh: true,
    enableRealTime: true,
    initializeOnMount: true,
  })

  return (
    <div className={cn("w-full space-y-6", className)}>
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Claude Concierge - Omnipresent AI</h1>
          <p className="text-gray-400 text-sm">
            Platform-wide intelligence with complete awareness of all 43+ agents and real-time coordination
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge className="bg-purple-500/10 text-purple-400 border-purple-500/20">
            <Brain className="w-3 h-3 mr-1" />
            AI Active
          </Badge>
          <Badge className="bg-green-500/10 text-green-400 border-green-500/20">
            <Eye className="w-3 h-3 mr-1" />
            Monitoring 43+ Agents
          </Badge>
          <Button
            size="sm"
            variant="outline"
            className="border-white/20 text-white"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <Activity className={cn("w-4 h-4 mr-2", autoRefresh && "animate-pulse text-green-400")} />
            Auto-refresh {autoRefresh ? 'On' : 'Off'}
          </Button>
        </div>
      </div>

      {/* Real-time Insights */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {insights.length > 0 ? (
          insights.slice(0, 4).map((insight, index) => (
            <motion.div
              key={insight.timestamp + index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <InsightCard insight={insight} />
            </motion.div>
          ))
        ) : (
          mockInsights.map((insight, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <InsightCard insight={insight} />
            </motion.div>
          ))
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Interface */}
        <div className="lg:col-span-1">
          <ConciergeChatInterface />
        </div>

        {/* Main Content Area */}
        <div className="lg:col-span-2">
          <Card className="bg-white/5 border-white/10">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white">Platform Activity</CardTitle>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="ghost" className="h-8">
                    <Filter className="w-4 h-4" />
                  </Button>
                  <Button size="sm" variant="ghost" className="h-8">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {platformActivities.length > 0 ? (
                  platformActivities.slice(0, 20).map((activity, index) => (
                    <ActivityCard key={activity.id} activity={activity} />
                  ))
                ) : (
                  <div className="text-center py-8">
                    <Activity className="w-8 h-8 text-gray-500 mx-auto mb-2" />
                    <p className="text-gray-400 text-sm">No platform activities available</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Proactive Suggestions */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-white">AI-Powered Suggestions</h2>
          <Badge className="bg-blue-500/10 text-blue-400 border-blue-500/20 text-xs">
            {suggestions.length} Active
          </Badge>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {suggestions.length > 0 ? (
            suggestions.map((suggestion) => (
              <SuggestionCard
                key={suggestion.id}
                suggestion={suggestion}
                onApply={applySuggestion}
                onDismiss={dismissSuggestion}
              />
            ))
          ) : (
            <div className="col-span-full text-center py-8">
              <Sparkles className="w-8 h-8 text-gray-500 mx-auto mb-2" />
              <p className="text-gray-400 text-sm">No proactive suggestions available</p>
            </div>
          )}
        </div>
      </div>

      {/* System Status */}
      <Card className="bg-gradient-to-r from-green-500/10 to-blue-500/10 border-white/10">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">Omnipresent Intelligence Status</h3>
              <p className="text-gray-400 text-sm">
                Claude Concierge is actively monitoring and coordinating across the entire platform ecosystem
              </p>
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse shadow-[0_0_10px_rgba(34,197,94,0.5)]" />
                <span className="text-sm text-green-400 font-semibold">System Optimal</span>
              </div>
              <Button className="bg-purple-600 hover:bg-purple-500 text-white">
                <Settings className="w-4 h-4 mr-2" />
                Configure AI
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default ClaudeConciergeInterface