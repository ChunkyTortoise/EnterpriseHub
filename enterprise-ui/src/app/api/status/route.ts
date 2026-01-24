/**
 * System Status Endpoint for Jorge's Real Estate AI Platform
 * Detailed system status for monitoring dashboards
 */

import { NextRequest, NextResponse } from 'next/server'

interface SystemStatusResponse {
  platform: {
    name: string
    version: string
    environment: string
    deployment_id: string
    build_time: string
    commit_hash: string
  }
  services: {
    jorge_seller_bot: {
      status: 'active' | 'idle' | 'error'
      last_activity: string | null
      conversations_today: number
      success_rate: number
    }
    lead_bot: {
      status: 'active' | 'idle' | 'error'
      last_activity: string | null
      automations_running: number
      success_rate: number
    }
    intent_decoder: {
      status: 'active' | 'idle' | 'error'
      last_activity: string | null
      analyses_today: number
      accuracy_rate: number
    }
    realtime_coordination: {
      status: 'connected' | 'disconnected' | 'degraded'
      active_connections: number
      last_heartbeat: string | null
    }
  }
  performance: {
    frontend: {
      page_load_time_ms: number
      api_response_time_ms: number
      websocket_latency_ms: number | null
      error_rate: number
    }
    backend: {
      available: boolean
      response_time_ms: number | null
      queue_size: number
      active_requests: number
    }
  }
  business_metrics: {
    leads_processed_today: number
    qualifications_completed: number
    automations_triggered: number
    revenue_opportunities: number
    conversion_rate: number
  }
  alerts: Array<{
    severity: 'info' | 'warning' | 'error' | 'critical'
    message: string
    timestamp: string
    component: string
  }>
}

export async function GET(request: NextRequest): Promise<NextResponse<SystemStatusResponse>> {
  try {
    const currentTime = new Date().toISOString()

    // Platform information
    const platform = {
      name: "Jorge's Real Estate AI Platform",
      version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      deployment_id: process.env.VERCEL_GIT_COMMIT_SHA?.substring(0, 7) || 'local',
      build_time: process.env.NEXT_PUBLIC_BUILD_TIME || currentTime,
      commit_hash: process.env.VERCEL_GIT_COMMIT_SHA || 'unknown'
    }

    // Service status (in production, these would be real metrics)
    const services = {
      jorge_seller_bot: {
        status: 'active' as const,
        last_activity: currentTime,
        conversations_today: Math.floor(Math.random() * 25) + 5, // Mock data
        success_rate: 0.87
      },
      lead_bot: {
        status: 'active' as const,
        last_activity: currentTime,
        automations_running: Math.floor(Math.random() * 10) + 2,
        success_rate: 0.92
      },
      intent_decoder: {
        status: 'active' as const,
        last_activity: currentTime,
        analyses_today: Math.floor(Math.random() * 150) + 50,
        accuracy_rate: 0.95
      },
      realtime_coordination: {
        status: process.env.NEXT_PUBLIC_ENABLE_WEBSOCKET === 'true' ? 'connected' : 'disconnected' as const,
        active_connections: 1,
        last_heartbeat: currentTime
      }
    }

    // Performance metrics
    const performance = {
      frontend: {
        page_load_time_ms: 850, // Would be measured in production
        api_response_time_ms: 120,
        websocket_latency_ms: services.realtime_coordination.status === 'connected' ? 45 : null,
        error_rate: 0.002
      },
      backend: {
        available: !!process.env.NEXT_PUBLIC_API_BASE,
        response_time_ms: process.env.NEXT_PUBLIC_API_BASE ? 180 : null,
        queue_size: 3,
        active_requests: 7
      }
    }

    // Business metrics (mock data for demonstration)
    const business_metrics = {
      leads_processed_today: Math.floor(Math.random() * 50) + 20,
      qualifications_completed: Math.floor(Math.random() * 15) + 8,
      automations_triggered: Math.floor(Math.random() * 30) + 12,
      revenue_opportunities: Math.floor(Math.random() * 2500000) + 500000,
      conversion_rate: 0.23
    }

    // System alerts
    const alerts = []

    // Check for configuration issues
    if (!process.env.NEXT_PUBLIC_API_BASE) {
      alerts.push({
        severity: 'warning' as const,
        message: 'Backend API URL not configured',
        timestamp: currentTime,
        component: 'configuration'
      })
    }

    if (!process.env.NEXT_PUBLIC_SOCKET_URL) {
      alerts.push({
        severity: 'warning' as const,
        message: 'WebSocket URL not configured - real-time features disabled',
        timestamp: currentTime,
        component: 'realtime'
      })
    }

    if (performance.frontend.error_rate > 0.01) {
      alerts.push({
        severity: 'error' as const,
        message: `High error rate: ${(performance.frontend.error_rate * 100).toFixed(2)}%`,
        timestamp: currentTime,
        component: 'frontend'
      })
    }

    const statusData: SystemStatusResponse = {
      platform,
      services,
      performance,
      business_metrics,
      alerts
    }

    return NextResponse.json(statusData, {
      status: 200,
      headers: {
        'Cache-Control': 'public, max-age=30', // Cache for 30 seconds
        'X-Status-Check': 'jorge-platform-v1'
      }
    })

  } catch (error) {
    console.error('Status check failed:', error)

    return NextResponse.json(
      {
        platform: {
          name: "Jorge's Real Estate AI Platform",
          version: 'unknown',
          environment: 'error',
          deployment_id: 'unknown',
          build_time: 'unknown',
          commit_hash: 'unknown'
        },
        error: 'Failed to retrieve system status'
      },
      { status: 500 }
    )
  }
}

// OPTIONS method for CORS
export async function OPTIONS(request: NextRequest): Promise<NextResponse> {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    }
  })
}