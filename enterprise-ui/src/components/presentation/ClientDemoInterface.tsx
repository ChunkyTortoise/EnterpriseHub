'use client';

/**
 * Jorge's Real Estate AI Platform - Client Demonstration Interface
 * Professional client demo environment with seeded data and live ROI calculations
 * Version: 2.0.0
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play,
  RefreshCw,
  Download,
  Clock,
  TrendingUp,
  Users,
  DollarSign,
  Zap,
  Settings,
  BarChart3,
  MessageSquare,
  Home,
  Target,
  CheckCircle2
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/components/ui/use-toast';

// Demo scenario types
type DemoScenario =
  | 'luxury_agent'
  | 'mid_market'
  | 'first_time_buyer'
  | 'investor_focused'
  | 'high_volume';

interface ClientProfile {
  id: string;
  name: string;
  agency_name: string;
  market_segment: DemoScenario;
  monthly_leads: number;
  avg_deal_size: number;
  commission_rate: number;
  current_challenges: string[];
  goals: string[];
  pain_points: string[];
  geographic_market: string;
  experience_level: string;
  tech_adoption: string;
}

interface DemoSession {
  session_id: string;
  client_profile: ClientProfile;
  demo_leads: any[];
  demo_properties: any[];
  demo_conversations: any[];
  roi_calculation: any;
  performance_metrics: any;
  created_at: string;
  expires_at: string;
  status: string;
}

interface PerformanceMetrics {
  response_times: {
    traditional_avg: string;
    jorge_avg: string;
    improvement: string;
  };
  conversion_rates: {
    traditional: string;
    jorge: string;
    improvement: string;
  };
  accuracy_scores: {
    traditional: string;
    jorge: string;
    improvement: string;
  };
  monthly_performance: {
    leads_processed: number;
    traditional_conversions: number;
    jorge_conversions: number;
    additional_deals: number;
    additional_revenue: number;
  };
  business_impact: {
    revenue_increase: string;
    cost_reduction: string;
    roi: string;
    payback_period: string;
  };
}

export function ClientDemoInterface() {
  const [selectedScenario, setSelectedScenario] = useState<DemoScenario>('mid_market');
  const [demoSession, setDemoSession] = useState<DemoSession | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const { toast } = useToast();

  // Demo scenario configurations
  const scenarios = {
    luxury_agent: {
      name: 'Luxury Real Estate Agent',
      icon: '💎',
      description: 'High-end properties ($1M+) with sophisticated clientele',
      color: 'from-amber-500 to-yellow-600',
      highlights: ['Premium Service Scaling', 'Immediate Response', 'White-glove Experience']
    },
    mid_market: {
      name: 'Mid-Market Residential',
      icon: '🏡',
      description: 'Standard residential properties with typical families',
      color: 'from-blue-500 to-indigo-600',
      highlights: ['Volume Efficiency', 'Process Automation', 'Consistent Quality']
    },
    first_time_buyer: {
      name: 'First-Time Buyer Specialist',
      icon: '🔑',
      description: 'Entry-level properties with extensive buyer education',
      color: 'from-green-500 to-emerald-600',
      highlights: ['Streamlined Education', 'Faster Closings', 'Guided Process']
    },
    investor_focused: {
      name: 'Investment Property Pro',
      icon: '📊',
      description: 'Investment properties with ROI-focused analysis',
      color: 'from-purple-500 to-violet-600',
      highlights: ['Instant Analysis', 'Deal Velocity', 'Portfolio Growth']
    },
    high_volume: {
      name: 'High-Volume Operations',
      icon: '⚡',
      description: 'Large-scale operations focusing on efficiency',
      color: 'from-red-500 to-rose-600',
      highlights: ['Massive Scale', 'Quality Control', 'Team Coordination']
    }
  };

  const createDemoSession = useCallback(async () => {
    if (loading) return;

    setLoading(true);
    try {
      const response = await fetch('/api/v1/client-demonstrations/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scenario: selectedScenario,
          client_name: `Demo ${scenarios[selectedScenario].name}`,
          agency_name: `Professional ${scenarios[selectedScenario].name} Agency`
        })
      });

      if (!response.ok) throw new Error('Failed to create demo session');

      const session: DemoSession = await response.json();
      setDemoSession(session);
      setActiveTab('overview');

      toast({
        title: 'Demo Session Created',
        description: `Professional ${scenarios[selectedScenario].name} demonstration ready`,
      });

    } catch (error) {
      console.error('Error creating demo session:', error);
      toast({
        title: 'Error',
        description: 'Failed to create demo session. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [selectedScenario, loading, toast]);

  const resetDemoSession = useCallback(async () => {
    if (!demoSession || loading) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/v1/client-demonstrations/sessions/${demoSession.session_id}/reset`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Failed to reset demo session');

      const newSession: DemoSession = await response.json();
      setDemoSession(newSession);

      toast({
        title: 'Demo Reset',
        description: 'Fresh demo data generated successfully',
      });

    } catch (error) {
      console.error('Error resetting demo session:', error);
      toast({
        title: 'Error',
        description: 'Failed to reset demo session. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  }, [demoSession, loading, toast]);

  const extendSession = useCallback(async () => {
    if (!demoSession) return;

    try {
      const response = await fetch(`/api/v1/client-demonstrations/sessions/${demoSession.session_id}/extend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ additional_hours: 1 })
      });

      if (!response.ok) throw new Error('Failed to extend session');

      toast({
        title: 'Session Extended',
        description: 'Demo session extended by 1 hour',
      });

    } catch (error) {
      console.error('Error extending session:', error);
      toast({
        title: 'Error',
        description: 'Failed to extend session. Please try again.',
        variant: 'destructive',
      });
    }
  }, [demoSession, toast]);

  const exportResults = useCallback(async () => {
    if (!demoSession) return;

    try {
      // Export demo results as PDF or JSON
      const exportData = {
        client_profile: demoSession.client_profile,
        roi_calculation: demoSession.roi_calculation,
        performance_metrics: demoSession.performance_metrics,
        session_info: {
          session_id: demoSession.session_id,
          scenario: selectedScenario,
          created_at: demoSession.created_at
        }
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], {
        type: 'application/json'
      });

      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `jorge-demo-${selectedScenario}-${new Date().toISOString().split('T')[0]}.json`;
      a.click();

      URL.revokeObjectURL(url);

      toast({
        title: 'Export Complete',
        description: 'Demo results exported successfully',
      });

    } catch (error) {
      console.error('Error exporting results:', error);
      toast({
        title: 'Error',
        description: 'Failed to export results. Please try again.',
        variant: 'destructive',
      });
    }
  }, [demoSession, selectedScenario, toast]);

  // Calculate time remaining
  const getTimeRemaining = useCallback(() => {
    if (!demoSession) return '';

    const now = new Date();
    const expires = new Date(demoSession.expires_at);
    const diff = expires.getTime() - now.getTime();

    if (diff <= 0) return 'Expired';

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    return `${hours}h ${minutes}m`;
  }, [demoSession]);

  if (!demoSession) {
    return (
      <div className=\"min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 p-6\">
        <div className=\"mx-auto max-w-6xl\">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className=\"text-center mb-12\"
          >
            <h1 className=\"text-4xl font-bold text-white mb-4\">
              Jorge's AI Platform
              <span className=\"block text-2xl text-blue-400 font-normal mt-2\">
                Client Demonstration Center
              </span>
            </h1>
            <p className=\"text-gray-300 text-lg max-w-3xl mx-auto\">
              Professional real estate AI demonstrations with realistic data,
              ROI calculations, and performance benchmarks
            </p>
          </motion.div>

          {/* Scenario Selection */}
          <div className=\"grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8\">
            {Object.entries(scenarios).map(([key, scenario]) => (
              <motion.div
                key={key}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Card
                  className={`
                    relative overflow-hidden cursor-pointer transition-all
                    ${selectedScenario === key
                      ? 'ring-2 ring-blue-500 bg-slate-800'
                      : 'bg-slate-800 hover:bg-slate-700'
                    }
                  `}
                  onClick={() => setSelectedScenario(key as DemoScenario)}
                >
                  <div className={`absolute inset-0 bg-gradient-to-br ${scenario.color} opacity-10`} />

                  <CardHeader className=\"relative\">
                    <div className=\"flex items-center space-x-3\">
                      <span className=\"text-2xl\">{scenario.icon}</span>
                      <div>
                        <CardTitle className=\"text-white text-lg\">{scenario.name}</CardTitle>
                        <p className=\"text-gray-400 text-sm mt-1\">{scenario.description}</p>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent className=\"relative\">
                    <div className=\"space-y-2\">
                      {scenario.highlights.map((highlight, idx) => (
                        <div key={idx} className=\"flex items-center space-x-2\">
                          <CheckCircle2 className=\"w-4 h-4 text-green-400\" />
                          <span className=\"text-gray-300 text-sm\">{highlight}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>

          {/* Start Demo Button */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className=\"text-center\"
          >
            <Button
              onClick={createDemoSession}
              disabled={loading}
              size=\"lg\"
              className=\"bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 text-lg\"
            >
              {loading ? (
                <>
                  <RefreshCw className=\"w-5 h-5 mr-2 animate-spin\" />
                  Creating Demo...
                </>
              ) : (
                <>
                  <Play className=\"w-5 h-5 mr-2\" />
                  Start {scenarios[selectedScenario].name} Demo
                </>
              )}
            </Button>

            <p className=\"text-gray-400 text-sm mt-4\">
              Demo includes realistic lead data, property inventory,
              Jorge bot conversations, and comprehensive ROI analysis
            </p>
          </motion.div>
        </div>
      </div>
    );
  }

  // Demo session interface
  return (
    <div className=\"min-h-screen bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800 p-6\">
      <div className=\"mx-auto max-w-7xl\">
        {/* Demo Session Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className=\"bg-slate-800 rounded-xl p-6 mb-8\"
        >
          <div className=\"flex items-center justify-between\">
            <div>
              <h1 className=\"text-3xl font-bold text-white flex items-center\">
                <span className=\"mr-3\">{scenarios[selectedScenario].icon}</span>
                {demoSession.client_profile.name}
                <Badge variant=\"secondary\" className=\"ml-3\">
                  {scenarios[selectedScenario].name}
                </Badge>
              </h1>
              <p className=\"text-gray-400 mt-2\">
                {demoSession.client_profile.agency_name} • {demoSession.client_profile.geographic_market}
              </p>
            </div>

            <div className=\"flex items-center space-x-3\">
              <div className=\"text-right text-sm\">
                <div className=\"text-gray-400\">Time Remaining</div>
                <div className=\"text-white font-mono\">{getTimeRemaining()}</div>
              </div>

              <Button
                onClick={extendSession}
                variant=\"outline\"
                size=\"sm\"
              >
                <Clock className=\"w-4 h-4 mr-1\" />
                Extend
              </Button>

              <Button
                onClick={resetDemoSession}
                variant=\"outline\"
                size=\"sm\"
                disabled={loading}
              >
                <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
                Reset
              </Button>

              <Button
                onClick={exportResults}
                variant=\"outline\"
                size=\"sm\"
              >
                <Download className=\"w-4 h-4 mr-1\" />
                Export
              </Button>
            </div>
          </div>

          {/* Key Metrics Overview */}
          <div className=\"grid md:grid-cols-4 gap-4 mt-6\">
            <Card className=\"bg-slate-700 border-slate-600\">
              <CardContent className=\"p-4 text-center\">
                <Users className=\"w-6 h-6 text-blue-400 mx-auto mb-2\" />
                <div className=\"text-2xl font-bold text-white\">{demoSession.client_profile.monthly_leads}</div>
                <div className=\"text-gray-400 text-sm\">Monthly Leads</div>
              </CardContent>
            </Card>

            <Card className=\"bg-slate-700 border-slate-600\">
              <CardContent className=\"p-4 text-center\">
                <DollarSign className=\"w-6 h-6 text-green-400 mx-auto mb-2\" />
                <div className=\"text-2xl font-bold text-white\">
                  ${(demoSession.client_profile.avg_deal_size / 1000).toFixed(0)}K
                </div>
                <div className=\"text-gray-400 text-sm\">Avg Deal Size</div>
              </CardContent>
            </Card>

            <Card className=\"bg-slate-700 border-slate-600\">
              <CardContent className=\"p-4 text-center\">
                <Zap className=\"w-6 h-6 text-yellow-400 mx-auto mb-2\" />
                <div className=\"text-2xl font-bold text-white\">
                  {demoSession.performance_metrics.response_times.jorge_avg}
                </div>
                <div className=\"text-gray-400 text-sm\">Response Time</div>
              </CardContent>
            </Card>

            <Card className=\"bg-slate-700 border-slate-600\">
              <CardContent className=\"p-4 text-center\">
                <TrendingUp className=\"w-6 h-6 text-purple-400 mx-auto mb-2\" />
                <div className=\"text-2xl font-bold text-white\">
                  {demoSession.performance_metrics.business_impact.roi}
                </div>
                <div className=\"text-gray-400 text-sm\">ROI</div>
              </CardContent>
            </Card>
          </div>
        </motion.div>

        {/* Demo Content Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className=\"mb-6\">
            <TabsTrigger value=\"overview\">Overview</TabsTrigger>
            <TabsTrigger value=\"roi\">ROI Analysis</TabsTrigger>
            <TabsTrigger value=\"performance\">Performance</TabsTrigger>
            <TabsTrigger value=\"leads\">Lead Management</TabsTrigger>
            <TabsTrigger value=\"conversations\">Jorge Conversations</TabsTrigger>
            <TabsTrigger value=\"properties\">Property Matching</TabsTrigger>
          </TabsList>

          <AnimatePresence mode=\"wait\">
            <TabsContent value=\"overview\" className=\"space-y-6\">
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                {/* Overview content with client challenges, goals, etc. */}
                <div className=\"grid md:grid-cols-2 gap-6\">
                  <Card className=\"bg-slate-800 border-slate-600\">
                    <CardHeader>
                      <CardTitle className=\"text-white flex items-center\">
                        <Target className=\"w-5 h-5 mr-2\" />
                        Current Challenges
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className=\"space-y-3\">
                        {demoSession.client_profile.current_challenges.map((challenge, idx) => (
                          <div key={idx} className=\"flex items-start space-x-3\">
                            <div className=\"w-2 h-2 bg-red-400 rounded-full mt-2 flex-shrink-0\" />
                            <span className=\"text-gray-300\">{challenge}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card className=\"bg-slate-800 border-slate-600\">
                    <CardHeader>
                      <CardTitle className=\"text-white flex items-center\">
                        <CheckCircle2 className=\"w-5 h-5 mr-2\" />
                        Goals with Jorge AI
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className=\"space-y-3\">
                        {demoSession.client_profile.goals.map((goal, idx) => (
                          <div key={idx} className=\"flex items-start space-x-3\">
                            <div className=\"w-2 h-2 bg-green-400 rounded-full mt-2 flex-shrink-0\" />
                            <span className=\"text-gray-300\">{goal}</span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </motion.div>
            </TabsContent>

            <TabsContent value=\"roi\">
              {/* ROI Analysis content */}
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
              >
                <Card className=\"bg-slate-800 border-slate-600\">
                  <CardHeader>
                    <CardTitle className=\"text-white flex items-center\">
                      <BarChart3 className=\"w-5 h-5 mr-2\" />
                      ROI Analysis: Traditional vs Jorge AI
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className=\"grid md:grid-cols-3 gap-6\">
                      <div className=\"text-center\">
                        <div className=\"text-3xl font-bold text-red-400 mb-2\">
                          ${(demoSession.roi_calculation.summary?.traditional_total_cost || 0).toLocaleString()}
                        </div>
                        <div className=\"text-gray-400\">Traditional Annual Cost</div>
                      </div>

                      <div className=\"text-center\">
                        <div className=\"text-3xl font-bold text-blue-400 mb-2\">
                          ${(demoSession.roi_calculation.summary?.jorge_total_cost || 0).toLocaleString()}
                        </div>
                        <div className=\"text-gray-400\">Jorge AI Annual Cost</div>
                      </div>

                      <div className=\"text-center\">
                        <div className=\"text-3xl font-bold text-green-400 mb-2\">
                          ${(demoSession.roi_calculation.summary?.net_savings || 0).toLocaleString()}
                        </div>
                        <div className=\"text-gray-400\">Annual Savings</div>
                      </div>
                    </div>

                    <div className=\"mt-8\">
                      <div className=\"flex justify-between text-sm text-gray-400 mb-2\">
                        <span>Cost Reduction</span>
                        <span>{(demoSession.roi_calculation.summary?.cost_reduction_percentage || 0).toFixed(1)}%</span>
                      </div>
                      <Progress
                        value={demoSession.roi_calculation.summary?.cost_reduction_percentage || 0}
                        className=\"h-2\"
                      />
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </TabsContent>

            {/* Add other tab content as needed */}
          </AnimatePresence>
        </Tabs>
      </div>
    </div>
  );
}