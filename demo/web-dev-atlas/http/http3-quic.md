---
type: technical-note
title: "HTTP/3 and QUIC Transport"
description: "Running HTTP over UDP-based QUIC with built-in TLS 1.3 and independent stream recovery."
tags: [http, quic, networking]
resource: https://httpwg.org/specs/rfc9114.html
---

# HTTP/3 and QUIC Transport

HTTP/3 replaces TCP with **QUIC**, a multiplexed, encrypted transport protocol built on UDP.

## Why QUIC Matters
- **Zero TCP Head-of-Line Blocking:** Lost packets only stall the affected stream, not sibling streams like in [HTTP/2](http2-multiplexing.md).
- **0-RTT / 1-RTT Handshakes:** Integrates [TLS 1.3](../security/tls-https-handshakes.md) directly into the transport handshake.
- **Connection Migration:** Mobile clients switching Wi-Fi to cellular keep the same connection ID without re-handshaking.
