---
type: architecture-guide
title: "Distributed Tracing with OpenTelemetry"
description: "Tracking end-to-end request latency across browsers, APIs, queues, and databases."
tags: [devops, observability, performance]
resource: https://opentelemetry.io/docs/concepts/signals/traces/
---

# Distributed Tracing with OpenTelemetry

A distributed trace links spans across frontend fetches, [API middleware](../backend/middleware-pipelines.md), [background queues](../backend/background-job-queues.md), and SQL queries via `traceparent` headers.

## Why It Helps
- Pinpoints whether p99 latency comes from [N+1 SQL queries](../database/n-plus-one-queries.md), cold caches, or downstream APIs.
- Correlates directly with [structured logs](../backend/structured-logging.md).
