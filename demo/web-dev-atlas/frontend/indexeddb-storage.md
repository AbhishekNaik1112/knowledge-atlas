---
type: technical-note
title: "IndexedDB Client-Side Storage"
description: "Storing large structured objects, blobs, and offline sync queues asynchronously in the browser."
tags: [frontend, storage, browser]
resource: https://developer.mozilla.org/en-US/docs/Web/API/IndexedDB_API
---

# IndexedDB Client-Side Storage

Unlike synchronous, 5MB-capped `localStorage`, IndexedDB is an asynchronous, transactional NoSQL object store with indexes.

## Use Cases
- Caching large datasets or documents for offline-first [Service Workers](service-workers-pwa.md).
- Queuing mutations while offline and replaying with [idempotency keys](../backend/idempotency-keys.md).
