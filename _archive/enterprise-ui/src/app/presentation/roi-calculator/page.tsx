// Jorge's ROI Calculator and Value Proposition Interface
// Professional client presentation system for justifying 6% premium commission

'use client';

import { useState } from 'react';
import {
  Calculator,
  TrendingUp,
  Users,
  Target,
  Zap,
  FileText,
  Download,
  BarChart3,
  Presentation,
  Lightbulb,
  ArrowRight
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useROICalculator, useROIPresets, useMarketInsights } from '@/hooks/useROICalculator';
import { ClientProfileBuilder } from '@/components/presentation/ClientProfileBuilder';
import { ROICalculator } from '@/components/presentation/ROICalculator';
import { ValuePropositionEngine } from '@/components/presentation/ValuePropositionEngine';
import { ROIVisualizations } from '@/components/presentation/ROIVisualizations';
import { CompetitorComparison } from '@/components/presentation/CompetitorComparison';

export default function ROICalculatorPage() {
  const [activeTab, setActiveTab] = useState('profile');
  const roiCalculator = useROICalculator();
  const presets = useROIPresets();
  const marketInsights = useMarketInsights();

  const handlePresetSelection = (preset: any) => {
    roiCalculator.setClientProfile(preset);
    setActiveTab('calculator');
  };

  const handleCalculationComplete = () => {
    roiCalculator.generatePresentation();
    setActiveTab('results');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-2">
                Jorge's ROI Calculator
              </h1>
              <p className="text-lg text-gray-600">
                Professional value proposition engine that justifies 6% premium commission through AI advantages
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                <Zap className="w-4 h-4 mr-1" />
                AI-Powered
              </Badge>
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                <TrendingUp className="w-4 h-4 mr-1" />
                Client-Ready
              </Badge>
              <Badge variant="outline" className="bg-purple-50 text-purple-700 border-purple-200">
                <Presentation className="w-4 h-4 mr-1" />
                Professional
              </Badge>
            </div>
          </div>

          {/* Progress Indicator */}
          <div className="mt-6 bg-white rounded-lg border p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-gray-700">Presentation Progress</span>
              <span className="text-sm text-gray-500">
                {Math.round(roiCalculator.completionPercentage)}% Complete
              </span>
            </div>

            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${roiCalculator.completionPercentage}%` }}
              />
            </div>

            <div className="flex items-center justify-between mt-3 text-xs">
              <div className={`flex items-center gap-1 ${roiCalculator.hasProfile ? 'text-blue-600' : 'text-gray-400'}`}>
                <Users className="w-3 h-3" />
                Profile
              </div>
              <div className={`flex items-center gap-1 ${roiCalculator.hasCalculation ? 'text-blue-600' : 'text-gray-400'}`}>
                <Calculator className="w-3 h-3" />
                ROI
              </div>
              <div className={`flex items-center gap-1 ${roiCalculator.hasPresentation ? 'text-blue-600' : 'text-gray-400'}`}>
                <Presentation className="w-3 h-3" />
                Presentation
              </div>
            </div>
          </div>
        </div>

        {/* Quick Start Presets */}
        {!roiCalculator.clientProfile && (
          <Card className="mb-6 border-2 border-dashed border-blue-200 bg-blue-50/30">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-blue-600" />
                Quick Start with Client Presets
              </CardTitle>
              <p className="text-gray-600">Choose a client profile to see Jorge's value proposition in action</p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Button
                  variant="outline"
                  className="h-auto p-4 text-left"
                  onClick={() => handlePresetSelection(presets.luxuryClient)}
                >
                  <div>
                    <div className="font-semibold text-purple-700">Luxury Market</div>
                    <div className="text-sm text-gray-600">$2.5M+ Properties</div>
                    <div className="text-xs text-gray-500 mt-1">Privacy & Premium Results</div>
                  </div>
                </Button>

                <Button
                  variant="outline"
                  className="h-auto p-4 text-left"
                  onClick={() => handlePresetSelection(presets.midMarketClient)}
                >
                  <div>
                    <div className="font-semibold text-blue-700">Mid-Market</div>
                    <div className="text-sm text-gray-600">$300K-$800K</div>
                    <div className="text-xs text-gray-500 mt-1">Value & Reliability</div>
                  </div>
                </Button>

                <Button
                  variant="outline"
                  className="h-auto p-4 text-left"
                  onClick={() => handlePresetSelection(presets.firstTimeClient)}
                >
                  <div>
                    <div className="font-semibold text-green-700">First-Time</div>
                    <div className="text-sm text-gray-600">$200K-$400K</div>
                    <div className="text-xs text-gray-500 mt-1">Education & Guidance</div>
                  </div>
                </Button>

                <Button
                  variant="outline"
                  className="h-auto p-4 text-left"
                  onClick={() => handlePresetSelection(presets.investorClient)}
                >
                  <div>
                    <div className="font-semibold text-orange-700">Investor</div>
                    <div className="text-sm text-gray-600">$500K+ Portfolio</div>
                    <div className="text-xs text-gray-500 mt-1">ROI & Speed</div>
                  </div>
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Main Interface */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="profile" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Client Profile
            </TabsTrigger>
            <TabsTrigger
              value="calculator"
              disabled={!roiCalculator.hasProfile}
              className="flex items-center gap-2"
            >
              <Calculator className="w-4 h-4" />
              ROI Calculator
            </TabsTrigger>
            <TabsTrigger
              value="results"
              disabled={!roiCalculator.hasCalculation}
              className="flex items-center gap-2"
            >
              <BarChart3 className="w-4 h-4" />
              Results
            </TabsTrigger>
            <TabsTrigger
              value="presentation"
              disabled={!roiCalculator.hasPresentation}
              className="flex items-center gap-2"
            >
              <Presentation className="w-4 h-4" />
              Presentation
            </TabsTrigger>
            <TabsTrigger
              value="comparison"
              className="flex items-center gap-2"
            >
              <Target className="w-4 h-4" />
              Competition
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile" className="space-y-6">
            <ClientProfileBuilder
              profile={roiCalculator.clientProfile}
              onProfileChange={roiCalculator.setClientProfile}
              onPropertyUpdate={roiCalculator.updateProperty}
              marketInsights={marketInsights}
            />

            {roiCalculator.clientProfile && (
              <div className="flex justify-end">
                <Button
                  onClick={() => setActiveTab('calculator')}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Continue to ROI Calculator
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            )}
          </TabsContent>

          <TabsContent value="calculator" className="space-y-6">
            <ROICalculator
              clientProfile={roiCalculator.clientProfile}
              roiCalculation={roiCalculator.roiCalculation}
              isCalculating={roiCalculator.isCalculating}
              onCalculate={roiCalculator.calculateROI}
              onComplete={handleCalculationComplete}
            />
          </TabsContent>

          <TabsContent value="results" className="space-y-6">
            {roiCalculator.roiCalculation && (
              <>
                <ROIVisualizations
                  roiCalculation={roiCalculator.roiCalculation}
                  clientProfile={roiCalculator.clientProfile!}
                />

                <div className="flex justify-between">
                  <Button
                    variant="outline"
                    onClick={() => roiCalculator.exportToJSON()}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Export Data
                  </Button>

                  <Button
                    onClick={() => setActiveTab('presentation')}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    Generate Presentation
                    <Presentation className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </>
            )}
          </TabsContent>

          <TabsContent value="presentation" className="space-y-6">
            {roiCalculator.valuePresentation && (
              <ValuePropositionEngine
                presentation={roiCalculator.valuePresentation}
                narrative={roiCalculator.valueNarrative!}
                roiCalculation={roiCalculator.roiCalculation!}
                onExportPDF={roiCalculator.exportToPDF}
              />
            )}
          </TabsContent>

          <TabsContent value="comparison" className="space-y-6">
            <CompetitorComparison
              marketSegment={roiCalculator.clientProfile?.marketSegment}
              propertyValue={roiCalculator.clientProfile?.propertyBudget}
            />
          </TabsContent>
        </Tabs>

        {/* Error Display */}
        {roiCalculator.error && (
          <Card className="mt-6 border-red-200 bg-red-50">
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-red-700">
                <Target className="w-5 h-5" />
                <span className="font-semibold">Error:</span>
                <span>{roiCalculator.error}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <div className="mt-12 text-center text-gray-500 border-t pt-6">
          <p>Jorge's AI Real Estate Platform - ROI Calculator v1.0</p>
          <p className="text-sm">Professional value proposition engine for 6% premium commission justification</p>
        </div>
      </div>
    </div>
  );
}