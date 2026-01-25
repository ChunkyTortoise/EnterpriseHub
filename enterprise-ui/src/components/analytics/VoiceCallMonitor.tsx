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
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const timer = setTimeout(() => {
      try {
        setActiveCalls(mockActiveCalls)
        setLoading(false)
      } catch (err) {
        setError('Failed to load voice monitor')
        setLoading(false)
      }
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
    <Card 
      className="jorge-card border-none bg-[#0f0f0f]/50 backdrop-blur-xl group overflow-hidden"
      role="region"
      aria-label="Retell AI Voice Monitor"
    >
      <CardHeader className="pb-2 border-b border-white/5 relative">
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-blue-400/50 to-transparent" />
        
        <div className="flex items-center justify-between relative z-10">
          <CardTitle className="text-sm font-bold flex items-center gap-2 text-white">
            <motion.div
              animate={{ scale: [1, 1.1, 1] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              aria-hidden="true"
            >
              <Phone className="w-4 h-4 text-blue-400" />
            </motion.div>
            Retell AI Voice Monitor
          </CardTitle>
          <div className="flex items-center gap-2" aria-live="polite">
            <motion.div 
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" 
              aria-hidden="true"
            />
            <span className="text-[10px] jorge-code text-gray-400">VOICE ENGINE LIVE</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-4">
        {loading ? (
          <div className="h-32 flex items-center justify-center" aria-busy="true" aria-label="Connecting to voice engine">
            <div className="relative">
              <Activity className="w-8 h-8 text-blue-500 animate-spin opacity-20" aria-hidden="true" />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-ping" />
              </div>
            </div>
            {/* Skeleton for call card */}
            <div className="hidden">
              <div className="w-full h-24 bg-white/5 animate-pulse rounded-xl" />
            </div>
          </div>
        ) : error ? (
          <div className="py-8 text-center space-y-3 text-red-400">
            <PhoneOff className="w-8 h-8 mx-auto opacity-50" aria-hidden="true" />
            <p className="text-xs jorge-code">{error}</p>
          </div>
        ) : activeCalls.length > 0 ? (
          <div className="space-y-4">
            <AnimatePresence mode="popLayout">
              {activeCalls.map(call => (
                <motion.div
                  key={call.id}
                  initial={{ opacity: 0, scale: 0.95, y: 10 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.95, x: 20 }}
                  whileHover={{ scale: 1.01 }}
                  className="bg-white/5 rounded-xl border border-white/10 p-4 relative overflow-hidden transition-colors hover:bg-white/10 group/call"
                  role="status"
                  aria-label={`Active call with ${call.leadName}`}
                >
                  {/* Background Waveform Animation */}
                  <div className="absolute inset-0 opacity-10 pointer-events-none flex items-center justify-around px-4" aria-hidden="true">
                    {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                      <motion.div
                        key={i}
                        animate={{ 
                          height: [10, 40, 10, 30, 10],
                          opacity: [0.3, 0.6, 0.3]
                        }}
                        transition={{ 
                          duration: 1.5 + (i * 0.2), 
                          repeat: Infinity, 
                          ease: "easeInOut" 
                        }}
                        className="w-[2px] bg-blue-400 rounded-full"
                      />
                    ))}
                  </div>

                  <div className="relative z-10">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-500/20 rounded-lg group-hover/call:bg-blue-500/30 transition-colors">
                          <User className="w-5 h-5 text-blue-400" aria-hidden="true" />
                        </div>
                        <div>
                          <h4 className="text-sm font-bold text-white group-hover/call:text-blue-300 transition-colors">
                            {call.leadName}
                          </h4>
                          <div className="flex items-center gap-2">
                            <Badge className="text-[10px] bg-blue-500/10 text-blue-400 border-none h-4 px-1.5">
                              {call.status.toUpperCase()}
                            </Badge>
                            <span className="text-[10px] text-gray-500 jorge-code group-hover/call:text-gray-400" aria-label={`Duration: ${formatDuration(call.duration)}`}>
                              {formatDuration(call.duration)}
                            </span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex flex-col items-end gap-1">
                        <div className="flex items-center gap-1.5">
                          <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                          </span>
                          <span className="text-[10px] text-red-400 jorge-code uppercase tracking-tighter">Recording</span>
                        </div>
                        <motion.div 
                          layout
                          className={cn(
                            "text-[10px] font-bold px-2.5 py-0.5 rounded-full border",
                            call.sentiment === 'positive' ? "bg-green-500/10 text-green-400 border-green-500/20" :
                            call.sentiment === 'negative' ? "bg-red-500/10 text-red-400 border-red-500/20" :
                            "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
                          )}
                          aria-label={`Sentiment: ${call.sentiment}`}
                        >
                          Sentiment: {call.sentiment.toUpperCase()}
                        </motion.div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-[10px] text-gray-500 mb-1 font-bold tracking-widest uppercase">
                        <span>Live AI Transcription</span>
                        <div className="flex gap-0.5" aria-hidden="true">
                          <motion.div animate={{ height: [2, 8, 2] }} transition={{ repeat: Infinity, duration: 0.8 }} className="w-[1px] bg-blue-400" />
                          <motion.div animate={{ height: [4, 12, 4] }} transition={{ repeat: Infinity, duration: 0.8, delay: 0.2 }} className="w-[1px] bg-blue-400" />
                          <motion.div animate={{ height: [2, 6, 2] }} transition={{ repeat: Infinity, duration: 0.8, delay: 0.4 }} className="w-[1px] bg-blue-400" />
                        </div>
                      </div>
                      <div 
                        className="bg-black/60 rounded-xl p-3 border border-white/5 italic text-xs text-gray-300 line-clamp-2 min-h-[3rem] group-hover/call:border-blue-500/20 transition-all"
                        aria-live="polite"
                      >
                        <motion.span
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ duration: 0.5 }}
                        >
                          &quot;{call.transcriptionSnippet}&quot;
                        </motion.span>
                      </div>
                    </div>

                    <div className="mt-4 flex gap-2 relative h-1 bg-white/5 rounded-full overflow-hidden">
                      <motion.div 
                        className="absolute inset-0 bg-gradient-to-r from-blue-600 via-blue-400 to-blue-600"
                        animate={{ 
                          x: ["-100%", "100%"],
                        }}
                        transition={{ 
                          duration: 3, 
                          repeat: Infinity, 
                          ease: "linear" 
                        }}
                        style={{ width: '30%' }}
                        aria-hidden="true"
                      />
                      <Progress 
                        value={75} 
                        className="h-1 bg-transparent" 
                        aria-label="Call progress"
                      />
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        ) : (
          <div className="text-center py-12 bg-white/2 rounded-2xl border border-dashed border-white/5">
            <PhoneOff className="w-10 h-10 text-gray-700 mx-auto mb-3 opacity-20" aria-hidden="true" />
            <p className="text-sm font-semibold text-gray-500">No active voice calls</p>
            <p className="text-[10px] text-gray-600 mt-2 jorge-code uppercase tracking-tighter">
              Next scheduled: Day 7 follow-up for Sarah J.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
