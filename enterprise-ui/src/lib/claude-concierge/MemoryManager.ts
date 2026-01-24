/**
 * Three-tier memory hierarchy implementation
 * Implements: PersonaAB-9 #21 (Memory Hierarchy)
 *
 * Tier 1 - Working Memory: Session storage, conversation context
 * Tier 2 - Episodic Memory: IndexedDB, 7-day retention, past interactions
 * Tier 3 - Semantic Memory: Server-stored, Jorge knowledge, platform docs
 */

import type {
  MemoryHierarchy,
  ConversationContext,
  PastInteraction,
  PlatformKnowledge,
  Message,
  LeadData,
  BotHandoff
} from './PersonaPromptEngine'

export interface EpisodicInteraction {
  id?: number
  conversationId: string
  message: Message
  timestamp: string
  summary: string
  outcome: 'success' | 'escalation' | 'incomplete' | 'handoff'
  relevanceScore: number
  relatedEntities: string[]
  keywords: string[]
}

export interface SearchOptions {
  limit: number
  minRelevance: number
  timeWindow?: number // Hours to look back
  entityFilter?: string[]
}

export class MemoryManager {
  private workingMemoryCache: Map<string, ConversationContext> = new Map()
  private episodicDb: EpisodicDatabase
  private semanticCache: PlatformKnowledge | null = null
  private readonly MAX_WORKING_MEMORY_SIZE = 50 // Max conversations in memory

  constructor() {
    this.episodicDb = new EpisodicDatabase()
    this.loadSemanticMemory()
    this.startPeriodicCleanup()
  }

  /**
   * Retrieve relevant memory for current conversation
   * PersonaAB-9 #40: Buffer of Thoughts pattern
   */
  async getRelevantMemory(
    conversationId: string,
    currentMessage: string
  ): Promise<MemoryHierarchy> {
    // 1. Working Memory (always loaded for active conversation)
    const workingMemory = this.getWorkingMemory(conversationId)

    // 2. Episodic Memory (similarity search based on current message)
    const episodicMemory = await this.searchEpisodicMemory(currentMessage, {
      limit: 5,
      minRelevance: 0.7,
      timeWindow: 168 // Last 7 days
    })

    // 3. Semantic Memory (always available, pre-loaded)
    const semanticMemory = await this.getSemanticMemory()

    return {
      workingMemory,
      episodicMemory: episodicMemory.map(this.convertToInterface),
      semanticMemory
    }
  }

  /**
   * Get or create working memory for conversation
   */
  getWorkingMemory(conversationId: string): ConversationContext {
    let context = this.workingMemoryCache.get(conversationId)

    if (!context) {
      context = {
        conversationId,
        messages: [],
        startTime: new Date().toISOString(),
        lastActivity: new Date().toISOString(),
        metadata: {
          botHandoffs: []
        }
      }
      this.workingMemoryCache.set(conversationId, context)
    }

    return context
  }

  /**
   * Add message to working memory and persist to episodic
   */
  async addMessage(
    conversationId: string,
    message: Message,
    metadata?: {
      outcome?: 'success' | 'escalation' | 'incomplete' | 'handoff'
      relatedEntities?: string[]
    }
  ): Promise<void> {
    // Update working memory
    const context = this.getWorkingMemory(conversationId)
    context.messages.push(message)
    context.lastActivity = new Date().toISOString()

    // Update metadata if provided
    if (metadata?.relatedEntities) {
      context.metadata.leadContext = this.extractLeadContext(metadata.relatedEntities)
    }

    this.workingMemoryCache.set(conversationId, context)

    // Persist to episodic memory (async, non-blocking)
    this.persistToEpisodicMemory(conversationId, message, metadata)
      .catch(error => {
        console.warn('Episodic memory persistence failed:', error)
        // Continue execution - memory loss for single interaction is acceptable
      })

    // Clean up working memory if it gets too large
    this.manageWorkingMemorySize()
  }

  /**
   * Update conversation metadata (lead context, intent scores, etc.)
   */
  updateConversationMetadata(
    conversationId: string,
    updates: {
      leadContext?: LeadData
      intentScores?: { frs: number; pcs: number }
      botHandoffs?: BotHandoff[]
    }
  ): void {
    const context = this.getWorkingMemory(conversationId)

    if (updates.leadContext) {
      context.metadata.leadContext = updates.leadContext
    }

    if (updates.intentScores) {
      context.metadata.intentScores = updates.intentScores
    }

    if (updates.botHandoffs) {
      context.metadata.botHandoffs = updates.botHandoffs
    }

    context.lastActivity = new Date().toISOString()
    this.workingMemoryCache.set(conversationId, context)
  }

  /**
   * Record bot handoff in memory systems
   */
  async recordBotHandoff(
    conversationId: string,
    fromBot: string,
    toBot: string,
    transferredContext: Record<string, any>
  ): Promise<void> {
    const handoff: BotHandoff = {
      fromBot,
      toBot,
      timestamp: new Date().toISOString(),
      context: transferredContext
    }

    // Update working memory
    const context = this.getWorkingMemory(conversationId)
    context.metadata.botHandoffs.push(handoff)
    this.workingMemoryCache.set(conversationId, context)

    // Create episodic record for handoff
    const handoffMessage: Message = {
      role: 'assistant',
      content: `Conversation transferred from ${fromBot} to ${toBot}`,
      timestamp: handoff.timestamp,
      metadata: { handoff: true, transferredContext }
    }

    await this.addMessage(conversationId, handoffMessage, {
      outcome: 'handoff',
      relatedEntities: [fromBot, toBot]
    })
  }

  /**
   * Get conversation history for analysis
   */
  getConversationHistory(conversationId: string): Message[] {
    const context = this.workingMemoryCache.get(conversationId)
    return context?.messages || []
  }

  /**
   * Search episodic memory using keyword and recency scoring
   * TODO: Implement vector similarity search in future enhancement
   */
  private async searchEpisodicMemory(
    query: string,
    options: SearchOptions
  ): Promise<EpisodicInteraction[]> {
    return await this.episodicDb.search(query, options)
  }

  /**
   * Convert EpisodicInteraction to PastInteraction interface
   */
  private convertToInterface(interaction: EpisodicInteraction): PastInteraction {
    return {
      id: interaction.id?.toString() || '',
      timestamp: interaction.timestamp,
      summary: interaction.summary,
      outcome: interaction.outcome,
      relevanceScore: interaction.relevanceScore,
      relatedEntities: interaction.relatedEntities
    }
  }

  /**
   * Load Jorge-specific knowledge from backend or cache
   */
  private async loadSemanticMemory(): Promise<void> {
    if (this.semanticCache) return

    try {
      // Try to load from backend API
      const response = await fetch('/api/concierge/knowledge-base')
      if (response.ok) {
        this.semanticCache = await response.json()
        return
      }
    } catch (error) {
      console.warn('Failed to load semantic memory from backend:', error)
    }

    // Fallback to default knowledge
    this.semanticCache = this.getDefaultSemanticMemory()
  }

  /**
   * Get semantic memory with lazy loading
   */
  private async getSemanticMemory(): Promise<PlatformKnowledge> {
    if (!this.semanticCache) {
      await this.loadSemanticMemory()
    }
    return this.semanticCache!
  }

  /**
   * Default semantic memory structure
   */
  private getDefaultSemanticMemory(): PlatformKnowledge {
    return {
      jorgeMethodology: {
        coreQuestions: [
          "Are you the owner of the property?",
          "What's your timeline for selling?",
          "What do you think your property is worth?",
          "What will you do if I can't get you that price?"
        ],
        temperatureThresholds: {
          hot: 75,
          warm: 50,
          lukewarm: 25
        },
        commissionRate: 6,
        confrontationalApproach: [
          "Direct questioning",
          "No-BS communication",
          "Motivation testing",
          "Stall-breaker techniques"
        ]
      },
      botCapabilities: {
        'jorge-seller-bot': {
          name: 'Jorge Seller Bot',
          description: 'Confrontational qualification specialist using LangGraph',
          strengths: [
            'Seller motivation testing',
            'Price negotiation',
            'Timeline qualification',
            'Stall detection and breaking'
          ],
          idealScenarios: [
            'Initial seller contact',
            'Price objection handling',
            'Motivation assessment',
            'Hot lead qualification'
          ],
          features: [
            '5-node LangGraph workflow',
            'FRS/PCS dual scoring',
            'Temperature classification',
            'GHL integration',
            'Stall-breaker automation'
          ],
          integrations: ['GoHighLevel CRM', 'Claude AI', 'WebSocket real-time']
        },
        'lead-bot': {
          name: 'Lead Bot',
          description: '3-7-30 day automation lifecycle with voice integration',
          strengths: [
            'Lead nurturing automation',
            'Voice call integration',
            'CMA delivery',
            'Follow-up sequencing'
          ],
          idealScenarios: [
            'New lead onboarding',
            'Buyer lead management',
            'Post-showing follow-up',
            'Contract-to-close nurture'
          ],
          features: [
            'Retell AI voice integration',
            'Automated CMA generation',
            'Multi-touch sequences',
            'Behavioral scoring'
          ],
          integrations: ['Retell AI', 'Zillow API', 'Email/SMS', 'Calendar scheduling']
        },
        'intent-decoder': {
          name: 'Intent Decoder',
          description: 'FRS/PCS dual scoring with ML behavioral analysis',
          strengths: [
            'Lead scoring accuracy',
            'Behavioral analysis',
            'Readiness assessment',
            'Performance analytics'
          ],
          idealScenarios: [
            'Lead prioritization',
            'Quality assessment',
            'Performance optimization',
            'Strategic routing'
          ],
          features: [
            '28-feature ML pipeline',
            'SHAP explainability',
            '95% accuracy rating',
            '42.3ms response time'
          ],
          integrations: ['Scikit-learn', 'SHAP', 'FastAPI', 'Real-time scoring']
        }
      },
      realEstateKnowledge: {
        marketTrends: [
          'Interest rate impact on buyer behavior',
          'Seasonal market patterns',
          'Inventory levels and pricing pressure',
          'Local market dynamics'
        ],
        processSteps: {
          'seller-onboarding': [
            'Initial qualification call',
            'Property valuation (CMA)',
            'Listing agreement signing',
            'Photography and marketing',
            'Showings and negotiations',
            'Contract to closing'
          ],
          'buyer-onboarding': [
            'Pre-approval verification',
            'Needs assessment',
            'Property search setup',
            'Showing coordination',
            'Offer preparation',
            'Transaction management'
          ]
        },
        commonObjections: {
          'seller-objections': [
            'Price is too low',
            'Not ready to sell yet',
            'Want to try FSBO first',
            'Commission is too high',
            'Market timing concerns'
          ],
          'buyer-objections': [
            'Price is too high',
            'Wrong location/area',
            'Needs too many repairs',
            'Can\'t afford monthly payment',
            'Want to see more options'
          ]
        },
        bestPractices: [
          'Always qualify motivation first',
          'Use CMAs to establish value',
          'Address objections with data',
          'Follow up within 24 hours',
          'Maintain consistent communication',
          'Document all interactions'
        ]
      }
    }
  }

  /**
   * Persist message to episodic memory with analysis
   */
  private async persistToEpisodicMemory(
    conversationId: string,
    message: Message,
    metadata?: {
      outcome?: 'success' | 'escalation' | 'incomplete' | 'handoff'
      relatedEntities?: string[]
    }
  ): Promise<void> {
    const summary = this.generateMessageSummary(message)
    const keywords = this.extractKeywords(message.content)
    const relatedEntities = metadata?.relatedEntities || this.extractEntities(message.content)

    const episodicEntry: EpisodicInteraction = {
      conversationId,
      message,
      timestamp: message.timestamp,
      summary,
      outcome: metadata?.outcome || 'success',
      relevanceScore: this.calculateRelevanceScore(message, keywords),
      relatedEntities,
      keywords
    }

    await this.episodicDb.storeInteraction(episodicEntry)
  }

  /**
   * Generate concise summary of message for episodic storage
   */
  private generateMessageSummary(message: Message): string {
    const content = message.content.toLowerCase()

    // Real estate intent detection
    if (content.includes('sell') || content.includes('selling')) {
      return `${message.role} discussed selling property`
    }
    if (content.includes('buy') || content.includes('buying')) {
      return `${message.role} discussed buying property`
    }
    if (content.includes('price') || content.includes('value')) {
      return `${message.role} discussed property pricing`
    }
    if (content.includes('showing') || content.includes('tour')) {
      return `${message.role} discussed property showing`
    }

    // Truncate content for generic summary
    const truncated = message.content.substring(0, 100)
    return `${message.role} message: ${truncated}${message.content.length > 100 ? '...' : ''}`
  }

  /**
   * Extract keywords for search indexing
   */
  private extractKeywords(content: string): string[] {
    const realEstateKeywords = [
      'sell', 'buy', 'property', 'house', 'home', 'price', 'value', 'listing',
      'showing', 'tour', 'offer', 'commission', 'agent', 'realtor', 'market',
      'mortgage', 'financing', 'closing', 'contract', 'negotiation'
    ]

    const words = content.toLowerCase().match(/\b\w+\b/g) || []
    return words.filter(word =>
      word.length > 3 &&
      realEstateKeywords.includes(word)
    )
  }

  /**
   * Extract entities (names, locations, etc.) from message content
   */
  private extractEntities(content: string): string[] {
    const entities: string[] = []

    // Extract potential property addresses (simple pattern)
    const addressPattern = /\b\d+\s+[A-Za-z\s]+(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Blvd|Boulevard)\b/g
    const addresses = content.match(addressPattern) || []
    entities.push(...addresses)

    // Extract price amounts
    const pricePattern = /\$[\d,]+/g
    const prices = content.match(pricePattern) || []
    entities.push(...prices)

    // Extract capitalized words (potential names/locations)
    const namePattern = /\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g
    const names = content.match(namePattern) || []
    entities.push(...names.slice(0, 3)) // Limit to first 3

    return entities
  }

  /**
   * Calculate relevance score for message based on content and keywords
   */
  private calculateRelevanceScore(message: Message, keywords: string[]): number {
    let score = 0.5 // Base score

    // Higher score for user messages (more informative)
    if (message.role === 'user') {
      score += 0.2
    }

    // Higher score for messages with real estate keywords
    score += Math.min(keywords.length * 0.1, 0.3)

    // Higher score for longer messages (more context)
    if (message.content.length > 100) {
      score += 0.1
    }

    return Math.min(score, 1.0)
  }

  /**
   * Extract lead context from related entities
   */
  private extractLeadContext(entities: string[]): LeadData | undefined {
    // This is a simplified extraction - in production would use more sophisticated NLP
    const priceEntities = entities.filter(e => e.startsWith('$'))
    const addressEntities = entities.filter(e => /\d+\s+.*(?:St|Ave|Rd|Dr|Blvd)/i.test(e))

    if (priceEntities.length > 0 || addressEntities.length > 0) {
      return {
        id: `lead_${Date.now()}`,
        name: 'Extracted Lead',
        email: '',
        phone: '',
        intent: 'selling', // Default assumption
        timeline: 'unknown',
        budget: priceEntities.length > 0 ? parseInt(priceEntities[0].replace(/[$,]/g, '')) : undefined,
        propertyType: 'residential',
        location: addressEntities[0] || 'unknown'
      }
    }

    return undefined
  }

  /**
   * Manage working memory size to prevent memory leaks
   */
  private manageWorkingMemorySize(): void {
    if (this.workingMemoryCache.size > this.MAX_WORKING_MEMORY_SIZE) {
      // Remove oldest conversations
      const conversationIds = Array.from(this.workingMemoryCache.keys())
      const sortedByActivity = conversationIds
        .map(id => ({
          id,
          lastActivity: this.workingMemoryCache.get(id)!.lastActivity
        }))
        .sort((a, b) => new Date(a.lastActivity).getTime() - new Date(b.lastActivity).getTime())

      const toRemove = sortedByActivity.slice(0, 10) // Remove oldest 10
      toRemove.forEach(item => this.workingMemoryCache.delete(item.id))
    }
  }

  /**
   * Start periodic cleanup of old episodic memories
   */
  private startPeriodicCleanup(): void {
    // Clean up every 24 hours
    setInterval(() => {
      this.cleanupOldMemories().catch(error => {
        console.warn('Memory cleanup failed:', error)
      })
    }, 24 * 60 * 60 * 1000)
  }

  /**
   * Cleanup old episodic memories (7-day retention)
   */
  async cleanupOldMemories(): Promise<void> {
    const sevenDaysAgo = Date.now() - 7 * 24 * 60 * 60 * 1000
    await this.episodicDb.deleteOlderThan(sevenDaysAgo)
  }

  /**
   * Get memory statistics for debugging/monitoring
   */
  getMemoryStats(): {
    workingMemorySize: number
    totalConversations: number
    avgMessagesPerConversation: number
  } {
    const conversations = Array.from(this.workingMemoryCache.values())
    const totalMessages = conversations.reduce((sum, conv) => sum + conv.messages.length, 0)

    return {
      workingMemorySize: this.workingMemoryCache.size,
      totalConversations: conversations.length,
      avgMessagesPerConversation: conversations.length > 0 ? totalMessages / conversations.length : 0
    }
  }
}

/**
 * IndexedDB wrapper for episodic memory
 * Handles persistent storage of conversation interactions
 */
export class EpisodicDatabase {
  private db: IDBDatabase | null = null
  private readonly DB_NAME = 'jorge-concierge-memory'
  private readonly DB_VERSION = 1
  private readonly STORE_NAME = 'interactions'

  async init(): Promise<void> {
    if (this.db) return

    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.DB_NAME, this.DB_VERSION)

      request.onerror = () => reject(request.error)
      request.onsuccess = () => {
        this.db = request.result
        resolve()
      }

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result

        // Create interactions store
        const store = db.createObjectStore(this.STORE_NAME, {
          keyPath: 'id',
          autoIncrement: true
        })

        // Create indexes for efficient searching
        store.createIndex('timestamp', 'timestamp', { unique: false })
        store.createIndex('conversationId', 'conversationId', { unique: false })
        store.createIndex('keywords', 'keywords', { unique: false, multiEntry: true })
        store.createIndex('relatedEntities', 'relatedEntities', { unique: false, multiEntry: true })
        store.createIndex('outcome', 'outcome', { unique: false })
      }
    })
  }

  async storeInteraction(interaction: EpisodicInteraction): Promise<number> {
    await this.init()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.STORE_NAME], 'readwrite')
      const store = transaction.objectStore(this.STORE_NAME)
      const request = store.add({
        ...interaction,
        timestamp: interaction.timestamp || new Date().toISOString(),
      })

      request.onsuccess = () => resolve(request.result as number)
      request.onerror = () => reject(request.error)
    })
  }

  async search(query: string, options: SearchOptions): Promise<EpisodicInteraction[]> {
    await this.init()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.STORE_NAME], 'readonly')
      const store = transaction.objectStore(this.STORE_NAME)
      const results: EpisodicInteraction[] = []

      // Use timestamp index to limit search window if specified
      let cursor: IDBRequest
      if (options.timeWindow) {
        const cutoffTime = new Date(Date.now() - options.timeWindow * 60 * 60 * 1000).toISOString()
        const range = IDBKeyRange.lowerBound(cutoffTime)
        cursor = store.index('timestamp').openCursor(range)
      } else {
        cursor = store.openCursor()
      }

      cursor.onsuccess = (event) => {
        const currentCursor = (event.target as IDBRequest).result
        if (currentCursor && results.length < options.limit) {
          const interaction: EpisodicInteraction = currentCursor.value

          // Calculate relevance score based on keyword and entity matches
          const relevance = this.calculateSearchRelevance(interaction, query)

          if (relevance >= options.minRelevance) {
            interaction.relevanceScore = relevance
            results.push(interaction)
          }

          currentCursor.continue()
        } else {
          // Sort by relevance score and return
          results.sort((a, b) => b.relevanceScore - a.relevanceScore)
          resolve(results)
        }
      }

      cursor.onerror = () => reject(cursor.error)
    })
  }

  private calculateSearchRelevance(interaction: EpisodicInteraction, query: string): number {
    const queryLower = query.toLowerCase()
    const queryWords = queryLower.split(/\s+/).filter(word => word.length > 2)

    let score = 0

    // Check keywords match
    const keywordMatches = interaction.keywords.filter(keyword =>
      queryWords.some(qWord => keyword.includes(qWord))
    ).length
    score += keywordMatches * 0.3

    // Check summary match
    if (interaction.summary.toLowerCase().includes(queryLower)) {
      score += 0.4
    }

    // Check entity match
    const entityMatches = interaction.relatedEntities.filter(entity =>
      queryWords.some(qWord => entity.toLowerCase().includes(qWord))
    ).length
    score += entityMatches * 0.2

    // Recency bonus (more recent = higher score)
    const ageInHours = (Date.now() - new Date(interaction.timestamp).getTime()) / (60 * 60 * 1000)
    const recencyBonus = Math.max(0, 1 - ageInHours / (7 * 24)) * 0.1 // Decay over 7 days
    score += recencyBonus

    return Math.min(score, 1.0)
  }

  async deleteOlderThan(timestamp: number): Promise<void> {
    await this.init()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.STORE_NAME], 'readwrite')
      const store = transaction.objectStore(this.STORE_NAME)
      const index = store.index('timestamp')

      const range = IDBKeyRange.upperBound(new Date(timestamp).toISOString())
      const request = index.openCursor(range)

      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result
        if (cursor) {
          cursor.delete()
          cursor.continue()
        } else {
          resolve()
        }
      }

      request.onerror = () => reject(request.error)
    })
  }

  async getStats(): Promise<{
    totalInteractions: number
    oldestInteraction: string | null
    newestInteraction: string | null
  }> {
    await this.init()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([this.STORE_NAME], 'readonly')
      const store = transaction.objectStore(this.STORE_NAME)

      const countRequest = store.count()
      countRequest.onsuccess = () => {
        const totalInteractions = countRequest.result

        if (totalInteractions === 0) {
          resolve({
            totalInteractions: 0,
            oldestInteraction: null,
            newestInteraction: null
          })
          return
        }

        // Get oldest and newest timestamps
        const timestampIndex = store.index('timestamp')

        const oldestRequest = timestampIndex.openCursor()
        oldestRequest.onsuccess = (event) => {
          const oldestCursor = (event.target as IDBRequest).result
          const oldestTimestamp = oldestCursor ? oldestCursor.value.timestamp : null

          const newestRequest = timestampIndex.openCursor(null, 'prev')
          newestRequest.onsuccess = (event) => {
            const newestCursor = (event.target as IDBRequest).result
            const newestTimestamp = newestCursor ? newestCursor.value.timestamp : null

            resolve({
              totalInteractions,
              oldestInteraction: oldestTimestamp,
              newestInteraction: newestTimestamp
            })
          }
        }
      }

      countRequest.onerror = () => reject(countRequest.error)
    })
  }
}