---
type: architecture-guide
title: "Service Workers and Offline-First PWAs"
description: "Intercepting network requests with Cache Storage for offline support and instant repeat loads."
tags: [frontend, pwa, caching]
resource: https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API
---

# Service Workers and Offline-First PWAs

A Service Worker is a programmable network proxy running in the browser between your app and the network.

## Caching Strategies
- **Cache-First:** Instant loads for fingerprinted static bundles.
- **Stale-While-Revalidate:** Serve cached data immediately while updating in the background.
- Store structured offline state in [IndexedDB](indexeddb-storage.md) alongside [HTTP caching](../http/caching.md).
