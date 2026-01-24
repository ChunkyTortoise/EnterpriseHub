'use client'

import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Progress } from '@/components/ui/progress'
import {
  Bell,
  Settings,
  BarChart3,
  Users,
  Phone,
  MessageSquare,
  Brain,
  DollarSign,
  TrendingUp,
  Activity,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Clock,
  Monitor,
  Smartphone,
  Wifi,
  WifiOff
} from 'lucide-react'

// Import our dashboard components
import JorgeSellerDashboard from './dashboards/JorgeSellerDashboard'
import LeadBotDashboard from './dashboards/LeadBotDashboard'
import IntentDecoderDashboard from './dashboards/IntentDecoderDashboard'

interface SystemHealthData {
  overall_status: 'optimal' | 'good' | 'degraded' | 'critical'
  bots: {
    jorge_seller: {
      status: 'online' | 'offline' | 'degraded'
      conversations_active: number
      response_time_ms: number
      qualification_rate: number
    }
    lead_bot: {
      status: 'online' | 'offline' | 'degraded'
      sequences_active: number
      automation_health: number
      retell_ai_connected: boolean
    }
    intent_decoder: {
      status: 'online' | 'offline' | 'degraded'
      analyses_queued: number
      accuracy_rate: number
      processing_speed_ms: number
    }
  }
  cross_bot_coordination: {
    handoff_success_rate: number
    data_sync_status: 'synchronized' | 'syncing' | 'error'
    shared_context_accuracy: number
  }
  infrastructure: {
    redis_status: 'healthy' | 'degraded' | 'down'
    ghl_api_status: 'connected' | 'limited' | 'disconnected'
    claude_api_status: 'active' | 'limited' | 'down'
    database_performance: 'optimal' | 'slow' | 'critical'
  }
  real_time_metrics: {
    total_interactions_today: number
    revenue_pipeline: number
    leads_qualified_today: number
    system_uptime: number
  }
}

const JorgeCommandCenter: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview')
  const [isOnline, setIsOnline] = useState(true)
  const [lastUpdateTime, setLastUpdateTime] = useState<Date>(new Date())

  // System health monitoring with 2-second refresh
  const { data: healthData, isLoading, error, refetch } = useQuery({
    queryKey: ['jorge-command-center-health'],
    queryFn: async (): Promise<SystemHealthData> => {
      const response = await fetch('/api/dashboard/metrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metric_types: ['bot_performance', 'revenue_tracking'],
          real_time: true
        })
      })
      if (!response.ok) throw new Error('Failed to fetch system health')

      // Mock comprehensive system health data
      return {
        overall_status: 'optimal',
        bots: {
          jorge_seller: {
            status: 'online',
            conversations_active: 23,
            response_time_ms: 1847,
            qualification_rate: 67.2
          },
          lead_bot: {
            status: 'online',
            sequences_active: 45,
            automation_health: 89.2,
            retell_ai_connected: true
          },
          intent_decoder: {
            status: 'online',
            analyses_queued: 3,
            accuracy_rate: 95.3,
            processing_speed_ms: 42.1
          }
        },
        cross_bot_coordination: {
          handoff_success_rate: 94.7,
          data_sync_status: 'synchronized',
          shared_context_accuracy: 97.8
        },
        infrastructure: {
          redis_status: 'healthy',
          ghl_api_status: 'connected',
          claude_api_status: 'active',
          database_performance: 'optimal'
        },
        real_time_metrics: {
          total_interactions_today: 89,
          revenue_pipeline: 847500,
          leads_qualified_today: 18,
          system_uptime: 99.7
        }
      }
    },
    refetchInterval: 2000, // 2-second real-time updates for system health
    staleTime: 0
  })

  // Network status monitoring
  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // Update timestamp on data refresh
  useEffect(() => {
    if (healthData && !isLoading) {
      setLastUpdateTime(new Date())
    }
  }, [healthData, isLoading])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'optimal':
      case 'online':
      case 'healthy':
      case 'active':
      case 'connected': return 'text-green-600 bg-green-100'
      case 'good':
      case 'degraded':
      case 'limited':
      case 'slow': return 'text-yellow-600 bg-yellow-100'
      case 'critical':
      case 'offline':
      case 'down':
      case 'disconnected': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  if (isLoading && !healthData) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[...Array(6)].map((_, i) => (
              <Card key={i} className="animate-pulse">
                <CardContent className="p-6">
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-8 bg-gray-200 rounded w-1/2"></div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation Bar */}
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Jorge Branding */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">J</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Jorge's AI Command Center</h1>
                <p className="text-sm text-gray-500">Real Estate Bot Ecosystem</p>
              </div>
            </div>

            {/* Network Status Indicator */}
            <div className="flex items-center space-x-2">
              {isOnline ? (
                <Wifi className="h-5 w-5 text-green-500" />
              ) : (
                <WifiOff className="h-5 w-5 text-red-500" />
              )}
              <span className="text-sm text-gray-600">
                {isOnline ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>

          {/* System Status & Controls */}
          <div className="flex items-center space-x-4">
            {/* Overall System Status */}
            <Badge className={getStatusColor(healthData?.overall_status || 'unknown')}>
              {healthData?.overall_status?.toUpperCase() || 'LOADING'}
            </Badge>

            {/* Last Update Time */}
            <div className="text-sm text-gray-500">
              <Clock className="h-4 w-4 inline mr-1" />
              Updated {lastUpdateTime.toLocaleTimeString()}
            </div>

            {/* Quick Actions */}
            <Button variant="outline" size="sm">
              <Bell className="h-4 w-4 mr-2" />
              Alerts
            </Button>
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </Button>

            {/* Mobile Responsive Toggle */}
            <div className="md:hidden">
              <Button variant="ghost" size="sm">
                <Monitor className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="p-6">
        <div className="max-w-7xl mx-auto">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            {/* Tab Navigation */}
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview" className="flex items-center space-x-2">
                <BarChart3 className="h-4 w-4" />
                <span>Overview</span>
              </TabsTrigger>
              <TabsTrigger value="seller-bot" className="flex items-center space-x-2">
                <Users className="h-4 w-4" />
                <span>Jorge Seller</span>
              </TabsTrigger>
              <TabsTrigger value="lead-bot" className="flex items-center space-x-2">
                <Phone className="h-4 w-4" />
                <span>Lead Bot</span>
              </TabsTrigger>
              <TabsTrigger value="intent-decoder" className="flex items-center space-x-2">
                <Brain className="h-4 w-4" />
                <span>ML Analytics</span>
              </TabsTrigger>
            </TabsList>

            {/* Overview Tab - Unified Dashboard */}
            <TabsContent value="overview" className="space-y-6">
              {/* Key Performance Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Total Interactions Today</p>
                        <p className="text-2xl font-bold text-blue-600">
                          {healthData?.real_time_metrics.total_interactions_today || 0}
                        </p>
                      </div>
                      <Activity className="h-8 w-8 text-blue-500" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Revenue Pipeline</p>
                        <p className="text-2xl font-bold text-green-600">
                          ${(healthData?.real_time_metrics.revenue_pipeline || 0).toLocaleString()}
                        </p>
                      </div>
                      <DollarSign className="h-8 w-8 text-green-500" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Qualified Leads Today</p>
                        <p className="text-2xl font-bold text-purple-600">
                          {healthData?.real_time_metrics.leads_qualified_today || 0}
                        </p>
                      </div>
                      <CheckCircle2 className="h-8 w-8 text-purple-500" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-600">System Uptime</p>
                        <p className="text-2xl font-bold text-orange-600">
                          {healthData?.real_time_metrics.system_uptime || 0}%
                        </p>
                      </div>
                      <TrendingUp className="h-8 w-8 text-orange-500" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Bot Status Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Jorge Seller Bot Status */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Users className="h-5 w-5 text-blue-500" />
                      <span>Jorge Seller Bot</span>
                      <Badge className={getStatusColor(healthData?.bots.jorge_seller.status || 'unknown')}>
                        {healthData?.bots.jorge_seller.status?.toUpperCase() || 'UNKNOWN'}
                      </Badge>
                    </CardTitle>
                    <CardDescription>Confrontational Q1-Q4 qualification system</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Active Conversations</span>
                        <span className="text-sm font-bold">
                          {healthData?.bots.jorge_seller.conversations_active || 0}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Qualification Rate</span>
                        <span className="text-sm font-bold text-green-600">
                          {healthData?.bots.jorge_seller.qualification_rate || 0}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Response Time</span>
                        <span className="text-sm font-bold">
                          {healthData?.bots.jorge_seller.response_time_ms || 0}ms
                        </span>
                      </div>
                      <Progress value={healthData?.bots.jorge_seller.qualification_rate || 0} className="mt-2" />
                    </div>
                  </CardContent>
                </Card>

                {/* Lead Bot Status */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Phone className="h-5 w-5 text-green-500" />
                      <span>Lead Bot</span>
                      <Badge className={getStatusColor(healthData?.bots.lead_bot.status || 'unknown')}>
                        {healthData?.bots.lead_bot.status?.toUpperCase() || 'UNKNOWN'}
                      </Badge>
                    </CardTitle>
                    <CardDescription>3-7-30 day automation with Retell AI</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Active Sequences</span>
                        <span className="text-sm font-bold">
                          {healthData?.bots.lead_bot.sequences_active || 0}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Automation Health</span>
                        <span className="text-sm font-bold text-green-600">
                          {healthData?.bots.lead_bot.automation_health || 0}%
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium">Retell AI</span>
                        <Badge variant={healthData?.bots.lead_bot.retell_ai_connected ? 'secondary' : 'destructive'}>
                          {healthData?.bots.lead_bot.retell_ai_connected ? 'Connected' : 'Disconnected'}
                        </Badge>
                      </div>
                      <Progress value={healthData?.bots.lead_bot.automation_health || 0} className="mt-2" />
                    </div>
                  </CardContent>
                </Card>

                {/* Intent Decoder Status */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                      <Brain className="h-5 w-5 text-purple-500" />
                      <span>Intent Decoder</span>
                      <Badge className={getStatusColor(healthData?.bots.intent_decoder.status || 'unknown')}>
                        {healthData?.bots.intent_decoder.status?.toUpperCase() || 'UNKNOWN'}
                      </Badge>
                    </CardTitle>
                    <CardDescription>28-feature ML pipeline (95% accuracy)</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Queue Depth</span>
                        <span className="text-sm font-bold">
                          {healthData?.bots.intent_decoder.analyses_queued || 0}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Accuracy Rate</span>
                        <span className="text-sm font-bold text-green-600">
                          {healthData?.bots.intent_decoder.accuracy_rate || 0}%
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">Processing Speed</span>
                        <span className="text-sm font-bold">
                          {healthData?.bots.intent_decoder.processing_speed_ms || 0}ms
                        </span>
                      </div>
                      <Progress value={healthData?.bots.intent_decoder.accuracy_rate || 0} className="mt-2" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Cross-Bot Coordination & Infrastructure Status */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Cross-Bot Coordination</CardTitle>
                    <CardDescription>Inter-bot communication and data synchronization</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Handoff Success Rate</span>
                        <span className="text-sm font-bold text-green-600">
                          {healthData?.cross_bot_coordination.handoff_success_rate || 0}%
                        </span>
                      </div>
                      <Progress value={healthData?.cross_bot_coordination.handoff_success_rate || 0} />

                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Data Sync Status</span>
                        <Badge className={getStatusColor(healthData?.cross_bot_coordination.data_sync_status || 'unknown')}>
                          {healthData?.cross_bot_coordination.data_sync_status || 'Unknown'}
                        </Badge>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Context Accuracy</span>
                        <span className="text-sm font-bold text-blue-600">
                          {healthData?.cross_bot_coordination.shared_context_accuracy || 0}%
                        </span>
                      </div>
                      <Progress value={healthData?.cross_bot_coordination.shared_context_accuracy || 0} />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Infrastructure Health</CardTitle>
                    <CardDescription>Backend services and API connections</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center p-3 rounded-lg bg-gray-50">
                        <p className="text-xs font-medium text-gray-600">Redis Cache</p>
                        <Badge className={getStatusColor(healthData?.infrastructure.redis_status || 'unknown')} size="sm">
                          {healthData?.infrastructure.redis_status || 'Unknown'}
                        </Badge>
                      </div>
                      <div className="text-center p-3 rounded-lg bg-gray-50">
                        <p className="text-xs font-medium text-gray-600">GHL API</p>
                        <Badge className={getStatusColor(healthData?.infrastructure.ghl_api_status || 'unknown')} size="sm">
                          {healthData?.infrastructure.ghl_api_status || 'Unknown'}
                        </Badge>
                      </div>
                      <div className="text-center p-3 rounded-lg bg-gray-50">
                        <p className="text-xs font-medium text-gray-600">Claude API</p>
                        <Badge className={getStatusColor(healthData?.infrastructure.claude_api_status || 'unknown')} size="sm">
                          {healthData?.infrastructure.claude_api_status || 'Unknown'}
                        </Badge>
                      </div>
                      <div className="text-center p-3 rounded-lg bg-gray-50">
                        <p className="text-xs font-medium text-gray-600">Database</p>
                        <Badge className={getStatusColor(healthData?.infrastructure.database_performance || 'unknown')} size="sm">
                          {healthData?.infrastructure.database_performance || 'Unknown'}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            {/* Individual Dashboard Tabs */}
            <TabsContent value="seller-bot">
              <JorgeSellerDashboard />
            </TabsContent>

            <TabsContent value="lead-bot">
              <LeadBotDashboard />
            </TabsContent>

            <TabsContent value="intent-decoder">
              <IntentDecoderDashboard />
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  )
}

export default JorgeCommandCenter