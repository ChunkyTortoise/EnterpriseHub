// Interactive ROI Calculator Component
// Real-time ROI calculations with scenario modeling

'use client';

import { useState, useEffect } from 'react';
import {
  Calculator,
  TrendingUp,
  Clock,
  DollarSign,
  Target,
  Zap,
  BarChart3,
  Lightbulb,
  AlertCircle,
  CheckCircle,
  ArrowUp,
  ArrowDown,
  Loader2
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { type ClientProfile, type ROICalculation, ROIEngine } from '@/lib/presentation/ROIEngine';

interface ROICalculatorProps {
  clientProfile: ClientProfile | null;
  roiCalculation: ROICalculation | null;
  isCalculating: boolean;
  onCalculate: (timeHorizonMonths?: number) => void;
  onComplete: () => void;
}

export function ROICalculator({
  clientProfile,
  roiCalculation,
  isCalculating,
  onCalculate,
  onComplete
}: ROICalculatorProps) {
  const [timeHorizon, setTimeHorizon] = useState(12);
  const [selectedScenario, setSelectedScenario] = useState(1); // 0=conservative, 1=expected, 2=optimistic

  useEffect(() => {
    if (clientProfile && !roiCalculation && !isCalculating) {
      onCalculate(timeHorizon);
    }
  }, [clientProfile, roiCalculation, isCalculating, onCalculate, timeHorizon]);

  if (!clientProfile) {
    return (
      <Card className="p-8 text-center">
        <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">Client Profile Required</h3>
        <p className="text-gray-600">Please create a client profile before calculating ROI.</p>
      </Card>
    );
  }

  const handleCalculate = () => {
    onCalculate(timeHorizon);
  };

  const handleComplete = () => {
    onComplete();
  };

  const getROIColor = (value: number) => {
    if (value >= 300000) return 'text-green-600';
    if (value >= 150000) return 'text-blue-600';
    if (value >= 50000) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScenarioIcon = (index: number) => {
    if (index === 0) return <ArrowDown className="w-4 h-4" />;
    if (index === 1) return <Target className="w-4 h-4" />;
    return <ArrowUp className="w-4 h-4" />;
  };

  const getScenarioColor = (index: number) => {
    if (index === 0) return 'border-orange-200 bg-orange-50 text-orange-700';
    if (index === 1) return 'border-blue-200 bg-blue-50 text-blue-700';
    return 'border-green-200 bg-green-50 text-green-700';
  };

  return (
    <div className="space-y-6">
      {/* Client Context */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calculator className="w-5 h-5 text-blue-600" />
            ROI Calculation for {clientProfile.name}
          </CardTitle>
          <div className="flex items-center gap-4 text-sm text-gray-600">
            <span>Property Budget: {ROIEngine.formatCurrency(clientProfile.propertyBudget)}</span>
            <Badge variant="outline">{clientProfile.marketSegment}</Badge>
            <Badge
              variant="outline"
              className={
                clientProfile.urgency === 'high'
                  ? 'border-red-200 text-red-700'
                  : clientProfile.urgency === 'medium'
                  ? 'border-yellow-200 text-yellow-700'
                  : 'border-green-200 text-green-700'
              }
            >
              {clientProfile.urgency} urgency
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Time Horizon Control */}
            <div>
              <Label>Time Horizon: {timeHorizon} months</Label>
              <div className="mt-3">
                <Slider
                  value={[timeHorizon]}
                  onValueChange={(value) => setTimeHorizon(value[0])}
                  max={24}
                  min={6}
                  step={3}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>6 months</span>
                  <span>12 months</span>
                  <span>24 months</span>
                </div>
              </div>
            </div>

            {/* Calculate Button */}
            <div className="flex items-end">
              <Button
                onClick={handleCalculate}
                disabled={isCalculating}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                {isCalculating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Calculating ROI...
                  </>
                ) : (
                  <>
                    <Calculator className="w-4 h-4 mr-2" />
                    Calculate ROI
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ROI Results */}
      {roiCalculation && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="border-l-4 border-l-green-500">
              <CardContent className="p-4 text-center">
                <DollarSign className="w-8 h-8 text-green-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-green-600">
                  {ROIEngine.formatCurrency(roiCalculation.netROI)}
                </div>
                <div className="text-sm text-gray-600">Net ROI</div>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-blue-500">
              <CardContent className="p-4 text-center">
                <TrendingUp className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-blue-600">
                  {(roiCalculation.jorgeAIBenefits.total / Math.abs(roiCalculation.jorgeAICosts.total - roiCalculation.traditionalCosts.total)).toFixed(1)}x
                </div>
                <div className="text-sm text-gray-600">ROI Multiple</div>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-purple-500">
              <CardContent className="p-4 text-center">
                <Clock className="w-8 h-8 text-purple-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-purple-600">
                  {roiCalculation.breakEvenMonths}
                </div>
                <div className="text-sm text-gray-600">Break-Even Months</div>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-orange-500">
              <CardContent className="p-4 text-center">
                <Target className="w-8 h-8 text-orange-600 mx-auto mb-2" />
                <div className="text-2xl font-bold text-orange-600">
                  {ROIEngine.formatPercentage(roiCalculation.estimatedRevenueLift)}
                </div>
                <div className="text-sm text-gray-600">Price Optimization</div>
              </CardContent>
            </Card>
          </div>

          {/* Cost-Benefit Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Traditional Costs */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Traditional Agent Costs</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Commission (3%):</span>
                  <span>{ROIEngine.formatCurrency(roiCalculation.traditionalCosts.commission)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Carrying Costs:</span>
                  <span>{ROIEngine.formatCurrency(roiCalculation.traditionalCosts.carryingCosts)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Marketing:</span>
                  <span>{ROIEngine.formatCurrency(roiCalculation.traditionalCosts.marketingCosts)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Opportunity Cost:</span>
                  <span>{ROIEngine.formatCurrency(roiCalculation.traditionalCosts.opportunityCost)}</span>
                </div>
                <hr />
                <div className="flex justify-between font-bold">
                  <span>Total:</span>
                  <span className="text-red-600">
                    {ROIEngine.formatCurrency(roiCalculation.traditionalCosts.total)}
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Jorge AI Costs */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Jorge AI Costs</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Commission (6%):</span>
                  <span>{ROIEngine.formatCurrency(roiCalculation.jorgeAICosts.commission)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Platform Fees:</span>
                  <span>{ROIEngine.formatCurrency(roiCalculation.jorgeAICosts.platformFees)}</span>
                </div>
                <div className="flex justify-between text-gray-400">
                  <span>Hidden Costs:</span>
                  <span>$0</span>
                </div>
                <div className="flex justify-between text-gray-400">
                  <span>Delays:</span>
                  <span>$0</span>
                </div>
                <hr />
                <div className="flex justify-between font-bold">
                  <span>Total:</span>
                  <span className="text-blue-600">
                    {ROIEngine.formatCurrency(roiCalculation.jorgeAICosts.total)}
                  </span>
                </div>
              </CardContent>
            </Card>

            {/* Jorge AI Benefits */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Jorge AI Benefits</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600">Faster Sale:</span>
                  <span>{ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.fasterSale)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Higher Price:</span>
                  <span>{ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.higherPrice)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Market Intel:</span>
                  <span>{ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.marketIntelligence)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Client Experience:</span>
                  <span>{ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.clientExperience)}</span>
                </div>
                <hr />
                <div className="flex justify-between font-bold">
                  <span>Total Value:</span>
                  <span className="text-green-600">
                    {ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.total)}
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Scenario Analysis */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-purple-600" />
                Scenario Analysis
              </CardTitle>
              <p className="text-gray-600">
                Compare conservative, expected, and optimistic outcomes
              </p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {roiCalculation.scenarios.map((scenario, index) => (
                  <Card
                    key={scenario.name}
                    className={`cursor-pointer transition-all ${
                      selectedScenario === index
                        ? 'ring-2 ring-blue-500 shadow-md'
                        : 'hover:shadow-sm'
                    } ${getScenarioColor(index)}`}
                    onClick={() => setSelectedScenario(index)}
                  >
                    <CardHeader className="pb-3">
                      <CardTitle className="text-sm flex items-center gap-2">
                        {getScenarioIcon(index)}
                        {scenario.name}
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <p className="text-xs mb-3">{scenario.description}</p>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span>Net ROI:</span>
                          <span className={`font-semibold ${getROIColor(scenario.results.netROI)}`}>
                            {ROIEngine.formatCurrency(scenario.results.netROI)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Price Boost:</span>
                          <span>{ROIEngine.formatPercentage(scenario.results.estimatedRevenueLift)}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Selected Scenario Details */}
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-semibold mb-2">
                  {roiCalculation.scenarios[selectedScenario].name} - Assumptions
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  {Object.entries(roiCalculation.scenarios[selectedScenario].assumptions).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-gray-600 capitalize">{key.replace(/([A-Z])/g, ' $1')}:</span>
                      <span className="font-medium">
                        {typeof value === 'number' && value < 1
                          ? ROIEngine.formatPercentage(value)
                          : value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Market Comparisons */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-yellow-600" />
                Jorge vs Traditional Agents
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                {roiCalculation.marketComparisons.map((comparison, index) => (
                  <div key={index} className="text-center">
                    <div className="text-lg font-bold text-green-600 mb-1">
                      +{comparison.improvement.toFixed(1)}%
                    </div>
                    <div className="text-sm font-semibold mb-1">
                      {comparison.category}
                    </div>
                    <div className="text-xs text-gray-600 space-y-1">
                      <div>Traditional: {comparison.traditional} {comparison.unit}</div>
                      <div>Jorge AI: {comparison.jorgeAI} {comparison.unit}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Value Propositions Preview */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-amber-600" />
                Key Value Propositions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {roiCalculation.jorgeAdvantages.slice(0, 4).map((advantage, index) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <h4 className="font-semibold text-sm mb-2">{advantage.title}</h4>
                    <p className="text-xs text-gray-600 mb-2">{advantage.description}</p>
                    <div className="text-sm font-bold text-blue-600">
                      Value: {ROIEngine.formatCurrency(advantage.quantifiedBenefit)}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Action Button */}
          <div className="flex justify-center">
            <Button
              onClick={handleComplete}
              size="lg"
              className="bg-green-600 hover:bg-green-700 px-8"
            >
              <CheckCircle className="w-5 h-5 mr-2" />
              Generate Professional Presentation
            </Button>
          </div>
        </>
      )}
    </div>
  );
}