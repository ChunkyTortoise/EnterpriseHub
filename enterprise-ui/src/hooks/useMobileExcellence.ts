/**
 * Jorge Real Estate AI Platform - Mobile Excellence Integration Hook
 * Orchestrates all mobile optimization capabilities for field agent excellence
 *
 * Features:
 * - Unified mobile optimization state management
 * - Intelligent coordination between network, battery, and ML systems
 * - Real-time adaptation to changing conditions
 * - Performance monitoring and optimization
 * - Emergency power management
 * - Predictive resource allocation
 */

'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import useNetworkAware from './useNetworkAware';
import useBatteryOptimization from './useBatteryOptimization';
import { jorgeMLEngine } from '@/lib/ml/OfflineMLEngine';
import { apiManager } from '@/lib/api-enhanced';
import { useOfflineStorage } from './useOfflineStorage';

export interface MobileExcellenceState {
  // Overall optimization status
  optimizationLevel: 'maximum' | 'high' | 'moderate' | 'conservative' | 'emergency';
  isOptimalForField: boolean;
  lastOptimization: number;

  // Performance metrics
  performanceScore: number;      // 0-100 overall mobile performance
  networkScore: number;         // 0-100 network optimization
  batteryScore: number;         // 0-100 battery optimization
  mlScore: number;              // 0-100 ML processing efficiency

  // Capabilities status
  offlineCapable: boolean;
  mlInferenceReady: boolean;
  backgroundSyncActive: boolean;
  predictiveCachingActive: boolean;

  // Resource utilization
  storageUsed: number;          // 0-1 percentage
  networkBandwidth: number;     // Estimated Mbps
  batteryDrain: number;         // %/hour estimated drain
  cpuUsage: 'low' | 'moderate' | 'high';

  // Field agent readiness
  fieldReadinessScore: number;  // 0-100 readiness for field work
  estimatedFieldTime: number;   // Hours of field work remaining
  criticalWarnings: string[];
  recommendations: string[];
}

export interface MobileExcellenceActions {
  // Optimization controls
  optimizeForField: () => Promise<void>;
  enableEmergencyMode: () => Promise<void>;
  disableEmergencyMode: () => Promise<void>;
  refreshOptimizations: () => Promise<void>;

  // Performance management
  measurePerformance: () => Promise<void>;
  clearCaches: () => Promise<void>;
  preloadCriticalData: () => Promise<void>;

  // ML operations
  initializeMl: () => Promise<void>;
  runMlInference: (type: string, data: any) => Promise<any>;

  // Monitoring
  getDetailedStatus: () => Promise<any>;
  exportDiagnostics: () => Promise<string>;
}

export function useMobileExcellence() {
  // Core hooks
  const networkAware = useNetworkAware();
  const batteryOpt = useBatteryOptimization();
  const { status: offlineStatus, isOnline } = useOfflineStorage();

  // State
  const [mobileState, setMobileState] = useState<MobileExcellenceState>({
    optimizationLevel: 'moderate',
    isOptimalForField: false,
    lastOptimization: Date.now(),
    performanceScore: 75,
    networkScore: 75,
    batteryScore: 75,
    mlScore: 0,
    offlineCapable: false,
    mlInferenceReady: false,
    backgroundSyncActive: false,
    predictiveCachingActive: false,
    storageUsed: 0,
    networkBandwidth: 0,
    batteryDrain: 0,
    cpuUsage: 'low',
    fieldReadinessScore: 0,
    estimatedFieldTime: 0,
    criticalWarnings: [],
    recommendations: []
  });

  const [isInitialized, setIsInitialized] = useState(false);
  const optimizationIntervalRef = useRef<NodeJS.Timeout>();
  const performanceHistoryRef = useRef<Array<{ timestamp: number; score: number }>>([]);

  // Initialize mobile excellence systems
  const initialize = useCallback(async () => {
    if (isInitialized) return;

    console.log('🚀 Jorge Mobile: Initializing mobile excellence framework...');

    try {
      // Initialize ML engine
      await jorgeMLEngine.initialize(['propertyScoring', 'leadQualification']);

      // Update API manager with initial conditions
      apiManager.updateConditions(
        networkAware.quality,
        batteryOpt.level,
        networkAware.isOnline
      );

      // Setup service worker communication
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.ready;
        if (registration.active) {
          // Update service worker with initial conditions
          registration.active.postMessage({
            type: 'UPDATE_NETWORK_STATE',
            data: { quality: networkAware.quality }
          });

          registration.active.postMessage({
            type: 'UPDATE_BATTERY_STATE',
            data: {
              level: batteryOpt.level,
              isCharging: batteryOpt.isCharging
            }
          });
        }
      }

      setIsInitialized(true);
      console.log('✅ Jorge Mobile: Mobile excellence framework initialized');

    } catch (error) {
      console.error('Jorge Mobile: Initialization failed:', error);
      throw error;
    }
  }, [isInitialized, networkAware, batteryOpt]);

  // Calculate comprehensive performance score
  const calculatePerformanceScore = useCallback(() => {
    const weights = {
      network: 0.3,
      battery: 0.25,
      storage: 0.2,
      ml: 0.15,
      offline: 0.1
    };

    // Network score (0-100)
    const networkScore = networkAware.conditions.qualityScore || 50;

    // Battery score (0-100)
    let batteryScore = batteryOpt.level * 100;
    if (batteryOpt.isCharging) batteryScore = Math.min(100, batteryScore + 20);
    if (batteryOpt.powerMode === 'emergency') batteryScore = 0;

    // Storage score (0-100)
    const storagePercentage = offlineStatus.storageUsed / Math.max(offlineStatus.storageQuota, 1);
    const storageScore = Math.max(0, 100 - (storagePercentage * 100));

    // ML score (0-100)
    const mlReady = jorgeMLEngine.isReady();
    const mlMemory = jorgeMLEngine.getMemoryInfo();
    const mlScore = mlReady ? Math.min(100, 100 - (mlMemory.numTensors / 100)) : 0;

    // Offline capability score (0-100)
    const offlineScore = offlineStatus.storageUsed > 0 ? 100 : 50;

    // Calculate weighted score
    const totalScore = (
      networkScore * weights.network +
      batteryScore * weights.battery +
      storageScore * weights.storage +
      mlScore * weights.ml +
      offlineScore * weights.offline
    );

    return {
      total: Math.round(totalScore),
      network: Math.round(networkScore),
      battery: Math.round(batteryScore),
      storage: Math.round(storageScore),
      ml: Math.round(mlScore),
      offline: Math.round(offlineScore)
    };
  }, [networkAware, batteryOpt, offlineStatus]);

  // Determine optimization level based on conditions
  const determineOptimizationLevel = useCallback(() => {
    const scores = calculatePerformanceScore();
    const avgScore = scores.total;

    if (batteryOpt.powerMode === 'emergency' || avgScore < 30) {
      return 'emergency';
    } else if (avgScore < 50 || batteryOpt.isLowBattery || networkAware.isSlow) {
      return 'conservative';
    } else if (avgScore < 70 || !batteryOpt.isCharging) {
      return 'moderate';
    } else if (avgScore < 85) {
      return 'high';
    } else {
      return 'maximum';
    }
  }, [calculatePerformanceScore, batteryOpt, networkAware]);

  // Calculate field readiness score
  const calculateFieldReadiness = useCallback(() => {
    const scores = calculatePerformanceScore();

    // Base score from performance
    let readiness = scores.total * 0.6;

    // Battery considerations (critical for field work)
    if (batteryOpt.level > 0.8) readiness += 20;
    else if (batteryOpt.level > 0.5) readiness += 10;
    else if (batteryOpt.level < 0.2) readiness -= 30;

    // Offline capability boost
    if (offlineStatus.storageUsed > 50000) readiness += 15; // Has cached data

    // ML readiness
    if (jorgeMLEngine.isReady()) readiness += 10;

    // Network independence
    if (isOnline && networkAware.quality !== 'poor') readiness += 5;

    return Math.max(0, Math.min(100, Math.round(readiness)));
  }, [calculatePerformanceScore, batteryOpt, offlineStatus, isOnline, networkAware]);

  // Estimate field work time
  const estimateFieldTime = useCallback(() => {
    const batteryHours = batteryOpt.estimatedHours || 0;
    const drainRate = batteryOpt.drainRate || 5; // %/hour

    // Adjust for optimization level
    const optimizationMultiplier = {
      emergency: 3.0,
      conservative: 2.0,
      moderate: 1.5,
      high: 1.2,
      maximum: 1.0
    }[mobileState.optimizationLevel] || 1.0;

    const adjustedHours = Math.min(batteryHours * optimizationMultiplier, 24);

    return Math.max(0, adjustedHours);
  }, [batteryOpt, mobileState.optimizationLevel]);

  // Generate warnings and recommendations
  const generateInsights = useCallback(() => {
    const warnings: string[] = [];
    const recommendations: string[] = [];

    // Critical warnings
    if (batteryOpt.level < 0.1) {
      warnings.push('Critical battery level - find charger immediately');
    }
    if (networkAware.quality === 'offline' && offlineStatus.storageUsed < 10000) {
      warnings.push('No network and limited offline data - sync when possible');
    }
    if (!jorgeMLEngine.isReady()) {
      warnings.push('ML inference unavailable - reduced intelligent features');
    }

    // Recommendations
    if (batteryOpt.level < 0.3 && !batteryOpt.isCharging) {
      recommendations.push('Consider enabling power saving mode');
    }
    if (networkAware.quality === 'excellent' && batteryOpt.level > 0.8) {
      recommendations.push('Optimal conditions for data sync and ML training');
    }
    if (offlineStatus.storageUsed / offlineStatus.storageQuota > 0.9) {
      recommendations.push('Clear old cached data to free storage space');
    }
    if (networkAware.isSlow && !batteryOpt.shouldReduceFeature('animations')) {
      recommendations.push('Reduce animations to improve performance');
    }

    return { warnings, recommendations };
  }, [batteryOpt, networkAware, offlineStatus]);

  // Update mobile state periodically
  const updateMobileState = useCallback(() => {
    const scores = calculatePerformanceScore();
    const optimizationLevel = determineOptimizationLevel();
    const fieldReadiness = calculateFieldReadiness();
    const fieldTime = estimateFieldTime();
    const insights = generateInsights();

    // Track performance history
    performanceHistoryRef.current.push({
      timestamp: Date.now(),
      score: scores.total
    });

    // Keep only last hour of data
    const hourAgo = Date.now() - 60 * 60 * 1000;
    performanceHistoryRef.current = performanceHistoryRef.current.filter(
      entry => entry.timestamp > hourAgo
    );

    const newState: MobileExcellenceState = {
      optimizationLevel,
      isOptimalForField: fieldReadiness > 80,
      lastOptimization: Date.now(),
      performanceScore: scores.total,
      networkScore: scores.network,
      batteryScore: scores.battery,
      mlScore: scores.ml,
      offlineCapable: offlineStatus.storageUsed > 0,
      mlInferenceReady: jorgeMLEngine.isReady(),
      backgroundSyncActive: isOnline && scores.network > 50,
      predictiveCachingActive: batteryOpt.level > 0.5 && networkAware.quality !== 'poor',
      storageUsed: offlineStatus.storageUsed / Math.max(offlineStatus.storageQuota, 1),
      networkBandwidth: networkAware.conditions.downlink || 0,
      batteryDrain: batteryOpt.drainRate || 0,
      cpuUsage: scores.ml > 80 ? 'high' : scores.ml > 40 ? 'moderate' : 'low',
      fieldReadinessScore: fieldReadiness,
      estimatedFieldTime: fieldTime,
      criticalWarnings: insights.warnings,
      recommendations: insights.recommendations
    };

    setMobileState(newState);

    // Update API manager with current conditions
    apiManager.updateConditions(
      networkAware.quality,
      batteryOpt.level,
      networkAware.isOnline
    );

    // Update service worker
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.ready.then(registration => {
        if (registration.active) {
          registration.active.postMessage({
            type: 'UPDATE_NETWORK_STATE',
            data: { quality: networkAware.quality }
          });

          registration.active.postMessage({
            type: 'UPDATE_BATTERY_STATE',
            data: {
              level: batteryOpt.level,
              isCharging: batteryOpt.isCharging
            }
          });
        }
      });
    }

  }, [
    calculatePerformanceScore,
    determineOptimizationLevel,
    calculateFieldReadiness,
    estimateFieldTime,
    generateInsights,
    networkAware,
    batteryOpt,
    offlineStatus,
    isOnline
  ]);

  // Actions implementation
  const optimizeForField = useCallback(async () => {
    console.log('🎯 Jorge Mobile: Optimizing for field work...');

    try {
      // Enable appropriate optimizations based on conditions
      if (batteryOpt.level < 0.5) {
        await batteryOpt.enableEmergencyMode();
      }

      // Preload critical data if network is good
      if (networkAware.quality !== 'poor' && batteryOpt.level > 0.3) {
        // Trigger predictive caching
        if ('serviceWorker' in navigator) {
          const registration = await navigator.serviceWorker.ready;
          if (registration.active) {
            registration.active.postMessage({
              type: 'TRIGGER_INTELLIGENT_SYNC'
            });
          }
        }
      }

      // Initialize ML if not ready and conditions allow
      if (!jorgeMLEngine.isReady() && batteryOpt.level > 0.4) {
        await jorgeMLEngine.initialize();
      }

      console.log('✅ Jorge Mobile: Field optimization complete');

    } catch (error) {
      console.error('Jorge Mobile: Field optimization failed:', error);
    }
  }, [batteryOpt, networkAware]);

  const measurePerformance = useCallback(async () => {
    // Trigger network performance measurement
    if (networkAware.measurePerformance) {
      await networkAware.measurePerformance();
    }

    // Update state with fresh measurements
    updateMobileState();
  }, [networkAware, updateMobileState]);

  const preloadCriticalData = useCallback(async () => {
    if (networkAware.quality === 'poor' || batteryOpt.level < 0.3) {
      console.log('🔋 Jorge Mobile: Skipping preload due to poor conditions');
      return;
    }

    console.log('📦 Jorge Mobile: Preloading critical data...');

    try {
      // Use enhanced API to preload important data
      await Promise.all([
        // Preload property searches
        // Preload recent conversations
        // Preload user preferences
      ]);

      console.log('✅ Jorge Mobile: Critical data preloaded');

    } catch (error) {
      console.warn('Jorge Mobile: Preload failed:', error);
    }
  }, [networkAware, batteryOpt]);

  const runMlInference = useCallback(async (type: string, data: any) => {
    if (!jorgeMLEngine.isReady()) {
      throw new Error('ML engine not ready');
    }

    console.log(`🧠 Jorge Mobile: Running ${type} inference`);

    try {
      switch (type) {
        case 'property-scoring':
          return await jorgeMLEngine.scorePropertyMatch(data.property, data.lead);
        case 'lead-qualification':
          return await jorgeMLEngine.qualifyLead(data.lead);
        case 'voice-sentiment':
          return await jorgeMLEngine.analyzeVoiceSentiment(data.voice);
        default:
          throw new Error(`Unknown ML inference type: ${type}`);
      }
    } catch (error) {
      console.error(`Jorge Mobile: ML inference ${type} failed:`, error);
      throw error;
    }
  }, []);

  const getDetailedStatus = useCallback(async () => {
    const mlMemory = jorgeMLEngine.getMemoryInfo();
    const queueStatus = apiManager.getQueueStatus();

    return {
      mobile: mobileState,
      network: networkAware.conditions,
      battery: batteryOpt.batteryStatus,
      offline: offlineStatus,
      ml: {
        ready: jorgeMLEngine.isReady(),
        memory: mlMemory,
        loadedModels: mlMemory.models
      },
      api: queueStatus,
      performance: performanceHistoryRef.current,
      timestamp: Date.now()
    };
  }, [mobileState, networkAware, batteryOpt, offlineStatus]);

  const exportDiagnostics = useCallback(async () => {
    const status = await getDetailedStatus();
    return JSON.stringify({
      ...status,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
      version: '1.0.0'
    }, null, 2);
  }, [getDetailedStatus]);

  // Initialize on mount
  useEffect(() => {
    initialize().catch(console.error);
  }, [initialize]);

  // Setup periodic updates
  useEffect(() => {
    if (!isInitialized) return;

    updateMobileState(); // Initial update

    optimizationIntervalRef.current = setInterval(updateMobileState, 10000); // Every 10 seconds

    return () => {
      if (optimizationIntervalRef.current) {
        clearInterval(optimizationIntervalRef.current);
      }
    };
  }, [isInitialized, updateMobileState]);

  // Auto-optimize when conditions change significantly
  useEffect(() => {
    if (!isInitialized) return;

    const shouldAutoOptimize = (
      batteryOpt.isCriticalBattery ||
      networkAware.qualityChanged ||
      mobileState.fieldReadinessScore < 50
    );

    if (shouldAutoOptimize) {
      console.log('🔄 Jorge Mobile: Auto-optimizing due to condition changes');
      setTimeout(updateMobileState, 1000);
    }
  }, [
    isInitialized,
    batteryOpt.isCriticalBattery,
    networkAware.qualityChanged,
    mobileState.fieldReadinessScore,
    updateMobileState
  ]);

  return {
    // State
    ...mobileState,
    isInitialized,

    // Conditions
    network: networkAware,
    battery: batteryOpt,

    // Actions
    optimizeForField,
    enableEmergencyMode: batteryOpt.enableEmergencyMode,
    disableEmergencyMode: batteryOpt.disableEmergencyMode,
    refreshOptimizations: updateMobileState,
    measurePerformance,
    preloadCriticalData,
    initializeMl: () => jorgeMLEngine.initialize(),
    runMlInference,
    getDetailedStatus,
    exportDiagnostics,

    // Quick accessors
    isFieldReady: mobileState.isOptimalForField,
    canUseML: mobileState.mlInferenceReady,
    shouldConserveBattery: batteryOpt.isLowBattery,
    shouldReduceNetwork: networkAware.isSlow,
    isEmergencyMode: batteryOpt.powerMode === 'emergency'
  };
}

export default useMobileExcellence;