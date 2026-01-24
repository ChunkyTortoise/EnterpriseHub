'use client';

import { motion } from "framer-motion";
import { Suspense } from "react";
import { VoiceRecorder } from "@/components/mobile/voice/VoiceRecorder";
import { VoiceNotesList } from "@/components/mobile/voice/VoiceNotesList";
import { VoiceCommands } from "@/components/mobile/voice/VoiceCommands";
import { useVoiceRecording } from "@/hooks/useVoiceRecording";
import {
  MicrophoneIcon,
  SpeakerWaveIcon,
  Cog6ToothIcon,
} from "@heroicons/react/24/outline";

export default function VoiceNotesPage() {
  const {
    isRecording,
    isProcessing,
    currentNote,
    voiceNotes,
    isListening,
    toggleRecording,
    deleteNote,
    exportNote,
  } = useVoiceRecording();

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div className="space-y-1">
          <h1 className="text-2xl font-bold jorge-heading text-jorge-electric">
            Voice Notes
          </h1>
          <p className="text-sm text-gray-400 jorge-code">
            Capture field insights hands-free
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Real-time status indicator */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-black/30 border border-white/10">
            <div className={`w-2 h-2 rounded-full transition-all duration-300 ${
              isRecording
                ? 'bg-red-500 animate-pulse'
                : isListening
                  ? 'bg-jorge-electric jorge-glow-pulse'
                  : 'bg-gray-500'
            }`} />
            <span className="text-xs jorge-code text-gray-300">
              {isRecording ? 'REC' : isListening ? 'LISTENING' : 'READY'}
            </span>
          </div>

          {/* Settings button */}
          <motion.button
            whileTap={{ scale: 0.95 }}
            className="p-2 rounded-lg bg-white/10 jorge-haptic"
          >
            <Cog6ToothIcon className="w-5 h-5 text-gray-400" />
          </motion.button>
        </div>
      </motion.div>

      {/* Voice Commands Panel */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
      >
        <Suspense fallback={<VoiceCommandsLoading />}>
          <VoiceCommands
            isListening={isListening}
            isRecording={isRecording}
          />
        </Suspense>
      </motion.div>

      {/* Main Voice Recorder */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Suspense fallback={<VoiceRecorderLoading />}>
          <VoiceRecorder
            isRecording={isRecording}
            isProcessing={isProcessing}
            currentNote={currentNote}
            onToggleRecording={toggleRecording}
          />
        </Suspense>
      </motion.div>

      {/* Voice Notes List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="space-y-4"
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold jorge-heading text-white">
            Recent Notes
          </h2>
          <span className="text-sm text-gray-400 jorge-code">
            {voiceNotes.length} notes
          </span>
        </div>

        <Suspense fallback={<VoiceNotesLoading />}>
          <VoiceNotesList
            notes={voiceNotes}
            onDeleteNote={deleteNote}
            onExportNote={exportNote}
          />
        </Suspense>
      </motion.div>

      {/* Quick Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="grid grid-cols-3 gap-4"
      >
        <div className="jorge-glass p-4 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <MicrophoneIcon className="w-4 h-4 text-jorge-electric" />
            <span className="text-xs jorge-code text-gray-400">TODAY</span>
          </div>
          <div className="text-lg font-bold text-white">
            {voiceNotes.filter(note =>
              new Date(note.timestamp).toDateString() === new Date().toDateString()
            ).length}
          </div>
          <div className="text-xs text-gray-500">Notes</div>
        </div>

        <div className="jorge-glass p-4 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <SpeakerWaveIcon className="w-4 h-4 text-jorge-gold" />
            <span className="text-xs jorge-code text-gray-400">ACCURACY</span>
          </div>
          <div className="text-lg font-bold text-white">94%</div>
          <div className="text-xs text-gray-500">Recognition</div>
        </div>

        <div className="jorge-glass p-4 rounded-xl">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-4 h-4 bg-jorge-glow rounded-full" />
            <span className="text-xs jorge-code text-gray-400">TIME</span>
          </div>
          <div className="text-lg font-bold text-white">
            {Math.round(voiceNotes.reduce((acc, note) => acc + note.duration, 0) / 60)}m
          </div>
          <div className="text-xs text-gray-500">Total</div>
        </div>
      </motion.div>

      {/* Bottom spacing for mobile nav */}
      <div className="h-24" />
    </div>
  );
}

// Loading components
function VoiceCommandsLoading() {
  return (
    <div className="jorge-glass p-4 rounded-xl animate-pulse">
      <div className="h-4 bg-white/10 rounded mb-3" />
      <div className="grid grid-cols-2 gap-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-8 bg-white/5 rounded" />
        ))}
      </div>
    </div>
  );
}

function VoiceRecorderLoading() {
  return (
    <div className="jorge-glass p-6 rounded-xl animate-pulse">
      <div className="flex flex-col items-center space-y-4">
        <div className="w-20 h-20 bg-white/10 rounded-full" />
        <div className="h-4 w-32 bg-white/10 rounded" />
        <div className="h-8 w-24 bg-white/5 rounded-full" />
      </div>
    </div>
  );
}

function VoiceNotesLoading() {
  return (
    <div className="space-y-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="jorge-glass p-4 rounded-xl animate-pulse">
          <div className="flex items-start justify-between mb-2">
            <div className="h-4 w-32 bg-white/10 rounded" />
            <div className="h-4 w-16 bg-white/10 rounded" />
          </div>
          <div className="space-y-2">
            <div className="h-3 w-full bg-white/5 rounded" />
            <div className="h-3 w-3/4 bg-white/5 rounded" />
          </div>
          <div className="flex items-center gap-2 mt-3">
            <div className="h-6 w-16 bg-white/5 rounded-full" />
            <div className="h-6 w-20 bg-white/5 rounded-full" />
          </div>
        </div>
      ))}
    </div>
  );
}