// Presenter Control Panel
// Professional controls for managing presentations in real-time

'use client'

import { useState, useEffect } from 'react'
import {
  Play,
  Pause,
  Square,
  SkipForward,
  SkipBack,
  Volume2,
  VolumeX,
  Mic,
  MicOff,
  Camera,
  CameraOff,
  Users,
  Clock,
  Eye,
  MousePointer2,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  MessageSquare,
  Settings,
  Monitor,
  Presentation,
  Lightbulb,
  BarChart3
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'

interface PresentationControlsProps {
  sessionId: string
  isPlaying: boolean
  currentSlide: number
  totalSlides: number
  timeElapsed: number
  estimatedTimeRemaining: number
  engagementMetrics: {
    attentionScore: number
    interactionLevel: number
    questionsAsked: number
    objectionsRaised: number
    commitmentSignals: number
  }
  onPlay: () => void
  onPause: () => void
  onStop: () => void
  onNext: () => void
  onPrevious: () => void
  onGoToSlide: (index: number) => void
  onVolumeChange: (volume: number) => void
  onMicToggle: () => void
  onCameraToggle: () => void
  onShareScreen: () => void
  className?: string
}

interface PredictiveAlert {
  type: 'attention_drop' | 'confusion_detected' | 'interest_spike' | 'objection_incoming'
  message: string
  urgency: 'low' | 'medium' | 'high'
  recommendation: string
}

export function PresentationControls({
  sessionId,
  isPlaying,
  currentSlide,
  totalSlides,
  timeElapsed,
  estimatedTimeRemaining,
  engagementMetrics,
  onPlay,
  onPause,
  onStop,
  onNext,
  onPrevious,
  onGoToSlide,
  onVolumeChange,
  onMicToggle,
  onCameraToggle,
  onShareScreen,
  className
}: PresentationControlsProps) {
  const [volume, setVolume] = useState([80])
  const [isMuted, setIsMuted] = useState(false)
  const [isMicActive, setIsMicActive] = useState(false)
  const [isCameraActive, setIsCameraActive] = useState(false)
  const [showAdvancedControls, setShowAdvancedControls] = useState(false)
  const [alerts, setAlerts] = useState<PredictiveAlert[]>([])

  const progress = ((currentSlide + 1) / totalSlides) * 100

  // Simulate real-time alerts based on engagement
  useEffect(() => {
    if (!isPlaying) return

    const interval = setInterval(() => {
      const newAlerts: PredictiveAlert[] = []

      // Attention drop alert
      if (engagementMetrics.attentionScore < 60) {
        newAlerts.push({
          type: 'attention_drop',
          message: 'Client attention is dropping',
          urgency: 'high',
          recommendation: 'Ask an engaging question or switch to interactive element'
        })
      }

      // Confusion detection
      if (engagementMetrics.interactionLevel > 80 && engagementMetrics.attentionScore < 70) {
        newAlerts.push({
          type: 'confusion_detected',
          message: 'Possible confusion detected',
          urgency: 'medium',
          recommendation: 'Pause and check for understanding'
        })
      }

      // Interest spike
      if (engagementMetrics.interactionLevel > 90) {
        newAlerts.push({
          type: 'interest_spike',
          message: 'High interest detected',
          urgency: 'low',
          recommendation: 'Capitalize on interest with deeper dive'
        })
      }

      setAlerts(newAlerts)
    }, 5000)

    return () => clearInterval(interval)
  }, [isPlaying, engagementMetrics])

  const handleVolumeChange = (newVolume: number[]) => {
    setVolume(newVolume)
    onVolumeChange(newVolume[0])
  }

  const toggleMute = () => {
    setIsMuted(!isMuted)
    onVolumeChange(isMuted ? volume[0] : 0)
  }

  const toggleMic = () => {
    setIsMicActive(!isMicActive)
    onMicToggle()
  }

  const toggleCamera = () => {
    setIsCameraActive(!isCameraActive)
    onCameraToggle()
  }

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  const getEngagementColor = (score: number) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getAlertColor = (urgency: string) => {
    switch (urgency) {
      case 'high': return 'border-red-500 bg-red-500/10 text-red-300'
      case 'medium': return 'border-yellow-500 bg-yellow-500/10 text-yellow-300'
      case 'low': return 'border-green-500 bg-green-500/10 text-green-300'
      default: return 'border-gray-500 bg-gray-500/10 text-gray-300'
    }
  }

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'attention_drop': return <AlertTriangle className="w-4 h-4" />
      case 'confusion_detected': return <Eye className="w-4 h-4" />
      case 'interest_spike': return <TrendingUp className="w-4 h-4" />
      case 'objection_incoming': return <MessageSquare className="w-4 h-4" />
      default: return <CheckCircle className="w-4 h-4" />
    }
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Quick Status Overview */}
      <Card className="bg-white/5 border-white/10">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/30">
                {isPlaying ? 'Live' : 'Paused'}
              </Badge>
              <div className="text-sm text-gray-300">
                Slide {currentSlide + 1} of {totalSlides}
              </div>
              <div className="text-sm text-gray-300">
                {formatTime(timeElapsed)} elapsed
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className={cn('text-sm font-semibold', getEngagementColor(engagementMetrics.attentionScore))}>
                {Math.round(engagementMetrics.attentionScore)}% engaged
              </div>
            </div>
          </div>

          <Progress value={progress} className="h-2" />
        </CardContent>
      </Card>

      <Tabs defaultValue="controls" className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-slate-800 border-slate-700">
          <TabsTrigger value="controls" className="data-[state=active]:bg-slate-700">
            <Play className="w-4 h-4 mr-2" />
            Controls
          </TabsTrigger>
          <TabsTrigger value="analytics" className="data-[state=active]:bg-slate-700">
            <BarChart3 className="w-4 h-4 mr-2" />
            Analytics
          </TabsTrigger>
          <TabsTrigger value="slides" className="data-[state=active]:bg-slate-700">
            <Presentation className="w-4 h-4 mr-2" />
            Slides
          </TabsTrigger>
          <TabsTrigger value="alerts" className="data-[state=active]:bg-slate-700">
            <AlertTriangle className="w-4 h-4 mr-2" />
            Alerts {alerts.length > 0 && `(${alerts.length})`}
          </TabsTrigger>
        </TabsList>

        {/* Primary Controls */}
        <TabsContent value="controls" className="space-y-4">
          <Card className="bg-white/5 border-white/10">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Play className="w-5 h-5" />
                Presentation Controls
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Playback Controls */}
              <div className="flex items-center justify-center gap-3">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={onPrevious}
                  disabled={currentSlide === 0}
                  className="border-slate-600 text-gray-300 hover:bg-slate-800 disabled:opacity-50"
                >
                  <SkipBack className="w-4 h-4" />
                </Button>

                <Button
                  onClick={isPlaying ? onPause : onPlay}
                  size="lg"
                  className={cn(
                    'px-8',
                    isPlaying
                      ? 'bg-amber-600 hover:bg-amber-700'
                      : 'bg-green-600 hover:bg-green-700'
                  )}
                >
                  {isPlaying ? (
                    <>
                      <Pause className="w-5 h-5 mr-2" />
                      Pause
                    </>
                  ) : (
                    <>
                      <Play className="w-5 h-5 mr-2" />
                      Start
                    </>
                  )}
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={onNext}
                  disabled={currentSlide === totalSlides - 1}
                  className="border-slate-600 text-gray-300 hover:bg-slate-800 disabled:opacity-50"
                >
                  <SkipForward className="w-4 h-4" />
                </Button>

                <Button
                  size="sm"
                  variant="outline"
                  onClick={onStop}
                  className="border-red-600 text-red-300 hover:bg-red-600/10"
                >
                  <Square className="w-4 h-4" />
                </Button>
              </div>

              {/* Audio/Video Controls */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h4 className="text-white font-medium">Audio Controls</h4>
                  <div className="flex items-center gap-3">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={toggleMute}
                      className="border-slate-600 text-gray-300 hover:bg-slate-800"
                    >
                      {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                    </Button>
                    <div className="flex-1">
                      <Slider
                        value={isMuted ? [0] : volume}
                        onValueChange={handleVolumeChange}
                        max={100}
                        step={5}
                        disabled={isMuted}
                      />
                    </div>
                    <span className="text-sm text-gray-300 w-10">{isMuted ? 0 : volume[0]}%</span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">Microphone</span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={toggleMic}
                      className={cn(
                        'border-slate-600',
                        isMicActive
                          ? 'bg-red-500/20 text-red-300 border-red-500/30'
                          : 'text-gray-300 hover:bg-slate-800'
                      )}
                    >
                      {isMicActive ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
                    </Button>
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="text-white font-medium">Video & Sharing</h4>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">Camera</span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={toggleCamera}
                      className={cn(
                        'border-slate-600',
                        isCameraActive
                          ? 'bg-green-500/20 text-green-300 border-green-500/30'
                          : 'text-gray-300 hover:bg-slate-800'
                      )}
                    >
                      {isCameraActive ? <Camera className="w-4 h-4" /> : <CameraOff className="w-4 h-4" />}
                    </Button>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-300">Screen Share</span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={onShareScreen}
                      className="border-slate-600 text-gray-300 hover:bg-slate-800"
                    >
                      <Monitor className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Live Analytics */}
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="bg-white/5 border-white/10">
              <CardHeader>
                <CardTitle className="text-white text-sm">Engagement Metrics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-gray-300">Attention Score</span>
                    <span className={getEngagementColor(engagementMetrics.attentionScore)}>
                      {Math.round(engagementMetrics.attentionScore)}%
                    </span>
                  </div>
                  <Progress value={engagementMetrics.attentionScore} className="h-2" />
                </div>

                <div>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-gray-300">Interaction Level</span>
                    <span className={getEngagementColor(engagementMetrics.interactionLevel)}>
                      {Math.round(engagementMetrics.interactionLevel)}%
                    </span>
                  </div>
                  <Progress value={engagementMetrics.interactionLevel} className="h-2" />
                </div>

                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div className="text-center p-2 bg-white/5 rounded">
                    <div className="text-blue-400 font-semibold">{engagementMetrics.questionsAsked}</div>
                    <div className="text-gray-400">Questions</div>
                  </div>
                  <div className="text-center p-2 bg-white/5 rounded">
                    <div className="text-red-400 font-semibold">{engagementMetrics.objectionsRaised}</div>
                    <div className="text-gray-400">Objections</div>
                  </div>
                  <div className="text-center p-2 bg-white/5 rounded">
                    <div className="text-green-400 font-semibold">{engagementMetrics.commitmentSignals}</div>
                    <div className="text-gray-400">Signals</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/5 border-white/10">
              <CardHeader>
                <CardTitle className="text-white text-sm">Session Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-300">Elapsed Time</span>
                  </div>
                  <span className="text-white font-mono">{formatTime(timeElapsed)}</span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-300">Estimated Remaining</span>
                  </div>
                  <span className="text-white font-mono">{formatTime(estimatedTimeRemaining)}</span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2">
                    <Presentation className="w-4 h-4 text-gray-400" />
                    <span className="text-gray-300">Progress</span>
                  </div>
                  <span className="text-white">{Math.round(progress)}%</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Slide Navigation */}
        <TabsContent value="slides" className="space-y-4">
          <Card className="bg-white/5 border-white/10">
            <CardHeader>
              <CardTitle className="text-white text-sm">Slide Navigation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {Array.from({ length: totalSlides }, (_, index) => (
                  <Button
                    key={index}
                    size="sm"
                    variant={currentSlide === index ? "default" : "outline"}
                    onClick={() => onGoToSlide(index)}
                    className={cn(
                      "text-xs",
                      currentSlide === index
                        ? "bg-blue-600 hover:bg-blue-700"
                        : "border-slate-600 text-gray-300 hover:bg-slate-800"
                    )}
                  >
                    Slide {index + 1}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AI Alerts */}
        <TabsContent value="alerts" className="space-y-4">
          <Card className="bg-white/5 border-white/10">
            <CardHeader>
              <CardTitle className="text-white text-sm flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                AI Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <AnimatePresence>
                {alerts.length > 0 ? (
                  <div className="space-y-3">
                    {alerts.map((alert, index) => (
                      <motion.div
                        key={index}
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        className={cn(
                          'p-3 rounded-lg border text-sm',
                          getAlertColor(alert.urgency)
                        )}
                      >
                        <div className="flex items-start gap-2">
                          {getAlertIcon(alert.type)}
                          <div className="flex-1">
                            <div className="font-medium mb-1">{alert.message}</div>
                            <div className="text-xs opacity-80">{alert.recommendation}</div>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6 text-gray-400">
                    <CheckCircle className="w-8 h-8 mx-auto mb-2" />
                    <p className="text-sm">All systems running smoothly</p>
                  </div>
                )}
              </AnimatePresence>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default PresentationControls