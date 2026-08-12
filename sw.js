const CACHE="fondsmonitor-v3";
const STATIC=["./","./index.html","./manifest.webmanifest","./icon.svg"];
self.addEventListener("install",e=>{self.skipWaiting();e.waitUntil(caches.open(CACHE).then(c=>c.addAll(STATIC)))});
self.addEventListener("activate",e=>e.waitUntil(Promise.all([caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))),self.clients.claim()])));
self.addEventListener("fetch",e=>{
 const u=new URL(e.request.url);
 if(u.pathname.endsWith("/data/nav.json")||e.request.mode==="navigate"){
   e.respondWith(fetch(e.request,{cache:"no-store"}).then(r=>{const cp=r.clone();if(r.ok)caches.open(CACHE).then(c=>c.put(e.request,cp));return r}).catch(()=>caches.match(e.request).then(r=>r||caches.match("./index.html"))));
   return;
 }
 e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request)));
});