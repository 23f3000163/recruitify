const STATIC_CACHE = 'recruitify-static-v1'
const RUNTIME_CACHE = 'recruitify-runtime-v1'
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/favicon.svg',
  '/icon-192.svg',
  '/icon-512.svg'
]

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(STATIC_ASSETS))
  )
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== STATIC_CACHE && key !== RUNTIME_CACHE)
          .map((key) => caches.delete(key))
      )
    })
  )
  self.clients.claim()
})

function isSameOrigin(url) {
  return url.origin === self.location.origin
}

self.addEventListener('fetch', (event) => {
  const request = event.request

  if (request.method !== 'GET') {
    return
  }

  const url = new URL(request.url)
  if (!isSameOrigin(url)) {
    return
  }

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const responseClone = response.clone()
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(request, responseClone)
          })
          return response
        })
        .catch(async () => {
          const cachedPage = await caches.match(request)
          if (cachedPage) {
            return cachedPage
          }
          const appShell = await caches.match('/index.html')
          return appShell || Response.error()
        })
    )
    return
  }

  const isAssetRequest = ['style', 'script', 'worker', 'image', 'font'].includes(
    request.destination
  )

  if (!isAssetRequest) {
    return
  }

  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      const networkResponse = fetch(request)
        .then((response) => {
          const responseClone = response.clone()
          caches.open(RUNTIME_CACHE).then((cache) => {
            cache.put(request, responseClone)
          })
          return response
        })
        .catch(() => cachedResponse)

      return cachedResponse || networkResponse
    })
  )
})
