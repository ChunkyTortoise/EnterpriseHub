// Competitor Comparison Component
// Professional analysis of Jorge vs traditional agents

'use client';

import { useState } from 'react';
import {
  Target,
  TrendingUp,
  Clock,
  Brain,
  Phone,
  Shield,
  Star,
  AlertCircle,
  CheckCircle,
  X,
  Zap,
  Users,
  Award,
  BarChart3
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { type ClientProfile, ROIEngine } from '@/lib/presentation/ROIEngine';

interface CompetitorComparisonProps {
  marketSegment?: ClientProfile['marketSegment'];
  propertyValue?: number;
}

interface CompetitorProfile {
  name: string;
  type: string;
  commission: number;
  strengths: string[];
  weaknesses: string[];
  responseTime: string;
  technology: string;
  experience: string;
  availability: string;
  priceOptimization: number;
  clientSatisfaction: number;
  marketKnowledge: number;
  efficiency: number;
}

export function CompetitorComparison({ marketSegment = 'mid-market', propertyValue = 500000 }: CompetitorComparisonProps) {
  const [selectedComparison, setSelectedComparison] = useState('overview');

  const competitors: CompetitorProfile[] = [
    {
      name: "Jorge's AI Platform",
      type: "AI-Powered Premium",
      commission: 6.0,
      strengths: [
        "24/7 AI qualification",
        "5% price optimization",
        "95% qualification accuracy",
        "Complete automation",
        "Real-time market intelligence"
      ],
      weaknesses: [
        "Higher upfront commission"
      ],
      responseTime: "2 minutes",
      technology: "Advanced AI Platform",
      experience: "AI + Human Expertise",
      availability: "24/7 AI + Business Hours Human",
      priceOptimization: 5.0,
      clientSatisfaction: 92,
      marketKnowledge: 95,
      efficiency: 90,
    },
    {
      name: "Traditional Full Service",
      type: "Traditional Agent",
      commission: 3.0,
      strengths: [
        "Lower commission",
        "Personal relationship",
        "Local market knowledge",
        "Established network"
      ],
      weaknesses: [
        "Limited availability",
        "Manual processes",
        "Slower response times",
        "Variable quality",
        "Human limitations"
      ],
      responseTime: "6+ hours",
      technology: "Basic CRM",
      experience: "Human Only",
      availability: "Business Hours Only",
      priceOptimization: 0.5,
      clientSatisfaction: 72,
      marketKnowledge: 70,
      efficiency: 45,
    },
    {
      name: "Discount Broker",
      type: "Low-Cost Provider",
      commission: 1.5,
      strengths: [
        "Lowest cost",
        "Basic MLS access",
        "Simple transactions"
      ],
      weaknesses: [
        "Minimal service",
        "No market expertise",
        "Limited support",
        "Self-service model",
        "No qualification"
      ],
      responseTime: "24+ hours",
      technology: "Basic Website",
      experience: "Minimal Support",
      availability: "Self-Service",
      priceOptimization: 0,
      clientSatisfaction: 58,
      marketKnowledge: 40,
      efficiency: 30,
    },
    {
      name: "Tech-Forward Agent",
      type: "Modern Traditional",
      commission: 3.5,
      strengths: [
        "Some automation",
        "Digital marketing",
        "CRM integration",
        "Online presence"
      ],
      weaknesses: [
        "Limited AI capabilities",
        "Still manual qualification",
        "Human bottlenecks",
        "Inconsistent technology use"
      ],
      responseTime: "2-4 hours",
      technology: "Modern CRM + Some Tools",
      experience: "Tech-Savvy Human",
      availability: "Extended Hours",
      priceOptimization: 1.5,
      clientSatisfaction: 78,
      marketKnowledge: 75,
      efficiency: 65,
    }
  ];

  const jorge = competitors[0];
  const traditional = competitors[1];

  const calculateValueComparison = (competitor: CompetitorProfile) => {
    const commissionCost = propertyValue * (competitor.commission / 100);
    const priceOptimizationValue = propertyValue * (competitor.priceOptimization / 100);
    const efficiencyValue = (competitor.efficiency / 100) * 25000; // Time value
    const satisfactionValue = (competitor.clientSatisfaction / 100) * 15000; // Referral value

    const totalValue = priceOptimizationValue + efficiencyValue + satisfactionValue;
    const netValue = totalValue - commissionCost;

    return {
      commissionCost,
      priceOptimizationValue,
      totalValue,
      netValue,
      roiMultiple: totalValue / commissionCost
    };
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-50';
    if (score >= 75) return 'text-blue-600 bg-blue-50';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getScoreIcon = (score: number) => {
    if (score >= 90) return <Star className="w-4 h-4" />;
    if (score >= 75) return <CheckCircle className="w-4 h-4" />;
    if (score >= 60) return <AlertCircle className="w-4 h-4" />;
    return <X className="w-4 h-4" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-2xl">
            <Target className="w-6 h-6 text-blue-600" />
            Competitive Analysis: Jorge vs Traditional Agents
          </CardTitle>
          <p className="text-gray-600">
            Professional comparison of Jorge's AI platform against traditional real estate services
          </p>
          <div className="flex items-center gap-4 mt-3">
            <Badge variant="outline">
              {marketSegment} Market
            </Badge>
            <Badge variant="outline">
              Property Value: {ROIEngine.formatCurrency(propertyValue)}
            </Badge>
          </div>
        </CardHeader>
      </Card>

      <Tabs value={selectedComparison} onValueChange={setSelectedComparison} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="detailed">Detailed Analysis</TabsTrigger>
          <TabsTrigger value="value">Value Comparison</TabsTrigger>
          <TabsTrigger value="scenarios">Use Cases</TabsTrigger>
        </TabsList>

        {/* Overview Comparison */}
        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Jorge AI Platform */}
            <Card className="border-2 border-blue-200 bg-blue-50/30">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5 text-blue-600" />
                  Jorge's AI Platform
                </CardTitle>
                <Badge className="w-fit bg-blue-600 text-white">6% Premium Commission</Badge>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-white rounded-lg">
                    <div className="text-2xl font-bold text-blue-600 mb-1">2 min</div>
                    <div className="text-xs text-gray-600">Response Time</div>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg">
                    <div className="text-2xl font-bold text-green-600 mb-1">95%</div>
                    <div className="text-xs text-gray-600">Qualification Accuracy</div>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg">
                    <div className="text-2xl font-bold text-purple-600 mb-1">5%</div>
                    <div className="text-xs text-gray-600">Price Optimization</div>
                  </div>
                  <div className="text-center p-3 bg-white rounded-lg">
                    <div className="text-2xl font-bold text-orange-600 mb-1">24/7</div>
                    <div className="text-xs text-gray-600">AI Availability</div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-sm mb-2">Key Advantages:</h4>
                  <div className="space-y-1">
                    {jorge.strengths.map((strength, index) => (
                      <div key={index} className="flex items-center gap-2 text-sm">
                        <CheckCircle className="w-3 h-3 text-green-600 flex-shrink-0" />
                        <span>{strength}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="font-semibold text-green-800 text-sm">Value Proposition:</div>
                  <div className="text-green-700 text-sm mt-1">
                    {(calculateValueComparison(jorge).roiMultiple).toFixed(1)}x ROI through AI optimization,
                    delivering {ROIEngine.formatCurrency(calculateValueComparison(jorge).netValue)} net value
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Traditional Agent */}
            <Card className="border-2 border-gray-200">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-gray-600" />
                  Traditional Agent
                </CardTitle>
                <Badge variant="outline" className="w-fit">3% Standard Commission</Badge>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-600 mb-1">6+ hrs</div>
                    <div className="text-xs text-gray-600">Response Time</div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-yellow-600 mb-1">65%</div>
                    <div className="text-xs text-gray-600">Qualification Accuracy</div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-red-600 mb-1">0.5%</div>
                    <div className="text-xs text-gray-600">Price Optimization</div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-600 mb-1">9-5</div>
                    <div className="text-xs text-gray-600">Availability</div>
                  </div>
                </div>

                <div>
                  <h4 className="font-semibold text-sm mb-2">Limitations:</h4>
                  <div className="space-y-1">
                    {traditional.weaknesses.map((weakness, index) => (
                      <div key={index} className="flex items-center gap-2 text-sm">
                        <X className="w-3 h-3 text-red-500 flex-shrink-0" />
                        <span>{weakness}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <div className="font-semibold text-yellow-800 text-sm">Value Concern:</div>
                  <div className="text-yellow-700 text-sm mt-1">
                    Lower commission but {ROIEngine.formatCurrency(calculateValueComparison(jorge).netValue - calculateValueComparison(traditional).netValue)} less value delivery due to manual limitations
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Quick Comparison Table */}
          <Card>
            <CardHeader>
              <CardTitle>At-a-Glance Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Feature</th>
                      <th className="text-center py-2">Jorge AI</th>
                      <th className="text-center py-2">Traditional</th>
                      <th className="text-center py-2">Advantage</th>
                    </tr>
                  </thead>
                  <tbody className="space-y-2">
                    <tr className="border-b">
                      <td className="py-3 font-medium">Response Time</td>
                      <td className="text-center text-green-600 font-bold">2 minutes</td>
                      <td className="text-center text-red-600">6+ hours</td>
                      <td className="text-center">
                        <Badge variant="outline" className="text-green-700 border-green-200">
                          18x faster
                        </Badge>
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="py-3 font-medium">Qualification Accuracy</td>
                      <td className="text-center text-green-600 font-bold">95%</td>
                      <td className="text-center text-yellow-600">65%</td>
                      <td className="text-center">
                        <Badge variant="outline" className="text-green-700 border-green-200">
                          +46% better
                        </Badge>
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="py-3 font-medium">Price Optimization</td>
                      <td className="text-center text-green-600 font-bold">5%</td>
                      <td className="text-center text-red-600">0.5%</td>
                      <td className="text-center">
                        <Badge variant="outline" className="text-green-700 border-green-200">
                          10x better
                        </Badge>
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="py-3 font-medium">Availability</td>
                      <td className="text-center text-green-600 font-bold">24/7</td>
                      <td className="text-center text-gray-600">Business Hours</td>
                      <td className="text-center">
                        <Badge variant="outline" className="text-green-700 border-green-200">
                          Always on
                        </Badge>
                      </td>
                    </tr>
                    <tr className="border-b">
                      <td className="py-3 font-medium">Client Satisfaction</td>
                      <td className="text-center text-green-600 font-bold">92%</td>
                      <td className="text-center text-yellow-600">72%</td>
                      <td className="text-center">
                        <Badge variant="outline" className="text-green-700 border-green-200">
                          +28% higher
                        </Badge>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Detailed Analysis */}
        <TabsContent value="detailed">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {competitors.map((competitor, index) => (
              <Card key={index} className={index === 0 ? 'border-2 border-blue-200' : ''}>
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">{competitor.name}</CardTitle>
                  <Badge variant="outline" className="w-fit text-xs">
                    {competitor.type}
                  </Badge>
                  <div className="text-2xl font-bold">
                    {competitor.commission}% Commission
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Performance Scores */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs">Price Optimization:</span>
                      <div className={`px-2 py-1 rounded text-xs font-bold flex items-center gap-1 ${getScoreColor(competitor.priceOptimization * 20)}`}>
                        {getScoreIcon(competitor.priceOptimization * 20)}
                        {competitor.priceOptimization}%
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs">Satisfaction:</span>
                      <div className={`px-2 py-1 rounded text-xs font-bold flex items-center gap-1 ${getScoreColor(competitor.clientSatisfaction)}`}>
                        {getScoreIcon(competitor.clientSatisfaction)}
                        {competitor.clientSatisfaction}%
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs">Market Knowledge:</span>
                      <div className={`px-2 py-1 rounded text-xs font-bold flex items-center gap-1 ${getScoreColor(competitor.marketKnowledge)}`}>
                        {getScoreIcon(competitor.marketKnowledge)}
                        {competitor.marketKnowledge}%
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs">Efficiency:</span>
                      <div className={`px-2 py-1 rounded text-xs font-bold flex items-center gap-1 ${getScoreColor(competitor.efficiency)}`}>
                        {getScoreIcon(competitor.efficiency)}
                        {competitor.efficiency}%
                      </div>
                    </div>
                  </div>

                  {/* Key Details */}
                  <div className="space-y-2 text-xs">
                    <div>
                      <span className="font-medium">Response:</span> {competitor.responseTime}
                    </div>
                    <div>
                      <span className="font-medium">Technology:</span> {competitor.technology}
                    </div>
                    <div>
                      <span className="font-medium">Availability:</span> {competitor.availability}
                    </div>
                  </div>

                  {/* Value Calculation */}
                  <div className="pt-2 border-t">
                    <div className="text-center">
                      <div className="text-lg font-bold text-blue-600">
                        {ROIEngine.formatCurrency(calculateValueComparison(competitor).netValue)}
                      </div>
                      <div className="text-xs text-gray-600">Net Value</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Value Comparison */}
        <TabsContent value="value">
          <Card>
            <CardHeader>
              <CardTitle>Total Value Analysis</CardTitle>
              <p className="text-gray-600">Complete cost-benefit comparison for {ROIEngine.formatCurrency(propertyValue)} property</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {competitors.map((competitor, index) => {
                  const analysis = calculateValueComparison(competitor);
                  return (
                    <div key={index} className={`p-4 rounded-lg border-2 ${index === 0 ? 'border-blue-200 bg-blue-50' : 'border-gray-200 bg-gray-50'}`}>
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-bold">{competitor.name}</h3>
                        <Badge variant={index === 0 ? "default" : "outline"}>
                          {competitor.commission}% Commission
                        </Badge>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 text-center">
                        <div>
                          <div className="text-lg font-bold text-red-600">
                            {ROIEngine.formatCurrency(analysis.commissionCost)}
                          </div>
                          <div className="text-xs text-gray-600">Commission Cost</div>
                        </div>
                        <div>
                          <div className="text-lg font-bold text-green-600">
                            {ROIEngine.formatCurrency(analysis.priceOptimizationValue)}
                          </div>
                          <div className="text-xs text-gray-600">Price Optimization</div>
                        </div>
                        <div>
                          <div className="text-lg font-bold text-blue-600">
                            {ROIEngine.formatCurrency(analysis.totalValue)}
                          </div>
                          <div className="text-xs text-gray-600">Total Value</div>
                        </div>
                        <div>
                          <div className={`text-lg font-bold ${analysis.netValue > 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {ROIEngine.formatCurrency(analysis.netValue)}
                          </div>
                          <div className="text-xs text-gray-600">Net Value</div>
                        </div>
                        <div>
                          <div className="text-lg font-bold text-purple-600">
                            {analysis.roiMultiple.toFixed(1)}x
                          </div>
                          <div className="text-xs text-gray-600">ROI Multiple</div>
                        </div>
                      </div>

                      {index === 0 && (
                        <div className="mt-4 p-3 bg-green-100 rounded-lg border border-green-200">
                          <div className="text-sm font-semibold text-green-800">
                            Best Value: {ROIEngine.formatCurrency(analysis.netValue - calculateValueComparison(competitors[1]).netValue)} more value than traditional agents
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Use Case Scenarios */}
        <TabsContent value="scenarios">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">When to Choose Jorge's AI Platform</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium">High-Value Properties ($500K+)</div>
                      <div className="text-sm text-gray-600">AI optimization justifies premium commission</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium">Time-Sensitive Transactions</div>
                      <div className="text-sm text-gray-600">24/7 AI ensures no missed opportunities</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium">Investment Properties</div>
                      <div className="text-sm text-gray-600">Data-driven insights maximize ROI</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium">Luxury Market</div>
                      <div className="text-sm text-gray-600">Premium service with AI efficiency</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium">First-Time Buyers/Sellers</div>
                      <div className="text-sm text-gray-600">AI education prevents costly mistakes</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Traditional Agent Limitations</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium">Limited Availability</div>
                      <div className="text-sm text-gray-600">Business hours only, missed evening/weekend leads</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium">Manual Qualification</div>
                      <div className="text-sm text-gray-600">Inconsistent screening, wasted time on unqualified leads</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium">Outdated Market Analysis</div>
                      <div className="text-sm text-gray-600">Static CMAs vs real-time AI pricing</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium">Process Bottlenecks</div>
                      <div className="text-sm text-gray-600">Human limitations create delays and errors</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <X className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="font-medium">No Predictive Analytics</div>
                      <div className="text-sm text-gray-600">Reactive approach misses market opportunities</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* ROI Comparison Summary */}
          <Card className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-200">
            <CardContent className="p-6">
              <div className="text-center">
                <h3 className="text-2xl font-bold text-gray-900 mb-4">The Bottom Line</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                  <div>
                    <div className="text-3xl font-bold text-green-600 mb-1">
                      {(calculateValueComparison(jorge).roiMultiple).toFixed(1)}x
                    </div>
                    <div className="text-sm text-gray-600">Jorge's ROI Multiple</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-blue-600 mb-1">
                      {ROIEngine.formatCurrency(calculateValueComparison(jorge).netValue - calculateValueComparison(traditional).netValue)}
                    </div>
                    <div className="text-sm text-gray-600">Additional Value vs Traditional</div>
                  </div>
                  <div>
                    <div className="text-3xl font-bold text-purple-600 mb-1">95%</div>
                    <div className="text-sm text-gray-600">AI Qualification Accuracy</div>
                  </div>
                </div>
                <p className="text-lg text-gray-700">
                  Jorge's 6% commission delivers {(calculateValueComparison(jorge).roiMultiple).toFixed(1)}x value through AI optimization,
                  making it the superior choice for serious real estate transactions.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}