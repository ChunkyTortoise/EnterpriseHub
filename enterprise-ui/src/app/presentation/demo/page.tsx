// Jorge's Demo Mode - Main Interface
// Professional demonstration system for showcasing AI capabilities

'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  PlayCircle,
  Settings,
  Monitor,
  Users,
  Brain,
  BarChart3,
  ArrowRight,
  Sparkles,
  Shield,
  Zap,
  Target,
  Clock,
  Award
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import useDemoMode, { useScenarioSelection } from '@/hooks/useDemoMode';

export default function DemoModePage() {
  const [demoState, demoActions] = useDemoMode();
  const { scenarios, categorized } = useScenarioSelection();
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    // Ensure demo data is fresh when page loads
    demoActions.refreshDemoData();
  }, [demoActions]);

  const categoryStats = {
    seller_qualification: { count: categorized.seller_qualification.length, color: 'bg-red-500' },
    buyer_nurture: { count: categorized.buyer_nurture.length, color: 'bg-blue-500' },
    market_intelligence: { count: categorized.market_intelligence.length, color: 'bg-green-500' },
    cross_bot_coordination: { count: categorized.cross_bot_coordination.length, color: 'bg-purple-500' }
  };

  const handleQuickDemo = async (scenarioId: string) => {
    await demoActions.loadScenario(scenarioId);
    window.open('/presentation/demo/live', '_blank');
  };

  if (demoState.isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading Jorge's Demo System...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Header */}
      <header className="bg-black/20 backdrop-blur-md border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Monitor className="w-8 h-8 text-blue-400" />
                <div>
                  <h1 className="text-2xl font-bold text-white">Jorge's AI Demo Center</h1>
                  <p className="text-blue-200 text-sm">Professional AI Platform Demonstrations</p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Badge variant="outline" className="bg-blue-500/10 text-blue-300 border-blue-400">
                <Brain className="w-4 h-4 mr-1" />
                AI-Powered Demos
              </Badge>
              <Badge variant="outline" className="bg-green-500/10 text-green-300 border-green-400">
                <Shield className="w-4 h-4 mr-1" />
                Client-Safe Data
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center bg-blue-500/10 text-blue-300 px-4 py-2 rounded-full mb-6">
            <Sparkles className="w-5 h-5 mr-2" />
            Professional Client Demonstrations
          </div>

          <h2 className="text-5xl font-bold text-white mb-4 leading-tight">
            Showcase Jorge's AI<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-400">
              Real Estate Ecosystem
            </span>
          </h2>

          <p className="text-xl text-gray-300 max-w-3xl mx-auto mb-8 leading-relaxed">
            Professional demonstration system featuring realistic scenarios, synthetic data, and live bot interactions
            that highlight Jorge's competitive advantages while maintaining complete client privacy.
          </p>

          <div className="flex items-center justify-center gap-4">
            <Link href="/presentation/demo/scenarios">
              <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 text-lg">
                <PlayCircle className="w-5 h-5 mr-2" />
                Start Professional Demo
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>

            <Link href="/presentation/demo/live">
              <Button variant="outline" size="lg" className="border-white/20 text-white hover:bg-white/10 px-8 py-3 text-lg">
                <Monitor className="w-5 h-5 mr-2" />
                Live Presentation Mode
              </Button>
            </Link>
          </div>
        </motion.div>

        {/* Quick Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-12"
        >
          <Card className="bg-white/5 border-white/10 text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-white mb-2">{scenarios.length}</div>
              <div className="text-sm text-gray-300">Demo Scenarios</div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-blue-400 mb-2">{demoState.demoProperties.length}</div>
              <div className="text-sm text-gray-300">Synthetic Properties</div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-green-400 mb-2">{demoState.demoLeads.length}</div>
              <div className="text-sm text-gray-300">Client Personas</div>
            </CardContent>
          </Card>

          <Card className="bg-white/5 border-white/10 text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-purple-400 mb-2">100%</div>
              <div className="text-sm text-gray-300">Data Privacy</div>
            </CardContent>
          </Card>
        </motion.div>

        {/* Demo Categories */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.6 }}
        >
          <h3 className="text-2xl font-bold text-white mb-6">Featured Demo Scenarios</h3>

          <Tabs value={selectedCategory} onValueChange={setSelectedCategory} className="w-full">
            <TabsList className="grid w-full grid-cols-5 bg-white/5 border border-white/10">
              <TabsTrigger value="all" className="data-[state=active]:bg-white/10">
                All Scenarios
              </TabsTrigger>
              <TabsTrigger value="seller_qualification" className="data-[state=active]:bg-red-500/20">
                <Target className="w-4 h-4 mr-2" />
                Seller Qualification
              </TabsTrigger>
              <TabsTrigger value="buyer_nurture" className="data-[state=active]:bg-blue-500/20">
                <Users className="w-4 h-4 mr-2" />
                Buyer Nurture
              </TabsTrigger>
              <TabsTrigger value="market_intelligence" className="data-[state=active]:bg-green-500/20">
                <BarChart3 className="w-4 h-4 mr-2" />
                Market Intelligence
              </TabsTrigger>
              <TabsTrigger value="cross_bot_coordination" className="data-[state=active]:bg-purple-500/20">
                <Brain className="w-4 h-4 mr-2" />
                Bot Coordination
              </TabsTrigger>
            </TabsList>

            <TabsContent value="all" className="mt-6">
              <ScenarioGrid scenarios={scenarios} onQuickDemo={handleQuickDemo} />
            </TabsContent>

            <TabsContent value="seller_qualification" className="mt-6">
              <ScenarioGrid scenarios={categorized.seller_qualification} onQuickDemo={handleQuickDemo} />
            </TabsContent>

            <TabsContent value="buyer_nurture" className="mt-6">
              <ScenarioGrid scenarios={categorized.buyer_nurture} onQuickDemo={handleQuickDemo} />
            </TabsContent>

            <TabsContent value="market_intelligence" className="mt-6">
              <ScenarioGrid scenarios={categorized.market_intelligence} onQuickDemo={handleQuickDemo} />
            </TabsContent>

            <TabsContent value="cross_bot_coordination" className="mt-6">
              <ScenarioGrid scenarios={categorized.cross_bot_coordination} onQuickDemo={handleQuickDemo} />
            </TabsContent>
          </Tabs>
        </motion.div>

        {/* Jorge Advantages Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.6 }}
          className="mt-16"
        >
          <div className="bg-gradient-to-r from-blue-600/10 to-purple-600/10 rounded-2xl p-8 border border-blue-500/20">
            <div className="text-center mb-8">
              <h3 className="text-3xl font-bold text-white mb-4">Why Jorge's AI Ecosystem Wins</h3>
              <p className="text-gray-300 text-lg max-w-3xl mx-auto">
                These demonstrations showcase the competitive advantages that justify Jorge's 6% premium commission
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="bg-blue-500/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Zap className="w-8 h-8 text-blue-400" />
                </div>
                <h4 className="text-lg font-semibold text-white mb-2">Speed & Efficiency</h4>
                <p className="text-gray-300 text-sm">
                  Sell properties in 21 days vs. 45-day market average through AI-powered buyer matching
                </p>
              </div>

              <div className="text-center">
                <div className="bg-green-500/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Award className="w-8 h-8 text-green-400" />
                </div>
                <h4 className="text-lg font-semibold text-white mb-2">Premium Results</h4>
                <p className="text-gray-300 text-sm">
                  95% accuracy in pricing, 89% client satisfaction, and guaranteed sale commitments
                </p>
              </div>

              <div className="text-center">
                <div className="bg-purple-500/10 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Brain className="w-8 h-8 text-purple-400" />
                </div>
                <h4 className="text-lg font-semibold text-white mb-2">AI Innovation</h4>
                <p className="text-gray-300 text-sm">
                  Confrontational qualification, predictive analytics, and 24/7 automated follow-up
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Error Display */}
        {demoState.error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-6"
          >
            <Card className="border-red-500/20 bg-red-500/5">
              <CardContent className="p-4">
                <div className="flex items-center gap-2 text-red-400">
                  <Target className="w-5 h-5" />
                  <span className="font-semibold">Demo System Error:</span>
                  <span>{demoState.error}</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>
    </div>
  );
}

// Scenario Grid Component
interface ScenarioGridProps {
  scenarios: any[];
  onQuickDemo: (scenarioId: string) => void;
}

function ScenarioGrid({ scenarios, onQuickDemo }: ScenarioGridProps) {
  const getCategoryColor = (category: string) => {
    const colors = {
      seller_qualification: 'border-red-500/30 bg-red-500/5',
      buyer_nurture: 'border-blue-500/30 bg-blue-500/5',
      market_intelligence: 'border-green-500/30 bg-green-500/5',
      cross_bot_coordination: 'border-purple-500/30 bg-purple-500/5'
    };
    return colors[category as keyof typeof colors] || 'border-gray-500/30 bg-gray-500/5';
  };

  const getCategoryIcon = (category: string) => {
    const icons = {
      seller_qualification: Target,
      buyer_nurture: Users,
      market_intelligence: BarChart3,
      cross_bot_coordination: Brain
    };
    const Icon = icons[category as keyof typeof icons] || Target;
    return <Icon className="w-5 h-5" />;
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {scenarios.map((scenario, index) => (
        <motion.div
          key={scenario.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1, duration: 0.5 }}
        >
          <Card className={`${getCategoryColor(scenario.category)} border hover:bg-white/5 transition-all duration-200`}>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between mb-2">
                <Badge variant="outline" className="text-xs">
                  {getCategoryIcon(scenario.category)}
                  <span className="ml-1">{scenario.duration} min</span>
                </Badge>
                <Clock className="w-4 h-4 text-gray-400" />
              </div>
              <CardTitle className="text-white text-lg leading-tight">{scenario.name}</CardTitle>
            </CardHeader>

            <CardContent className="pt-0">
              <p className="text-gray-300 text-sm mb-4 line-clamp-2">{scenario.description}</p>

              <div className="space-y-3">
                {/* Key Benefits */}
                <div>
                  <div className="text-xs text-gray-400 mb-1">Jorge Advantages:</div>
                  <div className="space-y-1">
                    {scenario.jorgeAdvantages?.slice(0, 2).map((advantage: string, i: number) => (
                      <div key={i} className="text-xs text-blue-300 flex items-center">
                        <div className="w-1 h-1 bg-blue-400 rounded-full mr-2"></div>
                        {advantage}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2 pt-2">
                  <Link href={`/presentation/demo/scenarios?id=${scenario.id}`} className="flex-1">
                    <Button size="sm" className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                      <Settings className="w-4 h-4 mr-2" />
                      Configure
                    </Button>
                  </Link>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onQuickDemo(scenario.id)}
                    className="border-white/20 text-white hover:bg-white/10"
                  >
                    <PlayCircle className="w-4 h-4 mr-2" />
                    Quick Demo
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  );
}