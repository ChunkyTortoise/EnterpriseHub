/**
 * Omnipresent Concierge Provider - Track 2 Platform Integration
 * Provides context-aware AI guidance across the entire platform
 *
 * Features:
 * 🎯 Automatic context detection and guidance generation
 * 🤝 Bot coordination recommendations
 * 💰 ROI optimization suggestions
 * 📱 Mobile field assistance
 * 🎭 Client presentation support
 * 🧠 Jorge preference learning
 */

'use client'

import React, { createContext, useContext, useEffect, useRef, useState, useCallback } from 'react'
import { usePathname } from 'next/navigation'
import { useSession } from 'next-auth/react'
import {
  OmnipresentConciergeService,
  getOmnipresentConciergeService,
  createPlatformContext,
  type PlatformContext,
  type ConciergeResponse,
  type ServiceMetrics
} from '@/lib/claude-concierge/OmnipresentConciergeService'
import { useConciergeStore } from '@/store/useConciergeStore'
import { useToast } from '@/hooks/use-toast'

// ============================================================================
// CONTEXT TYPES
// ============================================================================

interface OmnipresentConciergeContextValue {
  // Service Instance
  service: OmnipresentConciergeService
  isInitialized: boolean
  isConnected: boolean

  // Platform Intelligence
  currentContext: PlatformContext | null
  lastGuidance: ConciergeResponse | null
  isGeneratingGuidance: boolean

  // Real-time Features
  omnipresentMonitoring: boolean
  proactiveAssistance: boolean
  contextualHints: boolean

  // Performance & Metrics
  serviceMetrics: ServiceMetrics | null
  connectionQuality: string
  responseTimeMs: number

  // Actions
  enableOmnipresence: () => Promise<void>
  disableOmnipresence: () => void
  requestGuidance: (mode?: string, scope?: string) => Promise<ConciergeResponse | null>
  updateContext: (updates: Partial<PlatformContext>) => void
  learnFromDecision: (decision: Record<string, any>, outcome: Record<string, any>) => Promise<void>

  // Field Work Actions
  enableFieldMode: (locationData: Record<string, any>) => Promise<void>
  disableFieldMode: () => void

  // Presentation Mode Actions
  enablePresentationMode: (clientProfile: Record<string, any>) => Promise<void>
  disablePresentationMode: () => void

  // Bot Coordination
  requestBotCoordination: (targetBot: string, reason: string, urgency?: string) => Promise<void>
  requestRealTimeCoaching: (situation: Record<string, any>, urgency?: string) => Promise<void>
}

const OmnipresentConciergeContext = createContext<OmnipresentConciergeContextValue | null>(null)

// ============================================================================
// PLATFORM CONTEXT DETECTION UTILITIES
// ============================================================================

/**
 * Detect current platform context based on route, user activity, and system state
 */
function detectPlatformContext(
  pathname: string,
  session: any,
  customData: Record<string, any> = {}
): PlatformContext {
  const deviceType = typeof window !== 'undefined' && window.innerWidth < 768 ? 'mobile' : 'desktop'

  // Determine user role based on route and session
  let userRole = 'agent'
  if (pathname.includes('/executive')) userRole = 'executive'
  else if (pathname.includes('/client') || pathname.includes('/presentation')) userRole = 'client'

  // Extract business context based on current page
  const businessContext = extractBusinessContext(pathname, customData)

  return createPlatformContext({
    current_page: pathname,
    user_role: userRole,
    session_id: session?.user?.id || `anon_${Date.now()}`,
    device_type: deviceType,
    connection_quality: detectConnectionQuality(),
    ...businessContext,
    ...customData
  })
}

/**
 * Extract business-specific context based on current route
 */
function extractBusinessContext(pathname: string, customData: Record<string, any>) {
  const context: Partial<PlatformContext> = {}

  // Page-specific context extraction
  if (pathname.includes('/jorge')) {
    context.bot_statuses = {
      jorge_seller_bot: { status: 'active', performance: { success_rate: 0.87 } },
      lead_bot: { status: 'active', performance: { success_rate: 0.92 } },
      intent_decoder: { status: 'active', performance: { success_rate: 0.95 } }
    }
    context.business_metrics = {
      conversion_rate: 0.34,
      pipeline_value: 2450000,
      active_deals: 12,
      avg_deal_size: 485000
    }
  }

  if (pathname.includes('/executive')) {
    context.business_metrics = {
      monthly_revenue: 180000,
      commission_earned: 42000,
      deals_closed: 8,
      pipeline_health: 0.85
    }
    context.commission_opportunities = [
      { property_id: 'prop_001', estimated_commission: 24000, probability: 0.8 },
      { property_id: 'prop_002', estimated_commission: 18500, probability: 0.6 }
    ]
  }

  if (pathname.includes('/field-agent')) {
    context.location_context = {
      current_latitude: customData.latitude || 30.2672,
      current_longitude: customData.longitude || -97.7431,
      current_address: customData.address || 'Rancho Cucamonga, TX',
      nearby_properties: customData.nearby_properties || []
    }
    context.device_type = 'mobile'
    context.offline_capabilities = true
  }

  if (pathname.includes('/presentation')) {
    context.user_role = 'client'
    context.active_properties = customData.presentation_properties || []
  }

  return context
}

/**
 * Detect connection quality based on navigator and performance metrics
 */
function detectConnectionQuality(): string {
  if (typeof window === 'undefined') return 'good'

  // Use Network Information API if available
  const connection = (navigator as any).connection
  if (connection) {
    if (connection.effectiveType === '4g' && connection.downlink > 2) return 'excellent'
    if (connection.effectiveType === '4g' || connection.effectiveType === '3g') return 'good'
    return 'poor'
  }

  // Fallback to simple heuristics
  const now = performance.now()
  const paintEntries = performance.getEntriesByType('paint')
  if (paintEntries.length > 0) {
    const firstPaint = paintEntries[0].startTime
    if (firstPaint < 1000) return 'excellent'
    if (firstPaint < 2500) return 'good'
    return 'poor'
  }

  return 'good'
}

// ============================================================================
// MAIN PROVIDER COMPONENT
// ============================================================================

interface OmnipresentConciergeProviderProps {
  children: React.ReactNode
  enableAutoGuidance?: boolean
  enableRealTimeUpdates?: boolean
  updateInterval?: number
}

export function OmnipresentConciergeProvider({
  children,
  enableAutoGuidance = true,
  enableRealTimeUpdates = true,
  updateInterval = 30000 // 30 seconds
}: OmnipresentConciergeProviderProps) {
  // Hooks
  const pathname = usePathname()
  const { data: session } = useSession()
  const { toast } = useToast()

  // Service and State
  const serviceRef = useRef<OmnipresentConciergeService | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [currentContext, setCurrentContext] = useState<PlatformContext | null>(null)
  const [lastGuidance, setLastGuidance] = useState<ConciergeResponse | null>(null)
  const [isGeneratingGuidance, setIsGeneratingGuidance] = useState(false)
  const [serviceMetrics, setServiceMetrics] = useState<ServiceMetrics | null>(null)
  const [connectionQuality, setConnectionQuality] = useState('good')
  const [responseTimeMs, setResponseTimeMs] = useState(0)

  // Feature Flags
  const [omnipresentMonitoring, setOmnipresentMonitoring] = useState(false)
  const [proactiveAssistance, setProactiveAssistance] = useState(enableAutoGuidance)
  const [contextualHints, setContextualHints] = useState(true)

  // Mode States
  const [fieldModeEnabled, setFieldModeEnabled] = useState(false)
  const [presentationModeEnabled, setPresentationModeEnabled] = useState(false)
  const [fieldLocationData, setFieldLocationData] = useState<Record<string, any>>({})
  const [clientProfile, setClientProfile] = useState<Record<string, any>>({})

  // Update intervals
  const guidanceIntervalRef = useRef<NodeJS.Timeout>()
  const metricsIntervalRef = useRef<NodeJS.Timeout>()

  // Initialize service
  useEffect(() => {
    const initializeService = async () => {
      try {
        const service = getOmnipresentConciergeService()
        serviceRef.current = service

        // Set up event listeners
        service.on('connected', () => {
          setIsConnected(true)
          toast({
            title: "🎯 Omnipresent Intelligence Active",
            description: "Claude Concierge is now monitoring your platform activity.",
            duration: 3000,
          })
        })

        service.on('disconnected', () => {
          setIsConnected(false)
        })

        service.on('guidance-generated', ({ guidance }) => {
          setLastGuidance(guidance)
          setResponseTimeMs(guidance.response_time_ms)

          // Show proactive notifications for high urgency guidance
          if (guidance.urgency_level === 'urgent' || guidance.urgency_level === 'high') {
            toast({
              title: "⚡ Urgent Guidance",
              description: guidance.primary_guidance.substring(0, 100) + '...',
              duration: 8000,
            })
          }
        })

        service.on('error', ({ type, error }) => {
          console.error(`Concierge error (${type}):`, error)

          // User-friendly error notifications
          if (type === 'connection-error') {
            toast({
              title: "Connection Issue",
              description: "Reconnecting to AI services...",
              variant: "destructive",
              duration: 5000,
            })
          }
        })

        service.on('real-time-guidance', (guidance) => {
          setLastGuidance(guidance)

          if (contextualHints && guidance.page_specific_tips?.length > 0) {
            toast({
              title: "💡 Contextual Tip",
              description: guidance.page_specific_tips[0],
              duration: 6000,
            })
          }
        })

        // Connect real-time features if enabled
        if (enableRealTimeUpdates) {
          await service.connectRealTime()
        }

        // Health check
        await service.healthCheck()

        setIsInitialized(true)
        console.log('🎯 Omnipresent Concierge Provider initialized')

      } catch (error) {
        console.error('Failed to initialize Omnipresent Concierge:', error)
        toast({
          title: "Initialization Error",
          description: "AI guidance services are temporarily unavailable.",
          variant: "destructive",
          duration: 8000,
        })
      }
    }

    initializeService()

    return () => {
      if (serviceRef.current) {
        serviceRef.current.disconnectRealTime()
      }
      if (guidanceIntervalRef.current) clearInterval(guidanceIntervalRef.current)
      if (metricsIntervalRef.current) clearInterval(metricsIntervalRef.current)
    }
  }, [])

  // Update context when route changes
  useEffect(() => {
    if (!isInitialized) return

    const newContext = detectPlatformContext(pathname, session, {
      field_mode_enabled: fieldModeEnabled,
      field_location_data: fieldLocationData,
      presentation_mode_enabled: presentationModeEnabled,
      client_profile: clientProfile
    })

    setCurrentContext(newContext)

    // Send context update to service
    if (enableRealTimeUpdates && serviceRef.current) {
      serviceRef.current.sendContextUpdate(newContext)
    }

    // Generate guidance for significant page changes
    if (proactiveAssistance && (
      pathname.includes('/jorge') ||
      pathname.includes('/executive') ||
      pathname.includes('/field-agent') ||
      pathname.includes('/presentation')
    )) {
      // Debounce guidance generation
      setTimeout(() => {
        requestGuidance('proactive')
      }, 1500)
    }

  }, [pathname, session, isInitialized, proactiveAssistance, fieldModeEnabled, presentationModeEnabled])

  // Set up periodic guidance updates
  useEffect(() => {
    if (!omnipresentMonitoring || !currentContext) return

    guidanceIntervalRef.current = setInterval(() => {
      requestGuidance('proactive', 'platform_wide')
    }, updateInterval)

    return () => {
      if (guidanceIntervalRef.current) {
        clearInterval(guidanceIntervalRef.current)
      }
    }
  }, [omnipresentMonitoring, currentContext, updateInterval])

  // Set up metrics monitoring
  useEffect(() => {
    if (!isInitialized) return

    const updateMetrics = async () => {
      try {
        if (serviceRef.current) {
          const metrics = await serviceRef.current.getMetrics()
          setServiceMetrics(metrics)
        }
      } catch (error) {
        console.error('Error updating metrics:', error)
      }
    }

    // Initial metrics load
    updateMetrics()

    // Periodic metrics updates
    metricsIntervalRef.current = setInterval(updateMetrics, 60000) // 1 minute

    return () => {
      if (metricsIntervalRef.current) {
        clearInterval(metricsIntervalRef.current)
      }
    }
  }, [isInitialized])

  // Update connection quality periodically
  useEffect(() => {
    const updateConnectionQuality = () => {
      setConnectionQuality(detectConnectionQuality())
    }

    updateConnectionQuality()
    const interval = setInterval(updateConnectionQuality, 30000)

    return () => clearInterval(interval)
  }, [])

  // ========================================================================
  // ACTION METHODS
  // ========================================================================

  const enableOmnipresence = useCallback(async () => {
    if (!serviceRef.current || !currentContext) return

    try {
      setOmnipresentMonitoring(true)

      toast({
        title: "🎯 Omnipresent Mode Enabled",
        description: "Claude is now continuously monitoring and providing guidance.",
        duration: 4000,
      })

    } catch (error) {
      console.error('Error enabling omnipresence:', error)
      toast({
        title: "Error",
        description: "Failed to enable omnipresent monitoring.",
        variant: "destructive",
      })
    }
  }, [currentContext])

  const disableOmnipresence = useCallback(() => {
    setOmnipresentMonitoring(false)
    if (guidanceIntervalRef.current) {
      clearInterval(guidanceIntervalRef.current)
    }

    toast({
      title: "Omnipresent Mode Disabled",
      description: "Manual guidance mode activated.",
      duration: 3000,
    })
  }, [])

  const requestGuidance = useCallback(async (
    mode: string = 'reactive',
    scope?: string
  ): Promise<ConciergeResponse | null> => {
    if (!serviceRef.current || !currentContext || isGeneratingGuidance) return null

    try {
      setIsGeneratingGuidance(true)
      const startTime = performance.now()

      const guidance = await serviceRef.current.generateContextualGuidance(
        currentContext,
        mode,
        scope
      )

      const endTime = performance.now()
      setResponseTimeMs(endTime - startTime)
      setLastGuidance(guidance)

      return guidance

    } catch (error) {
      console.error('Error requesting guidance:', error)
      toast({
        title: "Guidance Error",
        description: "Unable to generate guidance at this time.",
        variant: "destructive",
      })
      return null
    } finally {
      setIsGeneratingGuidance(false)
    }
  }, [currentContext, isGeneratingGuidance])

  const updateContext = useCallback((updates: Partial<PlatformContext>) => {
    if (!currentContext) return

    const updatedContext = { ...currentContext, ...updates }
    setCurrentContext(updatedContext)

    // Send real-time update
    if (enableRealTimeUpdates && serviceRef.current) {
      serviceRef.current.sendContextUpdate(updatedContext)
    }
  }, [currentContext, enableRealTimeUpdates])

  const learnFromDecision = useCallback(async (
    decision: Record<string, any>,
    outcome: Record<string, any>
  ) => {
    if (!serviceRef.current || !currentContext) return

    try {
      await serviceRef.current.learnFromDecision({
        decision,
        outcome,
        platform_context: currentContext
      })

      toast({
        title: "🧠 Learning Recorded",
        description: "Claude has learned from this decision to improve future recommendations.",
        duration: 4000,
      })

    } catch (error) {
      console.error('Error recording learning:', error)
    }
  }, [currentContext])

  const enableFieldMode = useCallback(async (locationData: Record<string, any>) => {
    setFieldModeEnabled(true)
    setFieldLocationData(locationData)

    if (!serviceRef.current || !currentContext) return

    try {
      await serviceRef.current.generateFieldAssistance({
        location_data: locationData,
        platform_context: { ...currentContext, device_type: 'mobile' }
      })

      toast({
        title: "📱 Field Mode Active",
        description: "Location-specific assistance enabled for property visits.",
        duration: 4000,
      })

    } catch (error) {
      console.error('Error enabling field mode:', error)
    }
  }, [currentContext])

  const disableFieldMode = useCallback(() => {
    setFieldModeEnabled(false)
    setFieldLocationData({})

    toast({
      title: "Field Mode Disabled",
      description: "Returned to standard guidance mode.",
      duration: 3000,
    })
  }, [])

  const enablePresentationMode = useCallback(async (clientProfile: Record<string, any>) => {
    setPresentationModeEnabled(true)
    setClientProfile(clientProfile)

    if (!serviceRef.current || !currentContext) return

    try {
      await serviceRef.current.providePresentationSupport({
        client_profile: clientProfile,
        presentation_context: {
          type: 'client_meeting',
          duration: '60 minutes',
          objectives: ['property_showcase', 'value_proposition', 'close_deal']
        },
        platform_context: { ...currentContext, user_role: 'client' }
      })

      toast({
        title: "🎭 Presentation Mode Active",
        description: "Client-safe guidance with talking points enabled.",
        duration: 4000,
      })

    } catch (error) {
      console.error('Error enabling presentation mode:', error)
    }
  }, [currentContext])

  const disablePresentationMode = useCallback(() => {
    setPresentationModeEnabled(false)
    setClientProfile({})

    toast({
      title: "Presentation Mode Disabled",
      description: "Returned to agent guidance mode.",
      duration: 3000,
    })
  }, [])

  const requestBotCoordination = useCallback(async (
    targetBot: string,
    reason: string,
    urgency: string = 'scheduled'
  ) => {
    if (!serviceRef.current || !currentContext) return

    try {
      await serviceRef.current.coordinateBotEcosystem({
        conversation_id: currentContext.session_id,
        target_bot: targetBot,
        reason,
        urgency,
        platform_context: currentContext
      })

      toast({
        title: "🤝 Bot Coordination Requested",
        description: `Handoff to ${targetBot} has been orchestrated.`,
        duration: 4000,
      })

    } catch (error) {
      console.error('Error requesting bot coordination:', error)
    }
  }, [currentContext])

  const requestRealTimeCoaching = useCallback(async (
    situation: Record<string, any>,
    urgency: string = 'medium'
  ) => {
    if (!serviceRef.current || !currentContext) return

    try {
      await serviceRef.current.provideRealTimeCoaching({
        conversation_id: currentContext.session_id,
        current_situation: situation,
        urgency,
        platform_context: currentContext
      })

      toast({
        title: "🎓 Real-time Coaching",
        description: "Tactical guidance has been provided for the current situation.",
        duration: 4000,
      })

    } catch (error) {
      console.error('Error requesting real-time coaching:', error)
    }
  }, [currentContext])

  // ========================================================================
  // CONTEXT VALUE
  // ========================================================================

  const contextValue: OmnipresentConciergeContextValue = {
    // Service Instance
    service: serviceRef.current!,
    isInitialized,
    isConnected,

    // Platform Intelligence
    currentContext,
    lastGuidance,
    isGeneratingGuidance,

    // Real-time Features
    omnipresentMonitoring,
    proactiveAssistance,
    contextualHints,

    // Performance & Metrics
    serviceMetrics,
    connectionQuality,
    responseTimeMs,

    // Actions
    enableOmnipresence,
    disableOmnipresence,
    requestGuidance,
    updateContext,
    learnFromDecision,

    // Field Work Actions
    enableFieldMode,
    disableFieldMode,

    // Presentation Mode Actions
    enablePresentationMode,
    disablePresentationMode,

    // Bot Coordination
    requestBotCoordination,
    requestRealTimeCoaching
  }

  return (
    <OmnipresentConciergeContext.Provider value={contextValue}>
      {children}
    </OmnipresentConciergeContext.Provider>
  )
}

// ============================================================================
// HOOK FOR CONSUMING CONTEXT
// ============================================================================

export function useOmnipresentConcierge() {
  const context = useContext(OmnipresentConciergeContext)

  if (!context) {
    throw new Error('useOmnipresentConcierge must be used within an OmnipresentConciergeProvider')
  }

  return context
}

// ============================================================================
// SPECIALIZED HOOKS FOR DIFFERENT USE CASES
// ============================================================================

/**
 * Hook for field agents working on mobile devices
 */
export function useFieldAgentConcierge() {
  const context = useOmnipresentConcierge()

  return {
    ...context,
    enableLocationTracking: (locationData: Record<string, any>) =>
      context.enableFieldMode(locationData),
    disableLocationTracking: () => context.disableFieldMode(),
    requestPropertyGuidance: (propertyData: Record<string, any>) =>
      context.requestGuidance('field_work', 'operational'),
    reportFieldDecision: (decision: Record<string, any>, outcome: Record<string, any>) =>
      context.learnFromDecision(decision, outcome)
  }
}

/**
 * Hook for executive dashboard and strategic guidance
 */
export function useExecutiveConcierge() {
  const context = useOmnipresentConcierge()

  return {
    ...context,
    requestStrategicGuidance: () => context.requestGuidance('executive', 'strategic'),
    requestRevenueOptimization: () => context.requestGuidance('proactive', 'platform_wide'),
    requestPipelineAnalysis: () => context.requestGuidance('executive', 'workflow'),
    requestMarketIntelligence: () => context.requestGuidance('executive', 'strategic')
  }
}

/**
 * Hook for client presentations and demos
 */
export function usePresentationConcierge() {
  const context = useOmnipresentConcierge()

  return {
    ...context,
    startClientPresentation: (clientProfile: Record<string, any>) =>
      context.enablePresentationMode(clientProfile),
    endClientPresentation: () => context.disablePresentationMode(),
    requestTalkingPoints: (topic: string) =>
      context.requestGuidance('presentation', 'strategic'),
    requestObjectionHandling: (objection: Record<string, any>) =>
      context.requestRealTimeCoaching(objection, 'high')
  }
}

export default OmnipresentConciergeProvider