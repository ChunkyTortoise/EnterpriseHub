// Voice Notes Types for Jorge's Real Estate AI Platform

export interface VoiceNote {
  id: string;
  propertyId?: string;
  leadId?: string;
  transcript: string;
  audioBlob: Blob;
  duration: number; // in seconds
  timestamp: number;
  location?: GeolocationCoordinates;
  category: VoiceNoteCategory;
  confidence: number; // 0-1 speech recognition confidence
  keywords: string[];
  actionItems: ActionItem[];
  sentiment: 'positive' | 'negative' | 'neutral';
  isProcessed?: boolean;
  metadata?: {
    audioLevel?: number;
    noiseLevel?: number;
    speechRate?: number;
    language?: string;
    deviceInfo?: string;
  };
}

export type VoiceNoteCategory =
  | 'property_features'
  | 'client_feedback'
  | 'follow_up_tasks'
  | 'market_observations'
  | 'showing_notes'
  | 'personal_memo';

export interface ActionItem {
  id: string;
  task: string;
  priority: 'low' | 'medium' | 'high';
  dueDate?: number;
  assignee?: string;
  isCompleted: boolean;
  extractedFrom: string; // transcript excerpt
}

export interface VoiceCommand {
  id: string;
  phrase: string;
  action: string;
  parameters?: Record<string, any>;
  confidence: number;
  timestamp: number;
}

export interface SpeechRecognitionResult {
  transcript: string;
  confidence: number;
  isFinal: boolean;
  alternatives?: Array<{
    transcript: string;
    confidence: number;
  }>;
}

export interface VoiceProcessingOptions {
  continuous?: boolean;
  interimResults?: boolean;
  maxAlternatives?: number;
  language?: string;
  grammars?: string[];
}

export interface AudioAnalysisResult {
  volume: number;
  pitch?: number;
  tempo?: number;
  clarity: number;
  noiseLevel: number;
  speechDetected: boolean;
}

export interface VoiceRecordingState {
  isRecording: boolean;
  isProcessing: boolean;
  isListening: boolean;
  isPaused: boolean;
  recordingDuration: number;
  audioLevel: number;
  error?: string;
}

export interface VoicePermissions {
  microphone: 'granted' | 'denied' | 'prompt';
  speechRecognition: boolean;
  location?: 'granted' | 'denied' | 'prompt';
}

// Real Estate specific voice recognition patterns
export interface RealEstateVocabulary {
  propertyTerms: string[];
  financialTerms: string[];
  locationTerms: string[];
  clientTerms: string[];
  actionTerms: string[];
}

export interface VoiceNoteAnalytics {
  totalNotes: number;
  totalDuration: number;
  averageConfidence: number;
  categoryCounts: Record<VoiceNoteCategory, number>;
  dailyActivity: Array<{
    date: string;
    noteCount: number;
    totalDuration: number;
  }>;
  topKeywords: Array<{
    keyword: string;
    count: number;
    category: VoiceNoteCategory;
  }>;
  actionItemStats: {
    total: number;
    completed: number;
    overdue: number;
    byPriority: Record<string, number>;
  };
}

// Jorge-specific voice note extensions
export interface JorgeVoiceNote extends VoiceNote {
  botAnalysis?: {
    temperature: 'hot' | 'warm' | 'cold';
    urgency: number; // 1-10 scale
    followUpRecommendations: string[];
    relatedProperties?: string[];
    clientSentiment?: {
      score: number; // -1 to 1
      keywords: string[];
      concerns: string[];
      interests: string[];
    };
  };
  commissionImpact?: {
    estimatedValue: number;
    probability: number; // 0-1
    timeline: string;
  };
}

export interface VoiceNoteExport {
  format: 'text' | 'audio' | 'json' | 'pdf';
  includeMetadata: boolean;
  includeActionItems: boolean;
  includeLocation: boolean;
  dateRange?: {
    start: number;
    end: number;
  };
  categories?: VoiceNoteCategory[];
}

export interface VoiceSearchQuery {
  query: string;
  categories?: VoiceNoteCategory[];
  dateRange?: {
    start: number;
    end: number;
  };
  keywords?: string[];
  minConfidence?: number;
  hasActionItems?: boolean;
  hasLocation?: boolean;
}

export interface VoiceIntegrationSettings {
  autoTranscribe: boolean;
  autoCategories: boolean;
  autoActionItems: boolean;
  autoKeywords: boolean;
  autoLocation: boolean;
  confidenceThreshold: number;
  maxRecordingDuration: number; // in seconds
  audioQuality: 'low' | 'medium' | 'high';
  offlineMode: boolean;
  syncOnWifi: boolean;
  deleteAfterSync: boolean;
}

export interface OfflineVoiceNote {
  note: VoiceNote;
  syncStatus: 'pending' | 'syncing' | 'synced' | 'failed';
  syncAttempts: number;
  lastSyncAttempt?: number;
}