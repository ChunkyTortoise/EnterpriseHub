/**
 * Claude Concierge Context API Route
 * Provides real-time platform state and context information
 */

import { NextRequest, NextResponse } from 'next/server'

// Mock data for demonstration - in production, this would connect to actual data sources
const mockBotStatuses = [
  {
    id: 'jorge-seller-bot',
    name: 'Jorge Seller Bot',
    status: 'online' as const,
    activeConversations: 3,
    conversationsToday: 12,
    leadsQualified: 8,
    responseTimeMs: 850,
    lastActivity: new Date().toISOString()
  },
  {
    id: 'lead-bot',
    name: 'Lead Bot',
    status: 'online' as const,
    activeConversations: 5,
    conversationsToday: 18,
    leadsQualified: 12,
    responseTimeMs: 650,
    lastActivity: new Date().toISOString()
  },
  {
    id: 'intent-decoder',
    name: 'Intent Decoder',
    status: 'online' as const,
    activeConversations: 1,
    conversationsToday: 25,
    leadsQualified: 20,
    responseTimeMs: 42,
    lastActivity: new Date().toISOString()
  }
]

const mockMarketConditions = {
  interestRates: {
    current: 7.2,
    trend: 'stable',
    lastUpdate: new Date().toISOString()
  },
  inventory: {
    level: 'low',
    monthsSupply: 2.8,
    trend: 'declining'
  },
  priceIndex: {
    current: 385.2,
    changePercent: 2.1,
    period: '30d'
  }
}

const mockHotLeads = [
  {
    id: 'lead_001',
    name: 'Sarah Johnson',
    temperature: 85,
    intent: 'selling',
    lastContact: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), // 2 hours ago
    priority: 'high',
    source: 'jorge-seller-bot'
  },
  {
    id: 'lead_002',
    name: 'Mike Chen',
    temperature: 78,
    intent: 'buying',
    lastContact: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(), // 4 hours ago
    priority: 'high',
    source: 'lead-bot'
  }
]

export async function GET(request: NextRequest) {
  try {
    // In production, this would fetch real-time data from:
    // - Bot status APIs
    // - CRM systems (GoHighLevel)
    // - Market data APIs
    // - Analytics databases

    // Get query parameters for filtering
    const { searchParams } = new URL(request.url)
    const includeMetrics = searchParams.get('metrics') === 'true'
    const includeSuggestions = searchParams.get('suggestions') === 'true'

    // Base context data
    const contextData = {
      timestamp: new Date().toISOString(),
      activeBots: mockBotStatuses,
      marketConditions: mockMarketConditions,
      hotLeads: mockHotLeads,
    }

    // Add optional metrics
    if (includeMetrics) {
      const totalConversations = mockBotStatuses.reduce(
        (sum, bot) => sum + bot.conversationsToday,
        0
      )
      const totalLeadsQualified = mockBotStatuses.reduce(
        (sum, bot) => sum + bot.leadsQualified,
        0
      )
      const avgResponseTime = Math.round(
        mockBotStatuses.reduce((sum, bot) => sum + bot.responseTimeMs, 0) /
          mockBotStatuses.length
      )

      contextData['metrics'] = {
        totalConversations,
        totalLeadsQualified,
        avgResponseTime,
        conversionRate: totalLeadsQualified / totalConversations,
        onlineBots: mockBotStatuses.filter(bot => bot.status === 'online').length,
        totalBots: mockBotStatuses.length
      }
    }

    // Add optional suggestions
    if (includeSuggestions) {
      contextData['suggestions'] = await generateContextualSuggestions(contextData)
    }

    return NextResponse.json(contextData, {
      headers: {
        'Cache-Control': 'no-cache, must-revalidate',
        'Content-Type': 'application/json'
      }
    })

  } catch (error) {
    console.error('Context API error:', error)

    return NextResponse.json(
      { error: 'Failed to fetch platform context' },
      { status: 500 }
    )
  }
}

async function generateContextualSuggestions(context: any) {
  // Generate intelligent suggestions based on current platform state
  const suggestions = []

  // High-temperature leads need immediate attention
  const highTempLeads = context.hotLeads?.filter(
    (lead: any) => lead.temperature > 80
  )
  if (highTempLeads?.length > 0) {
    suggestions.push({
      type: 'opportunity',
      title: `${highTempLeads.length} hot leads need attention`,
      description: 'High-temperature leads are most likely to convert. Follow up within the next hour.',
      priority: 'high',
      action: {
        type: 'navigation',
        label: 'View Hot Leads',
        data: { route: '/leads?filter=hot' }
      }
    })
  }

  // Bot performance optimization
  const slowBots = context.activeBots?.filter(
    (bot: any) => bot.responseTimeMs > 1000
  )
  if (slowBots?.length > 0) {
    suggestions.push({
      type: 'best_practice',
      title: 'Optimize bot response times',
      description: 'Some bots are responding slowly. Consider reviewing their configuration.',
      priority: 'medium',
      action: {
        type: 'navigation',
        label: 'Check Bot Performance',
        data: { route: '/jorge?tab=analytics' }
      }
    })
  }

  // Market opportunity alerts
  if (context.marketConditions?.inventory?.level === 'low') {
    suggestions.push({
      type: 'opportunity',
      title: 'Low inventory market opportunity',
      description: 'Current low inventory means higher prices and faster sales for sellers.',
      priority: 'medium',
      action: {
        type: 'bot_start',
        label: 'Start Seller Campaign',
        data: { botId: 'jorge-seller-bot', context: { marketCondition: 'low-inventory' } }
      }
    })
  }

  // Workflow completion suggestions
  const activeBotCount = context.activeBots?.filter(
    (bot: any) => bot.activeConversations > 0
  ).length || 0

  if (activeBotCount === 0) {
    suggestions.push({
      type: 'workflow',
      title: 'No active conversations',
      description: 'Consider starting lead outreach or prospecting to maintain pipeline flow.',
      priority: 'low',
      action: {
        type: 'navigation',
        label: 'View Lead Pipeline',
        data: { route: '/leads' }
      }
    })
  }

  return suggestions
}

// Handle preflight OPTIONS request for CORS
export async function OPTIONS(request: NextRequest) {
  return new Response(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  })
}