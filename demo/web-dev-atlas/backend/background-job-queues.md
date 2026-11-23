---
type: architecture-guide
title: "Background Job Queues and Workers"
description: "Offloading slow emails, PDFs, and embeddings from HTTP request threads to async workers."
tags: [backend, reliability, architecture]
resource: https://12factor.net/processes
---

# Background Job Queues and Workers

Keeping HTTP handlers fast requires moving slow I/O (emails, video transcoding, [webhook syncs](../http/webhooks-signatures.md)) to background workers.

## Reliability Patterns
- **At-Least-Once Delivery:** Workers acknowledge jobs only after completion; make handlers idempotent via [idempotency keys](idempotency-keys.md).
- **Exponential Backoff + DLQ:** Retry transient errors with jitter, then route poison pills to a Dead Letter Queue.
