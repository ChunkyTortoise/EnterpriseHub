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

    // TODO: Replace with actual FastAPI backend call
    // const response = await fetch('http://localhost:8002/process_seller_message', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(body)
    // })
    // const data = await response.json()

    // Mock response for development (remove when FastAPI is ready)
    const mockResponse: SellerChatResponse = {
      response_message: "Look, I'm not here to waste time. What condition is the house in? Be honest - does it need major repairs, minor fixes, or is it move-in ready?",
      seller_temperature: 'cold',
      questions_answered: 1,
      qualification_complete: false,
      actions_taken: [
        { type: 'add_tag', tag: 'seller_cold' },
        { type: 'update_custom_field', field: 'seller_temperature', value: 'cold' }
      ],
      next_steps: 'Continue Q1-Q4 qualification - 3 questions remaining',
      analytics: {
        seller_temperature: 'cold',
        questions_answered: 1,
        qualification_progress: '1/4',
        qualification_complete: false,
        property_condition: 'unknown',
        price_expectation: null,
        motivation: null,
        urgency: null
      }
    }

    return NextResponse.json({
      status: 'success',
      data: mockResponse,
      backend_status: 'mock_response',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Jorge Seller Bot API Error:', error)

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

  if (!contact_id) {
    return NextResponse.json(
      { error: 'Missing contact_id parameter', status: 'error' },
      { status: 400 }
    )
  }

  // TODO: Get seller state from FastAPI backend
  // const response = await fetch(`http://localhost:8002/seller_state/${contact_id}`)

  // Mock response for development
  return NextResponse.json({
    status: 'success',
    data: {
      contact_id,
      current_question: 1,
      questions_answered: 0,
      qualification_complete: false,
      seller_temperature: 'cold'
    },
    backend_status: 'mock_response',
    timestamp: new Date().toISOString()
  })
}