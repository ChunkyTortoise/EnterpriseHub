/**
 * Jorge Command Center Component Tests
 * Comprehensive testing for the unified bot orchestration dashboard
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { JorgeCommandCenter } from '../JorgeCommandCenter'
import { useChatStore } from '@/store/useChatStore'
import { useWebSocket } from '@/components/providers/WebSocketProvider'
import { useBotStatus, useRealTimeMetrics } from '@/lib/hooks/useBotStatus'

// Mock dependencies
jest.mock('@/store/useChatStore')
jest.mock('@/components/providers/WebSocketProvider')
jest.mock('@/lib/hooks/useBotStatus')
jest.mock('@/lib/hooks/useRealTimeMetrics')
jest.mock('@/lib/jorge-api-client')

const mockUseChatStore = useChatStore as jest.MockedFunction<typeof useChatStore>
const mockUseWebSocket = useWebSocket as jest.MockedFunction<typeof useWebSocket>
const mockUseBotStatus = useBotStatus as jest.MockedFunction<typeof useBotStatus>
const mockUseRealTimeMetrics = useRealTimeMetrics as jest.MockedFunction<typeof useRealTimeMetrics>

// Test utilities
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})

const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = createTestQueryClient()
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

describe('JorgeCommandCenter', () => {
  const mockBotStatuses = {
    'jorge-seller': {
      status: 'active',
      activeConversations: 3,
      performance: {
        avgResponseTime: 1200,
        successRate: 87,
        totalProcessed: 15,
        errorsToday: 1
      },
      health: {
        responseTime: 1200,
        lastHealthCheck: new Date().toISOString()
      }
    },
    'lead-bot': {
      status: 'idle',
      activeConversations: 0,
      performance: {
        avgResponseTime: 800,
        successRate: 95,
        totalProcessed: 8,
        errorsToday: 0
      },
      health: {
        responseTime: 800,
        lastHealthCheck: new Date().toISOString()
      }
    },
    'intent-decoder': {
      status: 'processing',
      activeConversations: 1,
      performance: {
        avgResponseTime: 42,
        successRate: 96,
        totalProcessed: 25,
        errorsToday: 0
      },
      health: {
        responseTime: 42,
        lastHealthCheck: new Date().toISOString()
      }
    }
  }

  const mockMetrics = {
    conversations: {
      active: 4,
      completed_today: 12,
      hot_leads: 3,
      qualified_sellers: 8,
      avg_response_time_ms: 1000
    },
    jorge_seller_bot: {
      conversations_today: 15,
      qualified_sellers: 8,
      temperature_distribution: { hot: 3, warm: 4, cold: 1 },
      confrontational_effectiveness: 87
    },
    system_health: {
      overall_status: 'healthy' as const,
      redis_status: 'healthy' as const,
      ghl_api_status: 'connected' as const,
      claude_api_status: 'active' as const
    }
  }

  beforeEach(() => {
    // Reset all mocks
    jest.clearAllMocks()

    // Default mock implementations
    mockUseChatStore.mockReturnValue({
      startJorgeSellerConversation: jest.fn()
    } as any)

    mockUseWebSocket.mockReturnValue({
      connected: true,
      connectionState: 'connected',
      reconnect: jest.fn(),
      disconnect: jest.fn(),
      lastUpdate: new Date().toISOString(),
      error: null
    } as any)

    mockUseBotStatus.mockReturnValue({
      botStatus: mockBotStatuses,
      getOverallHealth: jest.fn().mockReturnValue('healthy'),
      getActiveBotsCount: jest.fn().mockReturnValue(2),
      isAnyBotProcessing: jest.fn().mockReturnValue(true),
      lastUpdate: new Date().toISOString()
    } as any)

    mockUseRealTimeMetrics.mockReturnValue({
      metrics: mockMetrics,
      isLoading: false,
      error: null,
      dataAge: 2,
      lastUpdate: new Date().toISOString()
    } as any)
  })

  describe('Rendering', () => {
    it('renders without crashing', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      expect(screen.getByText('Jorge Command Center')).toBeInTheDocument()
    })

    it('displays platform description', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      expect(screen.getByText(/Professional AI-powered real estate command center/)).toBeInTheDocument()
    })

    it('shows production ready badge', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      expect(screen.getByText('✅ Production Ready')).toBeInTheDocument()
      expect(screen.getByText('🤖 LangGraph Powered')).toBeInTheDocument()
    })
  })

  describe('Real-time Status Integration', () => {
    it('displays live connection status when connected', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      expect(screen.getByText('Live')).toBeInTheDocument()
      expect(screen.getByText('💚 Healthy')).toBeInTheDocument()
    })

    it('shows polling mode when disconnected', () => {
      mockUseWebSocket.mockReturnValue({
        connected: false,
        connectionState: 'disconnected',
        reconnect: jest.fn(),
        disconnect: jest.fn(),
        lastUpdate: null,
        error: 'Connection failed'
      } as any)

      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      expect(screen.getByText('Polling')).toBeInTheDocument()
    })

    it('displays connection error alert', () => {
      mockUseWebSocket.mockReturnValue({
        connected: false,
        connectionState: 'error',
        reconnect: jest.fn(),
        disconnect: jest.fn(),
        lastUpdate: null,
        error: 'WebSocket failed'
      } as any)

      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      expect(screen.getByText(/WebSocket connection failed/)).toBeInTheDocument()
    })
  })

  describe('System Metrics', () => {
    it('displays real-time conversation metrics', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      expect(screen.getByText('4')).toBeInTheDocument() // Active conversations
      expect(screen.getByText('8')).toBeInTheDocument() // Qualified sellers
      expect(screen.getByText('1000ms')).toBeInTheDocument() // Response time
    })

    it('shows data age indicator when connected', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      expect(screen.getByText(/Data age: 2s/)).toBeInTheDocument()
    })

    it('indicates processing activity', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      // Should show processing indicators for active bots
      expect(screen.getByText(/Bots processing/)).toBeInTheDocument()
    })
  })

  describe('Bot Performance Cards', () => {
    it('displays bot status cards with real-time data', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      // Jorge Seller Bot card
      expect(screen.getByText('Jorge Seller Bot')).toBeInTheDocument()
      expect(screen.getByText('Active')).toBeInTheDocument()

      // Lead Bot card
      expect(screen.getByText('Lead Bot')).toBeInTheDocument()
      expect(screen.getByText('Ready')).toBeInTheDocument()

      // Intent Decoder card
      expect(screen.getByText('Intent Decoder')).toBeInTheDocument()
      expect(screen.getByText('Processing')).toBeInTheDocument()
    })

    it('shows current step for active bots', () => {
      // Update mock to include current step
      const mockBotStatusesWithStep = {
        ...mockBotStatuses,
        'jorge-seller': {
          ...mockBotStatuses['jorge-seller'],
          currentStep: 'Q2 - Price Expectation'
        }
      }

      mockUseBotStatus.mockReturnValue({
        botStatus: mockBotStatusesWithStep,
        getOverallHealth: jest.fn().mockReturnValue('healthy'),
        getActiveBotsCount: jest.fn().mockReturnValue(2),
        isAnyBotProcessing: jest.fn().mockReturnValue(true),
        lastUpdate: new Date().toISOString()
      } as any)

      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      expect(screen.getByText('Q2 - Price Expectation')).toBeInTheDocument()
    })

    it('displays performance metrics correctly', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      // Check for response times
      expect(screen.getByText('1200ms')).toBeInTheDocument()
      expect(screen.getByText('42ms')).toBeInTheDocument()

      // Check for success rates
      expect(screen.getByText('87.0%')).toBeInTheDocument()
      expect(screen.getByText('96.0%')).toBeInTheDocument()
    })
  })

  describe('Analytics Tab', () => {
    it('displays real-time system status', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      // Switch to analytics tab
      fireEvent.click(screen.getByText('Performance Analytics'))

      expect(screen.getByText('Real-time System Status')).toBeInTheDocument()
      expect(screen.getByText('Connected')).toBeInTheDocument()
      expect(screen.getByText('healthy')).toBeInTheDocument()
    })

    it('shows Jorge seller metrics', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      fireEvent.click(screen.getByText('Performance Analytics'))

      expect(screen.getByText('Jorge Seller Metrics')).toBeInTheDocument()
      expect(screen.getByText('87%')).toBeInTheDocument() // Confrontational effectiveness
    })

    it('displays ML pipeline performance', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      fireEvent.click(screen.getByText('Performance Analytics'))

      expect(screen.getByText('ML Pipeline Metrics')).toBeInTheDocument()
      expect(screen.getByText('Target: 42ms • 95% accuracy')).toBeInTheDocument()
    })
  })

  describe('User Interactions', () => {
    it('handles bot conversation start', async () => {
      const mockStartConversation = jest.fn().mockResolvedValue('conv_123')
      mockUseChatStore.mockReturnValue({
        startJorgeSellerConversation: mockStartConversation
      } as any)

      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      const startButton = screen.getByText('Start Chat')
      fireEvent.click(startButton)

      await waitFor(() => {
        expect(mockStartConversation).toHaveBeenCalled()
      })
    })

    it('handles tab navigation', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      // Test tab switching
      fireEvent.click(screen.getByText('Active Chat'))
      expect(screen.getByText('No Active Chat')).toBeInTheDocument()

      fireEvent.click(screen.getByText('Performance Analytics'))
      expect(screen.getByText('Real-time System Status')).toBeInTheDocument()

      fireEvent.click(screen.getByText('Bot Dashboard'))
      expect(screen.getByText('Jorge Seller Bot')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('displays error state when metrics fail to load', () => {
      mockUseRealTimeMetrics.mockReturnValue({
        metrics: null,
        isLoading: false,
        error: new Error('Failed to fetch metrics'),
        dataAge: 0,
        lastUpdate: null
      } as any)

      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      // Should still render but show error indicators
      expect(screen.getByText('Jorge Command Center')).toBeInTheDocument()
    })

    it('handles WebSocket connection errors gracefully', () => {
      mockUseWebSocket.mockReturnValue({
        connected: false,
        connectionState: 'error',
        reconnect: jest.fn(),
        disconnect: jest.fn(),
        lastUpdate: null,
        error: 'Connection timeout'
      } as any)

      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      expect(screen.getByText(/Using polling mode for updates/)).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels for status indicators', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      const statusIndicators = screen.getAllByRole('status', { hidden: true })
      expect(statusIndicators.length).toBeGreaterThan(0)
    })

    it('supports keyboard navigation', () => {
      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      const buttons = screen.getAllByRole('button')
      buttons.forEach(button => {
        expect(button).not.toHaveAttribute('tabindex', '-1')
      })
    })
  })

  describe('Performance', () => {
    it('renders within acceptable time', () => {
      const startTime = performance.now()

      render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      const endTime = performance.now()
      const renderTime = endTime - startTime

      // Should render within 100ms
      expect(renderTime).toBeLessThan(100)
    })

    it('updates efficiently with new data', async () => {
      const { rerender } = render(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      // Update metrics
      const updatedMetrics = {
        ...mockMetrics,
        conversations: {
          ...mockMetrics.conversations,
          active: 5
        }
      }

      mockUseRealTimeMetrics.mockReturnValue({
        metrics: updatedMetrics,
        isLoading: false,
        error: null,
        dataAge: 1,
        lastUpdate: new Date().toISOString()
      } as any)

      rerender(
        <TestWrapper>
          <JorgeCommandCenter />
        </TestWrapper>
      )

      expect(screen.getByText('5')).toBeInTheDocument()
    })
  })
})