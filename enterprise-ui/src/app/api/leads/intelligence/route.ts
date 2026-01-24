import { NextRequest, NextResponse } from 'next/server'

interface LeadIntelligenceRequest {
  contact_id: string
  location_id: string
  analyze_type: 'intent_scoring' | 'behavioral_analysis' | 'conversation_intelligence' | 'full_analysis'
  conversation_data?: {
    messages: Array<{
      timestamp: string
      sender: 'lead' | 'agent'
      content: string
      channel: 'sms' | 'email' | 'phone' | 'chat'
    }>
  }
  lead_data?: {
    budget?: number
    timeline?: string
    preferences?: Record<string, any>
    source?: string
  }
}

interface LeadIntelligenceResponse {
  contact_id: string
  analysis_id: string
  scores: {
    intent_score: number // 0-100
    behavioral_score: number // 0-100
    engagement_score: number // 0-100
    readiness_score: number // 0-100
    overall_score: number // 0-100
  }
  classification: {
    temperature: 'hot' | 'warm' | 'cold'
    intent_category: 'buyer' | 'seller' | 'investor' | 'curious'
    urgency_level: 'immediate' | 'active' | 'passive' | 'future'
    qualification_status: 'qualified' | 'partially_qualified' | 'unqualified'
  }
  insights: {
    key_indicators: string[]
    concerns: string[]
    opportunities: string[]
    recommended_actions: string[]
  }
  ml_analysis: {
    confidence: number // 0-1
    model_version: string
    processing_time_ms: number
    feature_importance: Record<string, number>
  }
  conversation_intelligence?: {
    sentiment: 'positive' | 'neutral' | 'negative'
    emotional_indicators: string[]
    objections_detected: string[]
    buying_signals: string[]
    next_best_action: string
  }
}

export async function POST(request: NextRequest) {
  try {
    const body: LeadIntelligenceRequest = await request.json()

    // Validate required fields
    if (!body.contact_id || !body.location_id || !body.analyze_type) {
      return NextResponse.json(
        {
          error: 'Missing required fields: contact_id, location_id, analyze_type',
          status: 'error'
        },
        { status: 400 }
      )
    }

    // TODO: Replace with actual FastAPI backend call to ML analytics engine
    // const response = await fetch('http://localhost:8001/analyze_lead_intelligence', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(body)
    // })
    // const data = await response.json()

    // Mock response for development (based on actual ML pipeline specs)
    const analysisId = `intel_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

    const mockResponse: LeadIntelligenceResponse = {
      contact_id: body.contact_id,
      analysis_id: analysisId,
      scores: {
        intent_score: 82,
        behavioral_score: 75,
        engagement_score: 88,
        readiness_score: 79,
        overall_score: 81
      },
      classification: {
        temperature: 'warm',
        intent_category: 'buyer',
        urgency_level: 'active',
        qualification_status: 'qualified'
      },
      insights: {
        key_indicators: [
          'Specific budget mentioned ($400k-500k)',
          'Timeline defined (60-90 days)',
          'Active engagement in conversation',
          'Pre-approval mentioned'
        ],
        concerns: [
          'First-time homebuyer concerns',
          'Market timing uncertainty'
        ],
        opportunities: [
          'Ready for immediate showings',
          'Flexible on location within target area',
          'Strong financial position'
        ],
        recommended_actions: [
          'Schedule property showings ASAP',
          'Provide market analysis for confidence',
          'Connect with preferred lender',
          'Set up automated property alerts'
        ]
      },
      ml_analysis: {
        confidence: 0.87,
        model_version: 'v2.1.3',
        processing_time_ms: 42,
        feature_importance: {
          'budget_clarity': 0.23,
          'timeline_specificity': 0.19,
          'engagement_frequency': 0.18,
          'financial_readiness': 0.22,
          'location_flexibility': 0.12,
          'urgency_indicators': 0.06
        }
      }
    }

    // Add conversation intelligence if requested
    if (body.analyze_type === 'conversation_intelligence' || body.analyze_type === 'full_analysis') {
      mockResponse.conversation_intelligence = {
        sentiment: 'positive',
        emotional_indicators: ['excitement', 'urgency', 'trust'],
        objections_detected: ['price_concern', 'timing_uncertainty'],
        buying_signals: ['asking_about_financing', 'requesting_showings', 'timeline_urgency'],
        next_best_action: 'Schedule immediate property viewing for top 3 matches'
      }
    }

    return NextResponse.json({
      status: 'success',
      data: mockResponse,
      backend_status: 'mock_response',
      processing_time_ms: 42,
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Lead Intelligence API Error:', error)

    return NextResponse.json(
      {
        error: 'Internal server error',
        status: 'error',
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    )
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const contact_id = searchParams.get('contact_id')
  const analysis_id = searchParams.get('analysis_id')

  if (!contact_id && !analysis_id) {
    return NextResponse.json(
      { error: 'Missing contact_id or analysis_id parameter', status: 'error' },
      { status: 400 }
    )
  }

  // TODO: Get analysis history from FastAPI backend
  // const response = await fetch(`http://localhost:8001/intelligence_history/${contact_id || analysis_id}`)

  // Mock response for development
  return NextResponse.json({
    status: 'success',
    data: {
      contact_id: contact_id || 'mock_contact',
      analysis_history: [
        {
          analysis_id: 'intel_001',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          overall_score: 78,
          temperature: 'warm',
          confidence: 0.85
        },
        {
          analysis_id: 'intel_002',
          timestamp: new Date().toISOString(),
          overall_score: 81,
          temperature: 'warm',
          confidence: 0.87
        }
      ],
      trend_analysis: {
        score_trend: 'increasing',
        engagement_trend: 'stable',
        readiness_trend: 'improving'
      }
    },
    backend_status: 'mock_response',
    timestamp: new Date().toISOString()
  })
}