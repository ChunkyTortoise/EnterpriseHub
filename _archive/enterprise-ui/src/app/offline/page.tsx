// Jorge's Real Estate AI Platform - Offline Page
// Fallback page for PWA when no internet connection is available

'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { WifiOff, RefreshCw, Database, FileText, Mic, Camera, CheckCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useNetwork } from '@/hooks/useNetwork'
import { useOfflineData } from '@/hooks/useOfflineData'

interface OfflinePageProps {
  className?: string
}

interface OfflineCapability {
  icon: React.ReactNode
  title: string
  description: string
  available: boolean
}

export default function OfflinePage({ className }: OfflinePageProps) {
  const { isOnline, testConnectionSpeed } = useNetwork()
  const { getAllData, syncQueuedActions } = useOfflineData({
    storeName: 'offline-cache',
    autoSync: false
  })

  const [isRetrying, setIsRetrying] = useState(false)
  const [cachedDataStats, setCachedDataStats] = useState({
    properties: 0,
    leads: 0,
    conversations: 0
  })

  // Load cached data statistics
  useEffect(() => {
    loadCachedDataStats()
  }, [])

  // Auto-redirect when connection is restored
  useEffect(() => {
    if (isOnline) {
      // Give a moment to sync, then redirect
      setTimeout(() => {
        window.location.href = '/field-agent'
      }, 2000)
    }
  }, [isOnline])

  const loadCachedDataStats = async () => {
    try {
      // Get cached data counts
      const propertiesData = await getAllData('properties')
      const leadsData = await getAllData('leads')
      const conversationsData = await getAllData('conversations')

      setCachedDataStats({
        properties: propertiesData.data?.length || 0,
        leads: leadsData.data?.length || 0,
        conversations: conversationsData.data?.length || 0
      })
    } catch (error) {
      console.error('Failed to load cached data stats:', error)
    }
  }

  const handleRetryConnection = async () => {
    setIsRetrying(true)

    try {
      const result = await testConnectionSpeed()
      if (result.quality !== 'offline') {
        // Connection restored
        await syncQueuedActions()
        window.location.reload()
      }
    } catch (error) {
      console.error('Connection test failed:', error)
    } finally {
      setIsRetrying(false)
    }
  }

  const offlineCapabilities: OfflineCapability[] = [
    {
      icon: <Database className="w-6 h-6" />,
      title: 'Cached Properties',
      description: `${cachedDataStats.properties} properties available offline`,
      available: cachedDataStats.properties > 0
    },
    {
      icon: <FileText className="w-6 h-6" />,
      title: 'Lead Information',
      description: `${cachedDataStats.leads} leads stored locally`,
      available: cachedDataStats.leads > 0
    },
    {
      icon: <Mic className="w-6 h-6" />,
      title: 'Voice Notes',
      description: 'Record notes for later sync',
      available: true
    },
    {
      icon: <Camera className="w-6 h-6" />,
      title: 'Property Photos',
      description: 'Capture photos for analysis when online',
      available: true
    }
  ]

  if (isOnline) {
    return (
      <div className={cn('min-h-screen bg-gray-950 text-white flex items-center justify-center', className)}>
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 mx-auto mb-4 text-green-400"
          >
            <RefreshCw className="w-16 h-16" />
          </motion.div>
          <h2 className="text-2xl font-bold text-green-400 mb-2">Connection Restored!</h2>
          <p className="text-gray-400">Syncing data and redirecting...</p>
        </motion.div>
      </div>
    )
  }

  return (
    <div className={cn('min-h-screen bg-gray-950 text-white', className)}>
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <motion.div
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-20 h-20 mx-auto mb-6 text-red-400"
          >
            <WifiOff className="w-20 h-20" />
          </motion.div>

          <h1 className="text-3xl font-bold mb-4">
            Jorge AI - <span className="text-red-400">Offline Mode</span>
          </h1>

          <p className="text-gray-400 max-w-md mx-auto">
            You're currently offline, but Jorge's AI platform continues to work with cached data and offline features.
          </p>
        </motion.div>

        {/* Connection Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 mb-8"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-red-400 mb-1">
                No Internet Connection
              </h3>
              <p className="text-sm text-gray-400">
                Check your connection and try again
              </p>
            </div>

            <button
              onClick={handleRetryConnection}
              disabled={isRetrying}
              className={cn(
                'px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors',
                'flex items-center gap-2',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              <motion.div
                animate={isRetrying ? { rotate: 360 } : {}}
                transition={isRetrying ? { duration: 1, repeat: Infinity, ease: "linear" } : {}}
              >
                <RefreshCw className="w-4 h-4" />
              </motion.div>
              {isRetrying ? 'Checking...' : 'Retry'}
            </button>
          </div>
        </motion.div>

        {/* Offline Capabilities */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-8"
        >
          <h2 className="text-xl font-semibold mb-6">Available Offline Features</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {offlineCapabilities.map((capability, index) => (
              <motion.div
                key={capability.title}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 * index }}
                className={cn(
                  'p-4 rounded-lg border transition-all',
                  capability.available
                    ? 'bg-green-500/10 border-green-500/30 text-green-400'
                    : 'bg-gray-800/50 border-gray-700 text-gray-400'
                )}
              >
                <div className="flex items-start gap-3">
                  <div className={cn(
                    'p-2 rounded-lg',
                    capability.available ? 'bg-green-500/20' : 'bg-gray-700/50'
                  )}>
                    {capability.icon}
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium">{capability.title}</h3>
                      {capability.available && (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      )}
                    </div>
                    <p className="text-sm opacity-75">{capability.description}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Quick Access to Offline Features */}
        {(cachedDataStats.properties > 0 || cachedDataStats.leads > 0) && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-gray-800/50 rounded-xl p-6 mb-8"
          >
            <h2 className="text-xl font-semibold mb-4">Quick Access</h2>

            <div className="grid grid-cols-2 gap-4">
              {cachedDataStats.properties > 0 && (
                <button
                  onClick={() => window.location.href = '/field-agent/properties?offline=true'}
                  className="p-4 bg-blue-500/20 border border-blue-500/30 rounded-lg text-blue-400 hover:bg-blue-500/30 transition-colors text-left"
                >
                  <Database className="w-6 h-6 mb-2" />
                  <div className="font-medium">View Properties</div>
                  <div className="text-sm opacity-75">{cachedDataStats.properties} cached</div>
                </button>
              )}

              {cachedDataStats.leads > 0 && (
                <button
                  onClick={() => window.location.href = '/field-agent/leads?offline=true'}
                  className="p-4 bg-green-500/20 border border-green-500/30 rounded-lg text-green-400 hover:bg-green-500/30 transition-colors text-left"
                >
                  <FileText className="w-6 h-6 mb-2" />
                  <div className="font-medium">View Leads</div>
                  <div className="text-sm opacity-75">{cachedDataStats.leads} available</div>
                </button>
              )}
            </div>
          </motion.div>
        )}

        {/* Helpful Tips */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-6"
        >
          <h2 className="text-lg font-semibold text-blue-400 mb-4">Offline Tips</h2>

          <div className="space-y-3 text-sm text-gray-300">
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0" />
              <p>Data you create offline will automatically sync when connection is restored</p>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0" />
              <p>Voice notes and photos are saved locally and won't be lost</p>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0" />
              <p>Basic calculators and tools work without internet</p>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 bg-blue-400 rounded-full mt-2 flex-shrink-0" />
              <p>Cached property data remains available for quick reference</p>
            </div>
          </div>
        </motion.div>

        {/* Connection Help */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0 }}
          className="mt-8 text-center text-gray-400"
        >
          <p className="text-sm mb-4">
            Having connection issues? Try these steps:
          </p>

          <div className="flex flex-wrap justify-center gap-4 text-xs">
            <span className="px-3 py-1 bg-gray-800 rounded-full">Check WiFi settings</span>
            <span className="px-3 py-1 bg-gray-800 rounded-full">Toggle airplane mode</span>
            <span className="px-3 py-1 bg-gray-800 rounded-full">Move to better signal area</span>
            <span className="px-3 py-1 bg-gray-800 rounded-full">Restart your device</span>
          </div>
        </motion.div>
      </div>
    </div>
  )
}