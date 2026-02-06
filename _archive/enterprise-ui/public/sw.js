/**
 * Jorge Real Estate AI Platform - Service Worker
 * Background sync, caching, and offline capabilities
 *
 * Features:
 * - Background sync for offline operations
 * - Intelligent caching strategy
 * - Push notification handling
 * - Auto-update management
 * - Jorge-specific optimizations
 */

const CACHE_NAME = 'jorge-real-estate-v1';
const DYNAMIC_CACHE = 'jorge-dynamic-v1';
const API_CACHE = 'jorge-api-v1';

// Jorge-specific cache patterns
const STATIC_ASSETS = [
  '/',
  '/jorge',
  '/field-agent',
  '/manifest.json',
  '/offline.html',
  // Core JavaScript and CSS will be added by Next.js
];

const API_PATTERNS = [
  /\/api\/properties/,
  /\/api\/conversations/,
  /\/api\/voice-notes/,
  /\/api\/user\/preferences/
];

const JORGE_API_BASE = process.env.NEXT_PUBLIC_JORGE_API_URL || 'http://localhost:8000';

// Cache strategies
const CACHE_STRATEGIES = {
  CACHE_FIRST: 'cache-first',
  NETWORK_FIRST: 'network-first',
  STALE_WHILE_REVALIDATE: 'stale-while-revalidate',
  NETWORK_ONLY: 'network-only',
  CACHE_ONLY: 'cache-only'
};

// ==============================================================================
// ENHANCED ML-POWERED SERVICE WORKER CAPABILITIES
// ==============================================================================

// ML Model cache
const ML_CACHE = 'jorge-ml-models-v1';
const ML_PREDICTIONS_CACHE = 'jorge-ml-predictions-v1';

// ML-specific patterns
const ML_MODEL_PATTERNS = [
  /\/models\/.*\.json$/,
  /\/models\/.*\.bin$/
];

// Background ML processing queue
let mlProcessingQueue = [];
let isMLProcessing = false;

// Network and battery awareness
let networkQuality = 'good';
let batteryLevel = 1.0;
let isCharging = false;

// Predictive caching state
let userLocationHistory = [];
let propertyAccessPatterns = new Map();
let lastPredictiveCacheUpdate = 0;

// ML Model loading state
let loadedMLModels = new Map();

// Enhanced ML utilities for service worker
const MLServiceWorkerUtils = {
  /**
   * Load TensorFlow.js in service worker context
   */
  async initializeTensorFlow() {
    try {
      // Import TensorFlow.js - for service worker we need to use importScripts
      // This is a simplified version - in production you'd load from CDN
      console.log('🧠 Jorge SW: Initializing TensorFlow.js...');

      // For now, we'll simulate ML capabilities
      // In production, you'd use: importScripts('https://cdn.jsdelivr.net/npm/@tensorflow/tfjs');
      return true;
    } catch (error) {
      console.error('Jorge SW: TensorFlow initialization failed:', error);
      return false;
    }
  },

  /**
   * Lightweight property scoring without full TensorFlow (for service worker)
   */
  scorePropertySimple(propertyData, userPreferences) {
    // Simplified scoring algorithm for service worker
    let score = 0;
    let factors = 0;

    // Price match (30% weight)
    if (propertyData.price && userPreferences.maxBudget) {
      const priceRatio = propertyData.price / userPreferences.maxBudget;
      if (priceRatio <= 1) {
        score += (1 - priceRatio) * 30;
      }
      factors++;
    }

    // Location preference (25% weight)
    if (propertyData.location && userPreferences.preferredAreas) {
      const locationMatch = userPreferences.preferredAreas.includes(propertyData.location);
      score += locationMatch ? 25 : 0;
      factors++;
    }

    // Size preference (20% weight)
    if (propertyData.sqft && userPreferences.minSqft) {
      const sizeMatch = propertyData.sqft >= userPreferences.minSqft;
      score += sizeMatch ? 20 : 0;
      factors++;
    }

    // Bedroom count (15% weight)
    if (propertyData.bedrooms && userPreferences.bedrooms) {
      const bedroomMatch = propertyData.bedrooms >= userPreferences.bedrooms;
      score += bedroomMatch ? 15 : 0;
      factors++;
    }

    // Days on market (10% weight) - fresher listings score higher
    if (propertyData.daysOnMarket !== undefined) {
      const freshness = Math.max(0, 1 - (propertyData.daysOnMarket / 365));
      score += freshness * 10;
      factors++;
    }

    return factors > 0 ? Math.min(100, score / factors * (factors / 5)) : 50;
  },

  /**
   * Determine if property should be prefetched
   */
  shouldPrefetchProperty(propertyData, userContext) {
    const score = this.scorePropertySimple(propertyData, userContext.preferences || {});
    const isInUserArea = this.isInUserArea(propertyData.location, userContext.currentLocation);
    const isRecentlyViewed = this.isRecentPattern(propertyData.id, 'property_view');

    return score > 60 || isInUserArea || isRecentlyViewed;
  },

  /**
   * Check if location is in user's area of interest
   */
  isInUserArea(propertyLocation, userLocation, radiusKm = 10) {
    if (!propertyLocation || !userLocation) return false;

    // Simple distance calculation (simplified for service worker)
    // In production, use proper geospatial calculations
    const lat1 = propertyLocation.lat || 0;
    const lng1 = propertyLocation.lng || 0;
    const lat2 = userLocation.lat || 0;
    const lng2 = userLocation.lng || 0;

    const distance = Math.sqrt(
      Math.pow(lat2 - lat1, 2) + Math.pow(lng2 - lng1, 2)
    ) * 111; // Rough km conversion

    return distance <= radiusKm;
  },

  /**
   * Check if ID matches recent access patterns
   */
  isRecentPattern(id, patternType) {
    const pattern = propertyAccessPatterns.get(patternType);
    if (!pattern) return false;

    const now = Date.now();
    const recentAccesses = pattern.filter(access =>
      now - access.timestamp < 24 * 60 * 60 * 1000 // Last 24 hours
    );

    return recentAccesses.some(access => access.id === id);
  },

  /**
   * Predict user's next likely actions
   */
  predictUserActions(userContext) {
    const predictions = [];
    const currentHour = new Date().getHours();

    // Time-based predictions
    if (currentHour >= 9 && currentHour <= 17) {
      predictions.push({
        action: 'property_search',
        probability: 0.7,
        reason: 'Business hours - likely to search properties'
      });
    }

    if (currentHour >= 18 && currentHour <= 21) {
      predictions.push({
        action: 'lead_followup',
        probability: 0.8,
        reason: 'Evening - peak time for client follow-ups'
      });
    }

    // Location-based predictions
    if (userContext.currentLocation) {
      predictions.push({
        action: 'nearby_properties',
        probability: 0.6,
        reason: 'User location available - may want nearby listings'
      });
    }

    // Pattern-based predictions
    const recentSearches = propertyAccessPatterns.get('property_search') || [];
    if (recentSearches.length > 0) {
      predictions.push({
        action: 'similar_properties',
        probability: 0.5,
        reason: 'Recent search activity - may want similar properties'
      });
    }

    return predictions.sort((a, b) => b.probability - a.probability);
  }
};

// Background ML processing functions
async function processMLQueue() {
  if (isMLProcessing || mlProcessingQueue.length === 0) return;

  isMLProcessing = true;
  console.log(`🧠 Jorge SW: Processing ML queue (${mlProcessingQueue.length} items)`);

  try {
    while (mlProcessingQueue.length > 0) {
      const task = mlProcessingQueue.shift();
      await processMLTask(task);

      // Yield control periodically to prevent blocking
      if (mlProcessingQueue.length % 5 === 0) {
        await new Promise(resolve => setTimeout(resolve, 10));
      }
    }
  } catch (error) {
    console.error('Jorge SW: ML processing failed:', error);
  } finally {
    isMLProcessing = false;
  }
}

async function processMLTask(task) {
  const { type, data, clientId } = task;

  try {
    let result = null;

    switch (type) {
      case 'score_property':
        result = MLServiceWorkerUtils.scorePropertySimple(data.property, data.userPreferences);
        break;

      case 'analyze_patterns':
        result = await analyzeUserPatterns(data.userId);
        break;

      case 'prefetch_predictions':
        result = await generatePrefetchPredictions(data.userContext);
        break;

      case 'cache_optimization':
        result = await optimizeCache(data.constraints);
        break;

      default:
        console.warn(`Unknown ML task type: ${type}`);
        return;
    }

    // Send result back to client
    const client = await self.clients.get(clientId);
    if (client) {
      client.postMessage({
        type: 'ML_RESULT',
        taskType: type,
        result: result,
        timestamp: Date.now()
      });
    }

    // Cache result for future use
    await cacheMLResult(type, data, result);

  } catch (error) {
    console.error(`Jorge SW: ML task ${type} failed:`, error);
  }
}

async function analyzeUserPatterns(userId) {
  // Analyze user behavior patterns for predictive insights
  const patterns = {
    searchFrequency: calculateSearchFrequency(),
    preferredTimeSlots: calculatePreferredTimes(),
    locationPatterns: calculateLocationPatterns(),
    propertyPreferences: calculatePropertyPreferences()
  };

  return {
    userId,
    patterns,
    lastAnalysis: Date.now(),
    recommendations: generatePatternRecommendations(patterns)
  };
}

async function generatePrefetchPredictions(userContext) {
  const predictions = MLServiceWorkerUtils.predictUserActions(userContext);

  // Generate specific prefetch recommendations
  const prefetchTargets = [];

  for (const prediction of predictions.slice(0, 3)) { // Top 3 predictions
    switch (prediction.action) {
      case 'property_search':
        prefetchTargets.push({
          type: 'api',
          url: '/api/properties/search',
          priority: prediction.probability,
          reason: prediction.reason
        });
        break;

      case 'nearby_properties':
        if (userContext.currentLocation) {
          prefetchTargets.push({
            type: 'api',
            url: `/api/properties/nearby?lat=${userContext.currentLocation.lat}&lng=${userContext.currentLocation.lng}`,
            priority: prediction.probability,
            reason: prediction.reason
          });
        }
        break;

      case 'lead_followup':
        prefetchTargets.push({
          type: 'api',
          url: '/api/conversations/active',
          priority: prediction.probability,
          reason: prediction.reason
        });
        break;
    }
  }

  return {
    predictions,
    prefetchTargets,
    generatedAt: Date.now()
  };
}

async function optimizeCache(constraints = {}) {
  const { batteryLevel = 1.0, networkQuality = 'good', storageUsed = 0 } = constraints;

  const optimization = {
    shouldClearOldData: storageUsed > 0.8,
    shouldReduceCaching: batteryLevel < 0.2 || networkQuality === 'poor',
    shouldPrefetch: batteryLevel > 0.5 && networkQuality === 'good',
    recommendedCacheSize: calculateOptimalCacheSize(batteryLevel, networkQuality),
    actionsRequired: []
  };

  if (optimization.shouldClearOldData) {
    optimization.actionsRequired.push('clear_old_cache');
  }

  if (optimization.shouldReduceCaching) {
    optimization.actionsRequired.push('reduce_caching');
  }

  if (optimization.shouldPrefetch) {
    optimization.actionsRequired.push('enable_prefetch');
  }

  return optimization;
}

function calculateSearchFrequency() {
  // Implement search frequency calculation
  return { daily: 5, weekly: 25, pattern: 'regular' };
}

function calculatePreferredTimes() {
  // Calculate when user is most active
  return { peak: [9, 17], secondary: [18, 21] };
}

function calculateLocationPatterns() {
  // Analyze location access patterns
  return { radius: 15, centers: [], frequency: 'moderate' };
}

function calculatePropertyPreferences() {
  // Extract property preference patterns
  return { priceRange: [200000, 500000], types: ['house'], features: [] };
}

function generatePatternRecommendations(patterns) {
  return [
    'Prefetch properties during peak hours',
    'Cache popular property types',
    'Optimize for mobile usage patterns'
  ];
}

function calculateOptimalCacheSize(batteryLevel, networkQuality) {
  let baseSize = 50; // MB

  if (batteryLevel < 0.3) baseSize *= 0.6;
  if (networkQuality === 'poor') baseSize *= 0.5;
  if (networkQuality === 'excellent') baseSize *= 1.5;

  return Math.max(10, Math.min(200, baseSize));
}

async function cacheMLResult(taskType, inputData, result) {
  try {
    const cache = await caches.open(ML_PREDICTIONS_CACHE);
    const cacheKey = `ml-${taskType}-${hashObject(inputData)}`;

    const cacheData = {
      result,
      timestamp: Date.now(),
      ttl: 60 * 60 * 1000 // 1 hour
    };

    await cache.put(cacheKey, new Response(JSON.stringify(cacheData)));
  } catch (error) {
    console.error('Jorge SW: Failed to cache ML result:', error);
  }
}

function hashObject(obj) {
  // Simple hash function for cache keys
  return btoa(JSON.stringify(obj)).replace(/[^a-zA-Z0-9]/g, '').substr(0, 16);
}

// Enhanced background sync with ML processing
async function performIntelligentSync() {
  console.log('🔄 Jorge SW: Starting intelligent sync...');

  try {
    // 1. Sync offline operations
    await syncOfflineOperations();

    // 2. Process ML queue
    await processMLQueue();

    // 3. Perform predictive caching if conditions are right
    if (batteryLevel > 0.5 && networkQuality !== 'poor') {
      await performPredictiveCaching();
    }

    // 4. Optimize cache based on current conditions
    const optimization = await optimizeCache({
      batteryLevel,
      networkQuality,
      storageUsed: await getStorageUsage()
    });

    await applyOptimizations(optimization);

    console.log('✅ Jorge SW: Intelligent sync complete');

  } catch (error) {
    console.error('Jorge SW: Intelligent sync failed:', error);
  }
}

async function performPredictiveCaching() {
  // Get user context for predictions
  const userContext = await getUserContext();
  if (!userContext) return;

  const predictions = await generatePrefetchPredictions(userContext);

  for (const target of predictions.prefetchTargets) {
    if (target.priority > 0.6) { // Only high-probability predictions
      try {
        await prefetchResource(target);
      } catch (error) {
        console.warn(`Jorge SW: Failed to prefetch ${target.url}:`, error);
      }
    }
  }
}

async function prefetchResource(target) {
  const cache = await caches.open(API_CACHE);

  try {
    const response = await fetch(target.url);
    if (response.ok) {
      await cache.put(target.url, response);
      console.log(`📦 Jorge SW: Prefetched ${target.url} (${target.reason})`);
    }
  } catch (error) {
    // Silent fail for prefetch operations
  }
}

async function getUserContext() {
  // Get user context from IndexedDB or other storage
  // This would integrate with the offline storage system
  try {
    // Placeholder - would integrate with OfflineStorage
    return {
      currentLocation: null,
      preferences: {},
      recentActivity: []
    };
  } catch (error) {
    return null;
  }
}

async function getStorageUsage() {
  if ('storage' in navigator && 'estimate' in navigator.storage) {
    const estimate = await navigator.storage.estimate();
    return estimate.usage && estimate.quota
      ? estimate.usage / estimate.quota
      : 0;
  }
  return 0;
}

async function applyOptimizations(optimization) {
  for (const action of optimization.actionsRequired) {
    switch (action) {
      case 'clear_old_cache':
        await clearOldCacheData();
        break;
      case 'reduce_caching':
        // Reduce caching aggressiveness
        break;
      case 'enable_prefetch':
        // Enable prefetching
        break;
    }
  }
}

async function clearOldCacheData() {
  const cacheNames = await caches.keys();
  for (const cacheName of cacheNames) {
    if (cacheName.includes('-v') && !cacheName.includes(CACHE_NAME)) {
      await caches.delete(cacheName);
    }
  }
}

// Install event - precache static assets
self.addEventListener('install', (event) => {
  console.log('🏢 Jorge SW: Installing service worker');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('🏢 Jorge SW: Precaching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        // Skip waiting to activate immediately
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Jorge SW: Install failed:', error);
      })
  );
});

// Activate event - cleanup old caches
self.addEventListener('activate', (event) => {
  console.log('🏢 Jorge SW: Activating service worker');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME &&
                cacheName !== DYNAMIC_CACHE &&
                cacheName !== API_CACHE) {
              console.log('🧹 Jorge SW: Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        // Take control of all clients immediately
        return self.clients.claim();
      })
  );
});

// Fetch event - intelligent caching strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests and chrome-extension requests
  if (request.method !== 'GET' || url.protocol === 'chrome-extension:') {
    return;
  }

  // API requests - use network-first strategy
  if (isApiRequest(request)) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Static assets - use cache-first strategy
  if (isStaticAsset(request)) {
    event.respondWith(handleStaticRequest(request));
    return;
  }

  // Dynamic content - use stale-while-revalidate
  event.respondWith(handleDynamicRequest(request));
});

// Enhanced Background Sync - handle offline operations and ML processing
self.addEventListener('sync', (event) => {
  console.log('🔄 Jorge SW: Background sync triggered:', event.tag);

  if (event.tag === 'jorge-offline-sync') {
    event.waitUntil(syncOfflineOperations());
  } else if (event.tag === 'jorge-property-sync') {
    event.waitUntil(syncPropertyData());
  } else if (event.tag === 'jorge-conversation-sync') {
    event.waitUntil(syncConversations());
  } else if (event.tag === 'jorge-intelligent-sync') {
    event.waitUntil(performIntelligentSync());
  } else if (event.tag === 'jorge-ml-processing') {
    event.waitUntil(processMLQueue());
  } else if (event.tag === 'jorge-predictive-cache') {
    event.waitUntil(performPredictiveCaching());
  }
});

// Push notifications - Jorge bot updates
self.addEventListener('push', (event) => {
  console.log('📱 Jorge SW: Push notification received');

  if (!event.data) return;

  try {
    const data = event.data.json();
    const { title, body, icon, badge, tag, data: notificationData } = data;

    const options = {
      body,
      icon: icon || '/icons/jorge-192.png',
      badge: badge || '/icons/jorge-badge.png',
      tag: tag || 'jorge-notification',
      data: notificationData,
      requireInteraction: notificationData?.priority === 'HIGH',
      actions: [
        {
          action: 'view',
          title: 'View Details',
          icon: '/icons/view.png'
        },
        {
          action: 'dismiss',
          title: 'Dismiss',
          icon: '/icons/dismiss.png'
        }
      ]
    };

    event.waitUntil(
      self.registration.showNotification(title, options)
    );
  } catch (error) {
    console.error('Jorge SW: Push notification error:', error);
  }
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  console.log('🔔 Jorge SW: Notification clicked:', event.action);

  event.notification.close();

  if (event.action === 'view') {
    const urlToOpen = event.notification.data?.url || '/jorge';

    event.waitUntil(
      clients.matchAll({ type: 'window' }).then((clientList) => {
        // If Jorge is already open, focus it
        for (const client of clientList) {
          if (client.url.includes('/jorge') && 'focus' in client) {
            return client.focus();
          }
        }

        // Otherwise open a new window
        if (clients.openWindow) {
          return clients.openWindow(urlToOpen);
        }
      })
    );
  }
});

// Enhanced Message handling from client
self.addEventListener('message', (event) => {
  console.log('💬 Jorge SW: Message received:', event.data);

  const { type, data } = event.data || {};

  if (type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (type === 'TRIGGER_SYNC') {
    // Manually trigger background sync
    self.registration.sync.register('jorge-offline-sync');
  } else if (type === 'CLEAR_CACHE') {
    clearAllCaches().then(() => {
      event.ports[0]?.postMessage({ success: true });
    });
  }
  // ML-specific message handlers
  else if (type === 'QUEUE_ML_TASK') {
    // Add ML task to processing queue
    const task = {
      ...data,
      clientId: event.source?.id,
      timestamp: Date.now()
    };
    mlProcessingQueue.push(task);

    // Trigger ML processing
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      self.registration.sync.register('jorge-ml-processing');
    } else {
      // Immediate processing if background sync not available
      processMLQueue();
    }

    event.ports[0]?.postMessage({ queued: true, position: mlProcessingQueue.length });
  }
  else if (type === 'UPDATE_NETWORK_STATE') {
    // Update network awareness
    networkQuality = data.quality || 'good';
    console.log(`🌐 Jorge SW: Network quality updated to ${networkQuality}`);

    // Trigger optimization if network improved significantly
    if (networkQuality === 'excellent' && batteryLevel > 0.7) {
      setTimeout(() => {
        self.registration.sync.register('jorge-predictive-cache');
      }, 5000);
    }
  }
  else if (type === 'UPDATE_BATTERY_STATE') {
    // Update battery awareness
    batteryLevel = data.level || 1.0;
    isCharging = data.isCharging || false;
    console.log(`🔋 Jorge SW: Battery updated to ${Math.round(batteryLevel * 100)}%`);

    // Trigger cache optimization for low battery
    if (batteryLevel < 0.2 && !isCharging) {
      optimizeCache({ batteryLevel, networkQuality }).then(applyOptimizations);
    }
  }
  else if (type === 'UPDATE_LOCATION') {
    // Track user location for predictive caching
    if (data.location) {
      userLocationHistory.push({
        ...data.location,
        timestamp: Date.now()
      });

      // Keep only last 24 hours
      const dayAgo = Date.now() - 24 * 60 * 60 * 1000;
      userLocationHistory = userLocationHistory.filter(loc => loc.timestamp > dayAgo);

      // Trigger predictive caching for new area
      if (batteryLevel > 0.5 && networkQuality !== 'poor') {
        setTimeout(() => {
          self.registration.sync.register('jorge-predictive-cache');
        }, 10000);
      }
    }
  }
  else if (type === 'TRACK_PATTERN') {
    // Track user access patterns for ML
    const { patternType, itemId, metadata } = data;
    if (!propertyAccessPatterns.has(patternType)) {
      propertyAccessPatterns.set(patternType, []);
    }

    const patterns = propertyAccessPatterns.get(patternType);
    patterns.push({
      id: itemId,
      timestamp: Date.now(),
      metadata: metadata || {}
    });

    // Keep only last 100 entries per pattern type
    if (patterns.length > 100) {
      patterns.splice(0, patterns.length - 100);
    }
  }
  else if (type === 'GET_ML_STATUS') {
    // Return ML processing status
    const status = {
      queueLength: mlProcessingQueue.length,
      isProcessing: isMLProcessing,
      loadedModels: Array.from(loadedMLModels.keys()),
      networkQuality,
      batteryLevel,
      lastCacheUpdate: lastPredictiveCacheUpdate
    };

    event.ports[0]?.postMessage({ type: 'ML_STATUS', status });
  }
  else if (type === 'TRIGGER_INTELLIGENT_SYNC') {
    // Manually trigger intelligent sync
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      self.registration.sync.register('jorge-intelligent-sync');
    } else {
      performIntelligentSync();
    }
  }
});

// Helper Functions

function isApiRequest(request) {
  const url = new URL(request.url);
  return url.pathname.startsWith('/api/') ||
         url.origin === JORGE_API_BASE ||
         API_PATTERNS.some(pattern => pattern.test(url.pathname));
}

function isStaticAsset(request) {
  const url = new URL(request.url);
  return url.pathname.match(/\.(js|css|png|jpg|jpeg|svg|ico|woff|woff2)$/) ||
         STATIC_ASSETS.includes(url.pathname);
}

async function handleApiRequest(request) {
  const cacheKey = getCacheKey(request);

  try {
    // Try network first
    const networkResponse = await fetch(request.clone());

    if (networkResponse.ok) {
      // Cache successful responses
      const cache = await caches.open(API_CACHE);
      cache.put(cacheKey, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('🌐 Jorge SW: Network failed, trying cache:', request.url);

    // Fallback to cache
    const cache = await caches.open(API_CACHE);
    const cachedResponse = await cache.match(cacheKey);

    if (cachedResponse) {
      return cachedResponse;
    }

    // If no cache available, return offline response
    return new Response(
      JSON.stringify({
        error: 'Offline',
        message: 'Jorge is working offline. Data will sync when connection is restored.'
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

async function handleStaticRequest(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);

  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('🌐 Jorge SW: Static asset failed:', request.url);

    // Fallback to offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/offline.html');
    }

    return new Response('Offline', { status: 503 });
  }
}

async function handleDynamicRequest(request) {
  const cache = await caches.open(DYNAMIC_CACHE);
  const cachedResponse = await cache.match(request);

  // Return cached response immediately if available
  if (cachedResponse) {
    // Update cache in background
    fetch(request).then((networkResponse) => {
      if (networkResponse.ok) {
        cache.put(request, networkResponse.clone());
      }
    }).catch(() => {
      // Silent fail for background updates
    });

    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('🌐 Jorge SW: Dynamic request failed:', request.url);

    if (request.mode === 'navigate') {
      return caches.match('/offline.html');
    }

    return new Response('Offline', { status: 503 });
  }
}

function getCacheKey(request) {
  const url = new URL(request.url);
  // Remove timestamp and other cache-busting params for API requests
  url.searchParams.delete('_t');
  url.searchParams.delete('timestamp');
  return url.toString();
}

// Background Sync Operations
async function syncOfflineOperations() {
  console.log('🔄 Jorge SW: Syncing offline operations');

  try {
    // Get pending operations from IndexedDB
    const operations = await getOfflineOperations();

    for (const operation of operations) {
      try {
        await syncSingleOperation(operation);
        await markOperationComplete(operation.id);
        console.log(`✅ Jorge SW: Synced operation ${operation.id}`);
      } catch (error) {
        console.error(`❌ Jorge SW: Failed to sync operation ${operation.id}:`, error);
        await incrementRetryCount(operation.id);
      }
    }

    // Notify clients of sync completion
    const clients = await self.clients.matchAll();
    clients.forEach(client => {
      client.postMessage({
        type: 'SYNC_COMPLETE',
        timestamp: Date.now()
      });
    });

  } catch (error) {
    console.error('Jorge SW: Background sync failed:', error);
  }
}

async function syncPropertyData() {
  console.log('🏠 Jorge SW: Syncing property data');
  // Implementation would sync cached property data
}

async function syncConversations() {
  console.log('💬 Jorge SW: Syncing conversations');
  // Implementation would sync bot conversations
}

async function syncSingleOperation(operation) {
  const { type, storeName, data, recordId } = operation;

  let url = `${JORGE_API_BASE}/api/`;
  let method = 'POST';
  let body = null;

  switch (storeName) {
    case 'cachedProperties':
      url += 'properties';
      break;
    case 'botConversations':
      url += 'conversations';
      break;
    case 'leadNotes':
      url += 'voice-notes';
      break;
    default:
      throw new Error(`Unknown store: ${storeName}`);
  }

  if (type === 'UPDATE' || type === 'DELETE') {
    url += `/${recordId}`;
    method = type === 'UPDATE' ? 'PUT' : 'DELETE';
  }

  if (data && (type === 'CREATE' || type === 'UPDATE')) {
    body = JSON.stringify(data);
  }

  const response = await fetch(url, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-Sync-Source': 'service-worker'
    },
    body
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

// IndexedDB helpers (simplified - full implementation would use the OfflineStorage class)
async function getOfflineOperations() {
  // This would interface with the IndexedDB to get pending operations
  // For now, return empty array
  return [];
}

async function markOperationComplete(operationId) {
  // Mark operation as complete in IndexedDB
}

async function incrementRetryCount(operationId) {
  // Increment retry count for failed operation
}

async function clearAllCaches() {
  const cacheNames = await caches.keys();
  await Promise.all(cacheNames.map(name => caches.delete(name)));
  console.log('🧹 Jorge SW: All caches cleared');
}