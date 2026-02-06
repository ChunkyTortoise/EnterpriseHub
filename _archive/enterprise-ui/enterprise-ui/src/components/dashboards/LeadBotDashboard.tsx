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
  Calendar,
  Phone,
  MessageSquare,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertTriangle,
  BarChart3,
  Mail,
  PhoneCall,
  Home,
  Star
} from 'lucide-react'

interface LeadAutomationSequence {
  contact_id: string
  contact_name: string
  email: string
  phone: string
  source: string
  current_day: number // Day in 3-7-30 sequence
  automation_status: {
    day_3_sms: 'scheduled' | 'sent' | 'replied' | 'failed'
    day_7_call: 'scheduled' | 'completed' | 'no_answer' | 'failed'
    day_30_reengagement: 'scheduled' | 'sent' | 'replied' | 'failed'
  }
  retell_ai_calls: Array<{
    call_id: string
    duration_minutes: number
    outcome: 'interested' | 'not_interested' | 'callback' | 'voicemail'
    scheduled_showing?: boolean
    timestamp: string
  }>
  behavioral_score: number // 0-100
  engagement_trend: 'increasing' | 'stable' | 'decreasing'
  cma_injected: boolean
  showing_scheduled: boolean
  post_showing_feedback?: {
    rating: number
    feedback: string
    interest_level: 'high' | 'medium' | 'low'
    next_steps: string
  }
}

interface LeadBotDashboardData {
  summary: {
    active_sequences: number
    day_3_completion_rate: number
    day_7_call_success_rate: number
    day_30_reengagement_rate: number
    retell_ai_call_minutes: number
    showings_scheduled_today: number
    total_touches_today: number
  }
  active_leads: LeadAutomationSequence[]
  performance_metrics: {
    automation_effectiveness: {
      day_3: { sent: number, replied: number, rate: number }
      day_7: { scheduled: number, completed: number, rate: number }
      day_30: { sent: number, reengaged: number, rate: number }
    }
    retell_ai_performance: {
      total_calls_today: number
      avg_call_duration: number
      showing_conversion_rate: number
      no_answer_rate: number
    }
    cma_injection_impact: {
      leads_with_cma: number
      conversion_lift: number
      avg_engagement_increase: number
    }
  }
  timeline_insights: {
    peak_engagement_times: string[]
    best_performing_sequences: string[]
    optimization_recommendations: string[]
  }
}

const LeadBotDashboard: React.FC = () => {
  const [selectedTimeframe, setSelectedTimeframe] = useState<'today' | 'week' | 'month'>('today')
  const [selectedLead, setSelectedLead] = useState<string | null>(null)

  // Real-time dashboard data with 5-second refresh for active sequences
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['lead-bot-dashboard', selectedTimeframe],
    queryFn: async (): Promise<LeadBotDashboardData> => {
      const response = await fetch('/api/bots/lead-bot', {
        method: 'GET'
      })
      if (!response.ok) throw new Error('Failed to fetch lead bot data')
      const result = await response.json()

      // Mock comprehensive data structure for development
      return {
        summary: {
          active_sequences: 45,
          day_3_completion_rate: 89.2,
          day_7_call_success_rate: 72.1,
          day_30_reengagement_rate: 43.5,
          retell_ai_call_minutes: 267,
          showings_scheduled_today: 8,
          total_touches_today: 34
        },
        active_leads: result.data.active_automations || [],
        performance_metrics: {
          automation_effectiveness: {
            day_3: { sent: 23, replied: 18, rate: 78.3 },
            day_7: { scheduled: 15, completed: 11, rate: 73.3 },
            day_30: { sent: 8, reengaged: 4, rate: 50.0 }
          },
          retell_ai_performance: {
            total_calls_today: 12,
            avg_call_duration: 4.2,
            showing_conversion_rate: 41.7,
            no_answer_rate: 25.0
          },
          cma_injection_impact: {
            leads_with_cma: 28,
            conversion_lift: 23.5,
            avg_engagement_increase: 34.2
          }
        },
        timeline_insights: {
          peak_engagement_times: ['10:00 AM', '2:00 PM', '7:00 PM'],
          best_performing_sequences: ['Day 3 SMS', 'Day 7 Retell Call'],
          optimization_recommendations: [
            'Increase Day 7 call frequency',
            'Add CMA to more sequences',
            'Optimize 2 PM send times'
          ]
        }
      }
    },
    refetchInterval: 5000, // 5-second real-time updates
    staleTime: 0
  })

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
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
          <CardTitle className="text-red-600">Lead Bot Dashboard Error</CardTitle>
          <CardDescription>
            Failed to load Lead Bot automation dashboard. Check backend connection.
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

  const getAutomationStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
      case 'sent':
      case 'replied': return 'bg-green-500 text-white'
      case 'scheduled': return 'bg-blue-500 text-white'
      case 'failed':
      case 'no_answer': return 'bg-red-500 text-white'
      default: return 'bg-gray-500 text-white'
    }
  }

  const getDayLabel = (day: number) => {
    if (day <= 3) return 'Day 3 SMS'
    if (day <= 7) return 'Day 7 Call'
    return 'Day 30 Re-engage'
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Lead Bot Dashboard</h1>
          <p className="text-gray-600 mt-1">3-7-30 Day Automation • Retell AI Integration • CMA Value Injection</p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600">Live Automation</span>
          </div>
          <Badge variant="secondary" className="bg-purple-100 text-purple-800">
            {data?.summary.active_sequences || 0} Active Sequences
          </Badge>
        </div>
      </div>

      {/* Key Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Day 3 Completion</p>
                <p className="text-2xl font-bold text-blue-600">{data?.summary.day_3_completion_rate || 0}%</p>
              </div>
              <MessageSquare className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Day 7 Call Success</p>
                <p className="text-2xl font-bold text-green-600">{data?.summary.day_7_call_success_rate || 0}%</p>
              </div>
              <PhoneCall className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Retell AI Minutes</p>
                <p className="text-2xl font-bold text-purple-600">{data?.summary.retell_ai_call_minutes || 0}</p>
              </div>
              <Phone className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Showings Today</p>
                <p className="text-2xl font-bold text-orange-600">{data?.summary.showings_scheduled_today || 0}</p>
              </div>
              <Home className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 3-7-30 Day Timeline Visualization */}
      <Card>
        <CardHeader>
          <CardTitle>Automation Timeline Performance</CardTitle>
          <CardDescription>
            Success rates across the 3-7-30 day lead nurture sequence
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Day 3 SMS Sequence */}
            <div className="flex items-center space-x-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-center w-12 h-12 bg-blue-500 text-white rounded-full">
                <MessageSquare className="h-6 w-6" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">Day 3 - SMS Sequence</h3>
                  <Badge className="bg-blue-500 text-white">
                    {data?.performance_metrics.automation_effectiveness.day_3.rate || 0}% Response Rate
                  </Badge>
                </div>
                <Progress
                  value={data?.performance_metrics.automation_effectiveness.day_3.rate || 0}
                  className="w-full"
                />
                <p className="text-sm text-gray-600 mt-1">
                  {data?.performance_metrics.automation_effectiveness.day_3.sent || 0} sent •
                  {data?.performance_metrics.automation_effectiveness.day_3.replied || 0} replied
                </p>
              </div>
            </div>

            {/* Day 7 Retell AI Call */}
            <div className="flex items-center space-x-4 p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center justify-center w-12 h-12 bg-green-500 text-white rounded-full">
                <Phone className="h-6 w-6" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">Day 7 - Retell AI Voice Call</h3>
                  <Badge className="bg-green-500 text-white">
                    {data?.performance_metrics.automation_effectiveness.day_7.rate || 0}% Success Rate
                  </Badge>
                </div>
                <Progress
                  value={data?.performance_metrics.automation_effectiveness.day_7.rate || 0}
                  className="w-full"
                />
                <p className="text-sm text-gray-600 mt-1">
                  {data?.performance_metrics.automation_effectiveness.day_7.scheduled || 0} scheduled •
                  {data?.performance_metrics.automation_effectiveness.day_7.completed || 0} completed
                </p>
              </div>
            </div>

            {/* Day 30 Re-engagement */}
            <div className="flex items-center space-x-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center justify-center w-12 h-12 bg-purple-500 text-white rounded-full">
                <TrendingUp className="h-6 w-6" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">Day 30 - Re-engagement Campaign</h3>
                  <Badge className="bg-purple-500 text-white">
                    {data?.performance_metrics.automation_effectiveness.day_30.rate || 0}% Re-engagement Rate
                  </Badge>
                </div>
                <Progress
                  value={data?.performance_metrics.automation_effectiveness.day_30.rate || 0}
                  className="w-full"
                />
                <p className="text-sm text-gray-600 mt-1">
                  {data?.performance_metrics.automation_effectiveness.day_30.sent || 0} sent •
                  {data?.performance_metrics.automation_effectiveness.day_30.reengaged || 0} re-engaged
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Retell AI Performance & CMA Impact */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Retell AI Call Performance</CardTitle>
            <CardDescription>Voice automation insights and conversion tracking</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Calls Today</p>
                  <p className="text-xl font-bold text-green-600">
                    {data?.performance_metrics.retell_ai_performance.total_calls_today || 0}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">Avg Duration</p>
                  <p className="text-xl font-bold text-blue-600">
                    {data?.performance_metrics.retell_ai_performance.avg_call_duration || 0}m
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Showing Conversion</span>
                  <span className="text-sm font-bold text-green-600">
                    {data?.performance_metrics.retell_ai_performance.showing_conversion_rate || 0}%
                  </span>
                </div>
                <Progress
                  value={data?.performance_metrics.retell_ai_performance.showing_conversion_rate || 0}
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm font-medium">No Answer Rate</span>
                  <span className="text-sm font-bold text-red-600">
                    {data?.performance_metrics.retell_ai_performance.no_answer_rate || 0}%
                  </span>
                </div>
                <Progress
                  value={data?.performance_metrics.retell_ai_performance.no_answer_rate || 0}
                  className="w-full"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>CMA Injection Impact</CardTitle>
            <CardDescription>Zillow-defense value positioning effectiveness</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="text-center p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                <p className="text-2xl font-bold text-yellow-600">
                  +{data?.performance_metrics.cma_injection_impact.conversion_lift || 0}%
                </p>
                <p className="text-sm font-medium text-yellow-800">Conversion Lift</p>
              </div>

              <div className="grid grid-cols-1 gap-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-600">Leads with CMA</span>
                  <span className="text-lg font-bold">
                    {data?.performance_metrics.cma_injection_impact.leads_with_cma || 0}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-600">Avg Engagement Increase</span>
                  <span className="text-lg font-bold text-green-600">
                    +{data?.performance_metrics.cma_injection_impact.avg_engagement_increase || 0}%
                  </span>
                </div>
              </div>

              <div className="pt-2 border-t border-gray-200">
                <p className="text-xs text-gray-500 text-center">
                  CMA injection combats Zillow estimates with professional market analysis
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Leads with Post-Showing Feedback */}
      <Card>
        <CardHeader>
          <CardTitle>Active Lead Sequences</CardTitle>
          <CardDescription>
            Live view of leads progressing through 3-7-30 day automation
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Lead</TableHead>
                <TableHead>Current Stage</TableHead>
                <TableHead>Automation Status</TableHead>
                <TableHead>Behavioral Score</TableHead>
                <TableHead>CMA Status</TableHead>
                <TableHead>Post-Showing</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {/* Mock active leads for demonstration */}
              <TableRow>
                <TableCell>
                  <div>
                    <p className="font-medium">Mike Johnson</p>
                    <p className="text-sm text-gray-500">mike.j@email.com</p>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge className="bg-green-500 text-white">Day 7 Call</Badge>
                </TableCell>
                <TableCell>
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      <span className="text-xs">Day 3 SMS - Replied</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Phone className="h-4 w-4 text-blue-500" />
                      <span className="text-xs">Day 7 Call - Scheduled</span>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">78</span>
                    <Progress value={78} className="w-16" />
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-green-600">CMA Sent</Badge>
                </TableCell>
                <TableCell>
                  <span className="text-sm text-gray-500">Pending</span>
                </TableCell>
                <TableCell>
                  <Button variant="outline" size="sm">
                    View Details
                  </Button>
                </TableCell>
              </TableRow>

              <TableRow>
                <TableCell>
                  <div>
                    <p className="font-medium">Lisa Chen</p>
                    <p className="text-sm text-gray-500">lisa.chen@email.com</p>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge className="bg-purple-500 text-white">Post-Showing</Badge>
                </TableCell>
                <TableCell>
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      <span className="text-xs">Day 7 Call - Completed</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Home className="h-4 w-4 text-orange-500" />
                      <span className="text-xs">Showing Completed</span>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">92</span>
                    <Progress value={92} className="w-16" />
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-green-600">CMA Reviewed</Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center space-x-1">
                    <Star className="h-4 w-4 text-yellow-500" />
                    <span className="text-sm font-medium">4.8</span>
                    <span className="text-xs text-gray-500">High Interest</span>
                  </div>
                </TableCell>
                <TableCell>
                  <Button variant="outline" size="sm">
                    View Feedback
                  </Button>
                </TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Optimization Insights */}
      <Card>
        <CardHeader>
          <CardTitle>Automation Insights</CardTitle>
          <CardDescription>AI-powered recommendations for sequence optimization</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="font-medium text-blue-900 mb-2">Peak Engagement Times</h4>
              <ul className="space-y-1">
                {data?.timeline_insights.peak_engagement_times.map((time, index) => (
                  <li key={index} className="text-sm text-blue-700">• {time}</li>
                ))}
              </ul>
            </div>

            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <h4 className="font-medium text-green-900 mb-2">Best Performing Sequences</h4>
              <ul className="space-y-1">
                {data?.timeline_insights.best_performing_sequences.map((sequence, index) => (
                  <li key={index} className="text-sm text-green-700">• {sequence}</li>
                ))}
              </ul>
            </div>

            <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
              <h4 className="font-medium text-yellow-900 mb-2">Optimization Opportunities</h4>
              <ul className="space-y-1">
                {data?.timeline_insights.optimization_recommendations.map((rec, index) => (
                  <li key={index} className="text-sm text-yellow-700">• {rec}</li>
                ))}
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default LeadBotDashboard