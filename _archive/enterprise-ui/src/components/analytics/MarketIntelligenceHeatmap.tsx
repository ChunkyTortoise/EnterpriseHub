/**
 * Market Intelligence Heatmap - Rancho Cucamonga Real Estate Analysis
 *
 * Interactive market intelligence visualization showing geospatial insights
 * for Rancho Cucamonga real estate markets with opportunity scoring and risk assessment.
 *
 * Future Enhancement: Full Deck.gl integration for 3D geographic visualization
 * Current: Professional placeholder with data structures and UI patterns
 */

'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Map,
  MapPin,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Home,
  Clock,
  AlertTriangle,
  Target,
  Activity,
  Filter
} from 'lucide-react';

// Market Intelligence Data Types
interface MarketArea {
  area_id: string;
  area_name: string;
  coordinates: [number, number];
  avg_price: number;
  price_change_30d: number;
  inventory_level: number;
  days_on_market: number;
  sale_velocity: number;
  opportunity_score: number;
  risk_factors: string[];
  key_insights: string[];
  hotness_rating: 'hot' | 'warm' | 'lukewarm' | 'cold';
}

interface MarketIntelligenceHeatmapProps {
  selectedArea?: string;
  onAreaSelect?: (areaId: string) => void;
  className?: string;
}

// Mock Rancho Cucamonga market data
const mockRancho CucamongaMarketData: MarketArea[] = [
  {
    area_id: 'rancho_cucamonga-central',
    area_name: 'Central Rancho Cucamonga',
    coordinates: [-97.7431, 30.2672],
    avg_price: 785000,
    price_change_30d: 8.3,
    inventory_level: 23,
    days_on_market: 18,
    sale_velocity: 94.2,
    opportunity_score: 87.5,
    risk_factors: ['High competition', 'Price volatility'],
    key_insights: ['Strong appreciation trend', 'Low inventory creates urgency'],
    hotness_rating: 'hot'
  },
  {
    area_id: 'rancho_cucamonga-south',
    area_name: 'South Rancho Cucamonga',
    coordinates: [-97.7431, 30.2172],
    avg_price: 612000,
    price_change_30d: 5.7,
    inventory_level: 34,
    days_on_market: 28,
    sale_velocity: 78.9,
    opportunity_score: 72.3,
    risk_factors: ['Seasonal fluctuation'],
    key_insights: ['Family-friendly market growth', 'Good value proposition'],
    hotness_rating: 'warm'
  },
  {
    area_id: 'rancho_cucamonga-east',
    area_name: 'East Rancho Cucamonga',
    coordinates: [-97.7031, 30.2672],
    avg_price: 545000,
    price_change_30d: 12.1,
    inventory_level: 28,
    days_on_market: 22,
    sale_velocity: 85.6,
    opportunity_score: 81.2,
    risk_factors: ['Gentrification pace', 'Infrastructure development'],
    key_insights: ['Highest appreciation rate', 'Emerging neighborhood potential'],
    hotness_rating: 'hot'
  },
  {
    area_id: 'rancho_cucamonga-west',
    area_name: 'West Rancho Cucamonga',
    coordinates: [-97.7831, 30.2672],
    avg_price: 923000,
    price_change_30d: 3.2,
    inventory_level: 41,
    days_on_market: 45,
    sale_velocity: 65.4,
    opportunity_score: 58.7,
    risk_factors: ['High price point', 'Market saturation'],
    key_insights: ['Luxury market stability', 'Slower but consistent sales'],
    hotness_rating: 'lukewarm'
  },
  {
    area_id: 'rancho_cucamonga-north',
    area_name: 'North Rancho Cucamonga',
    coordinates: [-97.7431, 30.3172],
    avg_price: 467000,
    price_change_30d: 6.8,
    inventory_level: 52,
    days_on_market: 35,
    sale_velocity: 71.2,
    opportunity_score: 69.5,
    risk_factors: ['Distance from downtown', 'Transportation access'],
    key_insights: ['Affordability advantage', 'Tech corridor proximity'],
    hotness_rating: 'warm'
  },
  {
    area_id: 'rancho_cucamonga-northwest',
    area_name: 'Northwest Rancho Cucamonga',
    coordinates: [-97.7831, 30.3372],
    avg_price: 734000,
    price_change_30d: 1.9,
    inventory_level: 67,
    days_on_market: 52,
    sale_velocity: 56.8,
    opportunity_score: 48.3,
    risk_factors: ['Market cooldown', 'Overpricing trends'],
    key_insights: ['Buyer\'s market emerging', 'Negotiation opportunities'],
    hotness_rating: 'cold'
  }
];

export function MarketIntelligenceHeatmap({
  selectedArea = 'rancho_cucamonga-central',
  onAreaSelect,
  className = ''
}: MarketIntelligenceHeatmapProps) {
  const [viewMode, setViewMode] = useState<'heatmap' | 'list' | 'insights'>('heatmap');
  const [selectedAreaData, setSelectedAreaData] = useState<MarketArea>(
    mockRancho CucamongaMarketData.find(area => area.area_id === selectedArea) || mockRancho CucamongaMarketData[0]
  );

  const getHotnessColor = (rating: string) => {
    switch (rating) {
      case 'hot': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'warm': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'lukewarm': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'cold': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getOpportunityBadge = (score: number) => {
    if (score >= 80) return { text: 'Excellent', color: 'bg-green-500/20 text-green-400' };
    if (score >= 70) return { text: 'Good', color: 'bg-yellow-500/20 text-yellow-400' };
    if (score >= 60) return { text: 'Moderate', color: 'bg-orange-500/20 text-orange-400' };
    return { text: 'Low', color: 'bg-red-500/20 text-red-400' };
  };

  const handleAreaClick = (area: MarketArea) => {
    setSelectedAreaData(area);
    onAreaSelect?.(area.area_id);
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Market Overview Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-slate-800/30 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded text-blue-400">
                <Map className="h-4 w-4" />
              </div>
              <div>
                <div className="text-lg font-bold text-slate-100">{mockRancho CucamongaMarketData.length}</div>
                <div className="text-xs text-slate-500">Market Areas</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/30 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-500/10 rounded text-green-400">
                <DollarSign className="h-4 w-4" />
              </div>
              <div>
                <div className="text-lg font-bold text-slate-100">
                  ${(mockRancho CucamongaMarketData.reduce((sum, area) => sum + area.avg_price, 0) / mockRancho CucamongaMarketData.length / 1000).toFixed(0)}K
                </div>
                <div className="text-xs text-slate-500">Avg Price</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/30 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-500/10 rounded text-orange-400">
                <Clock className="h-4 w-4" />
              </div>
              <div>
                <div className="text-lg font-bold text-slate-100">
                  {Math.round(mockRancho CucamongaMarketData.reduce((sum, area) => sum + area.days_on_market, 0) / mockRancho CucamongaMarketData.length)}
                </div>
                <div className="text-xs text-slate-500">Avg DOM</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/30 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded text-purple-400">
                <Target className="h-4 w-4" />
              </div>
              <div>
                <div className="text-lg font-bold text-slate-100">
                  {mockRancho CucamongaMarketData.filter(area => area.hotness_rating === 'hot' || area.hotness_rating === 'warm').length}
                </div>
                <div className="text-xs text-slate-500">Hot Markets</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Market Intelligence Interface */}
      <Card className="bg-slate-900/50 border-slate-800">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-slate-100 flex items-center gap-2">
                <Map className="h-5 w-5 text-emerald-400" />
                Rancho Cucamonga Market Intelligence Heatmap
              </CardTitle>
              <CardDescription className="text-slate-400">
                Real-time market analysis with geospatial intelligence and opportunity mapping
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="border-slate-600 text-slate-300"
              >
                <Filter className="h-3 w-3 mr-1" />
                Filters
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <Tabs value={viewMode} onValueChange={(value) => setViewMode(value as any)} className="space-y-4">
            <TabsList className="bg-slate-800 border-slate-700">
              <TabsTrigger value="heatmap">Heatmap View</TabsTrigger>
              <TabsTrigger value="list">Market List</TabsTrigger>
              <TabsTrigger value="insights">AI Insights</TabsTrigger>
            </TabsList>

            {/* Heatmap View */}
            <TabsContent value="heatmap" className="space-y-4">
              <div className="bg-slate-800/30 p-8 rounded-lg border border-slate-700 relative">
                {/* Map Placeholder */}
                <div className="aspect-[16/10] bg-slate-700/20 rounded-lg border border-slate-600 relative overflow-hidden">
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <Map className="h-16 w-16 text-slate-600 mx-auto mb-4" />
                      <p className="text-slate-400 mb-2">Interactive Market Heatmap</p>
                      <p className="text-slate-500 text-sm max-w-md">
                        Deck.gl-powered 3D market visualization will be rendered here with
                        real-time opportunity scoring and risk assessment overlays
                      </p>
                      <Badge className="mt-4 bg-emerald-500/10 text-emerald-400">
                        Deck.gl Integration Coming Soon
                      </Badge>
                    </div>
                  </div>

                  {/* Market Area Indicators (Placeholder) */}
                  <div className="absolute inset-0 p-4">
                    {mockRancho CucamongaMarketData.map((area, index) => (
                      <div
                        key={area.area_id}
                        className={`absolute w-12 h-12 rounded-full border-2 cursor-pointer transform -translate-x-1/2 -translate-y-1/2 transition-all hover:scale-110 ${
                          area.area_id === selectedAreaData.area_id
                            ? 'bg-blue-500/30 border-blue-400 ring-4 ring-blue-500/20'
                            : getHotnessColor(area.hotness_rating).replace('text-', 'border-').replace('/20', '/40')
                        }`}
                        style={{
                          left: `${20 + (index * 15) % 60}%`,
                          top: `${30 + (index * 12) % 40}%`
                        }}
                        onClick={() => handleAreaClick(area)}
                      >
                        <div className="w-full h-full rounded-full bg-current opacity-20"></div>
                        <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 whitespace-nowrap">
                          <div className="text-xs text-slate-300 font-medium">
                            {area.area_name.split(' ')[0]}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Selected Area Details */}
                {selectedAreaData && (
                  <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div className="flex items-center gap-3">
                        <MapPin className="h-5 w-5 text-blue-400" />
                        <h3 className="text-lg font-semibold text-slate-100">{selectedAreaData.area_name}</h3>
                        <Badge className={getHotnessColor(selectedAreaData.hotness_rating)}>
                          {selectedAreaData.hotness_rating}
                        </Badge>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-slate-800/50 p-3 rounded border border-slate-700">
                          <div className="text-sm text-slate-400">Average Price</div>
                          <div className="text-xl font-bold text-slate-100">
                            ${selectedAreaData.avg_price.toLocaleString()}
                          </div>
                          <div className={`text-sm flex items-center gap-1 ${
                            selectedAreaData.price_change_30d > 0 ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {selectedAreaData.price_change_30d > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                            {selectedAreaData.price_change_30d > 0 ? '+' : ''}{selectedAreaData.price_change_30d}% (30d)
                          </div>
                        </div>

                        <div className="bg-slate-800/50 p-3 rounded border border-slate-700">
                          <div className="text-sm text-slate-400">Days on Market</div>
                          <div className="text-xl font-bold text-slate-100">
                            {selectedAreaData.days_on_market}
                          </div>
                          <div className="text-sm text-slate-500">
                            {selectedAreaData.inventory_level} active listings
                          </div>
                        </div>

                        <div className="bg-slate-800/50 p-3 rounded border border-slate-700">
                          <div className="text-sm text-slate-400">Sale Velocity</div>
                          <div className="text-xl font-bold text-slate-100">
                            {selectedAreaData.sale_velocity}%
                          </div>
                          <div className="text-sm text-slate-500">Market activity</div>
                        </div>

                        <div className="bg-slate-800/50 p-3 rounded border border-slate-700">
                          <div className="text-sm text-slate-400">Opportunity Score</div>
                          <div className="text-xl font-bold text-slate-100">
                            {selectedAreaData.opportunity_score.toFixed(1)}
                          </div>
                          <Badge className={getOpportunityBadge(selectedAreaData.opportunity_score).color + ' text-xs'}>
                            {getOpportunityBadge(selectedAreaData.opportunity_score).text}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <h4 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                          <AlertTriangle className="h-4 w-4 text-yellow-400" />
                          Risk Factors
                        </h4>
                        <div className="space-y-1">
                          {selectedAreaData.risk_factors.map((risk, index) => (
                            <div key={index} className="text-sm text-slate-400">
                              • {risk}
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="text-sm font-medium text-slate-300 mb-2 flex items-center gap-2">
                          <Activity className="h-4 w-4 text-green-400" />
                          Key Insights
                        </h4>
                        <div className="space-y-1">
                          {selectedAreaData.key_insights.map((insight, index) => (
                            <div key={index} className="text-sm text-slate-400">
                              • {insight}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Market List View */}
            <TabsContent value="list" className="space-y-4">
              <div className="grid gap-4">
                {mockRancho CucamongaMarketData.map((area) => (
                  <Card
                    key={area.area_id}
                    className="bg-slate-800/30 border-slate-700 hover:border-blue-500/30 transition-all cursor-pointer"
                    onClick={() => handleAreaClick(area)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`w-4 h-4 rounded-full ${
                            area.hotness_rating === 'hot' ? 'bg-red-500' :
                            area.hotness_rating === 'warm' ? 'bg-orange-500' :
                            area.hotness_rating === 'lukewarm' ? 'bg-yellow-500' : 'bg-blue-500'
                          }`}></div>
                          <div>
                            <h3 className="text-slate-100 font-medium">{area.area_name}</h3>
                            <p className="text-slate-400 text-sm">${area.avg_price.toLocaleString()}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-sm">
                          <div className="text-center">
                            <div className="text-slate-100 font-medium">{area.days_on_market}d</div>
                            <div className="text-slate-500">DOM</div>
                          </div>
                          <div className="text-center">
                            <div className="text-slate-100 font-medium">{area.sale_velocity}%</div>
                            <div className="text-slate-500">Velocity</div>
                          </div>
                          <Badge className={getOpportunityBadge(area.opportunity_score).color}>
                            {area.opportunity_score.toFixed(0)}
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* AI Insights View */}
            <TabsContent value="insights" className="space-y-4">
              <div className="bg-slate-800/30 p-6 rounded-lg border border-slate-700">
                <div className="text-center mb-6">
                  <Activity className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                  <p className="text-slate-400 mb-2">AI-Powered Market Intelligence</p>
                  <p className="text-slate-500 text-sm">
                    Advanced market analysis, trend prediction, and opportunity identification
                  </p>
                </div>

                <div className="grid gap-4">
                  <div className="p-4 bg-green-900/20 border border-green-800/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="h-4 w-4 text-green-400" />
                      <span className="font-medium text-green-200">Market Opportunity Alert</span>
                    </div>
                    <p className="text-green-100 text-sm">
                      East Rancho Cucamonga showing strongest appreciation signals with 12.1% 30-day growth.
                      Recommend immediate lead generation focus in this area.
                    </p>
                  </div>

                  <div className="p-4 bg-yellow-900/20 border border-yellow-800/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="h-4 w-4 text-yellow-400" />
                      <span className="font-medium text-yellow-200">Market Shift Detection</span>
                    </div>
                    <p className="text-yellow-100 text-sm">
                      Northwest Rancho Cucamonga entering buyer's market conditions. Adjust pricing strategy
                      and increase negotiation coaching for agents.
                    </p>
                  </div>

                  <div className="p-4 bg-blue-900/20 border border-blue-800/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="h-4 w-4 text-blue-400" />
                      <span className="font-medium text-blue-200">Strategic Recommendation</span>
                    </div>
                    <p className="text-blue-100 text-sm">
                      Central Rancho Cucamonga inventory shortage creates seller's market opportunity.
                      Deploy Jorge's confrontational qualification to identify motivated sellers.
                    </p>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}

export default MarketIntelligenceHeatmap;