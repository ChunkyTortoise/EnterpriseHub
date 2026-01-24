'use client';

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  WifiIcon,
  CloudIcon,
  ExclamationTriangleIcon
} from "@heroicons/react/24/outline";

// Re-export the enhanced version
export { OfflineStorageIndicator as OfflineIndicator } from './OfflineStorageIndicator';

type NetworkStatus = 'online' | 'offline' | 'slow' | 'unknown';

interface NetworkInfo {
  status: NetworkStatus;
  effectiveType?: string;
  downlink?: number;
  rtt?: number;
}

export function OfflineIndicator() {
  const [networkInfo, setNetworkInfo] = useState<NetworkInfo>({
    status: 'unknown'
  });

  const [syncStatus, setSyncStatus] = useState<'synced' | 'syncing' | 'pending' | 'failed'>('synced');

  useEffect(() => {
    // Check initial network status
    const updateNetworkStatus = () => {
      const isOnline = navigator.onLine;
      let status: NetworkStatus = isOnline ? 'online' : 'offline';

      // Get connection info if available
      const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;

      if (connection && isOnline) {
        const effectiveType = connection.effectiveType;
        const downlink = connection.downlink;
        const rtt = connection.rtt;

        // Determine if connection is slow
        if (effectiveType === 'slow-2g' || effectiveType === '2g' || downlink < 1.5 || rtt > 300) {
          status = 'slow';
        }

        setNetworkInfo({
          status,
          effectiveType,
          downlink,
          rtt
        });
      } else {
        setNetworkInfo({ status });
      }
    };

    // Listen for network changes
    window.addEventListener('online', updateNetworkStatus);
    window.addEventListener('offline', updateNetworkStatus);

    // Listen for connection changes (if supported)
    const connection = (navigator as any).connection;
    if (connection) {
      connection.addEventListener('change', updateNetworkStatus);
    }

    // Initial check
    updateNetworkStatus();

    // Simulate sync status changes (in real app, this would connect to service worker)
    const syncInterval = setInterval(() => {
      if (networkInfo.status === 'offline') {
        setSyncStatus('pending');
      } else if (networkInfo.status === 'slow') {
        setSyncStatus('syncing');
      } else {
        setSyncStatus('synced');
      }
    }, 2000);

    return () => {
      window.removeEventListener('online', updateNetworkStatus);
      window.removeEventListener('offline', updateNetworkStatus);
      if (connection) {
        connection.removeEventListener('change', updateNetworkStatus);
      }
      clearInterval(syncInterval);
    };
  }, [networkInfo.status]);

  const getStatusConfig = () => {
    switch (networkInfo.status) {
      case 'offline':
        return {
          icon: ExclamationTriangleIcon,
          text: 'OFFLINE',
          color: 'text-red-400',
          bgColor: 'bg-red-500/20',
          borderColor: 'border-red-500/30'
        };
      case 'slow':
        return {
          icon: CloudIcon,
          text: 'SLOW',
          color: 'text-yellow-400',
          bgColor: 'bg-yellow-500/20',
          borderColor: 'border-yellow-500/30'
        };
      case 'online':
        return {
          icon: WifiIcon,
          text: 'ONLINE',
          color: 'text-jorge-glow',
          bgColor: 'bg-jorge-glow/20',
          borderColor: 'border-jorge-glow/30'
        };
      default:
        return {
          icon: CloudIcon,
          text: 'CHECKING',
          color: 'text-gray-400',
          bgColor: 'bg-gray-500/20',
          borderColor: 'border-gray-500/30'
        };
    }
  };

  const getSyncStatusConfig = () => {
    switch (syncStatus) {
      case 'syncing':
        return {
          text: 'SYNCING',
          color: 'text-jorge-electric',
          animate: true
        };
      case 'pending':
        return {
          text: 'PENDING',
          color: 'text-yellow-400',
          animate: false
        };
      case 'failed':
        return {
          text: 'FAILED',
          color: 'text-red-400',
          animate: false
        };
      default:
        return {
          text: 'SYNCED',
          color: 'text-jorge-glow',
          animate: false
        };
    }
  };

  const statusConfig = getStatusConfig();
  const syncConfig = getSyncStatusConfig();
  const StatusIcon = statusConfig.icon;

  return (
    <div className="flex items-center gap-2">
      {/* Network Status */}
      <motion.div
        layout
        className={`
          flex items-center gap-1 px-2 py-1 rounded-lg border
          ${statusConfig.bgColor} ${statusConfig.borderColor}
          backdrop-blur-sm
        `}
      >
        <StatusIcon className={`w-3 h-3 ${statusConfig.color}`} />
        <span className={`text-xs jorge-code ${statusConfig.color}`}>
          {statusConfig.text}
        </span>
      </motion.div>

      {/* Sync Status */}
      <AnimatePresence>
        {syncStatus !== 'synced' && (
          <motion.div
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            className={`
              flex items-center gap-1 px-2 py-1 rounded-lg
              bg-black/20 border border-white/10
              backdrop-blur-sm
            `}
          >
            {syncConfig.animate && (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                className="w-2 h-2 border border-jorge-electric border-t-transparent rounded-full"
              />
            )}
            <span className={`text-xs jorge-code ${syncConfig.color}`}>
              {syncConfig.text}
            </span>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Network Details (Debug - only show in dev) */}
      {process.env.NODE_ENV === 'development' && networkInfo.effectiveType && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="hidden sm:block text-xs jorge-code text-gray-500"
        >
          {networkInfo.effectiveType} | {networkInfo.downlink?.toFixed(1)}Mbps | {networkInfo.rtt}ms
        </motion.div>
      )}
    </div>
  );
}