// Central Presentation Control Hub
// Professional interface for managing all client presentations

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  Users,
  Calendar,
  TrendingUp,
  Clock,
  Target,
  Award,
  BarChart3,
  Play,
  Pause,
  Settings,
  Filter,
  Search,
  Download,
  Mail,
  Phone,
  MessageSquare,
  Eye
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import usePresentation from '@/hooks/usePresentation'
import { cn } from '@/lib/utils'

interface PresentationHubProps {
  className?: string
}

export function PresentationHub({ className }: PresentationHubProps) {
  const router = useRouter()
  const [presentationState, presentationActions] = usePresentation()
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [typeFilter, setTypeFilter] = useState<string>('all')

  const filteredSessions = [
    ...presentationState.activeSessions,
    ...presentationState.sessionHistory
  ].filter(session => {
    const matchesSearch = session.clientName.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'all' ||
      (statusFilter === 'active' && session.isActive) ||
      (statusFilter === 'completed' && !session.isActive)
    const matchesType = typeFilter === 'all' || session.sessionType === typeFilter

    return matchesSearch && matchesStatus && matchesType
  })

  const getSessionStatusColor = (isActive: boolean) => {
    return isActive
      ? 'bg-green-50 text-green-700 border-green-200'
      : 'bg-gray-50 text-gray-700 border-gray-200'
  }

  const getSessionTypeIcon = (type: string) => {
    switch (type) {
      case 'discovery': return <Users className="w-4 h-4" />
      case 'proposal': return <Target className="w-4 h-4" />
      case 'demo': return <Play className="w-4 h-4" />
      case 'closing': return <Award className="w-4 h-4" />
      default: return <BarChart3 className="w-4 h-4" />
    }
  }

  const getEngagementColor = (score: number) => {
    if (score >= 80) return 'text-green-500'
    if (score >= 60) return 'text-yellow-500'
    return 'text-red-500'
  }

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  const calculateConversionRate = () => {
    const completedSessions = presentationState.sessionHistory.length
    const successfulSessions = presentationState.sessionHistory.filter(session =>
      session.outcomes.some(outcome => outcome.type === 'commitment' || outcome.type === 'contract_signed')
    ).length

    return completedSessions > 0 ? Math.round((successfulSessions / completedSessions) * 100) : 0
  }

  const averageSessionDuration = () => {
    const sessions = presentationState.sessionHistory
    if (sessions.length === 0) return 0

    const totalDuration = sessions.reduce((sum, session) => sum + session.duration, 0)
    return Math.round(totalDuration / sessions.length / 60) // in minutes
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Presentation Command Center</h2>
          <p className="text-gray-400">Manage and monitor all client presentations</p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            className="border-slate-600 text-gray-300 hover:bg-slate-800"
          >
            <Download className="w-4 h-4 mr-2" />
            Export Data
          </Button>

          <Button
            size="sm"
            className="bg-blue-600 hover:bg-blue-700"
            onClick={() => router.push('/presentation')}
          >
            <Play className="w-4 h-4 mr-2" />
            New Presentation
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Sessions</p>
                <p className="text-2xl font-bold text-white">
                  {presentationState.activeSessions.length + presentationState.sessionHistory.length}
                </p>
              </div>
              <BarChart3 className="w-6 h-6 text-blue-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Active Now</p>
                <p className="text-2xl font-bold text-green-400">
                  {presentationState.activeSessions.length}
                </p>
              </div>
              <Play className="w-6 h-6 text-green-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Conversion Rate</p>
                <p className="text-2xl font-bold text-purple-400">
                  {calculateConversionRate()}%
                </p>
              </div>
              <TrendingUp className="w-6 h-6 text-purple-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Avg Duration</p>
                <p className="text-2xl font-bold text-amber-400">
                  {averageSessionDuration()}m
                </p>
              </div>
              <Clock className="w-6 h-6 text-amber-400" />
            </div>
          </CardContent>
        </Card>

        <Card className="bg-white/5 border-white/10">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Avg Engagement</p>
                <p className="text-2xl font-bold text-emerald-400">87%</p>
              </div>
              <Eye className="w-6 h-6 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters and Search */}
      <div className="flex items-center gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Search clients..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-slate-800 border-slate-600 text-white"
            />
          </div>
        </div>

        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40 bg-slate-800 border-slate-600 text-white">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-600">
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>

        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-40 bg-slate-800 border-slate-600 text-white">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-slate-800 border-slate-600">
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="discovery">Discovery</SelectItem>
            <SelectItem value="demo">Demo</SelectItem>
            <SelectItem value="proposal">Proposal</SelectItem>
            <SelectItem value="closing">Closing</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Sessions List */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader>
          <CardTitle className="text-white">Client Sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredSessions.length > 0 ? (
              filteredSessions.map((session) => (
                <div
                  key={session.id}
                  className="bg-white/5 rounded-lg p-4 border border-white/10 hover:border-blue-500/30 transition-colors cursor-pointer"
                  onClick={() => router.push(`/presentation/client/${session.id}`)}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        {getSessionTypeIcon(session.sessionType)}
                        <span className="font-semibold text-white">{session.clientName}</span>
                      </div>

                      <Badge className={getSessionStatusColor(session.isActive)}>
                        {session.isActive ? 'Live' : 'Completed'}
                      </Badge>

                      <Badge variant="outline" className="text-xs">
                        {session.sessionType}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-2 text-sm text-gray-400">
                      <span>{formatDuration(session.duration)}</span>
                      <span>•</span>
                      <span>
                        {session.isActive
                          ? 'Started ' + session.startTime.toLocaleTimeString()
                          : session.completedAt?.toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-3">
                    <div className="text-sm">
                      <span className="text-gray-400">Progress:</span>
                      <div className="flex items-center gap-2 mt-1">
                        <Progress
                          value={((session.currentSlide + 1) / session.agenda.length) * 100}
                          className="h-1.5 flex-1"
                        />
                        <span className="text-white text-xs">
                          {session.currentSlide + 1}/{session.agenda.length}
                        </span>
                      </div>
                    </div>

                    <div className="text-sm">
                      <span className="text-gray-400">Engagement:</span>
                      <div className={cn(
                        "font-semibold mt-1",
                        getEngagementColor(session.engagementMetrics.attentionScore)
                      )}>
                        {Math.round(session.engagementMetrics.attentionScore)}%
                      </div>
                    </div>

                    <div className="text-sm">
                      <span className="text-gray-400">Questions:</span>
                      <div className="text-white font-semibold mt-1">
                        {session.engagementMetrics.questionsAsked}
                      </div>
                    </div>

                    <div className="text-sm">
                      <span className="text-gray-400">Interactions:</span>
                      <div className="text-white font-semibold mt-1">
                        {session.interactionLog.length}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-400">
                      <span>Budget: </span>
                      <span className="text-white">
                        {session.clientProfile?.propertyBudget
                          ? `$${(session.clientProfile.propertyBudget / 1000).toFixed(0)}K`
                          : 'Not specified'
                        }
                      </span>
                      <span className="mx-2">•</span>
                      <span>Urgency: </span>
                      <span className="text-white capitalize">
                        {session.clientProfile?.urgency || 'medium'}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {session.isActive && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e.stopPropagation()
                            // Join live session
                            router.push(`/presentation/client/${session.id}`)
                          }}
                          className="border-green-600 text-green-300 hover:bg-green-600/10"
                        >
                          <Play className="w-3 h-3 mr-1" />
                          Join Live
                        </Button>
                      )}

                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation()
                          // View analytics
                        }}
                        className="border-slate-600 text-gray-300 hover:bg-slate-800"
                      >
                        <BarChart3 className="w-3 h-3 mr-1" />
                        Analytics
                      </Button>

                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation()
                          // Contact client
                        }}
                        className="border-slate-600 text-gray-300 hover:bg-slate-800"
                      >
                        <MessageSquare className="w-3 h-3 mr-1" />
                        Contact
                      </Button>
                    </div>
                  </div>

                  {/* Follow-up Actions */}
                  {session.followUpActions.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-white/10">
                      <div className="text-sm text-gray-400 mb-2">Follow-up Actions:</div>
                      <div className="flex items-center gap-2 flex-wrap">
                        {session.followUpActions.slice(0, 3).map((action, index) => (
                          <Badge
                            key={index}
                            variant="outline"
                            className={cn(
                              'text-xs',
                              action.priority === 'high'
                                ? 'border-red-500/30 text-red-300'
                                : action.priority === 'medium'
                                ? 'border-yellow-500/30 text-yellow-300'
                                : 'border-gray-500/30 text-gray-300'
                            )}
                          >
                            {action.type}: {action.description.slice(0, 30)}...
                          </Badge>
                        ))}
                        {session.followUpActions.length > 3 && (
                          <span className="text-xs text-gray-400">
                            +{session.followUpActions.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="text-center py-12">
                <BarChart3 className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-white mb-2">
                  No sessions found
                </h3>
                <p className="text-gray-400 mb-4">
                  {searchQuery || statusFilter !== 'all' || typeFilter !== 'all'
                    ? 'Try adjusting your search filters'
                    : 'Start your first client presentation to see it here'
                  }
                </p>
                <Button
                  onClick={() => router.push('/presentation')}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Play className="w-4 h-4 mr-2" />
                  New Presentation
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default PresentationHub