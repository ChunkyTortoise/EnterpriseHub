// Live Presentation Component
// Full-screen client-facing presentation interface with real-time controls

'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  Play,
  Pause,
  Square,
  SkipForward,
  SkipBack,
  Maximize,
  Minimize,
  Volume2,
  VolumeX,
  Settings,
  Users,
  Eye,
  MousePointer2,
  Mic,
  MicOff,
  Camera,
  CameraOff,
  Share,
  Download,
  Printer
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent } from '@/components/ui/card'
import { motion, AnimatePresence } from 'framer-motion'
import { cn } from '@/lib/utils'

interface LivePresentationProps {
  sessionId: string
  clientName: string
  currentSlide: number
  totalSlides: number
  isPlaying: boolean
  isFullScreen: boolean
  showControls: boolean
  showAnalytics: boolean
  engagementScore: number
  attentionLevel: number
  onPlay: () => void
  onPause: () => void
  onStop: () => void
  onNext: () => void
  onPrevious: () => void
  onFullScreen: () => void
  onToggleControls: () => void
  onToggleAnalytics: () => void
  children: React.ReactNode
}

export function LivePresentation({
  sessionId,
  clientName,
  currentSlide,
  totalSlides,
  isPlaying,
  isFullScreen,
  showControls,
  showAnalytics,
  engagementScore,
  attentionLevel,
  onPlay,
  onPause,
  onStop,
  onNext,
  onPrevious,
  onFullScreen,
  onToggleControls,
  onToggleAnalytics,
  children
}: LivePresentationProps) {
  const [volume, setVolume] = useState([80])
  const [isMuted, setIsMuted] = useState(false)
  const [isMicActive, setIsMicActive] = useState(false)
  const [isCameraActive, setIsCameraActive] = useState(false)
  const [cursorVisible, setCursorVisible] = useState(true)
  const [lastActivity, setLastActivity] = useState(Date.now())
  const cursorTimerRef = useRef<NodeJS.Timeout>()

  const progress = ((currentSlide + 1) / totalSlides) * 100

  // Auto-hide cursor in fullscreen mode
  useEffect(() => {
    if (!isFullScreen) return

    const handleMouseMove = () => {
      setCursorVisible(true)
      setLastActivity(Date.now())

      if (cursorTimerRef.current) {
        clearTimeout(cursorTimerRef.current)
      }

      cursorTimerRef.current = setTimeout(() => {
        setCursorVisible(false)
      }, 3000)
    }

    document.addEventListener('mousemove', handleMouseMove)

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      if (cursorTimerRef.current) {
        clearTimeout(cursorTimerRef.current)
      }
    }
  }, [isFullScreen])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      switch (event.key) {
        case ' ':
        case 'Enter':
          event.preventDefault()
          if (isPlaying) {
            onPause()
          } else {
            onPlay()
          }
          break
        case 'ArrowRight':
          event.preventDefault()
          onNext()
          break
        case 'ArrowLeft':
          event.preventDefault()
          onPrevious()
          break
        case 'f':
        case 'F11':
          event.preventDefault()
          onFullScreen()
          break
        case 'Escape':
          if (isFullScreen) {
            onFullScreen()
          }
          break
        case 'c':
          event.preventDefault()
          onToggleControls()
          break
        case 'a':
          event.preventDefault()
          onToggleAnalytics()
          break
        case 'm':
          event.preventDefault()
          setIsMuted(!isMuted)
          break
        case 's':
          event.preventDefault()
          onStop()
          break
      }
    }

    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [isPlaying, isFullScreen, isMuted, onPlay, onPause, onNext, onPrevious, onFullScreen, onToggleControls, onToggleAnalytics, onStop])

  const getEngagementColor = (score: number) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-yellow-400'
    return 'text-red-400'
  }

  const getEngagementBadgeColor = (score: number) => {
    if (score >= 80) return 'bg-green-500/10 text-green-400 border-green-500/30'
    if (score >= 60) return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30'
    return 'bg-red-500/10 text-red-400 border-red-500/30'
  }

  return (
    <div
      className={cn(
        'relative bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900',
        isFullScreen ? 'fixed inset-0 z-50' : 'min-h-screen',
        !cursorVisible && isFullScreen && 'cursor-none'
      )}
    >
      {/* Presentation Content */}
      <div className="h-full flex flex-col">
        {/* Header Bar */}
        <AnimatePresence>
          {(!isFullScreen || (isFullScreen && cursorVisible)) && (
            <motion.div
              initial={{ y: -100 }}
              animate={{ y: 0 }}
              exit={{ y: -100 }}
              className="bg-black/20 backdrop-blur-sm border-b border-white/10 px-6 py-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="text-white font-semibold">
                    {clientName} - Presentation
                  </div>

                  <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-500/30">
                    Session {sessionId.slice(0, 8)}
                  </Badge>

                  <div className="text-sm text-gray-300">
                    Slide {currentSlide + 1} of {totalSlides}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {showAnalytics && (
                    <>
                      <Badge variant="outline" className={getEngagementBadgeColor(engagementScore)}>
                        <Eye className="w-3 h-3 mr-1" />
                        Engagement: {Math.round(engagementScore)}%
                      </Badge>

                      <Badge variant="outline" className={getEngagementBadgeColor(attentionLevel)}>
                        <MousePointer2 className="w-3 h-3 mr-1" />
                        Attention: {Math.round(attentionLevel)}%
                      </Badge>
                    </>
                  )}

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={onToggleAnalytics}
                    className="border-slate-600 text-gray-300 hover:bg-slate-800"
                  >
                    <Eye className="w-4 h-4" />
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={onFullScreen}
                    className="border-slate-600 text-gray-300 hover:bg-slate-800"
                  >
                    {isFullScreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
                  </Button>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mt-3">
                <Progress value={progress} className="h-1" />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Main Content Area */}
        <div className="flex-1 relative overflow-hidden">
          {/* Slide Content */}
          <div className="h-full flex items-center justify-center p-8">
            {children}
          </div>

          {/* Real-time Analytics Overlay */}
          <AnimatePresence>
            {showAnalytics && (
              <motion.div
                initial={{ opacity: 0, x: 300 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 300 }}
                className="absolute top-4 right-4 w-72 space-y-3"
              >
                <Card className="bg-black/40 backdrop-blur-sm border-white/10">
                  <CardContent className="p-4">
                    <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                      <Eye className="w-4 h-4" />
                      Live Analytics
                    </h4>

                    <div className="space-y-3">
                      <div>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-gray-300">Engagement Score</span>
                          <span className={getEngagementColor(engagementScore)}>
                            {Math.round(engagementScore)}%
                          </span>
                        </div>
                        <Progress value={engagementScore} className="h-1.5" />
                      </div>

                      <div>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="text-gray-300">Attention Level</span>
                          <span className={getEngagementColor(attentionLevel)}>
                            {Math.round(attentionLevel)}%
                          </span>
                        </div>
                        <Progress value={attentionLevel} className="h-1.5" />
                      </div>

                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="text-center p-2 bg-white/5 rounded">
                          <div className="text-blue-400 font-semibold">0</div>
                          <div className="text-gray-400">Questions</div>
                        </div>
                        <div className="text-center p-2 bg-white/5 rounded">
                          <div className="text-purple-400 font-semibold">0</div>
                          <div className="text-gray-400">Interactions</div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Quick Insights */}
                <Card className="bg-black/40 backdrop-blur-sm border-white/10">
                  <CardContent className="p-3">
                    <div className="text-xs text-gray-300 space-y-1">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                        <span>Client is engaged</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                        <span>Good attention level</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Bottom Controls */}
        <AnimatePresence>
          {showControls && (!isFullScreen || (isFullScreen && cursorVisible)) && (
            <motion.div
              initial={{ y: 100 }}
              animate={{ y: 0 }}
              exit={{ y: 100 }}
              className="bg-black/40 backdrop-blur-sm border-t border-white/10 px-6 py-4"
            >
              <div className="flex items-center justify-between">
                {/* Playback Controls */}
                <div className="flex items-center gap-3">
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
                    className={cn(
                      'px-6',
                      isPlaying
                        ? 'bg-amber-600 hover:bg-amber-700'
                        : 'bg-green-600 hover:bg-green-700'
                    )}
                  >
                    {isPlaying ? (
                      <>
                        <Pause className="w-4 h-4 mr-2" />
                        Pause
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 mr-2" />
                        Play
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
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setIsMuted(!isMuted)}
                      className="border-slate-600 text-gray-300 hover:bg-slate-800"
                    >
                      {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                    </Button>

                    <div className="w-20">
                      <Slider
                        value={isMuted ? [0] : volume}
                        onValueChange={setVolume}
                        max={100}
                        step={5}
                        className="w-full"
                        disabled={isMuted}
                      />
                    </div>
                  </div>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setIsMicActive(!isMicActive)}
                    className={cn(
                      'border-slate-600',
                      isMicActive
                        ? 'bg-red-500/20 text-red-300 border-red-500/30'
                        : 'text-gray-300 hover:bg-slate-800'
                    )}
                  >
                    {isMicActive ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4" />}
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setIsCameraActive(!isCameraActive)}
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

                {/* Utility Controls */}
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-slate-600 text-gray-300 hover:bg-slate-800"
                  >
                    <Share className="w-4 h-4" />
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    className="border-slate-600 text-gray-300 hover:bg-slate-800"
                  >
                    <Download className="w-4 h-4" />
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    className="border-slate-600 text-gray-300 hover:bg-slate-800"
                  >
                    <Printer className="w-4 h-4" />
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    onClick={onToggleControls}
                    className="border-slate-600 text-gray-300 hover:bg-slate-800"
                  >
                    <Settings className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Floating Quick Controls (Only in fullscreen) */}
        {isFullScreen && !showControls && (
          <motion.div
            className="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-black/60 backdrop-blur-sm rounded-full px-4 py-2 border border-white/20"
            initial={{ y: 100, opacity: 0 }}
            animate={{ y: 0, opacity: cursorVisible ? 1 : 0.3 }}
            transition={{ duration: 0.3 }}
          >
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="ghost"
                onClick={onPrevious}
                disabled={currentSlide === 0}
                className="text-white hover:bg-white/10 disabled:opacity-50"
              >
                <SkipBack className="w-4 h-4" />
              </Button>

              <Button
                size="sm"
                variant="ghost"
                onClick={isPlaying ? onPause : onPlay}
                className="text-white hover:bg-white/10"
              >
                {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </Button>

              <Button
                size="sm"
                variant="ghost"
                onClick={onNext}
                disabled={currentSlide === totalSlides - 1}
                className="text-white hover:bg-white/10 disabled:opacity-50"
              >
                <SkipForward className="w-4 h-4" />
              </Button>

              <div className="w-px h-6 bg-white/20 mx-2" />

              <div className="text-xs text-white/80 px-2">
                {currentSlide + 1} / {totalSlides}
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Keyboard Shortcuts Help (Press ?) */}
      {/* This could be toggled with a help key */}
    </div>
  )
}

export default LivePresentation