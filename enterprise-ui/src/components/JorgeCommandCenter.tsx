// Jorge Real Estate Command Center
// Professional dashboard for managing Jorge's bot ecosystem with REAL-TIME WebSocket integration

'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Bot,
  TrendingUp,
  Phone,
  MessageSquare,
  Clock,
  Users,
  Target,
  Activity,
  Zap,
  Calendar,
  Star,
  Wifi,
  WifiOff,
  AlertTriangle,
  Loader2
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { jorgeApi, jorgeQueryKeys, type JorgeBotStatus } from '@/lib/jorge-api-client'
import { useChatStore } from '@/store/useChatStore'
import JorgeChatInterface from './JorgeChatInterface'
import { useWebSocket } from '@/components/providers/WebSocketProvider'
import { useBotStatus, type BotStatusMap } from '@/lib/hooks/useBotStatus'
import { useRealTimeMetrics } from '@/lib/hooks/useRealTimeMetrics'

interface BotPerformanceCardProps {
  bot: JorgeBotStatus
  realTimeBotStatus?: BotStatusMap[keyof BotStatusMap]
  onStartConversation: (botId: string) => void
  isRealTimeConnected?: boolean
}

function BotPerformanceCard({
  bot,
  realTimeBotStatus,
  onStartConversation,
  isRealTimeConnected = false
}: BotPerformanceCardProps) {
  // Use real-time status if available, otherwise fall back to bot data
  const currentStatus = realTimeBotStatus?.status || bot.status
  const currentStep = realTimeBotStatus?.currentStep || 'Ready'
  const activeConversations = realTimeBotStatus?.activeConversations || bot.conversationsToday
  const responseTime = realTimeBotStatus?.performance.avgResponseTime || bot.responseTimeMs
  const lastActivity = realTimeBotStatus?.lastActivity || bot.lastActivity

  const statusColor = {
    active: 'bg-green-500',
    processing: 'bg-blue-500',
    idle: 'bg-yellow-500',
    completed: 'bg-purple-500',
    error: 'bg-red-500',
    offline: 'bg-gray-400',
    online: 'bg-green-500',
    typing: 'bg-blue-500'
  }[currentStatus] || 'bg-gray-400'

  const statusText = {
    active: 'Active',
    processing: 'Processing',
    idle: 'Idle',
    completed: 'Ready',
    error: 'Error',
    offline: 'Offline',
    online: 'Online',
    typing: 'Typing'
  }[currentStatus] || currentStatus
  
  const getBotDescription = (botId: string) => {
    switch (botId) {
      case 'jorge-seller-bot':
        return 'Confrontational qualification specialist. No-BS approach for motivated sellers only.'
      case 'lead-bot':
        return '3-7-30 day automation lifecycle. Voice integration on Day 7 calls.'
      case 'intent-decoder':
        return 'FRS/PCS dual scoring with 95% accuracy. Temperature classification system.'
      default:
        return 'Specialized real estate AI agent.'
    }
  }
  
  const getBotFeatures = (botId: string) => {
    switch (botId) {
      case 'jorge-seller-bot':
        return ['LangGraph 5-node workflow', 'Stall-breaker automation', 'GHL sync', '6% commission system']
      case 'lead-bot':
        return ['Complete automation', 'Retell AI voice', 'CMA injection', 'Post-showing surveys']
      case 'intent-decoder':
        return ['28-feature pipeline', '42.3ms response', 'SHAP explainability', 'Claude escalation']
      default:
        return ['AI-powered', 'Real-time analysis', 'Enterprise-grade']
    }
  }
  
  return (
    <Card className="h-full hover:shadow-lg transition-all duration-200 border-l-4 border-l-blue-500">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Bot className="w-8 h-8 text-blue-600" />
              <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-white ${statusColor}`} />
            </div>
            <div>
              <CardTitle className="text-lg font-bold">{bot.name}</CardTitle>
              <p className="text-sm text-gray-600 mt-1">
                {getBotDescription(bot.id)}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {isRealTimeConnected && (
              <Wifi className="w-3 h-3 text-green-500" title="Real-time connected" />
            )}
            <Badge
              variant="outline"
              className={`${
                currentStatus === 'active' || currentStatus === 'online'
                  ? 'bg-green-50 text-green-700 border-green-200'
                  : currentStatus === 'processing'
                  ? 'bg-blue-50 text-blue-700 border-blue-200'
                  : currentStatus === 'error'
                  ? 'bg-red-50 text-red-700 border-red-200'
                  : 'bg-gray-50 text-gray-600'
              }`}
            >
              {statusText}
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Current Step (if real-time connected) */}
        {isRealTimeConnected && currentStep && currentStep !== 'Ready' && (
          <div className="p-2 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600" />
              <div className="text-sm font-medium text-blue-800">Current Step:</div>
            </div>
            <div className="text-sm text-blue-700 mt-1">{currentStep}</div>
          </div>
        )}

        {/* Performance Metrics */}
        <div className="grid grid-cols-3 gap-4 text-center">
          <div className="p-2 bg-blue-50 rounded-lg">
            <div className="text-lg font-bold text-blue-700">
              {activeConversations}
              {isRealTimeConnected && (
                <Loader2 className="w-3 h-3 inline ml-1 animate-pulse" />
              )}
            </div>
            <div className="text-xs text-blue-600">
              {isRealTimeConnected ? 'Active Now' : 'Today'}
            </div>
          </div>
          <div className="p-2 bg-green-50 rounded-lg">
            <div className="text-lg font-bold text-green-700">{bot.leadsQualified}</div>
            <div className="text-xs text-green-600">Qualified</div>
          </div>
          <div className="p-2 bg-purple-50 rounded-lg">
            <div className="text-lg font-bold text-purple-700">
              {Math.round(responseTime)}ms
            </div>
            <div className="text-xs text-purple-600">Response</div>
          </div>
        </div>
        
        {/* Bot Features */}
        <div className="space-y-2">
          <h4 className="font-semibold text-sm text-gray-700">Capabilities:</h4>
          <div className="flex flex-wrap gap-1">
            {getBotFeatures(bot.id).map((feature, index) => (
              <Badge key={index} variant="secondary" className="text-xs">
                {feature}
              </Badge>
            ))}
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Button 
            onClick={() => onStartConversation(bot.id)}
            className="flex-1 bg-blue-600 hover:bg-blue-700"
            size="sm"
            disabled={bot.status === 'offline'}
          >
            <MessageSquare className="w-4 h-4 mr-2" />
            Start Chat
          </Button>
          <Button variant="outline" size="sm">
            <Activity className="w-4 h-4 mr-1" />
            Stats
          </Button>
        </div>
        
        {/* Last Activity */}
        <div className="text-xs text-gray-500 border-t pt-2">
          <div className="flex items-center justify-between">
            <span>Last active:</span>
            <div className="flex items-center gap-1">
              {isRealTimeConnected && (
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              )}
              <span>
                {lastActivity
                  ? new Date(lastActivity).toLocaleTimeString()
                  : new Date(bot.lastActivity).toLocaleTimeString()
                }
              </span>
            </div>
          </div>
          {isRealTimeConnected && realTimeBotStatus && (
            <div className="flex justify-between mt-1 text-xs text-green-600">
              <span>Success Rate:</span>
              <span>{realTimeBotStatus.performance.successRate.toFixed(1)}%</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function SystemMetrics() {
  const { connected: wsConnected } = useWebSocket()
  const { botStatus, getActiveBotsCount, isAnyBotProcessing } = useBotStatus()
  const { metrics, isLoading, dataAge } = useRealTimeMetrics()

  const { data: bots = [] } = useQuery({
    queryKey: jorgeQueryKeys.bots,
    queryFn: jorgeApi.getBots,
    refetchInterval: wsConnected ? 60000 : 15000 // Slower refresh if WebSocket connected
  })

  // Use real-time metrics if available, otherwise fall back to bot data
  const totalConversations = metrics?.conversations.active ||
    bots.reduce((sum, bot) => sum + bot.conversationsToday, 0)

  const totalLeadsQualified = metrics?.conversations.qualified_sellers ||
    bots.reduce((sum, bot) => sum + bot.leadsQualified, 0)

  const avgResponseTime = metrics?.conversations.avg_response_time_ms ||
    (bots.length > 0
      ? Math.round(bots.reduce((sum, bot) => sum + bot.responseTimeMs, 0) / bots.length)
      : 0)

  const activeBots = getActiveBotsCount()
  const onlineBots = bots.filter(bot => bot.status === 'online').length
  const displayBotCount = wsConnected ? activeBots : onlineBots
  
  return (
    <div className="space-y-4">
      {/* Real-time connection status */}
      {wsConnected && (
        <Alert className="bg-green-50 border-green-200">
          <Wifi className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">
            <div className="flex items-center justify-between">
              <span>
                Real-time monitoring active • Data age: {dataAge}s
                {isAnyBotProcessing() && (
                  <span className="ml-2 text-green-600">• Bots processing</span>
                )}
              </span>
              {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
            </div>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className={wsConnected ? 'border-l-4 border-l-green-500' : ''}>
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <MessageSquare className="w-8 h-8 text-blue-600" />
              {wsConnected && isAnyBotProcessing() && (
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse ml-2" />
              )}
            </div>
            <div className="text-2xl font-bold text-gray-900">{totalConversations}</div>
            <div className="text-sm text-gray-600">
              {wsConnected ? 'Active Conversations' : 'Conversations Today'}
            </div>
          </CardContent>
        </Card>

        <Card className={wsConnected ? 'border-l-4 border-l-green-500' : ''}>
          <CardContent className="p-4 text-center">
            <Target className="w-8 h-8 text-green-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900">{totalLeadsQualified}</div>
            <div className="text-sm text-gray-600">Leads Qualified</div>
          </CardContent>
        </Card>

        <Card className={wsConnected ? 'border-l-4 border-l-green-500' : ''}>
          <CardContent className="p-4 text-center">
            <Zap className="w-8 h-8 text-purple-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-gray-900">
              {Math.round(avgResponseTime)}ms
            </div>
            <div className="text-sm text-gray-600">Avg Response</div>
            {wsConnected && metrics && (
              <div className="text-xs text-purple-600 mt-1">
                Target: 42ms
              </div>
            )}
          </CardContent>
        </Card>

        <Card className={wsConnected ? 'border-l-4 border-l-green-500' : ''}>
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <Bot className="w-8 h-8 text-orange-600" />
              {wsConnected && (
                <Wifi className="w-3 h-3 text-green-500 ml-1" />
              )}
            </div>
            <div className="text-2xl font-bold text-gray-900">
              {displayBotCount}/{bots.length}
            </div>
            <div className="text-sm text-gray-600">
              {wsConnected ? 'Bots Active' : 'Bots Online'}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export function JorgeCommandCenter() {
  const [activeChatBot, setActiveChatBot] = useState<string | null>(null)
  const [activeChatConversation, setActiveChatConversation] = useState<string | null>(null)

  // WebSocket and real-time hooks
  const { connected: wsConnected, connectionState, reconnect } = useWebSocket()
  const { botStatus, getOverallHealth, lastUpdate: botLastUpdate } = useBotStatus()
  const { metrics, lastUpdate: metricsLastUpdate, dataAge } = useRealTimeMetrics()

  const { data: bots = [], isLoading } = useQuery({
    queryKey: jorgeQueryKeys.bots,
    queryFn: jorgeApi.getBots,
    refetchInterval: wsConnected ? 60000 : 15000 // Slower refresh when WebSocket active
  })

  const startJorgeSellerConversation = useChatStore((state) => state.startJorgeSellerConversation)
  const overallHealth = getOverallHealth()
  
  const handleStartConversation = async (botId: string) => {
    if (botId === 'jorge-seller-bot') {
      try {
        const conversationId = await startJorgeSellerConversation()
        setActiveChatBot(botId)
        setActiveChatConversation(conversationId)
      } catch (error) {
        console.error('Failed to start conversation:', error)
      }
    } else {
      // For other bots, generate a conversation ID
      const conversationId = `conv_${Date.now()}_${botId}`
      setActiveChatBot(botId)
      setActiveChatConversation(conversationId)
    }
  }
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Bot className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <div className="text-lg font-medium text-gray-600">Loading Jorge's AI Platform...</div>
        </div>
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Jorge Command Center</h1>
          <p className="text-gray-600 mt-1">
            Professional AI-powered real estate bot ecosystem
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="bg-green-50 text-green-700">
            ✅ Production Ready
          </Badge>
          <Badge variant="outline" className="bg-blue-50 text-blue-700">
            🤖 LangGraph Powered
          </Badge>

          {/* Real-time status indicator */}
          {wsConnected ? (
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300">
              <Wifi className="w-3 h-3 mr-1" />
              Live
            </Badge>
          ) : (
            <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-300">
              <WifiOff className="w-3 h-3 mr-1" />
              Polling
            </Badge>
          )}

          {/* System health indicator */}
          <Badge
            variant="outline"
            className={`${
              overallHealth === 'healthy'
                ? 'bg-green-50 text-green-700 border-green-300'
                : overallHealth === 'degraded'
                ? 'bg-yellow-50 text-yellow-700 border-yellow-300'
                : 'bg-red-50 text-red-700 border-red-300'
            }`}
          >
            {overallHealth === 'healthy' && '💚 Healthy'}
            {overallHealth === 'degraded' && '⚠️ Degraded'}
            {overallHealth === 'critical' && '🔴 Critical'}
          </Badge>
        </div>
      </div>
      
      {/* System Metrics */}
      <SystemMetrics />
      
      <Tabs defaultValue="dashboard" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="dashboard">Bot Dashboard</TabsTrigger>
          <TabsTrigger value="chat">Active Chat</TabsTrigger>
          <TabsTrigger value="analytics">Performance Analytics</TabsTrigger>
        </TabsList>
        
        <TabsContent value="dashboard" className="space-y-6">
          {/* Real-time Connection Issues Alert */}
          {connectionState === 'error' && (
            <Alert className="mb-6 bg-yellow-50 border-yellow-200">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <AlertDescription className="text-yellow-800">
                <div className="flex items-center justify-between">
                  <span>WebSocket connection failed. Using polling mode for updates.</span>
                  <Button size="sm" variant="outline" onClick={reconnect}>
                    Reconnect
                  </Button>
                </div>
              </AlertDescription>
            </Alert>
          )}

          {/* Bot Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {bots.map((bot) => {
              // Map bot.id to real-time status key
              const botKey = bot.id.replace('-', '-') as keyof BotStatusMap
              const realTimeStatus = botStatus[botKey]

              return (
                <BotPerformanceCard
                  key={bot.id}
                  bot={bot}
                  realTimeBotStatus={realTimeStatus}
                  isRealTimeConnected={wsConnected}
                  onStartConversation={handleStartConversation}
                />
              )
            })}
          </div>
          
          {/* Special Features Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Star className="w-5 h-5 text-yellow-500" />
                Jorge's Unique Features
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <Phone className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                  <h3 className="font-semibold mb-1">Voice Integration</h3>
                  <p className="text-sm text-gray-600">Retell AI voice calls on Day 7 of lead sequence</p>
                </div>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <TrendingUp className="w-8 h-8 text-green-600 mx-auto mb-2" />
                  <h3 className="font-semibold mb-1">6% Commission System</h3>
                  <p className="text-sm text-gray-600">Automatic calculation with ML-predicted sale prices</p>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <Clock className="w-8 h-8 text-purple-600 mx-auto mb-2" />
                  <h3 className="font-semibold mb-1">3-7-30 Automation</h3>
                  <p className="text-sm text-gray-600">Complete lifecycle automation with behavioral scoring</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="chat">
          {activeChatBot && activeChatConversation ? (
            <JorgeChatInterface
              botId={activeChatBot}
              botName={bots.find(b => b.id === activeChatBot)?.name || 'Jorge AI Bot'}
              conversationId={activeChatConversation}
            />
          ) : (
            <Card className="h-[600px] flex items-center justify-center">
              <div className="text-center">
                <Bot className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">No Active Chat</h3>
                <p className="text-gray-500 mb-4">Select a bot from the dashboard to start a conversation</p>
                <Button onClick={() => handleStartConversation('jorge-seller-bot')}>
                  Start Jorge Seller Chat
                </Button>
              </div>
            </Card>
          )}
        </TabsContent>
        
        <TabsContent value="analytics">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Real-time System Status */}
            <Card className="border-l-4 border-l-blue-500">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5 text-blue-600" />
                  Real-time System Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm">Connection Status:</span>
                  <Badge variant={wsConnected ? 'secondary' : 'outline'}>
                    {wsConnected ? 'Connected' : 'Disconnected'}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">System Health:</span>
                  <Badge
                    variant={overallHealth === 'healthy' ? 'secondary' : 'destructive'}
                  >
                    {overallHealth}
                  </Badge>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm">Data Age:</span>
                  <span className="text-sm text-gray-600">{dataAge}s</span>
                </div>
                {botLastUpdate && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Bot Update:</span>
                    <span className="text-sm text-gray-600">
                      {new Date(botLastUpdate).toLocaleTimeString()}
                    </span>
                  </div>
                )}
                {metricsLastUpdate && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm">Metrics Update:</span>
                    <span className="text-sm text-gray-600">
                      {new Date(metricsLastUpdate).toLocaleTimeString()}
                    </span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Jorge Seller Bot Performance */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5 text-green-600" />
                  Jorge Seller Metrics
                </CardTitle>
              </CardHeader>
              <CardContent>
                {metrics?.jorge_seller_bot ? (
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm">Conversations Today:</span>
                      <span className="font-semibold">
                        {metrics.jorge_seller_bot.conversations_today}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Confrontational Effectiveness:</span>
                      <span className="font-semibold text-green-600">
                        {metrics.jorge_seller_bot.confrontational_effectiveness}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Hot Leads:</span>
                      <span className="font-semibold text-red-600">
                        {metrics.jorge_seller_bot.temperature_distribution.hot}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Avg Qualification Time:</span>
                      <span className="font-semibold">
                        {metrics.jorge_seller_bot.avg_qualification_time_minutes}min
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-4">
                    📊 Connecting to Jorge metrics...
                  </div>
                )}
              </CardContent>
            </Card>

            {/* ML Analytics Performance */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5 text-purple-600" />
                  ML Pipeline Metrics
                </CardTitle>
              </CardHeader>
              <CardContent>
                {metrics?.intent_decoder ? (
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm">Analyses Today:</span>
                      <span className="font-semibold">
                        {metrics.intent_decoder.analyses_today}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Accuracy Rate:</span>
                      <span className="font-semibold text-green-600">
                        {metrics.intent_decoder.accuracy_rate}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Avg Processing:</span>
                      <span
                        className={`font-semibold ${
                          metrics.intent_decoder.avg_processing_time_ms <= 42
                            ? 'text-green-600'
                            : 'text-yellow-600'
                        }`}
                      >
                        {metrics.intent_decoder.avg_processing_time_ms}ms
                      </span>
                    </div>
                    <div className="text-xs text-gray-500 pt-2">
                      Target: 42ms • 95% accuracy
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-4">
                    🧠 Connecting to ML analytics...
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Revenue Tracking */}
            {metrics?.revenue && (
              <Card className="col-span-1 md:col-span-2 lg:col-span-1">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-green-600" />
                    Revenue Pipeline
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm">Pipeline Value:</span>
                      <span className="font-semibold text-green-600">
                        ${metrics.revenue.potential_pipeline.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Jorge's Commission (6%):</span>
                      <span className="font-semibold text-purple-600">
                        ${metrics.revenue.commission_projected.toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm">Deals in Progress:</span>
                      <span className="font-semibold">
                        {metrics.revenue.deals_in_progress}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Lead Bot Automation */}
            <Card className="md:col-span-2 lg:col-span-2">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Phone className="w-5 h-5 text-blue-600" />
                  3-7-30 Lead Automation Performance
                </CardTitle>
              </CardHeader>
              <CardContent>
                {metrics?.lead_bot ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-lg font-bold text-blue-600">
                        {metrics.lead_bot.active_sequences}
                      </div>
                      <div className="text-xs text-gray-600">Active Sequences</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-green-600">
                        {metrics.lead_bot.day_7_call_success_rate}%
                      </div>
                      <div className="text-xs text-gray-600">Day 7 Call Success</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-purple-600">
                        {metrics.lead_bot.retell_ai_metrics.calls_today}
                      </div>
                      <div className="text-xs text-gray-600">Voice Calls Today</div>
                    </div>
                    <div className="text-center">
                      <div className="text-lg font-bold text-orange-600">
                        {metrics.lead_bot.cma_injection_impact}%
                      </div>
                      <div className="text-xs text-gray-600">CMA Impact</div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-4">
                    📞 Connecting to automation metrics...
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default JorgeCommandCenter