/**
 * Concierge-specific Zustand store
 * Extends existing useChatStore pattern
 *
 * Integration Points:
 * - useChatStore.ts:50-333 (chat management)
 * - providers.tsx:64-89 (real-time setup)
 */

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { ClaudeConciergeService } from '@/lib/claude-concierge/ClaudeConciergeService'
import { ContextManager } from '@/lib/claude-concierge/ContextManager'
import type {
  ConciergeResponse,
  SuggestedAction,
  BotHandoffRecommendation,
  ProactiveSuggestion
} from '@/lib/claude-concierge/ClaudeConciergeService'
import type { PlatformContext } from '@/lib/claude-concierge/ContextManager'

export interface ConciergeConversation {
  id: string
  messages: ConciergeMessage[]
  createdAt: string
  lastActivity: string
  metadata?: {
    totalInteractions: number
    avgResponseTime: number
    handoffsGenerated: number
  }
}

export interface ConciergeMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  metadata?: {
    reasoning?: string
    suggestedActions?: SuggestedAction[]
    handoffRecommendation?: BotHandoffRecommendation
    processingTime?: number
  }
}

export interface ProactiveSuggestionState extends ProactiveSuggestion {
  dismissed: boolean
  dismissedAt?: string
  acceptedAt?: string
}

export interface ConciergeState {
  // Service Management
  conciergeService: ClaudeConciergeService | null
  contextManager: ContextManager | null
  isInitialized: boolean
  initializationError: string | null

  // Conversation Management
  conversations: Record<string, ConciergeConversation>
  activeConversationId: string | null

  // UI State
  isVisible: boolean
  isExpanded: boolean
  isTyping: boolean
  lastResponseTime: number

  // Proactive Intelligence
  proactiveSuggestions: ProactiveSuggestionState[]
  lastSuggestionUpdate: string | null
  suggestionsEnabled: boolean

  // Performance Metrics
  responseTimeHistory: number[]
  errorCount: number
  totalInteractions: number

  // Actions - Initialization
  initializeConcierge: () => Promise<void>
  resetService: () => void

  // Actions - UI Management
  toggleVisibility: () => void
  setExpanded: (expanded: boolean) => void

  // Actions - Conversation Management
  sendMessage: (message: string) => Promise<void>
  createConversation: () => string
  setActiveConversation: (conversationId: string | null) => void
  clearConversation: (conversationId: string) => void

  // Actions - Suggestions Management
  generateProactiveSuggestions: () => Promise<void>
  dismissSuggestion: (suggestionId: string) => void
  acceptSuggestion: (suggestion: ProactiveSuggestionState) => Promise<void>
  toggleSuggestions: (enabled: boolean) => void

  // Actions - Bot Integration
  acceptHandoff: (handoff: BotHandoffRecommendation) => Promise<void>
  executeAction: (action: SuggestedAction) => Promise<void>

  // Actions - Context Tracking
  trackPageView: (route: string) => void
  trackUserAction: (action: any) => void

  // Actions - Analytics
  getPerformanceMetrics: () => any
  clearMetrics: () => void
}

export const useConciergeStore = create<ConciergeState>()(
  persist(
    (set, get) => ({
      // Initial State
      conciergeService: null,
      contextManager: null,
      isInitialized: false,
      initializationError: null,

      conversations: {},
      activeConversationId: null,

      isVisible: false,
      isExpanded: true,
      isTyping: false,
      lastResponseTime: 0,

      proactiveSuggestions: [],
      lastSuggestionUpdate: null,
      suggestionsEnabled: true,

      responseTimeHistory: [],
      errorCount: 0,
      totalInteractions: 0,

      // Initialize Concierge service
      initializeConcierge: async () => {
        try {
          set({ initializationError: null })

          const service = new ClaudeConciergeService('/api')
          const contextMgr = new ContextManager()

          set({
            conciergeService: service,
            contextManager: contextMgr,
            isInitialized: true,
          })

          // Generate initial proactive suggestions
          if (get().suggestionsEnabled) {
            await get().generateProactiveSuggestions()
          }

          console.log('Claude Concierge initialized successfully')
        } catch (error) {
          console.error('Failed to initialize Claude Concierge:', error)
          set({
            initializationError: error instanceof Error ? error.message : 'Unknown initialization error',
            isInitialized: false
          })
        }
      },

      // Reset service (for debugging/recovery)
      resetService: () => {
        set({
          conciergeService: null,
          contextManager: null,
          isInitialized: false,
          initializationError: null,
        })
      },

      // Toggle sidebar visibility
      toggleVisibility: () => {
        const wasVisible = get().isVisible
        set({ isVisible: !wasVisible })

        // Track visibility change
        get().trackUserAction({
          type: 'concierge_visibility',
          visible: !wasVisible,
          timestamp: new Date().toISOString()
        })
      },

      // Set expansion state
      setExpanded: (expanded) => {
        set({ isExpanded: expanded })

        get().trackUserAction({
          type: 'concierge_expansion',
          expanded,
          timestamp: new Date().toISOString()
        })
      },

      // Send message to Concierge
      sendMessage: async (message: string) => {
        const state = get()
        const startTime = Date.now()

        if (!state.conciergeService || !state.isInitialized) {
          throw new Error('Concierge service not initialized')
        }

        const conversationId = state.activeConversationId || get().createConversation()

        // Add user message immediately
        const userMessage: ConciergeMessage = {
          role: 'user',
          content: message,
          timestamp: new Date().toISOString(),
        }

        set((state) => ({
          conversations: {
            ...state.conversations,
            [conversationId]: {
              ...state.conversations[conversationId],
              messages: [...state.conversations[conversationId].messages, userMessage],
              lastActivity: userMessage.timestamp,
            }
          },
          isTyping: true,
        }))

        try {
          // Capture current platform context
          const platformContext = await state.contextManager?.captureContext()

          // Stream response from Concierge
          const responseGenerator = state.conciergeService.chat({
            userMessage: message,
            conversationId,
            platformContext,
          })

          let fullResponse = ''

          // Process streaming response
          for await (const chunk of responseGenerator) {
            fullResponse += chunk

            // Update assistant message in real-time
            set((state) => {
              const conversation = state.conversations[conversationId]
              const messages = conversation.messages
              const lastMessage = messages[messages.length - 1]

              // If last message is from assistant, update it; otherwise add new
              if (lastMessage?.role === 'assistant') {
                return {
                  conversations: {
                    ...state.conversations,
                    [conversationId]: {
                      ...conversation,
                      messages: [
                        ...messages.slice(0, -1),
                        {
                          ...lastMessage,
                          content: fullResponse,
                          timestamp: new Date().toISOString(),
                        }
                      ]
                    }
                  }
                }
              } else {
                return {
                  conversations: {
                    ...state.conversations,
                    [conversationId]: {
                      ...conversation,
                      messages: [
                        ...messages,
                        {
                          role: 'assistant',
                          content: fullResponse,
                          timestamp: new Date().toISOString(),
                        }
                      ]
                    }
                  }
                }
              }
            })
          }

          // Get final response with metadata
          const finalResponse = await responseGenerator.return()

          if (finalResponse) {
            const processingTime = Date.now() - startTime

            // Update final message with metadata
            set((state) => {
              const conversation = state.conversations[conversationId]
              const messages = conversation.messages
              const lastMessage = messages[messages.length - 1]

              return {
                conversations: {
                  ...state.conversations,
                  [conversationId]: {
                    ...conversation,
                    messages: [
                      ...messages.slice(0, -1),
                      {
                        ...lastMessage,
                        content: finalResponse.content,
                        metadata: {
                          reasoning: finalResponse.reasoning,
                          suggestedActions: finalResponse.suggestedActions,
                          handoffRecommendation: finalResponse.botHandoff,
                          processingTime,
                        }
                      }
                    ],
                    metadata: {
                      ...conversation.metadata,
                      totalInteractions: (conversation.metadata?.totalInteractions || 0) + 1,
                      avgResponseTime: conversation.metadata?.avgResponseTime
                        ? (conversation.metadata.avgResponseTime + processingTime) / 2
                        : processingTime,
                    }
                  }
                },
                isTyping: false,
                lastResponseTime: processingTime,
                responseTimeHistory: [...state.responseTimeHistory, processingTime].slice(-10), // Keep last 10
                totalInteractions: state.totalInteractions + 1
              }
            })
          }

          // Track successful interaction
          get().trackUserAction({
            type: 'concierge_message',
            success: true,
            processingTime: Date.now() - startTime,
            messageLength: message.length,
            responseLength: fullResponse.length,
            timestamp: new Date().toISOString()
          })

        } catch (error) {
          console.error('Concierge message failed:', error)

          // Add error message
          const errorMessage: ConciergeMessage = {
            role: 'assistant',
            content: 'I apologize, but I encountered an error processing your request. Please try again or let me help you navigate the platform directly.',
            timestamp: new Date().toISOString(),
          }

          set((state) => ({
            conversations: {
              ...state.conversations,
              [conversationId]: {
                ...state.conversations[conversationId],
                messages: [...state.conversations[conversationId].messages, errorMessage],
                lastActivity: errorMessage.timestamp,
              }
            },
            isTyping: false,
            errorCount: state.errorCount + 1
          }))

          // Track error
          get().trackUserAction({
            type: 'concierge_error',
            error: error instanceof Error ? error.message : 'Unknown error',
            timestamp: new Date().toISOString()
          })

          throw error
        }
      },

      // Create new conversation
      createConversation: () => {
        const conversationId = `concierge_${Date.now()}`

        set((state) => ({
          conversations: {
            ...state.conversations,
            [conversationId]: {
              id: conversationId,
              messages: [],
              createdAt: new Date().toISOString(),
              lastActivity: new Date().toISOString(),
              metadata: {
                totalInteractions: 0,
                avgResponseTime: 0,
                handoffsGenerated: 0
              }
            }
          },
          activeConversationId: conversationId,
        }))

        get().trackUserAction({
          type: 'concierge_conversation_created',
          conversationId,
          timestamp: new Date().toISOString()
        })

        return conversationId
      },

      // Set active conversation
      setActiveConversation: (conversationId) => {
        set({ activeConversationId: conversationId })

        if (conversationId) {
          get().trackUserAction({
            type: 'concierge_conversation_switched',
            conversationId,
            timestamp: new Date().toISOString()
          })
        }
      },

      // Clear conversation
      clearConversation: (conversationId) => {
        set((state) => {
          const { [conversationId]: removed, ...remaining } = state.conversations
          return {
            conversations: remaining,
            activeConversationId: state.activeConversationId === conversationId ? null : state.activeConversationId
          }
        })

        get().trackUserAction({
          type: 'concierge_conversation_cleared',
          conversationId,
          timestamp: new Date().toISOString()
        })
      },

      // Generate proactive suggestions
      generateProactiveSuggestions: async () => {
        const state = get()

        if (!state.conciergeService || !state.suggestionsEnabled) return

        try {
          const context = await state.contextManager?.captureContext()
          const suggestions = await state.conciergeService.analyzeContext(context)

          const suggestionStates: ProactiveSuggestionState[] = suggestions.map(suggestion => ({
            ...suggestion,
            dismissed: false
          }))

          set({
            proactiveSuggestions: suggestionStates,
            lastSuggestionUpdate: new Date().toISOString()
          })

          get().trackUserAction({
            type: 'concierge_suggestions_generated',
            count: suggestions.length,
            timestamp: new Date().toISOString()
          })

        } catch (error) {
          console.error('Failed to generate proactive suggestions:', error)
        }
      },

      // Dismiss proactive suggestion
      dismissSuggestion: (suggestionId) => {
        set((state) => ({
          proactiveSuggestions: state.proactiveSuggestions.map(s =>
            s.id === suggestionId
              ? { ...s, dismissed: true, dismissedAt: new Date().toISOString() }
              : s
          )
        }))

        get().trackUserAction({
          type: 'concierge_suggestion_dismissed',
          suggestionId,
          timestamp: new Date().toISOString()
        })
      },

      // Accept suggestion
      acceptSuggestion: async (suggestion) => {
        // Mark as accepted
        set((state) => ({
          proactiveSuggestions: state.proactiveSuggestions.map(s =>
            s.id === suggestion.id
              ? { ...s, acceptedAt: new Date().toISOString() }
              : s
          )
        }))

        // Execute the suggested action
        await get().executeAction(suggestion.action)

        get().trackUserAction({
          type: 'concierge_suggestion_accepted',
          suggestionId: suggestion.id,
          actionType: suggestion.action.type,
          timestamp: new Date().toISOString()
        })
      },

      // Toggle suggestions
      toggleSuggestions: (enabled) => {
        set({ suggestionsEnabled: enabled })

        if (enabled) {
          // Generate suggestions when re-enabled
          get().generateProactiveSuggestions()
        }

        get().trackUserAction({
          type: 'concierge_suggestions_toggled',
          enabled,
          timestamp: new Date().toISOString()
        })
      },

      // Accept bot handoff recommendation
      acceptHandoff: async (handoff: BotHandoffRecommendation) => {
        try {
          // Import useChatStore to trigger bot conversation
          const { useChatStore } = await import('@/store/useChatStore')
          const chatStore = useChatStore.getState()

          // Record handoff in concierge service
          const conversationId = get().activeConversationId
          if (conversationId && get().conciergeService) {
            await get().conciergeService!.recordBotHandoff(
              conversationId,
              handoff.targetBot,
              handoff.contextToTransfer
            )
          }

          // Start conversation with target bot
          if (handoff.targetBot === 'jorge-seller-bot') {
            const newConversationId = await chatStore.startJorgeSellerConversation(handoff.contextToTransfer)
            chatStore.setActiveConversation(newConversationId)
          }
          // Add other bot integrations as they become available

          // Hide concierge, user will see bot chat
          set({ isVisible: false })

          get().trackUserAction({
            type: 'concierge_handoff_accepted',
            targetBot: handoff.targetBot,
            confidence: handoff.confidence,
            timestamp: new Date().toISOString()
          })

        } catch (error) {
          console.error('Failed to execute bot handoff:', error)
          throw error
        }
      },

      // Execute suggested action
      executeAction: async (action: SuggestedAction) => {
        try {
          switch (action.type) {
            case 'navigation':
              if (typeof window !== 'undefined') {
                window.location.href = action.data.route
              }
              break

            case 'bot_start':
              if (action.data.botId === 'jorge-seller-bot') {
                const { useChatStore } = await import('@/store/useChatStore')
                const chatStore = useChatStore.getState()
                await chatStore.startJorgeSellerConversation(action.data.context)
                set({ isVisible: false }) // Hide concierge when starting bot
              }
              break

            case 'data_update':
              // Handle data update actions
              console.log('Data update action:', action.data)
              break

            case 'external_link':
              if (typeof window !== 'undefined') {
                window.open(action.data.url, '_blank')
              }
              break

            default:
              console.warn('Unknown action type:', action.type)
          }

          get().trackUserAction({
            type: 'concierge_action_executed',
            actionType: action.type,
            actionData: action.data,
            timestamp: new Date().toISOString()
          })

        } catch (error) {
          console.error('Failed to execute action:', error)
          throw error
        }
      },

      // Track page navigation for context
      trackPageView: (route: string) => {
        const state = get()
        state.contextManager?.trackNavigation(route)

        // Regenerate suggestions on significant page changes
        const majorPages = ['/jorge', '/leads', '/properties', '/analytics']
        if (majorPages.some(page => route.includes(page)) && state.suggestionsEnabled) {
          // Debounce suggestion generation
          setTimeout(() => {
            get().generateProactiveSuggestions()
          }, 2000)
        }
      },

      // Track user actions
      trackUserAction: (action: any) => {
        const state = get()
        state.contextManager?.trackUIInteraction(
          action.type,
          action.action || 'general',
          action
        )
      },

      // Get performance metrics
      getPerformanceMetrics: () => {
        const state = get()
        const avgResponseTime = state.responseTimeHistory.length > 0
          ? state.responseTimeHistory.reduce((sum, time) => sum + time, 0) / state.responseTimeHistory.length
          : 0

        return {
          totalInteractions: state.totalInteractions,
          avgResponseTime: Math.round(avgResponseTime),
          errorCount: state.errorCount,
          errorRate: state.totalInteractions > 0 ? state.errorCount / state.totalInteractions : 0,
          lastResponseTime: state.lastResponseTime,
          conversationsCount: Object.keys(state.conversations).length,
          activeSuggestions: state.proactiveSuggestions.filter(s => !s.dismissed && !s.acceptedAt).length,
          serviceMetrics: state.conciergeService?.getServiceMetrics() || null
        }
      },

      // Clear metrics (for reset/debugging)
      clearMetrics: () => {
        set({
          responseTimeHistory: [],
          errorCount: 0,
          totalInteractions: 0,
          lastResponseTime: 0
        })
      },
    }),
    {
      name: 'jorge-concierge-storage',
      partialize: (state) => ({
        conversations: state.conversations,
        activeConversationId: state.activeConversationId,
        proactiveSuggestions: state.proactiveSuggestions.filter(s => !s.dismissed), // Don't persist dismissed
        suggestionsEnabled: state.suggestionsEnabled,
        // Don't persist service instances or runtime state
      }),
      version: 1,
      migrate: (persistedState: any, version: number) => {
        // Handle schema migrations for future versions
        if (version === 0) {
          // Migration from version 0 to 1 (if needed)
          return {
            ...persistedState,
            suggestionsEnabled: persistedState.suggestionsEnabled ?? true
          }
        }
        return persistedState
      }
    }
  )
)

// Auto-initialize concierge when store is created (in browser only)
if (typeof window !== 'undefined') {
  // Initialize after a short delay to ensure other stores are ready
  setTimeout(() => {
    const store = useConciergeStore.getState()
    if (!store.isInitialized) {
      store.initializeConcierge().catch(error => {
        console.error('Auto-initialization failed:', error)
      })
    }
  }, 1000)
}