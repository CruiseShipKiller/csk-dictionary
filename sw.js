/* ═══════════════════════════════════════════════════════════════
   Cruise Dictionary — Service Worker
   ───────────────────────────────────────────────────────────────
   Caching strategy:
     • App shell (HTML, manifest, icons, hero): cache-first
     • dictionary.json: NETWORK-FIRST, cache fallback
         → online users always get fresh data
         → offline users get the last successfully cached copy
     • Google Fonts: cache-first runtime caching (so type works offline)

   UPDATING THE APP:
     Bump CACHE_VERSION below whenever index.html, the icons, the
     manifest, or the hero image change. The old cache is deleted on
     activation, so users pick up the new shell on their next visit.
     You do NOT need to bump the version just to update dictionary.json —
     network-first already keeps the word list fresh for online users.
   ═══════════════════════════════════════════════════════════════ */

const CACHE_VERSION = 'v1';
const CACHE_NAME = `cruise-dict-${CACHE_VERSION}`;

// Core files that make up the installable app shell.
// Paths are relative to the service worker's scope (repo root).
const APP_SHELL = [
  './',
  './index.html',
  './manifest.json',
  './dictionarybackgrond.png',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-512-maskable.png',
  './icons/apple-touch-icon.png'
];

// ── INSTALL ── pre-cache the app shell ─────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())   // activate new SW without waiting
  );
});

// ── ACTIVATE ── delete old version caches ──────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k.startsWith('cruise-dict-') && k !== CACHE_NAME)
          .map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())  // take control of open pages now
  );
});

// ── FETCH ── route by request type ─────────────────────────────
self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);

  // Only handle GET requests
  if (req.method !== 'GET') return;

  // 1. dictionary.json → network-first (fresh when online, cached when not)
  if (url.pathname.endsWith('dictionary.json')) {
    event.respondWith(networkFirst(req));
    return;
  }

  // 2. Google Fonts (CSS + font files) → cache-first runtime caching
  if (url.hostname === 'fonts.googleapis.com' || url.hostname === 'fonts.gstatic.com') {
    event.respondWith(cacheFirst(req));
    return;
  }

  // 3. Everything same-origin (app shell) → cache-first
  if (url.origin === self.location.origin) {
    event.respondWith(cacheFirst(req));
    return;
  }

  // 4. Anything else → just go to network
});

// ── STRATEGIES ─────────────────────────────────────────────────

// Network-first: try the network, fall back to cache on failure.
// On a successful fetch, refresh the cached copy for next offline use.
async function networkFirst(req) {
  const cache = await caches.open(CACHE_NAME);
  try {
    const fresh = await fetch(req);
    if (fresh && fresh.ok) {
      cache.put(req, fresh.clone());
    }
    return fresh;
  } catch (err) {
    const cached = await cache.match(req);
    if (cached) return cached;
    throw err;  // nothing cached and no network — let it fail
  }
}

// Cache-first: serve from cache if present, otherwise fetch and cache.
// Handles cross-origin (opaque) font responses too.
async function cacheFirst(req) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(req);
  if (cached) return cached;
  try {
    const fresh = await fetch(req);
    // Cache successful or opaque (cross-origin font) responses
    if (fresh && (fresh.ok || fresh.type === 'opaque')) {
      cache.put(req, fresh.clone());
    }
    return fresh;
  } catch (err) {
    // Offline and not cached. For navigations, fall back to index.html.
    if (req.mode === 'navigate') {
      const shell = await cache.match('./index.html');
      if (shell) return shell;
    }
    throw err;
  }
}
