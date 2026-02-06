/**
 * Claude Concierge Knowledge Base API Route
 * Serves Jorge's platform knowledge for semantic memory
 */

import { NextRequest, NextResponse } from 'next/server'

// Jorge's complete knowledge base for semantic memory
const jorgeKnowledgeBase = {
  jorgeMethodology: {
    coreQuestions: [
      "Are you the owner of the property?",
      "What's your timeline for selling?",
      "What do you think your property is worth?",
      "What will you do if I can't get you that price?"
    ],
    temperatureThresholds: {
      hot: 75,
      warm: 50,
      lukewarm: 25
    },
    commissionRate: 6,
    confrontationalApproach: [
      "Direct questioning to test motivation",
      "No-BS communication style",
      "Immediate objection handling",
      "Stall-breaker techniques for time wasters",
      "Value-first positioning"
    ],
    qualificationProcess: {
      step1: "Establish ownership and authority",
      step2: "Determine genuine timeline vs wishful thinking",
      step3: "Reality-check price expectations with data",
      step4: "Test commitment level with consequence questions"
    }
  },
  botCapabilities: {
    'jorge-seller-bot': {
      name: 'Jorge Seller Bot',
      description: 'Confrontational qualification specialist using LangGraph workflow',
      strengths: [
        'Seller motivation testing through direct confrontation',
        'Price objection handling with market data',
        'Timeline qualification and urgency assessment',
        'Stall detection and immediate redirection',
        'Commission justification through value demonstration'
      ],
      idealScenarios: [
        'Initial seller contact and qualification',
        'Price objection handling and market education',
        'Motivation assessment and commitment testing',
        'Hot lead identification and fast-track processing',
        'Time waster elimination and pipeline cleaning'
      ],
      features: [
        '5-node LangGraph workflow (analyze → detect_stall → strategy → response → followup)',
        'FRS (Financial Readiness Score) calculation',
        'PCS (Psychological Commitment Score) assessment',
        'Temperature classification with dynamic routing',
        'GHL CRM integration with automatic field population',
        'Stall-breaker automation for 4 common objection patterns',
        '6% commission positioning with ROI justification'
      ],
      integrations: ['GoHighLevel CRM', 'Claude AI', 'WebSocket real-time', 'SMS compliance'],
      performanceMetrics: {
        avgResponseTime: '850ms',
        qualificationAccuracy: '94%',
        hotLeadIdentification: '89%',
        stallBreakingSuccess: '76%'
      },
      bestPractices: [
        'Use for motivated seller leads only',
        'Apply 4 core questions in sequence',
        'Escalate to human when FRS+PCS > 150',
        'Document all objections for pattern analysis'
      ]
    },
    'lead-bot': {
      name: 'Lead Bot',
      description: '3-7-30 day automation lifecycle with voice integration',
      strengths: [
        'Systematic lead nurturing with proven sequences',
        'Voice call integration for personal touch',
        'CMA delivery and market education',
        'Follow-up automation with behavioral triggers',
        'Contract-to-close relationship management'
      ],
      idealScenarios: [
        'New lead onboarding and initial education',
        'Buyer lead management and property matching',
        'Post-showing follow-up and feedback collection',
        'Contract-to-close nurture and milestone tracking',
        'Re-engagement of dormant leads'
      ],
      features: [
        '3-day sequence: Initial CMA and value establishment',
        '7-day sequence: Retell AI voice call with human touch',
        '30-day sequence: Long-term nurture and market updates',
        'Automated CMA generation with Zillow-defense positioning',
        'Post-showing survey automation',
        'Behavioral scoring based on engagement patterns',
        'Multi-touch attribution across email, SMS, voice'
      ],
      integrations: ['Retell AI Voice', 'Zillow API', 'Email/SMS platforms', 'Calendar scheduling'],
      performanceMetrics: {
        avgResponseTime: '650ms',
        sequenceCompletion: '78%',
        voiceCallConnection: '65%',
        leadToShowing: '23%'
      },
      automationSequences: {
        day3: 'CMA delivery with market positioning',
        day7: 'Personal voice call with Retell AI',
        day14: 'Market update and new listing alerts',
        day30: 'Long-term relationship maintenance'
      }
    },
    'intent-decoder': {
      name: 'Intent Decoder',
      description: 'FRS/PCS dual scoring with ML behavioral analysis',
      strengths: [
        'Real-time lead scoring with 95% accuracy',
        'Behavioral pattern recognition and prediction',
        'Readiness assessment for optimal timing',
        'Performance analytics and optimization insights',
        'Multi-dimensional lead analysis'
      ],
      idealScenarios: [
        'Lead prioritization and resource allocation',
        'Quality assessment before human handoff',
        'Performance optimization and bot tuning',
        'Strategic routing and workflow optimization',
        'Predictive analytics for pipeline management'
      ],
      features: [
        '28-feature behavioral analysis pipeline',
        'SHAP explainability for decision transparency',
        '95% accuracy with 42.3ms response time',
        'Real-time FRS (Financial Readiness) scoring',
        'Real-time PCS (Psychological Commitment) scoring',
        'Confidence-based Claude escalation at 0.85 threshold',
        'Integration with all bot ecosystems for continuous learning'
      ],
      integrations: ['Scikit-learn ML', 'SHAP explainability', 'FastAPI real-time', 'All bot data feeds'],
      performanceMetrics: {
        avgResponseTime: '42.3ms',
        accuracyRate: '95.2%',
        falsePositiveRate: '3.1%',
        predictionConfidence: '89.7%'
      },
      scoringCriteria: {
        frs: 'Financial capability, timeline, budget verification',
        pcs: 'Motivation level, urgency, commitment indicators',
        combined: 'Weighted composite for final routing decisions'
      }
    }
  },
  realEstateKnowledge: {
    marketTrends: [
      'Interest rate impact on buyer behavior and affordability',
      'Seasonal market patterns affecting inventory and pricing',
      'Inventory levels and their direct correlation to pricing pressure',
      'Local market dynamics and micro-neighborhood variations',
      'Economic indicators affecting real estate demand'
    ],
    processSteps: {
      sellerOnboarding: [
        'Initial qualification call with Jorge methodology',
        'Property valuation using CMA and market analysis',
        'Listing agreement signing with commission explanation',
        'Professional photography and marketing asset creation',
        'Showing coordination and negotiation management',
        'Contract to closing with milestone communication'
      ],
      buyerOnboarding: [
        'Pre-approval verification and budget confirmation',
        'Comprehensive needs assessment and preference mapping',
        'Automated property search setup with alert preferences',
        'Showing coordination with feedback collection',
        'Offer preparation and negotiation strategy',
        'Transaction management from contract to close'
      ]
    },
    commonObjections: {
      sellerObjections: [
        'Your commission is too high compared to discount brokers',
        'The market price you suggested is too low for my property',
        'I want to try selling by owner first to save money',
        'I need to think about it and discuss with family',
        'The market timing isn\'t right, I want to wait'
      ],
      buyerObjections: [
        'The property price is higher than my budget allows',
        'This location doesn\'t meet our school district requirements',
        'The property needs too many repairs for our timeline',
        'I can\'t afford the monthly payment with current rates',
        'I want to see more options before making a decision'
      ]
    },
    objectionResponses: {
      commissionValue: [
        'Our 6% fee delivers 12-15% higher sale prices on average',
        'Professional marketing reaches 3x more qualified buyers',
        'Expert negotiation adds $15k+ value in typical transactions'
      ],
      priceReality: [
        'Let me show you recent comparable sales data',
        'Here\'s what similar properties actually sold for, not listed for',
        'Market value is determined by buyer actions, not owner opinions'
      ],
      timingConcerns: [
        'Every month you wait costs you $X in market appreciation',
        'Current inventory levels mean faster sales and higher prices',
        'Interest rate trends suggest now is optimal for your timeline'
      ]
    },
    bestPractices: [
      'Always qualify motivation before discussing price or process',
      'Use recent CMA data to establish realistic value expectations',
      'Address objections with data and market evidence',
      'Follow up within 24 hours of any significant interaction',
      'Maintain consistent communication throughout entire process',
      'Document all interactions for pattern analysis and improvement',
      'Focus on value delivery rather than fee justification',
      'Use Jorge\'s confrontational approach only with motivated prospects'
    ],
    marketIndicators: {
      buyerMarket: [
        'High inventory (6+ months supply)',
        'Increasing days on market',
        'Rising interest rates reducing affordability',
        'Price reductions becoming common'
      ],
      sellerMarket: [
        'Low inventory (3 months supply)',
        'Decreasing days on market',
        'Multiple offers on well-priced properties',
        'Price appreciation accelerating'
      ],
      balancedMarket: [
        'Moderate inventory (4-5 months supply)',
        'Stable pricing with modest appreciation',
        'Reasonable negotiation on both sides',
        'Predictable transaction timelines'
      ]
    }
  },
  platformWorkflows: {
    leadQualification: {
      description: 'Jorge\'s proven qualification methodology',
      steps: [
        'Ownership verification and decision-making authority',
        'Timeline assessment with consequences for delays',
        'Price expectation reality check with market data',
        'Motivation testing through direct confrontational questions'
      ],
      successMetrics: {
        qualificationTime: 'Under 10 minutes for clear yes/no',
        accuracy: 'Above 90% for hot/cold classification',
        escalation: 'Human handoff for FRS+PCS scores above 150'
      }
    },
    botHandoffs: {
      description: 'Intelligent routing between specialized bots',
      triggers: {
        toJorgeSellerBot: 'Seller intent detected, motivated timeline',
        toLeadBot: 'Buyer intent or post-qualification nurture needed',
        toIntentDecoder: 'Unclear intent requiring behavioral analysis'
      },
      contextTransfer: [
        'Conversation history and key insights',
        'Qualification scores and confidence levels',
        'Objections raised and responses attempted',
        'Timeline and urgency indicators'
      ]
    },
    performanceOptimization: {
      description: 'Continuous improvement methodology',
      metrics: [
        'Response time optimization for user experience',
        'Qualification accuracy for resource efficiency',
        'Conversion rates from each bot interaction',
        'Customer satisfaction and experience scores'
      ],
      optimizationCycle: [
        'Data collection from all bot interactions',
        'Pattern analysis for success/failure factors',
        'A/B testing of different approaches',
        'Implementation of proven improvements'
      ]
    }
  }
}

export async function GET(request: NextRequest) {
  try {
    // Get query parameters for filtering
    const { searchParams } = new URL(request.url)
    const section = searchParams.get('section')
    const botId = searchParams.get('botId')

    let responseData = jorgeKnowledgeBase

    // Filter by section if requested
    if (section) {
      const validSections = ['jorgeMethodology', 'botCapabilities', 'realEstateKnowledge', 'platformWorkflows']
      if (validSections.includes(section)) {
        responseData = { [section]: jorgeKnowledgeBase[section as keyof typeof jorgeKnowledgeBase] }
      } else {
        return NextResponse.json(
          { error: `Invalid section. Must be one of: ${validSections.join(', ')}` },
          { status: 400 }
        )
      }
    }

    // Filter by specific bot if requested
    if (botId && section === 'botCapabilities') {
      const botCapability = jorgeKnowledgeBase.botCapabilities[botId as keyof typeof jorgeKnowledgeBase.botCapabilities]
      if (botCapability) {
        responseData = { botCapabilities: { [botId]: botCapability } }
      } else {
        return NextResponse.json(
          { error: `Bot not found: ${botId}` },
          { status: 404 }
        )
      }
    }

    return NextResponse.json(responseData, {
      headers: {
        'Cache-Control': 'public, max-age=3600', // Cache for 1 hour
        'Content-Type': 'application/json'
      }
    })

  } catch (error) {
    console.error('Knowledge base API error:', error)

    return NextResponse.json(
      { error: 'Failed to fetch knowledge base' },
      { status: 500 }
    )
  }
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