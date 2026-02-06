// Customer Journey Orchestrator - End-to-End Experience Coordinator
// Professional interface for managing complete customer journeys across all specialized agents

'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Route, Users, Clock, Target, CheckCircle2, ArrowRight, Play,
  Pause, SkipForward, User, Bot, Phone, Mail, Calendar, FileText,
  TrendingUp, AlertTriangle, Zap, Brain, Star, Settings, Eye,
  Activity, MessageSquare, Building, DollarSign, Award, Crown
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'

// Journey Types
type JourneyType = 'FIRST_TIME_BUYER' | 'INVESTOR' | 'SELLER' | 'COMMERCIAL'
type JourneyStatus = 'active' | 'paused' | 'completed' | 'abandoned'
type StepStatus = 'pending' | 'active' | 'completed' | 'skipped' | 'failed'
type AgentHandoffType = 'SEQUENTIAL' | 'COLLABORATIVE' | 'ESCALATION'

interface JourneyStep {
  id: string
  name: string
  description: string
  agentId: string
  agentName: string
  estimatedDuration: number
  status: StepStatus
  startTime?: string
  endTime?: string
  output?: any
  nextSteps: string[]
  handoffType?: AgentHandoffType
}

interface CustomerJourney {
  id: string
  customerId: string
  customerName: string
  type: JourneyType
  status: JourneyStatus
  priority: 'low' | 'medium' | 'high' | 'urgent'
  currentStep: number
  totalSteps: number
  completionPercentage: number
  startTime: string
  estimatedCompletion?: string
  steps: JourneyStep[]
  analytics: {
    avgResponseTime: number
    customerSatisfaction: number
    handoffEfficiency: number
    touchpoints: number
  }
  context: {
    budget?: number
    timeframe?: string
    preferences?: string[]
    requirements?: string[]
  }
}

// Mock journey templates
const journeyTemplates: Record<JourneyType, Partial<JourneyStep>[]> = {
  FIRST_TIME_BUYER: [
    { name: 'Initial Consultation', agentId: 'claude-concierge', agentName: 'Claude Concierge', estimatedDuration: 30 },
    { name: 'Financial Pre-qualification', agentId: 'financial-agent', agentName: 'Financial Advisor Bot', estimatedDuration: 45 },
    { name: 'Preference Discovery', agentId: 'preference-agent', agentName: 'Preference Discovery Agent', estimatedDuration: 20 },
    { name: 'Property Search Setup', agentId: 'search-agent', agentName: 'Property Search Bot', estimatedDuration: 15 },
    { name: 'Market Education', agentId: 'education-agent', agentName: 'Market Education Bot', estimatedDuration: 60 },
    { name: 'Property Recommendations', agentId: 'matching-agent', agentName: 'Property Matching Agent', estimatedDuration: 30 },
    { name: 'Showing Coordination', agentId: 'showing-agent', agentName: 'Showing Coordinator Bot', estimatedDuration: 120 }
  ],
  INVESTOR: [
    { name: 'Investment Strategy Analysis', agentId: 'property-intelligence', agentName: 'Property Intelligence Agent', estimatedDuration: 45 },
    { name: 'Portfolio Assessment', agentId: 'portfolio-agent', agentName: 'Portfolio Analysis Bot', estimatedDuration: 60 },
    { name: 'Market Analysis', agentId: 'market-agent', agentName: 'Market Intelligence Bot', estimatedDuration: 30 },
    { name: 'ROI Calculations', agentId: 'roi-agent', agentName: 'ROI Calculator Agent', estimatedDuration: 25 },
    { name: 'Risk Assessment', agentId: 'risk-agent', agentName: 'Risk Analysis Bot', estimatedDuration: 40 },
    { name: 'Property Sourcing', agentId: 'sourcing-agent', agentName: 'Property Sourcing Agent', estimatedDuration: 90 }
  ],
  SELLER: [
    { name: 'Property Assessment', agentId: 'adaptive-jorge', agentName: 'Jorge Seller Bot', estimatedDuration: 30 },
    { name: 'Market Positioning', agentId: 'positioning-agent', agentName: 'Market Positioning Bot', estimatedDuration: 45 },
    { name: 'Pricing Strategy', agentId: 'pricing-agent', agentName: 'Pricing Strategy Agent', estimatedDuration: 20 },
    { name: 'Marketing Plan', agentId: 'marketing-agent', agentName: 'Marketing Automation Bot', estimatedDuration: 60 },
    { name: 'Listing Preparation', agentId: 'listing-agent', agentName: 'Listing Optimization Agent', estimatedDuration: 40 },
    { name: 'Showing Management', agentId: 'showing-agent', agentName: 'Showing Coordinator Bot', estimatedDuration: 120 }
  ],
  COMMERCIAL: [
    { name: 'Commercial Analysis', agentId: 'commercial-agent', agentName: 'Commercial Analysis Bot', estimatedDuration: 90 },
    { name: 'Market Research', agentId: 'research-agent', agentName: 'Commercial Research Agent', estimatedDuration: 120 },
    { name: 'Financial Modeling', agentId: 'modeling-agent', agentName: 'Financial Modeling Bot', estimatedDuration: 60 },
    { name: 'Due Diligence', agentId: 'diligence-agent', agentName: 'Due Diligence Agent', estimatedDuration: 180 }
  ]
}

// Mock active journeys
const mockActiveJourneys: CustomerJourney[] = [
  {
    id: 'journey-001',
    customerId: 'cust-001',
    customerName: 'Sarah Johnson',
    type: 'FIRST_TIME_BUYER',
    status: 'active',
    priority: 'high',
    currentStep: 3,
    totalSteps: 7,
    completionPercentage: 43,
    startTime: '2026-01-24T09:00:00Z',
    estimatedCompletion: '2026-01-24T14:30:00Z',
    steps: journeyTemplates.FIRST_TIME_BUYER.map((template, index) => ({
      id: `step-${index}`,
      ...template,
      status: index < 2 ? 'completed' : index === 2 ? 'active' : 'pending',
      handoffType: 'SEQUENTIAL'
    })) as JourneyStep[],
    analytics: {
      avgResponseTime: 2400,
      customerSatisfaction: 94,
      handoffEfficiency: 87,
      touchpoints: 12
    },
    context: {
      budget: 450000,
      timeframe: '3 months',
      preferences: ['Modern', '3+ bedrooms', 'Good schools'],
      requirements: ['Pre-approval completed', 'First-time buyer incentives']
    }
  },
  {
    id: 'journey-002',
    customerId: 'cust-002',
    customerName: 'Michael Chen',
    type: 'INVESTOR',
    status: 'active',
    priority: 'urgent',
    currentStep: 2,
    totalSteps: 6,
    completionPercentage: 33,
    startTime: '2026-01-24T10:15:00Z',
    estimatedCompletion: '2026-01-24T16:45:00Z',
    steps: journeyTemplates.INVESTOR.map((template, index) => ({
      id: `step-${index}`,
      ...template,
      status: index < 1 ? 'completed' : index === 1 ? 'active' : 'pending',
      handoffType: 'COLLABORATIVE'
    })) as JourneyStep[],
    analytics: {
      avgResponseTime: 1800,
      customerSatisfaction: 91,
      handoffEfficiency: 92,
      touchpoints: 8
    },
    context: {
      budget: 750000,
      timeframe: 'ASAP',
      preferences: ['Rental income', 'Appreciation potential'],
      requirements: ['Portfolio diversification', 'Cash flow positive']
    }
  },
  {
    id: 'journey-003',
    customerId: 'cust-003',
    customerName: 'Jennifer Davis',
    type: 'SELLER',
    status: 'active',
    priority: 'medium',
    currentStep: 4,
    totalSteps: 6,
    completionPercentage: 67,
    startTime: '2026-01-24T08:30:00Z',
    estimatedCompletion: '2026-01-24T15:00:00Z',
    steps: journeyTemplates.SELLER.map((template, index) => ({
      id: `step-${index}`,
      ...template,
      status: index < 3 ? 'completed' : index === 3 ? 'active' : 'pending',
      handoffType: 'SEQUENTIAL'
    })) as JourneyStep[],
    analytics: {
      avgResponseTime: 3200,
      customerSatisfaction: 88,
      handoffEfficiency: 85,
      touchpoints: 15
    },
    context: {
      timeframe: '6 weeks',
      preferences: ['Quick sale', 'Maximize price'],
      requirements: ['Professional staging', 'Marketing package']
    }
  }
]

function JourneyTypeIcon({ type }: { type: JourneyType }) {
  const icons = {
    FIRST_TIME_BUYER: <User className="w-4 h-4 text-blue-500" />,
    INVESTOR: <TrendingUp className="w-4 h-4 text-green-500" />,
    SELLER: <Building className="w-4 h-4 text-purple-500" />,
    COMMERCIAL: <Briefcase className="w-4 h-4 text-orange-500" />
  }
  return icons[type]
}

function PriorityBadge({ priority }: { priority: CustomerJourney['priority'] }) {
  const colors = {
    low: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
    medium: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    high: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
    urgent: 'bg-red-500/10 text-red-400 border-red-500/20'
  }

  return (
    <Badge variant="outline" className={cn("text-xs", colors[priority])}>
      {priority.toUpperCase()}
    </Badge>
  )
}

function StepStatusIndicator({ status }: { status: StepStatus }) {
  const indicators = {
    pending: <div className="w-3 h-3 rounded-full border-2 border-gray-500" />,
    active: <div className="w-3 h-3 rounded-full bg-blue-500 animate-pulse shadow-[0_0_10px_rgba(59,130,246,0.5)]" />,
    completed: <CheckCircle2 className="w-4 h-4 text-green-500" />,
    skipped: <div className="w-3 h-3 rounded-full border-2 border-yellow-500 bg-yellow-500/20" />,
    failed: <AlertTriangle className="w-4 h-4 text-red-500" />
  }

  return indicators[status]
}

function JourneyCard({ journey }: { journey: CustomerJourney }) {
  const currentStep = journey.steps[journey.currentStep]

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
            <div className="flex items-center gap-3">
              <JourneyTypeIcon type={journey.type} />
              <div>
                <CardTitle className="text-white text-sm font-semibold">{journey.customerName}</CardTitle>
                <p className="text-xs text-gray-400 capitalize">{journey.type.replace('_', ' ').toLowerCase()}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <PriorityBadge priority={journey.priority} />
              <Badge variant="outline" className="text-[10px] bg-white/5 border-white/10">
                {journey.completionPercentage}%
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-0 space-y-4">
          {/* Progress */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Step {journey.currentStep + 1} of {journey.totalSteps}</span>
              <span className="text-blue-400">{journey.completionPercentage}% complete</span>
            </div>
            <Progress value={journey.completionPercentage} className="h-2" />
          </div>

          {/* Current Step */}
          {currentStep && (
            <div className="p-3 bg-black/20 border border-white/5 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <StepStatusIndicator status={currentStep.status} />
                <span className="text-sm font-semibold text-white">{currentStep.name}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-400">
                <Bot className="w-3 h-3" />
                <span>{currentStep.agentName}</span>
                <Clock className="w-3 h-3 ml-2" />
                <span>{currentStep.estimatedDuration}m</span>
              </div>
            </div>
          )}

          {/* Context */}
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-white/5 rounded-lg p-2">
              <div className="text-[10px] text-gray-500 uppercase font-mono">Timeline</div>
              <div className="text-xs font-semibold text-white">{journey.context.timeframe || 'Flexible'}</div>
            </div>
            <div className="bg-white/5 rounded-lg p-2">
              <div className="text-[10px] text-gray-500 uppercase font-mono">Budget</div>
              <div className="text-xs font-semibold text-white">
                {journey.context.budget ? `$${journey.context.budget.toLocaleString()}` : 'TBD'}
              </div>
            </div>
          </div>

          {/* Analytics */}
          <div className="border-t border-white/10 pt-3">
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="text-center">
                <div className="text-green-400 font-semibold">{journey.analytics.customerSatisfaction}%</div>
                <div className="text-gray-500">Satisfaction</div>
              </div>
              <div className="text-center">
                <div className="text-blue-400 font-semibold">{journey.analytics.avgResponseTime}ms</div>
                <div className="text-gray-500">Avg Response</div>
              </div>
              <div className="text-center">
                <div className="text-purple-400 font-semibold">{journey.analytics.handoffEfficiency}%</div>
                <div className="text-gray-500">Handoffs</div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <Button size="sm" variant="outline" className="flex-1 border-white/20 text-white text-xs">
              <Eye className="w-3 h-3 mr-1" />
              View
            </Button>
            <Button size="sm" className="flex-1 bg-blue-600 hover:bg-blue-500 text-white text-xs">
              <Settings className="w-3 h-3 mr-1" />
              Manage
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

function JourneyTimeline({ journey }: { journey: CustomerJourney }) {
  return (
    <Card className="bg-white/5 border-white/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <Route className="w-5 h-5 text-purple-500" />
          Journey Timeline - {journey.customerName}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {journey.steps.map((step, index) => (
            <motion.div
              key={step.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center gap-4"
            >
              <div className="flex flex-col items-center">
                <StepStatusIndicator status={step.status} />
                {index < journey.steps.length - 1 && (
                  <div className={cn(
                    "w-px h-12 mt-2",
                    step.status === 'completed' ? "bg-green-500" : "bg-gray-600"
                  )} />
                )}
              </div>

              <div className={cn(
                "flex-1 p-4 rounded-lg border transition-all",
                step.status === 'active' && "bg-blue-500/10 border-blue-500/20",
                step.status === 'completed' && "bg-green-500/10 border-green-500/20",
                step.status === 'pending' && "bg-white/5 border-white/10",
                step.status === 'failed' && "bg-red-500/10 border-red-500/20"
              )}>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold text-white">{step.name}</h4>
                  <Badge variant="outline" className="text-[10px] bg-white/5 border-white/10">
                    {step.estimatedDuration}m
                  </Badge>
                </div>

                <p className="text-xs text-gray-400 mb-3">{step.description}</p>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <Bot className="w-3 h-3" />
                    <span>{step.agentName}</span>
                  </div>

                  {step.status === 'active' && (
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                      <span className="text-xs text-blue-400">In Progress</span>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function OrchestratorStats() {
  const totalJourneys = mockActiveJourneys.length
  const activeJourneys = mockActiveJourneys.filter(j => j.status === 'active').length
  const avgCompletion = Math.round(mockActiveJourneys.reduce((sum, j) => sum + j.completionPercentage, 0) / totalJourneys)
  const avgSatisfaction = Math.round(mockActiveJourneys.reduce((sum, j) => sum + j.analytics.customerSatisfaction, 0) / totalJourneys)

  const stats = [
    { label: 'Active Journeys', value: activeJourneys.toString(), icon: <Activity className="w-5 h-5" />, color: 'text-blue-400' },
    { label: 'Total Managed', value: totalJourneys.toString(), icon: <Users className="w-5 h-5" />, color: 'text-purple-400' },
    { label: 'Avg Completion', value: `${avgCompletion}%`, icon: <Target className="w-5 h-5" />, color: 'text-green-400' },
    { label: 'Satisfaction', value: `${avgSatisfaction}%`, icon: <Star className="w-5 h-5" />, color: 'text-yellow-400' }
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {stats.map((stat, index) => (
        <motion.div
          key={index}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
        >
          <Card className="bg-white/5 border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className={cn("p-2 rounded-lg bg-black/20", stat.color)}>
                  {stat.icon}
                </div>
                <div>
                  <div className="text-lg font-bold text-white">{stat.value}</div>
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

interface CustomerJourneyOrchestratorProps {
  className?: string
}

export function CustomerJourneyOrchestrator({ className = '' }: CustomerJourneyOrchestratorProps) {
  const [selectedJourney, setSelectedJourney] = useState<string | null>(null)
  const [selectedTab, setSelectedTab] = useState('active')

  const selectedJourneyData = selectedJourney
    ? mockActiveJourneys.find(j => j.id === selectedJourney)
    : null

  return (
    <div className={cn("w-full space-y-6", className)}>
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Customer Journey Orchestrator</h1>
          <p className="text-gray-400 text-sm">
            End-to-end experience coordination across all specialized agents
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Badge className="bg-green-500/10 text-green-400 border-green-500/20">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            {activeJourneys} Active Journeys
          </Badge>
          <Button size="sm" className="bg-purple-600 hover:bg-purple-500 text-white">
            <Route className="w-4 h-4 mr-2" />
            New Journey
          </Button>
        </div>
      </div>

      {/* Stats */}
      <OrchestratorStats />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Journey List */}
        <div className="lg:col-span-1">
          <Tabs value={selectedTab} onValueChange={setSelectedTab}>
            <TabsList className="bg-white/5 border border-white/10 w-full">
              <TabsTrigger value="active" className="data-[state=active]:bg-purple-600 flex-1">Active</TabsTrigger>
              <TabsTrigger value="templates" className="data-[state=active]:bg-purple-600 flex-1">Templates</TabsTrigger>
            </TabsList>

            <TabsContent value="active" className="mt-4">
              <div className="space-y-4">
                {mockActiveJourneys.map((journey) => (
                  <div
                    key={journey.id}
                    onClick={() => setSelectedJourney(journey.id === selectedJourney ? null : journey.id)}
                  >
                    <JourneyCard journey={journey} />
                  </div>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="templates" className="mt-4">
              <div className="space-y-3">
                {Object.entries(journeyTemplates).map(([type, steps]) => (
                  <Card key={type} className="bg-white/5 border-white/10 hover:border-white/20 transition-all cursor-pointer">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-3 mb-2">
                        <JourneyTypeIcon type={type as JourneyType} />
                        <span className="text-sm font-semibold text-white capitalize">
                          {type.replace('_', ' ').toLowerCase()}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mb-3">
                        {steps.length} steps • ~{steps.reduce((sum, step) => sum + (step.estimatedDuration || 0), 0)}m total
                      </p>
                      <Button size="sm" className="w-full bg-purple-600 hover:bg-purple-500 text-white text-xs">
                        Use Template
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
          </Tabs>
        </div>

        {/* Journey Details */}
        <div className="lg:col-span-2">
          {selectedJourneyData ? (
            <JourneyTimeline journey={selectedJourneyData} />
          ) : (
            <Card className="bg-gradient-to-br from-purple-500/10 to-blue-500/10 border-white/10">
              <CardContent className="p-12 text-center">
                <Route className="w-16 h-16 text-purple-500 mx-auto mb-6 opacity-50" />
                <h3 className="text-xl font-semibold text-white mb-3">Select a Journey</h3>
                <p className="text-gray-400 max-w-md mx-auto">
                  Choose an active journey from the left panel to view its detailed timeline and manage the customer experience.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Agent Coordination Status */}
      <Card className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-white/10">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-white mb-2">Multi-Agent Coordination</h3>
              <p className="text-gray-400 text-sm">
                Real-time orchestration of {mockActiveJourneys.reduce((sum, j) => sum + j.analytics.touchpoints, 0)} agent touchpoints across all active journeys
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Badge className="bg-green-500/10 text-green-400 border-green-500/20">
                <Activity className="w-3 h-3 mr-1" />
                95% Efficiency
              </Badge>
              <Button variant="outline" className="border-white/20 text-white">
                <Eye className="w-4 h-4 mr-2" />
                Monitor
              </Button>
              <Button className="bg-purple-600 hover:bg-purple-500 text-white">
                <Brain className="w-4 h-4 mr-2" />
                AI Optimize
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CustomerJourneyOrchestrator