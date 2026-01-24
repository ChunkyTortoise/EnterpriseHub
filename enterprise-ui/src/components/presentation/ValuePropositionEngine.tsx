// Value Proposition Engine Component
// Professional presentation system for client value demonstrations

'use client';

import { useState } from 'react';
import {
  Presentation,
  FileText,
  Download,
  Share,
  Play,
  Pause,
  SkipForward,
  SkipBack,
  Maximize2,
  Eye,
  Star,
  TrendingUp,
  Target,
  Zap,
  Users,
  ArrowRight,
  CheckCircle,
  Building
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { type ValuePresentation, type ValueNarrative } from '@/lib/presentation/ValueEngine';
import { type ROICalculation, ROIEngine } from '@/lib/presentation/ROIEngine';

interface ValuePropositionEngineProps {
  presentation: ValuePresentation;
  narrative: ValueNarrative;
  roiCalculation: ROICalculation;
  onExportPDF: () => Promise<void>;
}

export function ValuePropositionEngine({
  presentation,
  narrative,
  roiCalculation,
  onExportPDF
}: ValuePropositionEngineProps) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);

  const nextSlide = () => {
    if (currentSlide < presentation.slides.length - 1) {
      setCurrentSlide(currentSlide + 1);
    }
  };

  const prevSlide = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1);
    }
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const roiMultiple = roiCalculation.jorgeAIBenefits.total / Math.abs(roiCalculation.jorgeAICosts.total - roiCalculation.traditionalCosts.total);

  if (isFullscreen) {
    return (
      <div className="fixed inset-0 bg-black z-50 flex flex-col">
        {/* Fullscreen Header */}
        <div className="bg-gray-900 text-white p-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-lg font-bold">{presentation.title}</span>
            <Badge variant="outline" className="border-white text-white">
              Slide {currentSlide + 1} of {presentation.slides.length}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={prevSlide}
              disabled={currentSlide === 0}
              className="text-white hover:bg-gray-800"
            >
              <SkipBack className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={nextSlide}
              disabled={currentSlide === presentation.slides.length - 1}
              className="text-white hover:bg-gray-800"
            >
              <SkipForward className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleFullscreen}
              className="text-white hover:bg-gray-800"
            >
              Exit Fullscreen
            </Button>
          </div>
        </div>

        {/* Fullscreen Slide */}
        <div className="flex-1 bg-white p-12 overflow-auto">
          <div className="max-w-4xl mx-auto h-full flex flex-col">
            <div className="text-center mb-8">
              <h1 className="text-6xl font-bold text-gray-900 mb-4">
                {presentation.slides[currentSlide].title}
              </h1>
              {presentation.slides[currentSlide].subtitle && (
                <p className="text-2xl text-gray-600">
                  {presentation.slides[currentSlide].subtitle}
                </p>
              )}
            </div>

            <div className="flex-1 flex items-center justify-center">
              <div className="text-xl leading-relaxed text-gray-800 max-w-3xl text-center">
                {presentation.slides[currentSlide].content.split('\n').map((line, index) => (
                  <p key={index} className="mb-4">
                    {line}
                  </p>
                ))}
              </div>
            </div>

            {/* Slide-specific visualizations */}
            {presentation.slides[currentSlide].data && (
              <div className="mt-8">
                {presentation.slides[currentSlide].visualType === 'stats' && (
                  <div className="grid grid-cols-3 gap-6 text-center">
                    <div>
                      <div className="text-4xl font-bold text-green-600 mb-2">
                        {roiMultiple.toFixed(1)}x
                      </div>
                      <div className="text-lg text-gray-600">ROI Multiple</div>
                    </div>
                    <div>
                      <div className="text-4xl font-bold text-blue-600 mb-2">
                        {ROIEngine.formatCurrency(roiCalculation.netROI)}
                      </div>
                      <div className="text-lg text-gray-600">Net Benefit</div>
                    </div>
                    <div>
                      <div className="text-4xl font-bold text-purple-600 mb-2">
                        {roiCalculation.breakEvenMonths}mo
                      </div>
                      <div className="text-lg text-gray-600">Break-Even</div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Presentation Header */}
      <Card className="bg-gradient-to-r from-purple-50 to-blue-50 border-2">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-2xl">
                <Presentation className="w-6 h-6 text-purple-600" />
                Professional Value Presentation
              </CardTitle>
              <p className="text-gray-600 mt-2">{presentation.title}</p>
              <div className="flex items-center gap-4 mt-3">
                <Badge variant="outline">
                  <Users className="w-3 h-3 mr-1" />
                  {presentation.audience}
                </Badge>
                <Badge variant="outline">
                  <Clock className="w-3 h-3 mr-1" />
                  {presentation.duration}
                </Badge>
                <Badge variant="outline">
                  <FileText className="w-3 h-3 mr-1" />
                  {presentation.slides.length} slides
                </Badge>
              </div>
            </div>

            <div className="flex flex-col items-end gap-2">
              <div className="text-right">
                <div className="text-3xl font-bold text-green-600">{roiMultiple.toFixed(1)}x</div>
                <div className="text-sm text-gray-600">ROI Multiple</div>
              </div>
              <div className="flex gap-2">
                <Button onClick={onExportPDF} variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Export PDF
                </Button>
                <Button onClick={toggleFullscreen} size="sm" className="bg-purple-600 hover:bg-purple-700">
                  <Maximize2 className="w-4 h-4 mr-2" />
                  Present
                </Button>
              </div>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Narrative Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Executive Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg leading-relaxed text-gray-700 mb-6">
              {narrative.executiveSummary}
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {narrative.keyMetrics.map((metric, index) => (
                <div key={index} className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600 mb-1">
                    {metric.value}
                  </div>
                  <div className="text-sm font-medium text-gray-800">
                    {metric.label}
                  </div>
                  <div className="text-xs text-gray-600 mt-1">
                    {metric.impact}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Value Highlights</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2 text-sm">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span>24/7 AI Qualification</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span>5% Price Optimization</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span>48% Faster Sales</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span>95% Qualification Accuracy</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span>Guaranteed Results</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Slide Navigation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Presentation Slides</span>
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={prevSlide}
                disabled={currentSlide === 0}
              >
                <SkipBack className="w-4 h-4" />
              </Button>
              <span className="text-sm text-gray-600">
                {currentSlide + 1} of {presentation.slides.length}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={nextSlide}
                disabled={currentSlide === presentation.slides.length - 1}
              >
                <SkipForward className="w-4 h-4" />
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            {presentation.slides.map((slide, index) => (
              <Button
                key={index}
                variant={currentSlide === index ? "default" : "outline"}
                className="h-auto p-3 text-left"
                onClick={() => setCurrentSlide(index)}
              >
                <div>
                  <div className="font-semibold text-sm">{slide.title}</div>
                  <div className="text-xs text-gray-600 mt-1 capitalize">
                    {slide.visualType} slide
                  </div>
                </div>
              </Button>
            ))}
          </div>

          {/* Current Slide Display */}
          <Card className="border-2">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {presentation.slides[currentSlide].visualType === 'chart' && <TrendingUp className="w-5 h-5" />}
                {presentation.slides[currentSlide].visualType === 'comparison' && <Target className="w-5 h-5" />}
                {presentation.slides[currentSlide].visualType === 'stats' && <Zap className="w-5 h-5" />}
                {presentation.slides[currentSlide].visualType === 'narrative' && <FileText className="w-5 h-5" />}
                {presentation.slides[currentSlide].title}
              </CardTitle>
              {presentation.slides[currentSlide].subtitle && (
                <p className="text-gray-600">{presentation.slides[currentSlide].subtitle}</p>
              )}
            </CardHeader>
            <CardContent>
              <div className="prose max-w-none">
                {presentation.slides[currentSlide].content.split('\n').map((line, index) => {
                  if (line.startsWith('•')) {
                    return (
                      <div key={index} className="flex items-start gap-2 mb-2">
                        <div className="w-1.5 h-1.5 bg-blue-600 rounded-full mt-2.5 flex-shrink-0"></div>
                        <span>{line.substring(1).trim()}</span>
                      </div>
                    );
                  } else if (line.startsWith('**') && line.endsWith('**')) {
                    return (
                      <h3 key={index} className="font-bold text-lg text-gray-900 mb-3 mt-4">
                        {line.slice(2, -2)}
                      </h3>
                    );
                  } else if (line.trim()) {
                    return (
                      <p key={index} className="mb-3 leading-relaxed">
                        {line}
                      </p>
                    );
                  }
                  return null;
                })}
              </div>

              {/* Slide-specific data visualization */}
              {presentation.slides[currentSlide].data && (
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  {presentation.slides[currentSlide].visualType === 'stats' && (
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-3xl font-bold text-green-600 mb-2">
                          {roiMultiple.toFixed(1)}x
                        </div>
                        <div className="text-sm text-gray-600">ROI Multiple</div>
                      </div>
                      <div>
                        <div className="text-3xl font-bold text-blue-600 mb-2">
                          {ROIEngine.formatCurrency(roiCalculation.netROI)}
                        </div>
                        <div className="text-sm text-gray-600">Net Benefit</div>
                      </div>
                      <div>
                        <div className="text-3xl font-bold text-purple-600 mb-2">
                          {roiCalculation.breakEvenMonths}
                        </div>
                        <div className="text-sm text-gray-600">Break-Even (Months)</div>
                      </div>
                    </div>
                  )}

                  {presentation.slides[currentSlide].visualType === 'comparison' && (
                    <div className="space-y-4">
                      {roiCalculation.marketComparisons.slice(0, 3).map((comparison, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <span className="text-sm font-medium">{comparison.category}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-600">
                              {comparison.traditional} → {comparison.jorgeAI} {comparison.unit}
                            </span>
                            <Badge variant="outline" className="text-green-700">
                              +{comparison.improvement.toFixed(1)}%
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Slide Notes */}
              {presentation.slides[currentSlide].notes && (
                <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="flex items-start gap-2">
                    <Eye className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="text-sm font-medium text-blue-800 mb-1">Presentation Notes:</div>
                      <div className="text-sm text-blue-700">
                        {presentation.slides[currentSlide].notes}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </CardContent>
      </Card>

      {/* Call to Action */}
      <Card className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-200">
        <CardContent className="p-6">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-900 mb-3">Ready to Experience Jorge's AI Advantage?</h3>
            <p className="text-lg text-gray-700 mb-6">{narrative.callToAction}</p>

            <div className="flex items-center justify-center gap-4">
              <Button size="lg" className="bg-green-600 hover:bg-green-700">
                <CheckCircle className="w-5 h-5 mr-2" />
                Schedule Consultation
              </Button>
              <Button variant="outline" size="lg" onClick={onExportPDF}>
                <Download className="w-5 h-5 mr-2" />
                Download Proposal
              </Button>
            </div>

            <div className="grid grid-cols-3 gap-6 mt-8 pt-6 border-t border-gray-200">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600 mb-1">2 Minutes</div>
                <div className="text-sm text-gray-600">Average Response Time</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600 mb-1">95%</div>
                <div className="text-sm text-gray-600">Qualification Accuracy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600 mb-1">24/7</div>
                <div className="text-sm text-gray-600">AI Working for You</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Handout Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Executive Handout Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-gray-50 p-4 rounded-lg border">
            <pre className="text-sm whitespace-pre-wrap font-mono">
              {presentation.handoutSummary}
            </pre>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}