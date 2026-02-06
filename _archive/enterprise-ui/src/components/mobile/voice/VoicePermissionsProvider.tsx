'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MicrophoneIcon,
  SpeakerWaveIcon,
  MapPinIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';

interface VoicePermissions {
  microphone: 'granted' | 'denied' | 'prompt';
  speechRecognition: boolean;
  location: 'granted' | 'denied' | 'prompt';
}

interface VoicePermissionsContextType {
  permissions: VoicePermissions;
  requestPermissions: () => Promise<void>;
  hasAllRequiredPermissions: boolean;
}

const VoicePermissionsContext = createContext<VoicePermissionsContextType | null>(null);

export function useVoicePermissions() {
  const context = useContext(VoicePermissionsContext);
  if (!context) {
    throw new Error('useVoicePermissions must be used within VoicePermissionsProvider');
  }
  return context;
}

interface VoicePermissionsProviderProps {
  children: React.ReactNode;
}

export function VoicePermissionsProvider({ children }: VoicePermissionsProviderProps) {
  const [permissions, setPermissions] = useState<VoicePermissions>({
    microphone: 'prompt',
    speechRecognition: false,
    location: 'prompt',
  });
  const [showPermissionModal, setShowPermissionModal] = useState(false);
  const [isCheckingPermissions, setIsCheckingPermissions] = useState(true);

  useEffect(() => {
    checkPermissions();
  }, []);

  const checkPermissions = async () => {
    try {
      setIsCheckingPermissions(true);

      // Check microphone permission
      let microphonePermission: 'granted' | 'denied' | 'prompt' = 'prompt';
      try {
        const micResult = await navigator.permissions.query({ name: 'microphone' as PermissionName });
        microphonePermission = micResult.state as 'granted' | 'denied' | 'prompt';
      } catch (error) {
        // Fallback: try to access microphone directly
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          microphonePermission = 'granted';
          stream.getTracks().forEach(track => track.stop());
        } catch (error) {
          microphonePermission = 'denied';
        }
      }

      // Check speech recognition support
      const speechRecognitionSupport = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;

      // Check location permission (optional)
      let locationPermission: 'granted' | 'denied' | 'prompt' = 'prompt';
      try {
        const geoResult = await navigator.permissions.query({ name: 'geolocation' as PermissionName });
        locationPermission = geoResult.state as 'granted' | 'denied' | 'prompt';
      } catch (error) {
        // Geolocation permission query not supported, assume prompt
        locationPermission = 'prompt';
      }

      const newPermissions = {
        microphone: microphonePermission,
        speechRecognition: speechRecognitionSupport,
        location: locationPermission,
      };

      setPermissions(newPermissions);

      // Show permission modal if required permissions are not granted
      if (microphonePermission !== 'granted' || !speechRecognitionSupport) {
        setShowPermissionModal(true);
      }

    } catch (error) {
      console.error('Error checking permissions:', error);
    } finally {
      setIsCheckingPermissions(false);
    }
  };

  const requestPermissions = async () => {
    try {
      // Request microphone permission
      if (permissions.microphone !== 'granted') {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          stream.getTracks().forEach(track => track.stop());
          setPermissions(prev => ({ ...prev, microphone: 'granted' }));
        } catch (error) {
          setPermissions(prev => ({ ...prev, microphone: 'denied' }));
          throw new Error('Microphone permission denied');
        }
      }

      // Request location permission (optional)
      if (permissions.location === 'prompt') {
        try {
          await new Promise<GeolocationPosition>((resolve, reject) => {
            navigator.geolocation.getCurrentPosition(resolve, reject, { timeout: 5000 });
          });
          setPermissions(prev => ({ ...prev, location: 'granted' }));
        } catch (error) {
          setPermissions(prev => ({ ...prev, location: 'denied' }));
          // Location is optional, don't throw error
        }
      }

      setShowPermissionModal(false);

    } catch (error) {
      console.error('Error requesting permissions:', error);
      throw error;
    }
  };

  const hasAllRequiredPermissions = permissions.microphone === 'granted' && permissions.speechRecognition;

  if (isCheckingPermissions) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-jorge-gradient-dark">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="jorge-glass p-8 rounded-xl text-center"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-8 h-8 border-2 border-jorge-electric border-t-transparent rounded-full mx-auto mb-4"
          />
          <p className="text-white jorge-code">Checking voice permissions...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <VoicePermissionsContext.Provider
      value={{
        permissions,
        requestPermissions,
        hasAllRequiredPermissions,
      }}
    >
      {children}

      {/* Permission Request Modal */}
      <AnimatePresence>
        {showPermissionModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              className="jorge-glass p-6 rounded-xl max-w-md w-full"
            >
              <div className="text-center mb-6">
                <MicrophoneIcon className="w-12 h-12 text-jorge-electric mx-auto mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">
                  Voice Notes Permissions
                </h3>
                <p className="text-gray-400 text-sm">
                  Jorge needs access to your microphone to record voice notes and provide hands-free functionality.
                </p>
              </div>

              {/* Permission Status */}
              <div className="space-y-3 mb-6">
                <PermissionItem
                  icon={MicrophoneIcon}
                  name="Microphone Access"
                  status={permissions.microphone}
                  required={true}
                  description="Record voice notes and audio"
                />

                <PermissionItem
                  icon={SpeakerWaveIcon}
                  name="Speech Recognition"
                  status={permissions.speechRecognition ? 'granted' : 'denied'}
                  required={true}
                  description="Convert speech to text"
                />

                <PermissionItem
                  icon={MapPinIcon}
                  name="Location Access"
                  status={permissions.location}
                  required={false}
                  description="Tag notes with GPS location"
                />
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setShowPermissionModal(false)}
                  className="flex-1 px-4 py-3 bg-gray-500/20 border border-gray-500/30 rounded-lg text-gray-300 jorge-haptic"
                >
                  Skip
                </motion.button>

                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={requestPermissions}
                  className="flex-1 px-4 py-3 bg-jorge-electric/20 border border-jorge-electric/30 rounded-lg text-jorge-electric font-medium jorge-haptic"
                >
                  Enable Permissions
                </motion.button>
              </div>

              {/* Help Text */}
              <div className="mt-4 p-3 rounded-lg bg-blue-500/10 border border-blue-500/30">
                <div className="flex items-start gap-2">
                  <ExclamationTriangleIcon className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <div className="text-xs text-blue-300">
                    <div className="font-medium mb-1">Need Help?</div>
                    <div>If permissions are blocked, you can enable them in your browser settings under Privacy & Security → Microphone.</div>
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </VoicePermissionsContext.Provider>
  );
}

// Permission item component
interface PermissionItemProps {
  icon: React.ElementType;
  name: string;
  status: 'granted' | 'denied' | 'prompt' | boolean;
  required: boolean;
  description: string;
}

function PermissionItem({ icon: Icon, name, status, required, description }: PermissionItemProps) {
  const getStatusColor = () => {
    if (status === 'granted' || status === true) return 'text-green-400';
    if (status === 'denied' || status === false) return 'text-red-400';
    return 'text-yellow-400';
  };

  const getStatusIcon = () => {
    if (status === 'granted' || status === true) return CheckCircleIcon;
    if (status === 'denied' || status === false) return ExclamationTriangleIcon;
    return ExclamationTriangleIcon;
  };

  const getStatusText = () => {
    if (status === 'granted' || status === true) return 'Granted';
    if (status === 'denied' || status === false) return 'Denied';
    return 'Required';
  };

  const StatusIcon = getStatusIcon();

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-black/20">
      <Icon className="w-5 h-5 text-gray-400" />
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-white">{name}</span>
          {required && (
            <span className="text-xs px-2 py-0.5 bg-red-500/20 border border-red-500/30 rounded-full text-red-400">
              Required
            </span>
          )}
        </div>
        <p className="text-xs text-gray-400">{description}</p>
      </div>
      <div className="flex items-center gap-1">
        <StatusIcon className={`w-4 h-4 ${getStatusColor()}`} />
        <span className={`text-xs font-medium ${getStatusColor()}`}>
          {getStatusText()}
        </span>
      </div>
    </div>
  );
}