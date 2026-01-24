'use client';

import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  ArrowLeftIcon,
  CogIcon,
  MapPinIcon,
  BoltIcon,
  ClockIcon,
  ShieldCheckIcon,
  BellIcon,
  SignalIcon,
  PhoneIcon,
  TrashIcon,
  PlusIcon,
} from "@heroicons/react/24/outline";

import { SafetyControls } from "@/components/mobile/location/SafetyControls";
import { MobileNavigation } from "@/components/mobile/MobileNavigation";
import useLocationServices from "@/hooks/useLocationServices";

export default function LocationSettingsPage() {
  const router = useRouter();

  const {
    serviceStatus,
    batteryOptimized,
    backgroundEnabled,
    permissionStatus,
    updatePreferences,
    clearLocationHistory,
    exportLocationData,
  } = useLocationServices();

  const [settings, setSettings] = useState({
    trackingEnabled: true,
    backgroundTracking: false,
    batteryOptimization: true,
    accuracyLevel: 'balanced' as 'high' | 'balanced' | 'low',
    updateInterval: 30, // seconds
    historyRetention: 30, // days
    privacyMode: false,
    emergencySharing: true,
    autoCheckIn: true,
    checkInInterval: 30, // minutes
    showNotifications: true,
    hapticFeedback: true,
  });

  const [emergencyContacts, setEmergencyContacts] = useState([
    {
      id: '1',
      name: 'Emergency Services',
      phone: '911',
      relationship: 'Emergency',
      priority: 1,
      autoNotify: false,
    },
    {
      id: '2',
      name: 'Office Manager',
      phone: '(555) 123-4567',
      relationship: 'Supervisor',
      priority: 2,
      autoNotify: true,
    },
    {
      id: '3',
      name: 'Emergency Contact',
      phone: '(555) 987-6543',
      relationship: 'Family',
      priority: 3,
      autoNotify: true,
    },
  ]);

  const handleSettingChange = (key: string, value: any) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);

    // Update location services preferences
    updatePreferences({
      trackingEnabled: newSettings.trackingEnabled,
      backgroundTracking: newSettings.backgroundTracking,
      batteryOptimization: newSettings.batteryOptimization,
      accuracyLevel: newSettings.accuracyLevel,
      updateInterval: newSettings.updateInterval,
      historyRetention: newSettings.historyRetention,
      privacyMode: newSettings.privacyMode,
      emergencySharing: newSettings.emergencySharing,
    });
  };

  const handleExportData = () => {
    try {
      const data = exportLocationData();
      const blob = new Blob([data], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `jorge-location-data-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      console.log('Location data exported successfully');
    } catch (error) {
      console.error('Failed to export location data:', error);
    }
  };

  const handleClearHistory = () => {
    if (confirm('Are you sure you want to clear all location history? This cannot be undone.')) {
      clearLocationHistory();
      console.log('Location history cleared');
    }
  };

  const handleAddContact = () => {
    // In a real app, this would open a contact picker or form
    const newContact = {
      id: Date.now().toString(),
      name: 'New Contact',
      phone: '(555) 000-0000',
      relationship: 'Other',
      priority: emergencyContacts.length + 1,
      autoNotify: false,
    };
    setEmergencyContacts([...emergencyContacts, newContact]);
  };

  const handleRemoveContact = (contactId: string) => {
    setEmergencyContacts(emergencyContacts.filter(c => c.id !== contactId));
  };

  const SettingCard = ({ title, description, children }: {
    title: string;
    description?: string;
    children: React.ReactNode;
  }) => (
    <div className="jorge-card">
      <div className="mb-3">
        <h3 className="jorge-heading text-base">{title}</h3>
        {description && <p className="text-xs text-gray-400 mt-1">{description}</p>}
      </div>
      {children}
    </div>
  );

  const ToggleSwitch = ({ enabled, onToggle, label, description }: {
    enabled: boolean;
    onToggle: (enabled: boolean) => void;
    label: string;
    description?: string;
  }) => (
    <div className="flex items-start justify-between">
      <div className="flex-1">
        <div className="text-sm text-white font-medium">{label}</div>
        {description && <div className="text-xs text-gray-400 mt-1">{description}</div>}
      </div>
      <button
        onClick={() => onToggle(!enabled)}
        className={`relative w-12 h-6 rounded-full transition-colors jorge-haptic ${
          enabled ? 'bg-jorge-electric' : 'bg-gray-600'
        }`}
      >
        <motion.div
          animate={{ x: enabled ? 24 : 2 }}
          transition={{ duration: 0.2 }}
          className="w-5 h-5 bg-white rounded-full mt-0.5"
        />
      </button>
    </div>
  );

  return (
    <div className="min-h-screen bg-jorge-gradient-dark text-white">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between p-4 bg-jorge-dark/95 backdrop-blur border-b border-white/10"
      >
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.back()}
            className="p-2 bg-white/10 rounded-lg jorge-haptic"
          >
            <ArrowLeftIcon className="w-5 h-5" />
          </button>
          <div>
            <h1 className="jorge-display text-lg">LOCATION SETTINGS</h1>
            <p className="text-xs text-gray-400">GPS & Safety Configuration</p>
          </div>
        </div>

        <div className="flex items-center gap-1 text-xs jorge-code text-gray-400">
          <CogIcon className="w-4 h-4" />
          <span>CONFIGURE</span>
        </div>
      </motion.header>

      {/* Content */}
      <div className="container mx-auto px-4 py-6 pb-24 space-y-6">
        {/* Permission Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="jorge-card"
        >
          <h2 className="jorge-heading text-lg mb-4 flex items-center gap-2">
            <ShieldCheckIcon className="w-5 h-5 text-jorge-gold" />
            Permission Status
          </h2>

          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className={`text-sm font-semibold ${
                permissionStatus === 'granted' ? 'text-jorge-glow' :
                permissionStatus === 'denied' ? 'text-red-400' : 'text-yellow-400'
              }`}>
                {permissionStatus?.toUpperCase() || 'UNKNOWN'}
              </div>
              <div className="text-xs text-gray-400">Location Access</div>
            </div>
            <div className="text-center">
              <div className={`text-sm font-semibold ${
                'Notification' in window && Notification.permission === 'granted'
                  ? 'text-jorge-glow' : 'text-yellow-400'
              }`}>
                {'Notification' in window ? Notification.permission.toUpperCase() : 'UNAVAILABLE'}
              </div>
              <div className="text-xs text-gray-400">Notifications</div>
            </div>
          </div>

          {permissionStatus !== 'granted' && (
            <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded text-sm text-yellow-200">
              Location permission is required for GPS-enabled property matching.
              <button
                onClick={() => {
                  // Request permission again
                  navigator.geolocation.getCurrentPosition(
                    () => window.location.reload(),
                    (error) => console.error('Permission denied:', error)
                  );
                }}
                className="ml-2 px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs font-semibold rounded"
              >
                Request Permission
              </button>
            </div>
          )}
        </motion.div>

        {/* Core GPS Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <SettingCard
            title="GPS Tracking"
            description="Configure location tracking behavior and accuracy"
          >
            <div className="space-y-4">
              <ToggleSwitch
                enabled={settings.trackingEnabled}
                onToggle={(enabled) => handleSettingChange('trackingEnabled', enabled)}
                label="Location Tracking"
                description="Enable real-time GPS tracking for property matching"
              />

              <ToggleSwitch
                enabled={settings.backgroundTracking}
                onToggle={(enabled) => handleSettingChange('backgroundTracking', enabled)}
                label="Background Tracking"
                description="Continue tracking when app is in background"
              />

              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-white font-medium">Accuracy Level</div>
                  <div className="text-xs text-gray-400">Higher accuracy uses more battery</div>
                </div>
                <select
                  value={settings.accuracyLevel}
                  onChange={(e) => handleSettingChange('accuracyLevel', e.target.value)}
                  className="bg-white/10 border border-white/20 rounded px-3 py-1 text-sm text-white"
                >
                  <option value="low">Low (50-100m)</option>
                  <option value="balanced">Balanced (10-50m)</option>
                  <option value="high">High (5-10m)</option>
                </select>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-white font-medium">Update Interval</div>
                  <div className="text-xs text-gray-400">How often to update location</div>
                </div>
                <select
                  value={settings.updateInterval}
                  onChange={(e) => handleSettingChange('updateInterval', Number(e.target.value))}
                  className="bg-white/10 border border-white/20 rounded px-3 py-1 text-sm text-white"
                >
                  <option value={10}>10 seconds</option>
                  <option value={30}>30 seconds</option>
                  <option value={60}>1 minute</option>
                  <option value={300}>5 minutes</option>
                </select>
              </div>
            </div>
          </SettingCard>
        </motion.div>

        {/* Battery Optimization */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <SettingCard
            title="Battery Optimization"
            description="Minimize battery usage while maintaining functionality"
          >
            <div className="space-y-4">
              <ToggleSwitch
                enabled={settings.batteryOptimization}
                onToggle={(enabled) => handleSettingChange('batteryOptimization', enabled)}
                label="Smart Battery Management"
                description="Automatically adjust accuracy based on battery level"
              />

              <div className="p-3 bg-jorge-electric/10 rounded text-sm">
                <div className="flex items-center gap-2 mb-2">
                  <BoltIcon className="w-4 h-4 text-jorge-electric" />
                  <span className="font-medium text-jorge-electric">Battery Tips</span>
                </div>
                <ul className="text-xs text-gray-300 space-y-1">
                  <li>• Balanced accuracy mode provides best battery/accuracy trade-off</li>
                  <li>• Background tracking significantly increases battery usage</li>
                  <li>• Smart management reduces accuracy when battery is low</li>
                </ul>
              </div>
            </div>
          </SettingCard>
        </motion.div>

        {/* Privacy Settings */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <SettingCard
            title="Privacy & Data"
            description="Control location data storage and sharing"
          >
            <div className="space-y-4">
              <ToggleSwitch
                enabled={!settings.privacyMode}
                onToggle={(enabled) => handleSettingChange('privacyMode', !enabled)}
                label="Location History"
                description="Store location history for insights and analytics"
              />

              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-white font-medium">History Retention</div>
                  <div className="text-xs text-gray-400">How long to keep location data</div>
                </div>
                <select
                  value={settings.historyRetention}
                  onChange={(e) => handleSettingChange('historyRetention', Number(e.target.value))}
                  className="bg-white/10 border border-white/20 rounded px-3 py-1 text-sm text-white"
                >
                  <option value={7}>7 days</option>
                  <option value={30}>30 days</option>
                  <option value={90}>90 days</option>
                  <option value={365}>1 year</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <button
                  onClick={handleExportData}
                  className="py-2 bg-jorge-glow/20 text-jorge-glow text-xs font-semibold rounded jorge-haptic"
                >
                  Export Data
                </button>
                <button
                  onClick={handleClearHistory}
                  className="py-2 bg-red-500/20 text-red-400 text-xs font-semibold rounded jorge-haptic"
                >
                  Clear History
                </button>
              </div>
            </div>
          </SettingCard>
        </motion.div>

        {/* Safety Features */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <SettingCard
            title="Safety Features"
            description="Emergency protocols and automated check-ins"
          >
            <div className="space-y-4">
              <ToggleSwitch
                enabled={settings.emergencySharing}
                onToggle={(enabled) => handleSettingChange('emergencySharing', enabled)}
                label="Emergency Location Sharing"
                description="Automatically share location during emergency"
              />

              <ToggleSwitch
                enabled={settings.autoCheckIn}
                onToggle={(enabled) => handleSettingChange('autoCheckIn', enabled)}
                label="Automatic Check-In"
                description="Periodic safety check-ins while tracking"
              />

              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-white font-medium">Check-In Interval</div>
                  <div className="text-xs text-gray-400">How often to perform check-ins</div>
                </div>
                <select
                  value={settings.checkInInterval}
                  onChange={(e) => handleSettingChange('checkInInterval', Number(e.target.value))}
                  className="bg-white/10 border border-white/20 rounded px-3 py-1 text-sm text-white"
                >
                  <option value={15}>15 minutes</option>
                  <option value={30}>30 minutes</option>
                  <option value={60}>1 hour</option>
                  <option value={120}>2 hours</option>
                </select>
              </div>
            </div>
          </SettingCard>
        </motion.div>

        {/* Emergency Contacts */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <SettingCard
            title="Emergency Contacts"
            description="People to notify during emergencies or safety events"
          >
            <div className="space-y-3">
              {emergencyContacts.map((contact, index) => (
                <div key={contact.id} className="flex items-center justify-between p-3 bg-white/5 rounded">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-jorge-gradient rounded-full flex items-center justify-center">
                      <span className="text-white text-sm font-semibold">
                        {contact.name.charAt(0)}
                      </span>
                    </div>
                    <div>
                      <div className="text-sm text-white font-medium">{contact.name}</div>
                      <div className="text-xs text-gray-400">{contact.phone} • {contact.relationship}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${contact.autoNotify ? 'bg-jorge-glow' : 'bg-gray-500'}`} />
                    <button
                      onClick={() => handleRemoveContact(contact.id)}
                      className="p-1 text-red-400 hover:bg-red-500/20 rounded jorge-haptic"
                    >
                      <TrashIcon className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              ))}

              <button
                onClick={handleAddContact}
                className="w-full flex items-center justify-center gap-2 py-3 bg-white/5 text-gray-400 text-sm font-medium rounded jorge-haptic border border-dashed border-gray-600"
              >
                <PlusIcon className="w-4 h-4" />
                Add Contact
              </button>
            </div>
          </SettingCard>
        </motion.div>

        {/* Notifications */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <SettingCard
            title="Notifications & Feedback"
            description="How you receive alerts and feedback"
          >
            <div className="space-y-4">
              <ToggleSwitch
                enabled={settings.showNotifications}
                onToggle={(enabled) => handleSettingChange('showNotifications', enabled)}
                label="Push Notifications"
                description="Show notifications for geofence alerts and safety events"
              />

              <ToggleSwitch
                enabled={settings.hapticFeedback}
                onToggle={(enabled) => handleSettingChange('hapticFeedback', enabled)}
                label="Haptic Feedback"
                description="Vibration feedback for alerts and interactions"
              />
            </div>
          </SettingCard>
        </motion.div>

        {/* Advanced Safety Controls */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <SafetyControls
            showExtended={true}
            emergencyContacts={emergencyContacts}
            onEmergencyTriggered={() => {
              console.log('Emergency triggered from settings');
            }}
            onLocationShared={() => {
              console.log('Location shared from settings');
            }}
            onSettingsOpen={() => {
              console.log('Settings already open');
            }}
          />
        </motion.div>

        {/* Reset to Defaults */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="jorge-card border border-red-500/30"
        >
          <h3 className="jorge-heading text-base mb-3 text-red-400">Reset Settings</h3>
          <p className="text-sm text-gray-300 mb-4">
            Reset all location settings to their default values. This cannot be undone.
          </p>
          <button
            onClick={() => {
              if (confirm('Are you sure you want to reset all settings to defaults?')) {
                // Reset all settings to defaults
                const defaultSettings = {
                  trackingEnabled: true,
                  backgroundTracking: false,
                  batteryOptimization: true,
                  accuracyLevel: 'balanced' as const,
                  updateInterval: 30,
                  historyRetention: 30,
                  privacyMode: false,
                  emergencySharing: true,
                  autoCheckIn: true,
                  checkInInterval: 30,
                  showNotifications: true,
                  hapticFeedback: true,
                };
                setSettings(defaultSettings);
                updatePreferences(defaultSettings);
                console.log('Settings reset to defaults');
              }
            }}
            className="px-4 py-2 bg-red-500/20 text-red-400 text-sm font-semibold rounded jorge-haptic"
          >
            Reset to Defaults
          </button>
        </motion.div>
      </div>

      <MobileNavigation />
    </div>
  );
}