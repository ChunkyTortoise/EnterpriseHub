/**
 * API Service for Mobile App
 * Handles all API communications with backend
 */

import axios, {AxiosInstance, AxiosRequestConfig, AxiosResponse} from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import DeviceInfo from 'react-native-device-info';
import {Platform} from 'react-native';

import {AuthService} from './AuthService';
import {NetworkService} from './NetworkService';

export interface ApiConfig {
  baseURL: string;
  timeout: number;
  retries: number;
}

export interface MobileDashboard {
  leads_summary: {
    total_count: number;
    hot_leads: number;
    pending_followup: number;
    new_today: number;
  };
  quick_actions: Array<{
    id: string;
    title: string;
    icon: string;
  }>;
  notifications_count: number;
  performance_metrics: {
    conversion_rate: number;
    avg_response_time: number;
    leads_this_week: number;
  };
  sync_timestamp: string;
}

export interface LocationFilter {
  latitude: number;
  longitude: number;
  radius_miles: number;
}

export interface MobileLeadUpdate {
  status?: string;
  notes?: string;
  next_followup?: string;
  tags?: string[];
}

export interface SyncRequest {
  device_id: string;
  last_sync: string;
  pending_operations: any[];
  app_version: string;
}

class ApiServiceClass {
  private api: AxiosInstance;
  private config: ApiConfig;

  constructor() {
    this.config = {
      baseURL: __DEV__
        ? 'http://localhost:8000/api/mobile'
        : 'https://api.ghl-realestate-ai.com/api/mobile',
      timeout: 30000,
      retries: 3,
    };

    this.api = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.api.interceptors.request.use(
      async (config) => {
        // Add auth token
        const token = await AuthService.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add device info
        config.headers['X-Device-ID'] = await DeviceInfo.getUniqueId();
        config.headers['X-Device-Type'] = Platform.OS;
        config.headers['X-App-Version'] = DeviceInfo.getVersion();

        // Add location ID if available
        const locationId = await AsyncStorage.getItem('location_id');
        if (locationId) {
          config.headers['X-Location-ID'] = locationId;
        }

        console.log(`📡 API Request: ${config.method?.toUpperCase()} ${config.url}`);

        return config;
      },
      (error) => {
        console.error('📡 Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.api.interceptors.response.use(
      (response) => {
        console.log(`✅ API Response: ${response.config.url} - ${response.status}`);
        return response;
      },
      async (error) => {
        const originalRequest = error.config;

        // Handle 401 unauthorized
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            await AuthService.refreshToken();
            const newToken = await AuthService.getToken();
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return this.api(originalRequest);
          } catch (refreshError) {
            await AuthService.logout();
            return Promise.reject(refreshError);
          }
        }

        // Handle network errors
        if (!error.response && NetworkService.isOnline()) {
          console.warn('📡 Network error, retrying...');
          return this.retryRequest(originalRequest);
        }

        console.error(`❌ API Error: ${error.config?.url} - ${error.response?.status}`, error.response?.data);
        return Promise.reject(error);
      }
    );
  }

  private async retryRequest(config: AxiosRequestConfig, retryCount = 0): Promise<AxiosResponse> {
    if (retryCount >= this.config.retries) {
      throw new Error('Max retries exceeded');
    }

    // Exponential backoff
    const delay = Math.pow(2, retryCount) * 1000;
    await new Promise(resolve => setTimeout(resolve, delay));

    try {
      return await this.api(config);
    } catch (error) {
      return this.retryRequest(config, retryCount + 1);
    }
  }

  // Dashboard API
  async getDashboard(): Promise<MobileDashboard> {
    const response = await this.api.get<MobileDashboard>('/dashboard');
    return response.data;
  }

  // Leads API
  async getNearbyLeads(
    location: LocationFilter,
    page: number = 1,
    limit: number = 20
  ) {
    const response = await this.api.get('/leads/nearby', {
      params: {
        latitude: location.latitude,
        longitude: location.longitude,
        radius_miles: location.radius_miles,
        page,
        limit,
      },
    });
    return response.data;
  }

  async quickUpdateLead(leadId: string, updateData: MobileLeadUpdate) {
    const response = await this.api.post(`/leads/${leadId}/quick-update`, updateData);
    return response.data;
  }

  async getLeadDetails(leadId: string) {
    const response = await this.api.get(`/leads/${leadId}`);
    return response.data;
  }

  // Properties API
  async getPropertySwipeStack(leadId?: string, limit: number = 10) {
    const response = await this.api.get('/properties/swipe-stack', {
      params: { lead_id: leadId, limit },
    });
    return response.data;
  }

  async getPropertyDetails(propertyId: string) {
    const response = await this.api.get(`/properties/${propertyId}`);
    return response.data;
  }

  // Sync API
  async performSync(syncRequest: SyncRequest) {
    const response = await this.api.post('/sync', syncRequest);
    return response.data;
  }

  // Analytics API
  async getAnalyticsSummary(period: 'day' | 'week' | 'month' = 'week') {
    const response = await this.api.get('/analytics/summary', {
      params: { period },
    });
    return response.data;
  }

  // Notifications API
  async registerDevice(deviceToken: string, platform: string) {
    const deviceId = await DeviceInfo.getUniqueId();
    const appVersion = DeviceInfo.getVersion();

    const response = await this.api.post('/notifications/register', {
      device_id: deviceId,
      platform,
      fcm_token: deviceToken,
      app_version: appVersion,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    });
    return response.data;
  }

  async updateNotificationPreferences(preferences: Record<string, boolean>) {
    const response = await this.api.put('/notifications/preferences', preferences);
    return response.data;
  }

  // File upload API
  async uploadFile(uri: string, type: 'image' | 'document', entityType: string, entityId: string) {
    const formData = new FormData();
    formData.append('file', {
      uri,
      type: type === 'image' ? 'image/jpeg' : 'application/octet-stream',
      name: `${entityType}_${entityId}_${Date.now()}.${type === 'image' ? 'jpg' : 'pdf'}`,
    } as any);

    formData.append('entity_type', entityType);
    formData.append('entity_id', entityId);

    const response = await this.api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 1 minute for file uploads
    });

    return response.data;
  }

  // Search API
  async searchEntities(query: string, entityTypes: string[] = ['leads', 'properties']) {
    const response = await this.api.get('/search', {
      params: {
        q: query,
        types: entityTypes.join(','),
      },
    });
    return response.data;
  }

  // Voice API
  async submitVoiceNote(audioUri: string, leadId: string, transcript?: string) {
    const formData = new FormData();
    formData.append('audio', {
      uri: audioUri,
      type: 'audio/wav',
      name: `voice_note_${leadId}_${Date.now()}.wav`,
    } as any);

    formData.append('lead_id', leadId);
    if (transcript) {
      formData.append('transcript', transcript);
    }

    const response = await this.api.post('/voice/note', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  // Offline support
  async getOfflineData() {
    try {
      const [dashboardData, recentLeads, favoriteProperties] = await Promise.all([
        this.getDashboard(),
        this.getNearbyLeads({latitude: 0, longitude: 0, radius_miles: 50}, 1, 50),
        // Add more offline data requests
      ]);

      return {
        dashboard: dashboardData,
        leads: recentLeads,
        properties: favoriteProperties,
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      console.error('Failed to fetch offline data:', error);
      throw error;
    }
  }

  // Health check
  async healthCheck() {
    try {
      const response = await this.api.get('/health');
      return response.data;
    } catch (error) {
      return { status: 'error', error: error.message };
    }
  }

  // Configuration
  updateConfig(newConfig: Partial<ApiConfig>) {
    this.config = { ...this.config, ...newConfig };
    this.api.defaults.baseURL = this.config.baseURL;
    this.api.defaults.timeout = this.config.timeout;
  }
}

export const ApiService = new ApiServiceClass();