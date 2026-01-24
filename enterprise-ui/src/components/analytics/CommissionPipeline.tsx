'use client'

import { motion } from 'framer-motion'
import { 
  TrendingUp, 
  DollarSign, 
  BarChart3, 
  ArrowUpRight, 
  Target,
  Percent,
  Wallet,
  Briefcase
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

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
  const metrics = mockMetrics
  const targetProgress = (metrics.targets.current / metrics.targets.monthly) * 100

  return (
    <Card className="jorge-card border-none bg-[#0f0f0f]/50 backdrop-blur-xl h-full">
      <CardHeader className="pb-2 border-b border-white/5">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-bold flex items-center gap-2 text-white">
            <Briefcase className="w-4 h-4 text-jorge-gold" />
            6% Commission Pipeline
          </CardTitle>
          <Badge variant="outline" className="text-[10px] jorge-code border-jorge-gold/30 text-jorge-gold">
            PHASE 4 BI
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-6 space-y-6">
        {/* Main Stats */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <span className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Projected Revenue</span>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-white">${(metrics.projectedCommission / 1000).toFixed(0)}k</span>
              <span className="text-[10px] text-green-400 font-bold flex items-center">
                <ArrowUpRight className="w-2 h-2 mr-0.5" />
                12%
              </span>
            </div>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Pipeline Value</span>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-jorge-gold">${(metrics.totalValue / 1000000).toFixed(1)}M</span>
            </div>
          </div>
        </div>

        {/* Goal Progress */}
        <div className="space-y-2">
          <div className="flex justify-between items-end">
            <span className="text-[10px] text-gray-400 font-bold">Monthly Revenue Goal</span>
            <span className="text-[10px] text-white jorge-code">${(metrics.targets.current / 1000).toFixed(0)}k / ${(metrics.targets.monthly / 1000).toFixed(0)}k</span>
          </div>
          <div className="h-2 bg-white/5 rounded-full overflow-hidden">
            <motion.div 
              initial={{ width: 0 }}
              animate={{ width: `${targetProgress}%` }}
              transition={{ duration: 1, ease: "easeOut" }}
              className="h-full bg-gradient-to-r from-jorge-gold to-yellow-500"
            />
          </div>
        </div>

        {/* Grid Metrics */}
        <div className="grid grid-cols-3 gap-2">
          <div className="p-3 bg-white/5 rounded-xl border border-white/5 text-center">
            <Target className="w-4 h-4 text-purple-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-white">{metrics.dealsInProgress}</div>
            <div className="text-[9px] text-gray-500 uppercase">Active Deals</div>
          </div>
          <div className="p-3 bg-white/5 rounded-xl border border-white/5 text-center">
            <Percent className="w-4 h-4 text-blue-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-white">{metrics.conversionRate}%</div>
            <div className="text-[9px] text-gray-500 uppercase">Conversion</div>
          </div>
          <div className="p-3 bg-white/5 rounded-xl border border-white/5 text-center">
            <TrendingUp className="w-4 h-4 text-green-400 mx-auto mb-1" />
            <div className="text-lg font-bold text-white">${(metrics.avgSalePrice / 1000).toFixed(0)}k</div>
            <div className="text-[9px] text-gray-500 uppercase">Avg Price</div>
          </div>
        </div>

        {/* Dynamic Calculation Tooltip-style info */}
        <div className="bg-jorge-gold/10 border border-jorge-gold/20 rounded-lg p-3">
          <div className="flex items-center gap-2 mb-1">
            <DollarSign className="w-3 h-3 text-jorge-gold" />
            <span className="text-[10px] font-bold text-jorge-gold uppercase">Automatic 6% Logic</span>
          </div>
          <p className="text-[10px] text-jorge-gold/80 leading-relaxed">
            Jorge automatically calculates potential revenue based on Zillow-defensive CMAs and ML-predicted floor prices.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
