/**
 * Predictive Scoring Engine for Claude Concierge
 * ML-powered lead progression prediction with Jorge's methodology
 *
 * Implements: PersonaAB-9 #83 (Predictive Analytics), #45 (Behavioral Modeling)
 */

export interface LeadPrediction {
  leadId: string
  currentScore: number
  predictions: {
    close30Day: number    // Probability of closing in 30 days
    close60Day: number    // Probability of closing in 60 days
    close90Day: number    // Probability of closing in 90 days
  }
  factors: PredictiveFactors
  recommendations: PredictiveRecommendation[]
  confidence: number
  lastUpdated: string
}

export interface PredictiveFactors {
  behavioralSignals: {
    responseTime: number        // Average response time (lower = better)
    engagementRate: number      // Message engagement rate
    questionAsking: number      // Quality questions asked
    objectionPattern: number    // Objection handling success
  }
  qualificationData: {
    frs: number                // Financial Readiness Score
    pcs: number                // Psychological Commitment Score
    timelineUrgency: number    // Timeline pressure factor
    priceRealism: number       // Price expectation accuracy
  }
  marketFactors: {
    seasonality: number        // Market season impact
    inventoryLevel: number     // Current inventory pressure
    interestRateTrend: number  // Rate environment factor
    localMarketHeat: number    // Micro-market dynamics
  }
  historicalPerformance: {
    similarLeadsConversion: number  // Similar lead conversion rate
    agentSuccessRate: number       // Agent track record
    propertyTypeSuccess: number    // Property type conversion
    priceRangeSuccess: number      // Price range success rate
  }
}

export interface PredictiveRecommendation {
  type: 'timing' | 'approach' | 'escalation' | 'resource_allocation'
  priority: 'critical' | 'high' | 'medium' | 'low'
  title: string
  description: string
  action: {
    type: string
    parameters: Record<string, any>
  }
  expectedImpact: number  // Expected increase in close probability
}

export class PredictiveScoring {
  private modelWeights = {
    behavioral: 0.35,     // Behavioral signals weight
    qualification: 0.30,   // Jorge qualification data weight
    market: 0.20,         // Market condition weight
    historical: 0.15      // Historical performance weight
  }

  private thresholds = {
    highProbability: 0.75,    // High close probability
    mediumProbability: 0.45,  // Medium close probability
    lowProbability: 0.25,     // Low close probability
    criticalUrgency: 0.85     // Needs immediate attention
  }

  /**
   * Calculate lead progression prediction using Jorge's methodology
   */
  async calculatePrediction(
    leadId: string,
    leadData: any,
    conversationHistory: any[],
    marketData: any
  ): Promise<LeadPrediction> {
    try {
      // Extract behavioral signals from conversation
      const behavioralFactors = this.extractBehavioralSignals(conversationHistory)

      // Get qualification data from Jorge's system
      const qualificationFactors = this.extractQualificationFactors(leadData)

      // Incorporate market factors
      const marketFactors = this.extractMarketFactors(marketData)

      // Get historical performance data
      const historicalFactors = await this.getHistoricalFactors(leadData)

      // Calculate composite factors
      const factors: PredictiveFactors = {
        behavioralSignals: behavioralFactors,
        qualificationData: qualificationFactors,
        marketFactors: marketFactors,
        historicalPerformance: historicalFactors
      }

      // Calculate weighted prediction scores
      const predictions = this.calculateProgressionProbability(factors)

      // Generate recommendations
      const recommendations = this.generateRecommendations(factors, predictions)

      // Calculate overall confidence
      const confidence = this.calculateConfidence(factors)

      return {
        leadId,
        currentScore: this.calculateCurrentScore(factors),
        predictions,
        factors,
        recommendations,
        confidence,
        lastUpdated: new Date().toISOString()
      }

    } catch (error) {
      console.error('Prediction calculation failed:', error)
      return this.getFallbackPrediction(leadId)
    }
  }

  /**
   * Extract behavioral signals from conversation history
   */
  private extractBehavioralSignals(history: any[]): PredictiveFactors['behavioralSignals'] {
    if (!history.length) {
      return { responseTime: 0, engagementRate: 0, questionAsking: 0, objectionPattern: 0 }
    }

    // Calculate average response time
    const responseTimes = history
      .filter((msg, i) => i > 0 && msg.role === 'user')
      .map((msg, i) => {
        const prevMsg = history.find((h, idx) => idx < history.indexOf(msg) && h.role === 'assistant')
        if (prevMsg) {
          return new Date(msg.timestamp).getTime() - new Date(prevMsg.timestamp).getTime()
        }
        return 0
      })
      .filter(time => time > 0)

    const avgResponseTime = responseTimes.length ?
      responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length : 0

    // Response time score (faster = better, normalize to 0-1)
    const responseTimeScore = Math.max(0, Math.min(1, 1 - (avgResponseTime / (24 * 60 * 60 * 1000))))

    // Engagement rate (messages with questions, multiple sentences, etc.)
    const userMessages = history.filter(msg => msg.role === 'user')
    const engagedMessages = userMessages.filter(msg =>
      msg.content.includes('?') || msg.content.split('.').length > 2 || msg.content.length > 100
    )
    const engagementRate = userMessages.length ? engagedMessages.length / userMessages.length : 0

    // Question asking behavior (shows interest)
    const questionMessages = userMessages.filter(msg => msg.content.includes('?'))
    const questionAsking = userMessages.length ? questionMessages.length / userMessages.length : 0

    // Objection pattern (fewer objections = better)
    const objectionKeywords = ['but', 'however', 'expensive', 'too much', 'think about', 'maybe', 'not sure']
    const objectionMessages = userMessages.filter(msg =>
      objectionKeywords.some(keyword => msg.content.toLowerCase().includes(keyword))
    )
    const objectionPattern = Math.max(0, 1 - (objectionMessages.length / Math.max(1, userMessages.length)))

    return {
      responseTime: responseTimeScore,
      engagementRate,
      questionAsking,
      objectionPattern
    }
  }

  /**
   * Extract Jorge qualification factors (FRS/PCS scores)
   */
  private extractQualificationFactors(leadData: any): PredictiveFactors['qualificationData'] {
    return {
      frs: leadData.frs || 0,                          // Financial Readiness Score
      pcs: leadData.pcs || 0,                          // Psychological Commitment Score
      timelineUrgency: leadData.timelineUrgency || 0,  // Timeline pressure
      priceRealism: leadData.priceRealism || 0         // Price expectation accuracy
    }
  }

  /**
   * Extract market factors
   */
  private extractMarketFactors(marketData: any): PredictiveFactors['marketFactors'] {
    const month = new Date().getMonth()
    const seasonality = this.getSeasonalityFactor(month)

    return {
      seasonality,
      inventoryLevel: marketData.inventory?.monthsSupply ?
        Math.max(0, 1 - (marketData.inventory.monthsSupply / 6)) : 0.5,
      interestRateTrend: marketData.interestRates?.trend === 'declining' ? 0.8 :
                        marketData.interestRates?.trend === 'stable' ? 0.6 : 0.4,
      localMarketHeat: marketData.localHeat || 0.5
    }
  }

  /**
   * Get historical performance factors
   */
  private async getHistoricalFactors(leadData: any): Promise<PredictiveFactors['historicalPerformance']> {
    // In production, this would query actual historical data
    return {
      similarLeadsConversion: 0.65,  // 65% conversion for similar leads
      agentSuccessRate: 0.72,        // Agent's historical success rate
      propertyTypeSuccess: 0.68,     // Property type conversion rate
      priceRangeSuccess: 0.71        // Price range success rate
    }
  }

  /**
   * Calculate progression probabilities
   */
  private calculateProgressionProbability(factors: PredictiveFactors) {
    // Weighted composite score
    const composite =
      (factors.behavioralSignals.responseTime * 0.15 +
       factors.behavioralSignals.engagementRate * 0.15 +
       factors.behavioralSignals.questionAsking * 0.05 +
       factors.behavioralSignals.objectionPattern * 0.05) * this.modelWeights.behavioral +

      (factors.qualificationData.frs / 100 * 0.15 +
       factors.qualificationData.pcs / 100 * 0.10 +
       factors.qualificationData.timelineUrgency * 0.03 +
       factors.qualificationData.priceRealism * 0.02) * this.modelWeights.qualification +

      (factors.marketFactors.seasonality * 0.08 +
       factors.marketFactors.inventoryLevel * 0.06 +
       factors.marketFactors.interestRateTrend * 0.04 +
       factors.marketFactors.localMarketHeat * 0.02) * this.modelWeights.market +

      (factors.historicalPerformance.similarLeadsConversion * 0.06 +
       factors.historicalPerformance.agentSuccessRate * 0.05 +
       factors.historicalPerformance.propertyTypeSuccess * 0.02 +
       factors.historicalPerformance.priceRangeSuccess * 0.02) * this.modelWeights.historical

    // Apply time decay for different periods
    return {
      close30Day: composite * 0.8,          // 80% of base probability
      close60Day: composite * 1.0,          // Full probability
      close90Day: Math.min(1.0, composite * 1.15)  // 115% with ceiling
    }
  }

  /**
   * Generate actionable recommendations
   */
  private generateRecommendations(
    factors: PredictiveFactors,
    predictions: LeadPrediction['predictions']
  ): PredictiveRecommendation[] {
    const recommendations: PredictiveRecommendation[] = []

    // High probability leads need immediate action
    if (predictions.close30Day > this.thresholds.criticalUrgency) {
      recommendations.push({
        type: 'escalation',
        priority: 'critical',
        title: 'Hot Lead - Immediate Human Contact Required',
        description: `${(predictions.close30Day * 100).toFixed(0)}% probability of closing in 30 days. Escalate to human agent immediately.`,
        action: {
          type: 'escalate_to_human',
          parameters: { urgency: 'critical', reason: 'high_close_probability' }
        },
        expectedImpact: 0.15
      })
    }

    // Poor behavioral signals need nurturing
    if (factors.behavioralSignals.responseTime < 0.3 || factors.behavioralSignals.engagementRate < 0.4) {
      recommendations.push({
        type: 'approach',
        priority: 'high',
        title: 'Improve Engagement Strategy',
        description: 'Low engagement signals. Switch to more personalized, value-focused messaging.',
        action: {
          type: 'adjust_bot_strategy',
          parameters: { approach: 'high_value_nurture', frequency: 'daily' }
        },
        expectedImpact: 0.12
      })
    }

    // Market timing opportunities
    if (factors.marketFactors.inventoryLevel > 0.7 && factors.qualificationData.frs > 60) {
      recommendations.push({
        type: 'timing',
        priority: 'medium',
        title: 'Market Timing Advantage',
        description: 'Low inventory market favors sellers. Emphasize competitive advantage.',
        action: {
          type: 'market_timing_message',
          parameters: { focus: 'seller_advantage', urgency: 'medium' }
        },
        expectedImpact: 0.08
      })
    }

    return recommendations.sort((a, b) => {
      const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 }
      return priorityOrder[b.priority] - priorityOrder[a.priority]
    })
  }

  /**
   * Calculate prediction confidence
   */
  private calculateConfidence(factors: PredictiveFactors): number {
    // Confidence based on data completeness and quality
    const dataCompleteness =
      (factors.behavioralSignals.responseTime > 0 ? 0.25 : 0) +
      (factors.qualificationData.frs > 0 ? 0.25 : 0) +
      (factors.qualificationData.pcs > 0 ? 0.25 : 0) +
      (factors.marketFactors.inventoryLevel > 0 ? 0.25 : 0)

    return Math.min(0.95, dataCompleteness * 0.9)  // Max 95% confidence
  }

  /**
   * Calculate current overall score
   */
  private calculateCurrentScore(factors: PredictiveFactors): number {
    return Math.round(
      (factors.qualificationData.frs + factors.qualificationData.pcs) * 0.5 +
      factors.behavioralSignals.engagementRate * 20 +
      factors.marketFactors.inventoryLevel * 10
    )
  }

  /**
   * Get seasonality factor based on month
   */
  private getSeasonalityFactor(month: number): number {
    // Real estate seasonality: Spring/Summer higher, Winter lower
    const seasonalityMap = {
      0: 0.3,   // January
      1: 0.4,   // February
      2: 0.6,   // March
      3: 0.8,   // April
      4: 0.9,   // May
      5: 1.0,   // June
      6: 0.95,  // July
      7: 0.85,  // August
      8: 0.8,   // September
      9: 0.7,   // October
      10: 0.5,  // November
      11: 0.35  // December
    }
    return seasonalityMap[month as keyof typeof seasonalityMap] || 0.5
  }

  /**
   * Fallback prediction when calculation fails
   */
  private getFallbackPrediction(leadId: string): LeadPrediction {
    return {
      leadId,
      currentScore: 50,
      predictions: {
        close30Day: 0.3,
        close60Day: 0.45,
        close90Day: 0.6
      },
      factors: {
        behavioralSignals: { responseTime: 0.5, engagementRate: 0.5, questionAsking: 0.5, objectionPattern: 0.5 },
        qualificationData: { frs: 50, pcs: 50, timelineUrgency: 0.5, priceRealism: 0.5 },
        marketFactors: { seasonality: 0.5, inventoryLevel: 0.5, interestRateTrend: 0.5, localMarketHeat: 0.5 },
        historicalPerformance: { similarLeadsConversion: 0.5, agentSuccessRate: 0.5, propertyTypeSuccess: 0.5, priceRangeSuccess: 0.5 }
      },
      recommendations: [{
        type: 'escalation',
        priority: 'medium',
        title: 'Manual Review Required',
        description: 'Prediction calculation failed. Manual assessment recommended.',
        action: { type: 'manual_review', parameters: {} },
        expectedImpact: 0
      }],
      confidence: 0.1,
      lastUpdated: new Date().toISOString()
    }
  }
}