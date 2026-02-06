// Jorge's Scenario Playback Component
// Visual presentation layer for demo scenarios with property data and market context

'use client';

import { useState, useEffect } from 'react';
import {
  Home,
  MapPin,
  DollarSign,
  TrendingUp,
  Calendar,
  Users,
  BarChart3,
  Target,
  Clock,
  Award,
  Zap,
  Star,
  Eye
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { motion, AnimatePresence } from 'framer-motion';
import type { DemoScenario, ConversationStep } from '@/lib/demo/ScenarioEngine';
import type { ConversationState, SimulationSettings } from '@/lib/demo/ConversationSimulator';

interface ScenarioPlaybackProps {
  scenario: DemoScenario;
  conversationState: ConversationState;
  currentStep: ConversationStep | null;
  isTyping: boolean;
  settings: SimulationSettings;
  isFullScreen?: boolean;
  isMuted?: boolean;
}

export function ScenarioPlayback({
  scenario,
  conversationState,
  currentStep,
  isTyping,
  settings,
  isFullScreen = false,
  isMuted = false
}: ScenarioPlaybackProps) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [animationTrigger, setAnimationTrigger] = useState(0);

  // Update slide based on conversation progress
  useEffect(() => {
    if (currentStep) {
      const progress = conversationState.completedSteps.length / scenario.conversationFlow.length;
      const totalSlides = 4; // Property details, market context, Jorge advantages, results
      setCurrentSlide(Math.floor(progress * totalSlides));
      setAnimationTrigger(prev => prev + 1);
    }
  }, [currentStep, conversationState.completedSteps.length, scenario.conversationFlow.length]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getUrgencyColor = (urgency: string) => {
    const colors = {
      high: 'bg-red-500/10 text-red-400 border-red-500/30',
      medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30',
      low: 'bg-green-500/10 text-green-400 border-green-500/30'
    };
    return colors[urgency as keyof typeof colors] || 'bg-gray-500/10 text-gray-400 border-gray-500/30';
  };

  const property = scenario.propertyData[0];
  const marketContext = scenario.marketContext;

  const slides = [
    // Slide 1: Property Overview
    {
      title: "Target Property",
      icon: Home,
      content: (
        <div className="space-y-6">
          {property && (
            <>
              {/* Property Hero */}
              <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-xl p-6 border border-blue-500/20">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="text-2xl font-bold text-white mb-2">{property.address}</h3>
                    <p className="text-gray-300">{property.type}</p>
                  </div>
                  <Badge variant="outline" className={getUrgencyColor(property.urgency)}>
                    {property.urgency} urgency
                  </Badge>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white">{formatCurrency(property.price)}</div>
                    <div className="text-sm text-gray-400">Listing Price</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-400">{property.marketData.daysOnMarket}</div>
                    <div className="text-sm text-gray-400">Days on Market</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-400">${property.marketData.pricePerSqft}</div>
                    <div className="text-sm text-gray-400">Per Sq Ft</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-400">{property.marketData.appreciation}%</div>
                    <div className="text-sm text-gray-400">Appreciation</div>
                  </div>
                </div>

                <p className="text-gray-300 text-sm leading-relaxed">{property.story}</p>
              </div>

              {/* Property Features */}
              <div className="grid grid-cols-2 gap-4">
                {property.features.slice(0, 4).map((feature, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: index * 0.1, duration: 0.3 }}
                    className="bg-white/5 rounded-lg p-4 border border-white/10"
                  >
                    <div className="text-white font-medium text-sm mb-1">{feature.name}</div>
                    <div className="text-gray-300 text-sm">{feature.value}</div>
                    <div className={`text-xs mt-1 ${
                      feature.importance === 'high' ? 'text-red-400' :
                      feature.importance === 'medium' ? 'text-yellow-400' : 'text-green-400'
                    }`}>
                      {feature.importance} importance
                    </div>
                  </motion.div>
                ))}
              </div>
            </>
          )}
        </div>
      )
    },

    // Slide 2: Market Context
    {
      title: "Market Intelligence",
      icon: BarChart3,
      content: (
        <div className="space-y-6">
          <div className="bg-gradient-to-r from-green-500/10 to-blue-500/10 rounded-xl p-6 border border-green-500/20">
            <h3 className="text-xl font-bold text-white mb-3">{marketContext.name}</h3>
            <p className="text-gray-300 mb-4">{marketContext.context}</p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <h4 className="text-green-400 font-semibold mb-2 flex items-center">
                  <TrendingUp className="w-4 h-4 mr-2" />
                  Market Trends
                </h4>
                <div className="space-y-1">
                  {marketContext.trends.map((trend, i) => (
                    <div key={i} className="text-sm text-gray-300 flex items-start">
                      <div className="w-1.5 h-1.5 bg-green-400 rounded-full mt-2 mr-2 flex-shrink-0"></div>
                      {trend}
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-blue-400 font-semibold mb-2 flex items-center">
                  <Target className="w-4 h-4 mr-2" />
                  Opportunities
                </h4>
                <div className="space-y-1">
                  {marketContext.opportunities.map((opportunity, i) => (
                    <div key={i} className="text-sm text-gray-300 flex items-start">
                      <div className="w-1.5 h-1.5 bg-blue-400 rounded-full mt-2 mr-2 flex-shrink-0"></div>
                      {opportunity}
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-red-400 font-semibold mb-2 flex items-center">
                  <Award className="w-4 h-4 mr-2" />
                  Challenges
                </h4>
                <div className="space-y-1">
                  {marketContext.challenges.map((challenge, i) => (
                    <div key={i} className="text-sm text-gray-300 flex items-start">
                      <div className="w-1.5 h-1.5 bg-red-400 rounded-full mt-2 mr-2 flex-shrink-0"></div>
                      {challenge}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="bg-blue-500/10 rounded-lg p-4 border border-blue-500/20">
            <h4 className="text-blue-300 font-semibold mb-2">Jorge's Competitive Advantage</h4>
            <p className="text-blue-200 text-sm">{marketContext.jorgeAdvantage}</p>
          </div>
        </div>
      )
    },

    // Slide 3: Jorge's Methodology
    {
      title: "Jorge's Advantage",
      icon: Zap,
      content: (
        <div className="space-y-6">
          <div className="bg-gradient-to-r from-yellow-500/10 to-red-500/10 rounded-xl p-6 border border-yellow-500/20">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center">
              <Zap className="w-6 h-6 mr-2 text-yellow-400" />
              Why Jorge Commands 6% Commission
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-yellow-400 font-semibold mb-3">Methodology Advantages</h4>
                <div className="space-y-3">
                  {scenario.jorgeAdvantages.slice(0, 4).map((advantage, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.15, duration: 0.3 }}
                      className="bg-white/5 rounded-lg p-3 border border-white/10"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-6 h-6 bg-yellow-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                          <Star className="w-4 h-4 text-yellow-400" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-300 leading-relaxed">{advantage}</p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="text-blue-400 font-semibold mb-3">Client Benefits</h4>
                <div className="space-y-3">
                  {scenario.clientBenefits.slice(0, 4).map((benefit, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.15, duration: 0.3 }}
                      className="bg-white/5 rounded-lg p-3 border border-white/10"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-6 h-6 bg-blue-500/20 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                          <Award className="w-4 h-4 text-blue-400" />
                        </div>
                        <div>
                          <p className="text-sm text-gray-300 leading-relaxed">{benefit}</p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )
    },

    // Slide 4: Expected Results
    {
      title: "Expected Results",
      icon: Award,
      content: (
        <div className="space-y-6">
          <div className="bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-xl p-6 border border-purple-500/20">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center">
              <Award className="w-6 h-6 mr-2 text-purple-400" />
              Guaranteed Outcomes
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {scenario.expectedOutcomes.map((outcome, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1, duration: 0.3 }}
                  className="bg-white/5 rounded-lg p-4 border border-white/10 text-center"
                >
                  <div className="text-2xl font-bold text-white mb-2">{outcome.value}</div>
                  <div className="text-sm text-gray-400 mb-1">{outcome.metric}</div>
                  {outcome.comparison && (
                    <div className="text-xs text-blue-300">{outcome.comparison}</div>
                  )}
                  <Badge
                    variant="outline"
                    className={`text-xs mt-2 ${
                      outcome.significance === 'high'
                        ? 'bg-green-500/10 text-green-400 border-green-500/30'
                        : outcome.significance === 'medium'
                        ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30'
                        : 'bg-gray-500/10 text-gray-400 border-gray-500/30'
                    }`}
                  >
                    {outcome.significance} impact
                  </Badge>
                </motion.div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <h4 className="text-white font-semibold mb-3 flex items-center">
                <Clock className="w-4 h-4 mr-2" />
                Timeline
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Demo Duration</span>
                  <span className="text-white">{scenario.duration} minutes</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Expected Sale Time</span>
                  <span className="text-green-400">21-30 days</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Traditional Agent</span>
                  <span className="text-red-400">45-90 days</span>
                </div>
              </div>
            </div>

            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
              <h4 className="text-white font-semibold mb-3 flex items-center">
                <Users className="w-4 h-4 mr-2" />
                Participants
              </h4>
              <div className="space-y-2">
                {scenario.participants.map((participant, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                    <span className="text-gray-300">{participant.name}</span>
                    <Badge variant="outline" className="text-xs">
                      {participant.role.replace('_', ' ')}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )
    }
  ];

  const currentSlideData = slides[Math.min(currentSlide, slides.length - 1)];

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-900/50 to-blue-900/50 backdrop-blur-sm">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/10 bg-black/20 backdrop-blur-md">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <currentSlideData.icon className="w-6 h-6 text-blue-400" />
            <div>
              <h2 className="text-xl font-bold text-white">{currentSlideData.title}</h2>
              <p className="text-sm text-gray-400">{scenario.name}</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Slide Indicator */}
            <div className="flex items-center gap-2">
              {slides.map((_, index) => (
                <div
                  key={index}
                  className={`w-2 h-2 rounded-full transition-all duration-300 ${
                    index === currentSlide ? 'bg-blue-400 w-8' : 'bg-white/20'
                  }`}
                />
              ))}
            </div>

            <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/30">
              <Eye className="w-4 h-4 mr-1" />
              Client View
            </Badge>
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 p-6 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={`slide-${currentSlide}-${animationTrigger}`}
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="h-full"
          >
            {currentSlideData.content}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Current Step Indicator */}
      {currentStep && (
        <div className="px-6 py-3 border-t border-white/10 bg-black/20 backdrop-blur-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/30">
                Step {currentStep.stepNumber}
              </Badge>
              <span className="text-sm text-gray-400">
                {currentStep.demoNotes || 'Demo in progress...'}
              </span>
            </div>

            {settings.showConfidence && currentStep.content.confidence && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">Confidence:</span>
                <span className="text-sm text-blue-400 font-medium">
                  {Math.round(currentStep.content.confidence * 100)}%
                </span>
              </div>
            )}
          </div>

          {currentStep.jorgeStrategy && (
            <div className="mt-2 text-xs text-purple-300">
              <span className="font-medium">Strategy:</span> {currentStep.jorgeStrategy}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ScenarioPlayback;