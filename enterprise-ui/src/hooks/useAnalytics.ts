// Jorge Real Estate AI Analytics Hook
// React hook for comprehensive analytics data management and real-time updates

import { useState, useEffect, useCallback, useMemo } from 'react'
import {
  PerformanceReport,
  PerformanceMetrics,
  DateRange,
  AnalyticsQuery,
  RealTimeMetrics,
  BotPerformanceData,
  RevenueAnalysis,
  LeadQualityAnalysis,
  BenchmarkComparison,
  AIInsight,
  ActionableRecommendation,
  ChartDataPoint,
  ComparisonChartData
} from '@/types/analytics'
import { JorgeAnalyticsEngine } from '@/lib/analytics/MetricsEngine'
import { JorgeReportGenerator } from '@/lib/analytics/ReportGenerator'

interface UseAnalyticsOptions {
  dateRange?: DateRange
  autoRefresh?: boolean
  refreshInterval?: number
  includeRealTime?: boolean
}

interface UseAnalyticsReturn {
  // Core Data
  metrics: PerformanceMetrics | null
  reports: PerformanceReport[]
  realTimeMetrics: RealTimeMetrics | null

  // Calculated Data
  benchmarkComparisons: BenchmarkComparison[]
  insights: AIInsight[]
  recommendations: ActionableRecommendation[]

  // Chart Data
  revenueWaterfallData: any[]
  comparisonChartData: ComparisonChartData[]
  botPerformanceTrends: ChartDataPoint[][]

  // Loading States
  isLoading: boolean
  isGeneratingReport: boolean
  isRefreshing: boolean

  // Error Handling
  error: string | null
  lastUpdated: Date | null

  // Actions
  refreshData: () => Promise<void>
  generateReport: (templateId: string, customizations?: any) => Promise<PerformanceReport>
  exportReport: (reportId: string, format: 'pdf' | 'powerpoint' | 'excel') => Promise<Blob>
  updateDateRange: (range: DateRange) => void

  // Real-time Control
  startRealTimeUpdates: () => void
  stopRealTimeUpdates: () => void

  // Utilities
  formatMetric: (value: number, type: 'currency' | 'percentage' | 'number' | 'time') => string
  calculateTrend: (current: number, previous: number) => { direction: 'up' | 'down' | 'stable', change: number }
}

export function useAnalytics(options: UseAnalyticsOptions = {}): UseAnalyticsReturn {
  const {
    dateRange = JorgeAnalyticsEngine.generateDateRange('month'),
    autoRefresh = true,
    refreshInterval = 300000, // 5 minutes
    includeRealTime = true
  } = options

  // State Management
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null)
  const [reports, setReports] = useState<PerformanceReport[]>([])
  const [realTimeMetrics, setRealTimeMetrics] = useState<RealTimeMetrics | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isGeneratingReport, setIsGeneratingReport] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [currentDateRange, setCurrentDateRange] = useState<DateRange>(dateRange)

  // Real-time WebSocket state
  const [realTimeConnection, setRealTimeConnection] = useState<WebSocket | null>(null)
  const [realTimeEnabled, setRealTimeEnabled] = useState(includeRealTime)

  // Calculate all metrics
  const calculateMetrics = useCallback(async (): Promise<PerformanceMetrics> => {
    const botMetrics: BotPerformanceData[] = [
      JorgeAnalyticsEngine.calculateBotPerformance('jorge-seller', {
        conversations: 247,
        successful_qualifications: 215,
        conversion_rate: 0.71
      }, currentDateRange),
      JorgeAnalyticsEngine.calculateBotPerformance('lead-bot', {
        sequences: 156,
        completed_sequences: 142,
        cma_reports: 89
      }, currentDateRange),
      JorgeAnalyticsEngine.calculateBotPerformance('intent-decoder', {
        analyses: 423,
        successful_analyses: 412
      }, currentDateRange)
    ]

    return {
      botMetrics,
      revenueMetrics: JorgeAnalyticsEngine.calculateRevenueAnalysis(currentDateRange),
      leadMetrics: JorgeAnalyticsEngine.calculateLeadQualityAnalysis(currentDateRange),
      marketMetrics: JorgeAnalyticsEngine.calculateMarketIntelligence(currentDateRange),
      clientSatisfaction: JorgeAnalyticsEngine.calculateSatisfactionMetrics(),
      operationalEfficiency: JorgeAnalyticsEngine.calculateEfficiencyMetrics(),
      competitiveAnalysis: JorgeAnalyticsEngine.calculateCompetitiveAnalysis()
    }
  }, [currentDateRange])

  // Main data fetching function
  const fetchAnalyticsData = useCallback(async () => {
    try {
      setError(null)
      const newMetrics = await calculateMetrics()
      setMetrics(newMetrics)
      setLastUpdated(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics data')
      console.error('Analytics fetch error:', err)
    }
  }, [calculateMetrics])

  // Refresh data with loading state
  const refreshData = useCallback(async () => {
    setIsRefreshing(true)
    await fetchAnalyticsData()
    setIsRefreshing(false)
  }, [fetchAnalyticsData])

  // Generate new report
  const generateReport = useCallback(async (
    templateId: string,
    customizations?: any
  ): Promise<PerformanceReport> => {
    setIsGeneratingReport(true)
    setError(null)

    try {
      const report = await JorgeReportGenerator.generateReport(
        templateId,
        currentDateRange,
        customizations
      )

      setReports(prev => [report, ...prev])
      return report
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to generate report'
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setIsGeneratingReport(false)
    }
  }, [currentDateRange])

  // Export report functionality
  const exportReport = useCallback(async (
    reportId: string,
    format: 'pdf' | 'powerpoint' | 'excel'
  ): Promise<Blob> => {
    const report = reports.find(r => r.id === reportId)
    if (!report) {
      throw new Error('Report not found')
    }

    try {
      switch (format) {
        case 'pdf':
          return await JorgeReportGenerator.exportToPDF(report)
        case 'powerpoint':
          return await JorgeReportGenerator.exportToPowerPoint(report)
        case 'excel':
          return await JorgeReportGenerator.exportToExcel(report)
        default:
          throw new Error(`Unsupported export format: ${format}`)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to export report'
      setError(errorMessage)
      throw new Error(errorMessage)
    }
  }, [reports])

  // Update date range
  const updateDateRange = useCallback((range: DateRange) => {
    setCurrentDateRange(range)
  }, [])

  // Real-time WebSocket connection management
  const startRealTimeUpdates = useCallback(() => {
    if (realTimeConnection?.readyState === WebSocket.OPEN) return

    try {
      const ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8080'}/analytics`)

      ws.onopen = () => {
        console.log('✅ Real-time analytics connection established')
        setRealTimeConnection(ws)
        setRealTimeEnabled(true)
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'metrics_update') {
            setRealTimeMetrics(data.metrics)
          } else if (data.type === 'bot_performance_update') {
            // Update specific bot metrics
            setMetrics(prev => {
              if (!prev) return prev

              const updatedBotMetrics = prev.botMetrics.map(bot =>
                bot.botType === data.botType
                  ? { ...bot, ...data.updates }
                  : bot
              )

              return { ...prev, botMetrics: updatedBotMetrics }
            })
          }
        } catch (err) {
          console.error('Failed to parse real-time data:', err)
        }
      }

      ws.onclose = () => {
        console.log('Real-time analytics connection closed')
        setRealTimeConnection(null)
        setRealTimeEnabled(false)
      }

      ws.onerror = (error) => {
        console.error('Real-time analytics connection error:', error)
        setRealTimeConnection(null)
        setRealTimeEnabled(false)
      }
    } catch (err) {
      console.error('Failed to establish real-time connection:', err)
      setRealTimeEnabled(false)
    }
  }, [realTimeConnection])

  const stopRealTimeUpdates = useCallback(() => {
    if (realTimeConnection) {
      realTimeConnection.close()
      setRealTimeConnection(null)
      setRealTimeEnabled(false)
    }
  }, [realTimeConnection])

  // Calculated values
  const benchmarkComparisons = useMemo(() =>
    JorgeAnalyticsEngine.generateBenchmarkComparisons()
  , [])

  const insights = useMemo(() =>
    metrics ? JorgeAnalyticsEngine.generateAIInsights(metrics) : []
  , [metrics])

  const recommendations = useMemo(() =>
    metrics ? JorgeAnalyticsEngine.generateRecommendations(metrics) : []
  , [metrics])

  const revenueWaterfallData = useMemo(() =>
    JorgeAnalyticsEngine.generateRevenueWaterfallData()
  , [])

  const comparisonChartData = useMemo(() =>
    JorgeAnalyticsEngine.generateComparisonChartData()
  , [])

  const botPerformanceTrends = useMemo(() => {
    if (!metrics) return []

    return metrics.botMetrics.map(bot => {
      // Generate trend data for the last 30 days
      const days = 30
      const data: ChartDataPoint[] = []

      for (let i = days - 1; i >= 0; i--) {
        const date = new Date()
        date.setDate(date.getDate() - i)

        // Simulate some variance around the bot's performance metrics
        const baseAccuracy = bot.accuracy
        const variance = (Math.random() - 0.5) * 0.1 // ±5% variance

        data.push({
          date: date.toISOString().split('T')[0],
          value: Math.max(0, Math.min(1, baseAccuracy + variance)),
          label: `${bot.botName} Accuracy`,
          category: bot.botType,
          trend: variance > 0 ? 'up' : variance < 0 ? 'down' : 'stable'
        })
      }

      return data
    })
  }, [metrics])

  // Initial data load
  useEffect(() => {
    const loadInitialData = async () => {
      setIsLoading(true)
      await fetchAnalyticsData()
      setIsLoading(false)
    }

    loadInitialData()
  }, [fetchAnalyticsData])

  // Auto-refresh setup
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      if (!isLoading && !isGeneratingReport) {
        refreshData()
      }
    }, refreshInterval)

    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval, refreshData, isLoading, isGeneratingReport])

  // Real-time connection setup
  useEffect(() => {
    if (includeRealTime) {
      startRealTimeUpdates()
    }

    return () => {
      stopRealTimeUpdates()
    }
  }, [includeRealTime, startRealTimeUpdates, stopRealTimeUpdates])

  // Date range change effect
  useEffect(() => {
    refreshData()
  }, [currentDateRange, refreshData])

  // Utility functions
  const formatMetric = useCallback((value: number, type: 'currency' | 'percentage' | 'number' | 'time') =>
    JorgeAnalyticsEngine.formatMetric(value, type)
  , [])

  const calculateTrend = useCallback((current: number, previous: number) =>
    JorgeAnalyticsEngine.calculateTrend(current, previous)
  , [])

  return {
    // Core Data
    metrics,
    reports,
    realTimeMetrics,

    // Calculated Data
    benchmarkComparisons,
    insights,
    recommendations,

    // Chart Data
    revenueWaterfallData,
    comparisonChartData,
    botPerformanceTrends,

    // Loading States
    isLoading,
    isGeneratingReport,
    isRefreshing,

    // Error Handling
    error,
    lastUpdated,

    // Actions
    refreshData,
    generateReport,
    exportReport,
    updateDateRange,

    // Real-time Control
    startRealTimeUpdates,
    stopRealTimeUpdates,

    // Utilities
    formatMetric,
    calculateTrend
  }
}

// Specialized hooks for specific analytics needs
export function useRevenueAnalytics(dateRange?: DateRange) {
  const analytics = useAnalytics({ dateRange, autoRefresh: true })

  return {
    revenueMetrics: analytics.metrics?.revenueMetrics || null,
    revenueWaterfallData: analytics.revenueWaterfallData,
    isLoading: analytics.isLoading,
    error: analytics.error,
    refreshData: analytics.refreshData
  }
}

export function useBotPerformance(botType?: string) {
  const analytics = useAnalytics({ autoRefresh: true })

  const botData = analytics.metrics?.botMetrics.find(bot =>
    botType ? bot.botType === botType : true
  ) || null

  return {
    botPerformance: botData,
    allBots: analytics.metrics?.botMetrics || [],
    trends: analytics.botPerformanceTrends,
    isLoading: analytics.isLoading,
    error: analytics.error,
    refreshData: analytics.refreshData
  }
}

export function useCompetitiveAnalysis() {
  const analytics = useAnalytics({ autoRefresh: true })

  return {
    competitiveMetrics: analytics.metrics?.competitiveAnalysis || null,
    benchmarkComparisons: analytics.benchmarkComparisons,
    comparisonChartData: analytics.comparisonChartData,
    insights: analytics.insights.filter(insight => insight.category === 'competitive'),
    isLoading: analytics.isLoading,
    error: analytics.error,
    refreshData: analytics.refreshData
  }
}

export function useRealTimeMetrics() {
  const analytics = useAnalytics({
    includeRealTime: true,
    autoRefresh: true,
    refreshInterval: 30000 // 30 seconds
  })

  return {
    realTimeMetrics: analytics.realTimeMetrics,
    isConnected: analytics.realTimeMetrics !== null,
    startUpdates: analytics.startRealTimeUpdates,
    stopUpdates: analytics.stopRealTimeUpdates,
    lastUpdated: analytics.lastUpdated
  }
}