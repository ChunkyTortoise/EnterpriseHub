'use client';

import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import {
  MicrophoneIcon,
  StopIcon,
  PauseIcon,
  PlayIcon,
  ArrowPathIcon,
} from "@heroicons/react/24/outline";
import { AudioVisualizer } from "./AudioVisualizer";
import { TranscriptionDisplay } from "./TranscriptionDisplay";
import { VoiceNote } from "@/types/voice";

interface VoiceRecorderProps {
  isRecording: boolean;
  isProcessing: boolean;
  currentNote: VoiceNote | null;
  onToggleRecording: () => void;
}

export function VoiceRecorder({
  isRecording,
  isProcessing,
  currentNote,
  onToggleRecording,
}: VoiceRecorderProps) {
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  // Update recording duration
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isRecording && !isPaused) {
      interval = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording, isPaused]);

  // Reset duration when recording stops
  useEffect(() => {
    if (!isRecording) {
      setRecordingDuration(0);
    }
  }, [isRecording]);

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getRecordingStateText = () => {
    if (isProcessing) return "Processing...";
    if (isRecording && isPaused) return "Paused";
    if (isRecording) return "Recording";
    return "Ready to record";
  };

  const getRecordingStateColor = () => {
    if (isProcessing) return "text-jorge-gold";
    if (isRecording && isPaused) return "text-yellow-500";
    if (isRecording) return "text-red-500";
    return "text-gray-400";
  };

  return (
    <motion.div
      layout
      className="jorge-glass p-6 rounded-xl"
    >
      {/* Recording Status Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <motion.div
            animate={{
              scale: isRecording ? [1, 1.2, 1] : 1,
            }}
            transition={{
              repeat: isRecording ? Infinity : 0,
              duration: 2,
            }}
            className={`w-3 h-3 rounded-full ${
              isRecording
                ? 'bg-red-500'
                : isProcessing
                  ? 'bg-jorge-gold'
                  : 'bg-gray-500'
            }`}
          />
          <div>
            <p className={`text-sm font-medium ${getRecordingStateColor()}`}>
              {getRecordingStateText()}
            </p>
            <p className="text-xs text-gray-500 jorge-code">
              {isRecording ? formatDuration(recordingDuration) : 'Tap to start'}
            </p>
          </div>
        </div>

        {isRecording && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-1"
          >
            <div className="text-xs jorge-code text-gray-400">REC</div>
            <motion.div
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
              className="w-2 h-2 rounded-full bg-red-500"
            />
          </motion.div>
        )}
      </div>

      {/* Audio Visualizer */}
      <div className="mb-6">
        <AudioVisualizer
          isRecording={isRecording}
          audioLevel={audioLevel}
          isProcessing={isProcessing}
        />
      </div>

      {/* Real-time Transcription */}
      <AnimatePresence>
        {(isRecording || currentNote?.transcript) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6"
          >
            <TranscriptionDisplay
              transcript={currentNote?.transcript || ''}
              confidence={currentNote?.confidence || 0}
              isLive={isRecording}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Recording Controls */}
      <div className="flex items-center justify-center">
        <div className="flex items-center gap-4">
          {/* Pause/Resume Button (only when recording) */}
          {isRecording && (
            <motion.button
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => setIsPaused(!isPaused)}
              className="p-3 rounded-full bg-yellow-500/20 border border-yellow-500/30 jorge-haptic"
            >
              {isPaused ? (
                <PlayIcon className="w-6 h-6 text-yellow-500" />
              ) : (
                <PauseIcon className="w-6 h-6 text-yellow-500" />
              )}
            </motion.button>
          )}

          {/* Main Record/Stop Button */}
          <motion.button
            whileTap={{ scale: 0.95 }}
            whileHover={{ scale: 1.02 }}
            onClick={onToggleRecording}
            disabled={isProcessing}
            className={`
              relative p-6 rounded-full transition-all duration-300
              ${isRecording
                ? 'bg-red-500/20 border-2 border-red-500 shadow-red-500/20'
                : 'bg-jorge-electric/20 border-2 border-jorge-electric shadow-jorge-electric/20'
              }
              disabled:opacity-50 disabled:cursor-not-allowed
              shadow-2xl jorge-haptic
            `}
          >
            {isProcessing ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                <ArrowPathIcon className="w-8 h-8 text-jorge-gold" />
              </motion.div>
            ) : isRecording ? (
              <StopIcon className="w-8 h-8 text-red-500" />
            ) : (
              <MicrophoneIcon className="w-8 h-8 text-jorge-electric" />
            )}

            {/* Pulsing ring for recording state */}
            {isRecording && !isPaused && (
              <motion.div
                animate={{
                  scale: [1, 1.3, 1],
                  opacity: [0.5, 0, 0.5],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                className="absolute inset-0 rounded-full border-2 border-red-500"
              />
            )}

            {/* Glow effect */}
            <div className={`
              absolute inset-0 rounded-full blur-xl transition-opacity duration-300
              ${isRecording
                ? 'bg-red-500/30 opacity-100'
                : 'bg-jorge-electric/30 opacity-60'
              }
            `} />
          </motion.button>

          {/* Cancel Button (only when recording) */}
          {isRecording && (
            <motion.button
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              whileTap={{ scale: 0.9 }}
              onClick={() => {
                setRecordingDuration(0);
                setIsPaused(false);
                // Add cancel logic
              }}
              className="p-3 rounded-full bg-gray-500/20 border border-gray-500/30 jorge-haptic"
            >
              <StopIcon className="w-6 h-6 text-gray-500" />
            </motion.button>
          )}
        </div>
      </div>

      {/* Voice Commands Hint */}
      {!isRecording && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="text-center mt-4"
        >
          <p className="text-xs text-gray-500 jorge-code">
            Say "Start recording" or tap the microphone
          </p>
        </motion.div>
      )}

      {/* Current Note Category */}
      {currentNote?.category && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mt-4 flex justify-center"
        >
          <div className="px-3 py-1 rounded-full bg-jorge-electric/20 border border-jorge-electric/30">
            <span className="text-xs jorge-code text-jorge-electric">
              {currentNote.category.replace('_', ' ').toUpperCase()}
            </span>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}