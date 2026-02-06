// Jorge's Real Estate AI Platform - Network Detection Hook
// Provides real-time network status with connection quality detection

import { useState, useEffect, useCallback } from 'react'

interface NetworkState {
  isOnline: boolean
  isSlowConnection: boolean
  connectionType: string
  effectiveType: string
  rtt: number
  downlink: number
  saveData: boolean
}

interface ConnectionQuality {
  quality: 'excellent' | 'good' | 'poor' | 'offline'
  canLoadImages: boolean
  canStreamVideo: boolean
  shouldReduceData: boolean
  recommendedCacheStrategy: 'aggressive' | 'normal' | 'minimal'
}

// Extend Navigator interface for Network Information API
interface NavigatorWithConnection extends Navigator {
  connection?: {
    effectiveType: '4g' | '3g' | '2g' | 'slow-2g'
    rtt: number
    downlink: number
    saveData: boolean
    addEventListener: (event: string, handler: () => void) => void
    removeEventListener: (event: string, handler: () => void) => void
  }
}

export function useNetwork() {
  const [networkState, setNetworkState] = useState<NetworkState>({
    isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
    isSlowConnection: false,
    connectionType: 'unknown',
    effectiveType: '4g',
    rtt: 0,
    downlink: 0,
    saveData: false
  })

  const [connectionQuality, setConnectionQuality] = useState<ConnectionQuality>({
    quality: 'excellent',
    canLoadImages: true,
    canStreamVideo: true,
    shouldReduceData: false,
    recommendedCacheStrategy: 'normal'
  })

  const updateNetworkInfo = useCallback(() => {
    const nav = navigator as NavigatorWithConnection
    const connection = nav.connection

    const newState: NetworkState = {
      isOnline: navigator.onLine,
      isSlowConnection: false,
      connectionType: 'unknown',
      effectiveType: connection?.effectiveType || '4g',
      rtt: connection?.rtt || 0,
      downlink: connection?.downlink || 0,
      saveData: connection?.saveData || false
    }

    // Determine if connection is slow
    if (connection) {
      newState.isSlowConnection =
        connection.effectiveType === 'slow-2g' ||
        connection.effectiveType === '2g' ||
        connection.rtt > 1000 ||
        connection.downlink < 0.5

      newState.connectionType = connection.effectiveType
    }

    setNetworkState(newState)

    // Calculate connection quality
    let quality: ConnectionQuality['quality'] = 'excellent'
    let canLoadImages = true
    let canStreamVideo = true
    let shouldReduceData = false
    let recommendedCacheStrategy: ConnectionQuality['recommendedCacheStrategy'] = 'normal'

    if (!navigator.onLine) {
      quality = 'offline'
      canLoadImages = false
      canStreamVideo = false
      shouldReduceData = true
      recommendedCacheStrategy = 'aggressive'
    } else if (connection) {
      const { effectiveType, rtt, downlink, saveData } = connection

      if (effectiveType === 'slow-2g' || rtt > 2000 || downlink < 0.25) {
        quality = 'poor'
        canLoadImages = false
        canStreamVideo = false
        shouldReduceData = true
        recommendedCacheStrategy = 'aggressive'
      } else if (effectiveType === '2g' || rtt > 1000 || downlink < 0.5) {
        quality = 'poor'
        canLoadImages = true
        canStreamVideo = false
        shouldReduceData = true
        recommendedCacheStrategy = 'aggressive'
      } else if (effectiveType === '3g' || rtt > 500 || downlink < 1.0 || saveData) {
        quality = 'good'
        canLoadImages = true
        canStreamVideo = false
        shouldReduceData = saveData
        recommendedCacheStrategy = shouldReduceData ? 'aggressive' : 'normal'
      } else {
        quality = 'excellent'
        canLoadImages = true
        canStreamVideo = true
        shouldReduceData = saveData
        recommendedCacheStrategy = 'normal'
      }
    }

    setConnectionQuality({
      quality,
      canLoadImages,
      canStreamVideo,
      shouldReduceData,
      recommendedCacheStrategy
    })
  }, [])

  useEffect(() => {
    // Initial network info
    updateNetworkInfo()

    // Listen for online/offline events
    const handleOnline = () => {
      console.log('📡 Jorge AI: Connection restored')
      updateNetworkInfo()
    }

    const handleOffline = () => {
      console.log('📡 Jorge AI: Connection lost - switching to offline mode')
      updateNetworkInfo()
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    // Listen for connection quality changes
    const nav = navigator as NavigatorWithConnection
    if (nav.connection) {
      const handleConnectionChange = () => {
        console.log('📡 Jorge AI: Connection quality changed')
        updateNetworkInfo()
      }

      nav.connection.addEventListener('change', handleConnectionChange)

      return () => {
        window.removeEventListener('online', handleOnline)
        window.removeEventListener('offline', handleOffline)
        nav.connection?.removeEventListener('change', handleConnectionChange)
      }
    }

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [updateNetworkInfo])

  const testConnectionSpeed = useCallback(async (): Promise<{
    ping: number
    downloadSpeed: number
    quality: string
  }> => {
    if (!navigator.onLine) {
      return {
        ping: Infinity,
        downloadSpeed: 0,
        quality: 'offline'
      }
    }

    try {
      // Test ping using a small image request
      const startTime = performance.now()

      const response = await fetch('/api/health', {
        method: 'HEAD',
        cache: 'no-cache'
      })

      const ping = performance.now() - startTime

      // Estimate download speed using response timing
      let downloadSpeed = 0
      let quality = 'poor'

      if (ping < 100) {
        downloadSpeed = 10 // Assume high speed for low latency
        quality = 'excellent'
      } else if (ping < 300) {
        downloadSpeed = 5
        quality = 'good'
      } else if (ping < 1000) {
        downloadSpeed = 1
        quality = 'fair'
      }

      console.log(`📡 Jorge AI: Connection test - Ping: ${ping}ms, Quality: ${quality}`)

      return {
        ping,
        downloadSpeed,
        quality
      }
    } catch (error) {
      console.error('📡 Jorge AI: Connection test failed:', error)
      return {
        ping: Infinity,
        downloadSpeed: 0,
        quality: 'offline'
      }
    }
  }, [])

  const optimizeRequestForConnection = useCallback((baseOptions: RequestInit): RequestInit => {
    const optimizedOptions = { ...baseOptions }

    // Apply connection-specific optimizations
    switch (connectionQuality.quality) {
      case 'poor':
        optimizedOptions.headers = {
          ...optimizedOptions.headers,
          'Accept-Encoding': 'gzip, deflate',
          'Cache-Control': 'max-stale=3600' // Accept stale cache for poor connections
        }
        break

      case 'good':
        optimizedOptions.headers = {
          ...optimizedOptions.headers,
          'Accept-Encoding': 'gzip, deflate, br'
        }
        break

      case 'excellent':
        // No restrictions for excellent connections
        break

      case 'offline':
        // Return early - should use cached data
        throw new Error('Offline - use cached data')
    }

    // Reduce payload for data saver mode
    if (networkState.saveData) {
      optimizedOptions.headers = {
        ...optimizedOptions.headers,
        'Save-Data': 'on'
      }
    }

    return optimizedOptions
  }, [connectionQuality.quality, networkState.saveData])

  const shouldLoadResource = useCallback((resourceType: 'image' | 'video' | 'audio' | 'data'): boolean => {
    switch (resourceType) {
      case 'image':
        return connectionQuality.canLoadImages
      case 'video':
        return connectionQuality.canStreamVideo
      case 'audio':
        return connectionQuality.quality !== 'offline' && connectionQuality.quality !== 'poor'
      case 'data':
        return networkState.isOnline
      default:
        return networkState.isOnline
    }
  }, [connectionQuality, networkState.isOnline])

  return {
    // Basic network state
    isOnline: networkState.isOnline,
    isSlowConnection: networkState.isSlowConnection,
    connectionType: networkState.connectionType,
    effectiveType: networkState.effectiveType,

    // Connection metrics
    rtt: networkState.rtt,
    downlink: networkState.downlink,
    saveData: networkState.saveData,

    // Quality assessment
    connectionQuality,

    // Utility functions
    testConnectionSpeed,
    optimizeRequestForConnection,
    shouldLoadResource,

    // Jorge-specific helpers
    canHandlePropertyPhotos: connectionQuality.canLoadImages,
    canStreamBotConversations: connectionQuality.quality !== 'offline',
    shouldCacheAggressively: connectionQuality.recommendedCacheStrategy === 'aggressive',
    recommendReducedUI: connectionQuality.shouldReduceData || networkState.isSlowConnection
  }
}