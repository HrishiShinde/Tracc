const CACHE_NAME = "tracc-cache-v1";
const urlsToCache = [
  "/",
  "/static/css/style.css",
  "/static/js/app.js",
  // aur important assets
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
