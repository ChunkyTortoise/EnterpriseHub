'use client';

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import {
  MapPinIcon,
  SignalIcon,
  ShieldCheckIcon,
  BellIcon,
  CogIcon,
  ExclamationTriangleIcon,
  PhoneIcon,
  NavigationIcon,
  ChartBarIcon,
  HomeIcon,
} from "@heroicons/react/24/outline";

import useLocationServices from "@/hooks/useLocationServices";

interface LocationDashboardProps {
  onNavigateToMap?: () => void;
  onNavigateToGeofences?: () => void;
  onNavigateToSettings?: () => void;
}

export function LocationDashboard({
  onNavigateToMap,
  onNavigateToGeofences,
  onNavigateToSettings,
}: LocationDashboardProps) {
  const {
    currentLocation,
    serviceStatus,
    isLoading,
    isTracking,
    error,
    recentAlerts,
    geofenceStats,
    marketInsight,
    activeGeofences,
    permissionStatus,
    batteryOptimized,
    initializeLocation,
    startTracking,
    stopTracking,
    getCurrentLocation,
    getMarketInsight,
    triggerEmergency,
    dismissAlert,
  } = useLocationServices({
    trackingEnabled: true,
    batteryOptimization: true,
    accuracyLevel: 'balanced',
  });

  const [currentAddress, setCurrentAddress] = useState<string>('');
  const [emergencyMode, setEmergencyMode] = useState(false);

  // Initialize location services on component mount
  useEffect(() => {
    initializeLocation().catch(console.error);
  }, [initializeLocation]);

  // Get market insight when location changes
  useEffect(() => {
    if (currentLocation && !marketInsight) {
      getMarketInsight().catch(console.error);
    }
  }, [currentLocation, marketInsight, getMarketInsight]);

  // Mock address lookup
  useEffect(() => {
    if (currentLocation) {
      // In production, use reverse geocoding service
      setCurrentAddress('1200 Brickell Avenue, Miami, FL 33131');
    }
  }, [currentLocation]);

  const handleEmergencyTrigger = async () => {
    setEmergencyMode(true);
    try {
      await triggerEmergency();

      // Show emergency confirmation
      setTimeout(() => {
        setEmergencyMode(false);
      }, 5000);
    } catch (error) {
      console.error('Emergency trigger failed:', error);
      setEmergencyMode(false);
    }
  };

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy <= 10) return 'text-jorge-glow';
    if (accuracy <= 50) return 'text-jorge-electric';
    return 'text-jorge-gold';
  };

  const getAccuracyLabel = (accuracy: number) => {
    if (accuracy <= 10) return 'Precise';
    if (accuracy <= 50) return 'Good';
    return 'Fair';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-2"
      >
        <h1 className="jorge-display text-2xl">LOCATION INTELLIGENCE</h1>
        <div className="flex items-center justify-center gap-2 text-sm jorge-code text-gray-400">
          <NavigationIcon className="w-4 h-4 text-jorge-electric" />
          <span>GPS TRACKING</span>
          <span>•</span>
          <span className={`${isTracking ? 'text-jorge-glow' : 'text-yellow-400'}`}>
            {isTracking ? 'ACTIVE' : 'STANDBY'}
          </span>
          {batteryOptimized && (
            <>
              <span>•</span>
              <span className="text-jorge-electric">OPTIMIZED</span>
            </>
          )}
        </div>
      </motion.div>

      {/* Current Location Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="jorge-card"
      >
        {isLoading && !currentLocation && (
          <div className="flex items-center justify-center gap-3 py-8">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              className="w-6 h-6 border-2 border-jorge-electric border-t-transparent rounded-full"
            />
            <span className="jorge-code text-gray-400">Acquiring GPS signal...</span>
          </div>
        )}

        {error && (
          <div className="flex items-center justify-between p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
            <div className="flex items-center gap-3">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />
              <div>
                <p className="text-sm text-red-400 font-medium">Location Error</p>
                <p className="text-xs text-red-300 mt-1">{error}</p>
              </div>
            </div>
            <button
              onClick={() => initializeLocation()}
              className="px-3 py-1 bg-red-500/20 text-red-400 text-xs font-semibold rounded jorge-haptic"
            >
              RETRY
            </button>
          </div>
        )}

        {currentLocation && (
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-jorge-electric/20 rounded-lg">
                  <MapPinIcon className="w-5 h-5 text-jorge-electric" />
                </div>
                <div className="flex-1">
                  <h3 className="jorge-code text-sm font-medium text-white mb-1">
                    Current Location
                  </h3>
                  <p className="text-xs text-gray-300 leading-relaxed">
                    {currentAddress || 'Address resolving...'}
                  </p>
                  {marketInsight && (
                    <p className="text-xs text-jorge-glow mt-1">
                      {marketInsight.neighborhood} • Market: {marketInsight.marketData.marketVelocity}
                    </p>
                  )}
                </div>
              </div>
              <button
                onClick={onNavigateToMap}
                className="px-2 py-1 bg-jorge-glow/20 text-jorge-glow text-xs font-semibold rounded jorge-haptic"
              >
                VIEW MAP
              </button>
            </div>

            <div className="grid grid-cols-3 gap-4 pt-3 border-t border-white/10">
              <div className="text-center">
                <div className={`text-sm font-semibold ${getAccuracyColor(currentLocation.accuracy)}`}>
                  {getAccuracyLabel(currentLocation.accuracy)}
                </div>
                <div className="text-xs text-gray-400">Accuracy</div>
                <div className="text-xs text-gray-500 mt-0.5">
                  ±{Math.round(currentLocation.accuracy)}m
                </div>
              </div>
              <div className="text-center">
                <div className="text-sm text-jorge-electric font-semibold">
                  {serviceStatus.accuracy.toUpperCase()}
                </div>
                <div className="text-xs text-gray-400">Mode</div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {batteryOptimized ? 'Optimized' : 'High Power'}
                </div>
              </div>
              <div className="text-center">
                <div className="text-sm text-jorge-glow font-semibold">
                  {isTracking ? 'ON' : 'OFF'}
                </div>
                <div className="text-xs text-gray-400">Tracking</div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {isTracking ? 'Live Updates' : 'Manual Only'}
                </div>
              </div>
            </div>

            {/* Location Controls */}
            <div className="grid grid-cols-2 gap-2 pt-2">
              {!isTracking ? (
                <button
                  onClick={startTracking}
                  className="flex items-center justify-center gap-2 py-2 bg-jorge-electric/20 text-jorge-electric text-xs font-semibold rounded jorge-haptic"
                >
                  <SignalIcon className="w-4 h-4" />
                  START TRACKING
                </button>
              ) : (
                <button
                  onClick={stopTracking}
                  className="flex items-center justify-center gap-2 py-2 bg-yellow-500/20 text-yellow-400 text-xs font-semibold rounded jorge-haptic"
                >
                  <SignalIcon className="w-4 h-4" />
                  STOP TRACKING
                </button>
              )}

              <button
                onClick={getCurrentLocation}
                disabled={isLoading}
                className="flex items-center justify-center gap-2 py-2 bg-jorge-glow/20 text-jorge-glow text-xs font-semibold rounded jorge-haptic disabled:opacity-50"
              >
                <NavigationIcon className="w-4 h-4" />
                REFRESH
              </button>
            </div>
          </div>
        )}
      </motion.div>

      {/* Recent Alerts */}
      {recentAlerts.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="space-y-3"
        >
          <div className="flex items-center justify-between">
            <h2 className="jorge-heading text-lg flex items-center gap-2">
              <BellIcon className="w-5 h-5 text-jorge-gold" />
              Recent Alerts
            </h2>
            <span className="text-xs jorge-code text-gray-400">
              {recentAlerts.length} ACTIVE
            </span>
          </div>

          {recentAlerts.slice(0, 3).map((alert, index) => (
            <motion.div
              key={alert.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 + index * 0.05 }}
              className="jorge-card jorge-card-hover cursor-pointer relative"
              onClick={() => dismissAlert(alert.id)}
            >
              <div className="flex items-start gap-3">
                <div className={`p-2 rounded-lg ${
                  alert.priority === 'high' ? 'bg-red-500/20' :
                  alert.priority === 'medium' ? 'bg-yellow-500/20' : 'bg-blue-500/20'
                }`}>
                  <HomeIcon className={`w-4 h-4 ${
                    alert.priority === 'high' ? 'text-red-400' :
                    alert.priority === 'medium' ? 'text-yellow-400' : 'text-blue-400'
                  }`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white font-medium leading-snug">
                    {alert.message}
                  </p>
                  <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
                    <span>{Math.round(alert.distance)}m away</span>
                    <span>•</span>
                    <span>{new Date(alert.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}</span>
                    <span>•</span>
                    <span className="text-jorge-electric font-semibold">
                      {alert.priority.toUpperCase()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Alert actions */}
              {alert.actions && alert.actions.length > 0 && (
                <div className="flex gap-2 mt-3 pt-2 border-t border-white/10">
                  {alert.actions.slice(0, 2).map(action => (
                    <button
                      key={action.id}
                      className="flex-1 py-1 px-2 bg-jorge-electric/20 text-jorge-electric text-xs font-semibold rounded jorge-haptic"
                      onClick={(e) => {
                        e.stopPropagation();
                        console.log('Action triggered:', action);
                      }}
                    >
                      {action.label}
                    </button>
                  ))}
                </div>
              )}
            </motion.div>
          ))}

          {recentAlerts.length > 3 && (
            <button
              onClick={onNavigateToGeofences}
              className="w-full py-2 text-xs jorge-code text-gray-400 hover:text-jorge-electric transition-colors"
            >
              VIEW ALL {recentAlerts.length} ALERTS →
            </button>
          )}
        </motion.div>
      )}

      {/* Geofence Statistics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="jorge-card"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="jorge-heading text-base flex items-center gap-2">
            <ChartBarIcon className="w-4 h-4 text-jorge-glow" />
            Geofence Activity
          </h3>
          <button
            onClick={onNavigateToGeofences}
            className="text-xs jorge-code text-jorge-electric hover:text-jorge-glow"
          >
            MANAGE →
          </button>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <div className="property-value text-lg">
              {geofenceStats.activeGeofences}
            </div>
            <div className="text-xs text-gray-400">Active Areas</div>
          </div>
          <div className="text-center">
            <div className="property-value text-lg">
              {geofenceStats.todayTriggers}
            </div>
            <div className="text-xs text-gray-400">Today's Alerts</div>
          </div>
          <div className="text-center">
            <div className="property-value text-lg">
              {geofenceStats.weekTriggers}
            </div>
            <div className="text-xs text-gray-400">This Week</div>
          </div>
          <div className="text-center">
            <div className="property-value text-lg">
              {geofenceStats.batteryImpact.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-400">Battery Use</div>
          </div>
        </div>
      </motion.div>

      {/* Market Intelligence */}
      {marketInsight && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="jorge-card"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="jorge-heading text-base">Market Intelligence</h3>
            <span className="text-xs jorge-code text-gray-400">
              {marketInsight.neighborhood.toUpperCase()}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="property-value text-base">
                ${(marketInsight.marketData.medianPrice / 1000).toFixed(0)}K
              </div>
              <div className="text-xs text-gray-400">Median Price</div>
            </div>
            <div>
              <div className="property-value text-base">
                {marketInsight.marketData.averageDaysOnMarket}
              </div>
              <div className="text-xs text-gray-400">Avg Days</div>
            </div>
            <div>
              <div className={`text-sm font-semibold ${
                marketInsight.marketData.marketVelocity === 'hot' ? 'text-red-400' :
                marketInsight.marketData.marketVelocity === 'warm' ? 'text-orange-400' :
                marketInsight.marketData.marketVelocity === 'balanced' ? 'text-jorge-glow' : 'text-blue-400'
              }`}>
                {marketInsight.marketData.marketVelocity.toUpperCase()}
              </div>
              <div className="text-xs text-gray-400">Market</div>
            </div>
            <div>
              <div className="property-value text-base">
                ${marketInsight.marketData.pricePerSqft}
              </div>
              <div className="text-xs text-gray-400">Per SqFt</div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Safety Controls */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="jorge-card"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="jorge-heading text-base flex items-center gap-2">
            <ShieldCheckIcon className="w-4 h-4 text-jorge-gold" />
            Safety Controls
          </h3>
          {emergencyMode && (
            <div className="flex items-center gap-1">
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
                className="w-2 h-2 bg-red-500 rounded-full"
              />
              <span className="text-xs jorge-code text-red-400">EMERGENCY ACTIVE</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={handleEmergencyTrigger}
            disabled={emergencyMode}
            className={`flex items-center justify-center gap-2 py-3 text-xs font-semibold rounded jorge-haptic ${
              emergencyMode
                ? 'bg-red-500/30 text-red-300 cursor-not-allowed'
                : 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
            }`}
          >
            <PhoneIcon className="w-4 h-4" />
            {emergencyMode ? 'ACTIVE' : 'EMERGENCY'}
          </button>

          <button
            onClick={() => {
              if (currentLocation) {
                const url = `https://maps.google.com/maps?q=${currentLocation.lat},${currentLocation.lng}`;
                if (navigator.share) {
                  navigator.share({ title: 'My Location', url });
                } else {
                  navigator.clipboard?.writeText(url);
                }
              }
            }}
            className="flex items-center justify-center gap-2 py-3 bg-jorge-electric/20 text-jorge-electric text-xs font-semibold rounded jorge-haptic"
          >
            <NavigationIcon className="w-4 h-4" />
            SHARE LOCATION
          </button>

          <button
            onClick={onNavigateToSettings}
            className="flex items-center justify-center gap-2 py-2 bg-jorge-glow/20 text-jorge-glow text-xs font-semibold rounded jorge-haptic"
          >
            <CogIcon className="w-4 h-4" />
            SETTINGS
          </button>

          <div className="flex items-center justify-center gap-2 text-xs text-gray-400">
            <div className={`w-2 h-2 rounded-full ${
              permissionStatus === 'granted' ? 'bg-jorge-glow' :
              permissionStatus === 'denied' ? 'bg-red-400' : 'bg-yellow-400'
            }`} />
            Permission: {permissionStatus}
          </div>
        </div>

        <div className="text-xs text-gray-400 text-center mt-3 pt-3 border-t border-white/10">
          Emergency contacts will be notified automatically
        </div>
      </motion.div>

      {/* Location Statistics */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="jorge-card text-center"
      >
        <div className="grid grid-cols-3 gap-4">
          <div>
            <div className="property-value text-base">
              {currentLocation ? 1 : 0}
            </div>
            <div className="text-xs text-gray-400">GPS Fixes</div>
          </div>
          <div>
            <div className="property-value text-base">
              {activeGeofences.length}
            </div>
            <div className="text-xs text-gray-400">Geofences</div>
          </div>
          <div>
            <div className="property-value text-base">
              {recentAlerts.length}
            </div>
            <div className="text-xs text-gray-400">Alerts</div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}