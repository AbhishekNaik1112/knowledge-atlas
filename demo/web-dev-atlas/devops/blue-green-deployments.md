---
type: architecture-guide
title: "Blue-Green and Canary Deployments"
description: "Achieving zero-downtime releases and instant rollbacks with traffic shifting."
tags: [devops, deployment, reliability]
resource: https://martinfowler.com/bliki/BlueGreenDeployment.html
---

# Blue-Green and Canary Deployments

Zero-downtime releases require backward-compatible database migrations (expand-and-contract) and controlled traffic cutover.

- **Blue-Green:** Run old (Blue) and new (Green) environments side by side; flip router after [readiness checks](health-checks-readiness.md) pass.
- **Canary:** Route 1–5% of traffic to the new version while watching error rates and [traces](opentelemetry-tracing.md).
