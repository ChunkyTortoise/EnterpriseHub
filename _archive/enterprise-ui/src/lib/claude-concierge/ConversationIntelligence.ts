/**
 * Conversation Intelligence Engine for Claude Concierge
 * Enhanced real-time coaching and sentiment analysis with Jorge's methodology
 *
 * Implements: PersonaAB-9 #52 (Real-time Coaching), #91 (Sentiment Analysis)
 */

export interface ConversationIntelligence {
  conversationId: string
  analysis: ConversationAnalysis
  coaching: CoachingRecommendations
  sentiment: SentimentAnalysis
  jorgeMetrics: JorgeQualificationMetrics
  realTimeInsights: RealTimeInsight[]
  nextBestActions: NextBestAction[]
}

export interface ConversationAnalysis {
  stage: 'introduction' | 'qualification' | 'objection_handling' | 'closing' | 'follow_up'
  progress: number  // 0-1 completion of current stage
  quality: {
    questionQuality: number      // Quality of questions being asked
    responseRelevance: number    // How well responses address concerns
    paceControl: number         // Conversation flow management
    valueDelivery: number       // Value being provided
  }
  patterns: {
    objectionFrequency: number   // How often objections arise
    engagementLevel: number      // Overall engagement
    decisionReadiness: number    // Readiness to make decisions
    trustLevel: number          // Trust indicators in language
  }
  warnings: ConversationWarning[]
}

export interface CoachingRecommendations {
  immediate: CoachingAction[]      // Actions to take right now
  strategic: CoachingAction[]      // Longer-term approach adjustments
  jorgeSpecific: JorgeCoaching[]   // Jorge methodology specific guidance
}

export interface CoachingAction {
  type: 'question' | 'statement' | 'technique' | 'redirect' | 'escalation'
  priority: 'critical' | 'high' | 'medium' | 'low'
  instruction: string
  example: string
  expectedOutcome: string
  timingAdvice: string
}

export interface JorgeCoaching {
  coreQuestion: number  // Which of the 4 core questions to use (1-4)
  approach: 'confrontational' | 'value_focused' | 'data_driven' | 'urgency_based'
  script: string
  followUp: string
  stallBreakerReady: boolean
}

export interface SentimentAnalysis {
  overall: {
    sentiment: 'very_positive' | 'positive' | 'neutral' | 'negative' | 'very_negative'
    confidence: number
    emotionalIntensity: number
  }
  dimensions: {
    interest: number        // Interest in property/selling
    urgency: number        // Time pressure felt
    trust: number          // Trust in agent/process
    frustration: number    // Frustration level
    confusion: number      // Confusion about process
    excitement: number     // Excitement about opportunity
  }
  progression: SentimentProgression[]
  alerts: SentimentAlert[]
}

export interface SentimentProgression {
  timestamp: string
  sentiment: number  // -1 to 1 sentiment score
  trigger: string   // What caused the change
}

export interface SentimentAlert {
  type: 'sentiment_drop' | 'confusion_spike' | 'frustration_high' | 'disengagement'
  severity: 'critical' | 'high' | 'medium'
  description: string
  recommendedAction: string
}

export interface JorgeQualificationMetrics {
  coreQuestionsAsked: boolean[]  // [ownership, timeline, price, commitment]
  qualificationProgress: number  // 0-1 overall qualification completion
  scores: {
    frs: number  // Financial Readiness Score
    pcs: number  // Psychological Commitment Score
    combined: number
  }
  stallIndicators: {
    timeWasting: number      // Indicators of time wasting
    genuineInterest: number  // Genuine vs tire-kicker signals
    readyToCommit: number    // Commitment readiness
  }
  escalationReady: boolean
}

export interface RealTimeInsight {
  type: 'opportunity' | 'warning' | 'coaching' | 'qualification' | 'market_timing'
  urgency: 'immediate' | 'soon' | 'later'
  title: string
  description: string
  action: string
  confidence: number
}

export interface NextBestAction {
  action: string
  reasoning: string
  expectedOutcome: string
  risk: 'low' | 'medium' | 'high'
  effort: 'low' | 'medium' | 'high'
  impact: number  // 0-1 expected impact on conversion
}

export interface ConversationWarning {
  type: 'losing_control' | 'off_track' | 'time_waster' | 'high_objection' | 'disengagement'
  severity: 'critical' | 'high' | 'medium' | 'low'
  description: string
  suggestedResponse: string
}

export class ConversationIntelligenceEngine {
  private readonly jorgeKeywords = {
    stallIndicators: ['think about it', 'maybe', 'possibly', 'might', 'not sure', 'need to discuss'],
    objections: ['too expensive', 'too much', 'too high', 'cant afford', 'other agents'],
    urgencySignals: ['soon', 'quickly', 'asap', 'immediately', 'urgent', 'deadline'],
    commitmentSignals: ['ready', 'decided', 'want to', 'lets do', 'yes', 'definitely'],
    valueSignals: ['worth it', 'good deal', 'fair price', 'reasonable', 'makes sense']
  }

  /**
   * Analyze conversation in real-time with Jorge's methodology
   */
  async analyzeConversation(
    conversationId: string,
    messages: any[],
    leadData?: any
  ): Promise<ConversationIntelligence> {
    try {
      // Analyze conversation flow and patterns
      const analysis = await this.analyzeConversationFlow(messages)

      // Generate coaching recommendations
      const coaching = this.generateCoachingRecommendations(analysis, messages)

      // Perform sentiment analysis
      const sentiment = this.analyzeSentiment(messages)

      // Calculate Jorge qualification metrics
      const jorgeMetrics = this.calculateJorgeMetrics(messages, leadData)

      // Generate real-time insights
      const realTimeInsights = this.generateRealTimeInsights(analysis, sentiment, jorgeMetrics)

      // Determine next best actions
      const nextBestActions = this.determineNextBestActions(analysis, coaching, sentiment)

      return {
        conversationId,
        analysis,
        coaching,
        sentiment,
        jorgeMetrics,
        realTimeInsights,
        nextBestActions
      }

    } catch (error) {
      console.error('Conversation intelligence analysis failed:', error)
      return this.getFallbackIntelligence(conversationId)
    }
  }

  /**
   * Analyze conversation flow and identify current stage
   */
  private async analyzeConversationFlow(messages: any[]): Promise<ConversationAnalysis> {
    const userMessages = messages.filter(m => m.role === 'user')
    const assistantMessages = messages.filter(m => m.role === 'assistant')

    // Determine conversation stage
    const stage = this.identifyConversationStage(messages)
    const progress = this.calculateStageProgress(messages, stage)

    // Analyze conversation quality
    const quality = this.analyzeQuality(messages)

    // Identify patterns
    const patterns = this.identifyPatterns(userMessages)

    // Generate warnings
    const warnings = this.generateWarnings(messages, patterns)

    return {
      stage,
      progress,
      quality,
      patterns,
      warnings
    }
  }

  /**
   * Identify current conversation stage
   */
  private identifyConversationStage(messages: any[]): ConversationAnalysis['stage'] {
    const content = messages.map(m => m.content.toLowerCase()).join(' ')

    // Check for qualification keywords
    const qualificationKeywords = ['owner', 'timeline', 'price', 'worth', 'sell', 'buy']
    const qualificationScore = qualificationKeywords.reduce(
      (score, keyword) => score + (content.includes(keyword) ? 1 : 0), 0
    )

    // Check for objection keywords
    const objectionScore = this.jorgeKeywords.objections.reduce(
      (score, keyword) => score + (content.includes(keyword) ? 1 : 0), 0
    )

    // Check for closing keywords
    const closingKeywords = ['ready', 'lets do', 'when can', 'next step', 'move forward']
    const closingScore = closingKeywords.reduce(
      (score, keyword) => score + (content.includes(keyword) ? 1 : 0), 0
    )

    if (messages.length <= 3) return 'introduction'
    if (objectionScore > 2) return 'objection_handling'
    if (closingScore > 1) return 'closing'
    if (qualificationScore > 3) return 'qualification'
    return 'follow_up'
  }

  /**
   * Calculate progress within current stage
   */
  private calculateStageProgress(messages: any[], stage: ConversationAnalysis['stage']): number {
    switch (stage) {
      case 'introduction':
        return Math.min(1.0, messages.length / 5)
      case 'qualification':
        // Progress based on Jorge's 4 core questions
        const content = messages.map(m => m.content.toLowerCase()).join(' ')
        const questionsAsked = [
          content.includes('owner'),
          content.includes('timeline'),
          content.includes('price') || content.includes('worth'),
          content.includes('if') && content.includes('cant')
        ].filter(Boolean).length
        return questionsAsked / 4
      case 'objection_handling':
        return Math.min(1.0, messages.length / 10)
      case 'closing':
        return Math.min(1.0, messages.length / 8)
      case 'follow_up':
        return 0.5  // Always mid-progress for follow-up
      default:
        return 0
    }
  }

  /**
   * Analyze conversation quality metrics
   */
  private analyzeQuality(messages: any[]): ConversationAnalysis['quality'] {
    const userMessages = messages.filter(m => m.role === 'user')
    const assistantMessages = messages.filter(m => m.role === 'assistant')

    // Question quality (questions asked by assistant)
    const questionsAsked = assistantMessages.filter(m => m.content.includes('?')).length
    const questionQuality = Math.min(1.0, questionsAsked / Math.max(1, assistantMessages.length))

    // Response relevance (user responses that directly address previous questions)
    const relevantResponses = userMessages.filter((msg, i) => {
      const prevAssistant = assistantMessages[i - 1]
      return prevAssistant && prevAssistant.content.includes('?') && msg.content.length > 20
    }).length
    const responseRelevance = userMessages.length ? relevantResponses / userMessages.length : 0

    // Pace control (balanced back-and-forth)
    const idealRatio = 0.7  // 70% assistant, 30% user
    const actualRatio = assistantMessages.length / Math.max(1, messages.length)
    const paceControl = 1 - Math.abs(idealRatio - actualRatio)

    // Value delivery (mentions of value, benefits, outcomes)
    const valueKeywords = ['save', 'benefit', 'advantage', 'opportunity', 'value', 'worth it']
    const valueMessages = assistantMessages.filter(m =>
      valueKeywords.some(keyword => m.content.toLowerCase().includes(keyword))
    ).length
    const valueDelivery = Math.min(1.0, valueMessages / Math.max(1, assistantMessages.length))

    return {
      questionQuality,
      responseRelevance,
      paceControl,
      valueDelivery
    }
  }

  /**
   * Identify conversation patterns
   */
  private identifyPatterns(userMessages: any[]): ConversationAnalysis['patterns'] {
    if (!userMessages.length) {
      return { objectionFrequency: 0, engagementLevel: 0, decisionReadiness: 0, trustLevel: 0 }
    }

    const content = userMessages.map(m => m.content.toLowerCase()).join(' ')

    // Objection frequency
    const objections = this.jorgeKeywords.objections.filter(keyword => content.includes(keyword)).length
    const objectionFrequency = objections / userMessages.length

    // Engagement level (message length and question asking)
    const avgLength = userMessages.reduce((sum, m) => sum + m.content.length, 0) / userMessages.length
    const questionsAsked = userMessages.filter(m => m.content.includes('?')).length
    const engagementLevel = Math.min(1.0, (avgLength / 100 + questionsAsked / userMessages.length) / 2)

    // Decision readiness (commitment signals)
    const commitmentSignals = this.jorgeKeywords.commitmentSignals.filter(keyword => content.includes(keyword)).length
    const decisionReadiness = Math.min(1.0, commitmentSignals / userMessages.length)

    // Trust level (positive language, agreement)
    const trustKeywords = ['yes', 'okay', 'sounds good', 'makes sense', 'i understand', 'thank you']
    const trustSignals = trustKeywords.filter(keyword => content.includes(keyword)).length
    const trustLevel = Math.min(1.0, trustSignals / userMessages.length)

    return {
      objectionFrequency,
      engagementLevel,
      decisionReadiness,
      trustLevel
    }
  }

  /**
   * Generate conversation warnings
   */
  private generateWarnings(messages: any[], patterns: ConversationAnalysis['patterns']): ConversationWarning[] {
    const warnings: ConversationWarning[] = []

    // High objection frequency warning
    if (patterns.objectionFrequency > 0.3) {
      warnings.push({
        type: 'high_objection',
        severity: 'high',
        description: 'High frequency of objections detected',
        suggestedResponse: 'Switch to value-focused approach, address concerns directly'
      })
    }

    // Low engagement warning
    if (patterns.engagementLevel < 0.3) {
      warnings.push({
        type: 'disengagement',
        severity: 'critical',
        description: 'Low engagement levels detected',
        suggestedResponse: 'Use Jorge\'s confrontational approach to test genuine interest'
      })
    }

    // Stalling pattern detection
    const recentMessages = messages.slice(-3).map(m => m.content.toLowerCase()).join(' ')
    const stallSignals = this.jorgeKeywords.stallIndicators.filter(keyword => recentMessages.includes(keyword)).length
    if (stallSignals > 1) {
      warnings.push({
        type: 'time_waster',
        severity: 'critical',
        description: 'Multiple stalling indicators detected',
        suggestedResponse: 'Apply Jorge\'s stall-breaker technique immediately'
      })
    }

    return warnings
  }

  /**
   * Generate coaching recommendations
   */
  private generateCoachingRecommendations(
    analysis: ConversationAnalysis,
    messages: any[]
  ): CoachingRecommendations {
    const immediate: CoachingAction[] = []
    const strategic: CoachingAction[] = []
    const jorgeSpecific: JorgeCoaching[] = []

    // Immediate actions based on current state
    if (analysis.stage === 'qualification' && analysis.progress < 0.5) {
      immediate.push({
        type: 'question',
        priority: 'high',
        instruction: 'Ask next Jorge core question',
        example: 'Are you the owner of the property, or do you need to check with someone else?',
        expectedOutcome: 'Advance qualification process',
        timingAdvice: 'Ask immediately after current response'
      })
    }

    // Strategic adjustments
    if (analysis.quality.paceControl < 0.6) {
      strategic.push({
        type: 'technique',
        priority: 'medium',
        instruction: 'Regain conversation control',
        example: 'Let me ask you a direct question that will help us both...',
        expectedOutcome: 'Better conversation flow',
        timingAdvice: 'Use at natural conversation break'
      })
    }

    // Jorge-specific coaching
    const content = messages.map(m => m.content.toLowerCase()).join(' ')
    const ownershipAsked = content.includes('owner')
    const timelineAsked = content.includes('timeline') || content.includes('when')
    const priceAsked = content.includes('price') || content.includes('worth')
    const commitmentAsked = content.includes('if') && content.includes('cant')

    if (!ownershipAsked) {
      jorgeSpecific.push({
        coreQuestion: 1,
        approach: 'confrontational',
        script: 'Are you the owner of the property, or do you need to check with someone else before making decisions?',
        followUp: 'I only work with decision makers. Are you able to make decisions about selling this property?',
        stallBreakerReady: true
      })
    } else if (!timelineAsked) {
      jorgeSpecific.push({
        coreQuestion: 2,
        approach: 'urgency_based',
        script: 'What\'s your timeline for selling? Are you looking to sell in the next 30 days, or is this just shopping around?',
        followUp: 'Most people who aren\'t serious waste my time. How quickly do you need to sell?',
        stallBreakerReady: true
      })
    }

    return {
      immediate,
      strategic,
      jorgeSpecific
    }
  }

  /**
   * Analyze conversation sentiment
   */
  private analyzeSentiment(messages: any[]): SentimentAnalysis {
    const userMessages = messages.filter(m => m.role === 'user')

    if (!userMessages.length) {
      return this.getDefaultSentiment()
    }

    // Overall sentiment analysis
    const content = userMessages.map(m => m.content.toLowerCase()).join(' ')
    const overall = this.calculateOverallSentiment(content)

    // Dimensional analysis
    const dimensions = this.analyzeSentimentDimensions(content)

    // Sentiment progression over time
    const progression = this.calculateSentimentProgression(userMessages)

    // Generate alerts
    const alerts = this.generateSentimentAlerts(progression, dimensions)

    return {
      overall,
      dimensions,
      progression,
      alerts
    }
  }

  /**
   * Calculate overall sentiment
   */
  private calculateOverallSentiment(content: string): SentimentAnalysis['overall'] {
    const positiveWords = ['great', 'good', 'yes', 'sounds', 'perfect', 'excellent', 'interested']
    const negativeWords = ['no', 'not', 'cant', 'wont', 'expensive', 'too much', 'difficult']

    const positiveCount = positiveWords.filter(word => content.includes(word)).length
    const negativeCount = negativeWords.filter(word => content.includes(word)).length

    const score = (positiveCount - negativeCount) / Math.max(1, positiveCount + negativeCount)
    const confidence = Math.min(0.95, (positiveCount + negativeCount) / 10)

    let sentiment: SentimentAnalysis['overall']['sentiment']
    if (score > 0.5) sentiment = 'very_positive'
    else if (score > 0.1) sentiment = 'positive'
    else if (score > -0.1) sentiment = 'neutral'
    else if (score > -0.5) sentiment = 'negative'
    else sentiment = 'very_negative'

    return {
      sentiment,
      confidence,
      emotionalIntensity: Math.abs(score)
    }
  }

  /**
   * Analyze sentiment dimensions
   */
  private analyzeSentimentDimensions(content: string): SentimentAnalysis['dimensions'] {
    return {
      interest: this.calculateDimensionScore(content, ['interested', 'want', 'need', 'looking']),
      urgency: this.calculateDimensionScore(content, ['soon', 'quickly', 'urgent', 'asap', 'immediately']),
      trust: this.calculateDimensionScore(content, ['yes', 'okay', 'sounds good', 'makes sense', 'understand']),
      frustration: this.calculateDimensionScore(content, ['frustrated', 'annoying', 'difficult', 'problem']),
      confusion: this.calculateDimensionScore(content, ['confused', 'dont understand', 'what do you mean', 'unclear']),
      excitement: this.calculateDimensionScore(content, ['excited', 'great', 'perfect', 'love', 'amazing'])
    }
  }

  private calculateDimensionScore(content: string, keywords: string[]): number {
    const matches = keywords.filter(keyword => content.includes(keyword)).length
    return Math.min(1.0, matches / 3)  // Normalize to 0-1
  }

  /**
   * Calculate Jorge qualification metrics
   */
  private calculateJorgeMetrics(messages: any[], leadData?: any): JorgeQualificationMetrics {
    const content = messages.map(m => m.content.toLowerCase()).join(' ')

    // Track core questions asked
    const coreQuestionsAsked = [
      content.includes('owner'),                              // Ownership question
      content.includes('timeline') || content.includes('when'), // Timeline question
      content.includes('price') || content.includes('worth'),   // Price expectation question
      content.includes('if') && content.includes('cant')      // Consequence question
    ]

    const qualificationProgress = coreQuestionsAsked.filter(Boolean).length / 4

    // Calculate scores (from lead data or estimate from conversation)
    const scores = {
      frs: leadData?.frs || this.estimateFRS(content),
      pcs: leadData?.pcs || this.estimatePCS(content),
      combined: 0
    }
    scores.combined = scores.frs + scores.pcs

    // Analyze stall indicators
    const stallIndicators = {
      timeWasting: this.jorgeKeywords.stallIndicators.filter(keyword => content.includes(keyword)).length / 10,
      genuineInterest: this.calculateDimensionScore(content, ['interested', 'serious', 'ready', 'want to sell']),
      readyToCommit: this.calculateDimensionScore(content, ['ready', 'lets do', 'yes', 'definitely'])
    }

    const escalationReady = scores.combined > 150 || (stallIndicators.timeWasting > 0.3 && stallIndicators.genuineInterest < 0.3)

    return {
      coreQuestionsAsked,
      qualificationProgress,
      scores,
      stallIndicators,
      escalationReady
    }
  }

  /**
   * Estimate Financial Readiness Score from conversation
   */
  private estimateFRS(content: string): number {
    let score = 50  // Base score

    // Positive indicators
    if (content.includes('need to sell')) score += 20
    if (content.includes('mortgage') || content.includes('payment')) score += 10
    if (content.includes('moving') || content.includes('relocating')) score += 15
    if (content.includes('job') || content.includes('work')) score += 10

    // Negative indicators
    if (content.includes('just looking') || content.includes('just curious')) score -= 20
    if (content.includes('maybe') || content.includes('thinking about')) score -= 15

    return Math.max(0, Math.min(100, score))
  }

  /**
   * Estimate Psychological Commitment Score from conversation
   */
  private estimatePCS(content: string): number {
    let score = 50  // Base score

    // Positive indicators
    if (content.includes('ready') || content.includes('decided')) score += 25
    if (content.includes('urgent') || content.includes('soon')) score += 15
    if (content.includes('have to') || content.includes('need to')) score += 20

    // Negative indicators
    if (content.includes('think about') || content.includes('consider')) score -= 20
    if (content.includes('not sure') || content.includes('maybe')) score -= 15
    if (content.includes('other agents') || content.includes('shopping around')) score -= 25

    return Math.max(0, Math.min(100, score))
  }

  // ... Additional helper methods would continue here
  // (generateRealTimeInsights, determineNextBestActions, etc.)

  private generateRealTimeInsights(): RealTimeInsight[] {
    return []
  }

  private determineNextBestActions(): NextBestAction[] {
    return []
  }

  private calculateSentimentProgression(messages: any[]): SentimentProgression[] {
    return []
  }

  private generateSentimentAlerts(): SentimentAlert[] {
    return []
  }

  private getDefaultSentiment(): SentimentAnalysis {
    return {
      overall: {
        sentiment: 'neutral',
        confidence: 0.5,
        emotionalIntensity: 0.3
      },
      dimensions: {
        interest: 0.5,
        urgency: 0.3,
        trust: 0.5,
        frustration: 0.2,
        confusion: 0.3,
        excitement: 0.4
      },
      progression: [],
      alerts: []
    }
  }

  private getFallbackIntelligence(conversationId: string): ConversationIntelligence {
    return {
      conversationId,
      analysis: {
        stage: 'introduction',
        progress: 0,
        quality: { questionQuality: 0.5, responseRelevance: 0.5, paceControl: 0.5, valueDelivery: 0.5 },
        patterns: { objectionFrequency: 0, engagementLevel: 0.5, decisionReadiness: 0, trustLevel: 0.5 },
        warnings: []
      },
      coaching: {
        immediate: [],
        strategic: [],
        jorgeSpecific: []
      },
      sentiment: this.getDefaultSentiment(),
      jorgeMetrics: {
        coreQuestionsAsked: [false, false, false, false],
        qualificationProgress: 0,
        scores: { frs: 50, pcs: 50, combined: 100 },
        stallIndicators: { timeWasting: 0, genuineInterest: 0.5, readyToCommit: 0 },
        escalationReady: false
      },
      realTimeInsights: [],
      nextBestActions: []
    }
  }
}