"use client";

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  BarChart3,
  TrendingUp,
  FileText,
  Download,
  Calendar,
  Users,
  DollarSign,
  Target,
  Zap,
  Star,
  Share,
  Eye,
  Plus,
  RefreshCw,
  Play,
  Presentation
} from 'lucide-react'
import { PerformanceReports } from '@/components/analytics/PerformanceReports'
import { useAnalytics } from '@/hooks/useAnalytics'
import { format } from 'date-fns'

export default function ReportsPage() {
  const {
    reports,
    metrics,
    insights,
    recommendations,
    isLoading,
    isGeneratingReport,
    error,
    lastUpdated,
    generateReport,
    exportReport,
    refreshData
  } = useAnalytics({
    autoRefresh: true,
    includeRealTime: true
  })

  const [selectedReportType, setSelectedReportType] = useState<string>('all')
  const [showCreateModal, setShowCreateModal] = useState(false)

  // Quick metrics for dashboard overview
  const quickMetrics = metrics ? [
    {
      title: 'Total Revenue',
      value: `$${(metrics.revenueMetrics.totalRevenue / 1000000).toFixed(1)}M`,
      change: `+${((metrics.revenueMetrics.monthlyROI) * 100).toFixed(1)}%`,
      changeType: 'positive' as const,
      icon: DollarSign,
      color: 'text-green-400'
    },
    {
      title: 'Conversion Rate',
      value: `${(metrics.leadMetrics.conversionRate * 100).toFixed(1)}%`,
      change: '+255%',
      changeType: 'positive' as const,
      icon: Target,
      color: 'text-blue-400'
    },
    {
      title: 'Client Satisfaction',
      value: `${metrics.clientSatisfaction.overallSatisfaction}/5`,
      change: `NPS: ${metrics.clientSatisfaction.npsScore}`,
      changeType: 'positive' as const,
      icon: Star,
      color: 'text-yellow-400'
    },
    {
      title: 'Response Time',
      value: '2 min',
      change: '99.8% faster',
      changeType: 'positive' as const,
      icon: Zap,
      color: 'text-purple-400'
    }
  ] : []

  // Report templates
  const reportTemplates = [
    {
      id: 'executive-summary',
      name: 'Executive Summary',
      description: 'One-page performance overview for stakeholders',
      estimatedTime: '15 seconds',
      icon: FileText,
      popular: true,
      features: ['Key metrics', 'ROI analysis', 'Competitive position']
    },
    {
      id: 'client-presentation',
      name: 'Client Presentation',
      description: 'Professional presentation showcasing Jorge AI advantages',
      estimatedTime: '45 seconds',
      icon: Presentation,
      popular: true,
      features: ['Jorge introduction', 'Success stories', 'Technology advantages', 'ROI calculator']
    },
    {
      id: 'detailed-analysis',
      name: 'Detailed Analysis',
      description: 'Comprehensive performance analysis across all metrics',
      estimatedTime: '2 minutes',
      icon: BarChart3,
      popular: false,
      features: ['Bot deep-dive', 'Revenue analysis', 'Lead quality', 'Optimization recommendations']
    },
    {
      id: 'competitive-analysis',
      name: 'Competitive Analysis',
      description: 'Market positioning and competitive intelligence',
      estimatedTime: '90 seconds',
      icon: TrendingUp,
      popular: false,
      features: ['Market position', 'Competitive benchmarks', 'Technology leadership']
    }
  ]

  const handleGenerateReport = async (templateId: string) => {
    try {
      await generateReport(templateId)
      setShowCreateModal(false)
    } catch (err) {
      console.error('Failed to generate report:', err)
    }
  }

  const handleExportReport = async (reportId: string, format: 'pdf' | 'powerpoint' | 'excel') => {
    try {
      const blob = await exportReport(reportId, format)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `jorge-ai-report-${reportId}.${format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Failed to export report:', err)
    }
  }

  if (isLoading && !metrics) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-4">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-400 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold text-slate-200">Loading Jorge AI Analytics...</h2>
            <p className="text-slate-400 mt-2">Calculating performance metrics and generating insights</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">
              Performance Reports & Analytics
            </h1>
            <p className="text-slate-300 text-lg">
              Professional reports showcasing Jorge AI's competitive advantages and ROI
            </p>
            {lastUpdated && (
              <p className="text-slate-400 text-sm mt-1">
                Last updated: {format(lastUpdated, 'PPp')}
              </p>
            )}
          </div>

          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={refreshData}
              disabled={isLoading}
              className="border-slate-600 text-slate-200 hover:bg-slate-700"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Plus className="h-4 w-4 mr-2" />
              Create Report
            </Button>
          </div>
        </div>

        {error && (
          <Card className="bg-red-900/50 border-red-700">
            <CardContent className="p-4">
              <p className="text-red-200">Error: {error}</p>
            </CardContent>
          </Card>
        )}

        {/* Quick Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickMetrics.map((metric) => (
            <Card key={metric.title} className="bg-slate-800/50 border-slate-700">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-400">{metric.title}</p>
                    <p className="text-2xl font-bold text-white">{metric.value}</p>
                    <p className={`text-sm ${metric.color}`}>{metric.change}</p>
                  </div>
                  <div className={`p-3 rounded-full bg-slate-700 ${metric.color}`}>
                    <metric.icon className="h-6 w-6" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content */}
        <Tabs defaultValue="reports" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 bg-slate-800 border-slate-700">
            <TabsTrigger value="reports" className="data-[state=active]:bg-blue-600">
              <FileText className="h-4 w-4 mr-2" />
              Reports
            </TabsTrigger>
            <TabsTrigger value="analytics" className="data-[state=active]:bg-blue-600">
              <BarChart3 className="h-4 w-4 mr-2" />
              Analytics
            </TabsTrigger>
            <TabsTrigger value="insights" className="data-[state=active]:bg-blue-600">
              <TrendingUp className="h-4 w-4 mr-2" />
              Insights
            </TabsTrigger>
          </TabsList>

          {/* Reports Tab */}
          <TabsContent value="reports" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Recent Reports */}
              <div className="lg:col-span-2">
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader>
                    <div className="flex justify-between items-center">
                      <CardTitle className="text-white">Recent Reports</CardTitle>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          className="border-slate-600 text-slate-200 hover:bg-slate-700"
                        >
                          <Eye className="h-4 w-4 mr-2" />
                          View All
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {reports.length === 0 ? (
                        <div className="text-center py-8">
                          <FileText className="h-12 w-12 text-slate-500 mx-auto mb-4" />
                          <h3 className="text-lg font-semibold text-slate-200 mb-2">No Reports Yet</h3>
                          <p className="text-slate-400 mb-4">Create your first performance report to get started.</p>
                          <Button onClick={() => setShowCreateModal(true)}>
                            <Plus className="h-4 w-4 mr-2" />
                            Create Report
                          </Button>
                        </div>
                      ) : (
                        reports.slice(0, 5).map((report) => (
                          <div key={report.id} className="p-4 rounded-lg bg-slate-700/50 border border-slate-600">
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <h3 className="font-semibold text-white">{report.title}</h3>
                                <p className="text-sm text-slate-400">
                                  {format(new Date(report.createdAt), 'PPp')} • {report.reportType}
                                </p>
                              </div>
                              <Badge
                                className={
                                  report.status === 'ready'
                                    ? 'bg-green-900 text-green-200'
                                    : report.status === 'generating'
                                    ? 'bg-yellow-900 text-yellow-200'
                                    : 'bg-slate-900 text-slate-200'
                                }
                              >
                                {report.status}
                              </Badge>
                            </div>

                            <div className="flex justify-between items-center mt-4">
                              <div className="flex gap-2">
                                <Badge variant="outline" className="text-xs">
                                  {report.insights.length} insights
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                  {report.recommendations.length} recommendations
                                </Badge>
                              </div>

                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleExportReport(report.id, 'pdf')}
                                  className="border-slate-600 text-slate-200 hover:bg-slate-600"
                                >
                                  <Download className="h-3 w-3 mr-1" />
                                  PDF
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleExportReport(report.id, 'powerpoint')}
                                  className="border-slate-600 text-slate-200 hover:bg-slate-600"
                                >
                                  <Presentation className="h-3 w-3 mr-1" />
                                  PPT
                                </Button>
                                <Button
                                  size="sm"
                                  className="bg-blue-600 hover:bg-blue-700"
                                >
                                  <Play className="h-3 w-3 mr-1" />
                                  Present
                                </Button>
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Report Templates */}
              <div>
                <Card className="bg-slate-800/50 border-slate-700">
                  <CardHeader>
                    <CardTitle className="text-white">Quick Create</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {reportTemplates.map((template) => (
                      <div key={template.id} className="p-3 rounded-lg bg-slate-700/30 border border-slate-600">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <template.icon className="h-5 w-5 text-blue-400" />
                            <div>
                              <h4 className="font-medium text-white text-sm">{template.name}</h4>
                              {template.popular && (
                                <Badge className="bg-yellow-900 text-yellow-200 text-xs">Popular</Badge>
                              )}
                            </div>
                          </div>
                        </div>
                        <p className="text-xs text-slate-400 mb-3">{template.description}</p>
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-slate-500">{template.estimatedTime}</span>
                          <Button
                            size="sm"
                            onClick={() => handleGenerateReport(template.id)}
                            disabled={isGeneratingReport}
                            className="bg-blue-600 hover:bg-blue-700 text-xs py-1 px-2"
                          >
                            Create
                          </Button>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics">
            <PerformanceReports />
          </TabsContent>

          {/* Insights Tab */}
          <TabsContent value="insights" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* AI Insights */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <TrendingUp className="h-5 w-5" />
                    AI-Generated Insights
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {insights.slice(0, 5).map((insight) => (
                    <div key={insight.id} className="p-4 rounded-lg bg-slate-700/30 border border-slate-600">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-medium text-white text-sm">{insight.title}</h4>
                        <Badge
                          className={
                            insight.impact === 'high'
                              ? 'bg-red-900 text-red-200'
                              : insight.impact === 'medium'
                              ? 'bg-yellow-900 text-yellow-200'
                              : 'bg-green-900 text-green-200'
                          }
                        >
                          {insight.impact}
                        </Badge>
                      </div>
                      <p className="text-slate-300 text-sm mb-3">{insight.description}</p>
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-slate-500">
                          Confidence: {(insight.confidence * 100).toFixed(0)}%
                        </span>
                        {insight.actionable && (
                          <Badge variant="outline" className="text-xs">
                            Actionable
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Recommendations */}
              <Card className="bg-slate-800/50 border-slate-700">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <Target className="h-5 w-5" />
                    Strategic Recommendations
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {recommendations.slice(0, 5).map((rec) => (
                    <div key={rec.id} className="p-4 rounded-lg bg-slate-700/30 border border-slate-600">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-medium text-white text-sm">{rec.title}</h4>
                        <Badge
                          className={
                            rec.priority === 'critical'
                              ? 'bg-red-900 text-red-200'
                              : rec.priority === 'high'
                              ? 'bg-orange-900 text-orange-200'
                              : rec.priority === 'medium'
                              ? 'bg-yellow-900 text-yellow-200'
                              : 'bg-green-900 text-green-200'
                          }
                        >
                          {rec.priority}
                        </Badge>
                      </div>
                      <p className="text-slate-300 text-sm mb-3">{rec.description}</p>
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-500">ROI: {rec.expectedROI}x</span>
                        <span className="text-slate-500">{rec.implementationTime}</span>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}