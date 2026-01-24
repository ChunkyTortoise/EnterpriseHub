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

// Background Sync - handle offline operations
self.addEventListener('sync', (event) => {
  console.log('🔄 Jorge SW: Background sync triggered:', event.tag);

  if (event.tag === 'jorge-offline-sync') {
    event.waitUntil(syncOfflineOperations());
  } else if (event.tag === 'jorge-property-sync') {
    event.waitUntil(syncPropertyData());
  } else if (event.tag === 'jorge-conversation-sync') {
    event.waitUntil(syncConversations());
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

// Message handling from client
self.addEventListener('message', (event) => {
  console.log('💬 Jorge SW: Message received:', event.data);

  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (event.data?.type === 'TRIGGER_SYNC') {
    // Manually trigger background sync
    self.registration.sync.register('jorge-offline-sync');
  } else if (event.data?.type === 'CLEAR_CACHE') {
    clearAllCaches().then(() => {
      event.ports[0]?.postMessage({ success: true });
    });
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