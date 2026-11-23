---
type: reference
title: "Resource Hints: Preconnect, Preload, and Prefetch"
description: "Instructing the browser which origins, fonts, and next-page chunks to fetch early."
tags: [performance, html, networking]
resource: https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/rel/preload
---

# Resource Hints: Preconnect, Preload, and Prefetch

Resource hints let the browser start DNS/TLS or downloads before the parser discovers them late in CSS/JS.

- `rel="preconnect"`: Warm DNS + [TLS](../security/tls-https-handshakes.md) to critical third-party API/CDN origins.
- `rel="preload"`: High-priority fetch for the LCP hero image or critical font on the current page.
- `rel="prefetch"`: Low-priority background fetch for likely next-route [code-split chunks](lazy-loading-code-splitting.md).
