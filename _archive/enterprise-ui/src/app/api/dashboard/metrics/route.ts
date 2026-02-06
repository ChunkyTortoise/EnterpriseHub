import { NextRequest, NextResponse } from 'next/server'

interface DashboardMetricsRequest {
  location_id?: string
  date_range?: {
    start: string
    end: string
  }
  metric_types?: Array<'bot_performance' | 'lead_metrics' | 'conversion_rates' | 'revenue_tracking'>
  real_time?: boolean
}

interface DashboardMetricsResponse {
  location_id?: string
  timestamp: string
  real_time_status: boolean

  // Bot Performance Metrics
  bot_performance: {
    jorge_seller_bot: {
      conversations_today: number
      qualified_sellers: number
      hot_leads: number
      completion_rate: number // percentage
      avg_response_time_ms: number
      q1_q4_conversion_rate: number
    }
    lead_bot: {
      active_sequences: number
      day_3_completion_rate: number
      day_7_call_success_rate: number
      day_30_reengagement_rate: number
      retell_ai_call_minutes: number
    }
    intent_decoder: {
      analyses_today: number
      accuracy_rate: number // 95% target
      avg_processing_time_ms: number
      confidence_distribution: Record<string, number>
    }
  }

  // Lead Flow Metrics
  lead_metrics: {
    new_leads_today: number
    qualified_leads: number
    hot_warm_cold_distribution: {
      hot: number
      warm: number
      cold: number
    }
    conversion_funnel: {
      total_inquiries: number
      qualified: number
      showings_scheduled: number
      offers_made: number
      contracts_signed: number
    }
    source_breakdown: Record<string, number>
  }

  // Revenue Tracking
  revenue_tracking: {
    jorge_commission_rate: number // 6%
    potential_revenue_pipeline: number
    closed_deals_this_month: number
    avg_deal_size: number
    commission_earned_ytd: number
    deals_in_pipeline: Array<{
      contact_id: string
      property_value: number
      estimated_close_date: string
      probability: number
      commission_amount: number
    }>
  }

  // System Health
  system_health: {
    redis_status: 'healthy' | 'degraded' | 'down'
    ghl_api_status: 'connected' | 'limited' | 'disconnected'
    claude_api_status: 'active' | 'limited' | 'down'
    database_status: 'operational' | 'slow' | 'down'
    last_health_check: string
    uptime_percentage: number
  }
}

export async function POST(request: NextRequest) {
  try {
    const body: DashboardMetricsRequest = await request.json()

    // TODO: Replace with actual FastAPI backend call
    // const response = await fetch('http://localhost:8001/dashboard_metrics', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(body)
    // })
    // const data = await response.json()

    // Mock response for development (realistic Jorge bot metrics)
    const mockResponse: DashboardMetricsResponse = {
      location_id: body.location_id || 'loc_001',
      timestamp: new Date().toISOString(),
      real_time_status: body.real_time || false,

      bot_performance: {
        jorge_seller_bot: {
          conversations_today: 23,
          qualified_sellers: 8,
          hot_leads: 3,
          completion_rate: 67.2, // 67.2% complete Q1-Q4
          avg_response_time_ms: 1847,
          q1_q4_conversion_rate: 34.8 // Jorge's confrontational approach
        },
        lead_bot: {
          active_sequences: 45,
          day_3_completion_rate: 89.2,
          day_7_call_success_rate: 72.1,
          day_30_reengagement_rate: 43.5,
          retell_ai_call_minutes: 267
        },
        intent_decoder: {
          analyses_today: 89,
          accuracy_rate: 95.3, // Matches Jorge's 95% target
          avg_processing_time_ms: 42, // Matches Jorge's 42.3ms spec
          confidence_distribution: {
            'high': 67.2,
            'medium': 23.8,
            'low': 9.0
          }
        }
      },

      lead_metrics: {
        new_leads_today: 31,
        qualified_leads: 18,
        hot_warm_cold_distribution: {
          hot: 5,
          warm: 13,
          cold: 13
        },
        conversion_funnel: {
          total_inquiries: 31,
          qualified: 18,
          showings_scheduled: 12,
          offers_made: 6,
          contracts_signed: 2
        },
        source_breakdown: {
          'facebook_ads': 12,
          'google_ads': 8,
          'zillow_leads': 6,
          'referrals': 3,
          'website_direct': 2
        }
      },

      revenue_tracking: {
        jorge_commission_rate: 6.0, // Jorge's 6% commission rate
        potential_revenue_pipeline: 847500, // $8.47M pipeline * 6% * probability
        closed_deals_this_month: 4,
        avg_deal_size: 425000,
        commission_earned_ytd: 178000,
        deals_in_pipeline: [
          {
            contact_id: 'hot_seller_001',
            property_value: 450000,
            estimated_close_date: '2026-02-15',
            probability: 0.85,
            commission_amount: 27000
          },
          {
            contact_id: 'warm_seller_002',
            property_value: 380000,
            estimated_close_date: '2026-03-01',
            probability: 0.65,
            commission_amount: 22800
          },
          {
            contact_id: 'hot_seller_003',
            property_value: 525000,
            estimated_close_date: '2026-02-28',
            probability: 0.92,
            commission_amount: 31500
          }
        ]
      },

      system_health: {
        redis_status: 'healthy',
        ghl_api_status: 'connected',
        claude_api_status: 'active',
        database_status: 'operational',
        last_health_check: new Date().toISOString(),
        uptime_percentage: 99.7
      }
    }

    return NextResponse.json({
      status: 'success',
      data: mockResponse,
      backend_status: 'mock_response',
      cache_duration_seconds: body.real_time ? 5 : 300, // 5sec for real-time, 5min for standard
      timestamp: new Date().toISOString()
    })

  } catch (error) {
    console.error('Dashboard Metrics API Error:', error)

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
  const metric_type = searchParams.get('metric_type')
  const location_id = searchParams.get('location_id')

  // Simple GET request for basic metrics
  const basicMetrics = {
    status: 'success',
    data: {
      summary: {
        active_conversations: 23,
        qualified_leads_today: 8,
        hot_leads: 3,
        system_status: 'operational'
      },
      jorge_performance: {
        qualification_rate: 67.2,
        avg_response_time: '1.8s',
        hot_lead_conversion: 34.8
      }
    },
    backend_status: 'mock_response',
    timestamp: new Date().toISOString()
  }

  return NextResponse.json(basicMetrics)
}