// Agent Ecosystem Integration Hook
// Comprehensive hook that integrates APIs, WebSocket, and state management

import { useEffect, useCallback, useRef } from 'react'
import { useAgentEcosystemStore } from '@/store/agentEcosystemStore'
import { useRealtime } from '@/lib/providers/RealtimeProvider'
import { agentEcosystemAPI } from '@/lib/api/AgentEcosystemAPI'
import { claudeConciergeAPI } from '@/lib/api/ClaudeConciergeAPI'
import { customerJourneyAPI } from '@/lib/api/CustomerJourneyAPI'
import { propertyIntelligenceAPI } from '@/lib/api/PropertyIntelligenceAPI'

interface IntegrationOptions {
  autoRefresh?: boolean
  refreshInterval?: number
  enableRealTime?: boolean
  initializeOnMount?: boolean
}

export function useAgentEcosystemIntegration(options: IntegrationOptions = {}) {
  const {
    autoRefresh = true,
    refreshInterval = 30000, // 30 seconds
    enableRealTime = true,
    initializeOnMount = true,
  } = options

  // Store actions
  const store = useAgentEcosystemStore()

  // Real-time connection
  const realtime = useRealtime()

  // Refs for intervals
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const initializeRef = useRef(false)

  // Initialize all data
  const initialize = useCallback(async () => {
    if (initializeRef.current) return
    initializeRef.current = true

    console.log('🚀 Initializing Agent Ecosystem Integration...')

    try {
      // Set loading states
      store.setLoading('agents', true)
      store.setLoading('journeys', true)
      store.setLoading('concierge', true)

      // Clear previous errors
      store.clearAllErrors()

      // Fetch all initial data in parallel
      const [
        agentStatuses,
        agentMetrics,
        platformActivities,
        activeCoordinations,
        journeysResponse,
        journeyAnalytics,
        conciergeInsights,
        proactiveSuggestions,
      ] = await Promise.allSettled([
        agentEcosystemAPI.getAgentStatuses(),
        agentEcosystemAPI.getAgentMetrics(),
        agentEcosystemAPI.getPlatformActivities(100),
        agentEcosystemAPI.getActiveCoordinations(),
        customerJourneyAPI.getJourneys({ limit: 50 }),
        customerJourneyAPI.getAnalytics(),
        claudeConciergeAPI.getRealtimeInsights(),
        claudeConciergeAPI.getProactiveSuggestions(),
      ])

      // Update agents data
      if (agentStatuses.status === 'fulfilled') {
        store.setAgents(agentStatuses.value)
        console.log(`✅ Loaded ${agentStatuses.value.length} agents`)
      } else {
        console.error('❌ Failed to load agents:', agentStatuses.reason)
        store.setError('agents', 'Failed to load agent statuses')
      }

      if (agentMetrics.status === 'fulfilled') {
        store.setAgentMetrics(agentMetrics.value)
      }

      // Update platform activities
      if (platformActivities.status === 'fulfilled') {
        store.setPlatformActivities(platformActivities.value)
        console.log(`✅ Loaded ${platformActivities.value.length} platform activities`)
      }

      // Update coordinations
      if (activeCoordinations.status === 'fulfilled') {
        store.setActiveCoordinations(activeCoordinations.value)
        console.log(`✅ Loaded ${activeCoordinations.value.length} active coordinations`)
      }

      // Update journeys data
      if (journeysResponse.status === 'fulfilled') {
        store.setJourneys(journeysResponse.value.journeys)
        console.log(`✅ Loaded ${journeysResponse.value.journeys.length} customer journeys`)
        store.setError('journeys', null)
      } else {
        console.error('❌ Failed to load journeys:', journeysResponse.reason)
        store.setError('journeys', 'Failed to load customer journeys')
      }

      if (journeyAnalytics.status === 'fulfilled') {
        store.setJourneyAnalytics(journeyAnalytics.value)
      }

      // Update concierge data
      if (conciergeInsights.status === 'fulfilled') {
        store.setConciergeInsights(conciergeInsights.value)
        console.log(`✅ Loaded ${conciergeInsights.value.length} concierge insights`)
        store.setError('concierge', null)
      } else {
        console.error('❌ Failed to load concierge insights:', conciergeInsights.reason)
        store.setError('concierge', 'Failed to load concierge insights')
      }

      if (proactiveSuggestions.status === 'fulfilled') {
        store.setProactiveSuggestions(proactiveSuggestions.value)
        console.log(`✅ Loaded ${proactiveSuggestions.value.length} proactive suggestions`)
      }

      // Mark concierge as active
      store.setConciergeActive(true)

      console.log('🎉 Agent Ecosystem Integration initialized successfully!')

    } catch (error) {
      console.error('❌ Failed to initialize agent ecosystem:', error)
      store.setError('agents', 'Failed to initialize agent ecosystem')
    } finally {
      store.setLoading('agents', false)
      store.setLoading('journeys', false)
      store.setLoading('concierge', false)
    }
  }, [store])

  // Refresh specific data types
  const refreshAgents = useCallback(async () => {
    try {
      const [statuses, metrics] = await Promise.all([
        agentEcosystemAPI.getAgentStatuses(),
        agentEcosystemAPI.getAgentMetrics(),
      ])
      store.setAgents(statuses)
      store.setAgentMetrics(metrics)
    } catch (error) {
      console.error('Failed to refresh agents:', error)
    }
  }, [store])

  const refreshPlatformActivities = useCallback(async () => {
    try {
      const activities = await agentEcosystemAPI.getPlatformActivities(100)
      store.setPlatformActivities(activities)
    } catch (error) {
      console.error('Failed to refresh platform activities:', error)
    }
  }, [store])

  const refreshJourneys = useCallback(async () => {
    try {
      const [journeysResponse, analytics] = await Promise.all([
        customerJourneyAPI.getJourneys({ limit: 50 }),
        customerJourneyAPI.getAnalytics(),
      ])
      store.setJourneys(journeysResponse.journeys)
      store.setJourneyAnalytics(analytics)
    } catch (error) {
      console.error('Failed to refresh journeys:', error)
    }
  }, [store])

  const refreshConcierge = useCallback(async () => {
    try {
      const [insights, suggestions] = await Promise.all([
        claudeConciergeAPI.getRealtimeInsights(),
        claudeConciergeAPI.getProactiveSuggestions(),
      ])
      store.setConciergeInsights(insights)
      store.setProactiveSuggestions(suggestions)
    } catch (error) {
      console.error('Failed to refresh concierge data:', error)
    }
  }, [store])

  // Full refresh
  const refresh = useCallback(async () => {
    console.log('🔄 Refreshing all agent ecosystem data...')
    await Promise.all([
      refreshAgents(),
      refreshPlatformActivities(),
      refreshJourneys(),
      refreshConcierge(),
    ])
    store.updateLastUpdate()
    console.log('✅ Agent ecosystem data refreshed')
  }, [refreshAgents, refreshPlatformActivities, refreshJourneys, refreshConcierge, store])

  // Setup real-time event handlers
  useEffect(() => {
    if (!enableRealTime || !realtime.isConnected) return

    console.log('🔗 Setting up real-time event subscriptions...')

    const unsubscribeFunctions: Array<() => void> = []

    // Agent status updates
    unsubscribeFunctions.push(
      realtime.subscribe('agent_status_changed', (event) => {
        console.log('📡 Agent status update:', event.data)
        const { agentId, status, responseTime, currentTask, accuracy } = event.data
        store.updateAgent(agentId, {
          status,
          responseTime,
          currentTask,
          accuracy,
          lastActivity: event.timestamp,
        })
      })
    )

    // Agent coordination events
    unsubscribeFunctions.push(
      realtime.subscribe(['agent_coordination', 'handoff_initiated', 'handoff_completed'], (event) => {
        console.log('🤝 Coordination update:', event.data)

        if (event.type === 'handoff_initiated') {
          store.addCoordination(event.data)
        } else if (event.type === 'handoff_completed') {
          store.completeCoordination(event.data.coordinationId)
        } else if (event.type === 'agent_coordination') {
          store.updateCoordination(event.data.id, event.data)
        }
      })
    )

    // Journey updates
    unsubscribeFunctions.push(
      realtime.subscribe('journey_step_completed', (event) => {
        console.log('📋 Journey step completed:', event.data)
        const { journeyId, stepId, completionData } = event.data

        // Update the journey step
        const journey = store.journeys[journeyId]
        if (journey) {
          const updatedSteps = journey.steps.map(step =>
            step.id === stepId
              ? { ...step, status: 'completed' as const, endTime: event.timestamp, output: completionData }
              : step
          )

          // Calculate new progress
          const completedSteps = updatedSteps.filter(s => s.status === 'completed').length
          const completionPercentage = Math.round((completedSteps / updatedSteps.length) * 100)

          store.updateJourney(journeyId, {
            steps: updatedSteps,
            completionPercentage,
            currentStep: Math.min(completedSteps, updatedSteps.length - 1),
          })
        }
      })
    )

    // Property analysis updates
    unsubscribeFunctions.push(
      realtime.subscribe('property_analysis_complete', (event) => {
        console.log('🏠 Property analysis completed:', event.data)
        store.addPropertyAnalysis(event.data)
      })
    )

    // Platform alerts
    unsubscribeFunctions.push(
      realtime.subscribe('platform_alert', (event) => {
        console.log('⚠️ Platform alert:', event.data)
        store.addPlatformActivity({
          id: event.id,
          type: 'system_alert',
          title: event.data.title || 'Platform Alert',
          description: event.data.message,
          timestamp: event.timestamp,
          priority: event.priority,
          status: 'active',
          metadata: event.data,
        })
      })
    )

    // Concierge insights
    unsubscribeFunctions.push(
      realtime.subscribe('concierge_insight', (event) => {
        console.log('💡 Concierge insight:', event.data)
        store.addConciergeInsight(event.data)
      })
    )

    console.log(`✅ Subscribed to ${unsubscribeFunctions.length} real-time event types`)

    // Cleanup function
    return () => {
      console.log('🧹 Cleaning up real-time subscriptions...')
      unsubscribeFunctions.forEach(unsubscribe => unsubscribe())
    }
  }, [enableRealTime, realtime.isConnected, store])

  // Setup auto-refresh
  useEffect(() => {
    if (!autoRefresh) return

    console.log(`⏰ Setting up auto-refresh every ${refreshInterval}ms`)

    refreshIntervalRef.current = setInterval(() => {
      // Only refresh if we're not getting real-time updates
      if (!realtime.isConnected) {
        refresh()
      } else {
        // Just refresh metrics and analytics when real-time is active
        Promise.all([
          agentEcosystemAPI.getAgentMetrics().then(store.setAgentMetrics).catch(console.error),
          customerJourneyAPI.getAnalytics().then(store.setJourneyAnalytics).catch(console.error),
        ])
      }
    }, refreshInterval)

    return () => {
      if (refreshIntervalRef.current) {
        clearInterval(refreshIntervalRef.current)
        refreshIntervalRef.current = null
      }
    }
  }, [autoRefresh, refreshInterval, realtime.isConnected, refresh, store])

  // Initialize on mount
  useEffect(() => {
    if (initializeOnMount) {
      initialize()
    }
  }, [initializeOnMount, initialize])

  // Agent management functions
  const pauseAgent = useCallback(async (agentId: string) => {
    try {
      await agentEcosystemAPI.pauseAgent(agentId)
      store.updateAgent(agentId, { status: 'standby' })
      console.log(`⏸️ Agent ${agentId} paused`)
    } catch (error) {
      console.error(`Failed to pause agent ${agentId}:`, error)
      throw error
    }
  }, [store])

  const resumeAgent = useCallback(async (agentId: string) => {
    try {
      await agentEcosystemAPI.resumeAgent(agentId)
      store.updateAgent(agentId, { status: 'active' })
      console.log(`▶️ Agent ${agentId} resumed`)
    } catch (error) {
      console.error(`Failed to resume agent ${agentId}:`, error)
      throw error
    }
  }, [store])

  const restartAgent = useCallback(async (agentId: string) => {
    try {
      await agentEcosystemAPI.restartAgent(agentId)
      console.log(`🔄 Agent ${agentId} restarted`)
      // Refresh agent status after restart
      setTimeout(() => refreshAgents(), 1000)
    } catch (error) {
      console.error(`Failed to restart agent ${agentId}:`, error)
      throw error
    }
  }, [refreshAgents])

  // Journey management functions
  const createJourney = useCallback(async (journeyData: Parameters<typeof customerJourneyAPI.createJourney>[0]) => {
    try {
      const newJourney = await customerJourneyAPI.createJourney(journeyData)
      store.addJourney(newJourney)
      console.log(`🆕 Journey created: ${newJourney.id}`)
      return newJourney
    } catch (error) {
      console.error('Failed to create journey:', error)
      throw error
    }
  }, [store])

  const updateJourney = useCallback(async (journeyId: string, updates: Parameters<typeof customerJourneyAPI.updateJourney>[1]) => {
    try {
      const updatedJourney = await customerJourneyAPI.updateJourney(journeyId, updates)
      store.updateJourney(journeyId, updatedJourney)
      console.log(`📝 Journey updated: ${journeyId}`)
      return updatedJourney
    } catch (error) {
      console.error(`Failed to update journey ${journeyId}:`, error)
      throw error
    }
  }, [store])

  // Concierge functions
  const sendConciergeMessage = useCallback(async (message: string) => {
    try {
      const response = await claudeConciergeAPI.sendMessage(message)
      console.log('🤖 Concierge response received')

      // Update suggestions if any
      if (response.suggestions) {
        store.setProactiveSuggestions(response.suggestions)
      }

      // Update insights if any
      if (response.insights) {
        response.insights.forEach(insight => store.addConciergeInsight(insight))
      }

      return response
    } catch (error) {
      console.error('Failed to send concierge message:', error)
      throw error
    }
  }, [store])

  const applySuggestion = useCallback(async (suggestionId: string) => {
    try {
      const result = await claudeConciergeAPI.applySuggestion(suggestionId)
      store.applySuggestion(suggestionId)
      console.log(`✅ Suggestion applied: ${suggestionId}`)
      return result
    } catch (error) {
      console.error(`Failed to apply suggestion ${suggestionId}:`, error)
      throw error
    }
  }, [store])

  return {
    // Initialization
    initialize,
    refresh,

    // Specific refreshers
    refreshAgents,
    refreshJourneys,
    refreshConcierge,

    // Agent management
    pauseAgent,
    resumeAgent,
    restartAgent,

    // Journey management
    createJourney,
    updateJourney,

    // Concierge
    sendConciergeMessage,
    applySuggestion,

    // Status
    isInitialized: initializeRef.current,
    isConnected: realtime.isConnected,
    lastUpdate: store.lastUpdate,
  }
}

export default useAgentEcosystemIntegration