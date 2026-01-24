// Jorge Real Estate Bot Ecosystem Coordination Store
// Enhanced multi-bot state management with real-time orchestration

import { create } from 'zustand'
import { jorgeApi, type ChatMessage, type JorgeBotStatus } from '@/lib/jorge-api-client'
import { subscribeToConversation, subscribeToBotStatus } from '@/lib/supabase'
import { socketManager, type BotStatusUpdate, type ConversationEvent } from '@/lib/socket'

// Bot Types for Jorge Ecosystem
export type JorgeBotType = 'jorge-seller' | 'lead-bot' | 'intent-decoder'

// Enhanced Bot Conversation with coordination data
interface BotConversation {
  id: string
  botId: JorgeBotType
  contactId?: string
  locationId?: string
  messages: ChatMessage[]
  isLoading: boolean
  lastActivity: Date

  // Multi-bot coordination
  parentWorkflowId?: string
  relatedConversations?: string[]
  handoffData?: any
  qualificationState?: QualificationState
}

// Jorge Seller Bot Qualification State
interface QualificationState {
  currentQuestion: number // 0-3 (Q1-Q4)
  questionsAnswered: number
  temperature: 'hot' | 'warm' | 'cold'
  propertyCondition?: string
  priceExpectation?: number
  motivationLevel?: string
  offerAcceptance?: boolean
  confrontationalEffectiveness?: number
  stallsDetected?: number
  nextRecommendedAction?: string
}

// Lead Bot Automation State
interface LeadAutomationState {
  sequenceDay: 3 | 7 | 30 | null
  currentAction: 'sms' | 'email' | 'call' | 'cma' | 'survey' | null
  completedActions: string[]
  scheduledActions: Array<{
    action: string
    scheduledTime: string
    completed: boolean
  }>
  retellCallId?: string
  cmaGenerated?: boolean
  surveyCompleted?: boolean
}

// Intent Decoder Analysis State
interface IntentAnalysisState {
  lastAnalysis?: {
    intentCategory: 'buyer' | 'seller' | 'investor' | 'curious'
    urgencyLevel: 'immediate' | 'active' | 'passive' | 'future'
    confidenceScore: number
    processingTime: number
    featuresTriggered: string[]
    timestamp: string
  }
  analysisHistory: Array<{
    timestamp: string
    category: string
    confidence: number
  }>
  needsReanalysis: boolean
}

// Multi-bot Workflow State
interface WorkflowState {
  id: string
  contactId: string
  locationId: string
  activeBot: JorgeBotType | null
  stage: 'qualification' | 'automation' | 'analysis' | 'handoff' | 'completed' | 'escalated'

  // Bot coordination
  jorgeSellerState?: QualificationState
  leadBotState?: LeadAutomationState
  intentDecoderState?: IntentAnalysisState

  // Handoff management
  handoffQueue: Array<{
    fromBot: JorgeBotType
    toBot: JorgeBotType
    reason: string
    timestamp: string
    data: any
  }>

  // Workflow metadata
  createdAt: string
  lastUpdate: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
}

// Enhanced Chat State with Multi-bot Coordination
interface EnhancedChatState {
  // Core Conversation Management
  conversations: Record<string, BotConversation>
  activeConversationId: string | null

  // Multi-bot Workflow Orchestration
  workflows: Record<string, WorkflowState>
  activeWorkflowId: string | null

  // Bot Status & Performance
  botStatuses: Record<JorgeBotType, JorgeBotStatus & {
    performanceMetrics?: {
      conversationsToday: number
      avgResponseTime: number
      successRate: number
      lastActivity: string
    }
  }>

  // Real-time Integration
  realTimeConnected: boolean
  lastRealTimeUpdate: string | null

  // Bot-specific State Management
  qualificationStates: Record<string, QualificationState> // keyed by contactId
  automationStates: Record<string, LeadAutomationState> // keyed by contactId
  analysisStates: Record<string, IntentAnalysisState> // keyed by contactId

  // Cross-bot Communication
  botMessages: Array<{
    fromBot: JorgeBotType
    toBot: JorgeBotType
    messageType: 'handoff' | 'data_request' | 'status_update'
    payload: any
    timestamp: string
  }>

  // UI State
  isTyping: Record<string, boolean>
  selectedBotView: JorgeBotType | 'all'

  // Core Actions
  setActiveConversation: (conversationId: string) => void
  setActiveWorkflow: (workflowId: string) => void
  sendMessage: (botId: JorgeBotType, content: string, workflowId?: string) => void
  addMessage: (conversationId: string, message: ChatMessage) => void
  setBotStatus: (botId: JorgeBotType, status: JorgeBotStatus) => void
  setTyping: (botId: JorgeBotType, isTyping: boolean) => void

  // Multi-bot Coordination Actions
  createWorkflow: (contactId: string, locationId: string, initialBot: JorgeBotType) => Promise<string>
  updateWorkflowStage: (workflowId: string, stage: WorkflowState['stage']) => void
  initiateHandoff: (fromBot: JorgeBotType, toBot: JorgeBotType, reason: string, data: any) => Promise<void>
  processHandoffQueue: (workflowId: string) => Promise<void>

  // Jorge-Specific Workflow Actions
  startJorgeSellerQualification: (contactId: string, locationId: string, leadData?: any) => Promise<string>
  triggerLeadAutomation: (contactId: string, sequenceDay: 3 | 7 | 30, trigger?: string) => Promise<void>
  requestIntentAnalysis: (contactId: string, conversationData: any) => Promise<void>

  // Bot Performance & Analytics
  updateBotPerformance: (botId: JorgeBotType, metrics: any) => void
  getBotCoordinationMetrics: () => any

  // Real-time Event Handlers
  handleBotStatusUpdate: (update: BotStatusUpdate) => void
  handleConversationEvent: (event: ConversationEvent) => void
  handleJorgeQualificationProgress: (data: any) => void
  handleLeadBotSequenceUpdate: (data: any) => void
  handleIntentAnalysisComplete: (data: any) => void

  // Real-time Setup
  connectRealtime: () => Promise<void>
  disconnectRealtime: () => void

  // Utility Actions
  escalateToHuman: (workflowId: string, reason: string) => Promise<void>
  exportWorkflowData: (workflowId: string) => any
  resetBotState: (botId: JorgeBotType) => void
}

export const useChatStore = create<EnhancedChatState>((set, get) => ({
  // Initial State
  conversations: {},
  activeConversationId: null,
  workflows: {},
  activeWorkflowId: null,
  botStatuses: {
    'jorge-seller': { id: 'jorge-seller', name: 'Jorge Seller Bot', status: 'offline', conversationsToday: 0, leadsQualified: 0, responseTimeMs: 0, lastActivity: new Date().toISOString() },
    'lead-bot': { id: 'lead-bot', name: 'Lead Bot', status: 'offline', conversationsToday: 0, leadsQualified: 0, responseTimeMs: 0, lastActivity: new Date().toISOString() },
    'intent-decoder': { id: 'intent-decoder', name: 'Intent Decoder', status: 'offline', conversationsToday: 0, leadsQualified: 0, responseTimeMs: 0, lastActivity: new Date().toISOString() }
  },
  realTimeConnected: false,
  lastRealTimeUpdate: null,
  qualificationStates: {},
  automationStates: {},
  analysisStates: {},
  botMessages: [],
  isTyping: {},
  selectedBotView: 'all',

  // Core Actions
  setActiveConversation: (conversationId) => {
    set({ activeConversationId: conversationId })
  },

  setActiveWorkflow: (workflowId) => {
    set({ activeWorkflowId: workflowId })
  },

  sendMessage: async (botId, content, workflowId) => {
    const state = get()
    const conversationId = state.activeConversationId

    if (!conversationId) {
      console.error('No active conversation')
      return
    }

    // Add user message immediately
    const userMessage: ChatMessage = {
      content,
      role: 'user',
      timestamp: new Date().toISOString(),
      botId
    }

    get().addMessage(conversationId, userMessage)
    get().setTyping(botId, true)

    try {
      // Use the Jorge API with workflow context
      const response = await jorgeApi.sendMessage(botId, content, {
        workflowId,
        conversationId,
        contactId: state.workflows[workflowId]?.contactId,
        locationId: state.workflows[workflowId]?.locationId
      })

      // Handle streaming response
      const stream = response.getReader()
      const decoder = new TextDecoder()
      let botResponse = ''

      while (true) {
        const { done, value } = await stream.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.chunk) {
                botResponse += data.chunk

                const streamMessage: ChatMessage = {
                  content: botResponse,
                  role: 'bot',
                  timestamp: new Date().toISOString(),
                  botId
                }

                get().addMessage(conversationId, streamMessage)
              }

              // Handle bot-specific progress updates
              if (data.progress) {
                get().updateBotSpecificState(botId, data.progress)
              }
            } catch (e) {
              console.warn('Failed to parse streaming chunk:', e)
            }
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error)

      const errorMessage: ChatMessage = {
        content: 'Sorry, I encountered an error. Please try again.',
        role: 'bot',
        timestamp: new Date().toISOString(),
        botId
      }

      get().addMessage(conversationId, errorMessage)
    } finally {
      get().setTyping(botId, false)
    }
  },

  addMessage: (conversationId, message) => {
    set((state) => {
      const conversation = state.conversations[conversationId] || {
        id: conversationId,
        botId: message.botId as JorgeBotType,
        messages: [],
        isLoading: false,
        lastActivity: new Date()
      }

      return {
        conversations: {
          ...state.conversations,
          [conversationId]: {
            ...conversation,
            messages: [...conversation.messages, message],
            lastActivity: new Date()
          }
        }
      }
    })
  },

  setBotStatus: (botId, status) => {
    set((state) => ({
      botStatuses: {
        ...state.botStatuses,
        [botId]: {
          ...state.botStatuses[botId],
          ...status,
          performanceMetrics: {
            ...state.botStatuses[botId]?.performanceMetrics,
            lastActivity: new Date().toISOString()
          }
        }
      }
    }))
  },

  setTyping: (botId, isTyping) => {
    set((state) => ({
      isTyping: {
        ...state.isTyping,
        [botId]: isTyping
      }
    }))
  },

  // Multi-bot Coordination Actions
  createWorkflow: async (contactId, locationId, initialBot) => {
    const workflowId = `workflow_${Date.now()}_${contactId}`
    const now = new Date().toISOString()

    const newWorkflow: WorkflowState = {
      id: workflowId,
      contactId,
      locationId,
      activeBot: initialBot,
      stage: 'qualification',
      handoffQueue: [],
      createdAt: now,
      lastUpdate: now,
      priority: 'medium'
    }

    set((state) => ({
      workflows: {
        ...state.workflows,
        [workflowId]: newWorkflow
      },
      activeWorkflowId: workflowId
    }))

    // Initialize bot-specific states
    switch (initialBot) {
      case 'jorge-seller':
        get().initializeQualificationState(contactId)
        break
      case 'lead-bot':
        get().initializeAutomationState(contactId)
        break
      case 'intent-decoder':
        get().initializeAnalysisState(contactId)
        break
    }

    return workflowId
  },

  updateWorkflowStage: (workflowId, stage) => {
    set((state) => ({
      workflows: {
        ...state.workflows,
        [workflowId]: {
          ...state.workflows[workflowId],
          stage,
          lastUpdate: new Date().toISOString()
        }
      }
    }))
  },

  initiateHandoff: async (fromBot, toBot, reason, data) => {
    const state = get()
    const workflowId = state.activeWorkflowId

    if (!workflowId) {
      console.error('No active workflow for handoff')
      return
    }

    const handoffItem = {
      fromBot,
      toBot,
      reason,
      timestamp: new Date().toISOString(),
      data
    }

    // Add to handoff queue
    set((state) => ({
      workflows: {
        ...state.workflows,
        [workflowId]: {
          ...state.workflows[workflowId],
          handoffQueue: [...state.workflows[workflowId].handoffQueue, handoffItem],
          stage: 'handoff' as const
        }
      }
    }))

    // Add cross-bot communication message
    get().addBotMessage(fromBot, toBot, 'handoff', data)

    // Process the handoff
    await get().processHandoffQueue(workflowId)
  },

  processHandoffQueue: async (workflowId) => {
    const state = get()
    const workflow = state.workflows[workflowId]

    if (!workflow || workflow.handoffQueue.length === 0) return

    const handoff = workflow.handoffQueue[0]

    // Update active bot
    set((state) => ({
      workflows: {
        ...state.workflows,
        [workflowId]: {
          ...state.workflows[workflowId],
          activeBot: handoff.toBot,
          handoffQueue: state.workflows[workflowId].handoffQueue.slice(1),
          stage: 'qualification' // Reset to appropriate stage
        }
      }
    }))

    // Notify backend about handoff
    try {
      await fetch('/api/workflows/handoff', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflowId,
          fromBot: handoff.fromBot,
          toBot: handoff.toBot,
          reason: handoff.reason,
          data: handoff.data
        })
      })
    } catch (error) {
      console.error('Failed to process handoff:', error)
    }
  },

  // Jorge-Specific Workflow Actions
  startJorgeSellerQualification: async (contactId, locationId, leadData = {}) => {
    try {
      const workflowId = await get().createWorkflow(contactId, locationId, 'jorge-seller')

      // Create conversation for Jorge Seller Bot
      const conversationId = `conv_${Date.now()}_jorge_seller_${contactId}`

      const conversation: BotConversation = {
        id: conversationId,
        botId: 'jorge-seller',
        contactId,
        locationId,
        messages: [],
        isLoading: false,
        lastActivity: new Date(),
        parentWorkflowId: workflowId
      }

      set((state) => ({
        conversations: {
          ...state.conversations,
          [conversationId]: conversation
        },
        activeConversationId: conversationId
      }))

      // Send initial greeting
      const greetingMessage: ChatMessage = {
        content: "Hello! I'm Jorge, your direct seller qualification specialist. I use a confrontational approach to identify motivated sellers only. Ready to see if your property is a good fit?",
        role: 'bot',
        timestamp: new Date().toISOString(),
        botId: 'jorge-seller'
      }

      get().addMessage(conversationId, greetingMessage)

      return workflowId
    } catch (error) {
      console.error('Failed to start Jorge Seller qualification:', error)
      throw error
    }
  },

  triggerLeadAutomation: async (contactId, sequenceDay, trigger = 'manual') => {
    try {
      // Update automation state
      set((state) => ({
        automationStates: {
          ...state.automationStates,
          [contactId]: {
            ...state.automationStates[contactId],
            sequenceDay,
            currentAction: 'sms', // Start with SMS
            scheduledActions: [
              {
                action: `day_${sequenceDay}_sms`,
                scheduledTime: new Date().toISOString(),
                completed: false
              }
            ]
          }
        }
      }))

      // Trigger backend automation
      await fetch('/api/lead-bot/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contactId,
          sequenceDay,
          trigger
        })
      })
    } catch (error) {
      console.error('Failed to trigger lead automation:', error)
    }
  },

  requestIntentAnalysis: async (contactId, conversationData) => {
    try {
      // Update analysis state
      set((state) => ({
        analysisStates: {
          ...state.analysisStates,
          [contactId]: {
            ...state.analysisStates[contactId],
            needsReanalysis: false
          }
        }
      }))

      // Request analysis from backend
      const response = await fetch('/api/intent-decoder/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contactId,
          conversationData
        })
      })

      const result = await response.json()

      // Update analysis state with results
      get().handleIntentAnalysisComplete(result)
    } catch (error) {
      console.error('Failed to request intent analysis:', error)
    }
  },

  // Bot Performance & Analytics
  updateBotPerformance: (botId, metrics) => {
    set((state) => ({
      botStatuses: {
        ...state.botStatuses,
        [botId]: {
          ...state.botStatuses[botId],
          performanceMetrics: {
            ...state.botStatuses[botId]?.performanceMetrics,
            ...metrics,
            lastActivity: new Date().toISOString()
          }
        }
      }
    }))
  },

  getBotCoordinationMetrics: () => {
    const state = get()
    const workflows = Object.values(state.workflows)

    return {
      totalWorkflows: workflows.length,
      activeWorkflows: workflows.filter(w => w.stage !== 'completed' && w.stage !== 'escalated').length,
      completedWorkflows: workflows.filter(w => w.stage === 'completed').length,
      escalatedWorkflows: workflows.filter(w => w.stage === 'escalated').length,
      averageWorkflowDuration: workflows.reduce((acc, w) => {
        const duration = new Date(w.lastUpdate).getTime() - new Date(w.createdAt).getTime()
        return acc + duration
      }, 0) / workflows.length,
      handoffsToday: state.botMessages.filter(m =>
        m.messageType === 'handoff' &&
        new Date(m.timestamp).toDateString() === new Date().toDateString()
      ).length
    }
  },

  // Real-time Event Handlers
  handleBotStatusUpdate: (update) => {
    get().setBotStatus(update.bot_type, {
      status: update.status,
      lastActivity: update.timestamp
    })

    set({
      realTimeConnected: true,
      lastRealTimeUpdate: update.timestamp
    })
  },

  handleConversationEvent: (event) => {
    // Process conversation events and update relevant states
    if (event.bot_type === 'jorge-seller' && event.event_type === 'qualification_updated') {
      get().updateQualificationState(event.contact_id, event.data)
    }

    set({ lastRealTimeUpdate: event.timestamp })
  },

  handleJorgeQualificationProgress: (data) => {
    get().updateQualificationState(data.contact_id, {
      currentQuestion: data.current_question,
      questionsAnswered: data.questions_answered,
      temperature: data.seller_temperature,
      confrontationalEffectiveness: data.confrontational_effectiveness,
      stallsDetected: data.stall_detected ? 1 : 0,
      nextRecommendedAction: data.next_step
    })
  },

  handleLeadBotSequenceUpdate: (data) => {
    get().updateAutomationState(data.contact_id, {
      sequenceDay: data.sequence_day,
      currentAction: data.action_type.includes('sms') ? 'sms' :
                    data.action_type.includes('email') ? 'email' :
                    data.action_type.includes('call') ? 'call' : null,
      completedActions: data.success ? [`${data.action_type}_${data.sequence_day}`] : [],
      retellCallId: data.retell_call_duration_seconds ? `call_${Date.now()}` : undefined
    })
  },

  handleIntentAnalysisComplete: (data) => {
    get().updateAnalysisState(data.contact_id, {
      lastAnalysis: {
        intentCategory: data.intent_category,
        urgencyLevel: data.urgency_level,
        confidenceScore: data.confidence_score,
        processingTime: data.processing_time_ms,
        featuresTriggered: data.ml_features_triggered,
        timestamp: new Date().toISOString()
      },
      needsReanalysis: false
    })
  },

  // Real-time Setup with Enhanced Integration
  connectRealtime: async () => {
    try {
      await socketManager.connect()

      // Set up event listeners for multi-bot coordination
      socketManager.on('bot_status_update', get().handleBotStatusUpdate)
      socketManager.on('conversation_event', get().handleConversationEvent)
      socketManager.on('jorge_qualification_progress', get().handleJorgeQualificationProgress)
      socketManager.on('lead_bot_sequence_update', get().handleLeadBotSequenceUpdate)
      socketManager.on('intent_analysis_complete', get().handleIntentAnalysisComplete)

      set({ realTimeConnected: true })
      console.log('✅ Jorge bot ecosystem connected to real-time coordination')
    } catch (error) {
      console.error('Failed to connect real-time coordination:', error)
      set({ realTimeConnected: false })
    }
  },

  disconnectRealtime: () => {
    socketManager.disconnect()
    set({
      realTimeConnected: false,
      lastRealTimeUpdate: null
    })
  },

  // Utility Actions
  escalateToHuman: async (workflowId, reason) => {
    const state = get()
    const workflow = state.workflows[workflowId]

    if (!workflow) return

    // Update workflow stage
    get().updateWorkflowStage(workflowId, 'escalated')

    // Add escalation message to active conversation
    if (state.activeConversationId) {
      const escalationMessage: ChatMessage = {
        content: `🚀 Escalating to human agent. Reason: ${reason}`,
        role: 'bot',
        timestamp: new Date().toISOString(),
        botId: workflow.activeBot || 'jorge-seller'
      }

      get().addMessage(state.activeConversationId, escalationMessage)
    }

    // Notify backend
    try {
      await fetch('/api/workflows/escalate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflowId,
          reason,
          contactId: workflow.contactId,
          locationId: workflow.locationId
        })
      })
    } catch (error) {
      console.error('Failed to escalate workflow:', error)
    }
  },

  exportWorkflowData: (workflowId) => {
    const state = get()
    const workflow = state.workflows[workflowId]

    if (!workflow) return null

    return {
      workflow,
      qualificationState: state.qualificationStates[workflow.contactId],
      automationState: state.automationStates[workflow.contactId],
      analysisState: state.analysisStates[workflow.contactId],
      conversations: Object.values(state.conversations).filter(c => c.parentWorkflowId === workflowId),
      botMessages: state.botMessages.filter(m => m.timestamp >= workflow.createdAt)
    }
  },

  resetBotState: (botId) => {
    set((state) => ({
      botStatuses: {
        ...state.botStatuses,
        [botId]: {
          ...state.botStatuses[botId],
          status: 'idle',
          conversationsToday: 0,
          performanceMetrics: {
            conversationsToday: 0,
            avgResponseTime: 0,
            successRate: 0,
            lastActivity: new Date().toISOString()
          }
        }
      },
      isTyping: {
        ...state.isTyping,
        [botId]: false
      }
    }))
  },

  // Helper Methods (internal use)
  initializeQualificationState: (contactId: string) => {
    set((state) => ({
      qualificationStates: {
        ...state.qualificationStates,
        [contactId]: {
          currentQuestion: 0,
          questionsAnswered: 0,
          temperature: 'cold',
          confrontationalEffectiveness: 0,
          stallsDetected: 0
        }
      }
    }))
  },

  initializeAutomationState: (contactId: string) => {
    set((state) => ({
      automationStates: {
        ...state.automationStates,
        [contactId]: {
          sequenceDay: null,
          currentAction: null,
          completedActions: [],
          scheduledActions: []
        }
      }
    }))
  },

  initializeAnalysisState: (contactId: string) => {
    set((state) => ({
      analysisStates: {
        ...state.analysisStates,
        [contactId]: {
          analysisHistory: [],
          needsReanalysis: true
        }
      }
    }))
  },

  updateQualificationState: (contactId: string, updates: Partial<QualificationState>) => {
    set((state) => ({
      qualificationStates: {
        ...state.qualificationStates,
        [contactId]: {
          ...state.qualificationStates[contactId],
          ...updates
        }
      }
    }))
  },

  updateAutomationState: (contactId: string, updates: Partial<LeadAutomationState>) => {
    set((state) => ({
      automationStates: {
        ...state.automationStates,
        [contactId]: {
          ...state.automationStates[contactId],
          ...updates
        }
      }
    }))
  },

  updateAnalysisState: (contactId: string, updates: Partial<IntentAnalysisState>) => {
    set((state) => ({
      analysisStates: {
        ...state.analysisStates,
        [contactId]: {
          ...state.analysisStates[contactId],
          ...updates,
          analysisHistory: updates.lastAnalysis ? [
            ...(state.analysisStates[contactId]?.analysisHistory || []),
            {
              timestamp: updates.lastAnalysis.timestamp,
              category: updates.lastAnalysis.intentCategory,
              confidence: updates.lastAnalysis.confidenceScore
            }
          ] : state.analysisStates[contactId]?.analysisHistory || []
        }
      }
    }))
  },

  updateBotSpecificState: (botId: JorgeBotType, progressData: any) => {
    if (botId === 'jorge-seller' && progressData.qualification) {
      get().updateQualificationState(progressData.contactId, progressData.qualification)
    } else if (botId === 'lead-bot' && progressData.automation) {
      get().updateAutomationState(progressData.contactId, progressData.automation)
    } else if (botId === 'intent-decoder' && progressData.analysis) {
      get().updateAnalysisState(progressData.contactId, progressData.analysis)
    }
  },

  addBotMessage: (fromBot: JorgeBotType, toBot: JorgeBotType, messageType: 'handoff' | 'data_request' | 'status_update', payload: any) => {
    const botMessage = {
      fromBot,
      toBot,
      messageType,
      payload,
      timestamp: new Date().toISOString()
    }

    set((state) => ({
      botMessages: [...state.botMessages, botMessage]
    }))
  }
} as any)) // Type assertion needed for helper methods

// Enhanced Bot Coordination Hooks for External Use
export const useJorgeWorkflow = () => {
  const workflows = useChatStore((state) => state.workflows)
  const activeWorkflowId = useChatStore((state) => state.activeWorkflowId)
  const createWorkflow = useChatStore((state) => state.createWorkflow)
  const updateWorkflowStage = useChatStore((state) => state.updateWorkflowStage)
  const initiateHandoff = useChatStore((state) => state.initiateHandoff)
  const escalateToHuman = useChatStore((state) => state.escalateToHuman)

  return {
    workflows,
    activeWorkflow: activeWorkflowId ? workflows[activeWorkflowId] : null,
    createWorkflow,
    updateWorkflowStage,
    initiateHandoff,
    escalateToHuman
  }
}

export const useMultiBotCoordination = () => {
  const botStatuses = useChatStore((state) => state.botStatuses)
  const qualificationStates = useChatStore((state) => state.qualificationStates)
  const automationStates = useChatStore((state) => state.automationStates)
  const analysisStates = useChatStore((state) => state.analysisStates)
  const botMessages = useChatStore((state) => state.botMessages)
  const getBotCoordinationMetrics = useChatStore((state) => state.getBotCoordinationMetrics)
  const startJorgeSellerQualification = useChatStore((state) => state.startJorgeSellerQualification)
  const triggerLeadAutomation = useChatStore((state) => state.triggerLeadAutomation)
  const requestIntentAnalysis = useChatStore((state) => state.requestIntentAnalysis)

  return {
    botStatuses,
    qualificationStates,
    automationStates,
    analysisStates,
    botMessages,
    metrics: getBotCoordinationMetrics(),
    startJorgeSellerQualification,
    triggerLeadAutomation,
    requestIntentAnalysis
  }
}

export const useRealTimeCoordination = () => {
  const realTimeConnected = useChatStore((state) => state.realTimeConnected)
  const lastRealTimeUpdate = useChatStore((state) => state.lastRealTimeUpdate)
  const connectRealtime = useChatStore((state) => state.connectRealtime)
  const disconnectRealtime = useChatStore((state) => state.disconnectRealtime)

  return {
    connected: realTimeConnected,
    lastUpdate: lastRealTimeUpdate,
    connect: connectRealtime,
    disconnect: disconnectRealtime
  }
}

// Cleanup on unmount
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    useChatStore.getState().disconnectRealtime()
  })
}