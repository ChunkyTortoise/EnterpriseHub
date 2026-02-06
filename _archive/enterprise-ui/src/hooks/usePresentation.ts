// React Hook for Presentation State Management
// Provides comprehensive presentation control and real-time updates

'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import PresentationOrchestrator, {
  type PresentationSession,
  type ClientProfile,
  type ClientInteraction,
  type EngagementMetrics,
  type PresentationOutcome,
  type FollowUpAction
} from '@/lib/presentation/PresentationOrchestrator'
import ClientAnalytics, {
  type ClientAnalyticsEvent,
  type EngagementPattern,
  type PredictiveInsight,
  type ClientBehaviorProfile
} from '@/lib/presentation/ClientAnalytics'

export interface UsePresentationOptions {
  enableAnalytics?: boolean
  enableRealTimeUpdates?: boolean
  autoSave?: boolean
  trackMouseMovement?: boolean
  trackVoiceInput?: boolean
}

export interface PresentationState {
  // Core State
  currentSession: PresentationSession | null
  isLoading: boolean
  error: string | null

  // Session Management
  activeSessions: PresentationSession[]
  sessionHistory: PresentationSession[]

  // Real-time Analytics
  engagementMetrics: EngagementMetrics
  behaviorProfile: ClientBehaviorProfile | null
  recentPatterns: EngagementPattern[]
  predictiveInsights: PredictiveInsight[]

  // Presentation Flow
  currentSlideIndex: number
  totalSlides: number
  presentationProgress: number
  timeElapsed: number
  timeRemaining: number

  // Interaction State
  isFullScreen: boolean
  isDemoMode: boolean
  isRecording: boolean
  showAnalytics: boolean
  showClaudeConcierge: boolean
}

export interface PresentationActions {
  // Session Management
  createSession: (clientName: string, sessionType: PresentationSession['sessionType'], clientProfile?: ClientProfile) => Promise<string>
  loadSession: (sessionId: string) => Promise<void>
  startSession: () => Promise<void>
  pauseSession: () => Promise<void>
  completeSession: () => Promise<PresentationOutcome>
  deleteSession: (sessionId: string) => Promise<void>

  // Navigation
  nextSlide: () => Promise<boolean>
  previousSlide: () => Promise<boolean>
  goToSlide: (index: number) => Promise<void>
  navigateToComponent: (component: 'intro' | 'roi_calculator' | 'demo' | 'performance_reports' | 'q_and_a') => Promise<void>

  // Interaction Tracking
  logInteraction: (interaction: Omit<ClientInteraction, 'id' | 'sessionId' | 'timestamp' | 'urgency' | 'followUpRequired' | 'confidence'>) => Promise<void>
  trackQuestion: (question: string, category?: string) => Promise<void>
  trackObjection: (objection: string, category?: string) => Promise<void>
  trackInterest: (topic: string) => Promise<void>
  trackConfusion: (area: string) => Promise<void>

  // Analytics
  trackMousePosition: (x: number, y: number) => void
  trackClick: (elementId: string, coordinates?: { x: number; y: number }) => void
  trackScroll: (scrollY: number) => void
  trackVoiceInput: (duration: number, confidence: number) => void

  // UI State
  toggleFullScreen: () => void
  toggleDemoMode: () => void
  toggleAnalytics: () => void
  toggleConcierge: () => void
  startRecording: () => void
  stopRecording: () => void

  // Client Profile
  updateClientProfile: (profile: Partial<ClientProfile>) => Promise<void>
  buildClientProfile: (answers: Record<string, any>) => ClientProfile

  // Follow-up Actions
  addFollowUpAction: (action: Omit<FollowUpAction, 'id' | 'sessionId'>) => Promise<void>
  completeFollowUpAction: (actionId: string) => Promise<void>
}

const defaultState: PresentationState = {
  currentSession: null,
  isLoading: false,
  error: null,
  activeSessions: [],
  sessionHistory: [],
  engagementMetrics: {
    attentionScore: 100,
    interactionLevel: 0,
    sentimentScore: 0,
    questionsAsked: 0,
    objectionsRaised: 0,
    commitmentSignals: 0,
    timeOnSlide: 0,
    mouseActivity: 0,
    scrollActivity: 0,
    lastInteraction: new Date()
  },
  behaviorProfile: null,
  recentPatterns: [],
  predictiveInsights: [],
  currentSlideIndex: 0,
  totalSlides: 0,
  presentationProgress: 0,
  timeElapsed: 0,
  timeRemaining: 0,
  isFullScreen: false,
  isDemoMode: false,
  isRecording: false,
  showAnalytics: false,
  showClaudeConcierge: true
}

export function usePresentation(options: UsePresentationOptions = {}): [PresentationState, PresentationActions] {
  const {
    enableAnalytics = true,
    enableRealTimeUpdates = true,
    autoSave = true,
    trackMouseMovement = true,
    trackVoiceInput = true
  } = options

  const [state, setState] = useState<PresentationState>(defaultState)
  const router = useRouter()

  // Refs
  const orchestratorRef = useRef<PresentationOrchestrator>()
  const analyticsRef = useRef<ClientAnalytics>()
  const unsubscribeSessionRef = useRef<(() => void) | null>(null)
  const unsubscribeAnalyticsRef = useRef<(() => void) | null>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  // Initialize services
  useEffect(() => {
    orchestratorRef.current = PresentationOrchestrator.getInstance()
    if (enableAnalytics) {
      analyticsRef.current = new ClientAnalytics()
    }

    // Load session history
    loadSessionHistory()

    return () => {
      if (unsubscribeSessionRef.current) {
        unsubscribeSessionRef.current()
      }
      if (unsubscribeAnalyticsRef.current) {
        unsubscribeAnalyticsRef.current()
      }
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [enableAnalytics])

  // Session timer
  useEffect(() => {
    if (state.currentSession?.isActive && !timerRef.current) {
      timerRef.current = setInterval(() => {
        setState(prevState => {
          if (!prevState.currentSession) return prevState

          const now = Date.now()
          const elapsed = Math.floor((now - prevState.currentSession.startTime.getTime()) / 1000)
          const totalEstimated = prevState.currentSession.agenda.reduce((sum, slide) => sum + slide.estimatedDuration, 0)
          const remaining = Math.max(0, totalEstimated - elapsed)
          const progress = totalEstimated > 0 ? Math.min(100, (elapsed / totalEstimated) * 100) : 0

          return {
            ...prevState,
            timeElapsed: elapsed,
            timeRemaining: remaining,
            presentationProgress: progress
          }
        })
      }, 1000)
    } else if (!state.currentSession?.isActive && timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
  }, [state.currentSession?.isActive])

  // Load session history
  const loadSessionHistory = useCallback(async () => {
    if (!orchestratorRef.current) return

    try {
      const allSessions = orchestratorRef.current.getAllSessions()
      const activeSessions = allSessions.filter(s => s.isActive)
      const sessionHistory = allSessions.filter(s => !s.isActive)

      setState(prevState => ({
        ...prevState,
        activeSessions,
        sessionHistory
      }))
    } catch (error) {
      setState(prevState => ({
        ...prevState,
        error: error instanceof Error ? error.message : 'Failed to load sessions'
      }))
    }
  }, [])

  // Session Management Actions
  const createSession = useCallback(async (
    clientName: string,
    sessionType: PresentationSession['sessionType'],
    clientProfile?: ClientProfile
  ): Promise<string> => {
    if (!orchestratorRef.current) throw new Error('Orchestrator not initialized')

    setState(prevState => ({ ...prevState, isLoading: true, error: null }))

    try {
      const session = await orchestratorRef.current.createSession(clientName, sessionType, clientProfile)

      setState(prevState => ({
        ...prevState,
        currentSession: session,
        currentSlideIndex: 0,
        totalSlides: session.agenda.length,
        engagementMetrics: session.engagementMetrics,
        isLoading: false
      }))

      return session.id
    } catch (error) {
      setState(prevState => ({
        ...prevState,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to create session'
      }))
      throw error
    }
  }, [])

  const loadSession = useCallback(async (sessionId: string): Promise<void> => {
    if (!orchestratorRef.current) throw new Error('Orchestrator not initialized')

    setState(prevState => ({ ...prevState, isLoading: true, error: null }))

    try {
      const session = orchestratorRef.current.getSession(sessionId)
      if (!session) throw new Error('Session not found')

      // Unsubscribe from previous session
      if (unsubscribeSessionRef.current) {
        unsubscribeSessionRef.current()
      }
      if (unsubscribeAnalyticsRef.current) {
        unsubscribeAnalyticsRef.current()
      }

      // Subscribe to session updates
      if (enableRealTimeUpdates) {
        unsubscribeSessionRef.current = orchestratorRef.current.subscribeToSession(sessionId, (updatedSession) => {
          setState(prevState => ({
            ...prevState,
            currentSession: updatedSession,
            currentSlideIndex: updatedSession.currentSlide,
            engagementMetrics: updatedSession.engagementMetrics
          }))
        })
      }

      // Subscribe to analytics updates
      if (enableAnalytics && analyticsRef.current) {
        unsubscribeAnalyticsRef.current = analyticsRef.current.subscribeToInsights(sessionId, (insight) => {
          setState(prevState => ({
            ...prevState,
            predictiveInsights: [insight, ...prevState.predictiveInsights.slice(0, 9)] // Keep last 10
          }))
        })

        // Generate behavior profile
        const behaviorProfile = analyticsRef.current.generateBehaviorProfile(sessionId)
        setState(prevState => ({ ...prevState, behaviorProfile }))
      }

      setState(prevState => ({
        ...prevState,
        currentSession: session,
        currentSlideIndex: session.currentSlide,
        totalSlides: session.agenda.length,
        engagementMetrics: session.engagementMetrics,
        isLoading: false
      }))
    } catch (error) {
      setState(prevState => ({
        ...prevState,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to load session'
      }))
    }
  }, [enableAnalytics, enableRealTimeUpdates])

  const startSession = useCallback(async (): Promise<void> => {
    if (!orchestratorRef.current || !state.currentSession) return

    try {
      await orchestratorRef.current.startSession(state.currentSession.id)
    } catch (error) {
      setState(prevState => ({
        ...prevState,
        error: error instanceof Error ? error.message : 'Failed to start session'
      }))
    }
  }, [state.currentSession])

  const pauseSession = useCallback(async (): Promise<void> => {
    if (!state.currentSession) return

    setState(prevState => ({
      ...prevState,
      currentSession: prevState.currentSession
        ? { ...prevState.currentSession, isActive: false }
        : null
    }))
  }, [state.currentSession])

  const completeSession = useCallback(async (): Promise<PresentationOutcome> => {
    if (!orchestratorRef.current || !state.currentSession) {
      throw new Error('No active session')
    }

    try {
      const outcome = await orchestratorRef.current.completeSession(state.currentSession.id)

      setState(prevState => ({
        ...prevState,
        currentSession: prevState.currentSession
          ? { ...prevState.currentSession, isActive: false, completedAt: new Date() }
          : null
      }))

      await loadSessionHistory()
      return outcome
    } catch (error) {
      setState(prevState => ({
        ...prevState,
        error: error instanceof Error ? error.message : 'Failed to complete session'
      }))
      throw error
    }
  }, [state.currentSession, loadSessionHistory])

  // Navigation Actions
  const nextSlide = useCallback(async (): Promise<boolean> => {
    if (!orchestratorRef.current || !state.currentSession) return false

    try {
      const success = await orchestratorRef.current.nextSlide(state.currentSession.id)
      if (enableAnalytics && analyticsRef.current) {
        analyticsRef.current.trackEvent({
          sessionId: state.currentSession.id,
          type: 'page_view',
          slideId: `slide_${state.currentSlideIndex + 1}`
        })
      }
      return success
    } catch (error) {
      setState(prevState => ({
        ...prevState,
        error: error instanceof Error ? error.message : 'Failed to navigate to next slide'
      }))
      return false
    }
  }, [state.currentSession, state.currentSlideIndex, enableAnalytics])

  const previousSlide = useCallback(async (): Promise<boolean> => {
    if (!orchestratorRef.current || !state.currentSession || state.currentSlideIndex === 0) return false

    try {
      await orchestratorRef.current.navigateToSlide(state.currentSession.id, state.currentSlideIndex - 1)
      if (enableAnalytics && analyticsRef.current) {
        analyticsRef.current.trackEvent({
          sessionId: state.currentSession.id,
          type: 'page_view',
          slideId: `slide_${state.currentSlideIndex - 1}`
        })
      }
      return true
    } catch (error) {
      setState(prevState => ({
        ...prevState,
        error: error instanceof Error ? error.message : 'Failed to navigate to previous slide'
      }))
      return false
    }
  }, [state.currentSession, state.currentSlideIndex, enableAnalytics])

  const goToSlide = useCallback(async (index: number): Promise<void> => {
    if (!orchestratorRef.current || !state.currentSession) return

    try {
      await orchestratorRef.current.navigateToSlide(state.currentSession.id, index)
      if (enableAnalytics && analyticsRef.current) {
        analyticsRef.current.trackEvent({
          sessionId: state.currentSession.id,
          type: 'page_view',
          slideId: `slide_${index}`
        })
      }
    } catch (error) {
      setState(prevState => ({
        ...prevState,
        error: error instanceof Error ? error.message : 'Failed to navigate to slide'
      }))
    }
  }, [state.currentSession, enableAnalytics])

  const navigateToComponent = useCallback(async (component: 'intro' | 'roi_calculator' | 'demo' | 'performance_reports' | 'q_and_a'): Promise<void> => {
    if (!state.currentSession) return

    const slideIndex = state.currentSession.agenda.findIndex(slide => slide.component === component)
    if (slideIndex >= 0) {
      await goToSlide(slideIndex)
    }
  }, [state.currentSession, goToSlide])

  // Interaction Tracking
  const logInteraction = useCallback(async (interaction: Omit<ClientInteraction, 'id' | 'sessionId' | 'timestamp' | 'urgency' | 'followUpRequired' | 'confidence'>): Promise<void> => {
    if (!orchestratorRef.current || !state.currentSession) return

    try {
      await orchestratorRef.current.logInteraction(state.currentSession.id, interaction)
    } catch (error) {
      console.error('Failed to log interaction:', error)
    }
  }, [state.currentSession])

  const trackQuestion = useCallback(async (question: string, category = 'general'): Promise<void> => {
    await logInteraction({
      type: 'question',
      content: question,
      sentiment: 'neutral',
      category: category as any
    })
  }, [logInteraction])

  const trackObjection = useCallback(async (objection: string, category = 'pricing'): Promise<void> => {
    await logInteraction({
      type: 'objection',
      content: objection,
      sentiment: 'negative',
      category: category as any
    })
  }, [logInteraction])

  const trackInterest = useCallback(async (topic: string): Promise<void> => {
    await logInteraction({
      type: 'interest',
      content: `Showed interest in: ${topic}`,
      sentiment: 'positive',
      category: 'capability'
    })
  }, [logInteraction])

  // Analytics Tracking
  const trackMousePosition = useCallback((x: number, y: number): void => {
    if (!enableAnalytics || !analyticsRef.current || !state.currentSession || !trackMouseMovement) return

    const currentSlide = state.currentSession.agenda[state.currentSlideIndex]
    analyticsRef.current.trackMouseMovement(state.currentSession.id, x, y, currentSlide?.id)
  }, [enableAnalytics, state.currentSession, state.currentSlideIndex, trackMouseMovement])

  const trackClick = useCallback((elementId: string, coordinates?: { x: number; y: number }): void => {
    if (!enableAnalytics || !analyticsRef.current || !state.currentSession) return

    const currentSlide = state.currentSession.agenda[state.currentSlideIndex]
    analyticsRef.current.trackClick(state.currentSession.id, elementId, currentSlide?.id, coordinates)
  }, [enableAnalytics, state.currentSession, state.currentSlideIndex])

  const trackScroll = useCallback((scrollY: number): void => {
    if (!enableAnalytics || !analyticsRef.current || !state.currentSession) return

    const currentSlide = state.currentSession.agenda[state.currentSlideIndex]
    analyticsRef.current.trackScroll(state.currentSession.id, scrollY, currentSlide?.id)
  }, [enableAnalytics, state.currentSession, state.currentSlideIndex])

  const trackVoiceInputCallback = useCallback((duration: number, confidence: number): void => {
    if (!enableAnalytics || !analyticsRef.current || !state.currentSession) return

    const currentSlide = state.currentSession.agenda[state.currentSlideIndex]
    analyticsRef.current.trackVoiceInput(state.currentSession.id, duration, confidence, currentSlide?.id)
  }, [enableAnalytics, state.currentSession, state.currentSlideIndex])

  // UI State Actions
  const toggleFullScreen = useCallback(() => {
    setState(prevState => ({ ...prevState, isFullScreen: !prevState.isFullScreen }))
  }, [])

  const toggleDemoMode = useCallback(() => {
    setState(prevState => ({ ...prevState, isDemoMode: !prevState.isDemoMode }))
  }, [])

  const toggleAnalytics = useCallback(() => {
    setState(prevState => ({ ...prevState, showAnalytics: !prevState.showAnalytics }))
  }, [])

  const toggleConcierge = useCallback(() => {
    setState(prevState => ({ ...prevState, showClaudeConcierge: !prevState.showClaudeConcierge }))
  }, [])

  // Build client profile from discovery questions
  const buildClientProfile = useCallback((answers: Record<string, any>): ClientProfile => {
    return {
      name: answers.name || 'Unknown Client',
      company: answers.company,
      propertyBudget: parseInt(answers.budget) || 500000,
      urgency: answers.urgency || 'medium',
      marketSegment: answers.segment || 'mid-market',
      experience: answers.experience || 'some',
      concerns: answers.concerns || [],
      priorities: answers.priorities || [],
      timeline: parseInt(answers.timeline) || 6,
      preferredCommunication: answers.communication || 'email',
      source: answers.source || 'referral',
      creditScore: parseInt(answers.creditScore),
      preApprovalAmount: parseInt(answers.preApproval)
    }
  }, [])

  const updateClientProfile = useCallback(async (profile: Partial<ClientProfile>): Promise<void> => {
    if (!state.currentSession) return

    setState(prevState => ({
      ...prevState,
      currentSession: prevState.currentSession
        ? {
            ...prevState.currentSession,
            clientProfile: {
              ...prevState.currentSession.clientProfile,
              ...profile
            } as ClientProfile
          }
        : null
    }))
  }, [state.currentSession])

  // Placeholder actions for unimplemented features
  const deleteSession = useCallback(async (sessionId: string): Promise<void> => {
    // Implementation would remove from storage
    await loadSessionHistory()
  }, [loadSessionHistory])

  const startRecording = useCallback(() => {
    setState(prevState => ({ ...prevState, isRecording: true }))
  }, [])

  const stopRecording = useCallback(() => {
    setState(prevState => ({ ...prevState, isRecording: false }))
  }, [])

  const addFollowUpAction = useCallback(async (action: Omit<FollowUpAction, 'id' | 'sessionId'>): Promise<void> => {
    // Implementation would add to current session
  }, [])

  const completeFollowUpAction = useCallback(async (actionId: string): Promise<void> => {
    // Implementation would mark action as complete
  }, [])

  const trackConfusion = useCallback(async (area: string): Promise<void> => {
    await logInteraction({
      type: 'confusion',
      content: `Confusion detected in: ${area}`,
      sentiment: 'negative',
      category: 'capability'
    })
  }, [logInteraction])

  const actions: PresentationActions = {
    createSession,
    loadSession,
    startSession,
    pauseSession,
    completeSession,
    deleteSession,
    nextSlide,
    previousSlide,
    goToSlide,
    navigateToComponent,
    logInteraction,
    trackQuestion,
    trackObjection,
    trackInterest,
    trackConfusion,
    trackMousePosition,
    trackClick,
    trackScroll,
    trackVoiceInput: trackVoiceInputCallback,
    toggleFullScreen,
    toggleDemoMode,
    toggleAnalytics,
    toggleConcierge,
    startRecording,
    stopRecording,
    updateClientProfile,
    buildClientProfile,
    addFollowUpAction,
    completeFollowUpAction
  }

  return [state, actions]
}

export default usePresentation