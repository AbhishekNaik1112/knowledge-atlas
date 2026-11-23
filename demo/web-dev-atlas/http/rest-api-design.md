---
type: architecture-guide
title: REST API Design Principles
description: Resource modeling, HTTP semantics, status codes, pagination, and versioning for web APIs.
tags: [http, rest, api-design]
resource: https://restfulapi.net/
---

# REST API Design Principles

RESTful APIs model domain entities as **resources** identified by stable URLs and manipulated using standard HTTP verbs (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`).

## Core Conventions
- **Idempotency & Safety:** `GET`, `HEAD`, and `OPTIONS` are safe and idempotent; `PUT` and `DELETE` are idempotent; `POST` is neither.
- **Status Codes:** Use `201 Created` with a `Location` header for new resources, `204 No Content` for deletions, `400`/`422` for validation failures, and `401`/`403` for auth errors.
- **Pagination:** Prefer cursor-based or `limit`/`offset` pagination with a `total` count for predictable client rendering.

## Cross-Cutting Concerns
- Browser clients calling an API on a different origin require [CORS preflight and headers](../security/cors.md).
- Stateless endpoints typically authenticate callers with [JWT bearer tokens](../security/jwt-auth.md).
- Read-heavy endpoints benefit from [HTTP caching and ETags](caching.md), while write-heavy endpoints should enforce [API rate limiting](../patterns/rate-limiting.md).
