---
type: pattern
title: "Webhook Delivery and HMAC Signatures"
description: "Verifying webhook authenticity with HMAC-SHA256, timestamp replay checks, and async processing."
tags: [http, webhooks, security]
resource: https://webhooks.fyi/
---

# Webhook Delivery and HMAC Signatures

Webhooks push event notifications from a provider to your HTTP endpoint instead of polling.

## Production Checklist
- **HMAC Verification:** Compute `HMAC-SHA256` over the raw request bytes and compare with `hmac.compare_digest`.
- **Fast Ack + Queue:** Return `202 Accepted` quickly and hand work off to [background job queues](../backend/background-job-queues.md).
- **Idempotency:** Deduplicate retries using event IDs and [idempotency keys](../backend/idempotency-keys.md).
