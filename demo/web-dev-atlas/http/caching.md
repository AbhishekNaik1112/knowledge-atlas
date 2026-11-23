---
type: technical-note
title: HTTP Caching and ETags
description: Reducing latency and origin load with Cache-Control directives, ETags, and conditional requests.
tags: [http, caching, performance]
resource: https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching
---

# HTTP Caching and ETags

HTTP caching lets browsers and CDNs reuse previously fetched responses without hitting the origin server on every request.

## Cache-Control Directives
- `public, max-age=3600`: Cacheable by both browser and shared CDN proxies for 1 hour.
- `private, no-cache`: Stored by the browser, but must revalidate with the origin before reuse.
- `no-store`: Never persist the response (used for sensitive payloads).

## Conditional Requests (`ETag` / `304`)
When a server includes an `ETag: "v1-abc"` header, the client sends `If-None-Match: "v1-abc"` on subsequent requests. If unchanged, the server replies with `304 Not Modified` and an empty body, saving bandwidth on [REST API endpoints](rest-api-design.md).
