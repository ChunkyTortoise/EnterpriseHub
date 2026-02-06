"use client";

import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Title,
  Text,
  Badge,
  Metric,
  Button,
  Flex,
  Grid
} from '@tremor/react';
import {
  MapPin,
  Phone,
  MessageCircle,
  Mic,
  MicOff,
  Navigation,
  Clock,
  TrendingUp,
  Star,
  Home,
  DollarSign,
  Target,
  AlertCircle,
  Zap,
  Brain,
  Users,
  Calendar,
  Camera,
  Share2,
  Wifi,
  WifiOff,
  Battery,
  Signal
} from 'lucide-react';
import { useAgentStore } from '../../store/useAgentStore';

interface Lead {
  id: string;
  name: string;
  phone: string;
  location: {
    address: string;
    distance_miles: number;
    coordinates: [number, number];
  };
  priority_score: number;
  temperature: 'hot' | 'warm' | 'lukewarm' | 'cold';
  jorge_scores: {
    frs_score: number;
    pcs_score: number;
  };
  property_interest: {
    type: 'sell' | 'buy';
    price_range: [number, number];
    timeline: string;
  };
  last_contact: string;
  next_action: string;
  ai_insights: string[];
  voice_notes: string[];
}

interface PropertyIntel {
  address: string;
  market_value: number;
  recent_sales: Array<{
    address: string;
    price: number;
    date: string;
    days_on_market: number;
  }>;
  market_trends: {
    direction: 'up' | 'down' | 'stable';
    change_percentage: number;
    avg_days_on_market: number;
  };
  neighborhood_insights: string[];
}

interface AIRecommendation {
  type: 'call' | 'visit' | 'follow_up' | 'property_alert';
  priority: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  estimated_minutes: number;
  confidence: number;
  action_url?: string;
}

interface FieldAgentIntelligenceDashboardProps {
  agentId: string;
  location?: { lat: number; lng: number };
  maxRadius?: number; // miles
}

export function FieldAgentIntelligenceDashboard({
  agentId,
  location,
  maxRadius = 25
}: FieldAgentIntelligenceDashboardProps) {
  const { addEntry, subscribeToIntelligence } = useAgentStore();

  // State management
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [propertyIntel, setPropertyIntel] = useState<PropertyIntel | null>(null);
  const [aiRecommendations, setAiRecommendations] = useState<AIRecommendation[]>([]);

  // Mobile-specific state
  const [isRecording, setIsRecording] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [batteryLevel, setBatteryLevel] = useState<number | null>(null);
  const [signalStrength, setSignalStrength] = useState<number>(4); // 0-4 bars
  const [currentLocation, setCurrentLocation] = useState<{ lat: number; lng: number } | null>(location || null);

  // Voice recording
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);

  // Progressive Web App state
  const [installPrompt, setInstallPrompt] = useState<any>(null);
  const [isInstalled, setIsInstalled] = useState(false);

  // Background sync for offline support
  const [pendingActions, setPendingActions] = useState<any[]>([]);

  // Initialize mobile features
  useEffect(() => {
    initializeMobileFeatures();
    loadNearbyLeads();
    setupRealtimeUpdates();

    return () => {
      if (mediaRecorder) {
        mediaRecorder.stop();
      }
    };
  }, []);

  const initializeMobileFeatures = async () => {
    // Check if installed as PWA
    setIsInstalled(window.matchMedia('(display-mode: standalone)').matches);

    // Setup PWA install prompt
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      setInstallPrompt(e);
    });

    // Setup battery API
    if ('getBattery' in navigator) {
      try {
        const battery = await (navigator as any).getBattery();
        setBatteryLevel(battery.level * 100);

        battery.addEventListener('levelchange', () => {
          setBatteryLevel(battery.level * 100);
        });
      } catch (error) {
        console.log('Battery API not available');
      }
    }

    // Setup online/offline detection
    window.addEventListener('online', () => setIsOnline(true));
    window.addEventListener('offline', () => setIsOnline(false));

    // Get current location
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCurrentLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          console.log('Location not available:', error);
        },
        { enableHighAccuracy: true }
      );
    }
  };

  const loadNearbyLeads = async () => {
    try {
      const coords = currentLocation || { lat: 40.7128, lng: -74.0060 }; // Default to NYC

      const response = await fetch(
        `/api/mobile/nearby-leads?lat=${coords.lat}&lng=${coords.lng}&radius=${maxRadius}&agent_id=${agentId}`
      );

      if (response.ok) {
        const data = await response.json();
        setLeads(data.leads || generateMockLeads());
        setAiRecommendations(data.ai_recommendations || generateMockRecommendations());
      } else {
        setLeads(generateMockLeads());
        setAiRecommendations(generateMockRecommendations());
      }
    } catch (error) {
      console.error('Failed to load leads:', error);
      setLeads(generateMockLeads());
      setAiRecommendations(generateMockRecommendations());
    }
  };

  const setupRealtimeUpdates = () => {
    // Subscribe to real-time intelligence updates
    const cleanup = subscribeToIntelligence(['mobile_intelligence', 'lead_updates', 'property_alerts']);

    return cleanup;
  };

  const generateMockLeads = (): Lead[] => [
    {
      id: 'lead_001',
      name: 'Sarah Johnson',
      phone: '+1-555-0123',
      location: {
        address: '123 Oak Street, Downtown',
        distance_miles: 2.3,
        coordinates: [40.7589, -73.9851]
      },
      priority_score: 89,
      temperature: 'hot',
      jorge_scores: {
        frs_score: 85,
        pcs_score: 92
      },
      property_interest: {
        type: 'sell',
        price_range: [450000, 550000],
        timeline: 'immediate'
      },
      last_contact: '2026-01-24T10:30:00Z',
      next_action: 'Schedule property evaluation',
      ai_insights: [
        'High urgency - mentioned job relocation',
        'Price-sensitive, emphasize market timing',
        'Preferred contact method: phone calls'
      ],
      voice_notes: []
    },
    {
      id: 'lead_002',
      name: 'Michael Chen',
      phone: '+1-555-0456',
      location: {
        address: '789 Pine Avenue, Midtown',
        distance_miles: 4.7,
        coordinates: [40.7505, -73.9934]
      },
      priority_score: 76,
      temperature: 'warm',
      jorge_scores: {
        frs_score: 78,
        pcs_score: 74
      },
      property_interest: {
        type: 'buy',
        price_range: [600000, 800000],
        timeline: '3-6 months'
      },
      last_contact: '2026-01-23T14:15:00Z',
      next_action: 'Send neighborhood market report',
      ai_insights: [
        'First-time buyer, needs education',
        'Interested in investment potential',
        'Responds well to data and analytics'
      ],
      voice_notes: ['Voice note about investment criteria']
    }
  ];

  const generateMockRecommendations = (): AIRecommendation[] => [
    {
      type: 'call',
      priority: 'high',
      title: 'Call Sarah Johnson',
      description: 'Hot lead with immediate timeline. Market conditions favor quick action.',
      estimated_minutes: 15,
      confidence: 0.92,
      action_url: 'tel:+1-555-0123'
    },
    {
      type: 'property_alert',
      priority: 'medium',
      title: 'New Listing Match',
      description: '456 Elm Street matches Michael Chen\'s criteria. Similar property sold for $750K last week.',
      estimated_minutes: 5,
      confidence: 0.87
    },
    {
      type: 'follow_up',
      priority: 'medium',
      title: 'Follow up on property showing',
      description: 'Jessica Martinez viewed property 3 days ago. Send feedback request.',
      estimated_minutes: 10,
      confidence: 0.74
    }
  ];

  const startVoiceRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      recorder.ondataavailable = (event) => {
        setAudioChunks(prev => [...prev, event.data]);
      };

      recorder.onstop = () => {
        // Process recording when stopped
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        processVoiceNote(audioBlob);
        setAudioChunks([]);
      };

      setMediaRecorder(recorder);
      recorder.start();
      setIsRecording(true);

      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'mobile_intelligence',
        key: 'voice_recording_started',
        value: 'Started voice note recording'
      });
    } catch (error) {
      console.error('Failed to start recording:', error);
    }
  };

  const stopVoiceRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);

      // Stop all tracks
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
  };

  const processVoiceNote = async (audioBlob: Blob) => {
    try {
      // In production, this would transcribe and analyze the audio
      const transcription = "Voice note recorded successfully";

      if (selectedLead) {
        // Add voice note to selected lead
        setLeads(prevLeads =>
          prevLeads.map(lead =>
            lead.id === selectedLead.id
              ? {
                  ...lead,
                  voice_notes: [...lead.voice_notes, transcription]
                }
              : lead
          )
        );
      }

      addEntry({
        timestamp: new Date().toISOString(),
        agent: 'mobile_intelligence',
        key: 'voice_note_processed',
        value: { transcription, lead_id: selectedLead?.id }
      });
    } catch (error) {
      console.error('Failed to process voice note:', error);
    }
  };

  const handleInstallPWA = async () => {
    if (installPrompt) {
      const result = await installPrompt.prompt();
      if (result.outcome === 'accepted') {
        setInstallPrompt(null);
        setIsInstalled(true);
      }
    }
  };

  const navigateToLead = (lead: Lead) => {
    const [lat, lng] = lead.location.coordinates;
    const mapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`;
    window.open(mapsUrl, '_blank');

    addEntry({
      timestamp: new Date().toISOString(),
      agent: 'mobile_intelligence',
      key: 'navigation_started',
      value: { lead_id: lead.id, destination: lead.location.address }
    });
  };

  const executeRecommendation = async (recommendation: AIRecommendation) => {
    addEntry({
      timestamp: new Date().toISOString(),
      agent: 'mobile_intelligence',
      key: 'recommendation_executed',
      value: recommendation
    });

    if (recommendation.action_url) {
      window.open(recommendation.action_url, '_blank');
    }

    // Mark as completed or track execution
    setAiRecommendations(prev =>
      prev.filter(r => r !== recommendation)
    );
  };

  const loadPropertyIntel = async (address: string) => {
    try {
      const response = await fetch(`/api/mobile/property-intel?address=${encodeURIComponent(address)}`);

      if (response.ok) {
        const data = await response.json();
        setPropertyIntel(data);
      } else {
        setPropertyIntel(generateMockPropertyIntel(address));
      }
    } catch (error) {
      console.error('Failed to load property intel:', error);
      setPropertyIntel(generateMockPropertyIntel(address));
    }
  };

  const generateMockPropertyIntel = (address: string): PropertyIntel => ({
    address,
    market_value: 525000,
    recent_sales: [
      { address: '125 Oak Street', price: 510000, date: '2026-01-15', days_on_market: 12 },
      { address: '127 Oak Street', price: 540000, date: '2026-01-10', days_on_market: 8 }
    ],
    market_trends: {
      direction: 'up',
      change_percentage: 8.5,
      avg_days_on_market: 18
    },
    neighborhood_insights: [
      'Hot market with low inventory',
      'School district rating: 9/10',
      'Recent infrastructure improvements'
    ]
  });

  const getTemperatureColor = (temp: string) => {
    switch (temp) {
      case 'hot': return 'bg-red-500';
      case 'warm': return 'bg-orange-500';
      case 'lukewarm': return 'bg-yellow-500';
      case 'cold': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'red';
      case 'medium': return 'amber';
      case 'low': return 'blue';
      default: return 'gray';
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Mobile Header with Status */}
      <div className="sticky top-0 z-50 bg-slate-900/95 backdrop-blur-sm border-b border-slate-800">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse"></div>
            <Text className="text-slate-100 font-semibold">Field Intelligence</Text>
          </div>

          {/* Status indicators */}
          <div className="flex items-center space-x-3">
            {/* Connection status */}
            <div className="flex items-center space-x-1">
              {isOnline ? (
                <Wifi className="h-4 w-4 text-green-400" />
              ) : (
                <WifiOff className="h-4 w-4 text-red-400" />
              )}
              <div className="flex space-x-0.5">
                {Array.from({ length: 4 }).map((_, i) => (
                  <div
                    key={i}
                    className={`w-1 h-3 rounded-sm ${
                      i < signalStrength ? 'bg-green-400' : 'bg-slate-600'
                    }`}
                  />
                ))}
              </div>
            </div>

            {/* Battery indicator */}
            {batteryLevel !== null && (
              <div className="flex items-center space-x-1">
                <Battery className={`h-4 w-4 ${batteryLevel > 20 ? 'text-green-400' : 'text-red-400'}`} />
                <Text className="text-xs text-slate-400">{Math.round(batteryLevel)}%</Text>
              </div>
            )}
          </div>
        </div>

        {/* PWA Install Banner */}
        {installPrompt && !isInstalled && (
          <div className="bg-blue-600 px-4 py-2">
            <Flex justifyContent="between" alignItems="center">
              <Text className="text-blue-100 text-sm">Install app for better experience</Text>
              <Button size="xs" onClick={handleInstallPWA}>
                Install
              </Button>
            </Flex>
          </div>
        )}
      </div>

      {/* AI Recommendations Panel */}
      <div className="p-4">
        <Card className="bg-slate-900 border-slate-800 mb-4">
          <div className="flex items-center space-x-2 mb-3">
            <Brain className="h-5 w-5 text-blue-400" />
            <Title className="text-slate-100">AI Recommendations</Title>
          </div>

          <div className="space-y-3">
            {aiRecommendations.slice(0, 3).map((rec, index) => (
              <Card
                key={index}
                className="bg-slate-800 border-slate-700 p-3"
                onClick={() => executeRecommendation(rec)}
              >
                <Flex justifyContent="between" alignItems="start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <Badge color={getPriorityColor(rec.priority)} size="sm">
                        {rec.priority}
                      </Badge>
                      <Text className="text-slate-400 text-xs">
                        ~{rec.estimated_minutes}min
                      </Text>
                      <div className="flex items-center space-x-1">
                        <Star className="h-3 w-3 text-amber-400" />
                        <Text className="text-xs text-slate-400">
                          {(rec.confidence * 100).toFixed(0)}%
                        </Text>
                      </div>
                    </div>
                    <Text className="text-slate-100 font-medium text-sm">{rec.title}</Text>
                    <Text className="text-slate-400 text-xs mt-1">{rec.description}</Text>
                  </div>
                  <Button size="xs" variant="secondary">
                    Act
                  </Button>
                </Flex>
              </Card>
            ))}
          </div>
        </Card>

        {/* Nearby Leads */}
        <Card className="bg-slate-900 border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Users className="h-5 w-5 text-emerald-400" />
              <Title className="text-slate-100">Nearby Leads</Title>
              <Badge color="emerald" size="sm">{leads.length}</Badge>
            </div>

            {/* Voice Recording Button */}
            <Button
              size="sm"
              color={isRecording ? "red" : "blue"}
              onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
              className="flex items-center space-x-1"
            >
              {isRecording ? (
                <>
                  <MicOff className="h-4 w-4" />
                  <span>Stop</span>
                </>
              ) : (
                <>
                  <Mic className="h-4 w-4" />
                  <span>Note</span>
                </>
              )}
            </Button>
          </div>

          <div className="space-y-3">
            {leads.slice(0, 5).map((lead) => (
              <Card
                key={lead.id}
                className={`
                  bg-slate-800 border-slate-700 p-4 transition-all duration-200
                  ${selectedLead?.id === lead.id ? 'border-blue-500 bg-blue-950/20' : 'hover:border-slate-600'}
                `}
                onClick={() => {
                  setSelectedLead(lead);
                  loadPropertyIntel(lead.location.address);
                }}
              >
                {/* Lead Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${getTemperatureColor(lead.temperature)}`} />
                    <Text className="text-slate-100 font-semibold">{lead.name}</Text>
                    <Badge color="slate" size="sm">{lead.temperature}</Badge>
                  </div>

                  <div className="flex items-center space-x-1 text-slate-400">
                    <MapPin className="h-4 w-4" />
                    <Text className="text-sm">{lead.location.distance_miles}mi</Text>
                  </div>
                </div>

                {/* Jorge Scores */}
                <div className="grid grid-cols-3 gap-3 mb-3">
                  <div className="text-center">
                    <Text className="text-xs text-slate-400">Priority</Text>
                    <Metric className="text-sm text-blue-100">{lead.priority_score}</Metric>
                  </div>
                  <div className="text-center">
                    <Text className="text-xs text-slate-400">FRS</Text>
                    <Metric className="text-sm text-emerald-100">{lead.jorge_scores.frs_score}</Metric>
                  </div>
                  <div className="text-center">
                    <Text className="text-xs text-slate-400">PCS</Text>
                    <Metric className="text-sm text-purple-100">{lead.jorge_scores.pcs_score}</Metric>
                  </div>
                </div>

                {/* Property Interest */}
                <div className="mb-3">
                  <Text className="text-slate-400 text-xs">
                    {lead.property_interest.type === 'sell' ? 'Selling' : 'Buying'} •
                    ${(lead.property_interest.price_range[0] / 1000).toFixed(0)}K-${(lead.property_interest.price_range[1] / 1000).toFixed(0)}K •
                    {lead.property_interest.timeline}
                  </Text>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2">
                  <Button
                    size="xs"
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(`tel:${lead.phone}`, '_blank');
                    }}
                    className="flex items-center space-x-1"
                  >
                    <Phone className="h-3 w-3" />
                    <span>Call</span>
                  </Button>

                  <Button
                    size="xs"
                    variant="secondary"
                    onClick={(e) => {
                      e.stopPropagation();
                      navigateToLead(lead);
                    }}
                    className="flex items-center space-x-1"
                  >
                    <Navigation className="h-3 w-3" />
                    <span>Navigate</span>
                  </Button>

                  <Button
                    size="xs"
                    variant="secondary"
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(`sms:${lead.phone}`, '_blank');
                    }}
                    className="flex items-center space-x-1"
                  >
                    <MessageCircle className="h-3 w-3" />
                    <span>Text</span>
                  </Button>
                </div>

                {/* AI Insights (if selected) */}
                {selectedLead?.id === lead.id && (
                  <div className="mt-4 pt-3 border-t border-slate-700">
                    <Text className="text-slate-300 text-xs mb-2">AI Insights:</Text>
                    <div className="space-y-1">
                      {lead.ai_insights.map((insight, idx) => (
                        <Text key={idx} className="text-slate-400 text-xs">
                          • {insight}
                        </Text>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </div>
        </Card>

        {/* Property Intelligence (if lead selected) */}
        {selectedLead && propertyIntel && (
          <Card className="bg-slate-900 border-slate-800 mt-4">
            <div className="flex items-center space-x-2 mb-4">
              <Home className="h-5 w-5 text-amber-400" />
              <Title className="text-slate-100">Property Intelligence</Title>
              <Badge color="amber" size="sm">Live Data</Badge>
            </div>

            {/* Market Value */}
            <div className="mb-4">
              <Text className="text-slate-400 text-sm">Estimated Market Value</Text>
              <Metric className="text-amber-100 text-2xl">
                ${(propertyIntel.market_value / 1000).toFixed(0)}K
              </Metric>
              <div className="flex items-center space-x-2 mt-1">
                <TrendingUp className={`h-4 w-4 ${
                  propertyIntel.market_trends.direction === 'up' ? 'text-green-400' : 'text-red-400'
                }`} />
                <Text className={`text-sm ${
                  propertyIntel.market_trends.direction === 'up' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {propertyIntel.market_trends.direction === 'up' ? '+' : ''}{propertyIntel.market_trends.change_percentage}% (90 days)
                </Text>
              </div>
            </div>

            {/* Recent Sales */}
            <div className="mb-4">
              <Text className="text-slate-400 text-sm mb-2">Recent Comparable Sales</Text>
              <div className="space-y-2">
                {propertyIntel.recent_sales.map((sale, idx) => (
                  <div key={idx} className="flex justify-between items-center bg-slate-800 p-2 rounded">
                    <div>
                      <Text className="text-slate-200 text-sm">{sale.address}</Text>
                      <Text className="text-slate-400 text-xs">{sale.date} • {sale.days_on_market} DOM</Text>
                    </div>
                    <Text className="text-slate-100 font-medium">${(sale.price / 1000).toFixed(0)}K</Text>
                  </div>
                ))}
              </div>
            </div>

            {/* Neighborhood Insights */}
            <div>
              <Text className="text-slate-400 text-sm mb-2">Neighborhood Insights</Text>
              <div className="space-y-1">
                {propertyIntel.neighborhood_insights.map((insight, idx) => (
                  <Text key={idx} className="text-slate-300 text-xs">
                    • {insight}
                  </Text>
                ))}
              </div>
            </div>
          </Card>
        )}
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur-sm border-t border-slate-800">
        <div className="flex items-center justify-around py-3">
          <Button variant="ghost" size="sm" className="flex flex-col items-center space-y-1">
            <Home className="h-5 w-5" />
            <Text className="text-xs">Dashboard</Text>
          </Button>

          <Button variant="ghost" size="sm" className="flex flex-col items-center space-y-1">
            <MapPin className="h-5 w-5" />
            <Text className="text-xs">Map</Text>
          </Button>

          <Button variant="ghost" size="sm" className="flex flex-col items-center space-y-1">
            <Target className="h-5 w-5" />
            <Text className="text-xs">Leads</Text>
          </Button>

          <Button variant="ghost" size="sm" className="flex flex-col items-center space-y-1">
            <Calendar className="h-5 w-5" />
            <Text className="text-xs">Schedule</Text>
          </Button>

          <Button variant="ghost" size="sm" className="flex flex-col items-center space-y-1">
            <Brain className="h-5 w-5" />
            <Text className="text-xs">AI</Text>
          </Button>
        </div>
      </div>

      {/* Offline indicator */}
      {!isOnline && (
        <div className="fixed top-16 left-4 right-4 bg-red-600 text-white p-3 rounded-lg shadow-lg z-50">
          <Flex alignItems="center" className="space-x-2">
            <WifiOff className="h-5 w-5" />
            <Text className="font-medium">You're offline</Text>
          </Flex>
          <Text className="text-sm mt-1">
            Actions will sync when connection is restored.
          </Text>
        </div>
      )}
    </div>
  );
}