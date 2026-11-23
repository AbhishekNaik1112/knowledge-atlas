---
type: architecture-guide
title: "Server-Side Rendering (SSR) and Hydration"
description: "Rendering HTML on the server for fast FCP/SEO and attaching client event listeners via hydration."
tags: [frontend, ssr, performance]
resource: https://web.dev/articles/rendering-on-the-web
---

# Server-Side Rendering (SSR) and Hydration

SSR generates complete HTML on the server per request, improving First Contentful Paint and SEO over blank SPA shells.

## Tradeoffs
- **Hydration Cost:** The client must download JS and attach listeners before the page becomes interactive ([INP](../performance/core-web-vitals.md)).
- **Streaming SSR & Islands:** Stream above-the-fold HTML early and hydrate interactive islands lazily with [code splitting](../performance/lazy-loading-code-splitting.md).
