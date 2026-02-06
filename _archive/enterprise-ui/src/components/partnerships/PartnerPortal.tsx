"use client"

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Globe,
  TrendingUp,
  Users,
  DollarSign,
  MapPin,
  Award,
  Settings,
  BarChart3,
  Handshake,
  Target,
  Calendar,
  FileText,
  Zap
} from 'lucide-react'

interface PartnerMetrics {
  partnerId: string
  partnerType: 'franchise' | 'mls_provider' | 'technology' | 'crm_provider'
  companyName: string
  monthlyRevenue: number
  performanceScore: number
  activeAgents: number
  leadsProcessed: number
  conversionRate: number
  marketCoverage: number
}

interface PartnershipOpportunity {
  opportunityId: string
  partnerType: string
  targetCompany: string
  potentialRevenue: number
  marketSize: string
  priority: 'high' | 'medium' | 'low'
  timeline: string
}

interface RevenueProjection {
  month: string
  revenue: number
  growth: number
}

const PartnerPortal: React.FC = () => {
  const [selectedView, setSelectedView] = useState<'dashboard' | 'performance' | 'opportunities' | 'onboarding'>('dashboard')
  const [partnerMetrics, setPartnerMetrics] = useState<PartnerMetrics[]>([])
  const [opportunities, setOpportunities] = useState<PartnershipOpportunity[]>([])
  const [revenueProjections, setRevenueProjections] = useState<RevenueProjection[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadPartnerData()
  }, [])

  const loadPartnerData = async () => {
    setIsLoading(true)
    try {
      // Simulate API calls - replace with real data fetching
      await new Promise(resolve => setTimeout(resolve, 1000))

      // Mock partner metrics
      setPartnerMetrics([
        {
          partnerId: 'franchise_century21_main',
          partnerType: 'franchise',
          companyName: 'Century 21 Main Street',
          monthlyRevenue: 45000,
          performanceScore: 94,
          activeAgents: 85,
          leadsProcessed: 1250,
          conversionRate: 18.5,
          marketCoverage: 75
        },
        {
          partnerId: 'mls_flexmls_primary',
          partnerType: 'mls_provider',
          companyName: 'FlexMLS',
          monthlyRevenue: 15000,
          performanceScore: 92,
          activeAgents: 450,
          leadsProcessed: 3200,
          conversionRate: 8.2,
          marketCoverage: 95
        },
        {
          partnerId: 'tech_retell_ai',
          partnerType: 'technology',
          companyName: 'Retell AI',
          monthlyRevenue: 8500,
          performanceScore: 89,
          activeAgents: 150,
          leadsProcessed: 890,
          conversionRate: 25.0,
          marketCoverage: 45
        }
      ])

      // Mock partnership opportunities
      setOpportunities([
        {
          opportunityId: 'op_remax_international',
          partnerType: 'franchise',
          targetCompany: 'RE/MAX International',
          potentialRevenue: 200000,
          marketSize: 'Large',
          priority: 'high',
          timeline: 'Q2 2026'
        },
        {
          opportunityId: 'op_mred_chicago',
          partnerType: 'mls_provider',
          targetCompany: 'MRED (Chicago)',
          potentialRevenue: 50000,
          marketSize: 'Medium',
          priority: 'medium',
          timeline: 'Q3 2026'
        },
        {
          opportunityId: 'op_compass_tech',
          partnerType: 'technology',
          targetCompany: 'Compass Technology',
          potentialRevenue: 75000,
          marketSize: 'Large',
          priority: 'high',
          timeline: 'Q4 2026'
        }
      ])

      // Mock revenue projections
      setRevenueProjections([
        { month: 'Jan', revenue: 68500, growth: 12 },
        { month: 'Feb', revenue: 72300, growth: 15 },
        { month: 'Mar', revenue: 79800, growth: 18 },
        { month: 'Apr', revenue: 85200, growth: 22 },
        { month: 'May', revenue: 92400, growth: 25 },
        { month: 'Jun', revenue: 98900, growth: 28 }
      ])

    } catch (error) {
      console.error('Failed to load partner data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getPartnerTypeIcon = (type: string) => {
    switch (type) {
      case 'franchise':
        return <Users className="h-5 w-5" />
      case 'mls_provider':
        return <Globe className="h-5 w-5" />
      case 'technology':
        return <Zap className="h-5 w-5" />
      case 'crm_provider':
        return <BarChart3 className="h-5 w-5" />
      default:
        return <Handshake className="h-5 w-5" />
    }
  }

  const getPartnerTypeColor = (type: string) => {
    switch (type) {
      case 'franchise':
        return 'bg-blue-500'
      case 'mls_provider':
        return 'bg-green-500'
      case 'technology':
        return 'bg-purple-500'
      case 'crm_provider':
        return 'bg-orange-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-500'
      case 'medium':
        return 'bg-yellow-500'
      case 'low':
        return 'bg-green-500'
      default:
        return 'bg-gray-500'
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
                <Handshake className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">Partnership Portal</h1>
                <p className="text-blue-200">Jorge's Global Partnership Ecosystem</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm text-blue-200">Total Partners</div>
                <div className="text-2xl font-bold">{partnerMetrics.length}</div>
              </div>
              <div className="text-right">
                <div className="text-sm text-blue-200">Monthly Revenue</div>
                <div className="text-2xl font-bold text-green-400">
                  {formatCurrency(partnerMetrics.reduce((sum, p) => sum + p.monthlyRevenue, 0))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6">
          <nav className="flex space-x-8">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
              { id: 'performance', label: 'Performance', icon: TrendingUp },
              { id: 'opportunities', label: 'Opportunities', icon: Target },
              { id: 'onboarding', label: 'Onboarding', icon: Users }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setSelectedView(tab.id as any)}
                className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                  selectedView === tab.id
                    ? 'border-blue-500 text-blue-400'
                    : 'border-transparent text-gray-400 hover:text-white'
                }`}
              >
                <tab.icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <AnimatePresence mode="wait">
          {selectedView === 'dashboard' && (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-8"
            >
              {/* Key Metrics */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Active Partners</p>
                      <p className="text-3xl font-bold text-white">{partnerMetrics.length}</p>
                      <p className="text-sm text-green-400">+2 this month</p>
                    </div>
                    <div className="p-3 bg-blue-500/20 rounded-lg">
                      <Users className="h-6 w-6 text-blue-400" />
                    </div>
                  </div>
                </motion.div>

                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Monthly Revenue</p>
                      <p className="text-3xl font-bold text-white">
                        {formatCurrency(partnerMetrics.reduce((sum, p) => sum + p.monthlyRevenue, 0))}
                      </p>
                      <p className="text-sm text-green-400">+15% vs last month</p>
                    </div>
                    <div className="p-3 bg-green-500/20 rounded-lg">
                      <DollarSign className="h-6 w-6 text-green-400" />
                    </div>
                  </div>
                </motion.div>

                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Avg Performance</p>
                      <p className="text-3xl font-bold text-white">
                        {Math.round(partnerMetrics.reduce((sum, p) => sum + p.performanceScore, 0) / partnerMetrics.length)}%
                      </p>
                      <p className="text-sm text-green-400">Excellent scores</p>
                    </div>
                    <div className="p-3 bg-purple-500/20 rounded-lg">
                      <Award className="h-6 w-6 text-purple-400" />
                    </div>
                  </div>
                </motion.div>

                <motion.div
                  whileHover={{ scale: 1.02 }}
                  className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Market Coverage</p>
                      <p className="text-3xl font-bold text-white">35%</p>
                      <p className="text-sm text-yellow-400">Growing rapidly</p>
                    </div>
                    <div className="p-3 bg-orange-500/20 rounded-lg">
                      <MapPin className="h-6 w-6 text-orange-400" />
                    </div>
                  </div>
                </motion.div>
              </div>

              {/* Partner Performance Grid */}
              <div className="space-y-6">
                <h3 className="text-xl font-semibold">Partner Performance</h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                  {partnerMetrics.map((partner) => (
                    <motion.div
                      key={partner.partnerId}
                      whileHover={{ scale: 1.02 }}
                      className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6"
                    >
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex items-center space-x-3">
                          <div className={`p-2 rounded-lg ${getPartnerTypeColor(partner.partnerType)}/20`}>
                            {getPartnerTypeIcon(partner.partnerType)}
                          </div>
                          <div>
                            <h4 className="font-semibold text-white">{partner.companyName}</h4>
                            <p className="text-sm text-gray-400 capitalize">{partner.partnerType.replace('_', ' ')}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold text-green-400">{partner.performanceScore}%</div>
                          <div className="text-xs text-gray-400">Performance</div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4 mb-4">
                        <div>
                          <div className="text-sm text-gray-400">Monthly Revenue</div>
                          <div className="text-lg font-semibold text-white">{formatCurrency(partner.monthlyRevenue)}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-400">Active Agents</div>
                          <div className="text-lg font-semibold text-white">{partner.activeAgents.toLocaleString()}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-400">Leads Processed</div>
                          <div className="text-lg font-semibold text-white">{partner.leadsProcessed.toLocaleString()}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-400">Conversion Rate</div>
                          <div className="text-lg font-semibold text-white">{partner.conversionRate}%</div>
                        </div>
                      </div>

                      {/* Performance Bar */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-400">Market Coverage</span>
                          <span className="text-white">{partner.marketCoverage}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${partner.marketCoverage}%` }}
                            transition={{ duration: 1, delay: 0.5 }}
                            className="bg-gradient-to-r from-blue-500 to-green-500 h-2 rounded-full"
                          />
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              {/* Revenue Projection Chart */}
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
                <h3 className="text-xl font-semibold mb-6">Revenue Projection</h3>
                <div className="grid grid-cols-6 gap-4 h-64">
                  {revenueProjections.map((projection, index) => (
                    <div key={projection.month} className="flex flex-col items-center justify-end space-y-2">
                      <div className="text-sm text-gray-400">{formatCurrency(projection.revenue)}</div>
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: `${(projection.revenue / 100000) * 100}%` }}
                        transition={{ duration: 1, delay: index * 0.1 }}
                        className="bg-gradient-to-t from-blue-500 to-green-500 w-full rounded-t-lg min-h-[20px]"
                      />
                      <div className="text-sm font-medium text-white">{projection.month}</div>
                      <div className="text-xs text-green-400">+{projection.growth}%</div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {selectedView === 'opportunities' && (
            <motion.div
              key="opportunities"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-8"
            >
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">Partnership Opportunities</h2>
                <button className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors">
                  Add Opportunity
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {opportunities.map((opportunity) => (
                  <motion.div
                    key={opportunity.opportunityId}
                    whileHover={{ scale: 1.02 }}
                    className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-lg ${getPartnerTypeColor(opportunity.partnerType)}/20`}>
                          {getPartnerTypeIcon(opportunity.partnerType)}
                        </div>
                        <div>
                          <h3 className="font-semibold text-white">{opportunity.targetCompany}</h3>
                          <p className="text-sm text-gray-400 capitalize">{opportunity.partnerType.replace('_', ' ')}</p>
                        </div>
                      </div>
                      <div className={`px-2 py-1 rounded-full text-xs font-semibold ${getPriorityColor(opportunity.priority)}/20 text-white border ${getPriorityColor(opportunity.priority)}/30`}>
                        {opportunity.priority.toUpperCase()}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 mb-4">
                      <div>
                        <div className="text-sm text-gray-400">Potential Revenue</div>
                        <div className="text-xl font-bold text-green-400">{formatCurrency(opportunity.potentialRevenue)}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-400">Market Size</div>
                        <div className="text-xl font-bold text-white">{opportunity.marketSize}</div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2 text-sm text-gray-400">
                        <Calendar className="h-4 w-4" />
                        <span>Target: {opportunity.timeline}</span>
                      </div>
                      <button className="bg-blue-600/20 text-blue-400 hover:bg-blue-600/30 px-3 py-1 rounded-lg text-sm transition-colors">
                        View Details
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Market Analysis */}
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
                <h3 className="text-xl font-semibold mb-6">Market Analysis</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-400">15</div>
                    <div className="text-sm text-gray-400">Markets Analyzed</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-400">$2.1M</div>
                    <div className="text-sm text-gray-400">Total Opportunity Value</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-400">87%</div>
                    <div className="text-sm text-gray-400">Success Probability</div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {selectedView === 'onboarding' && (
            <motion.div
              key="onboarding"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-8"
            >
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">Partner Onboarding</h2>
                <button className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors">
                  Start New Onboarding
                </button>
              </div>

              {/* Onboarding Progress */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {[
                  { stage: 'Contract Review', count: 3, color: 'blue' },
                  { stage: 'Technical Setup', count: 2, color: 'yellow' },
                  { stage: 'Training', count: 5, color: 'purple' },
                  { stage: 'Go Live', count: 1, color: 'green' }
                ].map((stage) => (
                  <div key={stage.stage} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
                    <div className="text-center">
                      <div className={`text-3xl font-bold text-${stage.color}-400`}>{stage.count}</div>
                      <div className="text-sm text-gray-400">{stage.stage}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Onboarding Checklist */}
              <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-6">
                <h3 className="text-xl font-semibold mb-6">Onboarding Checklist Template</h3>
                <div className="space-y-4">
                  {[
                    { task: 'Partnership Agreement Signed', completed: true },
                    { task: 'Technical Integration Specifications', completed: true },
                    { task: 'White-Label Branding Configuration', completed: true },
                    { task: 'Jorge Methodology Training Scheduled', completed: false },
                    { task: 'Data Migration Planning', completed: false },
                    { task: 'Go-Live Date Confirmation', completed: false },
                    { task: 'Success Metrics Definition', completed: false }
                  ].map((item, index) => (
                    <div key={index} className="flex items-center space-x-3">
                      <div className={`w-4 h-4 rounded border-2 ${
                        item.completed
                          ? 'bg-green-500 border-green-500'
                          : 'border-gray-400'
                      } flex items-center justify-center`}>
                        {item.completed && <div className="w-2 h-2 bg-white rounded-full" />}
                      </div>
                      <span className={item.completed ? 'text-green-400' : 'text-gray-300'}>
                        {item.task}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default PartnerPortal