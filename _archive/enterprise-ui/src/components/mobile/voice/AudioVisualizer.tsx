'use client';

import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";

interface AudioVisualizerProps {
  isRecording: boolean;
  audioLevel: number;
  isProcessing?: boolean;
}

export function AudioVisualizer({
  isRecording,
  audioLevel,
  isProcessing = false,
}: AudioVisualizerProps) {
  const [audioData, setAudioData] = useState<number[]>([]);
  const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);

  // Generate realistic audio visualization data
  useEffect(() => {
    let animationFrame: number;

    const updateAudioData = () => {
      if (isRecording) {
        // Generate realistic audio visualization bars
        const newData = Array.from({ length: 20 }, () => {
          const base = Math.random() * 0.7;
          const spike = Math.random() < 0.1 ? Math.random() * 0.3 : 0;
          return Math.min(base + spike + audioLevel * 0.5, 1);
        });
        setAudioData(newData);
      } else if (isProcessing) {
        // Gentle processing animation
        const newData = Array.from({ length: 20 }, (_, i) => {
          const wave = Math.sin(Date.now() * 0.005 + i * 0.3) * 0.3 + 0.3;
          return Math.max(0.1, wave);
        });
        setAudioData(newData);
      } else {
        // Fade to silent state
        setAudioData(prev => prev.map(val => Math.max(0, val - 0.05)));
      }

      animationFrame = requestAnimationFrame(updateAudioData);
    };

    updateAudioData();
    return () => cancelAnimationFrame(animationFrame);
  }, [isRecording, isProcessing, audioLevel]);

  return (
    <div className="relative">
      {/* Main Audio Bars */}
      <div className="flex items-end justify-center gap-1 h-24 px-4">
        {audioData.map((level, index) => (
          <motion.div
            key={index}
            className={`
              w-2 rounded-full transition-colors duration-300
              ${isRecording
                ? level > 0.7
                  ? 'bg-red-500'
                  : level > 0.4
                    ? 'bg-jorge-electric'
                    : 'bg-jorge-electric/50'
                : isProcessing
                  ? 'bg-jorge-gold/70'
                  : 'bg-gray-600/30'
              }
            `}
            animate={{
              height: `${8 + level * 60}px`,
            }}
            transition={{
              duration: 0.1,
              ease: "easeOut",
            }}
          />
        ))}
      </div>

      {/* Background Glow Effect */}
      <AnimatePresence>
        {isRecording && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute inset-0 bg-gradient-radial from-jorge-electric/20 via-transparent to-transparent blur-xl"
          />
        )}
      </AnimatePresence>

      {/* Frequency Bands Overlay */}
      {isRecording && (
        <div className="absolute inset-0 pointer-events-none">
          <div className="flex items-center justify-center h-full">
            <motion.div
              animate={{
                scale: [1, 1.1, 1],
                opacity: [0.3, 0.6, 0.3],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: "easeInOut",
              }}
              className="w-32 h-8 bg-gradient-to-r from-transparent via-jorge-electric/10 to-transparent rounded-full"
            />
          </div>
        </div>
      )}

      {/* Audio Level Indicator */}
      <div className="flex justify-center mt-2">
        <div className="flex items-center gap-1">
          {[0, 1, 2, 3, 4].map((level) => (
            <div
              key={level}
              className={`
                w-2 h-1 rounded-full transition-all duration-150
                ${audioLevel * 5 > level
                  ? level < 3
                    ? 'bg-jorge-electric'
                    : level < 4
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  : 'bg-gray-600/50'
                }
              `}
            />
          ))}
        </div>
      </div>

      {/* Processing Overlay */}
      <AnimatePresence>
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/20 backdrop-blur-sm rounded-lg flex items-center justify-center"
          >
            <div className="flex items-center gap-2">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                className="w-6 h-6 border-2 border-jorge-gold border-t-transparent rounded-full"
              />
              <span className="text-sm jorge-code text-jorge-gold">
                Analyzing audio...
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Real-time Audio Stats */}
      {isRecording && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3 grid grid-cols-3 gap-2 text-center"
        >
          <div className="space-y-1">
            <div className="text-xs jorge-code text-gray-400">LEVEL</div>
            <div className="text-sm font-mono text-jorge-electric">
              {Math.round(audioLevel * 100)}%
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs jorge-code text-gray-400">FREQ</div>
            <div className="text-sm font-mono text-jorge-electric">
              {isRecording ? '~2.4kHz' : '--'}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs jorge-code text-gray-400">QUALITY</div>
            <div className="text-sm font-mono text-jorge-electric">
              {audioLevel > 0.6 ? 'HIGH' : audioLevel > 0.3 ? 'MED' : 'LOW'}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}