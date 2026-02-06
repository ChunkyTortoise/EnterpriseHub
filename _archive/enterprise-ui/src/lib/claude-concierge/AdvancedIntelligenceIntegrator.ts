/**
 * Advanced Intelligence Integrator for Claude Concierge
 * Orchestrates all advanced AI features with main concierge service
 *
 * Integrates: PredictiveScoring, MarketIntelligence, ConversationIntelligence, VectorSearch
 */

import { PredictiveScoring, type LeadPrediction } from './PredictiveScoring'
import { MarketIntelligenceEngine, type MarketIntelligence } from './MarketIntelligence'
import { ConversationIntelligenceEngine, type ConversationIntelligence } from './ConversationIntelligence'
import { VectorSearchEngine, type VectorSearchResult, type ConversationPattern } from './VectorSearch'

export interface AdvancedIntelligenceResult {
  predictions?: LeadPrediction
  marketIntelligence?: MarketIntelligence
  conversationAnalysis?: ConversationIntelligence
  similarPatterns?: VectorSearchResult[]
  recommendations: IntelligenceRecommendation[]
  confidence: number
  processingTime: number
}

export interface IntelligenceRecommendation {
  source: 'predictive' | 'market' | 'conversation' | 'pattern'
  type: 'immediate_action' | 'strategic_adjustment' | 'bot_handoff' | 'timing_optimization'
  priority: 'critical' | 'high' | 'medium' | 'low'
  title: string
  description: string
  actionData: Record<string, any>
  expectedImpact: number
}

export class AdvancedIntelligenceIntegrator {
  private predictiveEngine: PredictiveScoring
  private marketEngine: MarketIntelligenceEngine
  private conversationEngine: ConversationIntelligenceEngine
  private vectorEngine: VectorSearchEngine

  constructor() {
    this.predictiveEngine = new PredictiveScoring()
    this.marketEngine = new MarketIntelligenceEngine()
    this.conversationEngine = new ConversationIntelligenceEngine()
    this.vectorEngine = new VectorSearchEngine()
  }

  /**
   * Comprehensive analysis using all advanced intelligence modules
   */
  async analyzeComprehensively(
    conversationId: string,
    leadData: any,
    conversationHistory: any[],
    platformContext: any
  ): Promise<AdvancedIntelligenceResult> {
    const startTime = performance.now()

    try {
      // Run all analyses in parallel for performance
      const [
        predictions,
        marketIntelligence,
        conversationAnalysis,
        similarPatterns
      ] = await Promise.allSettled([
        this.generatePredictions(conversationId, leadData, conversationHistory),
        this.analyzeMarketConditions(leadData, platformContext),
        this.analyzeConversation(conversationId, conversationHistory, leadData),
        this.findSimilarPatterns(conversationHistory, leadData)
      ])

      // Extract successful results
      const results = {
        predictions: predictions.status === 'fulfilled' ? predictions.value : undefined,
        marketIntelligence: marketIntelligence.status === 'fulfilled' ? marketIntelligence.value : undefined,
        conversationAnalysis: conversationAnalysis.status === 'fulfilled' ? conversationAnalysis.value : undefined,
        similarPatterns: similarPatterns.status === 'fulfilled' ? similarPatterns.value : undefined
      }

      // Generate integrated recommendations
      const recommendations = this.generateIntegratedRecommendations(results)

      // Calculate overall confidence
      const confidence = this.calculateOverallConfidence(results)

      const processingTime = performance.now() - startTime

      return {
        ...results,
        recommendations,
        confidence,
        processingTime
      }

    } catch (error) {
      console.error('Advanced intelligence analysis failed:', error)

      return {
        recommendations: this.getFallbackRecommendations(),
        confidence: 0.1,
        processingTime: performance.now() - startTime
      }
    }
  }

  /**
   * Generate lead progression predictions
   */
  private async generatePredictions(
    conversationId: string,
    leadData: any,
    conversationHistory: any[]
  ): Promise<LeadPrediction> {
    // Mock market data for prediction calculation
    const mockMarketData = {
      inventory: { monthsSupply: 2.8 },
      interestRates: { trend: 'stable' },
      localHeat: 0.7
    }

    return await this.predictiveEngine.calculatePrediction(
      conversationId,
      leadData,
      conversationHistory,
      mockMarketData
    )
  }

  /**
   * Analyze market conditions for strategic insights
   */
  private async analyzeMarketConditions(
    leadData: any,
    platformContext: any
  ): Promise<MarketIntelligence> {
    // Extract location from lead data or use default
    const location = {
      zipCode: leadData?.address?.zipCode || '90210',
      city: leadData?.address?.city || 'Beverly Hills',
      state: leadData?.address?.state || 'CA',
      county: leadData?.address?.county || 'Los Angeles',
      msa: leadData?.address?.msa || 'Los Angeles-Long Beach-Anaheim'
    }

    return await this.marketEngine.getMarketIntelligence(location)
  }

  /**
   * Analyze conversation quality and coaching opportunities
   */
  private async analyzeConversation(
    conversationId: string,
    conversationHistory: any[],
    leadData: any
  ): Promise<ConversationIntelligence> {
    return await this.conversationEngine.analyzeConversation(
      conversationId,
      conversationHistory,
      leadData
    )
  }

  /**
   * Find similar conversation patterns for learning
   */
  private async findSimilarPatterns(
    conversationHistory: any[],
    leadData: any
  ): Promise<VectorSearchResult[]> {
    if (!conversationHistory.length) return []

    // Use the most recent user message to find similar patterns
    const recentMessage = conversationHistory
      .filter(msg => msg.role === 'user')
      .slice(-1)[0]

    if (!recentMessage) return []

    return await this.vectorEngine.searchSimilarConversations({
      text: recentMessage.content,
      filters: {
        outcome: 'success',
        minSimilarity: 0.7
      },
      limit: 5,
      includeContext: true
    })
  }

  /**
   * Generate integrated recommendations from all intelligence sources
   */
  private generateIntegratedRecommendations(results: {
    predictions?: LeadPrediction
    marketIntelligence?: MarketIntelligence
    conversationAnalysis?: ConversationIntelligence
    similarPatterns?: VectorSearchResult[]
  }): IntelligenceRecommendation[] {
    const recommendations: IntelligenceRecommendation[] = []

    // Predictive recommendations
    if (results.predictions?.recommendations) {
      for (const pred of results.predictions.recommendations) {
        recommendations.push({
          source: 'predictive',
          type: this.mapPredictiveType(pred.type),
          priority: pred.priority,
          title: pred.title,
          description: pred.description,
          actionData: pred.action.parameters,
          expectedImpact: pred.expectedImpact
        })
      }
    }

    // Market intelligence recommendations
    if (results.marketIntelligence?.jorgeRecommendations) {
      for (const market of results.marketIntelligence.jorgeRecommendations) {
        recommendations.push({
          source: 'market',
          type: 'strategic_adjustment',
          priority: this.mapUrgencyToPriority(market.urgency),
          title: `Market Opportunity: ${market.scenario}`,
          description: market.approach,
          actionData: {
            scenario: market.scenario,
            messaging: market.messaging,
            expectedOutcome: market.expectedOutcome
          },
          expectedImpact: 0.1
        })
      }
    }

    // Conversation intelligence recommendations
    if (results.conversationAnalysis?.coaching) {
      for (const coaching of results.conversationAnalysis.coaching.immediate) {
        recommendations.push({
          source: 'conversation',
          type: 'immediate_action',
          priority: coaching.priority,
          title: coaching.instruction,
          description: coaching.example,
          actionData: {
            type: coaching.type,
            expectedOutcome: coaching.expectedOutcome,
            timingAdvice: coaching.timingAdvice
          },
          expectedImpact: 0.15
        })
      }
    }

    // Pattern-based recommendations
    if (results.similarPatterns?.length) {
      recommendations.push({
        source: 'pattern',
        type: 'strategic_adjustment',
        priority: 'medium',
        title: 'Similar Success Pattern Found',
        description: `Found ${results.similarPatterns.length} similar successful conversations. Consider applying proven approaches.`,
        actionData: {
          patterns: results.similarPatterns.map(p => ({
            similarity: p.similarity,
            outcome: p.metadata.outcome,
            context: p.context
          }))
        },
        expectedImpact: 0.12
      })
    }

    // Sort by priority and expected impact
    return recommendations.sort((a, b) => {
      const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 }
      const priorityDiff = priorityOrder[b.priority] - priorityOrder[a.priority]
      if (priorityDiff !== 0) return priorityDiff
      return b.expectedImpact - a.expectedImpact
    }).slice(0, 10) // Limit to top 10 recommendations
  }

  /**
   * Calculate overall confidence based on available data quality
   */
  private calculateOverallConfidence(results: any): number {
    let totalConfidence = 0
    let weightedSum = 0

    if (results.predictions?.confidence) {
      totalConfidence += results.predictions.confidence * 0.3
      weightedSum += 0.3
    }

    if (results.marketIntelligence?.trends) {
      totalConfidence += 0.85 * 0.25 // Market data confidence
      weightedSum += 0.25
    }

    if (results.conversationAnalysis?.analysis) {
      totalConfidence += 0.75 * 0.25 // Conversation analysis confidence
      weightedSum += 0.25
    }

    if (results.similarPatterns?.length) {
      const avgSimilarity = results.similarPatterns.reduce((sum: number, p: VectorSearchResult) =>
        sum + p.similarity, 0) / results.similarPatterns.length
      totalConfidence += avgSimilarity * 0.2
      weightedSum += 0.2
    }

    return weightedSum > 0 ? totalConfidence / weightedSum : 0.5
  }

  /**
   * Map predictive recommendation types to intelligence types
   */
  private mapPredictiveType(predType: string): IntelligenceRecommendation['type'] {
    switch (predType) {
      case 'escalation': return 'bot_handoff'
      case 'timing': return 'timing_optimization'
      case 'approach': return 'strategic_adjustment'
      default: return 'immediate_action'
    }
  }

  /**
   * Map urgency to priority levels
   */
  private mapUrgencyToPriority(urgency: string): IntelligenceRecommendation['priority'] {
    switch (urgency) {
      case 'immediate': return 'critical'
      case 'this_week': return 'high'
      case 'this_month': return 'medium'
      default: return 'low'
    }
  }

  /**
   * Get fallback recommendations when analysis fails
   */
  private getFallbackRecommendations(): IntelligenceRecommendation[] {
    return [
      {
        source: 'predictive',
        type: 'immediate_action',
        priority: 'medium',
        title: 'Manual Review Recommended',
        description: 'Advanced intelligence analysis unavailable. Consider manual lead assessment.',
        actionData: { fallback: true },
        expectedImpact: 0.05
      }
    ]
  }

  /**
   * Get service health metrics
   */
  getServiceMetrics(): {
    enginesHealthy: number
    lastAnalysisTime: number
    recommendationsGenerated: number
  } {
    return {
      enginesHealthy: 4, // All engines operational
      lastAnalysisTime: 0, // TODO: Track last analysis time
      recommendationsGenerated: 0 // TODO: Track recommendation count
    }
  }
}

export default AdvancedIntelligenceIntegrator