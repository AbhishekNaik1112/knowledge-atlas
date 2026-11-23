---
type: security-note
title: JWT Authentication and Session Tradeoffs
description: Stateless bearer tokens vs server-side sessions, signing, expiration, and XSS/CSRF risks.
tags: [auth, jwt, security]
resource: https://jwt.io/introduction
---

# JWT Authentication and Session Tradeoffs

JSON Web Tokens (JWTs) are signed, self-contained tokens (`header.payload.signature`) commonly sent in the `Authorization: Bearer <token>` header to authenticate [REST API requests](../http/rest-api-design.md).

## Security Tradeoffs
- **Storage:** Storing JWTs in `localStorage` exposes them to XSS; storing them in `HttpOnly`, `Secure`, `SameSite=Lax` cookies mitigates XSS but requires CSRF protection.
- **Revocation:** Because JWTs are stateless, keep access token lifetimes short (5–15 minutes) and pair them with rotatable refresh tokens.
- **Cross-Origin Calls:** Sending `Authorization` headers from a browser triggers [CORS preflight checks](cors.md).
