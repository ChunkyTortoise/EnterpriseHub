'use client';

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import {
  ShieldCheckIcon,
  PhoneIcon,
  MapPinIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  UserGroupIcon,
  ShareIcon,
  BellIcon,
  CogIcon,
  SignalIcon,
  BoltIcon,
  WifiIcon,
  DevicePhoneMobileIcon,
  HeartIcon,
} from "@heroicons/react/24/outline";

import useLocationServices from "@/hooks/useLocationServices";

interface EmergencyContact {
  id: string;
  name: string;
  phone: string;
  relationship: string;
  priority: number;
  autoNotify: boolean;
}

interface SafetyEvent {
  id: string;
  type: 'check_in' | 'emergency' | 'location_share' | 'safe_arrival';
  timestamp: number;
  location?: { lat: number; lng: number };
  message?: string;
  contacts?: string[];
  automated?: boolean;
}

interface SafetyControlsProps {
  showExtended?: boolean;
  emergencyContacts?: EmergencyContact[];
  onEmergencyTriggered?: (location: any) => void;
  onLocationShared?: (contacts: string[]) => void;
  onSettingsOpen?: () => void;
}

export function SafetyControls({
  showExtended = false,
  emergencyContacts = [],
  onEmergencyTriggered,
  onLocationShared,
  onSettingsOpen,
}: SafetyControlsProps) {
  const {
    currentLocation,
    shareLocation,
    triggerEmergency,
    isTracking,
    permissionStatus,
    batteryOptimized,
  } = useLocationServices();

  const [isEmergencyMode, setIsEmergencyMode] = useState(false);
  const [lastCheckIn, setLastCheckIn] = useState<number | null>(null);
  const [safetyEvents, setSafetyEvents] = useState<SafetyEvent[]>([]);
  const [autoCheckIn, setAutoCheckIn] = useState(true);
  const [checkInInterval, setCheckInInterval] = useState(30); // minutes
  const [selectedContacts, setSelectedContacts] = useState<string[]>([]);
  const [deviceStatus, setDeviceStatus] = useState({
    battery: 1.0,
    network: navigator.onLine,
    gps: !!currentLocation,
  });

  // Default emergency contacts if none provided
  const defaultContacts: EmergencyContact[] = [
    {
      id: 'emergency-911',
      name: '911 Emergency',
      phone: '911',
      relationship: 'Emergency Services',
      priority: 1,
      autoNotify: false,
    },
    {
      id: 'office-main',
      name: 'Office Manager',
      phone: '(555) 123-4567',
      relationship: 'Supervisor',
      priority: 2,
      autoNotify: true,
    },
    {
      id: 'spouse',
      name: 'Emergency Contact',
      phone: '(555) 987-6543',
      relationship: 'Family',
      priority: 3,
      autoNotify: true,
    },
  ];

  const contacts = emergencyContacts.length > 0 ? emergencyContacts : defaultContacts;

  // Monitor device status
  useEffect(() => {
    const updateDeviceStatus = () => {
      setDeviceStatus({
        battery: deviceStatus.battery, // Would be updated by battery API
        network: navigator.onLine,
        gps: !!currentLocation,
      });
    };

    window.addEventListener('online', updateDeviceStatus);
    window.addEventListener('offline', updateDeviceStatus);

    // Battery monitoring
    if ('getBattery' in navigator) {
      (navigator as any).getBattery().then((battery: any) => {
        setDeviceStatus(prev => ({ ...prev, battery: battery.level }));

        battery.addEventListener('levelchange', () => {
          setDeviceStatus(prev => ({ ...prev, battery: battery.level }));
        });
      });
    }

    return () => {
      window.removeEventListener('online', updateDeviceStatus);
      window.removeEventListener('offline', updateDeviceStatus);
    };
  }, [deviceStatus.battery, currentLocation]);

  // Auto check-in functionality
  useEffect(() => {
    if (!autoCheckIn || !isTracking) return;

    const interval = setInterval(() => {
      const now = Date.now();
      if (!lastCheckIn || now - lastCheckIn > checkInInterval * 60 * 1000) {
        performAutoCheckIn();
      }
    }, 60 * 1000); // Check every minute

    return () => clearInterval(interval);
  }, [autoCheckIn, isTracking, lastCheckIn, checkInInterval]);

  const performAutoCheckIn = () => {
    const now = Date.now();
    const event: SafetyEvent = {
      id: `checkin_${now}`,
      type: 'check_in',
      timestamp: now,
      location: currentLocation ? { lat: currentLocation.lat, lng: currentLocation.lng } : undefined,
      automated: true,
    };

    setSafetyEvents(prev => [event, ...prev.slice(0, 49)]);
    setLastCheckIn(now);

    console.log('Auto check-in performed at', new Date(now).toLocaleTimeString());
  };

  const handleEmergencyTrigger = async () => {
    if (isEmergencyMode) return;

    setIsEmergencyMode(true);

    try {
      // Trigger emergency with location services
      await triggerEmergency();

      // Create emergency event
      const event: SafetyEvent = {
        id: `emergency_${Date.now()}`,
        type: 'emergency',
        timestamp: Date.now(),
        location: currentLocation ? { lat: currentLocation.lat, lng: currentLocation.lng } : undefined,
        contacts: contacts.filter(c => c.autoNotify).map(c => c.id),
        message: 'EMERGENCY ALERT: Immediate assistance required',
      };

      setSafetyEvents(prev => [event, ...prev]);

      // Notify callback
      if (currentLocation) {
        onEmergencyTriggered?.(currentLocation);
      }

      // Auto-disable emergency mode after 30 seconds to prevent accidental re-triggers
      setTimeout(() => {
        setIsEmergencyMode(false);
      }, 30000);

    } catch (error) {
      console.error('Emergency trigger failed:', error);
      setIsEmergencyMode(false);
    }
  };

  const handleLocationShare = async () => {
    if (!currentLocation) {
      alert('Current location required to share location');
      return;
    }

    try {
      const contactsToShare = selectedContacts.length > 0
        ? selectedContacts
        : contacts.filter(c => c.autoNotify).map(c => c.id);

      await shareLocation(contactsToShare);

      // Create location share event
      const event: SafetyEvent = {
        id: `share_${Date.now()}`,
        type: 'location_share',
        timestamp: Date.now(),
        location: { lat: currentLocation.lat, lng: currentLocation.lng },
        contacts: contactsToShare,
        message: 'Location shared with selected contacts',
      };

      setSafetyEvents(prev => [event, ...prev]);
      onLocationShared?.(contactsToShare);

    } catch (error) {
      console.error('Location sharing failed:', error);
    }
  };

  const handleManualCheckIn = () => {
    const event: SafetyEvent = {
      id: `manual_checkin_${Date.now()}`,
      type: 'check_in',
      timestamp: Date.now(),
      location: currentLocation ? { lat: currentLocation.lat, lng: currentLocation.lng } : undefined,
      message: 'Manual safety check-in',
      automated: false,
    };

    setSafetyEvents(prev => [event, ...prev]);
    setLastCheckIn(Date.now());

    // Haptic feedback
    if ('vibrate' in navigator) {
      navigator.vibrate(100);
    }
  };

  const getDeviceStatusColor = () => {
    const issues = [
      !deviceStatus.gps,
      !deviceStatus.network,
      deviceStatus.battery < 0.2,
    ].filter(Boolean).length;

    if (issues === 0) return 'text-jorge-glow';
    if (issues === 1) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getTimeSinceLastCheckIn = () => {
    if (!lastCheckIn) return 'Never';

    const diff = Date.now() - lastCheckIn;
    const minutes = Math.floor(diff / (1000 * 60));
    const hours = Math.floor(diff / (1000 * 60 * 60));

    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-2">
          <ShieldCheckIcon className="w-5 h-5 text-jorge-gold" />
          <h2 className="jorge-heading text-lg">Safety Controls</h2>
        </div>
        <div className={`flex items-center gap-1 text-xs jorge-code ${getDeviceStatusColor()}`}>
          <div className="w-2 h-2 rounded-full bg-current" />
          <span>STATUS</span>
        </div>
      </motion.div>

      {/* Emergency Mode Banner */}
      {isEmergencyMode && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="jorge-card bg-red-500/20 border border-red-500/30"
        >
          <div className="flex items-center gap-3">
            <motion.div
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
              className="p-2 bg-red-500/30 rounded-full"
            >
              <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />
            </motion.div>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-400 mb-1">EMERGENCY MODE ACTIVE</h3>
              <p className="text-xs text-red-200">
                Emergency services and contacts have been notified. Location is being tracked continuously.
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Main Controls */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="jorge-card"
      >
        <div className="grid grid-cols-2 gap-3 mb-4">
          {/* Emergency Button */}
          <button
            onClick={handleEmergencyTrigger}
            disabled={isEmergencyMode}
            className={`flex items-center justify-center gap-2 py-4 text-sm font-semibold rounded-lg jorge-haptic ${
              isEmergencyMode
                ? 'bg-red-500/30 text-red-300 cursor-not-allowed'
                : 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
            }`}
          >
            <PhoneIcon className="w-5 h-5" />
            {isEmergencyMode ? 'EMERGENCY ACTIVE' : 'EMERGENCY'}
          </button>

          {/* Location Share */}
          <button
            onClick={handleLocationShare}
            disabled={!currentLocation}
            className="flex items-center justify-center gap-2 py-4 bg-jorge-electric/20 text-jorge-electric text-sm font-semibold rounded-lg jorge-haptic disabled:opacity-50"
          >
            <ShareIcon className="w-5 h-5" />
            SHARE LOCATION
          </button>
        </div>

        {/* Manual Check-In */}
        <button
          onClick={handleManualCheckIn}
          className="w-full flex items-center justify-center gap-2 py-3 bg-jorge-glow/20 text-jorge-glow text-sm font-semibold rounded-lg jorge-haptic"
        >
          <HeartIcon className="w-4 h-4" />
          CHECK-IN NOW
        </button>
      </motion.div>

      {/* Device Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="jorge-card"
      >
        <h3 className="jorge-heading text-base mb-3">Device Status</h3>

        <div className="grid grid-cols-3 gap-3 text-xs">
          <div className="flex items-center gap-2">
            <SignalIcon className={`w-4 h-4 ${deviceStatus.gps ? 'text-jorge-glow' : 'text-red-400'}`} />
            <div>
              <div className={`font-medium ${deviceStatus.gps ? 'text-jorge-glow' : 'text-red-400'}`}>
                {deviceStatus.gps ? 'GPS ON' : 'GPS OFF'}
              </div>
              <div className="text-gray-400">Location</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <WifiIcon className={`w-4 h-4 ${deviceStatus.network ? 'text-jorge-glow' : 'text-red-400'}`} />
            <div>
              <div className={`font-medium ${deviceStatus.network ? 'text-jorge-glow' : 'text-red-400'}`}>
                {deviceStatus.network ? 'ONLINE' : 'OFFLINE'}
              </div>
              <div className="text-gray-400">Network</div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <BoltIcon className={`w-4 h-4 ${
              deviceStatus.battery > 0.5 ? 'text-jorge-glow' :
              deviceStatus.battery > 0.2 ? 'text-yellow-400' : 'text-red-400'
            }`} />
            <div>
              <div className={`font-medium ${
                deviceStatus.battery > 0.5 ? 'text-jorge-glow' :
                deviceStatus.battery > 0.2 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {Math.round(deviceStatus.battery * 100)}%
              </div>
              <div className="text-gray-400">Battery</div>
            </div>
          </div>
        </div>

        {/* Warnings */}
        {(!deviceStatus.gps || !deviceStatus.network || deviceStatus.battery < 0.2) && (
          <div className="mt-3 p-2 bg-yellow-500/10 border border-yellow-500/30 rounded text-xs text-yellow-200">
            <div className="flex items-start gap-2">
              <ExclamationTriangleIcon className="w-4 h-4 text-yellow-400 mt-0.5" />
              <div>
                {!deviceStatus.gps && <div>• GPS disabled - Location services unavailable</div>}
                {!deviceStatus.network && <div>• No network connection - Emergency calling may be limited</div>}
                {deviceStatus.battery < 0.2 && <div>• Low battery - Consider charging device</div>}
              </div>
            </div>
          </div>
        )}
      </motion.div>

      {/* Auto Check-In Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="jorge-card"
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="jorge-heading text-base flex items-center gap-2">
            <ClockIcon className="w-4 h-4 text-jorge-electric" />
            Auto Check-In
          </h3>
          <button
            onClick={() => setAutoCheckIn(!autoCheckIn)}
            className={`px-3 py-1 text-xs font-semibold rounded jorge-haptic ${
              autoCheckIn
                ? 'bg-jorge-glow/20 text-jorge-glow'
                : 'bg-white/10 text-gray-400'
            }`}
          >
            {autoCheckIn ? 'ON' : 'OFF'}
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3 text-xs mb-3">
          <div className="text-center">
            <div className="text-sm text-white font-medium">
              {getTimeSinceLastCheckIn()}
            </div>
            <div className="text-gray-400">Last Check-In</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-jorge-electric font-medium">
              {checkInInterval}min
            </div>
            <div className="text-gray-400">Interval</div>
          </div>
        </div>

        {autoCheckIn && (
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <BellIcon className="w-3 h-3" />
            <span>Automatic check-ins every {checkInInterval} minutes when tracking</span>
          </div>
        )}
      </motion.div>

      {/* Emergency Contacts */}
      {showExtended && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="jorge-card"
        >
          <h3 className="jorge-heading text-base mb-3 flex items-center gap-2">
            <UserGroupIcon className="w-4 h-4 text-jorge-gold" />
            Emergency Contacts
          </h3>

          <div className="space-y-2">
            {contacts.slice(0, 3).map(contact => (
              <div
                key={contact.id}
                className="flex items-center justify-between p-2 bg-white/5 rounded"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-jorge-gradient rounded-full flex items-center justify-center">
                    <span className="text-white text-xs font-semibold">
                      {contact.name.charAt(0)}
                    </span>
                  </div>
                  <div>
                    <div className="text-sm text-white font-medium">{contact.name}</div>
                    <div className="text-xs text-gray-400">{contact.relationship}</div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {contact.autoNotify && (
                    <div className="w-2 h-2 bg-jorge-glow rounded-full" />
                  )}
                  <button
                    onClick={() => window.open(`tel:${contact.phone}`)}
                    className="p-1 bg-jorge-electric/20 text-jorge-electric rounded jorge-haptic"
                  >
                    <PhoneIcon className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={onSettingsOpen}
            className="w-full mt-3 py-2 bg-white/5 text-gray-400 text-xs font-medium rounded jorge-haptic"
          >
            MANAGE CONTACTS
          </button>
        </motion.div>
      )}

      {/* Recent Safety Events */}
      {showExtended && safetyEvents.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="jorge-card"
        >
          <h3 className="jorge-heading text-base mb-3">Recent Activity</h3>

          <div className="space-y-2">
            {safetyEvents.slice(0, 3).map(event => {
              const getEventIcon = () => {
                switch (event.type) {
                  case 'emergency':
                    return ExclamationTriangleIcon;
                  case 'location_share':
                    return ShareIcon;
                  case 'safe_arrival':
                    return HeartIcon;
                  case 'check_in':
                  default:
                    return ClockIcon;
                }
              };

              const getEventColor = () => {
                switch (event.type) {
                  case 'emergency':
                    return 'text-red-400';
                  case 'location_share':
                    return 'text-jorge-electric';
                  case 'safe_arrival':
                    return 'text-jorge-glow';
                  case 'check_in':
                  default:
                    return 'text-gray-400';
                }
              };

              const EventIcon = getEventIcon();
              const eventColor = getEventColor();

              return (
                <div key={event.id} className="flex items-start gap-3 p-2 bg-white/5 rounded">
                  <div className={`p-1 rounded ${eventColor}`}>
                    <EventIcon className="w-3 h-3" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-white">
                      {event.type === 'check_in' && (event.automated ? 'Auto check-in' : 'Manual check-in')}
                      {event.type === 'emergency' && 'Emergency triggered'}
                      {event.type === 'location_share' && 'Location shared'}
                      {event.type === 'safe_arrival' && 'Safe arrival'}
                    </div>
                    <div className="text-xs text-gray-400">
                      {new Date(event.timestamp).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* Quick Settings */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: showExtended ? 0.5 : 0.3 }}
        className="grid grid-cols-2 gap-3"
      >
        <button
          onClick={onSettingsOpen}
          className="flex items-center justify-center gap-2 py-3 bg-white/10 text-gray-400 text-xs font-semibold rounded jorge-haptic"
        >
          <CogIcon className="w-4 h-4" />
          SETTINGS
        </button>

        <div className="text-center text-xs text-gray-500 pt-3">
          {isTracking ? (
            <div className="flex items-center justify-center gap-1">
              <div className="w-2 h-2 bg-jorge-glow rounded-full jorge-glow-pulse" />
              <span>Safety monitoring active</span>
            </div>
          ) : (
            <div className="flex items-center justify-center gap-1">
              <div className="w-2 h-2 bg-gray-500 rounded-full" />
              <span>Monitoring paused</span>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}