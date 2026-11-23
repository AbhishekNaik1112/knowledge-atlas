---
type: technical-note
title: "Web Workers for Off-Main-Thread Compute"
description: "Running CPU-intensive parsing, crypto, or search indexing without blocking the UI thread."
tags: [frontend, javascript, performance]
resource: https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API
---

# Web Workers for Off-Main-Thread Compute

Web Workers execute JavaScript in background OS threads isolated from the DOM.

## Communication
- Exchange data via `postMessage()` (structured clone) or zero-copy `Transferable` `ArrayBuffer`s.
- Keeps the [event loop](event-loop-microtasks.md) responsive during large JSON/Markdown parsing.
- Distinct from [Service Workers](service-workers-pwa.md), which act as network proxies.
