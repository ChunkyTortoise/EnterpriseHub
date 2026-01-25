import { NextRequest, NextResponse } from 'next/server'

interface SellerChatRequest {
  contact_id: string
  location_id: string
  message: string
  contact_info?: {
    name?: string
    phone?: string
    email?: string
  }
}

interface SellerChatResponse {
  response_message: string
  seller_temperature: 'hot' | 'warm' | 'cold'
  questions_answered: number
  qualification_complete: boolean
  actions_taken: Array<{
    type: string
    [key: string]: any
  }>
  next_steps: string
  analytics: {
    seller_temperature: string
    questions_answered: number
    qualification_progress: string
    qualification_complete: boolean
    [key: string]: any
  }
}

export async function POST(request: NextRequest) {
  try {
    const body: SellerChatRequest = await request.json()

    // Validate required fields
    if (!body.contact_id || !body.location_id || !body.message) {
      return NextResponse.json(
        {
          error: 'Missing required fields: contact_id, location_id, message',
          status: 'error'
        },
        { status: 400 }
      )
    }

    // Call unified Jorge Seller Bot backend with enterprise features
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'

    const response = await fetch(`${backendUrl}/api/jorge-seller/process`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({
        contact_id: body.contact_id,
        location_id: body.location_id,
        message: body.message,
        contact_info: body.contact_info
      })
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status ${response.status}: ${response.statusText}`)
    }

    // Get structured response from unified Jorge bot
    const sellerResponse: SellerChatResponse = await response.json()

    return NextResponse.json({
      status: 'success',
      data: sellerResponse,
      backend_status: 'connected',
      backend_version: 'unified_enterprise_jorge',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Jorge Seller Bot API Error:', error)

    // Fallback response if backend is unavailable
    const fallbackResponse: SellerChatResponse = {
      response_message: "I'm experiencing technical difficulties connecting to my systems. Let me get Jorge on the line for you directly.",
      seller_temperature: 'cold',
      questions_answered: 0,
      qualification_complete: false,
      actions_taken: [
        { type: 'add_tag', tag: 'technical_issue' },
        { type: 'update_custom_field', field: 'needs_manual_followup', value: 'true' }
      ],
      next_steps: 'Manual follow-up required - backend connection failed',
      analytics: {
        seller_temperature: 'cold',
        questions_answered: 0,
        qualification_progress: '0/4',
        qualification_complete: false,
        backend_error: error instanceof Error ? error.message : 'Unknown error',
        fallback_mode: true
      }
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

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const contact_id = searchParams.get('contact_id')

  if (!contact_id) {
    return NextResponse.json(
      { error: 'Missing contact_id parameter', status: 'error' },
      { status: 400 }
    )
  }

  try {
    // Get seller state from FastAPI backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'

    // Try to get intent analysis first (this gives us FRS/PCS scores and classification)
    const intentResponse = await fetch(`${backendUrl}/api/intent-decoder/${contact_id}/score`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    let sellerData = {
      contact_id,
      current_question: 1,
      questions_answered: 0,
      qualification_complete: false,
      seller_temperature: 'cold'
    }

    if (intentResponse.ok) {
      const intentData = await intentResponse.json()

      // Transform intent analysis to seller state
      sellerData = {
        contact_id,
        current_question: Math.min(intentData.frsScore > 50 ? 3 : 1, 4),
        questions_answered: intentData.frsScore > 25 ? 1 : 0,
        qualification_complete: intentData.frsScore > 75 && intentData.pcsScore > 75,
        seller_temperature: intentData.temperature,
        frs_score: intentData.frsScore,
        pcs_score: intentData.pcsScore,
        classification: intentData.classification,
        next_best_action: intentData.nextBestAction,
        processing_time_ms: intentData.processingTimeMs
      }
    } else if (intentResponse.status === 404) {
      // Lead not found - return default state
      console.warn(`Lead ${contact_id} not found in intent analysis`)
    } else {
      throw new Error(`Intent analysis failed with status ${intentResponse.status}`)
    }

    return NextResponse.json({
      status: 'success',
      data: sellerData,
      backend_status: 'connected',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Get seller state error:', error)

    // Fallback to basic state if backend unavailable
    return NextResponse.json({
      status: 'success', // Don't fail completely
      data: {
        contact_id,
        current_question: 1,
        questions_answered: 0,
        qualification_complete: false,
        seller_temperature: 'unknown',
        error: 'Backend temporarily unavailable'
      },
      backend_status: 'fallback',
      error_detail: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    })
  }
}