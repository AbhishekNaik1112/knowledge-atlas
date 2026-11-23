---
type: pattern
title: "Structured JSON Logging and Correlation IDs"
description: "Emitting machine-parseable logs with trace_id and request context for fast incident debugging."
tags: [backend, observability, devops]
resource: https://12factor.net/logs
---

# Structured JSON Logging and Correlation IDs

Plaintext logs break down at scale. Structured JSON logs allow instant filtering by `request_id`, `user_id`, `status_code`, and `latency_ms`.

## Best Practices
- Attach a correlation `X-Request-ID` in [middleware](middleware-pipelines.md).
- Propagate `trace_id` from [OpenTelemetry](../devops/opentelemetry-tracing.md).
- Never log secrets, passwords, or raw [JWT](../security/jwt-auth.md) tokens.
