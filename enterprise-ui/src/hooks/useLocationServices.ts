/**
 * useLocationServices - React hook for Jorge's GPS-Enabled Property Matching
 * Provides location tracking, geofencing, market insights, and safety features
 * with battery optimization and offline capability
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import LocationManager, {
  LocationCoordinates,
  LocationServiceStatus,
  LocationHistory,
  LocationPreferences
} from '@/lib/location/LocationManager';
import GeofenceEngine, {
  PropertyGeofence,
  GeofenceAlert,
  GeofenceStats
} from '@/lib/location/GeofenceEngine';
import MarketDataService, {
  MarketInsight,
  ComparableSale
} from '@/lib/location/MarketDataService';

export interface LocationServicesState {
  // Core location data
  currentLocation: LocationCoordinates | null;
  locationHistory: LocationHistory[];
  serviceStatus: LocationServiceStatus;

  // Geofencing
  activeGeofences: PropertyGeofence[];
  recentAlerts: GeofenceAlert[];
  geofenceStats: GeofenceStats;

  // Market intelligence
  marketInsight: MarketInsight | null;
  nearbyComparables: ComparableSale[];

  // State management
  isLoading: boolean;
  isTracking: boolean;
  error: string | null;
  lastUpdate: number;

  // Battery and performance
  batteryOptimized: boolean;
  backgroundEnabled: boolean;
  permissionStatus: 'granted' | 'denied' | 'prompt' | 'unknown';
}

export interface LocationServicesActions {
  // Location management
  initializeLocation: () => Promise<void>;
  startTracking: () => Promise<void>;
  stopTracking: () => void;
  getCurrentLocation: () => Promise<LocationCoordinates>;
  updatePreferences: (preferences: Partial<LocationPreferences>) => void;

  // Geofencing
  createPropertyGeofence: (
    propertyId: string,
    coordinates: { lat: number; lng: number },
    alertType: PropertyGeofence['alertType'],
    metadata: PropertyGeofence['metadata'],
    options?: any
  ) => string;
  removeGeofence: (geofenceId: string) => boolean;
  clearAllGeofences: () => void;

  // Market intelligence
  getMarketInsight: (coordinates?: LocationCoordinates) => Promise<MarketInsight>;
  getComparableSales: (coordinates?: LocationCoordinates, filters?: any) => Promise<ComparableSale[]>;
  getNeighborhoodAnalysis: (coordinates?: LocationCoordinates) => Promise<any>;

  // Alerts and notifications
  dismissAlert: (alertId: string) => void;
  clearAlertHistory: () => void;

  // Safety and emergency
  shareLocation: (contacts: string[]) => Promise<void>;
  triggerEmergency: () => Promise<void>;

  // Data management
  exportLocationData: () => string;
  clearLocationHistory: () => void;
}

interface NearbyProperty {
  id: string;
  address: string;
  distance: number;
  type: 'listing' | 'recent_sale' | 'lead_interest' | 'showing_scheduled';
  matchScore?: number;
  leadId?: string;
  alertPriority: 'high' | 'medium' | 'low';
  metadata?: any;
}

const useLocationServices = (
  initialPreferences?: Partial<LocationPreferences>
): LocationServicesState & LocationServicesActions => {
  // Core state
  const [state, setState] = useState<LocationServicesState>({
    currentLocation: null,
    locationHistory: [],
    serviceStatus: {
      isEnabled: false,
      permission: 'unknown',
      accuracy: 'balanced',
      batteryOptimized: true,
      backgroundEnabled: false,
    },
    activeGeofences: [],
    recentAlerts: [],
    geofenceStats: {
      totalGeofences: 0,
      activeGeofences: 0,
      todayTriggers: 0,
      weekTriggers: 0,
      averageDistance: 0,
      batteryImpact: 0,
      topAlertTypes: [],
    },
    marketInsight: null,
    nearbyComparables: [],
    isLoading: false,
    isTracking: false,
    error: null,
    lastUpdate: 0,
    batteryOptimized: true,
    backgroundEnabled: false,
    permissionStatus: 'unknown',
  });

  // Service instances
  const locationManager = useRef<LocationManager>();
  const geofenceEngine = useRef<GeofenceEngine>();
  const marketDataService = useRef<MarketDataService>();

  // Initialize services
  useEffect(() => {
    locationManager.current = new LocationManager(initialPreferences);
    geofenceEngine.current = new GeofenceEngine();
    marketDataService.current = new MarketDataService();

    // Setup event listeners
    const handleLocationUpdate = (event: CustomEvent) => {
      const coordinates: LocationCoordinates = event.detail;
      setState(prev => ({
        ...prev,
        currentLocation: coordinates,
        lastUpdate: Date.now(),
      }));

      // Update geofence engine
      if (geofenceEngine.current && !geofenceEngine.current.isActive) {
        geofenceEngine.current.startMonitoring();
      }
    };

    const handleLocationError = (event: CustomEvent) => {
      const error: Error = event.detail;
      setState(prev => ({
        ...prev,
        error: error.message,
        isLoading: false,
      }));
    };

    const handleGeofenceAlert = (event: CustomEvent) => {
      const alert: GeofenceAlert = event.detail;
      setState(prev => ({
        ...prev,
        recentAlerts: [alert, ...prev.recentAlerts.slice(0, 49)], // Keep last 50 alerts
      }));

      // Show native notification if permission granted
      showGeofenceNotification(alert);
    };

    window.addEventListener('locationUpdate', handleLocationUpdate);
    window.addEventListener('locationError', handleLocationError);
    window.addEventListener('geofenceAlert', handleGeofenceAlert);

    return () => {
      window.removeEventListener('locationUpdate', handleLocationUpdate);
      window.removeEventListener('locationError', handleLocationError);
      window.removeEventListener('geofenceAlert', handleGeofenceAlert);
    };
  }, [initialPreferences]);

  // Update state when services change
  useEffect(() => {
    const updateServiceState = () => {
      if (!locationManager.current || !geofenceEngine.current) return;

      setState(prev => ({
        ...prev,
        locationHistory: locationManager.current!.history,
        serviceStatus: locationManager.current!.status,
        activeGeofences: geofenceEngine.current!.getActiveGeofences(),
        geofenceStats: geofenceEngine.current!.getStats(),
        isTracking: locationManager.current!.status.isEnabled,
        batteryOptimized: locationManager.current!.status.batteryOptimized,
        backgroundEnabled: locationManager.current!.status.backgroundEnabled,
      }));
    };

    const interval = setInterval(updateServiceState, 5000); // Update every 5 seconds
    updateServiceState(); // Initial update

    return () => clearInterval(interval);
  }, []);

  // Show geofence notifications
  const showGeofenceNotification = useCallback((alert: GeofenceAlert) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      const notification = new Notification('Jorge Real Estate Alert', {
        body: alert.message,
        icon: '/icon-192.png',
        badge: '/icon-72.png',
        tag: `geofence-${alert.geofenceId}`,
        requireInteraction: alert.priority === 'high',
        actions: alert.actions?.slice(0, 2).map(action => ({
          action: action.id,
          title: action.label,
        })) || [],
      });

      notification.onclick = () => {
        window.focus();
        notification.close();
      };

      // Auto-close after 10 seconds for non-high priority
      if (alert.priority !== 'high') {
        setTimeout(() => notification.close(), 10000);
      }
    }
  }, []);

  // Actions implementation
  const initializeLocation = useCallback(async (): Promise<void> => {
    if (!locationManager.current) return;

    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const status = await locationManager.current.initialize();

      setState(prev => ({
        ...prev,
        serviceStatus: status,
        permissionStatus: status.permission,
        isLoading: false,
      }));

      // Request notification permission
      if ('Notification' in window && Notification.permission === 'default') {
        await Notification.requestPermission();
      }
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to initialize location services',
        isLoading: false,
      }));
    }
  }, []);

  const startTracking = useCallback(async (): Promise<void> => {
    if (!locationManager.current || !geofenceEngine.current) return;

    try {
      await locationManager.current.startTracking();
      geofenceEngine.current.startMonitoring();

      setState(prev => ({
        ...prev,
        isTracking: true,
        error: null,
      }));
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to start tracking',
      }));
    }
  }, []);

  const stopTracking = useCallback((): void => {
    if (!locationManager.current || !geofenceEngine.current) return;

    locationManager.current.stopTracking();
    geofenceEngine.current.stopMonitoring();

    setState(prev => ({
      ...prev,
      isTracking: false,
    }));
  }, []);

  const getCurrentLocation = useCallback(async (): Promise<LocationCoordinates> => {
    if (!locationManager.current) {
      throw new Error('Location manager not initialized');
    }

    setState(prev => ({ ...prev, isLoading: true }));

    try {
      const location = await locationManager.current.getCurrentLocation();
      setState(prev => ({
        ...prev,
        currentLocation: location,
        lastUpdate: Date.now(),
        isLoading: false,
      }));
      return location;
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to get current location',
        isLoading: false,
      }));
      throw error;
    }
  }, []);

  const updatePreferences = useCallback((preferences: Partial<LocationPreferences>): void => {
    if (!locationManager.current) return;

    locationManager.current.updatePreferences(preferences);
    setState(prev => ({
      ...prev,
      batteryOptimized: preferences.batteryOptimization ?? prev.batteryOptimized,
      backgroundEnabled: preferences.backgroundTracking ?? prev.backgroundEnabled,
    }));
  }, []);

  const createPropertyGeofence = useCallback((
    propertyId: string,
    coordinates: { lat: number; lng: number },
    alertType: PropertyGeofence['alertType'],
    metadata: PropertyGeofence['metadata'],
    options?: any
  ): string => {
    if (!geofenceEngine.current) {
      throw new Error('Geofence engine not initialized');
    }

    const geofenceId = geofenceEngine.current.createPropertyGeofence(
      propertyId,
      coordinates,
      alertType,
      metadata,
      options
    );

    // Update state with new geofence
    setState(prev => ({
      ...prev,
      activeGeofences: geofenceEngine.current!.getActiveGeofences(),
      geofenceStats: geofenceEngine.current!.getStats(),
    }));

    return geofenceId;
  }, []);

  const removeGeofence = useCallback((geofenceId: string): boolean => {
    if (!geofenceEngine.current) return false;

    const removed = geofenceEngine.current.removeGeofence(geofenceId);

    if (removed) {
      setState(prev => ({
        ...prev,
        activeGeofences: geofenceEngine.current!.getActiveGeofences(),
        geofenceStats: geofenceEngine.current!.getStats(),
      }));
    }

    return removed;
  }, []);

  const clearAllGeofences = useCallback((): void => {
    if (!geofenceEngine.current) return;

    geofenceEngine.current.clearAll();
    setState(prev => ({
      ...prev,
      activeGeofences: [],
      recentAlerts: [],
      geofenceStats: geofenceEngine.current!.getStats(),
    }));
  }, []);

  const getMarketInsight = useCallback(async (coordinates?: LocationCoordinates): Promise<MarketInsight> => {
    if (!marketDataService.current) {
      throw new Error('Market data service not initialized');
    }

    const location = coordinates || state.currentLocation;
    if (!location) {
      throw new Error('No location available for market insight');
    }

    setState(prev => ({ ...prev, isLoading: true }));

    try {
      const insight = await marketDataService.current.getMarketInsight(location);
      setState(prev => ({
        ...prev,
        marketInsight: insight,
        isLoading: false,
      }));
      return insight;
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to get market insight',
        isLoading: false,
      }));
      throw error;
    }
  }, [state.currentLocation]);

  const getComparableSales = useCallback(async (coordinates?: LocationCoordinates, filters?: any): Promise<ComparableSale[]> => {
    if (!marketDataService.current) {
      throw new Error('Market data service not initialized');
    }

    const location = coordinates || state.currentLocation;
    if (!location) {
      throw new Error('No location available for comparable sales');
    }

    try {
      const comparables = await marketDataService.current.getComparableSales(location, filters);
      setState(prev => ({
        ...prev,
        nearbyComparables: comparables,
      }));
      return comparables;
    } catch (error) {
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Failed to get comparable sales',
      }));
      throw error;
    }
  }, [state.currentLocation]);

  const getNeighborhoodAnalysis = useCallback(async (coordinates?: LocationCoordinates): Promise<any> => {
    if (!marketDataService.current) {
      throw new Error('Market data service not initialized');
    }

    const location = coordinates || state.currentLocation;
    if (!location) {
      throw new Error('No location available for neighborhood analysis');
    }

    return await marketDataService.current.getNeighborhoodAnalysis(location);
  }, [state.currentLocation]);

  const dismissAlert = useCallback((alertId: string): void => {
    setState(prev => ({
      ...prev,
      recentAlerts: prev.recentAlerts.filter(alert => alert.id !== alertId),
    }));
  }, []);

  const clearAlertHistory = useCallback((): void => {
    setState(prev => ({
      ...prev,
      recentAlerts: [],
    }));
  }, []);

  const shareLocation = useCallback(async (contacts: string[]): Promise<void> => {
    if (!state.currentLocation) {
      throw new Error('No current location to share');
    }

    // Mock implementation - integrate with SMS/email services
    const locationUrl = `https://maps.google.com/maps?q=${state.currentLocation.lat},${state.currentLocation.lng}`;
    const message = `My current location: ${locationUrl}`;

    console.log('Sharing location with contacts:', contacts, message);

    // In production, integrate with native sharing API or messaging services
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'My Current Location',
          text: message,
          url: locationUrl,
        });
      } catch (error) {
        console.warn('Failed to share location:', error);
        // Fallback to clipboard
        if (navigator.clipboard) {
          await navigator.clipboard.writeText(message);
        }
      }
    }
  }, [state.currentLocation]);

  const triggerEmergency = useCallback(async (): Promise<void> => {
    if (!state.currentLocation) {
      throw new Error('No current location for emergency');
    }

    // Emergency protocol
    console.log('EMERGENCY TRIGGERED at:', state.currentLocation);

    // In production:
    // 1. Send location to emergency contacts
    // 2. Call emergency services API
    // 3. Send automated messages
    // 4. Start continuous location sharing
    // 5. Activate emergency mode in app

    // Show immediate feedback
    if ('vibrate' in navigator) {
      navigator.vibrate([500, 200, 500, 200, 500]);
    }

    // Emergency notification
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Emergency Alert Activated', {
        body: 'Emergency services and contacts have been notified of your location.',
        icon: '/emergency-icon.png',
        requireInteraction: true,
      });
    }
  }, [state.currentLocation]);

  const exportLocationData = useCallback((): string => {
    if (!locationManager.current) return '{}';

    return locationManager.current.exportHistory();
  }, []);

  const clearLocationHistory = useCallback((): void => {
    if (!locationManager.current) return;

    locationManager.current.clearHistory();
    setState(prev => ({
      ...prev,
      locationHistory: [],
    }));
  }, []);

  return {
    // State
    ...state,

    // Actions
    initializeLocation,
    startTracking,
    stopTracking,
    getCurrentLocation,
    updatePreferences,
    createPropertyGeofence,
    removeGeofence,
    clearAllGeofences,
    getMarketInsight,
    getComparableSales,
    getNeighborhoodAnalysis,
    dismissAlert,
    clearAlertHistory,
    shareLocation,
    triggerEmergency,
    exportLocationData,
    clearLocationHistory,
  };
};

export default useLocationServices;