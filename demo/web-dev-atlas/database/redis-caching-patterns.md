---
type: pattern
title: "Redis Caching Patterns (Cache-Aside & Write-Through)"
description: "Preventing cache stampedes, stale reads, and thundering herds with TTLs and jitter."
tags: [database, caching, redis, performance]
resource: https://redis.io/docs/latest/develop/use/patterns/
---

# Redis Caching Patterns (Cache-Aside & Write-Through)

In-memory caches like Redis cut database load and p99 latency for hot reads.

## Patterns & Pitfalls
- **Cache-Aside:** Check Redis -> on miss, query DB -> populate Redis with TTL + random jitter.
- **Stampede Protection:** Use single-flight locks or probabilistic early expiration for hot keys.
- Complement with [HTTP caching](../http/caching.md) at the edge.
