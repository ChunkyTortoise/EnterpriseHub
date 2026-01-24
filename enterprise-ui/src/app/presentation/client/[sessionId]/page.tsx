// Live Client Presentation Interface
// Full-screen professional presentation system for Jorge's client meetings

'use client'

import { useState, useEffect, useCallback } from 'react'
import { useParams, useRouter } from 'next/navigation'
import {
  Play,
  Pause,
  SkipForward,
  SkipBack,
  Maximize,
  Minimize,
  Settings,
  Mic,
  MicOff,
  MousePointer2,
  Eye,
  TrendingUp,
  Award,
  Users,
  MessageSquare,
  X,
  CheckCircle,
  AlertCircle,
  Lightbulb,
  BarChart3
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ClaudeConcierge } from '@/components/claude-concierge/ClaudeConcierge'
import { ROICalculator } from '@/components/presentation/ROICalculator'
import { LiveDemonstration } from '@/components/demo/LiveDemonstration'
import { PerformanceReports } from '@/components/analytics/PerformanceReports'
import usePresentation from '@/hooks/usePresentation'
import { cn } from '@/lib/utils'

export default function LiveClientPresentation() {
  const params = useParams()
  const router = useRouter()
  const sessionId = params.sessionId as string

  const [presentationState, presentationActions] = usePresentation({
    enableAnalytics: true,
    enableRealTimeUpdates: true,
    trackMouseMovement: true,
    trackVoiceInput: true
  })

  const [showPresenterView, setShowPresenterView] = useState(false)
  const [showSessionComplete, setShowSessionComplete] = useState(false)
  const [sessionOutcome, setSessionOutcome] = useState<any>(null)
  const [isVoiceActive, setIsVoiceActive] = useState(false)

  // Load session on mount
  useEffect(() => {
    if (sessionId) {
      presentationActions.loadSession(sessionId)
    }
  }, [sessionId])

  // Track mouse movement for analytics
  const handleMouseMove = useCallback((event: React.MouseEvent) => {
    if (presentationState.currentSession?.isActive) {
      presentationActions.trackMousePosition(event.clientX, event.clientY)
    }
  }, [presentationState.currentSession?.isActive, presentationActions])

  // Track clicks for analytics
  const handleClick = useCallback((event: React.MouseEvent) => {
    const target = event.target as HTMLElement
    const elementId = target.id || target.className || 'unknown'
    presentationActions.trackClick(elementId, { x: event.clientX, y: event.clientY })
  }, [presentationActions])

  // Track scroll for analytics
  const handleScroll = useCallback(() => {
    presentationActions.trackScroll(window.scrollY)
  }, [presentationActions])

  // Navigation handlers
  const handleStartPresentation = async () => {
    await presentationActions.startSession()
  }

  const handleNextSlide = async () => {
    const success = await presentationActions.nextSlide()
    if (!success) {
      // Reached end, complete session
      try {
        const outcome = await presentationActions.completeSession()
        setSessionOutcome(outcome)
        setShowSessionComplete(true)
      } catch (error) {
        console.error('Failed to complete session:', error)
      }
    }
  }

  const handlePreviousSlide = async () => {
    await presentationActions.previousSlide()
  }

  const toggleVoice = () => {
    if (isVoiceActive) {
      presentationActions.trackVoiceInput(5000, 0.8) // 5 second voice input with 80% confidence
      setIsVoiceActive(false)
    } else {
      setIsVoiceActive(true)
    }
  }

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!presentationState.currentSession?.isActive) return

      switch (event.key) {
        case 'ArrowRight':
        case ' ':
          event.preventDefault()
          handleNextSlide()
          break
        case 'ArrowLeft':
          event.preventDefault()
          handlePreviousSlide()
          break
        case 'f':
        case 'F11':
          event.preventDefault()
          presentationActions.toggleFullScreen()
          break
        case 'Escape':
          if (presentationState.isFullScreen) {
            presentationActions.toggleFullScreen()
          }
          break
        case 'p':
          event.preventDefault()
          setShowPresenterView(!showPresenterView)
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    window.addEventListener('scroll', handleScroll)

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      window.removeEventListener('scroll', handleScroll)
    }
  }, [presentationState.currentSession?.isActive, presentationState.isFullScreen, showPresenterView])

  if (!presentationState.currentSession) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p>Loading presentation...</p>
        </div>
      </div>
    )
  }

  const currentSlide = presentationState.currentSession.agenda[presentationState.currentSlideIndex]
  const progress = ((presentationState.currentSlideIndex + 1) / presentationState.totalSlides) * 100

  const renderSlideContent = () => {
    if (!currentSlide) return null

    switch (currentSlide.component) {
      case 'intro':
        return (
          <div className="space-y-8 text-center">
            <div className="mb-12">
              <h1 className="text-6xl font-bold text-white mb-6">
                Jorge's AI Real Estate Advantage
              </h1>
              <p className="text-2xl text-gray-300 mb-8">
                Why I Command 6% Commission in a 3% World
              </p>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
                <div className="text-center">
                  <div className="text-4xl font-bold text-blue-400 mb-2">47%</div>
                  <div className="text-gray-300">More Transactions</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-green-400 mb-2">96%</div>
                  <div className="text-gray-300">Client Satisfaction</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-purple-400 mb-2">24/7</div>
                  <div className="text-gray-300">AI Availability</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold text-amber-400 mb-2">8.3x</div>
                  <div className="text-gray-300">Technology ROI</div>
                </div>
              </div>
            </div>

            <div className="bg-white/5 rounded-lg p-8 max-w-3xl mx-auto">
              <h3 className="text-2xl font-semibold text-white mb-4">
                {presentationState.currentSession.clientProfile?.name || 'Valued Client'}
              </h3>
              <p className="text-lg text-gray-300 leading-relaxed">
                You're not just hiring an agent. You're gaining access to an AI-powered ecosystem
                that works 24/7 to maximize your property value, minimize time on market, and
                deliver an experience that justifies premium pricing through superior results.
              </p>
            </div>
          </div>
        )

      case 'demo':
        return (
          <LiveDemonstration
            scenario={{
              id: 'jorge_seller_demo',
              name: 'Jorge Seller Bot Demo',
              description: 'Live demonstration of Jorge\'s confrontational qualification methodology',
              category: 'qualification',
              duration: 10,
              participants: ['Jorge Seller Bot', 'Potential Client'],
              conversationFlow: []
            }}
            isActive={presentationState.currentSession.isActive}
            progress={60}
            conversationProgress={75}
            onStart={() => {}}
            onPause={() => {}}
            onReset={() => {}}
            onNext={handleNextSlide}
            onSkip={handleNextSlide}
            expectedOutcomes={[
              {
                metric: 'Lead Temperature',
                value: 'Hot (85°)',
                significance: 'high',
                comparison: 'vs Traditional: 65°'
              },
              {
                metric: 'Qualification Time',
                value: '3.2 minutes',
                significance: 'high',
                comparison: 'vs Traditional: 12 minutes'
              }
            ]}
            jorgeAdvantages={[
              'Confrontational methodology filters out time-wasters',
              'AI-powered FRS/PCS dual scoring system',
              'Real-time market intelligence integration',
              'Automatic stall-breaking protocols'
            ]}
          />
        )

      case 'roi_calculator':
        return (
          <ROICalculator
            clientProfile={presentationState.currentSession.clientProfile || null}
            roiCalculation={null}
            isCalculating={false}
            onCalculate={() => {}}
            onComplete={handleNextSlide}
          />
        )

      case 'performance_reports':
        return (
          <PerformanceReports
            timeRange="3_months"
            onTimeRangeChange={() => {}}
            botMetrics={{
              jorge_seller_bot: {
                totalConversations: 1247,
                conversionRate: 0.84,
                averageResponseTime: 1.2,
                qualificationAccuracy: 0.95,
                revenueGenerated: 2847000,
                clientSatisfaction: 0.96
              },
              lead_bot: {
                totalConversations: 892,
                conversionRate: 0.78,
                averageResponseTime: 0.8,
                qualificationAccuracy: 0.91,
                revenueGenerated: 1654000,
                clientSatisfaction: 0.92
              }
            }}
            revenueTrends={[
              { month: 'Jan', jorge: 890000, traditional: 320000 },
              { month: 'Feb', jorge: 1240000, traditional: 380000 },
              { month: 'Mar', jorge: 1580000, traditional: 420000 }
            ]}
            marketComparisons={[
              { metric: 'Average Sale Price', jorge: 847000, market: 692000, improvement: 22.4 },
              { metric: 'Days on Market', jorge: 18, market: 45, improvement: 60.0 },
              { metric: 'Client Satisfaction', jorge: 96, market: 78, improvement: 23.1 }
            ]}
          />
        )

      case 'q_and_a':
        return (
          <div className="space-y-8">
            <div className="text-center mb-12">
              <h2 className="text-5xl font-bold text-white mb-4">Questions & Next Steps</h2>
              <p className="text-xl text-gray-300">
                Let's address your concerns and outline our path forward
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <Card className="bg-white/5 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-blue-400" />
                    Common Questions
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <Button
                    variant="outline"
                    className="w-full text-left justify-start border-slate-600 text-gray-300 hover:bg-slate-800"
                    onClick={() => presentationActions.trackQuestion("How do you justify 6% commission?")}
                  >
                    "How do you justify 6% commission?"
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full text-left justify-start border-slate-600 text-gray-300 hover:bg-slate-800"
                    onClick={() => presentationActions.trackQuestion("What if AI makes mistakes?")}
                  >
                    "What if the AI makes mistakes?"
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full text-left justify-start border-slate-600 text-gray-300 hover:bg-slate-800"
                    onClick={() => presentationActions.trackQuestion("How fast can you sell my property?")}
                  >
                    "How fast can you sell my property?"
                  </Button>
                </CardContent>
              </Card>

              <Card className="bg-white/5 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <CheckCircle className="w-5 h-5 text-green-400" />
                    Next Steps
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                        1
                      </div>
                      <span className="text-gray-300">Property evaluation and CMA generation</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                        2
                      </div>
                      <span className="text-gray-300">AI-powered marketing strategy development</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white text-sm font-semibold">
                        3
                      </div>
                      <span className="text-gray-300">Contract signing and campaign launch</span>
                    </div>
                  </div>

                  <Button
                    className="w-full bg-green-600 hover:bg-green-700 mt-6"
                    onClick={() => {
                      presentationActions.trackInterest('Ready to proceed')
                      handleNextSlide()
                    }}
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    I'm Ready to Proceed
                  </Button>
                </CardContent>
              </Card>
            </div>

            <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-lg p-8 border border-blue-500/20">
              <div className="flex items-start gap-4">
                <Lightbulb className="w-8 h-8 text-amber-400 flex-shrink-0 mt-1" />
                <div>
                  <h4 className="text-xl font-semibold text-white mb-2">
                    Jorge's Performance Guarantee
                  </h4>
                  <p className="text-gray-300 text-lg leading-relaxed">
                    I'm so confident in my AI-powered approach that I guarantee your property will
                    receive more qualified leads, sell faster, and achieve a higher price than
                    traditional methods. If not, I'll reduce my commission to match market rates.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )

      default:
        return (
          <div className="text-center text-white">
            <h2 className="text-4xl font-bold mb-4">{currentSlide.title}</h2>
            <p className="text-gray-300">Content for this slide is being prepared...</p>
          </div>
        )
    }
  }

  return (
    <div
      className={cn(
        "min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white",
        presentationState.isFullScreen && "fixed inset-0 z-50"
      )}
      onMouseMove={handleMouseMove}
      onClick={handleClick}
    >
      {/* Presentation Header */}
      {!presentationState.isFullScreen && (
        <div className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <h1 className="text-xl font-semibold text-white">
                  {presentationState.currentSession.clientName}
                </h1>
                <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/30">
                  {presentationState.currentSession.sessionType}
                </Badge>
                <div className="text-sm text-gray-300">
                  Slide {presentationState.currentSlideIndex + 1} of {presentationState.totalSlides}
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="text-sm text-gray-300">
                  {Math.floor(presentationState.timeElapsed / 60)}m {presentationState.timeElapsed % 60}s
                </div>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={toggleVoice}
                  className={cn(
                    "border-slate-600",
                    isVoiceActive ? "bg-red-500/20 text-red-300 border-red-500/30" : "text-gray-300 hover:bg-slate-800"
                  )}
                >
                  {isVoiceActive ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowPresenterView(!showPresenterView)}
                  className="border-slate-600 text-gray-300 hover:bg-slate-800"
                >
                  <Settings className="w-4 h-4" />
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={presentationActions.toggleFullScreen}
                  className="border-slate-600 text-gray-300 hover:bg-slate-800"
                >
                  {presentationState.isFullScreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
                </Button>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mt-4">
              <Progress value={progress} className="h-1" />
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 p-8 max-w-7xl mx-auto">
        {renderSlideContent()}
      </div>

      {/* Navigation Controls */}
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-black/50 backdrop-blur-sm rounded-full px-6 py-3 border border-white/10">
        <div className="flex items-center gap-4">
          <Button
            size="sm"
            variant="outline"
            onClick={handlePreviousSlide}
            disabled={presentationState.currentSlideIndex === 0}
            className="border-slate-600 text-gray-300 hover:bg-slate-800 disabled:opacity-50"
          >
            <SkipBack className="w-4 h-4" />
          </Button>

          {!presentationState.currentSession.isActive ? (
            <Button
              onClick={handleStartPresentation}
              className="bg-green-600 hover:bg-green-700 px-6"
            >
              <Play className="w-4 h-4 mr-2" />
              Start Presentation
            </Button>
          ) : (
            <Button
              onClick={presentationActions.pauseSession}
              variant="outline"
              className="border-amber-600 text-amber-300 hover:bg-amber-600/10"
            >
              <Pause className="w-4 h-4 mr-2" />
              Pause
            </Button>
          )}

          <Button
            size="sm"
            variant="outline"
            onClick={handleNextSlide}
            className="border-slate-600 text-gray-300 hover:bg-slate-800"
          >
            <SkipForward className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Presenter View Sidebar */}
      {showPresenterView && (
        <div className="fixed right-0 top-0 h-full w-96 bg-black/90 backdrop-blur-sm border-l border-white/10 p-6 overflow-y-auto">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white">Presenter View</h3>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowPresenterView(false)}
              className="border-slate-600 text-gray-300 hover:bg-slate-800"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          <div className="space-y-6">
            {/* Current Slide Info */}
            <div className="bg-white/5 rounded-lg p-4">
              <h4 className="font-semibold text-white mb-2">Current Slide</h4>
              <p className="text-sm text-gray-300 mb-2">{currentSlide?.title}</p>
              <p className="text-xs text-gray-400">{currentSlide?.speakerNotes}</p>
            </div>

            {/* Engagement Metrics */}
            <div className="bg-white/5 rounded-lg p-4">
              <h4 className="font-semibold text-white mb-3">Live Engagement</h4>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Attention</span>
                  <span className="text-sm text-green-400">
                    {Math.round(presentationState.engagementMetrics.attentionScore)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Interaction</span>
                  <span className="text-sm text-blue-400">
                    {Math.round(presentationState.engagementMetrics.interactionLevel)}%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Questions</span>
                  <span className="text-sm text-purple-400">
                    {presentationState.engagementMetrics.questionsAsked}
                  </span>
                </div>
              </div>
            </div>

            {/* Predictive Insights */}
            {presentationState.predictiveInsights.length > 0 && (
              <div className="bg-white/5 rounded-lg p-4">
                <h4 className="font-semibold text-white mb-3">AI Insights</h4>
                <div className="space-y-3">
                  {presentationState.predictiveInsights.slice(0, 3).map((insight, index) => (
                    <div key={index} className="text-sm">
                      <div className={cn(
                        "font-medium mb-1",
                        insight.urgency === 'high' ? 'text-red-400' :
                        insight.urgency === 'medium' ? 'text-amber-400' : 'text-green-400'
                      )}>
                        {insight.type.replace(/_/g, ' ').toUpperCase()}
                      </div>
                      <div className="text-gray-300 text-xs">{insight.recommendation}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Session Complete Dialog */}
      <Dialog open={showSessionComplete} onOpenChange={setShowSessionComplete}>
        <DialogContent className="max-w-2xl bg-slate-900 text-white border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Award className="w-6 h-6 text-green-400" />
              Presentation Complete!
            </DialogTitle>
          </DialogHeader>

          {sessionOutcome && (
            <div className="py-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-400 mb-2">
                    {Math.round(sessionOutcome.overallScore)}%
                  </div>
                  <div className="text-gray-300">Overall Score</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-400 mb-2">
                    {Math.round(sessionOutcome.conversionProbability)}%
                  </div>
                  <div className="text-gray-300">Conversion Probability</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-400 mb-2">
                    {Math.round(sessionOutcome.clientSatisfaction)}%
                  </div>
                  <div className="text-gray-300">Client Satisfaction</div>
                </div>
              </div>

              <div className="bg-white/5 rounded-lg p-4">
                <h4 className="font-semibold text-white mb-3">Key Insights</h4>
                <ul className="space-y-2">
                  {sessionOutcome.keyInsights.map((insight: string, index: number) => (
                    <li key={index} className="text-sm text-gray-300 flex items-start gap-2">
                      <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
                      {insight}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-white/5 rounded-lg p-4">
                <h4 className="font-semibold text-white mb-3">Follow-up Actions</h4>
                <div className="space-y-2">
                  {sessionOutcome.nextSteps.map((action: any, index: number) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <span className="text-gray-300">{action.description}</span>
                      <Badge variant="outline" className="text-xs">
                        {action.priority}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-3">
                <Button
                  variant="outline"
                  onClick={() => router.push('/presentation')}
                  className="border-slate-600 text-gray-300 hover:bg-slate-800"
                >
                  Back to Hub
                </Button>
                <Button
                  className="bg-blue-600 hover:bg-blue-700"
                  onClick={() => {
                    // Generate follow-up email or report
                    router.push('/presentation')
                  }}
                >
                  Generate Follow-up
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Claude Concierge */}
      {presentationState.showClaudeConcierge && <ClaudeConcierge />}
    </div>
  )
}