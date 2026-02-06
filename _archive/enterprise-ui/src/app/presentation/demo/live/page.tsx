// Jorge's Live Demo Presentation
// Full-screen professional demonstration interface for client presentations

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  Monitor,
  Maximize,
  Minimize,
  Volume2,
  VolumeX,
  PlayCircle,
  PauseCircle,
  SkipForward,
  Settings,
  X,
  Users,
  MessageSquare,
  BarChart3,
  Clock,
  Target,
  Zap,
  CheckCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { motion, AnimatePresence } from 'framer-motion';
import useDemoMode, { useConversationDisplay, usePresentationControls } from '@/hooks/useDemoMode';
import { LiveDemonstration } from '@/components/demo/LiveDemonstration';
import { BotConversationDemo } from '@/components/demo/BotConversationDemo';
import { ScenarioPlayback } from '@/components/demo/ScenarioPlayback';

export default function LiveDemoPage() {
  const router = useRouter();
  const [demoState, demoActions] = useDemoMode();
  const conversationDisplay = useConversationDisplay();
  const presentationControls = usePresentationControls();
  const [isFullScreen, setIsFullScreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
  const [lastActivity, setLastActivity] = useState(Date.now());

  // Auto-hide controls in fullscreen after inactivity
  useEffect(() => {
    if (!isFullScreen) return;

    const handleActivity = () => {
      setLastActivity(Date.now());
      setShowControls(true);
    };

    const checkActivity = () => {
      if (Date.now() - lastActivity > 3000) {
        setShowControls(false);
      }
    };

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];
    events.forEach(event => {
      document.addEventListener(event, handleActivity);
    });

    const interval = setInterval(checkActivity, 1000);

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, handleActivity);
      });
      clearInterval(interval);
    };
  }, [isFullScreen, lastActivity]);

  // Fullscreen handling
  const toggleFullScreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => {
        setIsFullScreen(true);
      }).catch(console.error);
    } else {
      document.exitFullscreen().then(() => {
        setIsFullScreen(false);
      }).catch(console.error);
    }
  }, []);

  // Handle escape key
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'Escape':
          if (isFullScreen) {
            toggleFullScreen();
          } else {
            router.push('/presentation/demo/scenarios');
          }
          break;
        case ' ':
          e.preventDefault();
          if (presentationControls.isActive) {
            presentationControls.controls.pause();
          } else {
            presentationControls.controls.start();
          }
          break;
        case 'ArrowRight':
          e.preventDefault();
          presentationControls.controls.next();
          break;
        case 'r':
          if (e.ctrlKey) {
            e.preventDefault();
            presentationControls.controls.reset();
          }
          break;
        case 'f':
          e.preventDefault();
          toggleFullScreen();
          break;
        case 'm':
          e.preventDefault();
          setIsMuted(!isMuted);
          break;
      }
    };

    document.addEventListener('keydown', handleKeyPress);
    return () => document.removeEventListener('keydown', handleKeyPress);
  }, [isFullScreen, presentationControls, isMuted, toggleFullScreen, router]);

  // Start presentation mode if not already active
  useEffect(() => {
    if (!demoState.isPresentationMode) {
      demoActions.enterPresentationMode();
    }

    return () => {
      // Cleanup on unmount
      if (isFullScreen && document.fullscreenElement) {
        document.exitFullscreen().catch(console.error);
      }
    };
  }, [demoState.isPresentationMode, demoActions, isFullScreen]);

  if (!demoState.currentScenario) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <Card className="bg-white/5 border-white/10 max-w-md mx-auto">
          <CardContent className="p-8 text-center">
            <div className="w-16 h-16 bg-gray-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
              <Target className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-4">No Scenario Selected</h3>
            <p className="text-gray-300 mb-6">
              Please select a scenario before starting the live demonstration.
            </p>
            <Button
              onClick={() => router.push('/presentation/demo/scenarios')}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <Settings className="w-4 h-4 mr-2" />
              Configure Demo
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 overflow-hidden">
      {/* Main Presentation Area */}
      <div className="relative h-full flex flex-col">
        {/* Header (hidden in fullscreen unless controls shown) */}
        <AnimatePresence>
          {(!isFullScreen || showControls) && (
            <motion.header
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
              className="bg-black/40 backdrop-blur-md border-b border-white/10 px-6 py-4 z-50"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Monitor className="w-6 h-6 text-blue-400" />
                    <div>
                      <h1 className="text-lg font-bold text-white">Live Demo Presentation</h1>
                      <p className="text-blue-200 text-sm">{demoState.currentScenario.name}</p>
                    </div>
                  </div>

                  <Badge variant="outline" className="bg-green-500/10 text-green-300 border-green-400">
                    <CheckCircle className="w-4 h-4 mr-1" />
                    Live
                  </Badge>
                </div>

                <div className="flex items-center gap-3">
                  {/* Progress */}
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-400" />
                    <span className="text-white text-sm">
                      {Math.round(presentationControls.progress)}%
                    </span>
                  </div>

                  {/* Audio Toggle */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsMuted(!isMuted)}
                    className="text-white hover:bg-white/10"
                  >
                    {isMuted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4" />}
                  </Button>

                  {/* Fullscreen Toggle */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={toggleFullScreen}
                    className="text-white hover:bg-white/10"
                  >
                    {isFullScreen ? <Minimize className="w-4 h-4" /> : <Maximize className="w-4 h-4" />}
                  </Button>

                  {/* Exit */}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push('/presentation/demo/scenarios')}
                    className="text-white hover:bg-white/10"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mt-3">
                <Progress value={presentationControls.progress} className="h-1" />
              </div>
            </motion.header>
          )}
        </AnimatePresence>

        {/* Main Content Area */}
        <div className="flex-1 flex">
          {/* Primary Demo Area */}
          <div className="flex-1 flex flex-col">
            {/* Scenario Content */}
            <div className="flex-1 overflow-hidden">
              <ScenarioPlayback
                scenario={demoState.currentScenario}
                conversationState={conversationDisplay.conversationState}
                currentStep={conversationDisplay.currentStep}
                isTyping={conversationDisplay.isTyping}
                settings={conversationDisplay.settings}
                isFullScreen={isFullScreen}
                isMuted={isMuted}
              />
            </div>

            {/* Bot Conversation Interface */}
            <div className={`${isFullScreen ? 'h-1/3' : 'h-2/5'} border-t border-white/10`}>
              <BotConversationDemo
                scenario={demoState.currentScenario}
                conversationState={conversationDisplay.conversationState}
                currentStep={conversationDisplay.currentStep}
                isTyping={conversationDisplay.isTyping}
                onUserInput={(input) => {
                  // Handle simulated user input
                  console.log('User input:', input);
                }}
                isFullScreen={isFullScreen}
              />
            </div>
          </div>

          {/* Control Panel (hidden in fullscreen unless controls shown) */}
          <AnimatePresence>
            {(!isFullScreen || showControls) && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3 }}
                className="w-80 border-l border-white/10 bg-black/20 backdrop-blur-md"
              >
                <LiveDemonstration
                  scenario={demoState.currentScenario}
                  isActive={presentationControls.isActive}
                  progress={presentationControls.progress}
                  conversationProgress={demoState.conversationProgress}
                  onStart={presentationControls.controls.start}
                  onPause={presentationControls.controls.pause}
                  onReset={presentationControls.controls.reset}
                  onNext={presentationControls.controls.next}
                  onSkip={presentationControls.controls.skip}
                  expectedOutcomes={demoState.currentScenario.expectedOutcomes}
                  jorgeAdvantages={demoState.currentScenario.jorgeAdvantages}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Floating Controls (fullscreen only) */}
        <AnimatePresence>
          {isFullScreen && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: showControls ? 1 : 0.3, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              transition={{ duration: 0.3 }}
              className="absolute bottom-6 left-1/2 transform -translate-x-1/2 z-50"
            >
              <div className="bg-black/60 backdrop-blur-md rounded-full border border-white/20 px-4 py-3 flex items-center gap-3">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={presentationControls.isActive ? presentationControls.controls.pause : presentationControls.controls.start}
                  className="text-white hover:bg-white/20 rounded-full"
                >
                  {presentationControls.isActive ? (
                    <PauseCircle className="w-5 h-5" />
                  ) : (
                    <PlayCircle className="w-5 h-5" />
                  )}
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={presentationControls.controls.next}
                  className="text-white hover:bg-white/20 rounded-full"
                >
                  <SkipForward className="w-5 h-5" />
                </Button>

                <div className="w-px h-6 bg-white/20"></div>

                <div className="text-white text-sm font-medium">
                  {Math.round(presentationControls.progress)}%
                </div>

                <div className="w-px h-6 bg-white/20"></div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsMuted(!isMuted)}
                  className="text-white hover:bg-white/20 rounded-full"
                >
                  {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={toggleFullScreen}
                  className="text-white hover:bg-white/20 rounded-full"
                >
                  <Minimize className="w-5 h-5" />
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Help Overlay */}
        <AnimatePresence>
          {isFullScreen && showControls && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="absolute top-6 right-6 z-50"
            >
              <Card className="bg-black/60 backdrop-blur-md border-white/20">
                <CardContent className="p-4">
                  <div className="text-white text-sm space-y-1">
                    <div className="font-medium mb-2">Keyboard Shortcuts</div>
                    <div><kbd className="bg-white/20 px-1 rounded text-xs">Space</kbd> Play/Pause</div>
                    <div><kbd className="bg-white/20 px-1 rounded text-xs">→</kbd> Next Step</div>
                    <div><kbd className="bg-white/20 px-1 rounded text-xs">F</kbd> Fullscreen</div>
                    <div><kbd className="bg-white/20 px-1 rounded text-xs">M</kbd> Mute</div>
                    <div><kbd className="bg-white/20 px-1 rounded text-xs">Esc</kbd> Exit</div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error Display */}
        <AnimatePresence>
          {demoState.error && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.3 }}
              className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50"
            >
              <Card className="bg-red-500/10 border-red-500/30 max-w-md">
                <CardContent className="p-6 text-center">
                  <div className="text-red-400 mb-4">
                    <Target className="w-8 h-8 mx-auto" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">Demo Error</h3>
                  <p className="text-gray-300 mb-4">{demoState.error}</p>
                  <div className="flex gap-3 justify-center">
                    <Button
                      variant="outline"
                      onClick={presentationControls.controls.reset}
                      className="border-white/20 text-white hover:bg-white/10"
                    >
                      Restart Demo
                    </Button>
                    <Button
                      onClick={() => router.push('/presentation/demo/scenarios')}
                      className="bg-blue-600 hover:bg-blue-700"
                    >
                      Exit to Configuration
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}