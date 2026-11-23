---
type: pattern
title: "Idempotency Keys for Safe Retries"
description: "Preventing duplicate charges or writes on network retries using client-supplied Idempotency-Key headers."
tags: [backend, api-design, reliability]
resource: https://stripe.com/docs/api/idempotent_requests
---

# Idempotency Keys for Safe Retries

When a `POST` request times out, the client cannot know whether the server committed it. An `Idempotency-Key` header makes retries safe.

## Implementation
- Store `(idempotency_key, request_hash, response_status, response_body)` in Redis or a Postgres unique constraint inside an [ACID transaction](../database/acid-transactions.md).
- Replay the stored response on duplicate keys; reject mismatched payloads with `409`/`422`. Also essential for [webhooks](../http/webhooks-signatures.md).
