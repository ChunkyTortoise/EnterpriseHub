// Jorge's Real Estate AI Platform - Mobile Excellence Service Worker
// Advanced offline capabilities with intelligent sync and push notifications

import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching'
import { registerRoute, NavigationRoute } from 'workbox-routing'
import { NetworkFirst, CacheFirst, StaleWhileRevalidate } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'
import { BackgroundSync } from 'workbox-background-sync'
import { Queue } from 'workbox-background-sync'

// Precache all static assets
precacheAndRoute(self.__WB_MANIFEST)
cleanupOutdatedCaches()

// Background sync queues for offline actions
const propertyAnalysisQueue = new Queue('property-analysis-queue', {
  onSync: async ({ queue }) => {
    console.log('Syncing property analysis queue')
    let entry
    while ((entry = await queue.shiftRequest())) {
      try {
        await fetch(entry.request)
        console.log('Property analysis synced:', entry.request.url)
      } catch (error) {
        console.error('Property analysis sync failed:', error)
        await queue.unshiftRequest(entry)
        throw error
      }
    }
  }
})

const leadCaptureQueue = new Queue('lead-capture-queue', {
  onSync: async ({ queue }) => {
    console.log('Syncing lead capture queue')
    let entry
    while ((entry = await queue.shiftRequest())) {
      try {
        await fetch(entry.request)
        console.log('Lead data synced:', entry.request.url)
      } catch (error) {
        console.error('Lead sync failed:', error)
        await queue.unshiftRequest(entry)
        throw error
      }
    }
  }
})

// Property data caching with intelligent invalidation
registerRoute(
  ({ request }) => request.url.includes('/api/properties'),
  new NetworkFirst({
    cacheName: 'jorge-property-data',
    networkTimeoutSeconds: 3,
    plugins: [
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 24 * 60 * 60, // 24 hours
        purgeOnQuotaError: true,
      }),
      {
        // Add location-based cache invalidation
        cacheKeyWillBeUsed: async ({ request, mode }) => {
          const url = new URL(request.url)
          const params = new URLSearchParams(url.search)

          // Include location in cache key for location-specific data
          const lat = params.get('lat')
          const lng = params.get('lng')
          const locationKey = lat && lng ? `_${lat}_${lng}` : ''

          return `${url.pathname}${locationKey}${url.search}`
        }
      }
    ],
  })
)

// Lead scoring and ML analytics caching
registerRoute(
  ({ request }) => request.url.includes('/api/ml') || request.url.includes('/api/leads'),
  new NetworkFirst({
    cacheName: 'jorge-intelligence-cache',
    networkTimeoutSeconds: 5,
    plugins: [
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 2 * 60 * 60, // 2 hours
      }),
    ],
  })
)

// ========================================================================
// Week 5-8 ROI Enhancement API Caching
// ========================================================================

// Market intelligence + commission forecast — field agents need this offline
registerRoute(
  ({ request }) =>
    request.url.includes('/api/v1/rc-market') ||
    request.url.includes('/api/v1/commission-forecast'),
  new NetworkFirst({
    cacheName: 'jorge-market-intelligence',
    networkTimeoutSeconds: 5,
    plugins: [
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 4 * 60 * 60, // 4 hours
        purgeOnQuotaError: true,
      }),
    ],
  })
)

// Propensity scoring + SHAP explanations — cache for offline lead review
registerRoute(
  ({ request }) =>
    request.url.includes('/api/v1/propensity') &&
    request.method === 'GET',
  new NetworkFirst({
    cacheName: 'jorge-propensity-cache',
    networkTimeoutSeconds: 5,
    plugins: [
      new ExpirationPlugin({
        maxEntries: 200,
        maxAgeSeconds: 2 * 60 * 60, // 2 hours
      }),
    ],
  })
)

// Sentiment + behavioral analysis — read-heavy, cache aggressively
registerRoute(
  ({ request }) =>
    (request.url.includes('/api/v1/sentiment') ||
     request.url.includes('/api/v1/behavioral')) &&
    request.method === 'GET',
  new NetworkFirst({
    cacheName: 'jorge-sentiment-behavioral',
    networkTimeoutSeconds: 3,
    plugins: [
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 1 * 60 * 60, // 1 hour
      }),
    ],
  })
)

// Export engine — cache generated reports for offline viewing
registerRoute(
  ({ request }) => request.url.includes('/api/v1/exports'),
  new NetworkFirst({
    cacheName: 'jorge-export-reports',
    networkTimeoutSeconds: 10,
    plugins: [
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 24 * 60 * 60, // 24 hours
      }),
    ],
  })
)

// Background sync queue for Week 5-8 POST operations
const fieldOpsQueue = new Queue('field-ops-queue', {
  onSync: async ({ queue }) => {
    console.log('Syncing field operations queue')
    let entry
    while ((entry = await queue.shiftRequest())) {
      try {
        await fetch(entry.request)
        console.log('Field operation synced:', entry.request.url)
      } catch (error) {
        console.error('Field operation sync failed:', error)
        await queue.unshiftRequest(entry)
        throw error
      }
    }
  }
})

// Queue Week 5-8 POST requests when offline
registerRoute(
  ({ request }) =>
    request.method === 'POST' &&
    (request.url.includes('/api/v1/propensity/score') ||
     request.url.includes('/api/v1/propensity/explain') ||
     request.url.includes('/api/v1/sentiment/analyze') ||
     request.url.includes('/api/v1/behavioral/analyze') ||
     request.url.includes('/api/v1/compliance-enforcement/enforce') ||
     request.url.includes('/api/v1/channels/send')),
  async ({ request }) => {
    try {
      const response = await fetch(request.clone())
      return response
    } catch (error) {
      console.log('Field ops request failed, queuing for background sync')
      await fieldOpsQueue.pushRequest({ request: request.clone() })

      return new Response(JSON.stringify({
        success: false,
        message: 'Request queued for sync when connection is restored',
        queued: true,
        offline: true,
        timestamp: Date.now()
      }), {
        status: 202,
        statusText: 'Queued for Background Sync',
        headers: { 'Content-Type': 'application/json' }
      })
    }
  }
)

// Bot conversation caching with background sync
registerRoute(
  ({ request }) => request.url.includes('/api/bots') && request.method === 'POST',
  async ({ request }) => {
    try {
      const response = await fetch(request)
      return response
    } catch (error) {
      console.log('Bot request failed, queuing for background sync')

      // Clone the request for background sync
      const clonedRequest = request.clone()

      // Queue for background sync based on bot type
      if (request.url.includes('jorge-seller')) {
        await propertyAnalysisQueue.pushRequest({ request: clonedRequest })
      } else {
        await leadCaptureQueue.pushRequest({ request: clonedRequest })
      }

      // Return cached response if available
      const cache = await caches.open('jorge-bot-responses')
      const cachedResponse = await cache.match(request)

      if (cachedResponse) {
        console.log('Returning cached bot response')
        return cachedResponse
      }

      // Return offline fallback response
      return new Response(JSON.stringify({
        success: false,
        message: 'Request queued for when connection is restored',
        queued: true,
        timestamp: Date.now()
      }), {
        status: 202,
        statusText: 'Queued for Background Sync',
        headers: { 'Content-Type': 'application/json' }
      })
    }
  }
)

// Property image analysis with vision API fallback
registerRoute(
  ({ request }) => request.url.includes('/api/vision') || request.url.includes('/analyze-property'),
  new NetworkFirst({
    cacheName: 'jorge-vision-cache',
    networkTimeoutSeconds: 10,
    plugins: [
      new ExpirationPlugin({
        maxEntries: 20,
        maxAgeSeconds: 4 * 60 * 60, // 4 hours
      }),
    ],
  })
)

// Static assets with long-term caching
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'jorge-images',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 200,
        maxAgeSeconds: 30 * 24 * 60 * 60, // 30 days
      }),
    ],
  })
)

// JavaScript and CSS with stale-while-revalidate
registerRoute(
  ({ request }) =>
    request.destination === 'script' ||
    request.destination === 'style' ||
    request.destination === 'font',
  new StaleWhileRevalidate({
    cacheName: 'jorge-static-assets',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 7 * 24 * 60 * 60, // 7 days
      }),
    ],
  })
)

// Navigation fallback for offline
const navigationRoute = new NavigationRoute(
  new NetworkFirst({
    cacheName: 'jorge-pages',
    networkTimeoutSeconds: 3,
    plugins: [
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 24 * 60 * 60, // 24 hours
      }),
    ],
  }),
  {
    // Only cache successful responses
    allowlist: [/^\/field-agent/, /^\/dashboard/, /^\/analytics/],
    denylist: [/^\/api/],
  }
)

registerRoute(navigationRoute)

// Push notification handling
self.addEventListener('push', (event) => {
  console.log('Push notification received:', event)

  if (!event.data) {
    console.log('Push event but no data')
    return
  }

  const data = event.data.json()
  console.log('Push notification data:', data)

  const options = {
    body: data.body || 'New notification from Jorge AI',
    icon: '/icons/icon-192.png',
    badge: '/icons/badge-72.png',
    tag: data.tag || 'jorge-notification',
    requireInteraction: data.priority === 'high',
    actions: data.actions || [
      {
        action: 'view',
        title: 'View Details',
        icon: '/icons/action-view.png'
      },
      {
        action: 'dismiss',
        title: 'Dismiss',
        icon: '/icons/action-dismiss.png'
      }
    ],
    data: {
      url: data.url || '/field-agent',
      timestamp: Date.now(),
      ...data.data
    }
  }

  // Custom notification logic based on type
  let title = data.title || 'Jorge AI Platform'

  switch (data.type) {
    case 'hot_lead':
      title = '🔥 Hot Lead Alert'
      options.body = `New hot lead: ${data.leadName || 'Lead'} - Temperature: ${data.temperature || 'High'}`
      options.requireInteraction = true
      options.tag = 'hot-lead'
      break

    case 'property_match':
      title = '🏠 Property Match Found'
      options.body = `Perfect match for ${data.clientName}: ${data.propertyAddress}`
      options.tag = 'property-match'
      break

    case 'bot_escalation':
      title = '🤖 Bot Escalation'
      options.body = `${data.botName} needs your attention for ${data.leadName}`
      options.tag = 'bot-escalation'
      options.requireInteraction = true
      break

    case 'system_alert':
      title = '⚠️ System Alert'
      options.body = data.body || 'System notification'
      options.tag = 'system-alert'
      break

    case 'market_alert':
      title = '📊 Market Alert'
      options.body = `${data.neighborhood}: ${data.alertMessage || 'Market condition change detected'}`
      options.tag = 'market-alert'
      break

    case 'compliance_block':
      title = '🛡️ Compliance Alert'
      options.body = `Message blocked: ${data.violationType || 'Compliance violation detected'}`
      options.tag = 'compliance-block'
      options.requireInteraction = true
      break

    case 'propensity_update':
      title = '🎯 Lead Score Update'
      options.body = `${data.leadName}: Score changed to ${data.temperature} (${data.probability}%)`
      options.tag = 'propensity-update'
      break
  }

  event.waitUntil(
    self.registration.showNotification(title, options)
  )
})

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  console.log('Notification clicked:', event)

  event.notification.close()

  const action = event.action
  const data = event.notification.data

  let targetUrl = data.url || '/field-agent'

  // Handle different actions
  if (action === 'view') {
    targetUrl = data.url || '/field-agent'
  } else if (action === 'dismiss') {
    console.log('Notification dismissed')
    return
  }

  // Add notification context to URL
  const url = new URL(targetUrl, self.location.origin)
  if (data.leadId) {
    url.searchParams.set('leadId', data.leadId)
  }
  if (data.propertyId) {
    url.searchParams.set('propertyId', data.propertyId)
  }
  if (data.notificationType) {
    url.searchParams.set('fromNotification', data.notificationType)
  }

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Check if there's already a window open
      for (const client of clientList) {
        if (client.url === url.href && 'focus' in client) {
          return client.focus()
        }
      }

      // Open new window if none found
      if (clients.openWindow) {
        return clients.openWindow(url.href)
      }
    })
  )
})

// Background sync event
self.addEventListener('sync', (event) => {
  console.log('Background sync triggered:', event.tag)

  if (event.tag === 'property-analysis-sync') {
    event.waitUntil(doPropertyAnalysisSync())
  } else if (event.tag === 'lead-capture-sync') {
    event.waitUntil(doLeadCaptureSync())
  } else if (event.tag === 'field-ops-sync') {
    event.waitUntil(doFieldOpsSync())
  }
})

// Sync functions
async function doPropertyAnalysisSync() {
  console.log('Performing property analysis background sync')

  try {
    // Get queued property analysis requests from IndexedDB
    const db = await openDB('jorge-offline-queue', 1)
    const tx = db.transaction('property-analysis', 'readwrite')
    const store = tx.objectStore('property-analysis')
    const requests = await store.getAll()

    for (const request of requests) {
      try {
        const response = await fetch(request.url, {
          method: request.method,
          headers: request.headers,
          body: request.body
        })

        if (response.ok) {
          console.log('Synced property analysis:', request.id)
          await store.delete(request.id)
        }
      } catch (error) {
        console.error('Failed to sync property analysis:', request.id, error)
      }
    }

    await tx.complete
  } catch (error) {
    console.error('Property analysis sync failed:', error)
  }
}

async function doLeadCaptureSync() {
  console.log('Performing lead capture background sync')

  try {
    const db = await openDB('jorge-offline-queue', 1)
    const tx = db.transaction('lead-capture', 'readwrite')
    const store = tx.objectStore('lead-capture')
    const requests = await store.getAll()

    for (const request of requests) {
      try {
        const response = await fetch(request.url, {
          method: request.method,
          headers: request.headers,
          body: request.body
        })

        if (response.ok) {
          console.log('Synced lead capture:', request.id)
          await store.delete(request.id)
        }
      } catch (error) {
        console.error('Failed to sync lead capture:', request.id, error)
      }
    }

    await tx.complete
  } catch (error) {
    console.error('Lead capture sync failed:', error)
  }
}

async function doFieldOpsSync() {
  console.log('Performing field operations background sync')

  try {
    const db = await openDB('jorge-offline-queue', 2)
    const tx = db.transaction('field-ops', 'readwrite')
    const store = tx.objectStore('field-ops')
    const requests = await store.getAll()

    for (const request of requests) {
      try {
        const response = await fetch(request.url, {
          method: request.method,
          headers: request.headers,
          body: request.body
        })

        if (response.ok) {
          console.log('Synced field operation:', request.id)
          await store.delete(request.id)
        }
      } catch (error) {
        console.error('Failed to sync field operation:', request.id, error)
      }
    }

    await tx.complete
  } catch (error) {
    console.error('Field operations sync failed:', error)
  }
}

// Simple IndexedDB helper
async function openDB(name, version) {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(name, version || 2)

    request.onerror = () => reject(request.error)
    request.onsuccess = () => resolve(request.result)

    request.onupgradeneeded = (event) => {
      const db = event.target.result

      if (!db.objectStoreNames.contains('property-analysis')) {
        db.createObjectStore('property-analysis', { keyPath: 'id', autoIncrement: true })
      }

      if (!db.objectStoreNames.contains('lead-capture')) {
        db.createObjectStore('lead-capture', { keyPath: 'id', autoIncrement: true })
      }

      // Week 5-8 field operations stores
      if (!db.objectStoreNames.contains('field-ops')) {
        db.createObjectStore('field-ops', { keyPath: 'id', autoIncrement: true })
      }

      if (!db.objectStoreNames.contains('market-snapshots')) {
        const store = db.createObjectStore('market-snapshots', { keyPath: 'neighborhood' })
        store.createIndex('timestamp', 'timestamp', { unique: false })
      }

      if (!db.objectStoreNames.contains('propensity-scores')) {
        const store = db.createObjectStore('propensity-scores', { keyPath: 'contact_id' })
        store.createIndex('temperature', 'temperature', { unique: false })
        store.createIndex('timestamp', 'timestamp', { unique: false })
      }

      if (!db.objectStoreNames.contains('compliance-results')) {
        const store = db.createObjectStore('compliance-results', { keyPath: 'id', autoIncrement: true })
        store.createIndex('contact_id', 'contact_id', { unique: false })
        store.createIndex('status', 'status', { unique: false })
      }
    }
  })
}

// Skip waiting to activate immediately
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
})

console.log('Jorge AI Service Worker loaded - Mobile Excellence Ready')