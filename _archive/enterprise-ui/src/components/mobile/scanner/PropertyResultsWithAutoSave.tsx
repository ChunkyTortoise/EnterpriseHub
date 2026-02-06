/**
 * Jorge Real Estate AI Platform - Property Results with Auto-Save
 * Enhanced PropertyResults component with comprehensive offline protection
 *
 * Features:
 * - Auto-save property scan results every 2 seconds
 * - Instant save on photo capture or property data generation
 * - Tab state persistence for better UX
 * - Bookmark state auto-save
 * - Offline resilience with visual feedback
 */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  HomeIcon,
  StarIcon,
  ShareIcon,
  DocumentTextIcon,
  ChartBarIcon,
  BuildingOffice2Icon,
  MapPinIcon,
  CalendarIcon,
  CurrencyDollarIcon,
  PhotoIcon,
  BookmarkIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid, BookmarkIcon as BookmarkIconSolid } from '@heroicons/react/24/solid';

import { AutoSaveIndicator, AutoSaveToast } from '@/components/mobile/AutoSaveIndicator';
import { usePropertyScanAutoSave } from '@/hooks/useAutoSave';

interface PropertyData {
  id: string;
  address: string;
  price: number;
  bedrooms: number;
  bathrooms: number;
  squareFootage: number;
  mlsId: string;
  daysOnMarket: number;
  listingType: 'sale' | 'rent';
  photos: string[];
  description?: string;
  coordinates?: { lat: number; lng: number };
  neighborhood?: string;
}

interface JorgeAnalysis {
  verdict: 'recommend' | 'caution' | 'avoid';
  confidence: number;
  reason: string;
  commission: number;
  marketPosition: 'hot' | 'warm' | 'cold';
  priceAnalysis: {
    isGoodDeal: boolean;
    priceVsMarket: number;
    comparables: Array<{
      address: string;
      price: number;
      soldDate: string;
      similarity: number;
    }>;
  };
}

interface CMAData {
  estimatedValue: number;
  confidenceRange: { min: number; max: number };
  marketTrends: {
    priceChange30d: number;
    priceChange90d: number;
    avgDaysOnMarket: number;
  };
  recommendations: string[];
}

interface PropertyScanResult {
  id: string;
  propertyData: PropertyData;
  jorgeAnalysis: JorgeAnalysis;
  cmaData: CMAData;
  scanMetadata: {
    timestamp: number;
    scanType: 'qr' | 'camera' | 'barcode' | 'voice';
    location?: { lat: number; lng: number };
    deviceInfo: string;
    qualityScore: number;
  };
  capturedPhoto?: string; // base64 or URL
  isBookmarked: boolean;
  userNotes?: string;
}

type TabType = 'overview' | 'analysis' | 'cma' | 'comparables';

interface PropertyResultsWithAutoSaveProps {
  scanResult: PropertyScanResult | null;
  isLoading?: boolean;
  onSave?: (result: PropertyScanResult) => void;
  onShare?: (result: PropertyScanResult) => void;
  onBookmark?: (propertyId: string, bookmarked: boolean) => void;
  onCapturePhoto?: () => void;
}

export function PropertyResultsWithAutoSave({
  scanResult,
  isLoading = false,
  onSave,
  onShare,
  onBookmark,
  onCapturePhoto
}: PropertyResultsWithAutoSaveProps) {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [showToast, setShowToast] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [userNotes, setUserNotes] = useState('');

  // Initialize auto-save with default scan result
  const initialScanResult: PropertyScanResult = {
    id: '',
    propertyData: {
      id: '',
      address: '',
      price: 0,
      bedrooms: 0,
      bathrooms: 0,
      squareFootage: 0,
      mlsId: '',
      daysOnMarket: 0,
      listingType: 'sale',
      photos: []
    },
    jorgeAnalysis: {
      verdict: 'recommend',
      confidence: 0,
      reason: '',
      commission: 0,
      marketPosition: 'warm',
      priceAnalysis: {
        isGoodDeal: false,
        priceVsMarket: 0,
        comparables: []
      }
    },
    cmaData: {
      estimatedValue: 0,
      confidenceRange: { min: 0, max: 0 },
      marketTrends: {
        priceChange30d: 0,
        priceChange90d: 0,
        avgDaysOnMarket: 0
      },
      recommendations: []
    },
    scanMetadata: {
      timestamp: Date.now(),
      scanType: 'qr',
      deviceInfo: navigator.userAgent.substring(0, 50),
      qualityScore: 1.0
    },
    isBookmarked: false
  };

  // Auto-save hook for property scan results
  const [autoSaveState, autoSaveActions] = usePropertyScanAutoSave(initialScanResult);

  // Update auto-save data when scanResult changes
  useEffect(() => {
    if (scanResult) {
      const updatedResult: PropertyScanResult = {
        ...scanResult,
        isBookmarked,
        userNotes: userNotes || scanResult.userNotes,
        scanMetadata: {
          ...scanResult.scanMetadata,
          timestamp: Date.now()
        }
      };

      autoSaveActions.setData(updatedResult);

      // Trigger immediate save for new scan results
      if (scanResult.id !== autoSaveState.data.id) {
        handleNewScanResult(updatedResult);
      }
    }
  }, [scanResult, isBookmarked, userNotes]);

  // Save immediately on new scan result
  const handleNewScanResult = useCallback(async (result: PropertyScanResult) => {
    try {
      const saved = await autoSaveActions.saveNow();
      if (saved) {
        setShowToast(true);
        onSave?.(result);
      }
    } catch (error) {
      console.error('Failed to save scan result:', error);
    }
  }, [autoSaveActions, onSave]);

  // Update tab state in auto-save
  useEffect(() => {
    autoSaveActions.updateData({
      userInterface: {
        activeTab,
        lastViewed: Date.now()
      }
    });
  }, [activeTab, autoSaveActions]);

  // Update user notes in auto-save
  const handleNotesChange = useCallback((notes: string) => {
    setUserNotes(notes);
    autoSaveActions.updateData({ userNotes: notes });
  }, [autoSaveActions]);

  // Handle bookmark toggle with auto-save
  const handleBookmarkToggle = useCallback(async () => {
    const newBookmarkState = !isBookmarked;
    setIsBookmarked(newBookmarkState);

    // Update auto-save immediately for bookmark changes
    autoSaveActions.updateData({ isBookmarked: newBookmarkState });
    await autoSaveActions.saveNow();

    onBookmark?.(autoSaveState.data.propertyData.id, newBookmarkState);
  }, [isBookmarked, autoSaveActions, onBookmark, autoSaveState.data.propertyData.id]);

  // Handle photo capture with auto-save
  const handleCapturePhoto = useCallback(async () => {
    onCapturePhoto?.();

    // Will be updated when photo is captured via props
    // The parent component should pass the captured photo in the scanResult
  }, [onCapturePhoto]);

  // Handle share with save
  const handleShare = useCallback(async () => {
    // Ensure data is saved before sharing
    await autoSaveActions.saveNow();
    onShare?.(autoSaveState.data);
  }, [autoSaveActions, onShare, autoSaveState.data]);

  if (isLoading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="jorge-glass p-6 rounded-xl"
      >
        <div className="flex items-center justify-center py-12">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          >
            <HomeIcon className="w-8 h-8 text-jorge-electric" />
          </motion.div>
          <span className="ml-3 text-jorge-electric font-medium">
            Analyzing property...
          </span>
        </div>
      </motion.div>
    );
  }

  if (!scanResult) {
    return (
      <div className="jorge-glass p-6 rounded-xl text-center text-gray-400">
        <HomeIcon className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p className="jorge-code text-sm">No property data available</p>
      </div>
    );
  }

  const { propertyData, jorgeAnalysis, cmaData } = scanResult;

  const tabs = [
    { id: 'overview', label: 'Overview', icon: HomeIcon },
    { id: 'analysis', label: 'Jorge\'s Take', icon: ChartBarIcon },
    { id: 'cma', label: 'Market Value', icon: CurrencyDollarIcon },
    { id: 'comparables', label: 'Comps', icon: BuildingOffice2Icon }
  ] as const;

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="jorge-glass rounded-xl overflow-hidden"
      >
        {/* Header with Auto-Save Indicator */}
        <div className="relative p-4 bg-gradient-to-r from-jorge-electric/20 via-jorge-glow/20 to-jorge-gold/20">
          <div className="absolute top-3 right-3">
            <AutoSaveIndicator
              status={autoSaveState.status}
              lastSaved={autoSaveState.lastSaved}
              saveCount={autoSaveState.saveCount}
              error={autoSaveState.error}
              size="sm"
              position="inline"
            />
          </div>

          <div className="flex items-start justify-between mb-3">
            <div className="flex-1 pr-12">
              <h2 className="text-lg font-bold text-white jorge-heading mb-1">
                {propertyData.address}
              </h2>
              <div className="flex items-center gap-3 text-sm text-gray-300">
                <span className="jorge-code">MLS: {propertyData.mlsId}</span>
                <span className="jorge-code">{propertyData.daysOnMarket} days</span>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="text-2xl font-bold text-jorge-glow jorge-heading">
              ${propertyData.price.toLocaleString()}
            </div>

            <div className="flex items-center gap-2">
              {/* Photo Capture Button */}
              <button
                onClick={handleCapturePhoto}
                className="p-2 bg-jorge-electric/20 text-jorge-electric rounded-lg jorge-haptic"
              >
                <PhotoIcon className="w-5 h-5" />
              </button>

              {/* Bookmark Button */}
              <button
                onClick={handleBookmarkToggle}
                className={`p-2 rounded-lg jorge-haptic ${
                  isBookmarked
                    ? 'bg-jorge-gold/20 text-jorge-gold'
                    : 'bg-white/10 text-gray-400'
                }`}
              >
                {isBookmarked ? (
                  <BookmarkIconSolid className="w-5 h-5" />
                ) : (
                  <BookmarkIcon className="w-5 h-5" />
                )}
              </button>

              {/* Share Button */}
              <button
                onClick={handleShare}
                className="p-2 bg-jorge-glow/20 text-jorge-glow rounded-lg jorge-haptic"
              >
                <ShareIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-white/10">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 flex items-center justify-center gap-2 px-3 py-3 text-xs font-medium transition-colors jorge-haptic ${
                activeTab === tab.id
                  ? 'text-jorge-electric border-b-2 border-jorge-electric bg-jorge-electric/10'
                  : 'text-gray-400 hover:text-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="p-4">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
            >
              {activeTab === 'overview' && (
                <div className="space-y-4">
                  {/* Property Details */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-xl font-bold text-jorge-glow">{propertyData.bedrooms}</div>
                      <div className="text-xs text-gray-400 jorge-code">Bedrooms</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold text-jorge-glow">{propertyData.bathrooms}</div>
                      <div className="text-xs text-gray-400 jorge-code">Bathrooms</div>
                    </div>
                    <div className="text-center">
                      <div className="text-xl font-bold text-jorge-glow">{propertyData.squareFootage.toLocaleString()}</div>
                      <div className="text-xs text-gray-400 jorge-code">Sq Ft</div>
                    </div>
                  </div>

                  {/* User Notes */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Agent Notes
                    </label>
                    <textarea
                      value={userNotes}
                      onChange={(e) => handleNotesChange(e.target.value)}
                      placeholder="Add your notes about this property..."
                      className="w-full p-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 resize-none jorge-code text-sm"
                      rows={3}
                    />
                  </div>
                </div>
              )}

              {activeTab === 'analysis' && (
                <div className="space-y-4">
                  {/* Jorge's Verdict */}
                  <div className={`p-4 rounded-lg border-l-4 ${
                    jorgeAnalysis.verdict === 'recommend'
                      ? 'bg-green-500/10 border-green-500'
                      : jorgeAnalysis.verdict === 'caution'
                        ? 'bg-orange-500/10 border-orange-500'
                        : 'bg-red-500/10 border-red-500'
                  }`}>
                    <div className="flex items-center gap-2 mb-2">
                      <div className={`text-lg font-bold ${
                        jorgeAnalysis.verdict === 'recommend'
                          ? 'text-green-400'
                          : jorgeAnalysis.verdict === 'caution'
                            ? 'text-orange-400'
                            : 'text-red-400'
                      }`}>
                        {jorgeAnalysis.verdict.toUpperCase()}
                      </div>
                      <div className="text-sm text-gray-400 jorge-code">
                        {Math.round(jorgeAnalysis.confidence * 100)}% confidence
                      </div>
                    </div>
                    <p className="text-gray-300 text-sm">{jorgeAnalysis.reason}</p>
                  </div>

                  {/* Commission & Market Position */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="jorge-card text-center">
                      <div className="text-xl font-bold text-jorge-gold">
                        ${jorgeAnalysis.commission.toLocaleString()}
                      </div>
                      <div className="text-xs text-gray-400 jorge-code">Commission (6%)</div>
                    </div>
                    <div className="jorge-card text-center">
                      <div className={`text-xl font-bold ${
                        jorgeAnalysis.marketPosition === 'hot'
                          ? 'text-red-400'
                          : jorgeAnalysis.marketPosition === 'warm'
                            ? 'text-orange-400'
                            : 'text-blue-400'
                      }`}>
                        {jorgeAnalysis.marketPosition.toUpperCase()}
                      </div>
                      <div className="text-xs text-gray-400 jorge-code">Market Position</div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'cma' && (
                <div className="space-y-4">
                  <div className="jorge-card text-center">
                    <div className="text-2xl font-bold text-jorge-glow mb-1">
                      ${cmaData.estimatedValue.toLocaleString()}
                    </div>
                    <div className="text-xs text-gray-400 jorge-code mb-3">Estimated Market Value</div>
                    <div className="text-sm text-gray-300">
                      Range: ${cmaData.confidenceRange.min.toLocaleString()} - ${cmaData.confidenceRange.max.toLocaleString()}
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h4 className="font-semibold text-white">Market Trends</h4>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="jorge-card text-center">
                        <div className={`text-lg font-bold ${
                          cmaData.marketTrends.priceChange30d >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {cmaData.marketTrends.priceChange30d >= 0 ? '+' : ''}{cmaData.marketTrends.priceChange30d}%
                        </div>
                        <div className="text-xs text-gray-400 jorge-code">30-Day Change</div>
                      </div>
                      <div className="jorge-card text-center">
                        <div className="text-lg font-bold text-jorge-electric">
                          {cmaData.marketTrends.avgDaysOnMarket}
                        </div>
                        <div className="text-xs text-gray-400 jorge-code">Avg Days on Market</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'comparables' && (
                <div className="space-y-3">
                  {jorgeAnalysis.priceAnalysis.comparables.map((comp, index) => (
                    <div key={index} className="jorge-card">
                      <div className="flex justify-between items-start mb-2">
                        <div className="text-sm font-medium text-white">{comp.address}</div>
                        <div className="text-sm font-bold text-jorge-glow">
                          ${comp.price.toLocaleString()}
                        </div>
                      </div>
                      <div className="flex justify-between text-xs text-gray-400">
                        <span className="jorge-code">Sold {comp.soldDate}</span>
                        <span className="jorge-code">{Math.round(comp.similarity * 100)}% similar</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </motion.div>

      {/* Success Toast */}
      <AnimatePresence>
        {showToast && (
          <AutoSaveToast
            status="saved"
            message="Property data saved locally"
            onClose={() => setShowToast(false)}
            autoHide={3000}
          />
        )}
      </AnimatePresence>
    </>
  );
}