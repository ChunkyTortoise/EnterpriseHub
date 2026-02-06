"use client"

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Activity, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Clock, Zap } from 'lucide-react'
import { getPerformanceTracker, PerformanceMetrics } from '@/lib/performance/PerformanceTracker'

interface MetricCardProps {
  title: string
  current?: number
  target: number
  unit: string
  icon: React.ReactNode
  health?: string
  trend?: number[]
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  current,
  target,
  unit,
  icon,
  health = 'unknown',
  trend = []
}) => {
  const getHealthColor = (health: string) => {
    switch (health) {
      case 'excellent': return 'text-green-600 bg-green-50'
      case 'good': return 'text-blue-600 bg-blue-50'
      case 'warning': return 'text-yellow-600 bg-yellow-50'
      case 'critical': return 'text-red-600 bg-red-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'excellent': return <CheckCircle className="h-4 w-4" />
      case 'good': return <CheckCircle className="h-4 w-4" />
      case 'warning': return <AlertTriangle className="h-4 w-4" />
      case 'critical': return <AlertTriangle className="h-4 w-4" />
      default: return <Clock className="h-4 w-4" />
    }
  }

  const getTrendIcon = () => {
    if (trend.length < 2) return null
    const recent = trend.slice(-3)
    const avg = recent.reduce((a, b) => a + b, 0) / recent.length
    const earlier = trend.slice(-6, -3)
    const earlierAvg = earlier.length > 0 ? earlier.reduce((a, b) => a + b, 0) / earlier.length : avg

    return avg < earlierAvg ? (
      <TrendingDown className="h-4 w-4 text-green-600" />
    ) : (
      <TrendingUp className="h-4 w-4 text-red-600" />
    )
  }

  const isExceedingTarget = current !== undefined && current > target

  return (
    <Card className={`${isExceedingTarget ? 'border-red-200 bg-red-50/30' : ''}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="flex items-center space-x-2">
          {getTrendIcon()}
          {icon}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">
              {current !== undefined ? `${current}${unit}` : '--'}
            </div>
            <p className="text-xs text-muted-foreground">
              Target: {target}{unit}
            </p>
          </div>
          <Badge className={getHealthColor(health)}>
            <div className="flex items-center space-x-1">
              {getHealthIcon(health)}
              <span className="capitalize">{health}</span>
            </div>
          </Badge>
        </div>

        {/* Performance Bar */}
        <div className="mt-3">
          <div className="flex justify-between text-xs text-muted-foreground mb-1">
            <span>Performance</span>
            <span>{current !== undefined ? Math.round((target / Math.max(current, target)) * 100) : '--'}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-500 ${
                health === 'excellent' ? 'bg-green-500' :
                health === 'good' ? 'bg-blue-500' :
                health === 'warning' ? 'bg-yellow-500' :
                health === 'critical' ? 'bg-red-500' :
                'bg-gray-400'
              }`}
              style={{
                width: current !== undefined ? `${Math.min((target / current) * 100, 100)}%` : '0%'
              }}
            />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

interface JorgeEnterpriseMetrics {
  jorge_empire_status: {
    jorge_bot: {
      response_time: {
        avg_ms: number
        p95_ms: number
        target_ms: number
      }
      requests: {
        total: number
        success_rate: number
      }
      health_status: string
    }
    lead_automation: {
      latency: {
        avg_ms: number
        p95_ms: number
        target_ms: number
      }
      totals: {
        success_rate: number
      }
      health_status: string
    }
    websocket_coordination: {
      delivery_time: {
        avg_ms: number
        p95_ms: number
        target_ms: number
      }
      deliveries: {
        success_rate: number
      }
      health_status: string
    }
    overall_system: {
      status: string
      active_alerts: number
    }
  }
  performance_grade: string
  generated_at: string
}

const PerformanceDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<PerformanceMetrics>()
  const [enterpriseMetrics, setEnterpriseMetrics] = useState<JorgeEnterpriseMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const performanceTracker = getPerformanceTracker()

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoading(true)

        // Get frontend metrics
        const frontendMetrics = performanceTracker.getRealTimeMetrics()
        setMetrics(frontendMetrics)

        // Get backend enterprise metrics
        const response = await fetch('/api/performance/summary')
        if (response.ok) {
          const backendMetrics = await response.json()
          setEnterpriseMetrics(backendMetrics)
        } else {
          console.warn('Backend performance metrics unavailable')
        }

        setError(null)
      } catch (err) {
        console.error('Failed to fetch performance metrics:', err)
        setError('Failed to load performance data')
      } finally {
        setLoading(false)
      }
    }

    // Initial fetch
    fetchMetrics()

    // Update every 5 seconds
    const interval = setInterval(fetchMetrics, 5000)
    return () => clearInterval(interval)
  }, [])

  if (loading && !metrics && !enterpriseMetrics) {
    return (
      <div className="performance-dashboard p-6">
        <div className="flex items-center justify-center h-64">
          <div className="flex items-center space-x-2">
            <Activity className="h-6 w-6 animate-pulse" />
            <span className="text-lg">Loading performance metrics...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error && !metrics && !enterpriseMetrics) {
    return (
      <div className="performance-dashboard p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-red-700 mb-2">Performance Monitoring Unavailable</h3>
            <p className="text-gray-600">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="performance-dashboard space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Performance Dashboard</h2>
          <p className="text-muted-foreground">
            Real-time monitoring of Jorge's AI Empire platform
          </p>
        </div>
        {enterpriseMetrics && (
          <Badge
            className={`text-sm px-3 py-1 ${
              enterpriseMetrics.performance_grade.startsWith('A') ? 'bg-green-100 text-green-800' :
              enterpriseMetrics.performance_grade.startsWith('B') ? 'bg-blue-100 text-blue-800' :
              'bg-yellow-100 text-yellow-800'
            }`}
          >
            {enterpriseMetrics.performance_grade}
          </Badge>
        )}
      </div>

      {/* Jorge Empire Metrics Grid */}
      {enterpriseMetrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            title="Jorge Response Time"
            current={enterpriseMetrics.jorge_empire_status.jorge_bot.response_time.avg_ms}
            target={42}
            unit="ms"
            icon={<Zap className="h-5 w-5 text-blue-600" />}
            health={enterpriseMetrics.jorge_empire_status.jorge_bot.health_status}
          />

          <MetricCard
            title="Lead Automation"
            current={enterpriseMetrics.jorge_empire_status.lead_automation.latency.avg_ms}
            target={500}
            unit="ms"
            icon={<Activity className="h-5 w-5 text-green-600" />}
            health={enterpriseMetrics.jorge_empire_status.lead_automation.health_status}
          />

          <MetricCard
            title="WebSocket Delivery"
            current={enterpriseMetrics.jorge_empire_status.websocket_coordination.delivery_time.avg_ms}
            target={10}
            unit="ms"
            icon={<TrendingUp className="h-5 w-5 text-purple-600" />}
            health={enterpriseMetrics.jorge_empire_status.websocket_coordination.health_status}
          />

          <MetricCard
            title="Success Rate"
            current={Math.round(
              (enterpriseMetrics.jorge_empire_status.jorge_bot.requests.success_rate +
               enterpriseMetrics.jorge_empire_status.lead_automation.totals.success_rate +
               enterpriseMetrics.jorge_empire_status.websocket_coordination.deliveries.success_rate) / 3
            )}
            target={95}
            unit="%"
            icon={<CheckCircle className="h-5 w-5 text-green-600" />}
            health={
              enterpriseMetrics.jorge_empire_status.jorge_bot.requests.success_rate > 95 ? 'excellent' :
              enterpriseMetrics.jorge_empire_status.jorge_bot.requests.success_rate > 90 ? 'good' :
              'warning'
            }
          />
        </div>
      )}

      {/* Frontend Metrics Grid (Fallback) */}
      {!enterpriseMetrics && metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <MetricCard
            title="Jorge Response Time"
            current={metrics.jorge_avg}
            target={42}
            unit="ms"
            icon={<Zap className="h-5 w-5 text-blue-600" />}
            health={metrics.api_health}
          />

          <MetricCard
            title="Automation Success"
            current={metrics.automation_success_rate}
            target={95}
            unit="%"
            icon={<Activity className="h-5 w-5 text-green-600" />}
            health={
              (metrics.automation_success_rate || 0) > 95 ? 'excellent' :
              (metrics.automation_success_rate || 0) > 90 ? 'good' :
              'warning'
            }
          />

          <MetricCard
            title="Cache Hit Rate"
            current={metrics.cache_hit_rate}
            target={95}
            unit="%"
            icon={<TrendingUp className="h-5 w-5 text-purple-600" />}
            health="good"
          />
        </div>
      )}

      {/* System Status */}
      {enterpriseMetrics && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>System Status</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {enterpriseMetrics.jorge_empire_status.overall_system.status.toUpperCase()}
                </div>
                <div className="text-sm text-muted-foreground">Overall Status</div>
              </div>

              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {enterpriseMetrics.jorge_empire_status.overall_system.active_alerts}
                </div>
                <div className="text-sm text-muted-foreground">Active Alerts</div>
              </div>

              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  99.5%
                </div>
                <div className="text-sm text-muted-foreground">Uptime</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Last Updated */}
      <div className="text-right text-xs text-muted-foreground">
        Last updated: {enterpriseMetrics ?
          new Date(enterpriseMetrics.generated_at).toLocaleTimeString() :
          new Date().toLocaleTimeString()
        }
      </div>
    </div>
  )
}

export default PerformanceDashboard