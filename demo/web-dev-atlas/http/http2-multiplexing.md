---
type: technical-note
title: "HTTP/2 Multiplexing and Header Compression"
description: "Eliminating head-of-line blocking at the HTTP layer with binary framing, streams, and HPACK."
tags: [http, networking, performance]
resource: https://httpwg.org/specs/rfc9113.html
---

# HTTP/2 Multiplexing and Header Compression

HTTP/2 replaces HTTP/1.1's text-based sequential requests with a binary framing layer over a single TCP connection.

## Key Mechanisms
- **Multiplexed Streams:** Multiple request/response streams interleave concurrently on one TCP connection, removing application-layer head-of-line blocking.
- **HPACK:** Compresses repetitive headers (`Cookie`, `User-Agent`) using static/dynamic tables.
- **TCP Caveat:** Packet loss still stalls all streams at the TCP layer, which [HTTP/3 and QUIC](http3-quic.md) solves using UDP.

Pairs well with [HTTP caching](caching.md) and [image optimization](../performance/image-optimization-webp-avif.md).
