// Jorge's Demo Control Panel
// Professional presentation controls for live demonstrations

'use client';

import { useState } from 'react';
import {
  PlayCircle,
  PauseCircle,
  RotateCcw,
  SkipForward,
  Monitor,
  Settings,
  Volume2,
  VolumeX,
  Clock,
  Users,
  Target,
  Zap,
  CheckCircle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { motion } from 'framer-motion';
import type { DemoScenario } from '@/lib/demo/ScenarioEngine';

interface DemoControlPanelProps {
  scenario: DemoScenario | null;
  isActive: boolean;
  progress: number;
  onStart: () => void;
  onPause: () => void;
  onReset: () => void;
  onNext: () => void;
  onPresentationMode: () => void;
}

export function DemoControlPanel({
  scenario,
  isActive,
  progress,
  onStart,
  onPause,
  onReset,
  onNext,
  onPresentationMode
}: DemoControlPanelProps) {
  const [isMuted, setIsMuted] = useState(false);
  const [autoAdvance, setAutoAdvance] = useState(false);
  const [showNotes, setShowNotes] = useState(true);

  if (!scenario) {
    return (
      <Card className="bg-white/5 border-white/10">
        <CardContent className="p-6 text-center">
          <div className="w-16 h-16 bg-gray-500/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <Target className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-gray-400">Select a scenario to begin</p>
        </CardContent>
      </Card>
    );
  }

  const formatTime = (minutes: number) => {
    return `${Math.floor(minutes)}:${Math.round((minutes % 1) * 60).toString().padStart(2, '0')}`;
  };

  const getScenarioStatus = () => {
    if (progress === 100) return { label: 'Complete', color: 'text-green-400', icon: CheckCircle };
    if (isActive) return { label: 'Running', color: 'text-blue-400', icon: PlayCircle };
    if (progress > 0) return { label: 'Paused', color: 'text-yellow-400', icon: PauseCircle };
    return { label: 'Ready', color: 'text-gray-400', icon: Clock };
  };

  const status = getScenarioStatus();
  const StatusIcon = status.icon;

  return (
    <div className="space-y-4">
      {/* Scenario Status */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader className="pb-3">
          <CardTitle className="text-white text-lg flex items-center">
            <StatusIcon className={`w-5 h-5 mr-2 ${status.color}`} />
            Demo Status
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0 space-y-4">
          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Progress</span>
              <span className="text-white">{Math.round(progress)}%</span>
            </div>
            <Progress value={progress} className="h-2" />
            <div className="flex items-center justify-between text-xs text-gray-400">
              <span>0:00</span>
              <span className={status.color}>{status.label}</span>
              <span>{formatTime(scenario.duration)}</span>
            </div>
          </div>

          {/* Scenario Info */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <div className="text-gray-400">Duration</div>
              <div className="text-white">{scenario.duration} minutes</div>
            </div>
            <div>
              <div className="text-gray-400">Participants</div>
              <div className="text-white">{scenario.participants.length}</div>
            </div>
            <div>
              <div className="text-gray-400">Category</div>
              <div className="text-white capitalize">{scenario.category.replace('_', ' ')}</div>
            </div>
            <div>
              <div className="text-gray-400">Steps</div>
              <div className="text-white">{scenario.conversationFlow.length}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Primary Controls */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader className="pb-3">
          <CardTitle className="text-white text-lg flex items-center">
            <Zap className="w-5 h-5 mr-2 text-blue-400" />
            Demo Controls
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0 space-y-4">
          {/* Main Action Buttons */}
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={isActive ? onPause : onStart}
              disabled={progress === 100}
              className={`
                ${isActive
                  ? 'bg-yellow-600 hover:bg-yellow-700'
                  : progress === 100
                    ? 'bg-gray-600 cursor-not-allowed'
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
                  Complete
                </>
              ) : (
                <>
                  <PlayCircle className="w-4 h-4 mr-2" />
                  {progress > 0 ? 'Resume' : 'Start Demo'}
                </>
              )}
            </Button>

            <Button
              onClick={onReset}
              variant="outline"
              className="border-white/20 text-white hover:bg-white/10"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>
          </div>

          {/* Secondary Controls */}
          <div className="grid grid-cols-2 gap-3">
            <Button
              onClick={onNext}
              disabled={!isActive && progress !== 100}
              size="sm"
              variant="outline"
              className="border-white/20 text-white hover:bg-white/10"
            >
              <SkipForward className="w-4 h-4 mr-2" />
              Next Step
            </Button>

            <Button
              onClick={onPresentationMode}
              size="sm"
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Monitor className="w-4 h-4 mr-2" />
              Present
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Demo Settings */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader className="pb-3">
          <CardTitle className="text-white text-lg flex items-center">
            <Settings className="w-5 h-5 mr-2 text-gray-400" />
            Demo Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0 space-y-4">
          {/* Audio Controls */}
          <div className="flex items-center justify-between">
            <Label className="text-white text-sm flex items-center">
              {isMuted ? (
                <VolumeX className="w-4 h-4 mr-2 text-gray-400" />
              ) : (
                <Volume2 className="w-4 h-4 mr-2 text-blue-400" />
              )}
              Audio Enabled
            </Label>
            <Switch
              checked={!isMuted}
              onCheckedChange={(checked) => setIsMuted(!checked)}
            />
          </div>

          {/* Auto-Advance */}
          <div className="flex items-center justify-between">
            <Label className="text-white text-sm flex items-center">
              <PlayCircle className="w-4 h-4 mr-2 text-blue-400" />
              Auto-Advance Steps
            </Label>
            <Switch
              checked={autoAdvance}
              onCheckedChange={setAutoAdvance}
            />
          </div>

          {/* Show Demo Notes */}
          <div className="flex items-center justify-between">
            <Label className="text-white text-sm flex items-center">
              <Target className="w-4 h-4 mr-2 text-blue-400" />
              Show Demo Notes
            </Label>
            <Switch
              checked={showNotes}
              onCheckedChange={setShowNotes}
            />
          </div>

          {/* Demo Speed Control */}
          <div className="space-y-2">
            <Label className="text-white text-sm">Demo Speed</Label>
            <div className="space-y-1">
              <Slider
                defaultValue={[75]}
                max={150}
                min={25}
                step={25}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-gray-400">
                <span>0.25x</span>
                <span>Normal</span>
                <span>1.5x</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Scenario Overview */}
      <Card className="bg-white/5 border-white/10">
        <CardHeader className="pb-3">
          <CardTitle className="text-white text-lg flex items-center">
            <Target className="w-5 h-5 mr-2 text-purple-400" />
            Scenario Overview
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-0 space-y-4">
          <div>
            <h5 className="font-semibold text-white mb-2">{scenario.name}</h5>
            <p className="text-gray-300 text-sm">{scenario.description}</p>
          </div>

          {/* Key Benefits */}
          <div className="space-y-3">
            <div>
              <div className="text-gray-400 text-sm mb-1">Jorge Advantages:</div>
              <div className="space-y-1">
                {scenario.jorgeAdvantages.slice(0, 3).map((advantage, i) => (
                  <div key={i} className="text-xs text-blue-300 flex items-start">
                    <div className="w-1 h-1 bg-blue-400 rounded-full mr-2 mt-1.5 flex-shrink-0"></div>
                    <span>{advantage}</span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <div className="text-gray-400 text-sm mb-1">Client Benefits:</div>
              <div className="space-y-1">
                {scenario.clientBenefits.slice(0, 3).map((benefit, i) => (
                  <div key={i} className="text-xs text-green-300 flex items-start">
                    <div className="w-1 h-1 bg-green-400 rounded-full mr-2 mt-1.5 flex-shrink-0"></div>
                    <span>{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Expected Outcomes */}
          <div>
            <div className="text-gray-400 text-sm mb-2">Expected Outcomes:</div>
            <div className="grid grid-cols-2 gap-2">
              {scenario.expectedOutcomes.slice(0, 4).map((outcome, i) => (
                <div key={i} className="bg-white/5 rounded-lg p-2 border border-white/10">
                  <div className="text-xs text-gray-400">{outcome.metric}</div>
                  <div className="text-sm font-semibold text-white">{outcome.value}</div>
                  {outcome.comparison && (
                    <div className="text-xs text-blue-300">{outcome.comparison}</div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Participants */}
          <div>
            <div className="text-gray-400 text-sm mb-2">Participants:</div>
            <div className="space-y-1">
              {scenario.participants.map((participant, i) => (
                <div key={i} className="flex items-center gap-2">
                  <Users className="w-3 h-3 text-gray-400" />
                  <span className="text-sm text-white">{participant.name}</span>
                  <Badge variant="outline" className="text-xs">
                    {participant.role.replace('_', ' ')}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border-blue-500/20">
          <CardContent className="p-4">
            <div className="text-center space-y-3">
              <div className="text-blue-300 font-semibold text-sm">Ready to impress your client?</div>
              <Button
                onClick={onPresentationMode}
                size="lg"
                className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
              >
                <Monitor className="w-5 h-5 mr-2" />
                Launch Professional Presentation
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

export default DemoControlPanel;