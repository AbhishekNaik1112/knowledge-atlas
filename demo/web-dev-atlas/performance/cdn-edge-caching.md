---
type: architecture-guide
title: "CDN Edge Caching and Cache Invalidation"
description: "Serving static and semi-dynamic content from global edge PoPs with surrogate keys."
tags: [performance, cdn, caching]
resource: https://developer.mozilla.org/en-US/docs/Glossary/CDN
---

# CDN Edge Caching and Cache Invalidation

CDNs terminate [TLS](../security/tls-https-handshakes.md) and cache responses close to users, cutting RTT from hundreds of milliseconds to single digits.

## Cache Control & Purging
- Use `s-maxage` + `stale-while-revalidate` in [HTTP Cache-Control](../http/caching.md).
- Tag responses with `Surrogate-Key` headers for instant targeted purging on content updates.
