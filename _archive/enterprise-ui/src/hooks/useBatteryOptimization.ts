/**
 * Jorge Real Estate AI Platform - Battery Optimization Hook
 * Intelligent power management for all-day field agent use
 *
 * Features:
 * - Real-time battery monitoring with Battery API
 * - Adaptive performance scaling based on battery level
 * - Power-aware feature degradation
 * - Charging status optimization
 * - Background activity throttling
 * - Emergency power preservation mode
 */

'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

export type BatteryLevel = 'critical' | 'low' | 'medium' | 'high' | 'full';
export type PowerMode = 'maximum' | 'balanced' | 'power-saver' | 'emergency';

export interface BatteryStatus {
  // Core battery data
  level: number;              // 0-1 (percentage)
  isCharging: boolean;
  chargingTime: number;       // seconds (Infinity if not charging)
  dischargingTime: number;    // seconds (Infinity if charging)

  // Calculated status
  batteryLevel: BatteryLevel;
  estimatedHours: number;     // Hours remaining
  isLowBattery: boolean;
  isCriticalBattery: boolean;

  // Power optimization
  powerMode: PowerMode;
  previousLevel: number;
  drainRate: number;          // % per minute
  lastUpdate: number;
  isStable: boolean;

  // Optimization state
  backgroundThrottled: boolean;
  animationsReduced: boolean;
  locationReducedAccuracy: boolean;
  screenBrightnessOptimized: boolean;
}

export interface PowerOptimizationConfig {
  // Battery thresholds
  criticalThreshold: number;    // 0.05 (5%)
  lowThreshold: number;         // 0.20 (20%)
  mediumThreshold: number;      // 0.50 (50%)

  // Feature controls
  reduceAnimationsAt: number;   // 0.30 (30%)
  throttleBackgroundAt: number; // 0.25 (25%)
  reducePrecisionAt: number;    // 0.15 (15%)
  emergencyModeAt: number;      // 0.10 (10%)

  // Performance tuning
  locationFrequencyNormal: number;     // 5000ms
  locationFrequencyReduced: number;    // 15000ms
  locationFrequencyEmergency: number;  // 60000ms

  syncFrequencyNormal: number;         // 30000ms
  syncFrequencyReduced: number;        // 60000ms
  syncFrequencyEmergency: number;      // 300000ms

  // UI optimizations
  animationDuration: {
    normal: number;
    reduced: number;
    minimal: number;
  };

  // Network optimizations
  requestTimeoutNormal: number;        // 10000ms
  requestTimeoutReduced: number;       // 5000ms
  maxConcurrentRequests: {
    normal: number;
    reduced: number;
    emergency: number;
  };
}

const DEFAULT_CONFIG: PowerOptimizationConfig = {
  criticalThreshold: 0.05,
  lowThreshold: 0.20,
  mediumThreshold: 0.50,
  reduceAnimationsAt: 0.30,
  throttleBackgroundAt: 0.25,
  reducePrecisionAt: 0.15,
  emergencyModeAt: 0.10,
  locationFrequencyNormal: 5000,
  locationFrequencyReduced: 15000,
  locationFrequencyEmergency: 60000,
  syncFrequencyNormal: 30000,
  syncFrequencyReduced: 60000,
  syncFrequencyEmergency: 300000,
  animationDuration: {
    normal: 300,
    reduced: 150,
    minimal: 0
  },
  requestTimeoutNormal: 10000,
  requestTimeoutReduced: 5000,
  maxConcurrentRequests: {
    normal: 10,
    reduced: 5,
    emergency: 2
  }
};

export function useBatteryOptimization(config: Partial<PowerOptimizationConfig> = {}) {
  const [batteryStatus, setBatteryStatus] = useState<BatteryStatus>({
    level: 1.0,
    isCharging: false,
    chargingTime: Infinity,
    dischargingTime: Infinity,
    batteryLevel: 'full',
    estimatedHours: 0,
    isLowBattery: false,
    isCriticalBattery: false,
    powerMode: 'balanced',
    previousLevel: 1.0,
    drainRate: 0,
    lastUpdate: Date.now(),
    isStable: true,
    backgroundThrottled: false,
    animationsReduced: false,
    locationReducedAccuracy: false,
    screenBrightnessOptimized: false
  });

  const [optimizationConfig] = useState<PowerOptimizationConfig>({
    ...DEFAULT_CONFIG,
    ...config
  });

  const batteryRef = useRef<any>(null);
  const drainHistoryRef = useRef<{ timestamp: number; level: number }[]>([]);
  const updateIntervalRef = useRef<NodeJS.Timeout>();

  // Calculate battery level category
  const getBatteryLevel = useCallback((level: number): BatteryLevel => {
    if (level <= optimizationConfig.criticalThreshold) return 'critical';
    if (level <= optimizationConfig.lowThreshold) return 'low';
    if (level <= optimizationConfig.mediumThreshold) return 'medium';
    if (level < 0.90) return 'high';
    return 'full';
  }, [optimizationConfig]);

  // Calculate optimal power mode
  const getPowerMode = useCallback((level: number, isCharging: boolean, drainRate: number): PowerMode => {
    if (level <= optimizationConfig.emergencyModeAt && !isCharging) {
      return 'emergency';
    }
    if (level <= optimizationConfig.lowThreshold && !isCharging) {
      return 'power-saver';
    }
    if (level > optimizationConfig.mediumThreshold || isCharging) {
      return drainRate > 2 ? 'balanced' : 'maximum'; // If draining >2%/min, use balanced
    }
    return 'balanced';
  }, [optimizationConfig]);

  // Calculate battery drain rate (% per minute)
  const calculateDrainRate = useCallback((level: number): number => {
    const now = Date.now();
    const history = drainHistoryRef.current;

    // Add current reading
    history.push({ timestamp: now, level });

    // Keep only last 10 minutes of data
    const tenMinutesAgo = now - 10 * 60 * 1000;
    const recentHistory = history.filter(reading => reading.timestamp > tenMinutesAgo);
    drainHistoryRef.current = recentHistory;

    if (recentHistory.length < 2) return 0;

    // Calculate drain rate from oldest to newest reading
    const oldest = recentHistory[0];
    const newest = recentHistory[recentHistory.length - 1];
    const timeDiff = newest.timestamp - oldest.timestamp; // ms
    const levelDiff = oldest.level - newest.level; // Positive means draining

    if (timeDiff <= 0) return 0;

    // Convert to % per minute
    const drainPerMinute = (levelDiff * 100) / (timeDiff / 60000);
    return Math.max(0, drainPerMinute);
  }, []);

  // Estimate hours remaining
  const estimateHoursRemaining = useCallback((level: number, drainRate: number, isCharging: boolean): number => {
    if (isCharging) return Infinity;
    if (drainRate <= 0) return Infinity;

    const remainingPercent = level * 100;
    const hoursRemaining = remainingPercent / (drainRate * 60); // Convert from per-minute to per-hour
    return Math.max(0, hoursRemaining);
  }, []);

  // Update battery status
  const updateBatteryStatus = useCallback((battery: any) => {
    if (!battery) return;

    const level = battery.level || 1.0;
    const isCharging = battery.charging || false;
    const chargingTime = battery.chargingTime || Infinity;
    const dischargingTime = battery.dischargingTime || Infinity;

    const drainRate = calculateDrainRate(level);
    const batteryLevel = getBatteryLevel(level);
    const powerMode = getPowerMode(level, isCharging, drainRate);
    const estimatedHours = estimateHoursRemaining(level, drainRate, isCharging);

    setBatteryStatus(prev => {
      const levelChanged = Math.abs(prev.level - level) > 0.01; // 1% change threshold

      return {
        level,
        isCharging,
        chargingTime,
        dischargingTime,
        batteryLevel,
        estimatedHours,
        isLowBattery: level <= optimizationConfig.lowThreshold,
        isCriticalBattery: level <= optimizationConfig.criticalThreshold,
        powerMode,
        previousLevel: levelChanged ? prev.level : prev.previousLevel,
        drainRate,
        lastUpdate: Date.now(),
        isStable: !levelChanged,
        backgroundThrottled: level <= optimizationConfig.throttleBackgroundAt && !isCharging,
        animationsReduced: level <= optimizationConfig.reduceAnimationsAt && !isCharging,
        locationReducedAccuracy: level <= optimizationConfig.reducePrecisionAt && !isCharging,
        screenBrightnessOptimized: level <= optimizationConfig.lowThreshold && !isCharging
      };
    });
  }, [calculateDrainRate, getBatteryLevel, getPowerMode, estimateHoursRemaining, optimizationConfig]);

  // Initialize battery monitoring
  useEffect(() => {
    const initializeBattery = async () => {
      try {
        // Try to get battery API
        const battery = await (navigator as any).getBattery?.();

        if (battery) {
          batteryRef.current = battery;

          // Initial update
          updateBatteryStatus(battery);

          // Set up event listeners
          battery.addEventListener('chargingchange', () => updateBatteryStatus(battery));
          battery.addEventListener('levelchange', () => updateBatteryStatus(battery));
          battery.addEventListener('chargingtimechange', () => updateBatteryStatus(battery));
          battery.addEventListener('dischargingtimechange', () => updateBatteryStatus(battery));

          // Periodic updates for drain rate calculation
          updateIntervalRef.current = setInterval(() => {
            updateBatteryStatus(battery);
          }, 60000); // Every minute

        } else {
          console.warn('🔋 Jorge Battery: Battery API not supported, using fallback');
          // Fallback for browsers without Battery API
          setBatteryStatus(prev => ({
            ...prev,
            level: 0.75, // Assume reasonable battery level
            batteryLevel: 'high',
            powerMode: 'balanced'
          }));
        }

      } catch (error) {
        console.warn('🔋 Jorge Battery: Failed to initialize battery monitoring:', error);
        // Use conservative defaults
        setBatteryStatus(prev => ({
          ...prev,
          level: 0.50,
          batteryLevel: 'medium',
          powerMode: 'balanced'
        }));
      }
    };

    initializeBattery();

    return () => {
      const battery = batteryRef.current;
      if (battery) {
        battery.removeEventListener('chargingchange', updateBatteryStatus);
        battery.removeEventListener('levelchange', updateBatteryStatus);
        battery.removeEventListener('chargingtimechange', updateBatteryStatus);
        battery.removeEventListener('dischargingtimechange', updateBatteryStatus);
      }

      if (updateIntervalRef.current) {
        clearInterval(updateIntervalRef.current);
      }
    };
  }, [updateBatteryStatus]);

  // Power optimization utilities
  const shouldReduceFeature = useCallback((feature: 'animations' | 'background' | 'location' | 'brightness'): boolean => {
    if (batteryStatus.isCharging) return false;

    switch (feature) {
      case 'animations':
        return batteryStatus.animationsReduced;
      case 'background':
        return batteryStatus.backgroundThrottled;
      case 'location':
        return batteryStatus.locationReducedAccuracy;
      case 'brightness':
        return batteryStatus.screenBrightnessOptimized;
      default:
        return false;
    }
  }, [batteryStatus]);

  const getLocationFrequency = useCallback((): number => {
    if (batteryStatus.isCharging) {
      return optimizationConfig.locationFrequencyNormal;
    }

    switch (batteryStatus.powerMode) {
      case 'emergency':
        return optimizationConfig.locationFrequencyEmergency;
      case 'power-saver':
        return optimizationConfig.locationFrequencyReduced;
      case 'balanced':
      case 'maximum':
      default:
        return optimizationConfig.locationFrequencyNormal;
    }
  }, [batteryStatus, optimizationConfig]);

  const getSyncFrequency = useCallback((): number => {
    if (batteryStatus.isCharging) {
      return optimizationConfig.syncFrequencyNormal;
    }

    switch (batteryStatus.powerMode) {
      case 'emergency':
        return optimizationConfig.syncFrequencyEmergency;
      case 'power-saver':
        return optimizationConfig.syncFrequencyReduced;
      case 'balanced':
      case 'maximum':
      default:
        return optimizationConfig.syncFrequencyNormal;
    }
  }, [batteryStatus, optimizationConfig]);

  const getAnimationDuration = useCallback((): number => {
    if (batteryStatus.isCharging) {
      return optimizationConfig.animationDuration.normal;
    }

    if (batteryStatus.powerMode === 'emergency') {
      return optimizationConfig.animationDuration.minimal;
    }

    if (batteryStatus.animationsReduced) {
      return optimizationConfig.animationDuration.reduced;
    }

    return optimizationConfig.animationDuration.normal;
  }, [batteryStatus, optimizationConfig]);

  const getRequestTimeout = useCallback((): number => {
    if (batteryStatus.powerMode === 'power-saver' || batteryStatus.powerMode === 'emergency') {
      return optimizationConfig.requestTimeoutReduced;
    }

    return optimizationConfig.requestTimeoutNormal;
  }, [batteryStatus.powerMode, optimizationConfig]);

  const getMaxConcurrentRequests = useCallback((): number => {
    switch (batteryStatus.powerMode) {
      case 'emergency':
        return optimizationConfig.maxConcurrentRequests.emergency;
      case 'power-saver':
        return optimizationConfig.maxConcurrentRequests.reduced;
      case 'balanced':
      case 'maximum':
      default:
        return optimizationConfig.maxConcurrentRequests.normal;
    }
  }, [batteryStatus.powerMode, optimizationConfig]);

  // Emergency power preservation
  const enableEmergencyMode = useCallback(() => {
    setBatteryStatus(prev => ({
      ...prev,
      powerMode: 'emergency',
      backgroundThrottled: true,
      animationsReduced: true,
      locationReducedAccuracy: true,
      screenBrightnessOptimized: true
    }));

    // Notify other components about emergency mode
    window.dispatchEvent(new CustomEvent('jorge-emergency-power', {
      detail: { enabled: true, batteryLevel: batteryStatus.level }
    }));
  }, [batteryStatus.level]);

  const disableEmergencyMode = useCallback(() => {
    // Recalculate normal optimizations
    const level = batteryStatus.level;
    setBatteryStatus(prev => ({
      ...prev,
      powerMode: getPowerMode(level, prev.isCharging, prev.drainRate),
      backgroundThrottled: level <= optimizationConfig.throttleBackgroundAt && !prev.isCharging,
      animationsReduced: level <= optimizationConfig.reduceAnimationsAt && !prev.isCharging,
      locationReducedAccuracy: level <= optimizationConfig.reducePrecisionAt && !prev.isCharging,
      screenBrightnessOptimized: level <= optimizationConfig.lowThreshold && !prev.isCharging
    }));

    window.dispatchEvent(new CustomEvent('jorge-emergency-power', {
      detail: { enabled: false, batteryLevel: batteryStatus.level }
    }));
  }, [batteryStatus, getPowerMode, optimizationConfig]);

  const formatBatteryTime = useCallback((hours: number): string => {
    if (!isFinite(hours)) return 'Unknown';
    if (hours > 24) return '> 1 day';

    const wholeHours = Math.floor(hours);
    const minutes = Math.floor((hours - wholeHours) * 60);

    if (wholeHours > 0) {
      return `${wholeHours}h ${minutes}m`;
    }
    return `${minutes}m`;
  }, []);

  return {
    // Battery status
    batteryStatus,
    config: optimizationConfig,

    // Power optimization utilities
    shouldReduceFeature,
    getLocationFrequency,
    getSyncFrequency,
    getAnimationDuration,
    getRequestTimeout,
    getMaxConcurrentRequests,

    // Emergency controls
    enableEmergencyMode,
    disableEmergencyMode,

    // Formatting helpers
    formatBatteryTime,

    // Quick accessors
    level: batteryStatus.level,
    isCharging: batteryStatus.isCharging,
    isLowBattery: batteryStatus.isLowBattery,
    isCriticalBattery: batteryStatus.isCriticalBattery,
    powerMode: batteryStatus.powerMode,
    estimatedTime: formatBatteryTime(batteryStatus.estimatedHours),
    drainRate: batteryStatus.drainRate,

    // Optimization status
    isOptimized: batteryStatus.powerMode !== 'maximum',
    shouldThrottle: batteryStatus.backgroundThrottled,
    shouldReduceAnimations: batteryStatus.animationsReduced,
    shouldReduceAccuracy: batteryStatus.locationReducedAccuracy
  };
}

export default useBatteryOptimization;

// Jorge-specific battery utilities
export const JorgeBatteryUtils = {
  /**
   * Get battery color indicator for UI
   */
  getBatteryColor: (level: number, isCharging: boolean): string => {
    if (isCharging) return 'text-jorge-electric';
    if (level <= 0.05) return 'text-red-500';
    if (level <= 0.20) return 'text-yellow-500';
    return 'text-jorge-glow';
  },

  /**
   * Get battery icon based on level and charging status
   */
  getBatteryIcon: (level: number, isCharging: boolean): string => {
    if (isCharging) return '🔌';
    if (level <= 0.05) return '🪫';
    if (level <= 0.25) return '🔋';
    if (level <= 0.50) return '🔋';
    if (level <= 0.75) return '🔋';
    return '🔋';
  },

  /**
   * Check if feature should be available based on battery
   */
  isFeatureAvailable: (feature: 'voice' | 'camera' | 'gps' | 'sync', powerMode: PowerMode): boolean => {
    if (powerMode === 'emergency') {
      return feature === 'gps'; // Only GPS in emergency
    }
    if (powerMode === 'power-saver') {
      return feature !== 'camera'; // Disable camera in power saver
    }
    return true;
  },

  /**
   * Get recommended screen brightness (0-1)
   */
  getRecommendedBrightness: (batteryLevel: number, isCharging: boolean): number => {
    if (isCharging) return 1.0;
    if (batteryLevel <= 0.10) return 0.3;
    if (batteryLevel <= 0.20) return 0.5;
    if (batteryLevel <= 0.50) return 0.7;
    return 1.0;
  }
};