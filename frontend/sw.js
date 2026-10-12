// Circadian Hydration Platform - PWA Service Worker (sw.js)
const CACHE_NAME = 'circadian-cache-v1';
const ASSETS_TO_CACHE = [
  './',
  './index.html',
  './manifest.json',
  'https://cdn.tailwindcss.com',
  'https://cdn.jsdelivr.net/npm/chart.js',
  'https://unpkg.com/lucide@latest',
  'https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js'
];

// 1. 설치 및 핵심 리소스 캐싱
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE).catch((err) => {
        console.warn('Pre-cache partial fail, continuing:', err);
      });
    })
  );
  self.skipWaiting();
});

// 2. 활성화 및 구버전 캐시 정리
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  return self.clients.claim();
});

// 3. 네트워크 우선 / 캐시 폴백 전략
self.addEventListener('fetch', (event) => {
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});

// 4. 백그라운드 푸시 알림 수신 (Push API)
self.addEventListener('push', (event) => {
  let data = {
    title: '[Circadian] 서카디언 수분 루틴 알림',
    body: '물 섭취 루틴을 체크할 시간입니다.'
  };

  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: 'https://cdn-icons-png.flaticon.com/512/3105/3105807.png',
    badge: 'https://cdn-icons-png.flaticon.com/512/3105/3105807.png',
    vibrate: [200, 100, 200],
    tag: 'circadian-scheduled-push',
    renotify: true,
    data: {
      url: './'
    }
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

// 5. 알림 클릭 시 앱 열기
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes('circadian') && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow('./');
      }
    })
  );
});

// 6. 메인 스크립트에서 직접 서비스워커를 통한 OS 알림 발송 요청 수신
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SHOW_NOTIFICATION') {
    const { title, body } = event.data;
    self.registration.showNotification(title, {
      body: body,
      icon: 'https://cdn-icons-png.flaticon.com/512/3105/3105807.png',
      badge: 'https://cdn-icons-png.flaticon.com/512/3105/3105807.png',
      vibrate: [150, 75, 150],
      tag: 'circadian-local-push-' + Date.now(),
      renotify: true,
      data: { url: './' }
    });
  }
});
