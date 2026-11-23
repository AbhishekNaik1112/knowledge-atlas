---
type: technical-note
title: "TLS 1.3 and HTTPS Handshakes"
description: "How TLS 1.3 establishes encrypted channels in 1-RTT with forward secrecy."
tags: [security, tls, networking]
resource: https://www.rfc-editor.org/rfc/rfc8446
---

# TLS 1.3 and HTTPS Handshakes

TLS 1.3 encrypts HTTP traffic in transit, guaranteeing confidentiality, integrity, and server authentication.

## Improvements Over TLS 1.2
- **1-RTT Handshake:** Cuts connection setup latency in half.
- **Forward Secrecy Only:** Removes legacy RSA key exchange; uses ephemeral Diffie-Hellman (`ECDHE`).
- **HSTS:** Send `Strict-Transport-Security` so browsers never downgrade to plaintext HTTP; terminated often at [Nginx](../devops/reverse-proxy-nginx.md) or [HTTP/3](../http/http3-quic.md).
