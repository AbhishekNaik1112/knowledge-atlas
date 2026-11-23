---
type: technical-note
title: "HTTP Compression with Gzip and Brotli"
description: "Reducing payload transfer size for text assets and JSON APIs using Brotli and Gzip."
tags: [http, performance, compression]
resource: https://developer.mozilla.org/en-US/docs/Web/HTTP/Compression
---

# HTTP Compression with Gzip and Brotli

Compressing text-based responses (`text/html`, `application/javascript`, `application/json`) cuts transfer bytes by 60–80%.

## Choosing an Algorithm
- **Brotli (`br`):** ~15–25% smaller than Gzip for static assets; pre-compress at build time or at the [Nginx reverse proxy](../devops/reverse-proxy-nginx.md).
- **Gzip:** Fast dynamic compression for [REST API](rest-api-design.md) JSON responses.
- Always set `Vary: Accept-Encoding` during [content negotiation](content-negotiation.md).
