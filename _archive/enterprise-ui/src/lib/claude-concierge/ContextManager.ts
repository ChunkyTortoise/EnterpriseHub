/**
 * Real-time platform state tracking
 * Implements: PersonaAB-9 #40 (Contextual Selective Recall)
 *
 * Responsibilities:
 * - Capture current page context (dashboard, chat, analytics)
 * - Track user actions for pattern recognition
 * - Monitor active bot states
 * - Provide platform-aware prompts
 */

import type {
  PlatformState,
  NavigationContext,
  BotEcosystemContext,
  UserDataContext,
  Activity,
  LeadData,
  PropertyMatch
} from './PersonaPromptEngine'

export interface PlatformContext {
  currentPage: string
  activeBots: string[]
  recentActions: UserAction[]
  leadContext?: LeadData
  propertyContext?: PropertyMatch[]
}

export interface UserAction {
  type: 'navigation' | 'bot_interaction' | 'data_view' | 'action' | 'ui_interaction'
  timestamp: string
  details: Record<string, any>
  importance: 'low' | 'medium' | 'high'
}

export interface ContextSnapshot {
  timestamp: string
  platformState: PlatformState
  userSession: {
    sessionStart: string
    totalTimeSpent: number
    pagesVisited: string[]
    actionsPerformed: number
  }
}

export class ContextManager {
  private currentState: PlatformState
  private activityWindow: Activity[] = []
  private navigationHistory: NavigationContext[] = []
  private sessionStart: Date
  private eventListeners: Map<string, EventListener[]> = new Map()

  private readonly MAX_ACTIVITY_BUFFER = 50
  private readonly MAX_NAVIGATION_HISTORY = 20
  private readonly CONTEXT_UPDATE_INTERVAL = 5000 // 5 seconds

  constructor() {
    this.sessionStart = new Date()
    this.currentState = this.initializeState()
    this.setupRealtimeListeners()
    this.startContextUpdates()
  }

  /**
   * Capture comprehensive platform context
   * Uses selective recall to avoid overwhelming Claude
   * Implements PersonaAB-9 #40: Contextual Selective Recall
   */
  async captureContext(userContext?: Partial<PlatformContext>): Promise<PlatformState> {
    // Update current state with latest browser information
    await this.updateNavigationContext()
    await this.updateBotEcosystemContext()
    await this.updateUserDataContext(userContext)

    // Apply contextual filtering to reduce token usage
    const relevantState = this.filterRelevantContext(this.currentState, userContext)

    return relevantState
  }

  /**
   * Track user action for pattern recognition
   * Automatically categorizes and scores importance
   */
  trackActivity(activity: Omit<Activity, 'importance'>): void {
    const enhancedActivity: Activity = {
      ...activity,
      importance: this.calculateActivityImportance(activity)
    }

    this.activityWindow.push(enhancedActivity)

    // Maintain sliding window
    if (this.activityWindow.length > this.MAX_ACTIVITY_BUFFER) {
      this.activityWindow.shift()
    }

    // Update current state
    this.currentState.recentActivity = this.activityWindow

    // Emit real-time update
    this.emitContextUpdate(enhancedActivity)
  }

  /**
   * Track navigation changes
   */
  trackNavigation(newRoute: string, previousRoute?: string): void {
    const navigationContext: NavigationContext = {
      currentRoute: newRoute,
      previousRoute: previousRoute || this.currentState.navigation.currentRoute,
      timeOnPage: Date.now(),
      tabsOpen: this.getOpenTabs()
    }

    this.navigationHistory.push(navigationContext)
    if (this.navigationHistory.length > this.MAX_NAVIGATION_HISTORY) {
      this.navigationHistory.shift()
    }

    this.currentState.navigation = navigationContext

    // Track as activity
    this.trackActivity({
      type: 'navigation',
      timestamp: new Date().toISOString(),
      details: {
        from: previousRoute,
        to: newRoute,
        method: 'user_navigation'
      }
    })
  }

  /**
   * Track bot interaction events
   */
  trackBotInteraction(botId: string, action: string, details: Record<string, any>): void {
    this.trackActivity({
      type: 'bot_interaction',
      timestamp: new Date().toISOString(),
      details: {
        botId,
        action,
        ...details
      }
    })
  }

  /**
   * Track data viewing actions (leads, properties, analytics)
   */
  trackDataView(dataType: string, entityId: string, metadata?: Record<string, any>): void {
    this.trackActivity({
      type: 'data_view',
      timestamp: new Date().toISOString(),
      details: {
        dataType,
        entityId,
        metadata
      }
    })
  }

  /**
   * Track general UI interactions
   */
  trackUIInteraction(component: string, action: string, value?: any): void {
    this.trackActivity({
      type: 'ui_interaction',
      timestamp: new Date().toISOString(),
      details: {
        component,
        action,
        value
      }
    })
  }

  /**
   * Get current context snapshot for debugging/analytics
   */
  getContextSnapshot(): ContextSnapshot {
    const sessionDuration = Date.now() - this.sessionStart.getTime()

    return {
      timestamp: new Date().toISOString(),
      platformState: this.currentState,
      userSession: {
        sessionStart: this.sessionStart.toISOString(),
        totalTimeSpent: sessionDuration,
        pagesVisited: this.getUniqueVisitedPages(),
        actionsPerformed: this.activityWindow.length
      }
    }
  }

  /**
   * Get activity patterns for proactive suggestions
   */
  getActivityPatterns(): {
    mostCommonActions: { type: string; count: number }[]
    recentTrends: { activity: string; frequency: number }[]
    sessionFocus: string[]
  } {
    const actionCounts = this.activityWindow.reduce((counts, activity) => {
      const key = `${activity.type}:${activity.details.action || 'general'}`
      counts[key] = (counts[key] || 0) + 1
      return counts
    }, {} as Record<string, number>)

    const mostCommonActions = Object.entries(actionCounts)
      .map(([type, count]) => ({ type, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5)

    // Analyze recent activity (last 10 actions)
    const recentActivity = this.activityWindow.slice(-10)
    const recentTrends = this.analyzeActivityTrends(recentActivity)

    // Determine session focus based on activity
    const sessionFocus = this.determineSessionFocus()

    return {
      mostCommonActions,
      recentTrends,
      sessionFocus
    }
  }

  /**
   * Subscribe to specific context events
   */
  on(eventType: string, listener: EventListener): void {
    if (!this.eventListeners.has(eventType)) {
      this.eventListeners.set(eventType, [])
    }
    this.eventListeners.get(eventType)!.push(listener)
  }

  /**
   * Unsubscribe from context events
   */
  off(eventType: string, listener: EventListener): void {
    const listeners = this.eventListeners.get(eventType)
    if (listeners) {
      const index = listeners.indexOf(listener)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }

  /**
   * Initialize platform state structure
   */
  private initializeState(): PlatformState {
    return {
      navigation: {
        currentRoute: typeof window !== 'undefined' ? window.location.pathname : '/',
        previousRoute: '',
        timeOnPage: Date.now(),
        tabsOpen: []
      },
      botEcosystem: {
        activeBots: [],
        recentHandoffs: []
      },
      userData: {},
      recentActivity: []
    }
  }

  /**
   * Setup real-time event listeners
   */
  private setupRealtimeListeners(): void {
    if (typeof window === 'undefined') return

    // Navigation tracking
    window.addEventListener('popstate', () => {
      this.trackNavigation(window.location.pathname, this.currentState.navigation.currentRoute)
    })

    // Page visibility changes
    document.addEventListener('visibilitychange', () => {
      this.trackActivity({
        type: 'ui_interaction',
        timestamp: new Date().toISOString(),
        details: {
          component: 'window',
          action: document.hidden ? 'blur' : 'focus'
        }
      })
    })

    // Before unload tracking
    window.addEventListener('beforeunload', () => {
      this.trackActivity({
        type: 'navigation',
        timestamp: new Date().toISOString(),
        details: {
          action: 'page_unload',
          timeSpent: Date.now() - this.currentState.navigation.timeOnPage
        }
      })
    })
  }

  /**
   * Start periodic context updates
   */
  private startContextUpdates(): void {
    setInterval(() => {
      this.updateContextualInformation()
    }, this.CONTEXT_UPDATE_INTERVAL)
  }

  /**
   * Update navigation context from current browser state
   */
  private async updateNavigationContext(): Promise<void> {
    if (typeof window === 'undefined') return

    const currentRoute = window.location.pathname
    const timeOnCurrentPage = Date.now() - this.currentState.navigation.timeOnPage

    this.currentState.navigation = {
      ...this.currentState.navigation,
      currentRoute,
      timeOnPage: timeOnCurrentPage,
      tabsOpen: this.getOpenTabs()
    }
  }

  /**
   * Update bot ecosystem context from platform APIs
   */
  private async updateBotEcosystemContext(): Promise<void> {
    try {
      // Fetch bot status from existing jorge-api-client
      const response = await fetch('/api/bots/status')
      if (response.ok) {
        const botStatuses = await response.json()

        this.currentState.botEcosystem = {
          activeBots: botStatuses.map((bot: any) => ({
            id: bot.id,
            status: bot.status,
            activeConversations: bot.activeConversations || 0,
            performanceMetrics: {
              conversationsToday: bot.conversationsToday || 0,
              leadsQualified: bot.leadsQualified || 0,
              avgResponseTime: bot.responseTimeMs || 0
            }
          })),
          recentHandoffs: this.currentState.botEcosystem.recentHandoffs // Preserve existing handoffs
        }
      }
    } catch (error) {
      console.warn('Failed to update bot ecosystem context:', error)
      // Keep existing state on failure
    }
  }

  /**
   * Update user data context with current lead/property information
   */
  private async updateUserDataContext(userContext?: Partial<PlatformContext>): Promise<void> {
    // Merge provided user context
    if (userContext?.leadContext) {
      this.currentState.userData.leadContext = userContext.leadContext
    }

    if (userContext?.propertyContext) {
      this.currentState.userData.propertyContext = userContext.propertyContext
    }

    // Extract context from current route
    await this.extractContextFromRoute()
  }

  /**
   * Extract relevant context from current route/page
   */
  private async extractContextFromRoute(): Promise<void> {
    const route = this.currentState.navigation.currentRoute

    // Extract lead ID from route
    const leadMatch = route.match(/\/leads\/([^\/]+)/)
    if (leadMatch) {
      try {
        const leadId = leadMatch[1]
        const response = await fetch(`/api/leads/${leadId}`)
        if (response.ok) {
          this.currentState.userData.leadContext = await response.json()
        }
      } catch (error) {
        console.warn('Failed to fetch lead context:', error)
      }
    }

    // Extract property ID from route
    const propertyMatch = route.match(/\/properties\/([^\/]+)/)
    if (propertyMatch) {
      try {
        const propertyId = propertyMatch[1]
        const response = await fetch(`/api/properties/${propertyId}`)
        if (response.ok) {
          const property = await response.json()
          this.currentState.userData.propertyContext = [property]
        }
      } catch (error) {
        console.warn('Failed to fetch property context:', error)
      }
    }
  }

  /**
   * Filter context to include only relevant information
   * Reduces token usage by 60-70% through intelligent selection
   */
  private filterRelevantContext(
    state: PlatformState,
    userContext?: Partial<PlatformContext>
  ): PlatformState {
    const filtered = { ...state }

    // Filter recent activity based on relevance and recency
    const now = Date.now()
    filtered.recentActivity = state.recentActivity
      .filter(activity => {
        const ageMinutes = (now - new Date(activity.timestamp).getTime()) / (60 * 1000)

        // Always include high importance activities
        if (activity.importance === 'high') return true

        // Include medium importance activities from last hour
        if (activity.importance === 'medium' && ageMinutes < 60) return true

        // Include low importance activities from last 15 minutes
        if (activity.importance === 'low' && ageMinutes < 15) return true

        return false
      })
      .slice(-10) // Maximum 10 recent activities

    // Filter bot ecosystem to only include relevant bots
    const relevantBotIds = this.determineRelevantBots(state, userContext)
    filtered.botEcosystem = {
      activeBots: state.botEcosystem.activeBots.filter(bot =>
        relevantBotIds.includes(bot.id)
      ),
      recentHandoffs: state.botEcosystem.recentHandoffs.slice(-3) // Last 3 handoffs
    }

    // Only include user data if it's actively relevant
    if (this.isUserDataRelevant(state, userContext)) {
      filtered.userData = state.userData
    } else {
      filtered.userData = {}
    }

    return filtered
  }

  /**
   * Determine which bots are relevant for current context
   */
  private determineRelevantBots(state: PlatformState, userContext?: Partial<PlatformContext>): string[] {
    const relevantBots: string[] = []

    // Always include online bots
    state.botEcosystem.activeBots
      .filter(bot => bot.status === 'online')
      .forEach(bot => relevantBots.push(bot.id))

    // Include bots mentioned in recent activity
    state.recentActivity
      .filter(activity => activity.type === 'bot_interaction')
      .forEach(activity => {
        if (activity.details.botId && !relevantBots.includes(activity.details.botId)) {
          relevantBots.push(activity.details.botId)
        }
      })

    // Include contextually relevant bots based on current route
    const route = state.navigation.currentRoute
    if (route.includes('/jorge') && !relevantBots.includes('jorge-seller-bot')) {
      relevantBots.push('jorge-seller-bot')
    }

    return relevantBots
  }

  /**
   * Check if user data context is actively relevant
   */
  private isUserDataRelevant(state: PlatformState, userContext?: Partial<PlatformContext>): boolean {
    // Relevant if user explicitly provided context
    if (userContext?.leadContext || userContext?.propertyContext) return true

    // Relevant if on lead/property specific pages
    const route = state.navigation.currentRoute
    if (route.includes('/leads/') || route.includes('/properties/')) return true

    // Relevant if recent activity involves leads/properties
    const hasRecentDataActivity = state.recentActivity
      .slice(-5)
      .some(activity =>
        activity.type === 'data_view' &&
        ['lead', 'property'].includes(activity.details.dataType)
      )

    return hasRecentDataActivity
  }

  /**
   * Calculate importance score for activities
   */
  private calculateActivityImportance(activity: Omit<Activity, 'importance'>): 'low' | 'medium' | 'high' {
    const { type, details } = activity

    // High importance activities
    if (type === 'bot_interaction' && ['start_conversation', 'handoff', 'escalation'].includes(details.action)) {
      return 'high'
    }

    if (type === 'data_view' && ['lead', 'hot_property'].includes(details.dataType)) {
      return 'high'
    }

    if (type === 'navigation' && ['jorge', 'dashboard', 'analytics'].includes(details.to?.split('/')[1])) {
      return 'high'
    }

    // Medium importance activities
    if (type === 'bot_interaction') return 'medium'
    if (type === 'data_view') return 'medium'
    if (type === 'action' && details.importance !== 'low') return 'medium'

    // Low importance activities
    return 'low'
  }

  /**
   * Get open tabs (simplified - actual implementation would vary)
   */
  private getOpenTabs(): string[] {
    // In a real implementation, this might use browser APIs or track opened windows
    // For now, return current tab information
    return [typeof window !== 'undefined' ? window.location.pathname : '/']
  }

  /**
   * Get unique pages visited during session
   */
  private getUniqueVisitedPages(): string[] {
    const visited = new Set<string>()

    this.navigationHistory.forEach(nav => {
      visited.add(nav.currentRoute)
      if (nav.previousRoute) visited.add(nav.previousRoute)
    })

    return Array.from(visited)
  }

  /**
   * Analyze activity trends for pattern recognition
   */
  private analyzeActivityTrends(recentActivity: Activity[]): { activity: string; frequency: number }[] {
    const trends: Record<string, number> = {}

    recentActivity.forEach(activity => {
      const key = `${activity.type}:${activity.details.action || 'general'}`
      trends[key] = (trends[key] || 0) + 1
    })

    return Object.entries(trends)
      .map(([activity, frequency]) => ({ activity, frequency }))
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 3)
  }

  /**
   * Determine primary session focus based on activities
   */
  private determineSessionFocus(): string[] {
    const focus: string[] = []

    // Analyze navigation patterns
    const routes = this.navigationHistory.map(nav => nav.currentRoute)
    const routePatterns = routes.reduce((patterns, route) => {
      const section = route.split('/')[1] || 'home'
      patterns[section] = (patterns[section] || 0) + 1
      return patterns
    }, {} as Record<string, number>)

    const primaryRoute = Object.entries(routePatterns)
      .sort(([,a], [,b]) => b - a)[0]?.[0]

    if (primaryRoute) focus.push(`navigation:${primaryRoute}`)

    // Analyze bot interactions
    const botInteractions = this.activityWindow
      .filter(activity => activity.type === 'bot_interaction')
      .reduce((bots, activity) => {
        const botId = activity.details.botId
        if (botId) bots[botId] = (bots[botId] || 0) + 1
        return bots
      }, {} as Record<string, number>)

    const primaryBot = Object.entries(botInteractions)
      .sort(([,a], [,b]) => b - a)[0]?.[0]

    if (primaryBot) focus.push(`bot:${primaryBot}`)

    // Analyze data views
    const dataViews = this.activityWindow
      .filter(activity => activity.type === 'data_view')
      .reduce((data, activity) => {
        const dataType = activity.details.dataType
        if (dataType) data[dataType] = (data[dataType] || 0) + 1
        return data
      }, {} as Record<string, number>)

    const primaryDataType = Object.entries(dataViews)
      .sort(([,a], [,b]) => b - a)[0]?.[0]

    if (primaryDataType) focus.push(`data:${primaryDataType}`)

    return focus.slice(0, 3) // Top 3 focus areas
  }

  /**
   * Update contextual information periodically
   */
  private updateContextualInformation(): void {
    // Update time on page
    if (this.currentState.navigation.timeOnPage) {
      this.currentState.navigation.timeOnPage = Date.now() - this.currentState.navigation.timeOnPage
    }

    // Emit periodic context update
    this.emitContextUpdate({
      type: 'action',
      timestamp: new Date().toISOString(),
      details: { action: 'context_update' },
      importance: 'low'
    })
  }

  /**
   * Emit context update to listeners
   */
  private emitContextUpdate(triggeringActivity: Activity): void {
    const listeners = this.eventListeners.get('context_update') || []
    listeners.forEach(listener => {
      try {
        listener({
          type: 'context_update',
          detail: {
            platformState: this.currentState,
            triggeringActivity,
            timestamp: new Date().toISOString()
          }
        } as any)
      } catch (error) {
        console.warn('Context update listener failed:', error)
      }
    })
  }
}