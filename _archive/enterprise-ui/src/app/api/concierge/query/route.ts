/**
 * Claude Concierge Query API Route
 * Handles non-streaming Claude API requests for quick analysis
 * Used for: handoff evaluations, context analysis, routing decisions
 */

import { NextRequest, NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'

// Initialize Claude client with server-side API key
const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
})

export async function POST(request: NextRequest) {
  try {
    // Validate API key is configured
    if (!process.env.ANTHROPIC_API_KEY) {
      return NextResponse.json(
        { error: 'Claude API key not configured' },
        { status: 500 }
      )
    }

    // Parse request body
    const body = await request.json()
    const {
      systemPrompt,
      message,
      model = 'claude-3-5-haiku-20241022', // Default to fast model for queries
      maxTokens = 1024,
      temperature = 0
    } = body

    // Validate required fields
    if (!systemPrompt || !message) {
      return NextResponse.json(
        { error: 'Missing required fields: systemPrompt and message' },
        { status: 400 }
      )
    }

    // Validate content length (prevent abuse)
    if (systemPrompt.length > 20000 || message.length > 5000) {
      return NextResponse.json(
        { error: 'Content too long. System prompt max 20k chars, message max 5k chars.' },
        { status: 400 }
      )
    }

    // Rate limiting check
    const clientIP = request.headers.get('x-forwarded-for') || 'unknown'
    console.log(`Concierge query from ${clientIP}`)

    // Prepare Claude API request
    const claudeRequest = {
      model,
      max_tokens: Math.min(maxTokens, 2048), // Cap for quick queries
      temperature: Math.max(0, Math.min(temperature, 0.3)), // Low temperature for analysis
      system: systemPrompt,
      messages: [
        {
          role: 'user' as const,
          content: String(message)
        }
      ]
    }

    // Make Claude API request
    const response = await anthropic.messages.create(claudeRequest)

    // Extract text content
    const content = response.content[0]?.type === 'text'
      ? response.content[0].text
      : ''

    return NextResponse.json({
      content,
      usage: response.usage,
      model: response.model,
      responseTime: Date.now() // Add timestamp for performance monitoring
    })

  } catch (error) {
    console.error('Claude query error:', error)

    // Handle specific Claude API errors
    if (error instanceof Anthropic.APIError) {
      switch (error.status) {
        case 400:
          return NextResponse.json(
            { error: 'Invalid request format', details: error.message },
            { status: 400 }
          )
        case 401:
          return NextResponse.json(
            { error: 'Authentication failed' },
            { status: 401 }
          )
        case 429:
          return NextResponse.json(
            { error: 'Rate limit exceeded. Please try again later.' },
            { status: 429,
              headers: {
                'Retry-After': '60' // Suggest retry after 60 seconds
              }
            }
          )
        case 500:
        case 503:
          return NextResponse.json(
            { error: 'Claude service temporarily unavailable' },
            { status: 503 }
          )
        default:
          return NextResponse.json(
            { error: 'Claude API error', details: error.message },
            { status: error.status || 500 }
          )
      }
    }

    // Handle network or other errors
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}

// Handle preflight OPTIONS request for CORS
export async function OPTIONS(request: NextRequest) {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  })
}