// ROI Visualizations Component
// Professional charts and graphs for client presentations

'use client';

import { useState } from 'react';
import {
  BarChart3,
  PieChart,
  TrendingUp,
  Clock,
  Target,
  Zap,
  DollarSign,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  CheckCircle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { type ClientProfile, type ROICalculation, ROIEngine } from '@/lib/presentation/ROIEngine';

interface ROIVisualizationsProps {
  roiCalculation: ROICalculation;
  clientProfile: ClientProfile;
}

export function ROIVisualizations({ roiCalculation, clientProfile }: ROIVisualizationsProps) {
  const [selectedChart, setSelectedChart] = useState('overview');

  const roiMultiple = roiCalculation.jorgeAIBenefits.total / Math.abs(roiCalculation.jorgeAICosts.total - roiCalculation.traditionalCosts.total);
  const additionalInvestment = roiCalculation.jorgeAICosts.total - roiCalculation.traditionalCosts.total;

  // Calculate percentages for visualization
  const benefitPercentages = {
    fasterSale: (roiCalculation.jorgeAIBenefits.fasterSale / roiCalculation.jorgeAIBenefits.total) * 100,
    higherPrice: (roiCalculation.jorgeAIBenefits.higherPrice / roiCalculation.jorgeAIBenefits.total) * 100,
    marketIntel: (roiCalculation.jorgeAIBenefits.marketIntelligence / roiCalculation.jorgeAIBenefits.total) * 100,
    clientExp: (roiCalculation.jorgeAIBenefits.clientExperience / roiCalculation.jorgeAIBenefits.total) * 100,
  };

  const getColorByCategory = (category: string) => {
    const colors = {
      fasterSale: 'bg-blue-500',
      higherPrice: 'bg-green-500',
      marketIntel: 'bg-purple-500',
      clientExp: 'bg-orange-500',
    };
    return colors[category as keyof typeof colors] || 'bg-gray-500';
  };

  return (
    <div className="space-y-6">
      {/* Executive Summary */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-2xl">
            <TrendingUp className="w-6 h-6 text-blue-600" />
            ROI Analysis Summary for {clientProfile.name}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-4xl font-bold text-green-600 mb-2">
                {roiMultiple.toFixed(1)}x
              </div>
              <div className="text-lg text-gray-700">Return Multiple</div>
              <div className="text-sm text-gray-600">
                {ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.total)} value delivered
              </div>
            </div>

            <div className="text-center">
              <div className="text-4xl font-bold text-blue-600 mb-2">
                {ROIEngine.formatCurrency(roiCalculation.netROI)}
              </div>
              <div className="text-lg text-gray-700">Net ROI</div>
              <div className="text-sm text-gray-600">
                vs {ROIEngine.formatCurrency(additionalInvestment)} additional investment
              </div>
            </div>

            <div className="text-center">
              <div className="text-4xl font-bold text-purple-600 mb-2">
                {roiCalculation.breakEvenMonths}
              </div>
              <div className="text-lg text-gray-700">Months to Break-Even</div>
              <div className="text-sm text-gray-600">
                {ROIEngine.formatPercentage(roiCalculation.estimatedRevenueLift)} price optimization
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Chart Selector */}
      <Tabs value={selectedChart} onValueChange={setSelectedChart} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="benefits" className="flex items-center gap-2">
            <PieChart className="w-4 h-4" />
            Benefits
          </TabsTrigger>
          <TabsTrigger value="scenarios" className="flex items-center gap-2">
            <Target className="w-4 h-4" />
            Scenarios
          </TabsTrigger>
          <TabsTrigger value="timeline" className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            Timeline
          </TabsTrigger>
        </TabsList>

        {/* Overview Chart */}
        <TabsContent value="overview">
          <Card>
            <CardHeader>
              <CardTitle>Investment vs Value Comparison</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Traditional Agent Bar */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">Traditional Agent (3%)</span>
                    <span className="text-lg font-bold text-red-600">
                      {ROIEngine.formatCurrency(roiCalculation.traditionalCosts.total)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-8">
                    <div
                      className="bg-red-500 h-8 rounded-full flex items-center justify-end pr-3"
                      style={{ width: '60%' }}
                    >
                      <span className="text-white text-sm font-bold">Total Cost</span>
                    </div>
                  </div>
                </div>

                {/* Jorge AI Investment Bar */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">Jorge AI Investment (6%)</span>
                    <span className="text-lg font-bold text-blue-600">
                      {ROIEngine.formatCurrency(roiCalculation.jorgeAICosts.total)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-8">
                    <div
                      className="bg-blue-500 h-8 rounded-full flex items-center justify-end pr-3"
                      style={{ width: '80%' }}
                    >
                      <span className="text-white text-sm font-bold">Investment</span>
                    </div>
                  </div>
                </div>

                {/* Jorge AI Value Bar */}
                <div>
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">Jorge AI Value Delivered</span>
                    <span className="text-lg font-bold text-green-600">
                      {ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.total)}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-8">
                    <div
                      className="bg-green-500 h-8 rounded-full flex items-center justify-end pr-3"
                      style={{ width: '100%' }}
                    >
                      <span className="text-white text-sm font-bold">Total Value</span>
                    </div>
                  </div>
                </div>

                {/* Net Benefit */}
                <div className="p-4 bg-green-50 rounded-lg border-2 border-green-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <ArrowUp className="w-6 h-6 text-green-600" />
                      <span className="text-lg font-bold text-green-800">Net Benefit</span>
                    </div>
                    <span className="text-2xl font-bold text-green-600">
                      {ROIEngine.formatCurrency(roiCalculation.netROI)}
                    </span>
                  </div>
                  <div className="text-sm text-green-700 mt-2">
                    Jorge's 6% commission delivers {roiMultiple.toFixed(1)}x value through AI optimization
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Benefits Breakdown */}
        <TabsContent value="benefits">
          <Card>
            <CardHeader>
              <CardTitle>Value Delivery Breakdown</CardTitle>
              <p className="text-gray-600">
                How Jorge's AI platform creates {ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.total)} in value
              </p>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Faster Sale */}
                <div className="flex items-center gap-4">
                  <div className="w-16 text-right">
                    <span className="text-2xl font-bold text-blue-600">
                      {benefitPercentages.fasterSale.toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-medium">Faster Sale Completion</span>
                      <span className="font-bold text-blue-600">
                        {ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.fasterSale)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-6">
                      <div
                        className="bg-blue-500 h-6 rounded-full flex items-center px-2"
                        style={{ width: `${benefitPercentages.fasterSale}%` }}
                      >
                        <Clock className="w-4 h-4 text-white mr-2" />
                        <span className="text-white text-xs font-bold">18 vs 35 days</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Higher Price */}
                <div className="flex items-center gap-4">
                  <div className="w-16 text-right">
                    <span className="text-2xl font-bold text-green-600">
                      {benefitPercentages.higherPrice.toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-medium">AI Price Optimization</span>
                      <span className="font-bold text-green-600">
                        {ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.higherPrice)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-6">
                      <div
                        className="bg-green-500 h-6 rounded-full flex items-center px-2"
                        style={{ width: `${benefitPercentages.higherPrice}%` }}
                      >
                        <TrendingUp className="w-4 h-4 text-white mr-2" />
                        <span className="text-white text-xs font-bold">5% above market</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Market Intelligence */}
                <div className="flex items-center gap-4">
                  <div className="w-16 text-right">
                    <span className="text-2xl font-bold text-purple-600">
                      {benefitPercentages.marketIntel.toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-medium">Market Intelligence Value</span>
                      <span className="font-bold text-purple-600">
                        {ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.marketIntelligence)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-6">
                      <div
                        className="bg-purple-500 h-6 rounded-full flex items-center px-2"
                        style={{ width: `${benefitPercentages.marketIntel}%` }}
                      >
                        <Target className="w-4 h-4 text-white mr-2" />
                        <span className="text-white text-xs font-bold">AI insights</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Client Experience */}
                <div className="flex items-center gap-4">
                  <div className="w-16 text-right">
                    <span className="text-2xl font-bold text-orange-600">
                      {benefitPercentages.clientExp.toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-medium">Superior Client Experience</span>
                      <span className="font-bold text-orange-600">
                        {ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.clientExperience)}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-6">
                      <div
                        className="bg-orange-500 h-6 rounded-full flex items-center px-2"
                        style={{ width: `${benefitPercentages.clientExp}%` }}
                      >
                        <Zap className="w-4 h-4 text-white mr-2" />
                        <span className="text-white text-xs font-bold">Referral value</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <div className="text-center">
                  <div className="text-3xl font-bold text-gray-800 mb-2">
                    {ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.total)}
                  </div>
                  <div className="text-lg text-gray-600">Total Value Delivered</div>
                  <div className="text-sm text-gray-500 mt-1">
                    vs {ROIEngine.formatCurrency(additionalInvestment)} additional investment
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Scenario Analysis */}
        <TabsContent value="scenarios">
          <Card>
            <CardHeader>
              <CardTitle>Scenario Analysis</CardTitle>
              <p className="text-gray-600">ROI outcomes under different market conditions</p>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {roiCalculation.scenarios.map((scenario, index) => (
                  <Card key={scenario.name} className={
                    index === 0 ? 'border-orange-200 bg-orange-50' :
                    index === 1 ? 'border-blue-200 bg-blue-50' :
                    'border-green-200 bg-green-50'
                  }>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg flex items-center gap-2">
                        {index === 0 && <ArrowDown className="w-5 h-5 text-orange-600" />}
                        {index === 1 && <Target className="w-5 h-5 text-blue-600" />}
                        {index === 2 && <ArrowUp className="w-5 h-5 text-green-600" />}
                        {scenario.name}
                      </CardTitle>
                      <p className="text-sm text-gray-600">{scenario.description}</p>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="text-center">
                          <div className={`text-2xl font-bold ${
                            index === 0 ? 'text-orange-600' :
                            index === 1 ? 'text-blue-600' :
                            'text-green-600'
                          }`}>
                            {ROIEngine.formatCurrency(scenario.results.netROI)}
                          </div>
                          <div className="text-sm text-gray-600">Net ROI</div>
                        </div>

                        <div className="space-y-2 text-sm">
                          {Object.entries(scenario.assumptions).map(([key, value]) => (
                            <div key={key} className="flex justify-between">
                              <span className="text-gray-600 capitalize">
                                {key.replace(/([A-Z])/g, ' $1')}:
                              </span>
                              <span className="font-medium">
                                {typeof value === 'number' && value < 1
                                  ? ROIEngine.formatPercentage(value)
                                  : value}
                              </span>
                            </div>
                          ))}
                        </div>

                        <div className="pt-2 border-t">
                          <div className="flex justify-between text-xs">
                            <span>ROI Multiple:</span>
                            <span className="font-bold">
                              {(scenario.results.netROI / Math.abs(additionalInvestment)).toFixed(1)}x
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Timeline View */}
        <TabsContent value="timeline">
          <Card>
            <CardHeader>
              <CardTitle>Value Realization Timeline</CardTitle>
              <p className="text-gray-600">When benefits are realized during the transaction</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Timeline Steps */}
                <div className="relative">
                  <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-gray-300"></div>

                  {/* Immediate Benefits */}
                  <div className="flex items-start gap-4 pb-6">
                    <div className="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                      <Zap className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-bold text-lg">Immediate (Day 1)</h3>
                      <p className="text-gray-600 mb-2">AI qualification begins instantly</p>
                      <div className="text-sm space-y-1">
                        <div>• 24/7 lead qualification active</div>
                        <div>• Real-time market analysis</div>
                        <div>• Professional bot ecosystem deployed</div>
                      </div>
                    </div>
                  </div>

                  {/* Week 1 Benefits */}
                  <div className="flex items-start gap-4 pb-6">
                    <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
                      <Clock className="w-6 h-6 text-green-600" />
                    </div>
                    <div>
                      <h3 className="font-bold text-lg">Week 1-2</h3>
                      <p className="text-gray-600 mb-2">Process optimization delivers results</p>
                      <div className="text-sm space-y-1">
                        <div>• Qualified leads identified</div>
                        <div>• Market positioning optimized</div>
                        <div>• Automation sequences launched</div>
                      </div>
                      <Badge variant="outline" className="mt-2">
                        ~{ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.marketIntelligence / 4)} value
                      </Badge>
                    </div>
                  </div>

                  {/* Month 1 Benefits */}
                  <div className="flex items-start gap-4 pb-6">
                    <div className="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center">
                      <TrendingUp className="w-6 h-6 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="font-bold text-lg">Month 1</h3>
                      <p className="text-gray-600 mb-2">Transaction completion and price optimization</p>
                      <div className="text-sm space-y-1">
                        <div>• Property sold (18 vs 35 days average)</div>
                        <div>• Price optimization realized</div>
                        <div>• Carrying cost savings captured</div>
                      </div>
                      <Badge variant="outline" className="mt-2">
                        ~{ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.fasterSale + roiCalculation.jorgeAIBenefits.higherPrice)} value
                      </Badge>
                    </div>
                  </div>

                  {/* Ongoing Benefits */}
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center">
                      <ArrowRight className="w-6 h-6 text-orange-600" />
                    </div>
                    <div>
                      <h3 className="font-bold text-lg">Ongoing</h3>
                      <p className="text-gray-600 mb-2">Long-term relationship value</p>
                      <div className="text-sm space-y-1">
                        <div>• Client satisfaction and referrals</div>
                        <div>• Repeat business opportunities</div>
                        <div>• Network effect benefits</div>
                      </div>
                      <Badge variant="outline" className="mt-2">
                        {ROIEngine.formatCurrency(roiCalculation.jorgeAIBenefits.clientExperience)} lifetime value
                      </Badge>
                    </div>
                  </div>
                </div>

                {/* Break-even highlight */}
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="font-bold text-green-800">Break-Even: Month {roiCalculation.breakEvenMonths}</span>
                  </div>
                  <p className="text-green-700 text-sm">
                    The additional 3% commission investment is recovered through AI value delivery,
                    with {ROIEngine.formatCurrency(roiCalculation.netROI)} in net benefit continuing beyond break-even.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}