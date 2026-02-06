// Jorge's Real Estate AI Platform - Floating Voice Button
// Always-accessible voice interface with visual feedback

'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Mic, MicOff, Volume2, VolumeX } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FloatingVoiceButtonProps {
  isListening: boolean
  onToggle: () => void
  transcript?: string
  className?: string
  size?: 'sm' | 'md' | 'lg'
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left'
  showTranscript?: boolean
  disabled?: boolean
}

export function FloatingVoiceButton({
  isListening,
  onToggle,
  transcript,
  className,
  size = 'md',
  position = 'bottom-right',
  showTranscript = true,
  disabled = false
}: FloatingVoiceButtonProps) {
  const [audioLevel, setAudioLevel] = useState(0)
  const [showHint, setShowHint] = useState(false)
  const [isPressed, setIsPressed] = useState(false)

  // Simulate audio level visualization when listening
  useEffect(() => {
    if (!isListening) {
      setAudioLevel(0)
      return
    }

    const interval = setInterval(() => {
      // Simulate realistic audio level fluctuation
      const baseLevel = 0.3
      const variation = Math.random() * 0.7
      setAudioLevel(baseLevel + variation)
    }, 100)

    return () => clearInterval(interval)
  }, [isListening])

  // Show hint on first load
  useEffect(() => {
    const hasSeenHint = localStorage.getItem('jorge-voice-hint-seen')
    if (!hasSeenHint && !disabled) {
      const timer = setTimeout(() => {
        setShowHint(true)
        setTimeout(() => {
          setShowHint(false)
          localStorage.setItem('jorge-voice-hint-seen', 'true')
        }, 3000)
      }, 2000)
      return () => clearTimeout(timer)
    }
  }, [disabled])

  // Haptic feedback
  const triggerHaptic = useCallback((intensity: 'light' | 'medium' | 'heavy' = 'medium') => {
    if (typeof navigator !== 'undefined' && 'vibrate' in navigator) {
      switch (intensity) {
        case 'light':
          navigator.vibrate(10)
          break
        case 'medium':
          navigator.vibrate(25)
          break
        case 'heavy':
          navigator.vibrate(50)
          break
      }
    }
  }, [])

  const handleToggle = useCallback(() => {
    if (disabled) return

    triggerHaptic(isListening ? 'light' : 'medium')
    onToggle()
  }, [disabled, isListening, onToggle, triggerHaptic])

  const handlePressStart = useCallback(() => {
    if (disabled) return
    setIsPressed(true)
    triggerHaptic('light')
  }, [disabled, triggerHaptic])

  const handlePressEnd = useCallback(() => {
    setIsPressed(false)
  }, [])

  const sizeClasses = {
    sm: {
      button: 'w-12 h-12',
      icon: 'w-5 h-5',
      transcript: 'text-xs max-w-32'
    },
    md: {
      button: 'w-16 h-16',
      icon: 'w-6 h-6',
      transcript: 'text-sm max-w-40'
    },
    lg: {
      button: 'w-20 h-20',
      icon: 'w-8 h-8',
      transcript: 'text-base max-w-48'
    }
  }

  const positionClasses = {
    'bottom-right': 'bottom-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'top-right': 'top-4 right-4',
    'top-left': 'top-4 left-4'
  }

  return (
    <div className={cn('fixed z-50', positionClasses[position], className)}>
      {/* Transcript Display */}
      <AnimatePresence>
        {showTranscript && transcript && transcript.trim() && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 10 }}
            className={cn(
              'absolute bottom-full mb-3 right-0',
              'bg-gray-900/95 backdrop-blur-sm border border-gray-700',
              'rounded-lg px-3 py-2 shadow-xl',
              sizeClasses[size].transcript
            )}
          >
            <div className="text-white font-medium mb-1">
              Voice Input:
            </div>
            <div className="text-gray-300 leading-tight">
              {transcript}
            </div>

            {/* Speech bubble arrow */}
            <div className="absolute top-full right-4 w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-l-transparent border-r-transparent border-t-gray-700" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Usage Hint */}
      <AnimatePresence>
        {showHint && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, x: 20 }}
            animate={{ opacity: 1, scale: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.8, x: 20 }}
            className="absolute bottom-full mb-3 right-0 bg-blue-500/90 backdrop-blur-sm text-white px-3 py-2 rounded-lg text-sm max-w-48 shadow-xl border border-blue-400/50"
          >
            <div className="font-medium mb-1">Jorge Voice Assistant</div>
            <div className="text-xs opacity-90">
              Tap to talk with AI • Try "Analyze property" or "Find comps"
            </div>

            {/* Speech bubble arrow */}
            <div className="absolute top-full right-4 w-0 h-0 border-l-[6px] border-r-[6px] border-t-[6px] border-l-transparent border-r-transparent border-t-blue-500" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Voice Button */}
      <motion.button
        whileHover={disabled ? {} : { scale: 1.05 }}
        whileTap={disabled ? {} : { scale: 0.95 }}
        animate={{
          scale: isPressed ? 0.95 : 1,
          boxShadow: isListening
            ? `0 0 ${20 + audioLevel * 30}px rgba(59, 130, 246, ${0.5 + audioLevel * 0.3})`
            : '0 4px 20px rgba(0, 0, 0, 0.3)'
        }}
        onClick={handleToggle}
        onTouchStart={handlePressStart}
        onTouchEnd={handlePressEnd}
        onMouseDown={handlePressStart}
        onMouseUp={handlePressEnd}
        onMouseLeave={handlePressEnd}
        disabled={disabled}
        className={cn(
          // Base styles
          'relative overflow-hidden rounded-full transition-all duration-200',
          'flex items-center justify-center shadow-lg',
          'touch-manipulation select-none',
          'focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-900',

          // Size
          sizeClasses[size].button,

          // State-based styling
          disabled
            ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
            : isListening
              ? 'bg-gradient-to-br from-red-500 to-red-600 text-white'
              : 'bg-gradient-to-br from-blue-500 to-blue-600 text-white hover:from-blue-400 hover:to-blue-500'
        )}
        aria-label={isListening ? 'Stop voice recording' : 'Start voice recording'}
        aria-pressed={isListening}
      >
        {/* Background pulse effect */}
        {isListening && (
          <motion.div
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.5, 0.8, 0.5]
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
              ease: "easeInOut"
            }}
            className="absolute inset-0 rounded-full bg-white/20"
          />
        )}

        {/* Audio level visualizer rings */}
        {isListening && (
          <>
            <motion.div
              animate={{
                scale: [1, 1.5, 1],
                opacity: [0.3, 0.6, 0.3]
              }}
              transition={{
                duration: 0.8,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.1
              }}
              className="absolute inset-0 rounded-full border-2 border-white/30"
              style={{
                transform: `scale(${1 + audioLevel * 0.3})`
              }}
            />
            <motion.div
              animate={{
                scale: [1, 1.8, 1],
                opacity: [0.2, 0.4, 0.2]
              }}
              transition={{
                duration: 1.2,
                repeat: Infinity,
                ease: "easeInOut",
                delay: 0.2
              }}
              className="absolute inset-0 rounded-full border border-white/20"
              style={{
                transform: `scale(${1.2 + audioLevel * 0.5})`
              }}
            />
          </>
        )}

        {/* Icon */}
        <div className="relative z-10">
          <AnimatePresence mode="wait">
            {isListening ? (
              <motion.div
                key="listening"
                initial={{ scale: 0, rotate: 180 }}
                animate={{ scale: 1, rotate: 0 }}
                exit={{ scale: 0, rotate: -180 }}
                transition={{ duration: 0.3 }}
              >
                <MicOff className={cn(sizeClasses[size].icon)} />
              </motion.div>
            ) : (
              <motion.div
                key="not-listening"
                initial={{ scale: 0, rotate: -180 }}
                animate={{ scale: 1, rotate: 0 }}
                exit={{ scale: 0, rotate: 180 }}
                transition={{ duration: 0.3 }}
              >
                <Mic className={cn(sizeClasses[size].icon)} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Active indicator dot */}
        {isListening && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
            className="absolute -top-1 -right-1 w-4 h-4 bg-red-400 rounded-full border-2 border-white"
          >
            <motion.div
              animate={{
                scale: [1, 1.2, 1],
                opacity: [1, 0.7, 1]
              }}
              transition={{
                duration: 1,
                repeat: Infinity
              }}
              className="w-full h-full bg-red-400 rounded-full"
            />
          </motion.div>
        )}

        {/* Press feedback overlay */}
        <AnimatePresence>
          {isPressed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.3 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-white rounded-full"
            />
          )}
        </AnimatePresence>

        {/* Disabled overlay */}
        {disabled && (
          <div className="absolute inset-0 bg-gray-600/50 rounded-full flex items-center justify-center">
            <VolumeX className={cn(sizeClasses[size].icon, 'text-gray-400')} />
          </div>
        )}
      </motion.button>

      {/* Status indicator */}
      <AnimatePresence>
        {isListening && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className="absolute -bottom-1 left-1/2 transform -translate-x-1/2 bg-red-500 text-white px-2 py-1 rounded text-xs font-medium whitespace-nowrap"
          >
            Listening...
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// Companion component for voice command hints
interface VoiceCommandHintsProps {
  isVisible: boolean
  commands: string[]
  className?: string
}

export function VoiceCommandHints({ isVisible, commands, className }: VoiceCommandHintsProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 10, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 10, scale: 0.95 }}
          className={cn(
            'bg-gray-900/95 backdrop-blur-sm border border-gray-700 rounded-lg p-3 shadow-xl',
            className
          )}
        >
          <div className="text-sm font-medium text-white mb-2">
            Try saying:
          </div>
          <div className="space-y-1">
            {commands.map((command, index) => (
              <motion.div
                key={command}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="text-xs text-blue-400 bg-blue-500/10 px-2 py-1 rounded"
              >
                "{command}"
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}