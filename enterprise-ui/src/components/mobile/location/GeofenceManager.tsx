'use client';

import { motion } from "framer-motion";
import { useState } from "react";
import {
  CompassIcon,
  PlusIcon,
  TrashIcon,
  PencilIcon,
  BellIcon,
  MapPinIcon,
  ClockIcon,
  BatteryIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";

import useLocationServices from "@/hooks/useLocationServices";
import type { PropertyGeofence } from "@/lib/location/GeofenceEngine";

interface GeofenceManagerProps {
  onCreateGeofence?: () => void;
  onEditGeofence?: (geofenceId: string) => void;
}

export function GeofenceManager({
  onCreateGeofence,
  onEditGeofence,
}: GeofenceManagerProps) {
  const {
    activeGeofences,
    recentAlerts,
    geofenceStats,
    currentLocation,
    removeGeofence,
    deactivateGeofence,
    clearAllGeofences,
    createPropertyGeofence,
  } = useLocationServices();

  const [selectedGeofence, setSelectedGeofence] = useState<PropertyGeofence | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [filter, setFilter] = useState<'all' | 'active' | 'triggered'>('all');

  // Filter geofences based on current filter
  const filteredGeofences = activeGeofences.filter(geofence => {
    switch (filter) {
      case 'active':
        return geofence.isActive;
      case 'triggered':
        return geofence.triggerCount > 0;
      default:
        return true;
    }
  });

  const getAlertTypeColor = (alertType: PropertyGeofence['alertType']) => {
    switch (alertType) {
      case 'hot_lead_match':
        return 'text-red-400 bg-red-500/20';
      case 'showing_scheduled':
        return 'text-jorge-electric bg-jorge-electric/20';
      case 'new_listing':
        return 'text-jorge-glow bg-jorge-glow/20';
      case 'price_drop':
        return 'text-jorge-gold bg-jorge-gold/20';
      case 'client_nearby':
        return 'text-blue-400 bg-blue-500/20';
      default:
        return 'text-gray-400 bg-gray-500/20';
    }
  };

  const getAlertTypeLabel = (alertType: PropertyGeofence['alertType']) => {
    switch (alertType) {
      case 'hot_lead_match':
        return 'Hot Lead Match';
      case 'showing_scheduled':
        return 'Showing Scheduled';
      case 'new_listing':
        return 'New Listing';
      case 'price_drop':
        return 'Price Drop';
      case 'client_nearby':
        return 'Client Nearby';
      default:
        return alertType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
  };

  const getPriorityColor = (priority: PropertyGeofence['priority']) => {
    switch (priority) {
      case 'high':
        return 'text-red-400';
      case 'medium':
        return 'text-yellow-400';
      case 'low':
        return 'text-green-400';
      default:
        return 'text-gray-400';
    }
  };

  const formatDistance = (meters: number) => {
    if (meters >= 1000) {
      return `${(meters / 1000).toFixed(1)}km`;
    }
    return `${Math.round(meters)}m`;
  };

  const formatLastTriggered = (timestamp?: number) => {
    if (!timestamp) return 'Never';

    const now = Date.now();
    const diff = now - timestamp;
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  const handleRemoveGeofence = (geofenceId: string) => {
    if (confirm('Are you sure you want to remove this geofence?')) {
      removeGeofence(geofenceId);
      if (selectedGeofence?.id === geofenceId) {
        setSelectedGeofence(null);
      }
    }
  };

  const handleToggleGeofence = (geofence: PropertyGeofence) => {
    if (geofence.isActive) {
      deactivateGeofence(geofence.id);
    } else {
      // Reactivate geofence (would need method in hook)
      console.log('Reactivating geofence:', geofence.id);
    }
  };

  const handleCreateQuickGeofence = () => {
    if (!currentLocation) {
      alert('Current location is required to create a geofence');
      return;
    }

    // Create a generic property alert geofence at current location
    createPropertyGeofence(
      `quick_${Date.now()}`,
      { lat: currentLocation.lat, lng: currentLocation.lng },
      'new_listing',
      {
        propertyAddress: 'Current Location',
        propertyType: 'quick_alert',
      },
      {
        radius: 200,
        priority: 'medium',
      }
    );

    console.log('Created quick geofence at current location');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-2"
      >
        <h1 className="jorge-display text-2xl">GEOFENCE MANAGER</h1>
        <div className="flex items-center justify-center gap-2 text-sm jorge-code text-gray-400">
          <CompassIcon className="w-4 h-4 text-jorge-electric" />
          <span>{activeGeofences.length} ACTIVE</span>
          <span>•</span>
          <span>{geofenceStats.todayTriggers} TODAY</span>
          <span>•</span>
          <span className="text-jorge-gold">{geofenceStats.batteryImpact.toFixed(1)}% BATTERY</span>
        </div>
      </motion.div>

      {/* Stats Overview */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="jorge-card"
      >
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center">
            <div className="property-value text-lg">{geofenceStats.activeGeofences}</div>
            <div className="text-xs text-gray-400">Active Areas</div>
          </div>
          <div className="text-center">
            <div className="property-value text-lg">{geofenceStats.weekTriggers}</div>
            <div className="text-xs text-gray-400">Week Triggers</div>
          </div>
          <div className="text-center">
            <div className="property-value text-lg">
              {geofenceStats.averageDistance > 0 ? formatDistance(geofenceStats.averageDistance) : '0m'}
            </div>
            <div className="text-xs text-gray-400">Avg Distance</div>
          </div>
          <div className="text-center">
            <div className={`text-lg font-bold ${geofenceStats.batteryImpact > 5 ? 'text-yellow-400' : 'text-jorge-glow'}`}>
              {geofenceStats.batteryImpact.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-400">Battery Impact</div>
          </div>
        </div>
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="jorge-card"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="jorge-heading text-base">Quick Actions</h3>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={handleCreateQuickGeofence}
            disabled={!currentLocation}
            className="flex items-center justify-center gap-2 py-3 bg-jorge-electric/20 text-jorge-electric text-xs font-semibold rounded jorge-haptic disabled:opacity-50"
          >
            <PlusIcon className="w-4 h-4" />
            CREATE HERE
          </button>

          <button
            onClick={() => setShowCreateForm(true)}
            className="flex items-center justify-center gap-2 py-3 bg-jorge-glow/20 text-jorge-glow text-xs font-semibold rounded jorge-haptic"
          >
            <MapPinIcon className="w-4 h-4" />
            CUSTOM AREA
          </button>

          <button
            onClick={() => {
              if (confirm('Clear all geofences? This cannot be undone.')) {
                clearAllGeofences();
              }
            }}
            className="flex items-center justify-center gap-2 py-2 bg-red-500/20 text-red-400 text-xs font-semibold rounded jorge-haptic"
          >
            <TrashIcon className="w-4 h-4" />
            CLEAR ALL
          </button>

          <div className="flex items-center justify-center gap-2 text-xs text-gray-400">
            <BatteryIcon className="w-4 h-4" />
            <span>Battery Optimized</span>
          </div>
        </div>
      </motion.div>

      {/* Filter Tabs */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="flex bg-white/5 rounded-lg p-1"
      >
        {[
          { id: 'all', label: 'All', count: activeGeofences.length },
          { id: 'active', label: 'Active', count: activeGeofences.filter(g => g.isActive).length },
          { id: 'triggered', label: 'Triggered', count: activeGeofences.filter(g => g.triggerCount > 0).length },
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setFilter(tab.id as any)}
            className={`flex-1 py-2 px-3 rounded-lg text-xs font-semibold transition-colors jorge-haptic ${
              filter === tab.id
                ? 'bg-jorge-electric/20 text-jorge-electric'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {tab.label} ({tab.count})
          </button>
        ))}
      </motion.div>

      {/* Geofence List */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="space-y-3"
      >
        {filteredGeofences.length === 0 ? (
          <div className="jorge-card text-center py-8">
            <CompassIcon className="w-12 h-12 text-gray-400 mx-auto mb-3" />
            <p className="text-gray-400 text-sm">
              {filter === 'all' ? 'No geofences created yet' :
               filter === 'active' ? 'No active geofences' :
               'No triggered geofences'}
            </p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="mt-3 px-4 py-2 bg-jorge-electric/20 text-jorge-electric text-xs font-semibold rounded jorge-haptic"
            >
              Create Your First Geofence
            </button>
          </div>
        ) : (
          filteredGeofences.map((geofence, index) => (
            <motion.div
              key={geofence.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 + index * 0.05 }}
              className={`jorge-card jorge-card-hover cursor-pointer ${
                !geofence.isActive ? 'opacity-60' : ''
              }`}
              onClick={() => setSelectedGeofence(
                selectedGeofence?.id === geofence.id ? null : geofence
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3 flex-1">
                  <div className={`p-2 rounded-lg ${getAlertTypeColor(geofence.alertType)}`}>
                    <BellIcon className="w-4 h-4" />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-sm font-medium text-white truncate">
                        {geofence.metadata.propertyAddress}
                      </h4>
                      <span className={`text-xs font-semibold ${getPriorityColor(geofence.priority)}`}>
                        {geofence.priority.toUpperCase()}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-gray-400 mb-2">
                      <span className={getAlertTypeColor(geofence.alertType).split(' ')[0]}>
                        {getAlertTypeLabel(geofence.alertType)}
                      </span>
                      <span>•</span>
                      <span>{formatDistance(geofence.radius)} radius</span>
                      <span>•</span>
                      <span>{geofence.triggerCount} triggers</span>
                    </div>

                    <div className="flex items-center gap-4 text-xs text-gray-500">
                      <span>Last: {formatLastTriggered(geofence.lastTriggered)}</span>
                      <span>Created: {new Date(geofence.createdAt).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {geofence.isActive ? (
                    <CheckCircleIcon className="w-5 h-5 text-jorge-glow" />
                  ) : (
                    <XCircleIcon className="w-5 h-5 text-gray-400" />
                  )}
                </div>
              </div>

              {/* Expanded Details */}
              {selectedGeofence?.id === geofence.id && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="mt-4 pt-4 border-t border-white/10 space-y-3"
                >
                  {/* Metadata */}
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    {geofence.metadata.leadName && (
                      <div>
                        <div className="text-gray-400">Lead</div>
                        <div className="text-white font-medium">{geofence.metadata.leadName}</div>
                      </div>
                    )}
                    {geofence.metadata.listingPrice && (
                      <div>
                        <div className="text-gray-400">Price</div>
                        <div className="text-jorge-gold font-medium">
                          ${(geofence.metadata.listingPrice / 1000).toFixed(0)}K
                        </div>
                      </div>
                    )}
                    {geofence.metadata.mlScore && (
                      <div>
                        <div className="text-gray-400">ML Score</div>
                        <div className="text-jorge-electric font-medium">{geofence.metadata.mlScore}/100</div>
                      </div>
                    )}
                    {geofence.metadata.botAssignment && (
                      <div>
                        <div className="text-gray-400">Bot</div>
                        <div className="text-jorge-glow font-medium">
                          {geofence.metadata.botAssignment.replace(/_/g, ' ')}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Conditions */}
                  {geofence.conditions.length > 0 && (
                    <div>
                      <div className="text-xs text-gray-400 mb-2">Conditions:</div>
                      <div className="space-y-1">
                        {geofence.conditions.map((condition, idx) => (
                          <div key={idx} className="flex items-center gap-2 text-xs text-gray-300">
                            <div className="w-1 h-1 bg-jorge-electric rounded-full" />
                            <span>
                              {condition.type === 'time_range' && condition.params.timeRange &&
                                `Active ${condition.params.timeRange.start}:00-${condition.params.timeRange.end}:00`
                              }
                              {condition.type === 'battery_level' && condition.params.minBattery &&
                                `Min battery: ${(condition.params.minBattery * 100).toFixed(0)}%`
                              }
                              {condition.type === 'previous_trigger_cooldown' && condition.params.cooldownHours &&
                                `Cooldown: ${condition.params.cooldownHours}h`
                              }
                              {condition.type === 'network_status' && condition.params.requiresNetwork &&
                                'Requires network connection'
                              }
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="grid grid-cols-3 gap-2 pt-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleToggleGeofence(geofence);
                      }}
                      className={`py-2 text-xs font-semibold rounded jorge-haptic ${
                        geofence.isActive
                          ? 'bg-yellow-500/20 text-yellow-400'
                          : 'bg-jorge-glow/20 text-jorge-glow'
                      }`}
                    >
                      {geofence.isActive ? 'Disable' : 'Enable'}
                    </button>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onEditGeofence?.(geofence.id);
                      }}
                      className="py-2 bg-jorge-electric/20 text-jorge-electric text-xs font-semibold rounded jorge-haptic"
                    >
                      <PencilIcon className="w-3 h-3 mx-auto" />
                    </button>

                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRemoveGeofence(geofence.id);
                      }}
                      className="py-2 bg-red-500/20 text-red-400 text-xs font-semibold rounded jorge-haptic"
                    >
                      <TrashIcon className="w-3 h-3 mx-auto" />
                    </button>
                  </div>
                </motion.div>
              )}
            </motion.div>
          ))
        )}
      </motion.div>

      {/* Recent Alert Types Summary */}
      {geofenceStats.topAlertTypes.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="jorge-card"
        >
          <h3 className="jorge-heading text-base mb-3">Most Common Alerts</h3>
          <div className="space-y-2">
            {geofenceStats.topAlertTypes.slice(0, 3).map((alertType, index) => (
              <div key={alertType.type} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${getAlertTypeColor(alertType.type as any).split(' ')[1]}`} />
                  <span className="text-sm text-white">
                    {getAlertTypeLabel(alertType.type as any)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-jorge-electric font-medium">{alertType.count}</span>
                  <span className="text-xs text-gray-400">triggers</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Performance Warning */}
      {geofenceStats.batteryImpact > 5 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="jorge-card border border-yellow-500/30 bg-yellow-500/10"
        >
          <div className="flex items-start gap-3">
            <ExclamationTriangleIcon className="w-5 h-5 text-yellow-400 mt-0.5" />
            <div>
              <h4 className="text-sm font-medium text-yellow-400 mb-1">High Battery Usage</h4>
              <p className="text-xs text-yellow-200 mb-2">
                Your geofences are using {geofenceStats.batteryImpact.toFixed(1)}% of battery.
                Consider reducing the number of active geofences or enabling battery optimization.
              </p>
              <button className="px-3 py-1 bg-yellow-500/20 text-yellow-400 text-xs font-semibold rounded jorge-haptic">
                Optimize Settings
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Create Form Modal (would be implemented as a separate component) */}
      {showCreateForm && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur flex items-center justify-center p-4"
          onClick={() => setShowCreateForm(false)}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="jorge-card max-w-md w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="jorge-heading text-lg mb-4">Create Custom Geofence</h3>
            <p className="text-sm text-gray-400 mb-4">
              This feature will allow you to create custom geofences by selecting locations on the map or entering addresses.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowCreateForm(false)}
                className="flex-1 py-2 bg-white/10 text-gray-400 text-sm font-semibold rounded jorge-haptic"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  onCreateGeofence?.();
                  setShowCreateForm(false);
                }}
                className="flex-1 py-2 bg-jorge-electric/20 text-jorge-electric text-sm font-semibold rounded jorge-haptic"
              >
                Open Map
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </div>
  );
}