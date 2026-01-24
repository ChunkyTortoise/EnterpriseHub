import { NextRequest, NextResponse } from 'next/server'

interface LeadAutomationRequest {
  contact_id: string
  location_id: string
  automation_type: 'day_3' | 'day_7' | 'day_30' | 'post_showing' | 'contract_to_close'
  trigger_data?: {
    showing_date?: string
    property_id?: string
    feedback?: string
    [key: string]: any
  }
}

interface LeadAutomationResponse {
  automation_id: string
  contact_id: string
  automation_type: string
  status: 'scheduled' | 'sent' | 'completed' | 'failed'
  scheduled_for: string
  actions_taken: Array<{
    type: string
    channel: 'sms' | 'email' | 'voice_call'
    content?: string
    scheduled_time?: string
  }>
  next_followup?: {
    type: string
    scheduled_for: string
  }
}

export async function POST(request: NextRequest) {
  try {
    const body: LeadAutomationRequest = await request.json()

    // Validate required fields
    if (!body.contact_id || !body.location_id || !body.automation_type) {
      return NextResponse.json(
        {
          error: 'Missing required fields: contact_id, location_id, automation_type',
          status: 'error'
        },
        { status: 400 }
      )
    }

    // TODO: Replace with actual FastAPI backend call
    // const response = await fetch('http://localhost:8001/trigger_automation', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(body)
    // })
    // const data = await response.json()

    // Mock response for development
    const automationId = `auto_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const scheduledTime = new Date(Date.now() + 3600000).toISOString() // 1 hour from now

    const mockResponse: LeadAutomationResponse = {
      automation_id: automationId,
      contact_id: body.contact_id,
      automation_type: body.automation_type,
      status: 'scheduled',
      scheduled_for: scheduledTime,
      actions_taken: [
        {
          type: 'sms_sequence',
          channel: 'sms',
          content: `Hi! Jorge here. Following up on your home search. Found some great options that match your criteria. Ready to schedule showings?`,
          scheduled_time: scheduledTime
        }
      ],
      next_followup: {
        type: 'day_7_voice_call',
        scheduled_for: new Date(Date.now() + 7 * 24 * 3600000).toISOString()
      }
    }

    // Add specific logic based on automation type
    switch (body.automation_type) {
      case 'day_7':
        mockResponse.actions_taken.push({
          type: 'retell_voice_call',
          channel: 'voice_call',
          scheduled_time: scheduledTime
        })
        break
      case 'post_showing':
        mockResponse.actions_taken.push({
          type: 'feedback_survey',
          channel: 'sms',
          content: 'How did the showing go? Any thoughts on the property?'
        })
        break
    }

    return NextResponse.json({
      status: 'success',
      data: mockResponse,
      backend_status: 'mock_response',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Lead Bot API Error:', error)

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
  const automation_id = searchParams.get('automation_id')

  if (!contact_id && !automation_id) {
    return NextResponse.json(
      { error: 'Missing contact_id or automation_id parameter', status: 'error' },
      { status: 400 }
    )
  }

  // TODO: Get automation status from FastAPI backend
  // const response = await fetch(`http://localhost:8001/automation_status/${automation_id || contact_id}`)

  // Mock response for development
  return NextResponse.json({
    status: 'success',
    data: {
      contact_id: contact_id || 'mock_contact',
      active_automations: [
        {
          automation_id: 'auto_123',
          type: 'day_3',
          status: 'completed',
          completed_at: new Date().toISOString()
        },
        {
          automation_id: 'auto_124',
          type: 'day_7',
          status: 'scheduled',
          scheduled_for: new Date(Date.now() + 24 * 3600000).toISOString()
        }
      ],
      lifecycle_stage: 'day_7',
      total_touches: 3,
      engagement_score: 75
    },
    backend_status: 'mock_response',
    timestamp: new Date().toISOString()
  })
}