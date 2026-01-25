// Jorge's Real Estate AI Platform - Connection Status Component
// Real-time network status with offline capabilities indicator

'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Wifi, WifiOff, Signal, SignalLow, SignalMedium, SignalHigh, CloudOff, Sync } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useNetwork } from '@/hooks/useNetwork'

interface ConnectionStatusProps {
  className?: string
  showDetails?: boolean
  autoHide?: boolean
  autoHideDelay?: number
}

interface StatusState {
  isVisible: boolean
  lastStatusChange: number
  showFullStatus: boolean
}

export function ConnectionStatus({
  className,
  showDetails = false,
  autoHide = true,
  autoHideDelay = 3000
}: ConnectionStatusProps) {
  const {
    isOnline,
    isSlowConnection,
    connectionQuality,
    effectiveType,
    rtt,
    downlink,
    shouldCacheAggressively,
    canHandlePropertyPhotos
  } = useNetwork()

  const [state, setState] = useState<StatusState>({
    isVisible: true,
    lastStatusChange: Date.now(),
    showFullStatus: false
  })

  // Track connection status changes
  useEffect(() => {
    setState(prev => ({
      ...prev,
      lastStatusChange: Date.now(),
      isVisible: true
    }))

    if (autoHide && isOnline) {
      const timer = setTimeout(() => {
        setState(prev => ({ ...prev, isVisible: false }))
      }, autoHideDelay)

      return () => clearTimeout(timer)
    }
  }, [isOnline, connectionQuality.quality, autoHide, autoHideDelay])

  const getQualityIcon = () => {
    if (!isOnline) {
      return <WifiOff className="w-4 h-4" />
    }

    switch (connectionQuality.quality) {
      case 'excellent':
        return <SignalHigh className="w-4 h-4" />
      case 'good':
        return <SignalMedium className="w-4 h-4" />
      case 'poor':
        return <SignalLow className="w-4 h-4" />
      default:
        return <Signal className="w-4 h-4" />
    }
  }

  const getQualityColor = () => {
    if (!isOnline) {
      return 'text-red-400 bg-red-500/20 border-red-500/30'
    }

    switch (connectionQuality.quality) {
      case 'excellent':
        return 'text-green-400 bg-green-500/20 border-green-500/30'
      case 'good':
        return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30'
      case 'poor':
        return 'text-orange-400 bg-orange-500/20 border-orange-500/30'
      default:
        return 'text-gray-400 bg-gray-500/20 border-gray-500/30'
    }
  }

  const getStatusMessage = () => {
    if (!isOnline) {
      return 'Offline Mode - Limited functionality'
    }

    if (isSlowConnection) {
      return 'Slow connection - Optimizing for performance'
    }

    switch (connectionQuality.quality) {
      case 'excellent':
        return 'Excellent connection - All features available'
      case 'good':
        return 'Good connection - Full functionality'
      case 'poor':
        return 'Poor connection - Some features limited'
      default:
        return 'Connected'
    }
  }

  const getCapabilities = () => {
    const capabilities = []

    if (!isOnline) {
      capabilities.push('📱 Basic functions only')
      capabilities.push('💾 Cached data available')
      capabilities.push('🔄 Sync when reconnected')
    } else {
      if (canHandlePropertyPhotos) {
        capabilities.push('📸 Property photo analysis')
      }
      if (connectionQuality.canStreamVideo) {
        capabilities.push('🎥 Video content')
      }
      if (!connectionQuality.shouldReduceData) {
        capabilities.push('🚀 Full AI features')
      } else {
        capabilities.push('⚡ Power saver mode')
      }
      if (shouldCacheAggressively) {
        capabilities.push('💾 Aggressive caching')
      }
    }

    return capabilities
  }

  // Don't render if set to auto-hide and not visible
  if (autoHide && !state.isVisible && isOnline && connectionQuality.quality === 'excellent') {
    return null
  }

  return (
    <AnimatePresence>
      {(state.isVisible || !isOnline || connectionQuality.quality !== 'excellent') && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className={cn(
            'backdrop-blur-sm border-b transition-all duration-300',
            getQualityColor(),
            className
          )}
          onClick={() => setState(prev => ({ ...prev, showFullStatus: !prev.showFullStatus }))}
        >
          <div className="px-4 py-2">
            {/* Basic Status Bar */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {getQualityIcon()}
                <span className="text-sm font-medium">
                  {isOnline ? connectionQuality.quality.charAt(0).toUpperCase() + connectionQuality.quality.slice(1) : 'Offline'}
                </span>

                {/* Connection Type Badge */}
                {isOnline && (
                  <span className="text-xs px-2 py-1 rounded bg-white/10 backdrop-blur-sm">
                    {effectiveType?.toUpperCase() || 'Unknown'}
                  </span>
                )}

                {/* Sync Status */}
                {shouldCacheAggressively && (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    className="text-xs"
                  >
                    <Sync className="w-3 h-3" />
                  </motion.div>
                )}
              </div>

              {/* Quick Indicators */}
              <div className="flex items-center gap-1 text-xs">
                {!canHandlePropertyPhotos && (
                  <span className="px-2 py-1 rounded bg-white/10">No Photos</span>
                )}
                {connectionQuality.shouldReduceData && (
                  <span className="px-2 py-1 rounded bg-white/10">Data Saver</span>
                )}
              </div>
            </div>

            {/* Detailed Status */}
            <AnimatePresence>
              {(state.showFullStatus || showDetails) && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                  className="mt-3 pt-3 border-t border-white/20"
                >
                  {/* Status Message */}
                  <div className="text-sm mb-3 opacity-90">
                    {getStatusMessage()}
                  </div>

                  {/* Connection Metrics */}
                  {isOnline && (
                    <div className="grid grid-cols-3 gap-4 mb-3 text-xs">
                      <div className="text-center">
                        <div className="font-medium">Latency</div>
                        <div className="opacity-75">{rtt}ms</div>
                      </div>
                      <div className="text-center">
                        <div className="font-medium">Speed</div>
                        <div className="opacity-75">{downlink.toFixed(1)} Mbps</div>
                      </div>
                      <div className="text-center">
                        <div className="font-medium">Type</div>
                        <div className="opacity-75">{effectiveType}</div>
                      </div>
                    </div>
                  )}

                  {/* Capabilities List */}
                  <div className="space-y-1">
                    <div className="text-xs font-medium opacity-75">Available Features:</div>
                    {getCapabilities().map((capability, index) => (
                      <motion.div
                        key={capability}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="text-xs opacity-75"
                      >
                        {capability}
                      </motion.div>
                    ))}
                  </div>

                  {/* Offline Mode Instructions */}
                  {!isOnline && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-3 p-2 bg-white/10 rounded text-xs"
                    >
                      <div className="font-medium mb-1">Offline Mode Active</div>
                      <div className="opacity-75">
                        • Cached properties and leads available<br/>
                        • Voice notes saved locally<br/>
                        • Data will sync when reconnected
                      </div>
                    </motion.div>
                  )}

                  {/* Poor Connection Tips */}
                  {isOnline && connectionQuality.quality === 'poor' && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="mt-3 p-2 bg-white/10 rounded text-xs"
                    >
                      <div className="font-medium mb-1">Connection Tips</div>
                      <div className="opacity-75">
                        • Move to better signal area<br/>
                        • Some features may be slower<br/>
                        • Large images won't load automatically
                      </div>
                    </motion.div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Click Indicator */}
          {!showDetails && (
            <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-white/20 rounded-full" />
          )}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// Companion component for connection quality indicator in other parts of the app
interface ConnectionQualityIndicatorProps {
  className?: string
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
}

export function ConnectionQualityIndicator({
  className,
  size = 'sm',
  showLabel = false
}: ConnectionQualityIndicatorProps) {
  const { isOnline, connectionQuality } = useNetwork()

  const sizeClasses = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5'
  }

  const getIndicatorColor = () => {
    if (!isOnline) return 'text-red-400'

    switch (connectionQuality.quality) {
      case 'excellent': return 'text-green-400'
      case 'good': return 'text-yellow-400'
      case 'poor': return 'text-orange-400'
      default: return 'text-gray-400'
    }
  }

  return (
    <div className={cn('flex items-center gap-1', className)}>
      <motion.div
        animate={isOnline ? {} : { opacity: [1, 0.5, 1] }}
        transition={isOnline ? {} : { duration: 2, repeat: Infinity }}
        className={cn(getIndicatorColor())}
      >
        {isOnline ? (
          <Wifi className={sizeClasses[size]} />
        ) : (
          <WifiOff className={sizeClasses[size]} />
        )}
      </motion.div>

      {showLabel && (
        <span className={cn(
          'text-xs font-medium',
          getIndicatorColor()
        )}>
          {isOnline ? connectionQuality.quality : 'offline'}
        </span>
      )}
    </div>
  )
}