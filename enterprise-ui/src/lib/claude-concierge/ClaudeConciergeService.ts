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

    this.setupContextTracking()
  }

  /**
   * Main conversation handler with streaming support
   * Pattern: Similar to useChatStore.sendMessage but with memory integration
   */
  async *chat(request: ConciergeRequest): AsyncGenerator<string, ConciergeResponse> {
    try {
      // 1. Track user interaction
      this.contextManager.trackUIInteraction('concierge', 'message_sent', {
        conversationId: request.conversationId,
        messageLength: request.userMessage.length
      })

      // 2. Load memory context with relevance filtering
      const memoryContext = await this.memoryManager.getRelevantMemory(
        request.conversationId,
        request.userMessage
      )

      // 3. Assemble current platform context
      const platformContext = await this.contextManager.captureContext(
        request.platformContext
      )

      // 4. Generate optimized prompt (PersonaAB-9 #26: Meta-Prompting)
      const systemPrompt = this.promptEngine.buildConciergePrompt({
        memoryContext,
        platformContext,
        conversationHistory: memoryContext.workingMemory.messages,
      })

      // 5. Stream response from Claude via backend proxy
      const streamResponse = await this.streamFromClaude({
        systemPrompt,
        userMessage: request.userMessage,
        conversationHistory: memoryContext.workingMemory.messages
      })

      // 6. Process stream and update memory
      const finalResponse = yield* this.processStreamWithMemory(
        streamResponse,
        request.conversationId,
        request.userMessage
      )

      return finalResponse
    } catch (error) {
      console.error('Concierge chat failed:', error)

      // Graceful fallback response
      const fallbackResponse = this.createFallbackResponse(error)
      yield fallbackResponse.content
      return fallbackResponse
    }
  }

  /**
   * Analyze platform state and provide proactive suggestions
   * PersonaAB-9 #40: Contextual Selective Recall
   */
  async analyzeContext(context?: PlatformContext): Promise<ProactiveSuggestion[]> {
    try {
      // Capture current platform state
      const platformState = await this.contextManager.captureContext(context)

      // Get activity patterns for analysis
      const activityPatterns = this.contextManager.getActivityPatterns()

      // Generate context analysis prompt
      const analysisPrompt = this.promptEngine.buildContextAnalysisPrompt(platformState)

      // Use fast model for quick analysis
      const response = await this.queryClaude({
        systemPrompt: analysisPrompt,
        userMessage: JSON.stringify(activityPatterns),
        model: this.MODEL_ROUTING,
        maxTokens: 1024
      })

      // Parse suggestions from response
      const suggestions = this.parseSuggestionsFromResponse(response)

      // Track analysis event
      this.contextManager.trackUIInteraction('concierge', 'context_analyzed', {
        suggestionsGenerated: suggestions.length,
        patterns: activityPatterns.sessionFocus
      })

      return suggestions
    } catch (error) {
      console.error('Context analysis failed:', error)
      return this.getFallbackSuggestions(context)
    }
  }

  /**
   * Advanced intelligence analysis with all AI modules
   * PersonaAB-9 #83 (Predictive Analytics), #67 (Market Integration)
   */
  async analyzeWithAdvancedIntelligence(
    conversationId: string,
    leadData: any,
    conversationHistory: any[],
    platformContext?: PlatformContext
  ): Promise<AdvancedIntelligenceResult> {
    try {
      // Capture current platform context if not provided
      const context = platformContext || await this.contextManager.captureContext()

      // Run comprehensive analysis using all intelligence modules
      const result = await this.intelligenceIntegrator.analyzeComprehensively(
        conversationId,
        leadData,
        conversationHistory,
        context
      )

      // Track advanced analysis usage
      this.contextManager.trackUIInteraction('concierge', 'advanced_analysis', {
        conversationId,
        confidence: result.confidence,
        recommendationsCount: result.recommendations.length,
        processingTime: result.processingTime
      })

      return result
    } catch (error) {
      console.error('Advanced intelligence analysis failed:', error)

      // Return minimal fallback result
      return {
        recommendations: [],
        confidence: 0.1,
        processingTime: 0
      }
    }
  }

  /**
   * Determine if conversation should be handed off to specialized bot
   * PersonaAB-9 #77: Multi-Agent Orchestration
   */
  async evaluateHandoff(
    conversationId: string,
    message: string
  ): Promise<BotHandoffRecommendation | null> {
    try {
      // Get recent conversation context
      const conversationHistory = this.memoryManager.getConversationHistory(conversationId)
      const recentMessages = conversationHistory.slice(-5) // Last 5 messages

      // Build handoff evaluation prompt
      const handoffPrompt = this.promptEngine.buildHandoffPrompt()

      // Use fast model for routing decisions
      const response = await this.queryClaude({
        systemPrompt: handoffPrompt,
        userMessage: this.formatHandoffAnalysisInput(recentMessages, message),
        model: this.MODEL_ROUTING,
        maxTokens: 512
      })

      // Parse handoff decision
      const handoffDecision = this.parseHandoffDecision(response)

      // Track handoff evaluation
      this.contextManager.trackBotInteraction('concierge', 'handoff_evaluation', {
        conversationId,
        recommendation: handoffDecision?.targetBot || 'none',
        confidence: handoffDecision?.confidence || 0
      })

      return handoffDecision
    } catch (error) {
      console.error('Handoff evaluation failed:', error)
      return null
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
    const response = await fetch(`${this.baseApiUrl}/concierge/chat`, {
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
        stream: true
      })
    })

    if (!response.ok) {
      throw new Error(`Claude API request failed: ${response.status} ${response.statusText}`)
    }

    return response.body!
  }

  /**
   * Direct Claude query without streaming (for routing/analysis)
   */
  private async queryClaude(params: {
    systemPrompt: string
    userMessage: string
    model?: string
    maxTokens?: number
  }): Promise<string> {
    const response = await fetch(`${this.baseApiUrl}/concierge/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        systemPrompt: params.systemPrompt,
        message: params.userMessage,
        model: params.model || this.MODEL_MAIN,
        maxTokens: params.maxTokens || 1024
      })
    })

    if (!response.ok) {
      throw new Error(`Claude query failed: ${response.status} ${response.statusText}`)
    }

    const result = await response.json()
    return result.content
  }

  /**
   * Process streaming response and update memory systems
   */
  private async *processStreamWithMemory(
    stream: ReadableStream,
    conversationId: string,
    userMessage: string
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

              if (data.type === 'content_block_delta' && data.delta?.text) {
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
          botHandoff
        }
      })

      // Update context with successful interaction
      this.contextManager.trackUIInteraction('concierge', 'response_completed', {
        conversationId,
        responseLength: fullContent.length,
        hasActions: suggestedActions.length > 0,
        hasHandoff: !!botHandoff
      })

      return {
        content: parsedResponse.cleanContent,
        reasoning,
        suggestedActions,
        botHandoff
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

    // Extract handoff recommendation
    const handoffMatch = content.match(/<handoff>\s*<bot>(.*?)<\/bot>\s*<confidence>(.*?)<\/confidence>\s*<reasoning>(.*?)<\/reasoning>\s*(?:<context>(.*?)<\/context>)?\s*<\/handoff>/s)
    if (handoffMatch) {
      botHandoff = {
        targetBot: handoffMatch[1].trim() as any,
        confidence: parseFloat(handoffMatch[2].trim()),
        reasoning: handoffMatch[3].trim(),
        contextToTransfer: this.parseContextString(handoffMatch[4] || '{}')
      }
      cleanContent = cleanContent.replace(handoffMatch[0], '').trim()
    }

    // Extract suggestions
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
      cleanContent = cleanContent.replace(suggestionMatch[0], '').trim()
    }

    // Extract reasoning (if any structured reasoning blocks exist)
    const reasoningMatch = content.match(/<reasoning>(.*?)<\/reasoning>/s)
    if (reasoningMatch) {
      reasoning = reasoningMatch[1].trim()
      cleanContent = cleanContent.replace(reasoningMatch[0], '').trim()
    }

    return {
      cleanContent: cleanContent.trim(),
      reasoning,
      suggestedActions,
      botHandoff
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
   * Create fallback response for errors
   */
  private createFallbackResponse(error: any): ConciergeResponse {
    const isNetworkError = error.name === 'TypeError' || error.message.includes('fetch')
    const isRateLimit = error.message.includes('429')

    let content = "I'm having trouble connecting to my AI services right now. "

    if (isRateLimit) {
      content += "I'm experiencing high usage - please try again in a moment."
    } else if (isNetworkError) {
      content += "Please check your internet connection and try again."
    } else {
      content += "Let me help you navigate the platform directly instead."
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
   */
  private getFallbackSuggestions(context?: PlatformContext): ProactiveSuggestion[] {
    const now = new Date().toISOString()

    return [
      {
        id: `fallback_${Date.now()}_1`,
        type: 'feature',
        title: 'Explore Jorge Seller Bot',
        description: 'Try the confrontational qualification specialist for motivated sellers',
        priority: 'medium',
        action: {
          type: 'bot_start',
          label: 'Start Jorge Seller Bot',
          description: 'Begin seller qualification',
          data: { botId: 'jorge-seller-bot' }
        }
      },
      {
        id: `fallback_${Date.now()}_2`,
        type: 'workflow',
        title: 'Check Lead Performance',
        description: 'Review recent lead qualification and conversion metrics',
        priority: 'medium',
        action: {
          type: 'navigation',
          label: 'View Analytics',
          description: 'Open performance dashboard',
          data: { route: '/jorge?tab=analytics' }
        }
      }
    ]
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
}