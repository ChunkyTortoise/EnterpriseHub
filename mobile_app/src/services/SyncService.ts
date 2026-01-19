/**
 * Sync Service for Mobile Offline-First Architecture
 * Handles bidirectional data synchronization with the backend
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-netinfo/netinfo';
import BackgroundJob from 'react-native-background-job';
import DeviceInfo from 'react-native-device-info';

import {ApiService} from './ApiService';
import {OfflineStorageService} from './OfflineStorageService';

export interface SyncOperation {
  id: string;
  type: 'create' | 'update' | 'delete';
  entityType: 'lead' | 'property' | 'note' | 'task';
  entityId: string;
  data: any;
  timestamp: string;
  retryCount: number;
}

export interface SyncStatus {
  isOnline: boolean;
  isSyncing: boolean;
  lastSyncTime: string | null;
  pendingOperations: number;
  failedOperations: number;
}

class SyncServiceClass {
  private isInitialized = false;
  private isOnline = false;
  private isSyncing = false;
  private syncInterval: NodeJS.Timeout | null = null;
  private pendingOperations: SyncOperation[] = [];

  async initialize() {
    if (this.isInitialized) return;

    try {
      // Load pending operations from storage
      await this.loadPendingOperations();

      // Listen to network state changes
      NetInfo.addEventListener(state => {
        const wasOnline = this.isOnline;
        this.isOnline = state.isConnected ?? false;

        // If we just came back online, trigger sync
        if (!wasOnline && this.isOnline) {
          console.log('📶 Network restored, triggering sync...');
          this.triggerSync();
        }
      });

      // Get initial network state
      const netInfo = await NetInfo.fetch();
      this.isOnline = netInfo.isConnected ?? false;

      // Set up periodic sync
      this.setupPeriodicSync();

      // Set up background sync
      this.setupBackgroundSync();

      this.isInitialized = true;
      console.log('🔄 SyncService initialized');

    } catch (error) {
      console.error('❌ SyncService initialization failed:', error);
    }
  }

  private setupPeriodicSync() {
    // Sync every 5 minutes when app is active
    this.syncInterval = setInterval(() => {
      if (this.isOnline && !this.isSyncing) {
        this.triggerSync();
      }
    }, 5 * 60 * 1000); // 5 minutes
  }

  private setupBackgroundSync() {
    // Configure background sync for when app is backgrounded
    BackgroundJob.start({
      jobKey: 'ghlRealEstateSync',
      period: 15000, // 15 seconds
    });

    BackgroundJob.on('ghlRealEstateSync', () => {
      if (this.isOnline && this.pendingOperations.length > 0) {
        this.triggerBackgroundSync();
      }
    });
  }

  async triggerSync(force = false): Promise<SyncStatus> {
    if (this.isSyncing && !force) {
      return this.getSyncStatus();
    }

    if (!this.isOnline) {
      console.log('📱 Offline - sync skipped');
      return this.getSyncStatus();
    }

    this.isSyncing = true;

    try {
      console.log('🔄 Starting sync...');

      // Process pending operations
      await this.processPendingOperations();

      // Fetch server updates
      await this.fetchServerUpdates();

      // Update last sync time
      await AsyncStorage.setItem('lastSyncTime', new Date().toISOString());

      console.log('✅ Sync completed successfully');

    } catch (error) {
      console.error('❌ Sync failed:', error);
    } finally {
      this.isSyncing = false;
    }

    return this.getSyncStatus();
  }

  async triggerBackgroundSync(): Promise<void> {
    try {
      // Lightweight background sync - only critical operations
      const criticalOps = this.pendingOperations
        .filter(op => op.type === 'create' || (op.type === 'update' && op.retryCount < 3))
        .slice(0, 5); // Limit to 5 operations

      if (criticalOps.length === 0) return;

      console.log(`🔄 Background sync processing ${criticalOps.length} operations`);

      for (const operation of criticalOps) {
        try {
          await this.processOperation(operation);
          this.removePendingOperation(operation.id);
        } catch (error) {
          operation.retryCount++;
          console.warn(`⚠️ Background sync operation failed: ${operation.id}`, error);
        }
      }

      await this.savePendingOperations();

    } catch (error) {
      console.error('❌ Background sync failed:', error);
    }
  }

  async queueOperation(operation: Omit<SyncOperation, 'id' | 'timestamp' | 'retryCount'>): Promise<string> {
    const syncOperation: SyncOperation = {
      ...operation,
      id: `sync_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date().toISOString(),
      retryCount: 0,
    };

    this.pendingOperations.push(syncOperation);
    await this.savePendingOperations();

    console.log(`📝 Operation queued: ${syncOperation.type} ${syncOperation.entityType}`);

    // Try immediate sync if online
    if (this.isOnline && !this.isSyncing) {
      setTimeout(() => this.triggerSync(), 100);
    }

    return syncOperation.id;
  }

  private async processPendingOperations(): Promise<void> {
    if (this.pendingOperations.length === 0) return;

    console.log(`📤 Processing ${this.pendingOperations.length} pending operations`);

    const maxBatchSize = 10;
    const batch = this.pendingOperations.slice(0, maxBatchSize);

    for (const operation of batch) {
      try {
        await this.processOperation(operation);
        this.removePendingOperation(operation.id);
        console.log(`✅ Operation processed: ${operation.id}`);

      } catch (error) {
        operation.retryCount++;
        console.error(`❌ Operation failed: ${operation.id}`, error);

        // Remove operations that have failed too many times
        if (operation.retryCount >= 5) {
          console.warn(`🗑️ Removing failed operation: ${operation.id}`);
          this.removePendingOperation(operation.id);
        }
      }
    }

    await this.savePendingOperations();
  }

  private async processOperation(operation: SyncOperation): Promise<void> {
    const { type, entityType, entityId, data } = operation;

    switch (entityType) {
      case 'lead':
        await this.processLeadOperation(type, entityId, data);
        break;
      case 'property':
        await this.processPropertyOperation(type, entityId, data);
        break;
      case 'note':
        await this.processNoteOperation(type, entityId, data);
        break;
      case 'task':
        await this.processTaskOperation(type, entityId, data);
        break;
      default:
        throw new Error(`Unsupported entity type: ${entityType}`);
    }
  }

  private async processLeadOperation(type: string, entityId: string, data: any): Promise<void> {
    switch (type) {
      case 'create':
        // Create new lead via API
        break;
      case 'update':
        await ApiService.quickUpdateLead(entityId, data);
        break;
      case 'delete':
        // Delete lead via API
        break;
    }
  }

  private async processPropertyOperation(type: string, entityId: string, data: any): Promise<void> {
    // Process property operations
  }

  private async processNoteOperation(type: string, entityId: string, data: any): Promise<void> {
    // Process note operations
  }

  private async processTaskOperation(type: string, entityId: string, data: any): Promise<void> {
    // Process task operations
  }

  private async fetchServerUpdates(): Promise<void> {
    try {
      const lastSyncTime = await AsyncStorage.getItem('lastSyncTime');
      const deviceId = await DeviceInfo.getUniqueId();

      const syncRequest = {
        device_id: deviceId,
        last_sync: lastSyncTime || new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(), // 24h ago
        pending_operations: [],
        app_version: DeviceInfo.getVersion(),
      };

      const serverResponse = await ApiService.performSync(syncRequest);

      if (serverResponse.server_updates && serverResponse.server_updates.length > 0) {
        console.log(`📥 Processing ${serverResponse.server_updates.length} server updates`);

        // Apply server updates to local storage
        for (const update of serverResponse.server_updates) {
          await OfflineStorageService.applyServerUpdate(update);
        }
      }

    } catch (error) {
      console.error('❌ Failed to fetch server updates:', error);
    }
  }

  private removePendingOperation(operationId: string): void {
    this.pendingOperations = this.pendingOperations.filter(op => op.id !== operationId);
  }

  private async loadPendingOperations(): Promise<void> {
    try {
      const stored = await AsyncStorage.getItem('pendingOperations');
      if (stored) {
        this.pendingOperations = JSON.parse(stored);
        console.log(`📂 Loaded ${this.pendingOperations.length} pending operations`);
      }
    } catch (error) {
      console.error('❌ Failed to load pending operations:', error);
      this.pendingOperations = [];
    }
  }

  private async savePendingOperations(): Promise<void> {
    try {
      await AsyncStorage.setItem('pendingOperations', JSON.stringify(this.pendingOperations));
    } catch (error) {
      console.error('❌ Failed to save pending operations:', error);
    }
  }

  getSyncStatus(): SyncStatus {
    return {
      isOnline: this.isOnline,
      isSyncing: this.isSyncing,
      lastSyncTime: null, // Will be loaded async
      pendingOperations: this.pendingOperations.length,
      failedOperations: this.pendingOperations.filter(op => op.retryCount > 0).length,
    };
  }

  async getLastSyncTime(): Promise<string | null> {
    return await AsyncStorage.getItem('lastSyncTime');
  }

  async forcefulSync(): Promise<SyncStatus> {
    return this.triggerSync(true);
  }

  async clearPendingOperations(): Promise<void> {
    this.pendingOperations = [];
    await AsyncStorage.removeItem('pendingOperations');
    console.log('🗑️ Cleared all pending operations');
  }

  destroy(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }

    BackgroundJob.stop('ghlRealEstateSync');
    console.log('🛑 SyncService destroyed');
  }
}

export const SyncService = new SyncServiceClass();