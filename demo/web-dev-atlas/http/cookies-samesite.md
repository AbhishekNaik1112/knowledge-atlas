---
type: security-note
title: "HTTP Cookies and SameSite Attributes"
description: "Configuring HttpOnly, Secure, and SameSite flags to protect session cookies."
tags: [http, cookies, security]
resource: https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies
---

# HTTP Cookies and SameSite Attributes

Cookies store small stateful tokens in the browser and are automatically attached to matching requests.

## Security Flags
- `HttpOnly`: Blocks `document.cookie` access, mitigating [XSS](../security/xss-prevention.md) token theft.
- `Secure`: Restricts transmission to [HTTPS/TLS](../security/tls-https-handshakes.md) connections.
- `SameSite=Lax` or `Strict`: Defends against [CSRF](../security/csrf-protection.md) on cross-site requests.

Compare with bearer tokens in [JWT authentication](../security/jwt-auth.md).
