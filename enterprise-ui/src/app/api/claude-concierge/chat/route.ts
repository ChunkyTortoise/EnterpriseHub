/**
 * Claude Concierge Chat API - Frontend Bridge
 * Connects to the unified Claude Concierge Agent backend
 *
 * Provides omnipresent AI guidance with platform-wide agent coordination
 */

import { NextRequest, NextResponse } from 'next/server'

interface ChatRequest {
  message: string
  sessionId: string
  context: {
    currentPage: string
    userRole?: string
    locationContext?: any
    activeLeads?: any[]
    botStatuses?: any
    userActivity?: any[]
    businessMetrics?: any
    activeProperties?: any[]
    marketConditions?: any
    priorityActions?: any[]
    pendingNotifications?: any[]
  }
}

interface ConciergeResponse {
  response: string
  insights?: Array<{
    category: string
    title: string
    value: string
    trend: 'up' | 'down' | 'stable'
    trendValue: number
    description: string
    timestamp: string
  }>
  suggestions?: Array<{
    id: string
    type: string
    title: string
    description: string
    impact: string
    confidence: number
    actionable: boolean
    estimatedBenefit?: string
    relatedAgents: string[]
    priority: string
    createdAt: string
  }>
  actions?: any[]
  confidence: number
  processingTime: number
  agentContext: string[]
}

export async function POST(request: NextRequest) {
  try {
    const body: ChatRequest = await request.json()

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

    // Call unified Claude Concierge Agent backend
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
          currentPage: body.context?.currentPage || 'unknown',
          userRole: body.context?.userRole || 'agent',
          sessionId: body.sessionId,
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
    const conciergeResponse: ConciergeResponse = await response.json()

    return NextResponse.json({
      status: 'success',
      data: conciergeResponse,
      backend_status: 'connected',
      backend_version: 'unified_claude_concierge_agent',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Claude Concierge chat error:', error)

    // Fallback response if backend is unavailable
    const fallbackResponse: ConciergeResponse = {
      response: "I'm temporarily experiencing some connectivity issues. Let me get back to you in a moment with my full platform intelligence.",
      insights: [],
      suggestions: [],
      actions: [],
      confidence: 0.5,
      processingTime: 0,
      agentContext: ['fallback_mode']
    }

    return NextResponse.json(
      {
        error: 'Backend connection failed',
        status: 'error',
        data: fallbackResponse,
        backend_status: 'disconnected',
        error_detail: error instanceof Error ? error.message : 'Unknown error',
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
