

const CACHE_NAME = 'e-materials-store-v1';
const STATIC_CACHE = 'static-v1';
const DYNAMIC_CACHE = 'dynamic-v1';

const urlsToCache = [
  '/',
  '/static/css/style.css',
  '/static/js/main.js',
  '/static/images/favicon.ico'
];

self.addEventListener('install', function(event) {
  console.log('Service Worker installing...');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(function(cache) {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
      .then(function() {
        console.log('Static resources cached');
        return self.skipWaiting();
      })
      .catch(function(error) {
        // Handle storage access blocked by tracking prevention
        console.warn('Cache storage access blocked or failed:', error);
        // Continue installation even if caching fails
        return self.skipWaiting();
      })
  );
});

self.addEventListener('activate', function(event) {
  console.log('Service Worker activating...');
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName).catch(function(error) {
              console.warn('Failed to delete cache:', cacheName, error);
            });
          }
        })
      );
    }).then(function() {
      console.log('Service Worker activated');
      return self.clients.claim();
    }).catch(function(error) {
      // Handle storage access blocked by tracking prevention
      console.warn('Cache storage access blocked during activation:', error);
      // Continue activation even if cache operations fail
      return self.clients.claim();
    })
  );
});

self.addEventListener('fetch', function(event) {
  
  if (event.request.method !== 'GET') {
    return;
  }

  
  if (!event.request.url.startsWith('http')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        
        if (response) {
          return response;
        }
        
        
        const fetchRequest = event.request.clone();
        
        return fetch(fetchRequest).then(function(response) {
          
          if (!response || response.status !== 200 || response.type !== 'basic') {
            return response;
          }
          
          
          const responseToCache = response.clone();
          
          
          const cacheToUse = event.request.url.includes('/static/') ? STATIC_CACHE : DYNAMIC_CACHE;
          
          // Try to cache, but don't fail if storage is blocked
          caches.open(cacheToUse)
            .then(function(cache) {
              cache.put(event.request, responseToCache);
            })
            .catch(function(error) {
              // Silently handle storage access blocked by tracking prevention
              // The response will still be returned to the client
            });
          
          return response;
        }).catch(function(error) {
          console.log('Fetch failed:', error);
          
          // Try to return cached fallback, but handle storage access errors
          if (event.request.mode === 'navigate') {
            return caches.match('/').catch(function() {
              // If cache access fails, return the fetch error
              throw error;
            });
          }
          throw error;
        });
      })
      .catch(function(error) {
        // If cache.match fails (storage blocked), just fetch normally
        return fetch(event.request).catch(function(fetchError) {
          console.log('Both cache and fetch failed:', fetchError);
          throw fetchError;
        });
      })
  );
});
