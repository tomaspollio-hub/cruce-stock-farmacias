const CACHE = 'farmacias-global-v2';

const STATIC = [
  '/login.html',
  '/cadete.html',
  '/operador.html',
  '/index.html',
  '/historial.html',
  '/nuevo-cruce.html',
  '/usuarios.html',
  '/config.html',
  '/css/variables.css',
  '/css/reset.css',
  '/css/layout.css',
  '/css/components.css',
  '/js/auth.js',
  '/js/toast.js',
  '/js/mobile-nav.js',
  '/js/storage.js',
  '/img/logo-global.png',
  '/manifest.json',
];

// Instalar: pre-cachear todos los assets estáticos
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(STATIC)).then(() => self.skipWaiting())
  );
});

// Activar: eliminar caches viejos
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => clients.claim())
  );
});

// Fetch: network-first para API, cache-first para estáticos
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Solo interceptar requests del mismo origen
  if (url.origin !== self.location.origin) return;

  if (url.pathname.startsWith('/api/')) {
    // API: intentar red, caer a cache si no hay conexión
    e.respondWith(
      fetch(e.request)
        .then(res => {
          if (res.ok) {
            const clone = res.clone();
            caches.open(CACHE).then(c => c.put(e.request, clone));
          }
          return res;
        })
        .catch(() => caches.match(e.request))
    );
  } else {
    // Estáticos: cache primero, red como fallback
    e.respondWith(
      caches.match(e.request).then(cached => cached || fetch(e.request))
    );
  }
});
