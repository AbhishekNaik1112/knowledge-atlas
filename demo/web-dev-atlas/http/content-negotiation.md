---
type: reference
title: "HTTP Content Negotiation"
description: "Using Accept, Accept-Encoding, and Accept-Language headers to serve the best representation."
tags: [http, rest, api-design]
resource: https://developer.mozilla.org/en-US/docs/Web/HTTP/Content_negotiation
---

# HTTP Content Negotiation

Content negotiation lets a single URI serve multiple representations based on client request headers.

## Common Headers
- `Accept`: Media type preference (`application/json`, `text/html`).
- `Accept-Encoding`: Compression algorithms (`br`, `gzip`) handled by [compression](compression-gzip-brotli.md).
- `Vary`: Tells [CDNs](../performance/cdn-edge-caching.md) and [HTTP caches](caching.md) which request headers affect the cached response.
