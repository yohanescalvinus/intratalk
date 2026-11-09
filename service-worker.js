const CACHE = 'intratalk-v1';
const ASSETS = [
  './',
  './index.html',
  './manifest.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  // Jangan intercept request ke server signaling (port 8443)
  if (e.request.url.includes(':8443')) return;

  e.respondWith(
    caches.match(e.request).then(res => {
      return res || fetch(e.request).then(netRes => {
        if (e.request.method === 'GET' && netRes.status === 200) {
          const clone = netRes.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
        }
        return netRes;
      }).catch(() => caches.match('./index.html'));
    })
  );
});
