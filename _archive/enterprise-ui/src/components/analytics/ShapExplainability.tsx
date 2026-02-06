'use client'

import React from 'react'
import { motion } from 'framer-motion'
import { Info, TrendingUp, TrendingDown, Target, Zap, Clock, Brain } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ShapFeature {
  name: string
  value: number
  impact: 'positive' | 'negative' | 'neutral'
  description: string
  icon: React.ReactNode
}

interface ShapExplainabilityProps {
  baseScore: number
  finalScore: number
  features: ShapFeature[]
  className?: string
}

export function ShapExplainability({
  baseScore = 50,
  finalScore = 85,
  features = [
    { 
      name: 'Financial Readiness', 
      value: 15, 
      impact: 'positive', 
      description: 'Pre-approved with high down payment.',
      icon: <Target className="w-3 h-3" />
    },
    { 
      name: 'Psychological Commitment', 
      value: 12, 
      impact: 'positive', 
      description: 'Expressed urgent need to move for work.',
      icon: <Brain className="w-3 h-3" />
    },
    { 
      name: 'Timeline Alignment', 
      value: 10, 
      impact: 'positive', 
      description: 'Looking to close within 30 days.',
      icon: <Clock className="w-3 h-3" />
    },
    { 
      name: 'Budget Constraint', 
      value: -5, 
      impact: 'negative', 
      description: 'Budget is slightly below market average for desired area.',
      icon: <TrendingDown className="w-3 h-3" />
    },
    { 
      name: 'Engagement Quality', 
      value: 3, 
      impact: 'positive', 
      description: 'Fast response times to bot queries.',
      icon: <Zap className="w-3 h-3" />
    },
  ],
  className
}: ShapExplainabilityProps) {
  return (
    <div className={cn("p-4 bg-jorge-dark/40 border border-white/10 rounded-2xl backdrop-blur-xl", className)}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h4 className="text-white font-bold text-sm tracking-tight uppercase jorge-code">Lead Explainability</h4>
          <p className="text-[10px] text-gray-500 font-mono">SHAP Waterfall Analysis • v4.0.2</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="text-right">
            <div className="text-xs text-gray-500 font-mono uppercase">Final Score</div>
            <div className="text-xl font-black text-jorge-glow leading-none">{finalScore}</div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {/* Base Score Row */}
        <div className="relative">
          <div className="flex items-center justify-between text-[10px] text-gray-500 font-mono uppercase mb-1 px-1">
            <span>Baseline</span>
            <span>{baseScore}</span>
          </div>
          <div className="h-2 bg-white/5 rounded-full overflow-hidden">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${baseScore}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
              className="h-full bg-gray-600/50"
            />
          </div>
        </div>

        {/* Feature Impacts */}
        <div className="space-y-3 relative">
          {/* Vertical Guide Lines */}
          <div className="absolute left-[50%] top-0 bottom-0 w-px bg-white/5 -translate-x-1/2 hidden sm:block" />
          
          {features.map((feature, index) => {
            const isPositive = feature.impact === 'positive'
            const absoluteValue = Math.abs(feature.value)
            
            return (
              <motion.div 
                key={feature.name}
                initial={{ opacity: 0, x: isPositive ? 20 : -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + index * 0.1, duration: 0.5 }}
                className="group relative"
              >
                <div className="flex items-center justify-between mb-1 px-1">
                  <div className="flex items-center gap-2">
                    <div className={cn(
                      "p-1 rounded-md",
                      isPositive ? "bg-green-500/10 text-green-400" : "bg-red-500/10 text-red-400"
                    )}>
                      {feature.icon}
                    </div>
                    <span className="text-xs font-bold text-gray-300 group-hover:text-white transition-colors">
                      {feature.name}
                    </span>
                  </div>
                  <span className={cn(
                    "text-[10px] font-mono font-bold",
                    isPositive ? "text-green-400" : "text-red-400"
                  )}>
                    {isPositive ? '+' : ''}{feature.value}
                  </span>
                </div>
                
                <div className="h-3 relative flex items-center">
                  {/* Background Track */}
                  <div className="absolute inset-0 bg-white/5 rounded-full" />
                  
                  {/* Impact Bar */}
                  <div className="relative flex-1 h-full">
                    <motion.div
                      initial={{ scaleX: 0 }}
                      animate={{ scaleX: 1 }}
                      transition={{ delay: 1 + index * 0.1, duration: 0.8 }}
                      style={{ 
                        width: `${absoluteValue}%`,
                        left: isPositive ? `${baseScore}%` : `${baseScore - absoluteValue}%`,
                        originX: isPositive ? 0 : 1
                      }}
                      className={cn(
                        "absolute top-0 bottom-0 rounded-full shadow-[0_0_10px_rgba(0,0,0,0.5)]",
                        isPositive 
                          ? "bg-gradient-to-r from-blue-600 to-jorge-glow" 
                          : "bg-gradient-to-r from-red-600 to-orange-500"
                      )}
                    />
                  </div>
                </div>
                
                {/* Tooltip on hover */}
                <div className="mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <p className="text-[10px] text-gray-500 italic leading-tight pl-7">
                    {feature.description}
                  </p>
                </div>
              </motion.div>
            )
          })}
        </div>

        {/* Final Result */}
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 2, duration: 0.5 }}
          className="pt-4 border-t border-white/5"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-jorge-glow animate-pulse" />
              <span className="text-[10px] text-gray-400 font-mono uppercase">Confidence Level</span>
            </div>
            <span className="text-[10px] text-jorge-glow font-bold font-mono">98.4%</span>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
