---
type: technical-note
title: API Rate Limiting Strategies
description: Protecting web services from abuse and cascading failures using token bucket and sliding window limits.
tags: [api-design, reliability, security]
resource: https://datatracker.ietf.org/doc/html/rfc6585
---

# API Rate Limiting Strategies

Rate limiting caps the number of requests a client can make in a time window, protecting [REST APIs](../http/rest-api-design.md) and [realtime streams](../realtime/websockets-vs-sse.md) from abuse and traffic spikes.

## Common Algorithms
- **Token Bucket:** Allows short bursts up to bucket capacity while enforcing a steady average refill rate.
- **Sliding Window Log / Counter:** Smooths boundary bursts that affect fixed-window counters.

## Client Feedback
Return `429 Too Many Requests` along with `Retry-After` and `X-RateLimit-Remaining` headers so well-behaved clients can back off gracefully.
