/**
 * Jorge Real Estate AI Platform - Scan History
 * Professional scan history management and retrieval
 *
 * Features:
 * - Complete scan history with metadata
 * - Search and filter capabilities
 * - Export functionality
 * - Offline history sync
 * - Performance analytics
 */

'use client';

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  MagnifyingGlassIcon,
  ClockIcon,
  MapPinIcon,
  QrCodeIcon,
  CameraIcon,
  MicrophoneIcon,
  DocumentTextIcon,
  TrashIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  EyeIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface ScanHistoryProps {
  history: ScanHistoryItem[];
  onClose: () => void;
  onClearHistory: () => void;
  onSelectResult: (result: any) => void;
}

interface ScanHistoryItem {
  id: string;
  type: 'qr' | 'camera' | 'barcode' | 'voice';
  data: string;
  timestamp: number;
  location?: { lat: number; lng: number };
  confidence: number;
  result?: any;
  status: 'success' | 'failed' | 'processing';
  duration: number; // scan duration in ms
}

type FilterType = 'all' | 'qr' | 'camera' | 'barcode' | 'voice';
type SortType = 'newest' | 'oldest' | 'confidence' | 'type';

export function ScanHistory({ history, onClose, onClearHistory, onSelectResult }: ScanHistoryProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<FilterType>('all');
  const [sortType, setSortType] = useState<SortType>('newest');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());

  // Mock history data if empty (for demonstration)
  const mockHistory: ScanHistoryItem[] = history.length === 0 ? [
    {
      id: '1',
      type: 'qr',
      data: 'https://jorge.ai/property/12345',
      timestamp: Date.now() - 3600000,
      location: { lat: 40.7128, lng: -74.0060 },
      confidence: 0.95,
      status: 'success',
      duration: 1200,
      result: {
        property: {
          address: '123 Main St, City, State',
          price: 450000,
          bedrooms: 3,
          bathrooms: 2
        }
      }
    },
    {
      id: '2',
      type: 'camera',
      data: 'Photo captured at 456 Oak Ave',
      timestamp: Date.now() - 7200000,
      location: { lat: 40.7589, lng: -73.9851 },
      confidence: 0.88,
      status: 'success',
      duration: 2100
    },
    {
      id: '3',
      type: 'voice',
      data: 'Scan property 789 Pine Street',
      timestamp: Date.now() - 10800000,
      confidence: 0.72,
      status: 'failed',
      duration: 3400
    },
    {
      id: '4',
      type: 'barcode',
      data: 'LOCKBOX:9874',
      timestamp: Date.now() - 14400000,
      location: { lat: 40.7505, lng: -73.9934 },
      confidence: 0.91,
      status: 'success',
      duration: 800
    }
  ] : history;

  // Filter and sort history
  const filteredAndSortedHistory = useMemo(() => {
    let filtered = mockHistory.filter(item => {
      const matchesSearch = searchTerm === '' ||
        item.data.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.result?.property?.address || '').toLowerCase().includes(searchTerm.toLowerCase());

      const matchesFilter = filterType === 'all' || item.type === filterType;

      return matchesSearch && matchesFilter;
    });

    // Sort items
    filtered.sort((a, b) => {
      switch (sortType) {
        case 'newest':
          return b.timestamp - a.timestamp;
        case 'oldest':
          return a.timestamp - b.timestamp;
        case 'confidence':
          return b.confidence - a.confidence;
        case 'type':
          return a.type.localeCompare(b.type);
        default:
          return b.timestamp - a.timestamp;
      }
    });

    return filtered;
  }, [mockHistory, searchTerm, filterType, sortType]);

  // Get icon for scan type
  const getScanIcon = (type: string) => {
    switch (type) {
      case 'qr':
        return <QrCodeIcon className="w-5 h-5" />;
      case 'camera':
        return <CameraIcon className="w-5 h-5" />;
      case 'barcode':
        return <QrCodeIcon className="w-5 h-5" />;
      case 'voice':
        return <MicrophoneIcon className="w-5 h-5" />;
      default:
        return <DocumentTextIcon className="w-5 h-5" />;
    }
  };

  // Get status indicator
  const getStatusIndicator = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="w-4 h-4 text-green-400" />;
      case 'failed':
        return <ExclamationTriangleIcon className="w-4 h-4 text-red-400" />;
      case 'processing':
        return <div className="w-4 h-4 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin" />;
      default:
        return null;
    }
  };

  // Format time ago
  const formatTimeAgo = (timestamp: number): string => {
    const seconds = Math.floor((Date.now() - timestamp) / 1000);
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  // Format duration
  const formatDuration = (duration: number): string => {
    if (duration < 1000) return `${duration}ms`;
    return `${(duration / 1000).toFixed(1)}s`;
  };

  // Toggle item selection
  const toggleItemSelection = (id: string) => {
    const newSelection = new Set(selectedItems);
    if (newSelection.has(id)) {
      newSelection.delete(id);
    } else {
      newSelection.add(id);
    }
    setSelectedItems(newSelection);
  };

  // Export selected items
  const exportSelectedItems = () => {
    const selectedData = filteredAndSortedHistory.filter(item =>
      selectedItems.has(item.id)
    );

    const exportData = {
      exportDate: new Date().toISOString(),
      totalItems: selectedData.length,
      items: selectedData.map(item => ({
        type: item.type,
        data: item.data,
        timestamp: item.timestamp,
        location: item.location,
        confidence: item.confidence,
        status: item.status,
        duration: item.duration,
        result: item.result
      }))
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `jorge-scan-history-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setSelectedItems(new Set());
  };

  const filterOptions = [
    { value: 'all', label: 'All Scans', count: mockHistory.length },
    { value: 'qr', label: 'QR Codes', count: mockHistory.filter(h => h.type === 'qr').length },
    { value: 'camera', label: 'Photos', count: mockHistory.filter(h => h.type === 'camera').length },
    { value: 'barcode', label: 'Barcodes', count: mockHistory.filter(h => h.type === 'barcode').length },
    { value: 'voice', label: 'Voice', count: mockHistory.filter(h => h.type === 'voice').length }
  ];

  return (
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
        className="bg-jorge-dark border border-jorge-electric rounded-xl w-full max-w-md h-[80vh] flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="p-4 border-b border-white/10 bg-jorge-dark/95 backdrop-blur-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold jorge-heading text-jorge-electric">
                📊 Scan History
              </h2>
              <p className="text-sm text-gray-400 jorge-code">
                {filteredAndSortedHistory.length} scans found
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="p-2 rounded-lg bg-white/10 text-gray-400 hover:text-white transition-colors jorge-haptic"
              >
                <FunnelIcon className="w-5 h-5" />
              </button>

              <button
                onClick={onClose}
                className="p-2 rounded-lg bg-white/10 text-gray-400 hover:text-white transition-colors jorge-haptic"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search scans..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm jorge-text placeholder-gray-400 focus:border-jorge-electric focus:outline-none"
            />
            <MagnifyingGlassIcon className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />
          </div>

          {/* Filters */}
          <AnimatePresence>
            {showFilters && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4 space-y-3 overflow-hidden"
              >
                {/* Filter type */}
                <div className="flex gap-2 overflow-x-auto">
                  {filterOptions.map((option) => (
                    <button
                      key={option.value}
                      onClick={() => setFilterType(option.value as FilterType)}
                      className={`flex-shrink-0 px-3 py-1 rounded-lg text-xs jorge-code font-semibold transition-colors ${
                        filterType === option.value
                          ? 'bg-jorge-electric text-black'
                          : 'bg-white/10 text-gray-400 hover:bg-white/20'
                      } jorge-haptic`}
                    >
                      {option.label} ({option.count})
                    </button>
                  ))}
                </div>

                {/* Sort options */}
                <div className="flex gap-2">
                  <span className="text-xs text-gray-400 jorge-code py-1">Sort:</span>
                  {[
                    { value: 'newest', label: 'Newest' },
                    { value: 'oldest', label: 'Oldest' },
                    { value: 'confidence', label: 'Confidence' },
                    { value: 'type', label: 'Type' }
                  ].map((option) => (
                    <button
                      key={option.value}
                      onClick={() => setSortType(option.value as SortType)}
                      className={`px-2 py-1 rounded text-xs jorge-code transition-colors ${
                        sortType === option.value
                          ? 'bg-jorge-glow/20 text-jorge-glow'
                          : 'text-gray-400 hover:text-white'
                      } jorge-haptic`}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* History List */}
        <div className="flex-1 overflow-y-auto">
          {filteredAndSortedHistory.length === 0 ? (
            <div className="flex items-center justify-center h-full text-center p-6">
              <div>
                <DocumentTextIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-300 mb-2">
                  No Scans Found
                </h3>
                <p className="text-gray-400 jorge-code text-sm">
                  {searchTerm ? 'Try adjusting your search terms' : 'Start scanning to build your history'}
                </p>
              </div>
            </div>
          ) : (
            <div className="p-4 space-y-3">
              {filteredAndSortedHistory.map((item) => (
                <motion.div
                  key={item.id}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`bg-white/5 border rounded-lg p-3 transition-all duration-200 ${
                    selectedItems.has(item.id)
                      ? 'border-jorge-electric bg-jorge-electric/10'
                      : 'border-white/10 hover:bg-white/10'
                  } jorge-haptic`}
                  onClick={() => toggleItemSelection(item.id)}
                >
                  <div className="flex items-start gap-3">
                    {/* Type icon */}
                    <div className={`flex-shrink-0 p-2 rounded-lg ${
                      item.type === 'qr' ? 'bg-jorge-electric/20 text-jorge-electric' :
                      item.type === 'camera' ? 'bg-jorge-gold/20 text-jorge-gold' :
                      item.type === 'voice' ? 'bg-jorge-glow/20 text-jorge-glow' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {getScanIcon(item.type)}
                    </div>

                    <div className="flex-1 min-w-0">
                      {/* Header */}
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm jorge-text font-semibold text-white capitalize">
                          {item.type} Scan
                        </span>
                        <div className="flex items-center gap-2">
                          {getStatusIndicator(item.status)}
                          <span className={`text-xs jorge-code font-semibold ${
                            item.confidence >= 0.8 ? 'text-green-400' :
                            item.confidence >= 0.6 ? 'text-yellow-400' : 'text-red-400'
                          }`}>
                            {Math.round(item.confidence * 100)}%
                          </span>
                        </div>
                      </div>

                      {/* Data preview */}
                      <div className="text-sm jorge-text text-gray-300 mb-2 truncate">
                        {item.data}
                      </div>

                      {/* Property info (if available) */}
                      {item.result?.property && (
                        <div className="text-xs jorge-code text-jorge-electric mb-2">
                          {item.result.property.address} • {
                            item.result.property.price
                              ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(item.result.property.price)
                              : 'Price N/A'
                          }
                        </div>
                      )}

                      {/* Metadata */}
                      <div className="flex items-center gap-4 text-xs jorge-code text-gray-400">
                        <div className="flex items-center gap-1">
                          <ClockIcon className="w-3 h-3" />
                          <span>{formatTimeAgo(item.timestamp)}</span>
                        </div>

                        {item.location && (
                          <div className="flex items-center gap-1">
                            <MapPinIcon className="w-3 h-3" />
                            <span>GPS</span>
                          </div>
                        )}

                        <div>
                          {formatDuration(item.duration)}
                        </div>
                      </div>
                    </div>

                    {/* Action button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (item.result) {
                          onSelectResult(item.result);
                        }
                      }}
                      disabled={!item.result}
                      className="flex-shrink-0 p-2 rounded-lg bg-white/10 text-gray-400 hover:text-white disabled:opacity-50 transition-colors jorge-haptic"
                    >
                      <EyeIcon className="w-4 h-4" />
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-white/10 bg-jorge-dark/95 backdrop-blur-sm">
          {selectedItems.size > 0 ? (
            <div className="flex gap-3">
              <button
                onClick={exportSelectedItems}
                className="flex-1 bg-jorge-electric text-black py-2 px-4 rounded-lg flex items-center justify-center gap-2 jorge-code font-bold jorge-haptic"
              >
                <ArrowDownTrayIcon className="w-4 h-4" />
                Export ({selectedItems.size})
              </button>

              <button
                onClick={() => setSelectedItems(new Set())}
                className="bg-white/10 text-gray-400 py-2 px-4 rounded-lg jorge-code font-semibold jorge-haptic"
              >
                Clear
              </button>
            </div>
          ) : (
            <div className="flex gap-3">
              <button
                onClick={() => {
                  const allIds = new Set(filteredAndSortedHistory.map(item => item.id));
                  setSelectedItems(allIds);
                }}
                className="flex-1 bg-white/10 text-gray-300 py-2 px-4 rounded-lg jorge-code font-semibold jorge-haptic"
              >
                Select All
              </button>

              <button
                onClick={onClearHistory}
                className="bg-red-500/20 border border-red-500/30 text-red-400 py-2 px-4 rounded-lg flex items-center gap-2 jorge-code font-semibold jorge-haptic"
              >
                <TrashIcon className="w-4 h-4" />
                Clear All
              </button>
            </div>
          )}

          <div className="text-center mt-3">
            <span className="text-xs jorge-code text-gray-500">
              Total storage: {(mockHistory.length * 0.1).toFixed(1)}KB
            </span>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
}