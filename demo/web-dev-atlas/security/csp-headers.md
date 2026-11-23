---
type: security-note
title: "Content Security Policy (CSP)"
description: "Restricting script, style, and connect-src origins using Content-Security-Policy headers and nonces."
tags: [security, http, headers]
resource: https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP
---

# Content Security Policy (CSP)

CSP is an HTTP response header instructing the browser which script, image, and API origins are allowed to load or execute.

## Best Practices
- Replace `'unsafe-inline'` with per-request cryptographic nonces (`'nonce-...'`).
- Restrict `connect-src` to your API and [WebSocket](../realtime/websockets-vs-sse.md) origins.
- Pair with [XSS prevention](xss-prevention.md) for layered browser defense.
