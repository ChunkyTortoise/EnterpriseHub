/**
 * Core orchestration service for Claude Concierge
 * Implements: PersonaAB-9 #21 (Memory Hierarchy), #26 (Meta-Prompting)
 *
 * Responsibilities:
 * - Claude API communication with streaming support
 * - Dynamic prompt assembly based on context
 * - Intelligent bot routing decisions
 * - Memory persistence coordination
 */

import { ContextManager, type PlatformContext } from './ContextManager'
import { MemoryManager, type EpisodicInteraction } from './MemoryManager'
import { PersonaPromptEngine, type MemoryHierarchy, type Message, type PlatformState } from './PersonaPromptEngine'
import { AdvancedIntelligenceIntegrator, type AdvancedIntelligenceResult, type IntelligenceRecommendation } from './AdvancedIntelligenceIntegrator'
import { BotCoordinationEngine, type BotSession, type CoordinationMetrics, type HandoffResult, type CoachingResult } from './BotCoordinationEngine'

export interface ConciergeRequest {
  userMessage: string
  conversationId: string
  platformContext?: PlatformContext
}

export interface ConciergeResponse {
  content: string
  reasoning?: string
  suggestedActions?: SuggestedAction[]
  botHandoff?: BotHandoffRecommendation
  memoryUpdates?: MemoryUpdate[]
  advancedIntelligence?: AdvancedIntelligenceResult
  leadIntelligence?: {
    frs_score?: number
    pcs_score?: number
    lead_score?: number
  }
}

export interface SuggestedAction {
  type: 'navigation' | 'bot_start' | 'data_update' | 'external_link'
  label: string
  description: string
  data: Record<string, any>
  priority?: 'high' | 'medium' | 'low'
}

export interface BotHandoffRecommendation {
  targetBot: 'jorge-seller-bot' | 'lead-bot' | 'intent-decoder'
  confidence: number
  reasoning: string
  contextToTransfer: Record<string, any>
}

export interface MemoryUpdate {
  type: 'conversation' | 'episodic' | 'semantic'
  data: any
}

export interface ProactiveSuggestion {
  id: string
  type: 'workflow' | 'feature' | 'best_practice' | 'opportunity'
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  action: SuggestedAction
  expiresAt?: string
}

export interface StreamChunk {
  type: 'content' | 'reasoning' | 'action' | 'handoff' | 'complete'
  content?: string
  data?: any
}

export class ClaudeConciergeService {
  private contextManager: ContextManager
  private memoryManager: MemoryManager
  private promptEngine: PersonaPromptEngine
  private intelligenceIntegrator: AdvancedIntelligenceIntegrator
  private coordinationEngine: BotCoordinationEngine
  private baseApiUrl: string

  // Configuration
  private readonly MAX_TOKENS = 4096
  private readonly TEMPERATURE = 0.7
  private readonly MODEL_MAIN = 'claude-3-5-sonnet-20241022'
  private readonly MODEL_ROUTING = 'claude-3-5-haiku-20241022'

  constructor(baseApiUrl: string = '/api') {
    this.baseApiUrl = baseApiUrl
    this.contextManager = new ContextManager()
    this.memoryManager = new MemoryManager()
    this.promptEngine = new PersonaPromptEngine()
    this.intelligenceIntegrator = new AdvancedIntelligenceIntegrator()
    this.coordinationEngine = new BotCoordinationEngine()

    this.setupContextTracking()
    this.initializeOmnipresentCapabilities()
  }

  /**
   * Main conversation handler with streaming support and bulletproof error handling
   * Pattern: Similar to useChatStore.sendMessage but with memory integration
   */
  async *chat(request: ConciergeRequest): AsyncGenerator<string, ConciergeResponse> {
    const correlationId = `chat_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    try {
      // Import error service for robust error handling
      const { errorService, apiWithRetry } = await import('@/lib/errors/ErrorService')

      // 1. Track user interaction with correlation ID
      this.contextManager.trackUIInteraction('concierge', 'message_sent', {
        conversationId: request.conversationId,
        messageLength: request.userMessage.length,
        correlationId
      })

      // 2. Load memory context with retry on failure
      const memoryContext = await apiWithRetry(
        () => this.memoryManager.getRelevantMemory(
          request.conversationId,
          request.userMessage
        ),
        'memory_retrieval',
        { correlationId, maxRetries: 2 }
      )

      // 3. Assemble current platform context with retry
      const platformContext = await apiWithRetry(
        () => this.contextManager.captureContext(request.platformContext),
        'context_capture',
        { correlationId, maxRetries: 2 }
      )

      // 4. Generate optimized prompt (PersonaAB-9 #26: Meta-Prompting)
      const systemPrompt = this.promptEngine.buildConciergePrompt({
        memoryContext,
        platformContext,
        conversationHistory: memoryContext.workingMemory.messages,
      })

      // 5. Stream response from Claude via backend proxy with retry
      const streamResponse = await errorService.withRetry(
        () => this.streamFromClaude({
          systemPrompt,
          userMessage: request.userMessage,
          conversationHistory: memoryContext.workingMemory.messages
        }),
        'claude_api_stream',
        {
          maxRetries: 3,
          initialDelayMs: 2000,
          retryIf: (error) => error.shouldRetry && error.code !== 'AUTH_ERROR'
        },
        { correlationId }
      )

      // 6. Process stream and update memory with error handling
      const finalResponse = yield* this.processStreamWithMemory(
        streamResponse,
        request.conversationId,
        request.userMessage,
        correlationId
      )

      return finalResponse
    } catch (error) {
      // CRITICAL: Never silently fail - always provide user feedback
      const { errorService } = await import('@/lib/errors/ErrorService')
      const errorInfo = await errorService.handleError(
        error,
        'ClaudeConciergeService.chat',
        { correlationId, reportToService: true }
      )

      console.error('🚨 CONCIERGE CHAT FAILURE [NEVER SILENT]:', {
        errorId: errorInfo.id,
        correlationId,
        context: 'chat',
        userMessage: request.userMessage.substring(0, 100) + '...',
        timestamp: new Date().toISOString()
      })

      // Create detailed fallback response with actionable guidance
      const fallbackResponse = this.createFallbackResponse(errorInfo, correlationId)

      // Always yield something to the user - never silent failure
      yield fallbackResponse.content
      return fallbackResponse
    }
  }

  /**
   * Analyze platform state and provide proactive suggestions
   * PersonaAB-9 #40: Contextual Selective Recall
   * BULLETPROOF: Always returns suggestions, never empty due to errors
   */
  async analyzeContext(context?: PlatformContext): Promise<ProactiveSuggestion[]> {
    const correlationId = `context_analysis_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    try {
      const { errorService, apiWithRetry } = await import('@/lib/errors/ErrorService')

      // Capture current platform state with retry
      const platformState = await apiWithRetry(
        () => this.contextManager.captureContext(context),
        'platform_context_capture',
        { correlationId, maxRetries: 2 }
      )

      // Get activity patterns for analysis with fallback
      let activityPatterns
      try {
        activityPatterns = this.contextManager.getActivityPatterns()
      } catch (patternError) {
        console.warn('Activity patterns unavailable, using fallback:', patternError)
        activityPatterns = { sessionFocus: 'general', actionsPerformed: 0 }
      }

      // Generate context analysis prompt
      const analysisPrompt = this.promptEngine.buildContextAnalysisPrompt(platformState)

      // Use fast model for quick analysis with robust retry
      const result = await errorService.withRetry(
        () => this.queryClaude({
          systemPrompt: analysisPrompt,
          userMessage: JSON.stringify(activityPatterns),
          model: this.MODEL_ROUTING,
          maxTokens: 1024
        }),
        'context_analysis_claude',
        {
          maxRetries: 2,
          initialDelayMs: 1000,
          retryIf: (error) => error.shouldRetry
        },
        { correlationId }
      )

      // Parse suggestions from response with validation
      // Support both raw JSON response and structured model
      const content = typeof result === 'string' ? result : (result.content || result.primary_guidance)
      const suggestions = this.parseSuggestionsFromResponse(content)

      // Validate suggestions quality
      const validSuggestions = suggestions.filter(s =>
        s.title && s.description && s.action && s.type
      )

      // Track analysis event with detailed metrics
      this.contextManager.trackUIInteraction('concierge', 'context_analyzed', {
        suggestionsGenerated: validSuggestions.length,
        patterns: activityPatterns.sessionFocus,
        correlationId,
        analysisSuccess: true
      })

      return validSuggestions.length > 0 ? validSuggestions : this.getFallbackSuggestions(context)
    } catch (error) {
      // 🚨 NEVER return empty array silently - always provide fallback suggestions
      const { errorService } = await import('@/lib/errors/ErrorService')
      const errorInfo = await errorService.handleError(
        error,
        'ClaudeConciergeService.analyzeContext',
        {
          correlationId,
          reportToService: true,
          logToConsole: true
        }
      )

      console.error('🚨 CONTEXT ANALYSIS FAILURE [FALLBACK ENGAGED]:', {
        errorId: errorInfo.id,
        correlationId,
        severity: errorInfo.severity,
        retryable: errorInfo.shouldRetry,
        userMessage: errorInfo.userMessage
      })

      // Track the failure and fallback engagement
      this.contextManager.trackUIInteraction('concierge', 'context_analysis_fallback', {
        errorId: errorInfo.id,
        correlationId,
        fallbackEngaged: true
      })

      // Always provide meaningful fallback suggestions
      return this.getFallbackSuggestions(context, errorInfo)
    }
  }

  /**
   * Advanced intelligence analysis with all AI modules
   * PersonaAB-9 #83 (Predictive Analytics), #67 (Market Integration)
   * BULLETPROOF: Always returns meaningful results, never empty due to errors
   */
  async analyzeWithAdvancedIntelligence(
    conversationId: string,
    leadData: any,
    conversationHistory: any[],
    platformContext?: PlatformContext
  ): Promise<AdvancedIntelligenceResult> {
    const correlationId = `advanced_intel_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const startTime = Date.now()

    try {
      const { errorService, apiWithRetry } = await import('@/lib/errors/ErrorService')

      // Capture current platform context if not provided, with retry
      const context = platformContext || await apiWithRetry(
        () => this.contextManager.captureContext(),
        'platform_context_advanced',
        { correlationId, maxRetries: 2 }
      )

      // Run comprehensive analysis using all intelligence modules with retry
      const result = await errorService.withRetry(
        () => this.intelligenceIntegrator.analyzeComprehensively(
          conversationId,
          leadData,
          conversationHistory,
          context
        ),
        'advanced_intelligence_analysis',
        {
          maxRetries: 2,
          initialDelayMs: 2000,
          retryIf: (error) => error.shouldRetry && error.severity !== 'critical'
        },
        { correlationId }
      )

      // Validate result quality
      const validatedResult = this.validateAdvancedIntelligenceResult(result)

      // Track advanced analysis usage with detailed metrics
      this.contextManager.trackUIInteraction('concierge', 'advanced_analysis', {
        conversationId,
        confidence: validatedResult.confidence,
        recommendationsCount: validatedResult.recommendations.length,
        processingTime: validatedResult.processingTime,
        correlationId,
        analysisSuccess: true,
        validationPassed: true
      })

      return validatedResult
    } catch (error) {
      // 🚨 NEVER return empty result silently - provide intelligent fallback
      const { errorService } = await import('@/lib/errors/ErrorService')
      const errorInfo = await errorService.handleError(
        error,
        'ClaudeConciergeService.analyzeWithAdvancedIntelligence',
        {
          correlationId,
          reportToService: true,
          logToConsole: true
        }
      )

      const processingTime = Date.now() - startTime

      console.error('🚨 ADVANCED INTELLIGENCE FAILURE [FALLBACK ENGAGED]:', {
        errorId: errorInfo.id,
        conversationId,
        correlationId,
        processingTime,
        severity: errorInfo.severity,
        retryable: errorInfo.shouldRetry
      })

      // Track failure and fallback engagement
      this.contextManager.trackUIInteraction('concierge', 'advanced_analysis_fallback', {
        conversationId,
        errorId: errorInfo.id,
        correlationId,
        processingTime,
        fallbackEngaged: true
      })

      // Return intelligent fallback based on available data
      return this.createIntelligentAdvancedFallback(
        conversationId,
        leadData,
        conversationHistory,
        processingTime,
        errorInfo
      )
    }
  }

  /**
   * Determine if conversation should be handed off to specialized bot
   * PersonaAB-9 #77: Multi-Agent Orchestration
   * BULLETPROOF: Never returns null silently - always provides fallback
   */
  async evaluateHandoff(
    conversationId: string,
    message: string
  ): Promise<BotHandoffRecommendation | null> {
    const correlationId = `handoff_eval_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    try {
      const { errorService, apiWithRetry } = await import('@/lib/errors/ErrorService')

      // Get recent conversation context with retry
      const conversationHistory = await apiWithRetry(
        () => this.memoryManager.getConversationHistory(conversationId),
        'conversation_history',
        { correlationId, maxRetries: 2 }
      )

      const recentMessages = conversationHistory.slice(-5) // Last 5 messages

      // Build handoff evaluation prompt
      const handoffPrompt = this.promptEngine.buildHandoffPrompt()

      // Use fast model for routing decisions with retry
      const result = await errorService.withRetry(
        () => this.queryClaude({
          systemPrompt: handoffPrompt,
          userMessage: this.formatHandoffAnalysisInput(recentMessages, message),
          model: this.MODEL_ROUTING,
          maxTokens: 512
        }),
        'handoff_evaluation',
        {
          maxRetries: 2,
          initialDelayMs: 1000,
          retryIf: (error) => error.shouldRetry && error.code !== 'AUTH_ERROR'
        },
        { correlationId }
      )

      // Parse handoff decision with validation
      const content = typeof result === 'string' ? result : (result.content || result.primary_guidance)
      const handoffDecision = this.parseHandoffDecision(content)

      // Track handoff evaluation with detailed metadata
      this.contextManager.trackBotInteraction('concierge', 'handoff_evaluation', {
        conversationId,
        recommendation: handoffDecision?.targetBot || 'none',
        confidence: handoffDecision?.confidence || 0,
        correlationId,
        messageLength: message.length,
        historyLength: recentMessages.length
      })

      return handoffDecision
    } catch (error) {
      // 🚨 CRITICAL: Never return null silently - always log and provide fallback
      const { errorService } = await import('@/lib/errors/ErrorService')
      const errorInfo = await errorService.handleError(
        error,
        'ClaudeConciergeService.evaluateHandoff',
        {
          correlationId,
          reportToService: true,
          logToConsole: true
        }
      )

      console.error('🚨 HANDOFF EVALUATION FAILURE [NO SILENT RETURN]:', {
        errorId: errorInfo.id,
        conversationId,
        correlationId,
        severity: errorInfo.severity,
        retryable: errorInfo.shouldRetry,
        userMessage: errorInfo.userMessage
      })

      // Provide intelligent fallback based on message content
      const fallbackHandoff = this.createIntelligentHandoffFallback(message, errorInfo)

      // Track the fallback decision
      this.contextManager.trackBotInteraction('concierge', 'handoff_fallback', {
        conversationId,
        errorId: errorInfo.id,
        fallbackRecommendation: fallbackHandoff?.targetBot || 'none',
        fallbackConfidence: fallbackHandoff?.confidence || 0
      })

      return fallbackHandoff
    }
  }

  /**
   * Get conversation context for external systems
   */
  async getConversationContext(conversationId: string): Promise<{
    messages: Message[]
    metadata: any
    summary: string
  }> {
    const workingMemory = this.memoryManager.getWorkingMemory(conversationId)

    return {
      messages: workingMemory.messages,
      metadata: workingMemory.metadata,
      summary: this.generateConversationSummary(workingMemory.messages)
    }
  }

  /**
   * Update conversation with external context (from bot handoffs)
   */
  async updateConversationContext(
    conversationId: string,
    context: Record<string, any>
  ): Promise<void> {
    await this.memoryManager.updateConversationMetadata(conversationId, context)

    // Track context update
    this.contextManager.trackUIInteraction('concierge', 'context_updated', {
      conversationId,
      contextKeys: Object.keys(context)
    })
  }

  /**
   * Record successful bot handoff
   */
  async recordBotHandoff(
    conversationId: string,
    targetBot: string,
    transferredContext: Record<string, any>
  ): Promise<void> {
    await this.memoryManager.recordBotHandoff(
      conversationId,
      'concierge',
      targetBot,
      transferredContext
    )

    this.contextManager.trackBotInteraction('concierge', 'handoff_completed', {
      conversationId,
      targetBot,
      contextTransferred: Object.keys(transferredContext)
    })
  }

  /**
   * Get service health and performance metrics
   */
  getServiceMetrics(): {
    memoryStats: any
    contextStats: any
    responseTimeMetrics: any
    intelligenceStats: any
  } {
    const memoryStats = this.memoryManager.getMemoryStats()
    const contextSnapshot = this.contextManager.getContextSnapshot()
    const intelligenceStats = this.intelligenceIntegrator.getServiceMetrics()

    return {
      memoryStats,
      contextStats: {
        sessionDuration: contextSnapshot.userSession.totalTimeSpent,
        pagesVisited: contextSnapshot.userSession.pagesVisited.length,
        actionsPerformed: contextSnapshot.userSession.actionsPerformed
      },
      responseTimeMetrics: {
        // TODO: Implement response time tracking
        avgResponseTime: 0,
        lastResponseTime: 0
      },
      intelligenceStats: {
        enginesHealthy: intelligenceStats.enginesHealthy,
        lastAnalysisTime: intelligenceStats.lastAnalysisTime,
        recommendationsGenerated: intelligenceStats.recommendationsGenerated
      }
    }
  }

  /**
   * Stream response from Claude via backend proxy
   * Implements security by never exposing API key to frontend
   */
  private async streamFromClaude(params: {
    systemPrompt: string
    userMessage: string
    conversationHistory: Message[]
  }): Promise<ReadableStream> {
    const response = await fetch(`${this.baseApiUrl}/claude-concierge/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        systemPrompt: params.systemPrompt,
        messages: [
          ...params.conversationHistory,
          {
            role: 'user',
            content: params.userMessage
          }
        ],
        model: this.MODEL_MAIN,
        maxTokens: this.MAX_TOKENS,
        temperature: this.TEMPERATURE,
        stream: true,
        // Match backend expectations
        platform_context: await this.contextManager.captureContext()
      })
    })

    if (!response.ok) {
      throw new Error(`Claude API request failed: ${response.status} ${response.statusText}`)
    }

    return response.body!
  }

  /**
   * Direct Claude query without streaming (for routing/analysis)
   * ENHANCED: Now handles structured ConciergeResponseModel
   */
  private async queryClaude(params: {
    systemPrompt: string
    userMessage: string
    model?: string
    maxTokens?: number
  }): Promise<any> {
    const response = await fetch(`${this.baseApiUrl}/claude-concierge/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        systemPrompt: params.systemPrompt,
        message: params.userMessage,
        model: params.model || this.MODEL_MAIN,
        maxTokens: params.maxTokens || 1024,
        streaming: false,
        platform_context: await this.contextManager.captureContext()
      })
    })

    if (!response.ok) {
      throw new Error(`Claude query failed: ${response.status} ${response.statusText}`)
    }

    return await response.json()
  }

  /**
   * Process streaming response and update memory systems
   * BULLETPROOF: Handles stream failures gracefully
   */
  private async *processStreamWithMemory(
    stream: ReadableStream,
    conversationId: string,
    userMessage: string,
    correlationId?: string
  ): AsyncGenerator<string, ConciergeResponse> {
    const reader = stream.getReader()
    const decoder = new TextDecoder()

    let fullContent = ''
    let reasoning = ''
    let suggestedActions: SuggestedAction[] = []
    let botHandoff: BotHandoffRecommendation | null = null

    try {
      // Add user message to memory immediately
      await this.memoryManager.addMessage(conversationId, {
        role: 'user',
        content: userMessage,
        timestamp: new Date().toISOString()
      })

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              // Handle platform-standard format from FastAPI
              if (data.type === 'content' && data.data?.content) {
                const text = data.data.content
                fullContent += text
                yield text
              } 
              // Fallback for raw Anthropic format if needed
              else if (data.type === 'content_block_delta' && data.delta?.text) {
                const text = data.delta.text
                fullContent += text
                yield text
              }
            } catch (e) {
              console.warn('Failed to parse streaming chunk:', e)
            }
          }
        }
      }

      // Parse final response for structured elements
      const parsedResponse = this.parseStructuredResponse(fullContent)
      reasoning = parsedResponse.reasoning
      suggestedActions = parsedResponse.suggestedActions
      botHandoff = parsedResponse.botHandoff

      // Add assistant response to memory
      await this.memoryManager.addMessage(conversationId, {
        role: 'assistant',
        content: parsedResponse.cleanContent,
        timestamp: new Date().toISOString(),
        metadata: {
          reasoning,
          suggestedActions,
          botHandoff,
          leadIntelligence: parsedResponse.leadIntelligence
        }
      })

      // Update context with successful interaction
      this.contextManager.trackUIInteraction('concierge', 'response_completed', {
        conversationId,
        responseLength: fullContent.length,
        hasActions: suggestedActions.length > 0,
        hasHandoff: !!botHandoff,
        hasLeadIntelligence: !!parsedResponse.leadIntelligence
      })

      return {
        content: parsedResponse.cleanContent,
        reasoning,
        suggestedActions,
        botHandoff,
        leadIntelligence: parsedResponse.leadIntelligence
      }
    } catch (error) {
      console.error('Stream processing failed:', error)
      throw error
    } finally {
      reader.releaseLock()
    }
  }

  /**
   * Parse structured response elements from Claude output
   * ENHANCED: Now handles real orchestrator tags including immediate_actions and bot_coordination
   */
  private parseStructuredResponse(content: string): {
    cleanContent: string
    reasoning: string
    suggestedActions: SuggestedAction[]
    botHandoff: BotHandoffRecommendation | null
  } {
    let cleanContent = content
    let reasoning = ''
    const suggestedActions: SuggestedAction[] = []
    let botHandoff: BotHandoffRecommendation | null = null
    const leadIntelligence: any = {}

    // 1. Extract handoff recommendation (Full tag set)
    const handoffMatch = content.match(/<handoff>\s*<bot>(.*?)<\/bot>\s*<confidence>(.*?)<\/confidence>\s*<reasoning>(.*?)<\/reasoning>\s*(?:<context>(.*?)<\/context>)?\s*<\/handoff>/s)
    if (handoffMatch) {
      botHandoff = {
        targetBot: handoffMatch[1].trim() as any,
        confidence: parseFloat(handoffMatch[2].trim()),
        reasoning: handoffMatch[3].trim(),
        contextToTransfer: this.parseContextString(handoffMatch[4] || '{}')
      }
      cleanContent = cleanContent.replace(handoffMatch[0], '')
    }

    // 1.5 Extract Lead Intelligence Scores
    const frsMatch = content.match(/<frs_score>(.*?)<\/frs_score>/i)
    if (frsMatch) {
      leadIntelligence.frs_score = parseFloat(frsMatch[1].trim())
      cleanContent = cleanContent.replace(frsMatch[0], '')
    }
    const pcsMatch = content.match(/<pcs_score>(.*?)<\/pcs_score>/i)
    if (pcsMatch) {
      leadIntelligence.pcs_score = parseFloat(pcsMatch[1].trim())
      cleanContent = cleanContent.replace(pcsMatch[0], '')
    }
    const leadScoreMatch = content.match(/<lead_score>(.*?)<\/lead_score>/i)
    if (leadScoreMatch) {
      leadIntelligence.lead_score = parseFloat(leadScoreMatch[1].trim())
      cleanContent = cleanContent.replace(leadScoreMatch[0], '')
    }

    // 2. Extract immediate actions (New tag format from real orchestrator)
    const actionsBlockMatch = content.match(/<immediate_actions>(.*?)<\/immediate_actions>/s)
    if (actionsBlockMatch) {
      const actionRegex = /<action\s+priority="(.*?)"\s+category="(.*?)">(.*?)<\/action>/gs
      let actionMatch
      while ((actionMatch = actionRegex.exec(actionsBlockMatch[1])) !== null) {
        suggestedActions.push({
          type: 'bot_start', // Map to bot_start for execution
          label: actionMatch[3].trim(),
          description: `Action Priority: ${actionMatch[1]}`,
          priority: actionMatch[1] as any,
          data: { category: actionMatch[2] }
        })
      }
      cleanContent = cleanContent.replace(actionsBlockMatch[0], '')
    }

    // 3. Extract suggestions (Original tag format)
    const suggestionRegex = /<suggestion type="(.*?)">\s*<title>(.*?)<\/title>\s*<description>(.*?)<\/description>\s*<priority>(.*?)<\/priority>\s*<\/suggestion>/gs
    let suggestionMatch
    while ((suggestionMatch = suggestionRegex.exec(content)) !== null) {
      suggestedActions.push({
        type: suggestionMatch[1].trim() as any,
        label: suggestionMatch[2].trim(),
        description: suggestionMatch[3].trim(),
        priority: suggestionMatch[4].trim() as any,
        data: {}
      })
      cleanContent = cleanContent.replace(suggestionMatch[0], '')
    }

    // 4. Extract bot coordination suggestions
    const botCoordMatch = content.match(/<bot_coordination>(.*?)<\/bot_coordination>/s)
    if (botCoordMatch) {
      const coordRegex = /<suggestion\s+bot_type="(.*?)">(.*?)<\/suggestion>/gs
      let coordMatch
      while ((coordMatch = coordRegex.exec(botCoordMatch[1])) !== null) {
        suggestedActions.push({
          type: 'bot_start',
          label: `Handoff to ${coordMatch[1]}`,
          description: coordMatch[2].trim(),
          priority: 'medium',
          data: { botId: coordMatch[1] }
        })
      }
      cleanContent = cleanContent.replace(botCoordMatch[0], '')
    }

    // 5. Extract reasoning
    const reasoningMatch = content.match(/<reasoning>(.*?)<\/reasoning>/s)
    if (reasoningMatch) {
      reasoning = reasoningMatch[1].trim()
      cleanContent = cleanContent.replace(reasoningMatch[0], '')
    }

    // 6. Clean up remaining metadata tags
    const metadataTags = ['primary_guidance', 'urgency_level', 'risk_alerts'];
    for (const tag of metadataTags) {
      const tagRegex = new RegExp(`<${tag}>(.*?)<\/${tag}>`, 'gs');
      cleanContent = cleanContent.replace(tagRegex, '');
    }

    return {
      cleanContent: cleanContent.trim(),
      reasoning,
      suggestedActions,
      botHandoff,
      leadIntelligence: Object.keys(leadIntelligence).length > 0 ? leadIntelligence : undefined
    }
  }

  /**
   * Parse context string safely
   */
  private parseContextString(contextStr: string): Record<string, any> {
    try {
      return JSON.parse(contextStr)
    } catch {
      return {}
    }
  }

  /**
   * Parse handoff decision from Claude response
   */
  private parseHandoffDecision(response: string): BotHandoffRecommendation | null {
    try {
      const parsed = JSON.parse(response)

      if (!parsed.shouldHandoff || !parsed.targetBot) {
        return null
      }

      return {
        targetBot: parsed.targetBot,
        confidence: parsed.confidence || 0,
        reasoning: parsed.reasoning || '',
        contextToTransfer: parsed.contextToTransfer || {}
      }
    } catch (error) {
      console.warn('Failed to parse handoff decision:', error)
      return null
    }
  }

  /**
   * Format handoff analysis input for Claude
   */
  private formatHandoffAnalysisInput(recentMessages: Message[], currentMessage: string): string {
    const conversation = recentMessages
      .map(msg => `${msg.role}: ${msg.content}`)
      .join('\n')

    return `Recent Conversation:\n${conversation}\n\nNew User Message: ${currentMessage}`
  }

  /**
   * Parse suggestions from context analysis response
   */
  private parseSuggestionsFromResponse(response: string): ProactiveSuggestion[] {
    try {
      const parsed = JSON.parse(response)

      if (!Array.isArray(parsed)) {
        return []
      }

      return parsed.map((suggestion, index) => ({
        id: `suggestion_${Date.now()}_${index}`,
        ...suggestion
      }))
    } catch (error) {
      console.warn('Failed to parse suggestions:', error)
      return []
    }
  }

  /**
   * Create fallback response for errors using error classification
   * ENHANCED: Provides detailed guidance and correlation tracking
   */
  private createFallbackResponse(errorInfo: any, correlationId?: string): ConciergeResponse {
    let content = errorInfo.userMessage || "I'm having trouble connecting to my AI services right now. "

    // Add specific guidance based on error type
    if (errorInfo.category === 'network') {
      content += " Please check your internet connection and try again."
    } else if (errorInfo.category === 'api' && errorInfo.code === 'RATE_LIMIT') {
      content += " I'm experiencing high usage - please try again in a moment."
    } else if (errorInfo.shouldRetry) {
      content += " This appears to be a temporary issue. Please try again."
    } else {
      content += " Let me help you navigate the platform directly instead."
    }

    return {
      content,
      suggestedActions: [
        {
          type: 'navigation',
          label: 'Go to Dashboard',
          description: 'Return to the main Jorge Command Center',
          data: { route: '/jorge' }
        },
        {
          type: 'bot_start',
          label: 'Start Jorge Seller Bot',
          description: 'Begin seller qualification process',
          data: { botId: 'jorge-seller-bot' }
        }
      ]
    }
  }

  /**
   * Get fallback suggestions when analysis fails
   * ENHANCED: Intelligent fallback based on error context
   */
  private getFallbackSuggestions(context?: PlatformContext, errorInfo?: any): ProactiveSuggestion[] {
    const now = new Date().toISOString()
    const timestamp = Date.now()

    // Base fallback suggestions
    const baseSuggestions = [
      {
        id: `fallback_${timestamp}_1`,
        type: 'feature' as const,
        title: 'Explore Jorge Seller Bot',
        description: 'Try the confrontational qualification specialist for motivated sellers',
        priority: 'medium' as const,
        action: {
          type: 'bot_start' as const,
          label: 'Start Jorge Seller Bot',
          description: 'Begin seller qualification',
          data: { botId: 'jorge-seller-bot' }
        }
      },
      {
        id: `fallback_${timestamp}_2`,
        type: 'workflow' as const,
        title: 'Check Lead Performance',
        description: 'Review recent lead qualification and conversion metrics',
        priority: 'medium' as const,
        action: {
          type: 'navigation' as const,
          label: 'View Analytics',
          description: 'Open performance dashboard',
          data: { route: '/jorge?tab=analytics' }
        }
      }
    ]

    // Add error-specific suggestions if error info is available
    if (errorInfo) {
      if (errorInfo.category === 'network') {
        baseSuggestions.unshift({
          id: `fallback_${timestamp}_network`,
          type: 'workflow' as const,
          title: 'Connection Issue Detected',
          description: 'Try refreshing the page or check your internet connection',
          priority: 'high' as const,
          action: {
            type: 'navigation' as const,
            label: 'Refresh Page',
            description: 'Reload the application',
            data: { route: window.location.pathname }
          }
        })
      } else if (errorInfo.category === 'api') {
        baseSuggestions.unshift({
          id: `fallback_${timestamp}_api`,
          type: 'workflow' as const,
          title: 'Service Temporarily Unavailable',
          description: 'AI services are experiencing issues. Try again in a moment.',
          priority: 'high' as const,
          action: {
            type: 'navigation' as const,
            label: 'Try Jorge Bots Directly',
            description: 'Access bot interfaces directly',
            data: { route: '/jorge?tab=bots' }
          }
        })
      }
    }

    return baseSuggestions
  }

  /**
   * Create intelligent handoff fallback when handoff evaluation fails
   */
  private createIntelligentHandoffFallback(
    message: string,
    errorInfo: any
  ): BotHandoffRecommendation | null {
    // Simple keyword-based fallback logic
    const lowerMessage = message.toLowerCase()

    // Detect seller-related keywords
    if (lowerMessage.includes('sell') || lowerMessage.includes('listing') ||
        lowerMessage.includes('price') || lowerMessage.includes('market')) {
      return {
        targetBot: 'jorge-seller-bot',
        confidence: 0.7, // Lower confidence for fallback
        reasoning: `Fallback recommendation based on seller keywords. Original analysis failed due to: ${errorInfo.code}`,
        contextToTransfer: {
          fallback_reason: errorInfo.code,
          original_message: message,
          confidence_reduced: true,
          manual_review_suggested: true
        }
      }
    }

    // Detect lead nurture keywords
    if (lowerMessage.includes('follow') || lowerMessage.includes('contact') ||
        lowerMessage.includes('schedule') || lowerMessage.includes('call')) {
      return {
        targetBot: 'lead-bot',
        confidence: 0.6,
        reasoning: `Fallback recommendation based on lead management keywords. Original analysis failed due to: ${errorInfo.code}`,
        contextToTransfer: {
          fallback_reason: errorInfo.code,
          original_message: message,
          confidence_reduced: true,
          manual_review_suggested: true
        }
      }
    }

    // No clear handoff needed or detectable - return null
    return null
  }

  /**
   * Create intelligent advanced intelligence fallback
   */
  private createIntelligentAdvancedFallback(
    conversationId: string,
    leadData: any,
    conversationHistory: any[],
    processingTime: number,
    errorInfo: any
  ): any {
    // Basic analysis based on available data
    const messageCount = conversationHistory?.length || 0
    const hasLeadData = leadData && Object.keys(leadData).length > 0

    // Simple heuristics for fallback recommendations
    const recommendations = []

    if (messageCount === 0) {
      recommendations.push({
        type: 'initialization',
        priority: 'high',
        suggestion: 'Start conversation with Jorge Seller Bot for immediate lead qualification',
        confidence: 0.8
      })
    } else if (messageCount < 3) {
      recommendations.push({
        type: 'engagement',
        priority: 'medium',
        suggestion: 'Continue engagement to gather more qualification data',
        confidence: 0.6
      })
    } else {
      recommendations.push({
        type: 'analysis',
        priority: 'medium',
        suggestion: 'Review conversation patterns and consider bot handoff',
        confidence: 0.5
      })
    }

    if (!hasLeadData) {
      recommendations.push({
        type: 'data_collection',
        priority: 'high',
        suggestion: 'Collect basic lead information before proceeding',
        confidence: 0.9
      })
    }

    return {
      recommendations,
      confidence: 0.3, // Low confidence for fallback
      processingTime,
      fallback_reason: errorInfo.code,
      manual_review_required: true,
      original_error: {
        code: errorInfo.code,
        category: errorInfo.category,
        severity: errorInfo.severity
      }
    }
  }

  /**
   * Validate advanced intelligence result quality
   */
  private validateAdvancedIntelligenceResult(result: any): any {
    // Ensure minimum result structure
    if (!result || typeof result !== 'object') {
      return {
        recommendations: [],
        confidence: 0.1,
        processingTime: 0,
        validation_failed: true
      }
    }

    // Ensure recommendations array exists
    if (!Array.isArray(result.recommendations)) {
      result.recommendations = []
    }

    // Ensure confidence is a valid number
    if (typeof result.confidence !== 'number' || isNaN(result.confidence)) {
      result.confidence = 0.1
    }

    // Clamp confidence to valid range
    result.confidence = Math.max(0, Math.min(1, result.confidence))

    // Ensure processing time is valid
    if (typeof result.processingTime !== 'number' || isNaN(result.processingTime)) {
      result.processingTime = 0
    }

    return result
  }

  /**
   * Generate conversation summary for context
   */
  private generateConversationSummary(messages: Message[]): string {
    if (messages.length === 0) {
      return 'No conversation yet'
    }

    const recentMessages = messages.slice(-3)
    const summary = recentMessages
      .map(msg => `${msg.role}: ${msg.content.substring(0, 100)}`)
      .join(' | ')

    return `Recent: ${summary}`
  }

  /**
   * Setup context tracking for concierge interactions
   */
  private setupContextTracking(): void {
    this.contextManager.on('context_update', (event: any) => {
      // Could emit events to external systems or analytics
      // For now, just log for debugging
      console.debug('Context updated:', event.detail.triggeringActivity)
    })
  }

  // ✨ OMNIPRESENT COORDINATION METHODS

  /**
   * Initialize omnipresent capabilities for cross-bot coordination
   */
  private async initializeOmnipresentCapabilities(): Promise<void> {
    try {
      // Initialize the coordination engine
      await this.coordinationEngine.initialize()

      // Setup coordination event listeners
      this.setupCoordinationEventHandlers()

      console.log('✅ Omnipresent Claude Concierge capabilities initialized')
    } catch (error) {
      console.error('❌ Failed to initialize omnipresent capabilities:', error)
    }
  }

  /**
   * Enable omnipresent monitoring for a conversation
   * Makes Concierge aware of all bot activities and able to provide real-time coaching
   */
  async enableOmnipresentAwareness(
    conversationId: string,
    contactId: string,
    locationId: string
  ): Promise<void> {
    try {
      // Enable bot coordination monitoring
      await this.coordinationEngine.enableOmnipresentMonitoring(conversationId, contactId, locationId)

      // Update memory context to include omnipresent state
      await this.memoryManager.updateWorkingMemory(conversationId, {
        omnipresent_monitoring: {
          enabled: true,
          conversation_id: conversationId,
          contact_id: contactId,
          location_id: locationId,
          enabled_at: new Date().toISOString()
        }
      })

      // Track in platform context
      this.contextManager.trackUIInteraction('concierge', 'omnipresent_enabled', {
        conversationId,
        contactId,
        locationId
      })

      console.log(`🎯 Omnipresent awareness enabled for conversation ${conversationId}`)
    } catch (error) {
      console.error('❌ Failed to enable omnipresent awareness:', error)
      throw error
    }
  }

  /**
   * Orchestrate a bot handoff with full context preservation
   */
  async orchestrateBotHandoff(
    conversationId: string,
    targetBot: 'jorge-seller' | 'lead-bot' | 'intent-decoder',
    reason: string,
    urgency: 'immediate' | 'scheduled' | 'background' = 'scheduled'
  ): Promise<HandoffResult> {
    try {
      // Get current conversation context
      const memoryContext = await this.memoryManager.getRelevantMemory(conversationId, reason)
      const platformContext = await this.contextManager.captureContext()

      // Build handoff request with Jorge methodology context
      const handoffRequest = {
        conversation_id: conversationId,
        from_bot: 'claude-concierge' as const,
        to_bot: targetBot,
        contact_id: platformContext.currentData?.lead?.id || '',
        location_id: platformContext.currentData?.lead?.locationId || '',
        handoff_reason: this.categorizeHandoffReason(reason),
        urgency,
        context_transfer: {
          conversation_history: memoryContext.workingMemory.messages,
          lead_temperature: this.extractLeadTemperature(memoryContext),
          qualification_scores: this.extractQualificationScores(memoryContext),
          current_intent: reason,
          next_recommended_action: await this.generateNextAction(targetBot, memoryContext)
        }
      }

      // Execute handoff via coordination engine
      const result = await this.coordinationEngine.orchestrateHandoff(handoffRequest)

      // Update memory with handoff details
      if (result.success) {
        await this.memoryManager.recordEpisodicInteraction(conversationId, {
          type: 'bot_handoff',
          outcome: 'success',
          details: {
            target_bot: targetBot,
            handoff_id: result.handoff_id,
            context_preserved: result.context_preserved,
            handoff_time_ms: result.handoff_time_ms
          }
        })
      }

      return result
    } catch (error) {
      console.error('❌ Bot handoff orchestration failed:', error)
      throw error
    }
  }

  /**
   * Provide real-time coaching to active bots based on conversation analysis
   */
  async provideRealTimeCoaching(
    conversationId: string,
    coachingType: 'response_optimization' | 'timing_adjustment' | 'strategy_pivot' | 'objection_handling' | 'temperature_escalation',
    analysisContext?: any
  ): Promise<CoachingResult> {
    try {
      // Analyze conversation for coaching opportunities
      const memoryContext = await this.memoryManager.getRelevantMemory(conversationId, 'coaching analysis')
      const conversationIntelligence = await this.intelligenceIntegrator.analyzeConversation(
        conversationId,
        memoryContext.workingMemory.messages
      )

      // Generate Jorge-specific coaching guidance
      const coachingGuidance = await this.generateJorgeCoaching(
        coachingType,
        conversationIntelligence,
        analysisContext
      )

      // Deliver coaching via coordination engine
      const result = await this.coordinationEngine.provideRealTimeCoaching(
        conversationId,
        coachingType,
        coachingGuidance.suggestion,
        coachingGuidance.urgency
      )

      // Track coaching delivery
      await this.memoryManager.recordEpisodicInteraction(conversationId, {
        type: 'coaching_provided',
        outcome: result.delivered ? 'delivered' : 'failed',
        details: {
          coaching_type: coachingType,
          coaching_id: result.coaching_id,
          guidance: coachingGuidance.suggestion
        }
      })

      return result
    } catch (error) {
      console.error('❌ Real-time coaching failed:', error)
      throw error
    }
  }

  /**
   * Get real-time coordination metrics for omnipresent intelligence
   */
  getCoordinationMetrics(): CoordinationMetrics {
    return this.coordinationEngine.getCoordinationMetrics()
  }

  /**
   * Get active bot sessions across the platform
   */
  getActiveBotSessions(): BotSession[] {
    return this.coordinationEngine.getActiveSessions()
  }

  /**
   * Sync context across all active bots for a conversation
   */
  async syncContextAcrossBots(conversationId: string): Promise<void> {
    try {
      // Get latest intelligence insights
      const memoryContext = await this.memoryManager.getRelevantMemory(conversationId, 'context sync')
      const intelligence = await this.intelligenceIntegrator.analyzeComprehensively(
        conversationId,
        {}, // Lead data from context
        memoryContext.workingMemory.messages,
        await this.contextManager.captureContext()
      )

      // Update coordination engine with latest context
      await this.coordinationEngine.syncContextAcrossBots(conversationId)

      // Track context sync
      this.contextManager.trackUIInteraction('concierge', 'context_sync', {
        conversationId,
        intelligenceUpdated: intelligence.recommendations.length > 0
      })

      console.log(`🔄 Context synchronized across bots for conversation ${conversationId}`)
    } catch (error) {
      console.error('❌ Cross-bot context sync failed:', error)
      throw error
    }
  }

  // Private helper methods for omnipresent coordination

  private setupCoordinationEventHandlers(): void {
    // Listen for coordination opportunities
    // These would be implemented to handle real-time events from the coordination engine
    console.log('📡 Coordination event handlers configured')
  }

  private categorizeHandoffReason(reason: string): 'qualification_complete' | 'needs_specialized_help' | 'escalation' | 'sequence_trigger' | 'coach_request' {
    // Smart categorization based on reason content
    if (reason.includes('qualification') || reason.includes('qualify')) return 'qualification_complete'
    if (reason.includes('sequence') || reason.includes('follow')) return 'sequence_trigger'
    if (reason.includes('coach') || reason.includes('help')) return 'coach_request'
    if (reason.includes('escalate') || reason.includes('complex')) return 'escalation'
    return 'needs_specialized_help'
  }

  private extractLeadTemperature(memoryContext: any): 'hot' | 'warm' | 'cold' {
    // Extract temperature from conversation context
    const messages = memoryContext.workingMemory.messages || []
    if (messages.length === 0) return 'cold'

    // Simple heuristic - would be enhanced with actual temperature tracking
    const urgentKeywords = ['urgent', 'asap', 'immediately', 'ready']
    const engagementKeywords = ['interested', 'questions', 'when', 'how']

    const recentText = messages.slice(-3).map(m => m.content).join(' ').toLowerCase()

    if (urgentKeywords.some(keyword => recentText.includes(keyword))) return 'hot'
    if (engagementKeywords.some(keyword => recentText.includes(keyword))) return 'warm'
    return 'cold'
  }

  private extractQualificationScores(memoryContext: any): { frs_score?: number; pcs_score?: number; confidence?: number } {
    // Extract qualification scores from memory context
    // This would integrate with Jorge's actual scoring system
    return {
      frs_score: 65, // Financial Readiness Score placeholder
      pcs_score: 78, // Psychological Commitment Score placeholder
      confidence: 0.82
    }
  }

  private async generateNextAction(targetBot: string, memoryContext: any): Promise<string> {
    // Generate next recommended action based on target bot and context
    switch (targetBot) {
      case 'jorge-seller':
        return 'Begin confrontational qualification with Jorge\'s 4 core questions'
      case 'lead-bot':
        return 'Start 3-7-30 day nurture sequence with CMA value injection'
      case 'intent-decoder':
        return 'Run 28-feature ML analysis for FRS/PCS scoring'
      default:
        return 'Continue conversation with platform guidance'
    }
  }

  private async generateJorgeCoaching(
    coachingType: string,
    conversationIntelligence: any,
    analysisContext?: any
  ): Promise<{ suggestion: string; urgency: 'immediate' | 'next_message' | 'informational' }> {
    // Generate Jorge-specific coaching based on type and context
    switch (coachingType) {
      case 'objection_handling':
        return {
          suggestion: "Use Jorge's confrontational approach: Acknowledge → Challenge assumption → Pivot to qualification. Don't coddle the objection.",
          urgency: 'immediate'
        }
      case 'temperature_escalation':
        return {
          suggestion: "Apply heat: Increase urgency, challenge timeline, emphasize competition and scarcity. Jorge's method works.",
          urgency: 'next_message'
        }
      case 'response_optimization':
        return {
          suggestion: "Keep under 160 chars, no emojis. Direct and professional. Challenge assumptions, don't be agreeable.",
          urgency: 'immediate'
        }
      case 'strategy_pivot':
        return {
          suggestion: "Pivot to qualification focus. Ask hard questions about timeline, motivation, and decision-making authority.",
          urgency: 'next_message'
        }
      default:
        return {
          suggestion: "Apply Jorge's no-BS methodology: Direct questions, confrontational qualification, focus on motivated sellers only.",
          urgency: 'informational'
        }
    }
  }
}