/**
 * Jorge Real Estate AI Platform - Property Scanner
 * Professional field agent tool for instant property intelligence
 *
 * Features:
 * - QR code scanning with instant property lookup
 * - Camera integration with GPS-tagged photos
 * - Barcode scanning for lockbox codes
 * - Offline-first operation with sync capabilities
 * - Voice command integration
 * - Instant CMA generation
 * - Jorge's confrontational analysis style
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  QrCodeIcon,
  CameraIcon,
  MapPinIcon,
  MicrophoneIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  BoltIcon
} from '@heroicons/react/24/outline';
import {
  QrCodeIcon as QrCodeIconSolid,
  CameraIcon as CameraIconSolid,
  MicrophoneIcon as MicrophoneIconSolid
} from '@heroicons/react/24/solid';

import { QRScanner } from '@/components/mobile/scanner/QRScanner';
import { CameraCapture } from '@/components/mobile/scanner/CameraCapture';
import { PropertyResults } from '@/components/mobile/scanner/PropertyResults';
import { VoiceCommands } from '@/components/mobile/scanner/VoiceCommands';
import { ScanHistory } from '@/components/mobile/scanner/ScanHistory';

import { usePropertyScanner } from '@/hooks/usePropertyScanner';
import { useOfflineStorage } from '@/hooks/useOfflineStorage';
import { useVoiceCommands } from '@/hooks/useVoiceCommands';

type ScanMode = 'qr' | 'camera' | 'barcode' | 'voice';

interface ScannerStats {
  totalScans: number;
  successfulScans: number;
  offlineScans: number;
  avgScanTime: number;
}

export default function PropertyScannerPage() {
  const [scanMode, setScanMode] = useState<ScanMode>('qr');
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [stats, setStats] = useState<ScannerStats>({
    totalScans: 0,
    successfulScans: 0,
    offlineScans: 0,
    avgScanTime: 0
  });

  const scanStartTime = useRef<number>(0);

  const {
    scanProperty,
    generateCMA,
    isLoading,
    error: scanError,
    scanHistory,
    clearHistory
  } = usePropertyScanner();

  const { isOnline } = useOfflineStorage();
  const {
    isListening,
    transcript,
    startListening,
    stopListening,
    isSupported: voiceSupported
  } = useVoiceCommands();

  // Handle scan initiation
  const handleStartScan = async (mode: ScanMode) => {
    setScanMode(mode);
    setIsScanning(true);
    setScanResult(null);
    scanStartTime.current = Date.now();

    try {
      // Initialize camera or scanner based on mode
      switch (mode) {
        case 'voice':
          if (voiceSupported) {
            await startListening();
          }
          break;
        default:
          // QR/Camera/Barcode handled by child components
          break;
      }
    } catch (error) {
      console.error('Failed to start scan:', error);
      setIsScanning(false);
    }
  };

  // Handle scan completion
  const handleScanComplete = async (data: string, scanType: string = 'qr') => {
    const scanTime = Date.now() - scanStartTime.current;

    try {
      setIsScanning(false);

      // Process the scanned data
      const result = await scanProperty(data, {
        scanType,
        scanTime,
        location: await getCurrentLocation(),
        offline: !isOnline
      });

      setScanResult(result);

      // Update stats
      setStats(prev => ({
        totalScans: prev.totalScans + 1,
        successfulScans: prev.successfulScans + (result ? 1 : 0),
        offlineScans: prev.offlineScans + (!isOnline ? 1 : 0),
        avgScanTime: ((prev.avgScanTime * prev.totalScans) + scanTime) / (prev.totalScans + 1)
      }));

      // Auto-generate CMA for property results
      if (result?.property) {
        await generateCMA(result.property.id);
      }

    } catch (error) {
      console.error('Scan processing failed:', error);
      setIsScanning(false);
    }
  };

  // Get current location for context
  const getCurrentLocation = (): Promise<{ lat: number; lng: number } | null> => {
    return new Promise((resolve) => {
      if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            resolve({
              lat: position.coords.latitude,
              lng: position.coords.longitude
            });
          },
          () => resolve(null),
          { timeout: 5000, enableHighAccuracy: true }
        );
      } else {
        resolve(null);
      }
    });
  };

  // Handle voice command processing
  useEffect(() => {
    if (transcript && isListening) {
      // Process voice commands for property lookup
      handleScanComplete(transcript, 'voice');
      stopListening();
    }
  }, [transcript, isListening, stopListening]);

  // Scan mode configurations
  const scanModes = [
    {
      id: 'qr' as const,
      name: 'QR Code',
      icon: QrCodeIcon,
      activeIcon: QrCodeIconSolid,
      description: 'Scan property QR codes',
      color: 'jorge-electric'
    },
    {
      id: 'camera' as const,
      name: 'Camera',
      icon: CameraIcon,
      activeIcon: CameraIconSolid,
      description: 'Photo + GPS tagging',
      color: 'jorge-gold'
    },
    {
      id: 'barcode' as const,
      name: 'Barcode',
      icon: QrCodeIcon,
      activeIcon: QrCodeIconSolid,
      description: 'Scan lockbox codes',
      color: 'jorge-glow'
    },
    {
      id: 'voice' as const,
      name: 'Voice',
      icon: MicrophoneIcon,
      activeIcon: MicrophoneIconSolid,
      description: 'Voice property lookup',
      color: 'jorge-steel',
      disabled: !voiceSupported
    }
  ];

  return (
    <div className="min-h-screen bg-jorge-gradient-dark text-white relative overflow-hidden">
      {/* Header */}
      <div className="relative z-20 px-4 py-6">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-6"
        >
          <div>
            <h1 className="jorge-heading text-2xl mb-2">
              🔍 Property Scanner
            </h1>
            <p className="text-gray-400 jorge-code text-sm">
              Jorge's field intelligence tool
            </p>
          </div>

          {/* Status indicators */}
          <div className="flex items-center gap-3">
            {/* Offline indicator */}
            {!isOnline && (
              <div className="flex items-center gap-1 px-2 py-1 rounded-lg bg-yellow-500/20 border border-yellow-500/30">
                <ExclamationTriangleIcon className="w-4 h-4 text-yellow-400" />
                <span className="text-xs jorge-code text-yellow-400">OFFLINE</span>
              </div>
            )}

            {/* Scanner status */}
            <div className={`flex items-center gap-1 px-2 py-1 rounded-lg ${
              isScanning
                ? 'bg-jorge-electric/20 border-jorge-electric/30'
                : 'bg-gray-500/20 border-gray-500/30'
            }`}>
              <div className={`w-2 h-2 rounded-full ${
                isScanning ? 'bg-jorge-electric animate-pulse' : 'bg-gray-500'
              }`} />
              <span className={`text-xs jorge-code ${
                isScanning ? 'text-jorge-electric' : 'text-gray-400'
              }`}>
                {isScanning ? 'SCANNING' : 'READY'}
              </span>
            </div>
          </div>
        </motion.div>

        {/* Scanner Mode Selection */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 gap-3 mb-6"
        >
          {scanModes.map((mode) => {
            const Icon = scanMode === mode.id ? mode.activeIcon : mode.icon;
            const isActive = scanMode === mode.id;
            const isDisabled = mode.disabled;

            return (
              <motion.button
                key={mode.id}
                onClick={() => !isDisabled && handleStartScan(mode.id)}
                disabled={isDisabled || isScanning}
                className={`
                  relative p-4 rounded-xl border transition-all duration-200
                  ${isActive
                    ? 'bg-jorge-electric/20 border-jorge-electric text-jorge-electric'
                    : isDisabled
                    ? 'bg-gray-500/10 border-gray-500/20 text-gray-500'
                    : 'bg-white/5 border-white/10 text-gray-300 hover:border-white/20'
                  }
                  ${!isDisabled && 'jorge-haptic jorge-touch-target'}
                `}
                whileTap={!isDisabled ? { scale: 0.95 } : undefined}
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-6 h-6" />
                  <div className="text-left">
                    <div className="font-semibold jorge-text">{mode.name}</div>
                    <div className="text-xs text-gray-400 jorge-code">
                      {mode.description}
                    </div>
                  </div>
                </div>

                {/* Active indicator */}
                {isActive && (
                  <motion.div
                    layoutId="activeScanMode"
                    className="absolute inset-0 rounded-xl border-2 border-jorge-electric"
                    initial={false}
                    transition={{
                      type: "spring",
                      stiffness: 500,
                      damping: 30
                    }}
                  />
                )}

                {/* Disabled overlay */}
                {isDisabled && (
                  <div className="absolute inset-0 bg-black/50 rounded-xl flex items-center justify-center">
                    <span className="text-xs jorge-code text-gray-400">N/A</span>
                  </div>
                )}
              </motion.button>
            );
          })}
        </motion.div>

        {/* Quick Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="grid grid-cols-4 gap-2 mb-6"
        >
          {[
            { label: 'Total', value: stats.totalScans, color: 'text-gray-300' },
            { label: 'Success', value: stats.successfulScans, color: 'text-jorge-glow' },
            { label: 'Offline', value: stats.offlineScans, color: 'text-yellow-400' },
            { label: 'Avg Time', value: `${(stats.avgScanTime / 1000).toFixed(1)}s`, color: 'text-jorge-electric' }
          ].map((stat) => (
            <div key={stat.label} className="bg-white/5 rounded-lg p-2 text-center">
              <div className={`text-lg font-bold jorge-code ${stat.color}`}>
                {stat.value}
              </div>
              <div className="text-xs text-gray-400 jorge-code">
                {stat.label}
              </div>
            </div>
          ))}
        </motion.div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="flex gap-3 mb-6"
        >
          <button
            onClick={() => setShowHistory(true)}
            className="flex-1 bg-white/5 border border-white/10 rounded-lg p-3 flex items-center gap-2 jorge-haptic"
          >
            <DocumentTextIcon className="w-5 h-5 text-gray-400" />
            <span className="text-sm jorge-text">History</span>
            {scanHistory.length > 0 && (
              <div className="ml-auto bg-jorge-electric text-black text-xs px-2 py-0.5 rounded-full jorge-code">
                {scanHistory.length}
              </div>
            )}
          </button>

          <button
            onClick={() => navigator.geolocation?.getCurrentPosition(console.log)}
            className="bg-white/5 border border-white/10 rounded-lg p-3 flex items-center gap-2 jorge-haptic"
          >
            <MapPinIcon className="w-5 h-5 text-gray-400" />
            <span className="text-sm jorge-text">GPS</span>
          </button>
        </motion.div>
      </div>

      {/* Scanner Interface */}
      <div className="relative z-10 px-4">
        <AnimatePresence mode="wait">
          {isScanning && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="mb-6"
            >
              {scanMode === 'qr' && (
                <QRScanner
                  onScanComplete={(data) => handleScanComplete(data, 'qr')}
                  onClose={() => setIsScanning(false)}
                />
              )}

              {scanMode === 'camera' && (
                <CameraCapture
                  onPhotoCapture={(data) => handleScanComplete(data, 'photo')}
                  onClose={() => setIsScanning(false)}
                />
              )}

              {scanMode === 'barcode' && (
                <QRScanner
                  onScanComplete={(data) => handleScanComplete(data, 'barcode')}
                  onClose={() => setIsScanning(false)}
                  mode="barcode"
                />
              )}

              {scanMode === 'voice' && (
                <VoiceCommands
                  isListening={isListening}
                  transcript={transcript}
                  onClose={() => {
                    stopListening();
                    setIsScanning(false);
                  }}
                />
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Scan Results */}
        <AnimatePresence>
          {scanResult && (
            <PropertyResults
              result={scanResult}
              onClose={() => setScanResult(null)}
            />
          )}
        </AnimatePresence>

        {/* Error Display */}
        {scanError && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-red-500/20 border border-red-500/30 rounded-lg p-4 mb-6"
          >
            <div className="flex items-center gap-2 mb-2">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />
              <span className="font-semibold text-red-400">Scan Error</span>
            </div>
            <p className="text-red-300 jorge-code text-sm">{scanError}</p>
          </motion.div>
        )}

        {/* Empty State */}
        {!isScanning && !scanResult && !scanError && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-center py-12"
          >
            <BoltIcon className="w-16 h-16 text-jorge-electric mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-semibold mb-2 text-gray-300">
              Ready to Scan
            </h3>
            <p className="text-gray-400 jorge-code text-sm mb-6">
              Select a scan mode above to start property intelligence gathering
            </p>

            {/* Feature highlights */}
            <div className="grid grid-cols-2 gap-4 max-w-md mx-auto">
              {[
                { icon: '⚡', text: 'Instant CMA' },
                { icon: '📱', text: 'Offline Ready' },
                { icon: '🎯', text: 'GPS Tagged' },
                { icon: '🤖', text: 'Jorge Analysis' }
              ].map((feature) => (
                <div key={feature.text} className="flex items-center gap-2">
                  <span className="text-lg">{feature.icon}</span>
                  <span className="text-xs jorge-code text-gray-400">
                    {feature.text}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* Scan History Modal */}
      <AnimatePresence>
        {showHistory && (
          <ScanHistory
            history={scanHistory}
            onClose={() => setShowHistory(false)}
            onClearHistory={clearHistory}
            onSelectResult={setScanResult}
          />
        )}
      </AnimatePresence>

      {/* Loading overlay */}
      <AnimatePresence>
        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center"
          >
            <div className="bg-jorge-dark border border-jorge-electric rounded-xl p-6 text-center">
              <div className="w-8 h-8 border-2 border-jorge-electric border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-jorge-electric jorge-code font-semibold">
                Processing scan...
              </p>
              <p className="text-gray-400 jorge-code text-sm mt-1">
                Generating Jorge's analysis
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}