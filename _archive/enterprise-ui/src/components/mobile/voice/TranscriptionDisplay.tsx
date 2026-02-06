'use client';

import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";
import {
  SpeakerWaveIcon,
  DocumentDuplicateIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from "@heroicons/react/24/outline";

interface TranscriptionDisplayProps {
  transcript: string;
  confidence: number;
  isLive: boolean;
  keywords?: string[];
  actionItems?: string[];
}

export function TranscriptionDisplay({
  transcript,
  confidence,
  isLive,
  keywords = [],
  actionItems = [],
}: TranscriptionDisplayProps) {
  const [displayText, setDisplayText] = useState('');
  const [copied, setCopied] = useState(false);

  // Typewriter effect for live transcription
  useEffect(() => {
    if (isLive && transcript) {
      setDisplayText(transcript);
    } else if (!isLive) {
      setDisplayText(transcript);
    }
  }, [transcript, isLive]);

  const getConfidenceColor = () => {
    if (confidence >= 0.9) return 'text-green-500';
    if (confidence >= 0.7) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getConfidenceIcon = () => {
    if (confidence >= 0.9) return CheckCircleIcon;
    if (confidence >= 0.7) return SpeakerWaveIcon;
    return ExclamationTriangleIcon;
  };

  const ConfidenceIcon = getConfidenceIcon();

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(transcript);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  };

  const highlightKeywords = (text: string) => {
    if (!keywords.length) return text;

    let highlightedText = text;
    keywords.forEach(keyword => {
      const regex = new RegExp(`\\b(${keyword})\\b`, 'gi');
      highlightedText = highlightedText.replace(regex, `<mark class="bg-jorge-electric/20 text-jorge-electric px-1 rounded">$1</mark>`);
    });

    return highlightedText;
  };

  if (!transcript && !isLive) return null;

  return (
    <motion.div
      layout
      className="jorge-glass p-4 rounded-xl border border-white/10"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <SpeakerWaveIcon className="w-4 h-4 text-jorge-electric" />
          <span className="text-sm jorge-code text-gray-300">
            {isLive ? 'Live Transcription' : 'Transcript'}
          </span>
          {isLive && (
            <motion.div
              animate={{ opacity: [1, 0.3, 1] }}
              transition={{ repeat: Infinity, duration: 1.5 }}
              className="w-2 h-2 rounded-full bg-red-500"
            />
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Confidence indicator */}
          <div className="flex items-center gap-1">
            <ConfidenceIcon className={`w-4 h-4 ${getConfidenceColor()}`} />
            <span className={`text-xs jorge-code ${getConfidenceColor()}`}>
              {Math.round(confidence * 100)}%
            </span>
          </div>

          {/* Copy button */}
          {transcript && (
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={copyToClipboard}
              className="p-1.5 rounded-lg bg-white/10 jorge-haptic"
            >
              <AnimatePresence mode="wait">
                {copied ? (
                  <motion.div
                    key="check"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    exit={{ scale: 0 }}
                  >
                    <CheckCircleIcon className="w-4 h-4 text-green-500" />
                  </motion.div>
                ) : (
                  <motion.div
                    key="copy"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    exit={{ scale: 0 }}
                  >
                    <DocumentDuplicateIcon className="w-4 h-4 text-gray-400" />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.button>
          )}
        </div>
      </div>

      {/* Transcript Content */}
      <div className="space-y-3">
        {displayText ? (
          <motion.div
            layout
            className="text-sm text-gray-100 leading-relaxed"
          >
            {isLive ? (
              // Live typing effect
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                dangerouslySetInnerHTML={{ __html: highlightKeywords(displayText) }}
              />
            ) : (
              <div dangerouslySetInnerHTML={{ __html: highlightKeywords(displayText) }} />
            )}

            {isLive && (
              <motion.span
                animate={{ opacity: [1, 0, 1] }}
                transition={{ repeat: Infinity, duration: 1 }}
                className="text-jorge-electric ml-1"
              >
                |
              </motion.span>
            )}
          </motion.div>
        ) : (
          <div className="text-sm text-gray-400 italic">
            {isLive ? 'Listening...' : 'No transcript available'}
          </div>
        )}

        {/* Real Estate Keywords */}
        {keywords.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-wrap gap-1"
          >
            <span className="text-xs text-gray-400 jorge-code mr-2">Keywords:</span>
            {keywords.map((keyword, index) => (
              <motion.span
                key={keyword}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className="px-2 py-1 text-xs bg-jorge-electric/10 border border-jorge-electric/30 rounded-full text-jorge-electric"
              >
                {keyword}
              </motion.span>
            ))}
          </motion.div>
        )}

        {/* Action Items */}
        {actionItems.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-2"
          >
            <span className="text-xs text-gray-400 jorge-code">Action Items:</span>
            <div className="space-y-1">
              {actionItems.map((item, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-start gap-2 text-xs"
                >
                  <div className="w-2 h-2 rounded-full bg-jorge-gold mt-1 flex-shrink-0" />
                  <span className="text-gray-200">{item}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* Quality Indicators */}
      <div className="mt-3 pt-3 border-t border-white/5">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1">
              <span className="text-gray-400 jorge-code">Quality:</span>
              <span className={getConfidenceColor()}>
                {confidence >= 0.9 ? 'Excellent' : confidence >= 0.7 ? 'Good' : 'Fair'}
              </span>
            </div>
            {transcript && (
              <div className="flex items-center gap-1">
                <span className="text-gray-400 jorge-code">Words:</span>
                <span className="text-gray-300">
                  {transcript.split(' ').filter(word => word.length > 0).length}
                </span>
              </div>
            )}
          </div>

          {isLive && (
            <div className="flex items-center gap-1 text-gray-400 jorge-code">
              <div className="w-1 h-1 rounded-full bg-jorge-electric animate-pulse" />
              <span>Processing...</span>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}