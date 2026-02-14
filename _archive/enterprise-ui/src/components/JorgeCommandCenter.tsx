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
  Loader2,
  Brain,
  Map
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { jorgeApi, jorgeQueryKeys, type JorgeBotStatus } from '@/lib/jorge-api-client'
import { jorgeSellerApi } from '@/lib/api/jorge-seller-api'
import { useChatStore } from '@/store/useChatStore'
import JorgeChatInterface from './JorgeChatInterface'
import { useWebSocket } from '@/components/providers/WebSocketProvider'
import useBotStatus, { type BotStatusMap } from '@/lib/hooks/useBotStatus'
import { useRealTimeMetrics } from '@/lib/hooks/useRealTimeMetrics'
import { useJorgeWebSocketHandlers, useJorgeLeadSubscription } from '@/lib/websocket-handlers/jorge-handlers'
import { useAgentEcosystemStore } from '@/store/agentEcosystemStore'
import { ShapExplainability } from './analytics/ShapExplainability'
import { HeatmapOfOpportunity } from './analytics/HeatmapOfOpportunity'
import { BotInsightsPanel } from './analytics/BotInsightsPanel'
import { VoiceCallMonitor } from './analytics/VoiceCallMonitor'
import { CommissionPipeline } from './analytics/CommissionPipeline'
import { LeadBotSequenceProgress, LeadBotMessageTimeline, LeadBotActionControls } from './lead-bot'
import { useLeadBotWebSocketHandlers } from '@/lib/websocket-handlers/lead-bot-handlers'
import { cn } from '@/lib/utils'

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
  // Get Jorge-specific data from agent ecosystem store
  const agents = useAgentEcosystemStore(state => state.agents)
  const jorgeAgent = agents['jorge-seller-bot']

  // Use real-time status if available, otherwise fall back to bot data
  const currentStatus = realTimeBotStatus?.status || bot.status
  const currentStep = realTimeBotStatus?.currentStep || jorgeAgent?.currentStep || 'Ready'
  const activeConversations = realTimeBotStatus?.activeConversations || bot.conversationsToday
  const responseTime = realTimeBotStatus?.performance?.avgResponseTime || bot.responseTimeMs
  const lastActivity = realTimeBotStatus?.lastActivity || jorgeAgent?.lastActivity || bot.lastActivity

  // Jorge-specific metrics from real-time data
  const jorgeMetadata = jorgeAgent?.metadata
  const frsScore = jorgeMetadata?.frsScore
  const pcsScore = jorgeMetadata?.pcsScore
  const sellerTemperature = jorgeMetadata?.sellerTemperature
  const questionsAnswered = jorgeMetadata?.questionsAnswered || 0
  const stallDetected = jorgeMetadata?.stallDetected
  const confrontationalEffectiveness = jorgeMetadata?.confrontationalEffectiveness

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
    <Card className="h-full jorge-card jorge-card-hover border-l-4 border-l-blue-500 overflow-hidden">
      <CardHeader className="pb-3 relative">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Bot className="w-6 h-6 text-blue-500" />
              </div>
              <div className={`absolute -bottom-1 -right-1 w-3 h-3 rounded-full border-2 border-card ${statusColor}`} />
            </div>
            <div>
              <CardTitle className="text-lg font-bold text-white">{bot.name}</CardTitle>
              <p className="text-xs text-gray-400 mt-1 line-clamp-1">
                {getBotDescription(bot.id)}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            {isRealTimeConnected && (
              <Wifi className="w-3 h-3 text-jorge-glow animate-pulse" title="Real-time connected" />
            )}
            <Badge
              variant="outline"
              className={cn(
                "jorge-code text-[10px]",
                currentStatus === 'active' || currentStatus === 'online'
                  ? 'bg-green-500/10 text-green-400 border-green-500/20'
                  : currentStatus === 'processing'
                  ? 'bg-blue-500/10 text-blue-400 border-blue-500/20'
                  : currentStatus === 'error'
                  ? 'bg-red-500/10 text-red-400 border-red-500/20'
                  : 'bg-gray-500/10 text-gray-400 border-gray-500/20'
              )}
            >
              {statusText}
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Current Step (if real-time connected) */}
        {isRealTimeConnected && currentStep && currentStep !== 'Ready' && (
          <div className="p-2 bg-blue-500/5 border border-blue-500/10 rounded-lg">
            <div className="flex items-center gap-2">
              <Activity className="w-3 h-3 text-blue-400" />
              <div className="text-[10px] jorge-code text-blue-300">Current Step:</div>
            </div>
            <div className="text-xs text-blue-200 mt-1 font-medium">{currentStep}</div>
          </div>
        )}

        {/* Performance Metrics */}
        <div className="grid grid-cols-3 gap-2 text-center">
          <div className="p-2 bg-blue-500/5 rounded-lg border border-blue-500/10">
            <div className="text-lg font-bold text-blue-400">
              {activeConversations}
              {isRealTimeConnected && (
                <Loader2 className="w-3 h-3 inline ml-1 animate-pulse" />
              )}
            </div>
            <div className="text-[10px] jorge-code text-blue-500/70">
              {isRealTimeConnected ? 'Active' : 'Today'}
            </div>
          </div>
          <div className="p-2 bg-jorge-glow/5 rounded-lg border border-jorge-glow/10">
            <div className="text-lg font-bold text-jorge-glow">{bot.leadsQualified}</div>
            <div className="text-[10px] jorge-code text-jorge-glow/70">Qual</div>
          </div>
          <div className="p-2 bg-jorge-gold/5 rounded-lg border border-jorge-gold/10">
            <div className="text-lg font-bold text-jorge-gold">
              {Math.round(responseTime)}<span className="text-[10px]">ms</span>
            </div>
            <div className="text-[10px] jorge-code text-jorge-gold/70">Lat</div>
          </div>
        </div>

        {/* Jorge-Specific Real-Time Metrics */}
        {bot.id === 'jorge-seller-bot' && isRealTimeConnected && jorgeMetadata && (
          <div className="space-y-3 pt-2 border-t border-white/5">
            {/* Qualification Progress */}
            {questionsAnswered > 0 && (
              <div className="p-2 bg-purple-500/5 rounded-lg border border-purple-500/10">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] jorge-code text-purple-400">QUALIFICATION</span>
                  <span className="text-xs text-purple-300 font-bold">{questionsAnswered}/4</span>
                </div>
                <div className="w-full bg-white/5 rounded-full h-1.5">
                  <div
                    className="bg-purple-500 h-1.5 rounded-full transition-all duration-500"
                    style={{ width: `${(questionsAnswered / 4) * 100}%` }}
                  />
                </div>
              </div>
            )}

            {/* FRS/PCS Scores */}
            {(frsScore || pcsScore) && (
              <div className="grid grid-cols-2 gap-2">
                {frsScore && (
                  <div className="p-2 bg-blue-500/5 rounded-lg border border-blue-500/10 text-center">
                    <div className="text-sm font-bold text-blue-400">{frsScore}</div>
                    <div className="text-[9px] jorge-code text-blue-500/70">FRS</div>
                  </div>
                )}
                {pcsScore && (
                  <div className="p-2 bg-purple-500/5 rounded-lg border border-purple-500/10 text-center">
                    <div className="text-sm font-bold text-purple-400">{pcsScore}</div>
                    <div className="text-[9px] jorge-code text-purple-500/70">PCS</div>
                  </div>
                )}
              </div>
            )}

            {/* Temperature Badge */}
            {sellerTemperature && (
              <div className="flex items-center justify-between">
                <span className="text-[10px] jorge-code text-gray-400">TEMPERATURE</span>
                <Badge className={cn(
                  "text-[9px] px-2 py-0.5 font-bold transition-all duration-500",
                  sellerTemperature === 'hot'
                    ? 'bg-red-500/20 text-red-400 border-red-500/30 shadow-[0_0_10px_rgba(239,68,68,0.3)]'
                    : sellerTemperature === 'warm'
                    ? 'bg-orange-500/20 text-orange-400 border-orange-500/30'
                    : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                )}>
                  {sellerTemperature.toUpperCase()}
                  {sellerTemperature === 'hot' && '🔥'}
                </Badge>
              </div>
            )}

            {/* Stall Detection Alert */}
            {stallDetected && (
              <div className="p-2 bg-yellow-500/10 rounded-lg border border-yellow-500/20 flex items-center gap-2">
                <AlertTriangle className="w-3 h-3 text-yellow-400" />
                <div className="flex-1">
                  <div className="text-[10px] jorge-code text-yellow-400">STALL DETECTED</div>
                  <div className="text-[9px] text-yellow-300/70">Confrontational script ready</div>
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Bot Features */}
        <div className="space-y-2">
          <h4 className="jorge-code text-[10px] text-gray-500">Capabilities:</h4>
          <div className="flex flex-wrap gap-1">
            {getBotFeatures(bot.id).map((feature, index) => (
              <Badge key={index} variant="secondary" className="text-[9px] bg-white/5 text-gray-300 border-none px-1.5 py-0">
                {feature}
              </Badge>
            ))}
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Button 
            onClick={() => onStartConversation(bot.id)}
            className="flex-1 bg-jorge-electric hover:bg-blue-600 text-white jorge-haptic h-8 text-xs"
            size="sm"
            disabled={bot.status === 'offline'}
          >
            <MessageSquare className="w-3 h-3 mr-2" />
            Control
          </Button>
          <Button variant="outline" size="sm" className="h-8 text-xs border-white/10 hover:bg-white/5">
            <Activity className="w-3 h-3" />
          </Button>
        </div>
        
        {/* Last Activity */}
        <div className="text-[10px] jorge-code text-gray-600 border-t border-white/5 pt-2">
          <div className="flex items-center justify-between">
            <span>Last Heartbeat:</span>
            <div className="flex items-center gap-1">
              {isRealTimeConnected && (
                <div className="w-1.5 h-1.5 bg-jorge-glow rounded-full animate-pulse" />
              )}
              <span className="text-gray-400">
                {lastActivity
                  ? new Date(lastActivity).toLocaleTimeString()
                  : new Date(bot.lastActivity).toLocaleTimeString()
                }
              </span>
            </div>
          </div>
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
        <Alert className="bg-jorge-glow/5 border-jorge-glow/20 text-jorge-glow h-10 py-0 flex items-center">
          <Wifi className="h-4 w-4 text-jorge-glow" />
          <AlertDescription className="text-jorge-glow/80 jorge-code text-[10px] flex items-center justify-between w-full ml-2">
            <div className="flex items-center gap-2">
              <span>Real-time monitoring active • Data age: {dataAge}s</span>
              {isAnyBotProcessing() && (
                <div className="flex items-center gap-1 text-jorge-glow">
                  <span className="w-1 h-1 bg-jorge-glow rounded-full animate-ping" />
                  <span>Bots processing</span>
                </div>
              )}
            </div>
            {isLoading && <Loader2 className="w-3 h-3 animate-spin" />}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className={cn("jorge-card group hover:bg-white/[0.02] transition-colors cursor-default", wsConnected && 'border-l-2 border-l-jorge-glow')}>
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <MessageSquare className="w-5 h-5 text-blue-500 group-hover:scale-110 transition-transform" />
              {wsConnected && isAnyBotProcessing() && (
                <div className="w-2 h-2 bg-jorge-glow rounded-full animate-pulse ml-2" />
              )}
            </div>
            <div className="jorge-stat group-hover:text-jorge-glow transition-colors">{totalConversations}</div>
            <div className="jorge-label mt-1">
              {wsConnected ? 'Active' : 'Daily'} Volume
            </div>
          </CardContent>
        </Card>

        <Card className={cn("jorge-card group hover:bg-white/[0.02] transition-colors cursor-default", wsConnected && 'border-l-2 border-l-jorge-glow')}>
          <CardContent className="p-4 text-center">
            <Target className="w-5 h-5 text-jorge-glow mx-auto mb-2 group-hover:scale-110 transition-transform" />
            <div className="jorge-stat group-hover:text-jorge-glow transition-colors">{totalLeadsQualified}</div>
            <div className="jorge-label mt-1">Total Qualified</div>
          </CardContent>
        </Card>

        <Card className={cn("jorge-card group hover:bg-white/[0.02] transition-colors cursor-default", wsConnected && 'border-l-2 border-l-jorge-glow')}>
          <CardContent className="p-4 text-center">
            <Zap className="w-5 h-5 text-purple-500 mx-auto mb-2 group-hover:scale-110 transition-transform" />
            <div className="jorge-stat group-hover:text-jorge-glow transition-colors">
              {Math.round(avgResponseTime)}<span className="text-xs font-normal text-gray-500 ml-0.5">ms</span>
            </div>
            <div className="jorge-label mt-1">Avg Latency</div>
          </CardContent>
        </Card>

        <Card className={cn("jorge-card group hover:bg-white/[0.02] transition-colors cursor-default", wsConnected && 'border-l-2 border-l-jorge-glow')}>
          <CardContent className="p-4 text-center">
            <div className="flex items-center justify-center mb-2">
              <Bot className="w-5 h-5 text-orange-500 group-hover:scale-110 transition-transform" />
            </div>
            <div className="jorge-stat group-hover:text-jorge-glow transition-colors">
              {displayBotCount}<span className="text-xs font-normal text-gray-500 ml-0.5">/ {bots.length}</span>
            </div>
            <div className="jorge-label mt-1">
              Agent Coverage
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
  const [activeLeadId, setActiveLeadId] = useState<string | null>(null)

  // WebSocket and real-time hooks
  const { connected: wsConnected, connectionState, reconnect } = useWebSocket()
  const { botStatus, getOverallHealth, lastUpdate: botLastUpdate } = useBotStatus()
  const { metrics, lastUpdate: metricsLastUpdate, dataAge } = useRealTimeMetrics()

  // Jorge-specific WebSocket integration
  useJorgeWebSocketHandlers()
  useJorgeLeadSubscription(activeLeadId)

  // Lead Bot WebSocket integration
  useLeadBotWebSocketHandlers()

  // Agent ecosystem store for real-time bot data
  const agents = useAgentEcosystemStore(state => state.agents)
  const platformActivities = useAgentEcosystemStore(state => state.platformActivities)
  const conciergeInsights = useAgentEcosystemStore(state => state.conciergeInsights)

  // Get Jorge-specific agent data
  const jorgeAgent = agents['jorge-seller-bot']

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
        console.log('🎯 Starting Jorge Seller Bot conversation...')

        // Use new Jorge Seller API with demo lead data
        const result = await jorgeSellerApi.startQualification({
          leadId: 'demo-lead-1',
          leadName: 'John Seller',
          phone: '+15125551234',
          propertyAddress: '123 Main St, Rancho Cucamonga TX',
          email: 'john.seller@example.com'
        })

        if (result.status === 'started') {
          setActiveChatBot(botId)
          setActiveChatConversation(result.conversationId)
          setActiveLeadId('demo-lead-1')

          console.log('✅ Jorge conversation started:', result.conversationId)
        } else {
          console.error('❌ Failed to start Jorge conversation:', result.message)
        }
      } catch (error) {
        console.error('Failed to start Jorge conversation:', error)
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
          <div className="text-lg font-medium text-gray-600">Loading Jorge&apos;s AI Platform...</div>
        </div>
      </div>
    )
  }
  
  return (
    <div className="space-y-8 animate-in fade-in duration-700">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <div className="w-8 h-8 bg-jorge-electric rounded flex items-center justify-center shadow-[0_0_15px_rgba(0,82,255,0.4)]">
              <Zap className="w-5 h-5 text-white fill-current" />
            </div>
            <h1 className="text-3xl font-bold text-white tracking-tighter">JORGE <span className="text-jorge-electric">BRAIN</span></h1>
          </div>
          <p className="jorge-label">
            Enterprise Real Estate Intelligence • <span className="text-gray-400">v4.0.2</span>
          </p>
        </div>
        
        <div className="flex items-center flex-wrap gap-2">
          {/* Status Badges */}
          <div className="flex bg-white/5 border border-white/10 rounded-full p-1 pr-3 items-center gap-2">
            <div className={cn(
              "w-2 h-2 rounded-full ml-2",
              wsConnected ? "bg-jorge-glow animate-pulse" : "bg-yellow-500"
            )} />
            <span className="text-[10px] jorge-code text-gray-300">
              {wsConnected ? "System Live" : "Polling Mode"}
            </span>
          </div>

          <Badge variant="outline" className={cn(
            "jorge-code text-[10px] border-none px-3 py-1",
            overallHealth === 'healthy' ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"
          )}>
            {overallHealth === 'healthy' ? "HEALTHY" : "CRITICAL"}
          </Badge>

          <Badge variant="outline" className="jorge-code text-[10px] bg-blue-500/10 text-blue-400 border-none px-3 py-1">
            PROD READY
          </Badge>
        </div>
      </div>
      
      {/* System Metrics */}
      <SystemMetrics />
      
      <Tabs defaultValue="dashboard" className="space-y-6">
        <TabsList className="bg-white/5 border border-white/10 p-1 rounded-xl h-11 w-full max-w-xl">
          <TabsTrigger value="dashboard" className="rounded-lg data-[state=active]:bg-jorge-electric data-[state=active]:text-white jorge-code text-[10px]">Command</TabsTrigger>
          <TabsTrigger value="chat" className="rounded-lg data-[state=active]:bg-jorge-electric data-[state=active]:text-white jorge-code text-[10px]">Interface</TabsTrigger>
          <TabsTrigger value="sequences" className="rounded-lg data-[state=active]:bg-jorge-electric data-[state=active]:text-white jorge-code text-[10px]">Sequences</TabsTrigger>
          <TabsTrigger value="analytics" className="rounded-lg data-[state=active]:bg-jorge-electric data-[state=active]:text-white jorge-code text-[10px]">Analytics</TabsTrigger>
        </TabsList>
        
        <TabsContent value="dashboard" className="space-y-6">
          {/* Real-time Connection Issues Alert */}
          {connectionState === 'error' && (
            <Alert className="mb-6 bg-red-500/10 border-red-500/20 text-red-400 animate-pulse">
              <WifiOff className="h-4 w-4 text-red-400" />
              <AlertDescription className="text-red-300 jorge-code text-[10px] flex items-center justify-between w-full ml-2">
                <div className="flex flex-col">
                  <span className="font-bold uppercase tracking-widest">Sync Interrupted</span>
                  <span>WebSocket connection lost. Falling back to 15s polling.</span>
                </div>
                <Button 
                  size="sm" 
                  variant="outline" 
                  onClick={reconnect}
                  className="h-7 text-[10px] border-red-500/30 hover:bg-red-500/20 text-red-300"
                >
                  Attempt Reconnect
                </Button>
              </AlertDescription>
            </Alert>
          )}

          {connectionState === 'connecting' && (
            <Alert className="mb-6 bg-yellow-500/10 border-yellow-500/20 text-yellow-400">
              <Loader2 className="h-4 w-4 animate-spin text-yellow-400" />
              <AlertDescription className="text-yellow-300 jorge-code text-[10px] ml-2">
                <span className="font-bold uppercase tracking-widest">Establishing Secure Link...</span>
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
          
          {/* Proactive Agentic Operations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <BotInsightsPanel />
            <VoiceCallMonitor />
          </div>

          {/* Jorge-Specific Concierge Insights */}
          {wsConnected && conciergeInsights.filter(insight => insight.botId === 'jorge-seller-bot').length > 0 && (
            <Card className="jorge-card border-none bg-white/5 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-jorge-glow" />
                  Jorge AI Insights
                  <Badge variant="outline" className="bg-jorge-glow/10 text-jorge-glow border-jorge-glow/20 text-[10px]">
                    Live
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {conciergeInsights
                    .filter(insight => insight.botId === 'jorge-seller-bot')
                    .slice(0, 3)
                    .map((insight) => (
                      <div
                        key={insight.id}
                        className={cn(
                          "p-3 rounded-lg border flex items-start gap-3 transition-all duration-300",
                          insight.severity === 'high'
                            ? 'bg-red-500/10 border-red-500/20'
                            : insight.severity === 'medium'
                            ? 'bg-orange-500/10 border-orange-500/20'
                            : 'bg-blue-500/10 border-blue-500/20'
                        )}
                      >
                        <div className={cn(
                          "w-2 h-2 rounded-full mt-2 animate-pulse",
                          insight.severity === 'high'
                            ? 'bg-red-400'
                            : insight.severity === 'medium'
                            ? 'bg-orange-400'
                            : 'bg-blue-400'
                        )} />
                        <div className="flex-1">
                          <div className="text-sm font-semibold text-white mb-1">
                            {insight.title}
                          </div>
                          <div className="text-xs text-gray-300 mb-2">
                            {insight.description}
                          </div>
                          <div className="flex items-center justify-between">
                            <div className="text-[10px] text-gray-500 jorge-code">
                              {new Date(insight.timestamp).toLocaleTimeString()}
                            </div>
                            <Button
                              size="sm"
                              className="h-6 text-[10px] bg-jorge-electric hover:bg-blue-600"
                            >
                              {insight.actionLabel}
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))
                  }
                </div>
              </CardContent>
            </Card>
          )}

          {/* Lead Bot Sequence Management */}
          {activeLeadId && (
            <Card className="jorge-card border-none bg-white/5 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-blue-500" />
                  Lead Bot Sequence - Lead {activeLeadId}
                  <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20 text-[10px]">
                    3-7-30 Day
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-2">
                    <LeadBotSequenceProgress
                      leadId={activeLeadId}
                      onSequenceUpdate={(status) => {
                        console.log('Sequence updated:', status);
                      }}
                    />
                  </div>
                  <div>
                    <LeadBotActionControls
                      leadId={activeLeadId}
                      onActionTriggered={(action, result) => {
                        console.log('Action triggered:', action, result);
                      }}
                    />
                  </div>
                </div>
                <div className="mt-6">
                  <LeadBotMessageTimeline
                    leadId={activeLeadId}
                    maxEvents={10}
                  />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Lead Bot Quick Start (when no active lead) */}
          {!activeLeadId && (
            <Card className="jorge-card border-none bg-white/5 backdrop-blur-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-blue-500" />
                  Lead Bot Management
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <Phone className="w-16 h-16 text-blue-400 mx-auto mb-4 opacity-50" />
                  <h3 className="text-lg font-medium text-white mb-2">No Active Lead Sequence</h3>
                  <p className="text-sm text-gray-400 mb-4">
                    Start a Jorge conversation to activate Lead Bot sequence monitoring
                  </p>
                  <Button
                    onClick={() => handleStartConversation('jorge-seller-bot')}
                    className="bg-blue-500 hover:bg-blue-600 text-white"
                  >
                    <MessageSquare className="w-4 h-4 mr-2" />
                    Start Jorge Conversation
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Special Features Section */}
          <Card className="jorge-card border-none bg-white/5 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Star className="w-5 h-5 text-yellow-500" />
                Jorge&apos;s Unique Features
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

        <TabsContent value="sequences">
          {activeLeadId ? (
            <div className="space-y-6">
              {/* Lead Sequence Header */}
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-white">Lead Sequence Management</h2>
                  <p className="text-gray-400 mt-1">
                    Monitoring 3-7-30 day sequence for Lead {activeLeadId}
                  </p>
                </div>
                <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20">
                  Active Sequence
                </Badge>
              </div>

              {/* Main Sequence Dashboard */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Sequence Progress - Takes 2 columns */}
                <div className="lg:col-span-2">
                  <LeadBotSequenceProgress
                    leadId={activeLeadId}
                    onSequenceUpdate={(status) => {
                      console.log('Sequence updated:', status);
                    }}
                    className="h-full"
                  />
                </div>

                {/* Action Controls */}
                <div>
                  <LeadBotActionControls
                    leadId={activeLeadId}
                    onActionTriggered={(action, result) => {
                      console.log('Action triggered:', action, result);
                    }}
                    className="h-full"
                  />
                </div>
              </div>

              {/* Message Timeline */}
              <LeadBotMessageTimeline
                leadId={activeLeadId}
                maxEvents={20}
              />
            </div>
          ) : (
            <Card className="h-[600px] flex items-center justify-center">
              <div className="text-center">
                <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">No Active Lead Sequence</h3>
                <p className="text-gray-500 mb-4">Start a Jorge conversation to begin lead sequence monitoring</p>
                <div className="space-y-3">
                  <Button onClick={() => handleStartConversation('jorge-seller-bot')}>
                    <MessageSquare className="w-4 h-4 mr-2" />
                    Start Jorge Seller Chat
                  </Button>
                  <div className="text-xs text-gray-500">
                    Or create a test sequence for demonstration purposes
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => {
                      setActiveLeadId('test-lead-demo');
                      console.log('Test lead sequence activated');
                    }}
                  >
                    <Calendar className="w-4 h-4 mr-2" />
                    Demo Lead Sequence
                  </Button>
                </div>
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

            {/* Heatmap of Opportunity */}
            <Card className="col-span-1 md:col-span-2">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-bold flex items-center gap-2">
                  <Map className="w-4 h-4 text-jorge-glow" />
                  Heatmap of Opportunity (Rancho Cucamonga, TX)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <HeatmapOfOpportunity />
              </CardContent>
            </Card>

            {/* Revenue Tracking (Commission Pipeline) */}
            <CommissionPipeline />

            {/* Lead Score Explainability (SHAP) */}
            <Card className="md:col-span-2 lg:col-span-1">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-bold flex items-center gap-2">
                  <Brain className="w-4 h-4 text-jorge-glow" />
                  Lead Score Explainability
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ShapExplainability 
                  baseScore={50} 
                  finalScore={88}
                  className="bg-transparent border-none p-0 backdrop-blur-none"
                />
              </CardContent>
            </Card>

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