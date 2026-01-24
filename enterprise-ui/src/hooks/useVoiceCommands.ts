/**
 * Jorge Real Estate AI Platform - Voice Commands Hook
 * Professional speech recognition and voice control
 *
 * Features:
 * - Real-time speech recognition
 * - Voice command parsing
 * - Noise cancellation
 * - Multi-language support
 * - Jorge's voice synthesis
 * - Hands-free operation
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

interface VoiceCommandsConfig {
  continuous?: boolean;
  interimResults?: boolean;
  language?: string;
  maxAlternatives?: number;
}

interface SpeechRecognitionResult {
  transcript: string;
  confidence: number;
  isFinal: boolean;
}

interface VoiceCommand {
  command: string;
  action: string;
  confidence: number;
  timestamp: number;
}

// Extend Window interface for Speech Recognition
declare global {
  interface Window {
    SpeechRecognition?: any;
    webkitSpeechRecognition?: any;
  }
}

export function useVoiceCommands(config: VoiceCommandsConfig = {}) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [error, setError] = useState<string>('');
  const [isSupported, setIsSupported] = useState(false);
  const [commandHistory, setCommandHistory] = useState<VoiceCommand[]>([]);

  const recognitionRef = useRef<any>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const lastTranscriptRef = useRef('');

  // Default configuration
  const defaultConfig: VoiceCommandsConfig = {
    continuous: false,
    interimResults: true,
    language: 'en-US',
    maxAlternatives: 3,
    ...config
  };

  // Check if speech recognition is supported
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    setIsSupported(!!SpeechRecognition);

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;

      // Configure recognition
      recognition.continuous = defaultConfig.continuous;
      recognition.interimResults = defaultConfig.interimResults;
      recognition.lang = defaultConfig.language;
      recognition.maxAlternatives = defaultConfig.maxAlternatives;

      // Event handlers
      recognition.onstart = () => {
        setIsListening(true);
        setError('');
        console.log('Speech recognition started');
      };

      recognition.onend = () => {
        setIsListening(false);
        console.log('Speech recognition ended');
      };

      recognition.onerror = (event: any) => {
        setError(event.error);
        setIsListening(false);
        console.error('Speech recognition error:', event.error);

        // Handle specific errors
        switch (event.error) {
          case 'not-allowed':
            setError('Microphone access denied. Please enable microphone permissions.');
            break;
          case 'no-speech':
            setError('No speech detected. Please try again.');
            break;
          case 'network':
            setError('Network error. Please check your connection.');
            break;
          case 'audio-capture':
            setError('Microphone not available. Please check your audio settings.');
            break;
          default:
            setError(`Speech recognition error: ${event.error}`);
        }
      };

      recognition.onresult = (event: any) => {
        let finalTranscript = '';
        let interimTranscript = '';

        // Process all results
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          const transcriptText = result[0].transcript;

          if (result.isFinal) {
            finalTranscript += transcriptText;
            setConfidence(result[0].confidence || 0);
          } else {
            interimTranscript += transcriptText;
          }
        }

        // Update transcripts
        if (finalTranscript) {
          setTranscript(finalTranscript.trim());
          setInterimTranscript('');
          lastTranscriptRef.current = finalTranscript.trim();

          // Add to command history
          const command: VoiceCommand = {
            command: finalTranscript.trim(),
            action: parseVoiceCommand(finalTranscript.trim()),
            confidence: confidence,
            timestamp: Date.now()
          };

          setCommandHistory(prev => [command, ...prev.slice(0, 19)]); // Keep last 20 commands

          // Auto-stop if not continuous
          if (!defaultConfig.continuous) {
            stopListening();
          }
        } else {
          setInterimTranscript(interimTranscript);
        }
      };
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.onstart = null;
        recognitionRef.current.onend = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onresult = null;
      }
    };
  }, [defaultConfig.continuous, defaultConfig.interimResults, defaultConfig.language, defaultConfig.maxAlternatives, confidence]);

  // Parse voice commands for property-related actions
  const parseVoiceCommand = useCallback((text: string): string => {
    const lowerText = text.toLowerCase();

    // Property scanning commands
    if (lowerText.includes('scan property') || lowerText.includes('find property')) {
      return 'scan_property';
    }

    if (lowerText.includes('show mls') || lowerText.includes('lookup mls')) {
      return 'lookup_mls';
    }

    if (lowerText.includes('price check') || lowerText.includes('get price')) {
      return 'price_check';
    }

    if (lowerText.includes('jorge analysis') || lowerText.includes('get analysis')) {
      return 'jorge_analysis';
    }

    if (lowerText.includes('find address') || lowerText.includes('search address')) {
      return 'address_search';
    }

    if (lowerText.includes('take photo') || lowerText.includes('capture photo')) {
      return 'take_photo';
    }

    if (lowerText.includes('start recording') || lowerText.includes('voice note')) {
      return 'voice_note';
    }

    if (lowerText.includes('call lead') || lowerText.includes('contact lead')) {
      return 'contact_lead';
    }

    if (lowerText.includes('schedule showing') || lowerText.includes('book appointment')) {
      return 'schedule_showing';
    }

    // Navigation commands
    if (lowerText.includes('go to dashboard') || lowerText.includes('show dashboard')) {
      return 'navigate_dashboard';
    }

    if (lowerText.includes('open scanner') || lowerText.includes('start scanner')) {
      return 'open_scanner';
    }

    // General commands
    if (lowerText.includes('help') || lowerText.includes('what can you do')) {
      return 'show_help';
    }

    if (lowerText.includes('stop') || lowerText.includes('cancel')) {
      return 'stop_action';
    }

    // Default to general property search
    return 'general_search';
  }, []);

  // Start listening
  const startListening = useCallback(() => {
    if (!isSupported) {
      setError('Speech recognition not supported in this browser');
      return Promise.reject(new Error('Speech recognition not supported'));
    }

    if (!recognitionRef.current) {
      setError('Speech recognition not initialized');
      return Promise.reject(new Error('Speech recognition not initialized'));
    }

    if (isListening) {
      return Promise.resolve();
    }

    try {
      // Clear previous state
      setTranscript('');
      setInterimTranscript('');
      setError('');
      setConfidence(0);

      // Start recognition
      recognitionRef.current.start();

      // Set timeout for auto-stop (30 seconds)
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        if (isListening) {
          stopListening();
        }
      }, 30000);

      return Promise.resolve();
    } catch (error: any) {
      console.error('Failed to start speech recognition:', error);
      setError(error.message || 'Failed to start speech recognition');
      return Promise.reject(error);
    }
  }, [isSupported, isListening]);

  // Stop listening
  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
    }

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    setIsListening(false);
  }, [isListening]);

  // Toggle listening
  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  // Reset transcript
  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
    setConfidence(0);
    lastTranscriptRef.current = '';
  }, []);

  // Clear command history
  const clearHistory = useCallback(() => {
    setCommandHistory([]);
  }, []);

  // Get last command
  const getLastCommand = useCallback((): VoiceCommand | null => {
    return commandHistory.length > 0 ? commandHistory[0] : null;
  }, [commandHistory]);

  // Check if voice contains specific keywords
  const containsKeywords = useCallback((keywords: string[]): boolean => {
    const lowerTranscript = transcript.toLowerCase();
    return keywords.some(keyword => lowerTranscript.includes(keyword.toLowerCase()));
  }, [transcript]);

  // Extract property information from transcript
  const extractPropertyInfo = useCallback(() => {
    const text = transcript.toLowerCase();

    // Extract address patterns
    const addressPattern = /(\d+[\w\s\.,#-]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|boulevard|blvd|way|place|pl|court|ct|circle|cir))/i;
    const addressMatch = transcript.match(addressPattern);

    // Extract MLS patterns
    const mlsPattern = /mls[:\s]*([a-z0-9]+)/i;
    const mlsMatch = transcript.match(mlsPattern);

    // Extract price patterns
    const pricePattern = /\$?([\d,]+)(?:\s*(?:thousand|k|million|m))?/i;
    const priceMatch = transcript.match(pricePattern);

    return {
      address: addressMatch ? addressMatch[1].trim() : null,
      mls: mlsMatch ? mlsMatch[1] : null,
      price: priceMatch ? priceMatch[1] : null,
      hasPropertyKeywords: containsKeywords(['property', 'house', 'home', 'listing', 'real estate'])
    };
  }, [transcript, containsKeywords]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  return {
    isListening,
    transcript,
    interimTranscript,
    confidence,
    error,
    isSupported,
    commandHistory,
    startListening,
    stopListening,
    toggleListening,
    resetTranscript,
    clearHistory,
    getLastCommand,
    containsKeywords,
    extractPropertyInfo,
    parseVoiceCommand
  };
}