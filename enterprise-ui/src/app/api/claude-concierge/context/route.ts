/**
 * Claude Concierge Context API - Frontend Bridge
 * Connects to the unified Claude Concierge Agent backend for context analysis
 *
 * Provides platform context analysis and proactive suggestion generation
 */

import { NextRequest, NextResponse } from 'next/server'

interface ContextRequest {
  sessionId: string
  contextType?: 'platform_analysis' | 'conversation_intelligence' | 'predictive_scoring' | 'market_intelligence'
  platformState?: any
  userActivity?: any[]
  conversationHistory?: any[]
  leadData?: any
  marketData?: any
}

export async function POST(request: NextRequest) {
  try {
    const body: ContextRequest = await request.json()

    // Validate required fields
    if (!body.sessionId) {
      return NextResponse.json(
        {
          error: 'Missing required field: sessionId',
          status: 'error'
        },
        { status: 400 }
      )
    }

    // For POST requests (context analysis), use appropriate analysis endpoint based on contextType
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    let endpoint = '/api/claude-concierge/analyze/platform' // Default

    switch (body.contextType) {
      case 'platform_analysis':
        endpoint = '/api/claude-concierge/analyze/platform'
        break
      case 'conversation_intelligence':
        endpoint = '/api/claude-concierge/analyze/coordination'
        break
      case 'predictive_scoring':
        endpoint = '/api/claude-concierge/analyze/platform'
        break
      case 'market_intelligence':
        endpoint = '/api/claude-concierge/analyze/platform'
        break
    }

    const response = await fetch(`${backendUrl}${endpoint}`, {
      method: 'GET', // These are analysis endpoints that return structured data
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status ${response.status}: ${response.statusText}`)
    }

    const analysis = await response.json()

    return NextResponse.json({
      status: 'success',
      analysis,
      contextType: body.contextType || 'platform_analysis',
      backend_status: 'connected',
      backend_version: 'unified_claude_concierge_agent',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Claude context analysis error:', error)

    // Fallback response if backend is unavailable
    const fallbackAnalysis = {
      summary: 'Context analysis temporarily unavailable. Platform monitoring continues in background.',
      type: 'fallback',
      suggestions: [],
      insights: ['Backend connection issue detected'],
      urgency: 'low',
      parseError: false
    }

    return NextResponse.json(
      {
        error: 'Context analysis failed',
        status: 'error',
        analysis: fallbackAnalysis,
        backend_status: 'disconnected',
        error_detail: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  try {
    // Handle GET requests for context retrieval
    const { searchParams } = new URL(request.url)
    const sessionId = searchParams.get('sessionId')

    if (!sessionId) {
      return NextResponse.json(
        { error: 'Missing sessionId parameter', status: 'error' },
        { status: 400 }
      )
    }

    // Get context from unified backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'

    const response = await fetch(`${backendUrl}/api/claude-concierge/context/${sessionId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status ${response.status}: ${response.statusText}`)
    }

    const contextData = await response.json()

    return NextResponse.json({
      status: 'success',
      data: contextData,
      backend_status: 'connected',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Get context error:', error)

    // Fallback context if backend unavailable
    return NextResponse.json({
      status: 'success',
      data: {
        sessionId: new URL(request.url).searchParams.get('sessionId') || 'fallback',
        context: {
          currentPage: 'unknown',
          userRole: 'agent',
          sessionId: 'fallback',
          error: 'Backend temporarily unavailable'
        },
        insights: [],
        suggestions: []
      },
      backend_status: 'fallback',
      error_detail: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    })
  }
}

// Handle CORS preflight
export async function OPTIONS() {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  })
}