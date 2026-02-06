/**
 * Jorge Real Estate AI Platform - QR Code Scanner
 * High-performance QR code and barcode scanning for property intelligence
 *
 * Features:
 * - Real-time QR code detection using html5-qrcode library
 * - Barcode scanning support (Code128, Code39, EAN, UPC)
 * - Multiple format support optimized for real estate
 * - Torch/flashlight control for low-light scanning
 * - Professional UI integrated with Jorge's design system
 * - Battery-optimized scanning performance
 */

'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  SunIcon,
  CameraIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  BoltIcon
} from '@heroicons/react/24/outline';
import { Html5QrcodeScanner, Html5QrcodeSupportedFormats, Html5QrcodeResult } from 'html5-qrcode';
interface QRScannerProps {
  onScanComplete: (data: string) => void;
  onClose: () => void;
  mode?: 'qr' | 'barcode';
}

interface ScanResult {
  data: string;
  format: string;
  timestamp: number;
  confidence: number;
}

export function QRScanner({ onScanComplete, onClose, mode = 'qr' }: QRScannerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const scannerRef = useRef<Html5QrcodeScanner | null>(null);
  const scannerDivRef = useRef<HTMLDivElement>(null);

  const [isInitialized, setIsInitialized] = useState(false);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [error, setError] = useState<string>('');
  const [torchEnabled, setTorchEnabled] = useState(false);
  const [scanHistory, setScanHistory] = useState<ScanResult[]>([]);
  const [isScanning, setIsScanning] = useState(true);
  const [lastScanTime, setLastScanTime] = useState(0);

  // Get supported formats based on mode
  const getSupportedFormats = useCallback(() => {
    if (mode === 'barcode') {
      return [
        Html5QrcodeSupportedFormats.CODE_128,
        Html5QrcodeSupportedFormats.CODE_39,
        Html5QrcodeSupportedFormats.EAN_13,
        Html5QrcodeSupportedFormats.EAN_8,
        Html5QrcodeSupportedFormats.UPC_A,
        Html5QrcodeSupportedFormats.UPC_E,
        Html5QrcodeSupportedFormats.QR_CODE // Include QR for hybrid scanning
      ];
    } else {
      return [
        Html5QrcodeSupportedFormats.QR_CODE,
        Html5QrcodeSupportedFormats.CODE_128, // Include common barcodes
        Html5QrcodeSupportedFormats.CODE_39
      ];
    }
  }, [mode]);

  // Scanner configuration optimized for real estate field agents
  const getScannerConfig = useCallback(() => {
    return {
      fps: 10, // Conservative for battery life
      qrbox: { width: 250, height: 250 }, // Adequate scan area
      aspectRatio: 1.0, // Square scan area
      disableFlip: false, // Allow scanning flipped codes
      supportedScanTypes: getSupportedFormats(),
      videoConstraints: {
        facingMode: 'environment', // Prefer rear camera
        advanced: [
          {
            focusMode: 'continuous',
            zoom: 1.0
          }
        ]
      }
    };
  }, [getSupportedFormats]);

  // Initialize real QR/barcode scanner
  const initializeScanner = useCallback(async () => {
    try {
      setError('');

      if (!scannerDivRef.current) {
        setError('Scanner container not available');
        return;
      }

      const config = getScannerConfig();
      const scanner = new Html5QrcodeScanner('qr-scanner-container', config, false);

      scannerRef.current = scanner;

      // Handle successful scan
      const onScanSuccess = (decodedText: string, decodedResult: Html5QrcodeResult) => {
        const result: ScanResult = {
          data: decodedText,
          format: decodedResult.result.format?.formatName || 'Unknown',
          timestamp: Date.now(),
          confidence: 0.95 // html5-qrcode doesn't provide confidence scores
        };

        setLastScanTime(Date.now());
        setScanHistory(prev => [result, ...prev.slice(0, 4)]);
        setIsScanning(false);

        // Brief success feedback, then report result
        setTimeout(() => {
          onScanComplete(decodedText);
        }, 500);
      };

      // Handle scan errors (mostly "No QR code found", which is normal)
      const onScanError = (errorMessage: string) => {
        // Only show actual errors, not "No QR code found" messages
        if (!errorMessage.includes('No QR code found') &&
            !errorMessage.includes('No barcode found') &&
            !errorMessage.includes('NotFoundException')) {
          console.warn('QR Scanner error:', errorMessage);
        }
      };

      // Start scanning
      scanner.render(onScanSuccess, onScanError);

      setHasPermission(true);
      setIsInitialized(true);

    } catch (error: any) {
      console.error('Scanner initialization failed:', error);
      setHasPermission(false);
      setError(error.message || 'Scanner initialization failed');
    }
  }, [getScannerConfig, onScanComplete]);

  // Cleanup scanner
  const cleanup = useCallback(async () => {
    try {
      if (scannerRef.current) {
        await scannerRef.current.clear();
        scannerRef.current = null;
      }
    } catch (error) {
      console.warn('Scanner cleanup warning:', error);
    }

    setIsInitialized(false);
    setIsScanning(true); // Reset for next use
  }, []);

  // Get current camera stream for torch control
  const getCameraStream = useCallback(async (): Promise<MediaStream | null> => {
    try {
      // The Html5QrcodeScanner manages its own video stream
      // We need to access it for torch control
      const video = document.querySelector('#qr-scanner-container video') as HTMLVideoElement;
      if (video && video.srcObject) {
        return video.srcObject as MediaStream;
      }
    } catch (error) {
      console.warn('Could not access camera stream for torch control:', error);
    }
    return null;
  }, []);

  // Toggle torch
  const toggleTorch = useCallback(async () => {
    try {
      const stream = await getCameraStream();
      if (!stream) {
        console.warn('Camera stream not available for torch control');
        return;
      }

      const track = stream.getVideoTracks()[0];
      if (!track) {
        console.warn('Video track not available for torch control');
        return;
      }

      const capabilities = track.getCapabilities?.();
      if (!capabilities?.torch) {
        console.warn('Torch not supported on this device');
        return;
      }

      await track.applyConstraints({
        advanced: [{ torch: !torchEnabled } as any]
      });
      setTorchEnabled(!torchEnabled);
    } catch (error) {
      console.error('Torch toggle failed:', error);
      setError('Torch control not available');
    }
  }, [torchEnabled, getCameraStream]);

  // Initialize scanner on mount
  useEffect(() => {
    initializeScanner();
    return cleanup;
  }, [initializeScanner, cleanup]);

  const getScannerTitle = () => {
    switch (mode) {
      case 'barcode':
        return '📋 Barcode Scanner';
      default:
        return '📱 QR Code Scanner';
    }
  };

  const getScannerInstructions = () => {
    switch (mode) {
      case 'barcode':
        return 'Align barcode within the frame';
      default:
        return 'Center QR code in the scanning area';
    }
  };

  return (
    <>
      {/* Custom styles to override html5-qrcode defaults and integrate with Jorge theme */}
      <style jsx>{`
        #qr-scanner-container {
          border: none !important;
          border-radius: 0 !important;
        }

        #qr-scanner-container video {
          border-radius: 0 !important;
          object-fit: cover !important;
        }

        #qr-scanner-container div[id*="qr-shaded-region"] {
          background: rgba(0, 0, 0, 0.6) !important;
        }

        #qr-scanner-container div[id*="qr-scanner"] {
          border: 2px solid #0052FF !important;
          border-radius: 12px !important;
        }

        #qr-scanner-container button {
          display: none !important; /* Hide html5-qrcode buttons */
        }

        #qr-scanner-container select {
          display: none !important; /* Hide camera selection */
        }
      `}</style>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative bg-black rounded-xl overflow-hidden border border-jorge-electric/30"
      >
      {/* Header */}
      <div className="absolute top-0 left-0 right-0 z-20 bg-black/80 backdrop-blur-sm p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold jorge-heading text-jorge-electric">
              {getScannerTitle()}
            </h3>
            <p className="text-sm text-gray-400 jorge-code">
              {getScannerInstructions()}
            </p>
          </div>

          <div className="flex items-center gap-2">
            {/* Torch toggle */}
            <button
              onClick={toggleTorch}
              className={`p-2 rounded-lg transition-colors ${
                torchEnabled
                  ? 'bg-yellow-500/20 text-yellow-400'
                  : 'bg-white/10 text-gray-400'
              } jorge-haptic`}
            >
              <SunIcon className="w-5 h-5" />
            </button>

            {/* Close button */}
            <button
              onClick={onClose}
              className="p-2 rounded-lg bg-white/10 text-gray-400 hover:text-white transition-colors jorge-haptic"
            >
              <XMarkIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Scanner Area */}
      <div className="relative aspect-[4/3] bg-black">
        {hasPermission === false ? (
          // Permission denied state
          <div className="absolute inset-0 flex items-center justify-center text-center p-6">
            <div>
              <ExclamationTriangleIcon className="w-16 h-16 text-red-400 mx-auto mb-4" />
              <h3 className="text-lg font-bold text-red-400 mb-2">Camera Access Required</h3>
              <p className="text-gray-400 jorge-code text-sm mb-4">
                {error}
              </p>
              <button
                onClick={initializeScanner}
                className="bg-jorge-gradient text-white py-2 px-4 rounded-lg jorge-code font-semibold jorge-haptic"
              >
                Retry Access
              </button>
            </div>
          </div>
        ) : !isInitialized ? (
          // Loading state
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <CameraIcon className="w-16 h-16 text-jorge-electric mx-auto mb-4 animate-pulse" />
              <p className="text-jorge-electric jorge-code font-semibold">
                Initializing scanner...
              </p>
            </div>
          </div>
        ) : (
          <>
            {/* QR Scanner Container */}
            <div
              id="qr-scanner-container"
              ref={scannerDivRef}
              className="w-full h-full"
              style={{
                // Override html5-qrcode default styles
                border: 'none',
                borderRadius: '0',
              }}
            />

            {/* Scanning overlay */}
            <div className="absolute inset-0 pointer-events-none z-10">
              {/* Scan area frame */}
              <div className="absolute inset-8 border-2 border-jorge-electric rounded-lg">
                {/* Animated scanning line */}
                <motion.div
                  className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-jorge-electric to-transparent"
                  animate={{
                    y: [0, '100%', 0]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />

                {/* Corner indicators */}
                {['top-left', 'top-right', 'bottom-left', 'bottom-right'].map((corner) => (
                  <div
                    key={corner}
                    className={`absolute w-6 h-6 border-4 border-jorge-electric ${
                      corner.includes('top') ? '-top-2' : '-bottom-2'
                    } ${
                      corner.includes('left') ? '-left-2' : '-right-2'
                    } ${
                      corner.includes('top') && corner.includes('left') ? 'border-r-0 border-b-0' :
                      corner.includes('top') && corner.includes('right') ? 'border-l-0 border-b-0' :
                      corner.includes('bottom') && corner.includes('left') ? 'border-r-0 border-t-0' :
                      'border-l-0 border-t-0'
                    }`}
                  />
                ))}
              </div>

              {/* Scan success indicator */}
              <AnimatePresence>
                {!isScanning && (
                  <motion.div
                    initial={{ scale: 0, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0, opacity: 0 }}
                    className="absolute inset-0 bg-jorge-electric/20 flex items-center justify-center"
                  >
                    <div className="text-center">
                      <CheckCircleIcon className="w-16 h-16 text-jorge-glow mx-auto mb-2" />
                      <p className="text-jorge-glow jorge-code font-bold">Scan Complete!</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </>
        )}
      </div>

      {/* Bottom controls */}
      <div className="absolute bottom-0 left-0 right-0 z-20 bg-black/80 backdrop-blur-sm p-4">
        <div className="flex items-center justify-between">
          {/* Scan history */}
          <div className="flex items-center gap-2">
            <span className="text-xs jorge-code text-gray-400">History:</span>
            <div className="flex gap-1">
              {scanHistory.slice(0, 3).map((result, index) => (
                <div
                  key={`${result.timestamp}-${index}`}
                  className="w-2 h-2 bg-jorge-glow rounded-full opacity-60"
                  style={{ opacity: 0.8 - (index * 0.2) }}
                />
              ))}
            </div>
          </div>

          {/* Status */}
          <div className="text-center">
            {isScanning ? (
              <div className="flex items-center gap-2">
                <BoltIcon className="w-4 h-4 text-jorge-electric animate-pulse" />
                <span className="text-jorge-electric jorge-code text-sm font-semibold">
                  SCANNING...
                </span>
              </div>
            ) : (
              <span className="text-jorge-glow jorge-code text-sm font-semibold">
                PROCESSING...
              </span>
            )}
          </div>

          {/* Instructions */}
          <div className="text-right">
            <span className="text-xs jorge-code text-gray-400">
              {mode === 'barcode' ? 'Barcode' : 'QR Code'}
            </span>
          </div>
        </div>
      </div>

      {/* Error display */}
      {error && hasPermission !== false && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-20 left-4 right-4 bg-red-500/20 border border-red-500/30 rounded-lg p-3"
        >
          <div className="flex items-center gap-2">
            <ExclamationTriangleIcon className="w-4 h-4 text-red-400" />
            <span className="text-red-300 jorge-code text-sm">
              {error}
            </span>
          </div>
        </motion.div>
      )}
    </motion.div>
    </>
  );
}