/**
 * Advanced Analytics Interface - SHAP Analysis & Market Intelligence
 *
 * Integrates with Jorge's Phase 7 Advanced Analytics Backend to provide:
 * - SHAP waterfall charts using Recharts for ML explainability
 * - Austin market intelligence heatmaps using Deck.gl
 * - Real-time performance metrics with <50ms API response targets
 * - Export and sharing capabilities for professional reporting
 *
 * Performance Targets:
 * - SHAP generation: <30ms waterfall creation
 * - Market analysis: <50ms geospatial intelligence
 * - Real-time updates: <10ms WebSocket event delivery
 */

'use client';

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import {
  BarChart3,
  TrendingUp,
  Map,
  Download,
  Share2,
  Zap,
  Target,
  Activity,
  Clock,
  MapPin,
  DollarSign,
  Brain,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Plus,
  Filter,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Eye
} from 'lucide-react';
import { useAgentStore } from '@/store/useAgentStore';
import { SHAPWaterfallChart } from './SHAPWaterfallChart';
import { MarketIntelligenceHeatmap } from './MarketIntelligenceHeatmap';

// Analytics Data Types
interface SHAPWaterfallData {
  feature: string;
  contribution: number;
  cumulative: number;
  importance: number;
  direction: 'positive' | 'negative';
  description: string;
}

interface SHAPAnalysis {
  analysis_id: string;
  lead_id: string;
  prediction_score: number;
  base_value: number;
  final_prediction: number;
  confidence: number;
  features: SHAPWaterfallData[];
  generated_at: string;
  processing_time_ms: number;
}

interface MarketIntelligenceData {
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
}

interface PerformanceMetrics {
  total_analyses: number;
  avg_processing_time_ms: number;
  api_response_time_ms: number;
  cache_hit_rate: number;
  accuracy_score: number;
  uptime_percentage: number;
}

interface AdvancedAnalyticsProps {
  locationId: string;
  className?: string;
}

export function AdvancedAnalyticsInterface({ locationId, className = '' }: AdvancedAnalyticsProps) {
  // State Management
  const [activeTab, setActiveTab] = useState<'shap' | 'market' | 'performance'>('shap');
  const [shapAnalysis, setSHAPAnalysis] = useState<SHAPAnalysis | null>(null);
  const [marketData, setMarketData] = useState<MarketIntelligenceData[]>([]);
  const [performanceMetrics, setPerformanceMetrics] = useState<PerformanceMetrics | null>(null);
  const [selectedLeadId, setSelectedLeadId] = useState<string>('demo-lead-123');
  const [selectedArea, setSelectedArea] = useState<string>('austin-central');
  const [isLoading, setIsLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [exportDialog, setExportDialog] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  // Store integration
  const { addEntry, addIntelligenceAlert, connectBIWebSockets, getBIConnectionHealth, getConnectionStatus } = useAgentStore();

  // Initialize component and connect to enhanced WebSocket system
  useEffect(() => {
    initializeAnalytics();

    // Connect to BI WebSockets using the enhanced management system
    connectBIWebSockets(locationId);

    return () => {
      // Cleanup handled by AgentStore disconnectBIWebSockets
    };
  }, [locationId, connectBIWebSockets]);

  const initializeAnalytics = async () => {
    setIsLoading(true);

    try {
      // Load initial data in parallel
      await Promise.all([
        fetchSHAPAnalysis(),
        fetchMarketIntelligence(),
        fetchPerformanceMetrics()
      ]);

      setLastUpdate(new Date().toISOString());
    } catch (err) {
      console.error('Failed to initialize analytics:', err);
      setError('Failed to load analytics data');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchSHAPAnalysis = async () => {
    try {
      const startTime = Date.now();

      const response = await fetch(`/api/v1/analytics/shap/${selectedLeadId}`, {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`SHAP analysis failed: ${response.status}`);
      }

      const data: SHAPAnalysis = await response.json();
      setSHAPAnalysis(data);

      const processingTime = Date.now() - startTime;

      // Track performance in agent store
      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'advanced_analytics',
        key: 'shap_analysis_loaded',
        value: {
          lead_id: selectedLeadId,
          processing_time_ms: processingTime,
          prediction_score: data.prediction_score,
          confidence: data.confidence
        }
      });

      // Alert if processing time exceeds target
      if (processingTime > 30) {
        addIntelligenceAlert({
          type: 'performance',
          severity: 'medium',
          title: 'SHAP Analysis Slow',
          message: `SHAP generation took ${processingTime}ms (target: <30ms)`,
          timestamp: new Date().toISOString(),
          data: { lead_id: selectedLeadId, processing_time_ms: processingTime }
        });
      }

    } catch (err) {
      console.error('SHAP analysis error:', err);
      throw err;
    }
  };

  const fetchMarketIntelligence = async () => {
    try {
      const startTime = Date.now();

      const response = await fetch(`/api/v1/analytics/market-intelligence/austin?area=${selectedArea}`, {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Market intelligence failed: ${response.status}`);
      }

      const data: MarketIntelligenceData[] = await response.json();
      setMarketData(data);

      const processingTime = Date.now() - startTime;

      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'advanced_analytics',
        key: 'market_intelligence_loaded',
        value: {
          area: selectedArea,
          areas_count: data.length,
          processing_time_ms: processingTime
        }
      });

      // Alert if processing time exceeds target
      if (processingTime > 50) {
        addIntelligenceAlert({
          type: 'performance',
          severity: 'medium',
          title: 'Market Analysis Slow',
          message: `Market intelligence took ${processingTime}ms (target: <50ms)`,
          timestamp: new Date().toISOString(),
          data: { area: selectedArea, processing_time_ms: processingTime }
        });
      }

    } catch (err) {
      console.error('Market intelligence error:', err);
      throw err;
    }
  };

  const fetchPerformanceMetrics = async () => {
    try {
      const response = await fetch('/api/v1/analytics/performance', {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Performance metrics failed: ${response.status}`);
      }

      const data: PerformanceMetrics = await response.json();
      setPerformanceMetrics(data);

    } catch (err) {
      console.error('Performance metrics error:', err);
      throw err;
    }
  };

  const generateNewSHAPAnalysis = async () => {
    setIsGenerating(true);

    try {
      const response = await fetch(`/api/v1/analytics/shap/generate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          lead_id: selectedLeadId,
          include_confidence_intervals: true,
          explanation_depth: 'detailed'
        })
      });

      if (!response.ok) {
        throw new Error(`SHAP generation failed: ${response.status}`);
      }

      const result = await response.json();

      // Refresh data
      await fetchSHAPAnalysis();

      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'advanced_analytics',
        key: 'shap_analysis_generated',
        value: {
          lead_id: selectedLeadId,
          generation_time_ms: result.processing_time_ms
        }
      });

    } catch (err) {
      console.error('SHAP generation error:', err);
      setError('Failed to generate SHAP analysis');
    } finally {
      setIsGenerating(false);
    }
  };

  const getAuthToken = () => {
    // In production, this would get the actual JWT token
    return 'demo-token';
  };

  const handleFeatureClick = (feature: any) => {
    console.log('Feature clicked:', feature);
    // Could implement detailed feature analysis dialog
  };

  // Performance Metrics Cards
  const PerformanceCards = () => (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
      {performanceMetrics && [
        {
          title: 'API Response Time',
          value: `${performanceMetrics.api_response_time_ms}ms`,
          change: performanceMetrics.api_response_time_ms < 50 ? 'good' : 'warning',
          icon: <Clock className="h-4 w-4" />,
          target: '<50ms'
        },
        {
          title: 'Cache Hit Rate',
          value: `${Math.round(performanceMetrics.cache_hit_rate * 100)}%`,
          change: performanceMetrics.cache_hit_rate > 0.8 ? 'good' : 'warning',
          icon: <Zap className="h-4 w-4" />,
          target: '>80%'
        },
        {
          title: 'Accuracy Score',
          value: `${Math.round(performanceMetrics.accuracy_score * 100)}%`,
          change: performanceMetrics.accuracy_score > 0.9 ? 'good' : 'warning',
          icon: <Target className="h-4 w-4" />,
          target: '>90%'
        },
        {
          title: 'Total Analyses',
          value: performanceMetrics.total_analyses.toLocaleString(),
          change: 'neutral',
          icon: <BarChart3 className="h-4 w-4" />,
          target: 'Cumulative'
        },
        {
          title: 'Avg Processing Time',
          value: `${performanceMetrics.avg_processing_time_ms}ms`,
          change: performanceMetrics.avg_processing_time_ms < 30 ? 'good' : 'warning',
          icon: <Activity className="h-4 w-4" />,
          target: '<30ms'
        },
        {
          title: 'System Uptime',
          value: `${performanceMetrics.uptime_percentage.toFixed(2)}%`,
          change: performanceMetrics.uptime_percentage > 99 ? 'good' : 'warning',
          icon: <CheckCircle className="h-4 w-4" />,
          target: '>99%'
        }
      ].map((metric, index) => (
        <Card key={index} className="bg-slate-900/30 border-slate-800">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${
                  metric.change === 'good' ? 'bg-green-500/10 text-green-400' :
                  metric.change === 'warning' ? 'bg-yellow-500/10 text-yellow-400' :
                  'bg-blue-500/10 text-blue-400'
                }`}>
                  {metric.icon}
                </div>
                <div>
                  <div className="text-lg font-bold text-slate-100">{metric.value}</div>
                  <div className="text-xs text-slate-500">{metric.title}</div>
                  <div className="text-xs text-slate-600">Target: {metric.target}</div>
                </div>
              </div>
              {metric.change === 'good' && <ArrowUpRight className="h-4 w-4 text-green-400" />}
              {metric.change === 'warning' && <AlertTriangle className="h-4 w-4 text-yellow-400" />}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );

  // Connection Status Indicator
  const connectionHealth = getBIConnectionHealth();

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center p-8 ${className}`}>
        <div className="text-center">
          <BarChart3 className="h-8 w-8 text-blue-400 animate-pulse mx-auto mb-4" />
          <p className="text-slate-400">Loading advanced analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header Controls */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-100 mb-2">Advanced Analytics Intelligence</h2>
          <p className="text-slate-400 text-sm">
            SHAP explainability analysis and Austin market intelligence with real-time insights
          </p>
        </div>

        <div className="flex items-center gap-3">
          {lastUpdate && (
            <div className="text-xs text-slate-500">
              Last update: {new Date(lastUpdate).toLocaleTimeString()}
            </div>
          )}

          <Badge
            variant={connectionHealth.status === 'excellent' ? 'default' : 'destructive'}
            className={connectionHealth.status === 'excellent' ? 'bg-green-500/10 text-green-500' : 'bg-yellow-500/10 text-yellow-500'}
          >
            WebSocket {connectionHealth.connected}/{connectionHealth.total}
          </Badge>

          <Button
            size="sm"
            variant="outline"
            onClick={initializeAnalytics}
            disabled={isLoading}
            className="border-slate-600 text-slate-300"
          >
            <RefreshCw className={`h-3 w-3 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert className="bg-red-500/10 border-red-500/30 text-red-400">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Analytics Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Performance Overview */}
      <PerformanceCards />

      {/* Main Analytics Tabs */}
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as any)} className="space-y-4">
        <TabsList className="bg-slate-900 border-slate-800">
          <TabsTrigger value="shap" className="data-[state=active]:bg-slate-800">
            <Brain className="h-4 w-4 mr-2" />
            SHAP Analysis
          </TabsTrigger>
          <TabsTrigger value="market" className="data-[state=active]:bg-slate-800">
            <Map className="h-4 w-4 mr-2" />
            Market Intelligence
          </TabsTrigger>
          <TabsTrigger value="performance" className="data-[state=active]:bg-slate-800">
            <TrendingUp className="h-4 w-4 mr-2" />
            Performance
          </TabsTrigger>
        </TabsList>

        {/* SHAP Analysis Tab */}
        <TabsContent value="shap" className="space-y-4">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-slate-100 flex items-center gap-2">
                    <Brain className="h-5 w-5 text-blue-400" />
                    SHAP Explainability Analysis
                  </CardTitle>
                  <CardDescription className="text-slate-400">
                    Machine learning prediction explainability with feature contribution analysis
                  </CardDescription>
                </div>
                <div className="flex items-center gap-3">
                  <Select value={selectedLeadId} onValueChange={setSelectedLeadId}>
                    <SelectTrigger className="w-48 bg-slate-800 border-slate-700 text-slate-300">
                      <SelectValue placeholder="Select lead..." />
                    </SelectTrigger>
                    <SelectContent className="bg-slate-800 border-slate-700">
                      <SelectItem value="demo-lead-123">Demo Lead #123</SelectItem>
                      <SelectItem value="demo-lead-456">Demo Lead #456</SelectItem>
                      <SelectItem value="demo-lead-789">Demo Lead #789</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button
                    onClick={generateNewSHAPAnalysis}
                    disabled={isGenerating}
                    className="bg-blue-600 hover:bg-blue-500"
                  >
                    {isGenerating ? (
                      <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                    ) : (
                      <Zap className="h-3 w-3 mr-1" />
                    )}
                    Generate Analysis
                  </Button>
                </div>
              </div>
            </CardHeader>

            {shapAnalysis && (
              <CardContent>
                {/* SHAP Summary */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                  <div className="bg-slate-800/30 p-3 rounded-lg">
                    <div className="text-sm text-slate-400">Prediction Score</div>
                    <div className="text-xl font-bold text-slate-100">
                      {(shapAnalysis.prediction_score * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-slate-800/30 p-3 rounded-lg">
                    <div className="text-sm text-slate-400">Confidence</div>
                    <div className="text-xl font-bold text-slate-100">
                      {(shapAnalysis.confidence * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-slate-800/30 p-3 rounded-lg">
                    <div className="text-sm text-slate-400">Base Value</div>
                    <div className="text-xl font-bold text-slate-100">
                      {shapAnalysis.base_value.toFixed(3)}
                    </div>
                  </div>
                  <div className="bg-slate-800/30 p-3 rounded-lg">
                    <div className="text-sm text-slate-400">Processing Time</div>
                    <div className="text-xl font-bold text-slate-100">
                      {shapAnalysis.processing_time_ms}ms
                    </div>
                  </div>
                </div>

                {/* SHAP Waterfall Chart */}
                <div className="mb-6">
                  <SHAPWaterfallChart
                    data={shapAnalysis}
                    height={400}
                    showConfidenceIntervals={true}
                    onFeatureClick={handleFeatureClick}
                  />
                </div>

                {/* Export Actions */}
                <div className="flex items-center gap-3 pt-4 border-t border-slate-700">
                  <Button
                    variant="outline"
                    onClick={() => setExportDialog(true)}
                    className="border-slate-600 text-slate-300"
                  >
                    <Download className="h-3 w-3 mr-1" />
                    Export Analysis
                  </Button>
                  <Button
                    variant="outline"
                    className="border-slate-600 text-slate-300"
                  >
                    <Share2 className="h-3 w-3 mr-1" />
                    Share Report
                  </Button>
                  <Button
                    variant="outline"
                    className="border-slate-600 text-slate-300"
                  >
                    <Eye className="h-3 w-3 mr-1" />
                    View Details
                  </Button>
                </div>
              </CardContent>
            )}
          </Card>
        </TabsContent>

        {/* Market Intelligence Tab */}
        <TabsContent value="market" className="space-y-4">
          <MarketIntelligenceHeatmap
            selectedArea={selectedArea}
            onAreaSelect={setSelectedArea}
          />
        </TabsContent>

        {/* Performance Tab */}
        <TabsContent value="performance" className="space-y-4">
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader>
              <CardTitle className="text-slate-100 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-purple-400" />
                Analytics Performance Monitoring
              </CardTitle>
              <CardDescription className="text-slate-400">
                Real-time performance metrics and system health monitoring
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-slate-800/30 p-8 rounded-lg text-center">
                <TrendingUp className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400 mb-2">Performance Dashboard</p>
                <p className="text-slate-500 text-sm">
                  Detailed performance charts and monitoring will be displayed here
                </p>
                <div className="mt-4 text-sm text-slate-500">
                  • Real-time API response times<br/>
                  • ML model inference performance<br/>
                  • WebSocket connection health<br/>
                  • Cache efficiency metrics
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Export Dialog */}
      <Dialog open={exportDialog} onOpenChange={setExportDialog}>
        <DialogContent className="bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-slate-100">Export Analytics Report</DialogTitle>
            <DialogDescription className="text-slate-400">
              Generate a comprehensive analytics report for sharing or archival
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="text-sm text-slate-300">
              Report will include:
              <ul className="mt-2 space-y-1 text-slate-400">
                <li>• SHAP explainability analysis with visualizations</li>
                <li>• Performance metrics and benchmarks</li>
                <li>• Market intelligence insights (if available)</li>
                <li>• Executive summary and recommendations</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setExportDialog(false)}
              className="border-slate-600 text-slate-300"
            >
              Cancel
            </Button>
            <Button
              onClick={() => {
                // Implementation for actual export
                setExportDialog(false);
              }}
              className="bg-blue-600 hover:bg-blue-500"
            >
              <Download className="h-3 w-3 mr-1" />
              Export Report
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default AdvancedAnalyticsInterface;