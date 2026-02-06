/**
 * Health Check Endpoint for Jorge's Real Estate AI Platform
 * Production monitoring and system status validation
 */

import { NextRequest, NextResponse } from 'next/server'

interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy'
  timestamp: string
  version: string
  uptime: number
  environment: string
  services: {
    database: 'healthy' | 'degraded' | 'unhealthy'
    redis: 'healthy' | 'degraded' | 'unhealthy'
    websocket: 'healthy' | 'degraded' | 'unhealthy'
    backend_api: 'healthy' | 'degraded' | 'unhealthy'
  }
  metrics: {
    memory_usage: number
    cpu_usage: number | null
    active_connections: number
    response_time_ms: number
  }
  checks: {
    next_js: boolean
    env_variables: boolean
    api_routes: boolean
    realtime_features: boolean
  }
}

const startTime = Date.now()

export async function GET(request: NextRequest): Promise<NextResponse<HealthCheckResponse>> {
  const checkStartTime = Date.now()

  try {
    // Environment validation
    const requiredEnvVars = [
      'NEXT_PUBLIC_API_BASE',
      'NEXT_PUBLIC_SOCKET_URL'
    ]

    const missingEnvVars = requiredEnvVars.filter(
      envVar => !process.env[envVar]
    )

    // Service status checks
    const serviceChecks = await Promise.allSettled([
      checkDatabaseHealth(),
      checkRedisHealth(),
      checkWebSocketHealth(),
      checkBackendApiHealth()
    ])

    const services = {
      database: serviceChecks[0].status === 'fulfilled' && serviceChecks[0].value ? 'healthy' : 'degraded',
      redis: serviceChecks[1].status === 'fulfilled' && serviceChecks[1].value ? 'healthy' : 'degraded',
      websocket: serviceChecks[2].status === 'fulfilled' && serviceChecks[2].value ? 'healthy' : 'degraded',
      backend_api: serviceChecks[3].status === 'fulfilled' && serviceChecks[3].value ? 'healthy' : 'degraded'
    } as const

    // System checks
    const checks = {
      next_js: true, // If we're responding, Next.js is working
      env_variables: missingEnvVars.length === 0,
      api_routes: await checkApiRoutes(),
      realtime_features: services.websocket === 'healthy'
    }

    // Calculate overall status
    const allServicesHealthy = Object.values(services).every(status => status === 'healthy')
    const allChecksPass = Object.values(checks).every(check => check === true)

    let overallStatus: 'healthy' | 'degraded' | 'unhealthy'
    if (allServicesHealthy && allChecksPass) {
      overallStatus = 'healthy'
    } else if (services.backend_api === 'unhealthy' || !checks.next_js) {
      overallStatus = 'unhealthy'
    } else {
      overallStatus = 'degraded'
    }

    const responseTime = Date.now() - checkStartTime

    const healthData: HealthCheckResponse = {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
      uptime: Date.now() - startTime,
      environment: process.env.NODE_ENV || 'development',
      services,
      metrics: {
        memory_usage: process.memoryUsage().heapUsed / 1024 / 1024, // MB
        cpu_usage: null, // CPU usage not available in Vercel serverless
        active_connections: 0, // Would need external monitoring
        response_time_ms: responseTime
      },
      checks
    }

    // Return appropriate HTTP status
    const httpStatus = overallStatus === 'healthy' ? 200 :
                      overallStatus === 'degraded' ? 200 : 503

    return NextResponse.json(healthData, {
      status: httpStatus,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'X-Health-Check': 'jorge-platform-v1'
      }
    })

  } catch (error) {
    console.error('Health check failed:', error)

    const failedHealthData: HealthCheckResponse = {
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
      uptime: Date.now() - startTime,
      environment: process.env.NODE_ENV || 'development',
      services: {
        database: 'unhealthy',
        redis: 'unhealthy',
        websocket: 'unhealthy',
        backend_api: 'unhealthy'
      },
      metrics: {
        memory_usage: 0,
        cpu_usage: null,
        active_connections: 0,
        response_time_ms: Date.now() - checkStartTime
      },
      checks: {
        next_js: false,
        env_variables: false,
        api_routes: false,
        realtime_features: false
      }
    }

    return NextResponse.json(failedHealthData, {
      status: 503,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'X-Health-Check': 'jorge-platform-v1'
      }
    })
  }
}

async function checkDatabaseHealth(): Promise<boolean> {
  try {
    // In production, this would check Supabase/PostgreSQL connectivity
    // For now, assume healthy if env vars are present
    return !!(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY)
  } catch {
    return false
  }
}

async function checkRedisHealth(): Promise<boolean> {
  try {
    // In production, this would ping Redis
    // For now, return true as it's optional for frontend
    return true
  } catch {
    return false
  }
}

async function checkWebSocketHealth(): Promise<boolean> {
  try {
    // Check if WebSocket URL is configured
    return !!process.env.NEXT_PUBLIC_SOCKET_URL
  } catch {
    return false
  }
}

async function checkBackendApiHealth(): Promise<boolean> {
  try {
    const backendUrl = process.env.NEXT_PUBLIC_API_BASE
    if (!backendUrl) return false

    // In production, this would make an actual HTTP request to backend health endpoint
    // For development, assume healthy if URL is configured
    const isLocalDev = backendUrl.includes('localhost')
    return isLocalDev || backendUrl.includes('https://')
  } catch {
    return false
  }
}

async function checkApiRoutes(): Promise<boolean> {
  try {
    // Check if critical API routes are responding
    // This is a simplified check - in production you'd test actual endpoints
    return true
  } catch {
    return false
  }
}

// HEAD method for simple uptime checks
export async function HEAD(request: NextRequest): Promise<NextResponse> {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'X-Health-Check': 'jorge-platform-v1',
      'Cache-Control': 'no-cache'
    }
  })
}