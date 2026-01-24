/**
 * Claude Concierge Context Analysis API
 * Handles platform context analysis and proactive suggestion generation
 *
 * Integrates with: MarketIntelligence, PredictiveScoring, ConversationIntelligence
 */

import { NextRequest } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'

// Initialize Claude client
const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY || '',
})

export async function POST(request: NextRequest) {
  try {
    // Validate API key
    if (!process.env.ANTHROPIC_API_KEY) {
      return new Response(JSON.stringify({
        error: 'Claude API not configured'
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      })
    }

    // Parse request body
    const {
      contextType = 'platform_analysis',
      platformState,
      userActivity,
      conversationHistory,
      leadData,
      marketData
    } = await request.json()

    // Build context-specific system prompt
    const systemPrompt = buildContextPrompt(contextType, {
      platformState,
      userActivity,
      conversationHistory,
      leadData,
      marketData
    })

    // Create analysis message based on context type
    const analysisMessage = formatAnalysisMessage(contextType, {
      platformState,
      userActivity,
      conversationHistory,
      leadData,
      marketData
    })

    // Query Claude for context analysis
    const response = await anthropic.messages.create({
      model: 'claude-3-5-haiku-20241022', // Fast model for context analysis
      max_tokens: 2048,
      system: systemPrompt,
      messages: [
        {
          role: 'user',
          content: analysisMessage
        }
      ]
    })

    // Extract content from response
    const content = response.content[0]
    if (content.type !== 'text') {
      throw new Error('Unexpected response type from Claude')
    }

    // Parse structured response
    const analysis = parseContextAnalysis(content.text, contextType)

    return new Response(JSON.stringify({
      analysis,
      contextType,
      usage: response.usage,
      timestamp: new Date().toISOString()
    }), {
      headers: { 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Claude context analysis error:', error)

    return new Response(JSON.stringify({
      error: 'Context analysis failed',
      details: error instanceof Error ? error.message : 'Unknown error'
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
  }
}

/**
 * Build context-specific system prompts
 */
function buildContextPrompt(contextType: string, data: any): string {
  const basePrompt = `You are Claude Concierge, an AI guide for Jorge's Real Estate AI Platform.

Key Capabilities:
- Jorge Seller Bot: Confrontational qualification specialist (6% commission focus)
- Lead Bot: Complete 3-7-30 day automation with voice integration
- Intent Decoder: FRS/PCS scoring with 95% accuracy
- ML Analytics: 28-feature behavioral pipeline (42.3ms response)

Your Role: Provide strategic guidance, proactive suggestions, and intelligent bot coordination.`

  switch (contextType) {
    case 'platform_analysis':
      return `${basePrompt}

Analyze the user's current platform activity and provide proactive suggestions.

Focus Areas:
- Navigation patterns and workflow optimization
- Bot utilization opportunities
- Lead qualification status and next steps
- Market timing recommendations

Return JSON with:
{
  "suggestions": [
    {
      "type": "workflow|feature|best_practice|opportunity",
      "title": "string",
      "description": "string",
      "priority": "high|medium|low",
      "action": {
        "type": "navigation|bot_start|data_update",
        "label": "string",
        "data": {}
      }
    }
  ],
  "insights": ["string array of key insights"],
  "urgency": "high|medium|low"
}`

    case 'conversation_intelligence':
      return `${basePrompt}

Analyze conversation patterns and provide coaching recommendations using Jorge's methodology.

Jorge's Core Framework:
- 4 Core Questions: motivation, timeline, decision process, price range
- FRS/PCS Dual Scoring (Financial + Psychological Commitment)
- Temperature Classification: Hot (75+), Warm (50-74), Lukewarm (25-49), Cold (<25)
- Confrontational approach targeting motivated sellers only

Return JSON analysis with coaching insights and next-step recommendations.`

    case 'predictive_scoring':
      return `${basePrompt}

Analyze lead behavior and provide progression predictions.

Scoring Factors:
- Behavioral signals (response time, engagement, questions)
- Jorge qualification data (FRS/PCS scores)
- Market factors (seasonality, inventory, rates)
- Historical performance patterns

Return JSON with probability predictions and actionable recommendations.`

    case 'market_intelligence':
      return `${basePrompt}

Analyze market conditions and provide strategic recommendations using Jorge's approach.

Market Analysis Focus:
- Inventory levels and competitive dynamics
- Pricing trends and appreciation patterns
- Seasonal factors and timing opportunities
- Interest rate impacts on buyer behavior

Return JSON with market insights and Jorge-specific messaging recommendations.`

    default:
      return basePrompt
  }
}

/**
 * Format analysis message based on context type
 */
function formatAnalysisMessage(contextType: string, data: any): string {
  switch (contextType) {
    case 'platform_analysis':
      return `Platform State: ${JSON.stringify(data.platformState || {})}
User Activity: ${JSON.stringify(data.userActivity || {})}

Analyze current activity and provide proactive suggestions for workflow optimization.`

    case 'conversation_intelligence':
      return `Conversation History: ${JSON.stringify(data.conversationHistory || [])}
Lead Data: ${JSON.stringify(data.leadData || {})}

Analyze conversation patterns and provide Jorge methodology coaching recommendations.`

    case 'predictive_scoring':
      return `Lead Data: ${JSON.stringify(data.leadData || {})}
Conversation History: ${JSON.stringify(data.conversationHistory || [])}
Market Data: ${JSON.stringify(data.marketData || {})}

Calculate lead progression predictions and provide next-step recommendations.`

    case 'market_intelligence':
      return `Market Data: ${JSON.stringify(data.marketData || {})}
Lead Context: ${JSON.stringify(data.leadData || {})}

Analyze market conditions and provide Jorge-specific strategic recommendations.`

    default:
      return `Context: ${JSON.stringify(data)}

Provide general platform analysis and recommendations.`
  }
}

/**
 * Parse structured response from Claude
 */
function parseContextAnalysis(content: string, contextType: string): any {
  try {
    // Try to parse JSON response
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      return JSON.parse(jsonMatch[0]);
    }

    // Fallback to text parsing
    return {
      summary: content,
      type: contextType,
      parseError: true
    }
  } catch (error) {
    console.warn('Failed to parse context analysis response:', error)

    return {
      summary: content,
      type: contextType,
      suggestions: [],
      parseError: true
    }
  }
}

// Handle CORS preflight
export async function OPTIONS() {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  })
}