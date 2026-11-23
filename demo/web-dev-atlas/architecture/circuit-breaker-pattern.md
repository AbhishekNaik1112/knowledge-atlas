---
type: pattern
title: "Circuit Breaker Pattern for Resilient APIs"
description: "Failing fast when downstream services degrade to prevent cascading timeouts."
tags: [architecture, reliability, backend]
resource: https://martinfowler.com/bliki/CircuitBreaker.html
---

# Circuit Breaker Pattern for Resilient APIs

When a downstream dependency slows down or fails, unbounded retries exhaust [connection pools](../database/connection-pooling.md) and worker threads.

## States
- **Closed:** Requests flow normally; failures are counted in a sliding window.
- **Open:** Requests fail fast immediately without calling the failing upstream.
- **Half-Open:** After a cooldown, a few probe requests test recovery before closing again.

Combine with [API rate limiting](../patterns/rate-limiting.md) and [readiness probes](../devops/health-checks-readiness.md).
