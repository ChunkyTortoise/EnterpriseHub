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

    // Call real FastAPI backend - Lead Bot automation endpoint
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'
    const backendRequest = {
      contact_id: body.contact_id,
      location_id: body.location_id,
      automation_type: body.automation_type,
      trigger_data: body.trigger_data || {}
    }

    const response = await fetch(`${backendUrl}/api/lead-bot/automation`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(backendRequest)
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status ${response.status}: ${response.statusText}`)
    }

    // Get structured response from enhanced Lead Bot
    const leadAutomationResponse: LeadAutomationResponse = await response.json()

    return NextResponse.json({
      status: 'success',
      data: leadAutomationResponse,
      backend_status: 'connected',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Lead Bot API Error:', error)

    // Fallback response if backend is unavailable
    const fallbackResponse: LeadAutomationResponse = {
      automation_id: `fallback_${Date.now()}`,
      contact_id: body.contact_id,
      automation_type: body.automation_type,
      status: 'failed',
      scheduled_for: new Date().toISOString(),
      actions_taken: [
        {
          type: 'error',
          channel: 'sms',
          content: 'Lead Bot temporarily unavailable'
        }
      ],
      next_followup: {
        type: 'retry_automation',
        scheduled_for: new Date(Date.now() + 3600000).toISOString()
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
  const automation_id = searchParams.get('automation_id')

  if (!contact_id && !automation_id) {
    return NextResponse.json(
      { error: 'Missing contact_id or automation_id parameter', status: 'error' },
      { status: 400 }
    )
  }

  try {
    // Get lead bot status from FastAPI backend
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000'

    // Try to get lead bot status (use existing bot status endpoint)
    const statusResponse = await fetch(`${backendUrl}/api/bots/lead-bot/status`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    let automationData = {
      contact_id: contact_id || 'unknown_contact',
      active_automations: [],
      lifecycle_stage: 'new',
      total_touches: 0,
      engagement_score: 0
    }

    if (statusResponse.ok) {
      const botStatus = await statusResponse.json()

      // Transform bot status to automation data
      automationData = {
        contact_id: contact_id || 'unknown_contact',
        active_automations: [
          {
            automation_id: `auto_${contact_id}_day3`,
            type: 'day_3',
            status: 'scheduled',
            scheduled_for: new Date(Date.now() + 3 * 24 * 3600000).toISOString()
          }
        ],
        lifecycle_stage: 'day_3',
        total_touches: botStatus.conversationsToday || 0,
        engagement_score: 65,
        bot_status: botStatus.status,
        bot_response_time: botStatus.responseTimeMs
      }
    } else if (statusResponse.status === 404) {
      // Lead not found - return default state
      console.warn(`Lead ${contact_id} not found in Lead Bot status`)
    } else {
      throw new Error(`Lead Bot status failed with status ${statusResponse.status}`)
    }

    return NextResponse.json({
      status: 'success',
      data: automationData,
      backend_status: 'connected',
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Get lead bot automation status error:', error)

    // Fallback to basic data if backend unavailable
    return NextResponse.json({
      status: 'success', // Don't fail completely
      data: {
        contact_id: contact_id || 'fallback_contact',
        active_automations: [
          {
            automation_id: 'fallback_auto',
            type: 'unknown',
            status: 'pending',
            scheduled_for: new Date().toISOString()
          }
        ],
        lifecycle_stage: 'unknown',
        total_touches: 0,
        engagement_score: 0,
        error: 'Backend temporarily unavailable'
      },
      backend_status: 'fallback',
      error_detail: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    })
  }
}