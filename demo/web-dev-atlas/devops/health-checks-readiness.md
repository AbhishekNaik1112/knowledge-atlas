---
type: pattern
title: "Liveness vs Readiness Health Probes"
description: "Distinguishing process aliveness from dependency readiness in container orchestrators."
tags: [devops, reliability, kubernetes]
resource: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
---

# Liveness vs Readiness Health Probes

Conflating liveness and readiness causes cascading restarts during transient DB hiccups.

- **Liveness (`/healthz`):** Lightweight check that the event loop isn't deadlocked; failure triggers container restart.
- **Readiness (`/readyz`):** Verifies DB/Redis connectivity; failure removes the pod from load-balancer rotation—also used during [graceful shutdown](../backend/graceful-shutdown.md).
