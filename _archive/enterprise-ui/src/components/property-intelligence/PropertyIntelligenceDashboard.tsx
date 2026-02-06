// Property Intelligence Dashboard - Investment-Grade Analysis Interface
// Advanced property analysis beyond CMA generation with institutional-level insights

'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Home, TrendingUp, DollarSign, MapPin, Calculator, AlertTriangle,
  Target, BarChart3, PieChart, Activity, Star, Shield, Clock,
  Eye, Settings, ChevronRight, ArrowUp, ArrowDown, Zap,
  Building, Users, Globe, Briefcase, Award, Brain
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

// Property Intelligence Types
interface PropertyAnalysis {
  propertyId: string
  address: string
  analysisLevel: 'BASIC' | 'STANDARD' | 'PREMIUM' | 'INSTITUTIONAL'
  investmentStrategy: 'RENTAL_INCOME' | 'FIX_AND_FLIP' | 'BUY_AND_HOLD' | 'COMMERCIAL'
  scoring: {
    totalScore: number
    cashFlowScore: number
    appreciationScore: number
    riskScore: number
    projectedROI: number
  }
  marketPositioning: {
    competitiveRanking: number
    totalComps: number
    pricingStrategy: string
    absorptionRate: number
  }
  investment: {
    purchasePrice: number
    estimatedValue: number
    projectedCashFlow: number
    capRate: number
    cashOnCashReturn: number
    breakEvenAnalysis: {
      months: number
      totalCashRequired: number
    }
  }
  condition: {
    overallScore: number
    majorIssues: string[]
    improvementRecommendations: {
      item: string
      cost: number
      roiImpact: number
    }[]
  }
  neighborhood: {
    demographics: string
    growthTrend: 'increasing' | 'stable' | 'declining'
    projectedAppreciation: number
    walkScore: number
    schoolRating: number
  }
  riskAssessment: {
    overallRisk: 'low' | 'moderate' | 'high'
    factors: {
      market: number
      financial: number
      physical: number
      regulatory: number
    }
    mitigationStrategies: string[]
  }
  timestamp: string
  analysisTimeMs: number
}

// Mock property analysis data
const mockPropertyAnalysis: PropertyAnalysis = {
  propertyId: 'prop-12345',
  address: '123 Maple Street, Austin, TX 78701',
  analysisLevel: 'PREMIUM',
  investmentStrategy: 'RENTAL_INCOME',
  scoring: {
    totalScore: 87,
    cashFlowScore: 92,
    appreciationScore: 83,
    riskScore: 78,
    projectedROI: 14.2
  },
  marketPositioning: {
    competitiveRanking: 8,
    totalComps: 47,
    pricingStrategy: 'Optimal - 3% below market for quick absorption',
    absorptionRate: 65
  },
  investment: {
    purchasePrice: 485000,
    estimatedValue: 515000,
    projectedCashFlow: 2400,
    capRate: 7.8,
    cashOnCashReturn: 12.4,
    breakEvenAnalysis: {
      months: 18,
      totalCashRequired: 125000
    }
  },
  condition: {
    overallScore: 82,
    majorIssues: ['HVAC system 12+ years old', 'Minor electrical updates needed'],
    improvementRecommendations: [
      { item: 'Kitchen renovation', cost: 15000, roiImpact: 18.5 },
      { item: 'Bathroom updates', cost: 8000, roiImpact: 12.3 },
      { item: 'New flooring', cost: 12000, roiImpact: 14.7 }
    ]
  },
  neighborhood: {
    demographics: 'Young professionals, median age 32',
    growthTrend: 'increasing',
    projectedAppreciation: 6.8,
    walkScore: 78,
    schoolRating: 8
  },
  riskAssessment: {
    overallRisk: 'moderate',
    factors: {
      market: 85,
      financial: 78,
      physical: 82,
      regulatory: 90
    },
    mitigationStrategies: [
      'Diversify with additional properties in different areas',
      'Maintain 6-month emergency fund',
      'Regular property maintenance schedule'
    ]
  },
  timestamp: '2026-01-24T10:30:00Z',
  analysisTimeMs: 28500
}

function ScoreCircle({ score, label, color = 'blue' }: { score: number, label: string, color?: string }) {
  const strokeColor = {
    blue: 'stroke-blue-500',
    green: 'stroke-green-500',
    yellow: 'stroke-yellow-500',
    red: 'stroke-red-500',
    purple: 'stroke-purple-500'
  }[color]

  const textColor = {
    blue: 'text-blue-400',
    green: 'text-green-400',
    yellow: 'text-yellow-400',
    red: 'text-red-400',
    purple: 'text-purple-400'
  }[color]

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-20 h-20">
        <svg className="w-20 h-20 transform -rotate-90" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            stroke="currentColor"
            strokeWidth="6"
            fill="none"
            className="text-white/10"
          />
          {/* Progress circle */}
          <motion.circle
            cx="50"
            cy="50"
            r="45"
            stroke="currentColor"
            strokeWidth="6"
            fill="none"
            className={strokeColor}
            strokeLinecap="round"
            initial={{ strokeDasharray: "0 283" }}
            animate={{ strokeDasharray: `${(score / 100) * 283} 283` }}
            transition={{ duration: 1, ease: "easeOut" }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={cn("text-lg font-bold", textColor)}>{score}</span>
        </div>
      </div>
      <span className="text-xs text-gray-400 mt-2 text-center">{label}</span>
    </div>
  )
}

function InvestmentMetrics({ investment }: { investment: PropertyAnalysis['investment'] }) {
  return (
    <Card className="bg-white/5 border-white/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <Calculator className="w-5 h-5 text-green-500" />
          Investment Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-xs text-gray-400">Purchase Price</span>
              <span className="text-sm font-semibold text-white">${investment.purchasePrice.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-gray-400">Current Value</span>
              <span className="text-sm font-semibold text-green-400">${investment.estimatedValue.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-gray-400">Monthly Cash Flow</span>
              <span className="text-sm font-semibold text-green-400">+${investment.projectedCashFlow.toLocaleString()}</span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-xs text-gray-400">Cap Rate</span>
              <span className="text-sm font-semibold text-blue-400">{investment.capRate}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-gray-400">Cash-on-Cash</span>
              <span className="text-sm font-semibold text-blue-400">{investment.cashOnCashReturn}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-xs text-gray-400">Break Even</span>
              <span className="text-sm font-semibold text-yellow-400">{investment.breakEvenAnalysis.months} months</span>
            </div>
          </div>
        </div>

        <div className="border-t border-white/10 pt-4">
          <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-4 h-4 text-green-400" />
              <span className="text-sm font-semibold text-green-400">Strong Investment Opportunity</span>
            </div>
            <p className="text-xs text-gray-300">
              Above-market cash flow with solid appreciation potential.
              Total cash required: ${investment.breakEvenAnalysis.totalCashRequired.toLocaleString()}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function MarketPositioning({ positioning }: { positioning: PropertyAnalysis['marketPositioning'] }) {
  return (
    <Card className="bg-white/5 border-white/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <Target className="w-5 h-5 text-purple-500" />
          Market Positioning
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Competitive Ranking</span>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-white">#{positioning.competitiveRanking}</span>
              <span className="text-xs text-gray-500">of {positioning.totalComps}</span>
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Market Position</span>
              <span className="text-purple-400">{Math.round((positioning.competitiveRanking / positioning.totalComps) * 100)}th percentile</span>
            </div>
            <Progress value={((positioning.totalComps - positioning.competitiveRanking) / positioning.totalComps) * 100} className="h-2" />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-gray-400">Absorption Rate</span>
              <span className="text-blue-400">{positioning.absorptionRate}%</span>
            </div>
            <Progress value={positioning.absorptionRate} className="h-2" />
          </div>

          <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <Zap className="w-3 h-3 text-purple-400" />
              <span className="text-xs font-semibold text-purple-400 uppercase tracking-wider">Pricing Strategy</span>
            </div>
            <p className="text-xs text-gray-300">{positioning.pricingStrategy}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function RiskAssessment({ risk }: { risk: PropertyAnalysis['riskAssessment'] }) {
  const riskColor = {
    low: 'green',
    moderate: 'yellow',
    high: 'red'
  }[risk.overallRisk]

  const riskFactors = [
    { name: 'Market Risk', score: risk.factors.market, icon: <Globe className="w-4 h-4" /> },
    { name: 'Financial Risk', score: risk.factors.financial, icon: <DollarSign className="w-4 h-4" /> },
    { name: 'Physical Risk', score: risk.factors.physical, icon: <Building className="w-4 h-4" /> },
    { name: 'Regulatory Risk', score: risk.factors.regulatory, icon: <Shield className="w-4 h-4" /> }
  ]

  return (
    <Card className="bg-white/5 border-white/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <Shield className="w-5 h-5 text-yellow-500" />
          Risk Assessment
          <Badge
            variant="outline"
            className={cn(
              "ml-auto text-xs",
              riskColor === 'green' && "bg-green-500/10 text-green-400 border-green-500/20",
              riskColor === 'yellow' && "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
              riskColor === 'red' && "bg-red-500/10 text-red-400 border-red-500/20"
            )}
          >
            {risk.overallRisk.toUpperCase()}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {riskFactors.map((factor, index) => (
          <div key={index} className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-gray-400">{factor.icon}</span>
                <span className="text-sm text-white">{factor.name}</span>
              </div>
              <span className="text-sm font-semibold text-white">{factor.score}/100</span>
            </div>
            <Progress value={factor.score} className="h-1.5" />
          </div>
        ))}

        <div className="border-t border-white/10 pt-4">
          <h4 className="text-sm font-semibold text-white mb-2">Mitigation Strategies</h4>
          <div className="space-y-2">
            {risk.mitigationStrategies.map((strategy, index) => (
              <div key={index} className="flex items-start gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-yellow-400 mt-1.5 flex-shrink-0" />
                <span className="text-xs text-gray-300">{strategy}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function NeighborhoodIntelligence({ neighborhood }: { neighborhood: PropertyAnalysis['neighborhood'] }) {
  const trendIcon = {
    increasing: <ArrowUp className="w-4 h-4 text-green-400" />,
    stable: <Activity className="w-4 h-4 text-blue-400" />,
    declining: <ArrowDown className="w-4 h-4 text-red-400" />
  }[neighborhood.growthTrend]

  return (
    <Card className="bg-white/5 border-white/10">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-white">
          <MapPin className="w-5 h-5 text-cyan-500" />
          Neighborhood Intelligence
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-gray-400" />
              <span className="text-sm text-white">Demographics</span>
            </div>
            <p className="text-xs text-gray-300">{neighborhood.demographics}</p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {trendIcon}
              <span className="text-sm text-white">Growth Trend</span>
            </div>
            <p className="text-xs text-gray-300 capitalize">{neighborhood.growthTrend}</p>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <div className="text-lg font-bold text-green-400">+{neighborhood.projectedAppreciation}%</div>
            <div className="text-xs text-gray-400">Appreciation</div>
          </div>
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <div className="text-lg font-bold text-blue-400">{neighborhood.walkScore}</div>
            <div className="text-xs text-gray-400">Walk Score</div>
          </div>
          <div className="text-center p-3 bg-white/5 rounded-lg">
            <div className="text-lg font-bold text-purple-400">{neighborhood.schoolRating}/10</div>
            <div className="text-xs text-gray-400">Schools</div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

interface PropertyIntelligenceDashboardProps {
  propertyId?: string
  className?: string
}

export function PropertyIntelligenceDashboard({
  propertyId,
  className = ''
}: PropertyIntelligenceDashboardProps) {
  const [selectedTab, setSelectedTab] = useState('overview')
  const [isAnalyzing, setIsAnalyzing] = useState(false)

  // Simulate analysis loading
  useEffect(() => {
    if (propertyId) {
      setIsAnalyzing(true)
      const timer = setTimeout(() => setIsAnalyzing(false), 2000)
      return () => clearTimeout(timer)
    }
  }, [propertyId])

  const analysis = mockPropertyAnalysis

  return (
    <div className={cn("w-full space-y-6", className)}>
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white mb-2">Property Intelligence Dashboard</h1>
          <div className="flex items-center gap-3">
            <span className="text-gray-400 text-sm">{analysis.address}</span>
            <Badge className="bg-purple-500/10 text-purple-400 border-purple-500/20 text-xs">
              {analysis.analysisLevel}
            </Badge>
            <div className="flex items-center gap-1 text-xs text-gray-500">
              <Clock className="w-3 h-3" />
              {analysis.analysisTimeMs}ms analysis
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" className="border-white/20 text-white">
            <Eye className="w-4 h-4 mr-2" />
            View Report
          </Button>
          <Button size="sm" className="bg-purple-600 hover:bg-purple-500 text-white">
            <Brain className="w-4 h-4 mr-2" />
            Reanalyze
          </Button>
        </div>
      </div>

      {/* Overall Scores */}
      <Card className="bg-gradient-to-r from-purple-500/10 to-blue-500/10 border-white/10">
        <CardContent className="p-6">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
            <ScoreCircle score={analysis.scoring.totalScore} label="Overall Score" color="purple" />
            <ScoreCircle score={analysis.scoring.cashFlowScore} label="Cash Flow" color="green" />
            <ScoreCircle score={analysis.scoring.appreciationScore} label="Appreciation" color="blue" />
            <ScoreCircle score={analysis.scoring.riskScore} label="Risk Score" color="yellow" />
            <div className="col-span-2 md:col-span-1 flex flex-col items-center justify-center">
              <div className="text-3xl font-bold text-white">{analysis.scoring.projectedROI}%</div>
              <div className="text-xs text-gray-400 text-center">Projected ROI</div>
            </div>
          </div>

          <div className="mt-6 flex items-center justify-between">
            <div className="text-sm text-gray-400">
              Investment Strategy: <span className="text-white font-semibold">{analysis.investmentStrategy.replace('_', ' ')}</span>
            </div>
            <Badge className="bg-green-500/10 text-green-400 border-green-500/20">
              <Award className="w-3 h-3 mr-1" />
              Recommended Investment
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Detailed Analysis Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab}>
        <TabsList className="bg-white/5 border border-white/10">
          <TabsTrigger value="overview" className="data-[state=active]:bg-purple-600">Overview</TabsTrigger>
          <TabsTrigger value="investment" className="data-[state=active]:bg-purple-600">Investment</TabsTrigger>
          <TabsTrigger value="market" className="data-[state=active]:bg-purple-600">Market</TabsTrigger>
          <TabsTrigger value="risk" className="data-[state=active]:bg-purple-600">Risk</TabsTrigger>
          <TabsTrigger value="neighborhood" className="data-[state=active]:bg-purple-600">Neighborhood</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <InvestmentMetrics investment={analysis.investment} />
            <MarketPositioning positioning={analysis.marketPositioning} />
            <RiskAssessment risk={analysis.riskAssessment} />
            <NeighborhoodIntelligence neighborhood={analysis.neighborhood} />
          </div>
        </TabsContent>

        <TabsContent value="investment" className="mt-6">
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div className="xl:col-span-2">
              <InvestmentMetrics investment={analysis.investment} />
            </div>
            <Card className="bg-white/5 border-white/10">
              <CardHeader>
                <CardTitle className="text-white">Improvement Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analysis.condition.improvementRecommendations.map((rec, index) => (
                    <div key={index} className="p-3 bg-black/20 border border-white/5 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-semibold text-white">{rec.item}</span>
                        <Badge className="bg-green-500/10 text-green-400 border-green-500/20 text-xs">
                          +{rec.roiImpact}% ROI
                        </Badge>
                      </div>
                      <div className="text-xs text-gray-400">Cost: ${rec.cost.toLocaleString()}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="market" className="mt-6">
          <MarketPositioning positioning={analysis.marketPositioning} />
        </TabsContent>

        <TabsContent value="risk" className="mt-6">
          <RiskAssessment risk={analysis.riskAssessment} />
        </TabsContent>

        <TabsContent value="neighborhood" className="mt-6">
          <NeighborhoodIntelligence neighborhood={analysis.neighborhood} />
        </TabsContent>
      </Tabs>

      {/* Analysis Status */}
      {isAnalyzing && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="fixed bottom-6 right-6 bg-purple-600 text-white p-4 rounded-lg shadow-lg border border-purple-500/20"
        >
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            <span className="text-sm font-semibold">Analyzing property...</span>
          </div>
        </motion.div>
      )}
    </div>
  )
}

export default PropertyIntelligenceDashboard