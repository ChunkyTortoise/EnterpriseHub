/**
 * Jorge Real Estate AI Platform - QR Code Scanner
 * High-performance QR code and barcode scanning for property intelligence
 *
 * Features:
 * - Real-time QR code detection
 * - Barcode scanning support
 * - Multiple format support (QR, Code128, EAN, etc.)
 * - Torch/flashlight control
 * - Scan area targeting
 * - Performance optimizations for mobile
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

// Mock QR scanner - In production, use a library like @zxing/library or html5-qrcode
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
  const animationRef = useRef<number>();

  const [isInitialized, setIsInitialized] = useState(false);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [error, setError] = useState<string>('');
  const [torchEnabled, setTorchEnabled] = useState(false);
  const [scanHistory, setScanHistory] = useState<ScanResult[]>([]);
  const [isScanning, setIsScanning] = useState(true);
  const [lastScanTime, setLastScanTime] = useState(0);

  // Camera constraints for optimal scanning
  const getCameraConstraints = useCallback(() => {
    return {
      video: {
        facingMode: 'environment', // Prefer rear camera
        width: { ideal: 1280, min: 640 },
        height: { ideal: 720, min: 480 },
        frameRate: { ideal: 30, min: 15 },
        focusMode: 'continuous',
        zoom: 1
      },
      audio: false
    };
  }, []);

  // Initialize camera
  const initializeCamera = useCallback(async () => {
    try {
      setError('');

      const constraints = getCameraConstraints();
      const stream = await navigator.mediaDevices.getUserMedia(constraints);

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;

        // Wait for video to load
        await new Promise<void>((resolve, reject) => {
          if (!videoRef.current) return reject(new Error('Video element not available'));

          videoRef.current.onloadedmetadata = () => {
            videoRef.current?.play()
              .then(() => resolve())
              .catch(reject);
          };

          videoRef.current.onerror = () => reject(new Error('Video load failed'));
        });

        setHasPermission(true);
        setIsInitialized(true);

        // Check torch capability
        const track = stream.getVideoTracks()[0];
        const capabilities = track.getCapabilities?.();
        if (capabilities?.torch) {
          // Torch is supported
        }
      }
    } catch (error: any) {
      console.error('Camera initialization failed:', error);
      setHasPermission(false);
      setError(error.message || 'Camera access denied');
    }
  }, [getCameraConstraints]);

  // Cleanup camera
  const cleanup = useCallback(() => {
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }

    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    setIsInitialized(false);
  }, []);

  // Mock QR code detection - Replace with actual scanner library
  const detectQRCode = useCallback((): ScanResult | null => {
    if (!videoRef.current || !canvasRef.current || !isScanning) return null;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (!ctx || video.readyState !== 4) return null;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Mock QR detection with sample data
    // In production, use a real QR detection library here
    const mockDetection = Math.random() < 0.01; // 1% chance per frame

    if (mockDetection) {
      // Simulate different types of scanned data
      const sampleData = [
        'https://jorge.ai/property/12345',
        'LOCKBOX:9874',
        'MLS:RE0012345',
        'PROPERTY:123 Main St, City, State 12345',
        '{"propertyId":"prop_123","address":"456 Oak Ave","price":450000}'
      ];

      const randomData = sampleData[Math.floor(Math.random() * sampleData.length)];

      return {
        data: randomData,
        format: mode === 'barcode' ? 'Code128' : 'QR_CODE',
        timestamp: Date.now(),
        confidence: 0.85 + Math.random() * 0.15 // 85-100% confidence
      };
    }

    return null;
  }, [isScanning, mode]);

  // Scanning loop
  const scan = useCallback(() => {
    if (!isInitialized || !isScanning) return;

    const now = Date.now();

    // Rate limiting - prevent too frequent scans
    if (now - lastScanTime < 100) {
      animationRef.current = requestAnimationFrame(scan);
      return;
    }

    const result = detectQRCode();

    if (result) {
      setLastScanTime(now);
      setScanHistory(prev => [result, ...prev.slice(0, 4)]); // Keep last 5 results

      // Success feedback
      setIsScanning(false);

      // Brief delay for user feedback, then report result
      setTimeout(() => {
        onScanComplete(result.data);
      }, 500);

      return;
    }

    // Continue scanning
    animationRef.current = requestAnimationFrame(scan);
  }, [detectQRCode, isInitialized, isScanning, lastScanTime, onScanComplete]);

  // Toggle torch
  const toggleTorch = useCallback(async () => {
    if (!streamRef.current) return;

    try {
      const track = streamRef.current.getVideoTracks()[0];
      await track.applyConstraints({
        advanced: [{ torch: !torchEnabled } as any]
      });
      setTorchEnabled(!torchEnabled);
    } catch (error) {
      console.error('Torch toggle failed:', error);
    }
  }, [torchEnabled]);

  // Initialize on mount
  useEffect(() => {
    initializeCamera();
    return cleanup;
  }, [initializeCamera, cleanup]);

  // Start scanning when initialized
  useEffect(() => {
    if (isInitialized && isScanning) {
      animationRef.current = requestAnimationFrame(scan);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isInitialized, isScanning, scan]);

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
                onClick={initializeCamera}
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
            {/* Video feed */}
            <video
              ref={videoRef}
              className="w-full h-full object-cover"
              playsInline
              muted
            />

            {/* Hidden canvas for image processing */}
            <canvas
              ref={canvasRef}
              className="hidden"
            />

            {/* Scanning overlay */}
            <div className="absolute inset-0 pointer-events-none">
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
  );
}