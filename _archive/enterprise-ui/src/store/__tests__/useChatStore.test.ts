/**
 * Enhanced Chat Store Tests
 * Testing multi-bot coordination and state management
 */

import { act, renderHook } from '@testing-library/react'
import { useChatStore, useJorgeWorkflow, useMultiBotCoordination, useRealTimeCoordination } from '../useChatStore'
import { socketManager } from '@/lib/socket'

// Mock dependencies
jest.mock('@/lib/socket')
jest.mock('@/lib/supabase')

const mockSocketManager = socketManager as jest.Mocked<typeof socketManager>

describe('Enhanced Chat Store', () => {
  beforeEach(() => {
    // Reset store state
    useChatStore.setState({
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
      selectedBotView: 'all'
    }, true)

    jest.clearAllMocks()
  })

  describe('Workflow Management', () => {
    it('creates new workflow with initial bot', async () => {
      const { result } = renderHook(() => useChatStore())

      await act(async () => {
        const workflowId = await result.current.createWorkflow('contact_123', 'loc_456', 'jorge-seller')

        expect(workflowId).toMatch(/^workflow_/)
        expect(result.current.workflows[workflowId]).toBeDefined()
        expect(result.current.workflows[workflowId].activeBot).toBe('jorge-seller')
        expect(result.current.workflows[workflowId].stage).toBe('qualification')
        expect(result.current.activeWorkflowId).toBe(workflowId)
      })
    })

    it('initializes bot-specific states', async () => {
      const { result } = renderHook(() => useChatStore())

      await act(async () => {
        await result.current.createWorkflow('contact_123', 'loc_456', 'jorge-seller')

        expect(result.current.qualificationStates['contact_123']).toEqual({
          currentQuestion: 0,
          questionsAnswered: 0,
          temperature: 'cold',
          confrontationalEffectiveness: 0,
          stallsDetected: 0
        })
      })
    })

    it('updates workflow stage', () => {
      const { result } = renderHook(() => useChatStore())

      act(() => {
        // Set up initial workflow
        const workflowId = 'workflow_test'
        result.current.workflows[workflowId] = {
          id: workflowId,
          contactId: 'contact_123',
          locationId: 'loc_456',
          activeBot: 'jorge-seller',
          stage: 'qualification',
          handoffQueue: [],
          createdAt: new Date().toISOString(),
          lastUpdate: new Date().toISOString(),
          priority: 'medium'
        }

        result.current.updateWorkflowStage(workflowId, 'automation')

        expect(result.current.workflows[workflowId].stage).toBe('automation')
        expect(result.current.workflows[workflowId].lastUpdate).toBeDefined()
      })
    })

    it('processes handoffs between bots', async () => {
      const { result } = renderHook(() => useChatStore())

      // Set up workflow
      const workflowId = 'workflow_test'

      act(() => {
        result.current.workflows[workflowId] = {
          id: workflowId,
          contactId: 'contact_123',
          locationId: 'loc_456',
          activeBot: 'jorge-seller',
          stage: 'qualification',
          handoffQueue: [],
          createdAt: new Date().toISOString(),
          lastUpdate: new Date().toISOString(),
          priority: 'medium'
        }
        result.current.activeWorkflowId = workflowId
      })

      // Mock fetch for handoff API
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ success: true })
      } as Response)

      await act(async () => {
        await result.current.initiateHandoff(
          'jorge-seller',
          'lead-bot',
          'Qualification completed',
          { sellerTemperature: 'hot' }
        )

        expect(result.current.workflows[workflowId].activeBot).toBe('lead-bot')
        expect(result.current.workflows[workflowId].stage).toBe('qualification')
        expect(result.current.botMessages).toHaveLength(1)
        expect(result.current.botMessages[0].messageType).toBe('handoff')
      })
    })
  })

  describe('Jorge Seller Bot Integration', () => {
    it('starts Jorge seller qualification workflow', async () => {
      const { result } = renderHook(() => useChatStore())

      await act(async () => {
        const workflowId = await result.current.startJorgeSellerQualification('contact_123', 'loc_456')

        expect(workflowId).toBeDefined()
        expect(result.current.workflows[workflowId]).toBeDefined()
        expect(result.current.workflows[workflowId].activeBot).toBe('jorge-seller')

        // Should create conversation
        const conversations = Object.values(result.current.conversations)
        const jorgeConversation = conversations.find(c => c.botId === 'jorge-seller')
        expect(jorgeConversation).toBeDefined()
        expect(jorgeConversation?.messages).toHaveLength(1) // Initial greeting
      })
    })

    it('updates qualification state from real-time events', () => {
      const { result } = renderHook(() => useChatStore())

      act(() => {
        result.current.handleJorgeQualificationProgress({
          contact_id: 'contact_123',
          current_question: 2,
          questions_answered: 3,
          seller_temperature: 'hot',
          confrontational_effectiveness: 87,
          stall_detected: false,
          next_step: 'Q3 - Motivation'
        })

        expect(result.current.qualificationStates['contact_123']).toEqual({
          currentQuestion: 2,
          questionsAnswered: 3,
          temperature: 'hot',
          confrontationalEffectiveness: 87,
          stallsDetected: 0,
          nextRecommendedAction: 'Q3 - Motivation'
        })
      })
    })
  })

  describe('Lead Bot Integration', () => {
    it('triggers lead automation sequence', async () => {
      const { result } = renderHook(() => useChatStore())

      // Mock fetch for automation API
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ success: true })
      } as Response)

      await act(async () => {
        await result.current.triggerLeadAutomation('contact_456', 7, 'qualification_complete')

        expect(result.current.automationStates['contact_456']).toEqual({
          sequenceDay: 7,
          currentAction: 'sms',
          scheduledActions: [
            {
              action: 'day_7_sms',
              scheduledTime: expect.any(String),
              completed: false
            }
          ]
        })
      })
    })

    it('handles lead bot sequence updates', () => {
      const { result } = renderHook(() => useChatStore())

      act(() => {
        result.current.handleLeadBotSequenceUpdate({
          contact_id: 'contact_789',
          sequence_day: 30,
          action_type: 'call_completed',
          success: true,
          retell_call_duration_seconds: 180
        })

        expect(result.current.automationStates['contact_789']).toEqual({
          sequenceDay: 30,
          currentAction: 'call',
          completedActions: ['call_completed_30'],
          retellCallId: expect.stringMatching(/^call_/)
        })
      })
    })
  })

  describe('Intent Decoder Integration', () => {
    it('requests intent analysis', async () => {
      const { result } = renderHook(() => useChatStore())

      // Mock fetch for analysis API
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          intent_category: 'seller',
          urgency_level: 'immediate',
          confidence_score: 0.92,
          processing_time_ms: 38,
          ml_features_triggered: ['high_motivation']
        })
      } as Response)

      await act(async () => {
        await result.current.requestIntentAnalysis('contact_def', {
          messages: ['I need to sell quickly'],
          context: 'initial_contact'
        })

        expect(result.current.analysisStates['contact_def']).toEqual({
          needsReanalysis: false
        })
      })
    })

    it('handles intent analysis completion', () => {
      const { result } = renderHook(() => useChatStore())

      act(() => {
        result.current.handleIntentAnalysisComplete({
          contact_id: 'contact_ghi',
          intent_category: 'buyer',
          urgency_level: 'active',
          confidence_score: 0.89,
          processing_time_ms: 45,
          ml_features_triggered: ['price_sensitive', 'ready_to_buy']
        })

        expect(result.current.analysisStates['contact_ghi'].lastAnalysis).toEqual({
          intentCategory: 'buyer',
          urgencyLevel: 'active',
          confidenceScore: 0.89,
          processingTime: 45,
          featuresTriggered: ['price_sensitive', 'ready_to_buy'],
          timestamp: expect.any(String)
        })

        expect(result.current.analysisStates['contact_ghi'].analysisHistory).toHaveLength(1)
      })
    })
  })

  describe('Real-time Event Integration', () => {
    it('connects to WebSocket with event handlers', async () => {
      const { result } = renderHook(() => useChatStore())

      mockSocketManager.connect = jest.fn().mockResolvedValue({} as any)
      mockSocketManager.on = jest.fn()

      await act(async () => {
        await result.current.connectRealtime()

        expect(result.current.realTimeConnected).toBe(true)
        expect(mockSocketManager.connect).toHaveBeenCalled()
        expect(mockSocketManager.on).toHaveBeenCalledWith('bot_status_update', expect.any(Function))
        expect(mockSocketManager.on).toHaveBeenCalledWith('jorge_qualification_progress', expect.any(Function))
      })
    })

    it('handles bot status updates from WebSocket', () => {
      const { result } = renderHook(() => useChatStore())

      act(() => {
        result.current.handleBotStatusUpdate({
          bot_type: 'jorge-seller',
          contact_id: 'contact_123',
          status: 'active',
          timestamp: new Date().toISOString()
        })

        expect(result.current.botStatuses['jorge-seller'].status).toBe('active')
        expect(result.current.realTimeConnected).toBe(true)
        expect(result.current.lastRealTimeUpdate).toBeDefined()
      })
    })

    it('disconnects WebSocket cleanly', () => {
      const { result } = renderHook(() => useChatStore())

      mockSocketManager.disconnect = jest.fn()

      act(() => {
        result.current.disconnectRealtime()

        expect(mockSocketManager.disconnect).toHaveBeenCalled()
        expect(result.current.realTimeConnected).toBe(false)
        expect(result.current.lastRealTimeUpdate).toBeNull()
      })
    })
  })

  describe('Cross-bot Communication', () => {
    it('adds bot messages for cross-bot communication', () => {
      const { result } = renderHook(() => useChatStore())

      act(() => {
        result.current.addBotMessage(
          'jorge-seller',
          'lead-bot',
          'handoff',
          { sellerTemperature: 'hot', qualificationComplete: true }
        )

        expect(result.current.botMessages).toHaveLength(1)
        expect(result.current.botMessages[0]).toEqual({
          fromBot: 'jorge-seller',
          toBot: 'lead-bot',
          messageType: 'handoff',
          payload: { sellerTemperature: 'hot', qualificationComplete: true },
          timestamp: expect.any(String)
        })
      })
    })

    it('calculates coordination metrics correctly', () => {
      const { result } = renderHook(() => useChatStore())

      // Set up test data
      act(() => {
        const now = new Date().toISOString()
        const workflow1 = {
          id: 'workflow_1',
          contactId: 'contact_1',
          locationId: 'loc_1',
          activeBot: 'jorge-seller' as const,
          stage: 'qualification' as const,
          handoffQueue: [],
          createdAt: now,
          lastUpdate: now,
          priority: 'medium' as const
        }

        const workflow2 = {
          ...workflow1,
          id: 'workflow_2',
          stage: 'completed' as const
        }

        result.current.workflows = {
          workflow_1: workflow1,
          workflow_2: workflow2
        }

        result.current.botMessages = [
          {
            fromBot: 'jorge-seller',
            toBot: 'lead-bot',
            messageType: 'handoff',
            payload: {},
            timestamp: new Date().toISOString()
          }
        ]

        const metrics = result.current.getBotCoordinationMetrics()

        expect(metrics).toEqual({
          totalWorkflows: 2,
          activeWorkflows: 1,
          completedWorkflows: 1,
          escalatedWorkflows: 0,
          averageWorkflowDuration: expect.any(Number),
          handoffsToday: 1
        })
      })
    })
  })

  describe('Error Handling', () => {
    it('handles workflow escalation', async () => {
      const { result } = renderHook(() => useChatStore())

      // Set up workflow and conversation
      const workflowId = 'workflow_test'
      const conversationId = 'conv_test'

      act(() => {
        result.current.workflows[workflowId] = {
          id: workflowId,
          contactId: 'contact_123',
          locationId: 'loc_456',
          activeBot: 'jorge-seller',
          stage: 'qualification',
          handoffQueue: [],
          createdAt: new Date().toISOString(),
          lastUpdate: new Date().toISOString(),
          priority: 'medium'
        }

        result.current.conversations[conversationId] = {
          id: conversationId,
          botId: 'jorge-seller',
          messages: [],
          isLoading: false,
          lastActivity: new Date()
        }

        result.current.activeConversationId = conversationId
      })

      // Mock fetch for escalation API
      global.fetch = jest.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ success: true })
      } as Response)

      await act(async () => {
        await result.current.escalateToHuman(workflowId, 'Customer request')

        expect(result.current.workflows[workflowId].stage).toBe('escalated')
        expect(result.current.conversations[conversationId].messages).toHaveLength(1)
        expect(result.current.conversations[conversationId].messages[0].content).toContain('Escalating to human agent')
      })
    })

    it('resets bot state correctly', () => {
      const { result } = renderHook(() => useChatStore())

      // Set up bot with active state
      act(() => {
        result.current.botStatuses['jorge-seller'] = {
          ...result.current.botStatuses['jorge-seller'],
          status: 'active',
          conversationsToday: 10,
          performanceMetrics: {
            conversationsToday: 10,
            avgResponseTime: 1200,
            successRate: 87,
            lastActivity: new Date().toISOString()
          }
        }

        result.current.isTyping['jorge-seller'] = true

        result.current.resetBotState('jorge-seller')

        expect(result.current.botStatuses['jorge-seller'].status).toBe('idle')
        expect(result.current.botStatuses['jorge-seller'].conversationsToday).toBe(0)
        expect(result.current.isTyping['jorge-seller']).toBe(false)
      })
    })
  })

  describe('Data Export', () => {
    it('exports complete workflow data', () => {
      const { result } = renderHook(() => useChatStore())

      const workflowId = 'workflow_export'

      act(() => {
        // Set up comprehensive test data
        result.current.workflows[workflowId] = {
          id: workflowId,
          contactId: 'contact_export',
          locationId: 'loc_export',
          activeBot: 'jorge-seller',
          stage: 'qualification',
          handoffQueue: [],
          createdAt: new Date().toISOString(),
          lastUpdate: new Date().toISOString(),
          priority: 'high'
        }

        result.current.qualificationStates['contact_export'] = {
          currentQuestion: 2,
          questionsAnswered: 2,
          temperature: 'warm',
          confrontationalEffectiveness: 78,
          stallsDetected: 0
        }

        const exportData = result.current.exportWorkflowData(workflowId)

        expect(exportData).toEqual({
          workflow: result.current.workflows[workflowId],
          qualificationState: result.current.qualificationStates['contact_export'],
          automationState: result.current.automationStates['contact_export'],
          analysisState: result.current.analysisStates['contact_export'],
          conversations: expect.any(Array),
          botMessages: expect.any(Array)
        })
      })
    })
  })
})

describe('Jorge Workflow Hook', () => {
  it('provides workflow management interface', () => {
    const { result } = renderHook(() => useJorgeWorkflow())

    expect(result.current).toEqual({
      workflows: expect.any(Object),
      activeWorkflow: null,
      createWorkflow: expect.any(Function),
      updateWorkflowStage: expect.any(Function),
      initiateHandoff: expect.any(Function),
      escalateToHuman: expect.any(Function)
    })
  })
})

describe('Multi-Bot Coordination Hook', () => {
  it('provides bot coordination interface', () => {
    const { result } = renderHook(() => useMultiBotCoordination())

    expect(result.current).toEqual({
      botStatuses: expect.any(Object),
      qualificationStates: expect.any(Object),
      automationStates: expect.any(Object),
      analysisStates: expect.any(Object),
      botMessages: expect.any(Array),
      metrics: expect.any(Object),
      startJorgeSellerQualification: expect.any(Function),
      triggerLeadAutomation: expect.any(Function),
      requestIntentAnalysis: expect.any(Function)
    })
  })
})

describe('Real-time Coordination Hook', () => {
  it('provides real-time connection interface', () => {
    const { result } = renderHook(() => useRealTimeCoordination())

    expect(result.current).toEqual({
      connected: expect.any(Boolean),
      lastUpdate: null,
      connect: expect.any(Function),
      disconnect: expect.any(Function)
    })
  })
})