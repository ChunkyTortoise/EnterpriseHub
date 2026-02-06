"use client";

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Star,
  Quote,
  User,
  TrendingUp,
  DollarSign,
  Award,
  CheckCircle,
  Heart,
  MessageSquare,
  ThumbsUp
} from 'lucide-react'
import { useState } from 'react'

// Client testimonials data
const testimonials = [
  {
    id: 'testimonial-1',
    clientName: 'Sarah Martinez',
    clientType: 'Seller',
    quote: "Jorge's AI responded in 2 minutes and sold my house for 15% above asking. The confrontational qualification actually helped me understand I was ready to sell immediately. No other agent has this technology.",
    rating: 5,
    transactionValue: 475000,
    outcome: 'Sold 23 days, 15% above asking price',
    jorgeAdvantage: [
      '2-minute response vs 2-day industry average',
      'Confrontational qualification revealed true motivation',
      'AI-powered pricing strategy maximized value'
    ],
    date: '2024-01-15',
    featured: true,
    avatar: '🏠'
  },
  {
    id: 'testimonial-2',
    clientName: 'Michael Chen',
    clientType: 'Buyer',
    quote: "The 3-7-30 nurture sequence kept me engaged without being pushy. The Day 7 voice call with market analysis was exactly what I needed to make a decision. Found my perfect home in 6 weeks.",
    rating: 5,
    transactionValue: 320000,
    outcome: 'Purchase completed in 6 weeks',
    jorgeAdvantage: [
      'Automated nurture sequence maintained perfect timing',
      'Voice integration provided personal touch at scale',
      'Market intelligence helped identify perfect property'
    ],
    date: '2024-01-08',
    featured: true,
    avatar: '🏡'
  },
  {
    id: 'testimonial-3',
    clientName: 'Jennifer Rodriguez',
    clientType: 'Referral Partner',
    quote: "Jorge's AI system has transformed how I refer clients. The response time and qualification process is so superior that my referrals always choose Jorge. He's generated $2.3M in referral business for me this year.",
    rating: 5,
    transactionValue: 2300000,
    outcome: '$2.3M in referred transactions',
    jorgeAdvantage: [
      'Instant response creates immediate trust',
      'Professional qualification process',
      'Technology advantage wins every comparison'
    ],
    date: '2024-01-03',
    featured: true,
    avatar: '🤝'
  },
  {
    id: 'testimonial-4',
    clientName: 'David Thompson',
    clientType: 'Investor',
    quote: "The market intelligence and CMA accuracy is incredible. Jorge's AI found me 3 off-market properties and provided analysis that saved me $180K. The ROI on working with Jorge is exceptional.",
    rating: 5,
    transactionValue: 1250000,
    outcome: '3 properties acquired, $180K saved',
    jorgeAdvantage: [
      'AI-powered market intelligence',
      'Off-market property identification',
      '93% CMA accuracy vs manual analysis'
    ],
    date: '2023-12-28',
    featured: true,
    avatar: '💼'
  },
  {
    id: 'testimonial-5',
    clientName: 'Amanda Foster',
    clientType: 'Seller',
    quote: "I was skeptical about the confrontational approach, but Jorge's AI quickly identified that I wasn't truly ready to sell. Six months later when I was motivated, the process was flawless. Sold in 12 days at full price.",
    rating: 5,
    transactionValue: 398000,
    outcome: 'Sold in 12 days at full asking price',
    jorgeAdvantage: [
      'Confrontational qualification prevented wasted time',
      'Perfect timing identification',
      'Stall-breaking methodology created clarity'
    ],
    date: '2023-12-15',
    featured: true,
    avatar: '✨'
  },
  {
    id: 'testimonial-6',
    clientName: 'Robert Kim',
    clientType: 'Buyer',
    quote: "Jorge's AI provided real-time market analysis that helped me act fast in a competitive market. We submitted an offer within hours and won against 7 other bidders. The technology advantage is real.",
    rating: 5,
    transactionValue: 565000,
    outcome: 'Won competitive bidding situation',
    jorgeAdvantage: [
      'Real-time market analysis',
      'Competitive strategy optimization',
      'Speed advantage in hot market'
    ],
    date: '2023-12-10',
    featured: false,
    avatar: '🏆'
  }
]

export function ClientTestimonials() {
  const [selectedTestimonial, setSelectedTestimonial] = useState(testimonials[0])
  const [showAll, setShowAll] = useState(false)

  const featuredTestimonials = testimonials.filter(t => t.featured)
  const displayedTestimonials = showAll ? testimonials : featuredTestimonials

  // Calculate summary statistics
  const averageRating = testimonials.reduce((sum, t) => sum + t.rating, 0) / testimonials.length
  const totalTransactionValue = testimonials.reduce((sum, t) => sum + t.transactionValue, 0)
  const clientTypes = testimonials.reduce((acc, t) => {
    acc[t.clientType] = (acc[t.clientType] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(value)

  return (
    <div className="space-y-6">
      {/* Testimonial Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-r from-slate-800/50 to-yellow-900/20 border-slate-700">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">Average Rating</p>
                <p className="text-2xl font-bold text-white">{averageRating.toFixed(1)}/5</p>
                <p className="text-sm text-yellow-400">Excellent</p>
              </div>
              <div className="p-3 rounded-full bg-yellow-600/20">
                <Star className="h-6 w-6 text-yellow-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-slate-800/50 to-green-900/20 border-slate-700">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">Total Value</p>
                <p className="text-2xl font-bold text-white">{formatCurrency(totalTransactionValue / 1000000)}M</p>
                <p className="text-sm text-green-400">Transactions</p>
              </div>
              <div className="p-3 rounded-full bg-green-600/20">
                <DollarSign className="h-6 w-6 text-green-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-slate-800/50 to-blue-900/20 border-slate-700">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">Client Types</p>
                <p className="text-2xl font-bold text-white">{Object.keys(clientTypes).length}</p>
                <p className="text-sm text-blue-400">Categories</p>
              </div>
              <div className="p-3 rounded-full bg-blue-600/20">
                <User className="h-6 w-6 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-r from-slate-800/50 to-purple-900/20 border-slate-700">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-400">Satisfaction</p>
                <p className="text-2xl font-bold text-white">100%</p>
                <p className="text-sm text-purple-400">Recommend</p>
              </div>
              <div className="p-3 rounded-full bg-purple-600/20">
                <ThumbsUp className="h-6 w-6 text-purple-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Testimonials Display */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Featured Testimonial */}
        <Card className="lg:col-span-2 bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Quote className="h-5 w-5" />
              Featured Client Success Story
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Client Info */}
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-2xl">
                  {selectedTestimonial.avatar}
                </div>
                <div>
                  <h3 className="text-xl font-semibold text-white">{selectedTestimonial.clientName}</h3>
                  <p className="text-slate-400">{selectedTestimonial.clientType}</p>
                  <div className="flex items-center gap-2 mt-1">
                    {Array.from({ length: selectedTestimonial.rating }).map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    ))}
                    <span className="text-sm text-slate-400 ml-2">
                      {new Date(selectedTestimonial.date).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Quote */}
              <div className="relative">
                <Quote className="absolute -top-2 -left-2 h-8 w-8 text-blue-400/30" />
                <blockquote className="text-lg text-slate-200 italic pl-6 leading-relaxed">
                  "{selectedTestimonial.quote}"
                </blockquote>
              </div>

              {/* Outcome */}
              <div className="p-4 bg-green-900/20 border border-green-800/50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle className="h-5 w-5 text-green-400" />
                  <h4 className="font-medium text-green-200">Outcome</h4>
                </div>
                <p className="text-green-100">{selectedTestimonial.outcome}</p>
                {selectedTestimonial.transactionValue > 0 && (
                  <p className="text-sm text-green-200 mt-1">
                    Transaction Value: {formatCurrency(selectedTestimonial.transactionValue)}
                  </p>
                )}
              </div>

              {/* Jorge Advantages */}
              <div className="space-y-3">
                <h4 className="font-medium text-white flex items-center gap-2">
                  <Award className="h-5 w-5 text-blue-400" />
                  Jorge AI Advantages Highlighted
                </h4>
                <div className="space-y-2">
                  {selectedTestimonial.jorgeAdvantage.map((advantage, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-slate-700/30 rounded-lg">
                      <div className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <CheckCircle className="h-4 w-4 text-white" />
                      </div>
                      <span className="text-sm text-slate-200">{advantage}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Testimonial List */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-white flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Client Stories
              </CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowAll(!showAll)}
                className="border-slate-600 text-slate-200 hover:bg-slate-700"
              >
                {showAll ? 'Featured Only' : 'View All'}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {displayedTestimonials.map((testimonial) => (
                <div
                  key={testimonial.id}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedTestimonial.id === testimonial.id
                      ? 'bg-blue-900/30 border-blue-700'
                      : 'bg-slate-700/30 border-slate-600 hover:bg-slate-700/50'
                  }`}
                  onClick={() => setSelectedTestimonial(testimonial)}
                >
                  <div className="flex items-center gap-3 mb-2">
                    <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-sm">
                      {testimonial.avatar}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-white truncate">{testimonial.clientName}</p>
                      <p className="text-xs text-slate-400">{testimonial.clientType}</p>
                    </div>
                    <div className="flex items-center gap-1">
                      {Array.from({ length: testimonial.rating }).map((_, i) => (
                        <Star key={i} className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                      ))}
                    </div>
                  </div>

                  <p className="text-sm text-slate-300 line-clamp-2">
                    "{testimonial.quote.substring(0, 120)}..."
                  </p>

                  <div className="flex justify-between items-center mt-3">
                    <Badge variant="outline" className="text-xs">
                      {formatCurrency(testimonial.transactionValue)}
                    </Badge>
                    <span className="text-xs text-slate-500">
                      {new Date(testimonial.date).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Client Type Breakdown */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Client Success by Category
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(clientTypes).map(([type, count]) => {
              const typeTestimonials = testimonials.filter(t => t.clientType === type)
              const avgValue = typeTestimonials.reduce((sum, t) => sum + t.transactionValue, 0) / count
              const avgRating = typeTestimonials.reduce((sum, t) => sum + t.rating, 0) / count

              return (
                <div key={type} className="p-4 bg-slate-700/30 rounded-lg border border-slate-600">
                  <div className="flex items-center gap-2 mb-3">
                    <User className="h-5 w-5 text-blue-400" />
                    <h4 className="font-medium text-white">{type}s</h4>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-400">Count</span>
                      <span className="font-semibold text-white">{count}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-400">Avg Value</span>
                      <span className="font-semibold text-white">{formatCurrency(avgValue)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-400">Avg Rating</span>
                      <div className="flex items-center gap-1">
                        <span className="font-semibold text-white">{avgRating.toFixed(1)}</span>
                        <Star className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                      </div>
                    </div>
                  </div>

                  {type === 'Seller' && (
                    <div className="mt-3 p-2 bg-green-900/20 border border-green-800/50 rounded">
                      <p className="text-xs text-green-200">87% qualification rate with confrontational methodology</p>
                    </div>
                  )}

                  {type === 'Buyer' && (
                    <div className="mt-3 p-2 bg-blue-900/20 border border-blue-800/50 rounded">
                      <p className="text-xs text-blue-200">3-7-30 nurture sequence with voice integration</p>
                    </div>
                  )}

                  {type === 'Referral Partner' && (
                    <div className="mt-3 p-2 bg-purple-900/20 border border-purple-800/50 rounded">
                      <p className="text-xs text-purple-200">Technology advantage wins every comparison</p>
                    </div>
                  )}

                  {type === 'Investor' && (
                    <div className="mt-3 p-2 bg-yellow-900/20 border border-yellow-800/50 rounded">
                      <p className="text-xs text-yellow-200">AI-powered market intelligence and CMA accuracy</p>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Key Testimonial Insights */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Heart className="h-5 w-5" />
            Client Success Insights
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-green-900/20 border border-green-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Star className="h-5 w-5 text-green-400" />
                <h4 className="font-medium text-green-200">Exceptional Satisfaction</h4>
              </div>
              <p className="text-sm text-green-100">
                5-star average rating across all client types demonstrates consistent excellence.
                Jorge AI delivers superior results through technology advantages.
              </p>
            </div>

            <div className="p-4 bg-blue-900/20 border border-blue-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="h-5 w-5 text-blue-400" />
                <h4 className="font-medium text-blue-200">Proven ROI</h4>
              </div>
              <p className="text-sm text-blue-100">
                Clients consistently achieve above-market results through Jorge's AI-powered
                approach. Average outcomes exceed industry standards significantly.
              </p>
            </div>

            <div className="p-4 bg-purple-900/20 border border-purple-800/50 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Award className="h-5 w-5 text-purple-400" />
                <h4 className="font-medium text-purple-200">Technology Advantage</h4>
              </div>
              <p className="text-sm text-purple-100">
                Clients repeatedly highlight Jorge's technology advantage as the key
                differentiator. Speed, accuracy, and intelligence create superior experiences.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}