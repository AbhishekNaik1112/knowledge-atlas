---
type: architecture-guide
title: "Event-Driven Sync with Webhooks"
description: "Keeping distributed developer tools and catalogs synchronized via signed push events."
tags: [architecture, webhooks, realtime]
resource: https://webhooks.fyi/
---

# Event-Driven Sync with Webhooks

Push-based webhooks let repositories notify downstream services immediately when code or docs change, avoiding wasteful polling.

## Design Essentials
- Verify payload authenticity with [HMAC signatures](../http/webhooks-signatures.md).
- Process heavy work asynchronously in [background job queues](../backend/background-job-queues.md) after returning `202 Accepted`.
- Track sync state and protect against duplicate deliveries with [idempotency keys](../backend/idempotency-keys.md).
