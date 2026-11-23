---
type: technical-note
title: "Docker Multi-Stage Builds"
description: "Separating build toolchains from minimal runtime images for smaller, safer containers."
tags: [devops, docker, containers]
resource: https://docs.docker.com/build/building/multi-stage/
---

# Docker Multi-Stage Builds

Multi-stage Dockerfiles compile assets or wheels in a builder stage and copy only runtime artifacts into a slim final image.

## Benefits
- **Smaller Images:** Excludes compilers, headers, and dev dependencies—faster pulls and deploys.
- **Smaller Attack Surface:** Fewer binaries in production; run as a non-root user.
