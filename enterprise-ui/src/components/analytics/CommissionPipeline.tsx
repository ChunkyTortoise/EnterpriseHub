'use client'

import { useState, useEffect } from 'react'
import { motion, useSpring, useTransform, animate } from 'framer-motion'
import { 
  TrendingUp, 
  DollarSign, 
  BarChart3, 
  ArrowUpRight, 
  Target,
  Percent,
  Wallet,
  Briefcase,
  Sparkles
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

function AnimatedNumber({ value, prefix = "", suffix = "", decimals = 0 }: { value: number, prefix?: string, suffix?: string, decimals?: number }) {
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    const controls = animate(displayValue, value, {
      duration: 2,
      ease: "easeOut",
      onUpdate: (latest) => setDisplayValue(latest)
    })
    return () => controls.stop()
  }, [value])

  return (
    <span aria-live="polite" aria-atomic="true">
      <span className="sr-only">{prefix}{value.toFixed(decimals)}{suffix}</span>
      <span aria-hidden="true">{prefix}{displayValue.toFixed(decimals)}{suffix}</span>
    </span>
  )
}

interface PipelineMetrics {
  totalValue: number
  projectedCommission: number
  dealsInProgress: number
  conversionRate: number
  avgSalePrice: number
  targets: {
    monthly: number
    current: number
  }
}

const mockMetrics: PipelineMetrics = {
  totalValue: 12500000,
  projectedCommission: 750000,
  dealsInProgress: 14,
  conversionRate: 68,
  avgSalePrice: 892000,
  targets: {
    monthly: 1000000,
    current: 750000
  }
}

export function CommissionPipeline() {
  const [metrics, setMetrics] = useState<PipelineMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const timer = setTimeout(() => {
      setMetrics(mockMetrics)
      setLoading(false)
    }, 800)
    return () => clearTimeout(timer)
  }, [])

  if (loading || !metrics) {
    return (
      <Card className="jorge-card border-none bg-[#0f0f0f]/50 backdrop-blur-xl h-full animate-pulse">
        <div className="p-6 space-y-6">
          <div className="h-4 bg-white/5 rounded w-1/3" />
          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className="h-3 bg-white/5 rounded w-1/2" />
              <div className="h-8 bg-white/10 rounded w-full" />
            </div>
            <div className="space-y-2">
              <div className="h-3 bg-white/5 rounded w-1/2" />
              <div className="h-8 bg-white/10 rounded w-full" />
            </div>
          </div>
          <div className="h-2 bg-white/5 rounded w-full" />
          <div className="grid grid-cols-3 gap-3">
            {[1, 2, 3].map(i => <div key={i} className="h-20 bg-white/5 rounded-2xl" />)}
          </div>
        </div>
      </Card>
    )
  }

  const targetProgress = (metrics.targets.current / metrics.targets.monthly) * 100

  return (
    <Card 
      className="jorge-card border-none bg-[#0f0f0f]/50 backdrop-blur-xl h-full group overflow-hidden"
      role="region"
      aria-label="6% Commission Pipeline"
    >
      <CardHeader className="pb-2 border-b border-white/5 relative">
        <div className="absolute top-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-jorge-gold/50 to-transparent" />
        
        <div className="flex items-center justify-between relative z-10">
          <CardTitle className="text-sm font-bold flex items-center gap-2 text-white">
            <motion.div
              animate={{ rotate: [0, 5, -5, 0] }}
              transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
              aria-hidden="true"
            >
              <Briefcase className="w-4 h-4 text-jorge-gold" />
            </motion.div>
            6% Commission Pipeline
          </CardTitle>
          <Badge variant="outline" className="text-[10px] jorge-code border-jorge-gold/30 text-jorge-gold bg-jorge-gold/5">
            <Sparkles className="w-3 h-3 mr-1 animate-pulse" aria-hidden="true" />
            ELITE BI
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-6 space-y-6">
        {/* Main Stats */}
        <div className="grid grid-cols-2 gap-6">
          <motion.div 
            whileHover={{ scale: 1.02 }}
            className="space-y-1 group/stat cursor-default"
            tabIndex={0}
          >
            <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold group-hover/stat:text-jorge-gold transition-colors">Projected Revenue</span>
            <div className="flex items-baseline gap-1">
              <span className="text-3xl font-bold text-white tracking-tighter">
                <AnimatedNumber value={metrics.projectedCommission / 1000} prefix="$" suffix="k" />
              </span>
              <motion.span 
                initial={{ opacity: 0, x: -5 }}
                animate={{ opacity: 1, x: 0 }}
                className="text-[10px] text-green-400 font-bold flex items-center"
                aria-label="12% increase"
              >
                <ArrowUpRight className="w-3 h-3 mr-0.5" aria-hidden="true" />
                12%
              </motion.span>
            </div>
          </motion.div>
          <motion.div 
            whileHover={{ scale: 1.02 }}
            className="space-y-1 group/stat cursor-default"
            tabIndex={0}
          >
            <span className="text-[10px] text-gray-500 uppercase tracking-widest font-bold group-hover/stat:text-jorge-gold transition-colors">Pipeline Value</span>
            <div className="flex items-baseline gap-1">
              <span className="text-3xl font-bold text-jorge-gold tracking-tighter">
                <AnimatedNumber value={metrics.totalValue / 1000000} prefix="$" suffix="M" decimals={1} />
              </span>
            </div>
          </motion.div>
        </div>

        {/* Goal Progress */}
        <div className="space-y-3" role="progressbar" aria-valuenow={targetProgress} aria-valuemin={0} aria-valuemax={100} aria-label="Monthly revenue goal progress">
          <div className="flex justify-between items-end">
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400 font-bold uppercase tracking-tighter">Monthly Revenue Goal</span>
              <div className="h-1 w-1 rounded-full bg-jorge-gold animate-ping" aria-hidden="true" />
            </div>
            <span className="text-[11px] text-white jorge-code font-bold">
              <AnimatedNumber value={metrics.targets.current / 1000} prefix="$" suffix="k" /> / <span className="text-gray-500">${(metrics.targets.monthly / 1000).toFixed(0)}k</span>
            </span>
          </div>
          <div className="h-2.5 bg-white/5 rounded-full overflow-hidden relative">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${targetProgress}%` }}
              transition={{ duration: 2, ease: "easeOut" }}
              className="h-full bg-gradient-to-r from-jorge-gold via-yellow-400 to-jorge-gold relative"
            >
              {/* Shimmer effect */}
              <motion.div
                animate={{ x: ["-100%", "200%"] }}
                transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent w-1/2"
                aria-hidden="true"
              />
            </motion.div>
          </div>
        </div>

        {/* Grid Metrics */}
        <div className="grid grid-cols-3 gap-3">
          {[
            { icon: <Target className="w-4 h-4 text-purple-400" aria-hidden="true" />, value: metrics.dealsInProgress, label: "Active Deals" },
            { icon: <Percent className="w-4 h-4 text-blue-400" aria-hidden="true" />, value: metrics.conversionRate, label: "Conversion", suffix: "%" },
            { icon: <TrendingUp className="w-4 h-4 text-green-400" aria-hidden="true" />, value: metrics.avgSalePrice / 1000, label: "Avg Price", prefix: "$", suffix: "k" }
          ].map((item, i) => (
            <motion.div 
              key={i}
              whileHover={{ y: -4, backgroundColor: "rgba(255, 255, 255, 0.08)" }}
              className="p-3 bg-white/5 rounded-2xl border border-white/5 text-center transition-colors group/item"
              tabIndex={0}
            >
              <div className="mb-2 flex justify-center group-hover/item:scale-110 transition-transform">
                {item.icon}
              </div>
              <div className="text-xl font-bold text-white tracking-tighter">
                <AnimatedNumber value={item.value} prefix={item.prefix} suffix={item.suffix} />
              </div>
              <div className="text-[9px] text-gray-500 uppercase font-bold tracking-widest">{item.label}</div>
            </motion.div>
          ))}
        </div>

        {/* Dynamic Calculation Tooltip-style info */}
        <motion.div 
          whileHover={{ scale: 1.01 }}
          className="bg-jorge-gold/10 border border-jorge-gold/20 rounded-2xl p-4 relative group/info overflow-hidden"
          role="complementary"
          aria-label="Revenue calculation logic"
        >
          {/* Animated background glow */}
          <div className="absolute top-0 right-0 w-24 h-24 bg-jorge-gold/10 blur-3xl rounded-full group-hover/info:scale-150 transition-transform" aria-hidden="true" />
          
          <div className="flex items-center gap-2 mb-2 relative z-10">
            <DollarSign className="w-4 h-4 text-jorge-gold" aria-hidden="true" />
            <span className="text-[11px] font-bold text-jorge-gold uppercase tracking-widest">Automatic 6% Logic</span>
          </div>
          <p className="text-[11px] text-jorge-gold/80 leading-relaxed relative z-10">
            Jorge automatically calculates potential revenue based on <span className="text-jorge-gold font-bold">Zillow-defensive CMAs</span> and ML-predicted floor prices, ensuring you always know your exact pipeline value.
          </p>
        </motion.div>
      </CardContent>
    </Card>
  )
}

  )
}
