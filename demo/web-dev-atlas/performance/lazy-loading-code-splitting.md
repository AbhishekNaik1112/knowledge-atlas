---
type: technical-note
title: "Route-Based Code Splitting and Lazy Loading"
description: "Shrinking initial JavaScript bundles with dynamic import() and native image lazy loading."
tags: [performance, frontend, bundling]
resource: https://web.dev/articles/reduce-javascript-payloads-with-code-splitting
---

# Route-Based Code Splitting and Lazy Loading

Shipping a single monolithic JS bundle delays hydration and hurts [Core Web Vitals](core-web-vitals.md).

## Techniques
- **Dynamic `import()`:** Split routes, charts, and modals into on-demand chunks.
- **Native `loading="lazy"`:** Defer offscreen images below the fold (never on the LCP hero image!).
- Combine with [resource hints](preload-prefetch-hints.md) for likely next navigations.
