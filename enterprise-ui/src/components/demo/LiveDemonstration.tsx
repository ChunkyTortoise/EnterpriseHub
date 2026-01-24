// Jorge's Live Demonstration Component
// Real-time demo control and metrics display for professional presentations

'use client';

import { useState, useEffect } from 'react';
import {
  PlayCircle,
  PauseCircle,
  SkipForward,
  RotateCcw,
  Target,
  TrendingUp,
  Award,
  Clock,
  Users,
  MessageSquare,
  BarChart3,
  Zap,
  CheckCircle,
  DollarSign
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { motion, AnimatePresence } from 'framer-motion';
import type { DemoScenario, DemoOutcome } from '@/lib/demo/ScenarioEngine';

interface LiveDemonstrationProps {
  scenario: DemoScenario;
  isActive: boolean;
  progress: number;
  conversationProgress: number;
  onStart: () => void;
  onPause: () => void;
  onReset: () => void;
  onNext: () => void;
  onSkip: () => void;
  expectedOutcomes: DemoOutcome[];
  jorgeAdvantages: string[];
}

export function LiveDemonstration({
  scenario,
  isActive,
  progress,
  conversationProgress,
  onStart,
  onPause,
  onReset,
  onNext,
  onSkip,
  expectedOutcomes,
  jorgeAdvantages
}: LiveDemonstrationProps) {
  const [startTime] = useState(Date.now());
  const [elapsedTime, setElapsedTime] = useState(0);
  const [realtimeMetrics, setRealtimeMetrics] = useState({
    clientEngagement: 85,
    demonstrationImpact: 92,
    jorgeCredibility: 96,
    salesMomentum: 78
  });

  // Update elapsed time
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsedTime(Date.now() - startTime);
    }, 1000);

    return () => clearInterval(interval);
  }, [startTime]);

  // Simulate real-time metrics updates
  useEffect(() => {
    if (!isActive) return;

    const interval = setInterval(() => {
      setRealtimeMetrics(prev => ({
        clientEngagement: Math.min(100, prev.clientEngagement + (Math.random() * 4 - 2)),
        demonstrationImpact: Math.min(100, prev.demonstrationImpact + (Math.random() * 3 - 1)),
        jorgeCredibility: Math.min(100, prev.jorgeCredibility + (Math.random() * 2 - 1)),
        salesMomentum: Math.min(100, prev.salesMomentum + (Math.random() * 6 - 3))
      }));
    }, 2000);

    return () => clearInterval(interval);
  }, [isActive]);

  const formatTime = (milliseconds: number) => {
    const seconds = Math.floor(milliseconds / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getMetricColor = (value: number) => {
    if (value >= 90) return 'text-green-400';
    if (value >= 75) return 'text-blue-400';
    if (value >= 60) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getOutcomeIcon = (metric: string) => {
    const iconMap: Record<string, any> = {
      'Lead Temperature': Target,
      'Qualification Time': Clock,
      'Commitment Level': Award,
      'Sale Speed': TrendingUp,
      'ROI Accuracy': BarChart3,
      'Client Satisfaction': Users,
      'Pricing Accuracy': DollarSign
    };
    return iconMap[metric] || CheckCircle;
  };

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6">
      {/* Demo Status */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader className="pb-3">
          <CardTitle className="text-white text-lg flex items-center">
            <Target className="w-5 h-5 mr-2 text-blue-400" />
            Demo Status
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Progress */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Overall Progress</span>
              <span className="text-white font-medium">{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Conversation</span>
              <span className="text-white font-medium">{Math.round(conversationProgress)}%</span>
            </div>
            <Progress value={conversationProgress} className="h-2" />
          </div>

          {/* Timer */}
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-400">Elapsed Time</span>
            <span className="text-white font-medium font-mono">{formatTime(elapsedTime)}</span>
          </div>

          {/* Status Badge */}
          <div className="flex justify-center">
            <Badge
              variant="outline"
              className={`${
                isActive
                  ? 'bg-green-500/10 text-green-400 border-green-500/30'
                  : progress === 100
                  ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                  : 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30'
              }`}
            >
              {isActive ? (
                <>
                  <PlayCircle className="w-4 h-4 mr-1" />
                  Live Demo Running
                </>
              ) : progress === 100 ? (
                <>
                  <CheckCircle className="w-4 h-4 mr-1" />
                  Demo Complete
                </>
              ) : (
                <>
                  <PauseCircle className="w-4 h-4 mr-1" />
                  Demo Paused
                </>
              )}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Demo Controls */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader className="pb-3">
          <CardTitle className="text-white text-lg flex items-center">
            <Zap className="w-5 h-5 mr-2 text-blue-400" />
            Presentation Controls
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={isActive ? onPause : onStart}
              disabled={progress === 100}
              className={`
                ${isActive
                  ? 'bg-yellow-600 hover:bg-yellow-700'
                  : progress === 100
                  ? 'bg-gray-600'
                  : 'bg-green-600 hover:bg-green-700'
                } text-white
              `}
            >
              {isActive ? (
                <>
                  <PauseCircle className="w-4 h-4 mr-2" />
                  Pause
                </>
              ) : progress === 100 ? (
                <>
                  <CheckCircle className="w-4 h-4 mr-2" />
                  Done
                </>
              ) : (
                <>
                  <PlayCircle className="w-4 h-4 mr-2" />
                  {progress > 0 ? 'Resume' : 'Start'}
                </>
              )}
            </Button>

            <Button
              onClick={onNext}
              disabled={!isActive}
              variant="outline"
              className="border-white/20 text-white hover:bg-white/10"
            >
              <SkipForward className="w-4 h-4 mr-2" />
              Next Step
            </Button>
          </div>

          <Button
            onClick={onReset}
            variant="outline"
            size="sm"
            className="w-full border-white/20 text-white hover:bg-white/10"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset Demo
          </Button>
        </CardContent>
      </Card>

      {/* Real-time Metrics */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader className="pb-3">
          <CardTitle className="text-white text-lg flex items-center">
            <BarChart3 className="w-5 h-5 mr-2 text-green-400" />
            Live Metrics
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <AnimatePresence>
            {Object.entries(realtimeMetrics).map(([key, value], index) => (
              <motion.div
                key={key}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="space-y-2"
              >
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-400 capitalize">
                    {key.replace(/([A-Z])/g, ' $1').trim()}
                  </span>
                  <span className={`font-medium ${getMetricColor(value)}`}>
                    {Math.round(value)}%
                  </span>
                </div>
                <Progress value={value} className="h-1.5" />
              </motion.div>
            ))}
          </AnimatePresence>
        </CardContent>
      </Card>

      {/* Expected Outcomes */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader className="pb-3">
          <CardTitle className="text-white text-lg flex items-center">
            <Award className="w-5 h-5 mr-2 text-purple-400" />
            Expected Outcomes
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {expectedOutcomes.map((outcome, index) => {
            const Icon = getOutcomeIcon(outcome.metric);
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white/5 rounded-lg p-3 border border-white/10"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-2">
                    <Icon className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <div className="text-white text-sm font-medium">{outcome.metric}</div>
                      <div className="text-blue-300 text-sm font-semibold">{outcome.value}</div>
                      {outcome.comparison && (
                        <div className="text-gray-400 text-xs">{outcome.comparison}</div>
                      )}
                    </div>
                  </div>
                  <Badge
                    variant="outline"
                    className={`text-xs ${
                      outcome.significance === 'high'
                        ? 'bg-green-500/10 text-green-400 border-green-500/30'
                        : outcome.significance === 'medium'
                        ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/30'
                        : 'bg-gray-500/10 text-gray-400 border-gray-500/30'
                    }`}
                  >
                    {outcome.significance}
                  </Badge>
                </div>
              </motion.div>
            );
          })}
        </CardContent>
      </Card>

      {/* Jorge Advantages */}
      <Card className="bg-gradient-to-br from-blue-500/10 to-purple-500/10 border-blue-500/20">
        <CardHeader className="pb-3">
          <CardTitle className="text-white text-lg flex items-center">
            <Zap className="w-5 h-5 mr-2 text-yellow-400" />
            Jorge's Advantages
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {jorgeAdvantages.slice(0, 4).map((advantage, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.15 }}
              className="flex items-start gap-2 text-sm"
            >
              <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0"></div>
              <span className="text-blue-300 leading-relaxed">{advantage}</span>
            </motion.div>
          ))}
        </CardContent>
      </Card>

      {/* Demo Information */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader className="pb-3">
          <CardTitle className="text-white text-lg flex items-center">
            <MessageSquare className="w-5 h-5 mr-2 text-gray-400" />
            Scenario Info
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-gray-400">Duration</div>
              <div className="text-white">{scenario.duration} min</div>
            </div>
            <div>
              <div className="text-gray-400">Category</div>
              <div className="text-white capitalize">{scenario.category.replace('_', ' ')}</div>
            </div>
            <div>
              <div className="text-gray-400">Steps</div>
              <div className="text-white">{scenario.conversationFlow.length}</div>
            </div>
            <div>
              <div className="text-gray-400">Participants</div>
              <div className="text-white">{scenario.participants.length}</div>
            </div>
          </div>

          <div>
            <div className="text-gray-400 mb-2">Description</div>
            <p className="text-gray-300 text-xs leading-relaxed">{scenario.description}</p>
          </div>
        </CardContent>
      </Card>

      {/* Demo Tips */}
      <Card className="bg-gradient-to-br from-green-500/10 to-blue-500/10 border-green-500/20">
        <CardHeader className="pb-3">
          <CardTitle className="text-white text-lg flex items-center">
            <Target className="w-5 h-5 mr-2 text-green-400" />
            Presentation Tips
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-xs">
          <div className="flex items-start gap-2">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full mt-1.5 flex-shrink-0"></div>
            <span className="text-green-300">Emphasize Jorge's confrontational qualification methodology</span>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full mt-1.5 flex-shrink-0"></div>
            <span className="text-green-300">Highlight the 6% commission value proposition</span>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full mt-1.5 flex-shrink-0"></div>
            <span className="text-green-300">Focus on speed and guaranteed results</span>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full mt-1.5 flex-shrink-0"></div>
            <span className="text-green-300">Use real-time metrics to build credibility</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default LiveDemonstration;