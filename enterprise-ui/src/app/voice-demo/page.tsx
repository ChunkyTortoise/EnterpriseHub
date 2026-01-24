'use client';

import { motion } from "framer-motion";
import { useState } from "react";
import { VoiceRecorder } from "@/components/mobile/voice/VoiceRecorder";
import { VoiceNotesList } from "@/components/mobile/voice/VoiceNotesList";
import { VoiceCommands } from "@/components/mobile/voice/VoiceCommands";
import { VoicePermissionsProvider } from "@/components/mobile/voice/VoicePermissionsProvider";
import { VoiceProcessingIndicator } from "@/components/mobile/voice/VoiceProcessingIndicator";
import { useVoiceRecording } from "@/hooks/useVoiceRecording";
import {
  MicrophoneIcon,
  SpeakerWaveIcon,
  DocumentTextIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";

// Demo data for showcase
const demoVoiceNotes = [
  {
    id: 'demo-1',
    transcript: 'Client loved the kitchen and the open floor plan. They mentioned the backyard is perfect for their kids. Ready to move forward with an offer. Need to follow up with mortgage pre-approval status.',
    audioBlob: new Blob(),
    duration: 45,
    timestamp: Date.now() - 3600000,
    category: 'client_feedback' as const,
    confidence: 0.94,
    keywords: ['kitchen', 'open floor plan', 'backyard', 'offer', 'mortgage', 'pre-approval'],
    actionItems: [
      {
        id: 'action-1',
        task: 'Follow up with mortgage pre-approval status',
        priority: 'high' as const,
        isCompleted: false,
        extractedFrom: 'Need to follow up with mortgage pre-approval status.',
      }
    ],
    sentiment: 'positive' as const,
    location: {
      latitude: 40.7128,
      longitude: -74.0060,
      accuracy: 10,
      altitude: null,
      altitudeAccuracy: null,
      heading: null,
      speed: null,
    },
  },
  {
    id: 'demo-2',
    transcript: 'Property showing went well. 123 Main Street has great potential but needs kitchen updates. Estimated renovation cost around $25,000. Client budget allows for it. Schedule second showing with contractor.',
    audioBlob: new Blob(),
    duration: 32,
    timestamp: Date.now() - 7200000,
    category: 'showing_notes' as const,
    confidence: 0.89,
    keywords: ['123 Main Street', 'kitchen updates', '$25,000', 'renovation', 'contractor', 'second showing'],
    actionItems: [
      {
        id: 'action-2',
        task: 'Schedule second showing with contractor',
        priority: 'medium' as const,
        isCompleted: false,
        extractedFrom: 'Schedule second showing with contractor.',
      }
    ],
    sentiment: 'neutral' as const,
  },
  {
    id: 'demo-3',
    transcript: 'Market observation: Neighborhood is trending upward. Three new listings this week, all priced 15% higher than last month. Inventory is low. Good time for sellers.',
    audioBlob: new Blob(),
    duration: 28,
    timestamp: Date.now() - 10800000,
    category: 'market_observations' as const,
    confidence: 0.92,
    keywords: ['market', 'neighborhood', 'trending upward', 'listings', '15% higher', 'inventory', 'sellers'],
    actionItems: [],
    sentiment: 'positive' as const,
  },
];

export default function VoiceDemoPage() {
  const [showDemo, setShowDemo] = useState(false);
  const [currentDemo, setCurrentDemo] = useState<'recorder' | 'list' | 'commands'>('recorder');
  const [processingStage, setProcessingStage] = useState<'recording' | 'analyzing' | 'transcribing' | 'categorizing' | 'complete'>('recording');
  const [processingProgress, setProcessingProgress] = useState(0);

  // Real voice recording hook for actual functionality
  const voiceHook = useVoiceRecording();

  const handleDemoStart = () => {
    setShowDemo(true);
    setCurrentDemo('recorder');
    // Simulate processing stages
    simulateProcessing();
  };

  const simulateProcessing = () => {
    setProcessingStage('recording');
    setProcessingProgress(0);

    setTimeout(() => {
      setProcessingStage('analyzing');
      animateProgress(20);
    }, 2000);

    setTimeout(() => {
      setProcessingStage('transcribing');
      animateProgress(60);
    }, 4000);

    setTimeout(() => {
      setProcessingStage('categorizing');
      animateProgress(90);
    }, 6000);

    setTimeout(() => {
      setProcessingStage('complete');
      setProcessingProgress(100);
    }, 8000);
  };

  const animateProgress = (targetProgress: number) => {
    let current = processingProgress;
    const increment = (targetProgress - current) / 20;
    const timer = setInterval(() => {
      current += increment;
      setProcessingProgress(current);
      if (current >= targetProgress) {
        clearInterval(timer);
      }
    }, 50);
  };

  return (
    <VoicePermissionsProvider>
      <div className="min-h-screen bg-jorge-gradient-dark">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-5">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,82,255,0.1)_0%,transparent_50%)]" />
        </div>

        <div className="relative z-10 container mx-auto px-4 py-8">
          {!showDemo ? (
            /* Demo Introduction */
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-4xl mx-auto text-center"
            >
              <div className="space-y-8">
                {/* Hero Section */}
                <div className="space-y-6">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2 }}
                    className="w-24 h-24 mx-auto rounded-full bg-jorge-electric/20 border border-jorge-electric/30 flex items-center justify-center"
                  >
                    <MicrophoneIcon className="w-12 h-12 text-jorge-electric" />
                  </motion.div>

                  <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 }}
                    className="text-4xl font-bold jorge-heading text-white"
                  >
                    Jorge's Voice Notes System
                  </motion.h1>

                  <motion.p
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4 }}
                    className="text-xl text-gray-300 max-w-2xl mx-auto"
                  >
                    Professional voice recording system for real estate professionals.
                    Capture field observations, client feedback, and property insights hands-free.
                  </motion.p>
                </div>

                {/* Feature Grid */}
                <motion.div
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 }}
                  className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12"
                >
                  <div className="jorge-glass p-6 rounded-xl text-center">
                    <SpeakerWaveIcon className="w-8 h-8 text-jorge-electric mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-white mb-2">
                      Real-Time Speech-to-Text
                    </h3>
                    <p className="text-sm text-gray-400">
                      High-accuracy transcription with real estate terminology recognition
                    </p>
                  </div>

                  <div className="jorge-glass p-6 rounded-xl text-center">
                    <SparklesIcon className="w-8 h-8 text-jorge-gold mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-white mb-2">
                      Smart Categorization
                    </h3>
                    <p className="text-sm text-gray-400">
                      AI-powered categorization and action item extraction
                    </p>
                  </div>

                  <div className="jorge-glass p-6 rounded-xl text-center">
                    <DocumentTextIcon className="w-8 h-8 text-jorge-glow mx-auto mb-4" />
                    <h3 className="text-lg font-semibold text-white mb-2">
                      Voice Commands
                    </h3>
                    <p className="text-sm text-gray-400">
                      Hands-free navigation and control for field work
                    </p>
                  </div>
                </motion.div>

                {/* Demo Button */}
                <motion.div
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.6 }}
                  className="mt-12"
                >
                  <button
                    onClick={handleDemoStart}
                    className="px-8 py-4 bg-jorge-electric/20 border border-jorge-electric/30 rounded-xl text-jorge-electric font-semibold text-lg hover:bg-jorge-electric/30 transition-all duration-200 jorge-haptic"
                  >
                    Experience Voice Notes Demo
                  </button>
                </motion.div>

                {/* Technical Specs */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.7 }}
                  className="mt-16 jorge-glass p-6 rounded-xl"
                >
                  <h3 className="text-lg font-semibold text-white mb-4">
                    Technical Specifications
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                    <div>
                      <div className="text-xl font-bold text-jorge-electric">95%+</div>
                      <div className="text-xs text-gray-400">Recognition Accuracy</div>
                    </div>
                    <div>
                      <div className="text-xl font-bold text-jorge-gold">~100ms</div>
                      <div className="text-xs text-gray-400">Response Latency</div>
                    </div>
                    <div>
                      <div className="text-xl font-bold text-jorge-glow">Offline</div>
                      <div className="text-xs text-gray-400">Capable</div>
                    </div>
                    <div>
                      <div className="text-xl font-bold text-jorge-steel">PWA</div>
                      <div className="text-xs text-gray-400">Ready</div>
                    </div>
                  </div>
                </motion.div>
              </div>
            </motion.div>
          ) : (
            /* Interactive Demo */
            <div className="max-w-4xl mx-auto">
              {/* Demo Header */}
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-between mb-8"
              >
                <div>
                  <h1 className="text-2xl font-bold jorge-heading text-white">
                    Voice Notes Demo
                  </h1>
                  <p className="text-gray-400 jorge-code">
                    Interactive demonstration of Jorge's voice recording system
                  </p>
                </div>

                <button
                  onClick={() => setShowDemo(false)}
                  className="px-4 py-2 bg-gray-500/20 border border-gray-500/30 rounded-lg text-gray-300 jorge-haptic"
                >
                  Back to Overview
                </button>
              </motion.div>

              {/* Demo Navigation */}
              <div className="flex gap-2 mb-6">
                {[
                  { id: 'recorder', name: 'Voice Recorder', icon: MicrophoneIcon },
                  { id: 'list', name: 'Notes List', icon: DocumentTextIcon },
                  { id: 'commands', name: 'Voice Commands', icon: SpeakerWaveIcon },
                ].map(({ id, name, icon: Icon }) => (
                  <button
                    key={id}
                    onClick={() => setCurrentDemo(id as any)}
                    className={`
                      flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200
                      ${currentDemo === id
                        ? 'bg-jorge-electric/20 border border-jorge-electric/30 text-jorge-electric'
                        : 'bg-white/5 border border-white/10 text-gray-400 hover:bg-white/10'
                      }
                    `}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="text-sm jorge-code">{name}</span>
                  </button>
                ))}
              </div>

              {/* Demo Content */}
              <div className="space-y-6">
                {currentDemo === 'recorder' && (
                  <motion.div
                    key="recorder"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                  >
                    <VoiceRecorder
                      isRecording={processingStage === 'recording'}
                      isProcessing={processingStage !== 'recording' && processingStage !== 'complete'}
                      currentNote={null}
                      onToggleRecording={() => simulateProcessing()}
                    />
                  </motion.div>
                )}

                {currentDemo === 'list' && (
                  <motion.div
                    key="list"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                  >
                    <VoiceNotesList
                      notes={demoVoiceNotes}
                      onDeleteNote={() => {}}
                      onExportNote={() => {}}
                    />
                  </motion.div>
                )}

                {currentDemo === 'commands' && (
                  <motion.div
                    key="commands"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                  >
                    <VoiceCommands
                      isListening={false}
                      isRecording={false}
                    />
                  </motion.div>
                )}
              </div>
            </div>
          )}

          {/* Processing Indicator (for demo) */}
          <VoiceProcessingIndicator
            isVisible={showDemo && processingStage !== 'complete'}
            processingStage={processingStage}
            progress={processingProgress}
          />
        </div>
      </div>
    </VoicePermissionsProvider>
  );
}