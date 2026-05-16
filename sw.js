// Service Worker — Cruce Stock Farmacias
// Solo registra la app como instalable (PWA). Sin cache offline por ahora.
self.addEventListener('install',  () => self.skipWaiting());
self.addEventListener('activate', e  => e.waitUntil(clients.claim()));
