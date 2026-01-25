/**
 * Jorge Real Estate AI Platform - Auto-Save Status Indicator
 * Visual feedback component for field agents to see save status
 *
 * Features:
 * - Real-time save status with animations
 * - Connection quality indication
 * - Manual save/sync controls
 * - Error state handling with retry options
 */

'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CloudIcon,
  CloudArrowUpIcon,
  ExclamationCircleIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  WifiIcon,
  SignalIcon,
  BoltIcon
} from '@heroicons/react/24/outline';
import { AutoSaveStatus } from '@/hooks/useAutoSave';

interface AutoSaveIndicatorProps {
  status: AutoSaveStatus;
  lastSaved?: number | null;
  lastSynced?: number | null;
  error?: string | null;
  saveCount?: number;
  isOnline?: boolean;
  connectionQuality?: 'excellent' | 'good' | 'poor' | 'offline';

  // Actions
  onManualSave?: () => void;
  onManualSync?: () => void;
  onRetry?: () => void;

  // Appearance
  size?: 'sm' | 'md' | 'lg';
  position?: 'top-right' | 'bottom-right' | 'inline';
  showDetails?: boolean;
}

export function AutoSaveIndicator({
  status,
  lastSaved,
  lastSynced,
  error,
  saveCount = 0,
  isOnline = true,
  connectionQuality = 'good',
  onManualSave,
  onManualSync,
  onRetry,
  size = 'md',
  position = 'top-right',
  showDetails = false
}: AutoSaveIndicatorProps) {

  // Status configuration
  const getStatusConfig = () => {
    switch (status) {
      case 'saving':
        return {
          icon: ArrowPathIcon,
          color: 'text-jorge-electric',
          bgColor: 'bg-jorge-electric/10',
          message: 'Saving...',
          animate: true
        };
      case 'saved':
        return {
          icon: CheckCircleIcon,
          color: 'text-jorge-glow',
          bgColor: 'bg-jorge-glow/10',
          message: 'Auto-saved',
          animate: false
        };
      case 'synced':
        return {
          icon: CloudArrowUpIcon,
          color: 'text-green-400',
          bgColor: 'bg-green-400/10',
          message: 'Synced to cloud',
          animate: false
        };
      case 'error':
        return {
          icon: ExclamationCircleIcon,
          color: 'text-red-400',
          bgColor: 'bg-red-400/10',
          message: error || 'Save failed',
          animate: true
        };
      case 'conflict':
        return {
          icon: ExclamationCircleIcon,
          color: 'text-orange-400',
          bgColor: 'bg-orange-400/10',
          message: 'Conflict detected',
          animate: true
        };
      default:
        return {
          icon: CloudIcon,
          color: 'text-gray-400',
          bgColor: 'bg-gray-400/10',
          message: 'Ready',
          animate: false
        };
    }
  };

  // Connection status
  const getConnectionIcon = () => {
    if (!isOnline) return <WifiIcon className="w-4 h-4 text-red-400" />;

    switch (connectionQuality) {
      case 'excellent':
        return <SignalIcon className="w-4 h-4 text-green-400" />;
      case 'good':
        return <SignalIcon className="w-4 h-4 text-jorge-electric" />;
      case 'poor':
        return <SignalIcon className="w-4 h-4 text-orange-400" />;
      default:
        return <WifiIcon className="w-4 h-4 text-gray-400" />;
    }
  };

  // Format relative time
  const formatTimeAgo = (timestamp: number | null) => {
    if (!timestamp) return 'Never';

    const now = Date.now();
    const diff = now - timestamp;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (seconds < 60) return `${seconds}s ago`;
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return new Date(timestamp).toLocaleDateString();
  };

  const statusConfig = getStatusConfig();
  const StatusIcon = statusConfig.icon;

  // Size variants
  const sizeClasses = {
    sm: 'p-2 text-xs',
    md: 'p-3 text-sm',
    lg: 'p-4 text-base'
  };

  // Position variants
  const positionClasses = {
    'top-right': 'fixed top-4 right-4 z-50',
    'bottom-right': 'fixed bottom-4 right-4 z-50',
    'inline': 'relative'
  };

  if (!showDetails && position !== 'inline') {
    // Compact floating indicator
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className={`${positionClasses[position]} ${sizeClasses[size]}`}
      >
        <motion.div
          className={`flex items-center gap-2 ${statusConfig.bgColor} ${statusConfig.color} rounded-lg border border-current/20 backdrop-blur-sm`}
          animate={statusConfig.animate ? { scale: [1, 1.1, 1] } : {}}
          transition={statusConfig.animate ? { repeat: Infinity, duration: 2 } : {}}
        >
          <StatusIcon
            className={`w-4 h-4 ${statusConfig.animate ? 'animate-spin' : ''}`}
          />
          {size !== 'sm' && (
            <span className="font-medium">{statusConfig.message}</span>
          )}
          {isOnline && size === 'lg' && getConnectionIcon()}
        </motion.div>
      </motion.div>
    );
  }

  // Detailed indicator with controls
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`${position !== 'inline' ? positionClasses[position] : ''} max-w-sm`}
    >
      <div className="bg-jorge-dark/95 backdrop-blur border border-white/10 rounded-xl p-4 space-y-3">
        {/* Status Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={`p-2 ${statusConfig.bgColor} rounded-lg`}>
              <StatusIcon
                className={`w-5 h-5 ${statusConfig.color} ${statusConfig.animate ? 'animate-spin' : ''}`}
              />
            </div>
            <div>
              <div className="font-semibold text-white jorge-heading">
                {statusConfig.message}
              </div>
              {saveCount > 0 && (
                <div className="text-xs text-gray-400 jorge-code">
                  {saveCount} auto-saves
                </div>
              )}
            </div>
          </div>

          {/* Connection Status */}
          <div className="flex items-center gap-2">
            {getConnectionIcon()}
            <span className="text-xs text-gray-400 jorge-code">
              {isOnline ? connectionQuality : 'offline'}
            </span>
          </div>
        </div>

        {/* Timestamps */}
        <div className="grid grid-cols-2 gap-3 text-xs text-gray-400 jorge-code">
          <div>
            <div className="text-gray-500">Last Saved</div>
            <div>{formatTimeAgo(lastSaved)}</div>
          </div>
          <div>
            <div className="text-gray-500">Last Synced</div>
            <div>{formatTimeAgo(lastSynced)}</div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="bg-red-500/10 border border-red-500/20 rounded-lg p-3"
          >
            <div className="text-red-300 text-xs jorge-code">{error}</div>
          </motion.div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-2">
          {onManualSave && (
            <button
              onClick={onManualSave}
              className="flex-1 bg-jorge-electric/20 text-jorge-electric hover:bg-jorge-electric/30 px-3 py-2 rounded-lg text-xs font-semibold transition-colors jorge-haptic"
            >
              Save Now
            </button>
          )}

          {onManualSync && isOnline && (
            <button
              onClick={onManualSync}
              className="flex-1 bg-jorge-glow/20 text-jorge-glow hover:bg-jorge-glow/30 px-3 py-2 rounded-lg text-xs font-semibold transition-colors jorge-haptic"
            >
              Sync
            </button>
          )}

          {error && onRetry && (
            <button
              onClick={onRetry}
              className="flex-1 bg-red-400/20 text-red-300 hover:bg-red-400/30 px-3 py-2 rounded-lg text-xs font-semibold transition-colors jorge-haptic"
            >
              Retry
            </button>
          )}
        </div>

        {/* Help Text */}
        {status === 'saved' && !lastSynced && (
          <div className="text-xs text-gray-500 jorge-code">
            Data saved locally. Will sync when online.
          </div>
        )}
      </div>
    </motion.div>
  );
}

/**
 * Compact save indicator for form fields
 */
interface FieldSaveIndicatorProps {
  status: AutoSaveStatus;
  className?: string;
}

export function FieldSaveIndicator({ status, className = '' }: FieldSaveIndicatorProps) {
  const statusConfig = getStatusConfig();
  const StatusIcon = statusConfig.icon;

  function getStatusConfig() {
    switch (status) {
      case 'saving':
        return { icon: ArrowPathIcon, color: 'text-jorge-electric animate-spin' };
      case 'saved':
        return { icon: CheckCircleIcon, color: 'text-jorge-glow' };
      case 'synced':
        return { icon: CloudArrowUpIcon, color: 'text-green-400' };
      case 'error':
        return { icon: ExclamationCircleIcon, color: 'text-red-400' };
      default:
        return { icon: CloudIcon, color: 'text-gray-400' };
    }
  }

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={status}
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.8 }}
        className={`inline-flex items-center ${className}`}
      >
        <StatusIcon className={`w-4 h-4 ${statusConfig.color}`} />
      </motion.div>
    </AnimatePresence>
  );
}

/**
 * Toast notification for save events
 */
interface AutoSaveToastProps {
  status: AutoSaveStatus;
  message?: string;
  onClose?: () => void;
  autoHide?: number; // ms
}

export function AutoSaveToast({
  status,
  message,
  onClose,
  autoHide = 3000
}: AutoSaveToastProps) {
  React.useEffect(() => {
    if (autoHide && onClose) {
      const timer = setTimeout(onClose, autoHide);
      return () => clearTimeout(timer);
    }
  }, [autoHide, onClose]);

  const statusConfig = getStatusConfig();
  const StatusIcon = statusConfig.icon;

  function getStatusConfig() {
    switch (status) {
      case 'saved':
        return {
          icon: CheckCircleIcon,
          color: 'text-jorge-glow',
          bgColor: 'bg-jorge-glow/10',
          borderColor: 'border-jorge-glow/20'
        };
      case 'error':
        return {
          icon: ExclamationCircleIcon,
          color: 'text-red-400',
          bgColor: 'bg-red-400/10',
          borderColor: 'border-red-400/20'
        };
      default:
        return {
          icon: CloudIcon,
          color: 'text-gray-400',
          bgColor: 'bg-gray-400/10',
          borderColor: 'border-gray-400/20'
        };
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 50, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 50, scale: 0.95 }}
      className={`fixed bottom-20 left-4 right-4 mx-auto max-w-sm ${statusConfig.bgColor} ${statusConfig.borderColor} border backdrop-blur rounded-lg p-4 z-50`}
    >
      <div className="flex items-center gap-3">
        <StatusIcon className={`w-5 h-5 ${statusConfig.color} flex-shrink-0`} />
        <div className="flex-1">
          <div className="text-white font-medium jorge-heading">
            {message || getStatusMessage(status)}
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ×
          </button>
        )}
      </div>
    </motion.div>
  );
}

function getStatusMessage(status: AutoSaveStatus): string {
  switch (status) {
    case 'saved':
      return 'Changes saved locally';
    case 'synced':
      return 'Changes synced to cloud';
    case 'error':
      return 'Save failed - will retry';
    case 'conflict':
      return 'Conflict detected';
    default:
      return 'Ready';
  }
}