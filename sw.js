const CACHE = 'farmacias-global-v9';

// Solo pre-cachear imágenes y manifest — CSS/JS/HTML siempre van a la red primero
const STATIC_IMAGES = [
  '/img/logo-global.png',
  '/manifest.json',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(STATIC_IMAGES))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith('/api/')) {
    // API: red primero, cache como fallback offline
    e.respondWith(
      fetch(e.request)
        .then(res => {
          if (res.ok) caches.open(CACHE).then(c => c.put(e.request, res.clone()));
          return res;
        })
        .catch(() => caches.match(e.request).then(cached =>
          cached || new Response(
            JSON.stringify({ ok: false, motivo: 'offline' }),
            { status: 503, headers: { 'Content-Type': 'application/json' } }
          )
        ))
    );
  } else if (
    url.pathname.endsWith('.html') || url.pathname === '/' ||
    url.pathname.endsWith('.css')  || url.pathname.endsWith('.js')
  ) {
    // HTML / CSS / JS: siempre red primero — nunca sirve stale
    // Cache solo como fallback si no hay conexión (cadete en ruta)
    e.respondWith(
      fetch(e.request, { cache: 'no-cache' })
        .then(res => {
          if (res.ok) caches.open(CACHE).then(c => c.put(e.request, res.clone()));
          return res;
        })
        .catch(() => caches.match(e.request))
    );
  } else {
    // Imágenes: cache primero
    e.respondWith(
      caches.match(e.request).then(cached => cached || fetch(e.request))
    );
  }
});
