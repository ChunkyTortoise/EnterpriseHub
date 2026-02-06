/**
 * Jorge Real Estate AI Platform - Offline Storage React Hook
 * Easy-to-use React hook for accessing offline storage capabilities
 *
 * Features:
 * - Reactive state management for offline operations
 * - Optimistic UI updates with automatic rollback
 * - Real-time sync status monitoring
 * - Jorge-specific convenience methods
 * - Error boundary integration
 */

'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { offlineStorage, OfflineOperation, PropertyData, ConversationThread, VoiceNote, UserSettings } from '@/lib/offline/OfflineStorage';

interface OfflineStatus {
  isOnline: boolean;
  syncStatus: 'idle' | 'syncing' | 'paused' | 'error';
  pendingOperations: number;
  lastSync?: number;
  storageUsed: number;
  storageQuota: number;
}

interface OptimisticOperation<T> {
  id: string;
  type: 'CREATE' | 'UPDATE' | 'DELETE';
  data: T;
  storeName: string;
  timestamp: number;
  status: 'pending' | 'success' | 'error';
  rollbackData?: T;
}

export function useOfflineStorage() {
  const [status, setStatus] = useState<OfflineStatus>({
    isOnline: navigator.onLine,
    syncStatus: 'idle',
    pendingOperations: 0,
    storageUsed: 0,
    storageQuota: 0
  });

  const [optimisticOps, setOptimisticOps] = useState<OptimisticOperation<any>[]>([]);
  const statusUpdateRef = useRef<NodeJS.Timeout>();

  // Update status periodically
  useEffect(() => {
    const updateStatus = async () => {
      try {
        const pendingOps = await offlineStorage.getPendingOperations();
        const storageStats = await offlineStorage.getStorageStats();

        setStatus(prev => ({
          ...prev,
          isOnline: navigator.onLine,
          pendingOperations: pendingOps.length,
          storageUsed: storageStats.used,
          storageQuota: storageStats.quota
        }));
      } catch (error) {
        console.error('Failed to update offline status:', error);
      }
    };

    // Initial update
    updateStatus();

    // Set up periodic updates
    statusUpdateRef.current = setInterval(updateStatus, 5000);

    // Listen for online/offline events
    const handleOnline = () => setStatus(prev => ({ ...prev, isOnline: true }));
    const handleOffline = () => setStatus(prev => ({ ...prev, isOnline: false }));

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      if (statusUpdateRef.current) {
        clearInterval(statusUpdateRef.current);
      }
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Generic storage operations with optimistic updates
  const store = useCallback(async <T>(
    storeName: string,
    data: T,
    options?: { optimistic?: boolean; rollbackData?: T }
  ): Promise<void> => {
    const operationId = `op_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    try {
      // Add optimistic operation if enabled
      if (options?.optimistic) {
        const optimisticOp: OptimisticOperation<T> = {
          id: operationId,
          type: 'CREATE',
          data,
          storeName,
          timestamp: Date.now(),
          status: 'pending',
          rollbackData: options.rollbackData
        };

        setOptimisticOps(prev => [...prev, optimisticOp]);
      }

      // Perform actual storage operation
      await offlineStorage.store(storeName, data);

      // Mark optimistic operation as successful
      if (options?.optimistic) {
        setOptimisticOps(prev =>
          prev.map(op =>
            op.id === operationId
              ? { ...op, status: 'success' as const }
              : op
          )
        );

        // Remove successful operation after delay
        setTimeout(() => {
          setOptimisticOps(prev => prev.filter(op => op.id !== operationId));
        }, 2000);
      }

    } catch (error) {
      // Handle optimistic rollback
      if (options?.optimistic && options?.rollbackData) {
        setOptimisticOps(prev =>
          prev.map(op =>
            op.id === operationId
              ? { ...op, status: 'error' as const }
              : op
          )
        );

        // Attempt rollback
        try {
          await offlineStorage.store(storeName, options.rollbackData);
        } catch (rollbackError) {
          console.error('Rollback failed:', rollbackError);
        }
      }

      throw error;
    }
  }, []);

  const retrieve = useCallback(async <T>(
    storeName: string,
    id: string
  ): Promise<T | null> => {
    return await offlineStorage.retrieve<T>(storeName, id);
  }, []);

  const query = useCallback(async <T>(
    storeName: string,
    options?: {
      index?: string;
      range?: IDBKeyRange;
      direction?: IDBCursorDirection;
      limit?: number;
    }
  ): Promise<T[]> => {
    return await offlineStorage.query<T>(storeName, options);
  }, []);

  const remove = useCallback(async (
    storeName: string,
    id: string,
    options?: { optimistic?: boolean }
  ): Promise<void> => {
    const operationId = `op_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    try {
      // Get current data for potential rollback
      let rollbackData = null;
      if (options?.optimistic) {
        rollbackData = await offlineStorage.retrieve(storeName, id);

        const optimisticOp: OptimisticOperation<any> = {
          id: operationId,
          type: 'DELETE',
          data: { id },
          storeName,
          timestamp: Date.now(),
          status: 'pending',
          rollbackData
        };

        setOptimisticOps(prev => [...prev, optimisticOp]);
      }

      await offlineStorage.delete(storeName, id);

      // Mark as successful
      if (options?.optimistic) {
        setOptimisticOps(prev =>
          prev.map(op =>
            op.id === operationId
              ? { ...op, status: 'success' as const }
              : op
          )
        );

        setTimeout(() => {
          setOptimisticOps(prev => prev.filter(op => op.id !== operationId));
        }, 2000);
      }

    } catch (error) {
      // Handle rollback on error
      if (options?.optimistic) {
        setOptimisticOps(prev =>
          prev.map(op =>
            op.id === operationId
              ? { ...op, status: 'error' as const }
              : op
          )
        );
      }

      throw error;
    }
  }, []);

  // Jorge-specific convenience methods
  const jorge = {
    // Property operations
    storeProperty: useCallback(async (property: PropertyData, optimistic = true) => {
      return store('cachedProperties', property, { optimistic });
    }, [store]),

    getProperty: useCallback(async (propertyId: string): Promise<PropertyData | null> => {
      return retrieve<PropertyData>('cachedProperties', propertyId);
    }, [retrieve]),

    getPropertiesNearLocation: useCallback(async (lat: number, lng: number, radius = 5): Promise<PropertyData[]> => {
      return offlineStorage.getPropertiesNearLocation(lat, lng, radius);
    }, []),

    // Conversation operations
    storeConversation: useCallback(async (conversation: ConversationThread, optimistic = true) => {
      return store('botConversations', conversation, { optimistic });
    }, [store]),

    getConversation: useCallback(async (conversationId: string): Promise<ConversationThread | null> => {
      return retrieve<ConversationThread>('botConversations', conversationId);
    }, [retrieve]),

    getActiveConversations: useCallback(async (): Promise<ConversationThread[]> => {
      return offlineStorage.getActiveConversations();
    }, []),

    // Voice note operations
    storeVoiceNote: useCallback(async (note: VoiceNote, optimistic = true) => {
      return store('leadNotes', note, { optimistic });
    }, [store]),

    getVoiceNote: useCallback(async (noteId: string): Promise<VoiceNote | null> => {
      return retrieve<VoiceNote>('leadNotes', noteId);
    }, [retrieve]),

    getVoiceNotesForProperty: useCallback(async (propertyId: string): Promise<VoiceNote[]> => {
      return offlineStorage.getVoiceNotesForProperty(propertyId);
    }, []),

    // User preferences
    storePreferences: useCallback(async (preferences: UserSettings, optimistic = true) => {
      return store('userPreferences', preferences, { optimistic });
    }, [store]),

    getPreferences: useCallback(async (userId: string): Promise<UserSettings | null> => {
      return retrieve<UserSettings>('userPreferences', userId);
    }, [retrieve])
  };

  // Storage management
  const clearAllData = useCallback(async (): Promise<void> => {
    await offlineStorage.clearAllData();
    setOptimisticOps([]);
  }, []);

  const getStorageStats = useCallback(async () => {
    return offlineStorage.getStorageStats();
  }, []);

  // Optimistic UI helpers
  const getOptimisticOperations = useCallback(() => {
    return optimisticOps;
  }, [optimisticOps]);

  const hasOptimisticOperation = useCallback((storeName: string, recordId?: string) => {
    return optimisticOps.some(op =>
      op.storeName === storeName &&
      (recordId ? (op.data as any)?.id === recordId : true) &&
      op.status === 'pending'
    );
  }, [optimisticOps]);

  const getOptimisticValue = useCallback(<T>(storeName: string, recordId: string): T | null => {
    const op = optimisticOps.find(op =>
      op.storeName === storeName &&
      (op.data as any)?.id === recordId &&
      op.status === 'pending'
    );

    return op ? op.data as T : null;
  }, [optimisticOps]);

  // Error handling
  const retryFailedOperations = useCallback(async () => {
    const failedOps = optimisticOps.filter(op => op.status === 'error');

    for (const op of failedOps) {
      try {
        if (op.type === 'DELETE') {
          await offlineStorage.delete(op.storeName, (op.data as any).id);
        } else {
          await offlineStorage.store(op.storeName, op.data);
        }

        setOptimisticOps(prev =>
          prev.map(prevOp =>
            prevOp.id === op.id
              ? { ...prevOp, status: 'success' as const }
              : prevOp
          )
        );
      } catch (error) {
        console.error(`Failed to retry operation ${op.id}:`, error);
      }
    }
  }, [optimisticOps]);

  // Add generic data storage methods needed by property scanner
  const storeData = useCallback(async (key: string, data: any): Promise<void> => {
    return store('scanCache', { id: key, data, timestamp: Date.now() });
  }, [store]);

  const getData = useCallback(async (key: string): Promise<any> => {
    const result = await retrieve<{ id: string; data: any; timestamp: number }>('scanCache', key);
    return result ? result.data : null;
  }, [retrieve]);

  return {
    // Status
    status,
    isOnline: status.isOnline,
    syncStatus: status.syncStatus,
    pendingOperations: status.pendingOperations,

    // Core operations
    store,
    retrieve,
    query,
    remove,
    storeData,
    getData,

    // Jorge-specific operations
    jorge,

    // Storage management
    clearAllData,
    getStorageStats,

    // Optimistic UI
    getOptimisticOperations,
    hasOptimisticOperation,
    getOptimisticValue,
    retryFailedOperations,

    // Helpers
    formatBytes: (bytes: number) => {
      if (bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    getStoragePercentage: () => {
      if (status.storageQuota === 0) return 0;
      return (status.storageUsed / status.storageQuota) * 100;
    }
  };
}

// Specialized hooks for specific data types
export function usePropertyStorage() {
  const { jorge } = useOfflineStorage();
  return jorge;
}

export function useConversationStorage() {
  const { jorge } = useOfflineStorage();

  const addMessageToConversation = useCallback(async (
    conversationId: string,
    message: ConversationThread['messages'][0],
    optimistic = true
  ) => {
    const conversation = await jorge.getConversation(conversationId);
    if (!conversation) return;

    const updatedConversation = {
      ...conversation,
      messages: [...conversation.messages, message],
      last_activity: Date.now(),
      sync_version: Date.now()
    };

    await jorge.storeConversation(updatedConversation, optimistic);
  }, [jorge]);

  const updateJorgeContext = useCallback(async (
    conversationId: string,
    context: Partial<ConversationThread['jorge_context']>,
    optimistic = true
  ) => {
    const conversation = await jorge.getConversation(conversationId);
    if (!conversation) return;

    const updatedConversation = {
      ...conversation,
      jorge_context: {
        ...conversation.jorge_context,
        ...context
      },
      sync_version: Date.now()
    };

    await jorge.storeConversation(updatedConversation, optimistic);
  }, [jorge]);

  return {
    ...jorge,
    addMessageToConversation,
    updateJorgeContext
  };
}

export function useVoiceNoteStorage() {
  const { jorge } = useOfflineStorage();

  const storeVoiceNoteWithAnalysis = useCallback(async (
    note: Omit<VoiceNote, 'id' | 'created_at' | 'sync_version'>,
    optimistic = true
  ) => {
    const enrichedNote: VoiceNote = {
      ...note,
      id: `voice_note_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      created_at: Date.now(),
      sync_version: Date.now()
    };

    await jorge.storeVoiceNote(enrichedNote, optimistic);
    return enrichedNote.id;
  }, [jorge]);

  return {
    ...jorge,
    storeVoiceNoteWithAnalysis
  };
}