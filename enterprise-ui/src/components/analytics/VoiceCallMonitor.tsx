'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Phone, 
  PhoneForwarded, 
  PhoneOff, 
  Mic, 
  Activity, 
  User, 
  Clock,
  Volume2,
  Waves
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

interface ActiveCall {
  id: string
  leadName: string
  status: 'connecting' | 'active' | 'analyzing' | 'completed'
  duration: number
  sentiment: 'positive' | 'neutral' | 'negative'
  transcriptionSnippet: string
}

const mockActiveCalls: ActiveCall[] = [
  {
    id: 'call-1',
    leadName: 'Sarah Johnson',
    status: 'active',
    duration: 145,
    sentiment: 'positive',
    transcriptionSnippet: "...actually I was thinking about selling my property in the next 3 months if the price is right..."
  }
]

export function VoiceCallMonitor() {
  const [activeCalls, setActiveCalls] = useState<ActiveCall[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setActiveCalls(mockActiveCalls)
      setLoading(false)
    }, 1500)
    return () => clearTimeout(timer)
  }, [])

  // Simulate duration ticking
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveCalls(calls => 
        calls.map(call => 
          call.status === 'active' 
            ? { ...call, duration: call.duration + 1 } 
            : call
        )
      )
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <Card className="jorge-card border-none bg-[#0f0f0f]/50 backdrop-blur-xl">
      <CardHeader className="pb-2 border-b border-white/5">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-bold flex items-center gap-2 text-white">
            <Phone className="w-4 h-4 text-blue-400" />
            Retell AI Voice Monitor
          </CardTitle>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-[10px] jorge-code text-gray-400">VOICE ENGINE ACTIVE</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-4">
        {loading ? (
          <div className="h-32 flex items-center justify-center">
            <Activity className="w-6 h-6 text-blue-500 animate-spin" />
          </div>
        ) : activeCalls.length > 0 ? (
          <div className="space-y-4">
            <AnimatePresence>
              {activeCalls.map(call => (
                <motion.div
                  key={call.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="bg-white/5 rounded-xl border border-white/10 p-4 relative overflow-hidden"
                >
                  {/* Background Waveform Animation */}
                  <div className="absolute inset-0 opacity-10 pointer-events-none flex items-center justify-center">
                    <Waves className="w-full h-full text-blue-400 animate-pulse" />
                  </div>

                  <div className="relative z-10">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-500/20 rounded-lg">
                          <User className="w-5 h-5 text-blue-400" />
                        </div>
                        <div>
                          <h4 className="text-sm font-bold text-white">{call.leadName}</h4>
                          <div className="flex items-center gap-2">
                            <Badge className="text-[10px] bg-blue-500/10 text-blue-400 border-none h-4">
                              {call.status.toUpperCase()}
                            </Badge>
                            <span className="text-[10px] text-gray-500 jorge-code">
                              {formatDuration(call.duration)}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex flex-col items-end gap-1">
                        <div className="flex items-center gap-1">
                          <Mic className="w-3 h-3 text-red-400 animate-pulse" />
                          <span className="text-[10px] text-red-400 jorge-code uppercase">Recording</span>
                        </div>
                        <div className={cn(
                          "text-[10px] font-bold px-2 py-0.5 rounded-full",
                          call.sentiment === 'positive' ? "bg-green-500/10 text-green-400" :
                          call.sentiment === 'negative' ? "bg-red-500/10 text-red-400" :
                          "bg-yellow-500/10 text-yellow-400"
                        )}>
                          Sentiment: {call.sentiment.toUpperCase()}
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-[10px] text-gray-500 mb-1">
                        <span>Live Transcription Snippet</span>
                        <Volume2 className="w-3 h-3" />
                      </div>
                      <div className="bg-black/40 rounded-lg p-3 border border-white/5 italic text-xs text-gray-300 line-clamp-2">
                        &quot;{call.transcriptionSnippet}&quot;
                      </div>
                    </div>

                    <div className="mt-4 flex gap-2">
                      <Progress value={75} className="h-1 bg-white/5" />
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        ) : (
          <div className="text-center py-8">
            <PhoneOff className="w-8 h-8 text-gray-600 mx-auto mb-2 opacity-20" />
            <p className="text-xs text-gray-500">No active voice calls</p>
            <p className="text-[10px] text-gray-600 mt-1">Next scheduled: Day 7 follow-up for Sarah J.</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
