// Jorge Real Estate AI Analytics & Performance Reporting Types
// Professional analytics system for demonstrating Jorge's competitive advantages

export interface DateRange {
  start: string
  end: string
}

export interface PerformanceReport {
  id: string
  title: string
  reportType: 'monthly' | 'quarterly' | 'annual' | 'custom' | 'client-presentation'
  period: DateRange
  metrics: PerformanceMetrics
  comparisons: BenchmarkComparison[]
  insights: AIInsight[]
  recommendations: ActionableRecommendation[]
  clientTestimonials: Testimonial[]
  exportFormats: ExportFormat[]
  createdAt: string
  updatedAt: string
  status: 'generating' | 'ready' | 'archived'
  visibility: 'internal' | 'client' | 'prospect'
}

export interface PerformanceMetrics {
  botMetrics: BotPerformanceData[]
  revenueMetrics: RevenueAnalysis
  leadMetrics: LeadQualityAnalysis
  marketMetrics: MarketIntelligenceData
  clientSatisfaction: SatisfactionMetrics
  operationalEfficiency: EfficiencyMetrics
  competitiveAnalysis: CompetitiveMetrics
}

export interface BotPerformanceData {
  botType: 'jorge-seller' | 'lead-bot' | 'intent-decoder' | 'property-scanner' | 'buyer-assistant'
  botName: string
  botDescription: string

  // Core Performance Metrics
  responseTime: {
    average: number
    median: number
    p95: number
    p99: number
  }

  // Accuracy & Quality Metrics
  accuracy: number
  confidenceScore: number
  conversationVolume: number
  conversationSuccess: number
  conversionRate: number

  // Jorge-Specific Metrics
  sellerQualificationRate?: number
  temperatureAccuracy?: number
  stallBreakerSuccess?: number
  confrontationalEffectiveness?: number

  // Lead Bot Specific
  sequenceCompletionRate?: number
  nurtureTouchpoints?: number
  voiceCallSuccess?: number
  cmaGenerated?: number

  // Client Experience
  clientSatisfactionScore: number
  escalationRate: number
  complaintRate: number

  // Operational Excellence
  uptime: number
  errorRate: number
  lastActivity: string

  // Trend Analysis
  trendDirection: 'improving' | 'stable' | 'declining'
  monthOverMonthChange: number
  yearOverYearChange: number
}

export interface RevenueAnalysis {
  // Core Revenue Metrics
  totalRevenue: number
  totalCommission: number
  averageCommission: number

  // Transaction Analysis
  transactionVolume: number
  averageTransactionValue: number
  averageDaysToClose: number

  // Jorge AI Impact Analysis
  preAI: {
    monthlyTransactions: number
    averageCommission: number
    conversionRate: number
    averageDaysToClose: number
  }

  postAI: {
    monthlyTransactions: number
    averageCommission: number
    conversionRate: number
    averageDaysToClose: number
  }

  // ROI Calculation
  aiImplementationCost: number
  monthlyROI: number
  annualROIProjection: number
  paybackPeriod: number // in months

  // Growth Projections
  projectedAnnualRevenue: number
  marketShareGrowth: number
  competitiveAdvantage: number
}

export interface LeadQualityAnalysis {
  // Lead Volume & Quality
  totalLeads: number
  qualifiedLeads: number
  hotLeads: number
  conversionRate: number

  // Jorge Qualification Process
  sellerLeads: {
    total: number
    qualified: number
    qualificationRate: number
    averageTemperatureScore: number
    stallsHandled: number
    motivatedSellers: number
  }

  // Lead Response & Engagement
  averageResponseTime: number // in minutes
  leadEngagementRate: number
  followUpCompletionRate: number

  // Lead Scoring Distribution
  scoreDistribution: {
    cold: number    // 0-25
    lukewarm: number // 26-49
    warm: number    // 50-74
    hot: number     // 75-100
  }

  // Lead Source Performance
  leadSources: Array<{
    source: string
    volume: number
    quality: number
    conversionRate: number
    costPerLead: number
    roi: number
  }>

  // Lifecycle Performance
  lifecycle: {
    averageNurtureTime: number
    touchpointsToConversion: number
    dropOffStage: string
    optimizationOpportunities: string[]
  }
}

export interface MarketIntelligenceData {
  // Market Analysis Delivered
  cmaReports: number
  marketAnalyses: number
  pricingRecommendations: number
  timingInsights: number

  // Accuracy & Impact
  cmaAccuracy: number
  pricingOptimization: number
  marketTrendAccuracy: number
  timingRecommendationSuccess: number

  // Competitive Intelligence
  competitorTracking: {
    agentsMonitored: number
    marketShareAnalysis: number
    pricingComparisons: number
    strategicAdvantages: string[]
  }

  // Client Value Delivered
  averageValueIncrease: number
  timeToMarketReduction: number
  marketingEfficiencyGain: number
  clientEducationPoints: number
}

export interface SatisfactionMetrics {
  // Net Promoter Score
  npsScore: number
  npsResponses: number
  promoters: number
  passives: number
  detractors: number

  // Client Satisfaction Breakdown
  botExperience: number
  responseQuality: number
  professionalismRating: number
  technologyAdvantage: number
  overallSatisfaction: number

  // Retention & Growth
  clientRetentionRate: number
  referralGenerated: number
  upsellSuccess: number
  repeatBusinessRate: number

  // Testimonial Data
  testimonialCount: number
  averageRating: number
  strongRecommendations: number
  caseStudiesAvailable: number
}

export interface EfficiencyMetrics {
  // Operational Efficiency
  processAutomation: number
  manualTaskReduction: number
  timeToResponseImprovement: number
  workflowOptimization: number

  // Cost Savings
  operationalCostReduction: number
  marketingEfficiency: number
  leadProcessingCost: number
  customerAcquisitionCost: number

  // Resource Utilization
  botUtilizationRate: number
  peakPerformancePeriods: string[]
  scalabilityFactor: number
  capacityUtilization: number
}

export interface CompetitiveMetrics {
  // Market Position
  marketRanking: number
  marketShare: number
  competitiveAdvantage: string[]
  differentiationFactors: string[]

  // Performance vs Competition
  responseTimeComparison: number
  conversionRateComparison: number
  technologyLeadership: number
  clientSatisfactionComparison: number

  // Competitive Intelligence
  competitorAnalysis: Array<{
    competitorName: string
    marketShare: number
    strengths: string[]
    weaknesses: string[]
    jorgeAdvantages: string[]
  }>
}

export interface BenchmarkComparison {
  metric: string
  jorgeValue: number
  industryAverage: number
  topQuartile: number
  improvement: number
  ranking: 'leader' | 'above-average' | 'average' | 'below-average'
  explanation: string
}

export interface AIInsight {
  id: string
  category: 'performance' | 'optimization' | 'market' | 'client' | 'competitive'
  title: string
  description: string
  impact: 'high' | 'medium' | 'low'
  actionable: boolean
  recommendation?: string
  dataSupport: string[]
  confidence: number
  timestamp: string
}

export interface ActionableRecommendation {
  id: string
  title: string
  description: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  category: 'bot-optimization' | 'process-improvement' | 'market-strategy' | 'client-experience'
  estimatedImpact: string
  implementationTime: string
  resourceRequirement: 'low' | 'medium' | 'high'
  expectedROI: number
  actionSteps: string[]
}

export interface Testimonial {
  id: string
  clientName: string
  clientType: 'seller' | 'buyer' | 'investor' | 'referral-partner'
  quote: string
  rating: number
  transactionValue?: number
  outcome: string
  jorgeAdvantage: string[]
  date: string
  verified: boolean
  featured: boolean
}

export interface ExportFormat {
  format: 'pdf' | 'powerpoint' | 'excel' | 'json' | 'image'
  name: string
  description: string
  size?: string
  available: boolean
}

// Chart Data Types
export interface ChartDataPoint {
  date: string
  value: number
  label?: string
  category?: string
  trend?: 'up' | 'down' | 'stable'
}

export interface ComparisonChartData {
  metric: string
  before: number
  after: number
  improvement: number
  color: string
}

export interface RevenueWaterfallData {
  category: string
  value: number
  type: 'positive' | 'negative' | 'total'
  description: string
}

export interface BotPerformanceTrend {
  bot: string
  timeRange: string
  metrics: {
    accuracy: ChartDataPoint[]
    responseTime: ChartDataPoint[]
    satisfaction: ChartDataPoint[]
    volume: ChartDataPoint[]
  }
}

// Report Builder Types
export interface ReportTemplate {
  id: string
  name: string
  description: string
  type: 'executive-summary' | 'detailed-analysis' | 'client-presentation' | 'competitive-analysis'
  sections: ReportSection[]
  estimatedGenerationTime: number
  targetAudience: string[]
}

export interface ReportSection {
  id: string
  title: string
  type: 'metrics' | 'chart' | 'insights' | 'testimonials' | 'recommendations'
  required: boolean
  customizable: boolean
  dataRequirements: string[]
}

// Analytics Query Types
export interface AnalyticsQuery {
  dateRange: DateRange
  bots?: string[]
  metrics?: string[]
  groupBy?: 'day' | 'week' | 'month' | 'quarter'
  filters?: Record<string, any>
  includeComparisons?: boolean
  includePredictions?: boolean
}

export interface AnalyticsResponse {
  query: AnalyticsQuery
  data: PerformanceMetrics
  generatedAt: string
  cacheExpiresAt?: string
  insights: AIInsight[]
  recommendations: ActionableRecommendation[]
}

// Presentation Mode Types
export interface PresentationConfig {
  mode: 'fullscreen' | 'windowed'
  autoAdvance: boolean
  autoAdvanceDelay?: number
  showSpeakerNotes: boolean
  showProgressBar: boolean
  theme: 'jorge-professional' | 'jorge-executive' | 'client-friendly'
  transitions: boolean
}

export interface PresentationSlide {
  id: string
  title: string
  subtitle?: string
  type: 'title' | 'metrics' | 'chart' | 'comparison' | 'testimonial' | 'summary'
  content: any
  speakerNotes?: string
  duration?: number
}

// Real-time Analytics Types
export interface RealTimeMetrics {
  botsOnline: number
  activeConversations: number
  leadsProcessedToday: number
  revenueToday: number
  averageResponseTime: number
  clientSatisfactionLive: number
  lastUpdated: string
}

export interface MetricsUpdate {
  metric: string
  value: number
  change: number
  trend: 'up' | 'down' | 'stable'
  timestamp: string
}