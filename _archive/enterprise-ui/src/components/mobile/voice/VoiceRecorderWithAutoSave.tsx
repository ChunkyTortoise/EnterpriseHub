/**
 * Jorge Real Estate AI Platform - Voice Recorder with Auto-Save
 * Enhanced VoiceRecorder component with comprehensive offline protection
 *
 * Features:
 * - Auto-save voice notes every 3 seconds during recording
 * - Instant save on recording completion
 * - Transcript auto-save as it's generated
 * - Visual feedback for save status
 * - Offline resilience with sync on reconnect
 */

'use client';

import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect, useCallback } from "react";
import {
  MicrophoneIcon,
  StopIcon,
  PauseIcon,
  PlayIcon,
  ArrowPathIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

import { AudioVisualizer } from "./AudioVisualizer";
import { TranscriptionDisplay } from "./TranscriptionDisplay";
import { AutoSaveIndicator, FieldSaveIndicator, AutoSaveToast } from "@/components/mobile/AutoSaveIndicator";
import { useVoiceNoteAutoSave } from "@/hooks/useAutoSave";
import { VoiceNote } from "@/types/voice";

interface VoiceRecorderWithAutoSaveProps {
  isRecording: boolean;
  isProcessing: boolean;
  currentNote: VoiceNote | null;
  onToggleRecording: () => void;
  onCancelRecording?: () => void;
  onVoiceNoteSaved?: (note: VoiceNote) => void;

  // Auto-save configuration
  propertyId?: string;
  leadId?: string;
  category?: string;
  location?: { lat: number; lng: number };
}

export function VoiceRecorderWithAutoSave({
  isRecording,
  isProcessing,
  currentNote,
  onToggleRecording,
  onCancelRecording,
  onVoiceNoteSaved,
  propertyId,
  leadId,
  category = 'showing_notes',
  location
}: VoiceRecorderWithAutoSaveProps) {
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [audioLevel, setAudioLevel] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [showToast, setShowToast] = useState(false);

  // Initialize auto-save with default note structure
  const initialNote: VoiceNote = {
    id: '',
    propertyId: propertyId || null,
    leadId: leadId || null,
    transcript: '',
    audioBlob: null,
    duration: 0,
    timestamp: Date.now(),
    location: location || null,
    category,
    confidence: 0,
    keywords: [],
    actionItems: [],
    sentiment: 'neutral',
    isProcessed: false,
    metadata: {
      deviceType: 'mobile',
      quality: 'high',
      format: 'webm',
      recordingMode: 'standard'
    }
  };

  // Auto-save hook for voice notes
  const [autoSaveState, autoSaveActions] = useVoiceNoteAutoSave(initialNote);

  // Update recording duration
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isRecording && !isPaused) {
      interval = setInterval(() => {
        setRecordingDuration(prev => {
          const newDuration = prev + 1;
          // Update auto-save data with duration
          autoSaveActions.updateData({ duration: newDuration });
          return newDuration;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording, isPaused, autoSaveActions]);

  // Reset duration when recording stops
  useEffect(() => {
    if (!isRecording) {
      setRecordingDuration(0);
    }
  }, [isRecording]);

  // Update auto-save data when currentNote changes
  useEffect(() => {
    if (currentNote) {
      autoSaveActions.updateData({
        ...currentNote,
        timestamp: currentNote.timestamp || Date.now(),
        location: location || currentNote.location,
        category: category || currentNote.category
      });

      // Trigger save on recording completion
      if (!isRecording && !isProcessing && currentNote.transcript) {
        handleRecordingComplete(currentNote);
      }
    }
  }, [currentNote, isRecording, isProcessing, location, category]);

  // Save immediately on recording completion
  const handleRecordingComplete = useCallback(async (note: VoiceNote) => {
    try {
      // Ensure we have complete data
      const completeNote: VoiceNote = {
        ...note,
        id: note.id || `voice_${Date.now()}`,
        timestamp: Date.now(),
        duration: recordingDuration,
        isProcessed: true,
        location: location || note.location,
        category: category || note.category
      };

      // Update and save immediately
      autoSaveActions.setData(completeNote);
      const saved = await autoSaveActions.saveNow();

      if (saved) {
        setShowToast(true);
        onVoiceNoteSaved?.(completeNote);
      }
    } catch (error) {
      console.error('Failed to save voice note:', error);
    }
  }, [recordingDuration, location, category, autoSaveActions, onVoiceNoteSaved]);

  // Handle recording state changes for auto-save
  useEffect(() => {
    if (isRecording) {
      // Start new recording - reset auto-save state
      const newNote: VoiceNote = {
        ...initialNote,
        id: `voice_${Date.now()}`,
        timestamp: Date.now(),
        propertyId: propertyId || null,
        leadId: leadId || null,
        category,
        location: location || null
      };
      autoSaveActions.setData(newNote);
    }
  }, [isRecording, propertyId, leadId, category, location]);

  // Handle transcription updates
  useEffect(() => {
    if (currentNote?.transcript && currentNote.transcript !== autoSaveState.data.transcript) {
      // Update transcript in auto-save (will trigger auto-save after interval)
      autoSaveActions.updateData({
        transcript: currentNote.transcript,
        confidence: currentNote.confidence || 0,
        keywords: currentNote.keywords || [],
        actionItems: currentNote.actionItems || []
      });
    }
  }, [currentNote?.transcript, currentNote?.confidence, autoSaveState.data.transcript, autoSaveActions]);

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

  const handleCancel = () => {
    setIsPaused(false);
    setRecordingDuration(0);
    autoSaveActions.resetData();
    onCancelRecording?.();
  };

  return (
    <>
      <motion.div
        layout
        className="jorge-glass p-6 rounded-xl relative"
      >
        {/* Auto-Save Indicator */}
        <div className="absolute top-4 right-4 z-10">
          <AutoSaveIndicator
            status={autoSaveState.status}
            lastSaved={autoSaveState.lastSaved}
            saveCount={autoSaveState.saveCount}
            error={autoSaveState.error}
            size="sm"
            position="inline"
          />
        </div>

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
              <div className="flex items-center gap-2">
                <p className={`text-sm font-medium ${getRecordingStateColor()}`}>
                  {getRecordingStateText()}
                </p>
                {(isRecording || autoSaveState.pendingChanges) && (
                  <FieldSaveIndicator status={autoSaveState.status} />
                )}
              </div>
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

        {/* Real-time Transcription with Save Status */}
        <AnimatePresence>
          {(isRecording || currentNote?.transcript || autoSaveState.data.transcript) && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-6"
            >
              <div className="relative">
                <TranscriptionDisplay
                  transcript={currentNote?.transcript || autoSaveState.data.transcript || ''}
                  confidence={currentNote?.confidence || autoSaveState.data.confidence || 0}
                  isLive={isRecording}
                />

                {/* Transcript Save Indicator */}
                {autoSaveState.data.transcript && (
                  <div className="absolute top-2 right-2">
                    <FieldSaveIndicator status={autoSaveState.status} />
                  </div>
                )}
              </div>
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
                onClick={() => {
                  setIsPaused(!isPaused);
                  // Trigger save when pausing (important moment)
                  if (!isPaused) {
                    autoSaveActions.saveNow();
                  }
                }}
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
                onClick={handleCancel}
                className="p-3 rounded-full bg-gray-500/20 border border-gray-500/30 jorge-haptic"
              >
                <XMarkIcon className="w-6 h-6 text-gray-400" />
              </motion.button>
            )}
          </div>
        </div>

        {/* Auto-Save Status Footer */}
        {autoSaveState.saveCount > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 text-xs text-gray-500 jorge-code text-center"
          >
            Auto-saved {autoSaveState.saveCount} time{autoSaveState.saveCount !== 1 ? 's' : ''}
            {autoSaveState.lastSaved && (
              <> • Last saved {Math.floor((Date.now() - autoSaveState.lastSaved) / 1000)}s ago</>
            )}
          </motion.div>
        )}
      </motion.div>

      {/* Success Toast */}
      <AnimatePresence>
        {showToast && (
          <AutoSaveToast
            status="saved"
            message="Voice note saved locally"
            onClose={() => setShowToast(false)}
            autoHide={3000}
          />
        )}
      </AnimatePresence>
    </>
  );
}