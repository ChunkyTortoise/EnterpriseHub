/**
 * Jorge Real Estate AI Platform - Network-Aware Loading Hook
 * Intelligent connection quality detection and adaptive loading strategies
 *
 * Features:
 * - Real-time connection quality monitoring
 * - Adaptive loading strategies based on network conditions
 * - Smart prefetching and caching decisions
 * - Bandwidth-aware data compression
 * - Network change detection and adaptation
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

export type NetworkQuality = 'excellent' | 'good' | 'fair' | 'poor' | 'offline';
export type ConnectionType = '4g' | '3g' | '2g' | 'slow-2g' | 'wifi' | 'ethernet' | 'unknown';

export interface NetworkConditions {
  // Connection details
  quality: NetworkQuality;
  connectionType: ConnectionType;
  isOnline: boolean;

  // Performance metrics
  effectiveType: string;
  downlink: number;        // Mbps
  rtt: number;            // Round-trip time in ms
  saveData: boolean;      // User preference for data savings

  // Calculated metrics
  qualityScore: number;   // 0-100
  isSlowConnection: boolean;
  isFastConnection: boolean;
  isUnmetered: boolean;

  // State
  isStable: boolean;
  lastQualityChange: number;
  connectionHistory: NetworkQuality[];
}

export interface AdaptiveLoadingConfig {
  // Image loading
  imageQuality: 'low' | 'medium' | 'high';
  enableLazyLoading: boolean;
  preloadImages: boolean;

  // API requests
  requestBatchSize: number;
  requestTimeout: number;
  enableCompression: boolean;
  priorityQueue: boolean;

  // Caching
  cacheStrategy: 'aggressive' | 'moderate' | 'minimal';
  prefetchRadius: number;    // Properties to prefetch around current location

  // Real-time features
  enableLiveUpdates: boolean;
  updateFrequency: number;   // ms between updates
  enableBackgroundSync: boolean;
}

const DEFAULT_CONFIG: AdaptiveLoadingConfig = {
  imageQuality: 'medium',
  enableLazyLoading: true,
  preloadImages: false,
  requestBatchSize: 5,
  requestTimeout: 10000,
  enableCompression: false,
  priorityQueue: false,
  cacheStrategy: 'moderate',
  prefetchRadius: 2,
  enableLiveUpdates: true,
  updateFrequency: 5000,
  enableBackgroundSync: true
};

// Network quality thresholds
const QUALITY_THRESHOLDS = {
  excellent: { downlink: 10, rtt: 50 },    // >10 Mbps, <50ms RTT
  good: { downlink: 4, rtt: 150 },         // >4 Mbps, <150ms RTT
  fair: { downlink: 1.5, rtt: 300 },       // >1.5 Mbps, <300ms RTT
  poor: { downlink: 0.5, rtt: 800 },       // >0.5 Mbps, <800ms RTT
  offline: { downlink: 0, rtt: Infinity }
};

export function useNetworkAware() {
  const [conditions, setConditions] = useState<NetworkConditions>({
    quality: 'good',
    connectionType: 'unknown',
    isOnline: navigator.onLine,
    effectiveType: 'unknown',
    downlink: 0,
    rtt: 0,
    saveData: false,
    qualityScore: 75,
    isSlowConnection: false,
    isFastConnection: false,
    isUnmetered: false,
    isStable: true,
    lastQualityChange: Date.now(),
    connectionHistory: []
  });

  const [config, setConfig] = useState<AdaptiveLoadingConfig>(DEFAULT_CONFIG);
  const stabilityTimeoutRef = useRef<NodeJS.Timeout>();
  const measurementIntervalRef = useRef<NodeJS.Timeout>();

  // Calculate network quality based on metrics
  const calculateQuality = useCallback((downlink: number, rtt: number): NetworkQuality => {
    if (!navigator.onLine) return 'offline';

    if (downlink >= QUALITY_THRESHOLDS.excellent.downlink && rtt <= QUALITY_THRESHOLDS.excellent.rtt) {
      return 'excellent';
    }
    if (downlink >= QUALITY_THRESHOLDS.good.downlink && rtt <= QUALITY_THRESHOLDS.good.rtt) {
      return 'good';
    }
    if (downlink >= QUALITY_THRESHOLDS.fair.downlink && rtt <= QUALITY_THRESHOLDS.fair.rtt) {
      return 'fair';
    }
    if (downlink >= QUALITY_THRESHOLDS.poor.downlink && rtt <= QUALITY_THRESHOLDS.poor.rtt) {
      return 'poor';
    }

    return 'poor';
  }, []);

  // Calculate quality score (0-100)
  const calculateQualityScore = useCallback((quality: NetworkQuality, downlink: number, rtt: number): number => {
    switch (quality) {
      case 'excellent': return Math.min(100, 90 + (downlink - 10) * 2);
      case 'good': return Math.min(89, 70 + (downlink - 4) * 3);
      case 'fair': return Math.min(69, 40 + (downlink - 1.5) * 20);
      case 'poor': return Math.min(39, 10 + downlink * 20);
      case 'offline': return 0;
      default: return 50;
    }
  }, []);

  // Detect connection type from effective type
  const getConnectionType = useCallback((effectiveType: string): ConnectionType => {
    switch (effectiveType) {
      case '4g': return '4g';
      case '3g': return '3g';
      case '2g': return '2g';
      case 'slow-2g': return 'slow-2g';
      default:
        // Try to detect based on connection info
        const connection = (navigator as any).connection;
        if (connection?.type) {
          if (connection.type === 'wifi' || connection.type === 'ethernet') {
            return connection.type as ConnectionType;
          }
        }
        return 'unknown';
    }
  }, []);

  // Update network conditions
  const updateConditions = useCallback(() => {
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;

    if (!connection) {
      // Fallback: Basic online/offline detection
      setConditions(prev => ({
        ...prev,
        isOnline: navigator.onLine,
        quality: navigator.onLine ? 'good' : 'offline'
      }));
      return;
    }

    const downlink = connection.downlink || 0;
    const rtt = connection.rtt || 0;
    const effectiveType = connection.effectiveType || 'unknown';
    const saveData = connection.saveData || false;

    const quality = calculateQuality(downlink, rtt);
    const qualityScore = calculateQualityScore(quality, downlink, rtt);
    const connectionType = getConnectionType(effectiveType);

    setConditions(prev => {
      const qualityChanged = prev.quality !== quality;
      const newHistory = qualityChanged
        ? [quality, ...prev.connectionHistory.slice(0, 9)] // Keep last 10
        : prev.connectionHistory;

      // Reset stability timer if quality changed
      if (qualityChanged) {
        if (stabilityTimeoutRef.current) {
          clearTimeout(stabilityTimeoutRef.current);
        }

        stabilityTimeoutRef.current = setTimeout(() => {
          setConditions(current => ({ ...current, isStable: true }));
        }, 5000); // Consider stable after 5 seconds
      }

      return {
        ...prev,
        quality,
        connectionType,
        isOnline: navigator.onLine,
        effectiveType,
        downlink,
        rtt,
        saveData,
        qualityScore,
        isSlowConnection: quality === 'poor' || quality === 'offline',
        isFastConnection: quality === 'excellent',
        isUnmetered: connectionType === 'wifi' || connectionType === 'ethernet',
        isStable: qualityChanged ? false : prev.isStable,
        lastQualityChange: qualityChanged ? Date.now() : prev.lastQualityChange,
        connectionHistory: newHistory
      };
    });
  }, [calculateQuality, calculateQualityScore, getConnectionType]);

  // Performance measurement via network requests
  const measurePerformance = useCallback(async () => {
    try {
      const startTime = performance.now();

      // Small test request to measure actual performance
      const response = await fetch('/api/health/ping', {
        method: 'GET',
        cache: 'no-store'
      });

      const endTime = performance.now();
      const actualRtt = endTime - startTime;

      if (response.ok) {
        // Update conditions with measured RTT
        setConditions(prev => {
          const measuredQuality = calculateQuality(prev.downlink, actualRtt);
          return {
            ...prev,
            rtt: actualRtt,
            quality: measuredQuality,
            qualityScore: calculateQualityScore(measuredQuality, prev.downlink, actualRtt)
          };
        });
      }
    } catch (error) {
      // Network error - likely offline or very poor connection
      setConditions(prev => ({
        ...prev,
        quality: 'offline',
        qualityScore: 0
      }));
    }
  }, [calculateQuality, calculateQualityScore]);

  // Auto-configure loading settings based on network conditions
  const updateLoadingConfig = useCallback((networkConditions: NetworkConditions) => {
    const newConfig: AdaptiveLoadingConfig = { ...DEFAULT_CONFIG };

    switch (networkConditions.quality) {
      case 'excellent':
        newConfig.imageQuality = 'high';
        newConfig.preloadImages = true;
        newConfig.requestBatchSize = 20;
        newConfig.requestTimeout = 15000;
        newConfig.cacheStrategy = 'aggressive';
        newConfig.prefetchRadius = 5;
        newConfig.updateFrequency = 2000;
        break;

      case 'good':
        newConfig.imageQuality = 'high';
        newConfig.preloadImages = false;
        newConfig.requestBatchSize = 10;
        newConfig.requestTimeout = 12000;
        newConfig.cacheStrategy = 'moderate';
        newConfig.prefetchRadius = 3;
        newConfig.updateFrequency = 3000;
        break;

      case 'fair':
        newConfig.imageQuality = 'medium';
        newConfig.preloadImages = false;
        newConfig.requestBatchSize = 5;
        newConfig.requestTimeout = 10000;
        newConfig.enableCompression = true;
        newConfig.cacheStrategy = 'moderate';
        newConfig.prefetchRadius = 2;
        newConfig.updateFrequency = 5000;
        break;

      case 'poor':
        newConfig.imageQuality = 'low';
        newConfig.preloadImages = false;
        newConfig.requestBatchSize = 2;
        newConfig.requestTimeout = 8000;
        newConfig.enableCompression = true;
        newConfig.priorityQueue = true;
        newConfig.cacheStrategy = 'minimal';
        newConfig.prefetchRadius = 1;
        newConfig.enableLiveUpdates = false;
        newConfig.updateFrequency = 10000;
        newConfig.enableBackgroundSync = false;
        break;

      case 'offline':
        newConfig.enableLiveUpdates = false;
        newConfig.enableBackgroundSync = false;
        newConfig.cacheStrategy = 'minimal';
        newConfig.prefetchRadius = 0;
        break;
    }

    // Respect user's data saving preference
    if (networkConditions.saveData) {
      newConfig.imageQuality = 'low';
      newConfig.preloadImages = false;
      newConfig.enableCompression = true;
      newConfig.requestBatchSize = Math.min(newConfig.requestBatchSize, 3);
      newConfig.prefetchRadius = Math.min(newConfig.prefetchRadius, 1);
      newConfig.enableLiveUpdates = false;
    }

    setConfig(newConfig);
  }, []);

  // Initialize and setup event listeners
  useEffect(() => {
    // Initial measurement
    updateConditions();
    measurePerformance();

    // Event listeners
    const handleOnline = () => {
      updateConditions();
      measurePerformance();
    };

    const handleOffline = () => {
      setConditions(prev => ({
        ...prev,
        isOnline: false,
        quality: 'offline',
        qualityScore: 0
      }));
    };

    const handleConnectionChange = () => {
      updateConditions();
      // Measure actual performance after a brief delay
      setTimeout(measurePerformance, 1000);
    };

    // Register event listeners
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    const connection = (navigator as any).connection;
    if (connection) {
      connection.addEventListener('change', handleConnectionChange);
    }

    // Periodic measurements (less frequent to save battery)
    measurementIntervalRef.current = setInterval(() => {
      updateConditions();
      if (Math.random() < 0.3) { // 30% chance to measure performance
        measurePerformance();
      }
    }, 30000); // Every 30 seconds

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);

      if (connection) {
        connection.removeEventListener('change', handleConnectionChange);
      }

      if (measurementIntervalRef.current) {
        clearInterval(measurementIntervalRef.current);
      }

      if (stabilityTimeoutRef.current) {
        clearTimeout(stabilityTimeoutRef.current);
      }
    };
  }, [updateConditions, measurePerformance]);

  // Auto-update config when conditions change
  useEffect(() => {
    updateLoadingConfig(conditions);
  }, [conditions.quality, conditions.saveData, updateLoadingConfig]);

  // Public API
  const isNetworkSuitable = useCallback((operation: 'sync' | 'upload' | 'download' | 'stream') => {
    switch (operation) {
      case 'sync':
        return conditions.quality !== 'offline' && conditions.isStable;
      case 'upload':
        return conditions.quality === 'excellent' || conditions.quality === 'good';
      case 'download':
        return conditions.quality !== 'offline' && conditions.quality !== 'poor';
      case 'stream':
        return conditions.quality === 'excellent';
      default:
        return conditions.isOnline;
    }
  }, [conditions]);

  const shouldDegrade = useCallback((feature: 'images' | 'animations' | 'realtime' | 'background') => {
    const isLowBandwidth = conditions.isSlowConnection || conditions.saveData;

    switch (feature) {
      case 'images':
        return isLowBandwidth;
      case 'animations':
        return conditions.quality === 'poor' || conditions.saveData;
      case 'realtime':
        return conditions.quality === 'poor' || conditions.quality === 'offline';
      case 'background':
        return !conditions.isUnmetered || conditions.saveData;
      default:
        return false;
    }
  }, [conditions]);

  const getOptimalTimeout = useCallback((baseTimeout: number = 5000): number => {
    const multiplier = {
      excellent: 1,
      good: 1.2,
      fair: 1.5,
      poor: 2,
      offline: 0
    }[conditions.quality] || 1;

    return Math.min(baseTimeout * multiplier, 30000); // Max 30 seconds
  }, [conditions.quality]);

  return {
    // Network state
    conditions,
    config,

    // Utilities
    isNetworkSuitable,
    shouldDegrade,
    getOptimalTimeout,

    // Manual controls
    measurePerformance,
    updateConditions,

    // Events (for UI feedback)
    isStable: conditions.isStable,
    qualityChanged: Date.now() - conditions.lastQualityChange < 5000,

    // Quick accessors
    isOnline: conditions.isOnline,
    quality: conditions.quality,
    isFast: conditions.isFastConnection,
    isSlow: conditions.isSlowConnection,
    shouldSaveData: conditions.saveData || conditions.isSlowConnection
  };
}

export default useNetworkAware;

// Jorge-specific network utilities
export const JorgeNetworkUtils = {
  /**
   * Get recommended image quality based on network conditions
   */
  getImageQuality: (conditions: NetworkConditions): 'low' | 'medium' | 'high' => {
    if (conditions.saveData || conditions.quality === 'poor') return 'low';
    if (conditions.quality === 'excellent') return 'high';
    return 'medium';
  },

  /**
   * Determine if property data should be prefetched
   */
  shouldPrefetchProperties: (conditions: NetworkConditions, userLocation?: { lat: number; lng: number }): boolean => {
    return conditions.quality !== 'offline' &&
           conditions.quality !== 'poor' &&
           conditions.isUnmetered &&
           !conditions.saveData &&
           !!userLocation;
  },

  /**
   * Get optimal batch size for API requests
   */
  getRequestBatchSize: (conditions: NetworkConditions, defaultSize: number = 10): number => {
    const factor = {
      excellent: 2,
      good: 1.5,
      fair: 1,
      poor: 0.5,
      offline: 0
    }[conditions.quality] || 1;

    return Math.max(1, Math.floor(defaultSize * factor));
  },

  /**
   * Check if real-time features should be enabled
   */
  shouldEnableRealTime: (conditions: NetworkConditions): boolean => {
    return conditions.quality !== 'offline' &&
           conditions.quality !== 'poor' &&
           conditions.isStable;
  }
};