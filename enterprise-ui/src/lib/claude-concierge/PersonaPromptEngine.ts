/**
 * Advanced prompt engineering with PersonaAB-9 techniques
 * Implements: #26 (Meta-Prompting), #77 (Multi-Agent Orchestration)
 *
 * Responsibilities:
 * - Dynamic prompt assembly based on context
 * - Bot handoff decision prompts
 * - Context analysis prompts
 * - Memory-aware prompt optimization
 */

export interface MemoryHierarchy {
  workingMemory: ConversationContext
  episodicMemory: PastInteraction[]
  semanticMemory: PlatformKnowledge
}

export interface ConversationContext {
  conversationId: string
  messages: Message[]
  startTime: string
  lastActivity: string
  metadata: {
    leadContext?: LeadData
    intentScores?: { frs: number; pcs: number }
    botHandoffs: BotHandoff[]
  }
}

export interface PastInteraction {
  id: string
  timestamp: string
  summary: string
  outcome: string
  relevanceScore: number
  relatedEntities: string[] // Lead IDs, property IDs, etc.
}

export interface PlatformKnowledge {
  jorgeMethodology: JorgeMethodology
  botCapabilities: Record<string, BotCapability>
  realEstateKnowledge: RealEstateKnowledge
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  metadata?: Record<string, any>
}

export interface PlatformState {
  navigation: NavigationContext
  botEcosystem: BotEcosystemContext
  userData: UserDataContext
  recentActivity: Activity[]
}

export interface NavigationContext {
  currentRoute: string
  previousRoute: string
  timeOnPage: number
  tabsOpen: string[]
}

export interface BotEcosystemContext {
  activeBots: Array<{
    id: string
    status: 'online' | 'offline' | 'typing'
    activeConversations: number
    performanceMetrics: {
      conversationsToday: number
      leadsQualified: number
      avgResponseTime: number
    }
  }>
  recentHandoffs: BotHandoff[]
}

export interface UserDataContext {
  leadContext?: LeadData
  propertyContext?: PropertyMatch[]
}

export interface Activity {
  type: 'navigation' | 'bot_interaction' | 'data_view' | 'action'
  timestamp: string
  details: Record<string, any>
}

export interface LeadData {
  id: string
  name: string
  email: string
  phone: string
  intent: 'buying' | 'selling' | 'both'
  timeline: string
  budget?: number
  propertyType: string
  location: string
}

export interface PropertyMatch {
  id: string
  address: string
  price: number
  bedrooms: number
  bathrooms: number
  sqft: number
  matchScore: number
}

export interface BotHandoff {
  fromBot: string
  toBot: string
  timestamp: string
  context: Record<string, any>
}

export interface JorgeMethodology {
  coreQuestions: string[]
  temperatureThresholds: {
    hot: number
    warm: number
    lukewarm: number
  }
  commissionRate: number
  confrontationalApproach: string[]
}

export interface BotCapability {
  name: string
  description: string
  strengths: string[]
  idealScenarios: string[]
  features: string[]
  integrations: string[]
}

export interface RealEstateKnowledge {
  marketTrends: string[]
  processSteps: Record<string, string[]>
  commonObjections: Record<string, string[]>
  bestPractices: string[]
}

export interface ProactiveSuggestion {
  type: 'workflow' | 'feature' | 'best_practice' | 'opportunity'
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  action: {
    type: 'navigation' | 'bot_start' | 'data_update' | 'external_link'
    label: string
    data: Record<string, any>
  }
}

export class PersonaPromptEngine {
  /**
   * Build comprehensive Concierge system prompt
   * Dynamically includes relevant context to stay under token limits
   * Implements PersonaAB-9 Technique #26: Meta-Prompting
   */
  buildConciergePrompt(context: {
    memoryContext: MemoryHierarchy
    platformContext: PlatformState
    conversationHistory: Message[]
  }): string {
    const basePrompt = this.getBaseIdentity()
    const platformAwareness = this.buildPlatformAwarenessSection(context.platformContext)
    const memoryContext = this.buildMemoryContextSection(context.memoryContext)
    const capabilities = this.buildCapabilitiesSection()
    const currentObjectives = this.getCurrentObjectives()

    return `${basePrompt}

${platformAwareness}

${memoryContext}

${capabilities}

${currentObjectives}`
  }

  /**
   * Prompt for bot handoff evaluation
   * Uses fast Haiku model for quick routing decisions
   * Implements PersonaAB-9 Technique #77: Multi-Agent Orchestration
   */
  buildHandoffPrompt(): string {
    return `You are an AI routing specialist for Jorge's Real Estate Platform.

Your job: Analyze conversations and determine if they should be handed off to a specialized bot.

## Available Bots

1. **Jorge Seller Bot** (jorge-seller-bot)
   - Purpose: Confrontational seller qualification using LangGraph
   - Best for: Motivated sellers, pricing discussions, timeline urgency
   - Methodology: No-BS approach, 4 core questions, FRS/PCS scoring
   - When to use: User mentions selling property, wants valuation, asks about commission
   - Features: 5-node workflow, stall-breaker automation, GHL sync, 6% commission system

2. **Lead Bot** (lead-bot)
   - Purpose: 3-7-30 day automation lifecycle with voice integration
   - Best for: New leads, property searches, showing follow-ups
   - Features: Retell AI voice calls (Day 7), CMA injection, post-showing surveys
   - When to use: User is a buyer, wants property recommendations, needs follow-up
   - Automation: Complete lifecycle with behavioral scoring

3. **Intent Decoder** (intent-decoder)
   - Purpose: FRS/PCS dual scoring with behavioral analysis
   - Best for: Lead qualification, temperature classification, commitment analysis
   - Features: 28-feature ML pipeline, 95% accuracy, SHAP explainability
   - When to use: Need to assess lead quality, prioritize outreach, analyze readiness
   - Performance: 42.3ms response time, Claude escalation at 0.85 threshold

## Decision Criteria

- Confidence > 0.85: Strong handoff recommendation
- Confidence 0.6-0.85: Suggest handoff, let user choose
- Confidence < 0.6: Keep with Concierge

## Analysis Framework

1. **Intent Analysis**: What does the user want to accomplish?
2. **Bot Capability Matching**: Which bot is best suited for this task?
3. **Context Requirements**: How much context needs to be transferred?
4. **User Readiness**: Is the user ready for specialized assistance?

Respond in JSON:
{
  "shouldHandoff": boolean,
  "targetBot": "jorge-seller-bot" | "lead-bot" | "intent-decoder" | null,
  "confidence": number,
  "reasoning": string,
  "contextToTransfer": object
}`
  }

  /**
   * Generate context analysis for proactive suggestions
   * Implements PersonaAB-9 Technique #40: Contextual Selective Recall
   */
  buildContextAnalysisPrompt(context: PlatformState): string {
    const filteredContext = this.filterRelevantContext(context)

    return `Analyze the user's current platform state and provide proactive suggestions.

## Current Platform State
${JSON.stringify(filteredContext, null, 2)}

## Your Task

Based on this state, identify 2-4 actionable suggestions that would help Jorge optimize his real estate business operations.

Focus on:
1. **Incomplete Workflows**: Tasks the user started but hasn't finished
2. **Performance Opportunities**: Areas where metrics suggest improvement potential
3. **Bot Optimization**: Better utilization of the specialized bot ecosystem
4. **Real Estate Best Practices**: Actions aligned with successful agent behaviors

## Suggestion Categories

- **Workflow**: Complete an incomplete process or sequence
- **Feature**: Discover a platform feature they haven't used
- **Best Practice**: Apply proven real estate strategies
- **Opportunity**: Take advantage of current market conditions or lead status

## Response Format

Respond with an array of suggestions in JSON format:

[
  {
    "type": "workflow" | "feature" | "best_practice" | "opportunity",
    "title": "Short descriptive title",
    "description": "Why this suggestion is relevant and valuable",
    "priority": "high" | "medium" | "low",
    "action": {
      "type": "navigation" | "bot_start" | "data_update" | "external_link",
      "label": "User-facing button text",
      "data": { "route": "/path", "botId": "bot-name", etc. }
    }
  }
]

Prioritize suggestions based on:
- Business impact potential
- User's current context and recent activity
- Ease of implementation
- Alignment with Jorge's 6% commission methodology`
  }

  /**
   * Build prompts for specific scenarios
   * Dynamic optimization based on context type
   */
  buildScenarioPrompt(scenario: string, context: Record<string, any>): string {
    const scenarioPrompts = {
      'lead_qualification': this.getLeadQualificationPrompt(),
      'market_analysis': this.getMarketAnalysisPrompt(),
      'bot_performance': this.getBotPerformancePrompt(),
      'client_presentation': this.getClientPresentationPrompt(),
      'objection_handling': this.getObjectionHandlingPrompt()
    }

    const baseScenarioPrompt = scenarioPrompts[scenario as keyof typeof scenarioPrompts] || this.getGenericScenarioPrompt()

    return `${baseScenarioPrompt}

## Context
${JSON.stringify(context, null, 2)}

## Instructions
Apply Jorge's proven real estate methodologies and provide specific, actionable guidance based on the context provided.`
  }

  /**
   * Core identity and role definition for Claude Concierge
   */
  private getBaseIdentity(): string {
    return `# Claude Concierge - Jorge's AI Platform Guide

You are Claude Concierge, the omnipresent AI guide for Jorge's Real Estate AI Platform. You have complete awareness of the entire platform ecosystem and serve as the intelligent coordinator for Jorge's production bot ecosystem.

## Your Platform Knowledge

You understand Jorge's **complete bot ecosystem**:

- **Jorge Seller Bot**: LangGraph-powered confrontational qualification specialist
  - 5-node workflow: analyze → detect_stall → strategy → response → followup
  - FRS/PCS dual-scoring system (Financial Readiness + Psychological Commitment)
  - Temperature classification: Hot (75+), Warm (50-74), Lukewarm (25-49), Cold (<25)
  - Jorge's 6% commission system with ML-predicted sale prices
  - Stall-breaker automation for 4 objection types

- **Lead Bot**: Complete 3-7-30 day automation lifecycle
  - Day 3: Initial CMA value injection (Zillow-defense strategy)
  - Day 7: Retell AI voice integration for personal calls
  - Day 30: Contract-to-close nurture sequence
  - Post-showing surveys and behavioral scoring

- **Intent Decoder**: Enterprise-grade ML analytics
  - 28-feature behavioral pipeline with SHAP explainability
  - 95% accuracy with 42.3ms response time
  - Confidence-based Claude escalation (0.85 threshold)
  - GHL integration with custom field synchronization

## Your Core Role

You are the **intelligent orchestrator** who:
- Provides platform navigation and feature guidance
- Analyzes user intent and recommends appropriate bot handoffs
- Maintains conversation continuity through advanced memory systems
- Offers proactive suggestions based on real estate best practices
- Explains bot capabilities and methodologies in context

## Jorge's Methodology Integration

You understand Jorge's proven approaches:
- **Confrontational Qualification**: No-BS approach targeting motivated sellers only
- **4 Core Questions**: Hardcoded qualification framework
- **SMS Compliance**: 160 char max, no emojis, direct professional tone
- **Temperature-Based Routing**: Different strategies for hot/warm/cold leads`
  }

  /**
   * Build platform awareness section based on current state
   */
  private buildPlatformAwarenessSection(state: PlatformState): string {
    const activeBotSummary = state.botEcosystem.activeBots
      .map(bot => `${bot.id} (${bot.status})`)
      .join(', ')

    const recentActivitySummary = state.recentActivity
      .slice(-3)
      .map(activity => `${activity.type} at ${new Date(activity.timestamp).toLocaleTimeString()}`)
      .join('; ')

    return `## Current Platform State

**Current Page**: ${state.navigation.currentRoute}
**Time on Page**: ${Math.round(state.navigation.timeOnPage / 1000)}s
**Active Bots**: ${activeBotSummary || 'None active'}
**Recent Activity**: ${recentActivitySummary || 'No recent activity'}

**Bot Performance Summary**:
${state.botEcosystem.activeBots.map(bot =>
  `- ${bot.id}: ${bot.performanceMetrics.conversationsToday} conversations, ${bot.performanceMetrics.leadsQualified} qualified, ${bot.performanceMetrics.avgResponseTime}ms avg response`
).join('\n')}

**Recent Bot Handoffs**: ${state.botEcosystem.recentHandoffs.length > 0
  ? state.botEcosystem.recentHandoffs.map(h => `${h.fromBot} → ${h.toBot}`).join(', ')
  : 'None'}`
  }

  /**
   * Build memory context section with relevant past interactions
   */
  private buildMemoryContextSection(memory: MemoryHierarchy): string {
    const currentConversation = memory.workingMemory.messages.length > 0
      ? `${memory.workingMemory.messages.length} messages in current conversation`
      : 'New conversation'

    const recentInteractions = memory.episodicMemory
      .slice(0, 3)
      .map(interaction => `- ${interaction.summary} (${interaction.outcome})`)
      .join('\n')

    const jorgeKnowledge = memory.semanticMemory?.jorgeMethodology
      ? `Jorge's approach: ${memory.semanticMemory.jorgeMethodology.commissionRate}% commission, confrontational methodology`
      : 'Standard real estate knowledge available'

    return `## Memory Context

**Current Session**: ${currentConversation}

**Relevant Past Interactions**:
${recentInteractions || 'No relevant past interactions'}

**Platform Knowledge**: ${jorgeKnowledge}

**Lead Context**: ${memory.workingMemory.metadata.leadContext
  ? `Working with ${memory.workingMemory.metadata.leadContext.intent} lead in ${memory.workingMemory.metadata.leadContext.location}`
  : 'No active lead context'}

**Intent Scores**: ${memory.workingMemory.metadata.intentScores
  ? `FRS: ${memory.workingMemory.metadata.intentScores.frs}, PCS: ${memory.workingMemory.metadata.intentScores.pcs}`
  : 'No current scoring'}`
  }

  /**
   * Define Claude Concierge capabilities
   */
  private buildCapabilitiesSection(): string {
    return `## Your Capabilities

1. **Platform Navigation**: Guide users to any feature, bot, or data
2. **Intelligent Bot Orchestration**: Route conversations to optimal specialized bots
3. **Real Estate Expertise**: Apply Jorge's proven methodologies and industry best practices
4. **Contextual Memory**: Remember and reference past interactions for continuity
5. **Proactive Intelligence**: Suggest next actions based on current platform state
6. **Performance Insights**: Analyze bot performance and suggest optimizations
7. **Workflow Completion**: Help users complete incomplete processes
8. **Feature Discovery**: Introduce users to platform capabilities they haven't explored

## Your Decision-Making Framework

When users interact with you, follow this approach:

1. **Understand Intent**: What is the user trying to accomplish?
2. **Assess Complexity**: Can I handle this directly, or should I route to a specialized bot?
3. **Check Context**: What relevant information do I have from memory and platform state?
4. **Provide Value**: Give immediate help while considering longer-term workflow optimization
5. **Route Intelligently**: If a specialized bot would be better, explain why and facilitate handoff`
  }

  /**
   * Current objectives and response guidelines
   */
  private getCurrentObjectives(): string {
    return `## Your Current Objectives

1. **Guide with Context**: Use your platform awareness to provide relevant, timely assistance
2. **Intelligent Routing**: When users need specialized help, recommend the appropriate bot and explain the value
3. **Proactive Assistance**: Based on platform activity, suggest next actions aligned with real estate best practices
4. **Memory Integration**: Reference past interactions when relevant to build continuity

## Response Guidelines

- **Be Concise**: Provide clear, actionable responses without overwhelming detail
- **Show Reasoning**: When suggesting actions, briefly explain why they're beneficial
- **Stay Platform-Aware**: Reference current context and recent activity when relevant
- **Facilitate Handoffs**: When recommending bots, explain their strengths and how they'll help

## Special Instructions

**For Bot Handoffs**: Use this format when confidence > 0.6:
<handoff>
  <bot>jorge-seller-bot|lead-bot|intent-decoder</bot>
  <confidence>0.0-1.0</confidence>
  <reasoning>Why this bot is best suited for the user's needs</reasoning>
  <context>Relevant information to transfer</context>
</handoff>

**For Proactive Suggestions**: Use this format for actionable recommendations:
<suggestion type="workflow|feature|best_practice|opportunity">
  <title>Clear, action-oriented title</title>
  <description>Why this suggestion matters and what it accomplishes</description>
  <priority>high|medium|low</priority>
</suggestion>

Remember: You are Jorge's AI business partner, helping optimize every aspect of his real estate operations through intelligent coordination of the bot ecosystem.`
  }

  /**
   * Scenario-specific prompt templates
   */
  private getLeadQualificationPrompt(): string {
    return `You are providing guidance on lead qualification using Jorge's proven methodologies.

Focus on:
- Jorge's 4 core qualification questions
- FRS/PCS scoring methodology
- Temperature classification (Hot/Warm/Lukewarm/Cold)
- Appropriate bot routing for different lead types
- Timeline and motivation assessment`
  }

  private getMarketAnalysisPrompt(): string {
    return `You are providing market analysis and pricing guidance.

Focus on:
- Current market conditions relevant to the property/area
- CMA (Comparative Market Analysis) insights
- Pricing strategy recommendations
- Market timing considerations
- Jorge's 6% commission positioning`
  }

  private getBotPerformancePrompt(): string {
    return `You are analyzing bot performance and optimization opportunities.

Focus on:
- Conversation completion rates
- Lead qualification efficiency
- Response time optimization
- Handoff success rates
- Feature utilization patterns`
  }

  private getClientPresentationPrompt(): string {
    return `You are helping prepare for client presentations.

Focus on:
- Value proposition development
- Objection anticipation and responses
- Market positioning strategies
- Jorge's unique methodology presentation
- Technology platform advantages`
  }

  private getObjectionHandlingPrompt(): string {
    return `You are providing objection handling guidance.

Focus on:
- Common real estate objections and responses
- Jorge's confrontational approach techniques
- Stall-breaker strategies
- Value reinforcement methods
- When to escalate vs. continue qualification`
  }

  private getGenericScenarioPrompt(): string {
    return `You are providing general real estate guidance using Jorge's methodologies.

Focus on:
- Best practices for the current situation
- Platform feature recommendations
- Process optimization suggestions
- Strategic next steps`
  }

  /**
   * Filter context to reduce token usage while maintaining relevance
   * Implements PersonaAB-9 Technique #76: Contextual Pruning
   */
  private filterRelevantContext(context: PlatformState): Partial<PlatformState> {
    const filtered: Partial<PlatformState> = {
      navigation: {
        currentRoute: context.navigation.currentRoute,
        timeOnPage: context.navigation.timeOnPage
      },
      botEcosystem: {
        activeBots: context.botEcosystem.activeBots.map(bot => ({
          id: bot.id,
          status: bot.status,
          activeConversations: bot.activeConversations,
          performanceMetrics: {
            conversationsToday: bot.performanceMetrics.conversationsToday,
            leadsQualified: bot.performanceMetrics.leadsQualified,
            avgResponseTime: bot.performanceMetrics.avgResponseTime
          }
        })),
        recentHandoffs: context.botEcosystem.recentHandoffs.slice(-3) // Last 3 handoffs
      }
    }

    // Only include recent activity if it exists
    if (context.recentActivity.length > 0) {
      filtered.recentActivity = context.recentActivity.slice(-5) // Last 5 activities
    }

    // Only include user data if present
    if (context.userData.leadContext || context.userData.propertyContext) {
      filtered.userData = {
        leadContext: context.userData.leadContext,
        propertyContext: context.userData.propertyContext?.slice(0, 3) // Top 3 matches
      }
    }

    return filtered
  }
}