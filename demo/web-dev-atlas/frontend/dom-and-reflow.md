---
type: technical-note
title: "Browser Rendering Pipeline: DOM, Layout, and Paint"
description: "Understanding style recalculation, layout reflow, paint, and GPU compositing."
tags: [frontend, browser, performance]
resource: https://web.dev/articles/rendering-performance
---

# Browser Rendering Pipeline: DOM, Layout, and Paint

Every visual update passes through **Style -> Layout (Reflow) -> Paint -> Composite**.

## Avoiding Layout Thrashing
- Batch DOM reads (`offsetHeight`) before DOM writes (`style.width`).
- Animate `transform` and `opacity` on the compositor thread instead of `top`/`left`.
- Impacts [Core Web Vitals](../performance/core-web-vitals.md) (CLS/INP) and [CSS Grid/Flexbox](css-grid-vs-flexbox.md).
