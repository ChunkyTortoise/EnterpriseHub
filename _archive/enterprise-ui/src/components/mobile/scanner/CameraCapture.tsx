/**
 * Jorge Real Estate AI Platform - Camera Capture
 * Professional photo capture with GPS tagging and metadata
 *
 * Features:
 * - High-quality photo capture
 * - GPS coordinate tagging
 * - Property metadata embedding
 * - Image compression and optimization
 * - Instant photo preview
 * - Multiple format support
 */

'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  SunIcon,
  CameraIcon,
  PhotoIcon,
  MapPinIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowDownTrayIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

interface CameraCaptureProps {
  onPhotoCapture: (photoData: string) => void;
  onClose: () => void;
}

interface PhotoMetadata {
  timestamp: number;
  location: { lat: number; lng: number } | null;
  orientation: number;
  dimensions: { width: number; height: number };
  fileSize: number;
  quality: number;
}

interface CapturedPhoto {
  dataUrl: string;
  metadata: PhotoMetadata;
  thumbnail: string;
}

export function CameraCapture({ onPhotoCapture, onClose }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [isInitialized, setIsInitialized] = useState(false);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [error, setError] = useState<string>('');
  const [torchEnabled, setTorchEnabled] = useState(false);
  const [currentLocation, setCurrentLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [capturedPhoto, setCapturedPhoto] = useState<CapturedPhoto | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const [photoHistory, setPhotoHistory] = useState<CapturedPhoto[]>([]);

  // Camera constraints for high-quality photos
  const getCameraConstraints = useCallback(() => {
    return {
      video: {
        facingMode: 'environment', // Prefer rear camera
        width: { ideal: 1920, min: 1280 },
        height: { ideal: 1080, min: 720 },
        frameRate: { ideal: 30 },
        focusMode: 'continuous',
        exposureMode: 'continuous',
        whiteBalanceMode: 'continuous'
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

  // Get current location
  const getCurrentLocation = useCallback(() => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCurrentLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude
          });
        },
        (error) => {
          console.error('Location access failed:', error);
        },
        {
          enableHighAccuracy: true,
          timeout: 10000,
          maximumAge: 300000 // 5 minutes
        }
      );
    }
  }, []);

  // Cleanup camera
  const cleanup = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    setIsInitialized(false);
  }, []);

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

  // Capture photo
  const capturePhoto = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current || isCapturing) return;

    setIsCapturing(true);

    try {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      const ctx = canvas.getContext('2d');

      if (!ctx || video.readyState !== 4) {
        throw new Error('Video not ready');
      }

      // Set canvas dimensions
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Draw current frame
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Get high-quality image data
      const dataUrl = canvas.toDataURL('image/jpeg', 0.95);

      // Create thumbnail
      const thumbnailCanvas = document.createElement('canvas');
      const thumbnailCtx = thumbnailCanvas.getContext('2d');
      const thumbnailSize = 150;

      thumbnailCanvas.width = thumbnailSize;
      thumbnailCanvas.height = thumbnailSize;

      if (thumbnailCtx) {
        // Calculate aspect ratio for thumbnail
        const aspectRatio = canvas.width / canvas.height;
        let drawWidth = thumbnailSize;
        let drawHeight = thumbnailSize;
        let offsetX = 0;
        let offsetY = 0;

        if (aspectRatio > 1) {
          drawHeight = thumbnailSize / aspectRatio;
          offsetY = (thumbnailSize - drawHeight) / 2;
        } else {
          drawWidth = thumbnailSize * aspectRatio;
          offsetX = (thumbnailSize - drawWidth) / 2;
        }

        thumbnailCtx.drawImage(canvas, offsetX, offsetY, drawWidth, drawHeight);
      }

      const thumbnail = thumbnailCanvas.toDataURL('image/jpeg', 0.7);

      // Create metadata
      const metadata: PhotoMetadata = {
        timestamp: Date.now(),
        location: currentLocation,
        orientation: screen.orientation?.angle || 0,
        dimensions: {
          width: canvas.width,
          height: canvas.height
        },
        fileSize: Math.round(dataUrl.length * 0.75), // Approximate file size
        quality: 0.95
      };

      const photo: CapturedPhoto = {
        dataUrl,
        metadata,
        thumbnail
      };

      setCapturedPhoto(photo);
      setPhotoHistory(prev => [photo, ...prev.slice(0, 4)]); // Keep last 5 photos

      // Flash effect
      const flashDiv = document.createElement('div');
      flashDiv.className = 'fixed inset-0 bg-white pointer-events-none z-50';
      flashDiv.style.opacity = '0.8';
      document.body.appendChild(flashDiv);

      setTimeout(() => {
        document.body.removeChild(flashDiv);
      }, 100);

    } catch (error: any) {
      console.error('Photo capture failed:', error);
      setError(error.message || 'Photo capture failed');
    } finally {
      setIsCapturing(false);
    }
  }, [currentLocation, isCapturing]);

  // Use captured photo
  const usePhoto = useCallback(() => {
    if (!capturedPhoto) return;

    // Embed metadata in the photo data
    const photoWithMetadata = {
      image: capturedPhoto.dataUrl,
      metadata: capturedPhoto.metadata,
      type: 'property_photo'
    };

    onPhotoCapture(JSON.stringify(photoWithMetadata));
  }, [capturedPhoto, onPhotoCapture]);

  // Download photo
  const downloadPhoto = useCallback(() => {
    if (!capturedPhoto) return;

    const link = document.createElement('a');
    link.href = capturedPhoto.dataUrl;
    link.download = `jorge-property-photo-${new Date().toISOString().slice(0, 10)}.jpg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, [capturedPhoto]);

  // Format file size
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Format location
  const formatLocation = (location: { lat: number; lng: number } | null): string => {
    if (!location) return 'No location';
    return `${location.lat.toFixed(6)}, ${location.lng.toFixed(6)}`;
  };

  // Initialize on mount
  useEffect(() => {
    initializeCamera();
    getCurrentLocation();
    return cleanup;
  }, [initializeCamera, getCurrentLocation, cleanup]);

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
              📷 Property Camera
            </h3>
            <p className="text-sm text-gray-400 jorge-code">
              High-quality photos with GPS tagging
            </p>
          </div>

          <div className="flex items-center gap-2">
            {/* Location indicator */}
            <div className={`flex items-center gap-1 px-2 py-1 rounded-lg ${
              currentLocation ? 'bg-jorge-glow/20 text-jorge-glow' : 'bg-gray-500/20 text-gray-400'
            }`}>
              <MapPinIcon className="w-3 h-3" />
              <span className="text-xs jorge-code">GPS</span>
            </div>

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

      {/* Camera Area */}
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
                Initializing camera...
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

            {/* Hidden canvas for capture */}
            <canvas
              ref={canvasRef}
              className="hidden"
            />

            {/* Camera overlay */}
            <div className="absolute inset-0 pointer-events-none">
              {/* Grid lines for composition */}
              <div className="absolute inset-8">
                {/* Rule of thirds grid */}
                <div className="absolute inset-0">
                  {/* Vertical lines */}
                  <div className="absolute left-1/3 top-0 bottom-0 w-px bg-white/20" />
                  <div className="absolute left-2/3 top-0 bottom-0 w-px bg-white/20" />

                  {/* Horizontal lines */}
                  <div className="absolute top-1/3 left-0 right-0 h-px bg-white/20" />
                  <div className="absolute top-2/3 left-0 right-0 h-px bg-white/20" />
                </div>

                {/* Center focus point */}
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                  <div className="w-8 h-8 border-2 border-white rounded-full opacity-50" />
                </div>
              </div>

              {/* Capture flash effect */}
              {isCapturing && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: [0, 1, 0] }}
                  transition={{ duration: 0.2 }}
                  className="absolute inset-0 bg-white"
                />
              )}
            </div>
          </>
        )}
      </div>

      {/* Bottom controls */}
      <div className="absolute bottom-0 left-0 right-0 z-20 bg-black/80 backdrop-blur-sm p-4">
        <div className="flex items-center justify-center">
          {/* Capture button */}
          <motion.button
            onClick={capturePhoto}
            disabled={!isInitialized || isCapturing}
            className="w-16 h-16 rounded-full bg-white border-4 border-jorge-electric disabled:opacity-50 jorge-haptic"
            whileTap={{ scale: 0.9 }}
          >
            {isCapturing ? (
              <div className="w-8 h-8 border-2 border-jorge-electric border-t-transparent rounded-full animate-spin mx-auto" />
            ) : (
              <CameraIcon className="w-8 h-8 text-jorge-electric mx-auto" />
            )}
          </motion.button>
        </div>

        {/* Photo thumbnails */}
        {photoHistory.length > 0 && (
          <div className="flex justify-center gap-2 mt-3">
            {photoHistory.slice(0, 3).map((photo, index) => (
              <motion.img
                key={photo.metadata.timestamp}
                src={photo.thumbnail}
                alt={`Photo ${index + 1}`}
                className="w-12 h-12 rounded-lg border border-white/20 object-cover jorge-haptic"
                style={{ opacity: 0.8 - (index * 0.2) }}
                onClick={() => setCapturedPhoto(photo)}
                whileTap={{ scale: 0.9 }}
              />
            ))}
          </div>
        )}

        {/* Location and metadata */}
        <div className="flex items-center justify-between mt-3 text-xs jorge-code text-gray-400">
          <div className="flex items-center gap-2">
            <MapPinIcon className="w-3 h-3" />
            <span>{formatLocation(currentLocation)}</span>
          </div>

          <div className="flex items-center gap-2">
            <ClockIcon className="w-3 h-3" />
            <span>{new Date().toLocaleTimeString()}</span>
          </div>
        </div>
      </div>

      {/* Photo preview modal */}
      <AnimatePresence>
        {capturedPhoto && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-jorge-dark border border-jorge-electric rounded-xl max-w-md w-full max-h-[90vh] overflow-hidden"
            >
              {/* Preview header */}
              <div className="p-4 border-b border-white/10">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold jorge-heading text-jorge-electric">
                    📷 Photo Preview
                  </h3>
                  <button
                    onClick={() => setCapturedPhoto(null)}
                    className="p-2 rounded-lg bg-white/10 text-gray-400 hover:text-white transition-colors jorge-haptic"
                  >
                    <XMarkIcon className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Photo */}
              <div className="p-4">
                <img
                  src={capturedPhoto.dataUrl}
                  alt="Captured property photo"
                  className="w-full rounded-lg border border-white/10"
                />

                {/* Metadata */}
                <div className="grid grid-cols-2 gap-4 mt-4 text-xs jorge-code">
                  <div className="space-y-2">
                    <div>
                      <span className="text-gray-400">Dimensions:</span>
                      <div className="text-white">
                        {capturedPhoto.metadata.dimensions.width} × {capturedPhoto.metadata.dimensions.height}
                      </div>
                    </div>

                    <div>
                      <span className="text-gray-400">File Size:</span>
                      <div className="text-white">
                        {formatFileSize(capturedPhoto.metadata.fileSize)}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div>
                      <span className="text-gray-400">Quality:</span>
                      <div className="text-white">
                        {Math.round(capturedPhoto.metadata.quality * 100)}%
                      </div>
                    </div>

                    <div>
                      <span className="text-gray-400">GPS:</span>
                      <div className={`${capturedPhoto.metadata.location ? 'text-jorge-glow' : 'text-red-400'}`}>
                        {capturedPhoto.metadata.location ? '✓ Tagged' : '✗ No location'}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Location details */}
                {capturedPhoto.metadata.location && (
                  <div className="mt-3 p-3 bg-jorge-glow/10 border border-jorge-glow/20 rounded-lg">
                    <div className="text-xs jorge-code text-gray-400 mb-1">GPS Coordinates</div>
                    <div className="text-xs jorge-code text-jorge-glow font-mono">
                      {formatLocation(capturedPhoto.metadata.location)}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-3 mt-4">
                  <button
                    onClick={downloadPhoto}
                    className="flex-1 bg-white/10 border border-white/20 text-white py-2 px-4 rounded-lg flex items-center justify-center gap-2 jorge-code font-semibold jorge-haptic"
                  >
                    <ArrowDownTrayIcon className="w-4 h-4" />
                    Download
                  </button>

                  <button
                    onClick={usePhoto}
                    className="flex-1 bg-jorge-gradient text-white py-2 px-4 rounded-lg flex items-center justify-center gap-2 jorge-code font-bold jorge-haptic"
                  >
                    <CheckCircleIcon className="w-4 h-4" />
                    Use Photo
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

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