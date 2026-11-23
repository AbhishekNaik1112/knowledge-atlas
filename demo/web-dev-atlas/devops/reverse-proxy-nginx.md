---
type: architecture-guide
title: "Reverse Proxies with Nginx"
description: "Terminating TLS, buffering slow clients, compressing responses, and load balancing upstreams."
tags: [devops, networking, nginx]
resource: https://nginx.org/en/docs/
---

# Reverse Proxies with Nginx

A reverse proxy sits in front of application servers to handle networking concerns uniformly.

## Responsibilities
- [TLS 1.3 termination](../security/tls-https-handshakes.md) and [HTTP/2](../http/http2-multiplexing.md) / [HTTP/3](../http/http3-quic.md).
- [Brotli/Gzip compression](../http/compression-gzip-brotli.md) and static asset serving.
- Upstream health checks and WebSocket/`text/event-stream` proxy pass for [SSE](../realtime/websockets-vs-sse.md).
