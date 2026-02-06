/**
 * Jorge Real Estate AI Platform - Enhanced Offline Storage Indicator
 * Professional status indicator with storage analytics and sync progress
 *
 * Features:
 * - Real-time sync status monitoring
 * - Storage usage visualization
 * - Pending operations breakdown
 * - Jorge-branded error handling
 * - Interactive storage management
 */

'use client';

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  WifiIcon,
  CloudIcon,
  ExclamationTriangleIcon,
  CircleStackIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
  ChartBarIcon
} from "@heroicons/react/24/outline";
import { useOfflineStorage } from "@/hooks/useOfflineStorage";

interface StorageBreakdown {
  properties: number;
  conversations: number;
  voiceNotes: number;
  operations: number;
}

export function OfflineStorageIndicator() {
  const {
    status,
    isOnline,
    syncStatus,
    pendingOperations,
    getStorageStats,
    formatBytes,
    getStoragePercentage,
    retryFailedOperations
  } = useOfflineStorage();

  const [showDetails, setShowDetails] = useState(false);
  const [storageBreakdown, setStorageBreakdown] = useState<StorageBreakdown>({
    properties: 0,
    conversations: 0,
    voiceNotes: 0,
    operations: 0
  });

  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);

  useEffect(() => {
    const updateStorageDetails = async () => {
      try {
        const stats = await getStorageStats();
        setStorageBreakdown(stats.breakdown as StorageBreakdown);
      } catch (error) {
        console.error('Failed to get storage breakdown:', error);
      }
    };

    updateStorageDetails();
    const interval = setInterval(updateStorageDetails, 10000); // Update every 10 seconds

    return () => clearInterval(interval);
  }, [getStorageStats]);

  useEffect(() => {
    if (syncStatus === 'idle' && pendingOperations === 0) {
      setLastSyncTime(new Date());
    }
  }, [syncStatus, pendingOperations]);

  const getNetworkStatusConfig = () => {
    if (!isOnline) {
      return {
        icon: ExclamationTriangleIcon,
        text: 'OFFLINE',
        color: 'text-red-400',
        bgColor: 'bg-red-500/20',
        borderColor: 'border-red-500/30',
        description: 'No internet connection'
      };
    }

    switch (syncStatus) {
      case 'syncing':
        return {
          icon: ArrowPathIcon,
          text: 'SYNCING',
          color: 'text-jorge-electric',
          bgColor: 'bg-jorge-electric/20',
          borderColor: 'border-jorge-electric/30',
          description: `Syncing ${pendingOperations} operations`
        };
      case 'error':
        return {
          icon: XCircleIcon,
          text: 'SYNC ERROR',
          color: 'text-red-400',
          bgColor: 'bg-red-500/20',
          borderColor: 'border-red-500/30',
          description: 'Sync failed, will retry'
        };
      case 'paused':
        return {
          icon: CloudIcon,
          text: 'PAUSED',
          color: 'text-yellow-400',
          bgColor: 'bg-yellow-500/20',
          borderColor: 'border-yellow-500/30',
          description: 'Sync paused'
        };
      default:
        return {
          icon: CheckCircleIcon,
          text: 'SYNCED',
          color: 'text-jorge-glow',
          bgColor: 'bg-jorge-glow/20',
          borderColor: 'border-jorge-glow/30',
          description: 'All data synchronized'
        };
    }
  };

  const formatTimeAgo = (date: Date | null) => {
    if (!date) return 'Never';
    const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  const storagePercentage = getStoragePercentage();
  const networkConfig = getNetworkStatusConfig();
  const NetworkIcon = networkConfig.icon;

  return (
    <div className="relative">
      {/* Main Indicator */}
      <motion.div
        layout
        className={`
          flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer
          ${networkConfig.bgColor} ${networkConfig.borderColor}
          backdrop-blur-sm transition-all duration-200
          hover:bg-opacity-30
        `}
        onClick={() => setShowDetails(!showDetails)}
      >
        {/* Network Status Icon */}
        <NetworkIcon
          className={`w-4 h-4 ${networkConfig.color} ${
            syncStatus === 'syncing' ? 'animate-spin' : ''
          }`}
        />

        {/* Status Text */}
        <span className={`text-xs jorge-code ${networkConfig.color} font-medium`}>
          {networkConfig.text}
        </span>

        {/* Pending Operations Badge */}
        {pendingOperations > 0 && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="bg-jorge-electric text-black text-xs px-1.5 py-0.5 rounded-full jorge-code font-bold"
          >
            {pendingOperations}
          </motion.div>
        )}

        {/* Storage Usage Bar */}
        <div className="hidden sm:flex items-center gap-1">
          <CircleStackIcon className="w-3 h-3 text-gray-400" />
          <div className="w-16 h-1.5 bg-black/30 rounded-full overflow-hidden">
            <motion.div
              className={`h-full rounded-full ${
                storagePercentage > 80 ? 'bg-red-400' :
                storagePercentage > 60 ? 'bg-yellow-400' :
                'bg-jorge-glow'
              }`}
              initial={{ width: 0 }}
              animate={{ width: `${Math.min(storagePercentage, 100)}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <span className="text-xs text-gray-400 jorge-code">
            {Math.round(storagePercentage)}%
          </span>
        </div>
      </motion.div>

      {/* Detailed Panel */}
      <AnimatePresence>
        {showDetails && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute top-full mt-2 right-0 z-50 w-80 bg-black/90 border border-white/10 rounded-xl p-4 backdrop-blur-lg"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-bold jorge-text text-jorge-glow">
                🏢 Jorge Storage Status
              </h3>
              <button
                onClick={() => setShowDetails(false)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Network Status */}
            <div className={`p-3 rounded-lg mb-4 ${networkConfig.bgColor} border ${networkConfig.borderColor}`}>
              <div className="flex items-center gap-2 mb-1">
                <NetworkIcon className={`w-4 h-4 ${networkConfig.color}`} />
                <span className={`text-sm jorge-text ${networkConfig.color} font-medium`}>
                  {networkConfig.text}
                </span>
              </div>
              <p className="text-xs text-gray-300 jorge-text">
                {networkConfig.description}
              </p>
              {lastSyncTime && (
                <p className="text-xs text-gray-400 jorge-code mt-1">
                  Last sync: {formatTimeAgo(lastSyncTime)}
                </p>
              )}
            </div>

            {/* Storage Breakdown */}
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-2">
                <ChartBarIcon className="w-4 h-4 text-jorge-glow" />
                <span className="text-sm jorge-text text-jorge-glow font-medium">Storage Usage</span>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-xs jorge-code">
                  <span className="text-gray-300">Used:</span>
                  <span className="text-white">{formatBytes(status.storageUsed)}</span>
                </div>
                <div className="flex justify-between text-xs jorge-code">
                  <span className="text-gray-300">Quota:</span>
                  <span className="text-white">{formatBytes(status.storageQuota)}</span>
                </div>

                {/* Storage Bar */}
                <div className="w-full h-2 bg-black/50 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full ${
                      storagePercentage > 80 ? 'bg-gradient-to-r from-red-500 to-red-400' :
                      storagePercentage > 60 ? 'bg-gradient-to-r from-yellow-500 to-yellow-400' :
                      'bg-gradient-to-r from-jorge-glow to-jorge-electric'
                    }`}
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(storagePercentage, 100)}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>

                {/* Data Breakdown */}
                <div className="grid grid-cols-2 gap-2 mt-3">
                  {Object.entries(storageBreakdown).map(([key, size]) => (
                    <div key={key} className="bg-white/5 rounded p-2">
                      <div className="text-xs text-gray-400 jorge-code capitalize">
                        {key === 'voiceNotes' ? 'Voice Notes' : key}
                      </div>
                      <div className="text-xs text-white jorge-code font-medium">
                        {formatBytes(size)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              {syncStatus === 'error' && (
                <button
                  onClick={retryFailedOperations}
                  className="flex-1 bg-jorge-electric text-black text-xs jorge-code font-bold py-2 px-3 rounded-lg hover:bg-jorge-electric/80 transition-colors"
                >
                  Retry Sync
                </button>
              )}

              {pendingOperations > 0 && (
                <div className="flex-1 bg-yellow-500/20 border border-yellow-500/30 text-yellow-400 text-xs jorge-code font-medium py-2 px-3 rounded-lg text-center">
                  {pendingOperations} Pending
                </div>
              )}

              {syncStatus === 'idle' && pendingOperations === 0 && (
                <div className="flex-1 bg-jorge-glow/20 border border-jorge-glow/30 text-jorge-glow text-xs jorge-code font-medium py-2 px-3 rounded-lg text-center">
                  ✓ All Synced
                </div>
              )}
            </div>

            {/* Storage Warning */}
            {storagePercentage > 80 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-3 p-2 bg-red-500/20 border border-red-500/30 rounded-lg"
              >
                <div className="flex items-center gap-2">
                  <ExclamationTriangleIcon className="w-4 h-4 text-red-400" />
                  <span className="text-xs text-red-400 jorge-text font-medium">
                    Storage Nearly Full
                  </span>
                </div>
                <p className="text-xs text-red-300 jorge-text mt-1">
                  Consider clearing old data to ensure optimal performance.
                </p>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}