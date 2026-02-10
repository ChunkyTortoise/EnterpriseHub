// Agent Ecosystem Dashboard - 43+ Agent Coordination Hub
// Professional interface for Jorge's complete AI agent ecosystem

'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Bot, Users, TrendingUp, BarChart3, MessageSquare, Calendar,
  Target, Zap, Brain, Eye, Settings, ChevronRight, Activity,
  Layers3, Network, Sparkles, Crown, Star, Clock, CheckCircle2,
  AlertTriangle, ArrowRight, Globe, Briefcase
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

// Agent Status Types
interface AgentStatus {
  id: string
  name: string
  type: 'primary' | 'secondary' | 'support' | 'intelligence'
  category: string
  status: 'active' | 'standby' | 'processing' | 'offline'
  currentTask?: string
  responseTime: number
  accuracy: number
  totalInteractions: number
  specialization: string
  coordination?: {
    connectedAgents: string[]
    activeHandoffs: number
  }
  data_provenance?: {
    source: string
    timestamp: string
    demo_mode: boolean
    note?: string
  }
}

import { useAgentEcosystemIntegration } from '@/hooks/useAgentEcosystemIntegration'
import { useAgentStats, useAgents, usePlatformActivities, useLoadingState, useAgentMetrics } from '@/store/agentEcosystemStore'

// Mock agent data will be replaced by real data
const mockAgentData: AgentStatus[] = [
  // Core Intelligence Agents (New)
  {
    id: 'claude-concierge',
    name: 'Claude Concierge Agent',
    type: 'primary',
    category: 'Platform Intelligence',
    status: 'active',
    currentTask: 'Coordinating multi-agent property analysis',
    responseTime: 1800,
    accuracy: 96,
    totalInteractions: 1247,
    specialization: 'Omnipresent AI Platform Guide',
    coordination: {
      connectedAgents: ['property-intelligence', 'journey-orchestrator', 'jorge-seller'],
      activeHandoffs: 3
    }
  },
  {
    id: 'property-intelligence',
    name: 'Property Intelligence Agent',
    type: 'primary',
    category: 'Property Analysis',
    status: 'processing',
    currentTask: 'Generating institutional-grade investment analysis',
    responseTime: 25000,
    accuracy: 94,
    totalInteractions: 892,
    specialization: 'Investment-Grade Property Analysis',
    coordination: {
      connectedAgents: ['claude-concierge', 'cma-generator', 'quant-agent'],
      activeHandoffs: 2
    }
  },
  {
    id: 'journey-orchestrator',
    name: 'Customer Journey Orchestrator',
    type: 'primary',
    category: 'Experience Coordination',
    status: 'active',
    currentTask: 'Managing 5 concurrent customer journeys',
    responseTime: 3200,
    accuracy: 91,
    totalInteractions: 2156,
    specialization: 'End-to-End Experience Coordination',
    coordination: {
      connectedAgents: ['jorge-seller', 'lead-bot', 'intent-decoder'],
      activeHandoffs: 5
    }
  },
  // Enhanced Track 1 Agents
  {
    id: 'adaptive-jorge',
    name: 'Adaptive Jorge Seller Bot',
    type: 'primary',
    category: 'Lead Qualification',
    status: 'active',
    currentTask: 'Real-time question adaptation (FRS: 78, PCS: 85)',
    responseTime: 2400,
    accuracy: 89,
    totalInteractions: 3421,
    specialization: 'Confrontational Seller Qualification',
    coordination: {
      connectedAgents: ['intent-decoder', 'lead-bot', 'journey-orchestrator'],
      activeHandoffs: 4
    }
  },
  {
    id: 'predictive-lead',
    name: 'Predictive Lead Bot',
    type: 'secondary',
    category: 'Lead Lifecycle',
    status: 'active',
    currentTask: 'ML-powered timing optimization for Day 7 calls',
    responseTime: 1200,
    accuracy: 92,
    totalInteractions: 2834,
    specialization: '3-7-30 Day Lifecycle Automation',
    coordination: {
      connectedAgents: ['adaptive-jorge', 'voice-intelligence'],
      activeHandoffs: 2
    }
  },
  {
    id: 'realtime-intent',
    name: 'Real-time Intent Decoder',
    type: 'intelligence',
    category: 'Behavioral Analysis',
    status: 'active',
    currentTask: 'Streaming analysis of 12 concurrent conversations',
    responseTime: 850,
    accuracy: 95,
    totalInteractions: 5679,
    specialization: 'FRS/PCS Behavioral Scoring',
    coordination: {
      connectedAgents: ['adaptive-jorge', 'claude-concierge', 'ml-analytics'],
      activeHandoffs: 8
    }
  },
  // Supporting Ecosystem
  {
    id: 'enhanced-orchestrator',
    name: 'Enhanced Bot Orchestrator',
    type: 'support',
    category: 'Coordination',
    status: 'active',
    currentTask: 'Managing 15 concurrent agent interactions',
    responseTime: 450,
    accuracy: 97,
    totalInteractions: 12456,
    specialization: 'Multi-Agent Coordination',
    coordination: {
      connectedAgents: ['all-agents'],
      activeHandoffs: 15
    }
  },
  // Add more existing agents for demo
  ...Array.from({ length: 36 }, (_, i) => ({
    id: `agent-${i + 7}`,
    name: `Specialized Agent ${i + 7}`,
    type: Math.random() > 0.5 ? 'secondary' : 'support' as 'secondary' | 'support',
    category: ['Analytics', 'Communication', 'Processing', 'Support'][i % 4],
    status: ['active', 'standby', 'processing'][Math.floor(Math.random() * 3)] as 'active' | 'standby' | 'processing',
    responseTime: Math.floor(Math.random() * 5000) + 500,
    accuracy: Math.floor(Math.random() * 20) + 80,
    totalInteractions: Math.floor(Math.random() * 10000) + 100,
    specialization: `Agent ${i + 7} Specialization`,
    coordination: {
      connectedAgents: [`agent-${(i + 1) % 43}`, `agent-${(i + 2) % 43}`],
      activeHandoffs: Math.floor(Math.random() * 3)
    }
  }))
]

function AgentStatusIndicator({ status }: { status: AgentStatus['status'] }) {
  const colors = {
    active: 'bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]',
    standby: 'bg-yellow-500 shadow-[0_0_10px_rgba(234,179,8,0.5)]',
    processing: 'bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)]',
    offline: 'bg-red-500'
  }

  return (
    <div className={cn(
      "w-2 h-2 rounded-full",
      colors[status],
      status === 'processing' && "animate-pulse"
    )} />
  )
}

function AgentTypeIcon({ type }: { type: AgentStatus['type'] }) {
  const icons = {
    primary: <Crown className="w-4 h-4 text-yellow-500" />,
    secondary: <Star className="w-4 h-4 text-blue-500" />,
    support: <Bot className="w-4 h-4 text-gray-400" />,
    intelligence: <Brain className="w-4 h-4 text-purple-500" />
  }

  return icons[type]
}

function AgentCard({ agent }: { agent: AgentStatus }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, y: -2 }}
      className="group"
    >
      <Card className="bg-white/5 border-white/10 hover:border-white/20 transition-all cursor-pointer">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AgentTypeIcon type={agent.type} />
              <AgentStatusIndicator status={agent.status} />
              <span className="text-xs text-gray-400 uppercase font-mono tracking-wider">{agent.category}</span>
            </div>
            <Badge variant="outline" className="text-[10px] bg-white/5 border-white/10">
              {agent.accuracy}% ACC
            </Badge>
          </div>

          <CardTitle className="text-white text-sm font-semibold leading-tight group-hover:text-blue-400 transition-colors">
            {agent.name}
          </CardTitle>

          <p className="text-xs text-gray-500 leading-relaxed">{agent.specialization}</p>
        </CardHeader>

        <CardContent className="pt-0 space-y-3">
          {agent.currentTask && (
            <div className="p-2 bg-black/20 border border-white/5 rounded-lg">
              <div className="flex items-center gap-1 mb-1">
                <Activity className="w-3 h-3 text-blue-500" />
                <span className="text-[10px] text-blue-400 uppercase font-mono tracking-wider">Active Task</span>
              </div>
              <p className="text-xs text-gray-300 leading-relaxed">{agent.currentTask}</p>
            </div>
          )}

          <div className="grid grid-cols-2 gap-2">
            <div className="bg-white/5 rounded-lg p-2">
              <div className="text-[10px] text-gray-500 uppercase font-mono">Response</div>
              <div className="text-xs font-bold text-white">{agent.responseTime}ms</div>
            </div>
            <div className="bg-white/5 rounded-lg p-2">
              <div className="text-[10px] text-gray-500 uppercase font-mono">Interactions</div>
              <div className="text-xs font-bold text-white">{agent.totalInteractions.toLocaleString()}</div>
            </div>
          </div>

          {agent.coordination && (
            <div className="border-t border-white/10 pt-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">Connected: {agent.coordination.connectedAgents.length}</span>
                <span className="text-blue-400">Handoffs: {agent.coordination.activeHandoffs}</span>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}

function EcosystemStats() {
  const agentStats = useAgentStats()
  const agents = useAgents()
  const agentList = Object.values(agents)

  const totalInteractions = agentList.reduce((sum, agent) => sum + agent.totalInteractions, 0)
  const avgAccuracy = agentList.length > 0
    ? Math.round(agentList.reduce((sum, agent) => sum + agent.accuracy, 0) / agentList.length)
    : 0
  const totalHandoffs = agentList.reduce((sum, agent) => sum + (agent.coordination?.activeHandoffs || 0), 0)

  const stats = [
    { label: 'Total Agents', value: agentStats.total.toString(), icon: <Bot className="w-5 h-5" />, color: 'text-blue-400' },
    { label: 'Active Now', value: agentStats.active.toString(), icon: <Zap className="w-5 h-5" />, color: 'text-green-400' },
    { label: 'Total Interactions', value: totalInteractions.toLocaleString(), icon: <MessageSquare className="w-5 h-5" />, color: 'text-purple-400' },
    { label: 'Avg Accuracy', value: `${avgAccuracy}%`, icon: <Target className="w-5 h-5" />, color: 'text-yellow-400' },
    { label: 'Active Handoffs', value: totalHandoffs.toString(), icon: <Network className="w-5 h-5" />, color: 'text-cyan-400' },
    { label: 'System Health', value: '97%', icon: <CheckCircle2 className="w-5 h-5" />, color: 'text-green-400' }
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {stats.map((stat, index) => (
        <motion.div
          key={index}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <Card className="bg-white/5 border-white/10 hover:border-white/20 transition-all">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className={cn("p-2 rounded-lg bg-black/20", stat.color)}>
                  {stat.icon}
                </div>
                <div>
                  <div className="text-xl font-bold text-white">{stat.value}</div>
                  <div className="text-xs text-gray-400">{stat.label}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  )
}

function CoordinationVisualization() {
  const agents = useAgents()
  const primaryAgents = Object.values(agents).filter(a => a.type === 'primary').slice(0, 6)
  const agentList = Object.values(agents)
  const totalHandoffs = agentList.reduce((sum, agent) => sum + (agent.coordination?.activeHandoffs || 0), 0)

  return (
    <Card className="bg-gradient-to-br from-white/5 to-white/[0.02] border-white/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <Network className="w-5 h-5 text-blue-500" />
          Real-time Agent Coordination
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative h-64 overflow-hidden">
          {/* Central Hub */}
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
              className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(59,130,246,0.3)]"
            >
              <Sparkles className="w-8 h-8 text-white" />
            </motion.div>
          </div>

          {/* Agent Nodes */}
          {primaryAgents.map((agent, index) => {
            const angle = (index * 60) * (Math.PI / 180)
            const radius = 90
            const x = Math.cos(angle) * radius
            const y = Math.sin(angle) * radius

            return (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0 }}
                animate={{
                  opacity: 1,
                  x: x,
                  y: y
                }}
                transition={{ delay: index * 0.2 }}
                className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
              >
                <div className="relative">
                  {/* Connection Line */}
                  <div
                    className="absolute w-px bg-gradient-to-r from-blue-500/50 to-transparent origin-left"
                    style={{
                      height: `${radius}px`,
                      transform: `rotate(${angle + 180}rad)`
                    }}
                  />

                  {/* Agent Node */}
                  <div className="w-12 h-12 bg-white/10 border border-white/20 rounded-full flex items-center justify-center backdrop-blur-sm">
                    <AgentTypeIcon type={agent.type} />
                  </div>

                  {/* Agent Label */}
                  <div className="absolute top-full mt-2 left-1/2 transform -translate-x-1/2 text-center">
                    <div className="text-xs font-semibold text-white whitespace-nowrap bg-black/50 px-2 py-1 rounded">
                      {agent.name.split(' ')[0]}
                    </div>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>

        <div className="mt-6 flex items-center justify-center gap-4 text-xs text-gray-400">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
            Live Coordination
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-purple-500 rounded-full" />
            {totalHandoffs} Active Handoffs
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

interface AgentEcosystemDashboardProps {
  className?: string
}

export function AgentEcosystemDashboard({ className = '' }: AgentEcosystemDashboardProps) {
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [searchTerm, setSearchTerm] = useState('')

  // Use real data from the store
  const agents = useAgents()
  const agentStats = useAgentStats()
  const agentMetrics = useAgentMetrics()
  const platformActivities = usePlatformActivities()
  const loadingState = useLoadingState()

  // Initialize the integration
  const integration = useAgentEcosystemIntegration({
    autoRefresh: true,
    enableRealTime: true,
    initializeOnMount: true,
  })

  const agentList = Object.values(agents)

  const filteredAgents = agentList.filter(agent => {
    const matchesCategory = selectedCategory === 'all' || agent.category.toLowerCase() === selectedCategory
    const matchesSearch = agent.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         agent.specialization.toLowerCase().includes(searchTerm.toLowerCase())
    return matchesCategory && matchesSearch
  })

  const categories = Array.from(new Set(agentList.map(a => a.category)))
  const totalHandoffs = agentList.reduce((sum, agent) => sum + (agent.coordination?.activeHandoffs || 0), 0)
  const provenance = agentMetrics?.data_provenance

  return (
    <div className={cn("w-full space-y-6", className)}>
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Agent Ecosystem Dashboard</h1>
          <p className="text-gray-400 text-sm">
            Jorge's complete 43+ agent ecosystem with real-time coordination and advanced intelligence
          </p>
          {provenance && (
            <p className="text-xs text-gray-500 mt-1">
              Data provenance: {provenance.source} • {provenance.timestamp}
              {provenance.note ? ` • ${provenance.note}` : ''}
            </p>
          )}
        </div>

        <div className="flex items-center gap-3">
          {provenance && (
            <Badge className={provenance.demo_mode ? "bg-red-500/10 text-red-300 border-red-500/20" : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"}>
              {provenance.demo_mode ? "DEMO DATA" : "SANDBOX DATA"}
            </Badge>
          )}
          <Badge className="bg-green-500/10 text-green-400 border-green-500/20">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            All Systems Operational
          </Badge>
          <Button size="sm" className="bg-blue-600 hover:bg-blue-500 text-white">
            <Settings className="w-4 h-4 mr-2" />
            Configure
          </Button>
        </div>
      </div>

      {/* Ecosystem Stats */}
      <EcosystemStats />

      {/* Coordination Visualization */}
      <CoordinationVisualization />

      {/* Agent Management */}
      <Tabs value={selectedCategory} onValueChange={setSelectedCategory} className="w-full">
        <TabsList className="bg-white/5 border border-white/10">
          <TabsTrigger value="all" className="data-[state=active]:bg-blue-600">All Agents</TabsTrigger>
          <TabsTrigger value="platform intelligence" className="data-[state=active]:bg-blue-600">Intelligence</TabsTrigger>
          <TabsTrigger value="lead qualification" className="data-[state=active]:bg-blue-600">Qualification</TabsTrigger>
          <TabsTrigger value="property analysis" className="data-[state=active]:bg-blue-600">Property</TabsTrigger>
          <TabsTrigger value="coordination" className="data-[state=active]:bg-blue-600">Coordination</TabsTrigger>
        </TabsList>

        <TabsContent value={selectedCategory} className="mt-6">
          {loadingState.agents ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">
              {Array.from({ length: 8 }).map((_, index) => (
                <div key={index} className="h-64 bg-white/5 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">
              <AnimatePresence mode="popLayout">
                {filteredAgents.map((agent) => (
                  <AgentCard key={agent.id} agent={agent} />
                ))}
              </AnimatePresence>
            </div>
          )}

          {!loadingState.agents && filteredAgents.length === 0 && (
            <div className="text-center py-12">
              <Bot className="w-12 h-12 text-gray-500 mx-auto mb-4" />
              <p className="text-gray-400">
                {agentList.length === 0 ? 'No agents available' : 'No agents found in this category'}
              </p>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Quick Actions */}
      <Card className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-white/10">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">Omnipresent AI Control Center</h3>
              <p className="text-gray-400 text-sm">
                Deploy Claude Concierge across the entire platform for omnipresent intelligence and coordination
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Button variant="outline" className="border-white/20 text-white">
                <Eye className="w-4 h-4 mr-2" />
                Monitor
              </Button>
              <Button className="bg-blue-600 hover:bg-blue-500 text-white">
                <ArrowRight className="w-4 h-4 mr-2" />
                Launch Concierge
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default AgentEcosystemDashboard
