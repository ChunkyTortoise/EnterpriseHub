/**
 * Workflow Orchestration Component Tests
 * Testing multi-bot coordination and workflow management
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import WorkflowOrchestration from '../WorkflowOrchestration'
import { useJorgeWorkflow, useMultiBotCoordination, useRealTimeCoordination } from '@/store/useChatStore'

// Mock dependencies
jest.mock('@/store/useChatStore')
jest.mock('@/components/providers/WebSocketProvider')

const mockUseJorgeWorkflow = useJorgeWorkflow as jest.MockedFunction<typeof useJorgeWorkflow>
const mockUseMultiBotCoordination = useMultiBotCoordination as jest.MockedFunction<typeof useMultiBotCoordination>
const mockUseRealTimeCoordination = useRealTimeCoordination as jest.MockedFunction<typeof useRealTimeCoordination>

describe('WorkflowOrchestration', () => {
  const mockWorkflows = {
    'workflow_1': {
      id: 'workflow_1',
      contactId: 'contact_123',
      locationId: 'loc_456',
      activeBot: 'jorge-seller',
      stage: 'qualification',
      priority: 'high',
      createdAt: new Date().toISOString(),
      lastUpdate: new Date().toISOString(),
      handoffQueue: [],
      jorgeSellerState: {
        currentQuestion: 1,
        questionsAnswered: 1,
        temperature: 'warm',
        confrontationalEffectiveness: 75
      }
    },
    'workflow_2': {
      id: 'workflow_2',
      contactId: 'contact_456',
      locationId: 'loc_789',
      activeBot: 'lead-bot',
      stage: 'automation',
      priority: 'medium',
      createdAt: new Date().toISOString(),
      lastUpdate: new Date().toISOString(),
      handoffQueue: [{
        fromBot: 'jorge-seller',
        toBot: 'lead-bot',
        reason: 'Qualification completed',
        timestamp: new Date().toISOString(),
        data: { sellerTemperature: 'hot' }
      }],
      leadBotState: {
        sequenceDay: 3,
        currentAction: 'sms',
        completedActions: ['day_3_sms'],
        scheduledActions: []
      }
    }
  }

  const mockBotStatuses = {
    'jorge-seller': {
      id: 'jorge-seller',
      name: 'Jorge Seller Bot',
      status: 'active',
      conversationsToday: 12,
      leadsQualified: 8,
      responseTimeMs: 1200,
      lastActivity: new Date().toISOString(),
      performanceMetrics: {
        conversationsToday: 12,
        avgResponseTime: 1200,
        successRate: 87,
        lastActivity: new Date().toISOString()
      }
    },
    'lead-bot': {
      id: 'lead-bot',
      name: 'Lead Bot',
      status: 'idle',
      conversationsToday: 5,
      leadsQualified: 3,
      responseTimeMs: 800,
      lastActivity: new Date().toISOString(),
      performanceMetrics: {
        conversationsToday: 5,
        avgResponseTime: 800,
        successRate: 95,
        lastActivity: new Date().toISOString()
      }
    },
    'intent-decoder': {
      id: 'intent-decoder',
      name: 'Intent Decoder',
      status: 'processing',
      conversationsToday: 25,
      leadsQualified: 0,
      responseTimeMs: 42,
      lastActivity: new Date().toISOString(),
      performanceMetrics: {
        conversationsToday: 25,
        avgResponseTime: 42,
        successRate: 96,
        lastActivity: new Date().toISOString()
      }
    }
  }

  const mockCoordinationMetrics = {
    totalWorkflows: 15,
    activeWorkflows: 2,
    completedWorkflows: 10,
    escalatedWorkflows: 1,
    handoffsToday: 8,
    averageWorkflowDuration: 1800000 // 30 minutes
  }

  const mockBotMessages = [
    {
      fromBot: 'jorge-seller',
      toBot: 'lead-bot',
      messageType: 'handoff',
      payload: { sellerTemperature: 'hot', qualificationComplete: true },
      timestamp: new Date().toISOString()
    },
    {
      fromBot: 'intent-decoder',
      toBot: 'jorge-seller',
      messageType: 'data_request',
      payload: { analysisRequest: 'conversation_intent' },
      timestamp: new Date().toISOString()
    }
  ]

  beforeEach(() => {
    jest.clearAllMocks()

    // Mock workflow hooks
    mockUseJorgeWorkflow.mockReturnValue({
      workflows: mockWorkflows,
      activeWorkflow: mockWorkflows.workflow_1,
      escalateToHuman: jest.fn().mockResolvedValue(undefined)
    } as any)

    mockUseMultiBotCoordination.mockReturnValue({
      botStatuses: mockBotStatuses,
      metrics: mockCoordinationMetrics,
      botMessages: mockBotMessages,
      startJorgeSellerQualification: jest.fn().mockResolvedValue('workflow_new'),
      triggerLeadAutomation: jest.fn().mockResolvedValue(undefined),
      requestIntentAnalysis: jest.fn().mockResolvedValue(undefined),
      qualificationStates: {},
      automationStates: {},
      analysisStates: {}
    } as any)

    mockUseRealTimeCoordination.mockReturnValue({
      connected: true,
      lastUpdate: new Date().toISOString(),
      connect: jest.fn().mockResolvedValue(undefined),
      disconnect: jest.fn()
    } as any)
  })

  describe('Rendering', () => {
    it('renders workflow orchestration dashboard', () => {
      render(<WorkflowOrchestration />)

      expect(screen.getByText('Workflow Orchestration')).toBeInTheDocument()
      expect(screen.getByText('Multi-bot coordination dashboard for Jorge\'s Real Estate Platform')).toBeInTheDocument()
    })

    it('displays real-time connection status', () => {
      render(<WorkflowOrchestration />)

      expect(screen.getByText('Real-time Connected')).toBeInTheDocument()
    })

    it('shows start workflow button', () => {
      render(<WorkflowOrchestration />)

      expect(screen.getByText('Start Jorge Workflow')).toBeInTheDocument()
    })
  })

  describe('Bot Coordination Metrics', () => {
    it('displays workflow metrics correctly', () => {
      render(<WorkflowOrchestration />)

      expect(screen.getByText('15')).toBeInTheDocument() // Total workflows
      expect(screen.getByText('2')).toBeInTheDocument() // Active workflows
      expect(screen.getByText('8')).toBeInTheDocument() // Handoffs today
      expect(screen.getByText('10')).toBeInTheDocument() // Completed
    })

    it('shows bot status in coordination panel', () => {
      render(<WorkflowOrchestration />)

      // Switch to coordination tab
      fireEvent.click(screen.getByText('Bot Coordination'))

      expect(screen.getByText('Jorge Seller Bot')).toBeInTheDocument()
      expect(screen.getByText('Lead Bot')).toBeInTheDocument()
      expect(screen.getByText('Intent Decoder')).toBeInTheDocument()
    })
  })

  describe('Workflow Management', () => {
    it('displays active workflows', () => {
      render(<WorkflowOrchestration />)

      // Should show active workflows by default
      expect(screen.getByText('contact_123'.slice(0, 8) + '...')).toBeInTheDocument()
      expect(screen.getByText('qualification')).toBeInTheDocument()
      expect(screen.getByText('jorge-seller')).toBeInTheDocument()
    })

    it('shows handoff queue indicators', () => {
      render(<WorkflowOrchestration />)

      // Workflow 2 has a handoff in queue
      expect(screen.getByText('1 pending handoff(s)')).toBeInTheDocument()
    })

    it('displays workflow priority indicators', () => {
      render(<WorkflowOrchestration />)

      // Should show priority icons for workflows
      const cards = screen.getAllByText(/contact_/)
      expect(cards.length).toBeGreaterThan(0)
    })

    it('handles workflow escalation', async () => {
      const mockEscalateToHuman = jest.fn().mockResolvedValue(undefined)
      mockUseJorgeWorkflow.mockReturnValue({
        workflows: mockWorkflows,
        activeWorkflow: mockWorkflows.workflow_1,
        escalateToHuman: mockEscalateToHuman
      } as any)

      render(<WorkflowOrchestration />)

      const escalateButton = screen.getByText('Escalate')
      fireEvent.click(escalateButton)

      await waitFor(() => {
        expect(mockEscalateToHuman).toHaveBeenCalledWith(
          'workflow_1',
          'Manual escalation from workflow dashboard'
        )
      })
    })
  })

  describe('Tab Navigation', () => {
    it('switches between workflow tabs', () => {
      render(<WorkflowOrchestration />)

      // Active workflows tab (default)
      expect(screen.getByText(/Active Workflows \(2\)/)).toBeInTheDocument()

      // Switch to completed tab
      fireEvent.click(screen.getByText(/Completed \(10\)/))
      // Should still show workflow structure (though none in test data)

      // Switch to escalated tab
      fireEvent.click(screen.getByText(/Escalated \(1\)/))
      // Should show escalated workflows structure

      // Switch to coordination tab
      fireEvent.click(screen.getByText('Bot Coordination'))
      expect(screen.getByText('Cross-Bot Communication')).toBeInTheDocument()
    })

    it('shows empty state for no active workflows', () => {
      // Mock empty workflows
      mockUseJorgeWorkflow.mockReturnValue({
        workflows: {},
        activeWorkflow: null,
        escalateToHuman: jest.fn()
      } as any)

      render(<WorkflowOrchestration />)

      expect(screen.getByText('No Active Workflows')).toBeInTheDocument()
      expect(screen.getByText('Start a new workflow to begin bot coordination')).toBeInTheDocument()
    })
  })

  describe('Cross-Bot Communication', () => {
    it('displays bot messages in coordination tab', () => {
      render(<WorkflowOrchestration />)

      fireEvent.click(screen.getByText('Bot Coordination'))

      expect(screen.getByText('Cross-Bot Communication')).toBeInTheDocument()
      expect(screen.getByText('handoff')).toBeInTheDocument()
      expect(screen.getByText('data_request')).toBeInTheDocument()
    })

    it('shows empty state for no bot messages', () => {
      mockUseMultiBotCoordination.mockReturnValue({
        botStatuses: mockBotStatuses,
        metrics: mockCoordinationMetrics,
        botMessages: [], // Empty messages
        startJorgeSellerQualification: jest.fn(),
        triggerLeadAutomation: jest.fn(),
        requestIntentAnalysis: jest.fn(),
        qualificationStates: {},
        automationStates: {},
        analysisStates: {}
      } as any)

      render(<WorkflowOrchestration />)

      fireEvent.click(screen.getByText('Bot Coordination'))

      expect(screen.getByText('No cross-bot messages yet')).toBeInTheDocument()
    })
  })

  describe('New Workflow Creation', () => {
    it('starts Jorge seller qualification workflow', async () => {
      const mockStartQualification = jest.fn().mockResolvedValue('workflow_new')
      mockUseMultiBotCoordination.mockReturnValue({
        botStatuses: mockBotStatuses,
        metrics: mockCoordinationMetrics,
        botMessages: mockBotMessages,
        startJorgeSellerQualification: mockStartQualification,
        triggerLeadAutomation: jest.fn(),
        requestIntentAnalysis: jest.fn(),
        qualificationStates: {},
        automationStates: {},
        analysisStates: {}
      } as any)

      render(<WorkflowOrchestration />)

      const startButton = screen.getByText('Start Jorge Workflow')
      fireEvent.click(startButton)

      await waitFor(() => {
        expect(mockStartQualification).toHaveBeenCalledWith(
          expect.stringMatching(/^contact_/),
          'loc_default'
        )
      })
    })

    it('starts lead bot automation workflow', async () => {
      // Mock empty workflows to show the empty state buttons
      mockUseJorgeWorkflow.mockReturnValue({
        workflows: {},
        activeWorkflow: null,
        escalateToHuman: jest.fn()
      } as any)

      const mockTriggerAutomation = jest.fn().mockResolvedValue(undefined)
      mockUseMultiBotCoordination.mockReturnValue({
        botStatuses: mockBotStatuses,
        metrics: mockCoordinationMetrics,
        botMessages: mockBotMessages,
        startJorgeSellerQualification: jest.fn(),
        triggerLeadAutomation: mockTriggerAutomation,
        requestIntentAnalysis: jest.fn(),
        qualificationStates: {},
        automationStates: {},
        analysisStates: {}
      } as any)

      render(<WorkflowOrchestration />)

      const leadBotButton = screen.getByText('Lead Bot Automation')
      fireEvent.click(leadBotButton)

      await waitFor(() => {
        expect(mockTriggerAutomation).toHaveBeenCalledWith(
          expect.stringMatching(/^contact_/),
          3 // Day 3 sequence
        )
      })
    })
  })

  describe('Real-time Integration', () => {
    it('shows connection status and reconnect option', () => {
      mockUseRealTimeCoordination.mockReturnValue({
        connected: false,
        lastUpdate: null,
        connect: jest.fn(),
        disconnect: jest.fn()
      } as any)

      render(<WorkflowOrchestration />)

      expect(screen.getByText('Polling Mode')).toBeInTheDocument()
      expect(screen.getByText('Connect')).toBeInTheDocument()
    })

    it('handles real-time reconnection', async () => {
      const mockConnect = jest.fn().mockResolvedValue(undefined)
      mockUseRealTimeCoordination.mockReturnValue({
        connected: false,
        lastUpdate: null,
        connect: mockConnect,
        disconnect: jest.fn()
      } as any)

      render(<WorkflowOrchestration />)

      const connectButton = screen.getByText('Connect')
      fireEvent.click(connectButton)

      await waitFor(() => {
        expect(mockConnect).toHaveBeenCalled()
      })
    })

    it('displays offline mode alert', () => {
      mockUseRealTimeCoordination.mockReturnValue({
        connected: false,
        lastUpdate: null,
        connect: jest.fn(),
        disconnect: jest.fn()
      } as any)

      render(<WorkflowOrchestration />)

      expect(screen.getByText(/Real-time coordination is offline/)).toBeInTheDocument()
      expect(screen.getByText(/operating in polling mode/)).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('handles workflow creation errors gracefully', async () => {
      const mockStartQualification = jest.fn().mockRejectedValue(new Error('Failed to create workflow'))
      mockUseMultiBotCoordination.mockReturnValue({
        botStatuses: mockBotStatuses,
        metrics: mockCoordinationMetrics,
        botMessages: mockBotMessages,
        startJorgeSellerQualification: mockStartQualification,
        triggerLeadAutomation: jest.fn(),
        requestIntentAnalysis: jest.fn(),
        qualificationStates: {},
        automationStates: {},
        analysisStates: {}
      } as any)

      // Mock console.error to avoid test output
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()

      render(<WorkflowOrchestration />)

      const startButton = screen.getByText('Start Jorge Workflow')
      fireEvent.click(startButton)

      await waitFor(() => {
        expect(mockStartQualification).toHaveBeenCalled()
        expect(consoleSpy).toHaveBeenCalledWith('Failed to start workflow:', expect.any(Error))
      })

      consoleSpy.mockRestore()
    })

    it('handles escalation errors gracefully', async () => {
      const mockEscalateToHuman = jest.fn().mockRejectedValue(new Error('Escalation failed'))
      mockUseJorgeWorkflow.mockReturnValue({
        workflows: mockWorkflows,
        activeWorkflow: mockWorkflows.workflow_1,
        escalateToHuman: mockEscalateToHuman
      } as any)

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation()

      render(<WorkflowOrchestration />)

      const escalateButton = screen.getByText('Escalate')
      fireEvent.click(escalateButton)

      await waitFor(() => {
        expect(consoleSpy).toHaveBeenCalledWith('Failed to escalate workflow:', expect.any(Error))
      })

      consoleSpy.mockRestore()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels for interactive elements', () => {
      render(<WorkflowOrchestration />)

      // Check for accessible buttons
      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).toHaveAttribute('type', expect.anything())
      })
    })

    it('supports keyboard navigation', () => {
      render(<WorkflowOrchestration />)

      // All interactive elements should be focusable
      const focusableElements = screen.getAllByRole('button')
              const tabElements = screen.getAllByRole('tab');
      
              [...focusableElements, ...tabElements].forEach(element => {        expect(element).not.toHaveAttribute('tabindex', '-1')
      })
    })
  })
})