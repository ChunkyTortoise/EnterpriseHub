// Offline capabilities hook for Jorge's Real Estate Platform
// Enables field agents to work with cached data when offline

'use client'

import { useState, useEffect } from 'react'

interface OfflineData {
  conversations: Record<string, any>
  properties: Record<string, any> 
  leads: Record<string, any>
  lastSync: string
}

export function useOfflineCapability() {
  const [isOnline, setIsOnline] = useState(true)
  const [offlineData, setOfflineData] = useState<OfflineData>({
    conversations: {},
    properties: {},
    leads: {},
    lastSync: new Date().toISOString()
  })
  const [pendingActions, setPendingActions] = useState<any[]>([])

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      syncPendingActions()
    }
    const handleOffline = () => setIsOnline(false)
    
    // Set initial state
    setIsOnline(navigator.onLine)
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    return () => {
      window.removeEventListener('online', handleOnline) 
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  // Load offline data from cache on mount
  useEffect(() => {
    loadOfflineData()
  }, [])

  const loadOfflineData = async () => {
    try {
      const cache = await caches.open('jorge-offline-v1')
      const cachedData = await cache.match('/offline/data')
      
      if (cachedData) {
        const data = await cachedData.json()
        setOfflineData(data)
      }
    } catch (error) {
      console.warn('Failed to load offline data:', error)
    }
  }

  const saveOfflineData = async (key: keyof OfflineData, data: any) => {
    const updatedOfflineData = {
      ...offlineData,
      [key]: { ...offlineData[key], ...data },
      lastSync: new Date().toISOString()
    }
    
    setOfflineData(updatedOfflineData)
    
    // Cache data for offline use
    try {
      const cache = await caches.open('jorge-offline-v1')
      await cache.put(
        '/offline/data',
        new Response(JSON.stringify(updatedOfflineData))
      )
    } catch (error) {
      console.warn('Failed to save offline data:', error)
    }
  }

  // Cache property data for offline browsing
  const cachePropertyData = async (propertyId: string, propertyData: any) => {
    await saveOfflineData('properties', { [propertyId]: propertyData })
  }

  // Cache conversation data
  const cacheConversation = async (conversationId: string, messages: any[]) => {
    await saveOfflineData('conversations', { [conversationId]: messages })
  }

  // Cache lead information
  const cacheLeadData = async (leadId: string, leadData: any) => {
    await saveOfflineData('leads', { [leadId]: leadData })
  }

  // Queue actions for when back online
  const queueAction = (action: {
    type: string
    endpoint: string
    data: any
    timestamp: string
  }) => {
    const updatedActions = [...pendingActions, action]
    setPendingActions(updatedActions)
    
    // Store in localStorage for persistence
    localStorage.setItem('jorge_pending_actions', JSON.stringify(updatedActions))
  }

  // Sync pending actions when back online
  const syncPendingActions = async () => {
    if (!isOnline || pendingActions.length === 0) return

    console.log(`Syncing ${pendingActions.length} pending actions...`)
    
    const syncPromises = pendingActions.map(async (action) => {
      try {
        const response = await fetch(action.endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(action.data)
        })
        
        if (!response.ok) {
          throw new Error(`Failed to sync ${action.type}: ${response.statusText}`)
        }
        
        return { success: true, action }
      } catch (error) {
        console.error(`Failed to sync action ${action.type}:`, error)
        return { success: false, action, error }
      }
    })
    
    const results = await Promise.allSettled(syncPromises)
    
    // Remove successfully synced actions
    const failedActions = results
      .filter((result, index) => {
        if (result.status === 'rejected') return true
        if (result.status === 'fulfilled' && !result.value.success) return true
        return false
      })
      .map((_, index) => pendingActions[index])
    
    setPendingActions(failedActions)
    localStorage.setItem('jorge_pending_actions', JSON.stringify(failedActions))
    
    const successCount = pendingActions.length - failedActions.length
    console.log(`Successfully synced ${successCount} actions`)
  }

  // Offline-friendly API request wrapper
  const offlineRequest = async (
    endpoint: string, 
    options: RequestInit = {},
    fallbackData?: any
  ) => {
    if (isOnline) {
      try {
        const response = await fetch(endpoint, options)
        
        if (response.ok) {
          const data = await response.json()
          
          // Cache successful responses
          if (options.method === 'GET') {
            const cache = await caches.open('jorge-api-cache-v1')
            await cache.put(endpoint, response.clone())
          }
          
          return { data, fromCache: false, success: true }
        }
        
        throw new Error(`Request failed: ${response.statusText}`)
        
      } catch (error) {
        console.warn('Online request failed, checking cache:', error)
        
        // Fall back to cache
        const cache = await caches.open('jorge-api-cache-v1')
        const cachedResponse = await cache.match(endpoint)
        
        if (cachedResponse) {
          const data = await cachedResponse.json()
          return { data, fromCache: true, success: true }
        }
        
        if (fallbackData) {
          return { data: fallbackData, fromCache: true, success: true }
        }
        
        throw error
      }
    } else {
      // Offline mode
      if (options.method === 'POST' || options.method === 'PUT') {
        // Queue the action for later sync
        queueAction({
          type: options.method,
          endpoint,
          data: JSON.parse(options.body as string || '{}'),
          timestamp: new Date().toISOString()
        })
        
        return { data: { queued: true }, fromCache: false, success: true }
      }
      
      // Try to serve from cache for GET requests
      const cache = await caches.open('jorge-api-cache-v1')
      const cachedResponse = await cache.match(endpoint)
      
      if (cachedResponse) {
        const data = await cachedResponse.json()
        return { data, fromCache: true, success: true }
      }
      
      if (fallbackData) {
        return { data: fallbackData, fromCache: true, success: true }
      }
      
      throw new Error('Offline: No cached data available')
    }
  }

  // Get offline status summary
  const getOfflineStatus = () => ({
    isOnline,
    pendingActionsCount: pendingActions.length,
    lastSync: offlineData.lastSync,
    cachedConversations: Object.keys(offlineData.conversations).length,
    cachedProperties: Object.keys(offlineData.properties).length,
    cachedLeads: Object.keys(offlineData.leads).length
  })

  return {
    isOnline,
    offlineData,
    pendingActionsCount: pendingActions.length,
    
    // Cache functions
    cachePropertyData,
    cacheConversation, 
    cacheLeadData,
    
    // Request wrapper
    offlineRequest,
    
    // Sync functions
    queueAction,
    syncPendingActions,
    
    // Status
    getOfflineStatus
  }
}