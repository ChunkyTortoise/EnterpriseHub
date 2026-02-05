/**
 * Claude Concierge Query API - Frontend Bridge
 * Connects to the unified Claude Concierge Agent backend for direct queries
 *
 * Used for: handoff evaluation, context analysis, quick decisions
 */

import { NextRequest, NextResponse } from 'next/server'

interface QueryRequest {
  message: string
  sessionId: string
  queryType?: 'handoff_evaluation' | 'context_analysis' | 'quick_decision' | 'general'
  context?: any
}

export async function POST(request: NextRequest) {
  try {
    const body: QueryRequest = await request.json()

    // Validate required fields
    if (!body.message || !body.sessionId) {
      return NextResponse.json(
        {
          error: 'Missing required fields: message, sessionId',
          status: 'error'
        },
        { status: 400 }
      )
    }

    // Call unified Claude Concierge Agent backend chat endpoint
    // (The query endpoint reuses the chat functionality with specific context)
    const backendUrl =
      process.env.ENTERPRISE_API_BASE_URL ||
      process.env.BACKEND_URL ||
      'http://localhost:8000'

    const response = await fetch(`${backendUrl}/api/claude-concierge/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        message: body.message,
        sessionId: body.sessionId,
        context: {
          currentPage: body.context?.currentPage || 'query_interface',
          userRole: body.context?.userRole || 'agent',
          sessionId: body.sessionId,
          queryType: body.queryType || 'general',
          locationContext: body.context?.locationContext || {},
          activeLeads: body.context?.activeLeads || [],
          botStatuses: body.context?.botStatuses || {},
          userActivity: body.context?.userActivity || [],
          businessMetrics: body.context?.businessMetrics || {},
          activeProperties: body.context?.activeProperties || [],
          marketConditions: body.context?.marketConditions || {},
          priorityActions: body.context?.priorityActions || [],
          pendingNotifications: body.context?.pendingNotifications || []
        }
      })
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status ${response.status}: ${response.statusText}`)
    }

    // Get structured response from unified Claude Concierge Agent
    const conciergeResponse = await response.json()

    // Transform response to match original query API format
    return NextResponse.json({
      status: 'success',
      content: conciergeResponse.response,
      insights: conciergeResponse.insights,
      suggestions: conciergeResponse.suggestions,
      confidence: conciergeResponse.confidence,
      processingTime: conciergeResponse.processingTime,
      agentContext: conciergeResponse.agentContext,
      queryType: body.queryType || 'general',
      backend_status: 'connected',
      backend_version: 'unified_claude_concierge_agent',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Claude Concierge query error:', error)

    // Handle specific error types with appropriate responses
    if (error instanceof Error) {
      if (error.message.includes('rate_limit_exceeded') || error.message.includes('429')) {
        return NextResponse.json({
          error: 'Rate limit exceeded',
          details: 'Please try again in a moment',
          status: 'rate_limited',
          backend_status: 'rate_limited',
          timestamp: new Date().toISOString()
        }, { status: 429 })
      }

      if (error.message.includes('invalid_api_key') || error.message.includes('401')) {
        return NextResponse.json({
          error: 'Invalid API configuration',
          details: 'Authentication failed',
          status: 'auth_error',
          backend_status: 'auth_failed',
          timestamp: new Date().toISOString()
        }, { status: 401 })
      }
    }

    // Fallback response for general errors
    return NextResponse.json(
      {
        error: 'Query processing failed',
        details: error instanceof Error ? error.message : 'Unknown error',
        status: 'error',
        content: "I'm experiencing technical difficulties. Let me try to reconnect with my systems.",
        confidence: 0.0,
        processingTime: 0,
        agentContext: ['fallback_mode'],
        backend_status: 'disconnected',
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    )
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
