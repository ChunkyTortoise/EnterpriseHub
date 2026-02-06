'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { VoiceNote, VoiceNoteCategory, VoiceRecordingState, SpeechRecognitionResult, ActionItem } from '@/types/voice';
import { SpeechProcessor } from '@/lib/voice/SpeechProcessor';
import { AudioManager } from '@/lib/voice/AudioManager';
import { VoiceAnalytics } from '@/lib/voice/VoiceAnalytics';
import { useOfflineStorage } from '@/hooks/useOfflineStorage';

export interface UseVoiceRecordingReturn {
  // State
  isRecording: boolean;
  isProcessing: boolean;
  isListening: boolean;
  currentNote: VoiceNote | null;
  voiceNotes: VoiceNote[];
  error: string | null;

  // Actions
  toggleRecording: () => Promise<void>;
  pauseRecording: () => void;
  resumeRecording: () => void;
  cancelRecording: () => void;
  deleteNote: (id: string) => void;
  exportNote: (id: string, format: 'text' | 'audio') => Promise<void>;

  // Voice Commands
  processVoiceCommand: (command: string) => void;

  // Settings
  permissions: {
    microphone: boolean;
    speechRecognition: boolean;
    location: boolean;
  };
}

export function useVoiceRecording(): UseVoiceRecordingReturn {
  // State
  const [recordingState, setRecordingState] = useState<VoiceRecordingState>({
    isRecording: false,
    isProcessing: false,
    isListening: false,
    isPaused: false,
    recordingDuration: 0,
    audioLevel: 0,
  });

  const [currentNote, setCurrentNote] = useState<VoiceNote | null>(null);
  const [voiceNotes, setVoiceNotes] = useState<VoiceNote[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [permissions, setPermissions] = useState({
    microphone: false,
    speechRecognition: false,
    location: false,
  });

  // Refs for audio processing
  const speechProcessor = useRef<SpeechProcessor | null>(null);
  const audioManager = useRef<AudioManager | null>(null);
  const voiceAnalytics = useRef<VoiceAnalytics | null>(null);
  const recordingStartTime = useRef<number>(0);
  const durationInterval = useRef<NodeJS.Timeout | null>(null);

  // Offline storage for voice notes
  const { saveData, getData, getAllData } = useOfflineStorage();

  // Initialize processors
  useEffect(() => {
    initializeProcessors();
    loadExistingNotes();
    checkPermissions();

    return () => {
      if (durationInterval.current) {
        clearInterval(durationInterval.current);
      }
    };
  }, []);

  const initializeProcessors = () => {
    try {
      speechProcessor.current = new SpeechProcessor({
        continuous: true,
        interimResults: true,
        language: 'en-US',
        maxAlternatives: 3,
      });

      audioManager.current = new AudioManager();
      voiceAnalytics.current = new VoiceAnalytics();

      // Set up speech recognition events
      speechProcessor.current.onResult = handleSpeechResult;
      speechProcessor.current.onError = handleSpeechError;
      speechProcessor.current.onStart = () => {
        setRecordingState(prev => ({ ...prev, isListening: true }));
      };
      speechProcessor.current.onEnd = () => {
        setRecordingState(prev => ({ ...prev, isListening: false }));
      };

      // Set up audio events
      audioManager.current.onAudioLevel = (level: number) => {
        setRecordingState(prev => ({ ...prev, audioLevel: level }));
      };

    } catch (err) {
      console.error('Failed to initialize voice processors:', err);
      setError('Failed to initialize voice recognition');
    }
  };

  const checkPermissions = async () => {
    try {
      // Check microphone permission
      const microphonePermission = await navigator.permissions.query({ name: 'microphone' as PermissionName });

      // Check speech recognition support
      const speechRecognitionSupport = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;

      // Check location permission (optional)
      let locationPermission = false;
      try {
        const geoPermission = await navigator.permissions.query({ name: 'geolocation' as PermissionName });
        locationPermission = geoPermission.state === 'granted';
      } catch {
        locationPermission = false;
      }

      setPermissions({
        microphone: microphonePermission.state === 'granted',
        speechRecognition: speechRecognitionSupport,
        location: locationPermission,
      });
    } catch (err) {
      console.error('Failed to check permissions:', err);
    }
  };

  const loadExistingNotes = async () => {
    try {
      const savedNotes = await getAllData('voice-notes');
      if (savedNotes) {
        const notes = Object.values(savedNotes) as VoiceNote[];
        setVoiceNotes(notes.sort((a, b) => b.timestamp - a.timestamp));
      }
    } catch (err) {
      console.error('Failed to load voice notes:', err);
    }
  };

  const handleSpeechResult = (result: SpeechRecognitionResult) => {
    if (currentNote) {
      setCurrentNote(prev => ({
        ...prev!,
        transcript: result.transcript,
        confidence: result.confidence,
      }));

      // Process voice commands if detected
      if (result.isFinal) {
        processVoiceCommand(result.transcript);
      }
    }
  };

  const handleSpeechError = (error: string) => {
    console.error('Speech recognition error:', error);
    setError(error);
  };

  const startRecordingTimer = () => {
    recordingStartTime.current = Date.now();
    durationInterval.current = setInterval(() => {
      const duration = Math.floor((Date.now() - recordingStartTime.current) / 1000);
      setRecordingState(prev => ({ ...prev, recordingDuration: duration }));
    }, 1000);
  };

  const stopRecordingTimer = () => {
    if (durationInterval.current) {
      clearInterval(durationInterval.current);
      durationInterval.current = null;
    }
  };

  const toggleRecording = async () => {
    try {
      if (!recordingState.isRecording) {
        // Start recording
        await startRecording();
      } else {
        // Stop recording
        await stopRecording();
      }
    } catch (err) {
      console.error('Recording error:', err);
      setError(err instanceof Error ? err.message : 'Recording failed');
    }
  };

  const startRecording = async () => {
    setError(null);
    setRecordingState(prev => ({ ...prev, isProcessing: true }));

    try {
      // Request microphone permission if not granted
      if (!permissions.microphone) {
        await navigator.mediaDevices.getUserMedia({ audio: true });
      }

      // Start audio recording
      await audioManager.current?.startRecording();

      // Start speech recognition
      speechProcessor.current?.start();

      // Get location if available
      let location: GeolocationCoordinates | undefined;
      if (permissions.location) {
        try {
          const position = await new Promise<GeolocationPosition>((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, {
              timeout: 5000,
              maximumAge: 60000,
            });
          });
          location = position.coords;
        } catch {
          // Location optional, continue without it
        }
      }

      // Create new note
      const newNote: VoiceNote = {
        id: `voice-note-${Date.now()}`,
        transcript: '',
        audioBlob: new Blob(),
        duration: 0,
        timestamp: Date.now(),
        location,
        category: 'personal_memo', // Default category
        confidence: 0,
        keywords: [],
        actionItems: [],
        sentiment: 'neutral',
      };

      setCurrentNote(newNote);
      setRecordingState(prev => ({
        ...prev,
        isRecording: true,
        isProcessing: false,
        recordingDuration: 0,
      }));

      startRecordingTimer();

    } catch (err) {
      console.error('Failed to start recording:', err);
      setError('Failed to start recording. Please check microphone permissions.');
      setRecordingState(prev => ({ ...prev, isProcessing: false }));
    }
  };

  const stopRecording = async () => {
    setRecordingState(prev => ({ ...prev, isProcessing: true }));

    try {
      // Stop timers
      stopRecordingTimer();

      // Stop audio recording and get blob
      const audioBlob = await audioManager.current?.stopRecording();

      // Stop speech recognition
      speechProcessor.current?.stop();

      if (currentNote && audioBlob) {
        // Analyze the note
        const analyzedNote = await analyzeVoiceNote({
          ...currentNote,
          audioBlob,
          duration: recordingState.recordingDuration,
        });

        // Save to offline storage
        await saveData(`voice-notes/${analyzedNote.id}`, analyzedNote);

        // Add to notes list
        setVoiceNotes(prev => [analyzedNote, ...prev]);

        // Clear current note
        setCurrentNote(null);
      }

      setRecordingState(prev => ({
        ...prev,
        isRecording: false,
        isProcessing: false,
        recordingDuration: 0,
      }));

    } catch (err) {
      console.error('Failed to stop recording:', err);
      setError('Failed to save recording');
      setRecordingState(prev => ({ ...prev, isProcessing: false }));
    }
  };

  const analyzeVoiceNote = async (note: VoiceNote): Promise<VoiceNote> => {
    if (!voiceAnalytics.current) return note;

    try {
      // Extract keywords
      const keywords = voiceAnalytics.current.extractKeywords(note.transcript);

      // Extract action items
      const actionItems = voiceAnalytics.current.extractActionItems(note.transcript);

      // Categorize the note
      const category = voiceAnalytics.current.categorizeNote(note.transcript);

      // Analyze sentiment
      const sentiment = voiceAnalytics.current.analyzeSentiment(note.transcript);

      return {
        ...note,
        keywords,
        actionItems,
        category,
        sentiment,
        isProcessed: true,
      };
    } catch (err) {
      console.error('Failed to analyze voice note:', err);
      return note;
    }
  };

  const pauseRecording = () => {
    audioManager.current?.pauseRecording();
    speechProcessor.current?.stop();
    stopRecordingTimer();
    setRecordingState(prev => ({ ...prev, isPaused: true }));
  };

  const resumeRecording = () => {
    audioManager.current?.resumeRecording();
    speechProcessor.current?.start();
    startRecordingTimer();
    setRecordingState(prev => ({ ...prev, isPaused: false }));
  };

  const cancelRecording = () => {
    stopRecordingTimer();
    audioManager.current?.cancelRecording();
    speechProcessor.current?.stop();
    setCurrentNote(null);
    setRecordingState(prev => ({
      ...prev,
      isRecording: false,
      isProcessing: false,
      isPaused: false,
      recordingDuration: 0,
    }));
  };

  const deleteNote = async (id: string) => {
    try {
      // Remove from storage
      await saveData(`voice-notes/${id}`, null);

      // Remove from state
      setVoiceNotes(prev => prev.filter(note => note.id !== id));
    } catch (err) {
      console.error('Failed to delete note:', err);
      setError('Failed to delete note');
    }
  };

  const exportNote = async (id: string, format: 'text' | 'audio') => {
    try {
      const note = voiceNotes.find(n => n.id === id);
      if (!note) return;

      if (format === 'text') {
        // Create text file
        const text = `Voice Note - ${new Date(note.timestamp).toLocaleString()}\n\n${note.transcript}`;
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `voice-note-${note.id}.txt`;
        a.click();

        URL.revokeObjectURL(url);
      } else if (format === 'audio') {
        // Export audio file
        const url = URL.createObjectURL(note.audioBlob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `voice-note-${note.id}.wav`;
        a.click();

        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Failed to export note:', err);
      setError('Failed to export note');
    }
  };

  const processVoiceCommand = useCallback((command: string) => {
    const lowerCommand = command.toLowerCase().trim();

    // Voice command patterns for Jorge's platform
    if (lowerCommand.includes('start recording') || lowerCommand.includes('begin recording')) {
      if (!recordingState.isRecording) {
        toggleRecording();
      }
    } else if (lowerCommand.includes('stop recording') || lowerCommand.includes('end recording')) {
      if (recordingState.isRecording) {
        toggleRecording();
      }
    } else if (lowerCommand.includes('property note')) {
      if (currentNote) {
        setCurrentNote(prev => prev ? { ...prev, category: 'property_features' } : null);
      }
    } else if (lowerCommand.includes('client feedback') || lowerCommand.includes('client reaction')) {
      if (currentNote) {
        setCurrentNote(prev => prev ? { ...prev, category: 'client_feedback' } : null);
      }
    } else if (lowerCommand.includes('follow up') || lowerCommand.includes('follow-up') || lowerCommand.includes('task')) {
      if (currentNote) {
        setCurrentNote(prev => prev ? { ...prev, category: 'follow_up_tasks' } : null);
      }
    } else if (lowerCommand.includes('showing note') || lowerCommand.includes('showing')) {
      if (currentNote) {
        setCurrentNote(prev => prev ? { ...prev, category: 'showing_notes' } : null);
      }
    } else if (lowerCommand.includes('market') || lowerCommand.includes('neighborhood')) {
      if (currentNote) {
        setCurrentNote(prev => prev ? { ...prev, category: 'market_observations' } : null);
      }
    }
  }, [recordingState.isRecording, currentNote, toggleRecording]);

  return {
    // State
    isRecording: recordingState.isRecording,
    isProcessing: recordingState.isProcessing,
    isListening: recordingState.isListening,
    currentNote,
    voiceNotes,
    error,

    // Actions
    toggleRecording,
    pauseRecording,
    resumeRecording,
    cancelRecording,
    deleteNote,
    exportNote,

    // Voice Commands
    processVoiceCommand,

    // Settings
    permissions,
  };
}