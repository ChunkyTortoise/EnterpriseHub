'use client';

import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import {
  MicrophoneIcon,
  SpeakerWaveIcon,
  CpuChipIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
} from "@heroicons/react/24/outline";

interface VoiceProcessingIndicatorProps {
  isVisible?: boolean;
  processingStage?: 'recording' | 'analyzing' | 'transcribing' | 'categorizing' | 'complete' | 'error';
  progress?: number;
  message?: string;
}

export function VoiceProcessingIndicator({
  isVisible = false,
  processingStage = 'recording',
  progress = 0,
  message,
}: VoiceProcessingIndicatorProps) {
  const [currentStage, setCurrentStage] = useState(processingStage);
  const [stageProgress, setStageProgress] = useState(0);

  useEffect(() => {
    setCurrentStage(processingStage);
  }, [processingStage]);

  useEffect(() => {
    // Animate progress changes
    const targetProgress = progress;
    const startProgress = stageProgress;
    const duration = 500; // 500ms animation
    const startTime = Date.now();

    const animateProgress = () => {
      const elapsed = Date.now() - startTime;
      const progressRatio = Math.min(elapsed / duration, 1);
      const easeOutQuad = 1 - Math.pow(1 - progressRatio, 2);

      const currentProgress = startProgress + (targetProgress - startProgress) * easeOutQuad;
      setStageProgress(currentProgress);

      if (progressRatio < 1) {
        requestAnimationFrame(animateProgress);
      }
    };

    requestAnimationFrame(animateProgress);
  }, [progress]);

  const getStageInfo = () => {
    switch (currentStage) {
      case 'recording':
        return {
          icon: MicrophoneIcon,
          title: 'Recording Audio',
          description: 'Capturing your voice note...',
          color: 'jorge-electric',
          bgColor: 'jorge-electric/10',
          borderColor: 'jorge-electric/30',
        };
      case 'analyzing':
        return {
          icon: CpuChipIcon,
          title: 'Analyzing Audio',
          description: 'Processing audio quality and detecting speech...',
          color: 'jorge-gold',
          bgColor: 'jorge-gold/10',
          borderColor: 'jorge-gold/30',
        };
      case 'transcribing':
        return {
          icon: SpeakerWaveIcon,
          title: 'Converting to Text',
          description: 'Converting speech to text using AI...',
          color: 'jorge-glow',
          bgColor: 'jorge-glow/10',
          borderColor: 'jorge-glow/30',
        };
      case 'categorizing':
        return {
          icon: CpuChipIcon,
          title: 'Smart Categorization',
          description: 'Extracting keywords and action items...',
          color: 'jorge-steel',
          bgColor: 'jorge-steel/10',
          borderColor: 'jorge-steel/30',
        };
      case 'complete':
        return {
          icon: CheckCircleIcon,
          title: 'Processing Complete',
          description: 'Voice note saved successfully',
          color: 'green-500',
          bgColor: 'green-500/10',
          borderColor: 'green-500/30',
        };
      case 'error':
        return {
          icon: ExclamationCircleIcon,
          title: 'Processing Error',
          description: 'Failed to process voice note',
          color: 'red-500',
          bgColor: 'red-500/10',
          borderColor: 'red-500/30',
        };
      default:
        return {
          icon: MicrophoneIcon,
          title: 'Ready',
          description: 'Voice processing ready',
          color: 'gray-400',
          bgColor: 'gray-400/10',
          borderColor: 'gray-400/30',
        };
    }
  };

  const stageInfo = getStageInfo();
  const Icon = stageInfo.icon;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -50, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -50, scale: 0.9 }}
          className="fixed top-4 left-4 right-4 z-50"
        >
          <motion.div
            layout
            className={`
              jorge-glass p-4 rounded-xl border
              bg-${stageInfo.bgColor} border-${stageInfo.borderColor}
              shadow-lg backdrop-blur-sm
            `}
          >
            <div className="flex items-center gap-3">
              {/* Stage Icon */}
              <motion.div
                animate={{
                  scale: currentStage === 'recording' ? [1, 1.1, 1] : 1,
                  rotate: currentStage === 'analyzing' || currentStage === 'transcribing' ? 360 : 0,
                }}
                transition={{
                  scale: {
                    repeat: currentStage === 'recording' ? Infinity : 0,
                    duration: 2,
                  },
                  rotate: {
                    repeat: currentStage === 'analyzing' || currentStage === 'transcribing' ? Infinity : 0,
                    duration: 2,
                    ease: "linear",
                  },
                }}
                className={`
                  p-2 rounded-lg
                  bg-${stageInfo.bgColor} border border-${stageInfo.borderColor}
                `}
              >
                <Icon className={`w-5 h-5 text-${stageInfo.color}`} />
              </motion.div>

              {/* Stage Info */}
              <div className="flex-1 min-w-0">
                <motion.h4
                  layout
                  className={`text-sm font-semibold text-${stageInfo.color} jorge-heading`}
                >
                  {stageInfo.title}
                </motion.h4>
                <motion.p
                  layout
                  className="text-xs text-gray-400 jorge-code"
                >
                  {message || stageInfo.description}
                </motion.p>
              </div>

              {/* Progress Indicator */}
              {(currentStage === 'analyzing' || currentStage === 'transcribing' || currentStage === 'categorizing') && (
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 relative">
                    <svg className="w-8 h-8 transform -rotate-90" viewBox="0 0 32 32">
                      <circle
                        cx="16"
                        cy="16"
                        r="12"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        className="text-gray-600"
                      />
                      <circle
                        cx="16"
                        cy="16"
                        r="12"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeDasharray={`${2 * Math.PI * 12}`}
                        strokeDashoffset={`${2 * Math.PI * 12 * (1 - stageProgress / 100)}`}
                        className={`text-${stageInfo.color} transition-all duration-500 ease-out`}
                        strokeLinecap="round"
                      />
                    </svg>
                  </div>
                  <span className={`text-xs font-mono text-${stageInfo.color}`}>
                    {Math.round(stageProgress)}%
                  </span>
                </div>
              )}

              {/* Success/Error Indicators */}
              {currentStage === 'complete' && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center"
                >
                  <CheckCircleIcon className="w-5 h-5 text-green-500" />
                </motion.div>
              )}

              {currentStage === 'error' && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center"
                >
                  <ExclamationCircleIcon className="w-5 h-5 text-red-500" />
                </motion.div>
              )}

              {/* Recording Level Indicator */}
              {currentStage === 'recording' && (
                <div className="flex items-center gap-1">
                  {[1, 2, 3, 4, 5].map((level) => (
                    <motion.div
                      key={level}
                      animate={{
                        height: [4, 8, 12, 8, 4],
                        opacity: [0.3, 1, 1, 1, 0.3],
                      }}
                      transition={{
                        repeat: Infinity,
                        duration: 1.5,
                        delay: level * 0.1,
                      }}
                      className="w-1 bg-jorge-electric rounded-full"
                      style={{ height: '4px' }}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* Progress Bar */}
            {(currentStage === 'analyzing' || currentStage === 'transcribing' || currentStage === 'categorizing') && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-3"
              >
                <div className="w-full bg-gray-700 rounded-full h-1.5 overflow-hidden">
                  <motion.div
                    className={`h-full bg-${stageInfo.color} rounded-full`}
                    style={{ width: `${stageProgress}%` }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                  />
                </div>
              </motion.div>
            )}

            {/* Real-time Stats for Recording */}
            {currentStage === 'recording' && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-3 pt-3 border-t border-white/10"
              >
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-xs text-gray-400 jorge-code">QUALITY</div>
                    <div className="text-sm font-mono text-jorge-electric">95%</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-400 jorge-code">LEVEL</div>
                    <div className="text-sm font-mono text-jorge-electric">-12dB</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-400 jorge-code">TIME</div>
                    <div className="text-sm font-mono text-jorge-electric">0:42</div>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Processing Stats */}
            {(currentStage === 'transcribing' || currentStage === 'categorizing') && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-3 pt-3 border-t border-white/10"
              >
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-xs text-gray-400 jorge-code">CONFIDENCE</div>
                    <div className="text-sm font-mono text-jorge-gold">94%</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-400 jorge-code">WORDS</div>
                    <div className="text-sm font-mono text-jorge-gold">127</div>
                  </div>
                </div>
              </motion.div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}