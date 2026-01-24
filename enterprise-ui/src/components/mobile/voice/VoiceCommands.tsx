'use client';

import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";
import {
  CommandLineIcon,
  SpeakerWaveIcon,
  ChatBubbleLeftRightIcon,
  HomeIcon,
  MapPinIcon,
  UserIcon,
  ClockIcon,
  TagIcon,
} from "@heroicons/react/24/outline";

interface VoiceCommandsProps {
  isListening: boolean;
  isRecording: boolean;
  onVoiceCommand?: (command: string, params?: any) => void;
}

interface VoiceCommand {
  id: string;
  phrase: string;
  description: string;
  icon: React.ElementType;
  category: 'navigation' | 'recording' | 'notes' | 'property';
  examples: string[];
  color: string;
}

const voiceCommands: VoiceCommand[] = [
  {
    id: 'start-recording',
    phrase: 'Start recording',
    description: 'Begin voice note recording',
    icon: SpeakerWaveIcon,
    category: 'recording',
    examples: ['Start recording', 'Begin note', 'Record voice note'],
    color: 'jorge-electric',
  },
  {
    id: 'property-note',
    phrase: 'Property note for [address]',
    description: 'Create property-specific note',
    icon: HomeIcon,
    category: 'property',
    examples: ['Property note for 123 Main Street', 'Note about this house', 'Property features'],
    color: 'jorge-gold',
  },
  {
    id: 'client-feedback',
    phrase: 'Client feedback',
    description: 'Record client reactions',
    icon: UserIcon,
    category: 'notes',
    examples: ['Client feedback', 'Client loves this', 'Buyer reaction'],
    color: 'jorge-glow',
  },
  {
    id: 'follow-up-task',
    phrase: 'Add follow-up [task]',
    description: 'Create action item',
    icon: ClockIcon,
    category: 'notes',
    examples: ['Add follow-up call mortgage broker', 'Schedule second showing', 'Get HOA docs'],
    color: 'jorge-steel',
  },
  {
    id: 'location-note',
    phrase: 'Location note',
    description: 'GPS-tagged observation',
    icon: MapPinIcon,
    category: 'property',
    examples: ['Location note', 'Neighborhood observation', 'Market insight'],
    color: 'jorge-electric',
  },
  {
    id: 'tag-as-hot',
    phrase: 'Tag as hot lead',
    description: 'Mark as priority',
    icon: TagIcon,
    category: 'notes',
    examples: ['Tag as hot lead', 'This is hot', 'Priority client'],
    color: 'red-500',
  },
  {
    id: 'navigate-dashboard',
    phrase: 'Go to dashboard',
    description: 'Navigate to main dashboard',
    icon: CommandLineIcon,
    category: 'navigation',
    examples: ['Go to dashboard', 'Show main screen', 'Navigate home'],
    color: 'jorge-electric',
  },
  {
    id: 'share-note',
    phrase: 'Share this note',
    description: 'Share with client or team',
    icon: ChatBubbleLeftRightIcon,
    category: 'notes',
    examples: ['Share this note', 'Send to client', 'Share with team'],
    color: 'jorge-glow',
  },
];

export function VoiceCommands({ isListening, isRecording, onVoiceCommand }: VoiceCommandsProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [recentCommands, setRecentCommands] = useState<string[]>([]);
  const [expandedCommand, setExpandedCommand] = useState<string | null>(null);

  const categories = [
    { id: 'all', name: 'All', icon: CommandLineIcon },
    { id: 'recording', name: 'Recording', icon: SpeakerWaveIcon },
    { id: 'property', name: 'Property', icon: HomeIcon },
    { id: 'notes', name: 'Notes', icon: ChatBubbleLeftRightIcon },
    { id: 'navigation', name: 'Navigate', icon: MapPinIcon },
  ];

  const filteredCommands = selectedCategory === 'all'
    ? voiceCommands
    : voiceCommands.filter(cmd => cmd.category === selectedCategory);

  const handleCommandTrigger = (command: VoiceCommand) => {
    setRecentCommands(prev => [command.id, ...prev.slice(0, 4)]);
    onVoiceCommand?.(command.id);
  };

  return (
    <motion.div
      layout
      className="jorge-glass p-4 rounded-xl"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <CommandLineIcon className="w-5 h-5 text-jorge-electric" />
          <h3 className="text-lg font-semibold jorge-heading text-white">
            Voice Commands
          </h3>
        </div>

        {/* Voice status indicator */}
        <div className="flex items-center gap-2">
          {isListening && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="flex items-center gap-1"
            >
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
                className="w-2 h-2 rounded-full bg-jorge-electric"
              />
              <span className="text-xs jorge-code text-jorge-electric">
                LISTENING
              </span>
            </motion.div>
          )}
        </div>
      </div>

      {/* Category Filter */}
      <div className="mb-4">
        <div className="flex gap-2 overflow-x-auto scrollbar-hide">
          {categories.map((category) => {
            const Icon = category.icon;
            const isActive = selectedCategory === category.id;

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
                <Icon className="w-4 h-4" />
                <span className="text-sm jorge-code">{category.name}</span>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Commands Grid */}
      <div className="space-y-2">
        <AnimatePresence mode="popLayout">
          {filteredCommands.map((command, index) => {
            const Icon = command.icon;
            const isExpanded = expandedCommand === command.id;
            const isRecent = recentCommands.includes(command.id);

            return (
              <motion.div
                key={command.id}
                layout
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.05 }}
                className={`
                  relative p-3 rounded-lg border transition-all duration-200
                  ${isRecent
                    ? 'bg-jorge-electric/10 border-jorge-electric/30'
                    : 'bg-white/5 border-white/10 hover:bg-white/10'
                  }
                `}
              >
                <motion.button
                  whileTap={{ scale: 0.98 }}
                  onClick={() => setExpandedCommand(isExpanded ? null : command.id)}
                  className="w-full text-left jorge-haptic"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Icon className={`w-5 h-5 text-${command.color}`} />
                      <div>
                        <div className="font-medium text-white text-sm">
                          "{command.phrase}"
                        </div>
                        <div className="text-xs text-gray-400">
                          {command.description}
                        </div>
                      </div>
                    </div>

                    {/* Recent indicator */}
                    {isRecent && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="w-2 h-2 rounded-full bg-jorge-electric"
                      />
                    )}
                  </div>
                </motion.button>

                {/* Expanded Examples */}
                <AnimatePresence>
                  {isExpanded && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-3 pt-3 border-t border-white/10"
                    >
                      <div className="space-y-2">
                        <div className="text-xs jorge-code text-gray-400 uppercase">
                          Examples:
                        </div>
                        {command.examples.map((example, exampleIndex) => (
                          <motion.button
                            key={exampleIndex}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: exampleIndex * 0.1 }}
                            onClick={() => handleCommandTrigger(command)}
                            className="block w-full text-left p-2 rounded bg-black/20 hover:bg-black/30 transition-colors jorge-haptic"
                          >
                            <span className="text-sm text-gray-200">
                              "{example}"
                            </span>
                          </motion.button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Quick Action Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="mt-4 pt-4 border-t border-white/10"
      >
        <div className="flex items-center justify-between">
          <div className="text-xs jorge-code text-gray-400">
            Quick Actions
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 mt-2">
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={() => handleCommandTrigger(voiceCommands[0])}
            className="p-2 rounded bg-jorge-electric/20 border border-jorge-electric/30 jorge-haptic"
          >
            <div className="flex items-center gap-2">
              <SpeakerWaveIcon className="w-4 h-4 text-jorge-electric" />
              <span className="text-sm text-jorge-electric">Start Recording</span>
            </div>
          </motion.button>

          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={() => handleCommandTrigger(voiceCommands[1])}
            className="p-2 rounded bg-jorge-gold/20 border border-jorge-gold/30 jorge-haptic"
          >
            <div className="flex items-center gap-2">
              <HomeIcon className="w-4 h-4 text-jorge-gold" />
              <span className="text-sm text-jorge-gold">Property Note</span>
            </div>
          </motion.button>
        </div>
      </motion.div>

      {/* Voice Commands Help */}
      {!isRecording && !isListening && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/30"
        >
          <div className="text-xs text-blue-400 space-y-1">
            <div className="font-medium">💡 Pro Tip:</div>
            <div>Say any command phrase to trigger it hands-free while recording</div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}