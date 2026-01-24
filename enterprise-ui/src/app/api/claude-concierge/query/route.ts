/**
 * Claude Concierge Direct Query API
 * Handles direct (non-streaming) queries to Claude for routing and analysis
 *
 * Used for: handoff evaluation, context analysis, quick decisions
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
      systemPrompt,
      message,
      model = 'claude-3-5-sonnet-20241022',
      maxTokens = 1024
    } = await request.json()

    // Validate required fields
    if (!systemPrompt || !message) {
      return new Response(JSON.stringify({
        error: 'Missing required fields: systemPrompt, message'
      }), {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      })
    }

    // Query Claude directly
    const response = await anthropic.messages.create({
      model,
      max_tokens: maxTokens,
      system: systemPrompt,
      messages: [
        {
          role: 'user' as const,
          content: message
        }
      ] as Anthropic.MessageParam[]
    })

    // Extract content from response
    const content = response.content[0]
    if (content.type !== 'text') {
      throw new Error('Unexpected response type from Claude')
    }

    // Return the response content
    return new Response(JSON.stringify({
      content: content.text,
      usage: response.usage,
      model: response.model
    }), {
      headers: { 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Claude Concierge query error:', error)

    // Handle specific Claude API errors
    if (error instanceof Error) {
      if (error.message.includes('rate_limit_exceeded')) {
        return new Response(JSON.stringify({
          error: 'Rate limit exceeded',
          details: 'Please try again in a moment'
        }), {
          status: 429,
          headers: { 'Content-Type': 'application/json' }
        })
      }

      if (error.message.includes('invalid_api_key')) {
        return new Response(JSON.stringify({
          error: 'Invalid API key'
        }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' }
        })
      }
    }

    return new Response(JSON.stringify({
      error: 'Claude API request failed',
      details: error instanceof Error ? error.message : 'Unknown error'
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    })
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