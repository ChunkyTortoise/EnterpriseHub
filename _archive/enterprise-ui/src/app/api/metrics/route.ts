/**
 * Performance Metrics Endpoint for Jorge's Real Estate AI Platform
 * Prometheus-compatible metrics for monitoring and alerting
 */

import { NextRequest, NextResponse } from 'next/server'

interface MetricsResponse {
  timestamp: string
  metrics: {
    // System metrics
    system_uptime_seconds: number
    memory_usage_bytes: number
    active_sessions: number

    // Application metrics
    jorge_seller_conversations_total: number
    jorge_seller_qualifications_completed: number
    jorge_seller_response_time_ms: number
    jorge_seller_success_rate: number

    lead_bot_automations_total: number
    lead_bot_sequences_active: number
    lead_bot_response_time_ms: number
    lead_bot_success_rate: number

    intent_decoder_analyses_total: number
    intent_decoder_accuracy_rate: number
    intent_decoder_processing_time_ms: number

    // Real-time metrics
    websocket_connections_active: number
    websocket_messages_per_second: number
    websocket_latency_ms: number

    // Frontend performance
    page_load_time_p95_ms: number
    api_request_duration_p95_ms: number
    error_rate_percentage: number

    // Business metrics
    daily_revenue_opportunities_usd: number
    conversion_rate_percentage: number
    customer_satisfaction_score: number
  }
  labels: {
    environment: string
    version: string
    deployment: string
    region: string
  }
}

const startTime = Date.now()

export async function GET(request: NextRequest): Promise<NextResponse> {
  try {
    const url = new URL(request.url)
    const format = url.searchParams.get('format') || 'json'

    const currentTime = Date.now()
    const timestamp = new Date().toISOString()

    // Calculate metrics (in production, these would come from actual monitoring)
    const metrics = {
      // System metrics
      system_uptime_seconds: Math.floor((currentTime - startTime) / 1000),
      memory_usage_bytes: process.memoryUsage().heapUsed,
      active_sessions: Math.floor(Math.random() * 10) + 1,

      // Jorge Seller Bot metrics
      jorge_seller_conversations_total: Math.floor(Math.random() * 150) + 50,
      jorge_seller_qualifications_completed: Math.floor(Math.random() * 25) + 8,
      jorge_seller_response_time_ms: 1200 + Math.floor(Math.random() * 400),
      jorge_seller_success_rate: 0.87 + Math.random() * 0.08,

      // Lead Bot metrics
      lead_bot_automations_total: Math.floor(Math.random() * 80) + 20,
      lead_bot_sequences_active: Math.floor(Math.random() * 15) + 3,
      lead_bot_response_time_ms: 800 + Math.floor(Math.random() * 300),
      lead_bot_success_rate: 0.92 + Math.random() * 0.05,

      // Intent Decoder metrics
      intent_decoder_analyses_total: Math.floor(Math.random() * 500) + 100,
      intent_decoder_accuracy_rate: 0.95 + Math.random() * 0.03,
      intent_decoder_processing_time_ms: 42 + Math.floor(Math.random() * 20),

      // Real-time metrics
      websocket_connections_active: process.env.NEXT_PUBLIC_ENABLE_WEBSOCKET === 'true' ?
        Math.floor(Math.random() * 5) + 1 : 0,
      websocket_messages_per_second: 2.3 + Math.random() * 3.7,
      websocket_latency_ms: 45 + Math.floor(Math.random() * 30),

      // Frontend performance
      page_load_time_p95_ms: 850 + Math.floor(Math.random() * 400),
      api_request_duration_p95_ms: 120 + Math.floor(Math.random() * 80),
      error_rate_percentage: 0.2 + Math.random() * 0.8,

      // Business metrics
      daily_revenue_opportunities_usd: Math.floor(Math.random() * 3000000) + 500000,
      conversion_rate_percentage: 23 + Math.random() * 12,
      customer_satisfaction_score: 4.2 + Math.random() * 0.7
    }

    const labels = {
      environment: process.env.NODE_ENV || 'development',
      version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
      deployment: process.env.VERCEL_GIT_COMMIT_SHA?.substring(0, 7) || 'local',
      region: process.env.VERCEL_REGION || 'local'
    }

    if (format === 'prometheus') {
      // Return Prometheus format
      const prometheusMetrics = generatePrometheusFormat(metrics, labels)
      return new NextResponse(prometheusMetrics, {
        status: 200,
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'Cache-Control': 'no-cache'
        }
      })
    }

    // Return JSON format
    const metricsData: MetricsResponse = {
      timestamp,
      metrics,
      labels
    }

    return NextResponse.json(metricsData, {
      status: 200,
      headers: {
        'Cache-Control': 'public, max-age=15', // Cache for 15 seconds
        'X-Metrics-Version': 'jorge-platform-v1'
      }
    })

  } catch (error) {
    console.error('Metrics collection failed:', error)
    return NextResponse.json(
      { error: 'Failed to collect metrics' },
      { status: 500 }
    )
  }
}

function generatePrometheusFormat(
  metrics: MetricsResponse['metrics'],
  labels: MetricsResponse['labels']
): string {
  const labelString = Object.entries(labels)
    .map(([key, value]) => `${key}="${value}"`)
    .join(',')

  const lines = []

  // Helper function to add metric
  const addMetric = (name: string, value: number, help: string, type: string = 'gauge') => {
    lines.push(`# HELP ${name} ${help}`)
    lines.push(`# TYPE ${name} ${type}`)
    lines.push(`${name}{${labelString}} ${value}`)
    lines.push('')
  }

  // System metrics
  addMetric('jorge_system_uptime_seconds', metrics.system_uptime_seconds, 'System uptime in seconds')
  addMetric('jorge_memory_usage_bytes', metrics.memory_usage_bytes, 'Memory usage in bytes')
  addMetric('jorge_active_sessions', metrics.active_sessions, 'Number of active user sessions')

  // Jorge Seller Bot metrics
  addMetric('jorge_seller_conversations_total', metrics.jorge_seller_conversations_total, 'Total conversations handled by Jorge Seller Bot', 'counter')
  addMetric('jorge_seller_qualifications_completed', metrics.jorge_seller_qualifications_completed, 'Number of completed qualifications', 'counter')
  addMetric('jorge_seller_response_time_ms', metrics.jorge_seller_response_time_ms, 'Average response time in milliseconds')
  addMetric('jorge_seller_success_rate', metrics.jorge_seller_success_rate, 'Success rate (0-1)')

  // Lead Bot metrics
  addMetric('jorge_lead_bot_automations_total', metrics.lead_bot_automations_total, 'Total automations processed', 'counter')
  addMetric('jorge_lead_bot_sequences_active', metrics.lead_bot_sequences_active, 'Number of active automation sequences')
  addMetric('jorge_lead_bot_response_time_ms', metrics.lead_bot_response_time_ms, 'Average response time in milliseconds')
  addMetric('jorge_lead_bot_success_rate', metrics.lead_bot_success_rate, 'Success rate (0-1)')

  // Intent Decoder metrics
  addMetric('jorge_intent_decoder_analyses_total', metrics.intent_decoder_analyses_total, 'Total intent analyses performed', 'counter')
  addMetric('jorge_intent_decoder_accuracy_rate', metrics.intent_decoder_accuracy_rate, 'Accuracy rate (0-1)')
  addMetric('jorge_intent_decoder_processing_time_ms', metrics.intent_decoder_processing_time_ms, 'Average processing time in milliseconds')

  // Real-time metrics
  addMetric('jorge_websocket_connections_active', metrics.websocket_connections_active, 'Number of active WebSocket connections')
  addMetric('jorge_websocket_messages_per_second', metrics.websocket_messages_per_second, 'WebSocket messages per second')
  addMetric('jorge_websocket_latency_ms', metrics.websocket_latency_ms, 'WebSocket latency in milliseconds')

  // Frontend performance
  addMetric('jorge_page_load_time_p95_ms', metrics.page_load_time_p95_ms, '95th percentile page load time in milliseconds')
  addMetric('jorge_api_request_duration_p95_ms', metrics.api_request_duration_p95_ms, '95th percentile API request duration in milliseconds')
  addMetric('jorge_error_rate_percentage', metrics.error_rate_percentage, 'Error rate percentage')

  // Business metrics
  addMetric('jorge_daily_revenue_opportunities_usd', metrics.daily_revenue_opportunities_usd, 'Daily revenue opportunities in USD')
  addMetric('jorge_conversion_rate_percentage', metrics.conversion_rate_percentage, 'Conversion rate percentage')
  addMetric('jorge_customer_satisfaction_score', metrics.customer_satisfaction_score, 'Customer satisfaction score (1-5)')

  return lines.join('\n')
}

// Health check for metrics endpoint
export async function HEAD(request: NextRequest): Promise<NextResponse> {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'X-Metrics-Available': 'true',
      'Cache-Control': 'no-cache'
    }
  })
}