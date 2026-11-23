---
type: security-note
title: "Cross-Site Request Forgery (CSRF) Defense"
description: "Preventing unauthorized state-changing requests via SameSite cookies, CSRF tokens, and Origin checks."
tags: [security, csrf, browser]
resource: https://owasp.org/www-community/attacks/csrf
---

# Cross-Site Request Forgery (CSRF) Defense

CSRF tricks a victim's authenticated browser into sending unwanted state-changing requests to a trusted site.

## Mitigations
- **SameSite Cookies:** Set `SameSite=Lax` or `Strict` on [session cookies](../http/cookies-samesite.md).
- **Synchronizer / Double-Submit Tokens:** Require an unpredictable header token on `POST`/`PUT`/`DELETE`.
- **Origin / Referer Validation:** Combine with strict [CORS](cors.md) policies.
