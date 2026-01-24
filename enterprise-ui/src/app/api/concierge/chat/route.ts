/**
 * Claude Concierge Chat API Route
 * Handles streaming responses from Claude API with security proxy
 *
 * Security: API key is server-side only, never exposed to frontend
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
      messages,
      model = 'claude-3-5-sonnet-20241022',
      maxTokens = 4096,
      temperature = 0.7,
      stream = true
    } = body

    // Validate required fields
    if (!systemPrompt || !messages || !Array.isArray(messages)) {
      return NextResponse.json(
        { error: 'Missing required fields: systemPrompt and messages' },
        { status: 400 }
      )
    }

    // Validate messages format
    for (const message of messages) {
      if (!message.role || !message.content) {
        return NextResponse.json(
          { error: 'Invalid message format: role and content required' },
          { status: 400 }
        )
      }

      if (!['user', 'assistant'].includes(message.role)) {
        return NextResponse.json(
          { error: 'Invalid message role: must be user or assistant' },
          { status: 400 }
        )
      }
    }

    // Rate limiting check (basic implementation)
    const userAgent = request.headers.get('user-agent') || 'unknown'
    const clientIP = request.headers.get('x-forwarded-for') || 'unknown'

    // TODO: Implement proper rate limiting with Redis or database
    // For now, just log for monitoring
    console.log(`Concierge API request from ${clientIP} (${userAgent})`)

    // Prepare Claude API request
    const claudeRequest = {
      model,
      max_tokens: Math.min(maxTokens, 4096), // Cap max tokens
      temperature: Math.max(0, Math.min(temperature, 1)), // Clamp temperature
      system: systemPrompt,
      messages: messages.map((msg: any) => ({
        role: msg.role,
        content: String(msg.content).substring(0, 10000) // Limit content length
      })),
      stream
    }

    if (stream) {
      // Create streaming response
      const stream = await anthropic.messages.stream(claudeRequest)

      // Create readable stream for Next.js response
      const readableStream = new ReadableStream({
        async start(controller) {
          try {
            for await (const chunk of stream) {
              // Format chunk for client consumption
              const data = JSON.stringify(chunk)
              const formattedChunk = `data: ${data}\n\n`

              controller.enqueue(new TextEncoder().encode(formattedChunk))
            }

            // Send completion signal
            controller.enqueue(new TextEncoder().encode('data: [DONE]\n\n'))
            controller.close()
          } catch (error) {
            console.error('Streaming error:', error)

            // Send error to client
            const errorData = JSON.stringify({
              type: 'error',
              message: 'Streaming failed'
            })
            controller.enqueue(
              new TextEncoder().encode(`data: ${errorData}\n\n`)
            )
            controller.close()
          }
        }
      })

      return new Response(readableStream, {
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'X-Accel-Buffering': 'no' // Disable Nginx buffering
        }
      })
    } else {
      // Non-streaming response
      const response = await anthropic.messages.create(claudeRequest)

      return NextResponse.json({
        content: response.content[0]?.type === 'text'
          ? response.content[0].text
          : '',
        usage: response.usage,
        model: response.model
      })
    }

  } catch (error) {
    console.error('Claude API error:', error)

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
            { status: 429 }
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