---
type: technical-note
title: "JavaScript Event Loop, Tasks, and Microtasks"
description: "How the call stack, microtask queue (Promises), and macrotask queue schedule execution."
tags: [javascript, frontend, concurrency]
resource: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Event_loop
---

# JavaScript Event Loop, Tasks, and Microtasks

JavaScript runs on a single main thread per browsing context, coordinating async work via queues.

## Execution Order
1. Run synchronous call stack to completion.
2. Drain the **entire microtask queue** (`Promise.then`, `queueMicrotask`) before the next render.
3. Run one macrotask (`setTimeout`, UI event) and repeat.

Offload heavy CPU work to [Web Workers](web-workers.md) to keep [INP](../performance/core-web-vitals.md) low.
