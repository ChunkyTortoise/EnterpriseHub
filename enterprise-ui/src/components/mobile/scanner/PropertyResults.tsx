/**
 * Jorge Real Estate AI Platform - Property Results Display
 * Professional property intelligence display with Jorge's confrontational analysis
 *
 * Features:
 * - Instant property data visualization
 * - Jorge's confrontational market analysis
 * - CMA generation and display
 * - Lead matching integration
 * - Market timing insights
 * - Professional client-ready presentation
 */

'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  HomeIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  ArrowArrowTrendingUpIcon,
  ArrowArrowTrendingDownIcon,
  ClockIcon,
  UserGroupIcon,
  ChartBarIcon,
  DocumentTextIcon,
  ShareIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  BoltIcon,
  EyeIcon,
  PhoneIcon
} from '@heroicons/react/24/outline';
import {
  HeartIcon,
  BookmarkIcon
} from '@heroicons/react/24/solid';

interface PropertyResultsProps {
  result: PropertyScanResult;
  onClose: () => void;
}

interface PropertyScanResult {
  property: {
    id: string;
    address: string;
    price: number;
    bedrooms: number;
    bathrooms: number;
    sqft: number;
    lotSize: number;
    yearBuilt: number;
    propertyType: string;
    status: string;
    daysOnMarket: number;
    mlsNumber: string;
    photos: string[];
  };
  marketAnalysis: {
    pricePerSqft: number;
    marketTrend: 'up' | 'down' | 'stable';
    trendPercentage: number;
    comparablesSold: number;
    avgDaysOnMarket: number;
    priceReduction: number;
    hotScore: number;
  };
  jorgeAnalysis: {
    verdict: string;
    confrontationalTone: string;
    redFlags: string[];
    opportunities: string[];
    recommendedAction: string;
    commission: number;
  };
  cma?: {
    lowEstimate: number;
    highEstimate: number;
    suggestedListing: number;
    comparables: Array<{
      address: string;
      price: number;
      sqft: number;
      daysOnMarket: number;
    }>;
  };
  scanning: {
    scanType: string;
    timestamp: number;
    location?: { lat: number; lng: number };
    confidence: number;
  };
}

export function PropertyResults({ result, onClose }: PropertyResultsProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'analysis' | 'cma' | 'comparables'>('overview');
  const [showFullAnalysis, setShowFullAnalysis] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [isSharing, setIsSharing] = useState(false);

  // Format currency
  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  // Format number with commas
  const formatNumber = (num: number): string => {
    return new Intl.NumberFormat('en-US').format(num);
  };

  // Calculate price per sqft
  const pricePerSqft = Math.round(result.property.price / result.property.sqft);

  // Market trend indicator
  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <ArrowTrendingUpIcon className="w-5 h-5 text-green-400" />;
      case 'down':
        return <ArrowTrendingDownIcon className="w-5 h-5 text-red-400" />;
      default:
        return <div className="w-5 h-5 rounded-full bg-yellow-400" />;
    }
  };

  // Hot score color
  const getHotScoreColor = (score: number) => {
    if (score >= 80) return 'text-red-400';
    if (score >= 60) return 'text-orange-400';
    if (score >= 40) return 'text-yellow-400';
    return 'text-gray-400';
  };

  // Save property
  const saveProperty = () => {
    setIsSaved(!isSaved);
    // TODO: Implement actual save to favorites/watchlist
  };

  // Share property
  const shareProperty = async () => {
    setIsSharing(true);

    try {
      if (navigator.share) {
        await navigator.share({
          title: `Property: ${result.property.address}`,
          text: `Check out this property analyzed by Jorge AI: ${formatCurrency(result.property.price)} - ${result.jorgeAnalysis.verdict}`,
          url: window.location.href
        });
      } else {
        // Fallback to clipboard
        await navigator.clipboard.writeText(
          `Property: ${result.property.address}\nPrice: ${formatCurrency(result.property.price)}\nJorge's Analysis: ${result.jorgeAnalysis.verdict}\n\nScanned with Jorge AI`
        );
        alert('Property details copied to clipboard!');
      }
    } catch (error) {
      console.error('Share failed:', error);
    } finally {
      setIsSharing(false);
    }
  };

  const tabs = [
    { id: 'overview', name: 'Overview', icon: HomeIcon },
    { id: 'analysis', name: 'Jorge AI', icon: BoltIcon },
    { id: 'cma', name: 'CMA', icon: ChartBarIcon },
    { id: 'comparables', name: 'Comps', icon: ArrowTrendingUpIcon }
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 50 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 50 }}
      className="fixed inset-x-0 bottom-0 top-1/3 bg-jorge-dark border-t border-jorge-electric rounded-t-2xl overflow-hidden z-40"
    >
      {/* Header */}
      <div className="sticky top-0 bg-jorge-dark/95 backdrop-blur-sm border-b border-white/10 p-4 z-10">
        <div className="flex items-center justify-between mb-4">
          <div className="flex-1">
            <h2 className="text-lg font-bold jorge-heading text-jorge-electric">
              🏠 Property Intelligence
            </h2>
            <p className="text-sm text-gray-400 jorge-code">
              {result.property.address}
            </p>
          </div>

          <div className="flex items-center gap-2">
            {/* Save button */}
            <motion.button
              onClick={saveProperty}
              whileTap={{ scale: 0.9 }}
              className="p-2 rounded-lg bg-white/10 jorge-haptic"
            >
              <BookmarkIcon
                className={`w-5 h-5 transition-colors ${
                  isSaved ? 'text-jorge-gold' : 'text-gray-400'
                }`}
              />
            </motion.button>

            {/* Share button */}
            <motion.button
              onClick={shareProperty}
              disabled={isSharing}
              whileTap={{ scale: 0.9 }}
              className="p-2 rounded-lg bg-white/10 jorge-haptic"
            >
              <ShareIcon className="w-5 h-5 text-gray-400" />
            </motion.button>

            {/* Close button */}
            <motion.button
              onClick={onClose}
              whileTap={{ scale: 0.9 }}
              className="p-2 rounded-lg bg-white/10 jorge-haptic"
            >
              <XMarkIcon className="w-5 h-5 text-gray-400" />
            </motion.button>
          </div>
        </div>

        {/* Key metrics */}
        <div className="grid grid-cols-4 gap-3">
          <div className="text-center">
            <div className="property-value text-xl font-bold">
              {formatCurrency(result.property.price)}
            </div>
            <div className="text-xs text-gray-400 jorge-code">Price</div>
          </div>

          <div className="text-center">
            <div className="text-jorge-electric text-xl font-bold jorge-code">
              {result.property.bedrooms}/{result.property.bathrooms}
            </div>
            <div className="text-xs text-gray-400 jorge-code">Bed/Bath</div>
          </div>

          <div className="text-center">
            <div className="text-white text-xl font-bold jorge-code">
              {formatNumber(result.property.sqft)}
            </div>
            <div className="text-xs text-gray-400 jorge-code">Sq Ft</div>
          </div>

          <div className="text-center">
            <div className={`text-xl font-bold jorge-code ${getHotScoreColor(result.marketAnalysis.hotScore)}`}>
              {result.marketAnalysis.hotScore}
            </div>
            <div className="text-xs text-gray-400 jorge-code">Hot Score</div>
          </div>
        </div>

        {/* Tab navigation */}
        <div className="flex gap-1 mt-4">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <motion.button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex-1 flex items-center justify-center gap-1 py-2 px-3 rounded-lg text-xs jorge-code font-semibold transition-colors ${
                  isActive
                    ? 'bg-jorge-electric text-black'
                    : 'bg-white/5 text-gray-400 hover:bg-white/10'
                } jorge-haptic`}
                whileTap={{ scale: 0.95 }}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.name}</span>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          {activeTab === 'overview' && (
            <motion.div
              key="overview"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-4 space-y-6"
            >
              {/* Property Details */}
              <div className="bg-white/5 rounded-xl p-4">
                <h3 className="text-lg font-bold jorge-text text-jorge-glow mb-3">
                  Property Details
                </h3>

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-400 jorge-code">Type:</span>
                      <span className="text-white jorge-text">{result.property.propertyType}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400 jorge-code">Year Built:</span>
                      <span className="text-white jorge-text">{result.property.yearBuilt}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400 jorge-code">Lot Size:</span>
                      <span className="text-white jorge-text">{formatNumber(result.property.lotSize)} sq ft</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-400 jorge-code">Status:</span>
                      <span className={`jorge-text font-semibold ${
                        result.property.status === 'Active' ? 'text-green-400' : 'text-yellow-400'
                      }`}>
                        {result.property.status}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400 jorge-code">Days on Market:</span>
                      <span className="text-white jorge-text">{result.property.daysOnMarket}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400 jorge-code">MLS #:</span>
                      <span className="text-white jorge-code">{result.property.mlsNumber}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Market Overview */}
              <div className="bg-white/5 rounded-xl p-4">
                <h3 className="text-lg font-bold jorge-text text-jorge-glow mb-3">
                  Market Overview
                </h3>

                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 jorge-code">Price per Sq Ft:</span>
                    <span className="text-jorge-electric font-bold jorge-code">
                      {formatCurrency(pricePerSqft)}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 jorge-code">Market Trend:</span>
                    <div className="flex items-center gap-2">
                      {getTrendIcon(result.marketAnalysis.marketTrend)}
                      <span className={`font-bold jorge-code ${
                        result.marketAnalysis.marketTrend === 'up' ? 'text-green-400' :
                        result.marketAnalysis.marketTrend === 'down' ? 'text-red-400' : 'text-yellow-400'
                      }`}>
                        {result.marketAnalysis.trendPercentage > 0 ? '+' : ''}{result.marketAnalysis.trendPercentage}%
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 jorge-code">Recent Sales:</span>
                    <span className="text-white jorge-text">
                      {result.marketAnalysis.comparablesSold} properties
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-gray-400 jorge-code">Avg Days on Market:</span>
                    <span className="text-white jorge-text">
                      {result.marketAnalysis.avgDaysOnMarket} days
                    </span>
                  </div>
                </div>
              </div>

              {/* Scan Details */}
              <div className="bg-white/5 rounded-xl p-4">
                <h3 className="text-lg font-bold jorge-text text-jorge-glow mb-3">
                  Scan Information
                </h3>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400 jorge-code">Scan Type:</span>
                    <span className="text-white jorge-text capitalize">{result.scanning.scanType}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400 jorge-code">Timestamp:</span>
                    <span className="text-white jorge-code">
                      {new Date(result.scanning.timestamp).toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400 jorge-code">Confidence:</span>
                    <span className={`jorge-code font-semibold ${
                      result.scanning.confidence > 0.8 ? 'text-green-400' :
                      result.scanning.confidence > 0.6 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {Math.round(result.scanning.confidence * 100)}%
                    </span>
                  </div>
                  {result.scanning.location && (
                    <div className="flex justify-between">
                      <span className="text-gray-400 jorge-code">GPS Location:</span>
                      <span className="text-jorge-glow jorge-code font-mono text-xs">
                        {result.scanning.location.lat.toFixed(6)}, {result.scanning.location.lng.toFixed(6)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'analysis' && (
            <motion.div
              key="analysis"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-4 space-y-6"
            >
              {/* Jorge's Verdict */}
              <div className="bg-gradient-to-r from-jorge-electric/20 to-jorge-glow/20 border border-jorge-electric/30 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-3">
                  <BoltIcon className="w-6 h-6 text-jorge-electric" />
                  <h3 className="text-lg font-bold jorge-heading text-jorge-electric">
                    Jorge's Verdict
                  </h3>
                </div>

                <p className="text-white jorge-text leading-relaxed mb-3">
                  {result.jorgeAnalysis.verdict}
                </p>

                <div className="bg-black/20 rounded-lg p-3">
                  <p className="text-jorge-glow jorge-text font-semibold italic">
                    "{result.jorgeAnalysis.confrontationalTone}"
                  </p>
                </div>
              </div>

              {/* Commission Calculator */}
              <div className="bg-jorge-gold/10 border border-jorge-gold/30 rounded-xl p-4">
                <h3 className="text-lg font-bold jorge-text text-jorge-gold mb-3">
                  💰 Jorge's 6% Commission
                </h3>

                <div className="text-center">
                  <div className="property-value text-3xl font-bold mb-2">
                    {formatCurrency(result.jorgeAnalysis.commission)}
                  </div>
                  <p className="text-jorge-gold/80 jorge-code text-sm">
                    Total commission at {formatCurrency(result.property.price)}
                  </p>
                </div>
              </div>

              {/* Red Flags */}
              {result.jorgeAnalysis.redFlags.length > 0 && (
                <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />
                    <h3 className="text-lg font-bold jorge-text text-red-400">
                      Red Flags
                    </h3>
                  </div>

                  <ul className="space-y-2">
                    {result.jorgeAnalysis.redFlags.map((flag, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-red-400 mt-1">•</span>
                        <span className="text-red-300 jorge-text text-sm">{flag}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Opportunities */}
              {result.jorgeAnalysis.opportunities.length > 0 && (
                <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <CheckCircleIcon className="w-5 h-5 text-green-400" />
                    <h3 className="text-lg font-bold jorge-text text-green-400">
                      Opportunities
                    </h3>
                  </div>

                  <ul className="space-y-2">
                    {result.jorgeAnalysis.opportunities.map((opportunity, index) => (
                      <li key={index} className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">•</span>
                        <span className="text-green-300 jorge-text text-sm">{opportunity}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recommended Action */}
              <div className="bg-jorge-electric/10 border border-jorge-electric/30 rounded-xl p-4">
                <h3 className="text-lg font-bold jorge-text text-jorge-electric mb-3">
                  ⚡ Recommended Action
                </h3>

                <p className="text-white jorge-text leading-relaxed">
                  {result.jorgeAnalysis.recommendedAction}
                </p>

                <div className="flex gap-3 mt-4">
                  <button className="flex-1 bg-jorge-gradient text-white py-2 px-4 rounded-lg jorge-code font-bold jorge-haptic">
                    Contact Lead
                  </button>
                  <button className="flex-1 bg-white/10 text-white py-2 px-4 rounded-lg jorge-code font-semibold jorge-haptic">
                    Schedule Viewing
                  </button>
                </div>
              </div>
            </motion.div>
          )}

          {activeTab === 'cma' && (
            <motion.div
              key="cma"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-4 space-y-6"
            >
              {result.cma ? (
                <>
                  {/* CMA Summary */}
                  <div className="bg-white/5 rounded-xl p-4">
                    <h3 className="text-lg font-bold jorge-text text-jorge-glow mb-4">
                      📊 Comparative Market Analysis
                    </h3>

                    <div className="grid grid-cols-3 gap-4 text-center mb-4">
                      <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-3">
                        <div className="text-red-400 font-bold jorge-code text-lg">
                          {formatCurrency(result.cma.lowEstimate)}
                        </div>
                        <div className="text-gray-400 jorge-code text-xs">Low</div>
                      </div>

                      <div className="bg-jorge-electric/20 border border-jorge-electric/30 rounded-lg p-3">
                        <div className="property-value font-bold jorge-code text-lg">
                          {formatCurrency(result.cma.suggestedListing)}
                        </div>
                        <div className="text-gray-400 jorge-code text-xs">Suggested</div>
                      </div>

                      <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-3">
                        <div className="text-green-400 font-bold jorge-code text-lg">
                          {formatCurrency(result.cma.highEstimate)}
                        </div>
                        <div className="text-gray-400 jorge-code text-xs">High</div>
                      </div>
                    </div>

                    {/* Price range */}
                    <div className="bg-black/20 rounded-lg p-3">
                      <div className="text-center text-white jorge-text">
                        Estimated Market Range: <span className="text-jorge-electric font-bold">
                          {formatCurrency(result.cma.lowEstimate)} - {formatCurrency(result.cma.highEstimate)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Comparables */}
                  <div className="bg-white/5 rounded-xl p-4">
                    <h3 className="text-lg font-bold jorge-text text-jorge-glow mb-4">
                      🏠 Recent Comparables
                    </h3>

                    <div className="space-y-3">
                      {result.cma.comparables.map((comp, index) => (
                        <div key={index} className="bg-black/20 rounded-lg p-3">
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex-1">
                              <div className="text-white jorge-text font-semibold text-sm">
                                {comp.address}
                              </div>
                              <div className="text-gray-400 jorge-code text-xs">
                                {formatNumber(comp.sqft)} sq ft • {comp.daysOnMarket} DOM
                              </div>
                            </div>
                            <div className="text-jorge-electric font-bold jorge-code">
                              {formatCurrency(comp.price)}
                            </div>
                          </div>

                          <div className="text-xs jorge-code text-gray-400">
                            ${Math.round(comp.price / comp.sqft)}/sq ft
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </>
              ) : (
                <div className="text-center py-12">
                  <ChartBarIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-300 mb-2">
                    CMA Generation in Progress
                  </h3>
                  <p className="text-gray-400 jorge-code text-sm">
                    Jorge is analyzing comparable properties...
                  </p>
                  <div className="w-8 h-8 border-2 border-jorge-electric border-t-transparent rounded-full animate-spin mx-auto mt-4" />
                </div>
              )}
            </motion.div>
          )}

          {activeTab === 'comparables' && (
            <motion.div
              key="comparables"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="p-4 space-y-6"
            >
              <div className="text-center py-12">
                <ArrowTrendingUpIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-300 mb-2">
                  Detailed Comparables
                </h3>
                <p className="text-gray-400 jorge-code text-sm">
                  Extended market analysis coming soon
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom Action Bar */}
      <div className="sticky bottom-0 bg-jorge-dark/95 backdrop-blur-sm border-t border-white/10 p-4">
        <div className="flex gap-3">
          <button className="flex-1 bg-jorge-gradient text-white py-3 px-4 rounded-lg jorge-code font-bold flex items-center justify-center gap-2 jorge-haptic">
            <PhoneIcon className="w-4 h-4" />
            Contact Lead
          </button>

          <button className="bg-white/10 border border-white/20 text-white py-3 px-4 rounded-lg jorge-code font-semibold jorge-haptic">
            <EyeIcon className="w-5 h-5" />
          </button>

          <button className="bg-white/10 border border-white/20 text-white py-3 px-4 rounded-lg jorge-code font-semibold jorge-haptic">
            <DocumentTextIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}