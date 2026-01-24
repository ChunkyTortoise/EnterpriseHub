/**
 * Vector Search Engine for Claude Concierge
 * Semantic similarity search for episodic memory and conversation patterns
 *
 * Implements: PersonaAB-9 #62 (Semantic Memory), #73 (Pattern Recognition)
 */

export interface VectorSearchResult {
  id: string
  content: string
  similarity: number
  metadata: {
    timestamp: string
    conversationId?: string
    leadId?: string
    botId?: string
    outcome?: string
    tags?: string[]
  }
  context?: {
    before?: string
    after?: string
  }
}

export interface SemanticQuery {
  text: string
  filters?: {
    timeRange?: { start: string; end: string }
    botId?: string
    leadId?: string
    outcome?: 'success' | 'failure' | 'pending'
    tags?: string[]
    minSimilarity?: number
  }
  limit?: number
  includeContext?: boolean
}

export interface ConversationPattern {
  pattern: string
  frequency: number
  successRate: number
  avgOutcome: number
  examples: VectorSearchResult[]
  recommendations: string[]
}

export interface EpisodicMemoryEntry {
  id: string
  embedding: number[]
  content: string
  timestamp: string
  metadata: Record<string, any>
  indexed: boolean
}

export class VectorSearchEngine {
  private memoryStore: Map<string, EpisodicMemoryEntry> = new Map()
  private indexedEntries: EpisodicMemoryEntry[] = []
  private readonly embeddingDimension = 384  // Sentence transformers dimension
  private isInitialized = false

  /**
   * Initialize the vector search engine
   */
  async initialize(): Promise<void> {
    try {
      // In production, this would initialize:
      // - Sentence transformer model or API
      // - Vector database connection (Pinecone, Weaviate, etc.)
      // - Load existing embeddings from IndexedDB

      await this.loadExistingMemories()
      this.isInitialized = true

      console.log('Vector search engine initialized')
    } catch (error) {
      console.error('Vector search initialization failed:', error)
      this.isInitialized = false
    }
  }

  /**
   * Add new memory entry with automatic embedding
   */
  async addMemory(
    id: string,
    content: string,
    metadata: Record<string, any>
  ): Promise<void> {
    if (!this.isInitialized) {
      await this.initialize()
    }

    try {
      // Generate embedding for content
      const embedding = await this.generateEmbedding(content)

      const entry: EpisodicMemoryEntry = {
        id,
        embedding,
        content,
        timestamp: new Date().toISOString(),
        metadata,
        indexed: true
      }

      this.memoryStore.set(id, entry)
      this.indexedEntries.push(entry)

      // In production, persist to IndexedDB
      await this.persistMemory(entry)

    } catch (error) {
      console.error('Failed to add memory:', error)
    }
  }

  /**
   * Search for similar memories using semantic similarity
   */
  async searchSimilar(query: SemanticQuery): Promise<VectorSearchResult[]> {
    if (!this.isInitialized) {
      await this.initialize()
    }

    try {
      // Generate query embedding
      const queryEmbedding = await this.generateEmbedding(query.text)

      // Calculate similarities with all indexed memories
      let results: VectorSearchResult[] = []

      for (const entry of this.indexedEntries) {
        const similarity = this.calculateCosineSimilarity(queryEmbedding, entry.embedding)

        // Apply minimum similarity threshold
        if (similarity < (query.filters?.minSimilarity || 0.3)) {
          continue
        }

        // Apply filters
        if (!this.passesFilters(entry, query.filters)) {
          continue
        }

        // Add context if requested
        const context = query.includeContext ?
          await this.getContext(entry.id) : undefined

        results.push({
          id: entry.id,
          content: entry.content,
          similarity,
          metadata: entry.metadata,
          context
        })
      }

      // Sort by similarity and apply limit
      results = results
        .sort((a, b) => b.similarity - a.similarity)
        .slice(0, query.limit || 10)

      return results

    } catch (error) {
      console.error('Vector search failed:', error)
      return []
    }
  }

  /**
   * Find conversation patterns using clustering and analysis
   */
  async findConversationPatterns(
    type: 'successful_closes' | 'objection_handling' | 'qualification_techniques' | 'stall_breakers'
  ): Promise<ConversationPattern[]> {
    try {
      const patterns: ConversationPattern[] = []

      // Get relevant memories based on type
      const relevantMemories = await this.getRelevantMemoriesForPattern(type)

      // Cluster similar conversations
      const clusters = this.clusterSimilarMemories(relevantMemories)

      // Analyze each cluster for patterns
      for (const cluster of clusters) {
        const pattern = await this.analyzeClusterPattern(cluster, type)
        if (pattern.frequency > 2) {  // Only include patterns that appear multiple times
          patterns.push(pattern)
        }
      }

      // Sort by success rate and frequency
      return patterns.sort((a, b) =>
        (b.successRate * b.frequency) - (a.successRate * a.frequency)
      )

    } catch (error) {
      console.error('Pattern analysis failed:', error)
      return []
    }
  }

  /**
   * Get similar successful conversations for coaching
   */
  async getSimilarSuccessfulConversations(
    currentConversation: string,
    limit: number = 5
  ): Promise<VectorSearchResult[]> {
    const query: SemanticQuery = {
      text: currentConversation,
      filters: {
        outcome: 'success',
        minSimilarity: 0.5
      },
      limit,
      includeContext: true
    }

    return await this.searchSimilar(query)
  }

  /**
   * Find examples of handling specific objections
   */
  async findObjectionHandlingExamples(objection: string): Promise<VectorSearchResult[]> {
    const query: SemanticQuery = {
      text: `objection: ${objection}`,
      filters: {
        tags: ['objection_handling'],
        minSimilarity: 0.4
      },
      limit: 8,
      includeContext: true
    }

    return await this.searchSimilar(query)
  }

  /**
   * Get coaching recommendations based on conversation similarity
   */
  async getCoachingRecommendations(
    currentConversation: string,
    currentStage: string
  ): Promise<{
    similarSuccesses: VectorSearchResult[]
    avoidPatterns: VectorSearchResult[]
    recommendations: string[]
  }> {
    // Find similar successful conversations
    const similarSuccesses = await this.getSimilarSuccessfulConversations(currentConversation)

    // Find patterns to avoid (similar failed conversations)
    const avoidQuery: SemanticQuery = {
      text: currentConversation,
      filters: {
        outcome: 'failure',
        minSimilarity: 0.4
      },
      limit: 3
    }
    const avoidPatterns = await this.searchSimilar(avoidQuery)

    // Generate recommendations
    const recommendations = this.generateRecommendationsFromPatterns(
      similarSuccesses,
      avoidPatterns,
      currentStage
    )

    return {
      similarSuccesses,
      avoidPatterns,
      recommendations
    }
  }

  /**
   * Generate text embedding using sentence transformers (simplified)
   */
  private async generateEmbedding(text: string): Promise<number[]> {
    // In production, this would use:
    // - Sentence-BERT model (local or API)
    // - OpenAI embeddings API
    // - Anthropic embeddings (when available)
    // - Local transformer.js implementation

    // For now, create a simple hash-based embedding (not production-ready)
    return this.createSimpleEmbedding(text)
  }

  /**
   * Create a simple embedding for demonstration (NOT for production)
   */
  private createSimpleEmbedding(text: string): number[] {
    const words = text.toLowerCase().split(/\s+/)
    const embedding = new Array(this.embeddingDimension).fill(0)

    // Simple word hashing to dimensions
    for (const word of words) {
      const hash = this.simpleHash(word)
      const index = Math.abs(hash) % this.embeddingDimension
      embedding[index] += 1
    }

    // Normalize
    const magnitude = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0))
    return magnitude > 0 ? embedding.map(val => val / magnitude) : embedding
  }

  /**
   * Simple string hash function
   */
  private simpleHash(str: string): number {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + char
      hash = hash & hash  // Convert to 32-bit integer
    }
    return hash
  }

  /**
   * Calculate cosine similarity between two vectors
   */
  private calculateCosineSimilarity(a: number[], b: number[]): number {
    if (a.length !== b.length) return 0

    let dotProduct = 0
    let magnitudeA = 0
    let magnitudeB = 0

    for (let i = 0; i < a.length; i++) {
      dotProduct += a[i] * b[i]
      magnitudeA += a[i] * a[i]
      magnitudeB += b[i] * b[i]
    }

    magnitudeA = Math.sqrt(magnitudeA)
    magnitudeB = Math.sqrt(magnitudeB)

    if (magnitudeA === 0 || magnitudeB === 0) return 0

    return dotProduct / (magnitudeA * magnitudeB)
  }

  /**
   * Check if memory entry passes filters
   */
  private passesFilters(
    entry: EpisodicMemoryEntry,
    filters?: SemanticQuery['filters']
  ): boolean {
    if (!filters) return true

    // Time range filter
    if (filters.timeRange) {
      const timestamp = new Date(entry.timestamp).getTime()
      const start = new Date(filters.timeRange.start).getTime()
      const end = new Date(filters.timeRange.end).getTime()
      if (timestamp < start || timestamp > end) return false
    }

    // Bot ID filter
    if (filters.botId && entry.metadata.botId !== filters.botId) {
      return false
    }

    // Lead ID filter
    if (filters.leadId && entry.metadata.leadId !== filters.leadId) {
      return false
    }

    // Outcome filter
    if (filters.outcome && entry.metadata.outcome !== filters.outcome) {
      return false
    }

    // Tags filter
    if (filters.tags && filters.tags.length > 0) {
      const entryTags = entry.metadata.tags || []
      if (!filters.tags.some(tag => entryTags.includes(tag))) {
        return false
      }
    }

    return true
  }

  /**
   * Get conversation context around a memory entry
   */
  private async getContext(entryId: string): Promise<{ before?: string; after?: string }> {
    const entry = this.memoryStore.get(entryId)
    if (!entry || !entry.metadata.conversationId) {
      return {}
    }

    // Find entries from the same conversation before and after this one
    const conversationEntries = Array.from(this.memoryStore.values())
      .filter(e => e.metadata.conversationId === entry.metadata.conversationId)
      .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())

    const currentIndex = conversationEntries.findIndex(e => e.id === entryId)

    return {
      before: currentIndex > 0 ? conversationEntries[currentIndex - 1].content : undefined,
      after: currentIndex < conversationEntries.length - 1 ? conversationEntries[currentIndex + 1].content : undefined
    }
  }

  /**
   * Load existing memories from persistence layer
   */
  private async loadExistingMemories(): Promise<void> {
    // In production, load from IndexedDB
    // For now, create some sample memories for Jorge's methodology

    const sampleMemories = [
      {
        id: 'successful_close_1',
        content: 'Owner confirmed, timeline is 30 days, price realistic at $485K, commitment strong',
        metadata: {
          outcome: 'success',
          botId: 'jorge-seller-bot',
          tags: ['qualification', 'hot_lead', 'quick_close'],
          frs: 85,
          pcs: 90
        }
      },
      {
        id: 'objection_handling_1',
        content: 'Commission too high objection handled with value demonstration and ROI calculation',
        metadata: {
          outcome: 'success',
          botId: 'jorge-seller-bot',
          tags: ['objection_handling', 'commission', 'value_prop']
        }
      },
      {
        id: 'stall_breaker_1',
        content: 'Think about it stall broken with consequence question: What happens if you wait 6 months?',
        metadata: {
          outcome: 'success',
          botId: 'jorge-seller-bot',
          tags: ['stall_breaker', 'confrontational', 'timeline']
        }
      }
    ]

    for (const memory of sampleMemories) {
      await this.addMemory(memory.id, memory.content, memory.metadata)
    }
  }

  /**
   * Persist memory to storage
   */
  private async persistMemory(entry: EpisodicMemoryEntry): Promise<void> {
    // In production, save to IndexedDB
    // For now, just keep in memory
    console.debug('Persisting memory entry:', entry.id)
  }

  /**
   * Get relevant memories for pattern analysis
   */
  private async getRelevantMemoriesForPattern(
    type: 'successful_closes' | 'objection_handling' | 'qualification_techniques' | 'stall_breakers'
  ): Promise<EpisodicMemoryEntry[]> {
    const tagMap = {
      successful_closes: ['hot_lead', 'quick_close', 'closed'],
      objection_handling: ['objection_handling', 'commission', 'price_objection'],
      qualification_techniques: ['qualification', 'jorge_questions', 'frs', 'pcs'],
      stall_breakers: ['stall_breaker', 'confrontational', 'timeline']
    }

    const relevantTags = tagMap[type]

    return this.indexedEntries.filter(entry => {
      const entryTags = entry.metadata.tags || []
      return relevantTags.some(tag => entryTags.includes(tag))
    })
  }

  /**
   * Cluster similar memories for pattern analysis
   */
  private clusterSimilarMemories(memories: EpisodicMemoryEntry[]): EpisodicMemoryEntry[][] {
    // Simple clustering based on similarity threshold
    const clusters: EpisodicMemoryEntry[][] = []
    const used = new Set<string>()

    for (const memory of memories) {
      if (used.has(memory.id)) continue

      const cluster = [memory]
      used.add(memory.id)

      // Find similar memories
      for (const other of memories) {
        if (used.has(other.id)) continue

        const similarity = this.calculateCosineSimilarity(memory.embedding, other.embedding)
        if (similarity > 0.6) {  // High similarity threshold for clustering
          cluster.push(other)
          used.add(other.id)
        }
      }

      if (cluster.length > 1) {
        clusters.push(cluster)
      }
    }

    return clusters
  }

  /**
   * Analyze cluster to extract pattern
   */
  private async analyzeClusterPattern(
    cluster: EpisodicMemoryEntry[],
    type: string
  ): Promise<ConversationPattern> {
    const successes = cluster.filter(entry => entry.metadata.outcome === 'success')
    const total = cluster.length

    // Extract common elements
    const commonWords = this.extractCommonWords(cluster.map(entry => entry.content))
    const pattern = commonWords.slice(0, 5).join(' ')

    return {
      pattern,
      frequency: total,
      successRate: total > 0 ? successes.length / total : 0,
      avgOutcome: this.calculateAverageOutcome(cluster),
      examples: cluster.slice(0, 3).map(entry => ({
        id: entry.id,
        content: entry.content,
        similarity: 1.0,
        metadata: entry.metadata
      })),
      recommendations: this.generatePatternRecommendations(pattern, successes.length / total)
    }
  }

  /**
   * Extract common words from a set of texts
   */
  private extractCommonWords(texts: string[]): string[] {
    const wordCounts = new Map<string, number>()

    for (const text of texts) {
      const words = text.toLowerCase().split(/\s+/)
      for (const word of words) {
        if (word.length > 3) {  // Skip short words
          wordCounts.set(word, (wordCounts.get(word) || 0) + 1)
        }
      }
    }

    // Return words that appear in at least half the texts
    const threshold = Math.ceil(texts.length / 2)
    return Array.from(wordCounts.entries())
      .filter(([_, count]) => count >= threshold)
      .sort((a, b) => b[1] - a[1])
      .map(([word, _]) => word)
  }

  /**
   * Calculate average outcome score for cluster
   */
  private calculateAverageOutcome(cluster: EpisodicMemoryEntry[]): number {
    const scores = cluster
      .map(entry => entry.metadata.frs || entry.metadata.pcs || 50)
      .filter(score => score > 0)

    return scores.length > 0 ? scores.reduce((sum, score) => sum + score, 0) / scores.length : 50
  }

  /**
   * Generate recommendations from patterns
   */
  private generatePatternRecommendations(pattern: string, successRate: number): string[] {
    const recommendations: string[] = []

    if (successRate > 0.8) {
      recommendations.push(`High success pattern: Use "${pattern}" approach when possible`)
    }

    if (successRate > 0.6) {
      recommendations.push(`Effective technique: Incorporate elements of "${pattern}"`)
    } else {
      recommendations.push(`Review and refine: "${pattern}" shows mixed results`)
    }

    return recommendations
  }

  /**
   * Generate coaching recommendations from similar conversations
   */
  private generateRecommendationsFromPatterns(
    successes: VectorSearchResult[],
    failures: VectorSearchResult[],
    currentStage: string
  ): string[] {
    const recommendations: string[] = []

    // Analyze successful patterns
    if (successes.length > 0) {
      recommendations.push('Based on similar successful conversations:')

      const successfulApproaches = successes
        .slice(0, 3)
        .map(result => `"${result.content.substring(0, 100)}..."`)

      recommendations.push(...successfulApproaches)
    }

    // Warn about failure patterns
    if (failures.length > 0) {
      recommendations.push('Avoid these patterns that led to failures:')

      const failurePatterns = failures
        .slice(0, 2)
        .map(result => `Avoid: "${result.content.substring(0, 80)}..."`)

      recommendations.push(...failurePatterns)
    }

    // Stage-specific recommendations
    if (currentStage === 'qualification') {
      recommendations.push('Focus on Jorge\'s 4 core questions for qualification')
    } else if (currentStage === 'objection_handling') {
      recommendations.push('Use confrontational approach with data backing')
    }

    return recommendations
  }
}