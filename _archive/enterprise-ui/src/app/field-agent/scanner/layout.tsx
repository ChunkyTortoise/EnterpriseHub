/**
 * Jorge Real Estate AI Platform - Scanner Layout
 * Optimized layout for field agent property scanning
 *
 * Features:
 * - Full-screen scanner interface
 * - Minimal UI for focus
 * - Emergency controls always accessible
 * - Camera permission management
 * - Location service integration
 */

'use client';

import { motion } from "framer-motion";
import { Suspense, useEffect, useState } from "react";
import {
  ExclamationTriangleIcon,
  CameraIcon,
  MapPinIcon,
  SignalIcon,
  BoltIcon
} from "@heroicons/react/24/outline";

interface ScannerLayoutProps {
  children: React.ReactNode;
}

interface PermissionStatus {
  camera: PermissionState | null;
  location: PermissionState | null;
  microphone: PermissionState | null;
}

export default function ScannerLayout({ children }: ScannerLayoutProps) {
  const [permissions, setPermissions] = useState<PermissionStatus>({
    camera: null,
    location: null,
    microphone: null
  });

  const [showPermissionPrompt, setShowPermissionPrompt] = useState(false);

  // Check and request permissions on mount
  useEffect(() => {
    checkPermissions();
  }, []);

  const checkPermissions = async () => {
    try {
      // Check camera permission
      const cameraPermission = await navigator.permissions.query({ name: 'camera' as PermissionName });

      // Check location permission
      const locationPermission = await navigator.permissions.query({ name: 'geolocation' as PermissionName });

      // Check microphone permission
      const microphonePermission = await navigator.permissions.query({ name: 'microphone' as PermissionName });

      const newPermissions = {
        camera: cameraPermission.state,
        location: locationPermission.state,
        microphone: microphonePermission.state
      };

      setPermissions(newPermissions);

      // Show permission prompt if any critical permissions are denied
      const hasRequiredPermissions = newPermissions.camera === 'granted' || newPermissions.camera === 'prompt';
      if (!hasRequiredPermissions) {
        setShowPermissionPrompt(true);
      }

    } catch (error) {
      console.error('Permission check failed:', error);
      setShowPermissionPrompt(true);
    }
  };

  const requestPermissions = async () => {
    try {
      // Request camera access
      if (permissions.camera !== 'granted') {
        await navigator.mediaDevices.getUserMedia({ video: true });
      }

      // Request location access
      if (permissions.location !== 'granted') {
        await new Promise<void>((resolve, reject) => {
          navigator.geolocation.getCurrentPosition(
            () => resolve(),
            reject,
            { enableHighAccuracy: true, timeout: 10000 }
          );
        });
      }

      // Request microphone access
      if (permissions.microphone !== 'granted') {
        await navigator.mediaDevices.getUserMedia({ audio: true });
      }

      // Re-check permissions after requests
      await checkPermissions();
      setShowPermissionPrompt(false);

    } catch (error) {
      console.error('Permission request failed:', error);
    }
  };

  const getPermissionIcon = (permission: PermissionState | null) => {
    switch (permission) {
      case 'granted':
        return <div className="w-2 h-2 bg-jorge-glow rounded-full" />;
      case 'denied':
        return <div className="w-2 h-2 bg-red-500 rounded-full" />;
      default:
        return <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />;
    }
  };

  return (
    <div className="relative min-h-screen bg-black text-white overflow-hidden">
      {/* Scanner-specific background */}
      <div className="absolute inset-0">
        {/* Grid overlay for scanner alignment */}
        <div className="absolute inset-0 opacity-5">
          <div
            className="w-full h-full"
            style={{
              backgroundImage: `
                linear-gradient(rgba(0,82,255,0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0,82,255,0.1) 1px, transparent 1px)
              `,
              backgroundSize: '20px 20px'
            }}
          />
        </div>

        {/* Scanning beam animation */}
        <motion.div
          className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-jorge-electric to-transparent"
          animate={{
            y: [0, window.innerHeight || 800, 0]
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </div>

      {/* Minimal header for scanner mode */}
      <div className="relative z-50 flex items-center justify-between px-4 py-3 bg-black/80 backdrop-blur-sm border-b border-white/10">
        {/* Jorge branding */}
        <div className="flex items-center gap-2">
          <BoltIcon className="w-5 h-5 text-jorge-electric" />
          <span className="text-sm jorge-code text-jorge-electric font-bold">
            JORGE SCANNER
          </span>
        </div>

        {/* Permission status indicators */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <CameraIcon className="w-4 h-4 text-gray-400" />
            {getPermissionIcon(permissions.camera)}
          </div>

          <div className="flex items-center gap-1">
            <MapPinIcon className="w-4 h-4 text-gray-400" />
            {getPermissionIcon(permissions.location)}
          </div>

          <div className="flex items-center gap-1">
            <SignalIcon className="w-4 h-4 text-gray-400" />
            {getPermissionIcon(permissions.microphone)}
          </div>

          {/* Emergency button */}
          <button className="w-8 h-8 rounded-full bg-red-600 flex items-center justify-center text-white text-xs font-bold jorge-haptic">
            🆘
          </button>
        </div>
      </div>

      {/* Main scanner content */}
      <main className="relative z-10 flex-1">
        <Suspense fallback={<ScannerLoadingSkeleton />}>
          {children}
        </Suspense>
      </main>

      {/* Permission prompt modal */}
      {showPermissionPrompt && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-jorge-dark border border-jorge-electric rounded-xl p-6 max-w-md w-full text-center"
          >
            <div className="w-16 h-16 bg-jorge-electric/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <ExclamationTriangleIcon className="w-8 h-8 text-jorge-electric" />
            </div>

            <h2 className="text-xl font-bold jorge-heading text-jorge-electric mb-2">
              Scanner Permissions
            </h2>

            <p className="text-gray-300 jorge-text mb-6 text-sm">
              Jorge's Property Scanner needs camera and location access for optimal field intelligence gathering.
            </p>

            {/* Permission breakdown */}
            <div className="space-y-3 mb-6">
              {[
                {
                  icon: CameraIcon,
                  name: 'Camera Access',
                  description: 'QR scanning + photo capture',
                  status: permissions.camera,
                  required: true
                },
                {
                  icon: MapPinIcon,
                  name: 'Location Access',
                  description: 'GPS tagging + property context',
                  status: permissions.location,
                  required: true
                },
                {
                  icon: SignalIcon,
                  name: 'Microphone Access',
                  description: 'Voice commands',
                  status: permissions.microphone,
                  required: false
                }
              ].map((perm) => (
                <div
                  key={perm.name}
                  className="flex items-center gap-3 p-3 bg-white/5 rounded-lg border border-white/10"
                >
                  <perm.icon className={`w-5 h-5 ${
                    perm.status === 'granted' ? 'text-jorge-glow' :
                    perm.status === 'denied' ? 'text-red-400' :
                    'text-yellow-400'
                  }`} />

                  <div className="flex-1 text-left">
                    <div className="font-semibold jorge-text text-sm flex items-center gap-2">
                      {perm.name}
                      {perm.required && (
                        <span className="text-xs bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded jorge-code">
                          REQUIRED
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-400 jorge-code">
                      {perm.description}
                    </div>
                  </div>

                  {getPermissionIcon(perm.status)}
                </div>
              ))}
            </div>

            {/* Action buttons */}
            <div className="flex gap-3">
              <button
                onClick={() => setShowPermissionPrompt(false)}
                className="flex-1 bg-white/10 text-gray-300 py-3 px-4 rounded-lg jorge-code font-semibold jorge-haptic"
              >
                Skip
              </button>

              <button
                onClick={requestPermissions}
                className="flex-1 bg-jorge-gradient text-white py-3 px-4 rounded-lg jorge-code font-bold jorge-haptic"
              >
                Grant Access
              </button>
            </div>

            <p className="text-xs text-gray-500 jorge-code mt-3">
              Permissions can be changed later in browser settings
            </p>
          </motion.div>
        </motion.div>
      )}

      {/* Scanning indicators */}
      <div className="fixed top-20 left-4 right-4 z-40 pointer-events-none">
        {/* Corner frame indicators */}
        {['top-left', 'top-right', 'bottom-left', 'bottom-right'].map((corner) => (
          <motion.div
            key={corner}
            className={`absolute w-8 h-8 border-2 border-jorge-electric ${
              corner.includes('top') ? 'top-0' : 'bottom-0'
            } ${
              corner.includes('left') ? 'left-0' : 'right-0'
            } ${
              corner.includes('top') && corner.includes('left') ? 'border-r-0 border-b-0' :
              corner.includes('top') && corner.includes('right') ? 'border-l-0 border-b-0' :
              corner.includes('bottom') && corner.includes('left') ? 'border-r-0 border-t-0' :
              'border-l-0 border-t-0'
            }`}
            animate={{
              opacity: [0.3, 1, 0.3]
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              delay: corner === 'top-left' ? 0 : corner === 'top-right' ? 0.2 : corner === 'bottom-right' ? 0.4 : 0.6
            }}
          />
        ))}
      </div>
    </div>
  );
}

// Loading skeleton for scanner interface
function ScannerLoadingSkeleton() {
  return (
    <div className="p-4 space-y-6 animate-pulse">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-6 w-40 bg-white/10 rounded" />
          <div className="h-4 w-32 bg-white/5 rounded" />
        </div>
        <div className="flex gap-2">
          <div className="h-8 w-16 bg-white/10 rounded-lg" />
          <div className="h-8 w-8 bg-white/10 rounded-lg" />
        </div>
      </div>

      {/* Scanner mode buttons skeleton */}
      <div className="grid grid-cols-2 gap-3">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-20 bg-white/5 rounded-xl border border-white/10" />
        ))}
      </div>

      {/* Stats skeleton */}
      <div className="grid grid-cols-4 gap-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-16 bg-white/5 rounded-lg" />
        ))}
      </div>

      {/* Scanner area skeleton */}
      <div className="h-64 bg-white/5 rounded-xl border border-white/10 flex items-center justify-center">
        <BoltIcon className="w-16 h-16 text-white/20" />
      </div>
    </div>
  );
}