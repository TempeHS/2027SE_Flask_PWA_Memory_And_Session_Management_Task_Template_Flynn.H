/**
 * Service worker: lets the app install as a PWA and show an offline page.
 * README Step 10 changes what it caches and when old caches are deleted.
 */

const CACHE_NAME = "canteen-v2";
const STATIC_ASSETS = [
  "/offline.html",
  "/static/css/bootstrap.min.css",
  "/static/css/style.css",
  "/static/js/bootstrap.bundle.min.js",
  "/static/js/app.js",
  "/static/images/logo.svg",
  "/static/images/favicon.png",
  "/static/manifest.json",
  "/static/icons/icon-192x192.png",
  "/static/icons/icon-512x512.png",
];

/**
 * Install: download and cache the static files the app needs offline.
 */
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting()),
  );
});

/**
 * Activate: runs when a new version of this file takes over.
 * README Step 10 makes it delete caches left by older versions.
 */
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((names) =>
        Promise.all(
          names
            .filter((name) => name !== CACHE_NAME)
            .map((name) => caches.delete(name)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

/**
 * Fetch: runs for every request a page makes.
 * README Step 10 limits caching to static files and the offline page.
 */
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (event.request.method !== "GET" || url.origin !== location.origin) return;

  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches
        .match(event.request)
        .then((cached) => cached || fetch(event.request)),
    );
  } else if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request).catch(() => caches.match("/offline.html")),
    );
  }
});
