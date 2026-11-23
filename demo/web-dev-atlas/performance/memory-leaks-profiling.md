---
type: technical-note
title: "Finding Memory Leaks with Heap Snapshots"
description: "Detecting detached DOM nodes, uncleaned event listeners, and growing closures."
tags: [performance, debugging, javascript]
resource: https://developer.chrome.com/docs/devtools/memory-problems/
---

# Finding Memory Leaks with Heap Snapshots

Long-lived SPAs and Node.js servers degrade when references prevent garbage collection.

## Common Culprits
- Forgotten `addEventListener` / `setInterval` / [WebSocket](../realtime/websockets-vs-sse.md) subscriptions on unmount.
- Unbounded in-memory caches without LRU eviction.
- Compare three sequential heap snapshots in DevTools to isolate retained objects.
