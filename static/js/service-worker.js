const CACHE_NAME = "tracc-static-v3";
const STATIC_ASSETS = [
  "/static/css/themes.css",
  "/static/css/fonts.css",
  "/static/css/styles.css",
  "/static/css/components.css",
  "/static/js/themes.js",
  "/static/js/ajax.js",
  "/static/js/app-shell.js",
  "/static/js/analytics.js",
  "/static/js/dashboard.js",
  "/static/js/profile-form.js",
  "/static/js/weight-logs.js",
  "/static/js/settings.js",
  "/static/js/settings-legacy.js",
  "/static/js/push-reminders.js",
  "/static/assets/img/tp-logo-192.png",
  "/static/assets/img/tp-logo-512.png",
  "/static/manifest.json",
  "https://cdn.jsdelivr.net/npm/chart.js",
  "https://cdn.jsdelivr.net/npm/fullcalendar/index.global.min.js",
];

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await Promise.all(STATIC_ASSETS.map(async (url) => {
      try {
      const response = await fetch(url, { cache: "reload", mode: url.startsWith("https://") ? "cors" : "same-origin" });
      if (response.ok || response.type === "opaque") await cache.put(url, response);
      } catch (error) {
        // A temporarily unavailable asset must not prevent the worker installing.
      }
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter((name) => name.startsWith("tracc-static-") && name !== CACHE_NAME)
      .map((name) => caches.delete(name)));
    await self.clients.claim();
  })());
});

self.addEventListener("push", (event) => {
  let payload = {};
  try { payload = event.data ? event.data.json() : {}; } catch (error) { payload = { body: event.data?.text() || "" }; }
  event.waitUntil(self.registration.showNotification(payload.title || "Tracc reminder", {
    body: payload.body || "Your daily weight check-in is waiting.",
    icon: "/static/assets/img/tp-logo-192.png",
    badge: "/static/assets/img/tp-logo-192.png",
    data: { url: payload.url || "/dashboard/" },
  }));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = new URL(event.notification.data?.url || "/dashboard/", self.location.origin).href;
  event.waitUntil((async () => {
    const windows = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const client of windows) {
      if (new URL(client.url).origin === self.location.origin) {
        await client.navigate(target);
        return client.focus();
      }
    }
    return self.clients.openWindow(target);
  })());
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  // Never cache authenticated pages or API responses: they contain user data.
  const isLocalStatic = url.origin === self.location.origin && url.pathname.startsWith("/static/");
  const isChartVendor = url.origin === "https://cdn.jsdelivr.net" &&
    (url.pathname === "/npm/chart.js" || url.pathname === "/npm/fullcalendar/index.global.min.js");
  if (request.method !== "GET" || (!isLocalStatic && !isChartVendor)) return;

  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);
    const network = fetch(request).then((response) => {
      if (response.ok) cache.put(request, response.clone());
      return response;
    }).catch(() => cached);
    return cached || network;
  })());
});
