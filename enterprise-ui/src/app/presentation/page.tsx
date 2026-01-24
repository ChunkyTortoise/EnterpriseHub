// Main Presentation Hub - Entry Point for Client Presentations
// Professional interface for Jorge's client-facing presentation system

'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  PresentationIcon,
  Users,
  TrendingUp,
  Award,
  Clock,
  Plus,
  Play,
  BarChart3,
  Target,
  Zap,
  Calendar,
  User,
  Building,
  DollarSign,
  Timer
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ClaudeConcierge } from '@/components/claude-concierge/ClaudeConcierge'
import usePresentation, { type ClientProfile } from '@/hooks/usePresentation'
import { cn } from '@/lib/utils'

export default function PresentationHub() {
  const router = useRouter()
  const [presentationState, presentationActions] = usePresentation()
  const [showNewSessionDialog, setShowNewSessionDialog] = useState(false)
  const [newSessionData, setNewSessionData] = useState({
    clientName: '',
    sessionType: 'demo' as const,
    propertyBudget: 500000,
    urgency: 'medium' as const,
    marketSegment: 'mid-market' as const,
    experience: 'some' as const,
    timeline: 6
  })

  const handleCreateSession = async () => {
    try {
      const clientProfile: ClientProfile = {
        name: newSessionData.clientName,
        propertyBudget: newSessionData.propertyBudget,
        urgency: newSessionData.urgency,
        marketSegment: newSessionData.marketSegment,
        experience: newSessionData.experience,
        timeline: newSessionData.timeline,
        concerns: [],
        priorities: [],
        preferredCommunication: 'email',
        source: 'referral'
      }

      const sessionId = await presentationActions.createSession(
        newSessionData.clientName,
        newSessionData.sessionType,
        clientProfile
      )

      setShowNewSessionDialog(false)
      router.push(`/presentation/client/${sessionId}`)
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  const getSessionTypeIcon = (type: string) => {
    switch (type) {
      case 'discovery': return <Users className="w-5 h-5" />
      case 'proposal': return <Target className="w-5 h-5" />
      case 'demo': return <Play className="w-5 h-5" />
      case 'closing': return <Award className="w-5 h-5" />
      default: return <PresentationIcon className="w-5 h-5" />
    }
  }

  const getSessionTypeColor = (type: string) => {
    switch (type) {
      case 'discovery': return 'bg-blue-50 text-blue-700 border-blue-200'
      case 'proposal': return 'bg-purple-50 text-purple-700 border-purple-200'
      case 'demo': return 'bg-green-50 text-green-700 border-green-200'
      case 'closing': return 'bg-amber-50 text-amber-700 border-amber-200'
      default: return 'bg-gray-50 text-gray-700 border-gray-200'
    }
  }

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    }
    return `${minutes}m`
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Header */}
      <div className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">
                Jorge's Professional Presentation Hub
              </h1>
              <p className="text-gray-300">
                Command Center for Client Presentations & Deal Closing
              </p>
            </div>

            <div className="flex items-center gap-4">
              <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/30">
                <Zap className="w-4 h-4 mr-1" />
                AI-Powered
              </Badge>

              <Dialog open={showNewSessionDialog} onOpenChange={setShowNewSessionDialog}>
                <DialogTrigger asChild>
                  <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
                    <Plus className="w-5 h-5 mr-2" />
                    New Presentation
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl bg-slate-900 text-white border-slate-700">
                  <DialogHeader>
                    <DialogTitle className="text-white">Create New Client Presentation</DialogTitle>
                  </DialogHeader>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 py-6">
                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="clientName" className="text-gray-300">Client Name</Label>
                        <Input
                          id="clientName"
                          value={newSessionData.clientName}
                          onChange={(e) => setNewSessionData(prev => ({ ...prev, clientName: e.target.value }))}
                          placeholder="Enter client name"
                          className="bg-slate-800 border-slate-600 text-white"
                        />
                      </div>

                      <div>
                        <Label htmlFor="sessionType" className="text-gray-300">Presentation Type</Label>
                        <Select
                          value={newSessionData.sessionType}
                          onValueChange={(value: any) => setNewSessionData(prev => ({ ...prev, sessionType: value }))}
                        >
                          <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-slate-600">
                            <SelectItem value="discovery">Discovery Meeting</SelectItem>
                            <SelectItem value="demo">AI Demo & Capabilities</SelectItem>
                            <SelectItem value="proposal">Value Proposition</SelectItem>
                            <SelectItem value="closing">Closing & Commitment</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label htmlFor="propertyBudget" className="text-gray-300">Property Budget</Label>
                        <Input
                          id="propertyBudget"
                          type="number"
                          value={newSessionData.propertyBudget}
                          onChange={(e) => setNewSessionData(prev => ({ ...prev, propertyBudget: parseInt(e.target.value) || 0 }))}
                          placeholder="500000"
                          className="bg-slate-800 border-slate-600 text-white"
                        />
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <Label htmlFor="urgency" className="text-gray-300">Urgency Level</Label>
                        <Select
                          value={newSessionData.urgency}
                          onValueChange={(value: any) => setNewSessionData(prev => ({ ...prev, urgency: value }))}
                        >
                          <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-slate-600">
                            <SelectItem value="low">Low - Exploring Options</SelectItem>
                            <SelectItem value="medium">Medium - Active Search</SelectItem>
                            <SelectItem value="high">High - Urgent Need</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label htmlFor="marketSegment" className="text-gray-300">Market Segment</Label>
                        <Select
                          value={newSessionData.marketSegment}
                          onValueChange={(value: any) => setNewSessionData(prev => ({ ...prev, marketSegment: value }))}
                        >
                          <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent className="bg-slate-800 border-slate-600">
                            <SelectItem value="first-time">First-Time Buyer</SelectItem>
                            <SelectItem value="mid-market">Mid-Market</SelectItem>
                            <SelectItem value="luxury">Luxury Market</SelectItem>
                            <SelectItem value="investor">Investor/Portfolio</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      <div>
                        <Label htmlFor="timeline" className="text-gray-300">Timeline (Months)</Label>
                        <Input
                          id="timeline"
                          type="number"
                          value={newSessionData.timeline}
                          onChange={(e) => setNewSessionData(prev => ({ ...prev, timeline: parseInt(e.target.value) || 0 }))}
                          placeholder="6"
                          className="bg-slate-800 border-slate-600 text-white"
                        />
                      </div>
                    </div>
                  </div>

                  <div className="flex justify-end gap-3">
                    <Button
                      variant="outline"
                      onClick={() => setShowNewSessionDialog(false)}
                      className="border-slate-600 text-gray-300 hover:bg-slate-800"
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={handleCreateSession}
                      disabled={!newSessionData.clientName}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      <Play className="w-4 h-4 mr-2" />
                      Start Presentation
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-6">
        <Tabs defaultValue="dashboard" className="w-full">
          <TabsList className="bg-slate-800 border-slate-700 mb-8">
            <TabsTrigger value="dashboard" className="data-[state=active]:bg-slate-700">
              <BarChart3 className="w-4 h-4 mr-2" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="active" className="data-[state=active]:bg-slate-700">
              <Play className="w-4 h-4 mr-2" />
              Active Sessions
            </TabsTrigger>
            <TabsTrigger value="history" className="data-[state=active]:bg-slate-700">
              <Clock className="w-4 h-4 mr-2" />
              Session History
            </TabsTrigger>
          </TabsList>

          {/* Dashboard */}
          <TabsContent value="dashboard" className="space-y-6">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card className="bg-white/5 border-white/10">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Total Sessions</p>
                      <p className="text-3xl font-bold text-white">
                        {presentationState.activeSessions.length + presentationState.sessionHistory.length}
                      </p>
                    </div>
                    <PresentationIcon className="w-8 h-8 text-blue-400" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white/5 border-white/10">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Active Now</p>
                      <p className="text-3xl font-bold text-green-400">
                        {presentationState.activeSessions.length}
                      </p>
                    </div>
                    <Play className="w-8 h-8 text-green-400" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white/5 border-white/10">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Avg Conversion</p>
                      <p className="text-3xl font-bold text-purple-400">84%</p>
                    </div>
                    <TrendingUp className="w-8 h-8 text-purple-400" />
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-white/5 border-white/10">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Avg Duration</p>
                      <p className="text-3xl font-bold text-amber-400">42m</p>
                    </div>
                    <Timer className="w-8 h-8 text-amber-400" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Quick Actions */}
            <Card className="bg-white/5 border-white/10">
              <CardHeader>
                <CardTitle className="text-white">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Button
                    variant="outline"
                    className="h-24 flex flex-col items-center justify-center border-blue-500/30 text-blue-300 hover:bg-blue-500/10"
                    onClick={() => setShowNewSessionDialog(true)}
                  >
                    <Plus className="w-6 h-6 mb-2" />
                    New Demo Session
                  </Button>

                  <Button
                    variant="outline"
                    className="h-24 flex flex-col items-center justify-center border-purple-500/30 text-purple-300 hover:bg-purple-500/10"
                    onClick={() => router.push('/presentation/roi-calculator')}
                  >
                    <DollarSign className="w-6 h-6 mb-2" />
                    ROI Calculator
                  </Button>

                  <Button
                    variant="outline"
                    className="h-24 flex flex-col items-center justify-center border-green-500/30 text-green-300 hover:bg-green-500/10"
                    onClick={() => router.push('/presentation/reports')}
                  >
                    <BarChart3 className="w-6 h-6 mb-2" />
                    Performance Reports
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Active Sessions */}
          <TabsContent value="active" className="space-y-6">
            {presentationState.activeSessions.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {presentationState.activeSessions.map((session) => (
                  <Card key={session.id} className="bg-white/5 border-white/10">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          {getSessionTypeIcon(session.sessionType)}
                          <div>
                            <CardTitle className="text-white">{session.clientName}</CardTitle>
                            <p className="text-sm text-gray-400">
                              {session.sessionType.charAt(0).toUpperCase() + session.sessionType.slice(1)} Session
                            </p>
                          </div>
                        </div>
                        <Badge className={getSessionTypeColor(session.sessionType)}>
                          Active
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-400">Progress</span>
                        <span className="text-white">
                          {session.currentSlide + 1} / {session.agenda.length} slides
                        </span>
                      </div>

                      <div className="w-full bg-slate-700 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all"
                          style={{
                            width: `${((session.currentSlide + 1) / session.agenda.length) * 100}%`
                          }}
                        />
                      </div>

                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-400">Started</span>
                          <div className="text-white">
                            {session.startTime.toLocaleTimeString()}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-400">Duration</span>
                          <div className="text-white">
                            {formatDuration(session.duration)}
                          </div>
                        </div>
                      </div>

                      <Button
                        className="w-full bg-blue-600 hover:bg-blue-700"
                        onClick={() => router.push(`/presentation/client/${session.id}`)}
                      >
                        <Play className="w-4 h-4 mr-2" />
                        Continue Session
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="bg-white/5 border-white/10">
                <CardContent className="p-12 text-center">
                  <Play className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">
                    No Active Presentations
                  </h3>
                  <p className="text-gray-400 mb-6">
                    Start a new client presentation to begin showcasing Jorge's AI capabilities
                  </p>
                  <Button
                    onClick={() => setShowNewSessionDialog(true)}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    Start New Presentation
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Session History */}
          <TabsContent value="history" className="space-y-6">
            {presentationState.sessionHistory.length > 0 ? (
              <div className="space-y-4">
                {presentationState.sessionHistory.map((session) => (
                  <Card key={session.id} className="bg-white/5 border-white/10">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-3">
                            {getSessionTypeIcon(session.sessionType)}
                            <div>
                              <h4 className="font-semibold text-white">{session.clientName}</h4>
                              <p className="text-sm text-gray-400">
                                {session.sessionType.charAt(0).toUpperCase() + session.sessionType.slice(1)} Session
                              </p>
                            </div>
                          </div>

                          <div className="text-sm text-gray-400">
                            <div>Completed: {session.completedAt?.toLocaleDateString()}</div>
                            <div>Duration: {formatDuration(session.duration)}</div>
                          </div>
                        </div>

                        <div className="flex items-center gap-3">
                          <Badge className={getSessionTypeColor(session.sessionType)}>
                            Completed
                          </Badge>
                          <Button
                            variant="outline"
                            size="sm"
                            className="border-slate-600 text-gray-300 hover:bg-slate-800"
                          >
                            View Details
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card className="bg-white/5 border-white/10">
                <CardContent className="p-12 text-center">
                  <Clock className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold text-white mb-2">
                    No Presentation History
                  </h3>
                  <p className="text-gray-400">
                    Complete your first client presentation to see history here
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Claude Concierge */}
      <ClaudeConcierge />
    </div>
  )
}