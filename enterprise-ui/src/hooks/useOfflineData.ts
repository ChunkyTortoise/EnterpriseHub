// Jorge's Real Estate AI Platform - Offline Data Management Hook
// Provides seamless offline capabilities with intelligent sync

import { useState, useEffect, useCallback, useRef } from 'react'
import { useNetwork } from './useNetwork'

interface OfflineDataOptions {
  storeName: string
  syncEndpoint?: string
  autoSync?: boolean
  maxRetries?: number
  retryDelay?: number
}

interface QueuedAction {
  id: string
  type: string
  data: any
  endpoint: string
  method: string
  timestamp: number
  retries: number
}

interface OfflineDataState {
  isOnline: boolean
  isSyncing: boolean
  hasQueuedActions: boolean
  queueSize: number
  lastSyncTime: number | null
  syncError: string | null
}

class OfflineQueue {
  private dbName = 'jorge-offline-storage'
  private version = 1
  private db: IDBDatabase | null = null

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version)

      request.onerror = () => reject(request.error)
      request.onsuccess = () => {
        this.db = request.result
        resolve()
      }

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result

        // Property data store
        if (!db.objectStoreNames.contains('properties')) {
          const propertyStore = db.createObjectStore('properties', { keyPath: 'id' })
          propertyStore.createIndex('location', ['lat', 'lng'])
          propertyStore.createIndex('timestamp', 'timestamp')
        }

        // Lead data store
        if (!db.objectStoreNames.contains('leads')) {
          const leadStore = db.createObjectStore('leads', { keyPath: 'id' })
          leadStore.createIndex('temperature', 'temperature')
          leadStore.createIndex('timestamp', 'timestamp')
        }

        // Bot conversations store
        if (!db.objectStoreNames.contains('conversations')) {
          const conversationStore = db.createObjectStore('conversations', { keyPath: 'id' })
          conversationStore.createIndex('leadId', 'leadId')
          conversationStore.createIndex('botType', 'botType')
        }

        // Sync queue store
        if (!db.objectStoreNames.contains('syncQueue')) {
          const queueStore = db.createObjectStore('syncQueue', { keyPath: 'id' })
          queueStore.createIndex('type', 'type')
          queueStore.createIndex('timestamp', 'timestamp')
        }

        // Analytics cache
        if (!db.objectStoreNames.contains('analytics')) {
          const analyticsStore = db.createObjectStore('analytics', { keyPath: 'key' })
          analyticsStore.createIndex('timestamp', 'timestamp')
        }
      }
    })
  }

  async store(storeName: string, data: any): Promise<void> {
    if (!this.db) await this.init()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readwrite')
      const store = transaction.objectStore(storeName)

      const request = store.put({
        ...data,
        timestamp: Date.now(),
        synced: false
      })

      request.onerror = () => reject(request.error)
      request.onsuccess = () => resolve()
    })
  }

  async get(storeName: string, id: string): Promise<any> {
    if (!this.db) await this.init()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)
      const request = store.get(id)

      request.onerror = () => reject(request.error)
      request.onsuccess = () => resolve(request.result)
    })
  }

  async getAll(storeName: string, indexName?: string, value?: any): Promise<any[]> {
    if (!this.db) await this.init()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readonly')
      const store = transaction.objectStore(storeName)

      let request: IDBRequest

      if (indexName && value !== undefined) {
        const index = store.index(indexName)
        request = index.getAll(value)
      } else {
        request = store.getAll()
      }

      request.onerror = () => reject(request.error)
      request.onsuccess = () => resolve(request.result)
    })
  }

  async queueAction(action: QueuedAction): Promise<void> {
    if (!this.db) await this.init()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['syncQueue'], 'readwrite')
      const store = transaction.objectStore('syncQueue')

      const request = store.put(action)

      request.onerror = () => reject(request.error)
      request.onsuccess = () => resolve()
    })
  }

  async getQueuedActions(): Promise<QueuedAction[]> {
    if (!this.db) await this.init()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['syncQueue'], 'readonly')
      const store = transaction.objectStore('syncQueue')
      const request = store.getAll()

      request.onerror = () => reject(request.error)
      request.onsuccess = () => resolve(request.result)
    })
  }

  async removeQueuedAction(id: string): Promise<void> {
    if (!this.db) await this.init()

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['syncQueue'], 'readwrite')
      const store = transaction.objectStore('syncQueue')
      const request = store.delete(id)

      request.onerror = () => reject(request.error)
      request.onsuccess = () => resolve()
    })
  }

  async clearExpiredData(storeName: string, maxAge: number): Promise<void> {
    if (!this.db) await this.init()

    const cutoffTime = Date.now() - maxAge

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([storeName], 'readwrite')
      const store = transaction.objectStore('storeName')
      const index = store.index('timestamp')
      const range = IDBKeyRange.upperBound(cutoffTime)

      const request = index.openCursor(range)

      request.onerror = () => reject(request.error)
      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result
        if (cursor) {
          cursor.delete()
          cursor.continue()
        } else {
          resolve()
        }
      }
    })
  }
}

export function useOfflineData(options: OfflineDataOptions) {
  const { isOnline } = useNetwork()
  const [state, setState] = useState<OfflineDataState>({
    isOnline,
    isSyncing: false,
    hasQueuedActions: false,
    queueSize: 0,
    lastSyncTime: null,
    syncError: null
  })

  const offlineQueue = useRef(new OfflineQueue())
  const syncInProgress = useRef(false)

  const {
    storeName,
    syncEndpoint,
    autoSync = true,
    maxRetries = 3,
    retryDelay = 5000
  } = options

  // Initialize offline storage
  useEffect(() => {
    offlineQueue.current.init().catch(console.error)
  }, [])

  // Update online status
  useEffect(() => {
    setState(prev => ({ ...prev, isOnline }))

    // Auto-sync when coming back online
    if (isOnline && autoSync && !syncInProgress.current) {
      syncQueuedActions()
    }
  }, [isOnline, autoSync])

  // Check queued actions on mount
  useEffect(() => {
    checkQueuedActions()
  }, [])

  const checkQueuedActions = useCallback(async () => {
    try {
      const queuedActions = await offlineQueue.current.getQueuedActions()
      setState(prev => ({
        ...prev,
        hasQueuedActions: queuedActions.length > 0,
        queueSize: queuedActions.length
      }))
    } catch (error) {
      console.error('Failed to check queued actions:', error)
    }
  }, [])

  const storeData = useCallback(async (data: any, forceQueue = false) => {
    try {
      // Store data locally first
      await offlineQueue.current.store(storeName, data)

      if (isOnline && !forceQueue && syncEndpoint) {
        // Try to sync immediately if online
        try {
          const response = await fetch(syncEndpoint, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
          })

          if (!response.ok) {
            throw new Error(`Sync failed: ${response.status}`)
          }

          console.log('Data synced immediately')
          return { success: true, synced: true }
        } catch (syncError) {
          console.warn('Immediate sync failed, queuing for later:', syncError)
          await queueForSync(data, 'create')
        }
      } else {
        // Queue for sync when offline or forced
        await queueForSync(data, 'create')
      }

      await checkQueuedActions()
      return { success: true, synced: false }
    } catch (error) {
      console.error('Failed to store data:', error)
      return { success: false, error: error.message }
    }
  }, [isOnline, storeName, syncEndpoint])

  const getData = useCallback(async (id: string) => {
    try {
      const data = await offlineQueue.current.get(storeName, id)
      return { success: true, data }
    } catch (error) {
      console.error('Failed to get data:', error)
      return { success: false, error: error.message }
    }
  }, [storeName])

  const getAllData = useCallback(async (indexName?: string, value?: any) => {
    try {
      const data = await offlineQueue.current.getAll(storeName, indexName, value)
      return { success: true, data }
    } catch (error) {
      console.error('Failed to get all data:', error)
      return { success: false, error: error.message }
    }
  }, [storeName])

  const queueForSync = useCallback(async (data: any, actionType: string) => {
    const queuedAction: QueuedAction = {
      id: crypto.randomUUID(),
      type: actionType,
      data,
      endpoint: syncEndpoint || '',
      method: 'POST',
      timestamp: Date.now(),
      retries: 0
    }

    await offlineQueue.current.queueAction(queuedAction)
    await checkQueuedActions()
  }, [syncEndpoint, checkQueuedActions])

  const syncQueuedActions = useCallback(async () => {
    if (syncInProgress.current || !isOnline || !syncEndpoint) return

    syncInProgress.current = true
    setState(prev => ({ ...prev, isSyncing: true, syncError: null }))

    try {
      const queuedActions = await offlineQueue.current.getQueuedActions()

      for (const action of queuedActions) {
        try {
          const response = await fetch(action.endpoint, {
            method: action.method,
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(action.data)
          })

          if (response.ok) {
            // Remove successfully synced action
            await offlineQueue.current.removeQueuedAction(action.id)
            console.log('Synced queued action:', action.id)
          } else {
            // Increment retry count
            action.retries++

            if (action.retries >= maxRetries) {
              console.error('Max retries reached for action:', action.id)
              await offlineQueue.current.removeQueuedAction(action.id)
            } else {
              // Update retry count and delay next attempt
              await offlineQueue.current.queueAction(action)
              setTimeout(() => {
                // Retry after delay
              }, retryDelay * action.retries)
            }
          }
        } catch (syncError) {
          console.error('Failed to sync action:', action.id, syncError)
          action.retries++

          if (action.retries >= maxRetries) {
            await offlineQueue.current.removeQueuedAction(action.id)
          } else {
            await offlineQueue.current.queueAction(action)
          }
        }
      }

      setState(prev => ({
        ...prev,
        lastSyncTime: Date.now()
      }))

      await checkQueuedActions()
    } catch (error) {
      console.error('Sync failed:', error)
      setState(prev => ({
        ...prev,
        syncError: error.message
      }))
    } finally {
      syncInProgress.current = false
      setState(prev => ({ ...prev, isSyncing: false }))
    }
  }, [isOnline, syncEndpoint, maxRetries, retryDelay, checkQueuedActions])

  const clearExpiredData = useCallback(async (maxAge: number = 7 * 24 * 60 * 60 * 1000) => {
    try {
      await offlineQueue.current.clearExpiredData(storeName, maxAge)
      console.log('Expired data cleared')
    } catch (error) {
      console.error('Failed to clear expired data:', error)
    }
  }, [storeName])

  return {
    ...state,
    storeData,
    getData,
    getAllData,
    syncQueuedActions,
    clearExpiredData,
    offlineQueue: offlineQueue.current
  }
}