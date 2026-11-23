---
type: reference
title: "Core Web Vitals: LCP, INP, and CLS"
description: "Measuring and optimizing loading (LCP), interactivity (INP), and visual stability (CLS)."
tags: [performance, frontend, web-vitals]
resource: https://web.dev/articles/vitals
---

# Core Web Vitals: LCP, INP, and CLS

Google's Core Web Vitals measure real-user perceived performance:

- **LCP (Largest Contentful Paint <= 2.5s):** Optimize hero [images](image-optimization-webp-avif.md), [SSR](../frontend/hydration-and-ssr.md), and [resource hints](preload-prefetch-hints.md).
- **INP (Interaction to Next Paint <= 200ms):** Break up long tasks on the [event loop](../frontend/event-loop-microtasks.md) and offload to [Web Workers](../frontend/web-workers.md).
- **CLS (Cumulative Layout Shift <= 0.1):** Reserve image/ad dimensions to prevent [reflows](../frontend/dom-and-reflow.md).
