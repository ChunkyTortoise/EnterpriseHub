/**
 * Claude Concierge Streaming Chat API
 * Handles streaming conversations with Claude for the Concierge service
 *
 * Security: ANTHROPIC_API_KEY stays server-side only
 */

import { NextRequest } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'

// Initialize Claude client
const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY || '',
})

// Type for message structure
interface ClaudeMessage {
  role: 'user' | 'assistant'
  content: string
}

export async function POST(request: NextRequest) {
  try {
    // Validate API key
    if (!process.env.ANTHROPIC_API_KEY) {
      return new Response('Claude API not configured', {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      })
    }

    // Parse request body
    const {
      systemPrompt,
      messages = [],
      model = 'claude-3-5-sonnet-20241022',
      maxTokens = 4096,
      temperature = 0.7,
      stream: enableStreaming = true
    } = await request.json()

    // Validate required fields
    if (!systemPrompt || !Array.isArray(messages)) {
      return new Response('Missing required fields: systemPrompt, messages', {
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      })
    }

    // Create Claude stream
    const claudeStream = await anthropic.messages.create({
      model,
      max_tokens: maxTokens,
      temperature,
      system: systemPrompt,
      messages: messages.map((msg: ClaudeMessage) => ({
        role: msg.role,
        content: msg.content
      })) as Anthropic.MessageParam[],
      stream: enableStreaming
    })

    // Create a readable stream to pipe Claude's response
    const readable = new ReadableStream({
      async start(controller) {
        try {
          for await (const chunk of claudeStream) {
            const sseData = `data: ${JSON.stringify(chunk)}\n\n`
            controller.enqueue(new TextEncoder().encode(sseData))
          }

          // Send completion marker
          controller.enqueue(new TextEncoder().encode('data: [DONE]\n\n'))
          controller.close()
        } catch (error) {
          console.error('Claude streaming error:', error)

          // Send error as SSE
          const errorData = `data: ${JSON.stringify({
            type: 'error',
            error: error instanceof Error ? error.message : 'Streaming failed'
          })}\n\n`

          controller.enqueue(new TextEncoder().encode(errorData))
          controller.close()
        }
      }
    })

    // Return streaming response with proper headers
    return new Response(readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    })

  } catch (error) {
    console.error('Claude Concierge chat error:', error)

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