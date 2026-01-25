// Agent Ecosystem State Management
// Centralized store for agent statuses, coordination, and real-time updates

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'
import { immer } from 'zustand/middleware/immer'
import { AgentStatus, AgentMetrics, PlatformActivity, AgentCoordination } from '@/lib/api/AgentEcosystemAPI'
import { CustomerJourney, JourneyAnalytics } from '@/lib/api/CustomerJourneyAPI'
import { PropertyAnalysis } from '@/lib/api/PropertyIntelligenceAPI'
import { ConciergeInsight, ProactiveSuggestion } from '@/lib/api/ClaudeConciergeAPI'

// Main Store State Interface
interface AgentEcosystemState {
  // Agents
  agents: Record<string, AgentStatus>
  agentMetrics: AgentMetrics | null
  selectedAgent: string | null

  // Platform Activities
  platformActivities: PlatformActivity[]

  // Coordination
  activeCoordinations: AgentCoordination[]
  handoffHistory: AgentCoordination[]

  // Customer Journeys
  journeys: Record<string, CustomerJourney>
  journeyAnalytics: JourneyAnalytics | null
  selectedJourney: string | null

  // Property Intelligence
  propertyAnalyses: Record<string, PropertyAnalysis>
  selectedProperty: string | null

  // Claude Concierge
  conciergeInsights: ConciergeInsight[]
  proactiveSuggestions: ProactiveSuggestion[]
  conciergeActive: boolean

  // UI State
  loading: {
    agents: boolean
    journeys: boolean
    properties: boolean
    concierge: boolean
  }
  errors: {
    agents: string | null
    journeys: string | null
    properties: string | null
    concierge: string | null
  }

  // Filters and Views
  filters: {
    agentTypes: string[]
    agentStatuses: string[]
    activityTypes: string[]
    journeyTypes: string[]
    timeRange: string
  }

  // Real-time Status
  realTimeEnabled: boolean
  lastUpdate: string | null
}

// Actions Interface
interface AgentEcosystemActions {
  // Agent Actions
  setAgents: (agents: AgentStatus[]) => void
  updateAgent: (agentId: string, updates: Partial<AgentStatus>) => void
  setAgentMetrics: (metrics: AgentMetrics) => void
  selectAgent: (agentId: string | null) => void

  // Platform Activity Actions
  setPlatformActivities: (activities: PlatformActivity[]) => void
  addPlatformActivity: (activity: PlatformActivity) => void
  markActivityResolved: (activityId: string) => void

  // Coordination Actions
  setActiveCoordinations: (coordinations: AgentCoordination[]) => void
  addCoordination: (coordination: AgentCoordination) => void
  updateCoordination: (coordinationId: string, updates: Partial<AgentCoordination>) => void
  completeCoordination: (coordinationId: string) => void

  // Journey Actions
  setJourneys: (journeys: CustomerJourney[]) => void
  addJourney: (journey: CustomerJourney) => void
  updateJourney: (journeyId: string, updates: Partial<CustomerJourney>) => void
  setJourneyAnalytics: (analytics: JourneyAnalytics) => void
  selectJourney: (journeyId: string | null) => void

  // Property Actions
  setPropertyAnalyses: (analyses: PropertyAnalysis[]) => void
  addPropertyAnalysis: (analysis: PropertyAnalysis) => void
  updatePropertyAnalysis: (propertyId: string, updates: Partial<PropertyAnalysis>) => void
  selectProperty: (propertyId: string | null) => void

  // Concierge Actions
  setConciergeInsights: (insights: ConciergeInsight[]) => void
  addConciergeInsight: (insight: ConciergeInsight) => void
  setProactiveSuggestions: (suggestions: ProactiveSuggestion[]) => void
  applySuggestion: (suggestionId: string) => void
  dismissSuggestion: (suggestionId: string) => void
  setConciergeActive: (active: boolean) => void

  // Loading and Error Actions
  setLoading: (key: keyof AgentEcosystemState['loading'], loading: boolean) => void
  setError: (key: keyof AgentEcosystemState['errors'], error: string | null) => void
  clearAllErrors: () => void

  // Filter Actions
  updateFilters: (updates: Partial<AgentEcosystemState['filters']>) => void
  resetFilters: () => void

  // Real-time Actions
  setRealTimeEnabled: (enabled: boolean) => void
  updateLastUpdate: () => void

  // Utility Actions
  reset: () => void
  getAgentsByType: (type: string) => AgentStatus[]
  getActiveAgents: () => AgentStatus[]
  getAgentCoordinations: (agentId: string) => AgentCoordination[]
  getJourneysByStatus: (status: CustomerJourney['status']) => CustomerJourney[]
  getHighPriorityActivities: () => PlatformActivity[]
}

// Combined Store Type
type AgentEcosystemStore = AgentEcosystemState & AgentEcosystemActions

// Default State
const defaultState: AgentEcosystemState = {
  agents: {},
  agentMetrics: null,
  selectedAgent: null,
  platformActivities: [],
  activeCoordinations: [],
  handoffHistory: [],
  journeys: {},
  journeyAnalytics: null,
  selectedJourney: null,
  propertyAnalyses: {},
  selectedProperty: null,
  conciergeInsights: [],
  proactiveSuggestions: [],
  conciergeActive: false,
  loading: {
    agents: false,
    journeys: false,
    properties: false,
    concierge: false,
  },
  errors: {
    agents: null,
    journeys: null,
    properties: null,
    concierge: null,
  },
  filters: {
    agentTypes: [],
    agentStatuses: [],
    activityTypes: [],
    journeyTypes: [],
    timeRange: '24h',
  },
  realTimeEnabled: true,
  lastUpdate: null,
}

// Create the store
export const useAgentEcosystemStore = create<AgentEcosystemStore>()(
  subscribeWithSelector(
    immer((set, get) => ({
      ...defaultState,

      // Agent Actions
      setAgents: (agents) => set((state) => {
        state.agents = agents.reduce((acc, agent) => {
          acc[agent.id] = agent
          return acc
        }, {} as Record<string, AgentStatus>)
        state.lastUpdate = new Date().toISOString()
      }),

      updateAgent: (agentId, updates) => set((state) => {
        if (state.agents[agentId]) {
          Object.assign(state.agents[agentId], updates)
          state.lastUpdate = new Date().toISOString()
        }
      }),

      setAgentMetrics: (metrics) => set((state) => {
        state.agentMetrics = metrics
      }),

      selectAgent: (agentId) => set((state) => {
        state.selectedAgent = agentId
      }),

      // Platform Activity Actions
      setPlatformActivities: (activities) => set((state) => {
        state.platformActivities = activities
        state.lastUpdate = new Date().toISOString()
      }),

      addPlatformActivity: (activity) => set((state) => {
        state.platformActivities.unshift(activity)
        // Keep only latest 1000 activities
        if (state.platformActivities.length > 1000) {
          state.platformActivities = state.platformActivities.slice(0, 1000)
        }
        state.lastUpdate = new Date().toISOString()
      }),

      markActivityResolved: (activityId) => set((state) => {
        const activity = state.platformActivities.find(a => a.id === activityId)
        if (activity) {
          activity.status = 'resolved'
        }
      }),

      // Coordination Actions
      setActiveCoordinations: (coordinations) => set((state) => {
        state.activeCoordinations = coordinations
        state.lastUpdate = new Date().toISOString()
      }),

      addCoordination: (coordination) => set((state) => {
        state.activeCoordinations.push(coordination)
        state.lastUpdate = new Date().toISOString()
      }),

      updateCoordination: (coordinationId, updates) => set((state) => {
        const coordination = state.activeCoordinations.find(c => c.id === coordinationId)
        if (coordination) {
          Object.assign(coordination, updates)
        }
      }),

      completeCoordination: (coordinationId) => set((state) => {
        const index = state.activeCoordinations.findIndex(c => c.id === coordinationId)
        if (index !== -1) {
          const completed = state.activeCoordinations.splice(index, 1)[0]
          completed.status = 'completed'
          state.handoffHistory.unshift(completed)
          // Keep only latest 500 in history
          if (state.handoffHistory.length > 500) {
            state.handoffHistory = state.handoffHistory.slice(0, 500)
          }
        }
      }),

      // Journey Actions
      setJourneys: (journeys) => set((state) => {
        state.journeys = journeys.reduce((acc, journey) => {
          acc[journey.id] = journey
          return acc
        }, {} as Record<string, CustomerJourney>)
        state.lastUpdate = new Date().toISOString()
      }),

      addJourney: (journey) => set((state) => {
        state.journeys[journey.id] = journey
        state.lastUpdate = new Date().toISOString()
      }),

      updateJourney: (journeyId, updates) => set((state) => {
        if (state.journeys[journeyId]) {
          Object.assign(state.journeys[journeyId], updates)
          state.lastUpdate = new Date().toISOString()
        }
      }),

      setJourneyAnalytics: (analytics) => set((state) => {
        state.journeyAnalytics = analytics
      }),

      selectJourney: (journeyId) => set((state) => {
        state.selectedJourney = journeyId
      }),

      // Property Actions
      setPropertyAnalyses: (analyses) => set((state) => {
        state.propertyAnalyses = analyses.reduce((acc, analysis) => {
          acc[analysis.propertyId] = analysis
          return acc
        }, {} as Record<string, PropertyAnalysis>)
        state.lastUpdate = new Date().toISOString()
      }),

      addPropertyAnalysis: (analysis) => set((state) => {
        state.propertyAnalyses[analysis.propertyId] = analysis
        state.lastUpdate = new Date().toISOString()
      }),

      updatePropertyAnalysis: (propertyId, updates) => set((state) => {
        if (state.propertyAnalyses[propertyId]) {
          Object.assign(state.propertyAnalyses[propertyId], updates)
          state.lastUpdate = new Date().toISOString()
        }
      }),

      selectProperty: (propertyId) => set((state) => {
        state.selectedProperty = propertyId
      }),

      // Concierge Actions
      setConciergeInsights: (insights) => set((state) => {
        state.conciergeInsights = insights
        state.lastUpdate = new Date().toISOString()
      }),

      addConciergeInsight: (insight) => set((state) => {
        state.conciergeInsights.unshift(insight)
        // Keep only latest 100 insights
        if (state.conciergeInsights.length > 100) {
          state.conciergeInsights = state.conciergeInsights.slice(0, 100)
        }
      }),

      setProactiveSuggestions: (suggestions) => set((state) => {
        state.proactiveSuggestions = suggestions
      }),

      applySuggestion: (suggestionId) => set((state) => {
        state.proactiveSuggestions = state.proactiveSuggestions.filter(s => s.id !== suggestionId)
      }),

      dismissSuggestion: (suggestionId) => set((state) => {
        state.proactiveSuggestions = state.proactiveSuggestions.filter(s => s.id !== suggestionId)
      }),

      setConciergeActive: (active) => set((state) => {
        state.conciergeActive = active
      }),

      // Loading and Error Actions
      setLoading: (key, loading) => set((state) => {
        state.loading[key] = loading
      }),

      setError: (key, error) => set((state) => {
        state.errors[key] = error
      }),

      clearAllErrors: () => set((state) => {
        state.errors = {
          agents: null,
          journeys: null,
          properties: null,
          concierge: null,
        }
      }),

      // Filter Actions
      updateFilters: (updates) => set((state) => {
        Object.assign(state.filters, updates)
      }),

      resetFilters: () => set((state) => {
        state.filters = {
          agentTypes: [],
          agentStatuses: [],
          activityTypes: [],
          journeyTypes: [],
          timeRange: '24h',
        }
      }),

      // Real-time Actions
      setRealTimeEnabled: (enabled) => set((state) => {
        state.realTimeEnabled = enabled
      }),

      updateLastUpdate: () => set((state) => {
        state.lastUpdate = new Date().toISOString()
      }),

      // Utility Actions
      reset: () => set(() => ({ ...defaultState })),

      getAgentsByType: (type) => {
        const state = get()
        return Object.values(state.agents).filter(agent => agent.type === type)
      },

      getActiveAgents: () => {
        const state = get()
        return Object.values(state.agents).filter(agent => agent.status === 'active')
      },

      getAgentCoordinations: (agentId) => {
        const state = get()
        return state.activeCoordinations.filter(
          coord => coord.fromAgent === agentId || coord.toAgent === agentId
        )
      },

      getJourneysByStatus: (status) => {
        const state = get()
        return Object.values(state.journeys).filter(journey => journey.status === status)
      },

      getHighPriorityActivities: () => {
        const state = get()
        return state.platformActivities.filter(activity =>
          activity.priority === 'urgent' || activity.priority === 'high'
        )
      },
    }))
  )
)

// Selector Hooks for optimized re-renders
export const useAgents = () => useAgentEcosystemStore(state => state.agents)
export const useSelectedAgent = () => useAgentEcosystemStore(state =>
  state.selectedAgent ? state.agents[state.selectedAgent] : null
)
export const useAgentMetrics = () => useAgentEcosystemStore(state => state.agentMetrics)
export const usePlatformActivities = () => useAgentEcosystemStore(state => state.platformActivities)
export const useActiveCoordinations = () => useAgentEcosystemStore(state => state.activeCoordinations)
export const useJourneys = () => useAgentEcosystemStore(state => state.journeys)
export const useSelectedJourney = () => useAgentEcosystemStore(state =>
  state.selectedJourney ? state.journeys[state.selectedJourney] : null
)
export const usePropertyAnalyses = () => useAgentEcosystemStore(state => state.propertyAnalyses)
export const useConciergeInsights = () => useAgentEcosystemStore(state => state.conciergeInsights)
export const useProactiveSuggestions = () => useAgentEcosystemStore(state => state.proactiveSuggestions)
export const useLoadingState = () => useAgentEcosystemStore(state => state.loading)
export const useErrorState = () => useAgentEcosystemStore(state => state.errors)
export const useFilters = () => useAgentEcosystemStore(state => state.filters)

// Computed Selectors
export const useAgentStats = () => useAgentEcosystemStore(state => {
  const agents = Object.values(state.agents)
  return {
    total: agents.length,
    active: agents.filter(a => a.status === 'active').length,
    processing: agents.filter(a => a.status === 'processing').length,
    standby: agents.filter(a => a.status === 'standby').length,
    offline: agents.filter(a => a.status === 'offline').length,
    primary: agents.filter(a => a.type === 'primary').length,
    secondary: agents.filter(a => a.type === 'secondary').length,
    support: agents.filter(a => a.type === 'support').length,
    intelligence: agents.filter(a => a.type === 'intelligence').length,
  }
})

export const useJourneyStats = () => useAgentEcosystemStore(state => {
  const journeys = Object.values(state.journeys)
  return {
    total: journeys.length,
    active: journeys.filter(j => j.status === 'active').length,
    completed: journeys.filter(j => j.status === 'completed').length,
    paused: journeys.filter(j => j.status === 'paused').length,
    abandoned: journeys.filter(j => j.status === 'abandoned').length,
    firstTimeBuyer: journeys.filter(j => j.type === 'FIRST_TIME_BUYER').length,
    investor: journeys.filter(j => j.type === 'INVESTOR').length,
    seller: journeys.filter(j => j.type === 'SELLER').length,
    commercial: journeys.filter(j => j.type === 'COMMERCIAL').length,
  }
})

export default useAgentEcosystemStore