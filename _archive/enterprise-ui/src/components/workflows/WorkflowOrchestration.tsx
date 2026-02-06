/**
 * Workflow Orchestration Dashboard
 *
 * Comprehensive multi-bot coordination interface for Jorge's Real Estate Platform
 * Manages workflows across Jorge Seller Bot, Lead Bot, and Intent Decoder
 */

'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Activity,
  ArrowRight,
  Bot,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Users,
  MessageSquare,
  Phone,
  Zap,
  TrendingUp,
  RefreshCw,
  ExternalLink,
  Workflow,
  GitMerge,
  Timer
} from 'lucide-react'
import { useJorgeWorkflow, useMultiBotCoordination, useRealTimeCoordination } from '@/store/useChatStore'

interface WorkflowCardProps {
  workflow: any
  onViewDetails: (workflowId: string) => void
  onEscalate: (workflowId: string) => void
}

function WorkflowCard({ workflow, onViewDetails, onEscalate }: WorkflowCardProps) {
  const getStageColor = (stage: string) => {
    switch (stage) {
      case 'qualification': return 'bg-blue-100 text-blue-800'
      case 'automation': return 'bg-purple-100 text-purple-800'
      case 'analysis': return 'bg-green-100 text-green-800'
      case 'handoff': return 'bg-yellow-100 text-yellow-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'escalated': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'urgent': return <AlertTriangle className="w-4 h-4 text-red-500" />
      case 'high': return <TrendingUp className="w-4 h-4 text-orange-500" />
      case 'medium': return <Clock className="w-4 h-4 text-blue-500" />
      case 'low': return <Timer className="w-4 h-4 text-gray-500" />
      default: return <Clock className="w-4 h-4 text-gray-500" />
    }
  }

  const getBotIcon = (botType: string) => {
    switch (botType) {
      case 'jorge-seller': return <MessageSquare className="w-4 h-4 text-blue-600" />
      case 'lead-bot': return <Phone className="w-4 h-4 text-green-600" />
      case 'intent-decoder': return <Zap className="w-4 h-4 text-purple-600" />
      default: return <Bot className="w-4 h-4 text-gray-600" />
    }
  }

  return (
    <Card className="hover:shadow-lg transition-all duration-200">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getBotIcon(workflow.activeBot)}
            <CardTitle className="text-sm font-medium">
              {workflow.contactId.slice(0, 8)}...
            </CardTitle>
            {getPriorityIcon(workflow.priority)}
          </div>
          <Badge className={getStageColor(workflow.stage)}>
            {workflow.stage}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Active Bot and Progress */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">Active Bot:</span>
          <div className="flex items-center gap-1">
            {getBotIcon(workflow.activeBot)}
            <span className="text-sm font-medium">{workflow.activeBot}</span>
          </div>
        </div>

        {/* Handoff Queue */}
        {workflow.handoffQueue?.length > 0 && (
          <div className="flex items-center gap-2 p-2 bg-yellow-50 rounded">
            <GitMerge className="w-4 h-4 text-yellow-600" />
            <span className="text-sm text-yellow-800">
              {workflow.handoffQueue.length} pending handoff(s)
            </span>
          </div>
        )}

        {/* Timing Information */}
        <div className="flex justify-between text-xs text-gray-500">
          <span>Created: {new Date(workflow.createdAt).toLocaleTimeString()}</span>
          <span>Updated: {new Date(workflow.lastUpdate).toLocaleTimeString()}</span>
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => onViewDetails(workflow.id)}
            className="flex-1"
          >
            <ExternalLink className="w-3 h-3 mr-1" />
            Details
          </Button>
          {workflow.stage !== 'escalated' && workflow.stage !== 'completed' && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onEscalate(workflow.id)}
              className="text-red-600 border-red-200 hover:bg-red-50"
            >
              <AlertTriangle className="w-3 h-3 mr-1" />
              Escalate
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

function BotCoordinationMetrics() {
  const { metrics } = useMultiBotCoordination()
  const { connected, lastUpdate } = useRealTimeCoordination()

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card>
        <CardContent className="p-4 text-center">
          <Workflow className="w-6 h-6 text-blue-600 mx-auto mb-2" />
          <div className="text-2xl font-bold">{metrics.totalWorkflows || 0}</div>
          <div className="text-sm text-gray-600">Total Workflows</div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4 text-center">
          <Activity className="w-6 h-6 text-green-600 mx-auto mb-2" />
          <div className="text-2xl font-bold">{metrics.activeWorkflows || 0}</div>
          <div className="text-sm text-gray-600">Active Workflows</div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4 text-center">
          <GitMerge className="w-6 h-6 text-purple-600 mx-auto mb-2" />
          <div className="text-2xl font-bold">{metrics.handoffsToday || 0}</div>
          <div className="text-sm text-gray-600">Handoffs Today</div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4 text-center">
          <CheckCircle2 className="w-6 h-6 text-green-600 mx-auto mb-2" />
          <div className="text-2xl font-bold">{metrics.completedWorkflows || 0}</div>
          <div className="text-sm text-gray-600">Completed</div>
        </CardContent>
      </Card>
    </div>
  )
}

function BotStatusPanel() {
  const { botStatuses } = useMultiBotCoordination()
  const bots = Object.values(botStatuses)

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {bots.map((bot) => (
        <Card key={bot.id} className="border-l-4 border-l-blue-500">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm">{bot.name}</CardTitle>
              <Badge
                variant={bot.status === 'online' ? 'secondary' : 'outline'}
                className={
                  bot.status === 'online'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-gray-100 text-gray-600'
                }
              >
                {bot.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Conversations:</span>
                <span className="font-medium">{bot.conversationsToday}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Response Time:</span>
                <span className="font-medium">{bot.responseTimeMs}ms</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Success Rate:</span>
                <span className="font-medium">
                  {bot.performanceMetrics?.successRate || 0}%
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

function CrossBotMessages() {
  const { botMessages } = useMultiBotCoordination()
  const recentMessages = botMessages.slice(-10) // Last 10 messages

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5" />
          Cross-Bot Communication
        </CardTitle>
      </CardHeader>
      <CardContent>
        {recentMessages.length === 0 ? (
          <div className="text-center text-gray-500 py-4">
            No cross-bot messages yet
          </div>
        ) : (
          <div className="space-y-2">
            {recentMessages.map((message, index) => (
              <div key={index} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                <div className="flex items-center gap-2">
                  {message.fromBot === 'jorge-seller' && <MessageSquare className="w-4 h-4 text-blue-600" />}
                  {message.fromBot === 'lead-bot' && <Phone className="w-4 h-4 text-green-600" />}
                  {message.fromBot === 'intent-decoder' && <Zap className="w-4 h-4 text-purple-600" />}
                  <span className="text-sm font-medium">{message.fromBot}</span>
                </div>

                <ArrowRight className="w-3 h-3 text-gray-400" />

                <div className="flex items-center gap-2">
                  {message.toBot === 'jorge-seller' && <MessageSquare className="w-4 h-4 text-blue-600" />}
                  {message.toBot === 'lead-bot' && <Phone className="w-4 h-4 text-green-600" />}
                  {message.toBot === 'intent-decoder' && <Zap className="w-4 h-4 text-purple-600" />}
                  <span className="text-sm font-medium">{message.toBot}</span>
                </div>

                <Badge variant="outline" className="text-xs">
                  {message.messageType}
                </Badge>

                <span className="text-xs text-gray-500 ml-auto">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default function WorkflowOrchestration() {
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null)
  const { workflows, activeWorkflow, escalateToHuman } = useJorgeWorkflow()
  const { startJorgeSellerQualification, triggerLeadAutomation } = useMultiBotCoordination()
  const { connected, connect, disconnect } = useRealTimeCoordination()

  const workflowList = Object.values(workflows)
  const activeWorkflows = workflowList.filter(w => w.stage !== 'completed' && w.stage !== 'escalated')
  const completedWorkflows = workflowList.filter(w => w.stage === 'completed')
  const escalatedWorkflows = workflowList.filter(w => w.stage === 'escalated')

  const handleViewDetails = (workflowId: string) => {
    setSelectedWorkflow(workflowId)
  }

  const handleEscalate = async (workflowId: string) => {
    try {
      await escalateToHuman(workflowId, 'Manual escalation from workflow dashboard')
      console.log('Workflow escalated successfully')
    } catch (error) {
      console.error('Failed to escalate workflow:', error)
    }
  }

  const handleStartNewWorkflow = async (botType: 'jorge-seller' | 'lead-bot') => {
    const contactId = `contact_${Date.now()}`
    const locationId = 'loc_default'

    try {
      if (botType === 'jorge-seller') {
        await startJorgeSellerQualification(contactId, locationId)
      } else if (botType === 'lead-bot') {
        await triggerLeadAutomation(contactId, 3) // Start with Day 3 sequence
      }
      console.log(`${botType} workflow started successfully`)
    } catch (error) {
      console.error('Failed to start workflow:', error)
    }
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header with Real-time Status */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Workflow Orchestration</h1>
          <p className="text-gray-600 mt-1">
            Multi-bot coordination dashboard for Jorge's Real Estate Platform
          </p>
        </div>

        <div className="flex items-center gap-3">
          {connected ? (
            <Badge variant="secondary" className="bg-green-100 text-green-800">
              <Activity className="w-3 h-3 mr-1 animate-pulse" />
              Real-time Connected
            </Badge>
          ) : (
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-yellow-50 text-yellow-700">
                <RefreshCw className="w-3 h-3 mr-1" />
                Polling Mode
              </Badge>
              <Button size="sm" variant="outline" onClick={connect}>
                Connect
              </Button>
            </div>
          )}

          <Button onClick={() => handleStartNewWorkflow('jorge-seller')}>
            Start Jorge Workflow
          </Button>
        </div>
      </div>

      {/* Connection Status Alert */}
      {!connected && (
        <Alert className="bg-yellow-50 border-yellow-200">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <AlertDescription className="text-yellow-800">
            Real-time coordination is offline. Bot coordination is operating in polling mode.
            <Button
              size="sm"
              variant="ghost"
              className="ml-2 text-yellow-700 underline"
              onClick={connect}
            >
              Reconnect
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Metrics Overview */}
      <BotCoordinationMetrics />

      <Tabs defaultValue="active" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="active">
            Active Workflows ({activeWorkflows.length})
          </TabsTrigger>
          <TabsTrigger value="completed">
            Completed ({completedWorkflows.length})
          </TabsTrigger>
          <TabsTrigger value="escalated">
            Escalated ({escalatedWorkflows.length})
          </TabsTrigger>
          <TabsTrigger value="coordination">
            Bot Coordination
          </TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4">
          {activeWorkflows.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <Workflow className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">No Active Workflows</h3>
                <p className="text-gray-500 mb-4">Start a new workflow to begin bot coordination</p>
                <div className="flex gap-2 justify-center">
                  <Button onClick={() => handleStartNewWorkflow('jorge-seller')}>
                    Jorge Seller Qualification
                  </Button>
                  <Button variant="outline" onClick={() => handleStartNewWorkflow('lead-bot')}>
                    Lead Bot Automation
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {activeWorkflows.map((workflow) => (
                <WorkflowCard
                  key={workflow.id}
                  workflow={workflow}
                  onViewDetails={handleViewDetails}
                  onEscalate={handleEscalate}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="completed" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {completedWorkflows.map((workflow) => (
              <WorkflowCard
                key={workflow.id}
                workflow={workflow}
                onViewDetails={handleViewDetails}
                onEscalate={handleEscalate}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="escalated" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {escalatedWorkflows.map((workflow) => (
              <WorkflowCard
                key={workflow.id}
                workflow={workflow}
                onViewDetails={handleViewDetails}
                onEscalate={handleEscalate}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="coordination" className="space-y-6">
          {/* Bot Status Panel */}
          <BotStatusPanel />

          {/* Cross-Bot Communication */}
          <CrossBotMessages />
        </TabsContent>
      </Tabs>
    </div>
  )
}