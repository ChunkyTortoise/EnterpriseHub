'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Brain, 
  Zap, 
  Target, 
  AlertCircle, 
  ArrowRight, 
  CheckCircle2, 
  MessageSquare,
  TrendingUp,
  Clock,
  ChevronRight
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export interface BotInsight {
  id: string
  type: 'lead' | 'system' | 'market'
  severity: 'high' | 'medium' | 'low'
  title: string
  description: string
  actionLabel?: string
  botId: string
  timestamp: string
}

const mockInsights: BotInsight[] = [
  {
    id: 'insight-1',
    type: 'lead',
    severity: 'high',
    title: 'High-Intent Lead Detected',
    description: 'Lead in Zilker (Austin) showed 95% psychological commitment (PCS). Recommend immediate Day 7 Voice Call trigger.',
    actionLabel: 'Trigger Voice Call',
    botId: 'intent-decoder',
    timestamp: new Date().toISOString()
  },
  {
    id: 'insight-2',
    type: 'market',
    severity: 'medium',
    title: 'Market Shift: Westlake',
    description: 'Inventory levels in Westlake decreased by 12% this week. Adjust pricing strategies for active sellers.',
    actionLabel: 'Update Pricing',
    botId: 'jorge-seller-bot',
    timestamp: new Date(Date.now() - 3600000).toISOString()
  },
  {
    id: 'insight-3',
    type: 'system',
    severity: 'low',
    title: 'Automation Sequence Optimized',
    description: '3-7-30 sequence for "Warm" leads now seeing 15% higher engagement with CMA value injection.',
    botId: 'lead-bot',
    timestamp: new Date(Date.now() - 7200000).toISOString()
  }
]

export function BotInsightsPanel() {
  const [insights, setInsights] = useState<BotInsight[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Simulate loading insights
    const timer = setTimeout(() => {
      try {
        setInsights(mockInsights)
        setLoading(false)
      } catch (err) {
        setError('Failed to load insights')
        setLoading(false)
      }
    }, 1000)
    return () => clearTimeout(timer)
  }, [])

  const getSeverityStyles = (severity: BotInsight['severity']) => {
    switch (severity) {
      case 'high':
        return 'border-l-red-500 bg-red-500/5'
      case 'medium':
        return 'border-l-yellow-500 bg-yellow-500/5'
      case 'low':
        return 'border-l-blue-500 bg-blue-500/5'
      default:
        return 'border-l-gray-500 bg-gray-500/5'
    }
  }

  const getTypeIcon = (type: BotInsight['type']) => {
    switch (type) {
      case 'lead':
        return <Target className="w-4 h-4 text-red-400" aria-hidden="true" />
      case 'market':
        return <TrendingUp className="w-4 h-4 text-yellow-400" aria-hidden="true" />
      case 'system':
        return <Zap className="w-4 h-4 text-blue-400" aria-hidden="true" />
    }
  }

  return (
    <Card 
      className="jorge-card overflow-hidden border-none bg-[#0f0f0f]/50 backdrop-blur-xl group"
      role="region"
      aria-label="Agentic UI Suggestions"
    >
      <CardHeader className="pb-2 border-b border-white/5 relative overflow-hidden">
        {/* Animated header glow */}
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-jorge-electric/50 to-transparent" />
        
        <div className="flex items-center justify-between relative z-10">
          <CardTitle className="text-sm font-bold flex items-center gap-2 text-white">
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              aria-hidden="true"
            >
              <Brain className="w-4 h-4 text-jorge-electric" />
            </motion.div>
            Agentic UI Suggestions
          </CardTitle>
          <Badge 
            variant="outline" 
            className="text-[10px] jorge-code border-jorge-electric/30 text-jorge-electric bg-jorge-electric/5"
            aria-live="polite"
          >
            <span className="relative flex h-1.5 w-1.5 mr-1.5" aria-hidden="true">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-jorge-electric opacity-75"></span>
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-jorge-electric"></span>
            </span>
            LIVE INSIGHTS
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="max-h-[400px] overflow-y-auto custom-scrollbar">
          {loading ? (
            <div className="p-8 text-center space-y-4" aria-busy="true" aria-label="Analyzing data">
              <div className="flex justify-center">
                <Brain className="w-8 h-8 text-jorge-electric animate-pulse" aria-hidden="true" />
              </div>
              <p className="text-xs text-gray-500 jorge-code">Jorge-Brain is analyzing data...</p>
              
              {/* Skeleton UI */}
              <div className="space-y-4 mt-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="flex gap-4 p-4 border-l-2 border-white/5 bg-white/5 animate-pulse rounded-r-lg">
                    <div className="w-4 h-4 bg-white/10 rounded-full" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-white/10 rounded w-3/4" />
                      <div className="h-3 bg-white/5 rounded w-full" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : error ? (
            <div className="p-8 text-center space-y-4 text-red-400">
              <AlertCircle className="w-8 h-8 mx-auto opacity-50" />
              <p className="text-xs jorge-code">{error}</p>
              <Button 
                variant="outline" 
                size="sm" 
                className="text-[10px] h-7 border-red-500/20 hover:bg-red-500/10"
                onClick={() => { setError(null); setLoading(true); }}
              >
                Retry Analysis
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-white/5">
              <AnimatePresence mode="popLayout">
                {insights.map((insight, index) => (
                  <motion.div
                    key={insight.id}
                    initial={{ opacity: 0, y: 10, filter: 'blur(4px)' }}
                    animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                    exit={{ opacity: 0, x: -20, filter: 'blur(4px)' }}
                    transition={{ 
                      type: "spring",
                      stiffness: 260,
                      damping: 20,
                      delay: index * 0.1 
                    }}
                    whileHover={{ backgroundColor: "rgba(255, 255, 255, 0.03)" }}
                    className={cn(
                      "p-4 border-l-2 transition-all duration-300 relative group/item",
                      getSeverityStyles(insight.severity)
                    )}
                    tabIndex={0}
                    role="article"
                    aria-labelledby={`insight-title-${insight.id}`}
                  >
                    {/* Hover Glow Effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-jorge-electric/0 via-jorge-electric/[0.02] to-transparent opacity-0 group-hover/item:opacity-100 transition-opacity pointer-events-none" />

                    <div className="flex items-start justify-between gap-4 relative z-10">
                      <div className="flex-1 space-y-1">
                        <div className="flex items-center gap-2">
                          {getTypeIcon(insight.type)}
                          <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                            {insight.type}
                          </span>
                          <span className="text-[10px] text-gray-600 jorge-code">
                            {new Date(insight.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        <h4 
                          id={`insight-title-${insight.id}`}
                          className="text-sm font-semibold text-white leading-tight group-hover/item:text-jorge-electric transition-colors"
                        >
                          {insight.title}
                        </h4>
                        <p className="text-xs text-gray-400 leading-relaxed">
                          {insight.description}
                        </p>
                      </div>
                      
                      {insight.severity === 'high' && (
                        <motion.div 
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{ duration: 2, repeat: Infinity }}
                          className="flex-shrink-0"
                          aria-label="High Priority"
                        >
                          <AlertCircle className="w-5 h-5 text-red-500 shadow-[0_0_10px_rgba(239,68,68,0.3)]" />
                        </motion.div>
                      )}
                    </div>
                    
                    {insight.actionLabel && (
                      <div className="mt-3 flex items-center justify-between relative z-10">
                        <motion.div
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          <Button 
                            size="sm" 
                            className="h-7 text-[10px] bg-jorge-electric hover:bg-blue-600 text-white border-none rounded-full px-3 shadow-[0_0_15px_rgba(0,112,243,0.2)] hover:shadow-[0_0_20px_rgba(0,112,243,0.4)] transition-all"
                            aria-label={`${insight.actionLabel}: ${insight.title}`}
                          >
                            {insight.actionLabel}
                            <ChevronRight className="w-3 h-3 ml-1" aria-hidden="true" />
                          </Button>
                        </motion.div>
                        <div className="text-[10px] text-gray-600 jorge-code group-hover/item:text-gray-400 transition-colors">
                          via {insight.botId}
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
        
        {!loading && !error && (
          <div className="p-3 bg-white/5 border-t border-white/5 text-center group/footer">
            <Button 
              variant="ghost" 
              size="sm" 
              className="w-full h-8 text-[10px] text-gray-500 hover:text-white hover:bg-white/5 transition-all"
            >
              <span className="mr-2">View All Insights</span>
              <motion.div
                animate={{ x: [0, 4, 0] }}
                transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                aria-hidden="true"
              >
                <ArrowRight className="w-3 h-3" />
              </motion.div>
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
