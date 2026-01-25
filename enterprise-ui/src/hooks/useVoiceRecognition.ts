// Jorge's Real Estate AI Platform - Voice Recognition Hook
// Hands-free voice interaction for field work and driving

import { useState, useEffect, useCallback, useRef } from 'react'

interface VoiceRecognitionState {
  isListening: boolean
  isSupported: boolean
  transcript: string
  finalTranscript: string
  interimTranscript: string
  confidence: number
  error: string | null
  isProcessing: boolean
}

interface VoiceCommand {
  patterns: string[]
  action: string
  description: string
  examples: string[]
}

interface VoiceRecognitionOptions {
  language?: string
  continuous?: boolean
  interimResults?: boolean
  maxAlternatives?: number
  grammars?: string[]
  hotwords?: string[]
  autoRestart?: boolean
  noiseThreshold?: number
}

// Jorge-specific voice commands for real estate operations
const JORGE_VOICE_COMMANDS: VoiceCommand[] = [
  {
    patterns: ['analyze property', 'analyze this property', 'property analysis'],
    action: 'ANALYZE_PROPERTY',
    description: 'Analyze current property for market intelligence',
    examples: ['Analyze this property', 'Property analysis']
  },
  {
    patterns: ['find comps', 'comparable properties', 'find comparables', 'show comps'],
    action: 'FIND_COMPARABLES',
    description: 'Find comparable properties in the area',
    examples: ['Find comps for this property', 'Show me comparables']
  },
  {
    patterns: ['new lead', 'capture lead', 'add lead', 'create lead'],
    action: 'CAPTURE_LEAD',
    description: 'Start lead capture process',
    examples: ['New lead capture', 'Add a new lead']
  },
  {
    patterns: ['call jorge bot', 'talk to jorge', 'jorge seller bot', 'seller qualification'],
    action: 'JORGE_BOT',
    description: 'Start conversation with Jorge Seller Bot',
    examples: ['Call Jorge bot', 'Talk to Jorge seller bot']
  },
  {
    patterns: ['price estimate', 'property value', 'market value', 'estimate value'],
    action: 'PRICE_ESTIMATE',
    description: 'Get AI-powered property valuation',
    examples: ['What\'s this property worth?', 'Price estimate']
  },
  {
    patterns: ['voice note', 'take note', 'record note', 'add note'],
    action: 'VOICE_NOTE',
    description: 'Record voice note for current property or lead',
    examples: ['Take a voice note', 'Record my thoughts']
  },
  {
    patterns: ['schedule showing', 'book appointment', 'set appointment', 'schedule visit'],
    action: 'SCHEDULE_SHOWING',
    description: 'Schedule property showing or client meeting',
    examples: ['Schedule a showing', 'Book appointment for tomorrow']
  },
  {
    patterns: ['hot leads', 'show hot leads', 'urgent leads', 'priority leads'],
    action: 'HOT_LEADS',
    description: 'Display high-priority leads requiring attention',
    examples: ['Show me hot leads', 'What urgent leads do I have?']
  },
  {
    patterns: ['today schedule', 'todays agenda', 'what\'s next', 'my schedule'],
    action: 'TODAY_SCHEDULE',
    description: 'Show today\'s schedule and upcoming appointments',
    examples: ['What\'s my schedule today?', 'Show today\'s agenda']
  },
  {
    patterns: ['client info', 'lead information', 'tell me about', 'who is'],
    action: 'CLIENT_INFO',
    description: 'Get information about specific client or lead',
    examples: ['Tell me about Sarah Johnson', 'Client info for John Smith']
  }
]

export function useVoiceRecognition(options: VoiceRecognitionOptions = {}) {
  const {
    language = 'en-US',
    continuous = true,
    interimResults = true,
    maxAlternatives = 1,
    autoRestart = true,
    noiseThreshold = 0.3
  } = options

  const [state, setState] = useState<VoiceRecognitionState>({
    isListening: false,
    isSupported: false,
    transcript: '',
    finalTranscript: '',
    interimTranscript: '',
    confidence: 0,
    error: null,
    isProcessing: false
  })

  const recognitionRef = useRef<SpeechRecognition | null>(null)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const restartTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Check browser support
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const isSupported = !!SpeechRecognition

    setState(prev => ({ ...prev, isSupported }))

    if (isSupported) {
      recognitionRef.current = new SpeechRecognition()
      setupSpeechRecognition()
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort()
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      if (restartTimeoutRef.current) {
        clearTimeout(restartTimeoutRef.current)
      }
    }
  }, [])

  const setupSpeechRecognition = useCallback(() => {
    if (!recognitionRef.current) return

    const recognition = recognitionRef.current

    recognition.lang = language
    recognition.continuous = continuous
    recognition.interimResults = interimResults
    recognition.maxAlternatives = maxAlternatives

    recognition.onstart = () => {
      console.log('🎤 Jorge AI: Voice recognition started')
      setState(prev => ({
        ...prev,
        isListening: true,
        error: null
      }))
    }

    recognition.onend = () => {
      console.log('🎤 Jorge AI: Voice recognition ended')
      setState(prev => ({ ...prev, isListening: false }))

      // Auto-restart if enabled and not manually stopped
      if (autoRestart && state.isListening) {
        restartTimeoutRef.current = setTimeout(() => {
          startListening()
        }, 1000)
      }
    }

    recognition.onerror = (event) => {
      console.error('🎤 Jorge AI: Voice recognition error:', event.error)

      let errorMessage = 'Voice recognition error'

      switch (event.error) {
        case 'no-speech':
          errorMessage = 'No speech detected. Try speaking closer to the microphone.'
          break
        case 'audio-capture':
          errorMessage = 'Audio capture failed. Check microphone permissions.'
          break
        case 'not-allowed':
          errorMessage = 'Microphone access denied. Please allow microphone permissions.'
          break
        case 'network':
          errorMessage = 'Network error. Voice recognition requires internet connection.'
          break
        case 'aborted':
          errorMessage = 'Voice recognition was stopped.'
          break
        default:
          errorMessage = `Voice recognition error: ${event.error}`
      }

      setState(prev => ({
        ...prev,
        error: errorMessage,
        isListening: false
      }))
    }

    recognition.onresult = (event) => {
      let interimTranscript = ''
      let finalTranscript = ''
      let confidence = 0

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        const transcript = result[0].transcript

        if (result.isFinal) {
          finalTranscript += transcript
          confidence = result[0].confidence
        } else {
          interimTranscript += transcript
        }
      }

      setState(prev => ({
        ...prev,
        transcript: finalTranscript || interimTranscript,
        finalTranscript,
        interimTranscript,
        confidence,
        error: null
      }))

      // Process final results for voice commands
      if (finalTranscript) {
        processVoiceCommand(finalTranscript.toLowerCase().trim())
      }

      // Auto-stop listening after period of silence
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      timeoutRef.current = setTimeout(() => {
        if (recognitionRef.current && state.isListening) {
          recognitionRef.current.stop()
        }
      }, 3000) // Stop after 3 seconds of silence
    }
  }, [language, continuous, interimResults, maxAlternatives, autoRestart, state.isListening])

  const startListening = useCallback(() => {
    if (!recognitionRef.current || state.isListening) return

    try {
      setState(prev => ({ ...prev, error: null }))
      recognitionRef.current.start()
      console.log('🎤 Jorge AI: Starting voice recognition...')
    } catch (error) {
      console.error('🎤 Jorge AI: Failed to start voice recognition:', error)
      setState(prev => ({
        ...prev,
        error: 'Failed to start voice recognition'
      }))
    }
  }, [state.isListening])

  const stopListening = useCallback(() => {
    if (recognitionRef.current && state.isListening) {
      recognitionRef.current.stop()
      console.log('🎤 Jorge AI: Stopping voice recognition...')
    }

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    if (restartTimeoutRef.current) {
      clearTimeout(restartTimeoutRef.current)
    }
  }, [state.isListening])

  const toggleListening = useCallback(() => {
    if (state.isListening) {
      stopListening()
    } else {
      startListening()
    }
  }, [state.isListening, startListening, stopListening])

  const processVoiceCommand = useCallback((transcript: string) => {
    setState(prev => ({ ...prev, isProcessing: true }))

    // Find matching voice command
    const matchedCommand = JORGE_VOICE_COMMANDS.find(command =>
      command.patterns.some(pattern =>
        transcript.includes(pattern.toLowerCase())
      )
    )

    if (matchedCommand) {
      console.log('🎤 Jorge AI: Voice command detected:', matchedCommand.action)

      // Emit custom event for voice command
      const event = new CustomEvent('jorgeVoiceCommand', {
        detail: {
          command: matchedCommand.action,
          transcript,
          confidence: state.confidence,
          timestamp: Date.now()
        }
      })

      window.dispatchEvent(event)
    } else {
      console.log('🎤 Jorge AI: No command matched, treating as general speech:', transcript)

      // Emit general voice input event
      const event = new CustomEvent('jorgeVoiceInput', {
        detail: {
          transcript,
          confidence: state.confidence,
          timestamp: Date.now()
        }
      })

      window.dispatchEvent(event)
    }

    setState(prev => ({ ...prev, isProcessing: false }))
  }, [state.confidence])

  const clearTranscript = useCallback(() => {
    setState(prev => ({
      ...prev,
      transcript: '',
      finalTranscript: '',
      interimTranscript: '',
      confidence: 0
    }))
  }, [])

  const resetError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }))
  }, [])

  // Get available voice commands for current context
  const getAvailableCommands = useCallback((context?: string) => {
    if (context) {
      // Filter commands by context (e.g., 'property', 'lead', 'schedule')
      return JORGE_VOICE_COMMANDS.filter(command =>
        command.action.toLowerCase().includes(context.toLowerCase()) ||
        command.description.toLowerCase().includes(context.toLowerCase())
      )
    }

    return JORGE_VOICE_COMMANDS
  }, [])

  // Check if transcript matches any command pattern
  const isVoiceCommand = useCallback((transcript: string) => {
    return JORGE_VOICE_COMMANDS.some(command =>
      command.patterns.some(pattern =>
        transcript.toLowerCase().includes(pattern.toLowerCase())
      )
    )
  }, [])

  return {
    // State
    ...state,

    // Control functions
    startListening,
    stopListening,
    toggleListening,
    clearTranscript,
    resetError,

    // Voice command utilities
    getAvailableCommands,
    isVoiceCommand,
    processVoiceCommand,

    // Jorge-specific helpers
    isFieldWorkMode: state.isListening && !state.error,
    canUseVoiceCommands: state.isSupported && !state.error,
    shouldShowVoiceHints: state.isListening && !state.finalTranscript,
    confidenceLevel: state.confidence > 0.8 ? 'high' : state.confidence > 0.6 ? 'medium' : 'low'
  }
}

// Type definitions for Speech Recognition API
declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition
    webkitSpeechRecognition: typeof SpeechRecognition
  }

  interface SpeechRecognitionEvent extends Event {
    resultIndex: number
    results: SpeechRecognitionResultList
  }

  interface SpeechRecognitionErrorEvent extends Event {
    error: string
    message?: string
  }

  class SpeechRecognition extends EventTarget {
    continuous: boolean
    grammars: SpeechGrammarList
    interimResults: boolean
    lang: string
    maxAlternatives: number
    serviceURI: string

    onaudioend: ((this: SpeechRecognition, ev: Event) => any) | null
    onaudiostart: ((this: SpeechRecognition, ev: Event) => any) | null
    onend: ((this: SpeechRecognition, ev: Event) => any) | null
    onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => any) | null
    onnomatch: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null
    onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => any) | null
    onsoundend: ((this: SpeechRecognition, ev: Event) => any) | null
    onsoundstart: ((this: SpeechRecognition, ev: Event) => any) | null
    onspeechend: ((this: SpeechRecognition, ev: Event) => any) | null
    onspeechstart: ((this: SpeechRecognition, ev: Event) => any) | null
    onstart: ((this: SpeechRecognition, ev: Event) => any) | null

    abort(): void
    start(): void
    stop(): void
  }

  interface SpeechRecognitionResultList {
    readonly length: number
    item(index: number): SpeechRecognitionResult
    [index: number]: SpeechRecognitionResult
  }

  interface SpeechRecognitionResult {
    readonly isFinal: boolean
    readonly length: number
    item(index: number): SpeechRecognitionAlternative
    [index: number]: SpeechRecognitionAlternative
  }

  interface SpeechRecognitionAlternative {
    readonly confidence: number
    readonly transcript: string
  }
}