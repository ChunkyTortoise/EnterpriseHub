"use client"

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Globe,
  TrendingUp,
  DollarSign,
  Users,
  AlertTriangle,
  CheckCircle,
  XCircle,
  MapPin,
  BarChart3,
  Target,
  Clock,
  Flag,
  Zap,
  Shield,
  Calendar
} from 'lucide-react'

interface MarketData {
  marketId: string
  countryCode: string
  countryName: string
  region: 'north_america' | 'europe' | 'asia_pacific' | 'latin_america' | 'middle_east_africa'
  marketSize: number
  successProbability: number
  roiProjection: number
  investmentRequired: number
  timelineMonths: number
  expansionPriority: number
  competitionIntensity: number
  marketMaturity: 'emerging' | 'developing' | 'mature' | 'saturated'
  culturalComplexity: 'low' | 'medium' | 'high'
  regulatoryComplexity: 'low' | 'medium' | 'high'
  keyOpportunities: string[]
  mainChallenges: string[]
  currency: string
  language: string[]
}

interface GlobalTrend {
  trend: string
  description: string
  impact: 'high' | 'medium' | 'low'
  opportunity: string
}

const MarketSelector: React.FC = () => {
  const [selectedMarket, setSelectedMarket] = useState<MarketData | null>(null)
  const [markets, setMarkets] = useState<MarketData[]>([])
  const [globalTrends, setGlobalTrends] = useState<GlobalTrend[]>([])
  const [selectedRegion, setSelectedRegion] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'priority' | 'probability' | 'roi' | 'size'>('priority')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadMarketData()
  }, [])

  const loadMarketData = async () => {
    setIsLoading(true)
    try {
      // Simulate API call - replace with real data fetching
      await new Promise(resolve => setTimeout(resolve, 1200))

      // Mock market data
      setMarkets([
        {
          marketId: 'ca',
          countryCode: 'CA',
          countryName: 'Canada',
          region: 'north_america',
          marketSize: 750000,
          successProbability: 0.87,
          roiProjection: 0.45,
          investmentRequired: 650000,
          timelineMonths: 12,
          expansionPriority: 1,
          competitionIntensity: 0.35,
          marketMaturity: 'mature',
          culturalComplexity: 'low',
          regulatoryComplexity: 'medium',
          keyOpportunities: [
            'High MLS penetration (98%)',
            'English language market',
            'Similar real estate practices',
            'Strong digital adoption'
          ],
          mainChallenges: [
            'PIPEDA compliance requirements',
            'Provincial licensing variations',
            'Foreign buyer taxes in some provinces'
          ],
          currency: 'CAD',
          language: ['English', 'French']
        },
        {
          marketId: 'uk',
          countryCode: 'GB',
          countryName: 'United Kingdom',
          region: 'europe',
          marketSize: 580000,
          successProbability: 0.72,
          roiProjection: 0.38,
          investmentRequired: 850000,
          timelineMonths: 18,
          expansionPriority: 2,
          competitionIntensity: 0.55,
          marketMaturity: 'mature',
          culturalComplexity: 'medium',
          regulatoryComplexity: 'high',
          keyOpportunities: [
            'Large addressable market',
            'English language advantage',
            'Strong PropTech adoption',
            'Brexit opportunities'
          ],
          mainChallenges: [
            'Different commission structure (1-3.5%)',
            'UK GDPR compliance',
            'Formal business culture',
            'Established property portals'
          ],
          currency: 'GBP',
          language: ['English']
        },
        {
          marketId: 'de',
          countryCode: 'DE',
          countryName: 'Germany',
          region: 'europe',
          marketSize: 920000,
          successProbability: 0.68,
          roiProjection: 0.42,
          investmentRequired: 950000,
          timelineMonths: 24,
          expansionPriority: 3,
          competitionIntensity: 0.48,
          marketMaturity: 'mature',
          culturalComplexity: 'medium',
          regulatoryComplexity: 'high',
          keyOpportunities: [
            'Largest EU market',
            'Data-driven culture fits Jorge methodology',
            'Growing digital real estate market',
            '6% commission acceptable'
          ],
          mainChallenges: [
            'German language requirement',
            'Strict GDPR enforcement',
            'Complex regulatory environment',
            'Formal business approach'
          ],
          currency: 'EUR',
          language: ['German']
        },
        {
          marketId: 'au',
          countryCode: 'AU',
          countryName: 'Australia',
          region: 'asia_pacific',
          marketSize: 450000,
          successProbability: 0.78,
          roiProjection: 0.52,
          investmentRequired: 720000,
          timelineMonths: 15,
          expansionPriority: 2,
          competitionIntensity: 0.42,
          marketMaturity: 'mature',
          culturalComplexity: 'low',
          regulatoryComplexity: 'medium',
          keyOpportunities: [
            'English language market',
            'High real estate activity',
            'Tech-savvy population',
            'Similar business culture'
          ],
          mainChallenges: [
            'Distance and timezone',
            'Privacy Act compliance',
            'State licensing variations',
            'Established local players'
          ],
          currency: 'AUD',
          language: ['English']
        }
      ])

      // Mock global trends
      setGlobalTrends([
        {
          trend: 'AI Adoption Acceleration',
          description: 'Real estate AI adoption growing 35% annually worldwide',
          impact: 'high',
          opportunity: 'First-mover advantage in emerging markets'
        },
        {
          trend: 'Remote Work Impact',
          description: 'Sustained impact on residential preferences',
          impact: 'medium',
          opportunity: 'Suburban and rural market expansion'
        },
        {
          trend: 'PropTech Investment Growth',
          description: 'Global PropTech investment reaching record highs',
          impact: 'high',
          opportunity: 'Partnership and acquisition opportunities'
        },
        {
          trend: 'Regulatory Harmonization',
          description: 'Cross-border regulations becoming standardized',
          impact: 'medium',
          opportunity: 'Easier international expansion'
        }
      ])

    } catch (error) {
      console.error('Failed to load market data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredMarkets = markets
    .filter(market => selectedRegion === 'all' || market.region === selectedRegion)
    .sort((a, b) => {
      switch (sortBy) {
        case 'priority':
          return a.expansionPriority - b.expansionPriority
        case 'probability':
          return b.successProbability - a.successProbability
        case 'roi':
          return b.roiProjection - a.roiProjection
        case 'size':
          return b.marketSize - a.marketSize
        default:
          return a.expansionPriority - b.expansionPriority
      }
    })

  const getRegionColor = (region: string) => {
    switch (region) {
      case 'north_america':
        return 'bg-blue-500'
      case 'europe':
        return 'bg-green-500'
      case 'asia_pacific':
        return 'bg-purple-500'
      case 'latin_america':
        return 'bg-yellow-500'
      case 'middle_east_africa':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getMaturityColor = (maturity: string) => {
    switch (maturity) {
      case 'emerging':
        return 'text-green-400'
      case 'developing':
        return 'text-yellow-400'
      case 'mature':
        return 'text-blue-400'
      case 'saturated':
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  }

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'low':
        return 'text-green-400'
      case 'medium':
        return 'text-yellow-400'
      case 'high':
        return 'text-red-400'
      default:
        return 'text-gray-400'
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const formatPercentage = (value: number) => {
    return `${Math.round(value * 100)}%`
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 text-white">
      {/* Header */}
      <div className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="p-2 bg-blue-500 rounded-lg">
                <Globe className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Global Market Intelligence</h1>
                <p className="text-blue-200">Jorge's International Expansion Dashboard</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm text-blue-200">Markets Analyzed</div>
                <div className="text-2xl font-bold">{markets.length}</div>
              </div>
              <div className="text-right">
                <div className="text-sm text-blue-200">Total Opportunity</div>
                <div className="text-2xl font-bold text-green-400">
                  {formatCurrency(markets.reduce((sum, m) => sum + m.marketSize, 0))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="border-b border-white/10 bg-black/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div className="flex items-center space-x-2">
                <label className="text-sm text-gray-400">Region:</label>
                <select
                  value={selectedRegion}
                  onChange={(e) => setSelectedRegion(e.target.value)}
                  className="bg-white/5 border border-white/10 rounded-lg px-3 py-1 text-white"
                >
                  <option value="all">All Regions</option>
                  <option value="north_america">North America</option>
                  <option value="europe">Europe</option>
                  <option value="asia_pacific">Asia Pacific</option>
                  <option value="latin_america">Latin America</option>
                  <option value="middle_east_africa">Middle East & Africa</option>
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <label className="text-sm text-gray-400">Sort by:</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="bg-white/5 border border-white/10 rounded-lg px-3 py-1 text-white"
                >
                  <option value="priority">Priority</option>
                  <option value="probability">Success Probability</option>
                  <option value="roi">ROI Projection</option>
                  <option value="size">Market Size</option>
                </select>
              </div>
            </div>

            <button className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors flex items-center space-x-2">
              <Target className="h-4 w-4" />
              <span>Generate Strategy</span>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Market List */}
          <div className="lg:col-span-2 space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Market Opportunities</h2>
              <div className="text-sm text-gray-400">
                {filteredMarkets.length} markets found
              </div>
            </div>

            <div className="space-y-4">
              {filteredMarkets.map((market) => (
                <motion.div
                  key={market.marketId}
                  whileHover={{ scale: 1.01 }}
                  onClick={() => setSelectedMarket(market)}
                  className={`cursor-pointer bg-white/5 backdrop-blur-sm border rounded-xl p-6 transition-all ${
                    selectedMarket?.marketId === market.marketId
                      ? 'border-blue-500 bg-blue-500/10'
                      : 'border-white/10 hover:border-white/20'
                  }`}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-4">
                      <div className={`w-3 h-3 rounded-full ${getRegionColor(market.region)}`} />
                      <div>
                        <h3 className="text-lg font-semibold text-white">{market.countryName}</h3>
                        <p className="text-sm text-gray-400">
                          {market.region.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())} • {market.currency}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-green-400">{formatPercentage(market.successProbability)}</div>
                      <div className="text-xs text-gray-400">Success Probability</div>
                    </div>
                  </div>

                  <div className="grid grid-cols-4 gap-4 mb-4">
                    <div>
                      <div className="text-sm text-gray-400">Market Size</div>
                      <div className="text-lg font-semibold text-white">{formatCurrency(market.marketSize)}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-400">ROI Projection</div>
                      <div className="text-lg font-semibold text-white">{formatPercentage(market.roiProjection)}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-400">Investment</div>
                      <div className="text-lg font-semibold text-white">{formatCurrency(market.investmentRequired)}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-400">Timeline</div>
                      <div className="text-lg font-semibold text-white">{market.timelineMonths}mo</div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4 text-sm">
                      <div className="flex items-center space-x-1">
                        <Flag className="h-4 w-4 text-gray-400" />
                        <span className={getMaturityColor(market.marketMaturity)}>
                          {market.marketMaturity.charAt(0).toUpperCase() + market.marketMaturity.slice(1)}
                        </span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Shield className="h-4 w-4 text-gray-400" />
                        <span className={getComplexityColor(market.regulatoryComplexity)}>
                          {market.regulatoryComplexity.charAt(0).toUpperCase() + market.regulatoryComplexity.slice(1)} Regulatory
                        </span>
                      </div>
                    </div>
                    <div className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                      Priority #{market.expansionPriority}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Market Details */}
          <div className="space-y-6">
            {selectedMarket ? (
              <AnimatePresence>
                <motion.div
                  key={selectedMarket.marketId}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="space-y-6"
                >
                  <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
                    <div className="flex items-center space-x-4 mb-6">
                      <div className={`w-4 h-4 rounded-full ${getRegionColor(selectedMarket.region)}`} />
                      <h3 className="text-xl font-semibold text-white">{selectedMarket.countryName}</h3>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <h4 className="text-sm font-medium text-gray-400 mb-2">Key Opportunities</h4>
                        <div className="space-y-2">
                          {selectedMarket.keyOpportunities.map((opportunity, index) => (
                            <div key={index} className="flex items-center space-x-2 text-sm">
                              <CheckCircle className="h-4 w-4 text-green-400 flex-shrink-0" />
                              <span className="text-gray-300">{opportunity}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="text-sm font-medium text-gray-400 mb-2">Main Challenges</h4>
                        <div className="space-y-2">
                          {selectedMarket.mainChallenges.map((challenge, index) => (
                            <div key={index} className="flex items-center space-x-2 text-sm">
                              <AlertTriangle className="h-4 w-4 text-yellow-400 flex-shrink-0" />
                              <span className="text-gray-300">{challenge}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/10">
                        <div>
                          <div className="text-sm text-gray-400">Cultural Complexity</div>
                          <div className={`text-lg font-semibold ${getComplexityColor(selectedMarket.culturalComplexity)}`}>
                            {selectedMarket.culturalComplexity.charAt(0).toUpperCase() + selectedMarket.culturalComplexity.slice(1)}
                          </div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-400">Competition</div>
                          <div className="text-lg font-semibold text-white">
                            {formatPercentage(selectedMarket.competitionIntensity)}
                          </div>
                        </div>
                      </div>

                      <div className="pt-4">
                        <h4 className="text-sm font-medium text-gray-400 mb-2">Languages</h4>
                        <div className="flex flex-wrap gap-2">
                          {selectedMarket.language.map((lang) => (
                            <span key={lang} className="px-2 py-1 bg-white/10 rounded text-xs text-white">
                              {lang}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="mt-6 pt-6 border-t border-white/10">
                      <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg transition-colors flex items-center justify-center space-x-2">
                        <Target className="h-4 w-4" />
                        <span>Create Expansion Plan</span>
                      </button>
                    </div>
                  </div>
                </motion.div>
              </AnimatePresence>
            ) : (
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6 text-center">
                <MapPin className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-400">Select a market to view detailed analysis</p>
              </div>
            )}

            {/* Global Trends */}
            <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Global Trends</h3>
              <div className="space-y-4">
                {globalTrends.map((trend, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-white">{trend.trend}</h4>
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        trend.impact === 'high' ? 'bg-red-500/20 text-red-400' :
                        trend.impact === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
                        'bg-green-500/20 text-green-400'
                      }`}>
                        {trend.impact.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400">{trend.description}</p>
                    <p className="text-xs text-blue-300">{trend.opportunity}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MarketSelector