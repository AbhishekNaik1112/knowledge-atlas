---
type: pattern
title: "Debouncing vs Throttling in UI Events"
description: "Controlling high-frequency input, scroll, and resize handlers to save CPU and API calls."
tags: [performance, javascript, patterns]
resource: https://css-tricks.com/debouncing-throttling-explained-examples/
---

# Debouncing vs Throttling in UI Events

Firing an API call or [layout calculation](../frontend/dom-and-reflow.md) on every keystroke or scroll pixel overwhelms both browser and backend.

- **Debounce:** Wait until events pause for $N$ ms (ideal for live search boxes).
- **Throttle:** Execute at most once every $N$ ms (ideal for scroll/resize listeners).
- Combine with server-side [rate limiting](../patterns/rate-limiting.md).
