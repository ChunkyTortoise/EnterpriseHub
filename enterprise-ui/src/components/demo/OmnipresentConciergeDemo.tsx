/**
 * Omnipresent Concierge Demo - Track 2 Features Showcase
 * Demonstrates the enhanced omnipresent intelligence capabilities
 *
 * Features Demonstrated:
 * 🎯 Context-aware guidance for every page/component
 * 🤝 Bot coordination recommendations
 * 💰 ROI optimization suggestions
 * 📱 Mobile field assistance
 * 🎭 Client presentation mode
 * 🧠 Jorge memory & learning system
 */

'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import {
  Eye,
  Bot,
  Zap,
  MapPin,
  PresentationChart,
  Brain,
  Activity,
  Users,
  ArrowRightLeft,
  Sparkles,
  Target,
  TrendingUp,
  Shield,
  Lightbulb,
  Clock,
  AlertTriangle,
  CheckCircle,
  Settings
} from 'lucide-react'
import { useOmnipresentConcierge } from '@/components/providers/OmnipresentConciergeProvider'
import { createPlatformContext } from '@/lib/claude-concierge/OmnipresentConciergeService'
import { useToast } from '@/hooks/use-toast'

// ============================================================================
// DEMO DATA
// ============================================================================

const DEMO_CONTEXTS = {
  executive_dashboard: {
    current_page: '/executive-dashboard',
    user_role: 'executive',
    active_leads: [
      { id: 'lead_001', name: 'Sarah Chen', score: 85, value: '$650,000' },
      { id: 'lead_002', name: 'Mike Rodriguez', score: 92, value: '$450,000' },
      { id: 'lead_003', name: 'Jennifer Walsh', score: 78, value: '$520,000' }
    ],
    business_metrics: {
      monthly_revenue: 180000,
      commission_earned: 42000,
      deals_closed: 8,
      pipeline_health: 0.85,
      conversion_rate: 0.34
    },
    bot_statuses: {
      jorge_seller_bot: { status: 'active', success_rate: 0.87, active_conversations: 5 },
      lead_bot: { status: 'active', success_rate: 0.92, active_conversations: 12 },
      intent_decoder: { status: 'active', success_rate: 0.95, processed_today: 47 }
    }
  },

  field_agent: {
    current_page: '/field-agent',
    user_role: 'agent',
    device_type: 'mobile',
    location_context: {
      current_latitude: 30.2672,
      current_longitude: -97.7431,
      current_address: '1234 Austin Heights Dr, Austin, TX 78704',
      nearby_properties: [
        { id: 'prop_001', address: '1240 Austin Heights Dr', price: 485000, status: 'available' },
        { id: 'prop_002', address: '1228 Austin Heights Dr', price: 525000, status: 'pending' }
      ]
    },
    active_properties: [
      { id: 'prop_showing_001', address: '1234 Austin Heights Dr', client: 'Sarah Chen', time: '2:00 PM' }
    ]
  },

  client_presentation: {
    current_page: '/presentation/client/demo',
    user_role: 'client',
    active_properties: [
      { id: 'presentation_001', address: '567 Lake Austin Blvd', price: 750000, features: ['waterfront', 'updated_kitchen'] }
    ],
    client_profile: {
      name: 'Michael & Sarah Thompson',
      budget_max: 800000,
      preferences: ['waterfront', 'good_schools', 'modern'],
      timeline: 'urgent',
      financing: 'pre_approved'
    }
  }
}

const DEMO_SCENARIOS = [
  {
    id: 'high_value_lead',
    title: 'High-Value Lead Qualification',
    description: 'Jorge needs to qualify a $2M+ luxury property lead',
    context: {
      active_leads: [{ id: 'luxury_001', name: 'David Kim', value: '$2,100,000', urgency: 'high' }],
      priority_actions: [{ type: 'qualification', urgency: 'immediate', value: 2100000 }]
    }
  },
  {
    id: 'bot_handoff',
    title: 'Bot Coordination Needed',
    description: 'Multiple bots need coordination for optimal lead handling',
    context: {
      bot_statuses: {
        jorge_seller_bot: { status: 'overloaded', queue_length: 8 },
        lead_bot: { status: 'available', capacity: 0.6 },
        intent_decoder: { status: 'processing', current_load: 0.9 }
      }
    }
  },
  {
    id: 'market_opportunity',
    title: 'Market Opportunity Alert',
    description: 'New market conditions create revenue opportunities',
    context: {
      market_conditions: {
        interest_rates: 'dropping',
        inventory: 'low',
        demand: 'high',
        opportunity_score: 0.92
      }
    }
  }
]

// ============================================================================
// MAIN DEMO COMPONENT
// ============================================================================

export function OmnipresentConciergeDemo() {
  const {
    isInitialized,
    isConnected,
    currentContext,
    lastGuidance,
    isGeneratingGuidance,
    omnipresentMonitoring,
    serviceMetrics,
    connectionQuality,
    responseTimeMs,
    enableOmnipresence,
    disableOmnipresence,
    requestGuidance,
    updateContext,
    learnFromDecision,
    enableFieldMode,
    enablePresentationMode,
    requestBotCoordination,
    requestRealTimeCoaching
  } = useOmnipresentConcierge()

  const { toast } = useToast()

  const [selectedContext, setSelectedContext] = useState('executive_dashboard')
  const [selectedScenario, setSelectedScenario] = useState('')
  const [guidanceMode, setGuidanceMode] = useState('proactive')
  const [customDecision, setCustomDecision] = useState('')
  const [customOutcome, setCustomOutcome] = useState('')

  // Auto-enable omnipresence for demo
  useEffect(() => {
    if (isInitialized && !omnipresentMonitoring) {
      setTimeout(() => {
        enableOmnipresence()
      }, 2000)
    }
  }, [isInitialized, omnipresentMonitoring])

  // Update context when demo context changes
  useEffect(() => {
    if (DEMO_CONTEXTS[selectedContext as keyof typeof DEMO_CONTEXTS]) {
      const demoContext = DEMO_CONTEXTS[selectedContext as keyof typeof DEMO_CONTEXTS]
      updateContext(demoContext)
    }
  }, [selectedContext])

  const handleScenarioDemo = async (scenario: any) => {
    setSelectedScenario(scenario.id)
    updateContext(scenario.context)

    toast({
      title: "🎭 Demo Scenario Loaded",
      description: scenario.description,
      duration: 4000,
    })

    // Request guidance for the scenario
    setTimeout(() => {
      requestGuidance('reactive', 'workflow')
    }, 1000)
  }

  const handleLearningDemo = async () => {
    if (!customDecision.trim() || !customOutcome.trim()) {
      toast({
        title: "Missing Information",
        description: "Please enter both decision and outcome for learning demo.",
        variant: "destructive"
      })
      return
    }

    const decision = {
      type: 'demo_decision',
      description: customDecision,
      context: selectedContext,
      timestamp: new Date().toISOString()
    }

    const outcome = {
      type: 'demo_outcome',
      description: customOutcome,
      success: customOutcome.toLowerCase().includes('success') || customOutcome.toLowerCase().includes('positive'),
      timestamp: new Date().toISOString()
    }

    await learnFromDecision(decision, outcome)
    setCustomDecision('')
    setCustomOutcome('')
  }

  const renderStatusIndicator = (status: string, value: any) => {
    const getColor = () => {
      if (typeof value === 'boolean') return value ? 'green' : 'red'
      if (typeof value === 'number') {
        if (value > 0.8) return 'green'
        if (value > 0.6) return 'yellow'
        return 'red'
      }
      if (status === 'active' || status === 'connected') return 'green'
      if (status === 'pending' || status === 'initializing') return 'yellow'
      return 'red'
    }

    const color = getColor()

    return (
      <div className={`w-3 h-3 rounded-full bg-${color}-500`} />
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-purple-200">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-2xl">
                <Sparkles className="w-8 h-8 text-purple-600" />
                Omnipresent Concierge Demo
                <Badge variant="secondary" className="bg-purple-100 text-purple-700">
                  Track 2
                </Badge>
              </CardTitle>
              <CardDescription className="text-lg mt-2">
                Experience context-aware AI guidance across Jorge's platform
              </CardDescription>
            </div>

            <div className="flex items-center gap-4">
              {/* Status Indicators */}
              <div className="flex items-center gap-2">
                {renderStatusIndicator('', isInitialized)}
                <span className="text-sm">
                  {isInitialized ? 'Initialized' : 'Loading...'}
                </span>
              </div>

              <div className="flex items-center gap-2">
                {renderStatusIndicator('', isConnected)}
                <span className="text-sm">
                  {isConnected ? 'Connected' : 'Offline'}
                </span>
              </div>

              <div className="flex items-center gap-2">
                <Eye className={`w-4 h-4 ${omnipresentMonitoring ? 'text-green-600' : 'text-gray-400'}`} />
                <span className="text-sm">
                  {omnipresentMonitoring ? 'Monitoring' : 'Inactive'}
                </span>
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      <Tabs defaultValue="contexts" className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="contexts">Contexts</TabsTrigger>
          <TabsTrigger value="scenarios">Scenarios</TabsTrigger>
          <TabsTrigger value="bots">Bot Coordination</TabsTrigger>
          <TabsTrigger value="field">Field Mode</TabsTrigger>
          <TabsTrigger value="presentation">Presentation</TabsTrigger>
          <TabsTrigger value="learning">Learning</TabsTrigger>
        </TabsList>

        {/* Context Selection Demo */}
        <TabsContent value="contexts" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Context Selection */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="w-5 h-5" />
                  Platform Context
                </CardTitle>
                <CardDescription>
                  Switch between different platform contexts to see adaptive guidance
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {Object.entries(DEMO_CONTEXTS).map(([key, context]) => (
                  <Button
                    key={key}
                    variant={selectedContext === key ? "default" : "outline"}
                    className="w-full justify-start"
                    onClick={() => setSelectedContext(key)}
                  >
                    <div className="flex items-center gap-2">
                      {key === 'executive_dashboard' && <TrendingUp className="w-4 h-4" />}
                      {key === 'field_agent' && <MapPin className="w-4 h-4" />}
                      {key === 'client_presentation' && <PresentationChart className="w-4 h-4" />}
                      {key.replace('_', ' ').toUpperCase()}
                    </div>
                  </Button>
                ))}

                <div className="pt-4 space-y-2">
                  <Label>Guidance Mode</Label>
                  <select
                    value={guidanceMode}
                    onChange={(e) => setGuidanceMode(e.target.value)}
                    className="w-full p-2 border rounded-md"
                  >
                    <option value="proactive">Proactive</option>
                    <option value="reactive">Reactive</option>
                    <option value="executive">Executive</option>
                    <option value="field_work">Field Work</option>
                    <option value="presentation">Presentation</option>
                  </select>
                </div>

                <Button
                  onClick={() => requestGuidance(guidanceMode, 'workflow')}
                  disabled={isGeneratingGuidance}
                  className="w-full"
                >
                  {isGeneratingGuidance ? (
                    <Zap className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Sparkles className="w-4 h-4 mr-2" />
                  )}
                  Generate Contextual Guidance
                </Button>
              </CardContent>
            </Card>

            {/* Current Context Display */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  Current Context
                </CardTitle>
              </CardHeader>
              <CardContent>
                {currentContext ? (
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span className="font-medium">Page:</span>
                      <Badge variant="outline">{currentContext.current_page}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium">Role:</span>
                      <Badge variant="outline">{currentContext.user_role}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium">Device:</span>
                      <Badge variant="outline">{currentContext.device_type}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium">Active Leads:</span>
                      <Badge variant="outline">{currentContext.active_leads?.length || 0}</Badge>
                    </div>
                    {connectionQuality && (
                      <div className="flex justify-between">
                        <span className="font-medium">Connection:</span>
                        <Badge
                          variant="outline"
                          className={
                            connectionQuality === 'excellent' ? 'text-green-600' :
                            connectionQuality === 'good' ? 'text-yellow-600' : 'text-red-600'
                          }
                        >
                          {connectionQuality}
                        </Badge>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No context available</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Latest Guidance Display */}
          {lastGuidance && (
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Lightbulb className="w-5 h-5 text-yellow-500" />
                  Latest Guidance
                  <Badge
                    variant={
                      lastGuidance.urgency_level === 'urgent' ? 'destructive' :
                      lastGuidance.urgency_level === 'high' ? 'default' : 'outline'
                    }
                  >
                    {lastGuidance.urgency_level}
                  </Badge>
                  <Badge variant="outline">
                    {Math.round(lastGuidance.confidence_score * 100)}% confidence
                  </Badge>
                  <Badge variant="outline">
                    {responseTimeMs}ms
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-lg">{lastGuidance.primary_guidance}</p>

                {lastGuidance.immediate_actions.length > 0 && (
                  <div>
                    <h4 className="font-semibold flex items-center gap-2 mb-2">
                      <Zap className="w-4 h-4" />
                      Immediate Actions
                    </h4>
                    <div className="space-y-2">
                      {lastGuidance.immediate_actions.map((action, index) => (
                        <div key={index} className="flex items-center justify-between p-2 bg-muted rounded">
                          <span className="text-sm">{action.description}</span>
                          <Badge variant="outline">{action.priority}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {lastGuidance.page_specific_tips.length > 0 && (
                  <div>
                    <h4 className="font-semibold flex items-center gap-2 mb-2">
                      <Target className="w-4 h-4" />
                      Page-Specific Tips
                    </h4>
                    <ul className="space-y-1">
                      {lastGuidance.page_specific_tips.map((tip, index) => (
                        <li key={index} className="text-sm text-muted-foreground">• {tip}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {lastGuidance.risk_alerts.length > 0 && (
                  <div>
                    <h4 className="font-semibold flex items-center gap-2 mb-2 text-red-600">
                      <AlertTriangle className="w-4 h-4" />
                      Risk Alerts
                    </h4>
                    <div className="space-y-2">
                      {lastGuidance.risk_alerts.map((alert, index) => (
                        <div key={index} className="p-2 bg-red-50 border border-red-200 rounded">
                          <p className="text-sm font-medium text-red-800">{alert.description}</p>
                          <p className="text-xs text-red-600">{alert.mitigation}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Demo Scenarios */}
        <TabsContent value="scenarios" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {DEMO_SCENARIOS.map((scenario) => (
              <Card key={scenario.id} className={selectedScenario === scenario.id ? 'border-purple-300 bg-purple-50' : ''}>
                <CardHeader>
                  <CardTitle className="text-lg">{scenario.title}</CardTitle>
                  <CardDescription>{scenario.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={() => handleScenarioDemo(scenario)}
                    disabled={isGeneratingGuidance}
                    className="w-full"
                  >
                    {selectedScenario === scenario.id ? (
                      <CheckCircle className="w-4 h-4 mr-2" />
                    ) : (
                      <Sparkles className="w-4 h-4 mr-2" />
                    )}
                    {selectedScenario === scenario.id ? 'Active' : 'Try This Scenario'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Bot Coordination Demo */}
        <TabsContent value="bots" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bot className="w-5 h-5" />
                  Bot Coordination
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={() => requestBotCoordination('jorge-seller', 'High-value lead requires qualification', 'immediate')}
                  className="w-full"
                >
                  <ArrowRightLeft className="w-4 h-4 mr-2" />
                  Request Jorge Seller Bot
                </Button>

                <Button
                  onClick={() => requestBotCoordination('lead-bot', 'Lead nurturing sequence needed', 'scheduled')}
                  variant="outline"
                  className="w-full"
                >
                  <Users className="w-4 h-4 mr-2" />
                  Request Lead Bot
                </Button>

                <Button
                  onClick={() => requestRealTimeCoaching({
                    situation: 'client_objection',
                    objection_type: 'price_concern',
                    property_value: 650000
                  }, 'high')}
                  variant="outline"
                  className="w-full"
                >
                  <Brain className="w-4 h-4 mr-2" />
                  Request Real-time Coaching
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Performance Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                {serviceMetrics ? (
                  <div className="space-y-3 text-sm">
                    <div className="flex justify-between">
                      <span>Requests Processed:</span>
                      <span className="font-mono">{serviceMetrics.requests_processed}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Avg Response Time:</span>
                      <span className="font-mono">{serviceMetrics.avg_response_time_ms}ms</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Active Sessions:</span>
                      <span className="font-mono">{serviceMetrics.active_sessions}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Cache Hit Rate:</span>
                      <span className="font-mono">{Math.round(serviceMetrics.cache_hit_rate * 100)}%</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-muted-foreground">Loading metrics...</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Field Mode Demo */}
        <TabsContent value="field" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MapPin className="w-5 h-5" />
                Mobile Field Assistance Demo
              </CardTitle>
              <CardDescription>
                Experience location-aware guidance for property visits
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={() => enableFieldMode({
                  latitude: 30.2672,
                  longitude: -97.7431,
                  address: '1234 Austin Heights Dr, Austin, TX 78704',
                  property_type: 'single_family',
                  visit_purpose: 'client_showing',
                  client_name: 'Sarah Chen'
                })}
                className="w-full"
              >
                <MapPin className="w-4 h-4 mr-2" />
                Enable Field Mode (Demo Location)
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Presentation Mode Demo */}
        <TabsContent value="presentation" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PresentationChart className="w-5 h-5" />
                Client Presentation Mode Demo
              </CardTitle>
              <CardDescription>
                Client-safe guidance with professional talking points
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={() => enablePresentationMode({
                  name: 'Michael & Sarah Thompson',
                  budget_max: 800000,
                  preferences: ['waterfront', 'good_schools', 'modern'],
                  timeline: 'urgent',
                  financing: 'pre_approved',
                  decision_makers: 'both_present'
                })}
                className="w-full"
              >
                <PresentationChart className="w-4 h-4 mr-2" />
                Enable Presentation Mode (Demo Client)
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Learning System Demo */}
        <TabsContent value="learning" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-5 h-5" />
                Jorge Memory & Learning System
              </CardTitle>
              <CardDescription>
                Train the AI by providing decision-outcome pairs
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label>Decision Made</Label>
                <Input
                  value={customDecision}
                  onChange={(e) => setCustomDecision(e.target.value)}
                  placeholder="e.g., Reduced price by 5% to accelerate sale"
                />
              </div>

              <div className="space-y-2">
                <Label>Outcome Achieved</Label>
                <Input
                  value={customOutcome}
                  onChange={(e) => setCustomOutcome(e.target.value)}
                  placeholder="e.g., Received 3 offers within 48 hours"
                />
              </div>

              <Button
                onClick={handleLearningDemo}
                disabled={!customDecision.trim() || !customOutcome.trim()}
                className="w-full"
              >
                <Brain className="w-4 h-4 mr-2" />
                Record Learning Event
              </Button>

              <div className="pt-4 border-t space-y-2">
                <h4 className="font-semibold">Pre-built Learning Examples:</h4>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setCustomDecision('Switched from email to SMS for follow-up')
                    setCustomOutcome('Response rate increased by 60%')
                  }}
                  className="w-full text-left justify-start"
                >
                  📱 Communication Channel Optimization
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setCustomDecision('Scheduled showing within 24 hours of inquiry')
                    setCustomOutcome('Lead converted to offer, closed successfully')
                  }}
                  className="w-full text-left justify-start"
                >
                  ⚡ Rapid Response Strategy
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default OmnipresentConciergeDemo