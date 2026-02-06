'use client';

import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import {
  PlayIcon,
  PauseIcon,
  ShareIcon,
  TrashIcon,
  DocumentDuplicateIcon,
  TagIcon,
  MapPinIcon,
  ClockIcon,
  SpeakerWaveIcon,
  EllipsisVerticalIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";
import { VoiceNote } from "@/types/voice";

interface VoiceNotesListProps {
  notes: VoiceNote[];
  onDeleteNote: (id: string) => void;
  onExportNote: (id: string, format: 'text' | 'audio') => void;
  onPlayNote?: (id: string) => void;
}

export function VoiceNotesList({
  notes,
  onDeleteNote,
  onExportNote,
  onPlayNote,
}: VoiceNotesListProps) {
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  // Sort notes by timestamp (newest first)
  const sortedNotes = [...notes].sort((a, b) => b.timestamp - a.timestamp);

  // Filter by category
  const filteredNotes = selectedCategory === 'all'
    ? sortedNotes
    : sortedNotes.filter(note => note.category === selectedCategory);

  // Group notes by date
  const groupedNotes = filteredNotes.reduce((groups, note) => {
    const date = new Date(note.timestamp).toDateString();
    if (!groups[date]) {
      groups[date] = [];
    }
    groups[date].push(note);
    return groups;
  }, {} as Record<string, VoiceNote[]>);

  const categories = [
    { id: 'all', name: 'All Notes', color: 'gray-400' },
    { id: 'property_features', name: 'Property', color: 'jorge-gold' },
    { id: 'client_feedback', name: 'Client', color: 'jorge-glow' },
    { id: 'follow_up_tasks', name: 'Tasks', color: 'jorge-steel' },
    { id: 'market_observations', name: 'Market', color: 'jorge-electric' },
    { id: 'showing_notes', name: 'Showings', color: 'green-400' },
    { id: 'personal_memo', name: 'Personal', color: 'purple-400' },
  ];

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'property_features': return '🏠';
      case 'client_feedback': return '👥';
      case 'follow_up_tasks': return '📋';
      case 'market_observations': return '📊';
      case 'showing_notes': return '🗝️';
      case 'personal_memo': return '📝';
      default: return '🎙️';
    }
  };

  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-500';
    if (confidence >= 0.7) return 'text-yellow-500';
    return 'text-red-500';
  };

  const handlePlayPause = (noteId: string) => {
    if (playingId === noteId) {
      setPlayingId(null);
    } else {
      setPlayingId(noteId);
      onPlayNote?.(noteId);
    }
  };

  const handleCopyTranscript = async (transcript: string) => {
    try {
      await navigator.clipboard.writeText(transcript);
      // Show success feedback
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  if (notes.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="jorge-glass p-8 rounded-xl text-center"
      >
        <SpeakerWaveIcon className="w-12 h-12 text-gray-500 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-white mb-2">
          No Voice Notes Yet
        </h3>
        <p className="text-gray-400 text-sm mb-4">
          Start recording to capture your field observations and insights
        </p>
        <button className="px-4 py-2 bg-jorge-electric/20 border border-jorge-electric/30 rounded-lg text-jorge-electric text-sm jorge-haptic">
          Start Recording
        </button>
      </motion.div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Category Filter */}
      <div className="flex gap-2 overflow-x-auto scrollbar-hide">
        {categories.map((category) => {
          const isActive = selectedCategory === category.id;
          const categoryCount = category.id === 'all'
            ? notes.length
            : notes.filter(note => note.category === category.id).length;

          return (
            <motion.button
              key={category.id}
              whileTap={{ scale: 0.95 }}
              onClick={() => setSelectedCategory(category.id)}
              className={`
                flex items-center gap-2 px-3 py-2 rounded-lg whitespace-nowrap
                transition-all duration-200 jorge-haptic
                ${isActive
                  ? 'bg-jorge-electric/20 border border-jorge-electric/30 text-jorge-electric'
                  : 'bg-white/5 border border-white/10 text-gray-400 hover:bg-white/10'
                }
              `}
            >
              <span className="text-sm jorge-code">{category.name}</span>
              {categoryCount > 0 && (
                <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                  isActive ? 'bg-jorge-electric/30' : 'bg-white/20'
                }`}>
                  {categoryCount}
                </span>
              )}
            </motion.button>
          );
        })}
      </div>

      {/* Notes List */}
      <div className="space-y-6">
        <AnimatePresence mode="popLayout">
          {Object.entries(groupedNotes).map(([date, dayNotes]) => (
            <motion.div
              key={date}
              layout
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-3"
            >
              {/* Date Header */}
              <div className="flex items-center gap-3">
                <h3 className="text-sm font-medium text-gray-300 jorge-code">
                  {date === new Date().toDateString() ? 'TODAY' : date.toUpperCase()}
                </h3>
                <div className="flex-1 h-px bg-gradient-to-r from-white/20 to-transparent" />
                <span className="text-xs text-gray-500 jorge-code">
                  {dayNotes.length} {dayNotes.length === 1 ? 'note' : 'notes'}
                </span>
              </div>

              {/* Notes for this date */}
              <div className="space-y-3">
                {dayNotes.map((note, index) => {
                  const isExpanded = expandedId === note.id;
                  const isPlaying = playingId === note.id;

                  return (
                    <motion.div
                      key={note.id}
                      layout
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="jorge-glass p-4 rounded-xl border border-white/10 hover:border-white/20 transition-all duration-200"
                    >
                      {/* Note Header */}
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-start gap-3 flex-1">
                          {/* Category Icon */}
                          <div className="text-lg">
                            {getCategoryIcon(note.category)}
                          </div>

                          {/* Note Info */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-sm font-medium text-white">
                                {note.category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                              </span>
                              {note.location && (
                                <div className="flex items-center gap-1 text-gray-400">
                                  <MapPinIcon className="w-3 h-3" />
                                  <span className="text-xs jorge-code">GPS</span>
                                </div>
                              )}
                            </div>

                            <div className="flex items-center gap-3 text-xs text-gray-400 jorge-code">
                              <div className="flex items-center gap-1">
                                <ClockIcon className="w-3 h-3" />
                                <span>{formatTimestamp(note.timestamp)}</span>
                              </div>
                              <div className="flex items-center gap-1">
                                <SpeakerWaveIcon className="w-3 h-3" />
                                <span>{formatDuration(note.duration)}</span>
                              </div>
                              <div className={`flex items-center gap-1 ${getConfidenceColor(note.confidence)}`}>
                                {note.confidence >= 0.9 ? (
                                  <CheckCircleIcon className="w-3 h-3" />
                                ) : (
                                  <ExclamationTriangleIcon className="w-3 h-3" />
                                )}
                                <span>{Math.round(note.confidence * 100)}%</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Actions Menu */}
                        <div className="flex items-center gap-1">
                          <motion.button
                            whileTap={{ scale: 0.9 }}
                            onClick={() => setExpandedId(isExpanded ? null : note.id)}
                            className="p-2 rounded-lg bg-white/10 jorge-haptic"
                          >
                            <EllipsisVerticalIcon className="w-4 h-4 text-gray-400" />
                          </motion.button>
                        </div>
                      </div>

                      {/* Transcript Preview */}
                      <div className="mb-3">
                        <p className="text-sm text-gray-200 leading-relaxed line-clamp-2">
                          {note.transcript || 'No transcript available'}
                        </p>
                      </div>

                      {/* Keywords */}
                      {note.keywords.length > 0 && (
                        <div className="mb-3">
                          <div className="flex flex-wrap gap-1">
                            {note.keywords.slice(0, 3).map((keyword) => (
                              <span
                                key={keyword}
                                className="px-2 py-1 text-xs bg-jorge-electric/10 border border-jorge-electric/30 rounded-full text-jorge-electric"
                              >
                                {keyword}
                              </span>
                            ))}
                            {note.keywords.length > 3 && (
                              <span className="px-2 py-1 text-xs bg-gray-500/20 rounded-full text-gray-400">
                                +{note.keywords.length - 3} more
                              </span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex items-center gap-2">
                        <motion.button
                          whileTap={{ scale: 0.95 }}
                          onClick={() => handlePlayPause(note.id)}
                          className="flex items-center gap-2 px-3 py-2 bg-jorge-electric/20 border border-jorge-electric/30 rounded-lg text-jorge-electric jorge-haptic"
                        >
                          {isPlaying ? (
                            <PauseIcon className="w-4 h-4" />
                          ) : (
                            <PlayIcon className="w-4 h-4" />
                          )}
                          <span className="text-sm">Play</span>
                        </motion.button>

                        <motion.button
                          whileTap={{ scale: 0.95 }}
                          onClick={() => handleCopyTranscript(note.transcript)}
                          className="p-2 bg-white/10 rounded-lg jorge-haptic"
                        >
                          <DocumentDuplicateIcon className="w-4 h-4 text-gray-400" />
                        </motion.button>

                        <motion.button
                          whileTap={{ scale: 0.95 }}
                          onClick={() => onExportNote(note.id, 'text')}
                          className="p-2 bg-white/10 rounded-lg jorge-haptic"
                        >
                          <ShareIcon className="w-4 h-4 text-gray-400" />
                        </motion.button>

                        <motion.button
                          whileTap={{ scale: 0.95 }}
                          onClick={() => onDeleteNote(note.id)}
                          className="p-2 bg-red-500/20 rounded-lg jorge-haptic"
                        >
                          <TrashIcon className="w-4 h-4 text-red-400" />
                        </motion.button>
                      </div>

                      {/* Expanded Content */}
                      <AnimatePresence>
                        {isExpanded && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="mt-4 pt-4 border-t border-white/10"
                          >
                            <div className="space-y-3">
                              {/* Full Transcript */}
                              <div>
                                <h4 className="text-sm font-medium text-gray-300 mb-2">
                                  Full Transcript
                                </h4>
                                <p className="text-sm text-gray-200 leading-relaxed">
                                  {note.transcript}
                                </p>
                              </div>

                              {/* Action Items */}
                              {note.actionItems.length > 0 && (
                                <div>
                                  <h4 className="text-sm font-medium text-gray-300 mb-2">
                                    Action Items
                                  </h4>
                                  <div className="space-y-1">
                                    {note.actionItems.map((item, itemIndex) => (
                                      <div key={itemIndex} className="flex items-start gap-2">
                                        <div className="w-2 h-2 rounded-full bg-jorge-gold mt-1.5 flex-shrink-0" />
                                        <span className="text-sm text-gray-200">{item.task}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Location Info */}
                              {note.location && (
                                <div>
                                  <h4 className="text-sm font-medium text-gray-300 mb-2">
                                    Location
                                  </h4>
                                  <div className="text-sm text-gray-400">
                                    Lat: {note.location.latitude.toFixed(6)},
                                    Long: {note.location.longitude.toFixed(6)}
                                  </div>
                                </div>
                              )}

                              {/* Export Options */}
                              <div className="flex gap-2 pt-2">
                                <button
                                  onClick={() => onExportNote(note.id, 'text')}
                                  className="px-3 py-2 bg-jorge-electric/20 border border-jorge-electric/30 rounded text-xs text-jorge-electric jorge-haptic"
                                >
                                  Export Text
                                </button>
                                <button
                                  onClick={() => onExportNote(note.id, 'audio')}
                                  className="px-3 py-2 bg-jorge-gold/20 border border-jorge-gold/30 rounded text-xs text-jorge-gold jorge-haptic"
                                >
                                  Export Audio
                                </button>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}