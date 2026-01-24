'use client'

import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  TrendingUp,
  Users,
  MessageCircle,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ThermometerSun,
  Zap,
  DollarSign,
  Phone
} from 'lucide-react'

interface SellerConversation {
  contact_id: string
  contact_name: string
  current_question: number
  questions_answered: number
  temperature: 'hot' | 'warm' | 'cold'
  last_message: string
  last_interaction: string
  property_value?: number
  completion_status: 'in_progress' | 'qualified' | 'disqualified'
  cma_triggered: boolean
  ghl_synced: boolean
}

interface SellerDashboardData {
  summary: {
    conversations_today: number
    qualified_sellers: number
    hot_leads: number
    completion_rate: number
    avg_response_time_ms: number
    q1_q4_conversion_rate: number
  }
  active_conversations: SellerConversation[]
  performance_metrics: {
    q1_completion_rate: number
    q2_completion_rate: number
    q3_completion_rate: number
    q4_completion_rate: number
    confrontational_effectiveness: number
    stall_breaker_success_rate: number
  }
  revenue_tracking: {
    potential_pipeline: number
    deals_in_progress: number
    avg_deal_size: number
    commission_projected: number
  }
  system_status: {
    ghl_connection: 'healthy' | 'degraded' | 'down'
    claude_api: 'active' | 'limited' | 'down'
    redis_cache: 'operational' | 'slow' | 'down'
  }
}

const JorgeSellerDashboard: React.FC = () => {
  const [selectedConversation, setSelectedConversation] = useState<string | null>(null)

  // Real-time dashboard data with 5-second refresh
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['jorge-seller-dashboard'],
    queryFn: async (): Promise<SellerDashboardData> => {
      const response = await fetch('/api/dashboard/metrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          metric_types: ['bot_performance'],
          real_time: true
        })
      })
      if (!response.ok) throw new Error('Failed to fetch dashboard data')
      const result = await response.json()
      return result.data
    },
    refetchInterval: 5000, // 5-second real-time updates
    staleTime: 0
  })

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-6">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-8 bg-gray-200 rounded w-1/2"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <Card className="m-8">
        <CardHeader>
          <CardTitle className="text-red-600">Dashboard Error</CardTitle>
          <CardDescription>
            Failed to load Jorge Seller Bot dashboard. Check backend connection.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={() => refetch()} variant="outline">
            Retry Connection
          </Button>
        </CardContent>
      </Card>
    )
  }

  const getTemperatureColor = (temp: string) => {
    switch (temp) {
      case 'hot': return 'bg-red-500 text-white'
      case 'warm': return 'bg-orange-500 text-white'
      case 'cold': return 'bg-blue-500 text-white'
      default: return 'bg-gray-500 text-white'
    }
  }

  const getQuestionLabel = (questionNum: number) => {
    const labels = {
      0: 'Initial Contact',
      1: 'Property Condition',
      2: 'Price Expectation',
      3: 'Motivation',
      4: 'Offer Acceptance'
    }
    return labels[questionNum as keyof typeof labels] || 'Complete'
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header with Jorge branding */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Jorge Seller Bot Dashboard</h1>
          <p className="text-gray-600 mt-1">Confrontational qualification • No-BS approach • 6% commission system</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="secondary" className="bg-green-100 text-green-800">
            {data?.system_status.ghl_connection === 'healthy' ? '✅ GHL Connected' : '❌ GHL Issues'}
          </Badge>
          <Badge variant="secondary" className="bg-blue-100 text-blue-800">
            Live Dashboard
          </Badge>
        </div>
      </div>

      {/* Key Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Conversations Today</p>
                <p className="text-2xl font-bold text-gray-900">{data?.summary.conversations_today || 0}</p>
              </div>
              <Users className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Qualified Sellers</p>
                <p className="text-2xl font-bold text-green-600">{data?.summary.qualified_sellers || 0}</p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">HOT Leads</p>
                <p className="text-2xl font-bold text-red-600">{data?.summary.hot_leads || 0}</p>
              </div>
              <ThermometerSun className="h-8 w-8 text-red-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Completion Rate</p>
                <p className="text-2xl font-bold text-purple-600">{data?.summary.completion_rate || 0}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Q1-Q4 Progress Tracker */}
      <Card>
        <CardHeader>
          <CardTitle>Jorge's Q1-Q4 Qualification Progress</CardTitle>
          <CardDescription>
            Confrontational methodology progress across all seller conversations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((questionNum) => {
                const completionRate = data?.performance_metrics?.[`q${questionNum}_completion_rate` as keyof typeof data.performance_metrics] || 0
                return (
                  <div key={questionNum} className="text-center">
                    <div className="flex items-center justify-center w-12 h-12 mx-auto mb-2 rounded-full bg-blue-100">
                      <span className="text-sm font-bold text-blue-600">Q{questionNum}</span>
                    </div>
                    <h4 className="font-medium text-gray-900">{getQuestionLabel(questionNum)}</h4>
                    <p className="text-sm text-gray-500 mt-1">{completionRate}% completion</p>
                    <Progress value={completionRate} className="mt-2" />
                  </div>
                )
              })}
            </div>

            <div className="mt-6 p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <div className="flex items-center space-x-2">
                <Zap className="h-5 w-5 text-yellow-600" />
                <p className="text-sm font-medium text-yellow-800">
                  Jorge's Confrontational Effectiveness: {data?.performance_metrics.confrontational_effectiveness || 0}%
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Temperature Distribution & Revenue Tracking */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Temperature Gauge</CardTitle>
            <CardDescription>Lead classification based on Jorge's criteria</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-red-500 rounded"></div>
                  <span className="font-medium">HOT (75+ Score)</span>
                </div>
                <span className="text-2xl font-bold text-red-600">{data?.summary.hot_leads || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-orange-500 rounded"></div>
                  <span className="font-medium">WARM (50-74)</span>
                </div>
                <span className="text-2xl font-bold text-orange-600">12</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 bg-blue-500 rounded"></div>
                  <span className="font-medium">COLD (<50)</span>
                </div>
                <span className="text-2xl font-bold text-blue-600">8</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Revenue Pipeline</CardTitle>
            <CardDescription>6% commission tracking for Jorge's deals</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Pipeline Value</span>
                <span className="text-xl font-bold text-green-600">
                  ${data?.revenue_tracking.potential_pipeline?.toLocaleString() || '0'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Projected Commission (6%)</span>
                <span className="text-xl font-bold text-purple-600">
                  ${data?.revenue_tracking.commission_projected?.toLocaleString() || '0'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Avg Deal Size</span>
                <span className="text-lg font-semibold">
                  ${data?.revenue_tracking.avg_deal_size?.toLocaleString() || '0'}
                </span>
              </div>
              <div className="flex items-center space-x-2 pt-2">
                <DollarSign className="h-5 w-5 text-green-500" />
                <span className="text-sm text-gray-600">
                  {data?.revenue_tracking.deals_in_progress || 0} deals in progress
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Conversations Table */}
      <Card>
        <CardHeader>
          <CardTitle>Active Seller Conversations</CardTitle>
          <CardDescription>
            Real-time view of Jorge's confrontational qualification sessions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Seller</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Temperature</TableHead>
                <TableHead>Last Message</TableHead>
                <TableHead>Property Value</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {/* Mock data for demonstration */}
              <TableRow>
                <TableCell>
                  <div>
                    <p className="font-medium">John Smith</p>
                    <p className="text-sm text-gray-500">john.smith@email.com</p>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">Q2 - Price</span>
                    <Progress value={50} className="w-20" />
                  </div>
                </TableCell>
                <TableCell>
                  <Badge className="bg-orange-500 text-white">WARM</Badge>
                </TableCell>
                <TableCell className="max-w-xs truncate">
                  "I think it's worth around $450k..."
                </TableCell>
                <TableCell>$450,000</TableCell>
                <TableCell>
                  <div className="flex items-center space-x-1">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    <span className="text-sm">CMA Triggered</span>
                  </div>
                </TableCell>
                <TableCell>
                  <Button variant="outline" size="sm">
                    View Chat
                  </Button>
                </TableCell>
              </TableRow>

              <TableRow>
                <TableCell>
                  <div>
                    <p className="font-medium">Sarah Johnson</p>
                    <p className="text-sm text-gray-500">sarah.j@email.com</p>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">Q4 - Offer</span>
                    <Progress value={90} className="w-20" />
                  </div>
                </TableCell>
                <TableCell>
                  <Badge className="bg-red-500 text-white">HOT</Badge>
                </TableCell>
                <TableCell className="max-w-xs truncate">
                  "Yes, let's do it! When can we close?"
                </TableCell>
                <TableCell>$385,000</TableCell>
                <TableCell>
                  <div className="flex items-center space-x-1">
                    <Phone className="h-4 w-4 text-blue-500" />
                    <span className="text-sm">Call Scheduled</span>
                  </div>
                </TableCell>
                <TableCell>
                  <Button variant="outline" size="sm">
                    View Chat
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* System Status Footer */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-4">
              <span className="text-gray-600">System Status:</span>
              <Badge variant={data?.system_status.ghl_connection === 'healthy' ? 'secondary' : 'destructive'}>
                GHL {data?.system_status.ghl_connection || 'Unknown'}
              </Badge>
              <Badge variant={data?.system_status.claude_api === 'active' ? 'secondary' : 'destructive'}>
                Claude {data?.system_status.claude_api || 'Unknown'}
              </Badge>
              <Badge variant={data?.system_status.redis_cache === 'operational' ? 'secondary' : 'destructive'}>
                Redis {data?.system_status.redis_cache || 'Unknown'}
              </Badge>
            </div>
            <div className="flex items-center space-x-2 text-gray-500">
              <Clock className="h-4 w-4" />
              <span>Avg Response: {data?.summary.avg_response_time_ms || 0}ms</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default JorgeSellerDashboard