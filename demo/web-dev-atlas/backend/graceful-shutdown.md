---
type: pattern
title: "Graceful Shutdown on SIGTERM"
description: "Draining in-flight HTTP requests and closing DB pools cleanly during deploys and autoscaling."
tags: [backend, devops, reliability]
resource: https://cloud.google.com/blog/products/containers-kubernetes/kubernetes-best-practices-terminating-with-grace
---

# Graceful Shutdown on SIGTERM

During rolling deploys, orchestrators send `SIGTERM` before force-killing a container.

## Shutdown Sequence
1. Mark [readiness health check](../devops/health-checks-readiness.md) unhealthy so load balancers stop sending new traffic.
2. Finish in-flight requests up to a timeout.
3. Close [database connection pools](../database/connection-pooling.md) and flush [telemetry](../devops/opentelemetry-tracing.md).
