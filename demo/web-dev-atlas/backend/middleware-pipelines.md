---
type: pattern
title: "HTTP Middleware Pipelines"
description: "Structuring cross-cutting concerns like auth, logging, rate limiting, and error handling."
tags: [backend, architecture, patterns]
resource: https://fastapi.tiangolo.com/tutorial/middleware/
---

# HTTP Middleware Pipelines

Middleware wraps request handlers in an onion-like chain, running before the route and after the response is produced.

## Typical Order
1. Request ID & [structured logging](structured-logging.md)
2. [CORS](../security/cors.md) & security headers ([CSP](../security/csp-headers.md))
3. [Rate limiting](../patterns/rate-limiting.md)
4. Authentication ([JWT](../security/jwt-auth.md) / API key)
