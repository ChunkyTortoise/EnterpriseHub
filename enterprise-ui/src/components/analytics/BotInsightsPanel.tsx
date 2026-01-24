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

  useEffect(() => {
    // Simulate loading insights
    const timer = setTimeout(() => {
      setInsights(mockInsights)
      setLoading(false)
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
        return <Target className="w-4 h-4 text-red-400" />
      case 'market':
        return <TrendingUp className="w-4 h-4 text-yellow-400" />
      case 'system':
        return <Zap className="w-4 h-4 text-blue-400" />
    }
  }

  return (
    <Card className="jorge-card overflow-hidden border-none bg-[#0f0f0f]/50 backdrop-blur-xl">
      <CardHeader className="pb-2 border-b border-white/5">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-bold flex items-center gap-2 text-white">
            <Brain className="w-4 h-4 text-jorge-electric" />
            Agentic UI Suggestions
          </CardTitle>
          <Badge variant="outline" className="text-[10px] jorge-code border-jorge-electric/30 text-jorge-electric">
            LIVE INSIGHTS
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="max-h-[400px] overflow-y-auto custom-scrollbar">
          {loading ? (
            <div className="p-8 text-center space-y-4">
              <div className="flex justify-center">
                <Brain className="w-8 h-8 text-jorge-electric animate-pulse" />
              </div>
              <p className="text-xs text-gray-500 jorge-code">Jorge-Brain is analyzing data...</p>
            </div>
          ) : (
            <div className="divide-y divide-white/5">
              <AnimatePresence initial={false}>
                {insights.map((insight, index) => (
                  <motion.div
                    key={insight.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className={cn(
                      "p-4 border-l-2 transition-colors hover:bg-white/5",
                      getSeverityStyles(insight.severity)
                    )}
                  >
                    <div className="flex items-start justify-between gap-4">
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
                        <h4 className="text-sm font-semibold text-white leading-tight">
                          {insight.title}
                        </h4>
                        <p className="text-xs text-gray-400 leading-relaxed">
                          {insight.description}
                        </p>
                      </div>
                      
                      {insight.severity === 'high' && (
                        <div className="flex-shrink-0">
                          <AlertCircle className="w-5 h-5 text-red-500 animate-pulse" />
                        </div>
                      )}
                    </div>
                    
                    {insight.actionLabel && (
                      <div className="mt-3 flex items-center justify-between">
                        <Button 
                          size="sm" 
                          className="h-7 text-[10px] bg-jorge-electric hover:bg-blue-600 text-white border-none rounded-full px-3"
                        >
                          {insight.actionLabel}
                          <ChevronRight className="w-3 h-3 ml-1" />
                        </Button>
                        <div className="text-[10px] text-gray-600 jorge-code">
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
        
        {!loading && (
          <div className="p-3 bg-white/5 border-t border-white/5 text-center">
            <Button variant="ghost" size="sm" className="w-full h-8 text-[10px] text-gray-400 hover:text-white hover:bg-transparent">
              View All Insights
              <ArrowRight className="w-3 h-3 ml-2" />
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
